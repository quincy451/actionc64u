from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


class TestActcAlinkRuntimeMatrix(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = Path(__file__).resolve().parents[2]
        self.make_text = (self.workspace / "udos" / "Makefile").read_text()

    def _assert_native_runtime_seed(self, case: dict[str, object], legacy_body: str) -> None:
        seed = str(case["seed_object"])
        body = next(line for line in seed.splitlines() if line.startswith("b "))
        expected_calls = re.findall(r"u([0-9A-Z])", legacy_body)
        body_calls = re.findall(r"u([0-9A-Z])", body)
        reloc_calls = re.findall(r"^r \d+ u([0-9A-Z])$", seed, re.MULTILINE)

        self.assertTrue(body.endswith("M"), body)
        self.assertIn("\nm ", "\n" + seed)
        self.assertEqual(body_calls, expected_calls)
        self.assertEqual(reloc_calls, expected_calls)
        self.assertNotIn(legacy_body, seed)

    def test_all_actc_runtime_probe_shapes_are_listed_in_makefile_matrices(self) -> None:
        probe_text = (self.workspace / "udos" / "tools" / "run_action_alink_prg_probe.py").read_text()

        probe_shapes = set(re.findall(r'"(actc_runtime_[^"]+)"\s*:', probe_text))
        probe_shapes.update(
            re.findall(r"_add_derived_[^(]+\(\s*\n\s*\"(actc_runtime_[^\"]+)\"", probe_text)
        )
        probe_shapes.update(
            re.findall(r"DIRECT_PRG_CASES\[\"(actc_runtime_[^\"]+)\"\]", probe_text)
        )
        matrix_groups = self._makefile_runtime_matrix_shape_groups(self.make_text)
        matrix_shapes = {shape for shapes in matrix_groups.values() for shape in shapes}

        missing = sorted(probe_shapes - matrix_shapes)
        stale = sorted(matrix_shapes - probe_shapes)
        unrun_groups = sorted(group for group in matrix_groups if f"for shape in $({group})" not in self.make_text)

        self.assertFalse(missing, "ACTC runtime probe shapes missing from Makefile matrices: " + ", ".join(missing))
        self.assertFalse(stale, "Makefile runtime matrix shapes missing from probe cases: " + ", ".join(stale))
        self.assertFalse(unrun_groups, "Makefile runtime matrix groups not used by a target: " + ", ".join(unrun_groups))

    def test_aggregate_target_runs_all_focused_runtime_matrices(self) -> None:
        focused_targets = set(
            re.findall(r"^\.PHONY:\s+(vice-action-actc-alink-launch-\S*runtime-matrix)$", self.make_text, re.MULTILINE)
        )
        expected_targets = focused_targets | {"vice-action-actc-alink-launch-helper-demos"}
        aggregate_targets = self._makefile_target_submakes(
            self.make_text,
            "vice-action-actc-alink-launch-runtime-matrices",
        )

        missing = sorted(expected_targets - aggregate_targets)
        stale = sorted(aggregate_targets - expected_targets)

        self.assertFalse(missing, "Focused runtime targets missing from aggregate: " + ", ".join(missing))
        self.assertFalse(stale, "Aggregate references unknown focused runtime targets: " + ", ".join(stale))

    def test_makefile_shape_groups_do_not_duplicate_entries(self) -> None:
        duplicated_shapes = {}
        for group, shapes in self._makefile_shape_group_lists(self.make_text).items():
            duplicates = sorted({shape for shape in shapes if shapes.count(shape) > 1})
            if duplicates:
                duplicated_shapes[group] = duplicates

        self.assertFalse(
            duplicated_shapes,
            "Makefile shape groups contain duplicate entries: "
            + "; ".join(
                f"{group}: {', '.join(shapes)}"
                for group, shapes in sorted(duplicated_shapes.items())
            ),
        )

    def test_makefile_shape_group_parser_preserves_duplicate_entries(self) -> None:
        groups = self._makefile_shape_group_lists(
            "ACTION_ACTC_ALINK_INPUT_RUNTIME_SHAPES := \\\n"
            "\tactc_runtime_input_one \\\n"
            "\tactc_runtime_input_one \\\n"
            "\tactc_runtime_input_two\n"
        )

        self.assertEqual(
            groups["ACTION_ACTC_ALINK_INPUT_RUNTIME_SHAPES"],
            [
                "actc_runtime_input_one",
                "actc_runtime_input_one",
                "actc_runtime_input_two",
            ],
        )

    def test_all_alink_object_code_probe_shapes_are_listed_in_makefile_matrices(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        probe_shapes = {
            shape
            for shape, case in probe.DIRECT_PRG_CASES.items()
            if shape.startswith("object_code_")
            or (shape.startswith("legacy_") and case.get("expect_alink_failure"))
        }
        matrix_shapes = set().union(
            self._makefile_shape_group(
                self.make_text,
                "ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES",
            ),
            self._makefile_shape_group(
                self.make_text,
                "ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES",
            ),
            self._makefile_shape_group(
                self.make_text,
                "ACTION_ALINK_PRG_OBJECT_CODE_REJECTION_CASES",
            ),
        )

        missing = sorted(probe_shapes - matrix_shapes)
        stale = sorted(matrix_shapes - probe_shapes)

        self.assertFalse(missing, "ALINK object-code probe shapes missing from Makefile matrices: " + ", ".join(missing))
        self.assertFalse(stale, "Makefile object-code matrices reference missing probe cases: " + ", ".join(stale))

    def test_actc_object_emission_launch_matrix_covers_focused_source_shapes(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_shapes = {
            shape
            for shape, case in probe.DIRECT_PRG_CASES.items()
            if "source" in case
            and not shape.startswith("actc_runtime_")
            and not shape.startswith("object_code_")
        }
        matrix_shapes = self._makefile_shape_group(self.make_text, "ACTION_ACTC_ALINK_OBJECT_EMISSION_SHAPES")
        direct_cases = set(probe.DIRECT_PRG_CASES)

        stale = sorted(matrix_shapes - direct_cases)
        known_matrix_shapes = matrix_shapes & direct_cases
        missing = sorted(expected_shapes - matrix_shapes)
        non_source = sorted(shape for shape in known_matrix_shapes if "source" not in probe.DIRECT_PRG_CASES[shape])
        wrong_family = sorted(
            shape
            for shape in known_matrix_shapes
            if shape.startswith("actc_runtime_") or shape.startswith("object_code_")
        )

        self.assertTrue(matrix_shapes, "No ACTC object-emission launch matrix shapes found")
        self.assertFalse(stale, "ACTC object-emission matrix references missing probe cases: " + ", ".join(stale))
        self.assertFalse(missing, "ACTC object-emission matrix missing focused shapes: " + ", ".join(missing))
        self.assertFalse(non_source, "ACTC object-emission matrix contains non-source cases: " + ", ".join(non_source))
        self.assertFalse(wrong_family, "ACTC object-emission matrix contains runtime/object-code families: " + ", ".join(wrong_family))
        self.assertIn(
            "for shape in $(ACTION_ACTC_ALINK_OBJECT_EMISSION_SHAPES)",
            self.make_text,
            "ACTC object-emission matrix group is not used by a target",
        )
        target_body = self._makefile_target_body(
            self.make_text,
            "vice-action-actc-alink-launch-object-emission-matrix",
        )
        self.assertIn(
            "timeout $(ACTION_ACTC_ALINK_PROBE_TIMEOUT) $(PYTHON) "
            "tools/run_action_actc_alink_launch_probe_direct.py",
            target_body,
        )
        self.assertIn(
            "--shape \"$$shape\" --attempts $(ACTION_ACTC_ALINK_PROBE_ATTEMPTS) --attempt-delay 4.0",
            target_body,
        )
        self.assertNotIn("for attempt in 1 2 3", target_body)

    def test_absolute_routine_launch_case_is_direct_and_library_free(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["actc_absolute_routine_address_linked"]
        self.assertIn("PROC KERNALOUT=($FFD0+2)(BYTE VALUE)", case["source"])
        self.assertIn("A9 21 48 A9 00 48 68 68 20 D2 FF", case["expected_object_fragments"])
        self.assertTrue(case["expected_tail_from_compiled_object"])
        self.assertEqual(case["expected_alink_loads"], [])
        self.assertEqual(case["screen_fragments"], ["!"])

    def test_linked_routine_alias_launch_case_uses_named_obj_relocation(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["actc_linked_routine_address_linked"]
        self.assertIn("PROC WORKERALIAS=(1-1)+WORKER()", case["source"])
        self.assertIn("r 1 x worker\n", case["expected_object_fragments"])
        self.assertTrue(case["expected_tail_from_compiled_object"])
        self.assertEqual(case["expected_alink_loads"], [])
        self.assertEqual(case["screen_fragments"], ["!"])

    def test_documented_actc_object_emission_matrix_count_matches_probe_cases(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_count = len(
            {
                shape
                for shape, case in probe.DIRECT_PRG_CASES.items()
                if "source" in case
                and not shape.startswith("actc_runtime_")
                and not shape.startswith("object_code_")
            }
        )
        documented_counts = {
            "actionc64u/docs/action_matrix.md": r"\| ACTC object emission \| (\d+) source-backed direct-launch shapes \|",
            "actionc64u/docs/active_direction.md": (
                r"object-emission launch matrix; it currently enumerates (\d+)\s+"
                r"non-runtime, non-object-code source shapes"
            ),
            "udos/README.md": (
                r"now covers all\s+(\d+) source-backed non-runtime, non-object-code "
                r"ACTC object-emission launch"
            ),
            "udos/BUILDING.md": (
                r"currently enumerates all (\d+) non-runtime, non-object-code source-backed\s+"
                r"object-emission shapes"
            ),
            "udos/MILESTONE_HANDOFF.md": (
                r"non-runtime source-backed ACTC object-emission matrix at (\d+) shapes"
            ),
        }

        for relative_path, pattern in documented_counts.items():
            with self.subTest(path=relative_path):
                text = (self.workspace / relative_path).read_text()
                match = re.search(pattern, text)
                self.assertIsNotNone(match, f"Missing documented ACTC object-emission count in {relative_path}")
                self.assertEqual(
                    int(match.group(1)),
                    expected_count,
                    f"Documented ACTC object-emission count in {relative_path} is stale",
                )

    def test_shipped_link_selected_library_helpers_have_compiler_and_object_contract(self) -> None:
        action_root = self.workspace / "actionc64u"
        actc_text = (action_root / "src" / "tools_udos" / "actc" / "actc.asm").read_text(encoding="ascii")
        runtime_lowering_text = (
            action_root
            / "src"
            / "tools_udos"
            / "actc"
            / "actc_overlay_emit_native_runtime_sequence.inc"
        ).read_text(encoding="ascii")
        runtime_modules = {
            path.stem.lower()
            for path in (action_root / "src" / "runtime" / "udos_modules").glob("rt_*.obj")
        }
        actc_runtime_map = self._actc_builtin_runtime_map(actc_text)
        compiler_runtime_names = {
            name.lower()
            for name in re.findall(r'\.asciiz\s+"(rt_[^"]+)"', runtime_lowering_text)
        }

        generic_contracts = {
            "gfx1.act": {
                "VICBANK": "rt_gfx_vic_bank",
                "BGCOLOR": "rt_gfx_bgcolor",
                "BORDERCOLOR": "rt_gfx_bordercolor",
                "SCREENBASE": "rt_gfx_screen_base",
                "BITMAPBASE": "rt_gfx_bitmap_base",
                "SCREENCELL": "rt_gfx_screen_cell",
                "COLORCELL": "rt_gfx_color_cell",
                "SCREENCOPY": "rt_gfx_screen_copy",
                "COLORCOPY": "rt_gfx_color_copy",
                "BITMAPFILL": "rt_gfx_bitmap_fill",
                "BITMAPCOPY": "rt_gfx_bitmap_copy",
                "BITMAPON": "rt_gfx_bitmap_on",
                "BITMAPOFF": "rt_gfx_bitmap_off",
                "MBITMAPON": "rt_gfx_mbitmap_on",
                "MBITMAPOFF": "rt_gfx_mbitmap_off",
            },
            "input1.act": {
                "JOY": "rt_joy",
                "JOYSEEN": "rt_jp",
                "JOYBTN1": "rt_jb1",
                "JOYBTN2": "rt_jb2",
                "MOUSEPOLL": "rt_mp",
                "MOUSESEEN": "rt_mseen",
                "MOUSEX": "rt_mx",
                "MOUSEY": "rt_my",
                "MOUSEBTN": "rt_mb",
                "MOUSEBTN1": "rt_mb1",
                "MOUSEBTN2": "rt_mb2",
            },
            "dbf1.act": {
                "DBFCREATE": "rt_dbf_create",
                "DBFOPEN": "rt_dbf_open",
                "DBFCLOSE": "rt_dbf_close",
                "DBFGO": "rt_dbf_go",
                "DBFFIELDCOUNT": "rt_dbf_fieldcount",
                "DBFFIELDLEN": "rt_dbf_fieldlen",
                "DBFREADBYTE": "rt_dbf_readbyte",
                "DBFREADFIELDBYTE": "rt_dbf_readfieldbyte",
                "DBFWRITEFIELDBYTE": "rt_dbf_writefieldbyte",
                "DBFWRITEBYTE": "rt_dbf_writebyte",
                "DBFAPPEND": "rt_dbf_append",
                "DBFPACK": "rt_dbf_pack",
                "DBFSAVE": "rt_dbf_save",
                "DBFDELETE": "rt_dbf_delete",
                "DBFUNDELETE": "rt_dbf_undelete",
                "DBFDELETED": "rt_dbf_deleted",
                "DBFHEADERLEN": "rt_dbf_headerlen",
                "DBFRECORDLEN": "rt_dbf_recordlen",
                "DBFTOTALRECS": "rt_dbf_totalrecs",
                "DBFCURRRECNO": "rt_dbf_currrecno",
            },
            "sidspr1.act": {
                "SPRITEHIT": "rt_sprite_hit",
                "SPRITEHITBG": "rt_sprite_hit_bg",
                "SIDOSC3": "rt_sid_osc3",
                "SIDENV3": "rt_sid_env3",
                "SPRITEON": "rt_sprite_on",
                "SPRITEOFF": "rt_sprite_off",
                "SPRITEPOS": "rt_sprite_pos",
                "SPRITEPTR": "rt_sprite_ptr",
                "SPRITEDATA": "rt_sprite_data",
                "SPRITECOLOR": "rt_sprite_color",
                "SPRITEMC": "rt_sprite_mc",
                "SPRITEXEXP": "rt_sprite_xexp",
                "SPRITEYEXP": "rt_sprite_yexp",
                "SPRITEPRIO": "rt_sprite_prio",
                "SETSPRITEMC": "rt_sprite_set_mc",
                "SIDFREQ": "rt_sid_freq",
                "SIDPULSE": "rt_sid_pulse",
                "SIDWAVE": "rt_sid_wave",
                "SIDAD": "rt_sid_ad",
                "SIDSR": "rt_sid_sr",
                "SIDON": "rt_sid_on",
                "SIDOFF": "rt_sid_off",
                "SIDVOL": "rt_sid_vol",
                "SIDCUTOFF": "rt_sid_cutoff",
                "SIDRES": "rt_sid_res",
                "SIDMODE": "rt_sid_mode",
                "SIDROUTE": "rt_sid_route",
                "SIDRST": "rt_sid_rst",
            },
        }

        for lib_name, helper_map in generic_contracts.items():
            with self.subTest(lib=lib_name):
                declared_helpers = self._library_call_names(action_root / "lib" / lib_name)
                self.assertEqual(declared_helpers, set(helper_map))
                for helper_name, runtime_name in helper_map.items():
                    self.assertEqual(actc_runtime_map.get(helper_name), runtime_name)
                    self.assertIn(runtime_name, runtime_modules)
                    self.assertIn(runtime_name, compiler_runtime_names)
                    module_text = (
                        action_root / "src" / "runtime" / "udos_modules" / f"{runtime_name}.obj"
                    ).read_text(encoding="ascii")
                    self.assertTrue(module_text.startswith("OBJ1\n"))
                    self.assertRegex(module_text, rf"(?m)^x {re.escape(runtime_name)} \d+ \d+$")
                    self.assertRegex(module_text, r"(?m)^b (?:u[0-9A-Za-z])*M$")
                    self.assertRegex(module_text, r"(?m)^m [0-9A-F]{2}(?: [0-9A-F]{2})*$")

        self.assertEqual(
            self._library_call_names(action_root / "lib" / "math1.act"),
            {
                "PRINTR",
                "PRINTRE",
                "FABS",
                "FSQRT",
                "FSIGN",
                "FTRUNC",
                "FFLOOR",
                "FCEIL",
                "FROUND",
                "FFRAC",
                "FMOD",
                "FHYPOT",
                "FPOW",
                "FSIN",
                "FCOS",
                "FTAN",
                "FATAN",
                "FATAN2",
                "FEXP",
                "FLN",
                "FLOG2",
                "FLOG10",
                "FMIN",
                "FMAX",
                "FCLAMP",
                "DEGTORAD",
                "RADTODEG",
            },
        )
        math_shapes = self._makefile_runtime_matrix_shape_groups(self.make_text).get(
            "ACTION_ACTC_ALINK_MATH_RUNTIME_SHAPES",
            set(),
        )
        for shape in {
            "actc_runtime_math1_printre_split_linked",
            "actc_runtime_math1_printr_split_linked",
            "actc_runtime_math1_fabs_split_linked",
            "actc_runtime_math1_fsqrt_split_linked",
            "actc_runtime_math1_fsign_split_linked",
            "actc_runtime_math1_ftrunc_split_linked",
            "actc_runtime_math1_ffloor_split_linked",
            "actc_runtime_math1_fceil_split_linked",
            "actc_runtime_math1_fround_split_linked",
            "actc_runtime_math1_ffrac_split_linked",
            "actc_runtime_math1_fmod_split_linked",
            "actc_runtime_math1_fhypot_split_linked",
            "actc_runtime_math1_fpow_split_linked",
            "actc_runtime_math1_fsin_split_linked",
            "actc_runtime_math1_fcos_split_linked",
            "actc_runtime_math1_ftan_split_linked",
            "actc_runtime_math1_fatan_split_linked",
            "actc_runtime_math1_fatan2_split_linked",
            "actc_runtime_math1_fexp_split_linked",
            "actc_runtime_math1_fln_split_linked",
            "actc_runtime_math1_flog2_split_linked",
            "actc_runtime_math1_flog10_split_linked",
            "actc_runtime_math1_deg_to_rad_split_linked",
            "actc_runtime_math1_rad_to_deg_split_linked",
            "actc_runtime_math1_fmin_split_linked",
            "actc_runtime_math1_fmax_split_linked",
            "actc_runtime_math1_fclamp_split_linked",
            "actc_runtime_math1_fclamp_permuted_split_linked",
        }:
            self.assertIn(shape, math_shapes)

        compiler_runtime_modules = {
            "rt_f_abs",
            "rt_f_add",
            "rt_f_cmp",
            "rt_f_div",
            "rt_f_mul",
            "rt_f_sign",
            "rt_f_trunc",
            "rt_f_floor",
            "rt_f_ceil",
            "rt_f_round",
            "rt_f_frac",
            "rt_f_mod",
            "rt_f_hypot",
            "rt_f_pow",
            "rt_f_sin",
            "rt_f_cos",
            "rt_f_tan",
            "rt_f_atan",
            "rt_f_atan2",
            "rt_f_exp",
            "rt_f_ln",
            "rt_f_log2",
            "rt_f_log10",
            "rt_f_deg_to_rad",
            "rt_f_rad_to_deg",
            "rt_f_min",
            "rt_f_max",
            "rt_f_clamp",
            "rt_f_sqrt",
            "rt_f_sub",
            "rt_f_to_i",
            "rt_i_div",
            "rt_i_mul",
            "rt_i_to_f",
            "rt_print_i",
            "rt_print_f",
            "rt_s_to_f",
        }
        dependency_only_runtime_modules = {
            "rt_dbf_pack_copy",
            "rt_dbf_pack_read",
            "rt_dbf_pack_step",
            "rt_dbf_pack_write",
            "rt_dbf_state",
            "rt_f_addsub_core",
            "rt_f_special",
            "rt_f_wrap_pi",
            "rt_js",
            "rt_ms",
            "rt_sid_filter_state",
            "rt_sid_state",
            "rt_sid_volume_state",
        }
        action_facing_runtime_modules = {
            runtime_name
            for helper_map in generic_contracts.values()
            for runtime_name in helper_map.values()
        } | compiler_runtime_modules

        unexpected_runtime_modules = sorted(
            runtime_modules - action_facing_runtime_modules - dependency_only_runtime_modules
        )
        missing_runtime_modules = sorted(action_facing_runtime_modules - runtime_modules)
        missing_dependency_modules = sorted(dependency_only_runtime_modules - runtime_modules)

        self.assertFalse(
            unexpected_runtime_modules,
            "Runtime OBJ modules must be Action-facing/compiler helpers or "
            "explicit dependency-only support: "
            + ", ".join(unexpected_runtime_modules),
        )
        self.assertFalse(
            missing_runtime_modules,
            "Action-facing/compiler runtime helpers missing OBJ modules: "
            + ", ".join(missing_runtime_modules),
        )
        self.assertFalse(
            missing_dependency_modules,
            "Dependency-only runtime support modules missing OBJ modules: "
            + ", ".join(missing_dependency_modules),
        )

    def test_input_runtime_matrix_covers_joystick_mouse_and_mixed_launches(self) -> None:
        matrix_groups = self._makefile_runtime_matrix_shape_groups(self.make_text)
        input_shapes = matrix_groups.get("ACTION_ACTC_ALINK_INPUT_RUNTIME_SHAPES", set())
        expected_shapes = {
            "actc_runtime_input_joystick_helpers_linked",
            "actc_runtime_input_joystick_condition_gfx_helper_linked",
            "actc_runtime_input_joystick_not_equal_condition_gfx_helper_linked",
            "actc_runtime_input_joystick_state_store_linked",
            "actc_runtime_input_joystick_two_button_mask_linked",
            "actc_runtime_input_joystick_button_state_helpers_linked",
            "actc_runtime_input_mouse_helpers_linked",
            "actc_runtime_input_mouse_state_store_linked",
            "actc_runtime_input_mouse_two_button_mask_linked",
            "actc_runtime_input_mouse_button_state_helpers_linked",
            "actc_runtime_input_mouse_button_condition_gfx_helper_linked",
            "actc_runtime_input_mouse_button_not_equal_condition_gfx_helper_linked",
            "actc_runtime_input_joystick_button_condition_gfx_helper_linked",
            "actc_runtime_input_joystick_button2_condition_gfx_helper_linked",
            "actc_runtime_input_mouse_button2_condition_gfx_helper_linked",
            "actc_runtime_input_variable_port_store_linked",
            "actc_runtime_input_dual_port_presence_store_linked",
            "actc_runtime_input_joystick_seen_result_gfx_arg_linked",
            "actc_runtime_input_mouse_seen_result_gfx_arg_linked",
            "actc_runtime_input_joystick_seen_result_sprite_second_arg_linked",
            "actc_runtime_input_mouse_seen_result_sprite_second_arg_linked",
            "actc_runtime_input_joystick_seen_nested_gfx_arg_linked",
            "actc_runtime_input_mouse_seen_nested_gfx_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sprite_second_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sprite_second_arg_linked",
            "actc_runtime_input_joystick_seen_result_sprite_first_arg_linked",
            "actc_runtime_input_mouse_seen_result_sprite_first_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sprite_first_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sprite_first_arg_linked",
            "actc_runtime_input_joystick_seen_result_sprite_data_first_arg_linked",
            "actc_runtime_input_mouse_seen_result_sprite_data_first_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sprite_data_first_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sprite_data_first_arg_linked",
            "actc_runtime_input_joystick_seen_result_sprite_ptr_first_arg_linked",
            "actc_runtime_input_mouse_seen_result_sprite_ptr_first_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sprite_ptr_first_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sprite_ptr_first_arg_linked",
            "actc_runtime_input_joystick_seen_result_sprite_pos_first_arg_linked",
            "actc_runtime_input_mouse_seen_result_sprite_pos_first_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sprite_pos_first_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sprite_pos_first_arg_linked",
            "actc_runtime_input_joystick_seen_result_sprite_set_mc_first_arg_linked",
            "actc_runtime_input_mouse_seen_result_sprite_set_mc_first_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sprite_set_mc_first_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sprite_set_mc_first_arg_linked",
            "actc_runtime_input_joystick_seen_result_sprite_mc_first_arg_linked",
            "actc_runtime_input_mouse_seen_result_sprite_mc_first_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sprite_mc_first_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sprite_mc_first_arg_linked",
            "actc_runtime_input_joystick_seen_result_sprite_xexp_first_arg_linked",
            "actc_runtime_input_mouse_seen_result_sprite_xexp_first_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sprite_xexp_first_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sprite_xexp_first_arg_linked",
            "actc_runtime_input_joystick_seen_result_sprite_yexp_first_arg_linked",
            "actc_runtime_input_mouse_seen_result_sprite_yexp_first_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sprite_yexp_first_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sprite_yexp_first_arg_linked",
            "actc_runtime_input_joystick_seen_result_sprite_prio_first_arg_linked",
            "actc_runtime_input_mouse_seen_result_sprite_prio_first_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sprite_prio_first_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sprite_prio_first_arg_linked",
            "actc_runtime_input_joystick_seen_result_sid_arg_linked",
            "actc_runtime_input_mouse_seen_result_sid_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sid_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sid_arg_linked",
            "actc_runtime_input_joystick_seen_result_sid_freq_second_arg_linked",
            "actc_runtime_input_mouse_seen_result_sid_freq_second_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sid_freq_second_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sid_freq_second_arg_linked",
            "actc_runtime_input_joystick_seen_result_sid_pulse_second_arg_linked",
            "actc_runtime_input_mouse_seen_result_sid_pulse_second_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sid_pulse_second_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sid_pulse_second_arg_linked",
            "actc_runtime_input_joystick_seen_result_sid_cutoff_arg_linked",
            "actc_runtime_input_mouse_seen_result_sid_cutoff_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sid_cutoff_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sid_cutoff_arg_linked",
            "actc_runtime_input_joystick_seen_result_sid_wave_first_arg_linked",
            "actc_runtime_input_mouse_seen_result_sid_wave_first_arg_linked",
            "actc_runtime_input_joystick_seen_result_sid_wave_second_arg_linked",
            "actc_runtime_input_mouse_seen_result_sid_wave_second_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sid_wave_first_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sid_wave_first_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sid_wave_second_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sid_wave_second_arg_linked",
            "actc_runtime_input_joystick_seen_result_sid_ad_first_arg_linked",
            "actc_runtime_input_mouse_seen_result_sid_ad_first_arg_linked",
            "actc_runtime_input_joystick_seen_result_sid_ad_second_arg_linked",
            "actc_runtime_input_mouse_seen_result_sid_ad_second_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sid_ad_first_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sid_ad_first_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sid_ad_second_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sid_ad_second_arg_linked",
            "actc_runtime_input_joystick_seen_result_sid_sr_first_arg_linked",
            "actc_runtime_input_mouse_seen_result_sid_sr_first_arg_linked",
            "actc_runtime_input_joystick_seen_result_sid_sr_second_arg_linked",
            "actc_runtime_input_mouse_seen_result_sid_sr_second_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sid_sr_first_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sid_sr_first_arg_linked",
            "actc_runtime_input_joystick_seen_nested_sid_sr_second_arg_linked",
            "actc_runtime_input_mouse_seen_nested_sid_sr_second_arg_linked",
            "actc_runtime_input_gfx_mixed_helpers_linked",
            "actc_runtime_input_mouse_result_gfx_arg_linked",
            "actc_runtime_input_mouse_result_sid_arg_linked",
            "actc_runtime_input_mouse_result_sprite_second_arg_linked",
            "actc_runtime_input_mouse_x_nested_sprite_first_arg_linked",
            "actc_runtime_input_mouse_x_result_sprite_pos_second_arg_linked",
            "actc_runtime_input_mouse_y_result_sprite_pos_third_arg_linked",
            "actc_runtime_input_mouse_xy_nested_sprite_pos_linked",
            "actc_runtime_input_mouse_button1_result_gfx_arg_linked",
            "actc_runtime_input_mouse_button2_result_gfx_arg_linked",
            "actc_runtime_input_mouse_button1_result_sprite_second_arg_linked",
            "actc_runtime_input_mouse_button2_result_sprite_second_arg_linked",
            "actc_runtime_input_mouse_button1_nested_gfx_arg_linked",
            "actc_runtime_input_mouse_button2_nested_gfx_arg_linked",
            "actc_runtime_input_mouse_button1_nested_sprite_second_arg_linked",
            "actc_runtime_input_mouse_button2_nested_sprite_second_arg_linked",
            "actc_runtime_input_joystick_button1_result_gfx_arg_linked",
            "actc_runtime_input_joystick_button2_result_gfx_arg_linked",
            "actc_runtime_input_joystick_button1_result_sprite_second_arg_linked",
            "actc_runtime_input_joystick_button2_result_sprite_second_arg_linked",
            "actc_runtime_input_joystick_button1_nested_gfx_arg_linked",
            "actc_runtime_input_joystick_button2_nested_gfx_arg_linked",
            "actc_runtime_input_joystick_button1_nested_sprite_second_arg_linked",
            "actc_runtime_input_joystick_button2_nested_sprite_second_arg_linked",
            "actc_runtime_input_mouse_button_result_sid_arg_linked",
            "actc_runtime_input_mouse_button_nested_sid_arg_linked",
            "actc_runtime_input_mouse_button1_result_sid_freq_second_arg_linked",
            "actc_runtime_input_mouse_button2_result_sid_freq_second_arg_linked",
            "actc_runtime_input_mouse_button1_nested_sid_freq_second_arg_linked",
            "actc_runtime_input_mouse_button2_nested_sid_freq_second_arg_linked",
            "actc_runtime_input_mouse_button1_result_sid_pulse_second_arg_linked",
            "actc_runtime_input_mouse_button2_result_sid_pulse_second_arg_linked",
            "actc_runtime_input_mouse_button1_nested_sid_pulse_second_arg_linked",
            "actc_runtime_input_mouse_button2_nested_sid_pulse_second_arg_linked",
            "actc_runtime_input_mouse_button1_result_sid_cutoff_arg_linked",
            "actc_runtime_input_mouse_button2_result_sid_cutoff_arg_linked",
            "actc_runtime_input_mouse_button1_nested_sid_cutoff_arg_linked",
            "actc_runtime_input_mouse_button2_nested_sid_cutoff_arg_linked",
            "actc_runtime_input_mouse_button1_result_sid_wave_first_arg_linked",
            "actc_runtime_input_mouse_button2_result_sid_wave_first_arg_linked",
            "actc_runtime_input_mouse_button1_result_sid_wave_second_arg_linked",
            "actc_runtime_input_mouse_button2_result_sid_wave_second_arg_linked",
            "actc_runtime_input_mouse_button1_result_sid_ad_first_arg_linked",
            "actc_runtime_input_mouse_button2_result_sid_ad_first_arg_linked",
            "actc_runtime_input_mouse_button1_result_sid_ad_second_arg_linked",
            "actc_runtime_input_mouse_button2_result_sid_ad_second_arg_linked",
            "actc_runtime_input_mouse_button1_result_sid_sr_first_arg_linked",
            "actc_runtime_input_mouse_button2_result_sid_sr_first_arg_linked",
            "actc_runtime_input_mouse_button1_result_sid_sr_second_arg_linked",
            "actc_runtime_input_mouse_button2_result_sid_sr_second_arg_linked",
            "actc_runtime_input_mouse_button1_nested_sid_wave_first_arg_linked",
            "actc_runtime_input_mouse_button2_nested_sid_wave_first_arg_linked",
            "actc_runtime_input_mouse_button1_nested_sid_wave_second_arg_linked",
            "actc_runtime_input_mouse_button2_nested_sid_wave_second_arg_linked",
            "actc_runtime_input_mouse_button1_nested_sid_ad_first_arg_linked",
            "actc_runtime_input_mouse_button2_nested_sid_ad_first_arg_linked",
            "actc_runtime_input_mouse_button1_nested_sid_ad_second_arg_linked",
            "actc_runtime_input_mouse_button2_nested_sid_ad_second_arg_linked",
            "actc_runtime_input_mouse_button1_nested_sid_sr_first_arg_linked",
            "actc_runtime_input_mouse_button2_nested_sid_sr_first_arg_linked",
            "actc_runtime_input_mouse_button1_nested_sid_sr_second_arg_linked",
            "actc_runtime_input_mouse_button2_nested_sid_sr_second_arg_linked",
            "actc_runtime_input_joystick_result_sid_arg_linked",
            "actc_runtime_input_joystick_button1_result_sid_arg_linked",
            "actc_runtime_input_joystick_button2_result_sid_arg_linked",
            "actc_runtime_input_joystick_nested_sid_arg_linked",
            "actc_runtime_input_joystick_result_sid_word_arg_linked",
            "actc_runtime_input_joystick_nested_sid_word_arg_linked",
            "actc_runtime_input_joystick_result_sid_first_arg_linked",
            "actc_runtime_input_joystick_result_sid_freq_second_arg_linked",
            "actc_runtime_input_joystick_button1_result_sid_freq_second_arg_linked",
            "actc_runtime_input_joystick_button2_result_sid_freq_second_arg_linked",
            "actc_runtime_input_joystick_nested_sid_freq_second_arg_linked",
            "actc_runtime_input_joystick_button1_nested_sid_freq_second_arg_linked",
            "actc_runtime_input_joystick_button2_nested_sid_freq_second_arg_linked",
            "actc_runtime_input_joystick_result_sid_pulse_second_arg_linked",
            "actc_runtime_input_joystick_button1_result_sid_pulse_second_arg_linked",
            "actc_runtime_input_joystick_button2_result_sid_pulse_second_arg_linked",
            "actc_runtime_input_joystick_nested_sid_pulse_second_arg_linked",
            "actc_runtime_input_joystick_button1_nested_sid_pulse_second_arg_linked",
            "actc_runtime_input_joystick_button2_nested_sid_pulse_second_arg_linked",
            "actc_runtime_input_joystick_button1_result_sid_cutoff_arg_linked",
            "actc_runtime_input_joystick_button2_result_sid_cutoff_arg_linked",
            "actc_runtime_input_joystick_button1_nested_sid_cutoff_arg_linked",
            "actc_runtime_input_joystick_button2_nested_sid_cutoff_arg_linked",
            "actc_runtime_input_joystick_result_sprite_second_arg_linked",
            "actc_runtime_input_joystick_nested_sprite_second_arg_linked",
            "actc_runtime_input_joystick_nested_sprite_first_arg_linked",
            "actc_runtime_input_joystick_result_sprite_first_arg_linked",
            "actc_runtime_input_joystick_result_sprite_data_first_arg_linked",
            "actc_runtime_input_joystick_result_sprite_data_second_arg_linked",
            "actc_runtime_input_joystick_result_sprite_ptr_first_arg_linked",
            "actc_runtime_input_joystick_result_sprite_ptr_second_arg_linked",
            "actc_runtime_input_joystick_result_sprite_mc_first_arg_linked",
            "actc_runtime_input_joystick_result_sprite_mc_second_arg_linked",
            "actc_runtime_input_joystick_result_sprite_xexp_first_arg_linked",
            "actc_runtime_input_joystick_result_sprite_xexp_second_arg_linked",
            "actc_runtime_input_joystick_result_sprite_yexp_first_arg_linked",
            "actc_runtime_input_joystick_result_sprite_yexp_second_arg_linked",
            "actc_runtime_input_joystick_result_sprite_prio_first_arg_linked",
            "actc_runtime_input_joystick_result_sprite_prio_second_arg_linked",
            "actc_runtime_input_joystick_result_sprite_set_mc_first_arg_linked",
            "actc_runtime_input_joystick_result_sprite_set_mc_second_arg_linked",
            "actc_runtime_input_joystick_result_sprite_pos_first_arg_linked",
            "actc_runtime_input_joystick_result_sprite_pos_second_arg_linked",
            "actc_runtime_input_joystick_result_sprite_pos_third_arg_linked",
            "actc_runtime_input_joystick_result_sid_second_arg_linked",
            "actc_runtime_input_joystick_result_sid_wave_first_arg_linked",
            "actc_runtime_input_joystick_button1_result_sid_wave_first_arg_linked",
            "actc_runtime_input_joystick_button2_result_sid_wave_first_arg_linked",
            "actc_runtime_input_joystick_button1_result_sid_wave_second_arg_linked",
            "actc_runtime_input_joystick_button2_result_sid_wave_second_arg_linked",
            "actc_runtime_input_joystick_nested_sid_wave_first_arg_linked",
            "actc_runtime_input_joystick_nested_sid_wave_second_arg_linked",
            "actc_runtime_input_joystick_button1_nested_sid_wave_first_arg_linked",
            "actc_runtime_input_joystick_button2_nested_sid_wave_first_arg_linked",
            "actc_runtime_input_joystick_button1_nested_sid_wave_second_arg_linked",
            "actc_runtime_input_joystick_button2_nested_sid_wave_second_arg_linked",
            "actc_runtime_input_joystick_result_sid_ad_first_arg_linked",
            "actc_runtime_input_joystick_result_sid_ad_second_arg_linked",
            "actc_runtime_input_joystick_button1_result_sid_ad_first_arg_linked",
            "actc_runtime_input_joystick_button2_result_sid_ad_first_arg_linked",
            "actc_runtime_input_joystick_button1_result_sid_ad_second_arg_linked",
            "actc_runtime_input_joystick_button2_result_sid_ad_second_arg_linked",
            "actc_runtime_input_joystick_nested_sid_ad_first_arg_linked",
            "actc_runtime_input_joystick_nested_sid_ad_second_arg_linked",
            "actc_runtime_input_joystick_button1_nested_sid_ad_first_arg_linked",
            "actc_runtime_input_joystick_button2_nested_sid_ad_first_arg_linked",
            "actc_runtime_input_joystick_button1_nested_sid_ad_second_arg_linked",
            "actc_runtime_input_joystick_button2_nested_sid_ad_second_arg_linked",
            "actc_runtime_input_joystick_result_sid_sr_first_arg_linked",
            "actc_runtime_input_joystick_result_sid_sr_second_arg_linked",
            "actc_runtime_input_joystick_button1_result_sid_sr_first_arg_linked",
            "actc_runtime_input_joystick_button2_result_sid_sr_first_arg_linked",
            "actc_runtime_input_joystick_button1_result_sid_sr_second_arg_linked",
            "actc_runtime_input_joystick_button2_result_sid_sr_second_arg_linked",
            "actc_runtime_input_joystick_nested_sid_sr_first_arg_linked",
            "actc_runtime_input_joystick_nested_sid_sr_second_arg_linked",
            "actc_runtime_input_joystick_button1_nested_sid_sr_first_arg_linked",
            "actc_runtime_input_joystick_button2_nested_sid_sr_first_arg_linked",
            "actc_runtime_input_joystick_button1_nested_sid_sr_second_arg_linked",
            "actc_runtime_input_joystick_button2_nested_sid_sr_second_arg_linked",
            "actc_runtime_input_joystick_result_gfx_first_arg_linked",
            "actc_runtime_input_joystick_result_gfx_second_arg_linked",
            "actc_runtime_input_joystick_result_gfx_third_arg_linked",
            "actc_runtime_input_sid_mixed_helpers_linked",
            "actc_runtime_input_sprite_mixed_helpers_linked",
            "actc_runtime_input_math_mixed_helpers_linked",
            "actc_runtime_input_mouse_math_mixed_helpers_linked",
            "actc_runtime_input_joystick_math_store_helpers_linked",
            "actc_runtime_input_mouse_math_store_helpers_linked",
            "actc_runtime_input1_export_sample_linked",
            "actc_runtime_input1_joy_split_linked",
            "actc_runtime_input1_joy_seen_split_linked",
            "actc_runtime_input1_joy_button_split_linked",
            "actc_runtime_input1_mouse_poll_split_linked",
            "actc_runtime_input1_mouse_seen_split_linked",
            "actc_runtime_input1_mouse_x_split_linked",
            "actc_runtime_input1_mouse_y_split_linked",
            "actc_runtime_input1_mouse_button_split_linked",
            "actc_runtime_input1_mouse_button_state_split_linked",
        }
        aggregate_targets = self._makefile_target_submakes(
            self.make_text,
            "vice-action-actc-alink-launch-runtime-matrices",
        )

        self.assertEqual(input_shapes, expected_shapes)
        self.assertIn("vice-action-actc-alink-launch-input-runtime-matrix", aggregate_targets)
        self.assertIn(
            "for shape in $(ACTION_ACTC_ALINK_INPUT_RUNTIME_SHAPES)",
            self.make_text,
            "INPUT runtime matrix must launch every declared input shape",
        )

    def test_direct_prg_matrix_covers_seeded_nested_input_sprite_pos_shapes(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_cases = {
            "input_mouse_y_nested_sprite_pos_third_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_POS.OBJ",
                    "LIB/RT_MY.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_xy_nested_sprite_pos_direct_linked": {
                "body": "b p0u1u2u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_POS.OBJ",
                    "LIB/RT_MX.OBJ",
                    "LIB/RT_MY.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_joystick_nested_sprite_pos_first_arg_direct_linked": {
                "body": "b p0u1p1p2u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_POS.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_pos_second_arg_direct_linked": {
                "body": "b p0p1u1p2u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_POS.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_pos_third_arg_direct_linked": {
                "body": "b p0p1p2u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_POS.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
        }
        target_body = self._makefile_target_body(self.make_text, "vice-action-alink-prg-matrix")

        for shape, expected in expected_cases.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertNotIn("source", case)
                self._assert_native_runtime_seed(case, expected["body"])
                self.assertEqual(case["expected_alink_loads"], expected["loads"])
        self.assertIn("[print(name) for name in p.DIRECT_PRG_CASES]", target_body)
        self.assertIn('--shape "$$shape" --skip-launch --attempts 1', target_body)

    def test_direct_prg_matrix_covers_seeded_nested_input_sprite_table_shapes(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_cases = {
            "input_mouse_x_nested_sprite_data_first_arg_direct_linked": {
                "body": "b u1p0u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_DATA.OBJ",
                    "LIB/RT_MX.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_x_nested_sprite_ptr_first_arg_direct_linked": {
                "body": "b u1p0u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_PTR.OBJ",
                    "LIB/RT_MX.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_x_nested_sprite_data_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_DATA.OBJ",
                    "LIB/RT_MX.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_x_nested_sprite_ptr_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_PTR.OBJ",
                    "LIB/RT_MX.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_joystick_nested_sprite_data_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_DATA.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_ptr_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_PTR.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_data_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_DATA.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_ptr_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_PTR.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
        }
        target_body = self._makefile_target_body(self.make_text, "vice-action-alink-prg-matrix")

        for shape, expected in expected_cases.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertNotIn("source", case)
                self._assert_native_runtime_seed(case, expected["body"])
                self.assertEqual(case["expected_alink_loads"], expected["loads"])
        self.assertIn("[print(name) for name in p.DIRECT_PRG_CASES]", target_body)
        self.assertIn('--shape "$$shape" --skip-launch --attempts 1', target_body)

    def test_direct_prg_matrix_covers_seeded_nested_input_side_effect_shapes(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_cases = {
            "input_mouse_x_nested_gfx_arg_direct_linked": {
                "body": "b u1u0r\n",
                "loads": [
                    "LIB/RT_GFX_BGCOLOR.OBJ",
                    "LIB/RT_MX.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_y_nested_gfx_border_arg_direct_linked": {
                "body": "b u1u0r\n",
                "loads": [
                    "LIB/RT_GFX_BORDERCOLOR.OBJ",
                    "LIB/RT_MY.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button1_nested_gfx_arg_direct_linked": {
                "body": "b u1u0r\n",
                "loads": [
                    "LIB/RT_GFX_BGCOLOR.OBJ",
                    "LIB/RT_MB1.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button2_nested_gfx_arg_direct_linked": {
                "body": "b u1u0r\n",
                "loads": [
                    "LIB/RT_GFX_BGCOLOR.OBJ",
                    "LIB/RT_MB2.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_joystick_button1_nested_gfx_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_GFX_BGCOLOR.OBJ",
                    "LIB/RT_JB1.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button2_nested_gfx_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_GFX_BGCOLOR.OBJ",
                    "LIB/RT_JB2.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_gfx_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_GFX_BGCOLOR.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_gfx_color_cell_first_arg_direct_linked": {
                "body": "b p0u1p1p2u0r\n",
                "loads": [
                    "LIB/RT_GFX_COLOR_CELL.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_gfx_color_cell_second_arg_direct_linked": {
                "body": "b p0p1u1p2u0r\n",
                "loads": [
                    "LIB/RT_GFX_COLOR_CELL.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_gfx_color_cell_third_arg_direct_linked": {
                "body": "b p0p1p2u1u0r\n",
                "loads": [
                    "LIB/RT_GFX_COLOR_CELL.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_gfx_screen_cell_first_arg_direct_linked": {
                "body": "b p0u1p1p2u0r\n",
                "loads": [
                    "LIB/RT_GFX_SCREEN_CELL.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_gfx_screen_cell_second_arg_direct_linked": {
                "body": "b p0p1u1p2u0r\n",
                "loads": [
                    "LIB/RT_GFX_SCREEN_CELL.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_gfx_screen_cell_third_arg_direct_linked": {
                "body": "b p0p1p2u1u0r\n",
                "loads": [
                    "LIB/RT_GFX_SCREEN_CELL.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_mouse_x_nested_sid_arg_direct_linked": {
                "body": "b u1u0r\n",
                "loads": [
                    "LIB/RT_SID_VOL.OBJ",
                    "LIB/RT_SID_VOLUME_STATE.OBJ",
                    "LIB/RT_MX.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button_nested_sid_arg_direct_linked": {
                "body": "b u1u0r\n",
                "loads": [
                    "LIB/RT_SID_VOL.OBJ",
                    "LIB/RT_SID_VOLUME_STATE.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button1_nested_sid_arg_direct_linked": {
                "body": "b u1u0r\n",
                "loads": [
                    "LIB/RT_SID_VOL.OBJ",
                    "LIB/RT_SID_VOLUME_STATE.OBJ",
                    "LIB/RT_MB1.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button2_nested_sid_arg_direct_linked": {
                "body": "b u1u0r\n",
                "loads": [
                    "LIB/RT_SID_VOL.OBJ",
                    "LIB/RT_SID_VOLUME_STATE.OBJ",
                    "LIB/RT_MB2.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_joystick_button1_nested_sid_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_VOL.OBJ",
                    "LIB/RT_SID_VOLUME_STATE.OBJ",
                    "LIB/RT_JB1.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button2_nested_sid_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_VOL.OBJ",
                    "LIB/RT_SID_VOLUME_STATE.OBJ",
                    "LIB/RT_JB2.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sid_wave_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SID_WAVE.OBJ",
                    "LIB/RT_SID_STATE.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sid_wave_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SID_WAVE.OBJ",
                    "LIB/RT_SID_STATE.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button1_nested_sid_wave_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SID_WAVE.OBJ",
                    "LIB/RT_SID_STATE.OBJ",
                    "LIB/RT_JB1.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button2_nested_sid_wave_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SID_WAVE.OBJ",
                    "LIB/RT_SID_STATE.OBJ",
                    "LIB/RT_JB2.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button1_nested_sid_wave_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SID_WAVE.OBJ",
                    "LIB/RT_SID_STATE.OBJ",
                    "LIB/RT_JB1.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button2_nested_sid_wave_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SID_WAVE.OBJ",
                    "LIB/RT_SID_STATE.OBJ",
                    "LIB/RT_JB2.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sid_ad_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SID_AD.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sid_ad_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SID_AD.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button1_nested_sid_ad_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SID_AD.OBJ",
                    "LIB/RT_JB1.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button2_nested_sid_ad_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SID_AD.OBJ",
                    "LIB/RT_JB2.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button1_nested_sid_ad_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SID_AD.OBJ",
                    "LIB/RT_JB1.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button2_nested_sid_ad_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SID_AD.OBJ",
                    "LIB/RT_JB2.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sid_sr_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SID_SR.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sid_sr_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SID_SR.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button1_nested_sid_sr_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SID_SR.OBJ",
                    "LIB/RT_JB1.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button2_nested_sid_sr_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SID_SR.OBJ",
                    "LIB/RT_JB2.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button1_nested_sid_sr_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SID_SR.OBJ",
                    "LIB/RT_JB1.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button2_nested_sid_sr_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SID_SR.OBJ",
                    "LIB/RT_JB2.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_mouse_button1_nested_sid_wave_first_arg_direct_linked": {
                "body": "b u1p0u0r\n",
                "loads": [
                    "LIB/RT_SID_WAVE.OBJ",
                    "LIB/RT_SID_STATE.OBJ",
                    "LIB/RT_MB1.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button2_nested_sid_wave_first_arg_direct_linked": {
                "body": "b u1p0u0r\n",
                "loads": [
                    "LIB/RT_SID_WAVE.OBJ",
                    "LIB/RT_SID_STATE.OBJ",
                    "LIB/RT_MB2.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button1_nested_sid_wave_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_WAVE.OBJ",
                    "LIB/RT_SID_STATE.OBJ",
                    "LIB/RT_MB1.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button2_nested_sid_wave_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_WAVE.OBJ",
                    "LIB/RT_SID_STATE.OBJ",
                    "LIB/RT_MB2.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button1_nested_sid_ad_first_arg_direct_linked": {
                "body": "b u1p0u0r\n",
                "loads": [
                    "LIB/RT_SID_AD.OBJ",
                    "LIB/RT_MB1.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button2_nested_sid_ad_first_arg_direct_linked": {
                "body": "b u1p0u0r\n",
                "loads": [
                    "LIB/RT_SID_AD.OBJ",
                    "LIB/RT_MB2.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button1_nested_sid_ad_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_AD.OBJ",
                    "LIB/RT_MB1.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button2_nested_sid_ad_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_AD.OBJ",
                    "LIB/RT_MB2.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button1_nested_sid_sr_first_arg_direct_linked": {
                "body": "b u1p0u0r\n",
                "loads": [
                    "LIB/RT_SID_SR.OBJ",
                    "LIB/RT_MB1.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button2_nested_sid_sr_first_arg_direct_linked": {
                "body": "b u1p0u0r\n",
                "loads": [
                    "LIB/RT_SID_SR.OBJ",
                    "LIB/RT_MB2.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button1_nested_sid_sr_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_SR.OBJ",
                    "LIB/RT_MB1.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button2_nested_sid_sr_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_SR.OBJ",
                    "LIB/RT_MB2.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_y_nested_sprite_first_arg_direct_linked": {
                "body": "b u1p0u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_COLOR.OBJ",
                    "LIB/RT_MY.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button_nested_sprite_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_COLOR.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button1_nested_sprite_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_COLOR.OBJ",
                    "LIB/RT_MB1.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button2_nested_sprite_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_COLOR.OBJ",
                    "LIB/RT_MB2.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_joystick_button1_nested_sprite_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_COLOR.OBJ",
                    "LIB/RT_JB1.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button2_nested_sprite_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_COLOR.OBJ",
                    "LIB/RT_JB2.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_COLOR.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_COLOR.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_mc_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_MC.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_mc_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_MC.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_xexp_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_XEXP.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_xexp_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_XEXP.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_yexp_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_YEXP.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_yexp_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_YEXP.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_prio_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_PRIO.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_prio_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_PRIO.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_set_mc_first_arg_direct_linked": {
                "body": "b p0u1p1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_SET_MC.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sprite_set_mc_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SPRITE_SET_MC.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
        }
        target_body = self._makefile_target_body(self.make_text, "vice-action-alink-prg-matrix")

        for shape, expected in expected_cases.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertNotIn("source", case)
                self._assert_native_runtime_seed(case, expected["body"])
                self.assertEqual(case["expected_alink_loads"], expected["loads"])
        self.assertIn("[print(name) for name in p.DIRECT_PRG_CASES]", target_body)
        self.assertIn('--shape "$$shape" --skip-launch --attempts 1', target_body)

    def test_direct_prg_matrix_covers_seeded_nested_input_sid_word_shapes(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_cases = {
            "input_mouse_x_nested_sid_freq_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_FREQ.OBJ",
                    "LIB/RT_MX.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button1_nested_sid_freq_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_FREQ.OBJ",
                    "LIB/RT_MB1.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button2_nested_sid_freq_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_FREQ.OBJ",
                    "LIB/RT_MB2.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_x_nested_sid_pulse_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_PULSE.OBJ",
                    "LIB/RT_MX.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button1_nested_sid_pulse_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_PULSE.OBJ",
                    "LIB/RT_MB1.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button2_nested_sid_pulse_second_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_PULSE.OBJ",
                    "LIB/RT_MB2.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_joystick_nested_sid_freq_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SID_FREQ.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button1_nested_sid_freq_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SID_FREQ.OBJ",
                    "LIB/RT_JB1.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button2_nested_sid_freq_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SID_FREQ.OBJ",
                    "LIB/RT_JB2.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sid_pulse_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SID_PULSE.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button1_nested_sid_pulse_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SID_PULSE.OBJ",
                    "LIB/RT_JB1.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button2_nested_sid_pulse_second_arg_direct_linked": {
                "body": "b p0p1u1u0r\n",
                "loads": [
                    "LIB/RT_SID_PULSE.OBJ",
                    "LIB/RT_JB2.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_nested_sid_cutoff_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_CUTOFF.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_mouse_button1_nested_sid_cutoff_arg_direct_linked": {
                "body": "b u1u0r\n",
                "loads": [
                    "LIB/RT_SID_CUTOFF.OBJ",
                    "LIB/RT_MB1.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_mouse_button2_nested_sid_cutoff_arg_direct_linked": {
                "body": "b u1u0r\n",
                "loads": [
                    "LIB/RT_SID_CUTOFF.OBJ",
                    "LIB/RT_MB2.OBJ",
                    "LIB/RT_MB.OBJ",
                    "LIB/RT_MS.OBJ",
                ],
            },
            "input_joystick_button1_nested_sid_cutoff_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_CUTOFF.OBJ",
                    "LIB/RT_JB1.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
            "input_joystick_button2_nested_sid_cutoff_arg_direct_linked": {
                "body": "b p0u1u0r\n",
                "loads": [
                    "LIB/RT_SID_CUTOFF.OBJ",
                    "LIB/RT_JB2.OBJ",
                    "LIB/RT_JOY.OBJ",
                ],
            },
        }
        target_body = self._makefile_target_body(self.make_text, "vice-action-alink-prg-matrix")

        for shape, expected in expected_cases.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertNotIn("source", case)
                self._assert_native_runtime_seed(case, expected["body"])
                self.assertEqual(case["expected_alink_loads"], expected["loads"])
        self.assertIn("[print(name) for name in p.DIRECT_PRG_CASES]", target_body)
        self.assertIn('--shape "$$shape" --skip-launch --attempts 1', target_body)

    def test_helper_free_runtime_matrix_covers_unused_helper_library_pruning(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "actc_runtime_helper_free_unused_helper_libraries_pruned"
        matrix_groups = self._makefile_runtime_matrix_shape_groups(self.make_text)
        runtime_shapes = matrix_groups.get("ACTION_ACTC_ALINK_RUNTIME_SHAPES", set())
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(
            shape,
            runtime_shapes,
            "Runtime matrix must prove helper-free programs ignore unused helper libraries",
        )
        self.assertIn("runtime_library_objects", case)
        self.assertNotIn("expected_alink_loads", case)
        staged_modules = set(case["runtime_library_objects"])
        for module_name in {
            "rt_print_f",
            "rt_gfx_bgcolor",
            "rt_sid_vol",
            "rt_sprite_on",
            "rt_joy",
            "rt_mp",
            "rt_dbf_open",
        }:
            self.assertIn(module_name, staged_modules)
            self.assertIn(f"LIB/{module_name.upper()}.OBJ", case["unexpected_alink_loads"])

    def test_object_code_graph_matrix_covers_lettered_library_dependency_helper(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shape = "object_code_library_dependency_lettered_import_library_helper"
        graph_shapes = self._makefile_shape_group(
            self.make_text,
            "ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES",
        )
        case = probe.DIRECT_PRG_CASES[shape]

        self.assertIn(shape, graph_shapes)
        self.assertEqual(case["expected_alink_loads"], ["LIB/A.OBJ", "LIB/HELPER.OBJ"])
        self.assertNotIn("extra_objects", case)
        for dummy_name in ("D0", "D9"):
            self.assertIn(f"LIB/{dummy_name}.OBJ", case["unexpected_alink_loads"])

    def test_runtime_matrix_targets_wrap_each_shape_with_timeout_and_retry(self) -> None:
        aggregate_targets = self._makefile_target_submakes(
            self.make_text,
            "vice-action-actc-alink-launch-runtime-matrices",
        )
        matrix_targets = sorted(target for target in aggregate_targets if target.endswith("-runtime-matrix"))

        self.assertIn("ACTION_ACTC_ALINK_PROBE_TIMEOUT ?= 720s", self.make_text)
        self.assertIn("ACTION_ACTC_ALINK_PROBE_ATTEMPTS ?= 5", self.make_text)
        self.assertIn("ACTION_ACTC_ALINK_INPUT_PROBE_ATTEMPTS ?= 5", self.make_text)
        self.assertTrue(matrix_targets, "No focused runtime matrix targets found")
        for target in matrix_targets:
            with self.subTest(target=target):
                body = self._makefile_target_body(self.make_text, target)
                self.assertTrue(body, f"Missing runtime launch matrix target {target}")
                self.assertIn("for shape in $(ACTION_ACTC_ALINK_", body)
                self.assertNotIn("for attempt in 1 2 3", body)
                self.assertIn(
                    "timeout $(ACTION_ACTC_ALINK_PROBE_TIMEOUT) $(PYTHON) "
                    "tools/run_action_actc_alink_launch_probe_direct.py",
                    body,
                )
                attempts_var = (
                    "ACTION_ACTC_ALINK_INPUT_PROBE_ATTEMPTS"
                    if target == "vice-action-actc-alink-launch-input-runtime-matrix"
                    else "ACTION_ACTC_ALINK_PROBE_ATTEMPTS"
                )
                self.assertIn(
                    f"--shape \"$$shape\" --attempts $({attempts_var}) --attempt-delay 4.0",
                    body,
                )
                self.assertIn("vp.cleanup_stale_vice(settle_seconds=1.0)", body)
                self.assertIn("runtime shape $$shape failed with status $$status", body)
                self.assertNotIn('--shape "$$shape" || exit $$?', body)

    def test_variable_gfx_matrix_covers_reassigned_helper_argument(self) -> None:
        matrix_groups = self._makefile_runtime_matrix_shape_groups(self.make_text)
        variable_gfx_shapes = matrix_groups.get("ACTION_ACTC_ALINK_VARIABLE_GFX_RUNTIME_SHAPES", set())

        self.assertIn(
            "actc_runtime_variable_gfx_reassigned_color_helpers_linked",
            variable_gfx_shapes,
            "Variable GFX runtime matrix must cover latest-store lookup across reassigned helper args",
        )

    def test_variable_sid_sprite_matrices_cover_reassigned_helper_arguments(self) -> None:
        matrix_groups = self._makefile_runtime_matrix_shape_groups(self.make_text)
        variable_sid_shapes = matrix_groups.get("ACTION_ACTC_ALINK_VARIABLE_SID_RUNTIME_SHAPES", set())
        variable_sprite_shapes = matrix_groups.get("ACTION_ACTC_ALINK_VARIABLE_SPRITE_RUNTIME_SHAPES", set())

        self.assertIn(
            "actc_runtime_variable_sid_reassigned_level_helpers_linked",
            variable_sid_shapes,
            "Variable SID runtime matrix must cover latest-store lookup across reassigned helper args",
        )
        self.assertIn(
            "actc_runtime_variable_sprite_reassigned_color_helpers_linked",
            variable_sprite_shapes,
            "Variable sprite runtime matrix must cover latest-store lookup across reassigned helper args",
        )

    def test_input1_demo_target_uses_exported_sample_source(self) -> None:
        self.assertIn(
            "vice-action-actc-alink-launch-input1-demo:",
            self.make_text,
            "Missing focused INPUT1 exported sample launch target",
        )
        self.assertIn(
            "--shape actc_runtime_input1_export_sample_linked --source-from /IMAGES/ACTION.DNP/SRC/INPUT1_DEMO.ACT",
            self.make_text,
            "INPUT1 demo target must compile the sample exported in the release workspace",
        )

    def test_dbf1_demo_target_uses_exported_sample_source(self) -> None:
        self.assertIn(
            "vice-action-actc-alink-launch-dbf1-demo:",
            self.make_text,
            "Missing focused DBF1 exported sample launch target",
        )
        self.assertIn(
            "--shape actc_runtime_dbf1_export_sample_linked --source-from /IMAGES/ACTION.DNP/SRC/DBF1_DEMO.ACT",
            self.make_text,
            "DBF1 demo target must compile the sample exported in the release workspace",
        )

    def test_input_runtime_matrix_covers_input1_split_helpers(self) -> None:
        matrix_groups = self._makefile_runtime_matrix_shape_groups(self.make_text)
        input_shapes = matrix_groups.get("ACTION_ACTC_ALINK_INPUT_RUNTIME_SHAPES", set())

        for shape in {
            "actc_runtime_input1_export_sample_linked",
            "actc_runtime_input1_joy_split_linked",
            "actc_runtime_input1_joy_seen_split_linked",
            "actc_runtime_input1_joy_button_split_linked",
            "actc_runtime_input1_mouse_poll_split_linked",
            "actc_runtime_input1_mouse_seen_split_linked",
            "actc_runtime_input1_mouse_x_split_linked",
            "actc_runtime_input1_mouse_y_split_linked",
            "actc_runtime_input1_mouse_button_split_linked",
            "actc_runtime_input1_mouse_button_state_split_linked",
        }:
            self.assertIn(shape, input_shapes)

    def test_dbf_runtime_matrix_covers_dbf1_split_helpers(self) -> None:
        matrix_groups = self._makefile_runtime_matrix_shape_groups(self.make_text)
        dbf_shapes = matrix_groups.get("ACTION_ACTC_ALINK_DBF_RUNTIME_SHAPES", set())

        self.assertEqual(
            dbf_shapes,
            {
                "actc_runtime_dbf1_export_sample_linked",
                "actc_runtime_dbf1_create_split_linked",
                "actc_runtime_dbf1_open_split_linked",
                "actc_runtime_dbf1_open_missing_file_linked",
                "actc_runtime_dbf1_close_split_linked",
                "actc_runtime_dbf1_close_state_reset_linked",
                "actc_runtime_dbf1_go_split_linked",
                "actc_runtime_dbf1_invalid_record_field_linked",
                "actc_runtime_dbf1_field_count_split_linked",
                "actc_runtime_dbf1_field_len_split_linked",
                "actc_runtime_dbf1_read_byte_split_linked",
                "actc_runtime_dbf1_large_file_read_byte_linked",
                "actc_runtime_dbf1_read_field_byte_split_linked",
                "actc_runtime_dbf1_write_field_byte_split_linked",
                "actc_runtime_dbf1_write_byte_split_linked",
                "actc_runtime_dbf1_save_split_linked",
                "actc_runtime_dbf1_large_file_save_linked",
                "actc_runtime_dbf1_save_invalid_handle_linked",
                "actc_runtime_dbf1_read_byte_invalid_offset_linked",
                "actc_runtime_dbf1_read_byte_invalid_handle_linked",
                "actc_runtime_dbf1_delete_undelete_split_linked",
                "actc_runtime_dbf1_append_split_linked",
                "actc_runtime_dbf1_pack_split_linked",
                "actc_runtime_dbf1_deleted_split_linked",
                "actc_runtime_dbf1_header_record_len_split_linked",
                "actc_runtime_dbf1_read_byte_result_sprite_arg_linked",
                "actc_runtime_dbf1_read_byte_joystick_offset_linked",
                "actc_runtime_dbf1_total_recs_split_linked",
                "actc_runtime_dbf1_curr_rec_no_split_linked",
                "actc_runtime_dbf1_total_recs_result_sid_arg_linked",
            },
        )

    def test_misc_runtime_matrix_covers_sidspr1_named_constant_splits(self) -> None:
        matrix_groups = self._makefile_runtime_matrix_shape_groups(self.make_text)
        misc_shapes = matrix_groups.get("ACTION_ACTC_ALINK_MISC_RUNTIME_SHAPES", set())

        for shape in {
            "actc_runtime_sidspr1_export_sample_linked",
            "actc_runtime_sidspr1_sid_wave_mask_linked",
            "actc_runtime_sidspr1_sid_mode_mask_linked",
            "actc_runtime_sidspr1_sprite_prio_back_linked",
        }:
            self.assertIn(shape, misc_shapes)

    def test_gfx_runtime_matrix_covers_gfx1_export_sample_splits(self) -> None:
        matrix_groups = self._makefile_runtime_matrix_shape_groups(self.make_text)
        gfx_shapes = matrix_groups.get("ACTION_ACTC_ALINK_GFX_RUNTIME_SHAPES", set())

        for shape in {
            "actc_runtime_gfx1_export_sample_linked",
            "actc_runtime_gfx1_bgcolor_split_linked",
            "actc_runtime_gfx1_bordercolor_split_linked",
            "actc_runtime_gfx1_vic_bank_split_linked",
            "actc_runtime_gfx1_screen_base_split_linked",
            "actc_runtime_gfx1_bitmap_base_split_linked",
            "actc_runtime_gfx1_screen_cell_split_linked",
            "actc_runtime_gfx1_color_cell_split_linked",
            "actc_runtime_gfx1_screen_copy_split_linked",
            "actc_runtime_gfx1_color_copy_split_linked",
            "actc_runtime_gfx1_bitmap_fill_split_linked",
            "actc_runtime_gfx1_bitmap_copy_split_linked",
            "actc_runtime_gfx1_bitmap_on_split_linked",
            "actc_runtime_gfx1_bitmap_off_split_linked",
            "actc_runtime_gfx1_mbitmap_on_split_linked",
            "actc_runtime_gfx1_mbitmap_off_split_linked",
        }:
            self.assertIn(shape, gfx_shapes)

    def test_math_runtime_matrix_covers_math1_split_helpers(self) -> None:
        matrix_groups = self._makefile_runtime_matrix_shape_groups(self.make_text)
        math_shapes = matrix_groups.get("ACTION_ACTC_ALINK_MATH_RUNTIME_SHAPES", set())

        for shape in {
            "actc_runtime_integer_add_sub_linked",
            "actc_runtime_integer_mul_div_linked",
            "actc_runtime_integer_mul_store_linked",
            "actc_runtime_integer_for_ascending_wrap_linked",
            "actc_runtime_integer_for_dynamic_descending_zero_linked",
            "actc_runtime_integer_for_nested_linked",
            "actc_runtime_math1_export_sample_linked",
            "actc_runtime_math1_fabs_split_linked",
            "actc_runtime_math1_fsqrt_split_linked",
            "actc_runtime_math1_fsign_split_linked",
            "actc_runtime_math1_ftrunc_split_linked",
            "actc_runtime_math1_ffloor_split_linked",
            "actc_runtime_math1_fceil_split_linked",
            "actc_runtime_math1_fround_split_linked",
            "actc_runtime_math1_ffrac_split_linked",
            "actc_runtime_math1_fmod_split_linked",
            "actc_runtime_math1_fhypot_split_linked",
            "actc_runtime_math1_fpow_split_linked",
            "actc_runtime_math1_fsin_split_linked",
            "actc_runtime_math1_fcos_split_linked",
            "actc_runtime_math1_ftan_split_linked",
            "actc_runtime_math1_fatan2_split_linked",
            "actc_runtime_math1_fexp_split_linked",
            "actc_runtime_math1_fln_split_linked",
            "actc_runtime_math1_flog2_split_linked",
            "actc_runtime_math1_flog10_split_linked",
            "actc_runtime_math1_deg_to_rad_split_linked",
            "actc_runtime_math1_rad_to_deg_split_linked",
            "actc_runtime_math1_fmin_split_linked",
            "actc_runtime_math1_fmax_split_linked",
            "actc_runtime_math1_fclamp_split_linked",
            "actc_runtime_math1_fclamp_permuted_split_linked",
            "actc_runtime_math1_printre_split_linked",
            "actc_runtime_math1_printr_split_linked",
            "actc_runtime_math1_real_int_split_linked",
            "actc_runtime_math1_real_to_int_split_linked",
            "actc_runtime_math1_real_add_split_linked",
            "actc_runtime_math1_real_sub_split_linked",
            "actc_runtime_math1_real_mul_split_linked",
            "actc_runtime_math1_real_div_split_linked",
            "actc_runtime_math1_real_cmp_split_linked",
        }:
            self.assertIn(shape, math_shapes)

        all_math_shapes = self._makefile_shape_group(
            self.make_text,
            "ACTION_ACTC_ALINK_MATH_RUNTIME_SHAPES",
        )
        self.assertIn("real_const_printre_folded", all_math_shapes)
        self.assertIn("actc_math1_angle_conversions_postfix_linked", all_math_shapes)

        direct_math_shapes = self._makefile_shape_group(
            self.make_text,
            "ACTION_ALINK_PRG_MATH_HELPER_SHAPES",
        )
        self.assertEqual(
            direct_math_shapes,
            {
                "runtime_real_f_add_full_range_helper_linked",
                "runtime_real_f_cmp_full_range_helper_linked",
                "runtime_real_f_div_full_range_helper_linked",
                "runtime_real_f_mul_full_range_helper_linked",
                "runtime_real_f_sqrt_full_range_helper_linked",
                "runtime_real_print_full_range_helper_linked",
                "runtime_real_f_sub_full_range_helper_linked",
                "runtime_real_f_to_i_full_range_helper_linked",
            },
        )
        body = self._makefile_target_body(
            self.make_text,
            "vice-action-actc-alink-launch-math-runtime-matrix",
        )
        self.assertIn("for shape in $(ACTION_ALINK_PRG_MATH_HELPER_SHAPES)", body)
        self.assertIn("tools/run_action_alink_prg_probe.py", body)

    def test_native_integer_lowering_is_compiler_owned(self) -> None:
        emitter = (
            self.workspace / "actionc64u" / "src" / "tools_udos" / "actc" / "actc_overlay_emit_object.asm"
        ).read_text(encoding="ascii")
        native_lowering = (
            self.workspace
            / "actionc64u"
            / "src"
            / "tools_udos"
            / "actc"
            / "actc_overlay_emit_native_integer.inc"
        ).read_text(encoding="ascii")
        native_local_lowering = (
            self.workspace
            / "actionc64u"
            / "src"
            / "tools_udos"
            / "actc"
            / "actc_overlay_emit_native_local_integer.inc"
        ).read_text(encoding="ascii")
        native_real_lowering = (
            self.workspace
            / "actionc64u"
            / "src"
            / "tools_udos"
            / "actc"
            / "actc_overlay_emit_native_real.inc"
        ).read_text(encoding="ascii")
        native_real_control_lowering = (
            self.workspace
            / "actionc64u"
            / "src"
            / "tools_udos"
            / "actc"
            / "actc_overlay_emit_native_real_control.inc"
        ).read_text(encoding="ascii")
        native_real_while_lowering = (
            self.workspace
            / "actionc64u"
            / "src"
            / "tools_udos"
            / "actc"
            / "actc_overlay_emit_native_real_while.inc"
        ).read_text(encoding="ascii")
        native_runtime_condition_lowering = (
            self.workspace
            / "actionc64u"
            / "src"
            / "tools_udos"
            / "actc"
            / "actc_overlay_emit_native_runtime_condition.inc"
        ).read_text(encoding="ascii")
        alink = (
            self.workspace / "actionc64u" / "src" / "tools_udos" / "alink" / "alink.asm"
        ).read_text(encoding="ascii")
        direct_prg = (
            self.workspace / "actionc64u" / "src" / "tools_udos" / "alink" / "direct_prg.inc"
        ).read_text(encoding="ascii")

        self.assertIn('.include "actc_overlay_emit_native_integer.inc"', emitter)
        self.assertIn('.include "actc_overlay_emit_native_local_integer.inc"', emitter)
        self.assertIn("is_main_native_integer_machine_object:", native_lowering)
        self.assertIn("native_int_emit_reloc_list:", native_lowering)
        self.assertIn("native_local_emit_reloc_list:", native_local_lowering)
        self.assertIn("native_real_detect:", native_real_lowering)
        self.assertIn("native_real_emit_machine_code_list:", native_real_lowering)
        self.assertIn("native_real_binary_body_pattern:", native_real_lowering)
        self.assertIn("native_real_emit_binary_machine_code:", native_real_lowering)
        self.assertIn("native_real_bits_body_pattern:", native_real_lowering)
        self.assertIn("native_real_emit_bits_machine_code:", native_real_lowering)
        self.assertIn("native_real_unary_signed_body_pattern:", native_real_lowering)
        self.assertIn("native_real_unary_positive_body_pattern:", native_real_lowering)
        self.assertIn("native_real_emit_unary_machine_code:", native_real_lowering)
        self.assertIn("native_real_input_body_pattern:", native_real_lowering)
        self.assertIn("native_real_input_stored_body_pattern:", native_real_lowering)
        self.assertIn("native_real_emit_input_machine_code:", native_real_lowering)
        self.assertIn("native_real_control_detect:", native_real_control_lowering)
        self.assertIn("native_real_control_plain_pattern:", native_real_control_lowering)
        self.assertIn("native_real_control_else_pattern:", native_real_control_lowering)
        self.assertIn("native_real_control_nested_pattern:", native_real_control_lowering)
        self.assertIn("native_real_control_do_simple_pattern:", native_real_control_lowering)
        self.assertIn("native_real_control_do_binary_add_pattern:", native_real_control_lowering)
        self.assertIn("native_real_control_do_binary_sub_zero_pattern:", native_real_control_lowering)
        self.assertIn("native_real_control_do_binary_sub_nonzero_pattern:", native_real_control_lowering)
        self.assertIn("native_real_control_emit_do_simple_machine_code:", native_real_control_lowering)
        self.assertIn("native_real_control_emit_do_binary_machine_code:", native_real_control_lowering)
        self.assertIn("native_real_control_emit_machine_code_list:", native_real_control_lowering)
        self.assertIn("native_real_while_simple_a_zero_pattern:", native_real_while_lowering)
        self.assertIn("native_real_while_simple_b_convert_pattern:", native_real_while_lowering)
        self.assertIn("native_real_while_binary_add_pattern:", native_real_while_lowering)
        self.assertIn("native_real_while_binary_sub_zero_pattern:", native_real_while_lowering)
        self.assertIn("native_real_while_binary_sub_nonzero_pattern:", native_real_while_lowering)
        self.assertIn("native_real_while_emit_machine_code_list:", native_real_while_lowering)
        self.assertIn("native_runtime_condition_arg_eq_pattern:", native_runtime_condition_lowering)
        self.assertIn("native_runtime_condition_arg_ne_pattern:", native_runtime_condition_lowering)
        self.assertIn("native_runtime_condition_noarg_eq_pattern:", native_runtime_condition_lowering)
        self.assertIn("native_runtime_condition_noarg_ne_pattern:", native_runtime_condition_lowering)
        self.assertIn("native_runtime_condition_emit_machine_code_list:", native_runtime_condition_lowering)
        self.assertNotIn("PRG_BUILD_INTEGER_SEQUENCE", alink)
        self.assertNotIn("integer_sequence", direct_prg)
        self.assertNotIn("direct_body_word_store", direct_prg)
        self.assertNotIn("direct_body_word_load_store", direct_prg)
        self.assertNotIn("direct_body_single_call", direct_prg)
        self.assertNotIn("direct_body_fanout", direct_prg)
        self.assertNotIn("direct_body_return", direct_prg)
        self.assertNotIn("direct_body_printmath", direct_prg)
        self.assertNotIn("direct_body_real_print_int", direct_prg)
        self.assertNotIn("find_linked_real_print_int_prg_case", direct_prg)
        self.assertNotIn("build_real_print_int_prg_content_or_fail", direct_prg)
        self.assertNotIn("direct_body_real_to_int", direct_prg)
        self.assertNotIn("find_linked_real_to_int_prg_case", direct_prg)
        self.assertNotIn("build_real_to_int_prg_content_or_fail", direct_prg)
        self.assertNotIn("p1u0T0S0L0U0u1S1r", direct_prg)
        self.assertNotIn("PRG_BUILD_REAL_PRINT_BINARY", alink)
        self.assertNotIn("find_linked_real_print_binary_prg_case", direct_prg)
        self.assertNotIn("build_real_print_binary_prg_content_or_fail", direct_prg)
        self.assertNotIn("append_real_print_binary", direct_prg)
        self.assertNotIn("direct_body_real_print_binary", direct_prg)
        self.assertNotIn("p1u0T0S0p3u0T1S1L0U0L1U1u1T2S2L2U2p4u2r", direct_prg)
        self.assertNotIn("PRG_BUILD_REAL_PRINT_FABS", alink)
        self.assertNotIn("linked_unary_value_index", alink)
        self.assertNotIn("linked_unary_print_index", alink)
        self.assertNotIn("find_linked_real_print_fabs_prg_case", direct_prg)
        self.assertNotIn("build_real_print_fabs_prg_content_or_fail", direct_prg)
        self.assertNotIn("append_real_print_fabs", direct_prg)
        self.assertNotIn("direct_body_real_print_fabs", direct_prg)
        self.assertNotIn("direct_body_real_print_unary_positive", direct_prg)
        self.assertNotIn("p0u0T0S0L0U0u1T1S1L1U1p1u2r", direct_prg)
        self.assertNotIn("p1u0T0S0L0U0u1T1S1L1U1p2u2r", direct_prg)
        self.assertNotIn("PRG_BUILD_INPUT_REAL_PRINT_INT", alink)
        self.assertNotIn("PRG_BUILD_INPUT_STORED_REAL_PRINT_INT", alink)
        self.assertNotIn("find_linked_input_real_print_int_prg_case", direct_prg)
        self.assertNotIn("find_linked_input_stored_real_print_int_prg_case", direct_prg)
        self.assertNotIn("build_input_real_print_int_prg_content_or_fail", direct_prg)
        self.assertNotIn("build_input_stored_real_print_int_prg_content_or_fail", direct_prg)
        self.assertNotIn("append_input_real_print_int", direct_prg)
        self.assertNotIn("append_input_stored_real_print_int", direct_prg)
        self.assertNotIn("direct_body_input_real_print_int", direct_prg)
        self.assertNotIn("direct_body_input_stored_real_print_int", direct_prg)
        self.assertNotIn("p0u0p2u1T0S0L0U0p3u2r", direct_prg)
        self.assertNotIn("p0u0S0p2u1T1S1L1U1p3u2r", direct_prg)
        self.assertNotIn("PRG_BUILD_REAL_IF_GT", alink)
        self.assertNotIn("find_linked_real_if_gt_prg_case", direct_prg)
        self.assertNotIn("build_real_if_gt_prg_content_or_fail", direct_prg)
        self.assertNotIn("direct_body_real_if", direct_prg)
        self.assertNotIn("direct_body_real_nested_if", direct_prg)
        self.assertNotIn("p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghp5S2vr", direct_prg)
        self.assertNotIn("p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghp5S2wp6S2vr", direct_prg)
        self.assertNotIn("p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghL0U0L1U1u1p5ghp6S2vvr", direct_prg)
        self.assertNotIn("PRG_BUILD_REAL_DO_UNTIL", alink)
        self.assertNotIn("find_linked_real_do_until_prg_case", direct_prg)
        self.assertNotIn("build_real_do_until_prg_content_or_fail", direct_prg)
        self.assertNotIn("direct_body_real_do_until", direct_prg)
        self.assertNotIn("append_real_do_until", direct_prg)
        self.assertNotIn("REAL_DO_UNTIL_", direct_prg)
        self.assertNotIn("p0p0T0S0p2u0T1S1dp4u0T0S0L0U0L1U1u1p5gtop6S2r", direct_prg)
        self.assertNotIn(
            "p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p5gtop6S3r",
            direct_prg,
        )
        self.assertNotIn("PRG_BUILD_REAL_WHILE", alink)
        self.assertNotIn("find_linked_real_while_prg_case", direct_prg)
        self.assertNotIn("build_real_while_prg_content_or_fail", direct_prg)
        self.assertNotIn("direct_body_real_while", direct_prg)
        self.assertNotIn("append_real_while", direct_prg)
        self.assertNotIn("REAL_WHILE_", direct_prg)
        self.assertNotIn("p1u0T0S0p3u0T1S1dL0U0L1U1u1p4gfp5S2p6p6T0S0xr", direct_prg)
        self.assertNotIn("PRG_BUILD_RUNTIME_HELPER_CONDITION", alink)
        self.assertNotIn("find_runtime_helper_condition_prg_case", direct_prg)
        self.assertNotIn("build_runtime_helper_condition_prg_content_or_fail", direct_prg)
        self.assertNotIn("direct_body_runtime_helper_if_eq", direct_prg)
        self.assertNotIn("direct_body_runtime_helper_noarg_if_eq", direct_prg)
        self.assertNotIn("p0u0p1qhp2u1vr", direct_prg)
        self.assertNotIn("u0p0qhp1u1vr", direct_prg)
        self.assertNotIn("direct_body_if_eq", direct_prg)
        self.assertNotIn("direct_body_if_ne", direct_prg)
        self.assertNotIn("direct_body_if_lt", direct_prg)
        self.assertNotIn("direct_body_if_gt", direct_prg)
        self.assertNotIn("direct_body_if_ge", direct_prg)
        self.assertNotIn("direct_body_if_le", direct_prg)
        self.assertNotIn("direct_body_if_else:\n", direct_prg)
        self.assertNotIn("direct_body_nested_if:\n", direct_prg)
        self.assertNotIn("direct_body_nested_else:\n", direct_prg)
        self.assertNotIn("direct_body_do_until_eq", direct_prg)
        self.assertNotIn("direct_body_do_until_lt", direct_prg)
        self.assertNotIn("direct_body_nested_do_until_eq", direct_prg)
        self.assertNotIn("direct_body_do_if_until_eq", direct_prg)
        self.assertNotIn("direct_body_do_if_else_until_eq", direct_prg)
        self.assertNotIn("direct_body_if_do_until_eq", direct_prg)
        self.assertNotIn("direct_body_if_else_do_until_eq", direct_prg)
        self.assertNotIn("direct_body_if_local_call_do_until_eq", direct_prg)
        for retired_local_body in (
            "if_else_local_call_do_until_eq",
            "nested_if_local_call",
            "nested_else_local_call",
            "nested_do_local_call",
            "nested_do_if_else_local_call",
            "if_local_call_nested_do_if_else",
            "if_else_local_call_nested_do_if_else",
            "nested_else_local_call_nested_do_if_else",
            "if_else_local_call_chain_nested_do_if_else",
            "nested_else_local_call_chain_nested_do_if_else",
        ):
            self.assertNotIn(f"direct_body_{retired_local_body}", direct_prg)
        self.assertNotIn("direct_prg_template_word_store", direct_prg)
        self.assertNotIn("direct_prg_template_word_load_store", direct_prg)
        self.assertNotIn("direct_prg_template_single_call", direct_prg)
        self.assertNotIn("direct_prg_template_fanout", direct_prg)
        self.assertNotIn("direct_prg_template_printmath", direct_prg)
        self.assertNotIn("direct_prg_template_if_eq", direct_prg)
        self.assertNotIn("direct_prg_template_if_ne", direct_prg)
        self.assertNotIn("direct_prg_template_if_lt", direct_prg)
        self.assertNotIn("direct_prg_template_if_gt", direct_prg)
        self.assertNotIn("direct_prg_template_if_ge", direct_prg)
        self.assertNotIn("direct_prg_template_if_le", direct_prg)
        self.assertNotIn("direct_prg_template_if_else:\n", direct_prg)
        self.assertNotIn("direct_prg_template_nested_if:\n", direct_prg)
        self.assertNotIn("direct_prg_template_nested_else:\n", direct_prg)
        self.assertNotIn("direct_prg_template_do_until_eq", direct_prg)
        self.assertNotIn("direct_prg_template_do_until_lt", direct_prg)
        self.assertNotIn("direct_prg_template_nested_do_until_eq", direct_prg)
        self.assertNotIn("direct_prg_template_do_if_until_eq", direct_prg)
        self.assertNotIn("direct_prg_template_do_if_else_until_eq", direct_prg)
        self.assertNotIn("direct_prg_template_if_do_until_eq", direct_prg)
        self.assertNotIn("direct_prg_template_if_else_do_until_eq", direct_prg)
        self.assertNotIn("direct_prg_template_if_local_call_do_until_eq", direct_prg)
        for retired_local_template in (
            "if_else_local_call_do_until_eq",
            "nested_if_local_call",
            "nested_else_local_call",
            "nested_do_local_call",
            "nested_do_if_else_local_call",
            "if_local_call_nested_do_if_else",
            "if_else_local_call_nested_do_if_else",
            "nested_else_local_call_nested_do_if_else",
            "if_else_local_call_chain_nested_do_if_else",
            "nested_else_local_call_chain_nested_do_if_else",
        ):
            self.assertNotIn(f"direct_prg_template_{retired_local_template}", direct_prg)
        self.assertNotIn("build_printmath_linked_string_int", direct_prg)
        self.assertNotIn("PRG_BUILD_PRINTMATH_STRING_INT", alink)

    def test_alink_runtime_helper_synthesis_is_removed(self) -> None:
        alink = (
            self.workspace / "actionc64u" / "src" / "tools_udos" / "alink" / "alink.asm"
        ).read_text(encoding="ascii")
        direct_prg = (
            self.workspace / "actionc64u" / "src" / "tools_udos" / "alink" / "direct_prg.inc"
        ).read_text(encoding="ascii")
        combined = alink + direct_prg

        for retired_symbol in (
            "PRG_BUILD_RUNTIME_HELPER_SEQUENCE",
            "find_runtime_helper_sequence_prg_case",
            "build_runtime_helper_sequence_prg_content_or_fail",
            "RUNTIME_HELPER_KIND_",
            "linked_runtime_",
            "runtime_name_rt_",
            "runtime_helper_prg_exit_template",
            "ALINK_RUNTIME_STORE",
            "ALINK_LINKED_LITERAL",
            "LINKED_LITERAL",
        ):
            self.assertNotIn(retired_symbol, combined)

        self.assertIn(
            "select_prg_build_strategy_or_fail:\n"
            "    lda #PRG_BUILD_DIRECT\n"
            "    sta prg_build_strategy\n"
            "    jsr find_object_code_prg_case",
            direct_prg,
        )
        self.assertIn(
            "build_prg_content_or_fail:\n"
            "    lda prg_build_strategy\n"
            "    cmp #PRG_BUILD_OBJECT_CODE",
            direct_prg,
        )

    def test_direct_prg_legacy_candidate_table_is_removed(self) -> None:
        direct_prg = (
            self.workspace / "actionc64u" / "src" / "tools_udos" / "alink" / "direct_prg.inc"
        ).read_text(encoding="ascii")
        alink = (
            self.workspace / "actionc64u" / "src" / "tools_udos" / "alink" / "alink.asm"
        ).read_text(encoding="ascii")

        for retired_symbol in (
            "direct_body_table_lo",
            "direct_body_table_hi",
            "direct_template_table_lo",
            "direct_template_table_hi",
            "direct_template_len_lo",
            "direct_template_len_hi",
            "direct_body_seeded_runtime",
            "direct_prg_template_seeded_runtime",
            "direct_candidate_index",
        ):
            self.assertNotIn(retired_symbol, direct_prg + alink)
        self.assertIn(
            "build_direct_prg_content_or_fail:\n    jmp build_direct_prg_fallback",
            direct_prg,
        )

    def test_seeded_alink_smoke_uses_relocatable_machine_objects(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_seeded_runtime_probe as probe

        main_obj = probe.seeded_main_object_text()
        work_obj = probe.seeded_work_object_text()
        self.assertIn("x main 0 19\nb u0M\nu w\nm 20 00 00", main_obj)
        self.assertIn("r 1 u0\n", main_obj)
        self.assertIn("x w 0 1\nb M\nm 60\n", work_obj)
        self.assertNotIn("b e0u0", main_obj)
        self.assertNotIn("b s0i0r", work_obj)
        self.assertEqual(
            probe.EXPECTED_PRG,
            bytes.fromhex("0010201310A9A58DD003A90085028503A2024C0FCF60"),
        )

    def test_local_procedure_matrix_uses_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        for shape in (
            "if_local_call_do_until_eq",
            "while_lt_local_call",
            "if_else_local_call_do_until_eq",
            "nested_if_local_call",
            "nested_else_local_call",
            "nested_do_local_call",
            "nested_do_if_else_local_call",
            "if_local_call_nested_do_if_else",
            "if_else_local_call_nested_do_if_else",
            "nested_else_local_call_nested_do_if_else",
            "if_else_local_call_chain_nested_do_if_else",
            "nested_else_local_call_chain_nested_do_if_else",
        ):
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                fragments = "".join(case["expected_object_fragments"])
                self.assertIn("b M\n", fragments)
                self.assertIn("x __idata ", fragments)
                self.assertIn("x __iptr ", fragments)
                self.assertGreaterEqual(case["store_check_addr"], 0x1000)

    def test_local_call_loop_uses_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["if_local_call_do_until_eq"]
        self.assertIn(
            "x main 0 166\n"
            "x a 104 56\n"
            "x __p1l0 88 1\n"
            "x __p0l0 104 1\n"
            "x __idata 160 4\n"
            "x __iptr 164 2\n",
            case["expected_object_fragments"],
        )
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 83 x __p1l0\n"
            "r 86 x a\n"
            "r 157 x __p0l0\n"
            "r 164 x __idata\n",
            case["expected_object_fragments"],
        )
        self.assertEqual(case["store_check_addr"], 0x10A2)
        self.assertEqual(case["store_check_value"], 2)

    def test_local_call_while_uses_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["while_lt_local_call"]
        self.assertIn(
            "x main 0 111\n"
            "x a 89 18\n"
            "x __p1l0 30 1\n"
            "x __p1l1 73 1\n"
            "x __idata 107 2\n"
            "x __iptr 109 2\n",
            case["expected_object_fragments"],
        )
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 65 x __p1l1\n"
            "r 68 x a\n"
            "r 71 x __p1l0\n"
            "r 109 x __idata\n",
            case["expected_object_fragments"],
        )
        self.assertEqual(case["store_check_addr"], 0x106B)
        self.assertEqual(case["store_check_value"], 1)

    def test_simple_equality_if_uses_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["if_eq"]
        self.assertIn(
            "x main 0 107\nx __if0 85 1\nx __idata 101 4\nx __iptr 105 2\n",
            case["expected_object_fragments"],
        )
        self.assertIn(
            "r 3 x __iptr\nr 9 x __iptr\nr 66 x __if0\nr 105 x __idata\n",
            case["expected_object_fragments"],
        )
        self.assertEqual(case["store_check_addr"], 0x1067)

    def test_simple_not_equal_if_uses_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["if_ne"]
        self.assertIn(
            "x main 0 127\nx __if0 105 1\nx __idata 121 4\nx __iptr 125 2\n",
            case["expected_object_fragments"],
        )
        self.assertIn(
            "r 3 x __iptr\nr 9 x __iptr\nr 86 x __if0\nr 125 x __idata\n",
            case["expected_object_fragments"],
        )
        self.assertEqual(case["store_check_addr"], 0x107B)

    def test_simple_less_than_if_uses_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["if_lt"]
        self.assertIn(
            "x main 0 126\nx __if0 104 1\nx __idata 120 4\nx __iptr 124 2\n",
            case["expected_object_fragments"],
        )
        self.assertIn(
            "r 3 x __iptr\nr 9 x __iptr\nr 85 x __if0\nr 124 x __idata\n",
            case["expected_object_fragments"],
        )
        self.assertEqual(case["store_check_addr"], 0x107A)

    def test_simple_greater_than_if_uses_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["if_gt"]
        self.assertIn(
            "x main 0 128\nx __if0 106 1\nx __idata 122 4\nx __iptr 126 2\n",
            case["expected_object_fragments"],
        )
        self.assertIn(
            "r 3 x __iptr\nr 9 x __iptr\nr 87 x __if0\nr 126 x __idata\n",
            case["expected_object_fragments"],
        )
        self.assertEqual(case["store_check_addr"], 0x107C)

    def test_simple_greater_equal_if_uses_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["if_ge"]
        self.assertIn(
            "x main 0 126\nx __if0 104 1\nx __idata 120 4\nx __iptr 124 2\n",
            case["expected_object_fragments"],
        )
        self.assertIn(
            "r 3 x __iptr\nr 9 x __iptr\nr 85 x __if0\nr 124 x __idata\n",
            case["expected_object_fragments"],
        )
        self.assertEqual(case["store_check_addr"], 0x107A)

    def test_simple_less_equal_if_uses_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["if_le"]
        self.assertIn(
            "x main 0 128\nx __if0 106 1\nx __idata 122 4\nx __iptr 126 2\n",
            case["expected_object_fragments"],
        )
        self.assertIn(
            "r 3 x __iptr\nr 9 x __iptr\nr 87 x __if0\nr 126 x __idata\n",
            case["expected_object_fragments"],
        )
        self.assertEqual(case["store_check_addr"], 0x107C)

    def test_simple_if_else_uses_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["if_else"]
        self.assertIn(
            "x main 0 127\nx __if0 88 1\nx __if1 105 1\nx __idata 121 4\nx __iptr 125 2\n",
            case["expected_object_fragments"],
        )
        self.assertIn(
            "r 3 x __iptr\nr 9 x __iptr\nr 66 x __if0\nr 86 x __if1\nr 125 x __idata\n",
            case["expected_object_fragments"],
        )
        self.assertEqual(case["store_check_addr"], 0x107B)
        true_case = probe.DIRECT_PRG_CASES["if_else_true"]
        self.assertEqual(true_case["expected_object_fragments"], case["expected_object_fragments"])
        self.assertEqual(true_case["store_check_addr"], 0x107B)
        self.assertEqual(true_case["store_check_value"], 0x01)

    def test_nested_if_variants_use_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["nested_if"]
        self.assertIn(
            "x main 0 167\nx __if0 143 1\nx __if2 143 1\n"
            "x __idata 159 6\nx __iptr 165 2\n",
            case["expected_object_fragments"],
        )
        self.assertIn(
            "r 3 x __iptr\nr 9 x __iptr\nr 85 x __if0\n"
            "r 124 x __if2\nr 165 x __idata\n",
            case["expected_object_fragments"],
        )
        self.assertEqual(case["store_check_addr"], 0x10A3)
        false_case = probe.DIRECT_PRG_CASES["nested_if_outer_false"]
        self.assertEqual(false_case["expected_object_fragments"], case["expected_object_fragments"])
        self.assertEqual(false_case["store_check_value"], 0x00)

        else_case = probe.DIRECT_PRG_CASES["nested_else"]
        self.assertIn(
            "x main 0 187\nx __if0 163 1\nx __if2 146 1\n"
            "x __if3 163 1\nx __idata 179 6\nx __iptr 185 2\n",
            else_case["expected_object_fragments"],
        )
        self.assertIn("r 144 x __if3\n", "".join(else_case["expected_object_fragments"]))
        self.assertEqual(else_case["store_check_addr"], 0x10B7)
        self.assertEqual(else_case["store_check_value"], 0x04)

    def test_do_until_variants_use_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        equality = probe.DIRECT_PRG_CASES["do_until_eq"]
        self.assertIn(
            "x main 0 105\nx __do0 30 1\nx __idata 101 2\nx __iptr 103 2\n",
            equality["expected_object_fragments"],
        )
        self.assertIn("r 83 x __do0\n", "".join(equality["expected_object_fragments"]))
        self.assertEqual(equality["store_check_addr"], 0x1065)

        less_than = probe.DIRECT_PRG_CASES["do_until_lt"]
        self.assertIn(
            "x main 0 126\nx __do0 47 1\nx __idata 120 4\nx __iptr 124 2\n",
            less_than["expected_object_fragments"],
        )
        self.assertIn("r 102 x __do0\n", "".join(less_than["expected_object_fragments"]))
        self.assertEqual(less_than["store_check_addr"], 0x1078)

        nested = probe.DIRECT_PRG_CASES["nested_do_until_eq"]
        self.assertIn(
            "x main 0 179\nx __do0 47 1\nx __do1 64 1\n"
            "x __idata 173 4\nx __iptr 177 2\n",
            nested["expected_object_fragments"],
        )
        self.assertIn(
            "r 117 x __do1\nr 155 x __do0\n",
            "".join(nested["expected_object_fragments"]),
        )
        self.assertEqual(nested["store_check_addr"], 0x10AD)

        mixed_cases = {
            "do_if_until_eq": ("x __do0 47 1\nx __if2 119 1\n", 0x10AF),
            "do_if_else_until_eq": ("x __do0 47 1\nx __if2 122 1\n", 0x10C3),
            "if_do_until_eq": ("x __if0 140 1\nx __do1 85 1\n", 0x109E),
            "if_else_do_until_eq": (
                "x __if0 143 1\nx __if1 198 1\nx __do1 85 1\nx __if3 143 1\n",
                0x10D8,
            ),
        }
        for shape, (exports, result_addr) in mixed_cases.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                fragments = "".join(case["expected_object_fragments"])
                self.assertIn(exports, fragments)
                self.assertEqual(case["store_check_addr"], result_addr)

    def test_real_do_until_matrix_uses_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        simple_shapes = (
            "real_do_until_eq",
            "real_do_until_ne",
            "real_do_until_lt",
            "real_do_until_le",
            "real_do_until_gt",
            "real_do_until_ge",
        )
        for shape in simple_shapes:
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                fragments = "".join(case["expected_object_fragments"])
                self.assertEqual(
                    case["expected_object_fragments"],
                    probe._REAL_DO_SIMPLE_OBJECT_FRAGMENTS,
                )
                self.assertIn(
                    "x main 0 146\nx __idata 132 14\nx __doa 132 4\nx __dob 136 4\n"
                    "x __doy 140 2\nx __doyhi 141 1\nx __doptr 142 4\n",
                    fragments,
                )
                self.assertIn("r 142 x __doa\nr 144 x __dob\n", fragments)
                self.assertEqual(case["expected_tail"][142:146], bytes.fromhex("84108810"))
                self.assertNotIn("b p0p0T0S0", fragments)

        binary_shapes = {
            "real_do_until_gt_real_add_loop": "rt_f_add",
            "real_do_until_ge_real_add_loop": "rt_f_add",
            "real_do_until_lt_real_add_loop": "rt_f_add",
            "real_do_until_le_real_add_loop": "rt_f_add",
            "real_do_until_gt_real_sub_loop": "rt_f_sub",
            "real_do_until_ge_real_sub_loop": "rt_f_sub",
            "real_do_until_lt_real_sub_loop": "rt_f_sub",
            "real_do_until_le_real_sub_loop": "rt_f_sub",
        }
        for shape, op_module in binary_shapes.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                fragments = "".join(case["expected_object_fragments"])
                self.assertEqual(
                    case["expected_object_fragments"],
                    probe._real_do_binary_object_fragments(op_module),
                )
                self.assertIn(
                    "x main 0 194\nx __idata 174 20\nx __doa 174 4\nx __dob 178 4\n"
                    "x __doc 182 4\nx __doy 186 2\nx __doyhi 187 1\nx __doptr 188 6\n",
                    fragments,
                )
                self.assertIn(
                    "r 188 x __doa\nr 190 x __dob\nr 192 x __doc\n",
                    fragments,
                )
                self.assertEqual(case["expected_tail"][188:194], bytes.fromhex("ae10b210b610"))
                self.assertNotIn("b p0p0T0S0", fragments)
                self.assertNotIn("b p1u0T0S0", fragments)

    def test_real_while_matrix_uses_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        simple_shapes = (
            "real_while_gt_once",
            "real_while_ge_once",
            "real_while_lt_once",
            "real_while_le_once",
            "real_while_gt_update_nonzero_once",
            "real_while_ge_update_nonzero_once",
            "real_while_lt_update_nonzero_once",
            "real_while_le_update_nonzero_once",
        )
        for shape in simple_shapes:
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                fragments = "".join(case["expected_object_fragments"])
                self.assertEqual(
                    case["expected_object_fragments"],
                    probe._REAL_WHILE_SIMPLE_OBJECT_FRAGMENTS,
                )
                self.assertIn(
                    "x main 0 149\nx __whloop 40 1\nx __idata 135 14\nx __wha 135 4\n"
                    "x __whb 139 4\nx __why 143 2\nx __whyhi 144 1\nx __whptr 145 4\n",
                    fragments,
                )
                self.assertIn("r 104 x __whloop\n", fragments)
                self.assertEqual(case["expected_tail"][145:149], bytes.fromhex("87108b10"))
                self.assertNotIn("fp5S2", fragments)

        binary_shapes = {
            "real_while_gt_real_sub_loop": "rt_f_sub",
            "real_while_ge_real_sub_loop": "rt_f_sub",
            "real_while_lt_real_add_loop": "rt_f_add",
            "real_while_le_real_add_loop": "rt_f_add",
            "real_while_gt_real_add_skip": "rt_f_add",
            "real_while_ge_real_add_skip": "rt_f_add",
            "real_while_lt_real_sub_skip": "rt_f_sub",
            "real_while_le_real_sub_skip": "rt_f_sub",
        }
        for shape, op_module in binary_shapes.items():
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                fragments = "".join(case["expected_object_fragments"])
                self.assertEqual(
                    case["expected_object_fragments"],
                    probe._real_while_binary_object_fragments(op_module),
                )
                self.assertIn(
                    "x main 0 197\nx __whloop 60 1\nx __idata 177 20\nx __wha 177 4\n"
                    "x __whb 181 4\nx __whc 185 4\nx __why 189 2\n"
                    "x __whyhi 190 1\nx __whptr 191 6\n",
                    fragments,
                )
                self.assertIn("r 146 x __whloop\n", fragments)
                self.assertEqual(case["expected_tail"][191:197], bytes.fromhex("b110b510b910"))
                self.assertNotIn("fp6S3", fragments)
                self.assertNotIn("fp7S3", fragments)

    def test_runtime_condition_matrix_uses_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        cases = {
            "actc_runtime_input_joystick_condition_gfx_helper_linked": (
                probe._runtime_condition_arg_object_fragments("rt_joy", 2, 0, 6)
            ),
            "actc_runtime_input_joystick_not_equal_condition_gfx_helper_linked": (
                probe._runtime_condition_arg_object_fragments("rt_joy", 2, 1, 6, 0xF0)
            ),
            "actc_runtime_input_mouse_button_condition_gfx_helper_linked": (
                probe._runtime_condition_noarg_object_fragments("rt_mb", 0, 6)
            ),
            "actc_runtime_input_mouse_button_not_equal_condition_gfx_helper_linked": (
                probe._runtime_condition_noarg_object_fragments("rt_mb", 1, 6, 0xF0)
            ),
            "actc_runtime_input_joystick_button_condition_gfx_helper_linked": (
                probe._runtime_condition_arg_object_fragments("rt_jb1", 2, 0, 3)
            ),
            "actc_runtime_input_joystick_button2_condition_gfx_helper_linked": (
                probe._runtime_condition_arg_object_fragments("rt_jb2", 2, 0, 7)
            ),
            "actc_runtime_input_mouse_button2_condition_gfx_helper_linked": (
                probe._runtime_condition_noarg_object_fragments("rt_mb2", 0, 7)
            ),
        }
        for shape, expected_fragments in cases.items():
            with self.subTest(shape=shape):
                fragments = probe.DIRECT_PRG_CASES[shape]["expected_object_fragments"]
                joined = "".join(fragments)
                self.assertEqual(fragments, expected_fragments)
                self.assertIn("b u0u1M\n", joined)
                self.assertIn("\nm ", "\n" + joined)
                self.assertNotIn("qhp", joined)
                self.assertNotIn("nhp", joined)

    def test_literal_runtime_sequence_matrix_uses_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        self.assertEqual(len(probe.RUNTIME_LITERAL_SEQUENCE_SHAPES), 194)
        self.assertEqual(len(set(probe.RUNTIME_LITERAL_SEQUENCE_SHAPES)), 194)
        self.assertEqual(len(probe.RUNTIME_LITERAL_STATE_SEQUENCE_SHAPES), 106)
        self.assertEqual(len(probe.RUNTIME_STORED_RESULT_SEQUENCE_SHAPES), 77)
        self.assertEqual(len(probe.RUNTIME_NESTED_SEQUENCE_SHAPES), 9)

        self.assertEqual(len(probe.RUNTIME_DBF_SEQUENCE_SHAPES), 19)
        self.assertEqual(len(probe.RUNTIME_NESTED_SEQUENCE_SHAPES), 9)
        for shape in probe.RUNTIME_LITERAL_SEQUENCE_SHAPES:
            with self.subTest(shape=shape):
                fragments = probe.DIRECT_PRG_CASES[shape]["expected_object_fragments"]
                body_lines = [
                    line[2:]
                    for fragment in fragments
                    if isinstance(fragment, str)
                    for line in fragment.splitlines()
                    if line.startswith("b ")
                ]
                self.assertGreaterEqual(len(body_lines), 1)
                self.assertRegex(body_lines[0], r"^(?:u[0-9A-Z])+M$")
                self.assertTrue(all(body == "M" for body in body_lines[1:]))
                self.assertIn("m ", "".join(fragments))

    def test_complex_compiled_runtime_cases_use_independent_link_oracle(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shapes = probe.COMPILED_RUNTIME_LINK_ORACLE_SHAPES
        self.assertEqual(len(shapes), 310)
        self.assertEqual(len(set(shapes)), 310)
        for shape in shapes:
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertIn("source", case)
                self.assertTrue(case["runtime_library_objects"])
                self.assertTrue(case["expected_tail_from_compiled_object"])
                self.assertNotIn(shape, probe.RUNTIME_LITERAL_SEQUENCE_SHAPES)

    def test_while_equality_uses_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["while_eq"]
        fragments = "".join(case["expected_object_fragments"])
        self.assertIn(
            "x main 0 108\nx __p0l0 30 1\nx __p0l1 88 1\n"
            "x __idata 104 2\nx __iptr 106 2\n",
            fragments,
        )
        self.assertIn(
            "r 3 x __iptr\nr 9 x __iptr\nr 66 x __p0l1\n"
            "r 86 x __p0l0\nr 106 x __idata\n",
            fragments,
        )
        self.assertEqual(case["store_check_addr"], 0x1068)
        self.assertEqual(case["store_check_value"], 0x01)

    def test_direct_ordered_while_conditions_use_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected = {
            "while_ne": (108, 88, 104, 106, 66, 86, 0x1068, 0x01),
            "while_lt": (107, 87, 103, 105, 65, 85, 0x1067, 0x01),
            "while_gt": (109, 89, 105, 107, 67, 87, 0x1069, 0x00),
            "while_ge": (107, 87, 103, 105, 65, 85, 0x1067, 0x00),
            "while_le": (109, 89, 105, 107, 67, 87, 0x1069, 0x01),
        }
        for shape, values in expected.items():
            with self.subTest(shape=shape):
                root_size, exit_offset, data_offset, pointer_offset, branch_reloc, back_reloc, address, value = values
                case = probe.DIRECT_PRG_CASES[shape]
                fragments = "".join(case["expected_object_fragments"])
                self.assertIn(
                    f"x main 0 {root_size}\nx __p0l0 30 1\nx __p0l1 {exit_offset} 1\n"
                    f"x __idata {data_offset} 2\nx __iptr {pointer_offset} 2\n",
                    fragments,
                )
                self.assertIn(
                    f"r 3 x __iptr\nr 9 x __iptr\nr {branch_reloc} x __p0l1\n"
                    f"r {back_reloc} x __p0l0\nr {pointer_offset} x __idata\n",
                    fragments,
                )
                self.assertEqual(case["store_check_addr"], address)
                self.assertEqual(case["store_check_value"], value)

    def test_printmath_uses_native_object_code_and_link_selected_library_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["printmath"]
        self.assertIn("X=X + 7 - 3", case["source"])
        self.assertIn(
            "x main 0 272\nx __idata 262 8\nx __iptr 270 2\n",
            case["expected_object_fragments"],
        )
        self.assertIn("b u0u1M\nb M\nb M\n", case["expected_object_fragments"])
        self.assertEqual(case["runtime_library_objects"], ["rt_print_i"])
        self.assertEqual(case["expected_alink_loads"], ["LIB/W.OBJ", "LIB/RT_PRINT_I.OBJ"])
        work_object = case["extra_library_objects"]["W.OBJ"]
        self.assertIn("b u0M\nb M\nb M\n", work_object)
        self.assertIn("m A2 00 BD", work_object)
        self.assertNotIn("b s0i0r", work_object)

    def test_native_integer_runtime_case_covers_precedence_division_and_zero_divisor(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["actc_runtime_integer_mul_div_linked"]
        self.assertIn("PrintIE(A+B*C)", case["source"])
        self.assertIn("PrintIE((A+B)*C)", case["source"])
        self.assertIn("PrintIE(B/C)", case["source"])
        self.assertIn("PrintIE(B/0)", case["source"])
        self.assertIn("x main 0 298\nx __idata 290 6\nx __iptr 296 2\n", case["expected_object_fragments"])
        self.assertIn("b u0u1u2M\nb M\nb M\n", case["expected_object_fragments"])
        self.assertEqual(case["runtime_library_objects"], ["rt_i_mul", "rt_print_i", "rt_i_div"])
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/RT_I_MUL.OBJ", "LIB/RT_PRINT_I.OBJ", "LIB/RT_I_DIV.OBJ"],
        )

    def test_native_integer_runtime_case_covers_add_sub_without_mul_div_helpers(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["actc_runtime_integer_add_sub_linked"]
        self.assertIn("PrintIE(A+B-C)", case["source"])
        self.assertIn(
            "x main 0 113\nx __idata 105 6\nx __iptr 111 2\n",
            case["expected_object_fragments"],
        )
        self.assertIn("b u0M\nb M\nb M\n", case["expected_object_fragments"])
        self.assertEqual(case["expected_alink_loads"], ["LIB/RT_PRINT_I.OBJ"])
        self.assertEqual(
            case["unexpected_alink_loads"],
            ["LIB/RT_I_MUL.OBJ", "LIB/RT_I_DIV.OBJ"],
        )

    def test_native_integer_runtime_case_prints_inside_dynamic_while(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES[
            "actc_runtime_integer_dynamic_while_print_mul_linked"
        ]
        self.assertIn("PrintIE(I)", case["source"])
        self.assertIn(
            "x main 0 159\nx __p0l0 30 1\nx __p0l1 139 1\n"
            "x __idata 155 2\nx __iptr 157 2\n",
            case["expected_object_fragments"],
        )
        self.assertIn("b u0u1M\n", case["expected_object_fragments"])
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/RT_PRINT_I.OBJ", "LIB/RT_I_MUL.OBJ"],
        )
        self.assertEqual(case["unexpected_alink_loads"], ["LIB/RT_I_DIV.OBJ"])
        self.assertEqual(case["screen_fragments"], ["1", "2"])
        self.assertEqual(case["store_check_value"], 4)

    def test_native_integer_runtime_case_calls_noarg_helper_inside_dynamic_while(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES[
            "actc_runtime_integer_dynamic_while_noarg_helper_linked"
        ]
        self.assertIn("SidRst()", case["source"])
        self.assertIn(
            "x main 0 138\nx __p0l0 30 1\nx __p0l1 118 1\n"
            "x __idata 134 2\nx __iptr 136 2\n",
            case["expected_object_fragments"],
        )
        self.assertIn("b u0M\n", case["expected_object_fragments"])
        self.assertIn("u rt_sid_rst\n", case["expected_object_fragments"])
        self.assertEqual(case["extra_store_checks"], [{"addr": 0x1086, "value": 1}])
        self.assertEqual(
            case["unexpected_alink_loads"],
            ["LIB/RT_SID_ON.OBJ", "LIB/RT_SID_VOL.OBJ", "LIB/RT_SID_ROUTE.OBJ"],
        )

    def test_native_integer_runtime_case_calls_a_byte_helper_inside_dynamic_while(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES[
            "actc_runtime_integer_dynamic_while_a_byte_helper_linked"
        ]
        self.assertIn("SidVol(I+10)", case["source"])
        self.assertIn(
            "x main 0 174\nx __p0l0 30 1\nx __p0l1 154 1\n"
            "x __idata 170 2\nx __iptr 172 2\n",
            case["expected_object_fragments"],
        )
        self.assertIn("b u0M\n", case["expected_object_fragments"])
        self.assertIn("u rt_sid_vol\n", case["expected_object_fragments"])
        self.assertEqual(case["extra_store_checks"], [{"addr": 0x10AA, "value": 1}])
        self.assertEqual(
            case["expected_alink_loads"],
            ["LIB/RT_SID_VOL.OBJ", "LIB/RT_SID_VOLUME_STATE.OBJ"],
        )
        self.assertEqual(
            case["unexpected_alink_loads"],
            ["LIB/RT_SID_MODE.OBJ", "LIB/RT_SID_FREQ.OBJ"],
        )

    def test_native_integer_runtime_case_calls_xy_word_helper_inside_dynamic_while(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES[
            "actc_runtime_integer_dynamic_while_xy_word_helper_linked"
        ]
        self.assertIn("SidCutoff(I+300)", case["source"])
        self.assertIn(
            "x main 0 176\nx __p0l0 30 1\nx __p0l1 156 1\n"
            "x __idata 172 2\nx __iptr 174 2\n",
            case["expected_object_fragments"],
        )
        self.assertIn("b u0M\n", case["expected_object_fragments"])
        self.assertIn("u rt_sid_cutoff\n", case["expected_object_fragments"])
        self.assertEqual(case["extra_store_checks"], [{"addr": 0x10AC, "value": 1}])
        self.assertEqual(case["expected_alink_loads"], ["LIB/RT_SID_CUTOFF.OBJ"])
        self.assertEqual(
            case["unexpected_alink_loads"],
            ["LIB/RT_SID_FREQ.OBJ", "LIB/RT_SID_RES.OBJ"],
        )

    def test_native_integer_runtime_case_covers_assignment_store(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        case = probe.DIRECT_PRG_CASES["actc_runtime_integer_mul_store_linked"]
        self.assertIn("A=B*C", case["source"])
        self.assertIn("PrintIE(A)", case["source"])
        self.assertIn("x main 0 109\nx __idata 101 6\nx __iptr 107 2\n", case["expected_object_fragments"])
        self.assertIn("b u0u1M\nb M\nb M\n", case["expected_object_fragments"])
        self.assertEqual(case["runtime_library_objects"], ["rt_i_mul", "rt_print_i"])
        self.assertEqual(case["screen_fragments"], ["14"])

    def test_native_integer_runtime_cases_cover_for_direction_wrap_and_nesting(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        ascending = probe.DIRECT_PRG_CASES[
            "actc_runtime_integer_for_ascending_wrap_linked"
        ]
        self.assertIn("FOR I=1 TO 3", ascending["source"])
        self.assertIn("FOR I=65535 TO 65535", ascending["source"])
        self.assertIn(
            "x main 0 645\nx __for0 81 1\nx __fend0 314 1\n"
            "x __for1 365 1\nx __fend1 595 1\n",
            "".join(ascending["expected_object_fragments"]),
        )
        self.assertEqual(ascending["store_check_value"], 7)

        dynamic = probe.DIRECT_PRG_CASES[
            "actc_runtime_integer_for_dynamic_descending_zero_linked"
        ]
        self.assertIn("FOR I=5 TO 1 STEP D", dynamic["source"])
        self.assertIn("FOR I=1 TO 3 STEP Z", dynamic["source"])
        self.assertIn(
            "x main 0 689\nx __for0 118 1\nx __fend0 351 1\n"
            "x __for1 405 1\nx __fend1 635 1\n",
            "".join(dynamic["expected_object_fragments"]),
        )
        self.assertEqual(dynamic["store_check_value"], 9)

        nested = probe.DIRECT_PRG_CASES["actc_runtime_integer_for_nested_linked"]
        self.assertIn("FOR I=1 TO 2", nested["source"])
        self.assertIn("FOR J=1 TO 2", nested["source"])
        self.assertIn(
            "x main 0 650\nx __for0 81 1\nx __fend0 598 1\n"
            "x __for1 240 1\nx __fend1 521 1\n",
            "".join(nested["expected_object_fragments"]),
        )
        self.assertEqual(nested["store_check_value"], 12)

        for case in (ascending, dynamic, nested):
            self.assertEqual(case["expected_alink_loads"], ["LIB/RT_PRINT_I.OBJ"])
            self.assertEqual(
                case["unexpected_alink_loads"],
                ["LIB/RT_I_MUL.OBJ", "LIB/RT_I_DIV.OBJ"],
            )

    def test_plain_word_store_and_load_store_use_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        source_case = probe.DIRECT_PRG_CASES["word_load_store"]
        self.assertIn("X=7\rY=X", source_case["source"])
        self.assertIn(
            "x main 0 72\nx __idata 66 4\nx __iptr 70 2\n",
            source_case["expected_object_fragments"],
        )
        self.assertIn("b M\nb M\nb M\n", source_case["expected_object_fragments"])

        for shape in ("word_store", "word_load_store_seeded"):
            with self.subTest(shape=shape):
                seed = probe.DIRECT_PRG_CASES[shape]["seed_object"]
                self.assertIn("b M\n", seed)
                self.assertIn("\nm ", seed)
                self.assertIn("r 3 x __iptr\n", seed)
                self.assertNotIn("b p0S0", seed)

    def test_basic_return_and_transitive_library_seeds_use_native_object_code(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        empty_seed = probe.DIRECT_PRG_CASES["empty_return"]["seed_object"]
        self.assertIn("b M\n", empty_seed)
        self.assertIn("\nm A9 A5", empty_seed)
        self.assertNotIn("b r\n", empty_seed)

        transitive = probe.DIRECT_PRG_CASES["transitive_library_load"]
        self.assertIn("b u0M\n", transitive["seed_object"])
        self.assertIn("r 1 u0\n", transitive["seed_object"])
        for dependency in transitive["extra_library_objects"].values():
            self.assertIn("b ", dependency)
            self.assertIn("\nm ", dependency)
            self.assertNotIn("b r\n", dependency)

    def test_legacy_body_rejections_cover_retired_native_shapes(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        shapes = (
            "legacy_integer_body_missing_mul_helper_rejects",
            "legacy_integer_body_stack_underflow_rejects",
            "legacy_word_store_body_rejects",
            "legacy_word_load_store_body_rejects",
            "legacy_empty_return_body_rejects",
            "legacy_single_call_body_rejects",
            "legacy_fanout_body_rejects",
            "legacy_printmath_body_rejects",
            "legacy_string_integer_library_body_rejects",
            "legacy_if_eq_body_rejects",
            "legacy_if_ne_body_rejects",
            "legacy_if_lt_body_rejects",
            "legacy_if_gt_body_rejects",
            "legacy_if_ge_body_rejects",
            "legacy_if_le_body_rejects",
            "legacy_if_else_body_rejects",
            "legacy_nested_if_body_rejects",
            "legacy_nested_if_else_body_rejects",
            "legacy_do_until_eq_body_rejects",
            "legacy_do_until_lt_body_rejects",
            "legacy_nested_do_until_eq_body_rejects",
            "legacy_do_if_until_eq_body_rejects",
            "legacy_do_if_else_until_eq_body_rejects",
            "legacy_if_do_until_eq_body_rejects",
            "legacy_if_else_do_until_eq_body_rejects",
            "legacy_if_local_call_do_until_eq_body_rejects",
        )
        rejection_matrix = self._makefile_shape_group(
            self.make_text,
            "ACTION_ALINK_PRG_OBJECT_CODE_REJECTION_CASES",
        )

        for shape in shapes:
            with self.subTest(shape=shape):
                case = probe.DIRECT_PRG_CASES[shape]
                self.assertTrue(case["expect_alink_failure"])
                self.assertEqual(case["expected_alink_error"], "UNSUPPORTED BODY")
                self.assertIn(shape, rejection_matrix)

    def test_sid_runtime_matrix_covers_sidspr1_sid_split_helpers(self) -> None:
        matrix_groups = self._makefile_runtime_matrix_shape_groups(self.make_text)
        sid_shapes = matrix_groups.get("ACTION_ACTC_ALINK_SID_RUNTIME_SHAPES", set())

        for shape in {
            "actc_runtime_sidspr1_sid_vol_split_linked",
            "actc_runtime_sidspr1_sid_freq_split_linked",
            "actc_runtime_sidspr1_sid_pulse_split_linked",
            "actc_runtime_sidspr1_sid_ad_split_linked",
            "actc_runtime_sidspr1_sid_sr_split_linked",
            "actc_runtime_sidspr1_sid_route_split_linked",
            "actc_runtime_sidspr1_sid_res_split_linked",
            "actc_runtime_sidspr1_sid_cutoff_split_linked",
            "actc_runtime_sidspr1_sid_mode_split_linked",
            "actc_runtime_sidspr1_sid_wave_split_linked",
            "actc_runtime_sidspr1_sid_on_split_linked",
            "actc_runtime_sidspr1_sid_off_split_linked",
            "actc_runtime_sidspr1_sid_rst_split_linked",
            "actc_runtime_sidspr1_sid_osc3_split_linked",
            "actc_runtime_sidspr1_sid_env3_split_linked",
        }:
            self.assertIn(shape, sid_shapes)

    def test_sprite_runtime_matrix_covers_sidspr1_sprite_split_helpers(self) -> None:
        matrix_groups = self._makefile_runtime_matrix_shape_groups(self.make_text)
        sprite_shapes = matrix_groups.get("ACTION_ACTC_ALINK_SPRITE_RUNTIME_SHAPES", set())

        for shape in {
            "actc_runtime_sidspr1_sprite_color_split_linked",
            "actc_runtime_sidspr1_sprite_data_split_linked",
            "actc_runtime_sidspr1_sprite_ptr_split_linked",
            "actc_runtime_sidspr1_sprite_pos_split_linked",
            "actc_runtime_sidspr1_sprite_on_split_linked",
            "actc_runtime_sidspr1_sprite_off_split_linked",
            "actc_runtime_sidspr1_sprite_hit_split_linked",
            "actc_runtime_sidspr1_sprite_hit_bg_split_linked",
            "actc_runtime_sidspr1_sprite_mc_split_linked",
            "actc_runtime_sidspr1_sprite_xexp_split_linked",
            "actc_runtime_sidspr1_sprite_yexp_split_linked",
            "actc_runtime_sidspr1_sprite_prio_split_linked",
            "actc_runtime_sidspr1_sprite_set_mc_split_linked",
        }:
            self.assertIn(shape, sprite_shapes)

    def test_gfx1_demo_target_uses_exported_sample_source(self) -> None:
        self.assertIn(
            "vice-action-actc-alink-launch-gfx1-demo:",
            self.make_text,
            "Missing focused GFX1 exported sample launch target",
        )
        self.assertIn(
            "--shape actc_runtime_gfx1_export_sample_linked --source-from /IMAGES/ACTION.DNP/SRC/GFX1_DEMO.ACT",
            self.make_text,
            "GFX1 demo target must compile the sample exported in the release workspace",
        )

    def test_math1_demo_target_uses_exported_sample_source(self) -> None:
        self.assertIn(
            "vice-action-actc-alink-launch-math1-demo:",
            self.make_text,
            "Missing focused MATH1 exported sample launch target",
        )
        self.assertIn(
            "--shape actc_runtime_math1_export_sample_linked --source-from /IMAGES/ACTION.DNP/SRC/MATH1_DEMO.ACT",
            self.make_text,
            "MATH1 demo target must compile the sample exported in the release workspace",
        )

    def test_sidspr1_demo_target_uses_exported_sample_source(self) -> None:
        self.assertIn(
            "vice-action-actc-alink-launch-sidspr1-demo:",
            self.make_text,
            "Missing focused SIDSPR1 exported sample launch target",
        )
        self.assertIn(
            "--shape actc_runtime_sidspr1_export_sample_linked --source-from /IMAGES/ACTION.DNP/SRC/SIDSPR1_DEMO.ACT",
            self.make_text,
            "SIDSPR1 demo target must compile the sample exported in the release workspace",
        )

    def test_helper_demo_aggregate_runs_all_exported_samples(self) -> None:
        expected_targets = {
            "vice-action-actc-alink-launch-input1-demo",
            "vice-action-actc-alink-launch-dbf1-demo",
            "vice-action-actc-alink-launch-gfx1-demo",
            "vice-action-actc-alink-launch-math1-demo",
            "vice-action-actc-alink-launch-sidspr1-demo",
        }
        body = self._makefile_target_body(
            self.make_text,
            "vice-action-actc-alink-launch-helper-demos",
        )
        aggregate_targets = set(
            re.findall(
                r"\$\(MAKE\)\s+(vice-action-actc-alink-launch-[A-Za-z0-9]+-demo)\b",
                body,
            )
        )

        self.assertTrue(body, "Missing aggregate exported helper demo launch target")
        self.assertEqual(aggregate_targets, expected_targets)

    @staticmethod
    def _makefile_runtime_matrix_shape_groups(make_text: str) -> dict[str, set[str]]:
        groups: dict[str, set[str]] = {}
        current_group: str | None = None

        for line in make_text.splitlines():
            group_match = re.match(r"^(ACTION_ACTC_ALINK_[A-Z_]*RUNTIME_SHAPES)\s*:=", line)
            if group_match:
                current_group = group_match.group(1)
                groups[current_group] = set()

            if current_group is not None:
                groups[current_group].update(re.findall(r"\bactc_runtime_[A-Za-z0-9_]+", line))
                if not line.rstrip().endswith("\\"):
                    current_group = None

        return groups

    @staticmethod
    def _makefile_shape_group(make_text: str, group: str) -> set[str]:
        shapes: set[str] = set()
        active = False

        for line in make_text.splitlines():
            if not active:
                match = re.match(rf"^{re.escape(group)}\s*:=\s*(.*)$", line)
                if match is None:
                    continue
                active = True
                payload = match.group(1)
            else:
                payload = line

            shapes.update(re.findall(r"\b[A-Za-z0-9_]+\b", payload))
            if not line.rstrip().endswith("\\"):
                break

        return shapes

    @staticmethod
    def _makefile_shape_group_lists(make_text: str) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {}
        current_group: str | None = None

        for line in make_text.splitlines():
            if current_group is None:
                match = re.match(r"^([A-Z0-9_]+_SHAPES)\s*:=\s*(.*)$", line)
                if match is None:
                    continue
                current_group = match.group(1)
                groups[current_group] = []
                payload = match.group(2)
            else:
                payload = line

            groups[current_group].extend(re.findall(r"\b[A-Za-z0-9_]+\b", payload))
            if not line.rstrip().endswith("\\"):
                current_group = None

        return groups

    @staticmethod
    def _library_call_names(path: Path) -> set[str]:
        text = path.read_text(encoding="ascii")
        return {
            match.group(1).upper()
            for match in re.finditer(
                r"\b(?:PROC|(?:BYTE|CARD|INT|REAL)\s+FUNC)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
                text,
            )
        }

    @staticmethod
    def _actc_builtin_runtime_map(actc_text: str) -> dict[str, str]:
        builtin_symbols = {
            match.group(1): match.group(2).upper()
            for match in re.finditer(
                r"^(builtin_symbol_[A-Za-z0-9_]+):\n\s*\.asciiz\s+\"([^\"]+)\"",
                actc_text,
                re.MULTILINE,
            )
        }
        runtime_symbols = {
            match.group(1): match.group(2).lower()
            for match in re.finditer(
                r"^(runtime_symbol_[A-Za-z0-9_]+):\n\s*\.asciiz\s+\"([^\"]+)\"",
                actc_text,
                re.MULTILINE,
            )
        }
        runtime_map: dict[str, str] = {}
        for match in re.finditer(
            r"\.byte\s+\$[0-9A-Fa-f]+,\s*"
            r"<(?P<builtin>builtin_symbol_[A-Za-z0-9_]+),\s*>"
            r"(?P=builtin),\s*"
            r"<(?P<runtime>runtime_symbol_[A-Za-z0-9_]+),\s*>"
            r"(?P=runtime)",
            actc_text,
        ):
            builtin_label = match.group("builtin")
            runtime_label = match.group("runtime")
            if builtin_label in builtin_symbols and runtime_label in runtime_symbols:
                runtime_map[builtin_symbols[builtin_label]] = runtime_symbols[runtime_label]
        return runtime_map

    @staticmethod
    def _makefile_target_submakes(make_text: str, target: str) -> set[str]:
        body = TestActcAlinkRuntimeMatrix._makefile_target_body(make_text, target)
        return set(re.findall(r"\$\(MAKE\)\s+(vice-action-actc-alink-launch-\S+)\b", body))

    @staticmethod
    def _makefile_target_body(make_text: str, target: str) -> str:
        target_match = re.search(
            rf"^{re.escape(target)}:[ \t]*(?:[^\n]*)\n((?:\t[^\n]*\n)+)",
            make_text,
            re.MULTILINE,
        )
        if target_match is None:
            return ""
        return target_match.group(1)


if __name__ == "__main__":
    unittest.main()
