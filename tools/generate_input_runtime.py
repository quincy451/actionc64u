#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from generate_reu_runtime import ObjectBuilder


PORT = 0x02
STATE_BASE = 0x03
POT_X = 0x04
POT_Y = 0x05
BUTTONS = 0x06
ACTIVITY = 0x07
DELTA = 0x08

CIA1_PORT_A = 0xDC00
CIA1_PORT_B = 0xDC01
CIA1_DDRA = 0xDC02
SID_POTX = 0xD419
SID_POTY = 0xD41A


def render_module(builder: ObjectBuilder) -> str:
    lines: list[str] = []
    for line in builder.render().splitlines():
        if not line.startswith("m "):
            lines.append(line)
            continue
        code = bytes.fromhex(line[2:])
        for offset in range(0, len(code), 64):
            chunk = code[offset : offset + 64]
            lines.append("m " + " ".join(f"{value:02X}" for value in chunk))
    lines.append(f"n {builder.module}")
    return "\n".join(lines) + "\n"


def state_index(builder: ObjectBuilder, field: int) -> None:
    builder.zero_page(0xA6, STATE_BASE)  # LDX current per-port state base
    for _ in range(field):
        builder.emit(0xE8)  # INX


def state_load(builder: ObjectBuilder, field: int) -> None:
    state_index(builder, field)
    builder.reference(0xBD, "rt_ms")  # LDA rt_ms,X


def state_store(builder: ObjectBuilder, field: int) -> None:
    state_index(builder, field)
    builder.reference(0x9D, "rt_ms")  # STA rt_ms,X


def state_sbc(builder: ObjectBuilder, field: int) -> None:
    state_index(builder, field)
    builder.reference(0xFD, "rt_ms")  # SBC rt_ms,X


def state_adc(builder: ObjectBuilder, field: int) -> None:
    state_index(builder, field)
    builder.reference(0x7D, "rt_ms")  # ADC rt_ms,X


def emit_muxed_pot_read(builder: ObjectBuilder, read_y: bool) -> None:
    # The SID needs the requested control port selected long enough to finish a
    # conversion. Preserve the keyboard scanner's CIA state around the sample.
    builder.emit(0x08, 0x78)  # PHP; SEI
    builder.absolute(0xAD, CIA1_DDRA)
    builder.emit(0x48)  # PHA
    builder.immediate(0x09, 0xC0)
    builder.absolute(0x8D, CIA1_DDRA)
    builder.absolute(0xAD, CIA1_PORT_A)
    builder.emit(0x48)  # PHA
    builder.immediate(0x29, 0x3F)
    builder.zero_page(0x05, POT_X)  # ORA selected PA6/PA7 mask
    builder.absolute(0x8D, CIA1_PORT_A)

    # Two 256-iteration loops exceed the 1351's documented 1.6 ms settling
    # interval on a 1 MHz C64.
    builder.immediate(0xA0, 0x02)
    builder.label("mux_delay_outer")
    builder.immediate(0xA2, 0x00)
    builder.label("mux_delay_inner")
    builder.emit(0xCA)  # DEX
    builder.branch(0xD0, "mux_delay_inner")
    builder.emit(0x88)  # DEY
    builder.branch(0xD0, "mux_delay_outer")

    builder.absolute(0xAD, SID_POTX)
    builder.zero_page(0x85, POT_X)
    if read_y:
        builder.absolute(0xAD, SID_POTY)
        builder.zero_page(0x85, POT_Y)

    builder.emit(0x68)
    builder.absolute(0x8D, CIA1_PORT_A)
    builder.emit(0x68)
    builder.absolute(0x8D, CIA1_DDRA)
    builder.emit(0x28)  # PLP


def joystick_module() -> ObjectBuilder:
    b = ObjectBuilder("rt_joy")
    b.zero_page(0x85, PORT)
    b.immediate(0xC9, 0x01)
    b.branch(0xD0, "port2")
    b.absolute(0xAD, CIA1_PORT_B)
    b.zero_page(0x85, BUTTONS)
    b.immediate(0xA9, 0x40)  # PA6 selects control port 1 POT lines
    b.branch(0xD0, "port_ready")
    b.label("port2")
    b.absolute(0xAD, CIA1_PORT_A)
    b.zero_page(0x85, BUTTONS)
    b.immediate(0xA9, 0x80)  # PA7 selects control port 2 POT lines
    b.label("port_ready")
    b.zero_page(0x85, POT_X)

    b.zero_page(0xA5, BUTTONS)
    b.immediate(0x49, 0xFF)
    b.immediate(0x29, 0x1F)
    b.zero_page(0x85, BUTTONS)

    emit_muxed_pot_read(b, False)
    b.zero_page(0xA5, POT_X)
    b.immediate(0xC9, 0x80)
    b.branch(0xB0, "return_state")
    b.zero_page(0xA5, BUTTONS)
    b.immediate(0x09, 0x20)
    b.zero_page(0x85, BUTTONS)
    b.label("return_state")
    b.zero_page(0xA5, BUTTONS)
    b.emit(0x60)
    b.export("rt_joy")
    return b


def joystick_state_module() -> ObjectBuilder:
    b = ObjectBuilder("rt_js")
    b.code = bytearray(2)
    b.export("rt_js", 0, 2)
    return b


def joystick_presence_module() -> ObjectBuilder:
    b = ObjectBuilder("rt_jp")
    b.zero_page(0x85, PORT)
    b.jsr("rt_joy")
    b.zero_page(0xA6, PORT)
    b.emit(0xCA)  # DEX: port 1/2 becomes state index 0/1
    b.immediate(0xC9, 0x00)
    b.branch(0xF0, "return_seen")
    b.immediate(0xA9, 0x01)
    b.reference(0x9D, "rt_js")
    b.label("return_seen")
    b.reference(0xBD, "rt_js")
    b.emit(0x60)
    b.export("rt_jp")
    return b


def normalized_mask_module(module: str, source: str, mask: int) -> ObjectBuilder:
    b = ObjectBuilder(module)
    b.jsr(source)
    b.immediate(0x29, mask)
    b.branch(0xF0, "not_set")
    b.immediate(0xA9, 0x01)
    b.emit(0x60)
    b.label("not_set")
    b.immediate(0xA9, 0x00)
    b.emit(0x60)
    b.export(module)
    return b


def mouse_state_module() -> ObjectBuilder:
    b = ObjectBuilder("rt_ms")
    # Byte 0 selects the current seven-byte per-port record. Default to port 1.
    b.code = bytearray([1] + [0] * 14)
    b.export("rt_ms", 0, len(b.code))
    return b


