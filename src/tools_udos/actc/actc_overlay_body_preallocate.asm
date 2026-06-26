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
    lda #<pattern_proc
    ldy #>pattern_proc
    jsr pattern_matches_local_scan_ptr
    bcs preallocate_body_externals_overlay_not_proc
    jmp preallocate_body_externals_overlay_proc_decl

preallocate_body_externals_overlay_not_proc:
    lda #ACTC_OVERLAY_CTX_CURRENT_PROC_INDEX_PTR_LO
    jsr load_byte_from_context_ptr
    cmp #$FF
    bne :+
    jmp preallocate_body_externals_overlay_skip_line
:
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
    jsr read_scan_char_at_y
    sty saved_y_local
    cmp #'('
    beq preallocate_body_externals_overlay_call
    cmp #'='
    beq preallocate_body_externals_overlay_assignment
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
    jsr read_scan_char_at_y
    cmp #'='
    bne preallocate_body_externals_overlay_skip_line
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    jsr read_scan_char_at_y
    cmp #'('
    bne preallocate_body_externals_overlay_skip_line
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    jsr advance_scan_ptr_by_local_pattern
    lda #ACTC_OVERLAY_CTX_SKIP_SOURCE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_PTR_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_body_externals_overlay_bad_proc
:   lda #ACTC_OVERLAY_CTX_FIND_EXPORT_INDEX_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_body_externals_overlay_bad_proc
:   txa
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
    jsr read_scan_char_at_y
    cmp #'='
    bne preallocate_real_unary_assignment_external_from_declared_overlay_miss
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
    bcs preallocate_real_unary_assignment_external_from_declared_overlay_miss
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    sty assignment_value_start_y_local
    jsr preallocate_real_plain_decimal_assignment_external_from_scan_y_overlay
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
    jsr read_scan_char_at_y
    cmp #'='
    beq :+
    jmp preallocate_word_int_assignment_external_from_declared_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    jsr read_scan_char_at_y
    cmp #')'
    beq :+
    jmp preallocate_int_conversion_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    jsr read_scan_char_at_y
    cmp #')'
    beq :+
    jmp preallocate_real_explicit_bridge_assignment_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    jsr read_scan_char_at_y
    cmp #'('
    beq :+
    jmp preallocate_real_print_statement_external_from_declared_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    jsr read_scan_char_at_y
    cmp #')'
    beq :+
    jmp preallocate_real_print_statement_external_from_declared_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    lda #ACTC_OVERLAY_CTX_PARSE_POSITIVE_WORD_SUM_FN_LO
    jsr call_context_function
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
    lda #ACTC_OVERLAY_CTX_PARSE_POSITIVE_WORD_SUM_FN_LO
    jsr call_context_function
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
    sec
    rts
preallocate_real_unary_print_external_from_scan_y_overlay_fabs:
    lda #'a'
    bne preallocate_real_unary_print_external_from_scan_y_overlay_operator
preallocate_real_unary_print_external_from_scan_y_overlay_fsqrt:
    lda #'q'
preallocate_real_unary_print_external_from_scan_y_overlay_operator:
    sta real_operator_local
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    jsr read_scan_char_at_y
    cmp #'('
    beq :+
    jmp preallocate_real_unary_print_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    jsr read_scan_char_at_y
    cmp #'+'
    beq preallocate_real_binary_print_external_from_scan_y_overlay_operator
    cmp #'-'
    beq preallocate_real_binary_print_external_from_scan_y_overlay_operator
    cmp #'*'
    beq preallocate_real_binary_print_external_from_scan_y_overlay_operator
    cmp #'/'
    bne preallocate_real_binary_print_external_from_scan_y_overlay_miss
preallocate_real_binary_print_external_from_scan_y_overlay_operator:
    sta real_operator_local
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    jsr read_scan_char_at_y
    cmp #'='
    beq preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_one
    cmp #'<'
    beq preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_lt
    cmp #'>'
    beq preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_gt
    jmp preallocate_real_condition_cmp_external_from_scan_y_overlay_miss
preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_one:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
    bcc preallocate_real_condition_cmp_external_from_scan_y_overlay_rhs
    jmp preallocate_real_condition_cmp_external_from_scan_y_overlay_miss
preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_lt:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_condition_cmp_external_from_scan_y_overlay_miss
:
    jsr read_scan_char_at_y
    cmp #'>'
    beq preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_second
    cmp #'='
    beq preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_second
    jmp preallocate_real_condition_cmp_external_from_scan_y_overlay_rhs
preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_gt:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_real_condition_cmp_external_from_scan_y_overlay_miss
:
    jsr read_scan_char_at_y
    cmp #'='
    bne preallocate_real_condition_cmp_external_from_scan_y_overlay_rhs
