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
        for tool in ["make", "c1541"]:
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
        listing = self.listing.read_text(encoding="ascii").lower()
        required_entries = [
            "udosboot",
            "udoscore",
            "alink.prg",
        ]

        for required in required_entries:
            self.assertIn(required, listing, msg=listing)

        self.assertNotIn("actsave.prg", listing)
        for workspace_only_tool in [
            "actc.prg",
            "actc_ovl0.bin",
            "actc_ovl1.bin",
            "actc_ovl2.bin",
            "actc_ovl3.bin",
            "actc_ovl4.bin",
            "actc_ovl5.bin",
            "actc_ovl6.bin",
            "actc_ovl7.bin",
            "actc_ovl8.bin",
            "actc_ovl9.bin",
            "actc_ovla.bin",
            "actc_ovlb.bin",
            "actc_ovlc.bin",
            "actc_ovld.bin",
            "actc_ovle.bin",
            "actc_ovlf.bin",
            "actc_ovlg.bin",
            "actc_ovlh.bin",
            "actdel.prg",
            "actdir.prg",
            "tree.ovl",
            "xcopy.ovl",
            "deltree.ovl",
            "act2save.prg",
            "actmon.prg",
            "actfile.prg",
            "actinfo.prg",
            "actedit.prg",
            "actedit_ovl1.bin",
            "actdbg.prg",
            "actdbg_ovl1.bin",
            "actdbg_ovl2.bin",
            "actmkdir.prg",
            "actmove.prg",
            "actnew.prg",
            "actrmdir.prg",
            "actsrc.prg",
            "actwrite.prg",
        ]:
            self.assertNotIn(workspace_only_tool, listing)

        action_root = (
            self.root.parent / "udos" / "build" / "udos-release-fs" / "IMAGES" / "ACTION.DNP"
        )
        for complete_workspace_entry in [
            "ACTC.PRG",
            "ACTC_OVL0.BIN",
            "ACTC_OVL1.BIN",
            "ACTC_OVL2.BIN",
            "ACTC_OVL3.BIN",
            "ACTC_OVL4.BIN",
            "ACTC_OVL5.BIN",
            "ACTC_OVL6.BIN",
            "ACTC_OVL7.BIN",
            "ACTC_OVL8.BIN",
            "ACTC_OVL9.BIN",
            "ACTC_OVLA.BIN",
            "ACTMON.PRG",
            "ACTFILE.PRG",
            "ACTINFO.PRG",
            "ACTEDIT.PRG",
            "ACTEDIT_OVL1.BIN",
            "ACTDBG.PRG",
            "ACTDBG_OVL1.BIN",
            "ACTDBG_OVL2.BIN",
            "ACTCOPY.PRG",
            "ACTDEL.PRG",
            "ACTDIR.PRG",
            "TREE.OVL",
            "XCOPY.OVL",
            "DELTREE.OVL",
            "ACTC_OVLB.BIN",
            "ACTC_OVLC.BIN",
            "ACTC_OVLD.BIN",
            "ACTC_OVLE.BIN",
            "ACTC_OVLF.BIN",
            "ACTC_OVLG.BIN",
            "ACTC_OVLH.BIN",
            "ACTC_OVLI.BIN",
            "ACTC_OVLJ.BIN",
            "ACTC_OVLK.BIN",
            "ACTC_OVLL.BIN",
            "ACTC_OVLM.BIN",
            "ACTC_OVLN.BIN",
            "ACTC_OVLO.BIN",
            "ACTC_OVLP.BIN",
            "ACTC_OVLQ.BIN",
            "ACTC_OVLR.BIN",
            "ACTC_OVLS.BIN",
            "ACTC_OVLT.BIN",
            "ACTC_OVLU.BIN",
        ]:
            self.assertTrue((action_root / complete_workspace_entry).is_file())

        self.assertEqual((action_root / "ACTEDIT_OVL1.BIN").read_bytes()[:5], b"AEOV\x02")
        self.assertEqual((action_root / "ACTDBG_OVL1.BIN").read_bytes()[:4], b"DGOV")
        self.assertEqual((action_root / "ACTDBG_OVL2.BIN").read_bytes()[:4], b"DGOV")
        self.assertNotIn("actcopy.prg", listing)

        act2save = action_root / "ACT2SAVE.PRG"
        actsave = action_root / "ACTSAVE.PRG"
        self.assertTrue(act2save.is_file())
        self.assertTrue(actsave.is_file())
        self.assertEqual(actsave.read_bytes(), act2save.read_bytes())


if __name__ == "__main__":
    unittest.main()
