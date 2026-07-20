from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestActdbg(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.build_dir = self.root / "build" / "udos_tools"
        sys.path.insert(0, str(self.root / "tools"))
        from vice_harness import screen_ram_to_text

        self.screen_ram_to_text = screen_ram_to_text

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
        self.run_checked([str(self.root / "tools" / "build_actdbg_udos.sh")])

    def make_workspace(
        self,
        tmpdir: str,
        code: bytes,
        records: list[str],
        source: str,
    ) -> Path:
        workspace = Path(tmpdir) / "ws"
        (workspace / "bin").mkdir(parents=True)
        (workspace / "src").mkdir()
        (workspace / "bin" / "MAIN.PRG").write_bytes(b"\x00\x10" + code)
        (workspace / "bin" / "MAIN.DBG").write_text(
            "\n".join(
                [
                    "DBG1",
                    "e 4096",
                    "m 0 MAIN",
                    "f 0 0 src/main.act",
                    "q 0 0 4096 0 1 1 MAIN",
                    *records,
                    "",
                ]
            ),
            encoding="ascii",
        )
        (workspace / "src" / "main.act").write_text(source, encoding="ascii")
        return workspace

    def make_multifile_workspace(self, tmpdir: str) -> Path:
        workspace = self.make_workspace(
            tmpdir,
            bytes((0x20, 0x05, 0x10, 0xEA, 0x60, 0xEA, 0x60)),
            [],
            "PROC MAIN()\rSUB()\rENDPROC\r",
        )
        (workspace / "bin" / "MAIN.DBG").write_text(
            "DBG1\n"
            "e 4096\n"
            "m 0 MAIN\n"
            "f 0 0 src/main.act\n"
            "f 0 1 src/sub.act\n"
            "q 0 0 4096 0 1 1 MAIN\n"
            "l 0 0 4096 0 2 1\n"
            "l 0 0 4099 0 3 1\n"
            "q 0 1 4101 1 1 1 SUB\n"
            "l 0 1 4101 1 2 1\n",
            encoding="ascii",
        )
        (workspace / "src" / "sub.act").write_text(
            "PROC SUB()\rX=1\rENDPROC\r",
            encoding="ascii",
        )
        return workspace

    def run_actdbg(
        self,
        workspace: Path,
        keys: list[int],
        cmdline: str = "MAIN",
        screen_code_cmdline: bool = False,
    ) -> dict:
        cmd = [
            str(self.build_dir / "tool_abi_harness"),
            "--prg",
            str(self.build_dir / "ACTDBG.PRG"),
            "--workspace",
            str(workspace),
            "--cmdline",
            cmdline,
            "--services-inc",
            str(self.build_dir / "udos_services.inc"),
            "--labels",
            str(self.build_dir / "actdbg.current.labels"),
            "--poke-byte",
            "actdbg_test_mode=1",
            "--poke-byte",
            f"actdbg_test_key_count={len(keys)}",
            "--dump",
            "actdbg_current_pc_lo:1",
            "--dump",
            "actdbg_current_pc_hi:1",
            "--dump",
            "actdbg_native_done:1",
            "--dump",
            "actdbg_native_failed:1",
            "--dump",
            "actdbg_native_sp:1",
            "--dump",
            "actdbg_break_hit:1",
            "--dump",
            "actdbg_view_mode:1",
            "--dump",
            "0x0400:1000",
            "--dump",
            "actdbg_test_key_count:1",
            "--dump",
            "actdbg_test_key_index:1",
            "--dump-cstr",
            "actdbg_source_path:128",
            "--dump-cstr",
            "actdbg_global_summary:40",
            "--dump-cstr",
            "actdbg_param_summary:40",
            "--dump-cstr",
            "actdbg_local_summary:40",
            "--dump-cstr",
            "actdbg_backtrace_summary:40",
            "--max-steps",
            "8000000",
        ]
        if screen_code_cmdline:
            cmd.append("--cmdline-screen-code")
        for index, key in enumerate(keys):
            cmd.extend(["--poke-byte", f"actdbg_test_key{index}=0x{key:02x}"])
        result = self.run_checked(cmd)
        summary = json.loads(result.stdout)
        self.assertTrue(summary["exited"], result.stdout)
        self.assertFalse(summary["hit_limit"], result.stdout)
        return summary

    def screen_text(self, summary: dict) -> str:
        return self.screen_ram_to_text(bytes(summary["dumps"]["0x0400"]))

    @staticmethod
    def pc(summary: dict) -> int:
        dumps = summary["dumps"]
        return dumps["actdbg_current_pc_lo"][0] | (dumps["actdbg_current_pc_hi"][0] << 8)

    def test_builds_resident_and_native_overlays(self) -> None:
        self.require_toolchain()
        self.build_tools()
        self.assertEqual((self.build_dir / "ACTDBG.PRG").read_bytes()[:2], b"\x00\x09")
        self.assertEqual((self.build_dir / "ACTDBG_OVL1.BIN").read_bytes()[:4], b"DGOV")
        self.assertEqual((self.build_dir / "ACTDBG_OVL2.BIN").read_bytes()[:4], b"DGOV")

    def test_exit_clears_debugger_screen_before_returning_to_udos(self) -> None:
        source = (self.root / "src" / "tools_udos" / "actdbg" / "actdbg.asm").read_text()
        exit_path = source.split("exit_ok:", 1)[1].split("fail_with_ptr:", 1)[0]
        self.assertIn("lda actdbg_test_mode\n    bne :+", exit_path)
        self.assertIn("lda #KEY_CLRHOME\n    jsr CHROUT", exit_path)
        self.assertLess(exit_path.index("jsr CHROUT"), exit_path.index("jmp svc_program_exit"))

    def test_loads_normal_prg_and_absolute_debug_sidecar(self) -> None:
        self.require_toolchain()
        self.build_tools()
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                b"\xea\x60",
                ["l 0 0 4096 0 2 1", "l 0 0 4097 0 3 1"],
                "PROC MAIN()\rNOP\rENDPROC\r",
            )
            summary = self.run_actdbg(workspace, [0xFF], "BIN/MAIN.PRG")
        self.assertEqual(self.pc(summary), 0x1000)
        self.assertEqual(summary["dumps"]["actdbg_native_failed"], [0])
        self.assertEqual(summary["dumps"]["actdbg_source_path"], "src/main.act")

    def test_long_debug_sidecar_preserves_buffered_input(self) -> None:
        self.require_toolchain()
        self.build_tools()
        records = [f"l 0 0 {4096 + index} 0 {index + 2} 1" for index in range(80)]
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                b"\xea\x60",
                records,
                "PROC MAIN()\rNOP\rENDPROC\r",
            )
            summary = self.run_actdbg(workspace, [0xFF], "BIN/MAIN.PRG")
        self.assertEqual(summary["dumps"]["actdbg_test_key_count"], [0])
        self.assertEqual(summary["dumps"]["actdbg_test_key_index"], [1])

    def test_actc_alink_native_output_runs_under_actdbg(self) -> None:
        self.require_toolchain()
        self.build_tools()
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])
        self.run_checked([str(self.root / "tools" / "build_alink_udos.sh")])
        sys.path.insert(0, str(self.root.parent / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        with tempfile.TemporaryDirectory() as tmpdir:
            fs_root = Path(tmpdir)
            action_root = fs_root / "IMAGES" / "ACTION.DNP"
            action_root.mkdir(parents=True)
            (action_root / "UDOSDIR.TXT").write_text("", encoding="ascii")
            project_root, _ = probe.prepare_workspace(fs_root, "PROJ3", "if_eq")
            probe.run_harness(probe.ACTION_ACTC_BUILD, probe.ACTION_ACTC_LABELS, project_root)
            probe.verify_actc_object_output(project_root, "if_eq")
            alink_summary = probe.run_harness(
                probe.ACTION_ALINK_BUILD,
                probe.ACTION_ALINK_LABELS,
                project_root,
            )
            probe.verify_alink_dependency_loads(alink_summary, "if_eq")
            probe.verify_host_output(project_root, "if_eq")
            sidecar_path = probe.verify_host_debug_output(project_root, "if_eq")
            sidecar = sidecar_path.read_text(encoding="ascii")
            summary = self.run_actdbg(
                action_root,
                [0x87, 0xFF],
                "PROJ3/BIN/MAIN.PRG",
                screen_code_cmdline=True,
            )

        self.assertIn("e 4096\n", sidecar)
        self.assertIn("q 0 0 4096", sidecar)
        self.assertIn("l 0 0 ", sidecar)
        self.assertIn("v g c 0 0 ", sidecar)
        self.assertEqual(summary["dumps"]["actdbg_source_path"], "PROJ3/src/main.act")
        self.assertEqual(summary["dumps"]["actdbg_native_done"], [1])
        self.assertEqual(summary["dumps"]["actdbg_native_failed"], [0])
        self.assertEqual(summary["dumps"]["actdbg_global_summary"], "x=7, y=1")

    def test_alink_debug_sidecar_uses_loaded_data_export_offset(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])
        self.run_checked([str(self.root / "tools" / "build_alink_udos.sh")])
        sys.path.insert(0, str(self.root.parent / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "actc_runtime_integer_add_sub_linked"
        with tempfile.TemporaryDirectory() as tmpdir:
            fs_root = Path(tmpdir)
            action_root = fs_root / "IMAGES" / "ACTION.DNP"
            action_root.mkdir(parents=True)
            (action_root / "UDOSDIR.TXT").write_text("", encoding="ascii")
            project_root, _ = probe.prepare_workspace(fs_root, "PROJ3", shape)
            probe.run_harness(probe.ACTION_ACTC_BUILD, probe.ACTION_ACTC_LABELS, project_root)
            probe.verify_actc_object_output(project_root, shape)
            probe.run_harness(probe.ACTION_ALINK_BUILD, probe.ACTION_ALINK_LABELS, project_root)
            probe.verify_host_output(project_root, shape)
            sidecar_path = probe.verify_host_debug_output(project_root, shape)
            sidecar_lines = sidecar_path.read_text(encoding="ascii").splitlines()

        self.assertIn("v g i 0 0 4201 2 0 2 5 a", sidecar_lines)
        self.assertIn("v g i 0 1 4203 2 0 3 5 b", sidecar_lines)
        self.assertIn("v g i 0 2 4205 2 0 4 5 c", sidecar_lines)

    def test_step_executes_one_native_instruction(self) -> None:
        self.require_toolchain()
        self.build_tools()
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                b"\xea\x60",
                ["l 0 0 4096 0 2 1", "l 0 0 4097 0 3 1"],
                "PROC MAIN()\rNOP\rENDPROC\r",
            )
            summary = self.run_actdbg(workspace, [0x86, 0xFF])
        self.assertEqual(self.pc(summary), 0x1001)
        self.assertEqual(summary["dumps"]["actdbg_native_done"], [0])
        self.assertEqual(summary["dumps"]["actdbg_native_failed"], [0])

    def test_continue_runs_native_program_to_completion(self) -> None:
        self.require_toolchain()
        self.build_tools()
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                b"\xea\x60",
                ["l 0 0 4096 0 2 1"],
                "PROC MAIN()\rNOP\rENDPROC\r",
            )
            summary = self.run_actdbg(workspace, [0x87, 0xFF])
        self.assertEqual(summary["dumps"]["actdbg_native_done"], [1])
        self.assertEqual(summary["dumps"]["actdbg_native_failed"], [0])
        self.assertEqual(summary["dumps"]["actdbg_view_mode"], [1])

    def test_step_into_over_and_out_follow_native_jsr_stack(self) -> None:
        self.require_toolchain()
        self.build_tools()
        code = bytes((0x20, 0x05, 0x10, 0xEA, 0x60, 0xEA, 0x60))
        records = [
            "l 0 0 4096 0 2 1",
            "l 0 0 4099 0 3 1",
            "q 0 1 4101 0 5 1 SUB",
            "l 0 1 4101 0 6 1",
        ]
        source = "PROC MAIN()\rSUB()\rENDPROC\r\rPROC SUB()\rNOP\rENDPROC\r"
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(tmpdir, code, records, source)
            step_into = self.run_actdbg(workspace, [0x86, 0xFF])
            step_over = self.run_actdbg(workspace, [0x8A, 0xFF])
            step_out = self.run_actdbg(workspace, [0x86, 0x8B, 0xFF])
        self.assertEqual(self.pc(step_into), 0x1005)
        self.assertEqual(step_into["dumps"]["actdbg_native_sp"], [0xFB])
        self.assertEqual(step_into["dumps"]["actdbg_backtrace_summary"], "SUB <- MAIN")
        self.assertEqual(self.pc(step_over), 0x1003)
        self.assertEqual(step_over["dumps"]["actdbg_native_sp"], [0xFD])
        self.assertEqual(self.pc(step_out), 0x1003)
        self.assertEqual(step_out["dumps"]["actdbg_native_sp"], [0xFD])

    def test_step_into_switches_to_linked_source_file(self) -> None:
        self.require_toolchain()
        self.build_tools()
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_multifile_workspace(tmpdir)
            summary = self.run_actdbg(workspace, [0x86, 0xFF])
        screen = self.screen_text(summary)
        self.assertEqual(summary["dumps"]["actdbg_source_path"], "src/sub.act")
        self.assertIn("src/sub.act", screen)
        self.assertIn("> x=1", screen)

    def test_source_navigation_crosses_procedures_lines_and_files(self) -> None:
        self.require_toolchain()
        self.build_tools()
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_multifile_workspace(tmpdir)
            next_proc = self.run_actdbg(workspace, [0x4D, 0xFF])
            next_line = self.run_actdbg(workspace, [0x4E, 0xFF])
            next_file = self.run_actdbg(workspace, [0x2E, 0xFF])
        self.assertEqual(next_proc["dumps"]["actdbg_source_path"], "src/sub.act")
        self.assertIn("> x=1", self.screen_text(next_proc))
        self.assertEqual(next_line["dumps"]["actdbg_source_path"], "src/main.act")
        self.assertIn("> endproc", self.screen_text(next_line))
        self.assertEqual(next_file["dumps"]["actdbg_source_path"], "src/sub.act")

    def test_edit_key_chains_active_linked_source_location(self) -> None:
        self.require_toolchain()
        self.build_tools()
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_multifile_workspace(tmpdir)
            summary = self.run_actdbg(workspace, [0x2E, 0x45])
        self.assertEqual(summary["dumps"]["actdbg_source_path"], "src/sub.act")
        self.assertTrue(summary["chain_requested"], msg=summary)
        self.assertEqual(summary["chain_command"], "ACTEDIT src/sub.act:2")

    def test_edit_key_rejects_overlength_location_without_truncation(self) -> None:
        self.require_toolchain()
        self.build_tools()
        long_source_path = "src/source_name_that_is_too_long.act"
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                b"\xea\x60",
                ["l 0 0 4096 0 2 1"],
                "PROC MAIN()\rNOP\rENDPROC\r",
            )
            (workspace / "src" / "source_name_that_is_too_long.act").write_text(
                "PROC MAIN()\rNOP\rENDPROC\r",
                encoding="ascii",
            )
            sidecar = workspace / "bin" / "MAIN.DBG"
            sidecar.write_text(
                sidecar.read_text(encoding="ascii").replace("src/main.act", long_source_path),
                encoding="ascii",
            )
            summary = self.run_actdbg(workspace, [0x45, 0xFF])
        self.assertFalse(summary["chain_requested"], msg=summary)
        self.assertEqual(summary["chain_command"], "")
        self.assertIn("e: edit handoff failed", self.screen_text(summary))

    def test_breakpoint_list_and_clear_all_views(self) -> None:
        self.require_toolchain()
        self.build_tools()
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                bytes((0xEA, 0x4C, 0x00, 0x10)),
                ["l 0 0 4096 0 2 1"],
                "PROC MAIN()\rLOOP\rENDPROC\r",
            )
            listed = self.run_actdbg(workspace, [0x42, 0x4C, 0xFF])
            cleared = self.run_actdbg(workspace, [0x42, 0x43, 0x4C, 0xFF])
        self.assertIn("0: src/main.act:2", self.screen_text(listed))
        self.assertIn("0: none", self.screen_text(cleared))

    def test_typed_variable_summaries_use_linked_native_addresses(self) -> None:
        self.require_toolchain()
        self.build_tools()
        code = bytes((0x60, 0x7F, 0xDC, 0xFE, 0xFE, 0xFF, 0x00, 0x00, 0x80, 0x3F))
        records = [
            "l 0 0 4096 0 2 1",
            "v g b 0 0 4097 1 0 2 5 b",
            "v g c 0 1 4098 2 0 2 12 c",
            "v p i 0 0 2 4100 2 0 1 11 n",
            "v l r 0 0 3 4102 4 0 2 7 r",
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                code,
                records,
                "PROC MAIN(N)\rBYTE B\rCARD C\rREAL R\rENDPROC\r",
            )
            summary = self.run_actdbg(workspace, [0xFF])
        self.assertEqual(summary["dumps"]["actdbg_global_summary"], "b=127, c=65244")
        self.assertEqual(summary["dumps"]["actdbg_param_summary"], "n=-2")
        self.assertEqual(summary["dumps"]["actdbg_local_summary"], "r=1.0")

    def test_continue_rearms_breakpoint_at_current_pc(self) -> None:
        self.require_toolchain()
        self.build_tools()
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                bytes((0xEA, 0x4C, 0x00, 0x10)),
                ["l 0 0 4096 0 2 1"],
                "PROC MAIN()\rLOOP\rENDPROC\r",
            )
            summary = self.run_actdbg(workspace, [0x42, 0x87, 0xFF])
        self.assertEqual(self.pc(summary), 0x1000)
        self.assertEqual(summary["dumps"]["actdbg_break_hit"], [1])
        self.assertEqual(summary["dumps"]["actdbg_native_done"], [0])
        self.assertEqual(summary["dumps"]["actdbg_native_failed"], [0])

    def test_variable_values_follow_absolute_linked_addresses(self) -> None:
        self.require_toolchain()
        self.build_tools()
        code = bytes((0xA9, 42, 0x8D, 0x0B, 0x10, 0xA9, 0, 0x8D, 0x0C, 0x10, 0x60, 0, 0))
        records = ["l 0 0 4096 0 2 1", "v g c 0 0 4107 2 0 2 5 x"]
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = self.make_workspace(
                tmpdir,
                code,
                records,
                "PROC MAIN()\rX=42\rENDPROC\r",
            )
            initial = self.run_actdbg(workspace, [0xFF])
            stopped = self.run_actdbg(workspace, [0x87, 0x03, 0xFF])
        self.assertEqual(initial["dumps"]["actdbg_global_summary"], "x=0")
        self.assertEqual(stopped["dumps"]["actdbg_global_summary"], "x=42")
        self.assertEqual(stopped["dumps"]["actdbg_native_done"], [1])


if __name__ == "__main__":
    unittest.main()
