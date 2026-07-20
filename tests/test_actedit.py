from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import unittest

import sys


class TestActedit(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(self.root / "tools"))
        from vice_harness import screen_ram_to_text  # type: ignore

        self.screen_ram_to_text = screen_ram_to_text
        self.build_dir = self.root / "build" / "udos_tools"

    def require_toolchain(self) -> None:
        for tool in ("cc", "ca65", "ld65", "make"):
            if shutil.which(tool) is None:
                self.skipTest(f"{tool} not found")

    def run_checked(self, cmd: list[str]) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            cmd,
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return result

    def build_tools(self) -> None:
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actedit_udos.sh")])

    def make_workspace(self, tmpdir: str, source_text: str) -> Path:
        workspace = Path(tmpdir) / "ws"
        (workspace / "src").mkdir(parents=True)
        (workspace / "bin").mkdir()
        (workspace / "src" / "main.act").write_text(source_text, encoding="ascii")
        return workspace

    def run_actedit(
        self,
        workspace: Path,
        cmdline: str,
        *,
        key_bytes: list[int],
        max_steps: int = 1_500_000,
        screen_code_cmdline: bool = False,
        prg_path: Path | None = None,
    ) -> dict:
        if prg_path is None:
            prg_path = self.build_dir / "ACTEDIT.PRG"
        cmd = [
            str(self.build_dir / "tool_abi_harness"),
            "--prg",
            str(prg_path),
            "--workspace",
            str(workspace),
            "--cmdline",
            cmdline,
            "--services-inc",
            str(self.build_dir / "udos_services.inc"),
            "--labels",
            str(self.build_dir / "actedit.current.labels"),
            "--poke-byte",
            "actedit_test_mode=1",
            "--poke-byte",
            f"actedit_test_key_count={len(key_bytes)}",
            "--dump",
            "0x0400:1000",
            "--dump-cstr",
            "actedit_source_path:128",
            "--dump",
            "actedit_current_line_lo:1",
            "--dump",
            "actedit_current_line_hi:1",
            "--dump",
            "actedit_left_col:1",
            "--dump",
            "actedit_cursor_col:1",
            "--dump",
            "actedit_dirty:1",
            "--dump",
            "actedit_source_stage_len_bank:1",
            "--dump",
            "actedit_source_line_count_lo:2",
            "--dump",
            "actedit_source_line_index_ready:1",
            "--dump",
            "actedit_logical_line_count_lo:2",
            "--dump",
            "actedit_logical_line_index_ready:1",
            "--dump",
            "actedit_piece_rebuild_count:1",
            "--dump",
            "actedit_direct_patch_count:1",
            "--dump",
            "actedit_direct_insert_count:1",
            "--dump",
            "actedit_direct_remove_count:1",
            "--dump",
            "actedit_direct_insert_update_count:1",
            "--dump",
            "actedit_logical_index_suffix_count:1",
            "--dump",
            "actedit_mutation_overlay_load_count:1",
            "--dump",
            "actedit_mutation_overlay_fail_count:1",
            "--max-steps",
            str(max_steps),
        ]
        if screen_code_cmdline:
            cmd.append("--cmdline-screen-code")
        for index, value in enumerate(key_bytes):
            cmd.extend(["--poke-byte", f"actedit_test_key{index}=0x{value:02X}"])
        result = self.run_checked(cmd)
        summary = json.loads(result.stdout)
        self.assertTrue(summary["exited"], msg=result.stdout)
        self.assertFalse(summary["hit_limit"], msg=result.stdout)
        self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
        return summary

    def test_actedit_builds(self) -> None:
        self.require_toolchain()
        result = self.run_checked([str(self.root / "tools" / "build_actedit_udos.sh")])
        built = Path(result.stdout.strip().splitlines()[-1])
        labels = self.build_dir / "actedit.current.labels"
        overlay = self.build_dir / "ACTEDIT_OVL1.BIN"
        self.assertTrue(built.is_file())
        self.assertGreater(built.stat().st_size, 2)
        self.assertTrue(labels.is_file())
        self.assertIn("actedit_source_path", labels.read_text(encoding="ascii"))
        overlay_data = overlay.read_bytes()
        self.assertEqual(overlay_data[:5], b"AEOV\x02")
        self.assertEqual(int.from_bytes(overlay_data[5:7], "little"), 0xA000)
        self.assertEqual(int.from_bytes(overlay_data[7:9], "little"), 0xA00D)
        self.assertEqual(int.from_bytes(overlay_data[9:11], "little"), len(overlay_data))

    def test_exit_clears_editor_screen_before_returning_to_udos(self) -> None:
        source = (self.root / "src" / "tools_udos" / "actedit" / "actedit.asm").read_text()
        exit_path = source.split("exit_ok:", 1)[1].split("clear_state:", 1)[0]
        self.assertIn("lda actedit_test_mode\n    bne :+", exit_path)
        self.assertIn("lda #KEY_CLRHOME\n    jsr CHROUT", exit_path)
        self.assertLess(exit_path.index("jsr CHROUT"), exit_path.index("jmp svc_program_exit"))

    def test_actedit_compile_build_and_debug_keys_queue_direct_tools(self) -> None:
        self.require_toolchain()
        self.build_tools()

        cases = (
            ("SRC/MAIN.ACT", 0x0F, "ACTC MAIN;"),
            ("MAIN", 0x02, "ACTC MAIN,"),
            ("MAIN", 0x04, "ACTC MAIN:"),
        )
        for cmdline, key, expected_command in cases:
            with self.subTest(command=expected_command), tempfile.TemporaryDirectory() as tmpdir:
                source = 'MODULE MAIN\rPROC MAIN()\rPrintE("OK")\rRETURN\r'
                workspace = self.make_workspace(tmpdir, source)
                summary = self.run_actedit(workspace, cmdline, key_bytes=[key])

                self.assertTrue(summary["chain_requested"], msg=summary)
                self.assertEqual(summary["chain_command"], expected_command, msg=summary)
                self.assertEqual(
                    (workspace / "src" / "main.act").read_bytes(),
                    source.encode("ascii"),
                )

    def test_actedit_loads_module_source_and_quits(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                'PROC MAIN()\rPRINT "HELLO"\rENDPROC\r',
            )
            summary = self.run_actedit(workspace, "MAIN", key_bytes=[0xFF])

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_source_path"], "src/main.act")
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [1])
        self.assertEqual(summary["dumps"]["actedit_current_line_hi"], [0])
        self.assertEqual(summary["dumps"]["actedit_left_col"], [0])
        self.assertEqual(summary["dumps"]["actedit_cursor_col"], [0])
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0])
        self.assertIn("actedit src/main.act", screen)
        self.assertIn("> proc main()", screen)
        self.assertIn('  print "hello"', screen)

    def test_actedit_normalizes_screen_code_module_source_path(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(tmpdir, "PROC MAIN()\rRETURN\r")
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0xFF],
                screen_code_cmdline=True,
            )

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_source_path"], "src/main.act")
        self.assertIn("> proc main()", screen)

    def test_actedit_loads_direct_source_path_and_quits(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                'PROC MAIN()\rPRINT "HELLO"\rENDPROC\r',
            )
            summary = self.run_actedit(workspace, "src/main.act", key_bytes=[0xFF])

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_source_path"], "src/main.act")
        self.assertIn("actedit src/main.act", screen)
        self.assertIn("> proc main()", screen)

    def test_actedit_loads_direct_source_path_at_requested_line(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                "PROC MAIN()\rPRINT A\rPRINT B\rENDPROC\r",
            )
            summary = self.run_actedit(
                workspace,
                "src/main.act:3",
                key_bytes=[0xFF],
            )

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_source_path"], "src/main.act")
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [3], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_current_line_hi"], [0], msg=screen)
        self.assertIn("> print b", screen)

    def test_actedit_renders_screen_code_path_and_requested_line(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                "MODULE MAIN\rPROC MAIN()\rRETURN\r",
            )
            summary = self.run_actedit(
                workspace,
                "src/main.act:2",
                key_bytes=[0xFF],
                screen_code_cmdline=True,
            )

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [2], msg=screen)
        self.assertIn("actedit src/main.act", screen)
        self.assertIn("> proc main()", screen)

    def test_actedit_loads_source_larger_than_64k_from_reu(self) -> None:
        self.require_toolchain()
        self.build_tools()

        source_text = "".join(
            f"LINE {line_number:04d} {'X' * 140}\r"
            for line_number in range(1, 451)
        )
        self.assertGreater(len(source_text), 0x10000)

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(tmpdir, source_text)
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x07, 0x34, 0x35, 0x30, 0x0D, 0x85, 0xFF],
                max_steps=15_000_000,
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        reu_stage = next(op for op in summary["ops"] if op["kind"] == "rsta")
        self.assertEqual(reu_stage["params"][2:5], [0, 0, 7], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_source_stage_len_bank"], [1], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_source_line_count_lo"], [0xC2, 0x01], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_source_line_index_ready"], [1], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [0xC2], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_current_line_hi"], [0x01], msg=screen)
        self.assertIn("> line 0450", screen)
        self.assertEqual(saved, source_text)

    def test_actedit_rebuilds_persistent_logical_line_index_after_split(self) -> None:
        self.require_toolchain()
        self.build_tools()

        source_lines = [f"A{line_number:03d}" for line_number in range(1, 301)]
        source_text = "\r".join(source_lines) + "\r"
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(tmpdir, source_text)
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x07, ord("1"), ord("5"), ord("0"), 0x0D, 0x1D, 0x0D, 0x85, 0xFF],
                max_steps=10_000_000,
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        expected_lines = source_lines[:149] + ["A", "150"] + source_lines[150:]
        self.assertEqual(saved, "\r".join(expected_lines) + "\r")
        self.assertEqual(summary["dumps"]["actedit_logical_line_count_lo"], [0x2D, 0x01])
        self.assertEqual(summary["dumps"]["actedit_logical_line_index_ready"], [1])
        self.assertEqual(summary["dumps"]["actedit_piece_rebuild_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_direct_patch_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_direct_insert_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_logical_index_suffix_count"], [2], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_mutation_overlay_load_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_mutation_overlay_fail_count"], [0], msg=summary)
        overlay_loads = [
            op
            for op in summary["ops"]
            if op["kind"] == "load" and op["path"] == "!ACTEDIT_OVL1.BIN"
        ]
        self.assertEqual(len(overlay_loads), 1, msg=summary)
        self.assertTrue(
            any(
                op["kind"] == "rwr"
                and op["params"][0:3] == [0x00, 0x00, 0x00]
                and op["params"][5:7] == [0xFF, 0x00]
                for op in summary["ops"]
            ),
            msg=summary,
        )
        self.assertTrue(
            any(
                op["kind"] == "rrd"
                and op["params"][2] < 0x03
                and op["params"][5:7] == [0x03, 0x00]
                for op in summary["ops"]
            ),
            msg=summary,
        )
        suffix_write_offsets = {
            tuple(op["params"][0:3])
            for op in summary["ops"]
            if op["kind"] == "rwr" and op["params"][2] < 0x03
        }
        self.assertIn((0xBF, 0x01, 0x00), suffix_write_offsets, msg=summary)
        self.assertIn((0xC2, 0x01, 0x00), suffix_write_offsets, msg=summary)

    def test_actedit_patches_source_piece_without_full_descriptor_rebuild(self) -> None:
        self.require_toolchain()
        self.build_tools()

        source_text = "A001\rA002\rA003\rA004\rA005\r"
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(tmpdir, source_text)
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x07, ord("3"), 0x0D, ord("X"), 0x11, 0x91, 0xFF],
                max_steps=3_000_000,
            )

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [3], msg=screen)
        self.assertIn("> xa003", screen)
        self.assertEqual(summary["dumps"]["actedit_piece_rebuild_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_direct_patch_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_logical_index_suffix_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_logical_line_index_ready"], [1])
        self.assertEqual(summary["dumps"]["actedit_mutation_overlay_load_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_mutation_overlay_fail_count"], [0], msg=summary)

    def test_actedit_missing_or_invalid_mutation_overlay_uses_rebuild_fallback(self) -> None:
        self.require_toolchain()
        self.build_tools()

        source_text = "A001\rA002\rA003\rA004\rA005\r"
        overlay_data = (self.build_dir / "ACTEDIT_OVL1.BIN").read_bytes()
        for mode in ("missing", "invalid"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmpdir:
                temp_root = Path(tmpdir)
                tool_dir = temp_root / "tools"
                tool_dir.mkdir()
                prg_path = tool_dir / "ACTEDIT.PRG"
                shutil.copy2(self.build_dir / "ACTEDIT.PRG", prg_path)
                if mode == "invalid":
                    (tool_dir / "ACTEDIT_OVL1.BIN").write_bytes(b"BAD!" + overlay_data[4:])
                workspace = self.make_workspace(tmpdir, source_text)
                summary = self.run_actedit(
                    workspace,
                    "MAIN",
                    key_bytes=[0x07, ord("3"), 0x0D, ord("X"), 0x11, 0x91, 0xFF],
                    max_steps=3_000_000,
                    prg_path=prg_path,
                )

            screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
            self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [3], msg=screen)
            self.assertIn("> xa003", screen)
            self.assertGreaterEqual(summary["dumps"]["actedit_piece_rebuild_count"][0], 2, msg=summary)
            self.assertEqual(summary["dumps"]["actedit_direct_patch_count"], [0], msg=summary)
            self.assertEqual(summary["dumps"]["actedit_mutation_overlay_load_count"], [0], msg=summary)
            self.assertEqual(summary["dumps"]["actedit_mutation_overlay_fail_count"], [1], msg=summary)
            overlay_loads = [
                op
                for op in summary["ops"]
                if op["kind"] == "load" and op["path"] == "!ACTEDIT_OVL1.BIN"
            ]
            self.assertEqual(len(overlay_loads), 1, msg=summary)

    def test_actedit_missing_or_invalid_mutation_overlay_rebuilds_removed_line(self) -> None:
        self.require_toolchain()
        self.build_tools()

        source_text = "PROC MAIN()\rPRINT \rA\rENDPROC\r"
        overlay_data = (self.build_dir / "ACTEDIT_OVL1.BIN").read_bytes()
        for mode in ("missing", "invalid"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmpdir:
                temp_root = Path(tmpdir)
                tool_dir = temp_root / "tools"
                tool_dir.mkdir()
                prg_path = tool_dir / "ACTEDIT.PRG"
                shutil.copy2(self.build_dir / "ACTEDIT.PRG", prg_path)
                if mode == "invalid":
                    (tool_dir / "ACTEDIT_OVL1.BIN").write_bytes(b"BAD!" + overlay_data[4:])
                workspace = self.make_workspace(tmpdir, source_text)
                summary = self.run_actedit(
                    workspace,
                    "MAIN",
                    key_bytes=[0x11, 0x11, 0x14, 0x85, 0xFF],
                    max_steps=3_000_000,
                    prg_path=prg_path,
                )
                saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

            self.assertEqual(saved, "PROC MAIN()\rPRINT A\rENDPROC\r")
            self.assertGreaterEqual(summary["dumps"]["actedit_piece_rebuild_count"][0], 2, msg=summary)
            self.assertEqual(summary["dumps"]["actedit_direct_remove_count"], [0], msg=summary)
            self.assertEqual(summary["dumps"]["actedit_mutation_overlay_load_count"], [0], msg=summary)
            self.assertEqual(summary["dumps"]["actedit_mutation_overlay_fail_count"], [1], msg=summary)

    def test_actedit_scrolls_vertically_and_horizontally(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                'PROC MAIN()\rPRINT "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"\rENDPROC\r',
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x1D, 0x1D, 0xFF],
            )

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [2])
        self.assertEqual(summary["dumps"]["actedit_current_line_hi"], [0])
        self.assertEqual(summary["dumps"]["actedit_left_col"], [0])
        self.assertEqual(summary["dumps"]["actedit_cursor_col"], [2])
        self.assertIn('> print "0123456789abcdefghijklmnopqrst', screen)

    def test_actedit_home_moves_to_line_start_then_file_top(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                "PROC MAIN()\rPRINT ABC\rPRINT DEF\rENDPROC\r",
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x1D, 0x1D, 0x1D, 0x13, 0x13, 0xFF],
            )

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [1], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_cursor_col"], [0], msg=screen)
        self.assertIn("> proc main()", screen)

    def test_actedit_page_and_file_navigation_keys(self) -> None:
        self.require_toolchain()
        self.build_tools()

        body = "".join(f"L{index:02d}\r" for index in range(1, 26))
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                "PROC MAIN()\r" + body + "ENDPROC\r",
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x8C, 0x93, 0x94, 0x94, 0xFF],
            )

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [27], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_cursor_col"], [7], msg=screen)
        self.assertIn("> endproc", screen)

    def test_actedit_insert_persists_across_line_navigation(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                'PROC MAIN()\rPRINT "HELLO"\rENDPROC\r',
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x58, 0x11, 0x91, 0xFF],
            )

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [2])
        self.assertEqual(summary["dumps"]["actedit_dirty"], [1])
        self.assertIn('> print "xhello"', screen)

    def test_actedit_undo_restores_last_insert(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                'PROC MAIN()\rPRINT "HELLO"\rENDPROC\r',
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x58, 0x15, 0x85, 0xFF],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertIn('> print "hello"', screen)
        self.assertEqual(saved, 'PROC MAIN()\rPRINT "HELLO"\rENDPROC\r')

    def test_actedit_multi_step_undo_walks_back_multiple_edits(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                'PROC MAIN()\rPRINT "HELLO"\rENDPROC\r',
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x58, 0x59, 0x15, 0x15, 0x85, 0xFF],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertIn('> print "hello"', screen)
        self.assertEqual(saved, 'PROC MAIN()\rPRINT "HELLO"\rENDPROC\r')

    def test_actedit_undo_journal_keeps_more_than_four_steps(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                'PROC MAIN()\rPRINT "HELLO"\rENDPROC\r',
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[
                    0x11, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D,
                    0x41, 0x42, 0x43, 0x44, 0x45,
                    0x15, 0x15, 0x15, 0x15, 0x15,
                    0x85, 0xFF,
                ],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertIn('> print "hello"', screen)
        self.assertEqual(saved, 'PROC MAIN()\rPRINT "HELLO"\rENDPROC\r')

    def test_actedit_undo_journal_restores_ten_typed_edits(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(tmpdir, "HELLO\r")
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[
                    *[ord(char) for char in "1234567890"],
                    *([0x15] * 10),
                    0x85,
                    0xFF,
                ],
                max_steps=100_000_000,
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertIn("> hello", screen)
        self.assertEqual(saved, "HELLO\r")

    def test_actedit_tracks_more_than_eight_distinct_line_patches(self) -> None:
        self.require_toolchain()
        self.build_tools()

        source_text = "A\r" * 12
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(tmpdir, source_text)
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=([0x58, 0x11] * 10) + [0x85, 0xFF],
                max_steps=4_000_000,
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertEqual(saved, "XA\r" + ("AX\r" * 9) + ("A\r" * 2))

    def test_actedit_redo_restores_last_undone_insert(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                'PROC MAIN()\rPRINT "HELLO"\rENDPROC\r',
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x58, 0x15, 0x19, 0x85, 0xFF],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertIn('> print "xhello"', screen)
        self.assertEqual(saved, 'PROC MAIN()\rPRINT "XHELLO"\rENDPROC\r')

    def test_actedit_new_edit_clears_redo_history(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                'PROC MAIN()\rPRINT "HELLO"\rENDPROC\r',
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x58, 0x15, 0x5A, 0x19, 0x85, 0xFF],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertIn('> print "zhello"', screen)
        self.assertEqual(saved, 'PROC MAIN()\rPRINT "ZHELLO"\rENDPROC\r')

    def test_actedit_save_writes_modified_source(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                'PROC MAIN()\rPRINT "HELLO"\rENDPROC\r',
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x58, 0x85, 0xFF],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertIn('> print "xhello"', screen)
        self.assertEqual(saved, 'PROC MAIN()\rPRINT "XHELLO"\rENDPROC\r')
        self.assertTrue(any(op["kind"] == "wopn" and op["path"] == "src/main.act" for op in summary["ops"]))
        self.assertTrue(any(op["kind"] == "wrte" and op["status"] == 1 for op in summary["ops"]))
        self.assertTrue(any(op["kind"] == "wcls" and op["status"] == 1 for op in summary["ops"]))

    def test_actedit_printable_command_letters_are_source_text(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(tmpdir, "\r")
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x47, 0x52, 0x55, 0x59, 0x85, 0xFF],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertIn("> gruy", screen)
        self.assertEqual(saved, "GRUY\r")

    def test_actedit_mark_copy_and_paste_duplicate_current_line_selection(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                'PROC MAIN()\rPRINT "HELLO"\rENDPROC\r',
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x86, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x87, 0x88, 0xFF],
            )

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [2], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_dirty"], [1], msg=screen)
        self.assertIn('> print "hellohello"', screen)

    def test_actedit_cut_selection_and_save_updates_source(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                'PROC MAIN()\rPRINT "HELLO"\rENDPROC\r',
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x86, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x8B, 0x85, 0xFF],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertIn('> print ""', screen)
        self.assertEqual(saved, 'PROC MAIN()\rPRINT ""\rENDPROC\r')

    def test_actedit_find_next_token_moves_to_next_match(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                "PROC MAIN()\rPRINT A\rPRINT B\rENDPROC\r",
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x89, 0xFF],
            )

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [3], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_cursor_col"], [0], msg=screen)
        self.assertIn("> print b", screen)

    def test_actedit_find_prev_token_moves_to_previous_match(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                "PROC MAIN()\rPRINT A\rPRINT B\rENDPROC\r",
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x11, 0x8A, 0xFF],
            )

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [2], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_cursor_col"], [0], msg=screen)
        self.assertIn("> print a", screen)

    def test_actedit_goto_line_moves_to_requested_line(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                "PROC MAIN()\rPRINT A\rPRINT B\rENDPROC\r",
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x07, 0x33, 0x0D, 0xFF],
            )

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [3], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_cursor_col"], [0], msg=screen)
        self.assertIn("> print b", screen)

    def test_actedit_replace_next_and_save_updates_source(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                "PROC MAIN()\rPRINT A\rPRINT A\rENDPROC\r",
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x12, 0x5A, 0x0D, 0x85, 0xFF],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [2], msg=screen)
        self.assertIn("> print z", screen)
        self.assertEqual(saved, "PROC MAIN()\rPRINT Z\rPRINT A\rENDPROC\r")

    def test_actedit_replace_all_and_save_updates_every_match(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                "PROC MAIN()\rCAT CAT\rCATALOG CAT\rENDPROC\r",
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x01, 0x43, 0x41, 0x54, 0x58, 0x0D, 0x85, 0xFF],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [3], msg=screen)
        self.assertIn("> catxalog catx", screen)
        self.assertEqual(saved, "PROC MAIN()\rCATX CATX\rCATXALOG CATX\rENDPROC\r")

    def test_actedit_replace_all_is_one_undo_operation(self) -> None:
        self.require_toolchain()
        self.build_tools()

        original = "PROC MAIN()\rCAT CAT\rCAT\rENDPROC\r"
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(tmpdir, original)
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x01, 0x44, 0x4F, 0x47, 0x0D, 0x15, 0x85, 0xFF],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [2], msg=screen)
        self.assertIn("> cat cat", screen)
        self.assertEqual(saved, original)

    def test_actedit_split_line_and_save_updates_source(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                "PROC MAIN()\rPRINT A\rENDPROC\r",
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x0D, 0x85, 0xFF],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [3], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_cursor_col"], [0], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertIn("> a", screen)
        self.assertEqual(saved, "PROC MAIN()\rPRINT \rA\rENDPROC\r")

    def test_actedit_direct_split_handles_inserted_line(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(tmpdir, "ABC\rEND\r")
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x1D, 0x0D, 0x1D, 0x0D, 0x85, 0xFF],
                max_steps=3_000_000,
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(saved, "A\rB\rC\rEND\r")
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [3], msg=screen)
        self.assertIn("> c", screen)
        self.assertEqual(summary["dumps"]["actedit_piece_rebuild_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_direct_patch_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_direct_insert_count"], [2], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_direct_remove_count"], [0], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_direct_insert_update_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_logical_index_suffix_count"], [3], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_logical_line_index_ready"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_mutation_overlay_fail_count"], [0], msg=summary)

    def test_actedit_join_line_with_delete_at_column_zero(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                "PROC MAIN()\rPRINT \rA\rENDPROC\r",
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x11, 0x14, 0x85, 0xFF],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [2], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_cursor_col"], [7], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertIn("> print a", screen)
        self.assertEqual(saved, "PROC MAIN()\rPRINT A\rENDPROC\r")
        self.assertEqual(summary["dumps"]["actedit_piece_rebuild_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_direct_patch_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_direct_remove_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_logical_index_suffix_count"], [2], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_logical_line_index_ready"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_mutation_overlay_load_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_mutation_overlay_fail_count"], [0], msg=summary)

    def test_actedit_direct_remove_handles_new_insert_piece(self) -> None:
        self.require_toolchain()
        self.build_tools()

        original = "PROC MAIN()\rPRINT A\rENDPROC\r"
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(tmpdir, original)
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, *([0x1D] * 6), 0x0D, 0x14, 0x85, 0xFF],
                max_steps=3_000_000,
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(saved, original)
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [2], msg=screen)
        self.assertIn("> print a", screen)
        self.assertEqual(summary["dumps"]["actedit_piece_rebuild_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_direct_patch_count"], [2], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_direct_insert_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_direct_remove_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_logical_line_index_ready"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_mutation_overlay_load_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_mutation_overlay_fail_count"], [0], msg=summary)

    def test_actedit_direct_remove_covers_source_edges_and_patch_piece(self) -> None:
        self.require_toolchain()
        self.build_tools()

        cases = (
            (
                "source-start",
                [ord("X"), 0x11, 0x13, 0x14, 0x85, 0xFF],
                "XAB\rC\rD\r",
                2,
            ),
            (
                "source-end",
                [0x11, 0x11, 0x11, 0x14, 0x85, 0xFF],
                "A\rB\rCD\r",
                1,
            ),
            (
                "patch",
                [0x11, 0x11, ord("X"), 0x11, 0x91, 0x13, 0x14, 0x85, 0xFF],
                "A\rBXC\rD\r",
                2,
            ),
        )
        for name, keys, expected, patch_count in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmpdir:
                workspace = self.make_workspace(tmpdir, "A\rB\rC\rD\r")
                summary = self.run_actedit(
                    workspace,
                    "MAIN",
                    key_bytes=keys,
                    max_steps=3_000_000,
                )
                saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

            self.assertEqual(saved, expected)
            self.assertEqual(summary["dumps"]["actedit_piece_rebuild_count"], [1], msg=summary)
            self.assertEqual(summary["dumps"]["actedit_direct_patch_count"], [patch_count], msg=summary)
            self.assertEqual(summary["dumps"]["actedit_direct_remove_count"], [1], msg=summary)
            self.assertEqual(summary["dumps"]["actedit_logical_line_index_ready"], [1], msg=summary)
            self.assertEqual(summary["dumps"]["actedit_mutation_overlay_fail_count"], [0], msg=summary)

    def test_actedit_multiline_cut_merges_endpoints(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                "PROC MAIN()\rAX\rBY\rENDPROC\r",
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x1D, 0x86, 0x11, 0x8B, 0x85, 0xFF],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [2], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_cursor_col"], [1], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertIn("> ay", screen)
        self.assertEqual(saved, "PROC MAIN()\rAY\rENDPROC\r")
        self.assertEqual(summary["dumps"]["actedit_piece_rebuild_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_direct_remove_count"], [1], msg=summary)

    def test_actedit_undo_restores_multiline_cut(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                "PROC MAIN()\rAX\rBY\rENDPROC\r",
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x1D, 0x86, 0x11, 0x8B, 0x15, 0x85, 0xFF],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [3], msg=screen)
        self.assertIn("> by", screen)
        self.assertEqual(saved, "PROC MAIN()\rAX\rBY\rENDPROC\r")

    def test_actedit_multiline_copy_and_paste_preserves_line_breaks(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                "PROC MAIN()\rA\rB\rENDPROC\r",
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x86, 0x11, 0x1D, 0x87, 0x11, 0x9D, 0x0D, 0x91, 0x88, 0x85, 0xFF],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertIn("> b", screen)
        self.assertEqual(saved, "PROC MAIN()\rA\rB\rA\rB\rENDPROC\r")
        self.assertEqual(summary["dumps"]["actedit_piece_rebuild_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_direct_insert_update_count"], [1], msg=summary)
        self.assertEqual(summary["dumps"]["actedit_logical_index_suffix_count"], [3], msg=summary)

    def test_actedit_multiline_delete_preserves_clipboard(self) -> None:
        self.require_toolchain()
        self.build_tools()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                "PROC MAIN()\rZ\rAX\rBY\rENDPROC\r",
            )
            summary = self.run_actedit(
                workspace,
                "MAIN",
                key_bytes=[0x11, 0x86, 0x1D, 0x87, 0x11, 0x86, 0x11, 0x14, 0x91, 0x88, 0x85, 0xFF],
            )
            saved = (workspace / "src" / "main.act").read_bytes().decode("ascii")

        screen = self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))
        self.assertEqual(summary["dumps"]["actedit_dirty"], [0], msg=screen)
        self.assertEqual(summary["dumps"]["actedit_current_line_lo"], [2], msg=screen)
        self.assertIn("> zz", screen)
        self.assertEqual(saved, "PROC MAIN()\rZZ\rAY\rENDPROC\r")


if __name__ == "__main__":
    unittest.main()
