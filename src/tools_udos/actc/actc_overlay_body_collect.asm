.include "actc_overlay_abi.inc"

.ifndef ACTC_KEEP_BODY_RESIDENT_FALLBACK
ACTC_KEEP_BODY_RESIDENT_FALLBACK = 0
.endif

.ifndef LOOP_MAX
LOOP_MAX = 16
.endif

.export actc_overlay_header
.export actc_overlay_entry
.export actc_overlay_end

.segment "CODE"

actc_overlay_header:
    .byte 'A','C','O','V'
    .byte ACTC_OVERLAY_ABI_VERSION
    .byte ACTC_OVERLAY_PASS_BODY_COLLECT
    .word ACTC_OVERLAY_EXEC_BASE
    .word actc_overlay_entry
    .word actc_overlay_end - actc_overlay_header
    .word $0000

actc_overlay_entry:
    stx ACTC_OVERLAY_CONTEXT_ZP
    sty ACTC_OVERLAY_CONTEXT_ZP+1
    ldy #ACTC_OVERLAY_CTX_PASS_ID
    lda #ACTC_OVERLAY_PASS_BODY_COLLECT
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    jsr publish_builtin_runtime_table
    ldy #ACTC_OVERLAY_CTX_BODY_MODE
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    beq actc_overlay_body_mode_collect
    cmp #ACTC_OVERLAY_BODY_MODE_TABLE_ONLY
    beq actc_overlay_ok
    bne actc_overlay_fail

actc_overlay_body_mode_collect:
    jsr collect_proc_body_ops_overlay
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

collect_proc_body_ops_overlay:
    lda #$00
    sta loop_depth_local
    sta for_pending_do_local
    lda #ACTC_OVERLAY_CTX_BEGIN_BODY_SCAN_FN_LO
    jsr call_context_function
    bcs collect_proc_body_ops_overlay_load_failed
    jsr reset_asmblock_count
    jmp collect_proc_body_ops_overlay_loop
collect_proc_body_ops_overlay_load_failed:
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_diag

collect_proc_body_ops_overlay_loop:
    jsr load_current_char
    bne collect_proc_body_ops_overlay_have_char
    jmp collect_proc_body_ops_overlay_done
collect_proc_body_ops_overlay_have_char:
    cmp #10
    beq collect_proc_body_ops_overlay_line_break
    cmp #13
    bne collect_proc_body_ops_overlay_after_line_break
collect_proc_body_ops_overlay_line_break:
    jmp collect_proc_body_ops_overlay_advance_blank
collect_proc_body_ops_overlay_after_line_break:
    lda #ACTC_OVERLAY_CTX_SKIP_SOURCE_SPACES_FN_LO
    jsr call_context_function
    jsr load_current_char
    bne collect_proc_body_ops_overlay_after_space_check
    jmp collect_proc_body_ops_overlay_done
collect_proc_body_ops_overlay_after_space_check:
    lda #<pattern_proc
    ldy #>pattern_proc
    jsr pattern_matches_local_scan_ptr
    bcs :+
    jmp collect_proc_body_ops_overlay_proc_decl
:

    lda #ACTC_OVERLAY_CTX_MATCH_SCALAR_DECL_FN_LO
    jsr call_context_function
    bcs collect_proc_body_ops_overlay_not_scalar_decl
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_BY_CONST_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_SKIP_SOURCE_SPACES_FN_LO
    jsr call_context_function
    lda #<pattern_func
    ldy #>pattern_func
    jsr pattern_matches_local_scan_ptr_keyword
    bcs :+
    jmp collect_proc_body_ops_overlay_func_decl
:
    jmp collect_proc_body_ops_overlay_scalar_decl_after_keyword
collect_proc_body_ops_overlay_not_scalar_decl:

    lda #ACTC_OVERLAY_CTX_CURRENT_PROC_INDEX_PTR_LO
    jsr load_byte_from_context_ptr
    cmp #$FF
    bne :+
    jmp collect_proc_body_ops_overlay_skip_line
:
    lda #ACTC_OVERLAY_CTX_STORE_CURRENT_BODY_DEBUG_MARK_FN_LO
    jsr call_context_function
    lda for_pending_do_local
    beq :+
    jmp collect_proc_body_ops_overlay_try_do
:

    jsr load_current_char
    cmp #'['
    beq collect_proc_body_ops_overlay_open_asmblock

collect_proc_body_ops_overlay_try_asmblock:
    lda #<pattern_asmblock
    ldy #>pattern_asmblock
    jsr pattern_matches_local_scan_ptr_keyword
    bcs collect_proc_body_ops_overlay_try_scalar_decl
    lda #<pattern_asmblock
    ldy #>pattern_asmblock
    jsr source_reader_consume_local_pattern
    jsr call_skip_source_spaces_context
    jsr load_current_char
    cmp #'['
    beq collect_proc_body_ops_overlay_open_asmblock
    jmp collect_proc_body_ops_overlay_bad_asm
collect_proc_body_ops_overlay_open_asmblock:
    jsr call_advance_scan_ptr_context
    jsr append_asmblock_marker
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_asm
:
collect_proc_body_ops_overlay_skip_asmblock:
    jsr load_current_char
    bne :+
    jmp collect_proc_body_ops_overlay_bad_asm
:
    cmp #']'
    beq collect_proc_body_ops_overlay_close_asmblock
    jsr call_advance_scan_ptr_context
    bcc collect_proc_body_ops_overlay_skip_asmblock
    jmp collect_proc_body_ops_overlay_bad_asm
collect_proc_body_ops_overlay_close_asmblock:
    jsr call_advance_scan_ptr_context
    jmp collect_proc_body_ops_overlay_skip_line

collect_proc_body_ops_overlay_try_scalar_decl:
    jmp collect_proc_body_ops_overlay_try_for
collect_proc_body_ops_overlay_scalar_decl_after_keyword:
    lda #ACTC_OVERLAY_CTX_CURRENT_PROC_INDEX_PTR_LO
    jsr load_byte_from_context_ptr
    cmp #$FF
    bne :+
    jmp collect_proc_body_ops_overlay_skip_line
:
    lda for_pending_do_local
    beq :+
    jmp collect_proc_body_ops_overlay_bad_proc
:
    lda #ACTC_OVERLAY_CTX_STORE_CURRENT_BODY_DEBUG_MARK_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_PTR_FN_LO
    jsr call_context_function
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_var
:   sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_CURRENT_PROC_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    lda #ACTC_OVERLAY_CTX_FIND_CURRENT_PROC_LOCAL_FN_LO
    jsr call_indexed_context_function_keep_x
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_var
:   txa
    ldx #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr store_a_to_context_byte_ptr
    ldy symbol_end_y_local
    jsr call_skip_inline_spaces_context
    jsr match_line_end_local
    bcc collect_proc_body_ops_overlay_local_skip_line
    lda #'='
    jsr match_scan_char_local
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_var
:   jmp collect_proc_body_ops_overlay_local_after_equals
collect_proc_body_ops_overlay_local_skip_line:
    jmp collect_proc_body_ops_overlay_skip_line
collect_proc_body_ops_overlay_local_after_equals:
    lda #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    lda #ACTC_OVERLAY_CTX_REQUIRE_WORD_VAR_FN_LO
    jsr call_indexed_context_function_keep_x
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_var
:   ldy symbol_end_y_local
    lda #'='
    jsr consume_scan_char_local
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:   jsr call_skip_inline_spaces_context
    lda #'['
    jsr match_scan_char_local
    bcc collect_proc_body_ops_overlay_try_local_int_group
    jmp collect_proc_body_ops_overlay_try_local_int_parse_value

collect_proc_body_ops_overlay_try_local_int_group:
    lda #'['
    jsr consume_scan_char_local
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:   lda #ACTC_OVERLAY_CTX_EMIT_RUNTIME_VALUE_FN_LO
    jsr call_context_function
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:   jsr call_skip_inline_spaces_context
    lda #']'
    jsr match_scan_char_local
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:   lda #']'
    jsr consume_scan_char_local
    bcc collect_proc_body_ops_overlay_try_local_int_after_value
    jmp collect_proc_body_ops_overlay_bad_literal

collect_proc_body_ops_overlay_try_local_int_parse_value:
    lda #ACTC_OVERLAY_CTX_EMIT_RUNTIME_VALUE_FN_LO
    jsr call_context_function
    bcc collect_proc_body_ops_overlay_try_local_int_after_value
    jmp collect_proc_body_ops_overlay_bad_literal

collect_proc_body_ops_overlay_try_local_int_after_value:
    jsr call_require_line_end_context
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:   lda #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    jsr load_append_body_op_ptr
    lda #'S'
    jsr call_loaded_target_with_a
    jmp collect_proc_body_ops_overlay_skip_line

collect_proc_body_ops_overlay_try_for:
    lda #<pattern_for
    ldy #>pattern_for
    jsr pattern_matches_local_scan_ptr_keyword
    bcc :+
    jmp collect_proc_body_ops_overlay_try_od
:
    lda #<pattern_for
    ldy #>pattern_for
    jsr source_reader_consume_local_pattern
    lda #ACTC_OVERLAY_CTX_SKIP_SOURCE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_PTR_FN_LO
    jsr call_context_function
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_var
:
    sty symbol_end_y_local
    jsr call_find_var_index_context
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_var
:
    stx for_counter_local
    lda #ACTC_OVERLAY_CTX_REQUIRE_WORD_VAR_FN_LO
    jsr call_indexed_context_function_keep_x
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_var
:
    ldy symbol_end_y_local
    jsr call_skip_inline_spaces_context
    lda #'='
    jsr consume_scan_char_local
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:
    lda #ACTC_OVERLAY_CTX_EMIT_RUNTIME_VALUE_FN_LO
    jsr call_context_function
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:
    jsr load_append_body_op_ptr
    ldx for_counter_local
    lda #'S'
    jsr call_loaded_target_with_a

    jsr call_skip_inline_spaces_context
    jsr call_copy_symbol_from_scan_y_context
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:
    sty symbol_end_y_local
    lda #<pattern_to
    ldy #>pattern_to
    jsr symbol_buffer_matches_local_const
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_EMIT_RUNTIME_VALUE_FN_LO
    jsr call_context_function
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:

    jsr call_skip_inline_spaces_context
    jsr match_line_end_local
    bcc collect_proc_body_ops_overlay_for_default_step
    jsr call_copy_symbol_from_scan_y_context
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:
    sty symbol_end_y_local
    lda #<pattern_step
    ldy #>pattern_step
    jsr symbol_buffer_matches_local_const
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:
    ldy symbol_end_y_local
    jsr call_skip_inline_spaces_context
    lda #'-'
    jsr match_scan_char_local
    bcs collect_proc_body_ops_overlay_for_positive_step
    lda #'-'
    sta for_direction_local
    lda #'-'
    jsr consume_scan_char_local
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:
    lda #ACTC_OVERLAY_CTX_STORE_ZERO_INT_LITERAL_FN_LO
    jsr call_context_function
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:
    jsr load_append_body_op_ptr
    lda #'p'
    jsr call_loaded_target_with_a
    lda #ACTC_OVERLAY_CTX_EMIT_RUNTIME_VALUE_FN_LO
    jsr call_context_function
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:
    jsr load_append_body_op_no_arg_ptr
    lda #'m'
    jsr call_loaded_target_with_a
    jmp collect_proc_body_ops_overlay_for_step_done

