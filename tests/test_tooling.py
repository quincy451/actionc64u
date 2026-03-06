from pathlib import Path
import subprocess
import sys
import unittest


class TestTooling(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def test_path_probe(self) -> None:
        result = subprocess.run(
            [sys.executable, str(self.root / "tools" / "path_probe.py")],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("All required local paths resolved.", result.stdout)

    def test_env_check_non_destructive(self) -> None:
        result = subprocess.run(
            [str(self.root / "tools" / "env_check.sh")],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )

        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, msg=combined)
        self.assertIn("STATUS", result.stdout)
        self.assertIn("Summary:", result.stdout)
        self.assertRegex(combined, r"PASS|FAIL")


if __name__ == "__main__":
    unittest.main()
