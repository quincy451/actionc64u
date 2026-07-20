; Native lowering for compact word-expression body operations, including
; surrounding string output, external calls, two nested integer IF/ELSE
; levels, and a simple post-test integer loop.
; The root export spans code and initialized data; local exports name nested
; data and branch targets so ALINK only performs closure and relocation work.

NATIVE_INT_USE_MUL = $01
NATIVE_INT_USE_DIV = $02
NATIVE_INT_USE_PRINT = $04
NATIVE_INT_MAX_STACK_DEPTH = 96
NATIVE_INT_MAX_DEBUG_OPS = ACTC_OVERLAY_BODY_OP_LIMIT
NATIVE_INT_MAX_FOR = 2
NATIVE_INT_MAX_DO = 2
NATIVE_INT_LOOP_FOR = 2

is_main_native_integer_machine_object:
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$01
    beq :+
    jmp native_int_object_no
:
    lda #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    jsr load_context_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcs :+
    jmp native_int_object_no
:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcs :+
    jmp native_int_object_no
:

    jsr native_int_find_helper_indices
    jsr native_int_compute_data_size
    lda #$00
    sta native_int_code_size_lo
    sta native_int_code_size_hi
    sta native_int_stack_depth
    sta native_int_lowering_seen
    sta native_int_used_helpers
    sta native_int_for_count
    sta native_int_for_open
    sta native_int_do_count
    ldx #$07
:   sta native_int_if_seen,x
    dex
    bpl :-
    sta native_int_debug_op_count
    lda native_int_data_size_lo
    ora native_int_data_size_hi
    beq :+
    lda #13
    jsr native_int_add_a_to_code_size
:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #$00
    sta native_int_body_pos

native_int_analyze_loop:
    jsr native_int_store_debug_offset
    ldy native_int_body_pos
    jsr emit_object_peek_payload_y
    ldx #(native_int_op_table_end-native_int_op_table-1)
native_int_analyze_dispatch_loop:
    cmp native_int_op_table,x
    beq native_int_analyze_dispatch_found
    dex
    bpl native_int_analyze_dispatch_loop
    jmp native_int_object_no
native_int_analyze_dispatch_found:
    lda native_int_analyze_handler_lo,x
    sta ACTC_OVERLAY_WORK_ZP
    lda native_int_analyze_handler_hi,x
    sta ACTC_OVERLAY_WORK_ZP+1
    jmp (ACTC_OVERLAY_WORK_ZP)

native_int_analyze_string:
    lda #18
    jmp native_int_analyze_string_common
native_int_analyze_string_line:
    lda #21
native_int_analyze_string_common:
    sta native_int_instruction_size
    jsr native_int_read_body_selector
    bcs :+
    jmp native_int_object_no
:
    lda #ACTC_OVERLAY_CTX_STRING_COUNT_PTR_LO
    jsr load_count_from_context
    cmp native_int_operand_index
    beq :+
    bcs :++
:   jmp native_int_object_no
:
    lda native_int_instruction_size
    jsr native_int_add_a_to_code_size
    jmp native_int_analyze_next

native_int_analyze_external_call:
    ; Argument/result calls need ABI-aware stack lowering; this path currently
    ; supports only ordinary procedure calls that do not consume an expression.
    lda native_int_stack_depth
    beq :+
    jmp native_int_object_no
:
    jsr native_int_read_body_selector
    bcs :+
    jmp native_int_object_no
:
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp native_int_operand_index
    beq :+
    bcs :++
:   jmp native_int_object_no
:
    lda #3
    jsr native_int_add_a_to_code_size
    jmp native_int_analyze_next

native_int_analyze_literal:
    jsr native_int_read_body_selector
    bcs :+
    jmp native_int_object_no
:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp native_int_operand_index
    bne :+
    jmp native_int_object_no
:
    bcs :+
    jmp native_int_object_no
:
    jsr native_int_analyze_push
    bcs :+
    jmp native_int_object_no
:
    lda #6
    jsr native_int_add_a_to_code_size
    jmp native_int_analyze_next

native_int_analyze_load:
    jsr native_int_read_body_selector
    bcs :+
    jmp native_int_object_no
:
    lda native_int_operand_index
    jsr native_int_word_var_offset
    bcs :+
    jmp native_int_object_no
:
    jsr native_int_analyze_push
    bcs :+
    jmp native_int_object_no
:
    lda #9
    jsr native_int_add_a_to_code_size
    jmp native_int_analyze_mark_lowering

native_int_analyze_store:
    jsr native_int_read_body_selector
    bcs :+
    jmp native_int_object_no
:
    lda native_int_operand_index
    jsr native_int_word_var_offset
    bcs :+
    jmp native_int_object_no
:
    jsr native_int_analyze_pop
    bcs :+
    jmp native_int_object_no
:
    lda #11
    jsr native_int_add_a_to_code_size
    jmp native_int_analyze_mark_lowering

native_int_analyze_for:
    lda native_int_stack_depth
    cmp #$02
    beq :+
    jmp native_int_analyze_for_bad
:
    jsr native_int_read_body_selector
    bcs :+
    jmp native_int_analyze_for_bad
:
    lda native_int_operand_index
    jsr native_int_word_var_offset
    bcs :+
    jmp native_int_analyze_for_bad
:
    ldy native_int_body_pos
    jsr emit_object_peek_payload_y
    cmp #'+'
    beq native_int_analyze_for_direction_ok
    cmp #'-'
    bne native_int_analyze_for_bad
native_int_analyze_for_direction_ok:
    sta native_int_instruction_size
    lda native_int_for_count
    cmp #NATIVE_INT_MAX_FOR
    bcs native_int_analyze_for_bad
    ldx native_int_for_open
    cpx #NATIVE_INT_MAX_FOR
    bcs native_int_analyze_for_bad
    sta native_int_for_stack,x
    tax
    lda native_int_var_data_size_hi
    bne native_int_analyze_for_bad
    lda native_int_var_data_size_lo
    cmp #$FD
    bcs native_int_analyze_for_bad
    sta native_int_for_data_offset,x
    clc
    adc #$04
    sta native_int_var_data_size_lo
    bcc :+
    inc native_int_var_data_size_hi
:
    clc
    lda native_int_data_size_lo
    adc #$04
    sta native_int_data_size_lo
    bcc :+
    inc native_int_data_size_hi
:
    clc
    lda native_int_code_size_lo
    adc #22
    sta native_int_for_target_lo,x
    lda native_int_code_size_hi
    adc #$00
    sta native_int_for_target_hi,x
    inc native_int_for_count
    inc native_int_for_open
    jsr native_int_analyze_pop
    bcc native_int_analyze_for_bad
    jsr native_int_analyze_pop
    bcc native_int_analyze_for_bad
    inc native_int_body_pos
    lda #130
    jsr native_int_add_a_to_code_size
    inc native_int_debug_op_count
    jsr native_int_store_debug_offset
    jmp native_int_analyze_mark_lowering
native_int_analyze_for_bad:
    jmp native_int_object_no

native_int_analyze_for_end:
    lda native_int_stack_depth
    bne native_int_analyze_for_bad
    lda native_int_for_open
    beq native_int_analyze_for_bad
    dec native_int_for_open
    ldx native_int_for_open
    lda native_int_for_stack,x
    tax
    lda #77
    jsr native_int_add_a_to_code_size
    lda native_int_code_size_lo
    sta native_int_for_end_target_lo,x
    lda native_int_code_size_hi
    sta native_int_for_end_target_hi,x
    inc native_int_body_pos
    jmp native_int_analyze_mark_lowering

native_int_analyze_exit:
    lda native_int_stack_depth
    bne native_int_analyze_for_bad
    jsr native_int_read_body_selector
    bcc native_int_analyze_for_bad
    lda native_int_operand_index
    cmp #NATIVE_INT_LOOP_FOR
    beq native_int_analyze_exit_for
    cmp #$00
    bne native_int_analyze_for_bad
    ldx native_int_if_open
native_int_analyze_exit_do_loop:
    dex
    bmi native_int_analyze_for_bad
    lda native_int_if_else_seen,x
    bpl native_int_analyze_exit_do_loop
    lda native_int_if_seen,x
    cmp #$02
    bcs native_int_analyze_for_bad
    lda #$01
    sta native_int_do_exit_seen,x
    bne native_int_analyze_exit_add
native_int_analyze_exit_for:
    ldx native_int_for_open
    beq native_int_analyze_for_bad
native_int_analyze_exit_add:
    lda #$03
    jsr native_int_add_a_to_code_size
    jmp native_int_analyze_mark_lowering

native_int_analyze_plain_do_end:
    lda native_int_stack_depth
    bne native_int_analyze_for_bad
    ldx native_int_if_open
    beq native_int_analyze_for_bad
    dex
    lda native_int_if_else_seen,x
    bpl native_int_analyze_for_bad
    lda #$03
    jsr native_int_add_a_to_code_size
    lda native_int_do_exit_seen,x
    beq :+
    jsr native_int_store_do_end_target
:
    jmp native_int_analyze_if_end_done

native_int_store_do_end_target:
    lda native_int_code_size_lo
    sta native_int_if_end_target_lo,x
    lda native_int_code_size_hi
    sta native_int_if_end_target_hi,x
    rts

native_int_analyze_add_sub:
    jsr native_int_analyze_binary
    bcs :+
    jmp native_int_object_no
:
    inc native_int_body_pos
    lda #19
    jsr native_int_add_a_to_code_size
    jmp native_int_analyze_mark_lowering

native_int_analyze_mul:
    lda native_int_mul_index
    cmp #$FF
    bne :+
    jmp native_int_object_no
