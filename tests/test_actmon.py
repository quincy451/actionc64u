from pathlib import Path
import subprocess
import tempfile
import unittest


class TestActmon(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.install_script = self.root / "tools" / "install_to_image.py"
        self.cpmemu = self.root.parent / "cpm65-u64" / "bin" / "cpmemu"

    def test_build_command_via_submit_flow(self) -> None:
        if not self.cpmemu.is_file():
            self.skipTest("cpmemu not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            drive = Path(tmpdir)
            install = subprocess.run(
                ["python3", str(self.install_script), str(drive)],
                cwd=self.root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(install.returncode, 0, msg=install.stdout + install.stderr)

            proc = subprocess.Popen(
                [str(self.cpmemu), str(drive / "actmon.com"), "build", "hello.act"],
                cwd=drive,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                stdout, stderr = proc.communicate(timeout=4)
            except subprocess.TimeoutExpired as exc:
                proc.kill()
                tail_out, tail_err = proc.communicate()
                stdout = (exc.stdout or "") + tail_out
                stderr = (exc.stderr or "") + tail_err

            output = stdout + stderr
            self.assertIn("HELLO FROM ACTIONC64U", output)
            self.assertTrue((drive / "hello.avm").is_file())
            self.assertTrue((drive / "hello.map").is_file())


if __name__ == "__main__":
    unittest.main()