preallocate_real_condition_cmp_external_from_scan_y_overlay_consume_second:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    lda #ACTC_OVERLAY_CTX_PARSE_POSITIVE_WORD_SUM_FN_LO
    jsr call_context_function
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
    lda #ACTC_OVERLAY_CTX_PARSE_POSITIVE_WORD_SUM_FN_LO
    jsr call_context_function
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
    lda #ACTC_OVERLAY_CTX_PARSE_POSITIVE_WORD_SUM_FN_LO
    jsr call_context_function
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
    lda #ACTC_OVERLAY_CTX_PARSE_POSITIVE_WORD_SUM_FN_LO
    jsr call_context_function
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
    jsr read_scan_char_at_y
    cmp #'0'
    beq :+
    jmp preallocate_consume_signed_word_prefix_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
    bcc :+
    jmp preallocate_consume_signed_word_prefix_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    jsr read_scan_char_at_y
    cmp #'-'
    beq :+
    jmp preallocate_consume_signed_word_prefix_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    jsr read_scan_char_at_y
    cmp #')'
    beq :+
    jmp preallocate_consume_close_and_line_end_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    jsr read_scan_char_at_y
    cmp #')'
    beq :+
    jmp preallocate_consume_close_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    jsr read_scan_char_at_y
    cmp #'('
    beq :+
    jmp preallocate_consume_keyword_open_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    sec
    rts
preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_fabs:
    lda #'a'
    bne preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_operator
preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_fsqrt:
    lda #'q'
preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_operator:
    sta real_operator_local
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    jsr read_scan_char_at_y
    cmp #'('
    beq :+
    jmp preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    jsr read_scan_char_at_y
    cmp #')'
    beq :+
    jmp preallocate_real_unary_operator_assignment_external_from_scan_y_overlay_miss
:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    jsr read_scan_char_at_y
    cmp #'+'
    beq preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_operator
    cmp #'-'
    beq preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_operator
    cmp #'*'
    beq preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_operator
    cmp #'/'
    bne preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_miss
preallocate_real_binary_operator_assignment_external_from_scan_y_overlay_operator:
    sta real_operator_local
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    jsr read_scan_char_at_y
    bne :+
    jmp preallocate_plain_call_args_overlay_done
:   cmp #10
    bne :+
    jmp preallocate_plain_call_args_overlay_done
:   cmp #13
    bne :+
    jmp preallocate_plain_call_args_overlay_done
:   cmp #'"'
    beq preallocate_plain_call_args_overlay_string
    cmp #'('
    beq preallocate_plain_call_args_overlay_lparen
    cmp #')'
    beq preallocate_plain_call_args_overlay_rparen
    jsr preallocate_int_conversion_external_from_scan_y_overlay
    bcc preallocate_plain_call_args_overlay_loop
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jsr call_context_function
    bcc preallocate_plain_call_args_overlay_symbol
preallocate_plain_call_args_overlay_consume_one:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
    bcs preallocate_plain_call_args_overlay_fail
    jmp preallocate_plain_call_args_overlay_loop
preallocate_plain_call_args_overlay_symbol:
    sty symbol_end_y_local
    jsr preallocate_declared_symbol_is_reserved_call_keyword_overlay
    bcc preallocate_plain_call_args_overlay_symbol_not_call
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    jsr read_scan_char_at_y
    cmp #'('
    bne preallocate_plain_call_args_overlay_symbol_not_call
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
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
    bcs preallocate_plain_call_args_overlay_fail
    jmp preallocate_plain_call_args_overlay_loop
preallocate_plain_call_args_overlay_rparen:
    lda preallocate_call_arg_scan_depth_local
    beq preallocate_plain_call_args_overlay_consume_done
    dec preallocate_call_arg_scan_depth_local
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
    bcs preallocate_plain_call_args_overlay_fail
    jmp preallocate_plain_call_args_overlay_loop
preallocate_plain_call_args_overlay_consume_done:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    jsr read_scan_char_at_y
    bne :+
    jmp preallocate_line_call_args_overlay_done
:   cmp #10
    bne :+
    jmp preallocate_line_call_args_overlay_done
:   cmp #13
    bne :+
    jmp preallocate_line_call_args_overlay_done
:   cmp #'"'
    beq preallocate_line_call_args_overlay_string
    cmp #'('
    beq preallocate_line_call_args_overlay_lparen
    cmp #')'
    beq preallocate_line_call_args_overlay_rparen
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
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
    bcs preallocate_line_call_args_overlay_fail
    jmp preallocate_line_call_args_overlay_loop
preallocate_line_call_args_overlay_symbol:
    sty symbol_end_y_local
    jsr preallocate_declared_symbol_is_reserved_call_keyword_overlay
    bcc preallocate_line_call_args_overlay_symbol_not_call
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jsr call_context_function
    jsr read_scan_char_at_y
    cmp #'('
    bne preallocate_line_call_args_overlay_symbol_not_call
    sty saved_y_local
    lda #ACTC_OVERLAY_CTX_RESOLVE_CALL_TARGET_FN_LO
    jsr call_context_function
    ldy saved_y_local
    lda #$01
    sta preallocate_line_ops_seen_local
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
    bcs preallocate_line_call_args_overlay_fail
    jmp preallocate_line_call_args_overlay_loop
preallocate_line_call_args_overlay_symbol_not_call:
    ldy symbol_end_y_local
    jmp preallocate_line_call_args_overlay_loop
preallocate_line_call_args_overlay_lparen:
    inc preallocate_call_arg_scan_depth_local
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
    bcs preallocate_line_call_args_overlay_fail
    jmp preallocate_line_call_args_overlay_loop
preallocate_line_call_args_overlay_rparen:
    lda preallocate_call_arg_scan_depth_local
    beq preallocate_line_call_args_overlay_consume_rparen
    dec preallocate_call_arg_scan_depth_local
preallocate_line_call_args_overlay_consume_rparen:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
    bcs preallocate_skip_string_in_plain_call_arg_overlay_fail
preallocate_skip_string_in_plain_call_arg_overlay_loop:
    jsr read_scan_char_at_y
    beq preallocate_skip_string_in_plain_call_arg_overlay_done
    cmp #10
    beq preallocate_skip_string_in_plain_call_arg_overlay_done
    cmp #13
    beq preallocate_skip_string_in_plain_call_arg_overlay_done
    cmp #'"'
    beq preallocate_skip_string_in_plain_call_arg_overlay_close
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
    bcs preallocate_skip_string_in_plain_call_arg_overlay_fail
    jmp preallocate_skip_string_in_plain_call_arg_overlay_loop
preallocate_skip_string_in_plain_call_arg_overlay_close:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jsr call_context_function
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
    lda #<pattern_fabs
    ldy #>pattern_fabs
    jsr symbol_buffer_matches_local_const
    bcc preallocate_declared_symbol_is_reserved_call_keyword_overlay_yes
    lda #<pattern_fsqrt
    ldy #>pattern_fsqrt
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

advance_scan_ptr_by_local_pattern:
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

; Builtin runtime helper lookup lives in the active body overlay.
; Each row packs the argument count into bits 6..7 of the builtin pointer high byte.
builtin_runtime_import_table:
    .byte (($02 << 6) | (>builtin_symbol_sid_freq & $3F)), <builtin_symbol_sid_freq, <runtime_symbol_rt_sid_freq, >runtime_symbol_rt_sid_freq
    .byte (($02 << 6) | (>builtin_symbol_sid_pulse & $3F)), <builtin_symbol_sid_pulse, <runtime_symbol_rt_sid_pulse, >runtime_symbol_rt_sid_pulse
    .byte (($02 << 6) | (>builtin_symbol_sid_wave & $3F)), <builtin_symbol_sid_wave, <runtime_symbol_rt_sid_wave, >runtime_symbol_rt_sid_wave
    .byte (($02 << 6) | (>builtin_symbol_sid_ad & $3F)), <builtin_symbol_sid_ad, <runtime_symbol_rt_sid_ad, >runtime_symbol_rt_sid_ad
    .byte (($02 << 6) | (>builtin_symbol_sid_sr & $3F)), <builtin_symbol_sid_sr, <runtime_symbol_rt_sid_sr, >runtime_symbol_rt_sid_sr
    .byte (($01 << 6) | (>builtin_symbol_sid_on & $3F)), <builtin_symbol_sid_on, <runtime_symbol_rt_sid_on, >runtime_symbol_rt_sid_on
    .byte (($01 << 6) | (>builtin_symbol_sid_off & $3F)), <builtin_symbol_sid_off, <runtime_symbol_rt_sid_off, >runtime_symbol_rt_sid_off
    .byte (($00 << 6) | (>builtin_symbol_sid_rst & $3F)), <builtin_symbol_sid_rst, <runtime_symbol_rt_sid_rst, >runtime_symbol_rt_sid_rst
    .byte (($01 << 6) | (>builtin_symbol_sid_route & $3F)), <builtin_symbol_sid_route, <runtime_symbol_rt_sid_route, >runtime_symbol_rt_sid_route
    .byte (($01 << 6) | (>builtin_symbol_sid_res & $3F)), <builtin_symbol_sid_res, <runtime_symbol_rt_sid_res, >runtime_symbol_rt_sid_res
    .byte (($01 << 6) | (>builtin_symbol_sid_cutoff & $3F)), <builtin_symbol_sid_cutoff, <runtime_symbol_rt_sid_cutoff, >runtime_symbol_rt_sid_cutoff
    .byte (($01 << 6) | (>builtin_symbol_sid_mode & $3F)), <builtin_symbol_sid_mode, <runtime_symbol_rt_sid_mode, >runtime_symbol_rt_sid_mode
    .byte (($01 << 6) | (>builtin_symbol_sid_vol & $3F)), <builtin_symbol_sid_vol, <runtime_symbol_rt_sid_vol, >runtime_symbol_rt_sid_vol
    .byte (($00 << 6) | (>builtin_symbol_sid_osc3 & $3F)), <builtin_symbol_sid_osc3, <runtime_symbol_rt_sid_osc3, >runtime_symbol_rt_sid_osc3
    .byte (($00 << 6) | (>builtin_symbol_sid_env3 & $3F)), <builtin_symbol_sid_env3, <runtime_symbol_rt_sid_env3, >runtime_symbol_rt_sid_env3
    .byte (($01 << 6) | (>builtin_symbol_vic_bank & $3F)), <builtin_symbol_vic_bank, <runtime_symbol_rt_gfx_vic_bank, >runtime_symbol_rt_gfx_vic_bank
    .byte (($01 << 6) | (>builtin_symbol_bg_color & $3F)), <builtin_symbol_bg_color, <runtime_symbol_rt_gfx_bgcolor, >runtime_symbol_rt_gfx_bgcolor
    .byte (($01 << 6) | (>builtin_symbol_border_color & $3F)), <builtin_symbol_border_color, <runtime_symbol_rt_gfx_bordercolor, >runtime_symbol_rt_gfx_bordercolor
    .byte (($01 << 6) | (>builtin_symbol_screen_base & $3F)), <builtin_symbol_screen_base, <runtime_symbol_rt_gfx_screen_base, >runtime_symbol_rt_gfx_screen_base
    .byte (($01 << 6) | (>builtin_symbol_bitmap_base & $3F)), <builtin_symbol_bitmap_base, <runtime_symbol_rt_gfx_bitmap_base, >runtime_symbol_rt_gfx_bitmap_base
    .byte (($03 << 6) | (>builtin_symbol_screen_cell & $3F)), <builtin_symbol_screen_cell, <runtime_symbol_rt_gfx_screen_cell, >runtime_symbol_rt_gfx_screen_cell
    .byte (($03 << 6) | (>builtin_symbol_color_cell & $3F)), <builtin_symbol_color_cell, <runtime_symbol_rt_gfx_color_cell, >runtime_symbol_rt_gfx_color_cell
    .byte (($01 << 6) | (>builtin_symbol_screen_copy & $3F)), <builtin_symbol_screen_copy, <runtime_symbol_rt_gfx_screen_copy, >runtime_symbol_rt_gfx_screen_copy
    .byte (($01 << 6) | (>builtin_symbol_color_copy & $3F)), <builtin_symbol_color_copy, <runtime_symbol_rt_gfx_color_copy, >runtime_symbol_rt_gfx_color_copy
    .byte (($01 << 6) | (>builtin_symbol_bitmap_fill & $3F)), <builtin_symbol_bitmap_fill, <runtime_symbol_rt_gfx_bitmap_fill, >runtime_symbol_rt_gfx_bitmap_fill
    .byte (($01 << 6) | (>builtin_symbol_bitmap_copy & $3F)), <builtin_symbol_bitmap_copy, <runtime_symbol_rt_gfx_bitmap_copy, >runtime_symbol_rt_gfx_bitmap_copy
    .byte (($00 << 6) | (>builtin_symbol_bitmap_on & $3F)), <builtin_symbol_bitmap_on, <runtime_symbol_rt_gfx_bitmap_on, >runtime_symbol_rt_gfx_bitmap_on
    .byte (($00 << 6) | (>builtin_symbol_bitmap_off & $3F)), <builtin_symbol_bitmap_off, <runtime_symbol_rt_gfx_bitmap_off, >runtime_symbol_rt_gfx_bitmap_off
    .byte (($00 << 6) | (>builtin_symbol_mbitmap_on & $3F)), <builtin_symbol_mbitmap_on, <runtime_symbol_rt_gfx_mbitmap_on, >runtime_symbol_rt_gfx_mbitmap_on
    .byte (($00 << 6) | (>builtin_symbol_mbitmap_off & $3F)), <builtin_symbol_mbitmap_off, <runtime_symbol_rt_gfx_mbitmap_off, >runtime_symbol_rt_gfx_mbitmap_off
    .byte (($01 << 6) | (>builtin_symbol_sprite_on & $3F)), <builtin_symbol_sprite_on, <runtime_symbol_rt_sprite_on, >runtime_symbol_rt_sprite_on
    .byte (($01 << 6) | (>builtin_symbol_sprite_off & $3F)), <builtin_symbol_sprite_off, <runtime_symbol_rt_sprite_off, >runtime_symbol_rt_sprite_off
    .byte (($00 << 6) | (>builtin_symbol_sprite_hit & $3F)), <builtin_symbol_sprite_hit, <runtime_symbol_rt_sprite_hit, >runtime_symbol_rt_sprite_hit
    .byte (($00 << 6) | (>builtin_symbol_sprite_hit_bg & $3F)), <builtin_symbol_sprite_hit_bg, <runtime_symbol_rt_sprite_hit_bg, >runtime_symbol_rt_sprite_hit_bg
    .byte (($02 << 6) | (>builtin_symbol_sprite_color & $3F)), <builtin_symbol_sprite_color, <runtime_symbol_rt_sprite_color, >runtime_symbol_rt_sprite_color
    .byte (($03 << 6) | (>builtin_symbol_sprite_pos & $3F)), <builtin_symbol_sprite_pos, <runtime_symbol_rt_sprite_pos, >runtime_symbol_rt_sprite_pos
    .byte (($02 << 6) | (>builtin_symbol_sprite_mc & $3F)), <builtin_symbol_sprite_mc, <runtime_symbol_rt_sprite_mc, >runtime_symbol_rt_sprite_mc
    .byte (($02 << 6) | (>builtin_symbol_sprite_xexp & $3F)), <builtin_symbol_sprite_xexp, <runtime_symbol_rt_sprite_xexp, >runtime_symbol_rt_sprite_xexp
    .byte (($02 << 6) | (>builtin_symbol_sprite_yexp & $3F)), <builtin_symbol_sprite_yexp, <runtime_symbol_rt_sprite_yexp, >runtime_symbol_rt_sprite_yexp
    .byte (($02 << 6) | (>builtin_symbol_sprite_prio & $3F)), <builtin_symbol_sprite_prio, <runtime_symbol_rt_sprite_prio, >runtime_symbol_rt_sprite_prio
    .byte (($02 << 6) | (>builtin_symbol_sprite_ptr & $3F)), <builtin_symbol_sprite_ptr, <runtime_symbol_rt_sprite_ptr, >runtime_symbol_rt_sprite_ptr
    .byte (($02 << 6) | (>builtin_symbol_sprite_data & $3F)), <builtin_symbol_sprite_data, <runtime_symbol_rt_sprite_data, >runtime_symbol_rt_sprite_data
    .byte (($02 << 6) | (>builtin_symbol_set_sprite_mc & $3F)), <builtin_symbol_set_sprite_mc, <runtime_symbol_rt_sprite_set_mc, >runtime_symbol_rt_sprite_set_mc
    .byte (($01 << 6) | (>builtin_symbol_joy & $3F)), <builtin_symbol_joy, <runtime_symbol_rt_joy, >runtime_symbol_rt_joy
    .byte (($01 << 6) | (>builtin_symbol_joy_seen & $3F)), <builtin_symbol_joy_seen, <runtime_symbol_rt_jp, >runtime_symbol_rt_jp
    .byte (($01 << 6) | (>builtin_symbol_joy_btn1 & $3F)), <builtin_symbol_joy_btn1, <runtime_symbol_rt_jb1, >runtime_symbol_rt_jb1
    .byte (($01 << 6) | (>builtin_symbol_joy_btn2 & $3F)), <builtin_symbol_joy_btn2, <runtime_symbol_rt_jb2, >runtime_symbol_rt_jb2
    .byte (($01 << 6) | (>builtin_symbol_mouse_poll & $3F)), <builtin_symbol_mouse_poll, <runtime_symbol_rt_mp, >runtime_symbol_rt_mp
    .byte (($00 << 6) | (>builtin_symbol_mouse_seen & $3F)), <builtin_symbol_mouse_seen, <runtime_symbol_rt_mseen, >runtime_symbol_rt_mseen
    .byte (($00 << 6) | (>builtin_symbol_mouse_x & $3F)), <builtin_symbol_mouse_x, <runtime_symbol_rt_mx, >runtime_symbol_rt_mx
    .byte (($00 << 6) | (>builtin_symbol_mouse_y & $3F)), <builtin_symbol_mouse_y, <runtime_symbol_rt_my, >runtime_symbol_rt_my
    .byte (($00 << 6) | (>builtin_symbol_mouse_btn & $3F)), <builtin_symbol_mouse_btn, <runtime_symbol_rt_mb, >runtime_symbol_rt_mb
    .byte (($00 << 6) | (>builtin_symbol_mouse_btn1 & $3F)), <builtin_symbol_mouse_btn1, <runtime_symbol_rt_mb1, >runtime_symbol_rt_mb1
    .byte (($00 << 6) | (>builtin_symbol_mouse_btn2 & $3F)), <builtin_symbol_mouse_btn2, <runtime_symbol_rt_mb2, >runtime_symbol_rt_mb2
    .byte (($01 << 6) | (>builtin_symbol_dbf_create & $3F)), <builtin_symbol_dbf_create, <runtime_symbol_rt_dbf_create, >runtime_symbol_rt_dbf_create
    .byte (($01 << 6) | (>builtin_symbol_dbf_open & $3F)), <builtin_symbol_dbf_open, <runtime_symbol_rt_dbf_open, >runtime_symbol_rt_dbf_open
    .byte (($01 << 6) | (>builtin_symbol_dbf_close & $3F)), <builtin_symbol_dbf_close, <runtime_symbol_rt_dbf_close, >runtime_symbol_rt_dbf_close
    .byte (($02 << 6) | (>builtin_symbol_dbf_go & $3F)), <builtin_symbol_dbf_go, <runtime_symbol_rt_dbf_go, >runtime_symbol_rt_dbf_go
    .byte (($01 << 6) | (>builtin_symbol_dbf_field_count & $3F)), <builtin_symbol_dbf_field_count, <runtime_symbol_rt_dbf_fieldcount, >runtime_symbol_rt_dbf_fieldcount
    .byte (($02 << 6) | (>builtin_symbol_dbf_field_len & $3F)), <builtin_symbol_dbf_field_len, <runtime_symbol_rt_dbf_fieldlen, >runtime_symbol_rt_dbf_fieldlen
    .byte (($02 << 6) | (>builtin_symbol_dbf_read_byte & $3F)), <builtin_symbol_dbf_read_byte, <runtime_symbol_rt_dbf_readbyte, >runtime_symbol_rt_dbf_readbyte
    .byte (($03 << 6) | (>builtin_symbol_dbf_read_field_byte & $3F)), <builtin_symbol_dbf_read_field_byte, <runtime_symbol_rt_dbf_readfieldbyte, >runtime_symbol_rt_dbf_readfieldbyte
    .byte (($03 << 6) | (>builtin_symbol_dbf_write_byte & $3F)), <builtin_symbol_dbf_write_byte, <runtime_symbol_rt_dbf_writebyte, >runtime_symbol_rt_dbf_writebyte
    .byte (($01 << 6) | (>builtin_symbol_dbf_append & $3F)), <builtin_symbol_dbf_append, <runtime_symbol_rt_dbf_append, >runtime_symbol_rt_dbf_append
    .byte (($01 << 6) | (>builtin_symbol_dbf_pack & $3F)), <builtin_symbol_dbf_pack, <runtime_symbol_rt_dbf_pack, >runtime_symbol_rt_dbf_pack
    .byte (($01 << 6) | (>builtin_symbol_dbf_save & $3F)), <builtin_symbol_dbf_save, <runtime_symbol_rt_dbf_save, >runtime_symbol_rt_dbf_save
    .byte (($01 << 6) | (>builtin_symbol_dbf_delete & $3F)), <builtin_symbol_dbf_delete, <runtime_symbol_rt_dbf_delete, >runtime_symbol_rt_dbf_delete
    .byte (($01 << 6) | (>builtin_symbol_dbf_undelete & $3F)), <builtin_symbol_dbf_undelete, <runtime_symbol_rt_dbf_undelete, >runtime_symbol_rt_dbf_undelete
    .byte (($01 << 6) | (>builtin_symbol_dbf_deleted & $3F)), <builtin_symbol_dbf_deleted, <runtime_symbol_rt_dbf_deleted, >runtime_symbol_rt_dbf_deleted
    .byte (($01 << 6) | (>builtin_symbol_dbf_header_len & $3F)), <builtin_symbol_dbf_header_len, <runtime_symbol_rt_dbf_headerlen, >runtime_symbol_rt_dbf_headerlen
    .byte (($01 << 6) | (>builtin_symbol_dbf_record_len & $3F)), <builtin_symbol_dbf_record_len, <runtime_symbol_rt_dbf_recordlen, >runtime_symbol_rt_dbf_recordlen
    .byte (($01 << 6) | (>builtin_symbol_dbf_total_recs & $3F)), <builtin_symbol_dbf_total_recs, <runtime_symbol_rt_dbf_totalrecs, >runtime_symbol_rt_dbf_totalrecs
    .byte (($01 << 6) | (>builtin_symbol_dbf_curr_rec_no & $3F)), <builtin_symbol_dbf_curr_rec_no, <runtime_symbol_rt_dbf_currrecno, >runtime_symbol_rt_dbf_currrecno
    .byte $00

runtime_symbol_rt_sid_freq:
    .asciiz "SID_FREQ"
runtime_symbol_rt_sid_pulse:
    .asciiz "SID_PULSE"
runtime_symbol_rt_sid_wave:
    .asciiz "SID_WAVE"
runtime_symbol_rt_sid_ad:
    .asciiz "SID_AD"
runtime_symbol_rt_sid_sr:
    .asciiz "SID_SR"
runtime_symbol_rt_sid_on:
    .asciiz "SID_ON"
runtime_symbol_rt_sid_off:
    .asciiz "SID_OFF"
runtime_symbol_rt_sid_rst:
    .asciiz "SID_RST"
runtime_symbol_rt_sid_route:
    .asciiz "SID_ROUTE"
runtime_symbol_rt_sid_res:
    .asciiz "SID_RES"
runtime_symbol_rt_sid_cutoff:
    .asciiz "SID_CUTOFF"
runtime_symbol_rt_sid_mode:
    .asciiz "SID_MODE"
runtime_symbol_rt_sid_vol:
    .asciiz "SID_VOL"
runtime_symbol_rt_sid_osc3:
    .asciiz "SID_OSC3"
runtime_symbol_rt_sid_env3:
    .asciiz "SID_ENV3"
runtime_symbol_rt_gfx_vic_bank:
    .asciiz "GFX_VIC_BANK"
runtime_symbol_rt_gfx_bgcolor:
    .asciiz "GFX_BGCOLOR"
runtime_symbol_rt_gfx_bordercolor:
    .asciiz "GFX_BORDERCOLOR"
runtime_symbol_rt_gfx_screen_base:
    .asciiz "GFX_SCREEN_BASE"
runtime_symbol_rt_gfx_bitmap_base:
    .asciiz "GFX_BITMAP_BASE"
runtime_symbol_rt_gfx_screen_cell:
    .asciiz "GFX_SCREEN_CELL"
runtime_symbol_rt_gfx_color_cell:
    .asciiz "GFX_COLOR_CELL"
runtime_symbol_rt_gfx_screen_copy:
    .asciiz "GFX_SCREEN_COPY"
runtime_symbol_rt_gfx_color_copy:
    .asciiz "GFX_COLOR_COPY"
runtime_symbol_rt_gfx_bitmap_fill:
    .asciiz "GFX_BITMAP_FILL"
runtime_symbol_rt_gfx_bitmap_copy:
    .asciiz "GFX_BITMAP_COPY"
runtime_symbol_rt_gfx_bitmap_on:
    .asciiz "GFX_BITMAP_ON"
runtime_symbol_rt_gfx_bitmap_off:
    .asciiz "GFX_BITMAP_OFF"
runtime_symbol_rt_gfx_mbitmap_on:
    .asciiz "GFX_MBITMAP_ON"
runtime_symbol_rt_gfx_mbitmap_off:
    .asciiz "GFX_MBITMAP_OFF"
runtime_symbol_rt_sprite_on:
    .asciiz "SPRITE_ON"
runtime_symbol_rt_sprite_off:
    .asciiz "SPRITE_OFF"
runtime_symbol_rt_sprite_hit:
    .asciiz "SPRITE_HIT"
runtime_symbol_rt_sprite_hit_bg:
    .asciiz "SPRITE_HIT_BG"
runtime_symbol_rt_sprite_color:
    .asciiz "SPRITE_COLOR"
runtime_symbol_rt_sprite_pos:
    .asciiz "SPRITE_POS"
runtime_symbol_rt_sprite_ptr:
    .asciiz "SPRITE_PTR"
runtime_symbol_rt_sprite_mc:
    .asciiz "SPRITE_MC"
runtime_symbol_rt_sprite_xexp:
    .asciiz "SPRITE_XEXP"
runtime_symbol_rt_sprite_yexp:
    .asciiz "SPRITE_YEXP"
runtime_symbol_rt_sprite_prio:
    .asciiz "SPRITE_PRIO"
runtime_symbol_rt_sprite_data:
    .asciiz "SPRITE_DATA"
runtime_symbol_rt_sprite_set_mc:
    .asciiz "SPRITE_SET_MC"
runtime_symbol_rt_joy:
    .asciiz "JOY"
runtime_symbol_rt_jp:
    .asciiz "JP"
runtime_symbol_rt_jb1:
    .asciiz "JB1"
runtime_symbol_rt_jb2:
    .asciiz "JB2"
runtime_symbol_rt_mp:
    .asciiz "MP"
runtime_symbol_rt_mseen:
    .asciiz "MSEEN"
runtime_symbol_rt_mx:
    .asciiz "MX"
runtime_symbol_rt_my:
    .asciiz "MY"
runtime_symbol_rt_mb:
    .asciiz "MB"
runtime_symbol_rt_mb1:
    .asciiz "MB1"
runtime_symbol_rt_mb2:
    .asciiz "MB2"
runtime_symbol_rt_dbf_create:
    .asciiz "DBF_CREATE"
runtime_symbol_rt_dbf_open:
    .asciiz "DBF_OPEN"
runtime_symbol_rt_dbf_close:
    .asciiz "DBF_CLOSE"
runtime_symbol_rt_dbf_go:
    .asciiz "DBF_GO"
runtime_symbol_rt_dbf_fieldcount:
    .asciiz "DBF_FIELDCOUNT"
runtime_symbol_rt_dbf_fieldlen:
    .asciiz "DBF_FIELDLEN"
runtime_symbol_rt_dbf_readbyte:
    .asciiz "DBF_READBYTE"
runtime_symbol_rt_dbf_readfieldbyte:
    .asciiz "DBF_READFIELDBYTE"
runtime_symbol_rt_dbf_writebyte:
    .asciiz "DBF_WRITEBYTE"
runtime_symbol_rt_dbf_append:
    .asciiz "DBF_APPEND"
runtime_symbol_rt_dbf_pack:
    .asciiz "DBF_PACK"
runtime_symbol_rt_dbf_save:
    .asciiz "DBF_SAVE"
runtime_symbol_rt_dbf_delete:
    .asciiz "DBF_DELETE"
runtime_symbol_rt_dbf_undelete:
    .asciiz "DBF_UNDELETE"
runtime_symbol_rt_dbf_deleted:
    .asciiz "DBF_DELETED"
runtime_symbol_rt_dbf_headerlen:
    .asciiz "DBF_HEADERLEN"
runtime_symbol_rt_dbf_recordlen:
    .asciiz "DBF_RECORDLEN"
runtime_symbol_rt_dbf_totalrecs:
    .asciiz "DBF_TOTALRECS"
runtime_symbol_rt_dbf_currrecno:
    .asciiz "DBF_CURRRECNO"
builtin_symbol_sprite_on:
    .asciiz "SPRITEON"
builtin_symbol_sprite_off:
    .asciiz "SPRITEOFF"
builtin_symbol_sprite_hit:
    .asciiz "SPRITEHIT"
builtin_symbol_sprite_hit_bg:
    .asciiz "SPRITEHITBG"
builtin_symbol_sprite_color:
    .asciiz "SPRITECOLOR"
builtin_symbol_sprite_pos:
    .asciiz "SPRITEPOS"
builtin_symbol_sprite_ptr:
    .asciiz "SPRITEPTR"
builtin_symbol_sprite_mc:
    .asciiz "SPRITEMC"
builtin_symbol_sprite_xexp:
    .asciiz "SPRITEXEXP"
builtin_symbol_sprite_yexp:
    .asciiz "SPRITEYEXP"
builtin_symbol_sprite_prio:
    .asciiz "SPRITEPRIO"
builtin_symbol_sprite_data:
    .asciiz "SPRITEDATA"
builtin_symbol_set_sprite_mc:
    .asciiz "SETSPRITEMC"
builtin_symbol_joy:
    .asciiz "JOY"
builtin_symbol_joy_seen:
    .asciiz "JOYSEEN"
builtin_symbol_joy_btn1:
    .asciiz "JOYBTN1"
builtin_symbol_joy_btn2:
    .asciiz "JOYBTN2"
builtin_symbol_mouse_poll:
    .asciiz "MOUSEPOLL"
builtin_symbol_mouse_seen:
    .asciiz "MOUSESEEN"
builtin_symbol_mouse_x:
    .asciiz "MOUSEX"
builtin_symbol_mouse_y:
    .asciiz "MOUSEY"
builtin_symbol_mouse_btn:
    .asciiz "MOUSEBTN"
builtin_symbol_mouse_btn1:
    .asciiz "MOUSEBTN1"
builtin_symbol_mouse_btn2:
    .asciiz "MOUSEBTN2"
builtin_symbol_dbf_create:
    .asciiz "DBFCREATE"
builtin_symbol_dbf_open:
    .asciiz "DBFOPEN"
builtin_symbol_dbf_close:
    .asciiz "DBFCLOSE"
builtin_symbol_dbf_go:
    .asciiz "DBFGO"
builtin_symbol_dbf_field_count:
    .asciiz "DBFFIELDCOUNT"
builtin_symbol_dbf_field_len:
    .asciiz "DBFFIELDLEN"
builtin_symbol_dbf_read_byte:
    .asciiz "DBFREADBYTE"
builtin_symbol_dbf_read_field_byte:
    .asciiz "DBFREADFIELDBYTE"
builtin_symbol_dbf_write_byte:
    .asciiz "DBFWRITEBYTE"
builtin_symbol_dbf_append:
    .asciiz "DBFAPPEND"
builtin_symbol_dbf_pack:
    .asciiz "DBFPACK"
builtin_symbol_dbf_save:
    .asciiz "DBFSAVE"
builtin_symbol_dbf_delete:
    .asciiz "DBFDELETE"
builtin_symbol_dbf_undelete:
    .asciiz "DBFUNDELETE"
builtin_symbol_dbf_deleted:
    .asciiz "DBFDELETED"
builtin_symbol_dbf_header_len:
    .asciiz "DBFHEADERLEN"
builtin_symbol_dbf_record_len:
    .asciiz "DBFRECORDLEN"
builtin_symbol_dbf_total_recs:
    .asciiz "DBFTOTALRECS"
builtin_symbol_dbf_curr_rec_no:
    .asciiz "DBFCURRRECNO"
builtin_symbol_sid_freq:
    .asciiz "SIDFREQ"
builtin_symbol_sid_pulse:
    .asciiz "SIDPULSE"
builtin_symbol_sid_wave:
    .asciiz "SIDWAVE"
builtin_symbol_sid_ad:
    .asciiz "SIDAD"
builtin_symbol_sid_sr:
    .asciiz "SIDSR"
builtin_symbol_sid_on:
    .asciiz "SIDON"
builtin_symbol_sid_off:
    .asciiz "SIDOFF"
builtin_symbol_sid_rst:
    .asciiz "SIDRST"
builtin_symbol_sid_route:
    .asciiz "SIDROUTE"
builtin_symbol_sid_res:
    .asciiz "SIDRES"
builtin_symbol_sid_cutoff:
    .asciiz "SIDCUTOFF"
builtin_symbol_sid_mode:
    .asciiz "SIDMODE"
builtin_symbol_sid_vol:
    .asciiz "SIDVOL"
builtin_symbol_sid_osc3:
    .asciiz "SIDOSC3"
builtin_symbol_sid_env3:
    .asciiz "SIDENV3"
builtin_symbol_vic_bank:
    .asciiz "VICBANK"
builtin_symbol_bg_color:
    .asciiz "BGCOLOR"
builtin_symbol_border_color:
    .asciiz "BORDERCOLOR"
builtin_symbol_screen_base:
    .asciiz "SCREENBASE"
builtin_symbol_bitmap_base:
    .asciiz "BITMAPBASE"
builtin_symbol_screen_cell:
    .asciiz "SCREENCELL"
builtin_symbol_color_cell:
    .asciiz "COLORCELL"
builtin_symbol_screen_copy:
    .asciiz "SCREENCOPY"
builtin_symbol_color_copy:
    .asciiz "COLORCOPY"
builtin_symbol_bitmap_fill:
    .asciiz "BITMAPFILL"
builtin_symbol_bitmap_copy:
    .asciiz "BITMAPCOPY"
builtin_symbol_bitmap_on:
    .asciiz "BITMAPON"
builtin_symbol_bitmap_off:
    .asciiz "BITMAPOFF"
builtin_symbol_mbitmap_on:
    .asciiz "MBITMAPON"
builtin_symbol_mbitmap_off:
    .asciiz "MBITMAPOFF"

pattern_int_decl:
    .asciiz "INT"
pattern_real_decl:
    .asciiz "REAL"
pattern_fabs:
    .asciiz "FABS"
pattern_fsqrt:
    .asciiz "FSQRT"
pattern_and:
    .asciiz "AND"
pattern_or:
    .asciiz "OR"
pattern_not:
    .asciiz "NOT"
pattern_proc:
    .asciiz "PROC"
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
rhs_var_index_local:
    .byte $00
keyword_scan_y_local:
    .byte $00
condition_mode_local:
    .byte $00
compare_char_local:
    .byte $00

actc_overlay_end:
