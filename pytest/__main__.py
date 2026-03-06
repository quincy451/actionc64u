from __future__ import annotations

import argparse
from pathlib import Path
import sys
import unittest

from . import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pytest",
        description="Bootstrap pytest compatibility runner for ActionC64U.",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="reduce test output")
    parser.add_argument("--version", action="store_true", help="print the local shim version")
    parser.add_argument("paths", nargs="*", help="optional test path roots")
    args, unknown = parser.parse_known_args(argv)

    if args.version:
        print(f"pytest {__version__}")
        return 0

    if unknown:
        parser.error(f"unsupported arguments for bootstrap runner: {' '.join(unknown)}")

    root = Path.cwd()
    start_dir = root / "tests"
    if args.paths:
        candidate = root / args.paths[0]
        if candidate.is_dir():
            start_dir = candidate
        elif candidate.is_file():
            start_dir = candidate.parent
        else:
            parser.error(f"test path not found: {candidate}")

    suite = unittest.defaultTestLoader.discover(str(start_dir), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=1 if args.quiet else 2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
