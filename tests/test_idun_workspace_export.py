from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


class TestIdunWorkspaceExport(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def test_export_contains_linux_tools_without_udos_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "idun-action"
            result = subprocess.run(
                [
                    "python3",
                    str(self.root / "tools" / "export_idun_workspace.py"),
                    "--output",
                    str(out),
                ],
                cwd=self.root,
                text=True,
                capture_output=True,
                check=False,
                timeout=180,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue((out / "TOOLS" / "actnew").is_file())
            self.assertTrue((out / "TOOLS" / "actchk").is_file())
            self.assertTrue((out / "TOOLS" / "actcopy").is_file())
            self.assertTrue((out / "TOOLS" / "actmove").is_file())
            self.assertTrue((out / "TOOLS" / "actmon").is_file())
            self.assertTrue((out / "TOOLS" / "actdbg").is_file())
            self.assertTrue((out / "TOOLS" / "xcopy").is_file())
            self.assertTrue((out / "TOOLS" / "deltree").is_file())
            self.assertTrue((out / "TOOLS" / "actedit").is_file())
            self.assertTrue((out / "TOOLS" / "actc").is_file())
            self.assertTrue((out / "TOOLS" / "alink").is_file())
            self.assertTrue((out / "SRC").is_dir())
            self.assertTrue((out / "OBJ").is_dir())
            self.assertTrue((out / "BIN").is_dir())
            self.assertTrue((out / "LIB").is_dir())
            self.assertTrue((out / "LIB" / "RT_PRINT_I.OBJ").is_file())
            self.assertTrue((out / "LIB" / "RT_I_MUL.OBJ").is_file())
            self.assertTrue((out / "LIB" / "RT_I_DIV.OBJ").is_file())
            self.assertTrue((out / "LIB" / "RT_GFX_SCREEN_CELL.OBJ").is_file())
            self.assertTrue((out / "LIB" / "RT_GFX_COLOR_CELL.OBJ").is_file())
            for name in (
                "RT_GFX_VIC_BANK.OBJ",
                "RT_GFX_BGCOLOR.OBJ",
                "RT_GFX_BORDERCOLOR.OBJ",
                "RT_GFX_SCREEN_BASE.OBJ",
                "RT_GFX_BITMAP_BASE.OBJ",
                "RT_GFX_SCREEN_COPY.OBJ",
                "RT_GFX_COLOR_COPY.OBJ",
                "RT_GFX_BITMAP_FILL.OBJ",
                "RT_GFX_BITMAP_COPY.OBJ",
                "RT_GFX_BITMAP_ON.OBJ",
                "RT_GFX_BITMAP_OFF.OBJ",
                "RT_GFX_MBITMAP_ON.OBJ",
                "RT_GFX_MBITMAP_OFF.OBJ",
            ):
                self.assertTrue((out / "LIB" / name).is_file())
            for pattern in ("rt_sid_*.obj", "rt_sprite_*.obj"):
                for source in (self.root / "src" / "runtime" / "modules").glob(pattern):
                    self.assertTrue((out / "LIB" / source.name.upper()).is_file())
            for name in (
                "RT_JOY.OBJ",
                "RT_JS.OBJ",
                "RT_JP.OBJ",
                "RT_JB1.OBJ",
                "RT_JB2.OBJ",
                "RT_MS.OBJ",
                "RT_MP.OBJ",
                "RT_MSEEN.OBJ",
                "RT_MX.OBJ",
                "RT_MY.OBJ",
                "RT_MB.OBJ",
                "RT_MB1.OBJ",
                "RT_MB2.OBJ",
            ):
                self.assertTrue((out / "LIB" / name).is_file())
            for name in (
                "RT_OVL_LOAD.OBJ",
                "RT_PRINT_LINE.OBJ",
                "RT_PRINT_STR.OBJ",
                "RT_REU_COPY.OBJ",
                "RT_REU_FREE.OBJ",
                "RT_REU_PEEK32.OBJ",
                "RT_REU_POKE32.OBJ",
            ):
                self.assertFalse((out / "LIB" / name).exists())
            for name in (
                "RT_REU_ALLOC.OBJ",
                "RT_REU_STATE.OBJ",
                "RT_REU_RESOLVE.OBJ",
                "RT_REU_TRANSFER.OBJ",
                "RT_REU_PEEK8.OBJ",
                "RT_REU_PEEK16.OBJ",
                "RT_REU_POKE8.OBJ",
                "RT_REU_POKE16.OBJ",
            ):
                self.assertTrue((out / "LIB" / name).is_file())
            for name in (
                "RT_F_ABS.OBJ",
                "RT_F_ADD.OBJ",
                "RT_F_ADDSUB_CORE.OBJ",
                "RT_F_CMP.OBJ",
                "RT_F_DIV.OBJ",
                "RT_F_MAX.OBJ",
                "RT_F_MIN.OBJ",
                "RT_F_MUL.OBJ",
                "RT_F_SQRT.OBJ",
                "RT_F_SUB.OBJ",
                "RT_F_TO_I.OBJ",
                "RT_I_TO_F.OBJ",
                "RT_PRINT_F.OBJ",
                "RT_S_TO_F.OBJ",
            ):
                self.assertTrue((out / "LIB" / name).is_file())
            self.assertFalse(any((out / "LIB").glob("*.MOD")))
            self.assertTrue((out / "LIB" / "DBF1.ACT").is_file())
            self.assertTrue((out / "LIB" / "MATH1.ACT").is_file())
            for name in (
                "DBF1_DEMO.ACT",
            ):
                self.assertTrue((out / "SRC" / name).is_file())
            for name in (
                "MATH1_DEMO.ACT",
                "OVL_DEMO.ACT",
                "REAL_CMP.ACT",
                "REAL_DEMO.ACT",
                "REAL_MATH.ACT",
                "REU_DEMO.ACT",
            ):
                self.assertTrue((out / "SRC" / name).is_file())
            self.assertFalse((out / "UDOSDIR.TXT").exists())
            self.assertFalse((out / "TOOLS" / "ACTNEW.PRG").exists())
            self.assertFalse((out / "TOOLS" / "ACT2SAVE.PRG").exists())
            self.assertFalse((out / "TOOLS" / "ACTCOPY.PRG").exists())
            self.assertFalse((out / "TOOLS" / "ACTDBG.PRG").exists())
            self.assertFalse((out / "TOOLS" / "ACTMON.PRG").exists())
            self.assertFalse((out / "TOOLS" / "XCOPY.OVL").exists())

            exported_names = {path.name.upper() for path in out.rglob("*")}
            self.assertNotIn("UDOS_SERVICES.INC", exported_names)
            self.assertNotIn("UDOSDIR.TXT", exported_names)
            for name in (
                "RT_DBF_SAVE.OBJ",
                "RT_DBF_ADAPTER_STATE.OBJ",
                "RT_DBF_ENSURE_REU.OBJ",
                "RT_DBF_FILE_LOAD_REU.OBJ",
                "RT_DBF_RAW_REU_READ.OBJ",
                "RT_DBF_RAW_REU_WRITE.OBJ",
                "RT_DBF_FILE_OPEN_WRITE.OBJ",
                "RT_DBF_FILE_WRITE_BYTE.OBJ",
                "RT_DBF_FILE_CLOSE.OBJ",
            ):
                self.assertIn(name, exported_names)

            readme = (out / "DOC" / "README.txt").read_text(encoding="ascii")
            self.assertIn("does not require UDOS", readme)
            self.assertIn("Linux executables", readme)
            operator = (out / "DOC" / "operator.txt").read_text(encoding="ascii")
            self.assertIn("Run TOOLS/actc <module> and TOOLS/alink <module>", operator)
            self.assertIn("resolves referenced native OBJ1 exports", operator)
            self.assertIn("selects only each reachable export range", operator)
            self.assertIn("canonical one-character import indexes", operator)
            self.assertIn("rejects ambiguous providers", operator)
            self.assertIn("canonical source records", operator)
            self.assertIn("TOOLS/actedit <module> index, find <text>, or symbols", operator)
            self.assertIn(".action/workspace.sqlite3", operator)
            self.assertIn("TOOLS/actdbg <module> source <address>", operator)
            self.assertIn(".action/debug.sqlite3", operator)
            self.assertIn("Live C64 control is not active yet", operator)
            self.assertNotIn("will be Linux tools", operator)
            runtime_status = (out / "DOC" / "runtime-status.txt").read_text(encoding="ascii")
            self.assertIn("RT_GFX_SCREEN_CELL.OBJ", runtime_status)
            self.assertIn("Legacy placeholders not exported", runtime_status)
            self.assertIn("RT_REU_COPY.OBJ", runtime_status)
            self.assertIn("REAL and signed INT source lowering is active", runtime_status)
            self.assertIn("BYTE/CARD/INT/REAL arrays, typed pointers", runtime_status)
            self.assertIn("BYTE/CARD/INT/REAL user functions are active", runtime_status)
            self.assertIn("the first parameter/result ABI is not reentrant", runtime_status)
            self.assertIn("REU BYTE ARRAY allocation and 8/16-bit peek/poke are active", runtime_status)
            self.assertIn("OVERLAY blocks are active as resident program-owned PRG sections", runtime_status)
            self.assertIn("DBF1 compiler lowering and link-selected DBF modules are active", runtime_status)
            self.assertIn("DBF target execution remains hardware-unverified", runtime_status)


if __name__ == "__main__":
    unittest.main()
