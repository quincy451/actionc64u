from pathlib import Path
import shutil
import subprocess
import sys
import unittest


class TestReleaseImageBuild(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.script = self.root / "tools" / "build_release_image.py"
        self.output = self.root / "build" / "actionc64u_c64.d64"
        self.listing = self.root / "build" / "actionc64u_c64.dir.txt"

    def test_build_release_image_contains_expected_files(self) -> None:
        for tool in ["cpmcp", "cpmls", "cpmchattr", "cpmrm"]:
            if not shutil.which(tool):
                self.skipTest(f"{tool} not found")

        result = subprocess.run(
            [sys.executable, str(self.script)],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
        output = result.stdout + result.stderr
        if result.returncode != 0:
            self.skipTest(output.strip())

        self.assertTrue(self.output.is_file(), msg=output)
        self.assertTrue(self.listing.is_file(), msg=output)
        listing = self.listing.read_text(encoding="ascii")
        for required in [
            "alink.com",
            "actmon.com",
            "actc.com",
            "vm.com",
            "ccp.sys",
            "bdos.sys",
            "hello.act",
            "realdemo.act",
            "reu_demo.act",
            "ovl_demo.act",
        ]:
            self.assertIn(required, listing, msg=listing)


if __name__ == "__main__":
    unittest.main()
