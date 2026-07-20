.include "udos_services.inc"
.include "actdbg_overlay_abi.inc"

.ifndef ACTDBG_KEEP_OPTIONAL_UI_RESIDENT_FALLBACK
ACTDBG_KEEP_OPTIONAL_UI_RESIDENT_FALLBACK = 0
.endif

.ifndef ACTDBG_KEEP_EXEC_RESIDENT_FALLBACK
ACTDBG_KEEP_EXEC_RESIDENT_FALLBACK = 0
.endif

.export start
.export actdbg_test_key_count
.export actdbg_test_key_index
.export actdbg_test_keys
.export actdbg_test_mode
.export actdbg_test_key0
.export actdbg_test_key1
.export actdbg_test_key2
.export actdbg_test_key3
.export actdbg_test_key4
.export actdbg_test_key5
.export actdbg_test_key6
.export actdbg_test_key7
.export actdbg_view_mode
.export actdbg_target_line_lo
.export actdbg_target_line_hi
.export actdbg_target_col
.export actdbg_source_path
.export actdbg_dbg_path
.export actdbg_prg_path
.export actdbg_module_name
.export actdbg_debugger_screen
.export actdbg_output_screen
.export actdbg_native_done
.export actdbg_current_pc_lo
.export actdbg_current_pc_hi

SCNKEY = $FF9F
GETIN = $FFE4
CHROUT = $FFD2

KEY_F3 = $86
KEY_F5 = $87
KEY_F7 = $88
KEY_F4 = $8A
KEY_F6 = $8B
KEY_RUNSTOP = $03
KEY_TEST_EXIT = $FF
KEY_B = $42
KEY_b = $62
KEY_B_PETSCII = $C2
KEY_T = $54
KEY_t = $74
KEY_T_PETSCII = $D4
KEY_Q = $51
KEY_q = $71
KEY_Q_PETSCII = $D1
KEY_C = $43
KEY_E = $45
KEY_L = $4C
KEY_M = $4D
KEY_N = $4E
KEY_COMMA = $2C
KEY_PERIOD = $2E
KEY_CLRHOME = $93
KEY_DOWN = $11
KEY_RIGHT = $1D
KEY_UP = $91
KEY_LEFT = $9D

SCREEN_RAM = $0400
SCREEN_COLS = 40
SCREEN_ROWS = 25
SOURCE_ROWS = 18
SOURCE_ROW_FIRST = 2
BACKTRACE_ROW = 20
GLOBAL_ROW = 21
PARAM_ROW = 22
LOCAL_ROW = 23
SUMMARY_LIMIT = 36

PRG_HEADER_LIMIT = 16
ACTDBG_FILE_WINDOW_LIMIT = 255

ACTDBG_PRG_REU_BASE_LO = $00
ACTDBG_PRG_REU_BASE_HI = $00
ACTDBG_PRG_REU_BASE_BANK = $00
ACTDBG_DBG_REU_BASE_LO = $00
ACTDBG_DBG_REU_BASE_HI = $00
ACTDBG_DBG_REU_BASE_BANK = $01
ACTDBG_SOURCE_REU_BASE_LO = $00
ACTDBG_SOURCE_REU_BASE_HI = $00
ACTDBG_SOURCE_REU_BASE_BANK = $02
ACTDBG_OUTPUT_REU_BASE_LO = $00
ACTDBG_OUTPUT_REU_BASE_HI = $00
ACTDBG_OUTPUT_REU_BASE_BANK = $03
ACTDBG_TARGET_REU_BASE_BANK = $06

ACTDBG_FILE_KIND_NONE = 0
ACTDBG_FILE_KIND_DBG = 1
ACTDBG_FILE_KIND_SOURCE = 2

VIEW_SOURCE = 0
VIEW_OUTPUT = 1

LINE_BUFFER_LIMIT = 159
PATH_LIMIT = 127
MODULE_LIMIT = 31
TEST_KEY_LIMIT = 8
NATIVE_CALLSTACK_MAX = 16
BREAKPOINT_MAX = 4

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
file_params:
    .res 9
src_ptr:
    .res 2
scan_ptr:
    .res 2
const_ptr:
    .res 2
base_ptr:
    .res 2
text_ptr:
    .res 2
row_ptr:
    .res 2
line_start_ptr:
    .res 2
line_work_ptr:
    .res 2
line_length_ptr:
    .res 2
status_ptr:
    .res 2

.code

start:
    jsr clear_state
    ldx #svc_retptr
    jsr actdbg_svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    bne have_args
    lda #<msg_usage
    ldy #>msg_usage
    jmp fail_with_ptr

have_args:
    ldx #svc_retptr
    jsr actdbg_svc_program_get_cmdline_ptr
    lda svc_retptr
    sta src_ptr
    lda svc_retptr+1
    sta src_ptr+1
    jsr copy_first_arg
    lda arg_buffer
    bne have_arg_text
    lda #<msg_usage
    ldy #>msg_usage
    jmp fail_with_ptr

have_arg_text:
    jsr build_launch_paths
    jsr derive_module_name_fallback
    jsr load_prg_header
    jsr load_dbg_sidecar
    jsr parse_dbg_records
    jsr sync_cursor_to_target_location
    jsr ensure_source_file_loaded_for_cursor
    jsr init_output_screen
    jsr init_debug_runtime
    bcc :+
    lda #<msg_bad_prg
    ldy #>msg_bad_prg
    jmp fail_with_ptr
:   jsr update_debug_location_from_current_pc
    jsr render_source_screen
    jsr show_source_screen

input_loop:
    jsr read_input_key
    jsr normalize_input_key
    cmp #$00
    beq input_loop
    cmp #KEY_UP
    bne :+
    jmp browse_source_up
:   cmp #KEY_DOWN
    bne :+
    jmp browse_source_down
:   cmp #KEY_LEFT
    bne :+
    jmp browse_source_left
:   cmp #KEY_RIGHT
    bne :+
    jmp browse_source_right
:   cmp #KEY_E
    bne :+
    jmp edit_source_location
:   cmp #KEY_B
    bne :+
    jmp toggle_breakpoint
:   cmp #KEY_C
    bne :+
    jmp clear_all_breakpoints
:   cmp #KEY_L
    bne :+
    jmp toggle_breakpoint_list
:   cmp #KEY_M
    bne :+
    jmp jump_next_proc
:   cmp #KEY_N
    bne :+
    jmp jump_next_line
:   cmp #KEY_COMMA
    bne :+
    jmp jump_prev_source_file
:   cmp #KEY_PERIOD
    bne :+
    jmp jump_next_source_file
:   cmp #KEY_b
    bne :+
    jmp toggle_breakpoint
:   cmp #KEY_B_PETSCII
    bne :+
    jmp toggle_breakpoint
:   cmp #KEY_T
    bne :+
    jmp toggle_trace_detail
:   cmp #KEY_t
    bne :+
    jmp toggle_trace_detail
:   cmp #KEY_T_PETSCII
    bne :+
    jmp toggle_trace_detail
:   cmp #KEY_F3
    bne :+
    jmp step_debugger
:
    cmp #KEY_F4
    bne :+
    jmp step_over_debugger
:
    cmp #KEY_F5
    bne :+
    jmp continue_debugger
:
    cmp #KEY_F6
    bne :+
    jmp step_out_debugger
:
    cmp #KEY_F7
    beq toggle_view
    cmp #KEY_RUNSTOP
    beq force_source_view
    cmp #KEY_TEST_EXIT
    bne :+
    jmp exit_ok
:
    cmp #KEY_Q
    bne :+
    jmp exit_ok
:
    cmp #KEY_q
    bne :+
    jmp exit_ok
:
    cmp #KEY_Q_PETSCII
    bne :+
    jmp exit_ok
:
    jmp input_loop

toggle_view:
    lda actdbg_view_mode
    beq switch_to_output
    jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

switch_to_output:
    jsr show_output_screen
    jmp input_loop

force_source_view:
    jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

browse_source_up:
    jsr move_source_cursor_up
    bcc :+
    jmp input_loop
:
    jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

browse_source_down:
    jsr move_source_cursor_down
    bcc :+
    jmp input_loop
:
    jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

browse_source_left:
    lda actdbg_source_col_offset
    bne :+
    jmp input_loop
:
    dec actdbg_source_col_offset
    jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

browse_source_right:
    jsr can_scroll_source_right
    bcc :+
    jmp input_loop
:
    inc actdbg_source_col_offset
    jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

clear_all_breakpoints:
    jsr clear_breakpoint_slots
    jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

toggle_breakpoint_list:
    lda actdbg_break_list_view
    eor #$01
    sta actdbg_break_list_view
    lda #$00
    sta actdbg_detail_view
    jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

jump_next_proc:
.if ACTDBG_KEEP_OPTIONAL_UI_RESIDENT_FALLBACK
    jsr select_next_proc_cursor
.else
    lda #ACTDBG_OVERLAY_CMD_NEXT_PROC
    jsr actdbg_overlay_run_command
.endif
    bcc :+
    jmp input_loop
:   jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

jump_next_line:
.if ACTDBG_KEEP_OPTIONAL_UI_RESIDENT_FALLBACK
    jsr select_next_line_cursor
.else
    lda #ACTDBG_OVERLAY_CMD_NEXT_LINE
    jsr actdbg_overlay_run_command
.endif
    bcc :+
    jmp input_loop
:   jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

jump_prev_source_file:
.if ACTDBG_KEEP_OPTIONAL_UI_RESIDENT_FALLBACK
    jsr select_prev_source_file_cursor
.else
    lda #ACTDBG_OVERLAY_CMD_PREV_SOURCE_FILE
    jsr actdbg_overlay_run_command
.endif
    bcc :+
    jmp input_loop
:   jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

jump_next_source_file:
.if ACTDBG_KEEP_OPTIONAL_UI_RESIDENT_FALLBACK
    jsr select_next_source_file_cursor
.else
    lda #ACTDBG_OVERLAY_CMD_NEXT_SOURCE_FILE
    jsr actdbg_overlay_run_command
.endif
    bcc :+
    jmp input_loop
:   jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

toggle_breakpoint:
.if ACTDBG_KEEP_OPTIONAL_UI_RESIDENT_FALLBACK
    jsr toggle_current_line_breakpoint
.else
    lda #ACTDBG_OVERLAY_CMD_TOGGLE_BREAKPOINT
    jsr actdbg_overlay_run_command
.endif
    jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

toggle_trace_detail:
    lda actdbg_detail_view
    eor #$01
    sta actdbg_detail_view
    lda #$00
    sta actdbg_break_list_view
    lda actdbg_view_mode
    beq :+
    jmp input_loop
:
    jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

step_debugger:
    jsr debug_step_instruction
    bcc :+
    jmp input_loop
:   jsr update_debug_location_from_current_pc
    lda actdbg_view_mode
    beq :+
    jmp input_loop
:
    jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

step_over_debugger:
    jsr debug_step_over_execution
    bcc :+
    jmp input_loop
:   jsr update_debug_location_from_current_pc
    lda actdbg_view_mode
    beq :+
    jmp input_loop
:
    jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

continue_debugger:
    jsr debug_continue_execution
    bcc :+
    jmp input_loop
:   jsr update_debug_location_from_current_pc
    lda actdbg_break_hit
    beq :+
    jsr render_source_screen
    jsr show_source_screen
    jmp input_loop
:
    lda actdbg_view_mode
    bne :+
    jsr render_source_screen
    jsr show_source_screen
:   jmp input_loop

step_out_debugger:
    jsr debug_step_out_execution
    bcc :+
    jmp input_loop
:   jsr update_debug_location_from_current_pc
    lda actdbg_view_mode
    beq :+
    jmp input_loop
:
    jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

edit_source_location:
    lda #$00
    sta actdbg_chain_failed
    jsr build_edit_location_command
    bcs edit_source_location_fail
    lda #<actdbg_chain_command
    sta svc_retptr
    lda #>actdbg_chain_command
    sta svc_retptr+1
    jsr actdbg_svc_program_chain_sc0
    bcs edit_source_location_fail
    jmp exit_ok
edit_source_location_fail:
    lda #$01
    sta actdbg_chain_failed
    jsr render_source_screen
    jsr show_source_screen
    jmp input_loop

build_edit_location_command:
    lda actdbg_source_path
    bne :+
    jmp build_edit_location_fail
:
    lda actdbg_cursor_line_lo
    ora actdbg_cursor_line_hi
    bne :+
    jmp build_edit_location_fail
:
    lda #$00
    sta actdbg_chain_len
    ldx #$00
build_edit_location_prefix:
    lda edit_command_prefix,x
    beq build_edit_location_path_begin
    jsr append_edit_command_char
    bcc :+
    jmp build_edit_location_fail
:
    inx
    bne build_edit_location_prefix
build_edit_location_path_begin:
    ldx #$00
build_edit_location_path:
    lda actdbg_source_path,x
    beq build_edit_location_separator
    jsr append_edit_command_char
    bcc :+
    jmp build_edit_location_fail
:
    inx
    cpx #PATH_LIMIT
    bcc build_edit_location_path
    jmp build_edit_location_fail
build_edit_location_separator:
    lda #':'
    jsr append_edit_command_char
    bcs build_edit_location_fail
    lda actdbg_cursor_line_lo
    sta word_tmp
    lda actdbg_cursor_line_hi
    sta word_tmp+1
    lda #$00
    sta digit_flag
    ldx #$00
build_edit_location_decimal_loop:
    cpx #$04
    beq build_edit_location_decimal_ones
    lda #$00
    sta hex_tmp
build_edit_location_decimal_subtract:
    lda word_tmp+1
    cmp decimal_divisors_hi,x
    bcc build_edit_location_decimal_digit
    bne :+
    lda word_tmp
    cmp decimal_divisors_lo,x
    bcc build_edit_location_decimal_digit
:
    sec
    lda word_tmp
    sbc decimal_divisors_lo,x
    sta word_tmp
    lda word_tmp+1
    sbc decimal_divisors_hi,x
    sta word_tmp+1
    inc hex_tmp
    bne build_edit_location_decimal_subtract
build_edit_location_decimal_digit:
    lda digit_flag
    bne build_edit_location_decimal_emit
    lda hex_tmp
    beq build_edit_location_decimal_next
build_edit_location_decimal_emit:
    lda hex_tmp
    clc
    adc #'0'
    jsr append_edit_command_char
    bcs build_edit_location_fail
    lda #$01
    sta digit_flag
build_edit_location_decimal_next:
    inx
    bne build_edit_location_decimal_loop
build_edit_location_decimal_ones:
    lda word_tmp
    clc
    adc #'0'
    jsr append_edit_command_char
    bcs build_edit_location_fail
    ldy actdbg_chain_len
    lda #$00
    sta actdbg_chain_command,y
    clc
    rts
build_edit_location_fail:
    sec
    rts

append_edit_command_char:
    ldy actdbg_chain_len
    cpy #31
    bcs append_edit_command_char_fail
    sta actdbg_chain_command,y
    iny
    sty actdbg_chain_len
    clc
    rts
append_edit_command_char_fail:
    sec
    rts

exit_ok:
    lda actdbg_test_mode
    bne :+
    lda #KEY_CLRHOME
    jsr CHROUT
:
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

fail_with_ptr:
    jsr print_ptr
    jsr actdbg_svc_console_newline
    lda #$01
    sta svc_retptr
    lda #$00
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

clear_state:
    lda #$00
    sta actdbg_view_mode
    sta actdbg_target_line_lo
    sta actdbg_target_line_hi
    sta actdbg_target_col
    sta actdbg_have_line_record
    sta actdbg_target_module_lo
    sta actdbg_target_module_hi
    sta actdbg_target_export_lo
    sta actdbg_target_export_hi
    sta actdbg_cursor_module_lo
    sta actdbg_cursor_module_hi
    sta actdbg_cursor_file_lo
    sta actdbg_cursor_file_hi
    sta actdbg_cursor_line_lo
    sta actdbg_cursor_line_hi
    sta actdbg_cursor_col
    sta actdbg_source_col_offset
    sta actdbg_loaded_source_valid
    sta actdbg_loaded_source_module_lo
    sta actdbg_loaded_source_module_hi
    sta actdbg_loaded_source_file_lo
    sta actdbg_loaded_source_file_hi
    sta actdbg_lookup_export_lo
    sta actdbg_lookup_export_hi
    sta actdbg_lookup_line_lo
    sta actdbg_lookup_line_hi
    sta actdbg_lookup_col
    sta actdbg_lookup_found
    sta actdbg_nav_found_after
    sta actdbg_break_list_view
    sta actdbg_backtrace_summary
    sta actdbg_global_summary
    sta actdbg_param_summary
    sta actdbg_local_summary
    sta actdbg_overlay_requested_kind
    sta actdbg_overlay_loaded_kind
    sta actdbg_chain_failed
    sta actdbg_chain_len
    sta actdbg_native_done
    sta actdbg_native_failed
    sta actdbg_native_a
    sta actdbg_native_x
    sta actdbg_native_y
    sta actdbg_native_target_valid
    sta actdbg_native_call_depth
    sta actdbg_current_pc_lo
    sta actdbg_current_pc_hi
    sta actdbg_prg_stage_len_lo
    sta actdbg_prg_stage_len_hi
    sta actdbg_prg_stage_len_bank
    sta actdbg_dbg_stage_len_lo
    sta actdbg_dbg_stage_len_hi
    sta actdbg_dbg_stage_len_bank
    sta actdbg_source_stage_len_lo
    sta actdbg_source_stage_len_hi
    sta actdbg_source_stage_len_bank
    sta actdbg_active_file_kind
    sta actdbg_file_window_kind
    sta actdbg_file_window_start_lo
    sta actdbg_file_window_start_hi
    sta actdbg_file_window_end_lo
    sta actdbg_file_window_end_hi
    sta actdbg_native_scan_lo
    sta actdbg_native_scan_hi
    sta actdbg_output_row
    sta actdbg_output_col
    sta arg_buffer
    sta actdbg_prg_path
    sta actdbg_dbg_path
    sta source_rel_path
    sta actdbg_source_path
    sta actdbg_project_root
    sta actdbg_module_name
    sta actdbg_proc_name
    sta actdbg_trace_proc_name
    sta actdbg_break_hit
    sta actdbg_break_lookup_found
    sta actdbg_detail_view
    lda #$20
    sta actdbg_native_p
    lda #$FD
    sta actdbg_native_sp
    lda #$00
    sta actdbg_test_key_index
    ldx #BREAKPOINT_MAX-1
clear_breakpoint_slots_loop:
    lda #$00
    sta actdbg_break_active,x
    sta actdbg_break_pc_lo,x
    sta actdbg_break_pc_hi,x
    sta actdbg_break_module_lo,x
    sta actdbg_break_module_hi,x
    sta actdbg_break_file_lo,x
    sta actdbg_break_file_hi,x
    sta actdbg_break_line_lo,x
    sta actdbg_break_line_hi,x
    dex
    bpl clear_breakpoint_slots_loop
    lda #$00
    lda actdbg_test_mode
    bne :+
    sta actdbg_test_key_count
:
    rts

copy_first_arg:
    ldy #$00
copy_first_arg_skip_spaces:
    lda (src_ptr),y
    cmp #' '
    bne copy_first_arg_begin
    iny
    bne copy_first_arg_skip_spaces
copy_first_arg_begin:
    ldx #$00
copy_first_arg_loop:
    lda (src_ptr),y
    beq copy_first_arg_done
    cmp #' '
    beq copy_first_arg_done
    cpx #PATH_LIMIT
    bcs copy_first_arg_done
    jsr actdbg_screen_code_to_ascii
    sta arg_buffer,x
    inx
    iny
    bne copy_first_arg_loop
copy_first_arg_done:
    lda #$00
    sta arg_buffer,x
    rts

actdbg_screen_code_to_ascii:
    cmp #$01
    bcc actdbg_screen_code_to_ascii_done
    cmp #$1B
    bcs actdbg_screen_code_to_ascii_done
    clc
    adc #$40
actdbg_screen_code_to_ascii_done:
    rts

build_launch_paths:
    jsr arg_has_dot
    bcs build_exact_paths
    lda #<actdbg_prg_path
    sta text_ptr
    lda #>actdbg_prg_path
    sta text_ptr+1
    lda #<prefix_bin
    ldy #>prefix_bin
    jsr copy_const_to_ptr
    lda #<arg_buffer
    ldy #>arg_buffer
    jsr append_const_to_ptr
    lda #<suffix_prg
    ldy #>suffix_prg
    jsr append_const_to_ptr

    lda #<actdbg_dbg_path
    sta text_ptr
    lda #>actdbg_dbg_path
    sta text_ptr+1
    lda #<prefix_bin
    ldy #>prefix_bin
    jsr copy_const_to_ptr
    lda #<arg_buffer
    ldy #>arg_buffer
    jsr append_const_to_ptr
    lda #<suffix_dbg
    ldy #>suffix_dbg
    jsr append_const_to_ptr
    rts

build_exact_paths:
    lda #<actdbg_prg_path
    sta text_ptr
    lda #>actdbg_prg_path
    sta text_ptr+1
    lda #<arg_buffer
    ldy #>arg_buffer
    jsr copy_const_to_ptr
    jsr derive_dbg_path_from_prg
    jsr derive_project_root_from_prg
    rts

arg_has_dot:
    ldy #$00
arg_has_dot_loop:
    lda arg_buffer,y
    beq arg_has_dot_no
    cmp #'.'
    beq arg_has_dot_yes
    iny
    cpy #PATH_LIMIT
    bcc arg_has_dot_loop
arg_has_dot_no:
    clc
    rts
arg_has_dot_yes:
    sec
    rts

load_prg_header:
    lda #<actdbg_prg_path
    sta file_params+0
    lda #>actdbg_prg_path
    sta file_params+1
    lda #ACTDBG_PRG_REU_BASE_LO
    sta file_params+2
    lda #ACTDBG_PRG_REU_BASE_HI
    sta file_params+3
    lda #ACTDBG_PRG_REU_BASE_BANK
    sta file_params+4
    lda #$00
    sta file_params+5
    sta file_params+6
    sta file_params+7
    sta file_params+8
    ldx #file_params
    jsr actdbg_svc_file_stage_reu_sc0
    lda file_params+5
    cmp #tool_file_status_ok
    beq load_prg_stage_ok
    cmp #tool_file_status_nofile
    bne load_prg_fail
    lda #<msg_no_prg
    ldy #>msg_no_prg
    jmp fail_with_ptr
load_prg_fail:
    lda #<msg_bad_prg
    ldy #>msg_bad_prg
    jmp fail_with_ptr
load_prg_stage_ok:
    lda file_params+6
    sta actdbg_prg_stage_len_lo
    lda file_params+7
    sta actdbg_prg_stage_len_hi
    lda file_params+8
    sta actdbg_prg_stage_len_bank
    lda #ACTDBG_PRG_REU_BASE_LO
    sta file_params+0
    lda #ACTDBG_PRG_REU_BASE_HI
    sta file_params+1
    lda #ACTDBG_PRG_REU_BASE_BANK
    sta file_params+2
    lda #<actdbg_prg_header
    sta file_params+3
    lda #>actdbg_prg_header
    sta file_params+4
    lda #PRG_HEADER_LIMIT
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr actdbg_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    bne load_prg_fail
load_prg_validate:
    lda actdbg_prg_stage_len_bank
    bne load_prg_bad
    lda actdbg_prg_stage_len_hi
    bne load_prg_size_ok
    lda actdbg_prg_stage_len_lo
    cmp #$03
    bcs load_prg_size_ok
    jmp load_prg_bad
load_prg_size_ok:
    lda actdbg_prg_header+1
    cmp #$08
    bcc load_prg_bad
    cmp #$C0
    bcc load_prg_ok
load_prg_bad:
    lda #<msg_bad_prg
    ldy #>msg_bad_prg
    jmp fail_with_ptr
load_prg_ok:
    rts

load_dbg_sidecar:
    lda #<actdbg_dbg_path
    sta file_params+0
    lda #>actdbg_dbg_path
    sta file_params+1
    lda #ACTDBG_DBG_REU_BASE_LO
    sta file_params+2
    lda #ACTDBG_DBG_REU_BASE_HI
    sta file_params+3
    lda #ACTDBG_DBG_REU_BASE_BANK
    sta file_params+4
    lda #$00
    sta file_params+5
    sta file_params+6
    sta file_params+7
    sta file_params+8
    ldx #file_params
    jsr actdbg_svc_file_stage_reu_sc0
    lda file_params+5
    cmp #tool_file_status_ok
    beq load_dbg_stage_ok
    cmp #tool_file_status_nofile
    bne load_dbg_fail
    lda #<msg_no_dbg
    ldy #>msg_no_dbg
    jmp fail_with_ptr
load_dbg_fail:
    lda #<msg_bad_dbg
    ldy #>msg_bad_dbg
    jmp fail_with_ptr
load_dbg_stage_ok:
    lda file_params+6
    sta actdbg_dbg_stage_len_lo
    lda file_params+7
    sta actdbg_dbg_stage_len_hi
    lda file_params+8
    sta actdbg_dbg_stage_len_bank
    lda actdbg_dbg_stage_len_bank
    bne load_dbg_fail
    lda #ACTDBG_DBG_REU_BASE_LO
    sta file_params+0
    lda #ACTDBG_DBG_REU_BASE_HI
    sta file_params+1
    lda #ACTDBG_DBG_REU_BASE_BANK
    sta file_params+2
    lda #<line_buffer
    sta file_params+3
    lda #>line_buffer
    sta file_params+4
    lda #$04
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr actdbg_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    bne load_dbg_fail
load_dbg_validate:
    lda line_buffer+0
    cmp #'D'
    bne load_dbg_bad
    lda line_buffer+1
    cmp #'B'
    bne load_dbg_bad
    lda line_buffer+2
    cmp #'G'
    bne load_dbg_bad
    lda line_buffer+3
    cmp #'1'
    beq load_dbg_ok
load_dbg_bad:
    lda #<msg_bad_dbg
    ldy #>msg_bad_dbg
    jmp fail_with_ptr
load_dbg_ok:
    rts

load_source_file:
    lda #<actdbg_source_path
    sta file_params+0
    lda #>actdbg_source_path
    sta file_params+1
    lda #ACTDBG_SOURCE_REU_BASE_LO
    sta file_params+2
    lda #ACTDBG_SOURCE_REU_BASE_HI
    sta file_params+3
    lda #ACTDBG_SOURCE_REU_BASE_BANK
    sta file_params+4
    lda #$00
    sta file_params+5
    sta file_params+6
    sta file_params+7
    sta file_params+8
    ldx #file_params
    jsr actdbg_svc_file_stage_reu_sc0
    lda file_params+5
    cmp #tool_file_status_ok
    beq load_source_stage_ok
    cmp #tool_file_status_too_large
    bne load_source_missing
    lda #<msg_source_large
    ldy #>msg_source_large
    jmp fail_with_ptr
load_source_missing:
    lda #<msg_no_source
    ldy #>msg_no_source
    jmp fail_with_ptr
load_source_stage_ok:
    lda file_params+6
    sta actdbg_source_stage_len_lo
    lda file_params+7
    sta actdbg_source_stage_len_hi
    lda file_params+8
    sta actdbg_source_stage_len_bank
    lda actdbg_source_stage_len_bank
    beq load_source_ok
    lda #<msg_source_large
    ldy #>msg_source_large
    jmp fail_with_ptr
load_source_ok:
    rts

actdbg_overlay_run_command:
    sta actdbg_overlay_requested_cmd
    jsr actdbg_overlay_select_requested_kind
    sta actdbg_overlay_requested_kind
    jsr actdbg_overlay_ensure_staged
    bcs actdbg_overlay_run_fail
    jsr actdbg_overlay_copy_staged_to_exec
    bcs actdbg_overlay_run_fail
    jsr actdbg_overlay_validate_loaded
    bcs actdbg_overlay_run_fail
    jmp actdbg_overlay_call_exec

actdbg_overlay_run_fail:
    sec
    lda #ACTDBG_OVERLAY_STATUS_FAILED
    rts

actdbg_overlay_select_requested_kind:
    lda actdbg_overlay_requested_cmd
    cmp #ACTDBG_OVERLAY_CMD_EXEC_INIT_RUNTIME
    bcc :+
    lda #ACTDBG_OVERLAY_KIND_EXEC
    rts
:   lda #ACTDBG_OVERLAY_KIND_OPTIONAL_UI
    rts

actdbg_overlay_ensure_staged:
    lda actdbg_overlay_ready
    beq actdbg_overlay_stage_begin
    lda actdbg_overlay_requested_kind
    cmp actdbg_overlay_loaded_kind
    beq actdbg_overlay_stage_ok
actdbg_overlay_stage_begin:
    lda actdbg_overlay_requested_kind
    cmp #ACTDBG_OVERLAY_KIND_OPTIONAL_UI
    bne actdbg_overlay_stage_exec
    lda #<actdbg_overlay_optional_ui_path
    bne actdbg_overlay_stage_set_path
actdbg_overlay_stage_exec:
    lda #<actdbg_overlay_exec_path
actdbg_overlay_stage_set_path:
    sta file_params+0
    lda actdbg_overlay_requested_kind
    cmp #ACTDBG_OVERLAY_KIND_OPTIONAL_UI
    bne :+
    lda #>actdbg_overlay_optional_ui_path
    bne actdbg_overlay_stage_set_path_hi
:   lda #>actdbg_overlay_exec_path
actdbg_overlay_stage_set_path_hi:
    sta file_params+1
    lda #ACTDBG_OVERLAY_REU_BASE_LO
    sta file_params+2
    lda #ACTDBG_OVERLAY_REU_BASE_HI
    sta file_params+3
    lda #ACTDBG_OVERLAY_REU_BASE_BANK
    sta file_params+4
    lda #$00
    sta file_params+5
    sta file_params+6
    sta file_params+7
    sta file_params+8
    ldx #file_params
    jsr actdbg_svc_file_stage_reu_sc0
    lda file_params+5
    sta actdbg_overlay_service_status
    cmp #tool_file_status_ok
    bne actdbg_overlay_stage_fail
    lda file_params+6
    sta actdbg_overlay_loaded_len
    lda file_params+7
    sta actdbg_overlay_loaded_len+1
    lda file_params+8
    beq :+
    jmp actdbg_overlay_stage_fail
:   lda actdbg_overlay_loaded_len
    ora actdbg_overlay_loaded_len+1
    beq actdbg_overlay_stage_fail
    lda actdbg_overlay_loaded_len+1
    cmp #>ACTDBG_OVERLAY_EXEC_SIZE
    bcc :+
    bne actdbg_overlay_stage_fail
    lda actdbg_overlay_loaded_len
    beq :+
    jmp actdbg_overlay_stage_fail
:   lda #$01
    sta actdbg_overlay_ready
    lda actdbg_overlay_requested_kind
    sta actdbg_overlay_loaded_kind
actdbg_overlay_stage_ok:
    clc
    rts

actdbg_overlay_stage_fail:
    lda #$00
    sta actdbg_overlay_ready
    sta actdbg_overlay_loaded_kind
    sec
    rts

actdbg_overlay_copy_staged_to_exec:
    lda #ACTDBG_OVERLAY_REU_BASE_LO
    sta file_params+0
    lda #ACTDBG_OVERLAY_REU_BASE_HI
    sta file_params+1
    lda #ACTDBG_OVERLAY_REU_BASE_BANK
    sta file_params+2
    lda #<ACTDBG_OVERLAY_EXEC_BASE
    sta file_params+3
    lda #>ACTDBG_OVERLAY_EXEC_BASE
    sta file_params+4
    lda actdbg_overlay_loaded_len
    sta file_params+5
    lda actdbg_overlay_loaded_len+1
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr actdbg_svc_reu_read_sc0
    lda file_params+7
    sta actdbg_overlay_service_status
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:   clc
    rts

actdbg_overlay_validate_loaded:
    lda ACTDBG_OVERLAY_EXEC_BASE+0
    cmp #'D'
    bne actdbg_overlay_validate_fail
    lda ACTDBG_OVERLAY_EXEC_BASE+1
    cmp #'G'
    bne actdbg_overlay_validate_fail
    lda ACTDBG_OVERLAY_EXEC_BASE+2
    cmp #'O'
    bne actdbg_overlay_validate_fail
    lda ACTDBG_OVERLAY_EXEC_BASE+3
    cmp #'V'
    bne actdbg_overlay_validate_fail
    lda ACTDBG_OVERLAY_EXEC_BASE+4
    cmp #ACTDBG_OVERLAY_ABI_VERSION
    bne actdbg_overlay_validate_fail
    lda ACTDBG_OVERLAY_EXEC_BASE+5
    cmp #<ACTDBG_OVERLAY_EXEC_BASE
    bne actdbg_overlay_validate_fail
    lda ACTDBG_OVERLAY_EXEC_BASE+6
    cmp #>ACTDBG_OVERLAY_EXEC_BASE
    bne actdbg_overlay_validate_fail
    lda ACTDBG_OVERLAY_EXEC_BASE+9
    cmp actdbg_overlay_loaded_len
    bne actdbg_overlay_validate_fail
    lda ACTDBG_OVERLAY_EXEC_BASE+10
    cmp actdbg_overlay_loaded_len+1
    bne actdbg_overlay_validate_fail
    clc
    rts

actdbg_overlay_validate_fail:
    sec
    rts

actdbg_overlay_call_exec:
    lda C64_MEMCFG
    sta actdbg_overlay_saved_memcfg
    and #C64_MEMCFG_BASIC_OFF_MASK
    sta C64_MEMCFG
    jsr actdbg_overlay_jsr_entry
    php
    lda actdbg_overlay_saved_memcfg
    sta C64_MEMCFG
    plp
    rts

actdbg_overlay_jsr_entry:
    sec
    lda ACTDBG_OVERLAY_EXEC_BASE+7
    sbc #$01
    sta actdbg_overlay_entry_minus_one
    lda ACTDBG_OVERLAY_EXEC_BASE+8
    sbc #$00
    pha
    lda actdbg_overlay_entry_minus_one
    pha
    rts

parse_dbg_records:
    jsr set_active_dbg_file
    lda #$00
    sta scan_ptr
    sta scan_ptr+1
    jsr skip_dbg_header_line
parse_dbg_loop:
    jsr copy_dbg_line_to_buffer
    bcc :+
    jmp parse_dbg_done
:
    lda line_buffer
    beq parse_dbg_loop
    cmp #'e'
    beq parse_dbg_entry
    cmp #'m'
    beq parse_dbg_module
    cmp #'f'
    beq parse_dbg_file
    cmp #'q'
    beq parse_dbg_proc
    cmp #'l'
    bne :+
    jmp parse_dbg_line
:
    cmp #'v'
    bne :+
    jmp parse_dbg_var
:
    jmp parse_dbg_loop

parse_dbg_entry:
    jsr token_scan_begin
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_current_pc_lo
    lda status_ptr+1
    sta actdbg_current_pc_hi
    jmp parse_dbg_loop

parse_dbg_module:
    lda actdbg_module_name
    bne parse_dbg_loop
    jsr token_scan_begin
    jsr token_skip_forward
    jsr token_skip_forward
    lda #MODULE_LIMIT
    sta token_copy_limit
    lda #<actdbg_module_name
    ldy #>actdbg_module_name
    jsr token_copy_to_buffer
    jmp parse_dbg_loop

parse_dbg_file:
    lda source_rel_path
    bne parse_dbg_loop
    jsr token_scan_begin
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_skip_forward
    lda #PATH_LIMIT
    sta token_copy_limit
    lda #<source_rel_path
    ldy #>source_rel_path
    jsr token_copy_to_buffer
    jmp parse_dbg_loop

parse_dbg_proc:
    lda actdbg_have_line_record
    beq :+
    jmp parse_dbg_loop
:
    lda actdbg_target_line_lo
    ora actdbg_target_line_hi
    beq :+
    jmp parse_dbg_loop
:
    jsr token_scan_begin
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_target_module_lo
    lda status_ptr+1
    sta actdbg_target_module_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_target_export_lo
    lda status_ptr+1
    sta actdbg_target_export_hi
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_target_line_lo
    lda status_ptr+1
    sta actdbg_target_line_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_target_col
    lda #MODULE_LIMIT
    sta token_copy_limit
    lda #<actdbg_proc_name
    ldy #>actdbg_proc_name
    jsr token_copy_to_buffer
    jmp parse_dbg_loop

parse_dbg_line:
    lda actdbg_have_line_record
    beq :+
    jmp parse_dbg_loop
:
    jsr token_scan_begin
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_target_module_lo
    lda status_ptr+1
    sta actdbg_target_module_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_target_export_lo
    lda status_ptr+1
    sta actdbg_target_export_hi
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_target_line_lo
    lda status_ptr+1
    sta actdbg_target_line_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_target_col
    lda #$01
    sta actdbg_have_line_record
    jmp parse_dbg_loop

parse_dbg_var:
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
    jmp parse_dbg_loop
:
    lda status_ptr+1
    cmp actdbg_target_module_hi
    beq :+
    jmp parse_dbg_loop
:
    lda actdbg_var_scope
    cmp #'g'
    beq parse_dbg_var_global
    jsr token_parse_u16
    lda status_ptr
    cmp actdbg_target_export_lo
    beq :+
    jmp parse_dbg_loop
:
    lda status_ptr+1
    cmp actdbg_target_export_hi
    beq :+
    jmp parse_dbg_loop
:
    lda actdbg_var_scope
    cmp #'p'
    beq parse_dbg_var_param
    cmp #'l'
    beq parse_dbg_var_local
    jmp parse_dbg_loop

parse_dbg_var_global:
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_skip_forward
    lda #<actdbg_global_summary
    ldy #>actdbg_global_summary
    jsr append_current_token_to_summary
    jmp parse_dbg_loop

parse_dbg_var_param:
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_skip_forward
    lda #<actdbg_param_summary
    ldy #>actdbg_param_summary
    jsr append_current_token_to_summary
    jmp parse_dbg_loop

parse_dbg_var_local:
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_skip_forward
    lda #<actdbg_local_summary
    ldy #>actdbg_local_summary
    jsr append_current_token_to_summary
    jmp parse_dbg_loop

parse_dbg_done:
    rts

skip_dbg_header_line:
skip_dbg_header_loop:
    jsr dbg_read_byte_at_scan_ptr
    bcc :+
    jmp skip_dbg_header_done
:
    beq skip_dbg_header_done
    cmp #$0D
    beq skip_dbg_header_break
    cmp #$0A
    beq skip_dbg_header_break
    jsr inc_scan_ptr
    jmp skip_dbg_header_loop
skip_dbg_header_break:
    jsr skip_newline_chars
skip_dbg_header_done:
    rts

copy_dbg_line_to_buffer:
    jsr dbg_read_byte_at_scan_ptr
    bcc :+
    jmp copy_dbg_line_empty
:
    beq copy_dbg_line_empty
    lda #$00
    sta copy_dbg_line_index
copy_dbg_line_loop:
    jsr dbg_read_byte_at_scan_ptr
    bcc :+
    jmp copy_dbg_line_done_no_break
:
    beq copy_dbg_line_done_no_break
    cmp #$0D
    beq copy_dbg_line_break
    cmp #$0A
    beq copy_dbg_line_break
    ldx copy_dbg_line_index
    cpx #LINE_BUFFER_LIMIT
    bcs copy_dbg_line_skip_store
    sta line_buffer,x
    inc copy_dbg_line_index
copy_dbg_line_skip_store:
    jsr inc_scan_ptr
    jmp copy_dbg_line_loop
copy_dbg_line_break:
    jsr skip_newline_chars
    ldx copy_dbg_line_index
    lda #$00
    sta line_buffer,x
    clc
    rts
copy_dbg_line_done_no_break:
    ldx copy_dbg_line_index
    lda #$00
    sta line_buffer,x
    clc
    rts
copy_dbg_line_empty:
    sec
    rts

resolve_source_path:
    ; Service calls may use shared scratch state, so derive this from the stable
    ; PRG path at the point where each source file is resolved.
    jsr derive_project_root_from_prg
    lda source_rel_path
    beq resolve_source_done
    cmp #'/'
    beq resolve_source_absolute
    lda actdbg_project_root
    beq resolve_source_relative
    lda #<actdbg_source_path
    sta text_ptr
    lda #>actdbg_source_path
    sta text_ptr+1
    lda #<actdbg_project_root
    ldy #>actdbg_project_root
    jsr copy_const_to_ptr
    lda #<slash_name
    ldy #>slash_name
    jsr append_const_to_ptr
    lda #<source_rel_path
    ldy #>source_rel_path
    jsr append_const_to_ptr
    rts
resolve_source_relative:
    lda #<actdbg_source_path
    sta text_ptr
    lda #>actdbg_source_path
    sta text_ptr+1
    lda #<source_rel_path
    ldy #>source_rel_path
    jsr copy_const_to_ptr
    rts
resolve_source_absolute:
    lda #<actdbg_source_path
    sta text_ptr
    lda #>actdbg_source_path
    sta text_ptr+1
    lda #<source_rel_path
    ldy #>source_rel_path
    jsr copy_const_to_ptr
resolve_source_done:
    rts

ensure_source_file_loaded_for_cursor:
    lda actdbg_loaded_source_valid
    beq ensure_source_file_lookup
    lda actdbg_cursor_module_lo
    cmp actdbg_loaded_source_module_lo
    bne ensure_source_file_lookup
    lda actdbg_cursor_module_hi
    cmp actdbg_loaded_source_module_hi
    bne ensure_source_file_lookup
    lda actdbg_cursor_file_lo
    cmp actdbg_loaded_source_file_lo
    bne ensure_source_file_lookup
    lda actdbg_cursor_file_hi
    cmp actdbg_loaded_source_file_hi
    beq ensure_source_file_done
ensure_source_file_lookup:
    lda actdbg_cursor_module_lo
    sta actdbg_lookup_module_lo
    lda actdbg_cursor_module_hi
    sta actdbg_lookup_module_hi
    lda actdbg_cursor_file_lo
    sta actdbg_lookup_file_lo
    lda actdbg_cursor_file_hi
    sta actdbg_lookup_file_hi
    lda #<source_rel_path
    ldy #>source_rel_path
    jsr lookup_source_path_for_lookup_ids_to_buffer
    lda source_rel_path
    beq ensure_source_file_missing
    jsr resolve_source_path
    jsr load_source_file
    lda actdbg_cursor_module_lo
    sta actdbg_loaded_source_module_lo
    lda actdbg_cursor_module_hi
    sta actdbg_loaded_source_module_hi
    lda actdbg_cursor_file_lo
    sta actdbg_loaded_source_file_lo
    lda actdbg_cursor_file_hi
    sta actdbg_loaded_source_file_hi
    lda #$01
    sta actdbg_loaded_source_valid
ensure_source_file_done:
    rts
ensure_source_file_missing:
    lda #<msg_no_source
    ldy #>msg_no_source
    jmp fail_with_ptr

lookup_source_path_for_lookup_ids_to_buffer:
    sta const_ptr
    sty const_ptr+1
    lda #$00
    ldy #$00
    sta (const_ptr),y
    jsr set_dbg_scan_to_body
lookup_source_path_loop:
    jsr copy_dbg_line_to_buffer
    bcc :+
    rts
:   lda line_buffer
    cmp #'f'
    bne lookup_source_path_loop
    jsr token_scan_begin
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    cmp actdbg_lookup_module_lo
    bne lookup_source_path_loop
    lda status_ptr+1
    cmp actdbg_lookup_module_hi
    bne lookup_source_path_loop
    jsr token_parse_u16
    lda status_ptr
    cmp actdbg_lookup_file_lo
    bne lookup_source_path_loop
    lda status_ptr+1
    cmp actdbg_lookup_file_hi
    bne lookup_source_path_loop
    lda #PATH_LIMIT
    sta token_copy_limit
    lda const_ptr
    ldy const_ptr+1
    jmp token_copy_to_buffer

render_source_screen:
    jsr ensure_source_file_loaded_for_cursor
    lda #<SCREEN_RAM
    sta base_ptr
    lda #>SCREEN_RAM
    sta base_ptr+1
    jsr fill_screen_spaces

    lda #$00
    sta current_row
    sta current_col
    lda #<title_prefix
    ldy #>title_prefix
    jsr draw_const_string_at
    lda #$00
    sta current_row
    lda #$07
    sta current_col
    lda #<actdbg_module_name
    ldy #>actdbg_module_name
    jsr draw_const_string_at
    lda actdbg_proc_name
    beq :+
    lda #$00
    sta current_row
    lda #20
    sta current_col
    lda #<proc_prefix
    ldy #>proc_prefix
    jsr draw_const_string_at
    lda #$00
    sta current_row
    lda #26
    sta current_col
    lda #<actdbg_proc_name
    ldy #>actdbg_proc_name
    jsr draw_const_string_at
:

    lda #$01
    sta current_row
    lda #$00
    sta current_col
    lda #<actdbg_source_path
    ldy #>actdbg_source_path
    jsr draw_const_string_at

    lda actdbg_cursor_line_lo
    sta line_number_lo
    lda actdbg_cursor_line_hi
    sta line_number_hi
    jsr set_active_source_file
    jsr find_source_line_start_for_requested_line

    lda status_ptr
    sta line_start_ptr
    lda status_ptr+1
    sta line_start_ptr+1

    lda actdbg_cursor_line_lo
    sta line_number_lo
    lda actdbg_cursor_line_hi
    sta line_number_hi

    ldy #10
rewind_source_lines:
    lda line_number_hi
    bne rewind_step
    lda line_number_lo
    cmp #$02
    bcc rewind_done
rewind_step:
    jsr move_to_previous_source_line
    bcs rewind_done
    lda line_number_lo
    bne :+
    dec line_number_hi
:   dec line_number_lo
    dey
    bne rewind_source_lines
rewind_done:
    lda line_start_ptr
    sta line_work_ptr
    lda line_start_ptr+1
    sta line_work_ptr+1

    lda line_number_lo
    sta work_line_lo
    lda line_number_hi
    sta work_line_hi

    ldx #$00
render_source_rows_loop:
    cpx #SOURCE_ROWS
    bcs render_source_done
    txa
    clc
    adc #SOURCE_ROW_FIRST
    tay
    sty current_row
    txa
    pha
    jsr draw_source_row
    pla
    tax
    txa
    pha
    jsr advance_source_line_ptr
    pla
    tax
    inc work_line_lo
    bne :+
    inc work_line_hi
:   inx
    jmp render_source_rows_loop
render_source_done:
    lda #BACKTRACE_ROW
    sta current_row
    lda #$00
    sta current_col
    lda #<backtrace_prefix
    ldy #>backtrace_prefix
    jsr draw_const_string_at
    lda #BACKTRACE_ROW
    sta current_row
    lda #$04
    sta current_col
    lda #<actdbg_backtrace_summary
    ldy #>actdbg_backtrace_summary
    jsr draw_const_string_at
    lda actdbg_break_list_view
    beq render_source_not_break_list
.if ACTDBG_KEEP_OPTIONAL_UI_RESIDENT_FALLBACK
    jsr rebuild_breakpoint_list_summaries
    jsr draw_breakpoint_list
.else
    lda #ACTDBG_OVERLAY_CMD_DRAW_OPTIONAL_VIEW
    jsr actdbg_overlay_run_command
    bcc render_source_help
    jsr clear_summary_buffers
    jsr draw_empty_variable_summaries
.endif
    jmp render_source_help
render_source_not_break_list:
    lda actdbg_detail_view
    beq render_source_vars
.if ACTDBG_KEEP_OPTIONAL_UI_RESIDENT_FALLBACK
    jsr draw_backtrace_details
.else
    lda #ACTDBG_OVERLAY_CMD_DRAW_OPTIONAL_VIEW
    jsr actdbg_overlay_run_command
    bcc render_source_help
    jsr clear_summary_buffers
    jsr draw_empty_variable_summaries
.endif
    jmp render_source_help
render_source_vars:
.if ACTDBG_KEEP_OPTIONAL_UI_RESIDENT_FALLBACK
    jsr draw_variable_summaries
.else
    lda #ACTDBG_OVERLAY_CMD_DRAW_VARIABLE_SUMMARIES
    jsr actdbg_overlay_run_command
    bcc render_source_help
    jsr clear_summary_buffers
    jsr draw_empty_variable_summaries
.endif
render_source_help:
    lda #24
    sta current_row
    lda #$00
    sta current_col
    lda actdbg_chain_failed
    beq render_source_help_normal
    lda #<edit_handoff_failed_line
    ldy #>edit_handoff_failed_line
    jmp render_source_help_draw
render_source_help_normal:
    lda #<help_line
    ldy #>help_line
render_source_help_draw:
    jsr draw_const_string_at
    rts

clear_summary_buffers:
    ldx #SUMMARY_LIMIT
clear_summary_buffers_loop:
    lda #$00
    sta actdbg_backtrace_summary,x
    sta actdbg_global_summary,x
    sta actdbg_param_summary,x
    sta actdbg_local_summary,x
    dex
    bpl clear_summary_buffers_loop
    rts

draw_empty_variable_summaries:
    lda #BACKTRACE_ROW
    sta current_row
    lda #$04
    sta current_col
    lda #<actdbg_backtrace_summary
    ldy #>actdbg_backtrace_summary
    jsr draw_const_string_at

    lda #GLOBAL_ROW
    sta current_row
    lda #$00
    sta current_col
    lda #<globals_prefix
    ldy #>globals_prefix
    jsr draw_const_string_at

    lda #PARAM_ROW
    sta current_row
    lda #$00
    sta current_col
    lda #<params_prefix
    ldy #>params_prefix
    jsr draw_const_string_at

    lda #LOCAL_ROW
    sta current_row
    lda #$00
    sta current_col
    lda #<locals_prefix
    ldy #>locals_prefix
    jmp draw_const_string_at

current_line_has_breakpoint:
    ldx #$00
current_line_breakpoint_loop:
    cpx #BREAKPOINT_MAX
    bcs current_line_breakpoint_miss
    lda actdbg_break_active,x
    beq current_line_breakpoint_next
    lda actdbg_break_module_lo,x
    cmp actdbg_cursor_module_lo
    bne current_line_breakpoint_next
    lda actdbg_break_module_hi,x
    cmp actdbg_cursor_module_hi
    bne current_line_breakpoint_next
    lda actdbg_break_file_lo,x
    cmp actdbg_cursor_file_lo
    bne current_line_breakpoint_next
    lda actdbg_break_file_hi,x
    cmp actdbg_cursor_file_hi
    bne current_line_breakpoint_next
    lda actdbg_break_line_lo,x
    cmp work_line_lo
    bne current_line_breakpoint_next
    lda actdbg_break_line_hi,x
    cmp work_line_hi
    beq current_line_breakpoint_hit
current_line_breakpoint_next:
    inx
    jmp current_line_breakpoint_loop
current_line_breakpoint_hit:
    sec
    rts
current_line_breakpoint_miss:
    clc
    rts

init_output_screen:
    lda #$00
    sta actdbg_output_row
    sta actdbg_output_col
    ldx #$00
init_output_screen_fill_loop:
    lda #$20
    sta actdbg_output_row_buffer,x
    inx
    cpx #SCREEN_COLS
    bcc init_output_screen_fill_loop
    ldx #$00
init_output_screen_write_loop:
    txa
    pha
    jsr store_output_row_buffer_to_reu_row_a
    pla
    tax
    inx
    cpx #SCREEN_ROWS
    bcc init_output_screen_write_loop
    rts

show_source_screen:
    lda #VIEW_SOURCE
    sta actdbg_view_mode
    rts

show_output_screen:
    lda #VIEW_OUTPUT
    sta actdbg_view_mode
    lda #<SCREEN_RAM
    sta base_ptr
    lda #>SCREEN_RAM
    sta base_ptr+1
    ldx #$00
show_output_screen_rows:
    txa
    pha
    jsr load_output_row_buffer_from_reu_row_a
    pla
    tax
    txa
    sta current_row
    ldx #$00
    lda current_row
    jsr calc_row_ptr
    ldy #$00
show_output_screen_copy_row:
    lda actdbg_output_row_buffer,y
    sta (row_ptr),y
    iny
    cpy #SCREEN_COLS
    bcc show_output_screen_copy_row
    ldx current_row
    inx
    cpx #SCREEN_ROWS
    bcc show_output_screen_rows
    rts

read_input_key:
    lda actdbg_test_mode
    beq read_input_real
    lda actdbg_test_key_count
    beq read_input_real
    ldy actdbg_test_key_index
    lda actdbg_test_keys,y
    inc actdbg_test_key_index
    dec actdbg_test_key_count
    rts

read_input_real:
    jsr actdbg_save_zp_state
    jsr SCNKEY
    jsr GETIN
    sta actdbg_input_key
    jsr actdbg_restore_zp_state
    lda actdbg_input_key
    rts

normalize_input_key:
    cmp #'a'
    bcc normalize_input_key_petscii
    cmp #'z'+1
    bcs normalize_input_key_petscii
    and #$DF
    rts
normalize_input_key_petscii:
    cmp #$C1
    bcc normalize_input_key_done
    cmp #$DB
    bcs normalize_input_key_done
    and #$7F
normalize_input_key_done:
    rts

set_output_reu_params_from_row_a:
    tay
    clc
    lda #ACTDBG_OUTPUT_REU_BASE_LO
    adc row_offset_lo,y
    sta file_params+0
    lda #ACTDBG_OUTPUT_REU_BASE_HI
    adc row_offset_hi,y
    sta file_params+1
    lda #ACTDBG_OUTPUT_REU_BASE_BANK
    adc #$00
    sta file_params+2
    rts

load_output_row_buffer_from_reu_row_a:
    jsr set_output_reu_params_from_row_a
    lda #<actdbg_output_row_buffer
    sta file_params+3
    lda #>actdbg_output_row_buffer
    sta file_params+4
    lda #SCREEN_COLS
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr actdbg_svc_reu_read_sc0
    rts

store_output_row_buffer_to_reu_row_a:
    jsr set_output_reu_params_from_row_a
    lda #<actdbg_output_row_buffer
    sta file_params+3
    lda #>actdbg_output_row_buffer
    sta file_params+4
    lda #SCREEN_COLS
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr actdbg_svc_reu_write_sc0
    rts

init_debug_runtime:
    lda #ACTDBG_OVERLAY_CMD_EXEC_INIT_RUNTIME
    jmp actdbg_overlay_run_command

set_dbg_scan_to_body:
    jsr set_active_dbg_file
    lda #$00
    sta scan_ptr
    sta scan_ptr+1
    jmp skip_dbg_header_line

update_debug_location_from_current_pc:
    jsr lookup_dbg_location_for_current_pc
    bcc :+
    lda #$01
    sta actdbg_target_line_lo
    lda #$00
    sta actdbg_target_line_hi
    lda #$01
    sta actdbg_target_col
    lda #$00
    sta actdbg_target_module_lo
    sta actdbg_target_module_hi
    sta actdbg_target_export_lo
    sta actdbg_target_export_hi
    sta actdbg_proc_name
:   jsr sync_cursor_to_target_location
.if ACTDBG_KEEP_OPTIONAL_UI_RESIDENT_FALLBACK
    jsr rebuild_backtrace_summary
    jsr rebuild_variable_summaries_for_current_scope
.else
    lda #ACTDBG_OVERLAY_CMD_REBUILD_STOP_SUMMARIES
    jsr actdbg_overlay_run_command
    bcc :+
    jsr clear_summary_buffers
:
.endif
    rts

sync_cursor_to_target_location:
    lda actdbg_target_module_lo
    sta actdbg_cursor_module_lo
    lda actdbg_target_module_hi
    sta actdbg_cursor_module_hi
    lda actdbg_target_file_lo
    sta actdbg_cursor_file_lo
    lda actdbg_target_file_hi
    sta actdbg_cursor_file_hi
    lda actdbg_target_line_lo
    sta actdbg_cursor_line_lo
    lda actdbg_target_line_hi
    sta actdbg_cursor_line_hi
    lda actdbg_target_col
    sta actdbg_cursor_col
    lda #$00
    sta actdbg_source_col_offset
    rts

.if ACTDBG_KEEP_OPTIONAL_UI_RESIDENT_FALLBACK
toggle_current_line_breakpoint:
    lda actdbg_cursor_line_lo
    ora actdbg_cursor_line_hi
    beq toggle_current_line_breakpoint_fail
    jsr find_breakpoint_slot_for_target_line
    bcs toggle_current_line_breakpoint_add
    lda #$00
    sta actdbg_break_active,x
    clc
    rts
toggle_current_line_breakpoint_add:
    jsr lookup_breakpoint_pc_for_target_line
    bcs toggle_current_line_breakpoint_fail
    jsr find_free_breakpoint_slot
    bcs toggle_current_line_breakpoint_fail
    lda #$01
    sta actdbg_break_active,x
    lda word_tmp
    sta actdbg_break_pc_lo,x
    lda word_tmp+1
    sta actdbg_break_pc_hi,x
    lda actdbg_cursor_module_lo
    sta actdbg_break_module_lo,x
    lda actdbg_cursor_module_hi
    sta actdbg_break_module_hi,x
    lda actdbg_cursor_file_lo
    sta actdbg_break_file_lo,x
    lda actdbg_cursor_file_hi
    sta actdbg_break_file_hi,x
    lda actdbg_cursor_line_lo
    sta actdbg_break_line_lo,x
    lda actdbg_cursor_line_hi
    sta actdbg_break_line_hi,x
    clc
    rts
toggle_current_line_breakpoint_fail:
    sec
    rts

find_breakpoint_slot_for_target_line:
    ldx #$00
find_breakpoint_slot_loop:
    cpx #BREAKPOINT_MAX
    bcs find_breakpoint_slot_fail
    lda actdbg_break_active,x
    beq find_breakpoint_slot_next
    lda actdbg_break_module_lo,x
    cmp actdbg_cursor_module_lo
    bne find_breakpoint_slot_next
    lda actdbg_break_module_hi,x
    cmp actdbg_cursor_module_hi
    bne find_breakpoint_slot_next
    lda actdbg_break_file_lo,x
    cmp actdbg_cursor_file_lo
    bne find_breakpoint_slot_next
    lda actdbg_break_file_hi,x
    cmp actdbg_cursor_file_hi
    bne find_breakpoint_slot_next
    lda actdbg_break_line_lo,x
    cmp actdbg_cursor_line_lo
    bne find_breakpoint_slot_next
    lda actdbg_break_line_hi,x
    cmp actdbg_cursor_line_hi
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
    cpx #BREAKPOINT_MAX
    bcs find_free_breakpoint_slot_fail
    lda actdbg_break_active,x
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
    sta actdbg_break_lookup_found
    jsr set_dbg_scan_to_body

lookup_breakpoint_pc_loop:
    jsr copy_dbg_line_to_buffer
    bcc :+
    jmp lookup_breakpoint_pc_done
:   lda line_buffer
    cmp #'l'
    bne lookup_breakpoint_pc_loop
    jsr token_scan_begin
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    cmp actdbg_cursor_module_lo
    bne lookup_breakpoint_pc_loop
    lda status_ptr+1
    cmp actdbg_cursor_module_hi
    bne lookup_breakpoint_pc_loop
    jsr token_parse_u16
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_dbg_candidate_pc_lo
    lda status_ptr+1
    sta actdbg_dbg_candidate_pc_hi
    jsr token_parse_u16
    lda status_ptr
    cmp actdbg_cursor_file_lo
    bne lookup_breakpoint_pc_loop
    lda status_ptr+1
    cmp actdbg_cursor_file_hi
    bne lookup_breakpoint_pc_loop
    jsr token_parse_u16
    lda status_ptr
    cmp actdbg_cursor_line_lo
    bne lookup_breakpoint_pc_loop
    lda status_ptr+1
    cmp actdbg_cursor_line_hi
    bne lookup_breakpoint_pc_loop
    lda actdbg_break_lookup_found
    beq lookup_breakpoint_store_pc
    lda actdbg_dbg_candidate_pc_hi
    cmp actdbg_break_lookup_pc_hi
    bcc lookup_breakpoint_store_pc
    bne lookup_breakpoint_pc_loop
    lda actdbg_dbg_candidate_pc_lo
    cmp actdbg_break_lookup_pc_lo
    bcs lookup_breakpoint_pc_loop

lookup_breakpoint_store_pc:
    lda #$01
    sta actdbg_break_lookup_found
    lda actdbg_dbg_candidate_pc_lo
    sta actdbg_break_lookup_pc_lo
    lda actdbg_dbg_candidate_pc_hi
    sta actdbg_break_lookup_pc_hi
    jmp lookup_breakpoint_pc_loop

lookup_breakpoint_pc_done:
    lda actdbg_break_lookup_found
    beq lookup_breakpoint_pc_fail
    lda actdbg_break_lookup_pc_lo
    sta word_tmp
    lda actdbg_break_lookup_pc_hi
    sta word_tmp+1
    clc
    rts
lookup_breakpoint_pc_fail:
    sec
    rts
.endif

lookup_dbg_location_for_current_pc:
    lda #ACTDBG_OVERLAY_CMD_EXEC_LOOKUP_LOCATION
    jmp actdbg_overlay_run_command

.if ACTDBG_KEEP_OPTIONAL_UI_RESIDENT_FALLBACK
rebuild_variable_summaries_for_current_scope:
    ldx #SUMMARY_LIMIT
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

.if ACTDBG_KEEP_OPTIONAL_UI_RESIDENT_FALLBACK
rebuild_breakpoint_list_summaries:
    ldx #SUMMARY_LIMIT
rebuild_break_list_clear_loop:
    lda #$00
    sta actdbg_trace_summary0,x
    sta actdbg_trace_summary1,x
    sta actdbg_trace_summary2,x
    dex
    bpl rebuild_break_list_clear_loop
    lda #$00
    sta actdbg_lookup_found
    ldx #$00
rebuild_break_list_slot_loop:
    cpx #BREAKPOINT_MAX
    bcs rebuild_break_list_done
    lda actdbg_break_active,x
    beq rebuild_break_list_next
    lda actdbg_lookup_found
    cmp #$03
    bcs rebuild_break_list_done
    txa
    pha
    lda actdbg_break_module_lo,x
    sta actdbg_lookup_module_lo
    lda actdbg_break_module_hi,x
    sta actdbg_lookup_module_hi
    lda actdbg_break_file_lo,x
    sta actdbg_lookup_file_lo
    lda actdbg_break_file_hi,x
    sta actdbg_lookup_file_hi
    lda #<source_rel_path
    ldy #>source_rel_path
    jsr lookup_source_path_for_lookup_ids_to_buffer
    lda actdbg_lookup_found
    jsr set_trace_summary_buffer_from_a
    ldx #$00
    pla
    tay
    tya
    sta hex_tmp
    lda source_rel_path
    beq rebuild_break_list_unknown
    lda #<source_rel_path
    ldy #>source_rel_path
    jsr append_cstr_to_summary
    jmp rebuild_break_list_append_line
rebuild_break_list_unknown:
    lda #'?'
    jsr append_summary_char_a
rebuild_break_list_append_line:
    ldy hex_tmp
    lda #':'
    jsr append_summary_char_a
    lda actdbg_break_line_lo,y
    sta word_tmp
    lda actdbg_break_line_hi,y
    sta word_tmp+1
    jsr append_summary_word_decimal
    ldy #$00
    lda #$00
    sta (const_ptr),y
    inc actdbg_lookup_found
    tya
    tax
rebuild_break_list_next:
    inx
    jmp rebuild_break_list_slot_loop
rebuild_break_list_done:
    lda actdbg_lookup_found
    bne :+
    lda #<actdbg_trace_summary0
    sta const_ptr
    lda #>actdbg_trace_summary0
    sta const_ptr+1
    ldx #$00
    lda #'N'
    jsr append_summary_char_a
    lda #'O'
    jsr append_summary_char_a
    lda #'N'
    jsr append_summary_char_a
    lda #'E'
    jsr append_summary_char_a
    ldy #$00
    lda #$00
    sta (const_ptr),y
:   rts

set_trace_summary_buffer_from_a:
    cmp #$00
    bne :+
    lda #<actdbg_trace_summary0
    sta const_ptr
    lda #>actdbg_trace_summary0
    sta const_ptr+1
    rts
:   cmp #$01
    bne :+
    lda #<actdbg_trace_summary1
    sta const_ptr
    lda #>actdbg_trace_summary1
    sta const_ptr+1
    rts
:   lda #<actdbg_trace_summary2
    sta const_ptr
    lda #>actdbg_trace_summary2
    sta const_ptr+1
    rts
.endif

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
:
    lda #$01
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
:
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
    lda #MODULE_LIMIT
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
.endif

fill_screen_spaces:
    lda #' '
    jsr ascii_to_screen
    ldy #$00
fill_screen_page0:
    sta (base_ptr),y
    iny
    bne fill_screen_page0
    inc base_ptr+1
    ldy #$00
fill_screen_page1:
    sta (base_ptr),y
    iny
    bne fill_screen_page1
    inc base_ptr+1
    ldy #$00
fill_screen_page2:
    sta (base_ptr),y
    iny
    bne fill_screen_page2
    inc base_ptr+1
    ldy #$00
fill_screen_page3:
    sta (base_ptr),y
    iny
    bne fill_screen_page3
    sec
    lda base_ptr
    sbc #$00
    sta base_ptr
    lda base_ptr+1
    sbc #$03
    sta base_ptr+1
    rts

draw_source_row:
    txa
    pha
    lda current_row
    ldx #$00
    jsr calc_row_ptr
    pla
    tax
    jsr current_line_has_breakpoint
    bcc draw_source_row_no_breakpoint
    lda #'*'
    bne draw_source_row_break_marker
draw_source_row_no_breakpoint:
    lda #' '
draw_source_row_break_marker:
    jsr ascii_to_screen
    ldy #$00
    sta (row_ptr),y
    iny
    lda work_line_lo
    cmp actdbg_cursor_line_lo
    bne draw_source_row_not_cursor
    lda work_line_hi
    cmp actdbg_cursor_line_hi
    bne draw_source_row_not_cursor
    lda #'>'
    bne draw_source_row_marker
draw_source_row_not_cursor:
    lda actdbg_cursor_module_lo
    cmp actdbg_target_module_lo
    bne draw_source_row_not_target
    lda actdbg_cursor_module_hi
    cmp actdbg_target_module_hi
    bne draw_source_row_not_target
    lda actdbg_cursor_file_lo
    cmp actdbg_target_file_lo
    bne draw_source_row_not_target
    lda actdbg_cursor_file_hi
    cmp actdbg_target_file_hi
    bne draw_source_row_not_target
    lda work_line_lo
    cmp actdbg_target_line_lo
    bne draw_source_row_not_target
    lda work_line_hi
    cmp actdbg_target_line_hi
    bne draw_source_row_not_target
    lda #'@'
    bne draw_source_row_marker
draw_source_row_not_target:
    lda #' '
draw_source_row_marker:
    jsr ascii_to_screen
    sta (row_ptr),y
    iny
    lda #' '
    jsr ascii_to_screen
    sta (row_ptr),y
    iny
    sty current_col
    jsr copy_source_line_to_buffer_from_line_work_ptr
    lda #<line_buffer
    sta text_ptr
    lda #>line_buffer
    sta text_ptr+1
    jsr apply_source_col_offset_to_text_ptr

draw_source_chars_loop:
    ldy #$00
    lda (text_ptr),y
    beq draw_source_chars_done
    cmp #$0D
    beq draw_source_chars_done
    cmp #$0A
    beq draw_source_chars_done
    ldy current_col
    cpy #SCREEN_COLS
    bcs draw_source_chars_done
    jsr ascii_to_screen
    sta (row_ptr),y
    inc text_ptr
    bne :+
    inc text_ptr+1
:   inc current_col
    jmp draw_source_chars_loop

draw_source_chars_done:
    rts

apply_source_col_offset_to_text_ptr:
    ldx actdbg_source_col_offset
    beq apply_source_col_offset_done
apply_source_col_offset_loop:
    ldy #$00
    lda (text_ptr),y
    beq apply_source_col_offset_done
    cmp #$0D
    beq apply_source_col_offset_done
    cmp #$0A
    beq apply_source_col_offset_done
    inc text_ptr
    bne :+
    inc text_ptr+1
:   dex
    bne apply_source_col_offset_loop
apply_source_col_offset_done:
    rts

advance_source_line_ptr:
    lda line_work_ptr
    sta status_ptr
    lda line_work_ptr+1
    sta status_ptr+1
    jsr advance_ptr_to_next_line
    lda status_ptr
    sta line_work_ptr
    lda status_ptr+1
    sta line_work_ptr+1
    rts

find_source_line_start:
    lda actdbg_target_line_lo
    sta line_number_lo
    lda actdbg_target_line_hi
    sta line_number_hi
    jmp find_source_line_start_for_requested_line

find_source_line_start_for_requested_line:
    lda #$00
    sta status_ptr
    sta status_ptr+1
    lda #$01
    sta work_line_lo
    lda #$00
    sta work_line_hi
find_source_loop:
    lda work_line_lo
    cmp line_number_lo
    bne find_source_step
    lda work_line_hi
    cmp line_number_hi
    beq find_source_done
find_source_step:
    jsr source_read_byte_at_status_ptr
    bcc :+
    jmp find_source_done
:
    beq find_source_done
    jsr advance_ptr_to_next_line
    inc work_line_lo
    bne :+
    inc work_line_hi
:   jmp find_source_loop
find_source_done:
    rts

move_source_cursor_up:
    lda actdbg_cursor_line_hi
    bne move_source_cursor_up_step
    lda actdbg_cursor_line_lo
    cmp #$02
    bcc move_source_cursor_up_fail
move_source_cursor_up_step:
    lda actdbg_cursor_line_lo
    bne :+
    dec actdbg_cursor_line_hi
:   dec actdbg_cursor_line_lo
    clc
    rts
move_source_cursor_up_fail:
    sec
    rts

move_source_cursor_down:
    lda actdbg_cursor_line_lo
    clc
    adc #$01
    sta line_number_lo
    lda actdbg_cursor_line_hi
    adc #$00
    sta line_number_hi
    jsr set_active_source_file
    jsr find_source_line_start_for_requested_line
    jsr source_read_byte_at_status_ptr
    bcs move_source_cursor_down_fail
    beq move_source_cursor_down_fail
    lda line_number_lo
    sta actdbg_cursor_line_lo
    lda line_number_hi
    sta actdbg_cursor_line_hi
    clc
    rts
move_source_cursor_down_fail:
    sec
    rts

can_scroll_source_right:
    lda actdbg_cursor_line_lo
    sta line_number_lo
    lda actdbg_cursor_line_hi
    sta line_number_hi
    jsr set_active_source_file
    jsr find_source_line_start_for_requested_line
    lda status_ptr
    sta line_work_ptr
    lda status_ptr+1
    sta line_work_ptr+1
    jsr copy_source_line_to_buffer_from_line_work_ptr
    ldx #$00
can_scroll_source_right_len_loop:
    lda line_buffer,x
    beq can_scroll_source_right_len_done
    inx
    cpx #LINE_BUFFER_LIMIT
    bcc can_scroll_source_right_len_loop
can_scroll_source_right_len_done:
    txa
    sec
    sbc actdbg_source_col_offset
    cmp #37
    bcc can_scroll_source_right_fail
    beq can_scroll_source_right_fail
    clc
    rts
can_scroll_source_right_fail:
    sec
    rts

clear_breakpoint_slots:
    ldx #BREAKPOINT_MAX-1
clear_breakpoint_slots_helper_loop:
    lda #$00
    sta actdbg_break_active,x
    sta actdbg_break_pc_lo,x
    sta actdbg_break_pc_hi,x
    sta actdbg_break_module_lo,x
    sta actdbg_break_module_hi,x
    sta actdbg_break_file_lo,x
    sta actdbg_break_file_hi,x
    sta actdbg_break_line_lo,x
    sta actdbg_break_line_hi,x
    dex
    bpl clear_breakpoint_slots_helper_loop
    rts

.if ACTDBG_KEEP_OPTIONAL_UI_RESIDENT_FALLBACK
set_cursor_from_lookup:
    lda actdbg_lookup_module_lo
    sta actdbg_cursor_module_lo
    lda actdbg_lookup_module_hi
    sta actdbg_cursor_module_hi
    lda actdbg_lookup_file_lo
    sta actdbg_cursor_file_lo
    lda actdbg_lookup_file_hi
    sta actdbg_cursor_file_hi
    lda actdbg_lookup_line_lo
    sta actdbg_cursor_line_lo
    lda actdbg_lookup_line_hi
    sta actdbg_cursor_line_hi
    lda actdbg_lookup_col
    sta actdbg_cursor_col
    lda #$00
    sta actdbg_source_col_offset
    clc
    rts

set_cursor_to_first_line_for_lookup_file:
    lda #$01
    sta actdbg_lookup_line_lo
    lda #$00
    sta actdbg_lookup_line_hi
    sta actdbg_lookup_col
    jsr set_dbg_scan_to_body
set_cursor_file_line_loop:
    jsr copy_dbg_line_to_buffer
    bcc :+
    jmp set_cursor_file_proc_fallback
:   lda line_buffer
    cmp #'l'
    bne set_cursor_file_line_loop
    jsr token_scan_begin
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    cmp actdbg_lookup_module_lo
    bne set_cursor_file_line_loop
    lda status_ptr+1
    cmp actdbg_lookup_module_hi
    bne set_cursor_file_line_loop
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    cmp actdbg_lookup_file_lo
    bne set_cursor_file_line_loop
    lda status_ptr+1
    cmp actdbg_lookup_file_hi
    bne set_cursor_file_line_loop
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_lookup_line_lo
    lda status_ptr+1
    sta actdbg_lookup_line_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_lookup_col
    jmp set_cursor_from_lookup
set_cursor_file_proc_fallback:
    jsr set_dbg_scan_to_body
set_cursor_file_proc_loop:
    jsr copy_dbg_line_to_buffer
    bcc :+
    jmp set_cursor_from_lookup
:   lda line_buffer
    cmp #'q'
    bne set_cursor_file_proc_loop
    jsr token_scan_begin
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    cmp actdbg_lookup_module_lo
    bne set_cursor_file_proc_loop
    lda status_ptr+1
    cmp actdbg_lookup_module_hi
    bne set_cursor_file_proc_loop
    jsr token_skip_forward
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    cmp actdbg_lookup_file_lo
    bne set_cursor_file_proc_loop
    lda status_ptr+1
    cmp actdbg_lookup_file_hi
    bne set_cursor_file_proc_loop
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_lookup_line_lo
    lda status_ptr+1
    sta actdbg_lookup_line_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_lookup_col
    jmp set_cursor_from_lookup

set_cursor_to_first_line_for_lookup_export:
    jsr set_dbg_scan_to_body
set_cursor_export_line_loop:
    jsr copy_dbg_line_to_buffer
    bcc :+
    jmp set_cursor_from_lookup
:   lda line_buffer
    cmp #'l'
    bne set_cursor_export_line_loop
    jsr token_scan_begin
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    cmp actdbg_lookup_module_lo
    bne set_cursor_export_line_loop
    lda status_ptr+1
    cmp actdbg_lookup_module_hi
    bne set_cursor_export_line_loop
    jsr token_parse_u16
    lda status_ptr
    cmp actdbg_lookup_export_lo
    bne set_cursor_export_line_loop
    lda status_ptr+1
    cmp actdbg_lookup_export_hi
    bne set_cursor_export_line_loop
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_lookup_file_lo
    lda status_ptr+1
    sta actdbg_lookup_file_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_lookup_line_lo
    lda status_ptr+1
    sta actdbg_lookup_line_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_lookup_col
    jmp set_cursor_from_lookup

select_next_source_file_cursor:
    lda #$00
    sta actdbg_lookup_found
    jsr set_dbg_scan_to_body
select_next_source_file_loop:
    jsr copy_dbg_line_to_buffer
    bcc select_next_source_file_have_line
    lda actdbg_lookup_found
    bne select_next_source_file_wrap
    jmp select_next_source_file_fail
select_next_source_file_wrap:
    jmp set_cursor_to_first_line_for_lookup_file
select_next_source_file_have_line:
    lda line_buffer
    cmp #'f'
    bne select_next_source_file_loop
    jsr token_scan_begin
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_dbg_candidate_module_lo
    lda status_ptr+1
    sta actdbg_dbg_candidate_module_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_dbg_candidate_file_lo
    lda status_ptr+1
    sta actdbg_dbg_candidate_file_hi
    lda actdbg_lookup_found
    bne :+
    lda actdbg_dbg_candidate_module_lo
    sta actdbg_lookup_module_lo
    lda actdbg_dbg_candidate_module_hi
    sta actdbg_lookup_module_hi
    lda actdbg_dbg_candidate_file_lo
    sta actdbg_lookup_file_lo
    lda actdbg_dbg_candidate_file_hi
    sta actdbg_lookup_file_hi
    lda #$01
    sta actdbg_lookup_found
:   lda actdbg_dbg_candidate_module_hi
    cmp actdbg_cursor_module_hi
    bcs :+
    jmp select_next_source_file_loop
:
    bne select_next_source_file_pick_candidate
    lda actdbg_dbg_candidate_module_lo
    cmp actdbg_cursor_module_lo
    bcs :+
    jmp select_next_source_file_loop
:
    bne select_next_source_file_pick_candidate
    lda actdbg_dbg_candidate_file_hi
    cmp actdbg_cursor_file_hi
    bcs :+
    jmp select_next_source_file_loop
:
    bne select_next_source_file_pick_candidate
    lda actdbg_dbg_candidate_file_lo
    cmp actdbg_cursor_file_lo
    bcs :+
    jmp select_next_source_file_loop
:
    bne select_next_source_file_pick_candidate
    jmp select_next_source_file_loop
select_next_source_file_pick_candidate:
    lda actdbg_dbg_candidate_module_lo
    sta actdbg_lookup_module_lo
    lda actdbg_dbg_candidate_module_hi
    sta actdbg_lookup_module_hi
    lda actdbg_dbg_candidate_file_lo
    sta actdbg_lookup_file_lo
    lda actdbg_dbg_candidate_file_hi
    sta actdbg_lookup_file_hi
    jmp set_cursor_to_first_line_for_lookup_file
select_next_source_file_fail:
    sec
    rts

select_prev_source_file_cursor:
    lda #$00
    sta actdbg_lookup_found
    jsr set_dbg_scan_to_body
select_prev_source_file_loop:
    jsr copy_dbg_line_to_buffer
    bcc :+
    lda actdbg_lookup_found
    beq select_prev_source_file_fail
    lda #$01
    sta actdbg_lookup_line_lo
    lda #$00
    sta actdbg_lookup_line_hi
    sta actdbg_lookup_col
    jmp set_cursor_from_lookup
:   lda line_buffer
    cmp #'f'
    bne select_prev_source_file_loop
    jsr token_scan_begin
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    sta word_tmp
    lda status_ptr+1
    sta word_tmp+1
    jsr token_parse_u16
    lda word_tmp
    cmp actdbg_cursor_module_lo
    bne :+
    lda word_tmp+1
    cmp actdbg_cursor_module_hi
    bne :+
    lda status_ptr
    cmp actdbg_cursor_file_lo
    bne :+
    lda status_ptr+1
    cmp actdbg_cursor_file_hi
    bne :+
    lda actdbg_lookup_found
    beq select_prev_source_file_loop
    lda #$01
    sta actdbg_lookup_line_lo
    lda #$00
    sta actdbg_lookup_line_hi
    sta actdbg_lookup_col
    jmp set_cursor_from_lookup
:   lda word_tmp
    sta actdbg_lookup_module_lo
    lda word_tmp+1
    sta actdbg_lookup_module_hi
    lda status_ptr
    sta actdbg_lookup_file_lo
    lda status_ptr+1
    sta actdbg_lookup_file_hi
    lda #$01
    sta actdbg_lookup_found
    jmp select_prev_source_file_loop
select_prev_source_file_fail:
    sec
    rts

candidate_after_cursor:
    lda actdbg_dbg_candidate_module_hi
    cmp actdbg_cursor_module_hi
    bcc candidate_after_cursor_fail
    bne candidate_after_cursor_hi_ok
    lda actdbg_dbg_candidate_module_lo
    cmp actdbg_cursor_module_lo
    bcc candidate_after_cursor_fail
    bne candidate_after_cursor_hi_ok
    lda actdbg_dbg_candidate_file_hi
    cmp actdbg_cursor_file_hi
    bcc candidate_after_cursor_fail
    bne candidate_after_cursor_hi_ok
    lda actdbg_dbg_candidate_file_lo
    cmp actdbg_cursor_file_lo
    bcc candidate_after_cursor_fail
    bne candidate_after_cursor_hi_ok
    lda actdbg_dbg_candidate_line_hi
    cmp actdbg_cursor_line_hi
    bcc candidate_after_cursor_fail
    bne candidate_after_cursor_hi_ok
    lda actdbg_dbg_candidate_line_lo
    cmp actdbg_cursor_line_lo
    bcc candidate_after_cursor_fail
    bne candidate_after_cursor_hi_ok
    lda actdbg_dbg_candidate_col
    cmp actdbg_cursor_col
    bcc candidate_after_cursor_fail
    beq candidate_after_cursor_fail
candidate_after_cursor_hi_ok:
    clc
    rts
candidate_after_cursor_fail:
    sec
    rts

capture_first_candidate_if_needed:
    lda actdbg_lookup_found
    bne capture_first_candidate_done
    lda actdbg_dbg_candidate_module_lo
    sta actdbg_lookup_module_lo
    lda actdbg_dbg_candidate_module_hi
    sta actdbg_lookup_module_hi
    lda actdbg_dbg_candidate_file_lo
    sta actdbg_lookup_file_lo
    lda actdbg_dbg_candidate_file_hi
    sta actdbg_lookup_file_hi
    lda actdbg_dbg_candidate_line_lo
    sta actdbg_lookup_line_lo
    lda actdbg_dbg_candidate_line_hi
    sta actdbg_lookup_line_hi
    lda actdbg_dbg_candidate_col
    sta actdbg_lookup_col
    lda #$01
    sta actdbg_lookup_found
capture_first_candidate_done:
    rts

select_next_proc_cursor:
    lda #$00
    sta actdbg_lookup_found
    jsr set_dbg_scan_to_body
select_next_proc_loop:
    jsr copy_dbg_line_to_buffer
    bcc select_next_proc_have_line
    lda actdbg_lookup_found
    bne select_next_proc_wrap
    jmp select_next_proc_fail
select_next_proc_wrap:
    jmp set_cursor_to_first_line_for_lookup_export
select_next_proc_have_line:
    lda line_buffer
    cmp #'q'
    bne select_next_proc_loop
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
    jsr token_skip_forward
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
    lda actdbg_lookup_found
    bne :+
    lda actdbg_dbg_candidate_module_lo
    sta actdbg_lookup_module_lo
    lda actdbg_dbg_candidate_module_hi
    sta actdbg_lookup_module_hi
    lda actdbg_dbg_candidate_export_lo
    sta actdbg_lookup_export_lo
    lda actdbg_dbg_candidate_export_hi
    sta actdbg_lookup_export_hi
    lda actdbg_dbg_candidate_file_lo
    sta actdbg_lookup_file_lo
    lda actdbg_dbg_candidate_file_hi
    sta actdbg_lookup_file_hi
    lda actdbg_dbg_candidate_line_lo
    sta actdbg_lookup_line_lo
    lda actdbg_dbg_candidate_line_hi
    sta actdbg_lookup_line_hi
    lda actdbg_dbg_candidate_col
    sta actdbg_lookup_col
    lda #$01
    sta actdbg_lookup_found
:
    jsr candidate_after_cursor
    bcc :+
    jmp select_next_proc_loop
:
    lda actdbg_dbg_candidate_module_lo
    sta actdbg_lookup_module_lo
    lda actdbg_dbg_candidate_module_hi
    sta actdbg_lookup_module_hi
    lda actdbg_dbg_candidate_export_lo
    sta actdbg_lookup_export_lo
    lda actdbg_dbg_candidate_export_hi
    sta actdbg_lookup_export_hi
    lda actdbg_dbg_candidate_file_lo
    sta actdbg_lookup_file_lo
    lda actdbg_dbg_candidate_file_hi
    sta actdbg_lookup_file_hi
    lda actdbg_dbg_candidate_line_lo
    sta actdbg_lookup_line_lo
    lda actdbg_dbg_candidate_line_hi
    sta actdbg_lookup_line_hi
    lda actdbg_dbg_candidate_col
    sta actdbg_lookup_col
    jmp set_cursor_to_first_line_for_lookup_export
select_next_proc_fail:
    sec
    rts

select_next_line_cursor:
    lda #$00
    sta actdbg_lookup_found
    jsr set_dbg_scan_to_body
select_next_line_loop:
    jsr copy_dbg_line_to_buffer
    bcc :+
    lda actdbg_lookup_found
    beq select_next_line_fail
    jmp set_cursor_from_lookup
:   lda line_buffer
    cmp #'l'
    bne select_next_line_loop
    jsr token_scan_begin
    jsr token_skip_forward
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_dbg_candidate_module_lo
    lda status_ptr+1
    sta actdbg_dbg_candidate_module_hi
    jsr token_skip_forward
    jsr token_skip_forward
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
    jsr capture_first_candidate_if_needed
    jsr candidate_after_cursor
    bcs select_next_line_loop
    lda actdbg_dbg_candidate_module_lo
    sta actdbg_lookup_module_lo
    lda actdbg_dbg_candidate_module_hi
    sta actdbg_lookup_module_hi
    lda actdbg_dbg_candidate_file_lo
    sta actdbg_lookup_file_lo
    lda actdbg_dbg_candidate_file_hi
    sta actdbg_lookup_file_hi
    lda actdbg_dbg_candidate_line_lo
    sta actdbg_lookup_line_lo
    lda actdbg_dbg_candidate_line_hi
    sta actdbg_lookup_line_hi
    lda actdbg_dbg_candidate_col
    sta actdbg_lookup_col
    jmp set_cursor_from_lookup
select_next_line_fail:
    sec
    rts
.endif

move_to_previous_source_line:
    lda line_start_ptr
    ora line_start_ptr+1
    beq move_prev_fail
move_prev_search:
    jsr dec_line_start_ptr
move_prev_skip_tail_breaks:
    jsr source_read_byte_at_line_start_ptr
    bcc :+
    jmp move_prev_found
:
    cmp #$0A
    beq move_prev_skip_break_step
    cmp #$0D
    beq move_prev_skip_break_step
    jmp move_prev_find_break
move_prev_skip_break_step:
    lda line_start_ptr
    ora line_start_ptr+1
    beq move_prev_found
    jsr dec_line_start_ptr
    jmp move_prev_skip_tail_breaks
move_prev_find_break:
    jsr source_read_byte_at_line_start_ptr
    bcc :+
    jmp move_prev_found
:
    cmp #$0A
    beq move_prev_after_break
    cmp #$0D
    beq move_prev_after_break
    lda line_start_ptr
    ora line_start_ptr+1
    beq move_prev_found
    jsr dec_line_start_ptr
    jmp move_prev_find_break
move_prev_after_break:
    jsr inc_line_start_ptr
move_prev_skip_breaks_forward:
    jsr source_read_byte_at_line_start_ptr
    bcc :+
    jmp move_prev_found
:
    cmp #$0A
    beq move_prev_skip_forward_one
    cmp #$0D
    beq move_prev_skip_forward_one
    jmp move_prev_found
move_prev_skip_forward_one:
    jsr inc_line_start_ptr
    jmp move_prev_skip_breaks_forward
move_prev_found:
    clc
    rts
move_prev_fail:
    sec
    rts

advance_ptr_to_next_line:
advance_ptr_to_next_line_loop:
    jsr source_read_byte_at_status_ptr
    bcc :+
    jmp advance_ptr_to_next_line_done
:
    beq advance_ptr_to_next_line_done
    cmp #$0D
    beq advance_ptr_skip_breaks
    cmp #$0A
    beq advance_ptr_skip_breaks
    jsr inc_status_ptr
    jmp advance_ptr_to_next_line_loop
advance_ptr_skip_breaks:
advance_ptr_skip_breaks_loop:
    jsr source_read_byte_at_status_ptr
    bcc :+
    rts
:
    cmp #$0D
    beq advance_ptr_skip_break_char
    cmp #$0A
    beq advance_ptr_skip_break_char
    rts
advance_ptr_skip_break_char:
    jsr inc_status_ptr
    jmp advance_ptr_skip_breaks_loop
advance_ptr_to_next_line_done:
    rts

calc_row_ptr:
    tay
    lda base_ptr
    clc
    adc row_offset_lo,y
    sta row_ptr
    lda base_ptr+1
    adc row_offset_hi,y
    sta row_ptr+1
    txa
    clc
    adc row_ptr
    sta row_ptr
    bcc :+
    inc row_ptr+1
:   rts

draw_const_string_at:
    sta const_ptr
    sty const_ptr+1
    lda const_ptr
    sta text_ptr
    lda const_ptr+1
    sta text_ptr+1
    lda #SCREEN_COLS
    sec
    sbc current_col
    sta draw_limit
    lda current_row
    ldx current_col
    jsr calc_row_ptr
    ldy #$00
draw_const_string_loop:
    cpy draw_limit
    bcs draw_const_string_done
    lda (text_ptr),y
    beq draw_const_string_done
    jsr ascii_to_screen
    sta (row_ptr),y
    iny
    cpy #SCREEN_COLS
    bcs draw_const_string_done
    jmp draw_const_string_loop
draw_const_string_done:
    rts

.if ACTDBG_KEEP_OPTIONAL_UI_RESIDENT_FALLBACK
draw_variable_summaries:
    lda #GLOBAL_ROW
    sta current_row
    lda #$00
    sta current_col
    lda #<globals_prefix
    ldy #>globals_prefix
    jsr draw_const_string_at
    lda #GLOBAL_ROW
    sta current_row
    lda #$03
    sta current_col
    lda #<actdbg_global_summary
    ldy #>actdbg_global_summary
    jsr draw_const_string_at

    lda #PARAM_ROW
    sta current_row
    lda #$00
    sta current_col
    lda #<params_prefix
    ldy #>params_prefix
    jsr draw_const_string_at
    lda #PARAM_ROW
    sta current_row
    lda #$03
    sta current_col
    lda #<actdbg_param_summary
    ldy #>actdbg_param_summary
    jsr draw_const_string_at

    lda #LOCAL_ROW
    sta current_row
    lda #$00
    sta current_col
    lda #<locals_prefix
    ldy #>locals_prefix
    jsr draw_const_string_at
    lda #LOCAL_ROW
    sta current_row
    lda #$03
    sta current_col
    lda #<actdbg_local_summary
    ldy #>actdbg_local_summary
    jmp draw_const_string_at

draw_backtrace_details:
    lda #GLOBAL_ROW
    sta current_row
    lda #$00
    sta current_col
    lda #<trace0_prefix
    ldy #>trace0_prefix
    jsr draw_const_string_at
    lda #GLOBAL_ROW
    sta current_row
    lda #$03
    sta current_col
    lda #<actdbg_trace_summary0
    ldy #>actdbg_trace_summary0
    jsr draw_const_string_at

    lda #PARAM_ROW
    sta current_row
    lda #$00
    sta current_col
    lda #<trace1_prefix
    ldy #>trace1_prefix
    jsr draw_const_string_at
    lda #PARAM_ROW
    sta current_row
    lda #$03
    sta current_col
    lda #<actdbg_trace_summary1
    ldy #>actdbg_trace_summary1
    jsr draw_const_string_at

    lda #LOCAL_ROW
    sta current_row
    lda #$00
    sta current_col
    lda #<trace2_prefix
    ldy #>trace2_prefix
    jsr draw_const_string_at
    lda #LOCAL_ROW
    sta current_row
    lda #$03
    sta current_col
    lda #<actdbg_trace_summary2
    ldy #>actdbg_trace_summary2
    jmp draw_const_string_at

draw_breakpoint_list:
    lda #GLOBAL_ROW
    sta current_row
    lda #$00
    sta current_col
    lda #<trace0_prefix
    ldy #>trace0_prefix
    jsr draw_const_string_at
    lda #GLOBAL_ROW
    sta current_row
    lda #$03
    sta current_col
    lda #<actdbg_trace_summary0
    ldy #>actdbg_trace_summary0
    jsr draw_const_string_at

    lda #PARAM_ROW
    sta current_row
    lda #$00
    sta current_col
    lda #<trace1_prefix
    ldy #>trace1_prefix
    jsr draw_const_string_at
    lda #PARAM_ROW
    sta current_row
    lda #$03
    sta current_col
    lda #<actdbg_trace_summary1
    ldy #>actdbg_trace_summary1
    jsr draw_const_string_at

    lda #LOCAL_ROW
    sta current_row
    lda #$00
    sta current_col
    lda #<trace2_prefix
    ldy #>trace2_prefix
    jsr draw_const_string_at
    lda #LOCAL_ROW
    sta current_row
    lda #$03
    sta current_col
    lda #<actdbg_trace_summary2
    ldy #>actdbg_trace_summary2
    jmp draw_const_string_at
.endif

token_scan_begin:
    lda #<line_buffer
    sta text_ptr
    lda #>line_buffer
    sta text_ptr+1
    rts

token_skip_forward:
    ldy #$00
token_skip_forward_chars:
    lda (text_ptr),y
    beq token_skip_forward_done
    cmp #' '
    beq token_skip_forward_spaces
    inc text_ptr
    bne token_skip_forward_chars
    inc text_ptr+1
    jmp token_skip_forward_chars
token_skip_forward_spaces:
    inc text_ptr
    bne token_skip_forward_spaces_scan
    inc text_ptr+1
token_skip_forward_spaces_scan:
    ldy #$00
    lda (text_ptr),y
    cmp #' '
    beq token_skip_forward_spaces
    rts
token_skip_forward_done:
    rts

token_copy_to_buffer:
    sta const_ptr
    sty const_ptr+1
    ldx #$00
token_copy_loop:
    ldy #$00
    lda (text_ptr),y
    beq token_copy_done
    cmp #' '
    beq token_copy_done
    cpx token_copy_limit
    bcs token_copy_skip
    sta (const_ptr),y
    inc const_ptr
    bne :+
    inc const_ptr+1
:
token_copy_skip:
    inc text_ptr
    bne :+
    inc text_ptr+1
:   inx
    jmp token_copy_loop
token_copy_done:
    ldy #$00
    lda #$00
    sta (const_ptr),y
    jsr token_skip_forward
    rts

append_current_token_to_summary:
    sta const_ptr
    sty const_ptr+1
    ldx #$00
append_summary_seek_end:
    ldy #$00
    lda (const_ptr),y
    beq append_summary_found_end
    inx
    cpx #SUMMARY_LIMIT
    bcs append_summary_skip_token
    inc const_ptr
    bne :+
    inc const_ptr+1
:   jmp append_summary_seek_end

append_summary_found_end:
    cpx #$00
    beq append_summary_copy_name
    cpx #SUMMARY_LIMIT-2
    bcs append_summary_skip_token
    lda #','
    sta (const_ptr),y
    inc const_ptr
    bne :+
    inc const_ptr+1
:   inx
    ldy #$00
    lda #' '
    sta (const_ptr),y
    inc const_ptr
    bne :+
    inc const_ptr+1
:   inx

append_summary_copy_name:
    ldy #$00
append_summary_copy_loop:
    lda (text_ptr),y
    beq append_summary_done
    cmp #' '
    beq append_summary_done
    cpx #SUMMARY_LIMIT
    bcs append_summary_skip_char
    sta (const_ptr),y
    inc const_ptr
    bne :+
    inc const_ptr+1
:   inx
append_summary_skip_char:
    inc text_ptr
    bne :+
    inc text_ptr+1
:   jmp append_summary_copy_loop

append_summary_done:
    ldy #$00
    lda #$00
    sta (const_ptr),y
    jsr token_skip_forward
    rts

append_summary_skip_token:
    jsr token_skip_forward
    rts

parse_current_var_summary_fields:
    jsr token_parse_u16
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_live_var_addr_lo
    lda status_ptr+1
    sta actdbg_live_var_addr_hi
    jsr token_parse_u16
    lda status_ptr
    sta actdbg_live_var_width
    jsr token_parse_u16
    jsr token_parse_u16
    jsr token_parse_u16
    rts

append_current_live_var_name_and_value_to_summary:
    sta const_ptr
    sty const_ptr+1
    jsr prepare_summary_append
    bcc :+
    rts
:
    ldx #$00
    jsr seek_text_ptr_to_tail_token

append_live_var_summary_name_loop:
    ldy #$00
    lda (text_ptr),y
    beq append_live_var_summary_value
    cmp #' '
    beq append_live_var_summary_value
    jsr append_summary_char_a
    inc text_ptr
    bne :+
    inc text_ptr+1
:   jmp append_live_var_summary_name_loop

append_live_var_summary_value:
    lda #'='
    jsr append_summary_char_a
    jsr append_live_var_value_to_summary
append_live_var_summary_finish:
    ldy #$00
    lda #$00
    sta (const_ptr),y
    rts

seek_text_ptr_to_tail_token:
    lda #<line_buffer
    sta text_ptr
    lda #>line_buffer
    sta text_ptr+1
seek_text_ptr_to_tail_end:
    ldy #$00
    lda (text_ptr),y
    beq seek_text_ptr_to_tail_back
    inc text_ptr
    bne seek_text_ptr_to_tail_end
    inc text_ptr+1
    jmp seek_text_ptr_to_tail_end
seek_text_ptr_to_tail_back:
    lda text_ptr
    bne :+
    dec text_ptr+1
:   dec text_ptr
seek_text_ptr_to_tail_skip_spaces:
    ldy #$00
    lda (text_ptr),y
    cmp #' '
    bne seek_text_ptr_to_tail_find_start
    lda text_ptr
    bne :+
    dec text_ptr+1
:   dec text_ptr
    jmp seek_text_ptr_to_tail_skip_spaces
seek_text_ptr_to_tail_find_start:
    lda text_ptr
    cmp #<line_buffer
    bne :+
    lda text_ptr+1
    cmp #>line_buffer
    beq seek_text_ptr_to_tail_done
:   lda text_ptr
    sta status_ptr
    lda text_ptr+1
    sta status_ptr+1
    lda status_ptr
    bne :+
    dec status_ptr+1
:   dec status_ptr
    ldy #$00
    lda (status_ptr),y
    cmp #' '
    beq seek_text_ptr_to_tail_done
    lda status_ptr
    sta text_ptr
    lda status_ptr+1
    sta text_ptr+1
    jmp seek_text_ptr_to_tail_find_start
seek_text_ptr_to_tail_done:
    rts

prepare_summary_append:
    ldx #$00
prepare_summary_seek_end:
    ldy #$00
    lda (const_ptr),y
    beq prepare_summary_found_end
    inx
    cpx #SUMMARY_LIMIT
    bcs prepare_summary_fail
    inc const_ptr
    bne :+
    inc const_ptr+1
:   jmp prepare_summary_seek_end

prepare_summary_found_end:
    cpx #$00
    beq prepare_summary_ok
    cpx #SUMMARY_LIMIT-2
    bcs prepare_summary_fail
    lda #','
    jsr append_summary_char_a
    lda #' '
    jsr append_summary_char_a
prepare_summary_ok:
    clc
    rts

prepare_summary_fail:
    sec
    rts

append_summary_char_a:
    cpx #SUMMARY_LIMIT
    bcs append_summary_char_done
    ldy #$00
    sta (const_ptr),y
    inc const_ptr
    bne :+
    inc const_ptr+1
:   inx
append_summary_char_done:
    rts

append_cstr_to_summary:
    sta text_ptr
    sty text_ptr+1
append_cstr_to_summary_loop:
    ldy #$00
    lda (text_ptr),y
    beq append_cstr_to_summary_done
    jsr append_summary_char_a
    inc text_ptr
    bne :+
    inc text_ptr+1
:   jmp append_cstr_to_summary_loop
append_cstr_to_summary_done:
    rts

append_backtrace_separator:
    lda #' '
    jsr append_summary_char_a
    lda #'<'
    jsr append_summary_char_a
    lda #'-'
    jsr append_summary_char_a
    lda #' '
    jmp append_summary_char_a

append_live_var_value_to_summary:
    lda actdbg_live_var_type
    cmp #'b'
    bne :+
    jmp append_live_var_value_byte_decimal
:
    cmp #'c'
    bne :+
    jmp append_live_var_value_card_decimal
:
    cmp #'i'
    bne :+
    jmp append_live_var_value_int_decimal
:
    cmp #'r'
    bne :+
    jmp append_live_var_value_real32
:
    lda actdbg_live_var_width
    cmp #$01
    bne :+
    jmp append_live_var_value_byte
:
    cmp #$02
    bne :+
    jmp append_live_var_value_word
:
    cmp #$04
    bne :+
    jmp append_live_var_value_dword
:
    lda #'?'
    jmp append_summary_char_a

append_live_var_value_byte:
    lda actdbg_live_var_addr_lo
    sta word_tmp
    lda actdbg_live_var_addr_hi
    sta word_tmp+1
    jsr save_summary_cursor
    jsr debug_load_byte_at_word_tmp_to_a
    php
    pha
    jsr restore_summary_cursor
    pla
    plp
    bcc :+
    lda #'?'
    jmp append_summary_char_a
:   pha
    lda #'$'
    jsr append_summary_char_a
    pla
    jmp append_summary_hex_byte_a

append_live_var_value_byte_decimal:
    lda actdbg_live_var_addr_lo
    sta word_tmp
    lda actdbg_live_var_addr_hi
    sta word_tmp+1
    jsr save_summary_cursor
    jsr debug_load_byte_at_word_tmp_to_a
    php
    pha
    jsr restore_summary_cursor
    pla
    plp
    bcc :+
    lda #'?'
    jmp append_summary_char_a
:   sta word_tmp
    lda #$00
    sta word_tmp+1
    jmp append_summary_word_decimal

append_live_var_value_card_decimal:
    lda actdbg_live_var_addr_lo
    sta word_tmp
    lda actdbg_live_var_addr_hi
    sta word_tmp+1
    jsr save_summary_cursor
    jsr debug_load_word_at_word_tmp_offset
    jsr restore_summary_cursor
    bcc :+
    lda #'?'
    jmp append_summary_char_a
:   jmp append_summary_word_decimal

append_live_var_value_int_decimal:
    lda actdbg_live_var_addr_lo
    sta word_tmp
    lda actdbg_live_var_addr_hi
    sta word_tmp+1
    jsr save_summary_cursor
    jsr debug_load_word_at_word_tmp_offset
    jsr restore_summary_cursor
    bcc :+
    lda #'?'
    jmp append_summary_char_a
:   lda word_tmp+1
    bpl :+
    lda #'-'
    jsr append_summary_char_a
    lda word_tmp
    eor #$FF
    sta word_tmp
    lda word_tmp+1
    eor #$FF
    sta word_tmp+1
    clc
    lda word_tmp
    adc #$01
    sta word_tmp
    lda word_tmp+1
    adc #$00
    sta word_tmp+1
:   jmp append_summary_word_decimal

append_live_var_value_real32:
    lda actdbg_live_var_addr_lo
    sta word_tmp
    lda actdbg_live_var_addr_hi
    sta word_tmp+1
    jsr save_summary_cursor
    jsr debug_load_word_at_word_tmp_offset
    jsr restore_summary_cursor
    bcc :+
    lda #'?'
    jmp append_summary_char_a
:   lda word_tmp
    sta actdbg_real_work0
    lda word_tmp+1
    sta actdbg_real_work1
    clc
    lda actdbg_live_var_addr_lo
    adc #$02
    sta word_tmp
    lda actdbg_live_var_addr_hi
    adc #$00
    sta word_tmp+1
    jsr save_summary_cursor
    jsr debug_load_word_at_word_tmp_offset
    jsr restore_summary_cursor
    bcc :+
    lda #'?'
    jmp append_summary_char_a
:   lda word_tmp
    sta actdbg_real_work2
    lda word_tmp+1
    sta actdbg_real_work3

    lda actdbg_real_work3
    and #$80
    sta actdbg_real_sign

    lda actdbg_real_work3
    and #$7F
    asl a
    sta actdbg_real_rawexp
    lda actdbg_real_work2
    and #$80
    beq :+
    inc actdbg_real_rawexp
:   lda actdbg_real_rawexp
    bne append_live_var_value_real_check_special
    lda actdbg_real_work0
    ora actdbg_real_work1
    ora actdbg_real_work2
    and #$7F
    bne append_live_var_value_real_check_special
    jmp append_live_var_value_real_zero
append_live_var_value_real_check_special:
    cmp #$FF
    bne append_live_var_value_real_check_range
    lda actdbg_real_work0
    ora actdbg_real_work1
    ora actdbg_real_work2
    and #$7F
    bne append_live_var_value_real_nan_jump
    jmp append_live_var_value_real_inf
append_live_var_value_real_nan_jump:
    jmp append_live_var_value_real_nan
append_live_var_value_real_check_range:
    cmp #143
    bcc :+
    jmp append_live_var_value_dword
:

    lda actdbg_real_work2
    and #$7F
    ora #$80
    sta actdbg_real_work2
    lda #$00
    sta actdbg_real_work3

    lda actdbg_real_rawexp
    cmp #134
    bcc append_live_var_value_real_shift_right_prepare
    sec
    sbc #134
    sta actdbg_real_shift
    lda actdbg_real_shift
    beq append_live_var_value_real_format
append_live_var_value_real_shift_left_loop:
    asl actdbg_real_work0
    rol actdbg_real_work1
    rol actdbg_real_work2
    rol actdbg_real_work3
    bcc :+
    jmp append_live_var_value_dword
:
    dec actdbg_real_shift
    bne append_live_var_value_real_shift_left_loop
    jmp append_live_var_value_real_format

append_live_var_value_real_shift_right_prepare:
    lda #134
    sec
    sbc actdbg_real_rawexp
    sta actdbg_real_shift
    lda actdbg_real_shift
    cmp #32
    bcc :+
    jmp append_live_var_value_real_zero
:
    beq append_live_var_value_real_format
append_live_var_value_real_shift_right_loop:
    lsr actdbg_real_work3
    ror actdbg_real_work2
    ror actdbg_real_work1
    ror actdbg_real_work0
    dec actdbg_real_shift
    bne append_live_var_value_real_shift_right_loop

append_live_var_value_real_format:
    lda actdbg_real_work0
    ora actdbg_real_work1
    ora actdbg_real_work2
    ora actdbg_real_work3
    bne :+
    jmp append_live_var_value_real_zero
:
    lda actdbg_real_sign
    beq :+
    lda #'-'
    jsr append_summary_char_a
:   lda actdbg_real_work2
    sta word_tmp
    lda actdbg_real_work3
    sta word_tmp+1
    jsr append_summary_word_decimal

    lda actdbg_real_work0
    ora actdbg_real_work1
    bne :+
    lda #'.'
    jsr append_summary_char_a
    lda #'0'
    jmp append_summary_char_a
:   lda actdbg_real_work0
    sta actdbg_real_frac_lo
    lda actdbg_real_work1
    sta actdbg_real_frac_hi
    ldx #$00
append_live_var_value_real_frac_loop:
    cpx #$04
    beq append_live_var_value_real_emit_frac
    jsr actdbg_real_fraction_mul10
    lda actdbg_real_temp2
    clc
    adc #'0'
    sta actdbg_real_digit0,x
    lda actdbg_real_temp0
    sta actdbg_real_frac_lo
    lda actdbg_real_temp1
    sta actdbg_real_frac_hi
    inx
    bne append_live_var_value_real_frac_loop

append_live_var_value_real_emit_frac:
    ldx #$03
:   lda actdbg_real_digit0,x
    cmp #'0'
    bne :+
    dex
    bpl :-
    ldx #$00
    lda #'.'
    jsr append_summary_char_a
    lda #'0'
    jmp append_summary_char_a
:   stx actdbg_real_digit_count
    lda #'.'
    jsr append_summary_char_a
    ldx #$00
append_live_var_value_real_emit_frac_loop:
    lda actdbg_real_digit0,x
    jsr append_summary_char_a
    cpx actdbg_real_digit_count
    beq append_live_var_value_real_done
    inx
    bne append_live_var_value_real_emit_frac_loop
append_live_var_value_real_done:
    rts

append_live_var_value_real_zero:
    lda #'0'
    jsr append_summary_char_a
    lda #'.'
    jsr append_summary_char_a
    lda #'0'
    jmp append_summary_char_a

append_live_var_value_real_inf:
    lda actdbg_real_sign
    beq :+
    lda #'-'
    jsr append_summary_char_a
:   lda #'i'
    jsr append_summary_char_a
    lda #'n'
    jsr append_summary_char_a
    lda #'f'
    jmp append_summary_char_a

append_live_var_value_real_nan:
    lda #'n'
    jsr append_summary_char_a
    lda #'a'
    jsr append_summary_char_a
    lda #'n'
    jmp append_summary_char_a

actdbg_real_fraction_mul10:
    lda #$00
    sta actdbg_real_temp0
    sta actdbg_real_temp1
    sta actdbg_real_temp2
    ldy #10
:   clc
    lda actdbg_real_temp0
    adc actdbg_real_frac_lo
    sta actdbg_real_temp0
    lda actdbg_real_temp1
    adc actdbg_real_frac_hi
    sta actdbg_real_temp1
    lda actdbg_real_temp2
    adc #$00
    sta actdbg_real_temp2
    dey
    bne :-
    rts

append_live_var_value_word:
    lda actdbg_live_var_addr_lo
    sta word_tmp
    lda actdbg_live_var_addr_hi
    sta word_tmp+1
    jsr save_summary_cursor
    jsr debug_load_word_at_word_tmp_offset
    jsr restore_summary_cursor
    bcc :+
    lda #'?'
    jmp append_summary_char_a
:   lda #'$'
    jsr append_summary_char_a
    lda word_tmp+1
    jsr append_summary_hex_byte_a
    lda word_tmp
    jmp append_summary_hex_byte_a

append_live_var_value_dword:
    lda actdbg_live_var_addr_lo
    sta word_tmp
    lda actdbg_live_var_addr_hi
    sta word_tmp+1
    jsr save_summary_cursor
    jsr debug_load_word_at_word_tmp_offset
    jsr restore_summary_cursor
    bcc :+
    lda #'?'
    jmp append_summary_char_a
:   lda word_tmp
    sta line_number_lo
    lda word_tmp+1
    sta line_number_hi
    clc
    lda actdbg_live_var_addr_lo
    adc #$02
    sta word_tmp
    lda actdbg_live_var_addr_hi
    adc #$00
    sta word_tmp+1
    jsr save_summary_cursor
    jsr debug_load_word_at_word_tmp_offset
    jsr restore_summary_cursor
    bcc :+
    lda #'?'
    jmp append_summary_char_a
:   lda #'$'
    jsr append_summary_char_a
    lda word_tmp+1
    jsr append_summary_hex_byte_a
    lda word_tmp
    jsr append_summary_hex_byte_a
    lda line_number_hi
    jsr append_summary_hex_byte_a
    lda line_number_lo
    jmp append_summary_hex_byte_a

append_summary_hex_byte_a:
    sta hex_tmp
    lsr a
    lsr a
    lsr a
    lsr a
    jsr append_summary_hex_nibble
    lda hex_tmp
    and #$0F
    jmp append_summary_hex_nibble

append_summary_hex_nibble:
    cmp #$0A
    bcc append_summary_hex_digit
    clc
    adc #('a'-10)
    jmp append_summary_char_a
append_summary_hex_digit:
    clc
    adc #'0'
    jmp append_summary_char_a

append_summary_word_decimal:
    lda #$00
    sta digit_flag
    sta summary_decimal_index
append_summary_word_decimal_loop:
    lda summary_decimal_index
    cmp #$04
    beq append_summary_word_decimal_ones
    jsr append_summary_word_decimal_digit_divisor
    inc summary_decimal_index
    bne append_summary_word_decimal_loop
append_summary_word_decimal_ones:
    lda word_tmp
    clc
    adc #'0'
    jmp append_summary_char_a

append_summary_word_decimal_digit_divisor:
    lda summary_decimal_index
    tay
    lda #$00
    sta hex_tmp
append_summary_word_decimal_sub_loop:
    lda word_tmp+1
    cmp decimal_divisors_hi,y
    bcc append_summary_word_decimal_digit_done
    bne :+
    lda word_tmp
    cmp decimal_divisors_lo,y
    bcc append_summary_word_decimal_digit_done
:   sec
    lda word_tmp
    sbc decimal_divisors_lo,y
    sta word_tmp
    lda word_tmp+1
    sbc decimal_divisors_hi,y
    sta word_tmp+1
    inc hex_tmp
    bne append_summary_word_decimal_sub_loop
append_summary_word_decimal_digit_done:
    lda digit_flag
    bne append_summary_word_decimal_emit_digit
    lda hex_tmp
    beq append_summary_word_decimal_skip_digit
append_summary_word_decimal_emit_digit:
    lda hex_tmp
    clc
    adc #'0'
    jsr append_summary_char_a
    lda #$01
    sta digit_flag
append_summary_word_decimal_skip_digit:
    rts

save_summary_cursor:
    txa
    sta actdbg_live_summary_len
    lda const_ptr
    sta actdbg_live_summary_ptr_lo
    lda const_ptr+1
    sta actdbg_live_summary_ptr_hi
    rts

restore_summary_cursor:
    lda actdbg_live_summary_ptr_lo
    sta const_ptr
    lda actdbg_live_summary_ptr_hi
    sta const_ptr+1
    lda actdbg_live_summary_len
    tax
    rts

copy_const_to_ptr:
    sta const_ptr
    sty const_ptr+1
    ldx #$00
copy_const_to_ptr_loop:
    ldy #$00
    lda (const_ptr),y
    sta (text_ptr),y
    beq copy_const_to_ptr_done
    inc const_ptr
    bne :+
    inc const_ptr+1
:   inc text_ptr
    bne copy_const_to_ptr_loop
    inc text_ptr+1
    jmp copy_const_to_ptr_loop
copy_const_to_ptr_done:
    rts

append_const_to_ptr:
    sta const_ptr
    sty const_ptr+1
    ldy #$00
append_seek_end:
    lda (text_ptr),y
    beq append_copy
    inc text_ptr
    bne append_seek_end
    inc text_ptr+1
    jmp append_seek_end
append_copy:
append_copy_loop:
    ldy #$00
    lda (const_ptr),y
    sta (text_ptr),y
    beq append_copy_done
    inc const_ptr
    bne :+
    inc const_ptr+1
:   inc text_ptr
    bne append_copy_loop
    inc text_ptr+1
    jmp append_copy_loop
append_copy_done:
    rts

derive_dbg_path_from_prg:
    lda #<actdbg_dbg_path
    sta text_ptr
    lda #>actdbg_dbg_path
    sta text_ptr+1
    lda #<actdbg_prg_path
    ldy #>actdbg_prg_path
    jsr copy_const_to_ptr
    ldy #$00
    sty status_ptr
    sty status_ptr+1
derive_dbg_scan:
    lda actdbg_dbg_path,y
    beq derive_dbg_found_end
    cmp #'.'
    bne derive_dbg_next
    sty status_ptr
derive_dbg_next:
    iny
    cpy #PATH_LIMIT
    bcc derive_dbg_scan
derive_dbg_found_end:
    lda status_ptr
    beq derive_dbg_append
    tay
    lda #'.'
    sta actdbg_dbg_path,y
    iny
    lda #'D'
    sta actdbg_dbg_path,y
    iny
    lda #'B'
    sta actdbg_dbg_path,y
    iny
    lda #'G'
    sta actdbg_dbg_path,y
    iny
    lda #$00
    sta actdbg_dbg_path,y
    rts
derive_dbg_append:
    lda #<actdbg_dbg_path
    sta text_ptr
    lda #>actdbg_dbg_path
    sta text_ptr+1
    lda #<suffix_dbg
    ldy #>suffix_dbg
    jmp append_const_to_ptr

derive_project_root_from_prg:
    lda #$00
    sta actdbg_project_root
    ldy #$00
    sty status_ptr
copy_parent_scan:
    lda actdbg_prg_path,y
    beq copy_parent_done
    cmp #'/'
    beq copy_parent_mark
    cmp #$5C
    beq copy_parent_mark
    iny
    cpy #PATH_LIMIT
    bcc copy_parent_scan
    bcs copy_parent_done
copy_parent_mark:
    sty status_ptr
    iny
    cpy #PATH_LIMIT
    bcc copy_parent_scan
copy_parent_done:
    lda status_ptr
    beq derive_project_done
    tax
    dex
    txa
    bmi derive_project_done
    ldy #$00
copy_parent_loop:
    cpy status_ptr
    beq copy_parent_term
    lda actdbg_prg_path,y
    sta actdbg_project_root,y
    iny
    bne copy_parent_loop
copy_parent_term:
    lda #$00
    sta actdbg_project_root,y
    jsr trim_bin_suffix
derive_project_done:
    rts

trim_bin_suffix:
    ldy #$00
trim_bin_len_loop:
    lda actdbg_project_root,y
    beq trim_bin_check
    iny
    cpy #PATH_LIMIT
    bcc trim_bin_len_loop
trim_bin_check:
    cpy #3
    bcc trim_bin_done
    lda actdbg_project_root+0
    and #$DF
    cmp #'B'
    bne trim_bin_path_check
    lda actdbg_project_root+1
    and #$DF
    cmp #'I'
    bne trim_bin_path_check
    lda actdbg_project_root+2
    and #$DF
    cmp #'N'
    bne trim_bin_path_check
    cpy #3
    bne trim_bin_path_check
    lda #$00
    sta actdbg_project_root
    rts
trim_bin_path_check:
    cpy #4
    bcc trim_bin_done
    lda actdbg_project_root-4,y
    cmp #'/'
    beq trim_bin_match
    cmp #$5C
    bne trim_bin_done
trim_bin_match:
    lda actdbg_project_root-3,y
    and #$DF
    cmp #'B'
    bne trim_bin_done
    lda actdbg_project_root-2,y
    and #$DF
    cmp #'I'
    bne trim_bin_done
    lda actdbg_project_root-1,y
    and #$DF
    cmp #'N'
    bne trim_bin_done
    lda #$00
    sta actdbg_project_root-4,y
trim_bin_done:
    rts

derive_module_name_fallback:
    lda actdbg_module_name
    bne derive_module_done
    jsr arg_has_dot
    bcc derive_from_arg
    ldy #$00
    sty status_ptr
    sty status_ptr+1
module_from_path_scan:
    lda actdbg_prg_path,y
    beq module_from_path_copy
    cmp #'/'
    beq module_from_path_mark
    cmp #$5C
    beq module_from_path_mark
    cmp #'.'
    beq module_from_path_ext
    iny
    cpy #PATH_LIMIT
    bcc module_from_path_scan
    bcs module_from_path_copy
module_from_path_mark:
    iny
    sty status_ptr
    jmp module_from_path_scan
module_from_path_ext:
    sty status_ptr+1
module_from_path_copy:
    ldx #$00
    ldy status_ptr
module_from_path_copy_loop:
    cpy status_ptr+1
    beq module_from_path_done
    lda actdbg_prg_path,y
    beq module_from_path_done
    cpx #MODULE_LIMIT
    bcs module_from_path_done
    sta actdbg_module_name,x
    inx
    iny
    bne module_from_path_copy_loop
module_from_path_done:
    lda #$00
    sta actdbg_module_name,x
    rts
derive_from_arg:
    ldy #$00
module_from_arg_loop:
    lda arg_buffer,y
    beq module_from_arg_done
    cpy #MODULE_LIMIT
    bcs module_from_arg_done
    sta actdbg_module_name,y
    iny
    bne module_from_arg_loop
module_from_arg_done:
    lda #$00
    sta actdbg_module_name,y
derive_module_done:
    rts

token_parse_u16:
    lda #$00
    sta status_ptr
    sta status_ptr+1
token_parse_loop:
    ldy #$00
    lda (text_ptr),y
    beq token_parse_done
    cmp #' '
    beq token_parse_done
    sec
    sbc #'0'
    bcc token_parse_skip
    cmp #10
    bcs token_parse_skip
    pha
    lda status_ptr
    sta line_number_lo
    lda status_ptr+1
    sta line_number_hi
    asl line_number_lo
    rol line_number_hi
    asl status_ptr
    rol status_ptr+1
    asl status_ptr
    rol status_ptr+1
    asl status_ptr
    rol status_ptr+1
    lda status_ptr
    clc
    adc line_number_lo
    sta status_ptr
    lda status_ptr+1
    adc line_number_hi
    sta status_ptr+1
    pla
    clc
    adc status_ptr
    sta status_ptr
    lda status_ptr+1
    adc #$00
    sta status_ptr+1
token_parse_skip:
    inc text_ptr
    bne token_parse_loop
    inc text_ptr+1
    jmp token_parse_loop
token_parse_done:
    jsr token_skip_forward
    rts

inc_scan_ptr:
    inc scan_ptr
    bne :+
    inc scan_ptr+1
:   rts

skip_newline_chars:
skip_newline_chars_loop:
    jsr dbg_read_byte_at_scan_ptr
    bcc :+
    rts
:
    cmp #$0D
    beq skip_newline_one
    cmp #$0A
    beq skip_newline_one
    rts
skip_newline_one:
    jsr inc_scan_ptr
    jmp skip_newline_chars_loop

inc_status_ptr:
    inc status_ptr
    bne :+
    inc status_ptr+1
:   rts

dec_line_start_ptr:
    lda line_start_ptr
    bne :+
    dec line_start_ptr+1
:   dec line_start_ptr
    rts

inc_line_start_ptr:
    inc line_start_ptr
    bne :+
    inc line_start_ptr+1
:   rts

set_active_dbg_file:
    lda #ACTDBG_FILE_KIND_DBG
    sta actdbg_active_file_kind
    rts

set_active_source_file:
    lda #ACTDBG_FILE_KIND_SOURCE
    sta actdbg_active_file_kind
    rts

dbg_read_byte_at_scan_ptr:
    lda scan_ptr
    sta line_length_ptr
    lda scan_ptr+1
    sta line_length_ptr+1
    jmp read_active_file_byte_at_line_length_ptr

source_read_byte_at_status_ptr:
    lda status_ptr
    sta line_length_ptr
    lda status_ptr+1
    sta line_length_ptr+1
    jmp read_active_file_byte_at_line_length_ptr

source_read_byte_at_line_start_ptr:
    lda line_start_ptr
    sta line_length_ptr
    lda line_start_ptr+1
    sta line_length_ptr+1
    jmp read_active_file_byte_at_line_length_ptr

copy_source_line_to_buffer_from_line_work_ptr:
    lda line_work_ptr
    sta line_length_ptr
    lda line_work_ptr+1
    sta line_length_ptr+1
    ldx #$00
copy_source_line_loop:
    jsr read_active_file_byte_at_line_length_ptr
    bcc :+
    jmp copy_source_line_done
:
    beq copy_source_line_done
    cmp #$0D
    beq copy_source_line_done
    cmp #$0A
    beq copy_source_line_done
    cpx #LINE_BUFFER_LIMIT
    bcs copy_source_line_skip_store
    sta line_buffer,x
    inx
copy_source_line_skip_store:
    inc line_length_ptr
    bne copy_source_line_loop
    inc line_length_ptr+1
    jmp copy_source_line_loop
copy_source_line_done:
    lda #$00
    sta line_buffer,x
    rts

read_active_file_byte_at_line_length_ptr:
    lda actdbg_active_file_kind
    cmp actdbg_file_window_kind
    bne refill_active_file_window
    lda line_length_ptr+1
    cmp actdbg_file_window_start_hi
    bcc refill_active_file_window
    bne :+
    lda line_length_ptr
    cmp actdbg_file_window_start_lo
    bcc refill_active_file_window
:
    lda line_length_ptr+1
    cmp actdbg_file_window_end_hi
    bcc read_active_file_byte_from_window
    bne refill_active_file_window
    lda line_length_ptr
    cmp actdbg_file_window_end_lo
    bcc read_active_file_byte_from_window
refill_active_file_window:
    jsr refill_active_file_window_from_line_length_ptr
    bcc read_active_file_byte_from_window
    sec
    rts

read_active_file_byte_from_window:
    sec
    lda line_length_ptr
    sbc actdbg_file_window_start_lo
    tay
    lda actdbg_file_window,y
    clc
    rts

refill_active_file_window_from_line_length_ptr:
    lda actdbg_active_file_kind
    cmp #ACTDBG_FILE_KIND_DBG
    beq refill_dbg_file_window
    cmp #ACTDBG_FILE_KIND_SOURCE
    beq refill_source_file_window
    sec
    rts

refill_dbg_file_window:
    sec
    lda actdbg_dbg_stage_len_lo
    sbc line_length_ptr
    sta word_tmp
    lda actdbg_dbg_stage_len_hi
    sbc line_length_ptr+1
    sta word_tmp+1
    bcc :+
    lda word_tmp
    ora word_tmp+1
    bne :++
:   jmp refill_active_file_window_fail
:
    clc
    lda #ACTDBG_DBG_REU_BASE_LO
    adc line_length_ptr
    sta file_params+0
    lda #ACTDBG_DBG_REU_BASE_HI
    adc line_length_ptr+1
    sta file_params+1
    lda #ACTDBG_DBG_REU_BASE_BANK
    adc #$00
    sta file_params+2
    jmp refill_active_file_window_finish_setup

refill_source_file_window:
    sec
    lda actdbg_source_stage_len_lo
    sbc line_length_ptr
    sta word_tmp
    lda actdbg_source_stage_len_hi
    sbc line_length_ptr+1
    sta word_tmp+1
    bcc :+
    lda word_tmp
    ora word_tmp+1
    bne :++
:   jmp refill_active_file_window_fail
:
    clc
    lda #ACTDBG_SOURCE_REU_BASE_LO
    adc line_length_ptr
    sta file_params+0
    lda #ACTDBG_SOURCE_REU_BASE_HI
    adc line_length_ptr+1
    sta file_params+1
    lda #ACTDBG_SOURCE_REU_BASE_BANK
    adc #$00
    sta file_params+2

refill_active_file_window_finish_setup:
    lda #<actdbg_file_window
    sta file_params+3
    lda #>actdbg_file_window
    sta file_params+4
    lda word_tmp+1
    bne refill_active_file_window_use_limit
    lda word_tmp
    cmp #ACTDBG_FILE_WINDOW_LIMIT
    bcc refill_active_file_window_use_remaining
refill_active_file_window_use_limit:
    lda #ACTDBG_FILE_WINDOW_LIMIT
refill_active_file_window_use_remaining:
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr actdbg_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    bne refill_active_file_window_fail
    lda actdbg_active_file_kind
    sta actdbg_file_window_kind
    lda line_length_ptr
    sta actdbg_file_window_start_lo
    lda line_length_ptr+1
    sta actdbg_file_window_start_hi
    clc
    lda line_length_ptr
    adc file_params+5
    sta actdbg_file_window_end_lo
    lda line_length_ptr+1
    adc #$00
    sta actdbg_file_window_end_hi
    clc
    rts

refill_active_file_window_fail:
    sec
    rts

ascii_to_screen:
    cmp #'a'
    bcc ascii_to_screen_check_upper
    cmp #'z'+1
    bcs ascii_to_screen_check_upper
    and #$DF
ascii_to_screen_check_upper:
    cmp #'A'
    bcc ascii_to_screen_done
    cmp #'Z'+1
    bcs ascii_to_screen_done
    sec
    sbc #$40
ascii_to_screen_done:
    rts

debug_step_instruction:
    lda #ACTDBG_OVERLAY_CMD_EXEC_STEP
    jmp actdbg_overlay_run_command

debug_continue_execution:
    lda #ACTDBG_OVERLAY_CMD_EXEC_CONTINUE
    jmp actdbg_overlay_run_command

debug_step_over_execution:
    lda #ACTDBG_OVERLAY_CMD_EXEC_STEP_OVER
    jmp actdbg_overlay_run_command

debug_step_out_execution:
    lda #ACTDBG_OVERLAY_CMD_EXEC_STEP_OUT
    jmp actdbg_overlay_run_command

debug_load_byte_at_word_tmp_to_a:
    lda #$01
    jsr debug_read_target_to_fetch_len_a
    bcc :+
    sec
    rts
:   lda actdbg_target_fetch_buffer+0
    clc
    rts

debug_load_word_at_word_tmp_offset:
    lda #$02
    jsr debug_read_target_to_fetch_len_a
    bcc :+
    sec
    rts
:   lda actdbg_target_fetch_buffer+0
    sta word_tmp
    lda actdbg_target_fetch_buffer+1
    sta word_tmp+1
    clc
    rts

debug_read_target_to_fetch_len_a:
    sta actdbg_target_read_len
    lda actdbg_native_target_valid
    beq debug_read_staged_prg
    sec
    lda word_tmp
    sbc #$02
    sta file_params+0
    lda word_tmp+1
    sbc #$00
    sta file_params+1
    bcs :+
    jmp debug_read_target_fail
:
    lda #ACTDBG_TARGET_REU_BASE_BANK
    sta file_params+2
    jmp debug_read_target_common

debug_read_staged_prg:
    sec
    lda word_tmp
    sbc actdbg_prg_header+0
    sta actdbg_room_check_lo
    lda word_tmp+1
    sbc actdbg_prg_header+1
    sta actdbg_room_check_hi
    bcc debug_read_target_fail
    clc
    lda actdbg_room_check_lo
    adc actdbg_target_read_len
    sta status_ptr
    lda actdbg_room_check_hi
    adc #$00
    sta status_ptr+1
    bcs debug_read_target_fail
    sec
    lda actdbg_prg_stage_len_lo
    sbc #$02
    sta file_params+0
    lda actdbg_prg_stage_len_hi
    sbc #$00
    sta file_params+1
    lda status_ptr+1
    cmp file_params+1
    bcc debug_read_staged_prg_room_ok
    bne debug_read_target_fail
    lda status_ptr
    cmp file_params+0
    bcc debug_read_staged_prg_room_ok
    bne debug_read_target_fail
debug_read_staged_prg_room_ok:
    clc
    lda actdbg_room_check_lo
    adc #$02
    sta file_params+0
    lda actdbg_room_check_hi
    adc #$00
    sta file_params+1
    lda #ACTDBG_PRG_REU_BASE_BANK
    adc #$00
    sta file_params+2

debug_read_target_common:
    lda #<actdbg_target_fetch_buffer
    sta file_params+3
    lda #>actdbg_target_fetch_buffer
    sta file_params+4
    lda actdbg_target_read_len
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr actdbg_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq debug_read_target_ok
debug_read_target_fail:
    sec
    rts
debug_read_target_ok:
    clc
    rts

actdbg_save_zp_state:
    ldx #$00
actdbg_save_zp_state_loop:
    lda $00E0,x
    sta actdbg_zp_save,x
    inx
    cpx #$20
    bcc actdbg_save_zp_state_loop
    rts

actdbg_restore_zp_state:
    ldx #$00
actdbg_restore_zp_state_loop:
    lda actdbg_zp_save,x
    sta $00E0,x
    inx
    cpx #$20
    bcc actdbg_restore_zp_state_loop
    rts

actdbg_restore_service_status:
    lda actdbg_service_status
    pha
    plp
    rts

actdbg_svc_program_get_cmdline_len:
    jsr actdbg_save_zp_state
    ldx #svc_retptr
    jsr svc_program_get_cmdline_len
    php
    pla
    sta actdbg_service_status
    lda svc_retptr
    sta actdbg_service_out+0
    lda svc_retptr+1
    sta actdbg_service_out+1
    jsr actdbg_restore_zp_state
    lda actdbg_service_out+0
    sta svc_retptr
    lda actdbg_service_out+1
    sta svc_retptr+1
    jmp actdbg_restore_service_status

actdbg_svc_program_get_cmdline_ptr:
    jsr actdbg_save_zp_state
    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    php
    pla
    sta actdbg_service_status
    lda svc_retptr
    sta actdbg_service_out+0
    lda svc_retptr+1
    sta actdbg_service_out+1
    jsr actdbg_restore_zp_state
    lda actdbg_service_out+0
    sta svc_retptr
    lda actdbg_service_out+1
    sta svc_retptr+1
    jmp actdbg_restore_service_status

actdbg_svc_program_chain_sc0:
    jsr actdbg_save_zp_state
    ldx #svc_retptr
    jsr svc_program_chain_sc0
    jmp actdbg_restore_simple_service

actdbg_svc_file_stage_reu_sc0:
    jsr actdbg_save_zp_state
    ldx #file_params
    jsr svc_file_stage_reu_sc0
    php
    pla
    sta actdbg_service_status
    lda file_params+5
    sta actdbg_service_out+0
    lda file_params+6
    sta actdbg_service_out+1
    lda file_params+7
    sta actdbg_service_out+2
    lda file_params+8
    sta actdbg_service_out+3
    jsr actdbg_restore_zp_state
    lda actdbg_service_out+0
    sta file_params+5
    lda actdbg_service_out+1
    sta file_params+6
    lda actdbg_service_out+2
    sta file_params+7
    lda actdbg_service_out+3
    sta file_params+8
    jmp actdbg_restore_service_status

actdbg_svc_reu_read_sc0:
    jsr actdbg_save_zp_state
    ldx #file_params
    jsr svc_reu_read_sc0
    jmp actdbg_restore_reu_result

actdbg_svc_reu_write_sc0:
    jsr actdbg_save_zp_state
    ldx #file_params
    jsr svc_reu_write_sc0
actdbg_restore_reu_result:
    php
    pla
    sta actdbg_service_status
    lda file_params+7
    sta actdbg_service_out+0
    jsr actdbg_restore_zp_state
    lda actdbg_service_out+0
    sta file_params+7
    jmp actdbg_restore_service_status

actdbg_svc_console_write_sc0:
    jsr actdbg_save_zp_state
    ldx #svc_retptr
    jsr svc_console_write_sc0
    jmp actdbg_restore_simple_service

actdbg_svc_console_newline:
    jsr actdbg_save_zp_state
    jsr svc_console_newline
actdbg_restore_simple_service:
    php
    pla
    sta actdbg_service_status
    jsr actdbg_restore_zp_state
    jmp actdbg_restore_service_status

print_ptr:
    sta svc_retptr
    sty svc_retptr+1
    jmp actdbg_svc_console_write_sc0

msg_usage:
    .asciiz "ACTDBG PROG OR PROG.PRG"
msg_no_prg:
    .asciiz "NO PRG"
msg_bad_prg:
    .asciiz "BAD PRG"
msg_no_dbg:
    .asciiz "NO DBG"
msg_bad_dbg:
    .asciiz "BAD DBG"
msg_no_source:
    .asciiz "NO SOURCE"
msg_source_large:
    .asciiz "SOURCE TOO LARGE"
title_prefix:
    .asciiz "ACTDBG "
proc_prefix:
    .asciiz "PROC: "
backtrace_prefix:
    .asciiz "BT: "
trace0_prefix:
    .asciiz "0: "
trace1_prefix:
    .asciiz "1: "
trace2_prefix:
    .asciiz "2: "
globals_prefix:
    .asciiz "G: "
params_prefix:
    .asciiz "P: "
locals_prefix:
    .asciiz "L: "
help_line:
    .asciiz "F3/4/5/6 F7 B E T Q ARROWS"
edit_handoff_failed_line:
    .asciiz "E: EDIT HANDOFF FAILED"
edit_command_prefix:
    .asciiz "ACTEDIT "
prefix_bin:
    .asciiz "BIN/"
suffix_prg:
    .asciiz ".PRG"
suffix_dbg:
    .asciiz ".DBG"
slash_name:
    .asciiz "/"
actdbg_overlay_optional_ui_path:
    .asciiz "!ACTDBG_OVL1.BIN"
actdbg_overlay_exec_path:
    .asciiz "!ACTDBG_OVL2.BIN"

decimal_divisors_lo:
    .byte <10000,<1000,<100,<10
decimal_divisors_hi:
    .byte >10000,>1000,>100,>10

row_offset_lo:
    .byte <(0*40), <(1*40), <(2*40), <(3*40), <(4*40), <(5*40), <(6*40), <(7*40), <(8*40), <(9*40)
    .byte <(10*40), <(11*40), <(12*40), <(13*40), <(14*40), <(15*40), <(16*40), <(17*40), <(18*40), <(19*40)
    .byte <(20*40), <(21*40), <(22*40), <(23*40), <(24*40)
row_offset_hi:
    .byte >(0*40), >(1*40), >(2*40), >(3*40), >(4*40), >(5*40), >(6*40), >(7*40), >(8*40), >(9*40)
    .byte >(10*40), >(11*40), >(12*40), >(13*40), >(14*40), >(15*40), >(16*40), >(17*40), >(18*40), >(19*40)
    .byte >(20*40), >(21*40), >(22*40), >(23*40), >(24*40)

arg_buffer:
    .res PATH_LIMIT+1
actdbg_prg_path:
    .res PATH_LIMIT+1
actdbg_dbg_path:
    .res PATH_LIMIT+1
source_rel_path:
    .res PATH_LIMIT+1
actdbg_source_path:
    .res PATH_LIMIT+1
actdbg_project_root:
    .res PATH_LIMIT+1
actdbg_module_name:
    .res MODULE_LIMIT+1
actdbg_proc_name:
    .res MODULE_LIMIT+1
actdbg_trace_proc_name:
    .res MODULE_LIMIT+1
line_buffer:
    .res LINE_BUFFER_LIMIT+1
actdbg_have_line_record:
    .res 1
actdbg_target_module_lo:
    .res 1
actdbg_target_module_hi:
    .res 1
actdbg_target_export_lo:
    .res 1
actdbg_target_export_hi:
    .res 1
actdbg_target_file_lo:
    .res 1
actdbg_target_file_hi:
    .res 1
actdbg_target_line_lo:
    .res 1
actdbg_target_line_hi:
    .res 1
actdbg_target_col:
    .res 1
actdbg_cursor_module_lo:
    .res 1
actdbg_cursor_module_hi:
    .res 1
actdbg_cursor_file_lo:
    .res 1
actdbg_cursor_file_hi:
    .res 1
actdbg_cursor_line_lo:
    .res 1
actdbg_cursor_line_hi:
    .res 1
actdbg_cursor_col:
    .res 1
actdbg_source_col_offset:
    .res 1
actdbg_loaded_source_valid:
    .res 1
actdbg_loaded_source_module_lo:
    .res 1
actdbg_loaded_source_module_hi:
    .res 1
actdbg_loaded_source_file_lo:
    .res 1
actdbg_loaded_source_file_hi:
    .res 1
actdbg_lookup_module_lo:
    .res 1
actdbg_lookup_module_hi:
    .res 1
actdbg_lookup_export_lo:
    .res 1
actdbg_lookup_export_hi:
    .res 1
actdbg_lookup_file_lo:
    .res 1
actdbg_lookup_file_hi:
    .res 1
actdbg_lookup_line_lo:
    .res 1
actdbg_lookup_line_hi:
    .res 1
actdbg_lookup_col:
    .res 1
actdbg_lookup_found:
    .res 1
actdbg_nav_found_after:
    .res 1
actdbg_best_proc_found:
    .res 1
actdbg_best_proc_pc_lo:
    .res 1
actdbg_best_proc_pc_hi:
    .res 1
actdbg_best_line_found:
    .res 1
actdbg_best_line_pc_lo:
    .res 1
actdbg_best_line_pc_hi:
    .res 1
actdbg_trace_best_found:
    .res 1
actdbg_trace_best_pc_lo:
    .res 1
actdbg_trace_best_pc_hi:
    .res 1
actdbg_dbg_candidate_module_lo:
    .res 1
actdbg_dbg_candidate_module_hi:
    .res 1
actdbg_dbg_candidate_export_lo:
    .res 1
actdbg_dbg_candidate_export_hi:
    .res 1
actdbg_dbg_candidate_pc_lo:
    .res 1
actdbg_dbg_candidate_pc_hi:
    .res 1
actdbg_dbg_candidate_file_lo:
    .res 1
actdbg_dbg_candidate_file_hi:
    .res 1
actdbg_dbg_candidate_line_lo:
    .res 1
actdbg_dbg_candidate_line_hi:
    .res 1
actdbg_dbg_candidate_col:
    .res 1
actdbg_break_lookup_found:
    .res 1
actdbg_break_lookup_pc_lo:
    .res 1
actdbg_break_lookup_pc_hi:
    .res 1
actdbg_var_scope:
    .res 1
actdbg_view_mode:
    .res 1
actdbg_detail_view:
    .res 1
actdbg_break_list_view:
    .res 1
actdbg_chain_failed:
    .res 1
actdbg_chain_len:
    .res 1
actdbg_chain_command:
    .res 32
actdbg_overlay_requested_cmd:
    .res 1
actdbg_overlay_requested_kind:
    .res 1
actdbg_overlay_ready:
    .res 1
actdbg_overlay_loaded_kind:
    .res 1
actdbg_test_key_count:
    .res 1
actdbg_test_key_index:
    .res 1
actdbg_test_mode:
    .res 1
actdbg_test_keys:
    .res TEST_KEY_LIMIT
actdbg_test_key0 = actdbg_test_keys+0
actdbg_test_key1 = actdbg_test_keys+1
actdbg_test_key2 = actdbg_test_keys+2
actdbg_test_key3 = actdbg_test_keys+3
actdbg_test_key4 = actdbg_test_keys+4
actdbg_test_key5 = actdbg_test_keys+5
actdbg_test_key6 = actdbg_test_keys+6
actdbg_test_key7 = actdbg_test_keys+7
token_copy_limit:
    .res 1
draw_limit:
    .res 1
current_row:
    .res 1
current_col:
    .res 1
copy_dbg_line_index:
    .res 1
actdbg_break_hit:
    .res 1
actdbg_break_active:
    .res BREAKPOINT_MAX
actdbg_break_pc_lo:
    .res BREAKPOINT_MAX
actdbg_break_pc_hi:
    .res BREAKPOINT_MAX
actdbg_break_module_lo:
    .res BREAKPOINT_MAX
actdbg_break_module_hi:
    .res BREAKPOINT_MAX
actdbg_break_file_lo:
    .res BREAKPOINT_MAX
actdbg_break_file_hi:
    .res BREAKPOINT_MAX
actdbg_break_line_lo:
    .res BREAKPOINT_MAX
actdbg_break_line_hi:
    .res BREAKPOINT_MAX
line_number_lo:
    .res 1
line_number_hi:
    .res 1
work_line_lo:
    .res 1
work_line_hi:
    .res 1
word_tmp:
    .res 2
digit_flag:
    .res 1
hex_tmp:
    .res 1
actdbg_live_var_addr_lo:
    .res 1
actdbg_live_var_addr_hi:
    .res 1
actdbg_live_var_width:
    .res 1
actdbg_live_var_type:
    .res 1
summary_decimal_index:
    .res 1
actdbg_real_work0:
    .res 1
actdbg_real_work1:
    .res 1
actdbg_real_work2:
    .res 1
actdbg_real_work3:
    .res 1
actdbg_real_sign:
    .res 1
actdbg_real_rawexp:
    .res 1
actdbg_real_shift:
    .res 1
actdbg_real_frac_lo:
    .res 1
actdbg_real_frac_hi:
    .res 1
actdbg_real_temp0:
    .res 1
actdbg_real_temp1:
    .res 1
actdbg_real_temp2:
    .res 1
actdbg_real_digit0:
    .res 4
actdbg_real_digit_count:
    .res 1
actdbg_live_summary_len:
    .res 1
actdbg_live_summary_ptr_lo:
    .res 1
actdbg_live_summary_ptr_hi:
    .res 1
actdbg_room_check_lo:
    .res 1
actdbg_room_check_hi:
    .res 1
actdbg_prg_stage_len_lo:
    .res 1
actdbg_prg_stage_len_hi:
    .res 1
actdbg_prg_stage_len_bank:
    .res 1
actdbg_dbg_stage_len_lo:
    .res 1
actdbg_dbg_stage_len_hi:
    .res 1
actdbg_dbg_stage_len_bank:
    .res 1
actdbg_source_stage_len_lo:
    .res 1
actdbg_source_stage_len_hi:
    .res 1
actdbg_source_stage_len_bank:
    .res 1
actdbg_overlay_loaded_len:
    .res 2
actdbg_overlay_service_status:
    .res 1
actdbg_overlay_saved_memcfg:
    .res 1
actdbg_overlay_entry_minus_one:
    .res 1
actdbg_active_file_kind:
    .res 1
actdbg_file_window_kind:
    .res 1
actdbg_file_window_start_lo:
    .res 1
actdbg_file_window_start_hi:
    .res 1
actdbg_file_window_end_lo:
    .res 1
actdbg_file_window_end_hi:
    .res 1
actdbg_prg_header:
    .res PRG_HEADER_LIMIT
actdbg_target_fetch_buffer:
    .res 2
actdbg_target_read_len:
    .res 1
actdbg_file_window:
    .res ACTDBG_FILE_WINDOW_LIMIT
actdbg_native_scan_lo:
    .res 1
actdbg_native_scan_hi:
    .res 1
actdbg_current_pc_lo:
    .res 1
actdbg_current_pc_hi:
    .res 1
actdbg_native_done:
    .res 1
actdbg_native_failed:
    .res 1
actdbg_native_sp:
    .res 1
actdbg_native_call_depth:
    .res 1
actdbg_native_a:
    .res 1
actdbg_native_x:
    .res 1
actdbg_native_y:
    .res 1
actdbg_native_p:
    .res 1
actdbg_native_target_valid:
    .res 1
actdbg_output_row:
    .res 1
actdbg_output_col:
    .res 1
actdbg_backtrace_index:
    .res 1
actdbg_backtrace_len:
    .res 1
actdbg_backtrace_slot:
    .res 1
actdbg_backtrace_pc_lo:
    .res 1
actdbg_backtrace_pc_hi:
    .res 1
actdbg_backtrace_summary:
    .res SUMMARY_LIMIT+1
actdbg_trace_summary0:
    .res SUMMARY_LIMIT+1
actdbg_trace_summary1:
    .res SUMMARY_LIMIT+1
actdbg_trace_summary2:
    .res SUMMARY_LIMIT+1
actdbg_global_summary:
    .res SUMMARY_LIMIT+1
actdbg_param_summary:
    .res SUMMARY_LIMIT+1
actdbg_local_summary:
    .res SUMMARY_LIMIT+1
actdbg_native_callstack_lo:
    .res NATIVE_CALLSTACK_MAX
actdbg_native_callstack_hi:
    .res NATIVE_CALLSTACK_MAX
actdbg_zp_save:
    .res $20
actdbg_service_out:
    .res 4
actdbg_service_status:
    .res 1
actdbg_input_key:
    .res 1
actdbg_debugger_screen = SCREEN_RAM
actdbg_output_row_buffer:
    .res SCREEN_COLS
actdbg_output_screen = actdbg_output_row_buffer
