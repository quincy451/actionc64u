#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


LINUX_TOOL_NAMES = (
    "actnew",
    "actadd",
    "actwork",
    "actsrc",
    "actfile",
    "actchk",
    "actdir",
    "actcopy",
    "actdel",
    "actmkdir",
    "actrmdir",
    "actmove",
    "actren",
    "actwrite",
    "actinfo",
    "actmon",
    "actdbg",
    "acttree",
    "tree",
    "xcopy",
    "deltree",
    "actedit",
    "act2save",
    "actsave",
    "actc",
    "alink",
)

ACTIVE_EXAMPLES = (
    "dbf1_demo.act",
    "gfx1_demo.act",
    "hello.act",
    "if.act",
    "input1_demo.act",
    "math.act",
    "math1_demo.act",
    "ovl_demo.act",
    "real_cmp.act",
    "real_demo.act",
    "real_math.act",
    "reu_demo.act",
    "sidspr1_demo.act",
)

ACTIVE_SOURCE_LIBRARIES = (
    "dbf1.act",
    "gfx1.act",
    "input1.act",
    "math1.act",
    "sidspr1.act",
)


def copy_named_files(source_dir: Path, target_dir: Path, names: tuple[str, ...]) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        source = source_dir / name
        if not source.is_file():
            raise FileNotFoundError(f"missing active source file: {source}")
        shutil.copy2(source, target_dir / source.name.upper())


