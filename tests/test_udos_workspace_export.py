from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestUdosWorkspaceExport(unittest.TestCase):
    def test_export_creates_udos_tree_with_guides_examples_and_libs(self) -> None:
        root = Path(__file__).resolve().parents[1]
        tool = root / "tools" / "export_udos_workspace.py"

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "out"
            result = subprocess.run(
                [sys.executable, str(tool), "--output", str(output)],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            image_root = output / "IMAGES" / "ACTION.DNP"
            self.assertTrue(image_root.is_dir())

            expected_dirs = ["BIN", "DOC", "LIB", "SRC"]
            for name in expected_dirs:
                self.assertTrue((image_root / name).is_dir(), name)

            self.assertTrue((image_root / "README.TXT").is_file())
            self.assertIn("D BIN", (image_root / "UDOSDIR.TXT").read_text(encoding="ascii"))
            self.assertIn("F README.TXT", (image_root / "UDOSDIR.TXT").read_text(encoding="ascii"))

            docs_dir = image_root / "DOC"
            self.assertTrue((docs_dir / "OPERATOR.TXT").is_file())
            self.assertTrue((docs_dir / "LANGUAGE.TXT").is_file())
            self.assertTrue((docs_dir / "VMABI.TXT").is_file())
            self.assertTrue((docs_dir / "UDOSRESM.TXT").is_file())
            self.assertIn("ActionC64U Operator Guide", (docs_dir / "OPERATOR.TXT").read_text(encoding="ascii"))

            src_dir = image_root / "SRC"
            self.assertTrue((src_dir / "HELLO.ACT").is_file())
            self.assertTrue((src_dir / "MATH.ACT").is_file())
            self.assertIn("PROC main()", (src_dir / "HELLO.ACT").read_text(encoding="ascii"))

            bin_dir = image_root / "BIN"
            for name in ["HELLO.AVM", "REURUN.AVM", "VMECHO.AVM", "FILECOPY.AVM"]:
                self.assertEqual((bin_dir / name).read_bytes()[:4], b"AVM1", name)
            self.assertTrue((bin_dir / "HELLO.AVT").is_file())
            self.assertEqual((image_root / "HELLO.AVM").read_bytes()[:4], b"AVM1")
            self.assertEqual((bin_dir / "UDOSHELLO.AVM").read_bytes()[:4], b"AVM1")
            self.assertEqual((bin_dir / "UDOSHELLO.AVM").read_bytes()[9], 1)
            self.assertEqual((image_root / "UDOSHELLO.AVM").read_bytes()[9], 1)
            self.assertEqual((bin_dir / "UDOSFLOW.AVM").read_bytes()[:4], b"AVM1")
            self.assertEqual((bin_dir / "UDOSFLOW.AVM").read_bytes()[9], 1)
            self.assertEqual((image_root / "UDOSFLOW.AVM").read_bytes()[9], 1)

            lib_dir = image_root / "LIB"
            bundle = (lib_dir / "LIBMODS.DAT").read_text(encoding="ascii")
            self.assertIn("FILE libpstr.mod", bundle)
            self.assertTrue((lib_dir / "LIBPSTR.MOD").is_file())
            self.assertTrue((lib_dir / "RT_PRINT_STR.AVO").is_file())
            self.assertTrue((lib_dir / "UDOSDIR.TXT").is_file())

    def test_export_with_udos_tools_builds_actinfo_when_prereqs_exist(self) -> None:
        root = Path(__file__).resolve().parents[1]
        tool = root / "tools" / "export_udos_workspace.py"
        udos_labels = root.parent / "udos" / "build" / "udos-resident.labels"
        if not udos_labels.is_file():
            self.skipTest("UDOS resident labels not built")

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "out"
            result = subprocess.run(
                [sys.executable, str(tool), "--output", str(output), "--build-udos-tools"],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            image_root = output / "IMAGES" / "ACTION.DNP"
            self.assertTrue((image_root / "ACTDIR.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACTDIR.PRG").is_file())
            self.assertTrue((image_root / "ACTADD.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACTADD.PRG").is_file())
            self.assertTrue((image_root / "ACT2SAVE.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACT2SAVE.PRG").is_file())
            self.assertTrue((image_root / "ACTC.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACTC.PRG").is_file())
            self.assertTrue((image_root / "ALINK.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ALINK.PRG").is_file())
            self.assertTrue((image_root / "ACTCHK.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACTCHK.PRG").is_file())
            self.assertTrue((image_root / "ACTMON.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACTMON.PRG").is_file())
            self.assertTrue((image_root / "ACTFILE.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACTFILE.PRG").is_file())
            self.assertTrue((image_root / "ACTWORK.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACTWORK.PRG").is_file())
            self.assertTrue((image_root / "ACTFLOW.BAT").is_file())
            self.assertTrue((image_root / "ACTNEW.BAT").is_file())
            self.assertTrue((image_root / "ACTNEW.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACTNEW.PRG").is_file())
            self.assertTrue((image_root / "ACTSRC.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACTSRC.PRG").is_file())
            self.assertTrue((image_root / "PROJECT.TXT").is_file())
            self.assertTrue((image_root / "MAIN.ACT").is_file())
            actnew_lines = (image_root / "ACTNEW.BAT").read_text(encoding="ascii").splitlines()
            self.assertTrue(actnew_lines)
            self.assertTrue(all(len(line) <= 31 for line in actnew_lines if line))
            self.assertTrue((image_root / "ACTINFO.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACTINFO.PRG").is_file())
            self.assertTrue((image_root / "ACTCOPY.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACTCOPY.PRG").is_file())
            self.assertTrue((image_root / "ACTDEL.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACTDEL.PRG").is_file())
            self.assertTrue((image_root / "ACTMKDIR.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACTMKDIR.PRG").is_file())
            self.assertTrue((image_root / "ACTMOVE.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACTMOVE.PRG").is_file())
            self.assertTrue((image_root / "ACTRMDIR.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACTRMDIR.PRG").is_file())
            self.assertTrue((image_root / "ACTWRITE.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "ACTWRITE.PRG").is_file())
            self.assertTrue((image_root / "AVMINFO.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "AVMINFO.PRG").is_file())
            self.assertTrue((image_root / "AVMRUN.PRG").is_file())
            self.assertTrue((image_root / "BIN" / "AVMRUN.PRG").is_file())


if __name__ == "__main__":
    unittest.main()
