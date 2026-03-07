from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestActcPrompt16OnTarget(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.build_actc = self.root / "tools" / "build_actc.sh"
        self.build_vm = self.root / "tools" / "build_vmrun.sh"
        self.runner = self.root / "tools" / "cpmemu_runner.py"
        self.libmods = sorted((self.root / "src" / "tools_cpm" / "libmods").glob("*.mod"))

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

    def stage_drive(self, drive: Path) -> None:
        shutil.copy2(self.root / "build" / "actc.com", drive / "actc.com")
        shutil.copy2(self.root / "build" / "vm.com", drive / "vm.com")
        for manifest in self.libmods:
            shutil.copy2(manifest, drive / manifest.name)

    def compile_and_run(self, source: Path) -> tuple[str, str]:
        with tempfile.TemporaryDirectory() as tmpdir:
            drive = Path(tmpdir)
            self.stage_drive(drive)
            shutil.copy2(source, drive / "main.act")

            compile_result = self.run_cpm(drive, "actc.com")
            compile_output = compile_result.stdout + compile_result.stderr
            self.assertEqual(compile_result.returncode, 0, msg=compile_output)

            run_result = self.run_cpm(drive, "vm.com", "main.avm")
            run_output = run_result.stdout + run_result.stderr
            self.assertEqual(run_result.returncode, 0, msg=run_output)

            map_text = (drive / "main.map").read_bytes().replace(b"\x00", b"").decode("ascii")
            return run_output, map_text

    def test_real_demo_uses_float_modules(self) -> None:
        self.build_tool(self.build_actc)
        self.build_tool(self.build_vm)
        output, map_text = self.compile_and_run(self.root / "examples" / "real_demo.act")
        self.assertIn("7.5", output)
        self.assertIn("rt.f_add", map_text)
        self.assertIn("rt.f_mul", map_text)
        self.assertIn("rt.i_to_f", map_text)
        self.assertIn("rt.print_f", map_text)

    def test_real_compare_uses_cmp_only(self) -> None:
        self.build_tool(self.build_actc)
        self.build_tool(self.build_vm)
        output, map_text = self.compile_and_run(self.root / "examples" / "real_cmp.act")
        self.assertIn("ok", output)
        self.assertIn("rt.f_cmp", map_text)
        self.assertNotIn("rt.print_f", map_text)

    def test_reu_demo_uses_sparse_reu_modules(self) -> None:
        self.build_tool(self.build_actc)
        self.build_tool(self.build_vm)
        output, map_text = self.compile_and_run(self.root / "examples" / "reu_demo.act")
        self.assertIn("reu ok", output)
        self.assertIn("rt.reu_alloc", map_text)
        self.assertIn("rt.reu_poke8", map_text)
        self.assertIn("rt.reu_peek8", map_text)
        self.assertNotIn("rt.ovl_call", map_text)

    def test_overlay_demo_tracks_overlay_modules(self) -> None:
        self.build_tool(self.build_actc)
        self.build_tool(self.build_vm)
        output, map_text = self.compile_and_run(self.root / "examples" / "ovl_demo.act")
        self.assertIn("42", output)
        self.assertIn("rt.ovl_load", map_text)
        self.assertIn("rt.ovl_call", map_text)
        self.assertIn("overlays:", map_text)
        self.assertIn("MATH", map_text)


if __name__ == "__main__":
    unittest.main()
