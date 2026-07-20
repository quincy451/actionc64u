#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import random
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

from generate_math_runtime import print_float_module


LOAD_ADDR = 0x2000


HARNESS_SOURCE = r"""
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "lib6502.h"

static char output[256];
static unsigned output_len;

static int chrout(M6502 *cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    if (output_len + 1 < sizeof output) {
        output[output_len++] = (char)cpu->registers->a;
    }
    return 0xfff0;
}

static void put32(uint8_t *memory, uint16_t address, uint32_t value)
{
    for (unsigned index = 0; index < 4; index++) {
        memory[address + index] = (uint8_t)(value >> (index * 8));
    }
}

int main(int argc, char **argv)
{
    enum {
        load_addr = 0x2000,
        input_addr = 0x3000,
        stop_addr = 0x1000,
    };
    static M6502_Memory memory;
    static M6502_Callbacks callbacks;
    static uint8_t image[4096];
    FILE *runtime;
    M6502 *cpu;
    size_t image_size;
    unsigned input;

    if (argc != 2) {
        return 2;
    }
    runtime = fopen(argv[1], "rb");
    if (!runtime) {
        return 3;
    }
    image_size = fread(image, 1, sizeof image, runtime);
    if (image_size == 0 || ferror(runtime)) {
        fclose(runtime);
        return 4;
    }
    fclose(runtime);

    cpu = M6502_new(NULL, memory, &callbacks);
    if (!cpu) {
        return 5;
    }
    M6502_setCallback(cpu, call, 0xffd2, chrout);
    while (scanf("%x", &input) == 1) {
        unsigned steps = 0;

        memcpy(memory + load_addr, image, image_size);
        memset(memory, 0, 0x100);
        put32(memory, input_addr, input);
        memory[0x02] = input_addr & 0xff;
        memory[0x03] = input_addr >> 8;
        memory[0xfff0] = 0x60;

        cpu->registers->a = 0;
        cpu->registers->x = 0;
        cpu->registers->y = 0;
        cpu->registers->p = 0x24;
        cpu->registers->s = 0xfd;
        cpu->registers->pc = load_addr;
        memory[0x01fe] = (stop_addr - 1) & 0xff;
        memory[0x01ff] = (stop_addr - 1) >> 8;
        output_len = 0;
        while (cpu->registers->pc != stop_addr && steps++ < 20000000) {
            M6502_run(cpu);
        }
        if (steps >= 20000000) {
            fprintf(stderr, "runtime timeout for print(%08x) at pc=%04x\n",
                    input, cpu->registers->pc);
            M6502_delete(cpu);
            return 6;
        }
        output[output_len] = 0;
        puts(output);
    }
    M6502_delete(cpu);
    return 0;
}
"""


def expected_print(bits: int) -> str:
    sign = "-" if bits & 0x80000000 else ""
    exponent_field = (bits >> 23) & 0xFF
    fraction = bits & 0x007FFFFF
    if exponent_field == 0xFF:
        return "NAN" if fraction else sign + "INF"
    if exponent_field == 0:
        if fraction == 0:
            return sign + "0"
        significand = fraction
        exponent = -126
    else:
        significand = 0x00800000 | fraction
        exponent = exponent_field - 127
    power = exponent - 23
    if power >= 0:
        return sign + str(significand << power)
    scale = -power
    digits = str(significand * (5**scale))
    if len(digits) <= scale:
        body = "0." + ("0" * (scale - len(digits))) + digits
    else:
        body = digits[:-scale] + "." + digits[-scale:]
    return sign + body.rstrip("0").rstrip(".")


def write_runtime(path: Path) -> int:
    builder = print_float_module()
    builder.render()
    code = bytearray(builder.code)
    for offset, label in builder.local_relocations:
        address = LOAD_ADDR + builder.labels[label]
        code[offset] = address & 0xFF
        code[offset + 1] = address >> 8
    path.write_bytes(code)
    return len(code)


def verification_cases(random_count: int, seed: int) -> list[int]:
    cases = [
        0x00000000,
        0x80000000,
        0x00000001,
        0x00000002,
        0x00000003,
        0x007FFFFE,
        0x007FFFFF,
        0x00800000,
        0x00800001,
        0x38D1B716,
        0x38D1B717,
        0x3F000000,
        0x3F800000,
        0x3FC00000,
        0x40200000,
        0x40400000,
        0x41200000,
        0x42FFFFFF,
        0x43000000,
        0x4B18967F,
        0x4B189680,
        0x7F7FFFFF,
        0x80800000,
        0xBF800000,
        0xC0333333,
        0xFF7FFFFF,
        0x7F800000,
        0xFF800000,
        0x7F800001,
        0x7FC00000,
        0xFFC00001,
    ]
    randomizer = random.Random(seed)
    cases.extend(randomizer.getrandbits(32) for _ in range(random_count))
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify generated rt_print_f machine code against exact finite decimals"
    )
    parser.add_argument("--random-cases", type=int, default=4096)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0xF10A7)
    parser.add_argument("--cc", default=os.environ.get("CC", "cc"))
    args = parser.parse_args()
    if args.random_cases < 0:
        parser.error("--random-cases must be non-negative")

    root = Path(__file__).resolve().parents[1]
    lib6502 = root / "third_party" / "lib6502"
    compiler = shlex.split(args.cc)
    if not compiler or shutil.which(compiler[0]) is None:
        raise SystemExit(f"C compiler not found: {args.cc}")
    if not (lib6502 / "lib6502.c").is_file():
        raise SystemExit(f"lib6502 source not found: {lib6502}")

    cases = verification_cases(args.random_cases, args.seed)
    with tempfile.TemporaryDirectory(prefix="action-f-print-") as temporary:
        work = Path(temporary)
        runtime_path = work / "rt_print_f.bin"
        source_path = work / "verify.c"
        harness_path = work / "verify"
        runtime_size = write_runtime(runtime_path)
        source_path.write_text(HARNESS_SOURCE, encoding="ascii")
        subprocess.run(
            [
                *compiler,
                "-std=c99",
                "-O2",
                "-Wall",
                "-Wextra",
                "-Wno-unused-function",
                f"-I{lib6502}",
                str(source_path),
                str(lib6502 / "lib6502.c"),
                "-o",
                str(harness_path),
            ],
            check=True,
        )
        completed = subprocess.run(
            [str(harness_path), str(runtime_path)],
            input="".join(f"{value:08x}\n" for value in cases),
            text=True,
            capture_output=True,
            check=True,
        )

    results = completed.stdout.splitlines()
    if len(results) != len(cases):
        raise SystemExit(f"expected {len(cases)} results, received {len(results)}")
    for index, (value, actual) in enumerate(zip(cases, results)):
        expected = expected_print(value)
        if actual != expected:
            raise SystemExit(
                f"case {index}: print({value:08x}): "
                f"got {actual!r}, expected {expected!r}"
            )
    print(
        f"rt_print_f {runtime_size} bytes: {len(cases)} exact edge/random strings passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
