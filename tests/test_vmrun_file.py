from pathlib import Path
import subprocess
import sys
import unittest


class TestVmRunFile(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.pack_tool = self.root / "tools" / "avm_pack.py"
        self.build_script = self.root / "tools" / "build_vmrun.sh"
        self.runner = self.root / "tools" / "cpmemu_runner.py"
        self.example_text = self.root / "examples" / "hello.avm.txt"
        self.example_avm = self.root / "examples" / "hello.avm"
        self.out_com = self.root / "build" / "vm.com"

    def test_vmrun_file_smoke(self) -> None:
        selftest = subprocess.run(
            [sys.executable, str(self.pack_tool), "--selftest"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(selftest.returncode, 0, msg=selftest.stdout + selftest.stderr)

        pack = subprocess.run(
            [
                sys.executable,
                str(self.pack_tool),
                str(self.example_text),
                "--text",
                "--entry-offset",
                "0",
                "--output",
                str(self.example_avm),
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(pack.returncode, 0, msg=pack.stdout + pack.stderr)
        self.assertTrue(self.example_avm.is_file())

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
                str(self.root / "examples"),
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
        self.assertIn("HELLO FROM AVM FILE", run_output)


if __name__ == "__main__":
    unittest.main()
