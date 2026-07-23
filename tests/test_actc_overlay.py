from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest


class TestActcOverlay(unittest.TestCase):
    ACTC_OVERLAY_ABI_VERSION = 5
    CTX_SIZE = 231
    ACTC_BODY_OVERLAY_MIN_HEADROOM = 0x60
    ACTC_DECL_OVERLAY_MIN_HEADROOM = 0x40
    ACTC_EMIT_OVERLAY_MIN_HEADROOM = 0x800
    ACTC_NATIVE_REAL_EMIT_MIN_HEADROOM = 0x300
    ACTC_NATIVE_INTEGER_EMIT_MIN_HEADROOM = 0x400
    ACTC_NATIVE_LOCAL_EMIT_MIN_HEADROOM = 0x80
    ACTC_NATIVE_LOCAL_RUNTIME_EMIT_MIN_HEADROOM = 0x200
    ACTC_NATIVE_LOCAL_MIXED_EMIT_MIN_HEADROOM = 0x80
    ACTC_NATIVE_FIXED_EMIT_MIN_HEADROOM = 0x100
    ACTC_NATIVE_RUNTIME_NESTED_EMIT_MIN_HEADROOM = 0x4F0
    ACTC_NATIVE_REAL_FUNCTION_EMIT_MIN_HEADROOM = 0x800
    ACTC_NATIVE_REAL_POSTFIX_EMIT_MIN_HEADROOM = 0x800
    ACTC_NATIVE_REAL_POSTFIX_CONTROL_EMIT_MIN_HEADROOM = 0x400
    ACTC_NATIVE_REAL_POSTFIX_MULTI_CONTROL_EMIT_MIN_HEADROOM = 0x400
    ACTC_NATIVE_REAL_POSTFIX_EXTENDED_CONTROL_EMIT_MIN_HEADROOM = 0x400
    ACTC_NATIVE_REAL_POSTFIX_EARLY_RETURN_EMIT_MIN_HEADROOM = 0x400
    ACTC_NATIVE_REAL_POSTFIX_LOOP_EMIT_MIN_HEADROOM = 0x400
    ACTC_NATIVE_REAL_POSTFIX_LOOP_EXIT_EMIT_MIN_HEADROOM = 0x300
    ACTC_NATIVE_REAL_POSTFIX_FOR_EMIT_MIN_HEADROOM = 0x100
    ACTC_NATIVE_REAL_POSTFIX_FOR_DYNAMIC_EMIT_MIN_HEADROOM = 0x20
    ACTC_NATIVE_REAL_POSTFIX_LITERAL_EMIT_MIN_HEADROOM = 0x280
    ACTC_OVERLAY_WINDOW_SIZE = 0x2000
    ACTC_PREPROCESS_CODE_WINDOW_SIZE = 0x2000

    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.build_dir = self.root / "build" / "udos_tools"

    def require_toolchain(self) -> None:
        for tool in ("ca65", "ld65"):
            if shutil.which(tool) is None:
                self.skipTest(f"{tool} not found")

    def test_real_inclusive_relations_reject_unordered_compare_result(self) -> None:
        runtime_root = self.root / "src" / "tools_udos" / "actc"
        for filename, prefix in (
            ("actc_overlay_emit_native_real_control.inc", "native_real_control"),
            ("actc_overlay_emit_native_real_while.inc", "native_real_while"),
        ):
            text = (runtime_root / filename).read_text(encoding="ascii")
            with self.subTest(filename=filename):
                self.assertIn(
                    f"{prefix}_map_ge:\n    lda #$02\n    ldx #$B0",
                    text,
                )
                self.assertIn(
                    f"{prefix}_map_le:\n    lda #$01\n    ldx #$10",
                    text,
                )

    def overlay_context_offset(self, field: str) -> int:
        abi_text = (
            self.root / "src" / "tools_udos" / "actc" / "actc_overlay_abi.inc"
        ).read_text(encoding="ascii")
        match = re.search(
            rf"^ACTC_OVERLAY_CTX_{re.escape(field)} = ([0-9]+)$",
            abi_text,
            flags=re.MULTILINE,
        )
        if match is None:
            self.fail(f"missing overlay context field: {field}")
        return int(match.group(1))

    def test_overlay_context_abi_is_compact(self) -> None:
        abi_text = (
            self.root / "src" / "tools_udos" / "actc" / "actc_overlay_abi.inc"
        ).read_text(encoding="ascii")
        actc_text = (
            self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        ).read_text(encoding="ascii")
        definitions = re.findall(
            r"^(ACTC_OVERLAY_CTX_[A-Z0-9_]+) = ([0-9]+)$",
            abi_text,
            flags=re.MULTILINE,
        )
        offsets = [int(value) for name, value in definitions if name != "ACTC_OVERLAY_CTX_SIZE"]
        self.assertEqual(offsets, list(range(self.CTX_SIZE)))
        self.assertIn(f"ACTC_OVERLAY_CTX_SIZE = {self.CTX_SIZE}", abi_text)

        retired_fields = (
            "INPUT_BASE",
            "OUTPUT_BASE",
            "SCAN_PTR_SLOT_PTR",
            "POP_LOOP_KIND_FN",
            "STORE_RUNTIME_UNTIL_FN",
            "PUSH_WHILE_FN",
            "PUSH_DO_FN",
            "STORE_RUNTIME_CONDITION_FN",
            "STORE_RUNTIME_EXPR_FN",
            "STORE_RUNTIME_WHILE_FN",
            "STORE_RUNTIME_PRINTIE_FN",
            "STORE_RUNTIME_PRINTI_FN",
            "PARSE_SMALL_VALUE_EXPR_FN",
        )
        for field in retired_fields:
            symbol = f"ACTC_OVERLAY_CTX_{field}"
            self.assertNotIn(symbol, abi_text)
            self.assertNotIn(symbol, actc_text)

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
        builtin_runtime_table_text = (
            self.root / "src" / "tools_udos" / "actc" / "actc_overlay_builtin_runtime_table.inc"
        ).read_text(encoding="ascii")
        overlay_abi_text = (
            self.root / "src" / "tools_udos" / "actc" / "actc_overlay_abi.inc"
        ).read_text(encoding="ascii")
        self.assertIn(".if ACTC_KEEP_BODY_RESIDENT_FALLBACK\nbuiltin_runtime_import_table:", actc_text)
        self.assertNotIn("set_resident_builtin_runtime_table_context:", actc_text)
        self.assertIn("find_or_store_builtin_runtime_external_from_table_ay:", actc_text)
        self.assertIn("find_or_store_prefixed_rt_external_from_ay:", actc_text)
        shared_table_include = '.include "actc_overlay_builtin_runtime_table.inc"'
        self.assertIn(shared_table_include, body_overlay_text)
        self.assertIn(shared_table_include, body_preallocate_overlay_text)
        self.assertIn("publish_builtin_runtime_table:", body_overlay_text)
        self.assertIn("publish_builtin_runtime_table:", body_preallocate_overlay_text)
        self.assertIn("ACTC_OVERLAY_CTX_BUILTIN_RUNTIME_TABLE_PTR_LO", body_overlay_text)
        self.assertIn("ACTC_OVERLAY_CTX_BUILTIN_RUNTIME_TABLE_PTR_LO", body_preallocate_overlay_text)
        self.assertIn(
            ".macro builtin_runtime_row arity, prefix_len, builtin_suffix, runtime_suffix",
            builtin_runtime_table_text,
        )
        self.assertIn(
            ".byte ((prefix_len << 3) | arity)",
            builtin_runtime_table_text,
        )
        self.assertIn(
            ".macro builtin_runtime_row_xy arity, prefix_len, builtin_suffix, runtime_suffix",
            builtin_runtime_table_text,
        )
        self.assertIn(
            ".byte ($80 | (prefix_len << 3) | arity)",
            builtin_runtime_table_text,
        )
        self.assertIn("builtin_runtime_import_table:", builtin_runtime_table_text)
        self.assertIn(
            'builtin_runtime_row $02, 0, "SIDFREQ", "SID_FREQ"',
            builtin_runtime_table_text,
        )
        self.assertIn(
            'builtin_runtime_row $01, 6, "2", "JB2"',
            builtin_runtime_table_text,
        )
        for row in (
            'builtin_runtime_row_xy $01, 3, "CUTOFF", "SID_CUTOFF"',
            'builtin_runtime_row_xy $01, 0, "SCREENBASE", "GFX_SCREEN_BASE"',
            'builtin_runtime_row_xy $01, 0, "BITMAPBASE", "GFX_BITMAP_BASE"',
            'builtin_runtime_row_xy $01, 0, "SCREENCOPY", "GFX_SCREEN_COPY"',
            'builtin_runtime_row_xy $01, 0, "COLORCOPY", "GFX_COLOR_COPY"',
            'builtin_runtime_row_xy $01, 6, "COPY", "GFX_BITMAP_COPY"',
            'builtin_runtime_row_xy $01, 0, "DBFCREATE", "DBF_CREATE"',
            'builtin_runtime_row_xy $01, 3, "OPEN", "DBF_OPEN"',
        ):
            self.assertIn(row, builtin_runtime_table_text)
        self.assertIn(
            'builtin_runtime_row $04, 3, "WRITEFIELDBYTE", "DBF_WRITEFIELDBYTE"',
            builtin_runtime_table_text,
        )
        self.assertTrue(builtin_runtime_table_text.rstrip().endswith(".byte $FF"))
        self.assertNotIn('"RT_SID_FREQ"', builtin_runtime_table_text)
        self.assertIn("ACTC_OVERLAY_PASS_BODY_PREALLOCATE", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_OBJECT", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_BODY_PREALLOCATE", actc_text)
        self.assertIn('.asciiz "!ACTC_OVL0.BIN"', actc_text)
        self.assertIn("cmp #ACTC_OVERLAY_PASS_COUNT", actc_text)
        self.assertIn("sta actc_overlay_path+9", actc_text)
        self.assertNotIn("actc_overlay_pass_table:", actc_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_LOCAL_OBJECT", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_OBJECT = $0A", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_CONTROL_OBJECT = $0B", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_WHILE_OBJECT = $0C", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_RUNTIME_CONDITION_OBJECT = $0D", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_RUNTIME_SEQUENCE_OBJECT = $0E", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_RUNTIME_NESTED_OBJECT = $0F", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_LOCAL_RUNTIME_OBJECT = $10", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_LOCAL_MIXED_OBJECT = $11", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_PREPROCESS = $12", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_FIXED_OBJECT = $13", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_FUNCTION_OBJECT = $14", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_OBJECT = $15", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_CONTROL_OBJECT = $16", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_MULTI_CONTROL_OBJECT = $17", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_EXTENDED_CONTROL_OBJECT = $18", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_EARLY_RETURN_OBJECT = $19", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_LOOP_OBJECT = $1A", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_LOOP_EXIT_OBJECT = $1B", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_FOR_OBJECT = $1C", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_FOR_DYNAMIC_OBJECT = $1D", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_LITERAL_OBJECT = $1E", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_PASS_COUNT = $1F", overlay_abi_text)
        self.assertIn("ldx #$14\nbuild_object_content_with_overlay_candidate_loop:", actc_text)
        self.assertIn("cmp #10\n    bcc :+", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_OBJECT", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_WHILE_OBJECT", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_RUNTIME_CONDITION_OBJECT", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_RUNTIME_NESTED_OBJECT", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_RUNTIME_SEQUENCE_OBJECT", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_LOCAL_RUNTIME_OBJECT", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_LOCAL_MIXED_OBJECT", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_OBJECT", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_CONTROL_OBJECT", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_MULTI_CONTROL_OBJECT", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_EXTENDED_CONTROL_OBJECT", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_EARLY_RETURN_OBJECT", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_LOOP_OBJECT", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_LOOP_EXIT_OBJECT", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_FOR_OBJECT", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_FOR_DYNAMIC_OBJECT", actc_text)
        self.assertIn(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_LITERAL_OBJECT", actc_text)
        self.assertLess(
            actc_text.index(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_EXTENDED_CONTROL_OBJECT"),
            actc_text.index(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_FOR_OBJECT"),
        )
        self.assertLess(
            actc_text.index(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_LOOP_OBJECT"),
            actc_text.index(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_LOOP_EXIT_OBJECT"),
        )
        self.assertLess(
            actc_text.index(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_LOOP_EXIT_OBJECT"),
            actc_text.index(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_EARLY_RETURN_OBJECT"),
        )
        self.assertLess(
            actc_text.index(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_EARLY_RETURN_OBJECT"),
            actc_text.index(".byte ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_FUNCTION_OBJECT"),
        )
        self.assertIn("ACTC_OVERLAY_STATUS_NOT_APPLICABLE", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_CTX_BODY_TABLE_ONLY = 200", overlay_abi_text)
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
        self.assertIn(
            f"ACTC_OVERLAY_ABI_VERSION = {self.ACTC_OVERLAY_ABI_VERSION}",
            overlay_abi_text,
        )
        self.assertIn("ACTC_OVERLAY_CTX_SOURCE_READER_CONSUME_TOKEN_FN_LO = 205", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_CTX_SOURCE_READER_TOKEN_VALUE_PTR_LO = 207", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_CTX_EVAL_REAL_CONST_FN_LO = 229", overlay_abi_text)
        self.assertIn("ACTC_OVERLAY_CTX_EVAL_REAL_CONST_FN_HI = 230", overlay_abi_text)
        self.assertIn(
            "sta actc_overlay_context+ACTC_OVERLAY_CTX_EVAL_REAL_CONST_FN_LO",
            actc_text,
        )
        self.assertIn(f"ACTC_OVERLAY_CTX_SIZE = {self.CTX_SIZE}", overlay_abi_text)
        self.assertIn("load_body_overlay_builtin_runtime_table:", actc_text)
        self.assertIn(
            "sta actc_overlay_context+ACTC_OVERLAY_CTX_BODY_MODE",
            actc_text,
        )
        self.assertIn("ACTC_OVERLAY_CTX_SYMBOL_BUFFER_MATCHES_CONST_PTR_FN_LO", actc_text)
        self.assertIn(
            "sta actc_overlay_context+ACTC_OVERLAY_CTX_SOURCE_READER_PEEK_TOKEN_FN_LO",
            actc_text,
        )
        self.assertIn(
            "sta actc_overlay_context+ACTC_OVERLAY_CTX_SOURCE_READER_CONSUME_TOKEN_FN_LO",
            actc_text,
        )
        self.assertIn(
            "sta actc_overlay_context+ACTC_OVERLAY_CTX_SOURCE_READER_TOKEN_VALUE_PTR_LO",
            actc_text,
        )
        self.assertIn('.include "actc_overlay_positive_word.inc"', body_overlay_text)
        self.assertIn('.include "actc_overlay_positive_word.inc"', body_preallocate_overlay_text)
        self.assertIn("ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_F_CMP_FN_LO", actc_text)
        self.assertIn("preallocate_body_externals_with_overlay:", actc_text)
        self.assertIn("ACTC_OVERLAY_BODY_MODE_PREALLOCATE_EXTERNALS", actc_text)
        self.assertIn(
            "    jmp resolve_unresolved_external_call_target_from_declared_or_fail\n"
            "resolve_call_target_from_declared_or_fail_fixed:",
            actc_text,
        )
        self.assertIn(
            "    sta call_target_kind\n"
            "    clc\n"
            "    rts\n"
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
            "    jsr source_reader_match_open_paren_from_scan_y\n"
            "    bcs preallocate_int_print_statement_call_external_miss_restore\n"
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
            "    jsr source_reader_match_open_paren_from_scan_y\n"
            "    bcs preallocate_call_with_arg_externals_fail\n"
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
            "    lda #$00\n"
            "    sta real_expression_depth_local\n"
            "; Bound recursive operand collection independently of the source-reader window.\n"
            "emit_runtime_real_value_nested_local_or_fail:",
            body_overlay_text,
        )
        self.assertIn(
            "emit_runtime_real_value_worker_local_or_fail:\n"
            "    jsr try_consume_real_open_local\n"
            "    bcs emit_runtime_real_value_local_try_fabs\n"
            "    jmp emit_runtime_real_explicit_value_after_open_local_or_fail",
            body_overlay_text,
        )
        self.assertIn(
            "preallocate_real_value_nested_external_from_scan_y_overlay:",
            body_preallocate_overlay_text,
        )
        self.assertIn(
            "preallocate_real_value_worker_external_from_scan_y_overlay:",
            body_preallocate_overlay_text,
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
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_preprocess.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_preallocate.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_runtime_imports.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_native_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_native_local_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_native_real_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_native_real_control_object.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_native_real_while_object.sh")])
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_runtime_condition_object.sh")]
        )
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_runtime_sequence_object.sh")]
        )
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_runtime_nested_object.sh")]
        )
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_local_runtime_object.sh")]
        )
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_local_mixed_object.sh")]
        )
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_fixed_object.sh")]
        )
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_real_postfix_object.sh")]
        )
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_real_postfix_control_object.sh")]
        )
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_real_postfix_multi_control_object.sh")]
        )
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_real_postfix_extended_control_object.sh")]
        )
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_real_postfix_early_return_object.sh")]
        )
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_real_postfix_loop_object.sh")]
        )
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_real_postfix_loop_exit_object.sh")]
        )
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_real_postfix_for_object.sh")]
        )
        self.run_checked(
            [
                str(
                    self.root
                    / "tools"
                    / "build_actc_overlay_emit_native_real_postfix_for_dynamic_object.sh"
                )
            ]
        )
        self.run_checked(
            [
                str(
                    self.root
                    / "tools"
                    / "build_actc_overlay_emit_native_real_postfix_literal_object.sh"
                )
            ]
        )

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

    def assert_emit_overlay_map_keeps_headroom(
        self,
        map_name: str,
        overlay_name: str,
        minimum_headroom: int | None = None,
    ) -> None:
        map_text = (self.build_dir / map_name).read_text(encoding="ascii")
        match = re.search(r"^CODE\s+[0-9A-Fa-f]{6}\s+[0-9A-Fa-f]{6}\s+([0-9A-Fa-f]{6})\s+", map_text, re.MULTILINE)
        self.assertIsNotNone(match, msg=map_text)
        assert match is not None
        headroom = self.ACTC_OVERLAY_WINDOW_SIZE - int(match.group(1), 16)
        required = self.ACTC_EMIT_OVERLAY_MIN_HEADROOM if minimum_headroom is None else minimum_headroom
        self.assertGreaterEqual(
            headroom,
            required,
            msg=f"{overlay_name} has only {headroom} bytes free for native object-emission growth\n{map_text}",
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
        additional_sources: dict[str, str] | None = None,
        additional_library_sources: dict[str, str] | None = None,
        expected_exit_status: int = 0,
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
            for relative, contents in (additional_sources or {}).items():
                path = source_dir / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(contents, encoding="ascii")
            if additional_library_sources:
                library_dir = project_root / "lib"
                library_dir.mkdir()
                for relative, contents in additional_library_sources.items():
                    path = library_dir / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(contents, encoding="ascii")

            command = [
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
            result = subprocess.run(
                command,
                cwd=self.root,
                text=True,
                capture_output=True,
                check=False,
                timeout=60,
            )
            self.assertEqual(
                result.returncode,
                expected_exit_status,
                msg=result.stdout + result.stderr,
            )

            summary = json.loads(result.stdout)
            self.last_overlay_ops = summary["ops"]
            self.assertEqual(summary["exit_status"], expected_exit_status, msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            if expected_exit_status != 0:
                return summary["console"]
            self.last_emit_overlay_pass = summary["dumps"]["actc_overlay_requested_pass"]
            self.assertIn(
                self.last_emit_overlay_pass,
                ([5], [8], [9], [10], [11], [12], [13], [14], [15], [16], [17], [19], [20], [21], [22], [23], [24], [25], [26], [27], [28], [29], [30]),
                msg=result.stdout,
            )
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

    def test_asmblock_opcode_table_covers_official_nmos_6502(self) -> None:
        table_text = (
            self.root / "src" / "tools_udos" / "actc" / "actc_asmblock_6502.inc"
        ).read_text(encoding="ascii")
        rows = re.findall(
            r'^\s*\.byte "([A-Z]{3})",(ACTC_ASM_MODE_[A-Z_]+),\$([0-9A-F]{2})$',
            table_text,
            flags=re.MULTILINE,
        )
        expected_opcodes = set(
            bytes.fromhex(
                "00 01 05 06 08 09 0A 0D 0E "
                "10 11 15 16 18 19 1D 1E "
                "20 21 24 25 26 28 29 2A 2C 2D 2E "
                "30 31 35 36 38 39 3D 3E "
                "40 41 45 46 48 49 4A 4C 4D 4E "
                "50 51 55 56 58 59 5D 5E "
                "60 61 65 66 68 69 6A 6C 6D 6E "
                "70 71 75 76 78 79 7D 7E "
                "81 84 85 86 88 8A 8C 8D 8E "
                "90 91 94 95 96 98 99 9A 9D "
                "A0 A1 A2 A4 A5 A6 A8 A9 AA AC AD AE "
                "B0 B1 B4 B5 B6 B8 B9 BA BC BD BE "
                "C0 C1 C4 C5 C6 C8 C9 CA CC CD CE "
                "D0 D1 D5 D6 D8 D9 DD DE "
                "E0 E1 E4 E5 E6 E8 E9 EA EC ED EE "
                "F0 F1 F5 F6 F8 F9 FD FE"
            )
        )
        opcodes = [int(opcode, 16) for _mnemonic, _mode, opcode in rows]

        self.assertEqual(len(rows), 151)
        self.assertEqual(set(opcodes), expected_opcodes)
        self.assertEqual(len(opcodes), len(set(opcodes)))
        self.assertEqual(
            len(rows),
            len({(mnemonic, mode) for mnemonic, mode, _opcode in rows}),
        )
        self.assertTrue(table_text.rstrip().endswith(".byte $00"))

    def test_asmblock_workspace_stays_outside_overlay_code(self) -> None:
        layout_text = (
            self.root / "src" / "tools_udos" / "actc" / "actc_asmblock_layout.inc"
        ).read_text(encoding="ascii")

        self.assertIn("ACTC_ASMBLOCK_PAGE_BUFFER = ACTC_OVERLAY_WORKSPACE_BASE", layout_text)
        self.assertIn(
            "ACTC_ASMBLOCK_LABEL_INDEX_BASE = ACTC_ASMBLOCK_PAGE_BUFFER + $0100",
            layout_text,
        )
        self.assertIn(
            "ACTC_ASMBLOCK_PASS9_SCRATCH = ACTC_ASMBLOCK_LABEL_INDEX_BASE + $0010",
            layout_text,
        )
        self.assertNotIn("ACTC_ASMBLOCK_OFFSET_LO", layout_text)
        self.assertNotIn("ACTC_ASMBLOCK_OFFSET_HI", layout_text)

    def test_asmblock_emits_all_addressing_mode_forms(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "ASMBLOCK [\r"
            "START:\r"
            "NOP ; PRINT( must remain opaque\r"
            "ASL A\r"
            "LDA #$7F\r"
            "LDA $10\r"
            "LDA $10,X\r"
            "LDX $10,Y\r"
            "LDA $1234\r"
            "LDA $1234,X\r"
            "LDA $1234,Y\r"
            "JMP ($1234)\r"
            "LDA ($10,X)\r"
            "LDA ($10),Y\r"
            "BNE START\r"
            "]\r"
            "RETURN\r",
            "actc-overlay-asmblock-addressing-modes",
        )

        self.assertIn(
            "m EA 0A A9 7F A5 10 B5 10 B6 10 AD 34 12 BD 34 12 "
            "B9 34 12 6C 34 12 A1 10 B1 10 D0 E4",
            obj,
        )
        self.assertIn("k 0\n", obj)
        self.assertNotIn("u jmp\n", obj)
        self.assertNotIn("u lda\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_shipped_asmblock_demo_compiles_with_native_actc(self) -> None:
        source = (self.root / "examples" / "asmblock_demo.act").read_text(
            encoding="ascii"
        )
        source = source.replace("MODULE ASMBLOCK_DEMO", "MODULE MAIN", 1)
        source = source.replace("\r\n", "\n").replace("\n", "\r")

        obj = self.compile_overlay_object(source, "native-asmblock-demo")

        self.assertIn("A9 15 0A 8D 00 00 AD 00 00 8D 00 04", obj)
        self.assertRegex(obj, r"r \d+ x __v0\n")
        self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_fixed_register_machine_routines_emit_native_call_abi(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "BYTE BRESULT\r"
            "CARD WRESULT\r"
            "BYTE FOURRESULT\r"
            "BYTE FUNC SEVEN=*()\r"
            "ASMBLOCK [\r"
            "LDA #7\r"
            "RTS\r"
            "]\r"
            "CARD FUNC PAIR=*(BYTE PLO,BYTE PHI)\r"
            "ASMBLOCK [\r"
            "RTS\r"
            "]\r"
            "BYTE FUNC FOUR=*(BYTE P0,BYTE P1,BYTE P2,BYTE P3)\r"
            "ASMBLOCK [\r"
            "LDA $A3\r"
            "RTS\r"
            "]\r"
            "PROC CAPTURE=*(BYTE FIRST,CARD WORDVAL,BYTE LAST)\r"
            "ASMBLOCK [\r"
            "STA $0340\r"
            "STX $0341\r"
            "STY $0342\r"
            "LDA $A3\r"
            "STA $0343\r"
            "RTS\r"
            "]\r"
            "PROC MAIN()\r"
            "BRESULT=SEVEN()\r"
            "WRESULT=PAIR(52,18)\r"
            "FOURRESULT=FOUR(1,2,3,77)\r"
            "CAPTURE(11,4660,44)\r"
            "RETURN\r",
            "actc-fixed-register-machine-abi",
        )

        self.assertIn(
            "x main 0 218\n"
            "x capture 170 15\n"
            "x four 185 3\n"
            "x pair 188 1\n"
            "x seven 189 3\n",
            obj,
        )
        self.assertIn("20 00 00 A2 00 48 8A 48", obj)
        self.assertIn("68 68 AA 68 68 20 00 00 48 8A 48", obj)
        self.assertIn(
            "68 68 8D A3 00 68 68 A8 68 68 AA 68 68 20 00 00 "
            "A2 00 48 8A 48",
            obj,
        )
        self.assertIn("68 68 8D A3 00 68 A8 68 AA 68 68 20 00 00", obj)
        self.assertIn(
            "8D 40 03 8E 41 03 8C 42 03 A5 A3 8D 43 03 60 "
            "A5 A3 60 60 A9 07 60",
            obj,
        )
        self.assertRegex(obj, r"r \d+ x seven\n")
        self.assertRegex(obj, r"r \d+ x pair\n")
        self.assertRegex(obj, r"r \d+ x four\n")
        self.assertRegex(obj, r"r \d+ x capture\n")
        self.assertNotIn("x pair_plo_lo", obj)
        self.assertNotIn("x capture_wordval_lo", obj)
        self.assertEqual(self.last_emit_overlay_pass, [19])

    def test_absolute_routine_declaration_emits_direct_register_call(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC KERNALOUT=($FFD0+2)(BYTE VALUE)\r"
            "PROC MAIN()\r"
            "KERNALOUT(65)\r"
            "RETURN\r",
            "actc-absolute-routine-address",
        )

        self.assertIn("A9 41 48 A9 00 48 68 68 20 D2 FF", obj)
        self.assertNotIn("x kernalout", obj)
        self.assertNotIn("u kernalout", obj)
        self.assertNotRegex(obj, r"r \d+ x kernalout")
        self.assertEqual(self.last_emit_overlay_pass, [19])

    def test_linked_routine_address_declarations_emit_named_relocations(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD VALUE\r"
            "PROC ALIAS=WORKER()\r"
            "PROC PLUS=WORKER+1()\r"
            "PROC MINUS=WORKER+-1()\r"
            "PROC EXPR=WORKER+(2*3)()\r"
            "PROC FIRST=(1 LSH 2)+WORKER()\r"
            "PROC WORKER()\r"
            "VALUE=1\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "ALIAS()\r"
            "PLUS()\r"
            "MINUS()\r"
            "EXPR()\r"
            "FIRST()\r"
            "RETURN\r",
            "actc-linked-routine-address",
        )

        self.assertGreaterEqual(obj.count("20 00 00"), 5)
        self.assertRegex(obj, r"r \d+ x worker\n")
        self.assertRegex(obj, r"r \d+ x worker 1\n")
        self.assertRegex(obj, r"r \d+ x worker -1\n")
        self.assertRegex(obj, r"r \d+ x worker 6\n")
        self.assertRegex(obj, r"r \d+ x worker 4\n")
        for name in ("alias", "plus", "minus", "expr", "first"):
            self.assertNotIn(f"x {name}", obj)
            self.assertNotIn(f"u {name}", obj)
        self.assertEqual(self.last_emit_overlay_pass, [19])

    def test_absolute_routine_tables_use_reserved_reu_bank(self) -> None:
        actc_text = (
            self.root / "src" / "tools_udos" / "actc" / "actc.asm"
        ).read_text(encoding="ascii")
        asmblock_text = (
            self.root / "src" / "tools_udos" / "actc" / "actc_asmblock_layout.inc"
        ).read_text(encoding="ascii")

        self.assertIn("ACTC_FIXED_NAME_REU_BASE_BANK = $FF", actc_text)
        self.assertIn("ACTC_FIXED_META_REU_BASE_BANK = $FF", actc_text)
        self.assertIn("ACTC_SOURCE_REU_BASE_BANK = $01", actc_text)
        self.assertIn("ACTC_BODY_DEBUG_REU_BASE_HI = $10", actc_text)
        self.assertIn("ACTC_BODY_DEBUG_REU_BASE_BANK = $FF", actc_text)
        self.assertIn("ACTC_ASMBLOCK_REU_HI_BASE = $00", asmblock_text)
        self.assertIn("ACTC_ASMBLOCK_REU_BANK = $FF", asmblock_text)
        self.assertNotIn("ACTC_FIXED_NAME_REU_BASE_BANK = $00", actc_text)
        self.assertNotIn("ACTC_FIXED_META_REU_BASE_BANK = $00", actc_text)

    def test_absolute_routines_support_returns_mixed_arguments_and_radix_addresses(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "BYTE BRESULT\r"
            "CARD WRESULT\r"
            "BYTE FUNC GETBYTE=($FFE0+4)()\r"
            "CARD FUNC GETWORD=65520()\r"
            "PROC MIXED=%1100000000000000(BYTE FIRST,CARD WORDVAL,BYTE LAST)\r"
            "PROC MAIN()\r"
            "BRESULT=GETBYTE()\r"
            "WRESULT=GETWORD()\r"
            "MIXED(11,4660,44)\r"
            "RETURN\r",
            "actc-absolute-routine-register-abi",
        )

        self.assertIn("20 E4 FF A2 00 48 8A 48", obj)
        self.assertIn("20 F0 FF 48 8A 48", obj)
        self.assertIn("68 68 8D A3 00 68 A8 68 AA 68 68 20 00 C0", obj)
        for name in ("getbyte", "getword", "mixed"):
            self.assertNotIn(f"x {name}", obj)
            self.assertNotIn(f"u {name}", obj)
            self.assertNotRegex(obj, rf"r \d+ x {name}")
        self.assertEqual(self.last_emit_overlay_pass, [19])

    def test_absolute_routines_compose_with_machine_runtime_and_asmblock(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "BYTE TRACE\r"
            "PROC KERNALOUT=$FFD2(BYTE VALUE)\r"
            "BYTE FUNC ECHO=*(BYTE VALUE)\r"
            "ASMBLOCK [\r"
            "LDA VALUE\r"
            "RTS\r"
            "]\r"
            "PROC MAIN()\r"
            "TRACE=1\r"
            "WHILE TRACE<2 DO\r"
            "SidVol(TRACE)\r"
            "TRACE=TRACE+1\r"
            "OD\r"
            "TRACE=ECHO(65)\r"
            "KERNALOUT(TRACE)\r"
            "ASMBLOCK [\r"
            "LDA TRACE\r"
            "STA $033C\r"
            "]\r"
            "RETURN\r",
            "actc-absolute-routine-composed",
        )

        self.assertEqual(self.last_emit_overlay_pass, [17])
        self.assertIn("u rt_sid_vol\n", obj)
        self.assertIn("20 D2 FF", obj)
        self.assertNotIn("x kernalout", obj)
        self.assertNotIn("u kernalout", obj)
        self.assertNotIn("b @", obj)

    def test_absolute_routine_declarations_validate_range_and_signature(self) -> None:
        self.build_actc_emit_overlay_stack()
        bad_sources = {
            "address_range": (
                "MODULE MAIN\rPROC BAD=$10000()\rPROC MAIN()\rRETURN\r"
            ),
            "real_parameter": (
                "MODULE MAIN\rPROC BAD=$FFD2(REAL VALUE)\rPROC MAIN()\rRETURN\r"
            ),
            "real_return": (
                "MODULE MAIN\rREAL FUNC BAD=$FFD2()\rPROC MAIN()\rRETURN\r"
            ),
            "duplicate": (
                "MODULE MAIN\rPROC BAD=$FFD2()\rPROC BAD=$FFE4()\r"
                "PROC MAIN()\rRETURN\r"
            ),
            "fixed_then_local_duplicate": (
                "MODULE MAIN\rPROC BAD=$FFD2()\rPROC BAD()\rRETURN\r"
                "PROC MAIN()\rRETURN\r"
            ),
            "local_then_fixed_duplicate": (
                "MODULE MAIN\rPROC BAD()\rRETURN\rPROC BAD=$FFD2()\r"
                "PROC MAIN()\rRETURN\r"
            ),
            "unknown_linked_target": (
                "MODULE MAIN\rPROC BAD=MISSING()\rPROC MAIN()\rRETURN\r"
            ),
            "linked_positive_addend_range": (
                "MODULE MAIN\rPROC BAD=TARGET+32768()\rPROC TARGET()\r"
                "RETURN\rPROC MAIN()\rRETURN\r"
            ),
            "linked_negative_addend_range": (
                "MODULE MAIN\rPROC BAD=TARGET+-32769()\rPROC TARGET()\r"
                "RETURN\rPROC MAIN()\rRETURN\r"
            ),
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            for name, source in bad_sources.items():
                with self.subTest(name=name):
                    project_root = Path(tmpdir) / name
                    source_dir = project_root / "src"
                    object_dir = project_root / "obj"
                    source_dir.mkdir(parents=True)
                    object_dir.mkdir()
                    (project_root / "ACTION.PROJ").write_text(
                        "ACTION PROJECT\rMAIN.ACT\r",
                        encoding="ascii",
                    )
                    (source_dir / "main.act").write_text(source, encoding="ascii")
                    result = subprocess.run(
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
                        ],
                        cwd=self.root,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertNotEqual(result.returncode, 0, msg=result.stdout)
                    diagnostic = (
                        "ROUTINE ADDRESS"
                        if name.startswith("linked_")
                        else "DECL OVL FAIL"
                    )
                    self.assertIn(diagnostic, result.stdout)

    def test_fixed_register_machine_routine_forces_capable_native_emitter(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC NOPPER=*()\r"
            "ASMBLOCK [\r"
            "RTS\r"
            "]\r"
            "PROC MAIN()\r"
            "NOPPER()\r"
            "RETURN\r",
            "actc-minimal-fixed-register-machine-emitter",
        )

        self.assertIn("x nopper", obj)
        self.assertIn("20 00 00", obj)
        self.assertRegex(obj, r"r \d+ x nopper\n")
        self.assertNotIn("b @", obj)
        self.assertEqual(self.last_emit_overlay_pass, [19])

    def test_fixed_register_call_arguments_accept_hex_and_binary_literals(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC CAPTURE=*(BYTE FIRST,CARD WORDVAL)\r"
            "ASMBLOCK [\r"
            "STA $0340\r"
            "STX $0341\r"
            "STY $0342\r"
            "RTS\r"
            "]\r"
            "PROC MAIN()\r"
            "CAPTURE($34,%0001001000110100)\r"
            "RETURN\r",
            "actc-fixed-register-radix-call-arguments",
        )

        self.assertIn("i 52\n", obj)
        self.assertIn("i 4660\n", obj)
        self.assertIn("8D 40 03 8E 41 03 8C 42 03 60", obj)
        self.assertRegex(obj, r"r \d+ x capture\n")
        self.assertEqual(self.last_emit_overlay_pass, [19])

    def test_raw_code_blocks_emit_native_bytes_and_relocations(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD BASE\r"
            "BYTE BRESULT\r"
            "CARD WRESULT\r"
            "BYTE FOURRESULT\r"
            "BYTE FUNC SEVEN=*()\r"
            "[$A9 7 $60]\r"
            "PROC LEGACY=*()\r"
            "[$FFA2$A686$CA0$AD0$60]\r"
            "CARD FUNC PAIR=*(BYTE LOW,BYTE HIGH)\r"
            "[$60]\r"
            "BYTE FUNC FOURTH=*(BYTE A,B,C,D)\r"
            "[$A3AD 0 $60]\r"
            "PROC CONSTANTS=*()\r"
            "['A' -1 4+$A7 BASE+2 SEVEN+1 * $60]\r"
            "PROC MAIN()\r"
            "[$A9 $34 $8D BASE]\r"
            "BRESULT=SEVEN()\r"
            "WRESULT=PAIR($34,%00010010)\r"
            "FOURRESULT=FOURTH(1,2,3,$4D)\r"
            "RETURN\r",
            "actc-raw-code-blocks",
        )

        self.assertIn("A2 FF 86 A6 A0 0C D0 0A 60", obj)
        self.assertIn("AD A3 00 60 60 A2 FF 86 A6", obj)
        self.assertIn("A9 07 60", obj)
        self.assertIn("41 FF FF AB 00 00 00 00 00 00 60", obj)
        self.assertRegex(obj, r"r \d+ x __v0 2\n")
        self.assertRegex(obj, r"r \d+ x seven 1\n")
        self.assertRegex(obj, r"r \d+ x __p\d+l\d+\n")
        self.assertRegex(obj, r"r \d+ x __v0\n")
        self.assertRegex(obj, r"r \d+ x seven\n")
        self.assertRegex(obj, r"r \d+ x pair\n")
        self.assertRegex(obj, r"r \d+ x fourth\n")
        self.assertNotIn("b @", obj)
        self.assertEqual(self.last_emit_overlay_pass, [19])

    def test_fixed_register_machine_routines_reject_unsupported_signatures(self) -> None:
        self.build_actc_emit_overlay_stack()
        bad_sources = {
            "real_return": (
                "MODULE MAIN\r"
                "REAL FUNC VALUE=*()\r"
                "ASMBLOCK [\rRTS\r]\r"
                "PROC MAIN()\rRETURN\r",
                "DECL OVL FAIL",
            ),
            "real_parameter": (
                "MODULE MAIN\r"
                "PROC VALUE=*(REAL ARG)\r"
                "ASMBLOCK [\rRTS\r]\r"
                "PROC MAIN()\rRETURN\r",
                "DECL OVL FAIL",
            ),
            "local_declaration": (
                "MODULE MAIN\r"
                "PROC VALUE=*()\r"
                "BYTE LOCAL\r"
                "ASMBLOCK [\rRTS\r]\r"
                "PROC MAIN()\rRETURN\r",
                "DECL OVL FAIL",
            ),
            "more_than_sixteen_abi_bytes": (
                "MODULE MAIN\r"
                "PROC VALUE=*(CARD P0,CARD P1,CARD P2,CARD P3,CARD P4,"
                "CARD P5,CARD P6,CARD P7,CARD P8)\r"
                "ASMBLOCK [\rRTS\r]\r"
                "PROC MAIN()\r"
                "VALUE(0,1,2,3,4,5,6,7,8)\r"
                "RETURN\r",
                "EMIT OVL FAIL",
            ),
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            for name, (source, diagnostic) in bad_sources.items():
                with self.subTest(name=name):
                    project_root = Path(tmpdir) / name
                    source_dir = project_root / "src"
                    object_dir = project_root / "obj"
                    source_dir.mkdir(parents=True)
                    object_dir.mkdir()
                    (project_root / "ACTION.PROJ").write_text(
                        "ACTION PROJECT\rMAIN.ACT\r",
                        encoding="ascii",
                    )
                    (source_dir / "main.act").write_text(source, encoding="ascii")
                    result = subprocess.run(
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
                        ],
                        cwd=self.root,
                        text=True,
                        capture_output=True,
                        check=False,
                        timeout=60,
                    )

                    self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                    summary = json.loads(result.stdout)
                    self.assertNotEqual(summary["exit_status"], 0, msg=result.stdout)
                    self.assertFalse(summary["hit_limit"], msg=result.stdout)
                    self.assertIn(diagnostic, summary["console"], msg=result.stdout)
                    self.assertFalse((object_dir / "MAIN.OBJ").exists())

    def test_asmblock_emits_symbols_labels_and_relocations(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD G\r"
            "PROC SET(P,Q)\r"
            "CARD L\r"
            "ASMBLOCK [\r"
            "START:\r"
            "LDA P\r"
            "STA G\r"
            "LDA Q\r"
            "STA L\r"
            "JMP DONE\r"
            "LDA #$00\r"
            "STA G\r"
            "DONE:\r"
            "]\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "SET(42,7)\r"
            "RETURN\r",
            "actc-overlay-asmblock-symbols-labels",
        )

        self.assertIn(
            "x main 0 103\n"
            "x set 44 49\n"
            "x __p0l0 72 1\n"
            "x __p0l1 92 1\n"
            "x __v0 93 2\n"
            "x __v1 95 2\n"
            "x __v2 97 2\n"
            "x __v3 99 2\n",
            obj,
        )
        self.assertIn(
            "68 AA 68 85 04 68 A0 05 91 06 68 88 91 06 "
            "68 A0 03 91 06 68 88 91 06 A5 04 48 8A 48",
            obj,
        )
        self.assertIn(
            "AD 00 00 8D 00 00 AD 00 00 8D 00 00 4C 00 00 "
            "A9 00 8D 00 00 60",
            obj,
        )
        self.assertIn(
            "r 26 x set\n"
            "r 73 x __v1\n"
            "r 76 x __v0\n"
            "r 79 x __v2\n"
            "r 82 x __v3\n"
            "r 85 x __p0l1\n"
            "r 90 x __v0\n",
            obj,
        )
        self.assertNotIn("b @0r\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_asmblock_relocates_module_local_routine(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD G\r"
            "PROC HELPER()\r"
            "G=1\r"
            "RETURN\r"
            "PROC RUN(P)\r"
            "CARD L\r"
            "ASMBLOCK [\r"
            "JSR HELPER\r"
            "LDA P\r"
            "STA L\r"
            "RTS\r"
            "]\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "RUN(0)\r"
            "RETURN\r",
            "actc-overlay-asmblock-local-routine",
        )

        self.assertIn("x helper", obj)
        self.assertIn("20 00 00 AD 00 00", obj)
        self.assertRegex(obj, r"r \d+ x helper\n")
        self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_asmblock_emits_decimal_operands(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "ASMBLOCK [\r"
            "LDX #0\r"
            "LDY #255\r"
            "LDA 16\r"
            "STA 4660\r"
            "]\r"
            "RETURN\r",
            "actc-overlay-asmblock-decimal-operands",
        )

        self.assertIn("m A2 00 A0 FF A5 10 8D 34 12", obj)
        self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_asmblock_indexed_label_operand_preserves_symbol(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "ASMBLOCK [\r"
            "LDX #0\r"
            "TABLE:\r"
            "NOP\r"
            "LDA TABLE,X\r"
            "STA $033C\r"
            "]\r"
            "RETURN\r",
            "actc-overlay-asmblock-indexed-label",
        )

        self.assertIn("m A2 00 EA BD 00 00 8D 3C 03", obj)
        self.assertRegex(obj, r"r \d+ x __p0l0\n")
        self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_card_function_asmblock_references_typed_symbols_and_returns_word(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD RESULT\r"
            "CARD TRACE\r"
            "CARD FUNC VALUE(CARD P,Q)\r"
            "CARD LOCAL\r"
            "ASMBLOCK [\r"
            "LDA P\r"
            "JMP STORE\r"
            "LDA #$E1\r"
            "STORE:\r"
            "STA LOCAL\r"
            "STA $033D\r"
            "LDA Q\r"
            "STA TRACE\r"
            "]\r"
            "RETURN(LOCAL+Q+1)\r"
            "PROC MAIN()\r"
            "RESULT=VALUE(40,1)\r"
            "ASMBLOCK [\r"
            "LDA RESULT\r"
            "STA $033C\r"
            "]\r"
            "RETURN\r",
            "actc-card-function-asmblock-symbols",
        )

        self.assertIn(
            "V p c 0 2 0 4 22\nV p c 0 3 0 4 24\nV l c 0 4 0 5 6\n",
            obj,
        )
        self.assertIn("x main 0 190\nx value 64 114\nx __p0l0 100 1\n", obj)
        self.assertIn("20 00 00 48 8A 48", obj)
        self.assertIn(
            "AD 00 00 4C 00 00 A9 E1 8D 00 00 8D 3D 03 AD 00 00 8D 00 00",
            obj,
        )
        self.assertIn("68 AA 68 60", obj)
        self.assertNotIn("u return\n", obj)
        self.assertIn(
            "r 26 x value\n"
            "r 43 x __v0\n"
            "r 93 x __v2\n"
            "r 96 x __p0l0\n"
            "r 101 x __v4\n"
            "r 107 x __v3\n"
            "r 110 x __v1\n",
            obj,
        )
        self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_card_function_runtime_helper_loop_uses_native_return_abi(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD R\r"
            "CARD FUNC F(CARD P)\r"
            "WHILE P<5 DO\r"
            "SidVol(P)\r"
            "P=P+1\r"
            "OD\r"
            "RETURN(P+1)\r"
            "PROC MAIN()\r"
            "R=F(4)\r"
            "RETURN\r",
            "actc-card-function-runtime-helper-loop",
        )

        self.assertEqual(self.last_emit_overlay_pass, [16])
        self.assertIn(
            "x main 0 214\nx f 52 156\nx __p0l0 71 1\n"
            "x __p0l1 170 1\nx __idata 208 4\nx __iptr 212 2\n",
            obj,
        )
        self.assertIn("20 00 00 48 8A 48", obj)
        self.assertIn(
            "68 AA 68 85 04 68 A0 03 91 06 68 88 91 06 A5 04 48 8A 48",
            obj,
        )
        self.assertIn("68 68 20 00 00", obj)
        self.assertIn("68 AA 68 60", obj)
        self.assertIn("r 20 x f\n", obj)
        self.assertIn("r 120 u0\n", obj)
        self.assertIn("u rt_sid_vol\n", obj)
        self.assertNotIn("u return\n", obj)

    def test_card_function_combines_asmblock_and_runtime_helper_loop(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD RESULT\r"
            "CARD TRACE\r"
            "CARD FUNC VALUE(CARD P)\r"
            "CARD LOCAL\r"
            "ASMBLOCK [\r"
            "LDA P\r"
            "STA LOCAL\r"
            "]\r"
            "WHILE LOCAL<41 DO\r"
            "SidVol(LOCAL)\r"
            "LOCAL=LOCAL+1\r"
            "OD\r"
            "ASMBLOCK [\r"
            "LDA LOCAL\r"
            "STA TRACE\r"
            "]\r"
            "RETURN(LOCAL+1)\r"
            "PROC MAIN()\r"
            "RESULT=VALUE(40)\r"
            "ASMBLOCK [\r"
            "LDA RESULT\r"
            "STA $033C\r"
            "LDA TRACE\r"
            "STA $033D\r"
            "]\r"
            "RETURN\r",
            "actc-card-function-asmblock-runtime-mixed",
        )

        self.assertEqual(self.last_emit_overlay_pass, [17])
        self.assertIn(
            "V p c 0 2 0 4 22\nV l c 0 3 0 5 6\n",
            obj,
        )
        self.assertIn(
            "x main 0 242\nx value 64 168\nx __p0l0 89 1\n"
            "x __p0l1 188 1\nx __v0 232 2\nx __v1 234 2\n"
            "x __v2 236 2\nx __v3 238 2\nx __idata 232 8\nx __iptr 240 2\n",
            obj,
        )
        self.assertEqual(obj.count("b u0M\n"), 2)
        self.assertIn("AD 00 00 8D 00 00", obj)
        self.assertIn("68 68 20 00 00", obj)
        self.assertIn("68 AA 68 60", obj)
        self.assertIn(
            "r 20 x value\n"
            "r 37 x __v0\n"
            "r 43 x __v1\n"
            "r 84 x __v2\n"
            "r 87 x __v3\n"
            "r 124 x __p0l1\n"
            "r 138 u0\n"
            "r 186 x __p0l0\n"
            "r 189 x __v3\n"
            "r 192 x __v1\n"
            "r 240 x __idata\n",
            obj,
        )
        self.assertIn("u rt_sid_vol\n", obj)
        body_lines = [line for line in obj.splitlines() if line.startswith("b ")]
        self.assertTrue(all(line.endswith("M") for line in body_lines), msg=obj)
        self.assertTrue(all(not any(op in line for op in "@AU") for line in body_lines), msg=obj)

    def test_asmblock_references_real_global_and_local_storage(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL GLOBAL\r"
            "PROC MAIN()\r"
            "REAL LOCAL\r"
            "ASMBLOCK [\r"
            "LDX #$00\r"
            "LDA #$11\r"
            "STA GLOBAL,X\r"
            "LDA #$22\r"
            "STA LOCAL,X\r"
            "LDX #$03\r"
            "LDA #$44\r"
            "STA GLOBAL,X\r"
            "LDA #$55\r"
            "STA LOCAL,X\r"
            "LDX #$00\r"
            "LDA GLOBAL,X\r"
            "STA $033C\r"
            "LDA LOCAL,X\r"
            "STA $033E\r"
            "LDX #$03\r"
            "LDA GLOBAL,X\r"
            "STA $033D\r"
            "LDA LOCAL,X\r"
            "STA $033F\r"
            "]\r"
            "RETURN\r",
            "actc-asmblock-real-storage",
        )

        self.assertEqual(self.last_emit_overlay_pass, [9])
        self.assertIn(
            "x main 0 91\n"
            "x __v0 81 4\n"
            "x __v1 85 4\n"
            "x __idata 81 8\n"
            "x __iptr 89 2\n",
            obj,
        )
        self.assertIn(
            "A2 00 A9 11 9D 00 00 A9 22 9D 00 00 "
            "A2 03 A9 44 9D 00 00 A9 55 9D 00 00",
            obj,
        )
        self.assertIn(
            "r 18 x __v0\n"
            "r 23 x __v1\n"
            "r 30 x __v0\n"
            "r 35 x __v1\n"
            "r 40 x __v0\n"
            "r 46 x __v1\n"
            "r 54 x __v0\n"
            "r 60 x __v1\n",
            obj,
        )
        self.assertIn("00 00 00 00 00 00 00 00 00 00\n", obj)
        self.assertNotIn("b @", obj)
        self.assertNotIn("u rt_f_", obj)

    def test_asmblock_real_storage_combines_with_runtime_imports(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL VALUE\r"
            "CARD ARG\r"
            "PROC MAIN()\r"
            "ARG=1\r"
            "ASMBLOCK [\r"
            "LDX #$03\r"
            "LDA #$2A\r"
            "STA VALUE,X\r"
            "]\r"
            "WHILE ARG<2 DO\r"
            "SidVol(ARG)\r"
            "ARG=ARG+1\r"
            "OD\r"
            "ASMBLOCK [\r"
            "LDX #$03\r"
            "LDA VALUE,X\r"
            "STA $033C\r"
            "]\r"
            "RETURN\r",
            "actc-asmblock-real-storage-runtime",
        )

        self.assertEqual(self.last_emit_overlay_pass, [17])
        self.assertIn(
            "x __v0 160 4\n"
            "x __v1 164 2\n"
            "x __idata 160 6\n"
            "x __iptr 166 2\n",
            obj,
        )
        self.assertIn("u rt_sid_vol\n", obj)
        self.assertNotIn("b @", obj)
        self.assertNotIn("u rt_f_", obj)

    def test_core_functions_require_value_return(self) -> None:
        self.build_actc_emit_overlay_stack()
        bad_sources = {
            "function_bare_return": (
                "MODULE MAIN\r"
                "CARD FUNC VALUE()\r"
                "RETURN\r"
                "PROC MAIN()\r"
                "RETURN\r"
            ),
            "real_function_bare_return": (
                "MODULE MAIN\r"
                "REAL FUNC VALUE()\r"
                "RETURN\r"
                "PROC MAIN()\r"
                "RETURN\r"
            ),
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            for name, source in bad_sources.items():
                with self.subTest(name=name):
                    project_root = Path(tmpdir) / name
                    source_dir = project_root / "src"
                    object_dir = project_root / "obj"
                    source_dir.mkdir(parents=True)
                    object_dir.mkdir()
                    (project_root / "ACTION.PROJ").write_text(
                        "ACTION PROJECT\rMAIN.ACT\r",
                        encoding="ascii",
                    )
                    (source_dir / "main.act").write_text(source, encoding="ascii")
                    result = subprocess.run(
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
                        ],
                        cwd=self.root,
                        text=True,
                        capture_output=True,
                        check=False,
                        timeout=60,
                    )

                    self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                    summary = json.loads(result.stdout)
                    self.assertNotEqual(summary["exit_status"], 0, msg=result.stdout)
                    self.assertFalse(summary["hit_limit"], msg=result.stdout)
                    self.assertIn("DECL OVL FAIL", summary["console"], msg=result.stdout)
                    self.assertFalse((object_dir / "MAIN.OBJ").exists())

    def test_real_function_returns_storage_pointer_and_caller_copies_value(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL SOURCE\r"
            "REAL RESULT\r"
            "REAL FUNC VALUE()\r"
            "RETURN(SOURCE)\r"
            "PROC MAIN()\r"
            "SOURCE=REAL(42)\r"
            "RESULT=VALUE()\r"
            "RETURN\r",
            "actc-real-function-direct-return",
        )

        self.assertEqual(self.last_emit_overlay_pass, [10])
        self.assertIn(
            "x main 0 76\n"
            "x value 61 5\n"
            "x __v0 66 4\n"
            "x __v1 70 4\n"
            "x __idata 66 8\n"
            "x __iptr 74 2\n"
            "b u0M\n"
            "b M\n"
            "b M\n"
            "b M\n"
            "b M\n"
            "b M\n",
            obj,
        )
        self.assertIn(
            "m A2 00 BD 00 00 85 06 E8 BD 00 00 85 07 "
            "A9 00 85 02 A9 00 85 03 A9 2A A2 00 20 00 00 "
            "20 00 00 85 04 86 05 A0 03 B1 04 99 00 00 88 10 F8",
            obj,
        )
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 14 l x __v0\n"
            "r 18 h x __v0\n"
            "r 26 u0\n"
            "r 29 x value\n"
            "r 40 x __v1\n"
            "r 62 l x __v0\n"
            "r 64 h x __v0\n"
            "r 74 x __idata\n",
            obj,
        )
        self.assertIn("u rt_i_to_f\ni 0\ni 42\n", obj)

    def test_real_function_uses_captured_nonfixed_storage_indexes(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL UNUSED\r"
            "REAL SOURCE\r"
            "REAL RESULT\r"
            "REAL FUNC VALUE()\r"
            "RETURN(SOURCE)\r"
            "PROC MAIN()\r"
            "SOURCE=REAL(42)\r"
            "RESULT=VALUE()\r"
            "RETURN\r",
            "actc-real-function-nonfixed-storage",
        )

        self.assertEqual(self.last_emit_overlay_pass, [10])
        self.assertIn(
            "x main 0 80\n"
            "x value 61 5\n"
            "x __v0 66 4\n"
            "x __v1 70 4\n"
            "x __v2 74 4\n"
            "x __idata 66 12\n"
            "x __iptr 78 2\n"
            "b u0M\n"
            "b M\n"
            "b M\n"
            "b M\n"
            "b M\n"
            "b M\n"
            "b M\n",
            obj,
        )
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 14 l x __v1\n"
            "r 18 h x __v1\n"
            "r 26 u0\n"
            "r 29 x value\n"
            "r 40 x __v2\n"
            "r 62 l x __v1\n"
            "r 64 h x __v1\n"
            "r 78 x __idata\n",
            obj,
        )
        self.assertIn("v unused 0 4\nv source 0 4\nv result 0 4\n", obj)

    def test_real_function_derives_mixed_width_module_storage_offsets(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD UNUSED\r"
            "REAL SOURCE\r"
            "REAL RESULT\r"
            "REAL FUNC VALUE()\r"
            "RETURN(SOURCE)\r"
            "PROC MAIN()\r"
            "SOURCE=REAL(42)\r"
            "RESULT=VALUE()\r"
            "RETURN\r",
            "actc-real-function-mixed-width-storage",
        )

        self.assertEqual(self.last_emit_overlay_pass, [10])
        self.assertIn(
            "x main 0 78\n"
            "x value 61 5\n"
            "x __v0 66 2\n"
            "x __v1 68 4\n"
            "x __v2 72 4\n"
            "x __idata 66 10\n"
            "x __iptr 76 2\n"
            "b u0M\n"
            "b M\n"
            "b M\n"
            "b M\n"
            "b M\n"
            "b M\n"
            "b M\n",
            obj,
        )
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 14 l x __v1\n"
            "r 18 h x __v1\n"
            "r 26 u0\n"
            "r 29 x value\n"
            "r 40 x __v2\n"
            "r 62 l x __v1\n"
            "r 64 h x __v1\n"
            "r 76 x __idata\n",
            obj,
        )
        self.assertIn("v unused 0\nv source 0 4\nv result 0 4\n", obj)

    def test_real_function_binds_word_parameter_and_returns_converted_storage(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL SOURCE\r"
            "REAL RESULT\r"
            "REAL FUNC VALUE(CARD P)\r"
            "SOURCE=REAL(P)\r"
            "RETURN(SOURCE)\r"
            "PROC MAIN()\r"
            "RESULT=VALUE(42)\r"
            "RETURN\r",
            "actc-real-function-word-param",
        )

        self.assertEqual(self.last_emit_overlay_pass, [10])
        self.assertIn(
            "x main 0 126\n"
            "x value 69 45\n"
            "x __v0 114 4\n"
            "x __v1 118 4\n"
            "x __v2 122 2\n"
            "x __idata 114 10\n"
            "x __iptr 124 2\n"
            "b u0M\n"
            "b u0M\n"
            "b M\n"
            "b M\n"
            "b M\n"
            "b M\n"
            "b M\n",
            obj,
        )
        self.assertIn(
            "A2 00 A9 2A 9D 00 00 E8 A9 00 9D 00 00 "
            "CA BD 00 00 48 E8 BD 00 00 48 20 00 00",
            obj,
        )
        self.assertIn(
            "68 AA 68 85 04 68 A0 09 91 06 68 88 91 06 "
            "A5 04 48 8A 48 A9 00 85 02 A9 00 85 03 "
            "A0 08 B1 06 48 C8 B1 06 AA 68 20 00 00",
            obj,
        )
        self.assertIn(
            "r 18 x __v2\n"
            "r 24 x __v2\n"
            "r 28 x __v2\n"
            "r 33 x __v2\n"
            "r 37 x value\n"
            "r 48 x __v1\n"
            "r 89 l x __v0\n"
            "r 93 h x __v0\n"
            "r 107 u0\n"
            "r 110 l x __v0\n"
            "r 112 h x __v0\n"
            "r 124 x __idata\n",
            obj,
        )
        self.assertIn("u rt_i_to_f\ni 42\n", obj)
        self.assertIn("v source 0 4\nv result 0 4\nv p 0\n", obj)

    def test_real_function_accepts_named_word_argument_storage(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD ARG\r"
            "REAL SOURCE\r"
            "REAL RESULT\r"
            "REAL FUNC VALUE(CARD P)\r"
            "SOURCE=REAL(P)\r"
            "RETURN(SOURCE)\r"
            "PROC MAIN()\r"
            "ARG=42\r"
            "RESULT=VALUE(ARG)\r"
            "RETURN\r",
            "actc-real-function-variable-word-param",
        )

        self.assertEqual(self.last_emit_overlay_pass, [10])
        self.assertIn(
            "x main 0 128\n"
            "x value 69 45\n"
            "x __v0 114 2\n"
            "x __v1 116 4\n"
            "x __v2 120 4\n"
            "x __v3 124 2\n"
            "x __idata 114 12\n"
            "x __iptr 126 2\n",
            obj,
        )
        self.assertIn(
            "r 18 x __v0\n"
            "r 24 x __v0\n"
            "r 28 x __v0\n"
            "r 33 x __v0\n"
            "r 37 x value\n"
            "r 48 x __v2\n"
            "r 89 l x __v1\n"
            "r 93 h x __v1\n"
            "r 107 u0\n"
            "r 110 l x __v1\n"
            "r 112 h x __v1\n"
            "r 126 x __idata\n",
            obj,
        )
        self.assertIn("u rt_i_to_f\ni 42\n", obj)
        self.assertIn("v arg 0\nv source 0 4\nv result 0 4\nv p 0\n", obj)

    def test_real_function_binds_named_real_argument_by_value(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL ARG\r"
            "REAL RESULT\r"
            "REAL FUNC VALUE(REAL P)\r"
            "RETURN(P)\r"
            "PROC MAIN()\r"
            "ARG=REAL(42)\r"
            "RESULT=VALUE(ARG)\r"
            "RETURN\r",
            "actc-real-function-real-param",
        )

        self.assertEqual(self.last_emit_overlay_pass, [10])
        self.assertIn(
            "x main 0 112\n"
            "x value 67 31\n"
            "x __v0 98 4\n"
            "x __v1 102 4\n"
            "x __v2 106 4\n"
            "x __idata 98 12\n"
            "x __iptr 110 2\n",
            obj,
        )
        self.assertIn(
            "A9 2A A2 00 20 00 00 A9 00 48 A9 00 48 20 00 00 "
            "85 04 86 05 A0 03 B1 04 99 00 00 88 10 F8",
            obj,
        )
        self.assertIn(
            "68 AA 68 85 04 68 85 03 68 85 02 A5 04 48 8A 48 "
            "A0 03 B1 02 99 00 00 88 10 F8 A9 00 A2 00 60",
            obj,
        )
        self.assertIn(
            "r 14 l x __v0\n"
            "r 18 h x __v0\n"
            "r 26 u0\n"
            "r 29 l x __v0\n"
            "r 32 h x __v0\n"
            "r 35 x value\n"
            "r 46 x __v1\n"
            "r 88 x __v2\n"
            "r 94 l x __v2\n"
            "r 96 h x __v2\n"
            "r 110 x __idata\n",
            obj,
        )
        self.assertIn("u rt_i_to_f\ni 0\ni 42\n", obj)
        self.assertIn("v arg 0 4\nv result 0 4\nv p 0 4\n", obj)

    def test_real_function_binds_two_named_real_arguments_by_value(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL LEFT\r"
            "REAL RIGHT\r"
            "REAL RESULT\r"
            "REAL FUNC FIRST(REAL A,B)\r"
            "RETURN(A)\r"
            "PROC MAIN()\r"
            "LEFT=REAL(1)\r"
            "RIGHT=REAL(2)\r"
            "RESULT=FIRST(LEFT,RIGHT)\r"
            "RETURN\r",
            "actc-real-function-two-real-params",
        )

        self.assertEqual(self.last_emit_overlay_pass, [10])
        self.assertIn(
            "x main 0 157\n"
            "x first 88 47\n"
            "x __v0 135 4\n"
            "x __v1 139 4\n"
            "x __v2 143 4\n"
            "x __v3 147 4\n"
            "x __v4 151 4\n"
            "x __idata 135 20\n"
            "x __iptr 155 2\n",
            obj,
        )
        self.assertIn(
            "r 14 l x __v0\n"
            "r 18 h x __v0\n"
            "r 26 u0\n"
            "r 29 l x __v1\n"
            "r 33 h x __v1\n"
            "r 41 u0\n"
            "r 44 l x __v0\n"
            "r 47 h x __v0\n"
            "r 50 l x __v1\n"
            "r 53 h x __v1\n"
            "r 56 x first\n"
            "r 67 x __v2\n"
            "r 104 x __v4\n"
            "r 120 x __v3\n"
            "r 131 l x __v3\n"
            "r 133 h x __v3\n"
            "r 155 x __idata\n",
            obj,
        )
        self.assertIn("u rt_i_to_f\ni 0\ni 1\ni 0\ni 2\n", obj)
        self.assertIn(
            "v left 0 4\nv right 0 4\nv result 0 4\nv a 0 4\nv b 0 4\n",
            obj,
        )
        self.assertIn(
            "L 0 88 0 5 11\n"
            "L 0 109 0 5 11\n"
            "L 0 130 0 6 1\n"
            "L 0 132 0 6 1\n"
            "L 0 134 0 6 1\n",
            obj,
        )

    def test_real_function_returns_second_named_real_parameter(self) -> None:
        source = (
            self.root
            / "tests"
            / "parity"
            / "two_real_second_return_permuted.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-real-function-two-real-params-second-return",
        )

        self.assertEqual(self.last_emit_overlay_pass, [10])
        self.assertIn(
            "x main 0 157\n"
            "x second 88 47\n"
            "x __v0 135 4\n"
            "x __v1 139 4\n"
            "x __v2 143 4\n"
            "x __v3 147 4\n"
            "x __v4 151 4\n"
            "x __idata 135 20\n"
            "x __iptr 155 2\n",
            obj,
        )
        self.assertIn(
            "r 14 l x __v2\n"
            "r 18 h x __v2\n"
            "r 26 u0\n"
            "r 29 l x __v1\n"
            "r 33 h x __v1\n"
            "r 41 u0\n"
            "r 44 l x __v2\n"
            "r 47 h x __v2\n"
            "r 50 l x __v1\n"
            "r 53 h x __v1\n"
            "r 56 x second\n"
            "r 67 x __v0\n",
            obj,
        )
        self.assertIn(
            "r 104 x __v4\n"
            "r 120 x __v3\n"
            "r 131 l x __v4\n"
            "r 133 h x __v4\n"
            "r 155 x __idata\n",
            obj,
        )
        self.assertIn("u rt_i_to_f\ni 0\ni 1\ni 0\ni 2\n", obj)
        self.assertIn(
            "v result 0 4\nv right 0 4\nv left 0 4\nv b 0 4\nv a 0 4\n",
            obj,
        )

    def test_real_function_selects_smaller_finite_parameter_natively(self) -> None:
        source = (
            self.root / "tests" / "parity" / "finite_real_min.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-real-function-finite-min",
        )

        self.assertEqual(self.last_emit_overlay_pass, [20])
        self.assertIn(
            "x main 0 185\n"
            "x min2 88 75\n"
            "x __v0 163 4\n"
            "x __v1 167 4\n"
            "x __v2 171 4\n"
            "x __v3 175 4\n"
            "x __v4 179 4\n"
            "x __idata 163 20\n"
            "x __iptr 183 2\n",
            obj,
        )
        self.assertIn("b u0u1M\nb u0M\n", obj)
        self.assertIn(
            "20 00 00 C9 FF D0 05 A9 00 A2 00 60 A9 00 A2 00 60",
            obj,
        )
        self.assertIn(
            "r 56 x min2\n"
            "r 67 x __v2\n"
            "r 104 x __v4\n"
            "r 120 x __v3\n"
            "r 131 l x __v4\n"
            "r 135 h x __v4\n"
            "r 139 l x __v3\n"
            "r 143 h x __v3\n"
            "r 147 u0\n"
            "r 154 l x __v4\n"
            "r 156 h x __v4\n"
            "r 159 l x __v3\n"
            "r 161 h x __v3\n",
            obj,
        )
        self.assertIn("u rt_f_cmp\nu rt_i_to_f\n", obj)
        self.assertNotIn("b S4S3L4U4L3U3u0p0lhL4U4rvL3U3r\n", obj)

    def test_real_function_finite_min_tracks_permuted_named_storage(self) -> None:
        source = (
            self.root / "tests" / "parity" / "finite_real_min_permuted.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-real-function-finite-min-permuted",
        )

        self.assertEqual(self.last_emit_overlay_pass, [20])
        self.assertIn(
            "x main 0 185\n"
            "x min2 88 75\n"
            "x __v0 163 4\n"
            "x __v1 167 4\n"
            "x __v2 171 4\n"
            "x __v3 175 4\n"
            "x __v4 179 4\n"
            "x __idata 163 20\n"
            "x __iptr 183 2\n",
            obj,
        )
        self.assertIn(
            "r 14 l x __v2\n"
            "r 18 h x __v2\n"
            "r 26 u1\n"
            "r 29 l x __v1\n"
            "r 33 h x __v1\n"
            "r 41 u1\n"
            "r 44 l x __v2\n"
            "r 47 h x __v2\n"
            "r 50 l x __v1\n"
            "r 53 h x __v1\n"
            "r 56 x min2\n"
            "r 67 x __v0\n",
            obj,
        )
        self.assertIn(
            "r 104 x __v4\n"
            "r 120 x __v3\n"
            "r 131 l x __v3\n"
            "r 135 h x __v3\n"
            "r 139 l x __v4\n"
            "r 143 h x __v4\n"
            "r 147 u0\n"
            "r 154 l x __v3\n"
            "r 156 h x __v3\n"
            "r 159 l x __v4\n"
            "r 161 h x __v4\n",
            obj,
        )
        self.assertIn("u rt_f_cmp\nu rt_i_to_f\n", obj)
        self.assertIn(
            "v result 0 4\nv right 0 4\nv left 0 4\nv b 0 4\nv a 0 4\n",
            obj,
        )

    def test_real_function_returns_selected_binary_helper_result(self) -> None:
        for function_name, runtime_module, expression in (
            ("ADD", "rt_f_add", "A+B"),
            ("SUBTRACT", "rt_f_sub", "A-B"),
            ("MULTIPLY", "rt_f_mul", "A*B"),
            ("DIVIDE", "rt_f_div", "A/B"),
            ("SMALLER", "rt_f_min", "FMin(A,B)"),
            ("LARGER", "rt_f_max", "FMax(B,A)"),
            ("REMAINDER", "rt_f_mod", "FMod(A,B)"),
            ("LENGTH", "rt_f_hypot", "FHypot(A,B)"),
        ):
            with self.subTest(function_name=function_name):
                obj = self.compile_overlay_object(
                    "MODULE MAIN\r"
                    "REAL LEFT\r"
                    "REAL RIGHT\r"
                    "REAL RESULT\r"
                    f"REAL FUNC {function_name}(REAL A,B)\r"
                    f"RETURN({expression})\r"
                    "PROC MAIN()\r"
                    "LEFT=REAL(3)\r"
                    "RIGHT=REAL(4)\r"
                    f"RESULT={function_name}(LEFT,RIGHT)\r"
                    "RETURN\r",
                    f"actc-real-function-{function_name.lower()}",
                )

                self.assertEqual(self.last_emit_overlay_pass, [20])
                self.assertIn(
                    "x main 0 189\n"
                    f"x {function_name.lower()} 88 75\n"
                    "x __v0 163 4\n"
                    "x __v1 167 4\n"
                    "x __v2 171 4\n"
                    "x __v3 175 4\n"
                    "x __v4 179 4\n"
                    "x __idata 163 24\n"
                    "x __fresult 183 4\n"
                    "x __iptr 187 2\n",
                    obj,
                )
                self.assertIn("b u0u1M\nb u0M\n", obj)
                self.assertIn("r 26 u1\n", obj)
                self.assertIn("r 41 u1\n", obj)
                self.assertIn("r 147 l x __fresult\nr 151 h x __fresult\n", obj)
                self.assertIn("r 155 u0\n", obj)
                self.assertIn("r 158 l x __fresult\nr 160 h x __fresult\n", obj)
                self.assertIn("u rt_i_to_f\n", obj)
                self.assertIn(f"u {runtime_module}\n", obj)
                for sibling in (
                    "rt_f_add",
                    "rt_f_sub",
                    "rt_f_mul",
                    "rt_f_div",
                    "rt_f_min",
                    "rt_f_max",
                    "rt_f_mod",
                    "rt_f_hypot",
                ):
                    if sibling != runtime_module:
                        self.assertNotIn(f"u {sibling}\n", obj)
                self.assertNotRegex(obj, r"(?m)^b .*S[0-9]")

    def test_asmblock_emits_symbolic_immediate_byte_relocations(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD G\r"
            "PROC MAIN(A)\r"
            "CARD L\r"
            "ASMBLOCK [\r"
            "LDA #<G\r"
            "LDX #>A\r"
            "LDY #<L\r"
            "LDA #>DONE\r"
            "LDA #<$1234\r"
            "LDX #>$1234\r"
            "DONE:\r"
            "]\r"
            "RETURN\r",
            "actc-overlay-asmblock-byte-relocations",
        )

        self.assertIn(
            "A9 00 A2 00 A0 00 A9 00 A9 34 A2 12 A9 A5 8D D0 03",
            obj,
        )
        self.assertIn(
            "r 33 l x __v0\n"
            "r 35 h x __v1\n"
            "r 37 l x __v2\n"
            "r 39 h x __p0l0\n",
            obj,
        )
        self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_asmblock_emits_signed_symbol_addends_for_all_relocation_parts(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "BYTE PAD\r"
            "CARD PAIR\r"
            "PROC MAIN()\r"
            "ASMBLOCK [\r"
            "LDA #$77\r"
            "STA PAD+1\r"
            "LDA #$34\r"
            "STA PAIR\r"
            "LDA #$12\r"
            "STA PAIR+1\r"
            "LDA PAIR+1\r"
            "STA $033C\r"
            "LDA PAIR-1\r"
            "STA $033D\r"
            "LDA #<PAIR+1\r"
            "STA $033E\r"
            "LDA #>PAIR+1\r"
            "STA $033F\r"
            "]\r"
            "RETURN\r",
            "actc-overlay-asmblock-symbol-addends",
        )

        self.assertRegex(obj, r"(?m)^r \d+ x __v1 1$")
        self.assertGreaterEqual(len(re.findall(r"(?m)^r \d+ x __v1 1$", obj)), 2)
        self.assertRegex(obj, r"(?m)^r \d+ x __v1 -1$")
        self.assertRegex(obj, r"(?m)^r \d+ l x __v1 1$")
        self.assertRegex(obj, r"(?m)^r \d+ h x __v1 1$")
        self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_asmblock_rejects_invalid_assembly(self) -> None:
        self.build_actc_emit_overlay_stack()
        bad_sources = {
            "invalid_opcode": (
                "MODULE MAIN\rPROC MAIN()\rASMBLOCK [\rXYZ #1\r]\rRETURN\r",
                "ASM",
            ),
            "duplicate_label": (
                "MODULE MAIN\rPROC MAIN()\rASMBLOCK [\rL:\rNOP\rL:\rNOP\r]\rRETURN\r",
                "ASM",
            ),
            "undefined_label": (
                "MODULE MAIN\rPROC MAIN()\rASMBLOCK [\rJMP MISSING\r]\rRETURN\r",
                "ASM",
            ),
            "undefined_immediate_symbol": (
                "MODULE MAIN\rPROC MAIN()\rASMBLOCK [\rLDA #<MISSING\r]\rRETURN\r",
                "ASM",
            ),
            "positive_addend_out_of_range": (
                "MODULE MAIN\rCARD VALUE\rPROC MAIN()\rASMBLOCK [\rLDA VALUE+128\r]\rRETURN\r",
                "ASM",
            ),
            "negative_addend_out_of_range": (
                "MODULE MAIN\rCARD VALUE\rPROC MAIN()\rASMBLOCK [\rLDA VALUE-129\r]\rRETURN\r",
                "ASM",
            ),
            "unterminated_block": (
                "MODULE MAIN\rPROC MAIN()\rASMBLOCK [\rNOP\rRETURN\r",
                "DECL OVL FAIL",
            ),
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            for name, (source, diagnostic) in bad_sources.items():
                with self.subTest(name=name):
                    project_root = Path(tmpdir) / name
                    source_dir = project_root / "src"
                    object_dir = project_root / "obj"
                    source_dir.mkdir(parents=True)
                    object_dir.mkdir()
                    (project_root / "ACTION.PROJ").write_text(
                        "ACTION PROJECT\rMAIN.ACT\r",
                        encoding="ascii",
                    )
                    (source_dir / "main.act").write_text(source, encoding="ascii")
                    result = subprocess.run(
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
                        ],
                        cwd=self.root,
                        text=True,
                        capture_output=True,
                        check=False,
                        timeout=60,
                    )

                    self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                    summary = json.loads(result.stdout)
                    self.assertNotEqual(summary["exit_status"], 0, msg=result.stdout)
                    self.assertFalse(summary["hit_limit"], msg=result.stdout)
                    self.assertIn(diagnostic, summary["console"], msg=result.stdout)
                    self.assertFalse((object_dir / "MAIN.OBJ").exists())

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

    def test_native_runtime_sequence_emitter_owns_abi_result_stores(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "BYTE J\r"
            "BYTE P\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "P=JoySeen(2)\r"
            "RETURN\r",
            "actc-overlay-native-integer-abi-result-calls",
        )

        self.assertIn("b u0u1M\n", obj)
        self.assertIn("\nm ", obj)
        self.assertIn("x __idata ", obj)
        self.assertIn("u rt_joy\n", obj)
        self.assertIn("u rt_jp\n", obj)
        self.assertNotIn("b p0u0S0p1u1S1r\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [14])

    def test_native_integer_emitter_owns_simple_equality_if(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "X=7\r"
            "IF X=7 THEN\r"
            "Y=1\r"
            "FI\r"
            "RETURN\r",
            "actc-overlay-native-integer-equality-if",
        )

        self.assertIn(
            "x main 0 107\n"
            "x __if0 85 1\n"
            "x __idata 101 4\n"
            "x __iptr 105 2\n",
            obj,
        )
        self.assertIn("b M\nb M\nb M\nb M\n", obj)
        self.assertIn(
            "68 85 05 68 85 04 68 85 03 68 C5 04 D0 06 "
            "A5 03 C5 05 F0 03 4C 00 00",
            obj,
        )
        self.assertIn("r 66 x __if0\n", obj)
        self.assertNotIn("b p0S0L0p1qhp2S1vr\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_simple_not_equal_if(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "X=2\r"
            "Y=1\r"
            "IF X<>Y THEN\r"
            "Y=3\r"
            "FI\r"
            "RETURN\r",
            "actc-overlay-native-integer-not-equal-if",
        )

        self.assertIn(
            "x main 0 127\n"
            "x __if0 105 1\n"
            "x __idata 121 4\n"
            "x __iptr 125 2\n",
            obj,
        )
        self.assertIn(
            "68 85 05 68 85 04 68 85 03 68 C5 04 D0 09 "
            "A5 03 C5 05 D0 03 4C 00 00",
            obj,
        )
        self.assertIn("r 86 x __if0\n", obj)
        self.assertNotIn("b p0S0p1S1L0L1nhp2S1vr\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_simple_less_than_if(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "X=1\r"
            "Y=2\r"
            "IF X<Y THEN\r"
            "Y=3\r"
            "FI\r"
            "RETURN\r",
            "actc-overlay-native-integer-less-than-if",
        )

        self.assertIn(
            "x main 0 126\n"
            "x __if0 104 1\n"
            "x __idata 120 4\n"
            "x __iptr 124 2\n",
            obj,
        )
        self.assertIn(
            "68 85 05 68 85 04 68 AA 68 E4 05 90 09 D0 04 "
            "C5 04 90 03 4C 00 00",
            obj,
        )
        self.assertIn("r 85 x __if0\n", obj)
        self.assertNotIn("b p0S0p1S1L0L1lhp2S1vr\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_simple_greater_than_if(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "X=2\r"
            "Y=1\r"
            "IF X>Y THEN\r"
            "Y=3\r"
            "FI\r"
            "RETURN\r",
            "actc-overlay-native-integer-greater-than-if",
        )

        self.assertIn(
            "x main 0 128\n"
            "x __if0 106 1\n"
            "x __idata 122 4\n"
            "x __iptr 126 2\n",
            obj,
        )
        self.assertIn(
            "68 85 05 68 85 04 68 AA 68 E4 05 90 08 D0 09 "
            "C5 04 90 02 D0 03 4C 00 00",
            obj,
        )
        self.assertIn("r 87 x __if0\n", obj)
        self.assertNotIn("b p0S0p1S1L0L1ghp2S1vr\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_simple_greater_equal_if(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "X=2\r"
            "Y=1\r"
            "IF X>=Y THEN\r"
            "Y=3\r"
            "FI\r"
            "RETURN\r",
            "actc-overlay-native-integer-greater-equal-if",
        )

        self.assertIn(
            "x main 0 126\n"
            "x __if0 104 1\n"
            "x __idata 120 4\n"
            "x __iptr 124 2\n",
            obj,
        )
        self.assertIn(
            "68 85 05 68 85 04 68 AA 68 E4 05 90 06 D0 07 "
            "C5 04 B0 03 4C 00 00",
            obj,
        )
        self.assertIn("r 85 x __if0\n", obj)
        self.assertNotIn("b p0S0p1S1L0L1lp2qhp3S1vr\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_simple_less_equal_if(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "X=1\r"
            "Y=1\r"
            "IF X<=Y THEN\r"
            "Y=3\r"
            "FI\r"
            "RETURN\r",
            "actc-overlay-native-integer-less-equal-if",
        )

        self.assertIn(
            "x main 0 128\n"
            "x __if0 106 1\n"
            "x __idata 122 4\n"
            "x __iptr 126 2\n",
            obj,
        )
        self.assertIn(
            "68 85 05 68 85 04 68 AA 68 E4 05 90 0B D0 06 "
            "C5 04 90 05 F0 03 4C 00 00",
            obj,
        )
        self.assertIn("r 87 x __if0\n", obj)
        self.assertNotIn("b p0S0p1S1L0L1gp2qhp3S1vr\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_simple_if_else(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "X=7\r"
            "IF X=8 THEN\r"
            "Y=1\r"
            "ELSE\r"
            "Y=2\r"
            "FI\r"
            "RETURN\r",
            "actc-overlay-native-integer-if-else",
        )

        self.assertIn(
            "x main 0 127\n"
            "x __if0 88 1\n"
            "x __if1 105 1\n"
            "x __idata 121 4\n"
            "x __iptr 125 2\n",
            obj,
        )
        self.assertIn("b M\nb M\nb M\nb M\nb M\n", obj)
        self.assertIn("4C 00 00 A9 02 48", obj)
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 66 x __if0\n"
            "r 86 x __if1\n"
            "r 125 x __idata\n",
            obj,
        )
        self.assertNotIn("b p0S0L0p1qhp2S1wp3S1vr\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_nested_if(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "CARD Z\r"
            "PROC MAIN()\r"
            "X=1\r"
            "Y=2\r"
            "IF X<Y THEN\r"
            "IF Y>1 THEN\r"
            "Z=3\r"
            "FI\r"
            "FI\r"
            "RETURN\r",
            "actc-overlay-native-integer-nested-if",
        )

        self.assertIn(
            "x main 0 167\n"
            "x __if0 143 1\n"
            "x __if2 143 1\n"
            "x __idata 159 6\n"
            "x __iptr 165 2\n",
            obj,
        )
        self.assertIn("b M\nb M\nb M\nb M\nb M\n", obj)
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 85 x __if0\n"
            "r 124 x __if2\n"
            "r 165 x __idata\n",
            obj,
        )
        self.assertNotIn("b p0S0p1S1L0L1lhL1p2ghp3S2vvr\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_nested_if_else(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "CARD Z\r"
            "PROC MAIN()\r"
            "X=1\r"
            "Y=2\r"
            "IF X<Y THEN\r"
            "IF Y>2 THEN\r"
            "Z=3\r"
            "ELSE\r"
            "Z=4\r"
            "FI\r"
            "FI\r"
            "RETURN\r",
            "actc-overlay-native-integer-nested-if-else",
        )

        self.assertIn(
            "x main 0 187\n"
            "x __if0 163 1\n"
            "x __if2 146 1\n"
            "x __if3 163 1\n"
            "x __idata 179 6\n"
            "x __iptr 185 2\n",
            obj,
        )
        self.assertIn("b M\nb M\nb M\nb M\nb M\nb M\n", obj)
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 85 x __if0\n"
            "r 124 x __if2\n"
            "r 144 x __if3\n"
            "r 185 x __idata\n",
            obj,
        )
        self.assertNotIn("b p0S0p1S1L0L1lhL1p2ghp3S2wp4S2vvr\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_nested_conditions_track_inversion_per_operation(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "CARD Z\r"
            "PROC MAIN()\r"
            "X=2\r"
            "Y=1\r"
            "IF X>=Y THEN\r"
            "IF Y<X THEN\r"
            "Z=5\r"
            "FI\r"
            "FI\r"
            "RETURN\r",
            "actc-overlay-native-integer-nested-mixed-inversion",
        )

        self.assertIn(
            "x main 0 168\n"
            "x __if0 144 1\n"
            "x __if2 144 1\n"
            "x __idata 160 6\n"
            "x __iptr 166 2\n",
            obj,
        )
        greater_equal = "90 06 D0 07 C5 04 B0 03 4C 00 00"
        less_than = "90 09 D0 04 C5 04 90 03 4C 00 00"
        self.assertIn(greater_equal, obj)
        self.assertIn(less_than, obj)
        self.assertLess(obj.index(greater_equal), obj.index(less_than))
        self.assertIn("r 85 x __if0\nr 125 x __if2\nr 166 x __idata\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_do_until_equality(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "PROC MAIN()\r"
            "X=0\r"
            "DO\r"
            "X=1\r"
            "UNTIL X=1\r"
            "OD\r"
            "RETURN\r",
            "actc-overlay-native-integer-do-until-equality",
        )

        self.assertIn(
            "x main 0 105\n"
            "x __do0 30 1\n"
            "x __idata 101 2\n"
            "x __iptr 103 2\n",
            obj,
        )
        self.assertIn("b M\nb M\nb M\nb M\n", obj)
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 83 x __do0\n"
            "r 103 x __idata\n",
            obj,
        )
        self.assertNotIn("b p0S0dp1S0L0p2qtor\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_do_until_less_than(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "X=1\r"
            "Y=2\r"
            "DO\r"
            "X=1\r"
            "UNTIL X<Y\r"
            "OD\r"
            "RETURN\r",
            "actc-overlay-native-integer-do-until-less-than",
        )

        self.assertIn(
            "x main 0 126\n"
            "x __do0 47 1\n"
            "x __idata 120 4\n"
            "x __iptr 124 2\n",
            obj,
        )
        self.assertIn(
            "68 85 05 68 85 04 68 AA 68 E4 05 90 09 D0 04 "
            "C5 04 90 03 4C 00 00",
            obj,
        )
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 102 x __do0\n"
            "r 124 x __idata\n",
            obj,
        )
        self.assertNotIn("b p0S0p1S1dp2S0L0L1ltor\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_for_loops_and_wrap_guards(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD I\r"
            "CARD S\r"
            "PROC MAIN()\r"
            "S=0\r"
            "FOR I=1 TO 3\r"
            "DO\r"
            "S=S+I\r"
            "OD\r"
            "FOR I=65535 TO 65535\r"
            "DO\r"
            "S=S+1\r"
            "OD\r"
            "PrintIE(S)\r"
            "RETURN\r",
            "actc-overlay-native-integer-for-wrap",
        )

        self.assertIn(
            "x main 0 645\n"
            "x __for0 81 1\n"
            "x __fend0 314 1\n"
            "x __for1 365 1\n"
            "x __fend1 595 1\n"
            "x __idata 631 12\n"
            "x __iptr 643 2\n",
            obj,
        )
        self.assertIn("b u0M\nb M\nb M\nb M\nb M\nb M\nb M\n", obj)
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 97 x __fend0\n"
            "r 143 x __fend0\n"
            "r 187 x __fend0\n"
            "r 302 x __fend0\n"
            "r 309 x __fend0\n"
            "r 312 x __for0\n"
            "r 381 x __fend1\n"
            "r 427 x __fend1\n"
            "r 471 x __fend1\n"
            "r 583 x __fend1\n"
            "r 590 x __fend1\n"
            "r 593 x __for1\n"
            "r 608 u0\n"
            "r 643 x __idata\n",
            obj,
        )
        self.assertIn("05 02 D0 03 4C 00 00 A5 03 30 2E", obj)
        self.assertIn(
            "A9 00 69 00 85 02 A0 07 B1 06 30 07 A5 02 F0 0A "
            "4C 00 00 A5 02 D0 03 4C 00 00 4C 00 00",
            obj,
        )
        self.assertIn(
            "L 0 237 0 9 1\n"
            "L 0 314 0 10 1\n"
            "L 0 320 0 10 1\n",
            obj,
        )
        self.assertIn(
            "L 0 518 0 13 1\n"
            "L 0 595 0 14 1\n"
            "L 0 604 0 14 1\n"
            "L 0 615 0 15 1\n",
            obj,
        )
        self.assertNotIn("L 0 768 ", obj)
        self.assertNotIn("F0+", obj)
        self.assertNotIn("F1+", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_nested_for_exit_target(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD I\r"
            "CARD J\r"
            "CARD S\r"
            "PROC MAIN()\r"
            "S=0\r"
            "FOR I=1 TO 2\r"
            "DO\r"
            "FOR J=1 TO 5\r"
            "DO\r"
            "S=S+J\r"
            "EXIT\r"
            "OD\r"
            "S=S+10\r"
            "OD\r"
            "PrintIE(S)\r"
            "RETURN\r",
            "actc-overlay-native-integer-nested-for-exit",
        )

        self.assertIn(
            "x main 0 650\n"
            "x __for0 81 1\n"
            "x __fend0 598 1\n"
            "x __for1 240 1\n"
            "x __fend1 476 1\n"
            "x __idata 634 14\n"
            "x __iptr 648 2\n",
            obj,
        )
        self.assertIn(
            "r 397 x __fend1\n"
            "r 464 x __fend1\n"
            "r 471 x __fend1\n"
            "r 474 x __for1\n"
            "r 586 x __fend0\n"
            "r 593 x __fend0\n"
            "r 596 x __for0\n",
            obj,
        )
        self.assertNotIn("XP", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_dynamic_plain_do_exit(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD I\r"
            "CARD S\r"
            "PROC MAIN()\r"
            "I=0\r"
            "S=0\r"
            "DO\r"
            "I=I+1\r"
            "IF I=3 THEN\r"
            "EXIT\r"
            "FI\r"
            "OD\r"
            "S=I\r"
            "RETURN\r",
            "actc-overlay-native-integer-dynamic-plain-do-exit",
        )

        self.assertIn(
            "x main 0 178\n"
            "x __do0 47 1\n"
            "x __if1 136 1\n"
            "x __if2 133 1\n"
            "x __idata 172 4\n"
            "x __iptr 176 2\n",
            obj,
        )
        self.assertIn(
            "F0 03 4C 00 00 4C 00 00 4C 00 00 A0 00",
            obj,
        )
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 128 x __if2\n"
            "r 131 x __if1\n"
            "r 134 x __do0\n"
            "r 176 x __idata\n",
            obj,
        )
        self.assertNotIn("b p0S0p1S1dL0p2aS0L0p3qhX0voL0S1r\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_dynamic_do_until_exit(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD I\r"
            "CARD S\r"
            "PROC MAIN()\r"
            "I=0\r"
            "S=0\r"
            "DO\r"
            "I=I+1\r"
            "IF I=2 THEN\r"
            "EXIT\r"
            "FI\r"
            "UNTIL I=10\r"
            "OD\r"
            "S=I\r"
            "RETURN\r",
            "actc-overlay-native-integer-dynamic-do-until-exit",
        )

        self.assertIn(
            "x main 0 213\n"
            "x __do0 47 1\n"
            "x __if1 171 1\n"
            "x __if2 133 1\n"
            "x __idata 207 4\n"
            "x __iptr 211 2\n",
            obj,
        )
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 128 x __if2\n"
            "r 131 x __if1\n"
            "r 169 x __do0\n"
            "r 211 x __idata\n",
            obj,
        )
        self.assertIn(
            "L 0 171 0 12 1\n"
            "L 0 171 0 13 1\n"
            "L 0 171 0 14 1\n"
            "L 0 180 0 14 1\n"
            "L 0 191 0 15 1\n",
            obj,
        )
        self.assertNotIn("L 0 256 ", obj)
        self.assertNotIn("b p0S0p1S1dL0p2aS0L0p3qhX0vL0p4qtoL0S1r\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_local_integer_emitter_owns_dynamic_while_add_sub_exit(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD I\r"
            "CARD S\r"
            "PROC MAIN()\r"
            "I=0\r"
            "S=0\r"
            "WHILE I<10 DO\r"
            "I=I+2\r"
            "I=I-1\r"
            "IF I=3 THEN\r"
            "EXIT\r"
            "FI\r"
            "OD\r"
            "S=I\r"
            "RETURN\r",
            "actc-overlay-native-local-integer-dynamic-while-add-sub-exit",
        )

        self.assertIn(
            "x main 0 260\n"
            "x __p0l0 47 1\n"
            "x __p0l1 218 1\n"
            "x __p0l2 215 1\n"
            "x __idata 254 4\n"
            "x __iptr 258 2\n",
            obj,
        )
        self.assertIn(
            "68 85 05 68 85 04 68 85 03 68 18 65 04 48 A5 03 65 05 48",
            obj,
        )
        self.assertIn(
            "68 85 05 68 85 04 68 85 03 68 38 E5 04 48 A5 03 E5 05 48",
            obj,
        )
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 82 x __p0l1\n"
            "r 210 x __p0l2\n"
            "r 213 x __p0l1\n"
            "r 216 x __p0l0\n"
            "r 258 x __idata\n",
            obj,
        )
        self.assertNotIn(
            "b p0S0p1S1dL0p2lfL0p3aS0L0p4mS0L0p5qhX1vxL0S1r\n",
            obj,
        )
        self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_native_local_integer_emitter_owns_dynamic_while_mul_div_exit(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD I\r"
            "CARD S\r"
            "PROC MAIN()\r"
            "I=1\r"
            "S=0\r"
            "WHILE I<20 DO\r"
            "I=I*2\r"
            "I=I/1\r"
            "IF I=6 THEN\r"
            "EXIT\r"
            "FI\r"
            "I=I+1\r"
            "OD\r"
            "S=I\r"
            "RETURN\r",
            "actc-overlay-native-local-integer-dynamic-while-mul-div-exit",
        )

        self.assertIn(
            "x main 0 313\n"
            "x __p0l0 47 1\n"
            "x __p0l1 271 1\n"
            "x __p0l2 223 1\n"
            "x __idata 307 4\n"
            "x __iptr 311 2\n",
            obj,
        )
        self.assertIn("b u0u1M\n", obj)
        self.assertEqual(obj.count("20 00 00 48 8A 48"), 2)
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 82 x __p0l1\n"
            "r 117 u0\n"
            "r 166 u1\n"
            "r 218 x __p0l2\n"
            "r 221 x __p0l1\n"
            "r 269 x __p0l0\n"
            "r 311 x __idata\n",
            obj,
        )
        self.assertIn("u rt_i_mul\nu rt_i_div\n", obj)
        self.assertNotIn("u rt_print_i\n", obj)
        self.assertNotIn(
            "b p0S0p1S1dL0p2lfL0p3*S0L0p4/S0L0p5qhX1vL0p6aS0xL0S1r\n",
            obj,
        )
        self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_native_local_integer_emitter_selects_only_used_math_helper(self) -> None:
        cases = (
            (
                "multiply",
                "I=1\rWHILE I<4 DO\rI=I*2\rOD\r",
                "x main 0 139\nx __p0l0 30 1\nx __p0l1 119 1\n"
                "x __idata 135 2\nx __iptr 137 2\n",
                "r 65 x __p0l1\nr 100 u0\nr 117 x __p0l0\n",
                "rt_i_mul",
                "rt_i_div",
            ),
            (
                "divide",
                "I=8\rWHILE I>1 DO\rI=I/2\rOD\r",
                "x main 0 141\nx __p0l0 30 1\nx __p0l1 121 1\n"
                "x __idata 137 2\nx __iptr 139 2\n",
                "r 67 x __p0l1\nr 102 u0\nr 119 x __p0l0\n",
                "rt_i_div",
                "rt_i_mul",
            ),
        )

        for name, body, exports, relocs, selected, pruned in cases:
            with self.subTest(name=name):
                obj = self.compile_overlay_object(
                    "MODULE MAIN\rCARD I\rPROC MAIN()\r" + body + "RETURN\r",
                    f"actc-overlay-native-local-integer-while-{name}-only",
                )
                self.assertIn(exports, obj)
                self.assertIn("b u0M\n", obj)
                self.assertIn(relocs, obj)
                self.assertIn(f"u {selected}\n", obj)
                self.assertNotIn(f"u {pruned}\n", obj)
                self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_native_local_integer_emitter_prints_inside_while_with_selected_helpers(self) -> None:
        cases = (
            (
                "print-only",
                "I=0\rWHILE I<3 DO\rPrintIE(I)\rI=I+1\rOD\r",
                "x main 0 155\nx __p0l0 30 1\nx __p0l1 135 1\n"
                "x __idata 151 2\nx __iptr 153 2\n",
                "b u0M\n",
                "r 65 x __p0l1\nr 80 u0\nr 133 x __p0l0\n",
                "u rt_print_i\n",
                ("u rt_i_mul\n", "u rt_i_div\n"),
            ),
            (
                "print-and-multiply",
                "I=1\rWHILE I<4 DO\rPrintIE(I)\rI=I*2\rOD\r",
                "x main 0 159\nx __p0l0 30 1\nx __p0l1 139 1\n"
                "x __idata 155 2\nx __iptr 157 2\n",
                "b u0u1M\n",
                "r 65 x __p0l1\nr 80 u0\nr 120 u1\nr 137 x __p0l0\n",
                "u rt_print_i\nu rt_i_mul\n",
                ("u rt_i_div\n",),
            ),
        )

        for name, body, exports, marker, relocs, selected, pruned in cases:
            with self.subTest(name=name):
                obj = self.compile_overlay_object(
                    "MODULE MAIN\rCARD I\rPROC MAIN()\r" + body + "RETURN\r",
                    f"actc-overlay-native-local-integer-while-{name}",
                )
                self.assertIn(exports, obj)
                self.assertIn(marker, obj)
                self.assertIn("68 AA 68 20 00 00 A9 0D 20 D2 FF", obj)
                self.assertIn(relocs, obj)
                self.assertIn(selected, obj)
                for helper in pruned:
                    self.assertNotIn(helper, obj)
                self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_native_local_integer_emitter_calls_external_inside_while(self) -> None:
        cases = (
            (
                "single-procedure",
                "MODULE MAIN\rCARD I\rPROC MAIN()\r"
                "I=0\rWHILE I<1 DO\rHelper()\rI=I+1\rOD\rRETURN\r",
                "x main 0 138\nx __p0l0 30 1\nx __p0l1 118 1\n"
                "x __idata 134 2\nx __iptr 136 2\n",
                "r 65 x __p0l1\nr 68 u0\nr 116 x __p0l0\n",
                1,
            ),
            (
                "multi-procedure",
                "MODULE MAIN\rCARD I\r"
                "PROC A()\rWHILE I<1 DO\rHelper()\rI=I+1\rOD\rRETURN\r"
                "PROC MAIN()\rI=0\rA()\rRETURN\r",
                "x main 0 142\nx a 49 89\nx __p0l0 49 1\n"
                "x __p0l1 137 1\nx __idata 138 2\nx __iptr 140 2\n",
                "r 31 x a\nr 84 x __p0l1\nr 87 u0\nr 135 x __p0l0\n",
                2,
            ),
        )

        for name, source, exports, relocs, import_marker_count in cases:
            with self.subTest(name=name):
                obj = self.compile_overlay_object(
                    source,
                    f"actc-overlay-native-local-integer-while-external-{name}",
                )
                self.assertIn(exports, obj)
                self.assertEqual(obj.count("b u0M\n"), import_marker_count, msg=obj)
                self.assertIn("20 00 00", obj)
                self.assertIn(relocs, obj)
                self.assertEqual(obj.count("u helper\n"), 1)
                self.assertNotIn("b p0S0dL0p1lfu0L0p2aS0xr\n", obj)
                self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_native_local_runtime_emitter_calls_a_byte_helper_inside_while(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD I\r"
            "PROC MAIN()\r"
            "I=0\r"
            "WHILE I<1 DO\r"
            "SidVol(I+10)\r"
            "I=I+1\r"
            "OD\r"
            "RETURN\r",
            "actc-overlay-native-local-runtime-while-a-byte",
        )

        self.assertIn(
            "x main 0 174\n"
            "x __p0l0 30 1\n"
            "x __p0l1 154 1\n"
            "x __idata 170 2\n"
            "x __iptr 172 2\n",
            obj,
        )
        self.assertIn("b u0M\n", obj)
        self.assertIn("68 68 20 00 00", obj)
        self.assertIn(
            "r 65 x __p0l1\n"
            "r 104 u0\n"
            "r 152 x __p0l0\n"
            "r 172 x __idata\n",
            obj,
        )
        self.assertIn("u rt_sid_vol\n", obj)
        self.assertNotIn("b p0S0dL0p1lfL0p2aS0p3u0L0p4aS0xr\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [16])

    def test_native_local_runtime_emitter_calls_xy_word_helper_inside_while(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD I\r"
            "PROC MAIN()\r"
            "I=0\r"
            "WHILE I<1 DO\r"
            "SidCutoff(I+300)\r"
            "I=I+1\r"
            "OD\r"
            "RETURN\r",
            "actc-overlay-native-local-runtime-while-xy-word",
        )

        self.assertIn(
            "x main 0 176\n"
            "x __p0l0 30 1\n"
            "x __p0l1 156 1\n"
            "x __idata 172 2\n"
            "x __iptr 174 2\n",
            obj,
        )
        self.assertIn("b u0M\n", obj)
        self.assertIn("68 A8 68 AA 20 00 00", obj)
        self.assertIn(
            "r 65 x __p0l1\n"
            "r 106 u0\n"
            "r 154 x __p0l0\n"
            "r 174 x __idata\n",
            obj,
        )
        self.assertIn("u rt_sid_cutoff\n", obj)
        self.assertNotIn("b p0S0dL0p1lfL0p2aS0p3U0L0p4aS0xr\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [16])

    def test_native_local_integer_emitter_owns_do_exit_target(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD S\r"
            "PROC MAIN()\r"
            "X=3\r"
            "S=0\r"
            "DO\r"
            "IF X=3 THEN\r"
            "EXIT\r"
            "FI\r"
            "S=99\r"
            "UNTIL X=10\r"
            "OD\r"
            "S=13\r"
            "RETURN\r",
            "actc-overlay-native-integer-do-exit",
        )

        self.assertIn(
            "x main 0 182\n"
            "x __p0l0 47 1\n"
            "x __p0l1 88 1\n"
            "x __p0l2 143 1\n"
            "x __idata 176 4\n"
            "x __iptr 180 2\n",
            obj,
        )
        self.assertIn(
            "r 83 x __p0l1\n"
            "r 86 x __p0l2\n"
            "r 141 x __p0l0\n",
            obj,
        )
        self.assertNotIn("X0", obj)
        self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_native_local_integer_emitter_owns_plain_do_loop(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "PROC MAIN()\r"
            "X=1\r"
            "DO\r"
            "X=2\r"
            "OD\r"
            "RETURN\r",
            "actc-overlay-native-integer-plain-do",
        )

        self.assertIn(
            "x main 0 70\n"
            "x __p0l0 30 1\n"
            "x __idata 66 2\n"
            "x __iptr 68 2\n",
            obj,
        )
        self.assertIn("r 48 x __p0l0\n", obj)
        self.assertNotIn("b p0S0dp1S0or\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_native_local_integer_emitter_owns_plain_do_exit_target(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD S\r"
            "PROC MAIN()\r"
            "X=3\r"
            "S=0\r"
            "DO\r"
            "IF X=3 THEN\r"
            "EXIT\r"
            "FI\r"
            "S=99\r"
            "OD\r"
            "S=13\r"
            "RETURN\r",
            "actc-overlay-native-integer-plain-do-exit",
        )

        self.assertIn(
            "x main 0 147\n"
            "x __p0l0 47 1\n"
            "x __p0l1 88 1\n"
            "x __p0l2 108 1\n"
            "x __idata 141 4\n"
            "x __iptr 145 2\n",
            obj,
        )
        self.assertIn(
            "r 83 x __p0l1\n"
            "r 86 x __p0l2\n"
            "r 106 x __p0l0\n",
            obj,
        )
        self.assertNotIn("X0", obj)
        self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_body_overlay_rejects_malformed_loop_structure(self) -> None:
        self.require_toolchain()
        self.build_actc_emit_overlay_stack()
        bad_sources = {
            "missing_do": (
                "MODULE MAIN\r"
                "CARD I\r"
                "PROC MAIN()\r"
                "FOR I=0 TO 3\r"
                "RETURN\r"
            ),
            "unmatched_od": (
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "OD\r"
                "RETURN\r"
            ),
            "unterminated_for": (
                "MODULE MAIN\r"
                "CARD I\r"
                "PROC MAIN()\r"
                "FOR I=0 TO 3\r"
                "DO\r"
                "RETURN\r"
            ),
            "unmatched_until": (
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "UNTIL 1\r"
                "RETURN\r"
            ),
            "unterminated_do": (
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "DO\r"
                "RETURN\r"
            ),
            "exit_outside_loop": (
                "MODULE MAIN\r"
                "PROC MAIN()\r"
                "EXIT\r"
                "RETURN\r"
            ),
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            for name, source in bad_sources.items():
                with self.subTest(name=name):
                    project_root = Path(tmpdir) / name
                    source_dir = project_root / "src"
                    object_dir = project_root / "obj"
                    source_dir.mkdir(parents=True)
                    object_dir.mkdir()
                    (project_root / "ACTION.PROJ").write_text(
                        "ACTION PROJECT\rMAIN.ACT\r",
                        encoding="ascii",
                    )
                    (source_dir / "main.act").write_text(source, encoding="ascii")
                    result = subprocess.run(
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
                        ],
                        cwd=self.root,
                        text=True,
                        capture_output=True,
                        check=False,
                        timeout=60,
                    )

                    self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                    summary = json.loads(result.stdout)
                    self.assertNotEqual(summary["exit_status"], 0, msg=result.stdout)
                    self.assertFalse(summary["hit_limit"], msg=result.stdout)
                    self.assertIn("BAD PROC", summary["console"], msg=result.stdout)
                    self.assertFalse((object_dir / "MAIN.OBJ").exists())

    def test_native_local_integer_emitter_owns_while_equality(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "PROC MAIN()\r"
            "X=0\r"
            "WHILE X=0 DO\r"
            "X=1\r"
            "OD\r"
            "RETURN\r",
            "actc-overlay-native-local-integer-while-equality",
        )

        self.assertIn(
            "x main 0 108\n"
            "x __p0l0 30 1\n"
            "x __p0l1 88 1\n"
            "x __idata 104 2\n"
            "x __iptr 106 2\n",
            obj,
        )
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 66 x __p0l1\n"
            "r 86 x __p0l0\n"
            "r 106 x __idata\n",
            obj,
        )
        self.assertNotIn("b p0S0dL0p0qfp1S0xr\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_native_local_integer_emitter_owns_while_exit_target(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "PROC MAIN()\r"
            "X=0\r"
            "WHILE X=0 DO\r"
            "EXIT\r"
            "OD\r"
            "X=7\r"
            "RETURN\r",
            "actc-overlay-native-local-integer-while-exit",
        )

        self.assertIn(
            "x main 0 111\n"
            "x __p0l0 30 1\n"
            "x __p0l1 74 1\n"
            "x __idata 107 2\n"
            "x __iptr 109 2\n",
            obj,
        )
        self.assertIn(
            "r 66 x __p0l1\n"
            "r 69 x __p0l1\n"
            "r 72 x __p0l0\n",
            obj,
        )
        self.assertNotIn("XC", obj)
        self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_native_local_integer_emitter_owns_direct_ordered_while_conditions(self) -> None:
        cases = (
            (
                "not-equal",
                "X=0\rWHILE X<>1 DO\rX=1\r",
                "x main 0 108\nx __p0l0 30 1\nx __p0l1 88 1\n"
                "x __idata 104 2\nx __iptr 106 2\n",
                "68 85 05 68 85 04 68 85 03 68 C5 04 D0 09 "
                "A5 03 C5 05 D0 03 4C 00 00",
                "r 3 x __iptr\nr 9 x __iptr\nr 66 x __p0l1\n"
                "r 86 x __p0l0\nr 106 x __idata\n",
                "b p0S0dL0p1nfp1S0xr\n",
            ),
            (
                "less-than",
                "X=0\rWHILE X<1 DO\rX=1\r",
                "x main 0 107\nx __p0l0 30 1\nx __p0l1 87 1\n"
                "x __idata 103 2\nx __iptr 105 2\n",
                "68 85 05 68 85 04 68 AA 68 E4 05 90 09 D0 04 "
                "C5 04 90 03 4C 00 00",
                "r 3 x __iptr\nr 9 x __iptr\nr 65 x __p0l1\n"
                "r 85 x __p0l0\nr 105 x __idata\n",
                "b p0S0dL0p1lfp1S0xr\n",
            ),
            (
                "greater-than",
                "X=1\rWHILE X>0 DO\rX=0\r",
                "x main 0 109\nx __p0l0 30 1\nx __p0l1 89 1\n"
                "x __idata 105 2\nx __iptr 107 2\n",
                "68 85 05 68 85 04 68 AA 68 E4 05 90 08 D0 09 "
                "C5 04 90 02 D0 03 4C 00 00",
                "r 3 x __iptr\nr 9 x __iptr\nr 67 x __p0l1\n"
                "r 87 x __p0l0\nr 107 x __idata\n",
                "b p1S0dL0p0gfp0S0xr\n",
            ),
        )

        for name, body, exports, machine, relocs, compact_body in cases:
            with self.subTest(name=name):
                obj = self.compile_overlay_object(
                    "MODULE MAIN\rCARD X\rPROC MAIN()\r" + body + "OD\rRETURN\r",
                    f"actc-overlay-native-local-integer-while-{name}",
                )
                self.assertIn(exports, obj)
                self.assertIn(machine, obj)
                self.assertIn(relocs, obj)
                self.assertNotIn(compact_body, obj)
                self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_native_local_integer_emitter_owns_inclusive_ordered_while_conditions(self) -> None:
        cases = (
            (
                "greater-equal",
                "X=1\rWHILE X>=1 DO\rX=0\r",
                "x main 0 107\nx __p0l0 30 1\nx __p0l1 87 1\n"
                "x __idata 103 2\nx __iptr 105 2\n",
                "68 85 05 68 85 04 68 AA 68 E4 05 90 06 D0 07 "
                "C5 04 B0 03 4C 00 00",
                "r 3 x __iptr\nr 9 x __iptr\nr 65 x __p0l1\n"
                "r 85 x __p0l0\nr 105 x __idata\n",
                "b p0S0dL0p1lp2qfp3S0xr\n",
            ),
            (
                "less-equal",
                "X=0\rWHILE X<=0 DO\rX=1\r",
                "x main 0 109\nx __p0l0 30 1\nx __p0l1 89 1\n"
                "x __idata 105 2\nx __iptr 107 2\n",
                "68 85 05 68 85 04 68 AA 68 E4 05 90 0B D0 06 "
                "C5 04 90 05 F0 03 4C 00 00",
                "r 3 x __iptr\nr 9 x __iptr\nr 67 x __p0l1\n"
                "r 87 x __p0l0\nr 107 x __idata\n",
                "b p0S0dL0p1gp2qfp3S0xr\n",
            ),
        )

        for name, body, exports, machine, relocs, compact_body in cases:
            with self.subTest(name=name):
                obj = self.compile_overlay_object(
                    "MODULE MAIN\rCARD X\rPROC MAIN()\r" + body + "OD\rRETURN\r",
                    f"actc-overlay-native-local-integer-while-{name}",
                )
                self.assertIn(exports, obj)
                self.assertIn(machine, obj)
                self.assertIn(relocs, obj)
                self.assertNotIn(compact_body, obj)
                self.assertEqual(self.last_emit_overlay_pass, [9])

    def test_native_integer_emitter_owns_nested_do_until_equality(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "X=0\r"
            "Y=0\r"
            "DO\r"
            "X=1\r"
            "DO\r"
            "Y=2\r"
            "UNTIL Y=2\r"
            "OD\r"
            "UNTIL X=1\r"
            "OD\r"
            "RETURN\r",
            "actc-overlay-native-integer-nested-do-until-equality",
        )

        self.assertIn(
            "x main 0 179\n"
            "x __do0 47 1\n"
            "x __do1 64 1\n"
            "x __idata 173 4\n"
            "x __iptr 177 2\n",
            obj,
        )
        self.assertIn("b M\nb M\nb M\nb M\nb M\n", obj)
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 117 x __do1\n"
            "r 155 x __do0\n"
            "r 177 x __idata\n",
            obj,
        )
        self.assertNotIn("b p0S0p1S1dp2S0dp3S1L1p4qtoL0p5qtor\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_do_if_until_equality(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "X=0\r"
            "Y=0\r"
            "DO\r"
            "X=1\r"
            "IF X=1 THEN\r"
            "Y=2\r"
            "FI\r"
            "UNTIL Y=2\r"
            "OD\r"
            "RETURN\r",
            "actc-overlay-native-integer-do-if-until-equality",
        )

        self.assertIn(
            "x main 0 179\n"
            "x __do0 47 1\n"
            "x __if2 119 1\n"
            "x __idata 173 4\n"
            "x __iptr 177 2\n",
            obj,
        )
        self.assertIn("b M\nb M\nb M\nb M\nb M\n", obj)
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 100 x __if2\n"
            "r 155 x __do0\n"
            "r 177 x __idata\n",
            obj,
        )
        self.assertNotIn("b p0S0p1S1dp2S0L0p3qhp4S1vL1p5qtor\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_do_if_else_until_equality(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "X=0\r"
            "Y=0\r"
            "DO\r"
            "X=1\r"
            "IF X=2 THEN\r"
            "Y=3\r"
            "ELSE\r"
            "Y=4\r"
            "FI\r"
            "UNTIL Y=4\r"
            "OD\r"
            "RETURN\r",
            "actc-overlay-native-integer-do-if-else-until-equality",
        )

        self.assertIn(
            "x main 0 199\n"
            "x __do0 47 1\n"
            "x __if2 122 1\n"
            "x __if3 139 1\n"
            "x __idata 193 4\n"
            "x __iptr 197 2\n",
            obj,
        )
        self.assertIn("b M\nb M\nb M\nb M\nb M\nb M\n", obj)
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 100 x __if2\n"
            "r 120 x __if3\n"
            "r 175 x __do0\n"
            "r 197 x __idata\n",
            obj,
        )
        self.assertNotIn("b p0S0p1S1dp2S0L0p3qhp4S1wp5S1vL1p6qtor\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_if_do_until_equality(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "X=1\r"
            "Y=0\r"
            "IF X=1 THEN\r"
            "DO\r"
            "Y=2\r"
            "UNTIL Y=2\r"
            "OD\r"
            "FI\r"
            "RETURN\r",
            "actc-overlay-native-integer-if-do-until-equality",
        )

        self.assertIn(
            "x main 0 162\n"
            "x __if0 140 1\n"
            "x __do1 85 1\n"
            "x __idata 156 4\n"
            "x __iptr 160 2\n",
            obj,
        )
        self.assertIn("b M\nb M\nb M\nb M\nb M\n", obj)
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 83 x __if0\n"
            "r 138 x __do1\n"
            "r 160 x __idata\n",
            obj,
        )
        self.assertNotIn("b p0S0p1S1L0p2qhdp3S1L1p4qtovr\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_emitter_owns_if_else_do_until_equality(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "X=1\r"
            "Y=0\r"
            "IF X=2 THEN\r"
            "DO\r"
            "Y=3\r"
            "UNTIL Y=3\r"
            "OD\r"
            "ELSE\r"
            "DO\r"
            "Y=4\r"
            "UNTIL Y=4\r"
            "OD\r"
            "FI\r"
            "RETURN\r",
            "actc-overlay-native-integer-if-else-do-until-equality",
        )

        self.assertIn(
            "x main 0 220\n"
            "x __if0 143 1\n"
            "x __if1 198 1\n"
            "x __do1 85 1\n"
            "x __if3 143 1\n"
            "x __idata 214 4\n"
            "x __iptr 218 2\n",
            obj,
        )
        self.assertIn("b M\nb M\nb M\nb M\nb M\nb M\nb M\n", obj)
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 83 x __if0\n"
            "r 138 x __do1\n"
            "r 141 x __if1\n"
            "r 196 x __if3\n"
            "r 218 x __idata\n",
            obj,
        )
        self.assertNotIn("b p0S0p1S1L0p2qhdp3S1L1p4qtowdp5S1L1p6qtovr\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

    def test_native_integer_relocation_scan_continues_after_if(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD X\r"
            "PROC MAIN()\r"
            "X=1\r"
            "IF X=1 THEN\r"
            "X=2\r"
            "FI\r"
            "ExtCall()\r"
            "RETURN\r",
            "actc-overlay-native-integer-post-if-import",
        )

        self.assertIn("x main 0 108\nx __if0 85 1\n", obj)
        self.assertIn("b u0M\n", obj)
        self.assertIn("r 66 x __if0\nr 86 u0\nr 106 x __idata\n", obj)
        self.assertIn("u extcall\n", obj)
        self.assertEqual(self.last_emit_overlay_pass, [8])

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
            "OD\r"
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
                "OD\r"
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
                "OD\r"
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
                "OD\r"
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
                "OD\r"
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
                "OD\r"
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
            "OD\r"
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
            "REAL S\r"
            "REAL T\r"
            "REAL U\r"
            "REAL V\r"
            "REAL W\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "R=FABS(A)\r"
            "Q=FSQRT(A)\r"
            "S=FSIGN(A)\r"
            "T=FTRUNC(A)\r"
            "U=FFLOOR(A)\r"
            "V=FCEIL(A)\r"
            "W=FROUND(A)\r"
            "X=FFRAC(A)\r"
            "RETURN\r",
            "actc-overlay-preallocation-body-mode-real-unary-assignments",
            {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        runtime_imports = (
            "rt_f_abs",
            "rt_f_sqrt",
            "rt_f_sign",
            "rt_f_trunc",
            "rt_f_floor",
            "rt_f_ceil",
            "rt_f_round",
            "rt_f_frac",
        )
        for runtime_import in runtime_imports:
            self.assertIn(f"u {runtime_import}\n", obj)
        for earlier, later in zip(runtime_imports, runtime_imports[1:]):
            self.assertLess(obj.index(f"u {earlier}\n"), obj.index(f"u {later}\n"), msg=obj)
        self.assertNotIn("u fabs\n", obj)
        self.assertNotIn("u fsqrt\n", obj)
        self.assertNotIn("u ffloor\n", obj)
        self.assertNotIn("u fceil\n", obj)
        self.assertNotIn("u fround\n", obj)
        self.assertNotIn("u ffrac\n", obj)

    def test_actc_preallocation_body_overlay_mode_maps_real_binary_assignments(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL R\r"
            "REAL Q\r"
            "REAL M\r"
            "REAL H\r"
            "PROC MAIN()\r"
            "R=A+B\r"
            "Q=A/B\r"
            "M=FMOD(A,B)\r"
            "H=FHYPOT(A,B)\r"
            "RETURN\r",
            "actc-overlay-preallocation-body-mode-real-binary-assignments",
            {"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        runtime_imports = ("rt_f_add", "rt_f_div", "rt_f_mod", "rt_f_hypot")
        for runtime_import in runtime_imports:
            self.assertIn(f"u {runtime_import}\n", obj)
        self.assertLess(obj.index("u rt_f_add\n"), obj.index("u rt_f_div\n"), msg=obj)
        self.assertLess(obj.index("u rt_f_div\n"), obj.index("u rt_f_mod\n"), msg=obj)
        self.assertLess(obj.index("u rt_f_mod\n"), obj.index("u rt_f_hypot\n"), msg=obj)

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
        self.assertFalse(
            any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVLI.BIN" for op in self.last_overlay_ops)
        )

    def test_actc_compile_path_preprocesses_define_and_set(self) -> None:
        obj = self.compile_overlay_object(
            "DEFINE WORD=\"CARD\", ONE=1,\r"
            " DOUBLE=\"ONE+ONE\"\r"
            "SET $49A=1\r"
            "MODULE MAIN\r"
            "WORD VALUE=DOUBLE\r"
            "PROC MAIN()\r"
            "VALUE=double\r"
            "RETURN\r",
            "actc-overlay-define-set-preprocess",
        )

        self.assertIn("v value 2\n", obj)
        self.assertNotIn("u word\n", obj)
        self.assertNotIn("u one\n", obj)
        self.assertNotIn("u double\n", obj)

    def test_actc_compile_path_preprocesses_nested_library_includes(self) -> None:
        obj = self.compile_overlay_object(
            'INCLUDE "wrap"\r'
            "PROC MAIN()\r"
            "VALUE=DOUBLE\r"
            "RETURN\r",
            "actc-overlay-nested-include-preprocess",
            additional_library_sources={
                "base.act": "MODULE MAIN\rCARD VALUE=0\r",
                "wrap.act": (
                    'INCLUDE "base.act"\r'
                    'DEFINE ONE=1, DOUBLE="ONE+ONE"\r'
                ),
            },
        )

        self.assertIn("A9 02 48 A9 00 48", obj)
        self.assertIn("v value 0\n", obj)
        self.assertNotIn("u double\n", obj)

    def test_actc_compile_path_define_substitution_is_token_aware(self) -> None:
        obj = self.compile_overlay_object(
            "DEFINE X=1\r"
            "MODULE MAIN\r"
            "CARD XTRA=2\r"
            "; X remains comment text\r"
            "PROC DATA=*()\r"
            "['X' X $60]\r"
            "PROC MAIN()\r"
            "DATA()\r"
            "RETURN\r",
            "actc-overlay-define-token-aware",
        )

        self.assertIn("v xtra 2\n", obj)
        self.assertIn("58 01 60 02 00", obj)

    def test_actc_compile_path_include_prefers_project_source(self) -> None:
        obj = self.compile_overlay_object(
            'INCLUDE "base"\rPROC MAIN()\rRETURN\r',
            "actc-overlay-include-source-precedence",
            additional_sources={"base.act": "MODULE MAIN\rCARD VALUE=1\r"},
            additional_library_sources={"base.act": "MODULE MAIN\rCARD VALUE=2\r"},
        )

        self.assertIn("v value 1\n", obj)
        self.assertNotIn("v value 2\n", obj)

    def test_actc_compile_path_preprocesses_typed_constants(self) -> None:
        obj = self.compile_overlay_object(
            "CARD CONST OUTPUT_ADDR=$C130,\r"
            " VALUE=7\r"
            "CARD CONST SHIFTED=VALUE LSH 4\r"
            "INT CONST NEG=-2\r"
            "MODULE MAIN\r"
            "CARD OUTPUT=OUTPUT_ADDR\r"
            "CARD VALUE_OUT=VALUE\r"
            "CARD SHIFT_OUT=SHIFTED\r"
            "INT NEG_OUT=NEG\r"
            "PROC MAIN()\r"
            "RETURN\r",
            "actc-overlay-typed-constants",
        )

        self.assertIn("v output 49456\n", obj)
        self.assertIn("v value_out 7\n", obj)
        self.assertIn("v shift_out 112\n", obj)
        self.assertIn("v neg_out 65534\n", obj)
        for constant in ("output_addr", "value", "shifted", "neg"):
            self.assertNotIn(f"v {constant} ", obj)

    def test_actc_compile_path_folds_idun_integer_constant_grammar(self) -> None:
        source = (self.root / "tests" / "parity" / "const_expr.act").read_text(
            encoding="ascii"
        ).replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-idun-integer-constant-grammar",
        )

        expected_values = {
            "precedence_out": 14,
            "grouped_out": 20,
            "divmod_out": 16,
            "shift_out": 256,
            "bits_out": 193,
            "signed_out": 65526,
            "remainder_out": 65534,
            "character_out": 66,
            "chex_out": 0x1234,
            "mixed_out": 2,
            "mask_out": 0xFFFF,
            "wide_out": 0xFFFF,
            "high_out": 0x8000,
            "negshift_out": 0xFFFF,
            "buttons_out": 0x11,
        }
        for name, value in expected_values.items():
            self.assertIn(f"v {name} {value}\n", obj)

    def test_actc_compile_path_matches_idun_builtin_constant_redefinition(self) -> None:
        obj = self.compile_overlay_object(
            "BYTE CONST JOY_UP=$01\r"
            "MODULE MAIN\r"
            "BYTE RESULT=JOY_UP\r"
            "PROC MAIN()\r"
            "RETURN\r",
            "actc-overlay-same-builtin-constant",
        )
        self.assertIn("v result 1\n", obj)

        console = self.compile_overlay_object(
            "BYTE CONST JOY_UP=$02\rMODULE MAIN\rPROC MAIN()\rRETURN\r",
            "actc-overlay-changed-builtin-constant",
            expected_exit_status=1,
        )
        self.assertIn("BAD CONST", console)

    def test_actc_compile_path_rejects_invalid_idun_constant_expressions(self) -> None:
        cases = {
            "division-zero": "1/0",
            "shift-range": "1 LSH 63",
            "signed-overflow": "(1 LSH 62)*2",
            "signed-add-overflow": "9223372036854775807+1",
            "signed-sub-underflow": "((1 LSH 62) LSH 1)-1",
            "signed-div-overflow": "((1 LSH 62) LSH 1)/-1",
            "signed-mod-overflow": "((1 LSH 62) LSH 1) MOD -1",
            "unclosed-group": "(1+2",
            "trailing-operator": "1+",
        }
        for name, expression in cases.items():
            with self.subTest(name=name):
                console = self.compile_overlay_object(
                    f"CARD CONST BAD={expression}\r"
                    "MODULE MAIN\rPROC MAIN()\rRETURN\r",
                    f"actc-overlay-constant-{name}",
                    expected_exit_status=1,
                )
                self.assertIn("CONST RANGE", console)

    def test_actc_compile_path_preprocesses_typed_constants_after_module(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "CARD CONST OUTPUT_ADDR=$C130\r"
            "CHAR CONST MARK=65\r"
            "CARD OUTPUT=OUTPUT_ADDR\r"
            "BYTE MARK_OUT=MARK\r"
            "PROC MAIN()\r"
            "RETURN\r",
            "actc-overlay-post-module-typed-constants",
        )

        self.assertIn("v output 49456\n", obj)
        self.assertIn("v mark_out 65\n", obj)
        self.assertNotIn("v output_addr ", obj)
        self.assertNotIn("v mark ", obj)

    def test_actc_compile_path_preprocesses_define_after_module(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            'DEFINE WORD="CARD", VALUE=7\r'
            "WORD OUTPUT=VALUE\r"
            "PROC MAIN()\r"
            "RETURN\r",
            "actc-overlay-post-module-define",
        )

        self.assertIn("v output 7\n", obj)
        self.assertNotIn("u word\n", obj)
        self.assertNotIn("v value ", obj)
        self.assertTrue(
            any(
                op["kind"] == "rsta"
                and op["path"] == "!ACTC_OVLI.BIN"
                and op["status"] == 1
                for op in self.last_overlay_ops
            )
        )

    def test_actc_compile_path_preprocesses_real_constant_text(self) -> None:
        obj = self.compile_overlay_object(
            "REAL CONST SCALE=3\r"
            "MODULE MAIN\r"
            "REAL RESULT\r"
            "PROC MAIN()\r"
            "RESULT=REAL(SCALE)\r"
            "RETURN\r",
            "actc-overlay-real-constant",
        )

        self.assertNotIn("u rt_i_to_f\n", obj)
        self.assertNotIn("u realbits\n", obj)
        self.assertIn("i 0\n", obj)
        self.assertIn("i 16448\n", obj)
        self.assertRegex(obj, r"(?m)^b p\w+p\w+T0S0r$")
        self.assertIn("v result 0 4\n", obj)
        self.assertNotIn("v scale ", obj)

    def test_actc_compile_path_folds_real_constant_expressions_to_binary32(self) -> None:
        obj = self.compile_overlay_object(
            "REAL CONST A=1.5\r"
            "REAL CONST B=(A+2.25)*2.0\r"
            "REAL CONST C=FSQRT(9.0)\r"
            "REAL CONST D=FABS(-0.0)\r"
            "REAL CONST E=1.0/0.0\r"
            "REAL CONST F=0.0/0.0\r"
            "REAL CONST G=1.0+2.0*3.0\r"
            "REAL CONST H=(1.0+2.0)*3.0\r"
            "MODULE MAIN\r"
            "REAL RA\rREAL RB\rREAL RC\rREAL RD\r"
            "REAL RE\rREAL RF\rREAL RG\rREAL RH\r"
            "PROC MAIN()\r"
            "RA=A\rRB=B\rRC=C\rRD=D\rRE=E\rRF=F\rRG=G\rRH=H\r"
            "RETURN\r",
            "actc-overlay-real-constant-expressions",
        )

        for value in (0, 16320, 16624, 16448, 32640, 32704, 16608, 16656):
            self.assertIn(f"i {value}\n", obj)
        for symbol in (
            "realbits",
            "rt_i_to_f",
            "rt_f_add",
            "rt_f_mul",
            "rt_f_div",
            "rt_f_abs",
            "rt_f_sqrt",
        ):
            self.assertNotIn(f"u {symbol}\n", obj)

    def test_actc_compile_path_rounds_real_constant_decimal_edges_to_even(self) -> None:
        obj = self.compile_overlay_object(
            "REAL CONST MIN=1.401298464324817e-45\r"
            "REAL CONST HALFMIN=7.006492321624085e-46\r"
            "REAL CONST ABOVEHALF=7.006492321624086e-46\r"
            "REAL CONST MAX=3.4028234663852886e38\r"
            "REAL CONST OVER=3.4028236e38\r"
            "REAL CONST NEGZERO=-0.0\r"
            "REAL CONST TIE0=1.000000059604644775390625\r"
            "REAL CONST TIE2=1.000000178813934326171875\r"
            "MODULE MAIN\r"
            "REAL R0\rREAL R1\rREAL R2\rREAL R3\r"
            "REAL R4\rREAL R5\rREAL R6\rREAL R7\r"
            "PROC MAIN()\r"
            "R0=MIN\rR1=HALFMIN\rR2=ABOVEHALF\rR3=MAX\r"
            "R4=OVER\rR5=NEGZERO\rR6=TIE0\rR7=TIE2\r"
            "RETURN\r",
            "actc-overlay-real-constant-rounding",
        )

        for value in (0, 1, 2, 16256, 32639, 32640, 32768, 65535):
            self.assertIn(f"i {value}\n", obj)
        self.assertNotRegex(obj, r"(?m)^u (?:realbits|rt_f_|rt_i_to_f)")

    def test_actc_compile_path_rejects_malformed_real_constant_expression(self) -> None:
        console = self.compile_overlay_object(
            "REAL CONST BAD=1.0+\rMODULE MAIN\rPROC MAIN()\rRETURN\r",
            "actc-overlay-real-constant-malformed",
            expected_exit_status=1,
        )

        self.assertIn("BAD CONST", console)

    def test_actc_compile_path_rejects_typed_constant_range(self) -> None:
        console = self.compile_overlay_object(
            "BYTE CONST TOO_BIG=256\rMODULE MAIN\rPROC MAIN()\rRETURN\r",
            "actc-overlay-typed-constant-range",
            expected_exit_status=1,
        )

        self.assertIn("CONST RANGE", console)

    def test_actc_compile_path_packs_complete_library_constant_headers(self) -> None:
        source = (self.root / "tests" / "parity" / "library_const_headers.act").read_text(
            encoding="ascii"
        )
        obj = self.compile_overlay_object(
            source.replace("\n", "\r"),
            "actc-overlay-library-constant-headers",
        )

        self.assertIn("v result 15\n", obj)
        self.assertNotIn("v gfx_black ", obj)
        self.assertNotIn("v math_pi ", obj)

    def test_actc_compile_path_includes_native_math1_constants_without_runtime_imports(self) -> None:
        source = (
            self.root / "tests" / "parity" / "math1_constants_include.act"
        ).read_text(encoding="ascii")
        math1 = (self.root / "lib" / "math1.act").read_text(encoding="ascii")
        obj = self.compile_overlay_object(
            source.replace("\n", "\r"),
            "actc-overlay-math1-constants-include",
            additional_library_sources={"math1.act": math1.replace("\n", "\r")},
        )

        self.assertNotIn("MODULE MATH1", math1)
        self.assertIn("i 4059\n", obj)
        self.assertIn("i 16457\n", obj)
        self.assertIn("v result 0 4\n", obj)
        self.assertNotRegex(obj, r"(?m)^u ")

    def test_actc_compile_path_updates_packed_definition_values(self) -> None:
        obj = self.compile_overlay_object(
            "DEFINE VALUE=1\r"
            "DEFINE VALUE=123456789\r"
            "DEFINE VALUE=2\r"
            "MODULE MAIN\r"
            "BYTE RESULT=[VALUE]\r"
            "PROC MAIN()\r"
            "RETURN\r",
            "actc-overlay-packed-definition-update",
        )

        self.assertIn("v result 2\n", obj)

    def test_actc_compile_path_rejects_define_store_overflow(self) -> None:
        long_value = "A" * 64
        definitions = "".join(
            f'DEFINE D{index:023d}="{long_value}"\r' for index in range(15)
        )
        console = self.compile_overlay_object(
            f"{definitions}MODULE MAIN\rPROC MAIN()\rRETURN\r",
            "actc-overlay-define-capacity",
            expected_exit_status=1,
        )

        self.assertIn("DEFINE LIMIT", console)

    def test_actc_compile_path_rejects_include_cycle(self) -> None:
        console = self.compile_overlay_object(
            'INCLUDE "a.act"\rPROC MAIN()\rRETURN\r',
            "actc-overlay-include-cycle",
            additional_library_sources={
                "a.act": 'INCLUDE "b.act"\r',
                "b.act": 'INCLUDE "a.act"\r',
            },
            expected_exit_status=1,
        )

        self.assertIn("INCLUDE CYCLE", console)

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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            object_path = object_dir / "MAIN.OBJ"
            if not object_path.is_file():
                object_path = object_dir / "main.obj"
            obj = object_path.read_text(encoding="ascii")
            self.assertIn("k 7\n", obj)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
                "OD\r"
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
                "OD\r"
                "DO\r"
                "UNTIL LeftUntil(LUntilArg(1)) AND RightUntil(RUntilArg(2))\r"
                "OD\r"
                "DO\r"
                "UNTIL NOT(UntilNotLeft(UNLArg(1)) OR UntilNotRight(UNRArg(2)))\r"
                "OD\r"
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
                "OD\r"
                "DO\r"
                "UNTIL (ChainUntilLeft(CULArg(1))>=ChainUntilRight(CURArg(2))) OR ChainUntilTail(CUTArg(3))=ChainUntilEnd(CUEArg(4))\r"
                "OD\r"
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [10], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVLA.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn("x main 0 58\nx __idata 52 4\nx __iptr 56 2\n", obj)
            self.assertIn("b u0u1M\nb M\nb M\n", obj)
            self.assertIn("r 18 u0\n", obj)
            self.assertIn("r 34 u1\n", obj)
            self.assertIn("r 56 x __idata\n", obj)
            self.assertIn("L 0 0 0 4 1\n", obj)
            self.assertNotIn("b p1u0T0S0L0U0p2u1r\n", obj)
            self.assertIn("u rt_i_to_f\n", obj)
            self.assertIn("u rt_print_f\n", obj)

    def test_native_real_emitter_owns_unary_prints(self) -> None:
        cases = (
            (
                "fabs",
                "A=REAL(0-7)\rX=FAbs(A)\r",
                "rt_s_to_f",
                "rt_f_abs",
                "F9",
                "FF",
                "p0u0T0S0L0U0u1T1S1L1U1p1u2r",
            ),
            (
                "fsqrt",
                "A=REAL(256)\rX=FSqrt(A)\r",
                "rt_i_to_f",
                "rt_f_sqrt",
                "00",
                "01",
                "p1u0T0S0L0U0u1T1S1L1U1p2u2r",
            ),
            (
                "fsign",
                "A=REAL(0-7)\rX=FSign(A)\r",
                "rt_s_to_f",
                "rt_f_sign",
                "F9",
                "FF",
                "p0u0T0S0L0U0u1T1S1L1U1p1u2r",
            ),
            (
                "ftrunc",
                "A=REAL(7)\rX=FTrunc(A)\r",
                "rt_i_to_f",
                "rt_f_trunc",
                "07",
                "00",
                "p1u0T0S0L0U0u1T1S1L1U1p2u2r",
            ),
            (
                "ffloor",
                "A=REAL(0-7)\rX=FFloor(A)\r",
                "rt_s_to_f",
                "rt_f_floor",
                "F9",
                "FF",
                "p0u0T0S0L0U0u1T1S1L1U1p1u2r",
            ),
            (
                "fceil",
                "A=REAL(7)\rX=FCeil(A)\r",
                "rt_i_to_f",
                "rt_f_ceil",
                "07",
                "00",
                "p1u0T0S0L0U0u1T1S1L1U1p2u2r",
            ),
            (
                "fround",
                "A=REAL(7)\rX=FRound(A)\r",
                "rt_i_to_f",
                "rt_f_round",
                "07",
                "00",
                "p1u0T0S0L0U0u1T1S1L1U1p2u2r",
            ),
            (
                "ffrac",
                "A=REAL(7)\rX=FFrac(A)\r",
                "rt_i_to_f",
                "rt_f_frac",
                "07",
                "00",
                "p1u0T0S0L0U0u1T1S1L1U1p2u2r",
            ),
        )
        for name, statements, convert_module, unary_module, value_lo, value_hi, compact_body in cases:
            with self.subTest(name=name):
                obj = self.compile_overlay_object(
                    "MODULE MAIN\r"
                    "REAL A\r"
                    "REAL X\r"
                    "PROC MAIN()\r"
                    f"{statements}"
                    "PrintRE(X)\r"
                    "RETURN\r",
                    f"actc-overlay-native-real-{name}",
                )

                self.assertEqual(self.last_emit_overlay_pass, [10])
                self.assertIn(
                    "x main 0 93\n"
                    "x __idata 81 8\n"
                    "x __ireala 81 4\n"
                    "x __irealx 85 4\n"
                    "x __iptr 89 4\n",
                    obj,
                )
                self.assertIn("b u0u1u2M\nb M\nb M\nb M\nb M\n", obj)
                self.assertIn(
                    "m A2 00 BD 00 00 85 02 E8 BD 00 00 85 03 "
                    f"A9 {value_lo} A2 {value_hi} 20 00 00 ",
                    obj,
                )
                self.assertIn(
                    "r 3 x __iptr\n"
                    "r 9 x __iptr\n"
                    "r 18 u0\n"
                    "r 23 x __iptr\n"
                    "r 29 x __iptr\n"
                    "r 36 x __iptr\n"
                    "r 42 x __iptr\n"
                    "r 47 u1\n"
                    "r 52 x __iptr\n"
                    "r 58 x __iptr\n"
                    "r 63 u2\n"
                    "r 89 x __ireala\n"
                    "r 91 x __irealx\n",
                    obj,
                )
                self.assertIn(f"u {convert_module}\n", obj)
                self.assertIn(f"u {unary_module}\n", obj)
                self.assertIn("u rt_print_f\n", obj)
                self.assertNotIn(f"b {compact_body}\n", obj)

        position_cases = (
            (
                "print-position",
                "MODULE MAIN\rREAL A\rPROC MAIN()\r"
                "A=REAL(7)\rPrintRE(FSign(A))\rRETURN\r",
                ("rt_f_sign", "rt_print_f"),
            ),
            (
                "condition-position",
                "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\r"
                "A=REAL(0-7)\rB=REAL(0)\r"
                "IF FSign(A)<B THEN\rPrintE(\"OK\")\rFI\rRETURN\r",
                ("rt_f_sign", "rt_f_cmp"),
            ),
            (
                "trunc-print-position",
                "MODULE MAIN\rREAL A\rPROC MAIN()\r"
                "A=REAL(7)\rPrintRE(FTrunc(A))\rRETURN\r",
                ("rt_f_trunc", "rt_print_f"),
            ),
            (
                "trunc-condition-position",
                "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\r"
                "A=REAL(7)\rB=REAL(8)\r"
                "IF FTrunc(A)<B THEN\rPrintE(\"OK\")\rFI\rRETURN\r",
                ("rt_f_trunc", "rt_f_cmp"),
            ),
            (
                "floor-print-position",
                "MODULE MAIN\rREAL A\rPROC MAIN()\r"
                "A=REAL(0-7)\rPrintRE(FFloor(A))\rRETURN\r",
                ("rt_f_floor", "rt_print_f"),
            ),
            (
                "floor-condition-position",
                "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\r"
                "A=REAL(0-7)\rB=REAL(0)\r"
                "IF FFloor(A)<B THEN\rPrintE(\"OK\")\rFI\rRETURN\r",
                ("rt_f_floor", "rt_f_cmp"),
            ),
            (
                "ceil-print-position",
                "MODULE MAIN\rREAL A\rPROC MAIN()\r"
                "A=REAL(7)\rPrintRE(FCeil(A))\rRETURN\r",
                ("rt_f_ceil", "rt_print_f"),
            ),
            (
                "ceil-condition-position",
                "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\r"
                "A=REAL(7)\rB=REAL(8)\r"
                "IF FCeil(A)<B THEN\rPrintE(\"OK\")\rFI\rRETURN\r",
                ("rt_f_ceil", "rt_f_cmp"),
            ),
            (
                "round-print-position",
                "MODULE MAIN\rREAL A\rPROC MAIN()\r"
                "A=REAL(7)\rPrintRE(FRound(A))\rRETURN\r",
                ("rt_f_round", "rt_print_f"),
            ),
            (
                "round-condition-position",
                "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\r"
                "A=REAL(7)\rB=REAL(8)\r"
                "IF FRound(A)<B THEN\rPrintE(\"OK\")\rFI\rRETURN\r",
                ("rt_f_round", "rt_f_cmp"),
            ),
            (
                "frac-print-position",
                "MODULE MAIN\rREAL A\rPROC MAIN()\r"
                "A=REAL(7)\rPrintRE(FFrac(A))\rRETURN\r",
                ("rt_f_frac", "rt_print_f"),
            ),
            (
                "frac-condition-position",
                "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\r"
                "A=REAL(7)\rB=REAL(8)\r"
                "IF FFrac(A)<B THEN\rPrintE(\"OK\")\rFI\rRETURN\r",
                ("rt_f_frac", "rt_f_cmp"),
            ),
            (
                "mod-print-position",
                "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\r"
                "A=REAL(7)\rB=REAL(3)\rPrintRE(FMod(A,B))\rRETURN\r",
                ("rt_f_mod", "rt_print_f"),
            ),
            (
                "mod-condition-position",
                "MODULE MAIN\rREAL A\rREAL B\rREAL C\rPROC MAIN()\r"
                "A=REAL(7)\rB=REAL(3)\rC=REAL(2)\r"
                "IF FMod(A,B)<C THEN\rPrintE(\"OK\")\rFI\rRETURN\r",
                ("rt_f_mod", "rt_f_cmp"),
            ),
            (
                "hypot-print-position",
                "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\r"
                "A=REAL(3)\rB=REAL(4)\rPrintRE(FHypot(A,B))\rRETURN\r",
                ("rt_f_hypot", "rt_print_f"),
            ),
            (
                "hypot-condition-position",
                "MODULE MAIN\rREAL A\rREAL B\rREAL C\rPROC MAIN()\r"
                "A=REAL(3)\rB=REAL(4)\rC=REAL(6)\r"
                "IF FHypot(A,B)<C THEN\rPrintE(\"OK\")\rFI\rRETURN\r",
                ("rt_f_hypot", "rt_f_cmp"),
            ),
            (
                "pow-print-position",
                "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\r"
                "A=REAL(2)\rB=REAL(10)\rPrintRE(FPow(A,B))\rRETURN\r",
                ("rt_f_pow", "rt_print_f"),
            ),
            (
                "pow-condition-position",
                "MODULE MAIN\rREAL A\rREAL B\rREAL C\rPROC MAIN()\r"
                "A=REAL(2)\rB=REAL(10)\rC=REAL(1025)\r"
                "IF FPow(A,B)<C THEN\rPrintE(\"OK\")\rFI\rRETURN\r",
                ("rt_f_pow", "rt_f_cmp"),
            ),
            (
                "sin-print-position",
                "MODULE MAIN\rREAL A\rPROC MAIN()\r"
                "A=REAL(2)\rPrintRE(FSin(A))\rRETURN\r",
                ("rt_f_sin", "rt_print_f"),
            ),
            (
                "sin-condition-position",
                "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\r"
                "A=REAL(2)\rB=REAL(1)\r"
                "IF FSin(A)<B THEN\rPrintE(\"OK\")\rFI\rRETURN\r",
                ("rt_f_sin", "rt_f_cmp"),
            ),
            (
                "cos-print-position",
                "MODULE MAIN\rREAL A\rPROC MAIN()\r"
                "A=REAL(2)\rPrintRE(FCos(A))\rRETURN\r",
                ("rt_f_cos", "rt_print_f"),
            ),
            (
                "cos-condition-position",
                "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\r"
                "A=REAL(2)\rB=REAL(0)\r"
                "IF FCos(A)<B THEN\rPrintE(\"OK\")\rFI\rRETURN\r",
                ("rt_f_cos", "rt_f_cmp"),
            ),
            (
                "tan-print-position",
                "MODULE MAIN\rREAL A\rPROC MAIN()\r"
                "A=REAL(2)\rPrintRE(FTan(A))\rRETURN\r",
                ("rt_f_tan", "rt_print_f"),
            ),
            (
                "tan-condition-position",
                "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\r"
                "A=REAL(2)\rB=REAL(0)\r"
                "IF FTan(A)<B THEN\rPrintE(\"OK\")\rFI\rRETURN\r",
                ("rt_f_tan", "rt_f_cmp"),
            ),
            (
                "exp-print-position",
                "MODULE MAIN\rREAL A\rPROC MAIN()\r"
                "A=REAL(1)\rPrintRE(FExp(A))\rRETURN\r",
                ("rt_f_exp", "rt_print_f"),
            ),
            (
                "exp-condition-position",
                "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\r"
                "A=REAL(1)\rB=REAL(3)\r"
                "IF FExp(A)<B THEN\rPrintE(\"OK\")\rFI\rRETURN\r",
                ("rt_f_exp", "rt_f_cmp"),
            ),
            (
                "ln-print-position",
                "MODULE MAIN\rREAL A\rPROC MAIN()\r"
                "A=REAL(2)\rPrintRE(FLn(A))\rRETURN\r",
                ("rt_f_ln", "rt_print_f"),
            ),
            (
                "ln-condition-position",
                "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\r"
                "A=REAL(2)\rB=REAL(1)\r"
                "IF FLn(A)<B THEN\rPrintE(\"OK\")\rFI\rRETURN\r",
                ("rt_f_ln", "rt_f_cmp"),
            ),
            (
                "log2-print-position",
                "MODULE MAIN\rREAL A\rPROC MAIN()\r"
                "A=REAL(8)\rPrintRE(FLog2(A))\rRETURN\r",
                ("rt_f_log2", "rt_print_f"),
            ),
            (
                "log2-condition-position",
                "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\r"
                "A=REAL(8)\rB=REAL(4)\r"
                "IF FLog2(A)<B THEN\rPrintE(\"OK\")\rFI\rRETURN\r",
                ("rt_f_log2", "rt_f_cmp"),
            ),
            (
                "log10-print-position",
                "MODULE MAIN\rREAL A\rPROC MAIN()\r"
                "A=REAL(1000)\rPrintRE(FLog10(A))\rRETURN\r",
                ("rt_f_log10", "rt_print_f"),
            ),
            (
                "log10-condition-position",
                "MODULE MAIN\rREAL A\rREAL B\rPROC MAIN()\r"
                "A=REAL(1000)\rB=REAL(4)\r"
                "IF FLog10(A)<B THEN\rPrintE(\"OK\")\rFI\rRETURN\r",
                ("rt_f_log10", "rt_f_cmp"),
            ),
        )
        for name, source, expected_modules in position_cases:
            with self.subTest(name=name):
                obj = self.compile_overlay_object(
                    source,
                    f"actc-overlay-native-real-fsign-{name}",
                )
                for runtime_module in expected_modules:
                    self.assertIn(f"u {runtime_module}\n", obj)
                for unrelated_module in (
                    "rt_f_abs",
                    "rt_f_sqrt",
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
                    "rt_f_exp",
                    "rt_f_ln",
                    "rt_f_log2",
                    "rt_f_log10",
                    "rt_f_min",
                    "rt_f_max",
                ):
                    if unrelated_module not in expected_modules:
                        self.assertNotIn(f"u {unrelated_module}\n", obj)

    def test_native_real_emitter_owns_math1_binary_calls(self) -> None:
        for function_name, runtime_module in (
            ("FMin", "rt_f_min"),
            ("FMax", "rt_f_max"),
            ("FMod", "rt_f_mod"),
            ("FHypot", "rt_f_hypot"),
            ("FPow", "rt_f_pow"),
        ):
            with self.subTest(function_name=function_name):
                obj = self.compile_overlay_object(
                    "MODULE MAIN\r"
                    "REAL A\r"
                    "REAL B\r"
                    "REAL X\r"
                    "PROC MAIN()\r"
                    "A=REAL(2)\r"
                    "B=REAL(1)\r"
                    f"X={function_name}(A,B)\r"
                    "PrintRE(X)\r"
                    "RETURN\r",
                    f"actc-overlay-native-real-{function_name.lower()}",
                )

                self.assertEqual(self.last_emit_overlay_pass, [10])
                self.assertIn(f"u {runtime_module}\n", obj)
                for other_module in (
                    "rt_f_min",
                    "rt_f_max",
                    "rt_f_mod",
                    "rt_f_hypot",
                    "rt_f_pow",
                    "rt_f_sin",
                    "rt_f_cos",
                    "rt_f_tan",
                ):
                    if other_module != runtime_module:
                        self.assertNotIn(f"u {other_module}\n", obj)
                self.assertNotIn(f"u {function_name.lower()}\n", obj)

    def test_recursive_real_preparation_preserves_postfix_helper_order(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "C=REAL(3)\r"
            "X=FMin(FMax(A,B),C)\r"
            "PrintRE(X)\r"
            "RETURN\r",
            "actc-overlay-recursive-real-preparation",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [21])
        self.assertIn(
            "x main 0 206\n"
            "x __idata 170 16\n"
            "x __rv0 170 4\n"
            "x __rv1 174 4\n"
            "x __rv2 178 4\n"
            "x __rv3 182 4\n",
            obj,
        )
        self.assertIn(
            "x __rt0 186 4\n"
            "x __rt1 190 4\n"
            "x __rt2 194 4\n"
            "x __rt3 198 4\n"
            "x __rt4 202 4\n",
            obj,
        )
        self.assertIn("b u0u1u2u3M\n", obj)
        self.assertIn("r 103 u1\n", obj)
        self.assertIn("r 130 u2\n", obj)
        self.assertIn(
            "u rt_i_to_f\nu rt_f_max\nu rt_f_min\nu rt_print_f\n",
            obj,
        )
        self.assertTrue(any(line.startswith("m ") for line in obj.splitlines()))

        mixed_prefix = (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "C=REAL(3)\r"
        )
        mixed_statement = (
            "X=FClamp(FAbs(A),FMin(B,C),FMax(A,C))\r"
            "PrintRE(X)\r"
            "RETURN\r"
        )
        mixed_padding = "\r" * (1270 - len(mixed_prefix) - len("X="))
        mixed_source = mixed_prefix + mixed_padding + mixed_statement
        self.assertEqual(mixed_source.index("FClamp"), 1270)
        mixed_obj = self.compile_overlay_object(
            mixed_source,
            "actc-overlay-recursive-real-mixed-preparation",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [21])
        self.assertIn(
            "x main 0 268\n"
            "x __idata 224 16\n"
            "x __rv0 224 4\n"
            "x __rv1 228 4\n"
            "x __rv2 232 4\n"
            "x __rv3 236 4\n",
            mixed_obj,
        )
        self.assertIn(
            "x __rt3 252 4\n"
            "x __rt4 256 4\n"
            "x __rt5 260 4\n"
            "x __rt6 264 4\n",
            mixed_obj,
        )
        self.assertIn("b u0u1u2u3u4u5M\n", mixed_obj)
        self.assertIn("r 184 u4\n", mixed_obj)
        self.assertIn(
            "u rt_i_to_f\nu rt_f_abs\nu rt_f_min\nu rt_f_max\n"
            "u rt_f_clamp\nu rt_print_f\n",
            mixed_obj,
        )
        self.assertTrue(any(line.startswith("m ") for line in mixed_obj.splitlines()))

        signed_obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "A=0-2\r"
            "B=REAL(3)\r"
            "X=FMax(FAbs(A),B)\r"
            "PrintRE(X)\r"
            "RETURN\r",
            "actc-overlay-recursive-real-signed-conversion",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [21])
        self.assertIn("x main 0 164\nx __idata 136 12\n", signed_obj)
        self.assertIn("A9 FE A2 FF 20 00 00", signed_obj)
        self.assertIn(
            "u rt_s_to_f\nu rt_i_to_f\nu rt_f_abs\nu rt_f_max\n"
            "u rt_print_f\n",
            signed_obj,
        )

    def test_nested_real_function_uses_generic_postfix_call_abi(self) -> None:
        source = (
            self.root / "tests" / "parity" / "real_function_nested_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-nested-real-function",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [21])
        self.assertIn(
            "x main 0 275\n"
            "x length 119 112\n"
            "x __idata 231 20\n"
            "x __rv0 231 4\n"
            "x __rv1 235 4\n"
            "x __rv2 239 4\n"
            "x __rv3 243 4\n"
            "x __rv4 247 4\n",
            obj,
        )
        self.assertIn(
            "x __rt0 251 4\n"
            "x __rt1 255 4\n"
            "x __rt2 259 4\n"
            "x __rt3 263 4\n"
            "x __rt4 267 4\n"
            "x __rt5 271 4\n",
            obj,
        )
        self.assertIn("b u0u1u2u3M\nb u0u1u2u3M\n", obj)
        self.assertIn("L 0 119 0 5 11\nL 0 140 0 5 11\n", obj)
        self.assertIn("L 1 0 0 8 1\n", obj)
        self.assertIn(
            "r 53 l x __rv0\n"
            "r 56 h x __rv0\n"
            "r 59 l x __rv1\n"
            "r 62 h x __rv1\n"
            "r 65 x length\n"
            "r 76 x __rt2\n",
            obj,
        )
        self.assertIn("r 135 x __rv4\nr 151 x __rv3\n", obj)
        self.assertIn(
            "r 224 u1\nr 227 l x __rt5\nr 229 h x __rt5\n",
            obj,
        )
        self.assertIn(
            "u rt_f_abs\nu rt_f_hypot\n"
            "u rt_i_to_f\nu rt_print_f\n",
            obj,
        )
        self.assertNotIn("b S4S3L3U3", obj)

    def test_nested_real_function_uses_real_local_storage(self) -> None:
        source = (
            self.root / "tests" / "parity" / "real_function_local_nested_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-local-nested-real-function",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [21])
        self.assertIn("V l r 0 5 0 6 6\n", obj)
        self.assertIn(
            "x main 0 290\n"
            "x length 119 123\n"
            "x __idata 242 24\n"
            "x __rv0 242 4\n"
            "x __rv1 246 4\n"
            "x __rv2 250 4\n"
            "x __rv3 254 4\n"
            "x __rv4 258 4\n"
            "x __rv5 262 4\n",
            obj,
        )
        self.assertIn(
            "x __rt0 266 4\n"
            "x __rt1 270 4\n"
            "x __rt2 274 4\n"
            "x __rt3 278 4\n"
            "x __rt4 282 4\n"
            "x __rt5 286 4\n",
            obj,
        )
        self.assertIn("r 135 x __rv4\nr 151 x __rv3\n", obj)
        self.assertIn(
            "r 162 l x __rv3\n"
            "r 166 h x __rv3\n"
            "r 170 l x __rt3\n"
            "r 174 h x __rt3\n"
            "r 178 u0\n"
            "r 183 x __rt3\n"
            "r 186 x __rv5\n",
            obj,
        )
        self.assertIn(
            "r 211 l x __rv5\n"
            "r 215 h x __rv5\n"
            "r 219 l x __rt4\n"
            "r 223 h x __rt4\n"
            "r 227 l x __rt5\n"
            "r 231 h x __rt5\n"
            "r 235 u1\n",
            obj,
        )
        self.assertIn(
            "u rt_f_abs\nu rt_f_hypot\n"
            "u rt_i_to_f\nu rt_print_f\n",
            obj,
        )

    def test_two_real_functions_use_independent_static_storage(self) -> None:
        source = (
            self.root / "tests" / "parity" / "real_two_function_nested_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-two-nested-real-functions",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [21])
        self.assertIn("q 0 0 6 11\nq 1 0 10 11\nq 2 0 14 6\n", obj)
        self.assertIn("V l r 0 6 0 7 6\n", obj)
        self.assertIn("V l r 1 9 0 11 6\n", obj)
        self.assertIn(
            "x main 0 496\n"
            "x length 170 123\n"
            "x shorter 293 123\n"
            "x __idata 416 40\n",
            obj,
        )
        self.assertIn("b u0u1u2u3u4M\n" * 3, obj)
        self.assertIn("r 65 x length\n", obj)
        self.assertIn("r 105 x shorter\n", obj)
        self.assertIn("r 186 x __rv5\nr 202 x __rv4\n", obj)
        self.assertIn("r 309 x __rv8\nr 325 x __rv7\n", obj)
        self.assertIn(
            "u rt_f_abs\nu rt_f_hypot\nu rt_f_min\n"
            "u rt_i_to_f\nu rt_print_f\n",
            obj,
        )
        self.assertNotIn("u rt_f_clamp\n", obj)

    def test_real_function_can_call_an_earlier_function(self) -> None:
        source = (
            self.root / "tests" / "parity" / "real_function_call_chain_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-real-function-call-chain",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [21])
        self.assertRegex(obj, r"(?m)^x main 0 \d+$")
        self.assertRegex(obj, r"(?m)^x length \d+ \d+$")
        self.assertRegex(obj, r"(?m)^x chain \d+ \d+$")
        self.assertEqual(len(re.findall(r"(?m)^r \d+ x length$", obj)), 1)
        self.assertEqual(len(re.findall(r"(?m)^r \d+ x chain$", obj)), 1)
        self.assertIn(
            "u rt_f_abs\nu rt_f_hypot\nu rt_f_max\n"
            "u rt_i_to_f\nu rt_print_f\n",
            obj,
        )
        self.assertNotIn("u rt_f_min\n", obj)

    def test_real_function_call_can_feed_an_intrinsic_expression(self) -> None:
        source = (
            self.root
            / "tests"
            / "parity"
            / "real_function_nested_local_call_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-real-function-nested-local-call",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [21])
        self.assertIn(
            "x main 0 468\n"
            "x length 119 112\n"
            "x chain 231 173\n"
            "x __idata 404 28\n",
            obj,
        )
        self.assertEqual(len(re.findall(r"(?m)^r \d+ x length$", obj)), 1)
        self.assertEqual(len(re.findall(r"(?m)^r \d+ x chain$", obj)), 1)
        self.assertIn(
            "u rt_f_abs\nu rt_f_hypot\nu rt_f_max\n"
            "u rt_i_to_f\nu rt_print_f\n",
            obj,
        )
        self.assertNotIn("u fmax\n", obj)
        self.assertNotIn("u rt_f_min\n", obj)

    def test_real_function_calls_can_feed_another_local_call(self) -> None:
        source = (
            self.root
            / "tests"
            / "parity"
            / "real_function_user_call_arguments_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-real-function-user-call-arguments",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [21])
        self.assertIn(
            "x main 0 596\n"
            "x lower 119 74\n"
            "x chain 193 347\n"
            "x __idata 540 28\n",
            obj,
        )
        self.assertEqual(len(re.findall(r"(?m)^r \d+ x lower$", obj)), 3)
        self.assertEqual(len(re.findall(r"(?m)^r \d+ x chain$", obj)), 1)
        self.assertIn("r 310 x __rt4\n", obj)
        self.assertIn("r 410 x __rt5\n", obj)
        self.assertIn("r 530 x __rt6\n", obj)
        self.assertIn("u rt_f_min\nu rt_i_to_f\nu rt_print_f\n", obj)
        self.assertNotIn("u rt_f_max\n", obj)
        self.assertNotIn("u rt_f_hypot\n", obj)

    def test_real_function_forward_assignment_call_is_frame_preserved(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL LEFT\r"
            "REAL RIGHT\r"
            "REAL RESULT\r"
            "REAL FUNC FIRST(REAL A,B)\r"
            "REAL TEMP\r"
            "TEMP=SECOND(A,B)\r"
            "RETURN(TEMP)\r"
            "REAL FUNC SECOND(REAL A,B)\r"
            "RETURN(A)\r"
            "PROC MAIN()\r"
            "LEFT=REAL(3)\r"
            "RIGHT=REAL(4)\r"
            "RESULT=FIRST(LEFT,RIGHT)\r"
            "RETURN\r",
            "actc-overlay-forward-real-function-assignment-call",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [21])
        self.assertRegex(obj, r"(?m)^x first \d+ \d+$")
        self.assertRegex(obj, r"(?m)^x second \d+ \d+$")
        self.assertEqual(len(re.findall(r"(?m)^r \d+ x second$", obj)), 1)
        self.assertEqual(len(re.findall(r"(?m)^r \d+ x first$", obj)), 1)

    def test_real_function_forward_expression_call_preserves_live_temporary(self) -> None:
        source = (
            self.root
            / "tests"
            / "parity"
            / "real_function_forward_frame_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-forward-real-function-expression-call",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [21])
        self.assertIn(
            "x main 0 442\n"
            "x first 119 193\n"
            "x second 312 74\n"
            "x __idata 386 28\n",
            obj,
        )
        self.assertIn("r 183 x __rv3\n", obj)
        self.assertIn("r 192 x __rv4\n", obj)
        self.assertIn("r 201 x __rt3\n", obj)
        self.assertIn("r 220 x second\n", obj)
        self.assertIn("r 240 x __rt3\n", obj)
        self.assertIn("r 251 x __rv4\n", obj)
        self.assertIn("r 262 x __rv3\n", obj)
        self.assertIn("r 275 x __rt4\n", obj)
        self.assertIn(
            "u rt_f_abs\nu rt_f_max\nu rt_f_min\n"
            "u rt_i_to_f\nu rt_print_f\n",
            obj,
        )

    def test_real_function_if_else_uses_relocatable_code_labels(self) -> None:
        source = (
            self.root / "tests" / "parity" / "real_function_if_else_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-real-function-if-else",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [22])
        self.assertIn(
            "x main 0 343\n"
            "x pick 170 125\n"
            "x __rf0 252 1\n"
            "x __re0 290 1\n"
            "x __idata 295 28\n",
            obj,
        )
        self.assertIn("C9 FF F0 03 4C 00 00", obj)
        self.assertIn("r 236 x __rf0\n", obj)
        self.assertIn("r 250 x __re0\n", obj)
        self.assertIn("r 229 u0\n", obj)
        self.assertIn("r 277 u1\n", obj)
        self.assertIn(
            "u rt_f_cmp\nu rt_f_max\nu rt_i_to_f\nu rt_print_f\n",
            obj,
        )
        self.assertNotIn("u rt_f_min\n", obj)

    def test_real_function_if_relations_preserve_nan_ordering_rules(self) -> None:
        cases = (
            (">", "C9 01 F0 03 4C 00 00"),
            (">=", "C9 02 90 03 4C 00 00"),
            ("<", "C9 FF F0 03 4C 00 00"),
            ("<=", "C9 01 30 03 4C 00 00"),
            ("=", "C9 00 F0 03 4C 00 00"),
            ("<>", "C9 00 D0 03 4C 00 00"),
        )
        for relation, machine in cases:
            with self.subTest(relation=relation):
                obj = self.compile_overlay_object(
                    "MODULE MAIN\r"
                    "REAL LEFT\rREAL RIGHT\rREAL RESULT\r"
                    "REAL FUNC PICK(REAL A,B)\r"
                    "REAL CHOICE\r"
                    f"IF A{relation}B THEN\r"
                    "CHOICE=A\r"
                    "ELSE\r"
                    "CHOICE=B\r"
                    "FI\r"
                    "RETURN(CHOICE)\r"
                    "PROC MAIN()\r"
                    "LEFT=REAL(3)\rRIGHT=REAL(4)\r"
                    "RESULT=PICK(LEFT,RIGHT)\r"
                    "RETURN\r",
                    f"actc-overlay-real-function-if-{ord(relation[0]):02x}-{len(relation)}",
                    extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
                )

                self.assertEqual(self.last_emit_overlay_pass, [22])
                self.assertIn(machine, obj)
                self.assertIn("x __rf0", obj)
                self.assertIn("x __re0", obj)
                self.assertIn("u rt_f_cmp\n", obj)

    def test_real_function_sequential_if_else_uses_distinct_code_labels(self) -> None:
        source = (
            self.root / "tests" / "parity" / "real_function_sequential_if_else_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-real-function-sequential-if-else",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [23])
        self.assertIn(
            "x main 0 425\n"
            "x pick 170 203\n"
            "x __rf00 252 1\n"
            "x __re00 263 1\n"
            "x __rf01 330 1\n"
            "x __re01 368 1\n"
            "x __idata 373 28\n",
            obj,
        )
        for relocation in (
            "r 236 x __rf00\n",
            "r 250 x __re00\n",
            "r 287 x __rf01\n",
            "r 328 x __re01\n",
        ):
            self.assertIn(relocation, obj)
        self.assertIn(
            "u rt_f_cmp\nu rt_f_max\nu rt_f_min\nu rt_i_to_f\nu rt_print_f\n",
            obj,
        )

    def test_real_function_nested_if_else_uses_depth_first_relocations(self) -> None:
        source = (
            self.root / "tests" / "parity" / "real_function_nested_if_else_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-real-function-nested-if-else",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [23])
        self.assertIn(
            "x main 0 613\n"
            "x pick 299 234\n"
            "x __rf00 490 1\n"
            "x __re00 528 1\n"
            "x __rf01 449 1\n"
            "x __re01 487 1\n"
            "x __idata 533 32\n",
            obj,
        )
        for relocation in (
            "r 365 x __rf00\n",
            "r 406 x __rf01\n",
            "r 447 x __re01\n",
            "r 488 x __re00\n",
        ):
            self.assertIn(relocation, obj)
        self.assertIn(
            "u rt_f_cmp\nu rt_i_to_f\nu rt_f_min\nu rt_f_max\nu rt_print_f\n",
            obj,
        )

    def test_real_function_four_sequential_if_uses_all_extended_control_slots(self) -> None:
        source = (
            self.root
            / "tests"
            / "parity"
            / "real_function_four_sequential_if_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-real-function-four-sequential-if",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [24])
        self.assertIn(
            "x main 0 420\n"
            "x pick 170 206\n"
            "x __rf00 260 1\n"
            "x __rf01 297 1\n"
            "x __rf02 334 1\n"
            "x __rf03 371 1\n"
            "x __idata 376 28\n",
            obj,
        )
        for relocation in (
            "r 247 x __rf00\n",
            "r 284 x __rf01\n",
            "r 321 x __rf02\n",
            "r 358 x __rf03\n",
        ):
            self.assertIn(relocation, obj)
        self.assertIn("u rt_f_cmp\nu rt_i_to_f\nu rt_print_f\n", obj)

    def test_real_function_four_deep_if_uses_depth_first_relocations_and_declines_fifth_control(self) -> None:
        source = (
            self.root
            / "tests"
            / "parity"
            / "real_function_four_deep_if_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-real-function-four-deep-if",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [24])
        self.assertIn(
            "x main 0 607\n"
            "x pick 299 232\n"
            "x __rf00 526 1\n"
            "x __rf01 526 1\n"
            "x __rf02 526 1\n"
            "x __rf03 515 1\n"
            "x __re03 526 1\n"
            "x __idata 531 32\n",
            obj,
        )
        for relocation in (
            "r 376 x __rf00\n",
            "r 417 x __rf01\n",
            "r 458 x __rf02\n",
            "r 499 x __rf03\n",
            "r 513 x __re03\n",
        ):
            self.assertIn(relocation, obj)
        self.assertIn("u rt_f_cmp\nu rt_i_to_f\nu rt_print_f\n", obj)

        sequential_source = (
            self.root
            / "tests"
            / "parity"
            / "real_function_four_sequential_if_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        five_control_source = sequential_source.replace(
            "RETURN(CHOICE)\r",
            "IF A<B THEN\rCHOICE=A\rFI\rRETURN(CHOICE)\r",
            1,
        )
        fallback_obj = self.compile_overlay_object(
            five_control_source,
            "actc-overlay-fallback-real-function-five-controls",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [5])
        self.assertNotIn("x __rf04 ", fallback_obj)

    def test_real_function_early_return_if_uses_pass_p_and_terminal_fallback(self) -> None:
        source = (
            self.root
            / "tests"
            / "parity"
            / "real_function_early_return_if_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-real-function-early-return-if",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [25])
        self.assertIn(
            "x main 0 288\n"
            "x pick 170 78\n"
            "x __rf00 243 1\n"
            "x __idata 248 24\n",
            obj,
        )
        for relocation in (
            "r 236 x __rf00\n",
            "r 239 l x __rv4\n",
            "r 241 h x __rv4\n",
            "r 244 l x __rv5\n",
            "r 246 h x __rv5\n",
        ):
            self.assertIn(relocation, obj)
        self.assertIn("u rt_f_cmp\nu rt_i_to_f\nu rt_print_f\n", obj)

        no_terminal_source = source.replace(
            "FI\rRETURN(B)\rPROC MAIN()",
            "FI\rPROC MAIN()",
            1,
        )
        fallback_obj = self.compile_overlay_object(
            no_terminal_source,
            "actc-overlay-fallback-real-function-early-return-no-terminal",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )
        self.assertEqual(self.last_emit_overlay_pass, [5])
        self.assertNotIn("x __rf00 ", fallback_obj)

    def test_real_function_early_return_four_deep_closes_all_control_labels(self) -> None:
        source = (
            self.root
            / "tests"
            / "parity"
            / "real_function_early_return_four_deep_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-real-function-early-return-four-deep",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [25])
        self.assertIn(
            "x main 0 580\n"
            "x pick 299 209\n"
            "x __rf00 503 1\n"
            "x __rf01 503 1\n"
            "x __rf02 503 1\n"
            "x __rf03 498 1\n"
            "x __re03 503 1\n"
            "x __idata 508 28\n",
            obj,
        )
        for relocation in (
            "r 365 x __rf00\n",
            "r 406 x __rf01\n",
            "r 447 x __rf02\n",
            "r 488 x __rf03\n",
            "r 496 x __re03\n",
            "r 491 l x __rv5\n",
            "r 493 h x __rv5\n",
            "r 499 l x __rv6\n",
            "r 501 h x __rv6\n",
            "r 504 l x __rv6\n",
            "r 506 h x __rv6\n",
        ):
            self.assertIn(relocation, obj)
        self.assertIn("u rt_f_cmp\nu rt_i_to_f\nu rt_print_f\n", obj)

    def test_real_function_loops_use_pass_q_with_distinct_back_and_exit_labels(self) -> None:
        source = (
            self.root / "tests" / "parity" / "real_function_loops_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-real-function-loops",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [26])
        self.assertIn(
            "x main 0 449\n"
            "x up 222 84\n"
            "x down 306 87\n"
            "x __rb00 264 1\n"
            "x __rb10 348 1\n"
            "x __rz10 388 1\n"
            "x __idata 393 32\n",
            obj,
        )
        for relocation in (
            "r 299 x __rb00\n",
            "r 372 x __rz10\n",
            "r 386 x __rb10\n",
        ):
            self.assertIn(relocation, obj)
        self.assertIn("u rt_f_cmp\nu rt_i_to_f\nu rt_print_f\n", obj)
        self.assertNotIn("u rt_f_add\n", obj)

    def test_real_function_loop_exit_uses_pass_r_with_distinct_targets(self) -> None:
        source = (
            self.root / "tests" / "parity" / "real_function_loop_exit_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-real-function-loop-exit",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [27])
        self.assertIn(
            "x main 0 432\n"
            "x plain 222 64\n"
            "x guarded 286 90\n"
            "x __rb00 264 1\n"
            "x __rz00 281 1\n"
            "x __rb10 328 1\n"
            "x __rz10 371 1\n"
            "x __idata 376 32\n",
            obj,
        )
        for relocation in (
            "r 276 x __rz00\n",
            "r 279 x __rb00\n",
            "r 352 x __rz10\n",
            "r 366 x __rz10\n",
            "r 369 x __rb10\n",
        ):
            self.assertIn(relocation, obj)
        self.assertIn("u rt_f_cmp\nu rt_i_to_f\nu rt_print_f\n", obj)
        self.assertNotIn("u rt_f_add\n", obj)

    def test_real_function_loop_exit_targets_nearest_nested_plain_loop(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL LEFT\r"
            "REAL RIGHT\r"
            "REAL RESULT\r"
            "REAL FUNC PICK(REAL A,B)\r"
            "DO\r"
            "DO\r"
            "A=B\r"
            "EXIT\r"
            "OD\r"
            "EXIT\r"
            "OD\r"
            "RETURN(A)\r"
            "PROC MAIN()\r"
            "LEFT=REAL(1)\r"
            "RIGHT=REAL(4)\r"
            "RESULT=PICK(LEFT,RIGHT)\r"
            "RETURN\r",
            "actc-overlay-real-function-nearest-loop-exit",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [27])
        for label in ("__rb00", "__rz00", "__rb01", "__rz01"):
            self.assertRegex(obj, rf"(?m)^x {label} [0-9]+ 1$")
            self.assertRegex(obj, rf"(?m)^r [0-9]+ x {label}$")

    def test_real_function_for_uses_pass_s_with_constant_card_bounds_and_steps(self) -> None:
        source = (
            self.root / "tests" / "parity" / "real_function_for_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-real-function-for",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [28])
        self.assertIn(
            "x main 0 624\n"
            "x ascend 196 177\n"
            "x descend 373 175\n"
            "x __rb00 268 1\n"
            "x __rz00 368 1\n"
            "x __rb10 445 1\n"
            "x __rz10 543 1\n"
            "x __idata 548 48\n",
            obj,
        )
        for relocation in (
            "r 296 x __rz00\n",
            "r 363 x __rb00\n",
            "r 366 x __rz00\n",
            "r 471 x __rz10\n",
            "r 538 x __rb10\n",
            "r 541 x __rz10\n",
        ):
            self.assertIn(relocation, obj)
        self.assertIn("u rt_f_add\nu rt_i_to_f\nu rt_print_f\n", obj)
        self.assertIn(
            "A0 00 B1 06 18 69 01 91 06 C8 B1 06 69 00 91 06 "
            "B0 03 4C 00 00 4C 00 00",
            obj,
        )
        self.assertIn(
            "A0 00 B1 06 18 69 FE 91 06 C8 B1 06 69 FF 91 06 "
            "90 03 4C 00 00 4C 00 00",
            obj,
        )

        four_deep_obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL START\rREAL DELTA\rREAL RESULT\r"
            "REAL FUNC PLUS(REAL A,B)\r"
            "CARD I\rCARD J\rCARD K\rCARD L\rREAL TOTAL\rTOTAL=A\r"
            "FOR I=1 TO 1\rDO\r"
            "FOR J=1 TO 1\rDO\r"
            "FOR K=1 TO 1\rDO\r"
            "FOR L=1 TO 1\rDO\r"
            "TOTAL=TOTAL+B\rOD\rOD\rOD\rOD\r"
            "RETURN(TOTAL)\r"
            "PROC MAIN()\rSTART=REAL(1)\rDELTA=REAL(1)\r"
            "RESULT=PLUS(START,DELTA)\rPrintRE(RESULT)\rRETURN\r",
            "actc-overlay-real-function-four-deep-for",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )
        self.assertEqual(self.last_emit_overlay_pass, [28])
        for slot in range(4):
            for prefix in ("__rb", "__rz"):
                label = f"{prefix}0{slot}"
                self.assertRegex(four_deep_obj, rf"(?m)^x {label} [0-9]+ 1$")
                self.assertRegex(four_deep_obj, rf"(?m)^r [0-9]+ x {label}$")

    def test_real_function_for_uses_pass_t_with_named_card_bounds(self) -> None:
        source = (
            self.root
            / "tests"
            / "parity"
            / "real_function_dynamic_for_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-real-function-dynamic-for",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [29])
        self.assertIn(
            "x main 0 813\n"
            "x fromouter 170 266\n"
            "x toouter 436 293\n"
            "x __rb00 242 1\n"
            "x __rz00 431 1\n"
            "x __rb01 299 1\n"
            "x __rz01 399 1\n"
            "x __rb10 508 1\n"
            "x __rz10 724 1\n"
            "x __rb11 584 1\n"
            "x __rz11 692 1\n"
            "x __idata 729 56\n",
            obj,
        )
        for relocation in (
            "r 270 x __rz00\n",
            "r 327 x __rz01\n",
            "r 394 x __rb01\n",
            "r 397 x __rz01\n",
            "r 426 x __rb00\n",
            "r 429 x __rz00\n",
            "r 536 x __rz10\n",
            "r 620 x __rz11\n",
            "r 687 x __rb11\n",
            "r 690 x __rz11\n",
            "r 719 x __rb10\n",
            "r 722 x __rz10\n",
        ):
            self.assertIn(relocation, obj)
        self.assertIn("u rt_f_add\nu rt_i_to_f\nu rt_print_f\n", obj)
        self.assertIn(
            "A0 01 B1 04 91 06 88 B1 04 91 06",
            obj,
        )
        self.assertIn(
            "A0 01 B1 06 D1 04 90 0E D0 09 88 B1 06 D1 04",
            obj,
        )

    def test_real_function_literals_use_pass_u_with_one_parameter_frames(self) -> None:
        source = (
            self.root
            / "tests"
            / "parity"
            / "math1_angle_conversions_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-math1-angle-conversions",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [30])
        self.assertIn("q 0 0 7 11\nq 1 0 14 11\nq 2 0 21 6\n", obj)
        self.assertIn(
            "V p r 0 4 0 7 25\n"
            "V l r 0 5 0 8 6\n"
            "V l r 0 6 0 9 6\n"
            "V p r 1 7 0 14 25\n"
            "V l r 1 8 0 15 6\n"
            "V l r 1 9 0 16 6\n",
            obj,
        )
        self.assertIn(
            "x main 0 584\n"
            "x locald2r 172 162\n"
            "x localr2d 334 162\n"
            "x __idata 496 40\n",
            obj,
        )
        self.assertEqual(obj.count("b u0u1u2u3M\n"), 3)
        body_lines = [line for line in obj.splitlines() if line.startswith("b ")]
        self.assertTrue(all(re.fullmatch(r"b (?:u[0-9A-Za-z])*M", line) for line in body_lines))
        self.assertEqual(
            obj.count(
                "A0 00 A9 DB 91 02 C8 A9 0F 91 02 C8 "
                "A9 49 91 02 C8 A9 40 91 02"
            ),
            3,
        )
        self.assertIn("r 73 x locald2r\n", obj)
        self.assertIn("r 107 x localr2d\n", obj)
        self.assertIn("u rt_i_to_f\nu rt_f_div\nu rt_f_mul\nu rt_print_f\n", obj)
        self.assertIn("i 4059\ni 16457\n", obj)

    def test_real_function_literal_controls_accept_grouped_real_locals(self) -> None:
        source = (
            self.root
            / "tests"
            / "parity"
            / "real_function_literal_clamp_comma_locals_postfix.act"
        ).read_text(encoding="ascii").replace("\n", "\r")
        obj = self.compile_overlay_object(
            source,
            "actc-overlay-real-literal-control-comma-locals",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [30])
        self.assertIn("V l r 0 ", obj)
        for name in ("product", "lower", "upper", "zerolocal"):
            self.assertRegex(obj, rf"(?m)^v {name} ")
        for label in ("__rf00", "__rf01", "__rf02"):
            self.assertRegex(obj, rf"(?m)^x {label} ")
        self.assertIn("u rt_f_cmp\n", obj)
        self.assertIn("u rt_f_mul\n", obj)

    def test_math1_angle_builtins_use_independent_runtime_imports(self) -> None:
        math1_header = (self.root / "lib" / "math1.act").read_text(
            encoding="ascii"
        )
        for name, call, expected, absent in (
            (
                "degrees-to-radians",
                "DegToRad",
                "rt_f_deg_to_rad",
                "rt_f_rad_to_deg",
            ),
            (
                "radians-to-degrees",
                "RadToDeg",
                "rt_f_rad_to_deg",
                "rt_f_deg_to_rad",
            ),
        ):
            with self.subTest(name=name):
                obj = self.compile_overlay_object(
                    (
                        'INCLUDE "MATH1"\r'
                        "MODULE MAIN\r"
                        "REAL VALUE\r"
                        "REAL RESULT\r"
                        "PROC MAIN()\r"
                        "VALUE=REAL(180)\r"
                        f"RESULT={call}(VALUE)\r"
                        "PrintRE(RESULT)\r"
                    ),
                    f"actc-overlay-math1-{name}",
                    extra_build_env={
                        "ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"
                    },
                    additional_sources={"MATH1.ACT": math1_header},
                )

                self.assertEqual(self.last_emit_overlay_pass, [5])
                self.assertIn(f"u {expected}\n", obj)
                self.assertNotIn(f"u {absent}\n", obj)
                self.assertIn("u rt_i_to_f\n", obj)
                self.assertIn("u rt_print_f\n", obj)

    def test_math1_exp_builtin_uses_an_independent_runtime_import(self) -> None:
        math1_header = (self.root / "lib" / "math1.act").read_text(
            encoding="ascii"
        )
        self.assertIn("; REAL FUNC FExp(REAL value)", math1_header)
        obj = self.compile_overlay_object(
            (
                'INCLUDE "MATH1"\r'
                "MODULE MAIN\r"
                "REAL VALUE\r"
                "REAL RESULT\r"
                "PROC MAIN()\r"
                "VALUE=REAL(1)\r"
                "RESULT=FExp(VALUE)\r"
                "PrintRE(RESULT)\r"
            ),
            "actc-overlay-math1-exp",
            extra_build_env={
                "ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"
            },
            additional_sources={"MATH1.ACT": math1_header},
        )

        self.assertEqual(self.last_emit_overlay_pass, [5])
        self.assertIn("u rt_f_exp\n", obj)
        for absent in ("rt_f_abs", "rt_f_hypot", "rt_f_deg_to_rad"):
            self.assertNotIn(f"u {absent}\n", obj)
        self.assertIn("u rt_i_to_f\n", obj)
        self.assertIn("u rt_print_f\n", obj)

    def test_math1_ln_builtin_uses_an_independent_runtime_import(self) -> None:
        math1_header = (self.root / "lib" / "math1.act").read_text(
            encoding="ascii"
        )
        self.assertIn("; REAL FUNC FLn(REAL value)", math1_header)
        obj = self.compile_overlay_object(
            (
                'INCLUDE "MATH1"\r'
                "MODULE MAIN\r"
                "REAL VALUE\r"
                "REAL RESULT\r"
                "PROC MAIN()\r"
                "VALUE=REAL(2)\r"
                "RESULT=FLn(VALUE)\r"
                "PrintRE(RESULT)\r"
            ),
            "actc-overlay-math1-ln",
            extra_build_env={
                "ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"
            },
            additional_sources={"MATH1.ACT": math1_header},
        )

        self.assertEqual(self.last_emit_overlay_pass, [5])
        self.assertIn("u rt_f_ln\n", obj)
        for absent in ("rt_f_exp", "rt_f_hypot", "rt_f_deg_to_rad"):
            self.assertNotIn(f"u {absent}\n", obj)
        self.assertIn("u rt_i_to_f\n", obj)
        self.assertIn("u rt_print_f\n", obj)

    def test_math1_log_wrappers_use_independent_runtime_imports(self) -> None:
        math1_header = (self.root / "lib" / "math1.act").read_text(
            encoding="ascii"
        )
        cases = (
            ("FLog2", "8", "rt_f_log2", "rt_f_log10"),
            ("FLog10", "1000", "rt_f_log10", "rt_f_log2"),
        )
        for function, value, expected, absent in cases:
            with self.subTest(function=function):
                self.assertIn(
                    f"; REAL FUNC {function}(REAL value)",
                    math1_header,
                )
                obj = self.compile_overlay_object(
                    (
                        'INCLUDE "MATH1"\r'
                        "MODULE MAIN\r"
                        "REAL VALUE\r"
                        "REAL RESULT\r"
                        "PROC MAIN()\r"
                        f"VALUE=REAL({value})\r"
                        f"RESULT={function}(VALUE)\r"
                        "PrintRE(RESULT)\r"
                    ),
                    f"actc-overlay-math1-{function.lower()}",
                    extra_build_env={
                        "ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"
                    },
                    additional_sources={"MATH1.ACT": math1_header},
                )

                self.assertEqual(self.last_emit_overlay_pass, [5])
                self.assertIn(f"u {expected}\n", obj)
                for unrelated in (absent, "rt_f_exp", "rt_f_deg_to_rad"):
                    self.assertNotIn(f"u {unrelated}\n", obj)
                self.assertIn("u rt_i_to_f\n", obj)
                self.assertIn("u rt_print_f\n", obj)

    def test_math1_angle_builtins_are_available_in_pass_u_functions(self) -> None:
        source = (
            self.root
            / "tests"
            / "parity"
            / "math1_angle_conversions_postfix.act"
        ).read_text(encoding="ascii")
        source = source.replace(
            "RADIANS=LOCALD2R(DEGREES)",
            "RADIANS=DegToRad(DEGREES)",
        ).replace(
            "RESULT_DEGREES=LOCALR2D(PI_VALUE)",
            "RESULT_DEGREES=RadToDeg(PI_VALUE)",
        )
        obj = self.compile_overlay_object(
            source.replace("\n", "\r"),
            "actc-overlay-math1-angle-builtins-pass-u",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [30])
        self.assertIn("u rt_f_deg_to_rad\n", obj)
        self.assertIn("u rt_f_rad_to_deg\n", obj)
        self.assertRegex(obj, r"(?m)^x locald2r [0-9]+ 162$")
        self.assertRegex(obj, r"(?m)^x localr2d [0-9]+ 162$")

    def test_real_function_loop_pass_owns_depth_four_and_declines_fifth_loop(self) -> None:
        def nested_loop_source(depth: int) -> str:
            return (
                "MODULE MAIN\r"
                "REAL START\r"
                "REAL LIMIT\r"
                "REAL RESULT\r"
                "REAL FUNC PICK(REAL A,B)\r"
                + ("DO\r" * depth)
                + "A=B\r"
                + ("UNTIL A>=B\rOD\r" * depth)
                + "RETURN(A)\r"
                "PROC MAIN()\r"
                "START=REAL(1)\r"
                "LIMIT=REAL(4)\r"
                "RESULT=PICK(START,LIMIT)\r"
                "PrintRE(RESULT)\r"
                "RETURN\r"
            )

        obj = self.compile_overlay_object(
            nested_loop_source(4),
            "actc-overlay-real-function-four-deep-loops",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [26])
        for slot in range(4):
            label = f"__rb0{slot}"
            self.assertRegex(obj, rf"(?m)^x {label} [0-9]+ 1$")
            self.assertRegex(obj, rf"(?m)^r [0-9]+ x {label}$")

        fallback_obj = self.compile_overlay_object(
            nested_loop_source(5),
            "actc-overlay-fallback-real-function-five-deep-loops",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
        )

        self.assertEqual(self.last_emit_overlay_pass, [5])
        self.assertNotIn("x __rb04 ", fallback_obj)

    def test_real_function_mutual_call_cycle_is_rejected(self) -> None:
        console = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL LEFT\r"
            "REAL RIGHT\r"
            "REAL RESULT\r"
            "REAL FUNC FIRST(REAL A,B)\r"
            "RETURN(SECOND(A,B))\r"
            "REAL FUNC SECOND(REAL A,B)\r"
            "RETURN(FIRST(A,B))\r"
            "PROC MAIN()\r"
            "LEFT=REAL(3)\r"
            "RIGHT=REAL(4)\r"
            "RESULT=FIRST(LEFT,RIGHT)\r"
            "RETURN\r",
            "actc-overlay-reject-mutual-real-function-cycle",
            extra_build_env={"ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY": "1"},
            expected_exit_status=1,
        )

        self.assertIn("EMIT OVL FAIL", console)

    def test_native_real_emitter_owns_math1_clamp_call(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(1)\r"
            "C=REAL(3)\r"
            "X=FClamp(A,B,C)\r"
            "PrintRE(X)\r"
            "RETURN\r",
            "actc-overlay-native-real-fclamp",
        )

        self.assertEqual(self.last_emit_overlay_pass, [20])
        self.assertIn(
            "x main 0 171\n"
            "x __idata 147 16\n"
            "x __ireala 147 4\n"
            "x __irealb 151 4\n"
            "x __irealc 155 4\n"
            "x __irealx 159 4\n"
            "x __iptr 163 8\n",
            obj,
        )
        self.assertIn("b u0u1u2M\nb M\nb M\nb M\nb M\nb M\nb M\n", obj)
        self.assertIn(
            "r 3 x __iptr\n"
            "r 9 x __iptr\n"
            "r 18 u0\n"
            "r 23 x __iptr\n"
            "r 29 x __iptr\n"
            "r 38 u0\n"
            "r 43 x __iptr\n"
            "r 49 x __iptr\n"
            "r 58 u0\n"
            "r 63 x __iptr\n"
            "r 69 x __iptr\n"
            "r 76 x __iptr\n"
            "r 82 x __iptr\n"
            "r 89 x __iptr\n"
            "r 95 x __iptr\n"
            "r 102 x __iptr\n"
            "r 108 x __iptr\n"
            "r 113 u1\n"
            "r 118 x __iptr\n"
            "r 124 x __iptr\n"
            "r 129 u2\n"
            "r 163 x __ireala\n"
            "r 165 x __irealb\n"
            "r 167 x __irealc\n"
            "r 169 x __irealx\n",
            obj,
        )
        self.assertIn("u rt_f_clamp\n", obj)
        self.assertIn("u rt_i_to_f\n", obj)
        self.assertIn("u rt_print_f\n", obj)
        self.assertNotIn("u rt_f_min\n", obj)
        self.assertNotIn("u rt_f_max\n", obj)
        self.assertNotIn("u rt_f_cmp\n", obj)
        self.assertNotIn("u fclamp\n", obj)

    def test_native_real_clamp_tracks_permuted_named_storage(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL VALUE\r"
            "REAL HIGH\r"
            "REAL LOW\r"
            "REAL RESULT\r"
            "PROC MAIN()\r"
            "HIGH=REAL(9)\r"
            "RESULT=REAL(3)\r"
            "LOW=REAL(5)\r"
            "VALUE=FClamp(RESULT,LOW,HIGH)\r"
            "PrintRE(VALUE)\r"
            "RETURN\r",
            "actc-overlay-native-real-fclamp-permuted",
        )

        self.assertEqual(self.last_emit_overlay_pass, [20])
        machine_hex = "".join(
            "".join(line.split()[1:])
            for line in obj.splitlines()
            if line.startswith("m ")
        )
        machine = bytes.fromhex(machine_hex)
        self.assertEqual(len(machine), 171)
        self.assertEqual(
            [machine[offset] for offset in (1, 21, 41, 61, 74, 87, 100, 116)],
            [2, 6, 4, 6, 4, 2, 0, 0],
        )
        self.assertEqual(
            [machine[offset] for offset in (14, 16, 34, 36, 54, 56)],
            [9, 0, 3, 0, 5, 0],
        )
        self.assertIn("u rt_f_clamp\n", obj)
        self.assertIn("u rt_i_to_f\n", obj)
        self.assertIn("u rt_print_f\n", obj)

    def test_native_real_emitter_owns_input_print_sequences(self) -> None:
        cases = (
            (
                "side-effect",
                "REAL A\r",
                "Joy(2)\rA=REAL(7)\rPrintRE(A)\r",
                "rt_joy",
                "x main 0 66\nx __idata 60 4\nx __iptr 64 2\n",
                "m A9 02 AA A0 00 20 00 00 ",
                (
                    "r 6 u0\n"
                    "r 11 x __iptr\n"
                    "r 17 x __iptr\n"
                    "r 26 u1\n"
                    "r 31 x __iptr\n"
                    "r 37 x __iptr\n"
                    "r 42 u2\n"
                    "r 64 x __idata\n"
                ),
                "p0u0p2u1T0S0L0U0p3u2r",
            ),
            (
                "stored-result",
                "BYTE J\rREAL A\r",
                "J=Joy(2)\rA=REAL(7)\rPrintRE(A)\r",
                "rt_joy",
                (
                    "x main 0 76\n"
                    "x __idata 68 6\n"
                    "x __iresult 68 2\n"
                    "x __iresulthi 69 1\n"
                    "x __ireala 70 4\n"
                    "x __iptr 74 2\n"
                ),
                "m A9 02 AA A0 00 20 00 00 8D 00 00 A9 00 8D 00 00 ",
                (
                    "r 6 u0\n"
                    "r 9 x __iresult\n"
                    "r 14 x __iresulthi\n"
                    "r 19 x __iptr\n"
                    "r 25 x __iptr\n"
                    "r 34 u1\n"
                    "r 39 x __iptr\n"
                    "r 45 x __iptr\n"
                    "r 50 u2\n"
                    "r 74 x __ireala\n"
                ),
                "p0u0S0p2u1T1S1L1U1p3u2r",
            ),
            (
                "word-argument",
                "REAL A\r",
                "ScreenBase(1024)\rA=REAL(7)\rPrintRE(A)\r",
                "rt_gfx_screen_base",
                "x main 0 66\nx __idata 60 4\nx __iptr 64 2\n",
                "m A9 00 AA A0 04 20 00 00 ",
                (
                    "r 6 u0\n"
                    "r 11 x __iptr\n"
                    "r 17 x __iptr\n"
                    "r 26 u1\n"
                    "r 31 x __iptr\n"
                    "r 37 x __iptr\n"
                    "r 42 u2\n"
                    "r 64 x __idata\n"
                ),
                "p0u0p2u1T0S0L0U0p3u2r",
            ),
        )
        for name, declarations, statements, first_helper, exports, machine, relocs, compact_body in cases:
            with self.subTest(name=name):
                obj = self.compile_overlay_object(
                    "MODULE MAIN\r"
                    f"{declarations}"
                    "PROC MAIN()\r"
                    f"{statements}"
                    "RETURN\r",
                    f"actc-overlay-native-real-input-{name}",
                )

                self.assertEqual(self.last_emit_overlay_pass, [10])
                self.assertIn(exports, obj)
                self.assertIn("b u0u1u2M\n", obj)
                self.assertIn(machine, obj)
                self.assertIn(relocs, obj)
                self.assertIn(f"u {first_helper}\n", obj)
                self.assertIn("u rt_i_to_f\n", obj)
                self.assertIn("u rt_print_f\n", obj)
                self.assertNotIn(f"b {compact_body}\n", obj)

    def test_native_real_input_bridge_rejects_non_runtime_external(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "REAL A\r"
            "PROC MAIN()\r"
            "ExtCall(2)\r"
            "A=REAL(7)\r"
            "PrintRE(A)\r"
            "RETURN\r",
            "actc-overlay-native-real-input-non-runtime",
        )

        self.assertNotEqual(self.last_emit_overlay_pass, [10])
        self.assertIn("u extcall\n", obj)
        self.assertIn("b p0u0p2u1T0S0L0U0p3u2r\n", obj)

    def test_native_real_control_emitter_owns_if_families(self) -> None:
        cases = (
            (
                "plain",
                "A=REAL(2)\rB=REAL(1)\rIF A>B THEN\rY=7\rFI\r",
                "x main 0 126\nx __idata 112 14\nx __ifa 112 4\nx __ifb 116 4\n"
                "x __ify 120 2\nx __ifyhi 121 1\nx __ifptr 122 4\n",
                "C9 01 D0 0A A9 07 A2 00 8D 00 00 8E 00 00",
                "r 78 x __ify\nr 81 x __ifyhi\nr 84 x __ify\nr 87 x __ifyhi\n"
                "r 122 x __ifa\nr 124 x __ifb\n",
                "p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghp5S2vr",
            ),
            (
                "else",
                "A=REAL(1)\rB=REAL(2)\rIF A<=B THEN\rY=7\rELSE\rY=9\rFI\r",
                "x main 0 140\nx __idata 126 14\nx __ifa 126 4\nx __ifb 130 4\n"
                "x __ify 134 2\nx __ifyhi 135 1\nx __ifptr 136 4\n",
                "C9 01 10 0E A9 07 A2 00 8D 00 00 8E 00 00 A9 01 D0 0A A9 09",
                "r 78 x __ify\nr 81 x __ifyhi\nr 92 x __ify\nr 95 x __ifyhi\n"
                "r 98 x __ify\nr 101 x __ifyhi\nr 136 x __ifa\nr 138 x __ifb\n",
                "p1u0T0S0p3u0T1S1L0U0L1U1u1p4lhp5S2wp6S2vr",
            ),
            (
                "nested",
                "A=REAL(2)\rB=REAL(1)\rIF A<>B THEN\rIF A<>B THEN\rY=7\rFI\rFI\r",
                "x main 0 160\nx __idata 146 14\nx __ifa 146 4\nx __ifb 150 4\n"
                "x __ify 154 2\nx __ifyhi 155 1\nx __ifptr 156 4\n",
                "C9 00 F0 2B A2 00 BD 00 00 85 02",
                "r 76 x __ifptr\nr 82 x __ifptr\nr 89 x __ifptr\nr 95 x __ifptr\n"
                "r 100 u1\nr 111 x __ify\nr 114 x __ifyhi\nr 117 x __ify\n"
                "r 120 x __ifyhi\nr 156 x __ifa\nr 158 x __ifb\n",
                "p1u0T0S0p3u0T1S1L0U0L1U1u1p4nhL0U0L1U1u1p5nhp6S2vvr",
            ),
        )
        for name, statements, exports, machine, tail_relocs, compact_body in cases:
            with self.subTest(name=name):
                obj = self.compile_overlay_object(
                    "MODULE MAIN\r"
                    "REAL A\r"
                    "REAL B\r"
                    "CARD Y\r"
                    "PROC MAIN()\r"
                    f"{statements}"
                    "RETURN\r",
                    f"actc-overlay-native-real-control-{name}",
                )

                self.assertEqual(self.last_emit_overlay_pass, [11])
                self.assertIn(exports, obj)
                self.assertIn("b u0u1M\nb M\nb M\nb M\nb M\nb M\nb M\n", obj)
                self.assertIn(machine, obj)
                self.assertIn(
                    "r 3 x __ifptr\nr 9 x __ifptr\nr 18 u0\n"
                    "r 23 x __ifptr\nr 29 x __ifptr\nr 38 u0\n"
                    "r 43 x __ifptr\nr 49 x __ifptr\nr 56 x __ifptr\n"
                    "r 62 x __ifptr\nr 67 u1\n",
                    obj,
                )
                self.assertIn(tail_relocs, obj)
                self.assertIn("u rt_i_to_f\n", obj)
                self.assertIn("u rt_f_cmp\n", obj)
                self.assertNotIn(f"b {compact_body}\n", obj)

    def test_native_real_control_emitter_owns_do_until_families(self) -> None:
        simple_exports = (
            "x main 0 146\nx __idata 132 14\nx __doa 132 4\nx __dob 136 4\n"
            "x __doy 140 2\nx __doyhi 141 1\nx __doptr 142 4\n"
        )
        binary_exports = (
            "x main 0 194\nx __idata 174 20\nx __doa 174 4\nx __dob 178 4\n"
            "x __doc 182 4\nx __doy 186 2\nx __doyhi 187 1\nx __doptr 188 6\n"
        )
        cases = (
            (
                "simple",
                "REAL A\rREAL B\rCARD Y\r",
                "A=REAL(0)\rB=REAL(1)\rDO\rA=REAL(2)\rUNTIL A>B\rOD\rY=7\r",
                simple_exports,
                "b u0u1M\nb M\nb M\nb M\nb M\nb M\nb M\n",
                "C9 01 D0 CB A9 07 A2 00 8D 00 00 8E 00 00",
                "r 58 u0\nr 63 x __doptr\nr 69 x __doptr\nr 76 x __doptr\n"
                "r 82 x __doptr\nr 87 u1\nr 98 x __doy\nr 101 x __doyhi\n"
                "r 104 x __doy\nr 107 x __doyhi\nr 142 x __doa\nr 144 x __dob\n",
                "rt_f_cmp",
                "p0p0T0S0p2u0T1S1dp4u0T0S0L0U0L1U1u1p5gtop6S2r",
            ),
            (
                "binary-add",
                "REAL A\rREAL B\rREAL C\rCARD Y\r",
                "A=REAL(0)\rB=REAL(3)\rC=REAL(1)\rDO\rA=A+C\r"
                "UNTIL A>B\rOD\rY=7\r",
                binary_exports,
                "b u0u1u2M\nb M\nb M\nb M\nb M\nb M\nb M\nb M\n",
                "C9 01 D0 B5 A9 07 A2 00 8D 00 00 8E 00 00",
                "r 100 u1\nr 105 x __doptr\nr 111 x __doptr\nr 118 x __doptr\n"
                "r 124 x __doptr\nr 129 u2\nr 140 x __doy\nr 143 x __doyhi\n"
                "r 146 x __doy\nr 149 x __doyhi\nr 188 x __doa\n"
                "r 190 x __dob\nr 192 x __doc\n",
                "rt_f_add",
                "p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p5gtop6S3r",
            ),
            (
                "binary-sub-zero",
                "REAL A\rREAL B\rREAL C\rCARD Y\r",
                "A=REAL(3)\rB=REAL(0)\rC=REAL(1)\rDO\rA=A-C\r"
                "UNTIL A>B\rOD\rY=7\r",
                binary_exports,
                "b u0u1u2M\nb M\nb M\nb M\nb M\nb M\nb M\nb M\n",
                "A9 03 A2 00 20 00 00 A2 02 BD 00 00 85 02",
                "r 100 u1\nr 105 x __doptr\nr 111 x __doptr\nr 118 x __doptr\n"
                "r 124 x __doptr\nr 129 u2\nr 140 x __doy\nr 143 x __doyhi\n"
                "r 146 x __doy\nr 149 x __doyhi\nr 188 x __doa\n"
                "r 190 x __dob\nr 192 x __doc\n",
                "rt_f_sub",
                "p1u0T0S0p2p2T1S1p4u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p5gtop6S3r",
            ),
            (
                "binary-sub-nonzero",
                "REAL A\rREAL B\rREAL C\rCARD Y\r",
                "A=REAL(3)\rB=REAL(1)\rC=REAL(1)\rDO\rA=A-C\r"
                "UNTIL A>=B\rOD\rY=7\r",
                binary_exports,
                "b u0u1u2M\nb M\nb M\nb M\nb M\nb M\nb M\nb M\n",
                "C9 02 B0 B5 A9 07 A2 00 8D 00 00 8E 00 00",
                "r 100 u1\nr 105 x __doptr\nr 111 x __doptr\nr 118 x __doptr\n"
                "r 124 x __doptr\nr 129 u2\nr 140 x __doy\nr 143 x __doyhi\n"
                "r 146 x __doy\nr 149 x __doyhi\nr 188 x __doa\n"
                "r 190 x __dob\nr 192 x __doc\n",
                "rt_f_sub",
                "p1u0T0S0p3u0T1S1p5u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p6gtop7S3r",
            ),
        )
        for name, declarations, statements, exports, bodies, machine, relocs, op, compact in cases:
            with self.subTest(name=name):
                obj = self.compile_overlay_object(
                    "MODULE MAIN\r"
                    f"{declarations}"
                    "PROC MAIN()\r"
                    f"{statements}"
                    "RETURN\r",
                    f"actc-overlay-native-real-do-until-{name}",
                )

                self.assertEqual(self.last_emit_overlay_pass, [11])
                self.assertIn(exports, obj)
                self.assertIn(bodies, obj)
                self.assertIn(machine, obj)
                self.assertIn(relocs, obj)
                self.assertIn("u rt_i_to_f\n", obj)
                self.assertIn(f"u {op}\n", obj)
                self.assertNotIn(f"b {compact}\n", obj)

    def test_native_real_while_emitter_owns_layout_families(self) -> None:
        simple_exports = (
            "x main 0 149\nx __whloop 40 1\nx __idata 135 14\nx __wha 135 4\n"
            "x __whb 139 4\nx __why 143 2\nx __whyhi 144 1\nx __whptr 145 4\n"
        )
        binary_exports = (
            "x main 0 197\nx __whloop 60 1\nx __idata 177 20\nx __wha 177 4\n"
            "x __whb 181 4\nx __whc 185 4\nx __why 189 2\nx __whyhi 190 1\n"
            "x __whptr 191 6\n"
        )
        simple_bodies = "b u0u1M\nb M\nb M\nb M\nb M\nb M\nb M\nb M\n"
        binary_bodies = "b u0u1u2M\nb M\nb M\nb M\nb M\nb M\nb M\nb M\nb M\n"
        simple_relocs = (
            "r 86 x __whptr\nr 92 x __whptr\nr 101 u0\n"
            "r 104 x __whloop\nr 107 x __why\nr 110 x __whyhi\n"
            "r 145 x __wha\nr 147 x __whb\n"
        )
        binary_relocs = (
            "r 143 u2\nr 146 x __whloop\nr 149 x __why\nr 152 x __whyhi\n"
            "r 191 x __wha\nr 193 x __whb\nr 195 x __whc\n"
        )
        cases = (
            (
                "simple-zero",
                "REAL A\rREAL B\rCARD Y\r",
                "A=REAL(2)\rB=REAL(1)\rWHILE A>B DO\rY=7\rA=REAL(0)\rOD\r",
                False,
                None,
                "C9 01 D0 21",
                "p1u0T0S0p3u0T1S1dL0U0L1U1u1p4gfp5S2p6p6T0S0xr",
            ),
            (
                "simple-convert",
                "REAL A\rREAL B\rCARD Y\r",
                "A=REAL(1)\rB=REAL(2)\rWHILE A<B DO\rY=7\rB=REAL(1)\rOD\r",
                False,
                None,
                "C9 FF D0 21",
                "p1u0T0S0p3u0T1S1dL0U0L1U1u1p4lfp5S2p7u0T1S1xr",
            ),
            (
                "binary-add",
                "REAL A\rREAL B\rREAL C\rCARD Y\r",
                "A=REAL(0)\rB=REAL(3)\rC=REAL(1)\rWHILE A<B DO\rY=7\rA=A+C\rOD\r",
                True,
                "rt_f_add",
                "C9 FF D0 37",
                "p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L1U1u1p5lfp6S3L0U0L2U2u2T0S0xr",
            ),
            (
                "binary-sub-zero",
                "REAL A\rREAL B\rREAL C\rCARD Y\r",
                "A=REAL(3)\rB=REAL(0)\rC=REAL(1)\rWHILE A>B DO\rY=7\rA=A-C\rOD\r",
                True,
                "rt_f_sub",
                "C9 01 D0 37",
                "p1u0T0S0p2p2T1S1p4u0T2S2dL0U0L1U1u1p5gfp6S3L0U0L2U2u2T0S0xr",
            ),
            (
                "binary-sub-nonzero",
                "REAL A\rREAL B\rREAL C\rCARD Y\r",
                "A=REAL(3)\rB=REAL(1)\rC=REAL(1)\rWHILE A>=B DO\rY=7\rA=A-C\rOD\r",
                True,
                "rt_f_sub",
                "C9 02 B0 37",
                "p1u0T0S0p3u0T1S1p5u0T2S2dL0U0L1U1u1p6gfp7S3L0U0L2U2u2T0S0xr",
            ),
        )
        for name, declarations, statements, binary, op, condition, compact in cases:
            with self.subTest(name=name):
                obj = self.compile_overlay_object(
                    "MODULE MAIN\r"
                    f"{declarations}"
                    "PROC MAIN()\r"
                    f"{statements}"
                    "RETURN\r",
                    f"actc-overlay-native-real-while-{name}",
                )

                self.assertEqual(self.last_emit_overlay_pass, [12])
                self.assertIn(binary_exports if binary else simple_exports, obj)
                self.assertIn(binary_bodies if binary else simple_bodies, obj)
                self.assertIn(condition, obj)
                self.assertIn(binary_relocs if binary else simple_relocs, obj)
                self.assertIn("u rt_i_to_f\n", obj)
                self.assertIn("u rt_f_cmp\n", obj)
                if op is not None:
                    self.assertIn(f"u {op}\n", obj)
                self.assertNotIn(f"b {compact}\n", obj)

    def test_native_runtime_condition_emitter_owns_argument_and_noarg_forms(self) -> None:
        cases = (
            (
                "argument-equal",
                "IF Joy(2)=0 THEN\rBgColor(6)\rFI\r",
                "x main 0 30\n",
                "m A9 02 20 00 00 C9 00 D0 05 A9 06 20 00 00 ",
                "r 3 u0\nr 12 u1\n",
                "u rt_joy\nu rt_gfx_bgcolor\n",
                "p0u0p1qhp2u1vr",
            ),
            (
                "noarg-not-equal",
                "IF MouseBtn()<>1 THEN\rBgColor(7)\rFI\r",
                "x main 0 28\n",
                "m 20 00 00 C9 01 F0 05 A9 07 20 00 00 ",
                "r 1 u0\nr 10 u1\n",
                "u rt_mb\nu rt_gfx_bgcolor\n",
                "u0p0nhp1u1vr",
            ),
        )
        for name, statements, export, machine, relocs, imports, compact in cases:
            with self.subTest(name=name):
                obj = self.compile_overlay_object(
                    "MODULE MAIN\rPROC MAIN()\r" + statements + "RETURN\r",
                    f"actc-overlay-native-runtime-condition-{name}",
                )

                self.assertEqual(self.last_emit_overlay_pass, [13])
                self.assertIn(export, obj)
                self.assertIn("b u0u1M\n", obj)
                self.assertIn(machine, obj)
                self.assertIn(relocs, obj)
                self.assertIn(imports, obj)
                self.assertNotIn(f"b {compact}\n", obj)

    def test_native_runtime_sequence_emitter_owns_literal_helper_chain(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "SidWave(1,64)\r"
            "SidOn(1)\r"
            "RETURN\r",
            "actc-overlay-native-runtime-sequence-literal-chain",
        )

        self.assertEqual(self.last_emit_overlay_pass, [14])
        self.assertIn("x main 0 28\n", obj)
        self.assertIn("b u0u1M\n", obj)
        self.assertIn("m A9 01 A0 40 20 00 00 A9 01 20 00 00 ", obj)
        self.assertIn("r 5 u0\nr 10 u1\n", obj)
        self.assertIn("u rt_sid_wave\nu rt_sid_on\n", obj)
        self.assertNotRegex(obj, r"(?m)^b .*p")

    def test_native_runtime_nested_emitter_owns_nested_readback_chain(self) -> None:
        obj = self.compile_overlay_object(
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "SidVol(Joy(2))\r"
            "RETURN\r",
            "actc-overlay-native-runtime-nested-readback-chain",
        )

        self.assertEqual(self.last_emit_overlay_pass, [15])
        self.assertIn("x main 0 24\n", obj)
        self.assertIn("b u1u0M\n", obj)
        self.assertIn("m A9 02 20 00 00 20 00 00 ", obj)
        self.assertIn("r 3 u1\nr 6 u0\n", obj)
        self.assertIn("u rt_sid_vol\nu rt_joy\n", obj)
        self.assertNotRegex(obj, r"(?m)^b .*p")

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
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [10], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVLA.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL6.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn(
                "x main 0 66\nx __idata 58 6\nx __iresult 62 2\n"
                "x __iresulthi 63 1\nx __iptr 64 2\n",
                obj,
            )
            self.assertIn("b u0u1M\nb M\nb M\nb M\nb M\n", obj)
            self.assertIn("r 18 u0\n", obj)
            self.assertIn("r 34 u1\n", obj)
            self.assertIn("r 37 x __iresult\n", obj)
            self.assertIn("r 40 x __iresulthi\n", obj)
            self.assertIn("r 64 x __idata\n", obj)
            self.assertIn("L 0 0 0 5 1\n", obj)
            self.assertIn("L 0 42 0 7 1\n", obj)
            self.assertNotIn("b p1u0T0S0L0U0u1S1r\n", obj)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [10], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVLA.BIN" and op["status"] == 1 for op in summary["ops"]),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn(
                "x main 0 132\n"
                "x __idata 114 12\n"
                "x __ireala 114 4\n"
                "x __irealb 118 4\n"
                "x __irealx 122 4\n"
                "x __iptr 126 6\n",
                obj,
            )
            self.assertIn("b u0u1u2M\nb M\nb M\nb M\nb M\nb M\n", obj)
            self.assertEqual(
                sum(line.startswith("x ") for line in obj.splitlines()),
                sum(line.startswith("b ") for line in obj.splitlines()),
                msg=obj,
            )
            self.assertIn(
                "m A2 00 BD 00 00 85 02 E8 BD 00 00 85 03 A9 03 A2 00 20 00 00 ",
                obj,
            )
            self.assertIn(
                "r 3 x __iptr\n"
                "r 9 x __iptr\n"
                "r 18 u0\n"
                "r 23 x __iptr\n"
                "r 29 x __iptr\n"
                "r 38 u0\n"
                "r 43 x __iptr\n"
                "r 49 x __iptr\n"
                "r 56 x __iptr\n"
                "r 62 x __iptr\n"
                "r 69 x __iptr\n"
                "r 75 x __iptr\n"
                "r 80 u1\n"
                "r 85 x __iptr\n"
                "r 91 x __iptr\n"
                "r 96 u2\n"
                "r 126 x __ireala\n"
                "r 128 x __irealb\n"
                "r 130 x __irealx\n",
                obj,
            )
            self.assertNotIn("b p1u0T0S0p3u0T1S1L0U0L1U1u1T2S2L2U2p4u2r\n", obj)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
            self.assertIn(summary["dumps"]["actc_overlay_requested_pass"], ([5], [8]), msg=result.stdout)
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
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 0)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        entry_offset = entry - load_base
        self.assertEqual(data[entry_offset], 0x8E)

    def test_native_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_native_object.sh")])

        overlay = self.build_dir / "ACTC_OVL8.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 8)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_object.map",
            "ACTC_OVL8.BIN",
            self.ACTC_NATIVE_INTEGER_EMIT_MIN_HEADROOM,
        )
        labels = (self.build_dir / "actc_overlay_emit_native_object.labels").read_text(encoding="ascii")
        self.assertIn(".is_main_native_integer_machine_object", labels)

    def test_native_local_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_native_local_object.sh")])

        overlay = self.build_dir / "ACTC_OVL9.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 9)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_local_object.map",
            "ACTC_OVL9.BIN",
            self.ACTC_NATIVE_LOCAL_EMIT_MIN_HEADROOM,
        )
        labels = (self.build_dir / "actc_overlay_emit_native_local_object.labels").read_text(
            encoding="ascii"
        )
        self.assertIn(".native_local_emit_reloc_list", labels)

    def test_native_local_runtime_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_local_runtime_object.sh")]
        )

        overlay = self.build_dir / "ACTC_OVLG.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 16)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_local_runtime_object.map",
            "ACTC_OVLG.BIN",
            self.ACTC_NATIVE_LOCAL_RUNTIME_EMIT_MIN_HEADROOM,
        )
        labels = (
            self.build_dir / "actc_overlay_emit_native_local_runtime_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_local_emit_external_a_call", labels)

    def test_native_fixed_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_fixed_object.sh")]
        )
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_real_function_object.sh")]
        )

        overlay = self.build_dir / "ACTC_OVLJ.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 19)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_fixed_object.map",
            "ACTC_OVLJ.BIN",
            self.ACTC_NATIVE_FIXED_EMIT_MIN_HEADROOM,
        )
        labels = (
            self.build_dir / "actc_overlay_emit_native_fixed_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_local_emit_fixed_call", labels)

    def test_native_local_mixed_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_local_mixed_object.sh")]
        )

        overlay = self.build_dir / "ACTC_OVLH.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 17)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_local_mixed_object.map",
            "ACTC_OVLH.BIN",
            self.ACTC_NATIVE_LOCAL_MIXED_EMIT_MIN_HEADROOM,
        )
        labels = (
            self.build_dir / "actc_overlay_emit_native_local_mixed_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_local_emit_asmblock", labels)
        self.assertIn(".native_local_emit_external_a_call", labels)
        self.assertIn(".native_local_emit_fixed_call", labels)
        self.assertIn(".native_local_emit_machine_arguments", labels)

    def test_native_real_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_emit_native_real_object.sh")])

        overlay = self.build_dir / "ACTC_OVLA.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 10)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_real_object.map",
            "ACTC_OVLA.BIN",
            self.ACTC_NATIVE_REAL_EMIT_MIN_HEADROOM,
        )
        labels = (self.build_dir / "actc_overlay_emit_native_real_object.labels").read_text(
            encoding="ascii"
        )
        self.assertIn(".native_real_detect", labels)
        self.assertIn(".native_real_emit_machine_code_list", labels)

    def test_native_real_control_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_real_control_object.sh")]
        )

        overlay = self.build_dir / "ACTC_OVLB.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 11)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_real_control_object.map", "ACTC_OVLB.BIN"
        )
        labels = (
            self.build_dir / "actc_overlay_emit_native_real_control_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_real_control_detect", labels)
        self.assertIn(".native_real_control_emit_machine_code_list", labels)

    def test_native_real_function_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_real_function_object.sh")]
        )

        overlay = self.build_dir / "ACTC_OVLK.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 20)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_real_function_object.map",
            "ACTC_OVLK.BIN",
            self.ACTC_NATIVE_REAL_FUNCTION_EMIT_MIN_HEADROOM,
        )
        labels = (
            self.build_dir / "actc_overlay_emit_native_real_function_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_real_function_detect", labels)
        self.assertIn(".native_real_function_emit_machine_code_list", labels)

    def test_native_real_postfix_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_real_postfix_object.sh")]
        )

        overlay = self.build_dir / "ACTC_OVLL.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 21)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_real_postfix_object.map",
            "ACTC_OVLL.BIN",
            self.ACTC_NATIVE_REAL_POSTFIX_EMIT_MIN_HEADROOM,
        )
        labels = (
            self.build_dir / "actc_overlay_emit_native_real_postfix_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_real_postfix_detect", labels)
        self.assertIn(".native_real_postfix_emit_machine_code_list", labels)

    def test_native_real_postfix_control_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [
                str(
                    self.root
                    / "tools"
                    / "build_actc_overlay_emit_native_real_postfix_control_object.sh"
                )
            ]
        )

        overlay = self.build_dir / "ACTC_OVLM.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 22)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_real_postfix_control_object.map",
            "ACTC_OVLM.BIN",
            self.ACTC_NATIVE_REAL_POSTFIX_CONTROL_EMIT_MIN_HEADROOM,
        )
        labels = (
            self.build_dir
            / "actc_overlay_emit_native_real_postfix_control_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_real_postfix_detect", labels)
        self.assertIn(".nrp_parse_if", labels)

    def test_native_real_postfix_multi_control_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [
                str(
                    self.root
                    / "tools"
                    / "build_actc_overlay_emit_native_real_postfix_multi_control_object.sh"
                )
            ]
        )

        overlay = self.build_dir / "ACTC_OVLN.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 23)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_real_postfix_multi_control_object.map",
            "ACTC_OVLN.BIN",
            self.ACTC_NATIVE_REAL_POSTFIX_MULTI_CONTROL_EMIT_MIN_HEADROOM,
        )
        labels = (
            self.build_dir
            / "actc_overlay_emit_native_real_postfix_multi_control_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_real_postfix_detect", labels)
        self.assertIn(".nrp_control_stack", labels)

    def test_native_real_postfix_extended_control_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [
                str(
                    self.root
                    / "tools"
                    / "build_actc_overlay_emit_native_real_postfix_extended_control_object.sh"
                )
            ]
        )

        overlay = self.build_dir / "ACTC_OVLO.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 24)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_real_postfix_extended_control_object.map",
            "ACTC_OVLO.BIN",
            self.ACTC_NATIVE_REAL_POSTFIX_EXTENDED_CONTROL_EMIT_MIN_HEADROOM,
        )
        labels = (
            self.build_dir
            / "actc_overlay_emit_native_real_postfix_extended_control_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_real_postfix_detect", labels)
        self.assertIn(".nrp_control_stack", labels)

    def test_native_real_postfix_early_return_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [
                str(
                    self.root
                    / "tools"
                    / "build_actc_overlay_emit_native_real_postfix_early_return_object.sh"
                )
            ]
        )

        overlay = self.build_dir / "ACTC_OVLP.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 25)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_real_postfix_early_return_object.map",
            "ACTC_OVLP.BIN",
            self.ACTC_NATIVE_REAL_POSTFIX_EARLY_RETURN_EMIT_MIN_HEADROOM,
        )
        labels = (
            self.build_dir
            / "actc_overlay_emit_native_real_postfix_early_return_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_real_postfix_detect", labels)
        self.assertIn(".nrp_early_return_seen", labels)

    def test_native_real_postfix_loop_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [
                str(
                    self.root
                    / "tools"
                    / "build_actc_overlay_emit_native_real_postfix_loop_object.sh"
                )
            ]
        )

        overlay = self.build_dir / "ACTC_OVLQ.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 26)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_real_postfix_loop_object.map",
            "ACTC_OVLQ.BIN",
            self.ACTC_NATIVE_REAL_POSTFIX_LOOP_EMIT_MIN_HEADROOM,
        )
        labels = (
            self.build_dir
            / "actc_overlay_emit_native_real_postfix_loop_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_real_postfix_detect", labels)
        self.assertIn(".nrp_loop_stack", labels)

    def test_native_real_postfix_loop_exit_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [
                str(
                    self.root
                    / "tools"
                    / "build_actc_overlay_emit_native_real_postfix_loop_exit_object.sh"
                )
            ]
        )

        overlay = self.build_dir / "ACTC_OVLR.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 27)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_real_postfix_loop_exit_object.map",
            "ACTC_OVLR.BIN",
            self.ACTC_NATIVE_REAL_POSTFIX_LOOP_EXIT_EMIT_MIN_HEADROOM,
        )
        labels = (
            self.build_dir
            / "actc_overlay_emit_native_real_postfix_loop_exit_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_real_postfix_detect", labels)
        self.assertIn(".nrp_loop_special_seen_any", labels)
        self.assertIn(".nrp_loop_user_exit", labels)

    def test_native_real_postfix_for_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [
                str(
                    self.root
                    / "tools"
                    / "build_actc_overlay_emit_native_real_postfix_for_object.sh"
                )
            ]
        )

        overlay = self.build_dir / "ACTC_OVLS.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 28)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_real_postfix_for_object.map",
            "ACTC_OVLS.BIN",
            self.ACTC_NATIVE_REAL_POSTFIX_FOR_EMIT_MIN_HEADROOM,
        )
        labels = (
            self.build_dir
            / "actc_overlay_emit_native_real_postfix_for_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_real_postfix_detect", labels)
        self.assertIn(".nrp_for_seen_any", labels)
        self.assertIn(".nrp_for_counter", labels)

    def test_native_real_postfix_for_dynamic_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [
                str(
                    self.root
                    / "tools"
                    / "build_actc_overlay_emit_native_real_postfix_for_dynamic_object.sh"
                )
            ]
        )

        overlay = self.build_dir / "ACTC_OVLT.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 29)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_real_postfix_for_dynamic_object.map",
            "ACTC_OVLT.BIN",
            self.ACTC_NATIVE_REAL_POSTFIX_FOR_DYNAMIC_EMIT_MIN_HEADROOM,
        )
        labels = (
            self.build_dir
            / "actc_overlay_emit_native_real_postfix_for_dynamic_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_real_postfix_detect", labels)
        self.assertIn(".nrp_for_dynamic_seen_any", labels)
        self.assertIn(".nrp_for_final_temp", labels)

    def test_native_real_postfix_literal_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [
                str(
                    self.root
                    / "tools"
                    / "build_actc_overlay_emit_native_real_postfix_literal_object.sh"
                )
            ]
        )

        overlay = self.build_dir / "ACTC_OVLU.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 30)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_real_postfix_literal_object.map",
            "ACTC_OVLU.BIN",
            self.ACTC_NATIVE_REAL_POSTFIX_LITERAL_EMIT_MIN_HEADROOM,
        )
        labels = (
            self.build_dir
            / "actc_overlay_emit_native_real_postfix_literal_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_real_postfix_detect", labels)
        self.assertIn(".nrp_control_stack", labels)
        self.assertIn(".nrp_early_return_seen", labels)
        self.assertIn(".nrp_literal_seen", labels)
        self.assertIn(".nrp_angle_seen", labels)
        self.assertIn(".nrp_function_param_count", labels)

    def test_native_real_while_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_real_while_object.sh")]
        )

        overlay = self.build_dir / "ACTC_OVLC.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 12)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_real_while_object.map", "ACTC_OVLC.BIN"
        )
        labels = (
            self.build_dir / "actc_overlay_emit_native_real_while_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_real_while_detect", labels)
        self.assertIn(".native_real_while_emit_machine_code_list", labels)

    def test_native_runtime_condition_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_runtime_condition_object.sh")]
        )

        overlay = self.build_dir / "ACTC_OVLD.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 13)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_runtime_condition_object.map", "ACTC_OVLD.BIN"
        )
        labels = (
            self.build_dir / "actc_overlay_emit_native_runtime_condition_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_runtime_condition_detect", labels)
        self.assertIn(".native_runtime_condition_emit_machine_code_list", labels)

    def test_native_runtime_sequence_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_runtime_sequence_object.sh")]
        )

        overlay = self.build_dir / "ACTC_OVLE.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 14)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom(
            "actc_overlay_emit_native_runtime_sequence_object.map", "ACTC_OVLE.BIN"
        )
        labels = (
            self.build_dir / "actc_overlay_emit_native_runtime_sequence_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_runtime_sequence_detect", labels)
        self.assertIn(".native_runtime_sequence_emit_machine_code_list", labels)

    def test_native_runtime_nested_emit_object_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked(
            [str(self.root / "tools" / "build_actc_overlay_emit_native_runtime_nested_object.sh")]
        )

        overlay = self.build_dir / "ACTC_OVLF.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 15)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assertGreaterEqual(
            self.ACTC_OVERLAY_WINDOW_SIZE - len(data),
            self.ACTC_NATIVE_RUNTIME_NESTED_EMIT_MIN_HEADROOM,
        )
        labels = (
            self.build_dir / "actc_overlay_emit_native_runtime_nested_object.labels"
        ).read_text(encoding="ascii")
        self.assertIn(".native_runtime_sequence_detect", labels)
        self.assertIn(".native_runtime_sequence_materialize_pending_result", labels)

    def test_native_local_emit_object_compiles_multi_procedure_control_flow(self) -> None:
        self.build_actc_emit_overlay_stack()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-native-local-control"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text(
                "ACTION PROJECT\rMAIN.ACT\r", encoding="ascii"
            )
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "CARD X\r"
                "CARD Y\r"
                "PROC A()\r"
                "DO\r"
                "Y=2\r"
                "UNTIL Y=2\r"
                "OD\r"
                "RETURN\r"
                "PROC MAIN()\r"
                "X=1\r"
                "Y=0\r"
                "IF X=1 THEN\r"
                "A()\r"
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
            self.assertTrue(
                any(
                    op["kind"] == "rsta"
                    and op["path"] == "!ACTC_OVL9.BIN"
                    and op["status"] == 1
                    for op in summary["ops"]
                ),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn(
                "x main 0 166\n"
                "x a 104 56\n"
                "x __p1l0 88 1\n"
                "x __p0l0 104 1\n"
                "x __idata 160 4\n"
                "x __iptr 164 2\n",
                obj,
            )
            self.assertIn(
                "r 3 x __iptr\n"
                "r 9 x __iptr\n"
                "r 83 x __p1l0\n"
                "r 86 x a\n"
                "r 157 x __p0l0\n"
                "r 164 x __idata\n",
                obj,
            )
            self.assertIn("m A2 00 BD 00 00", obj)
            self.assertNotIn("b dp0S1L1p1qtor", obj)

    def test_native_local_emit_object_compiles_local_call_inside_while(self) -> None:
        self.build_actc_emit_overlay_stack()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "actc-native-local-while"
            image_root = workspace / "IMAGES" / "ACTION.DNP"
            project_root = image_root / "PROJ3"
            source_dir = project_root / "src"
            object_dir = project_root / "OBJ"
            source_dir.mkdir(parents=True)
            object_dir.mkdir()
            (project_root / "ACTION.PROJ").write_text(
                "ACTION PROJECT\rMAIN.ACT\r", encoding="ascii"
            )
            (source_dir / "main.act").write_text(
                "MODULE MAIN\r"
                "CARD X\r"
                "PROC A()\r"
                "X=1\r"
                "RETURN\r"
                "PROC MAIN()\r"
                "X=0\r"
                "WHILE X<1 DO\r"
                "A()\r"
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
            self.assertTrue(
                any(
                    op["kind"] == "rsta"
                    and op["path"] == "!ACTC_OVL9.BIN"
                    and op["status"] == 1
                    for op in summary["ops"]
                ),
                msg=result.stdout,
            )
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertIn(
                "x main 0 111\n"
                "x a 89 18\n"
                "x __p1l0 30 1\n"
                "x __p1l1 73 1\n"
                "x __idata 107 2\n"
                "x __iptr 109 2\n",
                obj,
            )
            self.assertIn(
                "r 3 x __iptr\n"
                "r 9 x __iptr\n"
                "r 65 x __p1l1\n"
                "r 68 x a\n"
                "r 71 x __p1l0\n"
                "r 109 x __idata\n",
                obj,
            )
            self.assertIn("m A2 00 BD 00 00", obj)
            self.assertNotIn("b p0S0dL0p1qfc0xr", obj)

    def test_source_header_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_source_header.sh")])

        overlay = self.build_dir / "ACTC_OVL1.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 1)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))

    def test_preprocess_overlay_builds_with_expected_header_and_headroom(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_preprocess.sh")])

        overlay = self.build_dir / "ACTC_OVLI.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 18)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        # Pass I uses BSS in the shared $8000-$9FFF scratch window; code still
        # has the same hard $A000-$BFFF ceiling as every other ACTC pass.
        self.assertGreaterEqual(self.ACTC_PREPROCESS_CODE_WINDOW_SIZE - len(data), 512)

    def test_decl_counts_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_decl_counts.sh")])

        overlay = self.build_dir / "ACTC_OVL2.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 2)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assertGreaterEqual(
            self.ACTC_OVERLAY_WINDOW_SIZE - len(data),
            self.ACTC_DECL_OVERLAY_MIN_HEADROOM,
        )

    def test_payload_layout_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_payload_layout.sh")])

        overlay = self.build_dir / "ACTC_OVL3.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
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
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
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
            self.assertIn(
                summary["dumps"]["actc_overlay_requested_pass"],
                ([5], [8]),
                msg=result.stdout,
            )
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
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [14], msg=result.stdout)
            obj = (object_dir / "MAIN.OBJ").read_text(encoding="ascii")
            self.assertRegex(obj, r"(?m)^b (?:u[0-9A-Z])+M$")
            self.assertIn("\nm ", obj)
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
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 5)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        self.assert_emit_overlay_map_keeps_headroom("actc_overlay_emit_object.map", "ACTC_OVL5.BIN")
        labels = (self.build_dir / "actc_overlay_emit_object.labels").read_text(encoding="ascii")
        self.assertNotIn(".is_main_native_integer_machine_object", labels)
        self.assertNotIn(".native_real_detect", labels)
        self.assertNotIn(".native_real_emit_machine_code_list", labels)

    def test_body_collect_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_collect.sh")])

        overlay = self.build_dir / "ACTC_OVL6.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
        self.assertEqual(data[5], 6)

        load_base = data[6] | (data[7] << 8)
        entry = data[8] | (data[9] << 8)
        length = data[10] | (data[11] << 8)
        self.assertEqual(load_base, 0xA000)
        self.assertEqual(entry, 0xA000 + 14)
        self.assertEqual(length, len(data))
        real_value_entry = data[12] | (data[13] << 8)
        self.assertGreaterEqual(real_value_entry, entry)
        self.assertLess(real_value_entry, load_base + length)

    def test_body_preallocate_overlay_builds_with_expected_header(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_actc_overlay_body_preallocate.sh")])

        overlay = self.build_dir / "ACTC_OVL7.BIN"
        data = overlay.read_bytes()
        self.assertGreaterEqual(len(data), 18)
        self.assertEqual(data[0:4], b"ACOV")
        self.assertEqual(data[4], self.ACTC_OVERLAY_ABI_VERSION)
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
            source_ptr = self.overlay_context_offset("SOURCE_WINDOW_PTR_LO")
            source_len = self.overlay_context_offset("SOURCE_WINDOW_LEN_LO")
            module_name = self.overlay_context_offset("MODULE_NAME_PTR_LO")
            self.assertNotEqual(context[source_ptr:source_ptr + 2], [0, 0], msg=result.stdout)
            self.assertEqual(
                context[source_len:source_len + 5],
                [14, 0, 14, 0, 0],
                msg=result.stdout,
            )
            self.assertNotEqual(context[module_name:module_name + 2], [0, 0], msg=result.stdout)
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
            diag_ptr = self.overlay_context_offset("DIAG_PTR_LO")
            self.assertNotEqual(
                summary["dumps"]["actc_overlay_context"][diag_ptr:diag_ptr + 2],
                [0, 0],
                msg=result.stdout,
            )

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
            source_ptr = self.overlay_context_offset("SOURCE_WINDOW_PTR_LO")
            source_window_len = self.overlay_context_offset("SOURCE_WINDOW_LEN_LO")
            decl_var_count = self.overlay_context_offset("DECL_VAR_COUNT")
            var_count_ptr = self.overlay_context_offset("VAR_COUNT_PTR_LO")
            var_name_window = self.overlay_context_offset("VAR_NAME_WINDOW_PTR_LO")
            export_name_window = self.overlay_context_offset("EXPORT_NAME_WINDOW_PTR_LO")
            self.assertNotEqual(context[source_ptr:source_ptr + 2], [0, 0], msg=result.stdout)
            self.assertEqual(
                context[source_window_len:source_window_len + 5],
                [source_len & 0xFF, source_len >> 8, source_len & 0xFF, source_len >> 8, 0],
                msg=result.stdout,
            )
            self.assertEqual(context[decl_var_count:decl_var_count + 2], [3, 2], msg=result.stdout)
            self.assertNotEqual(context[var_count_ptr:var_count_ptr + 6], [0] * 6, msg=result.stdout)
            self.assertNotEqual(context[var_name_window:var_name_window + 8], [0] * 8, msg=result.stdout)
            self.assertNotEqual(context[export_name_window:export_name_window + 8], [0] * 8, msg=result.stdout)
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
            "duplicate_grouped_proc_local": "MODULE MAIN\rPROC MAIN()\rINT L,L\rRETURN\r",
            "grouped_local_duplicates_param": "MODULE MAIN\rPROC MAIN(P)\rINT L,P\rRETURN\r",
            "grouped_local_trailing_comma": "MODULE MAIN\rPROC MAIN()\rINT L,\rRETURN\r",
            "grouped_local_initializer": "MODULE MAIN\rPROC MAIN()\rINT L,R=1\rRETURN\r",
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

    def test_actc_runner_rejects_stale_overlay_abi_before_call(self) -> None:
        self.require_toolchain()
        self.run_checked([str(self.root / "tools" / "build_tool_abi_harness.sh")])
        self.run_checked([str(self.root / "tools" / "build_actc_udos.sh")])

        overlay_data = bytearray((self.build_dir / "ACTC_OVL0.BIN").read_bytes())
        self.assertEqual(overlay_data[4], self.ACTC_OVERLAY_ABI_VERSION)
        overlay_data[4] = self.ACTC_OVERLAY_ABI_VERSION - 1

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "stale-overlay-abi"
            workspace.mkdir()
            actc_prg = workspace / "ACTC.PRG"
            shutil.copyfile(self.build_dir / "ACTC.PRG", actc_prg)
            (workspace / "ACTC_OVL0.BIN").write_bytes(overlay_data)
            result = self.run_checked(
                [
                    str(self.build_dir / "tool_abi_harness"),
                    "--prg",
                    str(actc_prg),
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
                    "actc_overlay_requested_pass:1",
                    "--dump",
                    f"actc_overlay_context:{self.CTX_SIZE}",
                    "--dump",
                    "actc_overlay_service_status:1",
                    "--dump",
                    "actc_overlay_memcfg_before_call:1",
                    "--max-steps",
                    "200000",
                ]
            )

            summary = json.loads(result.stdout)
            self.assertTrue(summary["exited"], msg=result.stdout)
            self.assertFalse(summary["hit_limit"], msg=result.stdout)
            self.assertEqual(summary["registers"]["a"], 1, msg=result.stdout)
            self.assertEqual(summary["dumps"]["0x0001"], [0x37], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_requested_pass"], [0], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_context"][0:2], [0, 2], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_service_status"], [1], msg=result.stdout)
            self.assertEqual(summary["dumps"]["actc_overlay_memcfg_before_call"], [0], msg=result.stdout)
            self.assertTrue(
                any(op["kind"] == "rsta" and op["path"] == "!ACTC_OVL0.BIN" for op in summary["ops"]),
                msg=result.stdout,
            )
            self.assertTrue(any(op["kind"] == "rrd" for op in summary["ops"]), msg=result.stdout)

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
