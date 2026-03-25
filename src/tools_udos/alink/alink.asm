.include "udos_services.inc"

.export start

MANIFEST_LIMIT = 191
SOURCE_LIMIT = 511

IMPORT_PRINT_STR  = $01
IMPORT_PRINT_LINE = $02
IMPORT_FORMAT_INT = $04
IMPORT_PRINT_F    = $08
IMPORT_REU_ALLOC  = $10
IMPORT_REU_PEEK8  = $20
IMPORT_REU_PEEK16 = $40
IMPORT_REU_POKE8  = $80

IMPORT_REU_POKE16 = $01
IMPORT_OVL_LOAD   = $02
IMPORT_OVL_CALL   = $04

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

.code

start:
    jsr init_module_name
    jsr build_manifest_entry
    jsr require_loaded_project
    jsr require_manifest_entry_tracked
    jsr build_object_target_path
    jsr load_object_or_fail
    jsr parse_imports_or_fail
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
    lda #$11
    sta $03FC
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
:   lda #<import_rt_ovl_call
    sta const_ptr
    lda #>import_rt_ovl_call
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #IMPORT_OVL_CALL
    sta current_bit_hi
    rts
:   lda #<import_rt_ovl_load
    sta const_ptr
    lda #>import_rt_ovl_load
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #IMPORT_OVL_LOAD
    sta current_bit_hi
    rts
:   lda #<import_rt_print_f
    sta const_ptr
    lda #>import_rt_print_f
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #IMPORT_PRINT_F
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
    bcs :+
    lda #IMPORT_PRINT_STR
    sta current_bit_lo
    rts
:   lda #<import_rt_reu_alloc
    sta const_ptr
    lda #>import_rt_reu_alloc
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #IMPORT_REU_ALLOC
    sta current_bit_lo
    rts
:   lda #<import_rt_reu_peek16
    sta const_ptr
    lda #>import_rt_reu_peek16
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #IMPORT_REU_PEEK16
    sta current_bit_lo
    rts
:   lda #<import_rt_reu_peek8
    sta const_ptr
    lda #>import_rt_reu_peek8
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #IMPORT_REU_PEEK8
    sta current_bit_lo
    rts
:   lda #<import_rt_reu_poke16
    sta const_ptr
    lda #>import_rt_reu_poke16
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #IMPORT_REU_POKE16
    sta current_bit_hi
    rts
:   lda #<import_rt_reu_poke8
    sta const_ptr
    lda #>import_rt_reu_poke8
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs map_symbol_unresolved
    lda #IMPORT_REU_POKE8
    sta current_bit_lo
    rts
map_symbol_unresolved:
    lda #<msg_unresolved
    ldy #>msg_unresolved
    jmp fail_with_ptr

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

    lda #<map_include_prefix
    sta const_ptr
    lda #>map_include_prefix
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_module_symbol_lower
    jsr append_newline
    jsr append_import_include_lines
    jsr append_main_resolve_lines
    lda main_flags_lo
    and #IMPORT_PRINT_LINE
    beq :+
    lda #<map_resolve_prefix
    sta const_ptr
    lda #>map_resolve_prefix
    sta const_ptr+1
    jsr append_const_ptr
    lda #<import_rt_print_line
    sta const_ptr
    lda #>import_rt_print_line
    sta const_ptr+1
    jsr append_const_ptr
    lda #' '
    jsr append_char
    lda #<import_rt_print_str
    sta const_ptr
    lda #>import_rt_print_str
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_newline
:   lda #$00
    jmp append_char

append_import_include_lines:
    lda main_flags_lo
    and #IMPORT_FORMAT_INT
    beq append_import_include_lines_skip_format_int
    lda #<map_include_prefix
    sta const_ptr
    lda #>map_include_prefix
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_rt_format_int_literal
    jsr append_newline
append_import_include_lines_skip_format_int:
    lda main_flags_hi
    and #IMPORT_OVL_CALL
    beq append_import_include_lines_skip_ovl_call
    lda #<map_include_prefix
    sta const_ptr
    lda #>map_include_prefix
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_rt_ovl_call_literal
    jsr append_newline
append_import_include_lines_skip_ovl_call:
    lda main_flags_hi
    and #IMPORT_OVL_LOAD
    beq append_import_include_lines_skip_ovl_load
    lda #<map_include_prefix
    sta const_ptr
    lda #>map_include_prefix
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_rt_ovl_load_literal
    jsr append_newline
append_import_include_lines_skip_ovl_load:
    lda main_flags_lo
    and #IMPORT_PRINT_F
    beq append_import_include_lines_skip_print_f
    lda #<map_include_prefix
    sta const_ptr
    lda #>map_include_prefix
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_rt_print_f_literal
    jsr append_newline
append_import_include_lines_skip_print_f:
    lda main_flags_lo
    and #IMPORT_PRINT_LINE
    beq append_import_include_lines_skip_print_line
    lda #<map_include_prefix
    sta const_ptr
    lda #>map_include_prefix
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_rt_print_line_literal
    jsr append_newline
append_import_include_lines_skip_print_line:
    lda main_flags_lo
    and #IMPORT_PRINT_STR
    beq append_import_include_lines_done
    lda #<map_include_prefix
    sta const_ptr
    lda #>map_include_prefix
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_rt_print_str_literal
    jsr append_newline
append_import_include_lines_done:
    rts

append_main_resolve_lines:
    lda main_flags_lo
    and #IMPORT_FORMAT_INT
    beq append_main_resolve_lines_skip_format_int
    jsr append_main_resolve_prefix
    jsr append_rt_format_int_literal
    jsr append_newline
append_main_resolve_lines_skip_format_int:
    lda main_flags_hi
    and #IMPORT_OVL_CALL
    beq append_main_resolve_lines_skip_ovl_call
    jsr append_main_resolve_prefix
    jsr append_rt_ovl_call_literal
    jsr append_newline
append_main_resolve_lines_skip_ovl_call:
    lda main_flags_hi
    and #IMPORT_OVL_LOAD
    beq append_main_resolve_lines_skip_ovl_load
    jsr append_main_resolve_prefix
    jsr append_rt_ovl_load_literal
    jsr append_newline
append_main_resolve_lines_skip_ovl_load:
    lda main_flags_lo
    and #IMPORT_PRINT_F
    beq append_main_resolve_lines_skip_print_f
    jsr append_main_resolve_prefix
    jsr append_rt_print_f_literal
    jsr append_newline
append_main_resolve_lines_skip_print_f:
    lda main_flags_lo
    and #IMPORT_PRINT_LINE
    beq append_main_resolve_lines_skip_print_line
    jsr append_main_resolve_prefix
    jsr append_rt_print_line_literal
    jsr append_newline
append_main_resolve_lines_skip_print_line:
    lda main_flags_lo
    and #IMPORT_PRINT_STR
    beq append_main_resolve_lines_done
    jsr append_main_resolve_prefix
    jsr append_rt_print_str_literal
    jsr append_newline
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

append_rt_format_int_literal:
    lda #'r'
    jsr append_char
    lda #'t'
    jsr append_char
    lda #'.'
    jsr append_char
    lda #'f'
    jsr append_char
    lda #'o'
    jsr append_char
    lda #'r'
    jsr append_char
    lda #'m'
    jsr append_char
    lda #'a'
    jsr append_char
    lda #'t'
    jsr append_char
    lda #'_'
    jsr append_char
    lda #'i'
    jsr append_char
    lda #'n'
    jsr append_char
    lda #'t'
    jmp append_char

append_rt_ovl_call_literal:
    lda #'r'
    jsr append_char
    lda #'t'
    jsr append_char
    lda #'.'
    jsr append_char
    lda #'o'
    jsr append_char
    lda #'v'
    jsr append_char
    lda #'l'
    jsr append_char
    lda #'_'
    jsr append_char
    lda #'c'
    jsr append_char
    lda #'a'
    jsr append_char
    lda #'l'
    jsr append_char
    lda #'l'
    jmp append_char

append_rt_ovl_load_literal:
    lda #'r'
    jsr append_char
    lda #'t'
    jsr append_char
    lda #'.'
    jsr append_char
    lda #'o'
    jsr append_char
    lda #'v'
    jsr append_char
    lda #'l'
    jsr append_char
    lda #'_'
    jsr append_char
    lda #'l'
    jsr append_char
    lda #'o'
    jsr append_char
    lda #'a'
    jsr append_char
    lda #'d'
    jmp append_char

append_rt_print_f_literal:
    lda #'r'
    jsr append_char
    lda #'t'
    jsr append_char
    lda #'.'
    jsr append_char
    lda #'p'
    jsr append_char
    lda #'r'
    jsr append_char
    lda #'i'
    jsr append_char
    lda #'n'
    jsr append_char
    lda #'t'
    jsr append_char
    lda #'_'
    jsr append_char
    lda #'f'
    jmp append_char

append_rt_print_line_literal:
    lda #'r'
    jsr append_char
    lda #'t'
    jsr append_char
    lda #'.'
    jsr append_char
    lda #'p'
    jsr append_char
    lda #'r'
    jsr append_char
    lda #'i'
    jsr append_char
    lda #'n'
    jsr append_char
    lda #'t'
    jsr append_char
    lda #'_'
    jsr append_char
    lda #'l'
    jsr append_char
    lda #'i'
    jsr append_char
    lda #'n'
    jsr append_char
    lda #'e'
    jmp append_char

append_rt_print_str_literal:
    lda #'r'
    jsr append_char
    lda #'t'
    jsr append_char
    lda #'.'
    jsr append_char
    lda #'p'
    jsr append_char
    lda #'r'
    jsr append_char
    lda #'i'
    jsr append_char
    lda #'n'
    jsr append_char
    lda #'t'
    jsr append_char
    lda #'_'
    jsr append_char
    lda #'s'
    jsr append_char
    lda #'t'
    jsr append_char
    lda #'r'
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

import_rt_format_int:
    .asciiz "rt.format_int"
import_rt_ovl_call:
    .asciiz "rt.ovl_call"
import_rt_ovl_load:
    .asciiz "rt.ovl_load"
import_rt_print_f:
    .asciiz "rt.print_f"
import_rt_print_line:
    .asciiz "rt.print_line"
import_rt_print_str:
    .asciiz "rt.print_str"
import_rt_reu_alloc:
    .asciiz "rt.reu_alloc"
import_rt_reu_peek16:
    .asciiz "rt.reu_peek16"
import_rt_reu_peek8:
    .asciiz "rt.reu_peek8"
import_rt_reu_poke16:
    .asciiz "rt.reu_poke16"
import_rt_reu_poke8:
    .asciiz "rt.reu_poke8"

map_header:
    .byte "ALINK1",10,"MODULE ",0
map_object_prefix:
    .byte 10,"OBJECT OBJ/",0
map_object_suffix:
    .byte ".AVO",10,0
map_include_prefix:
    .byte "INCLUDE ",0
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
    .res 384
manifest_buffer:
    .res MANIFEST_LIMIT+1
