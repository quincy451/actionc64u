from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


class TestActcAlinkRuntimeMatrix(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = Path(__file__).resolve().parents[2]
        self.make_text = (self.workspace / "udos" / "Makefile").read_text()

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

    def test_actc_object_emission_launch_matrix_covers_focused_source_shapes(self) -> None:
        sys.path.insert(0, str(self.workspace / "udos" / "tools"))
        import run_action_alink_prg_probe as probe

        expected_shapes = {
            "single_call",
            "fanout",
            "local_chain_mixed_call",
            "local_external_chain_mixed_call",
            "local_external_helper_only_call",
            "local_external_deep_helper_only_call",
            "local_external_helper_mixed_repeat_call",
            "local_external_project_library_helper_closure",
            "local_external_project_imports_actc_secondary_export",
            "local_external_project_imports_actc_secondary_export_local_chain",
            "local_external_library_imports_actc_secondary_export",
            "local_external_library_imports_actc_secondary_export_local_chain",
            "local_external_direct_and_library_imports_actc_tail",
            "local_external_library_project_imports_actc_secondary_export",
            "local_external_library_project_imports_actc_secondary_export_local_chain",
            "local_external_mixed_shared_library_dependency_dedup",
            "local_external_dual_secondary_exports_shared_library_dedup",
            "local_external_dual_secondary_exports_shared_project_dedup",
            "local_external_dual_secondary_exports_shared_actc_local_dedup",
            "local_external_project_library_transitive_shared_tail",
            "local_external_project_library_transitive_project_tail",
            "local_external_project_library_transitive_tail_imports_actc_local_chain",
            "external_project_library_project_library_chain",
            "external_call",
            "local_external_call",
            "local_external_pair_call",
            "local_external_call_twice",
            "local_external_mixed_repeat_call",
            "external_pair_call",
            "external_triple_call",
            "external_lettered_import_call",
            "external_dependency_windowed_lettered_import_call",
            "local_external_project_dependency_windowed_lettered_import_call",
            "local_external_project_dependency_windowed_lettered_mixed_helper_call",
            "external_mixed_repeat_call",
            "external_call_twice",
        }
        matrix_shapes = self._makefile_shape_group(self.make_text, "ACTION_ACTC_ALINK_OBJECT_EMISSION_SHAPES")
        direct_cases = set(probe.DIRECT_PRG_CASES)

        stale = sorted(matrix_shapes - direct_cases)
        missing = sorted(expected_shapes - matrix_shapes)
        non_source = sorted(shape for shape in matrix_shapes if "source" not in probe.DIRECT_PRG_CASES[shape])
        wrong_family = sorted(
            shape
            for shape in matrix_shapes
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

    def test_shipped_link_selected_library_helpers_have_runtime_contract(self) -> None:
        action_root = self.workspace / "actionc64u"
        actc_text = (action_root / "src" / "tools_udos" / "actc" / "actc.asm").read_text(encoding="ascii")
        alink_text = (action_root / "src" / "tools_udos" / "alink" / "direct_prg.inc").read_text(encoding="ascii")
        runtime_modules = {
            path.stem.lower()
            for path in (action_root / "src" / "runtime" / "udos_modules").glob("rt_*.obj")
        }
        actc_runtime_map = self._actc_builtin_runtime_map(actc_text)
        alink_runtime_names = self._alink_runtime_names(alink_text)

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
                "DBFOPEN": "rt_dbf_open",
                "DBFCLOSE": "rt_dbf_close",
                "DBFGO": "rt_dbf_go",
                "DBFFIELDCOUNT": "rt_dbf_fieldcount",
                "DBFFIELDLEN": "rt_dbf_fieldlen",
                "DBFREADBYTE": "rt_dbf_readbyte",
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
                    self.assertIn(runtime_name, alink_runtime_names)

        self.assertEqual(
            self._library_call_names(action_root / "lib" / "math1.act"),
            {"PRINTR", "PRINTRE", "FABS", "FSQRT"},
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
        }:
            self.assertIn(shape, math_shapes)

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
            "actc_runtime_input_mouse_button2_condition_gfx_helper_linked",
            "actc_runtime_input_variable_port_store_linked",
            "actc_runtime_input_dual_port_presence_store_linked",
            "actc_runtime_input_gfx_mixed_helpers_linked",
            "actc_runtime_input_mouse_result_gfx_arg_linked",
            "actc_runtime_input_mouse_result_sid_arg_linked",
            "actc_runtime_input_mouse_result_sprite_second_arg_linked",
            "actc_runtime_input_mouse_x_result_sprite_pos_second_arg_linked",
            "actc_runtime_input_mouse_y_result_sprite_pos_third_arg_linked",
            "actc_runtime_input_mouse_button_result_sid_arg_linked",
            "actc_runtime_input_joystick_result_sid_arg_linked",
            "actc_runtime_input_joystick_result_sid_word_arg_linked",
            "actc_runtime_input_joystick_result_sid_first_arg_linked",
            "actc_runtime_input_joystick_result_sid_freq_second_arg_linked",
            "actc_runtime_input_joystick_result_sid_pulse_second_arg_linked",
            "actc_runtime_input_joystick_result_sprite_second_arg_linked",
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
            "actc_runtime_input_joystick_result_sid_ad_first_arg_linked",
            "actc_runtime_input_joystick_result_sid_ad_second_arg_linked",
            "actc_runtime_input_joystick_result_sid_sr_first_arg_linked",
            "actc_runtime_input_joystick_result_sid_sr_second_arg_linked",
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
                "actc_runtime_dbf1_open_split_linked",
                "actc_runtime_dbf1_close_split_linked",
                "actc_runtime_dbf1_close_state_reset_linked",
                "actc_runtime_dbf1_go_split_linked",
                "actc_runtime_dbf1_field_count_split_linked",
                "actc_runtime_dbf1_field_len_split_linked",
                "actc_runtime_dbf1_read_byte_split_linked",
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
            "actc_runtime_math1_export_sample_linked",
            "actc_runtime_math1_fabs_split_linked",
            "actc_runtime_math1_fsqrt_split_linked",
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
    def _alink_runtime_names(alink_text: str) -> set[str]:
        return {
            match.group(2).lower()
            for match in re.finditer(
                r"^(runtime_name_[A-Za-z0-9_]+):\n\s*\.asciiz\s+\"([^\"]+)\"",
                alink_text,
                re.MULTILINE,
            )
        }

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
