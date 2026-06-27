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
        self.assertIn("jsr source_reader_consume_scan_y", match.group("body"))
        self.assertNotIn("jsr advance_scan_y", match.group("body"))

    def test_line_skipping_consumes_through_source_reader(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        common_load_path = self.root / "src" / "tools_udos" / "common" / "action_project_load.inc"
        common_load_text = common_load_path.read_text(encoding="ascii")
        helper_ranges = (
            (actc_text, "skip_source_line", ".if ACTC_KEEP_DECL_RESIDENT_FALLBACK", "advance_scan_ptr"),
            (common_load_text, "skip_current_line", "skip_line_breaks:", "advance_scan_ptr"),
            (common_load_text, "skip_line_breaks", "source_reader_peek_scan_ptr:", "advance_scan_ptr"),
        )

        for text, label, next_label, raw_advance in helper_ranges:
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr source_reader_peek_scan", body, msg=label)
            self.assertIn("jsr source_reader_consume_scan", body, msg=label)
            self.assertNotIn(f"jsr {raw_advance}", body, msg=label)

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
                self.assertIn("jsr source_reader_consume_scan_y", body, msg=label)
            self.assertNotIn("jsr advance_scan_y", match.group("body"), msg=label)

    def test_keyword_pattern_char_matching_uses_source_reader_helper(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
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
            "consume_keyword_open_from_scan_y": "consume_keyword_from_scan_y:",
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
        self.assertIn("jsr source_reader_try_store_string_literal_byte_from_scan_ptr", body)
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
            r"store_small_decimal_literal_from_scan_ptr:",
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
        self.assertIn("sty reader_scan_y_data", body)
        self.assertIn("jsr source_reader_begin_symbol_token", body)
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
        self.assertIn("jsr source_reader_store_symbol_token_x", helper_body)
        self.assertIn("jsr source_reader_consume_scan_y", helper_body)
        self.assertIn("sty reader_scan_y_data", helper_body)

    def test_symbol_token_helpers_centralize_compatibility_publishing(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        helper_ranges = {
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
                "source_reader_publish_symbol_token:",
                ["lda #$00", "sta reader_token_buffer,y"],
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
        self.assertIn("jsr source_reader_terminate_symbol_token_y", body)
        self.assertIn("jsr source_reader_publish_symbol_token_to_export_ptr", body)
        self.assertIn("sty reader_scan_y_data", body)
        self.assertRegex(
            body,
            r"(?s)jsr source_reader_publish_symbol_token_to_export_ptr.*"
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
            r"source_reader_try_store_symbol_token_x_from_scan_y:",
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
        self.assertIn("sta reader_scan_y_data", body)
        self.assertIn("jsr source_reader_begin_symbol_token", body)
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
        self.assertIn("sta reader_scan_y_data", body)
        self.assertIn("jsr source_reader_begin_symbol_token", body)
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
                "copy_symbol_to_export_name_window:",
                "publish_symbol_token_to_var_name_window",
                "ACTC_OVERLAY_CTX_VAR_NAME_WINDOW_PTR",
            ),
            "copy_symbol_to_export_name_window": (
                "write_var_meta_window:",
                "publish_symbol_token_to_export_name_window",
                "ACTC_OVERLAY_CTX_EXPORT_NAME_WINDOW_PTR",
            ),
        }

        for label, (next_label, publish_helper, direct_context_name) in helper_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                overlay_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            body = match.group("body")
            self.assertIn("jsr load_overlay_symbol_token_ptr", body, msg=label)
            self.assertIn("sta (ACTC_OVERLAY_WORK_ZP),y", body, msg=label)
            self.assertIn("jsr overlay_symbol_token_char_valid_current", body, msg=label)
            self.assertIn(f"jsr {publish_helper}", body, msg=label)
            self.assertNotIn(direct_context_name, body, msg=label)
            self.assertNotIn("jsr uppercase_symbol_start_valid", body, msg=label)
            self.assertNotIn("jsr uppercase_symbol_body_valid", body, msg=label)

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

    def test_decl_count_overlay_inline_spaces_use_peek_consume_wrappers(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        self.assertIn("overlay_source_peek_scan_y:", overlay_text)
        self.assertIn("overlay_source_consume_scan_ptr:", overlay_text)

        match = re.search(
            r"skip_inline_spaces:\n(?P<body>.*?)\nclear_var_name_window:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr overlay_source_peek_scan_y", body)
        self.assertIn("jsr overlay_source_consume_scan_ptr", body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body)
        self.assertNotIn("jsr advance_source_scan", body)

    def test_decl_count_overlay_line_end_uses_peek_wrapper(self) -> None:
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
        self.assertIn("jsr overlay_source_peek_scan_y", body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body)

    def test_decl_count_overlay_var_symbol_reads_use_peek_wrapper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        match = re.search(
            r"copy_symbol_to_var_name_window:\n(?P<body>.*?)\ncopy_symbol_to_export_name_window:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr overlay_source_peek_scan_y", body)
        self.assertIn("jsr overlay_source_consume_scan_ptr", body)
        self.assertNotIn("jsr advance_source_scan", body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body)

    def test_decl_count_overlay_export_symbol_reads_use_peek_wrapper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        match = re.search(
            r"copy_symbol_to_export_name_window:\n(?P<body>.*?)\nwrite_var_meta_window:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr overlay_source_peek_scan_y", body)
        self.assertIn("jsr overlay_source_consume_scan_ptr", body)
        self.assertNotIn("jsr advance_source_scan", body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body)

    def test_decl_count_overlay_proc_param_punctuation_reads_use_peek_wrapper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        match = re.search(
            r"parse_proc_params:\n(?P<body>.*?)\nvalidate_decl_tail:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        body = match.group("body")
        self.assertIn("jsr overlay_source_peek_scan_y", body)
        self.assertIn("jsr overlay_source_consume_scan_ptr", body)
        self.assertNotIn("jsr advance_source_scan", body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body)

    def test_decl_count_overlay_decl_tail_delimiter_reads_use_peek_wrapper(self) -> None:
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
            self.assertIn("jsr overlay_source_peek_scan_y", body, msg=label)
            self.assertIn("jsr overlay_source_consume_scan_ptr", body, msg=label)
            self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body, msg=label)
            self.assertNotIn("jsr advance_source_scan", body, msg=label)

    def test_decl_count_overlay_keyword_reads_use_peek_wrapper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        helper_ranges = {
            "match_keyword_char": "match_keyword_char_fail:",
            "match_keyword_at_scan_delimiter": "match_keyword_at_scan_fail:",
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
            self.assertIn("jsr overlay_source_peek_scan_y", body, msg=label)
            if label == "match_keyword_char":
                self.assertIn("jsr overlay_source_consume_scan_ptr", body, msg=label)
            self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body, msg=label)
            self.assertNotIn("jsr advance_source_scan", body, msg=label)

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

    def test_decl_count_overlay_initializer_expr_reads_use_peek_wrapper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_decl_counts.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        helper_ranges = {
            "validate_initializer_expr": "validate_bracket_initializer_expr:",
            "validate_bracket_initializer_expr_loop": "validate_bracket_initializer_expr_done:",
            "validate_line_initializer_expr_loop": "validate_line_initializer_expr_done:",
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
            self.assertIn("jsr overlay_source_peek_scan_y", body, msg=label)
            if label == "match_keyword_char":
                self.assertIn("jsr overlay_source_consume_scan_ptr", body, msg=label)
                self.assertNotIn("jsr advance_source_scan", body, msg=label)
            self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body, msg=label)

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
        self.assertIn("jsr overlay_source_peek_scan_y", body)
        self.assertIn("jsr overlay_source_consume_scan_ptr", body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body)
        self.assertNotIn("jsr advance_source_scan", body)

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
        self.assertEqual(skip_blank_match.group("body").strip(), "jmp skip_source_whitespace")

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
        self.assertEqual(len(direct_scan_store_positions), 3)
        self.assertTrue(
            all(writeback_start <= pos < writeback_end for pos in direct_scan_store_positions),
            msg="direct SCAN_ZP writes should only publish resident declaration counts",
        )

        cache_store_positions = [
            match.start()
            for match in re.finditer(r"\bsta \(ACTC_OVERLAY_CACHE_ZP\),y", overlay_text)
        ]
        cache_store_match = re.search(
            r"copy_work_window_to_scan_cache:\n(?P<body>.*?)\nsetup_var_cache_ptr_x:",
            overlay_text,
            re.DOTALL,
        )
        self.assertIsNotNone(cache_store_match)
        assert cache_store_match is not None
        cache_store_start, cache_store_end = cache_store_match.span("body")
        self.assertEqual(len(cache_store_positions), 1)
        self.assertTrue(
            all(cache_store_start <= pos < cache_store_end for pos in cache_store_positions),
            msg="cache alias writes should stay inside the cache-copy helper",
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
        self.assertIn("jsr overlay_source_peek_scan_y", whitespace_body)
        self.assertIn("jsr overlay_source_consume_scan_ptr", whitespace_body)
        self.assertNotIn("jsr advance_source_scan", whitespace_body)
        self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", whitespace_body)

    def test_source_header_overlay_source_reads_go_through_local_peek(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_source_header.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
        self.assertIn("source_header_peek_scan_y:", overlay_text)
        self.assertIn("source_header_consume_scan_y:", overlay_text)

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
            "skip_source_spaces": "match_module_keyword:",
            "match_module_keyword": "compare_requested_module:",
            "compare_requested_module": "uppercase_ascii:",
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
            self.assertIn("jsr source_header_peek_scan_y", body, msg=label)
            self.assertIn("jsr source_header_consume_scan_y", body, msg=label)
            self.assertNotIn("lda (ACTC_OVERLAY_SCAN_ZP),y", body, msg=label)
            self.assertNotIn("jsr advance_source_scan", body, msg=label)
            if label in {
                "skip_source_whitespace",
                "skip_source_spaces",
                "match_module_keyword",
                "compare_requested_module",
            }:
                self.assertIn("bcs", body, msg=label)
            if label == "compare_requested_module":
                self.assertIn("jsr source_header_symbol_token_char_valid_x", body, msg=label)
                self.assertNotIn("jsr uppercase_symbol_start_valid", body, msg=label)
                self.assertNotIn("jsr uppercase_symbol_body_valid", body, msg=label)

        token_match = re.search(
            r"source_header_symbol_token_char_valid_x:\n(?P<body>.*?)\nuppercase_symbol_start_valid:",
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
                (r"emit_object_peek_payload_y:", r"msg_bad_literal:", "payload peek helper"),
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
            "actc_overlay_noop.asm",
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
            self.assertEqual(len(raw_locations), 3, msg=overlay_name)

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

    def test_body_collect_overlay_terminator_keywords_use_local_source_reader_helper(self) -> None:
        overlay_path = self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_collect.asm"
        overlay_text = overlay_path.read_text(encoding="ascii")
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
            self.assertIn(expected_first_char, body, msg=label)
            self.assertNotIn("jsr uppercase_ascii_local", body, msg=label)
            self.assertNotIn("ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO", body, msg=label)

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
        self.assertIn("jsr call_context_function", helper_body)

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
            r"emit_object_peek_payload_y:\n(?P<body>.*?)\nmsg_bad_literal:",
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
                self.assertIn("jsr advance_scan_ptr_by_local_pattern", overlay_text)
                helper_match = re.search(
                    r"advance_scan_ptr_by_local_pattern:\n(?P<body>.*?)\n"
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
            "store_module_var_from_scan_ptr_or_fail_save_name_done": "store_module_var_from_scan_ptr_or_fail_parse_value:",
            "collect_proc_body_ops_try_local_int_assignment": "collect_proc_body_ops_try_local_int_parse_value:",
            "collect_proc_body_ops_try_local_real_assignment": "collect_proc_body_ops_try_od:",
            "collect_proc_body_ops_try_assignment_word": "collect_proc_body_ops_try_local_call:",
        }

        for label, next_label in delimiter_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{next_label}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            self.assertIn("jsr source_reader_consume_scan_y", match.group("body"), msg=label)
            self.assertNotIn("jsr advance_scan_y", match.group("body"), msg=label)

    def test_runtime_expression_operators_consume_through_source_reader(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        operator_ranges = {
            "store_small_runtime_expr_compare_entry": "store_small_runtime_expr_rhs:",
            "store_runtime_real_print_with_newline_flag_from_scan_ptr": "store_runtime_real_print_with_newline_flag_zero:",
        }

        for label, next_label in operator_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{next_label}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            self.assertIn("jsr source_reader_consume_scan_y", match.group("body"), msg=label)
            self.assertNotIn("jsr advance_scan_y", match.group("body"), msg=label)

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

    def test_call_and_runtime_group_punctuation_consumes_through_source_reader(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        punctuation_ranges = {
            "emit_runtime_group_value_term_from_scan_y_or_fail": "emit_runtime_call_term_from_scan_y_or_fail:",
            "emit_call_args_from_scan_y_or_fail": "emit_runtime_value_from_scan_y_or_fail:",
            "emit_runtime_value_from_scan_y_or_fail": "emit_small_constant_sum_from_scan_y_or_fail:",
        }

        for label, next_label in punctuation_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            self.assertIn("jsr source_reader_consume_scan_y", match.group("body"), msg=label)
            self.assertNotIn("jsr advance_scan_y", match.group("body"), msg=label)

    def test_speculative_scan_loops_consume_through_source_reader(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        scan_ranges = {
            "scan_value_expr_for_top_level_arith_from_scan_y": ".if ACTC_KEEP_BODY_RESIDENT_FALLBACK",
            "scan_print_expr_for_bool_keywords_from_scan_y": ".endif",
            "scan_value_expr_for_bool_tokens_from_scan_y": "emit_runtime_bool_or_from_scan_y_or_fail:",
        }

        for label, next_label in scan_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            self.assertIn("jsr source_reader_consume_scan_y", match.group("body"), msg=label)
            self.assertNotIn("jsr advance_scan_y", match.group("body"), msg=label)

    def test_real_conversion_and_operator_paths_consume_through_source_reader(self) -> None:
        actc_path = self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        actc_text = actc_path.read_text(encoding="ascii")
        real_ranges = {
            "emit_runtime_int_explicit_value_from_scan_y_or_fail": "pack_expr_value_lo_as_positive_real_high_word:",
            "emit_real_explicit_bridge_assignment_from_scan_y_or_fail": "emit_real_explicit_value_after_open_from_scan_y_or_fail:",
            "emit_real_explicit_value_after_open_from_scan_y_or_fail": "emit_real_explicit_value_assignment_from_scan_y_or_fail:",
            "emit_real_wide_signed_int_assignment_from_scan_y_or_fail": "emit_real_bridge_assignment_from_var_index_ok:",
            "emit_real_add_assignment_after_copy_check": "emit_real_copy_assignment_from_scan_y_ok:",
            "emit_real_fabs_assignment_after_open_from_scan_y_or_fail": "resolve_call_target_from_declared_or_fail:",
            "try_consume_real_open_for_runtime_condition_from_scan_y": "emit_runtime_real_explicit_bridge_value_from_scan_y_or_fail:",
            "emit_runtime_real_explicit_bridge_value_from_scan_y_or_fail": "emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail:",
            "emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail": "emit_runtime_real_value_from_scan_y_or_fail:",
            "emit_runtime_real_condition_clause_from_scan_y_or_fail": "emit_runtime_condition_clause_from_scan_y_or_fail:",
        }

        for label, next_label in real_ranges.items():
            match = re.search(
                rf"{label}:\n(?P<body>.*?)\n{re.escape(next_label)}",
                actc_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match, msg=label)
            assert match is not None
            self.assertIn("jsr source_reader_consume_scan_y", match.group("body"), msg=label)
            self.assertNotIn("jsr advance_scan_y", match.group("body"), msg=label)

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
    ) -> None:
        source_name = re.escape(source_stem.lower())
        match = re.match(
            rf"^OBJ1\nf 0 src/{source_name}\.act\nq 0 0 (\d+) (\d+)\n((?:l 0 \d+ 0 \d+ \d+\n)*)",
            text,
        )
        self.assertIsNotNone(match, msg=text)
        assert match is not None
        self.assertGreaterEqual(int(match.group(1)), min_line, msg=text)
        self.assertEqual(int(match.group(2)), 6, msg=text)
        debug_lines = [line for line in match.group(3).splitlines() if line]
        self.assertEqual(len(debug_lines), count_body_ops(body), msg=text)
        for index, line in enumerate(debug_lines):
            self.assertRegex(line, rf"^l 0 {index} 0 \d+ \d+$", msg=text)
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
        self.assertGreater(reu_read["actual_len"], 20480)
        self.assertEqual(reu_read["actual_len"], reu_read["limit"])

    def test_reu_source_cache_module_header_name_crosses_window_without_lookahead(self) -> None:
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

    def test_reu_source_cache_source_header_overlay_skips_multi_window_prefix_without_lookahead(self) -> None:
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
            workspace = Path(tmpdir) / "actc-reu-source-header-overlay-prefix-no-lookahead"
            project_root = workspace / "IMAGES" / "ACTION.DNP" / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            source = (" " * 300) + "MODULE MAIN\rPROC MAIN()\rRETURN\r"
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
            self.assert_single_proc_object(
                (object_dir / "MAIN.OBJ").read_text(encoding="ascii"),
                "x main 0 51\n"
                "b L0L0aL0aL0aL0aL0aL0aL0aL0aL0aL0aL0azr\n"
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
                "x main 0 7\n"
                "b p0S0r\n"
                "i 2\n"
                "v a 1\n"
                "k 0\n"
                "n main\n",
                min_line=3,
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
                "x main 0 7\n"
                "b p0S0r\n"
                "i 2\n"
                "v a 1\n"
                "k 0\n"
                "n main\n",
                min_line=3,
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
                "x main 0 7\n"
                "b p0S0r\n"
                "i 2\n"
                "v a 1\n"
                "k 0\n"
                "n main\n",
                min_line=3,
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
                "x main 0 7\n"
                "b p0S0r\n"
                "i 2\n"
                "v a 1\n"
                "k 0\n"
                "n main\n",
                min_line=3,
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
                "x main 0 7\n"
                "b p0S0r\n"
                "i 2\n"
                "v a 1\n"
                "k 0\n"
                "n main\n",
                min_line=3,
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
                "x main 0 7\n"
                "b p0S0r\n"
                "i 2\n"
                "v abcdefghijklmnopqrstuvw 1\n"
                "k 0\n"
                "n main\n",
                min_line=3,
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
                "x main 0 7\n"
                "b p0S0r\n"
                "i 2\n"
                "v abcdefghijklmnopqrstuvw 1\n"
                "k 0\n"
                "n main\n",
                min_line=3,
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
                "x main 0 7\n"
                "b p0S0r\n"
                "i 2\n"
                "v abcdefghijklmnopqrstuvw 1\n"
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
                "x main 0 7\n"
                "b p0S0r\n"
                "i 2\n"
                "v abcdefghijklmnopqrstuvw 1\n"
                "k 0\n"
                "n main\n",
                min_line=3,
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
                    "x main 0 17\n"
                    "b p0p1qhp2S0vr\n"
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
                    "x main 0 17\n"
                    "b p0p1lhp2S0vr\n"
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
                    "x main 0 17\n"
                    "b p0p1ghp2S0vr\n"
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
                    "x main 0 21\n"
                    "b p0p1gp2qhp3S0vr\n"
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
                    "x main 0 21\n"
                    "b p0p1lp2qhp3S0vr\n"
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
                    "x main 0 17\n"
                    "b p0p1nhp2S0vr\n"
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
                    "b dp0S0p1p2np3p4nap5gtr\n"
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
                    "b dp0S0p1p2np3p4nap5gtr\n"
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
                    "b dp0S0p1p2np3qtr\n"
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
            two_arg_tail = (
                "x help 0 7\n"
                "x main 7 10\n"
                "b S1S0r\n"
                "b p0p1c0r\n"
                "i 1\n"
                "i 2\n"
                "v a 0\n"
                "v b 0\n"
                "k 0\n"
                "n main\n"
            )
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
                    "x help 0 4\n"
                    "x main 4 7\n"
                    "b S0r\n"
                    "b p0c0r\n"
                    "i 1\n"
                    "v n 0\n"
                    "k 0\n"
                    "n main\n",
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
            two_arg_tail = (
                "x help 0 7\n"
                "x main 7 10\n"
                "b S1S0r\n"
                "b p0p1c0r\n"
                "i 1\n"
                "i 2\n"
                "v a 0\n"
                "v b 0\n"
                "k 0\n"
                "n main\n"
            )
            one_arg_tail = (
                "x help 0 4\n"
                "x main 4 7\n"
                "b S0r\n"
                "b p0c0r\n"
                "i 1\n"
                "v n 0\n"
                "k 0\n"
                "n main\n"
            )
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