collect_proc_body_ops_overlay_for_positive_step:
    lda #'+'
    sta for_direction_local
    lda #ACTC_OVERLAY_CTX_EMIT_RUNTIME_VALUE_FN_LO
    jsr call_context_function
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:
    jmp collect_proc_body_ops_overlay_for_step_done

collect_proc_body_ops_overlay_for_default_step:
    lda #'+'
    sta for_direction_local
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_STORE_WORD_LITERAL_FN_LO
    jsr load_context_function_ptr
    lda #$01
    ldy #$00
    jsr call_loaded_target_with_a
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:
    ldy symbol_end_y_local
    jsr load_append_body_op_ptr
    lda #'p'
    jsr call_loaded_target_with_a

collect_proc_body_ops_overlay_for_step_done:
    jsr call_require_line_end_context
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:
    jsr load_append_body_op_ptr
    ldx for_counter_local
    lda #'F'
    jsr call_loaded_target_with_a
    jsr load_append_body_op_no_arg_ptr
    lda for_direction_local
    jsr call_loaded_target_with_a
    lda #$02
    jsr push_loop_kind_local_or_fail
    bcs collect_proc_body_ops_overlay_loop_bad_early
    lda #$01
    sta for_pending_do_local
    jmp collect_proc_body_ops_overlay_skip_line

collect_proc_body_ops_overlay_loop_bad_early:
    jmp collect_proc_body_ops_overlay_bad_proc

collect_proc_body_ops_overlay_try_od:
    lda #<pattern_od
    ldy #>pattern_od
    jsr pattern_matches_local_scan_ptr_keyword
    bcs collect_proc_body_ops_overlay_try_until
    ldx loop_depth_local
    beq collect_proc_body_ops_overlay_loop_bad_early
    dex
    stx loop_depth_local
    lda loop_kind_stack_local,x
    cmp #$02
    beq collect_proc_body_ops_overlay_close_for
    cmp #$01
    bcc :+
    jsr load_append_body_op_no_arg_ptr
    lda #'x'
    jsr call_loaded_target_with_a
    jmp collect_proc_body_ops_overlay_skip_line
:   jsr load_append_body_op_no_arg_ptr
    lda #'o'
    jsr call_loaded_target_with_a
    jmp collect_proc_body_ops_overlay_skip_line
collect_proc_body_ops_overlay_close_for:
    jsr load_append_body_op_no_arg_ptr
    lda #'O'
    jsr call_loaded_target_with_a
    jmp collect_proc_body_ops_overlay_skip_line

collect_proc_body_ops_overlay_try_until:
    lda #<pattern_until
    ldy #>pattern_until
    jsr pattern_matches_local_scan_ptr_keyword
    bcs collect_proc_body_ops_overlay_try_do
    ldx loop_depth_local
    beq collect_proc_body_ops_overlay_loop_bad_early
    dex
    lda loop_kind_stack_local,x
    beq :+
    jmp collect_proc_body_ops_overlay_bad_proc
:
    lda #<pattern_until
    ldy #>pattern_until
    jsr source_reader_consume_local_pattern
    lda #'t'
    jsr store_runtime_condition_with_a_local_or_fail
    bcs :+
    jmp collect_proc_body_ops_overlay_skip_line
:   jmp collect_proc_body_ops_overlay_bad_literal

collect_proc_body_ops_overlay_try_do:
    lda for_pending_do_local
    beq collect_proc_body_ops_overlay_try_while
    lda #<pattern_do
    ldy #>pattern_do
    jsr pattern_matches_local_scan_ptr_keyword
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_proc
:
    lda #$00
    sta for_pending_do_local
    jmp collect_proc_body_ops_overlay_skip_line

collect_proc_body_ops_overlay_try_while:
    lda #<pattern_while
    ldy #>pattern_while
    jsr pattern_matches_local_scan_ptr_keyword
    bcs collect_proc_body_ops_overlay_try_do_keyword
    lda #$01
    jsr push_loop_kind_local_or_fail
    bcs collect_proc_body_ops_overlay_loop_bad
    jsr load_append_body_op_no_arg_ptr
    lda #'d'
    jsr call_loaded_target_with_a
    lda #<pattern_while
    ldy #>pattern_while
    jsr source_reader_consume_local_pattern
    lda #'f'
    jsr store_runtime_condition_with_a_local_or_fail
    bcs :+
    jmp collect_proc_body_ops_overlay_skip_line
:   jmp collect_proc_body_ops_overlay_bad_literal

collect_proc_body_ops_overlay_try_do_keyword:
    lda #<pattern_do
    ldy #>pattern_do
    jsr pattern_matches_local_scan_ptr_keyword
    bcs collect_proc_body_ops_overlay_try_endif
    lda #$00
    jsr push_loop_kind_local_or_fail
    bcs collect_proc_body_ops_overlay_loop_bad
    jsr load_append_body_op_no_arg_ptr
    lda #'d'
    jsr call_loaded_target_with_a
    jmp collect_proc_body_ops_overlay_skip_line

collect_proc_body_ops_overlay_loop_bad:
    jmp collect_proc_body_ops_overlay_bad_proc

collect_proc_body_ops_overlay_try_endif:
    lda #<pattern_endif
    ldy #>pattern_endif
    jsr pattern_matches_local_scan_ptr_keyword
    bcs collect_proc_body_ops_overlay_try_fi
    jsr load_append_body_op_no_arg_ptr
    lda #'v'
    jsr call_loaded_target_with_a
    jmp collect_proc_body_ops_overlay_skip_line

collect_proc_body_ops_overlay_try_fi:
    lda #<pattern_fi
    ldy #>pattern_fi
    jsr pattern_matches_local_scan_ptr_keyword
    bcs collect_proc_body_ops_overlay_try_else
    jsr load_append_body_op_no_arg_ptr
    lda #'v'
    jsr call_loaded_target_with_a
    jmp collect_proc_body_ops_overlay_skip_line

collect_proc_body_ops_overlay_try_else:
    lda #<pattern_else
    ldy #>pattern_else
    jsr pattern_matches_local_scan_ptr_keyword
    bcs collect_proc_body_ops_overlay_try_if
    jsr load_append_body_op_no_arg_ptr
    lda #'w'
    jsr call_loaded_target_with_a
    jmp collect_proc_body_ops_overlay_skip_line

collect_proc_body_ops_overlay_try_if:
    lda #<pattern_if
    ldy #>pattern_if
    jsr pattern_matches_local_scan_ptr_keyword
    bcs collect_proc_body_ops_overlay_try_print_quote
    lda #<pattern_if
    ldy #>pattern_if
    jsr source_reader_consume_local_pattern
    lda #'h'
    jsr store_runtime_condition_with_a_local_or_fail
    bcs :+
    jmp collect_proc_body_ops_overlay_skip_line
:   jmp collect_proc_body_ops_overlay_bad_literal

collect_proc_body_ops_overlay_try_print_quote:
    lda #<pattern_print_quote
    ldy #>pattern_print_quote
    jsr pattern_matches_local_scan_ptr
    bcs collect_proc_body_ops_overlay_try_printe
    lda #<pattern_print_quote
    ldy #>pattern_print_quote
    jsr source_reader_consume_local_pattern
    lda #ACTC_OVERLAY_CTX_STORE_STRING_LITERAL_FN_LO
    jsr call_context_function
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:
    jsr load_append_body_op_ptr
    lda #'s'
    jsr call_loaded_target_with_a
    jmp collect_proc_body_ops_overlay_skip_line

collect_proc_body_ops_overlay_try_printe:
    lda #<pattern_printe_quote
    ldy #>pattern_printe_quote
    jsr pattern_matches_local_scan_ptr
    bcs collect_proc_body_ops_overlay_try_printre
    lda #<pattern_printe_quote
    ldy #>pattern_printe_quote
    jsr source_reader_consume_local_pattern
    lda #ACTC_OVERLAY_CTX_STORE_STRING_LITERAL_FN_LO
    jsr call_context_function
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:
    jsr load_append_body_op_ptr
    lda #'e'
    jsr call_loaded_target_with_a
    jmp collect_proc_body_ops_overlay_skip_line

collect_proc_body_ops_overlay_try_printre:
    lda #<pattern_printre
    ldy #>pattern_printre
    jsr pattern_matches_local_scan_ptr
    bcs collect_proc_body_ops_overlay_try_printr
    lda #<pattern_printre
    ldy #>pattern_printre
    jsr source_reader_consume_local_pattern
    lda #$01
    jsr store_runtime_real_print_with_newline_flag_local_or_fail
    bcs :+
    jmp collect_proc_body_ops_overlay_skip_line
:
    jmp collect_proc_body_ops_overlay_bad_literal

collect_proc_body_ops_overlay_try_printr:
    lda #<pattern_printr
    ldy #>pattern_printr
    jsr pattern_matches_local_scan_ptr
    bcs collect_proc_body_ops_overlay_try_printie
    lda #<pattern_printr
    ldy #>pattern_printr
    jsr source_reader_consume_local_pattern
    lda #$00
    jsr store_runtime_real_print_with_newline_flag_local_or_fail
    bcs :+
    jmp collect_proc_body_ops_overlay_skip_line
:
    jmp collect_proc_body_ops_overlay_bad_literal

collect_proc_body_ops_overlay_try_printie:
    lda #<pattern_printie
    ldy #>pattern_printie
    jsr pattern_matches_local_scan_ptr
    bcs collect_proc_body_ops_overlay_try_printi
    lda #<pattern_printie
    ldy #>pattern_printie
    jsr source_reader_consume_local_pattern
    lda #ACTC_OVERLAY_CTX_STORE_SMALL_DECIMAL_LITERAL_FN_LO
    jsr call_context_function
    bcc :+
    lda #'z'
    jsr store_runtime_expr_with_a_local_or_fail
    bcs :++
    jmp collect_proc_body_ops_overlay_skip_line
:   jsr load_append_body_op_ptr
    lda #'i'
    jsr call_loaded_target_with_a
    jmp collect_proc_body_ops_overlay_skip_line
:   jmp collect_proc_body_ops_overlay_bad_literal

collect_proc_body_ops_overlay_try_printi:
    lda #<pattern_printi
    ldy #>pattern_printi
    jsr pattern_matches_local_scan_ptr
    bcs collect_proc_body_ops_overlay_try_return
    lda #<pattern_printi
    ldy #>pattern_printi
    jsr source_reader_consume_local_pattern
    lda #ACTC_OVERLAY_CTX_STORE_SMALL_DECIMAL_LITERAL_FN_LO
    jsr call_context_function
    bcc :+
    lda #'y'
    jsr store_runtime_expr_with_a_local_or_fail
    bcs :++
    jmp collect_proc_body_ops_overlay_skip_line
:   jsr load_append_body_op_ptr
    lda #'j'
    jsr call_loaded_target_with_a
    jmp collect_proc_body_ops_overlay_skip_line
:   jmp collect_proc_body_ops_overlay_bad_literal

collect_proc_body_ops_overlay_try_return:
    lda #<pattern_return
    ldy #>pattern_return
    jsr pattern_matches_local_scan_ptr_keyword
    bcs collect_proc_body_ops_overlay_try_assignment
    lda #<pattern_return
    ldy #>pattern_return
    jsr source_reader_consume_local_pattern
    ldy #$00
    jsr call_skip_inline_spaces_context
    jsr match_line_end_local
    bcc collect_proc_body_ops_overlay_try_return_emit
    lda #ACTC_OVERLAY_CTX_EMIT_FUNCTION_RETURN_FN_LO
    jsr call_context_function
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:   jsr call_require_line_end_context
    bcc collect_proc_body_ops_overlay_try_return_emit
    jmp collect_proc_body_ops_overlay_bad_literal
collect_proc_body_ops_overlay_try_return_emit:
    jsr load_append_body_op_no_arg_ptr
    lda #'r'
    jsr call_loaded_target_with_a
    jmp collect_proc_body_ops_overlay_skip_line

collect_proc_body_ops_overlay_try_assignment:
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_PTR_FN_LO
    jsr call_context_function
    bcc :+
    jmp collect_proc_body_ops_overlay_skip_line
:   sty symbol_end_y_local
    lda #<pattern_exit
    ldy #>pattern_exit
    jsr symbol_buffer_matches_local_const
    bcs collect_proc_body_ops_overlay_try_assignment_not_exit
    ldy symbol_end_y_local
    jsr call_require_line_end_context
    bcs collect_proc_body_ops_overlay_exit_bad
    ldx loop_depth_local
    beq collect_proc_body_ops_overlay_exit_bad
    dex
    lda loop_kind_stack_local,x
    tax
    jsr load_append_body_op_ptr
    lda #'X'
    jsr call_loaded_target_with_a
    jmp collect_proc_body_ops_overlay_skip_line
collect_proc_body_ops_overlay_exit_bad:
    jmp collect_proc_body_ops_overlay_bad_proc
collect_proc_body_ops_overlay_try_assignment_not_exit:
    ldy symbol_end_y_local
    jsr call_skip_inline_spaces_context
    lda #'='
    jsr match_scan_char_local
    bcc :+
    jmp collect_proc_body_ops_overlay_try_local_call
:
    sty symbol_end_y_local
    jsr call_find_var_index_context
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_var
:   txa
    ldx #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr store_a_to_context_byte_ptr
    lda #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    lda #ACTC_OVERLAY_CTX_REQUIRE_WORD_VAR_FN_LO
    jsr call_indexed_context_function_keep_x
    bcc collect_proc_body_ops_overlay_try_assignment_word
    lda #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcc collect_proc_body_ops_overlay_try_assignment_real
    jmp collect_proc_body_ops_overlay_bad_var

collect_proc_body_ops_overlay_try_assignment_word:
    ldy symbol_end_y_local
    lda #'='
    jsr consume_scan_char_local
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:   lda #ACTC_OVERLAY_CTX_EMIT_RUNTIME_VALUE_FN_LO
    jsr call_context_function
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
collect_proc_body_ops_overlay_try_assignment_word_require_line_end:
    jsr call_require_line_end_context
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:   lda #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    jsr load_append_body_op_ptr
    lda #'S'
    jsr call_loaded_target_with_a
    jmp collect_proc_body_ops_overlay_skip_line

collect_proc_body_ops_overlay_try_assignment_real:
    ldy symbol_end_y_local
    lda #'='
    jsr consume_scan_char_local
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_literal
:   jsr emit_real_assignment_local_or_fail
    bcc collect_proc_body_ops_overlay_skip_line
    jmp collect_proc_body_ops_overlay_bad_literal

collect_proc_body_ops_overlay_try_local_call:
    ldy symbol_end_y_local
    lda #'('
    jsr match_scan_char_local
    bcs collect_proc_body_ops_overlay_skip_line
    lda #ACTC_OVERLAY_CTX_RESOLVE_CALL_TARGET_FN_LO
    jsr call_context_function
    bcc collect_proc_body_ops_overlay_call_resolved
    jmp collect_proc_body_ops_overlay_bad_proc
collect_proc_body_ops_overlay_call_resolved:
    ldy symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_EMIT_CALL_ARGS_FN_LO
    jsr call_context_function
    bcc :+
    jmp collect_proc_body_ops_overlay_bad_proc
:   lda #ACTC_OVERLAY_CTX_CALL_TARGET_KIND_PTR_LO
    jsr load_byte_from_context_ptr
    pha
    lda #ACTC_OVERLAY_CTX_CALL_TARGET_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    bpl collect_proc_body_ops_overlay_positive_call
    ldy loop_depth_local
    beq collect_proc_body_ops_overlay_positive_call
    pla
    lda #'U'
    bne collect_proc_body_ops_overlay_append_call
collect_proc_body_ops_overlay_positive_call:
    pla
    cmp #'A'
    bne collect_proc_body_ops_overlay_append_call
    ldy loop_depth_local
    bne collect_proc_body_ops_overlay_append_call
    lda #'u'
collect_proc_body_ops_overlay_append_call:
    pha
    jsr load_append_body_op_ptr
    pla
    jsr call_loaded_target_with_a

collect_proc_body_ops_overlay_skip_line:
    lda #ACTC_OVERLAY_CTX_SKIP_SOURCE_LINE_FN_LO
    jsr call_context_function
    jmp collect_proc_body_ops_overlay_loop

collect_proc_body_ops_overlay_proc_decl:
    lda loop_depth_local
    ora for_pending_do_local
    beq :+
    jmp collect_proc_body_ops_overlay_bad_proc
:
    lda #<pattern_proc
    ldy #>pattern_proc
    jsr source_reader_consume_local_pattern
    jmp collect_proc_body_ops_overlay_routine_decl_after_keyword

collect_proc_body_ops_overlay_func_decl:
    lda #<pattern_func
    ldy #>pattern_func
    jsr source_reader_consume_local_pattern
collect_proc_body_ops_overlay_routine_decl_after_keyword:
    lda #ACTC_OVERLAY_CTX_SKIP_SOURCE_SPACES_FN_LO
    jsr call_context_function
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_PTR_FN_LO
    jsr call_context_function
    bcs collect_proc_body_ops_overlay_bad_proc
    lda #ACTC_OVERLAY_CTX_RESOLVE_ROUTINE_DECL_FN_LO
    jsr call_context_function
    bcs collect_proc_body_ops_overlay_bad_proc
    txa
    cmp #$FF
    beq collect_proc_body_ops_overlay_skip_line
    ldx #ACTC_OVERLAY_CTX_CURRENT_PROC_INDEX_PTR_LO
    jsr store_a_to_context_byte_ptr
    lda #ACTC_OVERLAY_CTX_STORE_CURRENT_BODY_DEBUG_MARK_FN_LO
    jsr call_context_function
    jsr emit_current_proc_param_binds_local_or_fail
    jmp collect_proc_body_ops_overlay_skip_line

collect_proc_body_ops_overlay_advance_blank:
    jsr call_advance_scan_ptr_context
    jmp collect_proc_body_ops_overlay_loop

collect_proc_body_ops_overlay_bad_proc:
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_diag

collect_proc_body_ops_overlay_bad_var:
    lda #<msg_bad_var
    ldy #>msg_bad_var
    jmp fail_with_diag

collect_proc_body_ops_overlay_bad_literal:
    lda #<msg_bad_literal
    ldy #>msg_bad_literal
    jmp fail_with_diag

collect_proc_body_ops_overlay_bad_asm:
    lda #<msg_bad_asm
    ldy #>msg_bad_asm
    jmp fail_with_diag

collect_proc_body_ops_overlay_done:
    lda for_pending_do_local
    ora loop_depth_local
    beq :+
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_diag
:
    lda #ACTC_OVERLAY_CTX_FINISH_BODY_SCAN_FN_LO
    jsr call_context_function
    bcc :+
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_diag
:   clc
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

reset_asmblock_count:
    lda #ACTC_OVERLAY_CTX_IMPORT_FLAGS_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    and #$0F
    sta (ACTC_OVERLAY_WORK_ZP),y
    rts

append_asmblock_marker:
    lda #ACTC_OVERLAY_CTX_IMPORT_FLAGS_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp #$F0
    bcs append_asmblock_marker_full
    clc
    adc #$10
    sta (ACTC_OVERLAY_WORK_ZP),y
    sec
    sbc #$10
    lsr a
    lsr a
    lsr a
    lsr a
    tax
    jsr load_append_body_op_ptr
    lda #'@'
    jsr call_loaded_target_with_a
    clc
    rts
append_asmblock_marker_full:
    sec
    rts

call_skip_inline_spaces_context:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jmp call_context_function

call_skip_source_spaces_context:
    lda #ACTC_OVERLAY_CTX_SKIP_SOURCE_SPACES_FN_LO
    jmp call_context_function

call_require_line_end_context:
    lda #ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    jmp call_context_function

call_restore_source_mark_context:
    lda #ACTC_OVERLAY_CTX_RESTORE_SOURCE_MARK_FN_LO
    jmp call_context_function

call_copy_symbol_from_scan_y_context:
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    jmp call_context_function

call_find_var_index_context:
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jmp call_context_function

call_advance_scan_ptr_context:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_FN_LO
    jmp call_context_function

match_scan_char_local:
    sta stored_byte_local
    jsr read_scan_char_at_y
    cmp stored_byte_local
    bne match_scan_char_local_fail
    clc
    rts
match_scan_char_local_fail:
    sec
    rts

match_line_end_local:
    lda #$00
    jsr match_scan_char_local
    bcc match_line_end_local_ok
    lda #10
    jsr match_scan_char_local
    bcc match_line_end_local_ok
    lda #13
    jsr match_scan_char_local
    bcc match_line_end_local_ok
    sec
    rts
match_line_end_local_ok:
    clc
    rts

peek_decimal_digit_value_local:
    jsr read_scan_char_at_y
    cmp #'0'
    bcc peek_decimal_digit_value_local_fail
    cmp #'9'+1
    bcs peek_decimal_digit_value_local_fail
    sec
    sbc #'0'
    clc
    rts
peek_decimal_digit_value_local_fail:
    sec
    rts

consume_scan_char_local:
    sta stored_byte_local
    jsr read_scan_char_at_y
    cmp stored_byte_local
    bne consume_scan_char_local_fail
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jmp call_context_function
consume_scan_char_local_fail:
    sec
    rts

consume_uppercase_char_local:
    sta stored_byte_local
    jsr read_scan_char_at_y
    jsr uppercase_ascii_local
    cmp stored_byte_local
    bne consume_uppercase_char_local_fail
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    jmp call_context_function
consume_uppercase_char_local_fail:
    sec
    rts

uppercase_ascii_local:
    cmp #'a'
    bcc uppercase_ascii_local_done
    cmp #'z'+1
    bcs uppercase_ascii_local_done
    and #$DF
uppercase_ascii_local_done:
    rts

push_loop_kind_local_or_fail:
    pha
    ldx loop_depth_local
    cpx #LOOP_MAX
    bcc push_loop_kind_local_have_depth
    pla
    sec
    rts
push_loop_kind_local_have_depth:
    pla
    sta loop_kind_stack_local,x
    inc loop_depth_local
    rts

emit_current_proc_param_binds_local_or_fail:
    lda #ACTC_OVERLAY_CTX_CURRENT_PROC_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    lda #ACTC_OVERLAY_CTX_LOAD_PROC_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_PROC_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    and #ACTC_PROC_META_MACHINE
    bne emit_current_proc_param_binds_local_done
    lda (ACTC_OVERLAY_WORK_ZP),y
    and #ACTC_PROC_META_PARAM_COUNT_MASK
    beq emit_current_proc_param_binds_local_done
    sta param_bind_count_local
    iny
    clc
    adc (ACTC_OVERLAY_WORK_ZP),y
    sta param_bind_base_local
emit_current_proc_param_binds_local_loop:
    dec param_bind_base_local
    ldx param_bind_base_local
    jsr load_append_body_op_ptr
    lda #'S'
    jsr call_loaded_target_with_a
    dec param_bind_count_local
    bne emit_current_proc_param_binds_local_loop
emit_current_proc_param_binds_local_done:
    rts

emit_real_assignment_local_or_fail:
    lda #ACTC_OVERLAY_CTX_EMIT_REAL_FUNCTION_ASSIGNMENT_FN_LO
    jsr call_context_function
    bcs :+
    rts
:
    jsr call_skip_inline_spaces_context
    lda #'('
    jsr match_scan_char_local
    bcs :+
    jmp emit_real_small_int_assignment_local_or_fail
:
    jsr peek_decimal_digit_value_local
    bcs :+
    jmp emit_real_small_int_assignment_local_or_fail
:
    jsr try_consume_real_open_local
    bcs :+
    jmp emit_real_explicit_value_local_or_fail
:
    ; Recognize the one plain-word bridge before the shared REAL parser. This
    ; keeps assignment lowering on one path without losing CARD/INT conversion.
    sty symbol_start_y_local
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    jsr call_copy_symbol_from_scan_y_context
    bcs emit_real_assignment_local_try_runtime
    sty symbol_end_y_local
    jsr call_find_var_index_context
    bcs emit_real_assignment_local_try_runtime
    stx real_lhs_index_local
    ldx real_lhs_index_local
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_BRIDGE_WORD_VAR_FN_LO
    jsr call_indexed_context_function
    bcs emit_real_assignment_local_try_runtime
    ldy symbol_end_y_local
    jsr call_require_line_end_context
    bcs emit_real_assignment_local_after_value_fail
    jmp emit_real_bridge_assignment_local_ok
emit_real_assignment_local_try_runtime:
    jsr call_restore_source_mark_context
    ldy symbol_start_y_local
    jsr emit_runtime_real_value_local_or_fail
    bcs emit_real_assignment_local_after_value_fail
    jmp emit_real_binary_assignment_local_ok
emit_real_assignment_local_after_value_fail:
    sec
    rts

emit_real_binary_assignment_local_ok:
    jsr call_require_line_end_context
    bcs emit_real_binary_assignment_local_fail
    jsr load_append_body_op_ptr
    lda #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    lda #'T'
    jsr call_loaded_target_with_a
    lda #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    lda #'S'
    jsr call_loaded_target_with_a
    clc
    rts
emit_real_binary_assignment_local_fail:
    sec
    rts

emit_real_bridge_assignment_local_ok:
    jsr load_append_body_op_ptr
    ldx real_lhs_index_local
    lda #'L'
    jsr call_loaded_target_with_a
    ldx real_lhs_index_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_REAL_BRIDGE_EXTERNAL_FN_LO
    jsr call_indexed_context_function_keep_x
    bcc :+
    sec
    rts
:   jsr load_append_body_op_ptr
    lda #'u'
    jsr call_loaded_target_with_a
    lda #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    lda #'T'
    jsr call_loaded_target_with_a
    lda #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    lda #'S'
    jsr call_loaded_target_with_a
    clc
    rts

try_consume_int_open_local:
    sty symbol_start_y_local
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    lda #<pattern_int_decl
    ldy #>pattern_int_decl
    jsr consume_keyword_open_local
    bcs try_consume_int_open_local_fail_restore
    clc
    rts
try_consume_int_open_local_fail_restore:
    jsr call_restore_source_mark_context
    ldy symbol_start_y_local
    sec
    rts

try_emit_runtime_int_value_local_or_fail:
    lda #$00
    sta int_parse_matched_local
    jsr try_consume_int_open_local
    bcs try_emit_runtime_int_value_local_or_fail_miss
    lda #$01
    sta int_parse_matched_local
    jmp emit_runtime_int_explicit_value_after_open_local_or_fail
try_emit_runtime_int_value_local_or_fail_miss:
    sec
    rts

emit_runtime_int_explicit_value_after_open_local_or_fail:
    jsr call_copy_symbol_from_scan_y_context
    bcs emit_runtime_int_explicit_value_after_open_local_or_fail_fail
    sty symbol_end_y_local
    jsr call_find_var_index_context
    bcs emit_runtime_int_explicit_value_after_open_local_or_fail_fail
    stx real_lhs_index_local
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcs emit_runtime_int_explicit_value_after_open_local_or_fail_fail
    ldy symbol_end_y_local
    jsr call_skip_inline_spaces_context
    lda #')'
    jsr match_scan_char_local
    bcs emit_runtime_int_explicit_value_after_open_local_or_fail_fail
    lda #')'
    jsr consume_scan_char_local
    bcs emit_runtime_int_explicit_value_after_open_local_or_fail_fail
    jsr call_skip_inline_spaces_context
    sty symbol_end_y_local
    jsr load_append_body_op_ptr
    ldx real_lhs_index_local
    lda #'L'
    jsr call_loaded_target_with_a
    ldx real_lhs_index_local
    lda #'U'
    jsr call_loaded_target_with_a
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_F_TO_I_FN_LO
    jsr call_context_function
    bcs emit_runtime_int_explicit_value_after_open_local_or_fail_fail
    stx real_rhs_index_local
    jsr load_append_body_op_ptr
    ldx real_rhs_index_local
    lda #'u'
    jsr call_loaded_target_with_a
    ldy symbol_end_y_local
    clc
    rts
emit_runtime_int_explicit_value_after_open_local_or_fail_fail:
    sec
    rts

try_consume_real_open_local:
    sty symbol_start_y_local
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    lda #<pattern_real_decl
    ldy #>pattern_real_decl
    jsr consume_keyword_open_local
    bcs try_consume_real_open_local_fail_restore
    clc
    rts
try_consume_real_open_local_fail_restore:
    jsr call_restore_source_mark_context
    ldy symbol_start_y_local
    sec
    rts

try_consume_fabs_open_local:
    sty symbol_start_y_local
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    lda #<pattern_fabs
    ldy #>pattern_fabs
    jsr consume_keyword_open_local
    bcs try_consume_fabs_open_local_fail_restore
    clc
    rts
try_consume_fabs_open_local_fail_restore:
    jsr call_restore_source_mark_context
    ldy symbol_start_y_local
    sec
    rts

try_consume_fsqrt_open_local:
    sty symbol_start_y_local
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    lda #<pattern_fsqrt
    ldy #>pattern_fsqrt
    jsr consume_keyword_open_local
    bcs try_consume_fsqrt_open_local_fail_restore
    clc
    rts
try_consume_fsqrt_open_local_fail_restore:
    jsr call_restore_source_mark_context
    ldy symbol_start_y_local
    sec
    rts

try_consume_fsign_open_local:
    sty symbol_start_y_local
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    lda #<pattern_fsign
    ldy #>pattern_fsign
    jsr consume_keyword_open_local
    bcs try_consume_fsign_open_local_fail_restore
    clc
    rts
try_consume_fsign_open_local_fail_restore:
    jsr call_restore_source_mark_context
    ldy symbol_start_y_local
    sec
    rts

emit_real_explicit_bridge_assignment_local_or_fail:
    jsr call_copy_symbol_from_scan_y_context
    bcs emit_real_explicit_bridge_assignment_local_or_fail_fail
    sty symbol_end_y_local
    jsr call_find_var_index_context
    bcs emit_real_explicit_bridge_assignment_local_or_fail_fail
    stx real_lhs_index_local
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_BRIDGE_WORD_VAR_FN_LO
    jsr call_indexed_context_function
    bcs emit_real_explicit_bridge_assignment_local_or_fail_fail
    ldy symbol_end_y_local
    jsr call_skip_inline_spaces_context
    lda #')'
    jsr match_scan_char_local
    bcs emit_real_explicit_bridge_assignment_local_or_fail_fail
    lda #')'
    jsr consume_scan_char_local
    bcs emit_real_explicit_bridge_assignment_local_or_fail_fail
    jsr call_skip_inline_spaces_context
    jsr call_require_line_end_context
    bcs emit_real_explicit_bridge_assignment_local_or_fail_fail
    jmp emit_real_bridge_assignment_local_ok
emit_real_explicit_bridge_assignment_local_or_fail_fail:
    sec
    rts

emit_real_explicit_value_local_or_fail:
    sty symbol_start_y_local
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    jsr emit_real_explicit_bridge_assignment_local_or_fail
    bcs :+
    clc
    rts
:   jsr call_restore_source_mark_context
    ldy symbol_start_y_local
    jsr parse_positive_word_sum_local_or_fail
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_wide
:
    jsr call_skip_inline_spaces_context
    lda #')'
    jsr match_scan_char_local
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_wide
:
    lda #')'
    jsr consume_scan_char_local
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_wide
:
    jsr call_skip_inline_spaces_context
    jsr call_require_line_end_context
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_wide
:
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$01
    lda (ACTC_OVERLAY_WORK_ZP),y
    bne emit_real_explicit_value_local_or_fail_wide
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq emit_real_explicit_value_local_or_fail_zero
    lda #ACTC_OVERLAY_CTX_STORE_ZERO_INT_LITERAL_FN_LO
    jsr call_context_function
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_fail
:
    stx real_rhs_index_local
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta stored_byte_local
    ldy #$00
    lda #ACTC_OVERLAY_CTX_STORE_WORD_LITERAL_FN_LO
    jsr load_context_function_ptr
    lda stored_byte_local
    jsr call_loaded_target_with_a
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_fail
:
    stx real_rhs_index_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_I_TO_F_FN_LO
    jsr call_context_function
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_fail
:
    stx real_lhs_index_local
    jmp emit_real_explicit_value_local_finish

emit_real_explicit_value_local_or_fail_zero:
    lda #ACTC_OVERLAY_CTX_STORE_ZERO_INT_LITERAL_FN_LO
    jsr call_context_function
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_fail
:
    stx real_rhs_index_local
    stx real_lhs_index_local
    jmp emit_real_literal_assignment_local_from_indexes

emit_real_explicit_value_local_or_fail_wide:
    jsr call_restore_source_mark_context
    ldy symbol_start_y_local
    jsr parse_positive_word_sum_local_or_fail
    bcs emit_real_explicit_value_local_or_fail_signed_prep
    jsr call_skip_inline_spaces_context
    lda #')'
    jsr match_scan_char_local
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_signed_prep
:
    lda #')'
    jsr consume_scan_char_local
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_signed_prep
:
    jsr call_skip_inline_spaces_context
    jsr call_require_line_end_context
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_signed_prep
:
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta stored_byte_local
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    ora stored_byte_local
    bne :+
    jmp emit_real_explicit_value_local_or_fail_zero
:
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    tax
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    tay
    txa
    sta stored_byte_local
    lda #ACTC_OVERLAY_CTX_STORE_WORD_LITERAL_FN_LO
    jsr load_context_function_ptr
    lda stored_byte_local
    jsr call_loaded_target_with_a
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_fail
:
    stx real_rhs_index_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_I_TO_F_FN_LO
    jsr call_context_function
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_fail
:
    stx real_lhs_index_local
    jmp emit_real_explicit_value_local_finish

emit_real_explicit_value_local_or_fail_signed_prep:
    jsr call_restore_source_mark_context
    ldy symbol_start_y_local
    jsr call_skip_inline_spaces_context
    lda #'0'
    jsr match_scan_char_local
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_fail
:
    lda #'0'
    jsr consume_scan_char_local
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_fail
:
    jsr call_skip_inline_spaces_context
    lda #'-'
    jsr match_scan_char_local
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_fail
:
    lda #'-'
    jsr consume_scan_char_local
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_fail
:
    jsr parse_optional_grouped_positive_word_sum_local_or_fail
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_fail
:
    jsr call_skip_inline_spaces_context
    lda #')'
    jsr match_scan_char_local
    bcc :+
    jmp emit_real_explicit_value_local_or_fail_fail
:
    lda #')'
    jsr consume_scan_char_local
    bcs emit_real_explicit_value_local_or_fail_fail
    jsr call_skip_inline_spaces_context
    jsr call_require_line_end_context
    bcs emit_real_explicit_value_local_or_fail_fail
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda #$00
    sec
    sbc (ACTC_OVERLAY_WORK_ZP),y
    tax
    iny
    lda #$00
    sbc (ACTC_OVERLAY_WORK_ZP),y
    tay
    txa
    sta stored_byte_local
    lda #ACTC_OVERLAY_CTX_STORE_WORD_LITERAL_FN_LO
    jsr load_context_function_ptr
    lda stored_byte_local
    jsr call_loaded_target_with_a
    bcs emit_real_explicit_value_local_or_fail_fail
    stx real_rhs_index_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_S_TO_F_FN_LO
    jsr call_context_function
    bcs emit_real_explicit_value_local_or_fail_fail
    stx real_lhs_index_local

emit_real_explicit_value_local_finish:
    jsr load_append_body_op_ptr
    ldx real_rhs_index_local
    lda #'p'
    jsr call_loaded_target_with_a
    ldx real_lhs_index_local
    lda #'u'
    jsr call_loaded_target_with_a
    lda #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    lda #'T'
    jsr call_loaded_target_with_a
    lda #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    lda #'S'
    jsr call_loaded_target_with_a
    clc
    rts

emit_real_explicit_value_local_or_fail_fail:
    sec
    rts

.include "actc_overlay_positive_word.inc"

emit_runtime_real_push_literal_local_from_indexes:
    jsr load_append_body_op_ptr
    ldx real_rhs_index_local
    lda #'p'
    jsr call_loaded_target_with_a
    ldx real_lhs_index_local
    lda #'p'
    jsr call_loaded_target_with_a
    ldy symbol_end_y_local
    clc
    rts

emit_runtime_real_wide_bridge_value_local_from_indexes:
    jsr load_append_body_op_ptr
    ldx real_rhs_index_local
    lda #'p'
    jsr call_loaded_target_with_a
    ldx real_lhs_index_local
    lda #'u'
    jsr call_loaded_target_with_a
    ldy symbol_end_y_local
    clc
    rts

emit_runtime_real_unary_value_local_or_fail:
    jsr call_copy_symbol_from_scan_y_context
    bcs emit_runtime_real_unary_value_local_or_fail_fail
    sty symbol_end_y_local
    jsr call_find_var_index_context
    bcs emit_runtime_real_unary_value_local_or_fail_fail
    stx real_lhs_index_local
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcs emit_runtime_real_unary_value_local_or_fail_fail
    ldy symbol_end_y_local
    jsr call_skip_inline_spaces_context
    lda #')'
    jsr match_scan_char_local
    bcs emit_runtime_real_unary_value_local_or_fail_fail
    lda #')'
    jsr consume_scan_char_local
    bcs emit_runtime_real_unary_value_local_or_fail_fail
    jsr call_skip_inline_spaces_context
    sty symbol_end_y_local
    jsr load_append_body_op_ptr
    ldx real_lhs_index_local
    lda #'L'
    jsr call_loaded_target_with_a
    ldx real_lhs_index_local
    lda #'U'
    jsr call_loaded_target_with_a
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_REAL_OPERATOR_EXTERNAL_FN_LO
    jsr load_context_function_ptr
    lda real_operator_local
    jsr call_loaded_target_with_a
    bcs emit_runtime_real_unary_value_local_or_fail_fail
    stx real_rhs_index_local
    jsr load_append_body_op_ptr
    ldx real_rhs_index_local
    lda #'u'
    jsr call_loaded_target_with_a
    ldy symbol_end_y_local
    clc
    rts
emit_runtime_real_unary_value_local_or_fail_fail:
    sec
    rts

emit_runtime_real_binary_value_local_or_fail:
    sty symbol_start_y_local
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    lda #$00
    sta real_binary_function_local
    jsr call_copy_symbol_from_scan_y_context
    bcc :+
    jmp emit_runtime_real_binary_value_local_or_fail_restore
:
    sty symbol_end_y_local
    lda #<pattern_fmin
    ldy #>pattern_fmin
    jsr symbol_buffer_matches_local_const
    bcc emit_runtime_real_binary_value_local_fmin
    lda #<pattern_fmax
    ldy #>pattern_fmax
    jsr symbol_buffer_matches_local_const
    bcc emit_runtime_real_binary_value_local_fmax
    lda #<pattern_fclamp
    ldy #>pattern_fclamp
    jsr symbol_buffer_matches_local_const
    bcs emit_runtime_real_binary_value_local_first_symbol
    lda #'k'
    sta real_operator_local
    inc real_binary_function_local
    inc real_binary_function_local
    bne emit_runtime_real_binary_value_local_consume_open
emit_runtime_real_binary_value_local_fmax:
    lda #'>'
    bne emit_runtime_real_binary_value_local_function
emit_runtime_real_binary_value_local_fmin:
    lda #'<'
emit_runtime_real_binary_value_local_function:
    sta real_operator_local
    inc real_binary_function_local
emit_runtime_real_binary_value_local_consume_open:
    ldy symbol_end_y_local
    jsr call_skip_inline_spaces_context
    lda #'('
    jsr consume_scan_char_local
    bcc :+
    jmp emit_runtime_real_binary_value_local_or_fail_restore
:
    jsr call_skip_inline_spaces_context
    jsr call_copy_symbol_from_scan_y_context
    bcc :+
    jmp emit_runtime_real_binary_value_local_or_fail_restore
:
    sty symbol_end_y_local
emit_runtime_real_binary_value_local_first_symbol:
    jsr call_find_var_index_context
    bcc :+
    jmp emit_runtime_real_binary_value_local_or_fail_restore
:
    stx real_lhs_index_local
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcc :+
    jmp emit_runtime_real_binary_value_local_or_fail_restore
:
    ldy symbol_end_y_local
    jsr call_skip_inline_spaces_context
    lda real_binary_function_local
    beq emit_runtime_real_binary_value_local_infix_operator
    lda #','
    jsr consume_scan_char_local
    bcc :+
    jmp emit_runtime_real_binary_value_local_or_fail_restore
:
    jmp emit_runtime_real_binary_value_local_after_operator
emit_runtime_real_binary_value_local_infix_operator:
    lda #'+'
    jsr match_scan_char_local
    bcc emit_runtime_real_binary_value_local_operator
    lda #'-'
    jsr match_scan_char_local
    bcc emit_runtime_real_binary_value_local_operator
    lda #'*'
    jsr match_scan_char_local
    bcc emit_runtime_real_binary_value_local_operator
    lda #'/'
    jsr match_scan_char_local
    bcc emit_runtime_real_binary_value_local_operator
    jmp emit_runtime_real_binary_value_local_or_fail_restore
emit_runtime_real_binary_value_local_operator:
    sta real_operator_local
    lda real_operator_local
    jsr consume_scan_char_local
    bcs emit_runtime_real_binary_value_local_fail_near
emit_runtime_real_binary_value_local_after_operator:
    jsr call_skip_inline_spaces_context
    jsr call_copy_symbol_from_scan_y_context
    bcs emit_runtime_real_binary_value_local_fail_near
    sty symbol_end_y_local
    jsr call_find_var_index_context
    bcs emit_runtime_real_binary_value_local_fail_near
    stx real_rhs_index_local
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcs emit_runtime_real_binary_value_local_fail_near
    ldy symbol_end_y_local
    jsr call_skip_inline_spaces_context
    lda real_binary_function_local
    beq emit_runtime_real_binary_value_local_args_done
    cmp #$02
    bne emit_runtime_real_binary_value_local_consume_close
    lda #','
    jsr consume_scan_char_local
    bcs emit_runtime_real_binary_value_local_fail_near
    jsr call_skip_inline_spaces_context
    jsr call_copy_symbol_from_scan_y_context
    bcs emit_runtime_real_binary_value_local_fail_near
    sty symbol_end_y_local
    jsr call_find_var_index_context
    bcs emit_runtime_real_binary_value_local_fail_near
    stx real_third_index_local
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcs emit_runtime_real_binary_value_local_fail_near
    ldy symbol_end_y_local
    jsr call_skip_inline_spaces_context
    jmp emit_runtime_real_binary_value_local_consume_close
emit_runtime_real_binary_value_local_fail_near:
    jmp emit_runtime_real_binary_value_local_or_fail_restore
emit_runtime_real_binary_value_local_consume_close:
    lda #')'
    jsr consume_scan_char_local
    bcs emit_runtime_real_binary_value_local_or_fail_restore
    jsr call_skip_inline_spaces_context
emit_runtime_real_binary_value_local_args_done:
    sty symbol_end_y_local
    jsr load_append_body_op_ptr
    ldx real_lhs_index_local
    lda #'L'
    jsr call_loaded_target_with_a
    ldx real_lhs_index_local
    lda #'U'
    jsr call_loaded_target_with_a
    ldx real_rhs_index_local
    lda #'L'
    jsr call_loaded_target_with_a
    ldx real_rhs_index_local
    lda #'U'
    jsr call_loaded_target_with_a
    lda real_binary_function_local
    cmp #$02
    bne :+
    ldx real_third_index_local
    lda #'L'
    jsr call_loaded_target_with_a
    ldx real_third_index_local
    lda #'U'
    jsr call_loaded_target_with_a
:
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_REAL_OPERATOR_EXTERNAL_FN_LO
    jsr load_context_function_ptr
    lda real_operator_local
    jsr call_loaded_target_with_a
    bcs emit_runtime_real_binary_value_local_or_fail_restore
    stx real_rhs_index_local
    jsr load_append_body_op_ptr
    ldx real_rhs_index_local
    lda #'u'
    jsr call_loaded_target_with_a
    ldy symbol_end_y_local
    clc
    rts
emit_runtime_real_binary_value_local_or_fail_restore:
    jsr call_restore_source_mark_context
    ldy symbol_start_y_local
    sec
    rts