def mouse_poll_module() -> ObjectBuilder:
    b = ObjectBuilder("rt_mp")
    b.zero_page(0x85, PORT)
    b.immediate(0xC9, 0x01)
    b.branch(0xD0, "port2")
    b.absolute(0xAD, CIA1_PORT_B)
    b.zero_page(0x85, ACTIVITY)  # raw digital lines
    b.immediate(0xA9, 0x01)
    b.zero_page(0x85, STATE_BASE)
    b.immediate(0xA9, 0x40)
    b.branch(0xD0, "port_ready")
    b.label("port2")
    b.absolute(0xAD, CIA1_PORT_A)
    b.zero_page(0x85, ACTIVITY)
    b.immediate(0xA9, 0x08)
    b.zero_page(0x85, STATE_BASE)
    b.immediate(0xA9, 0x80)
    b.label("port_ready")
    b.zero_page(0x85, POT_X)  # mux mask until the sample overwrites it

    # In 1351 proportional mode left is FIRE and right is UP.
    b.zero_page(0xA5, ACTIVITY)
    b.immediate(0x49, 0xFF)
    b.zero_page(0x85, ACTIVITY)
    b.immediate(0x29, 0x10)
    for _ in range(4):
        b.emit(0x4A)  # LSR A
    b.zero_page(0x85, BUTTONS)
    b.zero_page(0xA5, ACTIVITY)
    b.immediate(0x29, 0x01)
    b.emit(0x0A)  # ASL A
    b.zero_page(0x05, BUTTONS)
    b.zero_page(0x85, BUTTONS)

    emit_muxed_pot_read(b, True)

    # Ignore the noise bit and don't-care high bit; retain position modulo 64.
    b.zero_page(0xA5, POT_X)
    b.emit(0x4A)
    b.immediate(0x29, 0x3F)
    b.zero_page(0x85, POT_X)
    b.zero_page(0xA5, POT_Y)
    b.emit(0x4A)
    b.immediate(0x29, 0x3F)
    b.zero_page(0x85, POT_Y)

    b.immediate(0xA2, 0x00)
    b.zero_page(0xA5, STATE_BASE)
    b.reference(0x9D, "rt_ms")

    state_load(b, 0)
    b.branch(0xD0, "update")
    b.immediate(0xA9, 0x01)
    state_store(b, 0)
    b.zero_page(0xA5, POT_X)
    state_store(b, 1)
    b.zero_page(0xA5, POT_Y)
    state_store(b, 2)
    b.zero_page(0xA5, BUTTONS)
    state_store(b, 5)
    b.zero_page(0xA5, BUTTONS)
    b.branch(0xF0, "initial_return")
    b.immediate(0xA9, 0x01)
    state_store(b, 6)
    b.label("initial_return")
    state_load(b, 6)
    b.emit(0x60)

    b.label("update")
    b.zero_page(0xA5, BUTTONS)
    b.zero_page(0x85, ACTIVITY)

    b.zero_page(0xA5, POT_X)
    b.emit(0x38)  # SEC
    state_sbc(b, 1)
    b.immediate(0x29, 0x3F)
    b.branch(0xF0, "store_prev_x")
    b.zero_page(0x85, DELTA)
    b.immediate(0xA9, 0x01)
    b.zero_page(0x85, ACTIVITY)
    b.zero_page(0xA5, DELTA)
    b.immediate(0xC9, 0x20)
    b.branch(0x90, "add_x")
    b.immediate(0x09, 0xC0)  # sign-extend the six-bit wrapped delta
    b.label("add_x")
    b.emit(0x18)  # CLC
    state_adc(b, 3)
    state_store(b, 3)
    b.label("store_prev_x")
    b.zero_page(0xA5, POT_X)
    state_store(b, 1)

    b.zero_page(0xA5, POT_Y)
    b.emit(0x38)
    state_sbc(b, 2)
    b.immediate(0x29, 0x3F)
    b.branch(0xF0, "store_prev_y")
    b.zero_page(0x85, DELTA)
    b.immediate(0xA9, 0x01)
    b.zero_page(0x85, ACTIVITY)
    b.zero_page(0xA5, DELTA)
    b.immediate(0xC9, 0x20)
    b.branch(0x90, "add_y")
    b.immediate(0x09, 0xC0)
    b.label("add_y")
    b.immediate(0x49, 0xFF)
    b.emit(0x18)  # CLC
    b.immediate(0x69, 0x01)  # invert POT Y movement for screen-down coordinates
    b.emit(0x18)
    state_adc(b, 4)
    state_store(b, 4)
    b.label("store_prev_y")
    b.zero_page(0xA5, POT_Y)
    state_store(b, 2)

    b.zero_page(0xA5, BUTTONS)
    state_store(b, 5)
    b.zero_page(0xA5, ACTIVITY)
    b.branch(0xF0, "return_seen")
    b.label("mark_seen")
    b.immediate(0xA9, 0x01)
    state_store(b, 6)
    b.label("return_seen")
    state_load(b, 6)
    b.emit(0x60)
    b.export("rt_mp")
    return b


def mouse_getter_module(module: str, field: int) -> ObjectBuilder:
    b = ObjectBuilder(module)
    b.immediate(0xA2, 0x00)
    b.reference(0xBD, "rt_ms")
    b.emit(0xAA)  # TAX current per-port state base
    for _ in range(field):
        b.emit(0xE8)
    b.reference(0xBD, "rt_ms")
    b.emit(0x60)
    b.export(module)
    return b


def modules() -> dict[str, ObjectBuilder]:
    builders = (
        joystick_module(),
        joystick_state_module(),
        joystick_presence_module(),
        normalized_mask_module("rt_jb1", "rt_joy", 0x10),
        normalized_mask_module("rt_jb2", "rt_joy", 0x20),
        mouse_state_module(),
        mouse_poll_module(),
        mouse_getter_module("rt_mseen", 6),
        mouse_getter_module("rt_mx", 3),
        mouse_getter_module("rt_my", 4),
        mouse_getter_module("rt_mb", 5),
        normalized_mask_module("rt_mb1", "rt_mb", 0x01),
        normalized_mask_module("rt_mb2", "rt_mb", 0x02),
    )
    return {f"{builder.module}.obj": builder for builder in builders}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate C64 input OBJ1 modules")
    parser.add_argument("--output", type=Path, action="append")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    runtime_root = Path(__file__).resolve().parents[1] / "src" / "runtime"
    outputs = args.output or [runtime_root / "modules", runtime_root / "udos_modules"]
    expected = {name: render_module(builder) for name, builder in modules().items()}
    stale: list[Path] = []
    for output in outputs:
        for name, text in expected.items():
            path = output / name
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
