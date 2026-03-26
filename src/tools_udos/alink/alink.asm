.include "udos_services.inc"

.export start

MANIFEST_LIMIT = 191
SOURCE_LIMIT = 511

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
compare_char:
    .res 1
current_bit_lo:
    .res 1
current_bit_hi:
    .res 1
main_flags_lo:
    .res 1
main_flags_hi:
    .res 1
save_mode:
    .res 1
truncated_flag:
    .res 1
edge_mask:
    .res 1

export_count = truncated_flag
export_index = save_mode
export_ptr = current_bit_lo

.code

start:
    jsr init_module_name
    jsr build_manifest_entry
    jsr require_loaded_project
    jsr require_manifest_entry_tracked
    jsr build_object_target_path
    jsr load_object_or_fail
    jsr parse_exports_or_fail
    jsr parse_imports_or_fail
    jsr build_live_set
    jsr resolve_import_closure
    jsr build_map_target_path
    jsr build_map_content
    jsr save_content_buffer_to_target
    bcc save_ok
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr

save_ok:
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
    jsr skip_cmdline_spaces
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

skip_cmdline_spaces:
    ldy #$00
skip_cmdline_spaces_loop:
    lda (src_ptr),y
    cmp #' '
    bne skip_cmdline_spaces_done
    inc src_ptr
    bne :+
    inc src_ptr+1
:   jmp skip_cmdline_spaces_loop
skip_cmdline_spaces_done:
    rts

load_object_or_fail:
    jsr probe_target_path
    lda file_params+6
    cmp #tool_file_status_ok
    beq load_object_present
    cmp #tool_file_status_too_large
    beq load_object_present
    cmp #tool_file_status_nofile
    beq load_object_missing
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_object_missing:
    lda #<msg_no_object
    ldy #>msg_no_object
    jmp fail_with_ptr
load_object_present:
    jsr load_source_file
    bcc load_object_loaded
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_object_loaded:
    lda truncated_flag
    beq load_object_check_header
    lda #<msg_too_large
    ldy #>msg_too_large
    jmp fail_with_ptr
load_object_check_header:
    lda source_buffer+0
    cmp #'A'
    bne load_object_bad
    lda source_buffer+1
    cmp #'V'
    bne load_object_bad
    lda source_buffer+2
    cmp #'O'
    bne load_object_bad
    lda source_buffer+3
    cmp #'1'
    beq load_object_done
load_object_bad:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
load_object_done:
    rts

parse_exports_or_fail:
    lda #$00
    sta export_count
    lda #<marker_calls
    sta const_ptr
    lda #>marker_calls
    sta const_ptr+1
    jsr find_pattern_at_const_ptr
    bcc parse_exports_limit_ready
    lda #<marker_imports
    sta const_ptr
    lda #>marker_imports
    sta const_ptr+1
    jsr find_pattern_at_const_ptr
    bcc parse_exports_limit_ready
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
parse_exports_limit_ready:
    lda scan_ptr
    sta src_ptr
    lda scan_ptr+1
    sta src_ptr+1

    lda #<marker_exports
    sta const_ptr
    lda #>marker_exports
    sta const_ptr+1
    jsr find_pattern_at_const_ptr
    bcc :+
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
:   jsr advance_scan_ptr_by_const_ptr

parse_exports_loop:
    lda scan_ptr+1
    cmp src_ptr+1
    bne :+
    lda scan_ptr
    cmp src_ptr
    beq parse_exports_done_check
:   ldy #$00
    lda (scan_ptr),y
    beq parse_exports_bad
    cmp #'"'
    beq parse_export_symbol
    jsr advance_scan_ptr
    jmp parse_exports_loop

parse_export_symbol:
    jsr advance_scan_ptr
    jsr copy_export_symbol_or_fail
    jmp parse_exports_loop

parse_exports_done_check:
    lda export_count
    bne parse_exports_done
parse_exports_bad:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
parse_exports_done:
    rts

copy_export_symbol_or_fail:
    lda export_count
    cmp #8
    bcc :+
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
:   ldx export_count
    jsr set_export_ptr_from_x
    ldy #$00
copy_export_symbol_or_fail_loop:
    lda (scan_ptr),y
    beq parse_exports_bad
    cmp #'"'
    beq copy_export_symbol_or_fail_done
    sta (export_ptr),y
    iny
    cpy #24
    bcc copy_export_symbol_or_fail_loop
    jmp parse_exports_bad
copy_export_symbol_or_fail_done:
    cpy #$00
    beq parse_exports_bad
    lda #$00
    sta (export_ptr),y
