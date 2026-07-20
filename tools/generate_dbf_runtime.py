#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from generate_reu_runtime import ObjectBuilder, object_import_code, object_import_index


SERVICE_IMPORTS = {
    0xCF2D: "RT_DBF_FILE_OPEN_WRITE",
    0xCF30: "RT_DBF_FILE_WRITE_BYTE",
    0xCF33: "RT_DBF_FILE_CLOSE",
    0xCF36: "RT_DBF_FILE_LOAD_REU",
    0xCF39: "RT_DBF_RAW_REU_READ",
    0xCF3C: "RT_DBF_RAW_REU_WRITE",
}


@dataclass(frozen=True)
class LegacyExport:
    name: str
    offset: int
    size: int


def migrate_legacy_module(path: Path) -> str:
    exports: list[LegacyExport] = []
    imports: list[str] = []
    code = bytearray()
    old_relocations: list[tuple[int, int]] = []
    lines = path.read_text(encoding="ascii").splitlines()
    if not lines or lines[0].strip().upper() != "OBJ1":
        raise ValueError(f"bad DBF object: {path}")
    for raw in lines[1:]:
        words = raw.split()
        if not words:
            continue
        if words[0] == "x":
            exports.append(
                LegacyExport(words[1].upper(), int(words[2], 0), int(words[3], 0))
            )
        elif words[0] == "u":
            imports.append(words[1].upper())
        elif words[0] == "m":
            code.extend(bytes.fromhex("".join(words[1:])))
        elif words[0] == "r" and words[2].startswith("u"):
            old_relocations.append(
                (int(words[1], 0), object_import_index(words[2][1:]))
            )

    relocations: list[tuple[int, str]] = []
    for offset, index in old_relocations:
        relocations.append((offset, imports[index]))

    for index in range(len(code) - 2):
        if code[index] != 0x20:
            continue
        address = code[index + 1] | (code[index + 2] << 8)
        symbol = SERVICE_IMPORTS.get(address)
        if symbol is None:
            continue
        code[index + 1] = 0
        code[index + 2] = 0
        if symbol not in imports:
            imports.append(symbol)
        relocations.append((index + 1, symbol))

    if not exports or not code:
        raise ValueError(f"incomplete DBF object: {path}")
    for address in SERVICE_IMPORTS:
        needle = bytes((0x20, address & 0xFF, address >> 8))
        if needle in code:
            raise ValueError(
                f"unmigrated service call {chr(36)}{address:04X}: {path}"
            )

    import_indexes = {symbol: index for index, symbol in enumerate(imports)}
    lines_out = ["OBJ1"]
    lines_out.extend(
        f"x {item.name} {item.offset} {item.size}" for item in exports
    )
    lines_out.append(
        "b "
        + "".join(
            f"u{object_import_code(index)}" for index in range(len(imports))
        )
        + "M"
    )
    lines_out.extend(f"u {symbol}" for symbol in imports)
    lines_out.append("m " + code.hex().upper())
    lines_out.extend(
        f"r {offset} u{object_import_code(import_indexes[symbol])}"
        for offset, symbol in sorted(relocations)
    )
    return "\n".join(lines_out) + "\n"


def adapter_state_module() -> ObjectBuilder:
    b = ObjectBuilder("RT_DBF_ADAPTER_STATE")
    b.code = bytearray((0xFF,))
    b.export("RT_DBF_ADAPTER_STATE", 0, 1)
    b.export("RT_DBF_REU_HANDLE", 0, 1)
    return b


def ensure_reu_module() -> ObjectBuilder:
    b = ObjectBuilder("RT_DBF_ENSURE_REU")
    b.require("RT_DBF_ADAPTER_STATE")
    b.reference(0xAD, "RT_DBF_REU_HANDLE")
    b.immediate(0xC9, 0xFF)
    b.branch(0xF0, "allocate")
    b.emit(0x60)
    b.label("allocate")
    b.immediate(0xA9, 0xFF)
    b.immediate(0xA2, 0xFF)
    b.jsr("RT_REU_ALLOC")
    b.reference(0x8D, "RT_DBF_REU_HANDLE")
    b.emit(0x60)
    b.export("RT_DBF_ENSURE_REU")
    return b


def raw_reu_adapter(name: str, write: bool) -> ObjectBuilder:
    b = ObjectBuilder(name)
    b.jsr("RT_DBF_ENSURE_REU")
    b.immediate(0xC9, 0xFF)
    b.branch(0xD0, "have_handle")
    b.immediate(0xA9, 0)
    b.zero_page(0x85, 0xF7)
    b.emit(0x60)
    b.label("have_handle")
    b.zero_page(0x85, 0xD6)
    b.emit(0x38)  # Convert the historical logical $0F4000 base to an offset.
    b.zero_page(0xA5, 0xF0)
    b.immediate(0xE9, 0x00)
    b.zero_page(0x85, 0xD1)
    b.zero_page(0xA5, 0xF1)
    b.immediate(0xE9, 0x40)
    b.zero_page(0x85, 0xD2)
    b.zero_page(0xA5, 0xF2)
    b.immediate(0xE9, 0x0F)
    b.branch(0xF0, "address_ok")
    b.immediate(0xA9, 0)
    b.zero_page(0x85, 0xF7)
    b.emit(0x60)
    b.label("address_ok")
    b.label("loop")
    b.zero_page(0xA5, 0xF5)
    b.zero_page(0x05, 0xF6)
    b.branch(0xF0, "success")
    if write:
        b.immediate(0xA0, 0)
        b.emit(0xB1, 0xF3)  # LDA ($F3),Y
        b.zero_page(0x85, 0x0E)
    b.zero_page(0xA5, 0xD6)
    b.zero_page(0xA6, 0xD1)
    b.zero_page(0xA4, 0xD2)
    b.jsr("RT_REU_POKE8" if write else "RT_REU_PEEK8")
    if write:
        b.immediate(0xC9, 1)
        b.branch(0xF0, "transferred")
        b.immediate(0xA9, 0)
        b.zero_page(0x85, 0xF7)
        b.emit(0x60)
    else:
        b.immediate(0xA0, 0)
        b.emit(0x91, 0xF3)  # STA ($F3),Y
    b.label("transferred")
    b.zero_page(0xE6, 0xD1)
    b.branch(0xD0, "offset_ok")
    b.zero_page(0xE6, 0xD2)
    b.branch(0xD0, "offset_ok")
    b.immediate(0xA9, 0)
    b.zero_page(0x85, 0xF7)
    b.emit(0x60)
    b.label("offset_ok")
    b.zero_page(0xE6, 0xF3)
    b.branch(0xD0, "pointer_ok")
    b.zero_page(0xE6, 0xF4)
    b.label("pointer_ok")
    b.zero_page(0xA5, 0xF5)
    b.branch(0xD0, "decrement_low")
    b.zero_page(0xC6, 0xF6)
    b.label("decrement_low")
    b.zero_page(0xC6, 0xF5)
    b.jmp_local("loop")
    b.label("success")
    b.immediate(0xA9, 0x01)
    b.zero_page(0x85, 0xF7)
    b.emit(0x60)
    b.export(name)
    return b


def file_load_reu_adapter() -> ObjectBuilder:
    b = ObjectBuilder("RT_DBF_FILE_LOAD_REU")
    for target in (0xF5, 0xF6, 0xF7, 0xF8):
        b.immediate(0xA9, 0)
        b.zero_page(0x85, target)
    b.jsr("RT_DBF_ENSURE_REU")
    b.immediate(0xC9, 0xFF)
    b.branch(0xD0, "have_reu")
    b.jmp_local("fail_no_open")
    b.label("have_reu")
    b.zero_page(0x85, 0xD6)

    b.immediate(0xA0, 0)
    b.label("name_scan")
    b.emit(0xB1, 0xF0)  # LDA ($F0),Y
    b.branch(0xF0, "name_ready")
    b.emit(0xC8)  # INY
    b.branch(0xD0, "name_scan")
    b.jmp_local("fail_no_open")
    b.label("name_ready")
    b.emit(0x98)  # TYA
    b.branch(0xD0, "name_nonempty")
    b.jmp_local("fail_no_open")
    b.label("name_nonempty")
    b.zero_page(0xA6, 0xF0)
    b.zero_page(0xA4, 0xF1)
    b.absolute(0x20, 0xFFBD)  # SETNAM
    b.immediate(0xA9, 2)
    b.immediate(0xA2, 8)
    b.immediate(0xA0, 2)
    b.absolute(0x20, 0xFFBA)  # SETLFS
    b.absolute(0x20, 0xFFC0)  # OPEN
    b.branch(0x90, "opened")
    b.jmp_local("fail_no_open")
    b.label("opened")
    b.immediate(0xA2, 2)
    b.absolute(0x20, 0xFFC6)  # CHKIN
    b.branch(0x90, "read_loop")
    b.jmp_local("close_fail")

    b.label("read_loop")
    b.absolute(0x20, 0xFFCF)  # CHRIN
    b.zero_page(0x85, 0x0E)
    b.absolute(0x20, 0xFFB7)  # READST
    b.zero_page(0x85, 0xD0)
    b.zero_page(0xA5, 0xD6)
    b.zero_page(0xA6, 0xF6)
    b.zero_page(0xA4, 0xF7)
    b.jsr("RT_REU_POKE8")
    b.immediate(0xC9, 1)
    b.branch(0xF0, "stored")
    b.jmp_local("close_fail")
    b.label("stored")

    b.zero_page(0xE6, 0xF6)  # INC length low
    b.branch(0xD0, "count_ok")
    b.zero_page(0xE6, 0xF7)
    b.branch(0xD0, "count_ok")
    b.jmp_local("close_fail")
    b.label("count_ok")
    b.zero_page(0xA5, 0xD0)
    b.branch(0xF0, "read_loop")
    b.immediate(0x29, 0x40)
    b.branch(0xD0, "close_success")
    b.jmp_local("close_fail")

    b.label("fail_no_open")
    b.immediate(0xA9, 0)
    b.zero_page(0x85, 0xF5)
    b.emit(0x60)

    b.label("close_fail")
    b.absolute(0x20, 0xFFCC)  # CLRCHN
    b.immediate(0xA9, 2)
    b.absolute(0x20, 0xFFC3)  # CLOSE
    b.immediate(0xA9, 0)
    b.zero_page(0x85, 0xF5)
    b.emit(0x60)

    b.label("close_success")
    b.absolute(0x20, 0xFFCC)
    b.immediate(0xA9, 2)
    b.absolute(0x20, 0xFFC3)
    b.immediate(0xA9, 1)
    b.zero_page(0x85, 0xF5)
    b.emit(0x60)
    b.export("RT_DBF_FILE_LOAD_REU")
    return b


def file_open_write_adapter() -> ObjectBuilder:
    b = ObjectBuilder("RT_DBF_FILE_OPEN_WRITE")
    b.immediate(0xA9, 0)
    b.zero_page(0x85, 0xF2)
    b.immediate(0xA0, 0)
    b.label("scan")
    b.emit(0xB1, 0xF0)
    b.branch(0xF0, "ready")
    b.emit(0xC8)
    b.branch(0xD0, "scan")
    b.emit(0x60)
    b.label("ready")
    b.emit(0x98)
    b.branch(0xD0, "nonempty")
    b.emit(0x60)
    b.label("nonempty")
    b.zero_page(0xA6, 0xF0)
    b.zero_page(0xA4, 0xF1)
    b.absolute(0x20, 0xFFBD)
    b.immediate(0xA9, 3)
    b.immediate(0xA2, 8)
    b.immediate(0xA0, 3)
    b.absolute(0x20, 0xFFBA)
    b.absolute(0x20, 0xFFC0)
    b.branch(0x90, "opened")
    b.emit(0x60)
    b.label("opened")
    b.immediate(0xA2, 3)
    b.absolute(0x20, 0xFFC9)  # CHKOUT
    b.branch(0x90, "success")
    b.immediate(0xA9, 3)
    b.absolute(0x20, 0xFFC3)
    b.emit(0x60)
    b.label("success")
    b.immediate(0xA9, 1)
    b.zero_page(0x85, 0xF2)
    b.emit(0x60)
    b.export("RT_DBF_FILE_OPEN_WRITE")
    return b


def file_write_byte_adapter() -> ObjectBuilder:
    b = ObjectBuilder("RT_DBF_FILE_WRITE_BYTE")
    b.immediate(0xA9, 0)
    b.zero_page(0x85, 0xF4)
    b.label("loop")
    b.zero_page(0xA5, 0xF2)
    b.zero_page(0x05, 0xF3)
    b.branch(0xF0, "success")
    b.immediate(0xA0, 0)
    b.emit(0xB1, 0xF0)
    b.absolute(0x20, 0xFFD2)  # CHROUT to selected output channel
    b.absolute(0x20, 0xFFB7)
    b.branch(0xF0, "written")
    b.emit(0x60)
    b.label("written")
    b.zero_page(0xE6, 0xF0)
    b.branch(0xD0, "pointer_ok")
    b.zero_page(0xE6, 0xF1)
    b.label("pointer_ok")
    b.zero_page(0xA5, 0xF2)
    b.branch(0xD0, "decrement_low")
    b.zero_page(0xC6, 0xF3)
    b.label("decrement_low")
    b.zero_page(0xC6, 0xF2)
    b.branch(0xD0, "loop")
    b.zero_page(0xA5, 0xF3)
    b.branch(0xD0, "loop")
    b.label("success")
    b.immediate(0xA9, 1)
    b.zero_page(0x85, 0xF4)
    b.emit(0x60)
    b.export("RT_DBF_FILE_WRITE_BYTE")
    return b


def file_close_adapter() -> ObjectBuilder:
    b = ObjectBuilder("RT_DBF_FILE_CLOSE")
    b.absolute(0x20, 0xFFCC)
    b.immediate(0xA9, 3)
    b.absolute(0x20, 0xFFC3)
    b.immediate(0xA9, 1)
    b.zero_page(0x85, 0xF0)
    b.emit(0x60)
    b.export("RT_DBF_FILE_CLOSE")
    return b


def generated_modules(root: Path) -> dict[str, str]:
    source_dir = root / "src" / "runtime" / "udos_modules"
    outputs = {
        path.name: migrate_legacy_module(path)
        for path in sorted(source_dir.glob("rt_dbf_*.obj"))
    }
    adapters = {
        "rt_dbf_adapter_state.obj": adapter_state_module(),
        "rt_dbf_ensure_reu.obj": ensure_reu_module(),
        "rt_dbf_raw_reu_read.obj": raw_reu_adapter("RT_DBF_RAW_REU_READ", False),
        "rt_dbf_raw_reu_write.obj": raw_reu_adapter("RT_DBF_RAW_REU_WRITE", True),
        "rt_dbf_file_load_reu.obj": file_load_reu_adapter(),
        "rt_dbf_file_open_write.obj": file_open_write_adapter(),
        "rt_dbf_file_write_byte.obj": file_write_byte_adapter(),
        "rt_dbf_file_close.obj": file_close_adapter(),
    }
    outputs.update({name: builder.render() for name, builder in adapters.items()})
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate DBF objects to standalone REU/KERNAL adapters"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "src" / "runtime" / "modules",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]

    stale: list[Path] = []
    for filename, expected in generated_modules(root).items():
        path = args.output / filename
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
