.include "udos_services.inc"

.export start

MANIFEST_LIMIT = 191
SOURCE_LIMIT = 255
ALINK_TRACE = $03FC

IMPORT_PRINT_STR  = $01
IMPORT_PRINT_LINE = $02
IMPORT_FORMAT_INT = $04
PENDING_SYMBOL_MAX = 7

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

export_count = truncated_flag
export_index = save_mode
export_ptr = current_bit_lo
body_ptr = src_ptr

.code

start:
    lda #$10
    sta ALINK_TRACE
    lda #$11
    sta ALINK_TRACE
    jsr init_module_name
    lda #$12
    sta ALINK_TRACE
    jsr build_manifest_entry
    jsr require_loaded_project
    jsr require_manifest_entry_tracked
    lda #$13
    sta ALINK_TRACE
    jsr build_object_target_path
    jsr load_object_or_fail
    lda #$14
    sta ALINK_TRACE
    jsr parse_exports_or_fail
    lda #$15
    sta ALINK_TRACE
    jsr parse_body_ops_or_fail
    lda #$16
    sta ALINK_TRACE
    jsr parse_external_symbols_or_fail
    lda #$17
    sta ALINK_TRACE
    jsr parse_strings_or_fail
    lda #$18
    sta ALINK_TRACE
    jsr parse_ints_or_fail
    lda #$19
    sta ALINK_TRACE
    jsr parse_import_mask_or_fail
    lda #$1A
    sta ALINK_TRACE
    jsr compute_code_bytes
    lda #$1B
    sta ALINK_TRACE
    jsr build_live_set
    lda #$1C
    sta ALINK_TRACE
    jsr resolve_import_closure
    lda #$1D
    sta ALINK_TRACE
    jsr build_avm_text_content_or_fail
    jsr build_avm_text_target_path
    lda #$1E
    sta ALINK_TRACE
    lda #$A0
    sta $03FD
    lda save_params+4
    sta $03FE
    jsr save_content_buffer_to_target
    php
    pla
    sta $03FF
    lda save_params+4
    sta $03FE
    lda #$A1
    sta $03FD
    lda #$1D
    sta ALINK_TRACE
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
    jsr load_source_file
    bcc load_object_loaded
    lda file_params+6
    cmp #tool_file_status_nofile
    beq load_object_missing
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_object_missing:
    lda #<msg_no_object
    ldy #>msg_no_object
    jmp fail_with_ptr
load_object_loaded:
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_avo1_header_or_fail
    rts

append_external_object_from_x_or_fail:
    txa
    pha
    jsr save_module_name
    pla
    tax
    jsr copy_pending_symbol_to_module_name_from_x
    txa
    pha
    jsr build_object_target_path
    jsr load_object_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_avo1_header_or_fail
    jsr parse_exports_or_fail
    jsr parse_body_ops_or_fail
    jsr parse_external_symbols_or_fail
    jsr parse_ints_or_fail
    jsr require_linkable_child_body_ops_or_fail
    jsr compute_code_bytes
    jsr build_live_set
    jsr queue_current_external_symbols_or_fail
    jsr append_current_object_live_code_only
    jsr restore_module_name
    pla
    tax
    rts

require_loaded_source_not_truncated_or_fail:
    lda truncated_flag
    beq require_loaded_source_not_truncated_or_fail_done
    lda #<msg_too_large
    ldy #>msg_too_large
    jmp fail_with_ptr
require_loaded_source_not_truncated_or_fail_done:
    rts

require_avo1_header_or_fail:
    lda source_buffer+0
    cmp #'A'
    bne require_avo1_header_bad
    lda source_buffer+1
    cmp #'V'
    bne require_avo1_header_bad
    lda source_buffer+2
    cmp #'O'
    bne require_avo1_header_bad
    lda source_buffer+3
    cmp #'1'
    beq require_avo1_header_done
require_avo1_header_bad:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
require_avo1_header_done:
    rts

parse_exports_or_fail:
    lda #$00
    sta export_count
    jsr reset_scan_ptr_after_header
