; Compiler-owned lowering for literal-only runtime helper call sequences.

NATIVE_RUNTIME_KIND_SPRITE_DATA = 1
NATIVE_RUNTIME_KIND_SPRITE_POS = 2
NATIVE_RUNTIME_KIND_GFX_BGCOLOR = 3
NATIVE_RUNTIME_KIND_SID_FREQ = 4
NATIVE_RUNTIME_KIND_XA_BYTE = 5
NATIVE_RUNTIME_KIND_XY_WORD = 6
NATIVE_RUNTIME_KIND_NO_ARG = 7
NATIVE_RUNTIME_KIND_A_BYTE = 8
NATIVE_RUNTIME_KIND_AY_BYTE = 9
NATIVE_RUNTIME_KIND_AXY_BYTES_CLC = 10
NATIVE_RUNTIME_KIND_X1_A0_BYTES = 11
NATIVE_RUNTIME_KIND_BYTE_READBACK = 12
NATIVE_RUNTIME_KIND_A_BYTE_READBACK = 13
NATIVE_RUNTIME_KIND_XY_WORD_READBACK = 14
NATIVE_RUNTIME_KIND_AY_BYTE_READBACK = 15
NATIVE_RUNTIME_KIND_AXY_BYTES_CLC_READBACK = 16
NATIVE_RUNTIME_KIND_AXY_E0_BYTES_CLC_READBACK = 17

NATIVE_RUNTIME_SEQUENCE_MAX_ARGS = 4
NATIVE_RUNTIME_SEQUENCE_MAX_CALLS = 16
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
NATIVE_RUNTIME_SEQUENCE_MAX_RELOCS = 64
.else
NATIVE_RUNTIME_SEQUENCE_MAX_RELOCS = 32
.endif
NATIVE_RUNTIME_SEQUENCE_MAX_DEBUG = 64
NATIVE_RUNTIME_SEQUENCE_MAX_STORES = 16
NATIVE_RUNTIME_SEQUENCE_MAX_VARIABLES = 36

native_runtime_sequence_detect:
    lda #$00
    sta native_runtime_sequence_claimed
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$01
    beq :+
    jmp native_runtime_sequence_detect_no
:
    lda #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    jsr load_context_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcs :+
    jmp native_runtime_sequence_detect_no
:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcs :+
    jmp native_runtime_sequence_detect_no
:
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    bne :+
    jmp native_runtime_sequence_detect_no
:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #$00
    sta native_runtime_sequence_emit_mode
    jsr native_runtime_sequence_parse
    bcs native_runtime_sequence_detect_no
    lda native_runtime_sequence_code_size_lo
    sta native_runtime_sequence_total_size_lo
    lda native_runtime_sequence_code_size_hi
    sta native_runtime_sequence_total_size_hi
    lda #$01
    sta native_runtime_sequence_claimed
    sec
    rts
native_runtime_sequence_detect_no:
    lda #$00
    sta native_runtime_sequence_claimed
    clc
    rts

native_runtime_sequence_parse:
    lda #$00
    sta native_runtime_sequence_body_pos
    sta native_runtime_sequence_arg_count
    sta native_runtime_sequence_call_count
    sta native_runtime_sequence_debug_count
    sta native_runtime_sequence_code_size_lo
    sta native_runtime_sequence_code_size_hi
    sta native_runtime_sequence_store_count
    sta native_runtime_sequence_reloc_count
    sta native_runtime_sequence_result_pending
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
    sta native_runtime_sequence_result_arg_index
.endif
    ldx #NATIVE_RUNTIME_SEQUENCE_MAX_VARIABLES-1
native_runtime_sequence_clear_store_values:
    sta native_runtime_sequence_store_valid,x
    dex
    bpl native_runtime_sequence_clear_store_values
native_runtime_sequence_parse_loop:
    ldy native_runtime_sequence_body_pos
    jsr emit_object_peek_payload_y
    cmp #'p'
    bne :+
    jmp native_runtime_sequence_parse_param
:
    cmp #'u'
    bne :+
    jmp native_runtime_sequence_parse_call
:
    cmp #'S'
    bne :+
    jmp native_runtime_sequence_parse_store
:
    cmp #'L'
    bne :+
    jmp native_runtime_sequence_parse_load
:
    cmp #'a'
    bne :+
    jmp native_runtime_sequence_parse_add
:
    cmp #'r'
    bne :+
    jmp native_runtime_sequence_parse_return
:
    sec
    rts

native_runtime_sequence_parse_param:
    jsr native_runtime_sequence_record_debug_offset
    bcs native_runtime_sequence_parse_param_fail
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY = 0
    lda native_runtime_sequence_result_pending
    beq :+
    lda #$00
    sta native_runtime_sequence_result_pending
:
.endif
    lda native_runtime_sequence_arg_count
    cmp #NATIVE_RUNTIME_SEQUENCE_MAX_ARGS
    bcc :+
    sec
    rts
:
    ldy native_runtime_sequence_body_pos
    iny
    jsr emit_object_peek_payload_y
    jsr native_runtime_sequence_decode_selector
    bcs native_runtime_sequence_parse_param_fail
    sta native_runtime_sequence_selector
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp native_runtime_sequence_selector
    beq native_runtime_sequence_parse_param_fail
    bcc native_runtime_sequence_parse_param_fail
    ldx native_runtime_sequence_selector
    jsr native_runtime_sequence_load_literal_x
    ldx native_runtime_sequence_arg_count
    lda native_runtime_sequence_literal_lo
    sta native_runtime_sequence_args_lo,x
    lda native_runtime_sequence_literal_hi
    sta native_runtime_sequence_args_hi,x
    lda #$00
    sta native_runtime_sequence_args_runtime,x
    sta native_runtime_sequence_args_ordinal,x
    inc native_runtime_sequence_arg_count
    inc native_runtime_sequence_body_pos
    inc native_runtime_sequence_body_pos
    jmp native_runtime_sequence_parse_loop
native_runtime_sequence_parse_param_fail:
    jmp native_runtime_sequence_parse_fail

native_runtime_sequence_parse_call:
    jsr native_runtime_sequence_record_debug_offset
    bcc :+
    jmp native_runtime_sequence_parse_call_fail
:
    lda native_runtime_sequence_call_count
    cmp #NATIVE_RUNTIME_SEQUENCE_MAX_CALLS
    bcs native_runtime_sequence_parse_call_early_fail
    ldy native_runtime_sequence_body_pos
    iny
    jsr emit_object_peek_payload_y
    jsr native_runtime_sequence_decode_selector
    bcs native_runtime_sequence_parse_call_early_fail
    sta native_runtime_sequence_import_index
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp native_runtime_sequence_import_index
    beq native_runtime_sequence_parse_call_early_fail
    bcc native_runtime_sequence_parse_call_early_fail
    ldx native_runtime_sequence_import_index
    jsr native_runtime_sequence_kind_for_external_x
    bcs native_runtime_sequence_parse_call_early_fail
    pha
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    pla
    sta native_runtime_sequence_helper_kind
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
    cmp #NATIVE_RUNTIME_KIND_AXY_E0_BYTES_CLC_READBACK+1
.else
    cmp #NATIVE_RUNTIME_KIND_A_BYTE_READBACK+1
.endif
    bcc native_runtime_sequence_parse_call_early_ok
native_runtime_sequence_parse_call_early_fail:
    jmp native_runtime_sequence_parse_fail
native_runtime_sequence_parse_call_early_ok:
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
    lda #$FF
    sta native_runtime_sequence_nested_outer_count
    lda native_runtime_sequence_result_pending
    beq native_runtime_sequence_parse_call_no_prior_result
    lda native_runtime_sequence_helper_kind
    cmp #NATIVE_RUNTIME_KIND_BYTE_READBACK
    bcs native_runtime_sequence_parse_call_spill_prior_result
    ldx #$00
native_runtime_sequence_parse_call_find_prior_runtime:
    cpx native_runtime_sequence_arg_count
    beq native_runtime_sequence_parse_call_materialize_prior_result
    lda native_runtime_sequence_args_runtime,x
    bne native_runtime_sequence_parse_call_spill_prior_result
    inx
    jmp native_runtime_sequence_parse_call_find_prior_runtime
native_runtime_sequence_parse_call_materialize_prior_result:
    jsr native_runtime_sequence_materialize_pending_result
    bcs native_runtime_sequence_parse_call_early_fail
    jmp native_runtime_sequence_parse_call_no_prior_result
native_runtime_sequence_parse_call_spill_prior_result:
    jsr native_runtime_sequence_spill_pending_result
    bcs native_runtime_sequence_parse_call_early_fail
native_runtime_sequence_parse_call_no_prior_result:
    lda native_runtime_sequence_helper_kind
    cmp #NATIVE_RUNTIME_KIND_BYTE_READBACK
    bne native_runtime_sequence_parse_call_not_nested_noarg
    lda native_runtime_sequence_arg_count
    beq native_runtime_sequence_parse_call_regular
    sta native_runtime_sequence_nested_outer_count
    jmp native_runtime_sequence_parse_call_emit_jsr
native_runtime_sequence_parse_call_not_nested_noarg:
    cmp #NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    bne native_runtime_sequence_parse_call_regular
    lda native_runtime_sequence_arg_count
    cmp #$02
    bcc native_runtime_sequence_parse_call_regular
    sec
    sbc #$01
    sta native_runtime_sequence_nested_outer_count
    tax
    lda native_runtime_sequence_args_runtime,x
    bne native_runtime_sequence_parse_call_nested_a_emit
    jsr native_runtime_sequence_load_arg_literal_x
    lda native_runtime_sequence_literal_hi
    bne native_runtime_sequence_parse_call_early_fail
native_runtime_sequence_parse_call_nested_a_emit:
    jsr native_runtime_sequence_emit_a_arg_x
    jmp native_runtime_sequence_parse_call_emit_jsr
native_runtime_sequence_parse_call_regular:
.endif
    jsr native_runtime_sequence_validate_args
    bcs native_runtime_sequence_parse_call_fail
    jsr native_runtime_sequence_emit_current_setup
    bcs native_runtime_sequence_parse_call_fail
native_runtime_sequence_parse_call_emit_jsr:
    lda #$20
    jsr native_runtime_sequence_emit_byte
    ldx native_runtime_sequence_reloc_count
    cpx #NATIVE_RUNTIME_SEQUENCE_MAX_RELOCS
    bcs native_runtime_sequence_parse_call_fail
    lda native_runtime_sequence_code_size_lo
    sta native_runtime_sequence_reloc_offsets_lo,x
    lda native_runtime_sequence_code_size_hi
    sta native_runtime_sequence_reloc_offsets_hi,x
    lda native_runtime_sequence_import_index
    sta native_runtime_sequence_reloc_targets,x
    lda #$00
    sta native_runtime_sequence_reloc_kinds,x
    jsr native_runtime_sequence_emit_zero
    jsr native_runtime_sequence_emit_zero
    inc native_runtime_sequence_reloc_count
    inc native_runtime_sequence_call_count
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
    lda native_runtime_sequence_nested_outer_count
    bmi native_runtime_sequence_parse_call_finish_regular
    sta native_runtime_sequence_arg_count
    sta native_runtime_sequence_result_arg_index
    lda #$01
    sta native_runtime_sequence_result_pending
    jmp native_runtime_sequence_parse_call_advance
native_runtime_sequence_parse_call_finish_regular:
.endif
    lda #$00
    sta native_runtime_sequence_arg_count
    lda native_runtime_sequence_helper_kind
    cmp #NATIVE_RUNTIME_KIND_BYTE_READBACK
    bcc native_runtime_sequence_parse_call_clear_result
    lda #$01
    sta native_runtime_sequence_result_pending
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
    lda #$00
    sta native_runtime_sequence_result_arg_index
    jmp native_runtime_sequence_parse_call_advance
.else
    bne native_runtime_sequence_parse_call_advance
.endif
native_runtime_sequence_parse_call_clear_result:
    lda #$00
    sta native_runtime_sequence_result_pending
native_runtime_sequence_parse_call_advance:
    inc native_runtime_sequence_body_pos
    inc native_runtime_sequence_body_pos
    jmp native_runtime_sequence_parse_loop
native_runtime_sequence_parse_call_fail:
    jmp native_runtime_sequence_parse_fail

.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
native_runtime_sequence_materialize_pending_result:
    lda native_runtime_sequence_arg_count
    cmp #NATIVE_RUNTIME_SEQUENCE_MAX_ARGS
    bcs native_runtime_sequence_materialize_pending_fail
native_runtime_sequence_materialize_pending_shift:
    ldx native_runtime_sequence_arg_count
native_runtime_sequence_materialize_pending_shift_loop:
    cpx native_runtime_sequence_result_arg_index
    beq native_runtime_sequence_materialize_pending_insert
    dex
    txa
    tay
    inx
    lda native_runtime_sequence_args_lo,y
    sta native_runtime_sequence_args_lo,x
    lda native_runtime_sequence_args_hi,y
    sta native_runtime_sequence_args_hi,x
    lda native_runtime_sequence_args_runtime,y
    sta native_runtime_sequence_args_runtime,x
    lda native_runtime_sequence_args_ordinal,y
    sta native_runtime_sequence_args_ordinal,x
    dex
    jmp native_runtime_sequence_materialize_pending_shift_loop
native_runtime_sequence_materialize_pending_insert:
    ldx native_runtime_sequence_result_arg_index
    lda #$00
    sta native_runtime_sequence_args_lo,x
    sta native_runtime_sequence_args_hi,x
    sta native_runtime_sequence_args_ordinal,x
    lda #$02
    sta native_runtime_sequence_args_runtime,x
    inc native_runtime_sequence_arg_count
    lda #$00
    sta native_runtime_sequence_result_pending
    clc
    rts
native_runtime_sequence_materialize_pending_fail:
    sec
    rts

native_runtime_sequence_spill_pending_result:
    lda native_runtime_sequence_store_count
    cmp #NATIVE_RUNTIME_SEQUENCE_MAX_STORES
    bcs native_runtime_sequence_spill_pending_fail
    jsr native_runtime_sequence_emit_result_store
    bcs native_runtime_sequence_spill_pending_fail
    jsr native_runtime_sequence_materialize_pending_result
    bcs native_runtime_sequence_spill_pending_fail
    ldx native_runtime_sequence_result_arg_index
    lda #$01
    sta native_runtime_sequence_args_runtime,x
    lda native_runtime_sequence_store_count
    sta native_runtime_sequence_args_ordinal,x
    inc native_runtime_sequence_store_count
    clc
    rts
native_runtime_sequence_spill_pending_fail:
    sec
    rts
.endif

native_runtime_sequence_parse_store:
    jsr native_runtime_sequence_record_debug_offset
    bcc :+
    jmp native_runtime_sequence_parse_store_fail
:
    lda native_runtime_sequence_result_pending
    bne native_runtime_sequence_parse_store_pending
    lda native_runtime_sequence_arg_count
    cmp #$01
    beq :+
    jmp native_runtime_sequence_parse_store_fail
:
    lda native_runtime_sequence_store_count
    cmp #NATIVE_RUNTIME_SEQUENCE_MAX_STORES
    bcc :+
    jmp native_runtime_sequence_parse_store_fail
:
    ldy native_runtime_sequence_body_pos
    iny
    jsr emit_object_peek_payload_y
    jsr native_runtime_sequence_decode_selector
    bcc :+
    jmp native_runtime_sequence_parse_store_fail
:
    sta native_runtime_sequence_selector
    cmp #NATIVE_RUNTIME_SEQUENCE_MAX_VARIABLES
    bcc :+
    jmp native_runtime_sequence_parse_store_fail
:
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp native_runtime_sequence_selector
    bne :+
    jmp native_runtime_sequence_parse_store_fail
:
    bcs :+
    jmp native_runtime_sequence_parse_store_fail
:
    ldx native_runtime_sequence_selector
    lda native_runtime_sequence_args_lo
    sta native_runtime_sequence_store_values_lo,x
    lda native_runtime_sequence_args_hi
    sta native_runtime_sequence_store_values_hi,x
    lda #$01
    sta native_runtime_sequence_store_valid,x
    lda native_runtime_sequence_args_runtime
    sta native_runtime_sequence_store_runtime,x
    lda native_runtime_sequence_args_ordinal
    sta native_runtime_sequence_store_ordinals,x
    lda native_runtime_sequence_args_runtime
    beq native_runtime_sequence_parse_store_recorded
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    jsr native_runtime_sequence_emit_result_store
    bcs native_runtime_sequence_parse_store_fail
native_runtime_sequence_parse_store_recorded:
    inc native_runtime_sequence_store_count
    lda #$00
    sta native_runtime_sequence_arg_count
    inc native_runtime_sequence_body_pos
    inc native_runtime_sequence_body_pos
    jmp native_runtime_sequence_parse_loop
native_runtime_sequence_parse_store_pending:
    lda native_runtime_sequence_arg_count
    bne native_runtime_sequence_parse_store_fail
    lda native_runtime_sequence_store_count
    cmp #NATIVE_RUNTIME_SEQUENCE_MAX_STORES
    bcs native_runtime_sequence_parse_store_fail
    ldy native_runtime_sequence_body_pos
    iny
    jsr emit_object_peek_payload_y
    jsr native_runtime_sequence_decode_selector
    bcs native_runtime_sequence_parse_store_fail
    sta native_runtime_sequence_selector
    cmp #NATIVE_RUNTIME_SEQUENCE_MAX_VARIABLES
    bcs native_runtime_sequence_parse_store_fail
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp native_runtime_sequence_selector
    beq native_runtime_sequence_parse_store_fail
    bcc native_runtime_sequence_parse_store_fail
    jsr native_runtime_sequence_emit_result_store
    bcs native_runtime_sequence_parse_store_fail
    ldx native_runtime_sequence_selector
    lda #$01
    sta native_runtime_sequence_store_valid,x
    sta native_runtime_sequence_store_runtime,x
    lda #$00
    sta native_runtime_sequence_store_values_lo,x
    sta native_runtime_sequence_store_values_hi,x
    lda native_runtime_sequence_store_count
    sta native_runtime_sequence_store_ordinals,x
    inc native_runtime_sequence_store_count
    lda #$00
    sta native_runtime_sequence_result_pending
    inc native_runtime_sequence_body_pos
    inc native_runtime_sequence_body_pos
    jmp native_runtime_sequence_parse_loop
native_runtime_sequence_parse_store_fail:
    jmp native_runtime_sequence_parse_fail

native_runtime_sequence_parse_load:
    jsr native_runtime_sequence_record_debug_offset
    bcs native_runtime_sequence_parse_load_fail
    lda native_runtime_sequence_arg_count
    cmp #NATIVE_RUNTIME_SEQUENCE_MAX_ARGS
    bcs native_runtime_sequence_parse_load_fail
    ldy native_runtime_sequence_body_pos
    iny
    jsr emit_object_peek_payload_y
    jsr native_runtime_sequence_decode_selector
    bcs native_runtime_sequence_parse_load_fail
    cmp #NATIVE_RUNTIME_SEQUENCE_MAX_VARIABLES
    bcs native_runtime_sequence_parse_load_fail
    tax
    lda native_runtime_sequence_store_valid,x
    beq native_runtime_sequence_parse_load_fail
    ldy native_runtime_sequence_arg_count
    lda native_runtime_sequence_store_values_lo,x
    sta native_runtime_sequence_args_lo,y
    lda native_runtime_sequence_store_values_hi,x
    sta native_runtime_sequence_args_hi,y
    lda native_runtime_sequence_store_runtime,x
    sta native_runtime_sequence_args_runtime,y
    lda native_runtime_sequence_store_ordinals,x
    sta native_runtime_sequence_args_ordinal,y
    inc native_runtime_sequence_arg_count
    inc native_runtime_sequence_body_pos
    inc native_runtime_sequence_body_pos
    jmp native_runtime_sequence_parse_loop
native_runtime_sequence_parse_load_fail:
    jmp native_runtime_sequence_parse_fail

native_runtime_sequence_parse_add:
    jsr native_runtime_sequence_record_debug_offset
    bcs native_runtime_sequence_parse_add_fail
    lda native_runtime_sequence_arg_count
    cmp #$02
    bcc native_runtime_sequence_parse_add_fail
    ldx native_runtime_sequence_arg_count
    dex
    lda native_runtime_sequence_args_runtime,x
    bne native_runtime_sequence_parse_add_fail
    dex
    lda native_runtime_sequence_args_runtime,x
    bne native_runtime_sequence_parse_add_fail
    lda native_runtime_sequence_arg_count
    tax
    dex
    stx native_runtime_sequence_temp_index
    dex
    clc
    lda native_runtime_sequence_args_lo,x
    ldy native_runtime_sequence_temp_index
    adc native_runtime_sequence_args_lo,y
    sta native_runtime_sequence_args_lo,x
    lda native_runtime_sequence_args_hi,x
    adc native_runtime_sequence_args_hi,y
    sta native_runtime_sequence_args_hi,x
    dec native_runtime_sequence_arg_count
    inc native_runtime_sequence_body_pos
    jmp native_runtime_sequence_parse_loop
native_runtime_sequence_parse_add_fail:
    jmp native_runtime_sequence_parse_fail

native_runtime_sequence_parse_return:
    jsr native_runtime_sequence_record_debug_offset
    bcs native_runtime_sequence_parse_fail
    lda native_runtime_sequence_arg_count
    bne native_runtime_sequence_parse_fail
    lda #$00
    sta native_runtime_sequence_result_pending
    lda native_runtime_sequence_call_count
    beq native_runtime_sequence_parse_fail
    ldy native_runtime_sequence_body_pos
    iny
    jsr emit_object_peek_payload_y
    bne native_runtime_sequence_parse_fail
    lda #<native_runtime_sequence_exit
    ldy #>native_runtime_sequence_exit
    ldx #(native_runtime_sequence_exit_end-native_runtime_sequence_exit)
    jsr native_runtime_sequence_emit_const
    lda native_runtime_sequence_store_count
    sta native_runtime_sequence_temp_index
native_runtime_sequence_emit_storage_loop:
    lda native_runtime_sequence_temp_index
    beq native_runtime_sequence_emit_storage_done
    jsr native_runtime_sequence_emit_zero
    jsr native_runtime_sequence_emit_zero
    dec native_runtime_sequence_temp_index
    jmp native_runtime_sequence_emit_storage_loop
native_runtime_sequence_emit_storage_done:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_BODY_DEBUG_COUNT_PTR_LO
    jsr load_indexed_byte_from_context_ptr
    cmp native_runtime_sequence_debug_count
    bne native_runtime_sequence_parse_fail
    clc
    rts
native_runtime_sequence_parse_fail:
    sec
    rts

native_runtime_sequence_record_debug_offset:
    ldx native_runtime_sequence_debug_count
    cpx #NATIVE_RUNTIME_SEQUENCE_MAX_DEBUG
    bcs native_runtime_sequence_record_debug_offset_fail
    lda native_runtime_sequence_code_size_lo
    sta native_runtime_sequence_debug_offsets_lo,x
    lda native_runtime_sequence_code_size_hi
    sta native_runtime_sequence_debug_offsets_hi,x
    inc native_runtime_sequence_debug_count
    clc
    rts
native_runtime_sequence_record_debug_offset_fail:
    sec
    rts

native_runtime_sequence_decode_selector:
    cmp #'0'
    bcc native_runtime_sequence_decode_selector_fail
    cmp #'9'+1
    bcs native_runtime_sequence_decode_selector_letter
    sec
    sbc #'0'
    clc
    rts
native_runtime_sequence_decode_selector_letter:
    jsr lowercase_ascii_overlay
    cmp #'a'
    bcc native_runtime_sequence_decode_selector_fail
    cmp #'z'+1
    bcs native_runtime_sequence_decode_selector_fail
    sec
    sbc #('a'-10)
    clc
    rts
native_runtime_sequence_decode_selector_fail:
    sec
    rts

native_runtime_sequence_kind_for_external_x:
    lda #ACTC_OVERLAY_CTX_SET_EXTERNAL_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    lda #<native_runtime_sequence_helper_table
    sta ACTC_OVERLAY_WORK_ZP
    lda #>native_runtime_sequence_helper_table
    sta ACTC_OVERLAY_WORK_ZP+1
native_runtime_sequence_kind_lookup_loop:
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq native_runtime_sequence_kind_lookup_fail
    sta native_runtime_sequence_table_kind
    jsr native_runtime_sequence_advance_table_ptr
    ldy #$00
native_runtime_sequence_kind_lookup_compare:
    lda (ACTC_OVERLAY_SCAN_ZP),y
    jsr lowercase_ascii_overlay
    cmp (ACTC_OVERLAY_WORK_ZP),y
    bne native_runtime_sequence_kind_lookup_next
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq native_runtime_sequence_kind_lookup_found
    iny
    bne native_runtime_sequence_kind_lookup_compare
native_runtime_sequence_kind_lookup_next:
    ldy #$00
native_runtime_sequence_kind_lookup_skip:
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq native_runtime_sequence_kind_lookup_skipped
    jsr native_runtime_sequence_advance_table_ptr
    jmp native_runtime_sequence_kind_lookup_skip
native_runtime_sequence_kind_lookup_skipped:
    jsr native_runtime_sequence_advance_table_ptr
    jmp native_runtime_sequence_kind_lookup_loop
native_runtime_sequence_kind_lookup_found:
    lda native_runtime_sequence_table_kind
    clc
    rts
native_runtime_sequence_kind_lookup_fail:
    sec
    rts

native_runtime_sequence_advance_table_ptr:
    inc ACTC_OVERLAY_WORK_ZP
    bne :+
    inc ACTC_OVERLAY_WORK_ZP+1
:
    rts

native_runtime_sequence_validate_args:
    ldx native_runtime_sequence_helper_kind
    lda native_runtime_sequence_arg_counts,x
    cmp native_runtime_sequence_arg_count
    beq :+
    sec
    rts
:
    lda #$00
    sta native_runtime_sequence_runtime_arg_count
    ldx #$00
native_runtime_sequence_validate_args_loop:
    cpx native_runtime_sequence_arg_count
    beq native_runtime_sequence_validate_args_ok
    stx native_runtime_sequence_temp_index
    lda native_runtime_sequence_args_runtime,x
    beq :+
    inc native_runtime_sequence_runtime_arg_count
    lda native_runtime_sequence_runtime_arg_count
    cmp #$03
    bcs native_runtime_sequence_validate_args_fail
    jmp native_runtime_sequence_validate_args_next
:
    lda native_runtime_sequence_helper_kind
    cmp #NATIVE_RUNTIME_KIND_SPRITE_DATA
    bne :+
    cpx #$01
    beq native_runtime_sequence_validate_args_next
:
    cmp #NATIVE_RUNTIME_KIND_SID_FREQ
    bne :+
    cpx #$01
    beq native_runtime_sequence_validate_args_next
:
    cmp #NATIVE_RUNTIME_KIND_XY_WORD
    bne :+
    cpx #$00
    beq native_runtime_sequence_validate_args_next
:
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
    cmp #NATIVE_RUNTIME_KIND_XY_WORD_READBACK
    bne :+
    cpx #$00
    beq native_runtime_sequence_validate_args_next
:
.endif
    jsr native_runtime_sequence_load_arg_literal_x
    lda native_runtime_sequence_helper_kind
    cmp #NATIVE_RUNTIME_KIND_SPRITE_POS
    bne native_runtime_sequence_validate_arg_high_zero
    ldx native_runtime_sequence_temp_index
    cpx #$01
    bne native_runtime_sequence_validate_arg_high_zero
    lda native_runtime_sequence_literal_hi
    cmp #$02
    bcs native_runtime_sequence_validate_args_fail
    jmp native_runtime_sequence_validate_args_next
native_runtime_sequence_validate_arg_high_zero:
    lda native_runtime_sequence_literal_hi
    bne native_runtime_sequence_validate_args_fail
native_runtime_sequence_validate_args_next:
    ldx native_runtime_sequence_temp_index
    inx
    jmp native_runtime_sequence_validate_args_loop
native_runtime_sequence_validate_args_ok:
    clc
    rts
native_runtime_sequence_validate_args_fail:
    sec
    rts

native_runtime_sequence_load_arg_literal_x:
    lda native_runtime_sequence_args_lo,x
    sta native_runtime_sequence_literal_lo
    lda native_runtime_sequence_args_hi,x
    sta native_runtime_sequence_literal_hi
    rts
native_runtime_sequence_load_literal_x:
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_runtime_sequence_literal_lo
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_runtime_sequence_literal_hi
    rts

native_runtime_sequence_emit_current_setup:
    lda native_runtime_sequence_helper_kind
    cmp #NATIVE_RUNTIME_KIND_SPRITE_DATA
    bne :+
    jmp native_runtime_sequence_emit_sprite_data
:
    cmp #NATIVE_RUNTIME_KIND_SPRITE_POS
    bne :+
    jmp native_runtime_sequence_emit_sprite_pos
:
    cmp #NATIVE_RUNTIME_KIND_GFX_BGCOLOR
    bne :+
    jmp native_runtime_sequence_emit_single_a
:
    cmp #NATIVE_RUNTIME_KIND_SID_FREQ
    bne :+
    jmp native_runtime_sequence_emit_sid_freq
:
    cmp #NATIVE_RUNTIME_KIND_XA_BYTE
    bne :+
    jmp native_runtime_sequence_emit_xa
:
    cmp #NATIVE_RUNTIME_KIND_XY_WORD
    bne :+
    jmp native_runtime_sequence_emit_xy_word
:
    cmp #NATIVE_RUNTIME_KIND_NO_ARG
    bne :+
    clc
    rts
:
    cmp #NATIVE_RUNTIME_KIND_A_BYTE
    bne :+
    jmp native_runtime_sequence_emit_single_a
:
    cmp #NATIVE_RUNTIME_KIND_AY_BYTE
    bne :+
    jmp native_runtime_sequence_emit_ay
:
    cmp #NATIVE_RUNTIME_KIND_AXY_BYTES_CLC
    bne :+
    jmp native_runtime_sequence_emit_axy
:
    cmp #NATIVE_RUNTIME_KIND_X1_A0_BYTES
    bne :+
    jmp native_runtime_sequence_emit_x1_a0
:
    cmp #NATIVE_RUNTIME_KIND_BYTE_READBACK
    bne :+
    clc
    rts
:
    cmp #NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    bne :+
    jmp native_runtime_sequence_emit_single_a
:
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
    cmp #NATIVE_RUNTIME_KIND_XY_WORD_READBACK
    bne :+
    jmp native_runtime_sequence_emit_xy_word
:
    cmp #NATIVE_RUNTIME_KIND_AY_BYTE_READBACK
    bne :+
    jmp native_runtime_sequence_emit_ay
:
    cmp #NATIVE_RUNTIME_KIND_AXY_BYTES_CLC_READBACK
    bne :+
    jmp native_runtime_sequence_emit_axy
:
    cmp #NATIVE_RUNTIME_KIND_AXY_E0_BYTES_CLC_READBACK
    bne native_runtime_sequence_emit_setup_fail
    jmp native_runtime_sequence_emit_axy_e0
.else
    jmp native_runtime_sequence_emit_setup_fail
.endif
native_runtime_sequence_emit_setup_fail:
    sec
    rts

native_runtime_sequence_emit_single_a:
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    clc
    rts

native_runtime_sequence_emit_sprite_data:
    lda native_runtime_sequence_args_runtime
    beq native_runtime_sequence_emit_sprite_data_not_arg0
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    ldx #$01
    jsr native_runtime_sequence_emit_x_arg_x
    ldx #$01
    jsr native_runtime_sequence_emit_y_high_arg_x
    clc
    rts
native_runtime_sequence_emit_sprite_data_not_arg0:
    lda native_runtime_sequence_args_runtime+1
    beq native_runtime_sequence_emit_sprite_data_literals
    ldx #$01
    jsr native_runtime_sequence_emit_a_arg_x
    lda #$AA
    jsr native_runtime_sequence_emit_byte
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    lda #$A0
    jsr native_runtime_sequence_emit_byte
    jsr native_runtime_sequence_emit_zero
    clc
    rts
native_runtime_sequence_emit_sprite_data_literals:
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    ldx #$01
    jsr native_runtime_sequence_emit_x_arg_x
    ldx #$01
    jsr native_runtime_sequence_emit_y_high_arg_x
    clc
    rts

native_runtime_sequence_emit_sprite_pos:
    lda native_runtime_sequence_args_runtime
    ora native_runtime_sequence_args_runtime+1
    ora native_runtime_sequence_args_runtime+2
    beq native_runtime_sequence_emit_sprite_pos_literals
    jmp native_runtime_sequence_emit_axy
native_runtime_sequence_emit_sprite_pos_literals:
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    ldx #$01
    jsr native_runtime_sequence_emit_x_arg_x
    ldx #$02
    jsr native_runtime_sequence_emit_y_arg_x
    ldx #$01
    jsr native_runtime_sequence_load_arg_literal_x
    lda native_runtime_sequence_literal_hi
    beq :+
    lda #$38
    bne native_runtime_sequence_emit_sprite_pos_carry
:
    lda #$18
native_runtime_sequence_emit_sprite_pos_carry:
    jsr native_runtime_sequence_emit_byte
    clc
    rts

native_runtime_sequence_emit_sid_freq:
    jmp native_runtime_sequence_emit_sprite_data

native_runtime_sequence_emit_xa:
    lda native_runtime_sequence_args_runtime
    beq native_runtime_sequence_emit_xa_not_arg0
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    lda #$AA
    jsr native_runtime_sequence_emit_byte
    ldx #$01
    jsr native_runtime_sequence_emit_a_arg_x
    clc
    rts
native_runtime_sequence_emit_xa_not_arg0:
    lda native_runtime_sequence_args_runtime+1
    beq native_runtime_sequence_emit_xa_literals
    ldx #$01
    jsr native_runtime_sequence_emit_a_arg_x
    ldx #$00
    jsr native_runtime_sequence_emit_x_arg_x
    clc
    rts
native_runtime_sequence_emit_xa_literals:
    ldx #$00
    jsr native_runtime_sequence_emit_x_arg_x
    ldx #$01
    jsr native_runtime_sequence_emit_a_arg_x
    clc
    rts

native_runtime_sequence_emit_x1_a0:
    lda native_runtime_sequence_args_runtime
    beq native_runtime_sequence_emit_x1_a0_not_arg0
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    ldx #$01
    jsr native_runtime_sequence_emit_x_arg_x
    clc
    rts
native_runtime_sequence_emit_x1_a0_not_arg0:
    lda native_runtime_sequence_args_runtime+1
    beq native_runtime_sequence_emit_x1_a0_literals
    ldx #$01
    jsr native_runtime_sequence_emit_a_arg_x
    lda #$AA
    jsr native_runtime_sequence_emit_byte
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    clc
    rts
native_runtime_sequence_emit_x1_a0_literals:
    ldx #$01
    jsr native_runtime_sequence_emit_x_arg_x
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    clc
    rts

native_runtime_sequence_emit_xy_word:
    lda native_runtime_sequence_args_runtime
    beq native_runtime_sequence_emit_xy_word_literal
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    lda #$AA
    jsr native_runtime_sequence_emit_byte
    lda #$A0
    jsr native_runtime_sequence_emit_byte
    jsr native_runtime_sequence_emit_zero
    clc
    rts
native_runtime_sequence_emit_xy_word_literal:
    ldx #$00
    jsr native_runtime_sequence_emit_x_arg_x
    ldx #$00
    jsr native_runtime_sequence_emit_y_high_arg_x
    clc
    rts

native_runtime_sequence_emit_ay:
    lda native_runtime_sequence_args_runtime
    beq native_runtime_sequence_emit_ay_not_arg0
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    ldx #$01
    jsr native_runtime_sequence_emit_y_arg_x
    clc
    rts
native_runtime_sequence_emit_ay_not_arg0:
    lda native_runtime_sequence_args_runtime+1
    beq native_runtime_sequence_emit_ay_literals
    ldx #$01
    jsr native_runtime_sequence_emit_a_arg_x
    lda #$A8
    jsr native_runtime_sequence_emit_byte
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    clc
    rts
native_runtime_sequence_emit_ay_literals:
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    ldx #$01
    jsr native_runtime_sequence_emit_y_arg_x
    clc
    rts

native_runtime_sequence_emit_axy:
    lda native_runtime_sequence_args_runtime
    beq native_runtime_sequence_emit_axy_not_arg0
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    ldx #$01
    jsr native_runtime_sequence_emit_x_arg_x
    ldx #$02
    jsr native_runtime_sequence_emit_y_arg_x
    jmp native_runtime_sequence_emit_axy_clc
native_runtime_sequence_emit_axy_not_arg0:
    lda native_runtime_sequence_args_runtime+1
    beq native_runtime_sequence_emit_axy_not_arg1
    ldx #$01
    jsr native_runtime_sequence_emit_a_arg_x
    lda #$AA
    jsr native_runtime_sequence_emit_byte
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    ldx #$02
    jsr native_runtime_sequence_emit_y_arg_x
    jmp native_runtime_sequence_emit_axy_clc
native_runtime_sequence_emit_axy_not_arg1:
    lda native_runtime_sequence_args_runtime+2
    beq native_runtime_sequence_emit_axy_literals
    ldx #$02
    jsr native_runtime_sequence_emit_a_arg_x
    lda #$A8
    jsr native_runtime_sequence_emit_byte
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    ldx #$01
    jsr native_runtime_sequence_emit_x_arg_x
native_runtime_sequence_emit_axy_clc:
    lda #$18
    jsr native_runtime_sequence_emit_byte
    clc
    rts
native_runtime_sequence_emit_axy_literals:
    ldx #$00
    jsr native_runtime_sequence_emit_a_arg_x
    ldx #$01
    jsr native_runtime_sequence_emit_x_arg_x
    ldx #$02
    jsr native_runtime_sequence_emit_y_arg_x
    lda #$18
    jsr native_runtime_sequence_emit_byte
    clc
    rts

.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
native_runtime_sequence_emit_axy_e0:
    lda native_runtime_sequence_args_runtime
    cmp #$02
    bne native_runtime_sequence_emit_axy_e0_no_direct_a
    lda #$48
    jsr native_runtime_sequence_emit_byte
    ldx #$03
    jsr native_runtime_sequence_emit_a_arg_x
    jsr native_runtime_sequence_emit_sta_e0
    lda #$68
    jsr native_runtime_sequence_emit_byte
    ldx #$01
    jsr native_runtime_sequence_emit_x_arg_x
    ldx #$02
    jsr native_runtime_sequence_emit_y_arg_x
    jmp native_runtime_sequence_emit_axy_clc
native_runtime_sequence_emit_axy_e0_no_direct_a:
    ldx #$03
    jsr native_runtime_sequence_emit_a_arg_x
    jsr native_runtime_sequence_emit_sta_e0
    jmp native_runtime_sequence_emit_axy

native_runtime_sequence_emit_sta_e0:
    lda #$85
    jsr native_runtime_sequence_emit_byte
    lda #$E0
    jmp native_runtime_sequence_emit_byte
.endif

native_runtime_sequence_emit_a_arg_x:
    stx native_runtime_sequence_temp_index
    lda native_runtime_sequence_args_runtime,x
    beq native_runtime_sequence_emit_a_arg_literal
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
    cmp #$02
    bne :+
    clc
    rts
:
.endif
    lda #$AD
    jsr native_runtime_sequence_emit_byte
    ldx native_runtime_sequence_temp_index
    jsr native_runtime_sequence_record_arg_low_reloc_x
    jsr native_runtime_sequence_emit_zero
    lda #$00
    jmp native_runtime_sequence_emit_byte
native_runtime_sequence_emit_a_arg_literal:
    lda #$A9
    jsr native_runtime_sequence_emit_byte
    ldx native_runtime_sequence_temp_index
    jsr native_runtime_sequence_load_arg_literal_x
    lda native_runtime_sequence_literal_lo
    jmp native_runtime_sequence_emit_byte

native_runtime_sequence_emit_x_arg_x:
    stx native_runtime_sequence_temp_index
    lda native_runtime_sequence_args_runtime,x
    beq native_runtime_sequence_emit_x_arg_literal
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
    cmp #$02
    beq native_runtime_sequence_emit_x_arg_direct
.endif
    lda #$AE
    jsr native_runtime_sequence_emit_byte
    ldx native_runtime_sequence_temp_index
    jsr native_runtime_sequence_record_arg_low_reloc_x
    jsr native_runtime_sequence_emit_zero
    lda #$00
    jmp native_runtime_sequence_emit_byte
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
native_runtime_sequence_emit_x_arg_direct:
    lda #$AA
    jmp native_runtime_sequence_emit_byte
.endif
native_runtime_sequence_emit_x_arg_literal:
    lda #$A2
    jsr native_runtime_sequence_emit_byte
    ldx native_runtime_sequence_temp_index
    jsr native_runtime_sequence_load_arg_literal_x
    lda native_runtime_sequence_literal_lo
    jmp native_runtime_sequence_emit_byte

native_runtime_sequence_emit_y_arg_x:
    stx native_runtime_sequence_temp_index
    lda native_runtime_sequence_args_runtime,x
    beq native_runtime_sequence_emit_y_arg_literal
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
    cmp #$02
    beq native_runtime_sequence_emit_y_arg_direct
.endif
    lda #$AC
    jsr native_runtime_sequence_emit_byte
    ldx native_runtime_sequence_temp_index
    jsr native_runtime_sequence_record_arg_low_reloc_x
    jsr native_runtime_sequence_emit_zero
    lda #$00
    jmp native_runtime_sequence_emit_byte
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
native_runtime_sequence_emit_y_arg_direct:
    lda #$A8
    jmp native_runtime_sequence_emit_byte
.endif
native_runtime_sequence_emit_y_arg_literal:
    lda #$A0
    jsr native_runtime_sequence_emit_byte
    ldx native_runtime_sequence_temp_index
    jsr native_runtime_sequence_load_arg_literal_x
    lda native_runtime_sequence_literal_lo
    jmp native_runtime_sequence_emit_byte

native_runtime_sequence_emit_y_high_arg_x:
    stx native_runtime_sequence_temp_index
    lda #$A0
    jsr native_runtime_sequence_emit_byte
    ldx native_runtime_sequence_temp_index
    jsr native_runtime_sequence_load_arg_literal_x
    lda native_runtime_sequence_literal_hi
    jmp native_runtime_sequence_emit_byte

native_runtime_sequence_record_arg_low_reloc_x:
    lda native_runtime_sequence_args_ordinal,x
    asl
    clc
    adc #$02
    jmp native_runtime_sequence_record_local_reloc_a

native_runtime_sequence_record_local_reloc_a:
    sta native_runtime_sequence_reloc_target
    ldx native_runtime_sequence_reloc_count
    cpx #NATIVE_RUNTIME_SEQUENCE_MAX_RELOCS
    bcs native_runtime_sequence_record_local_reloc_fail
    lda native_runtime_sequence_code_size_lo
    sta native_runtime_sequence_reloc_offsets_lo,x
    lda native_runtime_sequence_code_size_hi
    sta native_runtime_sequence_reloc_offsets_hi,x
    lda native_runtime_sequence_reloc_target
    sta native_runtime_sequence_reloc_targets,x
    lda #$01
    sta native_runtime_sequence_reloc_kinds,x
    inc native_runtime_sequence_reloc_count
    clc
    rts
native_runtime_sequence_record_local_reloc_fail:
    sec
    rts

native_runtime_sequence_emit_result_store:
    lda #$8D
    jsr native_runtime_sequence_emit_byte
    lda native_runtime_sequence_store_count
    asl
    clc
    adc #$02
    jsr native_runtime_sequence_record_local_reloc_a
    bcs native_runtime_sequence_emit_result_store_fail
    jsr native_runtime_sequence_emit_zero
    jsr native_runtime_sequence_emit_zero
    lda #$A9
    jsr native_runtime_sequence_emit_byte
    jsr native_runtime_sequence_emit_zero
    lda #$8D
    jsr native_runtime_sequence_emit_byte
    lda native_runtime_sequence_store_count
    asl
    clc
    adc #$03
    jsr native_runtime_sequence_record_local_reloc_a
    bcs native_runtime_sequence_emit_result_store_fail
    jsr native_runtime_sequence_emit_zero
    jsr native_runtime_sequence_emit_zero
    clc
    rts
native_runtime_sequence_emit_result_store_fail:
    sec
    rts

native_runtime_sequence_emit_zero:
    lda #$00
    jmp native_runtime_sequence_emit_byte

native_runtime_sequence_emit_byte:
    sta native_runtime_sequence_byte
    lda native_runtime_sequence_emit_mode
    beq native_runtime_sequence_emit_byte_count
    lda #' '
    jsr emit_char_overlay
    lda native_runtime_sequence_byte
    jsr emit_hex_byte_overlay
native_runtime_sequence_emit_byte_count:
    inc native_runtime_sequence_code_size_lo
    bne :+
    inc native_runtime_sequence_code_size_hi
:
    rts

native_runtime_sequence_emit_const:
    sta native_runtime_sequence_const_ptr
    sty native_runtime_sequence_const_ptr+1
    stx native_runtime_sequence_const_count
    ldy #$00
native_runtime_sequence_emit_const_loop:
    cpy native_runtime_sequence_const_count
    beq native_runtime_sequence_emit_const_done
    lda native_runtime_sequence_const_ptr
    sta ACTC_OVERLAY_WORK_ZP
    lda native_runtime_sequence_const_ptr+1
    sta ACTC_OVERLAY_WORK_ZP+1
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr native_runtime_sequence_emit_byte
    iny
    bne native_runtime_sequence_emit_const_loop
native_runtime_sequence_emit_const_done:
    rts

native_runtime_sequence_emit_debug_offset:
    ldx body_debug_index_data
    lda native_runtime_sequence_debug_offsets_lo,x
    ldy native_runtime_sequence_debug_offsets_hi,x
    jmp emit_word_decimal

native_runtime_sequence_emit_export_list:
    lda #$00
    sta word_value_lo
    sta word_value_hi
    lda native_runtime_sequence_total_size_hi
    beq :+
    jmp native_runtime_sequence_emit_export_fail
:
    lda native_runtime_sequence_total_size_lo
    ldx #$00
    jsr emit_machine_export_line
    lda native_runtime_sequence_store_count
    bne :+
    jmp native_runtime_sequence_emit_export_done
:
    asl
    sta native_runtime_sequence_export_size
    sec
    lda native_runtime_sequence_total_size_lo
    sbc native_runtime_sequence_export_size
    sta word_value_lo
    lda native_runtime_sequence_total_size_hi
    sbc #$00
    sta word_value_hi
    lda #<native_runtime_sequence_name_data
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>native_runtime_sequence_name_data
    sta ACTC_OVERLAY_SCAN_ZP+1
    lda native_runtime_sequence_export_size
    jsr native_runtime_sequence_emit_named_export_line
    lda #$00
    sta native_runtime_sequence_export_store_index
native_runtime_sequence_emit_store_export_loop:
    lda native_runtime_sequence_export_store_index
    cmp native_runtime_sequence_store_count
    bne :+
    jmp native_runtime_sequence_emit_export_done
:
    lda native_runtime_sequence_store_count
    asl
    sta native_runtime_sequence_export_size
    sec
    lda native_runtime_sequence_total_size_lo
    sbc native_runtime_sequence_export_size
    sta word_value_lo
    lda native_runtime_sequence_total_size_hi
    sbc #$00
    sta word_value_hi
    lda native_runtime_sequence_export_store_index
    asl
    clc
    adc word_value_lo
    sta word_value_lo
    bcc :+
    inc word_value_hi
:
    lda word_value_lo
    sta native_runtime_sequence_export_offset_lo
    lda word_value_hi
    sta native_runtime_sequence_export_offset_hi
    lda native_runtime_sequence_export_store_index
    cmp #$0A
    bcc native_runtime_sequence_emit_store_export_digit
    clc
    adc #('a'-10)
    bne native_runtime_sequence_emit_store_export_char_ready
native_runtime_sequence_emit_store_export_digit:
    clc
    adc #'0'
native_runtime_sequence_emit_store_export_char_ready:
    sta native_runtime_sequence_name_store+4
    lda #$00
    sta native_runtime_sequence_name_store+5
    lda #<native_runtime_sequence_name_store
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>native_runtime_sequence_name_store
    sta ACTC_OVERLAY_SCAN_ZP+1
    lda #$01
    jsr native_runtime_sequence_emit_named_export_line
    lda #'h'
    sta native_runtime_sequence_name_store+5
    lda #$00
    sta native_runtime_sequence_name_store+6
    lda #<native_runtime_sequence_name_store
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>native_runtime_sequence_name_store
    sta ACTC_OVERLAY_SCAN_ZP+1
    lda native_runtime_sequence_export_offset_lo
    sta word_value_lo
    lda native_runtime_sequence_export_offset_hi
    sta word_value_hi
    inc word_value_lo
    bne :+
    inc word_value_hi
:
    lda #$01
    jsr native_runtime_sequence_emit_named_export_line
    inc native_runtime_sequence_export_store_index
    jmp native_runtime_sequence_emit_store_export_loop
native_runtime_sequence_emit_export_done:
    clc
    rts
native_runtime_sequence_emit_export_fail:
    sec
    rts

native_runtime_sequence_emit_named_export_line:
    sta native_runtime_sequence_export_size
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr emit_lower_scan_zp_string
    lda #' '
    jsr emit_char_overlay
    lda word_value_lo
    ldy word_value_hi
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda native_runtime_sequence_export_size
    ldy #$00
    jsr emit_word_decimal
    jmp emit_newline

native_runtime_sequence_emit_body_marker_list:
    jsr native_runtime_sequence_select_body
    lda #'b'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #$00
    sta native_runtime_sequence_body_pos
native_runtime_sequence_emit_body_marker_loop:
    ldy native_runtime_sequence_body_pos
    jsr emit_object_peek_payload_y
    cmp #'p'
    bne :+
    inc native_runtime_sequence_body_pos
    inc native_runtime_sequence_body_pos
    jmp native_runtime_sequence_emit_body_marker_loop
:
    cmp #'S'
    beq native_runtime_sequence_emit_body_marker_skip_pair
    cmp #'L'
    beq native_runtime_sequence_emit_body_marker_skip_pair
    cmp #'a'
    bne :+
    inc native_runtime_sequence_body_pos
    jmp native_runtime_sequence_emit_body_marker_loop
:
    cmp #'u'
    bne native_runtime_sequence_emit_body_marker_done
    jsr emit_char_overlay
    inc native_runtime_sequence_body_pos
    ldy native_runtime_sequence_body_pos
    jsr emit_object_peek_payload_y
    jsr emit_char_overlay
    inc native_runtime_sequence_body_pos
    jmp native_runtime_sequence_emit_body_marker_loop
native_runtime_sequence_emit_body_marker_skip_pair:
    inc native_runtime_sequence_body_pos
    inc native_runtime_sequence_body_pos
    jmp native_runtime_sequence_emit_body_marker_loop
native_runtime_sequence_emit_body_marker_done:
    lda #'M'
    jsr emit_char_overlay
    jsr emit_newline
    lda native_runtime_sequence_store_count
    beq native_runtime_sequence_emit_body_marker_done_no_data
    asl
    clc
    adc #$01
    sta native_runtime_sequence_temp_index
native_runtime_sequence_emit_data_body_loop:
    lda #'b'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #'M'
    jsr emit_char_overlay
    jsr emit_newline
    dec native_runtime_sequence_temp_index
    bne native_runtime_sequence_emit_data_body_loop
native_runtime_sequence_emit_body_marker_done_no_data:
    clc
    rts

native_runtime_sequence_emit_machine_code_list:
    jsr native_runtime_sequence_select_body
    lda #'m'
    jsr emit_char_overlay
    lda #$01
    sta native_runtime_sequence_emit_mode
    jsr native_runtime_sequence_parse
    bcc :+
    rts
:
    jsr emit_newline
    lda #$00
    sta native_runtime_sequence_reloc_index
native_runtime_sequence_emit_reloc_loop:
    ldx native_runtime_sequence_reloc_index
    cpx native_runtime_sequence_reloc_count
    beq native_runtime_sequence_emit_machine_done
    lda #'r'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx native_runtime_sequence_reloc_index
    lda native_runtime_sequence_reloc_offsets_lo,x
    ldy native_runtime_sequence_reloc_offsets_hi,x
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    ldx native_runtime_sequence_reloc_index
    lda native_runtime_sequence_reloc_kinds,x
    bne native_runtime_sequence_emit_local_reloc
    lda #'u'
    jsr emit_char_overlay
    ldx native_runtime_sequence_reloc_index
    lda native_runtime_sequence_reloc_targets,x
    jsr emit_object_selector_overlay
    jmp native_runtime_sequence_emit_reloc_newline
native_runtime_sequence_emit_local_reloc:
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx native_runtime_sequence_reloc_index
    lda native_runtime_sequence_reloc_targets,x
    sec
    sbc #$02
    lsr
    php
    cmp #$0A
    bcc native_runtime_sequence_emit_local_reloc_digit
    clc
    adc #('a'-10)
    bne native_runtime_sequence_emit_local_reloc_char_ready
native_runtime_sequence_emit_local_reloc_digit:
    clc
    adc #'0'
native_runtime_sequence_emit_local_reloc_char_ready:
    sta native_runtime_sequence_name_store+4
    lda #$00
    sta native_runtime_sequence_name_store+5
    plp
    bcc native_runtime_sequence_emit_local_reloc_name_ready
    lda #'h'
    sta native_runtime_sequence_name_store+5
native_runtime_sequence_emit_local_reloc_name_ready:
    lda #<native_runtime_sequence_name_store
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>native_runtime_sequence_name_store
    sta ACTC_OVERLAY_SCAN_ZP+1
    jsr emit_lower_scan_zp_string
native_runtime_sequence_emit_reloc_newline:
    jsr emit_newline
    inc native_runtime_sequence_reloc_index
    jmp native_runtime_sequence_emit_reloc_loop
native_runtime_sequence_emit_machine_done:
    clc
    rts

native_runtime_sequence_select_body:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jmp load_resident_body_ptr_to_scan_zp

native_runtime_sequence_exit:
    .byte $A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF
native_runtime_sequence_exit_end:

native_runtime_sequence_name_data:
    .asciiz "__idata"
native_runtime_sequence_name_store:
    .byte "__rs0",$00,$00

native_runtime_sequence_arg_counts:
    .byte 0,2,3,1,2,2,1,0,1,2,3,2,0,1
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
    .byte 1,2,3,4
.endif

native_runtime_sequence_helper_table:
    .byte NATIVE_RUNTIME_KIND_SPRITE_DATA
    .asciiz "rt_sprite_data"
    .byte NATIVE_RUNTIME_KIND_SPRITE_POS
    .asciiz "rt_sprite_pos"
    .byte NATIVE_RUNTIME_KIND_XA_BYTE
    .asciiz "rt_sprite_color"
    .byte NATIVE_RUNTIME_KIND_XA_BYTE
    .asciiz "rt_sprite_ptr"
    .byte NATIVE_RUNTIME_KIND_X1_A0_BYTES
    .asciiz "rt_sprite_set_mc"
    .byte NATIVE_RUNTIME_KIND_A_BYTE
    .asciiz "rt_sprite_on"
    .byte NATIVE_RUNTIME_KIND_A_BYTE
    .asciiz "rt_sprite_off"
    .byte NATIVE_RUNTIME_KIND_AY_BYTE
    .asciiz "rt_sprite_mc"
    .byte NATIVE_RUNTIME_KIND_AY_BYTE
    .asciiz "rt_sprite_xexp"
    .byte NATIVE_RUNTIME_KIND_AY_BYTE
    .asciiz "rt_sprite_yexp"
    .byte NATIVE_RUNTIME_KIND_AY_BYTE
    .asciiz "rt_sprite_prio"
    .byte NATIVE_RUNTIME_KIND_GFX_BGCOLOR
    .asciiz "rt_gfx_bgcolor"
    .byte NATIVE_RUNTIME_KIND_GFX_BGCOLOR
    .asciiz "rt_gfx_bordercolor"
    .byte NATIVE_RUNTIME_KIND_A_BYTE
    .asciiz "rt_gfx_vic_bank"
    .byte NATIVE_RUNTIME_KIND_XY_WORD
    .asciiz "rt_gfx_screen_base"
    .byte NATIVE_RUNTIME_KIND_XY_WORD
    .asciiz "rt_gfx_bitmap_base"
    .byte NATIVE_RUNTIME_KIND_AXY_BYTES_CLC
    .asciiz "rt_gfx_screen_cell"
    .byte NATIVE_RUNTIME_KIND_AXY_BYTES_CLC
    .asciiz "rt_gfx_color_cell"
    .byte NATIVE_RUNTIME_KIND_A_BYTE
    .asciiz "rt_gfx_bitmap_fill"
    .byte NATIVE_RUNTIME_KIND_XY_WORD
    .asciiz "rt_gfx_screen_copy"
    .byte NATIVE_RUNTIME_KIND_XY_WORD
    .asciiz "rt_gfx_color_copy"
    .byte NATIVE_RUNTIME_KIND_XY_WORD
    .asciiz "rt_gfx_bitmap_copy"
    .byte NATIVE_RUNTIME_KIND_SID_FREQ
    .asciiz "rt_sid_freq"
    .byte NATIVE_RUNTIME_KIND_SID_FREQ
    .asciiz "rt_sid_pulse"
    .byte NATIVE_RUNTIME_KIND_AY_BYTE
    .asciiz "rt_sid_wave"
    .byte NATIVE_RUNTIME_KIND_AY_BYTE
    .asciiz "rt_sid_ad"
    .byte NATIVE_RUNTIME_KIND_AY_BYTE
    .asciiz "rt_sid_sr"
    .byte NATIVE_RUNTIME_KIND_A_BYTE
    .asciiz "rt_sid_on"
    .byte NATIVE_RUNTIME_KIND_A_BYTE
    .asciiz "rt_sid_off"
    .byte NATIVE_RUNTIME_KIND_A_BYTE
    .asciiz "rt_sid_vol"
    .byte NATIVE_RUNTIME_KIND_A_BYTE
    .asciiz "rt_sid_mode"
    .byte NATIVE_RUNTIME_KIND_A_BYTE
    .asciiz "rt_sid_route"
    .byte NATIVE_RUNTIME_KIND_A_BYTE
    .asciiz "rt_sid_res"
    .byte NATIVE_RUNTIME_KIND_XY_WORD
    .asciiz "rt_sid_cutoff"
    .byte NATIVE_RUNTIME_KIND_NO_ARG
    .asciiz "rt_sid_rst"
    .byte NATIVE_RUNTIME_KIND_BYTE_READBACK
    .asciiz "rt_sid_osc3"
    .byte NATIVE_RUNTIME_KIND_BYTE_READBACK
    .asciiz "rt_sid_env3"
    .byte NATIVE_RUNTIME_KIND_BYTE_READBACK
    .asciiz "rt_sprite_hit"
    .byte NATIVE_RUNTIME_KIND_BYTE_READBACK
    .asciiz "rt_sprite_hit_bg"
    .byte NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    .asciiz "rt_joy"
    .byte NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    .asciiz "rt_jp"
    .byte NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    .asciiz "rt_jb1"
    .byte NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    .asciiz "rt_jb2"
    .byte NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    .asciiz "rt_mp"
    .byte NATIVE_RUNTIME_KIND_BYTE_READBACK
    .asciiz "rt_mx"
    .byte NATIVE_RUNTIME_KIND_BYTE_READBACK
    .asciiz "rt_my"
    .byte NATIVE_RUNTIME_KIND_BYTE_READBACK
    .asciiz "rt_mb"
    .byte NATIVE_RUNTIME_KIND_BYTE_READBACK
    .asciiz "rt_mb1"
    .byte NATIVE_RUNTIME_KIND_BYTE_READBACK
    .asciiz "rt_mb2"
    .byte NATIVE_RUNTIME_KIND_BYTE_READBACK
    .asciiz "rt_mseen"
    .byte NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    .asciiz "rt_dbf_totalrecs"
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
    .byte NATIVE_RUNTIME_KIND_XY_WORD_READBACK
    .asciiz "rt_dbf_create"
    .byte NATIVE_RUNTIME_KIND_XY_WORD_READBACK
    .asciiz "rt_dbf_open"
    .byte NATIVE_RUNTIME_KIND_AY_BYTE_READBACK
    .asciiz "rt_dbf_go"
    .byte NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    .asciiz "rt_dbf_fieldcount"
    .byte NATIVE_RUNTIME_KIND_AY_BYTE_READBACK
    .asciiz "rt_dbf_fieldlen"
    .byte NATIVE_RUNTIME_KIND_AY_BYTE_READBACK
    .asciiz "rt_dbf_readbyte"
    .byte NATIVE_RUNTIME_KIND_AXY_BYTES_CLC_READBACK
    .asciiz "rt_dbf_readfieldbyte"
    .byte NATIVE_RUNTIME_KIND_AXY_E0_BYTES_CLC_READBACK
    .asciiz "rt_dbf_writefieldbyte"
    .byte NATIVE_RUNTIME_KIND_AXY_BYTES_CLC_READBACK
    .asciiz "rt_dbf_writebyte"
    .byte NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    .asciiz "rt_dbf_append"
    .byte NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    .asciiz "rt_dbf_pack"
    .byte NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    .asciiz "rt_dbf_save"
    .byte NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    .asciiz "rt_dbf_delete"
    .byte NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    .asciiz "rt_dbf_undelete"
    .byte NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    .asciiz "rt_dbf_deleted"
    .byte NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    .asciiz "rt_dbf_headerlen"
    .byte NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    .asciiz "rt_dbf_recordlen"
    .byte NATIVE_RUNTIME_KIND_A_BYTE_READBACK
    .asciiz "rt_dbf_currrecno"
.endif
    .byte NATIVE_RUNTIME_KIND_A_BYTE
    .asciiz "rt_dbf_close"
    .byte NATIVE_RUNTIME_KIND_NO_ARG
    .asciiz "rt_gfx_bitmap_on"
    .byte NATIVE_RUNTIME_KIND_NO_ARG
    .asciiz "rt_gfx_bitmap_off"
    .byte NATIVE_RUNTIME_KIND_NO_ARG
    .asciiz "rt_gfx_mbitmap_on"
    .byte NATIVE_RUNTIME_KIND_NO_ARG
    .asciiz "rt_gfx_mbitmap_off"
    .byte $00

native_runtime_sequence_claimed:
    .byte $00
native_runtime_sequence_emit_mode:
    .byte $00
native_runtime_sequence_body_pos:
    .byte $00
native_runtime_sequence_arg_count:
    .byte $00
native_runtime_sequence_call_count:
    .byte $00
native_runtime_sequence_reloc_count:
    .byte $00
native_runtime_sequence_debug_count:
    .byte $00
native_runtime_sequence_store_count:
    .byte $00
native_runtime_sequence_code_size_lo:
    .byte $00
native_runtime_sequence_code_size_hi:
    .byte $00
native_runtime_sequence_total_size_lo:
    .byte $00
native_runtime_sequence_total_size_hi:
    .byte $00
native_runtime_sequence_selector:
    .byte $00
native_runtime_sequence_import_index:
    .byte $00
native_runtime_sequence_helper_kind:
    .byte $00
native_runtime_sequence_table_kind:
    .byte $00
native_runtime_sequence_temp_index:
    .byte $00
native_runtime_sequence_runtime_arg_count:
    .byte $00
native_runtime_sequence_literal_lo:
    .byte $00
native_runtime_sequence_literal_hi:
    .byte $00
native_runtime_sequence_byte:
    .byte $00
native_runtime_sequence_const_count:
    .byte $00
native_runtime_sequence_reloc_index:
    .byte $00
native_runtime_sequence_export_size:
    .byte $00
native_runtime_sequence_export_store_index:
    .byte $00
native_runtime_sequence_export_offset_lo:
    .byte $00
native_runtime_sequence_export_offset_hi:
    .byte $00
native_runtime_sequence_reloc_target:
    .byte $00
native_runtime_sequence_const_ptr:
    .word $0000
native_runtime_sequence_args_lo:
    .res NATIVE_RUNTIME_SEQUENCE_MAX_ARGS
native_runtime_sequence_args_hi:
    .res NATIVE_RUNTIME_SEQUENCE_MAX_ARGS
native_runtime_sequence_args_runtime:
    .res NATIVE_RUNTIME_SEQUENCE_MAX_ARGS
native_runtime_sequence_args_ordinal:
    .res NATIVE_RUNTIME_SEQUENCE_MAX_ARGS
native_runtime_sequence_store_valid:
    .res NATIVE_RUNTIME_SEQUENCE_MAX_VARIABLES
native_runtime_sequence_store_values_lo:
    .res NATIVE_RUNTIME_SEQUENCE_MAX_VARIABLES
native_runtime_sequence_store_values_hi:
    .res NATIVE_RUNTIME_SEQUENCE_MAX_VARIABLES
native_runtime_sequence_store_runtime:
    .res NATIVE_RUNTIME_SEQUENCE_MAX_VARIABLES
native_runtime_sequence_store_ordinals:
    .res NATIVE_RUNTIME_SEQUENCE_MAX_VARIABLES
native_runtime_sequence_result_pending:
    .byte $00
.if ACTC_EMIT_NATIVE_RUNTIME_NESTED_ONLY
native_runtime_sequence_result_arg_index:
    .byte $00
native_runtime_sequence_nested_outer_count:
    .byte $00
.endif
native_runtime_sequence_reloc_offsets_lo:
    .res NATIVE_RUNTIME_SEQUENCE_MAX_RELOCS
native_runtime_sequence_reloc_offsets_hi:
    .res NATIVE_RUNTIME_SEQUENCE_MAX_RELOCS
native_runtime_sequence_reloc_targets:
    .res NATIVE_RUNTIME_SEQUENCE_MAX_RELOCS
native_runtime_sequence_reloc_kinds:
    .res NATIVE_RUNTIME_SEQUENCE_MAX_RELOCS
native_runtime_sequence_debug_offsets_lo:
    .res NATIVE_RUNTIME_SEQUENCE_MAX_DEBUG
native_runtime_sequence_debug_offsets_hi:
    .res NATIVE_RUNTIME_SEQUENCE_MAX_DEBUG
