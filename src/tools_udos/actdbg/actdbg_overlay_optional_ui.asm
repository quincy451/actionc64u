.include "actdbg_overlay_abi.inc"
.include "actdbg_overlay_resident.inc"

.export actdbg_overlay_header
.export actdbg_overlay_entry
.export actdbg_overlay_end

.segment "CODE"

actdbg_overlay_header:
    .byte 'D','G','O','V'
    .byte ACTDBG_OVERLAY_ABI_VERSION
    .word ACTDBG_OVERLAY_EXEC_BASE
    .word actdbg_overlay_entry
    .word actdbg_overlay_end - actdbg_overlay_header
    .word $0000

status_ptr = ACTDBG_RES_status_ptr
text_ptr = ACTDBG_RES_text_ptr
line_start_ptr = ACTDBG_RES_line_start_ptr
word_tmp = ACTDBG_RES_word_tmp
const_ptr = ACTDBG_RES_const_ptr
line_buffer = ACTDBG_RES_line_buffer
current_row = ACTDBG_RES_current_row
current_col = ACTDBG_RES_current_col
line_number_lo = ACTDBG_RES_line_number_lo
line_number_hi = ACTDBG_RES_line_number_hi
hex_tmp = ACTDBG_RES_hex_tmp
digit_flag = ACTDBG_RES_digit_flag
summary_decimal_index = ACTDBG_RES_summary_decimal_index
token_copy_limit = ACTDBG_RES_token_copy_limit
draw_limit = ACTDBG_RES_draw_limit
actdbg_target_module_lo = ACTDBG_RES_actdbg_target_module_lo
actdbg_target_module_hi = ACTDBG_RES_actdbg_target_module_hi
actdbg_target_export_lo = ACTDBG_RES_actdbg_target_export_lo
actdbg_target_export_hi = ACTDBG_RES_actdbg_target_export_hi
actdbg_target_file_lo = ACTDBG_RES_actdbg_target_file_lo
actdbg_target_file_hi = ACTDBG_RES_actdbg_target_file_hi
actdbg_target_line_lo = ACTDBG_RES_actdbg_target_line_lo
actdbg_target_line_hi = ACTDBG_RES_actdbg_target_line_hi
actdbg_target_col = ACTDBG_RES_actdbg_target_col
actdbg_global_summary = ACTDBG_RES_actdbg_global_summary
actdbg_param_summary = ACTDBG_RES_actdbg_param_summary
actdbg_local_summary = ACTDBG_RES_actdbg_local_summary
actdbg_backtrace_summary = ACTDBG_RES_actdbg_backtrace_summary
actdbg_trace_summary0 = ACTDBG_RES_actdbg_trace_summary0
actdbg_trace_summary1 = ACTDBG_RES_actdbg_trace_summary1
actdbg_trace_summary2 = ACTDBG_RES_actdbg_trace_summary2
actdbg_var_scope = ACTDBG_RES_actdbg_var_scope
actdbg_live_var_type = ACTDBG_RES_actdbg_live_var_type
actdbg_current_pc_lo = ACTDBG_RES_actdbg_current_pc_lo
actdbg_current_pc_hi = ACTDBG_RES_actdbg_current_pc_hi
actdbg_proc_name = ACTDBG_RES_actdbg_proc_name
actdbg_trace_proc_name = ACTDBG_RES_actdbg_trace_proc_name
actdbg_backtrace_index = ACTDBG_RES_actdbg_backtrace_index
actdbg_backtrace_slot = ACTDBG_RES_actdbg_backtrace_slot
actdbg_backtrace_len = ACTDBG_RES_actdbg_backtrace_len
actdbg_backtrace_pc_lo = ACTDBG_RES_actdbg_backtrace_pc_lo
actdbg_backtrace_pc_hi = ACTDBG_RES_actdbg_backtrace_pc_hi
actdbg_native_call_depth = ACTDBG_RES_actdbg_native_call_depth
actdbg_native_callstack_lo = ACTDBG_RES_actdbg_native_callstack_lo
actdbg_native_callstack_hi = ACTDBG_RES_actdbg_native_callstack_hi
actdbg_trace_best_found = ACTDBG_RES_actdbg_trace_best_found
actdbg_trace_best_pc_lo = ACTDBG_RES_actdbg_trace_best_pc_lo
actdbg_trace_best_pc_hi = ACTDBG_RES_actdbg_trace_best_pc_hi
actdbg_dbg_candidate_pc_lo = ACTDBG_RES_actdbg_dbg_candidate_pc_lo
actdbg_dbg_candidate_pc_hi = ACTDBG_RES_actdbg_dbg_candidate_pc_hi
set_dbg_scan_to_body = ACTDBG_RES_set_dbg_scan_to_body
copy_dbg_line_to_buffer = ACTDBG_RES_copy_dbg_line_to_buffer
token_scan_begin = ACTDBG_RES_token_scan_begin
token_skip_forward = ACTDBG_RES_token_skip_forward
token_parse_u16 = ACTDBG_RES_token_parse_u16
token_copy_to_buffer = ACTDBG_RES_token_copy_to_buffer
parse_current_var_summary_fields = ACTDBG_RES_parse_current_var_summary_fields
append_current_live_var_name_and_value_to_summary = ACTDBG_RES_append_current_live_var_name_and_value_to_summary
append_cstr_to_summary = ACTDBG_RES_append_cstr_to_summary
append_summary_char_a = ACTDBG_RES_append_summary_char_a
append_summary_hex_byte_a = ACTDBG_RES_append_summary_hex_byte_a
append_summary_word_decimal = ACTDBG_RES_append_summary_word_decimal
append_backtrace_separator = ACTDBG_RES_append_backtrace_separator
draw_const_string_at = ACTDBG_RES_draw_const_string_at
save_summary_cursor = ACTDBG_RES_save_summary_cursor
restore_summary_cursor = ACTDBG_RES_restore_summary_cursor

actdbg_overlay_entry:
    lda ACTDBG_RES_actdbg_overlay_requested_cmd
    cmp #ACTDBG_OVERLAY_CMD_DRAW_OPTIONAL_VIEW
    bne :+
    jmp actdbg_overlay_draw_optional_view
:   cmp #ACTDBG_OVERLAY_CMD_NEXT_PROC
    bne :+
    jmp select_next_proc_cursor
:   cmp #ACTDBG_OVERLAY_CMD_NEXT_LINE
    bne :+
    jmp select_next_line_cursor
:   cmp #ACTDBG_OVERLAY_CMD_PREV_SOURCE_FILE
    bne :+
    jmp select_prev_source_file_cursor
:   cmp #ACTDBG_OVERLAY_CMD_NEXT_SOURCE_FILE
    bne :+
    jmp select_next_source_file_cursor
:   cmp #ACTDBG_OVERLAY_CMD_REBUILD_STOP_SUMMARIES
    bne :+
    jmp actdbg_overlay_rebuild_stop_summaries
:   cmp #ACTDBG_OVERLAY_CMD_DRAW_VARIABLE_SUMMARIES
    bne :+
    jmp draw_variable_summaries
