from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestAlinkOnTarget(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.compiler = self.root / "tools" / "actionc64u_compile.py"
        self.build_alink = self.root / "tools" / "build_alink.sh"
        self.build_vm = self.root / "tools" / "build_vmrun.sh"
        self.runner = self.root / "tools" / "cpmemu_runner.py"
        self.runtime_aliases = [
            ("rt_print_str.avo", "pstr.avo"),
            ("rt_print_line.avo", "plin.avo"),
            ("rt_format_int.avo", "fint.avo"),
            ("rt_ovl_call.avo", "ovlc.avo"),
            ("rt_ovl_load.avo", "ovll.avo"),
        ]

    def build_tool(self, script: Path) -> None:
        result = subprocess.run(
            [str(script)],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        output = result.stdout + result.stderr
        if result.returncode != 0:
            self.skipTest(f"required CP/M tool build unavailable: {output.strip()}")

    def compile_object(self, source_name: str, output_name: str) -> Path:
        output = self.root / "build" / output_name
        result = subprocess.run(
            [
                sys.executable,
                str(self.compiler),
                str(self.root / "examples" / source_name),
                "--output",
                str(output),
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertTrue(output.is_file())
        return output

    def run_cpm(self, cwd: Path, program: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(self.runner),
                "--cwd",
                str(cwd),
                program,
                *args,
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )

    def stage_drive(self, drive: Path, main_object: Path) -> None:
        shutil.copy2(self.root / "build" / "alink.com", drive / "alink.com")
        shutil.copy2(self.root / "build" / "vm.com", drive / "vm.com")
        shutil.copy2(main_object, drive / "main.avo")
        for source_name, alias_name in self.runtime_aliases:
            shutil.copy2(self.root / "src" / "runtime" / "modules" / source_name, drive / alias_name)

    def read_text_output(self, path: Path) -> str:
        return path.read_bytes().replace(b"\x00", b"").decode("ascii")

    def test_hello_links_and_deadstrips_integer_module(self) -> None:
        self.build_tool(self.build_alink)
        self.build_tool(self.build_vm)
        main_object = self.compile_object("hello.act", "alink-hello.avo")

        with tempfile.TemporaryDirectory() as tmpdir:
            drive = Path(tmpdir)
            self.stage_drive(drive, main_object)

            link_result = self.run_cpm(drive, "alink.com")
            self.assertEqual(link_result.returncode, 0, msg=link_result.stdout + link_result.stderr)
            self.assertTrue((drive / "main.avm").is_file())
            self.assertTrue((drive / "main.map").is_file())

            map_text = self.read_text_output(drive / "main.map")
            self.assertIn("rt.print_line", map_text)
            self.assertIn("rt.print_str", map_text)
            self.assertNotIn("rt.format_int", map_text)

            run_result = self.run_cpm(drive, "vm.com", "main.avm")
            self.assertEqual(run_result.returncode, 0, msg=run_result.stdout + run_result.stderr)
            self.assertIn("HELLO FROM ACTIONC64U", run_result.stdout + run_result.stderr)

    def test_math_links_and_pulls_integer_module(self) -> None:
        self.build_tool(self.build_alink)
        self.build_tool(self.build_vm)
        main_object = self.compile_object("math.act", "alink-math.avo")

        with tempfile.TemporaryDirectory() as tmpdir:
            drive = Path(tmpdir)
            self.stage_drive(drive, main_object)

            link_result = self.run_cpm(drive, "alink.com")
            self.assertEqual(link_result.returncode, 0, msg=link_result.stdout + link_result.stderr)
            map_text = self.read_text_output(drive / "main.map")
            self.assertIn("rt.format_int", map_text)

    def test_overlay_object_links_overlay_segment(self) -> None:
        self.build_tool(self.build_alink)
        self.build_tool(self.build_vm)
        main_object = self.compile_object("ovl_demo.act", "alink-ovl.avo")

        with tempfile.TemporaryDirectory() as tmpdir:
            drive = Path(tmpdir)
            self.stage_drive(drive, main_object)

            link_result = self.run_cpm(drive, "alink.com")
            self.assertEqual(link_result.returncode, 0, msg=link_result.stdout + link_result.stderr)

            avm_data = (drive / "main.avm").read_bytes()
            payload_len = int.from_bytes(avm_data[5:7], "little")
            payload = avm_data[10 : 10 + payload_len]
            self.assertIn(b"OVLT", payload)
            self.assertIn(b"overlay:Math\x00", payload)

            map_text = self.read_text_output(drive / "main.map")
            self.assertIn("rt.ovl_call", map_text)
            self.assertIn("rt.ovl_load", map_text)
            self.assertIn("overlays:", map_text)
            self.assertIn("Math", map_text)

            run_result = self.run_cpm(drive, "vm.com", "main.avm")
            self.assertEqual(run_result.returncode, 0, msg=run_result.stdout + run_result.stderr)
            self.assertIn("42", run_result.stdout + run_result.stderr)


if __name__ == "__main__":
    unittest.main()
