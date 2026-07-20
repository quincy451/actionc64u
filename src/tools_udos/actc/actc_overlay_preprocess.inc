; Bounded native source preprocessing for pass 1. The original staged source
; stays in REU bank 1 until the complete transformed stream has been written to
; bank 2. Only then is it copied back, so a failed directive never leaves ACTC
; with a partially rewritten source unit.

PREPROCESS_REU_PARAMS = ACTC_OVERLAY_REU_PARAMS_ZP
PREPROCESS_SOURCE_BANK = $01
PREPROCESS_OUTPUT_BANK = $02
PREPROCESS_DEFINE_NAME_SIZE = 25
PREPROCESS_DEFINE_VALUE_SIZE = 65
; Packed records preserve the original fixed-table footprint while avoiding a
; 90-byte reservation for every short definition.
PREPROCESS_DEFINE_STORE_SIZE = 15 * (PREPROCESS_DEFINE_NAME_SIZE + PREPROCESS_DEFINE_VALUE_SIZE)
PREPROCESS_DEFINE_RECORD_MAX = 255
PREPROCESS_EXPANSION_LIMIT = 16
PREPROCESS_INCLUDE_DEPTH_MAX = 7
PREPROCESS_INCLUDE_NAME_SIZE = 25
PREPROCESS_INCLUDE_BANK_BASE = $02
preprocess_name_slot_ptr = ACTC_OVERLAY_WORK_ZP
preprocess_value_slot_ptr = ACTC_OVERLAY_SCAN_ZP
preprocess_expand_src_ptr = PREPROCESS_REU_PARAMS+0
preprocess_expand_dst_ptr = PREPROCESS_REU_PARAMS+2

preprocess_source:
    lda #<preprocess_msg_failed
    ldy #>preprocess_msg_failed
    jsr preprocess_set_diag
    ldy #ACTC_OVERLAY_CTX_SOURCE_TOTAL_LEN_BANK
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    beq :+
    jmp preprocess_source_too_large
:
    lda #$00
    sta preprocess_input_offset
    sta preprocess_input_offset+1
    sta preprocess_input_window_remaining
    sta preprocess_input_window_remaining+1
    sta preprocess_input_window_index
    sta preprocess_input_pushback_valid
    sta preprocess_io_failed
    sta preprocess_input_depth
    sta preprocess_input_dir
    sta preprocess_output_total
    sta preprocess_output_total+1
    sta preprocess_output_flush_offset
    sta preprocess_output_flush_offset+1
    sta preprocess_output_count
    sta preprocess_define_count
    sta preprocess_define_used
    sta preprocess_define_used+1
    sta preprocess_define_continues
    sta preprocess_const_continues
    sta preprocess_set_right_seen
    sta preprocess_source_changed
    lda #PREPROCESS_SOURCE_BANK
    sta preprocess_input_bank
    ldy #ACTC_OVERLAY_CTX_SOURCE_TOTAL_LEN_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta preprocess_input_total
    ldy #ACTC_OVERLAY_CTX_SOURCE_TOTAL_LEN_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta preprocess_input_total+1
    jsr preprocess_init_main_include_name

preprocess_source_line_loop:
    jsr preprocess_read_line
    bcc :+
    rts
:
    cmp #$00
    bne preprocess_source_have_line
    lda preprocess_define_continues
    bne :+
    lda preprocess_const_continues
    bne :+
    jmp preprocess_source_finish
:
    jmp preprocess_bad_define

preprocess_source_have_line:
    lda preprocess_define_continues
    beq preprocess_source_check_define
    lda #$00
    sta preprocess_line_scan
    jsr preprocess_parse_define_items
    bcs preprocess_source_continuation_fail
    jsr preprocess_emit_blank_line
    bcs preprocess_source_continuation_fail
    bcc preprocess_source_line_loop

preprocess_source_check_const_continuation:
    jsr preprocess_prepare_expanded_line
    bcs preprocess_source_continuation_fail
    lda #$00
    sta preprocess_line_scan
    jsr preprocess_parse_const_items
    bcs preprocess_source_continuation_fail
    jsr preprocess_emit_blank_line
    bcs preprocess_source_continuation_fail
    bcc preprocess_source_line_loop

preprocess_source_continuation_fail:
    jmp preprocess_source_fail

preprocess_source_check_define:
    lda preprocess_const_continues
    bne preprocess_source_check_const_continuation
    lda #<preprocess_keyword_define
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>preprocess_keyword_define
    sta ACTC_OVERLAY_SCAN_ZP+1
    jsr preprocess_match_line_keyword
    bcs preprocess_source_check_set
    jsr preprocess_parse_define_items
    bcs preprocess_source_continuation_fail
    jsr preprocess_emit_blank_line
    bcs preprocess_source_continuation_fail
    jmp preprocess_source_line_loop

preprocess_source_check_set:
    lda #<preprocess_keyword_set
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>preprocess_keyword_set
    sta ACTC_OVERLAY_SCAN_ZP+1
    jsr preprocess_match_line_keyword
    bcs preprocess_source_check_include
    jsr preprocess_validate_set
    bcs preprocess_source_fail
    jsr preprocess_emit_blank_line
    bcs preprocess_source_fail
    jmp preprocess_source_line_loop

preprocess_source_check_include:
    lda #<preprocess_keyword_include
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>preprocess_keyword_include
    sta ACTC_OVERLAY_SCAN_ZP+1
    jsr preprocess_match_line_keyword
    bcs preprocess_source_expand_line
    jsr preprocess_parse_include
    bcs preprocess_source_fail
    jmp preprocess_source_line_loop

preprocess_source_expand_line:
    jsr preprocess_prepare_expanded_line
    bcs preprocess_source_fail
    jsr preprocess_match_typed_const
    bcc :+
    jsr preprocess_canonicalize_routine_address
    bcs preprocess_source_fail
    jmp preprocess_source_emit_expanded_line
:
    jsr preprocess_parse_const_items
    bcs preprocess_source_fail
    jsr preprocess_emit_blank_line
    bcs preprocess_source_fail
    jmp preprocess_source_line_loop
preprocess_source_emit_expanded_line:
    jsr preprocess_emit_expanded_line
    bcs preprocess_source_fail
    jmp preprocess_source_line_loop

preprocess_source_finish:
    lda preprocess_define_count
    ora preprocess_set_right_seen
    ora preprocess_source_changed
    beq preprocess_source_done
    jsr preprocess_flush_output_partial
    bcs preprocess_source_fail
    jsr preprocess_copy_output_to_source
    bcs preprocess_source_fail
    ldy #ACTC_OVERLAY_CTX_SOURCE_TOTAL_LEN_LO
    lda preprocess_output_total
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    ldy #ACTC_OVERLAY_CTX_SOURCE_TOTAL_LEN_HI
    lda preprocess_output_total+1
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    ldy #ACTC_OVERLAY_CTX_SOURCE_TOTAL_LEN_BANK
    lda #$00
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
preprocess_source_done:
    clc
    rts

preprocess_source_too_large:
    lda #<preprocess_msg_source_large
    ldy #>preprocess_msg_source_large
    jsr preprocess_set_diag
preprocess_source_fail:
    sec
    rts

preprocess_set_diag:
    sta preprocess_diag_ptr
    sty preprocess_diag_ptr+1
    rts

; Return A=1 for a physical line and A=0 at end of source. Carry is reserved
; for an actual read or line-capacity failure.
preprocess_read_line:
    lda #$00
    sta preprocess_line_len
preprocess_read_line_loop:
    jsr preprocess_get_input_byte
    bcc preprocess_read_line_have_byte
    lda preprocess_io_failed
    bne preprocess_read_line_fail
    lda preprocess_line_len
    bne preprocess_read_line_done
    lda preprocess_input_depth
    beq preprocess_read_line_eof
    lda preprocess_define_continues
    ora preprocess_const_continues
    beq :+
    jmp preprocess_bad_define
