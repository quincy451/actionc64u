#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
import subprocess
import sys


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def copy_into(dest: Path, source: Path, name: str | None = None) -> None:
    target = dest / (name or source.name.lower())
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage ActionC64U CP/M tools into a filesystem directory")
    parser.add_argument("dest", help="target directory representing a CP/M drive")
    parser.add_argument("--no-build", action="store_true", help="skip rebuilding actc.com and vm.com first")
    args = parser.parse_args(argv)

    root = repo_root()
    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)

    if not args.no_build:
        for script in [
            root / "tools" / "build_actc.sh",
            root / "tools" / "build_vmrun.sh",
            root / "tools" / "build_actmon.sh",
        ]:
            result = subprocess.run([str(script)], cwd=root, text=True, capture_output=True, check=False)
            if result.returncode != 0:
                sys.stderr.write(result.stdout)
                sys.stderr.write(result.stderr)
                return result.returncode

    copy_into(dest, root / "build" / "actmon.com")
    copy_into(dest, root / "build" / "actc.com")
    copy_into(dest, root / "build" / "vm.com")
    for manifest in sorted((root / "src" / "tools_cpm" / "libmods").glob("*.mod")):
        copy_into(dest, manifest)
    for source_name, target_name in [
        ("hello.act", None),
        ("math.act", None),
        ("if.act", None),
        ("real_demo.act", "realdemo.act"),
        ("real_cmp.act", None),
        ("reu_demo.act", None),
        ("ovl_demo.act", None),
    ]:
        copy_into(dest, root / "examples" / source_name, target_name)

    print(f"staged files in {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
