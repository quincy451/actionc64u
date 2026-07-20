.include "udos_services.inc"
.include "actdbg_overlay_abi.inc"
.include "actdbg_overlay_resident.inc"

.export actdbg_overlay_header
.export actdbg_overlay_entry
.export actdbg_overlay_end

SCREEN_COLS = 40
SCREEN_ROWS = 25
SCREEN_RAM = $0400
VIEW_OUTPUT = 1
BREAKPOINT_MAX = 4
MODULE_LIMIT = 31
ACTDBG_PRG_REU_BASE_LO = $00
ACTDBG_PRG_REU_BASE_HI = $00
ACTDBG_PRG_REU_BASE_BANK = $00
ACTDBG_OUTPUT_REU_BASE_BANK = $03


.segment "CODE"

actdbg_overlay_header:
    .byte 'D','G','O','V'
    .byte ACTDBG_OVERLAY_ABI_VERSION
    .word ACTDBG_OVERLAY_EXEC_BASE
    .word actdbg_overlay_entry
    .word actdbg_overlay_end - actdbg_overlay_header
    .word $0000

svc_retptr = ACTDBG_RES_svc_retptr
file_params = ACTDBG_RES_file_params
scan_ptr = ACTDBG_RES_scan_ptr
const_ptr = ACTDBG_RES_const_ptr
base_ptr = ACTDBG_RES_base_ptr
text_ptr = ACTDBG_RES_text_ptr
row_ptr = ACTDBG_RES_row_ptr
line_start_ptr = ACTDBG_RES_line_start_ptr
status_ptr = ACTDBG_RES_status_ptr
word_tmp = ACTDBG_RES_word_tmp
digit_flag = ACTDBG_RES_digit_flag
hex_tmp = ACTDBG_RES_hex_tmp
actdbg_best_proc_found = ACTDBG_RES_actdbg_best_proc_found
actdbg_best_proc_pc_lo = ACTDBG_RES_actdbg_best_proc_pc_lo
actdbg_best_proc_pc_hi = ACTDBG_RES_actdbg_best_proc_pc_hi
actdbg_best_line_found = ACTDBG_RES_actdbg_best_line_found
actdbg_best_line_pc_lo = ACTDBG_RES_actdbg_best_line_pc_lo
actdbg_best_line_pc_hi = ACTDBG_RES_actdbg_best_line_pc_hi
actdbg_dbg_candidate_module_lo = ACTDBG_RES_actdbg_dbg_candidate_module_lo
actdbg_dbg_candidate_module_hi = ACTDBG_RES_actdbg_dbg_candidate_module_hi
actdbg_dbg_candidate_export_lo = ACTDBG_RES_actdbg_dbg_candidate_export_lo
actdbg_dbg_candidate_export_hi = ACTDBG_RES_actdbg_dbg_candidate_export_hi
actdbg_dbg_candidate_pc_lo = ACTDBG_RES_actdbg_dbg_candidate_pc_lo
actdbg_dbg_candidate_pc_hi = ACTDBG_RES_actdbg_dbg_candidate_pc_hi
actdbg_dbg_candidate_file_lo = ACTDBG_RES_actdbg_dbg_candidate_file_lo
actdbg_dbg_candidate_file_hi = ACTDBG_RES_actdbg_dbg_candidate_file_hi
actdbg_dbg_candidate_line_lo = ACTDBG_RES_actdbg_dbg_candidate_line_lo
actdbg_dbg_candidate_line_hi = ACTDBG_RES_actdbg_dbg_candidate_line_hi
actdbg_dbg_candidate_col = ACTDBG_RES_actdbg_dbg_candidate_col
actdbg_target_module_lo = ACTDBG_RES_actdbg_target_module_lo
actdbg_target_module_hi = ACTDBG_RES_actdbg_target_module_hi
actdbg_target_export_lo = ACTDBG_RES_actdbg_target_export_lo
actdbg_target_export_hi = ACTDBG_RES_actdbg_target_export_hi
actdbg_target_file_lo = ACTDBG_RES_actdbg_target_file_lo
actdbg_target_file_hi = ACTDBG_RES_actdbg_target_file_hi
actdbg_target_line_lo = ACTDBG_RES_actdbg_target_line_lo
actdbg_target_line_hi = ACTDBG_RES_actdbg_target_line_hi
actdbg_target_col = ACTDBG_RES_actdbg_target_col
actdbg_cursor_module_lo = ACTDBG_RES_actdbg_cursor_module_lo
actdbg_cursor_module_hi = ACTDBG_RES_actdbg_cursor_module_hi
actdbg_cursor_file_lo = ACTDBG_RES_actdbg_cursor_file_lo
actdbg_cursor_file_hi = ACTDBG_RES_actdbg_cursor_file_hi
actdbg_cursor_line_lo = ACTDBG_RES_actdbg_cursor_line_lo
actdbg_cursor_line_hi = ACTDBG_RES_actdbg_cursor_line_hi
actdbg_cursor_col = ACTDBG_RES_actdbg_cursor_col
actdbg_source_col_offset = ACTDBG_RES_actdbg_source_col_offset
actdbg_break_lookup_found = ACTDBG_RES_actdbg_break_lookup_found
actdbg_break_lookup_pc_lo = ACTDBG_RES_actdbg_break_lookup_pc_lo
actdbg_break_lookup_pc_hi = ACTDBG_RES_actdbg_break_lookup_pc_hi
actdbg_break_active = ACTDBG_RES_actdbg_break_active
actdbg_break_pc_lo = ACTDBG_RES_actdbg_break_pc_lo
actdbg_break_pc_hi = ACTDBG_RES_actdbg_break_pc_hi
actdbg_proc_name = ACTDBG_RES_actdbg_proc_name
token_copy_limit = ACTDBG_RES_token_copy_limit
actdbg_break_hit = ACTDBG_RES_actdbg_break_hit
actdbg_view_mode = ACTDBG_RES_actdbg_view_mode
actdbg_prg_header = ACTDBG_RES_actdbg_prg_header
actdbg_native_scan_lo = ACTDBG_RES_actdbg_native_scan_lo
actdbg_native_scan_hi = ACTDBG_RES_actdbg_native_scan_hi
actdbg_current_pc_lo = ACTDBG_RES_actdbg_current_pc_lo
actdbg_current_pc_hi = ACTDBG_RES_actdbg_current_pc_hi
actdbg_native_done = ACTDBG_RES_actdbg_native_done
actdbg_native_failed = ACTDBG_RES_actdbg_native_failed
actdbg_native_sp = ACTDBG_RES_actdbg_native_sp
actdbg_native_call_depth = ACTDBG_RES_actdbg_native_call_depth
actdbg_native_callstack_lo = ACTDBG_RES_actdbg_native_callstack_lo
actdbg_native_callstack_hi = ACTDBG_RES_actdbg_native_callstack_hi
actdbg_native_a = ACTDBG_RES_actdbg_native_a
actdbg_native_x = ACTDBG_RES_actdbg_native_x
actdbg_native_y = ACTDBG_RES_actdbg_native_y
actdbg_native_p = ACTDBG_RES_actdbg_native_p
actdbg_native_target_valid = ACTDBG_RES_actdbg_native_target_valid
actdbg_output_row = ACTDBG_RES_actdbg_output_row
actdbg_output_col = ACTDBG_RES_actdbg_output_col
actdbg_room_check_lo = ACTDBG_RES_actdbg_room_check_lo
actdbg_room_check_hi = ACTDBG_RES_actdbg_room_check_hi
actdbg_prg_stage_len_lo = ACTDBG_RES_actdbg_prg_stage_len_lo
actdbg_prg_stage_len_hi = ACTDBG_RES_actdbg_prg_stage_len_hi
actdbg_prg_stage_len_bank = ACTDBG_RES_actdbg_prg_stage_len_bank
actdbg_output_row_buffer = ACTDBG_RES_actdbg_output_row_buffer
line_buffer = ACTDBG_RES_line_buffer

set_dbg_scan_to_body = ACTDBG_RES_set_dbg_scan_to_body
copy_dbg_line_to_buffer = ACTDBG_RES_copy_dbg_line_to_buffer
token_scan_begin = ACTDBG_RES_token_scan_begin
token_skip_forward = ACTDBG_RES_token_skip_forward
token_parse_u16 = ACTDBG_RES_token_parse_u16
token_copy_to_buffer = ACTDBG_RES_token_copy_to_buffer
ascii_to_screen = ACTDBG_RES_ascii_to_screen
load_output_row_buffer_from_reu_row_a = ACTDBG_RES_load_output_row_buffer_from_reu_row_a
store_output_row_buffer_to_reu_row_a = ACTDBG_RES_store_output_row_buffer_to_reu_row_a
show_output_screen = ACTDBG_RES_show_output_screen

actdbg_overlay_entry:
    lda ACTDBG_RES_actdbg_overlay_requested_cmd
    cmp #ACTDBG_OVERLAY_CMD_EXEC_INIT_RUNTIME
    bne :+
    jmp init_debug_runtime
:   cmp #ACTDBG_OVERLAY_CMD_EXEC_LOOKUP_LOCATION
    bne :+
    jmp lookup_dbg_location_for_current_pc
:   cmp #ACTDBG_OVERLAY_CMD_EXEC_STEP
    bne :+
    jmp debug_step_instruction
:   cmp #ACTDBG_OVERLAY_CMD_EXEC_CONTINUE
    bne :+
    jmp debug_continue_execution
:   cmp #ACTDBG_OVERLAY_CMD_EXEC_STEP_OVER
    bne :+
    jmp debug_step_over_execution
:   cmp #ACTDBG_OVERLAY_CMD_EXEC_STEP_OUT
    bne :+
    jmp debug_step_out_execution
:   sec
    lda #ACTDBG_OVERLAY_STATUS_FAILED
    rts

init_debug_runtime:
    lda actdbg_current_pc_lo
    ora actdbg_current_pc_hi
    beq init_debug_runtime_fail
    lda actdbg_current_pc_lo
    sta actdbg_native_scan_lo
    lda actdbg_current_pc_hi
    sta actdbg_native_scan_hi
    lda #$00
    sta actdbg_native_done
    sta actdbg_native_failed
    sta actdbg_native_target_valid
    sta actdbg_native_a
    sta actdbg_native_x
    sta actdbg_native_y
    sta actdbg_native_call_depth
    lda #$20
    sta actdbg_native_p
    lda #$FD
    sta actdbg_native_sp
    clc
    rts
init_debug_runtime_fail:
    sec
    rts
lookup_dbg_location_for_current_pc:
    lda #$00
    sta actdbg_best_proc_found
    sta actdbg_best_line_found
    jsr set_dbg_scan_to_body

lookup_dbg_proc_loop:
    jsr copy_dbg_line_to_buffer
    bcc :+
    jmp lookup_dbg_proc_done
:   lda line_buffer
    cmp #'q'
    bne lookup_dbg_proc_loop
    jsr token_scan_begin
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_dbg_candidate_module_lo
    lda status_ptr+1
    sta actdbg_dbg_candidate_module_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_dbg_candidate_export_lo
    lda status_ptr+1
    sta actdbg_dbg_candidate_export_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_dbg_candidate_pc_lo
    lda status_ptr+1
    sta actdbg_dbg_candidate_pc_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_dbg_candidate_file_lo
    lda status_ptr+1
    sta actdbg_dbg_candidate_file_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_dbg_candidate_line_lo
    lda status_ptr+1
    sta actdbg_dbg_candidate_line_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_dbg_candidate_col
    lda actdbg_dbg_candidate_pc_hi
    cmp actdbg_current_pc_hi
    bcc :+
    bne lookup_dbg_proc_loop
    lda actdbg_dbg_candidate_pc_lo
    cmp actdbg_current_pc_lo
    bcc :+
    beq :+
    jmp lookup_dbg_proc_loop
:   lda actdbg_best_proc_found
    beq lookup_dbg_store_proc
    lda actdbg_dbg_candidate_pc_hi
    cmp actdbg_best_proc_pc_hi
    bcs :+
    jmp lookup_dbg_proc_loop
:
    bne lookup_dbg_store_proc
    lda actdbg_dbg_candidate_pc_lo
    cmp actdbg_best_proc_pc_lo
    bcs :+
    jmp lookup_dbg_proc_loop
:

lookup_dbg_store_proc:
    lda #$01
    sta actdbg_best_proc_found
    lda actdbg_dbg_candidate_module_lo
    sta actdbg_target_module_lo
    lda actdbg_dbg_candidate_module_hi
    sta actdbg_target_module_hi
    lda actdbg_dbg_candidate_export_lo
    sta actdbg_target_export_lo
    lda actdbg_dbg_candidate_export_hi
    sta actdbg_target_export_hi
    lda actdbg_dbg_candidate_file_lo
    sta actdbg_target_file_lo
    lda actdbg_dbg_candidate_file_hi
    sta actdbg_target_file_hi
    lda actdbg_dbg_candidate_line_lo
    sta actdbg_target_line_lo
    lda actdbg_dbg_candidate_line_hi
    sta actdbg_target_line_hi
    lda actdbg_dbg_candidate_col
    sta actdbg_target_col
    lda actdbg_dbg_candidate_pc_lo
    sta actdbg_best_proc_pc_lo
    lda actdbg_dbg_candidate_pc_hi
    sta actdbg_best_proc_pc_hi
    lda #MODULE_LIMIT
    sta token_copy_limit
    lda #<actdbg_proc_name
    ldy #>actdbg_proc_name
    jsr token_copy_to_buffer
    jmp lookup_dbg_proc_loop

lookup_dbg_proc_done:
    lda actdbg_best_proc_found
    bne :+
    sec
    rts
:   jsr set_dbg_scan_to_body

lookup_dbg_line_loop:
    jsr copy_dbg_line_to_buffer
    bcc :+
    jmp lookup_dbg_line_done
:   lda line_buffer
    cmp #'l'
    bne lookup_dbg_line_loop
    jsr token_scan_begin
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    cmp actdbg_target_module_lo
    beq :+
    jmp lookup_dbg_line_loop
:   lda status_ptr+1
    cmp actdbg_target_module_hi
    beq :+
    jmp lookup_dbg_line_loop
:   jsr token_parse_u16
    lda status_ptr
    cmp actdbg_target_export_lo
    beq :+
    jmp lookup_dbg_line_loop
:   lda status_ptr+1
    cmp actdbg_target_export_hi
    beq :+
    jmp lookup_dbg_line_loop
:   jsr token_parse_u16
    lda status_ptr
    sta actdbg_dbg_candidate_pc_lo
    lda status_ptr+1
    sta actdbg_dbg_candidate_pc_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_dbg_candidate_file_lo
    lda status_ptr+1
    sta actdbg_dbg_candidate_file_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_dbg_candidate_line_lo
    lda status_ptr+1
    sta actdbg_dbg_candidate_line_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_dbg_candidate_col
    lda actdbg_dbg_candidate_pc_hi
    cmp actdbg_current_pc_hi
    bcc :+
    bne lookup_dbg_line_loop
    lda actdbg_dbg_candidate_pc_lo
    cmp actdbg_current_pc_lo
    bcc :+
    beq :+
    jmp lookup_dbg_line_loop
:   lda actdbg_best_line_found
    beq lookup_dbg_store_line
    lda actdbg_dbg_candidate_pc_hi
    cmp actdbg_best_line_pc_hi
    bcs :+
    jmp lookup_dbg_line_loop
:
    bne lookup_dbg_store_line
    lda actdbg_dbg_candidate_pc_lo
    cmp actdbg_best_line_pc_lo
    bcs :+
    jmp lookup_dbg_line_loop
:

lookup_dbg_store_line:
    lda #$01
    sta actdbg_best_line_found
    lda actdbg_dbg_candidate_file_lo
    sta actdbg_target_file_lo
    lda actdbg_dbg_candidate_file_hi
    sta actdbg_target_file_hi
    lda actdbg_dbg_candidate_line_lo
    sta actdbg_target_line_lo
    lda actdbg_dbg_candidate_line_hi
    sta actdbg_target_line_hi
    lda actdbg_dbg_candidate_col
    sta actdbg_target_col
    lda actdbg_dbg_candidate_pc_lo
    sta actdbg_best_line_pc_lo
    lda actdbg_dbg_candidate_pc_hi
    sta actdbg_best_line_pc_hi
    jmp lookup_dbg_line_loop

lookup_dbg_line_done:
    clc
    rts
.include "actdbg_native_exec.inc"
actdbg_overlay_end:
