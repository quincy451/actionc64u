from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest


def count_body_ops(body: str) -> int:
    match = re.search(r"^b ([^\n]*)$", body, re.MULTILINE)
    if match is None:
        return 0
    stream = match.group(1)
    count = 0
    index = 0
    while index < len(stream):
        count += 1
        index += 1
        if index < len(stream) and stream[index] in "0123456789ABCDEF":
            index += 1
    return count


def native_word_store_object(var_name: str, initial_value: int, assigned_value: int) -> str:
    return (
        "x main 0 50\n"
        "x __idata 46 2\n"
        "x __iptr 48 2\n"
        "b M\n"
        "b M\n"
        "b M\n"
        "m A2 00 BD 00 00 85 06 E8 BD 00 00 85 07 "
        f"A9 {assigned_value & 0xFF:02X} 48 A9 {(assigned_value >> 8) & 0xFF:02X} 48 "
        "68 AA 68 A0 00 91 06 C8 8A 91 06 "
        "A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF "
        f"{initial_value & 0xFF:02X} {(initial_value >> 8) & 0xFF:02X} 00 00\n"
        "r 3 x __iptr\n"
        "r 9 x __iptr\n"
        "r 48 x __idata\n"
        f"i {assigned_value}\n"
        f"v {var_name.lower()} {initial_value}\n"
        "k 0\n"
        "n main\n"
    )


def native_one_arg_local_call_object_tail() -> str:
    return (
        "x main 0 62\n"
        "x help 38 20\n"
        "x __idata 58 2\n"
        "x __iptr 60 2\n"
        "b M\n"
        "b M\n"
        "b M\n"
        "b M\n"
        "m A2 00 BD 00 00 85 06 E8 BD 00 00 85 07 A9 01 48 A9 00 48 "
        "20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF "
        "68 AA 68 85 04 68 A0 01 91 06 68 88 91 06 A5 04 48 8A 48 "
        "60 00 00 00 00\n"
        "r 3 x __iptr\n"
        "r 9 x __iptr\n"
        "r 20 x help\n"
        "r 60 x __idata\n"
        "i 1\n"
        "v n 0\n"
        "k 0\n"
        "n main\n"
    )


def native_two_arg_local_call_object_tail() -> str:
    return (
        "x main 0 79\n"
        "x help 44 29\n"
        "x __idata 73 4\n"
        "x __iptr 77 2\n"
        "b M\n"
        "b M\n"
        "b M\n"
        "b M\n"
        "m A2 00 BD 00 00 85 06 E8 BD 00 00 85 07 A9 01 48 A9 00 48 "
        "A9 02 48 A9 00 48 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 "
        "A2 02 4C 0F CF 68 AA 68 85 04 68 A0 03 91 06 68 88 91 06 "
        "68 A0 01 91 06 68 88 91 06 A5 04 48 8A 48 60 00 00 00 00 "
        "00 00\n"
        "r 3 x __iptr\n"
        "r 9 x __iptr\n"
        "r 26 x help\n"
        "r 77 x __idata\n"
        "i 1\n"
        "i 2\n"
        "v a 0\n"
        "v b 0\n"
        "k 0\n"
        "n main\n"
    )


class TestActcReuSourceCache(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.build_dir = self.root / "build" / "udos_tools"

    def test_actc_scan_ptr_reads_stay_behind_source_reader_peek(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        common_load_path = self.root / "src" / "tools_udos" / "common" / "action_project_load.inc"
        common_count_path = self.root / "src" / "tools_udos" / "common" / "action_project_count.inc"
        common_entry_path = self.root / "src" / "tools_udos" / "common" / "action_project_entry.inc"
        manifest_scan_path = self.root / "src" / "tools_udos" / "common" / "action_project_manifest_scan.inc"
        offenders: list[str] = []

        for source_path, allowed_scopes in (
            (actc_path, set()),
            (common_load_path, {"source_reader_peek_scan_ptr:", "source_reader_peek_scan_y:"}),
            (common_count_path, set()),
            (common_entry_path, set()),
            (manifest_scan_path, set()),
        ):
            inside_allowed_scope = False
            for line_number, line in enumerate(source_path.read_text(encoding="ascii").splitlines(), 1):
                stripped = line.strip()
                if stripped in allowed_scopes:
                    inside_allowed_scope = True

                if ("lda (scan_ptr),y" in line or "cmp (scan_ptr),y" in line) and not inside_allowed_scope:
                    offenders.append(f"{source_path.relative_to(self.root)}:{line_number}: {stripped}")

                if inside_allowed_scope and stripped in {"rts", ".endmacro"}:
                    inside_allowed_scope = False

        self.assertEqual(offenders, [])

    def test_project_entry_matching_uses_source_reader_peek(self) -> None:
        common_entry_path = self.root / "src" / "tools_udos" / "common" / "action_project_entry.inc"
        common_entry_text = common_entry_path.read_text(encoding="ascii")
        match = re.search(
            r"entry_matches_current_line:\n(?P<body>.*?)\nentry_matches_current_line_ok:",
            common_entry_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_peek_scan_y", body)
        self.assertNotIn("project_reader_lda_scan_y", common_entry_text)
        self.assertNotIn("project_reader_cmp_scan_y", common_entry_text)
        self.assertNotIn("lda (scan_ptr),y", common_entry_text)
        self.assertNotIn("cmp (scan_ptr),y", common_entry_text)

    def test_parser_advances_stay_behind_source_reader_consume(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        offenders: list[str] = []
        inside_consume = False

        for line_number, line in enumerate(actc_path.read_text(encoding="ascii").splitlines(), 1):
            stripped = line.strip()
            if stripped == "source_reader_consume_scan_y:":
                inside_consume = True

            if stripped == "jsr advance_scan_y" and not inside_consume:
                offenders.append(f"{actc_path.relative_to(self.root)}:{line_number}: {stripped}")

            if inside_consume and stripped == "rts":
                inside_consume = False

        self.assertEqual(offenders, [])

    def test_source_reader_match_char_from_scan_y_is_non_consuming(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"source_reader_match_char_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_consume_char_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("sta compare_char", body)
        self.assertIn("jsr source_reader_peek_scan_y", body)
        self.assertIn("cmp compare_char", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_comparison_operator_probes_use_source_reader_match_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        helper_match = re.search(
            r"source_reader_match_comparison_operator_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_match_comparison_suffix_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr source_reader_peek_scan_y", helper_body)
        for expected in ("cmp #'='", "cmp #'<'", "cmp #'>'"):
            self.assertIn(expected, helper_body)
        self.assertNotIn("jsr source_reader_consume_scan_y", helper_body)
        self.assertNotIn("jsr advance_scan_y", helper_body)

        ranges = {
            "scan_value_expr_for_bool_tokens_from_scan_y_loop": (
                "scan_value_expr_for_bool_tokens_from_scan_y_next:",
            ),
        }

        for label, (next_label,) in ranges.items():
            match = re.search(
                rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                actc_text,
                re.DOTALL | re.MULTILINE,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr source_reader_match_comparison_operator_from_scan_y", body, msg=label)
            for forbidden in ("cmp #'='", "cmp #'<'", "cmp #'>'"):
                self.assertNotIn(forbidden, body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

    def test_less_than_suffix_probes_use_source_reader_match_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        helper_match = re.search(
            r"source_reader_match_comparison_suffix_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_match_line_end_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr source_reader_peek_scan_y", helper_body)
        self.assertIn("cmp #'='", helper_body)
        self.assertIn("cmp #'>'", helper_body)
        self.assertNotIn("cmp #'<'", helper_body)
        self.assertNotIn("jsr source_reader_consume_scan_y", helper_body)
        self.assertNotIn("jsr advance_scan_y", helper_body)

        ranges = {
            "preallocate_real_condition_cmp_external_consume_lt": (
                "preallocate_real_condition_cmp_external_consume_gt:",
            ),
            "preallocate_consume_comparison_operator_lt": (
                "preallocate_consume_comparison_operator_gt:",
            ),
            "store_small_runtime_expr_lt_entry": (
                "store_small_runtime_expr_gt_entry:",
            ),
        }

        for label, (next_label,) in ranges.items():
            match = re.search(
                rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                actc_text,
                re.DOTALL | re.MULTILINE,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr source_reader_match_comparison_suffix_from_scan_y", body, msg=label)
            self.assertNotIn("jsr source_reader_peek_scan_y", body, msg=label)
            self.assertNotIn("cmp #'='", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

    def test_line_end_probes_use_source_reader_match_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        helper_match = re.search(
            r"source_reader_match_line_end_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_match_numeric_sum_stop_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr source_reader_peek_scan_y", helper_body)
        self.assertIn("beq source_reader_match_numeric_sum_stop_from_scan_y_match", helper_body)
        self.assertIn("cmp #10", helper_body)
        self.assertIn("cmp #13", helper_body)
        self.assertNotIn("jsr source_reader_consume_scan_y", helper_body)
        self.assertNotIn("jsr advance_scan_y", helper_body)

        ranges = {
            "preallocate_declared_symbol_is_return_statement": (
                "preallocate_declared_symbol_is_return_statement_done:",
            ),
            "preallocate_require_then_or_line_end_at_scan_y": (
                "preallocate_require_then_or_line_end_at_scan_y_fail:",
            ),
            "preallocate_require_do_or_line_end_at_scan_y": (
                "preallocate_require_do_or_line_end_at_scan_y_fail:",
            ),
            "collect_proc_body_ops_try_return": (
                "collect_proc_body_ops_try_return_emit:",
            ),
            "require_line_end_at_scan_y": (
                "require_line_end_at_scan_y_ok:",
            ),
            "require_then_or_line_end_at_scan_y": (
                "require_then_or_line_end_at_scan_y_fail:",
            ),
            "require_do_or_line_end_at_scan_y": (
                "require_do_or_line_end_at_scan_y_fail:",
            ),
            "emit_small_constant_sum_from_scan_y_or_fail": (
                "emit_small_constant_sum_from_scan_y_or_fail_ok:",
            ),
        }

        for label, (next_label,) in ranges.items():
            match = re.search(
                rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                actc_text,
                re.DOTALL | re.MULTILINE,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr source_reader_match_line_end_from_scan_y", body, msg=label)
            self.assertNotIn("jsr source_reader_peek_scan_y", body, msg=label)
            self.assertNotIn("cmp #10", body, msg=label)
            self.assertNotIn("cmp #13", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

    def test_comparison_dispatches_use_source_reader_match_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        ranges = {
            "preallocate_real_condition_cmp_external_from_scan_y": (
                "preallocate_real_condition_cmp_external_compare_entry:",
            ),
            "preallocate_consume_comparison_operator_at_scan_y": (
                "preallocate_consume_comparison_operator_compare_entry:",
            ),
            "store_small_runtime_expr_from_scan_ptr": (
                "store_small_runtime_expr_compare_entry:",
            ),
        }

        for label, (next_label,) in ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr source_reader_match_comparison_operator_from_scan_y", body, msg=label)
            self.assertNotIn("jsr source_reader_peek_scan_y", body, msg=label)
            for forbidden in ("cmp #'='", "cmp #'<'", "cmp #'>'"):
                self.assertNotIn(forbidden, body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

        proven_dispatch_ranges = {
            "preallocate_real_condition_cmp_external_compare_entry": (
                "preallocate_real_condition_cmp_external_consume_single:",
                "bne preallocate_real_condition_cmp_external_consume_gt",
            ),
            "preallocate_consume_comparison_operator_compare_entry": (
                "preallocate_consume_comparison_operator_single:",
                "bne preallocate_consume_comparison_operator_gt",
            ),
            "store_small_runtime_expr_compare_entry": (
                "store_small_runtime_expr_eq:",
                "bne store_small_runtime_expr_gt_entry",
            ),
        }

        for label, (next_label, expected_jump) in proven_dispatch_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn(expected_jump, body, msg=label)
            self.assertNotIn("cmp #'>'", body, msg=label)
            self.assertNotIn("sec", body, msg=label)
            self.assertNotIn("rts", body, msg=label)

    def test_open_paren_probes_use_source_reader_match_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        helper_match = re.search(
            r"source_reader_match_open_paren_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_match_char_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr source_reader_peek_scan_y", helper_body)
        self.assertIn("cmp #'('", helper_body)
        self.assertNotIn("sta compare_char", helper_body)
        self.assertNotIn("jsr source_reader_consume_scan_y", helper_body)
        self.assertNotIn("jsr advance_scan_y", helper_body)

        ranges = {
            "preallocate_call_with_arg_externals_from_scan_y": (
                "preallocate_call_with_arg_externals_fail:",
            ),
            "preallocate_call_name_external_from_scan_y": (
                "preallocate_call_name_external_miss_restore:",
            ),
            "preallocate_call_bool_primary_external_from_scan_y": (
                "preallocate_call_bool_primary_external_group:",
            ),
            "preallocate_real_print_statement_external_from_scan_y": (
                "preallocate_real_print_statement_external_miss:",
            ),
            "preallocate_int_print_statement_call_external_from_scan_y": (
                "preallocate_int_print_statement_call_external_miss_restore:",
            ),
            "collect_proc_body_ops_try_local_call": (
                "collect_proc_body_ops_skip_line:",
            ),
            "emit_real_add_assignment_from_scan_y_or_fail": (
                "emit_real_add_assignment_after_copy_check:",
            ),
            "emit_runtime_value_from_scan_y_or_fail_after_group": (
                "emit_runtime_value_from_scan_y_or_fail_sum:",
            ),
            "parse_small_value_expr_at_scan_y_after_group": (
                "parse_small_value_expr_at_scan_y_sum_entry:",
            ),
            "store_proc_params_from_scan_y_for_current_export_or_fail": (
                "store_proc_params_from_scan_y_for_current_export_loop:",
            ),
        }

        for label, (next_label,) in ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr source_reader_match_open_paren_from_scan_y", body, msg=label)
            self.assertNotIn("cmp #'('", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

    def test_equals_probes_use_source_reader_match_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        ranges = {
            "collect_proc_body_ops_try_local_int_assignment": (
                "collect_proc_body_ops_try_local_int_parse_value:",
            ),
            "collect_proc_body_ops_try_local_real_assignment": (
                "collect_proc_body_ops_try_od:",
            ),
            "collect_proc_body_ops_try_assignment": (
                "collect_proc_body_ops_try_assignment_word:",
            ),
        }

        for label, (next_label,) in ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("lda #'='", body, msg=label)
            self.assertIn("jsr source_reader_match_char_from_scan_y", body, msg=label)
            self.assertNotIn("cmp #'='", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

    def test_greater_equal_suffix_probes_use_source_reader_match_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        ranges = {
            "preallocate_real_condition_cmp_external_consume_gt": (
                "preallocate_real_condition_cmp_external_consume_second:",
            ),
            "preallocate_consume_comparison_operator_gt": (
                "preallocate_consume_comparison_operator_second:",
            ),
            "store_small_runtime_expr_gt_entry": (
                "store_small_runtime_expr_ge:",
            ),
        }

        for label, (next_label,) in ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("lda #'='", body, msg=label)
            self.assertIn("jsr source_reader_match_char_from_scan_y", body, msg=label)
            self.assertNotIn("cmp #'='", body, msg=label)
            self.assertNotIn("jsr source_reader_peek_scan_y", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

    def test_scan_ptr_advances_stay_behind_source_reader_consume(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        common_load_path = self.root / "src" / "tools_udos" / "common" / "action_project_load.inc"
        common_mutate_path = self.root / "src" / "tools_udos" / "common" / "action_project_mutate.inc"
        manifest_scan_path = self.root / "src" / "tools_udos" / "common" / "action_project_manifest_scan.inc"
        self.assertIn(
            "source_reader_consume_scan_ptr:",
            common_load_path.read_text(encoding="ascii"),
        )
        common_load_text = common_load_path.read_text(encoding="ascii")
        consume_match = re.search(
            r"source_reader_consume_scan_ptr:\n(?P<body>.*?)\nadvance_scan_ptr:",
            common_load_text,
            re.DOTALL,
        )
        self.assertIsNotNone(consume_match)
        assert consume_match is not None
        self.assertIn("jsr source_reader_peek_scan_ptr", consume_match.group("body"))
        self.assertIn(
            "source_reader_consume_const_ptr_at_scan_ptr:",
            actc_path.read_text(encoding="ascii"),
        )
        offenders: list[str] = []
        inside_consume = False

        for source_path in (actc_path, common_load_path, common_mutate_path, manifest_scan_path):
            for line_number, line in enumerate(source_path.read_text(encoding="ascii").splitlines(), 1):
                stripped = line.strip()
                if stripped == "source_reader_consume_scan_ptr:":
                    inside_consume = True

                if stripped in {"jsr advance_scan_ptr", "jsr advance_scan_ptr_by_const_ptr"} and not inside_consume:
                    offenders.append(f"{source_path.relative_to(self.root)}:{line_number}: {stripped}")

                if inside_consume and stripped == "rts":
                    inside_consume = False

        self.assertEqual(offenders, [])

    def test_reader_state_mutations_stay_inside_source_reader_helpers(self) -> None:
        actc_dir = self.root / "src" / "tools_udos" / "actc"
        source_paths = [actc_dir / "actc.asm", *sorted(actc_dir.glob("actc_overlay_*.asm"))]
        mutation_re = re.compile(
            r"^\s*(?:sta|stx|sty|stz|inc|dec|asl|lsr|rol|ror)\s+reader_[A-Za-z0-9_]*"
        )
        label_re = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):$")
        allowed_exact_labels = {"save_reader_probe_mark"}
        offenders: list[str] = []

        for source_path in source_paths:
            current_label = ""
            for line_number, line in enumerate(source_path.read_text(encoding="ascii").splitlines(), 1):
                stripped = line.strip()
                label_match = label_re.fullmatch(stripped)
                if label_match:
                    current_label = label_match.group(1)

                if not mutation_re.search(line):
                    continue

                if current_label.startswith("source_reader_") or current_label in allowed_exact_labels:
                    continue

                offenders.append(
                    f"{source_path.relative_to(self.root)}:{line_number}: "
                    f"{stripped} under {current_label}"
                )

        self.assertEqual(offenders, [])

    def test_const_ptr_consume_verifies_fixed_pattern_through_source_reader(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"source_reader_consume_const_ptr_at_scan_ptr:\n"
            r"advance_scan_ptr_by_const_ptr:\n"
            r"(?P<body>.*?)\nuppercase_ascii:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_save_pattern_index_and_begin", body)
        self.assertIn("jsr source_reader_consume_pattern_char_from_scan_ptr", body)
        self.assertIn("bcs source_reader_consume_const_ptr_at_scan_ptr_fail", body)
        self.assertIn("source_reader_consume_const_ptr_at_scan_ptr_fail:", body)
        self.assertIn("jmp source_reader_restore_pattern_index_success", body)
        self.assertIn("jmp source_reader_restore_pattern_index_fail", body)
        self.assertNotIn("sta reader_pattern_index_data", body)
        self.assertNotIn("pha", body)
        self.assertNotIn("pla", body)
        self.assertNotIn("jsr source_reader_consume_scan_ptr", body)
        self.assertLess(
            body.index("source_reader_consume_const_ptr_at_scan_ptr_done:"),
            body.index("source_reader_consume_const_ptr_at_scan_ptr_fail:"),
        )

    def test_common_project_scan_ptr_consumes_are_intentional(self) -> None:
        common_paths = (
            self.root / "src" / "tools_udos" / "common" / "action_project_load.inc",
            self.root / "src" / "tools_udos" / "common" / "action_project_mutate.inc",
            self.root / "src" / "tools_udos" / "common" / "action_project_manifest_scan.inc",
        )
        allowed_prefixes = {
            "source_reader_consume_scan_ptr",
            "project_reader_consume_non_line_end_from_scan_ptr",
            "project_reader_consume_line_break_from_scan_ptr",
            "project_reader_consume_nonzero_from_scan_ptr",
        }
        offenders: list[str] = []

        for source_path in common_paths:
            current_label = ""
            for line_number, line in enumerate(source_path.read_text(encoding="ascii").splitlines(), 1):
                stripped = line.strip()
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*:", stripped):
                    current_label = stripped[:-1]

                allowed = any(
                    current_label == prefix or current_label.startswith(f"{prefix}_")
                    for prefix in allowed_prefixes
                )
                if stripped == "jsr source_reader_consume_scan_ptr" and not allowed:
                    offenders.append(
                        f"{source_path.relative_to(self.root)}:{line_number}: "
                        f"{stripped} under {current_label}"
                    )

        self.assertEqual(offenders, [])

    def test_inline_space_skipping_consumes_through_source_reader(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        self.assertIn("source_reader_consume_scan_y:", actc_text)

        match = re.search(
            r"skip_inline_spaces_at_scan_y:\n(?P<body>.*?)\nadvance_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_consume_inline_space_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", match.group("body"))

        helper_match = re.search(
            r"source_reader_consume_inline_space_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_consume_char_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr source_reader_peek_scan_y", helper_body)
        self.assertIn("cmp #' '", helper_body)
        self.assertIn("cmp #9", helper_body)
        self.assertIn("jsr source_reader_consume_scan_y", helper_body)

    def test_remaining_raw_scan_y_consumes_are_intentional(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        allowed_prefixes = {
            "source_reader_consume_symbol_token_x_from_scan_y",
            "source_reader_consume_decimal_digit_from_scan_y",
            "source_reader_consume_inline_space_from_scan_y",
            "source_reader_consume_plain_call_arg_string_byte_from_scan_y",
            "source_reader_consume_plain_call_arg_scan_byte_from_scan_y",
            "source_reader_consume_flat_call_arg_scan_byte_from_scan_y",
            "source_reader_consume_top_level_arith_scan_byte_from_scan_y",
            "source_reader_consume_bool_keyword_scan_byte_from_scan_y",
            "source_reader_consume_bool_token_scan_byte_from_scan_y",
            "source_reader_consume_char_from_scan_y",
            "source_reader_consume_uppercase_char_from_scan_y",
            "source_reader_consume_pattern_char_from_scan_y",
            "source_reader_peek_token_from_scan_y",
            "source_reader_scan_symbol_lookahead",
            "source_reader_scan_decimal_lookahead",
            "source_reader_scan_hex_lookahead",
            "source_reader_scan_binary_lookahead",
            "source_reader_consume_token_from_scan_y",
        }
        current_label = ""
        offenders: list[str] = []

        for line_number, line in enumerate(actc_path.read_text(encoding="ascii").splitlines(), 1):
            stripped = line.strip()
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*:", stripped):
                current_label = stripped[:-1]

            allowed = any(
                current_label == prefix or current_label.startswith(f"{prefix}_")
                for prefix in allowed_prefixes
            )
            if stripped == "jsr source_reader_consume_scan_y" and not allowed:
                offenders.append(
                    f"{actc_path.relative_to(self.root)}:{line_number}: "
                    f"{stripped} under {current_label}"
                )

        self.assertEqual(offenders, [])

    def test_remaining_raw_scan_ptr_consumes_are_intentional(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        allowed_prefixes = {
            "source_reader_consume_whitespace_from_scan_ptr",
            "source_reader_consume_inline_space_from_scan_ptr",
            "source_reader_consume_line_break_from_scan_ptr",
            "source_reader_consume_non_line_end_from_scan_ptr",
            "source_reader_consume_search_byte_from_scan_ptr",
            "source_reader_try_store_string_literal_byte_from_scan_ptr",
            "source_reader_finish_string_literal_from_scan_ptr",
            "source_reader_consume_pattern_char_from_scan_ptr",
        }
        current_label = ""
        offenders: list[str] = []

        for line_number, line in enumerate(actc_path.read_text(encoding="ascii").splitlines(), 1):
            stripped = line.strip()
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*:", stripped):
                current_label = stripped[:-1]

            allowed = any(
                current_label == prefix or current_label.startswith(f"{prefix}_")
                for prefix in allowed_prefixes
            )
            if stripped == "jsr source_reader_consume_scan_ptr" and not allowed:
                offenders.append(
                    f"{actc_path.relative_to(self.root)}:{line_number}: "
                    f"{stripped} under {current_label}"
                )

        self.assertEqual(offenders, [])

    def test_line_skipping_consumes_through_source_reader(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        common_load_path = self.root / "src" / "tools_udos" / "common" / "action_project_load.inc"
        common_load_text = common_load_path.read_text(encoding="ascii")
        helper_ranges = (
            (
                actc_text,
                "skip_source_line",
                ".if ACTC_KEEP_DECL_RESIDENT_FALLBACK",
                "advance_scan_ptr",
                "jsr source_reader_peek_scan_y",
                "jsr source_reader_consume_non_line_end_from_scan_ptr",
            ),
            (
                common_load_text,
                "skip_current_line",
                "skip_line_breaks:",
                "advance_scan_ptr",
                "jsr source_reader_peek_scan_ptr",
                "jsr project_reader_consume_non_line_end_from_scan_ptr",
            ),
            (
                common_load_text,
                "skip_line_breaks",
                "source_reader_peek_scan_ptr:",
                "advance_scan_ptr",
                "jsr source_reader_peek_scan_ptr",
                "jsr project_reader_consume_line_break_from_scan_ptr",
            ),
        )

        for text, label, next_label, raw_advance, expected_peek, expected_consume in helper_ranges:
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn(expected_peek, body, msg=label)
            self.assertIn(expected_consume, body, msg=label)
            self.assertNotIn(f"jsr {raw_advance}", body, msg=label)

    def test_common_project_manifest_scanners_consume_through_helpers(self) -> None:
        common_load_path = self.root / "src" / "tools_udos" / "common" / "action_project_load.inc"
        common_mutate_path = self.root / "src" / "tools_udos" / "common" / "action_project_mutate.inc"
        manifest_scan_path = self.root / "src" / "tools_udos" / "common" / "action_project_manifest_scan.inc"
        common_load_text = common_load_path.read_text(encoding="ascii")
        common_mutate_text = common_mutate_path.read_text(encoding="ascii")
        manifest_scan_text = manifest_scan_path.read_text(encoding="ascii")

        helper_ranges = {
            "project_reader_consume_non_line_end_from_scan_ptr": (
                "project_reader_consume_line_break_from_scan_ptr:",
                ("cmp #13", "cmp #10", "jsr source_reader_consume_scan_ptr"),
            ),
            "project_reader_consume_line_break_from_scan_ptr": (
                "project_reader_consume_manifest_line_byte_from_scan_ptr:",
                ("cmp #13", "cmp #10", "jsr source_reader_consume_scan_ptr"),
            ),
            "project_reader_consume_manifest_line_byte_from_scan_ptr": (
                "project_reader_consume_nonzero_from_scan_ptr:",
                ("jmp project_reader_consume_non_line_end_from_scan_ptr",),
            ),
            "project_reader_consume_nonzero_from_scan_ptr": (
                "project_reader_consume_manifest_shift_byte_from_scan_ptr:",
                ("beq project_reader_consume_nonzero_from_scan_ptr_fail", "jsr source_reader_consume_scan_ptr"),
            ),
            "project_reader_consume_manifest_shift_byte_from_scan_ptr": (
                "source_reader_peek_scan_ptr:",
                ("jmp project_reader_consume_nonzero_from_scan_ptr",),
            ),
        }

        for label, (next_label, expected_lines) in helper_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                common_load_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            if label in {
                "project_reader_consume_manifest_line_byte_from_scan_ptr",
                "project_reader_consume_manifest_shift_byte_from_scan_ptr",
            }:
                self.assertNotIn("jsr source_reader_consume_scan_ptr", body, msg=label)
            else:
                self.assertIn("jsr source_reader_peek_scan_ptr", body, msg=label)
            for expected in expected_lines:
                self.assertIn(expected, body, msg=label)
            self.assertNotIn("jsr advance_scan_ptr", body, msg=label)

        copy_match = re.search(
            r"copy_manifest_line_to_buffer_loop:\n(?P<body>.*?)\ncopy_manifest_line_to_buffer_done:",
            manifest_scan_text,
            re.DOTALL,
        )
        self.assertIsNotNone(copy_match)
        assert copy_match is not None
        copy_body = copy_match.group("body")
        self.assertIn("jsr project_reader_consume_manifest_line_byte_from_scan_ptr", copy_body)
        self.assertNotIn("jsr source_reader_consume_scan_ptr", copy_body)

        shift_match = re.search(
            r"remove_manifest_shift_loop:\n(?P<body>.*?)\nremove_manifest_done:",
            common_mutate_text,
            re.DOTALL,
        )
        self.assertIsNotNone(shift_match)
        assert shift_match is not None
        shift_body = shift_match.group("body")
        self.assertIn("jsr project_reader_consume_manifest_shift_byte_from_scan_ptr", shift_body)
        self.assertNotIn("jsr source_reader_consume_scan_ptr", shift_body)

    def test_token_helpers_consume_through_source_reader(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        helper_ranges = {
            "copy_symbol_from_scan_y": "consume_and_keyword_from_scan_y:",
            "scan_keyword_token_from_scan_y": "consume_keyword_open_from_scan_y:",
            "consume_keyword_open_from_scan_y": "consume_keyword_from_scan_y:",
        }

        for label, next_label in helper_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{next_label}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            if label == "scan_keyword_token_from_scan_y":
                self.assertIn("jsr source_reader_consume_pattern_char_from_scan_y", body, msg=label)
            elif label == "copy_symbol_from_scan_y":
                self.assertIn("jsr source_reader_try_store_symbol_token_x_from_scan_y", body, msg=label)
            else:
                self.assertIn("jsr source_reader_consume_keyword_token_from_scan_y", body, msg=label)
                self.assertIn("lda #'('", body, msg=label)
                self.assertIn("jsr source_reader_consume_expected_token_from_scan_y", body, msg=label)
                self.assertNotIn("jsr source_reader_consume_pattern_char_from_scan_y", body, msg=label)
                self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
                self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", match.group("body"), msg=label)

        keyword_match = re.search(
            r"source_reader_consume_keyword_token_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_consume_keyword_token_from_scan_y_fail:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(keyword_match)
        assert keyword_match is not None
        keyword_body = keyword_match.group("body")
        self.assertIn("jsr source_reader_peek_token_from_scan_y", keyword_body)
        self.assertIn("cmp #SOURCE_TOKEN_SYMBOL", keyword_body)
        self.assertIn("jsr source_reader_token_buffer_matches_const_ptr", keyword_body)
        self.assertIn("jsr source_reader_consume_token_from_scan_y", keyword_body)
        self.assertNotIn("jsr source_reader_consume_pattern_char_from_scan_y", keyword_body)
        self.assertNotIn("jsr source_reader_consume_scan_y", keyword_body)

    def test_keyword_pattern_char_matching_uses_source_reader_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        begin_match = re.search(
            r"source_reader_begin_pattern:\n(?P<body>.*?)\n"
            r"source_reader_consume_pattern_char_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(begin_match)
        assert begin_match is not None
        begin_body = begin_match.group("body")
        self.assertIn("sta reader_pattern_index_data", begin_body)
        begin_helper_ranges = {
            "source_reader_save_pattern_index_and_begin": (
                "source_reader_restore_pattern_index_success:",
                [
                    "lda reader_pattern_index_data",
                    "sta reader_saved_pattern_index_data",
                    "jmp source_reader_begin_pattern",
                ],
            ),
            "source_reader_restore_pattern_index_success": (
                "source_reader_restore_pattern_index_fail:",
                ["lda reader_saved_pattern_index_data", "sta reader_pattern_index_data", "clc"],
            ),
            "source_reader_restore_pattern_index_fail": (
                "source_reader_begin_pattern_from_scan_y:",
                ["lda reader_saved_pattern_index_data", "sta reader_pattern_index_data", "sec"],
            ),
            "source_reader_begin_pattern_from_scan_y": (
                "source_reader_begin_keyword_probe_from_scan_y:",
                ["sty reader_scan_y_data", "jmp source_reader_begin_pattern"],
            ),
            "source_reader_begin_keyword_probe_from_scan_y": (
                "source_reader_consume_pattern_char_from_scan_y:",
                [
                    "stx reader_saved_x_data",
                    "sty reader_start_y_data",
                    "jsr save_reader_probe_mark",
                    "jmp source_reader_begin_pattern_from_scan_y",
                ],
            ),
        }
        for label, (next_label, expected_lines) in begin_helper_ranges.items():
            helper_match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(helper_match, msg=label)
            assert helper_match is not None
            helper_body = helper_match.group("body")
            for expected in expected_lines:
                self.assertIn(expected, helper_body, msg=label)

        helper_ranges = {
            "source_reader_consume_pattern_char_from_scan_y": (
                "source_reader_consume_pattern_char_from_scan_ptr:",
                "source_reader_peek_scan_y",
                "source_reader_consume_scan_y",
                "sty reader_scan_y_data",
            ),
            "source_reader_consume_pattern_char_from_scan_ptr": (
                "source_reader_peek_keyword_delimiter_from_scan_ptr:",
                "source_reader_peek_scan_ptr",
                "source_reader_consume_scan_ptr",
                None,
            ),
        }

        for label, (next_label, peek_helper, consume_helper, extra_expected) in helper_ranges.items():
            helper_match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(helper_match, msg=label)
            assert helper_match is not None
            helper_body = helper_match.group("body")
            self.assertIn(f"jsr {peek_helper}", helper_body, msg=label)
            self.assertIn(f"jsr {consume_helper}", helper_body, msg=label)
            self.assertIn("inc reader_pattern_index_data", helper_body, msg=label)
            if extra_expected is not None:
                self.assertIn(extra_expected, helper_body, msg=label)

        caller_ranges = {
            "scan_keyword_token_from_scan_y": "consume_keyword_open_from_scan_y:",
            "pattern_matches_scan_ptr_slow": "pattern_matches_scan_ptr_slow_fail:",
            "pattern_matches_scan_ptr_keyword_slow": "pattern_matches_scan_ptr_keyword_slow_boundary:",
        }
        for label, next_label in caller_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{next_label}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            if label == "scan_keyword_token_from_scan_y":
                self.assertIn("jsr source_reader_begin_keyword_probe_from_scan_y", body, msg=label)
                self.assertNotIn("stx reader_saved_x_data", body, msg=label)
                self.assertNotIn("sty reader_start_y_data", body, msg=label)
                self.assertNotIn("sty reader_scan_y_data", body, msg=label)
                self.assertNotIn("jsr save_reader_probe_mark", body, msg=label)
                self.assertNotIn("jsr source_reader_begin_pattern\n", body, msg=label)
            else:
                self.assertIn("jsr source_reader_begin_pattern", body, msg=label)
            self.assertNotIn("sta reader_pattern_index_data", body, msg=label)
            if label.endswith("_slow"):
                self.assertIn("jsr source_reader_consume_pattern_char_from_scan_ptr", body, msg=label)
                self.assertNotIn("jsr source_reader_peek_scan_ptr", body, msg=label)
                self.assertNotIn("jsr source_reader_consume_scan_ptr", body, msg=label)
            else:
                self.assertIn("jsr source_reader_consume_pattern_char_from_scan_y", body, msg=label)
            self.assertNotIn("cmp compare_char", body, msg=label)

    def test_keyword_delimiter_matching_uses_source_reader_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        helper_ranges = {
            "source_reader_peek_keyword_delimiter_from_scan_ptr": (
                "source_reader_peek_keyword_delimiter_from_scan_y:",
                "jsr source_reader_peek_scan_ptr",
            ),
            "source_reader_peek_keyword_delimiter_from_scan_y": (
                "source_reader_keyword_delimiter_from_a:",
                "jsr source_reader_peek_scan_y",
            ),
            "source_reader_keyword_delimiter_from_a": (
                "source_reader_peek_keyword_token_boundary_from_scan_y:",
                "source_reader_keyword_delimiter_from_a_ok",
            ),
            "source_reader_peek_keyword_token_boundary_from_scan_y": (
                "scan_keyword_token_from_scan_y:",
                "jsr uppercase_symbol_body_valid",
            ),
        }

        for label, (next_label, expected) in helper_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            self.assertIn(expected, match.group("body"), msg=label)

        caller_ranges = {
            "pattern_matches_scan_ptr_keyword_boundary": (
                "pattern_matches_scan_ptr_keyword_ok:",
                "jsr source_reader_keyword_delimiter_from_a",
            ),
            "pattern_matches_scan_ptr_keyword_slow_boundary": (
                "pattern_matches_scan_ptr_keyword_slow_fail:",
                "jsr source_reader_peek_keyword_delimiter_from_scan_ptr",
            ),
        }
        for label, (next_label, expected) in caller_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{next_label}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn(expected, body, msg=label)
            self.assertNotIn("cmp #' '", body, msg=label)
            self.assertNotIn("cmp #9", body, msg=label)
            self.assertNotIn("cmp #10", body, msg=label)
            self.assertNotIn("cmp #13", body, msg=label)

    def test_keyword_token_boundary_uses_source_reader_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        helper_match = re.search(
            r"source_reader_peek_keyword_token_boundary_from_scan_y:\n(?P<body>.*?)\nscan_keyword_token_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr source_reader_peek_scan_y", helper_body)
        self.assertIn("jsr uppercase_ascii", helper_body)
        self.assertIn("jsr uppercase_symbol_body_valid", helper_body)

        caller_match = re.search(
            r"scan_keyword_token_from_scan_y_delimiter:\n(?P<body>.*?)\nconsume_keyword_open_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(caller_match)
        assert caller_match is not None
        caller_body = caller_match.group("body")
        self.assertIn("jsr source_reader_peek_keyword_token_boundary_from_scan_y", caller_body)
        self.assertNotIn("jsr uppercase_symbol_body_valid", caller_body)

    def test_small_decimal_parser_consumes_complete_source_reader_token(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"parse_small_decimal_at_scan_y:\n(?P<body>.*?)\n"
            r"parse_plain_word_literal_at_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_peek_token_from_scan_y", body)
        self.assertIn("cmp #SOURCE_TOKEN_DECIMAL", body)
        self.assertIn("lda reader_lookahead_value_hi_data", body)
        self.assertIn("lda reader_lookahead_value_lo_data", body)
        self.assertIn("jsr source_reader_consume_token_from_scan_y", body)
        self.assertNotIn("source_reader_peek_decimal_digit_value_from_scan_y", body)
        self.assertNotIn("source_reader_consume_decimal_digit_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_plain_word_literal_parser_consumes_complete_source_reader_token(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"parse_plain_word_literal_at_scan_y:\n(?P<body>.*?)\n"
            r"parse_positive_word_sum_at_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_peek_token_from_scan_y", body)
        self.assertIn("cmp #SOURCE_TOKEN_DECIMAL", body)
        self.assertIn("lda reader_lookahead_value_lo_data", body)
        self.assertIn("lda reader_lookahead_value_hi_data", body)
        self.assertIn("jsr source_reader_consume_token_from_scan_y", body)
        self.assertNotIn("source_reader_peek_decimal_digit_value_from_scan_y", body)
        self.assertNotIn("source_reader_consume_decimal_digit_from_scan_y", body)
        self.assertNotIn("cmp #'0'", body)
        self.assertNotIn("cmp #'9'+1", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

        peek_helper_match = re.search(
            r"source_reader_peek_decimal_digit_value_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_consume_decimal_digit_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(peek_helper_match)
        assert peek_helper_match is not None
        peek_helper_body = peek_helper_match.group("body")
        self.assertIn("jsr source_reader_peek_scan_y", peek_helper_body)
        self.assertIn("cmp #'0'", peek_helper_body)
        self.assertIn("cmp #'9'+1", peek_helper_body)
        self.assertIn("sbc #'0'", peek_helper_body)
        self.assertNotIn("jsr source_reader_consume_scan_y", peek_helper_body)

        helper_match = re.search(
            r"source_reader_consume_decimal_digit_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_consume_char_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr source_reader_peek_decimal_digit_value_from_scan_y", helper_body)
        self.assertIn("jsr source_reader_consume_scan_y", helper_body)

    def test_positive_word_reader_caches_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        abi_text = (
            self.root / "src" / "tools_udos" / "actc" / "actc_overlay_abi.inc"
        ).read_text(encoding="ascii")

        cache_match = re.search(
            r"source_reader_token_cache_matches_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_store_token_cache_key_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(cache_match)
        assert cache_match is not None
        cache_body = cache_match.group("body")
        for state in (
            "reader_lookahead_y_data",
            "reader_lookahead_scan_ptr_lo_data",
            "reader_lookahead_scan_ptr_hi_data",
            "reader_lookahead_window_next_data",
        ):
            self.assertIn(state, cache_body)

        peek_match = re.search(
            r"source_reader_peek_token_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_scan_symbol_lookahead:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(peek_match)
        assert peek_match is not None
        peek_body = peek_match.group("body")
        for token in (
            "SOURCE_TOKEN_EOF",
            "SOURCE_TOKEN_LINE_END",
            "SOURCE_TOKEN_DECIMAL",
            "SOURCE_TOKEN_SYMBOL",
            "SOURCE_TOKEN_EQ",
            "SOURCE_TOKEN_LT",
            "SOURCE_TOKEN_GT",
            "SOURCE_TOKEN_LE",
            "SOURCE_TOKEN_GE",
            "SOURCE_TOKEN_NE",
        ):
            self.assertIn(token, abi_text)
        self.assertIn("jsr source_reader_token_cache_matches_scan_y", peek_body)
        self.assertIn("jsr save_reader_probe_mark", peek_body)
        self.assertIn("jsr restore_reader_probe_mark", peek_body)

        for label, next_label in (
            ("source_reader_scan_symbol_lookahead", "source_reader_scan_decimal_lookahead:"),
            ("source_reader_scan_decimal_lookahead", "source_reader_accumulate_decimal_lookahead:"),
        ):
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr save_reader_probe_mark", body, msg=label)
            self.assertIn("jsr restore_reader_probe_mark", body, msg=label)
            self.assertIn("jsr source_reader_consume_scan_y", body, msg=label)

        positive_decimal = re.search(
            r"parse_positive_word_decimal_at_scan_y:\n(?P<body>.*?)\n"
            r"parse_positive_word_decimal_at_scan_y_fail:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(positive_decimal)
        assert positive_decimal is not None
        decimal_body = positive_decimal.group("body")
        self.assertIn("reader_lookahead_value_lo_data", decimal_body)
        self.assertIn("reader_lookahead_value_hi_data", decimal_body)
        self.assertIn("jsr source_reader_consume_token_from_scan_y", decimal_body)
        self.assertNotIn("source_reader_peek_decimal_digit_value_from_scan_y", decimal_body)

    def test_var_lookup_probe_restores_source_reader_on_miss(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"find_var_index_from_scan_y:\n(?P<body>.*?)\nfind_export_index_from_declared:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr save_reader_probe_mark", body)
        self.assertIn("find_var_index_from_scan_y_fail_restore:", body)
        self.assertIn("jsr restore_reader_probe_mark", body)
        self.assertLess(
            body.index("jsr restore_reader_probe_mark"),
            body.index("sec"),
            msg=body,
        )

    def test_fixed_pattern_helpers_probe_through_source_reader(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        helper_ranges = {
            "pattern_matches_scan_ptr": "pattern_matches_scan_ptr_keyword:",
            "pattern_matches_scan_ptr_keyword": "match_scalar_decl_at_scan_ptr:",
        }

        for label, next_label in helper_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{next_label}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn(f"{label}_slow:", body, msg=label)
            self.assertIn("jsr save_reader_probe_mark", body, msg=label)
            self.assertIn("jsr source_reader_consume_pattern_char_from_scan_ptr", body, msg=label)
            self.assertIn("jsr restore_reader_probe_mark", body, msg=label)

    def test_string_literal_helper_consumes_token_through_source_reader(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"store_string_literal_from_scan_ptr:\n(?P<body>.*?)\nstore_small_decimal_literal_from_scan_ptr:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_begin_string_literal_from_scan_ptr", body)
        self.assertIn("jsr source_reader_try_store_string_literal_byte_from_scan_ptr", body)
        self.assertIn("jsr source_reader_finish_string_literal_from_scan_ptr", body)
        begin_match = re.search(
            r"source_reader_begin_string_literal_from_scan_ptr:\n(?P<body>.*?)\n"
            r"store_string_literal_from_scan_ptr:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(begin_match)
        assert begin_match is not None
        begin_body = begin_match.group("body")
        self.assertIn("sta reader_token_ptr_lo_data", begin_body)
        self.assertIn("sta reader_token_ptr_hi_data", begin_body)
        self.assertIn("sta reader_pattern_index_data", begin_body)
        caller_match = re.search(
            r"store_string_literal_from_scan_ptr:\n(?P<body>.*?)\n"
            r"source_reader_try_store_string_literal_byte_from_scan_ptr:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(caller_match)
        assert caller_match is not None
        caller_body = caller_match.group("body")
        self.assertNotIn("sta (body_ptr),y", caller_body)
        self.assertNotIn("jsr source_reader_consume_scan_ptr", caller_body)
        self.assertNotIn("sta reader_token_ptr_lo_data", caller_body)
        self.assertNotIn("sta reader_token_ptr_hi_data", caller_body)
        self.assertNotIn("sta reader_pattern_index_data", caller_body)
        loop_match = re.search(
            r"store_string_literal_from_scan_ptr_loop:\n(?P<body>.*?)\n"
            r"store_string_literal_from_scan_ptr_fail:",
            body,
            re.DOTALL,
        )
        self.assertIsNotNone(loop_match)
        assert loop_match is not None
        loop_body = loop_match.group("body")
        self.assertNotIn("jsr source_reader_peek_scan_ptr", loop_body)
        self.assertNotIn("jsr source_reader_consume_scan_ptr", loop_body)

        helper_match = re.search(
            r"source_reader_try_store_string_literal_byte_from_scan_ptr:\n(?P<body>.*?)\n"
            r"source_reader_finish_string_literal_from_scan_ptr:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr source_reader_peek_scan_ptr", helper_body)
        self.assertIn("jsr source_reader_consume_scan_ptr", helper_body)
        self.assertIn("reader_token_ptr_lo_data", helper_body)
        self.assertIn("reader_token_ptr_hi_data", helper_body)
        self.assertIn("inc reader_pattern_index_data", helper_body)
        self.assertIn("lda #$01", helper_body)
        self.assertIn("lda #$ff", helper_body)
        self.assertNotIn("jsr source_reader_peek_scan_y", body)

        finish_match = re.search(
            r"source_reader_finish_string_literal_from_scan_ptr:\n(?P<body>.*?)\n"
            r"store_small_decimal_literal_from_scan_ptr:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(finish_match)
        assert finish_match is not None
        finish_body = finish_match.group("body")
        self.assertIn("ldy reader_pattern_index_data", finish_body)
        self.assertIn("sta (body_ptr),y", finish_body)
        self.assertIn("jsr source_reader_consume_scan_ptr", finish_body)
        self.assertIn("reader_token_ptr_lo_data", finish_body)
        self.assertIn("reader_token_ptr_hi_data", finish_body)

    def test_stream_output_buffer_covers_tiny_source_window_builds(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"source_buffer:\n(?P<body>.*?)\n; Reuse the source window storage for path assembly\.",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("(SOURCE_READ_LIMIT + 1) > OUTPUT_CHUNK_SIZE", body)
        self.assertIn("(SOURCE_LIMIT + 1) > OUTPUT_CHUNK_SIZE", body)
        self.assertIn(".res OUTPUT_CHUNK_SIZE", body)

    def test_overlay_builds_keep_resident_source_below_scratch(self) -> None:
        build_text = (
            self.root / "tools" / "build_actc_reu_cache_harness_udos.sh"
        ).read_text(encoding="ascii")
        actc_text = (
            self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        ).read_text(encoding="ascii")

        self.assertIn('ACTC_SOURCE_WINDOW="${ACTC_SOURCE_WINDOW:-1280}"', build_text)
        self.assertIn(
            '.assert bss_end <= ACTC_OVERLAY_SCRATCH_BASE, lderror, '
            '"ACTC resident image overlaps overlay scratch"',
            actc_text,
        )

    def test_symbol_helper_stores_token_through_stable_destination(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"copy_symbol_from_scan_y:\n(?P<body>.*?)\nconsume_and_keyword_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        caller_body = body.split("copy_symbol_from_scan_y_loop:", 1)[0]
        self.assertIn("jsr source_reader_begin_symbol_token_from_scan_y", caller_body)
        self.assertNotIn("sty reader_scan_y_data", caller_body)
        self.assertNotIn("jsr source_reader_begin_symbol_token\n", caller_body)
        self.assertIn("reader_token_buffer", body)
        self.assertIn("jsr source_reader_try_store_symbol_token_x_from_scan_y", body)
        self.assertIn("jsr source_reader_terminate_symbol_token_x", body)
        self.assertNotIn("sta (body_ptr),y", body)
        self.assertIn("jsr source_reader_publish_symbol_token", body)
        self.assertNotIn("sta declared_module_name,x", body)

        helper_match = re.search(
            r"source_reader_try_store_symbol_token_x_from_scan_y:\n(?P<body>.*?)\n"
            r"copy_symbol_from_scan_ptr:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr source_reader_peek_scan_y", helper_body)
        self.assertIn("jsr source_reader_symbol_token_char_valid_x", helper_body)
        self.assertIn("jsr source_reader_consume_symbol_token_x_from_scan_y", helper_body)
        self.assertIn("jsr source_reader_begin_symbol_token", helper_body)
        self.assertNotIn("jsr source_reader_consume_scan_y", helper_body)
        self.assertNotIn("sty reader_scan_y_data", helper_body)

        consume_helper_match = re.search(
            r"source_reader_consume_symbol_token_x_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_try_store_symbol_token_x_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(consume_helper_match)
        assert consume_helper_match is not None
        consume_helper_body = consume_helper_match.group("body")
        self.assertIn("jsr source_reader_store_symbol_token_x", consume_helper_body)
        self.assertIn("jsr source_reader_consume_scan_y", consume_helper_body)
        self.assertIn("sty reader_scan_y_data", consume_helper_body)

    def test_symbol_token_helpers_centralize_compatibility_publishing(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        helper_ranges = {
            "source_reader_begin_symbol_token_from_scan_y": (
                "source_reader_begin_symbol_token_from_scan_ptr:",
                ["sty reader_scan_y_data", "jmp source_reader_begin_symbol_token"],
            ),
            "source_reader_begin_symbol_token_from_scan_ptr": (
                "source_reader_begin_symbol_token:",
                ["lda #$00", "sta reader_scan_y_data", "jmp source_reader_begin_symbol_token"],
            ),
            "source_reader_begin_symbol_token": (
                "source_reader_store_symbol_token_y:",
                ["lda #<reader_token_buffer", "sta body_ptr", "lda #>reader_token_buffer", "sta body_ptr+1"],
            ),
            "source_reader_store_symbol_token_y": (
                "source_reader_store_symbol_token_x:",
                ["sta reader_token_buffer,y"],
            ),
            "source_reader_store_symbol_token_x": (
                "source_reader_terminate_symbol_token_y:",
                ["sta compare_char", "sta reader_token_buffer,y"],
            ),
            "source_reader_terminate_symbol_token_y": (
                "source_reader_terminate_symbol_token_x:",
                ["lda #$00", "sta reader_token_buffer,y"],
            ),
            "source_reader_terminate_symbol_token_x": (
                "source_reader_finish_proc_export_token_y:",
                ["lda #$00", "sta reader_token_buffer,y"],
            ),
            "source_reader_finish_proc_export_token_y": (
                "source_reader_publish_symbol_token:",
                [
                    "sty reader_scan_y_data",
                    "jsr source_reader_terminate_symbol_token_y",
                    "jmp source_reader_publish_symbol_token_to_export_ptr",
                ],
            ),
            "source_reader_publish_symbol_token": (
                "source_reader_publish_symbol_token_to_export_ptr:",
                ["lda reader_token_buffer,y", "sta declared_module_name,y"],
            ),
            "source_reader_publish_symbol_token_to_export_ptr": (
                "consume_and_keyword_from_scan_y:",
                ["lda reader_token_buffer,y", "sta (export_ptr),y"],
            ),
        }

        for label, (next_label, expected_lines) in helper_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            for expected in expected_lines:
                self.assertIn(expected, body, msg=label)
            if "publish" not in label:
                self.assertNotIn("sta declared_module_name", body, msg=label)
                self.assertNotIn("sta (export_ptr),y", body, msg=label)

    def test_proc_export_name_stages_through_source_reader_token_buffer(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"store_proc_export_from_scan_ptr_or_fail:\n(?P<body>.*?)\n"
            r"store_proc_params_from_scan_y_for_current_export_or_fail:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_begin_symbol_token", body)
        self.assertIn("jsr source_reader_try_store_proc_export_token_y", body)
        self.assertIn("jsr source_reader_finish_proc_export_token_y", body)
        self.assertNotIn("jsr source_reader_terminate_symbol_token_y", body)
        self.assertNotIn("jsr source_reader_publish_symbol_token_to_export_ptr", body)
        self.assertNotIn("sty reader_scan_y_data", body)
        self.assertRegex(
            body,
            r"(?s)jsr source_reader_finish_proc_export_token_y.*"
            r"jsr store_export_name_to_reu_x.*"
            r"ldy reader_scan_y_data.*"
            r"jsr store_proc_params_from_scan_y_for_current_export_or_fail",
        )

        loop_match = re.search(
            r"store_proc_export_from_scan_ptr_or_fail_loop:\n(?P<body>.*?)\n"
            r"store_proc_export_from_scan_ptr_or_fail_bad:",
            body,
            re.DOTALL,
        )
        self.assertIsNotNone(loop_match)
        assert loop_match is not None
        loop_body = loop_match.group("body")
        self.assertIn("jsr source_reader_try_store_proc_export_token_y", loop_body)
        self.assertNotIn("sta (export_ptr),y", loop_body)
        self.assertNotIn("jsr source_reader_store_symbol_token_y", loop_body)

        helper_match = re.search(
            r"source_reader_try_store_proc_export_token_y:\n(?P<body>.*?)\n"
            r"source_reader_consume_symbol_token_x_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr source_reader_peek_scan_y", helper_body)
        self.assertIn("jsr source_reader_symbol_token_char_valid_y", helper_body)
        self.assertIn("jsr source_reader_store_symbol_token_y", helper_body)
        self.assertIn("iny", helper_body)
        self.assertNotIn("jsr source_reader_consume_scan_y", helper_body)

        publish_match = re.search(
            r"source_reader_publish_symbol_token_to_export_ptr:\n(?P<body>.*?)\n"
            r"consume_and_keyword_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(publish_match)
        assert publish_match is not None
        publish_body = publish_match.group("body")
        self.assertIn("reader_token_buffer", publish_body)
        self.assertIn("sta (export_ptr),y", publish_body)

    def test_proc_param_punctuation_uses_expected_char_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"store_proc_params_from_scan_y_for_current_export_or_fail:\n(?P<body>.*?)\n"
            r"\.endif\n\nset_export_ptr_from_x:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        for expected in ("lda #'('", "lda #','", "lda #')'"):
            self.assertIn(expected, body)
        self.assertIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("cmp #','", body)
        self.assertNotIn("cmp #')'", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_symbol_token_classification_uses_source_reader_helpers(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        helper_ranges = {
            "source_reader_symbol_token_char_valid_y": (
                "source_reader_symbol_token_char_valid_x:",
                "cpy #$00",
            ),
            "source_reader_symbol_token_char_valid_x": (
                "source_reader_try_store_proc_export_token_y:",
                "cpx #$00",
            ),
        }

        for label, (next_label, index_check) in helper_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr uppercase_ascii", body, msg=label)
            self.assertIn(index_check, body, msg=label)
            self.assertIn("jmp uppercase_symbol_start_valid", body, msg=label)
            self.assertIn("jmp uppercase_symbol_body_valid", body, msg=label)

        caller_ranges = {
            "copy_symbol_from_scan_ptr_loop": (
                "copy_symbol_from_scan_ptr_store:",
                "jsr source_reader_symbol_token_char_valid_y",
            ),
            "copy_symbol_from_scan_ptr_stream_loop": (
                "copy_symbol_from_scan_ptr_stream_stored:",
                "jsr source_reader_try_store_symbol_token_x_from_scan_y",
            ),
            "copy_symbol_from_scan_y_loop": (
                "copy_symbol_from_scan_y_stored:",
                "jsr source_reader_try_store_symbol_token_x_from_scan_y",
            ),
            "store_proc_export_from_scan_ptr_or_fail_loop": (
                "store_proc_export_from_scan_ptr_or_fail_stored:",
                "jsr source_reader_try_store_proc_export_token_y",
            ),
        }

        for label, (next_label, expected) in caller_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn(expected, body, msg=label)
            self.assertNotIn("jsr uppercase_symbol_start_valid", body, msg=label)
            self.assertNotIn("jsr uppercase_symbol_body_valid", body, msg=label)

    def test_scan_ptr_symbol_helper_separates_source_offset_from_token_index(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"copy_symbol_from_scan_ptr:\n(?P<body>.*?)\ncopy_symbol_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        stream_match = re.search(
            r"copy_symbol_from_scan_ptr_stream:\n(?P<body>.*)",
            match.group("body"),
            re.DOTALL,
        )
        self.assertIsNotNone(stream_match)
        assert stream_match is not None
        body = stream_match.group("body")
        self.assertNotIn("(SOURCE_LIMIT & $ff)", match.group("body"))
        self.assertIn("jsr source_reader_begin_symbol_token_from_scan_ptr", body)
        self.assertNotIn("sta reader_scan_y_data", body)
        self.assertNotIn("jsr source_reader_begin_symbol_token\n", body)
        self.assertIn("jsr source_reader_try_store_symbol_token_x_from_scan_y", body)
        self.assertIn("jsr source_reader_terminate_symbol_token_x", body)
        self.assertIn("jsr source_reader_publish_symbol_token", body)
        self.assertIn("reader_token_buffer:", actc_text)
        self.assertIn("reader_token_buffer", actc_text)
        self.assertNotIn("sta (body_ptr),y", body)
        self.assertNotIn("sta declared_module_name,x", body)
        self.assertNotIn("sta declared_module_name,y", body)

    def test_declared_module_helper_separates_source_offset_from_token_index(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"copy_declared_module_or_fail:\n(?P<body>.*?)\ncompare_declared_module_or_fail:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        stream_match = re.search(
            r"copy_declared_module_or_fail_stream:\n(?P<body>.*)",
            match.group("body"),
            re.DOTALL,
        )
        self.assertIsNotNone(stream_match)
        assert stream_match is not None
        full_body = match.group("body")
        body = stream_match.group("body")
        self.assertNotIn("(SOURCE_LIMIT & $ff)", full_body)
        self.assertIn("jsr source_reader_begin_symbol_token", full_body)
        self.assertIn("jsr source_reader_store_symbol_token_y", full_body)
        self.assertIn("jsr source_reader_terminate_symbol_token_y", full_body)
        self.assertIn("jsr source_reader_symbol_token_char_valid_y", full_body)
        self.assertIn("jsr source_reader_publish_symbol_token", full_body)
        self.assertIn("jsr source_reader_begin_symbol_token_from_scan_ptr", body)
        self.assertNotIn("sta reader_scan_y_data", body)
        self.assertNotIn("jsr source_reader_begin_symbol_token\n", body)
        self.assertIn("jsr source_reader_try_store_symbol_token_x_from_scan_y", body)
        self.assertIn("jsr source_reader_terminate_symbol_token_x", body)
        self.assertIn("jsr source_reader_publish_symbol_token", body)
        self.assertNotIn("sta (body_ptr),y", full_body)
        self.assertNotIn("jsr uppercase_symbol_start_valid", full_body)
        self.assertNotIn("jsr uppercase_symbol_body_valid", full_body)
        self.assertNotIn("sta declared_module_name,x", body)
        self.assertNotIn("sta declared_module_name,y", body)

    def test_decl_count_overlay_symbol_helpers_publish_from_token_buffer(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        self.assertIn("overlay_symbol_token_buffer:", overlay_text)
        token_match = re.search(
            r"overlay_symbol_token_char_valid_current:\n(?P<body>.*?)\ncopy_symbol_to_var_name_window:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(token_match)
        assert token_match is not None
        token_body = token_match.group("body")
        self.assertIn("jsr uppercase_ascii", token_body)
        self.assertIn("ldy symbol_len_current", token_body)
        self.assertIn("jmp uppercase_symbol_start_valid", token_body)
        self.assertIn("jmp uppercase_symbol_body_valid", token_body)

        helper_ranges = {
            "copy_symbol_to_var_name_window": (
                "copy_symbol_to_var_name_window_fail:",
                "publish_symbol_token_to_var_name_window",
                "overlay_source_consume_var_name_token_char",
                "ACTC_OVERLAY_CTX_VAR_NAME_WINDOW_PTR",
            ),
            "copy_symbol_to_export_name_window": (
                "copy_symbol_to_export_name_window_fail:",
                "publish_symbol_token_to_export_name_window",
                "overlay_source_consume_export_name_token_char",
                "ACTC_OVERLAY_CTX_EXPORT_NAME_WINDOW_PTR",
            ),
        }

        for label, (next_label, publish_helper, consume_helper, direct_context_name) in helper_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                overlay_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr load_overlay_symbol_token_ptr", body, msg=label)
            self.assertIn(f"jsr {consume_helper}", body, msg=label)
            self.assertIn("sta (ACTC_OVERLAY_WORK_ZP),y", body, msg=label)
            self.assertNotIn("jsr overlay_symbol_token_char_valid_current", body, msg=label)
            self.assertIn(f"jsr {publish_helper}", body, msg=label)
            self.assertNotIn(direct_context_name, body, msg=label)
            self.assertNotIn("jsr uppercase_symbol_start_valid", body, msg=label)
            self.assertNotIn("jsr uppercase_symbol_body_valid", body, msg=label)

        consume_match = re.search(
            r"overlay_source_consume_symbol_token_body_char:\n(?P<body>.*?)\n"
            r"write_var_meta_window:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(consume_match)
        assert consume_match is not None
        consume_body = consume_match.group("body")
        self.assertIn("jsr overlay_symbol_token_char_valid_current", consume_body)
        self.assertIn("sta (ACTC_OVERLAY_WORK_ZP),y", consume_body)
        self.assertIn("jsr overlay_source_consume_scan_ptr", consume_body)
        self.assertNotIn("ACTC_OVERLAY_CTX_VAR_NAME_WINDOW_PTR", consume_body)
        self.assertNotIn("ACTC_OVERLAY_CTX_EXPORT_NAME_WINDOW_PTR", consume_body)
        self.assertNotIn("jsr uppercase_symbol_start_valid", consume_body)
        self.assertNotIn("jsr uppercase_symbol_body_valid", consume_body)

        publish_match = re.search(
            r"publish_symbol_token_to_var_name_window:\n(?P<body>.*?)\n"
            r"publish_symbol_token_to_export_name_window:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(publish_match)
        assert publish_match is not None
        self.assertIn("jsr load_var_name_window_ptr", publish_match.group("body"))
        self.assertIn("jmp copy_overlay_symbol_token_to_work_window", publish_match.group("body"))

        publish_match = re.search(
            r"publish_symbol_token_to_export_name_window:\n(?P<body>.*?)\n"
            r"copy_overlay_symbol_token_to_work_window:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(publish_match)
        assert publish_match is not None
        self.assertIn("jsr load_export_name_window_ptr", publish_match.group("body"))
        self.assertIn("jmp copy_overlay_symbol_token_to_work_window", publish_match.group("body"))

    def test_decl_count_overlay_inline_spaces_use_local_consume_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        self.assertIn("overlay_source_peek_scan_y:", overlay_text)
        self.assertIn("overlay_source_consume_scan_ptr:", overlay_text)

        match = re.search(
            r"skip_inline_spaces:\n(?P<body>.*?)\noverlay_source_match_line_end_from_scan_y:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr overlay_source_consume_inline_space_char", body)
        self.assertNotIn("jsr overlay_source_peek_scan_y", body)
        self.assertNotIn("jsr overlay_source_consume_scan_ptr", body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body)
        self.assertNotIn("jsr advance_source_scan", body)

        helper_match = re.search(
            r"overlay_source_consume_inline_space_char:\n(?P<body>.*?)\n"
            r"overlay_source_consume_whitespace_char:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr overlay_source_peek_scan_y", helper_body)
        self.assertIn("cmp #' '", helper_body)
        self.assertIn("cmp #9", helper_body)
        self.assertIn("jsr overlay_source_consume_scan_ptr", helper_body)

        whitespace_helper_match = re.search(
            r"overlay_source_consume_whitespace_char:\n(?P<body>.*?)\n"
            r"overlay_source_consume_line_char:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(whitespace_helper_match)
        assert whitespace_helper_match is not None
        whitespace_helper_body = whitespace_helper_match.group("body")
        self.assertIn("jsr overlay_source_peek_scan_y", whitespace_helper_body)
        for expected in ("cmp #' '", "cmp #9", "cmp #10", "cmp #13"):
            self.assertIn(expected, whitespace_helper_body)
        self.assertIn("jsr overlay_source_consume_scan_ptr", whitespace_helper_body)

    def test_decl_count_overlay_line_end_uses_local_match_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        match = re.search(
            r"require_line_end:\n(?P<body>.*?)\nskip_inline_spaces:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr skip_inline_spaces", body)
        self.assertIn("jsr overlay_source_match_line_end_from_scan_y", body)
        self.assertNotIn("jsr overlay_source_peek_scan_y", body)
        self.assertNotIn("cmp #10", body)
        self.assertNotIn("cmp #13", body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body)

        helper_match = re.search(
            r"overlay_source_match_line_end_from_scan_y:\n(?P<body>.*?)\noverlay_source_match_expected_char:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr overlay_source_peek_scan_y", helper_body)
        self.assertIn("cmp #10", helper_body)
        self.assertIn("cmp #13", helper_body)
        self.assertIn("clc", helper_body)
        self.assertIn("sec", helper_body)

    def test_decl_count_overlay_var_symbol_reads_use_peek_wrapper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        match = re.search(
            r"copy_symbol_to_var_name_window:\n(?P<body>.*?)\ncopy_symbol_to_var_name_window_done:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr overlay_source_consume_var_name_token_char", body)
        self.assertNotIn("jsr overlay_source_peek_scan_y", body)
        self.assertNotIn("jsr overlay_source_consume_scan_ptr", body)
        self.assertNotIn("jsr advance_source_scan", body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body)

        helper_match = re.search(
            r"overlay_source_consume_var_name_token_char:\n(?P<body>.*?)\n"
            r"overlay_source_consume_export_name_token_char:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr overlay_source_peek_scan_y", helper_body)
        self.assertIn("cmp #'='", helper_body)
        self.assertIn("cmp #','", helper_body)
        self.assertIn("cmp #'('", helper_body)
        self.assertIn("cmp #')'", helper_body)
        self.assertIn("cmp #10", helper_body)
        self.assertIn("cmp #13", helper_body)
        self.assertIn("jsr overlay_source_consume_symbol_token_body_char", helper_body)

    def test_decl_count_overlay_export_symbol_reads_use_peek_wrapper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        match = re.search(
            r"copy_symbol_to_export_name_window:\n(?P<body>.*?)\ncopy_symbol_to_export_name_window_done:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr overlay_source_consume_export_name_token_char", body)
        self.assertNotIn("jsr overlay_source_peek_scan_y", body)
        self.assertNotIn("jsr overlay_source_consume_scan_ptr", body)
        self.assertNotIn("jsr advance_source_scan", body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body)

        helper_match = re.search(
            r"overlay_source_consume_export_name_token_char:\n(?P<body>.*?)\n"
            r"overlay_source_consume_symbol_token_body_char:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr overlay_source_peek_scan_y", helper_body)
        self.assertIn("cmp #'('", helper_body)
        self.assertIn("cmp #'='", helper_body)
        self.assertIn("cmp #10", helper_body)
        self.assertIn("cmp #13", helper_body)
        self.assertIn("jsr overlay_source_consume_symbol_token_body_char", helper_body)

        body_helper_match = re.search(
            r"overlay_source_consume_symbol_token_body_char:\n(?P<body>.*?)\n"
            r"write_var_meta_window:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(body_helper_match)
        assert body_helper_match is not None
        body_helper = body_helper_match.group("body")
        self.assertIn("jsr overlay_symbol_token_char_valid_current", body_helper)
        self.assertIn("sta (ACTC_OVERLAY_WORK_ZP),y", body_helper)
        self.assertIn("jsr overlay_source_consume_scan_ptr", body_helper)
        self.assertNotIn("jsr overlay_source_peek_scan_y", body_helper)

    def test_decl_count_overlay_proc_param_punctuation_uses_expected_char_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        match = re.search(
            r"parse_proc_params:\n(?P<body>.*?)\nparse_optional_routine_binding:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        for expected in ("lda #'('", "lda #','", "lda #')'"):
            self.assertIn(expected, body)
        self.assertIn("jsr overlay_source_match_expected_char", body)
        self.assertIn("jsr overlay_source_consume_expected_char", body)
        self.assertNotIn("jsr overlay_source_peek_scan_y", body)
        self.assertNotIn("jsr overlay_source_consume_scan_ptr", body)
        for parser_cmp in ("cmp #'('", "cmp #','", "cmp #')'"):
            self.assertNotIn(parser_cmp, body)
        self.assertNotIn("jsr advance_source_scan", body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body)

        match_helper = re.search(
            r"overlay_source_match_expected_char:\n(?P<body>.*?)\noverlay_source_consume_expected_char:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match_helper)
        assert match_helper is not None
        match_helper_body = match_helper.group("body")
        self.assertIn("sta expected_char", match_helper_body)
        self.assertIn("jsr overlay_source_peek_scan_y", match_helper_body)
        self.assertIn("cmp expected_char", match_helper_body)
        self.assertIn("clc", match_helper_body)
        self.assertIn("sec", match_helper_body)

        consume_helper = re.search(
            r"overlay_source_consume_expected_char:\n(?P<body>.*?)\noverlay_source_consume_inline_space_char:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(consume_helper)
        assert consume_helper is not None
        consume_helper_body = consume_helper.group("body")
        self.assertIn("jsr overlay_source_match_expected_char", consume_helper_body)
        self.assertIn("jsr overlay_source_consume_scan_ptr", consume_helper_body)

    def test_decl_count_overlay_decl_tail_delimiters_use_source_helpers(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        helper_ranges = {
            "validate_decl_tail": "validate_module_decl_tail:",
            "validate_module_decl_tail": "validate_initializer_expr:",
        }
        for label, next_label in helper_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                overlay_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr skip_inline_spaces", body, msg=label)
            self.assertIn("jsr overlay_source_match_line_end_from_scan_y", body, msg=label)
            self.assertIn("jsr overlay_source_match_expected_char", body, msg=label)
            self.assertIn("jsr overlay_source_consume_expected_char", body, msg=label)
            self.assertNotIn("jsr overlay_source_peek_scan_y", body, msg=label)
            self.assertNotIn("jsr overlay_source_consume_scan_ptr", body, msg=label)
            self.assertNotIn("cmp #10", body, msg=label)
            self.assertNotIn("cmp #13", body, msg=label)
            self.assertNotIn("cmp #'='", body, msg=label)
            self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body, msg=label)
            self.assertNotIn("jsr advance_source_scan", body, msg=label)

    def test_decl_count_overlay_keyword_reads_use_peek_wrapper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        helper_ranges = {
            "match_keyword_char": "match_keyword_char_fail:",
            "match_keyword_at_scan_delimiter": "match_keyword_at_scan_fail:",
            "overlay_source_match_keyword_delimiter": "overlay_source_keyword_delimiter_from_a:",
        }
        for label, next_label in helper_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                overlay_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            if label == "match_keyword_char":
                self.assertIn("jsr overlay_source_peek_scan_y", body, msg=label)
                self.assertIn("jsr overlay_source_consume_scan_ptr", body, msg=label)
            elif label == "match_keyword_at_scan_delimiter":
                self.assertIn("jsr overlay_source_match_keyword_delimiter", body, msg=label)
                self.assertNotIn("jsr overlay_source_peek_scan_y", body, msg=label)
                self.assertNotIn("jsr overlay_source_keyword_delimiter_from_a", body, msg=label)
                for delimiter_check in ("cmp #' '", "cmp #9", "cmp #10", "cmp #13"):
                    self.assertNotIn(delimiter_check, body, msg=label)
            else:
                self.assertIn("jsr overlay_source_peek_scan_y", body, msg=label)
                self.assertIn("jmp overlay_source_keyword_delimiter_from_a", body, msg=label)
                for delimiter_check in ("cmp #' '", "cmp #9", "cmp #10", "cmp #13"):
                    self.assertNotIn(delimiter_check, body, msg=label)
            self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body, msg=label)
            self.assertNotIn("jsr advance_source_scan", body, msg=label)

        delimiter_match = re.search(
            r"overlay_source_keyword_delimiter_from_a:\n(?P<body>.*?)\n"
            r"overlay_source_rewind_keyword_match:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(delimiter_match)
        assert delimiter_match is not None
        delimiter_body = delimiter_match.group("body")
        for delimiter_check in ("cmp #' '", "cmp #9", "cmp #10", "cmp #13"):
            self.assertIn(delimiter_check, delimiter_body)
        self.assertIn("overlay_source_keyword_delimiter_ok:", delimiter_body)

        fail_match = re.search(
            r"match_keyword_at_scan_fail:\n(?P<body>.*?)\nmatch_keyword_at_scan_ok:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(fail_match)
        assert fail_match is not None
        fail_body = fail_match.group("body")
        self.assertIn("jsr overlay_source_rewind_keyword_match", fail_body)
        self.assertNotIn("dec ACTC_OVERLAY_SCAN_ZP", fail_body)
        self.assertNotIn("inc source_window_remaining", fail_body)

        rewind_match = re.search(
            r"overlay_source_rewind_keyword_match:\n(?P<body>.*?)\nuppercase_ascii:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(rewind_match)
        assert rewind_match is not None
        rewind_body = rewind_match.group("body")
        self.assertIn("dec ACTC_OVERLAY_SCAN_ZP", rewind_body)
        self.assertIn("dec source_mark", rewind_body)
        self.assertIn("inc source_window_remaining", rewind_body)

        load_next_match = re.search(
            r"load_next_source_window_from_context:\n(?P<body>.*?)\nadvance_source_scan:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(load_next_match)
        assert load_next_match is not None
        load_next_body = load_next_match.group("body")
        self.assertIn("txa", load_next_body)
        self.assertIn("tax", load_next_body)

    def test_decl_count_overlay_initializer_classification_uses_local_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        helper_match = re.search(
            r"overlay_symbol_body_char_valid:\n(?P<body>.*?)\nvalidate_initializer_expr_char:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr uppercase_ascii", helper_body)
        self.assertIn("jmp uppercase_symbol_body_valid", helper_body)

        helper_ranges = {
            "validate_initializer_expr_char": "validate_initializer_expr_char_token:",
            "init_value_keyword_tail_ok": "init_value_keyword_tail_bad:",
        }
        for label, next_label in helper_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                overlay_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr overlay_symbol_body_char_valid", body, msg=label)
            self.assertNotIn("jsr uppercase_ascii", body, msg=label)
            self.assertNotIn("jsr uppercase_symbol_body_valid", body, msg=label)

        constant_table_match = re.search(
            r"init_value_parse_builtin_constant_work_loop:\n(?P<body>.*?)\n"
            r"init_value_parse_builtin_constant_work_ok:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(constant_table_match)
        assert constant_table_match is not None
        constant_table_body = constant_table_match.group("body")
        self.assertIn("sta init_parse_tmp", constant_table_body)
        self.assertIn("sta init_value_builtin_symbol_load+2", constant_table_body)
        self.assertIn("ora init_parse_tmp", constant_table_body)
        self.assertIn("beq init_value_parse_builtin_constant_work_fail_restore", constant_table_body)
        self.assertIn("lda init_parse_tmp", constant_table_body)
        self.assertIn("sta init_value_builtin_symbol_load+1", constant_table_body)

    def test_decl_count_overlay_initializer_expr_delimiters_use_source_helpers(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        helper_ranges = {
            "validate_initializer_expr": (
                "validate_bracket_initializer_expr:",
                (
                    "jsr overlay_source_match_line_end_from_scan_y",
                    "lda #'['",
                    "jsr overlay_source_match_expected_char",
                ),
                ("jsr overlay_source_peek_scan_y", "jsr overlay_source_consume_scan_ptr"),
                ("cmp #10", "cmp #13", "cmp #'['"),
            ),
            "validate_bracket_initializer_expr": (
                "validate_bracket_initializer_expr_loop:",
                ("lda #'['", "jsr overlay_source_consume_expected_char"),
                ("jsr overlay_source_consume_scan_ptr",),
                (),
            ),
            "validate_bracket_initializer_expr_loop": (
                "validate_bracket_initializer_expr_done:",
                (
                    "jsr overlay_source_match_line_end_from_scan_y",
                    "lda #']'",
                    "jsr overlay_source_match_expected_char",
                    "jsr overlay_source_consume_initializer_body_char",
                ),
                ("jsr overlay_source_peek_scan_y", "jsr overlay_source_consume_scan_ptr"),
                ("cmp #10", "cmp #13", "cmp #']'"),
            ),
            "validate_bracket_initializer_expr_done": (
                "validate_line_initializer_expr:",
                ("lda #']'", "jsr overlay_source_consume_expected_char", "jsr require_line_end"),
                ("jsr overlay_source_consume_scan_ptr",),
                ("cmp #']'",),
            ),
            "validate_line_initializer_expr_loop": (
                "validate_line_initializer_expr_done:",
                (
                    "jsr overlay_source_match_line_end_from_scan_y",
                    "lda #']'",
                    "jsr overlay_source_match_expected_char",
                    "jsr overlay_source_consume_initializer_body_char",
                ),
                ("jsr overlay_source_peek_scan_y", "jsr overlay_source_consume_scan_ptr"),
                ("cmp #10", "cmp #13", "cmp #']'"),
            ),
            "overlay_source_consume_initializer_body_char": (
                "validate_initializer_expr_char:",
                (
                    "jsr overlay_source_peek_scan_y",
                    "jsr init_capture_char",
                    "jsr validate_initializer_expr_char",
                    "jsr overlay_source_consume_scan_ptr",
                ),
                (),
                (),
            ),
        }
        for label, (next_label, expected_lines, forbidden_lines, forbidden_compares) in helper_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                overlay_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            for expected in expected_lines:
                self.assertIn(expected, body, msg=label)
            for forbidden in forbidden_lines:
                self.assertNotIn(forbidden, body, msg=label)
            for forbidden in forbidden_compares:
                self.assertNotIn(forbidden, body, msg=label)
            self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body, msg=label)
            self.assertNotIn("jsr advance_source_scan", body, msg=label)

    def test_decl_count_overlay_line_skip_reads_use_peek_wrapper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        match = re.search(
            r"skip_source_line:\n(?P<body>.*?)\nmatch_module_keyword:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr overlay_source_consume_line_char", body)
        self.assertNotIn("jsr overlay_source_peek_scan_y", body)
        self.assertNotIn("jsr overlay_source_consume_scan_ptr", body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body)
        self.assertNotIn("jsr advance_source_scan", body)

        helper_match = re.search(
            r"overlay_source_consume_line_char:\n(?P<body>.*?)\nclear_var_name_window:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr ensure_source_window_available", helper_body)
        self.assertIn("lda source_page_failed", helper_body)
        self.assertIn("jsr overlay_source_peek_scan_y", helper_body)
        self.assertIn("cmp #10", helper_body)
        self.assertIn("cmp #13", helper_body)
        self.assertIn("jsr overlay_source_consume_scan_ptr", helper_body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", helper_body)
        self.assertNotIn("jsr advance_source_scan", helper_body)

    def test_decl_count_overlay_remaining_raw_scan_reads_are_documented(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        raw_pattern = re.compile(r"\b(?:lda|cmp) \(ACTC_OVERLAY_SCAN_ZP\),y")
        raw_positions = [match.start() for match in raw_pattern.finditer(overlay_text)]
        self.assertNotIn("overlay_hot_source_peek_scan_y", overlay_text)
        skip_blank_match = re.search(
            r"skip_blank_lines_and_spaces:\n(?P<body>.*?)\nskip_source_line:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(skip_blank_match)
        assert skip_blank_match is not None
        skip_blank_body = skip_blank_match.group("body")
        self.assertIn("jsr skip_source_whitespace", skip_blank_body)
        self.assertIn("jsr overlay_source_peek_scan_y", skip_blank_body)
        self.assertIn("cmp #';'", skip_blank_body)
        self.assertIn("jsr skip_source_line", skip_blank_body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", skip_blank_body)
        self.assertNotIn("jsr advance_source_scan", skip_blank_body)

        self.assertIn("ACTC_OVERLAY_CACHE_ZP = ACTC_OVERLAY_SCAN_ZP", overlay_text)
        self.assertIn("cmp (ACTC_OVERLAY_CACHE_ZP),y", overlay_text)
        allowed_ranges = (
            ("overlay_source_peek_scan_y", "overlay_source_consume_scan_ptr:"),
        )
        allowed_positions = set()
        for label, next_label in allowed_ranges:
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                overlay_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            start, end = match.span("body")
            allowed_positions.update(pos for pos in raw_positions if start <= pos < end)

        self.assertEqual(
            sorted(raw_positions),
            sorted(allowed_positions),
            msg="raw declaration-overlay scan reads must stay in documented peek/cache paths",
        )

    def test_decl_count_overlay_raw_scan_writes_are_classified(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")

        direct_scan_store_positions = [
            match.start()
            for match in re.finditer(r"\bsta \(ACTC_OVERLAY_SCAN_ZP\),y", overlay_text)
        ]
        writeback_match = re.search(
            r"write_resident_decl_counts:\n(?P<body>.*?)\nwrite_module_var_decl:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(writeback_match)
        assert writeback_match is not None
        writeback_start, writeback_end = writeback_match.span("body")
        self.assertEqual(len(direct_scan_store_positions), 4)
        self.assertTrue(
            all(writeback_start <= pos < writeback_end for pos in direct_scan_store_positions),
            msg="direct SCAN_ZP writes should only publish resident declaration and fixed counts",
        )

        cache_store_positions = [
            match.start()
            for match in re.finditer(r"\bsta \(ACTC_OVERLAY_CACHE_ZP\),y", overlay_text)
        ]
        cache_store_ranges: list[tuple[int, int]] = []
        for start_label, end_label in (
            ("store_fixed_meta_cache_x:", "load_fixed_meta_cache_x:"),
            ("copy_work_window_to_scan_cache:", "setup_var_cache_ptr_x:"),
        ):
            cache_store_match = re.search(
                rf"{start_label}\n(?P<body>.*?)\n{end_label}",
                overlay_text,
                re.DOTALL,
            )
            self.assertIsNotNone(cache_store_match, msg=start_label)
            assert cache_store_match is not None
            cache_store_ranges.append(cache_store_match.span("body"))
        self.assertEqual(len(cache_store_positions), 2)
        self.assertTrue(
            all(
                any(start <= pos < end for start, end in cache_store_ranges)
                for pos in cache_store_positions
            ),
            msg="cache alias writes should stay inside bounded cache-copy helpers",
        )

        protected_callers = {
            "find_var_name_cache_match_range": "find_export_name_cache_match:",
            "find_export_name_cache_match": "compare_var_name_window_to_cache_x:",
            "store_var_name_cache_x": "store_export_name_cache_x:",
            "store_export_name_cache_x": "copy_work_window_to_scan_cache:",
        }
        for label, next_label in protected_callers.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                overlay_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr save_source_scan_ptr", body, msg=label)
            self.assertIn("jsr restore_source_scan_ptr", body, msg=label)

    def test_decl_count_overlay_raw_scan_advances_are_classified(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        raw_advance_positions = [
            match.start()
            for match in re.finditer(r"\bjsr advance_source_scan\b", overlay_text)
        ]
        allowed_ranges = (
            ("overlay_source_consume_scan_ptr:", "advance_source_window_remaining:"),
        )
        allowed_positions = set()
        for label, next_label in allowed_ranges:
            match = re.search(
                rf"{re.escape(label)}\n(?P<body>.*?)\n{re.escape(next_label)}",
                overlay_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            start, end = match.span("body")
            allowed_positions.update(pos for pos in raw_advance_positions if start <= pos < end)

        self.assertNotIn("advance_source_by_symbol_len:", overlay_text)
        self.assertEqual(
            sorted(raw_advance_positions),
            sorted(allowed_positions),
            msg="raw declaration-overlay scan advances must stay behind the consume helper",
        )

        whitespace_match = re.search(
            r"skip_source_whitespace:\n(?P<body>.*?)\nskip_blank_lines_and_spaces:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(whitespace_match)
        assert whitespace_match is not None
        whitespace_body = whitespace_match.group("body")
        self.assertIn("jsr overlay_source_consume_whitespace_char", whitespace_body)
        self.assertNotIn("jsr overlay_source_peek_scan_y", whitespace_body)
        self.assertNotIn("jsr overlay_source_consume_scan_ptr", whitespace_body)
        self.assertNotIn("jsr advance_source_scan", whitespace_body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", whitespace_body)

    def test_source_header_overlay_source_reads_go_through_local_peek(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_source_header.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        lexical_text = (
            self.root / "src" / "tools_udos" / "actc" / "actc_overlay_lexical.inc"
        ).read_text(encoding="ascii")
        self.assertIn("source_header_peek_scan_y:", overlay_text)
        self.assertIn("source_header_consume_scan_y:", overlay_text)
        self.assertIn('.include "actc_overlay_lexical.inc"', overlay_text)

        raw_positions = [
            match.start()
            for match in re.finditer(r"\blda \(ACTC_OVERLAY_SCAN_ZP\),y", overlay_text)
        ]
        helper_match = re.search(
            r"source_header_peek_scan_y:\n(?P<body>.*?)\nmodule_keyword:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_start, helper_end = helper_match.span("body")
        self.assertTrue(raw_positions)
        self.assertTrue(all(helper_start <= pos < helper_end for pos in raw_positions))
        helper_body = helper_match.group("body")
        self.assertIn("jsr ensure_source_window_available", helper_body)
        self.assertIn("load_next_source_window_from_context:", overlay_text)

        consume_match = re.search(
            r"source_header_consume_scan_y:\n(?P<body>.*?)\nmodule_keyword:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(consume_match)
        assert consume_match is not None
        consume_body = consume_match.group("body")
        self.assertIn("jsr source_header_peek_scan_y", consume_body)
        self.assertIn("jsr advance_source_scan", consume_body)
        self.assertIn("lda source_page_failed", consume_body)
        self.assertIn("source_header_consume_scan_y_fail:", consume_body)
        self.assertIn("sec", consume_body)
        self.assertIn("clc", consume_body)

        helper_ranges = {
            "skip_source_whitespace": "skip_source_spaces:",
            "skip_source_spaces": "source_header_consume_whitespace_char:",
            "source_header_consume_whitespace_char": "source_header_consume_inline_space_char:",
            "source_header_consume_inline_space_char": "match_module_keyword:",
            "match_module_keyword": "compare_requested_module:",
            "compare_requested_module": "source_header_consume_uppercase_char:",
        }
        for label, next_label in helper_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                overlay_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            if label == "match_module_keyword":
                self.assertIn("jsr source_header_consume_uppercase_char", body, msg=label)
                self.assertNotIn("jsr source_header_peek_scan_y", body, msg=label)
                self.assertNotIn("jsr source_header_consume_scan_y", body, msg=label)
                self.assertNotIn("jsr uppercase_ascii", body, msg=label)
            elif label == "skip_source_whitespace":
                self.assertIn("jsr source_header_consume_whitespace_char", body, msg=label)
                self.assertNotIn("jsr source_header_peek_scan_y", body, msg=label)
                self.assertNotIn("jsr source_header_consume_scan_y", body, msg=label)
            elif label == "skip_source_spaces":
                self.assertIn("jsr source_header_consume_inline_space_char", body, msg=label)
                self.assertNotIn("jsr source_header_peek_scan_y", body, msg=label)
                self.assertNotIn("jsr source_header_consume_scan_y", body, msg=label)
            elif label == "compare_requested_module":
                self.assertIn("jsr source_header_consume_requested_module_char", body, msg=label)
                self.assertNotIn("jsr source_header_peek_scan_y", body, msg=label)
                self.assertNotIn("jsr source_header_consume_scan_y", body, msg=label)
                self.assertNotIn("jsr source_header_symbol_token_char_valid_x", body, msg=label)
            else:
                self.assertIn("jsr source_header_peek_scan_y", body, msg=label)
                self.assertIn("jsr source_header_consume_scan_y", body, msg=label)
            self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body, msg=label)
            self.assertNotIn("jsr advance_source_scan", body, msg=label)
            if label in {
                "skip_source_whitespace",
                "skip_source_spaces",
                "match_module_keyword",
            }:
                self.assertIn("bcs", body, msg=label)
            if label == "source_header_consume_whitespace_char":
                for expected in ("cmp #' '", "cmp #9", "cmp #10", "cmp #13"):
                    self.assertIn(expected, body, msg=label)
                self.assertIn("sec", body, msg=label)
            if label == "source_header_consume_inline_space_char":
                for expected in ("cmp #' '", "cmp #9"):
                    self.assertIn(expected, body, msg=label)
                for forbidden in ("cmp #10", "cmp #13"):
                    self.assertNotIn(forbidden, body, msg=label)
                self.assertIn("sec", body, msg=label)
            if label == "compare_requested_module":
                self.assertIn("bcc compare_requested_module_char_valid", body, msg=label)
                self.assertIn("jmp compare_requested_module_fail", body, msg=label)

        consume_upper_match = re.search(
            r"source_header_consume_uppercase_char:\n(?P<body>.*?)\n"
            r"\.include \"actc_overlay_lexical\.inc\"",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(consume_upper_match)
        assert consume_upper_match is not None
        consume_upper_body = consume_upper_match.group("body")
        self.assertIn("sta expected_char", consume_upper_body)
        self.assertIn("jsr source_header_peek_scan_y", consume_upper_body)
        self.assertIn("jsr uppercase_ascii", consume_upper_body)
        self.assertIn("cmp expected_char", consume_upper_body)
        self.assertIn("jsr source_header_consume_scan_y", consume_upper_body)
        self.assertIn("source_header_consume_uppercase_char_fail:", consume_upper_body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", consume_upper_body)
        self.assertNotIn("jsr advance_source_scan", consume_upper_body)

        consume_module_match = re.search(
            r"source_header_consume_requested_module_char:\n(?P<body>.*?)\n"
            r"save_module_start_mark:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(consume_module_match)
        assert consume_module_match is not None
        consume_module_body = consume_module_match.group("body")
        self.assertIn("jsr source_header_peek_scan_y", consume_module_body)
        self.assertIn("jsr source_header_symbol_token_char_valid_x", consume_module_body)
        self.assertIn("jsr uppercase_ascii", consume_module_body)
        self.assertIn("jsr source_header_consume_scan_y", consume_module_body)
        self.assertIn("source_header_consume_requested_module_fail:", consume_module_body)
        self.assertIn("sta compare_char", consume_module_body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", consume_module_body)
        self.assertNotIn("jsr advance_source_scan", consume_module_body)

        token_match = re.search(
            r"source_header_symbol_token_char_valid_x:\n(?P<body>.*?)\n"
            r"source_header_consume_requested_module_char:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(token_match)
        assert token_match is not None
        token_body = token_match.group("body")
        self.assertIn("jsr uppercase_ascii", token_body)
        self.assertIn("cpx #$00", token_body)
        self.assertIn("jmp uppercase_symbol_start_valid", token_body)
        self.assertIn("jmp uppercase_symbol_body_valid", token_body)
        for helper in (
            "uppercase_ascii:",
            "uppercase_symbol_start_valid:",
            "uppercase_symbol_body_valid:",
        ):
            self.assertIn(helper, lexical_text)

    def test_source_header_overlay_raw_scan_advances_are_classified(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_source_header.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        raw_advance_positions = [
            match.start()
            for match in re.finditer(r"\bjsr advance_source_scan\b", overlay_text)
        ]
        consume_match = re.search(
            r"source_header_consume_scan_y:\n(?P<body>.*?)\nmodule_keyword:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(consume_match)
        assert consume_match is not None
        consume_start, consume_end = consume_match.span("body")
        self.assertEqual(len(raw_advance_positions), 1)
        self.assertTrue(
            all(consume_start <= pos < consume_end for pos in raw_advance_positions),
            msg="source-header scan advances should stay behind source_header_consume_scan_y",
        )

    def test_overlay_scan_zp_raw_reads_are_classified(self) -> None:
        overlay_dir = self.root / "src" / "tools_udos" / "actc"
        raw_read_re = re.compile(r"\b(?:lda|cmp) \(ACTC_OVERLAY_SCAN_ZP\),y")
        allowed_ranges = {
            "actc_overlay_decl_counts.asm": (
                (r"overlay_source_peek_scan_y:", r"overlay_source_consume_scan_ptr:", "source peek helper"),
            ),
            "actc_overlay_emit_object.asm": (
                (
                    r"emit_external_call_sequence_current_is_sid_cutoff_loop:",
                    r"emit_external_call_sequence_current_is_sid_cutoff_yes:",
                    "external export symbol comparison",
                ),
                (r"emit_object_peek_payload_y:", r"actc_overlay_end:", "payload peek helper"),
            ),
            "actc_overlay_payload_layout.asm": (
                (r"payload_layout_peek_payload_y:", r"store_layout_locals_to_resident:", "payload peek helper"),
            ),
            "actc_overlay_source_header.asm": (
                (r"source_header_peek_scan_y:", r"module_keyword:", "source peek helper"),
            ),
        }
        expected_no_raw_reads = {
            "actc_overlay_body_collect.asm",
            "actc_overlay_body_preallocate.asm",
            "actc_overlay_emit_native_fixed_object.asm",
            "actc_overlay_emit_native_local_object.asm",
            "actc_overlay_emit_native_local_runtime_object.asm",
            "actc_overlay_emit_native_local_mixed_object.asm",
            "actc_overlay_emit_native_object.asm",
            "actc_overlay_emit_native_real_control_object.asm",
            "actc_overlay_emit_native_real_function_object.asm",
            "actc_overlay_emit_native_real_while_object.asm",
            "actc_overlay_emit_native_runtime_condition_object.asm",
            "actc_overlay_emit_native_runtime_sequence_object.asm",
            "actc_overlay_emit_native_runtime_nested_object.asm",
            "actc_overlay_emit_native_real_object.asm",
            "actc_overlay_noop.asm",
            "actc_overlay_preprocess.asm",
            "actc_overlay_runtime_imports.asm",
        }
        overlay_names = {path.name for path in overlay_dir.glob("actc_overlay_*.asm")}
        self.assertEqual(overlay_names, set(allowed_ranges) | expected_no_raw_reads)

        payload_overlays = {
            "actc_overlay_emit_object.asm",
            "actc_overlay_payload_layout.asm",
        }
        source_overlays = {
            "actc_overlay_decl_counts.asm",
            "actc_overlay_source_header.asm",
        }

        for overlay_name in sorted(overlay_names):
            overlay_text = (overlay_dir / overlay_name).read_text(encoding="ascii")
            raw_matches = list(raw_read_re.finditer(overlay_text))
            raw_locations = {
                match.start(): (
                    f"{overlay_name}:{overlay_text.count(chr(10), 0, match.start()) + 1}: "
                    f"{match.group(0)}"
                )
                for match in raw_matches
            }

            if overlay_name in expected_no_raw_reads:
                self.assertEqual(list(raw_locations.values()), [], msg=overlay_name)
                continue

            if overlay_name in payload_overlays:
                self.assertNotIn("ACTC_OVERLAY_CTX_SOURCE", overlay_text, msg=overlay_name)
                self.assertNotIn("LOAD_NEXT_SOURCE", overlay_text, msg=overlay_name)
                self.assertIn("ACTC_OVERLAY_CTX_BODY_PTR_SLOT_PTR", overlay_text, msg=overlay_name)
            if overlay_name in source_overlays:
                self.assertIn("ACTC_OVERLAY_CTX_SOURCE_WINDOW_PTR_LO", overlay_text, msg=overlay_name)

            allowed_positions: set[int] = set()
            for start_label, end_label, range_name in allowed_ranges[overlay_name]:
                match = re.search(
                    rf"{start_label}\n(?P<body>.*?)\n{end_label}",
                    overlay_text,
                    re.DOTALL,
                )
                self.assertIsNotNone(match, msg=f"{overlay_name}: {range_name}")
                assert match is not None
                start, end = match.span("body")
                allowed_positions.update(pos for pos in raw_locations if start <= pos < end)

            unexpected_locations = [
                raw_locations[pos]
                for pos in sorted(raw_locations)
                if pos not in allowed_positions
            ]
            self.assertEqual(unexpected_locations, [], msg=overlay_name)
            self.assertTrue(raw_locations, msg=overlay_name)

    def test_overlay_scan_zp_raw_writes_are_classified(self) -> None:
        overlay_dir = self.root / "src" / "tools_udos" / "actc"
        raw_store_re = re.compile(r"\bsta \(ACTC_OVERLAY_SCAN_ZP\),y")
        allowed_ranges = {
            "actc_overlay_decl_counts.asm": (
                (r"write_resident_decl_counts:", r"write_module_var_decl:", "resident declaration count writeback"),
            ),
            "actc_overlay_noop.asm": (
                (r"finish_workflow_command:", r"actc_overlay_ok:", "workflow command terminator"),
                (r"append_command_char:", r"append_command_char_fail:", "bounded workflow command write"),
            ),
        }
        expected_write_counts = {
            "actc_overlay_decl_counts.asm": 4,
            "actc_overlay_noop.asm": 2,
        }
        overlay_names = {path.name for path in overlay_dir.glob("actc_overlay_*.asm")}

        for overlay_name in sorted(overlay_names):
            overlay_text = (overlay_dir / overlay_name).read_text(encoding="ascii")
            raw_matches = list(raw_store_re.finditer(overlay_text))
            raw_locations = {
                match.start(): (
                    f"{overlay_name}:{overlay_text.count(chr(10), 0, match.start()) + 1}: "
                    f"{match.group(0)}"
                )
                for match in raw_matches
            }
            if overlay_name not in allowed_ranges:
                self.assertEqual(raw_locations, {}, msg=overlay_name)
                continue

            allowed_positions: set[int] = set()
            for start_label, end_label, range_name in allowed_ranges[overlay_name]:
                match = re.search(
                    rf"{start_label}\n(?P<body>.*?)\n{end_label}",
                    overlay_text,
                    re.DOTALL,
                )
                self.assertIsNotNone(match, msg=f"{overlay_name}: {range_name}")
                assert match is not None
                start, end = match.span("body")
                allowed_positions.update(pos for pos in raw_locations if start <= pos < end)

            unexpected_locations = [
                raw_locations[pos]
                for pos in sorted(raw_locations)
                if pos not in allowed_positions
            ]
            self.assertEqual(unexpected_locations, [], msg=overlay_name)
            self.assertEqual(len(raw_locations), expected_write_counts[overlay_name], msg=overlay_name)

    def test_body_collect_overlay_source_reads_go_through_local_reader(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_collect.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        raw_positions = [
            match.start()
            for match in re.finditer(r"\blda \(ACTC_OVERLAY_SCAN_ZP\),y", overlay_text)
        ]
        self.assertEqual(raw_positions, [])
        helper_match = re.search(
            r"read_scan_char_at_y:\n(?P<body>.*?)\nuppercase_ascii_local:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("ACTC_OVERLAY_CTX_PEEK_SCAN_Y_FN_LO", helper_body)
        self.assertIn("jsr call_loaded_target_with_a", helper_body)
        self.assertNotIn("jsr load_resident_scan_ptr_to_scan_zp", helper_body)

    def test_body_collect_overlay_remaining_raw_read_calls_are_helper_owned(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_collect.asm"
        allowed_labels = {
            "match_scan_char_local",
            "peek_decimal_digit_value_local",
            "consume_scan_char_local",
            "consume_uppercase_char_local",
        }
        labels_with_reads: list[str] = []
        offenders: list[str] = []
        current_label = "<file>"

        for line_number, line in enumerate(overlay_path.read_text(encoding="ascii").splitlines(), 1):
            label_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):", line)
            if label_match is not None:
                current_label = label_match.group(1)

            if "jsr read_scan_char_at_y" not in line:
                continue

            labels_with_reads.append(current_label)
            if current_label not in allowed_labels:
                offenders.append(f"{overlay_path.relative_to(self.root)}:{line_number}: {current_label}")

        self.assertEqual(offenders, [])
        self.assertEqual(set(labels_with_reads), allowed_labels)

    def test_body_collect_overlay_terminator_keywords_use_local_source_reader_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_collect.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        return_match = re.search(
            r"^collect_proc_body_ops_overlay_try_return:\n(?P<body>.*?)\n"
            r"^collect_proc_body_ops_overlay_try_return_emit:",
            overlay_text,
            re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(return_match)
        assert return_match is not None
        return_body = return_match.group("body")
        self.assertIn("jsr match_line_end_local", return_body)
        self.assertNotIn("jsr read_scan_char_at_y", return_body)
        self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", return_body)

        terminator_ranges = {
            "require_then_or_line_end_local": (
                "require_do_or_line_end_local:",
                "lda #'T'",
            ),
            "require_do_or_line_end_local": (
                "emit_real_small_int_assignment_local_or_fail:",
                "lda #'D'",
            ),
        }

        for label, (next_label, expected_first_char) in terminator_ranges.items():
            match = re.search(
                rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                overlay_text,
                re.DOTALL | re.MULTILINE,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr consume_uppercase_char_local", body, msg=label)
            self.assertIn("jsr match_line_end_local", body, msg=label)
            self.assertIn(expected_first_char, body, msg=label)
            self.assertNotIn("jsr read_scan_char_at_y", body, msg=label)
            self.assertNotIn("jsr uppercase_ascii_local", body, msg=label)
            self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

        line_end_helper_match = re.search(
            r"match_line_end_local:\n(?P<body>.*?)\npeek_decimal_digit_value_local:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(line_end_helper_match)
        assert line_end_helper_match is not None
        line_end_helper_body = line_end_helper_match.group("body")
        for expected in ("lda #$00", "lda #10", "lda #13"):
            self.assertIn(expected, line_end_helper_body)
        self.assertIn("jsr match_scan_char_local", line_end_helper_body)
        self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", line_end_helper_body)

        helper_match = re.search(
            r"consume_uppercase_char_local:\n(?P<body>.*?)\nuppercase_ascii_local:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("sta stored_byte_local", helper_body)
        self.assertIn("jsr read_scan_char_at_y", helper_body)
        self.assertIn("jsr uppercase_ascii_local", helper_body)
        self.assertIn("cmp stored_byte_local", helper_body)
        self.assertIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", helper_body)
        self.assertRegex(helper_body, r"\b(?:jsr|jmp) call_context_function\b")

    def test_body_collect_overlay_assignment_delimiters_use_local_source_reader_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_collect.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        dispatch_match = re.search(
            r"^collect_proc_body_ops_overlay_after_space_check:\n(?P<body>.*?)\n"
            r"^collect_proc_body_ops_overlay_local_skip_line:",
            overlay_text,
            re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(dispatch_match)
        assert dispatch_match is not None
        dispatch_body = dispatch_match.group("body")
        self.assertIn("jsr match_line_end_local", dispatch_body)
        self.assertIn("lda #'='", dispatch_body)
        self.assertIn("jsr match_scan_char_local", dispatch_body)
        self.assertNotIn("jsr read_scan_char_at_y", dispatch_body)
        self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", dispatch_body)

        delimiter_ranges = {
            "collect_proc_body_ops_overlay_try_assignment": (
                "collect_proc_body_ops_overlay_try_assignment_word:",
                ("lda #'='",),
                "jsr match_scan_char_local",
            ),
            "collect_proc_body_ops_overlay_local_after_equals": (
                "collect_proc_body_ops_overlay_try_local_int_parse_value:",
                ("lda #'='", "lda #'['", "lda #']'"),
                "jsr match_scan_char_local",
            ),
            "collect_proc_body_ops_overlay_try_assignment_word": (
                "collect_proc_body_ops_overlay_try_assignment_real:",
                ("lda #'='",),
                "jsr consume_scan_char_local",
            ),
            "collect_proc_body_ops_overlay_try_assignment_real": (
                "collect_proc_body_ops_overlay_try_local_call:",
                ("lda #'='",),
                "jsr consume_scan_char_local",
            ),
            "collect_proc_body_ops_overlay_try_local_call": (
                "collect_proc_body_ops_overlay_call_resolved:",
                ("lda #'('",),
                "jsr match_scan_char_local",
            ),
        }

        for label, (next_label, expected_chars, expected_helper) in delimiter_ranges.items():
            with self.subTest(label=label):
                match = re.search(
                    rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                    overlay_text,
                    re.DOTALL | re.MULTILINE,
                )
                self.assertIsNotNone(match, msg=label)
                assert match is not None
                body = match.group("body")
                for expected_char in expected_chars:
                    self.assertIn(expected_char, body, msg=label)
                self.assertIn(expected_helper, body, msg=label)
                if expected_helper == "jsr match_scan_char_local":
                    self.assertNotIn("jsr read_scan_char_at_y", body, msg=label)
                self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

        match_helper = re.search(
            r"match_scan_char_local:\n(?P<body>.*?)\n"
            r"peek_decimal_digit_value_local:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match_helper)
        assert match_helper is not None
        match_helper_body = match_helper.group("body")
        self.assertIn("sta stored_byte_local", match_helper_body)
        self.assertIn("jsr read_scan_char_at_y", match_helper_body)
        self.assertIn("cmp stored_byte_local", match_helper_body)
        self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", match_helper_body)
        self.assertNotIn("jsr call_context_function", match_helper_body)
        digit_helper_match = re.search(
            r"peek_decimal_digit_value_local:\n(?P<body>.*?)\n"
            r"consume_scan_char_local:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(digit_helper_match)
        assert digit_helper_match is not None
        digit_helper_body = digit_helper_match.group("body")
        self.assertIn("jsr read_scan_char_at_y", digit_helper_body)
        self.assertIn("cmp #'0'", digit_helper_body)
        self.assertIn("cmp #'9'+1", digit_helper_body)
        self.assertIn("sbc #'0'", digit_helper_body)
        self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", digit_helper_body)

        helper_match = re.search(
            r"consume_scan_char_local:\n(?P<body>.*?)\n"
            r"consume_uppercase_char_local:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("sta stored_byte_local", helper_body)
        self.assertIn("jsr read_scan_char_at_y", helper_body)
        self.assertIn("cmp stored_byte_local", helper_body)
        self.assertIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", helper_body)
        self.assertRegex(helper_body, r"\b(?:jsr|jmp) call_context_function\b")

    def test_body_collect_overlay_runtime_punctuation_uses_local_source_reader_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_collect.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        delimiter_ranges = {
            "emit_runtime_int_explicit_value_after_open_local_or_fail": (
                "emit_runtime_int_explicit_value_after_open_local_or_fail_fail:",
                ("lda #')'",),
            ),
            "emit_real_explicit_bridge_assignment_local_or_fail": (
                "emit_real_explicit_bridge_assignment_local_or_fail_fail:",
                ("lda #')'",),
            ),
            "emit_real_explicit_value_local_or_fail": (
                "emit_real_explicit_value_local_or_fail_wide:",
                ("lda #')'",),
            ),
            "emit_real_explicit_value_local_or_fail_wide": (
                "emit_real_explicit_value_local_or_fail_signed_prep:",
                ("lda #')'",),
            ),
            "emit_real_explicit_value_local_or_fail_signed_prep": (
                "emit_real_explicit_value_local_finish:",
                ("lda #'0'", "lda #'-'", "lda #')'"),
            ),
            "emit_runtime_real_unary_value_local_or_fail": (
                "emit_runtime_real_unary_value_local_or_fail_fail:",
                ("lda #')'",),
            ),
            "emit_runtime_real_binary_value_local_or_fail": (
                "emit_runtime_real_binary_value_local_or_fail_restore:",
                ("lda #'+'", "lda #'-'", "lda #'*'", "lda #'/'"),
            ),
            "emit_runtime_real_explicit_bridge_value_local_or_fail": (
                "emit_runtime_real_explicit_bridge_value_local_or_fail_fail:",
                ("lda #')'",),
            ),
            "emit_runtime_real_explicit_value_after_open_local_or_fail": (
                "emit_runtime_real_explicit_value_after_open_local_or_fail_wide:",
                ("lda #')'",),
            ),
            "emit_runtime_real_explicit_value_after_open_local_or_fail_wide": (
                "emit_runtime_real_explicit_value_after_open_local_or_fail_signed:",
                ("lda #')'",),
            ),
            "emit_runtime_real_explicit_value_after_open_local_or_fail_signed": (
                "emit_runtime_real_explicit_value_after_open_local_or_fail_zero:",
                ("lda #'0'", "lda #'-'", "lda #')'"),
            ),
            "store_runtime_real_print_with_newline_flag_local_or_fail": (
                "store_runtime_real_print_with_newline_flag_local_or_fail_fail:",
                ("lda #')'",),
            ),
            "emit_real_small_int_assignment_local_or_fail_signed": (
                "emit_real_small_int_assignment_local_or_fail_zero:",
                ("lda #'0'", "lda #'-'"),
            ),
        }
        matched_probe_labels = {
            "emit_runtime_int_explicit_value_after_open_local_or_fail",
            "emit_real_explicit_bridge_assignment_local_or_fail",
            "emit_real_explicit_value_local_or_fail",
            "emit_real_explicit_value_local_or_fail_wide",
            "emit_real_explicit_value_local_or_fail_signed_prep",
            "emit_runtime_real_unary_value_local_or_fail",
            "emit_runtime_real_binary_value_local_or_fail",
            "emit_runtime_real_explicit_bridge_value_local_or_fail",
            "emit_runtime_real_explicit_value_after_open_local_or_fail",
            "emit_runtime_real_explicit_value_after_open_local_or_fail_wide",
            "emit_runtime_real_explicit_value_after_open_local_or_fail_signed",
            "store_runtime_real_print_with_newline_flag_local_or_fail",
            "emit_real_small_int_assignment_local_or_fail_signed",
        }
        match_only_ranges = {
            "store_runtime_expr_with_a_local_or_fail_after_value": (
                "store_runtime_expr_with_a_local_or_fail_fail:",
                ("lda #')'",),
            ),
        }

        for label, (next_label, expected_checks) in match_only_ranges.items():
            with self.subTest(label=label):
                match = re.search(
                    rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                    overlay_text,
                    re.DOTALL | re.MULTILINE,
                )
                self.assertIsNotNone(match, msg=label)
                assert match is not None
                body = match.group("body")
                for expected_check in expected_checks:
                    self.assertIn(expected_check, body, msg=label)
                self.assertIn("jsr match_scan_char_local", body, msg=label)
                self.assertNotIn("jsr read_scan_char_at_y", body, msg=label)
                self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

        for label, (next_label, expected_checks) in delimiter_ranges.items():
            with self.subTest(label=label):
                match = re.search(
                    rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                    overlay_text,
                    re.DOTALL | re.MULTILINE,
                )
                self.assertIsNotNone(match, msg=label)
                assert match is not None
                body = match.group("body")
                for expected_check in expected_checks:
                    self.assertIn(expected_check, body, msg=label)
                if label in matched_probe_labels:
                    self.assertIn("jsr match_scan_char_local", body, msg=label)
                    self.assertNotIn("jsr read_scan_char_at_y", body, msg=label)
                self.assertIn("jsr consume_scan_char_local", body, msg=label)
                self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

    def test_body_collect_overlay_condition_and_keyword_consumes_use_local_source_reader_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_collect.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")

        condition_match = re.search(
            r"^emit_runtime_real_condition_clause_local_eq:\n(?P<body>.*?)\n"
            r"^emit_runtime_real_condition_clause_local_rhs:",
            overlay_text,
            re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(condition_match)
        assert condition_match is not None
        condition_body = condition_match.group("body")
        for expected in ("lda #'='", "lda #'<'", "lda #'>'"):
            self.assertIn(expected, condition_body)
        self.assertIn("jsr consume_scan_char_local", condition_body)
        self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", condition_body)
        condition_dispatch_match = re.search(
            r"^emit_runtime_real_condition_clause_local_or_fail:\n(?P<body>.*?)\n"
            r"^emit_runtime_real_condition_clause_local_eq:",
            overlay_text,
            re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(condition_dispatch_match)
        assert condition_dispatch_match is not None
        condition_dispatch_body = condition_dispatch_match.group("body")
        for expected in ("lda #'='", "lda #'<'", "lda #'>'"):
            self.assertIn(expected, condition_dispatch_body)
        self.assertIn("jsr match_scan_char_local", condition_dispatch_body)
        self.assertNotIn("jsr read_scan_char_at_y", condition_dispatch_body)
        self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", condition_dispatch_body)
        condition_ranges = {
            "emit_runtime_real_condition_clause_local_eq": (
                "emit_runtime_real_condition_clause_local_lt_entry:",
                "lda #'='",
                "jsr consume_scan_char_local",
            ),
            "emit_runtime_real_condition_clause_local_lt_entry": (
                "emit_runtime_real_condition_clause_local_gt_entry:",
                "lda #'<'",
                "jsr match_scan_char_local",
            ),
            "emit_runtime_real_condition_clause_local_gt_entry": (
                "emit_runtime_real_condition_clause_local_ne:",
                "lda #'>'",
                "jsr match_scan_char_local",
            ),
            "emit_runtime_real_condition_clause_local_ne": (
                "emit_runtime_real_condition_clause_local_le:",
                "lda #'>'",
                "jsr consume_scan_char_local",
            ),
            "emit_runtime_real_condition_clause_local_le": (
                "emit_runtime_real_condition_clause_local_ge:",
                "lda #'='",
                "jsr consume_scan_char_local",
            ),
            "emit_runtime_real_condition_clause_local_ge": (
                "emit_runtime_real_condition_clause_local_rhs:",
                "lda #'='",
                "jsr consume_scan_char_local",
            ),
        }
        for label, (next_label, expected, expected_helper) in condition_ranges.items():
            with self.subTest(label=label):
                match = re.search(
                    rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                    overlay_text,
                    re.DOTALL | re.MULTILINE,
                )
                self.assertIsNotNone(match, msg=label)
                assert match is not None
                body = match.group("body")
                self.assertIn(expected, body, msg=label)
                self.assertIn(expected_helper, body, msg=label)
                if expected_helper == "jsr match_scan_char_local":
                    self.assertNotIn("jsr read_scan_char_at_y", body, msg=label)
                self.assertIn("jsr consume_scan_char_local", body, msg=label)
                self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

        keyword_match = re.search(
            r"^consume_keyword_open_local:\n(?P<body>.*?)\n"
            r"^set_resident_const_ptr_from_ay:",
            overlay_text,
            re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(keyword_match)
        assert keyword_match is not None
        keyword_body = keyword_match.group("body")
        self.assertIn("jsr source_reader_begin_local_keyword_open", keyword_body)
        self.assertIn("jsr source_reader_local_pattern_char_from_index", keyword_body)
        self.assertIn("jsr source_reader_consume_local_pattern_char", keyword_body)
        self.assertIn("lda #'('", keyword_body)
        self.assertIn("jsr match_scan_char_local", keyword_body)
        self.assertIn("jsr consume_scan_char_local", keyword_body)
        self.assertNotIn("jsr read_scan_char_at_y", keyword_body)
        self.assertNotIn("sta reader_scan_y_local", keyword_body)
        self.assertNotIn("sta reader_pattern_index_local", keyword_body)
        self.assertNotIn("inc reader_pattern_index_local", keyword_body)
        self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", keyword_body)

        helper_ranges = {
            "source_reader_begin_local_keyword_open": (
                "source_reader_local_pattern_char_from_index:",
                [
                    "sta pattern_ptr_local",
                    "sty pattern_ptr_local+1",
                    "stx saved_x_local",
                    "sta reader_scan_y_local",
                    "sta reader_pattern_index_local",
                ],
            ),
            "source_reader_consume_local_pattern_char": (
                "source_reader_consume_local_pattern_char_fail:",
                [
                    "jsr source_reader_local_pattern_char_from_index",
                    "jsr consume_uppercase_char_local",
                    "sty reader_scan_y_local",
                    "inc reader_pattern_index_local",
                ],
            ),
        }
        for label, (next_label, expected_lines) in helper_ranges.items():
            helper_match = re.search(
                rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                overlay_text,
                re.DOTALL | re.MULTILINE,
            )
            self.assertIsNotNone(helper_match, msg=label)
            assert helper_match is not None
            helper_body = helper_match.group("body")
            for expected_line in expected_lines:
                self.assertIn(expected_line, helper_body, msg=label)
            if label == "source_reader_consume_local_pattern_char":
                self.assertNotIn("jsr read_scan_char_at_y", helper_body, msg=label)
                self.assertNotIn("jsr uppercase_ascii_local", helper_body, msg=label)

    def test_body_overlays_share_token_owned_positive_word_parser(self) -> None:
        actc_dir = self.root / "src" / "tools_udos" / "actc"
        include_text = (actc_dir / "actc_overlay_positive_word.inc").read_text(encoding="ascii")
        for overlay_name in (
            "actc_overlay_body_collect.asm",
            "actc_overlay_body_preallocate.asm",
        ):
            overlay_text = (actc_dir / overlay_name).read_text(encoding="ascii")
            self.assertIn('.include "actc_overlay_positive_word.inc"', overlay_text)
            self.assertNotIn("ACTC_OVERLAY_CTX_PARSE_POSITIVE_WORD_SUM_FN_LO", overlay_text)

        for label in (
            "parse_positive_word_sum_local_or_fail:",
            "parse_positive_word_term_local_or_fail:",
            "parse_positive_word_factor_local_or_fail:",
            "parse_optional_grouped_positive_word_sum_local_or_fail:",
        ):
            self.assertIn(label, include_text)
        for context_entry in (
            "ACTC_OVERLAY_CTX_SOURCE_READER_PEEK_TOKEN_FN_LO",
            "ACTC_OVERLAY_CTX_SOURCE_READER_CONSUME_TOKEN_FN_LO",
            "ACTC_OVERLAY_CTX_SOURCE_READER_TOKEN_VALUE_PTR_LO",
        ):
            self.assertIn(context_entry, include_text)
        self.assertNotIn("match_scan_char_local", include_text)
        self.assertNotIn("consume_scan_char_local", include_text)

    def test_body_collect_overlay_real_assignment_digit_dispatch_uses_local_source_reader_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_collect.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        match = re.search(
            r"^emit_real_assignment_local_or_fail:\n(?P<body>.*?)\n"
            r"^emit_real_binary_assignment_local_ok:",
            overlay_text,
            re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("lda #'('", body)
        self.assertIn("jsr match_scan_char_local", body)
        self.assertIn("jsr peek_decimal_digit_value_local", body)
        self.assertIn("jmp emit_real_small_int_assignment_local_or_fail", body)
        self.assertIn("jsr emit_runtime_real_value_local_or_fail", body)
        self.assertNotIn("cmp #'('", body)
        self.assertNotIn("cmp #'0'", body)
        self.assertNotIn("cmp #'9'+1", body)
        self.assertNotIn("jsr read_scan_char_at_y", body)
        self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body)

    def test_body_preallocate_overlay_terminator_keywords_use_local_source_reader_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_preallocate.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        terminator_ranges = {
            "preallocate_require_then_or_line_end_from_scan_y_overlay": (
                "preallocate_require_do_or_line_end_from_scan_y_overlay:",
                "lda #'T'",
            ),
            "preallocate_require_do_or_line_end_from_scan_y_overlay": (
                "preallocate_consume_upper_scan_char_from_y_overlay:",
                "lda #'D'",
            ),
        }

        for label, (next_label, expected_first_char) in terminator_ranges.items():
            match = re.search(
                rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                overlay_text,
                re.DOTALL | re.MULTILINE,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr preallocate_consume_upper_scan_char_from_y_overlay", body, msg=label)
            self.assertIn(expected_first_char, body, msg=label)
            self.assertNotIn("jsr uppercase_ascii_local", body, msg=label)
            self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

        helper_match = re.search(
            r"preallocate_consume_upper_scan_char_from_y_overlay:\n(?P<body>.*?)\nuppercase_ascii_local:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("sta compare_char_local", helper_body)
        self.assertIn("jsr read_scan_char_at_y", helper_body)
        self.assertIn("jsr uppercase_ascii_local", helper_body)
        self.assertIn("cmp compare_char_local", helper_body)
        self.assertIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", helper_body)
        self.assertIn("jmp call_context_function", helper_body)

    def test_body_preallocate_overlay_remaining_raw_read_calls_are_helper_owned(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_preallocate.asm"
        allowed_labels = {
            "preallocate_consume_upper_scan_char_from_y_overlay",
            "preallocate_match_scan_char_from_y_overlay",
            "preallocate_consume_scan_char_from_y_overlay",
        }
        labels_with_reads: list[str] = []
        offenders: list[str] = []
        current_label = "<file>"

        for line_number, line in enumerate(overlay_path.read_text(encoding="ascii").splitlines(), 1):
            label_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):", line)
            if label_match is not None:
                current_label = label_match.group(1)

            if "jsr read_scan_char_at_y" not in line:
                continue

            labels_with_reads.append(current_label)
            if current_label not in allowed_labels:
                offenders.append(f"{overlay_path.relative_to(self.root)}:{line_number}: {current_label}")

        self.assertEqual(offenders, [])
        self.assertEqual(set(labels_with_reads), allowed_labels)

    def test_body_preallocate_overlay_top_level_delimiters_use_local_source_reader_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_preallocate.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        dispatch_match = re.search(
            r"^preallocate_body_externals_overlay_not_proc:\n(?P<body>.*?)\n"
            r"^preallocate_body_externals_overlay_assignment:",
            overlay_text,
            re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(dispatch_match)
        assert dispatch_match is not None
        dispatch_body = dispatch_match.group("body")
        for expected_char in ("lda #'('", "lda #'='"):
            self.assertIn(expected_char, dispatch_body)
        self.assertIn("jsr preallocate_match_scan_char_from_y_overlay", dispatch_body)
        self.assertNotIn("jsr read_scan_char_at_y", dispatch_body)
        self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", dispatch_body)

        delimiter_ranges = {
            "preallocate_body_externals_overlay_assignment": (
                "preallocate_body_externals_overlay_scan_after_symbol:",
                "lda #'='",
            ),
            "preallocate_body_externals_overlay_print_statement": (
                "preallocate_body_externals_overlay_condition_statement:",
                "lda #'('",
            ),
            "preallocate_body_externals_overlay_call": (
                "preallocate_body_externals_overlay_skip_line:",
                "lda #'('",
            ),
        }

        for label, (next_label, expected_char) in delimiter_ranges.items():
            with self.subTest(label=label):
                match = re.search(
                    rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                    overlay_text,
                    re.DOTALL | re.MULTILINE,
                )
                self.assertIsNotNone(match, msg=label)
                assert match is not None
                body = match.group("body")
                self.assertIn(expected_char, body, msg=label)
                self.assertIn("jsr preallocate_consume_scan_char_from_y_overlay", body, msg=label)
                self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

        helper_match = re.search(
            r"preallocate_consume_scan_char_from_y_overlay:\n(?P<body>.*?)\n"
            r"uppercase_ascii_local:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("sta compare_char_local", helper_body)
        self.assertIn("jsr read_scan_char_at_y", helper_body)
        self.assertIn("cmp compare_char_local", helper_body)
        self.assertIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", helper_body)
        self.assertIn("jmp call_context_function", helper_body)

    def test_body_preallocate_overlay_assignment_entries_use_local_source_reader_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_preallocate.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        delimiter_ranges = {
            "preallocate_real_unary_assignment_external_from_declared_overlay": (
                "preallocate_real_unary_assignment_external_from_declared_overlay_done:",
                "lda #'='",
            ),
            "preallocate_word_int_assignment_external_from_declared_overlay": (
                "preallocate_word_int_assignment_external_from_declared_overlay_miss:",
                "lda #'='",
            ),
        }

        for label, (next_label, expected_char) in delimiter_ranges.items():
            with self.subTest(label=label):
                match = re.search(
                    rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                    overlay_text,
                    re.DOTALL | re.MULTILINE,
                )
                self.assertIsNotNone(match, msg=label)
                assert match is not None
                body = match.group("body")
                self.assertIn(expected_char, body, msg=label)
                self.assertIn("jsr preallocate_consume_scan_char_from_y_overlay", body, msg=label)
                self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

    def test_body_preallocate_overlay_conversion_print_delimiters_use_local_source_reader_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_preallocate.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        delimiter_ranges = {
            "preallocate_int_conversion_external_from_scan_y_overlay": (
                "preallocate_int_conversion_external_from_scan_y_overlay_miss:",
                ("lda #')'",),
            ),
            "preallocate_real_explicit_bridge_assignment_external_from_scan_y_overlay": (
                "preallocate_real_explicit_bridge_assignment_external_from_scan_y_overlay_miss:",
                ("lda #')'",),
            ),
            "preallocate_real_print_statement_external_from_declared_overlay": (
                "preallocate_real_print_statement_external_from_declared_overlay_miss:",
                ("lda #'('", "lda #')'"),
            ),
        }

        for label, (next_label, expected_chars) in delimiter_ranges.items():
            with self.subTest(label=label):
                match = re.search(
                    rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                    overlay_text,
                    re.DOTALL | re.MULTILINE,
                )
                self.assertIsNotNone(match, msg=label)
                assert match is not None
                body = match.group("body")
                for expected_char in expected_chars:
                    self.assertIn(expected_char, body, msg=label)
                self.assertIn("jsr preallocate_consume_scan_char_from_y_overlay", body, msg=label)
                self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

    def test_body_preallocate_overlay_shared_delimiter_helpers_use_local_source_reader_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_preallocate.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        delimiter_ranges = {
            "preallocate_consume_signed_word_prefix_from_scan_y_overlay": (
                "preallocate_consume_signed_word_prefix_from_scan_y_overlay_miss:",
                ("lda #'0'", "lda #'-'"),
            ),
            "preallocate_consume_close_and_line_end_from_scan_y_overlay": (
                "preallocate_consume_close_and_line_end_from_scan_y_overlay_miss:",
                ("lda #')'",),
            ),
            "preallocate_consume_close_from_scan_y_overlay": (
                "preallocate_consume_close_from_scan_y_overlay_miss:",
                ("lda #')'",),
            ),
            "preallocate_consume_keyword_open_from_scan_y_overlay": (
                "preallocate_consume_keyword_open_from_scan_y_overlay_miss:",
                ("lda #'('",),
            ),
        }

        for label, (next_label, expected_chars) in delimiter_ranges.items():
            with self.subTest(label=label):
                match = re.search(
                    rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                    overlay_text,
                    re.DOTALL | re.MULTILINE,
                )
                self.assertIsNotNone(match, msg=label)
                assert match is not None
                body = match.group("body")
                for expected_char in expected_chars:
                    self.assertIn(expected_char, body, msg=label)
                self.assertIn("jsr preallocate_consume_scan_char_from_y_overlay", body, msg=label)
                self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

    def test_body_preallocate_overlay_operator_delimiters_use_local_source_reader_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_preallocate.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        delimiter_ranges = {
            "preallocate_real_unary_print_external_from_scan_y_overlay": (
                "preallocate_real_unary_print_external_from_scan_y_overlay_miss:",
                ("lda #'('",),
            ),
            "preallocate_real_binary_print_external_from_scan_y_overlay": (
                "preallocate_real_binary_print_external_from_scan_y_overlay_miss:",
                ("lda #'+'", "lda #'-'", "lda #'*'", "lda #'/'"),
            ),
            "preallocate_real_condition_cmp_external_from_scan_y_overlay": (
                "preallocate_real_condition_cmp_external_from_scan_y_overlay_after_rhs:",
                ("lda #'='", "lda #'<'", "lda #'>'"),
            ),
            "preallocate_real_unary_operator_assignment_external_from_scan_y_overlay": (
                "preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_miss:",
                ("lda #'('", "lda #')'"),
            ),
            "preallocate_real_binary_operator_assignment_external_from_scan_y_overlay": (
                "preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_miss:",
                ("lda #'+'", "lda #'-'", "lda #'*'", "lda #'/'"),
            ),
        }
        matched_operator_labels = {
            "preallocate_real_binary_print_external_from_scan_y_overlay",
            "preallocate_real_condition_cmp_external_from_scan_y_overlay",
            "preallocate_real_binary_operator_assignment_external_from_scan_y_overlay",
        }

        for label, (next_label, expected_checks) in delimiter_ranges.items():
            with self.subTest(label=label):
                match = re.search(
                    rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                    overlay_text,
                    re.DOTALL | re.MULTILINE,
                )
                self.assertIsNotNone(match, msg=label)
                assert match is not None
                body = match.group("body")
                for expected_check in expected_checks:
                    self.assertIn(expected_check, body, msg=label)
                if label in matched_operator_labels:
                    self.assertIn("jsr preallocate_match_scan_char_from_y_overlay", body, msg=label)
                    self.assertNotIn("jsr read_scan_char_at_y", body, msg=label)
                self.assertIn("jsr preallocate_consume_scan_char_from_y_overlay", body, msg=label)
                self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

        suffix_ranges = {
            "preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_lt": (
                "preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_gt:",
                ("lda #'>'", "lda #'='"),
            ),
            "preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_gt": (
                "preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_second:",
                ("lda #'='",),
            ),
        }
        for label, (next_label, expected_chars) in suffix_ranges.items():
            with self.subTest(label=label):
                match = re.search(
                    rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                    overlay_text,
                    re.DOTALL | re.MULTILINE,
                )
                self.assertIsNotNone(match, msg=label)
                assert match is not None
                body = match.group("body")
                for expected_char in expected_chars:
                    self.assertIn(expected_char, body, msg=label)
                self.assertIn("jsr preallocate_match_scan_char_from_y_overlay", body, msg=label)
                self.assertIn("jsr preallocate_consume_scan_char_from_y_overlay", body, msg=label)
                self.assertNotIn("jsr read_scan_char_at_y", body, msg=label)
                self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

        match_helper = re.search(
            r"preallocate_match_scan_char_from_y_overlay:\n(?P<body>.*?)\n"
            r"preallocate_consume_scan_char_from_y_overlay:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match_helper)
        assert match_helper is not None
        match_helper_body = match_helper.group("body")
        self.assertIn("sta compare_char_local", match_helper_body)
        self.assertIn("jsr read_scan_char_at_y", match_helper_body)
        self.assertIn("cmp compare_char_local", match_helper_body)
        self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", match_helper_body)
        self.assertNotIn("jmp call_context_function", match_helper_body)

    def test_body_preallocate_overlay_call_arg_delimiters_use_local_source_reader_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_preallocate.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        delimiter_ranges = {
            "preallocate_plain_call_args_overlay_lparen": (
                "preallocate_plain_call_args_overlay_rparen:",
                ("lda #'('",),
            ),
            "preallocate_plain_call_args_overlay_rparen": (
                "preallocate_plain_call_args_overlay_done:",
                ("lda #')'",),
            ),
            "preallocate_line_call_args_overlay_symbol": (
                "preallocate_line_call_args_overlay_symbol_not_call:",
                ("lda #'('",),
            ),
            "preallocate_line_call_args_overlay_lparen": (
                "preallocate_line_call_args_overlay_rparen:",
                ("lda #'('",),
            ),
            "preallocate_line_call_args_overlay_rparen": (
                "preallocate_line_call_args_overlay_string:",
                ("lda #')'",),
            ),
            "preallocate_skip_string_in_plain_call_arg_overlay": (
                "preallocate_skip_string_in_plain_call_arg_overlay_loop:",
                ("lda #'\"'",),
            ),
            "preallocate_skip_string_in_plain_call_arg_overlay_close": (
                "preallocate_skip_string_in_plain_call_arg_overlay_done:",
                ("lda #'\"'",),
            ),
        }
        call_probe_ranges = {
            "preallocate_plain_call_args_overlay_symbol": (
                "preallocate_plain_call_args_overlay_symbol_not_call:",
            ),
            "preallocate_line_call_args_overlay_symbol": (
                "preallocate_line_call_args_overlay_symbol_not_call:",
            ),
        }

        for label, (next_label,) in call_probe_ranges.items():
            with self.subTest(label=label):
                match = re.search(
                    rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                    overlay_text,
                    re.DOTALL | re.MULTILINE,
                )
                self.assertIsNotNone(match, msg=label)
                assert match is not None
                body = match.group("body")
                self.assertIn("lda #'('", body, msg=label)
                self.assertIn("jsr preallocate_match_scan_char_from_y_overlay", body, msg=label)
                self.assertNotIn("jsr read_scan_char_at_y", body, msg=label)
                self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

        for label, (next_label, expected_chars) in delimiter_ranges.items():
            with self.subTest(label=label):
                match = re.search(
                    rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                    overlay_text,
                    re.DOTALL | re.MULTILINE,
                )
                self.assertIsNotNone(match, msg=label)
                assert match is not None
                body = match.group("body")
                for expected_char in expected_chars:
                    self.assertIn(expected_char, body, msg=label)
                self.assertIn("jsr preallocate_consume_scan_char_from_y_overlay", body, msg=label)
                self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

    def test_body_preallocate_overlay_call_arg_fallbacks_use_local_source_reader_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_preallocate.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        classifier_ranges = {
            "preallocate_plain_call_args_overlay_loop": (
                "preallocate_plain_call_args_overlay_consume_one:",
                ("lda #$00", "lda #10", "lda #13", "lda #'\"'", "lda #'('", "lda #')'"),
            ),
            "preallocate_line_call_args_overlay_loop": (
                "preallocate_line_call_args_overlay_consume_one:",
                ("lda #$00", "lda #10", "lda #13", "lda #'\"'", "lda #'('", "lda #')'"),
            ),
            "preallocate_skip_string_in_plain_call_arg_overlay_loop": (
                "preallocate_skip_string_in_plain_call_arg_overlay_close:",
                ("lda #$00", "lda #10", "lda #13", "lda #'\"'"),
            ),
        }
        fallback_ranges = {
            "preallocate_plain_call_args_overlay_consume_one": (
                "preallocate_plain_call_args_overlay_symbol:",
            ),
            "preallocate_line_call_args_overlay_consume_one": (
                "preallocate_line_call_args_overlay_symbol:",
            ),
            "preallocate_skip_string_in_plain_call_arg_overlay_loop": (
                "preallocate_skip_string_in_plain_call_arg_overlay_close:",
            ),
        }

        for label, (next_label, expected_chars) in classifier_ranges.items():
            with self.subTest(label=label):
                match = re.search(
                    rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                    overlay_text,
                    re.DOTALL | re.MULTILINE,
                )
                self.assertIsNotNone(match, msg=label)
                assert match is not None
                body = match.group("body")
                for expected_char in expected_chars:
                    self.assertIn(expected_char, body, msg=label)
                self.assertIn("jsr preallocate_match_scan_char_from_y_overlay", body, msg=label)
                self.assertNotIn("jsr read_scan_char_at_y", body, msg=label)
                self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

        for label, (next_label,) in fallback_ranges.items():
            with self.subTest(label=label):
                match = re.search(
                    rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                    overlay_text,
                    re.DOTALL | re.MULTILINE,
                )
                self.assertIsNotNone(match, msg=label)
                assert match is not None
                body = match.group("body")
                self.assertIn("jsr preallocate_advance_scan_char_from_y_overlay", body, msg=label)
                self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

        helper_match = re.search(
            r"preallocate_advance_scan_char_from_y_overlay:\n(?P<body>.*?)\n"
            r"uppercase_ascii_local:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", helper_body)
        self.assertIn("jmp call_context_function", helper_body)

    def test_payload_layout_overlay_payload_reads_go_through_local_peek(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_payload_layout.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        self.assertIn("payload_layout_peek_payload_y:", overlay_text)
        self.assertNotIn("ACTC_OVERLAY_CTX_SOURCE", overlay_text)
        self.assertNotIn("LOAD_NEXT_SOURCE", overlay_text)
        self.assertIn("ACTC_OVERLAY_CTX_BODY_PTR_SLOT_PTR", overlay_text)
        raw_positions = [
            match.start()
            for match in re.finditer(r"\blda \(ACTC_OVERLAY_SCAN_ZP\),y", overlay_text)
        ]
        helper_match = re.search(
            r"payload_layout_peek_payload_y:\n(?P<body>.*?)\nstore_layout_locals_to_resident:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_start, helper_end = helper_match.span("body")
        self.assertTrue(raw_positions)
        self.assertTrue(all(helper_start <= pos < helper_end for pos in raw_positions))

        match = re.search(
            r"compute_payload_layout_overlay:\n(?P<body>.*?)\ncompute_payload_layout_overlay_bad:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr payload_layout_peek_payload_y", body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body)

    def test_emit_object_overlay_payload_reads_go_through_local_peek(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_emit_object.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        self.assertIn("emit_object_peek_payload_y:", overlay_text)
        self.assertNotIn("ACTC_OVERLAY_CTX_SOURCE", overlay_text)
        self.assertNotIn("LOAD_NEXT_SOURCE", overlay_text)
        self.assertIn("ACTC_OVERLAY_CTX_BODY_PTR_SLOT_PTR", overlay_text)
        raw_positions = [
            match.start()
            for match in re.finditer(r"\blda \(ACTC_OVERLAY_SCAN_ZP\),y", overlay_text)
        ]
        helper_match = re.search(
            r"emit_object_peek_payload_y:\n(?P<body>.*?)\nactc_overlay_end:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_start, helper_end = helper_match.span("body")
        self.assertTrue(raw_positions)
        self.assertTrue(all(helper_start <= pos < helper_end for pos in raw_positions))

        for label, next_label in {
            "emit_body_ops_list_standard": "emit_machine_code_list:",
            "emit_scan_zp_string": "emit_scan_zp_string_done:",
            "emit_lower_scan_zp_string": "emit_lower_scan_zp_string_done:",
            "is_empty_main_machine_object": "is_empty_main_machine_object_yes:",
            "scan_zp_is_return_body": "scan_zp_is_return_body_yes:",
            "scan_zp_is_local_call_sequence_return_body": "emit_count_local_call_sequence_body:",
        }.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                overlay_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr emit_object_peek_payload_y", body, msg=label)
            self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body, msg=label)

    def test_source_scanning_overlays_reset_source_reader_before_running(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        source_overlay_ranges = {
            "collect_decls_with_overlay_if_possible": "collect_decls_with_overlay_fallback:",
            "detect_runtime_imports_with_overlay_if_possible": "detect_runtime_imports_with_overlay_ok:",
            "collect_proc_body_ops_with_overlay_if_possible": "collect_proc_body_ops_with_overlay_fallback:",
        }

        for label, next_label in source_overlay_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{next_label}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr source_reader_reset_to_start", body, msg=label)
            self.assertIn("jsr actc_overlay_run_pass", body, msg=label)
            self.assertLess(
                body.index("jsr source_reader_reset_to_start"),
                body.index("jsr actc_overlay_run_pass"),
                msg=label,
            )

    def test_body_overlay_advance_contexts_route_through_source_reader_consume(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        context_targets = {
            "ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_FN": "source_reader_consume_scan_ptr",
            "ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_BY_CONST_FN": "source_reader_consume_const_ptr_at_scan_ptr",
            "ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN": "source_reader_consume_scan_y",
            "ACTC_OVERLAY_CTX_PEEK_SCAN_Y_FN": "source_reader_peek_scan_y",
        }

        for context_name, target_name in context_targets.items():
            self.assertRegex(
                actc_text,
                rf"lda #<{target_name}\n"
                rf"\s+sta actc_overlay_context\+{context_name}_LO\n"
                rf"\s+lda #>{target_name}\n"
                rf"\s+sta actc_overlay_context\+{context_name}_HI",
                msg=context_name,
            )

    def test_body_overlay_local_pattern_advances_route_through_source_reader_context(self) -> None:
        overlay_paths = [
            self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_collect.asm",
            self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_preallocate.asm",
        ]

        for overlay_path in overlay_paths:
            with self.subTest(path=overlay_path.name):
                overlay_text = overlay_path.read_text(encoding="ascii")
                self.assertIn("jsr source_reader_consume_local_pattern", overlay_text)
                helper_match = re.search(
                    r"source_reader_consume_local_pattern:\n(?P<body>.*?)\n"
                    r"symbol_buffer_matches_local_const:",
                    overlay_text,
                    re.DOTALL,
                )
                self.assertIsNotNone(helper_match)
                assert helper_match is not None
                body = helper_match.group("body")
                self.assertIn("jsr set_resident_const_ptr_from_ay", body)
                self.assertIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_BY_CONST_FN_LO", body)
                self.assertIn("jmp call_context_function", body)
                self.assertNotIn("jsr advance_source_scan", body)
                self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body)
                self.assertNotIn("sta (ACTC_OVERLAY_SCAN_ZP),y", body)

    def test_assignment_delimiters_consume_through_source_reader(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        delimiter_ranges = {
            "collect_proc_body_ops_try_local_int_assignment": (
                "collect_proc_body_ops_try_local_int_parse_value:",
                ["lda #'='", "lda #'['", "lda #']'"],
            ),
            "collect_proc_body_ops_try_local_real_assignment": (
                "collect_proc_body_ops_try_od:",
                ["lda #'='"],
            ),
            "collect_proc_body_ops_try_assignment_word": (
                "collect_proc_body_ops_try_local_call:",
                ["lda #'='"],
            ),
        }

        for label, (next_label, expected_lines) in delimiter_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{next_label}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            for expected in expected_lines:
                self.assertIn(expected, body, msg=label)
            self.assertIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
            if label == "collect_proc_body_ops_try_local_int_assignment":
                self.assertNotIn("cmp #']'", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

    def test_module_var_initializer_punctuation_uses_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"store_module_var_from_scan_ptr_or_fail_save_name_done:\n(?P<body>.*?)\n"
            r"store_module_var_from_scan_ptr_or_fail_parse_value:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        for expected in ("lda #SOURCE_TOKEN_EQ", "lda #'['", "lda #']'"):
            self.assertIn(expected, body)
        self.assertIn("jsr source_reader_peek_token_from_scan_y", body)
        self.assertIn("jsr source_reader_consume_expected_token_from_scan_y", body)
        self.assertNotIn("jsr source_reader_peek_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("cmp #']'", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_preallocate_assignment_equals_uses_expected_char_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        assignment_ranges = {
            "preallocate_consume_real_assignment_equals_from_declared": (
                "preallocate_consume_real_assignment_equals_from_declared_miss:",
            ),
            "preallocate_consume_word_assignment_equals_from_declared": (
                "preallocate_consume_word_assignment_equals_from_declared_miss:",
            ),
        }

        for label, (next_label,) in assignment_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("lda #'='", body, msg=label)
            self.assertIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

    def test_runtime_expression_operators_use_expected_char_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        operator_ranges = {
            "store_small_runtime_expr_compare_entry": (
                "store_small_runtime_expr_rhs:",
                ["lda #'='", "lda #'<'", "lda #'>'"],
            ),
            "store_runtime_real_print_with_newline_flag_from_scan_ptr": (
                "store_runtime_real_print_with_newline_flag_zero:",
                ["lda #')'"],
            ),
        }

        for label, (next_label, expected_chars) in operator_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{next_label}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            for expected in expected_chars:
                self.assertIn(expected, body, msg=label)
            self.assertIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
            if label == "store_runtime_real_print_with_newline_flag_from_scan_ptr":
                self.assertNotIn("cmp #')'", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

    def test_small_runtime_print_closes_use_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        close_ranges = {
            "store_small_runtime_expr_sum_entry": "store_small_runtime_expr_compare_entry:",
            "store_small_runtime_expr_rhs": "store_small_runtime_expr_print:",
            "store_small_runtime_expr_bool_entry": "store_small_runtime_expr_consume_close_from_scan_y:",
        }

        for label, next_label in close_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr store_small_runtime_expr_consume_close_from_scan_y", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

        helper_match = re.search(
            r"store_small_runtime_expr_consume_close_from_scan_y:\n(?P<body>.*?)\n"
            r"store_small_runtime_condition_with_a_from_scan_ptr:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("lda #']'", helper_body)
        self.assertIn("lda #')'", helper_body)
        self.assertIn("jsr source_reader_consume_expected_token_from_scan_y", helper_body)
        self.assertIn("jmp source_reader_consume_expected_token_from_scan_y", helper_body)
        self.assertNotIn("jsr source_reader_consume_char_from_scan_y", helper_body)

    def test_statement_terminator_keywords_consume_through_source_reader(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        terminator_ranges = {
            "preallocate_require_then_or_line_end_at_scan_y": (
                "preallocate_require_do_or_line_end_at_scan_y:",
                "lda #'T'",
            ),
            "preallocate_require_do_or_line_end_at_scan_y": (
                "preallocate_declared_symbol_is_print_statement:",
                "lda #'D'",
            ),
            "require_then_or_line_end_at_scan_y": (
                "require_do_or_line_end_at_scan_y:",
                "lda #'T'",
            ),
            "require_do_or_line_end_at_scan_y": (
                ".endif",
                "lda #'D'",
            ),
        }

        for label, (next_label, expected_first_char) in terminator_ranges.items():
            match = re.search(
                rf"^{re.escape(label)}:\n(?P<body>.*?)\n^{re.escape(next_label)}",
                actc_text,
                re.DOTALL | re.MULTILINE,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr source_reader_consume_uppercase_char_from_scan_y", body, msg=label)
            self.assertIn(expected_first_char, body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr uppercase_ascii", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

        helper_match = re.search(
            r"source_reader_consume_uppercase_char_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_consume_pattern_char_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("sta compare_char", helper_body)
        self.assertIn("jsr source_reader_peek_scan_y", helper_body)
        self.assertIn("jsr uppercase_ascii", helper_body)
        self.assertIn("cmp compare_char", helper_body)
        self.assertIn("jsr source_reader_consume_scan_y", helper_body)
        self.assertNotIn("jsr advance_scan_y", helper_body)

    def test_runtime_value_punctuation_uses_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"emit_runtime_value_from_scan_y_or_fail:\n(?P<body>.*?)\n"
            r"emit_small_constant_sum_from_scan_y_or_fail:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("lda #SOURCE_TOKEN_EQ", body)
        self.assertIn("lda #'['", body)
        self.assertIn("lda #']'", body)
        self.assertIn("jsr source_reader_consume_expected_token_from_scan_y", body)
        self.assertNotIn("jsr source_reader_match_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_peek_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("cmp #']'", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_small_constant_sum_terminators_use_source_reader_match_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"emit_small_constant_sum_from_scan_y_or_fail:\n(?P<body>.*?)\n"
            r"emit_small_constant_sum_from_scan_y_or_fail_ok:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        for expected in ("lda #','", "lda #')'", "lda #']'"):
            self.assertIn(expected, body)
        self.assertIn("jsr source_reader_match_char_from_scan_y", body)
        self.assertNotIn("cmp #','", body)
        self.assertNotIn("cmp #')'", body)
        self.assertNotIn("cmp #']'", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_runtime_sum_operators_use_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"emit_runtime_sum_from_scan_y_or_fail:\n(?P<body>.*?)\n"
            r"store_expr_value_as_int_literal:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_peek_token_from_scan_y", body)
        self.assertIn("cmp #'+'", body)
        self.assertIn("cmp #'-'", body)
        self.assertIn("jsr source_reader_consume_token_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_peek_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_runtime_product_operators_use_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"emit_runtime_product_from_scan_y_or_fail:\n(?P<body>.*?)\n"
            r"store_expr_value_as_int_literal:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_peek_token_from_scan_y", body)
        self.assertIn("cmp #'*'", body)
        self.assertIn("cmp #'/'", body)
        self.assertIn("jsr source_reader_consume_token_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_peek_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_small_value_punctuation_uses_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"parse_small_value_expr_at_scan_y:\n(?P<body>.*?)\n"
            r"normalize_small_expr_value_to_bool:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("lda #SOURCE_TOKEN_EQ", body)
        self.assertIn("lda #'['", body)
        self.assertIn("lda #']'", body)
        self.assertIn("jsr source_reader_consume_expected_token_from_scan_y", body)
        self.assertNotIn("jsr source_reader_match_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_peek_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("cmp #']'", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_small_decimal_literal_probe_restores_source_reader_on_failure(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"store_small_decimal_literal_from_scan_ptr:\n(?P<body>.*?)\n"
            r"store_zero_int_literal:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertLess(
            body.index("jsr source_reader_save_literal_probe_mark"),
            body.index("jsr parse_small_value_expr_at_scan_y"),
        )
        fail_body = body.split("store_small_decimal_literal_from_scan_ptr_fail:", 1)[1]
        self.assertIn("jsr source_reader_restore_literal_probe_mark", fail_body)

        helper_match = re.search(
            r"source_reader_save_literal_probe_mark:\n(?P<save>.*?)\n"
            r"source_reader_restore_literal_probe_mark:\n(?P<restore>.*?)\n"
            r"save_reader_probe_mark:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        save_body = helper_match.group("save")
        restore_body = helper_match.group("restore")
        for state_name in (
            "literal_probe_scan_ptr_lo_data",
            "literal_probe_scan_ptr_hi_data",
            "literal_probe_window_start_data",
        ):
            self.assertIn(state_name, save_body)
            self.assertIn(state_name, restore_body)
        self.assertIn("jsr source_reader_load_next_window", restore_body)
        self.assertIn("sta reader_lookahead_valid_data", restore_body)

    def test_small_runtime_print_wrapper_punctuation_uses_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"store_small_runtime_expr_from_scan_ptr:\n(?P<body>.*?)\n"
            r"store_small_runtime_condition_with_a_from_scan_ptr:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        for expected in ("lda #SOURCE_TOKEN_EQ", "lda #'['", "lda #']'", "lda #')'"):
            self.assertIn(expected, body)
        self.assertIn("sta expr_runtime_wrapped_data", body)
        self.assertGreaterEqual(
            body.count("jsr source_reader_consume_expected_token_from_scan_y"),
            2,
        )
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_small_bool_group_punctuation_uses_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"parse_small_bool_primary_at_scan_y:\n(?P<body>.*?)\n"
            r"parse_small_condition_clause_at_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_peek_token_from_scan_y", body)
        self.assertIn("cmp #'('", body)
        self.assertIn("cmp #')'", body)
        self.assertIn("jsr source_reader_consume_token_from_scan_y", body)
        self.assertIn("jsr source_reader_token_is_comparison_operator", body)
        self.assertNotIn("jsr source_reader_match_open_paren_from_scan_y", body)
        self.assertNotIn("jsr source_reader_match_comparison_operator_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_boolean_keyword_consumption_uses_complete_symbol_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"consume_keyword_from_scan_y:\n(?P<body>.*?)\n"
            r"symbol_buffer_matches_const_ptr:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr save_source_reader_mark", body)
        self.assertIn("jsr source_reader_peek_token_from_scan_y", body)
        self.assertIn("cmp #SOURCE_TOKEN_SYMBOL", body)
        self.assertIn("jsr source_reader_token_buffer_matches_const_ptr", body)
        self.assertIn("jsr source_reader_consume_token_from_scan_y", body)
        self.assertIn("jsr restore_source_reader_mark", body)
        self.assertNotIn("jsr copy_symbol_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_small_value_parsers_share_token_comparison_tail(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        ranges = {
            "parse_small_condition_clause_at_scan_y": "parse_small_decimal_expr_at_scan_y:",
            "parse_small_decimal_expr_at_scan_y": "parse_small_comparison_tail_at_scan_y:",
        }
        for label, next_label in ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr parse_small_decimal_sum_at_scan_y", body, msg=label)
            if label == "parse_small_condition_clause_at_scan_y":
                self.assertIn("jmp parse_small_comparison_tail_at_scan_y", body)
            self.assertNotIn("source_reader_match_comparison_operator_from_scan_y", body)
            self.assertNotIn("source_reader_consume_char_from_scan_y", body)

    def test_small_comparison_operators_use_complete_source_reader_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"parse_small_comparison_tail_at_scan_y:\n(?P<body>.*?)\n"
            r"parse_small_decimal_sum_at_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_peek_token_from_scan_y", body)
        self.assertIn("jsr source_reader_token_is_comparison_operator", body)
        self.assertIn("jsr source_reader_consume_token_from_scan_y", body)

        classifier_match = re.search(
            r"source_reader_token_is_comparison_operator:\n(?P<body>.*?)\n"
            r"source_reader_match_open_paren_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(classifier_match)
        assert classifier_match is not None
        classifier_body = classifier_match.group("body")
        for token in (
            "SOURCE_TOKEN_EQ",
            "SOURCE_TOKEN_LT",
            "SOURCE_TOKEN_GT",
            "SOURCE_TOKEN_LE",
            "SOURCE_TOKEN_GE",
            "SOURCE_TOKEN_NE",
        ):
            self.assertIn(f"cmp #{token}", classifier_body)
        self.assertIn("pha", body)
        self.assertIn("pla", body)
        self.assertNotIn("source_reader_match_comparison_operator_from_scan_y", body)
        self.assertNotIn("source_reader_match_comparison_suffix_from_scan_y", body)
        self.assertNotIn("source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_small_decimal_arithmetic_operators_use_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        ranges = {
            "parse_small_decimal_sum_at_scan_y": (
                "parse_small_decimal_term_at_scan_y:",
                ["cmp #'+'", "cmp #'-'"],
            ),
            "parse_small_decimal_term_at_scan_y": (
                "parse_small_decimal_factor_at_scan_y:",
                ["cmp #'*'", "cmp #'/'"],
            ),
        }

        for label, (next_label, expected_literals) in ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr source_reader_peek_token_from_scan_y", body, msg=label)
            self.assertIn("jsr source_reader_consume_token_from_scan_y", body, msg=label)
            self.assertIn("pha", body, msg=label)
            self.assertIn("pla", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)
            for expected in expected_literals:
                self.assertIn(expected, body, msg=label)

    def test_numeric_sum_terminators_use_source_reader_match_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        helper_match = re.search(
            r"source_reader_match_numeric_sum_stop_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_consume_char_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr source_reader_peek_scan_y", helper_body)
        for expected in ("cmp #','", "cmp #')'", "cmp #']'", "cmp #'='", "cmp #'<'", "cmp #'>'"):
            self.assertIn(expected, helper_body)

        small_match = re.search(
            r"parse_small_decimal_sum_loop:\n(?P<body>.*?)\n"
            r"parse_small_decimal_sum_try_and:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(small_match)
        assert small_match is not None
        small_body = small_match.group("body")
        self.assertIn("jsr source_reader_peek_token_from_scan_y", small_body)
        self.assertIn("jsr source_reader_token_is_numeric_sum_stop", small_body)
        self.assertIn("cmp #SOURCE_TOKEN_SYMBOL", small_body)
        self.assertNotIn("source_reader_match_numeric_sum_stop_from_scan_y", small_body)
        self.assertNotIn("jsr source_reader_consume_scan_y", small_body)
        self.assertNotIn("jsr advance_scan_y", small_body)

        keyword_match = re.search(
            r"parse_small_decimal_sum_try_and:\n(?P<body>.*?)\n"
            r"parse_small_decimal_sum_add:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(keyword_match)
        assert keyword_match is not None
        keyword_body = keyword_match.group("body")
        self.assertEqual(keyword_body.count("jsr source_reader_token_buffer_matches_const_ptr"), 2)
        self.assertNotIn("jsr scan_keyword_token_from_scan_y", keyword_body)

        positive_match = re.search(
            r"parse_positive_word_sum_loop:\n(?P<body>.*?)\nparse_positive_word_sum_add:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(positive_match)
        assert positive_match is not None
        positive_body = positive_match.group("body")
        self.assertIn("jsr source_reader_peek_token_from_scan_y", positive_body)
        self.assertIn("jsr source_reader_token_is_numeric_sum_stop", positive_body)
        self.assertNotIn("source_reader_match_numeric_sum_stop_from_scan_y", positive_body)

        token_stop_match = re.search(
            r"source_reader_token_is_numeric_sum_stop:\n(?P<body>.*?)\n"
            r"source_reader_token_is_numeric_sum_stop_yes:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(token_stop_match)
        assert token_stop_match is not None
        token_stop_body = token_stop_match.group("body")
        for token in (
            "SOURCE_TOKEN_EOF",
            "SOURCE_TOKEN_LINE_END",
        ):
            self.assertIn(f"cmp #{token}", token_stop_body)
        for punctuation in ("cmp #','", "cmp #')'", "cmp #']'"):
            self.assertIn(punctuation, token_stop_body)
        self.assertIn("jmp source_reader_token_is_comparison_operator", token_stop_body)

    def test_small_decimal_group_punctuation_uses_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"parse_small_decimal_factor_group:\n(?P<body>.*?)\n"
            r"parse_small_decimal_factor_at_scan_y_fail:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_peek_token_from_scan_y", body)
        self.assertIn("cmp #')'", body)
        self.assertIn("jsr source_reader_consume_token_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_positive_word_arithmetic_operators_use_token_lookahead(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        ranges = {
            "parse_positive_word_sum_at_scan_y": (
                "parse_positive_word_term_at_scan_y:",
                ["cmp #'+'", "cmp #'-'"],
            ),
            "parse_positive_word_term_at_scan_y": (
                "parse_positive_word_factor_at_scan_y:",
                ["cmp #'*'", "cmp #'/'"],
            ),
        }

        for label, (next_label, expected_literals) in ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr source_reader_peek_token_from_scan_y", body, msg=label)
            self.assertIn("jsr source_reader_consume_token_from_scan_y", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)
            for expected in expected_literals:
                self.assertIn(expected, body, msg=label)
            if label == "parse_positive_word_sum_at_scan_y":
                self.assertIn("expr_word_sum_lo", body)
                self.assertIn("expr_word_sum_hi", body)
            else:
                self.assertIn("expr_compare_lo", body)
                self.assertIn("expr_compare_hi", body)

    def test_positive_word_group_punctuation_uses_token_lookahead(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        ranges = {
            "parse_positive_word_factor_group": "parse_optional_grouped_positive_word_sum_at_scan_y:",
            "parse_optional_grouped_positive_word_sum_at_scan_y": "parse_positive_word_decimal_at_scan_y:",
        }

        for label, next_label in ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr source_reader_peek_token_from_scan_y", body, msg=label)
            self.assertIn("jsr source_reader_consume_token_from_scan_y", body, msg=label)
            self.assertIn("cmp #')'", body, msg=label)
            self.assertNotIn("jsr source_reader_match_open_paren_from_scan_y", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

    def test_runtime_real_open_keyword_uses_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"try_consume_real_open_for_runtime_condition_from_scan_y:\n(?P<body>.*?)\n"
            r"try_consume_real_open_for_runtime_condition_from_scan_y_fail_restore:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("lda #<pattern_real_decl", body)
        self.assertIn("lda #>pattern_real_decl", body)
        self.assertIn("jsr consume_keyword_open_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_uppercase_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_runtime_real_bridge_close_paren_uses_complete_token(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"emit_runtime_real_explicit_bridge_value_from_scan_y_or_fail:\n(?P<body>.*?)\n"
            r"emit_runtime_real_explicit_bridge_value_from_scan_y_or_fail_fail:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("lda #')'", body)
        self.assertIn("jsr source_reader_consume_expected_token_from_scan_y", body)
        self.assertNotIn("cmp #')'", body)
        self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_runtime_real_explicit_value_tokens_use_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail:\n(?P<body>.*?)\n"
            r"emit_runtime_real_value_from_scan_y_or_fail:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        for expected in ("lda #')'", "lda #'-'"):
            self.assertIn(expected, body)
        self.assertIn("jsr source_reader_consume_single_zero_decimal_from_scan_y", body)
        self.assertIn("jsr source_reader_consume_expected_token_from_scan_y", body)
        self.assertGreaterEqual(body.count("jsr source_reader_consume_expected_token_from_scan_y"), 4)
        self.assertNotIn("cmp #')'", body)
        self.assertNotIn("cmp #'0'", body)
        self.assertNotIn("cmp #'-'", body)
        self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

        zero_match = re.search(
            r"source_reader_consume_single_zero_decimal_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_consume_single_zero_decimal_from_scan_y_fail:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(zero_match)
        assert zero_match is not None
        zero_body = zero_match.group("body")
        self.assertIn("jsr source_reader_peek_token_from_scan_y", zero_body)
        self.assertIn("cmp #SOURCE_TOKEN_DECIMAL", zero_body)
        self.assertIn("lda reader_lookahead_length_data", zero_body)
        self.assertIn("cmp #$01", zero_body)
        self.assertIn("lda reader_lookahead_value_lo_data", zero_body)
        self.assertIn("ora reader_lookahead_value_hi_data", zero_body)
        self.assertIn("jmp source_reader_consume_token_from_scan_y", zero_body)
        self.assertNotIn("jsr source_reader_consume_scan_y", zero_body)

    def test_runtime_real_condition_operators_use_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"emit_runtime_real_condition_clause_from_scan_y_or_fail:\n(?P<body>.*?)\n"
            r"emit_runtime_condition_clause_from_scan_y_or_fail:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_peek_token_from_scan_y", body)
        self.assertIn("jsr source_reader_token_is_comparison_operator", body)
        self.assertIn("jsr source_reader_consume_token_from_scan_y", body)
        for token in (
            "SOURCE_TOKEN_EQ",
            "SOURCE_TOKEN_LT",
            "SOURCE_TOKEN_GT",
            "SOURCE_TOKEN_LE",
            "SOURCE_TOKEN_GE",
        ):
            self.assertIn(f"cpx #{token}", body)
        for runtime_op in ("lda #'q'", "lda #'l'", "lda #'g'", "lda #'n'"):
            self.assertIn(runtime_op, body)
        store_match = re.search(
            r"emit_runtime_real_condition_clause_store_op:\n(?P<body>.*?)\n"
            r"emit_runtime_real_condition_clause_rhs:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(store_match)
        assert store_match is not None
        store_body = store_match.group("body")
        self.assertIn("lda expr_value_lo\n    pha", store_body)
        self.assertIn("jsr source_reader_consume_token_from_scan_y", store_body)
        self.assertIn("pla\nemit_runtime_real_condition_clause_fail:", store_body)

        rhs_match = re.search(
            r"emit_runtime_real_condition_clause_rhs:\n(?P<body>.*?)\n"
            r"emit_runtime_condition_clause_from_scan_y_or_fail:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(rhs_match)
        assert rhs_match is not None
        rhs_body = rhs_match.group("body")
        self.assertIn("jsr emit_runtime_real_value_from_scan_y_or_fail", rhs_body)
        self.assertIn("pla\n    sta expr_value_lo", rhs_body)
        self.assertNotIn("jsr source_reader_match_comparison_operator_from_scan_y", body)
        self.assertNotIn("jsr source_reader_match_comparison_suffix_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_runtime_condition_operators_use_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"emit_runtime_condition_clause_from_scan_y_or_fail:\n(?P<body>.*?)\n"
            r"emit_runtime_condition_clause_done:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_peek_token_from_scan_y", body)
        self.assertIn("jsr source_reader_token_is_comparison_operator", body)
        self.assertIn("jsr source_reader_consume_token_from_scan_y", body)
        for token in (
            "SOURCE_TOKEN_EQ",
            "SOURCE_TOKEN_LT",
            "SOURCE_TOKEN_GT",
            "SOURCE_TOKEN_LE",
            "SOURCE_TOKEN_GE",
        ):
            self.assertIn(f"cpx #{token}", body)
        for runtime_op in ("lda #'q'", "lda #'l'", "lda #'g'", "lda #'n'"):
            self.assertIn(runtime_op, body)
        self.assertNotIn("jsr source_reader_match_comparison_operator_from_scan_y", body)
        self.assertNotIn("jsr source_reader_match_comparison_suffix_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_runtime_call_arg_punctuation_uses_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"emit_call_args_from_scan_y_or_fail:\n(?P<body>.*?)\n"
            r"emit_runtime_value_from_scan_y_or_fail:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        for expected in ("lda #'('", "lda #','", "lda #')'"):
            self.assertIn(expected, body)
        self.assertIn("jsr source_reader_consume_expected_token_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

        helper_match = re.search(
            r"source_reader_consume_expected_token_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_consume_token_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr source_reader_peek_token_from_scan_y", helper_body)
        self.assertIn("cmp compare_char", helper_body)
        self.assertIn("jmp source_reader_consume_token_from_scan_y", helper_body)
        self.assertNotIn("jsr source_reader_peek_scan_y", helper_body)

    def test_runtime_group_punctuation_uses_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"emit_runtime_group_value_term_from_scan_y_or_fail:\n(?P<body>.*?)\n"
            r"emit_runtime_call_term_from_scan_y_or_fail:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_peek_token_from_scan_y", body)
        self.assertIn("cmp #'('", body)
        self.assertIn("cmp #')'", body)
        self.assertIn("jsr source_reader_consume_token_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_runtime_bool_primary_group_punctuation_uses_complete_tokens(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"emit_runtime_bool_primary_from_scan_y_or_fail:\n(?P<body>.*?)\n"
            r"\.if ACTC_KEEP_BODY_RESIDENT_FALLBACK",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_peek_token_from_scan_y", body)
        self.assertIn("cmp #'('", body)
        self.assertIn("cmp #')'", body)
        self.assertIn("jsr source_reader_consume_token_from_scan_y", body)
        self.assertIn("jsr source_reader_token_is_comparison_operator", body)
        self.assertNotIn("jsr source_reader_match_open_paren_from_scan_y", body)
        self.assertNotIn("jsr source_reader_match_comparison_operator_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_preallocate_call_arg_delimiters_use_expected_char_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        helper_match = re.search(
            r"source_reader_consume_char_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_consume_uppercase_char_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("sta compare_char", helper_body)
        self.assertIn("jsr source_reader_peek_scan_y", helper_body)
        self.assertIn("cmp compare_char", helper_body)
        self.assertIn("jsr source_reader_consume_scan_y", helper_body)
        self.assertNotIn("jsr uppercase_ascii", helper_body)

        exact_punctuation_ranges = {
            "preallocate_call_with_arg_externals_from_scan_y": (
                "preallocate_plain_call_externals_from_declared:",
                ["lda #'('"],
            ),
            "preallocate_plain_call_externals_from_declared": (
                "preallocate_plain_call_arg_externals_from_scan_y:",
                ["lda #'('"],
            ),
            "preallocate_plain_call_arg_externals_from_scan_y": (
                "preallocate_scan_plain_call_arg_for_externals_from_scan_y:",
                ["lda #','", "lda #')'"],
            ),
        }

        for label, (next_label, expected_literals) in exact_punctuation_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            if label == "preallocate_plain_call_arg_externals_from_scan_y":
                self.assertNotIn("cmp #','", body, msg=label)
                self.assertNotIn("cmp #')'", body, msg=label)
            for expected in expected_literals:
                self.assertIn(expected, body, msg=label)

        scanner_delimiter_ranges = {
            "preallocate_scan_plain_call_arg_for_externals_lparen": (
                "preallocate_scan_plain_call_arg_for_externals_rparen:",
                "lda #'('",
            ),
            "preallocate_scan_plain_call_arg_for_externals_rparen": (
                "preallocate_scan_plain_call_arg_for_externals_comma:",
                "lda #')'",
            ),
            "preallocate_scan_plain_call_arg_for_externals_comma": (
                "preallocate_scan_plain_call_arg_for_externals_string:",
                "lda #','",
            ),
            "preallocate_skip_string_in_plain_call_arg_from_scan_y": (
                "preallocate_skip_string_in_plain_call_arg_loop:",
                "lda #'\"'",
            ),
            "preallocate_skip_string_in_plain_call_arg_close": (
                "preallocate_skip_string_in_plain_call_arg_done:",
                "lda #'\"'",
            ),
        }

        for label, (next_label, expected_literal) in scanner_delimiter_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn(expected_literal, body, msg=label)
            self.assertIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

        scanner_loop_match = re.search(
            r"preallocate_scan_plain_call_arg_for_externals_loop:\n(?P<body>.*?)\n"
            r"preallocate_scan_plain_call_arg_for_externals_consume_one:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(scanner_loop_match)
        assert scanner_loop_match is not None
        scanner_loop_body = scanner_loop_match.group("body")
        self.assertIn("lda #')'", scanner_loop_body)
        self.assertIn("lda #','", scanner_loop_body)
        self.assertIn("jsr source_reader_match_char_from_scan_y", scanner_loop_body)
        self.assertNotIn("cmp #')'", scanner_loop_body)
        self.assertNotIn("cmp #','", scanner_loop_body)
        self.assertNotIn("jsr source_reader_consume_scan_y", scanner_loop_body)
        self.assertNotIn("jsr advance_scan_y", scanner_loop_body)

        scan_fallback_match = re.search(
            r"preallocate_scan_plain_call_arg_for_externals_consume_one:\n(?P<body>.*?)\n"
            r"preallocate_scan_plain_call_arg_for_externals_lparen:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(scan_fallback_match)
        assert scan_fallback_match is not None
        scan_fallback_body = scan_fallback_match.group("body")
        self.assertIn("jsr source_reader_consume_plain_call_arg_scan_byte_from_scan_y", scan_fallback_body)
        self.assertNotIn("jsr source_reader_consume_scan_y", scan_fallback_body)
        self.assertNotIn("jsr advance_scan_y", scan_fallback_body)

        string_loop_match = re.search(
            r"preallocate_skip_string_in_plain_call_arg_loop:\n(?P<body>.*?)\n"
            r"preallocate_skip_string_in_plain_call_arg_close:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(string_loop_match)
        assert string_loop_match is not None
        string_loop_body = string_loop_match.group("body")
        self.assertIn("jsr source_reader_consume_plain_call_arg_string_byte_from_scan_y", string_loop_body)
        self.assertNotIn("jsr source_reader_consume_scan_y", string_loop_body)
        self.assertNotIn("jsr advance_scan_y", string_loop_body)

        string_helper_match = re.search(
            r"source_reader_consume_plain_call_arg_string_byte_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_consume_plain_call_arg_scan_byte_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(string_helper_match)
        assert string_helper_match is not None
        string_helper_body = string_helper_match.group("body")
        self.assertIn("jsr source_reader_peek_scan_y", string_helper_body)
        self.assertIn("cmp #10", string_helper_body)
        self.assertIn("cmp #13", string_helper_body)
        self.assertIn("cmp #'\"'", string_helper_body)
        self.assertIn("jsr source_reader_consume_scan_y", string_helper_body)

        scan_helper_match = re.search(
            r"source_reader_consume_plain_call_arg_scan_byte_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_consume_line_call_scan_byte_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(scan_helper_match)
        assert scan_helper_match is not None
        scan_helper_body = scan_helper_match.group("body")
        for expected in ("cmp #10", "cmp #13", "cmp #'\"'", "cmp #'('", "cmp #')'", "cmp #','"):
            self.assertIn(expected, scan_helper_body)
        self.assertIn("jsr source_reader_peek_scan_y", scan_helper_body)
        self.assertIn("jsr source_reader_consume_scan_y", scan_helper_body)

        flat_match = re.search(
            r"preallocate_consume_flat_call_args_from_scan_y:\n(?P<body>.*?)\n"
            r"preallocate_real_explicit_assignment_external_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(flat_match)
        assert flat_match is not None
        flat_body = flat_match.group("body")
        self.assertIn("lda #'('", flat_body)
        self.assertIn("lda #')'", flat_body)
        self.assertIn("jsr source_reader_consume_char_from_scan_y", flat_body)
        self.assertIn("jsr source_reader_match_char_from_scan_y", flat_body)
        self.assertIn("jsr source_reader_consume_flat_call_arg_scan_byte_from_scan_y", flat_body)
        self.assertNotIn("cmp #')'", flat_body)
        self.assertNotIn("jsr source_reader_consume_scan_y", flat_body)
        self.assertNotIn("jsr advance_scan_y", flat_body)

        flat_helper_match = re.search(
            r"source_reader_consume_flat_call_arg_scan_byte_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_consume_char_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(flat_helper_match)
        assert flat_helper_match is not None
        flat_helper_body = flat_helper_match.group("body")
        for expected in ("cmp #10", "cmp #13", "cmp #'\"'", "cmp #'('", "cmp #')'"):
            self.assertIn(expected, flat_helper_body)
        self.assertIn("jsr source_reader_peek_scan_y", flat_helper_body)
        self.assertIn("jsr source_reader_consume_scan_y", flat_helper_body)

    def test_preallocate_line_call_scan_fallback_uses_source_reader_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        fallback_match = re.search(
            r"preallocate_scan_line_call_externals_consume_one:\n(?P<body>.*?)\n"
            r"preallocate_scan_line_call_externals_string:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(fallback_match)
        assert fallback_match is not None
        fallback_body = fallback_match.group("body")
        self.assertIn("jsr source_reader_consume_line_call_scan_byte_from_scan_y", fallback_body)
        self.assertNotIn("jsr source_reader_consume_scan_y", fallback_body)
        self.assertNotIn("jsr advance_scan_y", fallback_body)

        helper_match = re.search(
            r"source_reader_consume_line_call_scan_byte_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_consume_flat_call_arg_scan_byte_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn(
            "jmp source_reader_consume_plain_call_arg_string_byte_from_scan_y",
            helper_body,
        )
        self.assertNotIn("jsr source_reader_consume_scan_y", helper_body)
        self.assertNotIn("jsr advance_scan_y", helper_body)

    def test_preallocate_conversion_close_parens_use_expected_char_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        close_paren_ranges = {
            "preallocate_int_conversion_external_from_scan_y": (
                "preallocate_int_conversion_external_miss_restore:",
            ),
            "preallocate_real_bridge_conversion_external_from_scan_y": (
                "preallocate_real_bridge_conversion_external_miss_restore:",
            ),
            "preallocate_real_numeric_positive_conversion_external_from_scan_y": (
                "preallocate_real_numeric_positive_conversion_external_miss:",
            ),
            "preallocate_real_numeric_signed_conversion_external_from_scan_y": (
                "preallocate_real_numeric_signed_conversion_external_miss:",
            ),
            "preallocate_real_explicit_bridge_assignment_external_from_scan_y": (
                "preallocate_real_explicit_bridge_assignment_external_miss:",
            ),
            "preallocate_real_explicit_positive_assignment_external_from_scan_y": (
                "preallocate_real_explicit_positive_assignment_external_miss:",
            ),
            "preallocate_real_explicit_signed_assignment_external_from_scan_y": (
                "preallocate_real_explicit_signed_assignment_external_miss:",
            ),
            "preallocate_real_unary_operator_assignment_external_from_scan_y": (
                "preallocate_real_unary_operator_assignment_external_miss:",
            ),
            "preallocate_real_unary_print_external_from_scan_y": (
                "preallocate_real_unary_print_external_miss_restore:",
            ),
        }

        for label, (next_label,) in close_paren_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("lda #')'", body, msg=label)
            self.assertIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
            self.assertNotIn("cmp #')'", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

    def test_preallocate_real_binary_operators_use_expected_char_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        helper_match = re.search(
            r"source_reader_match_real_binary_operator_from_scan_y:\n(?P<body>.*?)\n"
            r"source_reader_match_comparison_operator_from_scan_y:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(helper_match)
        assert helper_match is not None
        helper_body = helper_match.group("body")
        self.assertIn("jsr source_reader_peek_scan_y", helper_body)
        for expected in ("cmp #'+'", "cmp #'-'", "cmp #'*'", "cmp #'/'"):
            self.assertIn(expected, helper_body)
        self.assertNotIn("jsr source_reader_consume_scan_y", helper_body)
        self.assertNotIn("jsr advance_scan_y", helper_body)

        operator_ranges = {
            "preallocate_real_binary_operator_assignment_external_from_scan_y": (
                "preallocate_real_binary_operator_assignment_external_miss:",
            ),
            "preallocate_real_binary_print_external_from_scan_y": (
                "preallocate_real_binary_print_external_miss_restore:",
            ),
        }

        for label, (next_label,) in operator_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr source_reader_match_real_binary_operator_from_scan_y", body, msg=label)
            for forbidden in ("cmp #'+'", "cmp #'-'", "cmp #'*'", "cmp #'/'"):
                self.assertNotIn(forbidden, body, msg=label)
            self.assertIn("sta real_operator_data", body, msg=label)
            self.assertIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)
            if label == "preallocate_real_binary_print_external_from_scan_y":
                self.assertIn("lda #')'", body, msg=label)
                self.assertIn("jsr source_reader_match_char_from_scan_y", body, msg=label)
                self.assertNotIn("cmp #')'", body, msg=label)

    def test_preallocate_condition_operators_use_expected_char_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        exact_ranges = {
            "preallocate_real_condition_cmp_external_from_scan_y": (
                "preallocate_declared_symbol_is_return_statement:",
                ["lda #'='", "lda #'<'", "lda #'>'"],
            ),
            "preallocate_call_bool_primary_external_from_scan_y": (
                "preallocate_consume_comparison_operator_at_scan_y:",
                ["lda #'('", "lda #')'"],
            ),
            "preallocate_consume_comparison_operator_at_scan_y": (
                "preallocate_save_declared_module_name:",
                ["lda #'='", "lda #'<'", "lda #'>'"],
            ),
        }

        for label, (next_label, expected_lines) in exact_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            for expected in expected_lines:
                self.assertIn(expected, body, msg=label)
            self.assertIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
            if label == "preallocate_call_bool_primary_external_from_scan_y":
                self.assertNotIn("cmp #')'", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

    def test_preallocate_print_punctuation_uses_expected_char_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        exact_ranges = {
            "preallocate_real_print_statement_external_from_scan_y": (
                "preallocate_real_print_statement_external_miss:",
            ),
            "preallocate_int_print_statement_call_external_from_scan_y": (
                "preallocate_int_print_statement_call_external_miss_restore:",
            ),
        }

        for label, (next_label,) in exact_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("lda #'('", body, msg=label)
            self.assertIn("lda #')'", body, msg=label)
            self.assertIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
            self.assertNotIn("cmp #')'", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

    def test_preallocate_signed_word_prefix_uses_expected_char_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"preallocate_consume_signed_word_prefix_from_scan_y:\n(?P<body>.*?)\n"
            r"preallocate_consume_signed_word_prefix_fail:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("lda #'0'", body)
        self.assertIn("lda #'-'", body)
        self.assertIn("jsr source_reader_consume_char_from_scan_y", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def test_speculative_scan_loops_consume_through_source_reader(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        scan_ranges = {
            "scan_value_expr_for_top_level_arith_from_scan_y": (
                ".if ACTC_KEEP_BODY_RESIDENT_FALLBACK",
                "jsr source_reader_consume_top_level_arith_scan_byte_from_scan_y",
                ("lda #','", "lda #']'", "lda #')'", "lda #'('"),
                ("cmp #','", "cmp #']'", "cmp #')'", "cmp #'('"),
            ),
            "scan_print_expr_for_bool_keywords_from_scan_y": (
                ".endif",
                "jsr source_reader_consume_bool_keyword_scan_byte_from_scan_y",
                ("lda #')'", "lda #'('"),
                ("cmp #')'", "cmp #'('"),
            ),
            "scan_value_expr_for_bool_tokens_from_scan_y": (
                "emit_runtime_bool_or_from_scan_y_or_fail:",
                "jsr source_reader_consume_bool_token_scan_byte_from_scan_y",
                ("lda #','", "lda #']'", "lda #')'", "lda #'('"),
                ("cmp #','", "cmp #']'", "cmp #')'", "cmp #'('"),
            ),
        }

        for label, (next_label, expected_helper, expected_matches, forbidden_compares) in scan_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn(expected_helper, body, msg=label)
            for expected in expected_matches:
                self.assertIn(expected, body, msg=label)
            self.assertIn("jsr source_reader_match_char_from_scan_y", body, msg=label)
            for forbidden in forbidden_compares:
                self.assertNotIn(forbidden, body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)
            if "bool" in label:
                self.assertIn("jsr source_reader_reset_bool_scan_state", body, msg=label)
                self.assertNotIn("sta reader_prev_symbol_data", body, msg=label)

        helper_ranges = {
            "source_reader_consume_top_level_arith_scan_byte_from_scan_y": (
                "source_reader_consume_bool_keyword_scan_byte_from_scan_y:",
                ("cmp #10", "cmp #13", "cmp #','", "cmp #']'", "cmp #')'", "cmp #'('"),
                False,
            ),
            "source_reader_consume_bool_keyword_scan_byte_from_scan_y": (
                "source_reader_consume_bool_token_scan_byte_from_scan_y:",
                ("cmp #10", "cmp #13", "cmp #')'", "cmp #'('"),
                True,
            ),
            "source_reader_consume_bool_token_scan_byte_from_scan_y": (
                "source_reader_consume_char_from_scan_y:",
                ("cmp #10", "cmp #13", "cmp #','", "cmp #']'", "cmp #')'", "cmp #'('", "cmp #'='", "cmp #'<'", "cmp #'>'"),
                True,
            ),
        }

        for label, (next_label, expected_checks, stores_prev_symbol) in helper_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr source_reader_peek_scan_y", body, msg=label)
            for expected in expected_checks:
                self.assertIn(expected, body, msg=label)
            if stores_prev_symbol:
                self.assertIn("jsr source_reader_note_bool_scan_byte_from_a", body, msg=label)
            self.assertIn("jsr source_reader_consume_scan_y", body, msg=label)

    def test_speculative_scan_punctuation_uses_expected_char_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        punctuation_ranges = {
            "scan_value_expr_for_top_level_arith_from_scan_y_comma": (
                "scan_value_expr_for_top_level_arith_from_scan_y_rparen:",
                "lda #','",
                "jsr source_reader_consume_char_from_scan_y",
            ),
            "scan_value_expr_for_top_level_arith_from_scan_y_rparen": (
                "scan_value_expr_for_top_level_arith_from_scan_y_lparen:",
                "lda #')'",
                "jsr source_reader_consume_char_from_scan_y",
            ),
            "scan_value_expr_for_top_level_arith_from_scan_y_lparen": (
                "scan_value_expr_for_top_level_arith_from_scan_y_found:",
                "lda #'('",
                "jsr source_reader_consume_char_from_scan_y",
            ),
            "scan_print_expr_for_bool_keywords_from_scan_y_rparen": (
                "scan_print_expr_for_bool_keywords_from_scan_y_lparen:",
                "lda #')'",
                "jsr source_reader_consume_bool_punctuation_from_scan_y",
            ),
            "scan_print_expr_for_bool_keywords_from_scan_y_lparen": (
                "scan_print_expr_for_bool_keywords_from_scan_y_try_and:",
                "lda #'('",
                "jsr source_reader_consume_bool_punctuation_from_scan_y",
            ),
            "scan_value_expr_for_bool_tokens_from_scan_y_comma": (
                "scan_value_expr_for_bool_tokens_from_scan_y_rparen:",
                "lda #','",
                "jsr source_reader_consume_bool_punctuation_from_scan_y",
            ),
            "scan_value_expr_for_bool_tokens_from_scan_y_rparen": (
                "scan_value_expr_for_bool_tokens_from_scan_y_lparen:",
                "lda #')'",
                "jsr source_reader_consume_bool_punctuation_from_scan_y",
            ),
            "scan_value_expr_for_bool_tokens_from_scan_y_lparen": (
                "scan_value_expr_for_bool_tokens_from_scan_y_try_and:",
                "lda #'('",
                "jsr source_reader_consume_bool_punctuation_from_scan_y",
            ),
        }

        for label, (next_label, expected_char, expected_helper) in punctuation_ranges.items():
            with self.subTest(label=label):
                match = re.search(
                    rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                    actc_text,
                    re.DOTALL,
                )
                self.assertIsNotNone(match, msg=label)
                assert match is not None
                body = match.group("body")
                self.assertIn(expected_char, body)
                self.assertIn(expected_helper, body)
                if "bool" in label:
                    self.assertNotIn("sta reader_prev_symbol_data", body)
                    self.assertNotIn("jsr source_reader_consume_char_from_scan_y", body)
                self.assertNotIn("jsr source_reader_consume_scan_y", body)
                self.assertNotIn("jsr advance_scan_y", body)

        helper_ranges = {
            "source_reader_note_bool_scan_byte_from_a": (
                "source_reader_reset_bool_scan_state:",
                ["jsr uppercase_ascii", "jsr uppercase_symbol_body_valid", "sta reader_prev_symbol_data"],
            ),
            "source_reader_reset_bool_scan_state": (
                "source_reader_consume_bool_punctuation_from_scan_y:",
                ["lda #$00", "sta reader_prev_symbol_data"],
            ),
            "source_reader_consume_bool_punctuation_from_scan_y": (
                "source_reader_consume_whitespace_from_scan_ptr:",
                [
                    "pha",
                    "jsr source_reader_reset_bool_scan_state",
                    "pla",
                    "jmp source_reader_consume_char_from_scan_y",
                ],
            ),
        }
        for label, (next_label, expected_lines) in helper_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            for expected in expected_lines:
                self.assertIn(expected, body, msg=label)

    def test_real_conversion_and_operator_paths_use_expected_char_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        real_ranges = {
            "emit_runtime_int_explicit_value_from_scan_y_or_fail": (
                "pack_expr_value_lo_as_positive_real_high_word:",
                ["lda #')'"],
            ),
        }

        for label, (next_label, expected_chars) in real_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            for expected in expected_chars:
                self.assertIn(expected, body, msg=label)
            self.assertIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
            self.assertNotIn("cmp #')'", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

    def test_real_explicit_assignment_delimiters_use_expected_char_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        exact_ranges = {
            "emit_real_explicit_bridge_assignment_from_scan_y_or_fail": (
                "emit_real_explicit_bridge_assignment_from_scan_y_or_fail_fail:",
                ["lda #')'"],
            ),
            "emit_real_explicit_value_after_open_from_scan_y_or_fail": (
                "emit_real_explicit_value_assignment_from_scan_y_or_fail:",
                ["lda #')'", "lda #'0'", "lda #'-'"],
            ),
            "emit_real_wide_signed_int_assignment_from_scan_y_or_fail": (
                "emit_real_wide_signed_int_assignment_from_scan_y_or_fail_fail:",
                ["lda #'0'", "lda #'-'"],
            ),
        }

        for label, (next_label, expected_lines) in exact_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            for expected in expected_lines:
                self.assertIn(expected, body, msg=label)
            self.assertIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
            if "bridge" in label or "after_open" in label:
                self.assertNotIn("cmp #')'", body, msg=label)
            if "signed" in label or "after_open" in label:
                self.assertNotIn("cmp #'0'", body, msg=label)
                self.assertNotIn("cmp #'-'", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

    def test_real_assignment_operators_use_expected_char_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        exact_ranges = {
            "emit_real_add_assignment_after_copy_check": (
                "emit_real_copy_assignment_from_scan_y_ok:",
                ["jsr source_reader_match_real_binary_operator_from_scan_y", "sta real_operator_data"],
            ),
            "emit_real_fabs_assignment_after_open_from_scan_y_or_fail": (
                "resolve_call_target_from_declared_or_fail:",
                ["lda #')'"],
            ),
        }

        for label, (next_label, expected_lines) in exact_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            for expected in expected_lines:
                self.assertIn(expected, body, msg=label)
            self.assertIn("jsr source_reader_consume_char_from_scan_y", body, msg=label)
            if label == "emit_real_add_assignment_after_copy_check":
                for forbidden in ("cmp #'+'", "cmp #'-'", "cmp #'*'", "cmp #'/'"):
                    self.assertNotIn(forbidden, body, msg=label)
            if "fabs" in label:
                self.assertNotIn("cmp #')'", body, msg=label)
            self.assertNotIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", body, msg=label)

    def test_real_assignment_digit_dispatch_uses_source_reader_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        match = re.search(
            r"emit_real_add_assignment_from_scan_y_or_fail:\n(?P<body>.*?)\n"
            r"emit_real_add_assignment_after_copy_check:",
            actc_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr source_reader_match_open_paren_from_scan_y", body)
        self.assertIn("jsr source_reader_peek_decimal_digit_value_from_scan_y", body)
        self.assertIn("jmp emit_real_small_int_assignment_from_scan_y_or_fail", body)
        self.assertNotIn("cmp #'('", body)
        self.assertNotIn("cmp #'0'", body)
        self.assertNotIn("cmp #'9'+1", body)
        self.assertNotIn("jsr source_reader_consume_scan_y", body)
        self.assertNotIn("jsr advance_scan_y", body)

    def require_toolchain(self) -> None:
        for tool in ("cc", "ca65", "ld65", "make"):
            if shutil.which(tool) is None:
                self.skipTest(f"{tool} not found")

    def run_checked(
        self,
        args: list[str],
        timeout: int = 120,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        run_env = os.environ.copy()
        if env is not None:
            run_env.update(env)
        result = subprocess.run(
            args,
            cwd=self.root,
            env=run_env,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return result

    def assert_single_proc_object(
        self,
        text: str,
        body: str,
        min_line: int = 2,
        source_stem: str = "main",
        debug_op_count: int | None = None,
    ) -> None:
        source_name = re.escape(source_stem.lower())
        match = re.match(
            rf"^OBJ1\nf 0 src/{source_name}\.act\nq 0 0 (\d+) (\d+)\n((?:[lL] 0 \d+ 0 \d+ \d+\n)*)",
            text,
        )
        self.assertIsNotNone(match, msg=text)
        assert match is not None
        self.assertGreaterEqual(int(match.group(1)), min_line, msg=text)
        self.assertEqual(int(match.group(2)), 6, msg=text)
        debug_lines = [line for line in match.group(3).splitlines() if line]
        expected_debug_ops = count_body_ops(body) if debug_op_count is None else debug_op_count
        self.assertEqual(len(debug_lines), expected_debug_ops, msg=text)
        debug_kinds = {line[0] for line in debug_lines}
        self.assertLessEqual(len(debug_kinds), 1, msg=text)
        native_offsets = []
        for index, line in enumerate(debug_lines):
            self.assertRegex(line, r"^[lL] 0 \d+ 0 \d+ \d+$", msg=text)
            fields = line.split()
            if fields[0] == "l":
                self.assertEqual(int(fields[2]), index, msg=text)
            else:
                native_offsets.append(int(fields[2]))
        self.assertEqual(native_offsets, sorted(native_offsets), msg=text)
        remainder = text[match.end() :]
        var_debug_prefix = re.match(
            r"^((?:V g [ibcr] \d+ 0 \d+ \d+\n|V [pl] [ibcr] \d+ \d+ 0 \d+ \d+\n)*)",
            remainder,
        )
        assert var_debug_prefix is not None
        self.assertEqual(remainder[var_debug_prefix.end() :], body, msg=text)

    def test_reu_source_cache_stages_large_source_and_pages_compile_window(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-source"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            source = 'MODULE MAIN\rPROC MAIN()\rPrintE("OK")\rRETURN\r' + ("\r" * 21000)
            source_path = source_dir / "main.act"
            source_path.write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "10000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 7\nb e0r\ns OK\nk 2\nn main\n",
            )

        reu_stage = next(op for op in summary["ops"] if op["kind"] == "rsta")
        reu_read = next(op for op in summary["ops"] if op["kind"] == "rrd")
        self.assertEqual(reu_stage["path"], "SRC/MAIN.ACT")
        self.assertEqual(reu_stage["status"], 1)
        self.assertGreater(reu_stage["actual_len"], 20480)
        self.assertEqual(reu_stage["params"][2:5], [0, 0, 1])
        self.assertEqual(reu_read["status"], 1)
        self.assertEqual(reu_read["actual_len"], 1535)
        self.assertEqual(reu_read["actual_len"], reu_read["limit"])
        self.assertTrue(
            any(
                op["kind"] == "rrd" and op["params"][:3] == [0, 0x50, 1]
                for op in summary["ops"]
            ),
            msg=result.stdout,
        )

    def test_reu_source_cache_resident_header_skips_comment_and_pages_module_name_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={
                "ACTC_SOURCE_WINDOW": "128",
                "ACTC_SOURCE_LOOKAHEAD": "0",
                "ACTC_USE_SOURCE_HEADER_OVERLAY": "0",
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-module-header-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            comment = "; resident header comment\r"
            module_keyword = "MODULE"
            module_name_offset = 126
            filler_len = module_name_offset - len(comment) - len(module_keyword)
            self.assertGreaterEqual(filler_len, 0)
            source = comment + module_keyword + (" " * filler_len) + "MAIN\rPROC MAIN()\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 16\n"
                "b M\n"
                "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
                "k 0\n"
                "n main\n",
            )

        tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [128, 0, 1]
        )
        self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_source_header_overlay_pages_module_name_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={
                "ACTC_SOURCE_WINDOW": "128",
                "ACTC_SOURCE_LOOKAHEAD": "0",
                "ACTC_USE_SOURCE_HEADER_OVERLAY": "1",
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-source-header-overlay-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            module_keyword = "MODULE"
            module_name_offset = 126
            filler_len = module_name_offset - len(module_keyword)
            self.assertGreaterEqual(filler_len, 0)
            source = module_keyword + (" " * filler_len) + "MAIN\rPROC MAIN()\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 16\n"
                "b M\n"
                "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
                "k 0\n"
                "n main\n",
            )

        tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [128, 0, 1]
        )
        self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_source_header_overlay_module_name_spans_multiple_windows_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={
                "ACTC_SOURCE_WINDOW": "16",
                "ACTC_SOURCE_LOOKAHEAD": "0",
                "ACTC_USE_SOURCE_HEADER_OVERLAY": "1",
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-source-header-overlay-module-name-multi-window-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            module_name = "ABCDEFGHIJKLMNOPQRSTUVW"
            module_name_lower = module_name.lower()
            (project_root / "ACTION.PROJ").write_text(
                f"ACTION PROJECT\r{module_name}.ACT\r",
                encoding="ascii",
            )

            module_name_offset = 15
            module_prefix = "MODULE "
            filler_len = module_name_offset - len(module_prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = module_prefix + (" " * filler_len) + module_name + "\rPROC MAIN()\rRETURN\r"
            (source_dir / f"{module_name}.ACT").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    module_name,
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / f"{module_name}.OBJ").read_text(encoding="ascii"),
                "x main 0 1\n"
                "b r\n"
                "k 0\n"
                f"n {module_name_lower}\n",
                source_stem=module_name,
            )

        first_tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [16, 0, 1]
        )
        second_tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [32, 0, 1]
        )
        self.assertGreater(first_tail_read["actual_len"], 0)
        self.assertGreater(second_tail_read["actual_len"], 0)

    def test_reu_source_cache_source_header_overlay_pages_module_keyword_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={
                "ACTC_SOURCE_WINDOW": "128",
                "ACTC_SOURCE_LOOKAHEAD": "0",
                "ACTC_USE_SOURCE_HEADER_OVERLAY": "1",
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-source-header-overlay-keyword-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            source = (" " * 126) + "MODULE MAIN\rPROC MAIN()\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 16\n"
                "b M\n"
                "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
                "k 0\n"
                "n main\n",
            )

        tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [128, 0, 1]
        )
        self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_source_header_overlay_skips_multi_window_comments_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={
                "ACTC_SOURCE_WINDOW": "128",
                "ACTC_SOURCE_LOOKAHEAD": "0",
                "ACTC_USE_SOURCE_HEADER_OVERLAY": "1",
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-source-header-overlay-comments-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            source = ";" + (" COMMENT" * 45) + "\r; SECOND COMMENT\r \tMODULE MAIN\rPROC MAIN()\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 16\n"
                "b M\n"
                "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
                "k 0\n"
                "n main\n",
            )

        first_tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [128, 0, 1]
        )
        second_tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1]
        )
        self.assertGreater(first_tail_read["actual_len"], 0)
        self.assertGreater(second_tail_read["actual_len"], 0)

    def test_reu_source_cache_source_header_overlay_skips_mixed_multi_window_prefix_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={
                "ACTC_SOURCE_WINDOW": "128",
                "ACTC_SOURCE_LOOKAHEAD": "0",
                "ACTC_USE_SOURCE_HEADER_OVERLAY": "1",
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-source-header-overlay-mixed-prefix-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            source = (" \t\r\n" * 75) + "MODULE MAIN\rPROC MAIN()\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 16\n"
                "b M\n"
                "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
                "k 0\n"
                "n main\n",
            )

        first_tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [128, 0, 1]
        )
        second_tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1]
        )
        self.assertGreater(first_tail_read["actual_len"], 0)
        self.assertGreater(second_tail_read["actual_len"], 0)

    def test_reu_source_cache_source_header_overlay_skips_multi_window_module_spacing_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={
                "ACTC_SOURCE_WINDOW": "128",
                "ACTC_SOURCE_LOOKAHEAD": "0",
                "ACTC_USE_SOURCE_HEADER_OVERLAY": "1",
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-source-header-overlay-module-spacing-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            source = "MODULE" + (" " * 300) + "MAIN\rPROC MAIN()\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 16\n"
                "b M\n"
                "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
                "k 0\n"
                "n main\n",
            )

        first_tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [128, 0, 1]
        )
        second_tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1]
        )
        self.assertGreater(first_tail_read["actual_len"], 0)
        self.assertGreater(second_tail_read["actual_len"], 0)

    def test_reu_source_cache_source_header_overlay_skips_mixed_multi_window_module_spacing_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={
                "ACTC_SOURCE_WINDOW": "128",
                "ACTC_SOURCE_LOOKAHEAD": "0",
                "ACTC_USE_SOURCE_HEADER_OVERLAY": "1",
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-source-header-overlay-mixed-module-spacing-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            source = "MODULE" + (" \t" * 150) + "MAIN\rPROC MAIN()\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 16\n"
                "b M\n"
                "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
                "k 0\n"
                "n main\n",
            )

        first_tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [128, 0, 1]
        )
        second_tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1]
        )
        self.assertGreater(first_tail_read["actual_len"], 0)
        self.assertGreater(second_tail_read["actual_len"], 0)

    def test_reu_source_cache_proc_name_crosses_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "128", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-proc-name-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            module_header = "MODULE MAIN\r"
            proc_prefix = "PROC "
            proc_name_offset = 127
            filler_len = proc_name_offset - len(module_header) - len(proc_prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = module_header + ("\r" * filler_len) + proc_prefix + "MAIN()\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 16\n"
                "b M\n"
                "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
                "k 0\n"
                "n main\n",
                min_line=100,
            )

        tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [128, 0, 1]
        )
        self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_module_var_name_crosses_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "128", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-module-var-name-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            module_header = "MODULE MAIN\r"
            decl_prefix = "INT "
            var_name = "VALUE"
            var_name_offset = 127
            filler_len = var_name_offset - len(module_header) - len(decl_prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = module_header + ("\r" * filler_len) + decl_prefix + var_name + "\rPROC MAIN()\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 1\n"
                "b r\n"
                "v value 0\n"
                "k 0\n"
                "n main\n",
                min_line=100,
            )

        tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [128, 0, 1]
        )
        self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_decl_overlay_skips_mixed_multi_window_prefix_before_module_var_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={
                "ACTC_SOURCE_WINDOW": "16",
                "ACTC_SOURCE_LOOKAHEAD": "0",
                "ACTC_USE_DECL_OVERLAY": "1",
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-decl-overlay-mixed-prefix-module-var-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            source = "MODULE MAIN\r" + (" \t\r\n" * 20) + "INT VALUE\rPROC MAIN()\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "14000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 1\n"
                "b r\n"
                "v value 0\n"
                "k 0\n"
                "n main\n",
                min_line=10,
            )

        self.assertTrue(
            any(op["kind"] == "rrd" and op["params"][0:3] == [32, 0, 1] for op in summary["ops"]),
            msg=result.stdout,
        )
        self.assertTrue(
            any(op["kind"] == "rrd" and op["params"][0:3] == [64, 0, 1] for op in summary["ops"]),
            msg=result.stdout,
        )

    def test_reu_source_cache_body_overlay_skips_mixed_multi_window_prefix_before_return_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={
                "ACTC_SOURCE_WINDOW": "16",
                "ACTC_SOURCE_LOOKAHEAD": "0",
                "ACTC_USE_BODY_OVERLAY": "1",
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-body-overlay-mixed-prefix-return-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            source = "MODULE MAIN\rPROC MAIN()\r" + (" \t\r\n" * 20) + "RETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "14000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 16\n"
                "b M\n"
                "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
                "k 0\n"
                "n main\n",
            )

        self.assertTrue(
            any(op["kind"] == "rrd" and op["params"][0:3] == [32, 0, 1] for op in summary["ops"]),
            msg=result.stdout,
        )
        self.assertTrue(
            any(op["kind"] == "rrd" and op["params"][0:3] == [96, 0, 1] for op in summary["ops"]),
            msg=result.stdout,
        )

    def test_reu_source_cache_proc_var_names_cross_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "128", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        module_header = "MODULE MAIN\r"
        param_prefix = module_header + "PROC MAIN("
        param_source = param_prefix + (" " * (127 - len(param_prefix))) + "VALUE)\rRETURN VALUE\r"
        local_prefix = module_header + "PROC MAIN()\r"
        local_decl_prefix = "INT "
        local_source = (
            local_prefix
            + ("\r" * (127 - len(local_prefix) - len(local_decl_prefix)))
            + local_decl_prefix
            + "VALUE\rRETURN VALUE\r"
        )
        cases = (
            (
                "proc-param",
                param_source,
                "V p i 0 0 0 2 116\n",
                "x main 0 7\n"
                "b S0L0r\n"
                "v value 0\n"
                "k 0\n"
                "n main\n",
                2,
            ),
            (
                "proc-local",
                local_source,
                "V l i 0 0 0 102 5\n",
                "x main 0 4\n"
                "b L0r\n"
                "v value 0\n"
                "k 0\n"
                "n main\n",
                2,
            ),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            summaries: list[tuple[dict, str]] = []
            for case_name, source, expected_debug, expected_tail, min_line in cases:
                with self.subTest(case_name=case_name):
                    workspace = Path(tmpdir) / f"actc-reu-{case_name}-name-no-lookahead"
                    project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                    source_dir = project_root / "src"
                    object_dir = project_root / "obj"
                    source_dir.mkdir(parents=True)
                    object_dir.mkdir()
                    (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
                    (source_dir / "main.act").write_text(source, encoding="ascii")

                    result = self.run_checked(
                        [
                            str(self.build_dir / "tool_abi_harness"),
                            "--prg",
                            str(self.build_dir / "ACTC_REU.PRG"),
                            "--workspace",
                            str(project_root),
                            "--cmdline",
                            "MAIN",
                            "--services-inc",
                            str(self.build_dir / "udos_services.inc"),
                            "--labels",
                            str(self.build_dir / "actc.reu.current.labels"),
                            "--max-steps",
                            "12000000",
                        ]
                    )

                    summary = json.loads(result.stdout)
                    self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                    self.assertFalse(summary["hit_limit"], msg=result.stdout)
                    obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
                    self.assertIn(expected_debug, obj)
                    self.assert_single_proc_object(obj, expected_tail, min_line=min_line)
                    summaries.append((summary, result.stdout))

        for summary, stdout in summaries:
            tail_read = next(
                (
                    op
                    for op in summary["ops"]
                    if op["kind"] == "rrd" and op["params"][0:3] == [128, 0, 1]
                ),
                None,
            )
            self.assertIsNotNone(tail_read, msg=stdout)
            assert tail_read is not None
            self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_proc_var_names_span_multiple_windows_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "16", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        module_header = "MODULE MAIN\r"
        long_name = "ABCDEFGHIJKLMNOPQRSTUVW"
        long_name_lower = long_name.lower()
        name_offset = 31
        param_prefix = module_header + "PROC MAIN("
        param_source = (
            param_prefix
            + (" " * (name_offset - len(param_prefix)))
            + long_name
            + ")\rRETURN "
            + long_name
            + "\r"
        )
        local_prefix = module_header + "PROC MAIN()\r"
        local_decl_prefix = "INT "
        local_source = (
            local_prefix
            + ("\r" * (name_offset - len(local_prefix) - len(local_decl_prefix)))
            + local_decl_prefix
            + long_name
            + "\rRETURN "
            + long_name
            + "\r"
        )
        cases = (
            (
                "proc-param",
                param_source,
                "x main 0 7\n"
                "b S0L0r\n"
                f"v {long_name_lower} 0\n"
                "k 0\n"
                "n main\n",
            ),
            (
                "proc-local",
                local_source,
                "x main 0 4\n"
                "b L0r\n"
                f"v {long_name_lower} 0\n"
                "k 0\n"
                "n main\n",
            ),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            summaries: list[tuple[dict, str]] = []
            for case_name, source, expected_tail in cases:
                with self.subTest(case_name=case_name):
                    workspace = Path(tmpdir) / f"actc-reu-{case_name}-name-multi-window-no-lookahead"
                    project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                    source_dir = project_root / "src"
                    object_dir = project_root / "obj"
                    source_dir.mkdir(parents=True)
                    object_dir.mkdir()
                    (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
                    (source_dir / "main.act").write_text(source, encoding="ascii")

                    result = self.run_checked(
                        [
                            str(self.build_dir / "tool_abi_harness"),
                            "--prg",
                            str(self.build_dir / "ACTC_REU.PRG"),
                            "--workspace",
                            str(project_root),
                            "--cmdline",
                            "MAIN",
                            "--services-inc",
                            str(self.build_dir / "udos_services.inc"),
                            "--labels",
                            str(self.build_dir / "actc.reu.current.labels"),
                            "--max-steps",
                            "14000000",
                        ]
                    )

                    summary = json.loads(result.stdout)
                    self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                    self.assertFalse(summary["hit_limit"], msg=result.stdout)
                    self.assert_single_proc_object(
                        (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                        expected_tail,
                        min_line=2,
                    )
                    summaries.append((summary, result.stdout))

        for summary, stdout in summaries:
            self.assertTrue(
                any(op["kind"] == "rrd" and op["params"][0:3] == [32, 0, 1] for op in summary["ops"]),
                msg=stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rrd" and op["params"][0:3] == [48, 0, 1] for op in summary["ops"]),
                msg=stdout,
            )

    def test_reu_source_cache_proc_name_spans_multiple_windows_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "16", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-proc-name-multi-window-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            module_header = "MODULE MAIN\r"
            proc_prefix = "PROC "
            proc_name = "ABCDEFGHIJKLMNOPQRSTUVW"
            proc_name_offset = 31
            filler_len = proc_name_offset - len(module_header) - len(proc_prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = module_header + ("\r" * filler_len) + proc_prefix + proc_name + '()\rPrintE("OK")\rRETURN\r'
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "14000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            proc_name_lower = proc_name.lower()
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                f"x {proc_name_lower} 0 7\n"
                "b e0r\n"
                "s OK\n"
                "k 2\n"
                "n main\n",
            )

        self.assertTrue(
            any(op["kind"] == "rrd" and op["params"][0:3] == [32, 0, 1] for op in summary["ops"]),
            msg=result.stdout,
        )
        self.assertTrue(
            any(op["kind"] == "rrd" and op["params"][0:3] == [48, 0, 1] for op in summary["ops"]),
            msg=result.stdout,
        )

    def test_reu_source_cache_compiles_proc_name_crossing_window_boundary(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-paged"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            module_header = "MODULE MAIN\r"
            proc_prefix = "PROC "
            name_offset = 20478
            filler_len = name_offset - len(module_header) - len(proc_prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = module_header + ("\r" * filler_len) + proc_prefix + 'MAIN()\rPrintE("OK")\rRETURN\r'
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 7\nb e0r\ns OK\nk 2\nn main\n",
            )

        reu_stage = next(op for op in summary["ops"] if op["kind"] == "rsta")
        tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
        )
        self.assertEqual(reu_stage["path"], "SRC/MAIN.ACT")
        self.assertGreater(reu_stage["actual_len"], 20480)
        self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_compiles_string_literal_crossing_window_boundary(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-string-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rPROC MAIN()\r"
            print_prefix = 'PrintE("'
            literal_offset = 20479
            filler_len = literal_offset - len(prefix) - len(print_prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + print_prefix + 'OK")\rRETURN\r'
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 7\nb e0r\ns OK\nk 2\nn main\n",
            )

        reu_stage = next(op for op in summary["ops"] if op["kind"] == "rsta")
        tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
        )
        self.assertEqual(reu_stage["path"], "SRC/MAIN.ACT")
        self.assertGreater(reu_stage["actual_len"], 20480)
        self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_string_literal_crosses_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "128", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-string-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rPROC MAIN()\r"
            print_prefix = 'PrintE("'
            literal_offset = 127
            filler_len = literal_offset - len(prefix) - len(print_prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + print_prefix + 'OK")\rRETURN\r'
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 7\nb e0r\ns OK\nk 2\nn main\n",
            )

        tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [128, 0, 1]
        )
        self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_string_literal_spans_multiple_windows_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "18", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-string-multi-window-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rPROC MAIN()\r"
            print_prefix = 'PrintE("'
            literal = "ABCDEFGHIJKLMNOPQRST"
            literal_offset = 35
            filler_len = literal_offset - len(prefix) - len(print_prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + print_prefix + literal + '")\rRETURN\r'
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "14000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 7\n"
                "b e0r\n"
                "s ABCDEFGHIJKLMNOPQRST\n"
                "k 2\n"
                "n main\n",
            )

        self.assertTrue(
            any(op["kind"] == "rrd" and op["params"][0:3] == [36, 0, 1] for op in summary["ops"]),
            msg=result.stdout,
        )
        self.assertTrue(
            any(op["kind"] == "rrd" and op["params"][0:3] == [54, 0, 1] for op in summary["ops"]),
            msg=result.stdout,
        )

    def test_reu_source_cache_fixed_patterns_cross_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "128", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            cases = (
                (
                    "printie",
                    "PrintIE(",
                    "7)\rRETURN\r",
                    "x main 0 7\nb i0r\ni 7\nk 6\nn main\n",
                ),
                (
                    "return",
                    "RETURN",
                    "\r",
                    "x main 0 16\n"
                    "b M\n"
                    "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
                    "k 0\n"
                    "n main\n",
                ),
            )

            for case_name, keyword, suffix, expected_body in cases:
                workspace = Path(tmpdir) / f"actc-reu-fixed-{case_name}-no-lookahead"
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                prefix = "MODULE MAIN\rPROC MAIN()\r"
                keyword_offset = 126
                filler_len = keyword_offset - len(prefix)
                self.assertGreaterEqual(filler_len, 0)
                source = prefix + ("\r" * filler_len) + keyword + suffix
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "12000000",
                    ]
                )

                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                self.assert_single_proc_object(
                    (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                    expected_body,
                )

                tail_read = next(
                    op
                    for op in summary["ops"]
                    if op["kind"] == "rrd" and op["params"][0:3] == [128, 0, 1]
                )
                self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_fixed_pattern_crosses_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-fixed-printie-page-aligned-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rPROC MAIN()\r"
            keyword_offset = 254
            filler_len = keyword_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + "PrintIE(7)\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "15000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 7\nb i0r\ni 7\nk 6\nn main\n",
            )

        tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1]
        )
        self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_return_keyword_crosses_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-fixed-return-page-aligned-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rPROC MAIN()\r"
            keyword_offset = 254
            filler_len = keyword_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + (" " * filler_len) + "RETURN 1\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "15000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 4\n"
                "b p0r\n"
                "i 1\n"
                "k 0\n"
                "n main\n",
            )

        tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1]
        )
        self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_comment_line_crosses_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "128", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-comment-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rPROC MAIN()\r"
            comment_offset = 126
            filler_len = comment_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + ";" + ("X" * 16) + "\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 16\n"
                "b M\n"
                "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
                "k 0\n"
                "n main\n",
            )

        tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [128, 0, 1]
        )
        self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_comment_line_crosses_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-comment-page-aligned-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rPROC MAIN()\r"
            comment_offset = 254
            filler_len = comment_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + ";" + ("X" * 32) + "\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 16\n"
                "b M\n"
                "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
                "k 0\n"
                "n main\n",
            )

        tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1]
        )
        self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_comment_line_spans_page_aligned_windows_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-comment-page-aligned-multi-window-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rPROC MAIN()\r"
            comment_offset = 254
            filler_len = comment_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + ";" + ("X" * 257) + "\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 16\n"
                "b M\n"
                "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
                "k 0\n"
                "n main\n",
            )

        tail_read = next(
            (
                op
                for op in summary["ops"]
                if op["kind"] == "rrd"
                and op["params"][0:3] == [0, 2, 1]
                and op.get("head", [None])[0] == 13
            ),
            None,
        )
        self.assertIsNotNone(tail_read, msg=result.stdout)

    def test_reu_source_cache_comment_line_spans_multiple_windows_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "128", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-comment-multi-window-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rPROC MAIN()\r"
            comment_offset = 126
            filler_len = comment_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + ";" + ("X" * 300) + "\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "14000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 16\n"
                "b M\n"
                "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
                "k 0\n"
                "n main\n",
            )

        self.assertTrue(
            any(op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1] for op in summary["ops"]),
            msg=result.stdout,
        )

    def test_reu_source_cache_commits_long_inline_spaces_across_window_boundary(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-space-commit"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rPROC MAIN()\r"
            print_prefix = "PrintIE("
            filler_len = 20470 - len(prefix) - len(print_prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + print_prefix + (" " * 320) + "7)\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 7\nb i0r\ni 7\nk 6\nn main\n",
            )

        reu_stage = next(op for op in summary["ops"] if op["kind"] == "rsta")
        later_reads = [
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
        ]
        self.assertEqual(reu_stage["path"], "SRC/MAIN.ACT")
        self.assertGreater(reu_stage["actual_len"], 20480)
        self.assertTrue(later_reads, msg=result.stdout)

    def test_reu_source_cache_inline_spaces_span_multiple_windows_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "128", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-inline-spaces-multi-window-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rPROC MAIN()\r"
            print_prefix = "PrintIE("
            print_offset = 126
            filler_len = print_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + print_prefix + (" " * 300) + "7)\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "16000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 7\nb i0r\ni 7\nk 6\nn main\n",
            )

        self.assertTrue(
            any(op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1] for op in summary["ops"]),
            msg=result.stdout,
        )

    def test_reu_source_cache_commits_long_expression_across_window_boundary(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-expression-commit"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            long_name = "ABCDEFGHIJKLMNOPQRSTUVW"
            expression = "+".join([long_name] * 12)
            prefix = f"MODULE MAIN\rINT {long_name}=[1]\rPROC MAIN()\r"
            print_prefix = "PrintIE("
            expression_offset = 20470
            filler_len = expression_offset - len(prefix) - len(print_prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + print_prefix + expression + ")\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "22000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            debug_records = re.findall(r"^([lL]) 0 (\d+) 0 \d+ \d+$", obj, re.MULTILINE)
            self.assertEqual(len(debug_records), 25, msg=obj)
            debug_kinds = {kind for kind, _ in debug_records}
            self.assertEqual(len(debug_kinds), 1, msg=obj)
            debug_offsets = [int(offset) for _, offset in debug_records]
            if debug_records[0][0] == "l":
                self.assertEqual(debug_offsets, list(range(25)), msg=obj)
            else:
                self.assertEqual(debug_offsets, sorted(debug_offsets), msg=obj)
                self.assertLess(debug_offsets[0], debug_offsets[-1], msg=obj)
            self.assertIn("x main 0 361\nx __idata 357 2\nx __iptr 359 2\n", obj)
            self.assertIn("b u0M\nb M\nb M\n", obj)
            self.assertEqual(obj.count("A0 00 B1 06 48 C8 B1 06 48"), 12, msg=obj)
            self.assertEqual(
                obj.count("68 85 05 68 85 04 68 85 03 68 18 65 04 48 A5 03 65 05 48"),
                11,
                msg=obj,
            )
            self.assertIn("r 3 x __iptr\nr 9 x __iptr\nr 334 u0\nr 359 x __idata\n", obj)
            self.assertIn("u rt_print_i\n", obj)
            self.assertIn("v abcdefghijklmnopqrstuvw 1\nk 6\nn main\n", obj)

        reu_stage = next(op for op in summary["ops"] if op["kind"] == "rsta")
        later_reads = [
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
        ]
        self.assertEqual(reu_stage["path"], "SRC/MAIN.ACT")
        self.assertGreater(reu_stage["actual_len"], 20480)
        self.assertTrue(later_reads, msg=result.stdout)

    def test_reu_source_cache_restores_window_after_failed_keyword_probe(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-keyword-restore"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            long_name = "ABCDEFGHIJKLMNOPQRSTUVW"
            prefix = f"MODULE MAIN\rINT {long_name}=[1]\rPROC MAIN()\r"
            print_prefix = "PrintIE("
            filler_len = 20470 - len(prefix) - len(print_prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + print_prefix + (" " * 250) + long_name + ")\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "18000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 7\n"
                "b L0zr\n"
                "v abcdefghijklmnopqrstuvw 1\n"
                "k 6\n"
                "n main\n",
            )

        reu_stage = next(op for op in summary["ops"] if op["kind"] == "rsta")
        later_reads = [
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
        ]
        rewound_reads = [
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 0, 1]
        ]
        self.assertEqual(reu_stage["path"], "SRC/MAIN.ACT")
        self.assertGreater(reu_stage["actual_len"], 20480)
        self.assertTrue(later_reads, msg=result.stdout)
        self.assertTrue(rewound_reads, msg=result.stdout)

    def test_reu_source_cache_aon_prefixed_names_are_not_bool_keywords(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-bool-keyword-boundaries"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            source = (
                "MODULE MAIN\r"
                "INT ANDVALUE=[1]\r"
                "INT ORVALUE=[2]\r"
                "INT NOTVALUE=[3]\r"
                "PROC MAIN()\r"
                "PrintIE(ANDVALUE)\r"
                "PrintIE(ORVALUE)\r"
                "RETURN NOTVALUE\r"
            )
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b L0zL1zL2r\n", obj)
            self.assertIn("v andvalue 1\n", obj)
            self.assertIn("v orvalue 2\n", obj)
            self.assertIn("v notvalue 3\n", obj)

    def test_reu_source_cache_assignment_operator_can_sit_at_y_wrap(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-assignment-wrap"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rINT A=[1]\rPROC MAIN()\r"
            filler_len = 20470 - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + "A" + (" " * 254) + "=2\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "18000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                native_word_store_object("a", 1, 2),
                min_line=3,
                debug_op_count=3,
            )

        later_reads = [
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
        ]
        self.assertTrue(later_reads, msg=result.stdout)

    def test_reu_source_cache_assignment_spaces_cross_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "128", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-assignment-spaces-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rINT A=[1]\rPROC MAIN()\r"
            assignment_offset = 126
            filler_len = assignment_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + "A  =2\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                native_word_store_object("a", 1, 2),
                min_line=3,
                debug_op_count=3,
            )

        tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [128, 0, 1]
        )
        self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_statement_line_end_crosses_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "128", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-statement-line-end-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rINT A=[1]\rPROC MAIN()\r"
            assignment_offset = 125
            filler_len = assignment_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + "A=2\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                native_word_store_object("a", 1, 2),
                min_line=3,
                debug_op_count=3,
            )

        tail_read = next(
            (
                op
                for op in summary["ops"]
                if op["kind"] == "rrd"
                and op["params"][0:3] == [128, 0, 1]
                and op.get("head", [None])[0] == 13
            ),
            None,
        )
        self.assertIsNotNone(tail_read, msg=result.stdout)

    def test_reu_source_cache_crlf_pair_crosses_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "128", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-crlf-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rINT A=[1]\rPROC MAIN()\r"
            assignment_offset = 124
            filler_len = assignment_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + "A=2\r\nRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                native_word_store_object("a", 1, 2),
                min_line=3,
                debug_op_count=3,
            )

        tail_read = next(
            (
                op
                for op in summary["ops"]
                if op["kind"] == "rrd"
                and op["params"][0:3] == [128, 0, 1]
                and op.get("head", [None])[0] == 10
            ),
            None,
        )
        self.assertIsNotNone(tail_read, msg=result.stdout)

    def test_reu_source_cache_crlf_pair_crosses_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-crlf-page-aligned-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rINT A=[1]\rPROC MAIN()\r"
            assignment_offset = 252
            filler_len = assignment_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + "A=2\r\nRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                native_word_store_object("a", 1, 2),
                min_line=3,
                debug_op_count=3,
            )

        tail_read = next(
            (
                op
                for op in summary["ops"]
                if op["kind"] == "rrd"
                and op["params"][0:3] == [0, 1, 1]
                and op.get("head", [None])[0] == 10
            ),
            None,
        )
        self.assertIsNotNone(tail_read, msg=result.stdout)

    def test_reu_source_cache_assignment_lhs_symbol_crosses_window_boundary(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-assignment-lhs-symbol"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            long_name = "ABCDEFGHIJKLMNOPQRSTUVW"
            prefix = f"MODULE MAIN\rINT {long_name}=[1]\rPROC MAIN()\r"
            assignment_offset = 20478
            filler_len = assignment_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + f"{long_name}=2\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "18000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                native_word_store_object("abcdefghijklmnopqrstuvw", 1, 2),
                min_line=3,
                debug_op_count=3,
            )

        later_reads = [
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
        ]
        self.assertTrue(later_reads, msg=result.stdout)

    def test_reu_source_cache_assignment_lhs_symbol_crosses_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "128", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-assignment-lhs-symbol-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            long_name = "ABCDEFGHIJKLMNOPQRSTUVW"
            prefix = f"MODULE MAIN\rINT {long_name}=[1]\rPROC MAIN()\r"
            assignment_offset = 126
            filler_len = assignment_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + f"{long_name}=2\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                native_word_store_object("abcdefghijklmnopqrstuvw", 1, 2),
                min_line=3,
                debug_op_count=3,
            )

        tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [128, 0, 1]
        )
        self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_assignment_lhs_symbol_crosses_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-assignment-lhs-symbol-page-aligned-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            long_name = "ABCDEFGHIJKLMNOPQRSTUVW"
            prefix = f"MODULE MAIN\rINT {long_name}=[1]\rPROC MAIN()\r"
            assignment_offset = 254
            filler_len = assignment_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + f"{long_name}=2\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "15000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                native_word_store_object("abcdefghijklmnopqrstuvw", 1, 2),
                min_line=3,
                debug_op_count=3,
            )

        tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1]
        )
        self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_assignment_lhs_symbol_spans_multiple_windows_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "16", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-assignment-lhs-symbol-multi-window-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            long_name = "ABCDEFGHIJKLMNOPQRSTUVW"
            prefix = f"MODULE MAIN\rINT {long_name}=[1]\rPROC MAIN()\r"
            assignment_offset = 63
            filler_len = assignment_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + ("\r" * filler_len) + f"{long_name}=2\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "14000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                native_word_store_object("abcdefghijklmnopqrstuvw", 1, 2),
                min_line=3,
                debug_op_count=3,
            )

        self.assertTrue(
            any(op["kind"] == "rrd" and op["params"][0:3] == [64, 0, 1] for op in summary["ops"]),
            msg=result.stdout,
        )
        self.assertTrue(
            any(op["kind"] == "rrd" and op["params"][0:3] == [80, 0, 1] for op in summary["ops"]),
            msg=result.stdout,
        )

    def test_reu_source_cache_statement_terminators_cross_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "128", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            summaries: list[tuple[dict, str, int]] = []
            cases = (
                (
                    "then",
                    126,
                    "MODULE MAIN\rINT A=[0]\rPROC MAIN()\rIF 1 ",
                    "THEN\rA=1\rFI\rRETURN\r",
                    ord("E"),
                    "x main 0 13\n"
                    "b p0hp1S0vr\n"
                    "i 1\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "do",
                    127,
                    "MODULE MAIN\rINT A=[0]\rPROC MAIN()\rWHILE 1 ",
                    "DO\rA=1\rOD\rRETURN\r",
                    ord("O"),
                    "x main 0 16\n"
                    "b dp0fp1S0xr\n"
                    "i 1\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
            )

            for case_name, keyword_offset, prefix, suffix, tail_byte, expected_body in cases:
                workspace = Path(tmpdir) / f"actc-reu-terminator-{case_name}"
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                filler_len = keyword_offset - len(prefix)
                self.assertGreaterEqual(filler_len, 0)
                source = prefix + (" " * filler_len) + suffix
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "16000000",
                    ]
                )

                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                self.assert_single_proc_object(
                    (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                    expected_body,
                    min_line=3,
                )
                summaries.append((summary, result.stdout, tail_byte))

        for summary, stdout, tail_byte in summaries:
            tail_read = next(
                (
                    op
                    for op in summary["ops"]
                    if op["kind"] == "rrd"
                    and op["params"][0:3] == [128, 0, 1]
                    and op.get("head", [None])[0] == tail_byte
                ),
                None,
            )
            self.assertIsNotNone(tail_read, msg=stdout)

    def test_reu_source_cache_statement_terminators_cross_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            summaries: list[tuple[dict, str, int]] = []
            cases = (
                (
                    "then",
                    254,
                    "MODULE MAIN\rINT A=[0]\rPROC MAIN()\rIF 1 ",
                    "THEN\rA=1\rFI\rRETURN\r",
                    ord("E"),
                    "x main 0 13\n"
                    "b p0hp1S0vr\n"
                    "i 1\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "do",
                    255,
                    "MODULE MAIN\rINT A=[0]\rPROC MAIN()\rWHILE 1 ",
                    "DO\rA=1\rOD\rRETURN\r",
                    ord("O"),
                    "x main 0 16\n"
                    "b dp0fp1S0xr\n"
                    "i 1\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
            )

            for case_name, keyword_offset, prefix, suffix, tail_byte, expected_body in cases:
                workspace = Path(tmpdir) / f"actc-reu-page-terminator-{case_name}"
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                filler_len = keyword_offset - len(prefix)
                self.assertGreaterEqual(filler_len, 0)
                source = prefix + (" " * filler_len) + suffix
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "16000000",
                    ]
                )

                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                self.assert_single_proc_object(
                    (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                    expected_body,
                    min_line=3,
                )
                summaries.append((summary, result.stdout, tail_byte))

        for summary, stdout, tail_byte in summaries:
            tail_read = next(
                (
                    op
                    for op in summary["ops"]
                    if op["kind"] == "rrd"
                    and op["params"][0:3] == [0, 1, 1]
                    and op.get("head", [None])[0] == tail_byte
                ),
                None,
            )
            self.assertIsNotNone(tail_read, msg=stdout)

    def test_reu_source_cache_condition_operators_cross_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            summaries: list[tuple[dict, str, int]] = []
            cases = (
                (
                    "eq",
                    "=",
                    ord("2"),
                    "x main 0 85\n"
                    "x __if0 65 1\n"
                    "x __idata 81 2\n"
                    "x __iptr 83 2\n"
                    "b M\n"
                    "b M\n"
                    "b M\n"
                    "b M\n"
                    "m A2 00 BD 00 00 85 06 E8 BD 00 00 85 07 A9 01 48 A9 00 48 "
                    "A9 02 48 A9 00 48 68 85 05 68 85 04 68 85 03 68 C5 04 D0 06 "
                    "A5 03 C5 05 F0 03 4C 00 00 A9 01 48 A9 00 48 68 AA 68 A0 00 "
                    "91 06 C8 8A 91 06 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C "
                    "0F CF 00 00 00 00\n"
                    "r 3 x __iptr\n"
                    "r 9 x __iptr\n"
                    "r 46 x __if0\n"
                    "r 83 x __idata\n"
                    "i 1\n"
                    "i 2\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "lt",
                    "<",
                    ord("2"),
                    "x main 0 84\n"
                    "x __if0 64 1\n"
                    "x __idata 80 2\n"
                    "x __iptr 82 2\n"
                    "b M\n"
                    "b M\n"
                    "b M\n"
                    "b M\n"
                    "m A2 00 BD 00 00 85 06 E8 BD 00 00 85 07 A9 01 48 A9 00 48 "
                    "A9 02 48 A9 00 48 68 85 05 68 85 04 68 AA 68 E4 05 90 09 "
                    "D0 04 C5 04 90 03 4C 00 00 A9 01 48 A9 00 48 68 AA 68 A0 00 "
                    "91 06 C8 8A 91 06 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C "
                    "0F CF 00 00 00 00\n"
                    "r 3 x __iptr\n"
                    "r 9 x __iptr\n"
                    "r 45 x __if0\n"
                    "r 82 x __idata\n"
                    "i 1\n"
                    "i 2\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "gt",
                    ">",
                    ord("2"),
                    "x main 0 86\n"
                    "x __if0 66 1\n"
                    "x __idata 82 2\n"
                    "x __iptr 84 2\n"
                    "b M\n"
                    "b M\n"
                    "b M\n"
                    "b M\n"
                    "m A2 00 BD 00 00 85 06 E8 BD 00 00 85 07 A9 01 48 A9 00 48 "
                    "A9 02 48 A9 00 48 68 85 05 68 85 04 68 AA 68 E4 05 90 08 "
                    "D0 09 C5 04 90 02 D0 03 4C 00 00 A9 01 48 A9 00 48 68 AA "
                    "68 A0 00 91 06 C8 8A 91 06 A9 A5 8D D0 03 A9 00 85 02 85 03 "
                    "A2 02 4C 0F CF 00 00 00 00\n"
                    "r 3 x __iptr\n"
                    "r 9 x __iptr\n"
                    "r 47 x __if0\n"
                    "r 84 x __idata\n"
                    "i 1\n"
                    "i 2\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "le",
                    "<=",
                    ord("="),
                    "x main 0 86\n"
                    "x __if0 66 1\n"
                    "x __idata 82 2\n"
                    "x __iptr 84 2\n"
                    "b M\n"
                    "b M\n"
                    "b M\n"
                    "b M\n"
                    "m A2 00 BD 00 00 85 06 E8 BD 00 00 85 07 A9 01 48 A9 00 48 "
                    "A9 02 48 A9 00 48 68 85 05 68 85 04 68 AA 68 E4 05 90 0B "
                    "D0 06 C5 04 90 05 F0 03 4C 00 00 A9 01 48 A9 00 48 68 AA "
                    "68 A0 00 91 06 C8 8A 91 06 A9 A5 8D D0 03 A9 00 85 02 85 03 "
                    "A2 02 4C 0F CF 00 00 00 00\n"
                    "r 3 x __iptr\n"
                    "r 9 x __iptr\n"
                    "r 47 x __if0\n"
                    "r 84 x __idata\n"
                    "i 1\n"
                    "i 2\n"
                    "i 0\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "ge",
                    ">=",
                    ord("="),
                    "x main 0 84\n"
                    "x __if0 64 1\n"
                    "x __idata 80 2\n"
                    "x __iptr 82 2\n"
                    "b M\n"
                    "b M\n"
                    "b M\n"
                    "b M\n"
                    "m A2 00 BD 00 00 85 06 E8 BD 00 00 85 07 A9 01 48 A9 00 48 "
                    "A9 02 48 A9 00 48 68 85 05 68 85 04 68 AA 68 E4 05 90 06 "
                    "D0 07 C5 04 B0 03 4C 00 00 A9 01 48 A9 00 48 68 AA 68 A0 "
                    "00 91 06 C8 8A 91 06 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 "
                    "02 4C 0F CF 00 00 00 00\n"
                    "r 3 x __iptr\n"
                    "r 9 x __iptr\n"
                    "r 45 x __if0\n"
                    "r 82 x __idata\n"
                    "i 1\n"
                    "i 2\n"
                    "i 0\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "ne",
                    "<>",
                    ord(">"),
                    "x main 0 85\n"
                    "x __if0 65 1\n"
                    "x __idata 81 2\n"
                    "x __iptr 83 2\n"
                    "b M\n"
                    "b M\n"
                    "b M\n"
                    "b M\n"
                    "m A2 00 BD 00 00 85 06 E8 BD 00 00 85 07 A9 01 48 A9 00 48 "
                    "A9 02 48 A9 00 48 68 85 05 68 85 04 68 85 03 68 C5 04 D0 09 "
                    "A5 03 C5 05 D0 03 4C 00 00 A9 01 48 A9 00 48 68 AA 68 A0 00 "
                    "91 06 C8 8A 91 06 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C "
                    "0F CF 00 00 00 00\n"
                    "r 3 x __iptr\n"
                    "r 9 x __iptr\n"
                    "r 46 x __if0\n"
                    "r 83 x __idata\n"
                    "i 1\n"
                    "i 2\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
            )

            for case_name, operator, tail_byte, expected_body in cases:
                workspace = Path(tmpdir) / f"actc-reu-page-condition-{case_name}"
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                prefix = "MODULE MAIN\rINT A=[0]\rPROC MAIN()\rIF 1"
                operator_offset = 255
                filler_len = operator_offset - len(prefix)
                self.assertGreaterEqual(filler_len, 0)
                source = prefix + (" " * filler_len) + operator + "2 THEN\rA=1\rFI\rRETURN\r"
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "18000000",
                    ]
                )

                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                self.assert_single_proc_object(
                    (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                    expected_body,
                    min_line=3,
                    debug_op_count=10 if case_name in {"le", "ge"} else 8,
                )
                summaries.append((summary, result.stdout, tail_byte))

        for summary, stdout, tail_byte in summaries:
            tail_read = next(
                (
                    op
                    for op in summary["ops"]
                    if op["kind"] == "rrd"
                    and op["params"][0:3] == [0, 1, 1]
                    and op.get("head", [None])[0] == tail_byte
                ),
                None,
            )
            self.assertIsNotNone(tail_read, msg=stdout)

    def test_reu_source_cache_runtime_real_condition_operators_cross_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            cases = (
                ("eq", "=", ord("B"), "b L0U0L1U1u0p0qhvr\n", 1),
                ("lt", "<", ord("B"), "b L0U0L1U1u0p0lhvr\n", 1),
                ("gt", ">", ord("B"), "b L0U0L1U1u0p0ghvr\n", 1),
                ("le", "<=", ord("="), "b L0U0L1U1u0p0lhvr\n", 2),
                ("ge", ">=", ord("="), "b L0U0L1U1u0p0ghvr\n", 0),
                ("ne", "<>", ord(">"), "b L0U0L1U1u0p0nhvr\n", 1),
            )
            for case_name, operator, tail_byte, expected_body, compare_literal in cases:
                with self.subTest(case=case_name):
                    workspace = Path(tmpdir) / f"actc-reu-page-runtime-real-condition-{case_name}"
                    project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                    source_dir = project_root / "src"
                    object_dir = project_root / "obj"
                    source_dir.mkdir(parents=True)
                    object_dir.mkdir()
                    (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                    prefix = "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\rIF A"
                    operator_offset = 255
                    filler_len = operator_offset - len(prefix)
                    self.assertGreaterEqual(filler_len, 0)
                    source = prefix + (" " * filler_len) + operator + "B THEN\rFI\rRETURN\r"
                    self.assertEqual(source.index(operator, len(prefix)), operator_offset)
                    self.assertEqual(ord(source[256]), tail_byte)
                    (source_dir / "main.act").write_text(source, encoding="ascii")

                    result = self.run_checked(
                        [
                            str(self.build_dir / "tool_abi_harness"),
                            "--prg",
                            str(self.build_dir / "ACTC_REU.PRG"),
                            "--workspace",
                            str(project_root),
                            "--cmdline",
                            "MAIN",
                            "--services-inc",
                            str(self.build_dir / "udos_services.inc"),
                            "--labels",
                            str(self.build_dir / "actc.reu.current.labels"),
                            "--max-steps",
                            "18000000",
                        ]
                    )

                    summary = json.loads(result.stdout)
                    self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                    self.assertFalse(summary["hit_limit"], msg=result.stdout)
                    self.assert_single_proc_object(
                        (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                        "x main 0 23\n"
                        + expected_body
                        + "u rt_f_cmp\n"
                        + f"i {compare_literal}\n"
                        + "v a 0 4\n"
                        + "v b 0 4\n"
                        + "k 0\n"
                        + "n main\n",
                        min_line=3,
                    )
                    self.assertTrue(
                        any(
                            op["kind"] == "rrd"
                            and op["params"][0:3] == [0, 1, 1]
                            and op.get("head", [None])[0] == tail_byte
                            for op in summary["ops"]
                        ),
                        msg=result.stdout,
                    )

    def test_reu_source_cache_resident_runtime_real_conversion_tokens_cross_page_aligned_window_without_lookahead(
        self,
    ) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={
                "ACTC_USE_BODY_OVERLAY": "0",
                "ACTC_KEEP_BODY_RESIDENT_FALLBACK": "1",
                "ACTC_ENABLE_REAL_CONST_EVALUATOR": "0",
                "ACTC_SOURCE_WINDOW": "256",
                "ACTC_SOURCE_LOOKAHEAD": "0",
            },
        )

        expected_object = (
            "x main 0 23\n"
            "b L0u0L1U1u1p0lhvr\n"
            "u rt_i_to_f\n"
            "u rt_f_cmp\n"
            "i 1\n"
            "v c 7\n"
            "v a 0 4\n"
            "k 0\n"
            "n main\n"
        )
        signed_expected_object = (
            "x main 0 23\n"
            "b L0U0p0u0u1p1ghvr\n"
            "u rt_s_to_f\n"
            "u rt_f_cmp\n"
            "i 65529\n"
            "i 1\n"
            "v a 0 4\n"
            "k 0\n"
            "n main\n"
        )
        prefix = "MODULE MAIN\rCARD C=[7]\rREAL A\rPROC MAIN()\rIF "
        signed_prefix = "MODULE MAIN\rREAL A\rPROC MAIN()\rIF A>"
        cases = (
            ("keyword", prefix, "", "REAL", "(C)<A THEN\rFI\rRETURN\r", 254, ord("A"), expected_object),
            ("open", prefix, "REAL", "(", "C)<A THEN\rFI\rRETURN\r", 255, ord("C"), expected_object),
            ("close", prefix, "REAL(C", ")", "<A THEN\rFI\rRETURN\r", 255, ord("<"), expected_object),
            (
                "signed-zero",
                signed_prefix,
                "REAL(",
                "0",
                "-7) THEN\rFI\rRETURN\r",
                255,
                ord("-"),
                signed_expected_object,
            ),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            for (
                case_name,
                case_prefix,
                fixed_before,
                token,
                trailing,
                token_offset,
                page_head,
                case_expected_object,
            ) in cases:
                with self.subTest(case=case_name):
                    workspace = Path(tmpdir) / f"actc-reu-page-resident-real-conversion-{case_name}"
                    project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                    source_dir = project_root / "src"
                    object_dir = project_root / "obj"
                    source_dir.mkdir(parents=True)
                    object_dir.mkdir()
                    (project_root / "ACTION.PROJ").write_text(
                        "ACTION PROJECT\rMAIN.ACT\r",
                        encoding="ascii",
                    )

                    filler_len = token_offset - len(case_prefix) - len(fixed_before)
                    self.assertGreaterEqual(filler_len, 0)
                    source = case_prefix + (" " * filler_len) + fixed_before + token + trailing
                    self.assertEqual(source[token_offset : token_offset + len(token)], token)
                    self.assertEqual(ord(source[256]), page_head)
                    (source_dir / "main.act").write_text(source, encoding="ascii")

                    result = self.run_checked(
                        [
                            str(self.build_dir / "tool_abi_harness"),
                            "--prg",
                            str(self.build_dir / "ACTC_REU.PRG"),
                            "--workspace",
                            str(project_root),
                            "--cmdline",
                            "MAIN",
                            "--services-inc",
                            str(self.build_dir / "udos_services.inc"),
                            "--labels",
                            str(self.build_dir / "actc.reu.current.labels"),
                            "--max-steps",
                            "24000000",
                        ]
                    )

                    summary = json.loads(result.stdout)
                    self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                    self.assertFalse(summary["hit_limit"], msg=result.stdout)
                    self.assert_single_proc_object(
                        (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                        case_expected_object,
                        min_line=3,
                    )
                    self.assertTrue(
                        any(
                            op["kind"] == "rrd"
                            and op["params"][0:3] == [0, 1, 1]
                            and op.get("head", [None])[0] == page_head
                            for op in summary["ops"]
                        ),
                        msg=result.stdout,
                    )

            workspace = Path(tmpdir) / "actc-reu-page-resident-real-conversion-reject-double-zero"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text(
                "ACTION PROJECT\rMAIN.ACT\r",
                encoding="ascii",
            )
            token_offset = 255
            fixed_before = "REAL("
            filler_len = token_offset - len(signed_prefix) - len(fixed_before)
            source = signed_prefix + (" " * filler_len) + fixed_before + "00-7) THEN\rFI\rRETURN\r"
            self.assertEqual(source[token_offset : token_offset + 2], "00")
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = subprocess.run(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "24000000",
                ],
                cwd=self.root,
                text=True,
                capture_output=True,
                check=False,
                timeout=120,
            )
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 1, msg=result.stdout)
            self.assertEqual(summary["console"], "BAD LITERAL\n", msg=result.stdout)
            self.assertFalse((object_dir / "MAIN.OBJ").exists())
            self.assertTrue(
                any(
                    op["kind"] == "rrd"
                    and op["params"][0:3] == [0, 1, 1]
                    and op.get("head", [None])[0] == ord("0")
                    for op in summary["ops"]
                ),
                msg=result.stdout,
            )

    def test_reu_source_cache_runtime_arithmetic_operators_cross_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            cases = (
                (
                    "add",
                    "+",
                    (
                        "x main 0 78\nx __idata 74 2\nx __iptr 76 2\n",
                        "b u0M\nb M\nb M\n",
                        "r 3 x __iptr\nr 9 x __iptr\nr 51 u0\nr 76 x __idata\n",
                    ),
                    "u rt_print_i\n",
                ),
                (
                    "sub",
                    "-",
                    (
                        "x main 0 78\nx __idata 74 2\nx __iptr 76 2\n",
                        "b u0M\nb M\nb M\n",
                        "r 3 x __iptr\nr 9 x __iptr\nr 51 u0\nr 76 x __idata\n",
                    ),
                    "u rt_print_i\n",
                ),
                (
                    "mul",
                    "*",
                    (
                        "x main 0 82\nx __idata 78 2\nx __iptr 80 2\n",
                        "b u0u1M\nb M\nb M\n",
                        "r 3 x __iptr\nr 9 x __iptr\nr 46 u0\nr 55 u1\nr 80 x __idata\n",
                    ),
                    "u rt_i_mul\nu rt_print_i\n",
                ),
                (
                    "div",
                    "/",
                    (
                        "x main 0 82\nx __idata 78 2\nx __iptr 80 2\n",
                        "b u0u1M\nb M\nb M\n",
                        "r 3 x __iptr\nr 9 x __iptr\nr 46 u0\nr 55 u1\nr 80 x __idata\n",
                    ),
                    "u rt_i_div\nu rt_print_i\n",
                ),
            )
            for case_name, operator, expected_fragments, expected_imports in cases:
                with self.subTest(case=case_name):
                    workspace = Path(tmpdir) / f"actc-reu-page-runtime-sum-{case_name}"
                    project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                    source_dir = project_root / "src"
                    object_dir = project_root / "obj"
                    source_dir.mkdir(parents=True)
                    object_dir.mkdir()
                    (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                    prefix = "MODULE MAIN\rINT A=[3]\rPROC MAIN()\rPrintIE(A"
                    operator_offset = 255
                    filler_len = operator_offset - len(prefix)
                    self.assertGreaterEqual(filler_len, 0)
                    source = prefix + (" " * filler_len) + operator + "2)\rRETURN\r"
                    self.assertEqual(source.index(operator, len(prefix)), operator_offset)
                    (source_dir / "main.act").write_text(source, encoding="ascii")

                    result = self.run_checked(
                        [
                            str(self.build_dir / "tool_abi_harness"),
                            "--prg",
                            str(self.build_dir / "ACTC_REU.PRG"),
                            "--workspace",
                            str(project_root),
                            "--cmdline",
                            "MAIN",
                            "--services-inc",
                            str(self.build_dir / "udos_services.inc"),
                            "--labels",
                            str(self.build_dir / "actc.reu.current.labels"),
                            "--max-steps",
                            "18000000",
                        ]
                    )

                    summary = json.loads(result.stdout)
                    self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                    self.assertFalse(summary["hit_limit"], msg=result.stdout)
                    obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
                    for fragment in expected_fragments:
                        self.assertIn(fragment, obj)
                    if expected_imports:
                        self.assertIn(expected_imports, obj)
                    else:
                        self.assertNotIn("u rt_i_mul\n", obj)
                        self.assertNotIn("u rt_i_div\n", obj)
                        self.assertNotIn("u rt_print_i\n", obj)
                    self.assertIn("i 2\n", obj)
                    self.assertIn("v a 3\n", obj)
                    self.assertTrue(
                        any(
                            op["kind"] == "rrd"
                            and op["params"][0:3] == [0, 1, 1]
                            and op.get("head", [None])[0] == ord("2")
                            for op in summary["ops"]
                        ),
                        msg=result.stdout,
                    )

    def test_reu_source_cache_assignment_bool_expr_crosses_y_wrap(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            summaries: list[tuple[dict, str]] = []
            cases = (
                (
                    "and",
                    "1" + (" " * 320) + "AND 1",
                    "x main 0 23\n"
                    "b p0p1np2p3nap4gS0r\n"
                    "i 1\n"
                    "i 0\n"
                    "i 1\n"
                    "i 0\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "or",
                    "0" + (" " * 320) + "OR 1",
                    "x main 0 23\n"
                    "b p0p1np2p3nap4gS0r\n"
                    "i 0\n"
                    "i 0\n"
                    "i 1\n"
                    "i 0\n"
                    "i 0\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "not",
                    (" " * 320) + "NOT 0",
                    "x main 0 15\n"
                    "b p0p1np2qS0r\n"
                    "i 0\n"
                    "i 0\n"
                    "i 0\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
            )

            for case_name, expression, expected_body in cases:
                workspace = Path(tmpdir) / f"actc-reu-assignment-bool-{case_name}"
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                prefix = "MODULE MAIN\rINT A=[0]\rPROC MAIN()\r"
                assignment_prefix = "A="
                filler_len = 20470 - len(prefix) - len(assignment_prefix)
                self.assertGreaterEqual(filler_len, 0)
                source = (
                    prefix
                    + ("\r" * filler_len)
                    + assignment_prefix
                    + expression
                    + "\rRETURN\r"
                )
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "22000000",
                    ]
                )

                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                self.assert_single_proc_object(
                    (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                    expected_body,
                    min_line=3,
                )
                summaries.append((summary, result.stdout))

        for summary, stdout in summaries:
            later_reads = [
                op
                for op in summary["ops"]
                if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
            ]
            self.assertTrue(later_reads, msg=stdout)

    def test_reu_source_cache_assignment_bool_keyword_crosses_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-assignment-bool-page-aligned-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rINT A=[0]\rPROC MAIN()\rA=1 "
            keyword_offset = 254
            filler_len = keyword_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + (" " * filler_len) + "AND 1\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "15000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 23\n"
                "b p0p1np2p3nap4gS0r\n"
                "i 1\n"
                "i 0\n"
                "i 1\n"
                "i 0\n"
                "i 1\n"
                "v a 0\n"
                "k 0\n"
                "n main\n",
                min_line=3,
            )

        tail_read = next(
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1]
        )
        self.assertGreater(tail_read["actual_len"], 0)

    def test_reu_source_cache_if_bool_condition_crosses_y_wrap(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            summaries: list[tuple[dict, str]] = []
            cases = (
                (
                    "and",
                    "1" + (" " * 320) + "AND 1",
                    "x main 0 29\n"
                    "b p0p1np2p3nap4ghp5S0vr\n"
                    "i 1\n"
                    "i 0\n"
                    "i 1\n"
                    "i 0\n"
                    "i 1\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "or",
                    "0" + (" " * 320) + "OR 1",
                    "x main 0 29\n"
                    "b p0p1np2p3nap4ghp5S0vr\n"
                    "i 0\n"
                    "i 0\n"
                    "i 1\n"
                    "i 0\n"
                    "i 0\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "not",
                    (" " * 320) + "NOT 0",
                    "x main 0 21\n"
                    "b p0p1np2qhp3S0vr\n"
                    "i 0\n"
                    "i 0\n"
                    "i 0\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
            )

            for case_name, expression, expected_body in cases:
                workspace = Path(tmpdir) / f"actc-reu-if-bool-{case_name}"
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                prefix = "MODULE MAIN\rINT A=[0]\rPROC MAIN()\r"
                if_prefix = "IF "
                filler_len = 20470 - len(prefix) - len(if_prefix)
                self.assertGreaterEqual(filler_len, 0)
                source = (
                    prefix
                    + ("\r" * filler_len)
                    + if_prefix
                    + expression
                    + " THEN\rA=1\rFI\rRETURN\r"
                )
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "26000000",
                    ]
                )

                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                self.assert_single_proc_object(
                    (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                    expected_body,
                    min_line=3,
                )
                summaries.append((summary, result.stdout))

        for summary, stdout in summaries:
            later_reads = [
                op
                for op in summary["ops"]
                if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
            ]
            rewound_reads = [
                op
                for op in summary["ops"]
                if op["kind"] == "rrd" and op["params"][0:3] == [0, 0, 1]
            ]
            self.assertTrue(later_reads, msg=stdout)
            self.assertTrue(rewound_reads, msg=stdout)

    def test_reu_source_cache_loop_bool_conditions_cross_y_wrap(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            summaries: list[tuple[dict, str]] = []
            cases = (
                (
                    "while-and",
                    "while",
                    "1" + (" " * 320) + "AND 1",
                    "x main 0 32\n"
                    "b dp0p1np2p3nap4gfp5S0xr\n"
                    "i 1\n"
                    "i 0\n"
                    "i 1\n"
                    "i 0\n"
                    "i 1\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "while-or",
                    "while",
                    "0" + (" " * 320) + "OR 1",
                    "x main 0 32\n"
                    "b dp0p1np2p3nap4gfp5S0xr\n"
                    "i 0\n"
                    "i 0\n"
                    "i 1\n"
                    "i 0\n"
                    "i 0\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "while-not",
                    "while",
                    (" " * 320) + "NOT 0",
                    "x main 0 24\n"
                    "b dp0p1np2qfp3S0xr\n"
                    "i 0\n"
                    "i 0\n"
                    "i 0\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "until-and",
                    "until",
                    "1" + (" " * 320) + "AND 1",
                    "x main 0 29\n"
                    "b dp0S0p1p2np3p4nap5gtor\n"
                    "i 1\n"
                    "i 1\n"
                    "i 0\n"
                    "i 1\n"
                    "i 0\n"
                    "i 1\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "until-or",
                    "until",
                    "0" + (" " * 320) + "OR 1",
                    "x main 0 29\n"
                    "b dp0S0p1p2np3p4nap5gtor\n"
                    "i 1\n"
                    "i 0\n"
                    "i 0\n"
                    "i 1\n"
                    "i 0\n"
                    "i 0\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "until-not",
                    "until",
                    (" " * 320) + "NOT 0",
                    "x main 0 21\n"
                    "b dp0S0p1p2np3qtor\n"
                    "i 1\n"
                    "i 0\n"
                    "i 0\n"
                    "i 0\n"
                    "v a 0\n"
                    "k 0\n"
                    "n main\n",
                ),
            )

            for case_name, loop_kind, expression, expected_body in cases:
                workspace = Path(tmpdir) / f"actc-reu-loop-bool-{case_name}"
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                prefix = "MODULE MAIN\rINT A=[0]\rPROC MAIN()\r"
                if loop_kind == "while":
                    loop_prefix = "WHILE "
                    filler_len = 20470 - len(prefix) - len(loop_prefix)
                    self.assertGreaterEqual(filler_len, 0)
                    source = (
                        prefix
                        + ("\r" * filler_len)
                        + loop_prefix
                        + expression
                        + " DO\rA=1\rOD\rRETURN\r"
                    )
                else:
                    loop_body_prefix = prefix + "DO\rA=1\r"
                    loop_prefix = "UNTIL "
                    filler_len = 20470 - len(loop_body_prefix) - len(loop_prefix)
                    self.assertGreaterEqual(filler_len, 0)
                    source = (
                        loop_body_prefix
                        + ("\r" * filler_len)
                        + loop_prefix
                        + expression
                        + "\rOD\rRETURN\r"
                    )
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "28000000",
                    ]
                )

                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                self.assert_single_proc_object(
                    (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                    expected_body,
                    min_line=3,
                )
                summaries.append((summary, result.stdout))

        for summary, stdout in summaries:
            later_reads = [
                op
                for op in summary["ops"]
                if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
            ]
            rewound_reads = [
                op
                for op in summary["ops"]
                if op["kind"] == "rrd" and op["params"][0:3] == [0, 0, 1]
            ]
            self.assertTrue(later_reads, msg=stdout)
            self.assertTrue(rewound_reads, msg=stdout)

    def test_reu_source_cache_return_and_local_bool_exprs_cross_y_wrap(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            summaries: list[tuple[dict, str]] = []
            cases = (
                (
                    "return-and",
                    "return",
                    "1" + (" " * 320) + "AND 1",
                    "x main 0 20\n"
                    "b p0p1np2p3nap4gr\n"
                    "i 1\n"
                    "i 0\n"
                    "i 1\n"
                    "i 0\n"
                    "i 1\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "return-or",
                    "return",
                    "0" + (" " * 320) + "OR 1",
                    "x main 0 20\n"
                    "b p0p1np2p3nap4gr\n"
                    "i 0\n"
                    "i 0\n"
                    "i 1\n"
                    "i 0\n"
                    "i 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "return-not",
                    "return",
                    (" " * 320) + "NOT 0",
                    "x main 0 12\n"
                    "b p0p1np2qr\n"
                    "i 0\n"
                    "i 0\n"
                    "i 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "local-and",
                    "local",
                    "1" + (" " * 320) + "AND 1",
                    "x main 0 26\n"
                    "b p0p1np2p3nap4gS0L0r\n"
                    "i 1\n"
                    "i 0\n"
                    "i 1\n"
                    "i 0\n"
                    "i 1\n"
                    "v l 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "local-or",
                    "local",
                    "0" + (" " * 320) + "OR 1",
                    "x main 0 26\n"
                    "b p0p1np2p3nap4gS0L0r\n"
                    "i 0\n"
                    "i 0\n"
                    "i 1\n"
                    "i 0\n"
                    "i 0\n"
                    "v l 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "local-not",
                    "local",
                    (" " * 320) + "NOT 0",
                    "x main 0 18\n"
                    "b p0p1np2qS0L0r\n"
                    "i 0\n"
                    "i 0\n"
                    "i 0\n"
                    "v l 0\n"
                    "k 0\n"
                    "n main\n",
                ),
            )

            for case_name, body_kind, expression, expected_body in cases:
                workspace = Path(tmpdir) / f"actc-reu-body-bool-{case_name}"
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                prefix = "MODULE MAIN\rPROC MAIN()\r"
                if body_kind == "return":
                    return_prefix = "RETURN "
                    filler_len = 20470 - len(prefix) - len(return_prefix)
                    self.assertGreaterEqual(filler_len, 0)
                    source = prefix + ("\r" * filler_len) + return_prefix + expression + "\r"
                else:
                    decl_prefix = "INT L="
                    filler_len = 20470 - len(prefix) - len(decl_prefix)
                    self.assertGreaterEqual(filler_len, 0)
                    source = prefix + ("\r" * filler_len) + decl_prefix + expression + "\rRETURN L\r"
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "28000000",
                    ]
                )

                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                self.assert_single_proc_object(
                    (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                    expected_body,
                    min_line=2,
                )
                summaries.append((summary, result.stdout))

        for summary, stdout in summaries:
            later_reads = [
                op
                for op in summary["ops"]
                if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
            ]
            rewound_reads = [
                op
                for op in summary["ops"]
                if op["kind"] == "rrd" and op["params"][0:3] == [0, 0, 1]
            ]
            self.assertTrue(later_reads, msg=stdout)
            self.assertTrue(rewound_reads, msg=stdout)

    def test_reu_source_cache_call_bool_args_cross_y_wrap(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            summaries: list[tuple[dict, str]] = []
            cases = (
                (
                    "and",
                    "1" + (" " * 320) + "AND 1",
                    "x help 0 4\n"
                    "x main 4 23\n"
                    "b S0r\n"
                    "b p0p1np2p3nap4gc0r\n"
                    "i 1\n"
                    "i 0\n"
                    "i 1\n"
                    "i 0\n"
                    "i 1\n"
                    "v n 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "or",
                    "0" + (" " * 320) + "OR 1",
                    "x help 0 4\n"
                    "x main 4 23\n"
                    "b S0r\n"
                    "b p0p1np2p3nap4gc0r\n"
                    "i 0\n"
                    "i 0\n"
                    "i 1\n"
                    "i 0\n"
                    "i 0\n"
                    "v n 0\n"
                    "k 0\n"
                    "n main\n",
                ),
                (
                    "not",
                    (" " * 320) + "NOT 0",
                    "x help 0 4\n"
                    "x main 4 15\n"
                    "b S0r\n"
                    "b p0p1np2qc0r\n"
                    "i 0\n"
                    "i 0\n"
                    "i 0\n"
                    "v n 0\n"
                    "k 0\n"
                    "n main\n",
                ),
            )

            for case_name, expression, expected_tail in cases:
                workspace = Path(tmpdir) / f"actc-reu-call-bool-{case_name}"
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                prefix = "MODULE MAIN\rPROC HELP(N)\rRETURN\rPROC MAIN()\r"
                call_prefix = "HELP("
                filler_len = 20470 - len(prefix) - len(call_prefix)
                self.assertGreaterEqual(filler_len, 0)
                source = prefix + ("\r" * filler_len) + call_prefix + expression + ")\rRETURN\r"
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "30000000",
                    ]
                )

                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
                self.assertRegex(obj, r"^OBJ1\nf 0 src/main\.act\nq 0 0 2 6\nq 1 0 4 6\n")
                self.assertIn("V p i 0 0 0 2 11\n", obj)
                self.assertTrue(obj.endswith(expected_tail), msg=obj)
                summaries.append((summary, result.stdout))

        for summary, stdout in summaries:
            later_reads = [
                op
                for op in summary["ops"]
                if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
            ]
            rewound_reads = [
                op
                for op in summary["ops"]
                if op["kind"] == "rrd" and op["params"][0:3] == [0, 0, 1]
            ]
            self.assertTrue(later_reads, msg=stdout)
            self.assertTrue(rewound_reads, msg=stdout)

    def test_reu_source_cache_call_arg_punctuation_crosses_y_wrap(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            summaries: list[tuple[dict, str]] = []
            two_arg_tail = native_two_arg_local_call_object_tail()
            cases = (
                (
                    "comma-after-first-arg",
                    "MODULE MAIN\rPROC HELP(A,B)\rRETURN\rPROC MAIN()\r",
                    "HELP(",
                    "1" + (" " * 320) + ",2)",
                    two_arg_tail,
                ),
                (
                    "close-after-second-arg",
                    "MODULE MAIN\rPROC HELP(A,B)\rRETURN\rPROC MAIN()\r",
                    "HELP(",
                    "1,2" + (" " * 320) + ")",
                    two_arg_tail,
                ),
                (
                    "close-after-single-arg",
                    "MODULE MAIN\rPROC HELP(N)\rRETURN\rPROC MAIN()\r",
                    "HELP(",
                    "1" + (" " * 320) + ")",
                    native_one_arg_local_call_object_tail(),
                ),
            )

            for case_name, prefix, call_prefix, call_text, expected_tail in cases:
                workspace = Path(tmpdir) / f"actc-reu-call-punct-{case_name}"
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                filler_len = 20470 - len(prefix) - len(call_prefix)
                self.assertGreaterEqual(filler_len, 0)
                source = prefix + ("\r" * filler_len) + call_prefix + call_text + "\rRETURN\r"
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "30000000",
                    ]
                )

                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
                self.assertRegex(obj, r"^OBJ1\nf 0 src/main\.act\nq 0 0 2 6\nq 1 0 4 6\n")
                self.assertTrue(obj.endswith(expected_tail), msg=obj)
                summaries.append((summary, result.stdout))

        for summary, stdout in summaries:
            later_reads = [
                op
                for op in summary["ops"]
                if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
            ]
            rewound_reads = [
                op
                for op in summary["ops"]
                if op["kind"] == "rrd" and op["params"][0:3] == [0, 0, 1]
            ]
            self.assertTrue(later_reads, msg=stdout)
            self.assertTrue(rewound_reads, msg=stdout)

    def test_reu_source_cache_call_arg_punctuation_crosses_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            summaries: list[tuple[dict, str, int]] = []
            two_arg_tail = native_two_arg_local_call_object_tail()
            one_arg_tail = native_one_arg_local_call_object_tail()
            cases = (
                (
                    "open-paren",
                    "MODULE MAIN\rPROC HELP(N)\rRETURN\rPROC MAIN()\r",
                    "HELP",
                    "(",
                    "1)",
                    ord("1"),
                    one_arg_tail,
                ),
                (
                    "comma-after-first-arg",
                    "MODULE MAIN\rPROC HELP(A,B)\rRETURN\rPROC MAIN()\r",
                    "HELP(1",
                    ",",
                    "2)",
                    ord("2"),
                    two_arg_tail,
                ),
                (
                    "close-after-single-arg",
                    "MODULE MAIN\rPROC HELP(N)\rRETURN\rPROC MAIN()\r",
                    "HELP(1",
                    ")",
                    "",
                    ord("\r"),
                    one_arg_tail,
                ),
            )

            for case_name, prefix, before_punctuation, punctuation, after_punctuation, tail_byte, expected_tail in cases:
                workspace = Path(tmpdir) / f"actc-reu-page-call-punct-{case_name}"
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                punctuation_offset = 255
                filler_len = punctuation_offset - len(prefix) - len(before_punctuation)
                self.assertGreaterEqual(filler_len, 0)
                source = (
                    prefix
                    + (" " * filler_len)
                    + before_punctuation
                    + punctuation
                    + after_punctuation
                    + "\rRETURN\r"
                )
                self.assertEqual(source.index(punctuation, len(prefix) + filler_len), punctuation_offset)
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "18000000",
                    ]
                )

                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
                self.assertRegex(obj, r"^OBJ1\nf 0 src/main\.act\nq 0 0 2 6\nq 1 0 4 6\n")
                self.assertTrue(obj.endswith(expected_tail), msg=obj)
                summaries.append((summary, result.stdout, tail_byte))

        for summary, stdout, tail_byte in summaries:
            tail_read = next(
                (
                    op
                    for op in summary["ops"]
                    if op["kind"] == "rrd"
                    and op["params"][0:3] == [0, 1, 1]
                    and op.get("head", [None])[0] == tail_byte
                ),
                None,
            )
            self.assertIsNotNone(tail_read, msg=stdout)

    def test_reu_source_cache_proc_param_open_paren_can_sit_at_y_wrap(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-param-wrap"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\r"
            proc_prefix = "PROC "
            proc_name_offset = 20470
            filler_len = proc_name_offset - len(prefix) - len(proc_prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = (
                prefix
                + ("\r" * filler_len)
                + proc_prefix
                + "MAIN"
                + (" " * 251)
                + "(N)\rRETURN N\r"
            )
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "18000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 7\n"
                "b S0L0r\n"
                "v n 0\n"
                "k 0\n"
                "n main\n",
            )

        later_reads = [
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
        ]
        self.assertTrue(later_reads, msg=result.stdout)

    def test_reu_source_cache_conversion_keywords_cross_y_wraps(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            def compile_source(case_name: str, source: str) -> tuple[dict, str, str]:
                workspace = Path(tmpdir) / case_name
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "22000000",
                    ]
                )
                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
                tail_reads = [
                    op
                    for op in summary["ops"]
                    if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
                ]
                self.assertTrue(tail_reads, msg=result.stdout)
                return summary, obj, result.stdout

            real_prefix = "MODULE MAIN\rREAL A\rPROC MAIN()\r"
            real_filler_len = 20470 - len(real_prefix)
            self.assertGreaterEqual(real_filler_len, 0)
            real_source = (
                real_prefix
                + ("\r" * real_filler_len)
                + "A="
                + (" " * 253)
                + "REAL(7)\rRETURN\r"
            )
            _, real_obj, _ = compile_source("actc-reu-real-keyword-wrap", real_source)
            self.assertIn("u rt_i_to_f\n", real_obj)
            self.assertIn("i 7\n", real_obj)

            int_prefix = "MODULE MAIN\rREAL A\rINT X\rPROC MAIN()\r"
            int_filler_len = 20470 - len(int_prefix)
            self.assertGreaterEqual(int_filler_len, 0)
            int_source = (
                int_prefix
                + ("\r" * int_filler_len)
                + "X="
                + (" " * 253)
                + "INT(A)\rRETURN\r"
            )
            _, int_obj, _ = compile_source("actc-reu-int-keyword-wrap", int_source)
            self.assertIn("u rt_f_to_i\n", int_obj)

    def test_reu_source_cache_conversion_keywords_cross_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            def compile_source(case_name: str, prefix: str, conversion: str) -> tuple[dict, str, str]:
                workspace = Path(tmpdir) / case_name
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                conversion_offset = 254
                filler_len = conversion_offset - len(prefix)
                self.assertGreaterEqual(filler_len, 0)
                source = prefix + (" " * filler_len) + conversion + "\rRETURN\r"
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "24000000",
                    ]
                )
                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
                self.assertTrue(
                    any(op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1] for op in summary["ops"]),
                    msg=result.stdout,
                )
                return summary, obj, result.stdout

            _, real_obj, _ = compile_source(
                "actc-reu-page-real-keyword-no-lookahead",
                "MODULE MAIN\rREAL A\rPROC MAIN()\rA=",
                "REAL(7)",
            )
            self.assertIn("u rt_i_to_f\n", real_obj)
            self.assertIn("i 7\n", real_obj)

            _, int_obj, _ = compile_source(
                "actc-reu-page-int-keyword-no-lookahead",
                "MODULE MAIN\rREAL A\rINT X\rPROC MAIN()\rX=",
                "INT(A)",
            )
            self.assertIn("u rt_f_to_i\n", int_obj)

    def test_positive_word_tokens_cross_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            def compile_expression(case_name: str, token_offset: int, expression: str) -> str:
                workspace = Path(tmpdir) / case_name
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                prefix = "MODULE MAIN\rREAL A\rPROC MAIN()\rA=REAL("
                filler_len = token_offset - len(prefix)
                self.assertGreaterEqual(filler_len, 0)
                source = prefix + (" " * filler_len) + expression + ")\rRETURN\r"
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "30000000",
                    ]
                )
                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                self.assertTrue(
                    any(op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1] for op in summary["ops"]),
                    msg=result.stdout,
                )
                return (object_dir / "MAIN.OBJ").read_text(encoding="ascii")

            decimal_obj = compile_expression("decimal-token-cross", 250, "65500+35")
            self.assertIn("u rt_i_to_f\n", decimal_obj)
            self.assertIn("i 65535\n", decimal_obj)

            symbol_obj = compile_expression("symbol-token-cross", 254, "SID_TRI+1")
            self.assertIn("u rt_i_to_f\n", symbol_obj)
            self.assertIn("i 17\n", symbol_obj)

            signed_obj = compile_expression("grouped-token-cross", 254, "0-(32767+1)")
            self.assertIn("u rt_s_to_f\n", signed_obj)
            self.assertIn("i 32768\n", signed_obj)

            nested_obj = compile_expression("nested-token-cross", 254, "2*(3+4)")
            self.assertIn("u rt_i_to_f\n", nested_obj)
            self.assertIn("i 14\n", nested_obj)

    def test_small_numeric_tokens_cross_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            for name, literal in (("decimal", "255"), ("hex", "$FF"), ("binary", "%11111111")):
                with self.subTest(radix=name):
                    workspace = Path(tmpdir) / f"actc-reu-small-{name}-token-cross"
                    project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                    source_dir = project_root / "src"
                    object_dir = project_root / "obj"
                    source_dir.mkdir(parents=True)
                    object_dir.mkdir()
                    (project_root / "ACTION.PROJ").write_text(
                        "ACTION PROJECT\rMAIN.ACT\r", encoding="ascii"
                    )

                    prefix = "MODULE MAIN\rPROC MAIN()\rPrintIE("
                    token_offset = 254
                    filler_len = token_offset - len(prefix)
                    self.assertGreaterEqual(filler_len, 0)
                    source = prefix + (" " * filler_len) + literal + ")\rRETURN\r"
                    (source_dir / "main.act").write_text(source, encoding="ascii")

                    result = self.run_checked(
                        [
                            str(self.build_dir / "tool_abi_harness"),
                            "--prg",
                            str(self.build_dir / "ACTC_REU.PRG"),
                            "--workspace",
                            str(project_root),
                            "--cmdline",
                            "MAIN",
                            "--services-inc",
                            str(self.build_dir / "udos_services.inc"),
                            "--labels",
                            str(self.build_dir / "actc.reu.current.labels"),
                            "--max-steps",
                            "16000000",
                        ]
                    )

                    summary = json.loads(result.stdout)
                    self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                    self.assertFalse(summary["hit_limit"], msg=result.stdout)
                    obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
                    self.assertIn("b i0r\n", obj)
                    self.assertIn("i 255\n", obj)
                    self.assertTrue(
                        any(
                            op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1]
                            for op in summary["ops"]
                        ),
                        msg=result.stdout,
                    )

    def test_reu_source_cache_small_value_delimiters_cross_page_aligned_window_without_lookahead(
        self,
    ) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={
                "ACTC_USE_BODY_OVERLAY": "0",
                "ACTC_KEEP_BODY_RESIDENT_FALLBACK": "1",
                "ACTC_ENABLE_REAL_CONST_EVALUATOR": "0",
                "ACTC_SOURCE_WINDOW": "256",
                "ACTC_SOURCE_LOOKAHEAD": "0",
            },
        )

        module_object = (
            "x main 0 1\n"
            "b r\n"
            "v a 7\n"
            "k 0\n"
            "n main\n"
        )
        small_object = (
            "x main 0 7\n"
            "b i0r\n"
            "i 7\n"
            "k 6\n"
            "n main\n"
        )
        runtime_object = (
            "x main 0 7\n"
            "b L0zr\n"
            "v a 3\n"
            "k 6\n"
            "n main\n"
        )
        cases = (
            (
                "module-equals",
                "MODULE MAIN\rINT A",
                "=",
                "[7]\rPROC MAIN()\rRETURN\r",
                ord("["),
                module_object,
            ),
            (
                "module-open",
                "MODULE MAIN\rINT A=",
                "[",
                "7]\rPROC MAIN()\rRETURN\r",
                ord("7"),
                module_object,
            ),
            (
                "module-close",
                "MODULE MAIN\rINT A=[7",
                "]",
                "\rPROC MAIN()\rRETURN\r",
                13,
                module_object,
            ),
            (
                "small-equals",
                "MODULE MAIN\rPROC MAIN()\rPrintIE(",
                "=",
                "[7])\rRETURN\r",
                ord("["),
                small_object,
            ),
            (
                "small-open",
                "MODULE MAIN\rPROC MAIN()\rPrintIE(=",
                "[",
                "7])\rRETURN\r",
                ord("7"),
                small_object,
            ),
            (
                "small-close",
                "MODULE MAIN\rPROC MAIN()\rPrintIE(=[7",
                "]",
                ")\rRETURN\r",
                ord(")"),
                small_object,
            ),
            (
                "runtime-equals",
                "MODULE MAIN\rINT A=[3]\rPROC MAIN()\rPrintIE(",
                "=",
                "[A])\rRETURN\r",
                ord("["),
                runtime_object,
            ),
            (
                "runtime-open",
                "MODULE MAIN\rINT A=[3]\rPROC MAIN()\rPrintIE(=",
                "[",
                "A])\rRETURN\r",
                ord("A"),
                runtime_object,
            ),
            (
                "runtime-close",
                "MODULE MAIN\rINT A=[3]\rPROC MAIN()\rPrintIE(=[A",
                "]",
                ")\rRETURN\r",
                ord(")"),
                runtime_object,
            ),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            for case_name, prefix, token, trailing, page_head, expected_object in cases:
                with self.subTest(case=case_name):
                    workspace = Path(tmpdir) / f"actc-reu-page-small-delimiter-{case_name}"
                    project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                    source_dir = project_root / "src"
                    object_dir = project_root / "obj"
                    source_dir.mkdir(parents=True)
                    object_dir.mkdir()
                    (project_root / "ACTION.PROJ").write_text(
                        "ACTION PROJECT\rMAIN.ACT\r",
                        encoding="ascii",
                    )

                    token_offset = 255
                    filler_len = token_offset - len(prefix)
                    self.assertGreaterEqual(filler_len, 0)
                    source = prefix + (" " * filler_len) + token + trailing
                    self.assertEqual(source[token_offset], token)
                    self.assertEqual(ord(source[256]), page_head)
                    (source_dir / "main.act").write_text(source, encoding="ascii")

                    result = self.run_checked(
                        [
                            str(self.build_dir / "tool_abi_harness"),
                            "--prg",
                            str(self.build_dir / "ACTC_REU.PRG"),
                            "--workspace",
                            str(project_root),
                            "--cmdline",
                            "MAIN",
                            "--services-inc",
                            str(self.build_dir / "udos_services.inc"),
                            "--labels",
                            str(self.build_dir / "actc.reu.current.labels"),
                            "--max-steps",
                            "24000000",
                        ]
                    )

                    summary = json.loads(result.stdout)
                    self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                    self.assertFalse(summary["hit_limit"], msg=result.stdout)
                    self.assert_single_proc_object(
                        (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                        expected_object,
                    )
                    self.assertTrue(
                        any(
                            op["kind"] == "rrd"
                            and op["params"][0:3] == [0, 1, 1]
                            and op.get("head", [None])[0] == page_head
                            for op in summary["ops"]
                        ),
                        msg=result.stdout,
                    )

    def test_reu_source_cache_overlay_runtime_fallback_restores_failed_literal_probe(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={
                "ACTC_USE_BODY_OVERLAY": "1",
                "ACTC_KEEP_BODY_RESIDENT_FALLBACK": "0",
                "ACTC_SOURCE_WINDOW": "256",
                "ACTC_SOURCE_LOOKAHEAD": "0",
            },
        )

        expected_object = (
            "x main 0 7\n"
            "b L0zr\n"
            "v a 3\n"
            "k 6\n"
            "n main\n"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text(
                "ACTION PROJECT\rMAIN.ACT\r",
                encoding="ascii",
            )

            prefix = "MODULE MAIN\rINT A=[3]\rPROC MAIN()\rPrintIE("
            filler_len = 255 - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + (" " * filler_len) + "=[A])\rRETURN\r"
            self.assertEqual(source[255:257], "=[")
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "24000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                expected_object,
            )
            self.assertTrue(
                any(
                    op["kind"] == "rrd"
                    and op["params"][0:3] == [0, 1, 1]
                    and op.get("head", [None])[0] == ord("[")
                    for op in summary["ops"]
                ),
                msg=result.stdout,
            )

    def test_small_boolean_keyword_crosses_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-small-bool-token-cross"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rPROC MAIN()\rPrintIE(1 "
            keyword_offset = 255
            filler_len = keyword_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + (" " * filler_len) + "OR 0)\rRETURN\r"
            self.assertEqual(source.index("OR 0"), keyword_offset)
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "16000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b i0r\n", obj)
            self.assertIn("i 1\n", obj)
            self.assertTrue(
                any(op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1] for op in summary["ops"]),
                msg=result.stdout,
            )

    def test_small_comparison_tail_preserves_outer_state_across_nested_rhs(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-small-nested-comparison"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "PrintIE(2>(1=1))\r"
                "PrintIE(0<(2=2))\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "16000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b i0i1r\n", obj)
            self.assertEqual(obj.count("i 1\n"), 2)

    def test_small_boolean_preserves_outer_state_across_nested_rhs(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-small-nested-boolean"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "PrintIE(1 OR 0)\r"
                "PrintIE(0 AND 1)\r"
                "PrintIE(1 OR (0 AND 0))\r"
                "PrintIE(0 AND (1 OR 1))\r"
                "PrintIE(NOT (1 AND 0))\r"
                "PrintIE(NOT NOT 1)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "18000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b i0i1i2i3i4i5r\n", obj)
            values = [int(value) for value in re.findall(r"^i (-?\d+)$", obj, re.MULTILINE)]
            self.assertEqual(values, [1, 0, 1, 0, 1, 1])

    def test_small_arithmetic_preserves_outer_state_across_grouped_rhs(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-small-nested-arithmetic"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "PrintIE(2+(3+4))\r"
                "PrintIE(10-(2+3))\r"
                "PrintIE(2*(3+4))\r"
                "PrintIE(8/(2+2))\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "16000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b i0i1i2i3r\n", obj)
            for value in (9, 5, 14, 2):
                self.assertIn(f"i {value}\n", obj)

    def test_decl_overlay_preserves_outer_comparison_state_across_nested_rhs(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-decl-nested-comparison"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "BYTE OP=[2>(1=1)]\r"
                "BYTE LHS=[0<(2=2)]\r"
                "PROC MAIN()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "16000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("v op 1\n", obj)
            self.assertIn("v lhs 1\n", obj)

    def test_reu_source_cache_builtin_helper_names_cross_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            cases = (
                (
                    "joy-helper",
                    "MODULE MAIN\rBYTE J\rPROC MAIN()\rJ=",
                    "Joy(2)",
                    "rt_joy",
                    "joy",
                ),
                (
                    "joy-seen-helper",
                    "MODULE MAIN\rBYTE J\rPROC MAIN()\rJ=",
                    "JoySeen(2)",
                    "rt_jp",
                    "joyseen",
                ),
                (
                    "joy-button1-helper",
                    "MODULE MAIN\rBYTE J\rPROC MAIN()\rJ=",
                    "JoyBtn1(2)",
                    "rt_jb1",
                    "joybtn1",
                ),
                (
                    "joy-button2-helper",
                    "MODULE MAIN\rBYTE J\rPROC MAIN()\rJ=",
                    "JoyBtn2(2)",
                    "rt_jb2",
                    "joybtn2",
                ),
                (
                    "mouse-poll-helper",
                    "MODULE MAIN\rBYTE M\rPROC MAIN()\rM=",
                    "MousePoll(1)",
                    "rt_mp",
                    "mousepoll",
                ),
                (
                    "mouse-seen-helper",
                    "MODULE MAIN\rBYTE M\rPROC MAIN()\rM=",
                    "MouseSeen()",
                    "rt_mseen",
                    "mouseseen",
                ),
                (
                    "mouse-x-helper",
                    "MODULE MAIN\rBYTE M\rPROC MAIN()\rM=",
                    "MouseX()",
                    "rt_mx",
                    "mousex",
                ),
                (
                    "mouse-y-helper",
                    "MODULE MAIN\rBYTE M\rPROC MAIN()\rM=",
                    "MouseY()",
                    "rt_my",
                    "mousey",
                ),
                (
                    "mouse-btn-helper",
                    "MODULE MAIN\rBYTE M\rPROC MAIN()\rM=",
                    "MouseBtn()",
                    "rt_mb",
                    "mousebtn",
                ),
                (
                    "mouse-button1-helper",
                    "MODULE MAIN\rBYTE M\rPROC MAIN()\rM=",
                    "MouseBtn1()",
                    "rt_mb1",
                    "mousebtn1",
                ),
                (
                    "mouse-button2-helper",
                    "MODULE MAIN\rBYTE M\rPROC MAIN()\rM=",
                    "MouseBtn2()",
                    "rt_mb2",
                    "mousebtn2",
                ),
                (
                    "dbf-create-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfCreate(12288)",
                    "rt_dbf_create",
                    "dbfcreate",
                ),
                (
                    "dbf-open-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfOpen(12288)",
                    "rt_dbf_open",
                    "dbfopen",
                ),
                (
                    "dbf-close-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "DbfClose(1)",
                    "rt_dbf_close",
                    "dbfclose",
                ),
                (
                    "dbf-go-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfGo(1,2)",
                    "rt_dbf_go",
                    "dbfgo",
                ),
                (
                    "dbf-field-count-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfFieldCount(1)",
                    "rt_dbf_fieldcount",
                    "dbffieldcount",
                ),
                (
                    "dbf-field-len-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfFieldLen(1,1)",
                    "rt_dbf_fieldlen",
                    "dbffieldlen",
                ),
                (
                    "dbf-read-byte-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfReadByte(1,1)",
                    "rt_dbf_readbyte",
                    "dbfreadbyte",
                ),
                (
                    "dbf-read-field-byte-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfReadFieldByte(1,1,0)",
                    "rt_dbf_readfieldbyte",
                    "dbfreadfieldbyte",
                ),
                (
                    "dbf-write-field-byte-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfWriteFieldByte(1,1,0,90)",
                    "rt_dbf_writefieldbyte",
                    "dbfwritefieldbyte",
                ),
                (
                    "dbf-write-byte-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfWriteByte(1,1,90)",
                    "rt_dbf_writebyte",
                    "dbfwritebyte",
                ),
                (
                    "dbf-append-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfAppend(1)",
                    "rt_dbf_append",
                    "dbfappend",
                ),
                (
                    "dbf-pack-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfPack(1)",
                    "rt_dbf_pack",
                    "dbfpack",
                ),
                (
                    "dbf-save-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfSave(1)",
                    "rt_dbf_save",
                    "dbfsave",
                ),
                (
                    "dbf-delete-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfDelete(1)",
                    "rt_dbf_delete",
                    "dbfdelete",
                ),
                (
                    "dbf-undelete-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfUndelete(1)",
                    "rt_dbf_undelete",
                    "dbfundelete",
                ),
                (
                    "dbf-deleted-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfDeleted(1)",
                    "rt_dbf_deleted",
                    "dbfdeleted",
                ),
                (
                    "dbf-header-len-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfHeaderLen(1)",
                    "rt_dbf_headerlen",
                    "dbfheaderlen",
                ),
                (
                    "dbf-record-len-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfRecordLen(1)",
                    "rt_dbf_recordlen",
                    "dbfrecordlen",
                ),
                (
                    "dbf-total-recs-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfTotalRecs(1)",
                    "rt_dbf_totalrecs",
                    "dbftotalrecs",
                ),
                (
                    "dbf-curr-rec-no-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "DbfCurrRecNo(1)",
                    "rt_dbf_currrecno",
                    "dbfcurrrecno",
                ),
                (
                    "gfx-vic-bank-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "VicBank(1)",
                    "rt_gfx_vic_bank",
                    "vicbank",
                ),
                (
                    "gfx-bg-color-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "BgColor(6)",
                    "rt_gfx_bgcolor",
                    "bgcolor",
                ),
                (
                    "gfx-border-color-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "BorderColor(14)",
                    "rt_gfx_bordercolor",
                    "bordercolor",
                ),
                (
                    "gfx-screen-base-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "ScreenBase(1024)",
                    "rt_gfx_screen_base",
                    "screenbase",
                ),
                (
                    "gfx-bitmap-base-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "BitmapBase(8192)",
                    "rt_gfx_bitmap_base",
                    "bitmapbase",
                ),
                (
                    "gfx-screen-cell-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "ScreenCell(5,2,65)",
                    "rt_gfx_screen_cell",
                    "screencell",
                ),
                (
                    "gfx-color-cell-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "ColorCell(5,2,10)",
                    "rt_gfx_color_cell",
                    "colorcell",
                ),
                (
                    "gfx-screen-copy-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "ScreenCopy(12288)",
                    "rt_gfx_screen_copy",
                    "screencopy",
                ),
                (
                    "gfx-color-copy-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "ColorCopy(12304)",
                    "rt_gfx_color_copy",
                    "colorcopy",
                ),
                (
                    "gfx-bitmap-fill-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "BitmapFill(60)",
                    "rt_gfx_bitmap_fill",
                    "bitmapfill",
                ),
                (
                    "gfx-bitmap-copy-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "BitmapCopy(20480)",
                    "rt_gfx_bitmap_copy",
                    "bitmapcopy",
                ),
                (
                    "gfx-bitmap-on-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "BitmapOn()",
                    "rt_gfx_bitmap_on",
                    "bitmapon",
                ),
                (
                    "gfx-bitmap-off-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "BitmapOff()",
                    "rt_gfx_bitmap_off",
                    "bitmapoff",
                ),
                (
                    "gfx-mbitmap-on-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "MBitmapOn()",
                    "rt_gfx_mbitmap_on",
                    "mbitmapon",
                ),
                (
                    "gfx-mbitmap-off-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "MBitmapOff()",
                    "rt_gfx_mbitmap_off",
                    "mbitmapoff",
                ),
                (
                    "sprite-hit-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "SpriteHit()",
                    "rt_sprite_hit",
                    "spritehit",
                ),
                (
                    "sprite-hit-bg-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "SpriteHitBg()",
                    "rt_sprite_hit_bg",
                    "spritehitbg",
                ),
                (
                    "sid-osc3-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "SidOsc3()",
                    "rt_sid_osc3",
                    "sidosc3",
                ),
                (
                    "sid-env3-helper",
                    "MODULE MAIN\rBYTE H\rPROC MAIN()\rH=",
                    "SidEnv3()",
                    "rt_sid_env3",
                    "sidenv3",
                ),
                (
                    "sprite-on-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SpriteOn(2)",
                    "rt_sprite_on",
                    "spriteon",
                ),
                (
                    "sprite-off-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SpriteOff(2)",
                    "rt_sprite_off",
                    "spriteoff",
                ),
                (
                    "sprite-pos-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SpritePos(2,52,86)",
                    "rt_sprite_pos",
                    "spritepos",
                ),
                (
                    "sprite-ptr-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SpritePtr(2,128)",
                    "rt_sprite_ptr",
                    "spriteptr",
                ),
                (
                    "sprite-data-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SpriteData(2,8192)",
                    "rt_sprite_data",
                    "spritedata",
                ),
                (
                    "sprite-color-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SpriteColor(2,5)",
                    "rt_sprite_color",
                    "spritecolor",
                ),
                (
                    "sprite-mc-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SpriteMC(2,1)",
                    "rt_sprite_mc",
                    "spritemc",
                ),
                (
                    "sprite-xexp-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SpriteXExp(2,1)",
                    "rt_sprite_xexp",
                    "spritexexp",
                ),
                (
                    "sprite-yexp-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SpriteYExp(2,1)",
                    "rt_sprite_yexp",
                    "spriteyexp",
                ),
                (
                    "sprite-prio-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SpritePrio(2,1)",
                    "rt_sprite_prio",
                    "spriteprio",
                ),
                (
                    "sprite-set-mc-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SetSpriteMC(5,10)",
                    "rt_sprite_set_mc",
                    "setspritemc",
                ),
                (
                    "sid-freq-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SidFreq(1,4660)",
                    "rt_sid_freq",
                    "sidfreq",
                ),
                (
                    "sid-pulse-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SidPulse(1,52)",
                    "rt_sid_pulse",
                    "sidpulse",
                ),
                (
                    "sid-wave-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SidWave(1,64)",
                    "rt_sid_wave",
                    "sidwave",
                ),
                (
                    "sid-ad-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SidAD(1,151)",
                    "rt_sid_ad",
                    "sidad",
                ),
                (
                    "sid-sr-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SidSR(1,248)",
                    "rt_sid_sr",
                    "sidsr",
                ),
                (
                    "sid-on-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SidOn(1)",
                    "rt_sid_on",
                    "sidon",
                ),
                (
                    "sid-off-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SidOff(1)",
                    "rt_sid_off",
                    "sidoff",
                ),
                (
                    "sid-vol-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SidVol(10)",
                    "rt_sid_vol",
                    "sidvol",
                ),
                (
                    "sid-cutoff-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SidCutoff(52)",
                    "rt_sid_cutoff",
                    "sidcutoff",
                ),
                (
                    "sid-res-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SidRes(10)",
                    "rt_sid_res",
                    "sidres",
                ),
                (
                    "sid-mode-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SidMode(48)",
                    "rt_sid_mode",
                    "sidmode",
                ),
                (
                    "sid-route-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SidRoute(7)",
                    "rt_sid_route",
                    "sidroute",
                ),
                (
                    "sid-rst-helper",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "SidRst()",
                    "rt_sid_rst",
                    "sidrst",
                ),
                (
                    "math-print-r-helper",
                    "MODULE MAIN\rREAL A\rPROC MAIN()\r",
                    "PrintR(A)",
                    "rt_print_f",
                    "printr",
                ),
                (
                    "math-print-re-helper",
                    "MODULE MAIN\rREAL A\rPROC MAIN()\r",
                    "PrintRE(A)",
                    "rt_print_f",
                    "printre",
                ),
                (
                    "math-fabs-helper",
                    "MODULE MAIN\rREAL A\rREAL R\rPROC MAIN()\rR=",
                    "FABS(A)",
                    "rt_f_abs",
                    "fabs",
                ),
                (
                    "math-fsqrt-helper",
                    "MODULE MAIN\rREAL A\rREAL R\rPROC MAIN()\rR=",
                    "FSQRT(A)",
                    "rt_f_sqrt",
                    "fsqrt",
                ),
            )

            for case_name, prefix, helper_call, runtime_import, stale_import in cases:
                with self.subTest(case=case_name):
                    workspace = Path(tmpdir) / f"actc-reu-page-helper-name-{case_name}"
                    project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                    source_dir = project_root / "src"
                    object_dir = project_root / "obj"
                    source_dir.mkdir(parents=True)
                    object_dir.mkdir()
                    (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                    helper_offset = 254
                    filler_len = helper_offset - len(prefix)
                    self.assertGreaterEqual(filler_len, 0)
                    source = prefix + (" " * filler_len) + helper_call + "\rRETURN\r"
                    (source_dir / "main.act").write_text(source, encoding="ascii")

                    result = self.run_checked(
                        [
                            str(self.build_dir / "tool_abi_harness"),
                            "--prg",
                            str(self.build_dir / "ACTC_REU.PRG"),
                            "--workspace",
                            str(project_root),
                            "--cmdline",
                            "MAIN",
                            "--services-inc",
                            str(self.build_dir / "udos_services.inc"),
                            "--labels",
                            str(self.build_dir / "actc.reu.current.labels"),
                            "--max-steps",
                            "24000000",
                        ]
                    )
                    summary = json.loads(result.stdout)
                    self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                    self.assertFalse(summary["hit_limit"], msg=result.stdout)
                    obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
                    self.assertIn(f"u {runtime_import}\n", obj)
                    self.assertNotIn(f"u {stale_import}\n", obj)
                    self.assertTrue(
                        any(op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1] for op in summary["ops"]),
                        msg=result.stdout,
                    )

    def test_reu_source_cache_long_builtin_helper_name_spans_tiny_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "16", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-long-helper-name-tiny-window-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rBYTE H\rPROC MAIN()\rH="
            helper_offset = 62
            filler_len = helper_offset - len(prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = prefix + (" " * filler_len) + "DbfWriteFieldByte(1,1,0,90)\rRETURN\r"
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "26000000",
                ]
            )
            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_dbf_writefieldbyte\n", obj)
            self.assertNotIn("u dbfwritefieldbyte\n", obj)
            self.assertTrue(
                any(op["kind"] == "rrd" and op["params"][0:3] == [16, 0, 1] for op in summary["ops"]),
                msg=result.stdout,
            )

    def test_reu_source_cache_builtin_constants_cross_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            cases = (
                (
                    "joy-buttons",
                    "JMASK",
                    "JOY_UP+JOY_BUTTON1+JOY_BUTTON2",
                    49,
                ),
                (
                    "joy-directions",
                    "JDIR",
                    "JOY_UP+JOY_DOWN+JOY_LEFT+JOY_RIGHT",
                    15,
                ),
                (
                    "mouse-buttons",
                    "MMASK",
                    "MOUSE_BUTTON1+MOUSE_BUTTON2",
                    3,
                ),
                (
                    "sid-wave-mask",
                    "WAVE",
                    "SID_TRI+SID_SAW+SID_PULSE+SID_NOISE",
                    240,
                ),
                (
                    "sid-filter-mask",
                    "FILT",
                    "SID_LOW+SID_BAND+SID_HIGH",
                    112,
                ),
                (
                    "sprite-priority",
                    "PRIO",
                    "SPR_FRONT+SPR_BACK",
                    1,
                ),
            )

            for case_name, var_name, expression, expected_value in cases:
                with self.subTest(case=case_name):
                    workspace = Path(tmpdir) / f"actc-reu-page-builtin-constant-{case_name}"
                    project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                    source_dir = project_root / "src"
                    object_dir = project_root / "obj"
                    source_dir.mkdir(parents=True)
                    object_dir.mkdir()
                    (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                    prefix = f"MODULE MAIN\rBYTE {var_name}\rPROC MAIN()\r{var_name}="
                    constant_offset = 254
                    filler_len = constant_offset - len(prefix)
                    self.assertGreaterEqual(filler_len, 0)
                    source = prefix + (" " * filler_len) + expression + "\rRETURN\r"
                    (source_dir / "main.act").write_text(source, encoding="ascii")

                    result = self.run_checked(
                        [
                            str(self.build_dir / "tool_abi_harness"),
                            "--prg",
                            str(self.build_dir / "ACTC_REU.PRG"),
                            "--workspace",
                            str(project_root),
                            "--cmdline",
                            "MAIN",
                            "--services-inc",
                            str(self.build_dir / "udos_services.inc"),
                            "--labels",
                            str(self.build_dir / "actc.reu.current.labels"),
                            "--max-steps",
                            "24000000",
                        ]
                    )
                    summary = json.loads(result.stdout)
                    self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                    self.assertFalse(summary["hit_limit"], msg=result.stdout)
                    obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
                    self.assertIn(f"i {expected_value}\n", obj)
                    self.assertIn(f"v {var_name.lower()} 0\n", obj)
                    self.assertNotIn("u ", obj)
                    self.assertTrue(
                        any(op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1] for op in summary["ops"]),
                        msg=result.stdout,
                    )

    def test_reu_source_cache_initializer_builtin_constants_cross_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            cases = (
                (
                    "joy-buttons",
                    "JMASK",
                    "JOY_UP+JOY_BUTTON1+JOY_BUTTON2",
                    49,
                ),
                (
                    "joy-directions",
                    "JDIR",
                    "JOY_UP+JOY_DOWN+JOY_LEFT+JOY_RIGHT",
                    15,
                ),
                (
                    "mouse-buttons",
                    "MMASK",
                    "MOUSE_BUTTON1+MOUSE_BUTTON2",
                    3,
                ),
                (
                    "sid-wave-mask",
                    "WAVE",
                    "SID_TRI+SID_SAW+SID_PULSE+SID_NOISE",
                    240,
                ),
                (
                    "sid-filter-mask",
                    "FILT",
                    "SID_LOW+SID_BAND+SID_HIGH",
                    112,
                ),
                (
                    "sprite-priority",
                    "PRIO",
                    "SPR_FRONT+SPR_BACK",
                    1,
                ),
            )

            for case_name, var_name, expression, expected_value in cases:
                with self.subTest(case=case_name):
                    workspace = Path(tmpdir) / f"actc-reu-page-init-builtin-constant-{case_name}"
                    project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                    source_dir = project_root / "src"
                    object_dir = project_root / "obj"
                    source_dir.mkdir(parents=True)
                    object_dir.mkdir()
                    (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                    prefix = f"MODULE MAIN\rBYTE {var_name}=["
                    constant_offset = 254
                    filler_len = constant_offset - len(prefix)
                    self.assertGreaterEqual(filler_len, 0)
                    source = prefix + (" " * filler_len) + expression + "]\rPROC MAIN()\rRETURN\r"
                    (source_dir / "main.act").write_text(source, encoding="ascii")

                    result = self.run_checked(
                        [
                            str(self.build_dir / "tool_abi_harness"),
                            "--prg",
                            str(self.build_dir / "ACTC_REU.PRG"),
                            "--workspace",
                            str(project_root),
                            "--cmdline",
                            "MAIN",
                            "--services-inc",
                            str(self.build_dir / "udos_services.inc"),
                            "--labels",
                            str(self.build_dir / "actc.reu.current.labels"),
                            "--max-steps",
                            "24000000",
                        ]
                    )
                    summary = json.loads(result.stdout)
                    self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                    self.assertFalse(summary["hit_limit"], msg=result.stdout)
                    obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
                    self.assertIn(f"v {var_name.lower()} {expected_value}\n", obj)
                    self.assertNotIn("u ", obj)
                    self.assertTrue(
                        any(op["kind"] == "rrd" and op["params"][0:3] == [0, 1, 1] for op in summary["ops"]),
                        msg=result.stdout,
                    )

    def test_reu_source_cache_runtime_group_restore_crosses_y_wrap(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-runtime-group-restore"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rPROC MAIN()\r"
            print_prefix = "PrintIE("
            filler_len = 20470 - len(prefix) - len(print_prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = (
                prefix
                + ("\r" * filler_len)
                + print_prefix
                + "("
                + "1"
                + (" " * 254)
                + ")=1)\rRETURN\r"
            )
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "25000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 7\n"
                "b i0r\n"
                "i 1\n"
                "k 6\n"
                "n main\n",
            )

        later_reads = [
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
        ]
        rewound_reads = [
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 0, 1]
        ]
        self.assertTrue(later_reads, msg=result.stdout)
        self.assertTrue(rewound_reads, msg=result.stdout)

    def test_reu_source_cache_const_group_restore_crosses_y_wrap(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-reu-const-group-restore"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\r"
            decl_prefix = "INT X=["
            filler_len = 20470 - len(prefix) - len(decl_prefix)
            self.assertGreaterEqual(filler_len, 0)
            source = (
                prefix
                + ("\r" * filler_len)
                + decl_prefix
                + "("
                + "1"
                + (" " * 254)
                + ")=1]\rPROC MAIN()\rRETURN\r"
            )
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC_REU.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.reu.current.labels"),
                    "--max-steps",
                    "25000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 1\n"
                "b r\n"
                "v x 1\n"
                "k 0\n"
                "n main\n",
                min_line=20000,
            )

        later_reads = [
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
        ]
        rewound_reads = [
            op
            for op in summary["ops"]
            if op["kind"] == "rrd" and op["params"][0:3] == [0, 0, 1]
        ]
        self.assertTrue(later_reads, msg=result.stdout)
        self.assertTrue(rewound_reads, msg=result.stdout)

    def test_reu_source_cache_group_punctuation_crosses_page_aligned_window_without_lookahead(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")],
            env={"ACTC_SOURCE_WINDOW": "256", "ACTC_SOURCE_LOOKAHEAD": "0"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            summaries: list[tuple[dict, str, int]] = []
            runtime_tail = (
                "x main 0 7\n"
                "b i0r\n"
                "i 1\n"
                "k 6\n"
                "n main\n"
            )
            const_bool_tail = (
                "x main 0 1\n"
                "b r\n"
                "v x 1\n"
                "k 0\n"
                "n main\n"
            )
            const_decimal_tail = (
                "x main 0 1\n"
                "b r\n"
                "v x 3\n"
                "k 0\n"
                "n main\n"
            )
            cases = (
                (
                    "runtime-open-paren",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "PrintIE(",
                    "(",
                    "1)=1)\rRETURN\r",
                    ord("1"),
                    runtime_tail,
                ),
                (
                    "runtime-close-paren",
                    "MODULE MAIN\rPROC MAIN()\r",
                    "PrintIE((1",
                    ")",
                    "=1)\rRETURN\r",
                    ord("="),
                    runtime_tail,
                ),
                (
                    "const-open-paren",
                    "MODULE MAIN\r",
                    "INT X=[",
                    "(",
                    "1)=1]\rPROC MAIN()\rRETURN\r",
                    ord("1"),
                    const_bool_tail,
                ),
                (
                    "const-close-paren",
                    "MODULE MAIN\r",
                    "INT X=[(1",
                    ")",
                    "=1]\rPROC MAIN()\rRETURN\r",
                    ord("="),
                    const_bool_tail,
                ),
                (
                    "const-decimal-open-paren",
                    "MODULE MAIN\r",
                    "INT X=[",
                    "(",
                    "3)]\rPROC MAIN()\rRETURN\r",
                    ord("3"),
                    const_decimal_tail,
                ),
                (
                    "const-decimal-close-paren",
                    "MODULE MAIN\r",
                    "INT X=[(3",
                    ")",
                    "]\rPROC MAIN()\rRETURN\r",
                    ord("]"),
                    const_decimal_tail,
                ),
            )

            for case_name, prefix, before_punctuation, punctuation, after_punctuation, tail_byte, expected_tail in cases:
                workspace = Path(tmpdir) / f"actc-reu-page-group-punct-{case_name}"
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                punctuation_offset = 255
                filler_len = punctuation_offset - len(prefix) - len(before_punctuation)
                self.assertGreaterEqual(filler_len, 0)
                source = prefix + (" " * filler_len) + before_punctuation + punctuation + after_punctuation
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "22000000",
                    ]
                )

                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                self.assert_single_proc_object(
                    (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                    expected_tail,
                )
                summaries.append((summary, result.stdout, tail_byte))

        for summary, stdout, tail_byte in summaries:
            tail_read = next(
                (
                    op
                    for op in summary["ops"]
                    if op["kind"] == "rrd"
                    and op["params"][0:3] == [0, 1, 1]
                    and op.get("head", [None])[0] == tail_byte
                ),
                None,
            )
            self.assertIsNotNone(tail_read, msg=stdout)

    def test_reu_source_cache_routes_long_boolean_scan_across_window_boundary(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            summaries: list[tuple[dict, str]] = []
            for case_name, expression in (
                ("and", "1" + (" " * 320) + "AND 1"),
                ("or", "0" + (" " * 320) + "OR 1"),
                ("not", (" " * 320) + "NOT 0"),
            ):
                workspace = Path(tmpdir) / f"actc-reu-boolean-prescan-{case_name}"
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                prefix = "MODULE MAIN\rPROC MAIN()\r"
                print_prefix = "PrintIE("
                filler_len = 20470 - len(prefix) - len(print_prefix)
                self.assertGreaterEqual(filler_len, 0)
                source = (
                    prefix
                    + ("\r" * filler_len)
                    + print_prefix
                    + expression
                    + ")\rRETURN\r"
                )
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "16000000",
                    ]
                )

                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                self.assert_single_proc_object(
                    (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                    "x main 0 7\n"
                    "b i0r\n"
                    "i 1\n"
                    "k 6\n"
                    "n main\n",
                )
                summaries.append((summary, result.stdout))

        for summary, stdout in summaries:
            reu_stage = next(op for op in summary["ops"] if op["kind"] == "rsta")
            later_reads = [
                op
                for op in summary["ops"]
                if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
            ]
            self.assertEqual(reu_stage["path"], "SRC/MAIN.ACT")
            self.assertGreater(reu_stage["actual_len"], 20480)
            self.assertTrue(later_reads, msg=stdout)

    def test_reu_source_cache_parses_const_bool_after_window_boundary_spaces(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_reu_cache_harness_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            summaries: list[tuple[dict, str]] = []
            for case_name, decl_prefix, boundary_tail, second_decl in (
                ("and", "BYTE A=[1", "AND 1]\r", "BYTE B=[0 OR 1]\r"),
                ("or", "BYTE A=[0", "OR 1]\r", "BYTE B=[1 AND 1]\r"),
                ("not", "BYTE A=[", "NOT 0]\r", "BYTE B=[1]\r"),
            ):
                workspace = Path(tmpdir) / f"actc-reu-const-bool-boundary-{case_name}"
                project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
                source_dir = project_root / "src"
                object_dir = project_root / "obj"
                source_dir.mkdir(parents=True)
                object_dir.mkdir()
                (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

                prefix = "MODULE MAIN\r"
                filler_len = 20470 - len(prefix) - len(decl_prefix)
                self.assertGreaterEqual(filler_len, 0)
                source = (
                    prefix
                    + ("\r" * filler_len)
                    + decl_prefix
                    + (" " * 24)
                    + boundary_tail
                    + second_decl
                    + "PROC MAIN()\rRETURN\r"
                )
                (source_dir / "main.act").write_text(source, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC_REU.PRG"),
                        "--workspace",
                        str(project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.reu.current.labels"),
                        "--max-steps",
                        "16000000",
                    ]
                )

                summary = json.loads(result.stdout)
                self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(summary["hit_limit"], msg=result.stdout)
                self.assert_single_proc_object(
                    (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                    "x main 0 1\n"
                    "b r\n"
                    "v a 1\n"
                    "v b 1\n"
                    "k 0\n"
                    "n main\n",
                    min_line=20000,
                )
                summaries.append((summary, result.stdout))

        for summary, stdout in summaries:
            later_reads = [
                op
                for op in summary["ops"]
                if op["kind"] == "rrd" and op["params"][0:3] == [0, 80, 1]
            ]
            rewound_reads = [
                op
                for op in summary["ops"]
                if op["kind"] == "rrd" and op["params"][0:3] == [0, 0, 1]
            ]
            self.assertTrue(later_reads, msg=stdout)
            self.assertTrue(rewound_reads, msg=stdout)


if __name__ == "__main__":
    unittest.main()
