from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class TestCompileFileIo(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.compiler = self.root / "tools" / "actionc64u_compile.py"
        self.build_vm = self.root / "tools" / "build_vmrun.sh"
        self.runner = self.root / "tools" / "cpmemu_runner.py"
        self.vm = self.root / "build" / "vm.com"

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

    def test_host_compiler_emits_file_copy_and_print_runtime_code(self) -> None:
        self.run_build()

        with tempfile.TemporaryDirectory() as tmpdir:
            drive = Path(tmpdir)
            source = drive / "main.act"
            avm = drive / "main.avm"
            source_text = drive / "source.txt"
            copied_text = drive / "copyout.txt"

            source.write_text(
                'PROC main()\nFileCopy("source.txt", "copyout.txt")\nFilePrint("copyout.txt")\nRETURN\n',
                encoding="ascii",
            )
            source_text.write_bytes(b"COMPILED FILE IO\r\n\x1a")

            compile_result = subprocess.run(
                [sys.executable, str(self.compiler), str(source), "--output", str(avm)],
                cwd=self.root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(compile_result.returncode, 0, msg=compile_result.stdout + compile_result.stderr)
            self.assertTrue(avm.is_file())
            self.assertTrue(avm.with_suffix(".avo").is_file())

            run_result = subprocess.run(
                [
                    sys.executable,
                    str(self.runner),
                    "--cwd",
                    str(drive),
                    str(self.vm),
                    avm.name,
                ],
                cwd=self.root,
                text=True,
                capture_output=True,
                check=False,
                timeout=20,
            )
            output = run_result.stdout + run_result.stderr

            self.assertEqual(run_result.returncode, 0, msg=output)
            self.assertIn("COMPILED FILE IO", output)
            self.assertTrue(copied_text.is_file(), msg=output)
            self.assertTrue(copied_text.read_bytes().startswith(b"COMPILED FILE IO\r\n"))


if __name__ == "__main__":
    unittest.main()
