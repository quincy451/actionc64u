.include "actc_overlay_abi.inc"

.export actc_overlay_header
.export actc_overlay_entry
.export actc_overlay_end

OVERLAY_NAME_STRIDE = 25
OVERLAY_VAR_MAX = 16
OVERLAY_EXPORT_MAX = 16
OVERLAY_FIXED_MAX = ACTC_FIXED_ROUTINE_MAX
INIT_CAPTURE_LIMIT = 512
ACTC_OVERLAY_CACHE_ZP = ACTC_OVERLAY_SCAN_ZP

.segment "CODE"

actc_overlay_header:
    .byte 'A','C','O','V'
    .byte ACTC_OVERLAY_ABI_VERSION
    .byte ACTC_OVERLAY_PASS_DECL_COUNTS
    .word ACTC_OVERLAY_EXEC_BASE
    .word actc_overlay_entry
    .word actc_overlay_end - actc_overlay_header
    .word $0000

actc_overlay_entry:
    stx ACTC_OVERLAY_CONTEXT_ZP
    sty ACTC_OVERLAY_CONTEXT_ZP+1
    ldy #ACTC_OVERLAY_CTX_PASS_ID
    lda #ACTC_OVERLAY_PASS_DECL_COUNTS
    sta (ACTC_OVERLAY_CONTEXT_ZP),y

    ldy #ACTC_OVERLAY_CTX_SOURCE_WINDOW_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP
    ldy #ACTC_OVERLAY_CTX_SOURCE_WINDOW_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP+1
    lda #$00
    sta source_mark
    sta source_mark+1
    sta source_mark+2
    sta source_page_failed
    sta decl_var_count
    sta var_total_count
    sta decl_proc_count
    sta seen_proc
    sta proc_flags_current
    sta fixed_decl_count
    sta routine_binding_current
    lda #$FF
    sta current_proc_index
    jsr load_source_window_remaining_from_context

    jsr skip_blank_lines_and_spaces
    jsr match_module_keyword
    bcc :+
    jmp decl_counts_fail
:
    jsr skip_source_line

decl_counts_loop:
    lda source_page_failed
    beq :+
    jmp decl_counts_fail
:
    jsr skip_blank_lines_and_spaces
    lda source_page_failed
    beq :+
    jmp decl_counts_fail
:
    lda source_window_remaining
    ora source_window_remaining+1
    bne :+
    jmp decl_counts_done
:
    ldy #$00
    jsr overlay_source_peek_scan_y
    bne :+
    jmp decl_counts_done
:

    jsr match_asmblock_keyword
    bcs decl_counts_try_proc
    jsr skip_source_whitespace
    lda #'['
    jsr overlay_source_consume_expected_char
    bcs decl_counts_asmblock_fail
decl_counts_skip_asmblock:
    lda source_page_failed
    bne decl_counts_asmblock_fail
    ldy #$00
    jsr overlay_source_peek_scan_y
    beq decl_counts_asmblock_fail
    cmp #']'
    beq decl_counts_close_asmblock
    jsr overlay_source_consume_scan_ptr
    bcs decl_counts_asmblock_fail
    jmp decl_counts_skip_asmblock
decl_counts_close_asmblock:
    jsr overlay_source_consume_scan_ptr
    bcs decl_counts_asmblock_fail
    jsr skip_source_line
    jmp decl_counts_loop

decl_counts_asmblock_fail:
    jmp decl_counts_fail

decl_counts_try_proc:
    jsr match_proc_keyword
    bcs decl_counts_try_scalar
    lda #$00
    sta proc_flags_current
decl_counts_write_routine:
    jsr write_proc_export_decl
    bcc :+
    jmp decl_counts_fail
:
    lda routine_binding_current
    bne decl_counts_write_routine_fixed
    lda #$01
    sta seen_proc
    inc decl_proc_count
decl_counts_write_routine_fixed:
    jsr skip_source_line
    jmp decl_counts_loop
decl_counts_try_scalar:
    jsr match_scalar_decl_keyword
    bcs decl_counts_try_return
    jsr skip_inline_spaces
    jsr match_func_keyword
    bcs decl_counts_scalar_decl
    lda decl_width_current
    cmp #$02
    beq decl_counts_word_function
    cmp #$04
    bne decl_counts_function_fail
    lda #(ACTC_PROC_META_FUNCTION | ACTC_PROC_META_REAL_RETURN)
    bne decl_counts_store_function_flags
decl_counts_word_function:
    lda decl_type_current
    cmp #'b'
    bne decl_counts_card_int_function
    lda #(ACTC_PROC_META_FUNCTION | ACTC_PROC_META_BYTE_RETURN)
    bne decl_counts_store_function_flags
decl_counts_card_int_function:
    lda #ACTC_PROC_META_FUNCTION
decl_counts_store_function_flags:
    sta proc_flags_current
    jmp decl_counts_write_routine
decl_counts_function_fail:
    jmp decl_counts_fail
decl_counts_scalar_decl:
    lda seen_proc
    bne decl_counts_proc_local
    jsr write_module_var_decl
    bcs decl_counts_fail
    inc decl_var_count
    inc var_total_count
    jmp decl_counts_skip_line
decl_counts_skip_line:
    jsr skip_source_line
    jmp decl_counts_loop

decl_counts_proc_local:
    jsr write_proc_local_var_decl
    bcs decl_counts_fail
    jmp decl_counts_skip_line

decl_counts_try_return:
    jsr match_return_keyword
    bcs decl_counts_skip_line
    lda current_proc_index
    cmp #$FF
    beq decl_counts_fail
    jsr skip_inline_spaces
    lda proc_flags_current
    bmi decl_counts_return_function
    jmp decl_counts_skip_line
decl_counts_return_function:
    ldy #$00
    jsr overlay_source_peek_scan_y
    cmp #'('
    bne decl_counts_fail
    jmp decl_counts_skip_line

decl_counts_done:
    jsr resolve_linked_fixed_targets
    bcs decl_counts_fail
    ldy #ACTC_OVERLAY_CTX_SOURCE_MARK_LO
    lda source_mark
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    ldy #ACTC_OVERLAY_CTX_SOURCE_MARK_HI
    lda source_mark+1
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    ldy #ACTC_OVERLAY_CTX_SOURCE_MARK_BANK
    lda source_mark+2
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    ldy #ACTC_OVERLAY_CTX_DECL_VAR_COUNT
    lda decl_var_count
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    ldy #ACTC_OVERLAY_CTX_DECL_PROC_COUNT
    lda decl_proc_count
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    jsr write_resident_decl_counts
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_OK
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    clc
    lda #ACTC_OVERLAY_STATUS_OK
    rts

decl_counts_fail:
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_FAILED
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    sec
    lda #ACTC_OVERLAY_STATUS_FAILED
    rts

write_resident_decl_counts:
    ldy #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP
    ldy #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP+1
    ldy #$00
    lda var_total_count
    sta (ACTC_OVERLAY_SCAN_ZP),y

    ldy #ACTC_OVERLAY_CTX_MODULE_VAR_COUNT_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP
    ldy #ACTC_OVERLAY_CTX_MODULE_VAR_COUNT_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP+1
    ldy #$00
    lda decl_var_count
    sta (ACTC_OVERLAY_SCAN_ZP),y

    ldy #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP
    ldy #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP+1
    ldy #$00
    lda decl_proc_count
    sta (ACTC_OVERLAY_SCAN_ZP),y

    ldy #ACTC_OVERLAY_CTX_FIXED_COUNT_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP
    ldy #ACTC_OVERLAY_CTX_FIXED_COUNT_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP+1
    ldy #$00
    lda fixed_decl_count
    sta (ACTC_OVERLAY_SCAN_ZP),y
    rts

resolve_linked_fixed_targets:
    lda #$00
    sta fixed_resolve_index
resolve_linked_fixed_targets_loop:
    lda fixed_resolve_index
    cmp fixed_decl_count
    beq resolve_linked_fixed_targets_done
    tax
    jsr load_fixed_meta_cache_x
    jsr load_fixed_meta_window_ptr
    ldy #ACTC_FIXED_META_BINDING
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp #ACTC_FIXED_BINDING_LINKED
    bne resolve_linked_fixed_targets_next
    ldx fixed_resolve_index
    jsr load_fixed_target_name_cache_x
    jsr find_export_name_cache_match
    bcs resolve_linked_fixed_targets_fail
    jsr load_fixed_meta_window_ptr
    lda cache_index
    ldy #ACTC_FIXED_META_RESERVED
    sta (ACTC_OVERLAY_WORK_ZP),y
    ldx fixed_resolve_index
    jsr store_fixed_meta_cache_x
    ldx fixed_resolve_index
    jsr load_fixed_name_cache_x
    ldx fixed_resolve_index
    jsr call_store_fixed_decl
resolve_linked_fixed_targets_next:
    inc fixed_resolve_index
    jmp resolve_linked_fixed_targets_loop
resolve_linked_fixed_targets_done:
    clc
    rts
resolve_linked_fixed_targets_fail:
    sec
    rts

write_module_var_decl:
    jsr skip_inline_spaces
    jsr write_var_debug_offset_window
    jsr clear_var_name_window
    jsr copy_symbol_to_var_name_window
    bcs write_module_var_decl_fail
    jsr ensure_var_capacity
    bcs write_module_var_decl_fail
    jsr find_module_var_name_cache_match
    bcc write_module_var_decl_fail
    ldx var_total_count
    jsr call_store_var_debug_offset
    jsr clear_decl_init_current
    jsr validate_module_decl_tail
    bcs write_module_var_decl_fail
    jsr write_var_meta_window
    ldx var_total_count
    jsr store_var_name_cache_x
    ldx var_total_count
    jsr call_store_var_name
    ldx var_total_count
    jsr call_store_var_meta
    clc
write_module_var_decl_done:
    rts
write_module_var_decl_fail:
    sec
    rts

write_proc_export_decl:
    lda #$00
    sta routine_binding_current
    jsr skip_inline_spaces
    jsr write_proc_debug_offset_window
    jsr clear_export_name_window
    jsr copy_symbol_to_export_name_window
    bcs write_proc_export_decl_fail
    jsr find_export_name_cache_match
    bcc write_proc_export_decl_fail
    jsr find_fixed_name_cache_match
    bcc write_proc_export_decl_fail
    jsr skip_inline_spaces
    jsr parse_optional_routine_binding
    bcs write_proc_export_decl_fail
    lda routine_binding_current
    beq write_proc_export_decl_local
    jsr write_fixed_routine_decl
    bcs write_proc_export_decl_fail
    lda #$FF
    sta current_proc_index
    clc
    rts
write_proc_export_decl_local:
    jsr ensure_export_capacity
    bcs write_proc_export_decl_fail
    ldx decl_proc_count
    jsr call_store_proc_debug_offset
    lda var_total_count
    sta proc_param_base_current
    lda #$00
    sta proc_param_count_current
    lda #$02
    sta decl_width_current
    lda #'i'
    sta decl_type_current
    jsr parse_proc_params
    bcs write_proc_export_decl_fail
    lda var_total_count
    sta proc_local_base_current
    lda #$00
    sta proc_local_count_current
    jsr write_proc_meta_window
    ldx decl_proc_count
    jsr store_export_name_cache_x
    ldx decl_proc_count
    jsr call_store_export_name
    ldx decl_proc_count
    jsr call_store_proc_meta
    lda decl_proc_count
    sta current_proc_index
    clc
write_proc_export_decl_done:
    rts
write_proc_export_decl_fail:
    sec
    rts

write_proc_local_var_decl:
    lda proc_flags_current
    and #ACTC_PROC_META_MACHINE
    beq :+
    jmp write_proc_local_var_decl_fail
:
    lda #$00
    sta proc_local_decl_grouped_current
write_proc_local_var_decl_loop:
    jsr skip_inline_spaces
    jsr write_var_debug_offset_window
    jsr clear_var_name_window
    jsr copy_symbol_to_var_name_window
    bcs write_proc_local_var_decl_fail
    jsr ensure_var_capacity
    bcs write_proc_local_var_decl_fail
    jsr find_current_param_name_cache_match
    bcc write_proc_local_var_decl_fail
    jsr find_current_local_name_cache_match
    bcc write_proc_local_var_decl_fail
    ldx var_total_count
    jsr call_store_var_debug_offset
    jsr skip_inline_spaces
    lda #','
    jsr overlay_source_match_expected_char
    bcc write_proc_local_var_decl_comma
    lda proc_local_decl_grouped_current
    beq write_proc_local_var_decl_validate_tail
    jsr require_line_end
    bcs write_proc_local_var_decl_fail
    jmp write_proc_local_var_decl_store_final
write_proc_local_var_decl_validate_tail:
    jsr validate_decl_tail
    bcs write_proc_local_var_decl_fail
write_proc_local_var_decl_store_final:
    jsr clear_decl_init_current
    jsr write_proc_local_var_decl_store
    rts
write_proc_local_var_decl_comma:
    lda #','
    jsr overlay_source_consume_expected_char
    bcs write_proc_local_var_decl_fail
    lda #$01
    sta proc_local_decl_grouped_current
    jsr clear_decl_init_current
    jsr write_proc_local_var_decl_store
    bcs write_proc_local_var_decl_fail
    jmp write_proc_local_var_decl_loop

