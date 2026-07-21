.include "actc_overlay_abi.inc"

.export actc_overlay_header
.export actc_overlay_entry
.export actc_overlay_end

.segment "CODE"

actc_overlay_header:
    .byte 'A','C','O','V'
    .byte ACTC_OVERLAY_ABI_VERSION
    .byte ACTC_OVERLAY_PASS_BODY_PREALLOCATE
    .word ACTC_OVERLAY_EXEC_BASE
    .word actc_overlay_entry
    .word actc_overlay_end - actc_overlay_header
    .word $0000

actc_overlay_entry:
    stx ACTC_OVERLAY_CONTEXT_ZP
    sty ACTC_OVERLAY_CONTEXT_ZP+1
    ldy #ACTC_OVERLAY_CTX_PASS_ID
    lda #ACTC_OVERLAY_PASS_BODY_PREALLOCATE
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    jsr publish_builtin_runtime_table

    jsr preallocate_body_externals_overlay
    bcs actc_overlay_fail

actc_overlay_ok:
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_OK
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    clc
    rts

actc_overlay_fail:
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_FAILED
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    sec
    rts

publish_builtin_runtime_table:
    ldy #ACTC_OVERLAY_CTX_BUILTIN_RUNTIME_TABLE_PTR_LO
    lda #<builtin_runtime_import_table
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    iny
    lda #>builtin_runtime_import_table
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    rts

preallocate_body_externals_overlay:
    lda #$00
    ldx #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr store_a_to_context_byte_ptr
    lda #$FF
    ldx #ACTC_OVERLAY_CTX_CURRENT_PROC_INDEX_PTR_LO
    jsr store_a_to_context_byte_ptr
    lda #ACTC_OVERLAY_CTX_BEGIN_BODY_SCAN_FN_LO
    jsr call_context_function
    bcc preallocate_body_externals_overlay_loop
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_diag

preallocate_body_externals_overlay_loop:
    jsr load_current_char
    bne preallocate_body_externals_overlay_have_char
    clc
    rts
preallocate_body_externals_overlay_have_char:
    cmp #10
    bne :+
    jmp preallocate_body_externals_overlay_advance_blank
:   cmp #13
    bne :+
    jmp preallocate_body_externals_overlay_advance_blank
:   lda #ACTC_OVERLAY_CTX_SKIP_SOURCE_SPACES_FN_LO
    jsr call_context_function
    jsr load_current_char
    bne preallocate_body_externals_overlay_after_space_check
    clc
    rts
preallocate_body_externals_overlay_after_space_check:
    lda #<pattern_asmblock
    ldy #>pattern_asmblock
    jsr pattern_matches_local_scan_ptr_keyword
    bcs preallocate_body_externals_overlay_not_asmblock
    jmp preallocate_body_externals_overlay_asmblock
preallocate_body_externals_overlay_not_asmblock:
    lda #<pattern_proc
    ldy #>pattern_proc
    jsr pattern_matches_local_scan_ptr
    bcs preallocate_body_externals_overlay_not_proc
    jmp preallocate_body_externals_overlay_proc_decl

preallocate_body_externals_overlay_not_proc:
    lda #ACTC_OVERLAY_CTX_MATCH_SCALAR_DECL_FN_LO
    jsr call_context_function
    bcs preallocate_body_externals_overlay_not_scalar_decl
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_BY_CONST_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_SKIP_SOURCE_SPACES_FN_LO
    jsr call_context_function
    lda #<pattern_func
    ldy #>pattern_func
    jsr pattern_matches_local_scan_ptr_keyword
    bcc :+
    jmp preallocate_body_externals_overlay_skip_line
:
    jmp preallocate_body_externals_overlay_func_decl
preallocate_body_externals_overlay_not_scalar_decl:
    lda #ACTC_OVERLAY_CTX_CURRENT_PROC_INDEX_PTR_LO
    jsr load_byte_from_context_ptr
    cmp #$FF
    bne :+
    jmp preallocate_body_externals_overlay_skip_line
:
    jsr load_current_char
    cmp #'['
    bne preallocate_body_externals_overlay_not_raw_block
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_FN_LO
    jsr call_context_function
    jmp preallocate_body_externals_overlay_skip_asmblock
preallocate_body_externals_overlay_not_raw_block:
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_PTR_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_body_externals_overlay_skip_line
:
    sty symbol_end_y_local
    jsr preallocate_declared_symbol_is_print_statement_overlay
    bcc preallocate_body_externals_overlay_print_statement
    jsr preallocate_declared_symbol_is_condition_statement_overlay
    bcc preallocate_body_externals_overlay_condition_statement
    lda #<pattern_return
    ldy #>pattern_return
    jsr symbol_buffer_matches_local_const
    bcc preallocate_body_externals_overlay_scan_after_symbol
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    sty saved_y_local
    lda #'('
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_body_externals_overlay_call
    lda #'='
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_body_externals_overlay_assignment
    jmp preallocate_body_externals_overlay_skip_line
preallocate_body_externals_overlay_assignment:
    lda symbol_end_y_local
    sta assignment_target_end_y_local
    jsr preallocate_real_unary_assignment_external_from_declared_overlay
    bcc preallocate_body_externals_overlay_skip_line
    ldy assignment_target_end_y_local
    jsr preallocate_word_int_assignment_external_from_declared_overlay
    bcc preallocate_body_externals_overlay_skip_line
    ldy assignment_target_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #'='
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc preallocate_body_externals_overlay_scan_at_y
    jmp preallocate_body_externals_overlay_skip_line
preallocate_body_externals_overlay_scan_after_symbol:
    ldy symbol_end_y_local
preallocate_body_externals_overlay_scan_at_y:
    jsr preallocate_plain_call_args_overlay
    jmp preallocate_body_externals_overlay_skip_line

preallocate_body_externals_overlay_print_statement:
    jsr preallocate_real_print_statement_external_from_declared_overlay
    bcc preallocate_body_externals_overlay_skip_line
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #'('
    jsr preallocate_consume_scan_char_from_y_overlay
    bcs preallocate_body_externals_overlay_skip_line
    jsr preallocate_plain_call_args_overlay
    jmp preallocate_body_externals_overlay_skip_line
preallocate_body_externals_overlay_condition_statement:
    jsr preallocate_real_condition_cmp_external_from_declared_overlay
    bcc preallocate_body_externals_overlay_skip_line
    ldy symbol_end_y_local
    jsr preallocate_line_call_args_overlay
    jmp preallocate_body_externals_overlay_skip_line
preallocate_body_externals_overlay_call:
    lda #ACTC_OVERLAY_CTX_RESOLVE_CALL_TARGET_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_body_externals_overlay_bad_proc
:   ldy saved_y_local
    lda #'('
    jsr preallocate_consume_scan_char_from_y_overlay
    bcs preallocate_body_externals_overlay_skip_line
    jsr preallocate_plain_call_args_overlay
    jmp preallocate_body_externals_overlay_skip_line

preallocate_body_externals_overlay_skip_line:
    lda #ACTC_OVERLAY_CTX_SKIP_SOURCE_LINE_FN_LO
    jsr call_context_function
    jmp preallocate_body_externals_overlay_loop

preallocate_body_externals_overlay_proc_decl:
    lda #<pattern_proc
    ldy #>pattern_proc
    jsr source_reader_consume_local_pattern
    jmp preallocate_body_externals_overlay_routine_decl_after_keyword
preallocate_body_externals_overlay_func_decl:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_BY_CONST_FN_LO
    jsr call_context_function
preallocate_body_externals_overlay_routine_decl_after_keyword:
    lda #ACTC_OVERLAY_CTX_SKIP_SOURCE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_PTR_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_body_externals_overlay_bad_proc
:   lda #ACTC_OVERLAY_CTX_RESOLVE_ROUTINE_DECL_FN_LO
    jsr call_context_function
    bcs preallocate_body_externals_overlay_bad_proc
    txa
    cmp #$FF
    beq preallocate_body_externals_overlay_skip_line
    ldx #ACTC_OVERLAY_CTX_CURRENT_PROC_INDEX_PTR_LO
    jsr store_a_to_context_byte_ptr
    jmp preallocate_body_externals_overlay_skip_line

preallocate_body_externals_overlay_advance_blank:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_FN_LO
    jsr call_context_function
    jmp preallocate_body_externals_overlay_loop

preallocate_body_externals_overlay_bad_proc:
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_diag

preallocate_body_externals_overlay_asmblock:
    lda #<pattern_asmblock
    ldy #>pattern_asmblock
    jsr source_reader_consume_local_pattern
    lda #ACTC_OVERLAY_CTX_SKIP_SOURCE_SPACES_FN_LO
    jsr call_context_function
    jsr load_current_char
    cmp #'['
    bne preallocate_body_externals_overlay_bad_asmblock
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_FN_LO
    jsr call_context_function
preallocate_body_externals_overlay_skip_asmblock:
    jsr load_current_char
    beq preallocate_body_externals_overlay_bad_asmblock
    cmp #']'
    beq preallocate_body_externals_overlay_close_asmblock
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_FN_LO
    jsr call_context_function
    bcc preallocate_body_externals_overlay_skip_asmblock
    jmp preallocate_body_externals_overlay_bad_asmblock
preallocate_body_externals_overlay_close_asmblock:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_FN_LO
    jsr call_context_function
    bcs preallocate_body_externals_overlay_bad_asmblock
    jmp preallocate_body_externals_overlay_skip_line

preallocate_body_externals_overlay_bad_asmblock:
    lda #<msg_bad_asmblock
    ldy #>msg_bad_asmblock
    jmp fail_with_diag

preallocate_real_unary_assignment_external_from_declared_overlay:
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr call_context_function
    bcs preallocate_real_unary_assignment_external_from_declared_overlay_miss
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcs preallocate_real_unary_assignment_external_from_declared_overlay_miss
    ldy assignment_target_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #'='
    jsr preallocate_consume_scan_char_from_y_overlay
    bcs preallocate_real_unary_assignment_external_from_declared_overlay_miss
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    sty assignment_value_start_y_local
    jsr preallocate_real_plain_decimal_assignment_external_from_scan_y_overlay
    bcc preallocate_real_unary_assignment_external_from_declared_overlay_done
    ldy assignment_value_start_y_local
    jsr preallocate_real_binary_function_assignment_external_from_scan_y_overlay
    bcc preallocate_real_unary_assignment_external_from_declared_overlay_done
    ldy assignment_value_start_y_local
    jsr preallocate_real_unary_operator_assignment_external_from_scan_y_overlay
    bcc preallocate_real_unary_assignment_external_from_declared_overlay_done
    ldy assignment_value_start_y_local
    jsr preallocate_real_explicit_bridge_assignment_external_from_scan_y_overlay
    bcc preallocate_real_unary_assignment_external_from_declared_overlay_done
    ldy assignment_value_start_y_local
    jsr preallocate_real_explicit_decimal_assignment_external_from_scan_y_overlay
    bcc preallocate_real_unary_assignment_external_from_declared_overlay_done
    ldy assignment_value_start_y_local
    jsr preallocate_real_binary_operator_assignment_external_from_scan_y_overlay
    bcc preallocate_real_unary_assignment_external_from_declared_overlay_done
    ldy assignment_value_start_y_local
    jsr preallocate_real_copy_or_bridge_assignment_external_from_scan_y_overlay
    bcs preallocate_real_unary_assignment_external_from_declared_overlay_miss
preallocate_real_unary_assignment_external_from_declared_overlay_done:
    clc
    rts
preallocate_real_unary_assignment_external_from_declared_overlay_miss:
    sec
    rts

preallocate_word_int_assignment_external_from_declared_overlay:
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_word_int_assignment_external_from_declared_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_REQUIRE_WORD_VAR_FN_LO
    jsr call_indexed_context_function
    bcc :+
    jmp preallocate_word_int_assignment_external_from_declared_overlay_miss
:
    ldy assignment_target_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #'='
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_word_int_assignment_external_from_declared_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    jsr preallocate_int_conversion_external_from_scan_y_overlay
    bcc :+
    jmp preallocate_word_int_assignment_external_from_declared_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_word_int_assignment_external_from_declared_overlay_miss
:
    clc
    rts
preallocate_word_int_assignment_external_from_declared_overlay_miss:
    sec
    rts

preallocate_int_conversion_external_from_scan_y_overlay:
    sty keyword_scan_y_local
    lda #<pattern_int_decl
    ldy #>pattern_int_decl
    jsr preallocate_consume_keyword_open_from_scan_y_overlay
    bcc :+
    jmp preallocate_int_conversion_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_int_conversion_external_from_scan_y_overlay_miss
:
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_int_conversion_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcc :+
    jmp preallocate_int_conversion_external_from_scan_y_overlay_miss
:
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #')'
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_int_conversion_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_F_TO_I_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_int_conversion_external_from_scan_y_overlay_miss
:
    clc
    rts
preallocate_int_conversion_external_from_scan_y_overlay_miss:
    ldy keyword_scan_y_local
    sec
    rts

preallocate_real_explicit_bridge_assignment_external_from_scan_y_overlay:
    sty keyword_scan_y_local
    lda #<pattern_real_decl
    ldy #>pattern_real_decl
    jsr preallocate_consume_keyword_open_from_scan_y_overlay
    bcc :+
    jmp preallocate_real_explicit_bridge_assignment_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_explicit_bridge_assignment_external_from_scan_y_overlay_miss
:
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_explicit_bridge_assignment_external_from_scan_y_overlay_miss
:
    stx rhs_var_index_local
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_BRIDGE_WORD_VAR_FN_LO
    jsr call_indexed_context_function
    bcc :+
    jmp preallocate_real_explicit_bridge_assignment_external_from_scan_y_overlay_miss
:
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #')'
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_real_explicit_bridge_assignment_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_explicit_bridge_assignment_external_from_scan_y_overlay_miss
:
    ldx rhs_var_index_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_REAL_BRIDGE_EXTERNAL_FN_LO
    jsr call_indexed_context_function
    bcc :+
    jmp preallocate_real_explicit_bridge_assignment_external_from_scan_y_overlay_miss
:
    clc
    rts
preallocate_real_explicit_bridge_assignment_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_print_statement_external_from_declared_overlay:
    lda #<preallocate_symbol_printr
    ldy #>preallocate_symbol_printr
    jsr symbol_buffer_matches_local_const
    bcc preallocate_real_print_statement_external_from_declared_overlay_parse
    lda #<preallocate_symbol_printre
    ldy #>preallocate_symbol_printre
    jsr symbol_buffer_matches_local_const
    bcc preallocate_real_print_statement_external_from_declared_overlay_parse
    sec
    rts
preallocate_real_print_statement_external_from_declared_overlay_parse:
    ldy symbol_end_y_local
    sty symbol_start_y_local
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #'('
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_real_print_statement_external_from_declared_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    jsr preallocate_real_print_value_external_from_scan_y_overlay
    bcc preallocate_real_print_statement_external_from_declared_overlay_after_value
    jmp preallocate_real_print_statement_external_from_declared_overlay_miss
preallocate_real_print_statement_external_from_declared_overlay_after_value:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #')'
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_real_print_statement_external_from_declared_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_print_statement_external_from_declared_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_PRINT_F_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_print_statement_external_from_declared_overlay_miss
:
    clc
    rts
preallocate_real_print_statement_external_from_declared_overlay_miss:
    lda #ACTC_OVERLAY_CTX_RESTORE_SOURCE_MARK_FN_LO
    jsr call_context_function
    lda symbol_start_y_local
    sta symbol_end_y_local
    ldy symbol_start_y_local
    sec
    rts

preallocate_real_print_value_external_from_scan_y_overlay:
    sty assignment_value_start_y_local
    jsr preallocate_real_bridge_conversion_external_from_scan_y_overlay
    bcc preallocate_real_print_value_external_from_scan_y_overlay_done
    ldy assignment_value_start_y_local
    jsr preallocate_real_numeric_conversion_external_from_scan_y_overlay
    bcc preallocate_real_print_value_external_from_scan_y_overlay_done
    ldy assignment_value_start_y_local
    jsr preallocate_real_binary_function_external_from_scan_y_overlay
    bcc preallocate_real_print_value_external_from_scan_y_overlay_done
    ldy assignment_value_start_y_local
    jsr preallocate_real_unary_print_external_from_scan_y_overlay
    bcc preallocate_real_print_value_external_from_scan_y_overlay_done
    ldy assignment_value_start_y_local
    jsr preallocate_real_binary_print_external_from_scan_y_overlay
    bcc preallocate_real_print_value_external_from_scan_y_overlay_done
    ldy assignment_value_start_y_local
    jsr preallocate_real_print_var_external_from_scan_y_overlay
    bcs preallocate_real_print_value_external_from_scan_y_overlay_miss
