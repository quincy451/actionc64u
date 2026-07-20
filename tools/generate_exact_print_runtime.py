#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from generate_reu_runtime import ObjectBuilder


A = 0x20
EA = 0x2C
SA = 0x30
CA = 0x32
COUNT = 0x34
STICKY = 0x35
TMP = 0x36
TMP2 = 0x37
QBYTE = 0x54
SCALE = 0x55
DIGCOUNT = 0x56
DIGSTART = 0x57
BIGCARRY = 0x58
K = 0x59

ZERO = 0
FINITE = 1
INFINITY = 2
NAN = 3

class Assembler(ObjectBuilder):
    def __init__(self, module: str) -> None:
        super().__init__(module)
        self.serial = 0

    def fresh(self, stem: str) -> str:
        self.serial += 1
        return f"L{self.serial}"

    def lda_i(self, value: int) -> None:
        self.immediate(0xA9, value)

    def ldx_i(self, value: int) -> None:
        self.immediate(0xA2, value)

    def ldy_i(self, value: int) -> None:
        self.immediate(0xA0, value)

    def lda(self, address: int) -> None:
        self.zero_page(0xA5, address)

    def ldx(self, address: int) -> None:
        self.zero_page(0xA6, address)

    def ldy(self, address: int) -> None:
        self.zero_page(0xA4, address)

    def sta(self, address: int) -> None:
        self.zero_page(0x85, address)

    def stx(self, address: int) -> None:
        self.zero_page(0x86, address)

    def sty(self, address: int) -> None:
        self.zero_page(0x84, address)

    def and_i(self, value: int) -> None:
        self.immediate(0x29, value)

    def and_(self, address: int) -> None:
        self.zero_page(0x25, address)

    def ora_i(self, value: int) -> None:
        self.immediate(0x09, value)

    def ora(self, address: int) -> None:
        self.zero_page(0x05, address)

    def eor_i(self, value: int) -> None:
        self.immediate(0x49, value)

    def eor(self, address: int) -> None:
        self.zero_page(0x45, address)

    def adc_i(self, value: int) -> None:
        self.immediate(0x69, value)

    def adc(self, address: int) -> None:
        self.zero_page(0x65, address)

    def sbc_i(self, value: int) -> None:
        self.immediate(0xE9, value)

    def sbc(self, address: int) -> None:
        self.zero_page(0xE5, address)

    def cmp_i(self, value: int) -> None:
        self.immediate(0xC9, value)

    def cmp(self, address: int) -> None:
        self.zero_page(0xC5, address)

    def cpx_i(self, value: int) -> None:
        self.immediate(0xE0, value)

    def inc(self, address: int) -> None:
        self.zero_page(0xE6, address)

    def dec(self, address: int) -> None:
        self.zero_page(0xC6, address)

    def asl(self, address: int) -> None:
        self.zero_page(0x06, address)

    def rol(self, address: int) -> None:
        self.zero_page(0x26, address)

    def lsr(self, address: int) -> None:
        self.zero_page(0x46, address)

    def ror(self, address: int) -> None:
        self.zero_page(0x66, address)

    def branch_far(self, opcode: int, target: str) -> None:
        inverse = {
            0x10: 0x30,  # BPL/BMI
            0x30: 0x10,
            0x50: 0x70,  # BVC/BVS
            0x70: 0x50,
            0x90: 0xB0,  # BCC/BCS
            0xB0: 0x90,
            0xD0: 0xF0,  # BNE/BEQ
            0xF0: 0xD0,
        }[opcode]
        skip = self.fresh("far_skip")
        self.branch(inverse, skip)
        self.jmp_local(target)
        self.label(skip)

    def jsr_local(self, target: str) -> None:
        self.local_reference(0x20, target)
def emit_clear(a: Assembler, destination: int, count: int) -> None:
    a.lda_i(0)
    for index in range(count):
        a.sta(destination + index)
def emit_load_pointer(a: Assembler, pointer: int, destination: int) -> None:
    for index in range(4):
        a.ldy_i(index)
        a.emit(0xB1, pointer)  # LDA (pointer),Y
        a.sta(destination + index)
def emit_decrement16(a: Assembler, address: int) -> None:
    no_borrow = a.fresh("dec16_no_borrow")
    a.lda(address)
    a.branch(0xD0, no_borrow)
    a.dec(address + 1)
    a.label(no_borrow)
    a.dec(address)
def emit_unpack(
    a: Assembler,
    base: int,
    exponent: int,
    sign: int,
    classification: int,
    stem: str,
) -> None:
    normal = a.fresh(f"{stem}_normal")
    subnormal = a.fresh(f"{stem}_subnormal")
    sub_loop = a.fresh(f"{stem}_sub_loop")
    exponent_done = a.fresh(f"{stem}_exponent_done")
    sub_done = a.fresh(f"{stem}_sub_done")
    is_zero = a.fresh(f"{stem}_zero")
    is_special = a.fresh(f"{stem}_special")
    is_inf = a.fresh(f"{stem}_inf")
    done = a.fresh(f"{stem}_done")

    a.lda(base + 3)
    a.and_i(0x80)
    a.sta(sign)
    a.lda(base + 3)
    a.and_i(0x7F)
    a.emit(0x0A)  # ASL A
    a.sta(TMP)
    a.lda(base + 2)
    a.and_i(0x80)
    a.branch(0xF0, exponent_done)
    a.inc(TMP)
    a.label(exponent_done)
    a.lda(TMP)
    a.cmp_i(0xFF)
    a.branch_far(0xF0, is_special)
    a.cmp_i(0)
    a.branch_far(0xF0, subnormal)

    a.label(normal)
    a.lda(TMP)
    a.emit(0x38)  # SEC
    a.sbc_i(127)
    a.sta(exponent)
    a.lda_i(0)
    a.sbc_i(0)
    a.sta(exponent + 1)
    a.lda(base + 2)
    a.and_i(0x7F)
    a.ora_i(0x80)
    a.sta(base + 2)
    a.lda_i(0)
    a.sta(base + 3)
    a.lda_i(FINITE)
    a.sta(classification)
    a.jmp_local(done)

    a.label(subnormal)
    a.lda(base + 2)
    a.and_i(0x7F)
    a.sta(TMP2)
    a.lda(base)
    a.ora(base + 1)
    a.ora(TMP2)
    a.branch_far(0xF0, is_zero)
    a.lda_i(0x82)  # -126
    a.sta(exponent)
    a.lda_i(0xFF)
    a.sta(exponent + 1)
    a.lda(base + 2)
    a.and_i(0x7F)
    a.sta(base + 2)
    a.lda_i(0)
    a.sta(base + 3)
    a.label(sub_loop)
    a.lda(base + 2)
    a.and_i(0x80)
    a.branch(0xD0, sub_done)
    a.emit(0x18)
    a.rol(base)
    a.rol(base + 1)
    a.rol(base + 2)
    emit_decrement16(a, exponent)
    a.jmp_local(sub_loop)
    a.label(sub_done)
    a.lda_i(FINITE)
    a.sta(classification)
    a.jmp_local(done)

    a.label(is_zero)
    emit_clear(a, base, 4)
    a.lda_i(0x82)
    a.sta(exponent)
    a.lda_i(0xFF)
    a.sta(exponent + 1)
    a.lda_i(ZERO)
    a.sta(classification)
    a.jmp_local(done)

    a.label(is_special)
    a.lda(base)
    a.ora(base + 1)
    a.sta(TMP2)
    a.lda(base + 2)
    a.and_i(0x7F)
    a.ora(TMP2)
    a.branch_far(0xF0, is_inf)
    a.lda_i(NAN)
    a.sta(classification)
    a.jmp_local(done)
    a.label(is_inf)
    a.lda_i(INFINITY)
    a.sta(classification)
    a.label(done)