parse_exports_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq parse_exports_done_check
    lda #<line_export
    sta const_ptr
    lda #>line_export
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs parse_exports_next_line
    jsr advance_scan_ptr_by_const_ptr
    jsr copy_export_symbol_line_or_fail
    jsr require_space_or_fail
    jsr parse_decimal_byte_or_fail
    ldx export_count
    sta export_offsets,x
    jsr require_space_or_fail
    jsr parse_decimal_byte_or_fail
    ldx export_count
    sta proc_sizes,x
    inc export_count
parse_exports_next_line:
    jsr skip_current_line
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

copy_export_symbol_line_or_fail:
    lda export_count
    cmp #8
    bcc :+
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
:   ldx export_count
    jsr set_export_ptr_from_x
    ldy #$00
copy_export_symbol_line_or_fail_loop:
    lda (scan_ptr),y
    beq parse_exports_bad
    cmp #' '
    beq copy_export_symbol_line_or_fail_done
    cmp #10
    beq copy_export_symbol_line_or_fail_done
    cmp #13
    beq copy_export_symbol_line_or_fail_done
    sta (export_ptr),y
    iny
    cpy #24
    bcc copy_export_symbol_line_or_fail_loop
    jmp parse_exports_bad
copy_export_symbol_line_or_fail_done:
    cpy #$00
    beq parse_exports_bad
    lda #$00
    sta (export_ptr),y
copy_export_symbol_line_advance_loop:
    cpy #$00
    beq copy_export_symbol_line_advanced
    jsr advance_scan_ptr
    dey
    bne copy_export_symbol_line_advance_loop
copy_export_symbol_line_advanced:
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

set_external_ptr_from_x:
    lda #<external_names
    sta export_ptr
    lda #>external_names
    sta export_ptr+1
set_external_ptr_from_x_loop:
    cpx #$00
    beq set_external_ptr_from_x_done
    clc
    lda export_ptr
    adc #25
    sta export_ptr
    lda export_ptr+1
    adc #$00
    sta export_ptr+1
    dex
    bne set_external_ptr_from_x_loop
set_external_ptr_from_x_done:
    rts

set_pending_ptr_from_x:
    lda #<manifest_buffer
    sta export_ptr
    lda #>manifest_buffer
    sta export_ptr+1
set_pending_ptr_from_x_loop:
    cpx #$00
    beq set_pending_ptr_from_x_done
    clc
    lda export_ptr
    adc #25
    sta export_ptr
    lda export_ptr+1
    adc #$00
    sta export_ptr+1
    dex
    bne set_pending_ptr_from_x_loop
set_pending_ptr_from_x_done:
    rts

set_body_ptr_from_x:
    lda #<body_ops_data
    sta body_ptr
    lda #>body_ops_data
    sta body_ptr+1
set_body_ptr_from_x_loop:
    cpx #$00
    beq set_body_ptr_from_x_done
    clc
    lda body_ptr
    adc #16
    sta body_ptr
    lda body_ptr+1
    adc #$00
    sta body_ptr+1
    dex
    bne set_body_ptr_from_x_loop
set_body_ptr_from_x_done:
    rts

set_string_ptr_from_x:
    lda #<string_literals
    sta const_ptr
    lda #>string_literals
    sta const_ptr+1
set_string_ptr_from_x_loop:
    cpx #$00
    beq set_string_ptr_from_x_done
    clc
    lda const_ptr
    adc #24
    sta const_ptr
    lda const_ptr+1
    adc #$00
    sta const_ptr+1
    dex
    bne set_string_ptr_from_x_loop
set_string_ptr_from_x_done:
    rts

parse_imports_or_fail:
    rts

parse_body_ops_or_fail:
    lda #$00
    sta export_index
    jsr reset_scan_ptr_after_header
parse_body_ops_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq parse_body_ops_done_check
    lda #<line_body
    sta const_ptr
    lda #>line_body
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs parse_body_ops_next_line
    jsr advance_scan_ptr_by_const_ptr
    lda export_index
    cmp export_count
    bcc :+
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
:   ldx export_index
    jsr set_body_ptr_from_x
    ldy #$00
parse_body_ops_string_loop:
    lda (scan_ptr),y
    beq parse_body_ops_string_done
    cmp #10
    beq parse_body_ops_string_done
    cmp #13
    beq parse_body_ops_string_done
    cmp #'c'
    beq parse_body_ops_store
    cmp #'u'
    beq parse_body_ops_store
    cmp #'s'
    beq parse_body_ops_store
    cmp #'i'
    beq parse_body_ops_store
    cmp #'r'
    beq parse_body_ops_store
    cmp #'0'
    bcc parse_body_ops_bad
    cmp #'7'+1
    bcs parse_body_ops_bad
