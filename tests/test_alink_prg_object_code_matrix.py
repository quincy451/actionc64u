from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path


class TestAlinkPrgObjectCodeMatrix(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = Path(__file__).resolve().parents[2]
        self.make_text = (self.workspace / "udos" / "Makefile").read_text()

    def test_documented_broad_direct_prg_matrix_count_matches_probe_cases(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_count = len(probe.DIRECT_PRG_CASES)
        documented_counts = {
            "actionc64u/README.md": r"currently enumerates (\d+) direct-PRG object/link shapes",
            "actionc64u/docs/action_matrix.md": r"\| ALINK matrix \| (\d+) direct-PRG object/link shapes \|",
            "actionc64u/docs/alink_status.md": r"broad direct-PRG matrix currently enumerates (\d+) probe shapes",
            "actionc64u/docs/active_direction.md": (
                r"vice-action-alink-prg-matrix` as the broad direct-PRG object/link matrix;\s+"
                r"it currently enumerates (\d+) shape probes"
            ),
            "udos/BUILDING.md": r"currently enumerates (\d+) object/link shapes",
            "udos/STATUS_UDOS.md": r"vice-action-alink-prg-matrix` now enumerates (\d+) direct-PRG\s+object/link shapes",
        }

        for relative_path, pattern in documented_counts.items():
            with self.subTest(path=relative_path):
                text = (self.workspace / relative_path).read_text()
                match = re.search(pattern, text)
                self.assertIsNotNone(match, f"Missing documented ALINK matrix count in {relative_path}")
                self.assertEqual(
                    int(match.group(1)),
                    expected_count,
                    f"Documented ALINK matrix count in {relative_path} is stale",
                )

    def test_asmblock_byte_relocation_cases_cover_link_and_rejection(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        linked = probe.DIRECT_PRG_CASES[
            "actc_asmblock_symbol_byte_relocations_linked"
        ]
        rejected = probe.DIRECT_PRG_CASES[
            "object_code_reloc_unknown_byte_mode_rejects"
        ]
        imported = probe.DIRECT_PRG_CASES[
            "object_code_adjacent_byte_relocation_import"
        ]
        overlapping = probe.DIRECT_PRG_CASES[
            "object_code_overlapping_final_byte_relocations_rejects"
        ]

        self.assertIn("LDA #<RESULT", linked["source"])
        self.assertIn("LDA #>DONE", linked["source"])
        fragments = "".join(linked["expected_object_fragments"])
        self.assertIn("r 74 l x __v0\n", fragments)
        self.assertIn("r 96 h x __p0l0\n", fragments)
        self.assertTrue(linked["expected_tail_from_compiled_object"])
        self.assertTrue(rejected["expect_alink_failure"])
        self.assertEqual(rejected["expected_alink_error"], "BAD OBJECT")
        self.assertIn("r 1 lo u0\nr 2 hi u0\n", imported["seed_object"])
        self.assertEqual(imported["expected_alink_loads"], ["LIB/HELPER.OBJ"])
        self.assertIn("r 0 l x main\nr 0 h x main\n", overlapping["seed_object"])
        self.assertTrue(overlapping["expect_alink_failure"])

    def test_asmblock_symbol_addend_case_covers_native_compile_link_and_launch(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["actc_asmblock_symbol_addends_linked"]
        fragments = "".join(case["expected_object_fragments"])

        self.assertIn("PAIR+1", case["source"])
        self.assertIn("PAIR-1", case["source"])
        self.assertIn(" l x __v1 1\n", fragments)
        self.assertIn(" h x __v1 1\n", fragments)
        self.assertIn(" x __v1 -1\n", fragments)
        self.assertTrue(case["expected_tail_from_compiled_object"])
        self.assertEqual(case["expected_alink_loads"], [])
        self.assertEqual(
            case["extra_store_checks"],
            [
                {"addr": 0x033D, "value": 0x77},
                {"addr": 0x033E, "value": 0x45},
                {"addr": 0x033F, "value": 0x10},
            ],
        )

    def test_probe_oracle_accepts_selector_aliases_and_signed_addends(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        relocs = probe._obj_relocs(
            "OBJ1\nr 0 l u0 1\nr 1 hi x target -1\nr 2 x target 2\n",
            "test object",
        )
        self.assertEqual(
            relocs,
            [
                (0, "import", 0, "low", 1),
                (1, "local", "target", "high", -1),
                (2, "local", "target", "word", 2),
            ],
        )
        code = bytearray(4)
        probe._patch_obj_reloc(code, 0, 0x10FF, 1, "low", "test object")
        probe._patch_obj_reloc(code, 1, 0x1000, -1, "high", "test object")
        probe._patch_obj_reloc(code, 2, 0x1234, 2, "word", "test object")
        self.assertEqual(code, bytearray([0x00, 0x0F, 0x36, 0x12]))
        with self.assertRaisesRegex(RuntimeError, "relocation address out of range"):
            probe._patch_obj_reloc(bytearray(2), 0, 0xFFFF, 1, "word", "test object")

    def test_asmblock_real_storage_case_covers_native_link_and_launch(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["actc_asmblock_real_storage_linked"]
        fragments = "".join(case["expected_object_fragments"])

        self.assertIn("REAL GLOBAL", case["source"])
        self.assertIn("REAL LOCAL", case["source"])
        self.assertIn("LDX #0", case["source"])
        self.assertIn("LDX #3", case["source"])
        self.assertIn("x __v0 81 4\nx __v1 85 4\n", fragments)
        self.assertIn("x __idata 81 8\n", fragments)
        self.assertEqual(case["expected_alink_loads"], [])
        self.assertTrue(case["expected_tail_from_compiled_object"])
        self.assertEqual(case["store_check_addr"], 0x033C)
        self.assertEqual(case["store_check_value"], 0x11)
        self.assertEqual(
            case["extra_store_checks"],
            [
                {"addr": 0x033D, "value": 0x44},
                {"addr": 0x033E, "value": 0x22},
                {"addr": 0x033F, "value": 0x55},
            ],
        )

    def test_real_function_case_covers_pointer_return_copy_and_selective_runtime_link(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["actc_real_function_direct_return_linked"]
        fragments = "".join(case["expected_object_fragments"])

        self.assertIn("REAL FUNC VALUE()", case["source"])
        self.assertIn("RETURN(SOURCE)", case["source"])
        self.assertIn("RESULT=VALUE()", case["source"])
        self.assertIn("x main 0 76\nx value 61 5\n", fragments)
        self.assertIn("r 29 x value\n", fragments)
        self.assertIn("r 14 l x __v0\nr 18 h x __v0\n", fragments)
        self.assertEqual(case["runtime_library_objects"], ["rt_i_to_f"])
        self.assertEqual(case["expected_alink_loads"], ["LIB/RT_I_TO_F.OBJ"])
        self.assertTrue(case["expected_tail_from_compiled_object"])
        self.assertEqual(case["store_check_addr"], 0x1046)
        self.assertEqual(case["store_check_hi_addr"], 0x1047)
        self.assertEqual(
            case["extra_store_checks"],
            [
                {"addr": 0x1048, "value": 0x28},
                {"addr": 0x1049, "value": 0x42},
            ],
        )

    def test_real_function_nonfixed_storage_case_covers_captured_indexes(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["actc_real_function_nonfixed_storage_linked"]
        fragments = "".join(case["expected_object_fragments"])

        self.assertIn("REAL UNUSED\rREAL SOURCE\rREAL RESULT", case["source"])
        self.assertIn("x __v0 66 4\nx __v1 70 4\nx __v2 74 4\n", fragments)
        self.assertIn("x __idata 66 12\nx __iptr 78 2\n", fragments)
        self.assertIn("r 14 l x __v1\nr 18 h x __v1\n", fragments)
        self.assertIn("r 40 x __v2\n", fragments)
        self.assertEqual(case["runtime_library_objects"], ["rt_i_to_f"])
        self.assertEqual(case["expected_alink_loads"], ["LIB/RT_I_TO_F.OBJ"])
        self.assertTrue(case["expected_tail_from_compiled_object"])
        self.assertEqual(case["store_check_addr"], 0x104A)
        self.assertEqual(case["store_check_hi_addr"], 0x104B)
        self.assertEqual(
            case["extra_store_checks"],
            [
                {"addr": 0x104C, "value": 0x28},
                {"addr": 0x104D, "value": 0x42},
            ],
        )

    def test_real_function_mixed_width_case_covers_cumulative_offsets(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["actc_real_function_mixed_width_storage_linked"]
        fragments = "".join(case["expected_object_fragments"])

        self.assertIn("CARD UNUSED\rREAL SOURCE\rREAL RESULT", case["source"])
        self.assertIn("x __v0 66 2\nx __v1 68 4\nx __v2 72 4\n", fragments)
        self.assertIn("x __idata 66 10\nx __iptr 76 2\n", fragments)
        self.assertIn("r 14 l x __v1\nr 18 h x __v1\n", fragments)
        self.assertIn("r 40 x __v2\n", fragments)
        self.assertEqual(case["runtime_library_objects"], ["rt_i_to_f"])
        self.assertEqual(case["expected_alink_loads"], ["LIB/RT_I_TO_F.OBJ"])
        self.assertTrue(case["expected_tail_from_compiled_object"])
        self.assertEqual(case["store_check_addr"], 0x1048)
        self.assertEqual(case["store_check_hi_addr"], 0x1049)
        self.assertEqual(
            case["extra_store_checks"],
            [
                {"addr": 0x104A, "value": 0x28},
                {"addr": 0x104B, "value": 0x42},
            ],
        )

    def test_real_function_word_param_case_covers_binding_and_conversion(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["actc_real_function_word_param_linked"]
        fragments = "".join(case["expected_object_fragments"])

        self.assertIn("REAL FUNC VALUE(CARD P)", case["source"])
        self.assertIn("SOURCE=REAL(P)", case["source"])
        self.assertIn("RESULT=VALUE(42)", case["source"])
        self.assertIn("x main 0 126\nx value 69 45\n", fragments)
        self.assertIn("x __v2 122 2\n", fragments)
        self.assertIn("b u0M\nb u0M\n", fragments)
        self.assertIn("r 37 x value\nr 48 x __v1\n", fragments)
        self.assertIn("r 107 u0\n", fragments)
        self.assertEqual(case["runtime_library_objects"], ["rt_i_to_f"])
        self.assertEqual(case["expected_alink_loads"], ["LIB/RT_I_TO_F.OBJ"])
        self.assertTrue(case["expected_tail_from_compiled_object"])
        self.assertEqual(case["store_check_addr"], 0x1076)
        self.assertEqual(case["store_check_hi_addr"], 0x1077)
        self.assertIn({"addr": 0x107A, "value": 42}, case["extra_store_checks"])

    def test_real_function_variable_word_param_case_loads_named_storage(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["actc_real_function_variable_word_param_linked"]
        fragments = "".join(case["expected_object_fragments"])

        self.assertIn("CARD ARG", case["source"])
        self.assertIn("ARG=42", case["source"])
        self.assertIn("RESULT=VALUE(ARG)", case["source"])
        self.assertIn("x main 0 128\nx value 69 45\n", fragments)
        self.assertIn("x __v0 114 2\n", fragments)
        self.assertIn(
            "r 18 x __v0\nr 24 x __v0\nr 28 x __v0\nr 33 x __v0\n",
            fragments,
        )
        self.assertIn("r 37 x value\nr 48 x __v2\n", fragments)
        self.assertIn("r 107 u0\n", fragments)
        self.assertEqual(case["runtime_library_objects"], ["rt_i_to_f"])
        self.assertEqual(case["expected_alink_loads"], ["LIB/RT_I_TO_F.OBJ"])
        self.assertTrue(case["expected_tail_from_compiled_object"])
        self.assertEqual(case["store_check_addr"], 0x1078)
        self.assertIn({"addr": 0x1072, "value": 42}, case["extra_store_checks"])
        self.assertIn({"addr": 0x107C, "value": 42}, case["extra_store_checks"])

    def test_real_function_real_param_case_copies_four_byte_argument(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["actc_real_function_real_param_linked"]
        fragments = "".join(case["expected_object_fragments"])

        self.assertIn("REAL FUNC VALUE(REAL P)", case["source"])
        self.assertIn("ARG=REAL(42)", case["source"])
        self.assertIn("RESULT=VALUE(ARG)", case["source"])
        self.assertIn("x main 0 112\nx value 67 31\n", fragments)
        self.assertIn("x __v0 98 4\nx __v1 102 4\nx __v2 106 4\n", fragments)
        self.assertIn("r 29 l x __v0\nr 32 h x __v0\n", fragments)
        self.assertIn("r 88 x __v2\n", fragments)
        self.assertIn("r 94 l x __v2\nr 96 h x __v2\n", fragments)
        self.assertEqual(case["runtime_library_objects"], ["rt_i_to_f"])
        self.assertEqual(case["expected_alink_loads"], ["LIB/RT_I_TO_F.OBJ"])
        self.assertTrue(case["expected_tail_from_compiled_object"])
        self.assertEqual(case["store_check_addr"], 0x1066)
        self.assertIn({"addr": 0x1064, "value": 0x28}, case["extra_store_checks"])
        self.assertIn({"addr": 0x106C, "value": 0x28}, case["extra_store_checks"])

    def test_real_function_two_param_case_preserves_argument_order(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["actc_real_function_two_real_params_linked"]
        fragments = "".join(case["expected_object_fragments"])

        self.assertIn("REAL FUNC FIRST(REAL A,B)", case["source"])
        self.assertIn("RESULT=FIRST(LEFT,RIGHT)", case["source"])
        self.assertIn("x main 0 157\nx first 88 47\n", fragments)
        self.assertIn("r 104 x __v4\nr 120 x __v3\n", fragments)
        self.assertIn("r 131 l x __v3\nr 133 h x __v3\n", fragments)
        self.assertEqual(case["runtime_library_objects"], ["rt_i_to_f"])
        self.assertEqual(case["expected_alink_loads"], ["LIB/RT_I_TO_F.OBJ"])
        self.assertTrue(case["expected_tail_from_compiled_object"])
        self.assertEqual(case["store_check_addr"], 0x108F)
        self.assertIn({"addr": 0x1095, "value": 0x80}, case["extra_store_checks"])
        self.assertIn({"addr": 0x109A, "value": 0x40}, case["extra_store_checks"])

    def test_real_function_two_param_case_returns_second_parameter(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES[
            "actc_real_function_two_real_params_second_return_linked"
        ]
        fragments = "".join(case["expected_object_fragments"])

        self.assertIn("REAL RESULT\rREAL RIGHT\rREAL LEFT", case["source"])
        self.assertIn("REAL FUNC SECOND(REAL B,A)", case["source"])
        self.assertIn("RESULT=SECOND(LEFT,RIGHT)", case["source"])
        self.assertIn("r 104 x __v4\nr 120 x __v3\n", fragments)
        self.assertIn("r 131 l x __v4\nr 133 h x __v4\n", fragments)
        self.assertEqual(case["runtime_library_objects"], ["rt_i_to_f"])
        self.assertEqual(case["expected_alink_loads"], ["LIB/RT_I_TO_F.OBJ"])
        self.assertTrue(case["expected_tail_from_compiled_object"])
        self.assertEqual(case["store_check_addr"], 0x1089)
        self.assertEqual(case["store_check_hi_value"], 0x40)
        self.assertIn({"addr": 0x1095, "value": 0x80}, case["extra_store_checks"])
        self.assertIn({"addr": 0x109A, "value": 0x40}, case["extra_store_checks"])

    def test_real_function_finite_min_case_selects_runtime_closure(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["actc_real_function_finite_min_linked"]
        fragments = "".join(case["expected_object_fragments"])

        self.assertIn("REAL FUNC MIN2(REAL A,B)", case["source"])
        self.assertIn("IF B<A THEN\rRETURN(B)", case["source"])
        self.assertIn("x main 0 185\nx min2 88 75\n", fragments)
        self.assertIn("b u0u1M\nb u0M\n", fragments)
        self.assertIn("r 147 u0\n", fragments)
        self.assertEqual(
            case["runtime_library_objects"],
            ["rt_f_cmp", "rt_i_to_f", "rt_f_special"],
        )
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/RT_F_CMP.OBJ", "LIB/RT_I_TO_F.OBJ", "LIB/RT_F_SPECIAL.OBJ"],
        )
        self.assertTrue(case["expected_tail_from_compiled_object"])
        self.assertEqual(case["store_check_addr"], 0x10AB)
        self.assertIn({"addr": 0x10B1, "value": 0x00}, case["extra_store_checks"])
        self.assertIn({"addr": 0x10B5, "value": 0x80}, case["extra_store_checks"])

    def test_real_function_finite_min_permuted_case_tracks_named_storage(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES[
            "actc_real_function_finite_min_permuted_linked"
        ]
        fragments = "".join(case["expected_object_fragments"])

        self.assertIn("REAL RESULT\rREAL RIGHT\rREAL LEFT", case["source"])
        self.assertIn("REAL FUNC MIN2(REAL B,A)", case["source"])
        self.assertIn("r 14 l x __v2\nr 18 h x __v2\n", fragments)
        self.assertIn("r 67 x __v0\n", fragments)
        self.assertIn("r 131 l x __v3\nr 135 h x __v3\n", fragments)
        self.assertIn("r 139 l x __v4\nr 143 h x __v4\n", fragments)
        self.assertEqual(
            case["runtime_library_objects"],
            ["rt_f_cmp", "rt_i_to_f", "rt_f_special"],
        )
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/RT_F_CMP.OBJ", "LIB/RT_I_TO_F.OBJ", "LIB/RT_F_SPECIAL.OBJ"],
        )
        self.assertTrue(case["expected_tail_from_compiled_object"])
        self.assertEqual(case["store_check_addr"], 0x10A5)
        self.assertIn({"addr": 0x10B2, "value": 0x40}, case["extra_store_checks"])
        self.assertIn({"addr": 0x10B5, "value": 0x80}, case["extra_store_checks"])

    def test_full_range_multiply_probe_forces_staged_root_object_path(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["runtime_real_f_mul_full_range_helper_linked"]
        seed_object = str(case["seed_object"]).encode("ascii")

        self.assertGreater(len(seed_object), 512 + 255)
        self.assertGreaterEqual(str(case["seed_object"]).count("\nf "), 20)
        self.assertGreaterEqual(int(case["min_debug_sidecar_size"]), 256)
        self.assertGreaterEqual(probe.TOOL_ABI_HARNESS_MAX_STEPS, 40_000_000)
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/RT_F_MUL.OBJ", "LIB/RT_F_SPECIAL.OBJ"],
        )

    def test_full_range_division_probe_is_standalone_and_covers_boundaries(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["runtime_real_f_div_full_range_helper_linked"]

        self.assertEqual(case["runtime_library_objects"], ["rt_f_div", "rt_f_special"])
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/RT_F_DIV.OBJ", "LIB/RT_F_SPECIAL.OBJ"],
        )
        self.assertIn("LIB/RT_S_TO_F.OBJ", case["unexpected_alink_loads"])
        self.assertGreaterEqual(len(case["extra_store_checks"]), 4 * 26 - 2)

    def test_full_range_square_root_probe_is_standalone_and_covers_boundaries(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["runtime_real_f_sqrt_full_range_helper_linked"]

        self.assertEqual(case["runtime_library_objects"], ["rt_f_sqrt", "rt_f_special"])
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/RT_F_SQRT.OBJ", "LIB/RT_F_SPECIAL.OBJ"],
        )
        self.assertIn("LIB/RT_F_DIV.OBJ", case["unexpected_alink_loads"])
        self.assertGreaterEqual(len(case["extra_store_checks"]), 4 * 27 - 2)

    def test_full_range_real_print_probe_is_standalone_and_covers_formats(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["runtime_real_print_full_range_helper_linked"]

        self.assertEqual(case["runtime_library_objects"], ["rt_print_f"])
        self.assertEqual(case["expected_alink_loads"], ["LIB/RT_PRINT_F.OBJ"])
        self.assertIn("LIB/RT_F_DIV.OBJ", case["unexpected_alink_loads"])
        self.assertIn("0000001401298464324817070923729583289916", case["screen_fragments"])
        self.assertIn("340282346638528859811704183484516925440", case["screen_fragments"])
        self.assertIn("inf", case["screen_fragments"])
        self.assertIn("-inf", case["screen_fragments"])
        self.assertIn("nan", case["screen_fragments"])

    def test_unordered_relocation_probe_reverses_source_offsets(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["object_code_unordered_named_symbol_relocations"]
        reloc_offsets = [
            int(line.split()[1])
            for line in str(case["seed_object"]).splitlines()
            if line.startswith("r ")
        ]

        self.assertEqual(reloc_offsets, [4, 1])
        self.assertEqual(case["expected_alink_loads"], ["LIB/HELPER.OBJ"])

    def test_object_code_launch_groups_reference_valid_probe_shapes(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        groups = self._makefile_object_code_shape_groups(self.make_text)
        grouped_shapes = {shape for shapes in groups.values() for shape in shapes}
        direct_cases = set(probe.DIRECT_PRG_CASES)
        successful_object_cases = {
            shape
            for shape, case in probe.DIRECT_PRG_CASES.items()
            if shape.startswith("object_code_") and not bool(case.get("expect_alink_failure", False))
        }
        rejection_object_cases = {
            shape
            for shape, case in probe.DIRECT_PRG_CASES.items()
            if shape.startswith("object_code_") and bool(case.get("expect_alink_failure", False))
        }

        stale = sorted(grouped_shapes - direct_cases)
        non_object = sorted(shape for shape in grouped_shapes if not shape.startswith("object_code_"))
        missing_successful = sorted(successful_object_cases - grouped_shapes)
        grouped_rejections = sorted(rejection_object_cases & grouped_shapes)
        unrun_groups = sorted(group for group in groups if f"for shape in $({group})" not in self.make_text)

        self.assertTrue(groups, "No ALINK PRG object-code launch shape groups found")
        self.assertFalse(stale, "Object-code launch group references missing probe cases: " + ", ".join(stale))
        self.assertFalse(non_object, "Object-code launch group contains non-object-code cases: " + ", ".join(non_object))
        self.assertFalse(
            missing_successful,
            "Successful object-code probe cases missing from launch groups: " + ", ".join(missing_successful),
        )
        self.assertFalse(
            grouped_rejections,
            "Object-code rejection probe cases should stay in the skip-launch matrix: "
            + ", ".join(grouped_rejections),
        )
        self.assertFalse(unrun_groups, "Object-code launch groups not used by a target: " + ", ".join(unrun_groups))

    def test_object_code_launch_groups_do_not_duplicate_shapes(self) -> None:
        groups = self._makefile_object_code_shape_group_lists(self.make_text)

        duplicates: list[str] = []
        for group, shapes in groups.items():
            seen: set[str] = set()
            for shape in shapes:
                if shape in seen:
                    duplicates.append(f"{group}:{shape}")
                seen.add(shape)

        self.assertFalse(
            duplicates,
            "Object-code launch groups should not duplicate shapes: " + ", ".join(duplicates),
        )

    def test_object_code_launch_group_parser_preserves_duplicates(self) -> None:
        groups = self._makefile_object_code_shape_group_lists(
            "ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES := \\\n"
            "\tobject_code_one \\\n"
            "\tobject_code_one \\\n"
            "\tobject_code_two\n"
        )

        self.assertEqual(
            groups["ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES"],
            ["object_code_one", "object_code_one", "object_code_two"],
        )

    def test_object_code_core_matrix_covers_runtime_helper_import_from_obj(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        expected_loads = {
            "object_code_external_runtime_helper_call": ["LIB/RT_GFX_BGCOLOR.OBJ"],
            "object_code_transitive_runtime_helper_call": ["LIB/A.OBJ", "LIB/RT_GFX_BGCOLOR.OBJ"],
            "object_code_project_transitive_runtime_helper_call": [
                "OBJ/A.OBJ",
                "LIB/RT_GFX_BGCOLOR.OBJ",
            ],
            "object_code_mixed_project_library_transitive_runtime_helper_call": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "LIB/RT_GFX_BGCOLOR.OBJ",
            ],
            "object_code_mixed_library_project_transitive_runtime_helper_call": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
                "LIB/RT_GFX_BGCOLOR.OBJ",
            ],
            "object_code_mixed_project_library_project_transitive_runtime_helper_call": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
                "LIB/RT_GFX_BGCOLOR.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                object_text = (
                    str(case["seed_object"])
                    + str(case.get("extra_objects", {}))
                    + str(case.get("extra_library_objects", {}))
                )

                self.assertIn(shape, core_shapes)
                self.assertEqual(case["runtime_library_objects"], ["rt_gfx_bgcolor"])
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("u rt_gfx_bgcolor", object_text)
                self.assertIn("r 3 u0", object_text)
                self.assertIn("LIB/RT_SID_FREQ.OBJ", case["unexpected_alink_loads"])

    def test_dependency_load_verifiers_ignore_failed_fallback_probes(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_actc_alink_launch_probe_direct as direct_probe
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_named_dependency_lettered_import_library_helper"
        summary = {
            "ops": [
                {"kind": "load", "path": "OBJ/A.OBJ", "status": 1},
                {"kind": "load", "path": "OBJ/HELPER.OBJ", "status": 3},
                {"kind": "load", "path": "LIB/HELPER.OBJ", "status": 1},
                {"kind": "rwr", "path": "OBJ/D0.OBJ", "status": 1},
            ],
        }

        probe.verify_alink_dependency_loads(summary, shape)
        direct_probe.verify_alink_dependency_loads(summary, shape)

    def test_object_code_rejection_cases_have_focused_skip_launch_target(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        rejection_cases = self._makefile_object_code_rejection_cases(self.make_text)
        expected_rejections = {
            shape
            for shape, case in probe.DIRECT_PRG_CASES.items()
            if shape.startswith("object_code_") and bool(case.get("expect_alink_failure", False))
        }

        stale = sorted(rejection_cases - set(probe.DIRECT_PRG_CASES))
        missing = sorted(expected_rejections - rejection_cases)
        unexpected = sorted(rejection_cases - expected_rejections)

        self.assertTrue(rejection_cases, "No focused ALINK object-code rejection cases found")
        self.assertFalse(stale, "Object-code rejection group references missing probe cases: " + ", ".join(stale))
        self.assertFalse(missing, "Object-code rejection probe cases missing from focused target: " + ", ".join(missing))
        self.assertFalse(unexpected, "Non-rejection object-code cases listed in rejection target: " + ", ".join(unexpected))
        self.assertIn(
            "for shape in $(ACTION_ALINK_PRG_OBJECT_CODE_REJECTION_CASES)",
            self.make_text,
            "Object-code rejection cases are not used by a Makefile target",
        )
        self.assertIn(
            "--shape \"$$shape\" --skip-launch --attempts 1",
            self.make_text,
            "Object-code rejection target must run probes with --skip-launch",
        )
        self.assertIn(
            "object_code_dependency_unknown_lowercase_import_index_rejects",
            rejection_cases,
            "Object-code rejection matrix must cover unresolved lowercase high-index dependency imports",
        )
        self.assertIn(
            "object_code_project_unknown_lowercase_import_index_blocks_library_fallback",
            rejection_cases,
            "Object-code rejection matrix must cover bad project OBJ lowercase imports blocking library fallback",
        )
        self.assertIn(
            "object_code_project_second_export_named_symbol_local_export",
            rejection_cases,
            "Object-code rejection matrix must cover named local exports outside the selected object-code range",
        )
        self.assertIn(
            "object_code_library_duplicate_export_rejects",
            rejection_cases,
            "Object-code rejection matrix must cover duplicate exports in loaded library OBJs",
        )
        self.assertIn(
            "object_code_project_duplicate_export_blocks_library_fallback",
            rejection_cases,
            "Object-code rejection matrix must cover duplicate project OBJ exports blocking library fallback",
        )
        self.assertIn(
            "object_code_project_zero_size_export_blocks_library_fallback",
            rejection_cases,
            "Object-code rejection matrix must cover zero-size project OBJ exports blocking library fallback",
        )
        self.assertIn(
            "object_code_project_export_offset_past_machine_blocks_library_fallback",
            rejection_cases,
            "Object-code rejection matrix must cover project OBJ export offsets past machine data blocking library fallback",
        )
        self.assertIn(
            "object_code_project_export_size_overruns_machine_blocks_library_fallback",
            rejection_cases,
            "Object-code rejection matrix must cover project OBJ export sizes overrunning machine data blocking library fallback",
        )
        self.assertIn(
            "object_code_project_reloc_malformed_offset_blocks_library_fallback",
            rejection_cases,
            "Object-code rejection matrix must cover malformed project OBJ relocations blocking library fallback",
        )

    def test_object_code_rejection_cases_do_not_duplicate_shapes(self) -> None:
        rejection_cases = self._makefile_object_code_rejection_case_list(self.make_text)
        seen: set[str] = set()
        duplicates: list[str] = []

        for shape in rejection_cases:
            if shape in seen:
                duplicates.append(shape)
            seen.add(shape)

        self.assertFalse(
            duplicates,
            "Object-code rejection matrix should not duplicate shapes: " + ", ".join(duplicates),
        )

    def test_object_code_rejection_parser_preserves_duplicates(self) -> None:
        rejection_cases = self._makefile_object_code_rejection_case_list(
            "ACTION_ALINK_PRG_OBJECT_CODE_REJECTION_CASES := \\\n"
            "\tobject_code_bad_one \\\n"
            "\tobject_code_bad_one \\\n"
            "\tobject_code_bad_two\n"
        )

        self.assertEqual(
            rejection_cases,
            ["object_code_bad_one", "object_code_bad_one", "object_code_bad_two"],
        )

    def test_object_code_aggregate_target_runs_all_focused_matrices(self) -> None:
        targets = self._makefile_target_submakes(self.make_text, "vice-action-alink-prg-object-code-matrices")

        self.assertEqual(
            targets,
            [
                "vice-action-alink-prg-object-code-graph-launch-matrix",
                "vice-action-alink-prg-object-code-core-launch-matrix",
                "vice-action-alink-prg-object-code-rejection-matrix",
            ],
        )

    def test_object_code_launch_matrices_clean_stale_vice_before_each_shape(self) -> None:
        for target in (
            "vice-action-alink-prg-object-code-graph-launch-matrix",
            "vice-action-alink-prg-object-code-core-launch-matrix",
        ):
            with self.subTest(target=target):
                body = self._makefile_target_body(self.make_text, target)
                cleanup = "vp.cleanup_stale_vice(settle_seconds=1.0)"
                retry_loop = "for attempt in $$(seq 1 $(ACTION_ALINK_PRG_OBJECT_CODE_PROBE_ATTEMPTS))"
                self.assertIn(cleanup, body)
                self.assertIn(retry_loop, body)
                self.assertLess(
                    body.index(cleanup),
                    body.index(retry_loop),
                    "Object-code launch matrices should clean stale VICE before the first attempt",
                )

    def test_alink_prg_probe_progress_output_is_verbose_gated(self) -> None:
        probe_text = (self.workspace / "udos" / "tools" / "run_action_alink_prg_probe.py").read_text()

        self.assertIn('parser.add_argument("--verbose"', probe_text)
        self.assertIn("def log_progress(verbose: bool", probe_text)
        self.assertNotIn('print({"stage":', probe_text)
        self.assertNotIn('print({"attempt":', probe_text)
        self.assertNotIn("print(result, flush=True)", probe_text)

    def test_alink_prg_probe_quits_vice_before_process_termination(self) -> None:
        probe_text = (self.workspace / "udos" / "tools" / "run_action_alink_prg_probe.py").read_text()

        quit_index = probe_text.index("client.quit_emulator()")
        close_index = probe_text.index("client.close()", quit_index)
        terminate_index = probe_text.index("vp.terminate_process_tree(process)", close_index)

        self.assertLess(quit_index, close_index)
        self.assertLess(close_index, terminate_index)

    def test_alink_prg_probe_mirrors_main_prg_for_linux_host_launch(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "UPPER" / "PROJ3"
            bin_root = project_root / "BIN"
            bin_root.mkdir(parents=True)
            payload = bytes([0x00, 0x10, 0x60])
            (bin_root / "MAIN.PRG").write_bytes(payload)
            (bin_root / "UDOSDIR.TXT").write_text("", encoding="ascii")

            probe.ensure_host_prg_catalog(project_root)

            catalog = (bin_root / "UDOSDIR.TXT").read_text(encoding="ascii")
            self.assertIn("F MAIN.PRG", catalog)
            self.assertEqual((bin_root / "main.prg").read_bytes(), payload)
            self.assertEqual((bin_root / "udosdir.txt").read_text(encoding="ascii"), catalog)

    def test_object_code_graph_matrix_covers_named_external_transitive_loads(self) -> None:
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_external_named_pair": ["LIB/A.OBJ", "LIB/B.OBJ"],
            "object_code_external_named_triple_root_imports": [
                "LIB/A.OBJ",
                "LIB/B.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_external_named_offset_transitive_call": [
                "LIB/A.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_named_transitive_call": ["LIB/A.OBJ", "LIB/B.OBJ"],
            "object_code_project_named_transitive_call": ["OBJ/A.OBJ", "OBJ/B.OBJ"],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                object_text = (
                    str(case["seed_object"])
                    + str(case.get("extra_objects", {}))
                    + str(case.get("extra_library_objects", {}))
                )
                self.assertIn(shape, graph_shapes)
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("r 1 x a", object_text)
                self.assertRegex(object_text, r"r [1347] x [bc]")

    def test_object_code_graph_matrix_covers_external_closure_beyond_import_alphabet(
        self,
    ) -> None:
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_external_chain_40"
        case = probe.DIRECT_PRG_CASES[shape]
        loads = case["expected_alink_loads"]
        objects = case["extra_library_objects"]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(len(loads), 40)
        self.assertEqual(loads[0], "LIB/D00.OBJ")
        self.assertEqual(loads[-1], "LIB/D39.OBJ")
        self.assertEqual(len(objects), 40)
        self.assertGreater(len(case["expected_tail"]), 36)

    def test_object_code_matrices_cover_external_closure_capacity_and_overflow(
        self,
    ) -> None:
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        rejection_shapes = self._makefile_object_code_rejection_cases(self.make_text)
        production_build = (
            self.workspace / "actionc64u" / "tools" / "build_alink_udos.sh"
        ).read_text()
        external_match = re.search(r"-D EXTERNAL_MAX=(\d+)", production_build)
        self.assertIsNotNone(external_match)
        assert external_match is not None
        external_limit = int(external_match.group(1))

        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        success_shape = f"object_code_external_chain_{external_limit}"
        overflow_shape = f"object_code_external_chain_{external_limit + 1}_rejects"
        success = probe.DIRECT_PRG_CASES[success_shape]
        overflow = probe.DIRECT_PRG_CASES[overflow_shape]

        self.assertIn(success_shape, graph_shapes)
        self.assertEqual(len(success["expected_alink_loads"]), external_limit)
        self.assertEqual(len(success["extra_library_objects"]), external_limit)
        self.assertFalse(success.get("expect_alink_failure", False))

        self.assertIn(overflow_shape, rejection_shapes)
        self.assertEqual(len(overflow["extra_library_objects"]), external_limit + 1)
        self.assertEqual(len(overflow["expected_alink_loads"]), external_limit)
        self.assertEqual(
            overflow["unexpected_alink_loads"],
            [f"LIB/D{external_limit:02d}.OBJ"],
        )
        self.assertEqual(overflow["expected_alink_error"], "BAD OBJECT")
        self.assertTrue(overflow["expect_alink_failure"])
        self.assertNotIn("expected_tail", overflow)

    def test_object_code_graph_matrix_covers_project_named_offset_library_dependency_loads(self) -> None:
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_named_offset_library_dependency"
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(
            shape,
            graph_shapes,
            "Object-code graph matrix must cover named project offset exports importing library deps",
        )
        self.assertEqual(case["expected_alink_loads"], ["OBJ/A.OBJ", "LIB/B.OBJ"])
        object_text = str(case["seed_object"]) + str(case["extra_objects"])
        self.assertIn("x a 2 4", object_text)
        self.assertIn("r 1 x a", object_text)
        self.assertIn("r 3 x b", object_text)

    def test_object_code_graph_matrix_covers_project_named_precedence_and_second_export_loads(self) -> None:
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_project_named_precedes_library": ["OBJ/A.OBJ"],
            "object_code_project_second_export_named_import": ["OBJ/A.OBJ", "LIB/B.OBJ"],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertIn(shape, graph_shapes)
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
                self.assertIn("r 1 x a", case["seed_object"])

    def test_object_code_graph_matrix_covers_project_second_export_named_lettered_helper_loads(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_project_second_export_named_lettered_import_project_helper": [
                "OBJ/A.OBJ",
                "OBJ/HELPER.OBJ",
            ],
            "object_code_project_second_export_named_lettered_import_library_helper": [
                "OBJ/A.OBJ",
                "LIB/HELPER.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("r 1 x a", case["seed_object"])
                self.assertIn("r 5 uA", str(case["extra_objects"]))

    def test_object_code_graph_matrix_covers_project_second_export_named_lowercase_helper_loads(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_project_second_export_named_lowercase_z_import_library_helper": [
                "OBJ/A.OBJ",
                "LIB/HELPER.OBJ",
            ],
            "object_code_project_second_export_named_lowercase_z_import_project_helper": [
                "OBJ/A.OBJ",
                "OBJ/HELPER.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("r 1 x a", case["seed_object"])
                self.assertIn("r 5 uz", str(case["extra_objects"]))

    def test_object_code_graph_matrix_covers_project_second_export_library_dependency_project_tail_loads(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_project_second_export_library_dependency_imports_project_tail": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
            ],
            "object_code_project_second_export_named_library_dependency_imports_project_tail": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("A.OBJ", case["extra_objects"])
                self.assertIn("B.OBJ", case["extra_library_objects"])
                self.assertIn("C.OBJ", case["extra_objects"])
                self.assertIn("LIB/C.OBJ", case["unexpected_alink_loads"])
                object_text = str(case["extra_library_objects"])
                self.assertIn("x b 4 4", object_text)

    def test_object_code_graph_matrix_covers_project_second_export_import(self) -> None:
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())

        self.assertIn(
            "object_code_project_second_export_import",
            graph_shapes,
            "Object-code graph matrix must cover project OBJ second-export imports before library fallback",
        )
        self.assertIn(
            "object_code_project_second_export_named_import",
            graph_shapes,
            "Object-code graph matrix must cover named project OBJ second-export imports before library fallback",
        )
        self.assertIn(
            "object_code_project_second_export_named_symbol_import",
            graph_shapes,
            "Object-code graph matrix must cover project second-export named relocations adding imports",
        )
        self.assertIn(
            "object_code_project_second_export_named_symbol_project_import",
            graph_shapes,
            "Object-code graph matrix must cover project second-export named relocations preferring project deps",
        )
        self.assertIn(
            "object_code_project_second_export_named_dual_second_export_mixed_tails",
            graph_shapes,
            "Object-code graph matrix must cover project second-export named relocations to mixed project/library tails",
        )
        self.assertIn(
            "object_code_project_second_export_imports_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover project second-export imports to project-local deps",
        )
        self.assertIn(
            "object_code_project_second_export_named_imports_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover project second-export named imports to project-local deps",
        )
        self.assertIn(
            "object_code_project_second_export_imports_library_dependency",
            graph_shapes,
            "Object-code graph matrix must cover project second-export imports to library deps",
        )
        self.assertIn(
            "object_code_project_second_export_named_imports_library_dependency",
            graph_shapes,
            "Object-code graph matrix must cover project second-export named imports to library deps",
        )
        self.assertIn(
            "object_code_project_second_export_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover project second-export imports to root-local exports",
        )
        self.assertIn(
            "object_code_project_second_export_named_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover project second-export named imports to root-local exports",
        )
        self.assertIn(
            "object_code_project_second_export_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover project second-export imports to offset root-local exports",
        )
        self.assertIn(
            "object_code_project_second_export_named_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover project second-export named imports to offset root-local exports",
        )
        self.assertIn(
            "object_code_project_second_export_dependency_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover project second-export deps importing root-local exports",
        )
        self.assertIn(
            "object_code_project_second_export_named_dependency_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover project second-export named deps importing root-local exports",
        )
        self.assertIn(
            "object_code_project_second_export_dependency_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover project second-export deps importing offset root-local exports",
        )
        self.assertIn(
            "object_code_project_second_export_named_dependency_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover project second-export named deps importing offset root-local exports",
        )
        self.assertIn(
            "object_code_project_second_export_lettered_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover selected second-export lettered imports to project deps",
        )
        self.assertIn(
            "object_code_project_second_export_named_lettered_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover named second-export lettered imports to project deps",
        )
        self.assertIn(
            "object_code_project_second_export_lettered_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover selected project second-export lettered imports to library deps",
        )
        self.assertIn(
            "object_code_project_second_export_named_lettered_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover named project second-export lettered imports to library deps",
        )
        self.assertIn(
            "object_code_project_second_export_lowercase_z_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover selected project second-export lowercase imports to library deps",
        )
        self.assertIn(
            "object_code_project_second_export_named_lowercase_z_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover named project second-export lowercase imports to library deps",
        )
        self.assertIn(
            "object_code_project_second_export_lowercase_z_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover selected project second-export lowercase imports to project deps",
        )
        self.assertIn(
            "object_code_project_second_export_named_lowercase_z_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover named project second-export lowercase imports to project deps",
        )
        self.assertIn(
            "object_code_project_second_export_dependency_dual_lettered_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover project second-export deps with mixed lettered helper imports",
        )
        self.assertIn(
            "object_code_project_second_export_dependency_dual_lowercase_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover project second-export deps with mixed high-index helper imports",
        )
        self.assertIn(
            "object_code_project_second_export_dependency_mixed_lettered_lowercase_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover project second-export deps with mixed lettered/high-index helper imports",
        )
        self.assertIn(
            "object_code_project_second_export_named_dependency_dual_lettered_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover project second-export named deps with mixed lettered helper imports",
        )
        self.assertIn(
            "object_code_project_second_export_named_dependency_dual_lowercase_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover project second-export named deps with mixed high-index helper imports",
        )
        self.assertIn(
            "object_code_project_second_export_named_dependency_mixed_lettered_lowercase_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover project second-export named deps with mixed lettered/high-index helper imports",
        )
        self.assertIn(
            "object_code_project_second_export_transitive_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover transitive selected second-export project deps",
        )
        self.assertIn(
            "object_code_project_second_export_named_transitive_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover named transitive selected second-export project deps",
        )
        self.assertIn(
            "object_code_project_second_export_project_dependency_imports_library_tail",
            graph_shapes,
            "Object-code graph matrix must cover project second-export project deps importing library tails",
        )
        self.assertIn(
            "object_code_project_second_export_named_project_dependency_imports_library_tail",
            graph_shapes,
            "Object-code graph matrix must cover named project second-export project deps importing library tails",
        )
        self.assertIn(
            "object_code_project_second_export_library_dependency_imports_project_tail",
            graph_shapes,
            "Object-code graph matrix must cover project second-export library deps importing project tails",
        )
        self.assertIn(
            "object_code_project_second_export_named_library_dependency_imports_project_tail",
            graph_shapes,
            "Object-code graph matrix must cover named project second-export library deps importing project tails",
        )
        self.assertIn(
            "object_code_project_second_export_transitive_library_dependency",
            graph_shapes,
            "Object-code graph matrix must cover transitive selected second-export library deps",
        )
        self.assertIn(
            "object_code_project_second_export_named_transitive_library_dependency",
            graph_shapes,
            "Object-code graph matrix must cover named transitive selected second-export library deps",
        )
        self.assertIn(
            "object_code_mixed_second_export_transitive_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover mixed transitive selected second-export deps",
        )
        self.assertIn(
            "object_code_mixed_second_export_named_transitive_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover mixed named transitive selected second-export deps",
        )

    def test_object_code_graph_matrix_covers_library_dual_import_dependencies(self) -> None:
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())

        self.assertIn(
            "object_code_library_dual_import_project_library_dependencies",
            graph_shapes,
            "Object-code graph matrix must cover one library OBJ relocating to project and library deps",
        )
        self.assertIn(
            "object_code_library_named_dual_import_project_library_dependencies",
            graph_shapes,
            "Object-code graph matrix must cover one library OBJ named-relocating to project and library deps",
        )
        self.assertIn(
            "object_code_project_dual_import_project_library_dependencies",
            graph_shapes,
            "Object-code graph matrix must cover one project OBJ relocating to project and library deps",
        )
        self.assertIn(
            "object_code_project_named_dual_import_project_library_dependencies",
            graph_shapes,
            "Object-code graph matrix must cover one project OBJ named-relocating to project and library deps",
        )
        self.assertIn(
            "object_code_library_dual_import_library_project_dependencies",
            graph_shapes,
            "Object-code graph matrix must cover one library OBJ relocating to library and project deps",
        )
        self.assertIn(
            "object_code_library_named_dual_import_library_project_dependencies",
            graph_shapes,
            "Object-code graph matrix must cover one library OBJ named-relocating to library and project deps",
        )
        self.assertIn(
            "object_code_project_dual_import_library_project_dependencies",
            graph_shapes,
            "Object-code graph matrix must cover one project OBJ relocating to library and project deps",
        )
        self.assertIn(
            "object_code_project_named_dual_import_library_project_dependencies",
            graph_shapes,
            "Object-code graph matrix must cover one project OBJ named-relocating to library and project deps",
        )
        self.assertIn(
            "object_code_library_dual_import_library_dependencies",
            graph_shapes,
            "Object-code graph matrix must cover one library OBJ relocating to two library deps",
        )
        self.assertIn(
            "object_code_library_named_dual_import_library_dependencies",
            graph_shapes,
            "Object-code graph matrix must cover one library OBJ named-relocating to two library deps",
        )
        self.assertIn(
            "object_code_project_dual_import_project_dependencies",
            graph_shapes,
            "Object-code graph matrix must cover one project OBJ relocating to two project deps",
        )
        self.assertIn(
            "object_code_project_named_dual_import_project_dependencies",
            graph_shapes,
            "Object-code graph matrix must cover one project OBJ named-relocating to two project deps",
        )
        self.assertIn(
            "object_code_mixed_project_library_closure",
            graph_shapes,
            "Object-code graph matrix must cover mixed root project/library deps with library tails",
        )
        self.assertIn(
            "object_code_named_mixed_project_library_closure",
            graph_shapes,
            "Object-code graph matrix must cover named mixed root project/library deps with library tails",
        )
        self.assertIn(
            "object_code_mixed_dual_transitive_project_library_closure",
            graph_shapes,
            "Object-code graph matrix must cover mixed root project/library deps with opposite transitive tails",
        )
        self.assertIn(
            "object_code_named_mixed_dual_transitive_project_library_closure",
            graph_shapes,
            "Object-code graph matrix must cover named mixed root project/library deps with opposite transitive tails",
        )
        self.assertIn(
            "object_code_mixed_library_project_closure",
            graph_shapes,
            "Object-code graph matrix must cover mixed root library/project deps with project tails",
        )
        self.assertIn(
            "object_code_named_mixed_library_project_closure",
            graph_shapes,
            "Object-code graph matrix must cover named mixed root library/project deps with project tails",
        )
        self.assertIn(
            "object_code_mixed_dual_transitive_library_project_closure",
            graph_shapes,
            "Object-code graph matrix must cover mixed root library/project deps with opposite transitive tails",
        )
        self.assertIn(
            "object_code_named_mixed_dual_transitive_library_project_closure",
            graph_shapes,
            "Object-code graph matrix must cover named mixed root library/project deps with opposite transitive tails",
        )
        self.assertIn(
            "object_code_library_dependency_lettered_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover library dependency lettered imports resolving to project OBJs",
        )
        self.assertIn(
            "object_code_library_named_dependency_lettered_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover library named dependency lettered imports resolving to project OBJs",
        )
        self.assertIn(
            "object_code_library_dependency_lowercase_z_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover library dependency lowercase imports resolving to project OBJs",
        )
        self.assertIn(
            "object_code_library_named_dependency_lowercase_z_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover library named dependency lowercase imports resolving to project OBJs",
        )
        self.assertIn(
            "object_code_library_dependency_lowercase_z_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover library dependency lowercase imports resolving to library OBJs",
        )
        self.assertIn(
            "object_code_library_named_dependency_lowercase_z_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover library named dependency lowercase imports resolving to library OBJs",
        )
        self.assertIn(
            "object_code_dependency_reloc_scan_windowed_imports",
            graph_shapes,
            "Object-code graph matrix must cover dependency relocation scans restored after source-windowed import lookup",
        )
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        windowed_case = probe.DIRECT_PRG_CASES[
            "object_code_dependency_reloc_scan_windowed_imports"
        ]
        windowed_dependency = windowed_case["extra_library_objects"]["A.OBJ"]
        self.assertGreater(len(windowed_dependency.encode("ascii")), 767)
        self.assertGreater(windowed_dependency.index("x a 0 34\n"), 512)
        self.assertIn("b u0u1u2u3u4u5u6u7u8u9uAM\n", windowed_dependency)
        self.assertIn(
            "object_code_library_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover library OBJ relocation back to root-local exports",
        )
        self.assertIn(
            "object_code_library_named_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover named library OBJ relocation back to root-local exports",
        )
        self.assertIn(
            "object_code_library_named_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover named library OBJ relocation back to offset root-local exports",
        )
        self.assertIn(
            "object_code_project_named_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover named project OBJ relocation back to offset root-local exports",
        )
        self.assertIn(
            "object_code_transitive_named_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover transitive named OBJ relocation back to root-local exports",
        )
        self.assertIn(
            "object_code_transitive_named_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover transitive named OBJ relocation back to offset root-local exports",
        )
        self.assertIn(
            "object_code_mixed_transitive_named_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover mixed project/library transitive named relocation back to root-local exports",
        )
        self.assertIn(
            "object_code_mixed_transitive_named_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover mixed project/library transitive named relocation back to offset root-local exports",
        )
        self.assertIn(
            "object_code_library_project_transitive_named_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover library-to-project transitive named relocation back to root-local exports",
        )
        self.assertIn(
            "object_code_library_project_transitive_named_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover library-to-project transitive named relocation back to offset root-local exports",
        )
        self.assertIn(
            "object_code_project_transitive_named_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover project transitive named relocation back to root-local exports",
        )
        self.assertIn(
            "object_code_project_transitive_named_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover project transitive named relocation back to offset root-local exports",
        )
        self.assertIn(
            "object_code_library_second_export_named_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover library second-export named relocation back to root-local exports",
        )
        self.assertIn(
            "object_code_library_second_export_named_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover library second-export named relocation back to offset root-local exports",
        )
        self.assertIn(
            "object_code_library_second_export_named_dependency_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover library second-export named dependency relocation back to root-local exports",
        )
        self.assertIn(
            "object_code_library_second_export_named_dependency_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover library second-export named dependency relocation back to offset root-local exports",
        )
        self.assertIn(
            "object_code_library_named_imports_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover library named imports to project-local deps",
        )
        self.assertIn(
            "object_code_library_named_offset_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover named offset library exports importing project-local deps",
        )
        self.assertIn(
            "object_code_library_second_export_imports_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover library second-export imports to project-local deps",
        )
        self.assertIn(
            "object_code_library_second_export_named_imports_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover library second-export named imports to project-local deps",
        )
        self.assertIn(
            "object_code_library_second_export_named_symbol_import",
            graph_shapes,
            "Object-code graph matrix must cover library second-export named relocations adding imports",
        )
        self.assertIn(
            "object_code_library_second_export_named_symbol_library_import",
            graph_shapes,
            "Object-code graph matrix must cover library second-export named relocations to library deps",
        )
        self.assertIn(
            "object_code_library_second_export_named_dual_second_export_mixed_tails",
            graph_shapes,
            "Object-code graph matrix must cover library second-export named relocations to mixed project/library tails",
        )
        self.assertIn(
            "object_code_library_second_export_dependency_dual_lettered_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover library second-export deps with mixed lettered helper imports",
        )
        self.assertIn(
            "object_code_library_second_export_dependency_dual_lowercase_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover library second-export deps with mixed high-index helper imports",
        )
        self.assertIn(
            "object_code_library_second_export_dependency_mixed_lettered_lowercase_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover library second-export deps with mixed lettered/high-index helper imports",
        )
        self.assertIn(
            "object_code_library_second_export_named_dependency_dual_lettered_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover library second-export named deps with mixed lettered helper imports",
        )
        self.assertIn(
            "object_code_library_second_export_named_dependency_dual_lowercase_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover library second-export named deps with mixed high-index helper imports",
        )
        self.assertIn(
            "object_code_library_second_export_named_dependency_mixed_lettered_lowercase_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover library second-export named deps with mixed lettered/high-index helper imports",
        )
        self.assertIn(
            "object_code_library_second_export_lettered_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover selected library second-export lettered imports to project deps",
        )
        self.assertIn(
            "object_code_library_second_export_named_lettered_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover named library second-export lettered imports to project deps",
        )
        self.assertIn(
            "object_code_library_second_export_lettered_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover selected library second-export lettered imports to library deps",
        )
        self.assertIn(
            "object_code_library_second_export_named_lettered_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover named library second-export lettered imports to library deps",
        )
        self.assertIn(
            "object_code_library_second_export_lowercase_z_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover selected library second-export lowercase imports to project deps",
        )
        self.assertIn(
            "object_code_library_second_export_named_lowercase_z_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover named library second-export lowercase imports to project deps",
        )
        self.assertIn(
            "object_code_library_second_export_lowercase_z_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover selected library second-export lowercase imports to library deps",
        )
        self.assertIn(
            "object_code_library_second_export_named_lowercase_z_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover named library second-export lowercase imports to library deps",
        )
        self.assertIn(
            "object_code_library_second_export_imports_library_dependency",
            graph_shapes,
            "Object-code graph matrix must cover library second-export imports to library deps",
        )
        self.assertIn(
            "object_code_library_second_export_named_imports_library_dependency",
            graph_shapes,
            "Object-code graph matrix must cover library second-export named imports to library deps",
        )
        self.assertIn(
            "object_code_library_second_export_transitive_library_dependency",
            graph_shapes,
            "Object-code graph matrix must cover transitive selected second-export library deps",
        )
        self.assertIn(
            "object_code_library_second_export_named_transitive_library_dependency",
            graph_shapes,
            "Object-code graph matrix must cover named transitive selected second-export library deps",
        )
        self.assertIn(
            "object_code_library_second_export_transitive_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover library selected second-export transitive project deps",
        )
        self.assertIn(
            "object_code_library_second_export_named_transitive_project_dependency",
            graph_shapes,
            "Object-code graph matrix must cover named library selected second-export transitive project deps",
        )
        self.assertIn(
            "object_code_library_second_export_project_dependency_imports_library_tail",
            graph_shapes,
            "Object-code graph matrix must cover library second-export project deps importing library tails",
        )
        self.assertIn(
            "object_code_library_second_export_named_project_dependency_imports_library_tail",
            graph_shapes,
            "Object-code graph matrix must cover named library second-export project deps importing library tails",
        )
        self.assertIn(
            "object_code_library_second_export_library_dependency_imports_project_tail",
            graph_shapes,
            "Object-code graph matrix must cover library second-export library deps importing project tails",
        )
        self.assertIn(
            "object_code_library_second_export_named_library_dependency_imports_project_tail",
            graph_shapes,
            "Object-code graph matrix must cover named library second-export library deps importing project tails",
        )
        self.assertIn(
            "object_code_mixed_second_export_shared_library_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover mixed second-export imports sharing one library dep",
        )
        self.assertIn(
            "object_code_mixed_second_export_shared_project_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover mixed second-export imports sharing one project dep",
        )
        self.assertIn(
            "object_code_mixed_second_export_named_shared_library_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover mixed second-export named relocations sharing one library dep",
        )
        self.assertIn(
            "object_code_mixed_second_export_named_shared_project_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover mixed second-export named relocations sharing one project dep",
        )
        self.assertIn(
            "object_code_mixed_second_export_dual_tail_closure",
            graph_shapes,
            "Object-code graph matrix must cover mixed second-export imports with independent project/library tails",
        )
        self.assertIn(
            "object_code_mixed_second_export_named_dual_tail_closure",
            graph_shapes,
            "Object-code graph matrix must cover mixed second-export named relocations with independent project/library tails",
        )
        self.assertIn(
            "object_code_library_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover root-local export relocation from offset root bodies",
        )
        self.assertIn(
            "object_code_library_second_export_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover selected library second exports relocating to root-local exports",
        )
        self.assertIn(
            "object_code_library_second_export_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover selected library second exports relocating to offset root-local exports",
        )
        self.assertIn(
            "object_code_library_second_export_dependency_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover selected second-export deps relocating to root-local exports",
        )
        self.assertIn(
            "object_code_library_second_export_dependency_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover selected second-export deps relocating to offset root-local exports",
        )
        self.assertIn(
            "object_code_project_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover project OBJ relocation back to root-local exports",
        )
        self.assertIn(
            "object_code_project_named_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover named project OBJ relocation back to root-local exports",
        )
        self.assertIn(
            "object_code_project_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover project OBJ relocation back to offset root-local exports",
        )
        self.assertIn(
            "object_code_transitive_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover transitive dependency relocation back to root-local exports",
        )
        self.assertIn(
            "object_code_transitive_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover transitive dependency relocation back to offset root-local exports",
        )
        self.assertIn(
            "object_code_mixed_transitive_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover mixed transitive relocation back to root-local exports",
        )
        self.assertIn(
            "object_code_mixed_transitive_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover mixed transitive relocation back to offset root-local exports",
        )
        self.assertIn(
            "object_code_library_project_transitive_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover library-to-project transitive root-local relocation",
        )
        self.assertIn(
            "object_code_library_project_transitive_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover library-to-project transitive offset root-local relocation",
        )
        self.assertIn(
            "object_code_project_transitive_imports_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover project-only transitive root-local relocation",
        )
        self.assertIn(
            "object_code_project_transitive_imports_offset_root_local_export",
            graph_shapes,
            "Object-code graph matrix must cover project-only transitive offset root-local relocation",
        )
        self.assertIn(
            "object_code_mixed_shared_library_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover project and library OBJs sharing one library dep",
        )
        self.assertIn(
            "object_code_root_library_share_library_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover root and library OBJ sharing one library dep",
        )
        self.assertIn(
            "object_code_root_project_share_project_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover root and project OBJ sharing one project dep",
        )
        self.assertIn(
            "object_code_root_project_share_library_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover root and project OBJ sharing one library dep",
        )
        self.assertIn(
            "object_code_root_project_library_share_library_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover root, project OBJ, and library OBJ sharing one library dep",
        )
        self.assertIn(
            "object_code_root_project_library_share_project_dependency_dedup",
            graph_shapes,
            "Object-code graph matrix must cover root, project OBJ, and library OBJ sharing one project dep",
        )
        self.assertIn(
            "object_code_root_second_export_project_library_project_library_chain",
            graph_shapes,
            "Object-code graph matrix must launch selected root exports through alternating project/library dependency chains",
        )
        self.assertIn(
            "object_code_root_second_export_library_project_library_project_chain",
            graph_shapes,
            "Object-code graph matrix must launch selected root exports through alternating library/project dependency chains",
        )
        named_shared_dependency_shapes = [
            "object_code_named_root_library_share_project_dependency_dedup",
            "object_code_named_root_library_share_library_dependency_dedup",
            "object_code_named_root_project_share_project_dependency_dedup",
            "object_code_named_root_project_share_library_dependency_dedup",
            "object_code_named_project_library_project_library_chain",
            "object_code_root_second_export_named_project_library_project_library_chain",
            "object_code_root_second_export_named_library_project_library_project_chain",
            "object_code_named_mixed_shared_dependency_dedup",
            "object_code_named_root_project_library_share_library_dependency_dedup",
            "object_code_named_root_project_library_share_project_dependency_dedup",
            "object_code_named_mixed_shared_library_dependency_dedup",
        ]
        for shape in named_shared_dependency_shapes:
            with self.subTest(shape=shape):
                self.assertIn(
                    shape,
                    graph_shapes,
                    "Object-code graph matrix must cover named shared-dependency dedup and chain cases",
                )

    def test_object_code_graph_matrix_covers_named_dual_import_dependency_loads(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_library_named_dual_import_project_library_dependencies": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_project_named_dual_import_project_library_dependencies": [
                "OBJ/A.OBJ",
                "OBJ/B.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_library_named_dual_import_library_project_dependencies": [
                "LIB/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
            ],
            "object_code_project_named_dual_import_library_project_dependencies": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
            ],
            "object_code_library_named_dual_import_library_dependencies": [
                "LIB/A.OBJ",
                "LIB/B.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_project_named_dual_import_project_dependencies": [
                "OBJ/A.OBJ",
                "OBJ/B.OBJ",
                "OBJ/C.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                object_text = str(case.get("extra_objects", {})) + str(case["extra_library_objects"])
                self.assertIn("r 1 x b", object_text)
                self.assertIn("r 4 x c", object_text)

    def test_object_code_graph_matrix_covers_named_mixed_closure_loads(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_named_mixed_project_library_closure": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_named_mixed_dual_transitive_project_library_closure": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "LIB/C.OBJ",
                "OBJ/D.OBJ",
            ],
            "object_code_named_mixed_library_project_closure": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
                "OBJ/C.OBJ",
            ],
            "object_code_named_mixed_dual_transitive_library_project_closure": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
                "OBJ/C.OBJ",
                "LIB/D.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                object_text = str(case["seed_object"]) + str(case.get("extra_objects", {})) + str(case["extra_library_objects"])
                self.assertIn("u a", object_text)
                self.assertIn("u b", object_text)
                self.assertIn("r 1 u0", object_text)
                self.assertIn("r 4 u1", object_text)
                self.assertIn("r 1 x c", object_text)

    def test_object_code_graph_matrix_covers_named_shared_dependency_dedup_loads(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_named_root_library_share_project_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_named_root_library_share_library_dependency_dedup": [
                "LIB/B.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_named_root_project_share_project_dependency_dedup": [
                "OBJ/A.OBJ",
                "OBJ/B.OBJ",
            ],
            "object_code_named_root_project_share_library_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_named_project_library_project_library_chain": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
                "LIB/D.OBJ",
            ],
            "object_code_named_mixed_shared_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
            ],
            "object_code_named_root_project_library_share_library_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_named_root_project_library_share_project_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
            ],
            "object_code_named_mixed_shared_library_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "LIB/C.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                object_text = str(case.get("extra_objects", {})) + str(case["extra_library_objects"])
                self.assertRegex(object_text, r"r \d+ x ")

    def test_object_code_graph_matrix_covers_library_named_project_dependency_loads(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_library_named_imports_project_dependency"
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertEqual(case["expected_alink_loads"], ["LIB/B.OBJ", "OBJ/A.OBJ"])
        self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
        object_text = str(case["extra_library_objects"])
        self.assertIn("r 1 x a", object_text)

    def test_object_code_graph_matrix_covers_library_named_offset_project_dependency_loads(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_library_named_offset_project_dependency"
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertEqual(case["expected_alink_loads"], ["LIB/B.OBJ", "OBJ/A.OBJ"])
        self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
        object_text = str(case["seed_object"]) + str(case["extra_library_objects"])
        self.assertIn("x b 2 4", object_text)
        self.assertIn("r 1 x b", object_text)
        self.assertIn("r 3 x a", object_text)

    def test_object_code_graph_matrix_covers_library_second_export_named_lettered_helper_loads(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_library_second_export_named_lettered_import_project_helper": [
                "LIB/A.OBJ",
                "OBJ/HELPER.OBJ",
            ],
            "object_code_library_second_export_named_lettered_import_library_helper": [
                "LIB/A.OBJ",
                "LIB/HELPER.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("r 1 x a", case["seed_object"])
                self.assertIn("r 5 uA", str(case["extra_library_objects"]))

    def test_object_code_graph_matrix_covers_library_second_export_named_lowercase_helper_loads(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_library_second_export_named_lowercase_z_import_project_helper": [
                "LIB/A.OBJ",
                "OBJ/HELPER.OBJ",
            ],
            "object_code_library_second_export_named_lowercase_z_import_library_helper": [
                "LIB/A.OBJ",
                "LIB/HELPER.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("r 1 x a", case["seed_object"])
                self.assertIn("r 5 uz", str(case["extra_library_objects"]))

    def test_object_code_graph_matrix_covers_library_second_export_library_dependency_project_tail_loads(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_library_second_export_library_dependency_imports_project_tail": [
                "LIB/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
            ],
            "object_code_library_second_export_named_library_dependency_imports_project_tail": [
                "LIB/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("C.OBJ", case["extra_objects"])
                self.assertIn("B.OBJ", case["extra_library_objects"])
                self.assertIn("LIB/C.OBJ", case["unexpected_alink_loads"])
                object_text = str(case["extra_library_objects"])
                self.assertIn("x b 4 4", object_text)

    def test_object_code_graph_matrix_covers_project_lettered_import_pruning(self) -> None:
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())

        self.assertIn(
            "object_code_project_lettered_import_pruned",
            graph_shapes,
            "Object-code graph matrix must cover project OBJ lettered imports without loading pruned deps",
        )
        self.assertIn(
            "object_code_project_lettered_import_call",
            graph_shapes,
            "Object-code graph matrix must cover lettered imports resolving to project OBJs",
        )
        self.assertIn(
            "object_code_project_dependency_lettered_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover project dependency lettered imports resolving to project OBJs",
        )
        self.assertIn(
            "object_code_project_named_dependency_lettered_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover project named dependency lettered imports resolving to project OBJs",
        )
        self.assertIn(
            "object_code_project_dependency_lettered_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover project dependency lettered imports resolving to library OBJs",
        )
        self.assertIn(
            "object_code_project_named_dependency_lettered_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover project named dependency lettered imports resolving to library OBJs",
        )
        self.assertIn(
            "object_code_project_dependency_dual_lettered_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover project dependency dual lettered imports resolving to mixed helper OBJs",
        )
        self.assertIn(
            "object_code_project_dependency_dual_lowercase_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover project dependency dual lowercase imports resolving to mixed helper OBJs",
        )
        self.assertIn(
            "object_code_project_named_dependency_mixed_lettered_lowercase_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover project named dependency mixed lettered/lowercase imports resolving to mixed helper OBJs",
        )
        self.assertIn(
            "object_code_project_named_dependency_dual_lettered_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover project named dependency dual lettered imports resolving to mixed helper OBJs",
        )
        self.assertIn(
            "object_code_project_named_dependency_dual_lowercase_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover project named dependency dual lowercase imports resolving to mixed helper OBJs",
        )
        self.assertIn(
            "object_code_library_dependency_dual_lettered_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover library dependency dual lettered imports resolving to mixed helper OBJs",
        )
        self.assertIn(
            "object_code_library_named_dependency_lettered_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover library named dependency lettered imports resolving to library OBJs",
        )
        self.assertIn(
            "object_code_library_dependency_dual_lowercase_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover library dependency dual lowercase imports resolving to mixed helper OBJs",
        )
        self.assertIn(
            "object_code_library_dependency_mixed_lettered_lowercase_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover library dependency mixed lettered/lowercase imports resolving to mixed helper OBJs",
        )
        self.assertIn(
            "object_code_library_named_dependency_mixed_lettered_lowercase_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover library named dependency mixed lettered/lowercase imports resolving to mixed helper OBJs",
        )
        self.assertIn(
            "object_code_library_named_dependency_dual_lettered_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover library named dependency dual lettered imports resolving to mixed helper OBJs",
        )
        self.assertIn(
            "object_code_library_named_dependency_dual_lowercase_import_mixed_helpers",
            graph_shapes,
            "Object-code graph matrix must cover library named dependency dual lowercase imports resolving to mixed helper OBJs",
        )
        self.assertIn(
            "object_code_lowercase_z_import_call",
            graph_shapes,
            "Object-code graph matrix must cover lowercase high-index OBJ imports",
        )
        self.assertIn(
            "object_code_project_lowercase_z_import_call",
            graph_shapes,
            "Object-code graph matrix must cover lowercase high-index imports resolving to project OBJs",
        )
        self.assertIn(
            "object_code_dependency_lowercase_z_import_pruned",
            graph_shapes,
            "Object-code graph matrix must cover lowercase high-index imports in dependency bodies",
        )
        self.assertIn(
            "object_code_project_dependency_lowercase_z_import_pruned",
            graph_shapes,
            "Object-code graph matrix must cover project OBJ lowercase high-index dependency imports",
        )
        self.assertIn(
            "object_code_project_dependency_lowercase_z_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover project dependency lowercase imports resolving to project OBJs",
        )
        self.assertIn(
            "object_code_project_named_dependency_lowercase_z_import_project_helper",
            graph_shapes,
            "Object-code graph matrix must cover project named dependency lowercase imports resolving to project OBJs",
        )
        self.assertIn(
            "object_code_project_named_dependency_lowercase_z_import_library_helper",
            graph_shapes,
            "Object-code graph matrix must cover project named dependency lowercase imports resolving to library OBJs",
        )

    def test_object_code_graph_matrix_covers_project_dependency_lettered_library_helper(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_dependency_lettered_import_library_helper"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(case["expected_alink_loads"], ["OBJ/A.OBJ", "LIB/HELPER.OBJ"])
        self.assertEqual(sorted(case["extra_objects"]), ["A.OBJ"])
        for unexpected_path in ("LIB/A.OBJ", "LIB/D0.OBJ", "LIB/D9.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_project_dependency_dual_lettered_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_dependency_dual_lettered_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["OBJ/A.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertEqual(sorted(case["extra_objects"]), ["A.OBJ", "PROJHELPER.OBJ"])
        for unexpected_path in ("LIB/A.OBJ", "LIB/PROJHELPER.OBJ", "LIB/D0.OBJ", "LIB/D9.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_project_dependency_dual_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_dependency_dual_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["OBJ/A.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("A.OBJ", case["extra_objects"])
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        for unexpected_path in (
            "OBJ/D0.OBJ",
            "OBJ/D33.OBJ",
            "LIB/A.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_project_dependency_mixed_lettered_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_dependency_mixed_lettered_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["OBJ/A.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("A.OBJ", case["extra_objects"])
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        object_text = str(case["extra_objects"]["A.OBJ"])
        self.assertIn("b uAuzM", object_text)
        self.assertIn("r 1 uA", object_text)
        self.assertIn("r 4 uz", object_text)
        for unexpected_path in (
            "OBJ/D0.OBJ",
            "OBJ/D33.OBJ",
            "LIB/A.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_project_named_dependency_mixed_lettered_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_named_dependency_mixed_lettered_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertIn("r 1 x a", case["seed_object"])
        self.assertEqual(
            case["expected_alink_loads"],
            ["OBJ/A.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("A.OBJ", case["extra_objects"])
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        object_text = str(case["extra_objects"]["A.OBJ"])
        self.assertIn("b uAuzM", object_text)
        self.assertIn("r 1 uA", object_text)
        self.assertIn("r 4 uz", object_text)
        for unexpected_path in (
            "OBJ/D0.OBJ",
            "OBJ/D33.OBJ",
            "LIB/A.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_library_dependency_dual_lettered_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_library_dependency_dual_lettered_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/A.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertEqual(sorted(case["extra_objects"]), ["PROJHELPER.OBJ"])
        for unexpected_path in ("LIB/PROJHELPER.OBJ", "LIB/D0.OBJ", "LIB/D9.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_library_dependency_dual_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_library_dependency_dual_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/A.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("A.OBJ", case["extra_library_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        for unexpected_path in (
            "OBJ/D0.OBJ",
            "OBJ/D33.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_library_dependency_mixed_lettered_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_library_dependency_mixed_lettered_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/A.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("A.OBJ", case["extra_library_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        object_text = str(case["extra_library_objects"]["A.OBJ"])
        self.assertIn("b uAuzM", object_text)
        self.assertIn("r 1 uA", object_text)
        self.assertIn("r 4 uz", object_text)
        for unexpected_path in (
            "OBJ/D0.OBJ",
            "OBJ/D33.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_library_named_dependency_mixed_lettered_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_library_named_dependency_mixed_lettered_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertIn("r 1 x a", case["seed_object"])
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/A.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("A.OBJ", case["extra_library_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        object_text = str(case["extra_library_objects"]["A.OBJ"])
        self.assertIn("b uAuzM", object_text)
        self.assertIn("r 1 uA", object_text)
        self.assertIn("r 4 uz", object_text)
        for unexpected_path in (
            "OBJ/D0.OBJ",
            "OBJ/D33.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_project_second_export_dependency_dual_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_second_export_dependency_dual_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["OBJ/A.OBJ", "OBJ/DEP.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("A.OBJ", case["extra_objects"])
        self.assertIn("DEP.OBJ", case["extra_objects"])
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        for unexpected_path in (
            "LIB/A.OBJ",
            "LIB/DEP.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_project_second_export_dependency_mixed_lettered_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_second_export_dependency_mixed_lettered_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["OBJ/A.OBJ", "OBJ/DEP.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("A.OBJ", case["extra_objects"])
        self.assertIn("DEP.OBJ", case["extra_objects"])
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        object_text = str(case["extra_objects"]["DEP.OBJ"])
        self.assertIn("b uAuzM", object_text)
        self.assertIn("r 1 uA", object_text)
        self.assertIn("r 4 uz", object_text)
        for unexpected_path in (
            "OBJ/D0.OBJ",
            "OBJ/D33.OBJ",
            "LIB/A.OBJ",
            "LIB/DEP.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_project_second_export_named_dependency_mixed_lettered_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_second_export_named_dependency_mixed_lettered_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["OBJ/A.OBJ", "OBJ/DEP.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("A.OBJ", case["extra_objects"])
        self.assertIn("DEP.OBJ", case["extra_objects"])
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        root_text = str(case["extra_objects"]["A.OBJ"])
        self.assertIn("r 1 x missing", root_text)
        self.assertIn("r 5 x dep", root_text)
        dep_text = str(case["extra_objects"]["DEP.OBJ"])
        self.assertIn("u d0", dep_text)
        self.assertIn("u projhelper", dep_text)
        self.assertIn("u d10", dep_text)
        self.assertIn("u libhelper", dep_text)
        self.assertIn("r 1 x projhelper", dep_text)
        self.assertIn("r 4 x libhelper", dep_text)
        for unexpected_path in (
            "OBJ/D0.OBJ",
            "OBJ/D33.OBJ",
            "LIB/A.OBJ",
            "LIB/DEP.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_library_second_export_dependency_dual_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_library_second_export_dependency_dual_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/A.OBJ", "OBJ/DEP.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("DEP.OBJ", case["extra_objects"])
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("A.OBJ", case["extra_library_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        for unexpected_path in (
            "LIB/DEP.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_library_second_export_dependency_mixed_lettered_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_library_second_export_dependency_mixed_lettered_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/A.OBJ", "OBJ/DEP.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("DEP.OBJ", case["extra_objects"])
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("A.OBJ", case["extra_library_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        object_text = str(case["extra_objects"]["DEP.OBJ"])
        self.assertIn("b uAuzM", object_text)
        self.assertIn("r 1 uA", object_text)
        self.assertIn("r 4 uz", object_text)
        for unexpected_path in (
            "OBJ/D0.OBJ",
            "OBJ/D33.OBJ",
            "LIB/DEP.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_library_second_export_named_dependency_mixed_lettered_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_library_second_export_named_dependency_mixed_lettered_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/A.OBJ", "OBJ/DEP.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("DEP.OBJ", case["extra_objects"])
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("A.OBJ", case["extra_library_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        root_text = str(case["extra_library_objects"]["A.OBJ"])
        self.assertIn("r 1 x missing", root_text)
        self.assertIn("r 5 x dep", root_text)
        dep_text = str(case["extra_objects"]["DEP.OBJ"])
        self.assertIn("u d0", dep_text)
        self.assertIn("u projhelper", dep_text)
        self.assertIn("u d10", dep_text)
        self.assertIn("u libhelper", dep_text)
        self.assertIn("r 1 x projhelper", dep_text)
        self.assertIn("r 4 x libhelper", dep_text)
        for unexpected_path in (
            "OBJ/D0.OBJ",
            "OBJ/D33.OBJ",
            "LIB/DEP.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_library_dependency_dual_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_root_second_export_library_dependency_dual_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, core_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/A.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("A.OBJ", case["extra_library_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        for unexpected_path in (
            "OBJ/D0.OBJ",
            "OBJ/D33.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_dependency_mixed_lettered_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_root_second_export_dependency_mixed_lettered_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, core_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["OBJ/A.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("A.OBJ", case["extra_objects"])
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        object_text = str(case["extra_objects"]["A.OBJ"])
        self.assertIn("b uAuzM", object_text)
        self.assertIn("r 1 uA", object_text)
        self.assertIn("r 4 uz", object_text)
        for unexpected_path in (
            "LIB/A.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_library_dependency_mixed_lettered_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_root_second_export_library_dependency_mixed_lettered_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, core_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/A.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("A.OBJ", case["extra_library_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        object_text = str(case["extra_library_objects"]["A.OBJ"])
        self.assertIn("b uAuzM", object_text)
        self.assertIn("r 1 uA", object_text)
        self.assertIn("r 4 uz", object_text)
        for unexpected_path in (
            "OBJ/D0.OBJ",
            "OBJ/D33.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_named_dependency_mixed_lettered_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_root_second_export_named_dependency_mixed_lettered_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, core_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["OBJ/A.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("A.OBJ", case["extra_objects"])
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        self.assertIn("r 5 x a", case["seed_object"])
        object_text = str(case["extra_objects"]["A.OBJ"])
        self.assertIn("u d0", object_text)
        self.assertIn("u projhelper", object_text)
        self.assertIn("u d10", object_text)
        self.assertIn("u libhelper", object_text)
        self.assertIn("r 1 x projhelper", object_text)
        self.assertIn("r 4 x libhelper", object_text)
        for unexpected_path in (
            "OBJ/D0.OBJ",
            "OBJ/D33.OBJ",
            "LIB/A.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_named_library_dependency_mixed_lettered_lowercase_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_root_second_export_named_library_dependency_mixed_lettered_lowercase_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, core_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/A.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("A.OBJ", case["extra_library_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        self.assertIn("r 5 x a", case["seed_object"])
        object_text = str(case["extra_library_objects"]["A.OBJ"])
        self.assertIn("u d0", object_text)
        self.assertIn("u projhelper", object_text)
        self.assertIn("u d10", object_text)
        self.assertIn("u libhelper", object_text)
        self.assertIn("r 1 x projhelper", object_text)
        self.assertIn("r 4 x libhelper", object_text)
        for unexpected_path in (
            "OBJ/D0.OBJ",
            "OBJ/D33.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D33.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_lettered_helper_imports(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        expected_loads = {
            "object_code_root_second_export_lettered_import_project_helper": [
                "OBJ/HELPER.OBJ",
            ],
            "object_code_root_second_export_lettered_import_library_helper": [
                "LIB/HELPER.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertIn(shape, core_shapes)
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("x main 1 19", case["seed_object"])
                self.assertIn("b uAM", case["seed_object"])
                self.assertIn("r 2 uA", case["seed_object"])
                self.assertIn("LIB/D0.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/D9.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_library_dependency_dual_lettered_mixed_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_root_second_export_library_dependency_dual_lettered_import_mixed_helpers"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, core_shapes)
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/A.OBJ", "OBJ/PROJHELPER.OBJ", "LIB/LIBHELPER.OBJ"],
        )
        self.assertIn("PROJHELPER.OBJ", case["extra_objects"])
        self.assertIn("A.OBJ", case["extra_library_objects"])
        self.assertIn("LIBHELPER.OBJ", case["extra_library_objects"])
        for unexpected_path in (
            "OBJ/D0.OBJ",
            "OBJ/D9.OBJ",
            "LIB/PROJHELPER.OBJ",
            "LIB/D0.OBJ",
            "LIB/D9.OBJ",
        ):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_project_dependency_offset_root_local_export(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_root_second_export_project_dependency_imports_offset_root_local_export"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, core_shapes)
        self.assertEqual(case["expected_alink_loads"], ["OBJ/B.OBJ"])
        self.assertIn("B.OBJ", case["extra_objects"])
        self.assertIn("B.OBJ", case["extra_library_objects"])
        for unexpected_path in ("OBJ/A.OBJ", "LIB/A.OBJ", "LIB/B.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_project_dependency_root_local_export(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_root_second_export_project_dependency_imports_root_local_export"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, core_shapes)
        self.assertEqual(case["expected_alink_loads"], ["OBJ/B.OBJ"])
        self.assertIn("B.OBJ", case["extra_objects"])
        self.assertIn("B.OBJ", case["extra_library_objects"])
        for unexpected_path in ("OBJ/A.OBJ", "LIB/A.OBJ", "LIB/B.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_named_offset_local_library_tail(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_root_second_export_named_offset_local_and_library_project_tail"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, core_shapes)
        self.assertEqual(case["expected_alink_loads"], ["LIB/B.OBJ", "OBJ/C.OBJ"])
        self.assertIn("C.OBJ", case["extra_objects"])
        self.assertIn("B.OBJ", case["extra_library_objects"])
        self.assertIn("C.OBJ", case["extra_library_objects"])
        for unexpected_path in ("OBJ/A.OBJ", "LIB/A.OBJ", "LIB/C.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_project_second_export_dependency_root_local_export(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_second_export_dependency_imports_root_local_export"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(case["expected_alink_loads"], ["OBJ/B.OBJ", "OBJ/C.OBJ"])
        self.assertIn("B.OBJ", case["extra_objects"])
        self.assertIn("C.OBJ", case["extra_objects"])
        self.assertIn("B.OBJ", case["extra_library_objects"])
        self.assertIn("C.OBJ", case["extra_library_objects"])
        for unexpected_path in ("OBJ/A.OBJ", "LIB/A.OBJ", "LIB/B.OBJ", "LIB/C.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_project_second_export_root_local_export(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_second_export_imports_root_local_export"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(case["expected_alink_loads"], ["OBJ/B.OBJ"])
        self.assertIn("B.OBJ", case["extra_objects"])
        self.assertIn("B.OBJ", case["extra_library_objects"])
        for unexpected_path in ("OBJ/A.OBJ", "LIB/A.OBJ", "LIB/B.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_project_second_export_offset_root_local_export(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_second_export_imports_offset_root_local_export"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(case["expected_alink_loads"], ["OBJ/B.OBJ"])
        self.assertIn("B.OBJ", case["extra_objects"])
        self.assertIn("B.OBJ", case["extra_library_objects"])
        for unexpected_path in ("OBJ/A.OBJ", "LIB/A.OBJ", "LIB/B.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_project_second_export_dependency_offset_root_local_export(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_second_export_dependency_imports_offset_root_local_export"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(case["expected_alink_loads"], ["OBJ/B.OBJ", "OBJ/C.OBJ"])
        self.assertIn("B.OBJ", case["extra_objects"])
        self.assertIn("C.OBJ", case["extra_objects"])
        self.assertIn("B.OBJ", case["extra_library_objects"])
        self.assertIn("C.OBJ", case["extra_library_objects"])
        for unexpected_path in ("OBJ/A.OBJ", "LIB/A.OBJ", "LIB/B.OBJ", "LIB/C.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_project_dependency_lowercase_library_helper(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_dependency_lowercase_z_import_pruned"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(case["expected_alink_loads"], ["OBJ/A.OBJ", "LIB/HELPER.OBJ"])
        self.assertEqual(sorted(case["extra_objects"]), ["A.OBJ"])
        for unexpected_path in ("LIB/A.OBJ", "LIB/D0.OBJ", "LIB/D34.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_project_dependency_lowercase_library_helper_with_project_decoys(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_dependency_lowercase_z_import_library_helper"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(case["expected_alink_loads"], ["OBJ/A.OBJ", "LIB/HELPER.OBJ"])
        self.assertIn("A.OBJ", case["extra_objects"])
        self.assertNotIn("HELPER.OBJ", case["extra_objects"])
        for unexpected_path in ("OBJ/D0.OBJ", "OBJ/D34.OBJ", "LIB/A.OBJ", "LIB/D0.OBJ", "LIB/D34.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_project_dependency_lowercase_project_helper_with_project_decoys(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_project_dependency_lowercase_z_import_project_helper"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(case["expected_alink_loads"], ["OBJ/A.OBJ", "OBJ/HELPER.OBJ"])
        self.assertIn("A.OBJ", case["extra_objects"])
        self.assertIn("HELPER.OBJ", case["extra_objects"])
        for unexpected_path in ("OBJ/D0.OBJ", "OBJ/D34.OBJ", "LIB/A.OBJ", "LIB/HELPER.OBJ", "LIB/D0.OBJ", "LIB/D34.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_library_dependency_lowercase_library_helper(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_library_dependency_lowercase_z_import_library_helper"
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(case["expected_alink_loads"], ["LIB/A.OBJ", "LIB/HELPER.OBJ"])
        self.assertNotIn("HELPER.OBJ", case["extra_objects"])
        for unexpected_path in ("OBJ/D0.OBJ", "OBJ/D34.OBJ", "LIB/D0.OBJ", "LIB/D34.OBJ"):
            self.assertIn(unexpected_path, case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_external_back_edge_cycle(self) -> None:
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())

        self.assertIn(
            "object_code_external_back_edge_cycle",
            graph_shapes,
            "Object-code graph matrix must cover relocations back to an already-loaded library OBJ",
        )
        self.assertIn(
            "object_code_project_cycle",
            graph_shapes,
            "Object-code graph matrix must cover project-local cycle dependency closure",
        )
        self.assertIn(
            "object_code_project_back_edge_cycle",
            graph_shapes,
            "Object-code graph matrix must cover project-local relocations back to an already-loaded project OBJ",
        )
        self.assertIn(
            "object_code_root_second_export_project_back_edge_cycle",
            graph_shapes,
            "Object-code graph matrix must cover root second-export relocations through project-local cycles",
        )
        self.assertIn(
            "object_code_root_second_export_named_project_back_edge_cycle",
            graph_shapes,
            "Object-code graph matrix must cover root second-export named relocations through project-local cycles",
        )
        self.assertIn(
            "object_code_root_second_export_library_back_edge_cycle",
            graph_shapes,
            "Object-code graph matrix must cover root second-export relocations through library-only cycles",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_project_library_back_edge_cycle",
            graph_shapes,
            "Object-code graph matrix must cover root second-export cycles from project OBJ to library OBJ",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_library_project_back_edge_cycle",
            graph_shapes,
            "Object-code graph matrix must cover root second-export cycles from library OBJ to project OBJ",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_project_offset_back_edge_cycle",
            graph_shapes,
            "Object-code graph matrix must cover root second-export cycles through sliced project OBJ exports",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_library_offset_back_edge_cycle",
            graph_shapes,
            "Object-code graph matrix must cover root second-export cycles through sliced library OBJ exports",
        )
        self.assertIn(
            "object_code_mixed_project_library_back_edge_cycle",
            graph_shapes,
            "Object-code graph matrix must cover library relocations back to a project-local OBJ",
        )
        self.assertIn(
            "object_code_mixed_project_offset_back_edge_cycle",
            graph_shapes,
            "Object-code graph matrix must cover library relocations back to a sliced project OBJ export",
        )
        self.assertIn(
            "object_code_mixed_library_project_back_edge_cycle",
            graph_shapes,
            "Object-code graph matrix must cover project relocations back to a library OBJ",
        )
        self.assertIn(
            "object_code_mixed_library_offset_back_edge_cycle",
            graph_shapes,
            "Object-code graph matrix must cover project relocations back to a sliced library OBJ export",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_project_library_triangle",
            graph_shapes,
            "Object-code graph matrix must cover mixed project/library triangle dependency closure",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_library_project_triangle",
            graph_shapes,
            "Object-code graph matrix must cover mixed library/project triangle dependency closure",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_project_library_diamond",
            graph_shapes,
            "Object-code graph matrix must cover mixed project/library diamond dependency closure",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_library_project_diamond",
            graph_shapes,
            "Object-code graph matrix must cover mixed library/project diamond dependency closure",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_project_library_square",
            graph_shapes,
            "Object-code graph matrix must cover mixed project/library square dependency closure",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_library_project_square",
            graph_shapes,
            "Object-code graph matrix must cover mixed library/project square dependency closure",
        )
        self.assertIn(
            "object_code_external_triangle",
            graph_shapes,
            "Object-code graph matrix must cover library-only triangle dependency closure",
        )
        self.assertIn(
            "object_code_external_diamond",
            graph_shapes,
            "Object-code graph matrix must cover library-only diamond dependency closure",
        )
        self.assertIn(
            "object_code_external_square",
            graph_shapes,
            "Object-code graph matrix must cover library-only square dependency closure",
        )
        self.assertIn(
            "object_code_project_triangle",
            graph_shapes,
            "Object-code graph matrix must cover project-local triangle dependency closure",
        )
        self.assertIn(
            "object_code_project_diamond",
            graph_shapes,
            "Object-code graph matrix must cover project-local diamond dependency closure",
        )
        self.assertIn(
            "object_code_project_square",
            graph_shapes,
            "Object-code graph matrix must cover project-local square dependency closure",
        )
        named_topology_shapes = [
            "object_code_external_named_cycle",
            "object_code_project_named_cycle",
            "object_code_external_named_back_edge_cycle",
            "object_code_project_named_back_edge_cycle",
            "object_code_root_second_export_named_project_back_edge_cycle",
            "object_code_root_second_export_named_library_back_edge_cycle",
            "object_code_root_second_export_named_mixed_project_library_back_edge_cycle",
            "object_code_root_second_export_named_mixed_library_project_back_edge_cycle",
            "object_code_root_second_export_named_mixed_project_offset_back_edge_cycle",
            "object_code_root_second_export_named_mixed_library_offset_back_edge_cycle",
            "object_code_root_second_export_named_mixed_project_library_triangle",
            "object_code_root_second_export_named_mixed_library_project_triangle",
            "object_code_root_second_export_named_mixed_project_library_diamond",
            "object_code_root_second_export_named_mixed_library_project_diamond",
            "object_code_root_second_export_named_mixed_project_library_square",
            "object_code_root_second_export_named_mixed_library_project_square",
            "object_code_mixed_project_library_named_back_edge_cycle",
            "object_code_mixed_project_offset_named_back_edge_cycle",
            "object_code_mixed_library_project_named_back_edge_cycle",
            "object_code_mixed_library_offset_named_back_edge_cycle",
            "object_code_external_named_triangle",
            "object_code_external_named_diamond",
            "object_code_external_named_square",
            "object_code_project_named_triangle",
            "object_code_project_named_diamond",
            "object_code_project_named_square",
        ]
        for shape in named_topology_shapes:
            with self.subTest(shape=shape):
                self.assertIn(
                    shape,
                    graph_shapes,
                    "Object-code graph matrix must cover named topology dependency closure",
                )

    def test_object_code_graph_matrix_covers_named_topology_loads(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_external_named_cycle": ["LIB/A.OBJ", "LIB/B.OBJ"],
            "object_code_project_named_cycle": ["OBJ/A.OBJ", "OBJ/B.OBJ"],
            "object_code_external_named_back_edge_cycle": ["LIB/A.OBJ", "LIB/B.OBJ"],
            "object_code_project_named_back_edge_cycle": ["OBJ/A.OBJ", "OBJ/B.OBJ"],
            "object_code_root_second_export_named_project_back_edge_cycle": ["OBJ/A.OBJ", "OBJ/B.OBJ"],
            "object_code_root_second_export_named_library_back_edge_cycle": ["LIB/A.OBJ", "LIB/B.OBJ"],
            "object_code_root_second_export_named_mixed_project_library_back_edge_cycle": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_root_second_export_named_mixed_library_project_back_edge_cycle": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
            ],
            "object_code_root_second_export_named_mixed_project_offset_back_edge_cycle": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_root_second_export_named_mixed_library_offset_back_edge_cycle": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
            ],
            "object_code_root_second_export_named_mixed_project_library_triangle": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_root_second_export_named_mixed_library_project_triangle": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
            ],
            "object_code_root_second_export_named_mixed_project_library_diamond": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_root_second_export_named_mixed_library_project_diamond": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
                "OBJ/C.OBJ",
            ],
            "object_code_root_second_export_named_mixed_project_library_square": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
                "LIB/D.OBJ",
            ],
            "object_code_root_second_export_named_mixed_library_project_square": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
                "LIB/C.OBJ",
                "OBJ/D.OBJ",
            ],
            "object_code_mixed_project_library_named_back_edge_cycle": ["OBJ/A.OBJ", "LIB/B.OBJ"],
            "object_code_mixed_project_offset_named_back_edge_cycle": ["OBJ/A.OBJ", "LIB/B.OBJ"],
            "object_code_mixed_library_project_named_back_edge_cycle": ["LIB/A.OBJ", "OBJ/B.OBJ"],
            "object_code_mixed_library_offset_named_back_edge_cycle": ["LIB/A.OBJ", "OBJ/B.OBJ"],
            "object_code_external_named_triangle": ["LIB/A.OBJ", "LIB/B.OBJ"],
            "object_code_external_named_diamond": ["LIB/A.OBJ", "LIB/B.OBJ", "LIB/C.OBJ"],
            "object_code_external_named_square": ["LIB/A.OBJ", "LIB/B.OBJ", "LIB/C.OBJ", "LIB/D.OBJ"],
            "object_code_project_named_triangle": ["OBJ/A.OBJ", "OBJ/B.OBJ"],
            "object_code_project_named_diamond": ["OBJ/A.OBJ", "OBJ/B.OBJ", "OBJ/C.OBJ"],
            "object_code_project_named_square": ["OBJ/A.OBJ", "OBJ/B.OBJ", "OBJ/C.OBJ", "OBJ/D.OBJ"],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                object_text = str(case.get("extra_objects", {})) + str(case["extra_library_objects"])
                self.assertRegex(object_text, r"r \d+ x ")

    def test_object_code_core_matrix_covers_project_large_dependency_page_crossing(self) -> None:
        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())

        self.assertIn(
            "object_code_split_machine_records",
            core_shapes,
            "Object-code core matrix must cover concatenated split machine-code records",
        )
        self.assertIn(
            "object_code_split_dependency_machine_records",
            core_shapes,
            "Object-code core matrix must cover split dependency machine-code records",
        )
        self.assertIn(
            "object_code_named_symbol_relocations",
            core_shapes,
            "Object-code core matrix must cover symbol-name relocation targets",
        )
        self.assertIn(
            "object_code_named_symbol_relocation_import_closure",
            core_shapes,
            "Object-code core matrix must cover symbol-name relocations adding imports",
        )
        self.assertIn(
            "object_code_project_named_symbol_relocation_import_closure",
            core_shapes,
            "Object-code core matrix must cover symbol-name relocations adding project imports",
        )
        self.assertIn(
            "object_code_named_symbol_dependency_import_closure",
            core_shapes,
            "Object-code core matrix must cover dependency symbol-name relocations adding imports",
        )
        self.assertIn(
            "object_code_project_named_symbol_dependency_import_closure",
            core_shapes,
            "Object-code core matrix must cover project dependency symbol-name relocations adding imports",
        )
        self.assertIn(
            "object_code_named_symbol_dependency_local_export",
            core_shapes,
            "Object-code core matrix must cover dependency symbol-name relocations to local exports",
        )
        self.assertIn(
            "object_code_project_named_symbol_dependency_local_export",
            core_shapes,
            "Object-code core matrix must cover project dependency symbol-name relocations to local exports",
        )
        self.assertIn(
            "object_code_named_symbol_dependency_offset_local_export",
            core_shapes,
            "Object-code core matrix must cover offset dependency symbol-name relocations to local exports",
        )
        self.assertIn(
            "object_code_project_named_symbol_dependency_offset_local_export",
            core_shapes,
            "Object-code core matrix must cover project offset dependency symbol-name relocations to local exports",
        )
        self.assertIn(
            "object_code_mixed_project_library_named_symbol_dependency_import_closure",
            core_shapes,
            "Object-code core matrix must cover project deps with symbol-name relocations importing library tails",
        )
        self.assertIn(
            "object_code_mixed_project_library_named_symbol_dependency_local_export",
            core_shapes,
            "Object-code core matrix must cover project deps with symbol-name relocations to local exports and library tails",
        )
        self.assertIn(
            "object_code_mixed_project_library_named_symbol_dependency_offset_local_export",
            core_shapes,
            "Object-code core matrix must cover project offset deps with symbol-name relocations importing library tails",
        )
        self.assertIn(
            "object_code_mixed_library_project_named_symbol_dependency_import_closure",
            core_shapes,
            "Object-code core matrix must cover library deps with symbol-name relocations importing project tails",
        )
        self.assertIn(
            "object_code_mixed_library_project_named_symbol_dependency_local_export",
            core_shapes,
            "Object-code core matrix must cover library deps with symbol-name relocations to local exports and project tails",
        )
        self.assertIn(
            "object_code_mixed_library_project_named_symbol_dependency_offset_local_export",
            core_shapes,
            "Object-code core matrix must cover library offset deps with symbol-name relocations importing project tails",
        )
        self.assertIn(
            "object_code_reloc_scan_windowed_imports",
            core_shapes,
            "Object-code core matrix must cover relocation scans restored after source-windowed import lookup",
        )
        self.assertIn(
            "object_code_named_large_root_page_crossing",
            core_shapes,
            "Object-code core matrix must cover named root-body page-crossing relocations",
        )
        self.assertIn(
            "object_code_named_large_root_multi_reloc_page_crossing",
            core_shapes,
            "Object-code core matrix must cover multiple named root-body page-crossing relocations",
        )
        self.assertIn(
            "object_code_large_dependency_page_crossing",
            core_shapes,
            "Object-code core matrix must cover page-crossing relocations in library OBJ dependencies",
        )
        self.assertIn(
            "object_code_named_large_dependency_page_crossing",
            core_shapes,
            "Object-code core matrix must cover named page-crossing relocations in library OBJ dependencies",
        )
        self.assertIn(
            "object_code_project_large_dependency_page_crossing",
            core_shapes,
            "Object-code core matrix must cover page-crossing relocations in project OBJ dependencies",
        )
        self.assertIn(
            "object_code_project_named_large_dependency_page_crossing",
            core_shapes,
            "Object-code core matrix must cover named page-crossing relocations in project OBJ dependencies",
        )
        self.assertIn(
            "object_code_project_large_dependency_library_tail_page_crossing",
            core_shapes,
            "Object-code core matrix must cover project large OBJ dependencies that import library tails",
        )
        self.assertIn(
            "object_code_project_named_large_dependency_library_tail_page_crossing",
            core_shapes,
            "Object-code core matrix must cover named project large OBJ dependencies that import library tails",
        )
        self.assertIn(
            "object_code_library_large_dependency_project_tail_page_crossing",
            core_shapes,
            "Object-code core matrix must cover library large OBJ dependencies that import project tails",
        )
        self.assertIn(
            "object_code_library_named_large_dependency_project_tail_page_crossing",
            core_shapes,
            "Object-code core matrix must cover named library large OBJ dependencies that import project tails",
        )
        self.assertIn(
            "object_code_root_second_export_large_dependency_page_crossing",
            core_shapes,
            "Object-code core matrix must cover selected root exports with library page-crossing deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_large_dependency_page_crossing",
            core_shapes,
            "Object-code core matrix must cover selected root exports with named library page-crossing deps",
        )
        self.assertIn(
            "object_code_root_second_export_project_large_dependency_page_crossing",
            core_shapes,
            "Object-code core matrix must cover selected root exports with project page-crossing deps",
        )
        self.assertIn(
            "object_code_root_second_export_project_large_dependency_library_tail_page_crossing",
            core_shapes,
            "Object-code core matrix must cover selected root exports with project page-crossing deps and library tails",
        )
        self.assertIn(
            "object_code_root_second_export_library_large_dependency_project_tail_page_crossing",
            core_shapes,
            "Object-code core matrix must cover selected root exports with library page-crossing deps and project tails",
        )
        self.assertIn(
            "object_code_root_second_export_named_project_large_dependency_page_crossing",
            core_shapes,
            "Object-code core matrix must cover selected root exports with named project page-crossing deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_project_large_dependency_library_tail_page_crossing",
            core_shapes,
            "Object-code core matrix must cover selected root exports with named project page-crossing deps and library tails",
        )
        self.assertIn(
            "object_code_root_second_export_named_library_large_dependency_project_tail_page_crossing",
            core_shapes,
            "Object-code core matrix must cover selected root exports with named library page-crossing deps and project tails",
        )
        self.assertIn(
            "object_code_root_second_export_imports_root_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root exports importing root-local exports",
        )
        self.assertIn(
            "object_code_root_second_export_named_imports_root_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root exports with named imports to root-local exports",
        )
        self.assertIn(
            "object_code_root_second_export_imports_offset_root_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root exports importing offset root-local exports",
        )
        self.assertIn(
            "object_code_root_second_export_named_imports_offset_root_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root exports with named imports to offset root-local exports",
        )
        self.assertIn(
            "object_code_root_second_export_offset_local_and_library_project_tail",
            core_shapes,
            "Object-code core matrix must cover selected root exports importing offset root-local exports plus library/project tails",
        )
        self.assertIn(
            "object_code_root_second_export_named_offset_local_and_library_project_tail",
            core_shapes,
            "Object-code core matrix must cover selected root exports with named imports to offset root-local exports plus library/project tails",
        )
        self.assertIn(
            "object_code_root_second_export_named_symbol_import",
            core_shapes,
            "Object-code core matrix must cover selected root exports whose named relocations add imports",
        )
        self.assertIn(
            "object_code_root_second_export_project_named_symbol_import",
            core_shapes,
            "Object-code core matrix must cover selected root exports whose named relocations prefer project deps",
        )
        self.assertIn(
            "object_code_root_second_export_transitive_library_dependency",
            core_shapes,
            "Object-code core matrix must cover selected root exports closing transitive library deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_transitive_library_dependency",
            core_shapes,
            "Object-code core matrix must cover selected root exports closing named transitive library deps",
        )
        self.assertIn(
            "object_code_root_second_export_transitive_project_dependency",
            core_shapes,
            "Object-code core matrix must cover selected root exports closing transitive project deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_transitive_project_dependency",
            core_shapes,
            "Object-code core matrix must cover selected root exports closing named transitive project deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_symbol_dependency_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root exports whose dependency named relocations bind to local exports",
        )
        self.assertIn(
            "object_code_root_second_export_project_named_symbol_dependency_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root exports whose project dependency named relocations bind to local exports",
        )
        self.assertIn(
            "object_code_root_second_export_named_symbol_dependency_offset_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root exports whose dependency named relocations bind to offset local exports",
        )
        self.assertIn(
            "object_code_root_second_export_project_named_symbol_dependency_offset_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root exports whose project dependency named relocations bind to offset local exports",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_project_library_named_symbol_dependency_import_closure",
            core_shapes,
            "Object-code core matrix must cover selected root exports with project deps whose named relocations import library tails",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_project_library_named_symbol_dependency_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root exports with project deps whose named relocations bind local exports and import library tails",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_project_library_named_symbol_dependency_offset_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root exports with project offset deps whose named relocations import library tails",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_library_project_named_symbol_dependency_import_closure",
            core_shapes,
            "Object-code core matrix must cover selected root exports with library deps whose named relocations import project tails",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_library_project_named_symbol_dependency_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root exports with library deps whose named relocations bind local exports and import project tails",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_library_project_named_symbol_dependency_offset_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root exports with library offset deps whose named relocations import project tails",
        )
        self.assertIn(
            "object_code_root_second_export_project_second_export_library_tail",
            core_shapes,
            "Object-code core matrix must cover selected root exports through project second-export deps importing library tails",
        )
        self.assertIn(
            "object_code_root_second_export_named_project_second_export_library_tail",
            core_shapes,
            "Object-code core matrix must cover selected root exports through named project second-export deps importing library tails",
        )
        self.assertIn(
            "object_code_root_second_export_project_second_export_library_dependency_imports_project_tail",
            core_shapes,
            "Object-code core matrix must cover selected root exports through project second-export deps importing library deps with project tails",
        )
        self.assertIn(
            "object_code_root_second_export_named_project_second_export_library_dependency_imports_project_tail",
            core_shapes,
            "Object-code core matrix must cover selected root exports through named project second-export deps importing library deps with project tails",
        )
        self.assertIn(
            "object_code_root_second_export_library_second_export_project_second_export_tail",
            core_shapes,
            "Object-code core matrix must cover selected root exports through library second-export deps importing project second-export tails",
        )
        self.assertIn(
            "object_code_root_second_export_named_library_second_export_project_second_export_tail",
            core_shapes,
            "Object-code core matrix must cover selected root exports through named library second-export deps importing project second-export tails",
        )
        self.assertIn(
            "object_code_root_second_export_library_second_export_project_dependency_imports_library_tail",
            core_shapes,
            "Object-code core matrix must cover selected root exports through library second-export deps importing project deps with library tails",
        )
        self.assertIn(
            "object_code_root_second_export_named_library_second_export_project_dependency_imports_library_tail",
            core_shapes,
            "Object-code core matrix must cover selected root exports through named library second-export deps importing project deps with library tails",
        )
        self.assertIn(
            "object_code_root_second_export_dual_second_export_mixed_tails",
            core_shapes,
            "Object-code core matrix must cover selected root exports importing project and library second-export deps with mixed tails",
        )
        self.assertIn(
            "object_code_root_second_export_named_dual_second_export_mixed_tails",
            core_shapes,
            "Object-code core matrix must cover selected root exports whose named relocations import project and library second-export deps with mixed tails",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_dual_transitive_project_library_closure",
            core_shapes,
            "Object-code core matrix must cover selected root exports with mixed dual-transitive project/library closure",
        )
        self.assertIn(
            "object_code_root_second_export_named_mixed_dual_transitive_project_library_closure",
            core_shapes,
            "Object-code core matrix must cover selected root exports with named mixed dual-transitive project/library closure",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_dual_transitive_library_project_closure",
            core_shapes,
            "Object-code core matrix must cover selected root exports with mixed dual-transitive library/project closure",
        )
        self.assertIn(
            "object_code_root_second_export_named_mixed_dual_transitive_library_project_closure",
            core_shapes,
            "Object-code core matrix must cover selected root exports with named mixed dual-transitive library/project closure",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_project_library_dependency",
            core_shapes,
            "Object-code core matrix must cover selected root exports closing mixed project/library deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_mixed_project_library_dependency",
            core_shapes,
            "Object-code core matrix must cover selected root exports closing named mixed project/library deps",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_project_second_export_library_dependency",
            core_shapes,
            "Object-code core matrix must cover selected root exports closing mixed project second-export/library deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_mixed_project_second_export_library_dependency",
            core_shapes,
            "Object-code core matrix must cover selected root exports closing named mixed project second-export/library deps",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_library_project_dependency",
            core_shapes,
            "Object-code core matrix must cover selected root exports closing mixed library/project deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_mixed_library_project_dependency",
            core_shapes,
            "Object-code core matrix must cover selected root exports closing named mixed library/project deps",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_library_second_export_project_dependency",
            core_shapes,
            "Object-code core matrix must cover selected root exports closing mixed library second-export/project deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_mixed_library_second_export_project_dependency",
            core_shapes,
            "Object-code core matrix must cover selected root exports closing named mixed library second-export/project deps",
        )
        self.assertIn(
            "object_code_root_second_export_dual_import_project_library_dependencies",
            core_shapes,
            "Object-code core matrix must cover selected root exports directly importing project and library deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_dual_import_project_library_dependencies",
            core_shapes,
            "Object-code core matrix must cover selected root exports directly named-importing project and library deps",
        )
        self.assertIn(
            "object_code_root_second_export_dual_import_project_second_export_library_dependencies",
            core_shapes,
            "Object-code core matrix must cover selected root exports directly importing project and library second-export deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_dual_import_project_second_export_library_dependencies",
            core_shapes,
            "Object-code core matrix must cover selected root exports directly named-importing project and library second-export deps",
        )
        self.assertIn(
            "object_code_root_second_export_dual_import_library_project_dependencies",
            core_shapes,
            "Object-code core matrix must cover selected root exports directly importing library and project deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_dual_import_library_project_dependencies",
            core_shapes,
            "Object-code core matrix must cover selected root exports directly named-importing library and project deps",
        )
        self.assertIn(
            "object_code_root_second_export_dual_import_library_second_export_project_dependencies",
            core_shapes,
            "Object-code core matrix must cover selected root exports directly importing library and project second-export deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_dual_import_library_second_export_project_dependencies",
            core_shapes,
            "Object-code core matrix must cover selected root exports directly named-importing library and project second-export deps",
        )
        self.assertIn(
            "object_code_root_second_export_dual_import_project_dependencies",
            core_shapes,
            "Object-code core matrix must cover selected root exports directly importing two project deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_dual_import_project_dependencies",
            core_shapes,
            "Object-code core matrix must cover selected root exports directly named-importing two project deps",
        )
        self.assertIn(
            "object_code_root_second_export_dual_import_library_dependencies",
            core_shapes,
            "Object-code core matrix must cover selected root exports directly importing two library deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_dual_import_library_dependencies",
            core_shapes,
            "Object-code core matrix must cover selected root exports directly named-importing two library deps",
        )
        self.assertIn(
            "object_code_root_second_export_dual_import_shared_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping a shared library dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_dual_import_shared_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping a named shared library dep",
        )
        self.assertIn(
            "object_code_root_second_export_dual_import_project_second_export_shared_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping a shared library dep from project second-export deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_dual_import_project_second_export_shared_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping a named shared library dep from project second-export deps",
        )
        self.assertIn(
            "object_code_root_second_export_dual_import_shared_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping a shared project dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_dual_import_shared_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping a named shared project dep",
        )
        self.assertIn(
            "object_code_root_second_export_dual_import_library_second_export_shared_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping a shared project dep from library second-export deps",
        )
        self.assertIn(
            "object_code_root_second_export_named_dual_import_library_second_export_shared_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping a named shared project dep from library second-export deps",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_shared_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping mixed project/library deps that share a project dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_mixed_shared_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping named mixed project/library deps that share a project dep",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_shared_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping mixed project/library deps that share a library dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_mixed_shared_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping named mixed project/library deps that share a library dep",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_project_second_export_shared_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping mixed project/library deps that share a selected project dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_mixed_project_second_export_shared_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping named mixed project/library deps that share a selected project dep",
        )
        self.assertIn(
            "object_code_root_second_export_mixed_library_second_export_shared_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping mixed project/library deps that share a selected library dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_mixed_library_second_export_shared_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports deduping named mixed project/library deps that share a selected library dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_project_share_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and project OBJs sharing one project dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_root_project_share_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and project OBJs sharing one named project dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_library_share_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and library OBJs sharing one project dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_root_library_share_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and library OBJs sharing one named project dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_project_share_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and project OBJs sharing one library dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_root_project_share_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and project OBJs sharing one named library dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_library_share_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and library OBJs sharing one library dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_root_library_share_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and library OBJs sharing one named library dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_project_second_export_share_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and project OBJs sharing one selected project dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_root_project_second_export_share_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and project OBJs sharing one named selected project dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_library_second_export_share_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and library OBJs sharing one selected library dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_root_library_second_export_share_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and library OBJs sharing one named selected library dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_project_library_second_export_share_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and project OBJs sharing one selected library dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_root_project_library_second_export_share_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and project OBJs sharing one named selected library dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_library_project_second_export_share_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and library OBJs sharing one selected project dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_root_library_project_second_export_share_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports and library OBJs sharing one named selected project dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_project_library_project_second_export_share_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports, project OBJs, and library OBJs sharing one selected project dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_root_project_library_project_second_export_share_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports, project OBJs, and library OBJs sharing one named selected project dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_project_library_library_second_export_share_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports, project OBJs, and library OBJs sharing one selected library dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_root_project_library_library_second_export_share_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports, project OBJs, and library OBJs sharing one named selected library dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_project_library_share_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports, project OBJs, and library OBJs sharing one library dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_root_project_library_share_library_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports, project OBJs, and library OBJs sharing one named library dep",
        )
        self.assertIn(
            "object_code_root_second_export_root_project_library_share_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports, project OBJs, and library OBJs sharing one project dep",
        )
        self.assertIn(
            "object_code_root_second_export_named_root_project_library_share_project_dependency_dedup",
            core_shapes,
            "Object-code core matrix must cover selected root exports, project OBJs, and library OBJs sharing one named project dep",
        )
        self.assertIn(
            "object_code_root_second_export_dependency_dual_lettered_import_mixed_helpers",
            core_shapes,
            "Object-code core matrix must cover selected root-export deps with mixed lettered helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_named_dependency_dual_lettered_import_mixed_helpers",
            core_shapes,
            "Object-code core matrix must cover selected root-export named deps with mixed lettered helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_dependency_lowercase_z_import_project_helper",
            core_shapes,
            "Object-code core matrix must cover selected root-export deps with high-index project helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_named_dependency_lowercase_z_import_project_helper",
            core_shapes,
            "Object-code core matrix must cover selected root-export named deps with high-index project helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_dependency_lowercase_z_import_library_helper",
            core_shapes,
            "Object-code core matrix must cover selected root-export deps with high-index library helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_named_dependency_lowercase_z_import_library_helper",
            core_shapes,
            "Object-code core matrix must cover selected root-export named deps with high-index library helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_dependency_dual_lowercase_import_mixed_helpers",
            core_shapes,
            "Object-code core matrix must cover selected root-export deps with mixed high-index helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_dependency_mixed_lettered_lowercase_import_mixed_helpers",
            core_shapes,
            "Object-code core matrix must cover selected root-export deps with mixed lettered/high-index helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_named_dependency_dual_lowercase_import_mixed_helpers",
            core_shapes,
            "Object-code core matrix must cover selected root-export named deps with mixed high-index helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_named_dependency_mixed_lettered_lowercase_import_mixed_helpers",
            core_shapes,
            "Object-code core matrix must cover selected root-export named deps with mixed lettered/high-index helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_library_dependency_lowercase_z_import_project_helper",
            core_shapes,
            "Object-code core matrix must cover selected root-export library deps with high-index project helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_named_library_dependency_lowercase_z_import_project_helper",
            core_shapes,
            "Object-code core matrix must cover selected root-export named library deps with high-index project helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_library_dependency_lowercase_z_import_library_helper",
            core_shapes,
            "Object-code core matrix must cover selected root-export library deps with high-index library helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_named_library_dependency_lowercase_z_import_library_helper",
            core_shapes,
            "Object-code core matrix must cover selected root-export named library deps with high-index library helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_library_dependency_dual_lettered_import_mixed_helpers",
            core_shapes,
            "Object-code core matrix must cover selected root-export library deps with mixed lettered helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_named_library_dependency_dual_lettered_import_mixed_helpers",
            core_shapes,
            "Object-code core matrix must cover selected root-export named library deps with mixed lettered helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_library_dependency_dual_lowercase_import_mixed_helpers",
            core_shapes,
            "Object-code core matrix must cover selected root-export library deps with mixed high-index helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_library_dependency_mixed_lettered_lowercase_import_mixed_helpers",
            core_shapes,
            "Object-code core matrix must cover selected root-export library deps with mixed lettered/high-index helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_named_library_dependency_dual_lowercase_import_mixed_helpers",
            core_shapes,
            "Object-code core matrix must cover selected root-export named library deps with mixed high-index helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_named_library_dependency_mixed_lettered_lowercase_import_mixed_helpers",
            core_shapes,
            "Object-code core matrix must cover selected root-export named library deps with mixed lettered/high-index helper imports",
        )
        self.assertIn(
            "object_code_root_second_export_dependency_imports_root_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root-export deps importing root-local exports",
        )
        self.assertIn(
            "object_code_root_second_export_named_dependency_imports_root_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root-export deps named-importing root-local exports",
        )
        self.assertIn(
            "object_code_root_second_export_project_dependency_imports_root_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root-export project deps importing root-local exports",
        )
        self.assertIn(
            "object_code_root_second_export_named_project_dependency_imports_root_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root-export project deps named-importing root-local exports",
        )
        self.assertIn(
            "object_code_root_second_export_dependency_imports_offset_root_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root-export deps importing offset root-local exports",
        )
        self.assertIn(
            "object_code_root_second_export_named_dependency_imports_offset_root_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root-export deps named-importing offset root-local exports",
        )
        self.assertIn(
            "object_code_root_second_export_project_dependency_imports_offset_root_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root-export project deps importing offset root-local exports",
        )
        self.assertIn(
            "object_code_root_second_export_named_project_dependency_imports_offset_root_local_export",
            core_shapes,
            "Object-code core matrix must cover selected root-export project deps named-importing offset root-local exports",
        )

    def test_object_code_core_matrix_covers_root_second_export_project_library_project_tail_loads(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_root_second_export_project_second_export_library_dependency_imports_project_tail": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
            ],
            "object_code_root_second_export_named_project_second_export_library_dependency_imports_project_tail": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("A.OBJ", case["extra_objects"])
                self.assertIn("B.OBJ", case["extra_library_objects"])
                self.assertIn("C.OBJ", case["extra_objects"])
                self.assertIn("LIB/C.OBJ", case["unexpected_alink_loads"])
                object_text = str(case["extra_objects"]) + str(case["extra_library_objects"])
                self.assertIn("x a 4 4", object_text)
                self.assertIn("x b 4 4", object_text)

    def test_object_code_graph_matrix_covers_root_second_export_project_library_chain_loads(
        self,
    ) -> None:
        groups = self._makefile_object_code_shape_groups(self.make_text)
        graph_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES", set())
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_root_second_export_project_library_project_library_chain": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
                "LIB/D.OBJ",
            ],
            "object_code_root_second_export_named_project_library_project_library_chain": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
                "LIB/D.OBJ",
            ],
            "object_code_root_second_export_library_project_library_project_chain": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
                "LIB/C.OBJ",
                "OBJ/D.OBJ",
            ],
            "object_code_root_second_export_named_library_project_library_project_chain": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
                "LIB/C.OBJ",
                "OBJ/D.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                self.assertIn(shape, graph_shapes)
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                if loads[0] == "OBJ/A.OBJ":
                    self.assertIn("A.OBJ", case["extra_objects"])
                    self.assertIn("B.OBJ", case["extra_library_objects"])
                    self.assertIn("C.OBJ", case["extra_objects"])
                    self.assertIn("D.OBJ", case["extra_library_objects"])
                    self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
                    self.assertIn("LIB/C.OBJ", case["unexpected_alink_loads"])
                else:
                    self.assertIn("A.OBJ", case["extra_library_objects"])
                    self.assertIn("B.OBJ", case["extra_objects"])
                    self.assertIn("C.OBJ", case["extra_library_objects"])
                    self.assertIn("D.OBJ", case["extra_objects"])
                    self.assertIn("LIB/B.OBJ", case["unexpected_alink_loads"])
                    self.assertIn("LIB/D.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_mixed_second_export_dependency_loads(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        expected_loads = {
            "object_code_root_second_export_mixed_project_second_export_library_dependency": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_root_second_export_named_mixed_project_second_export_library_dependency": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_root_second_export_mixed_library_second_export_project_dependency": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
            ],
            "object_code_root_second_export_named_mixed_library_second_export_project_dependency": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                object_text = str(case.get("extra_objects", {})) + str(case["extra_library_objects"])
                self.assertIn(shape, core_shapes)
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertEqual(
                    case["expected_tail"],
                    bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
                )
                self.assertIn("x unused_a 0 4", object_text)
                self.assertIn("x a 4 4", object_text)
                self.assertIn("m 20 00 00 60 20 00 00 60", object_text)
                self.assertIn("OBJ/MISSING.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/MISSING.OBJ", case["unexpected_alink_loads"])
                if "_named_" in shape:
                    self.assertIn("r 5 x a", case["seed_object"])
                    self.assertIn("r 1 x missing", object_text)
                    self.assertIn("r 5 x b", object_text)
                else:
                    self.assertIn("r 2 u0", case["seed_object"])
                    self.assertIn("r 1 u0", object_text)
                    self.assertIn("r 5 u1", object_text)
                if loads[0] == "OBJ/A.OBJ":
                    self.assertIn("A.OBJ", case["extra_objects"])
                    self.assertIn("B.OBJ", case["extra_library_objects"])
                    self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
                else:
                    self.assertIn("B.OBJ", case["extra_objects"])
                    self.assertIn("A.OBJ", case["extra_library_objects"])
                    self.assertIn("B.OBJ", case["extra_library_objects"])
                    self.assertIn("LIB/B.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_dual_import_second_export_loads(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        expected_loads = {
            "object_code_root_second_export_dual_import_project_second_export_library_dependencies": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_root_second_export_named_dual_import_project_second_export_library_dependencies": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_root_second_export_dual_import_library_second_export_project_dependencies": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
            ],
            "object_code_root_second_export_named_dual_import_library_second_export_project_dependencies": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                object_text = str(case.get("extra_objects", {})) + str(
                    case["extra_library_objects"]
                )
                self.assertIn(shape, core_shapes)
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertEqual(
                    case["expected_tail"],
                    bytes.fromhex("201610201710A9A58DD003A90085028503A2024C0FCF6060"),
                )
                self.assertIn("x unused_a 0 4", object_text)
                self.assertIn("x a 4 1", object_text)
                self.assertIn("x unused_b 0 4", object_text)
                self.assertIn("x b 4 1", object_text)
                self.assertIn("m 20 00 00 60 60", object_text)
                self.assertIn("OBJ/MISSING.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/MISSING.OBJ", case["unexpected_alink_loads"])
                if "_named_" in shape:
                    self.assertIn("r 5 x a", case["seed_object"])
                    self.assertIn("r 8 x b", case["seed_object"])
                    self.assertIn("r 1 x missing", object_text)
                else:
                    self.assertIn("r 2 u0", case["seed_object"])
                    self.assertIn("r 5 u1", case["seed_object"])
                    self.assertIn("u missing", object_text)
                    self.assertIn("r 1 u0", object_text)
                if loads[0] == "OBJ/A.OBJ":
                    self.assertIn("A.OBJ", case["extra_objects"])
                    self.assertNotIn("B.OBJ", case["extra_objects"])
                    self.assertIn("B.OBJ", case["extra_library_objects"])
                    self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
                else:
                    self.assertIn("B.OBJ", case["extra_objects"])
                    self.assertNotIn("A.OBJ", case["extra_objects"])
                    self.assertIn("A.OBJ", case["extra_library_objects"])
                    self.assertIn("LIB/B.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_dual_import_second_export_shared_dedup(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        expected_loads = {
            "object_code_root_second_export_dual_import_project_second_export_shared_library_dependency_dedup": [
                "OBJ/A.OBJ",
                "OBJ/C.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_root_second_export_named_dual_import_project_second_export_shared_library_dependency_dedup": [
                "OBJ/A.OBJ",
                "OBJ/C.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_root_second_export_dual_import_library_second_export_shared_project_dependency_dedup": [
                "LIB/A.OBJ",
                "LIB/C.OBJ",
                "OBJ/B.OBJ",
            ],
            "object_code_root_second_export_named_dual_import_library_second_export_shared_project_dependency_dedup": [
                "LIB/A.OBJ",
                "LIB/C.OBJ",
                "OBJ/B.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                object_text = str(case.get("extra_objects", {})) + str(
                    case["extra_library_objects"]
                )
                self.assertIn(shape, core_shapes)
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertEqual(
                    case["expected_tail"],
                    bytes.fromhex(
                        "201610201A10A9A58DD003A90085028503A2024C0FCF201E1060201E106060"
                    ),
                )
                self.assertIn("x unused_a 0 4", object_text)
                self.assertIn("x a 4 4", object_text)
                self.assertIn("x unused_c 0 4", object_text)
                self.assertIn("x c 4 4", object_text)
                self.assertIn("m 20 00 00 60 20 00 00 60", object_text)
                self.assertIn("OBJ/MISSING.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/MISSING.OBJ", case["unexpected_alink_loads"])
                if "_named_" in shape:
                    self.assertIn("r 5 x a", case["seed_object"])
                    self.assertIn("r 8 x c", case["seed_object"])
                    self.assertIn("r 1 x missing", object_text)
                    self.assertIn("r 5 x b", object_text)
                else:
                    self.assertIn("r 2 u0", case["seed_object"])
                    self.assertIn("r 5 u1", case["seed_object"])
                    self.assertIn("u missing", object_text)
                    self.assertIn("u b", object_text)
                    self.assertIn("r 1 u0", object_text)
                    self.assertIn("r 5 u1", object_text)
                if loads[-1] == "LIB/B.OBJ":
                    self.assertIn("A.OBJ", case["extra_objects"])
                    self.assertIn("C.OBJ", case["extra_objects"])
                    self.assertIn("B.OBJ", case["extra_library_objects"])
                    self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
                    self.assertIn("LIB/C.OBJ", case["unexpected_alink_loads"])
                else:
                    self.assertEqual(["LIB/A.OBJ", "LIB/C.OBJ", "OBJ/B.OBJ"], loads)
                    self.assertIn("B.OBJ", case["extra_objects"])
                    self.assertIn("A.OBJ", case["extra_library_objects"])
                    self.assertIn("C.OBJ", case["extra_library_objects"])
                    self.assertIn("LIB/B.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_mixed_shared_dedup_loads(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        expected_loads = {
            "object_code_root_second_export_mixed_shared_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
            ],
            "object_code_root_second_export_named_mixed_shared_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
            ],
            "object_code_root_second_export_mixed_shared_library_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_root_second_export_named_mixed_shared_library_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_root_second_export_mixed_project_second_export_shared_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
            ],
            "object_code_root_second_export_named_mixed_project_second_export_shared_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
            ],
            "object_code_root_second_export_mixed_library_second_export_shared_library_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_root_second_export_named_mixed_library_second_export_shared_library_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "LIB/C.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                object_text = str(case.get("extra_objects", {})) + str(
                    case["extra_library_objects"]
                )
                self.assertIn(shape, core_shapes)
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertEqual(
                    case["expected_tail"],
                    bytes.fromhex(
                        "201610201A10A9A58DD003A90085028503A2024C0FCF201E1060201E106060"
                    ),
                )
                self.assertIn("A.OBJ", case["extra_objects"])
                self.assertIn("B.OBJ", case["extra_library_objects"])
                self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
                self.assertIn("OBJ/MISSING.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/MISSING.OBJ", case["unexpected_alink_loads"])
                if "second_export" in shape.replace("root_second_export_", ""):
                    self.assertIn("x unused_c 0 4", object_text)
                    self.assertIn("x c 4 1", object_text)
                    self.assertIn("m 20 00 00 60 60", object_text)
                    if "_named_" in shape:
                        self.assertIn("r 5 x a", case["seed_object"])
                        self.assertIn("r 8 x b", case["seed_object"])
                        self.assertIn("r 1 x missing", object_text)
                    else:
                        self.assertIn("r 5 u1", case["seed_object"])
                        self.assertIn("r 8 u2", case["seed_object"])
                        self.assertIn("u missing", object_text)
                        self.assertIn("r 1 u0", object_text)
                if loads[-1] == "OBJ/C.OBJ":
                    self.assertIn("C.OBJ", case["extra_objects"])
                    self.assertIn("LIB/C.OBJ", case["unexpected_alink_loads"])
                else:
                    self.assertIn("C.OBJ", case["extra_library_objects"])

    def test_object_code_core_matrix_covers_root_second_export_selected_shared_dedup_loads(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        expected_loads = {
            "object_code_root_second_export_root_project_second_export_share_project_dependency_dedup": [
                "OBJ/A.OBJ",
                "OBJ/B.OBJ",
            ],
            "object_code_root_second_export_named_root_project_second_export_share_project_dependency_dedup": [
                "OBJ/A.OBJ",
                "OBJ/B.OBJ",
            ],
            "object_code_root_second_export_root_library_second_export_share_library_dependency_dedup": [
                "LIB/B.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_root_second_export_named_root_library_second_export_share_library_dependency_dedup": [
                "LIB/B.OBJ",
                "LIB/C.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                object_text = str(case.get("extra_objects", {})) + str(
                    case["extra_library_objects"]
                )
                self.assertIn(shape, core_shapes)
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("m 20 00 00 60 60", object_text)
                self.assertIn("OBJ/MISSING.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/MISSING.OBJ", case["unexpected_alink_loads"])
                if "_named_" in shape:
                    self.assertIn("r 5 x", case["seed_object"])
                    self.assertIn("r 1 x missing", object_text)
                else:
                    self.assertIn("r 2 u0", case["seed_object"])
                    self.assertIn("u missing", object_text)
                    self.assertIn("r 1 u0", object_text)
                if "project_second_export" in shape:
                    self.assertEqual(
                        case["expected_tail"],
                        bytes.fromhex(
                            "201610201710A9A58DD003A90085028503A2024C0FCF6020161060"
                        ),
                    )
                    self.assertIn("x unused_a 0 4", object_text)
                    self.assertIn("x a 4 1", object_text)
                    self.assertIn("A.OBJ", case["extra_objects"])
                    self.assertIn("B.OBJ", case["extra_objects"])
                    self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
                    self.assertIn("LIB/B.OBJ", case["unexpected_alink_loads"])
                else:
                    self.assertEqual(
                        case["expected_tail"],
                        bytes.fromhex(
                            "201610201A10A9A58DD003A90085028503A2024C0FCF201A106060"
                        ),
                    )
                    self.assertIn("x unused_c 0 4", object_text)
                    self.assertIn("x c 4 1", object_text)
                    self.assertIn("B.OBJ", case["extra_library_objects"])
                    self.assertIn("C.OBJ", case["extra_library_objects"])
                    self.assertIn("OBJ/B.OBJ", case["unexpected_alink_loads"])
                    self.assertIn("OBJ/C.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_selected_cross_location_dedup_loads(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        expected_loads = {
            "object_code_root_second_export_root_project_library_second_export_share_library_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_root_second_export_named_root_project_library_second_export_share_library_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_root_second_export_root_library_project_second_export_share_project_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_root_second_export_named_root_library_project_second_export_share_project_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                object_text = str(case.get("extra_objects", {})) + str(
                    case["extra_library_objects"]
                )
                self.assertIn(shape, core_shapes)
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("m 20 00 00 60 60", object_text)
                self.assertIn("OBJ/MISSING.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/MISSING.OBJ", case["unexpected_alink_loads"])
                if "_named_" in shape:
                    self.assertIn("r 5 x", case["seed_object"])
                    self.assertIn("r 1 x missing", object_text)
                else:
                    self.assertIn("r 2 u0", case["seed_object"])
                    self.assertIn("u missing", object_text)
                    self.assertIn("r 1 u0", object_text)
                if "library_second_export" in shape:
                    self.assertEqual(
                        case["expected_tail"],
                        bytes.fromhex(
                            "201610201A10A9A58DD003A90085028503A2024C0FCF201A106060"
                        ),
                    )
                    self.assertIn("A.OBJ", case["extra_objects"])
                    self.assertIn("C.OBJ", case["extra_library_objects"])
                    self.assertIn("x unused_c 0 4", object_text)
                    self.assertIn("x c 4 1", object_text)
                    self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
                    self.assertIn("OBJ/C.OBJ", case["unexpected_alink_loads"])
                else:
                    self.assertEqual(
                        case["expected_tail"],
                        bytes.fromhex(
                            "201610201710A9A58DD003A90085028503A2024C0FCF6020161060"
                        ),
                    )
                    self.assertIn("A.OBJ", case["extra_objects"])
                    self.assertIn("B.OBJ", case["extra_library_objects"])
                    self.assertIn("x unused_a 0 4", object_text)
                    self.assertIn("x a 4 1", object_text)
                    self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
                    self.assertIn("OBJ/B.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_mixed_selected_shared_dedup_loads(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        groups = self._makefile_object_code_shape_groups(self.make_text)
        core_shapes = groups.get("ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES", set())
        expected_loads = {
            "object_code_root_second_export_root_project_library_project_second_export_share_project_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
            ],
            "object_code_root_second_export_named_root_project_library_project_second_export_share_project_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "OBJ/C.OBJ",
            ],
            "object_code_root_second_export_root_project_library_library_second_export_share_library_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_root_second_export_named_root_project_library_library_second_export_share_library_dependency_dedup": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "LIB/C.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                object_text = str(case.get("extra_objects", {})) + str(
                    case["extra_library_objects"]
                )
                self.assertIn(shape, core_shapes)
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertEqual(
                    case["expected_tail"],
                    bytes.fromhex(
                        "201910201D10202110A9A58DD003A90085028503A2024C0FCF202110602021106060"
                    ),
                )
                self.assertIn("A.OBJ", case["extra_objects"])
                self.assertIn("B.OBJ", case["extra_library_objects"])
                self.assertIn("x unused_c 0 4", object_text)
                self.assertIn("x c 4 1", object_text)
                self.assertIn("m 20 00 00 60 60", object_text)
                self.assertIn("OBJ/MISSING.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/MISSING.OBJ", case["unexpected_alink_loads"])
                if "_named_" in shape:
                    self.assertIn("r 11 x c", case["seed_object"])
                    self.assertIn("r 1 x missing", object_text)
                else:
                    self.assertIn("r 8 u2", case["seed_object"])
                    self.assertIn("u missing", object_text)
                    self.assertIn("r 1 u0", object_text)
                if "project_second_export" in shape:
                    self.assertIn("C.OBJ", case["extra_objects"])
                    self.assertIn("LIB/C.OBJ", case["unexpected_alink_loads"])
                else:
                    self.assertIn("C.OBJ", case["extra_library_objects"])
                    self.assertIn("OBJ/C.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_mixed_dual_transitive_loads(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_root_second_export_mixed_dual_transitive_project_library_closure": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "LIB/C.OBJ",
                "OBJ/D.OBJ",
            ],
            "object_code_root_second_export_named_mixed_dual_transitive_project_library_closure": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
                "LIB/C.OBJ",
                "OBJ/D.OBJ",
            ],
            "object_code_root_second_export_mixed_dual_transitive_library_project_closure": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
                "OBJ/C.OBJ",
                "LIB/D.OBJ",
            ],
            "object_code_root_second_export_named_mixed_dual_transitive_library_project_closure": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
                "OBJ/C.OBJ",
                "LIB/D.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertEqual(
                    case["expected_tail"],
                    bytes.fromhex(
                        "201610201A10A9A58DD003A90085028503A2024C0FCF201E1060201F10606060"
                    ),
                )
                self.assertIn("OBJ/MISSING.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/MISSING.OBJ", case["unexpected_alink_loads"])
                if loads[0] == "OBJ/A.OBJ":
                    self.assertIn("A.OBJ", case["extra_objects"])
                    self.assertIn("D.OBJ", case["extra_objects"])
                    self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
                    self.assertIn("LIB/D.OBJ", case["unexpected_alink_loads"])
                else:
                    self.assertIn("B.OBJ", case["extra_objects"])
                    self.assertIn("C.OBJ", case["extra_objects"])
                    self.assertIn("LIB/B.OBJ", case["unexpected_alink_loads"])
                    self.assertIn("LIB/C.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_mixed_named_symbol_dependency_loads(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_root_second_export_mixed_project_library_named_symbol_dependency_import_closure": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_root_second_export_mixed_library_project_named_symbol_dependency_import_closure": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("r 5 x a", case["seed_object"])
                self.assertEqual(
                    case["expected_tail"],
                    bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
                )
                self.assertIn("OBJ/MISSING.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/MISSING.OBJ", case["unexpected_alink_loads"])
                if loads[0] == "OBJ/A.OBJ":
                    self.assertIn("A.OBJ", case["extra_objects"])
                    self.assertIn("B.OBJ", case["extra_library_objects"])
                    self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
                    self.assertIn("OBJ/B.OBJ", case["unexpected_alink_loads"])
                else:
                    self.assertIn("B.OBJ", case["extra_objects"])
                    self.assertIn("A.OBJ", case["extra_library_objects"])
                    self.assertIn("OBJ/A.OBJ", case["unexpected_alink_loads"])
                    self.assertIn("LIB/B.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_mixed_named_symbol_dependency_offset_local_exports(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_mixed_project_library_named_symbol_dependency_offset_local_export": [
                "OBJ/A.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_mixed_library_project_named_symbol_dependency_offset_local_export": [
                "LIB/A.OBJ",
                "OBJ/C.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("r 1 u0", case["seed_object"])
                object_text = str(case.get("extra_objects", {})) + str(case["extra_library_objects"])
                self.assertIn("x a 2 8", object_text)
                self.assertIn("x b 9 1", object_text)
                self.assertIn("u c", object_text)
                self.assertIn("r 4 x b", object_text)
                self.assertIn("r 7 x c", object_text)
                self.assertEqual(
                    case["expected_tail"],
                    bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCFEA201A10201B106060"),
                )
                self.assertIn("OBJ/B.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/B.OBJ", case["unexpected_alink_loads"])
                if loads[0] == "OBJ/A.OBJ":
                    self.assertIn("A.OBJ", case["extra_objects"])
                    self.assertIn("C.OBJ", case["extra_library_objects"])
                    self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
                else:
                    self.assertIn("A.OBJ", case["extra_library_objects"])
                    self.assertIn("C.OBJ", case["extra_objects"])
                    self.assertIn("OBJ/A.OBJ", case["unexpected_alink_loads"])
                    self.assertIn("LIB/C.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_mixed_named_symbol_dependency_local_exports(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_mixed_project_library_named_symbol_dependency_local_export": [
                "OBJ/A.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_mixed_library_project_named_symbol_dependency_local_export": [
                "LIB/A.OBJ",
                "OBJ/C.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("r 1 u0", case["seed_object"])
                object_text = str(case.get("extra_objects", {})) + str(case["extra_library_objects"])
                self.assertIn("x a 0 7", object_text)
                self.assertIn("x b 6 1", object_text)
                self.assertIn("u c", object_text)
                self.assertIn("r 1 x b", object_text)
                self.assertIn("r 4 x c", object_text)
                self.assertEqual(
                    case["expected_tail"],
                    bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF201910201A106060"),
                )
                self.assertIn("OBJ/B.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/B.OBJ", case["unexpected_alink_loads"])
                if loads[0] == "OBJ/A.OBJ":
                    self.assertIn("A.OBJ", case["extra_objects"])
                    self.assertIn("C.OBJ", case["extra_library_objects"])
                    self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
                else:
                    self.assertIn("A.OBJ", case["extra_library_objects"])
                    self.assertIn("C.OBJ", case["extra_objects"])
                    self.assertIn("OBJ/A.OBJ", case["unexpected_alink_loads"])
                    self.assertIn("LIB/C.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_mixed_named_symbol_dependency_offset_local_exports(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_root_second_export_mixed_project_library_named_symbol_dependency_offset_local_export": [
                "OBJ/A.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_root_second_export_mixed_library_project_named_symbol_dependency_offset_local_export": [
                "LIB/A.OBJ",
                "OBJ/C.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("r 5 x a", case["seed_object"])
                object_text = str(case.get("extra_objects", {})) + str(case["extra_library_objects"])
                self.assertIn("x a 2 8", object_text)
                self.assertIn("x b 9 1", object_text)
                self.assertIn("u c", object_text)
                self.assertIn("r 4 x b", object_text)
                self.assertIn("r 7 x c", object_text)
                self.assertEqual(
                    case["expected_tail"],
                    bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCFEA201A10201B106060"),
                )
                self.assertIn("OBJ/B.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/B.OBJ", case["unexpected_alink_loads"])
                self.assertIn("OBJ/MISSING.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/MISSING.OBJ", case["unexpected_alink_loads"])
                if loads[0] == "OBJ/A.OBJ":
                    self.assertIn("A.OBJ", case["extra_objects"])
                    self.assertIn("C.OBJ", case["extra_library_objects"])
                    self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
                else:
                    self.assertIn("A.OBJ", case["extra_library_objects"])
                    self.assertIn("C.OBJ", case["extra_objects"])
                    self.assertIn("OBJ/A.OBJ", case["unexpected_alink_loads"])
                    self.assertIn("LIB/C.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_mixed_named_symbol_dependency_local_exports(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_root_second_export_mixed_project_library_named_symbol_dependency_local_export": [
                "OBJ/A.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_root_second_export_mixed_library_project_named_symbol_dependency_local_export": [
                "LIB/A.OBJ",
                "OBJ/C.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("r 5 x a", case["seed_object"])
                object_text = str(case.get("extra_objects", {})) + str(case["extra_library_objects"])
                self.assertIn("x a 0 7", object_text)
                self.assertIn("x b 6 1", object_text)
                self.assertIn("u c", object_text)
                self.assertIn("r 1 x b", object_text)
                self.assertIn("r 4 x c", object_text)
                self.assertEqual(
                    case["expected_tail"],
                    bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF201910201A106060"),
                )
                self.assertIn("OBJ/B.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/B.OBJ", case["unexpected_alink_loads"])
                self.assertIn("OBJ/MISSING.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/MISSING.OBJ", case["unexpected_alink_loads"])
                if loads[0] == "OBJ/A.OBJ":
                    self.assertIn("A.OBJ", case["extra_objects"])
                    self.assertIn("C.OBJ", case["extra_library_objects"])
                    self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
                else:
                    self.assertIn("A.OBJ", case["extra_library_objects"])
                    self.assertIn("C.OBJ", case["extra_objects"])
                    self.assertIn("OBJ/A.OBJ", case["unexpected_alink_loads"])
                    self.assertIn("LIB/C.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_named_symbol_dependency_local_exports(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_root_second_export_named_symbol_dependency_local_export": [
                "LIB/A.OBJ",
            ],
            "object_code_root_second_export_project_named_symbol_dependency_local_export": [
                "OBJ/A.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("r 5 x a", case["seed_object"])
                object_text = str(case.get("extra_objects", {})) + str(case["extra_library_objects"])
                self.assertIn("x b 4 1", object_text)
                self.assertEqual(
                    case["expected_tail"],
                    bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
                )
                self.assertIn("OBJ/MISSING.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/MISSING.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/B.OBJ", case["unexpected_alink_loads"])
                if loads == ["OBJ/A.OBJ"]:
                    self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])
                    self.assertIn("OBJ/B.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_named_symbol_dependency_offset_local_exports(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_root_second_export_named_symbol_dependency_offset_local_export": [
                "LIB/A.OBJ",
            ],
            "object_code_root_second_export_project_named_symbol_dependency_offset_local_export": [
                "OBJ/A.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("r 5 x a", case["seed_object"])
                object_text = str(case.get("extra_objects", {})) + str(case["extra_library_objects"])
                self.assertIn("x a 2 5", object_text)
                self.assertIn("x b 6 1", object_text)
                self.assertIn("r 4 x b", object_text)
                self.assertEqual(
                    case["expected_tail"],
                    bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCFEA20171060"),
                )
                self.assertIn("OBJ/B.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/B.OBJ", case["unexpected_alink_loads"])
                self.assertIn("OBJ/MISSING.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/MISSING.OBJ", case["unexpected_alink_loads"])
                if loads == ["OBJ/A.OBJ"]:
                    self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_named_symbol_dependency_offset_local_exports(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_named_symbol_dependency_offset_local_export": [
                "LIB/A.OBJ",
            ],
            "object_code_project_named_symbol_dependency_offset_local_export": [
                "OBJ/A.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("r 1 u0", case["seed_object"])
                object_text = str(case.get("extra_objects", {})) + str(case["extra_library_objects"])
                self.assertIn("x a 2 5", object_text)
                self.assertIn("x b 6 1", object_text)
                self.assertIn("r 4 x b", object_text)
                self.assertEqual(
                    case["expected_tail"],
                    bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCFEA20171060"),
                )
                self.assertIn("OBJ/B.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/B.OBJ", case["unexpected_alink_loads"])
                if loads == ["OBJ/A.OBJ"]:
                    self.assertIn("LIB/A.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_root_second_export_library_project_library_tail_loads(
        self,
    ) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_root_second_export_library_second_export_project_dependency_imports_library_tail": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
                "LIB/C.OBJ",
            ],
            "object_code_root_second_export_named_library_second_export_project_dependency_imports_library_tail": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
                "LIB/C.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("A.OBJ", case["extra_library_objects"])
                self.assertIn("B.OBJ", case["extra_objects"])
                self.assertIn("C.OBJ", case["extra_library_objects"])
                self.assertIn("LIB/B.OBJ", case["unexpected_alink_loads"])
                self.assertIn("OBJ/C.OBJ", case["unexpected_alink_loads"])
                object_text = str(case["extra_objects"]) + str(case["extra_library_objects"])
                self.assertIn("x a 4 4", object_text)
                self.assertIn("x b 4 4", object_text)

    def test_object_code_core_matrix_covers_root_second_export_named_single_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_root_second_export_named_dependency_lowercase_z_import_project_helper": [
                "OBJ/A.OBJ",
                "OBJ/HELPER.OBJ",
            ],
            "object_code_root_second_export_named_dependency_lowercase_z_import_library_helper": [
                "OBJ/A.OBJ",
                "LIB/HELPER.OBJ",
            ],
            "object_code_root_second_export_named_library_dependency_lowercase_z_import_project_helper": [
                "LIB/A.OBJ",
                "OBJ/HELPER.OBJ",
            ],
            "object_code_root_second_export_named_library_dependency_lowercase_z_import_library_helper": [
                "LIB/A.OBJ",
                "LIB/HELPER.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                self.assertIn("OBJ/D34.OBJ", case["unexpected_alink_loads"])
                self.assertIn("LIB/D34.OBJ", case["unexpected_alink_loads"])

    def test_object_code_core_matrix_covers_named_large_page_crossing_loads(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_named_large_dependency_page_crossing": ["LIB/A.OBJ", "LIB/B.OBJ"],
            "object_code_named_large_root_page_crossing": ["LIB/HELPER.OBJ"],
            "object_code_named_large_root_multi_reloc_page_crossing": ["LIB/A.OBJ", "LIB/B.OBJ"],
            "object_code_project_named_large_dependency_page_crossing": ["OBJ/A.OBJ", "OBJ/B.OBJ"],
            "object_code_project_named_large_dependency_library_tail_page_crossing": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_library_named_large_dependency_project_tail_page_crossing": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
            ],
            "object_code_root_second_export_named_large_dependency_page_crossing": [
                "LIB/A.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_root_second_export_named_project_large_dependency_page_crossing": [
                "OBJ/A.OBJ",
                "OBJ/B.OBJ",
            ],
            "object_code_root_second_export_named_project_large_dependency_library_tail_page_crossing": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_root_second_export_named_library_large_dependency_project_tail_page_crossing": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
            ],
        }
        expected_relocation_fragments = {
            "object_code_named_large_root_page_crossing": "r 1 x helper",
            "object_code_named_large_root_multi_reloc_page_crossing": "r 1 x a",
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                object_text = str(case.get("seed_object", "")) + str(case.get("extra_objects", {})) + str(case["extra_library_objects"])
                self.assertIn(expected_relocation_fragments.get(shape, "r 1 x b"), object_text)
                self.assertGreater(len(case["expected_tail"]), 0x100)

    def test_object_code_core_matrix_covers_indexed_large_page_crossing_loads(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_loads = {
            "object_code_root_second_export_project_large_dependency_library_tail_page_crossing": [
                "OBJ/A.OBJ",
                "LIB/B.OBJ",
            ],
            "object_code_root_second_export_library_large_dependency_project_tail_page_crossing": [
                "LIB/A.OBJ",
                "OBJ/B.OBJ",
            ],
        }

        for shape, loads in expected_loads.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertEqual(case["expected_alink_loads"], loads)
                object_text = str(case.get("seed_object", "")) + str(case.get("extra_objects", {})) + str(case["extra_library_objects"])
                self.assertIn("r 1 u0", object_text)
                self.assertGreater(len(case["expected_tail"]), 0x100)

    @staticmethod
    def _makefile_object_code_shape_groups(make_text: str) -> dict[str, set[str]]:
        return {
            group: set(shapes)
            for group, shapes in TestAlinkPrgObjectCodeMatrix._makefile_object_code_shape_group_lists(
                make_text
            ).items()
        }

    @staticmethod
    def _makefile_object_code_shape_group_lists(make_text: str) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {}
        current_group: str | None = None

        for line in make_text.splitlines():
            group_match = re.match(r"^(ACTION_ALINK_PRG_OBJECT_CODE_[A-Z_]*SHAPES)\s*:=", line)
            if group_match:
                current_group = group_match.group(1)
                groups[current_group] = []

            if current_group is not None:
                groups[current_group].extend(re.findall(r"\bobject_code_[A-Za-z0-9_]+", line))
                if not line.rstrip().endswith("\\"):
                    current_group = None

        return groups

    @staticmethod
    def _makefile_object_code_rejection_cases(make_text: str) -> set[str]:
        return set(TestAlinkPrgObjectCodeMatrix._makefile_object_code_rejection_case_list(make_text))

    @staticmethod
    def _makefile_object_code_rejection_case_list(make_text: str) -> list[str]:
        cases: list[str] = []
        in_group = False

        for line in make_text.splitlines():
            if re.match(r"^ACTION_ALINK_PRG_OBJECT_CODE_REJECTION_CASES\s*:=", line):
                in_group = True

            if in_group:
                cases.extend(re.findall(r"\bobject_code_[A-Za-z0-9_]+", line))
                if not line.rstrip().endswith("\\"):
                    in_group = False

        return cases

    @staticmethod
    def _makefile_target_submakes(make_text: str, target_name: str) -> list[str]:
        target_header = f"{target_name}:"
        in_target = False
        targets: list[str] = []

        for line in make_text.splitlines():
            if line.startswith(target_header):
                in_target = True
                continue
            if in_target and line and not line.startswith(("\t", " ")):
                break
            if not in_target:
                continue
            match = re.match(r"[ \t]*\$\(MAKE\)\s+([A-Za-z0-9_.-]+)", line)
            if match:
                targets.append(match.group(1))

        return targets

    @staticmethod
    def _makefile_target_body(make_text: str, target_name: str) -> str:
        target_header = f"{target_name}:"
        in_target = False
        lines: list[str] = []

        for line in make_text.splitlines():
            if line.startswith(target_header):
                in_target = True
                continue
            if in_target and line and not line.startswith(("\t", " ")):
                break
            if in_target:
                lines.append(line)

        return "\n".join(lines)


if __name__ == "__main__":
    unittest.main()
