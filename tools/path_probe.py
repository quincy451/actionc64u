#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    workspace = root.parent

    targets = {
        "actionc64u": root,
        "udos": workspace / "udos",
        "action.pdf": root / "docs" / "inspiration" / "action.pdf",
        "lib6502": root / "third_party" / "lib6502" / "lib6502.c",
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
            "Missing required project paths. Verify the ActionC64U and UDOS "
            "trees were copied together.",
            file=sys.stderr,
        )
        return 1

    print("All required local paths resolved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