preallocate_real_print_value_external_from_scan_y_overlay_done:
    clc
    rts
preallocate_real_print_value_external_from_scan_y_overlay_miss:
    ldy assignment_value_start_y_local
    sec
    rts

preallocate_real_print_var_external_from_scan_y_overlay:
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_print_var_external_from_scan_y_overlay_miss
:
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_print_var_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcc :+
    jmp preallocate_real_print_var_external_from_scan_y_overlay_miss
:
    ldy symbol_end_y_local
    clc
    rts
preallocate_real_print_var_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_binary_function_assignment_external_from_scan_y_overlay:
    jsr preallocate_real_binary_function_external_from_scan_y_overlay
    bcs preallocate_real_binary_function_assignment_external_from_scan_y_overlay_miss
    lda #ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    jsr call_context_function
    bcs preallocate_real_binary_function_assignment_external_from_scan_y_overlay_miss
    clc
    rts
preallocate_real_binary_function_assignment_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_binary_function_external_from_scan_y_overlay:
    sty keyword_scan_y_local
    lda #$02
    sta real_function_arity_local
    lda #<pattern_fmin
    ldy #>pattern_fmin
    jsr preallocate_consume_keyword_open_from_scan_y_overlay
    bcs preallocate_real_binary_function_external_from_scan_y_overlay_try_fmax
    lda #'<'
    bne preallocate_real_binary_function_external_from_scan_y_overlay_operator
preallocate_real_binary_function_external_from_scan_y_overlay_try_fmax:
    ldy keyword_scan_y_local
    lda #<pattern_fmax
    ldy #>pattern_fmax
    jsr preallocate_consume_keyword_open_from_scan_y_overlay
    bcc preallocate_real_binary_function_external_from_scan_y_overlay_fmax
    ldy keyword_scan_y_local
    lda #<pattern_fclamp
    ldy #>pattern_fclamp
    jsr preallocate_consume_keyword_open_from_scan_y_overlay
    bcc :+
    jmp preallocate_real_binary_function_external_from_scan_y_overlay_miss
:
    inc real_function_arity_local
    lda #'k'
    bne preallocate_real_binary_function_external_from_scan_y_overlay_operator
preallocate_real_binary_function_external_from_scan_y_overlay_fmax:
    lda #'>'
preallocate_real_binary_function_external_from_scan_y_overlay_operator:
    sta real_operator_local
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcs preallocate_real_binary_function_external_from_scan_y_overlay_fail_near
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr call_context_function
    bcs preallocate_real_binary_function_external_from_scan_y_overlay_fail_near
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcs preallocate_real_binary_function_external_from_scan_y_overlay_fail_near
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #','
    jsr preallocate_consume_scan_char_from_y_overlay
    bcs preallocate_real_binary_function_external_from_scan_y_overlay_fail_near
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcs preallocate_real_binary_function_external_from_scan_y_overlay_fail_near
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr call_context_function
    bcs preallocate_real_binary_function_external_from_scan_y_overlay_fail_near
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcs preallocate_real_binary_function_external_from_scan_y_overlay_fail_near
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda real_function_arity_local
    cmp #$03
    bne preallocate_real_binary_function_external_from_scan_y_overlay_close
    lda #','
    jsr preallocate_consume_scan_char_from_y_overlay
    bcs preallocate_real_binary_function_external_from_scan_y_overlay_fail_near
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcs preallocate_real_binary_function_external_from_scan_y_overlay_miss
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr call_context_function
    bcs preallocate_real_binary_function_external_from_scan_y_overlay_miss
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcs preallocate_real_binary_function_external_from_scan_y_overlay_miss
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    jmp preallocate_real_binary_function_external_from_scan_y_overlay_close
preallocate_real_binary_function_external_from_scan_y_overlay_fail_near:
    jmp preallocate_real_binary_function_external_from_scan_y_overlay_miss
preallocate_real_binary_function_external_from_scan_y_overlay_close:
    lda #')'
    jsr preallocate_consume_scan_char_from_y_overlay
    bcs preallocate_real_binary_function_external_from_scan_y_overlay_miss
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_REAL_OPERATOR_EXTERNAL_FN_LO
    jsr load_context_function_ptr
    lda real_operator_local
    jsr call_loaded_target_with_a
    bcs preallocate_real_binary_function_external_from_scan_y_overlay_miss
    ldy symbol_end_y_local
    clc
    rts
preallocate_real_binary_function_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_bridge_conversion_external_from_scan_y_overlay:
    sty keyword_scan_y_local
    lda #<pattern_real_decl
    ldy #>pattern_real_decl
    jsr preallocate_consume_keyword_open_from_scan_y_overlay
    bcc :+
    jmp preallocate_real_bridge_conversion_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_bridge_conversion_external_from_scan_y_overlay_miss
:
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_bridge_conversion_external_from_scan_y_overlay_miss
:
    stx rhs_var_index_local
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_BRIDGE_WORD_VAR_FN_LO
    jsr call_indexed_context_function
    bcc :+
    jmp preallocate_real_bridge_conversion_external_from_scan_y_overlay_miss
:
    ldy symbol_end_y_local
    jsr preallocate_consume_close_from_scan_y_overlay
    bcc :+
    jmp preallocate_real_bridge_conversion_external_from_scan_y_overlay_miss
:
    sty symbol_end_y_local
    ldx rhs_var_index_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_REAL_BRIDGE_EXTERNAL_FN_LO
    jsr call_indexed_context_function
    bcc :+
    jmp preallocate_real_bridge_conversion_external_from_scan_y_overlay_miss
:
    ldy symbol_end_y_local
    clc
    rts
preallocate_real_bridge_conversion_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_numeric_conversion_external_from_scan_y_overlay:
    sty keyword_scan_y_local
    lda #<pattern_real_decl
    ldy #>pattern_real_decl
    jsr preallocate_consume_keyword_open_from_scan_y_overlay
    bcc :+
    jmp preallocate_real_numeric_conversion_external_from_scan_y_overlay_miss
:
    sty assignment_target_end_y_local
    jsr preallocate_real_numeric_signed_conversion_external_from_scan_y_overlay
    bcc preallocate_real_numeric_conversion_external_from_scan_y_overlay_done
    ldy assignment_target_end_y_local
    jsr preallocate_real_numeric_positive_conversion_external_from_scan_y_overlay
    bcc preallocate_real_numeric_conversion_external_from_scan_y_overlay_done
preallocate_real_numeric_conversion_external_from_scan_y_overlay_miss:
    sec
    rts
preallocate_real_numeric_conversion_external_from_scan_y_overlay_done:
    clc
    rts

preallocate_real_numeric_positive_conversion_external_from_scan_y_overlay:
    jsr parse_positive_word_sum_local_or_fail
    bcs preallocate_real_numeric_positive_conversion_external_from_scan_y_overlay_miss
    jsr preallocate_consume_close_from_scan_y_overlay
    bcs preallocate_real_numeric_positive_conversion_external_from_scan_y_overlay_miss
    sty symbol_end_y_local
    jsr preallocate_expr_value_is_zero_overlay
    bcc preallocate_real_numeric_positive_conversion_external_from_scan_y_overlay_done_restore
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_I_TO_F_FN_LO
    jsr call_context_function
    bcs preallocate_real_numeric_positive_conversion_external_from_scan_y_overlay_miss
preallocate_real_numeric_positive_conversion_external_from_scan_y_overlay_done_restore:
    ldy symbol_end_y_local
preallocate_real_numeric_positive_conversion_external_from_scan_y_overlay_done:
    clc
    rts
preallocate_real_numeric_positive_conversion_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_numeric_signed_conversion_external_from_scan_y_overlay:
    jsr preallocate_consume_signed_word_prefix_from_scan_y_overlay
    bcs preallocate_real_numeric_signed_conversion_external_from_scan_y_overlay_miss
    jsr parse_positive_word_sum_local_or_fail
    bcs preallocate_real_numeric_signed_conversion_external_from_scan_y_overlay_miss
    jsr preallocate_consume_close_from_scan_y_overlay
    bcs preallocate_real_numeric_signed_conversion_external_from_scan_y_overlay_miss
    sty symbol_end_y_local
    jsr preallocate_expr_value_is_zero_overlay
    bcc preallocate_real_numeric_signed_conversion_external_from_scan_y_overlay_done_restore
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_S_TO_F_FN_LO
    jsr call_context_function
    bcs preallocate_real_numeric_signed_conversion_external_from_scan_y_overlay_miss
