; Nested REAL postfix lowering to ordinary OBJ1 machine records.
.macpack longbranch

NRP_ENABLE_EARLY_RETURN = ACTC_EMIT_NATIVE_REAL_POSTFIX_EARLY_RETURN_ONLY
NRP_ENABLE_EXTENDED_CONTROL = ACTC_EMIT_NATIVE_REAL_POSTFIX_EXTENDED_CONTROL_ONLY + NRP_ENABLE_EARLY_RETURN
NRP_ENABLE_MULTI_CONTROL = ACTC_EMIT_NATIVE_REAL_POSTFIX_MULTI_CONTROL_ONLY + NRP_ENABLE_EXTENDED_CONTROL
NRP_ENABLE_CONTROL = ACTC_EMIT_NATIVE_REAL_POSTFIX_CONTROL_ONLY + NRP_ENABLE_MULTI_CONTROL
NRP_ENABLE_LOOP_EXIT = ACTC_EMIT_NATIVE_REAL_POSTFIX_LOOP_EXIT_ONLY
NRP_ENABLE_FOR_DYNAMIC = ACTC_EMIT_NATIVE_REAL_POSTFIX_FOR_DYNAMIC_ONLY
NRP_ENABLE_FOR = ACTC_EMIT_NATIVE_REAL_POSTFIX_FOR_ONLY + NRP_ENABLE_FOR_DYNAMIC
NRP_ENABLE_GENERIC_LOOP = ACTC_EMIT_NATIVE_REAL_POSTFIX_LOOP_ONLY + NRP_ENABLE_LOOP_EXIT
NRP_ENABLE_LOOP = NRP_ENABLE_GENERIC_LOOP + NRP_ENABLE_FOR
NRP_ENABLE_CONDITION = NRP_ENABLE_CONTROL + NRP_ENABLE_LOOP
NRP_ENABLE_LITERAL = ACTC_EMIT_NATIVE_REAL_POSTFIX_LITERAL_ONLY
NRP_ENABLE_VARIABLE_ARITY = NRP_ENABLE_LITERAL
NRP_ENABLE_WORD_VALUES = NRP_ENABLE_FOR + NRP_ENABLE_LITERAL

NRP_MODE_ANALYZE = 0
NRP_MODE_MACHINE = 1
NRP_MODE_RELOC = 2

NRP_PROGRAM_MAIN = 0
NRP_PROGRAM_REAL_FUNCTION = 1

NRP_VALUE_INT = 1
NRP_VALUE_VAR = 2
NRP_VALUE_TEMP = 3
NRP_VALUE_COMPARE = 4
NRP_VALUE_CONDITION = 5
.if NRP_ENABLE_FOR
NRP_VALUE_WORD = 6
.endif

NRP_HELPER_CONVERT = 1
NRP_HELPER_PRINT = 2
NRP_HELPER_UNARY = 3
NRP_HELPER_BINARY = 4
NRP_HELPER_TERNARY = 5
NRP_HELPER_COMPARE = 6

NRP_STACK_MAX = 8
NRP_TEMP_MAX = 16
NRP_DEBUG_MAX = 64
NRP_FUNCTION_MAX = 2
NRP_PROC_MAX = NRP_FUNCTION_MAX+1
.if NRP_ENABLE_MULTI_CONTROL
.if NRP_ENABLE_EXTENDED_CONTROL
NRP_CONTROL_MAX = 4
NRP_CONTROL_MIN = 3
NRP_CONTROL_MASK = 3
.else
NRP_CONTROL_MAX = 2
NRP_CONTROL_MIN = 2
NRP_CONTROL_MASK = 1
.endif
NRP_CONTROL_SLOT_MAX = NRP_FUNCTION_MAX*NRP_CONTROL_MAX
.endif
.if NRP_ENABLE_CONDITION
NRP_HELPER_BASE_COUNT = 21
.else
NRP_HELPER_BASE_COUNT = 20
.endif
.if NRP_ENABLE_LITERAL
NRP_HELPER_COUNT = NRP_HELPER_BASE_COUNT+2
.else
NRP_HELPER_COUNT = NRP_HELPER_BASE_COUNT
.endif
.if NRP_ENABLE_LOOP
NRP_LOOP_MAX = 4
NRP_LOOP_MASK = 3
NRP_LOOP_SLOT_MAX = NRP_FUNCTION_MAX*NRP_LOOP_MAX
NRP_LOOP_UNKNOWN = 0
NRP_LOOP_WHILE = 1
NRP_LOOP_UNTIL = 2
NRP_LOOP_PLAIN = 3
.if NRP_ENABLE_FOR
NRP_LOOP_FOR = 4
.endif
.endif

native_real_postfix_detect:
    lda #$00
    sta nrp_active
    sta nrp_rejected_call_graph
    sta nrp_program_mode
    sta nrp_call_edges
    sta nrp_call_edges+1
.if NRP_ENABLE_LITERAL
    sta nrp_literal_seen
    sta nrp_angle_seen
.endif
.if NRP_ENABLE_EARLY_RETURN
    sta nrp_early_return_seen
.endif
.if NRP_ENABLE_CONTROL
.if NRP_ENABLE_MULTI_CONTROL
    sta nrp_multi_control_seen
    ldx #(NRP_CONTROL_SLOT_MAX-1)
native_real_postfix_clear_multi_control_loop:
    sta nrp_if_seen,x
    sta nrp_if_has_else,x
    dex
    bpl native_real_postfix_clear_multi_control_loop
.else
    sta nrp_if_seen
    sta nrp_if_seen+1
    sta nrp_if_has_else
    sta nrp_if_has_else+1
.endif
.endif
.if NRP_ENABLE_LOOP
    sta nrp_loop_seen_any
.if NRP_ENABLE_FOR
    sta nrp_for_seen_any
.if NRP_ENABLE_FOR_DYNAMIC
    sta nrp_for_dynamic_seen_any
.endif
.endif
.if NRP_ENABLE_LOOP_EXIT
    sta nrp_loop_special_seen_any
.endif
    ldx #(NRP_LOOP_SLOT_MAX-1)
native_real_postfix_clear_loop_loop:
    sta nrp_loop_seen,x
    sta nrp_loop_has_exit,x
.if NRP_ENABLE_LOOP_EXIT
    sta nrp_loop_user_exit,x
.endif
    dex
    bpl native_real_postfix_clear_loop_loop
.endif
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$01
    beq native_real_postfix_detect_main
    cmp #$02
    jcc native_real_postfix_detect_no
    cmp #NRP_FUNCTION_MAX+2
    jcs native_real_postfix_detect_no
    sec
    sbc #$01
    sta nrp_function_count
    jmp native_real_postfix_detect_function

native_real_postfix_detect_main:
    lda #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    jsr load_context_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    jcc native_real_postfix_detect_no
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    jcc native_real_postfix_detect_no

    ldx #$00
    lda #ACTC_OVERLAY_CTX_LOAD_PROC_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_PROC_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    jne native_real_postfix_detect_no
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    jne native_real_postfix_detect_no

    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    jeq native_real_postfix_detect_no
    cmp #NRP_TEMP_MAX+1
    jcs native_real_postfix_detect_no
    sta nrp_var_count
    lda #ACTC_OVERLAY_CTX_MODULE_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp nrp_var_count
    jne native_real_postfix_detect_no
    sta nrp_module_var_count
    jmp native_real_postfix_detect_vars

native_real_postfix_detect_function:
    lda #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    jsr load_context_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    jcc native_real_postfix_detect_no
    ldx nrp_function_count
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    jcc native_real_postfix_detect_no

    lda #ACTC_OVERLAY_CTX_MODULE_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    sta nrp_module_var_count
    sta nrp_expected_var_index
    lda #$00
    sta nrp_function_index
native_real_postfix_detect_function_meta_loop:
    lda nrp_function_index
    cmp nrp_function_count
    beq native_real_postfix_detect_main_meta
    tax
    lda #ACTC_OVERLAY_CTX_LOAD_PROC_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_PROC_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
.if NRP_ENABLE_VARIABLE_ARITY
    sta nrp_saved_index
    and #(ACTC_PROC_META_FUNCTION | ACTC_PROC_META_REAL_RETURN)
    cmp #(ACTC_PROC_META_FUNCTION | ACTC_PROC_META_REAL_RETURN)
    jne native_real_postfix_detect_no
    lda nrp_saved_index
    and #ACTC_PROC_META_PARAM_COUNT_MASK
    jeq native_real_postfix_detect_no
    cmp #$03
    jcs native_real_postfix_detect_no
    ldx nrp_function_index
    sta nrp_function_param_count,x
.else
    cmp #(ACTC_PROC_META_FUNCTION | ACTC_PROC_META_REAL_RETURN | 2)
    jne native_real_postfix_detect_no
.endif
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp nrp_expected_var_index
    jne native_real_postfix_detect_no
    ldx nrp_function_index
    sta nrp_function_param_base,x
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta nrp_function_local_count,x
    clc
.if NRP_ENABLE_VARIABLE_ARITY
    adc nrp_function_param_count,x
.else
    adc #$02
.endif
    jcs native_real_postfix_detect_no
    clc
    adc nrp_expected_var_index
    jcs native_real_postfix_detect_no
    sta nrp_expected_var_index
    inc nrp_function_index
    jmp native_real_postfix_detect_function_meta_loop

native_real_postfix_detect_main_meta:
    ldx nrp_function_count
    lda #ACTC_OVERLAY_CTX_LOAD_PROC_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_PROC_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    jne native_real_postfix_detect_no
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    jne native_real_postfix_detect_no

    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp nrp_expected_var_index
    jne native_real_postfix_detect_no
    cmp #NRP_TEMP_MAX+1
    jcs native_real_postfix_detect_no
    sta nrp_var_count
    lda #NRP_PROGRAM_REAL_FUNCTION
    sta nrp_program_mode

native_real_postfix_detect_vars:
    ldx #$00
native_real_postfix_detect_var_loop:
.if NRP_ENABLE_FOR
    jsr nrp_var_x_kind
    jcc native_real_postfix_detect_no
    sta nrp_var_kind,x
.else
    jsr nrp_var_x_is_real
    jcc native_real_postfix_detect_no
.endif
    inx
    cpx nrp_var_count
    bcc native_real_postfix_detect_var_loop

    lda #ACTC_OVERLAY_CTX_STRING_COUNT_PTR_LO
    jsr load_count_from_context
    jne native_real_postfix_detect_no
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    jeq native_real_postfix_detect_no
    cmp #37
    jcs native_real_postfix_detect_no

    lda #$00
    sta nrp_nested
    lda nrp_program_mode
    jne native_real_postfix_analyze_function

    sta nrp_proc_index
    sta nrp_code_start_lo
    sta nrp_code_start_hi
    sta nrp_temp_base
    lda #NRP_MODE_ANALYZE
    jsr nrp_parse_body
    jcc native_real_postfix_detect_no
    lda #ACTC_OVERLAY_CTX_BODY_DEBUG_COUNT_PTR_LO
    ldx #$00
    jsr load_indexed_byte_from_context_ptr
    cmp nrp_debug_count
    jne native_real_postfix_detect_no
    lda nrp_code_lo
    sta nrp_code_size_lo
    lda nrp_code_hi
    sta nrp_code_size_hi
    lda nrp_temp_count
    sta nrp_temp_total
    jmp native_real_postfix_analyze_done

native_real_postfix_analyze_function:
    lda nrp_function_count
    sta nrp_proc_index
    lda #$00
    sta nrp_code_start_lo
    sta nrp_code_start_hi
    sta nrp_temp_base
    lda #NRP_MODE_ANALYZE
    jsr nrp_parse_body
    jcc native_real_postfix_detect_no
    lda #ACTC_OVERLAY_CTX_BODY_DEBUG_COUNT_PTR_LO
    ldx nrp_proc_index
    jsr load_indexed_byte_from_context_ptr
    cmp nrp_debug_count
    jne native_real_postfix_detect_no
    lda nrp_code_lo
    sta nrp_main_code_size_lo
    sta nrp_code_size_lo
    lda nrp_code_hi
    sta nrp_main_code_size_hi
    sta nrp_code_size_hi
    lda nrp_temp_count
    sta nrp_main_temp_count
    sta nrp_temp_total
    lda #$00
    sta nrp_function_index
native_real_postfix_analyze_function_loop:
    lda nrp_function_index
    cmp nrp_function_count
    beq native_real_postfix_analyze_done
    sta nrp_proc_index
    tax
    lda nrp_code_size_lo
    sta nrp_code_start_lo
    sta nrp_function_code_start_lo,x
    lda nrp_code_size_hi
    sta nrp_code_start_hi
    sta nrp_function_code_start_hi,x
    lda nrp_temp_total
    sta nrp_temp_base
    sta nrp_function_temp_base,x
    lda nrp_function_param_base,x
    sta nrp_param_base
    lda #NRP_MODE_ANALYZE
    jsr nrp_parse_body
    jcc native_real_postfix_detect_no
    lda #ACTC_OVERLAY_CTX_BODY_DEBUG_COUNT_PTR_LO
    ldx nrp_proc_index
    jsr load_indexed_byte_from_context_ptr
    cmp nrp_debug_count
    jne native_real_postfix_detect_no
    ldx nrp_function_index
    lda nrp_code_lo
    sta nrp_code_size_lo
    sec
    sbc nrp_code_start_lo
    sta nrp_function_code_size_lo,x
    lda nrp_code_hi
    sta nrp_code_size_hi
    sbc nrp_code_start_hi
    sta nrp_function_code_size_hi,x
    lda nrp_temp_count
    sta nrp_temp_total
    inc nrp_function_index
    jmp native_real_postfix_analyze_function_loop

native_real_postfix_analyze_done:
    lda nrp_program_mode
    cmp #NRP_PROGRAM_REAL_FUNCTION
    bne :+
    jsr nrp_validate_call_graph
    jcc native_real_postfix_detect_no
:
.if NRP_ENABLE_LITERAL
    lda nrp_angle_seen
    bne :+
    lda nrp_program_mode
    cmp #NRP_PROGRAM_REAL_FUNCTION
    jne native_real_postfix_detect_no
    lda nrp_literal_seen
    jeq native_real_postfix_detect_no
:
.elseif NRP_ENABLE_FOR_DYNAMIC
    lda nrp_for_dynamic_seen_any
    jeq native_real_postfix_detect_no
.elseif NRP_ENABLE_FOR
    lda nrp_for_seen_any
    jeq native_real_postfix_detect_no
.elseif NRP_ENABLE_EARLY_RETURN
    lda nrp_early_return_seen
    jeq native_real_postfix_detect_no
.elseif NRP_ENABLE_LOOP_EXIT
    lda nrp_loop_special_seen_any
    jeq native_real_postfix_detect_no
.elseif NRP_ENABLE_LOOP
    lda nrp_loop_seen_any
    jeq native_real_postfix_detect_no
.elseif NRP_ENABLE_MULTI_CONTROL
    lda nrp_multi_control_seen
    jeq native_real_postfix_detect_no
.elseif NRP_ENABLE_CONTROL
    lda nrp_if_seen
    ora nrp_if_seen+1
    jeq native_real_postfix_detect_no
.endif
    lda nrp_nested
    jeq native_real_postfix_detect_no
    lda nrp_var_count
    clc
    adc nrp_temp_total
    sta nrp_data_slots
    lda nrp_code_size_lo
    sta nrp_root_size_lo
    lda nrp_code_size_hi
    sta nrp_root_size_hi
    lda nrp_data_slots
    asl a
    asl a
    clc
    adc nrp_root_size_lo
    sta nrp_root_size_lo
    bcc :+
    inc nrp_root_size_hi
:
    lda #$01
    sta nrp_active
    sec
    rts
native_real_postfix_detect_no:
    lda #$00
    sta nrp_active
    clc
    rts

.if NRP_ENABLE_FOR
nrp_var_x_kind:
    lda #ACTC_OVERLAY_CTX_LOAD_VAR_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp #$04
    beq nrp_var_x_kind_real
    cmp #$02
    bne nrp_var_x_kind_no
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr lowercase_ascii_overlay
    cmp #'c'
    bne nrp_var_x_kind_no
    lda #NRP_VALUE_WORD
    sec
    rts
nrp_var_x_kind_real:
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr lowercase_ascii_overlay
    cmp #'r'
    bne nrp_var_x_kind_no
    lda #NRP_VALUE_VAR
    sec
    rts
nrp_var_x_kind_no:
    clc
    rts
.else
nrp_var_x_is_real:
    lda #ACTC_OVERLAY_CTX_LOAD_VAR_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp #$04
    bne nrp_var_x_is_real_no
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr lowercase_ascii_overlay
    cmp #'r'
    bne nrp_var_x_is_real_no
    sec
    rts