:
    jsr preprocess_pop_include
    bcs preprocess_read_line_fail
    jmp preprocess_read_line_loop
preprocess_read_line_eof:
    lda #$00
    clc
    rts

preprocess_read_line_have_byte:
    cmp #13
    beq preprocess_read_line_cr
    cmp #10
    beq preprocess_read_line_done
    ldx preprocess_line_len
    cpx #$FF
    bcs preprocess_read_line_too_long
    sta preprocess_line_a,x
    inc preprocess_line_len
    jmp preprocess_read_line_loop

preprocess_read_line_cr:
    jsr preprocess_get_input_byte
    bcs preprocess_read_line_cr_eof
    cmp #10
    beq preprocess_read_line_done
    sta preprocess_input_pushback_byte
    lda #$01
    sta preprocess_input_pushback_valid
    bne preprocess_read_line_done
preprocess_read_line_cr_eof:
    lda preprocess_io_failed
    bne preprocess_read_line_fail

preprocess_read_line_done:
    ldx preprocess_line_len
    lda #$00
    sta preprocess_line_a,x
    lda #$01
    clc
    rts

preprocess_read_line_too_long:
    lda #<preprocess_msg_line_long
    ldy #>preprocess_msg_line_long
    jsr preprocess_set_diag
preprocess_read_line_fail:
    sec
    rts

preprocess_get_input_byte:
    lda preprocess_input_pushback_valid
    beq preprocess_get_input_byte_window
    lda #$00
    sta preprocess_input_pushback_valid
    lda preprocess_input_pushback_byte
    clc
    rts

preprocess_get_input_byte_window:
    lda preprocess_input_window_remaining
    ora preprocess_input_window_remaining+1
    bne preprocess_get_input_byte_ready
    jsr preprocess_load_input_window
    bcc preprocess_get_input_byte_ready
    rts

preprocess_get_input_byte_ready:
    ldx preprocess_input_window_index
    lda preprocess_input_window,x
    pha
    inc preprocess_input_window_index
    lda preprocess_input_window_remaining
    bne :+
    dec preprocess_input_window_remaining+1
:
    dec preprocess_input_window_remaining
    inc preprocess_input_offset
    bne :+
    inc preprocess_input_offset+1
:
    pla
    clc
    rts

preprocess_load_input_window:
    sec
    lda preprocess_input_total
    sbc preprocess_input_offset
    sta preprocess_transfer_len
    lda preprocess_input_total+1
    sbc preprocess_input_offset+1
    sta preprocess_transfer_len+1
    ora preprocess_transfer_len
    bne preprocess_load_input_window_nonempty
    sec
    rts
preprocess_load_input_window_nonempty:
    lda preprocess_transfer_len+1
    beq preprocess_load_input_window_short
    lda #$00
    sta preprocess_transfer_len
    lda #$01
    sta preprocess_transfer_len+1
preprocess_load_input_window_short:
    lda #$00
    sta preprocess_input_window_index
    lda preprocess_transfer_len
    sta preprocess_input_window_remaining
    lda preprocess_transfer_len+1
    sta preprocess_input_window_remaining+1
    lda preprocess_input_offset
    sta PREPROCESS_REU_PARAMS+0
    lda preprocess_input_offset+1
    sta PREPROCESS_REU_PARAMS+1
    lda preprocess_input_bank
    sta PREPROCESS_REU_PARAMS+2
    lda #<preprocess_input_window
    sta PREPROCESS_REU_PARAMS+3
    lda #>preprocess_input_window
    sta PREPROCESS_REU_PARAMS+4
    lda preprocess_transfer_len
    sta PREPROCESS_REU_PARAMS+5
    lda preprocess_transfer_len+1
    sta PREPROCESS_REU_PARAMS+6
    lda #$00
    sta PREPROCESS_REU_PARAMS+7
    ldx #PREPROCESS_REU_PARAMS
    jsr svc_reu_read_sc0
    lda PREPROCESS_REU_PARAMS+7
    cmp #tool_file_status_ok
    beq preprocess_load_input_window_ok
    jmp preprocess_reu_fail
preprocess_load_input_window_ok:
    clc
    rts

preprocess_emit_blank_line:
    lda #13
    jmp preprocess_emit_byte

preprocess_emit_expanded_line:
    lda preprocess_expanded_ptr
    sta ACTC_OVERLAY_WORK_ZP
    lda preprocess_expanded_ptr+1
    sta ACTC_OVERLAY_WORK_ZP+1
    lda #$00
    sta preprocess_emit_index
preprocess_emit_expanded_line_loop:
    lda preprocess_emit_index
    cmp preprocess_expanded_len
    bcs preprocess_emit_blank_line
    tay
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr preprocess_emit_byte
    bcs preprocess_emit_expanded_line_fail
    inc preprocess_emit_index
    jmp preprocess_emit_expanded_line_loop
preprocess_emit_expanded_line_fail:
    rts

preprocess_emit_byte:
    pha
    inc preprocess_output_total
    bne preprocess_emit_byte_total_ok
    inc preprocess_output_total+1
    bne preprocess_emit_byte_total_ok
    pla
    lda #<preprocess_msg_source_large
    ldy #>preprocess_msg_source_large
    jsr preprocess_set_diag
    sec
    rts
preprocess_emit_byte_total_ok:
    ldx preprocess_output_count
    pla
    sta preprocess_output_window,x
    inc preprocess_output_count
    bne preprocess_emit_byte_ok
    jsr preprocess_flush_output_full
    rts
preprocess_emit_byte_ok:
    clc
    rts

preprocess_flush_output_full:
    lda #$00
    sta preprocess_transfer_len
    lda #$01
    sta preprocess_transfer_len+1
    jsr preprocess_write_output_window
    bcs preprocess_flush_output_full_fail
    inc preprocess_output_flush_offset+1
    clc
preprocess_flush_output_full_fail:
    rts

preprocess_flush_output_partial:
    lda preprocess_output_count
    beq preprocess_flush_output_partial_done
    sta preprocess_transfer_len
    lda #$00
    sta preprocess_transfer_len+1
    jsr preprocess_write_output_window
    bcs preprocess_flush_output_partial_fail
    clc
    lda preprocess_output_flush_offset
    adc preprocess_output_count
    sta preprocess_output_flush_offset
    lda preprocess_output_flush_offset+1
    adc #$00
    sta preprocess_output_flush_offset+1
    lda #$00
    sta preprocess_output_count
preprocess_flush_output_partial_done:
    clc
preprocess_flush_output_partial_fail:
    rts

preprocess_write_output_window:
    lda preprocess_output_flush_offset
    sta PREPROCESS_REU_PARAMS+0
    lda preprocess_output_flush_offset+1
    sta PREPROCESS_REU_PARAMS+1
    lda #PREPROCESS_OUTPUT_BANK
    sta PREPROCESS_REU_PARAMS+2
    lda #<preprocess_output_window
    sta PREPROCESS_REU_PARAMS+3
    lda #>preprocess_output_window
    sta PREPROCESS_REU_PARAMS+4
    lda preprocess_transfer_len
    sta PREPROCESS_REU_PARAMS+5
    lda preprocess_transfer_len+1
    sta PREPROCESS_REU_PARAMS+6
    lda #$00
    sta PREPROCESS_REU_PARAMS+7
    ldx #PREPROCESS_REU_PARAMS
    jsr svc_reu_write_sc0
    lda PREPROCESS_REU_PARAMS+7
    cmp #tool_file_status_ok
    beq preprocess_write_output_window_ok
    jmp preprocess_reu_fail
preprocess_write_output_window_ok:
    clc
    rts

preprocess_copy_output_to_source:
    lda #$00
    sta preprocess_copy_offset
    sta preprocess_copy_offset+1
preprocess_copy_output_loop:
    lda preprocess_copy_offset+1
    cmp preprocess_output_total+1
    bcc preprocess_copy_output_chunk
    bne preprocess_copy_output_done
    lda preprocess_copy_offset
    cmp preprocess_output_total
    bcs preprocess_copy_output_done