copy_export_symbol_or_fail_advance_loop:
    cpy #$00
    beq copy_export_symbol_or_fail_advanced
    jsr advance_scan_ptr
    dey
    bne copy_export_symbol_or_fail_advance_loop
copy_export_symbol_or_fail_advanced:
    jsr advance_scan_ptr
    inc export_count
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

parse_imports_or_fail:
    lda #$00
    sta main_flags_lo
    sta main_flags_hi
    lda #<marker_imports
    sta const_ptr
    lda #>marker_imports
    sta const_ptr+1
    jsr find_pattern_at_const_ptr
    bcc :+
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
:   jsr advance_scan_ptr_by_const_ptr

parse_imports_loop:
    jsr skip_import_delimiters
    ldy #$00
    lda (scan_ptr),y
    cmp #']'
    beq parse_imports_done
    cmp #'"'
    beq parse_import_symbol
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr

parse_import_symbol:
    jsr advance_scan_ptr
    ldy #$00
parse_import_symbol_loop:
    lda (scan_ptr),y
    beq parse_imports_bad
    cmp #'"'
    beq parse_import_symbol_done
    sta symbol_buffer,y
    iny
    cpy #24
    bcc parse_import_symbol_loop
parse_imports_bad:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
parse_import_symbol_done:
    lda #$00
    sta symbol_buffer,y
parse_import_symbol_advance_loop:
    cpy #$00
    beq parse_import_symbol_advanced
    jsr advance_scan_ptr
    dey
    bne parse_import_symbol_advance_loop
parse_import_symbol_advanced:
    jsr map_symbol_buffer_or_fail
    lda main_flags_lo
    ora current_bit_lo
    sta main_flags_lo
    lda main_flags_hi
    ora current_bit_hi
    sta main_flags_hi
    jsr advance_scan_ptr
    jmp parse_imports_loop
parse_imports_done:
    rts

build_live_set:
    lda #$00
    ldx #$00
build_live_set_clear_loop:
    cpx #8
    beq build_live_set_seed
    sta live_flags,x
    sta call_edge_masks,x
    inx
    bne build_live_set_clear_loop
build_live_set_seed:
    lda export_count
    bne :+
    jmp build_live_set_done
:   lda #$01
    sta live_flags+0
    lda #<marker_calls
    sta const_ptr
    lda #>marker_calls
    sta const_ptr+1
    jsr find_pattern_at_const_ptr
    bcc :+
    jmp build_live_set_done
:   jsr advance_scan_ptr_by_const_ptr
build_live_set_loop:
    jsr skip_call_pair_delimiters
    ldy #$00
    lda (scan_ptr),y
    cmp #']'
    beq build_live_set_propagate
    cmp #'['
    bne build_live_set_bad
    jsr advance_scan_ptr
    jsr skip_call_pair_delimiters
    jsr parse_quoted_symbol_or_fail
    jsr find_export_index_from_symbol_buffer
    bcs build_live_set_bad
    stx edge_mask
    jsr skip_call_pair_delimiters
    jsr parse_quoted_symbol_or_fail
    jsr find_export_index_from_symbol_buffer
    bcs build_live_set_bad
    txa
    tay
    lda bit_masks,y
    ldy edge_mask
    ora call_edge_masks,y
    sta call_edge_masks,y
    jsr skip_call_pair_delimiters
    ldy #$00
    lda (scan_ptr),y
    cmp #']'
    bne build_live_set_bad
    jsr advance_scan_ptr
    jmp build_live_set_loop

build_live_set_propagate:
    lda #$00
    sta compare_char
    ldx #$00
build_live_set_propagate_export_loop:
    cpx export_count
    beq build_live_set_propagate_check
    lda live_flags,x
    beq build_live_set_propagate_next_export
    lda call_edge_masks,x
    sta current_bit_lo
    ldy #$00
build_live_set_propagate_target_loop:
    cpy export_count
    beq build_live_set_propagate_next_export
    lda current_bit_lo
    and bit_masks,y
    beq build_live_set_propagate_next_target
    lda live_flags,y
    bne build_live_set_propagate_next_target
    lda #$01
    sta live_flags,y
    sta compare_char
build_live_set_propagate_next_target:
    iny
    bne build_live_set_propagate_target_loop
build_live_set_propagate_next_export:
    inx
    bne build_live_set_propagate_export_loop
build_live_set_propagate_check:
    lda compare_char
    bne build_live_set_propagate
build_live_set_done:
    rts
build_live_set_bad:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr

resolve_import_closure:
    lda main_flags_lo
    and #IMPORT_PRINT_LINE
    beq :+
    lda main_flags_lo
    ora #IMPORT_PRINT_STR
    sta main_flags_lo
:   rts

skip_import_delimiters:
    ldy #$00
skip_import_delimiters_loop:
    lda (scan_ptr),y
    cmp #' '
    beq skip_import_delimiters_advance
    cmp #','
    beq skip_import_delimiters_advance
    cmp #10
    beq skip_import_delimiters_advance
    cmp #13
    beq skip_import_delimiters_advance
    rts
skip_import_delimiters_advance:
    jsr advance_scan_ptr
    jmp skip_import_delimiters_loop

skip_call_pair_delimiters:
    ldy #$00
skip_call_pair_delimiters_loop:
    lda (scan_ptr),y
    cmp #' '
    beq skip_call_pair_delimiters_advance
    cmp #','
    beq skip_call_pair_delimiters_advance
    cmp #10
    beq skip_call_pair_delimiters_advance
    cmp #13
    beq skip_call_pair_delimiters_advance
    rts
skip_call_pair_delimiters_advance:
    jsr advance_scan_ptr
    jmp skip_call_pair_delimiters_loop

parse_quoted_symbol_or_fail:
    ldy #$00
    lda (scan_ptr),y
    cmp #'"'
    bne parse_quoted_symbol_or_fail_bad
    jsr advance_scan_ptr
    ldy #$00
parse_quoted_symbol_or_fail_loop:
    lda (scan_ptr),y
    beq parse_quoted_symbol_or_fail_bad
    cmp #'"'
    beq parse_quoted_symbol_or_fail_done
    sta symbol_buffer,y
    iny
    cpy #24
    bcc parse_quoted_symbol_or_fail_loop
parse_quoted_symbol_or_fail_bad:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
parse_quoted_symbol_or_fail_done:
    cpy #$00
    beq parse_quoted_symbol_or_fail_bad
    lda #$00
    sta symbol_buffer,y
parse_quoted_symbol_or_fail_advance_loop:
    cpy #$00
    beq parse_quoted_symbol_or_fail_advanced
    jsr advance_scan_ptr
    dey
    bne parse_quoted_symbol_or_fail_advance_loop
parse_quoted_symbol_or_fail_advanced:
    jsr advance_scan_ptr
    rts

map_symbol_buffer_or_fail:
    lda #$00
    sta current_bit_lo
    sta current_bit_hi
    lda #<import_rt_format_int
    sta const_ptr
    lda #>import_rt_format_int
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #IMPORT_FORMAT_INT
    sta current_bit_lo
    rts
:   lda #<import_rt_print_line
    sta const_ptr
    lda #>import_rt_print_line
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #IMPORT_PRINT_LINE
    sta current_bit_lo
    rts
:   lda #<import_rt_print_str
    sta const_ptr
    lda #>import_rt_print_str
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs map_symbol_unresolved
    lda #IMPORT_PRINT_STR
    sta current_bit_lo
    rts
map_symbol_unresolved:
    lda #<msg_unresolved
    ldy #>msg_unresolved
    jmp fail_with_ptr

find_export_index_from_symbol_buffer:
    ldx #$00
find_export_index_from_symbol_buffer_loop:
    cpx export_count
    beq find_export_index_from_symbol_buffer_fail
    stx compare_char
    jsr set_export_ptr_from_x
    ldx compare_char
    ldy #$00
find_export_index_from_symbol_buffer_compare_loop:
    lda (export_ptr),y
    cmp symbol_buffer,y
    bne find_export_index_from_symbol_buffer_next
    lda symbol_buffer,y
    beq find_export_index_from_symbol_buffer_done
    iny
    bne find_export_index_from_symbol_buffer_compare_loop
find_export_index_from_symbol_buffer_next:
    inx
    bne find_export_index_from_symbol_buffer_loop
find_export_index_from_symbol_buffer_fail:
    sec
    rts
find_export_index_from_symbol_buffer_done:
    clc
    rts

set_import_ptr_from_x:
    lda import_name_ptr_lo,x
    sta const_ptr
    lda import_name_ptr_hi,x
    sta const_ptr+1
    rts

load_current_import_bits_from_x:
    lda import_bits_lo,x
    sta current_bit_lo
    lda import_bits_hi,x
    sta current_bit_hi
    rts

import_selected_from_x:
    jsr load_current_import_bits_from_x
    lda main_flags_lo
    and current_bit_lo
    sta compare_char
    lda main_flags_hi
    and current_bit_hi
    ora compare_char
    rts

symbol_buffer_matches_const_ptr:
    ldy #$00
symbol_buffer_matches_const_ptr_loop:
    lda (const_ptr),y
    cmp symbol_buffer,y
    bne symbol_buffer_matches_const_ptr_fail
    lda (const_ptr),y
    beq symbol_buffer_matches_const_ptr_ok
    iny
    bne symbol_buffer_matches_const_ptr_loop
symbol_buffer_matches_const_ptr_fail:
    sec
    rts
symbol_buffer_matches_const_ptr_ok:
    clc
    rts

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

build_map_content:
    lda #<content_buffer
    sta content_ptr
    lda #>content_buffer
    sta content_ptr+1

    lda #<map_header
    sta const_ptr
    lda #>map_header
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_module_symbol_lower

    lda #<map_object_prefix
    sta const_ptr
    lda #>map_object_prefix
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_module_name_raw
    lda #<map_object_suffix
    sta const_ptr
    lda #>map_object_suffix
    sta const_ptr+1
    jsr append_const_ptr

    jsr append_export_lines
    jsr append_call_lines
    jsr append_live_lines
    jsr append_import_include_lines
    jsr append_main_resolve_lines
    lda #$00
    jmp append_char

append_import_include_lines:
    ldx #$00
append_import_include_lines_loop:
    cpx #IMPORT_TABLE_COUNT
    beq append_import_include_lines_done
    jsr import_selected_from_x
    beq append_import_include_lines_next
    stx compare_char
    lda #<map_include_prefix
    sta const_ptr
    lda #>map_include_prefix
    sta const_ptr+1
    jsr append_const_ptr
    ldx compare_char
    jsr set_import_ptr_from_x
    jsr append_const_ptr
    jsr append_newline
    ldx compare_char
append_import_include_lines_next:
    inx
    bne append_import_include_lines_loop
append_import_include_lines_done:
    rts

append_main_resolve_lines:
    ldx #$00
append_main_resolve_lines_loop:
    cpx #IMPORT_TABLE_COUNT
    beq append_main_resolve_lines_done
    jsr import_selected_from_x
    beq append_main_resolve_lines_next
    stx compare_char
    jsr append_main_resolve_prefix
    ldx compare_char
    jsr set_import_ptr_from_x
    jsr append_const_ptr
    jsr append_newline
    ldx compare_char
append_main_resolve_lines_next:
    inx
    bne append_main_resolve_lines_loop
append_main_resolve_lines_done:
    rts

append_main_resolve_prefix:
    lda #<map_resolve_prefix
    sta const_ptr
    lda #>map_resolve_prefix
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_module_symbol_lower
    lda #' '
    jmp append_char

append_export_lines:
    lda #$00
    sta export_index
append_export_lines_loop:
    ldx export_index
    cpx export_count
    beq append_export_lines_done
    lda #<map_export_prefix
    sta const_ptr
    lda #>map_export_prefix
    sta const_ptr+1
    jsr append_const_ptr
    ldx export_index
    jsr set_export_ptr_from_x
    ldy #$00
append_export_lines_symbol_loop:
    lda (export_ptr),y
    beq append_export_lines_symbol_done
    jsr append_char
    iny
    bne append_export_lines_symbol_loop
append_export_lines_symbol_done:
    jsr append_newline
    inc export_index
    jmp append_export_lines_loop
append_export_lines_done:
    rts

append_call_lines:
    lda #$00
    sta export_index
append_call_lines_export_loop:
    ldx export_index
    cpx export_count
    beq append_call_lines_done
    lda call_edge_masks,x
    sta edge_mask
    ldy #$00
append_call_lines_target_loop:
    cpy export_count
    beq append_call_lines_next_export
    lda edge_mask
    and bit_masks,y
    beq append_call_lines_next_target
    tya
    sta compare_char
    lda #<map_call_prefix
    sta const_ptr
    lda #>map_call_prefix
    sta const_ptr+1
    jsr append_const_ptr
    ldx export_index
    jsr set_export_ptr_from_x
    jsr append_export_ptr_lower
    lda #' '
    jsr append_char
    lda compare_char
    tax
    jsr set_export_ptr_from_x
    jsr append_export_ptr_lower
    ldy compare_char
    jsr append_newline
append_call_lines_next_target:
    iny
    bne append_call_lines_target_loop
append_call_lines_next_export:
    inc export_index
    jmp append_call_lines_export_loop
append_call_lines_done:
    rts

append_live_lines:
    lda #$00
    sta export_index
append_live_lines_loop:
    ldx export_index
    cpx export_count
    beq append_live_lines_done
    lda live_flags,x
    beq append_live_lines_next
    lda #<map_live_prefix
    sta const_ptr
    lda #>map_live_prefix
    sta const_ptr+1
    jsr append_const_ptr
    ldx export_index
    jsr set_export_ptr_from_x
    ldy #$00
append_live_lines_symbol_loop:
    lda (export_ptr),y
    beq append_live_lines_symbol_done
    jsr append_char
    iny
    bne append_live_lines_symbol_loop
append_live_lines_symbol_done:
    jsr append_newline
append_live_lines_next:
    inc export_index
    jmp append_live_lines_loop
append_live_lines_done:
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

append_module_name_raw:
    ldy #$00
append_module_name_raw_loop:
    lda module_name,y
    beq append_module_name_raw_done
    jsr append_char
    iny
    bne append_module_name_raw_loop
append_module_name_raw_done:
    rts

append_export_ptr_lower:
    ldy #$00
append_export_ptr_lower_loop:
    lda (export_ptr),y
    beq append_export_ptr_lower_done
    jsr lowercase_ascii
    jsr append_char
    iny
    bne append_export_ptr_lower_loop
append_export_ptr_lower_done:
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

append_newline:
    lda #10
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

lowercase_ascii:
    cmp #'A'
    bcc lowercase_ascii_done
    cmp #'Z'+1
    bcs lowercase_ascii_done
    ora #$20
lowercase_ascii_done:
    rts

build_module_stub_content:
    rts

.include "../common/action_project_module_arg.inc"
.include "../common/action_project_load.inc"
.include "../common/action_project_load_guard.inc"
.include "../common/action_project_entry.inc"
.include "../common/action_project_entry_guard.inc"
.include "../common/action_project_object_path.inc"
.include "../common/action_project_map_path.inc"
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
msg_no_object:
    .asciiz "NO OBJECT"
msg_probe_fail:
    .asciiz "PROBE FAIL"
msg_load_fail:
    .asciiz "LOAD FAIL"
msg_save_fail:
    .asciiz "SAVE FAIL"
msg_bad_avo:
    .asciiz "BAD AVO"
msg_too_large:
    .asciiz "TOO LARGE"
msg_unresolved:
    .asciiz "UNRESOLVED"
msg_created:
    .asciiz "CREATED"
msg_updated:
    .asciiz "UPDATED"
msg_ok:
    .asciiz "ALINK OK"

default_module_name:
    .asciiz "MAIN"
project_marker:
    .asciiz "ACTION.PROJ"

marker_imports:
    .byte 34,"imports",34,":[",0
marker_exports:
    .byte 34,"exports",34,":[",0
marker_calls:
    .byte 34,"calls",34,":[",0

import_rt_format_int:
    .asciiz "rt.format_int"
import_rt_print_line:
    .asciiz "rt.print_line"
import_rt_print_str:
    .asciiz "rt.print_str"
IMPORT_TABLE_COUNT = 3

import_bits_lo:
    .byte IMPORT_FORMAT_INT
    .byte IMPORT_PRINT_LINE
    .byte IMPORT_PRINT_STR
import_bits_hi:
    .byte $00
    .byte $00
    .byte $00
import_name_ptr_lo:
    .byte <import_rt_format_int
    .byte <import_rt_print_line
    .byte <import_rt_print_str
import_name_ptr_hi:
    .byte >import_rt_format_int
    .byte >import_rt_print_line
    .byte >import_rt_print_str

map_header:
    .byte "ALINK1",10,"MODULE ",0
map_object_prefix:
    .byte 10,"OBJECT OBJ/",0
map_object_suffix:
    .byte ".AVO",10,0
map_include_prefix:
    .byte "INCLUDE ",0
map_export_prefix:
    .byte "EXPORT ",0
map_call_prefix:
    .byte "CALL ",0
map_live_prefix:
    .byte "LIVE ",0
map_resolve_prefix:
    .byte "RESOLVE ",0

module_name:
    .res 25
manifest_entry:
    .res 32
target_path:
    .res 40
symbol_buffer:
    .res 25
source_buffer:
    .res SOURCE_LIMIT+1
content_buffer:
    .res 512
manifest_buffer:
    .res MANIFEST_LIMIT+1
export_names:
    .res 200
live_flags:
    .res 8
call_edge_masks:
    .res 8

bit_masks:
    .byte $01,$02,$04,$08,$10,$20,$40,$80
