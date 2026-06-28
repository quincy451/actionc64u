from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest


class TestActcOverlay(unittest.TestCase):
    CTX_SIZE = 233
    ACTC_BODY_OVERLAY_MIN_HEADROOM = 0x80
    ACTC_OVERLAY_WINDOW_SIZE = 0x2000

    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.build_dir = self.root / "build" / "udos_tools"

    def require_toolchain(self) -> None:
        for tool in ("ca65", "ld65"):
            if shutil.which(tool) is None:
                self.skipTest(f"{tool} not found")

    def test_body_overlay_call_resolver_uses_named_seam(self) -> None:
        actc_text = (self.root / "src" / "tools_udos" / "actc" / "actc.asm").read_text(encoding="ascii")
        self.assertIn(
            "lda #<resolve_body_overlay_call_target_from_declared_or_fail\n"
            "    sta actc_overlay_context+ACTC_OVERLAY_CTX_RESOLVE_CALL_TARGET_FN_LO\n"
            "    lda #>resolve_body_overlay_call_target_from_declared_or_fail\n"
            "    sta actc_overlay_context+ACTC_OVERLAY_CTX_RESOLVE_CALL_TARGET_FN_HI",
            actc_text,
        )
        self.assertIn(
            "resolve_body_overlay_call_target_from_declared_or_fail:\n"
            "    jmp resolve_call_target_from_declared_or_fail",
            actc_text,
        )
        self.assertIn(
            "actc_overlay_context+ACTC_OVERLAY_CTX_BUILTIN_RUNTIME_TABLE_PTR_LO",
            actc_text,
        )
        body_overlay_text = (
            self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_collect.asm"
        ).read_text(encoding="ascii")
        body_preallocate_overlay_text = (
            self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_preallocate.asm"
        ).read_text(encoding="ascii")
        overlay_abi_text = (
            self.root / "src" / "tools_udos" / "actc" / "actc_overlay_abi.inc"
        ).read_text(encoding="ascii")
        self.assertIn(".if ACTC_KEEP_BODY_RESIDENT_FALLBACK\nbuiltin_runtime_import_table:", actc_text)
        self.assertNotIn("set_resident_builtin_runtime_table_context:", actc_text)
        self.assertIn("find_or_store_builtin_runtime_external_from_table_ay:", actc_text)
        self.assertIn("find_or_store_prefixed_rt_external_from_ay:", actc_text)
        self.assertIn("builtin_runtime_import_table:", body_overlay_text)
        self.assertIn("builtin_runtime_import_table:", body_preallocate_overlay_text)
        self.assertIn("publish_builtin_runtime_table:", body_overlay_text)
        self.assertIn("publish_builtin_runtime_table:", body_preallocate_overlay_text)
        self.assertIn("ACTC_OVERLAY_CTX_BUILTIN_RUNTIME_TABLE_PTR_LO", body_overlay_text)
        self.assertIn("ACTC_OVERLAY_CTX_BUILTIN_RUNTIME_TABLE_PTR_LO", body_preallocate_overlay_text)
        self.assertIn(
            ".byte (($02 << 6) | (>builtin_symbol_sid_freq & $3F)), <builtin_symbol_sid_freq",
            body_overlay_text,
        )
        self.assertIn(
            ".byte (($02 << 6) | (>builtin_symbol_sid_freq & $3F)), <builtin_symbol_sid_freq",
            body_preallocate_overlay_text,
        )
        self.assertIn('.asciiz "SID_FREQ"', body_overlay_text)
        self.assertIn('.asciiz "SID_FREQ"', body_preallocate_overlay_text)
        self.assertNotIn('.asciiz "RT_SID_FREQ"', body_overlay_text)
        self.assertNotIn('.asciiz "RT_SID_FREQ"', body_preallocate_overlay_text)
        self.assertIn("ACTC_OVERLAY_PASS_BODY_PREALLOCATE", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_BODY_PREALLOCATE", actc_text)
        self.assertIn("!ACTC_OVL7.BIN", actc_text)
        self.assertIn("ACTC_OVERLAY_CTX_BODY_TABLE_ONLY = 228", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_CTX_BODY_MODE = ACTC_OVERLAY_CTX_BODY_TABLE_ONLY", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_CTX_SYMBOL_BUFFER_MATCHES_CONST_PTR_FN_LO", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_CTX_BODY_MODE", body_overlay_text)
        self.assertNotIn("ACTC_OVERLAY_BODY_MODE_PREALLOCATE_EXTERNALS", body_overlay_text)
        self.assertIn("preallocate_body_externals_overlay:", body_preallocate_overlay_text)
        self.assertIn("preallocate_plain_call_args_overlay:", body_preallocate_overlay_text)
        self.assertIn("preallocate_line_ops_seen_local:", body_preallocate_overlay_text)
        self.assertIn(
            "preallocate_line_call_args_overlay_done:\n"
            "    lda preallocate_line_ops_seen_local\n"
            "    beq preallocate_line_call_args_overlay_fail",
            body_preallocate_overlay_text,
        )
        self.assertIn(
            "preallocate_real_explicit_bridge_assignment_external_from_scan_y_overlay:",
            body_preallocate_overlay_text,
        )
        self.assertIn("preallocate_real_plain_decimal_assignment_external_from_scan_y_overlay:", body_preallocate_overlay_text)
        self.assertIn(
            "preallocate_real_explicit_decimal_assignment_external_from_scan_y_overlay:",
            body_preallocate_overlay_text,
        )
        self.assertIn("preallocate_real_print_statement_external_from_declared_overlay:", body_preallocate_overlay_text)
        self.assertIn("preallocate_real_print_value_external_from_scan_y_overlay:", body_preallocate_overlay_text)
        self.assertIn("preallocate_real_bridge_conversion_external_from_scan_y_overlay:", body_preallocate_overlay_text)
        self.assertIn("preallocate_real_numeric_conversion_external_from_scan_y_overlay:", body_preallocate_overlay_text)
        self.assertIn("preallocate_real_unary_print_external_from_scan_y_overlay:", body_preallocate_overlay_text)
        self.assertIn("preallocate_real_binary_print_external_from_scan_y_overlay:", body_preallocate_overlay_text)
        self.assertIn("preallocate_real_condition_cmp_external_from_declared_overlay:", body_preallocate_overlay_text)
        self.assertIn("preallocate_require_then_or_line_end_from_scan_y_overlay:", body_preallocate_overlay_text)
        self.assertIn("preallocate_consume_signed_word_prefix_from_scan_y_overlay:", body_preallocate_overlay_text)
        self.assertIn("preallocate_word_int_assignment_external_from_declared_overlay:", body_preallocate_overlay_text)
        self.assertIn("preallocate_int_conversion_external_from_scan_y_overlay:", body_preallocate_overlay_text)
        self.assertIn("ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_F_CMP_FN_LO", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_CTX_SIZE = 233", overlay_abi_text)
        self.assertIn("load_body_overlay_builtin_runtime_table:", actc_text)
        self.assertIn(
            "sta actc_overlay_context+ACTC_OVERLAY_CTX_BODY_MODE",
            actc_text,
        )
        self.assertIn("ACTC_OVERLAY_CTX_SYMBOL_BUFFER_MATCHES_CONST_PTR_FN_LO", actc_text)
        self.assertIn(".if ACTC_KEEP_BODY_RESIDENT_FALLBACK + ACTC_PREALLOCATE_BODY_EXTERNALS", actc_text)
        self.assertIn("ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_F_CMP_FN_LO", actc_text)
        self.assertIn("preallocate_body_externals_with_overlay:", actc_text)
        self.assertIn("ACTC_OVERLAY_BODY_MODE_PREALLOCATE_EXTERNALS", actc_text)
        self.assertIn(
            "    jmp resolve_unresolved_external_call_target_from_declared_or_fail\n"
            "resolve_call_target_from_declared_or_fail_local:",
            actc_text,
        )
        self.assertIn(
            "resolve_unresolved_external_call_target_from_declared_or_fail:\n"
            "    jsr find_or_store_external_from_declared",
            actc_text,
        )
        self.assertIn(".ifndef ACTC_PREALLOCATE_BODY_EXTERNALS", actc_text)
        self.assertIn("ACTC_PREALLOCATE_BODY_EXTERNALS = 0", actc_text)
        self.assertIn(".ifndef ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY", actc_text)
        self.assertIn("ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY = 0", actc_text)
        self.assertIn(".if ACTC_PREALLOCATE_BODY_EXTERNALS", actc_text)
        self.assertIn("    jsr preallocate_body_externals", actc_text)
        self.assertIn("preallocate_body_externals:\n    lda #$00\n    sta extern_count_data", actc_text)
        self.assertIn("preallocate_real_plain_decimal_assignment_external_from_declared:", actc_text)
        self.assertIn("preallocate_real_assignment_externals_from_declared:", actc_text)
        self.assertIn("preallocate_real_explicit_assignment_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_real_plain_positive_assignment_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_real_plain_signed_assignment_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_real_explicit_positive_assignment_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_real_explicit_signed_assignment_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_consume_signed_word_prefix_from_scan_y:", actc_text)
        self.assertIn("preallocate_real_unary_operator_assignment_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_real_copy_or_bridge_assignment_external_from_scan_y:", actc_text)

        self.assertIn("preallocate_real_binary_operator_assignment_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_word_assignment_externals_from_declared:", actc_text)
        self.assertIn("preallocate_int_of_real_assignment_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_plain_call_externals_from_declared:", actc_text)
        self.assertIn("preallocate_plain_call_arg_externals_from_scan_y:", actc_text)
        self.assertIn("preallocate_scan_plain_call_arg_for_externals_from_scan_y:", actc_text)
        self.assertIn("preallocate_skip_string_in_plain_call_arg_from_scan_y:", actc_text)
        self.assertIn("preallocate_call_name_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_call_arg_scan_depth_data:", actc_text)
        self.assertIn(
            "preallocate_plain_call_arg_externals_loop:\n"
            "    jsr skip_inline_spaces_at_scan_y\n"
            "    jsr preallocate_scan_plain_call_arg_for_externals_from_scan_y",
            actc_text,
        )
        self.assertIn("preallocate_call_expression_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_scan_line_call_externals_from_scan_y:", actc_text)
        self.assertIn("preallocate_declared_symbol_is_bool_keyword:", actc_text)
        self.assertIn("preallocate_declared_symbol_is_reserved_call_keyword:", actc_text)
        self.assertIn("preallocate_call_with_arg_externals_from_scan_y:", actc_text)
        self.assertIn("preallocate_int_conversion_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_real_bridge_conversion_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_real_numeric_conversion_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_real_unary_print_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_real_binary_print_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_bool_primary_start_y_data:", actc_text)
        self.assertIn("preallocate_print_start_y_data:", actc_text)
        self.assertIn(
            "preallocate_call_expression_external_from_scan_y:\n"
            "    jsr save_condition_reader_mark\n"
            "    jsr preallocate_call_with_arg_externals_from_scan_y",
            actc_text,
        )
        self.assertIn(
            "preallocate_call_expression_external_try_bool_restore:\n"
            "    jsr restore_condition_reader_mark\n"
            "    jsr save_condition_reader_mark\n"
            "    jsr preallocate_scan_line_call_externals_from_scan_y",
            actc_text,
        )
        self.assertIn(
            "preallocate_int_print_statement_call_external_try_arg_scan:\n"
            "    jsr restore_condition_reader_mark\n"
            "    ldy preallocate_print_start_y_data\n"
            "    jsr save_condition_reader_mark",
            actc_text,
        )
        self.assertIn(
            "preallocate_int_print_statement_call_external_try_arg_scan:\n"
            "    jsr restore_condition_reader_mark\n"
            "    ldy preallocate_print_start_y_data\n"
            "    jsr save_condition_reader_mark\n"
            "    jsr skip_inline_spaces_at_scan_y\n"
            "    jsr source_reader_peek_scan_y\n"
            "    cmp #'('\n"
            "    bne preallocate_int_print_statement_call_external_miss_restore\n"
            "    lda #'('\n"
            "    jsr source_reader_consume_char_from_scan_y\n"
            "    bcs preallocate_int_print_statement_call_external_miss_restore\n"
            "    jsr skip_inline_spaces_at_scan_y\n"
            "    jsr preallocate_scan_plain_call_arg_for_externals_from_scan_y",
            actc_text,
        )
        self.assertIn(
            "preallocate_call_name_external_from_scan_y:\n"
            "    sty symbol_start_y_data\n"
            "    jsr save_source_reader_mark\n"
            "    jsr copy_symbol_from_scan_y\n"
            "    bcs preallocate_call_name_external_miss_restore\n"
            "    sty symbol_end_y_data\n"
            "    jsr preallocate_declared_symbol_is_reserved_call_keyword\n"
            "    bcc preallocate_call_name_external_miss_restore\n"
            "    ldy symbol_end_y_data",
            actc_text,
        )
        self.assertIn(
            "preallocate_call_with_arg_externals_from_scan_y:\n"
            "    jsr copy_symbol_from_scan_y\n"
            "    bcs preallocate_call_with_arg_externals_fail\n"
            "    sty symbol_end_y_data\n"
            "    jsr preallocate_declared_symbol_is_reserved_call_keyword\n"
            "    bcc preallocate_call_with_arg_externals_fail\n"
            "    ldy symbol_end_y_data\n"
            "    jsr skip_inline_spaces_at_scan_y\n"
            "    jsr source_reader_peek_scan_y\n"
            "    cmp #'('\n"
            "    bne preallocate_call_with_arg_externals_fail\n"
            "    jsr resolve_call_target_from_declared_or_fail",
            actc_text,
        )
        self.assertIn("preallocate_call_term_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_call_condition_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_call_comparison_condition_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_call_comparison_clause_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_call_bool_condition_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_call_bool_or_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_call_bool_and_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_call_bool_not_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_call_bool_primary_external_from_scan_y:", actc_text)
        self.assertIn(
            "preallocate_call_condition_external_from_scan_y:\n"
            "    jsr save_condition_reader_mark\n"
            "    jsr preallocate_call_with_arg_externals_from_scan_y",
            actc_text,
        )
        self.assertIn(
            "    jsr preallocate_call_comparison_condition_external_from_scan_y\n"
            "    bcc preallocate_declared_symbol_is_real_condition_statement_done\n"
            "    ldy preallocate_condition_start_y_data\n"
            "    jsr preallocate_call_bool_condition_external_from_scan_y",
            actc_text,
        )
        self.assertIn(
            "preallocate_call_comparison_condition_external_from_scan_y:\n"
            "    jsr save_condition_reader_mark\n"
            "    jsr preallocate_call_comparison_clause_external_from_scan_y",
            actc_text,
        )
        self.assertIn(
            "preallocate_call_bool_condition_external_from_scan_y:\n"
            "    jsr save_condition_reader_mark\n"
            "    jsr preallocate_call_bool_or_external_from_scan_y",
            actc_text,
        )
        self.assertIn(
            "    sty preallocate_bool_primary_start_y_data\n"
            "    jsr save_group_reader_mark\n"
            "    jsr preallocate_call_comparison_clause_external_from_scan_y\n"
            "    bcc preallocate_call_bool_primary_external_done\n"
            "    jsr restore_group_reader_mark\n"
            "    ldy preallocate_bool_primary_start_y_data",
            actc_text,
        )
        self.assertIn("preallocate_consume_comparison_operator_at_scan_y:", actc_text)
        self.assertIn("preallocate_consume_flat_call_args_from_scan_y:", actc_text)
        self.assertIn("preallocate_declared_symbol_is_return_statement:", actc_text)
        self.assertIn(
            "preallocate_scan_line_call_externals_loop:\n"
            "    jsr source_reader_peek_scan_y",
            actc_text,
        )
        self.assertIn(
            "    jsr preallocate_int_conversion_external_from_scan_y\n"
            "    bcs preallocate_scan_line_call_externals_try_call\n"
            "    lda #$01\n"
            "    sta bool_ops_used_data",
            actc_text,
        )
        self.assertIn(
            "preallocate_int_print_statement_call_external_from_scan_y:\n"
            "    ldy symbol_end_y_data\n"
            "    sty preallocate_print_start_y_data\n"
            "    jsr save_condition_reader_mark",
            actc_text,
        )
        self.assertIn("preallocate_declared_symbol_is_real_if_condition:", actc_text)
        self.assertIn("preallocate_real_condition_cmp_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_require_condition_terminator_at_scan_y:", actc_text)
        self.assertIn("preallocate_require_do_or_line_end_at_scan_y:", actc_text)
        self.assertIn("    jsr parse_positive_word_sum_at_scan_y", actc_text)
        self.assertIn("    jsr find_or_store_rt_i_to_f_external", actc_text)
        self.assertIn("    jsr find_or_store_rt_s_to_f_external", actc_text)
        self.assertIn("    jsr find_or_store_rt_f_to_i_external", actc_text)
        self.assertIn("    jsr find_or_store_real_bridge_external_from_x", actc_text)
        self.assertIn("    jsr find_or_store_real_operator_external_from_a", actc_text)
        self.assertIn("    jsr find_or_store_rt_f_cmp_external", actc_text)
        self.assertIn("preallocate_declared_symbol_is_print_statement:", actc_text)
        self.assertIn("preallocate_real_print_statement_external_from_scan_y:", actc_text)
        self.assertIn("preallocate_int_print_statement_call_external_from_scan_y:", actc_text)
        self.assertIn(
            "preallocate_real_print_statement_external_from_scan_y:\n"
            "    ldy symbol_end_y_data",
            actc_text,
        )
        self.assertIn(
            "    jsr preallocate_real_bridge_conversion_external_from_scan_y\n"
            "    bcc preallocate_real_print_statement_external_after_value\n"
            "    jsr preallocate_real_numeric_conversion_external_from_scan_y\n"
            "    bcc preallocate_real_print_statement_external_after_value\n"
            "    jsr preallocate_real_unary_print_external_from_scan_y\n"
            "    bcc preallocate_real_print_statement_external_after_value\n"
            "    jsr preallocate_real_binary_print_external_from_scan_y\n"
            "    bcc preallocate_real_print_statement_external_after_value",
            actc_text,
        )

        body_overlay_text = (self.root / "src" / "tools_udos" / "actc" / "actc_overlay_body_collect.asm").read_text(
            encoding="ascii"
        )
        self.assertIn(
            "emit_runtime_real_value_local_or_fail:\n"
            "    jsr try_consume_real_open_local\n"
            "    bcs emit_runtime_real_value_local_try_fabs\n"
            "    jmp emit_runtime_real_explicit_value_after_open_local_or_fail",
            body_overlay_text,
        )
        self.assertIn("emit_runtime_real_unary_value_local_or_fail:", body_overlay_text)
        self.assertIn("emit_runtime_real_binary_value_local_or_fail:", body_overlay_text)
        self.assertIn(
            "    jsr emit_runtime_real_explicit_bridge_value_local_or_fail\n"
            "    bcs :+\n"
            "    clc\n"
            "    rts\n"
            ":",
            body_overlay_text,
        )

    def test_production_actc_build_defaults_to_overlay_preallocation(self) -> None:
        build_script = (self.root / "tools" / "build_actc_udos.sh").read_text(encoding="ascii")
        self.assertIn('ACTC_PREALLOCATE_BODY_EXTERNALS="${ACTC_PREALLOCATE_BODY_EXTERNALS:-1}"', build_script)
        self.assertIn(
            'ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY="${ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY:-1}"',
            build_script,
        )

    def run_checked(self, args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            args,
            cwd=self.root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return result

    def build_actc_emit_overlay_stack(self, extra_build_env: dict[str, str] | None = None) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        build_env["ACTC_PREALLOCATE_BODY_EXTERNALS"] = "1"
        if extra_build_env is not None:
            build_env.update(extra_build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_preallocate.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

    def assert_body_overlay_map_keeps_headroom(self, map_name: str, overlay_name: str) -> None:
        map_text = (self.build_dir / map_name).read_text(encoding="ascii")
        match = re.search(r"^CODE\s+([0-9A-Fa-f]{6})\s+([0-9A-Fa-f]{6})\s+([0-9A-Fa-f]{6})\s+", map_text, re.MULTILINE)
        self.assertIsNotNone(match, msg=map_text)
        assert match is not None
        size = int(match.group(3), 16)
        headroom = self.ACTC_OVERLAY_WINDOW_SIZE - size
        self.assertGreaterEqual(
            headroom,
            self.ACTC_BODY_OVERLAY_MIN_HEADROOM,
            msg=(
                f"{overlay_name} has only {headroom} bytes free in the ACTC body overlay window; "
                f"keep at least {self.ACTC_BODY_OVERLAY_MIN_HEADROOM} bytes for link-selected library growth\n"
                f"{map_text}"
            ),
        )

    def test_body_overlays_keep_library_growth_headroom(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_preallocate.sh")])
        self.assert_body_overlay_map_keeps_headroom("actc_overlay_body_collect.map", "ACTC_OVL6.BIN")
        self.assert_body_overlay_map_keeps_headroom("actc_overlay_body_preallocate.map", "ACTC_OVL7.BIN")

    def compile_overlay_object(
        self,
        source: str,
        workspace_name: str,
        extra_build_env: dict[str, str] | None = None,
    ) -> str:
        self.build_actc_emit_overlay_stack(extra_build_env)
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / workspace_name
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
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
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            if extra_build_env is not None and extra_build_env.get("ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY") == "1":
                self.assertTrue(
                    any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL7.BIN" and op["status"] == 1 for op in summary["ops"]),
                    msg=result.stdout,
                )
            return (object_dir / "MAIN.OBJ").read_text(encoding="ascii")

    def test_actc_preallocation_body_overlay_mode_records_plain_external_call(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "ExtCall()\r"
            "RETURN\r",
            "actc-overlay-preallocation-body-mode-plain-external-call",
            {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertIn("x main 0 19\n", obj)
        self.assertIn("b u0M\n", obj)
        self.assertEqual(obj.count("u extcall\n"), 1, msg=obj)
        self.assertIn("r 1 u0\n", obj)
        self.assertNotIn("b u0r\n", obj)

    def test_actc_preallocation_body_overlay_mode_records_nested_plain_call_args(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "OuterCall(1+InnerCall(NestedCall(2)),(OtherCall(4)),3)\r"
            "LaterCall()\r"
            "RETURN\r",
            "actc-overlay-preallocation-body-mode-nested-plain-call-args",
            {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        symbols = ("outercall", "innercall", "nestedcall", "othercall", "latercall")
        for symbol in symbols:
            self.assertIn(f"u {symbol}\n", obj)
        for left, right in zip(symbols, symbols[1:]):
            self.assertLess(obj.index(f"u {left}\n"), obj.index(f"u {right}\n"))

    def test_actc_preallocation_body_overlay_mode_records_assignment_and_return_call_exprs(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "INT X\r"
            "PROC MAIN()\r"
            "X=ExtCall(ArgOne(1))\r"
            "RETURN RetCall(ArgTwo(2))\r"
            "LaterCall()\r",
            "actc-overlay-preallocation-body-mode-assignment-return-call-exprs",
            {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        symbols = ("extcall", "argone", "retcall", "argtwo", "latercall")
        for symbol in symbols:
            self.assertIn(f"u {symbol}\n", obj)
        for left, right in zip(symbols, symbols[1:]):
            self.assertLess(obj.index(f"u {left}\n"), obj.index(f"u {right}\n"))

    def test_actc_preallocation_body_overlay_mode_records_print_call_exprs(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "PrintI(ExtCall(ArgOne(1)))\r"
            "PrintIE(OtherCall(2))\r"
            "RETURN\r",
            "actc-overlay-preallocation-body-mode-print-call-exprs",
            {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        symbols = ("extcall", "argone", "othercall")
        for symbol in symbols:
            self.assertIn(f"u {symbol}\n", obj)
        for left, right in zip(symbols, symbols[1:]):
            self.assertLess(obj.index(f"u {left}\n"), obj.index(f"u {right}\n"))
        self.assertNotIn("u printi\n", obj)
        self.assertNotIn("u printie\n", obj)

    def test_actc_preallocation_body_overlay_mode_maps_real_print_vars(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "PROC MAIN()\r"
            "PrintR(A)\r"
            "ExtCall()\r"
            "PrintRE(B)\r"
            "LaterCall()\r"
            "RETURN\r",
            "actc-overlay-preallocation-body-mode-real-print-vars",
            {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        symbols = ("rt_print_f", "extcall", "latercall")
        for symbol in symbols:
            self.assertIn(f"u {symbol}\n", obj)
        for left, right in zip(symbols, symbols[1:]):
            self.assertLess(obj.index(f"u {left}\n"), obj.index(f"u {right}\n"), msg=obj)
        self.assertNotIn("u printr\n", obj)
        self.assertNotIn("u printre\n", obj)

    def test_actc_preallocation_body_overlay_mode_maps_real_print_exprs(self) -> None:
        cases = (
            (
                "MODULE MAIN\r"
                "CARD C=[255]\r"
                "INT I=[0]\r"
                "PROC MAIN()\r"
                "PrintR(REAL(C))\r"
                "ExtCall()\r"
                "PrintRE(REAL(I))\r"
                "LaterCall()\r"
                "RETURN\r",
                "actc-overlay-preallocation-body-mode-real-print-bridge-exprs",
                ("rt_i_to_f", "rt_print_f", "extcall", "rt_s_to_f", "latercall"),
            ),
            (
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "PrintR(REAL(128*2))\r"
                "ExtCall()\r"
                "PrintRE(REAL(0-(128*2)))\r"
                "LaterCall()\r"
                "RETURN\r",
                "actc-overlay-preallocation-body-mode-real-print-numeric-exprs",
                ("rt_i_to_f", "rt_print_f", "extcall", "rt_s_to_f", "latercall"),
            ),
            (
                "MODULE MAIN\r"
                "REAL A\r"
                "PROC MAIN()\r"
                "PrintR(FABS(A))\r"
                "ExtCall()\r"
                "PrintRE(FSQRT(A))\r"
                "LaterCall()\r"
                "RETURN\r",
                "actc-overlay-preallocation-body-mode-real-print-unary-exprs",
                ("rt_f_abs", "rt_print_f", "extcall", "rt_f_sqrt", "latercall"),
            ),
            (
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "PROC MAIN()\r"
                "PrintR(A+B)\r"
                "ExtCall()\r"
                "PrintRE(A/B)\r"
                "LaterCall()\r"
                "RETURN\r",
                "actc-overlay-preallocation-body-mode-real-print-binary-exprs",
                ("rt_f_add", "rt_print_f", "extcall", "rt_f_div", "latercall"),
            ),
        )

        for source, workspace_name, symbols in cases:
            with self.subTest(workspace_name=workspace_name):
                obj = self.compile_overlay_object(
                    source,
                    workspace_name,
                    {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
                )

                for symbol in symbols:
                    self.assertIn(f"u {symbol}\n", obj)
                for earlier, later in zip(symbols, symbols[1:]):
                    self.assertLess(obj.index(f"u {earlier}\n"), obj.index(f"u {later}\n"), msg=obj)
                for builtin_name in ("real", "fabs", "fsqrt", "printr", "printre"):
                    self.assertNotIn(f"u {builtin_name}\n", obj)

    def test_actc_preallocation_body_overlay_mode_records_condition_call_exprs(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "IF LeftAnd(LAndArg(1)) AND RightAnd(RAndArg(2)) THEN\r"
            "FI\r"
            "WHILE NOT(WhileCall(WhileArg(3)) OR OtherCall(4)) DO\r"
            "OD\r"
            "DO\r"
            "UNTIL UntilCall(UntilArg(5))\r"
            "RETURN\r",
            "actc-overlay-preallocation-body-mode-condition-call-exprs",
            {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        symbols = (
            "leftand",
            "landarg",
            "rightand",
            "randarg",
            "whilecall",
            "whilearg",
            "othercall",
            "untilcall",
            "untilarg",
        )
        for symbol in symbols:
            self.assertIn(f"u {symbol}\n", obj)
        for left, right in zip(symbols, symbols[1:]):
            self.assertLess(obj.index(f"u {left}\n"), obj.index(f"u {right}\n"))
        for keyword in ("if", "while", "until", "and", "or", "not", "then", "do"):
            self.assertNotIn(f"u {keyword}\n", obj)

    def test_actc_preallocation_body_overlay_mode_maps_real_condition_compares(self) -> None:
        cases = (
            (
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "PROC MAIN()\r"
                "IF A<=B THEN\r"
                "FI\r"
                "ExtCall()\r"
                "RETURN\r",
                "actc-overlay-preallocation-body-mode-real-if-compare",
            ),
            (
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "PROC MAIN()\r"
                "WHILE A>B DO\r"
                "OD\r"
                "ExtCall()\r"
                "RETURN\r",
                "actc-overlay-preallocation-body-mode-real-while-compare",
            ),
            (
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "PROC MAIN()\r"
                "DO\r"
                "UNTIL A<>B\r"
                "ExtCall()\r"
                "RETURN\r",
                "actc-overlay-preallocation-body-mode-real-until-compare",
            ),
        )

        for source, workspace_name in cases:
            with self.subTest(workspace_name=workspace_name):
                obj = self.compile_overlay_object(
                    source,
                    workspace_name,
                    {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
                )

                self.assertIn("u rt_f_cmp\n", obj)
                self.assertIn("u extcall\n", obj)
                self.assertLess(obj.index("u rt_f_cmp\n"), obj.index("u extcall\n"), msg=obj)
                for keyword in ("if", "while", "until", "then", "do"):
                    self.assertNotIn(f"u {keyword}\n", obj)

    def test_actc_preallocation_body_overlay_mode_maps_real_condition_exprs(self) -> None:
        cases = (
            (
                "MODULE MAIN\r"
                "CARD C=[255]\r"
                "REAL A\r"
                "PROC MAIN()\r"
                "IF REAL(C)<A THEN\r"
                "FI\r"
                "ExtCall()\r"
                "WHILE A>=REAL(0-(128*2)) DO\r"
                "OD\r"
                "LaterCall()\r"
                "DO\r"
                "UNTIL REAL(C)<=A\r"
                "TailCall()\r"
                "RETURN\r",
                "actc-overlay-preallocation-body-mode-real-condition-bridge-exprs",
                ("rt_i_to_f", "rt_f_cmp", "extcall", "rt_s_to_f", "latercall", "tailcall"),
            ),
            (
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "PROC MAIN()\r"
                "IF FABS(A)<B THEN\r"
                "FI\r"
                "ExtCall()\r"
                "WHILE A+B>=FSQRT(B) DO\r"
                "OD\r"
                "LaterCall()\r"
                "DO\r"
                "UNTIL A/B<>B\r"
                "TailCall()\r"
                "RETURN\r",
                "actc-overlay-preallocation-body-mode-real-condition-unary-binary-exprs",
                ("rt_f_abs", "rt_f_cmp", "extcall", "rt_f_add", "rt_f_sqrt", "latercall", "rt_f_div", "tailcall"),
            ),
        )

        for source, workspace_name, symbols in cases:
            with self.subTest(workspace_name=workspace_name):
                obj = self.compile_overlay_object(
                    source,
                    workspace_name,
                    {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
                )

                for symbol in symbols:
                    self.assertIn(f"u {symbol}\n", obj)
                for earlier, later in zip(symbols, symbols[1:]):
                    self.assertLess(obj.index(f"u {earlier}\n"), obj.index(f"u {later}\n"), msg=obj)
                for builtin_name in ("real", "fabs", "fsqrt", "if", "then"):
                    self.assertNotIn(f"u {builtin_name}\n", obj)

    def test_actc_body_overlay_mode_lowers_rich_real_condition_exprs(self) -> None:
        cases = (
            (
                "MODULE MAIN\r"
                "CARD C=[255]\r"
                "INT I=[0]\r"
                "REAL A\r"
                "PROC MAIN()\r"
                "IF REAL(C)<A THEN\r"
                "FI\r"
                "WHILE A>=REAL(0-(128*2)) DO\r"
                "OD\r"
                "DO\r"
                "UNTIL REAL(C)<=A\r"
                "ExtCall()\r"
                "RETURN\r",
                "actc-overlay-body-mode-real-condition-bridge-exprs",
                ("rt_i_to_f", "rt_f_cmp", "rt_s_to_f"),
                ("extcall",),
            ),
            (
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "PROC MAIN()\r"
                "IF FABS(A)<B THEN\r"
                "FI\r"
                "WHILE A+B>=FSQRT(B) DO\r"
                "OD\r"
                "DO\r"
                "UNTIL A/B<>B\r"
                "ExtCall()\r"
                "RETURN\r",
                "actc-overlay-body-mode-real-condition-unary-binary-exprs",
                ("rt_f_abs", "rt_f_cmp", "rt_f_add", "rt_f_sqrt", "rt_f_div"),
                ("extcall",),
            ),
        )

        for source, workspace_name, ordered_runtime_symbols, unordered_symbols in cases:
            with self.subTest(workspace_name=workspace_name):
                obj = self.compile_overlay_object(source, workspace_name)

                for symbol in (*ordered_runtime_symbols, *unordered_symbols):
                    self.assertIn(f"u {symbol}\n", obj)
                for earlier, later in zip(ordered_runtime_symbols, ordered_runtime_symbols[1:]):
                    self.assertLess(obj.index(f"u {earlier}\n"), obj.index(f"u {later}\n"), msg=obj)
                for builtin_name in ("real", "fabs", "fsqrt", "if", "then"):
                    self.assertNotIn(f"u {builtin_name}\n", obj)

    def test_actc_preallocation_body_overlay_mode_maps_helper_families_to_runtime_objs(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "BYTE J\r"
            "BYTE M\r"
            "BYTE H\r"
            "PROC MAIN()\r"
            "SidVol(10)\r"
            "ScreenCell(5,2,65)\r"
            "SpriteOn(2)\r"
            "J=Joy(2)\r"
            "M=MousePoll(1)\r"
            "H=DbfOpen(12288)\r"
            "DbfClose(H)\r"
            "RETURN\r",
            "actc-overlay-preallocation-body-mode-helper-families",
            {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        runtime_imports = (
            "rt_sid_vol",
            "rt_gfx_screen_cell",
            "rt_sprite_on",
            "rt_joy",
            "rt_mp",
            "rt_dbf_open",
            "rt_dbf_close",
        )
        for runtime_import in runtime_imports:
            self.assertIn(f"u {runtime_import}\n", obj)
        for earlier, later in zip(runtime_imports, runtime_imports[1:]):
            self.assertLess(obj.index(f"u {earlier}\n"), obj.index(f"u {later}\n"), msg=obj)
        for builtin_name in ("sidvol", "screencell", "spriteon", "joy", "mousepoll", "dbfopen", "dbfclose"):
            self.assertNotIn(f"u {builtin_name}\n", obj)

    def test_actc_preallocation_body_overlay_mode_maps_all_input_helpers_to_runtime_objs(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "BYTE J\r"
            "BYTE P\r"
            "BYTE JB1\r"
            "BYTE JB2\r"
            "BYTE M\r"
            "BYTE MS\r"
            "BYTE MX\r"
            "BYTE MY\r"
            "BYTE MB\r"
            "BYTE MB1\r"
            "BYTE MB2\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "P=JoySeen(2)\r"
            "JB1=JoyBtn1(2)\r"
            "JB2=JoyBtn2(2)\r"
            "M=MousePoll(1)\r"
            "MS=MouseSeen()\r"
            "MX=MouseX()\r"
            "MY=MouseY()\r"
            "MB=MouseBtn()\r"
            "MB1=MouseBtn1()\r"
            "MB2=MouseBtn2()\r"
            "RETURN\r",
            "actc-overlay-preallocation-body-mode-input-helpers",
            {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        runtime_imports = (
            "rt_joy",
            "rt_jp",
            "rt_jb1",
            "rt_jb2",
            "rt_mp",
            "rt_mseen",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_mb1",
            "rt_mb2",
        )
        for runtime_import in runtime_imports:
            self.assertIn(f"u {runtime_import}\n", obj)
        for earlier, later in zip(runtime_imports, runtime_imports[1:]):
            self.assertLess(obj.index(f"u {earlier}\n"), obj.index(f"u {later}\n"), msg=obj)
        for builtin_name in (
            "joy",
            "joyseen",
            "joybtn1",
            "joybtn2",
            "mousepoll",
            "mouseseen",
            "mousex",
            "mousey",
            "mousebtn",
            "mousebtn1",
            "mousebtn2",
        ):
            self.assertNotIn(f"u {builtin_name}\n", obj)

    def test_actc_preallocation_body_overlay_mode_maps_input_conditions_to_runtime_objs(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "IF JoyBtn1(2) THEN\r"
            "FI\r"
            "WHILE MouseSeen() DO\r"
            "OD\r"
            "DO\r"
            "UNTIL MouseBtn2()\r"
            "RETURN\r",
            "actc-overlay-preallocation-body-mode-input-conditions",
            {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        runtime_imports = ("rt_jb1", "rt_mseen", "rt_mb2")
        for runtime_import in runtime_imports:
            self.assertIn(f"u {runtime_import}\n", obj)
        for earlier, later in zip(runtime_imports, runtime_imports[1:]):
            self.assertLess(obj.index(f"u {earlier}\n"), obj.index(f"u {later}\n"), msg=obj)
        for unused_runtime_import in (
            "rt_joy",
            "rt_jp",
            "rt_jb2",
            "rt_mp",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_mb1",
        ):
            self.assertNotIn(f"u {unused_runtime_import}\n", obj)
        for builtin_name in ("joybtn1", "mouseseen", "mousebtn2", "if", "while", "until", "then", "do"):
            self.assertNotIn(f"u {builtin_name}\n", obj)

    def test_actc_preallocation_body_overlay_mode_maps_real_unary_assignments(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL R\r"
            "REAL Q\r"
            "PROC MAIN()\r"
            "R=FABS(A)\r"
            "Q=FSQRT(A)\r"
            "RETURN\r",
            "actc-overlay-preallocation-body-mode-real-unary-assignments",
            {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        runtime_imports = ("rt_f_abs", "rt_f_sqrt")
        for runtime_import in runtime_imports:
            self.assertIn(f"u {runtime_import}\n", obj)
        self.assertLess(obj.index("u rt_f_abs\n"), obj.index("u rt_f_sqrt\n"), msg=obj)
        self.assertNotIn("u fabs\n", obj)
        self.assertNotIn("u fsqrt\n", obj)

    def test_actc_preallocation_body_overlay_mode_maps_real_binary_assignments(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL R\r"
            "REAL Q\r"
            "PROC MAIN()\r"
            "R=A+B\r"
            "Q=A/B\r"
            "RETURN\r",
            "actc-overlay-preallocation-body-mode-real-binary-assignments",
            {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        runtime_imports = ("rt_f_add", "rt_f_div")
        for runtime_import in runtime_imports:
            self.assertIn(f"u {runtime_import}\n", obj)
        self.assertLess(obj.index("u rt_f_add\n"), obj.index("u rt_f_div\n"), msg=obj)

    def test_actc_preallocation_body_overlay_mode_maps_real_bridge_assignments(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD C=[255]\r"
            "INT I=[0]\r"
            "REAL X\r"
            "REAL Y\r"
            "PROC MAIN()\r"
            "X=C\r"
            "Y=I\r"
            "RETURN\r",
            "actc-overlay-preallocation-body-mode-real-bridge-assignments",
            {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        runtime_imports = ("rt_i_to_f", "rt_s_to_f")
        for runtime_import in runtime_imports:
            self.assertIn(f"u {runtime_import}\n", obj)
        self.assertLess(obj.index("u rt_i_to_f\n"), obj.index("u rt_s_to_f\n"), msg=obj)

    def test_actc_preallocation_body_overlay_mode_maps_explicit_real_and_int_conversions(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD C=[255]\r"
            "CARD W=[0]\r"
            "INT I=[0]\r"
            "INT J=[0]\r"
            "REAL R\r"
            "REAL X\r"
            "REAL Y\r"
            "PROC MAIN()\r"
            "X=REAL(C)\r"
            "Y=REAL(I)\r"
            "W=INT(R)\r"
            "J=INT(R)\r"
            "RETURN\r",
            "actc-overlay-preallocation-body-mode-explicit-real-int-conversions",
            {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        runtime_imports = ("rt_i_to_f", "rt_s_to_f", "rt_f_to_i")
        for runtime_import in runtime_imports:
            self.assertIn(f"u {runtime_import}\n", obj)
        for earlier, later in zip(runtime_imports, runtime_imports[1:]):
            self.assertLess(obj.index(f"u {earlier}\n"), obj.index(f"u {later}\n"), msg=obj)
        self.assertNotIn("u real\n", obj)
        self.assertNotIn("u int\n", obj)

    def test_actc_preallocation_body_overlay_mode_maps_real_numeric_conversions(self) -> None:
        cases = (
            (
                "MODULE MAIN\r"
                "REAL X\r"
                "REAL Y\r"
                "PROC MAIN()\r"
                "X=REAL(255+1)\r"
                "ExtCall()\r"
                "Y=0-(128*2)\r"
                "LaterCall()\r"
                "RETURN\r",
                "actc-overlay-preallocation-body-mode-real-numeric-explicit-positive-plain-signed",
            ),
            (
                "MODULE MAIN\r"
                "REAL X\r"
                "REAL Y\r"
                "PROC MAIN()\r"
                "X=128*2\r"
                "ExtCall()\r"
                "Y=REAL(0-(512/2))\r"
                "LaterCall()\r"
                "RETURN\r",
                "actc-overlay-preallocation-body-mode-real-numeric-plain-positive-explicit-signed",
            ),
        )

        for source, workspace_name in cases:
            with self.subTest(workspace_name=workspace_name):
                obj = self.compile_overlay_object(
                    source,
                    workspace_name,
                    {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
                )

                runtime_imports = ("rt_i_to_f", "extcall", "rt_s_to_f", "latercall")
                for runtime_import in runtime_imports:
                    self.assertIn(f"u {runtime_import}\n", obj)
                for earlier, later in zip(runtime_imports, runtime_imports[1:]):
                    self.assertLess(obj.index(f"u {earlier}\n"), obj.index(f"u {later}\n"), msg=obj)
                self.assertNotIn("u real\n", obj)

    def test_actc_compile_path_emits_machine_obj_for_single_local_call(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC A()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "A()\r"
            "RETURN\r",
            "actc-overlay-machine-single-local-call",
        )

        self.assertIn("x main 0 20\n", obj)
        self.assertIn("x a 19 1\n", obj)
        self.assertEqual(obj.count("b M\n"), 2)
        self.assertIn("m 20 13 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n", obj)
        self.assertNotIn("b c0r\n", obj)

    def test_actc_compile_path_emits_machine_obj_for_local_fanout_calls(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC A()\r"
            "RETURN\r"
            "PROC B()\r"
            "A()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "A()\r"
            "B()\r"
            "RETURN\r",
            "actc-overlay-machine-local-fanout-calls",
        )

        self.assertIn("x main 0 27\n", obj)
        self.assertIn("x b 22 4\n", obj)
        self.assertIn("x a 26 1\n", obj)
        self.assertEqual(obj.count("b M\n"), 3)
        self.assertIn(
            "m 20 1A 10 20 16 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 1A 10 60 60\n",
            obj,
        )
        self.assertNotIn("b c0c1r\n", obj)

    def test_actc_compile_path_emits_machine_obj_for_multi_local_external_calls(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC A()\r"
            "RETURN\r"
            "PROC B()\r"
            "A()\r"
            "Helper()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "B()\r"
            "A()\r"
            "Other()\r"
            "RETURN\r",
            "actc-overlay-machine-multi-local-external-calls",
        )

        self.assertIn("x main 0 33\n", obj)
        self.assertIn("x b 25 7\n", obj)
        self.assertIn("x a 32 1\n", obj)
        self.assertIn("b u1u0M\n", obj)
        self.assertIn("b u0M\n", obj)
        self.assertIn("b M\n", obj)
        self.assertIn("u helper\n", obj)
        self.assertIn("u other\n", obj)
        self.assertIn(
            "m 20 19 10 20 20 10 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 20 10 20 00 00 60 60\n",
            obj,
        )
        self.assertIn("r 7 u1\n", obj)
        self.assertIn("r 29 u0\n", obj)
        self.assertNotIn("b c", obj)

    def test_actc_compile_path_emits_machine_obj_for_helper_only_external_call(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC A()\r"
            "Helper()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "A()\r"
            "RETURN\r",
            "actc-overlay-machine-helper-only-external-call",
        )

        self.assertIn("x main 0 23\n", obj)
        self.assertIn("x a 19 4\n", obj)
        self.assertEqual(obj.count("b u0M\n"), 2, msg=obj)
        self.assertIn("u helper\n", obj)
        self.assertIn(
            "m 20 13 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 00 00 60\n",
            obj,
        )
        self.assertIn("r 20 u0\n", obj)
        self.assertNotIn("b c", obj)

    def test_actc_compile_path_emits_machine_obj_for_deep_helper_only_external_call(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC A()\r"
            "Helper()\r"
            "RETURN\r"
            "PROC B()\r"
            "A()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "B()\r"
            "RETURN\r",
            "actc-overlay-machine-deep-helper-only-external-call",
        )

        self.assertIn("x main 0 27\n", obj)
        self.assertIn("x b 19 4\n", obj)
        self.assertIn("x a 23 4\n", obj)
        self.assertEqual(obj.count("b u0M\n"), 3, msg=obj)
        self.assertIn("u helper\n", obj)
        self.assertIn(
            "m 20 13 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 17 10 60 20 00 00 60\n",
            obj,
        )
        self.assertIn("r 24 u0\n", obj)
        self.assertNotIn("b c", obj)

    def test_actc_compile_path_emits_machine_obj_for_helper_only_mixed_repeated_external_calls(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC A()\r"
            "Helper()\r"
            "Other()\r"
            "Helper()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "A()\r"
            "RETURN\r",
            "actc-overlay-machine-helper-only-mixed-repeated-external-calls",
        )

        self.assertIn("x main 0 29\n", obj)
        self.assertIn("x a 19 10\n", obj)
        self.assertEqual(obj.count("b u0u1u0M\n"), 2, msg=obj)
        self.assertIn("u helper\n", obj)
        self.assertIn("u other\n", obj)
        self.assertIn(
            "m 20 13 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 00 00 20 00 00 20 00 00 60\n",
            obj,
        )
        self.assertIn("r 20 u0\n", obj)
        self.assertIn("r 23 u1\n", obj)
        self.assertIn("r 26 u0\n", obj)
        self.assertNotIn("b c", obj)

    def test_actc_compile_path_emits_machine_obj_for_single_external_call(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        build_env["ACTC_PREALLOCATE_BODY_EXTERNALS"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-machine-external-call"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "ExtCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("x main 0 19\n", obj)
            self.assertIn("b u0M\n", obj)
            self.assertIn("u extcall\n", obj)
            self.assertIn("m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n", obj)
            self.assertIn("r 1 u0\n", obj)
            self.assertNotIn("b u0r\n", obj)

    def test_actc_compile_path_emits_machine_obj_for_local_then_external_call(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        build_env["ACTC_PREALLOCATE_BODY_EXTERNALS"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-machine-local-external-call"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC A()\r"
                "RETURN\r"
                "PROC MAIN()\r"
                "A()\r"
                "Helper()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("x main 0 23\n", obj)
            self.assertIn("x a 22 1\n", obj)
            self.assertIn("b u0M\n", obj)
            self.assertIn("b M\n", obj)
            self.assertIn("u helper\n", obj)
            self.assertIn(
                "m 20 16 10 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n",
                obj,
            )
            self.assertIn("r 4 u0\n", obj)
            self.assertNotIn("b c0u0r\n", obj)

    def test_actc_compile_path_emits_machine_obj_for_local_then_two_external_calls(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        build_env["ACTC_PREALLOCATE_BODY_EXTERNALS"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-machine-local-external-pair-call"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC A()\r"
                "RETURN\r"
                "PROC MAIN()\r"
                "A()\r"
                "Helper()\r"
                "Other()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("x main 0 26\n", obj)
            self.assertIn("x a 25 1\n", obj)
            self.assertIn("b u0u1M\n", obj)
            self.assertIn("b M\n", obj)
            self.assertIn("u helper\n", obj)
            self.assertIn("u other\n", obj)
            self.assertIn(
                "m 20 19 10 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n",
                obj,
            )
            self.assertIn("r 4 u0\n", obj)
            self.assertIn("r 7 u1\n", obj)
            self.assertNotIn("b c0u0u1r\n", obj)

    def test_actc_compile_path_emits_machine_obj_for_local_then_repeated_external_call(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        build_env["ACTC_PREALLOCATE_BODY_EXTERNALS"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-machine-local-repeated-external-call"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC A()\r"
                "RETURN\r"
                "PROC MAIN()\r"
                "A()\r"
                "Helper()\r"
                "Helper()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("x main 0 26\n", obj)
            self.assertIn("x a 25 1\n", obj)
            self.assertIn("b u0u0M\n", obj)
            self.assertIn("b M\n", obj)
            self.assertEqual(obj.count("u helper\n"), 1, msg=obj)
            self.assertIn(
                "m 20 19 10 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n",
                obj,
            )
            self.assertIn("r 4 u0\n", obj)
            self.assertIn("r 7 u0\n", obj)
            self.assertNotIn("b c0u0u0r\n", obj)

    def test_actc_compile_path_emits_machine_obj_for_local_then_mixed_repeated_external_calls(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        build_env["ACTC_PREALLOCATE_BODY_EXTERNALS"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-machine-local-external-mixed-repeat-call"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC A()\r"
                "RETURN\r"
                "PROC MAIN()\r"
                "A()\r"
                "Helper()\r"
                "Other()\r"
                "Helper()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("x main 0 29\n", obj)
            self.assertIn("x a 28 1\n", obj)
            self.assertIn("b u0u1u0M\n", obj)
            self.assertIn("b M\n", obj)
            self.assertEqual(obj.count("u helper\n"), 1, msg=obj)
            self.assertIn("u other\n", obj)
            self.assertIn(
                "m 20 1C 10 20 00 00 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n",
                obj,
            )
            self.assertIn("r 4 u0\n", obj)
            self.assertIn("r 7 u1\n", obj)
            self.assertIn("r 10 u0\n", obj)
            self.assertNotIn("b c0u0u1u0r\n", obj)

    def test_actc_compile_path_emits_machine_obj_for_two_external_calls(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        build_env["ACTC_PREALLOCATE_BODY_EXTERNALS"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-machine-external-pair-call"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "Helper()\r"
                "Other()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("x main 0 22\n", obj)
            self.assertIn("b u0u1M\n", obj)
            self.assertIn("u helper\n", obj)
            self.assertIn("u other\n", obj)
            self.assertIn(
                "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n",
                obj,
            )
            self.assertIn("r 1 u0\n", obj)
            self.assertIn("r 4 u1\n", obj)
            self.assertNotIn("b u0u1r\n", obj)

    def test_actc_compile_path_emits_machine_obj_for_three_external_calls(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        build_env["ACTC_PREALLOCATE_BODY_EXTERNALS"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-machine-external-triple-call"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "Helper()\r"
                "Other()\r"
                "Third()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("x main 0 25\n", obj)
            self.assertIn("b u0u1u2M\n", obj)
            self.assertIn("u helper\n", obj)
            self.assertIn("u other\n", obj)
            self.assertIn("u third\n", obj)
            self.assertIn(
                "m 20 00 00 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n",
                obj,
            )
            self.assertIn("r 1 u0\n", obj)
            self.assertIn("r 4 u1\n", obj)
            self.assertIn("r 7 u2\n", obj)
            self.assertNotIn("b u0u1u2r\n", obj)

    def test_actc_compile_path_emits_machine_obj_for_mixed_repeated_external_calls(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        build_env["ACTC_PREALLOCATE_BODY_EXTERNALS"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-machine-external-mixed-repeat-call"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "Helper()\r"
                "Other()\r"
                "Helper()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("x main 0 25\n", obj)
            self.assertIn("b u0u1M\n", obj)
            self.assertEqual(obj.count("u helper\n"), 1, msg=obj)
            self.assertIn("u other\n", obj)
            self.assertIn(
                "m 20 00 00 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n",
                obj,
            )
            self.assertIn("r 1 u0\n", obj)
            self.assertIn("r 4 u1\n", obj)
            self.assertIn("r 7 u0\n", obj)
            self.assertNotIn("b u0u1u0r\n", obj)

    def test_actc_compile_path_emits_machine_obj_for_repeated_external_call(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        build_env["ACTC_PREALLOCATE_BODY_EXTERNALS"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-machine-repeated-external-call"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "Helper()\r"
                "Helper()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("x main 0 22\n", obj)
            self.assertIn("b u0M\n", obj)
            self.assertEqual(obj.count("u helper\n"), 1, msg=obj)
            self.assertIn(
                "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n",
                obj,
            )
            self.assertIn("r 1 u0\n", obj)
            self.assertIn("r 4 u0\n", obj)
            self.assertNotIn("b u0u0r\n", obj)

    def test_actc_compile_path_uses_decl_counts_overlay_when_enabled(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-compile"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "INT A=(8/2)+1+2*3\r"
                "BYTE B=[((1<2 AND 2<3) OR NOT(0=1))+1]\r"
                "PROC MAIN()\r"
                "PrintIE(A)\r"
                "PrintIE(B)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "8000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_context"][0:2], [5, 0], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL1.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL2.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL3.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL4.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL5.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("q 0 0 4 6\n", obj)
            self.assertIn("V g i 0 0 2 5\n", obj)
            self.assertIn("V g b 1 0 3 6\n", obj)
            self.assertIn("v a 11\n", obj)
            self.assertIn("v b 2\n", obj)

    def test_actc_compile_path_emits_param_and_local_debug_records(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-debug-vars"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "INT A\r"
                "PROC MAIN(P)\r"
                "INT L\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "8000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("V g i 0 0 2 5\n", obj)
            self.assertIn("V p i 0 1 0 3 11\n", obj)
            self.assertIn("V l i 0 2 0 4 5\n", obj)
            self.assertIn("v a 0\n", obj)
            self.assertIn("v p 0\n", obj)
            self.assertIn("v l 0\n", obj)

    def test_actc_compile_path_decl_overlay_pages_large_source(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-paged-compile"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")

            prefix = "MODULE MAIN\rINT A=(8/2)+1+2*3\r"
            filler_len = 20600 - len(prefix)
            self.assertGreater(filler_len, 0)
            source = (
                prefix
                + ("\r" * filler_len)
                + "BYTE B=[1+1]\r"
                + "PROC MAIN()\r"
                + "PrintIE(A)\r"
                + "PrintIE(B)\r"
                + "RETURN\r"
            )
            (source_dir / "main.act").write_text(source, encoding="ascii")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "24000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_context"][0:2], [5, 0], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL1.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL2.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL3.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL4.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL5.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertRegex(obj, r"q 0 0 \d+ 6\n")
            self.assertRegex(obj, r"V g i 0 0 2 5\n")
            self.assertRegex(obj, r"V g b 1 0 \d+ 6\n")
            self.assertIn("v a 11\n", obj)
            self.assertIn("v b 2\n", obj)

    def test_actc_compile_path_uses_body_overlay_when_enabled(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        build_env["ACTC_PREALLOCATE_BODY_EXTERNALS"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-body-overlay-compile"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "PrintE(\"OK\")\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("l 0 0 0 3 1\n", obj)
            self.assertIn("l 0 1 0 4 1\n", obj)
            self.assertIn("b e0r\n", obj)
            self.assertIn("s OK\n", obj)

    def test_actc_compile_path_body_overlay_preserves_multiple_print_literal_indices(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        build_env["ACTC_PREALLOCATE_BODY_EXTERNALS"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-body-overlay-print-literals"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "PrintE(\"LT\")\r"
                "PrintE(\"EQ\")\r"
                "PrintI(1)\r"
                "PrintIE(2)\r"
                "PrintE(\"GE\")\r"
                "PrintE(\"NE\")\r"
                "PrintI(3)\r"
                "PrintIE(4)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            object_path = object_dir / "MAIN.OBJ"
            if not object_path.is_file():
                object_path = object_dir / "main.obj"
            obj = object_path.read_text(encoding="ascii")
            self.assertIn("b e0e1j0i1e2e3j2i3r\n", obj)
            self.assertIn("s LT\n", obj)
            self.assertIn("s EQ\n", obj)
            self.assertIn("s GE\n", obj)
            self.assertIn("s NE\n", obj)
            self.assertIn("i 1\n", obj)
            self.assertIn("i 2\n", obj)
            self.assertIn("i 3\n", obj)
            self.assertIn("i 4\n", obj)
            self.assertNotIn("u printi\n", obj)
            self.assertNotIn("u printie\n", obj)

    def test_actc_compile_path_body_overlay_records_local_and_external_calls(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        build_env["ACTC_PREALLOCATE_BODY_EXTERNALS"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-body-overlay-external-call"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "Helper()\r"
                "ExtCall()\r"
                "RETURN\r"
                "PROC Helper()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("x main 0 7\n", obj)
            self.assertIn("x helper 7 1\n", obj)
            self.assertIn("b c1u0r\n", obj)
            self.assertIn("b r\n", obj)
            self.assertIn("u extcall\n", obj)

            builtin_project_root = image_root / "BUILTIN"
            builtin_source_dir = builtin_project_root / "src"
            builtin_object_dir = builtin_project_root / "obj"
            builtin_source_dir.mkdir(parents=True)
            builtin_object_dir.mkdir()
            (builtin_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (builtin_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "SidVol(10)\r"
                "ExtCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(builtin_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            builtin_summary = json.loads(result.stdout)
            self.assertEqual(builtin_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(builtin_summary["hit_limit"], msg=result.stdout)
            builtin_obj = (builtin_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b p0u0u1r\n", builtin_obj)
            self.assertIn("u rt_sid_vol\n", builtin_obj)
            self.assertIn("u extcall\n", builtin_obj)
            self.assertIn("i 10\n", builtin_obj)

            real_project_root = image_root / "REALIMPORT"
            real_source_dir = real_project_root / "src"
            real_object_dir = real_project_root / "obj"
            real_source_dir.mkdir(parents=True)
            real_object_dir.mkdir()
            (real_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (real_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=1000\r"
                "PrintRE(X)\r"
                "ExtCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(real_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            real_summary = json.loads(result.stdout)
            self.assertEqual(real_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(real_summary["hit_limit"], msg=result.stdout)
            real_obj = (real_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b p0u0T0S0L0U0p1u1u2r\n", real_obj)
            self.assertIn("u rt_i_to_f\n", real_obj)
            self.assertIn("u rt_print_f\n", real_obj)
            self.assertIn("u extcall\n", real_obj)
            self.assertLess(real_obj.index("u rt_print_f\n"), real_obj.index("u extcall\n"))
            self.assertIn("i 1000\n", real_obj)

            real_print_conversion_project_root = image_root / "REALPRINTCONVERSIONIMPORT"
            real_print_conversion_source_dir = real_print_conversion_project_root / "src"
            real_print_conversion_object_dir = real_print_conversion_project_root / "obj"
            real_print_conversion_source_dir.mkdir(parents=True)
            real_print_conversion_object_dir.mkdir()
            (real_print_conversion_project_root / "ACTION.PROJ").write_text(
                "ACTION PROJECT\rMAIN.ACT\r", encoding="ascii"
            )
            (real_print_conversion_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "CARD C=[255]\r"
                "INT I=[0]\r"
                "PROC MAIN()\r"
                "PrintR(REAL(C))\r"
                "PrintRE(REAL(I))\r"
                "ExtCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(real_print_conversion_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            real_print_conversion_summary = json.loads(result.stdout)
            self.assertEqual(real_print_conversion_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(real_print_conversion_summary["hit_limit"], msg=result.stdout)
            real_print_conversion_obj = (real_print_conversion_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b L0u0p0u1L1u2p1u1u3r\n", real_print_conversion_obj)
            real_print_conversion_symbols = ("rt_i_to_f", "rt_print_f", "rt_s_to_f", "extcall")
            for symbol in real_print_conversion_symbols:
                self.assertIn(f"u {symbol}\n", real_print_conversion_obj)
            self.assertNotIn("u real\n", real_print_conversion_obj)
            for left, right in zip(real_print_conversion_symbols, real_print_conversion_symbols[1:]):
                self.assertLess(
                    real_print_conversion_obj.index(f"u {left}\n"),
                    real_print_conversion_obj.index(f"u {right}\n"),
                )

            real_print_numeric_project_root = image_root / "REALPRINTNUMERICIMPORT"
            real_print_numeric_source_dir = real_print_numeric_project_root / "src"
            real_print_numeric_object_dir = real_print_numeric_project_root / "obj"
            real_print_numeric_source_dir.mkdir(parents=True)
            real_print_numeric_object_dir.mkdir()
            (real_print_numeric_project_root / "ACTION.PROJ").write_text(
                "ACTION PROJECT\rMAIN.ACT\r", encoding="ascii"
            )
            (real_print_numeric_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "PrintR(REAL(128*2))\r"
                "PrintRE(REAL(0-(128*2)))\r"
                "ExtCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(real_print_numeric_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            real_print_numeric_summary = json.loads(result.stdout)
            self.assertEqual(real_print_numeric_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(real_print_numeric_summary["hit_limit"], msg=result.stdout)
            real_print_numeric_obj = (real_print_numeric_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b p0u0p1u1p2u2p3u1u3r\n", real_print_numeric_obj)
            real_print_numeric_symbols = ("rt_i_to_f", "rt_print_f", "rt_s_to_f", "extcall")
            for symbol in real_print_numeric_symbols:
                self.assertIn(f"u {symbol}\n", real_print_numeric_obj)
            for left, right in zip(real_print_numeric_symbols, real_print_numeric_symbols[1:]):
                self.assertLess(
                    real_print_numeric_obj.index(f"u {left}\n"),
                    real_print_numeric_obj.index(f"u {right}\n"),
                )

            real_print_unary_project_root = image_root / "REALPRINTUNARYIMPORT"
            real_print_unary_source_dir = real_print_unary_project_root / "src"
            real_print_unary_object_dir = real_print_unary_project_root / "obj"
            real_print_unary_source_dir.mkdir(parents=True)
            real_print_unary_object_dir.mkdir()
            (real_print_unary_project_root / "ACTION.PROJ").write_text(
                "ACTION PROJECT\rMAIN.ACT\r", encoding="ascii"
            )
            (real_print_unary_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "PROC MAIN()\r"
                "PrintR(FABS(A))\r"
                "PrintRE(FSQRT(A))\r"
                "ExtCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(real_print_unary_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            real_print_unary_summary = json.loads(result.stdout)
            self.assertEqual(real_print_unary_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(real_print_unary_summary["hit_limit"], msg=result.stdout)
            real_print_unary_obj = (real_print_unary_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b L0U0u0p0u1L0U0u2p1u1u3r\n", real_print_unary_obj)
            real_print_unary_symbols = ("rt_f_abs", "rt_print_f", "rt_f_sqrt", "extcall")
            for symbol in real_print_unary_symbols:
                self.assertIn(f"u {symbol}\n", real_print_unary_obj)
            for left, right in zip(real_print_unary_symbols, real_print_unary_symbols[1:]):
                self.assertLess(
                    real_print_unary_obj.index(f"u {left}\n"),
                    real_print_unary_obj.index(f"u {right}\n"),
                )

            real_print_binary_project_root = image_root / "REALPRINTBINARYIMPORT"
            real_print_binary_source_dir = real_print_binary_project_root / "src"
            real_print_binary_object_dir = real_print_binary_project_root / "obj"
            real_print_binary_source_dir.mkdir(parents=True)
            real_print_binary_object_dir.mkdir()
            (real_print_binary_project_root / "ACTION.PROJ").write_text(
                "ACTION PROJECT\rMAIN.ACT\r", encoding="ascii"
            )
            (real_print_binary_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "PROC MAIN()\r"
                "PrintR(A+B)\r"
                "PrintRE(A/B)\r"
                "ExtCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(real_print_binary_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            real_print_binary_summary = json.loads(result.stdout)
            self.assertEqual(real_print_binary_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(real_print_binary_summary["hit_limit"], msg=result.stdout)
            real_print_binary_obj = (real_print_binary_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b L0U0L1U1u0p0u1L0U0L1U1u2p1u1u3r\n", real_print_binary_obj)
            real_print_binary_symbols = ("rt_f_add", "rt_print_f", "rt_f_div", "extcall")
            for symbol in real_print_binary_symbols:
                self.assertIn(f"u {symbol}\n", real_print_binary_obj)
            for left, right in zip(real_print_binary_symbols, real_print_binary_symbols[1:]):
                self.assertLess(
                    real_print_binary_obj.index(f"u {left}\n"),
                    real_print_binary_obj.index(f"u {right}\n"),
                )

            real_op_project_root = image_root / "REALOPIMPORT"
            real_op_source_dir = real_op_project_root / "src"
            real_op_object_dir = real_op_project_root / "obj"
            real_op_source_dir.mkdir(parents=True)
            real_op_object_dir.mkdir()
            (real_op_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (real_op_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "REAL R\r"
                "PROC MAIN()\r"
                "R=A+B\r"
                "ExtCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(real_op_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            real_op_summary = json.loads(result.stdout)
            self.assertEqual(real_op_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(real_op_summary["hit_limit"], msg=result.stdout)
            real_op_obj = (real_op_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b L0U0L1U1u0T2S2u1r\n", real_op_obj)
            self.assertIn("u rt_f_add\n", real_op_obj)
            self.assertIn("u extcall\n", real_op_obj)
            self.assertLess(real_op_obj.index("u rt_f_add\n"), real_op_obj.index("u extcall\n"))

            real_unary_project_root = image_root / "REALUNARYIMPORT"
            real_unary_source_dir = real_unary_project_root / "src"
            real_unary_object_dir = real_unary_project_root / "obj"
            real_unary_source_dir.mkdir(parents=True)
            real_unary_object_dir.mkdir()
            (real_unary_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (real_unary_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL R\r"
                "PROC MAIN()\r"
                "R=FABS(A)\r"
                "ExtCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(real_unary_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            real_unary_summary = json.loads(result.stdout)
            self.assertEqual(real_unary_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(real_unary_summary["hit_limit"], msg=result.stdout)
            real_unary_obj = (real_unary_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b L0U0u0T1S1u1r\n", real_unary_obj)
            self.assertIn("u rt_f_abs\n", real_unary_obj)
            self.assertIn("u extcall\n", real_unary_obj)
            self.assertLess(real_unary_obj.index("u rt_f_abs\n"), real_unary_obj.index("u extcall\n"))

            real_explicit_project_root = image_root / "REALEXPLICITIMPORT"
            real_explicit_source_dir = real_explicit_project_root / "src"
            real_explicit_object_dir = real_explicit_project_root / "obj"
            real_explicit_source_dir.mkdir(parents=True)
            real_explicit_object_dir.mkdir()
            (real_explicit_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (real_explicit_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL R\r"
                "PROC MAIN()\r"
                "R=REAL(3)\r"
                "ExtCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(real_explicit_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            real_explicit_summary = json.loads(result.stdout)
            self.assertEqual(real_explicit_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(real_explicit_summary["hit_limit"], msg=result.stdout)
            real_explicit_obj = (real_explicit_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_i_to_f\n", real_explicit_obj)
            self.assertIn("u extcall\n", real_explicit_obj)
            self.assertLess(real_explicit_obj.index("u rt_i_to_f\n"), real_explicit_obj.index("u extcall\n"))
            self.assertIn("i 3\n", real_explicit_obj)

            real_direct_bridge_project_root = image_root / "REALDIRECTBRIDGEIMPORT"
            real_direct_bridge_source_dir = real_direct_bridge_project_root / "src"
            real_direct_bridge_object_dir = real_direct_bridge_project_root / "obj"
            real_direct_bridge_source_dir.mkdir(parents=True)
            real_direct_bridge_object_dir.mkdir()
            (real_direct_bridge_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (real_direct_bridge_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "INT I\r"
                "REAL R\r"
                "PROC MAIN()\r"
                "R=I\r"
                "ExtCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(real_direct_bridge_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            real_direct_bridge_summary = json.loads(result.stdout)
            self.assertEqual(real_direct_bridge_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(real_direct_bridge_summary["hit_limit"], msg=result.stdout)
            real_direct_bridge_obj = (real_direct_bridge_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_s_to_f\n", real_direct_bridge_obj)
            self.assertIn("u extcall\n", real_direct_bridge_obj)
            self.assertLess(real_direct_bridge_obj.index("u rt_s_to_f\n"), real_direct_bridge_obj.index("u extcall\n"))

            real_explicit_bridge_project_root = image_root / "REALEXPLICITBRIDGEIMPORT"
            real_explicit_bridge_source_dir = real_explicit_bridge_project_root / "src"
            real_explicit_bridge_object_dir = real_explicit_bridge_project_root / "obj"
            real_explicit_bridge_source_dir.mkdir(parents=True)
            real_explicit_bridge_object_dir.mkdir()
            (real_explicit_bridge_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (real_explicit_bridge_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "INT I\r"
                "REAL R\r"
                "PROC MAIN()\r"
                "R=REAL(I)\r"
                "ExtCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(real_explicit_bridge_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            real_explicit_bridge_summary = json.loads(result.stdout)
            self.assertEqual(real_explicit_bridge_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(real_explicit_bridge_summary["hit_limit"], msg=result.stdout)
            real_explicit_bridge_obj = (real_explicit_bridge_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_s_to_f\n", real_explicit_bridge_obj)
            self.assertIn("u extcall\n", real_explicit_bridge_obj)
            self.assertLess(real_explicit_bridge_obj.index("u rt_s_to_f\n"), real_explicit_bridge_obj.index("u extcall\n"))

            real_wide_sources = (
                (
                    "REALPLAINWIDEPREALLOC",
                    "MODULE MAIN\r"
                    "REAL R\r"
                    "PROC MAIN()\r"
                    "R=(128*2)\r"
                    "ExtCall()\r"
                    "R=0-(128*2)\r"
                    "LaterCall()\r"
                    "RETURN\r",
                ),
                (
                    "REALEXPLICITWIDEPREALLOC",
                    "MODULE MAIN\r"
                    "REAL R\r"
                    "PROC MAIN()\r"
                    "R=REAL(128*2)\r"
                    "ExtCall()\r"
                    "R=REAL(0-(128*2))\r"
                    "LaterCall()\r"
                    "RETURN\r",
                ),
            )
            for project_name, source_text in real_wide_sources:
                real_wide_project_root = image_root / project_name
                real_wide_source_dir = real_wide_project_root / "src"
                real_wide_object_dir = real_wide_project_root / "obj"
                real_wide_source_dir.mkdir(parents=True)
                real_wide_object_dir.mkdir()
                (real_wide_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
                (real_wide_source_dir / "main.act").write_text(source_text, encoding="ascii")

                result = self.run_checked(
                    [
                        str(self.build_dir / "tool_abi_harness"),
                        "--prg",
                        str(self.build_dir / "ACTC.PRG"),
                        "--workspace",
                        str(real_wide_project_root),
                        "--cmdline",
                        "MAIN",
                        "--services-inc",
                        str(self.build_dir / "udos_services.inc"),
                        "--labels",
                        str(self.build_dir / "actc.current.labels"),
                        "--max-steps",
                        "12000000",
                    ]
                )
                real_wide_summary = json.loads(result.stdout)
                self.assertEqual(real_wide_summary["exit_status"], 0, msg=result.stdout)
                self.assertFalse(real_wide_summary["hit_limit"], msg=result.stdout)
                real_wide_obj = (real_wide_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
                real_wide_symbols = ("rt_i_to_f", "extcall", "rt_s_to_f", "latercall")
                for symbol in real_wide_symbols:
                    self.assertIn(f"u {symbol}\n", real_wide_obj)
                for left, right in zip(real_wide_symbols, real_wide_symbols[1:]):
                    self.assertLess(real_wide_obj.index(f"u {left}\n"), real_wide_obj.index(f"u {right}\n"))

            real_if_project_root = image_root / "REALIFIMPORT"
            real_if_source_dir = real_if_project_root / "src"
            real_if_object_dir = real_if_project_root / "obj"
            real_if_source_dir.mkdir(parents=True)
            real_if_object_dir.mkdir()
            (real_if_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (real_if_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "PROC MAIN()\r"
                "IF A<B THEN\r"
                "ExtCall()\r"
                "FI\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(real_if_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            real_if_summary = json.loads(result.stdout)
            self.assertEqual(real_if_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(real_if_summary["hit_limit"], msg=result.stdout)
            real_if_obj = (real_if_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_f_cmp\n", real_if_obj)
            self.assertIn("u extcall\n", real_if_obj)
            self.assertLess(real_if_obj.index("u rt_f_cmp\n"), real_if_obj.index("u extcall\n"))

            real_while_project_root = image_root / "REALWHILEIMPORT"
            real_while_source_dir = real_while_project_root / "src"
            real_while_object_dir = real_while_project_root / "obj"
            real_while_source_dir.mkdir(parents=True)
            real_while_object_dir.mkdir()
            (real_while_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (real_while_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "PROC MAIN()\r"
                "WHILE A<B DO\r"
                "ExtCall()\r"
                "OD\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(real_while_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            real_while_summary = json.loads(result.stdout)
            self.assertEqual(real_while_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(real_while_summary["hit_limit"], msg=result.stdout)
            real_while_obj = (real_while_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_f_cmp\n", real_while_obj)
            self.assertIn("u extcall\n", real_while_obj)
            self.assertLess(real_while_obj.index("u rt_f_cmp\n"), real_while_obj.index("u extcall\n"))

            real_until_project_root = image_root / "REALUNTILIMPORT"
            real_until_source_dir = real_until_project_root / "src"
            real_until_object_dir = real_until_project_root / "obj"
            real_until_source_dir.mkdir(parents=True)
            real_until_object_dir.mkdir()
            (real_until_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (real_until_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "PROC MAIN()\r"
                "DO\r"
                "UNTIL A<B\r"
                "ExtCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(real_until_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            real_until_summary = json.loads(result.stdout)
            self.assertEqual(real_until_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(real_until_summary["hit_limit"], msg=result.stdout)
            real_until_obj = (real_until_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_f_cmp\n", real_until_obj)
            self.assertIn("u extcall\n", real_until_obj)
            self.assertLess(real_until_obj.index("u rt_f_cmp\n"), real_until_obj.index("u extcall\n"))

            int_of_real_project_root = image_root / "INTOFREALIMPORT"
            int_of_real_source_dir = int_of_real_project_root / "src"
            int_of_real_object_dir = int_of_real_project_root / "obj"
            int_of_real_source_dir.mkdir(parents=True)
            int_of_real_object_dir.mkdir()
            (int_of_real_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (int_of_real_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "INT X\r"
                "PROC MAIN()\r"
                "X=INT(A)\r"
                "ExtCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(int_of_real_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            int_of_real_summary = json.loads(result.stdout)
            self.assertEqual(int_of_real_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(int_of_real_summary["hit_limit"], msg=result.stdout)
            int_of_real_obj = (int_of_real_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_f_to_i\n", int_of_real_obj)
            self.assertIn("u extcall\n", int_of_real_obj)
            self.assertLess(int_of_real_obj.index("u rt_f_to_i\n"), int_of_real_obj.index("u extcall\n"))

            int_expr_project_root = image_root / "INTEXPRIMPORT"
            int_expr_source_dir = int_expr_project_root / "src"
            int_expr_object_dir = int_expr_project_root / "obj"
            int_expr_source_dir.mkdir(parents=True)
            int_expr_object_dir.mkdir()
            (int_expr_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (int_expr_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "INT X\r"
                "PROC MAIN()\r"
                "X=INT(A)+1\r"
                "ExtCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(int_expr_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            int_expr_summary = json.loads(result.stdout)
            self.assertEqual(int_expr_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(int_expr_summary["hit_limit"], msg=result.stdout)
            int_expr_obj = (int_expr_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_f_to_i\n", int_expr_obj)
            self.assertIn("u extcall\n", int_expr_obj)
            self.assertNotIn("u int\n", int_expr_obj)
            self.assertNotIn("u t\n", int_expr_obj)
            self.assertNotIn("u nt\n", int_expr_obj)
            self.assertIn("i 1\n", int_expr_obj)
            self.assertIn("u0p0aS", int_expr_obj)
            self.assertLess(int_expr_obj.index("u rt_f_to_i\n"), int_expr_obj.index("u extcall\n"))

            int_return_project_root = image_root / "INTRETURNIMPORT"
            int_return_source_dir = int_return_project_root / "src"
            int_return_object_dir = int_return_project_root / "obj"
            int_return_source_dir.mkdir(parents=True)
            int_return_object_dir.mkdir()
            (int_return_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (int_return_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "PROC MAIN()\r"
                "RETURN INT(A)+1\r"
                "ExtCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(int_return_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            int_return_summary = json.loads(result.stdout)
            self.assertEqual(int_return_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(int_return_summary["hit_limit"], msg=result.stdout)
            int_return_obj = (int_return_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_f_to_i\n", int_return_obj)
            self.assertIn("u extcall\n", int_return_obj)
            self.assertNotIn("u int\n", int_return_obj)
            self.assertNotIn("u t\n", int_return_obj)
            self.assertNotIn("u nt\n", int_return_obj)
            self.assertIn("i 1\n", int_return_obj)
            self.assertIn("u0p0ar", int_return_obj)
            self.assertLess(int_return_obj.index("u rt_f_to_i\n"), int_return_obj.index("u extcall\n"))

            int_call_arg_project_root = image_root / "INTCALLARGIMPORT"
            int_call_arg_source_dir = int_call_arg_project_root / "src"
            int_call_arg_object_dir = int_call_arg_project_root / "obj"
            int_call_arg_source_dir.mkdir(parents=True)
            int_call_arg_object_dir.mkdir()
            (int_call_arg_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (int_call_arg_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "PROC MAIN()\r"
                "ExtCall(INT(A))\r"
                "LaterCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(int_call_arg_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            int_call_arg_summary = json.loads(result.stdout)
            self.assertEqual(int_call_arg_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(int_call_arg_summary["hit_limit"], msg=result.stdout)
            int_call_arg_obj = (int_call_arg_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            int_call_arg_symbols = ("extcall", "rt_f_to_i", "latercall")
            for symbol in int_call_arg_symbols:
                self.assertIn(f"u {symbol}\n", int_call_arg_obj)
            self.assertNotIn("u int\n", int_call_arg_obj)
            self.assertNotIn("u t\n", int_call_arg_obj)
            self.assertNotIn("u nt\n", int_call_arg_obj)
            self.assertIn("L0U0u1u0", int_call_arg_obj)
            for left, right in zip(int_call_arg_symbols, int_call_arg_symbols[1:]):
                self.assertLess(int_call_arg_obj.index(f"u {left}\n"), int_call_arg_obj.index(f"u {right}\n"))

            word_call_project_root = image_root / "WORDCALLEXPRIMPORT"
            word_call_source_dir = word_call_project_root / "src"
            word_call_object_dir = word_call_project_root / "obj"
            word_call_source_dir.mkdir(parents=True)
            word_call_object_dir.mkdir()
            (word_call_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (word_call_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "INT X\r"
                "PROC MAIN()\r"
                "X=ExtCall()\r"
                "LaterCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(word_call_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            word_call_summary = json.loads(result.stdout)
            self.assertEqual(word_call_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(word_call_summary["hit_limit"], msg=result.stdout)
            word_call_obj = (word_call_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u extcall\n", word_call_obj)
            self.assertIn("u latercall\n", word_call_obj)
            self.assertLess(word_call_obj.index("u extcall\n"), word_call_obj.index("u latercall\n"))

            return_call_project_root = image_root / "RETURNCALLEXPRIMPORT"
            return_call_source_dir = return_call_project_root / "src"
            return_call_object_dir = return_call_project_root / "obj"
            return_call_source_dir.mkdir(parents=True)
            return_call_object_dir.mkdir()
            (return_call_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (return_call_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "RETURN ExtCall()\r"
                "LaterCall()\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(return_call_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            return_call_summary = json.loads(result.stdout)
            self.assertEqual(return_call_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(return_call_summary["hit_limit"], msg=result.stdout)
            return_call_obj = (return_call_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u extcall\n", return_call_obj)
            self.assertIn("u latercall\n", return_call_obj)
            self.assertLess(return_call_obj.index("u extcall\n"), return_call_obj.index("u latercall\n"))

            arg_call_project_root = image_root / "ARGCALLEXPRIMPORT"
            arg_call_source_dir = arg_call_project_root / "src"
            arg_call_object_dir = arg_call_project_root / "obj"
            arg_call_source_dir.mkdir(parents=True)
            arg_call_object_dir.mkdir()
            (arg_call_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (arg_call_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "INT X\r"
                "PROC MAIN()\r"
                "X=ExtCall(ArgOne(1))\r"
                "X=LeftAssign(LAssignArg(1)) AND RightAssign(RAssignArg(2))\r"
                "RETURN RetCall(ArgTwo(2))\r"
                "RETURN LeftReturn(LReturnArg(3)) OR RightReturn(RReturnArg(4))\r"
                "LaterCall()\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(arg_call_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            arg_call_summary = json.loads(result.stdout)
            self.assertEqual(arg_call_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(arg_call_summary["hit_limit"], msg=result.stdout)
            arg_call_obj = (arg_call_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            arg_call_symbols = (
                "extcall",
                "argone",
                "leftassign",
                "lassignarg",
                "rightassign",
                "rassignarg",
                "retcall",
                "argtwo",
                "leftreturn",
                "lreturnarg",
                "rightreturn",
                "rreturnarg",
                "latercall",
            )
            for symbol in arg_call_symbols:
                self.assertIn(f"u {symbol}\n", arg_call_obj)
            for left, right in zip(arg_call_symbols, arg_call_symbols[1:]):
                self.assertLess(arg_call_obj.index(f"u {left}\n"), arg_call_obj.index(f"u {right}\n"))

            plain_arg_call_project_root = image_root / "PLAINARGCALLEXPRIMPORT"
            plain_arg_call_source_dir = plain_arg_call_project_root / "src"
            plain_arg_call_object_dir = plain_arg_call_project_root / "obj"
            plain_arg_call_source_dir.mkdir(parents=True)
            plain_arg_call_object_dir.mkdir()
            (plain_arg_call_project_root / "ACTION.PROJ").write_text(
                "ACTION PROJECT\rMAIN.ACT\r", encoding="ascii"
            )
            (plain_arg_call_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "OuterCall(1+InnerCall(NestedCall(2)),(OtherCall(4)),3)\r"
                "LaterCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(plain_arg_call_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            plain_arg_call_summary = json.loads(result.stdout)
            self.assertEqual(plain_arg_call_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(plain_arg_call_summary["hit_limit"], msg=result.stdout)
            plain_arg_call_obj = (plain_arg_call_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u outercall\n", plain_arg_call_obj)
            self.assertIn("u innercall\n", plain_arg_call_obj)
            self.assertIn("u nestedcall\n", plain_arg_call_obj)
            self.assertIn("u othercall\n", plain_arg_call_obj)
            self.assertIn("u latercall\n", plain_arg_call_obj)
            self.assertLess(plain_arg_call_obj.index("u outercall\n"), plain_arg_call_obj.index("u innercall\n"))
            self.assertLess(plain_arg_call_obj.index("u innercall\n"), plain_arg_call_obj.index("u nestedcall\n"))
            self.assertLess(plain_arg_call_obj.index("u nestedcall\n"), plain_arg_call_obj.index("u othercall\n"))
            self.assertLess(plain_arg_call_obj.index("u othercall\n"), plain_arg_call_obj.index("u latercall\n"))

            condition_call_project_root = image_root / "CONDITIONCALLEXPRIMPORT"
            condition_call_source_dir = condition_call_project_root / "src"
            condition_call_object_dir = condition_call_project_root / "obj"
            condition_call_source_dir.mkdir(parents=True)
            condition_call_object_dir.mkdir()
            (condition_call_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (condition_call_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "IF IfCall(IfArg(1)) THEN\r"
                "FI\r"
                "IF LeftAnd(LAndArg(1)) AND RightAnd(RAndArg(2)) THEN\r"
                "FI\r"
                "IF NOT NotIf(NotArg(3)) THEN\r"
                "FI\r"
                "WHILE WhileCall(WhileArg(1)) DO\r"
                "OD\r"
                "WHILE LeftOr(LOrArg(1)) OR RightOr(ROrArg(2)) DO\r"
                "OD\r"
                "WHILE (GroupLeft(GroupArg(1)) AND GroupRight(GroupRArg(2))) DO\r"
                "OD\r"
                "DO\r"
                "UNTIL UntilCall(UntilArg(1))\r"
                "DO\r"
                "UNTIL LeftUntil(LUntilArg(1)) AND RightUntil(RUntilArg(2))\r"
                "DO\r"
                "UNTIL NOT(UntilNotLeft(UNLArg(1)) OR UntilNotRight(UNRArg(2)))\r"
                "LaterCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(condition_call_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            condition_call_summary = json.loads(result.stdout)
            self.assertEqual(condition_call_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(condition_call_summary["hit_limit"], msg=result.stdout)
            condition_call_obj = (condition_call_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            condition_call_symbols = (
                "ifcall",
                "ifarg",
                "leftand",
                "landarg",
                "rightand",
                "randarg",
                "notif",
                "notarg",
                "whilecall",
                "whilearg",
                "leftor",
                "lorarg",
                "rightor",
                "rorarg",
                "groupleft",
                "grouparg",
                "groupright",
                "grouprarg",
                "untilcall",
                "untilarg",
                "leftuntil",
                "luntilarg",
                "rightuntil",
                "runtilarg",
                "untilnotleft",
                "unlarg",
                "untilnotright",
                "unrarg",
                "latercall",
            )
            for symbol in condition_call_symbols:
                self.assertIn(f"u {symbol}\n", condition_call_obj)
            for left, right in zip(condition_call_symbols, condition_call_symbols[1:]):
                self.assertLess(condition_call_obj.index(f"u {left}\n"), condition_call_obj.index(f"u {right}\n"))

            condition_compare_call_project_root = image_root / "CONDITIONCOMPARECALLEXPRIMPORT"
            condition_compare_call_source_dir = condition_compare_call_project_root / "src"
            condition_compare_call_object_dir = condition_compare_call_project_root / "obj"
            condition_compare_call_source_dir.mkdir(parents=True)
            condition_compare_call_object_dir.mkdir()
            (condition_compare_call_project_root / "ACTION.PROJ").write_text(
                "ACTION PROJECT\rMAIN.ACT\r", encoding="ascii"
            )
            (condition_compare_call_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "IF LeftIf(LIfArg(1))=RightIf(RIfArg(2)) THEN\r"
                "FI\r"
                "IF ChainLeftA(CLAArg(1))=ChainRightA(CRAArg(2)) AND ChainLeftB(CLBArg(3))<>ChainRightB(CRBArg(4)) THEN\r"
                "FI\r"
                "WHILE LeftWhile(LWhileArg(1))<>RightWhile(RWhileArg(2)) DO\r"
                "OD\r"
                "WHILE NOT(ChainWhileLeft(CWLArg(1))<=ChainWhileRight(CWRArg(2))) DO\r"
                "OD\r"
                "DO\r"
                "UNTIL LeftUntil(LUntilArg(1))>=RightUntil(RUntilArg(2))\r"
                "DO\r"
                "UNTIL (ChainUntilLeft(CULArg(1))>=ChainUntilRight(CURArg(2))) OR ChainUntilTail(CUTArg(3))=ChainUntilEnd(CUEArg(4))\r"
                "LaterCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(condition_compare_call_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            condition_compare_call_summary = json.loads(result.stdout)
            self.assertEqual(condition_compare_call_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(condition_compare_call_summary["hit_limit"], msg=result.stdout)
            condition_compare_call_obj = (condition_compare_call_object_dir / "MAIN.OBJ").read_text(
                encoding="ascii"
            )
            condition_compare_call_symbols = (
                "leftif",
                "lifarg",
                "rightif",
                "rifarg",
                "chainlefta",
                "claarg",
                "chainrighta",
                "craarg",
                "chainleftb",
                "clbarg",
                "chainrightb",
                "crbarg",
                "leftwhile",
                "lwhilearg",
                "rightwhile",
                "rwhilearg",
                "chainwhileleft",
                "cwlarg",
                "chainwhileright",
                "cwrarg",
                "leftuntil",
                "luntilarg",
                "rightuntil",
                "runtilarg",
                "chainuntilleft",
                "cularg",
                "chainuntilright",
                "curarg",
                "chainuntiltail",
                "cutarg",
                "chainuntilend",
                "cuearg",
                "latercall",
            )
            for symbol in condition_compare_call_symbols:
                self.assertIn(f"u {symbol}\n", condition_compare_call_obj)
            for left, right in zip(condition_compare_call_symbols, condition_compare_call_symbols[1:]):
                self.assertLess(
                    condition_compare_call_obj.index(f"u {left}\n"),
                    condition_compare_call_obj.index(f"u {right}\n"),
                )

            print_call_project_root = image_root / "PRINTCALLEXPRIMPORT"
            print_call_source_dir = print_call_project_root / "src"
            print_call_object_dir = print_call_project_root / "obj"
            print_call_source_dir.mkdir(parents=True)
            print_call_object_dir.mkdir()
            (print_call_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (print_call_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL R\r"
                "PROC MAIN()\r"
                "PrintI(ExtCall(PrintArg(1)))\r"
                "PrintI(LeftPrint(LPrintArg(1)) AND RightPrint(RPrintArg(2)))\r"
                "PrintIE(LineCall(LineArg(2)))\r"
                "PrintIE(SumPrint(SumArg(3))+TailPrint(TailArg(4)))\r"
                "PrintI(INT(R))\r"
                "LaterCall()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(print_call_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )
            print_call_summary = json.loads(result.stdout)
            self.assertEqual(print_call_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(print_call_summary["hit_limit"], msg=result.stdout)
            print_call_obj = (print_call_object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            print_call_symbols = (
                "extcall",
                "printarg",
                "leftprint",
                "lprintarg",
                "rightprint",
                "rprintarg",
                "linecall",
                "linearg",
                "sumprint",
                "sumarg",
                "tailprint",
                "tailarg",
                "rt_f_to_i",
                "latercall",
            )
            for symbol in print_call_symbols:
                self.assertIn(f"u {symbol}\n", print_call_obj)
            self.assertNotIn("u int\n", print_call_obj)
            for left, right in zip(print_call_symbols, print_call_symbols[1:]):
                self.assertLess(print_call_obj.index(f"u {left}\n"), print_call_obj.index(f"u {right}\n"))

            recursive_project_root = image_root / "RECURSE"
            recursive_source_dir = recursive_project_root / "src"
            recursive_object_dir = recursive_project_root / "obj"
            recursive_source_dir.mkdir(parents=True)
            recursive_object_dir.mkdir()
            (recursive_project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (recursive_source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "MAIN()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = subprocess.run(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(recursive_project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ],
                cwd=self.root,
                text=True,
                capture_output=True,
                check=False,
                timeout=60,
            )
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            recursive_summary = json.loads(result.stdout)
            self.assertNotEqual(recursive_summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(recursive_summary["hit_limit"], msg=result.stdout)
            self.assertIn("BAD PROC", recursive_summary["console"], msg=result.stdout)
            self.assertFalse((recursive_object_dir / "MAIN.OBJ").exists())

    def test_actc_compile_path_body_overlay_handles_real_add_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-body-overlay-real-add"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "REAL R\r"
                "PROC MAIN()\r"
                "R=A+B\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b L0U0L1U1u0T2S2r\n", obj)
            self.assertIn("u rt_f_add\n", obj)
            self.assertIn("V g r 0 0 2 6\n", obj)
            self.assertIn("V g r 1 0 3 6\n", obj)
            self.assertIn("V g r 2 0 4 6\n", obj)
            self.assertIn("v a 0 4\n", obj)
            self.assertIn("v b 0 4\n", obj)
            self.assertIn("v r 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_zero_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-body-overlay-real-zero"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=0\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b p0p0T0S0r\n", obj)
            self.assertIn("i 0\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_small_expr_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-body-overlay-real-small-expr"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=(1+2*3)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b p0p1T0S0r\n", obj)
            self.assertIn("i 0\n", obj)
            self.assertIn("i 16608\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_card_bridge_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-body-overlay-real-card-bridge"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "obj"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "CARD A=[255]\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "A=A+1\r"
                "X=A\r"
                "PrintE(\"DONE\")\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b L0p0aS0L0u0T1S1e0r\n", obj)
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("i 1\n", obj)
            self.assertIn("v a 255\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_int_bridge_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-int-bridge"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "INT A=[0]\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "A=0-7\r"
                "X=A\r"
                "PrintE(\"DONE\")\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b p0p1mS0L0u0T1S1e0r\n", obj)
            self.assertIn("u rt_s_to_f\n", obj)
            self.assertIn("i 7\n", obj)
            self.assertIn("v a 0\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_large_positive_bridge_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-large-bridge"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=(255+1)\r"
                "PrintE(\"DONE\")\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("i 256\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_explicit_card_conversion(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-explicit-card"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "CARD A=[255]\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "A=A+1\r"
                "X=REAL(A)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("i 1\n", obj)
            self.assertIn("v a 255\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_print_with_newline(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-printre"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=REAL(7)\r"
                "PrintRE(X)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b p1u0T0S0L0U0p2u1r\n", obj)
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("u rt_print_f\n", obj)

    def test_actc_compile_path_body_overlay_handles_int_of_real_var(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-int-of-real-var"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "INT X\r"
                "PROC MAIN()\r"
                "A=REAL(7)\r"
                "X=INT(A)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("u rt_f_to_i\n", obj)
            self.assertIn("i 0\n", obj)
            self.assertIn("i 7\n", obj)
            self.assertIn("v x 0\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_large_positive_direct_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-large-direct-assignment"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "PROC MAIN()\r"
                "A=32767\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("i 32767\n", obj)
            self.assertIn("v a 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_fractional_real_print_with_newline(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-printre-fraction"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "A=REAL(3)\r"
                "B=REAL(2)\r"
                "X=A/B\r"
                "PrintRE(X)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("b p1u0T0S0p3u0T1S1L0U0L1U1u1T2S2L2U2p4u2r\n", obj)
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("u rt_f_div\n", obj)
            self.assertIn("u rt_print_f\n", obj)
            self.assertIn("i 3\n", obj)
            self.assertIn("i 2\n", obj)
            self.assertIn("i 1\n", obj)
            self.assertIn("v a 0 4\n", obj)
            self.assertIn("v b 0 4\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_all_real_compare_ops(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-compare-all"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL A\r"
                "REAL B\r"
                "REAL C\r"
                "PROC MAIN()\r"
                "A=REAL(1)\r"
                "B=REAL(2)\r"
                "C=REAL(2)\r"
                "IF A<B THEN\r"
                "PrintE(\"LT\")\r"
                "FI\r"
                "IF B=C THEN\r"
                "PrintE(\"EQ\")\r"
                "FI\r"
                "IF C>=B THEN\r"
                "PrintE(\"GE\")\r"
                "FI\r"
                "IF A<>C THEN\r"
                "PrintE(\"NE\")\r"
                "FI\r"
                "IF B>A THEN\r"
                "PrintE(\"GT\")\r"
                "FI\r"
                "IF A<=B THEN\r"
                "PrintE(\"LE\")\r"
                "FI\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("u rt_f_cmp\n", obj)
            self.assertIn("s LT\n", obj)
            self.assertIn("s EQ\n", obj)
            self.assertIn("s GE\n", obj)
            self.assertIn("s NE\n", obj)
            self.assertIn("s GT\n", obj)
            self.assertIn("s LE\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_wide_mul_bridge_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-wide-mul"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=(128*2)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("i 256\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_signed_wide_mul_bridge_assignment(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-signed-wide-mul"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=0-(128*2)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_s_to_f\n", obj)
            self.assertIn("i 65280\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_explicit_large_sum_conversion(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-explicit-sum"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=REAL(255+1)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("i 256\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_explicit_wide_mul_conversion(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-explicit-wide-mul"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=REAL(128*2)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("i 256\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_explicit_signed_wide_div_conversion(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-explicit-signed-wide-div"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=REAL(0-(512/2))\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_s_to_f\n", obj)
            self.assertIn("i 65280\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_actc_compile_path_body_overlay_handles_real_explicit_signed_wide_mul_conversion(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-real-explicit-signed-wide-mul"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "REAL X\r"
                "PROC MAIN()\r"
                "X=REAL(0-(128*2))\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_s_to_f\n", obj)
            self.assertIn("i 65280\n", obj)
            self.assertIn("v x 0 4\n", obj)

    def test_noop_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_noop.sh")])

        overlay = self.build_dir / "ACTC_OVL0.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], 1)
        self.assertEqual(data[5], 0)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))

        entry_offset = entry - load_base
        self.assertEqual(data[entry_offset], 0x8E)

    def test_source_header_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])

        overlay = self.build_dir / "ACTC_OVL1.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], 1)
        self.assertEqual(data[5], 1)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))

    def test_decl_counts_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])

        overlay = self.build_dir / "ACTC_OVL2.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], 1)
        self.assertEqual(data[5], 2)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))

    def test_payload_layout_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])

        overlay = self.build_dir / "ACTC_OVL3.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], 1)
        self.assertEqual(data[5], 3)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))

    def test_runtime_import_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])

        overlay = self.build_dir / "ACTC_OVL4.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], 1)
        self.assertEqual(data[5], 4)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))

    def test_actc_compile_path_maps_referenced_hardware_builtins_to_runtime_objs(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-hardware-builtins"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "SpriteOn(2)\r"
                "SpriteHit()\r"
                "SpriteHitBg()\r"
                "SpriteColor(2,5)\r"
                "SpritePos(2,52,86)\r"
                "SpritePtr(2,128)\r"
                "SpriteData(2,64)\r"
                "SetSpriteMC(5,10)\r"
                "SidFreq(1,52)\r"
                "SidPulse(1,52)\r"
                "SidWave(1,64)\r"
                "SidAD(1,151)\r"
                "SidSR(1,248)\r"
                "SidOn(1)\r"
                "SidOff(1)\r"
                "SidRst()\r"
                "SidRoute(7)\r"
                "SidRes(10)\r"
                "SidCutoff(52)\r"
                "SidMode(48)\r"
                "SidVol(10)\r"
                "SidOsc3()\r"
                "SidEnv3()\r"
                "VicBank(1)\r"
                "BgColor(6)\r"
                "BorderColor(14)\r"
                "ScreenBase(1024)\r"
                "BitmapBase(8192)\r"
                "BitmapOn()\r"
                "BitmapOff()\r"
                "MBitmapOn()\r"
                "MBitmapOff()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_sprite_on\n", obj)
            self.assertIn("u rt_sprite_hit\n", obj)
            self.assertIn("u rt_sprite_hit_bg\n", obj)
            self.assertIn("u rt_sprite_color\n", obj)
            self.assertIn("u rt_sprite_pos\n", obj)
            self.assertIn("u rt_sprite_ptr\n", obj)
            self.assertIn("u rt_sprite_data\n", obj)
            self.assertIn("u rt_sprite_set_mc\n", obj)
            self.assertIn("u rt_sid_freq\n", obj)
            self.assertIn("u rt_sid_pulse\n", obj)
            self.assertIn("u rt_sid_wave\n", obj)
            self.assertIn("u rt_sid_ad\n", obj)
            self.assertIn("u rt_sid_sr\n", obj)
            self.assertIn("u rt_sid_on\n", obj)
            self.assertIn("u rt_sid_off\n", obj)
            self.assertIn("u rt_sid_rst\n", obj)
            self.assertIn("u rt_sid_route\n", obj)
            self.assertIn("u rt_sid_res\n", obj)
            self.assertIn("u rt_sid_cutoff\n", obj)
            self.assertIn("u rt_sid_mode\n", obj)
            self.assertIn("u rt_sid_vol\n", obj)
            self.assertIn("u rt_sid_osc3\n", obj)
            self.assertIn("u rt_sid_env3\n", obj)
            self.assertIn("u rt_gfx_vic_bank\n", obj)
            self.assertIn("u rt_gfx_bgcolor\n", obj)
            self.assertIn("u rt_gfx_bordercolor\n", obj)
            self.assertIn("u rt_gfx_screen_base\n", obj)
            self.assertIn("u rt_gfx_bitmap_base\n", obj)
            self.assertIn("u rt_gfx_bitmap_on\n", obj)
            self.assertIn("u rt_gfx_bitmap_off\n", obj)
            self.assertIn("u rt_gfx_mbitmap_on\n", obj)
            self.assertIn("u rt_gfx_mbitmap_off\n", obj)
            self.assertNotIn("u spriteon\n", obj)
            self.assertNotIn("u spritehit\n", obj)
            self.assertNotIn("u spritehitbg\n", obj)
            self.assertNotIn("u spritecolor\n", obj)
            self.assertNotIn("u spritepos\n", obj)
            self.assertNotIn("u spriteptr\n", obj)
            self.assertNotIn("u spritedata\n", obj)
            self.assertNotIn("u setspritemc\n", obj)
            self.assertNotIn("u sidfreq\n", obj)
            self.assertNotIn("u sidpulse\n", obj)
            self.assertNotIn("u sidwave\n", obj)
            self.assertNotIn("u sidad\n", obj)
            self.assertNotIn("u sidsr\n", obj)
            self.assertNotIn("u sidon\n", obj)
            self.assertNotIn("u sidoff\n", obj)
            self.assertNotIn("u sidrst\n", obj)
            self.assertNotIn("u sndrst\n", obj)
            self.assertNotIn("u sidroute\n", obj)
            self.assertNotIn("u sidres\n", obj)
            self.assertNotIn("u sidcutoff\n", obj)
            self.assertNotIn("u sidmode\n", obj)
            self.assertNotIn("u sidvol\n", obj)
            self.assertNotIn("u sidosc3\n", obj)
            self.assertNotIn("u sidenv3\n", obj)
            self.assertNotIn("u vicbank\n", obj)
            self.assertNotIn("u rt_" + "sound\n", obj)
            self.assertNotIn("u sound\n", obj)
            self.assertNotIn("u bgcolor\n", obj)
            self.assertNotIn("u bordercolor\n", obj)
            self.assertNotIn("u screenbase\n", obj)
            self.assertNotIn("u bitmapbase\n", obj)
            self.assertNotIn("u bitmapon\n", obj)
            self.assertNotIn("u bitmapoff\n", obj)
            self.assertNotIn("u mbitmapon\n", obj)
            self.assertNotIn("u mbitmapoff\n", obj)
            self.assertNotIn("u rt_sprite_off\n", obj)

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-input-builtins"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "BYTE JMASK\r"
                "BYTE MMASK\r"
                "BYTE JINIT=[JOY_UP+JOY_BUTTON1+JOY_BUTTON2]\r"
                "BYTE MINIT=[MOUSE_BUTTON1+MOUSE_BUTTON2]\r"
                "PROC MAIN()\r"
                "JMASK=JOY_UP+JOY_BUTTON1+JOY_BUTTON2\r"
                "MMASK=MOUSE_BUTTON1+MOUSE_BUTTON2\r"
                "Joy(2)\r"
                "JoySeen(2)\r"
                "JoyBtn1(2)\r"
                "JoyBtn2(2)\r"
                "MousePoll(1)\r"
                "MouseSeen()\r"
                "MouseX()\r"
                "MouseY()\r"
                "MouseBtn()\r"
                "MouseBtn1()\r"
                "MouseBtn2()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "12000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_joy\n", obj)
            self.assertIn("u rt_jp\n", obj)
            self.assertIn("u rt_jb1\n", obj)
            self.assertIn("u rt_jb2\n", obj)
            self.assertIn("u rt_mp\n", obj)
            self.assertIn("u rt_mseen\n", obj)
            self.assertIn("u rt_mx\n", obj)
            self.assertIn("u rt_my\n", obj)
            self.assertIn("u rt_mb\n", obj)
            self.assertIn("u rt_mb1\n", obj)
            self.assertIn("u rt_mb2\n", obj)
            self.assertIn("i 49\n", obj)
            self.assertIn("i 3\n", obj)
            self.assertIn("v jmask 0\n", obj)
            self.assertIn("v mmask 0\n", obj)
            self.assertIn("v jinit 49\n", obj)
            self.assertIn("v minit 3\n", obj)
            self.assertNotIn("u joy\n", obj)
            self.assertNotIn("u joyseen\n", obj)
            self.assertNotIn("u joybtn1\n", obj)
            self.assertNotIn("u joybtn2\n", obj)
            self.assertNotIn("u mousepoll\n", obj)
            self.assertNotIn("u mouseseen\n", obj)
            self.assertNotIn("u mousex\n", obj)
            self.assertNotIn("u mousey\n", obj)
            self.assertNotIn("u mousebtn\n", obj)
            self.assertNotIn("u mousebtn1\n", obj)
            self.assertNotIn("u mousebtn2\n", obj)

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-no-hardware-builtins"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--max-steps",
                    "6000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            plain_obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            hardware_runtime_modules = sorted(
                path.stem
                for path in (self.root / "src" / "runtime" / "udos_modules").glob("rt_*.obj")
                if path.stem.startswith(("rt_gfx_", "rt_sid_", "rt_sprite_"))
                or path.stem
                in {
                    "rt_joy",
                    "rt_jp",
                    "rt_jb1",
                    "rt_jb2",
                    "rt_js",
                    "rt_mp",
                    "rt_mseen",
                    "rt_mx",
                    "rt_my",
                    "rt_mb",
                    "rt_mb1",
                    "rt_mb2",
                    "rt_ms",
                }
            )
            for module_name in hardware_runtime_modules:
                self.assertNotIn(f"u {module_name}\n", plain_obj)

    def test_actc_preallocation_compile_path_maps_dbf_builtins_to_runtime_objs(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "BYTE HANDLE\r"
            "BYTE FIELDS\r"
            "BYTE FIELDLEN\r"
            "BYTE MOVED\r"
            "BYTE VALUE\r"
            "BYTE FIELDVALUE\r"
            "BYTE FIELDWROTE\r"
            "BYTE WROTE\r"
            "BYTE SAVED\r"
            "BYTE DELOK\r"
            "BYTE UNDELOK\r"
            "BYTE DELETED\r"
            "BYTE HEADERLEN\r"
            "BYTE RECORDLEN\r"
            "BYTE TOTAL\r"
            "BYTE RECNO\r"
            "PROC MAIN()\r"
            "HANDLE=DbfCreate(12288)\r"
            "HANDLE=DbfOpen(12288)\r"
            "FIELDS=DbfFieldCount(HANDLE)\r"
            "FIELDLEN=DbfFieldLen(HANDLE,1)\r"
            "MOVED=DbfGo(HANDLE,2)\r"
            "VALUE=DbfReadByte(HANDLE,1)\r"
            "FIELDVALUE=DbfReadFieldByte(HANDLE,1,0)\r"
            "FIELDWROTE=DbfWriteFieldByte(HANDLE,1,0,90)\r"
            "WROTE=DbfWriteByte(HANDLE,1,90)\r"
            "WROTE=DbfAppend(HANDLE)\r"
            "WROTE=DbfPack(HANDLE)\r"
            "SAVED=DbfSave(HANDLE)\r"
            "DELOK=DbfDelete(HANDLE)\r"
            "UNDELOK=DbfUndelete(HANDLE)\r"
            "DELETED=DbfDeleted(HANDLE)\r"
            "HEADERLEN=DbfHeaderLen(HANDLE)\r"
            "RECORDLEN=DbfRecordLen(HANDLE)\r"
            "TOTAL=DbfTotalRecs(HANDLE)\r"
            "RECNO=DbfCurrRecNo(HANDLE)\r"
            "DbfClose(HANDLE)\r"
            "RETURN\r",
            "actc-overlay-prealloc-dbf-builtins",
        )

        for runtime_import in (
            "rt_dbf_create",
            "rt_dbf_open",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_go",
            "rt_dbf_readbyte",
            "rt_dbf_readfieldbyte",
            "rt_dbf_writefieldbyte",
            "rt_dbf_writebyte",
            "rt_dbf_append",
            "rt_dbf_pack",
            "rt_dbf_save",
            "rt_dbf_delete",
            "rt_dbf_undelete",
            "rt_dbf_deleted",
            "rt_dbf_headerlen",
            "rt_dbf_recordlen",
            "rt_dbf_totalrecs",
            "rt_dbf_currrecno",
            "rt_dbf_close",
        ):
            self.assertIn(f"u {runtime_import}\n", obj)

        for builtin_name in (
            "dbfcreate",
            "dbfopen",
            "dbffieldcount",
            "dbffieldlen",
            "dbfgo",
            "dbfreadbyte",
            "dbfreadfieldbyte",
            "dbfwritefieldbyte",
            "dbfwritebyte",
            "dbfappend",
            "dbfpack",
            "dbfsave",
            "dbfdelete",
            "dbfundelete",
            "dbfdeleted",
            "dbfheaderlen",
            "dbfrecordlen",
            "dbftotalrecs",
            "dbfcurrrecno",
            "dbfclose",
        ):
            self.assertNotIn(f"u {builtin_name}\n", obj)

    def test_actc_preallocation_compile_path_maps_input_results_to_helper_arg_imports(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "BYTE J\r"
            "BYTE P\r"
            "BYTE M\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "P=JoySeen(2)\r"
            "SidVol(J)\r"
            "M=MousePoll(1)\r"
            "BgColor(M)\r"
            "RETURN\r",
            "actc-overlay-prealloc-input-helper-args",
        )

        runtime_imports = (
            "rt_joy",
            "rt_jp",
            "rt_sid_vol",
            "rt_mp",
            "rt_gfx_bgcolor",
        )
        for runtime_import in runtime_imports:
            self.assertIn(f"u {runtime_import}\n", obj)
        for earlier, later in zip(runtime_imports, runtime_imports[1:]):
            self.assertLess(obj.index(f"u {earlier}\n"), obj.index(f"u {later}\n"), msg=obj)

        self.assertIn("i 2\n", obj)
        self.assertIn("i 1\n", obj)
        self.assertIn("v j 0\n", obj)
        self.assertIn("v p 0\n", obj)
        self.assertIn("v m 0\n", obj)
        for builtin_name in ("joy", "joyseen", "sidvol", "mousepoll", "bgcolor"):
            self.assertNotIn(f"u {builtin_name}\n", obj)

    def test_actc_preallocation_compile_path_maps_sid_gfx_sprite_builtins_to_runtime_objs(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "SidVol(10)\r"
            "SidFreq(1,4660)\r"
            "BgColor(6)\r"
            "ScreenCell(5,2,65)\r"
            "SpriteOn(2)\r"
            "SpriteColor(2,5)\r"
            "SpritePos(2,52,86)\r"
            "RETURN\r",
            "actc-overlay-prealloc-sid-gfx-sprite-builtins",
        )

        runtime_imports = (
            "rt_sid_vol",
            "rt_sid_freq",
            "rt_gfx_bgcolor",
            "rt_gfx_screen_cell",
            "rt_sprite_on",
            "rt_sprite_color",
            "rt_sprite_pos",
        )
        for runtime_import in runtime_imports:
            self.assertIn(f"u {runtime_import}\n", obj)
        for earlier, later in zip(runtime_imports, runtime_imports[1:]):
            self.assertLess(obj.index(f"u {earlier}\n"), obj.index(f"u {later}\n"), msg=obj)

        for value in ("i 10\n", "i 1\n", "i 4660\n", "i 6\n", "i 5\n", "i 2\n", "i 65\n", "i 52\n", "i 86\n"):
            self.assertIn(value, obj)
        for builtin_name in (
            "sidvol",
            "sidfreq",
            "bgcolor",
            "screencell",
            "spriteon",
            "spritecolor",
            "spritepos",
        ):
            self.assertNotIn(f"u {builtin_name}\n", obj)

    def test_actc_preallocation_compile_path_maps_zero_arg_runtime_builtins_to_runtime_objs(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "SidRst()\r"
            "SidOsc3()\r"
            "SidEnv3()\r"
            "BitmapOn()\r"
            "BitmapOff()\r"
            "MBitmapOn()\r"
            "MBitmapOff()\r"
            "SpriteHit()\r"
            "SpriteHitBg()\r"
            "MouseSeen()\r"
            "MouseX()\r"
            "MouseY()\r"
            "MouseBtn()\r"
            "RETURN\r",
            "actc-overlay-prealloc-zero-arg-runtime-builtins",
        )

        runtime_imports = (
            "rt_sid_rst",
            "rt_sid_osc3",
            "rt_sid_env3",
            "rt_gfx_bitmap_on",
            "rt_gfx_bitmap_off",
            "rt_gfx_mbitmap_on",
            "rt_gfx_mbitmap_off",
            "rt_sprite_hit",
            "rt_sprite_hit_bg",
            "rt_mseen",
            "rt_mx",
            "rt_my",
            "rt_mb",
        )
        for runtime_import in runtime_imports:
            self.assertIn(f"u {runtime_import}\n", obj)
        for earlier, later in zip(runtime_imports, runtime_imports[1:]):
            self.assertLess(obj.index(f"u {earlier}\n"), obj.index(f"u {later}\n"), msg=obj)

        for builtin_name in (
            "sidrst",
            "sidosc3",
            "sidenv3",
            "bitmapon",
            "bitmapoff",
            "mbitmapon",
            "mbitmapoff",
            "spritehit",
            "spritehitbg",
            "mouseseen",
            "mousex",
            "mousey",
            "mousebtn",
        ):
            self.assertNotIn(f"u {builtin_name}\n", obj)

    def test_actc_preallocation_compile_path_maps_variable_arg_runtime_builtins_to_runtime_objs(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "BYTE VOICE\r"
            "BYTE VOL\r"
            "BYTE SPR\r"
            "BYTE COLOR\r"
            "CARD PTR\r"
            "PROC MAIN()\r"
            "VOICE=1\r"
            "VOL=10\r"
            "SPR=2\r"
            "COLOR=5\r"
            "PTR=8192\r"
            "SidVol(VOL)\r"
            "SidFreq(VOICE,PTR)\r"
            "BgColor(COLOR)\r"
            "ScreenBase(PTR)\r"
            "SpriteOn(SPR)\r"
            "SpriteColor(SPR,COLOR)\r"
            "SpriteData(SPR,PTR)\r"
            "RETURN\r",
            "actc-overlay-prealloc-variable-arg-runtime-builtins",
        )

        runtime_imports = (
            "rt_sid_vol",
            "rt_sid_freq",
            "rt_gfx_bgcolor",
            "rt_gfx_screen_base",
            "rt_sprite_on",
            "rt_sprite_color",
            "rt_sprite_data",
        )
        for runtime_import in runtime_imports:
            self.assertIn(f"u {runtime_import}\n", obj)
        for earlier, later in zip(runtime_imports, runtime_imports[1:]):
            self.assertLess(obj.index(f"u {earlier}\n"), obj.index(f"u {later}\n"), msg=obj)

        for variable_name in ("voice", "vol", "spr", "color", "ptr"):
            self.assertIn(f"v {variable_name} 0\n", obj)
        for builtin_name in (
            "sidvol",
            "sidfreq",
            "bgcolor",
            "screenbase",
            "spriteon",
            "spritecolor",
            "spritedata",
        ):
            self.assertNotIn(f"u {builtin_name}\n", obj)

    def test_actc_preallocation_compile_path_maps_remaining_gfx_builtins_to_runtime_objs(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "VicBank(1)\r"
            "BorderColor(14)\r"
            "BitmapBase(8192)\r"
            "ColorCell(5,2,10)\r"
            "ScreenCopy(12288)\r"
            "ColorCopy(12304)\r"
            "BitmapFill(60)\r"
            "BitmapCopy(20480)\r"
            "RETURN\r",
            "actc-overlay-prealloc-remaining-gfx-builtins",
        )

        runtime_imports = (
            "rt_gfx_vic_bank",
            "rt_gfx_bordercolor",
            "rt_gfx_bitmap_base",
            "rt_gfx_color_cell",
            "rt_gfx_screen_copy",
            "rt_gfx_color_copy",
            "rt_gfx_bitmap_fill",
            "rt_gfx_bitmap_copy",
        )
        for runtime_import in runtime_imports:
            self.assertIn(f"u {runtime_import}\n", obj)
        for earlier, later in zip(runtime_imports, runtime_imports[1:]):
            self.assertLess(obj.index(f"u {earlier}\n"), obj.index(f"u {later}\n"), msg=obj)

        for value in (
            "i 1\n",
            "i 14\n",
            "i 8192\n",
            "i 5\n",
            "i 2\n",
            "i 10\n",
            "i 12288\n",
            "i 12304\n",
            "i 60\n",
            "i 20480\n",
        ):
            self.assertIn(value, obj)
        for builtin_name in (
            "vicbank",
            "bordercolor",
            "bitmapbase",
            "colorcell",
            "screencopy",
            "colorcopy",
            "bitmapfill",
            "bitmapcopy",
        ):
            self.assertNotIn(f"u {builtin_name}\n", obj)

    def test_actc_preallocation_compile_path_maps_remaining_sid_builtins_to_runtime_objs(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "SidPulse(1,52)\r"
            "SidWave(1,64)\r"
            "SidAD(1,151)\r"
            "SidSR(1,248)\r"
            "SidOn(1)\r"
            "SidOff(1)\r"
            "SidRoute(7)\r"
            "SidRes(10)\r"
            "SidCutoff(52)\r"
            "SidMode(48)\r"
            "RETURN\r",
            "actc-overlay-prealloc-remaining-sid-builtins",
        )

        runtime_imports = (
            "rt_sid_pulse",
            "rt_sid_wave",
            "rt_sid_ad",
            "rt_sid_sr",
            "rt_sid_on",
            "rt_sid_off",
            "rt_sid_route",
            "rt_sid_res",
            "rt_sid_cutoff",
            "rt_sid_mode",
        )
        for runtime_import in runtime_imports:
            self.assertIn(f"u {runtime_import}\n", obj)
        for earlier, later in zip(runtime_imports, runtime_imports[1:]):
            self.assertLess(obj.index(f"u {earlier}\n"), obj.index(f"u {later}\n"), msg=obj)

        for value in (
            "i 1\n",
            "i 52\n",
            "i 64\n",
            "i 151\n",
            "i 248\n",
            "i 7\n",
            "i 10\n",
            "i 48\n",
        ):
            self.assertIn(value, obj)
        for builtin_name in (
            "sidpulse",
            "sidwave",
            "sidad",
            "sidsr",
            "sidon",
            "sidoff",
            "sidroute",
            "sidres",
            "sidcutoff",
            "sidmode",
        ):
            self.assertNotIn(f"u {builtin_name}\n", obj)

    def test_actc_preallocation_compile_path_maps_remaining_sprite_builtins_to_runtime_objs(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "SpriteOff(2)\r"
            "SpritePtr(2,128)\r"
            "SpriteMC(2,1)\r"
            "SpriteXExp(2,1)\r"
            "SpriteYExp(2,1)\r"
            "SpritePrio(2,1)\r"
            "SetSpriteMC(5,10)\r"
            "RETURN\r",
            "actc-overlay-prealloc-remaining-sprite-builtins",
        )

        runtime_imports = (
            "rt_sprite_off",
            "rt_sprite_ptr",
            "rt_sprite_mc",
            "rt_sprite_xexp",
            "rt_sprite_yexp",
            "rt_sprite_prio",
            "rt_sprite_set_mc",
        )
        for runtime_import in runtime_imports:
            self.assertIn(f"u {runtime_import}\n", obj)
        for earlier, later in zip(runtime_imports, runtime_imports[1:]):
            self.assertLess(obj.index(f"u {earlier}\n"), obj.index(f"u {later}\n"), msg=obj)

        for value in ("i 2\n", "i 128\n", "i 1\n", "i 5\n", "i 10\n"):
            self.assertIn(value, obj)
        for builtin_name in (
            "spriteoff",
            "spriteptr",
            "spritemc",
            "spritexexp",
            "spriteyexp",
            "spriteprio",
            "setspritemc",
        ):
            self.assertNotIn(f"u {builtin_name}\n", obj)

    def test_actc_compile_path_maps_screen_and_color_cell_builtins_to_runtime_objs(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        build_env = os.environ.copy()
        build_env["ACTC_USE_DECL_OVERLAY"] = "1"
        build_env["ACTC_USE_SOURCE_HEADER_OVERLAY"] = "1"
        build_env["ACTC_USE_LAYOUT_OVERLAY"] = "1"
        build_env["ACTC_USE_IMPORT_OVERLAY"] = "1"
        build_env["ACTC_USE_EMIT_OVERLAY"] = "1"
        build_env["ACTC_USE_BODY_OVERLAY"] = "1"
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")], env=build_env)
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-overlay-screen-color-cell-builtins"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text("ACTION PROJECT\rMAIN.ACT\r", encoding="ascii")
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "ScreenCell(5,2,65)\r"
                "ColorCell(5,2,10)\r"
                "ScreenCopy(12288)\r"
                "ColorCopy(12304)\r"
                "BitmapFill(60)\r"
                "BitmapCopy(20480)\r"
                "RETURN\r",
                encoding="ascii",
            )

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(project_root),
                    "--cmdline",
                    "MAIN",
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "5000000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["exit_status"], 0, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [5], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("u rt_gfx_screen_cell\n", obj)
            self.assertIn("u rt_gfx_color_cell\n", obj)
            self.assertIn("u rt_gfx_screen_copy\n", obj)
            self.assertIn("u rt_gfx_color_copy\n", obj)
            self.assertIn("u rt_gfx_bitmap_fill\n", obj)
            self.assertIn("u rt_gfx_bitmap_copy\n", obj)
            self.assertIn("i 65\n", obj)
            self.assertIn("i 10\n", obj)
            self.assertIn("i 12288\n", obj)
            self.assertIn("i 12304\n", obj)
            self.assertIn("i 60\n", obj)
            self.assertIn("i 20480\n", obj)
            self.assertNotIn("u screencell\n", obj)
            self.assertNotIn("u colorcell\n", obj)
            self.assertNotIn("u screencopy\n", obj)
            self.assertNotIn("u colorcopy\n", obj)
            self.assertNotIn("u bitmapfill\n", obj)
            self.assertNotIn("u bitmapcopy\n", obj)

    def test_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])

        overlay = self.build_dir / "ACTC_OVL5.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], 1)
        self.assertEqual(data[5], 5)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))

    def test_body_collect_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        overlay = self.build_dir / "ACTC_OVL6.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], 1)
        self.assertEqual(data[5], 6)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))

    def test_body_preallocate_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_preallocate.sh")])

        overlay = self.build_dir / "ACTC_OVL7.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], 1)
        self.assertEqual(data[5], 7)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))

    def test_actc_runner_stages_copies_banks_and_calls_noop_overlay(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_noop.sh")])
        overlay_data = (self.build_dir / "ACTC_OVL0.BIN").read_bytes()
        overlay_memcfg_seen_addr = 0xA000 + len(overlay_data) - 1

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "overlay-runner"
            workspace.mkdir()
            shutil.copyfile(self.build_dir / "ACTC_OVL0.BIN", workspace / "ACTC_OVL0.BIN")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(workspace),
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--entry-label",
                    "actc_overlay_run_pass",
                    "--reg-a",
                    "0",
                    "--poke-byte",
                    "0x0001=0x37",
                    "--dump",
                    "0x0001:1",
                    "--dump",
                    "actc_overlay_loaded_len:2",
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--dump",
                    "actc_overlay_service_status:1",
                    "--dump",
                    "actc_overlay_memcfg_before_call:1",
                    "--dump",
                    "actc_overlay_memcfg_after_restore:1",
                    "--dump",
                    f"0x{overlay_memcfg_seen_addr:04X}:1",
                    "--max-steps",
                    "200000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertTrue(summary["exited"], msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["registers"]["a"], 0, msg=result.stdout)
            self.assertEqual(summary["dumps"]["0x0001"], [0x37], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [0], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_context"][0:2], [0, 0], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_service_status"], [1], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_memcfg_before_call"], [0x36], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_memcfg_after_restore"], [0x37], msg=result.stdout)
            self.assertEqual(summary["dumps"][f"0x{overlay_memcfg_seen_addr:04X}"], [0x36], msg=result.stdout)

            loaded_len = summary["dumps"]["actc_overlay_loaded_len"]
            self.assertEqual(loaded_len[0] | (loaded_len[1] << 8), (self.build_dir / "ACTC_OVL0.BIN").stat().st_size)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL0.BIN" and op["params"][2:5] == [0, 0x80, 0] for op in summary["ops"]),
                msg=result.stdout,
            )

    def test_actc_runner_calls_source_header_overlay_with_source_context(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "overlay-source-header"
            workspace.mkdir()
            shutil.copyfile(self.build_dir / "ACTC_OVL1.BIN", workspace / "ACTC_OVL1.BIN")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(workspace),
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--entry-label",
                    "actc_overlay_run_pass",
                    "--reg-a",
                    "1",
                    "--poke-byte",
                    "0x0001=0x37",
                    "--poke-cstr",
                    "module_name=MAIN",
                    "--poke-cstr",
                    "source_buffer=  MODULE MAIN\r",
                    "--poke-word",
                    "source_window_len=14",
                    "--poke-word",
                    "source_total_len=14",
                    "--dump",
                    "0x0001:1",
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--dump",
                    "actc_overlay_memcfg_before_call:1",
                    "--dump",
                    "actc_overlay_memcfg_after_restore:1",
                    "--max-steps",
                    "200000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertTrue(summary["exited"], msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["registers"]["a"], 0, msg=result.stdout)
            self.assertEqual(summary["dumps"]["0x0001"], [0x37], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [1], msg=result.stdout)
            context = summary["dumps"]["actc_overlay_context"]
            self.assertEqual(context[0:2], [1, 0], msg=result.stdout)
            self.assertEqual(context[2:5], [9, 0, 0], msg=result.stdout)
            self.assertEqual(context[5:8], [0, 0, 1], msg=result.stdout)
            self.assertEqual(context[15:20], [14, 0, 14, 0, 0], msg=result.stdout)
            self.assertNotEqual(context[46:48], [0, 0], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_memcfg_before_call"], [0x36], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_memcfg_after_restore"], [0x37], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL1.BIN" and op["params"][2:5] == [0, 0x80, 0] for op in summary["ops"]),
                msg=result.stdout,
            )

    def test_actc_runner_rejects_mismatched_source_header_overlay_module(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "overlay-source-header-bad-module"
            workspace.mkdir()
            shutil.copyfile(self.build_dir / "ACTC_OVL1.BIN", workspace / "ACTC_OVL1.BIN")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(workspace),
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--entry-label",
                    "actc_overlay_run_pass",
                    "--reg-a",
                    "1",
                    "--poke-byte",
                    "0x0001=0x37",
                    "--poke-cstr",
                    "module_name=MAIN",
                    "--poke-cstr",
                    "source_buffer=MODULE OTHER\r",
                    "--poke-word",
                    "source_window_len=13",
                    "--poke-word",
                    "source_total_len=13",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "200000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertTrue(summary["exited"], msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["registers"]["a"], 2, msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_context"][0:2], [1, 2], msg=result.stdout)
            self.assertNotEqual(summary["dumps"]["actc_overlay_context"][11:13], [0, 0], msg=result.stdout)

    def test_actc_runner_calls_decl_counts_overlay_with_source_context(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])

        source = "MODULE MAIN\rINT A=(8/2)+1+2*3\rBYTE B=[((1<2 AND 2<3) OR NOT(0=1))+1]\rREAL R\rPROC MAIN(P,Q)\rINT L=[P+1]\rREAL Z\rRETURN\rPROC HELP()\rBYTE H\rRETURN\r"
        source_len = len(source)

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "overlay-decl-counts"
            workspace.mkdir()
            shutil.copyfile(self.build_dir / "ACTC_OVL2.BIN", workspace / "ACTC_OVL2.BIN")

            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(workspace),
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--entry-label",
                    "actc_overlay_run_pass",
                    "--reg-a",
                    "2",
                    "--poke-byte",
                    "0x0001=0x37",
                    "--poke-cstr",
                    f"source_buffer={source}",
                    "--poke-word",
                    f"source_window_len={source_len}",
                    "--poke-word",
                    f"source_total_len={source_len}",
                    "--dump",
                    "0x0001:1",
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--dump",
                    "actc_overlay_memcfg_before_call:1",
                    "--dump",
                    "actc_overlay_memcfg_after_restore:1",
                    "--dump",
                    "var_count_data:1",
                    "--dump",
                    "module_var_count_data:1",
                    "--dump",
                    "export_count_data:1",
                    "--max-steps",
                    "350000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertTrue(summary["exited"], msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["registers"]["a"], 0, msg=result.stdout)
            self.assertEqual(summary["dumps"]["0x0001"], [0x37], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [2], msg=result.stdout)
            context = summary["dumps"]["actc_overlay_context"]
            self.assertEqual(context[0:2], [2, 0], msg=result.stdout)
            self.assertEqual(context[2:5], [source_len & 0xFF, source_len >> 8, 0], msg=result.stdout)
            self.assertEqual(context[5:8], [0, 0, 1], msg=result.stdout)
            self.assertEqual(context[15:20], [source_len & 0xFF, source_len >> 8, source_len & 0xFF, source_len >> 8, 0], msg=result.stdout)
            self.assertEqual(context[20:22], [3, 2], msg=result.stdout)
            self.assertNotEqual(context[22:28], [0, 0, 0, 0, 0, 0], msg=result.stdout)
            self.assertNotEqual(context[28:36], [0, 0, 0, 0, 0, 0, 0, 0], msg=result.stdout)
            self.assertNotEqual(context[36:44], [0, 0, 0, 0, 0, 0, 0, 0], msg=result.stdout)
            self.assertEqual(summary["dumps"]["var_count_data"], [8], msg=result.stdout)
            self.assertEqual(summary["dumps"]["module_var_count_data"], [3], msg=result.stdout)
            self.assertEqual(summary["dumps"]["export_count_data"], [2], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_memcfg_before_call"], [0x36], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_memcfg_after_restore"], [0x37], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL2.BIN" and op["params"][2:5] == [0, 0x80, 0] for op in summary["ops"]),
                msg=result.stdout,
            )
            var_name_writes = [
                op for op in summary["ops"]
                if op["kind"] == "rwr" and op["params"][0:3] in ([0, 0xE4, 0], [25, 0xE4, 0], [50, 0xE4, 0], [75, 0xE4, 0], [100, 0xE4, 0], [125, 0xE4, 0], [150, 0xE4, 0], [175, 0xE4, 0])
            ]
            var_meta_writes = [
                op for op in summary["ops"]
                if op["kind"] == "rwr" and op["params"][0:3] in ([0, 0xE9, 0], [4, 0xE9, 0], [8, 0xE9, 0], [12, 0xE9, 0], [16, 0xE9, 0], [20, 0xE9, 0], [24, 0xE9, 0], [28, 0xE9, 0])
            ]
            export_name_writes = [
                op for op in summary["ops"]
                if op["kind"] == "rwr" and op["params"][0:3] in ([0, 0xE6, 0], [25, 0xE6, 0])
            ]
            proc_meta_writes = [
                op for op in summary["ops"]
                if op["kind"] == "rwr" and op["params"][0:3] in ([0, 0xEA, 0], [4, 0xEA, 0])
            ]
            self.assertEqual([op["head"][0:2] for op in var_name_writes], [[ord("A"), 0], [ord("B"), 0], [ord("R"), 0], [ord("P"), 0], [ord("Q"), 0], [ord("L"), 0], [ord("Z"), 0], [ord("H"), 0]], msg=result.stdout)
            self.assertEqual([op["head"][0:4] for op in var_meta_writes], [[11, 0, 2, ord("i")], [2, 0, 2, ord("b")], [0, 0, 4, ord("r")], [0, 0, 2, ord("i")], [0, 0, 2, ord("i")], [0, 0, 2, ord("i")], [0, 0, 4, ord("r")], [0, 0, 2, ord("b")]], msg=result.stdout)
            self.assertEqual(
                [bytes(op["head"][0:5]).rstrip(b"\x00").decode("ascii") for op in export_name_writes],
                ["MAIN", "HELP"],
                msg=result.stdout,
            )
            self.assertEqual(
                [op["head"][0:4] for op in proc_meta_writes],
                [[2, 3, 0, 5], [2, 3, 1, 5], [2, 3, 2, 5], [0, 7, 0, 7], [0, 7, 1, 7]],
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rrd" and op["params"][0:3] == [0, 0x80, 0] and op["params"][3:5] == [0, 0xA0] for op in summary["ops"]),
                msg=result.stdout,
            )

    def test_actc_runner_rejects_bad_decl_counts_overlay_sources(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])

        bad_sources = {
            "duplicate_module_var": "MODULE MAIN\rINT A\rBYTE A\rPROC MAIN()\rRETURN\r",
            "duplicate_proc_export": "MODULE MAIN\rPROC MAIN()\rRETURN\rPROC MAIN()\rRETURN\r",
            "duplicate_proc_param": "MODULE MAIN\rPROC MAIN(P,P)\rRETURN\r",
            "param_shadows_module": "MODULE MAIN\rINT A\rPROC MAIN(A)\rRETURN\r",
            "local_duplicates_param": "MODULE MAIN\rPROC MAIN(P)\rINT P\rRETURN\r",
            "duplicate_proc_local": "MODULE MAIN\rPROC MAIN()\rINT L\rBYTE L\rRETURN\r",
            "bad_module_var_name": "MODULE MAIN\rINT 1A\rPROC MAIN()\rRETURN\r",
            "bad_proc_tail": "MODULE MAIN\rPROC MAIN BAD\rRETURN\r",
            "empty_initializer": "MODULE MAIN\rINT A=\rPROC MAIN()\rRETURN\r",
            "unclosed_initializer": "MODULE MAIN\rINT A=[1\rPROC MAIN()\rRETURN\r",
            "trailing_operator_initializer": "MODULE MAIN\rINT A=[1+]\rPROC MAIN()\rRETURN\r",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "overlay-decl-rejects"
            workspace.mkdir()
            shutil.copyfile(self.build_dir / "ACTC_OVL2.BIN", workspace / "ACTC_OVL2.BIN")

            for name, source in bad_sources.items():
                with self.subTest(name=name):
                    source_len = len(source)
                    result = self.run_checked(
                        [
                            str(self.build_dir / "tool_abi_harness"),
                            "--prg",
                            str(self.build_dir / "ACTC.PRG"),
                            "--workspace",
                            str(workspace),
                            "--services-inc",
                            str(self.build_dir / "udos_services.inc"),
                            "--labels",
                            str(self.build_dir / "actc.current.labels"),
                            "--entry-label",
                            "actc_overlay_run_pass",
                            "--reg-a",
                            "2",
                            "--poke-byte",
                            "0x0001=0x37",
                            "--poke-cstr",
                            f"source_buffer={source}",
                            "--poke-word",
                            f"source_window_len={source_len}",
                            "--poke-word",
                            f"source_total_len={source_len}",
                            "--dump",
                            f"actc_overlay_context:{self.CTX_SIZE}",
                            "--max-steps",
                            "350000",
                        ]
                    )

                    summary = json.loads(result.stdout)
                    self.assertTrue(summary["exited"], msg=result.stdout)
                    self.assertFalse(summary["hit_limit"], msg=result.stdout)
                    self.assertEqual(summary["registers"]["a"], 2, msg=result.stdout)
                    self.assertEqual(summary["dumps"]["actc_overlay_context"][0:2], [2, 2], msg=result.stdout)

    def test_actc_runner_rejects_unknown_overlay_pass_id(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "overlay-runner"
            workspace.mkdir()
            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(self.build_dir / "ACTC.PRG"),
                    "--workspace",
                    str(workspace),
                    "--services-inc",
                    str(self.build_dir / "udos_services.inc"),
                    "--labels",
                    str(self.build_dir / "actc.current.labels"),
                    "--entry-label",
                    "actc_overlay_run_pass",
                    "--reg-a",
                    "127",
                    "--dump",
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--max-steps",
                    "200000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertTrue(summary["exited"], msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["registers"]["a"], 1, msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [127], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_context"][0:2], [127, 2], msg=result.stdout)
            self.assertFalse(summary["ops"], msg=result.stdout)


if __name__ == "__main__":
    unittest.main()
