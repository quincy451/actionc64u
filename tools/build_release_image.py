#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def cpm_root(root: Path) -> Path:
    return root.parent / "cpm65-u64"


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"required tool not found on PATH: {name}")
    return path


def find_base_image(root: Path) -> Path:
    cpm = cpm_root(root)
    images_dir = cpm / "images"
    if images_dir.is_dir():
        candidates = sorted(images_dir.glob("c64*.d64"))
        if candidates:
            return candidates[0]

    fallback = cpm / ".obj" / "src" / "arch" / "commodore" / "+c64_cbmfs" / "src" / "arch" / "commodore" / "+c64_cbmfs.d64"
    if fallback.is_file():
        return fallback

    raise RuntimeError("no base C64 CP/M image found; build ../cpm65-u64 C64 targets first")


def normalize_diskdefs(root: Path, dest: Path) -> None:
    diskdefs = cpm_root(root) / "diskdefs"
    if not diskdefs.is_file():
        raise RuntimeError(f"missing diskdefs file: {diskdefs}")
    dest.write_text(diskdefs.read_text(encoding="ascii").replace("\r\n", "\n"), encoding="ascii")


def run(command: list[str], *, cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def locate_core_file(root: Path, relative: str) -> Path:
    path = cpm_root(root) / relative
    if not path.is_file():
        raise RuntimeError(f"missing required CP/M-65 artifact: {path}")
    return path


def remove_file(image: Path, target_name: str, *, cwd: Path) -> None:
    subprocess.run(
        ["cpmchattr", "-f", "c1541", str(image), "n", f"0:{target_name}"],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    subprocess.run(
        ["cpmrm", "-f", "c1541", str(image), f"0:{target_name}"],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def inject_file(image: Path, source: Path, target_name: str, *, cwd: Path) -> None:
    remove_file(image, target_name, cwd=cwd)
    run(["cpmcp", "-f", "c1541", str(image), str(source), f"0:{target_name}"], cwd=cwd)


def list_image_files(image: Path, *, cwd: Path) -> list[str]:
    listing = subprocess.run(
        ["cpmls", "-f", "c1541", str(image)],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if listing.returncode != 0:
        raise RuntimeError(f"cpmls failed:\nstdout:\n{listing.stdout}\nstderr:\n{listing.stderr}")

    files: list[str] = []
    for line in listing.stdout.splitlines():
        entry = line.strip()
        if not entry or entry.endswith(":"):
            continue
        files.append(entry.lower())
    return files


def build_manifest_bundle(source_dir: Path, output_path: Path) -> None:
    parts: list[str] = []
    for manifest in sorted(source_dir.glob("*.mod")):
        text = manifest.read_text(encoding="ascii").replace("\r\n", "\n").strip()
        parts.append(f"FILE {manifest.name.lower()}\n{text}\nEND\n")
    output_path.write_text("\n".join(parts), encoding="ascii")


RELEASE_BASE_KEEP = {
    "adm3adrv.com",
    "adm3atst.com",
    "bdos.sys",
    "bedit.com",
    "capsdrv.com",
    "cbmfs.sys",
    "ccp.sys",
    "cls.com",
    "devices.com",
    "dinfo.com",
    "dump.com",
    "submit.com",
    "vt52drv.com",
    "vt52test.com",
}


def prune_base_image(image: Path, *, cwd: Path) -> None:
    for filename in list_image_files(image, cwd=cwd):
        if filename in RELEASE_BASE_KEEP:
            continue
        remove_file(image, filename, cwd=cwd)


def build_release_image(*, no_build: bool) -> tuple[Path, Path]:
    root = repo_root()
    require_tool("cpmcp")
    require_tool("cpmls")
    require_tool("cpmchattr")
    require_tool("cpmrm")

    build_dir = root / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    out_image = build_dir / "actionc64u_c64.d64"
    out_listing = build_dir / "actionc64u_c64.dir.txt"

    if not no_build:
        run([str(root / "tools" / "install_to_image.py"), "--clean", str(build_dir / "release_stage")], cwd=root)

    stage_dir = build_dir / "release_stage"
    if not stage_dir.is_dir():
        raise RuntimeError(f"missing staged files directory: {stage_dir}")

    base_image = find_base_image(root)
    shutil.copy2(base_image, out_image)

    ccp = locate_core_file(root, ".obj/src/+ccp/ccp")
    bdos = locate_core_file(root, ".obj/src/bdos/+bdos/bdos")
    optional_core = [
        ("bedit.com", cpm_root(root) / ".obj/apps/+bedit/out.com"),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        normalize_diskdefs(root, tmp / "diskdefs")
        manifest_bundle = tmp / "libmods.dat"
        build_manifest_bundle(root / "src" / "tools_cpm" / "libmods", manifest_bundle)

        prune_base_image(out_image, cwd=tmp)
        base_files = set(list_image_files(out_image, cwd=tmp))
        if "ccp.sys" not in base_files:
            inject_file(out_image, ccp, "ccp.sys", cwd=tmp)
        run(["cpmchattr", "-f", "c1541", str(out_image), "sr", "0:ccp.sys"], cwd=tmp)
        if "bdos.sys" not in base_files:
            inject_file(out_image, bdos, "bdos.sys", cwd=tmp)
        run(["cpmchattr", "-f", "c1541", str(out_image), "sr", "0:bdos.sys"], cwd=tmp)

        refreshed_files = set(list_image_files(out_image, cwd=tmp))
        for target_name, source in optional_core:
            if target_name in refreshed_files:
                continue
            if source.is_file():
                inject_file(out_image, source, target_name, cwd=tmp)
        inject_file(out_image, manifest_bundle, "libmods.dat", cwd=tmp)
        for source in sorted(stage_dir.iterdir()):
            if source.is_file():
                if source.suffix.lower() == ".mod":
                    continue
                inject_file(out_image, source, source.name.lower(), cwd=tmp)

        listing = subprocess.run(
            ["cpmls", "-f", "c1541", str(out_image)],
            cwd=tmp,
            text=True,
            capture_output=True,
            check=False,
        )
        if listing.returncode != 0:
            raise RuntimeError(f"cpmls failed:\nstdout:\n{listing.stdout}\nstderr:\n{listing.stderr}")
        out_listing.write_text(listing.stdout, encoding="ascii")

    return out_image, out_listing


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the ActionC64U C64 CP/M-65 release disk image")
    parser.add_argument("--no-build", action="store_true", help="reuse existing build/release_stage contents")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        image, listing = build_release_image(no_build=args.no_build)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    print(image)
    print(listing)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
