#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from build_release_image import build_release_image, inject_file, normalize_diskdefs, require_tool
from vice_harness import ViceHarness, ViceUnavailable, locate_x64sc

EXPECTED_MARKER = "HELLO FROM ACTIONC64U"


class VerificationUnavailable(RuntimeError):
    pass


class VerificationFailed(RuntimeError):
    pass


@dataclass(frozen=True)
class ScreenSnapshot:
    label: str
    screen: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_submit_file(path: Path, commands: list[str]) -> None:
    payload = bytearray()
    for command in reversed(commands):
        encoded = command.encode("ascii", errors="strict")
        if len(encoded) > 126:
            raise VerificationFailed(f"submit command is too long: {command!r}")
        record = bytearray((126, len(encoded)))
        record.extend(encoded)
        record.extend(b"\0" * (128 - len(record)))
        payload.extend(record)
    path.write_bytes(payload)


def compile_host_hello_avm(root: Path, output_path: Path) -> None:
    compiler = root / "tools" / "actionc64u_compile.py"
    source = root / "examples" / "hello.act"
    result = subprocess.run(
        [
            sys.executable,
            str(compiler),
            str(source),
            "--output",
            str(output_path),
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    compile_output = result.stdout + result.stderr
    if result.returncode != 0:
        raise VerificationFailed(f"host hello.avm compile failed:\n{compile_output}")
    if not output_path.is_file():
        raise VerificationFailed(f"host compiler succeeded but {output_path} is missing")


def is_unavailable_error(message: str) -> bool:
    needles = [
        "x64sc not found on PATH",
        "required tool not found on PATH",
        "no base C64 CP/M image found",
        "missing required CP/M-65 artifact",
        "CP/M-65 images directory not found",
        "unable to connect to VICE",
        "failed to start VICE monitor session",
        "timed out waiting for screen text 'A>'",
    ]
    return any(needle in message for needle in needles)


def write_transcript(path: Path, snapshots: list[ScreenSnapshot]) -> None:
    lines = [
        "ActionC64U release verification transcript",
        f"generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    for snapshot in snapshots:
        lines.append(f"[{snapshot.label}]")
        lines.append(snapshot.screen or "<empty screen>")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="ascii")


def collect_vm_run_transcript(
    *,
    disk_image: Path,
    expected_marker: str,
    boot_timeout: float,
    run_timeout: float,
) -> tuple[list[ScreenSnapshot], bool]:
    snapshots: list[ScreenSnapshot] = []
    with ViceHarness(disk_image=disk_image) as vice:
        boot_screen = vice.boot_to_cpm_prompt(timeout=boot_timeout)
        snapshots.append(ScreenSnapshot("boot", boot_screen))

        deadline = time.monotonic() + run_timeout
        last_screen = boot_screen
        while time.monotonic() < deadline:
            screen = vice.read_screen_text()
            if screen != last_screen:
                seconds_left = max(0.0, deadline - time.monotonic())
                elapsed = run_timeout - seconds_left
                label = f"screen+{elapsed:.1f}s"
                snapshots.append(ScreenSnapshot(label, screen))
                last_screen = screen
            if expected_marker in screen:
                return snapshots, True
            time.sleep(0.5)

    return snapshots, False


def run_verification(*, no_build: bool, transcript_path: Path, boot_timeout: float, run_timeout: float) -> Path:
    root = repo_root()
    locate_x64sc()
    for tool in ["cpmcp", "cpmls", "cpmchattr", "cpmrm"]:
        require_tool(tool)

    build_dir = root / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    release_image, _listing = build_release_image(no_build=no_build)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        verify_image = tmp / "actionc64u_c64_verify.d64"
        verify_avm = tmp / "hello.avm"
        submit_file = tmp / "$$$.sub"

        shutil.copy2(release_image, verify_image)
        compile_host_hello_avm(root, verify_avm)
        write_submit_file(submit_file, ["VM HELLO.AVM"])
        normalize_diskdefs(root, tmp / "diskdefs")
        inject_file(verify_image, verify_avm, "hello.avm", cwd=tmp)
        inject_file(verify_image, submit_file, "$$$.sub", cwd=tmp)

        snapshots, seen_marker = collect_vm_run_transcript(
            disk_image=verify_image,
            expected_marker=EXPECTED_MARKER,
            boot_timeout=boot_timeout,
            run_timeout=run_timeout,
        )
        write_transcript(transcript_path, snapshots)
        if not seen_marker:
            last_screen = snapshots[-1].screen if snapshots else "<empty screen>"
            raise VerificationFailed(
                f"expected marker {EXPECTED_MARKER!r} not found before timeout; "
                f"last screen was:\n{last_screen}"
            )

    return transcript_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the ActionC64U release image under VICE")
    parser.add_argument("--no-build", action="store_true", help="reuse existing build/release_stage contents")
    parser.add_argument(
        "--transcript",
        default=str(repo_root() / "build" / "verify_transcript.txt"),
        help="output transcript path",
    )
    parser.add_argument("--boot-timeout", type=float, default=120.0, help="seconds to wait for the CP/M prompt")
    parser.add_argument("--run-timeout", type=float, default=30.0, help="seconds to wait for the VM marker")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    transcript = Path(args.transcript)
    try:
        output_path = run_verification(
            no_build=args.no_build,
            transcript_path=transcript,
            boot_timeout=args.boot_timeout,
            run_timeout=args.run_timeout,
        )
    except VerificationFailed as exc:
        print(exc, file=sys.stderr)
        return 1
    except (ViceUnavailable, RuntimeError) as exc:
        message = str(exc)
        if is_unavailable_error(message):
            print(message, file=sys.stderr)
            return 2
        print(message, file=sys.stderr)
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
