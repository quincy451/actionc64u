.include "actc_overlay_abi.inc"

.ifndef ACTC_EMIT_NATIVE_ONLY
ACTC_EMIT_NATIVE_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_LOCAL_ONLY
ACTC_EMIT_NATIVE_LOCAL_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_REAL_ONLY
ACTC_EMIT_NATIVE_REAL_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_REAL_CONTROL_ONLY
ACTC_EMIT_NATIVE_REAL_CONTROL_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_REAL_WHILE_ONLY
ACTC_EMIT_NATIVE_REAL_WHILE_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_RUNTIME_CONDITION_ONLY
ACTC_EMIT_NATIVE_RUNTIME_CONDITION_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ONLY
ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_LOCAL_RUNTIME_ONLY
ACTC_EMIT_NATIVE_LOCAL_RUNTIME_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_LOCAL_MIXED_ONLY
ACTC_EMIT_NATIVE_LOCAL_MIXED_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_FIXED_ONLY
ACTC_EMIT_NATIVE_FIXED_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_REAL_FUNCTION_ONLY
ACTC_EMIT_NATIVE_REAL_FUNCTION_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_REAL_POSTFIX_ONLY
ACTC_EMIT_NATIVE_REAL_POSTFIX_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_REAL_POSTFIX_CONTROL_ONLY
ACTC_EMIT_NATIVE_REAL_POSTFIX_CONTROL_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_REAL_POSTFIX_MULTI_CONTROL_ONLY
ACTC_EMIT_NATIVE_REAL_POSTFIX_MULTI_CONTROL_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_REAL_POSTFIX_EXTENDED_CONTROL_ONLY
ACTC_EMIT_NATIVE_REAL_POSTFIX_EXTENDED_CONTROL_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_REAL_POSTFIX_EARLY_RETURN_ONLY
ACTC_EMIT_NATIVE_REAL_POSTFIX_EARLY_RETURN_ONLY = 0
.endif
.ifndef ACTC_EMIT_NATIVE_REAL_POSTFIX_LOOP_ONLY
ACTC_EMIT_NATIVE_REAL_POSTFIX_LOOP_ONLY = 0
.endif

ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ACTIVE = ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ONLY + ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY

.if ACTC_EMIT_NATIVE_REAL_POSTFIX_LOOP_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_LOOP_OBJECT
.elseif ACTC_EMIT_NATIVE_REAL_POSTFIX_EARLY_RETURN_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_EARLY_RETURN_OBJECT
.elseif ACTC_EMIT_NATIVE_REAL_POSTFIX_EXTENDED_CONTROL_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_EXTENDED_CONTROL_OBJECT
.elseif ACTC_EMIT_NATIVE_REAL_POSTFIX_MULTI_CONTROL_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_MULTI_CONTROL_OBJECT
.elseif ACTC_EMIT_NATIVE_REAL_POSTFIX_CONTROL_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_CONTROL_OBJECT
.elseif ACTC_EMIT_NATIVE_REAL_POSTFIX_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_POSTFIX_OBJECT
.elseif ACTC_EMIT_NATIVE_REAL_FUNCTION_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_FUNCTION_OBJECT
.elseif ACTC_EMIT_NATIVE_FIXED_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_FIXED_OBJECT
.elseif ACTC_EMIT_NATIVE_LOCAL_MIXED_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_LOCAL_MIXED_OBJECT
.elseif ACTC_EMIT_NATIVE_LOCAL_RUNTIME_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_LOCAL_RUNTIME_OBJECT
.elseif ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_RUNTIME_NESTED_OBJECT
.elseif ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_RUNTIME_SEQUENCE_OBJECT
.elseif ACTC_EMIT_NATIVE_RUNTIME_CONDITION_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_RUNTIME_CONDITION_OBJECT
.elseif ACTC_EMIT_NATIVE_REAL_WHILE_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_WHILE_OBJECT
.elseif ACTC_EMIT_NATIVE_REAL_CONTROL_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_CONTROL_OBJECT
.elseif ACTC_EMIT_NATIVE_REAL_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_REAL_OBJECT
.elseif ACTC_EMIT_NATIVE_LOCAL_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_LOCAL_OBJECT
.elseif ACTC_EMIT_NATIVE_ONLY
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_NATIVE_OBJECT
.else
ACTC_EMIT_OVERLAY_PASS = ACTC_OVERLAY_PASS_EMIT_OBJECT
.endif

.export actc_overlay_header
.export actc_overlay_entry
.export actc_overlay_end

.segment "CODE"

actc_overlay_header:
    .byte 'A','C','O','V'
    .byte ACTC_OVERLAY_ABI_VERSION
    .byte ACTC_EMIT_OVERLAY_PASS
    .word ACTC_OVERLAY_EXEC_BASE
    .word actc_overlay_entry
    .word actc_overlay_end - actc_overlay_header
    .word $0000

actc_overlay_entry:
    stx ACTC_OVERLAY_CONTEXT_ZP
    sty ACTC_OVERLAY_CONTEXT_ZP+1
    ldy #ACTC_OVERLAY_CTX_PASS_ID
    lda #ACTC_EMIT_OVERLAY_PASS
    sta (ACTC_OVERLAY_CONTEXT_ZP),y

.if ACTC_EMIT_NATIVE_REAL_POSTFIX_ONLY
    jsr native_real_postfix_detect
    bcs :+
    lda nrp_rejected_call_graph
    bne actc_overlay_fail
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_NOT_APPLICABLE
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    clc
    rts
:
.elseif ACTC_EMIT_NATIVE_REAL_FUNCTION_ONLY
    jsr native_real_function_detect
    bcs :+
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_NOT_APPLICABLE
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    clc
    rts
:
.elseif ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ACTIVE
    jsr native_runtime_sequence_detect
    bcs :+
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_NOT_APPLICABLE
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    clc
    rts
:
.elseif ACTC_EMIT_NATIVE_RUNTIME_CONDITION_ONLY
    jsr native_runtime_condition_detect
    bcs :+
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_NOT_APPLICABLE
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    clc
    rts
:
.elseif ACTC_EMIT_NATIVE_REAL_WHILE_ONLY
    jsr native_real_while_detect
    bcs :+
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_NOT_APPLICABLE
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    clc
    rts
:
.elseif ACTC_EMIT_NATIVE_REAL_CONTROL_ONLY
    jsr native_real_control_detect
    bcs :+
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_NOT_APPLICABLE
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    clc
    rts
:
.elseif ACTC_EMIT_NATIVE_REAL_ONLY
    jsr native_real_detect
    bcs :+
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_NOT_APPLICABLE
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    clc
    rts
:
.elseif ACTC_EMIT_NATIVE_ONLY
    jsr is_main_native_integer_machine_object
    bcs :+
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_NOT_APPLICABLE
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    clc
    rts
:
.endif

    jsr build_object_content_overlay
    bcs actc_overlay_fail

    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_OK
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    clc
    lda #ACTC_OVERLAY_STATUS_OK
    rts

actc_overlay_fail:
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_FAILED
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    sec
    lda #ACTC_OVERLAY_STATUS_FAILED
    rts

build_object_content_overlay:
    jsr emit_object_header
    jsr emit_debug_file_list
    bcs build_object_content_overlay_fail
    jsr emit_debug_proc_decl_list
    bcs build_object_content_overlay_fail
    jsr emit_debug_body_op_list
    bcs build_object_content_overlay_fail
    jsr emit_debug_var_list
    bcs build_object_content_overlay_fail
    jsr emit_export_list
    bcs build_object_content_overlay_fail
    jsr emit_body_ops_list
    bcs build_object_content_overlay_fail
    jsr emit_machine_code_list
    bcs build_object_content_overlay_fail
    jsr emit_external_list
    bcs build_object_content_overlay_fail
    jsr emit_string_list
    bcs build_object_content_overlay_fail
    jsr emit_int_list
    bcs build_object_content_overlay_fail
    jsr emit_var_list
    bcs build_object_content_overlay_fail

    lda #'k'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #ACTC_OVERLAY_CTX_IMPORT_FLAGS_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    and #$0F
    jsr emit_small_decimal
    jsr emit_newline

    lda #'n'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr emit_module_symbol_lower
    jsr emit_newline
    clc
    rts

build_object_content_overlay_fail:
    sec
    rts

emit_object_header:
    lda #'O'
    jsr emit_char_overlay
    lda #'B'
    jsr emit_char_overlay
    lda #'J'
    jsr emit_char_overlay
    lda #'1'
    jsr emit_char_overlay
    jsr emit_newline
    rts

emit_debug_file_list:
    lda #'f'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #'0'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #'s'
    jsr emit_char_overlay
    lda #'r'
    jsr emit_char_overlay
    lda #'c'
    jsr emit_char_overlay
    lda #'/'
    jsr emit_char_overlay
    jsr emit_module_symbol_lower
    lda #'.'
    jsr emit_char_overlay
    lda #'a'
    jsr emit_char_overlay
    lda #'c'
    jsr emit_char_overlay
    lda #'t'
    jsr emit_char_overlay
    jsr emit_newline
    clc
    rts

emit_debug_proc_decl_list:
    lda #$00
    sta entry_index_data
emit_debug_proc_decl_list_loop:
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq emit_debug_proc_decl_list_done
    lda #'q'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda entry_index_data
    jsr emit_small_decimal
    lda #' '
    jsr emit_char_overlay
    lda #'0'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_LOAD_PROC_DEBUG_LINECOL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_PROC_DEBUG_LINECOL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    pha
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    tay
    pla
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda #ACTC_OVERLAY_CTX_PROC_DEBUG_LINECOL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    pha
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    tay
    pla
    jsr emit_word_decimal
    jsr emit_newline
    inc entry_index_data
    jmp emit_debug_proc_decl_list_loop
emit_debug_proc_decl_list_done:
    clc
    rts

emit_debug_body_op_list:
    lda #$00
    sta entry_index_data
emit_debug_body_op_list_proc_loop:
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    bne :+
    jmp emit_debug_body_op_list_done
:
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_BODY_DEBUG_COUNT_PTR_LO
    jsr load_indexed_byte_from_context_ptr
    sta body_debug_count_local
    lda #$00
    sta body_debug_index_data
emit_debug_body_op_list_op_loop:
    lda body_debug_count_local
    cmp body_debug_index_data
    beq emit_debug_body_op_list_next_proc
.if ACTC_EMIT_NATIVE_REAL_POSTFIX_ONLY
    lda #'L'
.elseif ACTC_EMIT_NATIVE_REAL_FUNCTION_ONLY
    lda #'L'
.elseif ACTC_EMIT_NATIVE_ONLY
    lda #'L'
.elseif ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ACTIVE
    lda #'L'
.elseif ACTC_EMIT_NATIVE_RUNTIME_CONDITION_ONLY
    lda #'L'
.elseif ACTC_EMIT_NATIVE_REAL_WHILE_ONLY
    lda #'L'
.elseif ACTC_EMIT_NATIVE_REAL_CONTROL_ONLY
    lda #'L'
.elseif ACTC_EMIT_NATIVE_REAL_ONLY
    lda #'L'
.else
    lda #'l'
.endif
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda entry_index_data
    jsr emit_small_decimal
    lda #' '
    jsr emit_char_overlay
.if ACTC_EMIT_NATIVE_REAL_POSTFIX_ONLY
    jsr native_real_postfix_emit_debug_offset
.elseif ACTC_EMIT_NATIVE_REAL_FUNCTION_ONLY
    jsr native_real_function_emit_debug_offset
.elseif ACTC_EMIT_NATIVE_ONLY
    jsr native_int_load_debug_offset
    jsr emit_word_decimal
.elseif ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ACTIVE
    jsr native_runtime_sequence_emit_debug_offset
.elseif ACTC_EMIT_NATIVE_RUNTIME_CONDITION_ONLY
    jsr native_runtime_condition_emit_debug_offset
.elseif ACTC_EMIT_NATIVE_REAL_WHILE_ONLY
    jsr native_real_while_emit_debug_offset
.elseif ACTC_EMIT_NATIVE_REAL_CONTROL_ONLY
    jsr native_real_control_emit_debug_offset
.elseif ACTC_EMIT_NATIVE_REAL_ONLY
    jsr native_real_emit_debug_offset
.else
    lda body_debug_index_data
    jsr emit_small_decimal
.endif
    lda #' '
    jsr emit_char_overlay
    lda #'0'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx entry_index_data
    ldy body_debug_index_data
    lda #ACTC_OVERLAY_CTX_LOAD_BODY_DEBUG_LINECOL_FN_LO
    jsr call_proc_op_context_function
    lda #ACTC_OVERLAY_CTX_PROC_DEBUG_LINECOL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    pha
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    tay
    pla
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda #ACTC_OVERLAY_CTX_PROC_DEBUG_LINECOL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    pha
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    tay
    pla
    jsr emit_word_decimal
    jsr emit_newline
    inc body_debug_index_data
    jmp emit_debug_body_op_list_op_loop
emit_debug_body_op_list_next_proc:
    inc entry_index_data
    jmp emit_debug_body_op_list_proc_loop
emit_debug_body_op_list_done:
    clc
    rts

emit_debug_var_list:
    ldy #ACTC_OVERLAY_CTX_LOAD_VAR_DEBUG_LINECOL_FN_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta saved_a_local
    ldy #ACTC_OVERLAY_CTX_LOAD_VAR_DEBUG_LINECOL_FN_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    ora saved_a_local
    bne :+
    jmp emit_debug_var_list_done
:
    lda #$00
    sta entry_index_data
emit_debug_global_var_list_loop:
    lda #ACTC_OVERLAY_CTX_MODULE_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq emit_debug_global_var_list_done
    lda #'V'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #'g'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx entry_index_data
    jsr emit_debug_var_type_for_x
    lda entry_index_data
    jsr emit_small_decimal
    lda #' '
    jsr emit_char_overlay
    lda #'0'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_LOAD_VAR_DEBUG_LINECOL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_PROC_DEBUG_LINECOL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    pha
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    tay
    pla
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda #ACTC_OVERLAY_CTX_PROC_DEBUG_LINECOL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    pha
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    tay
    pla
    jsr emit_word_decimal
    jsr emit_newline
    inc entry_index_data
    jmp emit_debug_global_var_list_loop
emit_debug_global_var_list_done:
    lda #$00
    sta entry_index_data
emit_debug_proc_var_list_loop:
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq emit_debug_var_list_done
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_LOAD_PROC_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_PROC_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    and #ACTC_PROC_META_PARAM_COUNT_MASK
    sta body_debug_count_local
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta proc_var_base_local
    lda #'p'
    sta proc_var_scope_local
    jsr emit_debug_proc_var_records_for_current_proc
    lda #ACTC_OVERLAY_CTX_PROC_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta body_debug_count_local
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta proc_var_base_local
    lda #'l'
    sta proc_var_scope_local
    jsr emit_debug_proc_var_records_for_current_proc
    inc entry_index_data
    jmp emit_debug_proc_var_list_loop
emit_debug_var_list_done:
    clc
    rts

emit_debug_proc_var_records_for_current_proc:
    lda body_debug_count_local
    bne :+
    jmp emit_debug_proc_var_records_done
:
    lda #$00
    sta body_debug_index_data
emit_debug_proc_var_records_loop:
    lda body_debug_index_data
    cmp body_debug_count_local
    bne :+
    jmp emit_debug_proc_var_records_done
: 
    lda proc_var_base_local
    clc
    adc body_debug_index_data
    sta proc_var_index_local
    lda #'V'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda proc_var_scope_local
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx proc_var_index_local
    jsr emit_debug_var_type_for_x
    lda entry_index_data
    jsr emit_small_decimal
    lda #' '
    jsr emit_char_overlay
    lda proc_var_index_local
    jsr emit_small_decimal
    lda #' '
    jsr emit_char_overlay
    lda #'0'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx proc_var_index_local
    lda #ACTC_OVERLAY_CTX_LOAD_VAR_DEBUG_LINECOL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_PROC_DEBUG_LINECOL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    pha
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    tay
    pla
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda #ACTC_OVERLAY_CTX_PROC_DEBUG_LINECOL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    pha
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    tay
    pla
    jsr emit_word_decimal
    jsr emit_newline
    inc body_debug_index_data
    jmp emit_debug_proc_var_records_loop
emit_debug_proc_var_records_done:
    clc
    rts

emit_debug_var_type_for_x:
    pha
    txa
    pha
    lda #ACTC_OVERLAY_CTX_LOAD_VAR_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$03
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    pla
    tax
    pla
    rts

emit_export_list:
.if ACTC_EMIT_NATIVE_REAL_POSTFIX_ONLY
    jmp native_real_postfix_emit_export_list
.elseif ACTC_EMIT_NATIVE_REAL_FUNCTION_ONLY
    jmp native_real_function_emit_export_list
.elseif ACTC_EMIT_NATIVE_ONLY
    jmp emit_native_integer_export_list
.elseif ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ACTIVE
    jmp native_runtime_sequence_emit_export_list
.elseif ACTC_EMIT_NATIVE_RUNTIME_CONDITION_ONLY
    jmp native_runtime_condition_emit_export_list
.elseif ACTC_EMIT_NATIVE_REAL_WHILE_ONLY
    jmp native_real_while_emit_export_list
.elseif ACTC_EMIT_NATIVE_REAL_CONTROL_ONLY
    jmp native_real_control_emit_export_list
.elseif ACTC_EMIT_NATIVE_REAL_ONLY
    jmp native_real_emit_export_list
.else
    jsr is_main_local_call_sequence_machine_object
    bcc emit_export_list_not_local_call_sequence
    jmp emit_machine_local_call_sequence_export_list
emit_export_list_not_local_call_sequence:
    jsr is_main_local_external_call_sequence_machine_object
    bcc emit_export_list_not_local_external_call_sequence
    jmp emit_machine_local_external_call_sequence_export_list
emit_export_list_not_local_external_call_sequence:
    jsr is_main_pure_external_call_sequence_machine_object
    bcc emit_export_list_standard
    jmp emit_machine_external_call_sequence_export_list
emit_export_list_standard:
    lda #$00
    sta entry_index_data
emit_export_list_loop:
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq emit_export_list_done
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr emit_lower_scan_zp_string
    lda #' '
    jsr emit_char_overlay
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_LOAD_LAYOUT_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_LAYOUT_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    pha
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    tay
    pla
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda #ACTC_OVERLAY_CTX_LAYOUT_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda entry_index_data
    bne emit_export_list_layout_size
    jsr is_empty_main_machine_object
    bcc emit_export_list_layout_size
    lda #16
    ldy #$00
    jsr emit_word_decimal
    jmp emit_export_list_newline