parse_body_ops_store:
    sta (body_ptr),y
    iny
    cpy #15
    bcc parse_body_ops_string_loop
parse_body_ops_bad:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
parse_body_ops_string_done:
    lda #$00
    sta (body_ptr),y
    inc export_index
parse_body_ops_next_line:
    jsr skip_current_line
    jmp parse_body_ops_loop
parse_body_ops_done_check:
    lda export_index
    cmp export_count
    beq parse_body_ops_done
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
parse_body_ops_done:
    rts

parse_external_symbols_or_fail:
    lda #$00
    sta external_count
    jsr reset_scan_ptr_after_header
parse_external_symbols_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq parse_external_symbols_done
    lda #<line_external
    sta const_ptr
    lda #>line_external
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs parse_external_symbols_next_line
    jsr advance_scan_ptr_by_const_ptr
    jsr copy_external_symbol_line_or_fail
parse_external_symbols_next_line:
    jsr skip_current_line
    jmp parse_external_symbols_loop
parse_external_symbols_done:
    rts

copy_external_symbol_line_or_fail:
    lda external_count
    cmp #8
    bcc :+
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
:   ldx external_count
    jsr set_external_ptr_from_x
    ldy #$00
copy_external_symbol_line_or_fail_loop:
    lda (scan_ptr),y
    beq copy_external_symbol_line_or_fail_done
    cmp #' '
    beq copy_external_symbol_line_or_fail_done
    cmp #10
    beq copy_external_symbol_line_or_fail_done
    cmp #13
    beq copy_external_symbol_line_or_fail_done
    jsr lowercase_ascii
    cmp #'a'
    bcc copy_external_symbol_line_or_fail_symbol
    cmp #'z'+1
    bcc copy_external_symbol_line_or_fail_store
copy_external_symbol_line_or_fail_symbol:
    cmp #'0'
    bcc copy_external_symbol_line_or_fail_check_underscore
    cmp #'9'+1
    bcc copy_external_symbol_line_or_fail_store
copy_external_symbol_line_or_fail_check_underscore:
    cmp #'_'
    bne copy_external_symbol_line_or_fail_bad
copy_external_symbol_line_or_fail_store:
    sta (export_ptr),y
    iny
    cpy #24
    bcc copy_external_symbol_line_or_fail_loop
copy_external_symbol_line_or_fail_bad:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
copy_external_symbol_line_or_fail_done:
    cpy #$00
    beq copy_external_symbol_line_or_fail_bad
    lda #$00
    sta (export_ptr),y
    inc external_count
    rts

parse_strings_or_fail:
    lda #$00
    sta string_count
    jsr reset_scan_ptr_after_header
parse_strings_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq parse_strings_done
    lda #<line_string
    sta const_ptr
    lda #>line_string
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs parse_strings_next_line
    jsr advance_scan_ptr_by_const_ptr
    ldx string_count
    cpx #8
    bcc :+
parse_strings_bad:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
:   jsr set_string_ptr_from_x
    ldy #$00
parse_strings_value_loop:
    lda (scan_ptr),y
    beq parse_strings_value_done
    cmp #10
    beq parse_strings_value_done
    cmp #13
    beq parse_strings_done
    sta (const_ptr),y
    iny
    cpy #23
    bcc parse_strings_value_loop
    jmp parse_strings_bad
parse_strings_value_done:
    lda #$00
    sta (const_ptr),y
    inc string_count
parse_strings_next_line:
    jsr skip_current_line
    jmp parse_strings_loop
parse_strings_done:
    rts

parse_ints_or_fail:
    lda #$00
    sta int_count
    jsr reset_scan_ptr_after_header
parse_ints_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq parse_ints_done
    lda #<line_int
    sta const_ptr
    lda #>line_int
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs parse_ints_next_line
    jsr advance_scan_ptr_by_const_ptr
    ldx int_count
    cpx #8
    bcc :+
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
:   jsr parse_decimal_byte_or_fail
    ldx int_count
    sta int_values_lo,x
    lda #$00
    sta int_values_hi,x
    inc int_count
parse_ints_next_line:
    jsr skip_current_line
    jmp parse_ints_loop
parse_ints_done:
    rts

parse_import_mask_or_fail:
    lda #$00
    sta main_flags_lo
    sta main_flags_hi
    jsr reset_scan_ptr_after_header
parse_import_mask_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq parse_import_mask_missing
    lda #<line_import_mask
    sta const_ptr
    lda #>line_import_mask
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs parse_import_mask_next_line
    jsr advance_scan_ptr_by_const_ptr
    jsr parse_decimal_byte_or_fail
    sta main_flags_lo
    rts
parse_import_mask_next_line:
    jsr skip_current_line
    jmp parse_import_mask_loop
parse_import_mask_missing:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr

reset_scan_ptr_after_header:
    lda #<(source_buffer+4)
    sta scan_ptr
    lda #>(source_buffer+4)
    sta scan_ptr+1
    rts

require_space_or_fail:
    ldy #$00
    lda (scan_ptr),y
    cmp #' '
    beq require_space_or_fail_ok
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
require_space_or_fail_ok:
    jsr advance_scan_ptr
    rts

compute_code_bytes:
    lda #$00
    sta payload_bytes_data
    ldx #$00
compute_code_bytes_loop:
    cpx export_count
    beq compute_code_bytes_done
    lda export_offsets,x
    clc
    adc proc_sizes,x
    cmp payload_bytes_data
    bcc compute_code_bytes_next
    sta payload_bytes_data
compute_code_bytes_next:
    inx
    bne compute_code_bytes_loop
compute_code_bytes_done:
    rts

parse_decimal_byte_or_fail:
    lda #$00
    sta current_bit_lo
    sta compare_char
parse_decimal_byte_or_fail_loop:
    ldy #$00
    lda (scan_ptr),y
    cmp #'0'
    bcc parse_decimal_byte_or_fail_done_check
    cmp #'9'+1
    bcs parse_decimal_byte_or_fail_done_check
    sec
    sbc #'0'
    pha
    lda current_bit_lo
    asl a
    sta current_bit_hi
    asl a
    asl a
    clc
    adc current_bit_hi
    bcs parse_decimal_byte_or_fail_bad
    sta current_bit_lo
    pla
    clc
    adc current_bit_lo
    bcs parse_decimal_byte_or_fail_bad
    sta current_bit_lo
    lda #$01
    sta compare_char
    jsr advance_scan_ptr
    jmp parse_decimal_byte_or_fail_loop
parse_decimal_byte_or_fail_done_check:
    lda compare_char
    beq parse_decimal_byte_or_fail_bad
    lda current_bit_lo
    rts
parse_decimal_byte_or_fail_bad:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr

require_linkable_child_body_ops_or_fail:
    ldx #$00
require_linkable_child_body_ops_or_fail_export_loop:
    cpx export_count
    beq require_linkable_child_body_ops_or_fail_done
    txa
    pha
    jsr set_body_ptr_from_x
    ldy #$00
require_linkable_child_body_ops_or_fail_body_loop:
    lda (body_ptr),y
    beq require_linkable_child_body_ops_or_fail_next_export
    cmp #'s'
    beq require_linkable_child_body_ops_or_fail_bad
    iny
    bne require_linkable_child_body_ops_or_fail_body_loop
require_linkable_child_body_ops_or_fail_bad:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
require_linkable_child_body_ops_or_fail_next_export:
    pla
    tax
    inx
    bne require_linkable_child_body_ops_or_fail_export_loop
require_linkable_child_body_ops_or_fail_done:
    rts

build_live_set:
    lda #$00
    ldx #$00
build_live_set_clear_loop:
    cpx #8
    beq build_live_set_seed
    sta live_flags,x
    inx
    bne build_live_set_clear_loop
build_live_set_seed:
    lda export_count
    bne :+
    jmp build_live_set_done
:   jsr find_export_index_from_module_name
    bcc :+
    jmp build_live_set_bad
: 
    lda #$01
    sta live_flags,x
build_live_set_scan_again:
    lda #$00
    sta compare_char
    ldx #$00
