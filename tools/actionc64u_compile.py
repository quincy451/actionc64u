#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Iterable

OPCODE_CALLN = 0x49
OPCODE_SETP16 = 0x61
INTR_PRINT = 0xFF00
INTR_PRINTE = 0xFF10
INTR_EXIT = 0xFF20


@dataclass(frozen=True)
class Statement:
    kind: str
    value: str


def parse_source(text: str) -> list[Statement]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    index = 0

    if index < len(lines) and lines[index].upper().startswith("MODULE "):
        index += 1

    if index >= len(lines) or lines[index].upper() != "PROC MAIN()":
        raise ValueError("expected 'PROC main()'")
    index += 1

    statements: list[Statement] = []
    while index < len(lines):
        line = lines[index]
        upper = line.upper()
        if upper == "RETURN":
            index += 1
            break

        if upper.startswith("PRINTE(") or upper.startswith("PRINT("):
            kind = "PrintE" if upper.startswith("PRINTE(") else "Print"
            if not line.endswith(")"):
                raise ValueError(f"bad statement syntax: {line}")
            literal = line[line.find("(") + 1 : -1].strip()
            try:
                value = ast.literal_eval(literal)
            except (SyntaxError, ValueError) as exc:
                raise ValueError(f"invalid string literal: {literal}") from exc
            if not isinstance(value, str):
                raise ValueError(f"expected string literal in {line}")
            value.encode("ascii")
            statements.append(Statement(kind=kind, value=value))
            index += 1
            continue

        raise ValueError(f"unsupported statement: {line}")

    if index != len(lines):
        raise ValueError(f"unexpected trailing input: {lines[index]}")
    if not statements:
        raise ValueError("main must contain at least one Print/PrintE statement")
    return statements


def encode_u16(value: int) -> bytes:
    return bytes((value & 0xFF, (value >> 8) & 0xFF))


def compile_statements(statements: Iterable[Statement]) -> bytes:
    code = bytearray()
    strings = bytearray()
    pending_offsets: list[tuple[int, int]] = []

    for stmt in statements:
        code.append(OPCODE_SETP16)
        patch_index = len(code)
        code.extend(b"\x00\x00")
        pending_offsets.append((patch_index, len(strings)))

        intrinsic = INTR_PRINTE if stmt.kind == "PrintE" else INTR_PRINT
        code.append(OPCODE_CALLN)
        code.extend(encode_u16(intrinsic))

        strings.extend(stmt.value.encode("ascii"))
        strings.append(0)

    code.append(OPCODE_CALLN)
    code.extend(encode_u16(INTR_EXIT))

    string_base = len(code)
    for patch_index, string_offset in pending_offsets:
        absolute = string_base + string_offset
        code[patch_index : patch_index + 2] = encode_u16(absolute)

    code.extend(strings)
    return bytes(code)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compile a minimal Action-like source file into ActionC64U .avm")
    parser.add_argument("input", help="input .act file")
    parser.add_argument("-o", "--output", required=True, help="output .avm file")
    parser.add_argument("--entry-offset", type=int, default=0, help="entry offset for the generated payload")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.is_file():
        parser.error(f"input file not found: {input_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    source_text = input_path.read_text(encoding="ascii")
    statements = parse_source(source_text)
    payload = compile_statements(statements)

    avm_pack = Path(__file__).resolve().with_name("avm_pack.py")
    with tempfile.NamedTemporaryFile(
        mode="wb",
        suffix=".payload",
        prefix=f"{output_path.stem}-",
        dir=output_path.parent,
        delete=False,
    ) as handle:
        handle.write(payload)
        payload_path = Path(handle.name)

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(avm_pack),
                str(payload_path),
                "--entry-offset",
                str(args.entry_offset),
                "--output",
                str(output_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        payload_path.unlink(missing_ok=True)

    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        return result.returncode

    sys.stdout.write(result.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