nrp_var_x_is_real_no:
    clc
    rts
.endif

nrp_parse_body:
    sta nrp_mode
    lda #$00
    sta nrp_body_pos
    sta nrp_stack_depth
    sta nrp_debug_count
    sta nrp_pending_load
    sta nrp_pending_store
    sta nrp_saw_return
    sta nrp_param_binds_left
.if NRP_ENABLE_CONTROL
    sta nrp_control_count
    sta nrp_control_depth
.if NRP_ENABLE_MULTI_CONTROL
    sta nrp_control_index
.else
    sta nrp_control_else_seen
.endif
.endif
.if NRP_ENABLE_LOOP
    sta nrp_loop_count
    sta nrp_loop_depth
    sta nrp_loop_index
.if NRP_ENABLE_FOR
    sta nrp_for_pending
.endif
.endif
    lda nrp_temp_base
    sta nrp_temp_count
    lda nrp_code_start_lo
    sta nrp_code_lo
    lda nrp_code_start_hi
    sta nrp_code_hi
    lda nrp_program_mode
    cmp #NRP_PROGRAM_REAL_FUNCTION
    bne :+
    lda nrp_proc_index
    cmp nrp_function_count
    bcs :+
.if NRP_ENABLE_VARIABLE_ARITY
    tax
    lda nrp_function_param_count,x
    sta nrp_param_count
    sta nrp_param_binds_left
.else
    lda #$02
    sta nrp_param_binds_left
.endif
:
nrp_parse_body_loop:
    jsr nrp_read_body
    jeq nrp_parse_body_fail
    sta nrp_opcode
    jsr nrp_record_debug_offset
    jcc nrp_parse_body_fail
    lda nrp_opcode
    cmp #'p'
    jeq nrp_parse_push_int
    cmp #'L'
    jeq nrp_parse_load
    cmp #'U'
    jeq nrp_parse_load_end
    cmp #'u'
    jeq nrp_parse_call
    cmp #'C'
    jeq nrp_parse_local_call
.if NRP_ENABLE_FOR
    cmp #'a'
    jeq nrp_parse_int_add
    cmp #'m'
    jeq nrp_parse_int_sub
.endif
.if NRP_ENABLE_CONDITION
    cmp #'g'
    jeq nrp_parse_relation
    cmp #'l'
    jeq nrp_parse_relation
    cmp #'q'
    jeq nrp_parse_relation
    cmp #'n'
    jeq nrp_parse_relation
.endif
.if NRP_ENABLE_CONTROL
    cmp #'h'
    jeq nrp_parse_if
    cmp #'w'
    jeq nrp_parse_else
    cmp #'v'
    jeq nrp_parse_endif
.endif
.if NRP_ENABLE_LOOP
 .if NRP_ENABLE_FOR
    cmp #'F'
    jeq nrp_parse_for
    cmp #'O'
    jeq nrp_parse_for_end
 .endif
.if NRP_ENABLE_GENERIC_LOOP
    cmp #'d'
    jeq nrp_parse_loop_start
    cmp #'f'
    jeq nrp_parse_loop_while
    cmp #'t'
    jeq nrp_parse_loop_until
    cmp #'o'
    jeq nrp_parse_loop_until_end
    cmp #'x'
    jeq nrp_parse_loop_while_end
.if NRP_ENABLE_LOOP_EXIT
    cmp #'X'
    jeq nrp_parse_loop_exit
.endif
.endif
.endif
    cmp #'T'
    jeq nrp_parse_store
    cmp #'S'
    bne :+
    lda nrp_param_binds_left
    jne nrp_parse_param_bind
.if NRP_ENABLE_FOR
    lda nrp_pending_store
    jeq nrp_parse_for_initial_store
.endif
    jmp nrp_parse_store_end
:
    cmp #'r'
    jeq nrp_parse_return
    jmp nrp_parse_body_fail

nrp_parse_push_int:
    jsr nrp_read_selector
    jcc nrp_parse_body_fail
    cmp #36
    jcs nrp_parse_body_fail
.if NRP_ENABLE_WORD_VALUES
    sta nrp_literal_index
    jsr nrp_load_literal_word
    jcc nrp_parse_body_fail
    lda nrp_literal_lo
    sta nrp_value_lo
    lda nrp_literal_hi
    sta nrp_value_hi
    ldx nrp_literal_index
.else
    tax
.endif
    lda #NRP_VALUE_INT
    jsr nrp_push_value
    jcc nrp_parse_body_fail
    jmp nrp_parse_body_loop

nrp_parse_load:
    lda nrp_pending_load
    jne nrp_parse_body_fail
    jsr nrp_read_selector
    jcc nrp_parse_body_fail
    cmp nrp_var_count
    jcs nrp_parse_body_fail
    sta nrp_pending_value
    tax
.if NRP_ENABLE_FOR_DYNAMIC
    lda nrp_var_kind,x
    cmp #NRP_VALUE_WORD
    beq nrp_parse_load_push
    txa
    clc
    adc #$01
    sta nrp_pending_load
    lda nrp_var_kind,x
nrp_parse_load_push:
.else
    clc
    adc #$01
    sta nrp_pending_load
.if NRP_ENABLE_FOR
    lda nrp_var_kind,x
.else
    lda #NRP_VALUE_VAR
.endif
.endif
    jsr nrp_push_value
    jcc nrp_parse_body_fail
    jmp nrp_parse_body_loop

nrp_parse_load_end:
    lda nrp_pending_load
    jeq nrp_parse_body_fail
    jsr nrp_read_selector
    jcc nrp_parse_body_fail
    cmp nrp_pending_value
    jne nrp_parse_body_fail
    lda #$00
    sta nrp_pending_load
    jmp nrp_parse_body_loop

nrp_parse_store:
    lda nrp_pending_store
    jne nrp_parse_body_fail
    jsr nrp_read_selector
    jcc nrp_parse_body_fail
    cmp nrp_var_count
    jcs nrp_parse_body_fail
    sta nrp_pending_value
    clc
    adc #$01
    sta nrp_pending_store
    jmp nrp_parse_body_loop

nrp_parse_store_end:
    lda nrp_pending_store
    jeq nrp_parse_body_fail
    jsr nrp_read_selector
    jcc nrp_parse_body_fail
    cmp nrp_pending_value
    jne nrp_parse_body_fail
    lda #$00
    sta nrp_pending_store
    jsr nrp_pop_real_to_operand1
    jcc nrp_parse_body_fail
    lda #NRP_VALUE_VAR
    sta nrp_name_kind
    lda nrp_pending_value
    sta nrp_name_index
    jsr nrp_emit_copy_operand1_to_name
    jmp nrp_parse_body_loop

nrp_parse_call:
    jsr nrp_read_selector
    jcc nrp_parse_body_fail
    sta nrp_import_index
    tax
    jsr nrp_classify_external_x
    jcc nrp_parse_body_fail
    cmp #NRP_HELPER_CONVERT
    jeq nrp_parse_call_convert
    cmp #NRP_HELPER_PRINT
    jeq nrp_parse_call_print
    cmp #NRP_HELPER_UNARY
    jeq nrp_parse_call_unary
    cmp #NRP_HELPER_BINARY
    jeq nrp_parse_call_binary
    cmp #NRP_HELPER_TERNARY
    jeq nrp_parse_call_ternary
.if NRP_ENABLE_CONDITION
    cmp #NRP_HELPER_COMPARE
    jeq nrp_parse_call_compare
.endif
    jmp nrp_parse_body_fail

nrp_parse_call_convert:
    jsr nrp_pop_value
    jcc nrp_parse_body_fail
.if NRP_ENABLE_FOR
    sta nrp_conversion_source_kind
    cmp #NRP_VALUE_WORD
    beq nrp_parse_call_convert_word
    cmp #NRP_VALUE_INT
    jne nrp_parse_body_fail
    lda nrp_value_lo
    sta nrp_literal_lo
    lda nrp_value_hi
    sta nrp_literal_hi
    jmp nrp_parse_call_convert_allocate
nrp_parse_call_convert_word:
    stx nrp_conversion_word_index
nrp_parse_call_convert_allocate:
.else
    cmp #NRP_VALUE_INT
    jne nrp_parse_body_fail
    stx nrp_literal_index
.endif
    jsr nrp_allocate_temp
    jcc nrp_parse_body_fail
    stx nrp_dest_index
    jsr nrp_emit_conversion
    lda #NRP_VALUE_TEMP
    ldx nrp_dest_index
    jsr nrp_push_value
    jcc nrp_parse_body_fail
    jmp nrp_parse_body_loop

.if NRP_ENABLE_FOR
nrp_parse_int_add:
    lda #$00
    beq nrp_parse_int_arithmetic
nrp_parse_int_sub:
    lda #$01
nrp_parse_int_arithmetic:
    sta nrp_int_subtract
    jsr nrp_pop_value
    jcc nrp_parse_body_fail
    cmp #NRP_VALUE_INT
    jne nrp_parse_body_fail
    lda nrp_value_lo
    sta nrp_int_rhs_lo
    lda nrp_value_hi
    sta nrp_int_rhs_hi
    jsr nrp_pop_value
    jcc nrp_parse_body_fail
    cmp #NRP_VALUE_INT
    jne nrp_parse_body_fail
    lda nrp_int_subtract
    bne nrp_parse_int_subtract_value
    clc
    lda nrp_value_lo
    adc nrp_int_rhs_lo
    sta nrp_value_lo
    lda nrp_value_hi
    adc nrp_int_rhs_hi
    sta nrp_value_hi
    jmp nrp_parse_int_arithmetic_push
nrp_parse_int_subtract_value:
    sec
    lda nrp_value_lo
    sbc nrp_int_rhs_lo
    sta nrp_value_lo
    lda nrp_value_hi
    sbc nrp_int_rhs_hi
    sta nrp_value_hi
nrp_parse_int_arithmetic_push:
    lda #NRP_VALUE_INT
    ldx #$00
    jsr nrp_push_value
    jcc nrp_parse_body_fail
    jmp nrp_parse_body_loop
.endif

nrp_parse_call_print:
    jsr nrp_pop_value
    jcc nrp_parse_body_fail
    cmp #NRP_VALUE_INT
    jne nrp_parse_body_fail
    jsr nrp_pop_real_to_operand1
    jcc nrp_parse_body_fail
    jsr nrp_emit_print
    jmp nrp_parse_body_loop

nrp_parse_call_unary:
    jsr nrp_pop_real_to_operand1
    jcc nrp_parse_body_fail
    jsr nrp_mark_nested_operand1
    jsr nrp_allocate_temp
    jcc nrp_parse_body_fail
    stx nrp_dest_index
    jsr nrp_emit_unary
    lda #NRP_VALUE_TEMP
    ldx nrp_dest_index
    jsr nrp_push_value
    jcc nrp_parse_body_fail
    jmp nrp_parse_body_loop

nrp_parse_call_binary:
    jsr nrp_pop_real_to_operand2
    jcc nrp_parse_body_fail
    jsr nrp_pop_real_to_operand1
    jcc nrp_parse_body_fail
    jsr nrp_mark_nested_operands_2
    jsr nrp_allocate_temp
    jcc nrp_parse_body_fail
    stx nrp_dest_index
    jsr nrp_emit_binary
    lda #NRP_VALUE_TEMP
    ldx nrp_dest_index
    jsr nrp_push_value
    jcc nrp_parse_body_fail
    jmp nrp_parse_body_loop

nrp_parse_call_ternary:
    jsr nrp_pop_real_to_operand3
    jcc nrp_parse_body_fail
    jsr nrp_pop_real_to_operand2
    jcc nrp_parse_body_fail
    jsr nrp_pop_real_to_operand1
    jcc nrp_parse_body_fail
    jsr nrp_mark_nested_operands_3
    jsr nrp_allocate_temp
    jcc nrp_parse_body_fail
    stx nrp_dest_index
    jsr nrp_emit_ternary
    lda #NRP_VALUE_TEMP
    ldx nrp_dest_index
    jsr nrp_push_value
    jcc nrp_parse_body_fail
    jmp nrp_parse_body_loop

.if NRP_ENABLE_CONDITION
nrp_parse_call_compare:
    jsr nrp_pop_real_to_operand2
    jcc nrp_parse_body_fail
    jsr nrp_pop_real_to_operand1
    jcc nrp_parse_body_fail
    jsr nrp_mark_nested_operands_2
    jsr nrp_emit_compare
    lda #NRP_VALUE_COMPARE
    ldx #$00
    jsr nrp_push_value
    jcc nrp_parse_body_fail
    jmp nrp_parse_body_loop
.endif

nrp_parse_local_call:
    lda nrp_program_mode
    cmp #NRP_PROGRAM_REAL_FUNCTION
    jne nrp_parse_body_fail
    lda #$00
    sta nrp_preserve_frame
    jsr nrp_read_selector
    jcc nrp_parse_body_fail
    cmp nrp_function_count
    jcs nrp_parse_local_call_rejected
    sta nrp_call_export_index
    lda nrp_proc_index
    cmp nrp_function_count
    beq nrp_parse_local_call_allowed
    jcs nrp_parse_body_fail
    cmp nrp_call_export_index
    jeq nrp_parse_local_call_rejected
    lda #$01
    sta nrp_preserve_frame
    sta nrp_nested
    jsr nrp_record_call_edge
nrp_parse_local_call_allowed:
.if NRP_ENABLE_VARIABLE_ARITY
    ldx nrp_call_export_index
    lda nrp_function_param_count,x
    sta nrp_call_param_count
    cmp #$02
    bne nrp_parse_local_call_first_arg
.endif
    jsr nrp_pop_real_to_operand2
    jcc nrp_parse_body_fail
nrp_parse_local_call_first_arg:
    jsr nrp_pop_real_to_operand1
    jcc nrp_parse_body_fail
    ; A temporary consumed by another local call requires Pass L ownership.
.if NRP_ENABLE_VARIABLE_ARITY
    lda nrp_call_param_count
    cmp #$02
    bne :+
.endif
    jsr nrp_mark_nested_operands_2
.if NRP_ENABLE_VARIABLE_ARITY
    jmp :++
:
    jsr nrp_mark_nested_operand1
:
.endif
    lda nrp_preserve_frame
    beq :+
    jsr nrp_emit_frame_save
:
    lda nrp_operand1_kind
    sta nrp_name_kind
    lda nrp_operand1_index
    sta nrp_name_index
    jsr nrp_emit_push_name_pointer
.if NRP_ENABLE_VARIABLE_ARITY
    lda nrp_call_param_count
    cmp #$02
    bne :+
.endif
    lda nrp_operand2_kind
    sta nrp_name_kind
    lda nrp_operand2_index
    sta nrp_name_index
    jsr nrp_emit_push_name_pointer
.if NRP_ENABLE_VARIABLE_ARITY
:
.endif
    jsr nrp_emit_call_export
    lda nrp_preserve_frame
    beq nrp_parse_local_call_copy_return
    jsr nrp_emit_return_stage
    jsr nrp_emit_frame_restore
    jsr nrp_allocate_temp
    jcc nrp_parse_body_fail
    stx nrp_dest_index
    jsr nrp_emit_staged_return_copy
    jmp nrp_parse_local_call_push_result
nrp_parse_local_call_copy_return:
    jsr nrp_allocate_temp
    jcc nrp_parse_body_fail
    stx nrp_dest_index
    jsr nrp_emit_return_copy
nrp_parse_local_call_push_result:
    lda #NRP_VALUE_TEMP
    ldx nrp_dest_index
    jsr nrp_push_value
    jcc nrp_parse_body_fail
    jmp nrp_parse_body_loop
nrp_parse_local_call_rejected:
    lda #$01
    sta nrp_rejected_call_graph
    jmp nrp_parse_body_fail

nrp_record_call_edge:
    ldx nrp_call_export_index
    lda nrp_call_edge_bits,x
    ldx nrp_proc_index
    ora nrp_call_edges,x
    sta nrp_call_edges,x
    rts

nrp_validate_call_graph:
    lda nrp_call_edges
    and #$02
    beq nrp_validate_call_graph_ok
    lda nrp_call_edges+1
    and #$01
    beq nrp_validate_call_graph_ok
    lda #$01
    sta nrp_rejected_call_graph
    clc
    rts
nrp_validate_call_graph_ok:
    sec
    rts

.if NRP_ENABLE_CONDITION
nrp_parse_relation:
    jsr nrp_pop_value
    jcc nrp_parse_body_fail
    cmp #NRP_VALUE_INT
    jne nrp_parse_body_fail
    stx nrp_literal_index
    jsr nrp_load_literal_word
    jcc nrp_parse_body_fail
    jsr nrp_pop_value
    jcc nrp_parse_body_fail
    cmp #NRP_VALUE_COMPARE
    jne nrp_parse_body_fail
    jsr nrp_map_condition
    jcc nrp_parse_body_fail
    lda #NRP_VALUE_CONDITION
    ldx #$00
    jsr nrp_push_value
    jcc nrp_parse_body_fail
    jmp nrp_parse_body_loop

nrp_map_condition:
    lda nrp_literal_hi
    bne nrp_map_condition_no
    lda nrp_opcode
    cmp #'g'
    bne nrp_map_condition_l
    lda nrp_literal_lo
    beq nrp_map_condition_ge
    cmp #$01
    bne nrp_map_condition_no
    lda #$01
    ldx #$F0
    bne nrp_map_condition_store
nrp_map_condition_ge:
    lda #$02
    ldx #$90
    bne nrp_map_condition_store
nrp_map_condition_l:
    cmp #'l'
    bne nrp_map_condition_q
    lda nrp_literal_lo
    cmp #$01
    beq nrp_map_condition_lt
    cmp #$02
    bne nrp_map_condition_no
    lda #$01
    ldx #$30
    bne nrp_map_condition_store
nrp_map_condition_lt:
    lda #$FF
    ldx #$F0
    bne nrp_map_condition_store
nrp_map_condition_q:
    cmp #'q'
    bne nrp_map_condition_n
    lda nrp_literal_lo
    cmp #$01
    bne nrp_map_condition_no
    lda #$00
    ldx #$F0
    bne nrp_map_condition_store
nrp_map_condition_n:
    cmp #'n'
    bne nrp_map_condition_no
    lda nrp_literal_lo
    cmp #$01
    bne nrp_map_condition_no
    lda #$00
    ldx #$D0
nrp_map_condition_store:
    sta nrp_condition_cmp
    stx nrp_condition_true_branch
    sec
    rts
nrp_map_condition_no:
    clc
    rts
.endif

.if NRP_ENABLE_CONDITION + NRP_ENABLE_WORD_VALUES
nrp_load_literal_word:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp nrp_literal_index
    beq nrp_load_literal_word_no
    bcc nrp_load_literal_word_no
    ldx nrp_literal_index
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta nrp_literal_lo
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta nrp_literal_hi
    sec
    rts
nrp_load_literal_word_no:
    clc
    rts
.endif

.if NRP_ENABLE_FOR
nrp_parse_for_initial_store:
    lda nrp_for_pending
    jne nrp_parse_body_fail
    jsr nrp_read_selector
    jcc nrp_parse_body_fail
    cmp nrp_var_count
    jcs nrp_parse_body_fail
    sta nrp_for_pending_counter
    tax
    lda nrp_var_kind,x
    cmp #NRP_VALUE_WORD
    jne nrp_parse_body_fail
    jsr nrp_pop_value
    jcc nrp_parse_body_fail
.if NRP_ENABLE_FOR_DYNAMIC
    sta nrp_for_pending_initial_kind
    cmp #NRP_VALUE_WORD
    bne nrp_parse_for_initial_constant
    stx nrp_for_pending_initial_index
    lda #$01
    sta nrp_for_dynamic_seen_any
    jmp nrp_parse_for_initial_ready
nrp_parse_for_initial_constant:
.endif
    cmp #NRP_VALUE_INT
    jne nrp_parse_body_fail
    lda nrp_stack_depth
    jne nrp_parse_body_fail
    lda nrp_value_lo
    sta nrp_for_pending_initial_lo
    lda nrp_value_hi
    sta nrp_for_pending_initial_hi
.if NRP_ENABLE_FOR_DYNAMIC
nrp_parse_for_initial_ready:
    lda nrp_stack_depth
    jne nrp_parse_body_fail
.endif
    lda #$01
    sta nrp_for_pending
    jsr nrp_emit_for_initial_store
    jmp nrp_parse_body_loop

nrp_parse_for:
    lda nrp_program_mode
    cmp #NRP_PROGRAM_REAL_FUNCTION
    jne nrp_parse_body_fail
    lda nrp_proc_index
    cmp nrp_function_count
    jcs nrp_parse_body_fail
    lda nrp_for_pending
    jeq nrp_parse_body_fail
    jsr nrp_read_selector
    jcc nrp_parse_body_fail
    cmp nrp_for_pending_counter
    jne nrp_parse_body_fail
    jsr nrp_read_body
    cmp #'+'
    beq nrp_parse_for_direction_ok
    cmp #'-'
    jne nrp_parse_body_fail
nrp_parse_for_direction_ok:
    sta nrp_for_pending_direction
    jsr nrp_pop_value
    jcc nrp_parse_body_fail
    cmp #NRP_VALUE_INT
    jne nrp_parse_body_fail
    lda nrp_value_lo
    sta nrp_for_pending_step_lo
    lda nrp_value_hi
    sta nrp_for_pending_step_hi
    ora nrp_for_pending_step_lo
    jeq nrp_parse_body_fail
    jsr nrp_pop_value
    jcc nrp_parse_body_fail
.if NRP_ENABLE_FOR_DYNAMIC
    sta nrp_for_pending_final_kind
    cmp #NRP_VALUE_WORD
    bne nrp_parse_for_final_constant
    stx nrp_for_pending_final_index
    lda #$01
    sta nrp_for_dynamic_seen_any
    jmp nrp_parse_for_final_ready
nrp_parse_for_final_constant:
.endif
    cmp #NRP_VALUE_INT
    jne nrp_parse_body_fail
    lda nrp_stack_depth
    jne nrp_parse_body_fail
    lda nrp_value_lo
    sta nrp_for_pending_final_lo
    lda nrp_value_hi
    sta nrp_for_pending_final_hi
.if NRP_ENABLE_FOR_DYNAMIC
nrp_parse_for_final_ready:
    lda nrp_stack_depth
    jne nrp_parse_body_fail
.endif
    lda nrp_for_pending_direction
    cmp #'+'
    beq nrp_parse_for_positive_step
    lda nrp_for_pending_step_hi
    jpl nrp_parse_body_fail
    jmp nrp_parse_for_allocate
nrp_parse_for_positive_step:
    lda nrp_for_pending_step_hi
    jmi nrp_parse_body_fail
nrp_parse_for_allocate:
.if NRP_ENABLE_FOR_DYNAMIC
    lda nrp_for_pending_final_kind
    cmp #NRP_VALUE_WORD
    bne nrp_parse_for_allocate_loop
    jsr nrp_allocate_temp
    jcc nrp_parse_body_fail
    stx nrp_for_pending_final_temp
nrp_parse_for_allocate_loop:
.endif
    lda nrp_loop_count
    cmp #NRP_LOOP_MAX
    jcs nrp_parse_body_fail
    lda nrp_loop_depth
    cmp #NRP_LOOP_MAX
    jcs nrp_parse_body_fail
    lda nrp_proc_index
    asl a
    asl a
    clc
    adc nrp_loop_count
    sta nrp_loop_index
    ldy nrp_loop_depth
    sta nrp_loop_stack,y
    inc nrp_loop_count
    inc nrp_loop_depth
    lda #$01
    sta nrp_nested
    ldx nrp_loop_index
    lda #NRP_LOOP_FOR
    sta nrp_loop_kind,x
    lda nrp_for_pending_counter
    sta nrp_for_counter,x
    lda nrp_for_pending_final_lo
    sta nrp_for_final_lo,x
    lda nrp_for_pending_final_hi
    sta nrp_for_final_hi,x
.if NRP_ENABLE_FOR_DYNAMIC
    lda nrp_for_pending_final_kind
    sta nrp_for_final_kind,x
    lda nrp_for_pending_final_index
    sta nrp_for_final_index,x
    lda nrp_for_pending_final_temp
    sta nrp_for_final_temp,x
.endif
    lda nrp_for_pending_step_lo
    sta nrp_for_step_lo,x
    lda nrp_for_pending_step_hi
    sta nrp_for_step_hi,x
    lda nrp_for_pending_direction
    sta nrp_for_direction,x
.if NRP_ENABLE_FOR_DYNAMIC
    jsr nrp_emit_for_final_capture
    ldx nrp_loop_index
.endif
    lda nrp_mode
    bne nrp_parse_for_emit
    lda #$01
    sta nrp_for_seen_any
    sta nrp_loop_seen,x
    lda nrp_code_lo
    sta nrp_loop_start_offset_lo,x
    lda nrp_code_hi
    sta nrp_loop_start_offset_hi,x
nrp_parse_for_emit:
    lda #$00
    sta nrp_for_pending
    jsr nrp_emit_for_condition
    jsr nrp_record_debug_offset
    jcc nrp_parse_body_fail
    jmp nrp_parse_body_loop

nrp_parse_for_end:
    lda nrp_for_pending
    jne nrp_parse_body_fail
    lda nrp_stack_depth
    jne nrp_parse_body_fail
    jsr nrp_load_loop_top
    jcc nrp_parse_body_fail
    ldx nrp_loop_index
    lda nrp_loop_kind,x
    cmp #NRP_LOOP_FOR
    jne nrp_parse_body_fail
    jsr nrp_emit_for_increment
    lda nrp_mode
    bne nrp_parse_for_end_close
    ldx nrp_loop_index
    lda #$01
    sta nrp_loop_has_exit,x
    lda nrp_code_lo
    sta nrp_loop_exit_offset_lo,x
    lda nrp_code_hi
    sta nrp_loop_exit_offset_hi,x
nrp_parse_for_end_close:
    dec nrp_loop_depth
    jmp nrp_parse_body_loop
.endif

.if NRP_ENABLE_LOOP
.if NRP_ENABLE_GENERIC_LOOP
nrp_parse_loop_start:
    lda nrp_program_mode
    cmp #NRP_PROGRAM_REAL_FUNCTION
    jne nrp_parse_body_fail
    lda nrp_proc_index
    cmp nrp_function_count
    jcs nrp_parse_body_fail
    lda nrp_loop_count
    cmp #NRP_LOOP_MAX
    jcs nrp_parse_body_fail
    lda nrp_loop_depth
    cmp #NRP_LOOP_MAX
    jcs nrp_parse_body_fail
    lda nrp_proc_index
    asl a
    asl a
    clc
    adc nrp_loop_count
    sta nrp_loop_index
    ldy nrp_loop_depth
    sta nrp_loop_stack,y
    inc nrp_loop_count
    inc nrp_loop_depth
    lda #$01
    sta nrp_nested
    lda nrp_mode
    bne nrp_parse_loop_start_done
    lda #$01
    sta nrp_loop_seen_any
    ldx nrp_loop_index
    sta nrp_loop_seen,x
    lda #NRP_LOOP_UNKNOWN
    sta nrp_loop_kind,x
    lda nrp_code_lo
    sta nrp_loop_start_offset_lo,x
    lda nrp_code_hi
    sta nrp_loop_start_offset_hi,x
nrp_parse_loop_start_done:
    jmp nrp_parse_body_loop

nrp_parse_loop_while:
    lda #NRP_LOOP_WHILE
    ldy #'z'
    bne nrp_parse_loop_condition

nrp_parse_loop_until:
    lda #NRP_LOOP_UNTIL
    ldy #'b'
nrp_parse_loop_condition:
    sta nrp_byte
    sty nrp_loop_label_kind
    jsr nrp_pop_loop_condition
    jcc nrp_parse_body_fail
    ldx nrp_loop_index
    lda nrp_loop_kind,x
    beq nrp_parse_loop_condition_kind_ok
    cmp nrp_byte
    jne nrp_parse_body_fail
nrp_parse_loop_condition_kind_ok:
    lda nrp_mode
    bne nrp_parse_loop_condition_emit
    lda nrp_byte
    sta nrp_loop_kind,x
nrp_parse_loop_condition_emit:
    jsr nrp_emit_loop_condition_jump
    jmp nrp_parse_body_loop

nrp_parse_loop_until_end:
    jsr nrp_load_loop_top
    jcc nrp_parse_body_fail
    ldx nrp_loop_index
    lda nrp_loop_kind,x
.if NRP_ENABLE_LOOP_EXIT
    cmp #NRP_LOOP_UNTIL
    beq nrp_parse_loop_until_end_until
    cmp #NRP_LOOP_UNKNOWN
    beq nrp_parse_loop_plain_end
    cmp #NRP_LOOP_PLAIN
    jne nrp_parse_body_fail
nrp_parse_loop_plain_end:
    lda nrp_mode
    bne nrp_parse_loop_plain_end_emit
    lda #NRP_LOOP_PLAIN
    sta nrp_loop_kind,x
    lda #$01
    sta nrp_loop_special_seen_any
nrp_parse_loop_plain_end_emit:
    lda #'b'
    sta nrp_loop_label_kind
    jsr nrp_emit_loop_back_jump
    jsr nrp_record_user_exit_target
    jmp nrp_parse_loop_until_end_close
nrp_parse_loop_until_end_until:
    jsr nrp_record_user_exit_target
nrp_parse_loop_until_end_close:
    dec nrp_loop_depth
    jmp nrp_parse_body_loop
.else
    cmp #NRP_LOOP_UNTIL
    jne nrp_parse_body_fail
    dec nrp_loop_depth
    jmp nrp_parse_body_loop
.endif

nrp_parse_loop_while_end:
    jsr nrp_load_loop_top
    jcc nrp_parse_body_fail
    ldx nrp_loop_index
    lda nrp_loop_kind,x
    cmp #NRP_LOOP_WHILE
    jne nrp_parse_body_fail
    lda #'b'
    sta nrp_loop_label_kind
    jsr nrp_emit_loop_back_jump
    lda nrp_mode
    bne nrp_parse_loop_while_end_close
    ldx nrp_loop_index
    lda #$01
    sta nrp_loop_has_exit,x
    lda nrp_code_lo
    sta nrp_loop_exit_offset_lo,x
    lda nrp_code_hi
    sta nrp_loop_exit_offset_hi,x
nrp_parse_loop_while_end_close:
    dec nrp_loop_depth
    jmp nrp_parse_body_loop

.if NRP_ENABLE_LOOP_EXIT
nrp_parse_loop_exit:
    jsr nrp_load_loop_top
    jcc nrp_parse_body_fail
    jsr nrp_read_selector
    jcc nrp_parse_body_fail
    sta nrp_byte
    ldx nrp_loop_index
    lda nrp_byte
    beq nrp_parse_loop_exit_do
    cmp #$01
    jne nrp_parse_body_fail
    lda nrp_loop_kind,x
    cmp #NRP_LOOP_WHILE
    jne nrp_parse_body_fail
    jmp nrp_parse_loop_exit_record
nrp_parse_loop_exit_do:
    lda nrp_loop_kind,x
    cmp #NRP_LOOP_WHILE
    jeq nrp_parse_body_fail
    cmp #NRP_LOOP_UNTIL
    beq nrp_parse_loop_exit_record
    cmp #NRP_LOOP_PLAIN
    beq nrp_parse_loop_exit_record
    cmp #NRP_LOOP_UNKNOWN
    jne nrp_parse_body_fail
nrp_parse_loop_exit_record:
    lda nrp_mode
    bne nrp_parse_loop_exit_emit
    lda #$01
    sta nrp_loop_special_seen_any
    ldx nrp_loop_index
    sta nrp_loop_user_exit,x
nrp_parse_loop_exit_emit:
    lda #'z'
    sta nrp_loop_label_kind
    jsr nrp_emit_loop_back_jump
    jmp nrp_parse_body_loop

nrp_record_user_exit_target:
    lda nrp_mode
    bne nrp_record_user_exit_target_done
    ldx nrp_loop_index
    lda nrp_loop_user_exit,x
    beq nrp_record_user_exit_target_done
    lda #$01
    sta nrp_loop_has_exit,x
    lda nrp_code_lo
    sta nrp_loop_exit_offset_lo,x
    lda nrp_code_hi
    sta nrp_loop_exit_offset_hi,x
nrp_record_user_exit_target_done:
    rts
.endif

nrp_pop_loop_condition:
    jsr nrp_load_loop_top
    bcc nrp_pop_loop_condition_no
    jsr nrp_pop_value
    bcc nrp_pop_loop_condition_no
    cmp #NRP_VALUE_CONDITION
    bne nrp_pop_loop_condition_no
    lda nrp_stack_depth
    bne nrp_pop_loop_condition_no
    sec
    rts
nrp_pop_loop_condition_no:
    clc
    rts
.endif

nrp_load_loop_top:
    lda nrp_loop_depth
    beq nrp_load_loop_top_no
    sec
    sbc #$01
    tay
    lda nrp_loop_stack,y
    sta nrp_loop_index
    sec
    rts
nrp_load_loop_top_no:
    clc
    rts
.endif

.if NRP_ENABLE_CONTROL
.if NRP_ENABLE_MULTI_CONTROL
nrp_parse_if:
    lda nrp_program_mode
    cmp #NRP_PROGRAM_REAL_FUNCTION
    jne nrp_parse_body_fail
    lda nrp_proc_index
    cmp nrp_function_count
    jcs nrp_parse_body_fail
    lda nrp_control_count
    cmp #NRP_CONTROL_MAX
    jcs nrp_parse_body_fail
    lda nrp_control_depth
    cmp #NRP_CONTROL_MAX
    jcs nrp_parse_body_fail
    jsr nrp_pop_value
    jcc nrp_parse_body_fail
    cmp #NRP_VALUE_CONDITION
    jne nrp_parse_body_fail
    lda nrp_stack_depth
    jne nrp_parse_body_fail
    lda nrp_proc_index
    asl a
.if NRP_ENABLE_EXTENDED_CONTROL
    asl a
.endif
    clc
    adc nrp_control_count
    sta nrp_control_index
    ldy nrp_control_depth
    sta nrp_control_stack,y
    lda #$00
    sta nrp_control_else_stack,y
    inc nrp_control_count
    inc nrp_control_depth
    lda #$01
    sta nrp_nested
    jsr nrp_emit_if_branch
    lda nrp_mode
    bne nrp_parse_if_done
    ldx nrp_control_index
    lda #$01
    sta nrp_if_seen,x
    lda nrp_control_count
    cmp #NRP_CONTROL_MIN
    bcc nrp_parse_if_done
    lda #$01
    sta nrp_multi_control_seen
nrp_parse_if_done:
    jmp nrp_parse_body_loop

nrp_parse_else:
    lda nrp_control_depth
    jeq nrp_parse_body_fail
    sec
    sbc #$01
    tay
    lda nrp_control_else_stack,y
    jne nrp_parse_body_fail
    lda nrp_stack_depth
    jne nrp_parse_body_fail
    lda #$01
    sta nrp_control_else_stack,y
    lda nrp_control_stack,y
    sta nrp_control_index
    jsr nrp_emit_else_jump
    lda nrp_mode
    bne nrp_parse_else_done
    ldx nrp_control_index
    lda #$01
    sta nrp_if_has_else,x
    lda nrp_code_lo
    sta nrp_if_false_offset_lo,x
    lda nrp_code_hi
    sta nrp_if_false_offset_hi,x
nrp_parse_else_done:
    jmp nrp_parse_body_loop

nrp_parse_endif:
    lda nrp_control_depth
    jeq nrp_parse_body_fail
    sec
    sbc #$01
    tay
    lda nrp_control_stack,y
    sta nrp_control_index
    lda nrp_stack_depth
    jne nrp_parse_body_fail
    lda nrp_mode
    bne nrp_parse_endif_close
    ldx nrp_control_index
    lda nrp_control_else_stack,y
    beq nrp_parse_endif_store_false
    lda nrp_code_lo
    sta nrp_if_end_offset_lo,x
    lda nrp_code_hi
    sta nrp_if_end_offset_hi,x
    jmp nrp_parse_endif_close
nrp_parse_endif_store_false:
    lda nrp_code_lo
    sta nrp_if_false_offset_lo,x
    lda nrp_code_hi
    sta nrp_if_false_offset_hi,x
nrp_parse_endif_close:
    dec nrp_control_depth
    jmp nrp_parse_body_loop
.else
nrp_parse_if:
    lda nrp_program_mode
    cmp #NRP_PROGRAM_REAL_FUNCTION
    jne nrp_parse_body_fail
    lda nrp_proc_index
    cmp nrp_function_count
    jcs nrp_parse_body_fail
    lda nrp_control_count
    ora nrp_control_depth
    jne nrp_parse_body_fail
    jsr nrp_pop_value
    jcc nrp_parse_body_fail
    cmp #NRP_VALUE_CONDITION
    jne nrp_parse_body_fail
    lda nrp_stack_depth
    jne nrp_parse_body_fail
    lda #$01
    sta nrp_control_count
    sta nrp_control_depth
    sta nrp_nested
    jsr nrp_emit_if_branch
    lda nrp_mode
    bne nrp_parse_if_done
    ldx nrp_proc_index
    lda #$01
    sta nrp_if_seen,x
nrp_parse_if_done:
    jmp nrp_parse_body_loop

nrp_parse_else:
    lda nrp_control_depth
    cmp #$01
    jne nrp_parse_body_fail
    lda nrp_control_else_seen
    jne nrp_parse_body_fail
    lda nrp_stack_depth
    jne nrp_parse_body_fail
    lda #$01
    sta nrp_control_else_seen
    jsr nrp_emit_else_jump
    lda nrp_mode
    bne nrp_parse_else_done
    ldx nrp_proc_index
    lda #$01
    sta nrp_if_has_else,x
    lda nrp_code_lo
    sta nrp_if_false_offset_lo,x
    lda nrp_code_hi
    sta nrp_if_false_offset_hi,x
nrp_parse_else_done:
    jmp nrp_parse_body_loop

nrp_parse_endif:
    lda nrp_control_depth
    cmp #$01
    jne nrp_parse_body_fail
    lda nrp_stack_depth
    jne nrp_parse_body_fail
    lda nrp_mode
    bne nrp_parse_endif_close
    ldx nrp_proc_index
    lda nrp_control_else_seen
    beq nrp_parse_endif_store_false
    lda nrp_code_lo
    sta nrp_if_end_offset_lo,x
    lda nrp_code_hi
    sta nrp_if_end_offset_hi,x
    jmp nrp_parse_endif_close
nrp_parse_endif_store_false:
    lda nrp_code_lo
    sta nrp_if_false_offset_lo,x
    lda nrp_code_hi
    sta nrp_if_false_offset_hi,x
nrp_parse_endif_close:
    lda #$00
    sta nrp_control_depth
    jmp nrp_parse_body_loop
.endif
.endif

nrp_parse_param_bind:
    jsr nrp_read_selector
    jcc nrp_parse_body_fail
    sta nrp_name_index
    lda nrp_param_base
    clc
    adc nrp_param_binds_left
    sec
    sbc #$01
    cmp nrp_name_index
    jne nrp_parse_body_fail
    lda #NRP_VALUE_VAR
    sta nrp_name_kind
    jsr nrp_emit_param_bind
    dec nrp_param_binds_left
    jmp nrp_parse_body_loop

nrp_parse_return:
    lda nrp_pending_load
    ora nrp_pending_store
.if NRP_ENABLE_FOR
    ora nrp_for_pending
.endif
.if NRP_ENABLE_CONTROL
.if NRP_ENABLE_EARLY_RETURN
.else
    ora nrp_control_depth
.endif
.endif
.if NRP_ENABLE_LOOP
    ora nrp_loop_depth
.endif
    jne nrp_parse_body_fail
    lda nrp_program_mode
    cmp #NRP_PROGRAM_REAL_FUNCTION
    bne nrp_parse_main_return
    lda nrp_proc_index
    cmp nrp_function_count
    bcs nrp_parse_main_return
    lda nrp_param_binds_left
    jne nrp_parse_body_fail
    lda nrp_stack_depth
    cmp #$01
    jne nrp_parse_body_fail
    jsr nrp_pop_real_to_operand1
    jcc nrp_parse_body_fail
.if NRP_ENABLE_EARLY_RETURN
    jsr nrp_emit_return_pointer
    jsr nrp_read_body
    tax
    lda nrp_control_depth
    beq nrp_parse_return_terminal
    txa
    jeq nrp_parse_body_fail
    dec nrp_body_pos
    lda #$01
    sta nrp_early_return_seen
    jmp nrp_parse_body_loop
nrp_parse_return_terminal:
    txa
    jne nrp_parse_body_fail
.else
    jsr nrp_read_body
    jne nrp_parse_body_fail
    jsr nrp_emit_return_pointer
.endif
    lda #$01
    sta nrp_saw_return
    sec
    rts
nrp_parse_main_return:
    lda nrp_stack_depth
    jne nrp_parse_body_fail
    jsr nrp_read_body
    jne nrp_parse_body_fail
    jsr nrp_emit_exit
    lda #$01
    sta nrp_saw_return
    sec
    rts
nrp_parse_body_fail:
    clc
    rts

nrp_read_body:
    ldx nrp_proc_index
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    ldy nrp_body_pos
    jsr emit_object_peek_payload_y
    inc nrp_body_pos
    cmp #$00
    rts

nrp_read_selector:
    jsr nrp_read_body
    jmp external_import_selector_to_index

nrp_record_debug_offset:
    ldx nrp_debug_count
    cpx #NRP_DEBUG_MAX
    bcs nrp_record_debug_offset_no
    lda nrp_mode
    bne nrp_record_debug_offset_next
    lda nrp_proc_index
    jsr nrp_offset_debug_x_by_proc_a
    lda nrp_code_lo
    sta nrp_debug_lo,x
    lda nrp_code_hi
    sta nrp_debug_hi,x
nrp_record_debug_offset_next:
    inc nrp_debug_count
    sec
    rts
nrp_record_debug_offset_no:
    clc
    rts

nrp_push_value:
    pha
    ldy nrp_stack_depth
    cpy #NRP_STACK_MAX
    bcs nrp_push_value_no
    pla
    sta nrp_stack_kind,y
    txa
    sta nrp_stack_index,y
.if NRP_ENABLE_WORD_VALUES
    lda nrp_value_lo
    sta nrp_stack_value_lo,y
    lda nrp_value_hi
    sta nrp_stack_value_hi,y
.endif
    inc nrp_stack_depth
    sec
    rts
nrp_push_value_no:
    pla
    clc
    rts

nrp_pop_value:
    lda nrp_stack_depth
    beq nrp_pop_value_no
    dec nrp_stack_depth
    ldy nrp_stack_depth
.if NRP_ENABLE_WORD_VALUES
    lda nrp_stack_value_lo,y
    sta nrp_value_lo
    lda nrp_stack_value_hi,y
    sta nrp_value_hi
.endif
    ldx nrp_stack_index,y
    lda nrp_stack_kind,y
    sec
    rts
nrp_pop_value_no:
    clc
    rts

.if NRP_ENABLE_LITERAL
nrp_pop_real_to_operand1:
    jsr nrp_pop_real_value
    bcc nrp_pop_real_no
    sta nrp_operand1_kind
    stx nrp_operand1_index
    sec
    rts
nrp_pop_real_to_operand2:
    jsr nrp_pop_real_value
    bcc nrp_pop_real_no
    sta nrp_operand2_kind
    stx nrp_operand2_index
    sec
    rts
nrp_pop_real_to_operand3:
    jsr nrp_pop_real_value
    bcc nrp_pop_real_no
    sta nrp_operand3_kind
    stx nrp_operand3_index
    sec
    rts
nrp_pop_real_value:
    jsr nrp_pop_value
    bcc nrp_pop_real_no
    cmp #NRP_VALUE_VAR
    beq nrp_pop_real_value_ok
    cmp #NRP_VALUE_TEMP
    beq nrp_pop_real_value_ok
.if NRP_ENABLE_LITERAL
    cmp #NRP_VALUE_INT
    bne nrp_pop_real_no
    lda nrp_value_lo
    sta nrp_real_literal_b2
    lda nrp_value_hi
    sta nrp_real_literal_b3
    jsr nrp_pop_value
    bcc nrp_pop_real_no
    cmp #NRP_VALUE_INT
    bne nrp_pop_real_no
    lda nrp_value_lo
    sta nrp_real_literal_b0
    lda nrp_value_hi
    sta nrp_real_literal_b1
    jsr nrp_allocate_temp
    bcc nrp_pop_real_no
    stx nrp_dest_index
    jsr nrp_emit_real_literal_temp
    lda #$01
    sta nrp_literal_seen
    sta nrp_nested
    lda #NRP_VALUE_TEMP
    ldx nrp_dest_index
.else
    bne nrp_pop_real_no
.endif
nrp_pop_real_value_ok:
    sec
    rts
.else
nrp_pop_real_to_operand1:
    jsr nrp_pop_value
    bcc nrp_pop_real_no
    cmp #NRP_VALUE_VAR
    beq :+
    cmp #NRP_VALUE_TEMP
    bne nrp_pop_real_no
:
    sta nrp_operand1_kind
    stx nrp_operand1_index
    sec
    rts
nrp_pop_real_to_operand2:
    jsr nrp_pop_value
    bcc nrp_pop_real_no
    cmp #NRP_VALUE_VAR
    beq :+
    cmp #NRP_VALUE_TEMP
    bne nrp_pop_real_no
:
    sta nrp_operand2_kind
    stx nrp_operand2_index
    sec
    rts
nrp_pop_real_to_operand3:
    jsr nrp_pop_value
    bcc nrp_pop_real_no
    cmp #NRP_VALUE_VAR
    beq :+
    cmp #NRP_VALUE_TEMP
    bne nrp_pop_real_no
:
    sta nrp_operand3_kind
    stx nrp_operand3_index
    sec
    rts
.endif
nrp_pop_real_no:
    clc
    rts

nrp_allocate_temp:
    ldx nrp_temp_count
    cpx #NRP_TEMP_MAX
    bcs nrp_allocate_temp_no
    inc nrp_temp_count
    sec
    rts
nrp_allocate_temp_no:
    clc
    rts

nrp_mark_nested_operand1:
    lda nrp_operand1_kind
    cmp #NRP_VALUE_TEMP
    bne nrp_mark_nested_done
    lda #$01
    sta nrp_nested
nrp_mark_nested_done:
    rts
nrp_mark_nested_operands_2:
    jsr nrp_mark_nested_operand1
    lda nrp_operand2_kind
    cmp #NRP_VALUE_TEMP
    bne nrp_mark_nested_done
    lda #$01
    sta nrp_nested
    rts
nrp_mark_nested_operands_3:
    jsr nrp_mark_nested_operands_2
    lda nrp_operand3_kind
    cmp #NRP_VALUE_TEMP
    bne nrp_mark_nested_done
    lda #$01
    sta nrp_nested
    rts

nrp_classify_external_x:
    stx nrp_saved_index
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp nrp_saved_index
    beq nrp_classify_external_no
    bcc nrp_classify_external_no
    ldx nrp_saved_index
    lda #ACTC_OVERLAY_CTX_SET_EXTERNAL_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    ldx #$00
nrp_classify_external_loop:
    lda nrp_helper_name_lo,x
    sta ACTC_OVERLAY_WORK_ZP
    lda nrp_helper_name_hi,x
    sta ACTC_OVERLAY_WORK_ZP+1
    ldy #$00
nrp_classify_external_compare:
    lda (ACTC_OVERLAY_SCAN_ZP),y
    jsr lowercase_ascii_overlay
    cmp (ACTC_OVERLAY_WORK_ZP),y
    bne nrp_classify_external_next
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq nrp_classify_external_yes
    iny
    bne nrp_classify_external_compare
nrp_classify_external_next:
    inx
    cpx #NRP_HELPER_COUNT
    bcc nrp_classify_external_loop
nrp_classify_external_no:
    clc
    rts
nrp_classify_external_yes:
.if NRP_ENABLE_LITERAL
    cpx #(NRP_HELPER_COUNT-2)
    bcc :+
    lda #$01
    sta nrp_angle_seen
    sta nrp_nested
:
.endif
    lda nrp_helper_kind,x
    sec
    rts

.if NRP_ENABLE_LITERAL
nrp_emit_real_literal_temp:
    lda #NRP_VALUE_TEMP
    sta nrp_name_kind
    lda nrp_dest_index
    sta nrp_name_index
    lda #$02
    jsr nrp_emit_pointer
    lda nrp_real_literal_b0
    sta nrp_literal_store_template+3
    lda nrp_real_literal_b1
    sta nrp_literal_store_template+8
    lda nrp_real_literal_b2
    sta nrp_literal_store_template+13
    lda nrp_real_literal_b3
    sta nrp_literal_store_template+18
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_real_literal_temp_machine
    lda #(nrp_literal_store_template_end-nrp_literal_store_template)
    jmp nrp_advance_code
nrp_emit_real_literal_temp_machine:
    lda #$00
    sta nrp_saved_index
nrp_emit_real_literal_temp_machine_loop:
    ldx nrp_saved_index
    lda nrp_literal_store_template,x
    jsr nrp_emit_machine_byte
    inc nrp_saved_index
    lda nrp_saved_index
    cmp #(nrp_literal_store_template_end-nrp_literal_store_template)
    bcc nrp_emit_real_literal_temp_machine_loop
    rts
.endif

nrp_emit_conversion:
    lda #NRP_VALUE_TEMP
    sta nrp_name_kind
    lda nrp_dest_index
    sta nrp_name_index
    lda #$02
    jsr nrp_emit_pointer
.if NRP_ENABLE_FOR
    lda nrp_conversion_source_kind
    cmp #NRP_VALUE_WORD
    beq nrp_emit_conversion_word
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_conversion_literal_machine
    lda #$04
    jsr nrp_advance_code
    jmp nrp_emit_call_import
nrp_emit_conversion_literal_machine:
    lda #$A9
    jsr nrp_emit_machine_byte
    lda nrp_literal_lo
    jsr nrp_emit_machine_byte
    lda #$A2
    jsr nrp_emit_machine_byte
    lda nrp_literal_hi
    jsr nrp_emit_machine_byte
    jmp nrp_emit_call_import
nrp_emit_conversion_word:
    lda #NRP_VALUE_VAR
    sta nrp_name_kind
    lda nrp_conversion_word_index
    sta nrp_name_index
    lda #$06
    jsr nrp_emit_pointer
    lda #<nrp_for_load_ax_template
    ldy #>nrp_for_load_ax_template
    ldx #(nrp_for_load_ax_template_end-nrp_for_load_ax_template)
    jsr nrp_emit_for_const_bytes
    jmp nrp_emit_call_import
.else
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_conversion_machine
    lda #$04
    jsr nrp_advance_code
    jmp nrp_emit_call_import
nrp_emit_conversion_machine:
    ldx nrp_literal_index
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta nrp_literal_lo
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta nrp_literal_hi
    lda #$A9
    jsr nrp_emit_machine_byte
    lda nrp_literal_lo
    jsr nrp_emit_machine_byte
    lda #$A2
    jsr nrp_emit_machine_byte
    lda nrp_literal_hi
    jsr nrp_emit_machine_byte
    jmp nrp_emit_call_import
.endif

nrp_emit_unary:
    jsr nrp_emit_operand1_zp2
    jsr nrp_emit_dest_zp6
    jmp nrp_emit_call_import
nrp_emit_binary:
    jsr nrp_emit_operand1_zp2
    jsr nrp_emit_operand2_zp4
    jsr nrp_emit_dest_zp6
    jmp nrp_emit_call_import
nrp_emit_ternary:
    jsr nrp_emit_operand1_zp2
    jsr nrp_emit_operand2_zp4
    jsr nrp_emit_operand3_zp8
    jsr nrp_emit_dest_zp6
    jmp nrp_emit_call_import
.if NRP_ENABLE_CONDITION
nrp_emit_compare:
    jsr nrp_emit_operand1_zp2
    jsr nrp_emit_operand2_zp4
    jmp nrp_emit_call_import
.endif
nrp_emit_print:
    jsr nrp_emit_operand1_zp2
    jmp nrp_emit_call_import

.if NRP_ENABLE_CONTROL
nrp_emit_if_branch:
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_if_branch_machine
    cmp #NRP_MODE_RELOC
    bne nrp_emit_if_branch_advance
    lda #$05
    ldy #'f'
    jsr nrp_emit_control_reloc_delta
nrp_emit_if_branch_advance:
    lda #$07
    jmp nrp_advance_code
nrp_emit_if_branch_machine:
    lda #$C9
    jsr nrp_emit_machine_byte
    lda nrp_condition_cmp
    jsr nrp_emit_machine_byte
    lda nrp_condition_true_branch
    jsr nrp_emit_machine_byte
    lda #$03
    jsr nrp_emit_machine_byte
    lda #$4C
    jsr nrp_emit_machine_byte
    lda #$00
    jsr nrp_emit_machine_byte
    lda #$00
    jmp nrp_emit_machine_byte

nrp_emit_else_jump:
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_else_jump_machine
    cmp #NRP_MODE_RELOC
    bne nrp_emit_else_jump_advance
    lda #$01
    ldy #'e'
    jsr nrp_emit_control_reloc_delta
nrp_emit_else_jump_advance:
    lda #$03
    jmp nrp_advance_code
nrp_emit_else_jump_machine:
    lda #$4C
    jsr nrp_emit_machine_byte
    lda #$00
    jsr nrp_emit_machine_byte
    lda #$00
    jmp nrp_emit_machine_byte
.endif

.if NRP_ENABLE_LOOP
.if NRP_ENABLE_FOR
nrp_emit_for_initial_store:
.if NRP_ENABLE_FOR_DYNAMIC
    lda nrp_for_pending_initial_kind
    cmp #NRP_VALUE_WORD
    beq nrp_emit_for_initial_store_dynamic
.endif
    lda #NRP_VALUE_VAR
    sta nrp_name_kind
    lda nrp_for_pending_counter
    sta nrp_name_index
    lda #$06
    jsr nrp_emit_pointer
    lda nrp_for_pending_initial_lo
    sta nrp_for_store_template+3
    lda nrp_for_pending_initial_hi
    sta nrp_for_store_template+8
    lda #<nrp_for_store_template
    ldy #>nrp_for_store_template
    ldx #(nrp_for_store_template_end-nrp_for_store_template)
    jmp nrp_emit_for_const_bytes
.if NRP_ENABLE_FOR_DYNAMIC
nrp_emit_for_initial_store_dynamic:
    lda #NRP_VALUE_VAR
    sta nrp_name_kind
    lda nrp_for_pending_initial_index
    sta nrp_name_index
    lda #$04
    jsr nrp_emit_pointer
    lda #NRP_VALUE_VAR
    sta nrp_name_kind
    lda nrp_for_pending_counter
    sta nrp_name_index
    lda #$06
    jsr nrp_emit_pointer
    lda #<nrp_for_word_copy_template
    ldy #>nrp_for_word_copy_template
    ldx #(nrp_for_word_copy_template_end-nrp_for_word_copy_template)
    jmp nrp_emit_for_const_bytes

nrp_emit_for_final_capture:
    ldx nrp_loop_index
    lda nrp_for_final_kind,x
    cmp #NRP_VALUE_WORD
    bne nrp_emit_for_final_capture_done
    lda #NRP_VALUE_VAR
    sta nrp_name_kind
    lda nrp_for_final_index,x
    sta nrp_name_index
    lda #$04
    jsr nrp_emit_pointer
    ldx nrp_loop_index
    lda #NRP_VALUE_TEMP
    sta nrp_name_kind
    lda nrp_for_final_temp,x
    sta nrp_name_index
    lda #$06
    jsr nrp_emit_pointer
    lda #<nrp_for_word_copy_template
    ldy #>nrp_for_word_copy_template
    ldx #(nrp_for_word_copy_template_end-nrp_for_word_copy_template)
    jmp nrp_emit_for_const_bytes
nrp_emit_for_final_capture_done:
    rts
.endif

nrp_emit_for_condition:
    ldx nrp_loop_index
    lda #NRP_VALUE_VAR
    sta nrp_name_kind
    lda nrp_for_counter,x
    sta nrp_name_index
    lda #$06
    jsr nrp_emit_pointer
    ldx nrp_loop_index
    lda nrp_for_direction,x
    cmp #'-'
    beq nrp_emit_for_condition_descending
.if NRP_ENABLE_FOR_DYNAMIC
    lda nrp_for_final_kind,x
    cmp #NRP_VALUE_WORD
    beq nrp_emit_for_condition_ascending_dynamic
    lda #$C9
    sta nrp_for_ascending_template+4
    sta nrp_for_ascending_template+13
.endif
    lda nrp_for_final_hi,x
    sta nrp_for_ascending_template+5
    lda nrp_for_final_lo,x
    sta nrp_for_ascending_template+14
.if NRP_ENABLE_FOR_DYNAMIC
    jmp nrp_emit_for_condition_ascending_ready
nrp_emit_for_condition_ascending_dynamic:
    lda #NRP_VALUE_TEMP
    sta nrp_name_kind
    lda nrp_for_final_temp,x
    sta nrp_name_index
    lda #$04
    jsr nrp_emit_pointer
    lda #$D1
    sta nrp_for_ascending_template+4
    sta nrp_for_ascending_template+13
    lda #$04
    sta nrp_for_ascending_template+5
    sta nrp_for_ascending_template+14
nrp_emit_for_condition_ascending_ready:
.endif
    lda nrp_mode
    cmp #NRP_MODE_RELOC
    bne nrp_emit_for_condition_ascending_bytes
    lda #'z'
    sta nrp_loop_label_kind
    lda #20
    jsr nrp_emit_loop_reloc_delta
nrp_emit_for_condition_ascending_bytes:
    lda #<nrp_for_ascending_template
    ldy #>nrp_for_ascending_template
    ldx #(nrp_for_ascending_template_end-nrp_for_ascending_template)
    jmp nrp_emit_for_const_bytes
nrp_emit_for_condition_descending:
.if NRP_ENABLE_FOR_DYNAMIC
    lda nrp_for_final_kind,x
    cmp #NRP_VALUE_WORD
    beq nrp_emit_for_condition_descending_dynamic
    lda #$C9
    sta nrp_for_descending_template+4
    sta nrp_for_descending_template+13
.endif
    lda nrp_for_final_hi,x
    sta nrp_for_descending_template+5
    lda nrp_for_final_lo,x
    sta nrp_for_descending_template+14
.if NRP_ENABLE_FOR_DYNAMIC
    jmp nrp_emit_for_condition_descending_ready
nrp_emit_for_condition_descending_dynamic:
    lda #NRP_VALUE_TEMP
    sta nrp_name_kind
    lda nrp_for_final_temp,x
    sta nrp_name_index
    lda #$04
    jsr nrp_emit_pointer
    lda #$D1
    sta nrp_for_descending_template+4
    sta nrp_for_descending_template+13
    lda #$04
    sta nrp_for_descending_template+5
    sta nrp_for_descending_template+14
nrp_emit_for_condition_descending_ready:
.endif
    lda nrp_mode
    cmp #NRP_MODE_RELOC
    bne nrp_emit_for_condition_descending_bytes
    lda #'z'
    sta nrp_loop_label_kind
    lda #18
    jsr nrp_emit_loop_reloc_delta
nrp_emit_for_condition_descending_bytes:
    lda #<nrp_for_descending_template
    ldy #>nrp_for_descending_template
    ldx #(nrp_for_descending_template_end-nrp_for_descending_template)
    jmp nrp_emit_for_const_bytes

nrp_emit_for_increment:
    ldx nrp_loop_index
    lda #NRP_VALUE_VAR
    sta nrp_name_kind
    lda nrp_for_counter,x
    sta nrp_name_index
    lda #$06
    jsr nrp_emit_pointer
    ldx nrp_loop_index
    lda nrp_for_step_lo,x
    sta nrp_for_increment_template+6
    lda nrp_for_step_hi,x
    sta nrp_for_increment_template+13
    lda nrp_for_direction,x
    cmp #'-'
    beq nrp_emit_for_increment_descending
    lda #$B0
    bne nrp_emit_for_increment_branch_ready
nrp_emit_for_increment_descending:
    lda #$90
nrp_emit_for_increment_branch_ready:
    sta nrp_for_increment_template+16
    lda nrp_mode
    cmp #NRP_MODE_RELOC
    bne nrp_emit_for_increment_bytes
    lda #'b'
    sta nrp_loop_label_kind
    lda #19
    jsr nrp_emit_loop_reloc_delta
    lda #'z'
    sta nrp_loop_label_kind
    lda #22
    jsr nrp_emit_loop_reloc_delta
nrp_emit_for_increment_bytes:
    lda #<nrp_for_increment_template
    ldy #>nrp_for_increment_template
    ldx #(nrp_for_increment_template_end-nrp_for_increment_template)
    jmp nrp_emit_for_const_bytes

nrp_emit_for_const_bytes:
    sta nrp_for_template_ptr
    sty nrp_for_template_ptr+1
    stx nrp_for_template_len
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_for_const_bytes_machine
    txa
    jmp nrp_advance_code
nrp_emit_for_const_bytes_machine:
    lda #$00
    sta nrp_for_template_index
nrp_emit_for_const_bytes_loop:
    lda nrp_for_template_ptr
    sta ACTC_OVERLAY_WORK_ZP
    lda nrp_for_template_ptr+1
    sta ACTC_OVERLAY_WORK_ZP+1
    ldy nrp_for_template_index
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr nrp_emit_machine_byte
    inc nrp_for_template_index
    lda nrp_for_template_index
    cmp nrp_for_template_len
    bcc nrp_emit_for_const_bytes_loop
    rts
.endif

.if NRP_ENABLE_GENERIC_LOOP
nrp_emit_loop_condition_jump:
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_loop_condition_jump_machine
    cmp #NRP_MODE_RELOC
    bne nrp_emit_loop_condition_jump_advance
    lda #$05
    jsr nrp_emit_loop_reloc_delta
nrp_emit_loop_condition_jump_advance:
    lda #$07
    jmp nrp_advance_code
nrp_emit_loop_condition_jump_machine:
    lda #$C9
    jsr nrp_emit_machine_byte
    lda nrp_condition_cmp
    jsr nrp_emit_machine_byte
    lda nrp_condition_true_branch
    jsr nrp_emit_machine_byte
    lda #$03
    jsr nrp_emit_machine_byte
    lda #$4C
    jsr nrp_emit_machine_byte
    lda #$00
    jsr nrp_emit_machine_byte
    lda #$00
    jmp nrp_emit_machine_byte

nrp_emit_loop_back_jump:
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_loop_back_jump_machine
    cmp #NRP_MODE_RELOC
    bne nrp_emit_loop_back_jump_advance
    lda #$01
    jsr nrp_emit_loop_reloc_delta
nrp_emit_loop_back_jump_advance:
    lda #$03
    jmp nrp_advance_code
nrp_emit_loop_back_jump_machine:
    lda #$4C
    jsr nrp_emit_machine_byte
    lda #$00
    jsr nrp_emit_machine_byte
    lda #$00
    jmp nrp_emit_machine_byte
.endif
.endif

nrp_emit_param_bind:
    ; Preserve JSR's return address while reverse-popping caller argument pointers.
    lda nrp_param_binds_left
.if NRP_ENABLE_VARIABLE_ARITY
    cmp nrp_param_count
.else
    cmp #$02
.endif
    bne :+
    jsr nrp_emit_save_return
:
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_param_bind_machine
    cmp #NRP_MODE_RELOC
    bne nrp_emit_param_bind_advance
    lda #$0B
    jsr nrp_emit_named_word_reloc_delta
nrp_emit_param_bind_advance:
    lda #$10
    jsr nrp_advance_code
    jmp nrp_emit_param_bind_restore
nrp_emit_param_bind_machine:
    lda #$00
    sta nrp_saved_index
nrp_emit_param_bind_machine_loop:
    ldx nrp_saved_index
    lda nrp_param_bind_template,x
    jsr nrp_emit_machine_byte
    inc nrp_saved_index
    lda nrp_saved_index
    cmp #$10
    bcc nrp_emit_param_bind_machine_loop
nrp_emit_param_bind_restore:
    lda nrp_param_binds_left
    cmp #$01
    bne :+
    jsr nrp_emit_restore_return
:
    rts

nrp_emit_save_return:
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_save_return_machine
    lda #$05
    jmp nrp_advance_code
nrp_emit_save_return_machine:
    lda #$00
    sta nrp_saved_index
nrp_emit_save_return_machine_loop:
    ldx nrp_saved_index
    lda nrp_save_return_template,x
    jsr nrp_emit_machine_byte
    inc nrp_saved_index
    lda nrp_saved_index
    cmp #$05
    bcc nrp_emit_save_return_machine_loop
    rts

nrp_emit_restore_return:
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_restore_return_machine
    lda #$05
    jmp nrp_advance_code
nrp_emit_restore_return_machine:
    lda #$00
    sta nrp_saved_index
nrp_emit_restore_return_machine_loop:
    ldx nrp_saved_index
    lda nrp_restore_return_template,x
    jsr nrp_emit_machine_byte
    inc nrp_saved_index
    lda nrp_saved_index
    cmp #$05
    bcc nrp_emit_restore_return_machine_loop
    rts

nrp_emit_frame_save:
    lda nrp_param_base
    sta nrp_frame_name_index
    ldx nrp_proc_index
    lda nrp_function_local_count,x
    clc
.if NRP_ENABLE_VARIABLE_ARITY
    adc nrp_function_param_count,x
.else
    adc #$02
.endif
    sta nrp_frame_slots_left
nrp_emit_frame_save_var_loop:
    lda #NRP_VALUE_VAR
    sta nrp_name_kind
    lda nrp_frame_name_index
    sta nrp_name_index
    jsr nrp_emit_frame_save_slot
    inc nrp_frame_name_index
    dec nrp_frame_slots_left
    bne nrp_emit_frame_save_var_loop
    lda nrp_temp_count
    sec
    sbc nrp_temp_base
    sta nrp_frame_slots_left
    beq nrp_emit_frame_save_done
    lda nrp_temp_base
    sta nrp_frame_name_index
nrp_emit_frame_save_temp_loop:
    lda #NRP_VALUE_TEMP
    sta nrp_name_kind
    lda nrp_frame_name_index
    sta nrp_name_index
    jsr nrp_emit_frame_save_slot
    inc nrp_frame_name_index
    dec nrp_frame_slots_left
    bne nrp_emit_frame_save_temp_loop
nrp_emit_frame_save_done:
    rts

nrp_emit_frame_save_slot:
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_frame_save_slot_machine
    cmp #NRP_MODE_RELOC
    bne nrp_emit_frame_save_slot_advance
    lda #$03
    jsr nrp_emit_named_word_reloc_delta
nrp_emit_frame_save_slot_advance:
    lda #$09
    jmp nrp_advance_code
nrp_emit_frame_save_slot_machine:
    ldx #nrp_frame_save_template-nrp_frame_save_template
    lda #nrp_return_stage_template-nrp_frame_save_template
    jmp nrp_emit_frame_template

nrp_emit_return_stage:
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_return_stage_machine
    lda #$0E
    jmp nrp_advance_code
nrp_emit_return_stage_machine:
    ldx #nrp_return_stage_template-nrp_frame_save_template
    lda #nrp_frame_restore_template-nrp_frame_save_template
    jmp nrp_emit_frame_template

nrp_emit_frame_restore:
    lda nrp_temp_count
    sec
    sbc nrp_temp_base
    sta nrp_frame_slots_left
    beq nrp_emit_frame_restore_vars
    lda nrp_temp_count
    sec
    sbc #$01
    sta nrp_frame_name_index
nrp_emit_frame_restore_temp_loop:
    lda #NRP_VALUE_TEMP
    sta nrp_name_kind
    lda nrp_frame_name_index
    sta nrp_name_index
    jsr nrp_emit_frame_restore_slot
    dec nrp_frame_name_index
    dec nrp_frame_slots_left
    bne nrp_emit_frame_restore_temp_loop
nrp_emit_frame_restore_vars:
    ldx nrp_proc_index
    lda nrp_function_local_count,x
    clc
.if NRP_ENABLE_VARIABLE_ARITY
    adc nrp_function_param_count,x
.else
    adc #$02
.endif
    sta nrp_frame_slots_left
    clc
    adc nrp_param_base
    sec
    sbc #$01
    sta nrp_frame_name_index
nrp_emit_frame_restore_var_loop:
    lda #NRP_VALUE_VAR
    sta nrp_name_kind
    lda nrp_frame_name_index
    sta nrp_name_index
    jsr nrp_emit_frame_restore_slot
    dec nrp_frame_name_index
    dec nrp_frame_slots_left
    bne nrp_emit_frame_restore_var_loop
    rts

nrp_emit_frame_restore_slot:
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_frame_restore_slot_machine
    cmp #NRP_MODE_RELOC
    bne nrp_emit_frame_restore_slot_advance
    lda #$04
    jsr nrp_emit_named_word_reloc_delta
nrp_emit_frame_restore_slot_advance:
    lda #$0B
    jmp nrp_advance_code
nrp_emit_frame_restore_slot_machine:
    ldx #nrp_frame_restore_template-nrp_frame_save_template
    lda #nrp_staged_return_copy_template-nrp_frame_save_template
    jmp nrp_emit_frame_template

nrp_emit_staged_return_copy:
    lda #NRP_VALUE_TEMP
    sta nrp_name_kind
    lda nrp_dest_index
    sta nrp_name_index
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_staged_return_copy_machine
    cmp #NRP_MODE_RELOC
    bne nrp_emit_staged_return_copy_advance
    lda #$06
    jsr nrp_emit_named_word_reloc_delta
nrp_emit_staged_return_copy_advance:
    lda #$0B
    jmp nrp_advance_code
nrp_emit_staged_return_copy_machine:
    ldx #nrp_staged_return_copy_template-nrp_frame_save_template
    lda #nrp_frame_templates_end-nrp_frame_save_template
nrp_emit_frame_template:
    sta nrp_frame_template_end
nrp_emit_frame_template_loop:
    txa
    pha
    lda nrp_frame_save_template,x
    jsr nrp_emit_machine_byte
    pla
    tax
    inx
    cpx nrp_frame_template_end
    bcc nrp_emit_frame_template_loop
    rts

nrp_emit_push_name_pointer:
    ; Arguments are low/high pointers; the callee binds them in reverse order.
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_push_name_pointer_machine
    cmp #NRP_MODE_RELOC
    bne nrp_emit_push_name_pointer_advance
    lda #$01
    ldy #'l'
    jsr nrp_emit_named_byte_reloc_delta
    lda #$04
    ldy #'h'
    jsr nrp_emit_named_byte_reloc_delta
nrp_emit_push_name_pointer_advance:
    lda #$06
    jmp nrp_advance_code
nrp_emit_push_name_pointer_machine:
    lda #$00
    sta nrp_saved_index
nrp_emit_push_name_pointer_machine_loop:
    ldx nrp_saved_index
    lda nrp_push_pointer_template,x
    jsr nrp_emit_machine_byte
    inc nrp_saved_index
    lda nrp_saved_index
    cmp #$06
    bcc nrp_emit_push_name_pointer_machine_loop
    rts

nrp_emit_call_export:
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_call_export_machine
    cmp #NRP_MODE_RELOC
    bne nrp_emit_call_export_advance
    lda #$01
    jsr nrp_emit_export_reloc_delta
nrp_emit_call_export_advance:
    lda #$03
    jmp nrp_advance_code
nrp_emit_call_export_machine:
    lda #$20
    jsr nrp_emit_machine_byte
    lda #$00
    jsr nrp_emit_machine_byte
    lda #$00
    jmp nrp_emit_machine_byte

nrp_emit_return_copy:
    lda #NRP_VALUE_TEMP
    sta nrp_name_kind
    lda nrp_dest_index
    sta nrp_name_index
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_return_copy_machine
    cmp #NRP_MODE_RELOC
    bne nrp_emit_return_copy_advance
    lda #$09
    jsr nrp_emit_named_word_reloc_delta
nrp_emit_return_copy_advance:
    lda #$0E
    jmp nrp_advance_code
nrp_emit_return_copy_machine:
    lda #$00
    sta nrp_saved_index
nrp_emit_return_copy_machine_loop:
    ldx nrp_saved_index
    lda nrp_return_copy_template,x
    jsr nrp_emit_machine_byte
    inc nrp_saved_index
    lda nrp_saved_index
    cmp #$0E
    bcc nrp_emit_return_copy_machine_loop
    rts

nrp_emit_return_pointer:
    lda nrp_operand1_kind
    sta nrp_name_kind
    lda nrp_operand1_index
    sta nrp_name_index
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_return_pointer_machine
    cmp #NRP_MODE_RELOC
    bne nrp_emit_return_pointer_advance
    lda #$01
    ldy #'l'
    jsr nrp_emit_named_byte_reloc_delta
    lda #$03
    ldy #'h'
    jsr nrp_emit_named_byte_reloc_delta
nrp_emit_return_pointer_advance:
    lda #$05
    jmp nrp_advance_code
nrp_emit_return_pointer_machine:
    lda #$00
    sta nrp_saved_index
nrp_emit_return_pointer_machine_loop:
    ldx nrp_saved_index
    lda nrp_return_pointer_template,x
    jsr nrp_emit_machine_byte
    inc nrp_saved_index
    lda nrp_saved_index
    cmp #$05
    bcc nrp_emit_return_pointer_machine_loop
    rts

nrp_emit_operand1_zp2:
    lda nrp_operand1_kind
    sta nrp_name_kind
    lda nrp_operand1_index
    sta nrp_name_index
    lda #$02
    jmp nrp_emit_pointer
nrp_emit_operand2_zp4:
    lda nrp_operand2_kind
    sta nrp_name_kind
    lda nrp_operand2_index
    sta nrp_name_index
    lda #$04
    jmp nrp_emit_pointer
nrp_emit_operand3_zp8:
    lda nrp_operand3_kind
    sta nrp_name_kind
    lda nrp_operand3_index
    sta nrp_name_index
    lda #$08
    jmp nrp_emit_pointer
nrp_emit_dest_zp6:
    lda #NRP_VALUE_TEMP
    sta nrp_name_kind
    lda nrp_dest_index
    sta nrp_name_index
    lda #$06
    jmp nrp_emit_pointer

nrp_emit_pointer:
    sta nrp_pointer_zp
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_pointer_machine
    cmp #NRP_MODE_RELOC
    bne nrp_emit_pointer_advance
    lda #$01
    ldy #'l'
    jsr nrp_emit_named_byte_reloc_delta
    lda #$05
    ldy #'h'
    jsr nrp_emit_named_byte_reloc_delta
nrp_emit_pointer_advance:
    lda #$08
    jmp nrp_advance_code
nrp_emit_pointer_machine:
    lda #$A9
    jsr nrp_emit_machine_byte
    lda #$00
    jsr nrp_emit_machine_byte
    lda #$85
    jsr nrp_emit_machine_byte
    lda nrp_pointer_zp
    jsr nrp_emit_machine_byte
    lda #$A9
    jsr nrp_emit_machine_byte
    lda #$00
    jsr nrp_emit_machine_byte
    lda #$85
    jsr nrp_emit_machine_byte
    lda nrp_pointer_zp
    clc
    adc #$01
    jmp nrp_emit_machine_byte

nrp_emit_call_import:
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_call_import_machine
    cmp #NRP_MODE_RELOC
    bne nrp_emit_call_import_advance
    lda #$01
    jsr nrp_emit_import_reloc_delta
nrp_emit_call_import_advance:
    lda #$03
    jmp nrp_advance_code
nrp_emit_call_import_machine:
    lda #$20
    jsr nrp_emit_machine_byte
    lda #$00
    jsr nrp_emit_machine_byte
    lda #$00
    jmp nrp_emit_machine_byte

nrp_emit_copy_operand1_to_name:
    lda nrp_name_kind
    sta nrp_dest_kind
    lda nrp_name_index
    sta nrp_dest_name_index
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_copy_machine
    cmp #NRP_MODE_RELOC
    bne nrp_emit_copy_advance
    lda nrp_operand1_kind
    sta nrp_name_kind
    lda nrp_operand1_index
    sta nrp_name_index
    lda #$03
    jsr nrp_emit_named_word_reloc_delta
    lda nrp_dest_kind
    sta nrp_name_kind
    lda nrp_dest_name_index
    sta nrp_name_index
    lda #$06
    jsr nrp_emit_named_word_reloc_delta
nrp_emit_copy_advance:
    lda #$0B
    jmp nrp_advance_code
nrp_emit_copy_machine:
    lda #$00
    sta nrp_saved_index
nrp_emit_copy_machine_loop:
    ldx nrp_saved_index
    lda nrp_copy_template,x
    jsr nrp_emit_machine_byte
    inc nrp_saved_index
    lda nrp_saved_index
    cmp #$0B
    bcc nrp_emit_copy_machine_loop
    rts

nrp_emit_exit:
    lda nrp_mode
    cmp #NRP_MODE_MACHINE
    beq nrp_emit_exit_machine
    lda #$10
    jmp nrp_advance_code
nrp_emit_exit_machine:
    lda #$00
    sta nrp_saved_index
nrp_emit_exit_machine_loop:
    ldx nrp_saved_index
    lda nrp_exit_template,x
    jsr nrp_emit_machine_byte
    inc nrp_saved_index
    lda nrp_saved_index
    cmp #$10
    bcc nrp_emit_exit_machine_loop
    rts

nrp_emit_machine_byte:
    sta nrp_byte
    lda #' '
    jsr emit_char_overlay
    lda nrp_byte
    jsr emit_hex_byte_overlay
    lda #$01
    jmp nrp_advance_code

nrp_advance_code:
    clc
    adc nrp_code_lo
    sta nrp_code_lo
    bcc :+
    inc nrp_code_hi
:
    rts

native_real_postfix_emit_debug_offset:
    ldx body_debug_index_data
    lda entry_index_data
    jsr nrp_offset_debug_x_by_proc_a
    lda nrp_debug_lo,x
    ldy nrp_debug_hi,x
    jmp emit_word_decimal

nrp_offset_debug_x_by_proc_a:
    tay
    beq nrp_offset_debug_x_done
    txa
nrp_offset_debug_x_loop:
    clc
    adc #NRP_DEBUG_MAX
    dey
    bne nrp_offset_debug_x_loop
    tax
nrp_offset_debug_x_done:
    rts

native_real_postfix_emit_export_list:
    lda nrp_program_mode
    cmp #NRP_PROGRAM_REAL_FUNCTION
    beq native_real_postfix_emit_function_exports
    ldx #$00
    jsr nrp_emit_root_export
    jmp native_real_postfix_emit_data_exports
native_real_postfix_emit_function_exports:
    ldx nrp_function_count
    jsr nrp_emit_root_export
    lda #$00
    sta nrp_function_index
native_real_postfix_emit_function_export_loop:
    lda nrp_function_index
    cmp nrp_function_count
.if NRP_ENABLE_CONTROL
    beq native_real_postfix_emit_control_exports
.elseif NRP_ENABLE_LOOP
    beq native_real_postfix_emit_loop_exports
.else
    beq native_real_postfix_emit_data_exports
.endif
    tax
    jsr nrp_emit_function_export
    inc nrp_function_index
    jmp native_real_postfix_emit_function_export_loop
.if NRP_ENABLE_CONTROL
native_real_postfix_emit_control_exports:
.if NRP_ENABLE_MULTI_CONTROL
    lda #$00
    sta nrp_function_index
native_real_postfix_emit_control_export_function_loop:
    lda nrp_function_index
    cmp nrp_function_count
    beq native_real_postfix_emit_data_exports
    sta nrp_proc_index
    lda #$00
    sta nrp_control_ordinal
native_real_postfix_emit_control_export_loop:
    lda nrp_control_ordinal
    cmp #NRP_CONTROL_MAX
    beq native_real_postfix_emit_control_export_next_function
    lda nrp_function_index
    asl a
.if NRP_ENABLE_EXTENDED_CONTROL
    asl a
.endif
    clc
    adc nrp_control_ordinal
    sta nrp_control_index
    tax
    lda nrp_if_seen,x
    beq native_real_postfix_emit_control_export_next
    lda #'f'
    sta nrp_control_label_kind
    lda nrp_if_false_offset_lo,x
    sta nrp_export_offset_lo
    lda nrp_if_false_offset_hi,x
    sta nrp_export_offset_hi
    jsr nrp_emit_control_export
    ldx nrp_control_index
    lda nrp_if_has_else,x
    beq native_real_postfix_emit_control_export_next
    lda #'e'
    sta nrp_control_label_kind
    lda nrp_if_end_offset_lo,x
    sta nrp_export_offset_lo
    lda nrp_if_end_offset_hi,x
    sta nrp_export_offset_hi
    jsr nrp_emit_control_export
native_real_postfix_emit_control_export_next:
    inc nrp_control_ordinal
    jmp native_real_postfix_emit_control_export_loop
native_real_postfix_emit_control_export_next_function:
    inc nrp_function_index
    jmp native_real_postfix_emit_control_export_function_loop
.else
    lda #$00
    sta nrp_function_index
native_real_postfix_emit_control_export_loop:
    lda nrp_function_index
    cmp nrp_function_count
    beq native_real_postfix_emit_data_exports
    tax
    stx nrp_proc_index
    lda nrp_if_seen,x
    beq native_real_postfix_emit_control_export_next
    lda #'f'
    sta nrp_control_label_kind
    lda nrp_if_false_offset_lo,x
    sta nrp_export_offset_lo
    lda nrp_if_false_offset_hi,x
    sta nrp_export_offset_hi
    jsr nrp_emit_control_export
    ldx nrp_function_index
    lda nrp_if_has_else,x
    beq native_real_postfix_emit_control_export_next
    lda #'e'
    sta nrp_control_label_kind
    lda nrp_if_end_offset_lo,x
    sta nrp_export_offset_lo
    lda nrp_if_end_offset_hi,x
    sta nrp_export_offset_hi
    jsr nrp_emit_control_export
native_real_postfix_emit_control_export_next:
    inc nrp_function_index
    jmp native_real_postfix_emit_control_export_loop
.endif
.endif
.if NRP_ENABLE_LOOP
native_real_postfix_emit_loop_exports:
    lda #$00
    sta nrp_function_index
native_real_postfix_emit_loop_export_function_loop:
    lda nrp_function_index
    cmp nrp_function_count
    beq native_real_postfix_emit_data_exports
    sta nrp_proc_index
    lda #$00
    sta nrp_loop_ordinal
native_real_postfix_emit_loop_export_loop:
    lda nrp_loop_ordinal
    cmp #NRP_LOOP_MAX
    beq native_real_postfix_emit_loop_export_next_function
    lda nrp_function_index
    asl a
    asl a
    clc
    adc nrp_loop_ordinal
    sta nrp_loop_index
    tax
    lda nrp_loop_seen,x
    beq native_real_postfix_emit_loop_export_next
    lda #'b'
    sta nrp_loop_label_kind
    lda nrp_loop_start_offset_lo,x
    sta nrp_export_offset_lo
    lda nrp_loop_start_offset_hi,x
    sta nrp_export_offset_hi
    jsr nrp_emit_loop_export
    ldx nrp_loop_index
    lda nrp_loop_has_exit,x
    beq native_real_postfix_emit_loop_export_next
    lda #'z'
    sta nrp_loop_label_kind
    lda nrp_loop_exit_offset_lo,x
    sta nrp_export_offset_lo
    lda nrp_loop_exit_offset_hi,x
    sta nrp_export_offset_hi
    jsr nrp_emit_loop_export
native_real_postfix_emit_loop_export_next:
    inc nrp_loop_ordinal
    jmp native_real_postfix_emit_loop_export_loop
native_real_postfix_emit_loop_export_next_function:
    inc nrp_function_index
    jmp native_real_postfix_emit_loop_export_function_loop
.endif
native_real_postfix_emit_data_exports:
    lda nrp_code_size_lo
    sta nrp_export_offset_lo
    lda nrp_code_size_hi
    sta nrp_export_offset_hi
    jsr nrp_emit_data_export
    lda #NRP_VALUE_VAR
    sta nrp_name_kind
    lda #$00
    sta nrp_name_index
    jmp native_real_postfix_emit_var_export_loop

nrp_emit_root_export:
    stx nrp_saved_index
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx nrp_saved_index
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr emit_lower_scan_zp_string
    lda #' '
    jsr emit_char_overlay
    lda #$00
    tay
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda nrp_root_size_lo
    ldy nrp_root_size_hi
    jsr emit_word_decimal
    jsr emit_newline
    rts

nrp_emit_function_export:
    stx nrp_saved_index
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx nrp_saved_index
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr emit_lower_scan_zp_string
    lda #' '
    jsr emit_char_overlay
    ldx nrp_saved_index
    lda nrp_function_code_start_lo,x
    ldy nrp_function_code_start_hi,x
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    ldx nrp_saved_index
    lda nrp_function_code_size_lo,x
    ldy nrp_function_code_size_hi,x
    jsr emit_word_decimal
    jmp emit_newline

.if NRP_ENABLE_CONTROL
nrp_emit_control_export:
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr nrp_emit_control_name
    lda #' '
    jsr emit_char_overlay
    lda nrp_export_offset_lo
    ldy nrp_export_offset_hi
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda #$01
    ldy #$00
    jsr emit_word_decimal
    jmp emit_newline
.endif
.if NRP_ENABLE_LOOP
nrp_emit_loop_export:
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr nrp_emit_loop_name
    lda #' '
    jsr emit_char_overlay
    lda nrp_export_offset_lo
    ldy nrp_export_offset_hi
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda #$01
    ldy #$00
    jsr emit_word_decimal
    jmp emit_newline
.endif

native_real_postfix_emit_var_export_loop:
    lda nrp_name_index
    cmp nrp_var_count
    beq native_real_postfix_emit_temp_export_start
    jsr nrp_emit_internal_export
    inc nrp_name_index
    jsr nrp_advance_export_offset_four
    jmp native_real_postfix_emit_var_export_loop
native_real_postfix_emit_temp_export_start:
    lda #NRP_VALUE_TEMP
    sta nrp_name_kind
    lda #$00
    sta nrp_name_index
native_real_postfix_emit_temp_export_loop:
    lda nrp_name_index
    cmp nrp_temp_total
    beq native_real_postfix_emit_export_done
    jsr nrp_emit_internal_export
    inc nrp_name_index
    jsr nrp_advance_export_offset_four
    jmp native_real_postfix_emit_temp_export_loop
native_real_postfix_emit_export_done:
    clc
    rts

nrp_emit_data_export:
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #<nrp_name_data
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>nrp_name_data
    sta ACTC_OVERLAY_SCAN_ZP+1
    jsr emit_scan_zp_string
    lda #' '
    jsr emit_char_overlay
    lda nrp_export_offset_lo
    ldy nrp_export_offset_hi
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda nrp_var_count
    asl a
    asl a
    ldy #$00
    jsr emit_word_decimal
    jmp emit_newline

nrp_emit_internal_export:
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr nrp_emit_internal_name
    lda #' '
    jsr emit_char_overlay
    lda nrp_export_offset_lo
    ldy nrp_export_offset_hi
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda #$04
    ldy #$00
    jsr emit_word_decimal
    jmp emit_newline
nrp_advance_export_offset_four:
    lda nrp_export_offset_lo
    clc
    adc #$04
    sta nrp_export_offset_lo
    bcc :+
    inc nrp_export_offset_hi
:
    rts

native_real_postfix_emit_body_marker_list:
    jsr nrp_emit_root_body_marker
    lda nrp_program_mode
    cmp #NRP_PROGRAM_REAL_FUNCTION
    bne native_real_postfix_emit_body_data
    lda #$00
    sta nrp_function_index
native_real_postfix_emit_function_body_marker_loop:
    lda nrp_function_index
    cmp nrp_function_count
.if NRP_ENABLE_CONTROL
    beq native_real_postfix_emit_control_body_markers
.elseif NRP_ENABLE_LOOP
    beq native_real_postfix_emit_loop_body_markers
.else
    beq native_real_postfix_emit_body_data
.endif
    jsr nrp_emit_root_body_marker
    inc nrp_function_index
    jmp native_real_postfix_emit_function_body_marker_loop
.if NRP_ENABLE_CONTROL
native_real_postfix_emit_control_body_markers:
.if NRP_ENABLE_MULTI_CONTROL
    lda #$00
    sta nrp_function_index
native_real_postfix_emit_control_body_marker_function_loop:
    lda nrp_function_index
    cmp nrp_function_count
    beq native_real_postfix_emit_body_data
    lda #$00
    sta nrp_control_ordinal
native_real_postfix_emit_control_body_marker_loop:
    lda nrp_control_ordinal
    cmp #NRP_CONTROL_MAX
    beq native_real_postfix_emit_control_body_marker_next_function
    lda nrp_function_index
    asl a
.if NRP_ENABLE_EXTENDED_CONTROL
    asl a
.endif
    clc
    adc nrp_control_ordinal
    sta nrp_control_index
    tax
    lda nrp_if_seen,x
    beq native_real_postfix_emit_control_body_marker_next
    jsr emit_machine_body_marker_line
    ldx nrp_control_index
    lda nrp_if_has_else,x
    beq native_real_postfix_emit_control_body_marker_next
    jsr emit_machine_body_marker_line
native_real_postfix_emit_control_body_marker_next:
    inc nrp_control_ordinal
    jmp native_real_postfix_emit_control_body_marker_loop
native_real_postfix_emit_control_body_marker_next_function:
    inc nrp_function_index
    jmp native_real_postfix_emit_control_body_marker_function_loop
.else
    lda #$00
    sta nrp_function_index
native_real_postfix_emit_control_body_marker_loop:
    lda nrp_function_index
    cmp nrp_function_count
    beq native_real_postfix_emit_body_data
    tax
    lda nrp_if_seen,x
    beq native_real_postfix_emit_control_body_marker_next
    jsr emit_machine_body_marker_line
    ldx nrp_function_index
    lda nrp_if_has_else,x
    beq native_real_postfix_emit_control_body_marker_next
    jsr emit_machine_body_marker_line
native_real_postfix_emit_control_body_marker_next:
    inc nrp_function_index
    jmp native_real_postfix_emit_control_body_marker_loop
.endif
.endif
.if NRP_ENABLE_LOOP
native_real_postfix_emit_loop_body_markers:
    lda #$00
    sta nrp_function_index
native_real_postfix_emit_loop_body_marker_function_loop:
    lda nrp_function_index
    cmp nrp_function_count
    beq native_real_postfix_emit_body_data
    lda #$00
    sta nrp_loop_ordinal
native_real_postfix_emit_loop_body_marker_loop:
    lda nrp_loop_ordinal
    cmp #NRP_LOOP_MAX
    beq native_real_postfix_emit_loop_body_marker_next_function
    lda nrp_function_index
    asl a
    asl a
    clc
    adc nrp_loop_ordinal
    sta nrp_loop_index
    tax
    lda nrp_loop_seen,x
    beq native_real_postfix_emit_loop_body_marker_next
    jsr emit_machine_body_marker_line
    ldx nrp_loop_index
    lda nrp_loop_has_exit,x
    beq native_real_postfix_emit_loop_body_marker_next
    jsr emit_machine_body_marker_line
native_real_postfix_emit_loop_body_marker_next:
    inc nrp_loop_ordinal
    jmp native_real_postfix_emit_loop_body_marker_loop
native_real_postfix_emit_loop_body_marker_next_function:
    inc nrp_function_index
    jmp native_real_postfix_emit_loop_body_marker_function_loop
.endif
native_real_postfix_emit_body_data:
    lda nrp_data_slots
    clc
    adc #$01
    sta nrp_saved_index
    jmp native_real_postfix_emit_data_body_loop

nrp_emit_root_body_marker:
    lda #'b'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #$00
    sta nrp_saved_index
native_real_postfix_emit_body_import_loop:
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp nrp_saved_index
    beq native_real_postfix_emit_body_machine
    lda #'u'
    jsr emit_char_overlay
    lda nrp_saved_index
    jsr emit_object_selector_overlay
    inc nrp_saved_index
    jmp native_real_postfix_emit_body_import_loop
native_real_postfix_emit_body_machine:
    lda #'M'
    jsr emit_char_overlay
    jmp emit_newline
native_real_postfix_emit_data_body_loop:
    lda nrp_saved_index
    beq native_real_postfix_emit_body_done
    jsr emit_machine_body_marker_line
    dec nrp_saved_index
    jmp native_real_postfix_emit_data_body_loop
native_real_postfix_emit_body_done:
    clc
    rts

native_real_postfix_emit_machine_code_list:
    lda #'m'
    jsr emit_char_overlay
    lda #NRP_MODE_MACHINE
    jsr nrp_parse_program
    bcc native_real_postfix_emit_machine_fail
    lda nrp_data_slots
    asl a
    asl a
    sta nrp_saved_index
native_real_postfix_emit_machine_zero_loop:
    lda nrp_saved_index
    beq native_real_postfix_emit_machine_newline
    lda #$00
    jsr nrp_emit_machine_byte
    dec nrp_saved_index
    jmp native_real_postfix_emit_machine_zero_loop
native_real_postfix_emit_machine_newline:
    jsr emit_newline
    lda #NRP_MODE_RELOC
    jsr nrp_parse_program
    bcc native_real_postfix_emit_machine_fail
    clc
    rts
native_real_postfix_emit_machine_fail:
    sec
    rts

nrp_parse_program:
    sta nrp_program_parse_mode
    lda nrp_program_mode
    cmp #NRP_PROGRAM_REAL_FUNCTION
    beq nrp_parse_program_function
    lda #$00
    sta nrp_proc_index
    sta nrp_code_start_lo
    sta nrp_code_start_hi
    sta nrp_temp_base
    lda nrp_program_parse_mode
    jmp nrp_parse_body
nrp_parse_program_function:
    lda nrp_function_count
    sta nrp_proc_index
    lda #$00
    sta nrp_code_start_lo
    sta nrp_code_start_hi
    sta nrp_temp_base
    lda nrp_program_parse_mode
    jsr nrp_parse_body
    bcc nrp_parse_program_fail
    lda #$00
    sta nrp_function_index
nrp_parse_program_function_loop:
    lda nrp_function_index
    cmp nrp_function_count
    beq nrp_parse_program_done
    sta nrp_proc_index
    tax
    lda nrp_function_code_start_lo,x
    sta nrp_code_start_lo
    lda nrp_function_code_start_hi,x
    sta nrp_code_start_hi
    lda nrp_function_temp_base,x
    sta nrp_temp_base
    lda nrp_function_param_base,x
    sta nrp_param_base
    lda nrp_program_parse_mode
    jsr nrp_parse_body
    bcc nrp_parse_program_fail
    inc nrp_function_index
    jmp nrp_parse_program_function_loop
nrp_parse_program_done:
    sec
    rts
nrp_parse_program_fail:
    clc
    rts

nrp_emit_named_byte_reloc_delta:
    sty nrp_reloc_modifier
    jsr nrp_emit_reloc_prefix_delta
    lda nrp_reloc_modifier
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jmp nrp_emit_named_reloc_target
nrp_emit_named_word_reloc_delta:
    jsr nrp_emit_reloc_prefix_delta
    jmp nrp_emit_named_reloc_target
nrp_emit_import_reloc_delta:
    jsr nrp_emit_reloc_prefix_delta
    lda #'u'
    jsr emit_char_overlay
    lda nrp_import_index
    jsr emit_object_selector_overlay
    jmp emit_newline
nrp_emit_export_reloc_delta:
    jsr nrp_emit_reloc_prefix_delta
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx nrp_call_export_index
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr emit_lower_scan_zp_string
    jmp emit_newline
.if NRP_ENABLE_CONTROL
nrp_emit_control_reloc_delta:
    sty nrp_control_label_kind
    jsr nrp_emit_reloc_prefix_delta
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr nrp_emit_control_name
    jmp emit_newline
.endif
.if NRP_ENABLE_LOOP
nrp_emit_loop_reloc_delta:
    jsr nrp_emit_reloc_prefix_delta
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr nrp_emit_loop_name
    jmp emit_newline
.endif
nrp_emit_reloc_prefix_delta:
    clc
    adc nrp_code_lo
    sta nrp_reloc_offset_lo
    lda nrp_code_hi
    adc #$00
    sta nrp_reloc_offset_hi
    lda #'r'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda nrp_reloc_offset_lo
    ldy nrp_reloc_offset_hi
    jsr emit_word_decimal
    lda #' '
    jmp emit_char_overlay
nrp_emit_named_reloc_target:
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr nrp_emit_internal_name
    jmp emit_newline

nrp_emit_internal_name:
    lda #'_'
    jsr emit_char_overlay
    lda #'_'
    jsr emit_char_overlay
    lda #'r'
    jsr emit_char_overlay
    lda nrp_name_kind
    cmp #NRP_VALUE_TEMP
    beq :+
    lda #'v'
    bne nrp_emit_internal_name_suffix
:
    lda #'t'
nrp_emit_internal_name_suffix:
    jsr emit_char_overlay
    lda nrp_name_index
    jmp emit_object_selector_overlay

.if NRP_ENABLE_CONTROL
nrp_emit_control_name:
    lda #'_'
    jsr emit_char_overlay
    lda #'_'
    jsr emit_char_overlay
    lda #'r'
    jsr emit_char_overlay
    lda nrp_control_label_kind
    jsr emit_char_overlay
    lda nrp_proc_index
.if NRP_ENABLE_MULTI_CONTROL
    jsr emit_object_selector_overlay
    lda nrp_control_index
    and #NRP_CONTROL_MASK
    jmp emit_object_selector_overlay
.else
    jmp emit_object_selector_overlay
.endif
.endif
.if NRP_ENABLE_LOOP
nrp_emit_loop_name:
    lda #'_'
    jsr emit_char_overlay
    lda #'_'
    jsr emit_char_overlay
    lda #'r'
    jsr emit_char_overlay
    lda nrp_loop_label_kind
    jsr emit_char_overlay
    lda nrp_proc_index
    jsr emit_object_selector_overlay
    lda nrp_loop_index
    and #NRP_LOOP_MASK
    jmp emit_object_selector_overlay
.endif

nrp_helper_i_to_f: .asciiz "rt_i_to_f"
nrp_helper_s_to_f: .asciiz "rt_s_to_f"
nrp_helper_print_f: .asciiz "rt_print_f"
.if NRP_ENABLE_CONDITION
nrp_helper_f_cmp: .asciiz "rt_f_cmp"
.endif
nrp_helper_f_abs: .asciiz "rt_f_abs"
nrp_helper_f_sqrt: .asciiz "rt_f_sqrt"
nrp_helper_f_sign: .asciiz "rt_f_sign"
nrp_helper_f_trunc: .asciiz "rt_f_trunc"
nrp_helper_f_floor: .asciiz "rt_f_floor"
nrp_helper_f_ceil: .asciiz "rt_f_ceil"
nrp_helper_f_round: .asciiz "rt_f_round"
nrp_helper_f_frac: .asciiz "rt_f_frac"
nrp_helper_f_add: .asciiz "rt_f_add"
nrp_helper_f_sub: .asciiz "rt_f_sub"
nrp_helper_f_mul: .asciiz "rt_f_mul"
nrp_helper_f_div: .asciiz "rt_f_div"
nrp_helper_f_min: .asciiz "rt_f_min"
nrp_helper_f_max: .asciiz "rt_f_max"
nrp_helper_f_mod: .asciiz "rt_f_mod"
nrp_helper_f_hypot: .asciiz "rt_f_hypot"
nrp_helper_f_clamp: .asciiz "rt_f_clamp"
.if NRP_ENABLE_LITERAL
nrp_helper_f_deg_to_rad: .asciiz "rt_f_deg_to_rad"
nrp_helper_f_rad_to_deg: .asciiz "rt_f_rad_to_deg"
.endif

nrp_helper_name_lo:
    .byte <nrp_helper_i_to_f,<nrp_helper_s_to_f,<nrp_helper_print_f
.if NRP_ENABLE_CONDITION
    .byte <nrp_helper_f_cmp
.endif
    .byte <nrp_helper_f_abs,<nrp_helper_f_sqrt,<nrp_helper_f_sign
    .byte <nrp_helper_f_trunc,<nrp_helper_f_floor,<nrp_helper_f_ceil
    .byte <nrp_helper_f_round,<nrp_helper_f_frac,<nrp_helper_f_add
    .byte <nrp_helper_f_sub,<nrp_helper_f_mul,<nrp_helper_f_div
    .byte <nrp_helper_f_min,<nrp_helper_f_max,<nrp_helper_f_mod
    .byte <nrp_helper_f_hypot,<nrp_helper_f_clamp
.if NRP_ENABLE_LITERAL
    .byte <nrp_helper_f_deg_to_rad,<nrp_helper_f_rad_to_deg
.endif
nrp_helper_name_hi:
    .byte >nrp_helper_i_to_f,>nrp_helper_s_to_f,>nrp_helper_print_f
.if NRP_ENABLE_CONDITION
    .byte >nrp_helper_f_cmp
.endif
    .byte >nrp_helper_f_abs,>nrp_helper_f_sqrt,>nrp_helper_f_sign
    .byte >nrp_helper_f_trunc,>nrp_helper_f_floor,>nrp_helper_f_ceil
    .byte >nrp_helper_f_round,>nrp_helper_f_frac,>nrp_helper_f_add
    .byte >nrp_helper_f_sub,>nrp_helper_f_mul,>nrp_helper_f_div
    .byte >nrp_helper_f_min,>nrp_helper_f_max,>nrp_helper_f_mod
    .byte >nrp_helper_f_hypot,>nrp_helper_f_clamp
.if NRP_ENABLE_LITERAL
    .byte >nrp_helper_f_deg_to_rad,>nrp_helper_f_rad_to_deg
.endif
nrp_helper_kind:
    .byte NRP_HELPER_CONVERT,NRP_HELPER_CONVERT,NRP_HELPER_PRINT
.if NRP_ENABLE_CONDITION
    .byte NRP_HELPER_COMPARE
.endif
    .byte NRP_HELPER_UNARY,NRP_HELPER_UNARY,NRP_HELPER_UNARY,NRP_HELPER_UNARY
    .byte NRP_HELPER_UNARY,NRP_HELPER_UNARY,NRP_HELPER_UNARY,NRP_HELPER_UNARY
    .byte NRP_HELPER_BINARY,NRP_HELPER_BINARY,NRP_HELPER_BINARY,NRP_HELPER_BINARY
    .byte NRP_HELPER_BINARY,NRP_HELPER_BINARY,NRP_HELPER_BINARY,NRP_HELPER_BINARY
    .byte NRP_HELPER_TERNARY
.if NRP_ENABLE_LITERAL
    .byte NRP_HELPER_UNARY,NRP_HELPER_UNARY
.endif

nrp_call_edge_bits:
    .byte $01,$02

.if NRP_ENABLE_LITERAL
nrp_literal_store_template:
    .byte $A0,$00,$A9,$00,$91,$02,$C8
    .byte $A9,$00,$91,$02,$C8
    .byte $A9,$00,$91,$02,$C8
    .byte $A9,$00,$91,$02
nrp_literal_store_template_end:
.endif

.if NRP_ENABLE_FOR
nrp_for_load_ax_template:
    .byte $A0,$01,$B1,$06,$AA,$88,$B1,$06
nrp_for_load_ax_template_end:
nrp_for_store_template:
    .byte $A0,$00,$A9,$00,$91,$06,$C8,$A9,$00,$91,$06
nrp_for_store_template_end:
nrp_for_ascending_template:
    .byte $A0,$01,$B1,$06,$C9,$00,$90,$0E,$D0,$09,$88
    .byte $B1,$06,$C9,$00,$90,$05,$F0,$03,$4C,$00,$00
nrp_for_ascending_template_end:
nrp_for_descending_template:
    .byte $A0,$01,$B1,$06,$C9,$00,$90,$09,$D0,$0A,$88
    .byte $B1,$06,$C9,$00,$B0,$03,$4C,$00,$00
nrp_for_descending_template_end:
nrp_for_increment_template:
    .byte $A0,$00,$B1,$06,$18,$69,$00,$91,$06,$C8,$B1,$06
    .byte $69,$00,$91,$06,$B0,$03,$4C,$00,$00,$4C,$00,$00
nrp_for_increment_template_end:
.if NRP_ENABLE_FOR_DYNAMIC
nrp_for_word_copy_template:
    .byte $A0,$01,$B1,$04,$91,$06,$88,$B1,$04,$91,$06
nrp_for_word_copy_template_end:
.endif
.endif

nrp_copy_template:
    .byte $A0,$03,$B9,$00,$00,$99,$00,$00,$88,$10,$F7
nrp_exit_template:
    .byte $A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF
nrp_save_return_template:
    .byte $68,$AA,$68,$85,$04
nrp_restore_return_template:
    .byte $A5,$04,$48,$8A,$48
nrp_param_bind_template:
    .byte $68,$85,$03,$68,$85,$02,$A0,$03,$B1,$02,$99,$00,$00,$88,$10,$F8
nrp_frame_save_template:
    .byte $A0,$03,$B9,$00,$00,$48,$88,$10,$F9
nrp_return_stage_template:
    .byte $85,$04,$86,$05,$A0,$03,$B1,$04,$99,$0C,$00,$88,$10,$F8
nrp_frame_restore_template:
    .byte $A0,$00,$68,$99,$00,$00,$C8,$C0,$04,$90,$F7
nrp_staged_return_copy_template:
    .byte $A0,$03,$B9,$0C,$00,$99,$00,$00,$88,$10,$F7
nrp_frame_templates_end:
nrp_push_pointer_template:
    .byte $A9,$00,$48,$A9,$00,$48
nrp_return_copy_template:
    .byte $85,$04,$86,$05,$A0,$03,$B1,$04,$99,$00,$00,$88,$10,$F8
nrp_return_pointer_template:
    .byte $A9,$00,$A2,$00,$60
nrp_name_data:
    .asciiz "__idata"

.segment "BSS"
nrp_active: .res 1
nrp_mode: .res 1
nrp_program_mode: .res 1
nrp_program_parse_mode: .res 1
nrp_function_count: .res 1
nrp_function_index: .res 1
nrp_proc_index: .res 1
nrp_body_pos: .res 1
nrp_opcode: .res 1
nrp_var_count: .res 1
nrp_module_var_count: .res 1
nrp_temp_count: .res 1
nrp_temp_base: .res 1
nrp_temp_total: .res 1
nrp_main_temp_count: .res 1
nrp_data_slots: .res 1
nrp_stack_depth: .res 1
nrp_stack_kind: .res NRP_STACK_MAX
nrp_stack_index: .res NRP_STACK_MAX
.if NRP_ENABLE_WORD_VALUES
nrp_stack_value_lo: .res NRP_STACK_MAX
nrp_stack_value_hi: .res NRP_STACK_MAX
nrp_value_lo: .res 1
nrp_value_hi: .res 1
.endif
.if NRP_ENABLE_FOR
nrp_var_kind: .res NRP_TEMP_MAX
.endif
nrp_pending_load: .res 1
nrp_pending_store: .res 1
nrp_pending_value: .res 1
nrp_nested: .res 1
nrp_saw_return: .res 1
.if NRP_ENABLE_EARLY_RETURN
nrp_early_return_seen: .res 1
.endif
nrp_param_base: .res 1
nrp_expected_var_index: .res 1
nrp_function_param_base: .res NRP_FUNCTION_MAX
nrp_function_local_count: .res NRP_FUNCTION_MAX
.if NRP_ENABLE_VARIABLE_ARITY
nrp_function_param_count: .res NRP_FUNCTION_MAX
nrp_param_count: .res 1
nrp_call_param_count: .res 1
.endif
nrp_call_edges: .res NRP_FUNCTION_MAX
nrp_param_binds_left: .res 1
nrp_preserve_frame: .res 1
nrp_frame_name_index: .res 1
nrp_frame_slots_left: .res 1
nrp_frame_template_end: .res 1
.if NRP_ENABLE_CONTROL
nrp_control_count: .res 1
nrp_control_depth: .res 1
.if NRP_ENABLE_MULTI_CONTROL
nrp_control_index: .res 1
nrp_control_ordinal: .res 1
nrp_multi_control_seen: .res 1
nrp_control_stack: .res NRP_CONTROL_MAX
nrp_control_else_stack: .res NRP_CONTROL_MAX
.else
nrp_control_else_seen: .res 1
.endif
nrp_control_label_kind: .res 1
.if NRP_ENABLE_MULTI_CONTROL
nrp_if_seen: .res NRP_CONTROL_SLOT_MAX
nrp_if_has_else: .res NRP_CONTROL_SLOT_MAX
nrp_if_false_offset_lo: .res NRP_CONTROL_SLOT_MAX
nrp_if_false_offset_hi: .res NRP_CONTROL_SLOT_MAX
nrp_if_end_offset_lo: .res NRP_CONTROL_SLOT_MAX
nrp_if_end_offset_hi: .res NRP_CONTROL_SLOT_MAX
.else
nrp_if_seen: .res NRP_FUNCTION_MAX
nrp_if_has_else: .res NRP_FUNCTION_MAX
nrp_if_false_offset_lo: .res NRP_FUNCTION_MAX
nrp_if_false_offset_hi: .res NRP_FUNCTION_MAX
nrp_if_end_offset_lo: .res NRP_FUNCTION_MAX
nrp_if_end_offset_hi: .res NRP_FUNCTION_MAX
.endif
.endif
.if NRP_ENABLE_CONDITION
nrp_condition_cmp: .res 1
nrp_condition_true_branch: .res 1
.endif
.if NRP_ENABLE_LOOP
nrp_loop_count: .res 1
nrp_loop_depth: .res 1
nrp_loop_index: .res 1
nrp_loop_ordinal: .res 1
nrp_loop_seen_any: .res 1
.if NRP_ENABLE_FOR
nrp_for_seen_any: .res 1
nrp_for_pending: .res 1
nrp_for_pending_counter: .res 1
nrp_for_pending_direction: .res 1
nrp_for_pending_initial_lo: .res 1
nrp_for_pending_initial_hi: .res 1
nrp_for_pending_final_lo: .res 1
nrp_for_pending_final_hi: .res 1
nrp_for_pending_step_lo: .res 1
nrp_for_pending_step_hi: .res 1
nrp_for_counter: .res NRP_LOOP_SLOT_MAX
nrp_for_direction: .res NRP_LOOP_SLOT_MAX
nrp_for_final_lo: .res NRP_LOOP_SLOT_MAX
nrp_for_final_hi: .res NRP_LOOP_SLOT_MAX
nrp_for_step_lo: .res NRP_LOOP_SLOT_MAX
nrp_for_step_hi: .res NRP_LOOP_SLOT_MAX
.if NRP_ENABLE_FOR_DYNAMIC
nrp_for_dynamic_seen_any: .res 1
nrp_for_pending_initial_kind: .res 1
nrp_for_pending_initial_index: .res 1
nrp_for_pending_final_kind: .res 1
nrp_for_pending_final_index: .res 1
nrp_for_pending_final_temp: .res 1
nrp_for_final_kind: .res NRP_LOOP_SLOT_MAX
nrp_for_final_index: .res NRP_LOOP_SLOT_MAX
nrp_for_final_temp: .res NRP_LOOP_SLOT_MAX
.endif
.endif
.if NRP_ENABLE_LOOP_EXIT
nrp_loop_special_seen_any: .res 1
.endif
nrp_loop_label_kind: .res 1
nrp_loop_stack: .res NRP_LOOP_MAX
nrp_loop_seen: .res NRP_LOOP_SLOT_MAX
nrp_loop_kind: .res NRP_LOOP_SLOT_MAX
nrp_loop_has_exit: .res NRP_LOOP_SLOT_MAX
.if NRP_ENABLE_LOOP_EXIT
nrp_loop_user_exit: .res NRP_LOOP_SLOT_MAX
.endif
nrp_loop_start_offset_lo: .res NRP_LOOP_SLOT_MAX
nrp_loop_start_offset_hi: .res NRP_LOOP_SLOT_MAX
nrp_loop_exit_offset_lo: .res NRP_LOOP_SLOT_MAX
nrp_loop_exit_offset_hi: .res NRP_LOOP_SLOT_MAX
.endif
nrp_debug_count: .res 1
nrp_debug_lo: .res NRP_DEBUG_MAX*NRP_PROC_MAX
nrp_debug_hi: .res NRP_DEBUG_MAX*NRP_PROC_MAX
nrp_code_lo: .res 1
nrp_code_hi: .res 1
nrp_code_start_lo: .res 1
nrp_code_start_hi: .res 1
nrp_code_size_lo: .res 1
nrp_code_size_hi: .res 1
nrp_main_code_size_lo: .res 1
nrp_main_code_size_hi: .res 1
nrp_function_code_start_lo: .res NRP_FUNCTION_MAX
nrp_function_code_start_hi: .res NRP_FUNCTION_MAX
nrp_function_code_size_lo: .res NRP_FUNCTION_MAX
nrp_function_code_size_hi: .res NRP_FUNCTION_MAX
nrp_function_temp_base: .res NRP_FUNCTION_MAX
nrp_root_size_lo: .res 1
nrp_root_size_hi: .res 1
nrp_operand1_kind: .res 1
nrp_operand1_index: .res 1
nrp_operand2_kind: .res 1
nrp_operand2_index: .res 1
nrp_operand3_kind: .res 1
nrp_operand3_index: .res 1
nrp_dest_index: .res 1
nrp_dest_kind: .res 1
nrp_dest_name_index: .res 1
nrp_name_kind: .res 1
nrp_name_index: .res 1
nrp_import_index: .res 1
nrp_call_export_index: .res 1
nrp_rejected_call_graph: .res 1
nrp_literal_index: .res 1
nrp_literal_lo: .res 1
nrp_literal_hi: .res 1
.if NRP_ENABLE_LITERAL
nrp_literal_seen: .res 1
nrp_angle_seen: .res 1
nrp_real_literal_b0: .res 1
nrp_real_literal_b1: .res 1
nrp_real_literal_b2: .res 1
nrp_real_literal_b3: .res 1
.endif
.if NRP_ENABLE_FOR
nrp_conversion_source_kind: .res 1
nrp_conversion_word_index: .res 1
nrp_int_subtract: .res 1
nrp_int_rhs_lo: .res 1
nrp_int_rhs_hi: .res 1
nrp_for_template_ptr: .res 2
nrp_for_template_len: .res 1
nrp_for_template_index: .res 1
.endif
nrp_pointer_zp: .res 1
nrp_saved_index: .res 1
nrp_byte: .res 1
nrp_reloc_modifier: .res 1
nrp_reloc_offset_lo: .res 1
nrp_reloc_offset_hi: .res 1
nrp_export_offset_lo: .res 1
nrp_export_offset_hi: .res 1
.segment "CODE"
