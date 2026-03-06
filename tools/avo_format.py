#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

MAGIC = "AVO1"
VERSION = 1
SYMBOL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")


class AvoFormatError(ValueError):
    pass


@dataclass(frozen=True)
class OverlayObject:
    name: str
    imports: list[str]
    payload: bytes


@dataclass(frozen=True)
class AvoObject:
    module_name: str
    entry_offset: int
    exports: list[tuple[str, int]]
    imports: list[str]
    payload: bytes
    overlays: list[OverlayObject]
    version: int = VERSION


def _validate_symbol(name: str) -> None:
    if not SYMBOL_RE.match(name):
        raise AvoFormatError(f"invalid symbol name: {name!r}")


def _validate_offset(offset: int, payload_len: int, label: str) -> None:
    if not isinstance(offset, int):
        raise AvoFormatError(f"{label} must be an integer")
    if not 0 <= offset <= payload_len:
        raise AvoFormatError(f"{label} must point inside the payload")


def normalize_exports(exports: list[tuple[str, int]], payload_len: int) -> list[tuple[str, int]]:
    normalized: list[tuple[str, int]] = []
    seen: set[str] = set()
    for name, offset in exports:
        _validate_symbol(name)
        _validate_offset(offset, payload_len, f"export offset for {name}")
        if name in seen:
            raise AvoFormatError(f"duplicate export symbol: {name}")
        seen.add(name)
        normalized.append((name, offset))
    return sorted(normalized, key=lambda item: item[0])


def normalize_imports(imports: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for name in imports:
        _validate_symbol(name)
        if name not in seen:
            seen.add(name)
            normalized.append(name)
    return sorted(normalized)


def normalize_overlays(overlays: list[OverlayObject]) -> list[OverlayObject]:
    normalized: list[OverlayObject] = []
    seen: set[str] = set()
    for overlay in overlays:
        _validate_symbol(overlay.name)
        if overlay.name in seen:
            raise AvoFormatError(f"duplicate overlay name: {overlay.name}")
        seen.add(overlay.name)
        normalized.append(
            OverlayObject(
                name=overlay.name,
                imports=normalize_imports(overlay.imports),
                payload=overlay.payload,
            )
        )
    return sorted(normalized, key=lambda item: item.name)


def pack_avo(obj: AvoObject) -> str:
    if obj.version != VERSION:
        raise AvoFormatError(f"unsupported AVO version: {obj.version}")
    if not obj.module_name:
        raise AvoFormatError("module_name is required")
    _validate_symbol(obj.module_name)
    _validate_offset(obj.entry_offset, len(obj.payload), "entry_offset")

    data = {
        "entry_offset": obj.entry_offset,
        "exports": [[name, offset] for name, offset in normalize_exports(obj.exports, len(obj.payload))],
        "imports": normalize_imports(obj.imports),
        "module": obj.module_name,
        "overlays": [
            {
                "imports": overlay.imports,
                "name": overlay.name,
                "payload_hex": overlay.payload.hex(),
            }
            for overlay in normalize_overlays(obj.overlays)
        ],
        "payload_hex": obj.payload.hex(),
        "version": obj.version,
    }
    return MAGIC + "\n" + json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n"


def unpack_avo(text: str) -> AvoObject:
    lines = text.splitlines()
    if not lines or lines[0] != MAGIC:
        raise AvoFormatError("bad AVO magic")
    if len(lines) < 2:
        raise AvoFormatError("missing AVO metadata line")

    try:
        data = json.loads(lines[1])
    except json.JSONDecodeError as exc:
        raise AvoFormatError("invalid AVO metadata JSON") from exc

    if data.get("version") != VERSION:
        raise AvoFormatError(f"unsupported AVO version: {data.get('version')}")

    payload_hex = data.get("payload_hex", "")
    try:
        payload = bytes.fromhex(payload_hex)
    except ValueError as exc:
        raise AvoFormatError("payload_hex is not valid hex") from exc

    module_name = data.get("module")
    if not isinstance(module_name, str):
        raise AvoFormatError("module must be a string")

    entry_offset = data.get("entry_offset")
    if not isinstance(entry_offset, int):
        raise AvoFormatError("entry_offset must be an integer")

    raw_exports = data.get("exports", [])
    if not isinstance(raw_exports, list):
        raise AvoFormatError("exports must be a list")
    exports: list[tuple[str, int]] = []
    for item in raw_exports:
        if not isinstance(item, list) or len(item) != 2:
            raise AvoFormatError("each export must be [name, offset]")
        name, offset = item
        if not isinstance(name, str) or not isinstance(offset, int):
            raise AvoFormatError("invalid export entry")
        exports.append((name, offset))

    raw_imports = data.get("imports", [])
    if not isinstance(raw_imports, list) or any(not isinstance(name, str) for name in raw_imports):
        raise AvoFormatError("imports must be a list of strings")

    raw_overlays = data.get("overlays", [])
    if not isinstance(raw_overlays, list):
        raise AvoFormatError("overlays must be a list")
    overlays: list[OverlayObject] = []
    for item in raw_overlays:
        if not isinstance(item, dict):
            raise AvoFormatError("overlay entries must be objects")
        name = item.get("name")
        payload_hex = item.get("payload_hex", "")
        imports = item.get("imports", [])
        if not isinstance(name, str):
            raise AvoFormatError("overlay name must be a string")
        if not isinstance(imports, list) or any(not isinstance(symbol, str) for symbol in imports):
            raise AvoFormatError("overlay imports must be a list of strings")
        try:
            overlay_payload = bytes.fromhex(payload_hex)
        except ValueError as exc:
            raise AvoFormatError("overlay payload_hex is not valid hex") from exc
        overlays.append(
            OverlayObject(
                name=name,
                imports=normalize_imports(imports),
                payload=overlay_payload,
            )
        )

    return AvoObject(
        module_name=module_name,
        entry_offset=entry_offset,
        exports=normalize_exports(exports, len(payload)),
        imports=normalize_imports(raw_imports),
        payload=payload,
        overlays=normalize_overlays(overlays),
        version=VERSION,
    )


def write_avo(path: Path, obj: AvoObject) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pack_avo(obj), encoding="ascii")


def read_avo(path: Path) -> AvoObject:
    try:
        text = path.read_text(encoding="ascii")
    except UnicodeDecodeError as exc:
        raise AvoFormatError(f"{path} is not valid ASCII AVO text") from exc
    return unpack_avo(text)
