from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestParityHostVsTarget(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.host_compiler = self.root / "tools" / "actionc64u_compile.py"
        self.build_actc = self.root / "tools" / "build_actc.sh"
        self.build_vm = self.root / "tools" / "build_vmrun.sh"
        self.runner = self.root / "tools" / "cpmemu_runner.py"
        self.parity_dir = self.root / "tests" / "parity"
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

    def compile_host(self, source: Path, output: Path) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(self.host_compiler),
                str(source),
                "--output",
                str(output),
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        message = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, msg=message)
        self.assertTrue(output.is_file(), msg=message)

    def run_vm(self, cwd: Path, avm_name: str) -> str:
        result = self.run_cpm(cwd, "vm.com", avm_name)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, msg=output)
        return output

    def test_host_and_target_outputs_match(self) -> None:
        self.build_tool(self.build_actc)
        self.build_tool(self.build_vm)

        cases = sorted(self.parity_dir.glob("*.act"))
        self.assertTrue(cases, "expected parity sources")

        for case in cases:
            with self.subTest(source=case.name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    drive = Path(tmpdir)
                    shutil.copy2(self.root / "build" / "actc.com", drive / "actc.com")
                    shutil.copy2(self.root / "build" / "vm.com", drive / "vm.com")
                    for manifest in self.libmods:
                        shutil.copy2(manifest, drive / manifest.name)
                    shutil.copy2(case, drive / "main.act")

                    host_avm = drive / "host.avm"
                    self.compile_host(drive / "main.act", host_avm)

                    target_compile = self.run_cpm(drive, "actc.com")
                    target_output = target_compile.stdout + target_compile.stderr
                    self.assertEqual(target_compile.returncode, 0, msg=target_output)
                    self.assertTrue((drive / "main.avm").is_file(), msg=target_output)

                    host_output = self.run_vm(drive, "host.avm")
                    target_output = self.run_vm(drive, "main.avm")
                    self.assertEqual(host_output, target_output)


if __name__ == "__main__":
    unittest.main()
