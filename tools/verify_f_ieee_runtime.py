#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import random
import shlex
import shutil
import struct
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path

from generate_math_runtime import (
    COS_COEFFICIENT_BITS,
    DEGREES_TO_RADIANS_BITS,
    EXP_COEFFICIENT_BITS,
    EXP_LN2_BITS,
    EXP_LOWER_BITS,
    EXP_UPPER_BITS,
    LN_INVERSE_SQRT2_BITS,
    LN10_BITS,
    LN_ODD_DENOMINATOR_BITS,
    LN_SQRT2_BITS,
    MATH_HALF_PI_BITS,
    MATH_NEG_HALF_PI_BITS,
    MATH_NEG_PI_BITS,
    MATH_PI_BITS,
    MATH_TWO_PI_BITS,
    RADIANS_TO_DEGREES_BITS,
    SIN_COEFFICIENT_BITS,
    abs_module,
    addsub_core_module,
    addsub_wrapper_module,
    ceil_module,
    compare_module,
    cos_module,
    deg_to_rad_module,
    clamp_module,
    divide_module,
    exp_module,
    floor_module,
    float_to_int_module,
    frac_module,
    hypot_module,
    link_runtime_builders,
    ln_module,
    log10_module,
    log2_module,
    minmax_module,
    mod_module,
    multiply_module,
    pow_module,
    rad_to_deg_module,
    round_module,
    sign_module,
    sin_module,
    special_value_module,
    square_root_module,
    trunc_module,
    wrap_pi_module,
)
from verify_f_div_runtime import expected_division
from verify_f_sqrt_runtime import expected_square_root


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
        left_addr = 0x5000,
        right_addr = 0x5010,
        upper_addr = 0x5020,
        result_addr = 0x5030,
        stop_addr = 0x1000,
    };
    static M6502_Memory memory;
    static M6502_Callbacks callbacks;
    static uint8_t image[8192];
    FILE *runtime;
    M6502 *cpu;
    size_t image_size;
    unsigned left;
    unsigned right;
    unsigned upper = 0;
    uint16_t destination;
    int comparison;
    int clamp;
    int alias_left;
    int alias_right;

    if (argc != 3) {
        return 2;
    }
    comparison = strcmp(argv[2], "compare") == 0;
    clamp = strcmp(argv[2], "clamp") == 0;
    alias_left = strcmp(argv[2], "alias") == 0;
    alias_right = strcmp(argv[2], "alias-right") == 0;
    destination = alias_left ? left_addr : alias_right ? right_addr : result_addr;
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
    for (;;) {
        unsigned steps = 0;
        int fields = clamp
            ? scanf("%x %x %x", &left, &right, &upper)
            : scanf("%x %x", &left, &right);

        if (fields != (clamp ? 3 : 2)) {
            break;
        }

        memcpy(memory + load_addr, image, image_size);
        memset(memory, 0, 0x100);
        put32(memory, left_addr, left);
        put32(memory, right_addr, right);
        put32(memory, upper_addr, upper);
        if (!alias_left && !alias_right) {
            put32(memory, result_addr, 0xccccccccu);
        }
        memory[0x02] = left_addr & 0xff;
        memory[0x03] = left_addr >> 8;
        memory[0x04] = right_addr & 0xff;
        memory[0x05] = right_addr >> 8;
        memory[0x06] = destination & 0xff;
        memory[0x07] = destination >> 8;
        memory[0x08] = upper_addr & 0xff;
        memory[0x09] = upper_addr >> 8;

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
            printf("%08x\n", get32(memory, destination));
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


def expected_trunc(value: int) -> int:
    exponent = (value >> 23) & 0xFF
    if exponent >= 150:
        return value
    if exponent < 127:
        return value & 0x80000000
    return value & ~((1 << (150 - exponent)) - 1)


def expected_floor(value: int) -> int:
    truncated = expected_trunc(value)
    if value >> 31 and truncated != value:
        if truncated & 0x7FFFFFFF == 0:
            return 0xBF800000
        exponent = (value >> 23) & 0xFF
        return truncated + (1 << (150 - exponent))
    return truncated


def expected_ceil(value: int) -> int:
    return expected_floor(value ^ 0x80000000) ^ 0x80000000


def expected_round(value: int) -> int:
    truncated = expected_trunc(value)
    if truncated == value:
        return value
    exponent = (value >> 23) & 0xFF
    if exponent < 126:
        return value & 0x80000000
    if exponent == 126:
        return (value & 0x80000000) | 0x3F800000
    fractional_bits = 150 - exponent
    if value & (1 << (fractional_bits - 1)):
        return truncated + (1 << fractional_bits)
    return truncated


def expected_frac(value: int) -> int:
    return expected_addsub(value, expected_trunc(value), True)


def expected_mod(value: int, divisor: int) -> int:
    if is_nan(value) or is_nan(divisor):
        return CANONICAL_QNAN
    if divisor & 0x7FFFFFFF == 0 or is_infinity(value):
        return CANONICAL_QNAN
    if is_infinity(divisor):
        return value
    quotient = expected_division(value, divisor)
    truncated = expected_trunc(quotient)
    product = expected_multiply(truncated, divisor)
    return expected_addsub(value, product, True)


def expected_hypot(left: int, right: int) -> int:
    left_abs = left & 0x7FFFFFFF
    right_abs = right & 0x7FFFFFFF
    largest = expected_minmax(left_abs, right_abs, maximum=True)
    smallest = expected_minmax(left_abs, right_abs, maximum=False)
    if largest == 0x7F800000 or largest == 0:
        return largest
    ratio = expected_division(smallest, largest)
    square = expected_multiply(ratio, ratio)
    total = expected_addsub(0x3F800000, square, False)
    root = expected_square_root(total)
    return expected_multiply(largest, root)


def expected_angle_scale(value: int, factor: int) -> int:
    return expected_multiply(value, factor)


def expected_clamp(value: int, lower: int, upper: int) -> int:
    if is_nan(value) or is_nan(lower) or is_nan(upper):
        return CANONICAL_QNAN
    if expected_compare(lower, upper) > 0:
        return CANONICAL_QNAN
    bounded_low = expected_minmax(value, lower, maximum=True)
    return expected_minmax(bounded_low, upper, maximum=False)


def expected_exp(value: int) -> int:
    if is_nan(value):
        return CANONICAL_QNAN
    if value == 0x7F800000 or expected_compare(value, EXP_UPPER_BITS) > 0:
        return 0x7F800000
    if value == 0xFF800000 or expected_compare(value, EXP_LOWER_BITS) < 0:
        return 0

    quotient = expected_division(value, EXP_LN2_BITS)
    exponent = expected_floor(quotient)
    count = int(exact_finite(exponent))
    product = expected_multiply(exponent, EXP_LN2_BITS)
    reduced = expected_addsub(value, product, True)
    result = EXP_COEFFICIENT_BITS[-1]
    for coefficient in reversed(EXP_COEFFICIENT_BITS[:-1]):
        result = expected_multiply(reduced, result)
        result = expected_addsub(coefficient, result, False)
    while count > 0:
        result = expected_addsub(result, result, False)
        count -= 1
    while count < 0:
        result = expected_division(result, 0x40000000)
        count += 1
    return result


def expected_ln(value: int) -> int:
    if is_nan(value) or expected_compare(value, 0) < 0:
        return CANONICAL_QNAN
    if value & 0x7FFFFFFF == 0:
        return 0xFF800000
    if value == 0x7F800000:
        return value

    exponent = 0
    reduced = value
    while expected_compare(reduced, LN_SQRT2_BITS) > 0:
        reduced = expected_division(reduced, 0x40000000)
        exponent = expected_addsub(exponent, 0x3F800000, False)
    while expected_compare(reduced, LN_INVERSE_SQRT2_BITS) < 0:
        reduced = expected_addsub(reduced, reduced, False)
        exponent = expected_addsub(exponent, 0x3F800000, True)

    numerator = expected_addsub(reduced, 0x3F800000, True)
    denominator = expected_addsub(reduced, 0x3F800000, False)
    z = expected_division(numerator, denominator)
    z2 = expected_multiply(z, z)
    term = z
    result = term
    for divisor in LN_ODD_DENOMINATOR_BITS:
        term = expected_multiply(term, z2)
        contribution = expected_division(term, divisor)
        result = expected_addsub(result, contribution, False)
    doubled = expected_addsub(result, result, False)
    exponent_term = expected_multiply(exponent, EXP_LN2_BITS)
    return expected_addsub(doubled, exponent_term, False)


def expected_logarithm(value: int, denominator: int) -> int:
    return expected_division(expected_ln(value), denominator)


def expected_pow(base: int, exponent: int) -> int:
    if is_nan(base) or is_nan(exponent):
        return CANONICAL_QNAN
    if exponent & 0x7FFFFFFF == 0:
        return 0x3F800000
    if base & 0x7FFFFFFF == 0:
        return 0x7F800000 if exponent >> 31 else base
    if expected_compare(base, 0) > 0:
        logarithm = expected_ln(base)
        return expected_exp(expected_multiply(exponent, logarithm))

    whole = expected_trunc(exponent)
    if expected_compare(whole, exponent) != 0:
        return CANONICAL_QNAN
    magnitude = expected_exp(
        expected_multiply(exponent, expected_ln(base & 0x7FFFFFFF))
    )
    parity = expected_mod(whole & 0x7FFFFFFF, 0x40000000)
    if expected_compare(parity, 0x3F800000) == 0:
        return expected_addsub(0, magnitude, True)
    return magnitude


def expected_wrap_pi(value: int) -> int:
    if is_nan(value) or value & 0x7FFFFFFF == 0x7F800000:
        return CANONICAL_QNAN
    result = expected_mod(value, MATH_TWO_PI_BITS)
    if expected_compare(result, MATH_PI_BITS) > 0:
        return expected_addsub(result, MATH_TWO_PI_BITS, True)
    if expected_compare(result, MATH_NEG_PI_BITS) < 0:
        return expected_addsub(result, MATH_TWO_PI_BITS, False)
    return result


def expected_sin(value: int) -> int:
    angle = expected_wrap_pi(value)
    if is_nan(angle):
        return CANONICAL_QNAN
    if expected_compare(angle, MATH_HALF_PI_BITS) > 0:
        folded = expected_addsub(MATH_PI_BITS, angle, True)
    elif expected_compare(angle, MATH_NEG_HALF_PI_BITS) < 0:
        folded = expected_addsub(MATH_NEG_PI_BITS, angle, True)
    else:
        folded = angle

    square = expected_multiply(folded, folded)
    accumulator = SIN_COEFFICIENT_BITS[-1]
    for coefficient in reversed(SIN_COEFFICIENT_BITS[:-1]):
        accumulator = expected_addsub(
            coefficient,
            expected_multiply(square, accumulator),
            False,
        )
    polynomial = expected_addsub(
        0x3F800000,
        expected_multiply(square, accumulator),
        False,
    )
    return expected_multiply(folded, polynomial)


def expected_cos(value: int) -> int:
    angle = expected_wrap_pi(value)
    if is_nan(angle):
        return CANONICAL_QNAN
    negate = False
    if expected_compare(angle, MATH_HALF_PI_BITS) > 0:
        folded = expected_addsub(MATH_PI_BITS, angle, True)
        negate = True
    elif expected_compare(angle, MATH_NEG_HALF_PI_BITS) < 0:
        folded = expected_addsub(MATH_NEG_PI_BITS, angle, True)
        negate = True
    else:
        folded = angle

    square = expected_multiply(folded, folded)
    accumulator = COS_COEFFICIENT_BITS[-1]
    for coefficient in reversed(COS_COEFFICIENT_BITS[:-1]):
        accumulator = expected_addsub(
            coefficient,
            expected_multiply(square, accumulator),
            False,
        )
    result = expected_addsub(
        0x3F800000,
        expected_multiply(square, accumulator),
        False,
    )
    return result ^ 0x80000000 if negate else result


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
    if operation == "trunc":
        return [trunc_module()]
    if operation == "floor":
        return [floor_module(), trunc_module()]
    if operation == "ceil":
        return [ceil_module(), floor_module(), trunc_module()]
    if operation == "round":
        return [round_module(), trunc_module()]
    if operation == "frac":
        return [
            frac_module(),
            trunc_module(),
            addsub_wrapper_module("rt_f_sub", True),
            addsub_core_module(),
            special,
        ]
    if operation == "mod":
        return [
            mod_module(),
            divide_module(),
            trunc_module(),
            multiply_module(),
            addsub_wrapper_module("rt_f_sub", True),
            addsub_core_module(),
            special,
        ]
    if operation == "hypot":
        return [
            hypot_module(),
            abs_module(),
            minmax_module("rt_f_min", maximum=False),
            minmax_module("rt_f_max", maximum=True),
            divide_module(),
            multiply_module(),
            addsub_wrapper_module("rt_f_add", False),
            addsub_core_module(),
            square_root_module(),
            compare_module(),
            special,
        ]
    if operation == "exp":
        return [
            exp_module(),
            divide_module(),
            floor_module(),
            trunc_module(),
            float_to_int_module(),
            multiply_module(),
            addsub_wrapper_module("rt_f_sub", True),
            addsub_wrapper_module("rt_f_add", False),
            addsub_core_module(),
            special,
        ]
    if operation == "ln":
        return [
            ln_module(),
            divide_module(),
            multiply_module(),
            addsub_wrapper_module("rt_f_sub", True),
            addsub_wrapper_module("rt_f_add", False),
            addsub_core_module(),
            special,
        ]
    if operation in ("log2", "log10"):
        return [
            log2_module() if operation == "log2" else log10_module(),
            ln_module(),
            divide_module(),
            multiply_module(),
            addsub_wrapper_module("rt_f_sub", True),
            addsub_wrapper_module("rt_f_add", False),
            addsub_core_module(),
            special,
        ]
    if operation == "pow":
        return [
            pow_module(),
            ln_module(),
            exp_module(),
            mod_module(),
            floor_module(),
            trunc_module(),
            float_to_int_module(),
            divide_module(),
            multiply_module(),
            addsub_wrapper_module("rt_f_sub", True),
            addsub_wrapper_module("rt_f_add", False),
            addsub_core_module(),
            special,
        ]
    if operation in ("wrap_pi", "sin", "cos"):
        builders = []
        if operation == "sin":
            builders.append(sin_module())
        elif operation == "cos":
            builders.append(cos_module())
        builders.extend(
            [
                wrap_pi_module(),
                mod_module(),
                divide_module(),
                trunc_module(),
                multiply_module(),
                compare_module(),
                addsub_wrapper_module("rt_f_sub", True),
                addsub_wrapper_module("rt_f_add", False),
                addsub_core_module(),
                special,
            ]
        )
        return builders
    if operation == "deg_to_rad":
        return [deg_to_rad_module(), multiply_module(), special]
    if operation == "rad_to_deg":
        return [rad_to_deg_module(), multiply_module(), special]
    if operation in ("min", "max"):
        return [
            minmax_module(f"rt_f_{operation}", maximum=operation == "max"),
            compare_module(),
            special,
        ]
    if operation == "clamp":
        return [
            clamp_module(),
            minmax_module("rt_f_min", maximum=False),
            minmax_module("rt_f_max", maximum=True),
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
    # Unary rounding needs explicit half-way, near-half, and large-integral
    # values that are too sparse to rely on the random 32-bit stream to hit.
    round_edges = [
        0x3E800000,  # 0.25
        0x3F400000,  # 0.75
        0x3FC00000,  # 1.5
        0x40200000,  # 2.5
        0x4AFFFFFF,  # 8388607.5
        0x4B000001,  # 8388609, integral despite unit spacing
    ]
    cases.extend(
        (value, 0)
        for magnitude in round_edges
        for value in (magnitude, magnitude | 0x80000000)
    )
    randomizer = random.Random(seed)
    cases.extend(
        (randomizer.getrandbits(32), randomizer.getrandbits(32))
        for _ in range(random_count)
    )
    return cases


def verification_clamp_cases(
    random_count: int, seed: int
) -> list[tuple[int, int, int]]:
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
    cases = [
        (value, lower, upper)
        for value in edges
        for lower in edges
        for upper in edges
    ]
    randomizer = random.Random(seed ^ 0xC1A0)
    cases.extend(
        (
            randomizer.getrandbits(32),
            randomizer.getrandbits(32),
            randomizer.getrandbits(32),
        )
        for _ in range(random_count)
    )
    return cases


def verification_exp_cases(
    random_count: int, seed: int
) -> list[tuple[int, int]]:
    values = [
        0x00000000,
        0x80000000,
        0x00000001,
        0x007FFFFF,
        0x00800000,
        0x3F800000,
        0xBF800000,
        0x7F800000,
        0xFF800000,
        0x7F800001,
        0x7FC00000,
        0xFFC00001,
        0xFF7FFFFF,
        EXP_UPPER_BITS - 1,
        EXP_UPPER_BITS,
        EXP_UPPER_BITS + 1,
        EXP_LOWER_BITS - 1,
        EXP_LOWER_BITS,
        EXP_LOWER_BITS + 1,
    ]
    values.extend(
        int.from_bytes(struct.pack("<f", value), "little")
        for value in (-100.0, -10.0, -0.5, -0.1, 0.1, 0.5, 10.0, 80.0)
    )
    randomizer = random.Random(seed ^ 0xE7)
    values.extend(
        int.from_bytes(
            struct.pack("<f", randomizer.uniform(-103.97208404541016, 88.72283935546875)),
            "little",
        )
        for _ in range(random_count)
    )
    return [(value, 0) for value in values]


def verification_ln_cases(
    random_count: int, seed: int
) -> list[tuple[int, int]]:
    values = [
        0x00000000,
        0x80000000,
        0x00000001,
        0x007FFFFF,
        0x00800000,
        LN_INVERSE_SQRT2_BITS - 1,
        LN_INVERSE_SQRT2_BITS,
        LN_INVERSE_SQRT2_BITS + 1,
        0x3F800000,
        LN_SQRT2_BITS - 1,
        LN_SQRT2_BITS,
        LN_SQRT2_BITS + 1,
        0x40000000,
        0x7F7FFFFF,
        0x7F800000,
        0xFF800000,
        0xBF800000,
        0xFF7FFFFF,
        0x7F800001,
        0x7FC00000,
        0xFFC00001,
    ]
    values.extend(
        int.from_bytes(struct.pack("<f", value), "little")
        for value in (0.1, 0.5, 3.0, 10.0, 100.0)
    )
    randomizer = random.Random(seed ^ 0x1A)
    while len(values) < 26 + random_count:
        value = randomizer.getrandbits(31)
        if (value >> 23) & 0xFF != 0xFF:
            values.append(value)
    return [(value, 0) for value in values]


def verification_pow_cases(
    random_count: int, seed: int
) -> list[tuple[int, int]]:
    values = [
        0x00000000,
        0x80000000,
        0x3F800000,
        0xBF800000,
        0x40000000,
        0xC0000000,
        0x7F7FFFFF,
        0xFF7FFFFF,
        0x7F800000,
        0xFF800000,
        0x7F800001,
        0x7FC00000,
        0xFFC00001,
    ]
    exponents = values + [
        int.from_bytes(struct.pack("<f", value), "little")
        for value in (
            -31.0,
            -4.0,
            -3.0,
            -2.5,
            -2.0,
            -1.0,
            0.5,
            2.0,
            3.0,
            4.0,
            31.0,
        )
    ]
    cases = [(base, exponent) for base in values for exponent in exponents]
    randomizer = random.Random(seed ^ 0xF00)
    for index in range(random_count):
        if index & 1:
            base_value = randomizer.uniform(-32.0, 32.0)
            exponent_value = randomizer.randint(-32, 32)
        else:
            base_value = randomizer.uniform(0.0001, 32.0)
            exponent_value = randomizer.uniform(-32.0, 32.0)
        cases.append(
            (
                int.from_bytes(struct.pack("<f", base_value), "little"),
                int.from_bytes(struct.pack("<f", exponent_value), "little"),
            )
        )
    return cases


def verification_trig_cases(
    random_count: int, seed: int
) -> list[tuple[int, int]]:
    values = [
        0x00000000,
        0x80000000,
        0x00000001,
        0x007FFFFF,
        0x00800000,
        MATH_NEG_PI_BITS,
        MATH_NEG_HALF_PI_BITS,
        MATH_HALF_PI_BITS,
        MATH_PI_BITS,
        MATH_TWO_PI_BITS,
        MATH_NEG_PI_BITS - 1,
        MATH_NEG_PI_BITS + 1,
        MATH_NEG_HALF_PI_BITS - 1,
        MATH_NEG_HALF_PI_BITS + 1,
        MATH_HALF_PI_BITS - 1,
        MATH_HALF_PI_BITS + 1,
        MATH_PI_BITS - 1,
        MATH_PI_BITS + 1,
        MATH_TWO_PI_BITS - 1,
        MATH_TWO_PI_BITS + 1,
        0x7F7FFFFF,
        0xFF7FFFFF,
        0x7F800000,
        0xFF800000,
        0x7F800001,
        0x7FC00000,
        0xFFC00001,
    ]
    values.extend(
        int.from_bytes(struct.pack("<f", value), "little")
        for value in (
            -1000.0,
            -10.0,
            -7.0,
            -4.0,
            -0.5,
            0.5,
            0.7853981633974483,
            2.0,
            4.0,
            7.0,
            10.0,
            1000.0,
        )
    )
    randomizer = random.Random(seed ^ 0x51A)
    values.extend(randomizer.getrandbits(32) for _ in range(random_count))
    return [(value, 0) for value in values]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify generated add/sub/mul/cmp/sign/trunc/floor/ceil/round/frac/mod/hypot/exp/ln/log2/log10/pow/wrap/sin/cos/angle/min/max/clamp code against exact IEEE "
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
    clamp_cases = verification_clamp_cases(args.random_cases, args.seed)
    exp_cases = verification_exp_cases(args.random_cases, args.seed)
    ln_cases = verification_ln_cases(args.random_cases, args.seed)
    pow_cases = verification_pow_cases(args.random_cases, args.seed)
    trig_cases = verification_trig_cases(args.random_cases, args.seed)
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

        for operation in (
            "add",
            "sub",
            "mul",
            "cmp",
            "sign",
            "trunc",
            "floor",
            "ceil",
            "round",
            "frac",
            "mod",
            "hypot",
            "exp",
            "ln",
            "log2",
            "log10",
            "pow",
            "wrap_pi",
            "sin",
            "cos",
            "deg_to_rad",
            "rad_to_deg",
            "min",
            "max",
            "clamp",
        ):
            operation_cases = (
                clamp_cases
                if operation == "clamp"
                else exp_cases
                if operation == "exp"
                else ln_cases
                if operation in ("ln", "log2", "log10")
                else pow_cases
                if operation == "pow"
                else trig_cases
                if operation in ("wrap_pi", "sin", "cos")
                else cases
            )
            runtime_path = work / f"rt_f_{operation}.bin"
            image = link_runtime_builders(runtime_builders(operation), LOAD_ADDR)
            runtime_path.write_bytes(image)
            completed = subprocess.run(
                [
                    str(harness_path),
                    str(runtime_path),
                    "compare"
                    if operation == "cmp"
                    else "clamp"
                    if operation == "clamp"
                    else "value",
                ],
                input="".join(
                    " ".join(f"{value:08x}" for value in case) + "\n"
                    for case in operation_cases
                ),
                text=True,
                capture_output=True,
                check=True,
            )
            results = [int(line, 16) for line in completed.stdout.splitlines()]
            if len(results) != len(operation_cases):
                raise SystemExit(
                    f"{operation}: expected {len(operation_cases)} results, "
                    f"received {len(results)}"
                )
            for index, (case, actual) in enumerate(zip(operation_cases, results)):
                left, right = case[:2]
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
                elif operation == "trunc":
                    expected = expected_trunc(left)
                elif operation == "floor":
                    expected = expected_floor(left)
                elif operation == "ceil":
                    expected = expected_ceil(left)
                elif operation == "round":
                    expected = expected_round(left)
                elif operation == "frac":
                    expected = expected_frac(left)
                elif operation == "mod":
                    expected = expected_mod(left, right)
                elif operation == "hypot":
                    expected = expected_hypot(left, right)
                elif operation == "exp":
                    expected = expected_exp(left)
                elif operation == "ln":
                    expected = expected_ln(left)
                elif operation == "log2":
                    expected = expected_logarithm(left, EXP_LN2_BITS)
                elif operation == "log10":
                    expected = expected_logarithm(left, LN10_BITS)
                elif operation == "pow":
                    expected = expected_pow(left, right)
                elif operation == "wrap_pi":
                    expected = expected_wrap_pi(left)
                elif operation == "sin":
                    expected = expected_sin(left)
                elif operation == "cos":
                    expected = expected_cos(left)
                elif operation == "deg_to_rad":
                    expected = expected_angle_scale(
                        left, DEGREES_TO_RADIANS_BITS
                    )
                elif operation == "rad_to_deg":
                    expected = expected_angle_scale(
                        left, RADIANS_TO_DEGREES_BITS
                    )
                elif operation == "clamp":
                    expected = expected_clamp(left, right, case[2])
                else:
                    expected = expected_minmax(
                        left, right, maximum=operation == "max"
                    )
                if actual != expected:
                    raise SystemExit(
                        f"{operation} case {index}: "
                        f"{', '.join(f'{value:08x}' for value in case)}: "
                        f"got {actual:08x}, expected {expected:08x}"
                    )
            print(
                f"rt_f_{operation} {len(image)} linked bytes: "
                f"{len(operation_cases)} exact edge/random cases passed"
            )
            if operation in (
                "sign",
                "trunc",
                "floor",
                "ceil",
                "round",
                "frac",
                "mod",
                "hypot",
                "exp",
                "ln",
                "log2",
                "log10",
                "pow",
                "wrap_pi",
                "sin",
                "cos",
                "deg_to_rad",
                "rad_to_deg",
            ):
                alias_completed = subprocess.run(
                    [str(harness_path), str(runtime_path), "alias"],
                    input="".join(
                        f"{left:08x} {right:08x}\n"
                        for left, right in operation_cases
                    ),
                    text=True,
                    capture_output=True,
                    check=True,
                )
                alias_results = [
                    int(line, 16) for line in alias_completed.stdout.splitlines()
                ]
                for index, ((left, right), actual) in enumerate(
                    zip(operation_cases, alias_results)
                ):
                    expected = (
                        expected_sign(left)
                        if operation == "sign"
                        else expected_trunc(left)
                        if operation == "trunc"
                        else expected_floor(left)
                        if operation == "floor"
                        else expected_ceil(left)
                        if operation == "ceil"
                        else expected_round(left)
                        if operation == "round"
                        else expected_frac(left)
                        if operation == "frac"
                        else expected_mod(left, right)
                        if operation == "mod"
                        else expected_exp(left)
                        if operation == "exp"
                        else expected_ln(left)
                        if operation == "ln"
                        else expected_logarithm(left, EXP_LN2_BITS)
                        if operation == "log2"
                        else expected_logarithm(left, LN10_BITS)
                        if operation == "log10"
                        else expected_pow(left, right)
                        if operation == "pow"
                        else expected_wrap_pi(left)
                        if operation == "wrap_pi"
                        else expected_sin(left)
                        if operation == "sin"
                        else expected_cos(left)
                        if operation == "cos"
                        else expected_angle_scale(
                            left, DEGREES_TO_RADIANS_BITS
                        )
                        if operation == "deg_to_rad"
                        else expected_angle_scale(
                            left, RADIANS_TO_DEGREES_BITS
                        )
                        if operation == "rad_to_deg"
                        else expected_hypot(left, right)
                    )
                    if actual != expected:
                        raise SystemExit(
                            f"{operation} alias case {index}: {left:08x}: "
                            f"got {actual:08x}, expected {expected:08x}"
                        )
                print(
                    f"rt_f_{operation} {len(alias_results)} in-place alias cases passed"
                )
                if operation in ("mod", "hypot", "pow"):
                    alias_right_completed = subprocess.run(
                        [str(harness_path), str(runtime_path), "alias-right"],
                        input="".join(
                            f"{left:08x} {right:08x}\n"
                            for left, right in operation_cases
                        ),
                        text=True,
                        capture_output=True,
                        check=True,
                    )
                    alias_right_results = [
                        int(line, 16)
                        for line in alias_right_completed.stdout.splitlines()
                    ]
                    for index, ((left, right), actual) in enumerate(
                        zip(operation_cases, alias_right_results)
                    ):
                        expected = (
                            expected_mod(left, right)
                            if operation == "mod"
                            else expected_pow(left, right)
                            if operation == "pow"
                            else expected_hypot(left, right)
                        )
                        if actual != expected:
                            raise SystemExit(
                                f"{operation} right-alias case {index}: "
                                f"{left:08x} {right:08x}: got {actual:08x}, "
                                f"expected {expected:08x}"
                            )
                    print(
                        f"rt_f_{operation} "
                        f"{len(alias_right_results)} right-operand alias cases passed"
                    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
