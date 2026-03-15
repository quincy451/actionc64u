from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
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
            line = line.replace("[", "").replace("](", " ").replace(")", "")
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
        "README.TXT": "# ActionC64U UDOS Workspace\n\nThis workspace is a bridge payload for UDOS. It contains guides, examples, and runtime assets from the bootstrap ActionC64U repo while the UDOS-native Action tools are being built.\n",
        "OPERATOR.TXT": (root / "docs" / "operator_guide.md").read_text(encoding="utf-8"),
        "LANGUAGE.TXT": (root / "docs" / "language_guide.md").read_text(encoding="utf-8"),
        "VMABI.TXT": (root / "docs" / "vm_abi.md").read_text(encoding="utf-8"),
        "UDOSRESM.TXT": (root / "docs" / "udos_resume.md").read_text(encoding="utf-8"),
    }
    for name, text in docs.items():
        if name == "README.TXT":
            out = text.strip() + "\n"
        else:
            out = markdown_to_text(text)
        (docs_dir / name).write_text(out, encoding="ascii", errors="ignore")


def export_examples(root: Path, image_root: Path, src_dir: Path, bin_dir: Path) -> None:
    for source in sorted((root / "examples").glob("*.act")):
        shutil.copy2(source, src_dir / source.name.upper())

    pack_tool = root / "tools" / "avm_pack.py"
    avm_specs = [
        ((root / "examples" / "hello.avm"), "HELLO.AVM"),
    ]
    for existing, out_name in avm_specs:
        shutil.copy2(existing, bin_dir / out_name)
        shutil.copy2(existing, image_root / out_name)

    packed_specs = [
        ((root / "examples" / "udos_hello.avm.txt"), "UDOSHELLO.AVM", 1),
        ((root / "examples" / "udos_flow.avm.txt"), "UDOSFLOW.AVM", 1),
    ]
    for source, out_name, flags in packed_specs:
        built = bin_dir / out_name
        subprocess.run(
            [
                "python3",
                str(root / "tools" / "avm_pack.py"),
                "--text",
                "--flags",
                str(flags),
                str(source),
                "--output",
                str(built),
            ],
            cwd=root,
            check=True,
        )
        shutil.copy2(built, image_root / out_name)

    text_specs = [
        ((root / "examples" / "hello.avm.txt"), "HELLO.AVT", "HELLO.AVM"),
        ((root / "examples" / "reu_runtime.avm.txt"), "REURUN.AVT", "REURUN.AVM"),
        ((root / "examples" / "vmecho.avm.txt"), "VMECHO.AVT", "VMECHO.AVM"),
        ((root / "examples" / "filecopy_runtime.avm.txt"), "FILECOPY.AVT", "FILECOPY.AVM"),
    ]
    for text_path, text_name, bin_name in text_specs:
        shutil.copy2(text_path, bin_dir / text_name)
        subprocess.run(
            [sys.executable, str(pack_tool), str(text_path), "--text", "--output", str(bin_dir / bin_name)],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )


def export_udos_tools(root: Path, image_root: Path, bin_dir: Path) -> None:
    tool_specs = [
        ("build_actdir_udos.sh", "ACTDIR.PRG"),
        ("build_actinfo_udos.sh", "ACTINFO.PRG"),
        ("build_actwrite_udos.sh", "ACTWRITE.PRG"),
        ("build_avminfo_udos.sh", "AVMINFO.PRG"),
        ("build_avmrun_udos.sh", "AVMRUN.PRG"),
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
        shutil.copy2(built, bin_dir / out_name)
        shutil.copy2(built, image_root / out_name)


def export_libs(root: Path, lib_dir: Path) -> None:
    libmods = root / "src" / "tools_cpm" / "libmods"
    (lib_dir / "LIBMODS.DAT").write_text(build_manifest_bundle(libmods), encoding="ascii")
    for manifest in sorted(libmods.glob("*.mod")):
        shutil.copy2(manifest, lib_dir / manifest.name.upper())


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
    export_examples(root, image_root, src_dir, bin_dir)
    if args.build_udos_tools:
        export_udos_tools(root, image_root, bin_dir)
    export_libs(root, lib_dir)

    (image_root / "README.TXT").write_text(
        (
            "ACTIONC64U FOR UDOS\n"
            "\n"
            "DOC contains operator and language guides.\n"
            "SRC contains sample Action source files.\n"
            "BIN contains sample AVM assets.\n"
            "LIB contains the packed bootstrap runtime manifests.\n"
        ),
        encoding="ascii",
    )

    for directory in [docs_dir, src_dir, bin_dir, lib_dir, image_root]:
        write_manifest(directory)

    print(image_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
