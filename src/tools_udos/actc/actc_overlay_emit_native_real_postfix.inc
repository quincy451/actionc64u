; Straight-line nested REAL postfix lowering to ordinary OBJ1 machine records.
.macpack longbranch

NRP_MODE_ANALYZE = 0
NRP_MODE_MACHINE = 1
NRP_MODE_RELOC = 2

NRP_VALUE_INT = 1
NRP_VALUE_VAR = 2
NRP_VALUE_TEMP = 3

NRP_HELPER_CONVERT = 1
NRP_HELPER_PRINT = 2
NRP_HELPER_UNARY = 3
NRP_HELPER_BINARY = 4
NRP_HELPER_TERNARY = 5

NRP_STACK_MAX = 8
NRP_TEMP_MAX = 16
NRP_DEBUG_MAX = 64
NRP_HELPER_COUNT = 20

native_real_postfix_detect:
    lda #$00
    sta nrp_active
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$01
    jne native_real_postfix_detect_no
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
    ldx #$00
native_real_postfix_detect_var_loop:
    jsr nrp_var_x_is_real
    jcc native_real_postfix_detect_no
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

    lda #NRP_MODE_ANALYZE
    jsr nrp_parse_body
    jcc native_real_postfix_detect_no
    lda nrp_nested
    jeq native_real_postfix_detect_no
    lda #ACTC_OVERLAY_CTX_BODY_DEBUG_COUNT_PTR_LO
    ldx #$00
    jsr load_indexed_byte_from_context_ptr
    cmp nrp_debug_count
    jne native_real_postfix_detect_no

    lda nrp_code_lo
    sta nrp_code_size_lo
    lda nrp_code_hi
    sta nrp_code_size_hi
    lda nrp_var_count
    clc
    adc nrp_temp_count
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

nrp_parse_body:
    sta nrp_mode
    lda #$00
    sta nrp_body_pos
    sta nrp_stack_depth
    sta nrp_temp_count
    sta nrp_debug_count
    sta nrp_code_lo
    sta nrp_code_hi
    sta nrp_pending_load
    sta nrp_pending_store
    sta nrp_saw_return
    lda nrp_mode
    bne :+
    sta nrp_nested
:
nrp_parse_body_loop:
    jsr nrp_read_body
    jeq nrp_parse_body_fail
    sta nrp_opcode
    jsr nrp_record_debug_offset
    jcc nrp_parse_body_fail
    lda nrp_opcode
    cmp #'p'
    beq nrp_parse_push_int
    cmp #'L'
    beq nrp_parse_load
    cmp #'U'
    beq nrp_parse_load_end
    cmp #'u'
    jeq nrp_parse_call
    cmp #'T'
    beq nrp_parse_store
    cmp #'S'
    jeq nrp_parse_store_end
    cmp #'r'
    jeq nrp_parse_return
    jmp nrp_parse_body_fail

nrp_parse_push_int:
    jsr nrp_read_selector
    jcc nrp_parse_body_fail
    cmp #36
    jcs nrp_parse_body_fail
    tax
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
    clc
    adc #$01
    sta nrp_pending_load
    lda #NRP_VALUE_VAR
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
    jmp nrp_parse_body_fail

nrp_parse_call_convert:
    jsr nrp_pop_value
    jcc nrp_parse_body_fail
    cmp #NRP_VALUE_INT
    jne nrp_parse_body_fail
    stx nrp_literal_index
    jsr nrp_allocate_temp
    jcc nrp_parse_body_fail
    stx nrp_dest_index
    jsr nrp_emit_conversion
    lda #NRP_VALUE_TEMP
    ldx nrp_dest_index
    jsr nrp_push_value
    jcc nrp_parse_body_fail
    jmp nrp_parse_body_loop

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

nrp_parse_return:
    lda nrp_pending_load
    ora nrp_pending_store
    ora nrp_stack_depth
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
    ldx #$00
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
    ldx nrp_stack_index,y
    lda nrp_stack_kind,y
    sec
    rts
nrp_pop_value_no:
    clc
    rts

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
    lda nrp_helper_kind,x
    sec
    rts

nrp_emit_conversion:
    lda #NRP_VALUE_TEMP
    sta nrp_name_kind
    lda nrp_dest_index
    sta nrp_name_index
    lda #$02
    jsr nrp_emit_pointer
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
nrp_emit_print:
    jsr nrp_emit_operand1_zp2
    jmp nrp_emit_call_import

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
    lda nrp_debug_lo,x
    ldy nrp_debug_hi,x
    jmp emit_word_decimal

