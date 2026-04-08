from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestToolAbiPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.script = self.root / "tools" / "run_tool_abi_additive_pipeline.py"
        self.base_fs = self.root.parent / "udos" / "build" / "udos-release-fs-manual-pipeline-44"

    def run_scenario(self, scenario: str, expected_console: str, expected_avo_size: int, expected_avm_size: int) -> None:
        for tool in ("cc", "ca65", "ld65", "make"):
            if shutil.which(tool) is None:
                self.skipTest(f"{tool} not found")

        if not self.base_fs.is_dir():
            self.skipTest(f"missing base fs tree: {self.base_fs}")

        with tempfile.TemporaryDirectory() as tmpdir:
            out_fs = Path(tmpdir) / "harness-additive"
            result = subprocess.run(
                [
                    sys.executable,
                    str(self.script),
                    "--scenario",
                    scenario,
                    "--out-fs",
                    str(out_fs),
                    "--keep-workspace",
                ],
                cwd=self.root,
                text=True,
                capture_output=True,
                check=False,
                timeout=300,
            )

            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, msg=output)

            summary = json.loads(result.stdout)
            self.assertEqual(summary["scenario"], scenario)
            workspace = Path(summary["workspace"])
            actc_object_path = Path(summary["actc_object_path"])
            alink_image_path = Path(summary["alink_image_path"])

            self.assertTrue(workspace.is_dir(), msg=output)
            self.assertTrue(actc_object_path.is_file(), msg=output)
            self.assertTrue(alink_image_path.is_file(), msg=output)
            self.assertEqual(summary["avmrun_console"], expected_console)
            self.assertEqual(actc_object_path.stat().st_size, expected_avo_size)
            self.assertEqual(alink_image_path.stat().st_size, expected_avm_size)

    def test_additive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("additive", "HELLO\nTOOL7\n5459\n", 92, 76)

    def test_precedence_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("precedence", "145\n", 53, 31)

    def test_comparisons_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("comparisons", "14\n5\n1\n1\nTOOL7\n", 91, 72)

    def test_procedure_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("procedures", "ONE\nTWO\n", 66, 39)


if __name__ == "__main__":
    unittest.main()