emit_export_list_layout_size:
    lda #ACTC_OVERLAY_CTX_LAYOUT_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    pha
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    tay
    pla
    jsr emit_word_decimal
emit_export_list_newline:
    jsr emit_newline
    inc entry_index_data
    jmp emit_export_list_loop
emit_export_list_done:
    clc
    rts

emit_machine_external_call_sequence_export_list:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    jsr compute_external_call_sequence_machine_size
    ldx #$00
    ldy #$00
    sty word_value_lo
    sty word_value_hi
    jsr emit_machine_export_line
    clc
    rts

emit_machine_local_external_call_sequence_export_list:
    jsr store_last_local_call_sequence_export_index
    lda proc_var_index_local
    sta entry_index_data
emit_machine_local_external_call_sequence_export_loop:
    lda entry_index_data
    cmp proc_var_index_local
    bne emit_machine_local_external_call_sequence_export_helper
    lda #$00
    tay
    sta word_value_lo
    sta word_value_hi
    jsr compute_local_external_call_sequence_total_size
    ldx entry_index_data
    jsr emit_machine_export_line
    jmp emit_machine_local_external_call_sequence_export_next
emit_machine_local_external_call_sequence_export_helper:
    lda entry_index_data
    sta proc_var_scope_local
    jsr compute_local_external_call_sequence_offset_for_proc_var_scope
    lda proc_var_base_local
    sta word_value_lo
    lda #$00
    sta word_value_hi
    ldx entry_index_data
    jsr compute_local_external_call_sequence_helper_size_for_x
    ldx entry_index_data
    jsr emit_machine_export_line
emit_machine_local_external_call_sequence_export_next:
    lda entry_index_data
    beq emit_machine_local_external_call_sequence_export_done
    dec entry_index_data
    jmp emit_machine_local_external_call_sequence_export_loop
emit_machine_local_external_call_sequence_export_done:
    clc
    rts

emit_machine_local_call_sequence_export_list:
    jsr store_last_local_call_sequence_export_index
    lda proc_var_index_local
    sta entry_index_data
emit_machine_local_call_sequence_export_loop:
    lda entry_index_data
    cmp proc_var_index_local
    bne emit_machine_local_call_sequence_export_helper
    lda #$00
    tay
    sta word_value_lo
    sta word_value_hi
    jsr compute_local_call_sequence_total_size
    ldx entry_index_data
    jsr emit_machine_export_line
    jmp emit_machine_local_call_sequence_export_next
emit_machine_local_call_sequence_export_helper:
    lda entry_index_data
    sta proc_var_scope_local
    jsr compute_local_call_sequence_offset_for_proc_var_scope
    lda proc_var_base_local
    sta word_value_lo
    lda #$00
    sta word_value_hi
    ldx entry_index_data
    jsr compute_local_call_sequence_helper_size_for_x
    ldx entry_index_data
    jsr emit_machine_export_line
emit_machine_local_call_sequence_export_next:
    lda entry_index_data
    beq emit_machine_local_call_sequence_export_done
    dec entry_index_data
    jmp emit_machine_local_call_sequence_export_loop
emit_machine_local_call_sequence_export_done:
    clc
    rts

.endif

.if ACTC_EMIT_NATIVE_ONLY = 0
emit_machine_export_line:
    sta compare_char_local
    stx saved_x_local
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx saved_x_local
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr emit_lower_scan_zp_string
    lda #' '
    jsr emit_char_overlay
    lda word_value_lo
    ldy word_value_hi
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda compare_char_local
    ldy #$00
    jsr emit_word_decimal
    jmp emit_newline
.endif

emit_body_ops_list:
.if ACTC_EMIT_NATIVE_REAL_POSTFIX_ONLY
    jmp native_real_postfix_emit_body_marker_list
.elseif ACTC_EMIT_NATIVE_REAL_FUNCTION_ONLY
    jmp native_real_function_emit_body_marker_list
.elseif ACTC_EMIT_NATIVE_ONLY
    jsr emit_native_integer_body_marker_list
    clc
    rts
.elseif ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ACTIVE
    jmp native_runtime_sequence_emit_body_marker_list
.elseif ACTC_EMIT_NATIVE_RUNTIME_CONDITION_ONLY
    jmp native_runtime_condition_emit_body_marker_list
.elseif ACTC_EMIT_NATIVE_REAL_WHILE_ONLY
    jmp native_real_while_emit_body_marker_list
.elseif ACTC_EMIT_NATIVE_REAL_CONTROL_ONLY
    jmp native_real_control_emit_body_marker_list
.elseif ACTC_EMIT_NATIVE_REAL_ONLY
    jmp native_real_emit_body_marker_list
.else
    jsr is_main_local_call_sequence_machine_object
    bcc emit_body_ops_list_not_local_call_sequence
    jsr emit_machine_local_call_sequence_body_marker_list
    clc
    rts
emit_body_ops_list_not_local_call_sequence:
    jsr is_main_local_external_call_sequence_machine_object
    bcc emit_body_ops_list_not_local_external_call_sequence
    jsr emit_machine_local_external_call_sequence_body_marker_list
    clc
    rts
emit_body_ops_list_not_local_external_call_sequence:
    jsr is_main_pure_external_call_sequence_machine_object
    bcc emit_body_ops_list_standard
    jsr emit_machine_external_call_sequence_body_marker_line
    clc
    rts
emit_body_ops_list_standard:
    lda #$00
    sta entry_index_data
emit_body_ops_list_loop:
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq emit_body_ops_list_done
    lda #'b'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda entry_index_data
    bne emit_body_ops_list_portable
    jsr is_empty_main_machine_object
    bcc emit_body_ops_list_portable
    lda #'M'
    jsr emit_char_overlay
    jsr emit_newline
    inc entry_index_data
    jmp emit_body_ops_list_loop
emit_body_ops_list_portable:
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    ldy #$00
emit_body_ops_list_body_loop:
    jsr emit_object_peek_payload_y
    beq emit_body_ops_list_ret
    jsr emit_char_overlay
    iny
    bne emit_body_ops_list_body_loop
emit_body_ops_list_ret:
    cpy #$00
    beq emit_body_ops_list_emit_ret
    dey
    jsr emit_object_peek_payload_y
    cmp #'r'
    beq emit_body_ops_list_newline
emit_body_ops_list_emit_ret:
    lda #'r'
    jsr emit_char_overlay
emit_body_ops_list_newline:
    jsr emit_newline
    inc entry_index_data
    jmp emit_body_ops_list_loop
emit_body_ops_list_done:
    clc
    rts
.endif

emit_machine_code_list:
.if ACTC_EMIT_NATIVE_REAL_POSTFIX_ONLY
    jmp native_real_postfix_emit_machine_code_list
.elseif ACTC_EMIT_NATIVE_REAL_FUNCTION_ONLY
    jmp native_real_function_emit_machine_code_list
.elseif ACTC_EMIT_NATIVE_ONLY
    jsr emit_native_integer_machine_code_list
    jmp emit_machine_code_list_done
.elseif ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ACTIVE
    jmp native_runtime_sequence_emit_machine_code_list
.elseif ACTC_EMIT_NATIVE_RUNTIME_CONDITION_ONLY
    jmp native_runtime_condition_emit_machine_code_list
.elseif ACTC_EMIT_NATIVE_REAL_WHILE_ONLY
    jmp native_real_while_emit_machine_code_list
.elseif ACTC_EMIT_NATIVE_REAL_CONTROL_ONLY
    jmp native_real_control_emit_machine_code_list
.elseif ACTC_EMIT_NATIVE_REAL_ONLY
    jmp native_real_emit_machine_code_list
.else
    jsr is_empty_main_machine_object
    bcc emit_machine_code_list_check_local_call
    lda #<empty_main_machine_record
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>empty_main_machine_record
    sta ACTC_OVERLAY_SCAN_ZP+1
    jsr emit_scan_zp_string
    jsr emit_newline
    jmp emit_machine_code_list_done
emit_machine_code_list_check_local_call:
    jsr is_main_local_call_sequence_machine_object
    bcc emit_machine_code_list_check_local_external_call
    jsr emit_machine_local_call_sequence_code_list
    jmp emit_machine_code_list_done
emit_machine_code_list_check_local_external_call:
    jsr is_main_local_external_call_sequence_machine_object
    bcc emit_machine_code_list_check_external_call_sequence
    jsr emit_machine_local_external_call_sequence_code_list
    jmp emit_machine_code_list_done
emit_machine_code_list_check_external_call_sequence:
    jsr is_main_pure_external_call_sequence_machine_object
    bcc emit_machine_code_list_done
    jsr emit_machine_external_call_sequence_code_list
    jmp emit_machine_code_list_done
.endif
emit_machine_code_list_done:
    clc
    rts

.if (ACTC_EMIT_NATIVE_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_CONTROL_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_WHILE_ONLY = 0) .and (ACTC_EMIT_NATIVE_RUNTIME_CONDITION_ONLY = 0) .and (ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ACTIVE = 0) .and (ACTC_EMIT_NATIVE_REAL_FUNCTION_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_POSTFIX_ONLY = 0)
emit_machine_external_call_sequence_code_list:
    lda #'m'
    jsr emit_char_overlay
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #$00
    sta body_debug_index_data
