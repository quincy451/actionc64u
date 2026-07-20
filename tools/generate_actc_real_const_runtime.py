#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import re


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "src" / "runtime" / "modules"
ROOT_SYMBOLS = (
    "rt_f_add",
    "rt_f_sub",
    "rt_f_mul",
    "rt_f_div",
    "rt_f_abs",
    "rt_f_sqrt",
)
SYMBOL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class Relocation:
    offset: int
    symbol: str


@dataclass(frozen=True)
class Module:
    path: Path
    exports: tuple[tuple[str, int], ...]
    imports: tuple[str, ...]
    payload: bytes
    relocations: tuple[Relocation, ...]


def parse_module(path: Path) -> Module:
    lines = path.read_text(encoding="ascii").splitlines()
    if not lines or lines[0].strip().upper() != "OBJ1":
        raise ValueError(f"{path}: bad OBJ1 magic")

    exports: list[tuple[str, int]] = []
    imports: list[str] = []
    payload = bytearray()
    raw_relocations: list[tuple[int, str]] = []
    for line in lines[1:]:
        fields = line.split()
        if not fields:
            continue
        record = fields[0].lower()
        if record == "x":
            if len(fields) < 3 or not SYMBOL_RE.fullmatch(fields[1]):
                raise ValueError(f"{path}: malformed export: {line}")
            exports.append((fields[1], int(fields[2], 10)))
        elif record == "u":
            if len(fields) != 2 or not SYMBOL_RE.fullmatch(fields[1]):
                raise ValueError(f"{path}: malformed import: {line}")
            imports.append(fields[1])
        elif record == "m":
            try:
                payload.extend(bytes.fromhex("".join(fields[1:])))
            except ValueError as exc:
                raise ValueError(f"{path}: malformed machine data: {line}") from exc
        elif record == "r":
            if len(fields) == 3 and fields[2].lower().startswith("u"):
                index = int(fields[2][1:], 36)
                if index >= len(imports):
                    raise ValueError(f"{path}: relocation import out of range: {line}")
                raw_relocations.append((int(fields[1], 10), imports[index]))
            elif len(fields) >= 4 and fields[2].lower() == "x":
                raw_relocations.append((int(fields[1], 10), fields[3]))
            else:
                raise ValueError(f"{path}: unsupported relocation: {line}")

    for name, offset in exports:
        if offset < 0 or offset > len(payload):
            raise ValueError(f"{path}: export {name} is outside its payload")
    relocations = tuple(Relocation(offset, symbol) for offset, symbol in raw_relocations)
    occupied: set[int] = set()
    for relocation in relocations:
        if relocation.offset < 0 or relocation.offset + 1 >= len(payload):
            raise ValueError(f"{path}: relocation is outside its payload")
        if relocation.offset in occupied or relocation.offset + 1 in occupied:
            raise ValueError(f"{path}: overlapping relocations")
        occupied.update((relocation.offset, relocation.offset + 1))

    return Module(
        path=path,
        exports=tuple(exports),
        imports=tuple(imports),
        payload=bytes(payload),
        relocations=relocations,
    )


def load_closure() -> list[Module]:
    by_primary: dict[str, Module] = {}
    by_export: dict[str, Module] = {}
    for path in sorted(MODULE_DIR.glob("rt_f_*.obj")):
        module = parse_module(path)
        if not module.exports:
            continue
        by_primary[module.exports[0][0].lower()] = module
        for symbol, _ in module.exports:
            previous = by_export.setdefault(symbol.lower(), module)
            if previous is not module:
                raise ValueError(f"duplicate runtime export: {symbol}")

    ordered: list[Module] = []
    visiting: set[Path] = set()
    visited: set[Path] = set()

    def visit_symbol(symbol: str) -> None:
        module = by_export.get(symbol.lower()) or by_primary.get(symbol.lower())
        if module is None:
            raise ValueError(f"missing REAL runtime dependency: {symbol}")
        if module.path in visited:
            return
        if module.path in visiting:
            raise ValueError(f"cyclic REAL runtime dependency at {module.path.name}")
        visiting.add(module.path)
        for imported in module.imports:
            visit_symbol(imported)
        visiting.remove(module.path)
        visited.add(module.path)
        ordered.append(module)

    for symbol in ROOT_SYMBOLS:
        visit_symbol(symbol)
    return ordered


def asm_symbol(symbol: str) -> str:
    if not SYMBOL_RE.fullmatch(symbol):
        raise ValueError(f"unsupported runtime symbol: {symbol}")
    return "actc_const_" + symbol.lower()


def byte_lines(data: bytes) -> list[str]:
    return [
        "    .byte " + ",".join(f"${value:02X}" for value in data[index : index + 16])
        for index in range(0, len(data), 16)
    ]


def render(modules: list[Module]) -> str:
    all_exports = {
        symbol.lower(): (module, offset)
        for module in modules
        for symbol, offset in module.exports
    }
    lines = [
        "; Generated by tools/generate_actc_real_const_runtime.py.",
        "; This is the compile-time evaluator's private copy of shared runtime code.",
        "",
    ]
    for module in modules:
        primary = module.exports[0][0]
        base = asm_symbol(primary) + "_module"
        labels: dict[int, list[str]] = {}
        for symbol, offset in module.exports:
            labels.setdefault(offset, []).append(asm_symbol(symbol))
        relocations = {item.offset: item for item in module.relocations}

        lines.append(f"{base}:")
        position = 0
        pending = bytearray()

        def flush() -> None:
            nonlocal pending
            if pending:
                lines.extend(byte_lines(bytes(pending)))
                pending = bytearray()

        while position < len(module.payload):
            if position in labels:
                flush()
                for label in labels[position]:
                    lines.append(f"{label}:")
            relocation = relocations.get(position)
            if relocation is not None:
                flush()
                if relocation.symbol.lower() not in all_exports:
                    raise ValueError(
                        f"{module.path}: unresolved runtime symbol {relocation.symbol}"
                    )
                lines.append(f"    .word {asm_symbol(relocation.symbol)}")
                position += 2
                continue
            pending.append(module.payload[position])
            position += 1
        flush()
        if position in labels:
            for label in labels[position]:
                lines.append(f"{label}:")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the native ACTC compile-time REAL runtime include"
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rendered = render(load_closure())
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="ascii") != rendered:
            raise SystemExit(f"stale generated include: {args.output}")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="ascii")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
