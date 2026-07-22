from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path


def markdown_to_text(markdown: str) -> str:
    lines: list[str] = []
    in_code = False
    for raw in markdown.replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if not in_code:
            while line.startswith("#"):
                line = line[1:]
            line = line.lstrip()
            line = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 \2", line)
            line = line.replace("`", "")
        lines.append(line)
    text = "\n".join(lines).strip() + "\n"
    return text


def write_manifest(directory: Path) -> None:
    entries: list[str] = []
    for child in sorted(directory.iterdir(), key=lambda item: (item.is_file(), item.name.upper())):
        if child.name.upper() == "UDOSDIR.TXT":
            continue
        prefix = "D" if child.is_dir() else "F"
        entries.append(f"{prefix} {child.name.upper()}")
    (directory / "UDOSDIR.TXT").write_text("\n".join(entries) + ("\n" if entries else ""), encoding="ascii")


def build_manifest_bundle(source_dir: Path) -> str:
    parts: list[str] = []
    for manifest in sorted(source_dir.glob("*.mod")):
        text = manifest.read_text(encoding="ascii").replace("\r\n", "\n").strip()
        parts.append(f"FILE {manifest.name.lower()}\n{text}\nEND\n")
    return "\n".join(parts)


def export_docs(root: Path, docs_dir: Path) -> None:
    docs = {
        "README.TXT": (
            "# ActionC64U UDOS Workspace\n\n"
            "This workspace contains the UDOS-native Action tools, sample Action source, "
            "and linkable runtime modules. The default build path is ACTC.PRG -> "
            "ALINK.PRG -> BIN/<module>.PRG.\n"
        ),
        "OPERATOR.TXT": (
            "# ActionC64U UDOS Operator Guide\n\n"
            "Default workflow:\n\n"
            "1. Keep Action source under SRC/.\n"
            "2. Run ACTC.PRG <module> to build OBJ/<module>.OBJ.\n"
            "3. Run ALINK.PRG <module> to link BIN/<module>.PRG and .DBG.\n"
            "4. Run the linked PRG directly from BIN/.\n"
            "5. For source debugging, run ACTDBG.PRG <module>.\n"
        ),
        "LANGUAGE.TXT": (
            "# ActionC64U Source Notes\n\n"
            "Action source files use the .ACT extension. Project manifests use "
            "ACTION.PROJ and list the main source file. Linkable runtime modules "
            "are selected by ALINK from the symbols required by the compiled objects.\n\n"
            "DOC/INPUT1.TXT describes the current C64 joystick and mouse helper "
            "API. DOC/DBF1.TXT describes the current DBF helper API. "
            "LIB/DBF1.ACT, LIB/GFX1.ACT, LIB/INPUT1.ACT, "
            "LIB/MATH1.ACT, and LIB/SIDSPR1.ACT provide the matching Action "
            "declarations for DBF, graphics, input, REAL math, SID, and sprite helpers. ACTC "
            "recognizes those helper names directly and ALINK links only the "
            "referenced RT_*.OBJ modules.\n"
        ),
    }
    input1_doc = root / "docs" / "input1.md"
    if input1_doc.is_file():
        docs["INPUT1.TXT"] = input1_doc.read_text(encoding="utf-8")
    dbf1_doc = root / "docs" / "dbf1.md"
    if dbf1_doc.is_file():
        docs["DBF1.TXT"] = dbf1_doc.read_text(encoding="utf-8")
    debugger_doc = root / "docs" / "source_debugger_roadmap.md"
    if debugger_doc.is_file():
        docs["DEBUGGER.TXT"] = debugger_doc.read_text(encoding="utf-8")
    for name, text in docs.items():
        if name == "README.TXT":
            out = text.strip() + "\n"
        else:
            out = markdown_to_text(text)
        (docs_dir / name).write_text(out, encoding="ascii", errors="ignore")


def export_examples(root: Path, src_dir: Path) -> None:
    for source in sorted((root / "examples").glob("*.act")):
        shutil.copy2(source, src_dir / source.name.upper())


def export_library_sources(root: Path, lib_dir: Path) -> None:
    source_root = root / "lib"
    if not source_root.is_dir():
        return
    for source in sorted(source_root.glob("*.act")):
        shutil.copy2(source, lib_dir / source.name.upper())


def export_udos_tools(root: Path, image_root: Path, bin_dir: Path) -> None:
    aliases = {
        "ACT2SAVE.PRG": ["ACTSAVE.PRG"],
    }
    tool_specs = [
        ("build_actadd_udos.sh", "ACTADD.PRG"),
        ("build_act2save_udos.sh", "ACT2SAVE.PRG"),
        ("build_actc_udos.sh", "ACTC.PRG"),
        ("build_actc_overlay_noop.sh", "ACTC_OVL0.BIN"),
        ("build_actc_overlay_source_header.sh", "ACTC_OVL1.BIN"),
        ("build_actc_overlay_decl_counts.sh", "ACTC_OVL2.BIN"),
        ("build_actc_overlay_payload_layout.sh", "ACTC_OVL3.BIN"),
        ("build_actc_overlay_runtime_imports.sh", "ACTC_OVL4.BIN"),
        ("build_actc_overlay_emit_object.sh", "ACTC_OVL5.BIN"),
        ("build_actc_overlay_body_collect.sh", "ACTC_OVL6.BIN"),
        ("build_actc_overlay_body_preallocate.sh", "ACTC_OVL7.BIN"),
        ("build_actc_overlay_emit_native_object.sh", "ACTC_OVL8.BIN"),
        ("build_actc_overlay_emit_native_local_object.sh", "ACTC_OVL9.BIN"),
        ("build_actc_overlay_emit_native_real_object.sh", "ACTC_OVLA.BIN"),
        ("build_actc_overlay_emit_native_real_control_object.sh", "ACTC_OVLB.BIN"),
        ("build_actc_overlay_emit_native_real_while_object.sh", "ACTC_OVLC.BIN"),
        ("build_actc_overlay_emit_native_runtime_condition_object.sh", "ACTC_OVLD.BIN"),
        ("build_actc_overlay_emit_native_runtime_sequence_object.sh", "ACTC_OVLE.BIN"),
        ("build_actc_overlay_emit_native_runtime_nested_object.sh", "ACTC_OVLF.BIN"),
        ("build_actc_overlay_emit_native_local_runtime_object.sh", "ACTC_OVLG.BIN"),
        ("build_actc_overlay_emit_native_local_mixed_object.sh", "ACTC_OVLH.BIN"),
        ("build_actc_overlay_preprocess.sh", "ACTC_OVLI.BIN"),
        ("build_actc_overlay_emit_native_fixed_object.sh", "ACTC_OVLJ.BIN"),
        ("build_actc_overlay_emit_native_real_function_object.sh", "ACTC_OVLK.BIN"),
        ("build_actc_overlay_emit_native_real_postfix_object.sh", "ACTC_OVLL.BIN"),
        ("build_actc_overlay_emit_native_real_postfix_control_object.sh", "ACTC_OVLM.BIN"),
        ("build_actc_overlay_emit_native_real_postfix_multi_control_object.sh", "ACTC_OVLN.BIN"),
        ("build_actc_overlay_emit_native_real_postfix_extended_control_object.sh", "ACTC_OVLO.BIN"),
        ("build_actc_overlay_emit_native_real_postfix_early_return_object.sh", "ACTC_OVLP.BIN"),
        ("build_actc_overlay_emit_native_real_postfix_loop_object.sh", "ACTC_OVLQ.BIN"),
        ("build_actc_overlay_emit_native_real_postfix_loop_exit_object.sh", "ACTC_OVLR.BIN"),
        ("build_actc_overlay_emit_native_real_postfix_for_object.sh", "ACTC_OVLS.BIN"),
        ("build_alink_udos.sh", "ALINK.PRG"),
        ("build_actdbg_udos.sh", "ACTDBG.PRG"),
        ("build_actdbg_overlay_optional_ui.sh", "ACTDBG_OVL1.BIN"),
        ("build_actdbg_overlay_exec.sh", "ACTDBG_OVL2.BIN"),
        ("build_actchk_udos.sh", "ACTCHK.PRG"),
        ("build_actdir_udos.sh", "ACTDIR.PRG"),
        ("build_acttree_udos.sh", "TREE.OVL"),
        ("build_xcopy_udos.sh", "XCOPY.OVL"),
        ("build_deltree_udos.sh", "DELTREE.OVL"),
        ("build_actmon_udos.sh", "ACTMON.PRG"),
        ("build_actfile_udos.sh", "ACTFILE.PRG"),
        ("build_actinfo_udos.sh", "ACTINFO.PRG"),
        ("build_actnew_udos.sh", "ACTNEW.PRG"),
        ("build_actsrc_udos.sh", "ACTSRC.PRG"),
        ("build_actwork_udos.sh", "ACTWORK.PRG"),
        ("build_actcopy_udos.sh", "ACTCOPY.PRG"),
        ("build_actdel_udos.sh", "ACTDEL.PRG"),
        ("build_actedit_udos.sh", "ACTEDIT.PRG"),
        ("build_actedit_overlay_mutation.sh", "ACTEDIT_OVL1.BIN"),
        ("build_actmkdir_udos.sh", "ACTMKDIR.PRG"),
        ("build_actren_udos.sh", "ACTMOVE.PRG"),
        ("build_actrmdir_udos.sh", "ACTRMDIR.PRG"),
        ("build_actwrite_udos.sh", "ACTWRITE.PRG"),
    ]
    for script_name, out_name in tool_specs:
        build_tool = root / "tools" / script_name
        result = subprocess.run(
            ["bash", str(build_tool)],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        built = Path(result.stdout.strip().splitlines()[-1])
        shutil.copy2(built, image_root / out_name)
        for alias in aliases.get(out_name, []):
            shutil.copy2(built, image_root / alias)
        if out_name == "ACTWRITE.PRG":
            shutil.copy2(built, image_root / "W.PRG")

    (image_root / "ACTFLOW.BAT").write_text(
        "\n".join(
            [
                "ACTWRITE OUT.TXT",
                "ACTCOPY OUT.TXT COPY.TXT",
                "ACTMOVE COPY.TXT NEXT.TXT",
                "ACTDEL NEXT.TXT",
                "ECHO ACTFLOW OK",
                "",
            ]
        ),
        encoding="ascii",
    )
    (image_root / "PROJECT.TXT").write_text(
        (
            "ACTION PROJECT READY\n"
            "\n"
            "SRC contains Action source.\n"
            "BIN contains build outputs.\n"
            "OBJ contains intermediate artifacts.\n"
        ),
        encoding="ascii",
    )
    (image_root / "MAIN.ACT").write_text(
        "PROC MAIN()\nENDPROC\n",
        encoding="ascii",
    )
    (image_root / "APROJ.TXT").write_text(
        "ACTION PROJECT\nMAIN.ACT\n",
        encoding="ascii",
    )
    (image_root / "ACTNEW.BAT").write_text(
        "\n".join(
            [
                "MD %1",
                "CD %1",
                "MD SRC",
                "MD BIN",
                "MD OBJ",
                "COPY /APROJ.TXT ACTION.PROJ",
                "COPY /PROJECT.TXT README.TXT",
                "COPY /MAIN.ACT SRC/MAIN.ACT",
                "ECHO ACTNEW OK",
                "",
            ]
        ),
        encoding="ascii",
    )


def export_libs(root: Path, lib_dir: Path) -> None:
    libmods = root / "src" / "runtime" / "libmods"
    runtime_modules = root / "src" / "runtime" / "modules"
    udos_runtime_modules = root / "src" / "runtime" / "udos_modules"
    (lib_dir / "LIBMODS.DAT").write_text(build_manifest_bundle(libmods), encoding="ascii")
    for manifest in sorted(libmods.glob("*.mod")):
        shutil.copy2(manifest, lib_dir / manifest.name.upper())
    for obj in sorted(runtime_modules.glob("*.obj")):
        shutil.copy2(obj, lib_dir / obj.name.upper())
    if udos_runtime_modules.is_dir():
        for obj in sorted(udos_runtime_modules.glob("*.obj")):
            shutil.copy2(obj, lib_dir / obj.name.upper())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export a UDOS-compatible ActionC64U workspace tree")
    parser.add_argument(
        "--output",
        default="build/udos-action-fs",
        help="output directory that will receive IMAGES/ACTION.DNP/...",
    )
    parser.add_argument(
        "--build-udos-tools",
        action="store_true",
        help="build and export UDOS-native external tool proofs when prerequisites are available",
    )
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    out_root = Path(args.output).resolve()
    image_root = out_root / "IMAGES" / "ACTION.DNP"
    docs_dir = image_root / "DOC"
    src_dir = image_root / "SRC"
    bin_dir = image_root / "BIN"
    lib_dir = image_root / "LIB"

    if out_root.exists():
        shutil.rmtree(out_root)

    for directory in [docs_dir, src_dir, bin_dir, lib_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    export_docs(root, docs_dir)
    export_examples(root, src_dir)
    if args.build_udos_tools:
        export_udos_tools(root, image_root, bin_dir)
    export_libs(root, lib_dir)
    export_library_sources(root, lib_dir)

    (image_root / "README.TXT").write_text(
        (
            "ACTIONC64U FOR UDOS\n"
            "\n"
            "DOC contains operator and language guides.\n"
            "SRC contains sample Action source files.\n"
            "BIN contains generated native build outputs.\n"
            "LIB contains packed runtime manifests and linkable modules.\n"
        ),
        encoding="ascii",
    )

    for directory in [docs_dir, src_dir, bin_dir, lib_dir, image_root]:
        write_manifest(directory)

    print(image_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
