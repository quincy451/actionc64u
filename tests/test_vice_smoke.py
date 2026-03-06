from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from vice_harness import ViceHarness, ViceUnavailable, find_c64_disk_image, locate_x64sc  # noqa: E402


class TestViceSmoke(unittest.TestCase):
    def test_cpm65_boots_to_prompt_in_vice(self) -> None:
        try:
            x64sc_path = locate_x64sc()
            disk_image = find_c64_disk_image()
        except ViceUnavailable as exc:
            self.skipTest(str(exc))

        try:
            with ViceHarness(x64sc_path=x64sc_path, disk_image=disk_image) as vice:
                screen = vice.boot_to_cpm_prompt(timeout=120.0)
        except ViceUnavailable as exc:
            self.skipTest(str(exc))

        self.assertIn("A>", screen)


if __name__ == "__main__":
    unittest.main()
