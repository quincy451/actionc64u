#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import random
import shlex
import shutil
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path

from generate_math_runtime import (
    divide_module,
    link_runtime_builders,
    special_value_module,
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
        left_addr = 0x3000,
        right_addr = 0x3010,
        result_addr = 0x3020,
        stop_addr = 0x1000,
    };
    static M6502_Memory memory;
    static M6502_Callbacks callbacks;
    FILE *runtime;
    M6502 *cpu;
    unsigned left;
    unsigned right;

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
    while (scanf("%x %x", &left, &right) == 2) {
        unsigned steps = 0;

        memset(memory, 0, 0x100);
        put32(memory, left_addr, left);
        put32(memory, right_addr, right);
        put32(memory, result_addr, 0xccccccccu);
        memory[0x02] = left_addr & 0xff;
        memory[0x03] = left_addr >> 8;
        memory[0x04] = right_addr & 0xff;
        memory[0x05] = right_addr >> 8;
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
            fprintf(stderr, "runtime timeout for %08x / %08x at pc=%04x\n",
                    left, right, cpu->registers->pc);
            M6502_delete(cpu);
            return 6;
        }
        printf("%08x\n", get32(memory, result_addr));
    }
    M6502_delete(cpu);
    return 0;
}
"""


def decode_binary32(bits: int) -> tuple[int, int, Fraction | None]:
    sign = bits >> 31
    exponent = (bits >> 23) & 0xFF
    fraction = bits & 0x7FFFFF
    if exponent == 0xFF:
        return sign, exponent, None
    if exponent == 0:
        return sign, exponent, Fraction(fraction, 1 << 149)
    value = Fraction((1 << 23) | fraction, 1 << 23)
    if exponent >= 127:
        value *= 1 << (exponent - 127)
    else:
        value /= 1 << (127 - exponent)
    return sign, exponent, value


def round_nearest_even(value: Fraction) -> int:
    quotient, remainder = divmod(value.numerator, value.denominator)
    comparison = remainder * 2 - value.denominator
    return quotient + int(comparison > 0 or (comparison == 0 and quotient & 1))


def expected_division(left_bits: int, right_bits: int) -> int:
    left_sign, left_exponent, left = decode_binary32(left_bits)
    right_sign, right_exponent, right = decode_binary32(right_bits)
    result_sign = left_sign ^ right_sign
    left_fraction = left_bits & 0x7FFFFF
    right_fraction = right_bits & 0x7FFFFF

    if (left_exponent == 0xFF and left_fraction) or (
        right_exponent == 0xFF and right_fraction
    ):
        return 0x7FC00000
    if left_exponent == 0xFF:
        return 0x7FC00000 if right_exponent == 0xFF else (result_sign << 31) | 0x7F800000
    if right_exponent == 0xFF:
        return result_sign << 31
    assert left is not None and right is not None
    if right == 0:
        return 0x7FC00000 if left == 0 else (result_sign << 31) | 0x7F800000
    if left == 0:
        return result_sign << 31

    value = left / right
    numerator = value.numerator
    denominator = value.denominator
    exponent = numerator.bit_length() - denominator.bit_length()
    if (exponent >= 0 and numerator < denominator << exponent) or (
        exponent < 0 and numerator << -exponent < denominator
    ):
        exponent -= 1

    if exponent >= -126:
        if exponent <= 23:
            scaled = value * (1 << (23 - exponent))
        else:
            scaled = value / (1 << (exponent - 23))
        significand = round_nearest_even(scaled)
        if significand == 1 << 24:
            significand >>= 1
            exponent += 1
        if exponent > 127:
            return (result_sign << 31) | 0x7F800000
        if exponent >= -126:
            return (
                (result_sign << 31)
                | ((exponent + 127) << 23)
                | (significand & 0x7FFFFF)
            )

    fraction = round_nearest_even(value * (1 << 149))
    if fraction == 0:
        return result_sign << 31
    if fraction >= 1 << 23:
        return (result_sign << 31) | (1 << 23)
    return (result_sign << 31) | fraction


def write_runtime(path: Path) -> int:
    image = link_runtime_builders(
        [divide_module(), special_value_module()], LOAD_ADDR
    )
    path.write_bytes(image)
    return len(image)


def verification_cases(random_count: int, seed: int) -> list[tuple[int, int]]:
    edges = [
        0x00000000,
        0x80000000,
        0x00000001,
        0x00000002,
        0x00000003,
        0x007FFFFF,
        0x00800000,
        0x00800001,
        0x3F000000,
        0x3F800000,
        0x3FC00000,
        0x40000000,
        0x7F7FFFFF,
        0x80800000,
        0xBF800000,
            0xFF7FFFFF,
            0x7F800000,
            0xFF800000,
            0x7F800001,
            0x7FC00001,
            0xFFC00001,
    ]
    cases = [(left, right) for left in edges for right in edges]
    randomizer = random.Random(seed)
    cases.extend(
        (randomizer.getrandbits(32), randomizer.getrandbits(32))
        for _ in range(random_count)
    )
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify generated rt_f_div machine code against exact binary32 division"
    )
    parser.add_argument("--random-cases", type=int, default=4096)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0xD1A1DE)
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
    with tempfile.TemporaryDirectory(prefix="action-f-div-") as temporary:
        work = Path(temporary)
        runtime_path = work / "rt_f_div.bin"
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
            input="".join(f"{left:08x} {right:08x}\n" for left, right in cases),
            text=True,
            capture_output=True,
            check=True,
        )

    results = [int(line, 16) for line in completed.stdout.splitlines()]
    if len(results) != len(cases):
        raise SystemExit(f"expected {len(cases)} results, received {len(results)}")
    for index, ((left, right), actual) in enumerate(zip(cases, results)):
        expected = expected_division(left, right)
        if actual != expected:
            raise SystemExit(
                f"case {index}: {left:08x} / {right:08x}: "
                f"got {actual:08x}, expected {expected:08x}"
            )
    print(
        f"rt_f_div {runtime_size} bytes: {len(cases)} exact edge/random cases passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