preallocate_real_numeric_signed_conversion_external_from_scan_y_overlay_done_restore:
    ldy symbol_end_y_local
preallocate_real_numeric_signed_conversion_external_from_scan_y_overlay_done:
    clc
    rts
preallocate_real_numeric_signed_conversion_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_unary_print_external_from_scan_y_overlay:
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_unary_print_external_from_scan_y_overlay_miss
:
    sty symbol_end_y_local
    lda #<pattern_fabs
    ldy #>pattern_fabs
    jsr symbol_buffer_matches_local_const
    bcc preallocate_real_unary_print_external_from_scan_y_overlay_fabs
    lda #<pattern_fsqrt
    ldy #>pattern_fsqrt
    jsr symbol_buffer_matches_local_const
    bcc preallocate_real_unary_print_external_from_scan_y_overlay_fsqrt
    lda #<pattern_fsign
    ldy #>pattern_fsign
    jsr symbol_buffer_matches_local_const
    bcc preallocate_real_unary_print_external_from_scan_y_overlay_fsign
    lda #<pattern_ftrunc
    ldy #>pattern_ftrunc
    jsr symbol_buffer_matches_local_const
    bcc preallocate_real_unary_print_external_from_scan_y_overlay_ftrunc
    lda #<pattern_ffloor
    ldy #>pattern_ffloor
    jsr symbol_buffer_matches_local_const
    bcc preallocate_real_unary_print_external_from_scan_y_overlay_ffloor
    lda #<pattern_fceil
    ldy #>pattern_fceil
    jsr symbol_buffer_matches_local_const
    bcc preallocate_real_unary_print_external_from_scan_y_overlay_fceil
    lda #<pattern_fround
    ldy #>pattern_fround
    jsr symbol_buffer_matches_local_const
    bcc preallocate_real_unary_print_external_from_scan_y_overlay_fround
    sec
    rts
preallocate_real_unary_print_external_from_scan_y_overlay_fabs:
    lda #'a'
    bne preallocate_real_unary_print_external_from_scan_y_overlay_operator
preallocate_real_unary_print_external_from_scan_y_overlay_fsqrt:
    lda #'q'
    bne preallocate_real_unary_print_external_from_scan_y_overlay_operator
preallocate_real_unary_print_external_from_scan_y_overlay_fsign:
    lda #'g'
    bne preallocate_real_unary_print_external_from_scan_y_overlay_operator
preallocate_real_unary_print_external_from_scan_y_overlay_ftrunc:
    lda #'c'
    bne preallocate_real_unary_print_external_from_scan_y_overlay_operator
preallocate_real_unary_print_external_from_scan_y_overlay_ffloor:
    lda #'o'
    bne preallocate_real_unary_print_external_from_scan_y_overlay_operator
preallocate_real_unary_print_external_from_scan_y_overlay_fceil:
    lda #'l'
    bne preallocate_real_unary_print_external_from_scan_y_overlay_operator
preallocate_real_unary_print_external_from_scan_y_overlay_fround:
    lda #'r'
preallocate_real_unary_print_external_from_scan_y_overlay_operator:
    sta real_operator_local
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #'('
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_real_unary_print_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_unary_print_external_from_scan_y_overlay_miss
:
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_unary_print_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcc :+
    jmp preallocate_real_unary_print_external_from_scan_y_overlay_miss
:
    ldy symbol_end_y_local
    jsr preallocate_consume_close_from_scan_y_overlay
    bcc :+
    jmp preallocate_real_unary_print_external_from_scan_y_overlay_miss
:
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_REAL_OPERATOR_EXTERNAL_FN_LO
    jsr load_context_function_ptr
    lda real_operator_local
    jsr call_loaded_target_with_a
    bcc :+
    jmp preallocate_real_unary_print_external_from_scan_y_overlay_miss
:
    ldy symbol_end_y_local
    clc
    rts
preallocate_real_unary_print_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_binary_print_external_from_scan_y_overlay:
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_binary_print_external_from_scan_y_overlay_miss
:
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_binary_print_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcc :+
    jmp preallocate_real_binary_print_external_from_scan_y_overlay_miss
:
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #'+'
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_real_binary_print_external_from_scan_y_overlay_operator
    lda #'-'
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_real_binary_print_external_from_scan_y_overlay_operator
    lda #'*'
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_real_binary_print_external_from_scan_y_overlay_operator
    lda #'/'
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_real_binary_print_external_from_scan_y_overlay_operator
    jmp preallocate_real_binary_print_external_from_scan_y_overlay_miss
preallocate_real_binary_print_external_from_scan_y_overlay_operator:
    sta real_operator_local
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_real_binary_print_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_binary_print_external_from_scan_y_overlay_miss
:
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_binary_print_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcc :+
    jmp preallocate_real_binary_print_external_from_scan_y_overlay_miss
:
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_REAL_OPERATOR_EXTERNAL_FN_LO
    jsr load_context_function_ptr
    lda real_operator_local
    jsr call_loaded_target_with_a
    bcc :+
    jmp preallocate_real_binary_print_external_from_scan_y_overlay_miss
:
    ldy symbol_end_y_local
    clc
    rts
preallocate_real_binary_print_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_condition_cmp_external_from_declared_overlay:
    lda #<pattern_if
    ldy #>pattern_if
    jsr symbol_buffer_matches_local_const
    bcs preallocate_real_condition_cmp_external_from_declared_overlay_not_if
    lda #'h'
    bne preallocate_real_condition_cmp_external_from_declared_overlay_parse
preallocate_real_condition_cmp_external_from_declared_overlay_not_if:
    lda #<pattern_while
    ldy #>pattern_while
    jsr symbol_buffer_matches_local_const
    bcs preallocate_real_condition_cmp_external_from_declared_overlay_not_while
    lda #'f'
    bne preallocate_real_condition_cmp_external_from_declared_overlay_parse
preallocate_real_condition_cmp_external_from_declared_overlay_not_while:
    lda #<pattern_until
    ldy #>pattern_until
    jsr symbol_buffer_matches_local_const
    bcc :+
    sec
    rts
:
    lda #'t'
preallocate_real_condition_cmp_external_from_declared_overlay_parse:
    sta condition_mode_local
    ldy symbol_end_y_local
    sty symbol_start_y_local
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    jsr preallocate_real_condition_cmp_external_from_scan_y_overlay
    bcc preallocate_real_condition_cmp_external_from_declared_overlay_done
    lda #ACTC_OVERLAY_CTX_RESTORE_SOURCE_MARK_FN_LO
    jsr call_context_function
    lda symbol_start_y_local
    sta symbol_end_y_local
    ldy symbol_start_y_local
    sec
    rts
preallocate_real_condition_cmp_external_from_declared_overlay_done:
    clc
    rts

preallocate_real_condition_cmp_external_from_scan_y_overlay:
    jsr preallocate_real_condition_value_external_from_scan_y_overlay
    bcc preallocate_real_condition_cmp_external_from_scan_y_overlay_after_lhs
    jmp preallocate_real_condition_cmp_external_from_scan_y_overlay_miss
preallocate_real_condition_cmp_external_from_scan_y_overlay_after_lhs:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #'='
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_one
    lda #'<'
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_lt
    lda #'>'
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_gt
    jmp preallocate_real_condition_cmp_external_from_scan_y_overlay_miss
preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_one:
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc preallocate_real_condition_cmp_external_from_scan_y_overlay_rhs
    jmp preallocate_real_condition_cmp_external_from_scan_y_overlay_miss
preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_lt:
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_real_condition_cmp_external_from_scan_y_overlay_miss
:
    lda #'>'
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_second
    lda #'='
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_second
    jmp preallocate_real_condition_cmp_external_from_scan_y_overlay_rhs
preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_gt:
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_real_condition_cmp_external_from_scan_y_overlay_miss
:
    lda #'='
    jsr preallocate_match_scan_char_from_y_overlay
    bcs preallocate_real_condition_cmp_external_from_scan_y_overlay_rhs
preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_second:
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_real_condition_cmp_external_from_scan_y_overlay_miss
:
preallocate_real_condition_cmp_external_from_scan_y_overlay_rhs:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    jsr preallocate_real_condition_value_external_from_scan_y_overlay
    bcc preallocate_real_condition_cmp_external_from_scan_y_overlay_after_rhs
    jmp preallocate_real_condition_cmp_external_from_scan_y_overlay_miss
preallocate_real_condition_cmp_external_from_scan_y_overlay_after_rhs:
    jsr preallocate_require_condition_terminator_from_scan_y_overlay
    bcc :+
    jmp preallocate_real_condition_cmp_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_F_CMP_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_condition_cmp_external_from_scan_y_overlay_miss
:
    clc
    rts
preallocate_real_condition_cmp_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_condition_value_external_from_scan_y_overlay:
    jmp preallocate_real_print_value_external_from_scan_y_overlay

preallocate_require_condition_terminator_from_scan_y_overlay:
    lda condition_mode_local
    cmp #'h'
    beq preallocate_require_then_or_line_end_from_scan_y_overlay
    cmp #'f'
    beq preallocate_require_do_or_line_end_from_scan_y_overlay
    lda #ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    jmp call_context_function

preallocate_require_then_or_line_end_from_scan_y_overlay:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    jsr call_context_function
    bcs :+
    clc
    rts
:
    lda #'T'
    jsr preallocate_consume_upper_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_require_then_or_line_end_from_scan_y_overlay_miss
:
    lda #'H'
    jsr preallocate_consume_upper_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_require_then_or_line_end_from_scan_y_overlay_miss
:
    lda #'E'
    jsr preallocate_consume_upper_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_require_then_or_line_end_from_scan_y_overlay_miss
:
    lda #'N'
    jsr preallocate_consume_upper_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_require_then_or_line_end_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    jsr call_context_function
    rts
preallocate_require_then_or_line_end_from_scan_y_overlay_miss:
    sec
    rts

preallocate_require_do_or_line_end_from_scan_y_overlay:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    jsr call_context_function
    bcs :+
    clc
    rts
:
    lda #'D'
    jsr preallocate_consume_upper_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_require_do_or_line_end_from_scan_y_overlay_miss
:
    lda #'O'
    jsr preallocate_consume_upper_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_require_do_or_line_end_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    jsr call_context_function
    rts
preallocate_require_do_or_line_end_from_scan_y_overlay_miss:
    sec
    rts

preallocate_consume_upper_scan_char_from_y_overlay:
    sta compare_char_local
    jsr read_scan_char_at_y
    jsr uppercase_ascii_local
    cmp compare_char_local
    beq :+
    sec
    rts
:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jmp call_context_function

preallocate_match_scan_char_from_y_overlay:
    sta compare_char_local
    jsr read_scan_char_at_y
    cmp compare_char_local
    beq :+
    sec
    rts
:
    clc
    rts

preallocate_consume_scan_char_from_y_overlay:
    sta compare_char_local
    jsr read_scan_char_at_y
    cmp compare_char_local
    beq :+
    sec
    rts
:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jmp call_context_function

preallocate_advance_scan_char_from_y_overlay:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jmp call_context_function

uppercase_ascii_local:
    cmp #'a'
    bcc uppercase_ascii_local_done
    cmp #'z'+1
    bcs uppercase_ascii_local_done
    and #$DF
uppercase_ascii_local_done:
    rts

preallocate_real_plain_decimal_assignment_external_from_scan_y_overlay:
    sty symbol_start_y_local
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    jsr preallocate_real_plain_signed_assignment_external_from_scan_y_overlay
    bcc preallocate_real_plain_decimal_assignment_external_from_scan_y_overlay_done
    lda #ACTC_OVERLAY_CTX_RESTORE_SOURCE_MARK_FN_LO
    jsr call_context_function
    ldy symbol_start_y_local
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    jsr preallocate_real_plain_positive_assignment_external_from_scan_y_overlay
    bcc preallocate_real_plain_decimal_assignment_external_from_scan_y_overlay_done
    lda #ACTC_OVERLAY_CTX_RESTORE_SOURCE_MARK_FN_LO
    jsr call_context_function
    ldy symbol_start_y_local
    sec
    rts
preallocate_real_plain_decimal_assignment_external_from_scan_y_overlay_done:
    clc
    rts

preallocate_real_plain_positive_assignment_external_from_scan_y_overlay:
    jsr parse_positive_word_sum_local_or_fail
    bcs preallocate_real_plain_positive_assignment_external_from_scan_y_overlay_miss
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    jsr call_context_function
    bcs preallocate_real_plain_positive_assignment_external_from_scan_y_overlay_miss
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$01
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq preallocate_real_plain_positive_assignment_external_from_scan_y_overlay_done
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_I_TO_F_FN_LO
    jsr call_context_function
    bcs preallocate_real_plain_positive_assignment_external_from_scan_y_overlay_miss
preallocate_real_plain_positive_assignment_external_from_scan_y_overlay_done:
    clc
    rts
preallocate_real_plain_positive_assignment_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_plain_signed_assignment_external_from_scan_y_overlay:
    jsr preallocate_consume_signed_word_prefix_from_scan_y_overlay
    bcs preallocate_real_plain_signed_assignment_external_from_scan_y_overlay_miss
    jsr parse_positive_word_sum_local_or_fail
    bcs preallocate_real_plain_signed_assignment_external_from_scan_y_overlay_miss
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    jsr call_context_function
    bcs preallocate_real_plain_signed_assignment_external_from_scan_y_overlay_miss
    jsr preallocate_expr_value_is_zero_overlay
    bcc preallocate_real_plain_signed_assignment_external_from_scan_y_overlay_done
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_S_TO_F_FN_LO
    jsr call_context_function
    bcs preallocate_real_plain_signed_assignment_external_from_scan_y_overlay_miss
preallocate_real_plain_signed_assignment_external_from_scan_y_overlay_done:
    clc
    rts
preallocate_real_plain_signed_assignment_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_explicit_decimal_assignment_external_from_scan_y_overlay:
    sty keyword_scan_y_local
    lda #<pattern_real_decl
    ldy #>pattern_real_decl
    jsr preallocate_consume_keyword_open_from_scan_y_overlay
    bcc :+
    jmp preallocate_real_explicit_decimal_assignment_external_from_scan_y_overlay_miss
:
    jsr preallocate_real_explicit_decimal_after_open_from_scan_y_overlay
    bcc :+
    jmp preallocate_real_explicit_decimal_assignment_external_from_scan_y_overlay_miss
:
    clc
    rts
preallocate_real_explicit_decimal_assignment_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_explicit_decimal_after_open_from_scan_y_overlay:
    sty symbol_start_y_local
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    jsr preallocate_real_explicit_signed_assignment_external_from_scan_y_overlay
    bcc preallocate_real_explicit_decimal_after_open_from_scan_y_overlay_done
    lda #ACTC_OVERLAY_CTX_RESTORE_SOURCE_MARK_FN_LO
    jsr call_context_function
    ldy symbol_start_y_local
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    jsr preallocate_real_explicit_positive_assignment_external_from_scan_y_overlay
    bcc preallocate_real_explicit_decimal_after_open_from_scan_y_overlay_done
    lda #ACTC_OVERLAY_CTX_RESTORE_SOURCE_MARK_FN_LO
    jsr call_context_function
    ldy symbol_start_y_local
    sec
    rts
preallocate_real_explicit_decimal_after_open_from_scan_y_overlay_done:
    clc
    rts

preallocate_real_explicit_positive_assignment_external_from_scan_y_overlay:
    jsr parse_positive_word_sum_local_or_fail
    bcs preallocate_real_explicit_positive_assignment_external_from_scan_y_overlay_miss
    jsr preallocate_consume_close_and_line_end_from_scan_y_overlay
    bcs preallocate_real_explicit_positive_assignment_external_from_scan_y_overlay_miss
    jsr preallocate_expr_value_is_zero_overlay
    bcc preallocate_real_explicit_positive_assignment_external_from_scan_y_overlay_done
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_I_TO_F_FN_LO
    jsr call_context_function
    bcs preallocate_real_explicit_positive_assignment_external_from_scan_y_overlay_miss
preallocate_real_explicit_positive_assignment_external_from_scan_y_overlay_done:
    clc
    rts
preallocate_real_explicit_positive_assignment_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_explicit_signed_assignment_external_from_scan_y_overlay:
    jsr preallocate_consume_signed_word_prefix_from_scan_y_overlay
    bcs preallocate_real_explicit_signed_assignment_external_from_scan_y_overlay_miss
    jsr parse_positive_word_sum_local_or_fail
    bcs preallocate_real_explicit_signed_assignment_external_from_scan_y_overlay_miss
    jsr preallocate_consume_close_and_line_end_from_scan_y_overlay
    bcs preallocate_real_explicit_signed_assignment_external_from_scan_y_overlay_miss
    jsr preallocate_expr_value_is_zero_overlay
    bcc preallocate_real_explicit_signed_assignment_external_from_scan_y_overlay_done
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_S_TO_F_FN_LO
    jsr call_context_function
    bcs preallocate_real_explicit_signed_assignment_external_from_scan_y_overlay_miss
preallocate_real_explicit_signed_assignment_external_from_scan_y_overlay_done:
    clc
    rts
preallocate_real_explicit_signed_assignment_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_consume_signed_word_prefix_from_scan_y_overlay:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #'0'
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_consume_signed_word_prefix_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #'-'
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_consume_signed_word_prefix_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    clc
    rts
preallocate_consume_signed_word_prefix_from_scan_y_overlay_miss:
    sec
    rts

preallocate_consume_close_and_line_end_from_scan_y_overlay:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #')'
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_consume_close_and_line_end_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_consume_close_and_line_end_from_scan_y_overlay_miss
:
    clc
    rts
preallocate_consume_close_and_line_end_from_scan_y_overlay_miss:
    sec
    rts

preallocate_consume_close_from_scan_y_overlay:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #')'
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_consume_close_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    clc
    rts
preallocate_consume_close_from_scan_y_overlay_miss:
    sec
    rts

preallocate_expr_value_is_zero_overlay:
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    iny
    ora (ACTC_OVERLAY_WORK_ZP),y
    beq :+
    sec
    rts
:
    clc
    rts

preallocate_consume_keyword_open_from_scan_y_overlay:
    sta pattern_ptr_local
    sty pattern_ptr_local+1
    ldy keyword_scan_y_local
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_consume_keyword_open_from_scan_y_overlay_miss
:
    sty symbol_end_y_local
    lda pattern_ptr_local
    ldy pattern_ptr_local+1
    jsr symbol_buffer_matches_local_const
    bcc :+
    jmp preallocate_consume_keyword_open_from_scan_y_overlay_miss
:
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #'('
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_consume_keyword_open_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    clc
    rts
preallocate_consume_keyword_open_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_unary_operator_assignment_external_from_scan_y_overlay:
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_miss
:
    sty symbol_end_y_local
    lda #<pattern_fabs
    ldy #>pattern_fabs
    jsr symbol_buffer_matches_local_const
    bcc preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_fabs
    lda #<pattern_fsqrt
    ldy #>pattern_fsqrt
    jsr symbol_buffer_matches_local_const
    bcc preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_fsqrt
    lda #<pattern_fsign
    ldy #>pattern_fsign
    jsr symbol_buffer_matches_local_const
    bcc preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_fsign
    lda #<pattern_ftrunc
    ldy #>pattern_ftrunc
    jsr symbol_buffer_matches_local_const
    bcc preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_ftrunc
    lda #<pattern_ffloor
    ldy #>pattern_ffloor
    jsr symbol_buffer_matches_local_const
    bcc preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_ffloor
    lda #<pattern_fceil
    ldy #>pattern_fceil
    jsr symbol_buffer_matches_local_const
    bcc preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_fceil
    lda #<pattern_fround
    ldy #>pattern_fround
    jsr symbol_buffer_matches_local_const
    bcc preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_fround
    sec
    rts
preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_fabs:
    lda #'a'
    bne preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_operator
preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_fsqrt:
    lda #'q'
    bne preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_operator
preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_fsign:
    lda #'g'
    bne preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_operator
preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_ftrunc:
    lda #'c'
    bne preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_operator
preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_ffloor:
    lda #'o'
    bne preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_operator
preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_fceil:
    lda #'l'
    bne preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_operator
preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_fround:
    lda #'r'
preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_operator:
    sta real_operator_local
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #'('
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_miss
:
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcc :+
    jmp preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_miss
:
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #')'
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_REAL_OPERATOR_EXTERNAL_FN_LO
    jsr load_context_function_ptr
    lda real_operator_local
    jsr call_loaded_target_with_a
    bcc :+
    jmp preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_miss
:
    clc
    rts
preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_binary_operator_assignment_external_from_scan_y_overlay:
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_miss
:
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcc :+
    jmp preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_miss
:
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #'+'
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_operator
    lda #'-'
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_operator
    lda #'*'
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_operator
    lda #'/'
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_operator
    jmp preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_miss
preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_operator:
    sta real_operator_local
    jsr preallocate_consume_scan_char_from_y_overlay
    bcc :+
    jmp preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_miss
:
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcc :+
    jmp preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_miss
:
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_REAL_OPERATOR_EXTERNAL_FN_LO
    jsr load_context_function_ptr
    lda real_operator_local
    jsr call_loaded_target_with_a
    bcc :+
    jmp preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_miss
:
    clc
    rts
preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_real_copy_or_bridge_assignment_external_from_scan_y_overlay:
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_copy_or_bridge_assignment_external_from_scan_y_overlay_miss
:
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_copy_or_bridge_assignment_external_from_scan_y_overlay_miss
:
    stx rhs_var_index_local
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_copy_or_bridge_assignment_external_from_scan_y_overlay_miss
:
    ldx rhs_var_index_local
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcc preallocate_real_copy_or_bridge_assignment_external_from_scan_y_overlay_done
    ldx rhs_var_index_local
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_BRIDGE_WORD_VAR_FN_LO
    jsr call_indexed_context_function
    bcc :+
    jmp preallocate_real_copy_or_bridge_assignment_external_from_scan_y_overlay_miss
:
    ldx rhs_var_index_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_REAL_BRIDGE_EXTERNAL_FN_LO
    jsr call_indexed_context_function
    bcc preallocate_real_copy_or_bridge_assignment_external_from_scan_y_overlay_done
    jmp preallocate_real_copy_or_bridge_assignment_external_from_scan_y_overlay_miss
preallocate_real_copy_or_bridge_assignment_external_from_scan_y_overlay_done:
    clc
    rts
preallocate_real_copy_or_bridge_assignment_external_from_scan_y_overlay_miss:
    sec
    rts

preallocate_plain_call_args_overlay:
    lda #$00
    sta preallocate_call_arg_scan_depth_local
preallocate_plain_call_args_overlay_loop:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #$00
    jsr preallocate_match_scan_char_from_y_overlay
    bcs :+
    jmp preallocate_plain_call_args_overlay_done
:   lda #10
    jsr preallocate_match_scan_char_from_y_overlay
    bcs :+
    jmp preallocate_plain_call_args_overlay_done
:   lda #13
    jsr preallocate_match_scan_char_from_y_overlay
    bcs :+
    jmp preallocate_plain_call_args_overlay_done
:   lda #'"'
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_plain_call_args_overlay_string
    lda #'('
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_plain_call_args_overlay_lparen
    lda #')'
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_plain_call_args_overlay_rparen
    jsr preallocate_int_conversion_external_from_scan_y_overlay
    bcc preallocate_plain_call_args_overlay_loop
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc preallocate_plain_call_args_overlay_symbol
preallocate_plain_call_args_overlay_consume_one:
    jsr preallocate_advance_scan_char_from_y_overlay
    bcs preallocate_plain_call_args_overlay_fail
    jmp preallocate_plain_call_args_overlay_loop
preallocate_plain_call_args_overlay_symbol:
    sty symbol_end_y_local
    jsr preallocate_declared_symbol_is_reserved_call_keyword_overlay
    bcc preallocate_plain_call_args_overlay_symbol_not_call
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #'('
    jsr preallocate_match_scan_char_from_y_overlay
    bcs preallocate_plain_call_args_overlay_symbol_not_call
    sty saved_y_local
    lda #ACTC_OVERLAY_CTX_RESOLVE_CALL_TARGET_FN_LO
    jsr call_context_function
    ldy saved_y_local
    jmp preallocate_plain_call_args_overlay_loop
preallocate_plain_call_args_overlay_symbol_not_call:
    ldy symbol_end_y_local
    jmp preallocate_plain_call_args_overlay_loop
preallocate_plain_call_args_overlay_lparen:
    inc preallocate_call_arg_scan_depth_local
    lda #'('
    jsr preallocate_consume_scan_char_from_y_overlay
    bcs preallocate_plain_call_args_overlay_fail
    jmp preallocate_plain_call_args_overlay_loop
preallocate_plain_call_args_overlay_rparen:
    lda preallocate_call_arg_scan_depth_local
    beq preallocate_plain_call_args_overlay_consume_done
    dec preallocate_call_arg_scan_depth_local
    lda #')'
    jsr preallocate_consume_scan_char_from_y_overlay
    bcs preallocate_plain_call_args_overlay_fail
    jmp preallocate_plain_call_args_overlay_loop
preallocate_plain_call_args_overlay_consume_done:
    lda #')'
    jsr preallocate_consume_scan_char_from_y_overlay
    bcs preallocate_plain_call_args_overlay_fail
preallocate_plain_call_args_overlay_done:
    clc
    rts
preallocate_plain_call_args_overlay_string:
    jsr preallocate_skip_string_in_plain_call_arg_overlay
    bcs preallocate_plain_call_args_overlay_fail
    jmp preallocate_plain_call_args_overlay_loop
preallocate_plain_call_args_overlay_fail:
    sec
    rts

preallocate_line_call_args_overlay:
    lda #$00
    sta preallocate_call_arg_scan_depth_local
    sta preallocate_line_ops_seen_local
preallocate_line_call_args_overlay_loop:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #$00
    jsr preallocate_match_scan_char_from_y_overlay
    bcs :+
    jmp preallocate_line_call_args_overlay_done
:   lda #10
    jsr preallocate_match_scan_char_from_y_overlay
    bcs :+
    jmp preallocate_line_call_args_overlay_done
:   lda #13
    jsr preallocate_match_scan_char_from_y_overlay
    bcs :+
    jmp preallocate_line_call_args_overlay_done
:   lda #'"'
    jsr preallocate_match_scan_char_from_y_overlay
    bcs :+
    jmp preallocate_line_call_args_overlay_string
:   lda #'('
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_line_call_args_overlay_lparen
    lda #')'
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_line_call_args_overlay_rparen
    jsr preallocate_int_conversion_external_from_scan_y_overlay
    bcs preallocate_line_call_args_overlay_try_call
    lda #$01
    sta preallocate_line_ops_seen_local
    jmp preallocate_line_call_args_overlay_loop
preallocate_line_call_args_overlay_try_call:
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc preallocate_line_call_args_overlay_symbol
preallocate_line_call_args_overlay_consume_one:
    jsr preallocate_advance_scan_char_from_y_overlay
    bcs preallocate_line_call_args_overlay_fail
    jmp preallocate_line_call_args_overlay_loop
preallocate_line_call_args_overlay_symbol:
    sty symbol_end_y_local
    jsr preallocate_declared_symbol_is_reserved_call_keyword_overlay
    bcc preallocate_line_call_args_overlay_symbol_not_call
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    lda #'('
    jsr preallocate_match_scan_char_from_y_overlay
    bcs preallocate_line_call_args_overlay_symbol_not_call
    sty saved_y_local
    lda #ACTC_OVERLAY_CTX_RESOLVE_CALL_TARGET_FN_LO
    jsr call_context_function
    ldy saved_y_local
    lda #$01
    sta preallocate_line_ops_seen_local
    lda #'('
    jsr preallocate_consume_scan_char_from_y_overlay
    bcs preallocate_line_call_args_overlay_fail
    jmp preallocate_line_call_args_overlay_loop
preallocate_line_call_args_overlay_symbol_not_call:
    ldy symbol_end_y_local
    jmp preallocate_line_call_args_overlay_loop
preallocate_line_call_args_overlay_lparen:
    inc preallocate_call_arg_scan_depth_local
    lda #'('
    jsr preallocate_consume_scan_char_from_y_overlay
    bcs preallocate_line_call_args_overlay_fail
    jmp preallocate_line_call_args_overlay_loop
preallocate_line_call_args_overlay_rparen:
    lda preallocate_call_arg_scan_depth_local
    beq preallocate_line_call_args_overlay_consume_rparen
    dec preallocate_call_arg_scan_depth_local
preallocate_line_call_args_overlay_consume_rparen:
    lda #')'
    jsr preallocate_consume_scan_char_from_y_overlay
    bcs preallocate_line_call_args_overlay_fail
    jmp preallocate_line_call_args_overlay_loop
preallocate_line_call_args_overlay_string:
    jsr preallocate_skip_string_in_plain_call_arg_overlay
    bcs preallocate_line_call_args_overlay_fail
    jmp preallocate_line_call_args_overlay_loop
preallocate_line_call_args_overlay_done:
    lda preallocate_line_ops_seen_local
    beq preallocate_line_call_args_overlay_fail
    clc
    rts
preallocate_line_call_args_overlay_fail:
    sec
    rts

preallocate_skip_string_in_plain_call_arg_overlay:
    lda #'"'
    jsr preallocate_consume_scan_char_from_y_overlay
    bcs preallocate_skip_string_in_plain_call_arg_overlay_fail
preallocate_skip_string_in_plain_call_arg_overlay_loop:
    lda #$00
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_skip_string_in_plain_call_arg_overlay_done
    lda #10
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_skip_string_in_plain_call_arg_overlay_done
    lda #13
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_skip_string_in_plain_call_arg_overlay_done
    lda #'"'
    jsr preallocate_match_scan_char_from_y_overlay
    bcc preallocate_skip_string_in_plain_call_arg_overlay_close
    jsr preallocate_advance_scan_char_from_y_overlay
    bcs preallocate_skip_string_in_plain_call_arg_overlay_fail
    jmp preallocate_skip_string_in_plain_call_arg_overlay_loop
preallocate_skip_string_in_plain_call_arg_overlay_close:
    lda #'"'
    jsr preallocate_consume_scan_char_from_y_overlay
    bcs preallocate_skip_string_in_plain_call_arg_overlay_fail
preallocate_skip_string_in_plain_call_arg_overlay_done:
    clc
    rts
preallocate_skip_string_in_plain_call_arg_overlay_fail:
    sec
    rts

preallocate_declared_symbol_is_reserved_call_keyword_overlay:
    lda #<pattern_and
    ldy #>pattern_and
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_reserved_call_keyword_overlay_yes
    lda #<pattern_or
    ldy #>pattern_or
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_reserved_call_keyword_overlay_yes
    lda #<pattern_not
    ldy #>pattern_not
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_reserved_call_keyword_overlay_yes
    lda #<pattern_int_decl
    ldy #>pattern_int_decl
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_reserved_call_keyword_overlay_yes
    lda #<pattern_real_decl
    ldy #>pattern_real_decl
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_reserved_call_keyword_overlay_yes
    lda #<pattern_realbits
    ldy #>pattern_realbits
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_reserved_call_keyword_overlay_yes
    lda #<pattern_fabs
    ldy #>pattern_fabs
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_reserved_call_keyword_overlay_yes
    lda #<pattern_fsqrt
    ldy #>pattern_fsqrt
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_reserved_call_keyword_overlay_yes
    lda #<pattern_fsign
    ldy #>pattern_fsign
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_reserved_call_keyword_overlay_yes
    lda #<pattern_ftrunc
    ldy #>pattern_ftrunc
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_reserved_call_keyword_overlay_yes
    lda #<pattern_ffloor
    ldy #>pattern_ffloor
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_reserved_call_keyword_overlay_yes
    lda #<pattern_fceil
    ldy #>pattern_fceil
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_reserved_call_keyword_overlay_yes
    lda #<pattern_fround
    ldy #>pattern_fround
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_reserved_call_keyword_overlay_yes
    sec
    rts
preallocate_declared_symbol_is_reserved_call_keyword_overlay_yes:
    clc
    rts

preallocate_declared_symbol_is_print_statement_overlay:
    lda #<preallocate_symbol_print
    ldy #>preallocate_symbol_print
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_print_statement_overlay_yes
    lda #<preallocate_symbol_printe
    ldy #>preallocate_symbol_printe
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_print_statement_overlay_yes
    lda #<preallocate_symbol_printi
    ldy #>preallocate_symbol_printi
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_print_statement_overlay_yes
    lda #<preallocate_symbol_printie
    ldy #>preallocate_symbol_printie
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_print_statement_overlay_yes
    lda #<preallocate_symbol_printr
    ldy #>preallocate_symbol_printr
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_print_statement_overlay_yes
    lda #<preallocate_symbol_printre
    ldy #>preallocate_symbol_printre
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_print_statement_overlay_yes
    sec
    rts
