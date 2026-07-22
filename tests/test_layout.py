from pathlib import Path
import re
import unittest


class TestRepoLayout(unittest.TestCase):
    def test_repo_layout_smoke(self) -> None:
        root = Path(__file__).resolve().parents[1]

        required = [
            "README.md",
            "LICENSE",
            ".gitignore",
            "AGENTS.md",
            "docs/inspiration/action.pdf",
            "docs/setup_wsl.md",
            "docs/architecture.md",
            "docs/active_direction.md",
            "docs/new_math_func.txt",
            "docs/new_gfx_func.txt",
            "src/runtime",
            "src/runtime/libmods",
            "src/runtime/libmods/libpstr.mod",
            "src/runtime/libmods/libplin.mod",
            "src/runtime/modules",
            "src/runtime/udos_modules",
            "src/tools_udos/actc",
            "src/tools_udos/alink/alink.asm",
            "src/tools_udos/alink/direct_prg.inc",
            "src/tools_udos/actdbg/actdbg.asm",
            "src/tools_udos/actdbg/actdbg_native_exec.inc",
            "src/tools_udos/actdbg/actdbg_overlay_exec.asm",
            "src/tools_udos/actdbg/actdbg_overlay_optional_ui.asm",
            "src/tools_udos/common",
            "tools/object_format.py",
            "tools/generate_input_runtime.py",
            "tools/vice_harness.py",
            "tools/export_udos_workspace.py",
            "tools/build_actc_udos.sh",
            "tools/build_alink_udos.sh",
            "tools/build_actdbg_udos.sh",
            "tools/build_actdbg_overlay_exec.sh",
            "tools/build_actdbg_overlay_optional_ui.sh",
            "tools/build_tool_abi_harness.sh",
            "tools/generate_udos_service_inc.py",
            "third_party/lib6502/6502data.h",
            "third_party/lib6502/COPYING.lib6502",
            "third_party/lib6502/lib6502.c",
            "third_party/lib6502/lib6502.h",
            "pytest/__main__.py",
            "examples/hello.act",
            "examples/if.act",
            "examples/input1_demo.act",
            "examples/math.act",
            "examples/math1_demo.act",
            "examples/real_demo.act",
            "examples/reu_demo.act",
            "examples/ovl_demo.act",
            "lib/input1.act",
            "lib/math1.act",
            "tests/test_actc_capacity.py",
            "tests/test_actc_overlay.py",
            "tests/test_actdbg.py",
            "tests/test_layout.py",
            "tests/test_udos_workspace_export.py",
        ]

        legacy_ext = "a" + "vm"
        legacy_tool = legacy_ext
        removed_legacy_paths = [
            "src/vm",
            f"src/tools_udos/{legacy_tool}run",
            f"src/tools_udos/{legacy_tool}info",
            "src/tools_cpm",
            "src/tools_cpm/actc",
            "src/tools_cpm/alink",
            "src/tools_cpm/actmon",
            "src/tools_cpm/hello",
            "docs/cpm65_abi.md",
            "docs/cpmemu.md",
            "tools/actionc64u_compile.py",
            "tools/actionc64u_link.py",
            f"tools/{legacy_tool}_pack.py",
            "tools/build_actc.sh",
            "tools/build_cpm65_notes.sh",
            "tools/build_hello.sh",
            "tools/build_vmhello.sh",
            "tools/build_vmrun.sh",
            "tools/build_alink.sh",
            "tools/build_actmon.sh",
            "tools/cpmemu_runner.py",
            "tools/find_llvm_mos.sh",
            "tools/install_to_image.py",
            "tools/verify_release.py",
            f"examples/hello.{legacy_ext}",
            f"examples/hello.{legacy_ext}.txt",
            f"examples/reu_runtime.{legacy_ext}.txt",
        ]

        missing = [path for path in required if not (root / path).exists()]
        present_removed = [path for path in removed_legacy_paths if (root / path).exists()]
        self.assertFalse(missing, f"Missing required project paths: {missing}")
        self.assertFalse(present_removed, f"Removed VM-era paths are still present: {present_removed}")

    def test_imported_math_and_graphics_goal_contracts_are_recorded(self) -> None:
        root = Path(__file__).resolve().parents[1]
        math_goal = (root / "docs" / "new_math_func.txt").read_text(encoding="ascii")
        gfx_goal = (root / "docs" / "new_gfx_func.txt").read_text(encoding="ascii")

        for signature in (
            "REAL FUNC FExp(REAL value)",
            "REAL FUNC FATan2(REAL y,x)",
            "REAL FUNC FHypot(REAL x,y)",
            "REAL FUNC FATanh(REAL value)",
        ):
            self.assertIn(signature, math_goal)
        self.assertIn("no UDOS calls or resident service required", math_goal)
        self.assertIn("round-to-nearest/ties-to-even", math_goal)

        for declaration in ("SPRITE", "MSPRITE", "BITMAP", "MBITMAP"):
            self.assertRegex(gfx_goal, rf"(?m)^{declaration}\s+\w+=RESOURCE")
        self.assertIn("ASP1 sprite file", gfx_goal)
        self.assertIn("ABM1 bitmap file", gfx_goal)
        self.assertIn("PROC SpritePlace(BYTE slot,CARD asset,CARD x,BYTE y)", gfx_goal)
        self.assertIn("None of this functionality depends on UDOS", gfx_goal)

    def test_idun_parity_plan_separates_shared_features_from_os_services(self) -> None:
        root = Path(__file__).resolve().parents[1]
        parity = (root / "docs" / "idun_feature_parity.md").read_text(encoding="ascii")
        flat_parity = " ".join(parity.split())

        self.assertIn("## Executive Status", parity)
        self.assertIn("five portable groups", parity)
        self.assertIn("Passes 6 and 7 collect\nand preallocate bounded REAL operands", parity)
        self.assertIn("Pass L now consumes that stream", flat_parity)
        self.assertIn("intentional Idun mechanisms", parity)
        self.assertIn("Full MATH1 source library", parity)
        self.assertIn("Native implementation gap", parity)
        self.assertIn("Linux/APK deployment", parity)
        self.assertIn("Idun-specific", parity)
        self.assertIn("UDOS disk/DNP release", parity)
        self.assertIn("UDOS-specific", parity)
        self.assertIn("The constant foundation is complete", parity)
        self.assertIn("round-to-nearest, ties-to-even", parity)
        self.assertIn("Dedicated pass K", parity)
        self.assertIn("inventories are 1,361 broad direct-PRG shapes", flat_parity)
        self.assertIn("193 non-runtime source-backed object-emission shapes", flat_parity)
        self.assertIn("298 compiled-runtime", parity)
        self.assertIn("fifteen link-selected callable builtins", parity)
        self.assertIn("remaining 28 MATH1 routines", parity)
        self.assertIn("RT_F_FLOOR.OBJ", parity)
        self.assertIn("RT_F_ROUND.OBJ", parity)
        self.assertIn("RT_F_FRAC.OBJ", parity)
        self.assertIn("RT_F_MOD.OBJ", parity)
        self.assertIn("RT_F_HYPOT.OBJ", parity)
        self.assertIn("851 native ActionC64U unittests", parity)
        self.assertIn("153 Idun/Alpine unittests", parity)
        self.assertIn("138 Idun ASan/UBSan tests", parity)
        self.assertIn("21 Idun direct-PRG tests", parity)
        self.assertIn("242-test overlay suite and 198-test source-cache suite", parity)
        self.assertIn("Generalize native REAL", parity)
        self.assertIn("MATH1 reachable-only packaging", parity)
        self.assertIn("call-graph pruning", parity)
        self.assertIn("Pass L handles bounded nested straight-line trees", flat_parity)
        self.assertIn("real_two_function_nested_postfix.act", parity)
        self.assertIn("real_function_call_chain_postfix.act", parity)
        self.assertIn("real_function_nested_local_call_postfix.act", parity)
        self.assertIn("real_function_user_call_arguments_postfix.act", parity)
        self.assertIn("real_function_forward_frame_postfix.act", parity)
        self.assertIn("real_function_if_else_postfix.act", parity)
        self.assertIn("real_function_sequential_if_else_postfix.act", parity)
        self.assertIn("real_function_nested_if_else_postfix.act", parity)
        self.assertIn("real_function_four_sequential_if_postfix.act", parity)
        self.assertIn("real_function_four_deep_if_postfix.act", parity)
        self.assertIn("real_function_early_return_if_postfix.act", parity)
        self.assertIn("real_function_early_return_four_deep_postfix.act", parity)
        self.assertIn("real_function_loops_postfix.act", parity)
        self.assertIn("real_function_loop_exit_postfix.act", parity)
        self.assertIn("real_function_for_postfix.act", parity)
        self.assertIn("Pass L is 6,124 bytes with 2,068 bytes free", flat_parity)
        self.assertIn("pass M is 6,998 bytes with 1,194 bytes free", flat_parity)
        self.assertIn("pass N is 7,120 bytes with 1,072 bytes free", flat_parity)
        self.assertIn("pass O is 7,123 bytes with 1,069 bytes free", flat_parity)
        self.assertIn("pass-P image is 7,147 bytes with 1,045 bytes free", flat_parity)
        self.assertIn("pass-Q image is 7,151 bytes with 1,041 bytes free", flat_parity)
        self.assertIn("Pass R is 7,334 bytes with 858 bytes free", flat_parity)
        self.assertIn("Pass S is 7,828 bytes with 364 bytes free", flat_parity)
        self.assertIn("complete ACTC compiler, passes 0 through S", parity)
        self.assertIn("The portable products are therefore not yet at full feature parity", parity)
        self.assertNotIn("binary32 folding remains", parity)
        self.assertIn(
            "must not reintroduce a runtime runner",
            " ".join(parity.split()),
        )

    def test_runtime_machine_obj_export_sizes_match_machine_records(self) -> None:
        root = Path(__file__).resolve().parents[1]
        runtime_root = root / "src" / "runtime" / "udos_modules"
        mismatches = []

        for path in sorted(runtime_root.glob("*.obj")):
            lines = path.read_text(encoding="ascii").splitlines()
            body_lines = [line for line in lines if line.startswith("b ")]
            if not any("M" in line[2:] for line in body_lines):
                continue

            export_lines = [line for line in lines if line.startswith("x ")]
            machine_lines = [line for line in lines if line.startswith("m ")]
            self.assertGreaterEqual(len(export_lines), 1, f"{path} must have an export line")
            self.assertGreaterEqual(len(machine_lines), 1, f"{path} must have at least one machine record")

            machine_hex = "".join("".join(line.split()[1:]) for line in machine_lines)
            self.assertEqual(len(machine_hex) % 2, 0, f"{path} has an incomplete machine byte")
            self.assertRegex(machine_hex, r"^[0-9A-Fa-f]*$", f"{path} has non-hex machine bytes")
            machine_bytes = [machine_hex[index : index + 2] for index in range(0, len(machine_hex), 2)]
            for byte_text in machine_bytes:
                value = int(byte_text, 16)
                self.assertGreaterEqual(value, 0, f"{path} has invalid byte {byte_text}")
                self.assertLessEqual(value, 0xFF, f"{path} has invalid byte {byte_text}")
            actual_size = len(machine_bytes)

            exports = []
            for line in export_lines:
                parts = line.split()
                self.assertEqual(len(parts), 4, f"{path} has malformed export: {line}")
                name, offset, size = parts[1], int(parts[2]), int(parts[3])
                self.assertGreater(size, 0, f"{path} has empty export {name}")
                self.assertGreaterEqual(offset, 0, f"{path} has negative export offset {name}")
                self.assertLessEqual(
                    offset + size,
                    actual_size,
                    f"{path} export {name} exceeds its machine records",
                )
                exports.append((name.lower(), offset, size))

            canonical = [export for export in exports if export[0] == path.stem.lower()]
            self.assertEqual(
                len(canonical),
                1,
                f"{path} must have one canonical export named {path.stem}",
            )
            _, declared_offset, declared_size = canonical[0]
            self.assertEqual(declared_offset, 0, f"{path} canonical export must start at zero")
            if actual_size != declared_size:
                mismatches.append(f"{path.name}: export={declared_size} machine={actual_size}")

        self.assertFalse(mismatches, "Runtime OBJ machine sizes mismatch: " + ", ".join(mismatches))

    def test_runtime_modules_use_object_code_bodies(self) -> None:
        root = Path(__file__).resolve().parents[1]
        runtime_root = root / "src" / "runtime" / "udos_modules"
        offenders = []

        for path in sorted(runtime_root.glob("*.obj")):
            lines = path.read_text(encoding="ascii").splitlines()
            for line in lines:
                if not line.startswith("b "):
                    continue
                body = line[2:]
                if not re.fullmatch(r"(?:u[0-9]+)*M", body):
                    offenders.append(f"{path.name}: {line}")

        self.assertFalse(offenders, "Runtime OBJ modules must use object-code bodies: " + ", ".join(offenders))

    def test_runtime_object_symbols_fit_alink_limit(self) -> None:
        root = Path(__file__).resolve().parents[1]
        runtime_root = root / "src" / "runtime" / "udos_modules"
        offenders = []

        for path in sorted(runtime_root.glob("*.obj")):
            for line in path.read_text(encoding="ascii").splitlines():
                if not line.startswith(("x ", "u ")):
                    continue
                symbol = line.split()[1]
                if len(symbol) > 23:
                    offenders.append(f"{path.name}: {symbol}")

        self.assertFalse(
            offenders,
            "Runtime OBJ symbols exceed ALINK's 23-character limit: "
            + ", ".join(offenders),
        )

    def test_runtime_modules_are_documented(self) -> None:
        root = Path(__file__).resolve().parents[1]
        runtime_root = root / "src" / "runtime" / "udos_modules"
        readme = (runtime_root / "README.md").read_text(encoding="utf-8").lower()
        missing = [
            path.name
            for path in sorted(runtime_root.glob("rt_*.obj"))
            if f"`{path.name.lower()}`" not in readme
        ]

        self.assertFalse(missing, "Runtime OBJ modules missing from README.md: " + ", ".join(missing))

    def test_real32_docs_use_linker_runtime_symbol_names(self) -> None:
        root = Path(__file__).resolve().parents[1]
        docs = (root / "docs" / "real32.md").read_text(encoding="utf-8")
        expected = {
            "rt_f_add",
            "rt_f_sub",
            "rt_f_mul",
            "rt_f_div",
            "rt_f_cmp",
            "rt_f_sign",
            "rt_f_trunc",
            "rt_f_floor",
            "rt_f_ceil",
            "rt_f_round",
            "rt_f_frac",
            "rt_f_mod",
            "rt_f_hypot",
            "rt_f_min",
            "rt_f_max",
            "rt_f_clamp",
            "rt_f_abs",
            "rt_f_sqrt",
            "rt_i_to_f",
            "rt_s_to_f",
            "rt_f_to_i",
            "rt_print_f",
        }

        dotted = sorted(set(re.findall(r"`(rt\.[A-Za-z0-9_]+)`", docs)))
        documented = set(re.findall(r"`(rt_[A-Za-z0-9_]+)`", docs))
        runtime_modules = {
            path.stem for path in (root / "src" / "runtime" / "udos_modules").glob("rt_*.obj")
        }

        self.assertFalse(
            dotted,
            "REAL32 docs must use linker rt_* symbols, not dotted names: " + ", ".join(dotted),
        )
        self.assertTrue(
            expected <= documented,
            "REAL32 docs missing helper symbols: " + ", ".join(sorted(expected - documented)),
        )
        self.assertTrue(
            expected <= runtime_modules,
            "REAL32 documented helpers missing runtime OBJ modules: "
            + ", ".join(sorted(expected - runtime_modules)),
        )

    def test_sid_sprite_active_docs_are_c64_native(self) -> None:
        root = Path(__file__).resolve().parents[1]
        active_docs = [
            root / "docs" / "sidspr1_bindings_draft.act",
            root / "docs" / "sid_and_sprite_ideas.txt",
        ]
        rejected_tokens = ["Sound(", "SndRst", "Sound/SndRst"]
        offenders = []

        for path in active_docs:
            text = path.read_text(encoding="utf-8")
            for token in rejected_tokens:
                if token in text:
                    offenders.append(f"{path.relative_to(root)}: {token}")

        self.assertFalse(
            offenders,
            "Active C64 SID/sprite docs must not reintroduce Atari-style sound API names: "
            + ", ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
