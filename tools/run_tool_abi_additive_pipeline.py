#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
UDOS_ROOT = ROOT.parent / "udos"
BUILD_DIR = ROOT / "build" / "udos_tools"
HARNESS = BUILD_DIR / "tool_abi_harness"
ACTC_PRG = BUILD_DIR / "ACTC.PRG"
ALINK_PRG = BUILD_DIR / "ALINK.PRG"
AVMRUN_PRG = BUILD_DIR / "AVMRUN.PRG"
ACTC_LABELS = BUILD_DIR / "actc.current.labels"
ALINK_LABELS = BUILD_DIR / "alink.current.labels"
AVMRUN_LABELS = BUILD_DIR / "avmrun.current.labels"
SERVICES_INC = BUILD_DIR / "udos_services.inc"
DEFAULT_BASE_FS = UDOS_ROOT / "build" / "udos-release-fs-manual-pipeline-44"

SCENARIOS = {
    "additive": {
        "out_fs_name": "harness-actc-alink-avmrun-additive",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'PrintE("HELLO")\r'
            'W()\r'
            'PrintI(50 + 7 - 3)\r'
            'PrintIE(60 - 3 + 2)\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 38\n"
            "b e0u0p0p1ap2myp3p4mp5azr\n"
            "u w\n"
            "s HELLO\n"
            "i 50\n"
            "i 7\n"
            "i 3\n"
            "i 60\n"
            "i 3\n"
            "i 2\n"
            "k 7\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 64, 0, 0, 0, 1, 53, 0, 97, 53, 0, 73,
                16, 255, 69, 40, 0, 17, 50, 0, 17, 7, 0, 20, 17, 3, 0, 21,
                73, 48, 255, 17, 60, 0, 17, 3, 0, 21, 17, 2, 0, 20, 73, 49,
                255, 73, 32, 255, 97, 59, 0, 73, 0, 255, 17, 7, 0, 73, 49,
                255, 72, 72, 69, 76, 76, 79, 0, 84, 79, 79, 76, 0,
            ]
        ),
        "expected_console": "HELLO\nTOOL7\n5459\n",
    },
    "precedence": {
        "out_fs_name": "harness-actc-alink-avmrun-precedence",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'PrintI(2 + 3 * 4)\r'
            'PrintIE((20 - 5) / 3)\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 17\n"
            "b p0p1ayi2r\n"
            "i 2\n"
            "i 12\n"
            "i 5\n"
            "k 7\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 19, 0, 0, 0, 1, 19, 0, 17, 2, 0, 17,
                12, 0, 20, 73, 48, 255, 17, 5, 0, 73, 49, 255, 73, 32, 255,
            ]
        ),
        "expected_console": "145\n",
    },
    "comparisons": {
        "out_fs_name": "harness-actc-alink-avmrun-comparisons",
        "source": (
            'MODULE MAIN\r'
            'PROC MAIN()\r'
            'PrintIE(2 + 3 * 4)\r'
            'PrintIE((20 - 5) / 3)\r'
            'PrintIE((2 + 3) * 4 = 20)\r'
            'PrintIE((2 + 3 * 4) > 10)\r'
            'W()\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x main 0 40\n"
            "b p0p1azi2p3p4qzp5p6gzu0r\n"
            "u w\n"
            "i 2\n"
            "i 12\n"
            "i 5\n"
            "i 20\n"
            "i 20\n"
            "i 14\n"
            "i 10\n"
            "k 6\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 60, 0, 0, 0, 1, 55, 0, 17, 2, 0, 17,
                12, 0, 20, 73, 49, 255, 17, 5, 0, 73, 49, 255, 17, 20, 0,
                17, 20, 0, 22, 73, 49, 255, 17, 14, 0, 17, 10, 0, 29, 73,
                49, 255, 69, 42, 0, 73, 32, 255, 97, 55, 0, 73, 0, 255, 17,
                7, 0, 73, 49, 255, 72, 84, 79, 79, 76, 0,
            ]
        ),
        "expected_console": "14\n5\n1\n1\nTOOL7\n",
    },
    "procedures": {
        "out_fs_name": "harness-actc-alink-avmrun-procedures",
        "source": (
            'MODULE MAIN\r'
            'PROC HELLO()\r'
            'PrintE("ONE")\r'
            'RETURN\r'
            'PROC MAIN()\r'
            'HELLO()\r'
            'PrintE("TWO")\r'
            'RETURN\r'
        ),
        "expected_avo": (
            "AVO1\n"
            "x hello 0 7\n"
            "x main 7 10\n"
            "b e0r\n"
            "b c0e1r\n"
            "s ONE\n"
            "s TWO\n"
            "k 2\n"
            "n main\n"
        ),
        "expected_avm": bytes(
            [
                65, 86, 77, 49, 2, 27, 0, 7, 0, 1, 19, 0, 97, 19, 0, 73,
                16, 255, 72, 69, 0, 0, 97, 23, 0, 73, 16, 255, 73, 32, 255,
                79, 78, 69, 0, 84, 87, 79, 0,
            ]
        ),
        "expected_console": "ONE\nTWO\n",
    },
}


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )


def build_current_tools() -> None:
    for script in (
        "build_tool_abi_harness.sh",
        "build_actc_udos.sh",
        "build_alink_udos.sh",
        "build_avmrun_udos.sh",
    ):
        run([str(ROOT / "tools" / script)], cwd=ROOT)