emit_machine_external_call_sequence_code_loop:
    ldy body_debug_index_data
    jsr emit_object_peek_payload_y
    cmp #'r'
    beq emit_machine_external_call_sequence_code_epilogue
    cmp #'u'
    bne emit_machine_external_call_sequence_code_done
    lda body_debug_index_data
    pha
    inc body_debug_index_data
    ldy body_debug_index_data
    jsr emit_object_peek_payload_y
    sta proc_var_index_local
    pla
    beq emit_machine_external_call_sequence_code_emit_jsr
    jsr emit_machine_external_call_sequence_maybe_word_setup
emit_machine_external_call_sequence_code_emit_jsr:
    jsr emit_machine_external_jsr_placeholder_bytes
    inc body_debug_index_data
    jmp emit_machine_external_call_sequence_code_loop
emit_machine_external_call_sequence_code_epilogue:
    lda #<external_call_sequence_epilogue_bytes
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>external_call_sequence_epilogue_bytes
    sta ACTC_OVERLAY_SCAN_ZP+1
    jsr emit_scan_zp_string
    jsr emit_newline
    jsr emit_machine_external_call_sequence_reloc_list
emit_machine_external_call_sequence_code_done:
    clc
    rts

emit_machine_external_jsr_placeholder_bytes:
    lda #' '
    jsr emit_char_overlay
    lda #'2'
    jsr emit_char_overlay
    lda #'0'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #'0'
    jsr emit_char_overlay
    lda #'0'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #'0'
    jsr emit_char_overlay
    lda #'0'
    jmp emit_char_overlay

emit_machine_external_call_sequence_reloc_list:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #$00
    sta body_debug_index_data
    lda #$01
    sta proc_var_base_local
    lda #$00
    sta proc_var_scope_local
emit_machine_external_call_sequence_reloc_loop:
    ldy body_debug_index_data
    jsr emit_object_peek_payload_y
    cmp #'r'
    beq emit_machine_external_call_sequence_reloc_done
    cmp #'u'
    bne emit_machine_external_call_sequence_reloc_done
    inc body_debug_index_data
    ldy body_debug_index_data
    jsr emit_object_peek_payload_y
    sta proc_var_index_local
    lda body_debug_index_data
    cmp #$01
    beq emit_machine_external_call_sequence_reloc_write
    jsr emit_machine_external_call_sequence_maybe_word_reloc_advance
emit_machine_external_call_sequence_reloc_write:
    lda #'r'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda proc_var_base_local
    ldy proc_var_scope_local
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda #'u'
    jsr emit_char_overlay
    lda proc_var_index_local
    jsr emit_char_overlay
    jsr emit_newline
    jsr emit_advance_external_reloc_body_offset_by_three
    inc body_debug_index_data
    jmp emit_machine_external_call_sequence_reloc_loop
emit_machine_external_call_sequence_reloc_done:
    rts

compute_external_call_sequence_machine_size:
    lda #16
    sta word_value_lo
    lda #$00
    sta body_debug_index_data
compute_external_call_sequence_machine_size_loop:
    ldy body_debug_index_data
    jsr emit_object_peek_payload_y
    cmp #'u'
    bne compute_external_call_sequence_machine_size_done
    lda body_debug_index_data
    pha
    inc body_debug_index_data
    ldy body_debug_index_data
    jsr emit_object_peek_payload_y
    sta proc_var_index_local
    pla
    beq compute_external_call_sequence_machine_size_after_setup
    jsr emit_external_call_sequence_current_is_sid_cutoff
    bcc compute_external_call_sequence_machine_size_after_setup
    clc
    lda word_value_lo
    adc #$03
    sta word_value_lo
compute_external_call_sequence_machine_size_after_setup:
    clc
    lda word_value_lo
    adc #$03
    sta word_value_lo
    inc body_debug_index_data
    jmp compute_external_call_sequence_machine_size_loop
compute_external_call_sequence_machine_size_done:
    lda word_value_lo
    rts

emit_machine_external_call_sequence_maybe_word_setup:
    jsr emit_external_call_sequence_current_is_sid_cutoff
    bcc emit_machine_external_call_sequence_maybe_word_setup_done
    lda #<a_to_xy_word_setup_bytes
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>a_to_xy_word_setup_bytes
    sta ACTC_OVERLAY_SCAN_ZP+1
    jsr emit_scan_zp_string
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
emit_machine_external_call_sequence_maybe_word_setup_done:
    rts

emit_machine_external_call_sequence_maybe_word_reloc_advance:
    jsr emit_external_call_sequence_current_is_sid_cutoff
    bcc emit_machine_external_call_sequence_maybe_word_reloc_advance_done
    jsr emit_advance_external_reloc_body_offset_by_three
emit_machine_external_call_sequence_maybe_word_reloc_advance_done:
    rts

emit_advance_external_reloc_body_offset_by_three:
    clc
    lda proc_var_base_local
    adc #$03
    sta proc_var_base_local
    bcc :+
    inc proc_var_scope_local
:
    rts

emit_external_call_sequence_current_is_sid_cutoff:
    lda #$00
    sta compare_char_local
    lda proc_var_index_local
    jsr external_import_selector_to_index
    bcc emit_external_call_sequence_current_is_sid_cutoff_restore_body
    tax
    lda #ACTC_OVERLAY_CTX_SET_EXTERNAL_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    lda #<runtime_symbol_rt_sid_cutoff_emit
    sta ACTC_OVERLAY_WORK_ZP
    lda #>runtime_symbol_rt_sid_cutoff_emit
    sta ACTC_OVERLAY_WORK_ZP+1
    ldy #$00
emit_external_call_sequence_current_is_sid_cutoff_loop:
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp (ACTC_OVERLAY_SCAN_ZP),y
    bne emit_external_call_sequence_current_is_sid_cutoff_restore_body
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq emit_external_call_sequence_current_is_sid_cutoff_yes
    iny
    bne emit_external_call_sequence_current_is_sid_cutoff_loop
emit_external_call_sequence_current_is_sid_cutoff_yes:
    lda #$01
    sta compare_char_local
emit_external_call_sequence_current_is_sid_cutoff_restore_body:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda compare_char_local
    beq emit_external_call_sequence_current_is_sid_cutoff_no
    sec
    rts
emit_external_call_sequence_current_is_sid_cutoff_no:
    clc
    rts

emit_machine_local_external_call_sequence_code_list:
    jsr store_last_local_call_sequence_export_index
    lda #'m'
    jsr emit_char_overlay
    lda proc_var_index_local
    sta entry_index_data
emit_machine_local_external_call_sequence_code_export_loop:
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #$00
    sta body_debug_index_data
    jsr emit_machine_local_external_call_sequence_body_jsrs
    lda entry_index_data
    cmp proc_var_index_local
    bne emit_machine_local_external_call_sequence_code_helper_return
    lda #<external_call_sequence_epilogue_bytes
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>external_call_sequence_epilogue_bytes
    sta ACTC_OVERLAY_SCAN_ZP+1
    jsr emit_scan_zp_string
    jmp emit_machine_local_external_call_sequence_code_next
emit_machine_local_external_call_sequence_code_helper_return:
    lda #' '
    jsr emit_char_overlay
    lda #'6'
    jsr emit_char_overlay
    lda #'0'
    jsr emit_char_overlay
emit_machine_local_external_call_sequence_code_next:
    lda entry_index_data
    beq emit_machine_local_external_call_sequence_code_done
    dec entry_index_data
    jmp emit_machine_local_external_call_sequence_code_export_loop
emit_machine_local_external_call_sequence_code_done:
    jsr emit_newline
    jsr emit_machine_local_external_call_sequence_reloc_list
    clc
    rts

emit_machine_local_external_call_sequence_body_jsrs:
    ldy body_debug_index_data
    jsr emit_object_peek_payload_y
    cmp #'c'
    beq emit_machine_local_external_call_sequence_body_jsrs_local
    cmp #'u'
    beq emit_machine_local_external_call_sequence_body_jsrs_external
    rts
emit_machine_local_external_call_sequence_body_jsrs_local:
    inc body_debug_index_data
    ldy body_debug_index_data
    jsr emit_object_peek_payload_y
    sec
    sbc #'0'
    sta proc_var_scope_local
    jsr compute_local_external_call_sequence_offset_for_proc_var_scope
    jsr emit_machine_local_jsr_to_proc_var_base
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    inc body_debug_index_data
    jmp emit_machine_local_external_call_sequence_body_jsrs
emit_machine_local_external_call_sequence_body_jsrs_external:
    jsr emit_machine_external_jsr_placeholder_bytes
    inc body_debug_index_data
    inc body_debug_index_data
    jmp emit_machine_local_external_call_sequence_body_jsrs

emit_machine_local_jsr_to_proc_var_base:
    lda #' '
    jsr emit_char_overlay
    lda #'2'
    jsr emit_char_overlay
    lda #'0'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda proc_var_base_local
    jsr emit_hex_byte_overlay
    lda #' '
    jsr emit_char_overlay
    lda #'1'
    jsr emit_char_overlay
    lda #'0'
    jmp emit_char_overlay

emit_machine_local_external_call_sequence_reloc_list:
    jsr store_last_local_call_sequence_export_index
    lda #$00
    sta proc_var_base_local
    sta proc_var_scope_local
    lda proc_var_index_local
    sta entry_index_data
emit_machine_local_external_call_sequence_reloc_export_loop:
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #$00
    sta body_debug_index_data
    jsr emit_machine_local_external_call_sequence_relocs_for_body
    lda entry_index_data
    cmp proc_var_index_local
    bne emit_machine_local_external_call_sequence_reloc_helper_size
    jsr compute_local_external_call_sequence_main_code_size
    jmp emit_machine_local_external_call_sequence_reloc_after_size
emit_machine_local_external_call_sequence_reloc_helper_size:
    ldx entry_index_data
    jsr compute_local_external_call_sequence_helper_size_for_x
emit_machine_local_external_call_sequence_reloc_after_size:
    clc
    adc proc_var_base_local
    sta proc_var_base_local
    bcc :+
    inc proc_var_scope_local
:
    lda entry_index_data
    beq emit_machine_local_external_call_sequence_reloc_done
    dec entry_index_data
    jmp emit_machine_local_external_call_sequence_reloc_export_loop
emit_machine_local_external_call_sequence_reloc_done:
    rts

emit_machine_local_external_call_sequence_relocs_for_body:
    lda #$00
    sta body_debug_count_local
emit_machine_local_external_call_sequence_relocs_for_body_loop:
    ldy body_debug_index_data
    jsr emit_object_peek_payload_y
    cmp #'c'
    beq emit_machine_local_external_call_sequence_reloc_local
    cmp #'u'
    beq emit_machine_local_external_call_sequence_reloc_external
    cmp #'r'
    beq emit_machine_local_external_call_sequence_reloc_body_done
    rts
emit_machine_local_external_call_sequence_reloc_local:
    inc body_debug_index_data
    inc body_debug_index_data
    jsr advance_local_external_reloc_body_offset_by_three
    jmp emit_machine_local_external_call_sequence_relocs_for_body_loop
emit_machine_local_external_call_sequence_reloc_external:
    inc body_debug_index_data
    ldy body_debug_index_data
    jsr emit_object_peek_payload_y
    sta compare_char_local
    lda #'r'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldy proc_var_scope_local
    lda proc_var_base_local
    clc
    adc body_debug_count_local
    bcc :+
    iny
:
    clc
    adc #$01
    bcc :+
    iny
:
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda #'u'
    jsr emit_char_overlay
    lda compare_char_local
    jsr emit_char_overlay
    jsr emit_newline
    inc body_debug_index_data
    jsr advance_local_external_reloc_body_offset_by_three
    jmp emit_machine_local_external_call_sequence_relocs_for_body_loop
emit_machine_local_external_call_sequence_reloc_body_done:
    rts

advance_local_external_reloc_body_offset_by_three:
    clc
    lda body_debug_count_local
    adc #$03
    sta body_debug_count_local
    rts

emit_machine_local_call_sequence_code_list:
    jsr store_last_local_call_sequence_export_index
    lda #'m'
    jsr emit_char_overlay
    lda proc_var_index_local
    sta entry_index_data
emit_machine_local_call_sequence_code_export_loop:
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #$00
    sta body_debug_index_data
    jsr emit_machine_local_call_sequence_body_jsrs
    lda entry_index_data
    cmp proc_var_index_local
    bne emit_machine_local_call_sequence_code_helper_return
    lda #<external_call_sequence_epilogue_bytes
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>external_call_sequence_epilogue_bytes
    sta ACTC_OVERLAY_SCAN_ZP+1
    jsr emit_scan_zp_string
    jmp emit_machine_local_call_sequence_code_next
emit_machine_local_call_sequence_code_helper_return:
    lda #' '
    jsr emit_char_overlay
    lda #'6'
    jsr emit_char_overlay
    lda #'0'
    jsr emit_char_overlay
emit_machine_local_call_sequence_code_next:
    lda entry_index_data
    beq emit_machine_local_call_sequence_code_done
    dec entry_index_data
    jmp emit_machine_local_call_sequence_code_export_loop
emit_machine_local_call_sequence_code_done:
    jsr emit_newline
    clc
    rts

emit_machine_local_call_sequence_body_jsrs:
    ldy body_debug_index_data
    jsr emit_object_peek_payload_y
    cmp #'c'
    bne emit_machine_local_call_sequence_body_jsrs_done
    inc body_debug_index_data
    ldy body_debug_index_data
    jsr emit_object_peek_payload_y
    sec
    sbc #'0'
    sta proc_var_scope_local
    jsr compute_local_call_sequence_offset_for_proc_var_scope
    jsr emit_machine_local_jsr_to_proc_var_base
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    inc body_debug_index_data
    jmp emit_machine_local_call_sequence_body_jsrs
emit_machine_local_call_sequence_body_jsrs_done:
    rts

emit_machine_local_call_sequence_body_marker_list:
    lda #$00
    sta entry_index_data
emit_machine_local_call_sequence_body_marker_loop:
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq emit_machine_local_call_sequence_body_marker_done
    jsr emit_machine_body_marker_line
    inc entry_index_data
    jmp emit_machine_local_call_sequence_body_marker_loop
emit_machine_local_call_sequence_body_marker_done:
    rts

store_last_local_call_sequence_export_index:
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    sec
    sbc #$01
    sta proc_var_index_local
    rts

compute_local_call_sequence_total_size:
    jsr compute_local_call_sequence_main_code_size
    sta proc_var_base_local
    lda proc_var_index_local
    beq compute_local_call_sequence_total_size_done
    sec
    sbc #$01
    sta compare_char_local
compute_local_call_sequence_total_size_loop:
    ldx compare_char_local
    jsr compute_local_call_sequence_helper_size_for_x
    clc
    adc proc_var_base_local
    sta proc_var_base_local
    lda compare_char_local
    beq compute_local_call_sequence_total_size_done
    dec compare_char_local
    jmp compute_local_call_sequence_total_size_loop
compute_local_call_sequence_total_size_done:
    lda proc_var_base_local
    rts

compute_local_call_sequence_main_code_size:
    ldx proc_var_index_local
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    jsr emit_count_local_call_sequence_body
    lda #16
    jmp add_three_times_body_debug_count

compute_local_call_sequence_helper_size_for_x:
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    jsr emit_count_local_call_sequence_body
    lda #$01
    jmp add_three_times_body_debug_count

add_three_times_body_debug_count:
    ldx body_debug_count_local
add_three_times_body_debug_count_loop:
    cpx #$00
    beq add_three_times_body_debug_count_done
    clc
    adc #$03
    dex
    jmp add_three_times_body_debug_count_loop
add_three_times_body_debug_count_done:
    rts

compute_local_call_sequence_offset_for_proc_var_scope:
    lda proc_var_scope_local
    cmp proc_var_index_local
    bne compute_local_call_sequence_offset_for_helper
    lda #$00
    sta proc_var_base_local
    rts
compute_local_call_sequence_offset_for_helper:
    jsr compute_local_call_sequence_main_code_size
    sta proc_var_base_local
    lda proc_var_index_local
    sec
    sbc #$01
    sta compare_char_local
compute_local_call_sequence_offset_for_helper_loop:
    lda compare_char_local
    cmp proc_var_scope_local
    beq compute_local_call_sequence_offset_for_helper_done
    ldx compare_char_local
    jsr compute_local_call_sequence_helper_size_for_x
    clc
    adc proc_var_base_local
    sta proc_var_base_local
    dec compare_char_local
    jmp compute_local_call_sequence_offset_for_helper_loop
compute_local_call_sequence_offset_for_helper_done:
    rts

compute_local_external_call_sequence_total_size:
    jsr compute_local_external_call_sequence_main_code_size
    sta proc_var_base_local
    lda proc_var_index_local
    beq compute_local_external_call_sequence_total_size_done
    sec
    sbc #$01
    sta compare_char_local
compute_local_external_call_sequence_total_size_loop:
    ldx compare_char_local
    jsr compute_local_external_call_sequence_helper_size_for_x
    clc
    adc proc_var_base_local
    sta proc_var_base_local
    lda compare_char_local
    beq compute_local_external_call_sequence_total_size_done
    dec compare_char_local
    jmp compute_local_external_call_sequence_total_size_loop
compute_local_external_call_sequence_total_size_done:
    lda proc_var_base_local
    rts

compute_local_external_call_sequence_main_code_size:
    ldx proc_var_index_local
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    jsr emit_count_local_external_call_sequence_body
    lda #16
    jmp add_three_times_body_debug_count

compute_local_external_call_sequence_helper_size_for_x:
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    jsr emit_count_local_external_call_sequence_body
    lda #$01
    jmp add_three_times_body_debug_count

compute_local_external_call_sequence_offset_for_proc_var_scope:
    lda proc_var_scope_local
    cmp proc_var_index_local
    bne compute_local_external_call_sequence_offset_for_helper
    lda #$00
    sta proc_var_base_local
    rts
compute_local_external_call_sequence_offset_for_helper:
    jsr compute_local_external_call_sequence_main_code_size
    sta proc_var_base_local
    lda proc_var_index_local
    sec
    sbc #$01
    sta compare_char_local
compute_local_external_call_sequence_offset_for_helper_loop:
    lda compare_char_local
    cmp proc_var_scope_local
    beq compute_local_external_call_sequence_offset_for_helper_done
    ldx compare_char_local
    jsr compute_local_external_call_sequence_helper_size_for_x
    clc
    adc proc_var_base_local
    sta proc_var_base_local
    dec compare_char_local
    jmp compute_local_external_call_sequence_offset_for_helper_loop
compute_local_external_call_sequence_offset_for_helper_done:
    rts

emit_machine_local_external_call_sequence_body_marker_list:
    jsr store_last_local_call_sequence_export_index
    jsr emit_machine_local_external_call_sequence_flat_body_marker_line
    lda proc_var_index_local
    beq emit_machine_local_external_call_sequence_body_marker_done
    sec
    sbc #$01
    sta entry_index_data
emit_machine_local_external_call_sequence_body_marker_loop:
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    jsr emit_machine_local_external_call_sequence_body_marker_line
    lda entry_index_data
    beq emit_machine_local_external_call_sequence_body_marker_done
    dec entry_index_data
    jmp emit_machine_local_external_call_sequence_body_marker_loop
emit_machine_local_external_call_sequence_body_marker_done:
    rts

emit_machine_local_external_call_sequence_flat_body_marker_line:
    lda #'b'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda proc_var_index_local
    sta entry_index_data
emit_machine_local_external_call_sequence_flat_body_marker_loop:
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    jsr emit_machine_local_external_call_sequence_body_marker_refs
    lda entry_index_data
    bne emit_machine_local_external_call_sequence_flat_body_marker_continue
    jmp emit_machine_local_external_call_sequence_body_marker_machine
emit_machine_local_external_call_sequence_flat_body_marker_continue:
    dec entry_index_data
    jmp emit_machine_local_external_call_sequence_flat_body_marker_loop

emit_machine_local_external_call_sequence_body_marker_line:
    lda #'b'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #$00
    sta body_marker_visit_mask
    ldx entry_index_data
    jsr emit_machine_local_external_call_sequence_body_marker_closure_refs_for_x
    jmp emit_machine_local_external_call_sequence_body_marker_machine

emit_machine_local_external_call_sequence_body_marker_closure_refs_for_x:
    stx saved_x_local
    jsr emit_machine_local_external_call_sequence_body_marker_index_mask
    and body_marker_visit_mask
    beq emit_machine_local_external_call_sequence_body_marker_closure_refs_new
    rts
emit_machine_local_external_call_sequence_body_marker_closure_refs_new:
    jsr emit_machine_local_external_call_sequence_body_marker_index_mask
    ora body_marker_visit_mask
    sta body_marker_visit_mask
    ldx saved_x_local
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    jsr emit_machine_local_external_call_sequence_body_marker_refs
    ldy #$00
emit_machine_local_external_call_sequence_body_marker_closure_refs_loop:
    jsr emit_object_peek_payload_y
    cmp #'c'
    beq emit_machine_local_external_call_sequence_body_marker_closure_refs_local
    cmp #'u'
    beq emit_machine_local_external_call_sequence_body_marker_closure_refs_skip_external
    rts
emit_machine_local_external_call_sequence_body_marker_closure_refs_local:
    iny
    jsr emit_object_peek_payload_y
    sec
    sbc #'0'
    sta proc_var_scope_local
    iny
    tya
    pha
    lda ACTC_OVERLAY_SCAN_ZP
    pha
    lda ACTC_OVERLAY_SCAN_ZP+1
    pha
    ldx proc_var_scope_local
    jsr emit_machine_local_external_call_sequence_body_marker_closure_refs_for_x
    pla
    sta ACTC_OVERLAY_SCAN_ZP+1
    pla
    sta ACTC_OVERLAY_SCAN_ZP
    pla
    tay
    jmp emit_machine_local_external_call_sequence_body_marker_closure_refs_loop
emit_machine_local_external_call_sequence_body_marker_closure_refs_skip_external:
    iny
    iny
    jmp emit_machine_local_external_call_sequence_body_marker_closure_refs_loop

emit_machine_local_external_call_sequence_body_marker_index_mask:
    lda #$01
    ldx saved_x_local
    beq emit_machine_local_external_call_sequence_body_marker_index_mask_done
emit_machine_local_external_call_sequence_body_marker_index_mask_loop:
    asl a
    dex
    bne emit_machine_local_external_call_sequence_body_marker_index_mask_loop
emit_machine_local_external_call_sequence_body_marker_index_mask_done:
    rts

emit_machine_local_external_call_sequence_body_marker_refs:
    ldy #$00
emit_machine_local_external_call_sequence_body_marker_line_loop:
    jsr emit_object_peek_payload_y
    cmp #'c'
    beq emit_machine_local_external_call_sequence_body_marker_line_local
    cmp #'u'
    beq emit_machine_local_external_call_sequence_body_marker_line_external
    jmp emit_machine_local_external_call_sequence_body_marker_line_machine
emit_machine_local_external_call_sequence_body_marker_line_local:
    iny
    iny
    jmp emit_machine_local_external_call_sequence_body_marker_line_loop
emit_machine_local_external_call_sequence_body_marker_line_external:
    lda #'u'
    jsr emit_char_overlay
    iny
    jsr emit_object_peek_payload_y
    jsr emit_char_overlay
    iny
    jmp emit_machine_local_external_call_sequence_body_marker_line_loop
emit_machine_local_external_call_sequence_body_marker_line_machine:
    rts

emit_machine_local_external_call_sequence_body_marker_machine:
    lda #'M'
    jsr emit_char_overlay
    jsr emit_newline
    rts
.endif

emit_external_list:
    lda #$00
    sta entry_index_data
emit_external_list_loop:
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq emit_external_list_done
    lda #'u'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_EXTERNAL_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr emit_lower_scan_zp_string
    jsr emit_newline
    inc entry_index_data
    jmp emit_external_list_loop
emit_external_list_done:
    clc
    rts

emit_string_list:
    lda #$00
    sta entry_index_data
emit_string_list_loop:
    lda #ACTC_OVERLAY_CTX_STRING_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq emit_string_list_done
    lda #'s'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_STRING_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    jsr emit_scan_zp_string
    jsr emit_newline
    inc entry_index_data
    jmp emit_string_list_loop
emit_string_list_done:
    clc
    rts

emit_int_list:
    lda #$00
    sta entry_index_data
emit_int_list_loop:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq emit_int_list_done
    lda #'i'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    pha
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    tay
    pla
    jsr emit_word_decimal
    jsr emit_newline
    inc entry_index_data
    jmp emit_int_list_loop
emit_int_list_done:
    clc
    rts

emit_var_list:
    lda #$00
    sta entry_index_data
emit_var_list_loop:
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq emit_var_list_done
    lda #'v'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_VAR_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr emit_lower_scan_zp_string
    lda #' '
    jsr emit_char_overlay
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_LOAD_VAR_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    pha
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    tay
    pla
    jsr emit_word_decimal
    lda #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp #$02
    beq emit_var_list_newline
    pha
    lda #' '
    jsr emit_char_overlay
    pla
    jsr emit_small_decimal
emit_var_list_newline:
    jsr emit_newline
    inc entry_index_data
    jmp emit_var_list_loop
emit_var_list_done:
    clc
    rts

emit_module_symbol_lower:
    lda #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    jsr load_context_ptr_to_scan_zp
    jmp emit_lower_scan_zp_string

emit_scan_zp_string:
    ldy #$00
emit_scan_zp_string_loop:
    jsr emit_object_peek_payload_y
    beq emit_scan_zp_string_done
    jsr emit_char_overlay
    iny
    bne emit_scan_zp_string_loop
emit_scan_zp_string_done:
    rts

emit_lower_scan_zp_string:
    ldy #$00
emit_lower_scan_zp_string_loop:
    jsr emit_object_peek_payload_y
    beq emit_lower_scan_zp_string_done
    jsr lowercase_ascii_overlay
    jsr emit_char_overlay
    iny
    bne emit_lower_scan_zp_string_loop
emit_lower_scan_zp_string_done:
    rts

.if (ACTC_EMIT_NATIVE_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_CONTROL_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_WHILE_ONLY = 0) .and (ACTC_EMIT_NATIVE_RUNTIME_CONDITION_ONLY = 0) .and (ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ACTIVE = 0) .and (ACTC_EMIT_NATIVE_REAL_FUNCTION_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_POSTFIX_ONLY = 0)
is_empty_main_machine_object:
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$01
    bne is_empty_main_machine_object_no
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_empty_main_machine_object_no
    lda #ACTC_OVERLAY_CTX_STRING_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_empty_main_machine_object_no
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_empty_main_machine_object_no
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_empty_main_machine_object_no
    lda #ACTC_OVERLAY_CTX_MODULE_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_empty_main_machine_object_no
    lda #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    jsr load_context_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcc is_empty_main_machine_object_no
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcc is_empty_main_machine_object_no
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    ldy #$00
    jsr emit_object_peek_payload_y
    beq is_empty_main_machine_object_yes
    cmp #'r'
    bne is_empty_main_machine_object_no
    iny
    jsr emit_object_peek_payload_y
    bne is_empty_main_machine_object_no
is_empty_main_machine_object_yes:
    sec
    rts
is_empty_main_machine_object_no:
    clc
    rts
.endif

scan_zp_is_main_symbol:
    ldy #$00
    jsr emit_object_peek_payload_y
    jsr lowercase_ascii_overlay
    cmp #'m'
    bne scan_zp_is_main_symbol_no
    iny
    jsr emit_object_peek_payload_y
    jsr lowercase_ascii_overlay
    cmp #'a'
    bne scan_zp_is_main_symbol_no
    iny
    jsr emit_object_peek_payload_y
    jsr lowercase_ascii_overlay
    cmp #'i'
    bne scan_zp_is_main_symbol_no
    iny
    jsr emit_object_peek_payload_y
    jsr lowercase_ascii_overlay
    cmp #'n'
    bne scan_zp_is_main_symbol_no
    iny
    jsr emit_object_peek_payload_y
    bne scan_zp_is_main_symbol_no
    sec
    rts
scan_zp_is_main_symbol_no:
    clc
    rts

.if (ACTC_EMIT_NATIVE_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_CONTROL_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_WHILE_ONLY = 0) .and (ACTC_EMIT_NATIVE_RUNTIME_CONDITION_ONLY = 0) .and (ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ACTIVE = 0) .and (ACTC_EMIT_NATIVE_REAL_FUNCTION_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_POSTFIX_ONLY = 0)
scan_zp_is_return_body:
    ldy #$00
    jsr emit_object_peek_payload_y
    beq scan_zp_is_return_body_yes
    cmp #'r'
    bne scan_zp_is_return_body_no
    iny
    jsr emit_object_peek_payload_y
    bne scan_zp_is_return_body_no
scan_zp_is_return_body_yes:
    sec
    rts
scan_zp_is_return_body_no:
    clc
    rts

is_main_pure_external_call_sequence_machine_object:
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$01
    bne is_main_pure_external_call_sequence_machine_object_no
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    beq is_main_pure_external_call_sequence_machine_object_no
    cmp #36
    bcs is_main_pure_external_call_sequence_machine_object_no
    sta compare_char_local
    lda #ACTC_OVERLAY_CTX_STRING_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_main_pure_external_call_sequence_machine_object_no
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_main_pure_external_call_sequence_machine_object_no
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_main_pure_external_call_sequence_machine_object_no
    lda #ACTC_OVERLAY_CTX_MODULE_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_main_pure_external_call_sequence_machine_object_no
    lda #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    jsr load_context_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcc is_main_pure_external_call_sequence_machine_object_no
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcc is_main_pure_external_call_sequence_machine_object_no
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    jsr scan_zp_is_external_call_sequence_return_body
    bcc is_main_pure_external_call_sequence_machine_object_no
    sec
    rts
is_main_pure_external_call_sequence_machine_object_no:
    clc
    rts

scan_zp_is_external_call_sequence_return_body:
    ldy #$00
    sty body_debug_count_local
scan_zp_is_external_call_sequence_return_body_loop:
    jsr emit_object_peek_payload_y
    cmp #'u'
    beq scan_zp_is_external_call_sequence_return_body_call
    cmp #'r'
    beq scan_zp_is_external_call_sequence_return_body_ret
    jmp scan_zp_is_external_call_sequence_return_body_no
scan_zp_is_external_call_sequence_return_body_call:
    iny
    jsr emit_object_peek_payload_y
    jsr external_import_selector_to_index
    bcc scan_zp_is_external_call_sequence_return_body_no
    cmp compare_char_local
    bcs scan_zp_is_external_call_sequence_return_body_no
    inc body_debug_count_local
    iny
    jmp scan_zp_is_external_call_sequence_return_body_loop
scan_zp_is_external_call_sequence_return_body_ret:
    lda body_debug_count_local
    beq scan_zp_is_external_call_sequence_return_body_no
    iny
    jsr emit_object_peek_payload_y
    bne scan_zp_is_external_call_sequence_return_body_no
    sec
    rts
scan_zp_is_external_call_sequence_return_body_no:
    clc
    rts

.endif
external_import_selector_to_index:
    ; Object body selectors are one-byte base36 import IDs: 0-9, A-Z.
    cmp #'0'
    bcc external_import_selector_to_index_no
    cmp #':'
    bcc external_import_selector_to_index_digit
    cmp #'A'
    bcc external_import_selector_to_index_no
    cmp #'['
    bcs external_import_selector_to_index_no
    sec
    sbc #55
    sec
    rts
external_import_selector_to_index_digit:
    sec
    sbc #'0'
    sec
    rts
external_import_selector_to_index_no:
    clc
    rts

.if (ACTC_EMIT_NATIVE_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_CONTROL_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_WHILE_ONLY = 0) .and (ACTC_EMIT_NATIVE_RUNTIME_CONDITION_ONLY = 0) .and (ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ACTIVE = 0) .and (ACTC_EMIT_NATIVE_REAL_FUNCTION_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_POSTFIX_ONLY = 0)
emit_count_external_call_sequence_body:
    ldy #$00
    sty body_debug_count_local
emit_count_external_call_sequence_body_loop:
    jsr emit_object_peek_payload_y
    cmp #'u'
    bne emit_count_external_call_sequence_body_done
    inc body_debug_count_local
    iny
    iny
    jmp emit_count_external_call_sequence_body_loop
emit_count_external_call_sequence_body_done:
    rts

is_main_local_call_sequence_machine_object:
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$02
    bcc is_main_local_call_sequence_machine_object_no
    cmp #10
    bcs is_main_local_call_sequence_machine_object_no
    sta compare_char_local
    sec
    sbc #$01
    sta proc_var_index_local
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_main_local_call_sequence_machine_object_no
    lda #ACTC_OVERLAY_CTX_STRING_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_main_local_call_sequence_machine_object_no
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_main_local_call_sequence_machine_object_no
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_main_local_call_sequence_machine_object_no
    lda #ACTC_OVERLAY_CTX_MODULE_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_main_local_call_sequence_machine_object_no
    lda #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    jsr load_context_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcc is_main_local_call_sequence_machine_object_no
    ldx proc_var_index_local
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcc is_main_local_call_sequence_machine_object_no
    lda #$00
    sta entry_index_data
is_main_local_call_sequence_machine_object_body_loop:
    lda entry_index_data
    cmp compare_char_local
    beq is_main_local_call_sequence_machine_object_yes
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    jsr scan_zp_is_local_call_sequence_return_body
    bcc is_main_local_call_sequence_machine_object_no
    lda entry_index_data
    cmp proc_var_index_local
    bne is_main_local_call_sequence_machine_object_next_body
    lda body_debug_count_local
    beq is_main_local_call_sequence_machine_object_no
is_main_local_call_sequence_machine_object_next_body:
    inc entry_index_data
    jmp is_main_local_call_sequence_machine_object_body_loop
is_main_local_call_sequence_machine_object_yes:
    sec
    rts
is_main_local_call_sequence_machine_object_no:
    clc
    rts

scan_zp_is_local_call_sequence_return_body:
    ldy #$00
    sty body_debug_count_local
scan_zp_is_local_call_sequence_return_body_loop:
    jsr emit_object_peek_payload_y
    cmp #'c'
    beq scan_zp_is_local_call_sequence_return_body_call
    cmp #'r'
    beq scan_zp_is_local_call_sequence_return_body_ret
    jmp scan_zp_is_local_call_sequence_return_body_no
scan_zp_is_local_call_sequence_return_body_call:
    iny
    jsr emit_object_peek_payload_y
    cmp #'0'
    bcc scan_zp_is_local_call_sequence_return_body_no
    cmp #':'
    bcs scan_zp_is_local_call_sequence_return_body_no
    sec
    sbc #'0'
    cmp compare_char_local
    bcs scan_zp_is_local_call_sequence_return_body_no
    inc body_debug_count_local
    iny
    jmp scan_zp_is_local_call_sequence_return_body_loop
scan_zp_is_local_call_sequence_return_body_ret:
    iny
    jsr emit_object_peek_payload_y
    bne scan_zp_is_local_call_sequence_return_body_no
    sec
    rts
scan_zp_is_local_call_sequence_return_body_no:
    clc
    rts

emit_count_local_call_sequence_body:
    ldy #$00
    sty body_debug_count_local
emit_count_local_call_sequence_body_loop:
    jsr emit_object_peek_payload_y
    cmp #'c'
    bne emit_count_local_call_sequence_body_done
    inc body_debug_count_local
    iny
    iny
    jmp emit_count_local_call_sequence_body_loop
emit_count_local_call_sequence_body_done:
    rts

is_main_local_external_call_sequence_machine_object:
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$02
    bcc is_main_local_external_call_sequence_machine_object_no
    cmp #10
    bcs is_main_local_external_call_sequence_machine_object_no
    sta word_value_hi
    sec
    sbc #$01
    sta proc_var_index_local
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    beq is_main_local_external_call_sequence_machine_object_no
    cmp #10
    bcs is_main_local_external_call_sequence_machine_object_no
    sta compare_char_local
    lda #ACTC_OVERLAY_CTX_STRING_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_main_local_external_call_sequence_machine_object_no
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_main_local_external_call_sequence_machine_object_no
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_main_local_external_call_sequence_machine_object_no
    lda #ACTC_OVERLAY_CTX_MODULE_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    bne is_main_local_external_call_sequence_machine_object_no
    lda #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    jsr load_context_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcc is_main_local_external_call_sequence_machine_object_no
    ldx proc_var_index_local
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcc is_main_local_external_call_sequence_machine_object_no
    lda #$00
    sta entry_index_data
is_main_local_external_call_sequence_machine_object_body_loop:
    lda entry_index_data
    cmp word_value_hi
    beq is_main_local_external_call_sequence_machine_object_yes
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    jsr scan_zp_is_local_external_call_sequence_return_body
    bcc is_main_local_external_call_sequence_machine_object_no
    inc entry_index_data
    jmp is_main_local_external_call_sequence_machine_object_body_loop
is_main_local_external_call_sequence_machine_object_yes:
    sec
    rts
is_main_local_external_call_sequence_machine_object_no:
    clc
    rts

scan_zp_is_local_external_call_sequence_return_body:
    ldy #$00
    sty body_debug_count_local
scan_zp_is_local_external_call_sequence_return_body_loop:
    jsr emit_object_peek_payload_y
    cmp #'c'
    beq scan_zp_is_local_external_call_sequence_return_body_local_call
    cmp #'u'
    beq scan_zp_is_local_external_call_sequence_return_body_external_call
    cmp #'r'
    beq scan_zp_is_local_external_call_sequence_return_body_ret
    jmp scan_zp_is_local_external_call_sequence_return_body_no
scan_zp_is_local_external_call_sequence_return_body_local_call:
    iny
    jsr emit_object_peek_payload_y
    cmp #'0'
    bcc scan_zp_is_local_external_call_sequence_return_body_no
    cmp #':'
    bcs scan_zp_is_local_external_call_sequence_return_body_no
    sec
    sbc #'0'
    cmp word_value_hi
    bcs scan_zp_is_local_external_call_sequence_return_body_no
    inc body_debug_count_local
    iny
    jmp scan_zp_is_local_external_call_sequence_return_body_loop
scan_zp_is_local_external_call_sequence_return_body_external_call:
    iny
    jsr emit_object_peek_payload_y
    cmp #'0'
    bcc scan_zp_is_local_external_call_sequence_return_body_no
    cmp #':'
    bcs scan_zp_is_local_external_call_sequence_return_body_no
    sec
    sbc #'0'
    cmp compare_char_local
    bcs scan_zp_is_local_external_call_sequence_return_body_no
    inc body_debug_count_local
    iny
    jmp scan_zp_is_local_external_call_sequence_return_body_loop
scan_zp_is_local_external_call_sequence_return_body_ret:
    iny
    jsr emit_object_peek_payload_y
    bne scan_zp_is_local_external_call_sequence_return_body_no
    sec
    rts
scan_zp_is_local_external_call_sequence_return_body_no:
    clc
    rts

emit_count_local_external_call_sequence_body:
    ldy #$00
    lda #$00
    sta body_debug_count_local
emit_count_local_external_call_sequence_body_loop:
    jsr emit_object_peek_payload_y
    cmp #'c'
    beq emit_count_local_external_call_sequence_body_call
    cmp #'u'
    beq emit_count_local_external_call_sequence_body_call
    jmp emit_count_local_external_call_sequence_body_done
emit_count_local_external_call_sequence_body_call:
    inc body_debug_count_local
    iny
    iny
    jmp emit_count_local_external_call_sequence_body_loop
emit_count_local_external_call_sequence_body_done:
    rts
.endif

emit_machine_body_marker_line:
    lda #'b'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #'M'
    jsr emit_char_overlay
    jmp emit_newline

emit_machine_external_call_sequence_body_marker_line:
    lda #'b'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #$00
    sta entry_index_data
emit_machine_external_call_sequence_body_marker_loop:
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq emit_machine_external_call_sequence_body_marker_done
    lda #'u'
    jsr emit_char_overlay
    lda entry_index_data
    jsr emit_object_selector_overlay
    inc entry_index_data
    jmp emit_machine_external_call_sequence_body_marker_loop
emit_machine_external_call_sequence_body_marker_done:
    lda #'M'
    jsr emit_char_overlay
    jmp emit_newline

emit_object_selector_overlay:
    cmp #10
    bcc emit_object_selector_overlay_digit
    sec
    sbc #10
    clc
    adc #'A'
    jmp emit_char_overlay
emit_object_selector_overlay_digit:
    clc
    adc #'0'
    jmp emit_char_overlay

.if ACTC_EMIT_NATIVE_REAL_ONLY
.include "actc_overlay_emit_native_real.inc"
.endif

.if ACTC_EMIT_NATIVE_REAL_FUNCTION_ONLY
.include "actc_overlay_emit_native_real_function.inc"
.endif

.if ACTC_EMIT_NATIVE_REAL_POSTFIX_ONLY
.include "actc_overlay_emit_native_real_postfix.inc"
.endif

.if ACTC_EMIT_NATIVE_REAL_CONTROL_ONLY
.include "actc_overlay_emit_native_real_control.inc"
.endif

.if ACTC_EMIT_NATIVE_REAL_WHILE_ONLY
.include "actc_overlay_emit_native_real_while.inc"
.endif

.if ACTC_EMIT_NATIVE_RUNTIME_CONDITION_ONLY
.include "actc_overlay_emit_native_runtime_condition.inc"
.endif

.if ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ACTIVE
.include "actc_overlay_emit_native_runtime_sequence.inc"
.endif

.if ACTC_EMIT_NATIVE_ONLY
.if ACTC_EMIT_NATIVE_LOCAL_ONLY
.include "actc_overlay_emit_native_local_integer.inc"
.else
.include "actc_overlay_emit_native_integer.inc"
.endif
.endif

emit_newline:
    lda #10
    jmp emit_char_overlay

emit_hex_byte_overlay:
    sta emitted_char_local
    lda #ACTC_OVERLAY_CTX_APPEND_HEX_BYTE_UPPER_FN_LO
    jsr load_context_function_ptr
    lda emitted_char_local
    jmp call_loaded_target_with_a

emit_small_decimal:
    ldy #$00
    jmp emit_word_decimal

emit_word_decimal:
    sta word_value_lo
    sty word_value_hi
    lda #ACTC_OVERLAY_CTX_APPEND_WORD_DECIMAL_FN_LO
    jsr load_context_function_ptr
    lda word_value_lo
    ldy word_value_hi
    jmp call_loaded_target_with_a

lowercase_ascii_overlay:
    cmp #'A'
    bcc lowercase_ascii_overlay_done
    cmp #'Z'+1
    bcs lowercase_ascii_overlay_done
    ora #$20
lowercase_ascii_overlay_done:
    rts

load_count_from_context:
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    rts

load_indexed_byte_from_context_ptr:
    stx saved_x_local
    jsr load_context_ptr_to_work_zp
    ldy saved_x_local
    lda (ACTC_OVERLAY_WORK_ZP),y
    ldx saved_x_local
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

load_context_ptr_to_scan_zp:
    sta saved_a_local
    sty saved_y_local
    tay
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP
    iny
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP+1
    lda saved_a_local
    ldy saved_y_local
    rts

load_resident_body_ptr_to_scan_zp:
    lda #ACTC_OVERLAY_CTX_BODY_PTR_SLOT_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP+1
    rts

load_resident_export_ptr_to_scan_zp:
    lda #ACTC_OVERLAY_CTX_EXPORT_PTR_SLOT_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP+1
    rts

emit_char_overlay:
    sta emitted_char_local
    lda #ACTC_OVERLAY_CTX_APPEND_CHAR_FN_LO
    jsr load_context_function_ptr
    lda emitted_char_local
    jsr call_loaded_target_with_a
    rts

call_indexed_context_function:
    stx saved_x_local
    jsr load_context_function_ptr
    lda #$00
    ldx saved_x_local
    jsr call_loaded_target_with_a
    ldx saved_x_local
    rts

call_proc_op_context_function:
    jsr load_context_function_ptr
    sec
    lda call_target_ptr
    sbc #$01
    sta call_target_minus_one
    lda call_target_ptr+1
    sbc #$00
    pha
    lda call_target_minus_one
    pha
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

emit_object_peek_payload_y:
    ; Reads resident body/string/object payload windows selected by SET_*_PTR,
    ; not source text. Source-window paging belongs to SourceReader helpers.
    lda (ACTC_OVERLAY_SCAN_ZP),y
    rts

.if (ACTC_EMIT_NATIVE_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_CONTROL_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_WHILE_ONLY = 0) .and (ACTC_EMIT_NATIVE_RUNTIME_CONDITION_ONLY = 0) .and (ACTC_EMIT_NATIVE_RUNTIME_SEQUENCE_ACTIVE = 0) .and (ACTC_EMIT_NATIVE_REAL_FUNCTION_ONLY = 0) .and (ACTC_EMIT_NATIVE_REAL_POSTFIX_ONLY = 0)
empty_main_machine_record:
    .asciiz "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF"
external_call_sequence_epilogue_bytes:
    .asciiz " A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF"
a_to_xy_word_setup_bytes:
    .asciiz " AA A0 00"
runtime_symbol_rt_sid_cutoff_emit:
    .asciiz "RT_SID_CUTOFF"
.endif

actc_overlay_end:

.segment "BSS"

call_target_minus_one:
    .res 1
call_target_ptr:
    .res 2
call_arg_a:
    .res 1
entry_index_data:
    .res 1
compare_char_local:
    .res 1
word_value_lo:
    .res 1
word_value_hi:
    .res 1
body_debug_count_local:
    .res 1
body_debug_index_data:
    .res 1
proc_var_base_local:
    .res 1
proc_var_scope_local:
    .res 1
proc_var_index_local:
    .res 1
saved_a_local:
    .res 1
saved_x_local:
    .res 1
saved_y_local:
    .res 1
emitted_char_local:
    .res 1
body_marker_visit_mask:
    .res 1
