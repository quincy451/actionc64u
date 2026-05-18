from pathlib import Path
import json
import os
import shutil
import subprocess
import tempfile
import unittest


class TestActcOverlay(unittest.TestCase):
    CTX_SIZE = 216

    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.build_dir = self.root / "build" / "udos_tools"

    def require_toolchain(self) -> None:
        for tool in ("ca65", "ld65"):
            if shutil.which(tool) is None:
                self.skipTest(f"{tool} not found")

    def run_checked(self, args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            args,
            cwd=self.root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return result

    def test_actc_compile_path_uses_decl_counts_overlay_when_enabled(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-compile"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "INT A=(8/2)+1+2*3\r"
                "BYTE B=[((1<2 AND 2<3) OR NOT(0=1))+1]\r"
                "PROC MAIN()\r"
                "PrintIE(A)\r"
                "PrintIE(B)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "8000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_context"][0:2], [5, 0], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL1.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL2.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL3.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL4.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL5.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("q 0 0 4 6\n", obj)
            self.assertIn("V g i 0 0 2 5\n", obj)
            self.assertIn("V g b 1 0 3 6\n", obj)
            self.assertIn("v a 11\n", obj)
            self.assertIn("v b 2\n", obj)

    def test_actc_compile_path_emits_param_and_local_debug_records(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-debug-vars"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "INT A\r"
                "PROC MAIN(P)\r"
                "INT L\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "8000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("V g i 0 0 2 5\n", obj)
            self.assertIn("V p i 0 1 0 3 11\n", obj)
            self.assertIn("V l i 0 2 0 4 5\n", obj)
            self.assertIn("v a 0\n", obj)
            self.assertIn("v p 0\n", obj)
            self.assertIn("v l 0\n", obj)

    def test_actc_compile_path_decl_overlay_pages_large_source(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-paged-compile"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rINT A=(8/2)+1+2*3\r"
            filler_len = 20600 - len(prefix)
            self.assertGreater(filler_len, 0)
            source = (
                prefix
                + ("\r" * filler_len)
                + "BYTE B=[1+1]\r"
                + "PROC MAIN()\r"
                + "PrintIE(A)\r"
                + "PrintIE(B)\r"
                + "RETURN\r"
            )
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_context"][0:2], [5, 0], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL1.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL2.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL3.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL4.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL5.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertRegex(obj, r"q 0 0 \d+ 6\n")
            self.assertRegex(obj, r"V g i 0 0 2 5\n")
            self.assertRegex(obj, r"V g b 1 0 \d+ 6\n")
            self.assertIn("v a 11\n", obj)
            self.assertIn("v b 2\n", obj)

    def test_actc_compile_path_uses_body_overlay_when_enabled(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-body-overlay-compile"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "PrintE(\"OK\")\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("l 0 0 0 3 1\n", obj)
            self.assertIn("l 0 1 0 4 1\n", obj)
            self.assertIn("b e0r\n", obj)
            self.assertIn("s OK\n", obj)

    def test_actc_compile_path_body_overlay_preserves_multiple_print_literal_indices(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-body-overlay-print-literals"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "PrintE(\"LT\")\r"
                "PrintE(\"EQ\")\r"
                "PrintI(1)\r"
                "PrintIE(2)\r"
                "PrintE(\"GE\")\r"
                "PrintE(\"NE\")\r"
                "PrintI(3)\r"
                "PrintIE(4)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            object_path = object_dir / "MAIN.OBJ"
            if not object_path.is_file():
                object_path = object_dir / "main.obj"
            obj = object_path.read_text(encoding="ascii")
            self.assertIn("b e0e1j0i1e2e3j2i3r\n", obj)
            self.assertIn("s LT\n", obj)
            self.assertIn("s EQ\n", obj)
            self.assertIn("s GE\n", obj)
            self.assertIn("s NE\n", obj)
            self.assertIn("i 1\n", obj)
            self.assertIn("i 2\n", obj)
            self.assertIn("i 3\n", obj)
            self.assertIn("i 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_add_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-body-overlay-real-add"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "REAL R\r"
                "PROC MAIN()\r"
                "R=A+B\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b L0U0L1U1u0T2S2r\n", obj)
            self.assertIn("u rt_f_add\n", obj)
            self.assertIn("V g r 0 0 2 6\n", obj)
            self.assertIn("V g r 1 0 3 6\n", obj)
            self.assertIn("V g r 2 0 4 6\n", obj)
            self.assertIn("v a 0 4\n", obj)
            self.assertIn("v b 0 4\n", obj)
            self.assertIn("v r 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_zero_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-body-overlay-real-zero"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=0\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b p0p0T0S0r\n", obj)
            self.assertIn("i 0\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_small_expr_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-body-overlay-real-small-expr"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=(1+2*3)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b p0p1T0S0r\n", obj)
            self.assertIn("i 0\n", obj)
            self.assertIn("i 16608\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_card_bridge_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-body-overlay-real-card-bridge"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "CARD A=[255]\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "A=A+1\r"
                "X=A\r"
                "PrintE(\"DONE\")\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b L0p0aS0L0u0T1S1e0r\n", obj)
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("i 1\n", obj)
            self.assertIn("v a 255\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_int_bridge_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-int-bridge"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "INT A=[0]\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "A=0-7\r"
                "X=A\r"
                "PrintE(\"DONE\")\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b p0p1mS0L0u0T1S1e0r\n", obj)
            self.assertIn("u rt_s_to_f\n", obj)
            self.assertIn("i 7\n", obj)
            self.assertIn("v a 0\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_large_positive_bridge_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-large-bridge"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=(255+1)\r"
                "PrintE(\"DONE\")\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("i 256\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_explicit_card_conversion(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-explicit-card"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "CARD A=[255]\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "A=A+1\r"
                "X=REAL(A)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("i 1\n", obj)
            self.assertIn("v a 255\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_print_with_newline(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-printre"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=REAL(7)\r"
                "PrintRE(X)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b p1u0T0S0L0U0p2u1r\n", obj)
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("u rt_print_f\n", obj)

    def test_actc_compile_path_body_overlay_handles_int_of_real_var(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-int-of-real-var"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "INT X\r"
                "PROC MAIN()\r"
                "A=REAL(7)\r"
                "X=INT(A)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("u rt_f_to_i\n", obj)
            self.assertIn("i 0\n", obj)
            self.assertIn("i 7\n", obj)
            self.assertIn("v x 0\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_large_positive_direct_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-large-direct-assignment"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "PROC MAIN()\r"
                "A=32767\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("i 32767\n", obj)
            self.assertIn("v a 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_fractional_real_print_with_newline(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-printre-fraction"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "A=REAL(3)\r"
                "B=REAL(2)\r"
                "X=A/B\r"
                "PrintRE(X)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b p1u0T0S0p3u0T1S1L0U0L1U1u1T2S2L2U2p4u2r\n", obj)
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("u rt_f_div\n", obj)
            self.assertIn("u rt_print_f\n", obj)
            self.assertIn("i 3\n", obj)
            self.assertIn("i 2\n", obj)
            self.assertIn("i 1\n", obj)
            self.assertIn("v a 0 4\n", obj)
            self.assertIn("v b 0 4\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_all_real_compare_ops(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-compare-all"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "REAL C\r"
                "PROC MAIN()\r"
                "A=REAL(1)\r"
                "B=REAL(2)\r"
                "C=REAL(2)\r"
                "IF A<B THEN\r"
                "PrintE(\"LT\")\r"
                "FI\r"
                "IF B=C THEN\r"
                "PrintE(\"EQ\")\r"
                "FI\r"
                "IF C>=B THEN\r"
                "PrintE(\"GE\")\r"
                "FI\r"
                "IF A<>C THEN\r"
                "PrintE(\"NE\")\r"
                "FI\r"
                "IF B>A THEN\r"
                "PrintE(\"GT\")\r"
                "FI\r"
                "IF A<=B THEN\r"
                "PrintE(\"LE\")\r"
                "FI\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("u rt_f_cmp\n", obj)
            self.assertIn("s LT\n", obj)
            self.assertIn("s EQ\n", obj)
            self.assertIn("s GE\n", obj)
            self.assertIn("s NE\n", obj)
            self.assertIn("s GT\n", obj)
            self.assertIn("s LE\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_wide_mul_bridge_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-wide-mul"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=(128*2)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("i 256\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_signed_wide_mul_bridge_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-signed-wide-mul"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=0-(128*2)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_s_to_f\n", obj)
            self.assertIn("i 65280\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_explicit_large_sum_conversion(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-explicit-sum"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=REAL(255+1)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("i 256\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_explicit_wide_mul_conversion(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-explicit-wide-mul"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=REAL(128*2)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("i 256\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_explicit_signed_wide_div_conversion(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-explicit-signed-wide-div"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=REAL(0-(512/2))\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_s_to_f\n", obj)
            self.assertIn("i 65280\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_explicit_signed_wide_mul_conversion(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-explicit-signed-wide-mul"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=REAL(0-(128*2))\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_s_to_f\n", obj)
            self.assertIn("i 65280\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_noop_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_noop.sh")])

        overlay = self.build_dir / "ACTC_OVL0.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], 1)
        self.assertEqual(data[5], 0)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))

        entry_offset = entry - load_base
        self.assertEqual(data[entry_offset], 0x8E)

    def test_source_header_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])

        overlay = self.build_dir / "ACTC_OVL1.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], 1)
        self.assertEqual(data[5], 1)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))

    def test_decl_counts_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])

        overlay = self.build_dir / "ACTC_OVL2.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], 1)
        self.assertEqual(data[5], 2)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))

    def test_payload_layout_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])

        overlay = self.build_dir / "ACTC_OVL3.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], 1)
        self.assertEqual(data[5], 3)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))

    def test_runtime_import_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])

        overlay = self.build_dir / "ACTC_OVL4.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], 1)
        self.assertEqual(data[5], 4)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))

    def test_actc_compile_path_maps_referenced_hardware_builtins_to_runtime_objs(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-hardware-builtins"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "SpriteOn(2)\r"
                "SpriteColor(2,5)\r"
                "SpritePos(2,52,86)\r"
                "SpriteData(2,64)\r"
                "SetSpriteMC(5,10)\r"
                "SidFreq(1,52)\r"
                "SidPulse(1,52)\r"
                "SidWave(1,64)\r"
                "SidAD(1,151)\r"
                "SidSR(1,248)\r"
                "SidOn(1)\r"
                "SidOff(1)\r"
                "SidRst()\r"
                "SndRst()\r"
                "SidRoute(7)\r"
                "SidRes(10)\r"
                "SidVol(10)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_sprite_on\n", obj)
            self.assertIn("u rt_sprite_color\n", obj)
            self.assertIn("u rt_sprite_pos\n", obj)
            self.assertIn("u rt_sprite_data\n", obj)
            self.assertIn("u rt_sprite_set_mc\n", obj)
            self.assertIn("u rt_sid_freq\n", obj)
            self.assertIn("u rt_sid_pulse\n", obj)
            self.assertIn("u rt_sid_wave\n", obj)
            self.assertIn("u rt_sid_ad\n", obj)
            self.assertIn("u rt_sid_sr\n", obj)
            self.assertIn("u rt_sid_on\n", obj)
            self.assertIn("u rt_sid_off\n", obj)
            self.assertIn("u rt_sid_rst\n", obj)
            self.assertIn("u rt_sid_route\n", obj)
            self.assertIn("u rt_sid_res\n", obj)
            self.assertIn("u rt_sid_vol\n", obj)
            self.assertNotIn("u spriteon\n", obj)
            self.assertNotIn("u spritecolor\n", obj)
            self.assertNotIn("u spritepos\n", obj)
            self.assertNotIn("u spritedata\n", obj)
            self.assertNotIn("u setspritemc\n", obj)
            self.assertNotIn("u sidfreq\n", obj)
            self.assertNotIn("u sidpulse\n", obj)
            self.assertNotIn("u sidwave\n", obj)
            self.assertNotIn("u sidad\n", obj)
            self.assertNotIn("u sidsr\n", obj)
            self.assertNotIn("u sidon\n", obj)
            self.assertNotIn("u sidoff\n", obj)
            self.assertNotIn("u sidrst\n", obj)
            self.assertNotIn("u sndrst\n", obj)
            self.assertNotIn("u sidroute\n", obj)
            self.assertNotIn("u sidres\n", obj)
            self.assertNotIn("u sidvol\n", obj)
            self.assertNotIn("u rt_sprite_off\n", obj)

    def test_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        overlay = self.build_dir / "ACTC_OVL5.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], 1)
        self.assertEqual(data[5], 5)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))

    def test_body_collect_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        overlay = self.build_dir / "ACTC_OVL6.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], 1)
        self.assertEqual(data[5], 6)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))

    def test_actc_runner_stages_copies_banks_and_calls_noop_overlay(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_noop.sh")])
        overlay_data = (self.build_dir / "ACTC_OVL0.BIN").read_bytes()
        overlay_memcfg_seen_addr = 0xA000 + len(overlay_data) - 1

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "overlay-runner"
            workspace.mkdir()
            shutil.copyfile(self.build_dir / "ACTC_OVL0.BIN", workspace / "ACTC_OVL0.BIN")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(workspace),
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--entry-label",
                    "actc_overlay_run_pass",
                    "--reg-a",
                    "0",
                    "--poke-byte",
                    "0x0001=0x37",
                    "--dump",
                    "0x0001:1",
                    "--dump",
                    "actc_overlay_loaded_len:2",
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--dump",
                    "actc_overlay_service_status:1",
                    "--dump",
                    "actc_overlay_memcfg_before_call:1",
                    "--dump",
                    "actc_overlay_memcfg_after_restore:1",
                    "--dump",
                    f"0x{overlay_memcfg_seen_addr:04X}:1",
                    "--max-steps",
                    "200000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertTrue(summary["exited"], msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["registers"]["a"], 0, msg=result.stdout)
            self.assertEqual(summary["dumps"]["0x0001"], [0x37], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [0], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_context"][0:2], [0, 0], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_service_status"], [1], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_memcfg_before_call"], [0x36], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_memcfg_after_restore"], [0x37], msg=result.stdout)
            self.assertEqual(summary["dumps"][f"0x{overlay_memcfg_seen_addr:04X}"], [0x36], msg=result.stdout)

            loaded_len = summary["dumps"]["actc_overlay_loaded_len"]
            self.assertEqual(loaded_len[0] | (loaded_len[1] << 8), (self.build_dir / "ACTC_OVL0.BIN").stat().st_size)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL0.BIN" and op["params"][2:5] == [0, 0, 2] for op in summary["ops"]),
                msg=result.stdout,
            )

    def test_actc_runner_calls_source_header_overlay_with_source_context(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "overlay-source-header"
            workspace.mkdir()
            shutil.copyfile(self.build_dir / "ACTC_OVL1.BIN", workspace / "ACTC_OVL1.BIN")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(workspace),
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--entry-label",
                    "actc_overlay_run_pass",
                    "--reg-a",
                    "1",
                    "--poke-byte",
                    "0x0001=0x37",
                    "--poke-cstr",
                    "module_name=MAIN",
                    "--poke-cstr",
                    "source_buffer=  MODULE MAIN\r",
                    "--poke-word",
                    "source_window_len=14",
                    "--poke-word",
                    "source_total_len=14",
                    "--dump",
                    "0x0001:1",
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--dump",
                    "actc_overlay_memcfg_before_call:1",
                    "--dump",
                    "actc_overlay_memcfg_after_restore:1",
                    "--max-steps",
                    "200000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertTrue(summary["exited"], msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["registers"]["a"], 0, msg=result.stdout)
            self.assertEqual(summary["dumps"]["0x0001"], [0x37], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [1], msg=result.stdout)
            context = summary["dumps"]["actc_overlay_context"]
            self.assertEqual(context[0:2], [1, 0], msg=result.stdout)
            self.assertEqual(context[2:5], [9, 0, 0], msg=result.stdout)
            self.assertEqual(context[5:8], [0, 0, 1], msg=result.stdout)
            self.assertEqual(context[15:20], [14, 0, 14, 0, 0], msg=result.stdout)
            self.assertNotEqual(context[46:48], [0, 0], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_memcfg_before_call"], [0x36], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_memcfg_after_restore"], [0x37], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL1.BIN" and op["params"][2:5] == [0, 0, 2] for op in summary["ops"]),
                msg=result.stdout,
            )

    def test_actc_runner_rejects_mismatched_source_header_overlay_module(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "overlay-source-header-bad-module"
            workspace.mkdir()
            shutil.copyfile(self.build_dir / "ACTC_OVL1.BIN", workspace / "ACTC_OVL1.BIN")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(workspace),
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--entry-label",
                    "actc_overlay_run_pass",
                    "--reg-a",
                    "1",
                    "--poke-byte",
                    "0x0001=0x37",
                    "--poke-cstr",
                    "module_name=MAIN",
                    "--poke-cstr",
                    "source_buffer=MODULE OTHER\r",
                    "--poke-word",
                    "source_window_len=13",
                    "--poke-word",
                    "source_total_len=13",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "200000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertTrue(summary["exited"], msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["registers"]["a"], 2, msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_context"][0:2], [1, 2], msg=result.stdout)
            self.assertNotEqual(summary["dumps"]["actc_overlay_context"][11:13], [0, 0], msg=result.stdout)

    def test_actc_runner_calls_decl_counts_overlay_with_source_context(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])

        source = "MODULE MAIN\rINT A=(8/2)+1+2*3\rBYTE B=[((1<2 AND 2<3) OR NOT(0=1))+1]\rREAL R\rPROC MAIN(P,Q)\rINT L=[P+1]\rREAL Z\rRETURN\rPROC HELP()\rBYTE H\rRETURN\r"
        source_len = len(source)

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "overlay-decl-counts"
            workspace.mkdir()
            shutil.copyfile(self.build_dir / "ACTC_OVL2.BIN", workspace / "ACTC_OVL2.BIN")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(workspace),
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--entry-label",
                    "actc_overlay_run_pass",
                    "--reg-a",
                    "2",
                    "--poke-byte",
                    "0x0001=0x37",
                    "--poke-cstr",
                    f"source_buffer={source}",
                    "--poke-word",
                    f"source_window_len={source_len}",
                    "--poke-word",
                    f"source_total_len={source_len}",
                    "--dump",
                    "0x0001:1",
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--dump",
                    "actc_overlay_memcfg_before_call:1",
                    "--dump",
                    "actc_overlay_memcfg_after_restore:1",
                    "--dump",
                    "var_count_data:1",
                    "--dump",
                    "module_var_count_data:1",
                    "--dump",
                    "export_count_data:1",
                    "--max-steps",
                    "350000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertTrue(summary["exited"], msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["registers"]["a"], 0, msg=result.stdout)
            self.assertEqual(summary["dumps"]["0x0001"], [0x37], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [2], msg=result.stdout)
            context = summary["dumps"]["actc_overlay_context"]
            self.assertEqual(context[0:2], [2, 0], msg=result.stdout)
            self.assertEqual(context[2:5], [source_len & 0xFF, source_len >> 8, 0], msg=result.stdout)
            self.assertEqual(context[5:8], [0, 0, 1], msg=result.stdout)
            self.assertEqual(context[15:20], [source_len & 0xFF, source_len >> 8, source_len & 0xFF, source_len >> 8, 0], msg=result.stdout)
            self.assertEqual(context[20:22], [3, 2], msg=result.stdout)
            self.assertNotEqual(context[22:28], [0, 0, 0, 0, 0, 0], msg=result.stdout)
            self.assertNotEqual(context[28:36], [0, 0, 0, 0, 0, 0, 0, 0], msg=result.stdout)
            self.assertNotEqual(context[36:44], [0, 0, 0, 0, 0, 0, 0, 0], msg=result.stdout)
            self.assertEqual(summary["dumps"]["var_count_data"], [8], msg=result.stdout)
            self.assertEqual(summary["dumps"]["module_var_count_data"], [3], msg=result.stdout)
            self.assertEqual(summary["dumps"]["export_count_data"], [2], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_memcfg_before_call"], [0x36], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_memcfg_after_restore"], [0x37], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL2.BIN" and op["params"][2:5] == [0, 0, 2] for op in summary["ops"]),
                msg=result.stdout,
            )
            var_name_writes = [
                op for op in summary["ops"]
                if op["kind"] == "rwr" and op["params"][0:3] in ([0, 0xE4, 0], [25, 0xE4, 0], [50, 0xE4, 0], [75, 0xE4, 0], [100, 0xE4, 0], [125, 0xE4, 0], [150, 0xE4, 0], [175, 0xE4, 0])
            ]
            var_meta_writes = [
                op for op in summary["ops"]
                if op["kind"] == "rwr" and op["params"][0:3] in ([0, 0xE9, 0], [4, 0xE9, 0], [8, 0xE9, 0], [12, 0xE9, 0], [16, 0xE9, 0], [20, 0xE9, 0], [24, 0xE9, 0], [28, 0xE9, 0])
            ]
            export_name_writes = [
                op for op in summary["ops"]
                if op["kind"] == "rwr" and op["params"][0:3] in ([0, 0xE6, 0], [25, 0xE6, 0])
            ]
            proc_meta_writes = [
                op for op in summary["ops"]
                if op["kind"] == "rwr" and op["params"][0:3] in ([0, 0xEA, 0], [4, 0xEA, 0])
            ]
            self.assertEqual([op["head"][0:2] for op in var_name_writes], [[ord("A"), 0], [ord("B"), 0], [ord("R"), 0], [ord("P"), 0], [ord("Q"), 0], [ord("L"), 0], [ord("Z"), 0], [ord("H"), 0]], msg=result.stdout)
            self.assertEqual([op["head"][0:4] for op in var_meta_writes], [[11, 0, 2, ord("i")], [2, 0, 2, ord("b")], [0, 0, 4, ord("r")], [0, 0, 2, ord("i")], [0, 0, 2, ord("i")], [0, 0, 2, ord("i")], [0, 0, 4, ord("r")], [0, 0, 2, ord("b")]], msg=result.stdout)
            self.assertEqual(
                [bytes(op["head"][0:5]).rstrip(b"\x00").decode("ascii") for op in export_name_writes],
                ["MAIN", "HELP"],
                msg=result.stdout,
            )
            self.assertEqual(
                [op["head"][0:4] for op in proc_meta_writes],
                [[2, 3, 0, 5], [2, 3, 1, 5], [2, 3, 2, 5], [0, 7, 0, 7], [0, 7, 1, 7]],
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rrd" and op["params"][0:3] == [0, 0, 2] and op["params"][3:5] == [0, 0xA0] for op in summary["ops"]),
                msg=result.stdout,
            )

    def test_actc_runner_rejects_bad_decl_counts_overlay_sources(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])

        bad_sources = {
            "duplicate_module_var": "MODULE MAIN\rINT A\rBYTE A\rPROC MAIN()\rRETURN\r",
            "duplicate_proc_export": "MODULE MAIN\rPROC MAIN()\rRETURN\rPROC MAIN()\rRETURN\r",
            "duplicate_proc_param": "MODULE MAIN\rPROC MAIN(P,P)\rRETURN\r",
            "param_shadows_module": "MODULE MAIN\rINT A\rPROC MAIN(A)\rRETURN\r",
            "local_duplicates_param": "MODULE MAIN\rPROC MAIN(P)\rINT P\rRETURN\r",
            "duplicate_proc_local": "MODULE MAIN\rPROC MAIN()\rINT L\rBYTE L\rRETURN\r",
            "bad_module_var_name": "MODULE MAIN\rINT 1A\rPROC MAIN()\rRETURN\r",
            "bad_proc_tail": "MODULE MAIN\rPROC MAIN BAD\rRETURN\r",
            "empty_initializer": "MODULE MAIN\rINT A=\rPROC MAIN()\rRETURN\r",
            "unclosed_initializer": "MODULE MAIN\rINT A=[1\rPROC MAIN()\rRETURN\r",
            "trailing_operator_initializer": "MODULE MAIN\rINT A=[1+]\rPROC MAIN()\rRETURN\r",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "overlay-decl-rejects"
            workspace.mkdir()
            shutil.copyfile(self.build_dir / "ACTC_OVL2.BIN", workspace / "ACTC_OVL2.BIN")

            for name, source in bad_sources.items():
                with self.subTest(name=name):
                    source_len = len(source)
                    result = self.run_checked(
                        [
                            str(self.build_dir / "tool_abi_harness"),
                            "--prg",
                            str(self.build_dir / "ACTC.PRG"),
                            "--workspace",
                            str(workspace),
                            "--services-inc",
                            str(self.build_dir / "udos_services.inc"),
                            "--labels",
                            str(self.build_dir / "actc.current.labels"),
                            "--entry-label",
                            "actc_overlay_run_pass",
                            "--reg-a",
                            "2",
                            "--poke-byte",
                            "0x0001=0x37",
                            "--poke-cstr",
                            f"source_buffer={source}",
                            "--poke-word",
                            f"source_window_len={source_len}",
                            "--poke-word",
                            f"source_total_len={source_len}",
                            "--dump",
                            f"actc_overlay_context:{self.CTX_SIZE}",
                            "--max-steps",
                            "350000",
                        ]
                    )

                    summary = json.loads(result.stdout)
                    self.assertTrue(summary["exited"], msg=result.stdout)
                    self.assertFalse(summary["hit_limit"], msg=result.stdout)
                    self.assertEqual(summary["registers"]["a"], 2, msg=result.stdout)
                    self.assertEqual(summary["dumps"]["actc_overlay_context"][0:2], [2, 2], msg=result.stdout)

    def test_actc_runner_rejects_unknown_overlay_pass_id(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "overlay-runner"
            workspace.mkdir()
            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(workspace),
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--entry-label",
                    "actc_overlay_run_pass",
                    "--reg-a",
                    "127",
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "200000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertTrue(summary["exited"], msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["registers"]["a"], 1, msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [127], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_context"][0:2], [127, 2], msg=result.stdout)
            self.assertFalse(summary["ops"], msg=result.stdout)


if __name__ == "__main__":
    unittest.main()
