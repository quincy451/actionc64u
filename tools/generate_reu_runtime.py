#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


def object_import_code(index: int) -> str:
    if 0 <= index < 10:
        return chr(ord("0") + index)
    if index < 36:
        return chr(ord("A") + index - 10)
    raise ValueError("too many object imports")


def object_import_index(code: str) -> int:
    if len(code) != 1:
        raise ValueError(f"bad object import code: {code}")
    if "0" <= code <= "9":
        return ord(code) - ord("0")
    if "A" <= code <= "Z":
        return ord(code) - ord("A") + 10
    if "a" <= code <= "z":
        return ord(code) - ord("a") + 10
    raise ValueError(f"bad object import code: {code}")


@dataclass(frozen=True)
class Export:
    name: str
    offset: int
    size: int


class ObjectBuilder:
    def __init__(self, module: str) -> None:
        self.module = module
        self.code = bytearray()
        self.exports: list[Export] = []
        self.imports: list[str] = []
        self.relocations: list[tuple[int, str]] = []
        self.local_relocations: list[tuple[int, str]] = []
        self.labels: dict[str, int] = {}
        self.branches: list[tuple[int, str]] = []

    def emit(self, *values: int) -> None:
        self.code.extend(value & 0xFF for value in values)

    def immediate(self, opcode: int, value: int) -> None:
        self.emit(opcode, value)

    def zero_page(self, opcode: int, address: int) -> None:
        self.emit(opcode, address)

    def absolute(self, opcode: int, address: int) -> None:
        self.emit(opcode, address & 0xFF, address >> 8)

    def require(self, symbol: str) -> None:
        if symbol not in self.imports:
            self.imports.append(symbol)

    def reference(self, opcode: int, symbol: str) -> None:
        self.emit(opcode)
        offset = len(self.code)
        self.emit(0, 0)
        self.require(symbol)
        self.relocations.append((offset, symbol))

    def jsr(self, symbol: str) -> None:
        self.reference(0x20, symbol)

    def local_reference(self, opcode: int, label: str) -> None:
        self.emit(opcode)
        offset = len(self.code)
        self.emit(0, 0)
        self.local_relocations.append((offset, label))

    def jmp_local(self, label: str) -> None:
        self.local_reference(0x4C, label)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"duplicate label: {name}")
        self.labels[name] = len(self.code)

    def branch(self, opcode: int, label: str) -> None:
        self.emit(opcode)
        operand = len(self.code)
        self.emit(0)
        self.branches.append((operand, label))

    def export(self, name: str, offset: int = 0, size: int | None = None) -> None:
        self.exports.append(Export(name, offset, size or max(1, len(self.code) - offset)))

    def render(self) -> str:
        for operand, label in self.branches:
            if label not in self.labels:
                raise ValueError(f"unknown label: {label}")
            delta = self.labels[label] - (operand + 1)
            if not -128 <= delta <= 127:
                raise ValueError(f"branch out of range: {label}")
            self.code[operand] = delta & 0xFF
        exports = list(self.exports)
        if not exports:
            exports.append(Export(self.module, 0, max(1, len(self.code))))
        local_symbols: dict[str, str] = {}
        for _, label in self.local_relocations:
            if label not in self.labels:
                raise ValueError(f"unknown local relocation label: {label}")
            symbol = f"{self.module}_{label}".upper()
            local_symbols[label] = symbol
            if all(item.name != symbol for item in exports):
                exports.append(Export(symbol, self.labels[label], 1))

        lines = ["OBJ1"]
        lines.extend(f"x {item.name} {item.offset} {item.size}" for item in exports)
        body = "".join(
            f"u{object_import_code(index)}" for index in range(len(self.imports))
        ) + "M"
        lines.append(f"b {body}")
        lines.extend(f"u {symbol}" for symbol in self.imports)
        lines.append("m " + self.code.hex().upper())
        import_indexes = {name: index for index, name in enumerate(self.imports)}
        lines.extend(
            f"r {offset} u{object_import_code(import_indexes[symbol])}"
            for offset, symbol in self.relocations
        )
        lines.extend(
            f"r {offset} x {local_symbols[label]}"
            for offset, label in self.local_relocations
        )
        return "\n".join(lines) + "\n"


def state_module() -> ObjectBuilder:
    builder = ObjectBuilder("RT_REU_STATE")
    builder.code = bytearray(1539)
    builder.export("RT_REU_STATE", 0, len(builder.code))
    builder.export("RT_REU_IN_USE", 0, 256)
    builder.export("RT_REU_BASE_LO", 256, 256)
    builder.export("RT_REU_BASE_HI", 512, 256)
    builder.export("RT_REU_BASE_BANK", 768, 256)
    builder.export("RT_REU_SIZE_LO", 1024, 256)
    builder.export("RT_REU_SIZE_HI", 1280, 256)
    builder.export("RT_REU_NEXT_LO", 1536, 1)
    builder.export("RT_REU_NEXT_HI", 1537, 1)
    builder.export("RT_REU_NEXT_BANK", 1538, 1)
    return builder


