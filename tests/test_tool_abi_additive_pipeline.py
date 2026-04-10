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
        self.run_scenario("precedence", "145\n", 54, 31)

    def test_comparisons_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("comparisons", "14\n5\n1\n1\nTOOL7\n", 92, 72)

    def test_int_vars_basic_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("int_vars_basic", "0\n1\n", 55, 39)

    def test_int_vars_do_until_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("int_vars_do_until", "0\n1\nDONE\n", 73, 54)

    def test_int_vars_if_else_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("int_vars_if_else", "YES\nDONE\n", 96, 80)

    def test_int_vars_while_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("int_vars_while", "0\n1\nDONE\n", 73, 57)

    def test_int_vars_branch_calls_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("int_vars_branch_calls", "HELLO\nTOOL7\n", 131, 101)

    def test_int_vars_while_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("int_vars_while_external", "TOOL7\nDONE\n", 76, 72)

    def test_int_vars_multi_basic_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("int_vars_multi_basic", "0\n2\n3\n", 64, 47)

    def test_int_vars_multi_while_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("int_vars_multi_while", "0\n1\n2\n", 69, 54)

    def test_int_vars_multi_branch_calls_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("int_vars_multi_branch_calls", "HELLO\nTOOL7\n", 85, 66)

    def test_int_vars_multi_branch_shared_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("int_vars_multi_branch_shared_transitive", "MID1\nEND\nMID2\nEND\nDONE\n", 72, 87)

    def test_int_vars_multi_while_shared_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("int_vars_multi_while_shared_transitive", "MID1\nEND\nMID2\nEND\nDONE\n", 84, 100)

    def test_int_vars_multi_add_rhs_var_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("int_vars_multi_add_rhs_var", "3\n", 54, 35)

    def test_return_local_basic_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("return_local_basic", "2\n", 54, 25)

    def test_return_local_add_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("return_local_add", "5\n", 80, 33)

    def test_return_external_basic_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("return_external_basic", "7\n", 38, 25)

    def test_return_assign_local_var_expr_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("return_assign_local_var_expr", "1\n", 69, 37)

    def test_return_condition_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("return_condition_external", "OK\n", 54, 38)

    def test_return_external_add_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("return_external_add", "8\n", 46, 29)

    def test_comparison_ops_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("comparison_ops", "1\n1\n1\n1\n0\n0\n", 144, 91)

    def test_many_string_indices_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("many_string_indices", "A\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\n", 128, 143)

    def test_many_string_if_else_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("many_string_if_else", "I\nJ\nK\nL\nM\nN\nO\nP\n", 145, 156)

    def test_many_string_do_until_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("many_string_do_until", "A\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\n", 145, 153)

    def test_many_string_do_until_if_else_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("many_string_do_until_if_else", "I\nJ\nK\nL\nM\nN\nO\nP\n", 161, 166)

    def test_many_int_indices_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("many_int_indices", "0\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n14\n15\n16\n17\n18\n19\n", 183, 135)

    def test_many_int_if_else_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("many_int_if_else", "8\n9\n10\n11\n12\n13\n14\n15\n", 167, 124)

    def test_many_int_do_until_if_else_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("many_int_do_until_if_else", "8\n9\n10\n11\n12\n13\n14\n15\n", 183, 134)

    def test_comparison_ops_if_else_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("comparison_ops_if_else", "NE\nLT\nLE\nGE\n", 197, 149)

    def test_comparison_ops_loop_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("comparison_ops_loops", "DO\nDONE\n", 102, 76)

    def test_comparison_else_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("comparison_else", "YES\nDONE\n", 81, 62)

    def test_comparison_ops_branch_call_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("comparison_ops_branch_calls", "HELLO\nOK\n", 113, 77)

    def test_many_string_branch_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("many_string_branch_external", "TOOL7\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\n", 134, 155)

    def test_many_string_branch_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("many_string_branch_transitive", "MID\nEND\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\n", 134, 162)

    def test_many_string_nested_loops_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("many_string_nested_loops_external", "TOOL7\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\n", 138, 144)

    def test_many_string_branch_shared_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("many_string_branch_shared_transitive", "MID1\nEND\nMID2\nEND\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\n", 140, 181)

    def test_many_string17_branch_shared_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("many_string17_branch_shared_transitive", "MID1\nEND\nMID2\nEND\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\n", 165, 213)

    def test_dense_return_branch_shared_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("dense_return_branch_shared_transitive", "MID1\nEND\nMID2\nEND\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\n", 175, 227)

    def test_many_string_do_until_shared_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("many_string_do_until_shared_transitive", "MID1\nEND\nMID2\nEND\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\n", 120, 152)

    def test_many_string_nested_branch_shared_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("many_string_nested_branch_shared_transitive", "MID1\nEND\nMID2\nEND\nA\nB\nC\nD\nE\nF\nG\nH\n", 151, 178)

    def test_many_int_nested_loops_if_else_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("many_int_nested_loops_if_else", "8\n9\n10\n11\n12\n13\n14\n15\n", 199, 147)

    def test_many_string_nested_loops_if_else_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("many_string_nested_loops_if_else", "I\nJ\nK\nL\nM\nN\nO\nP\n", 177, 179)

    def test_branch_call_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("branch_calls", "HELLO\nDONE\n", 110, 69)

    def test_comparison_branch_call_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("comparison_branch_calls", "HELLO\nDONE\n", 119, 73)

    def test_nested_branch_call_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("nested_branch_calls", "HELLO\nDONE\n", 164, 102)

    def test_branch_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("branch_external", "TOOL7\nDONE\n", 80, 74)

    def test_nested_branch_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("nested_branch_external", "TOOL7\nDONE\n", 125, 104)

    def test_transitive_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("transitive_external", "START\nMID\nEND\nDONE\n", 57, 66)

    def test_transitive_branch_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("transitive_branch_external", "START\nMID\nEND\nDONE\n", 90, 93)

    def test_sibling_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("sibling_externals", "START\nMID1\nMID2\nDONE\n", 63, 68)

    def test_child_sibling_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("child_sibling_externals", "START\nMID\nEND1\nEND2\nDONE\n", 57, 82)

    def test_branch_transitive_local_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("branch_transitive_local", "LOCAL\nMID\nEND\nDONE\n", 108, 97)

    def test_repeated_root_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("repeated_root_externals", "START\nMID1\nMID2\nMID1\nDONE\n", 65, 71)

    def test_shared_transitive_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("shared_transitive_external", "START\nMID1\nEND\nMID2\nEND\nDONE\n", 63, 85)

    def test_branch_sibling_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("branch_sibling_externals", "MID1\nMID2\nDONE\n", 86, 83)

    def test_branch_shared_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("branch_shared_transitive", "MID1\nEND\nMID2\nEND\nDONE\n", 86, 100)

    def test_procedure_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("procedures", "ONE\nTWO\n", 66, 39)

    def test_if_block_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("if_blocks", "YES\nDONE\n", 86, 65)

    def test_else_block_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("else_blocks", "GOOD\nDONE\n", 74, 60)

    def test_nested_else_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("nested_else", "GOOD1\nDONE\n", 101, 86)

    def test_do_until_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("do_until", "BODY\nDONE\n", 66, 47)

    def test_do_until_call_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("do_until_calls", "HELLO\nTOOL7\nDONE\n", 91, 73)

    def test_do_until_if_else_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("do_until_if_else", "YES\nDONE\n", 98, 73)

    def test_do_until_branch_call_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("do_until_branch_calls", "HELLO\nDONE\n", 135, 83)

    def test_do_until_branch_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("do_until_branch_external", "TOOL7\nDONE\n", 96, 84)

    def test_nested_do_until_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("nested_do_until", "OUTER\nINNER\nDONE\n", 93, 70)

    def test_nested_do_until_call_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("nested_do_until_calls", "HELLO\nTOOL7\nDONE\n", 107, 83)

    def test_nested_do_until_if_else_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("nested_do_until_if_else", "OUTER\nINNER\nDONE\n", 141, 107)

    def test_nested_do_until_branch_mixed_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("nested_do_until_branch_mixed", "TOOL7\nHELLO\nDONE\n", 166, 135)

    def test_while_block_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("while_blocks", "DONE\n", 65, 49)

    def test_while_call_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("while_calls", "DONE\n", 91, 76)

    def test_while_if_else_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("while_if_else", "DONE\n", 100, 78)

    def test_while_branch_call_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("while_branch_calls", "DONE\n", 135, 86)

    def test_while_branch_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("while_branch_external", "DONE\n", 96, 87)

    def test_nested_while_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("nested_while", "DONE\n", 93, 76)

    def test_nested_while_call_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("nested_while_calls", "DONE\n", 107, 89)

    def test_nested_while_branch_mixed_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("nested_while_branch_mixed", "DONE\n", 166, 141)

    def test_while_shared_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("while_shared_transitive", "DONE\n", 69, 86)

    def test_do_until_nested_while_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("do_until_nested_while", "OUTER\nDONE\n", 93, 73)

    def test_while_nested_do_until_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("while_nested_do_until", "DONE\n", 93, 73)

    def test_do_until_nested_while_call_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("do_until_nested_while_calls", "HELLO\nDONE\n", 107, 86)

    def test_while_nested_do_until_call_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("while_nested_do_until_calls", "DONE\n", 107, 86)

    def test_do_until_nested_while_branch_mixed_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("do_until_nested_while_branch_mixed", "TOOL7\nDONE\n", 166, 138)

    def test_while_nested_do_until_shared_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("while_nested_do_until_shared_transitive", "DONE\n", 85, 96)

    def test_nested_if_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("nested_if", "INNERDONE\nOUTERDONE\n", 98, 77)

    def test_if_early_return_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("if_early_return", "START\nEARLY\n", 76, 62)

    def test_else_early_return_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("else_early_return", "EARLY\n", 76, 64)

    def test_do_until_early_return_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("do_until_early_return", "START\nEARLY\n", 77, 62)

    def test_while_early_return_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("while_early_return", "START\nEARLY\n", 77, 65)

    def test_nested_if_early_return_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("nested_if_early_return", "START\nEARLY\n", 121, 105)

    def test_if_return_local_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("if_return_local", "START\nHELLO\n", 94, 66)

    def test_if_return_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("if_return_external", "START\nTOOL7\n", 72, 66)

    def test_else_return_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("else_return_external", "TOOL7\n", 72, 68)

    def test_do_until_return_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("do_until_return_external", "START\nTOOL7\n", 73, 66)

    def test_while_return_local_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("while_return_local_external", "START\nHELLO\nTOOL7\n", 101, 85)

    def test_nested_if_return_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("nested_if_return_transitive", "START\nMID\nEND\n", 117, 121)

    def test_do_until_return_branch_mixed_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("do_until_return_branch_mixed", "START\nTOOL7\n", 126, 99)

    def test_nested_do_until_return_external_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("nested_do_until_return_external", "START\nTOOL7\n", 89, 76)

    def test_while_return_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("while_return_transitive", "START\nMID\nEND\n", 73, 81)

    def test_while_nested_do_until_return_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("while_nested_do_until_return_transitive", "START\nMID\nEND\n", 89, 91)

    def test_dense_mixed_nested_shared_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("dense_mixed_nested_shared_transitive", "MID2\nEND\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\n", 181, 223)

    def test_dense_return_nested_mixed_shared_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("dense_return_nested_mixed_shared_transitive", "MID1\nEND\nMID2\nEND\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\n", 182, 226)

    def test_dense_return_branch_nested_mixed_shared_transitive_pipeline_is_green_under_harness(self) -> None:
        self.run_scenario("dense_return_branch_nested_mixed_shared_transitive", "MID1\nEND\nMID2\nEND\nA\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\n", 208, 251)


if __name__ == "__main__":
    unittest.main()