build_live_set_export_loop:
    cpx export_count
    beq build_live_set_check
    lda live_flags,x
    beq build_live_set_next_export
    stx current_bit_hi
    jsr set_body_ptr_from_x
    ldy #$00
build_live_set_body_loop:
    lda (body_ptr),y
    beq build_live_set_next_export_restore
    cmp #'c'
    beq build_live_set_call
    cmp #'u'
    beq build_live_set_skip_pair
    cmp #'s'
    beq build_live_set_skip_pair
    cmp #'i'
    beq build_live_set_skip_pair
    cmp #'r'
    beq build_live_set_ret
    jmp build_live_set_bad
build_live_set_call:
    iny
    lda (body_ptr),y
    cmp #'0'
    bcc build_live_set_bad
    cmp #'7'+1
    bcs build_live_set_bad
    sec
    sbc #'0'
    tax
    lda live_flags,x
    bne build_live_set_call_done
    lda #$01
    sta live_flags,x
    sta compare_char
build_live_set_call_done:
    ldx current_bit_hi
    iny
    bne build_live_set_body_loop
build_live_set_skip_pair:
    iny
    iny
    bne build_live_set_body_loop
build_live_set_ret:
    iny
    bne build_live_set_body_loop
build_live_set_next_export_restore:
    ldx current_bit_hi
build_live_set_next_export:
    inx
    bne build_live_set_export_loop
build_live_set_check:
    lda compare_char
    bne build_live_set_scan_again
build_live_set_done:
    rts
build_live_set_bad:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr

clear_tool_scratch_before_save:
    lda #$00
    ldx #$00
clear_tool_scratch_before_save_loop:
    sta file_params,x
    inx
    cpx #(truncated_flag - file_params + 1)
    bcc clear_tool_scratch_before_save_loop
    rts

find_export_index_from_module_name:
    ldx #$00
find_export_index_from_module_name_loop:
    cpx export_count
    beq find_export_index_from_module_name_fail
    stx compare_char
    jsr set_export_ptr_from_x
    ldx compare_char
    ldy #$00
find_export_index_from_module_name_compare_loop:
    lda module_name,y
    jsr lowercase_ascii
    cmp (export_ptr),y
    bne find_export_index_from_module_name_next
    lda (export_ptr),y
    beq find_export_index_from_module_name_done
    iny
    bne find_export_index_from_module_name_compare_loop
find_export_index_from_module_name_next:
    inx
    bne find_export_index_from_module_name_loop
find_export_index_from_module_name_fail:
    sec
    rts
find_export_index_from_module_name_done:
    clc
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

build_avm_text_content_or_fail:
    lda #<content_buffer
    sta content_ptr
    lda #>content_buffer
    sta content_ptr+1
    lda #<avm_txt_entry_prefix
    sta const_ptr
    lda #>avm_txt_entry_prefix
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_module_symbol_lower
    jsr append_newline
    lda #$00
    sta string_use_mask
    sta pending_count
    jsr append_current_object_live_code_only
    jsr queue_current_external_symbols_or_fail
build_avm_text_pending_loop:
    ldx #$00
build_avm_text_pending_loop_next:
    cpx pending_count
    beq build_avm_text_strings
    txa
    pha
    jsr append_external_object_from_x_or_fail
    pla
    tax
    inx
    bne build_avm_text_pending_loop_next
build_avm_text_strings:
    ldx #$00
build_avm_text_strings_loop:
    cpx string_count
    beq build_avm_text_done
    lda bit_masks,x
    and string_use_mask
    beq build_avm_text_next_string
    txa
    pha
    jsr append_string_definition_from_x
    pla
    tax
build_avm_text_next_string:
    inx
    bne build_avm_text_strings_loop
build_avm_text_done:
    lda #$00
    jmp append_char

append_current_object_live_code_only:
    lda #$00
    sta main_flags_hi
append_current_object_live_code_only_proc_scan_loop:
    lda main_flags_hi
    cmp payload_bytes_data
    beq append_current_object_live_code_only_done
    jsr find_live_export_at_current_offset
    bcs append_current_object_live_code_only_gap
    stx export_index
    jsr append_export_label_from_x
    ldx export_index
    jsr append_live_call_lines_for_export_x
    clc
    lda main_flags_hi
    adc proc_sizes,x
    sta main_flags_hi
    bcc append_current_object_live_code_only_proc_scan_loop
    beq append_current_object_live_code_only_done
    jmp append_current_object_live_code_only_proc_scan_loop