native_real_postfix_emit_export_list:
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx #$00
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

    lda nrp_code_size_lo
    sta nrp_export_offset_lo
    lda nrp_code_size_hi
    sta nrp_export_offset_hi
    jsr nrp_emit_data_export
    lda #NRP_VALUE_VAR
    sta nrp_name_kind
    lda #$00
    sta nrp_name_index
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
    cmp nrp_temp_count
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
    jsr emit_newline
    lda nrp_data_slots
    clc
    adc #$01
    sta nrp_saved_index
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
    jsr nrp_parse_body
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
    jsr nrp_parse_body
    bcc native_real_postfix_emit_machine_fail
    clc
    rts
native_real_postfix_emit_machine_fail:
    sec
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

nrp_helper_i_to_f: .asciiz "rt_i_to_f"
nrp_helper_s_to_f: .asciiz "rt_s_to_f"
nrp_helper_print_f: .asciiz "rt_print_f"
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

nrp_helper_name_lo:
    .byte <nrp_helper_i_to_f,<nrp_helper_s_to_f,<nrp_helper_print_f
    .byte <nrp_helper_f_abs,<nrp_helper_f_sqrt,<nrp_helper_f_sign
    .byte <nrp_helper_f_trunc,<nrp_helper_f_floor,<nrp_helper_f_ceil
    .byte <nrp_helper_f_round,<nrp_helper_f_frac,<nrp_helper_f_add
    .byte <nrp_helper_f_sub,<nrp_helper_f_mul,<nrp_helper_f_div
    .byte <nrp_helper_f_min,<nrp_helper_f_max,<nrp_helper_f_mod
    .byte <nrp_helper_f_hypot,<nrp_helper_f_clamp
nrp_helper_name_hi:
    .byte >nrp_helper_i_to_f,>nrp_helper_s_to_f,>nrp_helper_print_f
    .byte >nrp_helper_f_abs,>nrp_helper_f_sqrt,>nrp_helper_f_sign
    .byte >nrp_helper_f_trunc,>nrp_helper_f_floor,>nrp_helper_f_ceil
    .byte >nrp_helper_f_round,>nrp_helper_f_frac,>nrp_helper_f_add
    .byte >nrp_helper_f_sub,>nrp_helper_f_mul,>nrp_helper_f_div
    .byte >nrp_helper_f_min,>nrp_helper_f_max,>nrp_helper_f_mod
    .byte >nrp_helper_f_hypot,>nrp_helper_f_clamp
nrp_helper_kind:
    .byte NRP_HELPER_CONVERT,NRP_HELPER_CONVERT,NRP_HELPER_PRINT
    .byte NRP_HELPER_UNARY,NRP_HELPER_UNARY,NRP_HELPER_UNARY,NRP_HELPER_UNARY
    .byte NRP_HELPER_UNARY,NRP_HELPER_UNARY,NRP_HELPER_UNARY,NRP_HELPER_UNARY
    .byte NRP_HELPER_BINARY,NRP_HELPER_BINARY,NRP_HELPER_BINARY,NRP_HELPER_BINARY
    .byte NRP_HELPER_BINARY,NRP_HELPER_BINARY,NRP_HELPER_BINARY,NRP_HELPER_BINARY
    .byte NRP_HELPER_TERNARY

nrp_copy_template:
    .byte $A0,$03,$B9,$00,$00,$99,$00,$00,$88,$10,$F7
nrp_exit_template:
    .byte $A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF
nrp_name_data:
    .asciiz "__idata"

.segment "BSS"
nrp_active: .res 1
nrp_mode: .res 1
nrp_body_pos: .res 1
nrp_opcode: .res 1
nrp_var_count: .res 1
nrp_temp_count: .res 1
nrp_data_slots: .res 1
nrp_stack_depth: .res 1
nrp_stack_kind: .res NRP_STACK_MAX
nrp_stack_index: .res NRP_STACK_MAX
nrp_pending_load: .res 1
nrp_pending_store: .res 1
nrp_pending_value: .res 1
nrp_nested: .res 1
nrp_saw_return: .res 1
nrp_debug_count: .res 1
nrp_debug_lo: .res NRP_DEBUG_MAX
nrp_debug_hi: .res NRP_DEBUG_MAX
nrp_code_lo: .res 1
nrp_code_hi: .res 1
nrp_code_size_lo: .res 1
nrp_code_size_hi: .res 1
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
nrp_literal_index: .res 1
nrp_literal_lo: .res 1
nrp_literal_hi: .res 1
nrp_pointer_zp: .res 1
nrp_saved_index: .res 1
nrp_byte: .res 1
nrp_reloc_modifier: .res 1
nrp_reloc_offset_lo: .res 1
nrp_reloc_offset_hi: .res 1
nrp_export_offset_lo: .res 1
nrp_export_offset_hi: .res 1
.segment "CODE"
