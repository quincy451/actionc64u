#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


FORMAT = "action-shared-6502-v1"
MANIFEST = Path("resources/shared_6502_manifest.json")
MODULE_ROOT = Path("src/runtime/modules")
EXCLUDED_MODULES = (
    "rt_dbf_create.obj",
    "rt_dbf_file_open_write.obj",
)
SHARED_TOOLS = (
    Path("tools/generate_exact_print_runtime.py"),
    Path("tools/generate_input_runtime.py"),
    Path("tools/generate_math_runtime.py"),
    Path("tools/generate_reu_runtime.py"),
    Path("tools/shared_6502_sync.py"),
)


def shared_files(root: Path) -> tuple[Path, ...]:
    module_root = root / MODULE_ROOT
    modules = tuple(
        path.relative_to(root)
        for path in sorted(module_root.glob("*.obj"))
        if path.name not in EXCLUDED_MODULES
    )
    return modules + SHARED_TOOLS


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(root: Path) -> dict[str, object]:
    files: dict[str, str] = {}
    for relative in shared_files(root):
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f"missing shared 6502 file: {path}")
        files[relative.as_posix()] = file_digest(path)
    return {
        "format": FORMAT,
        "authority": "native ActionC64U target runtime",
        "excluded_modules": list(EXCLUDED_MODULES),
        "files": files,
    }


def load_manifest(root: Path) -> dict[str, object]:
    path = root / MANIFEST
    with path.open("r", encoding="ascii") as source:
        manifest = json.load(source)
    if not isinstance(manifest, dict):
        raise ValueError(f"manifest root must be an object: {path}")
    return manifest


def write_manifest(root: Path) -> None:
    path = root / MANIFEST
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(build_manifest(root), indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="ascii")


def verify_manifest(root: Path) -> list[str]:
    try:
        recorded = load_manifest(root)
        current = build_manifest(root)
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as error:
        return [str(error)]

    errors: list[str] = []
    if recorded.get("format") != FORMAT:
        errors.append(f"unsupported manifest format in {root / MANIFEST}")
    if recorded.get("excluded_modules") != list(EXCLUDED_MODULES):
        errors.append(f"excluded module policy differs in {root / MANIFEST}")

    recorded_files = recorded.get("files")
    if not isinstance(recorded_files, dict):
        return errors + [f"manifest files must be an object in {root / MANIFEST}"]
    current_files = current["files"]
    assert isinstance(current_files, dict)

    for relative in sorted(set(recorded_files) - set(current_files)):
        errors.append(f"manifest lists missing shared file: {relative}")
    for relative in sorted(set(current_files) - set(recorded_files)):
        errors.append(f"shared file is absent from manifest: {relative}")
    for relative in sorted(set(recorded_files) & set(current_files)):
        if recorded_files[relative] != current_files[relative]:
            errors.append(f"shared file digest differs: {relative}")
    return errors


def compare_roots(first: Path, second: Path) -> list[str]:
    errors = [f"{first}: {error}" for error in verify_manifest(first)]
    errors.extend(f"{second}: {error}" for error in verify_manifest(second))
    if errors:
        return errors

    first_manifest = load_manifest(first)
    second_manifest = load_manifest(second)
    if first_manifest != second_manifest:
        errors.append(
            f"shared 6502 manifests differ: {first / MANIFEST} != {second / MANIFEST}"
        )
    return errors


def sync_from(source: Path, destination: Path) -> None:
    errors = verify_manifest(source)
    if errors:
        raise RuntimeError("source manifest is stale:\n" + "\n".join(errors))
    manifest = load_manifest(source)
    files = manifest["files"]
    assert isinstance(files, dict)
    for relative_text in sorted(files):
        relative = Path(relative_text)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, target)
    target_manifest = destination / MANIFEST
    target_manifest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / MANIFEST, target_manifest)


def report(errors: list[str]) -> int:
    if not errors:
        return 0
    for error in errors:
        print(f"STALE {error}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Keep shared Action 6502 runtime modules synchronized"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository to verify or update",
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write-manifest", action="store_true")
    action.add_argument("--check-peer", type=Path)
    action.add_argument("--sync-from", type=Path)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    if args.write_manifest:
        write_manifest(root)
        print(root / MANIFEST)
        return 0
    if args.sync_from is not None:
        sync_from(args.sync_from.resolve(), root)
        return report(verify_manifest(root))
    if args.check_peer is not None:
        return report(compare_roots(root, args.check_peer.resolve()))
    return report(verify_manifest(root))


if __name__ == "__main__":
    raise SystemExit(main())