def print_float_module() -> Assembler:
    name = "rt_print_f"
    a = Assembler(name)
    big_bytes = 54
    digit_bytes = 128
    big = a.fresh("big")
    digits = a.fresh("digits")
    state_count = a.fresh("state_count")
    state_start = a.fresh("state_start")
    state_bound = a.fresh("state_bound")
    state_zeros = a.fresh("state_zeros")
    chout = a.fresh("chout")
    print_sign = a.fresh("print_sign")
    print_nan = a.fresh("print_nan")
    print_inf = a.fresh("print_inf")
    print_zero = a.fresh("print_zero")
    finite = a.fresh("finite")
    clear_big = a.fresh("clear_big")
    exponent_negative = a.fresh("exponent_negative")
    scale_ready = a.fresh("scale_ready")
    shift_outer = a.fresh("shift_outer")
    shift_inner = a.fresh("shift_inner")
    multiply_outer = a.fresh("multiply_outer")
    multiply_inner = a.fresh("multiply_inner")
    decimal_outer = a.fresh("decimal_outer")
    decimal_byte = a.fresh("decimal_byte")
    decimal_bit = a.fresh("decimal_bit")
    decimal_no_subtract = a.fresh("decimal_no_subtract")
    trim = a.fresh("trim")
    output_ready = a.fresh("output_ready")
    output_integer = a.fresh("output_integer")
    output_integer_loop = a.fresh("output_integer_loop")
    output_fraction = a.fresh("output_fraction")
    output_fraction_loop = a.fresh("output_fraction_loop")
    output_small = a.fresh("output_small")
    output_zero_loop = a.fresh("output_zero_loop")
    output_all_digits = a.fresh("output_all_digits")
    output_all_loop = a.fresh("output_all_loop")
    done = a.fresh("done")

    def local_abs(opcode: int, label: str) -> None:
        a.local_reference(opcode, label)

    def emit_character(value: int) -> None:
        a.lda_i(value)
        a.jsr_local(chout)

    emit_load_pointer(a, 0x02, A)
    emit_unpack(a, A, EA, SA, CA, "source")
    a.lda(CA)
    a.cmp_i(NAN)
    a.branch_far(0xF0, print_nan)
    a.cmp_i(INFINITY)
    a.branch_far(0xF0, print_inf)
    a.cmp_i(ZERO)
    a.branch_far(0xF0, print_zero)

    a.label(finite)
    a.jsr_local(print_sign)
    a.ldx_i(big_bytes - 1)
    a.lda_i(0)
    a.label(clear_big)
    local_abs(0x9D, big)  # STA big,X
    a.emit(0xCA)  # DEX
    a.branch(0x10, clear_big)  # BPL
    for index in range(3):
        a.ldx_i(index)
        a.lda(A + index)
        local_abs(0x9D, big)

    # value = significand * 2^(EA-23).  For negative powers, multiplying the
    # significand by 5^(-K) gives an integer over the decimal scale 10^(-K).
    a.emit(0x38)
    a.lda(EA)
    a.sbc_i(23)
    a.sta(K)
    a.lda(EA + 1)
    a.sbc_i(0)
    a.sta(K + 1)
    a.lda(K + 1)
    a.branch(0x30, exponent_negative)
    a.lda_i(0)
    a.sta(SCALE)
    a.lda(K)
    a.sta(COUNT)
    a.label(shift_outer)
    a.lda(COUNT)
    a.branch_far(0xF0, scale_ready)
    a.emit(0x18)  # CLC
    a.ldx_i(0)
    a.ldy_i(big_bytes)
    a.label(shift_inner)
    local_abs(0x3E, big)  # ROL big,X
    a.emit(0xE8)  # INX
    a.emit(0x88)  # DEY; unlike CPX, this preserves carry between bytes
    a.branch(0xD0, shift_inner)
    a.dec(COUNT)
    a.jmp_local(shift_outer)

    a.label(exponent_negative)
    a.lda(K)
    a.eor_i(0xFF)
    a.emit(0x18)
    a.adc_i(1)
    a.sta(COUNT)
    a.sta(SCALE)
    a.label(multiply_outer)
    a.lda(COUNT)
    a.branch_far(0xF0, scale_ready)
    a.lda_i(0)
    a.sta(BIGCARRY)
    a.ldx_i(0)
    a.label(multiply_inner)
    local_abs(0xBD, big)  # LDA big,X
    a.sta(QBYTE)
    a.lda_i(0)
    a.sta(TMP2)
    a.lda(QBYTE)
    a.emit(0x0A)  # ASL A
    a.rol(TMP2)
    a.emit(0x0A)
    a.rol(TMP2)
    a.emit(0x18)
    a.adc(QBYTE)
    a.sta(TMP)
    a.lda(TMP2)
    a.adc_i(0)
    a.sta(TMP2)
    a.emit(0x18)
    a.lda(TMP)
    a.adc(BIGCARRY)
    local_abs(0x9D, big)  # STA big,X
    a.lda(TMP2)
    a.adc_i(0)
    a.sta(BIGCARRY)
    a.emit(0xE8)  # INX
    a.cpx_i(big_bytes)
    a.branch(0xD0, multiply_inner)
    a.dec(COUNT)
    a.jmp_local(multiply_outer)

    a.label(scale_ready)
    a.lda_i(0)
    a.sta(DIGCOUNT)
    a.label(decimal_outer)
    a.lda_i(0)
    a.sta(BIGCARRY)  # Decimal division remainder.
    a.sta(STICKY)  # OR of quotient bytes.
    a.ldx_i(big_bytes - 1)
    a.label(decimal_byte)
    local_abs(0xBD, big)  # LDA big,X
    a.sta(QBYTE)
    a.lda_i(0)
    a.sta(TMP)  # Quotient byte.
    a.lda_i(8)
    a.sta(K)
    a.label(decimal_bit)
    a.asl(QBYTE)
    a.rol(BIGCARRY)
    a.asl(TMP)
    a.lda(BIGCARRY)
    a.cmp_i(10)
    a.branch(0x90, decimal_no_subtract)
    a.sbc_i(10)
    a.sta(BIGCARRY)
    a.inc(TMP)
    a.label(decimal_no_subtract)
    a.dec(K)
    a.branch(0xD0, decimal_bit)
    a.lda(TMP)
    local_abs(0x9D, big)  # STA big,X
    a.ora(STICKY)
    a.sta(STICKY)
    a.emit(0xCA)  # DEX
    a.branch(0x10, decimal_byte)
    a.ldx(DIGCOUNT)
    a.lda(BIGCARRY)
    a.emit(0x18)
    a.adc_i(ord("0"))
    local_abs(0x9D, digits)  # STA digits,X
    a.inc(DIGCOUNT)
    a.lda(STICKY)
    a.branch_far(0xD0, decimal_outer)

    # Remove exact trailing decimal zeroes while reducing the decimal scale.
    # This keeps integral values compact and min-subnormal output finite.
    a.lda_i(0)
    a.sta(DIGSTART)
    a.label(trim)
    a.lda(SCALE)
    a.branch(0xF0, output_ready)
    a.ldx(DIGSTART)
    local_abs(0xBD, digits)  # LDA digits,X
    a.cmp_i(ord("0"))
    a.branch(0xD0, output_ready)
    a.inc(DIGSTART)
    a.dec(SCALE)
    a.jmp_local(trim)

    a.label(output_ready)
    a.lda(DIGCOUNT)
    local_abs(0x8D, state_count)
    a.lda(DIGSTART)
    local_abs(0x8D, state_start)
    a.lda(SCALE)
    a.branch_far(0xF0, output_integer)
    # Remaining digit count determines whether any digit precedes the point.
    a.lda(DIGCOUNT)
    a.emit(0x38)
    a.sbc(DIGSTART)
    a.sta(TMP)
    a.cmp(SCALE)
    a.branch_far(0x90, output_small)
    a.branch_far(0xF0, output_small)
    a.lda(DIGSTART)
    a.emit(0x18)
    a.adc(SCALE)
    local_abs(0x8D, state_bound)
    a.ldx(DIGCOUNT)
    a.emit(0xCA)  # DEX
    a.label(output_integer_loop)
    local_abs(0xBD, digits)
    a.jsr_local(chout)
    local_abs(0xEC, state_bound)  # CPX state_bound
    a.branch(0xF0, output_fraction)
    a.emit(0xCA)
    a.jmp_local(output_integer_loop)

    a.label(output_fraction)
    emit_character(ord("."))
    local_abs(0xAE, state_bound)  # LDX state_bound
    a.emit(0xCA)
    a.label(output_fraction_loop)
    local_abs(0xBD, digits)
    a.jsr_local(chout)
    local_abs(0xEC, state_start)
    a.branch_far(0xF0, done)
    a.emit(0xCA)
    a.jmp_local(output_fraction_loop)

    a.label(output_small)
    a.lda(SCALE)
    a.emit(0x38)
    a.sbc(TMP)
    local_abs(0x8D, state_zeros)
    emit_character(ord("0"))
    emit_character(ord("."))
    local_abs(0xAD, state_zeros)
    a.branch(0xF0, output_all_digits)
    a.label(output_zero_loop)
    emit_character(ord("0"))
    local_abs(0xCE, state_zeros)  # DEC state_zeros
    a.branch(0xD0, output_zero_loop)
    a.label(output_all_digits)
    local_abs(0xAE, state_count)  # LDX state_count
    a.emit(0xCA)
    a.label(output_all_loop)
    local_abs(0xBD, digits)
    a.jsr_local(chout)
    local_abs(0xEC, state_start)
    a.branch(0xF0, done)
    a.emit(0xCA)
    a.jmp_local(output_all_loop)

    a.label(output_integer)
    local_abs(0xAE, state_count)  # LDX state_count
    a.emit(0xCA)
    a.label(output_integer + "_loop")
    local_abs(0xBD, digits)
    a.jsr_local(chout)
    local_abs(0xEC, state_start)
    a.branch(0xF0, done)
    a.emit(0xCA)
    a.jmp_local(output_integer + "_loop")

    a.label(print_nan)
    for character in "NAN":
        emit_character(ord(character))
    a.emit(0x60)
    a.label(print_inf)
    a.jsr_local(print_sign)
    for character in "INF":
        emit_character(ord(character))
    a.emit(0x60)
    a.label(print_zero)
    a.jsr_local(print_sign)
    emit_character(ord("0"))
    a.emit(0x60)
    a.label(done)
    a.emit(0x60)

    a.label(print_sign)
    a.lda(SA)
    a.branch(0xF0, print_sign + "_done")
    emit_character(ord("-"))
    a.label(print_sign + "_done")
    a.emit(0x60)

    # CHROUT is allowed to use the C64 zero page.  X is the only live loop
    # register across output, so preserve it on the hardware stack and load
    # the character before entering KERNAL.
    a.label(chout)
    a.sta(QBYTE)
    a.emit(0x8A, 0x48)  # TXA; PHA
    a.lda(QBYTE)
    a.absolute(0x20, 0xFFD2)
    a.emit(0x68, 0xAA, 0x60)  # PLA; TAX; RTS

    a.label(big)
    a.emit(*([0] * big_bytes))
    a.label(digits)
    a.emit(*([0] * digit_bytes))
    for label in (state_count, state_start, state_bound, state_zeros):
        a.label(label)
        a.emit(0)
    a.export(name)
    return a


def render_module(builder: ObjectBuilder) -> str:
    rendered = builder.render()
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the exact-decimal binary32 print OBJ1 module"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "src/runtime/modules/rt_print_f.obj",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    expected = render_module(print_float_module())
    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="ascii") != expected:
            print(f"STALE {args.output}")
            return 1
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(expected, encoding="ascii")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
