from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class TestVmRunFileIo(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.pack_tool = self.root / "tools" / "avm_pack.py"
        self.runner = self.root / "tools" / "cpmemu_runner.py"
        self.build_vm = self.root / "tools" / "build_vmrun.sh"
        self.example_text = self.root / "examples" / "filecopy_runtime.avm.txt"
        self.out_vm = self.root / "build" / "vm.com"

    def run_build(self) -> None:
        result = subprocess.run(
            [str(self.build_vm)],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        output = result.stdout + result.stderr
        if result.returncode != 0:
            if result.returncode == 2 or "docs/blockers.md" in output:
                self.skipTest(f"required CP/M tool build unavailable: {output.strip()}")
            self.fail(output)

    def test_vmrun_can_copy_text_file_via_intrinsics(self) -> None:
        self.run_build()

        with tempfile.TemporaryDirectory() as tmpdir:
            drive = Path(tmpdir)
            avm_path = drive / "filecopy.avm"
            source_path = drive / "source.txt"
            copied_path = drive / "copyout.txt"

            source_path.write_bytes(b"VM FILE IO\r\n\x1a")

            pack = subprocess.run(
                [
                    sys.executable,
                    str(self.pack_tool),
                    str(self.example_text),
                    "--text",
                    "--output",
                    str(avm_path),
                ],
                cwd=self.root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(pack.returncode, 0, msg=pack.stdout + pack.stderr)
            self.assertTrue(avm_path.is_file())

            run_result = subprocess.run(
                [
                    sys.executable,
                    str(self.runner),
                    "--cwd",
                    str(drive),
                    str(self.out_vm),
                    avm_path.name,
                ],
                cwd=self.root,
                text=True,
                capture_output=True,
                check=False,
                timeout=20,
            )
            output = run_result.stdout + run_result.stderr

            self.assertEqual(run_result.returncode, 0, msg=output)
            self.assertIn("VM FILE IO", output)
            self.assertTrue(copied_path.is_file(), msg=output)
            self.assertTrue(copied_path.read_bytes().startswith(b"VM FILE IO\r\n"))


if __name__ == "__main__":
    unittest.main()