:
    jsr native_int_analyze_binary
    bcs :+
    jmp native_int_object_no
:
    lda native_int_used_helpers
    ora #NATIVE_INT_USE_MUL
    sta native_int_used_helpers
    inc native_int_body_pos
    lda #23
    jsr native_int_add_a_to_code_size
    jmp native_int_analyze_mark_lowering

native_int_analyze_div:
    lda native_int_div_index
    cmp #$FF
    bne :+
    jmp native_int_object_no
:
    jsr native_int_analyze_binary
    bcs :+
    jmp native_int_object_no
:
    lda native_int_used_helpers
    ora #NATIVE_INT_USE_DIV
    sta native_int_used_helpers
    inc native_int_body_pos
    lda #23
    jsr native_int_add_a_to_code_size
    jmp native_int_analyze_mark_lowering

native_int_analyze_do:
    lda native_int_stack_depth
    bne native_int_analyze_do_bad
    ldx native_int_if_open
    cpx #$02
    bcs native_int_analyze_do_bad
    lda native_int_if_seen,x
    beq native_int_analyze_do_first
    cmp #$02
    bcs native_int_analyze_do_bad
    lda native_int_do_exit_seen,x
    bne native_int_analyze_do_bad
    lda native_int_if_else_seen
    bmi native_int_analyze_do_bad
    inc native_int_if_seen,x
    inc native_int_if_else_seen,x
    txa
    clc
    adc #$02
    tax
    bne native_int_analyze_do_store_target
native_int_analyze_do_first:
    inc native_int_if_seen,x
    lda #$80
    sta native_int_if_else_seen,x
native_int_analyze_do_store_target:
    lda native_int_code_size_lo
    sta native_int_if_target_lo,x
    lda native_int_code_size_hi
    sta native_int_if_target_hi,x
    lda native_int_do_count
    cmp #NATIVE_INT_MAX_DO
    bcs native_int_analyze_do_bad
    inc native_int_do_count
    inc native_int_if_open
    inc native_int_body_pos
    jmp native_int_analyze_mark_lowering
native_int_analyze_do_bad:
    jmp native_int_object_no

native_int_analyze_equal_if:
    lda #23
native_int_analyze_compare_if:
    sta native_int_instruction_size
    lda #$00
    sta native_int_if_inverse
    jsr native_int_analyze_binary
    bcs :+
    jmp native_int_object_no
:
    inc native_int_body_pos
    ldy native_int_body_pos
    jsr emit_object_peek_payload_y
    cmp #'h'
    bne :+
    jmp native_int_analyze_compare_if_finish
:
    cmp #'t'
    bne :+
    jmp native_int_analyze_compare_until
:
    cmp #'p'
    beq :+
    jmp native_int_object_no
:
    bit native_int_instruction_size
    bmi :+
    jmp native_int_object_no
:
    jsr native_int_read_body_selector
    bcs :+
    jmp native_int_object_no
:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp native_int_operand_index
    beq native_int_analyze_ordered_if_bad
    bcc native_int_analyze_ordered_if_bad
    ldx native_int_operand_index
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    iny
    ora (ACTC_OVERLAY_WORK_ZP),y
    bne native_int_analyze_ordered_if_bad
    ldy native_int_body_pos
    jsr emit_object_peek_payload_y
    cmp #'q'
    bne native_int_analyze_ordered_if_bad
    inc native_int_body_pos
    ldy native_int_body_pos
    jsr emit_object_peek_payload_y
    cmp #'h'
    bne native_int_analyze_ordered_if_bad
    lda #$01
    sta native_int_if_inverse
    jmp native_int_analyze_compare_if_finish
native_int_analyze_ordered_if_bad:
    jmp native_int_object_no

native_int_analyze_not_equal_if:
    lda #23
    jmp native_int_analyze_compare_if
native_int_analyze_less_if:
    lda #$96
    jmp native_int_analyze_compare_if
native_int_analyze_greater_if:
    lda #$98
    jmp native_int_analyze_compare_if

native_int_analyze_compare_until:
    ldx native_int_if_open
    beq native_int_analyze_ordered_if_bad
    dex
    lda native_int_if_else_seen,x
    bpl native_int_analyze_ordered_if_bad
    inc native_int_body_pos
    ldy native_int_body_pos
    jsr emit_object_peek_payload_y
    cmp #'o'
    bne native_int_analyze_ordered_if_bad
    lda #$80
    sta native_int_if_inverse

native_int_analyze_compare_if_finish:
    jsr native_int_analyze_pop
    bcs :+
    jmp native_int_object_no
:
    lda native_int_if_inverse
    bmi native_int_analyze_compare_until_finish
    ldx native_int_if_open
    cpx #$02
    bcc :+
    jmp native_int_object_no
:
    lda native_int_if_seen,x
    beq :+
    jmp native_int_object_no
:
    lda #$01
    sta native_int_if_seen,x
    inc native_int_if_open
    inc native_int_body_pos
    jmp native_int_analyze_compare_finish_common
native_int_analyze_compare_until_finish:
    dec native_int_if_open
    inc native_int_body_pos
native_int_analyze_compare_finish_common:
    lda native_int_instruction_size
    and #$7F
    jsr native_int_add_a_to_code_size
    bit native_int_if_inverse
    bpl native_int_analyze_compare_debug
    lda native_int_do_exit_seen,x
    beq native_int_analyze_compare_debug
    jsr native_int_store_do_end_target
native_int_analyze_compare_debug:
    inc native_int_debug_op_count
    jsr native_int_store_debug_offset
    lda native_int_if_inverse
    beq :++
    bmi :+
    inc native_int_debug_op_count
    jsr native_int_store_debug_offset
:
    inc native_int_debug_op_count
    jsr native_int_store_debug_offset
:
    jmp native_int_analyze_mark_lowering

native_int_analyze_else:
    ldx native_int_if_open
    beq :+
    dex
    lda native_int_if_else_seen,x
    bmi :+
    beq :++
:
    jmp native_int_object_no
:
    lda #$01
    sta native_int_if_else_seen,x
    lda #$03
    jsr native_int_add_a_to_code_size
    lda native_int_code_size_lo
    sta native_int_if_target_lo,x
    lda native_int_code_size_hi
    sta native_int_if_target_hi,x
    inc native_int_body_pos
    jmp native_int_analyze_mark_lowering

native_int_analyze_if_end:
    ldx native_int_if_open
    beq :+
    dex
    lda native_int_if_else_seen,x
    bmi :+
    beq native_int_analyze_if_end_no_else
    lda native_int_code_size_lo
    sta native_int_if_end_target_lo,x
    lda native_int_code_size_hi
    sta native_int_if_end_target_hi,x
    jmp native_int_analyze_if_end_done
:
    jmp native_int_object_no
native_int_analyze_if_end_no_else:
    lda native_int_code_size_lo
    sta native_int_if_target_lo,x
    lda native_int_code_size_hi
    sta native_int_if_target_hi,x
native_int_analyze_if_end_done:
    stx native_int_if_open
    inc native_int_body_pos
native_int_analyze_mark_lowering:
    lda #$01
    sta native_int_lowering_seen
native_int_analyze_next:
    inc native_int_debug_op_count
    jmp native_int_analyze_loop

native_int_analyze_print:
    lda #6
    jmp native_int_analyze_print_common
native_int_analyze_print_line:
    lda #11
native_int_analyze_print_common:
    sta native_int_instruction_size
    lda native_int_print_index
    cmp #$FF
    bne :+
    jmp native_int_object_no
:
    jsr native_int_analyze_pop
    bcs :+
    jmp native_int_object_no
:
    lda native_int_used_helpers
    ora #NATIVE_INT_USE_PRINT
    sta native_int_used_helpers
    inc native_int_body_pos
    lda native_int_instruction_size
    jsr native_int_add_a_to_code_size
    jmp native_int_analyze_next

native_int_analyze_return:
    inc native_int_body_pos
    ldy native_int_body_pos
    jsr emit_object_peek_payload_y
    bne native_int_object_no
    lda native_int_if_open
    ora native_int_for_open
    ora native_int_stack_depth
    bne native_int_object_no
    lda native_int_lowering_seen
    beq native_int_object_no
    lda #16
    jsr native_int_add_a_to_code_size
    sec
    rts

native_int_object_no:
    clc
    rts

native_int_read_body_selector:
    inc native_int_body_pos
    ldy native_int_body_pos
    jsr emit_object_peek_payload_y
    jsr external_import_selector_to_index
    bcc native_int_read_body_selector_bad
    sta native_int_operand_index
    inc native_int_body_pos
    sec
    rts
native_int_read_body_selector_bad:
    clc
    rts

native_int_analyze_push:
    lda native_int_stack_depth
    cmp #NATIVE_INT_MAX_STACK_DEPTH
    bcs native_int_analyze_stack_bad
    inc native_int_stack_depth
    sec
    rts

native_int_analyze_pop:
    lda native_int_stack_depth
    beq native_int_analyze_stack_bad
    dec native_int_stack_depth
    sec
    rts

native_int_analyze_binary:
    lda native_int_stack_depth
    cmp #$02
    bcc native_int_analyze_stack_bad
    dec native_int_stack_depth
    sec
    rts
native_int_analyze_stack_bad:
    clc
    rts

native_int_add_a_to_code_size:
    clc
    adc native_int_code_size_lo
    sta native_int_code_size_lo
    bcc :+
    inc native_int_code_size_hi
:
    rts

native_int_store_debug_offset:
    ldx native_int_debug_op_count
    lda native_int_code_size_lo
    sta native_int_debug_offsets_lo,x
    rts

native_int_load_debug_offset:
    ldx body_debug_index_data
    lda native_int_debug_offsets_lo,x
    cpx #$00
    beq native_int_load_debug_offset_first
    cmp native_int_debug_emit_prev
    bcs native_int_load_debug_offset_ready
    inc native_int_debug_emit_hi
    bne native_int_load_debug_offset_ready
native_int_load_debug_offset_first:
    stx native_int_debug_emit_hi
native_int_load_debug_offset_ready:
    sta native_int_debug_emit_prev
    ldy native_int_debug_emit_hi
    rts

native_int_compute_data_size:
    lda #$00
    sta native_int_data_size_lo
    sta native_int_data_size_hi
    sta entry_index_data
native_int_compute_data_size_loop:
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq native_int_compute_data_size_done
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_LOAD_VAR_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp #$04
    beq :+
    lda #$02
:
    clc
    adc native_int_data_size_lo
    sta native_int_data_size_lo
    bcc :+
    inc native_int_data_size_hi
:
    inc entry_index_data
    jmp native_int_compute_data_size_loop
native_int_compute_data_size_done:
    lda native_int_data_size_lo
    sta native_int_var_data_size_lo
    lda native_int_data_size_hi
    sta native_int_var_data_size_hi
    lda #$00
    sta entry_index_data
native_int_compute_string_data_size_loop:
    lda #ACTC_OVERLAY_CTX_STRING_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq native_int_compute_string_data_size_done
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_STRING_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    ldy #$00
native_int_compute_string_data_size_byte_loop:
    jsr emit_object_peek_payload_y
    pha
    inc native_int_data_size_lo
    bne :+
    inc native_int_data_size_hi
:
    pla
    beq native_int_compute_string_data_size_next
    iny
    bne native_int_compute_string_data_size_byte_loop
    jmp native_int_object_no
native_int_compute_string_data_size_next:
    inc entry_index_data
    jmp native_int_compute_string_data_size_loop
native_int_compute_string_data_size_done:
    rts

native_int_compute_string_offset:
    lda native_int_var_data_size_lo
    sta native_int_string_offset_lo
    lda native_int_var_data_size_hi
    sta native_int_string_offset_hi
    lda #$00
    sta entry_index_data
native_int_compute_string_offset_loop:
    lda entry_index_data
    cmp native_int_operand_index
    beq native_int_compute_string_offset_done
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_STRING_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    ldy #$00
native_int_compute_string_offset_byte_loop:
    jsr emit_object_peek_payload_y
    pha
    inc native_int_string_offset_lo
    bne :+
    inc native_int_string_offset_hi
:
    pla
    beq native_int_compute_string_offset_next
    iny
    bne native_int_compute_string_offset_byte_loop
native_int_compute_string_offset_next:
    inc entry_index_data
    jmp native_int_compute_string_offset_loop
native_int_compute_string_offset_done:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    rts

native_int_word_var_offset:
    sta native_int_target_var
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp native_int_target_var
    beq native_int_word_var_offset_bad
    bcc native_int_word_var_offset_bad
    lda #$00
    sta native_int_var_offset
    sta entry_index_data
native_int_word_var_offset_loop:
    lda entry_index_data
    cmp native_int_target_var
    beq native_int_word_var_offset_target
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_LOAD_VAR_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp #$04
    beq :+
    lda #$02
:
    clc
    adc native_int_var_offset
    sta native_int_var_offset
    inc entry_index_data
    jmp native_int_word_var_offset_loop
native_int_word_var_offset_target:
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_LOAD_VAR_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp #$02
    bne native_int_word_var_offset_bad
    lda native_int_var_offset
    sec
    rts
native_int_word_var_offset_bad:
    clc
    rts

native_int_find_helper_indices:
    ldx #$02
native_int_find_helper_indices_loop:
    lda #$FF
    sta native_int_mul_index,x
    lda native_int_helper_name_lo,x
    ldy native_int_helper_name_hi,x
    stx native_int_operand_index
    jsr native_int_find_external
    ldx native_int_operand_index
    bcc :+
    sta native_int_mul_index,x
:   dex
    bpl native_int_find_helper_indices_loop
    rts

native_int_find_external:
    sta native_int_const_ptr_lo
    sty native_int_const_ptr_hi
    lda #$00
    sta entry_index_data
native_int_find_external_loop:
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq native_int_find_external_no
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_EXTERNAL_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    lda native_int_const_ptr_lo
    sta ACTC_OVERLAY_WORK_ZP
    lda native_int_const_ptr_hi
    sta ACTC_OVERLAY_WORK_ZP+1
    ldy #$00
native_int_find_external_compare:
    lda (ACTC_OVERLAY_SCAN_ZP),y
    jsr lowercase_ascii_overlay
    cmp (ACTC_OVERLAY_WORK_ZP),y
    bne native_int_find_external_next
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq native_int_find_external_yes
    iny
    bne native_int_find_external_compare
native_int_find_external_next:
    inc entry_index_data
    jmp native_int_find_external_loop
native_int_find_external_yes:
    lda entry_index_data
    sec
    rts
native_int_find_external_no:
    clc
    rts

emit_native_integer_export_list:
    jsr native_int_compute_root_size
    lda #$00
    sta native_int_export_offset_lo
    sta native_int_export_offset_hi
    lda native_int_root_size_lo
    sta native_int_export_size_lo
    lda native_int_root_size_hi
    sta native_int_export_size_hi
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr native_int_emit_export_line

    lda #$01
    sta native_int_export_size_lo
    lda #$00
    sta native_int_export_size_hi
    ldx #$00
native_int_emit_export_if_loop:
    lda native_int_if_seen,x
    beq native_int_emit_export_if_next
    lda native_int_if_target_lo,x
    sta native_int_export_offset_lo
    lda native_int_if_target_hi,x
    sta native_int_export_offset_hi
    txa
    pha
    jsr native_int_load_if_target_name_x
    jsr native_int_emit_export_line
    pla
    tax
    lda native_int_if_else_seen,x
    and #$01
    ora native_int_do_exit_seen,x
    beq native_int_emit_export_if_next
    lda native_int_if_end_target_lo,x
    sta native_int_export_offset_lo
    lda native_int_if_end_target_hi,x
    sta native_int_export_offset_hi
    txa
    pha
    jsr native_int_load_if_end_name_x
    jsr native_int_emit_export_line
    pla
    tax
native_int_emit_export_if_next:
    inx
    cpx #$02
    bne native_int_emit_export_if_loop
native_int_emit_export_list_no_if:
    ldx #$00
native_int_emit_export_for_loop:
    cpx native_int_for_count
    beq native_int_emit_export_list_no_for
    lda native_int_for_target_lo,x
    sta native_int_export_offset_lo
    lda native_int_for_target_hi,x
    sta native_int_export_offset_hi
    txa
    pha
    jsr native_int_load_for_target_name_x
    jsr native_int_emit_export_line
    pla
    tax
    lda native_int_for_end_target_lo,x
    sta native_int_export_offset_lo
    lda native_int_for_end_target_hi,x
    sta native_int_export_offset_hi
    txa
    pha
    jsr native_int_load_for_end_name_x
    jsr native_int_emit_export_line
    pla
    tax
    inx
    bne native_int_emit_export_for_loop
native_int_emit_export_list_no_for:
    lda native_int_data_size_lo
    ora native_int_data_size_hi
    beq native_int_emit_export_list_done
    lda native_int_code_size_lo
    sta native_int_export_offset_lo
    lda native_int_code_size_hi
    sta native_int_export_offset_hi
    lda native_int_data_size_lo
    sta native_int_export_size_lo
    lda native_int_data_size_hi
    sta native_int_export_size_hi
    lda #<native_int_name_data
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>native_int_name_data
    sta ACTC_OVERLAY_SCAN_ZP+1
    jsr native_int_emit_export_line

    clc
    lda native_int_code_size_lo
    adc native_int_data_size_lo
    sta native_int_export_offset_lo
    lda native_int_code_size_hi
    adc native_int_data_size_hi
    sta native_int_export_offset_hi
    lda #$02
    sta native_int_export_size_lo
    lda #$00
    sta native_int_export_size_hi
    lda #<native_int_name_pointer
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>native_int_name_pointer
    sta ACTC_OVERLAY_SCAN_ZP+1
    jsr native_int_emit_export_line
native_int_emit_export_list_done:
    clc
    rts

native_int_compute_root_size:
    clc
    lda native_int_code_size_lo
    adc native_int_data_size_lo
    sta native_int_root_size_lo
    lda native_int_code_size_hi
    adc native_int_data_size_hi
    sta native_int_root_size_hi
    lda native_int_data_size_lo
    ora native_int_data_size_hi
    beq :+
    clc
    lda native_int_root_size_lo
    adc #$02
    sta native_int_root_size_lo
    bcc :+
    inc native_int_root_size_hi
:
    rts

native_int_emit_export_line:
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr emit_lower_scan_zp_string
    lda #' '
    jsr emit_char_overlay
    lda native_int_export_offset_lo
    ldy native_int_export_offset_hi
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda native_int_export_size_lo
    ldy native_int_export_size_hi
    jsr emit_word_decimal
    jmp emit_newline

emit_native_integer_body_marker_list:
    lda #'b'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr native_int_emit_direct_body_imports
    lda #$00
    sta entry_index_data
native_int_emit_body_helpers_loop:
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq native_int_emit_body_helpers_done
    lda native_int_used_helpers
    and #NATIVE_INT_USE_MUL
    beq :+
    lda entry_index_data
    cmp native_int_mul_index
    beq native_int_emit_body_helper
:
    lda native_int_used_helpers
    and #NATIVE_INT_USE_DIV
    beq :+
    lda entry_index_data
    cmp native_int_div_index
    beq native_int_emit_body_helper
:
    lda native_int_used_helpers
    and #NATIVE_INT_USE_PRINT
    beq native_int_emit_body_helper_next
    lda entry_index_data
    cmp native_int_print_index
    bne native_int_emit_body_helper_next
native_int_emit_body_helper:
    lda #'u'
    jsr emit_char_overlay
    lda entry_index_data
    jsr emit_object_selector_overlay
native_int_emit_body_helper_next:
    inc entry_index_data
    jmp native_int_emit_body_helpers_loop
native_int_emit_body_helpers_done:
    lda #'M'
    jsr emit_char_overlay
    jsr emit_newline
    lda native_int_if_seen
    beq :+
    jsr emit_machine_body_marker_line
    lda native_int_if_else_seen
    and #$01
    ora native_int_do_exit_seen
    beq :+
    jsr emit_machine_body_marker_line
:
    lda native_int_nested_if_seen
    beq :+
    jsr emit_machine_body_marker_line
    lda native_int_nested_if_else_seen
    and #$01
    ora native_int_do_exit_seen+1
    beq :+
    jsr emit_machine_body_marker_line
:
    lda native_int_for_count
    sta entry_index_data
    beq :+
native_int_emit_body_for_markers:
    jsr emit_machine_body_marker_line
    jsr emit_machine_body_marker_line
    dec entry_index_data
    bne native_int_emit_body_for_markers
:
    lda native_int_data_size_lo
    ora native_int_data_size_hi
    beq native_int_emit_body_markers_done
    jsr emit_machine_body_marker_line
    jsr emit_machine_body_marker_line
native_int_emit_body_markers_done:
    rts

native_int_emit_direct_body_imports:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #$00
    sta native_int_body_pos
native_int_emit_direct_body_imports_loop:
    ldy native_int_body_pos
    jsr emit_object_peek_payload_y
    beq native_int_emit_direct_body_imports_done
    cmp #'u'
    beq native_int_emit_direct_body_import
    cmp #'s'
    beq native_int_emit_direct_body_imports_skip_selector
    cmp #'e'
    beq native_int_emit_direct_body_imports_skip_selector
    cmp #'p'
    beq native_int_emit_direct_body_imports_skip_selector
    cmp #'L'
    beq native_int_emit_direct_body_imports_skip_selector
    cmp #'S'
    beq native_int_emit_direct_body_imports_skip_selector
    cmp #'X'
    beq native_int_emit_direct_body_imports_skip_selector
    cmp #'F'
    beq native_int_emit_direct_body_imports_skip_for
    inc native_int_body_pos
    jmp native_int_emit_direct_body_imports_loop
native_int_emit_direct_body_imports_skip_selector:
    inc native_int_body_pos
    inc native_int_body_pos
    jmp native_int_emit_direct_body_imports_loop
native_int_emit_direct_body_imports_skip_for:
    inc native_int_body_pos
    inc native_int_body_pos
    inc native_int_body_pos
    jmp native_int_emit_direct_body_imports_loop
native_int_emit_direct_body_import:
    lda #'u'
    jsr emit_char_overlay
    inc native_int_body_pos
    ldy native_int_body_pos
    jsr emit_object_peek_payload_y
    jsr emit_char_overlay
    inc native_int_body_pos
    jmp native_int_emit_direct_body_imports_loop
native_int_emit_direct_body_imports_done:
    rts

emit_native_integer_machine_code_list:
    lda #'m'
    jsr emit_char_overlay
    lda native_int_data_size_lo
    ora native_int_data_size_hi
    beq :+
    lda #<native_int_prologue
    ldy #>native_int_prologue
    ldx #(native_int_prologue_end-native_int_prologue)
    jsr native_int_emit_const_bytes
:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #$00
    sta native_int_body_pos
    sta native_int_for_walk_count
    sta native_int_for_walk_open
native_int_emit_code_loop:
    ldy native_int_body_pos
    jsr emit_object_peek_payload_y
    ldx #(native_int_op_table_end-native_int_op_table-1)
native_int_emit_code_dispatch_loop:
    cmp native_int_op_table,x
    beq native_int_emit_code_dispatch_found
    dex
    bpl native_int_emit_code_dispatch_loop
    jmp native_int_emit_return
native_int_emit_code_dispatch_found:
    lda native_int_emit_handler_lo,x
    sta ACTC_OVERLAY_WORK_ZP
    lda native_int_emit_handler_hi,x
    sta ACTC_OVERLAY_WORK_ZP+1
    jmp (ACTC_OVERLAY_WORK_ZP)

native_int_emit_do:
    inc native_int_body_pos
    jmp native_int_emit_code_loop

native_int_emit_for:
    jsr native_int_read_body_selector
    lda native_int_operand_index
    jsr native_int_word_var_offset
    ldx native_int_for_walk_count
    sta native_int_for_counter_offset,x
    stx native_int_for_current
    ldx native_int_for_walk_open
    lda native_int_for_walk_count
    sta native_int_for_walk_stack,x
    inc native_int_for_walk_count
    inc native_int_for_walk_open
    ldy native_int_body_pos
    jsr emit_object_peek_payload_y
    inc native_int_body_pos
    ldx native_int_for_current
    lda native_int_for_data_offset,x
    clc
    adc #$02
    jsr native_int_emit_store_offset
    ldx native_int_for_current
    lda native_int_for_data_offset,x
    jsr native_int_emit_store_offset

    ; The staged step controls direction at runtime. A zero step exits before
    ; the body, while a negative high byte selects the descending comparison.
    lda #$A0
    jsr native_int_emit_byte
    ldx native_int_for_current
    lda native_int_for_data_offset,x
    clc
    adc #$02
    jsr native_int_emit_byte
    lda #<native_int_for_direction_bytes
    ldy #>native_int_for_direction_bytes
    ldx #(native_int_for_direction_bytes_end-native_int_for_direction_bytes)
    jsr native_int_emit_const_bytes

    ldx native_int_for_current
    lda native_int_for_counter_offset,x
    jsr native_int_emit_load_offset
    ldx native_int_for_current
    lda native_int_for_data_offset,x
    jsr native_int_emit_load_offset
    jsr native_int_emit_ordered_if_prefix
    lda #<native_int_less_equal_if_tail
    ldy #>native_int_less_equal_if_tail
    ldx #(native_int_less_equal_if_tail_end-native_int_less_equal_if_tail)
    jsr native_int_emit_const_bytes
    lda #<native_int_for_skip_descending_bytes
    ldy #>native_int_for_skip_descending_bytes
    ldx #(native_int_for_skip_descending_bytes_end-native_int_for_skip_descending_bytes)
    jsr native_int_emit_const_bytes

    ldx native_int_for_current
    lda native_int_for_counter_offset,x
    jsr native_int_emit_load_offset
    ldx native_int_for_current
    lda native_int_for_data_offset,x
    jsr native_int_emit_load_offset
    jsr native_int_emit_ordered_if_prefix
    lda #<native_int_greater_equal_if_tail
    ldy #>native_int_greater_equal_if_tail
    ldx #(native_int_greater_equal_if_tail_end-native_int_greater_equal_if_tail)
    jsr native_int_emit_const_bytes
    jmp native_int_emit_code_loop

native_int_emit_for_end:
    dec native_int_for_walk_open
    ldx native_int_for_walk_open
    lda native_int_for_walk_stack,x
    sta native_int_for_current
    tax
    lda native_int_for_counter_offset,x
    jsr native_int_emit_load_offset
    ldx native_int_for_current
    lda native_int_for_data_offset,x
    clc
    adc #$02
    jsr native_int_emit_load_offset
    lda #<native_int_add_bytes
    ldy #>native_int_add_bytes
    ldx #19
    jsr native_int_emit_const_bytes
    ldx native_int_for_current
    lda native_int_for_counter_offset,x
    jsr native_int_emit_store_offset

    ; Preserve the addition carry before inspecting the staged step sign.
    lda #<native_int_for_overflow_head
    ldy #>native_int_for_overflow_head
    ldx #(native_int_for_overflow_head_end-native_int_for_overflow_head)
    jsr native_int_emit_const_bytes
    ldx native_int_for_current
    lda native_int_for_data_offset,x
    clc
    adc #$03
    jsr native_int_emit_byte
    lda #<native_int_for_overflow_tail
    ldy #>native_int_for_overflow_tail
    ldx #(native_int_for_overflow_tail_end-native_int_for_overflow_tail)
    jsr native_int_emit_const_bytes
    inc native_int_body_pos
    jmp native_int_emit_code_loop

native_int_emit_exit:
    jsr native_int_read_body_selector
    jmp native_int_emit_jump

native_int_emit_string:
    lda #$00
    jmp native_int_emit_string_common
native_int_emit_string_line:
    lda #$01
native_int_emit_string_common:
    sta native_int_string_newline
    jsr native_int_read_body_selector
    jsr native_int_compute_string_offset
    lda #<native_int_string_ptr_head
    ldy #>native_int_string_ptr_head
    ldx #(native_int_string_ptr_head_end-native_int_string_ptr_head)
    jsr native_int_emit_const_bytes
    lda native_int_string_offset_lo
    jsr native_int_emit_byte
    lda #<native_int_string_ptr_mid
    ldy #>native_int_string_ptr_mid
    ldx #(native_int_string_ptr_mid_end-native_int_string_ptr_mid)
    jsr native_int_emit_const_bytes
    lda native_int_string_offset_hi
    jsr native_int_emit_byte
    lda #<native_int_string_ptr_tail
    ldy #>native_int_string_ptr_tail
    ldx #(native_int_string_ptr_tail_end-native_int_string_ptr_tail)
    jsr native_int_emit_const_bytes
    lda native_int_string_newline
    beq :+
    lda #<native_int_service_newline_bytes
    ldy #>native_int_service_newline_bytes
    ldx #(native_int_service_newline_bytes_end-native_int_service_newline_bytes)
    jsr native_int_emit_const_bytes
:
    jmp native_int_emit_code_loop

native_int_emit_external_call:
    jsr native_int_read_body_selector
    lda #<native_int_external_call_bytes
    ldy #>native_int_external_call_bytes
    ldx #(native_int_external_call_bytes_end-native_int_external_call_bytes)
    jsr native_int_emit_const_bytes
    jmp native_int_emit_code_loop

native_int_emit_literal:
    jsr native_int_read_body_selector
    ldx native_int_operand_index
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    lda #$A9
    jsr native_int_emit_byte
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr native_int_emit_byte
    lda #$48
    jsr native_int_emit_byte
    lda #$A9
    jsr native_int_emit_byte
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$01
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr native_int_emit_byte
    lda #$48
    jsr native_int_emit_byte
    jmp native_int_emit_code_loop

native_int_emit_load:
    jsr native_int_read_body_selector
    lda native_int_operand_index
    jsr native_int_word_var_offset
    jsr native_int_emit_load_offset
    jmp native_int_emit_code_loop

native_int_emit_load_offset:
    sta native_int_var_offset
    lda #$A0
    jsr native_int_emit_byte
    lda native_int_var_offset
    jsr native_int_emit_byte
    lda #<native_int_load_tail
    ldy #>native_int_load_tail
    ldx #(native_int_load_tail_end-native_int_load_tail)
    jmp native_int_emit_const_bytes

native_int_emit_store:
    jsr native_int_read_body_selector
    lda native_int_operand_index
    jsr native_int_word_var_offset
    jsr native_int_emit_store_offset
    jmp native_int_emit_code_loop

native_int_emit_store_offset:
    sta native_int_var_offset
    lda #<native_int_store_head
    ldy #>native_int_store_head
    ldx #(native_int_store_head_end-native_int_store_head)
    jsr native_int_emit_const_bytes
    lda native_int_var_offset
    jsr native_int_emit_byte
    lda #<native_int_store_tail
    ldy #>native_int_store_tail
    ldx #(native_int_store_tail_end-native_int_store_tail)
    jmp native_int_emit_const_bytes

native_int_emit_add:
    lda #<native_int_add_bytes
    ldy #>native_int_add_bytes
    jmp native_int_emit_add_sub
native_int_emit_sub:
    lda #<native_int_sub_bytes
    ldy #>native_int_sub_bytes
native_int_emit_add_sub:
    ldx #19
    jsr native_int_emit_const_bytes
    inc native_int_body_pos
    jmp native_int_emit_code_loop

native_int_emit_mul_div:
    lda #<native_int_mul_div_bytes
    ldy #>native_int_mul_div_bytes
    ldx #23
    jsr native_int_emit_const_bytes
    inc native_int_body_pos
    jmp native_int_emit_code_loop

native_int_emit_equal_if:
    jsr native_int_set_compare_inverse_from_body
    lda #<native_int_equal_if_bytes
    ldy #>native_int_equal_if_bytes
    ldx #(native_int_equal_if_bytes_end-native_int_equal_if_bytes)
    jmp native_int_emit_compare_if
native_int_emit_not_equal_if:
    jsr native_int_set_compare_inverse_from_body
    lda #<native_int_not_equal_if_bytes
    ldy #>native_int_not_equal_if_bytes
    ldx #(native_int_not_equal_if_bytes_end-native_int_not_equal_if_bytes)
    jmp native_int_emit_compare_if
native_int_emit_less_if:
    jsr native_int_set_compare_inverse_from_body
    jsr native_int_emit_ordered_if_prefix
    lda native_int_if_inverse
    and #$01
    beq :+
    lda #<native_int_greater_equal_if_tail
    ldy #>native_int_greater_equal_if_tail
    ldx #(native_int_greater_equal_if_tail_end-native_int_greater_equal_if_tail)
    jmp native_int_emit_compare_if
:
    lda #<native_int_less_if_tail
    ldy #>native_int_less_if_tail
    ldx #(native_int_less_if_tail_end-native_int_less_if_tail)
    jmp native_int_emit_compare_if
native_int_emit_greater_if:
    jsr native_int_set_compare_inverse_from_body
    jsr native_int_emit_ordered_if_prefix
    lda native_int_if_inverse
    and #$01
    beq :+
    lda #<native_int_less_equal_if_tail
    ldy #>native_int_less_equal_if_tail
    ldx #(native_int_less_equal_if_tail_end-native_int_less_equal_if_tail)
    jmp native_int_emit_compare_if
:
    lda #<native_int_greater_if_tail
    ldy #>native_int_greater_if_tail
    ldx #(native_int_greater_if_tail_end-native_int_greater_if_tail)
native_int_emit_compare_if:
    jsr native_int_emit_const_bytes
    jsr native_int_advance_compare_body
    jmp native_int_emit_code_loop

native_int_emit_ordered_if_prefix:
    lda #<native_int_ordered_if_prefix
    ldy #>native_int_ordered_if_prefix
    ldx #(native_int_ordered_if_prefix_end-native_int_ordered_if_prefix)
    jmp native_int_emit_const_bytes

native_int_set_compare_inverse_from_body:
    ldy native_int_body_pos
    iny
    jsr emit_object_peek_payload_y
    cmp #'t'
    beq native_int_set_compare_until
    cmp #'p'
    beq :+
    lda #$00
    sta native_int_if_inverse
    rts
native_int_set_compare_until:
    lda #$80
    sta native_int_if_inverse
    rts
:
    lda #$01
    sta native_int_if_inverse
    rts

native_int_advance_compare_body:
    bit native_int_if_inverse
    bmi native_int_advance_compare_until_body
    lda native_int_if_inverse
    asl
    clc
    adc native_int_if_inverse
    adc #$02
    adc native_int_body_pos
    sta native_int_body_pos
    rts
native_int_advance_compare_until_body:
    lda #$03
    clc
    adc native_int_body_pos
    sta native_int_body_pos
    rts

native_int_emit_else:
    inc native_int_body_pos
native_int_emit_jump:
    lda #<native_int_else_bytes
    ldy #>native_int_else_bytes
    ldx #(native_int_else_bytes_end-native_int_else_bytes)
    jsr native_int_emit_const_bytes
    jmp native_int_emit_code_loop

native_int_emit_if_end:
    inc native_int_body_pos
    jmp native_int_emit_code_loop

native_int_emit_print:
    lda #<native_int_print_bytes
    ldy #>native_int_print_bytes
    ldx #6
    jsr native_int_emit_const_bytes
    inc native_int_body_pos
    jmp native_int_emit_code_loop
native_int_emit_print_line:
    lda #<native_int_print_bytes
    ldy #>native_int_print_bytes
    ldx #6
    jsr native_int_emit_const_bytes
    lda #<native_int_newline_bytes
    ldy #>native_int_newline_bytes
    ldx #5
    jsr native_int_emit_const_bytes
    inc native_int_body_pos
    jmp native_int_emit_code_loop

native_int_emit_return:
    lda #<native_int_exit_bytes
    ldy #>native_int_exit_bytes
    ldx #16
    jsr native_int_emit_const_bytes
    jsr native_int_emit_data
    jsr emit_newline
    jmp native_int_emit_reloc_list

native_int_emit_data:
    lda #$00
    sta entry_index_data
native_int_emit_data_loop:
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq native_int_emit_data_pointer
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_LOAD_VAR_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr native_int_emit_byte
    lda #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$01
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr native_int_emit_byte
    lda #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp #$04
    bne native_int_emit_data_next
    lda #$00
    jsr native_int_emit_byte
    lda #$00
    jsr native_int_emit_byte
native_int_emit_data_next:
    inc entry_index_data
    jmp native_int_emit_data_loop
native_int_emit_data_pointer:
    lda #$00
    sta entry_index_data
native_int_emit_for_data_loop:
    lda entry_index_data
    cmp native_int_for_count
    beq native_int_emit_string_data_begin
    lda #$04
    sta native_int_instruction_size
native_int_emit_for_data_zero_loop:
    lda #$00
    jsr native_int_emit_byte
    dec native_int_instruction_size
    bne native_int_emit_for_data_zero_loop
    inc entry_index_data
    jmp native_int_emit_for_data_loop
native_int_emit_string_data_begin:
    lda #$00
    sta entry_index_data
native_int_emit_string_data_loop:
    lda #ACTC_OVERLAY_CTX_STRING_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq native_int_emit_data_pointer_value
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_STRING_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #$00
    sta native_int_string_pos
native_int_emit_string_data_byte_loop:
    ldy native_int_string_pos
    jsr emit_object_peek_payload_y
    jsr native_int_emit_byte
    lda native_int_machine_byte
    beq native_int_emit_string_data_next
    inc native_int_string_pos
    jmp native_int_emit_string_data_byte_loop
native_int_emit_string_data_next:
    inc entry_index_data
    jmp native_int_emit_string_data_loop
native_int_emit_data_pointer_value:
    lda native_int_data_size_lo
    ora native_int_data_size_hi
    beq native_int_emit_data_done
    lda #$00
    jsr native_int_emit_byte
    lda #$00
    jsr native_int_emit_byte
native_int_emit_data_done:
    rts

native_int_emit_const_bytes:
    sta native_int_const_ptr_lo
    sty native_int_const_ptr_hi
    stx native_int_const_len
    lda #$00
    sta native_int_const_index
native_int_emit_const_bytes_loop:
    lda native_int_const_index
    cmp native_int_const_len
    beq native_int_emit_const_bytes_done
    lda native_int_const_ptr_lo
    sta ACTC_OVERLAY_WORK_ZP
    lda native_int_const_ptr_hi
    sta ACTC_OVERLAY_WORK_ZP+1
    ldy native_int_const_index
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr native_int_emit_byte
    inc native_int_const_index
    jmp native_int_emit_const_bytes_loop
native_int_emit_const_bytes_done:
    rts

native_int_emit_byte:
    sta native_int_machine_byte
    lda #' '
    jsr emit_char_overlay
    lda native_int_machine_byte
    jmp emit_hex_byte_overlay

native_int_emit_reloc_list:
    lda native_int_data_size_lo
    ora native_int_data_size_hi
    beq native_int_emit_reloc_body_start_zero
    lda #$03
    ldy #$00
    jsr native_int_emit_named_reloc_pointer
    lda #$09
    ldy #$00
    jsr native_int_emit_named_reloc_pointer
    lda #13
    sta native_int_reloc_offset_lo
    lda #$00
    sta native_int_reloc_offset_hi
    jmp native_int_emit_reloc_body_begin
native_int_emit_reloc_body_start_zero:
    lda #$00
    sta native_int_reloc_offset_lo
    sta native_int_reloc_offset_hi
native_int_emit_reloc_body_begin:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #$00
    sta native_int_body_pos
    sta native_int_reloc_if_depth
    sta native_int_for_walk_count
    sta native_int_for_walk_open
native_int_emit_reloc_body_loop:
    ldy native_int_body_pos
    jsr emit_object_peek_payload_y
    ldx #(native_int_op_table_end-native_int_op_table-1)
native_int_emit_reloc_dispatch_loop:
    cmp native_int_op_table,x
    beq native_int_emit_reloc_dispatch_found
    dex
    bpl native_int_emit_reloc_dispatch_loop
    jmp native_int_emit_reloc_done_body
native_int_emit_reloc_dispatch_found:
    lda native_int_reloc_handler_lo,x
    sta ACTC_OVERLAY_WORK_ZP
    lda native_int_reloc_handler_hi,x
    sta ACTC_OVERLAY_WORK_ZP+1
    jmp (ACTC_OVERLAY_WORK_ZP)

native_int_emit_reloc_literal:
    lda #6
    jmp native_int_emit_reloc_two_byte_op
native_int_emit_reloc_load:
    lda #9
    jmp native_int_emit_reloc_two_byte_op
native_int_emit_reloc_store:
    lda #11
    jmp native_int_emit_reloc_two_byte_op
native_int_emit_reloc_do:
    inc native_int_reloc_if_depth
    inc native_int_body_pos
    jmp native_int_emit_reloc_body_loop

native_int_emit_reloc_plain_do_end:
    lda #$01
    jsr native_int_reloc_addend_to_ay
    jsr native_int_emit_named_reloc_if_target
    jsr native_int_restore_body_scan_ptr
    dec native_int_reloc_if_depth
    inc native_int_body_pos
    lda #$03
    jsr native_int_add_a_to_reloc_offset
    jmp native_int_emit_reloc_body_loop

native_int_emit_reloc_for:
    jsr native_int_read_body_selector
    ldx native_int_for_walk_open
    lda native_int_for_walk_count
    sta native_int_for_walk_stack,x
    sta native_int_for_current
    inc native_int_for_walk_count
    inc native_int_for_walk_open
    ldy native_int_body_pos
    jsr emit_object_peek_payload_y
    lda #38
    jsr native_int_emit_reloc_for_end_addend
    lda #84
    jsr native_int_emit_reloc_for_end_addend
    lda #128
    jsr native_int_emit_reloc_for_end_addend
    inc native_int_body_pos
    lda #130
    jsr native_int_add_a_to_reloc_offset
    jmp native_int_emit_reloc_body_loop

native_int_emit_reloc_for_end:
    dec native_int_for_walk_open
    ldx native_int_for_walk_open
    lda native_int_for_walk_stack,x
    sta native_int_for_current
    lda #65
    jsr native_int_emit_reloc_for_end_addend
    lda #72
    jsr native_int_emit_reloc_for_end_addend
    lda #75
    jsr native_int_emit_reloc_for_target_addend
    inc native_int_body_pos
    lda #77
    jsr native_int_add_a_to_reloc_offset
    jmp native_int_emit_reloc_body_loop

native_int_emit_reloc_exit:
    jsr native_int_read_body_selector
    lda native_int_operand_index
    cmp #NATIVE_INT_LOOP_FOR
    beq native_int_emit_reloc_exit_for
    ldx native_int_reloc_if_depth
native_int_emit_reloc_exit_do_loop:
    dex
    lda native_int_if_else_seen,x
    bpl native_int_emit_reloc_exit_do_loop
    txa
    pha
    lda #$01
    jsr native_int_reloc_addend_to_ay
    jsr native_int_emit_reloc_prefix
    pla
    tax
    jsr native_int_emit_named_reloc_if_end_x
    jsr native_int_restore_body_scan_ptr
    jmp native_int_emit_reloc_exit_advance
native_int_emit_reloc_exit_for:
    ldx native_int_for_walk_open
    dex
    lda native_int_for_walk_stack,x
    sta native_int_for_current
    lda #$01
    jsr native_int_emit_reloc_for_end_addend
native_int_emit_reloc_exit_advance:
    lda #$03
    jsr native_int_add_a_to_reloc_offset
    jmp native_int_emit_reloc_body_loop

native_int_emit_reloc_for_end_addend:
    jsr native_int_reloc_addend_to_ay
    jsr native_int_emit_named_reloc_for_end
    jmp native_int_restore_body_scan_ptr

native_int_emit_reloc_for_target_addend:
    jsr native_int_reloc_addend_to_ay
    jsr native_int_emit_named_reloc_for_target
    jmp native_int_restore_body_scan_ptr

native_int_emit_reloc_string:
    lda #18
    jmp native_int_emit_reloc_selector_op
native_int_emit_reloc_string_line:
    lda #21
native_int_emit_reloc_selector_op:
    sta native_int_instruction_size
    inc native_int_body_pos
    inc native_int_body_pos
    lda native_int_instruction_size
    jsr native_int_add_a_to_reloc_offset
    jmp native_int_emit_reloc_body_loop

native_int_emit_reloc_external_call:
    jsr native_int_read_body_selector
    ldx native_int_operand_index
    lda #$01
    jsr native_int_emit_import_reloc_addend
    lda #$03
    jsr native_int_add_a_to_reloc_offset
    jmp native_int_emit_reloc_body_loop

native_int_emit_reloc_two_byte_op:
    sta native_int_instruction_size
    inc native_int_body_pos
    inc native_int_body_pos
    lda native_int_instruction_size
    jsr native_int_add_a_to_reloc_offset
    jmp native_int_emit_reloc_body_loop
native_int_emit_reloc_add_sub:
    inc native_int_body_pos
    lda #19
    jsr native_int_add_a_to_reloc_offset
    jmp native_int_emit_reloc_body_loop
native_int_emit_reloc_mul:
    ldx native_int_mul_index
    jmp native_int_emit_reloc_mul_div
native_int_emit_reloc_div:
    ldx native_int_div_index
native_int_emit_reloc_mul_div:
    lda #18
    jsr native_int_emit_import_reloc_addend
    inc native_int_body_pos
    lda #23
    jsr native_int_add_a_to_reloc_offset
    jmp native_int_emit_reloc_body_loop
native_int_emit_reloc_equal_if:
    jsr native_int_set_compare_inverse_from_body
    lda #23
    sta native_int_instruction_size
    lda #21
    jmp native_int_emit_reloc_compare_if
native_int_emit_reloc_less_if:
    jsr native_int_set_compare_inverse_from_body
    lda #22
    sta native_int_instruction_size
    lda #20
    jmp native_int_emit_reloc_compare_if
native_int_emit_reloc_greater_if:
    jsr native_int_set_compare_inverse_from_body
    lda #24
    sta native_int_instruction_size
    lda #22
native_int_emit_reloc_compare_if:
    jsr native_int_reloc_addend_to_ay
    bit native_int_if_inverse
    bmi :+
    inc native_int_reloc_if_depth
:
    jsr native_int_emit_named_reloc_if_target
    jsr native_int_restore_body_scan_ptr
    jsr native_int_advance_compare_body
    lda native_int_instruction_size
    jsr native_int_add_a_to_reloc_offset
    bit native_int_if_inverse
    bpl native_int_emit_reloc_compare_done
    ldx native_int_reloc_if_depth
    dex
    lda native_int_if_seen,x
    cmp #$02
    bne native_int_emit_reloc_compare_until_close
    lda #$02
    sta native_int_if_else_seen,x
native_int_emit_reloc_compare_until_close:
    dec native_int_reloc_if_depth
native_int_emit_reloc_compare_done:
    jmp native_int_emit_reloc_body_loop
native_int_emit_reloc_else:
    lda #$01
    jsr native_int_reloc_addend_to_ay
    jsr native_int_emit_named_reloc_if_end
    jsr native_int_restore_body_scan_ptr
    inc native_int_body_pos
    lda #$03
    jsr native_int_add_a_to_reloc_offset
    jmp native_int_emit_reloc_body_loop
native_int_emit_reloc_if_end:
    dec native_int_reloc_if_depth
    inc native_int_body_pos
    jmp native_int_emit_reloc_body_loop
native_int_emit_reloc_print:
    lda #6
    jmp native_int_emit_reloc_print_common
native_int_emit_reloc_print_line:
    lda #11
