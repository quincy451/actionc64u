from pathlib import Path
import shutil
import subprocess
import sys
import unittest


class TestReleaseVerifyVice(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.script = self.root / "tools" / "verify_release.py"
        self.transcript = self.root / "build" / "verify_transcript.txt"

    def test_release_verification_succeeds_in_vice(self) -> None:
        for tool in ["x64sc", "cpmcp", "cpmls", "cpmchattr", "cpmrm"]:
            if not shutil.which(tool):
                self.skipTest(f"{tool} not found")

        result = subprocess.run(
            [sys.executable, str(self.script)],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=240,
        )
        output = result.stdout + result.stderr
        if result.returncode == 2:
            self.skipTest(output.strip())

        self.assertEqual(result.returncode, 0, msg=output)
        self.assertTrue(self.transcript.is_file(), msg=output)
        transcript = self.transcript.read_text(encoding="ascii")
        self.assertIn("HELLO FROM ACTIONC64U", transcript, msg=transcript)


if __name__ == "__main__":
    unittest.main()
