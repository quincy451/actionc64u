#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import os
import random
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

from generate_math_runtime import (
    link_runtime_builders,
    special_value_module,
    square_root_module,
)


LOAD_ADDR = 0x2000


HARNESS_SOURCE = r"""
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "lib6502.h"

static void put32(uint8_t *memory, uint16_t address, uint32_t value)
{
    for (unsigned index = 0; index < 4; index++) {
        memory[address + index] = (uint8_t)(value >> (index * 8));
    }
}

static uint32_t get32(const uint8_t *memory, uint16_t address)
{
    uint32_t value = 0;
    for (unsigned index = 0; index < 4; index++) {
        value |= (uint32_t)memory[address + index] << (index * 8);
    }
    return value;
}

int main(int argc, char **argv)
{
    enum {
        load_addr = 0x2000,
        input_addr = 0x3000,
        result_addr = 0x3020,
        stop_addr = 0x1000,
    };
    static M6502_Memory memory;
    static M6502_Callbacks callbacks;
    FILE *runtime;
    M6502 *cpu;
    unsigned input;

    if (argc != 2) {
        return 2;
    }
    runtime = fopen(argv[1], "rb");
    if (!runtime) {
        return 3;
    }
    if (fread(memory + load_addr, 1, 0x1000, runtime) == 0 || ferror(runtime)) {
        fclose(runtime);
        return 4;
    }
    fclose(runtime);

    cpu = M6502_new(NULL, memory, &callbacks);
    if (!cpu) {
        return 5;
    }
    while (scanf("%x", &input) == 1) {
        unsigned steps = 0;

        memset(memory, 0, 0x100);
        put32(memory, input_addr, input);
        put32(memory, result_addr, 0xccccccccu);
        memory[0x02] = input_addr & 0xff;
        memory[0x03] = input_addr >> 8;
        memory[0x06] = result_addr & 0xff;
        memory[0x07] = result_addr >> 8;

        cpu->registers->a = 0;
        cpu->registers->x = 0;
        cpu->registers->y = 0;
        cpu->registers->p = 0x24;
        cpu->registers->s = 0xfd;
        cpu->registers->pc = load_addr;
        memory[0x01fe] = (stop_addr - 1) & 0xff;
        memory[0x01ff] = (stop_addr - 1) >> 8;
        while (cpu->registers->pc != stop_addr && steps++ < 100000) {
            M6502_run(cpu);
        }
        if (steps >= 100000) {
            fprintf(stderr, "runtime timeout for sqrt(%08x) at pc=%04x\n",
                    input, cpu->registers->pc);
            M6502_delete(cpu);
            return 6;
        }
        printf("%08x\n", get32(memory, result_addr));
    }
    M6502_delete(cpu);
    return 0;
}
"""


def expected_square_root(bits: int) -> int:
    sign = bits >> 31
    exponent = (bits >> 23) & 0xFF
    significand = bits & 0x7FFFFF
    if exponent == 0xFF:
        if significand or sign:
            return 0x7FC00000
        return 0x7F800000
    if sign:
        return 0x80000000 if bits & 0x7FFFFFFF == 0 else 0x7FC00000
    if exponent == 0:
        if significand == 0:
            return 0
        exponent = 1
    else:
        significand |= 1 << 23

    while significand < 1 << 23:
        significand <<= 1
        exponent -= 1
    unbiased = exponent - 127
    odd_exponent = unbiased & 1
    if odd_exponent:
        unbiased -= 1
    result_exponent = unbiased // 2 + 127
    radicand = significand << (23 + odd_exponent)
    root = math.isqrt(radicand)
    remainder = radicand - root * root
    if remainder > root:
        root += 1
    return (result_exponent << 23) | (root & 0x7FFFFF)


def write_runtime(path: Path) -> int:
    image = link_runtime_builders(
        [square_root_module(), special_value_module()], LOAD_ADDR
    )
    path.write_bytes(image)
    return len(image)


def verification_cases(random_count: int, seed: int) -> list[int]:
    fractions = (0, 1, 2, 0x3FFFFF, 0x7FFFFE, 0x7FFFFF)
    cases = [(exponent << 23) | fraction for exponent in range(256) for fraction in fractions]
    cases.extend(
        [
            0x00000000,
            0x80000000,
            0x00000001,
            0x00000002,
            0x00000003,
            0x007FFFFE,
            0x007FFFFF,
            0x00800000,
            0x00800001,
            0x3E800000,
            0x3F000000,
            0x3F7FFFFF,
            0x3F800000,
            0x3F800001,
            0x40000000,
            0x40000001,
            0x40400000,
            0x40800000,
            0x41100000,
            0x41800000,
            0x4F000000,
            0x7F7FFFFF,
            0x80800000,
            0xBF800000,
            0xFF7FFFFF,
            0x7F800000,
            0xFF800000,
            0x7F800001,
            0x7FC00000,
            0xFFC00001,
        ]
    )
    randomizer = random.Random(seed)
    cases.extend(randomizer.getrandbits(32) for _ in range(random_count))
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify generated rt_f_sqrt machine code against exact binary32 square root"
    )
    parser.add_argument("--random-cases", type=int, default=4096)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x5A7E)
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
    with tempfile.TemporaryDirectory(prefix="action-f-sqrt-") as temporary:
        work = Path(temporary)
        runtime_path = work / "rt_f_sqrt.bin"
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

    results = [int(line, 16) for line in completed.stdout.splitlines()]
    if len(results) != len(cases):
        raise SystemExit(f"expected {len(cases)} results, received {len(results)}")
    for index, (value, actual) in enumerate(zip(cases, results)):
        expected = expected_square_root(value)
        if actual != expected:
            raise SystemExit(
                f"case {index}: sqrt({value:08x}): "
                f"got {actual:08x}, expected {expected:08x}"
            )
    print(
        f"rt_f_sqrt {runtime_size} bytes: {len(cases)} exact "
        "exponent-boundary/edge/random cases passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