def runtime_object_is_placeholder(path: Path) -> bool:
    lines = [line.strip() for line in path.read_text(encoding="ascii").splitlines() if line.strip()]
    if len(lines) < 2 or lines[0].upper() != "OBJ1" or not lines[1].startswith("{"):
        return False
    try:
        record = json.loads(lines[1])
        module = record["module"].encode("ascii")
        payload = bytes.fromhex(record["payload_hex"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeError(f"malformed runtime object: {path}") from error
    return payload == module + b"\0"


def build_linux_tools(root: Path) -> Path:
    result = subprocess.run(
        ["bash", str(root / "tools" / "build_linux_tools.sh")],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout + result.stderr)
    return Path(result.stdout.strip().splitlines()[-1])


def export_linux_tools(root: Path, tools_dir: Path, *, build: bool) -> None:
    source_dir = build_linux_tools(root) if build else root / "build" / "linux_tools"
    if not source_dir.is_dir():
        raise FileNotFoundError(f"missing Linux tools directory: {source_dir}")
    tools_dir.mkdir(parents=True, exist_ok=True)
    for name in LINUX_TOOL_NAMES:
        source = source_dir / name
        if not source.exists():
            raise FileNotFoundError(f"missing Linux tool: {source}")
        target = tools_dir / name
        if target.exists() or target.is_symlink():
            target.unlink()
        if source.is_symlink():
            link_target = source.resolve()
            shutil.copy2(link_target, target)
        else:
            shutil.copy2(source, target)
        target.chmod(target.stat().st_mode | 0o755)


def export_docs(
    docs_dir: Path,
    exported_runtime: list[str],
    skipped_runtime: list[str],
) -> None:
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "README.txt").write_text(
        (
            "ActionC64U Idun/Linux workspace\n"
            "\n"
            "TOOLS contains Linux executables that run on the Idun cartridge's "
            "Raspberry Pi side. SRC contains Action source. OBJ contains compiler "
            "objects. BIN contains generated C64 .PRG files. LIB contains "
            "linkable 6502 runtime modules used by the final .PRG.\n"
            "\n"
            "The exported workspace does not require UDOS. Build-time tools are Linux "
            "processes; generated .PRG files remain Commodore programs.\n"
        ),
        encoding="ascii",
    )
    (docs_dir / "operator.txt").write_text(
        (
            "Default workflow:\n"
            "\n"
            "1. Put Action source under SRC/.\n"
            "2. Run TOOLS/actnew <project> to create a project.\n"
            "3. Run TOOLS/actadd <module> inside a project to add modules.\n"
            "4. Run TOOLS/actwork, TOOLS/actsrc, TOOLS/actfile, and TOOLS/actchk "
            "for project inspection.\n"
            "5. Run TOOLS/actc <module> and TOOLS/alink <module>; ALINK emits "
            "BIN/<module>.PRG for the Commodore. ALINK resolves referenced "
            "native OBJ1 exports across OBJ and LIB even when filenames differ, "
            "selects only each reachable export range, rejects ambiguous "
            "providers, accepts canonical one-character import indexes, and "
            "writes canonical source records to BIN/<module>.DBG.\n"
            "6. Run TOOLS/actedit <module> index, find <text>, or symbols for "
            "SQLite-backed source navigation. Rebuildable editor state lives "
            "under .action/workspace.sqlite3.\n"
            "7. Run TOOLS/actdbg <module> source <address>, line <line>, or "
            "symbols [filter] to inspect linked source maps. break <line>, "
            "breaks, and clear <id> manage prepared breakpoints under "
            ".action/debug.sqlite3. Live C64 control is not active yet.\n"
        ),
        encoding="ascii",
    )
    (docs_dir / "runtime-status.txt").write_text(
        (
            "Standalone link-selected 6502 runtime modules\n"
            "\n"
            + "\n".join(exported_runtime)
            + "\n\nLegacy placeholders not exported\n\n"
            + "\n".join(skipped_runtime)
            + "\n\n"
            "BYTE/CARD/INT/REAL arrays, typed pointers and indirect parameters, "
            "length-prefixed BYTE strings, "
            "static local routine parameters, and BYTE/CARD/INT/REAL user "
            "functions are active compiler forms. Function calls can appear in "
            "expressions; the first parameter/result ABI is not reentrant. "
            "REAL and signed INT source lowering is active for the documented "
            "proof surface. REAL arithmetic uses link-selected IEEE-754 binary32 "
            "helpers, including exceptional-value handling; see the project "
            "REAL32 documentation for the verified behavior. REU BYTE ARRAY "
            "allocation and 8/16-bit peek/poke are active "
            "through direct C64 REU hardware modules. REU free/copy/32-bit "
            "operations remain unavailable. OVERLAY blocks are active as "
            "resident program-owned PRG sections; dynamic load/unload is not "
            "active. DBF1 compiler lowering and link-selected DBF modules are "
            "active. DBF files are staged in one allocator-owned REU block and "
            "loaded/saved through standalone C64 KERNAL adapters; DBF target "
            "execution remains hardware-unverified.\n"
        ),
        encoding="ascii",
    )


def export_runtime_modules(root: Path, lib_dir: Path) -> tuple[list[str], list[str]]:
    source_dir = root / "src" / "runtime" / "modules"
    exported: list[str] = []
    skipped: list[str] = []
    lib_dir.mkdir(parents=True, exist_ok=True)
    for source in sorted(source_dir.glob("*.obj")):
        if runtime_object_is_placeholder(source):
            skipped.append(source.name.upper())
            continue
        target_name = source.name.upper()
        shutil.copy2(source, lib_dir / target_name)
        exported.append(target_name)
    return exported, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export an Idun/Linux ActionC64U workspace")
    parser.add_argument(
        "--output",
        default="build/idun-action",
        help="output directory for the Linux-side Action workspace",
    )
    parser.add_argument(
        "--no-build-tools",
        action="store_true",
        help="copy existing build/linux_tools outputs instead of rebuilding",
    )
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    out_root = Path(args.output).resolve()
    if out_root.exists():
        shutil.rmtree(out_root)

    tools_dir = out_root / "TOOLS"
    src_dir = out_root / "SRC"
    obj_dir = out_root / "OBJ"
    bin_dir = out_root / "BIN"
    lib_dir = out_root / "LIB"
    docs_dir = out_root / "DOC"

    for directory in (src_dir, obj_dir, bin_dir, lib_dir):
        directory.mkdir(parents=True, exist_ok=True)

    export_linux_tools(root, tools_dir, build=not args.no_build_tools)
    copy_named_files(root / "examples", src_dir, ACTIVE_EXAMPLES)
    copy_named_files(root / "lib", lib_dir, ACTIVE_SOURCE_LIBRARIES)
    exported_runtime, skipped_runtime = export_runtime_modules(root, lib_dir)
    export_docs(docs_dir, exported_runtime, skipped_runtime)

    print(out_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
