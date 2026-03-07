from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestActcDeadStrip(unittest.TestCase):
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

    def read_map(self, path: Path) -> str:
        return path.read_bytes().replace(b"\x00", b"").decode("ascii")

    def test_print_only_skips_int_modules(self) -> None:
        self.build_tool(self.build_actc)
        self.build_tool(self.build_vm)
        with tempfile.TemporaryDirectory() as tmpdir:
            drive = Path(tmpdir)
            self.stage_drive(drive)
            (drive / "main.act").write_text('PROC main()\nPrintE("HELLO")\nRETURN\n', encoding="ascii")

            compile_result = self.run_cpm(drive, "actc.com")
            self.assertEqual(compile_result.returncode, 0, msg=compile_result.stdout + compile_result.stderr)
            map_text = self.read_map(drive / "main.map")
            self.assertIn("rt.print_line", map_text)
            self.assertIn("rt.print_str", map_text)
            self.assertNotIn("rt.format_int", map_text)
            self.assertNotIn("rt.f_", map_text)

    def test_printi_includes_int_module(self) -> None:
        self.build_tool(self.build_actc)
        self.build_tool(self.build_vm)
        with tempfile.TemporaryDirectory() as tmpdir:
            drive = Path(tmpdir)
            self.stage_drive(drive)
            (drive / "main.act").write_text(
                'PROC main()\nCARD x\nx = 7\nPrintIE(x)\nRETURN\n',
                encoding="ascii",
            )

            compile_result = self.run_cpm(drive, "actc.com")
            self.assertEqual(compile_result.returncode, 0, msg=compile_result.stdout + compile_result.stderr)
            map_text = self.read_map(drive / "main.map")
            self.assertIn("rt.format_int", map_text)


if __name__ == "__main__":
    unittest.main()
