from pathlib import Path
import subprocess
import sys
import unittest


class TestCompileAndRun(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.compiler = self.root / "tools" / "actionc64u_compile.py"
        self.build_script = self.root / "tools" / "build_vmrun.sh"
        self.runner = self.root / "tools" / "cpmemu_runner.py"
        self.source = self.root / "examples" / "hello.act"
        self.output = self.root / "build" / "hello.avm"
        self.out_com = self.root / "build" / "vm.com"

    def test_compile_and_run(self) -> None:
        compile_result = subprocess.run(
            [
                sys.executable,
                str(self.compiler),
                str(self.source),
                "--output",
                str(self.output),
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        compile_output = compile_result.stdout + compile_result.stderr
        self.assertEqual(compile_result.returncode, 0, msg=compile_output)
        self.assertTrue(self.output.is_file())
        self.assertTrue(self.output.with_suffix(".avo").is_file())

        blob = self.output.read_bytes()
        self.assertGreaterEqual(len(blob), 10)
        self.assertEqual(blob[:4], b"AVM1")
        self.assertEqual(blob[4], 1)

        build_result = subprocess.run(
            [str(self.build_script)],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        build_output = build_result.stdout + build_result.stderr

        if build_result.returncode != 0:
            if build_result.returncode == 2 or "docs/blockers.md" in build_output:
                self.skipTest(
                    "vm.com build unavailable; see docs/blockers.md. "
                    f"Details: {build_output.strip()}"
                )
            self.fail(build_output)

        if not self.out_com.is_file():
            self.fail(f"build succeeded but {self.out_com} is missing")

        run_result = subprocess.run(
            [
                sys.executable,
                str(self.runner),
                "--cwd",
                str(self.root / "build"),
                str(self.out_com),
                "hello.avm",
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )
        run_output = run_result.stdout + run_result.stderr

        self.assertEqual(run_result.returncode, 0, msg=run_output)
        self.assertIn("HELLO FROM ACTIONC64U", run_output)


if __name__ == "__main__":
    unittest.main()