native_int_emit_reloc_print_common:
    sta native_int_instruction_size
    ldx native_int_print_index
    lda #4
    jsr native_int_emit_import_reloc_addend
    inc native_int_body_pos
    lda native_int_instruction_size
    jsr native_int_add_a_to_reloc_offset
    jmp native_int_emit_reloc_body_loop

native_int_emit_reloc_done_body:
    lda native_int_data_size_lo
    ora native_int_data_size_hi
    beq native_int_emit_reloc_done
    clc
    lda native_int_code_size_lo
    adc native_int_data_size_lo
    sta native_int_temp_offset_lo
    lda native_int_code_size_hi
    adc native_int_data_size_hi
    tay
    lda native_int_temp_offset_lo
    jsr native_int_emit_named_reloc_data
native_int_emit_reloc_done:
    clc
    rts

native_int_restore_body_scan_ptr:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jmp load_resident_body_ptr_to_scan_zp

native_int_emit_import_reloc_addend:
    stx native_int_reloc_import_index
    jsr native_int_reloc_addend_to_ay
    jsr native_int_emit_reloc_prefix
    lda #'u'
    jsr emit_char_overlay
    lda native_int_reloc_import_index
    jsr emit_object_selector_overlay
    jmp emit_newline

native_int_reloc_addend_to_ay:
    clc
    adc native_int_reloc_offset_lo
    sta native_int_temp_offset_lo
    lda native_int_reloc_offset_hi
    adc #$00
    tay
    lda native_int_temp_offset_lo
    rts

native_int_emit_named_reloc_if_target:
    jsr native_int_emit_reloc_prefix
    lda native_int_reloc_if_depth
    tax
    dex
    jsr native_int_load_if_target_name_x
    jmp native_int_emit_named_reloc_target
native_int_emit_named_reloc_if_end:
    jsr native_int_emit_reloc_prefix
    lda native_int_reloc_if_depth
    tax
    dex
native_int_emit_named_reloc_if_end_x:
    jsr native_int_load_if_end_name_x
    jmp native_int_emit_named_reloc_target
native_int_emit_named_reloc_for_target:
    jsr native_int_emit_reloc_prefix
    ldx native_int_for_current
    jsr native_int_load_for_target_name_x
    jmp native_int_emit_named_reloc_target
native_int_emit_named_reloc_for_end:
    jsr native_int_emit_reloc_prefix
    ldx native_int_for_current
    jsr native_int_load_for_end_name_x
    jmp native_int_emit_named_reloc_target
native_int_load_if_end_name_x:
    txa
    asl
    ora #'1'
    bne native_int_load_if_name_digit
native_int_emit_named_reloc_pointer:
    jsr native_int_emit_reloc_prefix
    lda #<native_int_name_pointer
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>native_int_name_pointer
    sta ACTC_OVERLAY_SCAN_ZP+1
    jmp native_int_emit_named_reloc_target
native_int_emit_named_reloc_data:
    jsr native_int_emit_reloc_prefix
    lda #<native_int_name_data
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>native_int_name_data
    sta ACTC_OVERLAY_SCAN_ZP+1
native_int_emit_named_reloc_target:
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr emit_scan_zp_string
    jmp emit_newline

native_int_load_if_target_name_x:
    lda native_int_if_else_seen,x
    bmi native_int_load_loop_target_name_x
    cmp #$02
    beq native_int_load_if_end_name_x
    txa
    asl
    ora #'0'
native_int_load_if_name_digit:
    sta native_int_name_if_target+4
    lda #<native_int_name_if_target
    ldy #>native_int_name_if_target
    jmp native_int_set_scan_zp_ay
native_int_load_loop_target_name_x:
    txa
    ora #'0'
    sta native_int_name_do_target+4
    lda #<native_int_name_do_target
    ldy #>native_int_name_do_target
    jmp native_int_set_scan_zp_ay

native_int_load_for_target_name_x:
    txa
    ora #'0'
    sta native_int_name_for_target+5
    lda #<native_int_name_for_target
    ldy #>native_int_name_for_target
    jmp native_int_set_scan_zp_ay

native_int_load_for_end_name_x:
    txa
    ora #'0'
    sta native_int_name_for_end+6
    lda #<native_int_name_for_end
    ldy #>native_int_name_for_end
native_int_set_scan_zp_ay:
    sta ACTC_OVERLAY_SCAN_ZP
    sty ACTC_OVERLAY_SCAN_ZP+1
    rts

native_int_emit_reloc_prefix:
    sta native_int_temp_offset_lo
    sty native_int_temp_offset_hi
    lda #'r'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda native_int_temp_offset_lo
    ldy native_int_temp_offset_hi
    jsr emit_word_decimal
    lda #' '
    jmp emit_char_overlay

native_int_add_a_to_reloc_offset:
    clc
    adc native_int_reloc_offset_lo
    sta native_int_reloc_offset_lo
    bcc :+
    inc native_int_reloc_offset_hi
:
    rts

native_int_prologue:
    .byte $A2,$00,$BD,$00,$00,$85,$06,$E8,$BD,$00,$00,$85,$07
native_int_prologue_end:
native_int_load_tail:
    .byte $B1,$06,$48,$C8,$B1,$06,$48
native_int_load_tail_end:
native_int_store_head:
    .byte $68,$AA,$68,$A0
native_int_store_head_end:
native_int_store_tail:
    .byte $91,$06,$C8,$8A,$91,$06
native_int_store_tail_end:
native_int_add_bytes:
    .byte $68,$85,$05,$68,$85,$04,$68,$85,$03,$68,$18,$65,$04,$48,$A5,$03,$65,$05,$48
native_int_sub_bytes:
    .byte $68,$85,$05,$68,$85,$04,$68,$85,$03,$68,$38,$E5,$04,$48,$A5,$03,$E5,$05,$48
native_int_mul_div_bytes:
    .byte $A9,$04,$85,$02,$A9,$00,$85,$03,$68,$85,$05,$68,$85,$04,$68,$AA,$68,$20,$00,$00,$48,$8A,$48
native_int_equal_if_bytes:
    .byte $68,$85,$05,$68,$85,$04,$68,$85,$03,$68,$C5,$04,$D0,$06,$A5,$03,$C5,$05,$F0,$03,$4C,$00,$00
native_int_equal_if_bytes_end:
native_int_not_equal_if_bytes:
    .byte $68,$85,$05,$68,$85,$04,$68,$85,$03,$68,$C5,$04,$D0,$09,$A5,$03,$C5,$05,$D0,$03,$4C,$00,$00
native_int_not_equal_if_bytes_end:
native_int_ordered_if_prefix:
    .byte $68,$85,$05,$68,$85,$04,$68,$AA,$68,$E4,$05
native_int_ordered_if_prefix_end:
native_int_less_if_tail:
    .byte $90,$09,$D0,$04,$C5,$04,$90,$03,$4C,$00,$00
native_int_less_if_tail_end:
native_int_greater_if_tail:
    .byte $90,$08,$D0,$09,$C5,$04,$90,$02,$D0,$03,$4C,$00,$00
native_int_greater_if_tail_end:
native_int_greater_equal_if_tail:
    .byte $90,$06,$D0,$07,$C5,$04,$B0,$03,$4C,$00,$00
native_int_greater_equal_if_tail_end:
native_int_less_equal_if_tail:
    .byte $90,$0B,$D0,$06,$C5,$04,$90,$05,$F0,$03,$4C,$00,$00
native_int_less_equal_if_tail_end:
native_int_for_direction_bytes:
    .byte $B1,$06,$85,$02,$C8,$B1,$06,$85,$03,$05,$02,$D0,$03,$4C,$00,$00,$A5,$03,$30,$2E
native_int_for_direction_bytes_end:
native_int_for_skip_descending_bytes:
    .byte $A9,$00,$F0,$28
native_int_for_skip_descending_bytes_end:
native_int_for_overflow_head:
    .byte $A9,$00,$69,$00,$85,$02,$A0
native_int_for_overflow_head_end:
native_int_for_overflow_tail:
    .byte $B1,$06,$30,$07,$A5,$02,$F0,$0A,$4C,$00,$00,$A5,$02,$D0,$03,$4C,$00,$00,$4C,$00,$00
native_int_for_overflow_tail_end:
native_int_else_bytes:
    .byte $4C,$00,$00
native_int_else_bytes_end:
native_int_print_bytes:
    .byte $68,$AA,$68,$20,$00,$00
native_int_newline_bytes:
    .byte $A9,$0D,$20,$D2,$FF
native_int_string_ptr_head:
    .byte $A5,$06,$18,$69
native_int_string_ptr_head_end:
native_int_string_ptr_mid:
    .byte $85,$02,$A5,$07,$69
native_int_string_ptr_mid_end:
native_int_string_ptr_tail:
    .byte $85,$03,$A2,$02,$20,$03,$CF
native_int_string_ptr_tail_end:
native_int_service_newline_bytes:
    .byte $20,$06,$CF
native_int_service_newline_bytes_end:
native_int_external_call_bytes:
    .byte $20,$00,$00
native_int_external_call_bytes_end:
native_int_exit_bytes:
    .byte $A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF

native_int_op_table:
    .byte 's','e','u','p','L','S','a','m','*','/','d','o','F','O','X','q','n','l','g','w','v','y','z','r'
native_int_op_table_end:
native_int_analyze_handler_lo:
    .byte <native_int_analyze_string,<native_int_analyze_string_line,<native_int_analyze_external_call
    .byte <native_int_analyze_literal,<native_int_analyze_load,<native_int_analyze_store
    .byte <native_int_analyze_add_sub,<native_int_analyze_add_sub,<native_int_analyze_mul,<native_int_analyze_div
    .byte <native_int_analyze_do,<native_int_analyze_plain_do_end
    .byte <native_int_analyze_for,<native_int_analyze_for_end,<native_int_analyze_exit
    .byte <native_int_analyze_equal_if,<native_int_analyze_not_equal_if
    .byte <native_int_analyze_less_if,<native_int_analyze_greater_if,<native_int_analyze_else
    .byte <native_int_analyze_if_end,<native_int_analyze_print,<native_int_analyze_print_line,<native_int_analyze_return
native_int_analyze_handler_hi:
    .byte >native_int_analyze_string,>native_int_analyze_string_line,>native_int_analyze_external_call
    .byte >native_int_analyze_literal,>native_int_analyze_load,>native_int_analyze_store
    .byte >native_int_analyze_add_sub,>native_int_analyze_add_sub,>native_int_analyze_mul,>native_int_analyze_div
    .byte >native_int_analyze_do,>native_int_analyze_plain_do_end
    .byte >native_int_analyze_for,>native_int_analyze_for_end,>native_int_analyze_exit
    .byte >native_int_analyze_equal_if,>native_int_analyze_not_equal_if
    .byte >native_int_analyze_less_if,>native_int_analyze_greater_if,>native_int_analyze_else
    .byte >native_int_analyze_if_end,>native_int_analyze_print,>native_int_analyze_print_line,>native_int_analyze_return
native_int_emit_handler_lo:
    .byte <native_int_emit_string,<native_int_emit_string_line,<native_int_emit_external_call
    .byte <native_int_emit_literal,<native_int_emit_load,<native_int_emit_store
    .byte <native_int_emit_add,<native_int_emit_sub,<native_int_emit_mul_div,<native_int_emit_mul_div
    .byte <native_int_emit_do,<native_int_emit_else,<native_int_emit_for,<native_int_emit_for_end,<native_int_emit_exit
    .byte <native_int_emit_equal_if,<native_int_emit_not_equal_if
    .byte <native_int_emit_less_if,<native_int_emit_greater_if,<native_int_emit_else
    .byte <native_int_emit_if_end,<native_int_emit_print,<native_int_emit_print_line,<native_int_emit_return
native_int_emit_handler_hi:
    .byte >native_int_emit_string,>native_int_emit_string_line,>native_int_emit_external_call
    .byte >native_int_emit_literal,>native_int_emit_load,>native_int_emit_store
    .byte >native_int_emit_add,>native_int_emit_sub,>native_int_emit_mul_div,>native_int_emit_mul_div
    .byte >native_int_emit_do,>native_int_emit_else,>native_int_emit_for,>native_int_emit_for_end,>native_int_emit_exit
    .byte >native_int_emit_equal_if,>native_int_emit_not_equal_if
    .byte >native_int_emit_less_if,>native_int_emit_greater_if,>native_int_emit_else
    .byte >native_int_emit_if_end,>native_int_emit_print,>native_int_emit_print_line,>native_int_emit_return
native_int_reloc_handler_lo:
    .byte <native_int_emit_reloc_string,<native_int_emit_reloc_string_line,<native_int_emit_reloc_external_call
    .byte <native_int_emit_reloc_literal,<native_int_emit_reloc_load,<native_int_emit_reloc_store
    .byte <native_int_emit_reloc_add_sub,<native_int_emit_reloc_add_sub
    .byte <native_int_emit_reloc_mul,<native_int_emit_reloc_div,<native_int_emit_reloc_do
    .byte <native_int_emit_reloc_plain_do_end
    .byte <native_int_emit_reloc_for,<native_int_emit_reloc_for_end,<native_int_emit_reloc_exit
    .byte <native_int_emit_reloc_equal_if,<native_int_emit_reloc_equal_if
    .byte <native_int_emit_reloc_less_if,<native_int_emit_reloc_greater_if,<native_int_emit_reloc_else
    .byte <native_int_emit_reloc_if_end,<native_int_emit_reloc_print,<native_int_emit_reloc_print_line
    .byte <native_int_emit_reloc_done_body
native_int_reloc_handler_hi:
    .byte >native_int_emit_reloc_string,>native_int_emit_reloc_string_line,>native_int_emit_reloc_external_call
    .byte >native_int_emit_reloc_literal,>native_int_emit_reloc_load,>native_int_emit_reloc_store
    .byte >native_int_emit_reloc_add_sub,>native_int_emit_reloc_add_sub
    .byte >native_int_emit_reloc_mul,>native_int_emit_reloc_div,>native_int_emit_reloc_do
    .byte >native_int_emit_reloc_plain_do_end
    .byte >native_int_emit_reloc_for,>native_int_emit_reloc_for_end,>native_int_emit_reloc_exit
    .byte >native_int_emit_reloc_equal_if,>native_int_emit_reloc_equal_if
    .byte >native_int_emit_reloc_less_if,>native_int_emit_reloc_greater_if,>native_int_emit_reloc_else
    .byte >native_int_emit_reloc_if_end,>native_int_emit_reloc_print,>native_int_emit_reloc_print_line
    .byte >native_int_emit_reloc_done_body

native_int_name_mul:
    .asciiz "rt_i_mul"
native_int_name_div:
    .asciiz "rt_i_div"
native_int_name_print:
    .asciiz "rt_print_i"
native_int_helper_name_lo:
    .byte <native_int_name_mul,<native_int_name_div,<native_int_name_print
native_int_helper_name_hi:
    .byte >native_int_name_mul,>native_int_name_div,>native_int_name_print
native_int_name_data:
    .asciiz "__idata"
native_int_name_pointer:
    .asciiz "__iptr"
native_int_name_if_target:
    .asciiz "__if0"
native_int_name_do_target:
    .asciiz "__do0"
native_int_name_for_target:
    .asciiz "__for0"
native_int_name_for_end:
    .asciiz "__fend0"

native_int_body_pos:
    .byte $00
native_int_operand_index:
    .byte $00
native_int_stack_depth:
    .byte $00
native_int_lowering_seen:
    .byte $00
native_int_used_helpers:
    .byte $00
native_int_if_seen:
    .res 2, $00
native_int_nested_if_seen = native_int_if_seen+1
native_int_if_open:
    .byte $00
native_int_if_else_seen:
    .res 2, $00
native_int_nested_if_else_seen = native_int_if_else_seen+1
native_int_do_exit_seen:
    .res 2, $00
native_int_if_inverse:
    .byte $00
native_int_do_count:
    .byte $00
native_int_for_count:
    .byte $00
native_int_for_open:
    .byte $00
native_int_for_stack:
    .res NATIVE_INT_MAX_FOR, $00
native_int_for_data_offset:
    .res NATIVE_INT_MAX_FOR, $00
native_int_for_target_lo:
    .res NATIVE_INT_MAX_FOR, $00
native_int_for_target_hi:
    .res NATIVE_INT_MAX_FOR, $00
native_int_for_end_target_lo:
    .res NATIVE_INT_MAX_FOR, $00
native_int_for_end_target_hi:
    .res NATIVE_INT_MAX_FOR, $00
native_int_for_counter_offset:
    .res NATIVE_INT_MAX_FOR, $00
native_int_for_walk_count:
    .byte $00
native_int_for_walk_open:
    .byte $00
native_int_for_walk_stack:
    .res NATIVE_INT_MAX_FOR, $00
native_int_for_current:
    .byte $00
native_int_if_target_lo:
    .res 4, $00
native_int_nested_if_target_lo = native_int_if_target_lo+1
native_int_if_end_target_lo = native_int_if_target_lo+2
native_int_nested_if_end_target_lo = native_int_if_target_lo+3
native_int_if_target_hi:
    .res 4, $00
native_int_nested_if_target_hi = native_int_if_target_hi+1
native_int_if_end_target_hi = native_int_if_target_hi+2
native_int_nested_if_end_target_hi = native_int_if_target_hi+3
native_int_mul_index:
    .byte $FF
native_int_div_index:
    .byte $FF
native_int_print_index:
    .byte $FF
native_int_code_size_lo:
    .byte $00
native_int_code_size_hi:
    .byte $00
native_int_data_size_lo:
    .byte $00
native_int_data_size_hi:
    .byte $00
native_int_var_data_size_lo:
    .byte $00
native_int_var_data_size_hi:
    .byte $00
native_int_root_size_lo:
    .byte $00
native_int_root_size_hi:
    .byte $00
native_int_export_offset_lo:
    .byte $00
native_int_export_offset_hi:
    .byte $00
native_int_export_size_lo:
    .byte $00
native_int_export_size_hi:
    .byte $00
native_int_target_var:
    .byte $00
native_int_var_offset:
    .byte $00
native_int_instruction_size:
    .byte $00
native_int_const_ptr_lo:
    .byte $00
native_int_const_ptr_hi:
    .byte $00
native_int_const_len:
    .byte $00
native_int_const_index:
    .byte $00
native_int_machine_byte:
    .byte $00
native_int_string_offset_lo:
    .byte $00
native_int_string_offset_hi:
    .byte $00
native_int_string_newline:
    .byte $00
native_int_string_pos:
    .byte $00
native_int_reloc_offset_lo:
    .byte $00
native_int_reloc_offset_hi:
    .byte $00
native_int_reloc_import_index:
    .byte $00
native_int_reloc_if_depth:
    .byte $00
native_int_temp_offset_lo:
    .byte $00
native_int_temp_offset_hi:
    .byte $00
native_int_debug_op_count:
    .byte $00
native_int_debug_offsets_lo:
    .res NATIVE_INT_MAX_DEBUG_OPS, $00
native_int_debug_emit_prev:
    .byte $00
native_int_debug_emit_hi:
    .byte $00
