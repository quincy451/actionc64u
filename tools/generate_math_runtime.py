#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
from fractions import Fraction
from pathlib import Path

from generate_exact_print_runtime import print_float_module
from generate_reu_runtime import ObjectBuilder


_INVERSE_BRANCH = {
    0x10: 0x30,  # BPL / BMI
    0x30: 0x10,
    0x50: 0x70,  # BVC / BVS
    0x70: 0x50,
    0x90: 0xB0,  # BCC / BCS
    0xB0: 0x90,
    0xD0: 0xF0,  # BNE / BEQ
    0xF0: 0xD0,
}


SPECIAL_ADD = 0x00
SPECIAL_SUB = 0x80
SPECIAL_MUL = 0x01
SPECIAL_DIV = 0x02
SPECIAL_SQRT = 0x03
SPECIAL_STORE_INFINITY = 0x04
SPECIAL_COMPARE = 0x05
ALINK_SYMBOL_MAX = 23


def far_branch(builder: ObjectBuilder, opcode: int, target: str, tag: str) -> None:
    """Emit a conditional branch through a relocatable local JMP."""
    skip = f"far_{tag}_{len(builder.code)}"
    builder.branch(_INVERSE_BRANCH[opcode], skip)
    builder.jmp_local(target)
    builder.label(skip)


def binary32_power10_ceiling(exponent: int) -> int:
    """Return the least positive binary32 bit pattern not below 10**exponent."""
    target = (
        Fraction(10**exponent, 1)
        if exponent >= 0
        else Fraction(1, 10 ** -exponent)
    )
    bits = int.from_bytes(struct.pack("<f", float(target)), "little")
    raw_exponent = (bits >> 23) & 0xFF
    fraction = bits & 0x7FFFFF
    if raw_exponent == 0:
        represented = Fraction(fraction, 1 << 149)
    else:
        represented = Fraction((1 << 23) | fraction, 1 << 23)
        if raw_exponent >= 127:
            represented *= 1 << (raw_exponent - 127)
        else:
            represented /= 1 << (127 - raw_exponent)
    if represented < target:
        bits += 1
    return bits


def special_value_module() -> ObjectBuilder:
    """Build shared IEEE-754 binary32 exceptional-value handling."""
    b = ObjectBuilder("rt_f_special")

    operation = 0x08
    class_a = 0x09
    class_b = 0x0A
    sign_a = 0x0B
    sign_b = 0x0C
    result_sign = 0x0D
    value_ptr = 0x0E
    raw_exponent = 0x10
    fraction_high = 0x11
    scratch = 0x12

    value_finite = 0
    value_zero = 1
    value_infinity = 2
    value_nan = 3

    # A selects the operation. A set carry means the final result is complete;
    # clear carry asks the caller to continue through its finite arithmetic core.
    b.zero_page(0x85, operation)
    b.immediate(0xC9, SPECIAL_STORE_INFINITY)
    b.branch(0xD0, "classify_a")
    b.zero_page(0x86, result_sign)
    b.jmp_local("write_inf")

    b.label("classify_a")
    b.immediate(0xA2, 0x02)
    b.local_reference(0x20, "classify")
    b.zero_page(0x85, class_a)
    b.zero_page(0x86, sign_a)
    b.zero_page(0xA5, operation)
    b.immediate(0xC9, SPECIAL_SQRT)
    far_branch(b, 0xF0, "sqrt", "special_sqrt")

    b.immediate(0xA2, 0x04)
    b.local_reference(0x20, "classify")
    b.zero_page(0x85, class_b)
    b.zero_page(0x86, sign_b)

    # NaNs take precedence over every binary operation. Comparisons report the
    # otherwise-unused signed result value 2 to mean unordered.
    b.zero_page(0xA5, class_a)
    b.immediate(0xC9, value_nan)
    b.branch(0xF0, "nan_input")
    b.zero_page(0xA5, class_b)
    b.immediate(0xC9, value_nan)
    b.branch(0xF0, "nan_input")
    b.zero_page(0xA5, operation)
    b.immediate(0xC9, SPECIAL_COMPARE)
    far_branch(b, 0xF0, "finite", "ordered_compare")
    b.immediate(0x29, 0x7F)
    b.branch(0xF0, "addsub")
    b.immediate(0xC9, SPECIAL_MUL)
    far_branch(b, 0xF0, "multiply", "special_multiply")
    b.jmp_local("divide")

    b.label("nan_input")
    b.zero_page(0xA5, operation)
    b.immediate(0xC9, SPECIAL_COMPARE)
    far_branch(b, 0xD0, "store_qnan", "arithmetic_nan")
    b.immediate(0xA9, 0x02)
    b.immediate(0xA2, 0x00)
    b.emit(0x38, 0x60)  # SEC; RTS

    # Addition/subtraction applies the wrapper's sign toggle before resolving
    # infinity plus or minus infinity.
    b.label("addsub")
    b.zero_page(0xA5, sign_b)
    b.zero_page(0x45, operation)
    b.zero_page(0x85, sign_b)
    b.zero_page(0xA5, class_a)
    b.immediate(0xC9, value_infinity)
    b.branch(0xD0, "addsub_check_b")
    b.zero_page(0xA5, class_b)
    b.immediate(0xC9, value_infinity)
    b.branch(0xD0, "infinity_a")
    b.zero_page(0xA5, sign_a)
    b.zero_page(0x45, sign_b)
    far_branch(b, 0xD0, "store_qnan", "opposite_infinities")
    b.label("infinity_a")
    b.zero_page(0xA5, sign_a)
    b.zero_page(0x85, result_sign)
    b.jmp_local("write_inf")
    b.label("addsub_check_b")
    b.zero_page(0xA5, class_b)
    b.immediate(0xC9, value_infinity)
    far_branch(b, 0xD0, "finite", "addsub_finite")
    b.zero_page(0xA5, sign_b)
    b.zero_page(0x85, result_sign)
    b.jmp_local("write_inf")

    b.label("multiply")
    b.zero_page(0xA5, sign_a)
    b.zero_page(0x45, sign_b)
    b.zero_page(0x85, result_sign)
    b.zero_page(0xA5, class_a)
    b.immediate(0xC9, value_infinity)
    b.branch(0xD0, "multiply_check_b")
    b.zero_page(0xA5, class_b)
    b.immediate(0xC9, value_zero)
    b.branch(0xF0, "store_qnan")
    b.jmp_local("write_inf")
    b.label("multiply_check_b")
    b.zero_page(0xA5, class_b)
    b.immediate(0xC9, value_infinity)
    far_branch(b, 0xD0, "finite", "multiply_finite")
    b.zero_page(0xA5, class_a)
    b.immediate(0xC9, value_zero)
    b.branch(0xF0, "store_qnan")
    b.jmp_local("write_inf")

    b.label("divide")
    b.zero_page(0xA5, sign_a)
    b.zero_page(0x45, sign_b)
    b.zero_page(0x85, result_sign)
    b.zero_page(0xA5, class_a)
    b.immediate(0xC9, value_infinity)
    b.branch(0xD0, "divide_check_b")
    b.zero_page(0xA5, class_b)
    b.immediate(0xC9, value_infinity)
    b.branch(0xF0, "store_qnan")
    b.jmp_local("write_inf")
    b.label("divide_check_b")
    b.zero_page(0xA5, class_b)
    b.immediate(0xC9, value_infinity)
    b.branch(0xF0, "store_signed_zero")
    b.immediate(0xC9, value_zero)
    far_branch(b, 0xD0, "finite", "divide_finite")
    b.zero_page(0xA5, class_a)
    b.immediate(0xC9, value_zero)
    b.branch(0xF0, "store_qnan")
    b.jmp_local("write_inf")

    b.label("sqrt")
    b.zero_page(0xA5, class_a)
    b.immediate(0xC9, value_nan)
    b.branch(0xF0, "store_qnan")
    b.zero_page(0xA5, sign_a)
    b.branch(0x10, "sqrt_nonnegative")
    b.zero_page(0xA5, class_a)
    b.immediate(0xC9, value_zero)
    b.branch(0xF0, "finite")
    b.jmp_local("store_qnan")
    b.label("sqrt_nonnegative")
    b.zero_page(0xA5, class_a)
    b.immediate(0xC9, value_infinity)
    b.branch(0xD0, "finite")
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, result_sign)
    b.jmp_local("write_inf")

    b.label("finite")
    b.emit(0x18, 0x60)  # CLC; RTS

    b.label("store_qnan")
    b.immediate(0xA0, 0x00)
    b.immediate(0xA9, 0x00)
    b.emit(0x91, 0x06, 0xC8, 0x91, 0x06, 0xC8)
    b.immediate(0xA9, 0xC0)
    b.emit(0x91, 0x06, 0xC8)
    b.immediate(0xA9, 0x7F)
    b.emit(0x91, 0x06, 0x38, 0x60)

    b.label("write_inf")
    b.immediate(0xA0, 0x00)
    b.immediate(0xA9, 0x00)
    b.emit(0x91, 0x06, 0xC8, 0x91, 0x06, 0xC8)
    b.immediate(0xA9, 0x80)
    b.emit(0x91, 0x06, 0xC8)
    b.zero_page(0xA5, result_sign)
    b.immediate(0x09, 0x7F)
    b.emit(0x91, 0x06, 0x38, 0x60)

    b.label("store_signed_zero")
    b.immediate(0xA0, 0x00)
    b.immediate(0xA9, 0x00)
    b.emit(0x91, 0x06, 0xC8, 0x91, 0x06, 0xC8, 0x91, 0x06, 0xC8)
    b.zero_page(0xA5, result_sign)
    b.emit(0x91, 0x06, 0x38, 0x60)

    # X identifies one of the public source pointers ($02 or $04). Return the
    # class in A and the sign bit in X without modifying either source pointer.
    b.label("classify")
    b.emit(0xB5, 0x00)  # LDA $00,X
    b.zero_page(0x85, value_ptr)
    b.emit(0xE8, 0xB5, 0x00)  # INX; LDA $00,X
    b.zero_page(0x85, value_ptr + 1)
    b.immediate(0xA0, 0x03)
    b.emit(0xB1, value_ptr)
    b.immediate(0x29, 0x80)
    b.zero_page(0x85, result_sign)
    b.emit(0xB1, value_ptr)
    b.immediate(0x29, 0x7F)
    b.emit(0x0A)
    b.zero_page(0x85, raw_exponent)
    b.emit(0x88, 0xB1, value_ptr)  # DEY; LDA (value_ptr),Y
    b.zero_page(0x85, fraction_high)
    b.immediate(0x29, 0x80)
    b.branch(0xF0, "classify_exponent_ready")
    b.zero_page(0xE6, raw_exponent)
    b.label("classify_exponent_ready")
    b.zero_page(0xA5, raw_exponent)
    b.immediate(0xC9, 0xFF)
    b.branch(0xF0, "classify_nonfinite")
    b.zero_page(0xA5, raw_exponent)
    b.branch(0xD0, "classify_finite")
    b.zero_page(0xA5, fraction_high)
    b.immediate(0x29, 0x7F)
    b.zero_page(0x85, scratch)
    b.emit(0x88, 0xB1, value_ptr)
    b.zero_page(0x05, scratch)
    b.zero_page(0x85, scratch)
    b.emit(0x88, 0xB1, value_ptr)
    b.zero_page(0x05, scratch)
    b.branch(0xD0, "classify_finite")
    b.immediate(0xA9, value_zero)
    b.branch(0xD0, "classify_done")
    b.label("classify_nonfinite")
    b.zero_page(0xA5, fraction_high)
    b.immediate(0x29, 0x7F)
    b.zero_page(0x85, scratch)
    b.emit(0x88, 0xB1, value_ptr)
    b.zero_page(0x05, scratch)
    b.zero_page(0x85, scratch)
    b.emit(0x88, 0xB1, value_ptr)
    b.zero_page(0x05, scratch)
    b.branch(0xF0, "classify_infinity")
    b.immediate(0xA9, value_nan)
    b.branch(0xD0, "classify_done")
    b.label("classify_infinity")
    b.immediate(0xA9, value_infinity)
    b.branch(0xD0, "classify_done")
    b.label("classify_finite")
    b.immediate(0xA9, value_finite)
    b.label("classify_done")
    b.zero_page(0xA6, result_sign)
    b.emit(0x60)

    b.export("rt_f_special")
    return b


def compare_module() -> ObjectBuilder:
    """Build an IEEE-754 binary32 comparator with unordered NaN result 2."""
    b = ObjectBuilder("rt_f_cmp")

    b.immediate(0xA9, SPECIAL_COMPARE)
    b.jsr("rt_f_special")
    b.branch(0x90, "ordered")
    b.emit(0x60)
    b.label("ordered")

    # Different signs establish ordering unless both operands are signed zero.
    b.immediate(0xA0, 0x03)  # LDY #3
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.emit(0x51, 0x04)  # EOR ($04),Y
    b.branch(0x10, "same_sign")  # BPL

    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.immediate(0x29, 0x7F)  # AND #$7F
    b.zero_page(0x85, 0x08)  # STA $08
    for _ in range(3):
        b.emit(0x88)  # DEY
        b.emit(0xB1, 0x02)  # LDA ($02),Y
        b.zero_page(0x05, 0x08)  # ORA $08
        b.zero_page(0x85, 0x08)  # STA $08

    b.immediate(0xA0, 0x03)  # LDY #3
    b.emit(0xB1, 0x04)  # LDA ($04),Y
    b.immediate(0x29, 0x7F)  # AND #$7F
    b.zero_page(0x05, 0x08)  # ORA $08
    b.zero_page(0x85, 0x08)  # STA $08
    for index in range(3):
        b.emit(0x88)  # DEY
        b.emit(0xB1, 0x04)  # LDA ($04),Y
        b.zero_page(0x05, 0x08)  # ORA $08
        if index != 2:
            b.zero_page(0x85, 0x08)  # STA $08
    b.branch(0xF0, "equal")  # BEQ

    b.immediate(0xA0, 0x03)  # LDY #3
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.branch(0x30, "less")  # BMI
    b.branch(0x10, "greater")  # BPL, unconditional after LDA

    # Equal signs compare magnitude lexicographically from high byte to low.
    b.label("same_sign")
    b.immediate(0xA0, 0x03)  # LDY #3
    b.emit(0xB1, 0x04)  # LDA ($04),Y
    b.immediate(0x29, 0x7F)  # AND #$7F
    b.zero_page(0x85, 0x08)  # STA $08
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.immediate(0x29, 0x7F)  # AND #$7F
    b.zero_page(0xC5, 0x08)  # CMP $08
    b.branch(0x90, "magnitude_less")  # BCC
    b.branch(0xD0, "magnitude_greater")  # BNE
    b.emit(0x88)  # DEY

    b.label("compare_magnitude")
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.emit(0xD1, 0x04)  # CMP ($04),Y
    b.branch(0x90, "magnitude_less")  # BCC
    b.branch(0xD0, "magnitude_greater")  # BNE
    b.emit(0x88)  # DEY
    b.branch(0x10, "compare_magnitude")  # BPL

    b.label("equal")
    b.immediate(0xA9, 0x00)  # LDA #0
    b.emit(0xAA, 0x60)  # TAX; RTS

    b.label("magnitude_less")
    b.immediate(0xA0, 0x03)  # LDY #3
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.branch(0x30, "greater")  # BMI; reverse magnitude ordering for negatives

    b.label("less")
    b.immediate(0xA9, 0xFF)  # LDA #-1
    b.emit(0xAA, 0x60)  # TAX; RTS

    b.label("magnitude_greater")
    b.immediate(0xA0, 0x03)  # LDY #3
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.branch(0x30, "less")  # BMI; reverse magnitude ordering for negatives

    b.label("greater")
    b.immediate(0xA9, 0x01)  # LDA #1
    b.immediate(0xA2, 0x00)  # LDX #0
    b.emit(0x60)  # RTS

    b.export("rt_f_cmp")
    return b


def minmax_module(module: str, *, maximum: bool) -> ObjectBuilder:
    """Build FMin/FMax selection with the source-library NaN policy."""
    b = ObjectBuilder(module)

    b.jsr("rt_f_cmp")
    b.immediate(0xC9, 0x02)  # CMP #2; unordered means at least one NaN
    b.branch(0xF0, "unordered")
    b.immediate(0xC9, 0xFF if maximum else 0x01)
    b.branch(0xF0, "select_right")

    b.label("select_left")
    b.zero_page(0xA5, 0x02)
    b.zero_page(0x85, 0x08)
    b.zero_page(0xA5, 0x03)
    b.zero_page(0x85, 0x09)
    b.jmp_local("copy")

    b.label("select_right")
    b.zero_page(0xA5, 0x04)
    b.zero_page(0x85, 0x08)
    b.zero_page(0xA5, 0x05)
    b.zero_page(0x85, 0x09)
    b.jmp_local("copy")

    # The Action MATH1 source checks left<>left first. If both operands are
    # NaNs it therefore returns the right operand; if only right is NaN it
    # returns left. Preserve the selected operand bit-for-bit, including its
    # NaN payload and signed-zero representation.
    b.label("unordered")
    b.immediate(0xA0, 0x03)
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.immediate(0x29, 0x7F)
    b.immediate(0xC9, 0x7F)
    b.branch(0xD0, "select_left")
    b.emit(0x88)  # DEY
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.branch(0x10, "select_left")  # exponent low bit must be set
    b.immediate(0x29, 0x7F)
    b.branch(0xD0, "select_right")
    b.emit(0x88)  # DEY
    b.emit(0xB1, 0x02)
    b.branch(0xD0, "select_right")
    b.emit(0x88)  # DEY
    b.emit(0xB1, 0x02)
    b.branch(0xD0, "select_right")
    b.jmp_local("select_left")

    b.label("copy")
    b.immediate(0xA0, 0x00)
    b.label("copy_loop")
    b.emit(0xB1, 0x08)  # LDA ($08),Y
    b.emit(0x91, 0x06)  # STA ($06),Y
    b.emit(0xC8)  # INY
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "copy_loop")
    b.emit(0x60)

    b.export(module)
    return b


def float_to_int_module() -> ObjectBuilder:
    """Build finite binary32 to signed 16-bit truncation toward zero."""
    b = ObjectBuilder("rt_f_to_i")

    # Reconstruct the eight-bit biased exponent while retaining the sign byte.
    b.immediate(0xA0, 0x03)  # LDY #3
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.zero_page(0x85, 0x04)  # STA $04
    b.immediate(0x29, 0x7F)  # AND #$7F
    b.emit(0x0A)  # ASL
    b.zero_page(0x85, 0x05)  # STA $05
    b.emit(0x88)  # DEY
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.zero_page(0x85, 0x09)  # STA $09
    b.immediate(0x29, 0x80)  # AND #$80
    b.branch(0xF0, "exponent_ready")  # BEQ
    b.zero_page(0xE6, 0x05)  # INC $05

    b.label("exponent_ready")
    b.zero_page(0xA5, 0x05)  # LDA $05
    b.immediate(0xC9, 0x7F)  # CMP #127; magnitudes below one truncate to zero
    b.branch(0x90, "zero")  # BCC
    b.immediate(0xC9, 0x8F)  # CMP #143; exponent 16 cannot fit signed 16-bit
    b.branch(0xB0, "zero")  # BCS

    # Shift the 24-bit normalized significand down to an integer magnitude.
    b.immediate(0xA9, 0x96)  # LDA #150 == 127 bias + 23 fraction bits
    b.emit(0x38)  # SEC
    b.zero_page(0xE5, 0x05)  # SBC $05
    b.zero_page(0x85, 0x06)  # STA shift count
    b.immediate(0xA0, 0x00)  # LDY #0
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.zero_page(0x85, 0x07)  # STA magnitude low
    b.emit(0xC8)  # INY
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.zero_page(0x85, 0x08)  # STA magnitude high
    b.emit(0xC8)  # INY
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.immediate(0x29, 0x7F)  # AND #$7F
    b.immediate(0x09, 0x80)  # ORA #$80; restore implicit leading one
    b.zero_page(0x85, 0x09)  # STA magnitude extension

    b.label("shift")
    b.zero_page(0x46, 0x09)  # LSR extension
    b.zero_page(0x66, 0x08)  # ROR high
    b.zero_page(0x66, 0x07)  # ROR low
    b.zero_page(0xC6, 0x06)  # DEC shift count
    b.branch(0xD0, "shift")  # BNE

    b.zero_page(0xA5, 0x08)  # LDA magnitude high
    b.branch(0x30, "signed_limit")  # BMI
    b.zero_page(0xA5, 0x04)  # LDA saved sign byte
    b.branch(0x30, "negative")  # BMI
    b.zero_page(0xA5, 0x07)  # LDA result low
    b.zero_page(0xA6, 0x08)  # LDX result high
    b.emit(0x60)  # RTS

    # A magnitude with bit 15 set is valid only for exactly negative 32768.
    b.label("signed_limit")
    b.zero_page(0xA5, 0x04)  # LDA saved sign byte
    b.branch(0x10, "zero")  # BPL
    b.zero_page(0xA5, 0x08)  # LDA magnitude high
    b.immediate(0xC9, 0x80)  # CMP #$80
    b.branch(0xD0, "zero")  # BNE
    b.zero_page(0xA5, 0x07)  # LDA magnitude low
    b.branch(0xD0, "zero")  # BNE
    b.immediate(0xA9, 0x00)  # LDA #0
    b.immediate(0xA2, 0x80)  # LDX #$80
    b.emit(0x60)  # RTS

    b.label("negative")
    b.zero_page(0xA5, 0x07)  # LDA magnitude low
    b.immediate(0x49, 0xFF)  # EOR #$FF
    b.emit(0x18)  # CLC
    b.immediate(0x69, 0x01)  # ADC #1
    b.zero_page(0x85, 0x0A)  # STA result low
    b.zero_page(0xA5, 0x08)  # LDA magnitude high
    b.immediate(0x49, 0xFF)  # EOR #$FF
    b.immediate(0x69, 0x00)  # ADC #0
    b.emit(0xAA)  # TAX
    b.zero_page(0xA5, 0x0A)  # LDA result low
    b.emit(0x60)  # RTS

    b.label("zero")
    b.immediate(0xA9, 0x00)  # LDA #0
    b.emit(0xAA, 0x60)  # TAX; RTS

    b.export("rt_f_to_i")
    return b


def addsub_core_module() -> ObjectBuilder:
    """Build binary32 add/sub with IEEE special values and nearest-even rounding."""
    b = ObjectBuilder("rt_f_addsub_core")

    mant_a = 0x08
    mant_b = 0x0C
    exp_a = 0x10
    exp_b = 0x11
    sign_a = 0x12
    sign_b = 0x13
    result_exp = 0x14
    result_sign = 0x15
    count = 0x16
    sticky = 0x17
    temp = 0x18
    operation = 0x19

    def unpack(pointer: int, mantissa: int, exponent: int, sign: int, tag: str) -> None:
        b.immediate(0xA0, 0x00)  # LDY #0
        for index in range(3):
            b.emit(0xB1, pointer)  # LDA (pointer),Y
            b.zero_page(0x85, mantissa + index)
            if index != 2:
                b.emit(0xC8)  # INY
        b.zero_page(0xA5, mantissa + 2)
        b.zero_page(0x85, temp)
        b.immediate(0x29, 0x7F)
        b.zero_page(0x85, mantissa + 2)
        b.emit(0xC8)  # INY
        b.emit(0xB1, pointer)
        b.zero_page(0x85, sign)
        b.immediate(0x29, 0x7F)
        b.emit(0x0A)  # ASL
        b.zero_page(0x85, exponent)
        b.zero_page(0xA5, temp)
        b.immediate(0x29, 0x80)
        b.branch(0xF0, f"{tag}_exponent_ready")
        b.zero_page(0xE6, exponent)
        b.label(f"{tag}_exponent_ready")
        b.zero_page(0xA5, sign)
        b.immediate(0x29, 0x80)
        b.zero_page(0x85, sign)
        b.zero_page(0xA5, exponent)
        b.immediate(0xC9, 0xFF)
        far_branch(b, 0xF0, "zero", f"{tag}_nonfinite")
        b.zero_page(0xA5, exponent)
        b.branch(0xF0, f"{tag}_subnormal")
        b.zero_page(0xA5, mantissa + 2)
        b.immediate(0x09, 0x80)
        b.zero_page(0x85, mantissa + 2)
        b.branch(0xD0, f"{tag}_significand_ready")
        b.label(f"{tag}_subnormal")
        b.immediate(0xA9, 0x01)
        b.zero_page(0x85, exponent)
        b.label(f"{tag}_significand_ready")
        b.immediate(0xA9, 0x00)
        b.zero_page(0x85, mantissa + 3)
        for _ in range(3):
            b.zero_page(0x06, mantissa)  # ASL low
            for index in range(1, 4):
                b.zero_page(0x26, mantissa + index)  # ROL upper bytes

    def swap_bytes(left: int, right: int, length: int, tag: str) -> None:
        b.immediate(0xA2, length - 1)  # LDX #length-1
        b.label(f"swap_{tag}_loop")
        b.emit(0xB5, left)  # LDA left,X
        b.zero_page(0x85, temp)
        b.emit(0xB5, right)
        b.emit(0x95, left)
        b.zero_page(0xA5, temp)
        b.emit(0x95, right)
        b.emit(0xCA)  # DEX
        b.branch(0x10, f"swap_{tag}_loop")  # BPL

    def shift_result_right(tag: str) -> None:
        b.zero_page(0x46, mant_a + 3)
        for index in range(2, -1, -1):
            b.zero_page(0x66, mant_a + index)
        b.branch(0x90, f"{tag}_no_sticky")
        b.zero_page(0xA5, mant_a)
        b.immediate(0x09, 0x01)
        b.zero_page(0x85, mant_a)
        b.label(f"{tag}_no_sticky")
        b.zero_page(0xE6, result_exp)
        b.zero_page(0xA5, result_exp)
        b.immediate(0xC9, 0xFF)
        far_branch(b, 0xF0, "inf", f"{tag}_overflow")

    b.zero_page(0x85, operation)  # STA operation; $80 toggles RHS sign for subtraction
    b.jsr("rt_f_special")
    b.branch(0x90, "finite_operands")
    b.emit(0x60)
    b.label("finite_operands")
    unpack(0x02, mant_a, exp_a, sign_a, "a")
    unpack(0x04, mant_b, exp_b, sign_b, "b")
    b.zero_page(0xA5, sign_b)
    b.zero_page(0x45, operation)  # EOR operation
    b.zero_page(0x85, sign_b)

    # Keep the operand with the greater effective exponent in mantissa A.
    b.zero_page(0xA5, exp_a)
    b.zero_page(0xC5, exp_b)
    b.branch(0xB0, "exponents_ordered")
    b.zero_page(0xA5, exp_a)
    b.zero_page(0xA6, exp_b)
    b.zero_page(0x86, exp_a)
    b.zero_page(0x85, exp_b)
    b.zero_page(0xA5, sign_a)
    b.zero_page(0xA6, sign_b)
    b.zero_page(0x86, sign_a)
    b.zero_page(0x85, sign_b)
    swap_bytes(mant_a, mant_b, 4, "exponent_operands")
    b.label("exponents_ordered")
    b.zero_page(0xA5, exp_a)
    b.zero_page(0x85, result_exp)
    b.emit(0x38)  # SEC
    b.zero_page(0xE5, exp_b)
    b.zero_page(0x85, count)
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, sticky)
    b.zero_page(0xA5, count)
    b.branch(0xF0, "align")
    b.immediate(0xC9, 0x20)
    b.branch(0x90, "align_loop")

    # A shift of 32 or more leaves only a sticky contribution from B.
    b.zero_page(0xA5, mant_b)
    for index in range(1, 4):
        b.zero_page(0x05, mant_b + index)
    b.branch(0xF0, "clear_far_operand")
    b.immediate(0xA9, 0x01)
    b.label("clear_far_operand")
    b.zero_page(0x85, mant_b)
    b.immediate(0xA9, 0x00)
    for index in range(1, 4):
        b.zero_page(0x85, mant_b + index)
    b.jmp_local("align")

    b.label("align_loop")
    b.zero_page(0x46, mant_b + 3)
    for index in range(2, -1, -1):
        b.zero_page(0x66, mant_b + index)
    b.branch(0x90, "align_no_sticky")
    b.immediate(0xA9, 0x01)
    b.zero_page(0x85, sticky)
    b.label("align_no_sticky")
    b.zero_page(0xC6, count)
    b.branch(0xD0, "align_loop")
    b.zero_page(0xA5, sticky)
    b.branch(0xF0, "align")
    b.zero_page(0xA5, mant_b)
    b.immediate(0x09, 0x01)
    b.zero_page(0x85, mant_b)

    b.label("align")
    b.zero_page(0xA5, sign_a)
    b.zero_page(0x45, sign_b)
    b.branch(0xD0, "different_signs")

    # Same-sign operands add directly.
    b.zero_page(0xA5, sign_a)
    b.zero_page(0x85, result_sign)
    b.emit(0x18)  # CLC
    for index in range(4):
        b.zero_page(0xA5, mant_a + index)
        b.zero_page(0x65, mant_b + index)
        b.zero_page(0x85, mant_a + index)
    b.zero_page(0xA5, mant_a + 3)
    b.immediate(0x29, 0x08)
    far_branch(b, 0xF0, "round", "add_round")
    shift_result_right("add_normalize")
    b.jmp_local("round")

    # Different signs reduce to magnitude subtraction.
    b.label("different_signs")
    b.zero_page(0xA5, exp_a)
    b.zero_page(0xC5, exp_b)
    b.branch(0xD0, "subtract_magnitudes")
    b.immediate(0xA2, 0x03)
    b.label("compare_magnitudes")
    b.emit(0xB5, mant_a)
    b.emit(0xD5, mant_b)  # CMP mant_b,X
    b.branch(0x90, "swap_magnitudes")
    b.branch(0xD0, "subtract_magnitudes")
    b.emit(0xCA)
    b.branch(0x10, "compare_magnitudes")
    b.jmp_local("zero")

    b.label("swap_magnitudes")
    swap_bytes(mant_a, mant_b, 4, "magnitudes")
    b.zero_page(0xA5, sign_a)
    b.zero_page(0xA6, sign_b)
    b.zero_page(0x86, sign_a)
    b.zero_page(0x85, sign_b)

    b.label("subtract_magnitudes")
    b.zero_page(0xA5, sign_a)
    b.zero_page(0x85, result_sign)
    b.emit(0x38)  # SEC
    for index in range(4):
        b.zero_page(0xA5, mant_a + index)
        b.zero_page(0xE5, mant_b + index)
        b.zero_page(0x85, mant_a + index)
    b.zero_page(0xA5, mant_a)
    for index in range(1, 4):
        b.zero_page(0x05, mant_a + index)
    far_branch(b, 0xF0, "zero", "cancelled")

    b.label("normalize_subtraction")
    b.zero_page(0xA5, result_exp)
    b.immediate(0xC9, 0x01)
    b.branch(0xF0, "round")
    b.zero_page(0xA5, mant_a + 3)
    b.immediate(0x29, 0x04)
    b.branch(0xD0, "round")
    b.zero_page(0x06, mant_a)
    for index in range(1, 4):
        b.zero_page(0x26, mant_a + index)
    b.zero_page(0xC6, result_exp)
    b.branch(0xD0, "normalize_subtraction")

    # Round the retained 24-bit significand using guard, round, and sticky bits.
    b.label("round")
    b.zero_page(0xA5, mant_a)
    b.immediate(0x29, 0x04)
    b.branch(0xF0, "pack_result")
    b.zero_page(0xA5, mant_a)
    b.immediate(0x29, 0x03)
    b.branch(0xD0, "round_up")
    b.zero_page(0xA5, mant_a)
    b.immediate(0x29, 0x08)
    b.branch(0xF0, "pack_result")

    b.label("round_up")
    b.emit(0x18)
    b.zero_page(0xA5, mant_a)
    b.immediate(0x69, 0x08)
    b.zero_page(0x85, mant_a)
    for index in range(1, 4):
        b.zero_page(0xA5, mant_a + index)
        b.immediate(0x69, 0x00)
        b.zero_page(0x85, mant_a + index)
    b.zero_page(0xA5, mant_a + 3)
    b.immediate(0x29, 0x08)
    b.branch(0xF0, "pack_result")
    shift_result_right("round_normalize")

    b.label("pack_result")
    b.zero_page(0xA5, result_exp)
    b.immediate(0xC9, 0x01)
    b.branch(0xD0, "normal_exponent")
    b.zero_page(0xA5, mant_a + 3)
    b.immediate(0x29, 0x04)
    b.branch(0xD0, "normal_exponent")
    b.immediate(0xA9, 0x00)
    b.branch(0xF0, "exponent_field_ready")
    b.label("normal_exponent")
    b.zero_page(0xA5, result_exp)
    b.label("exponent_field_ready")
    b.zero_page(0x85, temp)

    for _ in range(3):
        b.zero_page(0x46, mant_a + 3)
        for index in range(2, -1, -1):
            b.zero_page(0x66, mant_a + index)

    b.immediate(0xA0, 0x00)
    b.zero_page(0xA5, mant_a)
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.zero_page(0xA5, mant_a + 1)
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.zero_page(0xA5, mant_a + 2)
    b.immediate(0x29, 0x7F)
    b.zero_page(0x85, sticky)
    b.zero_page(0xA5, temp)
    b.immediate(0x29, 0x01)
    b.branch(0xF0, "store_fraction_high")
    b.zero_page(0xA5, sticky)
    b.immediate(0x09, 0x80)
    b.branch(0xD0, "write_fraction_high")
    b.label("store_fraction_high")
    b.zero_page(0xA5, sticky)
    b.label("write_fraction_high")
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.zero_page(0xA5, temp)
    b.emit(0x4A)  # LSR A
    b.zero_page(0x05, result_sign)
    b.emit(0x91, 0x06)
    b.emit(0x60)

    b.label("inf")
    b.zero_page(0xA6, result_sign)
    b.immediate(0xA9, SPECIAL_STORE_INFINITY)
    b.jsr("rt_f_special")
    b.emit(0x60)

    b.label("zero")
    b.immediate(0xA0, 0x00)
    b.immediate(0xA9, 0x00)
    for index in range(4):
        b.emit(0x91, 0x06)
        if index != 3:
            b.emit(0xC8)
    b.emit(0x60)

    b.export("rt_f_addsub_core")
    return b


def multiply_module() -> ObjectBuilder:
    """Build binary32 multiplication with IEEE special values and nearest-even rounding."""
    b = ObjectBuilder("rt_f_mul")

    multiplicand = 0x08  # Six-byte shifted 24-bit input.
    multiplier = 0x0E  # Three-byte 24-bit input.
    product = 0x11  # Six-byte 48-bit product.
    exp_a = 0x17
    exp_b = 0x18
    sign = 0x19
    temp = 0x1A
    count = 0x1B
    sticky = 0x1C
    result_exp_lo = 0x1D
    result_exp_hi = 0x1E
    exponent_field = 0x1F

    def unpack(pointer: int, mantissa: int, exponent: int, tag: str) -> None:
        b.immediate(0xA0, 0x00)  # LDY #0
        b.emit(0xB1, pointer)  # LDA (pointer),Y
        b.zero_page(0x85, mantissa)
        b.emit(0xC8)
        b.emit(0xB1, pointer)
        b.zero_page(0x85, mantissa + 1)
        b.emit(0xC8)
        b.emit(0xB1, pointer)
        b.zero_page(0x85, temp)
        b.immediate(0x29, 0x7F)
        b.zero_page(0x85, mantissa + 2)
        b.emit(0xC8)
        b.emit(0xB1, pointer)
        b.immediate(0x29, 0x7F)
        b.emit(0x0A)  # ASL
        b.zero_page(0x85, exponent)
        b.zero_page(0xA5, temp)
        b.immediate(0x29, 0x80)
        b.branch(0xF0, f"{tag}_exponent_ready")
        b.zero_page(0xE6, exponent)
        b.label(f"{tag}_exponent_ready")

        b.zero_page(0xA5, exponent)
        b.immediate(0xC9, 0xFF)
        far_branch(b, 0xF0, "zero", f"{tag}_nonfinite")
        b.zero_page(0xA5, exponent)
        b.branch(0xD0, f"{tag}_normal")
        b.immediate(0xA9, 0x01)  # Subnormals use effective exponent one.
        b.zero_page(0x85, exponent)
        b.branch(0xD0, f"{tag}_significand_ready")
        b.label(f"{tag}_normal")
        b.zero_page(0xA5, mantissa + 2)
        b.immediate(0x09, 0x80)
        b.zero_page(0x85, mantissa + 2)
        b.label(f"{tag}_significand_ready")

        b.zero_page(0xA5, mantissa)
        b.zero_page(0x05, mantissa + 1)
        b.zero_page(0x05, mantissa + 2)
        far_branch(b, 0xF0, "signed_zero", f"{tag}_zero")

    b.immediate(0xA9, SPECIAL_MUL)
    b.jsr("rt_f_special")
    b.branch(0x90, "finite_operands")
    b.emit(0x60)
    b.label("finite_operands")

    # Multiplication and finite underflow preserve the XOR result sign.
    b.immediate(0xA0, 0x03)
    b.emit(0xB1, 0x02)
    b.emit(0x51, 0x04)  # EOR ($04),Y
    b.immediate(0x29, 0x80)
    b.zero_page(0x85, sign)
    unpack(0x02, multiplicand, exp_a, "a")
    unpack(0x04, multiplier, exp_b, "b")

    # The normalized 48-bit product targets bit 47, hence bias adjustment 126.
    b.emit(0x18)
    b.zero_page(0xA5, exp_a)
    b.zero_page(0x65, exp_b)
    b.zero_page(0x85, result_exp_lo)
    b.immediate(0xA9, 0x00)
    b.immediate(0x69, 0x00)
    b.zero_page(0x85, result_exp_hi)
    b.emit(0x38)
    b.zero_page(0xA5, result_exp_lo)
    b.immediate(0xE9, 0x7E)
    b.zero_page(0x85, result_exp_lo)
    b.zero_page(0xA5, result_exp_hi)
    b.immediate(0xE9, 0x00)
    b.zero_page(0x85, result_exp_hi)

    b.immediate(0xA9, 0x00)
    for index in range(3, 6):
        b.zero_page(0x85, multiplicand + index)
    for index in range(6):
        b.zero_page(0x85, product + index)

    # Shift-add the exact 24-by-24-bit significand product into six bytes.
    b.immediate(0xA9, 0x18)
    b.zero_page(0x85, count)
    b.label("multiply_loop")
    b.zero_page(0x46, multiplier + 2)
    b.zero_page(0x66, multiplier + 1)
    b.zero_page(0x66, multiplier)
    b.branch(0x90, "multiply_no_add")
    b.emit(0x18)
    for index in range(6):
        b.zero_page(0xA5, product + index)
        b.zero_page(0x65, multiplicand + index)
        b.zero_page(0x85, product + index)
    b.label("multiply_no_add")
    b.zero_page(0x06, multiplicand)
    for index in range(1, 6):
        b.zero_page(0x26, multiplicand + index)
    b.zero_page(0xC6, count)
    b.branch(0xD0, "multiply_loop")

    # Normalize any normal/subnormal input combination to product bit 47.
    b.label("normalize")
    b.zero_page(0xA5, product + 5)
    b.branch(0x30, "normalized")
    b.zero_page(0x06, product)
    for index in range(1, 6):
        b.zero_page(0x26, product + index)
    b.emit(0x38)
    b.zero_page(0xA5, result_exp_lo)
    b.immediate(0xE9, 0x01)
    b.zero_page(0x85, result_exp_lo)
    b.zero_page(0xA5, result_exp_hi)
    b.immediate(0xE9, 0x00)
    b.zero_page(0x85, result_exp_hi)
    b.immediate(0xA9, 0x01)
    b.branch(0xD0, "normalize")

    b.label("normalized")
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, sticky)
    b.zero_page(0xA5, result_exp_hi)
    b.branch(0x30, "subnormal")
    far_branch(b, 0xD0, "infinity", "positive_overflow")
    b.zero_page(0xA5, result_exp_lo)
    b.branch(0xF0, "subnormal")
    b.immediate(0xC9, 0xFF)
    far_branch(b, 0xF0, "infinity", "exponent_overflow")
    b.zero_page(0x85, exponent_field)
    b.jmp_local("round")

    # Shift into the exponent-zero position, retaining bits lost below bit zero.
    b.label("subnormal")
    b.emit(0x38)
    b.immediate(0xA9, 0x01)
    b.zero_page(0xE5, result_exp_lo)
    b.zero_page(0x85, count)
    b.immediate(0xA9, 0x00)
    b.zero_page(0xE5, result_exp_hi)
    far_branch(b, 0xD0, "signed_zero", "underflow_shift")
    b.label("subnormal_shift")
    b.zero_page(0x46, product + 5)
    for index in range(4, -1, -1):
        b.zero_page(0x66, product + index)
    b.branch(0x90, "subnormal_no_sticky")
    b.immediate(0xA9, 0x01)
    b.zero_page(0x85, sticky)
    b.label("subnormal_no_sticky")
    b.zero_page(0xC6, count)
    b.branch(0xD0, "subnormal_shift")
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, exponent_field)

    # Bits 47..24 are retained; bit 23 and below drive nearest-even rounding.
    b.label("round")
    b.zero_page(0xA5, product + 2)
    b.immediate(0x29, 0x80)
    b.branch(0xF0, "round_complete")
    b.zero_page(0xA5, product + 2)
    b.immediate(0x29, 0x7F)
    b.zero_page(0x05, product)
    b.zero_page(0x05, product + 1)
    b.zero_page(0x05, sticky)
    b.branch(0xD0, "round_up")
    b.zero_page(0xA5, product + 3)
    b.immediate(0x29, 0x01)
    b.branch(0xF0, "round_complete")

    b.label("round_up")
    b.emit(0x18)
    for index in range(3, 6):
        b.zero_page(0xA5, product + index)
        b.immediate(0x69, 0x01 if index == 3 else 0x00)
        b.zero_page(0x85, product + index)
    b.branch(0x90, "round_complete")
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, product + 3)
    b.zero_page(0x85, product + 4)
    b.immediate(0xA9, 0x80)
    b.zero_page(0x85, product + 5)
    b.zero_page(0xE6, exponent_field)
    b.zero_page(0xA5, exponent_field)
    b.immediate(0xC9, 0xFF)
    far_branch(b, 0xF0, "infinity", "round_overflow")

    b.label("round_complete")
    b.zero_page(0xA5, exponent_field)
    b.branch(0xD0, "pack")
    b.zero_page(0xA5, product + 5)
    b.branch(0x10, "pack")
    b.zero_page(0xE6, exponent_field)  # Rounded largest subnormal becomes normal.

    b.label("pack")
    b.immediate(0xA0, 0x00)
    b.zero_page(0xA5, product + 3)
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.zero_page(0xA5, product + 4)
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.zero_page(0xA5, exponent_field)
    b.emit(0x4A)  # Carry retains exponent bit zero.
    b.zero_page(0x85, temp)
    b.zero_page(0xA5, product + 5)
    b.immediate(0x29, 0x7F)
    b.branch(0x90, "pack_exponent_even")
    b.immediate(0x09, 0x80)
    b.label("pack_exponent_even")
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.zero_page(0xA5, temp)
    b.zero_page(0x05, sign)
    b.emit(0x91, 0x06)
    b.emit(0x60)

    b.label("infinity")
    b.zero_page(0xA6, sign)
    b.immediate(0xA9, SPECIAL_STORE_INFINITY)
    b.jsr("rt_f_special")
    b.emit(0x60)

    b.label("zero")
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, sign)
    b.label("signed_zero")
    b.immediate(0xA0, 0x00)
    b.immediate(0xA9, 0x00)
    for _ in range(3):
        b.emit(0x91, 0x06)
        b.emit(0xC8)
    b.zero_page(0xA5, sign)
    b.emit(0x91, 0x06)
    b.emit(0x60)

    b.export("rt_f_mul")
    return b


def divide_module() -> ObjectBuilder:
    """Build binary32 division with IEEE special values and nearest-even rounding."""
    b = ObjectBuilder("rt_f_div")

    significand_a = 0x08
    significand_b = 0x0B
    remainder = 0x0E  # Four-byte restoring-division remainder.
    quotient = 0x12  # Retained significand plus guard/round/sticky bits.
    exp_a = 0x16  # Signed effective biased exponent.
    exp_b = 0x18
    result_exp = 0x1A
    sign = 0x1C
    temp = 0x1D
    count = 0x1E
    exponent_field = 0x1F

    def unpack(pointer: int, significand: int, exponent: int, tag: str) -> None:
        b.immediate(0xA0, 0x00)  # LDY #0
        b.emit(0xB1, pointer)
        b.zero_page(0x85, significand)
        b.emit(0xC8)
        b.emit(0xB1, pointer)
        b.zero_page(0x85, significand + 1)
        b.emit(0xC8)
        b.emit(0xB1, pointer)
        b.zero_page(0x85, temp)
        b.immediate(0x29, 0x7F)
        b.zero_page(0x85, significand + 2)
        b.emit(0xC8)
        b.emit(0xB1, pointer)
        b.immediate(0x29, 0x7F)
        b.emit(0x0A)  # ASL
        b.zero_page(0x85, exponent)
        b.zero_page(0xA5, temp)
        b.immediate(0x29, 0x80)
        b.branch(0xF0, f"{tag}_exponent_ready")
        b.zero_page(0xE6, exponent)
        b.label(f"{tag}_exponent_ready")
        b.immediate(0xA9, 0x00)
        b.zero_page(0x85, exponent + 1)

        b.zero_page(0xA5, exponent)
        b.immediate(0xC9, 0xFF)
        far_branch(b, 0xF0, "zero", f"{tag}_nonfinite")
        b.zero_page(0xA5, exponent)
        b.branch(0xD0, f"{tag}_normal")
        b.immediate(0xA9, 0x01)  # Subnormals use effective exponent one.
        b.zero_page(0x85, exponent)
        b.branch(0xD0, f"{tag}_ready")
        b.label(f"{tag}_normal")
        b.zero_page(0xA5, significand + 2)
        b.immediate(0x09, 0x80)
        b.zero_page(0x85, significand + 2)
        b.label(f"{tag}_ready")

    def normalize(significand: int, exponent: int, tag: str) -> None:
        b.label(f"normalize_{tag}")
        b.zero_page(0xA5, significand + 2)
        b.branch(0x30, f"normalized_{tag}")
        b.zero_page(0x06, significand)
        b.zero_page(0x26, significand + 1)
        b.zero_page(0x26, significand + 2)
        b.emit(0x38)
        b.zero_page(0xA5, exponent)
        b.immediate(0xE9, 0x01)
        b.zero_page(0x85, exponent)
        b.zero_page(0xA5, exponent + 1)
        b.immediate(0xE9, 0x00)
        b.zero_page(0x85, exponent + 1)
        b.jmp_local(f"normalize_{tag}")
        b.label(f"normalized_{tag}")

    b.immediate(0xA9, SPECIAL_DIV)
    b.jsr("rt_f_special")
    b.branch(0x90, "finite_operands")
    b.emit(0x60)
    b.label("finite_operands")

    # Division and finite underflow preserve the XOR result sign.
    b.immediate(0xA0, 0x03)
    b.emit(0xB1, 0x02)
    b.emit(0x51, 0x04)
    b.immediate(0x29, 0x80)
    b.zero_page(0x85, sign)
    unpack(0x02, significand_a, exp_a, "a")
    unpack(0x04, significand_b, exp_b, "b")

    # The shared classifier has already handled every zero divisor.
    b.zero_page(0xA5, significand_b)
    b.zero_page(0x05, significand_b + 1)
    b.zero_page(0x05, significand_b + 2)
    far_branch(b, 0xF0, "zero", "zero_divisor")
    b.zero_page(0xA5, significand_a)
    b.zero_page(0x05, significand_a + 1)
    b.zero_page(0x05, significand_a + 2)
    far_branch(b, 0xF0, "signed_zero", "zero_numerator")

    normalize(significand_a, exp_a, "a")
    normalize(significand_b, exp_b, "b")

    # Biased result exponent is exp(A) - exp(B) + 127.
    b.emit(0x38)
    b.zero_page(0xA5, exp_a)
    b.zero_page(0xE5, exp_b)
    b.zero_page(0x85, result_exp)
    b.zero_page(0xA5, exp_a + 1)
    b.zero_page(0xE5, exp_b + 1)
    b.zero_page(0x85, result_exp + 1)
    b.emit(0x18)
    b.zero_page(0xA5, result_exp)
    b.immediate(0x69, 0x7F)
    b.zero_page(0x85, result_exp)
    b.zero_page(0xA5, result_exp + 1)
    b.immediate(0x69, 0x00)
    b.zero_page(0x85, result_exp + 1)

    for index in range(3):
        b.zero_page(0xA5, significand_a + index)
        b.zero_page(0x85, remainder + index)
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, remainder + 3)
    for index in range(4):
        b.zero_page(0x85, quotient + index)

    # Quotients below one are normalized by doubling the dividend.
    b.zero_page(0xA5, significand_a + 2)
    b.zero_page(0xC5, significand_b + 2)
    b.branch(0x90, "scale_dividend")
    b.branch(0xD0, "dividend_scaled")
    b.zero_page(0xA5, significand_a + 1)
    b.zero_page(0xC5, significand_b + 1)
    b.branch(0x90, "scale_dividend")
    b.branch(0xD0, "dividend_scaled")
    b.zero_page(0xA5, significand_a)
    b.zero_page(0xC5, significand_b)
    b.branch(0xB0, "dividend_scaled")
    b.label("scale_dividend")
    b.zero_page(0x06, remainder)
    for index in range(1, 4):
        b.zero_page(0x26, remainder + index)
    b.emit(0x38)
    b.zero_page(0xA5, result_exp)
    b.immediate(0xE9, 0x01)
    b.zero_page(0x85, result_exp)
    b.zero_page(0xA5, result_exp + 1)
    b.immediate(0xE9, 0x00)
    b.zero_page(0x85, result_exp + 1)
    b.label("dividend_scaled")

    # Emit 24 retained quotient bits, guard, round, and one sticky candidate.
    b.immediate(0xA9, 0x1B)
    b.zero_page(0x85, count)
    b.label("divide_loop")
    b.zero_page(0xA5, remainder + 3)
    b.branch(0xD0, "subtract_divisor")
    b.zero_page(0xA5, remainder + 2)
    b.zero_page(0xC5, significand_b + 2)
    b.branch(0x90, "quotient_zero_bit")
    b.branch(0xD0, "subtract_divisor")
    b.zero_page(0xA5, remainder + 1)
    b.zero_page(0xC5, significand_b + 1)
    b.branch(0x90, "quotient_zero_bit")
    b.branch(0xD0, "subtract_divisor")
    b.zero_page(0xA5, remainder)
    b.zero_page(0xC5, significand_b)
    b.branch(0x90, "quotient_zero_bit")

    b.label("subtract_divisor")
    b.emit(0x38)
    for index in range(3):
        b.zero_page(0xA5, remainder + index)
        b.zero_page(0xE5, significand_b + index)
        b.zero_page(0x85, remainder + index)
    b.zero_page(0xA5, remainder + 3)
    b.immediate(0xE9, 0x00)
    b.zero_page(0x85, remainder + 3)
    b.emit(0x38)
    b.branch(0xB0, "shift_quotient")

    b.label("quotient_zero_bit")
    b.emit(0x18)
    b.label("shift_quotient")
    for index in range(4):
        b.zero_page(0x26, quotient + index)
    b.zero_page(0x06, remainder)
    for index in range(1, 4):
        b.zero_page(0x26, remainder + index)
    b.zero_page(0xC6, count)
    b.branch(0xD0, "divide_loop")

    # Any exact remainder after the round bit contributes to sticky.
    b.zero_page(0xA5, remainder)
    for index in range(1, 4):
        b.zero_page(0x05, remainder + index)
    b.branch(0xF0, "quotient_ready")
    b.zero_page(0xA5, quotient)
    b.immediate(0x09, 0x01)
    b.zero_page(0x85, quotient)
    b.label("quotient_ready")

    # Classify the signed intermediate exponent before rounding.
    b.zero_page(0xA5, result_exp + 1)
    b.branch(0x30, "subnormal")
    far_branch(b, 0xD0, "infinity", "positive_overflow")
    b.zero_page(0xA5, result_exp)
    b.branch(0xF0, "subnormal")
    b.immediate(0xC9, 0xFF)
    far_branch(b, 0xF0, "infinity", "exponent_overflow")
    b.zero_page(0x85, exponent_field)
    b.jmp_local("round")

    # Shift into the exponent-zero position while folding lost bits into sticky.
    b.label("subnormal")
    b.emit(0x38)
    b.immediate(0xA9, 0x01)
    b.zero_page(0xE5, result_exp)
    b.zero_page(0x85, count)
    b.immediate(0xA9, 0x00)
    b.zero_page(0xE5, result_exp + 1)
    far_branch(b, 0xD0, "signed_zero", "underflow_shift_high")
    b.zero_page(0xA5, count)
    b.immediate(0xC9, 0x19)
    far_branch(b, 0xB0, "signed_zero", "underflow_shift_far")
    b.label("subnormal_shift")
    b.zero_page(0x46, quotient + 3)
    for index in range(2, -1, -1):
        b.zero_page(0x66, quotient + index)
    b.branch(0x90, "subnormal_no_sticky")
    b.zero_page(0xA5, quotient)
    b.immediate(0x09, 0x01)
    b.zero_page(0x85, quotient)
    b.label("subnormal_no_sticky")
    b.zero_page(0xC6, count)
    b.branch(0xD0, "subnormal_shift")
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, exponent_field)

    # Round the 24 retained bits from explicit guard, round, and sticky bits.
    b.label("round")
    b.zero_page(0xA5, quotient)
    b.immediate(0x29, 0x04)
    b.branch(0xF0, "round_complete")
    b.zero_page(0xA5, quotient)
    b.immediate(0x29, 0x03)
    b.branch(0xD0, "round_up")
    b.zero_page(0xA5, quotient)
    b.immediate(0x29, 0x08)
    b.branch(0xF0, "round_complete")

    b.label("round_up")
    b.emit(0x18)
    for index in range(4):
        b.zero_page(0xA5, quotient + index)
        b.immediate(0x69, 0x08 if index == 0 else 0x00)
        b.zero_page(0x85, quotient + index)
    b.zero_page(0xA5, quotient + 3)
    b.immediate(0x29, 0x08)
    b.branch(0xF0, "round_complete")
    b.zero_page(0x46, quotient + 3)
    for index in range(2, -1, -1):
        b.zero_page(0x66, quotient + index)
    b.zero_page(0xE6, exponent_field)
    b.zero_page(0xA5, exponent_field)
    b.immediate(0xC9, 0xFF)
    far_branch(b, 0xF0, "infinity", "round_overflow")

    b.label("round_complete")
    b.zero_page(0xA5, exponent_field)
    b.branch(0xD0, "pack")
    b.zero_page(0xA5, quotient + 3)
    b.immediate(0x29, 0x04)
    b.branch(0xF0, "pack")
    b.zero_page(0xE6, exponent_field)  # Rounded largest subnormal becomes normal.

    b.label("pack")
    for _ in range(3):
        b.zero_page(0x46, quotient + 3)
        for index in range(2, -1, -1):
            b.zero_page(0x66, quotient + index)
    b.immediate(0xA0, 0x00)
    b.zero_page(0xA5, quotient)
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.zero_page(0xA5, quotient + 1)
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.zero_page(0xA5, exponent_field)
    b.emit(0x4A)  # Carry retains exponent bit zero.
    b.zero_page(0x85, temp)
    b.zero_page(0xA5, quotient + 2)
    b.immediate(0x29, 0x7F)
    b.branch(0x90, "pack_exponent_even")
    b.immediate(0x09, 0x80)
    b.label("pack_exponent_even")
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.zero_page(0xA5, temp)
    b.zero_page(0x05, sign)
    b.emit(0x91, 0x06)
    b.emit(0x60)

    b.label("infinity")
    b.zero_page(0xA6, sign)
    b.immediate(0xA9, SPECIAL_STORE_INFINITY)
    b.jsr("rt_f_special")
    b.emit(0x60)

    b.label("zero")
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, sign)
    b.label("signed_zero")
    b.immediate(0xA0, 0x00)
    b.immediate(0xA9, 0x00)
    for _ in range(3):
        b.emit(0x91, 0x06)
        b.emit(0xC8)
    b.zero_page(0xA5, sign)
    b.emit(0x91, 0x06)
    b.emit(0x60)

    b.export("rt_f_div")
    return b


def square_root_module() -> ObjectBuilder:
    """Build binary32 square root with IEEE special values and nearest rounding."""
    b = ObjectBuilder("rt_f_sqrt")

    radicand = 0x08  # Six-byte exact significand scaling.
    remainder = 0x0E  # Four-byte restoring-square-root remainder.
    root = 0x12  # Three-byte floor square root.
    trial = 0x15  # Four-byte (root * 4 + 1) trial divisor.
    exponent = 0x19  # Signed effective biased input exponent.
    unbiased = 0x1B
    count = 0x1D
    temp = 0x1E
    exponent_field = 0x1F

    b.immediate(0xA9, SPECIAL_SQRT)
    b.jsr("rt_f_special")
    b.branch(0x90, "finite_operand")
    b.emit(0x60)
    b.label("finite_operand")

    # Read the complete operand before reusing the public source pointer bytes.
    b.immediate(0xA0, 0x00)
    for index in range(3):
        b.emit(0xB1, 0x02)
        b.zero_page(0x85, radicand + index)
        b.emit(0xC8)
    b.emit(0xB1, 0x02)
    b.zero_page(0x85, temp)

    # Preserve negative zero; all other negative inputs follow the +0 policy.
    b.zero_page(0xA5, temp)
    b.branch(0x10, "nonnegative")
    b.immediate(0x29, 0x7F)
    for index in range(3):
        b.zero_page(0x05, radicand + index)
    far_branch(b, 0xF0, "signed_zero", "negative_zero")
    b.jmp_local("zero")

    b.label("nonnegative")
    b.zero_page(0xA5, temp)
    b.immediate(0x29, 0x7F)
    b.emit(0x0A)
    b.zero_page(0x85, exponent)
    b.zero_page(0xA5, radicand + 2)
    b.immediate(0x29, 0x80)
    b.branch(0xF0, "exponent_ready")
    b.zero_page(0xE6, exponent)
    b.label("exponent_ready")
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, exponent + 1)
    b.zero_page(0xA5, radicand + 2)
    b.immediate(0x29, 0x7F)
    b.zero_page(0x85, radicand + 2)

    b.zero_page(0xA5, exponent)
    b.immediate(0xC9, 0xFF)
    far_branch(b, 0xF0, "zero", "nonfinite")
    b.zero_page(0xA5, exponent)
    b.branch(0xD0, "normal")
    b.zero_page(0xA5, radicand)
    b.zero_page(0x05, radicand + 1)
    b.zero_page(0x05, radicand + 2)
    far_branch(b, 0xF0, "signed_zero", "positive_zero")
    b.immediate(0xA9, 0x01)
    b.zero_page(0x85, exponent)
    b.branch(0xD0, "normalize")
    b.label("normal")
    b.zero_page(0xA5, radicand + 2)
    b.immediate(0x09, 0x80)
    b.zero_page(0x85, radicand + 2)

    # Normalize positive subnormal inputs while extending the signed exponent.
    b.label("normalize")
    b.zero_page(0xA5, radicand + 2)
    b.branch(0x30, "normalized")
    b.zero_page(0x06, radicand)
    b.zero_page(0x26, radicand + 1)
    b.zero_page(0x26, radicand + 2)
    b.emit(0x38)
    b.zero_page(0xA5, exponent)
    b.immediate(0xE9, 0x01)
    b.zero_page(0x85, exponent)
    b.zero_page(0xA5, exponent + 1)
    b.immediate(0xE9, 0x00)
    b.zero_page(0x85, exponent + 1)
    b.jmp_local("normalize")
    b.label("normalized")

    # Make the unbiased exponent even and retain its parity in the radicand shift.
    b.emit(0x38)
    b.zero_page(0xA5, exponent)
    b.immediate(0xE9, 0x7F)
    b.zero_page(0x85, unbiased)
    b.zero_page(0xA5, exponent + 1)
    b.immediate(0xE9, 0x00)
    b.zero_page(0x85, unbiased + 1)
    b.zero_page(0xA5, unbiased)
    b.immediate(0x29, 0x01)
    b.branch(0xF0, "even_exponent")
    b.immediate(0xA9, 0x18)
    b.zero_page(0x85, count)
    b.emit(0x38)
    b.zero_page(0xA5, unbiased)
    b.immediate(0xE9, 0x01)
    b.zero_page(0x85, unbiased)
    b.zero_page(0xA5, unbiased + 1)
    b.immediate(0xE9, 0x00)
    b.zero_page(0x85, unbiased + 1)
    b.jmp_local("result_exp")
    b.label("even_exponent")
    b.immediate(0xA9, 0x17)
    b.zero_page(0x85, count)

    b.label("result_exp")
    b.zero_page(0xA5, unbiased + 1)
    b.immediate(0xC9, 0x80)  # Carry becomes the arithmetic-shift sign bit.
    b.zero_page(0x66, unbiased + 1)
    b.zero_page(0x66, unbiased)
    b.emit(0x18)
    b.zero_page(0xA5, unbiased)
    b.immediate(0x69, 0x7F)
    b.zero_page(0x85, exponent_field)

    b.immediate(0xA9, 0x00)
    for index in range(3, 6):
        b.zero_page(0x85, radicand + index)
    for index in range(4):
        b.zero_page(0x85, remainder + index)
    for index in range(3):
        b.zero_page(0x85, root + index)

    # Form S << 23 for even exponents or S << 24 for odd exponents.
    b.label("scale_radicand")
    b.zero_page(0x06, radicand)
    for index in range(1, 6):
        b.zero_page(0x26, radicand + index)
    b.zero_page(0xC6, count)
    b.branch(0xD0, "scale_radicand")

    # Consume two high radicand bits per restoring square-root iteration.
    b.immediate(0xA9, 0x18)
    b.zero_page(0x85, count)
    b.label("sqrt_loop")
    b.zero_page(0xA5, radicand + 5)
    for _ in range(6):
        b.emit(0x4A)
    b.zero_page(0x85, temp)
    for _ in range(2):
        b.zero_page(0x06, radicand)
        for index in range(1, 6):
            b.zero_page(0x26, radicand + index)
    for _ in range(2):
        b.zero_page(0x06, remainder)
        for index in range(1, 4):
            b.zero_page(0x26, remainder + index)
    b.zero_page(0xA5, remainder)
    b.zero_page(0x05, temp)
    b.zero_page(0x85, remainder)

    for index in range(3):
        b.zero_page(0xA5, root + index)
        b.zero_page(0x85, trial + index)
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, trial + 3)
    for _ in range(2):
        b.zero_page(0x06, trial)
        for index in range(1, 4):
            b.zero_page(0x26, trial + index)
    b.zero_page(0xA5, trial)
    b.immediate(0x09, 0x01)
    b.zero_page(0x85, trial)

    for index in range(3, -1, -1):
        b.zero_page(0xA5, remainder + index)
        b.zero_page(0xC5, trial + index)
        b.branch(0x90, "root_zero_bit")
        if index != 0:
            b.branch(0xD0, "subtract_trial")

    b.label("subtract_trial")
    b.emit(0x38)
    for index in range(4):
        b.zero_page(0xA5, remainder + index)
        b.zero_page(0xE5, trial + index)
        b.zero_page(0x85, remainder + index)
    b.emit(0x38)
    b.branch(0xB0, "shift_root")
    b.label("root_zero_bit")
    b.emit(0x18)
    b.label("shift_root")
    for index in range(3):
        b.zero_page(0x26, root + index)
    b.zero_page(0xC6, count)
    far_branch(b, 0xD0, "sqrt_loop", "sqrt_continue")

    # For integer radicand T, round sqrt(T) up exactly when remainder > root.
    b.zero_page(0xA5, remainder + 3)
    b.branch(0xD0, "round_up")
    b.zero_page(0xA5, remainder + 2)
    b.zero_page(0xC5, root + 2)
    b.branch(0x90, "pack")
    b.branch(0xD0, "round_up")
    b.zero_page(0xA5, remainder + 1)
    b.zero_page(0xC5, root + 1)
    b.branch(0x90, "pack")
    b.branch(0xD0, "round_up")
    b.zero_page(0xA5, remainder)
    b.zero_page(0xC5, root)
    b.branch(0x90, "pack")
    b.branch(0xF0, "pack")
    b.label("round_up")
    b.emit(0x18)
    for index in range(3):
        b.zero_page(0xA5, root + index)
        b.immediate(0x69, 0x01 if index == 0 else 0x00)
        b.zero_page(0x85, root + index)

    b.label("pack")
    b.immediate(0xA0, 0x00)
    b.zero_page(0xA5, root)
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.zero_page(0xA5, root + 1)
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.zero_page(0xA5, exponent_field)
    b.emit(0x4A)  # Carry retains exponent bit zero.
    b.zero_page(0x85, temp)
    b.zero_page(0xA5, root + 2)
    b.immediate(0x29, 0x7F)
    b.branch(0x90, "pack_exponent_even")
    b.immediate(0x09, 0x80)
    b.label("pack_exponent_even")
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.zero_page(0xA5, temp)
    b.emit(0x91, 0x06)
    b.emit(0x60)

    b.label("zero")
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, temp)
    b.label("signed_zero")
    b.immediate(0xA0, 0x00)
    b.immediate(0xA9, 0x00)
    for _ in range(3):
        b.emit(0x91, 0x06)
        b.emit(0xC8)
    b.zero_page(0xA5, temp)
    b.immediate(0x29, 0x80)
    b.emit(0x91, 0x06)
    b.emit(0x60)

    b.export("rt_f_sqrt")
    return b


def compact_print_float_module() -> ObjectBuilder:
    """Retain the former seven-digit formatter as non-authoritative reference."""
    b = ObjectBuilder("rt_print_f")

    raw = 0
    digits = 4
    decimal_exp = 11
    last_digit = 12
    decimal_scale = 13
    binary_shift = 14
    raw_exp = 15
    sign = 16
    index = 17
    temp = 18
    numerator = 32
    denominator = 52
    remainder = 72
    quotient = 92
    state_size = 96

    state_ptr = 0x20
    numerator_ptr = 0x22
    denominator_ptr = 0x24
    remainder_ptr = 0x26
    quotient_ptr = 0x28
    table_ptr = 0x2A
    work_ptr = 0x2C
    carry = 0x2E
    scratch = 0x2F
    scratch_hi = 0x30
    loop_count = 0x31

    def jsr_local(label: str) -> None:
        b.local_reference(0x20, label)

    def state_load(offset: int) -> None:
        b.immediate(0xA0, offset)
        b.emit(0xB1, state_ptr)

    def state_store(offset: int) -> None:
        b.immediate(0xA0, offset)
        b.emit(0x91, state_ptr)

    def set_state_pointer(zp: int, offset: int) -> None:
        b.emit(0x18)
        b.zero_page(0xA5, state_ptr)
        b.immediate(0x69, offset)
        b.zero_page(0x85, zp)
        b.zero_page(0xA5, state_ptr + 1)
        b.immediate(0x69, 0x00)
        b.zero_page(0x85, zp + 1)

    def copy_pointer(source: int, target: int) -> None:
        b.zero_page(0xA5, source)
        b.zero_page(0x85, target)
        b.zero_page(0xA5, source + 1)
        b.zero_page(0x85, target + 1)

    def emit_ascii(value: int) -> None:
        b.immediate(0xA9, value)
        jsr_local("emit")

    def emit_digit_from_a() -> None:
        b.emit(0x18)
        b.immediate(0x69, ord("0"))
        jsr_local("emit")

    jsr_local("ip")

    # Snapshot the source value before the helper reuses public zero-page pointers.
    for offset in range(4):
        b.immediate(0xA0, offset)
        b.emit(0xB1, 0x02)
        state_store(raw + offset)
    state_load(raw + 3)
    b.immediate(0x29, 0x80)
    state_store(sign)

    # Zero retains its sign. Non-finite encodings get explicit stable spellings.
    state_load(raw + 3)
    b.immediate(0x29, 0x7F)
    for offset in range(3):
        b.immediate(0xA0, raw + offset)
        b.emit(0x11, state_ptr)  # ORA (state),Y
    b.branch(0xD0, "nonzero")
    b.jmp_local("pz")

    b.label("nonzero")
    state_load(raw + 3)
    b.immediate(0x29, 0x7F)
    b.emit(0x0A)
    state_store(raw_exp)
    state_load(raw + 2)
    b.immediate(0x29, 0x80)
    b.branch(0xF0, "raw_exponent_ready")
    state_load(raw_exp)
    b.emit(0x18)
    b.immediate(0x69, 0x01)
    state_store(raw_exp)
    b.label("raw_exponent_ready")
    state_load(raw_exp)
    b.immediate(0xC9, 0xFF)
    b.branch(0xD0, "finite")
    state_load(raw + 2)
    b.immediate(0x29, 0x7F)
    state_store(temp)
    state_load(raw + 1)
    b.immediate(0xA0, temp)
    b.emit(0x11, state_ptr)  # ORA (state),Y
    state_store(temp)
    state_load(raw)
    b.immediate(0xA0, temp)
    b.emit(0x11, state_ptr)
    b.branch(0xD0, "print_nan")
    state_load(sign)
    b.branch(0xF0, "print_infinity")
    emit_ascii(ord("-"))
    b.label("print_infinity")
    for char in "Infinity":
        emit_ascii(ord(char))
    b.emit(0x60)
    b.label("print_nan")
    for char in "NaN":
        emit_ascii(ord(char))
    b.emit(0x60)

    b.label("finite")
    state_load(sign)
    b.branch(0xF0, "magnitude_ready")
    emit_ascii(ord("-"))
    b.label("magnitude_ready")
    state_load(raw + 3)
    b.immediate(0x29, 0x7F)
    state_store(raw + 3)

    # Find floor(log10(value)) by comparing raw magnitudes with exact thresholds.
    b.immediate(0xA9, 38)
    state_store(decimal_exp)
    b.label("decimal_scan")
    b.immediate(0xA0, 0x03)
    b.label("decimal_compare")
    b.emit(0xB1, state_ptr)
    b.emit(0xD1, table_ptr)
    b.branch(0x90, "decimal_next")
    b.branch(0xD0, "decimal_found")
    b.emit(0x88)
    b.branch(0x10, "decimal_compare")
    b.immediate(0xA9, 0x01)
    b.branch(0xD0, "decimal_found")
    b.label("decimal_next")
    b.emit(0x18)
    b.zero_page(0xA5, table_ptr)
    b.immediate(0x69, 0x04)
    b.zero_page(0x85, table_ptr)
    b.zero_page(0xA5, table_ptr + 1)
    b.immediate(0x69, 0x00)
    b.zero_page(0x85, table_ptr + 1)
    state_load(decimal_exp)
    b.emit(0x38)
    b.immediate(0xE9, 0x01)
    state_store(decimal_exp)
    b.immediate(0xA9, 0x01)
    b.branch(0xD0, "decimal_scan")
    b.label("decimal_found")

    # Clear the exact rational workspace and reconstruct the 24-bit significand.
    b.immediate(0xA0, 0x00)
    b.immediate(0xA2, 20)
    b.immediate(0xA9, 0x00)
    b.label("clear_big")
    b.emit(0x91, numerator_ptr)
    b.emit(0x91, denominator_ptr)
    b.emit(0x91, remainder_ptr)
    b.emit(0xC8)
    b.emit(0xCA)
    b.branch(0xD0, "clear_big")
    b.immediate(0xA0, 0x00)
    b.immediate(0xA2, 0x04)
    b.label("clear_quotient")
    b.emit(0x91, quotient_ptr)
    b.emit(0xC8)
    b.emit(0xCA)
    b.branch(0xD0, "clear_quotient")
    b.immediate(0xA0, 0x00)
    b.immediate(0xA9, 0x01)
    b.emit(0x91, denominator_ptr)

    for offset in range(3):
        state_load(raw + offset)
        if offset == 2:
            b.immediate(0x29, 0x7F)
        b.immediate(0xA0, offset)
        b.emit(0x91, numerator_ptr)
    state_load(raw_exp)
    b.branch(0xD0, "normal_significand")
    b.immediate(0xA9, 0x01)
    state_store(raw_exp)
    b.branch(0xD0, "significand_ready")
    b.label("normal_significand")
    b.immediate(0xA0, 0x02)
    b.emit(0xB1, numerator_ptr)
    b.immediate(0x09, 0x80)
    b.emit(0x91, numerator_ptr)
    b.label("significand_ready")

    # value * 10**(6-d) = numerator / denominator, represented exactly.
    b.emit(0x38)
    b.immediate(0xA9, 0x06)
    b.immediate(0xA0, decimal_exp)
    b.emit(0xF1, state_ptr)
    state_store(decimal_scale)
    state_load(raw_exp)
    b.emit(0x18)
    b.immediate(0xA0, decimal_scale)
    b.emit(0x71, state_ptr)  # ADC (state),Y
    b.emit(0x38)
    b.immediate(0xE9, 150)
    state_store(binary_shift)

    state_load(decimal_scale)
    b.branch(0x30, "negative_decimal_scale")
    b.zero_page(0x85, loop_count)
    b.branch(0xF0, "decimal_scale_done")
    copy_pointer(numerator_ptr, work_ptr)
    b.label("multiply_numerator")
    jsr_local("m5")
    b.zero_page(0xC6, loop_count)
    b.branch(0xD0, "multiply_numerator")
    b.branch(0xF0, "decimal_scale_done")
    b.label("negative_decimal_scale")
    b.immediate(0x49, 0xFF)
    b.emit(0x18)
    b.immediate(0x69, 0x01)
    b.zero_page(0x85, loop_count)
    copy_pointer(denominator_ptr, work_ptr)
    b.label("multiply_denominator")
    jsr_local("m5")
    b.zero_page(0xC6, loop_count)
    b.branch(0xD0, "multiply_denominator")
    b.label("decimal_scale_done")

    state_load(binary_shift)
    b.branch(0x30, "negative_binary_shift")
    b.zero_page(0x85, loop_count)
    b.branch(0xF0, "binary_shift_done")
    copy_pointer(numerator_ptr, work_ptr)
    b.label("shift_numerator")
    jsr_local("shl")
    b.zero_page(0xC6, loop_count)
    b.branch(0xD0, "shift_numerator")
    b.branch(0xF0, "binary_shift_done")
    b.label("negative_binary_shift")
    b.immediate(0x49, 0xFF)
    b.emit(0x18)
    b.immediate(0x69, 0x01)
    b.zero_page(0x85, loop_count)
    copy_pointer(denominator_ptr, work_ptr)
    b.label("shift_denominator")
    jsr_local("shl")
    b.zero_page(0xC6, loop_count)
    b.branch(0xD0, "shift_denominator")
    b.label("binary_shift_done")

    # Divide the exact big integers, yielding at most eight decimal digits.
    b.immediate(0xA9, 160)
    b.zero_page(0x85, loop_count)
    b.label("bd")
    b.emit(0x18)
    b.immediate(0xA0, 0x00)
    b.immediate(0xA2, 20)
    b.label("divide_shift_numerator")
    b.emit(0xB1, numerator_ptr)
    b.emit(0x2A)
    b.emit(0x91, numerator_ptr)
    b.emit(0xC8)
    b.emit(0xCA)
    b.branch(0xD0, "divide_shift_numerator")
    b.immediate(0xA0, 0x00)
    b.immediate(0xA2, 20)
    b.label("divide_shift_remainder")
    b.emit(0xB1, remainder_ptr)
    b.emit(0x2A)
    b.emit(0x91, remainder_ptr)
    b.emit(0xC8)
    b.emit(0xCA)
    b.branch(0xD0, "divide_shift_remainder")
    b.emit(0x18)
    b.immediate(0xA0, 0x00)
    b.immediate(0xA2, 0x04)
    b.label("divide_shift_quotient")
    b.emit(0xB1, quotient_ptr)
    b.emit(0x2A)
    b.emit(0x91, quotient_ptr)
    b.emit(0xC8)
    b.emit(0xCA)
    b.branch(0xD0, "divide_shift_quotient")

    b.immediate(0xA0, 19)
    b.label("divide_compare")
    b.emit(0xB1, remainder_ptr)
    b.emit(0xD1, denominator_ptr)
    b.branch(0x90, "divide_no_subtract")
    b.branch(0xD0, "divide_subtract")
    b.emit(0x88)
    b.branch(0x10, "divide_compare")
    b.label("divide_subtract")
    b.emit(0x38)
    b.immediate(0xA0, 0x00)
    b.immediate(0xA2, 20)
    b.label("divide_subtract_loop")
    b.emit(0xB1, remainder_ptr)
    b.emit(0xF1, denominator_ptr)
    b.emit(0x91, remainder_ptr)
    b.emit(0xC8)
    b.emit(0xCA)
    b.branch(0xD0, "divide_subtract_loop")
    b.immediate(0xA0, 0x00)
    b.emit(0xB1, quotient_ptr)
    b.immediate(0x09, 0x01)
    b.emit(0x91, quotient_ptr)
    b.label("divide_no_subtract")
    b.zero_page(0xC6, loop_count)
    far_branch(b, 0xD0, "bd", "big_divide")

    # Round the exact rational to seven significant decimal digits, ties to even.
    b.emit(0x18)
    b.immediate(0xA0, 0x00)
    b.immediate(0xA2, 20)
    b.label("round_shift_remainder")
    b.emit(0xB1, remainder_ptr)
    b.emit(0x2A)
    b.emit(0x91, remainder_ptr)
    b.emit(0xC8)
    b.emit(0xCA)
    b.branch(0xD0, "round_shift_remainder")
    b.immediate(0xA0, 19)
    b.label("round_compare")
    b.emit(0xB1, remainder_ptr)
    b.emit(0xD1, denominator_ptr)
    b.branch(0x90, "round_done")
    b.branch(0xD0, "round_up_decimal")
    b.emit(0x88)
    b.branch(0x10, "round_compare")
    b.immediate(0xA0, 0x00)
    b.emit(0xB1, quotient_ptr)
    b.immediate(0x29, 0x01)
    b.branch(0xF0, "round_done")
    b.label("round_up_decimal")
    b.emit(0x18)
    b.immediate(0xA0, 0x00)
    b.emit(0xB1, quotient_ptr)
    b.immediate(0x69, 0x01)
    b.emit(0x91, quotient_ptr)
    b.emit(0xC8)
    b.immediate(0xA2, 0x03)
    b.label("round_carry")
    b.emit(0xB1, quotient_ptr)
    b.immediate(0x69, 0x00)
    b.emit(0x91, quotient_ptr)
    b.emit(0xC8)
    b.emit(0xCA)
    b.branch(0xD0, "round_carry")
    b.label("round_done")

    # A rounded 9,999,999.5 carries into the next decimal exponent.
    for offset, value in ((3, 0x00), (2, 0x98), (1, 0x96), (0, 0x80)):
        b.immediate(0xA0, offset)
        b.emit(0xB1, quotient_ptr)
        b.immediate(0xC9, value)
        b.branch(0xD0, "quotient_ready")
    for offset, value in enumerate((0x40, 0x42, 0x0F, 0x00)):
        b.immediate(0xA0, offset)
        b.immediate(0xA9, value)
        b.emit(0x91, quotient_ptr)
    state_load(decimal_exp)
    b.emit(0x18)
    b.immediate(0x69, 0x01)
    state_store(decimal_exp)
    b.label("quotient_ready")

    # Convert the seven-digit integer to unpacked decimal digits.
    b.immediate(0xA9, digits + 6)
    b.zero_page(0x85, loop_count)
    b.immediate(0xA9, 0x07)
    b.zero_page(0x85, scratch_hi)
    b.label("extract_digits")
    jsr_local("d10")
    b.zero_page(0xA4, loop_count)
    b.emit(0x91, state_ptr)
    b.zero_page(0xC6, loop_count)
    b.zero_page(0xC6, scratch_hi)
    b.branch(0xD0, "extract_digits")

    b.immediate(0xA2, 0x06)
    b.label("trim_digits")
    b.emit(0x8A)
    b.emit(0x18)
    b.immediate(0x69, digits)
    b.emit(0xA8)
    b.emit(0xB1, state_ptr)
    b.branch(0xD0, "digits_trimmed")
    b.emit(0xCA)
    b.branch(0x10, "trim_digits")
    b.label("digits_trimmed")
    b.emit(0x8A)
    state_store(last_digit)

    # Match C-style %g layout with precision seven.
    state_load(decimal_exp)
    b.branch(0x30, "format_negative_exp")
    b.immediate(0xC9, 0x07)
    b.branch(0x90, "format_fixed_jump")
    b.jmp_local("sci")
    b.label("format_negative_exp")
    b.immediate(0xC9, 0xFC)
    b.branch(0xB0, "format_fixed_jump")
    b.jmp_local("sci")
    b.label("format_fixed_jump")
    b.jmp_local("fix")

    b.label("fix")
    state_load(decimal_exp)
    b.branch(0x30, "fixed_negative")
    b.immediate(0xA9, 0x00)
    state_store(index)
    b.label("fixed_integer_loop")
    state_load(index)
    b.zero_page(0x85, scratch)
    state_load(last_digit)
    b.zero_page(0xC5, scratch)
    b.branch(0x90, "fixed_zero_digit")
    b.zero_page(0xA5, scratch)
    b.emit(0x18)
    b.immediate(0x69, digits)
    b.emit(0xA8)
    b.emit(0xB1, state_ptr)
    b.branch(0xD0, "fixed_emit_digit")
    b.label("fixed_zero_digit")
    b.immediate(0xA9, 0x00)
    b.label("fixed_emit_digit")
    emit_digit_from_a()
    state_load(index)
    b.emit(0x18)
    b.immediate(0x69, 0x01)
    state_store(index)
    state_load(index)
    b.zero_page(0x85, scratch)
    state_load(decimal_exp)
    b.zero_page(0xC5, scratch)
    b.branch(0xB0, "fixed_integer_loop")
    state_load(last_digit)
    b.zero_page(0x85, scratch)
    state_load(decimal_exp)
    b.zero_page(0xC5, scratch)
    b.branch(0xB0, "format_done")
    emit_ascii(ord("."))
    jsr_local("pd")
    b.label("format_done")
    b.emit(0x60)

    b.label("fixed_negative")
    emit_ascii(ord("0"))
    emit_ascii(ord("."))
    state_load(decimal_exp)
    b.immediate(0x49, 0xFF)
    b.emit(0x18)
    b.immediate(0x69, 0x01)
    b.emit(0x38)
    b.immediate(0xE9, 0x01)
    state_store(index)
    b.label("fixed_leading_zero_loop")
    state_load(index)
    b.branch(0xF0, "fixed_fraction_digits")
    emit_ascii(ord("0"))
    state_load(index)
    b.emit(0x38)
    b.immediate(0xE9, 0x01)
    state_store(index)
    b.branch(0xD0, "fixed_leading_zero_loop")
    b.label("fixed_fraction_digits")
    b.immediate(0xA9, 0x00)
    state_store(index)
    jsr_local("pd")
    b.emit(0x60)

    b.label("sci")
    state_load(digits)
    emit_digit_from_a()
    state_load(last_digit)
    b.branch(0xF0, "scientific_exponent")
    emit_ascii(ord("."))
    b.immediate(0xA9, 0x01)
    state_store(index)
    jsr_local("pd")
    b.label("scientific_exponent")
    emit_ascii(ord("E"))
    state_load(decimal_exp)
    b.branch(0x10, "positive_print_exponent")
    b.immediate(0x49, 0xFF)
    b.emit(0x18)
    b.immediate(0x69, 0x01)
    state_store(temp)
    emit_ascii(ord("-"))
    b.branch(0xD0, "print_exponent_magnitude")
    b.label("positive_print_exponent")
    state_store(temp)
    emit_ascii(ord("+"))
    b.label("print_exponent_magnitude")
    state_load(temp)
    b.immediate(0xC9, 10)
    b.branch(0x90, "print_exponent_ones")
    b.immediate(0xA2, 0x00)
    b.label("exponent_tens_loop")
    b.emit(0x38)
    b.immediate(0xE9, 10)
    b.emit(0xE8)
    b.immediate(0xC9, 10)
    b.branch(0xB0, "exponent_tens_loop")
    state_store(temp)
    b.emit(0x8A)
    emit_digit_from_a()
    state_load(temp)
    b.label("print_exponent_ones")
    emit_digit_from_a()
    b.emit(0x60)

    b.label("pz")
    state_load(sign)
    b.branch(0xF0, "print_zero_digit")
    emit_ascii(ord("-"))
    b.label("print_zero_digit")
    emit_ascii(ord("0"))
    b.emit(0x60)

    # Print digits[index..last_digit].
    b.label("pd")
    state_load(index)
    b.emit(0x18)
    b.immediate(0x69, digits)
    b.emit(0xA8)
    b.emit(0xB1, state_ptr)
    emit_digit_from_a()
    state_load(index)
    b.emit(0x18)
    b.immediate(0x69, 0x01)
    state_store(index)
    state_load(index)
    b.zero_page(0x85, scratch)
    state_load(last_digit)
    b.zero_page(0xC5, scratch)
    b.branch(0xB0, "pd")
    b.emit(0x60)

    # Restore all static-state pointers after KERNAL output may use zero page.
    b.label("ip")
    b.immediate(0xA2, 0x00)
    b.local_reference(0xBD, "sptr")
    b.zero_page(0x85, state_ptr)
    b.emit(0xE8)
    b.local_reference(0xBD, "sptr")
    b.zero_page(0x85, state_ptr + 1)
    set_state_pointer(numerator_ptr, numerator)
    set_state_pointer(denominator_ptr, denominator)
    set_state_pointer(remainder_ptr, remainder)
    set_state_pointer(quotient_ptr, quotient)
    b.immediate(0xA2, 0x00)
    b.local_reference(0xBD, "tptr")
    b.zero_page(0x85, table_ptr)
    b.emit(0xE8)
    b.local_reference(0xBD, "tptr")
    b.zero_page(0x85, table_ptr + 1)
    b.emit(0x60)

    # Multiply the 20-byte integer selected by work_ptr by five.
    b.label("m5")
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, carry)
    b.immediate(0xA0, 0x00)
    b.immediate(0xA2, 20)
    b.label("m5_loop")
    b.emit(0xB1, work_ptr)
    b.zero_page(0x85, scratch)
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, scratch_hi)
    b.zero_page(0xA5, scratch)
    for _ in range(2):
        b.emit(0x0A)
        b.zero_page(0x26, scratch_hi)
    b.emit(0x18)
    b.zero_page(0x65, scratch)
    b.branch(0x90, "m5_no_original_carry")
    b.zero_page(0xE6, scratch_hi)
    b.label("m5_no_original_carry")
    b.emit(0x18)
    b.zero_page(0x65, carry)
    b.branch(0x90, "m5_no_input_carry")
    b.zero_page(0xE6, scratch_hi)
    b.label("m5_no_input_carry")
    b.emit(0x91, work_ptr)
    b.zero_page(0xA5, scratch_hi)
    b.zero_page(0x85, carry)
    b.emit(0xC8)
    b.emit(0xCA)
    b.branch(0xD0, "m5_loop")
    b.emit(0x60)

    b.label("shl")
    b.emit(0x18)
    b.immediate(0xA0, 0x00)
    b.immediate(0xA2, 20)
    b.label("shl_loop")
    b.emit(0xB1, work_ptr)
    b.emit(0x2A)
    b.emit(0x91, work_ptr)
    b.emit(0xC8)
    b.emit(0xCA)
    b.branch(0xD0, "shl_loop")
    b.emit(0x60)

    # Divide the four-byte quotient by ten and return the remainder in A.
    b.label("d10")
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, carry)
    b.immediate(0xA9, 32)
    b.zero_page(0x85, scratch)
    b.label("d10_bit")
    b.emit(0x18)
    b.immediate(0xA0, 0x00)
    b.immediate(0xA2, 0x04)
    b.label("d10_shift")
    b.emit(0xB1, quotient_ptr)
    b.emit(0x2A)
    b.emit(0x91, quotient_ptr)
    b.emit(0xC8)
    b.emit(0xCA)
    b.branch(0xD0, "d10_shift")
    b.zero_page(0xA5, carry)
    b.emit(0x2A)
    b.zero_page(0x85, carry)
    b.immediate(0xC9, 10)
    b.branch(0x90, "d10_no_subtract")
    b.emit(0x38)
    b.immediate(0xE9, 10)
    b.zero_page(0x85, carry)
    b.immediate(0xA0, 0x00)
    b.emit(0xB1, quotient_ptr)
    b.immediate(0x09, 0x01)
    b.emit(0x91, quotient_ptr)
    b.label("d10_no_subtract")
    b.zero_page(0xC6, scratch)
    b.branch(0xD0, "d10_bit")
    b.zero_page(0xA5, carry)
    b.emit(0x60)

    b.label("emit")
    b.absolute(0x20, 0xFFD2)
    jsr_local("ip")
    b.emit(0x60)

    def relocatable_word(target: str) -> None:
        offset = len(b.code)
        b.emit(0x00, 0x00)
        b.local_relocations.append((offset, target))

    b.label("sptr")
    relocatable_word("state")
    b.label("tptr")
    relocatable_word("table")
    b.label("state")
    b.emit(*([0x00] * state_size))
    b.label("table")
    for exponent in range(38, -46, -1):
        b.emit(*binary32_power10_ceiling(exponent).to_bytes(4, "little"))

    b.export("rt_print_f")
    return b


