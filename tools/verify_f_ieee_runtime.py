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
    addsub_core_module,
    addsub_wrapper_module,
    compare_module,
    link_runtime_builders,
    minmax_module,
    multiply_module,
    sign_module,
    special_value_module,
)


LOAD_ADDR = 0x2000
CANONICAL_QNAN = 0x7FC00000


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
    static uint8_t image[4096];
    FILE *runtime;
    M6502 *cpu;
    size_t image_size;
    unsigned left;
    unsigned right;
    int comparison;

    if (argc != 3) {
        return 2;
    }
    comparison = strcmp(argv[2], "compare") == 0;
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
    while (scanf("%x %x", &left, &right) == 2) {
        unsigned steps = 0;

        memcpy(memory + load_addr, image, image_size);
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
        while (cpu->registers->pc != stop_addr && steps++ < 200000) {
            M6502_run(cpu);
        }
        if (steps >= 200000) {
            fprintf(stderr, "runtime timeout for %08x %08x at pc=%04x\n",
                    left, right, cpu->registers->pc);
            M6502_delete(cpu);
            return 6;
        }
        if (comparison) {
            printf("%04x\n", ((unsigned)cpu->registers->x << 8) |
                              cpu->registers->a);
        } else {
            printf("%08x\n", get32(memory, result_addr));
        }
    }
    M6502_delete(cpu);
    return 0;
}
"""


def is_nan(bits: int) -> bool:
    return bits & 0x7F800000 == 0x7F800000 and bool(bits & 0x007FFFFF)


def is_infinity(bits: int) -> bool:
    return bits & 0x7FFFFFFF == 0x7F800000


def exact_finite(bits: int) -> Fraction:
    exponent = (bits >> 23) & 0xFF
    fraction = bits & 0x7FFFFF
    if exponent == 0:
        value = Fraction(fraction, 1 << 149)
    else:
        value = Fraction((1 << 23) | fraction, 1 << 23)
        if exponent >= 127:
            value *= 1 << (exponent - 127)
        else:
            value /= 1 << (127 - exponent)
    return -value if bits >> 31 else value


def round_nearest_even(value: Fraction) -> int:
    quotient, remainder = divmod(value.numerator, value.denominator)
    comparison = remainder * 2 - value.denominator
    return quotient + int(comparison > 0 or (comparison == 0 and quotient & 1))


def floor_log2(value: Fraction) -> int:
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    if (exponent >= 0 and value.numerator < value.denominator << exponent) or (
        exponent < 0 and value.numerator << -exponent < value.denominator
    ):
        exponent -= 1
    return exponent


def encode_finite(value: Fraction, zero_sign: int = 0) -> int:
    if value == 0:
        return zero_sign << 31
    sign = int(value < 0)
    magnitude = abs(value)
    exponent = floor_log2(magnitude)
    if exponent >= -126:
        scaled = (
            magnitude * (1 << (23 - exponent))
            if exponent <= 23
            else magnitude / (1 << (exponent - 23))
        )
        significand = round_nearest_even(scaled)
        if significand == 1 << 24:
            significand >>= 1
            exponent += 1
        if exponent > 127:
            return (sign << 31) | 0x7F800000
        if exponent >= -126:
            return (
                (sign << 31)
                | ((exponent + 127) << 23)
                | (significand & 0x7FFFFF)
            )

    fraction = round_nearest_even(magnitude * (1 << 149))
    if fraction == 0:
        return sign << 31
    if fraction >= 1 << 23:
        return (sign << 31) | 0x00800000
    return (sign << 31) | fraction


def expected_addsub(left: int, right: int, subtract: bool) -> int:
    effective_right = right ^ (0x80000000 if subtract else 0)
    if is_nan(left) or is_nan(effective_right):
        return CANONICAL_QNAN
    if is_infinity(left):
        if is_infinity(effective_right) and (left ^ effective_right) >> 31:
            return CANONICAL_QNAN
        return left & 0xFF800000
    if is_infinity(effective_right):
        return effective_right & 0xFF800000

    value = exact_finite(left) + exact_finite(effective_right)
    both_negative_zero = (
        left == 0x80000000 and effective_right == 0x80000000
    )
    return encode_finite(value, int(both_negative_zero))


def expected_multiply(left: int, right: int) -> int:
    if is_nan(left) or is_nan(right):
        return CANONICAL_QNAN
    sign = (left ^ right) >> 31
    left_zero = left & 0x7FFFFFFF == 0
    right_zero = right & 0x7FFFFFFF == 0
    if (is_infinity(left) and right_zero) or (is_infinity(right) and left_zero):
        return CANONICAL_QNAN
    if is_infinity(left) or is_infinity(right):
        return (sign << 31) | 0x7F800000
    if left_zero or right_zero:
        return sign << 31
    return encode_finite(exact_finite(left) * exact_finite(right))


def expected_compare(left: int, right: int) -> int:
    if is_nan(left) or is_nan(right):
        return 2
    if left & 0x7FFFFFFF == 0 and right & 0x7FFFFFFF == 0:
        return 0
    left_sign = left >> 31
    right_sign = right >> 31
    if left_sign != right_sign:
        return -1 if left_sign else 1
    left_magnitude = left & 0x7FFFFFFF
    right_magnitude = right & 0x7FFFFFFF
    if left_magnitude == right_magnitude:
        return 0
    magnitude_result = -1 if left_magnitude < right_magnitude else 1
    return -magnitude_result if left_sign else magnitude_result


def expected_minmax(left: int, right: int, *, maximum: bool) -> int:
    if is_nan(left):
        return right
    if is_nan(right):
        return left
    comparison = expected_compare(left, right)
    if (maximum and comparison < 0) or (not maximum and comparison > 0):
        return right
    return left


def expected_sign(value: int) -> int:
    if is_nan(value):
        return CANONICAL_QNAN
    if value & 0x7FFFFFFF == 0:
        return value
    return 0xBF800000 if value >> 31 else 0x3F800000


def runtime_builders(operation: str):
    special = special_value_module()
    if operation == "add":
        return [
            addsub_wrapper_module("rt_f_add", False),
            addsub_core_module(),
            special,
        ]
    if operation == "sub":
        return [
            addsub_wrapper_module("rt_f_sub", True),
            addsub_core_module(),
            special,
        ]
    if operation == "mul":
        return [multiply_module(), special]
    if operation == "cmp":
        return [compare_module(), special]
    if operation == "sign":
        return [sign_module()]
    if operation in ("min", "max"):
        return [
            minmax_module(f"rt_f_{operation}", maximum=operation == "max"),
            compare_module(),
            special,
        ]
    raise ValueError(operation)


def verification_cases(random_count: int, seed: int) -> list[tuple[int, int]]:
    edges = [
        0x00000000,
        0x80000000,
        0x00000001,
        0x007FFFFF,
        0x00800000,
        0x3F000000,
        0x3F800000,
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
    cases = [(left, right) for left in edges for right in edges]
    randomizer = random.Random(seed)
    cases.extend(
        (randomizer.getrandbits(32), randomizer.getrandbits(32))
        for _ in range(random_count)
    )
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify generated add/sub/mul/cmp/sign/min/max code against exact IEEE "
            "binary32"
        )
    )
    parser.add_argument("--random-cases", type=int, default=2048)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x1EEE754)
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
    with tempfile.TemporaryDirectory(prefix="action-f-ieee-") as temporary:
        work = Path(temporary)
        source_path = work / "verify.c"
        harness_path = work / "verify"
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

        for operation in ("add", "sub", "mul", "cmp", "sign", "min", "max"):
            runtime_path = work / f"rt_f_{operation}.bin"
            image = link_runtime_builders(runtime_builders(operation), LOAD_ADDR)
            runtime_path.write_bytes(image)
            completed = subprocess.run(
                [
                    str(harness_path),
                    str(runtime_path),
                    "compare" if operation == "cmp" else "value",
                ],
                input="".join(f"{left:08x} {right:08x}\n" for left, right in cases),
                text=True,
                capture_output=True,
                check=True,
            )
            results = [int(line, 16) for line in completed.stdout.splitlines()]
            if len(results) != len(cases):
                raise SystemExit(
                    f"{operation}: expected {len(cases)} results, received {len(results)}"
                )
            for index, ((left, right), actual) in enumerate(zip(cases, results)):
                if operation == "add":
                    expected = expected_addsub(left, right, False)
                elif operation == "sub":
                    expected = expected_addsub(left, right, True)
                elif operation == "mul":
                    expected = expected_multiply(left, right)
                elif operation == "cmp":
                    expected = expected_compare(left, right) & 0xFFFF
                elif operation == "sign":
                    expected = expected_sign(left)
                else:
                    expected = expected_minmax(
                        left, right, maximum=operation == "max"
                    )
                if actual != expected:
                    raise SystemExit(
                        f"{operation} case {index}: {left:08x}, {right:08x}: "
                        f"got {actual:08x}, expected {expected:08x}"
                    )
            print(
                f"rt_f_{operation} {len(image)} linked bytes: "
                f"{len(cases)} exact edge/random cases passed"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
