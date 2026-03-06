#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    workspace = root.parent

    targets = {
        "actionc64u": root,
        "cpm65-u64": workspace / "cpm65-u64",
        "acheronvm": workspace / "acheronvm",
        "action.pdf": workspace / "action.pdf",
    }

    missing = []
    for label, path in targets.items():
        resolved = path.resolve()
        exists = resolved.exists()
        print(f"{label:10} {'PASS' if exists else 'FAIL'} {resolved}")
        if not exists:
            missing.append((label, resolved))

    if missing:
        print(
            "Missing required local paths. Verify you are running inside "
            "/mnt/c/test/action with adjacent cpm65-u64, acheronvm, and "
            "action.pdf.",
            file=sys.stderr,
        )
        return 1

    print("All required local paths resolved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
