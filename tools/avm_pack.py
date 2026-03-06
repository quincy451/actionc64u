#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import struct
import sys
import tempfile

MAGIC = b"AVM1"
VERSION = 1
HEADER = struct.Struct("<4sBHHB")
OPCODE_NATIVE = 0x2D
OPCODE_CALLN = 0x49


@dataclass(frozen=True)
class AvmFile:
    version: int
    payload: bytes
    entry_offset: int
    flags: int = 0


def parse_number(token: str) -> int:
    token = token.strip()
    if token.startswith("$"):
        return int(token[1:], 16)
    return int(token, 0)


def encode_text(source: str) -> bytes:
    payload = bytearray()
    for lineno, raw_line in enumerate(source.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].split(";", 1)[0].strip()
        if not line:
            continue

        parts = [part.rstrip(",") for part in line.split()]
        op = parts[0].lower()

        if op == "native":
            payload.append(OPCODE_NATIVE)
            continue

        if op == "calln":
            if len(parts) != 2:
                raise ValueError(f"line {lineno}: calln requires one address operand")
            target = parse_number(parts[1])
            if not 0 <= target <= 0xFFFF:
                raise ValueError(f"line {lineno}: calln target out of range: {parts[1]}")
            payload.extend((OPCODE_CALLN, target & 0xFF, target >> 8))
            continue

        if op in {"byte", "db"}:
            if len(parts) < 2:
                raise ValueError(f"line {lineno}: {op} requires at least one byte")
            for token in parts[1:]:
                value = parse_number(token)
                if not 0 <= value <= 0xFF:
                    raise ValueError(f"line {lineno}: byte out of range: {token}")
                payload.append(value)
            continue

        raise ValueError(f"line {lineno}: unsupported opcode/directive: {parts[0]}")

    return bytes(payload)


def pack_avm(payload: bytes, *, entry_offset: int, flags: int = 0, version: int = VERSION) -> bytes:
    if not 0 <= version <= 0xFF:
        raise ValueError("version must fit in one byte")
    if not 0 <= flags <= 0xFF:
        raise ValueError("flags must fit in one byte")
    if len(payload) > 0xFFFF:
        raise ValueError("payload too large for version 1 header")
    if not 0 <= entry_offset <= len(payload):
        raise ValueError("entry offset must point inside the payload")
    return HEADER.pack(MAGIC, version, len(payload), entry_offset, flags) + payload


def unpack_avm(data: bytes) -> AvmFile:
    if len(data) < HEADER.size:
        raise ValueError("file too short for AVM header")
    magic, version, payload_len, entry_offset, flags = HEADER.unpack_from(data)
    if magic != MAGIC:
        raise ValueError(f"bad magic: {magic!r}")
    if version != VERSION:
        raise ValueError(f"unsupported version: {version}")
    if flags != 0:
        raise ValueError(f"unsupported flags for version 1: {flags}")
    payload = data[HEADER.size : HEADER.size + payload_len]
    if len(payload) != payload_len:
        raise ValueError("truncated payload")
    if entry_offset > payload_len:
        raise ValueError("entry offset beyond payload length")
    return AvmFile(version=version, payload=payload, entry_offset=entry_offset, flags=flags)


def run_selftest() -> int:
    payload = encode_text("native\n")
    packed = pack_avm(payload, entry_offset=0)
    unpacked = unpack_avm(packed)
    if unpacked.payload != payload or unpacked.entry_offset != 0:
        print("selftest failed: roundtrip mismatch", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "selftest.avm"
        out_path.write_bytes(packed)
        reread = unpack_avm(out_path.read_bytes())
        if reread.payload != payload:
            print("selftest failed: disk roundtrip mismatch", file=sys.stderr)
            return 1

    print("avm_pack selftest OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pack raw bytes or tiny text into ActionC64U .avm files")
    parser.add_argument("input", nargs="?", help="input payload file")
    parser.add_argument("-o", "--output", help="output .avm file")
    parser.add_argument("--entry-offset", type=parse_number, default=0, help="entry offset within the payload")
    parser.add_argument("--text", action="store_true", help="treat input as tiny assembly-like text")
    parser.add_argument("--selftest", action="store_true", help="run pack/unpack self-test and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.selftest:
        return run_selftest()

    if not args.input or not args.output:
        parser.error("input and --output are required unless --selftest is used")

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.is_file():
        parser.error(f"input file not found: {input_path}")

    payload = encode_text(input_path.read_text()) if args.text else input_path.read_bytes()
    packed = pack_avm(payload, entry_offset=args.entry_offset)
    output_path.write_bytes(packed)
    print(f"wrote {output_path} ({len(payload)} payload bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