def alloc_module() -> ObjectBuilder:
    b = ObjectBuilder("RT_REU_ALLOC")
    b.require("RT_REU_STATE")
    b.zero_page(0x85, 0x02)  # STA size low
    b.zero_page(0x86, 0x03)  # STX size high
    b.emit(0x8A)  # TXA
    b.zero_page(0x05, 0x02)  # ORA size low
    b.branch(0xD0, "size_ok")
    b.immediate(0xA9, 0xFF)
    b.emit(0x60)
    b.label("size_ok")

    b.zero_page(0xA5, 0x01)  # LDA C64 memory port
    b.zero_page(0x85, 0x04)
    b.immediate(0x29, 0xF8)
    b.immediate(0x09, 0x05)
    b.zero_page(0x85, 0x01)
    b.immediate(0xA9, 0x55)
    b.absolute(0x8D, 0xDF04)
    b.absolute(0xCD, 0xDF04)
    b.branch(0xD0, "no_reu")
    b.immediate(0xA9, 0xAA)
    b.absolute(0x8D, 0xDF04)
    b.absolute(0xCD, 0xDF04)
    b.branch(0xD0, "no_reu")
    b.zero_page(0xA5, 0x04)
    b.zero_page(0x85, 0x01)

    b.immediate(0xA2, 0x00)
    b.label("scan")
    b.reference(0xBD, "RT_REU_IN_USE")  # LDA abs,X
    b.branch(0xF0, "found")
    b.emit(0xE8)  # INX
    b.immediate(0xE0, 0xFF)  # CPX #$FF; $FF is the failure handle
    b.branch(0xD0, "scan")
    b.immediate(0xA9, 0xFF)
    b.emit(0x60)

    b.label("no_reu")
    b.zero_page(0xA5, 0x04)
    b.zero_page(0x85, 0x01)
    b.immediate(0xA9, 0xFF)
    b.emit(0x60)

    b.label("found")
    b.emit(0x18)  # CLC
    b.reference(0xAD, "RT_REU_NEXT_LO")
    b.zero_page(0x65, 0x02)  # ADC size low
    b.zero_page(0x85, 0x05)
    b.reference(0xAD, "RT_REU_NEXT_HI")
    b.zero_page(0x65, 0x03)
    b.zero_page(0x85, 0x06)
    b.reference(0xAD, "RT_REU_NEXT_BANK")
    b.immediate(0x69, 0x00)
    b.zero_page(0x85, 0x07)
    b.branch(0x90, "capacity_ok")
    b.immediate(0xA9, 0xFF)
    b.emit(0x60)

    b.label("capacity_ok")
    b.reference(0xAD, "RT_REU_NEXT_LO")
    b.reference(0x9D, "RT_REU_BASE_LO")
    b.reference(0xAD, "RT_REU_NEXT_HI")
    b.reference(0x9D, "RT_REU_BASE_HI")
    b.reference(0xAD, "RT_REU_NEXT_BANK")
    b.reference(0x9D, "RT_REU_BASE_BANK")
    b.zero_page(0xA5, 0x02)
    b.reference(0x9D, "RT_REU_SIZE_LO")
    b.zero_page(0xA5, 0x03)
    b.reference(0x9D, "RT_REU_SIZE_HI")
    b.immediate(0xA9, 0x01)
    b.reference(0x9D, "RT_REU_IN_USE")
    b.zero_page(0xA5, 0x05)
    b.reference(0x8D, "RT_REU_NEXT_LO")
    b.zero_page(0xA5, 0x06)
    b.reference(0x8D, "RT_REU_NEXT_HI")
    b.zero_page(0xA5, 0x07)
    b.reference(0x8D, "RT_REU_NEXT_BANK")
    b.emit(0x8A, 0x60)  # TXA; RTS
    b.export("RT_REU_ALLOC")
    return b


def resolve_module() -> ObjectBuilder:
    b = ObjectBuilder("RT_REU_RESOLVE")
    b.require("RT_REU_STATE")
    b.immediate(0xC9, 0xFF)
    b.branch(0xD0, "handle_ok")
    b.emit(0x18, 0x60)  # CLC; RTS
    b.label("handle_ok")
    b.zero_page(0x85, 0x07)
    b.zero_page(0x86, 0x08)
    b.zero_page(0x84, 0x09)
    b.emit(0xAA)  # TAX
    b.reference(0xBD, "RT_REU_IN_USE")
    b.branch(0xD0, "allocated")
    b.emit(0x18, 0x60)
    b.label("allocated")

    b.emit(0x18)
    b.zero_page(0xA5, 0x08)
    b.zero_page(0x65, 0x0A)
    b.zero_page(0x85, 0x0C)
    b.zero_page(0xA5, 0x09)
    b.zero_page(0x65, 0x0B)
    b.zero_page(0x85, 0x0D)
    b.branch(0x90, "end_ok")
    b.emit(0x18, 0x60)
    b.label("end_ok")

    b.zero_page(0xA5, 0x0D)
    b.reference(0xDD, "RT_REU_SIZE_HI")  # CMP abs,X
    b.branch(0x90, "bounds_ok")
    b.branch(0xF0, "compare_low")
    b.emit(0x18, 0x60)
    b.label("compare_low")
    b.zero_page(0xA5, 0x0C)
    b.reference(0xDD, "RT_REU_SIZE_LO")
    b.branch(0x90, "bounds_ok")
    b.branch(0xF0, "bounds_ok")
    b.emit(0x18, 0x60)

    b.label("bounds_ok")
    b.emit(0x18)
    b.reference(0xBD, "RT_REU_BASE_LO")
    b.zero_page(0x65, 0x08)
    b.zero_page(0x85, 0x04)
    b.reference(0xBD, "RT_REU_BASE_HI")
    b.zero_page(0x65, 0x09)
    b.zero_page(0x85, 0x05)
    b.reference(0xBD, "RT_REU_BASE_BANK")
    b.immediate(0x69, 0x00)
    b.zero_page(0x85, 0x06)
    b.emit(0x38, 0x60)  # SEC; RTS
    b.export("RT_REU_RESOLVE")
    return b


def transfer_module() -> ObjectBuilder:
    b = ObjectBuilder("RT_REU_TRANSFER")
    b.zero_page(0x85, 0x10)  # command
    b.zero_page(0xA5, 0x01)
    b.zero_page(0x85, 0x11)  # saved memory port
    b.immediate(0x29, 0xF8)
    b.immediate(0x09, 0x05)
    b.zero_page(0x85, 0x01)
    for source, target in (
        (0x02, 0xDF02),
        (0x03, 0xDF03),
        (0x04, 0xDF04),
        (0x05, 0xDF05),
        (0x06, 0xDF06),
        (0x0A, 0xDF07),
        (0x0B, 0xDF08),
    ):
        b.zero_page(0xA5, source)
        b.absolute(0x8D, target)
    b.immediate(0xA9, 0x00)
    b.absolute(0x8D, 0xDF09)
    b.absolute(0x8D, 0xDF0A)
    b.zero_page(0xA5, 0x10)
    b.absolute(0x8D, 0xDF01)
    b.zero_page(0xA5, 0x11)
    b.immediate(0x29, 0xF8)
    b.zero_page(0x85, 0x01)
    b.absolute(0xAD, 0xFF00)
    b.absolute(0x8D, 0xFF00)
    b.zero_page(0xA5, 0x11)
    b.zero_page(0x85, 0x01)
    b.absolute(0xAD, 0xDF00)
    b.emit(0x60)
    b.export("RT_REU_TRANSFER")
    return b


def access_module(name: str, count: int, command: int, write: bool) -> ObjectBuilder:
    b = ObjectBuilder(name)
    b.emit(0x48)  # PHA handle while setting the count
    b.immediate(0xA9, count)
    b.zero_page(0x85, 0x0A)
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, 0x0B)
    b.emit(0x68)  # PLA handle
    b.jsr("RT_REU_RESOLVE")
    b.branch(0xB0, "resolved")
    if write:
        b.immediate(0xA9, 0x00)
        b.emit(0x60)
    elif count == 1:
        b.immediate(0xA9, 0x00)
        b.emit(0x60)
    else:
        b.immediate(0xA9, 0x00)
        b.immediate(0xA2, 0x00)
        b.emit(0x60)
    b.label("resolved")
    b.immediate(0xA9, 0x0E)
    b.zero_page(0x85, 0x02)
    b.immediate(0xA9, 0x00)
    b.zero_page(0x85, 0x03)
    b.immediate(0xA9, command)
    b.jsr("RT_REU_TRANSFER")
    if write:
        b.immediate(0xA9, 0x01)
    elif count == 1:
        b.zero_page(0xA5, 0x0E)
    else:
        b.zero_page(0xA6, 0x0F)
        b.zero_page(0xA5, 0x0E)
    b.emit(0x60)
    b.export(name)
    return b


def modules() -> dict[str, ObjectBuilder]:
    return {
        "rt_reu_state.obj": state_module(),
        "rt_reu_alloc.obj": alloc_module(),
        "rt_reu_resolve.obj": resolve_module(),
        "rt_reu_transfer.obj": transfer_module(),
        "rt_reu_peek8.obj": access_module("RT_REU_PEEK8", 1, 0xED, False),
        "rt_reu_peek16.obj": access_module("RT_REU_PEEK16", 2, 0xED, False),
        "rt_reu_poke8.obj": access_module("RT_REU_POKE8", 1, 0xEC, True),
        "rt_reu_poke16.obj": access_module("RT_REU_POKE16", 2, 0xEC, True),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate standalone REU OBJ1 modules")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "src" / "runtime" / "modules",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    stale: list[Path] = []
    for filename, builder in modules().items():
        path = args.output / filename
        expected = builder.render()
        if args.check:
            if not path.is_file() or path.read_text(encoding="ascii") != expected:
                stale.append(path)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected, encoding="ascii")
    if stale:
        for path in stale:
            print(f"STALE {path}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