preprocess_copy_output_chunk:
    sec
    lda preprocess_output_total
    sbc preprocess_copy_offset
    sta preprocess_transfer_len
    lda preprocess_output_total+1
    sbc preprocess_copy_offset+1
    sta preprocess_transfer_len+1
    beq preprocess_copy_output_short
    lda #$00
    sta preprocess_transfer_len
    lda #$01
    sta preprocess_transfer_len+1
preprocess_copy_output_short:
    lda preprocess_copy_offset
    sta PREPROCESS_REU_PARAMS+0
    lda preprocess_copy_offset+1
    sta PREPROCESS_REU_PARAMS+1
    lda #PREPROCESS_OUTPUT_BANK
    sta PREPROCESS_REU_PARAMS+2
    lda #<preprocess_input_window
    sta PREPROCESS_REU_PARAMS+3
    lda #>preprocess_input_window
    sta PREPROCESS_REU_PARAMS+4
    lda preprocess_transfer_len
    sta PREPROCESS_REU_PARAMS+5
    lda preprocess_transfer_len+1
    sta PREPROCESS_REU_PARAMS+6
    lda #$00
    sta PREPROCESS_REU_PARAMS+7
    ldx #PREPROCESS_REU_PARAMS
    jsr svc_reu_read_sc0
    lda PREPROCESS_REU_PARAMS+7
    cmp #tool_file_status_ok
    bne preprocess_reu_fail
    lda #PREPROCESS_SOURCE_BANK
    sta PREPROCESS_REU_PARAMS+2
    lda #$00
    sta PREPROCESS_REU_PARAMS+7
    ldx #PREPROCESS_REU_PARAMS
    jsr svc_reu_write_sc0
    lda PREPROCESS_REU_PARAMS+7
    cmp #tool_file_status_ok
    bne preprocess_reu_fail
    clc
    lda preprocess_copy_offset
    adc preprocess_transfer_len
    sta preprocess_copy_offset
    lda preprocess_copy_offset+1
    adc preprocess_transfer_len+1
    sta preprocess_copy_offset+1
    jmp preprocess_copy_output_loop
preprocess_copy_output_done:
    clc
    rts

preprocess_reu_fail:
    lda #$01
    sta preprocess_io_failed
    lda #<preprocess_msg_reu
    ldy #>preprocess_msg_reu
    jsr preprocess_set_diag
    sec
    rts

preprocess_match_line_keyword:
    lda #$00
    sta preprocess_line_scan
    jsr preprocess_line_skip_spaces
    ldx #$00
preprocess_match_line_keyword_loop:
    txa
    tay
    lda (ACTC_OVERLAY_SCAN_ZP),y
    beq preprocess_match_line_keyword_tail
    sta preprocess_expected_char
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    jsr uppercase_ascii
    cmp preprocess_expected_char
    bne preprocess_match_line_keyword_fail
    inc preprocess_line_scan
    inx
    bne preprocess_match_line_keyword_loop
preprocess_match_line_keyword_tail:
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    beq preprocess_match_line_keyword_ok
    cmp #' '
    beq preprocess_match_line_keyword_ok
    cmp #9
    beq preprocess_match_line_keyword_ok
preprocess_match_line_keyword_fail:
    sec
    rts
preprocess_match_line_keyword_ok:
    clc
    rts

preprocess_line_skip_spaces:
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    cmp #' '
    beq preprocess_line_skip_spaces_one
    cmp #9
    bne preprocess_line_skip_spaces_done
preprocess_line_skip_spaces_one:
    inc preprocess_line_scan
    bne preprocess_line_skip_spaces
preprocess_line_skip_spaces_done:
    rts

preprocess_parse_define_items:
    lda #$00
    sta preprocess_define_continues
preprocess_parse_define_items_loop:
    jsr preprocess_line_skip_spaces
    jsr preprocess_parse_define_name
    bcs preprocess_bad_define
    jsr preprocess_line_skip_spaces
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    cmp #'='
    bne preprocess_bad_define
    inc preprocess_line_scan
    jsr preprocess_line_skip_spaces
    jsr preprocess_parse_define_value
    bcs preprocess_bad_define
    jsr preprocess_store_define
    bcs preprocess_parse_define_items_fail
    jsr preprocess_line_skip_spaces
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    beq preprocess_parse_define_items_done
    cmp #';'
    beq preprocess_parse_define_items_done
    cmp #','
    bne preprocess_bad_define
    inc preprocess_line_scan
    jsr preprocess_line_skip_spaces
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    beq preprocess_parse_define_items_continues
    cmp #';'
    beq preprocess_parse_define_items_continues
    jmp preprocess_parse_define_items_loop
preprocess_parse_define_items_continues:
    lda #$01
    sta preprocess_define_continues
preprocess_parse_define_items_done:
    clc
    rts
preprocess_parse_define_items_fail:
    rts

preprocess_bad_define:
    lda #<preprocess_msg_bad_define
    ldy #>preprocess_msg_bad_define
    jsr preprocess_set_diag
    sec
    rts

preprocess_parse_define_name:
    ldx #$00
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    jsr uppercase_ascii
    jsr uppercase_symbol_start_valid
    bcs preprocess_parse_define_name_fail
preprocess_parse_define_name_loop:
    cpx #24
    bcs preprocess_parse_define_name_fail
    sta preprocess_name_temp,x
    inx
    inc preprocess_line_scan
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    jsr uppercase_ascii
    jsr uppercase_symbol_body_valid
    bcc preprocess_parse_define_name_loop
    lda #$00
    sta preprocess_name_temp,x
    clc
    rts
preprocess_parse_define_name_fail:
    sec
    rts

preprocess_parse_define_value:
    lda #$00
    sta preprocess_value_len
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    cmp #'"'
    beq preprocess_parse_define_quoted_value
preprocess_parse_define_unquoted_value_loop:
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    beq preprocess_parse_define_unquoted_value_done
    cmp #';'
    beq preprocess_parse_define_unquoted_value_done
    cmp #','
    beq preprocess_parse_define_unquoted_value_done
    cmp #'"'
    beq preprocess_parse_define_value_fail
    jsr preprocess_append_value_char
    bcs preprocess_parse_define_value_fail
    inc preprocess_line_scan
    jmp preprocess_parse_define_unquoted_value_loop
preprocess_parse_define_unquoted_value_done:
    jsr preprocess_trim_value_spaces
    lda preprocess_value_len
    beq preprocess_parse_define_value_fail
    tax
    lda #$00
    sta preprocess_value_temp,x
    clc
    rts

preprocess_parse_define_quoted_value:
    inc preprocess_line_scan
preprocess_parse_define_quoted_value_loop:
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    beq preprocess_parse_define_value_fail
    cmp #'"'
    beq preprocess_parse_define_quoted_value_done
    cmp #$5C
    bne preprocess_parse_define_quoted_value_store
    inc preprocess_line_scan
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    beq preprocess_parse_define_value_fail
    cmp #$5C
    beq preprocess_parse_define_quoted_value_store
    cmp #'"'
    bne preprocess_parse_define_value_fail
preprocess_parse_define_quoted_value_store:
    jsr preprocess_append_value_char
    bcs preprocess_parse_define_value_fail
    inc preprocess_line_scan
    jmp preprocess_parse_define_quoted_value_loop
preprocess_parse_define_quoted_value_done:
    inc preprocess_line_scan
    ldx preprocess_value_len
    lda #$00
    sta preprocess_value_temp,x
    lda preprocess_value_len
    beq preprocess_parse_define_value_fail
    clc
    rts
preprocess_parse_define_value_fail:
    sec
    rts

preprocess_append_value_char:
    ldx preprocess_value_len
    cpx #64
    bcs preprocess_append_value_char_fail
    sta preprocess_value_temp,x
    inc preprocess_value_len
    clc
    rts
preprocess_append_value_char_fail:
    sec
    rts

preprocess_trim_value_spaces:
    ldx preprocess_value_len
preprocess_trim_value_spaces_loop:
    cpx #$00
    beq preprocess_trim_value_spaces_done
    dex
    lda preprocess_value_temp,x
    cmp #' '
    beq preprocess_trim_value_spaces_remove
    cmp #9
    bne preprocess_trim_value_spaces_done_restore
preprocess_trim_value_spaces_remove:
    stx preprocess_value_len
    jmp preprocess_trim_value_spaces_loop
preprocess_trim_value_spaces_done_restore:
    inx
preprocess_trim_value_spaces_done:
    rts

preprocess_store_define:
    jsr preprocess_find_define
    bcs preprocess_store_define_new
    ldy #$02
    lda (preprocess_name_slot_ptr),y
    cmp preprocess_value_len
    bcc :+
    jmp preprocess_store_define_replace
:
    ; A larger replacement supersedes this record. Keeping its allocation makes
    ; the update atomic and avoids moving every later record in 6502 memory.
    ldy #$01
    lda #$00
    sta (preprocess_name_slot_ptr),y
preprocess_store_define_new:
    lda preprocess_define_count
    cmp #PREPROCESS_DEFINE_RECORD_MAX
    bne :+
preprocess_store_define_limit:
    lda #<preprocess_msg_define_limit
    ldy #>preprocess_msg_define_limit
    jsr preprocess_set_diag
    sec
    rts
:
    ldx #$00
preprocess_store_define_measure_name:
    lda preprocess_name_temp,x
    beq preprocess_store_define_name_measured
    inx
    cpx #PREPROCESS_DEFINE_NAME_SIZE
    bcc preprocess_store_define_measure_name
    jmp preprocess_store_define_limit
preprocess_store_define_name_measured:
    stx preprocess_define_name_len
    txa
    clc
    adc preprocess_value_len
    adc #$04
    sta preprocess_define_record_size
    clc
    lda preprocess_define_used
    adc preprocess_define_record_size
    sta preprocess_define_new_used
    lda preprocess_define_used+1
    adc #$00
    sta preprocess_define_new_used+1
    cmp #>PREPROCESS_DEFINE_STORE_SIZE
    bcc preprocess_store_define_capacity_ok
    bne preprocess_store_define_limit
    lda preprocess_define_new_used
    cmp #(<PREPROCESS_DEFINE_STORE_SIZE + 1)
    bcs preprocess_store_define_limit
preprocess_store_define_capacity_ok:
    clc
    lda #<preprocess_define_store
    adc preprocess_define_used
    sta preprocess_name_slot_ptr
    lda #>preprocess_define_store
    adc preprocess_define_used+1
    sta preprocess_name_slot_ptr+1
    ldy #$00
    lda preprocess_define_record_size
    sta (preprocess_name_slot_ptr),y
    iny
    lda preprocess_define_name_len
    sta (preprocess_name_slot_ptr),y
    iny
    lda preprocess_value_len
    sta (preprocess_name_slot_ptr),y
    ldx #$00
    ldy #$03
preprocess_store_define_name_loop:
    cpx preprocess_define_name_len
    bcs preprocess_store_define_name_done
    lda preprocess_name_temp,x
    sta (preprocess_name_slot_ptr),y
    inx
    iny
    bne preprocess_store_define_name_loop
preprocess_store_define_name_done:
    tya
    clc
    adc preprocess_name_slot_ptr
    sta preprocess_value_slot_ptr
    lda preprocess_name_slot_ptr+1
    adc #$00
    sta preprocess_value_slot_ptr+1
    inc preprocess_define_count
    lda preprocess_define_new_used
    sta preprocess_define_used
    lda preprocess_define_new_used+1
    sta preprocess_define_used+1
preprocess_store_define_replace:
    ldy #$00
preprocess_store_define_value_loop:
    lda preprocess_value_temp,y
    sta (preprocess_value_slot_ptr),y
    beq preprocess_store_define_done
    iny
    cpy #PREPROCESS_DEFINE_VALUE_SIZE
    bcc preprocess_store_define_value_loop
preprocess_store_define_done:
    clc
    rts

; Find preprocess_name_temp. Carry clear returns the packed record header in
; preprocess_name_slot_ptr and its current value in preprocess_value_slot_ptr.
preprocess_find_define:
    lda #$00
    sta preprocess_define_scan_count
    lda #<preprocess_define_store
    sta preprocess_name_slot_ptr
    lda #>preprocess_define_store
    sta preprocess_name_slot_ptr+1
preprocess_find_define_loop:
    lda preprocess_define_scan_count
    cmp preprocess_define_count
    bcs preprocess_find_define_fail
    ldy #$01
    lda (preprocess_name_slot_ptr),y
    beq preprocess_find_define_next
    sta preprocess_define_name_len
    ldx #$00
    ldy #$03
preprocess_find_define_compare:
    ; Y addresses the packed record while X addresses the temporary name.
    lda (preprocess_name_slot_ptr),y
    cmp preprocess_name_temp,x
    bne preprocess_find_define_next
    inx
    iny
    cpx preprocess_define_name_len
    bcc preprocess_find_define_compare
    lda preprocess_name_temp,x
    bne preprocess_find_define_next
    tya
    clc
    adc preprocess_name_slot_ptr
    sta preprocess_value_slot_ptr
    lda preprocess_name_slot_ptr+1
    adc #$00
    sta preprocess_value_slot_ptr+1
    clc
    rts
preprocess_find_define_next:
    ldy #$00
    lda (preprocess_name_slot_ptr),y
    beq preprocess_find_define_fail
    clc
    adc preprocess_name_slot_ptr
    sta preprocess_name_slot_ptr
    lda preprocess_name_slot_ptr+1
    adc #$00
    sta preprocess_name_slot_ptr+1
    inc preprocess_define_scan_count
    jmp preprocess_find_define_loop
preprocess_find_define_fail:
    sec
    rts

preprocess_validate_set:
    jsr preprocess_line_skip_spaces
    lda #$00
    sta preprocess_set_left_seen
preprocess_validate_set_left_loop:
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    beq preprocess_bad_set
    cmp #';'
    beq preprocess_bad_set
    cmp #'='
    beq preprocess_validate_set_right
    cmp #' '
    beq preprocess_validate_set_left_next
    cmp #9
    beq preprocess_validate_set_left_next
    lda #$01
    sta preprocess_set_left_seen
preprocess_validate_set_left_next:
    inc preprocess_line_scan
    bne preprocess_validate_set_left_loop
preprocess_validate_set_right:
    lda preprocess_set_left_seen
    beq preprocess_bad_set
    inc preprocess_line_scan
    jsr preprocess_line_skip_spaces
    lda #$00
    sta preprocess_set_right_seen
preprocess_validate_set_right_loop:
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    beq preprocess_validate_set_done
    cmp #';'
    beq preprocess_validate_set_done
    cmp #' '
    beq preprocess_validate_set_right_next
    cmp #9
    beq preprocess_validate_set_right_next
    lda #$01
    sta preprocess_set_right_seen
preprocess_validate_set_right_next:
    inc preprocess_line_scan
    bne preprocess_validate_set_right_loop
preprocess_validate_set_done:
    lda preprocess_set_right_seen
    beq preprocess_bad_set
    clc
    rts
preprocess_bad_set:
    lda #<preprocess_msg_bad_set
    ldy #>preprocess_msg_bad_set
    jsr preprocess_set_diag
    sec
    rts

preprocess_init_main_include_name:
    lda #$00
    sta preprocess_include_dirs
    ldy #$00
preprocess_init_main_include_name_loop:
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq preprocess_init_main_include_name_suffix
    jsr uppercase_ascii
    sta preprocess_include_names,y
    iny
    cpy #(PREPROCESS_INCLUDE_NAME_SIZE - 5)
    bcc preprocess_init_main_include_name_loop
    lda #$00
    sta preprocess_include_names,y
    rts
preprocess_init_main_include_name_suffix:
    lda #'.'
    sta preprocess_include_names,y
    iny
    lda #'A'
    sta preprocess_include_names,y
    iny
    lda #'C'
    sta preprocess_include_names,y
    iny
    lda #'T'
    sta preprocess_include_names,y
    iny
    lda #$00
    sta preprocess_include_names,y
    rts

preprocess_parse_include:
    jsr preprocess_line_skip_spaces
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    cmp #'"'
    beq :+
    jmp preprocess_bad_include
:
    inc preprocess_line_scan
    lda #$00
    sta preprocess_value_len
preprocess_parse_include_name_loop:
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    bne :+
    jmp preprocess_bad_include
:
    cmp #'"'
    beq preprocess_parse_include_name_done
    jsr uppercase_ascii
    cmp #$5C
    bne :+
    lda #'/'
:
    jsr preprocess_append_value_char
    bcc :+
    jmp preprocess_bad_include
:
    inc preprocess_line_scan
    jmp preprocess_parse_include_name_loop
preprocess_parse_include_name_done:
    inc preprocess_line_scan
    ldx preprocess_value_len
    lda #$00
    sta preprocess_value_temp,x
    jsr preprocess_line_skip_spaces
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    beq preprocess_parse_include_normalize
    cmp #';'
    beq :+
    jmp preprocess_bad_include
:

preprocess_parse_include_normalize:
    lda #$FF
    sta preprocess_include_explicit_dir
    lda preprocess_value_len
    cmp #$04
    bcc preprocess_parse_include_no_prefix
    lda preprocess_value_temp+0
    cmp #'S'
    bne preprocess_parse_include_try_lib_prefix
    lda preprocess_value_temp+1
    cmp #'R'
    bne preprocess_parse_include_no_prefix
    lda preprocess_value_temp+2
    cmp #'C'
    bne preprocess_parse_include_no_prefix
    lda preprocess_value_temp+3
    cmp #'/'
    bne preprocess_parse_include_no_prefix
    lda #$00
    beq preprocess_parse_include_strip_prefix
preprocess_parse_include_try_lib_prefix:
    lda preprocess_value_temp+0
    cmp #'L'
    bne preprocess_parse_include_no_prefix
    lda preprocess_value_temp+1
    cmp #'I'
    bne preprocess_parse_include_no_prefix
    lda preprocess_value_temp+2
    cmp #'B'
    bne preprocess_parse_include_no_prefix
    lda preprocess_value_temp+3
    cmp #'/'
    bne preprocess_parse_include_no_prefix
    lda #$01
preprocess_parse_include_strip_prefix:
    sta preprocess_include_explicit_dir
    ldx #$00
preprocess_parse_include_strip_prefix_loop:
    lda preprocess_value_temp+4,x
    sta preprocess_value_temp,x
    beq preprocess_parse_include_prefix_done
    inx
    cpx #(PREPROCESS_DEFINE_VALUE_SIZE - 4)
    bcc preprocess_parse_include_strip_prefix_loop
    jmp preprocess_bad_include
preprocess_parse_include_prefix_done:
    txa
    sta preprocess_value_len

preprocess_parse_include_no_prefix:
    lda preprocess_value_len
    bne :+
    jmp preprocess_bad_include
:
    lda #$00
    sta preprocess_include_name_len
    ldx #$00
preprocess_parse_include_validate_loop:
    cpx preprocess_value_len
    bcs preprocess_parse_include_validate_done
    lda preprocess_value_temp,x
    cmp #'/'
    bne :+
    jmp preprocess_bad_include
:
    cmp #':'
    bne :+
    jmp preprocess_bad_include
:
    cmp #'.'
    bne preprocess_parse_include_validate_next
    lda #$01
    sta preprocess_include_name_len
    inx
    cpx preprocess_value_len
    bcs preprocess_parse_include_validate_done
    lda preprocess_value_temp,x
    cmp #'.'
    bne :+
    jmp preprocess_bad_include
:
    dex
preprocess_parse_include_validate_next:
    inx
    bne preprocess_parse_include_validate_loop
preprocess_parse_include_validate_done:
    lda preprocess_include_name_len
    bne preprocess_parse_include_have_extension
    ldx preprocess_value_len
    cpx #(PREPROCESS_INCLUDE_NAME_SIZE - 4)
    bcs preprocess_bad_include
    lda #'.'
    sta preprocess_value_temp,x
    inx
    lda #'A'
    sta preprocess_value_temp,x
    inx
    lda #'C'
    sta preprocess_value_temp,x
    inx
    lda #'T'
    sta preprocess_value_temp,x
    inx
    lda #$00
    sta preprocess_value_temp,x
    stx preprocess_value_len
preprocess_parse_include_have_extension:
    lda preprocess_value_len
    sta preprocess_set_right_seen
    cmp #PREPROCESS_INCLUDE_NAME_SIZE
    bcs preprocess_bad_include
    lda preprocess_include_explicit_dir
    cmp #$FF
    bne preprocess_parse_include_have_try_dir
    lda preprocess_input_dir
preprocess_parse_include_have_try_dir:
    sta preprocess_include_try_dir
    jsr preprocess_stage_include_try_dir
    bcc preprocess_parse_include_staged
    lda PREPROCESS_REU_PARAMS+5
    cmp #tool_file_status_nofile
    bne preprocess_include_load_fail
    lda preprocess_include_explicit_dir
    cmp #$FF
    bne preprocess_include_missing
    lda preprocess_include_try_dir
    eor #$01
    sta preprocess_include_try_dir
    jsr preprocess_stage_include_try_dir
    bcc preprocess_parse_include_staged
    lda PREPROCESS_REU_PARAMS+5
    cmp #tool_file_status_nofile
    beq preprocess_include_missing
    jmp preprocess_include_load_fail

preprocess_parse_include_staged:
    lda PREPROCESS_REU_PARAMS+8
    beq :+
    lda #<preprocess_msg_include_large
    ldy #>preprocess_msg_include_large
    jsr preprocess_set_diag
    sec
    rts
:
    lda PREPROCESS_REU_PARAMS+6
    sta preprocess_include_loaded_len
    lda PREPROCESS_REU_PARAMS+7
    sta preprocess_include_loaded_len+1
    jsr preprocess_include_check_cycle
    bcs preprocess_parse_include_fail
    jsr preprocess_enter_include
    rts

preprocess_bad_include:
    lda #<preprocess_msg_bad_include
    ldy #>preprocess_msg_bad_include
    jsr preprocess_set_diag
preprocess_parse_include_fail:
    sec
    rts
preprocess_include_missing:
    lda #<preprocess_msg_include_missing
    ldy #>preprocess_msg_include_missing
    jsr preprocess_set_diag
    sec
    rts
preprocess_include_load_fail:
    lda #<preprocess_msg_failed
    ldy #>preprocess_msg_failed
    jsr preprocess_set_diag
    sec
    rts

preprocess_stage_include_try_dir:
    ldx #$00
    lda preprocess_include_try_dir
    beq preprocess_stage_include_src_prefix
    lda #'L'
    sta preprocess_line_b,x
    inx
    lda #'I'
    sta preprocess_line_b,x
    inx
    lda #'B'
    bne preprocess_stage_include_prefix_tail
preprocess_stage_include_src_prefix:
    lda #'S'
    sta preprocess_line_b,x
    inx
    lda #'R'
    sta preprocess_line_b,x
    inx
    lda #'C'
preprocess_stage_include_prefix_tail:
    sta preprocess_line_b,x
    inx
    lda #'/'
    sta preprocess_line_b,x
    inx
    ldy #$00
preprocess_stage_include_name_loop:
    lda preprocess_value_temp,y
    sta preprocess_line_b,x
    beq preprocess_stage_include_path_ready
    iny
    inx
    cpx #$FF
    bcc preprocess_stage_include_name_loop
    jmp preprocess_bad_include
preprocess_stage_include_path_ready:
    lda #<preprocess_line_b
    sta PREPROCESS_REU_PARAMS+0
    lda #>preprocess_line_b
    sta PREPROCESS_REU_PARAMS+1
    lda #$00
    sta PREPROCESS_REU_PARAMS+2
    sta PREPROCESS_REU_PARAMS+3
    lda preprocess_input_depth
    clc
    adc #(PREPROCESS_INCLUDE_BANK_BASE + 1)
    sta PREPROCESS_REU_PARAMS+4
    lda #$00
    sta PREPROCESS_REU_PARAMS+5
    sta PREPROCESS_REU_PARAMS+6
    sta PREPROCESS_REU_PARAMS+7
    sta PREPROCESS_REU_PARAMS+8
    ldx #PREPROCESS_REU_PARAMS
    jsr svc_file_stage_reu_sc0
    lda PREPROCESS_REU_PARAMS+5
    cmp #tool_file_status_ok
    beq preprocess_stage_include_ok
    sec
    rts
preprocess_stage_include_ok:
    clc
    rts

preprocess_include_check_cycle:
    ldx #$00
preprocess_include_check_cycle_loop:
    cpx preprocess_input_depth
    bcc preprocess_include_check_cycle_slot
    beq preprocess_include_check_cycle_slot
    clc
    rts
preprocess_include_check_cycle_slot:
    lda preprocess_include_dirs,x
    cmp preprocess_include_try_dir
    bne preprocess_include_check_cycle_next
    jsr preprocess_set_include_slot_ptr_x
    ldy #$00
preprocess_include_check_cycle_name_loop:
    lda preprocess_value_temp,y
    cmp (ACTC_OVERLAY_WORK_ZP),y
    bne preprocess_include_check_cycle_next
    lda preprocess_value_temp,y
    beq preprocess_include_cycle
    iny
    cpy #PREPROCESS_INCLUDE_NAME_SIZE
    bcc preprocess_include_check_cycle_name_loop
preprocess_include_check_cycle_next:
    inx
    bne preprocess_include_check_cycle_loop
preprocess_include_cycle:
    lda #<preprocess_msg_include_cycle
    ldy #>preprocess_msg_include_cycle
    jsr preprocess_set_diag
    sec
    rts

preprocess_enter_include:
    ldx preprocess_input_depth
    cpx #PREPROCESS_INCLUDE_DEPTH_MAX
    bcc preprocess_enter_include_capacity_ok
    lda #<preprocess_msg_include_depth
    ldy #>preprocess_msg_include_depth
    jsr preprocess_set_diag
    sec
    rts
preprocess_enter_include_capacity_ok:
    lda preprocess_input_total
    sta preprocess_parent_total_lo,x
    lda preprocess_input_total+1
    sta preprocess_parent_total_hi,x
    lda preprocess_input_offset
    sta preprocess_parent_offset_lo,x
    lda preprocess_input_offset+1
    sta preprocess_parent_offset_hi,x
    lda preprocess_input_bank
    sta preprocess_parent_bank,x
    lda preprocess_input_dir
    sta preprocess_parent_dir,x
    lda preprocess_input_pushback_valid
    sta preprocess_parent_pushback_valid,x
    lda preprocess_input_pushback_byte
    sta preprocess_parent_pushback_byte,x
    inc preprocess_input_depth
    ldx preprocess_input_depth
    lda preprocess_include_try_dir
    sta preprocess_include_dirs,x
    sta preprocess_input_dir
    jsr preprocess_set_include_slot_ptr_x
    ldy #$00
preprocess_enter_include_name_loop:
    lda preprocess_value_temp,y
    sta (ACTC_OVERLAY_WORK_ZP),y
    beq preprocess_enter_include_name_done
    iny
    cpy #PREPROCESS_INCLUDE_NAME_SIZE
    bcc preprocess_enter_include_name_loop
preprocess_enter_include_name_done:
    lda preprocess_include_loaded_len
    sta preprocess_input_total
    lda preprocess_include_loaded_len+1
    sta preprocess_input_total+1
    lda #$00
    sta preprocess_input_offset
    sta preprocess_input_offset+1
    lda preprocess_input_depth
    clc
    adc #PREPROCESS_INCLUDE_BANK_BASE
    sta preprocess_input_bank
    jsr preprocess_invalidate_input_window
    clc
    rts

preprocess_pop_include:
    lda preprocess_input_depth
    beq preprocess_pop_include_fail
    dec preprocess_input_depth
    ldx preprocess_input_depth
    lda preprocess_parent_total_lo,x
    sta preprocess_input_total
    lda preprocess_parent_total_hi,x
    sta preprocess_input_total+1
    lda preprocess_parent_offset_lo,x
    sta preprocess_input_offset
    lda preprocess_parent_offset_hi,x
    sta preprocess_input_offset+1
    lda preprocess_parent_bank,x
    sta preprocess_input_bank
    lda preprocess_parent_dir,x
    sta preprocess_input_dir
    jsr preprocess_invalidate_input_window
    lda preprocess_parent_pushback_byte,x
    sta preprocess_input_pushback_byte
    lda preprocess_parent_pushback_valid,x
    sta preprocess_input_pushback_valid
    clc
    rts
preprocess_pop_include_fail:
    sec
    rts

preprocess_invalidate_input_window:
    lda #$00
    sta preprocess_input_window_remaining
    sta preprocess_input_window_remaining+1
    sta preprocess_input_window_index
    sta preprocess_input_pushback_valid
    rts

preprocess_set_include_slot_ptr_x:
    lda #<preprocess_include_names
    sta ACTC_OVERLAY_WORK_ZP
    lda #>preprocess_include_names
    sta ACTC_OVERLAY_WORK_ZP+1
    txa
    beq preprocess_set_include_slot_ptr_done
    tay
preprocess_set_include_slot_ptr_loop:
    clc
    lda ACTC_OVERLAY_WORK_ZP
    adc #PREPROCESS_INCLUDE_NAME_SIZE
    sta ACTC_OVERLAY_WORK_ZP
    lda ACTC_OVERLAY_WORK_ZP+1
    adc #$00
    sta ACTC_OVERLAY_WORK_ZP+1
    dey
    bne preprocess_set_include_slot_ptr_loop
preprocess_set_include_slot_ptr_done:
    rts

preprocess_expand_line:
    lda #<preprocess_line_a
    sta preprocess_expand_src_ptr
    lda #>preprocess_line_a
    sta preprocess_expand_src_ptr+1
    lda #<preprocess_line_b
    sta preprocess_expand_dst_ptr
    lda #>preprocess_line_b
    sta preprocess_expand_dst_ptr+1
    lda preprocess_line_len
    sta preprocess_expand_src_len
    lda #$00
    sta preprocess_expand_pass
preprocess_expand_pass_loop:
    lda #$00
    sta preprocess_expand_scan
    sta preprocess_expand_dst_len
    sta preprocess_expand_changed
preprocess_expand_char_loop:
    lda preprocess_expand_scan
    cmp preprocess_expand_src_len
    bcc :+
    jmp preprocess_expand_pass_done
:
    tay
    lda (preprocess_expand_src_ptr),y
    cmp #';'
    beq preprocess_expand_copy_tail
    cmp #'"'
    beq preprocess_expand_copy_string
    cmp #39
    beq preprocess_expand_copy_character
    jsr uppercase_ascii
    jsr uppercase_symbol_start_valid
    bcs :+
    jmp preprocess_expand_symbol
:
    ldy preprocess_expand_scan
    lda (preprocess_expand_src_ptr),y
    jsr preprocess_expand_append_char
    bcc :+
    jmp preprocess_expand_fail
:
    inc preprocess_expand_scan
    jmp preprocess_expand_char_loop

preprocess_expand_copy_tail:
    jsr preprocess_expand_copy_remaining
    bcc :+
    jmp preprocess_expand_fail
:
    jmp preprocess_expand_pass_done

preprocess_expand_copy_string:
    ldy preprocess_expand_scan
    lda (preprocess_expand_src_ptr),y
    jsr preprocess_expand_append_char
    bcc :+
    jmp preprocess_expand_fail
:
    inc preprocess_expand_scan
preprocess_expand_copy_string_loop:
    lda preprocess_expand_scan
    cmp preprocess_expand_src_len
    bcc :+
    jmp preprocess_expand_pass_done
:
    tay
    lda (preprocess_expand_src_ptr),y
    pha
    jsr preprocess_expand_append_char
    bcc :+
    jmp preprocess_expand_copy_string_pop_fail
:
    inc preprocess_expand_scan
    pla
    cmp #$5C
    beq preprocess_expand_copy_string_escape
    cmp #'"'
    bne preprocess_expand_copy_string_loop
    jmp preprocess_expand_char_loop
preprocess_expand_copy_string_escape:
    lda preprocess_expand_scan
    cmp preprocess_expand_src_len
    bcc :+
    jmp preprocess_expand_pass_done
:
    tay
    lda (preprocess_expand_src_ptr),y
    jsr preprocess_expand_append_char
    bcc :+
    jmp preprocess_expand_fail
:
    inc preprocess_expand_scan
    jmp preprocess_expand_copy_string_loop
preprocess_expand_copy_string_pop_fail:
    pla
    jmp preprocess_expand_fail

preprocess_expand_copy_character:
    ldy preprocess_expand_scan
    lda (preprocess_expand_src_ptr),y
    jsr preprocess_expand_append_char
    bcc :+
    jmp preprocess_expand_fail
:
    inc preprocess_expand_scan
    lda preprocess_expand_scan
    cmp preprocess_expand_src_len
    bcc :+
    jmp preprocess_expand_pass_done
:
    tay
    lda (preprocess_expand_src_ptr),y
    pha
    jsr preprocess_expand_append_char
    bcc :+
    jmp preprocess_expand_copy_character_pop_fail
:
    inc preprocess_expand_scan
    pla
    cmp #$5C
    beq :+
    jmp preprocess_expand_copy_character_optional_quote
:
    lda preprocess_expand_scan
    cmp preprocess_expand_src_len
    bcc :+
    jmp preprocess_expand_pass_done
:
    tay
    lda (preprocess_expand_src_ptr),y
    jsr preprocess_expand_append_char
    bcc :+
    jmp preprocess_expand_fail
:
    inc preprocess_expand_scan
preprocess_expand_copy_character_optional_quote:
    lda preprocess_expand_scan
    cmp preprocess_expand_src_len
    bcc :+
    jmp preprocess_expand_pass_done
:
    tay
    lda (preprocess_expand_src_ptr),y
    cmp #39
    beq :+
    jmp preprocess_expand_char_loop
:
    jsr preprocess_expand_append_char
    bcc :+
    jmp preprocess_expand_fail
:
    inc preprocess_expand_scan
    jmp preprocess_expand_char_loop
preprocess_expand_copy_character_pop_fail:
    pla
    jmp preprocess_expand_fail

preprocess_expand_symbol:
    lda preprocess_expand_scan
    sta preprocess_expand_token_start
    ldx #$00
preprocess_expand_symbol_loop:
    lda preprocess_expand_scan
    cmp preprocess_expand_src_len
    bcc :+
    jmp preprocess_expand_symbol_ready
:
    tay
    lda (preprocess_expand_src_ptr),y
    jsr uppercase_ascii
    jsr uppercase_symbol_body_valid
    bcs preprocess_expand_symbol_ready
    cpx #24
    bcc :+
    jmp preprocess_expand_fail
:
    sta preprocess_name_temp,x
    inx
    inc preprocess_expand_scan
    jmp preprocess_expand_symbol_loop
preprocess_expand_symbol_ready:
    lda #$00
    sta preprocess_name_temp,x
    jsr preprocess_find_define
    bcs preprocess_expand_symbol_original
    lda #$01
    sta preprocess_expand_changed
    ldy #$00
preprocess_expand_symbol_value_loop:
    lda (preprocess_value_slot_ptr),y
    bne :+
    jmp preprocess_expand_char_loop
:
    jsr preprocess_expand_append_char
    bcc :+
    jmp preprocess_expand_fail
:
    iny
    cpy #PREPROCESS_DEFINE_VALUE_SIZE
    bcc preprocess_expand_symbol_value_loop
    jmp preprocess_expand_fail
preprocess_expand_symbol_original:
    lda preprocess_expand_token_start
    sta preprocess_expand_copy_index
preprocess_expand_symbol_original_loop:
    lda preprocess_expand_copy_index
    cmp preprocess_expand_scan
    bcc :+
    jmp preprocess_expand_char_loop
:
    tay
    lda (preprocess_expand_src_ptr),y
    jsr preprocess_expand_append_char
    bcc :+
    jmp preprocess_expand_fail
:
    inc preprocess_expand_copy_index
    jmp preprocess_expand_symbol_original_loop

preprocess_expand_copy_remaining:
    lda preprocess_expand_scan
    cmp preprocess_expand_src_len
    bcc :+
    jmp preprocess_expand_copy_remaining_done
:
    tay
    lda (preprocess_expand_src_ptr),y
    jsr preprocess_expand_append_char
    bcc :+
    jmp preprocess_expand_copy_remaining_fail
:
    inc preprocess_expand_scan
    jmp preprocess_expand_copy_remaining
preprocess_expand_copy_remaining_done:
    clc
preprocess_expand_copy_remaining_fail:
    rts

preprocess_expand_append_char:
    sta preprocess_expand_saved_char
    tya
    pha
    ldx preprocess_expand_dst_len
    cpx #$FE
    bcs preprocess_expand_append_char_fail
    ldy preprocess_expand_dst_len
    lda preprocess_expand_saved_char
    sta (preprocess_expand_dst_ptr),y
    inc preprocess_expand_dst_len
    pla
    tay
    clc
    rts
preprocess_expand_append_char_fail:
    pla
    tay
    lda #<preprocess_msg_expand_long
    ldy #>preprocess_msg_expand_long
    jsr preprocess_set_diag
    sec
    rts

preprocess_expand_pass_done:
    ldy preprocess_expand_dst_len
    lda #$00
    sta (preprocess_expand_dst_ptr),y
    lda preprocess_expand_changed
    beq preprocess_expand_publish
    jsr preprocess_expand_result_equals_source
    bcc preprocess_expand_cycle
    inc preprocess_expand_pass
    lda preprocess_expand_pass
    cmp #PREPROCESS_EXPANSION_LIMIT
    bcs preprocess_expand_limit
    jsr preprocess_expand_swap_buffers
    jmp preprocess_expand_pass_loop

preprocess_expand_publish:
    lda preprocess_expand_dst_ptr
    sta preprocess_expanded_ptr
    lda preprocess_expand_dst_ptr+1
    sta preprocess_expanded_ptr+1
    lda preprocess_expand_dst_len
    sta preprocess_expanded_len
    clc
    rts

preprocess_expand_result_equals_source:
    lda preprocess_expand_dst_len
    cmp preprocess_expand_src_len
    bne preprocess_expand_result_differs
    ldy #$00
preprocess_expand_result_equals_source_loop:
    cpy preprocess_expand_src_len
    bcs preprocess_expand_result_equal
    lda (preprocess_expand_src_ptr),y
    cmp (preprocess_expand_dst_ptr),y
    bne preprocess_expand_result_differs
    iny
    bne preprocess_expand_result_equals_source_loop
preprocess_expand_result_equal:
    clc
    rts
preprocess_expand_result_differs:
    sec
    rts

preprocess_expand_swap_buffers:
    lda preprocess_expand_src_ptr
    pha
    lda preprocess_expand_dst_ptr
    sta preprocess_expand_src_ptr
    pla
    sta preprocess_expand_dst_ptr
    lda preprocess_expand_src_ptr+1
    pha
    lda preprocess_expand_dst_ptr+1
    sta preprocess_expand_src_ptr+1
    pla
    sta preprocess_expand_dst_ptr+1
    lda preprocess_expand_dst_len
    sta preprocess_expand_src_len
    rts

preprocess_expand_cycle:
    lda #<preprocess_msg_define_cycle
    ldy #>preprocess_msg_define_cycle
    jsr preprocess_set_diag
    sec
    rts
preprocess_expand_limit:
    lda #<preprocess_msg_expand_limit
    ldy #>preprocess_msg_expand_limit
    jsr preprocess_set_diag
preprocess_expand_fail:
    sec
    rts

.include "actc_overlay_const.inc"
.include "actc_overlay_routine_address.inc"

preprocess_keyword_define:
    .asciiz "DEFINE"
preprocess_keyword_set:
    .asciiz "SET"
preprocess_keyword_include:
    .asciiz "INCLUDE"
preprocess_msg_failed:
    .asciiz "PREPROCESS FAIL"
preprocess_msg_source_large:
    .asciiz "SOURCE >64K"
preprocess_msg_line_long:
    .asciiz "SOURCE LINE LONG"
preprocess_msg_reu:
    .asciiz "PREPROCESS REU"
preprocess_msg_bad_define:
    .asciiz "BAD DEFINE"
preprocess_msg_define_limit:
    .asciiz "DEFINE LIMIT"
preprocess_msg_define_cycle:
    .asciiz "DEFINE CYCLE"
preprocess_msg_expand_limit:
    .asciiz "DEFINE EXPAND"
preprocess_msg_expand_long:
    .asciiz "EXPANDED LINE LONG"
preprocess_msg_bad_set:
    .asciiz "BAD SET"
preprocess_msg_bad_include:
    .asciiz "BAD INCLUDE"
preprocess_msg_include_depth:
    .asciiz "INCLUDE DEPTH"
preprocess_msg_include_cycle:
    .asciiz "INCLUDE CYCLE"
preprocess_msg_include_missing:
    .asciiz "INCLUDE NOT FOUND"
preprocess_msg_include_large:
    .asciiz "INCLUDE >64K"
preprocess_msg_bad_const:
    .asciiz "BAD CONST"
preprocess_msg_const_range:
    .asciiz "CONST RANGE"

.segment "BSS"
preprocess_diag_ptr:
    .res 2
preprocess_input_total:
    .res 2
preprocess_input_offset:
    .res 2
preprocess_input_window_remaining:
    .res 2
preprocess_input_window_index:
    .res 1
preprocess_input_pushback_valid:
    .res 1
preprocess_input_pushback_byte:
    .res 1
preprocess_input_depth:
    .res 1
preprocess_input_bank:
    .res 1
preprocess_input_dir:
    .res 1
preprocess_io_failed:
    .res 1
preprocess_transfer_len:
    .res 2
preprocess_output_total:
    .res 2
preprocess_output_flush_offset:
    .res 2
preprocess_output_count:
    .res 1
preprocess_copy_offset:
    .res 2
preprocess_line_len:
    .res 1
preprocess_line_scan:
    .res 1
preprocess_expected_char:
    .res 1
preprocess_define_count:
    .res 1
preprocess_define_used:
    .res 2
preprocess_define_new_used:
    .res 2
preprocess_define_scan_count:
    .res 1
preprocess_define_record_size:
    .res 1
preprocess_define_name_len:
    .res 1
preprocess_define_continues:
    .res 1
preprocess_const_continues:
    .res 1
preprocess_const_type:
    .res 1
preprocess_const_expr_scan:
    .res 1
preprocess_const_value_lo:
    .res 1
preprocess_const_value_hi:
    .res 1
    .res PREPROCESS_CONST_VALUE_WIDTH - 2
preprocess_const_lhs_lo:
    .res 1
preprocess_const_lhs_hi:
    .res 1
    .res PREPROCESS_CONST_VALUE_WIDTH - 2
preprocess_const_rhs_lo:
    .res 1
preprocess_const_rhs_hi:
    .res 1
    .res PREPROCESS_CONST_VALUE_WIDTH - 2
preprocess_const_work:
    .res PREPROCESS_CONST_VALUE_WIDTH
preprocess_const_digit_seen:
    .res 1
preprocess_const_base:
    .res 1
preprocess_const_digit:
    .res 1
preprocess_const_expect_operand:
    .res 1
preprocess_const_value_count:
    .res 1
preprocess_const_operator_count:
    .res 1
preprocess_const_current_operator:
    .res 1
preprocess_const_apply_operator:
    .res 1
preprocess_const_top_precedence:
    .res 1
preprocess_const_math_count:
    .res 1
preprocess_const_math_sign:
    .res 1
preprocess_const_left_negative:
    .res 1
preprocess_const_builtin_len:
    .res 1
preprocess_const_builtin_value:
    .res 1
preprocess_const_name_temp:
    .res PREPROCESS_DEFINE_NAME_SIZE
preprocess_const_eval_target:
    .res 2
preprocess_const_eval_target_minus_one:
    .res 1
preprocess_const_operator_stack:
    .res PREPROCESS_CONST_OPERATOR_STACK_MAX
preprocess_const_value_stack:
    .res PREPROCESS_CONST_VALUE_WIDTH * PREPROCESS_CONST_VALUE_STACK_MAX
preprocess_value_len:
    .res 1
preprocess_set_left_seen:
    .res 1
preprocess_set_right_seen:
    .res 1
preprocess_source_changed:
    .res 1
preprocess_expand_src_len:
    .res 1
preprocess_expand_dst_len:
    .res 1
preprocess_expand_scan:
    .res 1
preprocess_expand_pass:
    .res 1
preprocess_expand_changed:
    .res 1
preprocess_expand_token_start:
    .res 1
preprocess_expand_copy_index:
    .res 1
preprocess_expand_saved_char:
    .res 1
preprocess_expanded_ptr:
    .res 2
preprocess_expanded_len:
    .res 1
preprocess_emit_index:
    .res 1
preprocess_include_explicit_dir:
    .res 1
preprocess_include_try_dir:
    .res 1
preprocess_include_name_len:
    .res 1
preprocess_include_loaded_len:
    .res 2
preprocess_name_temp:
    .res PREPROCESS_DEFINE_NAME_SIZE
preprocess_value_temp:
    .res PREPROCESS_DEFINE_VALUE_SIZE
preprocess_line_a:
    .res 256
preprocess_line_b:
    .res 256
preprocess_input_window:
    .res 256
preprocess_output_window:
    .res 256
preprocess_define_store:
    .res PREPROCESS_DEFINE_STORE_SIZE
preprocess_parent_total_lo:
    .res PREPROCESS_INCLUDE_DEPTH_MAX
preprocess_parent_total_hi:
    .res PREPROCESS_INCLUDE_DEPTH_MAX
preprocess_parent_offset_lo:
    .res PREPROCESS_INCLUDE_DEPTH_MAX
preprocess_parent_offset_hi:
    .res PREPROCESS_INCLUDE_DEPTH_MAX
preprocess_parent_bank:
    .res PREPROCESS_INCLUDE_DEPTH_MAX
preprocess_parent_dir:
    .res PREPROCESS_INCLUDE_DEPTH_MAX
preprocess_parent_pushback_valid:
    .res PREPROCESS_INCLUDE_DEPTH_MAX
preprocess_parent_pushback_byte:
    .res PREPROCESS_INCLUDE_DEPTH_MAX
preprocess_include_dirs:
    .res PREPROCESS_INCLUDE_DEPTH_MAX + 1
preprocess_include_names:
    .res (PREPROCESS_INCLUDE_DEPTH_MAX + 1) * PREPROCESS_INCLUDE_NAME_SIZE

.segment "CODE"
