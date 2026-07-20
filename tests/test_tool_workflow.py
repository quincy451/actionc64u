from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import unittest


class TestToolWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.build_dir = cls.root / "build" / "udos_tools"
        for tool in ("cc", "ca65", "ld65", "make"):
            if shutil.which(tool) is None:
                raise unittest.SkipTest(f"{tool} not found")
        for script in (
            "build_tool_abi_harness.sh",
            "build_actc_udos.sh",
            "build_alink_udos.sh",
        ):
            cls.run_checked([str(cls.root / "tools" / script)])

    @classmethod
    def run_checked(cls, args: list[str]) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            args,
            cwd=cls.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        return result

    def run_tool(
        self,
        name: str,
        workspace: Path,
        cmdline: str,
        *,
        expected_status: int = 0,
    ) -> dict:
        result = subprocess.run(
            [
                str(self.build_dir / "tool_abi_harness"),
                "--prg",
                str(self.build_dir / f"{name}.PRG"),
                "--workspace",
                str(workspace),
                "--cmdline",
                cmdline,
                "--services-inc",
                str(self.build_dir / "udos_services.inc"),
                "--labels",
                str(self.build_dir / f"{name.lower()}.current.labels"),
                "--max-steps",
                "20000000",
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
        summary = json.loads(result.stdout)
        self.assertTrue(summary["exited"], msg=summary)
        self.assertFalse(summary["hit_limit"], msg=summary)
        self.assertEqual(result.returncode, expected_status, msg=result.stdout + result.stderr)
        self.assertEqual(summary["exit_status"], expected_status, msg=summary)
        return summary

    def assert_workflow_overlay_loaded(self, summary: dict, expected: bool) -> None:
        loaded = any(
            op["kind"] == "rsta"
            and op["path"] == "!ACTC_OVL0.BIN"
            and op["status"] == 1
            for op in summary["ops"]
        )
        self.assertEqual(loaded, expected, msg=summary)

    def test_compile_link_debug_successors_are_queued_after_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "project"
            for directory in ("src", "obj", "bin", "lib"):
                (workspace / directory).mkdir(parents=True, exist_ok=True)
            (workspace / "ACTION.PROJ").write_text(
                "ACTION PROJECT\rMAIN.ACT\r",
                encoding="ascii",
            )
            (workspace / "src" / "main.act").write_text(
                "MODULE MAIN\rPROC MAIN()\rRETURN\r",
                encoding="ascii",
            )

            compile_only = self.run_tool("ACTC", workspace, "MAIN;")
            self.assertTrue((workspace / "obj" / "MAIN.OBJ").is_file())
            self.assertFalse(compile_only["chain_requested"], msg=compile_only)
            self.assert_workflow_overlay_loaded(compile_only, False)

            compile_link = self.run_tool("ACTC", workspace, "MAIN,")
            self.assertTrue((workspace / "obj" / "MAIN.OBJ").is_file())
            self.assertTrue(compile_link["chain_requested"], msg=compile_link)
            self.assertEqual(compile_link["chain_command"], "ALINK MAIN", msg=compile_link)
            self.assert_workflow_overlay_loaded(compile_link, True)

            compile_debug = self.run_tool("ACTC", workspace, "MAIN:")
            self.assertTrue(compile_debug["chain_requested"], msg=compile_debug)
            self.assertEqual(compile_debug["chain_command"], "ALINK MAIN:", msg=compile_debug)
            self.assert_workflow_overlay_loaded(compile_debug, True)

            link_only = self.run_tool("ALINK", workspace, "MAIN")
            self.assertFalse(link_only["chain_requested"], msg=link_only)
            self.assertTrue((workspace / "bin" / "MAIN.PRG").is_file())
            self.assertTrue((workspace / "bin" / "MAIN.DBG").is_file())

            link_debug = self.run_tool("ALINK", workspace, "MAIN:")
            self.assertTrue(link_debug["chain_requested"], msg=link_debug)
            self.assertEqual(link_debug["chain_command"], "ACTDBG MAIN", msg=link_debug)

    def test_compile_failures_return_to_editor_source_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "project"
            for directory in ("src", "obj", "bin", "lib"):
                (workspace / directory).mkdir(parents=True, exist_ok=True)
            (workspace / "ACTION.PROJ").write_text(
                "ACTION PROJECT\rMAIN.ACT\r",
                encoding="ascii",
            )
            (workspace / "src" / "main.act").write_text(
                "MODULE MAIN\rPROC MAIN()\rMAIN()\rRETURN\r",
                encoding="ascii",
            )

            bare = self.run_tool("ACTC", workspace, "MAIN", expected_status=1)
            self.assertFalse(bare["chain_requested"], msg=bare)
            self.assertEqual(bare["console"], "BAD PROC\n", msg=bare)
            self.assert_workflow_overlay_loaded(bare, False)

            for suffix in (";", ",", ":"):
                with self.subTest(suffix=suffix):
                    summary = self.run_tool("ACTC", workspace, f"MAIN{suffix}")
                    self.assertTrue(summary["chain_requested"], msg=summary)
                    self.assertEqual(summary["chain_command"], "ACTEDIT MAIN:3", msg=summary)
                    self.assertEqual(summary["console"], "BAD PROC\n", msg=summary)
                    self.assert_workflow_overlay_loaded(summary, True)
            self.assertFalse((workspace / "obj" / "MAIN.OBJ").exists())

    def test_compile_failure_line_crosses_reu_source_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "project"
            for directory in ("src", "obj", "bin", "lib"):
                (workspace / directory).mkdir(parents=True, exist_ok=True)
            (workspace / "ACTION.PROJ").write_text(
                "ACTION PROJECT\rMAIN.ACT\r",
                encoding="ascii",
            )
            source = "MODULE MAIN\rPROC MAIN()\r" + ("\r" * 1300) + "MAIN()\rRETURN\r"
            self.assertGreater(len(source), 1280)
            (workspace / "src" / "main.act").write_text(source, encoding="ascii")

            summary = self.run_tool("ACTC", workspace, "MAIN;")
            self.assertTrue(summary["chain_requested"], msg=summary)
            self.assertEqual(summary["chain_command"], "ACTEDIT MAIN:1303", msg=summary)
            self.assert_workflow_overlay_loaded(summary, True)

    def test_compile_failure_editor_return_rejects_overlength_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "project"
            for directory in ("src", "obj", "bin", "lib"):
                (workspace / directory).mkdir(parents=True, exist_ok=True)
            module = "ABCDEFGHIJKLMNOPQRSTUV"
            (workspace / "ACTION.PROJ").write_text(
                f"ACTION PROJECT\r{module}.ACT\r",
                encoding="ascii",
            )
            (workspace / "src" / f"{module.lower()}.act").write_text(
                f"MODULE {module}\rPROC MAIN()\rMAIN()\rRETURN\r",
                encoding="ascii",
            )

            summary = self.run_tool("ACTC", workspace, f"{module};", expected_status=1)
            self.assertFalse(summary["chain_requested"], msg=summary)
            self.assert_workflow_overlay_loaded(summary, True)
            self.assertEqual(
                summary["console"],
                "BAD PROC\nEDIT RETURN FAILED\n",
                msg=summary,
            )
