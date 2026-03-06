#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

from avo_format import AvoFormatError, AvoObject, read_avo
from avm_pack import pack_avm


class LinkError(Exception):
    pass


@dataclass(frozen=True)
class IncludedObject:
    path: Path
    obj: AvoObject
    base_offset: int


def load_library_objects(runtime_dirs: list[Path]) -> list[tuple[Path, AvoObject]]:
    loaded: list[tuple[Path, AvoObject]] = []
    for runtime_dir in sorted(runtime_dirs, key=str):
        if not runtime_dir.exists():
            raise LinkError(f"runtime directory not found: {runtime_dir}")
        for path in sorted(runtime_dir.glob("*.avo")):
            loaded.append((path.resolve(), read_avo(path)))
    return loaded


def build_export_index(objects: list[tuple[Path, AvoObject]]) -> dict[str, tuple[Path, AvoObject]]:
    exports: dict[str, tuple[Path, AvoObject]] = {}
    for path, obj in objects:
        for name, _offset in obj.exports:
            if name in exports:
                other_path, _other_obj = exports[name]
                raise LinkError(f"duplicate export symbol '{name}' in {other_path} and {path}")
            exports[name] = (path, obj)
    return exports


def resolve_objects(main_path: Path, main_obj: AvoObject, libraries: list[tuple[Path, AvoObject]]) -> list[IncludedObject]:
    export_index = build_export_index([(main_path.resolve(), main_obj), *libraries])
    included: list[tuple[Path, AvoObject]] = [(main_path.resolve(), main_obj)]
    included_paths = {main_path.resolve()}
    pending = set(main_obj.imports)

    while pending:
        symbol = sorted(pending)[0]
        pending.remove(symbol)
        provider = export_index.get(symbol)
        if provider is None:
            raise LinkError(f"unresolved symbol: {symbol}")
        provider_path, provider_obj = provider
        if provider_path not in included_paths:
            included.append((provider_path, provider_obj))
            included_paths.add(provider_path)
            pending.update(provider_obj.imports)

    resolved: list[IncludedObject] = []
    base_offset = 0
    for path, obj in included:
        resolved.append(IncludedObject(path=path, obj=obj, base_offset=base_offset))
        base_offset += len(obj.payload)
    return resolved


def render_map(included: list[IncludedObject], export_index: dict[str, tuple[Path, AvoObject]]) -> str:
    lines = ["# ActionC64U Link Map", ""]
    lines.append(f"entry main @ 0x{included[0].base_offset + included[0].obj.entry_offset:04x}")
    lines.append("")
    lines.append("included modules:")
    for item in included:
        lines.append(
            f"- {item.obj.module_name} path={item.path} base=0x{item.base_offset:04x} size={len(item.obj.payload)}"
        )
    lines.append("")
    lines.append("exports:")
    for item in included:
        for name, offset in item.obj.exports:
            lines.append(f"- {name} = 0x{item.base_offset + offset:04x} ({item.obj.module_name})")
    lines.append("")
    lines.append("resolved imports:")
    for item in included:
        for symbol in item.obj.imports:
            provider_path, provider_obj = export_index[symbol]
            lines.append(f"- {item.obj.module_name}: {symbol} -> {provider_obj.module_name} ({provider_path})")
    lines.append("")
    return "\n".join(lines)


def link(main_path: Path, runtime_dirs: list[Path], avm_output: Path, map_output: Path) -> None:
    main_obj = read_avo(main_path)
    libraries = load_library_objects(runtime_dirs)
    export_index = build_export_index([(main_path.resolve(), main_obj), *libraries])
    included = resolve_objects(main_path, main_obj, libraries)
    payload = b"".join(item.obj.payload for item in included)
    avm_output.parent.mkdir(parents=True, exist_ok=True)
    avm_output.write_bytes(pack_avm(payload, entry_offset=main_obj.entry_offset))
    map_output.parent.mkdir(parents=True, exist_ok=True)
    map_output.write_text(render_map(included, export_index), encoding="ascii")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Link ActionC64U .avo objects into a final .avm")
    parser.add_argument("main_object", help="main .avo file")
    parser.add_argument("-o", "--output", help="output .avm file")
    parser.add_argument("--map-output", help="output link map path")
    parser.add_argument(
        "--runtime-dir",
        action="append",
        default=[],
        help="runtime module directory (default: src/runtime/modules)",
    )
    return parser


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_runtime_dirs() -> list[Path]:
    return [repo_root() / "src" / "runtime" / "modules"]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    main_path = Path(args.main_object)
    if not main_path.is_file():
        parser.error(f"main object not found: {main_path}")

    avm_output = Path(args.output) if args.output else main_path.with_suffix(".avm")
    map_output = Path(args.map_output) if args.map_output else avm_output.with_suffix(".map.txt")
    runtime_dirs = [Path(path) for path in args.runtime_dir] if args.runtime_dir else default_runtime_dirs()

    try:
        link(main_path, runtime_dirs, avm_output, map_output)
    except (AvoFormatError, LinkError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1

    print(f"wrote {avm_output}")
    print(f"wrote {map_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