preallocate_declared_symbol_is_print_statement_overlay_yes:
    clc
    rts

preallocate_declared_symbol_is_condition_statement_overlay:
    lda #<pattern_if
    ldy #>pattern_if
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_condition_statement_overlay_yes
    lda #<pattern_while
    ldy #>pattern_while
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_condition_statement_overlay_yes
    lda #<pattern_until
    ldy #>pattern_until
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_condition_statement_overlay_yes
    sec
    rts
preallocate_declared_symbol_is_condition_statement_overlay_yes:
    clc
    rts

load_current_char:
    ldy #$00
read_scan_char_at_y:
    sty saved_y_local
    lda call_arg_a
    sta saved_call_arg_local
    lda call_target_ptr
    sta saved_call_target_ptr_local
    lda call_target_ptr+1
    sta saved_call_target_ptr_local+1
    ldy #ACTC_OVERLAY_CTX_PEEK_SCAN_Y_FN_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target_ptr
    iny
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target_ptr+1
    ldy saved_y_local
    lda #$00
    jsr call_loaded_target_with_a
    php
    sta read_char_local
    lda saved_call_arg_local
    sta call_arg_a
    lda saved_call_target_ptr_local
    sta call_target_ptr
    lda saved_call_target_ptr_local+1
    sta call_target_ptr+1
    lda read_char_local
    ldy saved_y_local
    plp
    rts
pattern_matches_local_scan_ptr:
    jsr set_resident_const_ptr_from_ay
    lda #ACTC_OVERLAY_CTX_PATTERN_MATCHES_SCAN_PTR_FN_LO
    jmp call_context_function

pattern_matches_local_scan_ptr_keyword:
    jsr set_resident_const_ptr_from_ay
    lda #ACTC_OVERLAY_CTX_PATTERN_MATCHES_SCAN_PTR_KEYWORD_FN_LO
    jmp call_context_function

source_reader_consume_local_pattern:
    jsr set_resident_const_ptr_from_ay
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_BY_CONST_FN_LO
    jmp call_context_function

symbol_buffer_matches_local_const:
    jsr set_resident_const_ptr_from_ay
    lda #ACTC_OVERLAY_CTX_SYMBOL_BUFFER_MATCHES_CONST_PTR_FN_LO
    jmp call_context_function
set_resident_const_ptr_from_ay:
    sta pattern_ptr_local
    sty pattern_ptr_local+1
    lda #ACTC_OVERLAY_CTX_CONST_PTR_SLOT_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda pattern_ptr_local
    sta (ACTC_OVERLAY_WORK_ZP),y
    iny
    lda pattern_ptr_local+1
    sta (ACTC_OVERLAY_WORK_ZP),y
    rts

load_byte_from_context_ptr:
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    rts

load_x_from_context_byte_ptr:
    jsr load_byte_from_context_ptr
    tax
    rts

store_a_to_context_byte_ptr:
    sta stored_byte_local
    txa
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda stored_byte_local
    sta (ACTC_OVERLAY_WORK_ZP),y
    rts

fail_with_diag:
    sta saved_a_local
    sty saved_y_local
    ldy #ACTC_OVERLAY_CTX_DIAG_PTR_LO
    lda saved_a_local
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    ldy #ACTC_OVERLAY_CTX_DIAG_PTR_HI
    lda saved_y_local
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    sec
    rts

load_context_ptr_to_work_zp:
    sta saved_a_local
    sty saved_y_local
    tay
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    iny
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP+1
    lda saved_a_local
    ldy saved_y_local
    rts

call_context_function:
    jsr load_context_function_ptr
    lda #$00
    jmp call_loaded_target_with_a

call_indexed_context_function:
    stx saved_x_local
    jsr load_context_function_ptr
    lda #$00
    ldx saved_x_local
    jsr call_loaded_target_with_a
    ldx saved_x_local
    rts

load_context_function_ptr:
    sta saved_a_local
    sty saved_y_local
    tay
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target_ptr
    iny
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target_ptr+1
    lda saved_a_local
    ldy saved_y_local
    rts

call_loaded_target_with_a:
    sta call_arg_a
    sec
    lda call_target_ptr
    sbc #$01
    sta call_target_minus_one
    lda call_target_ptr+1
    sbc #$00
    pha
    lda call_target_minus_one
    pha
    lda call_arg_a
    rts

.include "actc_overlay_positive_word.inc"

; Shared front-coded builtin lookup data.
.include "actc_overlay_builtin_runtime_table.inc"

pattern_int_decl:
    .asciiz "INT"
pattern_real_decl:
    .asciiz "REAL"
pattern_realbits:
    .asciiz "REALBITS"
pattern_fabs:
    .asciiz "FABS"
pattern_fsqrt:
    .asciiz "FSQRT"
pattern_fsign:
    .asciiz "FSIGN"
pattern_ftrunc:
    .asciiz "FTRUNC"
pattern_ffloor:
    .asciiz "FFLOOR"
pattern_fceil:
    .asciiz "FCEIL"
pattern_fround:
    .asciiz "FROUND"
pattern_fmin:
    .asciiz "FMIN"
pattern_fmax:
    .asciiz "FMAX"
pattern_fclamp:
    .asciiz "FCLAMP"
pattern_and:
    .asciiz "AND"
pattern_or:
    .asciiz "OR"
pattern_not:
    .asciiz "NOT"
pattern_proc:
    .asciiz "PROC"
pattern_func:
    .asciiz "FUNC"
pattern_asmblock:
    .asciiz "ASMBLOCK"
pattern_if:
    .asciiz "IF"
pattern_while:
    .asciiz "WHILE"
pattern_do:
    .asciiz "DO"
pattern_od:
    .asciiz "OD"
pattern_until:
    .asciiz "UNTIL"
pattern_else:
    .asciiz "ELSE"
pattern_fi:
    .asciiz "FI"
pattern_endif:
    .asciiz "ENDIF"
pattern_return:
    .asciiz "RETURN"
preallocate_symbol_print:
    .asciiz "PRINT"
preallocate_symbol_printe:
    .asciiz "PRINTE"
preallocate_symbol_printr:
    .asciiz "PRINTR"
preallocate_symbol_printre:
    .asciiz "PRINTRE"
preallocate_symbol_printi:
    .asciiz "PRINTI"
preallocate_symbol_printie:
    .asciiz "PRINTIE"
pattern_print_quote:
    .byte "PRINT(",34,0
pattern_printe_quote:
    .byte "PRINTE(",34,0
pattern_printr:
    .asciiz "PRINTR("
pattern_printre:
    .asciiz "PRINTRE("
pattern_printi:
    .asciiz "PRINTI("
pattern_printie:
    .asciiz "PRINTIE("
msg_load_fail:
    .asciiz "LOAD FAIL"
msg_save_fail:
    .asciiz "SAVE FAIL"
msg_bad_proc:
    .asciiz "BAD PROC"
msg_bad_asmblock:
    .asciiz "BAD ASM"
msg_bad_var:
    .asciiz "BAD VAR"
msg_bad_literal:
    .asciiz "BAD LITERAL"
call_target_minus_one:
    .byte $00
call_target_ptr:
    .word $0000
call_arg_a:
    .byte $00
pattern_ptr_local:
    .word $0000
symbol_start_y_local:
    .byte $00
symbol_end_y_local:
    .byte $00
saved_a_local:
    .byte $00
saved_x_local:
    .byte $00
saved_y_local:
    .byte $00
stored_byte_local:
    .byte $00
read_char_local:
    .byte $00
saved_call_arg_local:
    .byte $00
saved_call_target_ptr_local:
    .word $0000
preallocate_call_arg_scan_depth_local:
    .byte $00
preallocate_line_ops_seen_local:
    .byte $00
assignment_target_end_y_local:
    .byte $00
assignment_value_start_y_local:
    .byte $00
real_operator_local:
    .byte $00
real_function_arity_local:
    .byte $00
rhs_var_index_local:
    .byte $00
keyword_scan_y_local:
    .byte $00
condition_mode_local:
    .byte $00
compare_char_local:
    .byte $00

actc_overlay_end:
