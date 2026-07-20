from pathlib import Path
import json
import os
import shutil
import subprocess
import tempfile
import unittest


class TestActcDeadStrip(unittest.TestCase):
    CTX_SIZE = 231

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.build_dir = cls.root / "build" / "udos_tools"
        for tool in ("ca65", "ld65"):
            if shutil.which(tool) is None:
                raise unittest.SkipTest(f"{tool} not found")

        cls.run_checked([str(cls.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        build_env["ACTC_PREALLOCATE_BODY_EXTERNALS"] = "1"
        build_env["ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY"] = "1"
        cls.run_checked([str(cls.root / "tools" / "build_actc_udos.sh")], env=build_env)
        for script_name in (
            "build_actc_overlay_decl_counts.sh",
            "build_actc_overlay_source_header.sh",
            "build_actc_overlay_body_collect.sh",
            "build_actc_overlay_body_preallocate.sh",
            "build_actc_overlay_runtime_imports.sh",
            "build_actc_overlay_payload_layout.sh",
            "build_actc_overlay_emit_object.sh",
            "build_actc_overlay_emit_native_object.sh",
            "build_actc_overlay_emit_native_real_object.sh",
            "build_actc_overlay_emit_native_real_control_object.sh",
            "build_actc_overlay_emit_native_real_while_object.sh",
            "build_actc_overlay_emit_native_runtime_condition_object.sh",
            "build_actc_overlay_emit_native_runtime_sequence_object.sh",
            "build_actc_overlay_emit_native_runtime_nested_object.sh",
            "build_actc_overlay_emit_native_local_runtime_object.sh",
            "build_actc_overlay_emit_native_local_mixed_object.sh",
            "build_actc_overlay_emit_native_fixed_object.sh",
        ):
            cls.run_checked([str(cls.root / "tools" / script_name)])

    @classmethod
    def run_checked(
        cls,
        args: list[str],
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            args,
            cwd=cls.root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        return result

    def compile_object(self, source: str, workspace_name: str) -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / workspace_name
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8], [10]), msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL7.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            return (object_dir / "MAIN.OBJ").read_text(encoding="ascii")

    def object_imports(self, obj: str) -> set[str]:
        return {
            line.split(maxsplit=1)[1].strip()
            for line in obj.splitlines()
            if line.startswith("u ")
        }

    def test_print_only_skips_numeric_runtime_modules(self) -> None:
        obj = self.compile_object(
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "PrintE(\"HELLO\")\r"
            "RETURN\r",
            "actc-deadstrip-print-only",
        )

        imports = self.object_imports(obj)
        self.assertIn("x main ", obj)
        self.assertIn("s HELLO\n", obj)
        self.assertNotIn("rt_i_to_f", imports)
        self.assertNotIn("rt_print_f", imports)
        self.assertFalse(any(symbol.startswith("rt_f_") for symbol in imports), msg=obj)

    def test_printie_uses_inline_integer_print_without_runtime_modules(self) -> None:
        obj = self.compile_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "PROC MAIN()\r"
            "X=7\r"
            "PrintIE(X)\r"
            "RETURN\r",
            "actc-deadstrip-printie",
        )

        imports = self.object_imports(obj)
        self.assertEqual(imports, set(), msg=obj)
        self.assertIn("b p0S0L0zr\n", obj)
        self.assertIn("i 7\n", obj)

    def test_real_print_includes_only_needed_numeric_runtime_modules(self) -> None:
        obj = self.compile_object(
            "MODULE MAIN\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "X=REAL(7)\r"
            "PrintRE(X)\r"
            "RETURN\r",
            "actc-deadstrip-real-print",
        )

        imports = self.object_imports(obj)
        self.assertEqual(imports, {"rt_i_to_f", "rt_print_f"}, msg=obj)
        self.assertIn("rt_i_to_f", imports)
        self.assertIn("rt_print_f", imports)
        self.assertNotIn("rt_s_to_f", imports)
        self.assertFalse(any(symbol.startswith("rt_f_") for symbol in imports), msg=obj)


if __name__ == "__main__":
    unittest.main()