emit_runtime_real_explicit_bridge_value_local_or_fail:
    jsr call_copy_symbol_from_scan_y_context
    bcs emit_runtime_real_explicit_bridge_value_local_or_fail_fail
    sty symbol_end_y_local
    jsr call_find_var_index_context
    bcs emit_runtime_real_explicit_bridge_value_local_or_fail_fail
    stx real_lhs_index_local
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_BRIDGE_WORD_VAR_FN_LO
    jsr call_indexed_context_function
    bcs emit_runtime_real_explicit_bridge_value_local_or_fail_fail
    ldy symbol_end_y_local
    jsr call_skip_inline_spaces_context
    lda #')'
    jsr match_scan_char_local
    bcs emit_runtime_real_explicit_bridge_value_local_or_fail_fail
    lda #')'
    jsr consume_scan_char_local
    bcs emit_runtime_real_explicit_bridge_value_local_or_fail_fail
    sty symbol_end_y_local
    jsr load_append_body_op_ptr
    ldx real_lhs_index_local
    lda #'L'
    jsr call_loaded_target_with_a
    ldx real_lhs_index_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_REAL_BRIDGE_EXTERNAL_FN_LO
    jsr call_indexed_context_function_keep_x
    bcs emit_runtime_real_explicit_bridge_value_local_or_fail_fail
    stx real_rhs_index_local
    jsr load_append_body_op_ptr
    ldx real_rhs_index_local
    lda #'u'
    jsr call_loaded_target_with_a
    ldy symbol_end_y_local
    jsr call_skip_inline_spaces_context
    clc
    rts
emit_runtime_real_explicit_bridge_value_local_or_fail_fail:
    sec
    rts

emit_runtime_real_explicit_value_after_open_local_or_fail:
    sty symbol_start_y_local
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    jsr emit_runtime_real_explicit_bridge_value_local_or_fail
    bcs :+
    clc
    rts
:
    jsr call_restore_source_mark_context
    ldy symbol_start_y_local
    jsr parse_positive_word_sum_local_or_fail
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_local_or_fail_wide
:   jsr call_skip_inline_spaces_context
    lda #')'
    jsr match_scan_char_local
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_local_or_fail_wide
:   lda #')'
    jsr consume_scan_char_local
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_local_or_fail_wide
:   jsr call_skip_inline_spaces_context
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$01
    lda (ACTC_OVERLAY_WORK_ZP),y
    bne emit_runtime_real_explicit_value_after_open_local_or_fail_wide
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    bne emit_runtime_real_explicit_value_after_open_local_or_fail_nonzero
    lda #ACTC_OVERLAY_CTX_STORE_ZERO_INT_LITERAL_FN_LO
    jsr call_context_function
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_local_or_fail_fail
:   stx real_rhs_index_local
    stx real_lhs_index_local
    jmp emit_runtime_real_push_literal_local_from_indexes
emit_runtime_real_explicit_value_after_open_local_or_fail_nonzero:
    lda #ACTC_OVERLAY_CTX_STORE_ZERO_INT_LITERAL_FN_LO
    jsr call_context_function
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_local_or_fail_fail
:   stx real_rhs_index_local
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta stored_byte_local
    ldy #$00
    lda #ACTC_OVERLAY_CTX_STORE_WORD_LITERAL_FN_LO
    jsr load_context_function_ptr
    lda stored_byte_local
    jsr call_loaded_target_with_a
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_local_or_fail_fail
:   stx real_rhs_index_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_I_TO_F_FN_LO
    jsr call_context_function
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_local_or_fail_fail
:   stx real_lhs_index_local
    jmp emit_runtime_real_wide_bridge_value_local_from_indexes

emit_runtime_real_explicit_value_after_open_local_or_fail_wide:
    jsr call_restore_source_mark_context
    ldy symbol_start_y_local
    jsr parse_positive_word_sum_local_or_fail
    bcs emit_runtime_real_explicit_value_after_open_local_or_fail_signed
    jsr call_skip_inline_spaces_context
    lda #')'
    jsr match_scan_char_local
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_local_or_fail_signed
:   lda #')'
    jsr consume_scan_char_local
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_local_or_fail_signed
:   jsr call_skip_inline_spaces_context
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta stored_byte_local
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    ora stored_byte_local
    bne :+
    jmp emit_runtime_real_explicit_value_after_open_local_or_fail_zero
:   lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    tax
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    tay
    txa
    sta stored_byte_local
    lda #ACTC_OVERLAY_CTX_STORE_WORD_LITERAL_FN_LO
    jsr load_context_function_ptr
    lda stored_byte_local
    jsr call_loaded_target_with_a
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_local_or_fail_fail
:   stx real_rhs_index_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_I_TO_F_FN_LO
    jsr call_context_function
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_local_or_fail_fail
:   stx real_lhs_index_local
    jmp emit_runtime_real_wide_bridge_value_local_from_indexes

emit_runtime_real_explicit_value_after_open_local_or_fail_signed:
    jsr call_restore_source_mark_context
    ldy symbol_start_y_local
    jsr call_skip_inline_spaces_context
    lda #'0'
    jsr match_scan_char_local
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_local_or_fail_fail
:   lda #'0'
    jsr consume_scan_char_local
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_local_or_fail_fail
:   jsr call_skip_inline_spaces_context
    lda #'-'
    jsr match_scan_char_local
    bcs emit_runtime_real_explicit_value_after_open_local_or_fail_fail
    lda #'-'
    jsr consume_scan_char_local
    bcs emit_runtime_real_explicit_value_after_open_local_or_fail_fail
    jsr parse_optional_grouped_positive_word_sum_local_or_fail
    bcs emit_runtime_real_explicit_value_after_open_local_or_fail_fail
    jsr call_skip_inline_spaces_context
    lda #')'
    jsr match_scan_char_local
    bcs emit_runtime_real_explicit_value_after_open_local_or_fail_fail
    lda #')'
    jsr consume_scan_char_local
    bcs emit_runtime_real_explicit_value_after_open_local_or_fail_fail
    jsr call_skip_inline_spaces_context
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta stored_byte_local
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    ora stored_byte_local
    bne :+
emit_runtime_real_explicit_value_after_open_local_or_fail_zero:
    lda #ACTC_OVERLAY_CTX_STORE_ZERO_INT_LITERAL_FN_LO
    jsr call_context_function
    bcs emit_runtime_real_explicit_value_after_open_local_or_fail_fail
    stx real_rhs_index_local
    stx real_lhs_index_local
    jmp emit_runtime_real_push_literal_local_from_indexes
:   lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda #$00
    sec
    sbc (ACTC_OVERLAY_WORK_ZP),y
    tax
    iny
    lda #$00
    sbc (ACTC_OVERLAY_WORK_ZP),y
    tay
    txa
    sta stored_byte_local
    lda #ACTC_OVERLAY_CTX_STORE_WORD_LITERAL_FN_LO
    jsr load_context_function_ptr
    lda stored_byte_local
    jsr call_loaded_target_with_a
    bcs emit_runtime_real_explicit_value_after_open_local_or_fail_fail
    stx real_rhs_index_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_S_TO_F_FN_LO
    jsr call_context_function
    bcs emit_runtime_real_explicit_value_after_open_local_or_fail_fail
    stx real_lhs_index_local
    jmp emit_runtime_real_wide_bridge_value_local_from_indexes

emit_runtime_real_explicit_value_after_open_local_or_fail_fail:
    sec
    rts

emit_runtime_real_value_local_or_fail:
    jsr try_consume_real_open_local
    bcs emit_runtime_real_value_local_try_fabs
    jmp emit_runtime_real_explicit_value_after_open_local_or_fail
emit_runtime_real_value_local_try_fabs:
    jsr try_consume_fabs_open_local
    bcs emit_runtime_real_value_local_try_fsqrt
    lda #'a'
    sta real_operator_local
    jmp emit_runtime_real_unary_value_local_or_fail
emit_runtime_real_value_local_try_fsqrt:
    jsr try_consume_fsqrt_open_local
    bcs emit_runtime_real_value_local_try_fsign
    lda #'q'
    sta real_operator_local
    jmp emit_runtime_real_unary_value_local_or_fail
emit_runtime_real_value_local_try_fsign:
    jsr try_consume_fsign_open_local
    bcs emit_runtime_real_value_local_try_binary
    lda #'g'
    sta real_operator_local
    jmp emit_runtime_real_unary_value_local_or_fail
emit_runtime_real_value_local_try_binary:
    jsr emit_runtime_real_binary_value_local_or_fail
    bcs emit_runtime_real_value_local_or_fail_generic
    clc
    rts
emit_runtime_real_value_local_or_fail_generic:
    lda #ACTC_OVERLAY_CTX_EMIT_RUNTIME_REAL_VALUE_FN_LO
    jmp call_context_function

store_runtime_expr_with_a_local_or_fail:
    sta runtime_print_op_local
    ldy #$00
    jsr try_emit_runtime_int_value_local_or_fail
    bcc store_runtime_expr_with_a_local_or_fail_after_value
    lda int_parse_matched_local
    bne store_runtime_expr_with_a_local_or_fail_fail
store_runtime_expr_with_a_local_or_fail_generic:
    lda #ACTC_OVERLAY_CTX_EMIT_RUNTIME_VALUE_FN_LO
    jsr call_context_function
    bcs store_runtime_expr_with_a_local_or_fail_fail
store_runtime_expr_with_a_local_or_fail_after_value:
    jsr call_skip_inline_spaces_context
    lda #')'
    jsr match_scan_char_local
    bcs store_runtime_expr_with_a_local_or_fail_fail
    jsr load_append_body_op_no_arg_ptr
    lda runtime_print_op_local
    jsr call_loaded_target_with_a
    clc
    rts
store_runtime_expr_with_a_local_or_fail_fail:
    sec
    rts

store_runtime_real_print_with_newline_flag_local_or_fail:
    sta runtime_print_op_local
    ldy #$00
    jsr emit_runtime_real_value_local_or_fail
    bcs store_runtime_real_print_with_newline_flag_local_or_fail_fail
    jsr call_skip_inline_spaces_context
    lda #')'
    jsr match_scan_char_local
    bcs store_runtime_real_print_with_newline_flag_local_or_fail_fail
    lda #')'
    jsr consume_scan_char_local
    bcs store_runtime_real_print_with_newline_flag_local_or_fail_fail
    jsr call_skip_inline_spaces_context
    jsr call_require_line_end_context
    bcs store_runtime_real_print_with_newline_flag_local_or_fail_fail
    lda runtime_print_op_local
    beq store_runtime_real_print_with_newline_flag_local_zero
    lda #ACTC_OVERLAY_CTX_STORE_WORD_LITERAL_FN_LO
    jsr load_context_function_ptr
    lda #$01
    ldy #$00
    jsr call_loaded_target_with_a
    bcs store_runtime_real_print_with_newline_flag_local_or_fail_fail
    bcc store_runtime_real_print_with_newline_flag_local_have_flag
store_runtime_real_print_with_newline_flag_local_zero:
    lda #ACTC_OVERLAY_CTX_STORE_ZERO_INT_LITERAL_FN_LO
    jsr call_context_function
    bcs store_runtime_real_print_with_newline_flag_local_or_fail_fail
store_runtime_real_print_with_newline_flag_local_have_flag:
    stx real_lhs_index_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_PRINT_F_FN_LO
    jsr call_context_function
    bcs store_runtime_real_print_with_newline_flag_local_or_fail_fail
    stx real_rhs_index_local
    jsr load_append_body_op_ptr
    ldx real_lhs_index_local
    lda #'p'
    jsr call_loaded_target_with_a
    ldx real_rhs_index_local
    lda #'u'
    jsr call_loaded_target_with_a
    clc
    rts
store_runtime_real_print_with_newline_flag_local_or_fail_fail:
    sec
    rts

condition_starts_with_local_real_value_or_fail:
    ldy #$00
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    jsr call_skip_inline_spaces_context
    jsr call_copy_symbol_from_scan_y_context
    bcs condition_starts_with_local_real_value_or_fail_fail_restore
    lda #<pattern_real_decl
    ldy #>pattern_real_decl
    jsr symbol_buffer_matches_local_const
    bcc condition_starts_with_local_real_value_or_fail_ok_restore
    lda #<pattern_fabs
    ldy #>pattern_fabs
    jsr symbol_buffer_matches_local_const
    bcc condition_starts_with_local_real_value_or_fail_ok_restore
    lda #<pattern_fsqrt
    ldy #>pattern_fsqrt
    jsr symbol_buffer_matches_local_const
    bcc condition_starts_with_local_real_value_or_fail_ok_restore
    lda #<pattern_fsign
    ldy #>pattern_fsign
    jsr symbol_buffer_matches_local_const
    bcc condition_starts_with_local_real_value_or_fail_ok_restore
    lda #<pattern_fmin
    ldy #>pattern_fmin
    jsr symbol_buffer_matches_local_const
    bcc condition_starts_with_local_real_value_or_fail_ok_restore
    lda #<pattern_fmax
    ldy #>pattern_fmax
    jsr symbol_buffer_matches_local_const
    bcc condition_starts_with_local_real_value_or_fail_ok_restore
    jsr call_find_var_index_context
    bcs condition_starts_with_local_real_value_or_fail_fail_restore
    stx real_lhs_index_local
    lda #ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    jsr call_indexed_context_function
    bcs condition_starts_with_local_real_value_or_fail_fail_restore
condition_starts_with_local_real_value_or_fail_ok_restore:
    jsr call_restore_source_mark_context
    ldy #$00
    clc
    rts
condition_starts_with_local_real_value_or_fail_fail_restore:
    jsr call_restore_source_mark_context
    ldy #$00
    sec
    rts

emit_runtime_real_condition_clause_local_or_fail:
    jsr call_skip_inline_spaces_context
    jsr emit_runtime_real_value_local_or_fail
    bcc :+
    jmp emit_runtime_real_condition_clause_local_or_fail_fail
:
    lda #'='
    jsr match_scan_char_local
    bcc emit_runtime_real_condition_clause_local_eq
    lda #'<'
    jsr match_scan_char_local
    bcc emit_runtime_real_condition_clause_local_lt_entry
    lda #'>'
    jsr match_scan_char_local
    bcc emit_runtime_real_condition_clause_local_gt_entry
    sec
    rts
emit_runtime_real_condition_clause_local_eq:
    lda #'q'
    sta runtime_compare_op_local
    lda #$01
    sta runtime_compare_flag_local
    lda #'='
    jsr consume_scan_char_local
    bcc :+
    jmp emit_runtime_real_condition_clause_local_or_fail_fail
:
    jmp emit_runtime_real_condition_clause_local_rhs
emit_runtime_real_condition_clause_local_lt_entry:
    lda #'<'
    jsr consume_scan_char_local
    bcc :+
    jmp emit_runtime_real_condition_clause_local_or_fail_fail
:
    lda #'>'
    jsr match_scan_char_local
    bcc emit_runtime_real_condition_clause_local_ne
    lda #'='
    jsr match_scan_char_local
    bcc emit_runtime_real_condition_clause_local_le
    lda #'l'
    sta runtime_compare_op_local
    lda #$01
    sta runtime_compare_flag_local
    jmp emit_runtime_real_condition_clause_local_rhs
emit_runtime_real_condition_clause_local_gt_entry:
    lda #'>'
    jsr consume_scan_char_local
    bcc :+
    jmp emit_runtime_real_condition_clause_local_or_fail_fail
:
    lda #'='
    jsr match_scan_char_local
    bcc emit_runtime_real_condition_clause_local_ge
    lda #'g'
    sta runtime_compare_op_local
    lda #$01
    sta runtime_compare_flag_local
    jmp emit_runtime_real_condition_clause_local_rhs
emit_runtime_real_condition_clause_local_ne:
    lda #'n'
    sta runtime_compare_op_local
    lda #$01
    sta runtime_compare_flag_local
    lda #'>'
    jsr consume_scan_char_local
    bcc :+
    jmp emit_runtime_real_condition_clause_local_or_fail_fail
:
    jmp emit_runtime_real_condition_clause_local_rhs
emit_runtime_real_condition_clause_local_le:
    lda #'l'
    sta runtime_compare_op_local
    lda #$02
    sta runtime_compare_flag_local
    lda #'='
    jsr consume_scan_char_local
    bcc :+
    jmp emit_runtime_real_condition_clause_local_or_fail_fail
:
    jmp emit_runtime_real_condition_clause_local_rhs
emit_runtime_real_condition_clause_local_ge:
    lda #'g'
    sta runtime_compare_op_local
    lda #$00
    sta runtime_compare_flag_local
    lda #'='
    jsr consume_scan_char_local
    bcc :+
    jmp emit_runtime_real_condition_clause_local_or_fail_fail
:
emit_runtime_real_condition_clause_local_rhs:
    jsr call_skip_inline_spaces_context
    jsr emit_runtime_real_value_local_or_fail
    bcc :+
    jmp emit_runtime_real_condition_clause_local_or_fail_fail
:
    sty symbol_end_y_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_F_CMP_FN_LO
    jsr call_context_function
    bcc :+
    jmp emit_runtime_real_condition_clause_local_or_fail_fail
:
    stx real_rhs_index_local
    jsr load_append_body_op_ptr
    ldx real_rhs_index_local
    lda #'u'
    jsr call_loaded_target_with_a
    lda runtime_compare_flag_local
    beq emit_runtime_real_condition_clause_local_zero_flag
    lda #ACTC_OVERLAY_CTX_STORE_WORD_LITERAL_FN_LO
    jsr load_context_function_ptr
    lda runtime_compare_flag_local
    ldy #$00
    jsr call_loaded_target_with_a
    bcc :+
    jmp emit_runtime_real_condition_clause_local_or_fail_fail
:
    jmp emit_runtime_real_condition_clause_local_have_flag
emit_runtime_real_condition_clause_local_zero_flag:
    lda #ACTC_OVERLAY_CTX_STORE_ZERO_INT_LITERAL_FN_LO
    jsr call_context_function
    bcc :+
    jmp emit_runtime_real_condition_clause_local_or_fail_fail
:
emit_runtime_real_condition_clause_local_have_flag:
    stx real_rhs_index_local
    jsr load_append_body_op_ptr
    ldx real_rhs_index_local
    lda #'p'
    jsr call_loaded_target_with_a
    jsr load_append_body_op_no_arg_ptr
    lda runtime_compare_op_local
    jsr call_loaded_target_with_a
    ldy symbol_end_y_local
    clc
    rts
emit_runtime_real_condition_clause_local_or_fail_fail:
    sec
    rts

store_runtime_condition_with_a_local_or_fail:
    sta runtime_condition_op_local
    ldy #$00
    jsr condition_starts_with_local_real_value_or_fail
    bcs store_runtime_condition_with_a_local_or_fail_generic
    ldy #$00
    jsr emit_runtime_real_condition_clause_local_or_fail
    bcs store_runtime_condition_with_a_local_or_fail_fail
    jmp store_runtime_condition_with_a_local_or_fail_after_value
store_runtime_condition_with_a_local_or_fail_generic:
    ldy #$00
    lda #ACTC_OVERLAY_CTX_EMIT_RUNTIME_VALUE_FN_LO
    jsr call_context_function
    bcs store_runtime_condition_with_a_local_or_fail_fail
store_runtime_condition_with_a_local_or_fail_after_value:
    lda runtime_condition_op_local
    cmp #'h'
    bne :+
    jsr require_then_or_line_end_local
    bcc store_runtime_condition_with_a_local_or_fail_done
    bcs store_runtime_condition_with_a_local_or_fail_fail
:   cmp #'f'
    bne :+
    jsr require_do_or_line_end_local
    bcc store_runtime_condition_with_a_local_or_fail_done
    bcs store_runtime_condition_with_a_local_or_fail_fail
:   jsr call_require_line_end_context
    bcs store_runtime_condition_with_a_local_or_fail_fail
store_runtime_condition_with_a_local_or_fail_done:
    jsr load_append_body_op_no_arg_ptr
    lda runtime_condition_op_local
    jsr call_loaded_target_with_a
    clc
    rts
store_runtime_condition_with_a_local_or_fail_fail:
    sec
    rts

require_then_or_line_end_local:
    jsr call_skip_inline_spaces_context
    jsr match_line_end_local
    bcc require_then_or_line_end_local_ok
    lda #'T'
    jsr consume_uppercase_char_local
    bcs require_then_or_line_end_local_fail
    lda #'H'
    jsr consume_uppercase_char_local
    bcs require_then_or_line_end_local_fail
    lda #'E'
    jsr consume_uppercase_char_local
    bcs require_then_or_line_end_local_fail
    lda #'N'
    jsr consume_uppercase_char_local
    bcs require_then_or_line_end_local_fail
    jsr call_skip_inline_spaces_context
    jsr match_line_end_local
    bcc require_then_or_line_end_local_ok
require_then_or_line_end_local_fail:
    sec
    rts
require_then_or_line_end_local_ok:
    clc
    rts

require_do_or_line_end_local:
    jsr call_skip_inline_spaces_context
    jsr match_line_end_local
    bcc require_do_or_line_end_local_ok
    lda #'D'
    jsr consume_uppercase_char_local
    bcs require_do_or_line_end_local_fail
    lda #'O'
    jsr consume_uppercase_char_local
    bcs require_do_or_line_end_local_fail
    jsr call_skip_inline_spaces_context
    jsr match_line_end_local
    bcc require_do_or_line_end_local_ok
require_do_or_line_end_local_fail:
    sec
    rts
require_do_or_line_end_local_ok:
    clc
    rts

emit_real_small_int_assignment_local_or_fail:
    sty symbol_start_y_local
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr call_context_function
    jsr parse_positive_word_sum_local_or_fail
    bcs emit_real_small_int_assignment_local_or_fail_wide
    jsr call_skip_inline_spaces_context
    jsr call_require_line_end_context
    bcs emit_real_small_int_assignment_local_or_fail_wide
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$01
    lda (ACTC_OVERLAY_WORK_ZP),y
    bne emit_real_small_int_assignment_local_or_fail_wide
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    bne emit_real_small_int_assignment_local_or_fail_nonzero
    lda #ACTC_OVERLAY_CTX_STORE_ZERO_INT_LITERAL_FN_LO
    jsr call_context_function
    bcc :+
    jmp emit_real_small_int_assignment_local_or_fail_fail
:
    stx real_rhs_index_local
    stx real_lhs_index_local
    jmp emit_real_literal_assignment_local_from_indexes
emit_real_small_int_assignment_local_or_fail_nonzero:
    lda #ACTC_OVERLAY_CTX_STORE_ZERO_INT_LITERAL_FN_LO
    jsr call_context_function
    bcc :+
    jmp emit_real_small_int_assignment_local_or_fail_fail
:
    stx real_rhs_index_local
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr pack_a_as_positive_real_high_word_local
    lda #ACTC_OVERLAY_CTX_STORE_WORD_LITERAL_FN_LO
    jsr load_context_function_ptr
    lda stored_byte_local
    jsr call_loaded_target_with_a
    bcc :+
    jmp emit_real_small_int_assignment_local_or_fail_fail
:
    stx real_lhs_index_local
    jmp emit_real_literal_assignment_local_from_indexes

emit_real_small_int_assignment_local_or_fail_wide:
    jsr call_restore_source_mark_context
    ldy symbol_start_y_local
    jsr parse_positive_word_sum_local_or_fail
    bcs emit_real_small_int_assignment_local_or_fail_signed
    jsr call_skip_inline_spaces_context
    jsr call_require_line_end_context
    bcs emit_real_small_int_assignment_local_or_fail_signed
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta stored_byte_local
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    ora stored_byte_local
    bne :+
    jmp emit_real_small_int_assignment_local_or_fail_zero
:
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    tax
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    tay
    txa
    sta stored_byte_local
    lda #ACTC_OVERLAY_CTX_STORE_WORD_LITERAL_FN_LO
    jsr load_context_function_ptr
    lda stored_byte_local
    jsr call_loaded_target_with_a
    bcc :+
    jmp emit_real_small_int_assignment_local_or_fail_fail
:
    stx real_rhs_index_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_I_TO_F_FN_LO
    jsr call_context_function
    bcc :+
    jmp emit_real_small_int_assignment_local_or_fail_fail
:
    stx real_lhs_index_local
    jmp emit_real_wide_bridge_assignment_local_from_indexes

emit_real_small_int_assignment_local_or_fail_signed:
    jsr call_restore_source_mark_context
    ldy symbol_start_y_local
    jsr call_skip_inline_spaces_context
    lda #'0'
    jsr match_scan_char_local
    bcc :+
    jmp emit_real_small_int_assignment_local_or_fail_fail
:
    lda #'0'
    jsr consume_scan_char_local
    bcc :+
    jmp emit_real_small_int_assignment_local_or_fail_fail
:
    jsr call_skip_inline_spaces_context
    lda #'-'
    jsr match_scan_char_local
    bcc :+
    jmp emit_real_small_int_assignment_local_or_fail_fail
:
    lda #'-'
    jsr consume_scan_char_local
    bcc :+
    jmp emit_real_small_int_assignment_local_or_fail_fail
:
    jsr parse_optional_grouped_positive_word_sum_local_or_fail
    bcc :+
    jmp emit_real_small_int_assignment_local_or_fail_fail
:
    jsr call_skip_inline_spaces_context
    jsr call_require_line_end_context
    bcc :+
    jmp emit_real_small_int_assignment_local_or_fail_fail
:
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta stored_byte_local
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    ora stored_byte_local
    bne :+
    jmp emit_real_small_int_assignment_local_or_fail_zero
:
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda #$00
    sec
    sbc (ACTC_OVERLAY_WORK_ZP),y
    tax
    iny
    lda #$00
    sbc (ACTC_OVERLAY_WORK_ZP),y
    tay
    txa
    sta stored_byte_local
    lda #ACTC_OVERLAY_CTX_STORE_WORD_LITERAL_FN_LO
    jsr load_context_function_ptr
    lda stored_byte_local
    jsr call_loaded_target_with_a
    bcs emit_real_small_int_assignment_local_or_fail_fail
    stx real_rhs_index_local
    lda #ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_S_TO_F_FN_LO
    jsr call_context_function
    bcs emit_real_small_int_assignment_local_or_fail_fail
    stx real_lhs_index_local
    jmp emit_real_wide_bridge_assignment_local_from_indexes

emit_real_small_int_assignment_local_or_fail_zero:
    lda #ACTC_OVERLAY_CTX_STORE_ZERO_INT_LITERAL_FN_LO
    jsr call_context_function
    bcs emit_real_small_int_assignment_local_or_fail_fail
    stx real_rhs_index_local
    stx real_lhs_index_local
    jmp emit_real_literal_assignment_local_from_indexes

emit_real_small_int_assignment_local_or_fail_fail:
    sec
    rts

emit_real_literal_assignment_local_from_indexes:
    jsr load_append_body_op_ptr
    ldx real_rhs_index_local
    lda #'p'
    jsr call_loaded_target_with_a
    ldx real_lhs_index_local
    lda #'p'
    jsr call_loaded_target_with_a
    lda #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    lda #'T'
    jsr call_loaded_target_with_a
    lda #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    lda #'S'
    jsr call_loaded_target_with_a
    clc
    rts

emit_real_wide_bridge_assignment_local_from_indexes:
    jsr load_append_body_op_ptr
    ldx real_rhs_index_local
    lda #'p'
    jsr call_loaded_target_with_a
    ldx real_lhs_index_local
    lda #'u'
    jsr call_loaded_target_with_a
    lda #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    lda #'T'
    jsr call_loaded_target_with_a
    lda #ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    jsr load_x_from_context_byte_ptr
    lda #'S'
    jsr call_loaded_target_with_a
    clc
    rts

pack_a_as_positive_real_high_word_local:
    sta stored_byte_local
    ldx #$00
pack_a_as_positive_real_high_word_local_shift_loop:
    lda stored_byte_local
    cmp #$80
    bcs pack_a_as_positive_real_high_word_local_shift_done
    asl stored_byte_local
    inx
    bne pack_a_as_positive_real_high_word_local_shift_loop
pack_a_as_positive_real_high_word_local_shift_done:
    lda stored_byte_local
    sec
    sbc #$80
    sta stored_byte_local
    txa
    eor #$07
    clc
    adc #127
    sta saved_y_local
    and #$01
    beq :+
    lda stored_byte_local
    ora #$80
    sta stored_byte_local
:   lda saved_y_local
    lsr a
    tay
    lda stored_byte_local
    clc
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

source_reader_begin_local_keyword_open:
    sta pattern_ptr_local
    sty pattern_ptr_local+1
    stx saved_x_local
    lda symbol_start_y_local
    sta reader_scan_y_local
    lda #$00
    sta reader_pattern_index_local
    rts

source_reader_local_pattern_char_from_index:
    lda pattern_ptr_local
    sta ACTC_OVERLAY_WORK_ZP
    lda pattern_ptr_local+1
    sta ACTC_OVERLAY_WORK_ZP+1
    ldy reader_pattern_index_local
    lda (ACTC_OVERLAY_WORK_ZP),y
    rts

source_reader_consume_local_pattern_char:
    jsr source_reader_local_pattern_char_from_index
    beq source_reader_consume_local_pattern_char_fail
    sta call_arg_a
    ldy reader_scan_y_local
    lda call_arg_a
    jsr consume_uppercase_char_local
    bcs source_reader_consume_local_pattern_char_fail
    sty reader_scan_y_local
    inc reader_pattern_index_local
    clc
    rts
source_reader_consume_local_pattern_char_fail:
    sec
    rts

symbol_buffer_matches_local_const:
    jsr set_resident_const_ptr_from_ay
    lda #ACTC_OVERLAY_CTX_SYMBOL_BUFFER_MATCHES_CONST_PTR_FN_LO
    jmp call_context_function

consume_keyword_open_local:
    jsr source_reader_begin_local_keyword_open
consume_keyword_open_local_loop:
    jsr source_reader_local_pattern_char_from_index
    beq consume_keyword_open_local_open
    jsr source_reader_consume_local_pattern_char
    bcs consume_keyword_open_local_fail
    jmp consume_keyword_open_local_loop
consume_keyword_open_local_fail:
    ldx saved_x_local
    ldy reader_scan_y_local
    sec
    rts
consume_keyword_open_local_open:
    ldy reader_scan_y_local
    lda #'('
    jsr match_scan_char_local
    bcs consume_keyword_open_local_fail
    lda #'('
    jsr consume_scan_char_local
    bcs consume_keyword_open_local_fail
    jsr call_skip_inline_spaces_context
    ldx saved_x_local
    clc
    rts

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

call_indexed_context_function_keep_x:
    stx saved_x_local
    jsr load_context_function_ptr
    lda #$00
    ldx saved_x_local
    jmp call_loaded_target_with_a

load_append_body_op_ptr:
    lda #ACTC_OVERLAY_CTX_APPEND_BODY_OP_FN_LO
    jmp load_context_function_ptr

load_append_body_op_no_arg_ptr:
    lda #ACTC_OVERLAY_CTX_APPEND_BODY_OP_NO_ARG_FN_LO
    jmp load_context_function_ptr

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



; Shared front-coded builtin lookup data.
.include "actc_overlay_builtin_runtime_table.inc"

pattern_int_decl:
    .asciiz "INT"
pattern_real_decl:
    .asciiz "REAL"
pattern_fabs:
    .asciiz "FABS"
pattern_fsqrt:
    .asciiz "FSQRT"
pattern_fsign:
    .asciiz "FSIGN"
pattern_fmin:
    .asciiz "FMIN"
pattern_fmax:
    .asciiz "FMAX"
pattern_fclamp:
    .asciiz "FCLAMP"
pattern_proc:
    .asciiz "PROC"
pattern_func:
    .asciiz "FUNC"
pattern_asmblock:
    .asciiz "ASMBLOCK"
pattern_exit:
    .asciiz "EXIT"
pattern_for:
    .asciiz "FOR"
pattern_to:
    .asciiz "TO"
pattern_step:
    .asciiz "STEP"
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
    .asciiz "LOAD"
msg_save_fail:
    .asciiz "SAVE"
msg_bad_proc:
    .asciiz "BAD PROC"
msg_bad_var:
    .asciiz "VAR"
msg_bad_literal:
    .asciiz "LIT"
msg_bad_asm:
    .asciiz "ASM"
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
param_bind_count_local:
    .byte $00
param_bind_base_local:
    .byte $00
real_lhs_index_local:
    .byte $00
real_rhs_index_local:
    .byte $00
real_third_index_local:
    .byte $00
real_operator_local:
    .byte $00
real_binary_function_local:
    .byte $00
runtime_print_op_local:
    .byte $00
runtime_condition_op_local:
    .byte $00
runtime_compare_op_local:
    .byte $00
runtime_compare_flag_local:
    .byte $00
int_parse_matched_local:
    .byte $00
reader_scan_y_local:
    .byte $00
reader_pattern_index_local:
    .byte $00
loop_depth_local:
    .byte $00
for_pending_do_local:
    .byte $00
for_counter_local:
    .byte $00
for_direction_local:
    .byte $00
loop_kind_stack_local:
    .res LOOP_MAX

actc_overlay_end:
