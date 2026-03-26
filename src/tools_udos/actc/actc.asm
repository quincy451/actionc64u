.include "udos_services.inc"

.export start

MANIFEST_LIMIT = 191
SOURCE_LIMIT = 255

IMPORT_PRINT_STR  = $01
IMPORT_PRINT_LINE = $02
IMPORT_FORMAT_INT = $04

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
file_params:
    .res 9
save_params:
    .res 5
src_ptr:
    .res 2
scan_ptr:
    .res 2
content_ptr:
    .res 2
const_ptr:
    .res 2
import_flags_lo:
    .res 1
truncated_flag:
    .res 1
compare_char:
    .res 1
save_mode:
    .res 1
hex_work:
    .res 1
list_started:
    .res 1

export_index = list_started
export_ptr = src_ptr

.code

start:
    jsr init_module_name
    jsr build_manifest_entry
    jsr require_loaded_project
    jsr require_manifest_entry_tracked
    jsr build_target_path
    jsr require_source_present
    jsr load_source_file
    bcc source_loaded
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
source_loaded:
    jsr parse_module_header_or_fail
    jsr collect_proc_exports_or_fail
    jsr collect_local_calls
    jsr build_object_target_path
    jsr probe_target_save_mode_or_fail
    jsr detect_runtime_imports
    jsr build_avo_content
    jsr save_content_buffer_to_target
    bcc save_ok
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr

save_ok:
    jsr report_save_mode_result
    lda #<msg_ok
    ldy #>msg_ok
    jsr print_line_ptr
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

init_module_name:
    ldx #svc_retptr
    jsr svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    beq init_module_name_default
    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    lda svc_retptr
    sta src_ptr
    lda svc_retptr+1
    sta src_ptr+1
    jsr copy_module_arg
    bcc init_module_name_done
    lda #<msg_bad_name
    ldy #>msg_bad_name
    jmp fail_with_ptr

init_module_name_default:
    ldy #$00
init_module_name_default_loop:
    lda default_module_name,y
    sta module_name,y
    beq init_module_name_done
    iny
    bne init_module_name_default_loop
init_module_name_done:
    rts

require_source_present:
    jsr probe_target_path
    lda file_params+6
    cmp #tool_file_status_ok
    beq require_source_present_done
    cmp #tool_file_status_too_large
    beq require_source_present_done
    cmp #tool_file_status_nofile
    beq require_source_present_missing
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
require_source_present_missing:
    lda #<msg_no_file
    ldy #>msg_no_file
    jmp fail_with_ptr
require_source_present_done:
    rts

parse_module_header_or_fail:
    lda #<source_buffer
    sta scan_ptr
    lda #>source_buffer
    sta scan_ptr+1
    jsr skip_source_whitespace
    lda #<pattern_module
    sta const_ptr
    lda #>pattern_module
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcc :+
    lda #<msg_bad_module
    ldy #>msg_bad_module
    jmp fail_with_ptr
:   ldy #$00
parse_module_header_keyword_advance:
    lda (const_ptr),y
    beq parse_module_header_keyword_done
    jsr advance_scan_ptr
    iny
    bne parse_module_header_keyword_advance
parse_module_header_keyword_done:
    jsr skip_source_spaces
    jsr copy_declared_module_or_fail
    jsr compare_declared_module_or_fail
    rts

skip_source_whitespace:
    ldy #$00
skip_source_whitespace_loop:
    lda (scan_ptr),y
    cmp #' '
    beq skip_source_whitespace_advance
    cmp #9
    beq skip_source_whitespace_advance
    cmp #10
    beq skip_source_whitespace_advance
    cmp #13
    beq skip_source_whitespace_advance
    rts
skip_source_whitespace_advance:
    jsr advance_scan_ptr
    jmp skip_source_whitespace_loop

skip_source_spaces:
    ldy #$00
skip_source_spaces_loop:
    lda (scan_ptr),y
    cmp #' '
    beq skip_source_spaces_advance
    cmp #9
    beq skip_source_spaces_advance
    rts
skip_source_spaces_advance:
    jsr advance_scan_ptr
    jmp skip_source_spaces_loop

copy_declared_module_or_fail:
    ldy #$00
copy_declared_module_or_fail_loop:
    lda (scan_ptr),y
    beq copy_declared_module_or_fail_bad
    jsr uppercase_ascii
    cmp #'A'
    bcc copy_declared_module_or_fail_done
    cmp #'Z'+1
    bcc copy_declared_module_or_fail_store
    cmp #'0'
    bcc copy_declared_module_or_fail_symbol
    cmp #'9'+1
    bcc copy_declared_module_or_fail_store
copy_declared_module_or_fail_symbol:
    cmp #'_'
    bne copy_declared_module_or_fail_done
copy_declared_module_or_fail_store:
    sta declared_module_name,y
    iny
    cpy #24
    bcc copy_declared_module_or_fail_loop
copy_declared_module_or_fail_bad:
    lda #<msg_bad_module
    ldy #>msg_bad_module
    jmp fail_with_ptr
copy_declared_module_or_fail_done:
    cpy #$00
    beq copy_declared_module_or_fail_bad
    lda #$00
    sta declared_module_name,y
    rts

compare_declared_module_or_fail:
    ldy #$00
compare_declared_module_or_fail_loop:
    lda declared_module_name,y
    sta compare_char
    lda module_name,y
    jsr uppercase_ascii
    cmp compare_char
    bne compare_declared_module_or_fail_bad
    lda compare_char
    beq compare_declared_module_or_fail_done
    iny
    bne compare_declared_module_or_fail_loop
compare_declared_module_or_fail_bad:
    lda #<msg_bad_module
    ldy #>msg_bad_module
    jmp fail_with_ptr
compare_declared_module_or_fail_done:
    rts

collect_proc_exports_or_fail:
    lda #$00
    sta export_count_data
    lda #<source_buffer
    sta scan_ptr
    lda #>source_buffer
    sta scan_ptr+1
collect_proc_exports_or_fail_loop:
    ldy #$00
    lda (scan_ptr),y
    beq collect_proc_exports_or_fail_done_check
    cmp #10
    beq collect_proc_exports_or_fail_advance_blank
    cmp #13
    beq collect_proc_exports_or_fail_advance_blank
    jsr skip_source_spaces
    ldy #$00
    lda (scan_ptr),y
    beq collect_proc_exports_or_fail_done_check
    lda #<pattern_proc
    sta const_ptr
    lda #>pattern_proc
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs collect_proc_exports_or_fail_skip_line
    jsr advance_scan_ptr_by_const_ptr
    jsr skip_source_spaces
    jsr store_proc_export_from_scan_ptr_or_fail
collect_proc_exports_or_fail_skip_line:
    jsr skip_source_line
    jmp collect_proc_exports_or_fail_loop
collect_proc_exports_or_fail_advance_blank:
    jsr advance_scan_ptr
    jmp collect_proc_exports_or_fail_loop
collect_proc_exports_or_fail_done_check:
    lda export_count_data
    bne collect_proc_exports_or_fail_done
    lda #<msg_no_proc
    ldy #>msg_no_proc
    jmp fail_with_ptr
collect_proc_exports_or_fail_done:
    rts

collect_local_calls:
    lda #$00
    sta call_count_data
    sta call_list_started
    lda #$FF
    sta current_proc_index_data
    lda #<source_buffer
    sta scan_ptr
    lda #>source_buffer
    sta scan_ptr+1
collect_local_calls_loop:
    ldy #$00
    lda (scan_ptr),y
    bne collect_local_calls_have_char
    jmp collect_local_calls_done
collect_local_calls_have_char:
    cmp #10
    beq collect_local_calls_advance_blank
    cmp #13
    beq collect_local_calls_advance_blank
    jsr skip_source_spaces
    ldy #$00
    lda (scan_ptr),y
    bne collect_local_calls_after_space_check
    jmp collect_local_calls_done
collect_local_calls_after_space_check:
    lda #<pattern_proc
    sta const_ptr
    lda #>pattern_proc
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcc collect_local_calls_proc_decl
    lda current_proc_index_data
    cmp #$FF
    beq collect_local_calls_skip_line
    jsr copy_symbol_from_scan_ptr
    bcs collect_local_calls_skip_line
    cmp #'('
    bne collect_local_calls_skip_line
    jsr find_export_index_from_declared
    bcs collect_local_calls_skip_line
    cpx current_proc_index_data
    beq collect_local_calls_skip_line
    stx hex_work
    jsr call_pair_already_recorded
    bcs collect_local_calls_skip_line
    ldy call_count_data
    cpy #8
    bcc :+
    lda #<msg_bad_call
    ldy #>msg_bad_call
    jmp fail_with_ptr
:   lda current_proc_index_data
    sta call_from_indices,y
    lda hex_work
    sta call_to_indices,y
    inc call_count_data
collect_local_calls_skip_line:
    jsr skip_source_line
    jmp collect_local_calls_loop
collect_local_calls_proc_decl:
    jsr advance_scan_ptr_by_const_ptr
    jsr skip_source_spaces
    jsr copy_symbol_from_scan_ptr
    bcs collect_local_calls_bad_proc
    jsr find_export_index_from_declared
    bcs collect_local_calls_bad_proc
    stx current_proc_index_data
    jsr skip_source_line
    jmp collect_local_calls_loop
collect_local_calls_advance_blank:
    jsr advance_scan_ptr
    jmp collect_local_calls_loop
collect_local_calls_bad_proc:
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_ptr
collect_local_calls_done:
    rts

call_pair_already_recorded:
    ldy #$00
call_pair_already_recorded_loop:
    cpy call_count_data
    beq call_pair_already_recorded_new
    lda call_from_indices,y
    cmp current_proc_index_data
    bne call_pair_already_recorded_next
    lda call_to_indices,y
    cmp hex_work
    beq call_pair_already_recorded_found
call_pair_already_recorded_next:
    iny
    bne call_pair_already_recorded_loop
call_pair_already_recorded_new:
    clc
    rts
call_pair_already_recorded_found:
    sec
    rts

skip_source_line:
    ldy #$00
skip_source_line_loop:
    lda (scan_ptr),y
    beq skip_source_line_done
    cmp #10
    beq skip_source_line_done
    cmp #13
    beq skip_source_line_done
    jsr advance_scan_ptr
    jmp skip_source_line_loop
skip_source_line_done:
    rts

store_proc_export_from_scan_ptr_or_fail:
    lda export_count_data
    cmp #8
    bcc :+
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_ptr
:   ldx export_count_data
    jsr set_export_ptr_from_x
    ldy #$00
store_proc_export_from_scan_ptr_or_fail_loop:
    lda (scan_ptr),y
    beq store_proc_export_from_scan_ptr_or_fail_done
    cmp #'('
    beq store_proc_export_from_scan_ptr_or_fail_done
    cmp #'='
    beq store_proc_export_from_scan_ptr_or_fail_done
    cmp #' '
    beq store_proc_export_from_scan_ptr_or_fail_done
    cmp #9
    beq store_proc_export_from_scan_ptr_or_fail_done
    cmp #10
    beq store_proc_export_from_scan_ptr_or_fail_done
    cmp #13
    beq store_proc_export_from_scan_ptr_or_fail_done
    jsr uppercase_ascii
    cmp #'A'
    bcc store_proc_export_from_scan_ptr_or_fail_bad
    cmp #'Z'+1
    bcc store_proc_export_from_scan_ptr_or_fail_store
    cmp #'0'
    bcc store_proc_export_from_scan_ptr_or_fail_symbol
    cmp #'9'+1
    bcc store_proc_export_from_scan_ptr_or_fail_store
store_proc_export_from_scan_ptr_or_fail_symbol:
    cmp #'_'
    bne store_proc_export_from_scan_ptr_or_fail_bad
store_proc_export_from_scan_ptr_or_fail_store:
    sta (export_ptr),y
    iny
    cpy #24
    bcc store_proc_export_from_scan_ptr_or_fail_loop
store_proc_export_from_scan_ptr_or_fail_bad:
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_ptr
store_proc_export_from_scan_ptr_or_fail_done:
    cpy #$00
    beq store_proc_export_from_scan_ptr_or_fail_bad
    lda #$00
    sta (export_ptr),y
    inc export_count_data
    rts

set_export_ptr_from_x:
    lda #<export_names
    sta export_ptr
    lda #>export_names
    sta export_ptr+1
set_export_ptr_from_x_loop:
    cpx #$00
    beq set_export_ptr_from_x_done
    clc
    lda export_ptr
    adc #25
    sta export_ptr
    lda export_ptr+1
    adc #$00
    sta export_ptr+1
    dex
    bne set_export_ptr_from_x_loop
set_export_ptr_from_x_done:
    rts

copy_symbol_from_scan_ptr:
    ldy #$00
copy_symbol_from_scan_ptr_loop:
    lda (scan_ptr),y
    beq copy_symbol_from_scan_ptr_done
    jsr uppercase_ascii
    cmp #'A'
    bcc copy_symbol_from_scan_ptr_done
    cmp #'Z'+1
    bcc copy_symbol_from_scan_ptr_store
    cmp #'0'
    bcc copy_symbol_from_scan_ptr_symbol
    cmp #'9'+1
    bcc copy_symbol_from_scan_ptr_store
copy_symbol_from_scan_ptr_symbol:
    cmp #'_'
    bne copy_symbol_from_scan_ptr_done
copy_symbol_from_scan_ptr_store:
    sta declared_module_name,y
    iny
    cpy #24
    bcc copy_symbol_from_scan_ptr_loop
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_ptr
copy_symbol_from_scan_ptr_done:
    cpy #$00
    beq copy_symbol_from_scan_ptr_fail
    pha
    lda #$00
    sta declared_module_name,y
    pla
    clc
    rts
copy_symbol_from_scan_ptr_fail:
    sec
    rts

find_export_index_from_declared:
    ldx #$00
find_export_index_from_declared_loop:
    cpx export_count_data
    beq find_export_index_from_declared_fail
    stx hex_work
    jsr set_export_ptr_from_x
    ldx hex_work
    ldy #$00
find_export_index_from_declared_compare_loop:
    lda (export_ptr),y
    cmp declared_module_name,y
    bne find_export_index_from_declared_next
    lda declared_module_name,y
    beq find_export_index_from_declared_done
    iny
    bne find_export_index_from_declared_compare_loop
find_export_index_from_declared_next:
    inx
    bne find_export_index_from_declared_loop
find_export_index_from_declared_fail:
    sec
    rts
find_export_index_from_declared_done:
    clc
    rts

detect_runtime_imports:
    lda #$00
    sta import_flags_lo

    lda #<pattern_print
    sta const_ptr
    lda #>pattern_print
    sta const_ptr+1
    jsr find_pattern_at_const_ptr
    bcs :+
    lda import_flags_lo
    ora #IMPORT_PRINT_STR
    sta import_flags_lo
:   lda #<pattern_printe
    sta const_ptr
    lda #>pattern_printe
    sta const_ptr+1
    jsr find_pattern_at_const_ptr
    bcs :+
    lda import_flags_lo
    ora #IMPORT_PRINT_LINE
    sta import_flags_lo
:   lda #<pattern_printi
    sta const_ptr
    lda #>pattern_printi
    sta const_ptr+1
    jsr find_pattern_at_const_ptr
    bcs :+
    lda import_flags_lo
    ora #IMPORT_FORMAT_INT|IMPORT_PRINT_STR
    sta import_flags_lo
:   lda #<pattern_printie
    sta const_ptr
    lda #>pattern_printie
    sta const_ptr+1
    jsr find_pattern_at_const_ptr
    bcs :+
    lda import_flags_lo
    ora #IMPORT_FORMAT_INT|IMPORT_PRINT_LINE
    sta import_flags_lo
:   rts

find_pattern_at_const_ptr:
    lda #<source_buffer
    sta scan_ptr
    lda #>source_buffer
    sta scan_ptr+1
find_pattern_at_const_ptr_loop:
    ldy #$00
    lda (scan_ptr),y
    beq find_pattern_at_const_ptr_fail
    jsr pattern_matches_scan_ptr
    bcc find_pattern_at_const_ptr_ok
    jsr advance_scan_ptr
    jmp find_pattern_at_const_ptr_loop
find_pattern_at_const_ptr_ok:
    clc
    rts
find_pattern_at_const_ptr_fail:
    sec
    rts

pattern_matches_scan_ptr:
    ldy #$00
pattern_matches_scan_ptr_loop:
    lda (const_ptr),y
    beq pattern_matches_scan_ptr_ok
    sta compare_char
    lda (scan_ptr),y
    beq pattern_matches_scan_ptr_fail
    jsr uppercase_ascii
    cmp compare_char
    bne pattern_matches_scan_ptr_fail
    iny
    bne pattern_matches_scan_ptr_loop
pattern_matches_scan_ptr_fail:
    sec
    rts
pattern_matches_scan_ptr_ok:
    clc
    rts

advance_scan_ptr_by_const_ptr:
    ldy #$00
advance_scan_ptr_by_const_ptr_loop:
    lda (const_ptr),y
    beq advance_scan_ptr_by_const_ptr_done
    jsr advance_scan_ptr
    iny
    bne advance_scan_ptr_by_const_ptr_loop
advance_scan_ptr_by_const_ptr_done:
    rts

uppercase_ascii:
    cmp #'a'
    bcc uppercase_ascii_done
    cmp #'z'+1
    bcs uppercase_ascii_done
    and #$DF
uppercase_ascii_done:
    rts

lowercase_ascii:
    cmp #'A'
    bcc lowercase_ascii_done
    cmp #'Z'+1
    bcs lowercase_ascii_done
    ora #$20
lowercase_ascii_done:
    rts

build_avo_content:
    lda #<content_buffer
    sta content_ptr
    lda #>content_buffer
    sta content_ptr+1

    lda #<avo_prefix_1
    sta const_ptr
    lda #>avo_prefix_1
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_export_list

    lda #<avo_prefix_2
    sta const_ptr
    lda #>avo_prefix_2
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_call_list

    lda #<avo_prefix_3
    sta const_ptr
    lda #>avo_prefix_3
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_import_list

    lda #<avo_prefix_4
    sta const_ptr
    lda #>avo_prefix_4
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_module_symbol_lower

    lda #<avo_prefix_5
    sta const_ptr
    lda #>avo_prefix_5
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_module_symbol_hex_lower
    lda #$00
    jsr append_hex_byte

    lda #<avo_suffix
    sta const_ptr
    lda #>avo_suffix
    sta const_ptr+1
    jsr append_const_ptr

    lda #$00
    jmp append_char

append_import_list:
    lda #$00
    sta list_started

    lda import_flags_lo
    and #IMPORT_FORMAT_INT
    beq :+
    lda #<import_rt_format_int
    sta const_ptr
    lda #>import_rt_format_int
    sta const_ptr+1
    jsr append_import_name
:   lda import_flags_lo
    and #IMPORT_PRINT_LINE
    beq :+
    lda #<import_rt_print_line
    sta const_ptr
    lda #>import_rt_print_line
    sta const_ptr+1
    jsr append_import_name
:   lda import_flags_lo
    and #IMPORT_PRINT_STR
    beq :+
    lda #<import_rt_print_str
    sta const_ptr
    lda #>import_rt_print_str
    sta const_ptr+1
    jsr append_import_name
:   rts

append_import_name:
    lda list_started
    beq :+
    lda #','
    jsr append_char
:   lda #'"'
    jsr append_char
    jsr append_const_ptr
    lda #'"'
    jsr append_char
    lda #$01
    sta list_started
    rts

append_export_list:
    lda #$00
    sta export_index
append_export_list_loop:
    ldx export_index
    cpx export_count_data
    beq append_export_list_done
    lda export_index
    beq :+
    lda #','
    jsr append_char
:   lda #'['
    jsr append_char
    lda #'"'
    jsr append_char
    ldx export_index
    jsr set_export_ptr_from_x
    ldy #$00
append_export_list_symbol_loop:
    lda (export_ptr),y
    beq append_export_list_symbol_done
    jsr lowercase_ascii
    jsr append_char
    iny
    bne append_export_list_symbol_loop
append_export_list_symbol_done:
    lda #'"'
    jsr append_char
    lda #','
    jsr append_char
    lda #'0'
    jsr append_char
    lda #']'
    jsr append_char
    inc export_index
    jmp append_export_list_loop
append_export_list_done:
    rts

append_call_list:
    lda #$00
    sta export_index
    sta call_list_started
append_call_list_loop:
    ldx export_index
    cpx call_count_data
    beq append_call_list_done
    lda call_list_started
    beq :+
    lda #','
    jsr append_char
:   lda #'['
    jsr append_char
    lda #'"'
    jsr append_char
    ldy export_index
    lda call_from_indices,y
    tax
    jsr set_export_ptr_from_x
    ldy #$00
append_call_list_symbol_loop:
    lda (export_ptr),y
    beq append_call_list_symbol_done
    jsr lowercase_ascii
    jsr append_char
    iny
    bne append_call_list_symbol_loop
append_call_list_symbol_done:
    lda #'"'
    jsr append_char
    lda #','
    jsr append_char
    lda #'"'
    jsr append_char
    ldy export_index
    lda call_to_indices,y
    tax
    jsr set_export_ptr_from_x
    ldy #$00
append_call_list_callee_loop:
    lda (export_ptr),y
    beq append_call_list_callee_done
    jsr lowercase_ascii
    jsr append_char
    iny
    bne append_call_list_callee_loop
append_call_list_callee_done:
    lda #'"'
    jsr append_char
    lda #']'
    jsr append_char
    lda #$01
    sta call_list_started
    inc export_index
    jmp append_call_list_loop
append_call_list_done:
    rts

append_module_symbol_lower:
    ldy #$00
append_module_symbol_lower_loop:
    lda module_name,y
    beq append_module_symbol_lower_done
    jsr lowercase_ascii
    jsr append_char
    iny
    bne append_module_symbol_lower_loop
append_module_symbol_lower_done:
    rts

append_module_symbol_hex_lower:
    ldy #$00
append_module_symbol_hex_lower_loop:
    lda module_name,y
    beq append_module_symbol_hex_lower_done
    jsr lowercase_ascii
    jsr append_hex_byte
    iny
    bne append_module_symbol_hex_lower_loop
append_module_symbol_hex_lower_done:
    rts

append_const_ptr:
    ldy #$00
append_const_ptr_loop:
    lda (const_ptr),y
    beq append_const_ptr_done
    jsr append_char
    iny
    bne append_const_ptr_loop
append_const_ptr_done:
    rts

append_hex_byte:
    sta hex_work
    lsr a
    lsr a
    lsr a
    lsr a
    jsr append_hex_nibble
    lda hex_work
    and #$0F
    jmp append_hex_nibble

append_hex_nibble:
    cmp #$0A
    bcc append_hex_nibble_digit
    clc
    adc #('a'-10)
    jmp append_char
append_hex_nibble_digit:
    clc
    adc #'0'
    jmp append_char

append_char:
    tax
    tya
    pha
    ldy #$00
    txa
    sta (content_ptr),y
    pla
    tay
    inc content_ptr
    bne :+
    inc content_ptr+1
:   rts

; action_project_save_write.inc also exposes a stub-save helper that expects this
; entry point. ACTC writes content_buffer directly, so this is intentionally empty.
build_module_stub_content:
    rts

.include "../common/action_project_module_arg.inc"
.include "../common/action_project_load.inc"
.include "../common/action_project_load_guard.inc"
.include "../common/action_project_entry.inc"
.include "../common/action_project_entry_guard.inc"
.include "../common/action_project_object_path.inc"
.include "../common/action_project_path.inc"
.include "../common/action_project_save_mode.inc"
.include "../common/action_project_save_write.inc"
.include "../common/action_project_source.inc"

print_line_ptr:
    jsr print_ptr
    jmp svc_console_newline

fail_with_ptr:
    jsr print_line_ptr
    lda #$01
    sta svc_retptr
    lda #$00
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

print_ptr:
    sta svc_retptr
    sty svc_retptr+1
    ldx #svc_retptr
    jmp svc_console_write_sc0

msg_bad_name:
    .asciiz "BAD NAME"
msg_no_project:
    .asciiz "NO PROJECT"
msg_not_in_project:
    .asciiz "NOT IN PROJECT"
msg_no_file:
    .asciiz "NO FILE"
msg_probe_fail:
    .asciiz "PROBE FAIL"
msg_load_fail:
    .asciiz "LOAD FAIL"
msg_bad_module:
    .asciiz "BAD MODULE"
msg_bad_proc:
    .asciiz "BAD PROC"
msg_bad_call:
    .asciiz "BAD CALL"
msg_save_fail:
    .asciiz "SAVE FAIL"
msg_created:
    .asciiz "CREATED"
msg_updated:
    .asciiz "UPDATED"
msg_no_proc:
    .asciiz "NO PROC"
msg_ok:
    .asciiz "ACTC OK"

default_module_name:
    .asciiz "MAIN"
project_marker:
    .asciiz "ACTION.PROJ"

pattern_module:
    .asciiz "MODULE"
pattern_proc:
    .asciiz "PROC"
pattern_print:
    .asciiz "PRINT("
pattern_printe:
    .asciiz "PRINTE("
pattern_printi:
    .asciiz "PRINTI("
pattern_printie:
    .asciiz "PRINTIE("

import_rt_format_int:
    .asciiz "rt.format_int"
import_rt_print_line:
    .asciiz "rt.print_line"
import_rt_print_str:
    .asciiz "rt.print_str"

avo_prefix_1:
    .byte "AVO1",10,"{",34,"entry_offset",34,":0,",34,"exports",34,":[",0
avo_prefix_2:
    .byte "],",34,"calls",34,":[",0
avo_prefix_3:
    .byte "],",34,"imports",34,":[",0
avo_prefix_4:
    .byte "],",34,"module",34,":",34,0
avo_prefix_5:
    .byte 34,",",34,"payload_hex",34,":",34,0
avo_suffix:
    .byte 34,",",34,"version",34,":1}",10,0

module_name:
    .res 25
declared_module_name:
    .res 25
manifest_entry:
    .res 32
target_path:
    .res 40
source_buffer:
    .res SOURCE_LIMIT+1
content_buffer:
    .res 640
manifest_buffer:
    .res MANIFEST_LIMIT+1
export_count_data:
    .res 1
call_count_data:
    .res 1
current_proc_index_data:
    .res 1
call_list_started:
    .res 1
export_names:
    .res 200
call_from_indices:
    .res 8
call_to_indices:
    .res 8