write_proc_local_var_decl_store:
    jsr write_var_meta_window
    ldx var_total_count
    jsr store_var_name_cache_x
    ldx var_total_count
    jsr call_store_var_name
    ldx var_total_count
    jsr call_store_var_meta
    inc var_total_count
    inc proc_local_count_current
    jsr write_proc_meta_window
    ldx current_proc_index
    jsr call_store_proc_meta
    clc
    rts
write_proc_local_var_decl_fail:
    sec
    rts

parse_proc_params:
    jsr skip_inline_spaces
    lda #'('
    jsr overlay_source_consume_expected_char
    bcc parse_proc_params_open
    jsr require_line_end
    rts
parse_proc_params_open:
    jsr skip_inline_spaces
    lda #')'
    jsr overlay_source_match_expected_char
    bcs parse_proc_params_loop
    clc
    rts
parse_proc_params_loop:
    jsr match_scalar_decl_keyword
    bcs parse_proc_params_have_type
    jsr skip_inline_spaces
parse_proc_params_have_type:
    lda proc_flags_current
    and #ACTC_PROC_META_MACHINE
    beq :+
    lda decl_width_current
    cmp #$04
    beq parse_proc_params_fail
:
    jsr clear_var_name_window
    jsr write_var_debug_offset_window
    jsr copy_symbol_to_var_name_window
    bcc :+
    sec
    rts
:
    jsr ensure_var_capacity
    bcs parse_proc_params_fail
    jsr find_module_var_name_cache_match
    bcc parse_proc_params_fail
    jsr find_current_param_name_cache_match
    bcc parse_proc_params_fail
    ldx var_total_count
    jsr call_store_var_debug_offset
    jsr clear_decl_init_current
    jsr write_var_meta_window
    ldx var_total_count
    jsr store_var_name_cache_x
    ldx var_total_count
    jsr call_store_var_name
    ldx var_total_count
    jsr call_store_var_meta
    inc var_total_count
    inc proc_param_count_current
    lda proc_param_count_current
    cmp #ACTC_PROC_META_PARAM_COUNT_MASK+1
    bcs parse_proc_params_fail
    jsr skip_inline_spaces
    lda #','
    jsr overlay_source_match_expected_char
    bcc parse_proc_params_next
    lda #')'
    jsr overlay_source_match_expected_char
    bcc parse_proc_params_done
parse_proc_params_fail:
    sec
    rts
parse_proc_params_next:
    lda #','
    jsr overlay_source_consume_expected_char
    bcs parse_proc_params_fail
    jsr skip_inline_spaces
    jmp parse_proc_params_loop
parse_proc_params_done:
    lda #')'
    jsr overlay_source_consume_expected_char
    bcs parse_proc_params_fail
    jsr require_line_end
    rts

; Classify an optional routine binding. =* introduces a local inline machine
; body; a numeric address records an absolute call target; a symbol optionally
; followed by +constant records a declaration-only alias to a local routine.
parse_optional_routine_binding:
    lda #'='
    jsr overlay_source_match_expected_char
    bcs parse_optional_routine_binding_absent
    lda #'='
    jsr overlay_source_consume_expected_char
    bcs parse_optional_routine_binding_fail_near
    jsr skip_inline_spaces
    lda #'*'
    jsr overlay_source_match_expected_char
    bcs parse_optional_routine_binding_fixed
    lda #'*'
    jsr overlay_source_consume_expected_char
    bcs parse_optional_routine_binding_fail_near
    jsr skip_inline_spaces
    lda proc_flags_current
    and #ACTC_PROC_META_REAL_RETURN
    bne parse_optional_routine_binding_fail_near
    lda proc_flags_current
    ora #ACTC_PROC_META_MACHINE
    sta proc_flags_current
parse_optional_routine_binding_absent:
    clc
    rts
parse_optional_routine_binding_fail_near:
    jmp parse_optional_routine_binding_fail
parse_optional_routine_binding_fixed:
    lda proc_flags_current
    and #ACTC_PROC_META_REAL_RETURN
    bne parse_optional_routine_binding_fail_near
    ldy #$00
    jsr overlay_source_peek_scan_y
    jsr uppercase_ascii
    jsr uppercase_symbol_start_valid
    bcc parse_optional_routine_binding_linked
    jsr parse_fixed_absolute_address
    bcs parse_optional_routine_binding_fail_near
    lda #$01
    sta routine_binding_current
    jsr skip_inline_spaces
    clc
    rts
parse_optional_routine_binding_linked:
    ldx fixed_decl_count
    jsr store_fixed_name_cache_x
    jsr clear_export_name_window
    jsr copy_symbol_to_export_name_window
    bcs parse_optional_routine_binding_fail_near
    ldx fixed_decl_count
    jsr store_fixed_target_name_cache_x
    ldx fixed_decl_count
    jsr load_fixed_name_cache_x
    lda #$00
    sta fixed_address_lo_current
    sta fixed_address_hi_current
    jsr skip_inline_spaces
    lda #'+'
    jsr overlay_source_match_expected_char
    bcs parse_optional_routine_binding_linked_done
    lda #'+'
    jsr overlay_source_consume_expected_char
    bcs parse_optional_routine_binding_fail
    jsr skip_inline_spaces
    lda #$00
    sta fixed_addend_negative
    lda #'-'
    jsr overlay_source_match_expected_char
    bcs parse_optional_routine_binding_linked_value
    lda #'-'
    jsr overlay_source_consume_expected_char
    bcs parse_optional_routine_binding_fail
    inc fixed_addend_negative
parse_optional_routine_binding_linked_value:
    jsr parse_fixed_absolute_address
    bcs parse_optional_routine_binding_fail
    lda fixed_addend_negative
    beq parse_optional_routine_binding_linked_positive
    lda fixed_address_lo_current
    ora fixed_address_hi_current
    beq parse_optional_routine_binding_fail
    lda fixed_address_hi_current
    cmp #$80
    bcc parse_optional_routine_binding_linked_negate
    bne parse_optional_routine_binding_fail
    lda fixed_address_lo_current
    bne parse_optional_routine_binding_fail
parse_optional_routine_binding_linked_negate:
    sec
    lda #$00
    sbc fixed_address_lo_current
    sta fixed_address_lo_current
    lda #$00
    sbc fixed_address_hi_current
    sta fixed_address_hi_current
    jmp parse_optional_routine_binding_linked_done
parse_optional_routine_binding_linked_positive:
    lda fixed_address_hi_current
    bmi parse_optional_routine_binding_fail
parse_optional_routine_binding_linked_done:
    lda #$02
    sta routine_binding_current
    jsr skip_inline_spaces
    clc
    rts
parse_optional_routine_binding_fail:
    sec
    rts

write_fixed_routine_decl:
    lda fixed_decl_count
    cmp #OVERLAY_FIXED_MAX
    bcs write_fixed_routine_decl_fail
    lda #$00
    sta fixed_param_count_current
    sta fixed_word_mask_lo_current
    sta fixed_word_mask_hi_current
    sta fixed_byte_count_current
    jsr parse_fixed_proc_params
    bcs write_fixed_routine_decl_fail
    jsr write_fixed_meta_window
    ldx fixed_decl_count
    jsr store_fixed_name_cache_x
    ldx fixed_decl_count
    jsr call_store_fixed_decl
    inc fixed_decl_count
    clc
    rts
write_fixed_routine_decl_fail:
    sec
    rts

parse_fixed_proc_params:
    lda #$02
    sta decl_width_current
    lda #'i'
    sta decl_type_current
    jsr skip_inline_spaces
    lda #'('
    jsr overlay_source_consume_expected_char
    bcs parse_fixed_proc_params_fail
    jsr skip_inline_spaces
    lda #')'
    jsr overlay_source_match_expected_char
    bcc parse_fixed_proc_params_done
parse_fixed_proc_params_loop:
    jsr match_scalar_decl_keyword
    bcs parse_fixed_proc_params_have_type
    jsr skip_inline_spaces
parse_fixed_proc_params_have_type:
    lda decl_width_current
    cmp #$04
    beq parse_fixed_proc_params_fail
    cmp #$02
    bne parse_fixed_proc_params_fail
    jsr clear_var_name_window
    jsr copy_symbol_to_var_name_window
    bcs parse_fixed_proc_params_fail
    lda fixed_param_count_current
    cmp #ACTC_PROC_META_PARAM_COUNT_MASK
    bcs parse_fixed_proc_params_fail
    ldx fixed_param_count_current
    lda decl_type_current
    cmp #'b'
    beq parse_fixed_proc_params_byte
    txa
    cmp #$08
    bcc parse_fixed_proc_params_word_low
    sec
    sbc #$08
    tax
    lda fixed_param_bit_table,x
    ora fixed_word_mask_hi_current
    sta fixed_word_mask_hi_current
    bne parse_fixed_proc_params_word_count
parse_fixed_proc_params_word_low:
    lda fixed_param_bit_table,x
    ora fixed_word_mask_lo_current
    sta fixed_word_mask_lo_current
parse_fixed_proc_params_word_count:
    inc fixed_byte_count_current
parse_fixed_proc_params_byte:
    inc fixed_byte_count_current
    lda fixed_byte_count_current
    cmp #17
    bcs parse_fixed_proc_params_fail
    inc fixed_param_count_current
    jsr skip_inline_spaces
    lda #','
    jsr overlay_source_match_expected_char
    bcc parse_fixed_proc_params_next
    lda #')'
    jsr overlay_source_match_expected_char
    bcc parse_fixed_proc_params_done
parse_fixed_proc_params_fail:
    sec
    rts
parse_fixed_proc_params_next:
    lda #','
    jsr overlay_source_consume_expected_char
    bcs parse_fixed_proc_params_fail
    jsr skip_inline_spaces
    jmp parse_fixed_proc_params_loop
parse_fixed_proc_params_done:
    lda #')'
    jsr overlay_source_consume_expected_char
    bcs parse_fixed_proc_params_fail
    jsr require_line_end
    rts

write_fixed_meta_window:
    ldy #ACTC_OVERLAY_CTX_FIXED_META_WINDOW_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    ldy #ACTC_OVERLAY_CTX_FIXED_META_WINDOW_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP+1
    lda proc_flags_current
    ora #ACTC_PROC_META_MACHINE
    ora fixed_param_count_current
    ldy #ACTC_FIXED_META_FLAGS
    sta (ACTC_OVERLAY_WORK_ZP),y
    lda fixed_word_mask_lo_current
    ldy #ACTC_FIXED_META_WORD_MASK_LO
    sta (ACTC_OVERLAY_WORK_ZP),y
    lda fixed_word_mask_hi_current
    ldy #ACTC_FIXED_META_WORD_MASK_HI
    sta (ACTC_OVERLAY_WORK_ZP),y
    lda fixed_byte_count_current
    ldy #ACTC_FIXED_META_BYTE_COUNT
    sta (ACTC_OVERLAY_WORK_ZP),y
    lda fixed_address_lo_current
    ldy #ACTC_FIXED_META_ADDRESS_LO
    sta (ACTC_OVERLAY_WORK_ZP),y
    lda fixed_address_hi_current
    ldy #ACTC_FIXED_META_ADDRESS_HI
    sta (ACTC_OVERLAY_WORK_ZP),y
    lda routine_binding_current
    sec
    sbc #$01
    ldy #ACTC_FIXED_META_BINDING
    sta (ACTC_OVERLAY_WORK_ZP),y
    lda #$00
    ldy #ACTC_FIXED_META_RESERVED
    sta (ACTC_OVERLAY_WORK_ZP),y
    ldx fixed_decl_count
    jsr store_fixed_meta_cache_x
    rts

parse_fixed_absolute_address:
    lda #$00
    sta fixed_address_lo_current
    sta fixed_address_hi_current
    sta fixed_address_digit_count
    ldy #$00
    jsr overlay_source_peek_scan_y
    cmp #'$'
    beq parse_fixed_absolute_hex
    cmp #'%'
    beq parse_fixed_absolute_binary
    jmp parse_fixed_absolute_decimal_loop

parse_fixed_absolute_hex:
    jsr overlay_source_consume_scan_ptr
    bcc :+
    jmp parse_fixed_absolute_address_fail
:
parse_fixed_absolute_hex_loop:
    ldy #$00
    jsr overlay_source_peek_scan_y
    jsr fixed_hex_digit_from_a
    bcc :+
    jmp parse_fixed_absolute_address_done
:
    sta fixed_address_digit_data
    ldx #$04
parse_fixed_absolute_hex_shift:
    jsr fixed_address_shift_left
    bcc :+
    jmp parse_fixed_absolute_address_fail
:
    dex
    bne parse_fixed_absolute_hex_shift
    lda fixed_address_lo_current
    ora fixed_address_digit_data
    sta fixed_address_lo_current
    inc fixed_address_digit_count
    lda fixed_address_digit_count
    cmp #$05
    bcc :+
    jmp parse_fixed_absolute_address_fail
:
    jsr overlay_source_consume_scan_ptr
    bcc :+
    jmp parse_fixed_absolute_address_fail
:
    jmp parse_fixed_absolute_hex_loop

parse_fixed_absolute_binary:
    jsr overlay_source_consume_scan_ptr
    bcc :+
    jmp parse_fixed_absolute_address_fail
:
parse_fixed_absolute_binary_loop:
    ldy #$00
    jsr overlay_source_peek_scan_y
    cmp #'0'
    beq parse_fixed_absolute_binary_digit
    cmp #'1'
    beq parse_fixed_absolute_binary_digit
    jmp parse_fixed_absolute_address_done
parse_fixed_absolute_binary_digit:
    pha
    jsr fixed_address_shift_left
    bcs parse_fixed_absolute_binary_pop_fail
    pla
    and #$01
    ora fixed_address_lo_current
    sta fixed_address_lo_current
    inc fixed_address_digit_count
    jsr overlay_source_consume_scan_ptr
    bcs parse_fixed_absolute_address_fail
    jmp parse_fixed_absolute_binary_loop
parse_fixed_absolute_binary_pop_fail:
    pla
    jmp parse_fixed_absolute_address_fail

parse_fixed_absolute_decimal_loop:
    ldy #$00
    jsr overlay_source_peek_scan_y
    cmp #'0'
    bcc parse_fixed_absolute_address_done
    cmp #'9'+1
    bcs parse_fixed_absolute_address_done
    sec
    sbc #'0'
    sta fixed_address_digit_data
    lda fixed_address_lo_current
    sta fixed_address_saved_lo
    lda fixed_address_hi_current
    sta fixed_address_saved_hi
    lda #$00
    sta fixed_address_lo_current
    sta fixed_address_hi_current
    lda #10
    sta fixed_address_mul_count
parse_fixed_absolute_decimal_mul_loop:
    clc
    lda fixed_address_lo_current
    adc fixed_address_saved_lo
    sta fixed_address_lo_current
    lda fixed_address_hi_current
    adc fixed_address_saved_hi
    bcs parse_fixed_absolute_address_fail
    sta fixed_address_hi_current
    dec fixed_address_mul_count
    bne parse_fixed_absolute_decimal_mul_loop
    clc
    lda fixed_address_lo_current
    adc fixed_address_digit_data
    sta fixed_address_lo_current
    lda fixed_address_hi_current
    adc #$00
    bcs parse_fixed_absolute_address_fail
    sta fixed_address_hi_current
    inc fixed_address_digit_count
    jsr overlay_source_consume_scan_ptr
    bcs parse_fixed_absolute_address_fail
    jmp parse_fixed_absolute_decimal_loop

parse_fixed_absolute_address_done:
    lda fixed_address_digit_count
    beq parse_fixed_absolute_address_fail
    clc
    rts
parse_fixed_absolute_address_fail:
    sec
    rts

fixed_address_shift_left:
    asl fixed_address_lo_current
    rol fixed_address_hi_current
    bcs fixed_address_shift_left_fail
    clc
    rts
fixed_address_shift_left_fail:
    sec
    rts

fixed_hex_digit_from_a:
    jsr uppercase_ascii
    cmp #'0'
    bcc fixed_hex_digit_from_a_fail
    cmp #'9'+1
    bcc fixed_hex_digit_from_a_decimal
    cmp #'A'
    bcc fixed_hex_digit_from_a_fail
    cmp #'F'+1
    bcs fixed_hex_digit_from_a_fail
    sec
    sbc #('A'-10)
    clc
    rts
fixed_hex_digit_from_a_decimal:
    sec
    sbc #'0'
    clc
    rts
fixed_hex_digit_from_a_fail:
    sec
    rts

fixed_param_bit_table:
    .byte $01,$02,$04,$08,$10,$20,$40,$80

validate_decl_tail:
    jsr skip_inline_spaces
    jsr overlay_source_match_line_end_from_scan_y
    bcc validate_decl_tail_ok
    lda #'='
    jsr overlay_source_match_expected_char
    bcc validate_decl_tail_initializer
    sec
    rts
validate_decl_tail_initializer:
    lda decl_width_current
    cmp #$02
    bne validate_decl_tail_fail
    lda #'='
    jsr overlay_source_consume_expected_char
    bcs validate_decl_tail_fail
    jsr skip_inline_spaces
    jsr validate_initializer_expr
    rts
validate_decl_tail_fail:
    sec
    rts
validate_decl_tail_ok:
    clc
    rts

validate_module_decl_tail:
    jsr skip_inline_spaces
    jsr overlay_source_match_line_end_from_scan_y
    bcc validate_module_decl_tail_ok
    lda #'='
    jsr overlay_source_match_expected_char
    bcc validate_module_decl_tail_initializer
    sec
    rts
validate_module_decl_tail_initializer:
    lda decl_width_current
    cmp #$02
    beq validate_module_decl_tail_initializer_word
    cmp #$04
    bne validate_module_decl_tail_fail
    lda decl_type_current
    cmp #'r'
    bne validate_module_decl_tail_fail
    lda #'='
    jsr overlay_source_consume_expected_char
    bcs validate_module_decl_tail_fail
    jsr skip_inline_spaces
    lda ACTC_OVERLAY_SCAN_ZP
    sta initializer_value_scan_ptr
    lda ACTC_OVERLAY_SCAN_ZP+1
    sta initializer_value_scan_ptr+1
    jsr validate_initializer_expr
    bcs validate_module_decl_tail_fail
    jsr require_real_zero_initializer_value
    bcs validate_module_decl_tail_fail
    jmp validate_module_decl_tail_ok
validate_module_decl_tail_initializer_word:
    lda #'='
    jsr overlay_source_consume_expected_char
    bcs validate_module_decl_tail_fail
    jsr skip_inline_spaces
    lda ACTC_OVERLAY_SCAN_ZP
    sta initializer_value_scan_ptr
    lda ACTC_OVERLAY_SCAN_ZP+1
    sta initializer_value_scan_ptr+1
    jsr validate_initializer_expr
    bcs validate_module_decl_tail_fail
    jsr try_store_simple_initializer_value
validate_module_decl_tail_ok:
    clc
    rts
validate_module_decl_tail_fail:
    sec
    rts

validate_initializer_expr:
    jsr overlay_source_match_line_end_from_scan_y
    bcs :+
    jmp validate_initializer_expr_fail
:
    jsr init_capture_reset
    lda #'['
    jsr overlay_source_match_expected_char
    bcc validate_bracket_initializer_expr
    jmp validate_line_initializer_expr

validate_bracket_initializer_expr:
    lda #'['
    jsr init_capture_char
    lda #'['
    jsr overlay_source_consume_expected_char
    bcc :+
    jmp validate_initializer_expr_fail
:
    jsr init_expr_state
validate_bracket_initializer_expr_loop:
    jsr overlay_source_match_line_end_from_scan_y
    bcs :+
    jmp validate_initializer_expr_fail
:
    lda #']'
    jsr overlay_source_match_expected_char
    bcc validate_bracket_initializer_expr_done
    jsr overlay_source_consume_initializer_body_char
    bcc :+
    jmp validate_initializer_expr_fail
:
    jmp validate_bracket_initializer_expr_loop
validate_bracket_initializer_expr_done:
    lda #']'
    jsr init_capture_char
    jsr init_capture_terminate
    jsr validate_initializer_expr_done
    bcc :+
    jmp validate_initializer_expr_fail
:
    lda #']'
    jsr overlay_source_consume_expected_char
    bcc :+
    jmp validate_initializer_expr_fail
:
    jsr require_line_end
    rts

validate_line_initializer_expr:
    jsr init_expr_state
validate_line_initializer_expr_loop:
    jsr overlay_source_match_line_end_from_scan_y
    bcc validate_line_initializer_expr_done
    lda #']'
    jsr overlay_source_match_expected_char
    bcs :+
    jmp validate_initializer_expr_fail
:
    jsr overlay_source_consume_initializer_body_char
    bcc :+
    jmp validate_initializer_expr_fail
:
    jmp validate_line_initializer_expr_loop
validate_line_initializer_expr_done:
    jsr init_capture_terminate
    jmp validate_initializer_expr_done

init_expr_state:
    lda #$00
    sta init_seen_token
    sta init_paren_depth
    sta init_last_char
    rts

overlay_symbol_body_char_valid:
    jsr uppercase_ascii
    jmp uppercase_symbol_body_valid

overlay_source_consume_initializer_body_char:
    ldy #$00
    jsr overlay_source_peek_scan_y
    jsr init_capture_char
    jsr validate_initializer_expr_char
    bcs overlay_source_consume_initializer_body_char_fail
    jsr overlay_source_consume_scan_ptr
    rts
overlay_source_consume_initializer_body_char_fail:
    sec
    rts

validate_initializer_expr_char:
    cmp #' '
    beq validate_initializer_expr_char_ok
    cmp #9
    beq validate_initializer_expr_char_ok
    sta init_last_char
    cmp #'('
    beq validate_initializer_expr_open_paren
    cmp #')'
    beq validate_initializer_expr_close_paren
    cmp #'['
    beq validate_initializer_expr_char_fail
    cmp #','
    beq validate_initializer_expr_char_fail
    cmp #'$'
    beq validate_initializer_expr_char_token
    jsr overlay_symbol_body_char_valid
    bcc validate_initializer_expr_char_token
    jsr validate_initializer_operator_char
    bcs validate_initializer_expr_char_fail
validate_initializer_expr_char_token:
    lda #$01
    sta init_seen_token
validate_initializer_expr_char_ok:
    clc
    rts
validate_initializer_expr_open_paren:
    inc init_paren_depth
    clc
    rts
validate_initializer_expr_close_paren:
    lda init_paren_depth
    beq validate_initializer_expr_char_fail
    dec init_paren_depth
    lda #$01
    sta init_seen_token
    clc
    rts
validate_initializer_expr_char_fail:
    sec
    rts

validate_initializer_operator_char:
    cmp #'+'
    beq validate_initializer_operator_char_ok
    cmp #'-'
    beq validate_initializer_operator_char_ok
    cmp #'*'
    beq validate_initializer_operator_char_ok
    cmp #'/'
    beq validate_initializer_operator_char_ok
    cmp #'<'
    beq validate_initializer_operator_char_ok
    cmp #'>'
    beq validate_initializer_operator_char_ok
    cmp #'='
    beq validate_initializer_operator_char_ok
    sec
    rts
validate_initializer_operator_char_ok:
    clc
    rts

validate_initializer_expr_done:
    lda init_seen_token
    beq validate_initializer_expr_fail
    lda init_paren_depth
    bne validate_initializer_expr_fail
    lda init_last_char
    cmp #'+'
    beq validate_initializer_expr_fail
    cmp #'-'
    beq validate_initializer_expr_fail
    cmp #'*'
    beq validate_initializer_expr_fail
    cmp #'/'
    beq validate_initializer_expr_fail
    cmp #'<'
    beq validate_initializer_expr_fail
    cmp #'>'
    beq validate_initializer_expr_fail
    cmp #'='
    beq validate_initializer_expr_fail
    cmp #'('
    beq validate_initializer_expr_fail
    clc
    rts
validate_initializer_expr_fail:
    sec
    rts

init_capture_reset:
    lda #<init_capture_buffer
    sta init_capture_write_ptr
    lda #>init_capture_buffer
    sta init_capture_write_ptr+1
    lda #<INIT_CAPTURE_LIMIT
    sta init_capture_remaining
    lda #>INIT_CAPTURE_LIMIT
    sta init_capture_remaining+1
    lda #$00
    sta init_capture_overflow
    rts

init_capture_char:
    sta init_capture_saved_char
    lda init_capture_remaining
    ora init_capture_remaining+1
    bne init_capture_char_store
    lda #$01
    sta init_capture_overflow
    lda init_capture_saved_char
    rts
init_capture_char_store:
    lda init_capture_write_ptr
    sta ACTC_OVERLAY_WORK_ZP
    lda init_capture_write_ptr+1
    sta ACTC_OVERLAY_WORK_ZP+1
    lda init_capture_saved_char
    ldy #$00
    sta (ACTC_OVERLAY_WORK_ZP),y
    inc init_capture_write_ptr
    bne :+
    inc init_capture_write_ptr+1
:
    lda init_capture_remaining
    bne :+
    dec init_capture_remaining+1
:
    dec init_capture_remaining
    lda init_capture_saved_char
    rts

init_capture_terminate:
    lda init_capture_write_ptr
    sta ACTC_OVERLAY_WORK_ZP
    lda init_capture_write_ptr+1
    sta ACTC_OVERLAY_WORK_ZP+1
    ldy #$00
    lda #$00
    sta (ACTC_OVERLAY_WORK_ZP),y
    rts

try_store_simple_initializer_value:
    lda init_capture_overflow
    bne try_store_simple_initializer_value_unsupported
    lda #<init_capture_buffer
    sta ACTC_OVERLAY_WORK_ZP
    lda #>init_capture_buffer
    sta ACTC_OVERLAY_WORK_ZP+1
    lda #$00
    sta init_parse_bracketed
    jsr init_value_skip_spaces_work
    jsr init_value_peek_char_work
    cmp #'['
    bne try_store_simple_initializer_value_first
    lda #$01
    sta init_parse_bracketed
    jsr init_value_advance_work
    jsr init_value_skip_spaces_work
try_store_simple_initializer_value_first:
    jsr init_value_try_parse_canonical_word_work
    bcc try_store_simple_initializer_word_tail
    jsr init_value_parse_bool_or_work
    bcs try_store_simple_initializer_value_unsupported
    jsr init_value_skip_spaces_work
    lda init_parse_bracketed
    beq try_store_simple_initializer_value_check_eol
    jsr init_value_peek_char_work
    cmp #']'
    bne try_store_simple_initializer_value_unsupported
    jsr init_value_advance_work
    jsr init_value_skip_spaces_work
try_store_simple_initializer_value_check_eol:
    jsr init_value_peek_char_work
    jsr init_value_is_line_end
    bcs try_store_simple_initializer_value_unsupported
    lda init_parse_value
    sta decl_init_lo_current
    lda #$00
    sta decl_init_hi_current
try_store_simple_initializer_value_unsupported:
    clc
    rts

try_store_simple_initializer_word_tail:
    jsr init_value_skip_spaces_work
    lda init_parse_bracketed
    beq try_store_simple_initializer_word_check_eol
    jsr init_value_peek_char_work
    cmp #']'
    bne try_store_simple_initializer_value_unsupported
    jsr init_value_advance_work
    jsr init_value_skip_spaces_work
try_store_simple_initializer_word_check_eol:
    jsr init_value_peek_char_work
    jsr init_value_is_line_end
    bcs try_store_simple_initializer_value_unsupported
    lda init_parse_value
    sta decl_init_lo_current
    lda init_parse_term
    sta decl_init_hi_current
    clc
    rts

; Typed CONST preprocessing emits $hhhh or -$hhhh. Parse that canonical form
; directly so word initializers retain both bytes; restore the input pointer
; when the expression uses the older general evaluator instead.
init_value_try_parse_canonical_word_work:
    jsr init_value_save_work_ptr
    lda #$00
    sta init_parse_left
    jsr init_value_peek_char_work
    cmp #'-'
    bne init_value_try_parse_canonical_word_dollar
    inc init_parse_left
    jsr init_value_advance_work
init_value_try_parse_canonical_word_dollar:
    jsr init_value_peek_char_work
    cmp #'$'
    bne init_value_try_parse_canonical_word_miss
    jsr init_value_advance_work
    lda #$00
    sta init_parse_value
    sta init_parse_term
    sta init_parse_saw_number
init_value_try_parse_canonical_word_loop:
    jsr init_value_peek_char_work
    jsr uppercase_ascii
    cmp #'0'
    bcc init_value_try_parse_canonical_word_done
    cmp #'9'+1
    bcc init_value_try_parse_canonical_word_decimal
    cmp #'A'
    bcc init_value_try_parse_canonical_word_done
    cmp #'F'+1
    bcs init_value_try_parse_canonical_word_done
    sec
    sbc #'A'-10
    bne init_value_try_parse_canonical_word_digit
init_value_try_parse_canonical_word_decimal:
    sec
    sbc #'0'
init_value_try_parse_canonical_word_digit:
    sta init_parse_digit
    ldx #$04
init_value_try_parse_canonical_word_shift:
    asl init_parse_value
    rol init_parse_term
    bcs init_value_try_parse_canonical_word_miss
    dex
    bne init_value_try_parse_canonical_word_shift
    lda init_parse_value
    clc
    adc init_parse_digit
    sta init_parse_value
    lda init_parse_term
    adc #$00
    sta init_parse_term
    bcs init_value_try_parse_canonical_word_miss
    inc init_parse_saw_number
    jsr init_value_advance_work
    jmp init_value_try_parse_canonical_word_loop
init_value_try_parse_canonical_word_done:
    lda init_parse_saw_number
    beq init_value_try_parse_canonical_word_miss
    lda init_parse_left
    beq init_value_try_parse_canonical_word_ok
    lda init_parse_value
    eor #$FF
    clc
    adc #$01
    sta init_parse_value
    lda init_parse_term
    eor #$FF
    adc #$00
    sta init_parse_term
init_value_try_parse_canonical_word_ok:
    clc
    rts
init_value_try_parse_canonical_word_miss:
    jsr init_value_restore_work_ptr
    sec
    rts

require_real_zero_initializer_value:
    lda init_capture_overflow
    bne require_real_zero_initializer_value_fail
    lda #<init_capture_buffer
    sta ACTC_OVERLAY_WORK_ZP
    lda #>init_capture_buffer
    sta ACTC_OVERLAY_WORK_ZP+1
    lda #$00
    sta init_parse_bracketed
    jsr init_value_skip_spaces_work
    jsr init_value_peek_char_work
    cmp #'['
    bne require_real_zero_initializer_value_first
    lda #$01
    sta init_parse_bracketed
    jsr init_value_advance_work
    jsr init_value_skip_spaces_work
require_real_zero_initializer_value_first:
    jsr init_value_parse_bool_or_work
    bcs require_real_zero_initializer_value_fail
    lda init_parse_value
    bne require_real_zero_initializer_value_fail
    jsr init_value_skip_spaces_work
    lda init_parse_bracketed
    beq require_real_zero_initializer_value_check_eol
    jsr init_value_peek_char_work
    cmp #']'
    bne require_real_zero_initializer_value_fail
    jsr init_value_advance_work
    jsr init_value_skip_spaces_work
require_real_zero_initializer_value_check_eol:
    jsr init_value_peek_char_work
    jsr init_value_is_line_end
    bcs require_real_zero_initializer_value_fail
    lda #$00
    sta decl_init_lo_current
    sta decl_init_hi_current
    clc
    rts
require_real_zero_initializer_value_fail:
    sec
    rts

init_value_parse_bool_or_work:
    jsr init_value_parse_bool_and_work
    bcs init_value_parse_bool_or_work_fail
init_value_parse_bool_or_work_loop:
    jsr init_value_consume_or_keyword_work
    bcs init_value_parse_bool_or_work_done
    jsr init_value_normalize_bool
    lda init_parse_value
    pha
    jsr init_value_parse_bool_and_work
    bcc :+
    pla
    jmp init_value_parse_bool_or_work_fail
:
    jsr init_value_normalize_bool
    lda init_parse_value
    sta init_parse_term
    pla
    ora init_parse_term
    beq init_value_parse_bool_or_work_store
    lda #$01
init_value_parse_bool_or_work_store:
    sta init_parse_value
    jmp init_value_parse_bool_or_work_loop
init_value_parse_bool_or_work_done:
    clc
    rts
init_value_parse_bool_or_work_fail:
    sec
    rts

init_value_parse_bool_and_work:
    jsr init_value_parse_bool_not_work
    bcs init_value_parse_bool_and_work_fail
init_value_parse_bool_and_work_loop:
    jsr init_value_consume_and_keyword_work
    bcs init_value_parse_bool_and_work_done
    jsr init_value_normalize_bool
    lda init_parse_value
    pha
    jsr init_value_parse_bool_not_work
    bcc :+
    pla
    jmp init_value_parse_bool_and_work_fail
:
    jsr init_value_normalize_bool
    lda init_parse_value
    sta init_parse_term
    pla
    and init_parse_term
    beq init_value_parse_bool_and_work_store
    lda #$01
init_value_parse_bool_and_work_store:
    sta init_parse_value
    jmp init_value_parse_bool_and_work_loop
init_value_parse_bool_and_work_done:
    clc
    rts
init_value_parse_bool_and_work_fail:
    sec
    rts

init_value_parse_bool_not_work:
    jsr init_value_consume_not_keyword_work
    bcs init_value_parse_condition_work
    jsr init_value_parse_bool_not_work
    bcs init_value_parse_bool_not_work_fail
    jsr init_value_normalize_bool
    lda init_parse_value
    eor #$01
    sta init_parse_value
    clc
    rts
init_value_parse_bool_not_work_fail:
    sec
    rts

init_value_parse_condition_work:
    jsr init_value_parse_expr_work
    bcc :+
    jmp init_value_parse_condition_work_fail
:
    lda init_parse_value
    pha
    jsr init_value_skip_spaces_work
    jsr init_value_peek_char_work
    cmp #'='
    beq init_value_parse_condition_work_eq
    cmp #'<'
    beq init_value_parse_condition_work_lt_entry
    cmp #'>'
    beq init_value_parse_condition_work_gt_entry
    pla
    sta init_parse_value
    clc
    rts
init_value_parse_condition_work_eq:
    jsr init_value_advance_work
    jsr init_value_parse_expr_work
    bcc :+
    jmp init_value_parse_condition_work_pop_fail
:
    pla
    cmp init_parse_value
    bne :+
    jmp init_value_parse_condition_work_true
:   
    jmp init_value_parse_condition_work_false
init_value_parse_condition_work_lt_entry:
    jsr init_value_advance_work
    jsr init_value_peek_char_work
    cmp #'='
    beq init_value_parse_condition_work_le
    cmp #'>'
    beq init_value_parse_condition_work_ne
    jsr init_value_parse_expr_work
    bcc :+
    jmp init_value_parse_condition_work_pop_fail
:
    pla
    cmp init_parse_value
    bcs :+
    jmp init_value_parse_condition_work_true
:   
    jmp init_value_parse_condition_work_false
init_value_parse_condition_work_gt_entry:
    jsr init_value_advance_work
    jsr init_value_peek_char_work
    cmp #'='
    beq init_value_parse_condition_work_ge
    jsr init_value_parse_expr_work
    bcc :+
    jmp init_value_parse_condition_work_pop_fail
:
    pla
    cmp init_parse_value
    bne :+
    jmp init_value_parse_condition_work_false
:   bcc :+
    jmp init_value_parse_condition_work_true
:   
    jmp init_value_parse_condition_work_false
init_value_parse_condition_work_le:
    jsr init_value_advance_work
    jsr init_value_parse_expr_work
    bcc :+
    jmp init_value_parse_condition_work_pop_fail
:
    pla
    cmp init_parse_value
    bcs :+
    jmp init_value_parse_condition_work_true
:   beq :+
    jmp init_value_parse_condition_work_false
:   jmp init_value_parse_condition_work_true
init_value_parse_condition_work_ge:
    jsr init_value_advance_work
    jsr init_value_parse_expr_work
    bcc :+
    jmp init_value_parse_condition_work_pop_fail
:
    pla
    cmp init_parse_value
    bcc :+
    jmp init_value_parse_condition_work_true
:   beq :+
    jmp init_value_parse_condition_work_false
:   jmp init_value_parse_condition_work_true
init_value_parse_condition_work_ne:
    jsr init_value_advance_work
    jsr init_value_parse_expr_work
    bcc :+
    jmp init_value_parse_condition_work_pop_fail
:
    pla
    cmp init_parse_value
    bne :+
    jmp init_value_parse_condition_work_false
:   
    jmp init_value_parse_condition_work_true
init_value_parse_condition_work_true:
    lda #$01
    sta init_parse_value
    clc
    rts
init_value_parse_condition_work_false:
    lda #$00
    sta init_parse_value
    clc
    rts
init_value_parse_condition_work_pop_fail:
    pla
init_value_parse_condition_work_fail:
    sec
    rts

init_value_normalize_bool:
    lda init_parse_value
    beq :+
    lda #$01
    sta init_parse_value
:
    clc
    rts

init_value_parse_expr_work:
    jsr init_value_parse_term_work
    bcs init_value_parse_expr_work_fail
init_value_parse_expr_work_loop:
    jsr init_value_skip_spaces_work
    jsr init_value_peek_char_work
    cmp #'+'
    beq init_value_parse_expr_work_add
    cmp #'-'
    beq init_value_parse_expr_work_sub
    clc
    rts
init_value_parse_expr_work_add:
    jsr init_value_advance_work
    lda init_parse_value
    pha
    jsr init_value_skip_spaces_work
    jsr init_value_parse_term_work
    bcc :+
    pla
    jmp init_value_parse_expr_work_fail
:
    lda init_parse_value
    sta init_parse_term
    pla
    clc
    adc init_parse_term
    bcs init_value_parse_expr_work_fail
    sta init_parse_value
    jmp init_value_parse_expr_work_loop
init_value_parse_expr_work_sub:
    jsr init_value_advance_work
    lda init_parse_value
    pha
    jsr init_value_skip_spaces_work
    jsr init_value_parse_term_work
    bcc :+
    pla
    jmp init_value_parse_expr_work_fail
:
    lda init_parse_value
    sta init_parse_term
    pla
    sec
    sbc init_parse_term
    bcc init_value_parse_expr_work_fail
    sta init_parse_value
    jmp init_value_parse_expr_work_loop
init_value_parse_expr_work_fail:
    sec
    rts

init_value_parse_term_work:
    jsr init_value_parse_factor_work
    bcs init_value_parse_term_work_fail
init_value_parse_term_work_loop:
    jsr init_value_skip_spaces_work
    jsr init_value_peek_char_work
    cmp #'*'
    beq init_value_parse_term_work_mul
    cmp #'/'
    beq init_value_parse_term_work_div
    clc
    rts
init_value_parse_term_work_mul:
    jsr init_value_advance_work
    lda init_parse_value
    pha
    jsr init_value_skip_spaces_work
    jsr init_value_parse_factor_work
    bcc :+
    pla
    jmp init_value_parse_term_work_fail
:
    lda init_parse_value
    sta init_parse_counter
    pla
    sta init_parse_left
    jsr init_value_multiply_left_counter
    bcs init_value_parse_term_work_fail
    jmp init_value_parse_term_work_loop
init_value_parse_term_work_div:
    jsr init_value_advance_work
    lda init_parse_value
    pha
    jsr init_value_skip_spaces_work
    jsr init_value_parse_factor_work
    bcc :+
    pla
    jmp init_value_parse_term_work_fail
:
    lda init_parse_value
    sta init_parse_counter
    pla
    sta init_parse_left
    jsr init_value_divide_left_counter
    bcs init_value_parse_term_work_fail
    jmp init_value_parse_term_work_loop
init_value_parse_term_work_fail:
    sec
    rts

init_value_parse_factor_work:
    jsr init_value_skip_spaces_work
    jsr init_value_peek_char_work
    cmp #'('
    beq init_value_parse_factor_work_group
    jsr init_value_parse_builtin_constant_work
    bcs :+
    lda init_parse_term
    sta init_parse_value
    clc
    rts
:
    jsr init_value_parse_number_work
    bcs init_value_parse_factor_work_fail
    lda init_parse_term
    sta init_parse_value
    clc
    rts
init_value_parse_factor_work_group:
    jsr init_value_advance_work
    jsr init_value_parse_bool_or_work
    bcs init_value_parse_factor_work_fail
    jsr init_value_skip_spaces_work
    jsr init_value_peek_char_work
    cmp #')'
    bne init_value_parse_factor_work_fail
    jsr init_value_advance_work
    clc
    rts
init_value_parse_factor_work_fail:
    sec
    rts

init_value_parse_builtin_constant_work:
    jsr init_value_save_work_ptr
    ldx #$00
init_value_parse_builtin_constant_work_loop:
    lda init_builtin_constant_table,x
    sta init_parse_tmp
    inx
    lda init_builtin_constant_table,x
    sta init_value_builtin_symbol_load+2
    ora init_parse_tmp
    beq init_value_parse_builtin_constant_work_fail_restore
    lda init_parse_tmp
    sta init_value_builtin_symbol_load+1
    inx
    lda init_builtin_constant_table,x
    sta init_parse_term
    inx
    stx init_const_table_index
    jsr init_value_restore_work_ptr
    jsr init_value_match_builtin_symbol_work
    bcc init_value_parse_builtin_constant_work_ok
    ldx init_const_table_index
    jmp init_value_parse_builtin_constant_work_loop
init_value_parse_builtin_constant_work_ok:
    clc
    rts
init_value_parse_builtin_constant_work_fail_restore:
    jsr init_value_restore_work_ptr
    sec
    rts

init_value_match_builtin_symbol_work:
    lda #$00
    sta init_symbol_index
init_value_match_builtin_symbol_work_loop:
    ldy init_symbol_index
init_value_builtin_symbol_load:
    lda $FFFF,y
    beq init_value_match_builtin_symbol_work_tail
    sta init_parse_tmp
    jsr init_value_peek_char_work
    jsr uppercase_ascii
    cmp init_parse_tmp
    bne init_value_match_builtin_symbol_work_fail
    jsr init_value_advance_work
    inc init_symbol_index
    bne init_value_match_builtin_symbol_work_loop
init_value_match_builtin_symbol_work_fail:
    sec
    rts
init_value_match_builtin_symbol_work_tail:
    jmp init_value_keyword_tail_ok

init_value_multiply_left_counter:
    lda #$00
    sta init_parse_tmp
init_value_multiply_left_counter_loop:
    lda init_parse_counter
    beq init_value_multiply_left_counter_done
    dec init_parse_counter
    lda init_parse_tmp
    clc
    adc init_parse_left
    bcs init_value_multiply_left_counter_fail
    sta init_parse_tmp
    jmp init_value_multiply_left_counter_loop
init_value_multiply_left_counter_done:
    lda init_parse_tmp
    sta init_parse_value
    clc
    rts
init_value_multiply_left_counter_fail:
    sec
    rts

init_value_divide_left_counter:
    lda init_parse_counter
    beq init_value_divide_left_counter_fail
    lda init_parse_left
    sta init_parse_tmp
    lda #$00
    sta init_parse_value
init_value_divide_left_counter_loop:
    lda init_parse_tmp
    cmp init_parse_counter
    bcc init_value_divide_left_counter_done
    sec
    sbc init_parse_counter
    sta init_parse_tmp
    inc init_parse_value
    jmp init_value_divide_left_counter_loop
init_value_divide_left_counter_done:
    clc
    rts
init_value_divide_left_counter_fail:
    sec
    rts

init_value_parse_number_work:
    lda #$00
    sta init_parse_term
    sta init_parse_saw_number
init_value_parse_number_work_loop:
    jsr init_value_peek_char_work
    cmp #'0'
    bcc init_value_parse_number_work_done
    cmp #'9'+1
    bcs init_value_parse_number_work_done
    sec
    sbc #'0'
    sta init_parse_digit
    lda init_parse_term
    asl a
    bcs init_value_parse_number_work_fail
    sta init_parse_tmp
    asl a
    bcs init_value_parse_number_work_fail
    asl a
    bcs init_value_parse_number_work_fail
    clc
    adc init_parse_tmp
    bcs init_value_parse_number_work_fail
    clc
    adc init_parse_digit
    bcs init_value_parse_number_work_fail
    sta init_parse_term
    lda #$01
    sta init_parse_saw_number
    jsr init_value_advance_work
    jmp init_value_parse_number_work_loop
init_value_parse_number_work_done:
    lda init_parse_saw_number
    beq init_value_parse_number_work_fail
    clc
    rts
init_value_parse_number_work_fail:
    sec
    rts

init_value_consume_or_keyword_work:
    jsr init_value_skip_spaces_work
    jsr init_value_save_work_ptr
    jsr init_value_peek_char_work
    jsr uppercase_ascii
    cmp #'O'
    bne init_value_consume_keyword_fail_restore
    jsr init_value_advance_work
    jsr init_value_peek_char_work
    jsr uppercase_ascii
    cmp #'R'
    bne init_value_consume_keyword_fail_restore
    jsr init_value_advance_work
    jsr init_value_keyword_tail_ok
    bcs init_value_consume_keyword_fail_restore
    clc
    rts

init_value_consume_and_keyword_work:
    jsr init_value_skip_spaces_work
    jsr init_value_save_work_ptr
    jsr init_value_peek_char_work
    jsr uppercase_ascii
    cmp #'A'
    bne init_value_consume_keyword_fail_restore
    jsr init_value_advance_work
    jsr init_value_peek_char_work
    jsr uppercase_ascii
    cmp #'N'
    bne init_value_consume_keyword_fail_restore
    jsr init_value_advance_work
    jsr init_value_peek_char_work
    jsr uppercase_ascii
    cmp #'D'
    bne init_value_consume_keyword_fail_restore
    jsr init_value_advance_work
    jsr init_value_keyword_tail_ok
    bcs init_value_consume_keyword_fail_restore
    clc
    rts

init_value_consume_not_keyword_work:
    jsr init_value_skip_spaces_work
    jsr init_value_save_work_ptr
    jsr init_value_peek_char_work
    jsr uppercase_ascii
    cmp #'N'
    bne init_value_consume_keyword_fail_restore
    jsr init_value_advance_work
    jsr init_value_peek_char_work
    jsr uppercase_ascii
    cmp #'O'
    bne init_value_consume_keyword_fail_restore
    jsr init_value_advance_work
    jsr init_value_peek_char_work
    jsr uppercase_ascii
    cmp #'T'
    bne init_value_consume_keyword_fail_restore
    jsr init_value_advance_work
    jsr init_value_keyword_tail_ok
    bcs init_value_consume_keyword_fail_restore
    clc
    rts

init_value_consume_keyword_fail_restore:
    jsr init_value_restore_work_ptr
    sec
    rts

init_value_keyword_tail_ok:
    jsr init_value_peek_char_work
    jsr overlay_symbol_body_char_valid
    bcc init_value_keyword_tail_bad
    clc
    rts
init_value_keyword_tail_bad:
    sec
    rts

init_value_peek_char_work:
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    rts

init_value_advance_work:
    inc ACTC_OVERLAY_WORK_ZP
    bne :+
    inc ACTC_OVERLAY_WORK_ZP+1
:
    rts

init_value_save_work_ptr:
    lda ACTC_OVERLAY_WORK_ZP
    sta saved_init_work_ptr
    lda ACTC_OVERLAY_WORK_ZP+1
    sta saved_init_work_ptr+1
    rts

init_value_restore_work_ptr:
    lda saved_init_work_ptr
    sta ACTC_OVERLAY_WORK_ZP
    lda saved_init_work_ptr+1
    sta ACTC_OVERLAY_WORK_ZP+1
    rts

init_value_skip_spaces_work:
    jsr init_value_peek_char_work
    cmp #' '
    beq init_value_skip_spaces_work_advance
    cmp #9
    beq init_value_skip_spaces_work_advance
    rts
init_value_skip_spaces_work_advance:
    jsr init_value_advance_work
    jmp init_value_skip_spaces_work

init_value_is_line_end:
    cmp #$00
    beq init_value_is_line_end_ok
    cmp #10
    beq init_value_is_line_end_ok
    cmp #13
    beq init_value_is_line_end_ok
    sec
    rts
init_value_is_line_end_ok:
    clc
    rts

clear_decl_init_current:
    lda #$00
    sta decl_init_lo_current
    sta decl_init_hi_current
    rts

require_line_end:
    jsr skip_inline_spaces
    jsr overlay_source_match_line_end_from_scan_y
    bcc require_line_end_ok
    sec
    rts
require_line_end_ok:
    clc
    rts

skip_inline_spaces:
skip_inline_spaces_loop:
    jsr overlay_source_consume_inline_space_char
    bcs skip_inline_spaces_done
    jmp skip_inline_spaces_loop
skip_inline_spaces_done:
    rts

overlay_source_match_line_end_from_scan_y:
    ldy #$00
    jsr overlay_source_peek_scan_y
    beq overlay_source_match_line_end_from_scan_y_ok
    cmp #10
    beq overlay_source_match_line_end_from_scan_y_ok
    cmp #13
    beq overlay_source_match_line_end_from_scan_y_ok
    sec
    rts
overlay_source_match_line_end_from_scan_y_ok:
    clc
    rts

overlay_source_match_expected_char:
    sta expected_char
    ldy #$00
    jsr overlay_source_peek_scan_y
    cmp expected_char
    beq overlay_source_match_expected_char_ok
    sec
    rts
overlay_source_match_expected_char_ok:
    clc
    rts

overlay_source_consume_expected_char:
    jsr overlay_source_match_expected_char
    bcs overlay_source_consume_expected_char_fail
    jsr overlay_source_consume_scan_ptr
    rts
overlay_source_consume_expected_char_fail:
    sec
    rts

overlay_source_consume_inline_space_char:
    ldy #$00
    jsr overlay_source_peek_scan_y
    cmp #' '
    beq overlay_source_consume_inline_space_char_consume
    cmp #9
    beq overlay_source_consume_inline_space_char_consume
    sec
    rts
overlay_source_consume_inline_space_char_consume:
    jsr overlay_source_consume_scan_ptr
    rts

overlay_source_consume_whitespace_char:
    ldy #$00
    jsr overlay_source_peek_scan_y
    cmp #' '
    beq overlay_source_consume_whitespace_char_consume
    cmp #9
    beq overlay_source_consume_whitespace_char_consume
    cmp #10
    beq overlay_source_consume_whitespace_char_consume
    cmp #13
    beq overlay_source_consume_whitespace_char_consume
    sec
    rts
overlay_source_consume_whitespace_char_consume:
    jsr overlay_source_consume_scan_ptr
    rts

overlay_source_consume_line_char:
    jsr ensure_source_window_available
    lda source_page_failed
    bne overlay_source_consume_line_char_done
    ldy #$00
    jsr overlay_source_peek_scan_y
    beq overlay_source_consume_line_char_done
    cmp #10
    beq overlay_source_consume_line_char_eol
    cmp #13
    beq overlay_source_consume_line_char_eol
    jsr overlay_source_consume_scan_ptr
    bcs overlay_source_consume_line_char_done
    clc
    rts
overlay_source_consume_line_char_eol:
    jsr overlay_source_consume_scan_ptr
    bcs overlay_source_consume_line_char_done
    jsr ensure_source_window_available
    lda source_page_failed
    bne overlay_source_consume_line_char_done
    ldy #$00
    jsr overlay_source_peek_scan_y
    cmp #10
    bne overlay_source_consume_line_char_done
    jsr overlay_source_consume_scan_ptr
overlay_source_consume_line_char_done:
    sec
    rts

clear_var_name_window:
    ldy #ACTC_OVERLAY_CTX_VAR_NAME_WINDOW_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    ldy #ACTC_OVERLAY_CTX_VAR_NAME_WINDOW_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP+1
    lda #$00
    ldy #24
clear_var_name_window_loop:
    sta (ACTC_OVERLAY_WORK_ZP),y
    dey
    bpl clear_var_name_window_loop
    rts

clear_export_name_window:
    ldy #ACTC_OVERLAY_CTX_EXPORT_NAME_WINDOW_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    ldy #ACTC_OVERLAY_CTX_EXPORT_NAME_WINDOW_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP+1
    lda #$00
    ldy #24
clear_export_name_window_loop:
    sta (ACTC_OVERLAY_WORK_ZP),y
    dey
    bpl clear_export_name_window_loop
    rts

overlay_symbol_token_char_valid_current:
    jsr uppercase_ascii
    ldy symbol_len_current
    bne overlay_symbol_token_char_valid_current_body
    jmp uppercase_symbol_start_valid
overlay_symbol_token_char_valid_current_body:
    jmp uppercase_symbol_body_valid

copy_symbol_to_var_name_window:
    jsr load_overlay_symbol_token_ptr
    lda #$00
    sta symbol_len_current
copy_symbol_to_var_name_window_loop:
    jsr overlay_source_consume_var_name_token_char
    bcs copy_symbol_to_var_name_window_fail
    beq copy_symbol_to_var_name_window_done
    lda symbol_len_current
    cmp #24
    bcc copy_symbol_to_var_name_window_loop
copy_symbol_to_var_name_window_done:
    lda symbol_len_current
    beq copy_symbol_to_var_name_window_fail
    tay
    lda #$00
    sta (ACTC_OVERLAY_WORK_ZP),y
    jsr publish_symbol_token_to_var_name_window
    clc
    rts
copy_symbol_to_var_name_window_fail:
    sec
    rts

copy_symbol_to_export_name_window:
    jsr load_overlay_symbol_token_ptr
    lda #$00
    sta symbol_len_current
copy_symbol_to_export_name_window_loop:
    jsr overlay_source_consume_export_name_token_char
    bcs copy_symbol_to_export_name_window_fail
    beq copy_symbol_to_export_name_window_done
    lda symbol_len_current
    cmp #24
    bcc copy_symbol_to_export_name_window_loop
copy_symbol_to_export_name_window_done:
    lda symbol_len_current
    beq copy_symbol_to_export_name_window_fail
    tay
    lda #$00
    sta (ACTC_OVERLAY_WORK_ZP),y
    jsr publish_symbol_token_to_export_name_window
    clc
    rts
copy_symbol_to_export_name_window_fail:
    sec
    rts

overlay_source_consume_var_name_token_char:
    ldy #$00
    jsr overlay_source_peek_scan_y
    beq overlay_source_consume_var_name_token_char_done
    cmp #' '
    beq overlay_source_consume_var_name_token_char_done
    cmp #9
    beq overlay_source_consume_var_name_token_char_done
    cmp #'='
    beq overlay_source_consume_var_name_token_char_done
    cmp #','
    beq overlay_source_consume_var_name_token_char_done
    cmp #'('
    beq overlay_source_consume_var_name_token_char_done
    cmp #')'
    beq overlay_source_consume_var_name_token_char_done
    cmp #10
    beq overlay_source_consume_var_name_token_char_done
    cmp #13
    beq overlay_source_consume_var_name_token_char_done
    jsr overlay_source_consume_symbol_token_body_char
    bcs overlay_source_consume_var_name_token_char_fail
    lda #$01
    clc
    rts
overlay_source_consume_var_name_token_char_done:
    lda #$00
    clc
    rts
overlay_source_consume_var_name_token_char_fail:
    sec
    rts

overlay_source_consume_export_name_token_char:
    ldy #$00
    jsr overlay_source_peek_scan_y
    beq overlay_source_consume_export_name_token_char_done
    cmp #' '
    beq overlay_source_consume_export_name_token_char_done
    cmp #9
    beq overlay_source_consume_export_name_token_char_done
    cmp #'('
    beq overlay_source_consume_export_name_token_char_done
    cmp #'='
    beq overlay_source_consume_export_name_token_char_done
    cmp #'+'
    beq overlay_source_consume_export_name_token_char_done
    cmp #10
    beq overlay_source_consume_export_name_token_char_done
    cmp #13
    beq overlay_source_consume_export_name_token_char_done
    jsr overlay_source_consume_symbol_token_body_char
    bcs overlay_source_consume_export_name_token_char_fail
    lda #$01
    clc
    rts
overlay_source_consume_export_name_token_char_done:
    lda #$00
    clc
    rts
overlay_source_consume_export_name_token_char_fail:
    sec
    rts

overlay_source_consume_symbol_token_body_char:
    jsr overlay_symbol_token_char_valid_current
    bcs overlay_source_consume_symbol_token_body_char_fail
    ldy symbol_len_current
    sta (ACTC_OVERLAY_WORK_ZP),y
    inc symbol_len_current
    jsr overlay_source_consume_scan_ptr
    rts
overlay_source_consume_symbol_token_body_char_fail:
    sec
    rts

write_var_meta_window:
    ldy #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    ldy #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP+1
    ldy #$00
    lda decl_init_lo_current
    sta (ACTC_OVERLAY_WORK_ZP),y
    iny
    lda decl_init_hi_current
    sta (ACTC_OVERLAY_WORK_ZP),y
    iny
    lda decl_width_current
    sta (ACTC_OVERLAY_WORK_ZP),y
    iny
    lda decl_type_current
    sta (ACTC_OVERLAY_WORK_ZP),y
    rts

write_proc_meta_window:
    ldy #ACTC_OVERLAY_CTX_PROC_META_WINDOW_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    ldy #ACTC_OVERLAY_CTX_PROC_META_WINDOW_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP+1
    ldy #$00
    lda proc_param_count_current
    ora proc_flags_current
    sta (ACTC_OVERLAY_WORK_ZP),y
    iny
    lda proc_param_base_current
    sta (ACTC_OVERLAY_WORK_ZP),y
    iny
    lda proc_local_count_current
    sta (ACTC_OVERLAY_WORK_ZP),y
    iny
    lda proc_local_base_current
    sta (ACTC_OVERLAY_WORK_ZP),y
    rts

write_proc_debug_offset_window:
    ldy #ACTC_OVERLAY_CTX_PROC_DEBUG_OFFSET_WINDOW_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    ldy #ACTC_OVERLAY_CTX_PROC_DEBUG_OFFSET_WINDOW_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP+1
    ldy #$00
    lda source_mark
    sta (ACTC_OVERLAY_WORK_ZP),y
    iny
    lda source_mark+1
    sta (ACTC_OVERLAY_WORK_ZP),y
    iny
    lda source_mark+2
    sta (ACTC_OVERLAY_WORK_ZP),y
    rts

write_var_debug_offset_window:
    jmp write_proc_debug_offset_window

ensure_var_capacity:
    lda var_total_count
    cmp #OVERLAY_VAR_MAX
    bcc ensure_capacity_ok
    sec
    rts

ensure_export_capacity:
    lda decl_proc_count
    cmp #OVERLAY_EXPORT_MAX
    bcc ensure_capacity_ok
    sec
    rts
ensure_capacity_ok:
    clc
    rts

find_module_var_name_cache_match:
    lda #$00
    sta cache_range_base
    lda decl_var_count
    sta cache_range_count
    jmp find_var_name_cache_match_range

find_current_param_name_cache_match:
    lda proc_param_base_current
    sta cache_range_base
    lda proc_param_count_current
    sta cache_range_count
    jmp find_var_name_cache_match_range

find_current_local_name_cache_match:
    lda proc_local_base_current
    sta cache_range_base
    lda proc_local_count_current
    sta cache_range_count
    jmp find_var_name_cache_match_range

find_var_name_cache_match_range:
    lda cache_range_count
    bne :+
    sec
    rts
:
    jsr save_source_scan_ptr
    lda cache_range_base
    sta cache_index
find_var_name_cache_match_range_loop:
    ldx cache_index
    jsr compare_var_name_window_to_cache_x
    bcc find_var_name_cache_match_range_found
    inc cache_index
    dec cache_range_count
    bne find_var_name_cache_match_range_loop
    jsr restore_source_scan_ptr
    sec
    rts
find_var_name_cache_match_range_found:
    jsr restore_source_scan_ptr
    clc
    rts

find_export_name_cache_match:
    lda decl_proc_count
    bne :+
    sec
    rts
:
    jsr save_source_scan_ptr
    lda #$00
    sta cache_index
find_export_name_cache_match_loop:
    ldx cache_index
    jsr compare_export_name_window_to_cache_x
    bcc find_export_name_cache_match_found
    inc cache_index
    lda cache_index
    cmp decl_proc_count
    bcc find_export_name_cache_match_loop
    jsr restore_source_scan_ptr
    sec
    rts
find_export_name_cache_match_found:
    jsr restore_source_scan_ptr
    clc
    rts

find_fixed_name_cache_match:
    lda fixed_decl_count
    bne :+
    sec
    rts
:
    jsr save_source_scan_ptr
    lda #$00
    sta cache_index
find_fixed_name_cache_match_loop:
    ldx cache_index
    jsr compare_fixed_name_window_to_cache_x
    bcc find_fixed_name_cache_match_found
    inc cache_index
    lda cache_index
    cmp fixed_decl_count
    bcc find_fixed_name_cache_match_loop
    jsr restore_source_scan_ptr
    sec
    rts
find_fixed_name_cache_match_found:
    jsr restore_source_scan_ptr
    clc
    rts

compare_var_name_window_to_cache_x:
    jsr setup_var_cache_ptr_x
    jsr load_var_name_window_ptr
    jmp compare_work_window_to_scan_cache

compare_export_name_window_to_cache_x:
    jsr setup_export_cache_ptr_x
    jsr load_export_name_window_ptr
    jmp compare_work_window_to_scan_cache

compare_fixed_name_window_to_cache_x:
    jsr setup_fixed_cache_ptr_x
    jsr load_export_name_window_ptr

compare_work_window_to_scan_cache:
    ldy #$00
compare_work_window_to_scan_cache_loop:
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp (ACTC_OVERLAY_CACHE_ZP),y
    bne compare_work_window_to_scan_cache_no
    cmp #$00
    beq compare_work_window_to_scan_cache_yes
    iny
    cpy #OVERLAY_NAME_STRIDE
    bcc compare_work_window_to_scan_cache_loop
compare_work_window_to_scan_cache_yes:
    clc
    rts
compare_work_window_to_scan_cache_no:
    sec
    rts

store_var_name_cache_x:
    stx cache_index
    jsr save_source_scan_ptr
    ldx cache_index
    jsr setup_var_cache_ptr_x
    jsr load_var_name_window_ptr
    jsr copy_work_window_to_scan_cache
    jsr restore_source_scan_ptr
    ldx cache_index
    rts

store_export_name_cache_x:
    stx cache_index
    jsr save_source_scan_ptr
    ldx cache_index
    jsr setup_export_cache_ptr_x
    jsr load_export_name_window_ptr
    jsr copy_work_window_to_scan_cache
    jsr restore_source_scan_ptr
    ldx cache_index
    rts

store_fixed_name_cache_x:
    stx cache_index
    jsr save_source_scan_ptr
    ldx cache_index
    jsr setup_fixed_cache_ptr_x
    jsr load_export_name_window_ptr
    jsr copy_work_window_to_scan_cache
    jsr restore_source_scan_ptr
    ldx cache_index
    rts

load_fixed_name_cache_x:
    stx cache_index
    jsr save_source_scan_ptr
    ldx cache_index
    jsr setup_fixed_cache_ptr_x
    jsr load_export_name_window_ptr
    jsr copy_scan_cache_to_work_window
    jsr restore_source_scan_ptr
    ldx cache_index
    rts

store_fixed_target_name_cache_x:
    stx cache_index
    jsr save_source_scan_ptr
    ldx cache_index
    jsr setup_fixed_target_cache_ptr_x
    jsr load_export_name_window_ptr
    jsr copy_work_window_to_scan_cache
    jsr restore_source_scan_ptr
    ldx cache_index
    rts

load_fixed_target_name_cache_x:
    stx cache_index
    jsr save_source_scan_ptr
    ldx cache_index
    jsr setup_fixed_target_cache_ptr_x
    jsr load_export_name_window_ptr
    jsr copy_scan_cache_to_work_window
    jsr restore_source_scan_ptr
    ldx cache_index
    rts

store_fixed_meta_cache_x:
    stx cache_index
    jsr save_source_scan_ptr
    ldx cache_index
    jsr setup_fixed_meta_cache_ptr_x
    jsr load_fixed_meta_window_ptr
    ldy #$00
store_fixed_meta_cache_x_loop:
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta (ACTC_OVERLAY_CACHE_ZP),y
    iny
    cpy #ACTC_FIXED_META_SIZE
    bcc store_fixed_meta_cache_x_loop
    jsr restore_source_scan_ptr
    ldx cache_index
    rts

load_fixed_meta_cache_x:
    stx cache_index
    jsr save_source_scan_ptr
    ldx cache_index
    jsr setup_fixed_meta_cache_ptr_x
    jsr load_fixed_meta_window_ptr
    ldy #$00
load_fixed_meta_cache_x_loop:
    lda (ACTC_OVERLAY_CACHE_ZP),y
    sta (ACTC_OVERLAY_WORK_ZP),y
    iny
    cpy #ACTC_FIXED_META_SIZE
    bcc load_fixed_meta_cache_x_loop
    jsr restore_source_scan_ptr
    ldx cache_index
    rts

copy_work_window_to_scan_cache:
    ldy #$00
copy_work_window_to_scan_cache_loop:
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta (ACTC_OVERLAY_CACHE_ZP),y
    iny
    cpy #OVERLAY_NAME_STRIDE
    bcc copy_work_window_to_scan_cache_loop
    rts

copy_scan_cache_to_work_window:
    ldy #$00
copy_scan_cache_to_work_window_loop:
    lda (ACTC_OVERLAY_CACHE_ZP),y
    sta (ACTC_OVERLAY_WORK_ZP),y
    iny
    cpy #OVERLAY_NAME_STRIDE
    bcc copy_scan_cache_to_work_window_loop
    rts

setup_var_cache_ptr_x:
    lda #<var_name_cache
    sta ACTC_OVERLAY_CACHE_ZP
    lda #>var_name_cache
    sta ACTC_OVERLAY_CACHE_ZP+1
    jmp setup_cache_ptr_x

setup_export_cache_ptr_x:
    lda #<export_name_cache
    sta ACTC_OVERLAY_CACHE_ZP
    lda #>export_name_cache
    sta ACTC_OVERLAY_CACHE_ZP+1
    jmp setup_cache_ptr_x

setup_fixed_cache_ptr_x:
    lda #<fixed_name_cache
    sta ACTC_OVERLAY_CACHE_ZP
    lda #>fixed_name_cache
    sta ACTC_OVERLAY_CACHE_ZP+1
    jmp setup_cache_ptr_x

setup_fixed_target_cache_ptr_x:
    lda #<fixed_target_name_cache
    sta ACTC_OVERLAY_CACHE_ZP
    lda #>fixed_target_name_cache
    sta ACTC_OVERLAY_CACHE_ZP+1
    jmp setup_cache_ptr_x

setup_fixed_meta_cache_ptr_x:
    lda #<fixed_meta_cache
    sta ACTC_OVERLAY_CACHE_ZP
    lda #>fixed_meta_cache
    sta ACTC_OVERLAY_CACHE_ZP+1
    txa
    beq setup_fixed_meta_cache_ptr_x_done
setup_fixed_meta_cache_ptr_x_loop:
    clc
    lda ACTC_OVERLAY_CACHE_ZP
    adc #ACTC_FIXED_META_SIZE
    sta ACTC_OVERLAY_CACHE_ZP
    bcc :+
    inc ACTC_OVERLAY_CACHE_ZP+1
:
    dex
    bne setup_fixed_meta_cache_ptr_x_loop
setup_fixed_meta_cache_ptr_x_done:
    rts

setup_cache_ptr_x:
    txa
    beq setup_cache_ptr_x_done
setup_cache_ptr_x_loop:
    clc
    lda ACTC_OVERLAY_CACHE_ZP
    adc #OVERLAY_NAME_STRIDE
    sta ACTC_OVERLAY_CACHE_ZP
    bcc :+
    inc ACTC_OVERLAY_CACHE_ZP+1
:
    dex
    bne setup_cache_ptr_x_loop
setup_cache_ptr_x_done:
    rts

load_var_name_window_ptr:
    ldy #ACTC_OVERLAY_CTX_VAR_NAME_WINDOW_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    ldy #ACTC_OVERLAY_CTX_VAR_NAME_WINDOW_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP+1
    rts

load_export_name_window_ptr:
    ldy #ACTC_OVERLAY_CTX_EXPORT_NAME_WINDOW_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    ldy #ACTC_OVERLAY_CTX_EXPORT_NAME_WINDOW_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP+1
    rts

load_fixed_meta_window_ptr:
    ldy #ACTC_OVERLAY_CTX_FIXED_META_WINDOW_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    ldy #ACTC_OVERLAY_CTX_FIXED_META_WINDOW_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP+1
    rts

load_overlay_symbol_token_ptr:
    lda #<overlay_symbol_token_buffer
    sta ACTC_OVERLAY_WORK_ZP
    lda #>overlay_symbol_token_buffer
    sta ACTC_OVERLAY_WORK_ZP+1
    rts

publish_symbol_token_to_var_name_window:
    jsr load_var_name_window_ptr
    jmp copy_overlay_symbol_token_to_work_window

publish_symbol_token_to_export_name_window:
    jsr load_export_name_window_ptr
    jmp copy_overlay_symbol_token_to_work_window

copy_overlay_symbol_token_to_work_window:
    ldy #$00
copy_overlay_symbol_token_to_work_window_loop:
    lda overlay_symbol_token_buffer,y
    sta (ACTC_OVERLAY_WORK_ZP),y
    beq copy_overlay_symbol_token_to_work_window_done
    iny
    cpy #OVERLAY_NAME_STRIDE
    bcc copy_overlay_symbol_token_to_work_window_loop
    lda #$00
    ldy #(OVERLAY_NAME_STRIDE - 1)
    sta (ACTC_OVERLAY_WORK_ZP),y
copy_overlay_symbol_token_to_work_window_done:
    rts

save_source_scan_ptr:
    lda ACTC_OVERLAY_SCAN_ZP
    sta saved_source_scan_ptr
    lda ACTC_OVERLAY_SCAN_ZP+1
    sta saved_source_scan_ptr+1
    rts

restore_source_scan_ptr:
    lda saved_source_scan_ptr
    sta ACTC_OVERLAY_SCAN_ZP
    lda saved_source_scan_ptr+1
    sta ACTC_OVERLAY_SCAN_ZP+1
    rts

call_store_var_name:
    ldy #ACTC_OVERLAY_CTX_STORE_VAR_NAME_FN_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target
    ldy #ACTC_OVERLAY_CTX_STORE_VAR_NAME_FN_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target+1
    jmp call_target_address

call_store_var_meta:
    ldy #ACTC_OVERLAY_CTX_STORE_VAR_META_FN_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target
    ldy #ACTC_OVERLAY_CTX_STORE_VAR_META_FN_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target+1
    jmp call_target_address

call_store_var_debug_offset:
    ldy #ACTC_OVERLAY_CTX_STORE_VAR_DEBUG_OFFSET_FN_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target
    ldy #ACTC_OVERLAY_CTX_STORE_VAR_DEBUG_OFFSET_FN_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target+1
    lda call_target
    ora call_target+1
    beq :+
    jmp call_target_address
:   rts

call_store_export_name:
    ldy #ACTC_OVERLAY_CTX_STORE_EXPORT_NAME_FN_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target
    ldy #ACTC_OVERLAY_CTX_STORE_EXPORT_NAME_FN_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target+1
    jmp call_target_address

call_store_proc_meta:
    ldy #ACTC_OVERLAY_CTX_STORE_PROC_META_FN_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target
    ldy #ACTC_OVERLAY_CTX_STORE_PROC_META_FN_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target+1
    jmp call_target_address

call_store_fixed_decl:
    ldy #ACTC_OVERLAY_CTX_STORE_FIXED_DECL_FN_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target
    ldy #ACTC_OVERLAY_CTX_STORE_FIXED_DECL_FN_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target+1
    jmp call_target_address

call_store_proc_debug_offset:
    ldy #ACTC_OVERLAY_CTX_STORE_PROC_DEBUG_OFFSET_FN_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target
    ldy #ACTC_OVERLAY_CTX_STORE_PROC_DEBUG_OFFSET_FN_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target+1
    jmp call_target_address

call_load_next_source_window:
    ldy #ACTC_OVERLAY_CTX_LOAD_NEXT_SOURCE_WINDOW_FN_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target
    ldy #ACTC_OVERLAY_CTX_LOAD_NEXT_SOURCE_WINDOW_FN_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target+1
    lda call_target
    ora call_target+1
    beq call_load_next_source_window_fail
    jsr call_target_address
    rts
call_load_next_source_window_fail:
    sec
    rts

call_target_address:
    sec
    lda call_target
    sbc #$01
    sta call_target_minus_one
    lda call_target+1
    sbc #$00
    pha
    lda call_target_minus_one
    pha
    rts

skip_source_whitespace:
skip_source_whitespace_loop:
    jsr overlay_source_consume_whitespace_char
    bcs skip_source_whitespace_done
    jmp skip_source_whitespace_loop
skip_source_whitespace_done:
    rts

skip_blank_lines_and_spaces:
skip_blank_lines_and_spaces_loop:
    jsr skip_source_whitespace
    ldy #$00
    jsr overlay_source_peek_scan_y
    cmp #';'
    bne skip_blank_lines_and_spaces_done
    jsr skip_source_line
    jmp skip_blank_lines_and_spaces_loop
skip_blank_lines_and_spaces_done:
    rts

skip_source_line:
skip_source_line_loop:
    jsr overlay_source_consume_line_char
    bcs skip_source_line_done
    jmp skip_source_line_loop
skip_source_line_done:
    rts

match_module_keyword:
    ldx #$00
match_module_keyword_loop:
    lda module_keyword,x
    bne :+
    jmp match_keyword_at_scan_delimiter
:
    jsr match_keyword_char
    bcc :+
    jmp match_keyword_at_scan_fail
:
    inx
    bne match_module_keyword_loop

match_proc_keyword:
    ldx #$00
match_proc_keyword_loop:
    lda proc_keyword,x
    bne :+
    jmp match_keyword_at_scan_delimiter
:
    jsr match_keyword_char
    bcc :+
    jmp match_keyword_at_scan_fail
:
    inx
    bne match_proc_keyword_loop

match_func_keyword:
    ldx #$00
match_func_keyword_loop:
    lda func_keyword,x
    bne :+
    jmp match_keyword_at_scan_delimiter
:
    jsr match_keyword_char
    bcc :+
    jmp match_keyword_at_scan_fail
:
    inx
    bne match_func_keyword_loop

match_return_keyword:
    ldx #$00
match_return_keyword_loop:
    lda return_keyword,x
    bne :+
    jsr overlay_source_match_keyword_delimiter
    bcc match_return_keyword_ok
    ldy #$00
    jsr overlay_source_peek_scan_y
    cmp #'('
    beq match_return_keyword_ok
    jmp match_keyword_at_scan_fail
:
    jsr match_keyword_char
    bcc :+
    jmp match_keyword_at_scan_fail
:
    inx
    bne match_return_keyword_loop
match_return_keyword_ok:
    clc
    rts

match_asmblock_keyword:
    ldx #$00
match_asmblock_keyword_loop:
    lda asmblock_keyword,x
    bne :+
    jmp match_keyword_at_scan_delimiter
:
    jsr match_keyword_char
    bcc :+
    jmp match_keyword_at_scan_fail
:
    inx
    bne match_asmblock_keyword_loop

match_scalar_decl_keyword:
    jsr match_int_keyword
    bcc match_scalar_decl_keyword_ok
    jsr match_byte_keyword
    bcc match_scalar_decl_keyword_ok
    jsr match_card_keyword
    bcc match_scalar_decl_keyword_ok
    jsr match_real_keyword
match_scalar_decl_keyword_ok:
    rts

match_scalar_decl_keyword_width2:
    lda #$02
    sta decl_width_current
    lda #'i'
    sta decl_type_current
    clc
    rts

match_scalar_decl_keyword_width4:
    lda #$04
    sta decl_width_current
    lda #'r'
    sta decl_type_current
    clc
    rts

match_int_keyword:
    ldx #$00
match_int_keyword_loop:
    lda int_keyword,x
    bne :+
    jmp match_keyword_at_scan_delimiter_width2
:
    jsr match_keyword_char
    bcc :+
    jmp match_keyword_at_scan_fail
:
    inx
    bne match_int_keyword_loop

match_byte_keyword:
    ldx #$00
match_byte_keyword_loop:
    lda byte_keyword,x
    bne :+
    jmp match_keyword_at_scan_delimiter_byte
:
    jsr match_keyword_char
    bcc :+
    jmp match_keyword_at_scan_fail
:
    inx
    bne match_byte_keyword_loop

match_card_keyword:
    ldx #$00
match_card_keyword_loop:
    lda card_keyword,x
    bne :+
    jmp match_keyword_at_scan_delimiter_card
:
    jsr match_keyword_char
    bcc :+
    jmp match_keyword_at_scan_fail
:
    inx
    bne match_card_keyword_loop

match_real_keyword:
    ldx #$00
match_real_keyword_loop:
    lda real_keyword,x
    bne :+
    jmp match_keyword_at_scan_delimiter_width4
:
    jsr match_keyword_char
    bcc :+
    jmp match_keyword_at_scan_fail
:
    inx
    bne match_real_keyword_loop

match_keyword_char:
    sta expected_char
    ldy #$00
    jsr overlay_source_peek_scan_y
    beq match_keyword_char_fail
    jsr uppercase_ascii
    cmp expected_char
    bne match_keyword_char_fail
    jsr overlay_source_consume_scan_ptr
    bcs match_keyword_char_fail
    clc
    rts
match_keyword_char_fail:
    sec
    rts

match_keyword_at_scan_delimiter_width2:
    jsr match_keyword_at_scan_delimiter
    bcs :+
    jmp match_scalar_decl_keyword_width2
:
    rts

match_keyword_at_scan_delimiter_byte:
    jsr match_keyword_at_scan_delimiter
    bcs :+
    lda #$02
    sta decl_width_current
    lda #'b'
    sta decl_type_current
    clc
    rts
:   rts

match_keyword_at_scan_delimiter_card:
    jsr match_keyword_at_scan_delimiter
    bcs :+
    lda #$02
    sta decl_width_current
    lda #'c'
    sta decl_type_current
    clc
    rts
:   rts

match_keyword_at_scan_delimiter_width4:
    jsr match_keyword_at_scan_delimiter
    bcs :+
    jmp match_scalar_decl_keyword_width4
:
    rts

match_keyword_at_scan_delimiter:
    jsr overlay_source_match_keyword_delimiter
    bcc match_keyword_at_scan_ok
match_keyword_at_scan_fail:
    jsr overlay_source_rewind_keyword_match
    sec
    rts
match_keyword_at_scan_ok:
    clc
    rts

overlay_source_match_keyword_delimiter:
    ldy #$00
    jsr overlay_source_peek_scan_y
    jmp overlay_source_keyword_delimiter_from_a

overlay_source_keyword_delimiter_from_a:
    beq overlay_source_keyword_delimiter_ok
    cmp #' '
    beq overlay_source_keyword_delimiter_ok
    cmp #9
    beq overlay_source_keyword_delimiter_ok
    cmp #10
    beq overlay_source_keyword_delimiter_ok
    cmp #13
    beq overlay_source_keyword_delimiter_ok
    sec
    rts
overlay_source_keyword_delimiter_ok:
    clc
    rts

overlay_source_rewind_keyword_match:
    txa
    beq overlay_source_rewind_keyword_match_done
overlay_source_rewind_keyword_match_loop:
    dec ACTC_OVERLAY_SCAN_ZP
    lda ACTC_OVERLAY_SCAN_ZP
    cmp #$FF
    bne :+
    dec ACTC_OVERLAY_SCAN_ZP+1
:
    dec source_mark
    lda source_mark
    cmp #$FF
    bne :+
    dec source_mark+1
    lda source_mark+1
    cmp #$FF
    bne :+
    dec source_mark+2
:
    inc source_window_remaining
    bne :+
    inc source_window_remaining+1
:
    dex
    bne overlay_source_rewind_keyword_match_loop
overlay_source_rewind_keyword_match_done:
    rts

uppercase_ascii:
    cmp #'a'
    bcc uppercase_ascii_done
    cmp #'z'+1
    bcs uppercase_ascii_done
    and #$DF
uppercase_ascii_done:
    rts

uppercase_symbol_start_valid:
    cmp #'A'
    bcc uppercase_symbol_start_valid_fail
    cmp #'Z'+1
    bcs uppercase_symbol_start_valid_fail
    clc
    rts
uppercase_symbol_start_valid_fail:
    sec
    rts

uppercase_symbol_body_valid:
    cmp #'A'
    bcc uppercase_symbol_body_valid_check_digit
    cmp #'Z'+1
    bcc uppercase_symbol_body_valid_ok
uppercase_symbol_body_valid_check_digit:
    cmp #'0'
    bcc uppercase_symbol_body_valid_check_underscore
    cmp #'9'+1
    bcc uppercase_symbol_body_valid_ok
uppercase_symbol_body_valid_check_underscore:
    cmp #'_'
    beq uppercase_symbol_body_valid_ok
    sec
    rts
uppercase_symbol_body_valid_ok:
    clc
    rts

load_source_window_remaining_from_context:
    ldy #ACTC_OVERLAY_CTX_SOURCE_WINDOW_LEN_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta source_window_remaining
    ldy #ACTC_OVERLAY_CTX_SOURCE_WINDOW_LEN_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta source_window_remaining+1
    rts

load_source_window_ptr_from_context:
    ldy #ACTC_OVERLAY_CTX_SOURCE_WINDOW_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP
    ldy #ACTC_OVERLAY_CTX_SOURCE_WINDOW_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP+1
    rts

source_mark_before_total:
    ldy #ACTC_OVERLAY_CTX_SOURCE_TOTAL_LEN_BANK
    lda source_mark+2
    cmp (ACTC_OVERLAY_CONTEXT_ZP),y
    bcc source_mark_before_total_yes
    bne source_mark_before_total_no
    ldy #ACTC_OVERLAY_CTX_SOURCE_TOTAL_LEN_HI
    lda source_mark+1
    cmp (ACTC_OVERLAY_CONTEXT_ZP),y
    bcc source_mark_before_total_yes
    bne source_mark_before_total_no
    ldy #ACTC_OVERLAY_CTX_SOURCE_TOTAL_LEN_LO
    lda source_mark
    cmp (ACTC_OVERLAY_CONTEXT_ZP),y
    bcc source_mark_before_total_yes
source_mark_before_total_no:
    clc
    rts
source_mark_before_total_yes:
    sec
    rts

ensure_source_window_available:
    lda source_window_remaining
    ora source_window_remaining+1
    bne ensure_source_window_available_done
    jsr source_mark_before_total
    bcs ensure_source_window_available_load_next
ensure_source_window_available_done:
    rts
ensure_source_window_available_load_next:
    jmp load_next_source_window_from_context

overlay_source_peek_scan_y:
    jsr ensure_source_window_available
    lda source_page_failed
    beq overlay_source_peek_scan_y_read
    lda #$00
    rts
overlay_source_peek_scan_y_read:
    lda (ACTC_OVERLAY_SCAN_ZP),y
    rts

overlay_source_consume_scan_ptr:
    jsr ensure_source_window_available
    lda source_page_failed
    bne overlay_source_consume_scan_ptr_fail
    jsr advance_source_scan
    lda source_page_failed
    bne overlay_source_consume_scan_ptr_fail
    clc
    rts
overlay_source_consume_scan_ptr_fail:
    sec
    rts

advance_source_window_remaining:
    lda source_window_remaining
    ora source_window_remaining+1
    beq advance_source_window_remaining_done
    lda source_window_remaining
    bne :+
    dec source_window_remaining+1
:
    dec source_window_remaining
    lda source_window_remaining
    ora source_window_remaining+1
    bne advance_source_window_remaining_done
    tya
    pha
    jsr source_mark_before_total
    bcs advance_source_window_load_next
    pla
    tay
    rts
advance_source_window_load_next:
    pla
    tay
    jmp load_next_source_window_from_context
advance_source_window_remaining_done:
    rts

load_next_source_window_from_context:
    pha
    txa
    pha
    tya
    pha
    jsr call_load_next_source_window
    bcc load_next_source_window_from_context_ok
    lda #$01
    sta source_page_failed
    jmp load_next_source_window_from_context_restore
load_next_source_window_from_context_ok:
    jsr load_source_window_ptr_from_context
    jsr load_source_window_remaining_from_context
load_next_source_window_from_context_restore:
    pla
    tay
    pla
    tax
    pla
    rts

advance_source_scan:
    inc ACTC_OVERLAY_SCAN_ZP
    bne :+
    inc ACTC_OVERLAY_SCAN_ZP+1
:
    inc source_mark
    bne :+
    inc source_mark+1
    bne :+
    inc source_mark+2
:
    jsr advance_source_window_remaining
    rts

module_keyword:
    .asciiz "MODULE"
proc_keyword:
    .asciiz "PROC"
func_keyword:
    .asciiz "FUNC"
return_keyword:
    .asciiz "RETURN"
asmblock_keyword:
    .asciiz "ASMBLOCK"
int_keyword:
    .asciiz "INT"
byte_keyword:
    .asciiz "BYTE"
card_keyword:
    .asciiz "CARD"
real_keyword:
    .asciiz "REAL"
init_builtin_constant_table:
    .byte <init_builtin_const_sid_tri, >init_builtin_const_sid_tri, $10
    .byte <init_builtin_const_sid_saw, >init_builtin_const_sid_saw, $20
    .byte <init_builtin_const_sid_pulse, >init_builtin_const_sid_pulse, $40
    .byte <init_builtin_const_sid_noise, >init_builtin_const_sid_noise, $80
    .byte <init_builtin_const_sid_low, >init_builtin_const_sid_low, $10
    .byte <init_builtin_const_sid_band, >init_builtin_const_sid_band, $20
    .byte <init_builtin_const_sid_high, >init_builtin_const_sid_high, $40
    .byte <init_builtin_const_spr_front, >init_builtin_const_spr_front, $00
    .byte <init_builtin_const_spr_back, >init_builtin_const_spr_back, $01
    .byte <init_builtin_const_joy_up, >init_builtin_const_joy_up, $01
    .byte <init_builtin_const_joy_down, >init_builtin_const_joy_down, $02
    .byte <init_builtin_const_joy_left, >init_builtin_const_joy_left, $04
    .byte <init_builtin_const_joy_right, >init_builtin_const_joy_right, $08
    .byte <init_builtin_const_joy_button1, >init_builtin_const_joy_button1, $10
    .byte <init_builtin_const_joy_button2, >init_builtin_const_joy_button2, $20
    .byte <init_builtin_const_mouse_button1, >init_builtin_const_mouse_button1, $01
    .byte <init_builtin_const_mouse_button2, >init_builtin_const_mouse_button2, $02
    .byte $00,$00,$00
init_builtin_const_sid_tri:
    .asciiz "SID_TRI"
init_builtin_const_sid_saw:
    .asciiz "SID_SAW"
init_builtin_const_sid_pulse:
    .asciiz "SID_PULSE"
init_builtin_const_sid_noise:
    .asciiz "SID_NOISE"
init_builtin_const_sid_low:
    .asciiz "SID_LOW"
init_builtin_const_sid_band:
    .asciiz "SID_BAND"
init_builtin_const_sid_high:
    .asciiz "SID_HIGH"
init_builtin_const_spr_front:
    .asciiz "SPR_FRONT"
init_builtin_const_spr_back:
    .asciiz "SPR_BACK"
init_builtin_const_joy_up:
    .asciiz "JOY_UP"
init_builtin_const_joy_down:
    .asciiz "JOY_DOWN"
init_builtin_const_joy_left:
    .asciiz "JOY_LEFT"
init_builtin_const_joy_right:
    .asciiz "JOY_RIGHT"
init_builtin_const_joy_button1:
    .asciiz "JOY_BUTTON1"
init_builtin_const_joy_button2:
    .asciiz "JOY_BUTTON2"
init_builtin_const_mouse_button1:
    .asciiz "MOUSE_BUTTON1"
init_builtin_const_mouse_button2:
    .asciiz "MOUSE_BUTTON2"
source_mark:
    .byte $00,$00,$00
source_window_remaining:
    .word $0000
source_page_failed:
    .byte $00
call_target:
    .word $0000
call_target_minus_one:
    .byte $00
expected_char:
    .byte $00
decl_var_count:
    .byte $00
var_total_count:
    .byte $00
decl_proc_count:
    .byte $00
fixed_decl_count:
    .byte $00
seen_proc:
    .byte $00
current_proc_index:
    .byte $00
decl_width_current:
    .byte $00
decl_type_current:
    .byte $00
decl_init_lo_current:
    .byte $00
decl_init_hi_current:
    .byte $00
proc_param_count_current:
    .byte $00
proc_flags_current:
    .byte $00
proc_param_base_current:
    .byte $00
proc_local_count_current:
    .byte $00
proc_local_base_current:
    .byte $00
proc_local_decl_grouped_current:
    .byte $00
routine_binding_current:
    .byte $00
fixed_param_count_current:
    .byte $00
fixed_word_mask_lo_current:
    .byte $00
fixed_word_mask_hi_current:
    .byte $00
fixed_byte_count_current:
    .byte $00
fixed_address_lo_current:
    .byte $00
fixed_address_hi_current:
    .byte $00
fixed_address_digit_count:
    .byte $00
fixed_address_digit_data:
    .byte $00
fixed_address_saved_lo:
    .byte $00
fixed_address_saved_hi:
    .byte $00
fixed_address_mul_count:
    .byte $00
fixed_addend_negative:
    .byte $00
fixed_resolve_index:
    .byte $00
symbol_len_current:
    .byte $00
advance_count:
    .byte $00
init_seen_token:
    .byte $00
init_paren_depth:
    .byte $00
init_last_char:
    .byte $00
initializer_value_scan_ptr:
    .word $0000
init_capture_write_ptr:
    .word $0000
init_capture_remaining:
    .word $0000
init_capture_overflow:
    .byte $00
init_capture_saved_char:
    .byte $00
init_parse_bracketed:
    .byte $00
init_parse_value:
    .byte $00
init_parse_term:
    .byte $00
init_parse_digit:
    .byte $00
init_parse_tmp:
    .byte $00
init_parse_saw_number:
    .byte $00
init_parse_left:
    .byte $00
init_parse_counter:
    .byte $00
init_const_table_index:
    .byte $00
init_symbol_index:
    .byte $00
cache_index:
    .byte $00
cache_range_base:
    .byte $00
cache_range_count:
    .byte $00
saved_source_scan_ptr:
    .word $0000
saved_init_work_ptr:
    .word $0000

actc_overlay_end:

.segment "BSS"

init_capture_buffer:
    .res INIT_CAPTURE_LIMIT + 1
overlay_symbol_token_buffer:
    .res OVERLAY_NAME_STRIDE
var_name_cache:
    .res OVERLAY_VAR_MAX * OVERLAY_NAME_STRIDE
export_name_cache:
    .res OVERLAY_EXPORT_MAX * OVERLAY_NAME_STRIDE
fixed_name_cache:
    .res OVERLAY_FIXED_MAX * OVERLAY_NAME_STRIDE
fixed_target_name_cache:
    .res OVERLAY_FIXED_MAX * OVERLAY_NAME_STRIDE
fixed_meta_cache:
    .res OVERLAY_FIXED_MAX * ACTC_FIXED_META_SIZE