def prepare_workspace(base_fs: Path, out_fs: Path, source: str) -> Path:
    project_root = out_fs / "IMAGES" / "ACTION.DNP" / "PROJ3"
    shutil.rmtree(out_fs, ignore_errors=True)
    shutil.copytree(base_fs, out_fs)
    (project_root / "src" / "main.act").write_text(source, encoding="ascii")
    for stale in (
        project_root / "obj" / "MAIN.AVO",
        project_root / "obj" / "main.avo",
        project_root / "bin" / "MAIN.AVM",
        project_root / "bin" / "main.avm",
        project_root / "MAIN.AVO",
        project_root / "main.avo",
        project_root / "MAIN.AVM",
        project_root / "main.avm",
    ):
        if stale.exists():
            stale.unlink()
    return project_root


def run_harness(prg: Path, workspace: Path, cmdline: str, labels: Path, extra: list[str]) -> dict:
    cmd = [
        str(HARNESS),
        "--prg",
        str(prg),
        "--workspace",
        str(workspace),
        "--cmdline",
        cmdline,
        "--services-inc",
        str(SERVICES_INC),
        "--labels",
        str(labels),
        "--max-steps",
        "4000000",
        *extra,
    ]
    result = run(cmd, cwd=ROOT)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"failed to decode harness output for {prg.name}:\n{result.stdout}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def find_last_op(summary: dict, kind: str) -> dict:
    matches = [op for op in summary.get("ops", []) if op.get("kind") == kind]
    require(bool(matches), f"missing {kind!r} operation in harness summary")
    return matches[-1]


def verify_actc(project_root: Path, summary: dict, expected_avo: str) -> None:
    require(summary["exit_status"] == 0, f"ACTC exited nonzero: {summary['exit_status']}")
    save_op = find_last_op(summary, "save")
    require(save_op["path"] == "OBJ/MAIN.AVO", f"unexpected ACTC save path: {save_op['path']!r}")
    require(save_op["actual_len"] == len(expected_avo.encode("ascii")), f"unexpected ACTC object size: {save_op['actual_len']}")
    output_path = project_root / "obj" / "MAIN.AVO"
    require(output_path.is_file(), f"missing ACTC output: {output_path}")
    text = output_path.read_text(encoding="ascii", errors="replace")
    require(text == expected_avo, f"unexpected ACTC object text:\n{text}")


def verify_alink(project_root: Path, summary: dict, expected_avm: bytes) -> None:
    require(summary["exit_status"] == 0, f"ALINK exited nonzero: {summary['exit_status']}")
    save_op = find_last_op(summary, "save")
    require(save_op["path"] == "BIN/MAIN.AVM", f"unexpected ALINK save path: {save_op['path']!r}")
    require(save_op["actual_len"] == len(expected_avm), f"unexpected ALINK image size: {save_op['actual_len']}")
    output_path = project_root / "bin" / "MAIN.AVM"
    require(output_path.is_file(), f"missing ALINK output: {output_path}")
    data = output_path.read_bytes()
    require(data == expected_avm, f"unexpected ALINK bytes: {list(data)}")


def verify_avmrun(summary: dict, expected_console: str) -> None:
    require(summary["exit_status"] == 0, f"AVMRUN exited nonzero: {summary['exit_status']}")
    require(summary.get("console", "") == expected_console, f"unexpected AVMRUN console: {summary.get('console', '')!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run named ACTC -> ALINK -> AVMRUN harness proofs")
    parser.add_argument("--base-fs", type=Path, default=DEFAULT_BASE_FS)
    parser.add_argument("--out-fs", type=Path)
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="additive")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--keep-workspace", action="store_true")
    args = parser.parse_args()
    scenario = SCENARIOS[args.scenario]

    if not args.base_fs.is_dir():
        raise RuntimeError(f"missing base fs tree: {args.base_fs}")

    if not args.skip_build:
        build_current_tools()

    out_fs = args.out_fs if args.out_fs is not None else (UDOS_ROOT / "build" / scenario["out_fs_name"])
    project_root = prepare_workspace(args.base_fs, out_fs, scenario["source"])

    actc = run_harness(
        ACTC_PRG,
        project_root,
        "MAIN",
        ACTC_LABELS,
        ["--op-dump-cstr", "target_path:32", "--op-dump-cstr", "content_buffer:256"],
    )
    verify_actc(project_root, actc, scenario["expected_avo"])

    alink = run_harness(
        ALINK_PRG,
        project_root,
        "MAIN",
        ALINK_LABELS,
        ["--op-dump-cstr", "target_path:32", "--op-dump-cstr", "binary_target_path:32", "--op-dump", "content_buffer:80"],
    )
    verify_alink(project_root, alink, scenario["expected_avm"])

    avmrun = run_harness(
        AVMRUN_PRG,
        project_root,
        "BIN/MAIN.AVM",
        AVMRUN_LABELS,
        [],
    )
    verify_avmrun(avmrun, scenario["expected_console"])

    summary = {
        "scenario": args.scenario,
        "workspace": str(project_root),
        "actc_object_path": str(project_root / "obj" / "MAIN.AVO"),
        "alink_image_path": str(project_root / "bin" / "MAIN.AVM"),
        "avmrun_console": avmrun["console"],
    }
    print(json.dumps(summary, indent=2))

    if not args.keep_workspace:
        shutil.rmtree(out_fs, ignore_errors=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