append_current_object_live_code_only_gap:
    inc main_flags_hi
    bne append_current_object_live_code_only_proc_scan_loop
append_current_object_live_code_only_done:
    rts

find_live_export_at_current_offset:
    ldx #$00
find_live_export_at_current_offset_loop:
    cpx export_count
    beq find_live_export_at_current_offset_fail
    lda live_flags,x
    beq find_live_export_at_current_offset_next
    lda export_offsets,x
    cmp main_flags_hi
    beq find_live_export_at_current_offset_done
find_live_export_at_current_offset_next:
    inx
    bne find_live_export_at_current_offset_loop
find_live_export_at_current_offset_fail:
    sec
    rts
find_live_export_at_current_offset_done:
    clc
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

append_export_label_from_x:
    jsr set_export_ptr_from_x
    jsr append_export_ptr_lower
    lda #':'
    jsr append_char
    jmp append_newline

append_external_label_from_x:
    jsr set_external_ptr_from_x
    jsr append_export_ptr_lower
    lda #':'
    jsr append_char
    jmp append_newline

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

append_live_call_lines_for_export_x:
    txa
    pha
    jsr set_body_ptr_from_x
    ldy #$00
append_live_call_lines_for_export_x_loop:
    lda (body_ptr),y
    bne :+
    jmp append_live_call_lines_for_export_x_done
: 
    cmp #'c'
    beq append_live_call_lines_for_export_x_call
    cmp #'u'
    beq append_live_call_lines_for_export_x_external
    cmp #'s'
    beq append_live_call_lines_for_export_x_print
    cmp #'i'
    beq :+
    cmp #'r'
    beq :++
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
:   jmp append_live_call_lines_for_export_x_printie
:   jmp append_live_call_lines_for_export_x_ret
append_live_call_lines_for_export_x_call:
    iny
    lda (body_ptr),y
    cmp #'0'
    bcc :+
    cmp #'7'+1
    bcs :+
    sec
    sbc #'0'
    sta current_bit_hi
    tya
    sta compare_char
    lda #<avm_txt_call_prefix
    sta const_ptr
    lda #>avm_txt_call_prefix
    sta const_ptr+1
    jsr append_const_ptr
    ldx current_bit_hi
    jsr set_export_ptr_from_x
    jsr append_export_ptr_lower
    jsr append_newline
    ldy compare_char
    iny
    bne append_live_call_lines_for_export_x_loop
:   jmp append_live_call_lines_for_export_x_bad
append_live_call_lines_for_export_x_external:
    iny
    lda (body_ptr),y
    cmp #'0'
    bcc append_live_call_lines_for_export_x_bad
    cmp #'7'+1
    bcs append_live_call_lines_for_export_x_bad
    sec
    sbc #'0'
    sta current_bit_hi
    tya
    sta compare_char
    lda #<avm_txt_call_prefix
    sta const_ptr
    lda #>avm_txt_call_prefix
    sta const_ptr+1
    jsr append_const_ptr
    ldx current_bit_hi
    jsr set_external_ptr_from_x
    jsr append_export_ptr_lower
    jsr append_newline
    ldy compare_char
    iny
    jmp append_live_call_lines_for_export_x_loop
append_live_call_lines_for_export_x_print:
    iny
    lda (body_ptr),y
    cmp #'0'
    bcc append_live_call_lines_for_export_x_bad
    cmp #'7'+1
    bcs append_live_call_lines_for_export_x_bad
    sec
    sbc #'0'
    tax
    lda bit_masks,x
    ora string_use_mask
    sta string_use_mask
    tya
    sta compare_char
    jsr append_setp16_string_from_x
    jsr append_calln_print_line
    ldy compare_char
    iny
    jmp append_live_call_lines_for_export_x_loop
append_live_call_lines_for_export_x_printie:
    iny
    lda (body_ptr),y
    cmp #'0'
    bcc append_live_call_lines_for_export_x_bad
    cmp #'7'+1
    bcs append_live_call_lines_for_export_x_bad
    sec
    sbc #'0'
    tax
    tya
    sta compare_char
    jsr append_push16_int_from_x
    jsr append_calln_printie_line
    ldy compare_char
    iny
    jmp append_live_call_lines_for_export_x_loop
append_live_call_lines_for_export_x_ret:
    tya
    sta compare_char
    jsr append_ret_line
    ldy compare_char
    iny
    jmp append_live_call_lines_for_export_x_loop
append_live_call_lines_for_export_x_bad:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
append_live_call_lines_for_export_x_done:
    pla
    tax
    rts

append_ret_line:
    lda #<avm_txt_ret
    sta const_ptr
    lda #>avm_txt_ret
    sta const_ptr+1
    jsr append_const_ptr
    jmp append_newline

append_calln_print_line:
    lda #<avm_txt_calln_print
    sta const_ptr
    lda #>avm_txt_calln_print
    sta const_ptr+1
    jsr append_const_ptr
    jmp append_newline

append_calln_printie_line:
    lda #<avm_txt_calln_printie
    sta const_ptr
    lda #>avm_txt_calln_printie
    sta const_ptr+1
    jsr append_const_ptr
    jmp append_newline

append_push16_int_from_x:
    txa
    pha
    lda #<avm_txt_push16_prefix
    sta const_ptr
    lda #>avm_txt_push16_prefix
    sta const_ptr+1
    jsr append_const_ptr
    pla
    tax
    lda int_values_hi,x
    bne append_live_call_lines_for_export_x_bad
    lda int_values_lo,x
    jsr append_small_decimal
    jmp append_newline

append_setp16_string_from_x:
    txa
    pha
    lda #<avm_txt_setp16_prefix
    sta const_ptr
    lda #>avm_txt_setp16_prefix
    sta const_ptr+1
    jsr append_const_ptr
    pla
    tax
    jsr append_module_string_label_from_x
    jmp append_newline

append_string_definition_from_x:
    txa
    pha
    jsr append_module_string_label_from_x
    lda #':'
    jsr append_char
    jsr append_newline
    lda #<avm_txt_stringz_prefix
    sta const_ptr
    lda #>avm_txt_stringz_prefix
    sta const_ptr+1
    jsr append_const_ptr
    pla
    tax
    txa
    pha
    jsr set_string_ptr_from_x
    ldy #$00
append_string_definition_value_loop:
    lda (const_ptr),y
    beq append_string_definition_value_done
    jsr append_char
    iny
    bne append_string_definition_value_loop
append_string_definition_value_done:
    lda #<avm_txt_stringz_suffix
    sta const_ptr
    lda #>avm_txt_stringz_suffix
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_newline
    pla
    tax
    rts

append_module_string_label_from_x:
    txa
    pha
    jsr append_module_symbol_lower
    lda #'_'
    jsr append_char
    lda #'s'
    jsr append_char
    lda #'t'
    jsr append_char
    lda #'r'
    jsr append_char
    pla
    jsr append_small_decimal
    rts

append_small_decimal:
    cmp #10
    bcc append_small_decimal_ones
    ldx #$00
append_small_decimal_tens_loop:
    cmp #10
    bcc append_small_decimal_tens_done
    sec
    sbc #10
    inx
    bne append_small_decimal_tens_loop
append_small_decimal_tens_done:
    pha
    txa
    clc
    adc #'0'
    jsr append_char
    pla
append_small_decimal_ones:
    clc
    adc #'0'
    jmp append_char

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

save_module_name:
    ldy #$00
save_module_name_loop:
    lda module_name,y
    sta saved_module_name,y
    beq save_module_name_done
    iny
    cpy #25
    bcc save_module_name_loop
save_module_name_done:
    rts

restore_module_name:
    ldy #$00
restore_module_name_loop:
    lda saved_module_name,y
    sta module_name,y
    beq restore_module_name_done
    iny
    cpy #25
    bcc restore_module_name_loop
restore_module_name_done:
    rts

copy_export_ptr_to_module_name:
    ldy #$00
copy_export_ptr_to_module_name_loop:
    lda (export_ptr),y
    sta module_name,y
    beq copy_export_ptr_to_module_name_done
    iny
    cpy #25
    bcc copy_export_ptr_to_module_name_loop
copy_export_ptr_to_module_name_done:
    lda #$00
    sta module_name+24
    rts

copy_export_ptr_to_symbol_buffer:
    ldy #$00
copy_export_ptr_to_symbol_buffer_loop:
    lda (export_ptr),y
    sta symbol_buffer,y
    beq copy_export_ptr_to_symbol_buffer_done
    iny
    cpy #25
    bcc copy_export_ptr_to_symbol_buffer_loop
copy_export_ptr_to_symbol_buffer_done:
    lda #$00
    sta symbol_buffer+24
    rts

queue_current_external_symbols_or_fail:
    ldx #$00
queue_current_external_symbols_or_fail_loop:
    cpx external_count
    beq queue_current_external_symbols_or_fail_done
    txa
    pha
    jsr set_external_ptr_from_x
    jsr copy_export_ptr_to_symbol_buffer
    jsr enqueue_symbol_buffer_if_new_or_fail
queue_current_external_symbols_or_fail_next:
    pla
    tax
    inx
    bne queue_current_external_symbols_or_fail_loop
queue_current_external_symbols_or_fail_done:
    rts

enqueue_symbol_buffer_if_new_or_fail:
    ldx #$00
enqueue_symbol_buffer_if_new_or_fail_loop:
    cpx pending_count
    beq enqueue_symbol_buffer_if_new_or_fail_store
    stx compare_char
    jsr set_pending_ptr_from_x
    lda export_ptr
    sta const_ptr
    lda export_ptr+1
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcc enqueue_symbol_buffer_if_new_or_fail_done
    ldx compare_char
    inx
    bne enqueue_symbol_buffer_if_new_or_fail_loop
enqueue_symbol_buffer_if_new_or_fail_store:
    cpx #PENDING_SYMBOL_MAX
    bcc :+
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
:   jsr set_pending_ptr_from_x
    jsr copy_symbol_buffer_to_export_ptr
    inc pending_count
enqueue_symbol_buffer_if_new_or_fail_done:
    rts

copy_symbol_buffer_to_export_ptr:
    ldy #$00
copy_symbol_buffer_to_export_ptr_loop:
    lda symbol_buffer,y
    sta (export_ptr),y
    beq copy_symbol_buffer_to_export_ptr_done
    iny
    cpy #25
    bcc copy_symbol_buffer_to_export_ptr_loop
copy_symbol_buffer_to_export_ptr_done:
    lda #$00
    sta (export_ptr),y
    rts

copy_pending_symbol_to_module_name_from_x:
    jsr set_pending_ptr_from_x
    jmp copy_export_ptr_to_module_name

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
.include "../common/action_project_avm_text_path.inc"
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

line_import_mask:
    .byte "k ",0
line_export:
    .byte "x ",0
line_body:
    .byte "b ",0
line_external:
    .byte "u ",0
line_string:
    .byte "s ",0
line_int:
    .byte "i ",0

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

avm_txt_entry_prefix:
    .byte "entry ",0
avm_txt_call_prefix:
    .byte "call ",0
avm_txt_setp16_prefix:
    .byte "setp16 ",0
avm_txt_push16_prefix:
    .byte "push16 ",0
avm_txt_calln_print:
    .byte "calln print",0
avm_txt_calln_printie:
    .byte "calln printie",0
avm_txt_ret:
    .byte "ret",0
avm_txt_stringz_prefix:
    .byte "stringz ",0
avm_txt_stringz_suffix:
    .byte 0
bit_masks:
    .byte $01,$02,$04,$08,$10,$20,$40,$80

module_name:
    .res 25
target_path:
    .res 40

.segment "BSS"

source_buffer:
    .res SOURCE_LIMIT+1
content_buffer:
    .res 256
saved_module_name:
    .res 25
export_names:
    .res 200
export_offsets:
    .res 8
proc_sizes:
    .res 8
string_literals:
    .res 192
string_count:
    .res 1
payload_bytes_data:
    .res 1
live_flags:
    .res 8
string_use_mask:
    .res 1
body_ops_data:
    .res 128
manifest_entry:
    .res 32
external_names:
    .res 200
external_count:
    .res 1
pending_count:
    .res 1
symbol_buffer:
    .res 25
manifest_buffer:
    .res MANIFEST_LIMIT+1
int_values_lo:
    .res 8
int_values_hi:
    .res 8
int_count:
    .res 1
bss_end:
