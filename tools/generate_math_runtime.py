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
DEGREES_TO_RADIANS_BITS = 0x3C8EFA35
RADIANS_TO_DEGREES_BITS = 0x42652EE0
EXP_UPPER_BITS = 0x42B17218
EXP_LOWER_BITS = 0xC2CFF1B5
EXP_LN2_BITS = 0x3F317218
EXP_COEFFICIENT_BITS = (
    0x3F800000,
    0x3F800000,
    0x3F000000,
    0x3E2AAAAB,
    0x3D2AAAAB,
    0x3C088889,
    0x3AB60B61,
    0x39500D01,
    0x37D00D01,
)
LN_SQRT2_BITS = 0x3FB504F3
LN_INVERSE_SQRT2_BITS = 0x3F3504F3
LN_ODD_DENOMINATOR_BITS = (
    0x40400000,
    0x40A00000,
    0x40E00000,
    0x41100000,
    0x41300000,
    0x41500000,
)
LN10_BITS = 0x40135D8E


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


def clamp_module() -> ObjectBuilder:
    """Build FClamp from the link-selected comparison/min/max primitives."""
    b = ObjectBuilder("rt_f_clamp")

    # Entry pointers are value=$02, lower=$04, destination=$06, upper=$08.
    # Save them before calling dependencies because their zero-page workspaces
    # overlap the public argument area.
    b.immediate(0xA2, 0x07)  # LDX #7
    b.label("save_pointers")
    b.emit(0xB5, 0x02)  # LDA $02,X
    b.local_reference(0x9D, "state")  # STA state,X
    b.emit(0xCA)  # DEX
    b.branch(0x10, "save_pointers")  # BPL

    # Reject NaN value/lower/upper inputs exactly as the portable MATH1 source.
    for offset, tag in ((0, "value"), (2, "lower"), (6, "upper")):
        b.immediate(0xA2, offset)
        b.local_reference(0x20, "set_left")
        b.immediate(0xA2, offset)
        b.local_reference(0x20, "set_right")
        b.jsr("rt_f_cmp")
        b.immediate(0xC9, 0x02)
        far_branch(b, 0xF0, "qnan", f"{tag}_nan")

    # An inverted interval is invalid even when value happens to be in range.
    b.immediate(0xA2, 0x02)
    b.local_reference(0x20, "set_left")
    b.immediate(0xA2, 0x06)
    b.local_reference(0x20, "set_right")
    b.jsr("rt_f_cmp")
    b.immediate(0xC9, 0x01)
    b.branch(0xF0, "qnan")

    # temp = FMax(value, lower)
    b.immediate(0xA2, 0x00)
    b.local_reference(0x20, "set_left")
    b.immediate(0xA2, 0x02)
    b.local_reference(0x20, "set_right")
    b.immediate(0xA2, 0x08)
    b.local_reference(0x20, "set_dst")
    b.jsr("rt_f_max")

    # destination = FMin(temp, upper)
    b.immediate(0xA2, 0x08)
    b.local_reference(0x20, "set_left")
    b.immediate(0xA2, 0x06)
    b.local_reference(0x20, "set_right")
    b.immediate(0xA2, 0x04)
    b.local_reference(0x20, "set_dst")
    b.jsr("rt_f_min")
    b.emit(0x60)  # RTS

    b.label("qnan")
    b.immediate(0xA2, 0x04)
    b.local_reference(0x20, "set_dst")
    b.immediate(0xA0, 0x00)
    b.immediate(0xA9, 0x00)
    b.emit(0x91, 0x06, 0xC8, 0x91, 0x06, 0xC8)
    b.immediate(0xA9, 0xC0)
    b.emit(0x91, 0x06, 0xC8)
    b.immediate(0xA9, 0x7F)
    b.emit(0x91, 0x06, 0x60)

    for label, destination in (
        ("set_left", 0x02),
        ("set_right", 0x04),
        ("set_dst", 0x06),
    ):
        b.label(label)
        b.local_reference(0xBD, "state")  # LDA state,X
        b.zero_page(0x85, destination)
        b.emit(0xE8)  # INX
        b.local_reference(0xBD, "state")
        b.zero_page(0x85, destination + 1)
        b.emit(0x60)

    b.label("state")
    b.emit(*([0x00] * 8))  # Four saved entry pointers.
    temp_pointer_offset = len(b.code)
    b.emit(0x00, 0x00)
    b.local_relocations.append((temp_pointer_offset, "temp"))
    b.label("temp")
    b.emit(0x00, 0x00, 0x00, 0x00)
    # The primary export owns the private state and temporary storage too;
    # ALINK only retains relocations inside a selected export's byte range.
    b.export("rt_f_clamp")
    return b


def sign_module() -> ObjectBuilder:
    """Build FSign with canonical NaN and signed-zero preservation."""
    b = ObjectBuilder("rt_f_sign")

    sign_byte = 0x08
    scratch = 0x09

    # Detect NaN directly so the helper has no transitive dependencies.
    b.immediate(0xA0, 0x03)
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.zero_page(0x85, sign_byte)
    b.immediate(0x29, 0x7F)
    b.immediate(0xC9, 0x7F)
    b.branch(0xD0, "classify")
    b.emit(0x88)  # DEY
    b.emit(0xB1, 0x02)
    b.immediate(0x29, 0x80)
    b.branch(0xF0, "classify")
    b.emit(0xB1, 0x02)
    b.immediate(0x29, 0x7F)
    b.zero_page(0x85, scratch)
    b.emit(0x88)
    b.emit(0xB1, 0x02)
    b.zero_page(0x05, scratch)
    b.zero_page(0x85, scratch)
    b.emit(0x88)
    b.emit(0xB1, 0x02)
    b.zero_page(0x05, scratch)
    b.branch(0xF0, "classify")  # Infinity maps to signed one.

    # MATH1 returns its NAN constant rather than preserving an input payload.
    b.immediate(0xA0, 0x00)
    b.immediate(0xA9, 0x00)
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.immediate(0xA9, 0xC0)
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.immediate(0xA9, 0x7F)
    b.emit(0x91, 0x06)
    b.emit(0x60)

    b.label("classify")
    b.immediate(0xA0, 0x00)
    b.emit(0xB1, 0x02)
    b.emit(0xC8)
    b.emit(0x11, 0x02)  # ORA ($02),Y
    b.emit(0xC8)
    b.emit(0x11, 0x02)
    b.zero_page(0x85, scratch)
    b.zero_page(0xA5, sign_byte)
    b.immediate(0x29, 0x7F)
    b.zero_page(0x05, scratch)
    b.branch(0xF0, "copy_zero")
    b.zero_page(0xA5, sign_byte)
    b.branch(0x30, "negative")
    b.immediate(0xA9, 0x3F)
    b.branch(0xD0, "write_one")
    b.label("negative")
    b.immediate(0xA9, 0xBF)
    b.label("write_one")
    b.zero_page(0x85, sign_byte)
    b.immediate(0xA0, 0x00)
    b.immediate(0xA9, 0x00)
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.immediate(0xA9, 0x80)
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.zero_page(0xA5, sign_byte)
    b.emit(0x91, 0x06)
    b.emit(0x60)

    b.label("copy_zero")
    b.immediate(0xA0, 0x00)
    b.label("copy_zero_loop")
    b.emit(0xB1, 0x02)
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "copy_zero_loop")
    b.emit(0x60)

    b.export("rt_f_sign")
    return b


def abs_module() -> ObjectBuilder:
    """Build binary32 absolute value by clearing only the sign bit."""
    b = ObjectBuilder("rt_f_abs")
    b.immediate(0xA0, 0x00)
    b.label("copy")
    b.emit(0xB1, 0x02)
    b.immediate(0xC0, 0x03)
    b.branch(0xD0, "store")
    b.immediate(0x29, 0x7F)
    b.label("store")
    b.emit(0x91, 0x06, 0xC8)
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "copy")
    b.emit(0x60)
    b.export("rt_f_abs")
    return b


def angle_scale_module(module: str, factor_bits: int) -> ObjectBuilder:
    """Build an alias-safe unary angle conversion through binary32 multiply."""
    b = ObjectBuilder(module)
    b.local_reference(0xAD, "p")  # LDA factor pointer low byte.
    b.zero_page(0x85, 0x04)
    b.local_reference(0xAD, "ph")  # LDA factor pointer high byte.
    b.zero_page(0x85, 0x05)
    b.jsr("rt_f_mul")
    b.emit(0x60)

    b.label("p")
    pointer_offset = len(b.code)
    b.emit(0x00)
    b.label("ph")
    b.emit(0x00)
    b.local_relocations.append((pointer_offset, "k"))
    b.label("k")
    b.emit(*factor_bits.to_bytes(4, "little"))
    b.export(module)
    return b


def deg_to_rad_module() -> ObjectBuilder:
    return angle_scale_module("rt_f_deg_to_rad", DEGREES_TO_RADIANS_BITS)


def rad_to_deg_module() -> ObjectBuilder:
    return angle_scale_module("rt_f_rad_to_deg", RADIANS_TO_DEGREES_BITS)


def trunc_module() -> ObjectBuilder:
    """Build binary32 truncation toward zero without arithmetic helpers."""
    b = ObjectBuilder("rt_f_trunc")

    sign_byte = 0x08
    count = 0x09

    # Reconstruct the biased exponent while retaining the source sign.
    b.immediate(0xA0, 0x03)  # LDY #3
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.zero_page(0x85, sign_byte)
    b.immediate(0x29, 0x7F)
    b.emit(0x0A)  # ASL
    b.zero_page(0x85, count)
    b.emit(0x88)  # DEY
    b.emit(0xB1, 0x02)
    b.immediate(0x29, 0x80)
    b.branch(0xF0, "exponent_ready")
    b.zero_page(0xE6, count)

    b.label("exponent_ready")
    b.zero_page(0xA5, count)
    b.immediate(0xC9, 0x96)  # Bias 127 + 23 fraction bits.
    b.branch(0x90, "maybe_fractional")
    # This also preserves infinities and every NaN payload bit-for-bit.
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, count)
    b.branch(0xF0, "copy_value")

    b.label("maybe_fractional")
    b.immediate(0xC9, 0x7F)
    b.branch(0x90, "write_zero")
    b.immediate(0xA9, 0x96)
    b.emit(0x38)  # SEC
    b.zero_page(0xE5, count)
    b.zero_page(0x85, count)

    b.label("copy_value")
    b.immediate(0xA0, 0x00)
    b.label("copy_loop")
    b.emit(0xB1, 0x02)
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "copy_loop")
    b.zero_page(0xA5, count)
    b.branch(0xF0, "done")

    # Clear 150-exponent low significand bits in the copied destination.
    b.immediate(0xA0, 0x00)
    b.immediate(0xA9, 0x01)
    b.zero_page(0x85, sign_byte)
    b.label("clear_loop")
    b.zero_page(0xA5, sign_byte)
    b.immediate(0x49, 0xFF)
    b.emit(0x31, 0x06)  # AND ($06),Y
    b.emit(0x91, 0x06)
    b.zero_page(0xA5, sign_byte)
    b.emit(0x0A)  # ASL
    b.zero_page(0x85, sign_byte)
    b.branch(0xD0, "mask_ready")
    b.emit(0xC8)
    b.immediate(0xA9, 0x01)
    b.zero_page(0x85, sign_byte)
    b.label("mask_ready")
    b.zero_page(0xC6, count)
    b.branch(0xD0, "clear_loop")
    b.label("done")
    b.emit(0x60)

    b.label("write_zero")
    b.immediate(0xA0, 0x02)
    b.immediate(0xA9, 0x00)
    b.label("zero_loop")
    b.emit(0x91, 0x06)
    b.emit(0x88)
    b.branch(0x10, "zero_loop")
    b.immediate(0xA0, 0x03)
    b.zero_page(0xA5, sign_byte)
    b.immediate(0x29, 0x80)
    b.emit(0x91, 0x06)
    b.emit(0x60)

    b.export("rt_f_trunc")
    return b


def floor_module() -> ObjectBuilder:
    """Build binary32 floor from truncation plus an exact magnitude increment."""
    b = ObjectBuilder("rt_f_floor")

    count = 0x08
    mask = 0x09
    source_copy = 0x0A

    # Preserve the input so source and destination may refer to the same cell.
    b.immediate(0xA0, 0x00)  # LDY #0
    b.label("save_loop")
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.emit(0x99, source_copy, 0x00)  # STA source_copy,Y
    b.emit(0xC8)  # INY
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "save_loop")

    b.jsr("rt_f_trunc")

    # Positive values already have their floor. Negative integral values,
    # infinities, NaNs, and signed zero are unchanged by truncation too.
    b.immediate(0xA0, 0x03)
    b.emit(0xB9, source_copy, 0x00)  # LDA source_copy,Y
    b.branch(0x10, "done")  # BPL
    b.immediate(0xA0, 0x00)
    b.label("compare_loop")
    b.emit(0xB9, source_copy, 0x00)
    b.emit(0xD1, 0x06)  # CMP ($06),Y
    b.branch(0xD0, "negative_fraction")
    b.emit(0xC8)
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "compare_loop")
    b.label("done")
    b.emit(0x60)

    b.label("negative_fraction")
    # Reconstruct the truncated result's biased exponent.
    b.immediate(0xA0, 0x03)
    b.emit(0xB1, 0x06)
    b.immediate(0x29, 0x7F)
    b.emit(0x0A)  # ASL
    b.zero_page(0x85, count)
    b.emit(0x88)  # DEY
    b.emit(0xB1, 0x06)
    b.immediate(0x29, 0x80)
    b.branch(0xF0, "exponent_ready")
    b.zero_page(0xE6, count)

    b.label("exponent_ready")
    b.zero_page(0xA5, count)
    b.immediate(0xC9, 0x7F)
    b.branch(0x90, "write_negative_one")
    b.immediate(0xA9, 0x96)
    b.emit(0x38)  # SEC
    b.zero_page(0xE5, count)
    b.zero_page(0x85, count)

    # Add one integer unit to the truncated magnitude. The low COUNT bits are
    # zero, so this is an exact increment even when it carries into exponent.
    b.immediate(0xA0, 0x00)
    b.label("select_byte")
    b.zero_page(0xA5, count)
    b.immediate(0xC9, 0x08)
    b.branch(0x90, "select_bit")
    b.emit(0x38)
    b.immediate(0xE9, 0x08)  # SBC #8
    b.zero_page(0x85, count)
    b.emit(0xC8)
    b.branch(0xD0, "select_byte")

    b.label("select_bit")
    b.immediate(0xA9, 0x01)
    b.zero_page(0xA6, count)  # LDX count
    b.branch(0xF0, "add_unit")
    b.label("shift_bit")
    b.emit(0x0A)  # ASL
    b.emit(0xCA)  # DEX
    b.branch(0xD0, "shift_bit")

    b.label("add_unit")
    b.zero_page(0x85, mask)
    b.emit(0x18)  # CLC
    b.emit(0xB1, 0x06)
    b.zero_page(0x65, mask)
    b.emit(0x91, 0x06)
    b.branch(0x90, "done")
    b.label("carry_unit")
    b.emit(0xC8)
    b.emit(0xB1, 0x06)
    b.immediate(0x69, 0x00)
    b.emit(0x91, 0x06)
    b.branch(0xB0, "carry_unit")
    b.emit(0x60)

    b.label("write_negative_one")
    b.immediate(0xA0, 0x00)
    b.immediate(0xA9, 0x00)
    b.emit(0x91, 0x06, 0xC8, 0x91, 0x06, 0xC8)
    b.immediate(0xA9, 0x80)
    b.emit(0x91, 0x06, 0xC8)
    b.immediate(0xA9, 0xBF)
    b.emit(0x91, 0x06, 0x60)

    b.export("rt_f_floor")
    return b


def ceil_module() -> ObjectBuilder:
    """Build binary32 ceiling by applying floor to the negated operand."""
    b = ObjectBuilder("rt_f_ceil")

    source_copy = 0x0A

    # Preserve the input before changing its sign so source and destination may
    # refer to the same cell. The identity ceil(x) = -floor(-x) also preserves
    # NaN payloads, infinities, integral values, and signed zero bit-for-bit.
    b.immediate(0xA0, 0x00)  # LDY #0
    b.label("save_loop")
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.emit(0x99, source_copy, 0x00)  # STA source_copy,Y
    b.emit(0xC8)  # INY
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "save_loop")

    b.immediate(0xA0, 0x03)
    b.emit(0xB9, source_copy, 0x00)
    b.immediate(0x49, 0x80)
    b.emit(0x99, source_copy, 0x00)
    b.immediate(0xA9, source_copy)
    b.zero_page(0x85, 0x02)
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, 0x03)
    b.jsr("rt_f_floor")

    b.immediate(0xA0, 0x03)
    b.emit(0xB1, 0x06)
    b.immediate(0x49, 0x80)
    b.emit(0x91, 0x06)
    b.emit(0x60)

    b.export("rt_f_ceil")
    return b


def round_module() -> ObjectBuilder:
    """Build binary32 round-to-nearest with halfway cases away from zero."""
    b = ObjectBuilder("rt_f_round")

    count = 0x08
    mask = 0x09
    source_copy = 0x0A

    # Preserve the source before truncation so aliased source/destination
    # pointers are safe and integral or exceptional inputs can be returned
    # without reconstructing their payload bits.
    b.immediate(0xA0, 0x00)  # LDY #0
    b.label("save_loop")
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.emit(0x99, source_copy, 0x00)  # STA source_copy,Y
    b.emit(0xC8)  # INY
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "save_loop")

    b.jsr("rt_f_trunc")

    # Truncation is bit-identical for signed zero, integral values, infinities,
    # and NaNs. Returning here also avoids the large-integral error caused by
    # implementing round as floor(value + 0.5) unconditionally.
    b.immediate(0xA0, 0x00)
    b.label("compare_loop")
    b.emit(0xB9, source_copy, 0x00)
    b.emit(0xD1, 0x06)  # CMP ($06),Y
    b.branch(0xD0, "fractional")
    b.emit(0xC8)
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "compare_loop")
    b.label("done")
    b.emit(0x60)

    # Reconstruct the biased exponent from the saved source.
    b.label("fractional")
    b.immediate(0xA0, 0x03)
    b.emit(0xB9, source_copy, 0x00)
    b.immediate(0x29, 0x7F)
    b.emit(0x0A)  # ASL
    b.zero_page(0x85, count)
    b.emit(0x88)  # DEY
    b.emit(0xB9, source_copy, 0x00)
    b.immediate(0x29, 0x80)
    b.branch(0xF0, "exponent_ready")
    b.zero_page(0xE6, count)

    b.label("exponent_ready")
    b.zero_page(0xA5, count)
    b.immediate(0xC9, 0x7E)  # abs(value) < 0.5
    b.branch(0x90, "done")
    b.branch(0xF0, "write_signed_one")  # abs(value) is in [0.5, 1)

    # For exponents 127..149, bit (149-exponent) is the 0.5 place.
    b.immediate(0xA9, 0x95)  # 149
    b.emit(0x38)  # SEC
    b.zero_page(0xE5, count)
    b.zero_page(0x85, count)
    b.immediate(0xA0, 0x00)
    b.label("select_half_byte")
    b.zero_page(0xA5, count)
    b.immediate(0xC9, 0x08)
    b.branch(0x90, "select_half_bit")
    b.emit(0x38)
    b.immediate(0xE9, 0x08)
    b.zero_page(0x85, count)
    b.emit(0xC8)
    b.branch(0xD0, "select_half_byte")

    b.label("select_half_bit")
    b.immediate(0xA9, 0x01)
    b.zero_page(0xA6, count)  # LDX count
    b.branch(0xF0, "half_mask_ready")
    b.label("shift_half_bit")
    b.emit(0x0A)  # ASL
    b.emit(0xCA)  # DEX
    b.branch(0xD0, "shift_half_bit")
    b.label("half_mask_ready")
    b.zero_page(0x85, mask)
    b.emit(0x39, source_copy, 0x00)  # AND source_copy,Y
    b.branch(0xF0, "done")

    # The halfway bit and every larger fraction round away from zero. Move the
    # mask one place left to obtain one integer unit at this exponent, then add
    # it to the already-truncated magnitude.
    b.zero_page(0xA5, mask)
    b.emit(0x0A)  # ASL
    b.branch(0xD0, "unit_mask_ready")
    b.emit(0xC8)  # INY
    b.immediate(0xA9, 0x01)
    b.label("unit_mask_ready")
    b.zero_page(0x85, mask)
    b.emit(0x18)  # CLC
    b.emit(0xB1, 0x06)
    b.zero_page(0x65, mask)
    b.emit(0x91, 0x06)
    b.branch(0x90, "done")
    b.label("carry_unit")
    b.emit(0xC8)
    b.emit(0xB1, 0x06)
    b.immediate(0x69, 0x00)
    b.emit(0x91, 0x06)
    b.branch(0xB0, "carry_unit")
    b.emit(0x60)

    b.label("write_signed_one")
    b.immediate(0xA0, 0x00)
    b.immediate(0xA9, 0x00)
    b.emit(0x91, 0x06, 0xC8, 0x91, 0x06, 0xC8)
    b.immediate(0xA9, 0x80)
    b.emit(0x91, 0x06, 0xC8)
    b.emit(0xB9, source_copy, 0x00)
    b.immediate(0x29, 0x80)
    b.immediate(0x09, 0x3F)
    b.emit(0x91, 0x06, 0x60)

    b.export("rt_f_round")
    return b


def frac_module() -> ObjectBuilder:
    """Build the signed fractional part as value - trunc(value)."""
    b = ObjectBuilder("rt_f_frac")

    def load_local_pointer(low: str, high: str, destination: int) -> None:
        b.local_reference(0xAD, low)  # LDA pointer low
        b.zero_page(0x85, destination)
        b.local_reference(0xAD, high)  # LDA pointer high
        b.zero_page(0x85, destination + 1)

    # Preserve the caller's destination and operand outside zero page because
    # both dependencies own the shared arithmetic scratch area. Keeping the
    # inputs private also makes source/destination aliasing safe.
    b.zero_page(0xA5, 0x06)
    b.local_reference(0x8D, "dp")
    b.zero_page(0xA5, 0x07)
    b.local_reference(0x8D, "dph")
    b.immediate(0xA0, 0x00)
    b.label("save")
    b.emit(0xB1, 0x02)  # LDA ($02),Y
    b.local_reference(0x99, "src")  # STA src,Y
    b.emit(0xC8)
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "save")

    load_local_pointer("sp", "sph", 0x02)
    load_local_pointer("tp", "tph", 0x06)
    b.jsr("rt_f_trunc")

    load_local_pointer("sp", "sph", 0x02)
    load_local_pointer("tp", "tph", 0x04)
    load_local_pointer("dp", "dph", 0x06)
    b.jsr("rt_f_sub")
    b.emit(0x60)

    b.label("sp")
    source_pointer_offset = len(b.code)
    b.emit(0x00)
    b.label("sph")
    b.emit(0x00)
    b.local_relocations.append((source_pointer_offset, "src"))
    b.label("tp")
    trunc_pointer_offset = len(b.code)
    b.emit(0x00)
    b.label("tph")
    b.emit(0x00)
    b.local_relocations.append((trunc_pointer_offset, "trunc"))
    b.label("dp")
    b.emit(0x00)
    b.label("dph")
    b.emit(0x00)
    b.label("src")
    b.emit(0x00, 0x00, 0x00, 0x00)
    b.label("trunc")
    b.emit(0x00, 0x00, 0x00, 0x00)

    b.export("rt_f_frac")
    return b


def mod_module() -> ObjectBuilder:
    """Build value - trunc(value / divisor) * divisor."""
    b = ObjectBuilder("rt_f_mod")

    def load_local_pointer(low: str, high: str, destination: int) -> None:
        b.local_reference(0xAD, low)
        b.zero_page(0x85, destination)
        b.local_reference(0xAD, high)
        b.zero_page(0x85, destination + 1)

    def emit_pointer(low: str, high: str, target: str) -> None:
        b.label(low)
        offset = len(b.code)
        b.emit(0x00)
        b.label(high)
        b.emit(0x00)
        b.local_relocations.append((offset, target))

    # Every dependency uses overlapping zero-page work areas. Preserve both
    # operands before the first call so either one may alias the destination.
    b.zero_page(0xA5, 0x06)
    b.local_reference(0x8D, "dp")
    b.zero_page(0xA5, 0x07)
    b.local_reference(0x8D, "dph")
    b.immediate(0xA0, 0x00)
    b.label("save")
    b.emit(0xB1, 0x02)
    b.local_reference(0x99, "value")
    b.emit(0xB1, 0x04)
    b.local_reference(0x99, "divisor")
    b.emit(0xC8)
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "save")

    # The portable MATH1 contract returns a finite value unchanged when the
    # divisor is either infinity. NaN divisors and non-finite values continue
    # through the arithmetic closure, which canonicalizes them to quiet NaN.
    b.local_reference(0xAD, "divisor_3")
    b.immediate(0x29, 0x7F)
    b.immediate(0xC9, 0x7F)
    b.branch(0xD0, "calculate")
    b.local_reference(0xAD, "divisor_2")
    b.immediate(0xC9, 0x80)
    b.branch(0xD0, "calculate")
    b.local_reference(0xAD, "divisor_1")
    b.local_reference(0x0D, "divisor")
    b.branch(0xD0, "calculate")
    b.local_reference(0xAD, "value_3")
    b.immediate(0x29, 0x7F)
    b.immediate(0xC9, 0x7F)
    b.branch(0xD0, "return_value")
    b.local_reference(0xAD, "value_2")
    b.immediate(0x29, 0x80)
    b.branch(0xD0, "calculate")
    b.label("return_value")
    load_local_pointer("dp", "dph", 0x06)
    b.immediate(0xA0, 0x00)
    b.label("return_value_loop")
    b.local_reference(0xB9, "value")
    b.emit(0x91, 0x06)
    b.emit(0xC8)
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "return_value_loop")
    b.emit(0x60)

    b.label("calculate")
    load_local_pointer("vp", "vph", 0x02)
    load_local_pointer("rp", "rph", 0x04)
    load_local_pointer("qp", "qph", 0x06)
    b.jsr("rt_f_div")

    load_local_pointer("qp", "qph", 0x02)
    load_local_pointer("tp", "tph", 0x06)
    b.jsr("rt_f_trunc")

    load_local_pointer("tp", "tph", 0x02)
    load_local_pointer("rp", "rph", 0x04)
    load_local_pointer("pp", "pph", 0x06)
    b.jsr("rt_f_mul")

    load_local_pointer("vp", "vph", 0x02)
    load_local_pointer("pp", "pph", 0x04)
    load_local_pointer("dp", "dph", 0x06)
    b.jsr("rt_f_sub")
    b.emit(0x60)

    emit_pointer("vp", "vph", "value")
    emit_pointer("rp", "rph", "divisor")
    emit_pointer("qp", "qph", "quotient")
    emit_pointer("tp", "tph", "truncated")
    emit_pointer("pp", "pph", "product")
    b.label("dp")
    b.emit(0x00)
    b.label("dph")
    b.emit(0x00)
    for label in ("value", "divisor", "quotient", "truncated", "product"):
        for index in range(4):
            b.label(label if index == 0 else f"{label}_{index}")
            b.emit(0x00)

    b.export("rt_f_mod")
    return b


def hypot_module() -> ObjectBuilder:
    """Build a scaled square root of x*x + y*y without avoidable overflow."""
    b = ObjectBuilder("rt_f_hypot")

    pointer_targets = (
        "destination",
        "left",
        "right",
        "left_abs",
        "right_abs",
        "largest",
        "smallest",
        "ratio",
        "square",
        "one",
        "sum",
        "root",
    )
    pointer_offsets = {
        target: index * 2 for index, target in enumerate(pointer_targets)
    }

    def load_local_pointer(target: str, destination: int) -> None:
        b.immediate(0xA2, pointer_offsets[target])
        b.local_reference(0xBD, "pt")
        b.zero_page(0x85, destination)
        b.emit(0xE8)
        b.local_reference(0xBD, "pt")
        b.zero_page(0x85, destination + 1)

    # Dependencies share zero-page scratch, so snapshot both source values and
    # the caller's destination before invoking any helper.
    b.immediate(0xA2, pointer_offsets["destination"])
    b.zero_page(0xA5, 0x06)
    b.local_reference(0x9D, "pt")
    b.emit(0xE8)
    b.zero_page(0xA5, 0x07)
    b.local_reference(0x9D, "pt")
    b.immediate(0xA0, 0x00)
    b.label("save")
    b.emit(0xB1, 0x02)
    b.local_reference(0x99, "left")
    b.emit(0xB1, 0x04)
    b.local_reference(0x99, "right")
    b.emit(0xC8)
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "save")

    load_local_pointer("left", 0x02)
    load_local_pointer("left_abs", 0x06)
    b.jsr("rt_f_abs")
    load_local_pointer("right", 0x02)
    load_local_pointer("right_abs", 0x06)
    b.jsr("rt_f_abs")

    load_local_pointer("left_abs", 0x02)
    load_local_pointer("right_abs", 0x04)
    load_local_pointer("largest", 0x06)
    b.jsr("rt_f_max")
    load_local_pointer("left_abs", 0x02)
    load_local_pointer("right_abs", 0x04)
    load_local_pointer("smallest", 0x06)
    b.jsr("rt_f_min")

    # FAbs makes every finite magnitude and infinity nonnegative. Preserve
    # exact positive infinity and zero instead of entering a 0/0 or inf/inf
    # arithmetic path.
    b.local_reference(0xAD, "largest_3")
    b.immediate(0xC9, 0x7F)
    b.branch(0xD0, "check_zero")
    b.local_reference(0xAD, "largest_2")
    b.immediate(0xC9, 0x80)
    b.branch(0xD0, "calculate")
    b.local_reference(0xAD, "largest_1")
    b.local_reference(0x0D, "largest")
    b.branch(0xF0, "return_largest")
    b.jmp_local("calculate")

    b.label("check_zero")
    b.local_reference(0xAD, "largest")
    b.local_reference(0x0D, "largest_1")
    b.local_reference(0x0D, "largest_2")
    b.local_reference(0x0D, "largest_3")
    b.branch(0xD0, "calculate")
    b.label("return_largest")
    load_local_pointer("destination", 0x06)
    b.immediate(0xA0, 0x00)
    b.label("return_loop")
    b.local_reference(0xB9, "largest")
    b.emit(0x91, 0x06, 0xC8)
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "return_loop")
    b.emit(0x60)

    b.label("calculate")
    load_local_pointer("smallest", 0x02)
    load_local_pointer("largest", 0x04)
    load_local_pointer("ratio", 0x06)
    b.jsr("rt_f_div")
    load_local_pointer("ratio", 0x02)
    load_local_pointer("ratio", 0x04)
    load_local_pointer("square", 0x06)
    b.jsr("rt_f_mul")
    load_local_pointer("one", 0x02)
    load_local_pointer("square", 0x04)
    load_local_pointer("sum", 0x06)
    b.jsr("rt_f_add")
    load_local_pointer("sum", 0x02)
    load_local_pointer("root", 0x06)
    b.jsr("rt_f_sqrt")
    load_local_pointer("largest", 0x02)
    load_local_pointer("root", 0x04)
    load_local_pointer("destination", 0x06)
    b.jsr("rt_f_mul")
    b.emit(0x60)

    b.label("pt")
    b.emit(0x00, 0x00)
    for target in pointer_targets[1:]:
        offset = len(b.code)
        b.emit(0x00, 0x00)
        b.local_relocations.append((offset, target))
    for label in (
        "left",
        "right",
        "left_abs",
        "right_abs",
        "largest",
        "smallest",
        "ratio",
        "square",
        "sum",
        "root",
    ):
        for index in range(4):
            b.label(label if index == 0 else f"{label}_{index}")
            b.emit(0x00)
    b.label("one")
    b.emit(0x00, 0x00, 0x80, 0x3F)

    b.export("rt_f_hypot")
    return b


def exp_module() -> ObjectBuilder:
    """Build the portable MATH1 degree-8 binary32 exponential."""
    b = ObjectBuilder("rt_f_exp")

    pointer_targets = (
        "destination",
        "value",
        "quotient",
        "exponent",
        "product",
        "reduced",
        "accum",
        "work",
        "ln2",
        "two",
        *(f"c{index}" for index in range(len(EXP_COEFFICIENT_BITS))),
        "nan",
        "inf",
        "zero",
    )
    pointer_offsets = {
        target: index * 2 for index, target in enumerate(pointer_targets)
    }

    def load_local_pointer(target: str, destination: int) -> None:
        b.immediate(0xA2, pointer_offsets[target])
        b.local_reference(0xBD, "pt")
        b.zero_page(0x85, destination)
        b.emit(0xE8)
        b.local_reference(0xBD, "pt")
        b.zero_page(0x85, destination + 1)

    def load_input_byte(index: int) -> None:
        b.immediate(0xA0, index)
        b.emit(0xB1, 0x02)

    def compare_magnitude(
        bits: int, *, clear_sign: bool, overflow: str, tag: str
    ) -> None:
        if clear_sign:
            bits &= 0x7FFFFFFF
        encoded = bits.to_bytes(4, "little")
        for index in range(3, -1, -1):
            load_input_byte(index)
            if index == 3 and clear_sign:
                b.immediate(0x29, 0x7F)
            b.immediate(0xC9, encoded[index])
            b.branch(0x90, "input_ok")
            far_branch(b, 0xD0, overflow, f"{tag}_{index}")
        b.jmp_local("input_ok")

    # Every dependency owns zero-page scratch, so preserve the caller-visible
    # pointers and value before invoking any helper.
    b.immediate(0xA2, pointer_offsets["destination"])
    b.zero_page(0xA5, 0x06)
    b.local_reference(0x9D, "pt")
    b.emit(0xE8)
    b.zero_page(0xA5, 0x07)
    b.local_reference(0x9D, "pt")
    b.immediate(0xA0, 0x00)
    b.label("save")
    b.emit(0xB1, 0x02)
    b.local_reference(0x99, "value")
    b.emit(0xC8)
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "save")

    # Handle NaN and infinities without passing them through finite reduction.
    load_input_byte(3)
    b.immediate(0x29, 0x7F)
    b.immediate(0xC9, 0x7F)
    b.branch(0xD0, "finite")
    load_input_byte(2)
    b.branch(0x10, "finite")
    b.immediate(0x29, 0x7F)
    b.immediate(0xA0, 0x01)
    b.emit(0x11, 0x02)
    b.immediate(0xA0, 0x00)
    b.emit(0x11, 0x02)
    far_branch(b, 0xD0, "return_nan", "exp_nan")
    load_input_byte(3)
    far_branch(b, 0x30, "return_zero", "exp_negative_infinity")
    b.jmp_local("return_inf")

    # These are the same finite cutoffs used by the portable MATH1 source.
    b.label("finite")
    load_input_byte(3)
    b.branch(0x30, "negative")
    compare_magnitude(
        EXP_UPPER_BITS,
        clear_sign=False,
        overflow="return_inf",
        tag="upper",
    )
    b.label("negative")
    compare_magnitude(
        EXP_LOWER_BITS,
        clear_sign=True,
        overflow="return_zero",
        tag="lower",
    )

    b.label("input_ok")
    b.jmp_local("calculate")

    b.label("return_nan")
    load_local_pointer("nan", 0x02)
    b.jmp_local("copy_return")
    b.label("return_inf")
    load_local_pointer("inf", 0x02)
    b.jmp_local("copy_return")
    b.label("return_zero")
    load_local_pointer("zero", 0x02)
    b.label("copy_return")
    load_local_pointer("destination", 0x06)
    b.jmp_local("copy4")

    b.label("copy4")
    b.immediate(0xA0, 0x00)
    b.label("copy_loop")
    b.emit(0xB1, 0x02, 0x91, 0x06, 0xC8)
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "copy_loop")
    b.emit(0x60)

    b.label("calculate")
    load_local_pointer("value", 0x02)
    load_local_pointer("ln2", 0x04)
    load_local_pointer("quotient", 0x06)
    b.jsr("rt_f_div")

    load_local_pointer("quotient", 0x02)
    load_local_pointer("exponent", 0x06)
    b.jsr("rt_f_floor")

    load_local_pointer("exponent", 0x02)
    b.jsr("rt_f_to_i")
    b.local_reference(0x8D, "count")
    b.local_reference(0x8E, "count_hi")

    load_local_pointer("exponent", 0x02)
    load_local_pointer("ln2", 0x04)
    load_local_pointer("product", 0x06)
    b.jsr("rt_f_mul")
    load_local_pointer("value", 0x02)
    load_local_pointer("product", 0x04)
    load_local_pointer("reduced", 0x06)
    b.jsr("rt_f_sub")

    # Horner evaluation exactly matches lib/math1.act, rounding to binary32
    # after every multiplication and addition.
    load_local_pointer(f"c{len(EXP_COEFFICIENT_BITS) - 1}", 0x02)
    load_local_pointer("accum", 0x06)
    b.local_reference(0x20, "copy4")
    for index in range(len(EXP_COEFFICIENT_BITS) - 2, -1, -1):
        load_local_pointer("reduced", 0x02)
        load_local_pointer("accum", 0x04)
        load_local_pointer("work", 0x06)
        b.jsr("rt_f_mul")
        load_local_pointer(f"c{index}", 0x02)
        load_local_pointer("work", 0x04)
        load_local_pointer("accum", 0x06)
        b.jsr("rt_f_add")

    b.local_reference(0xAD, "count_hi")
    b.branch(0x30, "scale_negative")
    b.local_reference(0xAD, "count")
    far_branch(b, 0xF0, "finish", "exp_no_scale")
    b.label("scale_positive")
    load_local_pointer("accum", 0x02)
    load_local_pointer("accum", 0x04)
    load_local_pointer("work", 0x06)
    b.jsr("rt_f_add")
    load_local_pointer("work", 0x02)
    load_local_pointer("accum", 0x06)
    b.local_reference(0x20, "copy4")
    b.local_reference(0xCE, "count")
    b.branch(0xD0, "scale_positive")
    b.jmp_local("finish")

    b.label("scale_negative")
    load_local_pointer("accum", 0x02)
    load_local_pointer("two", 0x04)
    load_local_pointer("work", 0x06)
    b.jsr("rt_f_div")
    load_local_pointer("work", 0x02)
    load_local_pointer("accum", 0x06)
    b.local_reference(0x20, "copy4")
    b.local_reference(0xEE, "count")
    b.branch(0xD0, "scale_negative_check")
    b.local_reference(0xEE, "count_hi")
    b.label("scale_negative_check")
    b.local_reference(0xAD, "count")
    b.local_reference(0x0D, "count_hi")
    b.branch(0xD0, "scale_negative")

    b.label("finish")
    load_local_pointer("accum", 0x02)
    b.jmp_local("copy_return")

    b.label("pt")
    b.emit(0x00, 0x00)
    for target in pointer_targets[1:]:
        offset = len(b.code)
        b.emit(0x00, 0x00)
        b.local_relocations.append((offset, target))
    for label in (
        "value",
        "quotient",
        "exponent",
        "product",
        "reduced",
        "accum",
        "work",
    ):
        for index in range(4):
            b.label(label if index == 0 else f"{label}_{index}")
            b.emit(0x00)
    b.label("count")
    b.emit(0x00)
    b.label("count_hi")
    b.emit(0x00)
    for label, bits in (
        ("ln2", EXP_LN2_BITS),
        ("two", 0x40000000),
        *((f"c{index}", bits) for index, bits in enumerate(EXP_COEFFICIENT_BITS)),
        ("nan", 0x7FC00000),
        ("inf", 0x7F800000),
        ("zero", 0x00000000),
    ):
        b.label(label)
        b.emit(*bits.to_bytes(4, "little"))

    b.export("rt_f_exp")
    return b


def ln_module() -> ObjectBuilder:
    """Build the portable MATH1 binary32 natural logarithm."""
    b = ObjectBuilder("rt_f_ln")

    value_ptr = 0x0E
    reduced_ptr = 0x10
    exponent_ptr = 0x12
    state_count = 0
    state_count_hi = 1
    state_series_index = 2
    state_count_sign = 3
    state_count_magnitude = 4
    state_count_biased = 5

    pointer_targets = (
        "destination",
        "value",
        "reduced",
        "numerator",
        "sum",
        "z",
        "z2",
        "term",
        "result",
        "work",
        "exponent",
        "product",
        "denominator",
        "two",
        "one",
        "ln2",
        "nan",
        "inf",
        "negative_inf",
    )
    pointer_offsets = {
        target: index * 2 for index, target in enumerate(pointer_targets)
    }

    def load_local_pointer(target: str, destination: int) -> None:
        b.immediate(0xA2, pointer_offsets[target])
        b.local_reference(0xBD, "pt")
        b.zero_page(0x85, destination)
        b.emit(0xE8)
        b.local_reference(0xBD, "pt")
        b.zero_page(0x85, destination + 1)

    def load_indirect(pointer: int, index: int) -> None:
        b.immediate(0xA0, index)
        b.emit(0xB1, pointer)

    def or_indirect(pointer: int, index: int) -> None:
        b.immediate(0xA0, index)
        b.emit(0x11, pointer)

    def store_indirect(pointer: int, index: int) -> None:
        b.immediate(0xA0, index)
        b.emit(0x91, pointer)

    def state_load(offset: int) -> None:
        b.immediate(0xA2, offset)
        b.local_reference(0xBD, "state")

    def state_store(offset: int) -> None:
        b.immediate(0xA2, offset)
        b.local_reference(0x9D, "state")

    def state_increment(offset: int) -> None:
        b.immediate(0xA2, offset)
        b.local_reference(0xFE, "state")

    def state_decrement(offset: int) -> None:
        b.immediate(0xA2, offset)
        b.local_reference(0xDE, "state")

    def call_binary(
        symbol: str, left: str, right: str, destination: str
    ) -> None:
        load_local_pointer(left, 0x02)
        load_local_pointer(right, 0x04)
        load_local_pointer(destination, 0x06)
        b.jsr(symbol)

    def copy_local(source: str, destination: str) -> None:
        load_local_pointer(source, 0x02)
        load_local_pointer(destination, 0x06)
        b.local_reference(0x20, "copy4")

    # Preserve the destination and input before any dependency can claim
    # zero-page scratch. The first pointer-table slot is destination storage.
    b.immediate(0xA2, pointer_offsets["destination"])
    b.zero_page(0xA5, 0x06)
    b.local_reference(0x9D, "pt")
    b.emit(0xE8)
    b.zero_page(0xA5, 0x07)
    b.local_reference(0x9D, "pt")
    b.immediate(0xA0, 0x00)
    b.label("save")
    b.emit(0xB1, 0x02)
    b.local_reference(0x99, "value")
    b.emit(0xC8)
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "save")
    load_local_pointer("value", value_ptr)
    load_local_pointer("reduced", reduced_ptr)

    # Negative nonzero values, including negative infinity, are outside the
    # domain. Both zero signs return negative infinity.
    load_indirect(value_ptr, 3)
    b.branch(0x30, "negative")

    # Positive exponent-all-ones values are infinity or NaN.
    b.immediate(0x29, 0x7F)
    b.immediate(0xC9, 0x7F)
    b.branch(0xD0, "finite_positive")
    load_indirect(value_ptr, 2)
    b.branch(0x10, "finite_positive")
    b.immediate(0x29, 0x7F)
    or_indirect(value_ptr, 1)
    or_indirect(value_ptr, 0)
    far_branch(b, 0xD0, "return_nan", "pnan")
    b.jmp_local("return_inf")

    b.label("negative")
    load_indirect(value_ptr, 3)
    b.immediate(0x29, 0x7F)
    or_indirect(value_ptr, 2)
    or_indirect(value_ptr, 1)
    or_indirect(value_ptr, 0)
    far_branch(b, 0xF0, "return_ninf", "nzero")
    b.jmp_local("return_nan")

    b.label("finite_positive")
    load_indirect(value_ptr, 3)
    or_indirect(value_ptr, 2)
    or_indirect(value_ptr, 1)
    or_indirect(value_ptr, 0)
    far_branch(b, 0xF0, "return_ninf", "pzero")
    b.jmp_local("calculate")

    b.label("return_nan")
    load_local_pointer("nan", 0x02)
    b.jmp_local("copy_return")
    b.label("return_inf")
    load_local_pointer("inf", 0x02)
    b.jmp_local("copy_return")
    b.label("return_ninf")
    load_local_pointer("negative_inf", 0x02)
    b.label("copy_return")
    load_local_pointer("destination", 0x06)
    b.jmp_local("copy4")

    b.label("copy4")
    b.immediate(0xA0, 0x00)
    b.label("copy_loop")
    b.emit(0xB1, 0x02, 0x91, 0x06, 0xC8)
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "copy_loop")
    b.emit(0x60)

    b.label("calculate")
    # Extract the unbiased exponent and normalize the significand to [1, 2).
    load_indirect(value_ptr, 2)
    b.emit(0x0A)
    b.emit(0xC8, 0xB1, value_ptr)
    b.emit(0x2A)
    far_branch(b, 0xF0, "subnormal", "sub")

    b.emit(0x38)
    b.immediate(0xE9, 0x7F)
    state_store(state_count)
    b.immediate(0xA9, 0x00)
    b.immediate(0xE9, 0x00)
    state_store(state_count_hi)
    for index in range(2):
        load_indirect(value_ptr, index)
        store_indirect(reduced_ptr, index)
    load_indirect(value_ptr, 2)
    b.immediate(0x29, 0x7F)
    b.immediate(0x09, 0x80)
    store_indirect(reduced_ptr, 2)
    b.immediate(0xA9, 0x3F)
    store_indirect(reduced_ptr, 3)
    b.jmp_local("normalized")

    b.label("subnormal")
    b.immediate(0xA9, 0x82)
    state_store(state_count)
    b.immediate(0xA9, 0xFF)
    state_store(state_count_hi)
    for index in range(2):
        load_indirect(value_ptr, index)
        store_indirect(reduced_ptr, index)
    load_indirect(value_ptr, 2)
    b.immediate(0x29, 0x7F)
    store_indirect(reduced_ptr, 2)
    b.label("norm_sub")
    load_indirect(reduced_ptr, 2)
    b.branch(0x30, "subnormal_ready")
    load_indirect(reduced_ptr, 0)
    b.emit(0x0A, 0x91, reduced_ptr)
    b.emit(0xC8, 0xB1, reduced_ptr, 0x2A, 0x91, reduced_ptr)
    b.emit(0xC8, 0xB1, reduced_ptr, 0x2A, 0x91, reduced_ptr)
    state_decrement(state_count)
    b.immediate(0xA9, 0x00)
    b.branch(0xF0, "norm_sub")
    b.label("subnormal_ready")
    b.immediate(0xA9, 0x3F)
    store_indirect(reduced_ptr, 3)

    # The portable loops choose reduced in [1/sqrt(2), sqrt(2)]. A normalized
    # significand above sqrt(2) is divided by two exactly and increments the
    # integer exponent.
    b.label("normalized")
    sqrt2 = LN_SQRT2_BITS.to_bytes(4, "little")
    for index in range(3, -1, -1):
        load_indirect(reduced_ptr, index)
        b.immediate(0xC9, sqrt2[index])
        b.branch(0x90, "reduced_ready")
        b.branch(0xD0, "reduce_once")
    state_load(state_count_hi)
    b.branch(0x30, "reduce_once")
    b.jmp_local("reduced_ready")
    b.label("reduce_once")
    load_indirect(reduced_ptr, 2)
    b.immediate(0x29, 0x7F)
    store_indirect(reduced_ptr, 2)
    state_increment(state_count)
    b.branch(0xD0, "reduced_ready")
    state_increment(state_count_hi)

    b.label("reduced_ready")
    call_binary("rt_f_sub", "reduced", "one", "numerator")
    call_binary("rt_f_add", "reduced", "one", "sum")
    call_binary("rt_f_div", "numerator", "sum", "z")
    call_binary("rt_f_mul", "z", "z", "z2")
    copy_local("z", "term")
    copy_local("z", "result")

    b.immediate(0xA9, 0x00)
    state_store(state_series_index)
    load_local_pointer("denominator", exponent_ptr)
    for index, value in enumerate((0x00, 0x00, 0x40, 0x40)):
        b.immediate(0xA9, value)
        store_indirect(exponent_ptr, index)
    b.label("series_loop")
    call_binary("rt_f_mul", "term", "z2", "work")
    copy_local("work", "term")
    call_binary("rt_f_div", "term", "denominator", "work")
    call_binary("rt_f_add", "result", "work", "numerator")
    copy_local("numerator", "result")
    state_increment(state_series_index)
    state_load(state_series_index)
    b.immediate(0xC9, len(LN_ODD_DENOMINATOR_BITS))
    b.branch(0xF0, "series_done")
    call_binary("rt_f_add", "denominator", "two", "numerator")
    copy_local("numerator", "denominator")
    b.jmp_local("series_loop")

    b.label("series_done")
    call_binary("rt_f_add", "result", "result", "work")
    b.local_reference(0x20, "count_to_float")
    call_binary("rt_f_mul", "exponent", "ln2", "product")
    call_binary("rt_f_add", "work", "product", "destination")
    b.emit(0x60)

    # Convert the bounded -149..128 exponent to an exact binary32 value.
    b.label("count_to_float")
    load_local_pointer("exponent", exponent_ptr)
    state_load(state_count)
    b.immediate(0xA2, state_count_hi)
    b.local_reference(0x1D, "state")
    b.branch(0xD0, "count_nonzero")
    b.immediate(0xA9, 0x00)
    b.immediate(0xA0, 0x00)
    b.label("zero_exponent")
    b.emit(0x91, exponent_ptr, 0xC8)
    b.immediate(0xC0, 0x04)
    b.branch(0xD0, "zero_exponent")
    b.emit(0x60)

    b.label("count_nonzero")
    state_load(state_count_hi)
    b.branch(0x10, "count_positive")
    b.immediate(0xA9, 0x80)
    state_store(state_count_sign)
    state_load(state_count)
    b.immediate(0x49, 0xFF)
    b.emit(0x18)
    b.immediate(0x69, 0x01)
    b.jmp_local("cnt_mag_ready")
    b.label("count_positive")
    b.immediate(0xA9, 0x00)
    state_store(state_count_sign)
    state_load(state_count)
    b.label("cnt_mag_ready")
    state_store(state_count_magnitude)
    b.immediate(0xA9, 0x86)
    state_store(state_count_biased)
    b.label("count_normalize")
    state_load(state_count_magnitude)
    b.branch(0x30, "cnt_norm")
    b.emit(0x0A)
    state_store(state_count_magnitude)
    state_decrement(state_count_biased)
    b.immediate(0xA9, 0x00)
    b.branch(0xF0, "count_normalize")

    b.label("cnt_norm")
    b.immediate(0xA9, 0x00)
    b.immediate(0xA0, 0x00)
    b.emit(0x91, exponent_ptr, 0xC8, 0x91, exponent_ptr)
    state_load(state_count_magnitude)
    b.immediate(0x29, 0x7F)
    store_indirect(exponent_ptr, 2)
    state_load(state_count_biased)
    b.emit(0x4A)
    store_indirect(exponent_ptr, 3)
    b.branch(0x90, "cnt_low_clear")
    load_indirect(exponent_ptr, 2)
    b.immediate(0x09, 0x80)
    store_indirect(exponent_ptr, 2)
    b.label("cnt_low_clear")
    load_indirect(exponent_ptr, 3)
    b.immediate(0xA2, state_count_sign)
    b.local_reference(0x1D, "state")
    b.emit(0x91, exponent_ptr)
    b.emit(0x60)

    b.label("pt")
    b.emit(0x00, 0x00)
    for target in pointer_targets[1:]:
        offset = len(b.code)
        b.emit(0x00, 0x00)
        b.local_relocations.append((offset, target))

    for label in (
        "value",
        "reduced",
        "numerator",
        "sum",
        "z",
        "z2",
        "term",
        "result",
        "work",
        "exponent",
        "product",
        "denominator",
    ):
        b.label(label)
        b.emit(0x00, 0x00, 0x00, 0x00)

    b.label("state")
    b.emit(0x00, 0x00, 0x00, 0x00, 0x00, 0x00)

    for label, bits in (
        ("two", 0x40000000),
        ("one", 0x3F800000),
        ("ln2", EXP_LN2_BITS),
        ("nan", 0x7FC00000),
        ("inf", 0x7F800000),
        ("negative_inf", 0xFF800000),
    ):
        b.label(label)
        b.emit(*bits.to_bytes(4, "little"))

    b.export("rt_f_ln")
    return b


def logarithm_base_module(module: str, denominator_bits: int) -> ObjectBuilder:
    """Build an alias-safe FLn(value)/constant logarithm wrapper."""
    b = ObjectBuilder(module)

    def load_pointer(prefix: str, zero_page: int) -> None:
        b.local_reference(0xAD, f"{prefix}p")
        b.zero_page(0x85, zero_page)
        b.local_reference(0xAD, f"{prefix}ph")
        b.zero_page(0x85, zero_page + 1)

    # FLn and division may reuse all pointer zero-page cells, so retain the
    # caller's destination in module storage and stage the logarithm privately.
    b.zero_page(0xA5, 0x06)
    b.local_reference(0x8D, "dp")
    b.zero_page(0xA5, 0x07)
    b.local_reference(0x8D, "dph")
    load_pointer("t", 0x06)
    b.jsr("rt_f_ln")
    load_pointer("t", 0x02)
    load_pointer("k", 0x04)
    b.local_reference(0xAD, "dp")
    b.zero_page(0x85, 0x06)
    b.local_reference(0xAD, "dph")
    b.zero_page(0x85, 0x07)
    b.jsr("rt_f_div")
    b.emit(0x60)

    b.label("tp")
    temporary_pointer_offset = len(b.code)
    b.emit(0x00)
    b.label("tph")
    b.emit(0x00)
    b.local_relocations.append((temporary_pointer_offset, "t"))
    b.label("kp")
    constant_pointer_offset = len(b.code)
    b.emit(0x00)
    b.label("kph")
    b.emit(0x00)
    b.local_relocations.append((constant_pointer_offset, "k"))
    b.label("dp")
    b.emit(0x00)
    b.label("dph")
    b.emit(0x00)
    b.label("t")
    b.emit(0x00, 0x00, 0x00, 0x00)
    b.label("k")
    b.emit(*denominator_bits.to_bytes(4, "little"))

    b.export(module)
    return b


def log2_module() -> ObjectBuilder:
    return logarithm_base_module("rt_f_log2", EXP_LN2_BITS)


def log10_module() -> ObjectBuilder:
    return logarithm_base_module("rt_f_log10", LN10_BITS)


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
            abs_module(),
            special_value_module(),
            compare_module(),
            sign_module(),
            trunc_module(),
            floor_module(),
            ceil_module(),
            round_module(),
            frac_module(),
            mod_module(),
            hypot_module(),
            exp_module(),
            ln_module(),
            log2_module(),
            log10_module(),
            deg_to_rad_module(),
            rad_to_deg_module(),
            minmax_module("rt_f_min", maximum=False),
            minmax_module("rt_f_max", maximum=True),
            clamp_module(),
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