def addsub_wrapper_module(module: str, subtract: bool) -> ObjectBuilder:
    b = ObjectBuilder(module)
    b.immediate(0xA9, 0x80 if subtract else 0x00)
    b.jsr("rt_f_addsub_core")
    b.emit(0x60)
    b.export(module)
    return b


def render_module(builder: ObjectBuilder) -> str:
    rendered = builder.render()
    for line in rendered.splitlines():
        if not line.startswith(("x ", "u ")):
            continue
        symbol = line.split()[1]
        if len(symbol) > ALINK_SYMBOL_MAX:
            raise ValueError(
                f"{builder.module} symbol exceeds ALINK's {ALINK_SYMBOL_MAX}-character "
                f"limit: {symbol}"
            )

    lines: list[str] = []
    for line in rendered.splitlines():
        if not line.startswith("m "):
            lines.append(line)
            continue
        code = bytes.fromhex(line[2:])
        for offset in range(0, len(code), 64):
            chunk = code[offset : offset + 64]
            lines.append("m " + " ".join(f"{value:02X}" for value in chunk))
    lines.append(f"n {builder.module}")
    return "\n".join(lines) + "\n"


def link_runtime_builders(builders: list[ObjectBuilder], load_addr: int) -> bytes:
    """Link generated builders into one absolute test image."""
    addresses: dict[str, int] = {}
    cursor = load_addr
    for builder in builders:
        builder.render()
        for export in builder.exports:
            addresses[export.name] = cursor + export.offset
        cursor += len(builder.code)

    image = bytearray()
    cursor = load_addr
    for builder in builders:
        code = bytearray(builder.code)
        for offset, label in builder.local_relocations:
            address = cursor + builder.labels[label]
            code[offset] = address & 0xFF
            code[offset + 1] = address >> 8
        for offset, symbol in builder.relocations:
            address = addresses[symbol]
            code[offset] = address & 0xFF
            code[offset + 1] = address >> 8
        image.extend(code)
        cursor += len(code)
    return bytes(image)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate standalone math OBJ1 modules")
    parser.add_argument("--output", type=Path, action="append")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    runtime_root = Path(__file__).resolve().parents[1] / "src" / "runtime"
    outputs = args.output or [runtime_root / "modules", runtime_root / "udos_modules"]
    expected = {
        builder.module: render_module(builder)
        for builder in (
            special_value_module(),
            compare_module(),
            minmax_module("rt_f_min", maximum=False),
            minmax_module("rt_f_max", maximum=True),
            float_to_int_module(),
            addsub_core_module(),
            multiply_module(),
            divide_module(),
            square_root_module(),
            print_float_module(),
            addsub_wrapper_module("rt_f_add", False),
            addsub_wrapper_module("rt_f_sub", True),
        )
    }
    stale: list[Path] = []
    for output in outputs:
        for module, text in expected.items():
            path = output / f"{module}.obj"
            if args.check:
                if not path.is_file() or path.read_text(encoding="ascii") != text:
                    stale.append(path)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="ascii")

    if stale:
        for path in stale:
            print(f"STALE {path}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