:   cmp #ACTDBG_OVERLAY_CMD_TOGGLE_BREAKPOINT
    bne :+
    jmp toggle_current_line_breakpoint
:   sec
    lda #ACTDBG_OVERLAY_STATUS_FAILED
    rts

actdbg_overlay_draw_optional_view:
    lda ACTDBG_RES_actdbg_break_list_view
    beq actdbg_overlay_draw_trace_view
    jsr rebuild_breakpoint_list_summaries
    jsr draw_breakpoint_list
    clc
    lda #ACTDBG_OVERLAY_STATUS_OK
    rts
actdbg_overlay_draw_trace_view:
    jsr draw_backtrace_details
    clc
    lda #ACTDBG_OVERLAY_STATUS_OK
    rts

actdbg_overlay_rebuild_stop_summaries:
    jsr rebuild_backtrace_summary
    jsr rebuild_variable_summaries_for_current_scope
    clc
    lda #ACTDBG_OVERLAY_STATUS_OK
    rts

rebuild_breakpoint_list_summaries:
    ldx #36
rebuild_break_list_clear_loop:
    lda #$00
    sta ACTDBG_RES_actdbg_trace_summary0,x
    sta ACTDBG_RES_actdbg_trace_summary1,x
    sta ACTDBG_RES_actdbg_trace_summary2,x
    dex
    bpl rebuild_break_list_clear_loop
    lda #$00
    sta ACTDBG_RES_actdbg_lookup_found
    ldx #$00
rebuild_break_list_slot_loop:
    cpx #4
    bcs rebuild_break_list_done
    lda ACTDBG_RES_actdbg_break_active,x
    beq rebuild_break_list_next
    lda ACTDBG_RES_actdbg_lookup_found
    cmp #$03
    bcs rebuild_break_list_done
    txa
    pha
    lda ACTDBG_RES_actdbg_break_module_lo,x
    sta ACTDBG_RES_actdbg_lookup_module_lo
    lda ACTDBG_RES_actdbg_break_module_hi,x
    sta ACTDBG_RES_actdbg_lookup_module_hi
    lda ACTDBG_RES_actdbg_break_file_lo,x
    sta ACTDBG_RES_actdbg_lookup_file_lo
    lda ACTDBG_RES_actdbg_break_file_hi,x
    sta ACTDBG_RES_actdbg_lookup_file_hi
    lda #<ACTDBG_RES_source_rel_path
    ldy #>ACTDBG_RES_source_rel_path
    jsr ACTDBG_RES_lookup_source_path_for_lookup_ids_to_buffer
    lda ACTDBG_RES_actdbg_lookup_found
    jsr set_trace_summary_buffer_from_a
    ldx #$00
    pla
    tay
    tya
    sta ACTDBG_RES_hex_tmp
    lda ACTDBG_RES_source_rel_path
    beq rebuild_break_list_unknown
    lda #<ACTDBG_RES_source_rel_path
    ldy #>ACTDBG_RES_source_rel_path
    jsr ACTDBG_RES_append_cstr_to_summary
    jmp rebuild_break_list_append_line
rebuild_break_list_unknown:
    lda #'?'
    jsr ACTDBG_RES_append_summary_char_a
rebuild_break_list_append_line:
    ldy ACTDBG_RES_hex_tmp
    lda #':'
    jsr ACTDBG_RES_append_summary_char_a
    lda ACTDBG_RES_actdbg_break_line_lo,y
    sta ACTDBG_RES_word_tmp
    lda ACTDBG_RES_actdbg_break_line_hi,y
    sta ACTDBG_RES_word_tmp+1
    jsr ACTDBG_RES_append_summary_word_decimal
    ldy #$00
    lda #$00
    sta (ACTDBG_RES_const_ptr),y
    inc ACTDBG_RES_actdbg_lookup_found
    tya
    tax
rebuild_break_list_next:
    inx
    jmp rebuild_break_list_slot_loop
rebuild_break_list_done:
    lda ACTDBG_RES_actdbg_lookup_found
    bne :+
    lda #<ACTDBG_RES_actdbg_trace_summary0
    sta ACTDBG_RES_const_ptr
    lda #>ACTDBG_RES_actdbg_trace_summary0
    sta ACTDBG_RES_const_ptr+1
    ldx #$00
    lda #'N'
    jsr ACTDBG_RES_append_summary_char_a
    lda #'O'
    jsr ACTDBG_RES_append_summary_char_a
    lda #'N'
    jsr ACTDBG_RES_append_summary_char_a
    lda #'E'
    jsr ACTDBG_RES_append_summary_char_a
    ldy #$00
    lda #$00
    sta (ACTDBG_RES_const_ptr),y
:   rts

set_trace_summary_buffer_from_a:
    cmp #$00
    bne :+
    lda #<ACTDBG_RES_actdbg_trace_summary0
    sta ACTDBG_RES_const_ptr
    lda #>ACTDBG_RES_actdbg_trace_summary0
    sta ACTDBG_RES_const_ptr+1
    rts
:   cmp #$01
    bne :+
    lda #<ACTDBG_RES_actdbg_trace_summary1
    sta ACTDBG_RES_const_ptr
    lda #>ACTDBG_RES_actdbg_trace_summary1
    sta ACTDBG_RES_const_ptr+1
    rts
:   lda #<ACTDBG_RES_actdbg_trace_summary2
    sta ACTDBG_RES_const_ptr
    lda #>ACTDBG_RES_actdbg_trace_summary2
    sta ACTDBG_RES_const_ptr+1
    rts

set_cursor_from_lookup:
    lda ACTDBG_RES_actdbg_lookup_module_lo
    sta ACTDBG_RES_actdbg_cursor_module_lo
    lda ACTDBG_RES_actdbg_lookup_module_hi
    sta ACTDBG_RES_actdbg_cursor_module_hi
    lda ACTDBG_RES_actdbg_lookup_file_lo
    sta ACTDBG_RES_actdbg_cursor_file_lo
    lda ACTDBG_RES_actdbg_lookup_file_hi
    sta ACTDBG_RES_actdbg_cursor_file_hi
    lda ACTDBG_RES_actdbg_lookup_line_lo
    sta ACTDBG_RES_actdbg_cursor_line_lo
    lda ACTDBG_RES_actdbg_lookup_line_hi
    sta ACTDBG_RES_actdbg_cursor_line_hi
    lda ACTDBG_RES_actdbg_lookup_col
    sta ACTDBG_RES_actdbg_cursor_col
    lda #$00
    sta ACTDBG_RES_actdbg_source_col_offset
    clc
    lda #ACTDBG_OVERLAY_STATUS_OK
    rts

set_cursor_to_first_line_for_lookup_file:
    lda #$01
    sta ACTDBG_RES_actdbg_lookup_line_lo
    lda #$00
    sta ACTDBG_RES_actdbg_lookup_line_hi
    sta ACTDBG_RES_actdbg_lookup_col
    jsr ACTDBG_RES_set_dbg_scan_to_body
set_cursor_file_line_loop:
    jsr ACTDBG_RES_copy_dbg_line_to_buffer
    bcc :+
    jmp set_cursor_file_proc_fallback
:   lda ACTDBG_RES_line_buffer
    cmp #'l'
    bne set_cursor_file_line_loop
    jsr ACTDBG_RES_token_scan_begin
    jsr ACTDBG_RES_token_skip_forward
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    cmp ACTDBG_RES_actdbg_lookup_module_lo
    bne set_cursor_file_line_loop
    lda ACTDBG_RES_status_ptr+1
    cmp ACTDBG_RES_actdbg_lookup_module_hi
    bne set_cursor_file_line_loop
    jsr ACTDBG_RES_token_skip_forward
    jsr ACTDBG_RES_token_skip_forward
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    cmp ACTDBG_RES_actdbg_lookup_file_lo
    bne set_cursor_file_line_loop
    lda ACTDBG_RES_status_ptr+1
    cmp ACTDBG_RES_actdbg_lookup_file_hi
    bne set_cursor_file_line_loop
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_lookup_line_lo
    lda ACTDBG_RES_status_ptr+1
    sta ACTDBG_RES_actdbg_lookup_line_hi
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_lookup_col
    jmp set_cursor_from_lookup
set_cursor_file_proc_fallback:
    jsr ACTDBG_RES_set_dbg_scan_to_body
set_cursor_file_proc_loop:
    jsr ACTDBG_RES_copy_dbg_line_to_buffer
    bcc :+
    jmp set_cursor_from_lookup
:   lda ACTDBG_RES_line_buffer
    cmp #'q'
    bne set_cursor_file_proc_loop
    jsr ACTDBG_RES_token_scan_begin
    jsr ACTDBG_RES_token_skip_forward
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    cmp ACTDBG_RES_actdbg_lookup_module_lo
    bne set_cursor_file_proc_loop
    lda ACTDBG_RES_status_ptr+1
    cmp ACTDBG_RES_actdbg_lookup_module_hi
    bne set_cursor_file_proc_loop
    jsr ACTDBG_RES_token_skip_forward
    jsr ACTDBG_RES_token_skip_forward
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    cmp ACTDBG_RES_actdbg_lookup_file_lo
    bne set_cursor_file_proc_loop
    lda ACTDBG_RES_status_ptr+1
    cmp ACTDBG_RES_actdbg_lookup_file_hi
    bne set_cursor_file_proc_loop
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_lookup_line_lo
    lda ACTDBG_RES_status_ptr+1
    sta ACTDBG_RES_actdbg_lookup_line_hi
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_lookup_col
    jmp set_cursor_from_lookup

set_cursor_to_first_line_for_lookup_export:
    jsr ACTDBG_RES_set_dbg_scan_to_body
set_cursor_export_line_loop:
    jsr ACTDBG_RES_copy_dbg_line_to_buffer
    bcc :+
    jmp set_cursor_from_lookup
:   lda ACTDBG_RES_line_buffer
    cmp #'l'
    bne set_cursor_export_line_loop
    jsr ACTDBG_RES_token_scan_begin
    jsr ACTDBG_RES_token_skip_forward
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    cmp ACTDBG_RES_actdbg_lookup_module_lo
    bne set_cursor_export_line_loop
    lda ACTDBG_RES_status_ptr+1
    cmp ACTDBG_RES_actdbg_lookup_module_hi
    bne set_cursor_export_line_loop
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    cmp ACTDBG_RES_actdbg_lookup_export_lo
    bne set_cursor_export_line_loop
    lda ACTDBG_RES_status_ptr+1
    cmp ACTDBG_RES_actdbg_lookup_export_hi
    bne set_cursor_export_line_loop
    jsr ACTDBG_RES_token_skip_forward
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_lookup_file_lo
    lda ACTDBG_RES_status_ptr+1
    sta ACTDBG_RES_actdbg_lookup_file_hi
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_lookup_line_lo
    lda ACTDBG_RES_status_ptr+1
    sta ACTDBG_RES_actdbg_lookup_line_hi
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_lookup_col
    jmp set_cursor_from_lookup

select_next_source_file_cursor:
    lda #$00
    sta ACTDBG_RES_actdbg_lookup_found
    jsr ACTDBG_RES_set_dbg_scan_to_body
select_next_source_file_loop:
    jsr ACTDBG_RES_copy_dbg_line_to_buffer
    bcc select_next_source_file_have_line
    lda ACTDBG_RES_actdbg_lookup_found
    bne select_next_source_file_wrap
    sec
    lda #ACTDBG_OVERLAY_STATUS_FAILED
    rts
select_next_source_file_wrap:
    jmp set_cursor_to_first_line_for_lookup_file
select_next_source_file_have_line:
    lda ACTDBG_RES_line_buffer
    cmp #'f'
    bne select_next_source_file_loop
    jsr ACTDBG_RES_token_scan_begin
    jsr ACTDBG_RES_token_skip_forward
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_dbg_candidate_module_lo
    lda ACTDBG_RES_status_ptr+1
    sta ACTDBG_RES_actdbg_dbg_candidate_module_hi
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_dbg_candidate_file_lo
    lda ACTDBG_RES_status_ptr+1
    sta ACTDBG_RES_actdbg_dbg_candidate_file_hi
    lda ACTDBG_RES_actdbg_lookup_found
    bne :+
    lda ACTDBG_RES_actdbg_dbg_candidate_module_lo
    sta ACTDBG_RES_actdbg_lookup_module_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_module_hi
    sta ACTDBG_RES_actdbg_lookup_module_hi
    lda ACTDBG_RES_actdbg_dbg_candidate_file_lo
    sta ACTDBG_RES_actdbg_lookup_file_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_file_hi
    sta ACTDBG_RES_actdbg_lookup_file_hi
    lda #$01
    sta ACTDBG_RES_actdbg_lookup_found
:   lda ACTDBG_RES_actdbg_dbg_candidate_module_hi
    cmp ACTDBG_RES_actdbg_cursor_module_hi
    bcs :+
    jmp select_next_source_file_loop
:   bne select_next_source_file_pick_candidate
    lda ACTDBG_RES_actdbg_dbg_candidate_module_lo
    cmp ACTDBG_RES_actdbg_cursor_module_lo
    bcs :+
    jmp select_next_source_file_loop
:   bne select_next_source_file_pick_candidate
    lda ACTDBG_RES_actdbg_dbg_candidate_file_hi
    cmp ACTDBG_RES_actdbg_cursor_file_hi
    bcs :+
    jmp select_next_source_file_loop
:   bne select_next_source_file_pick_candidate
    lda ACTDBG_RES_actdbg_dbg_candidate_file_lo
    cmp ACTDBG_RES_actdbg_cursor_file_lo
    bcs :+
    jmp select_next_source_file_loop
:   bne select_next_source_file_pick_candidate
    jmp select_next_source_file_loop
select_next_source_file_pick_candidate:
    lda ACTDBG_RES_actdbg_dbg_candidate_module_lo
    sta ACTDBG_RES_actdbg_lookup_module_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_module_hi
    sta ACTDBG_RES_actdbg_lookup_module_hi
    lda ACTDBG_RES_actdbg_dbg_candidate_file_lo
    sta ACTDBG_RES_actdbg_lookup_file_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_file_hi
    sta ACTDBG_RES_actdbg_lookup_file_hi
    jmp set_cursor_to_first_line_for_lookup_file

select_prev_source_file_cursor:
    lda #$00
    sta ACTDBG_RES_actdbg_lookup_found
    jsr ACTDBG_RES_set_dbg_scan_to_body
select_prev_source_file_loop:
    jsr ACTDBG_RES_copy_dbg_line_to_buffer
    bcc :+
    lda ACTDBG_RES_actdbg_lookup_found
    beq select_prev_source_file_fail
    lda #$01
    sta ACTDBG_RES_actdbg_lookup_line_lo
    lda #$00
    sta ACTDBG_RES_actdbg_lookup_line_hi
    sta ACTDBG_RES_actdbg_lookup_col
    jmp set_cursor_from_lookup
:   lda ACTDBG_RES_line_buffer
    cmp #'f'
    bne select_prev_source_file_loop
    jsr ACTDBG_RES_token_scan_begin
    jsr ACTDBG_RES_token_skip_forward
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_word_tmp
    lda ACTDBG_RES_status_ptr+1
    sta ACTDBG_RES_word_tmp+1
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_word_tmp
    cmp ACTDBG_RES_actdbg_cursor_module_lo
    bne :+
    lda ACTDBG_RES_word_tmp+1
    cmp ACTDBG_RES_actdbg_cursor_module_hi
    bne :+
    lda ACTDBG_RES_status_ptr
    cmp ACTDBG_RES_actdbg_cursor_file_lo
    bne :+
    lda ACTDBG_RES_status_ptr+1
    cmp ACTDBG_RES_actdbg_cursor_file_hi
    bne :+
    lda ACTDBG_RES_actdbg_lookup_found
    beq select_prev_source_file_loop
    lda #$01
    sta ACTDBG_RES_actdbg_lookup_line_lo
    lda #$00
    sta ACTDBG_RES_actdbg_lookup_line_hi
    sta ACTDBG_RES_actdbg_lookup_col
    jmp set_cursor_from_lookup
:   lda ACTDBG_RES_word_tmp
    sta ACTDBG_RES_actdbg_lookup_module_lo
    lda ACTDBG_RES_word_tmp+1
    sta ACTDBG_RES_actdbg_lookup_module_hi
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_lookup_file_lo
    lda ACTDBG_RES_status_ptr+1
    sta ACTDBG_RES_actdbg_lookup_file_hi
    lda #$01
    sta ACTDBG_RES_actdbg_lookup_found
    jmp select_prev_source_file_loop
select_prev_source_file_fail:
    sec
    lda #ACTDBG_OVERLAY_STATUS_FAILED
    rts

candidate_after_cursor:
    lda ACTDBG_RES_actdbg_dbg_candidate_module_hi
    cmp ACTDBG_RES_actdbg_cursor_module_hi
    bcc candidate_after_cursor_fail
    bne candidate_after_cursor_hi_ok
    lda ACTDBG_RES_actdbg_dbg_candidate_module_lo
    cmp ACTDBG_RES_actdbg_cursor_module_lo
    bcc candidate_after_cursor_fail
    bne candidate_after_cursor_hi_ok
    lda ACTDBG_RES_actdbg_dbg_candidate_file_hi
    cmp ACTDBG_RES_actdbg_cursor_file_hi
    bcc candidate_after_cursor_fail
    bne candidate_after_cursor_hi_ok
    lda ACTDBG_RES_actdbg_dbg_candidate_file_lo
    cmp ACTDBG_RES_actdbg_cursor_file_lo
    bcc candidate_after_cursor_fail
    bne candidate_after_cursor_hi_ok
    lda ACTDBG_RES_actdbg_dbg_candidate_line_hi
    cmp ACTDBG_RES_actdbg_cursor_line_hi
    bcc candidate_after_cursor_fail
    bne candidate_after_cursor_hi_ok
    lda ACTDBG_RES_actdbg_dbg_candidate_line_lo
    cmp ACTDBG_RES_actdbg_cursor_line_lo
    bcc candidate_after_cursor_fail
    bne candidate_after_cursor_hi_ok
    lda ACTDBG_RES_actdbg_dbg_candidate_col
    cmp ACTDBG_RES_actdbg_cursor_col
    bcc candidate_after_cursor_fail
    beq candidate_after_cursor_fail
candidate_after_cursor_hi_ok:
    clc
    rts
candidate_after_cursor_fail:
    sec
    rts

capture_first_candidate_if_needed:
    lda ACTDBG_RES_actdbg_lookup_found
    bne capture_first_candidate_done
    lda ACTDBG_RES_actdbg_dbg_candidate_module_lo
    sta ACTDBG_RES_actdbg_lookup_module_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_module_hi
    sta ACTDBG_RES_actdbg_lookup_module_hi
    lda ACTDBG_RES_actdbg_dbg_candidate_file_lo
    sta ACTDBG_RES_actdbg_lookup_file_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_file_hi
    sta ACTDBG_RES_actdbg_lookup_file_hi
    lda ACTDBG_RES_actdbg_dbg_candidate_line_lo
    sta ACTDBG_RES_actdbg_lookup_line_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_line_hi
    sta ACTDBG_RES_actdbg_lookup_line_hi
    lda ACTDBG_RES_actdbg_dbg_candidate_col
    sta ACTDBG_RES_actdbg_lookup_col
    lda #$01
    sta ACTDBG_RES_actdbg_lookup_found
capture_first_candidate_done:
    rts

select_next_proc_cursor:
    lda #$00
    sta ACTDBG_RES_actdbg_lookup_found
    jsr ACTDBG_RES_set_dbg_scan_to_body
select_next_proc_loop:
    jsr ACTDBG_RES_copy_dbg_line_to_buffer
    bcc select_next_proc_have_line
    lda ACTDBG_RES_actdbg_lookup_found
    bne select_next_proc_wrap
    sec
    lda #ACTDBG_OVERLAY_STATUS_FAILED
    rts
select_next_proc_wrap:
    jmp set_cursor_to_first_line_for_lookup_export
select_next_proc_have_line:
    lda ACTDBG_RES_line_buffer
    cmp #'q'
    bne select_next_proc_loop
    jsr ACTDBG_RES_token_scan_begin
    jsr ACTDBG_RES_token_skip_forward
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_dbg_candidate_module_lo
    lda ACTDBG_RES_status_ptr+1
    sta ACTDBG_RES_actdbg_dbg_candidate_module_hi
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_dbg_candidate_export_lo
    lda ACTDBG_RES_status_ptr+1
    sta ACTDBG_RES_actdbg_dbg_candidate_export_hi
    jsr ACTDBG_RES_token_skip_forward
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_dbg_candidate_file_lo
    lda ACTDBG_RES_status_ptr+1
    sta ACTDBG_RES_actdbg_dbg_candidate_file_hi
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_dbg_candidate_line_lo
    lda ACTDBG_RES_status_ptr+1
    sta ACTDBG_RES_actdbg_dbg_candidate_line_hi
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_dbg_candidate_col
    lda ACTDBG_RES_actdbg_lookup_found
    bne :+
    lda ACTDBG_RES_actdbg_dbg_candidate_module_lo
    sta ACTDBG_RES_actdbg_lookup_module_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_module_hi
    sta ACTDBG_RES_actdbg_lookup_module_hi
    lda ACTDBG_RES_actdbg_dbg_candidate_export_lo
    sta ACTDBG_RES_actdbg_lookup_export_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_export_hi
    sta ACTDBG_RES_actdbg_lookup_export_hi
    lda ACTDBG_RES_actdbg_dbg_candidate_file_lo
    sta ACTDBG_RES_actdbg_lookup_file_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_file_hi
    sta ACTDBG_RES_actdbg_lookup_file_hi
    lda ACTDBG_RES_actdbg_dbg_candidate_line_lo
    sta ACTDBG_RES_actdbg_lookup_line_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_line_hi
    sta ACTDBG_RES_actdbg_lookup_line_hi
    lda ACTDBG_RES_actdbg_dbg_candidate_col
    sta ACTDBG_RES_actdbg_lookup_col
    lda #$01
    sta ACTDBG_RES_actdbg_lookup_found
:   jsr candidate_after_cursor
    bcc :+
    jmp select_next_proc_loop
:   lda ACTDBG_RES_actdbg_dbg_candidate_module_lo
    sta ACTDBG_RES_actdbg_lookup_module_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_module_hi
    sta ACTDBG_RES_actdbg_lookup_module_hi
    lda ACTDBG_RES_actdbg_dbg_candidate_export_lo
    sta ACTDBG_RES_actdbg_lookup_export_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_export_hi
    sta ACTDBG_RES_actdbg_lookup_export_hi
    lda ACTDBG_RES_actdbg_dbg_candidate_file_lo
    sta ACTDBG_RES_actdbg_lookup_file_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_file_hi
    sta ACTDBG_RES_actdbg_lookup_file_hi
    lda ACTDBG_RES_actdbg_dbg_candidate_line_lo
    sta ACTDBG_RES_actdbg_lookup_line_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_line_hi
    sta ACTDBG_RES_actdbg_lookup_line_hi
    lda ACTDBG_RES_actdbg_dbg_candidate_col
    sta ACTDBG_RES_actdbg_lookup_col
    jmp set_cursor_to_first_line_for_lookup_export

select_next_line_cursor:
    lda #$00
    sta ACTDBG_RES_actdbg_lookup_found
    jsr ACTDBG_RES_set_dbg_scan_to_body
select_next_line_loop:
    jsr ACTDBG_RES_copy_dbg_line_to_buffer
    bcc :+
    lda ACTDBG_RES_actdbg_lookup_found
    beq select_next_line_fail
    jmp set_cursor_from_lookup
:   lda ACTDBG_RES_line_buffer
    cmp #'l'
    bne select_next_line_loop
    jsr ACTDBG_RES_token_scan_begin
    jsr ACTDBG_RES_token_skip_forward
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_dbg_candidate_module_lo
    lda ACTDBG_RES_status_ptr+1
    sta ACTDBG_RES_actdbg_dbg_candidate_module_hi
    jsr ACTDBG_RES_token_skip_forward
    jsr ACTDBG_RES_token_skip_forward
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_dbg_candidate_file_lo
    lda ACTDBG_RES_status_ptr+1
    sta ACTDBG_RES_actdbg_dbg_candidate_file_hi
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_dbg_candidate_line_lo
    lda ACTDBG_RES_status_ptr+1
    sta ACTDBG_RES_actdbg_dbg_candidate_line_hi
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_dbg_candidate_col
    jsr capture_first_candidate_if_needed
    jsr candidate_after_cursor
    bcs select_next_line_loop
    lda ACTDBG_RES_actdbg_dbg_candidate_module_lo
    sta ACTDBG_RES_actdbg_lookup_module_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_module_hi
    sta ACTDBG_RES_actdbg_lookup_module_hi
    lda ACTDBG_RES_actdbg_dbg_candidate_file_lo
    sta ACTDBG_RES_actdbg_lookup_file_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_file_hi
    sta ACTDBG_RES_actdbg_lookup_file_hi
    lda ACTDBG_RES_actdbg_dbg_candidate_line_lo
    sta ACTDBG_RES_actdbg_lookup_line_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_line_hi
    sta ACTDBG_RES_actdbg_lookup_line_hi
    lda ACTDBG_RES_actdbg_dbg_candidate_col
    sta ACTDBG_RES_actdbg_lookup_col
    jmp set_cursor_from_lookup
select_next_line_fail:
    sec
    lda #ACTDBG_OVERLAY_STATUS_FAILED
    rts

draw_backtrace_details:
    lda #21
    sta ACTDBG_RES_current_row
    lda #$00
    sta ACTDBG_RES_current_col
    lda #<ACTDBG_RES_trace0_prefix
    ldy #>ACTDBG_RES_trace0_prefix
    jsr ACTDBG_RES_draw_const_string_at
    lda #21
    sta ACTDBG_RES_current_row
    lda #$03
    sta ACTDBG_RES_current_col
    lda #<ACTDBG_RES_actdbg_trace_summary0
    ldy #>ACTDBG_RES_actdbg_trace_summary0
    jsr ACTDBG_RES_draw_const_string_at

    lda #22
    sta ACTDBG_RES_current_row
    lda #$00
    sta ACTDBG_RES_current_col
    lda #<ACTDBG_RES_trace1_prefix
    ldy #>ACTDBG_RES_trace1_prefix
    jsr ACTDBG_RES_draw_const_string_at
    lda #22
    sta ACTDBG_RES_current_row
    lda #$03
    sta ACTDBG_RES_current_col
    lda #<ACTDBG_RES_actdbg_trace_summary1
    ldy #>ACTDBG_RES_actdbg_trace_summary1
    jsr ACTDBG_RES_draw_const_string_at

    lda #23
    sta ACTDBG_RES_current_row
    lda #$00
    sta ACTDBG_RES_current_col
    lda #<ACTDBG_RES_trace2_prefix
    ldy #>ACTDBG_RES_trace2_prefix
    jsr ACTDBG_RES_draw_const_string_at
    lda #23
    sta ACTDBG_RES_current_row
    lda #$03
    sta ACTDBG_RES_current_col
    lda #<ACTDBG_RES_actdbg_trace_summary2
    ldy #>ACTDBG_RES_actdbg_trace_summary2
    jmp ACTDBG_RES_draw_const_string_at

draw_breakpoint_list:
    lda #21
    sta ACTDBG_RES_current_row
    lda #$00
    sta ACTDBG_RES_current_col
    lda #<ACTDBG_RES_trace0_prefix
    ldy #>ACTDBG_RES_trace0_prefix
    jsr ACTDBG_RES_draw_const_string_at
    lda #21
    sta ACTDBG_RES_current_row
    lda #$03
    sta ACTDBG_RES_current_col
    lda #<ACTDBG_RES_actdbg_trace_summary0
    ldy #>ACTDBG_RES_actdbg_trace_summary0
    jsr ACTDBG_RES_draw_const_string_at

    lda #22
    sta ACTDBG_RES_current_row
    lda #$00
    sta ACTDBG_RES_current_col
    lda #<ACTDBG_RES_trace1_prefix
    ldy #>ACTDBG_RES_trace1_prefix
    jsr ACTDBG_RES_draw_const_string_at
    lda #22
    sta ACTDBG_RES_current_row
    lda #$03
    sta ACTDBG_RES_current_col
    lda #<ACTDBG_RES_actdbg_trace_summary1
    ldy #>ACTDBG_RES_actdbg_trace_summary1
    jsr ACTDBG_RES_draw_const_string_at

    lda #23
    sta ACTDBG_RES_current_row
    lda #$00
    sta ACTDBG_RES_current_col
    lda #<ACTDBG_RES_trace2_prefix
    ldy #>ACTDBG_RES_trace2_prefix
    jsr ACTDBG_RES_draw_const_string_at
    lda #23
    sta ACTDBG_RES_current_row
    lda #$03
    sta ACTDBG_RES_current_col
    lda #<ACTDBG_RES_actdbg_trace_summary2
    ldy #>ACTDBG_RES_actdbg_trace_summary2
    jmp ACTDBG_RES_draw_const_string_at

toggle_current_line_breakpoint:
    lda ACTDBG_RES_actdbg_cursor_line_lo
    ora ACTDBG_RES_actdbg_cursor_line_hi
    beq toggle_current_line_breakpoint_fail
    jsr find_breakpoint_slot_for_target_line
    bcs toggle_current_line_breakpoint_add
    lda #$00
    sta ACTDBG_RES_actdbg_break_active,x
    clc
    lda #ACTDBG_OVERLAY_STATUS_OK
    rts
toggle_current_line_breakpoint_add:
    jsr lookup_breakpoint_pc_for_target_line
    bcs toggle_current_line_breakpoint_fail
    jsr find_free_breakpoint_slot
    bcs toggle_current_line_breakpoint_fail
    lda #$01
    sta ACTDBG_RES_actdbg_break_active,x
    lda word_tmp
    sta ACTDBG_RES_actdbg_break_pc_lo,x
    lda word_tmp+1
    sta ACTDBG_RES_actdbg_break_pc_hi,x
    lda ACTDBG_RES_actdbg_cursor_module_lo
    sta ACTDBG_RES_actdbg_break_module_lo,x
    lda ACTDBG_RES_actdbg_cursor_module_hi
    sta ACTDBG_RES_actdbg_break_module_hi,x
    lda ACTDBG_RES_actdbg_cursor_file_lo
    sta ACTDBG_RES_actdbg_break_file_lo,x
    lda ACTDBG_RES_actdbg_cursor_file_hi
    sta ACTDBG_RES_actdbg_break_file_hi,x
    lda ACTDBG_RES_actdbg_cursor_line_lo
    sta ACTDBG_RES_actdbg_break_line_lo,x
    lda ACTDBG_RES_actdbg_cursor_line_hi
    sta ACTDBG_RES_actdbg_break_line_hi,x
    clc
    lda #ACTDBG_OVERLAY_STATUS_OK
    rts
toggle_current_line_breakpoint_fail:
    sec
    lda #ACTDBG_OVERLAY_STATUS_FAILED
    rts

find_breakpoint_slot_for_target_line:
    ldx #$00
find_breakpoint_slot_loop:
    cpx #4
    bcs find_breakpoint_slot_fail
    lda ACTDBG_RES_actdbg_break_active,x
    beq find_breakpoint_slot_next
    lda ACTDBG_RES_actdbg_break_module_lo,x
    cmp ACTDBG_RES_actdbg_cursor_module_lo
    bne find_breakpoint_slot_next
    lda ACTDBG_RES_actdbg_break_module_hi,x
    cmp ACTDBG_RES_actdbg_cursor_module_hi
    bne find_breakpoint_slot_next
    lda ACTDBG_RES_actdbg_break_file_lo,x
    cmp ACTDBG_RES_actdbg_cursor_file_lo
    bne find_breakpoint_slot_next
    lda ACTDBG_RES_actdbg_break_file_hi,x
    cmp ACTDBG_RES_actdbg_cursor_file_hi
    bne find_breakpoint_slot_next
    lda ACTDBG_RES_actdbg_break_line_lo,x
    cmp ACTDBG_RES_actdbg_cursor_line_lo
    bne find_breakpoint_slot_next
    lda ACTDBG_RES_actdbg_break_line_hi,x
    cmp ACTDBG_RES_actdbg_cursor_line_hi
    beq find_breakpoint_slot_hit
find_breakpoint_slot_next:
    inx
    jmp find_breakpoint_slot_loop
find_breakpoint_slot_hit:
    clc
    rts
find_breakpoint_slot_fail:
    sec
    rts

find_free_breakpoint_slot:
    ldx #$00
find_free_breakpoint_slot_loop:
    cpx #4
    bcs find_free_breakpoint_slot_fail
    lda ACTDBG_RES_actdbg_break_active,x
    beq find_free_breakpoint_slot_hit
    inx
    jmp find_free_breakpoint_slot_loop
find_free_breakpoint_slot_hit:
    clc
    rts
find_free_breakpoint_slot_fail:
    sec
    rts

lookup_breakpoint_pc_for_target_line:
    lda #$00
    sta ACTDBG_RES_actdbg_break_lookup_found
    jsr ACTDBG_RES_set_dbg_scan_to_body

lookup_breakpoint_pc_loop:
    jsr ACTDBG_RES_copy_dbg_line_to_buffer
    bcc :+
    jmp lookup_breakpoint_pc_done
:   lda ACTDBG_RES_line_buffer
    cmp #'l'
    bne lookup_breakpoint_pc_loop
    jsr ACTDBG_RES_token_scan_begin
    jsr ACTDBG_RES_token_skip_forward
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    cmp ACTDBG_RES_actdbg_cursor_module_lo
    bne lookup_breakpoint_pc_loop
    lda ACTDBG_RES_status_ptr+1
    cmp ACTDBG_RES_actdbg_cursor_module_hi
    bne lookup_breakpoint_pc_loop
    jsr ACTDBG_RES_token_parse_u16
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    sta ACTDBG_RES_actdbg_dbg_candidate_pc_lo
    lda ACTDBG_RES_status_ptr+1
    sta ACTDBG_RES_actdbg_dbg_candidate_pc_hi
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    cmp ACTDBG_RES_actdbg_cursor_file_lo
    bne lookup_breakpoint_pc_loop
    lda ACTDBG_RES_status_ptr+1
    cmp ACTDBG_RES_actdbg_cursor_file_hi
    bne lookup_breakpoint_pc_loop
    jsr ACTDBG_RES_token_parse_u16
    lda ACTDBG_RES_status_ptr
    cmp ACTDBG_RES_actdbg_cursor_line_lo
    bne lookup_breakpoint_pc_loop
    lda ACTDBG_RES_status_ptr+1
    cmp ACTDBG_RES_actdbg_cursor_line_hi
    bne lookup_breakpoint_pc_loop
    lda ACTDBG_RES_actdbg_break_lookup_found
    beq lookup_breakpoint_store_pc
    lda ACTDBG_RES_actdbg_dbg_candidate_pc_hi
    cmp ACTDBG_RES_actdbg_break_lookup_pc_hi
    bcc lookup_breakpoint_store_pc
    bne lookup_breakpoint_pc_loop
    lda ACTDBG_RES_actdbg_dbg_candidate_pc_lo
    cmp ACTDBG_RES_actdbg_break_lookup_pc_lo
    bcs lookup_breakpoint_pc_loop

lookup_breakpoint_store_pc:
    lda #$01
    sta ACTDBG_RES_actdbg_break_lookup_found
    lda ACTDBG_RES_actdbg_dbg_candidate_pc_lo
    sta ACTDBG_RES_actdbg_break_lookup_pc_lo
    lda ACTDBG_RES_actdbg_dbg_candidate_pc_hi
    sta ACTDBG_RES_actdbg_break_lookup_pc_hi
    jmp lookup_breakpoint_pc_loop

lookup_breakpoint_pc_done:
    lda ACTDBG_RES_actdbg_break_lookup_found
    beq lookup_breakpoint_pc_fail
    lda ACTDBG_RES_actdbg_break_lookup_pc_lo
    sta word_tmp
    lda ACTDBG_RES_actdbg_break_lookup_pc_hi
    sta word_tmp+1
    clc
    rts
lookup_breakpoint_pc_fail:
    sec
    rts

rebuild_variable_summaries_for_current_scope:
    ldx #36
rebuild_clear_summaries_loop:
    lda #$00
    sta actdbg_global_summary,x
    sta actdbg_param_summary,x
    sta actdbg_local_summary,x
    dex
    bpl rebuild_clear_summaries_loop
    jsr set_dbg_scan_to_body

rebuild_var_loop:
    jsr copy_dbg_line_to_buffer
    bcc :+
    rts
:   lda line_buffer
    cmp #'v'
    bne rebuild_var_loop
    jsr token_scan_begin
    jsr token_skip_forward
    ldy #$00
    lda (text_ptr),y
    sta actdbg_var_scope
    jsr token_skip_forward
    ldy #$00
    lda (text_ptr),y
    sta actdbg_live_var_type
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    cmp actdbg_target_module_lo
    beq :+
    jmp rebuild_var_loop
:   lda status_ptr+1
    cmp actdbg_target_module_hi
    beq :+
    jmp rebuild_var_loop
:   lda actdbg_var_scope
    cmp #'g'
    beq rebuild_global_var
    jsr token_parse_u16
    lda status_ptr
    cmp actdbg_target_export_lo
    beq :+
    jmp rebuild_var_loop
:   lda status_ptr+1
    cmp actdbg_target_export_hi
    beq :+
    jmp rebuild_var_loop
:   lda actdbg_var_scope
    cmp #'p'
    beq rebuild_param_var
    cmp #'l'
    beq rebuild_local_var
    jmp rebuild_var_loop

rebuild_global_var:
    jsr parse_current_var_summary_fields
    lda #<actdbg_global_summary
    ldy #>actdbg_global_summary
    jsr append_current_live_var_name_and_value_to_summary
    jmp rebuild_var_loop

rebuild_param_var:
    jsr parse_current_var_summary_fields
    lda #<actdbg_param_summary
    ldy #>actdbg_param_summary
    jsr append_current_live_var_name_and_value_to_summary
    jmp rebuild_var_loop

rebuild_local_var:
    jsr parse_current_var_summary_fields
    lda #<actdbg_local_summary
    ldy #>actdbg_local_summary
    jsr append_current_live_var_name_and_value_to_summary
    jmp rebuild_var_loop

rebuild_backtrace_summary:
    lda #$00
    sta actdbg_backtrace_summary
    sta actdbg_trace_summary0
    sta actdbg_trace_summary1
    sta actdbg_trace_summary2
    lda #<actdbg_backtrace_summary
    sta const_ptr
    lda #>actdbg_backtrace_summary
    sta const_ptr+1
    ldx #$00
    lda actdbg_current_pc_lo
    sta word_tmp
    lda actdbg_current_pc_hi
    sta word_tmp+1
    lda #<actdbg_proc_name
    sta line_start_ptr
    lda #>actdbg_proc_name
    sta line_start_ptr+1
    jsr save_summary_cursor
    lda #<actdbg_trace_summary0
    ldy #>actdbg_trace_summary0
    jsr build_named_pc_summary_at_buffer
    jsr restore_summary_cursor
    ldx #$00
    lda actdbg_proc_name
    bne :+
    lda #'?'
    jsr append_summary_char_a
    jmp rebuild_backtrace_summary_callers
:   lda #<actdbg_proc_name
    ldy #>actdbg_proc_name
    jsr append_cstr_to_summary

rebuild_backtrace_summary_callers:
    lda actdbg_native_call_depth
    sta actdbg_backtrace_index
    bne :+
    jmp rebuild_backtrace_summary_done
:   lda #$01
    sta actdbg_backtrace_slot
rebuild_backtrace_summary_prep:
    dec actdbg_backtrace_index
    jsr append_backtrace_separator
    stx actdbg_backtrace_len
    ldx actdbg_backtrace_index
    lda actdbg_native_callstack_lo,x
    sta word_tmp
    sta actdbg_backtrace_pc_lo
    lda actdbg_native_callstack_hi,x
    sta word_tmp+1
    sta actdbg_backtrace_pc_hi
    ldx actdbg_backtrace_len
    jsr save_summary_cursor
    lda #<actdbg_trace_proc_name
    ldy #>actdbg_trace_proc_name
    jsr lookup_proc_name_for_pc_to_buffer
    jsr restore_summary_cursor
    ldx actdbg_backtrace_len
    bcc :+
    jmp rebuild_backtrace_summary_append_pc
:   lda actdbg_trace_proc_name
    bne :+
    jmp rebuild_backtrace_summary_append_pc
:   lda #<actdbg_trace_proc_name
    ldy #>actdbg_trace_proc_name
    jsr append_cstr_to_summary
    lda actdbg_backtrace_slot
    cmp #$03
    bcc :+
    jmp rebuild_backtrace_summary_next
:   lda #<actdbg_trace_proc_name
    sta line_start_ptr
    lda #>actdbg_trace_proc_name
    sta line_start_ptr+1
    lda actdbg_backtrace_pc_lo
    sta word_tmp
    lda actdbg_backtrace_pc_hi
    sta word_tmp+1
    lda actdbg_backtrace_slot
    cmp #$01
    bne :+
    stx actdbg_backtrace_len
    jsr save_summary_cursor
    lda #<actdbg_trace_summary1
    ldy #>actdbg_trace_summary1
    jsr build_named_pc_summary_at_buffer
    jsr restore_summary_cursor
    ldx actdbg_backtrace_len
    jmp rebuild_backtrace_summary_bump_slot
:   stx actdbg_backtrace_len
    jsr save_summary_cursor
    lda #<actdbg_trace_summary2
    ldy #>actdbg_trace_summary2
    jsr build_named_pc_summary_at_buffer
    jsr restore_summary_cursor
    ldx actdbg_backtrace_len
rebuild_backtrace_summary_bump_slot:
    inc actdbg_backtrace_slot
    jmp rebuild_backtrace_summary_next

rebuild_backtrace_summary_append_pc:
    lda #'$'
    jsr append_summary_char_a
    lda word_tmp+1
    jsr append_summary_hex_byte_a
    lda word_tmp
    jsr append_summary_hex_byte_a
    lda actdbg_backtrace_slot
    cmp #$03
    bcs rebuild_backtrace_summary_next
    lda #<actdbg_trace_proc_name
    sta line_start_ptr
    lda #>actdbg_trace_proc_name
    sta line_start_ptr+1
    lda actdbg_backtrace_pc_lo
    sta word_tmp
    lda actdbg_backtrace_pc_hi
    sta word_tmp+1
    lda actdbg_backtrace_slot
    cmp #$01
    bne :+
    stx actdbg_backtrace_len
    jsr save_summary_cursor
    lda #<actdbg_trace_summary1
    ldy #>actdbg_trace_summary1
    jsr build_named_pc_summary_at_buffer
    jsr restore_summary_cursor
    ldx actdbg_backtrace_len
    jmp rebuild_backtrace_summary_bump_slot2
:   stx actdbg_backtrace_len
    jsr save_summary_cursor
    lda #<actdbg_trace_summary2
    ldy #>actdbg_trace_summary2
    jsr build_named_pc_summary_at_buffer
    jsr restore_summary_cursor
    ldx actdbg_backtrace_len
rebuild_backtrace_summary_bump_slot2:
    inc actdbg_backtrace_slot
rebuild_backtrace_summary_next:
    lda actdbg_backtrace_index
    beq rebuild_backtrace_summary_done
    jmp rebuild_backtrace_summary_prep
rebuild_backtrace_summary_done:
    ldy #$00
    lda #$00
    sta (const_ptr),y
    rts

build_named_pc_summary_at_buffer:
    sta const_ptr
    sty const_ptr+1
    ldx #$00
    ldy #$00
    lda (line_start_ptr),y
    bne :+
    lda #'?'
    jsr append_summary_char_a
    jmp build_named_pc_summary_pc
:   lda line_start_ptr
    ldy line_start_ptr+1
    jsr append_cstr_to_summary
build_named_pc_summary_pc:
    lda #' '
    jsr append_summary_char_a
    lda #'$'
    jsr append_summary_char_a
    lda word_tmp+1
    jsr append_summary_hex_byte_a
    lda word_tmp
    jsr append_summary_hex_byte_a
    ldy #$00
    lda #$00
    sta (const_ptr),y
    rts

lookup_proc_name_for_pc_to_buffer:
    sta line_start_ptr
    sty line_start_ptr+1
    lda #$00
    sta actdbg_trace_best_found
    sta actdbg_trace_proc_name
    jsr set_dbg_scan_to_body
lookup_proc_name_for_pc_loop:
    jsr copy_dbg_line_to_buffer
    bcc :+
    jmp lookup_proc_name_for_pc_done
:   lda line_buffer
    cmp #'q'
    bne lookup_proc_name_for_pc_loop
    jsr token_scan_begin
    jsr token_skip_forward
    jsr token_parse_u16
    jsr token_parse_u16
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_dbg_candidate_pc_lo
    lda status_ptr+1
    sta actdbg_dbg_candidate_pc_hi
    jsr token_parse_u16
    jsr token_parse_u16
    jsr token_parse_u16
    lda actdbg_dbg_candidate_pc_hi
    cmp word_tmp+1
    bcc :+
    bne lookup_proc_name_for_pc_loop
    lda actdbg_dbg_candidate_pc_lo
    cmp word_tmp
    bcc :+
    beq :+
    jmp lookup_proc_name_for_pc_loop
:   lda actdbg_trace_best_found
    beq lookup_proc_name_for_pc_store
    lda actdbg_dbg_candidate_pc_hi
    cmp actdbg_trace_best_pc_hi
    bcc lookup_proc_name_for_pc_loop
    bne lookup_proc_name_for_pc_store
    lda actdbg_dbg_candidate_pc_lo
    cmp actdbg_trace_best_pc_lo
    bcc lookup_proc_name_for_pc_loop

lookup_proc_name_for_pc_store:
    lda #$01
    sta actdbg_trace_best_found
    lda actdbg_dbg_candidate_pc_lo
    sta actdbg_trace_best_pc_lo
    lda actdbg_dbg_candidate_pc_hi
    sta actdbg_trace_best_pc_hi
    lda #31
    sta token_copy_limit
    lda line_start_ptr
    ldy line_start_ptr+1
    jsr token_copy_to_buffer
    jmp lookup_proc_name_for_pc_loop

lookup_proc_name_for_pc_done:
    lda actdbg_trace_best_found
    beq :+
    clc
    rts
:   sec
    rts

draw_variable_summaries:
    lda #21
    sta current_row
    lda #$00
    sta current_col
    lda #<ACTDBG_RES_globals_prefix
    ldy #>ACTDBG_RES_globals_prefix
    jsr draw_const_string_at
    lda #21
    sta current_row
    lda #$03
    sta current_col
    lda #<actdbg_global_summary
    ldy #>actdbg_global_summary
    jsr draw_const_string_at

    lda #22
    sta current_row
    lda #$00
    sta current_col
    lda #<ACTDBG_RES_params_prefix
    ldy #>ACTDBG_RES_params_prefix
    jsr draw_const_string_at
    lda #22
    sta current_row
    lda #$03
    sta current_col
    lda #<actdbg_param_summary
    ldy #>actdbg_param_summary
    jsr draw_const_string_at

    lda #23
    sta current_row
    lda #$00
    sta current_col
    lda #<ACTDBG_RES_locals_prefix
    ldy #>ACTDBG_RES_locals_prefix
    jsr draw_const_string_at
    lda #23
    sta current_row
    lda #$03
    sta current_col
    lda #<actdbg_local_summary
    ldy #>actdbg_local_summary
    clc
    jsr draw_const_string_at
    lda #ACTDBG_OVERLAY_STATUS_OK
    rts

actdbg_overlay_end:
