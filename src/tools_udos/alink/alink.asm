.include "udos_services.inc"

.export start

MANIFEST_LIMIT = 191
SOURCE_LIMIT = 255
BODY_OPS_STRIDE = 24
AVM_VERSION = 2
AVM_FLAG_ACHERON = 1
AVM_HEADER_SIZE = 12

PENDING_SYMBOL_MAX = 7
OPCODE_PUSH16 = $11
OPCODE_ADD = $14
OPCODE_SUB = $15
OPCODE_EQ = $16
OPCODE_NE = $17
OPCODE_LT = $1C
OPCODE_GT = $1D
OPCODE_CALL = $45
OPCODE_RET = $48
OPCODE_CALLN = $49
OPCODE_SETP16 = $61

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
file_params:
    .res 9
scan_ptr:
    .res 2
src_ptr:
    .res 2
save_params = file_params
const_ptr = svc_retptr
content_ptr = const_ptr
export_count = truncated_flag
export_index = export_index_zp
export_ptr = svc_retptr
body_ptr = src_ptr

.code

start:
    jsr init_module_name
    lda #$10
    sta $03FC
    jsr build_manifest_entry
    lda #$11
    sta $03FC
    jsr require_loaded_project
    lda #$12
    sta $03FC
    jsr require_manifest_entry_tracked
    lda #$13
    sta $03FC
    jsr build_object_target_path
    jsr load_object_or_fail
    jsr parse_exports_or_fail
    jsr parse_body_ops_or_fail
    jsr parse_external_symbols_or_fail
    jsr parse_strings_or_fail
    jsr parse_ints_or_fail
    jsr compute_code_bytes
    jsr build_live_set
    jsr build_avm_binary_content_or_fail
    lda #$41
    sta debug_phase_zp
    jsr build_binary_save_target_path
    jsr copy_target_path_to_binary_target_path
    lda #$C1
    sta binary_target_path+16
    lda #$42
    sta debug_phase_zp
    jsr save_source_buffer_to_target
    lda #$43
    sta debug_phase_zp
    bcc save_ok
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr

save_ok:
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
    adc #BODY_OPS_STRIDE
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

parse_body_ops_or_fail:
    lda #$00
    sta export_index
    jsr reset_scan_ptr_after_header
parse_body_ops_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    bne :+
    jmp parse_body_ops_done_check
:
    lda #<line_body
    sta const_ptr
    lda #>line_body
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcc :+
    jmp parse_body_ops_next_line
:
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
    cmp #'e'
    beq parse_body_ops_store
    cmp #'i'
    beq parse_body_ops_store
    cmp #'j'
    beq parse_body_ops_store
    cmp #'p'
    beq parse_body_ops_store
    cmp #'a'
    beq parse_body_ops_store
    cmp #'m'
    beq parse_body_ops_store
    cmp #'q'
    beq parse_body_ops_store
    cmp #'n'
    beq parse_body_ops_store
    cmp #'l'
    beq parse_body_ops_store
    cmp #'g'
    beq parse_body_ops_store
    cmp #'y'
    beq parse_body_ops_store
    cmp #'z'
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
    cpy #BODY_OPS_STRIDE
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
    stx entry_export_index
    lda #$01
    sta live_flags,x
build_live_set_scan_again:
    lda #$00
    sta compare_char
    ldx #$00
build_live_set_export_loop:
    cpx export_count
    bne :+
    jmp build_live_set_check
:
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
    cmp #'e'
    beq build_live_set_skip_pair
    cmp #'i'
    beq build_live_set_skip_pair
    cmp #'j'
    beq build_live_set_skip_pair
    cmp #'p'
    beq build_live_set_skip_pair
    cmp #'a'
    beq build_live_set_single
    cmp #'m'
    beq build_live_set_single
    cmp #'q'
    beq build_live_set_single
    cmp #'n'
    beq build_live_set_single
    cmp #'l'
    beq build_live_set_single
    cmp #'g'
    beq build_live_set_single
    cmp #'y'
    beq build_live_set_single
    cmp #'z'
    beq build_live_set_single
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
build_live_set_single:
    iny
    bne build_live_set_body_loop
build_live_set_ret:
    iny
    bne build_live_set_body_loop
build_live_set_next_export_restore:
    ldx current_bit_hi
build_live_set_next_export:
    inx
    beq :+
    jmp build_live_set_export_loop
:
build_live_set_check:
    lda compare_char
    beq :+
    jmp build_live_set_scan_again
:
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
    cpx #9
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

build_avm_binary_content_or_fail:
    jsr layout_payload_or_fail
    lda #$31
    sta debug_phase_zp
    jsr emit_payload_or_fail
    lda #$32
    sta debug_phase_zp
    jsr render_payload_as_binary_or_fail
    lda #$33
    sta debug_phase_zp
    rts

layout_payload_or_fail:
    lda #$00
    sta current_bit_lo
    sta current_bit_hi
    sta string_use_mask
    sta pending_count
    sta save_mode
    jsr layout_current_object_code_or_fail
    jsr copy_current_export_layout_to_root
    jsr save_current_string_state
    jsr queue_current_external_symbols_or_fail
layout_payload_pending_loop:
    ldx #$00
layout_payload_pending_next:
    cpx pending_count
    beq layout_payload_root_strings
    jsr layout_external_object_from_x_or_fail
    inx
    bne layout_payload_pending_next
layout_payload_root_strings:
    lda current_bit_lo
    sta code_limit_data
    jsr restore_saved_string_state
    lda #$00
    sta save_mode
    jsr layout_current_object_strings_or_fail
    ldx #$00
layout_payload_external_strings_next:
    cpx pending_count
    beq layout_payload_done
    jsr layout_external_object_strings_from_x_or_fail
    inx
    bne layout_payload_external_strings_next
layout_payload_done:
    rts

layout_external_object_from_x_or_fail:
    stx saved_pending_index
    jsr save_module_name
    ldx saved_pending_index
    jsr copy_pending_symbol_to_module_name_from_x
    lda current_bit_lo
    sta saved_state_lo
    lda current_bit_hi
    sta saved_state_hi
    jsr load_current_object_link_state_or_fail
    lda saved_state_hi
    sta current_bit_hi
    lda saved_state_lo
    sta current_bit_lo
    lda #$00
    sta string_use_mask
    lda #$01
    sta save_mode
    jsr layout_current_object_code_or_fail
    jsr find_export_index_from_module_name
    stx export_index
    ldx saved_pending_index
    ldy export_index
    lda current_export_offsets_lo,y
    sta pending_offsets_lo,x
    lda current_export_offsets_hi,y
    sta pending_offsets_hi,x
    jsr queue_current_external_symbols_or_fail
    lda string_use_mask
    sta pending_string_use_masks,x
    lda #$00
    sta save_mode
    ldx saved_pending_index
    jmp restore_module_name

layout_external_object_strings_from_x_or_fail:
    stx saved_pending_index
    jsr save_module_name
    ldx saved_pending_index
    lda current_bit_lo
    sta saved_state_lo
    lda current_bit_hi
    sta saved_state_hi
    jsr copy_pending_symbol_to_module_name_from_x
    jsr load_current_object_link_state_or_fail
    lda saved_state_hi
    sta current_bit_hi
    lda saved_state_lo
    sta current_bit_lo
    ldx saved_pending_index
    lda pending_string_use_masks,x
    sta string_use_mask
    lda current_bit_lo
    sta pending_string_bases_lo,x
    lda current_bit_hi
    sta pending_string_bases_hi,x
    lda #$01
    sta save_mode
    jsr layout_current_object_strings_or_fail
    ldx saved_pending_index
    jmp restore_module_name

layout_current_object_code_or_fail:
    lda #$00
    sta main_flags_hi
layout_current_object_code_loop:
    lda main_flags_hi
    cmp payload_bytes_data
    beq layout_current_object_code_done
    jsr find_live_export_at_current_offset
    bcs layout_current_object_code_gap
    stx export_index
    lda current_bit_lo
    sta current_export_offsets_lo,x
    lda current_bit_hi
    sta current_export_offsets_hi,x
    ldx export_index
    jsr note_strings_used_for_export_x_or_fail
    ldx export_index
    jsr add_proc_size_to_layout_from_x
    clc
    lda main_flags_hi
    adc proc_sizes,x
    sta main_flags_hi
    bcc layout_current_object_code_loop
    beq layout_current_object_code_done
    jmp layout_current_object_code_loop
layout_current_object_code_gap:
    inc main_flags_hi
    bne layout_current_object_code_loop
layout_current_object_code_done:
    rts

note_strings_used_for_export_x_or_fail:
    jsr set_body_ptr_from_x
    ldy #$00
note_strings_used_for_export_x_loop:
    lda (body_ptr),y
    beq note_strings_used_for_export_x_done
    cmp #'s'
    beq note_strings_used_for_export_x_string
    cmp #'e'
    beq note_strings_used_for_export_x_string
    iny
    bne note_strings_used_for_export_x_loop
note_strings_used_for_export_x_string:
    iny
    lda (body_ptr),y
    cmp #'0'
    bcc note_strings_used_for_export_x_bad
    cmp #'7'+1
    bcs note_strings_used_for_export_x_bad
    sec
    sbc #'0'
    tax
    lda bit_masks,x
    ora string_use_mask
    sta string_use_mask
    iny
    bne note_strings_used_for_export_x_loop
note_strings_used_for_export_x_bad:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
note_strings_used_for_export_x_done:
    rts

add_proc_size_to_layout_from_x:
    clc
    lda current_bit_lo
    adc proc_sizes,x
    sta current_bit_lo
    bcc :+
    inc current_bit_hi
:   lda save_mode
    bne add_proc_size_to_layout_from_x_done
    txa
    cmp entry_export_index
    bne add_proc_size_to_layout_from_x_done
    clc
    lda current_bit_lo
    adc #$02
    sta current_bit_lo
    bcc add_proc_size_to_layout_from_x_done
    inc current_bit_hi
add_proc_size_to_layout_from_x_done:
    rts

copy_current_export_layout_to_root:
    ldx #$00
copy_current_export_layout_to_root_loop:
    cpx #8
    beq copy_current_export_layout_to_root_done
    lda current_export_offsets_lo,x
    sta root_export_offsets_lo,x
    lda current_export_offsets_hi,x
    sta root_export_offsets_hi,x
    inx
    bne copy_current_export_layout_to_root_loop
copy_current_export_layout_to_root_done:
    rts

layout_current_object_strings_or_fail:
    ldx #$00
layout_current_object_strings_loop:
    cpx string_count
    beq layout_current_object_strings_done
    lda bit_masks,x
    and string_use_mask
    beq layout_current_object_strings_next
    lda save_mode
    bne layout_current_object_strings_store_done
    lda current_bit_lo
    sta root_string_offsets_lo,x
    lda current_bit_hi
    sta root_string_offsets_hi,x
layout_current_object_strings_store_done:
    txa
    pha
    jsr set_string_ptr_from_x
    jsr add_current_string_length_to_layout
    pla
    tax
layout_current_object_strings_next:
    inx
    bne layout_current_object_strings_loop
layout_current_object_strings_done:
    rts

add_current_string_length_to_layout:
    ldy #$00
add_current_string_length_to_layout_loop:
    lda (const_ptr),y
    beq add_current_string_length_to_layout_done
    iny
    bne add_current_string_length_to_layout_loop
add_current_string_length_to_layout_done:
    tya
    clc
    adc #$01
    clc
    adc current_bit_lo
    sta current_bit_lo
    bcc :+
    inc current_bit_hi
:   rts

emit_payload_or_fail:
    jsr load_current_object_link_state_or_fail
    lda #$34
    sta debug_phase
    lda #$00
    sta main_flags_lo
    sta main_flags_hi
    lda #$00
    sta string_use_mask
    sta save_mode
    jsr emit_current_object_code_or_fail
    lda #$35
    sta debug_phase
    jsr save_current_string_state
emit_payload_pending_loop:
    ldx #$00
emit_payload_pending_next:
    cpx pending_count
    beq emit_payload_root_strings
    jsr emit_external_object_code_from_x_or_fail
    inx
    bne emit_payload_pending_next
emit_payload_root_strings:
    lda #$36
    sta debug_phase
    jsr restore_saved_string_state
    jsr emit_current_object_strings_or_fail
    lda #$37
    sta debug_phase
    ldx #$00
emit_payload_external_strings_next:
    cpx pending_count
    beq emit_payload_done
    jsr emit_external_object_strings_from_x_or_fail
    inx
    bne emit_payload_external_strings_next
emit_payload_done:
    lda #$38
    sta debug_phase
    rts

emit_external_object_code_from_x_or_fail:
    lda #$51
    sta debug_phase_zp
    stx saved_pending_index
    jsr save_module_name
    ldx saved_pending_index
    jsr copy_pending_symbol_to_module_name_from_x
    lda main_flags_lo
    sta saved_state_lo
    lda main_flags_hi
    sta saved_state_hi
    jsr load_current_object_link_state_or_fail
    jsr snapshot_second_load_state
    lda #$52
    sta debug_phase_zp
    lda saved_state_hi
    sta main_flags_hi
    lda saved_state_lo
    sta main_flags_lo
    ldx saved_pending_index
    lda pending_offsets_lo,x
    sta current_bit_lo
    lda pending_offsets_hi,x
    sta current_bit_hi
    lda #$01
    sta save_mode
    stx pending_active_index
    lda pending_string_use_masks,x
    sta string_use_mask
    lda main_flags_hi
    sta saved_state_hi
    jsr layout_current_object_code_or_fail
    lda #$53
    sta debug_phase_zp
    lda saved_state_hi
    sta main_flags_hi
    jsr emit_current_object_code_or_fail
    lda #$54
    sta debug_phase_zp
    ldx saved_pending_index
    jmp restore_module_name

emit_external_object_strings_from_x_or_fail:
    lda #$61
    sta debug_phase_zp
    stx saved_pending_index
    jsr save_module_name
    ldx saved_pending_index
    jsr copy_pending_symbol_to_module_name_from_x
    lda main_flags_lo
    sta saved_state_lo
    lda main_flags_hi
    sta saved_state_hi
    jsr load_current_object_link_state_or_fail
    lda #$62
    sta debug_phase_zp
    lda saved_state_hi
    sta main_flags_hi
    lda saved_state_lo
    sta main_flags_lo
    ldx saved_pending_index
    lda pending_string_use_masks,x
    sta string_use_mask
    jsr emit_current_object_strings_or_fail
    lda #$63
    sta debug_phase_zp
    ldx saved_pending_index
    jmp restore_module_name

load_current_object_link_state_or_fail:
    lda #$70
    sta $03FC
    sta debug_phase_zp
    jsr build_object_target_path
    lda #$71
    sta $03FC
    sta debug_phase_zp
    jsr load_object_or_fail
    lda #$72
    sta $03FC
    sta debug_phase_zp
    lda file_params+6
    sta $03FD
    jsr require_loaded_source_not_truncated_or_fail
    lda #$73
    sta $03FC
    sta debug_phase_zp
    jsr require_avo1_header_or_fail
    lda #$74
    sta $03FC
    sta debug_phase_zp
    jsr parse_exports_or_fail
    lda #$75
    sta $03FC
    sta debug_phase_zp
    jsr parse_body_ops_or_fail
    lda #$76
    sta $03FC
    sta debug_phase_zp
    jsr parse_external_symbols_or_fail
    lda #$77
    sta $03FC
    sta debug_phase_zp
    jsr parse_strings_or_fail
    lda #$78
    sta $03FC
    sta debug_phase_zp
    jsr parse_ints_or_fail
    lda #$79
    sta $03FC
    sta debug_phase_zp
    jsr compute_code_bytes
    lda #$7A
    sta $03FC
    sta debug_phase_zp
    jsr build_live_set
    lda #$7B
    sta $03FC
    sta debug_phase_zp
    rts

emit_current_object_code_or_fail:
    lda #$00
    sta current_bit_hi
emit_current_object_code_loop:
    lda current_bit_hi
    cmp payload_bytes_data
    beq emit_current_object_code_done
    jsr find_live_export_at_emit_offset
    bcs emit_current_object_code_gap
    stx export_index
    ldx export_index
    jsr emit_live_bytes_for_export_x_or_fail
    ldx export_index
    clc
    lda current_bit_hi
    adc proc_sizes,x
    sta current_bit_hi
    bcc emit_current_object_code_loop
    beq emit_current_object_code_done
    jmp emit_current_object_code_loop
emit_current_object_code_gap:
    inc current_bit_hi
    bne emit_current_object_code_loop
emit_current_object_code_done:
    rts

find_live_export_at_emit_offset:
    ldx #$00
find_live_export_at_emit_offset_loop:
    cpx export_count
    beq find_live_export_at_emit_offset_fail
    lda live_flags,x
    beq find_live_export_at_emit_offset_next
    lda export_offsets,x
    cmp current_bit_hi
    beq find_live_export_at_emit_offset_done
find_live_export_at_emit_offset_next:
    inx
    bne find_live_export_at_emit_offset_loop
find_live_export_at_emit_offset_fail:
    sec
    rts
find_live_export_at_emit_offset_done:
    clc
    rts

emit_live_bytes_for_export_x_or_fail:
    txa
    pha
    stx export_index
    jsr set_body_ptr_from_x
    ldy #$00
emit_live_bytes_for_export_x_loop:
    lda (body_ptr),y
    bne :+
    jmp emit_live_bytes_for_export_x_done
:   cmp #'c'
    bne :+
    jmp emit_live_bytes_for_export_x_call
:   cmp #'u'
    bne :+
    jmp emit_live_bytes_for_export_x_external
:   cmp #'s'
    bne :+
    jmp emit_live_bytes_for_export_x_print
:   cmp #'e'
    bne :+
    jmp emit_live_bytes_for_export_x_printe
:   cmp #'i'
    bne :+
    jmp emit_live_bytes_for_export_x_printie
:   cmp #'j'
    bne :+
    jmp emit_live_bytes_for_export_x_printi
:   cmp #'p'
    bne :+
    jmp emit_live_bytes_for_export_x_push
:   cmp #'a'
    bne :+
    jmp emit_live_bytes_for_export_x_add
:   cmp #'m'
    bne :+
    jmp emit_live_bytes_for_export_x_sub
:   cmp #'q'
    bne :+
    jmp emit_live_bytes_for_export_x_eq
:   cmp #'n'
    bne :+
    jmp emit_live_bytes_for_export_x_ne
:   cmp #'l'
    bne :+
    jmp emit_live_bytes_for_export_x_lt
:   cmp #'g'
    bne :+
    jmp emit_live_bytes_for_export_x_gt
:   cmp #'y'
    bne :+
    jmp emit_live_bytes_for_export_x_printi_top
:   cmp #'z'
    bne :+
    jmp emit_live_bytes_for_export_x_printie_top
:   cmp #'r'
    bne :+
    jmp emit_live_bytes_for_export_x_ret
:
    jmp emit_live_bytes_for_export_x_bad
emit_live_bytes_for_export_x_call:
    iny
    jsr load_body_digit_index_to_x_or_fail
    jsr load_export_target_offset_from_x_or_fail
    jsr append_current_target_call_bytes
    iny
    jmp emit_live_bytes_for_export_x_loop
emit_live_bytes_for_export_x_external:
    iny
    jsr load_body_digit_index_to_x_or_fail
    tya
    pha
    jsr load_pending_offset_for_external_x_or_fail
    pla
    tay
    jsr append_current_target_call_bytes
    iny
    jmp emit_live_bytes_for_export_x_loop
emit_live_bytes_for_export_x_print:
    lda #$00
    pha
    jmp emit_live_bytes_for_export_x_print_common
emit_live_bytes_for_export_x_printe:
    lda #$10
    pha
emit_live_bytes_for_export_x_print_common:
    iny
    jsr load_body_digit_index_to_x_or_fail
    lda bit_masks,x
    ora string_use_mask
    sta string_use_mask
    jsr load_string_target_offset_from_x_or_fail
    lda #OPCODE_SETP16
    jsr append_payload_byte
    lda current_bit_lo
    jsr append_payload_byte
    lda current_bit_hi
    jsr append_payload_byte
    lda #OPCODE_CALLN
    jsr append_payload_byte
    pla
    jsr append_payload_byte
    lda #$FF
    jsr append_payload_byte
    iny
    jmp emit_live_bytes_for_export_x_loop
emit_live_bytes_for_export_x_printi:
    lda #$30
    pha
    jmp emit_live_bytes_for_export_x_printi_common
emit_live_bytes_for_export_x_printie:
    lda #$31
    pha
emit_live_bytes_for_export_x_printi_common:
    iny
    jsr load_body_digit_index_to_x_or_fail
    txa
    pha
    lda int_values_hi,x
    pha
    lda int_values_lo,x
    pha
    lda #OPCODE_PUSH16
    jsr append_payload_byte
    pla
    jsr append_payload_byte
    pla
    jsr append_payload_byte
    pla
    tax
    lda #OPCODE_CALLN
    jsr append_payload_byte
    pla
    jsr append_payload_byte
    lda #$FF
    jsr append_payload_byte
    iny
    jmp emit_live_bytes_for_export_x_loop
emit_live_bytes_for_export_x_push:
    iny
    jsr load_body_digit_index_to_x_or_fail
    txa
    pha
    lda int_values_hi,x
    pha
    lda int_values_lo,x
    pha
    lda #OPCODE_PUSH16
    jsr append_payload_byte
    pla
    jsr append_payload_byte
    pla
    jsr append_payload_byte
    pla
    tax
    iny
    jmp emit_live_bytes_for_export_x_loop
emit_live_bytes_for_export_x_add:
    lda #OPCODE_ADD
    jsr append_payload_byte
    iny
    jmp emit_live_bytes_for_export_x_loop
emit_live_bytes_for_export_x_sub:
    lda #OPCODE_SUB
    jsr append_payload_byte
    iny
    jmp emit_live_bytes_for_export_x_loop
emit_live_bytes_for_export_x_eq:
    lda #OPCODE_EQ
    jsr append_payload_byte
    iny
    jmp emit_live_bytes_for_export_x_loop
emit_live_bytes_for_export_x_ne:
    lda #OPCODE_NE
    jsr append_payload_byte
    iny
    jmp emit_live_bytes_for_export_x_loop
emit_live_bytes_for_export_x_lt:
    lda #OPCODE_LT
    jsr append_payload_byte
    iny
    jmp emit_live_bytes_for_export_x_loop
emit_live_bytes_for_export_x_gt:
    lda #OPCODE_GT
    jsr append_payload_byte
    iny
    jmp emit_live_bytes_for_export_x_loop
emit_live_bytes_for_export_x_printi_top:
    lda #$30
    pha
    jmp emit_live_bytes_for_export_x_print_top_common
emit_live_bytes_for_export_x_printie_top:
    lda #$31
    pha
emit_live_bytes_for_export_x_print_top_common:
    lda #OPCODE_CALLN
    jsr append_payload_byte
    pla
    jsr append_payload_byte
    lda #$FF
    jsr append_payload_byte
    iny
    jmp emit_live_bytes_for_export_x_loop
emit_live_bytes_for_export_x_ret:
    lda save_mode
    bne emit_live_bytes_for_export_x_ret_normal
    lda export_index
    cmp entry_export_index
    bne emit_live_bytes_for_export_x_ret_normal
    lda #OPCODE_CALLN
    jsr append_payload_byte
    lda #$20
    jsr append_payload_byte
    lda #$FF
    jsr append_payload_byte
    iny
    jmp emit_live_bytes_for_export_x_loop
emit_live_bytes_for_export_x_ret_normal:
    lda #OPCODE_RET
    jsr append_payload_byte
    iny
    jmp emit_live_bytes_for_export_x_loop
emit_live_bytes_for_export_x_bad:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
emit_live_bytes_for_export_x_done:
    pla
    tax
    rts

load_body_digit_index_to_x_or_fail:
    lda (body_ptr),y
    cmp #'0'
    bcs :+
    jmp emit_live_bytes_for_export_x_bad
:   cmp #'7'+1
    bcc :+
    jmp emit_live_bytes_for_export_x_bad
:   sec
    sbc #'0'
    tax
    rts

append_current_target_call_bytes:
    lda #OPCODE_CALL
    jsr append_payload_byte
    lda current_bit_lo
    jsr append_payload_byte
    lda current_bit_hi
    jmp append_payload_byte

load_export_target_offset_from_x_or_fail:
    lda save_mode
    beq :+
    lda current_export_offsets_lo,x
    sta current_bit_lo
    lda current_export_offsets_hi,x
    sta current_bit_hi
    rts
:   lda root_export_offsets_lo,x
    sta current_bit_lo
    lda root_export_offsets_hi,x
    sta current_bit_hi
    rts

load_string_target_offset_from_x_or_fail:
    tya
    pha
    lda save_mode
    beq :+
    stx compare_char
    ldy pending_active_index
    lda pending_string_bases_lo,y
    sta current_bit_lo
    lda pending_string_bases_hi,y
    sta current_bit_hi
    ldx #$00
load_string_target_offset_pending_loop:
    cpx compare_char
    beq load_string_target_offset_pending_done
    lda bit_masks,x
    and string_use_mask
    beq load_string_target_offset_pending_next
    txa
    pha
    jsr set_string_ptr_from_x
    jsr add_current_string_length_to_layout
    pla
    tax
load_string_target_offset_pending_next:
    inx
    bne load_string_target_offset_pending_loop
load_string_target_offset_pending_done:
    ldx compare_char
    pla
    tay
    rts
:   lda root_string_offsets_lo,x
    sta current_bit_lo
    lda root_string_offsets_hi,x
    sta current_bit_hi
    pla
    tay
    rts

load_pending_offset_for_external_x_or_fail:
    txa
    pha
    jsr set_external_ptr_from_x
    jsr copy_export_ptr_to_symbol_buffer
    jsr find_pending_index_from_symbol_buffer_or_fail
    lda pending_offsets_lo,x
    sta current_bit_lo
    lda pending_offsets_hi,x
    sta current_bit_hi
    pla
    tax
    rts

find_pending_index_from_symbol_buffer_or_fail:
    ldx #$00
find_pending_index_from_symbol_buffer_loop:
    cpx pending_count
    beq find_pending_index_from_symbol_buffer_bad
    stx compare_char
    jsr set_pending_ptr_from_x
    lda export_ptr
    sta const_ptr
    lda export_ptr+1
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcc find_pending_index_from_symbol_buffer_done
    ldx compare_char
    inx
    bne find_pending_index_from_symbol_buffer_loop
find_pending_index_from_symbol_buffer_bad:
    lda #<msg_bad_avo
    ldy #>msg_bad_avo
    jmp fail_with_ptr
find_pending_index_from_symbol_buffer_done:
    ldx compare_char
    rts

emit_current_object_strings_or_fail:
    ldx #$00
emit_current_object_strings_loop:
    cpx string_count
    beq emit_current_object_strings_done
    lda bit_masks,x
    and string_use_mask
    beq emit_current_object_strings_next
    txa
    pha
    jsr set_string_ptr_from_x
    ldy #$00
emit_current_object_strings_value_loop:
    lda (const_ptr),y
    beq emit_current_object_strings_value_done
    jsr append_payload_byte
    iny
    bne emit_current_object_strings_value_loop
emit_current_object_strings_value_done:
    lda #$00
    jsr append_payload_byte
    pla
    tax
emit_current_object_strings_next:
    inx
    bne emit_current_object_strings_loop
emit_current_object_strings_done:
    rts

append_payload_byte:
    tax
    tya
    pha
    lda main_flags_hi
    bne append_payload_byte_fail
    ldy main_flags_lo
    txa
    sta content_buffer,y
    pla
    tay
    inc main_flags_lo
    bne :+
    inc main_flags_hi
:   rts
append_payload_byte_fail:
    pla
    tay
    lda #<msg_too_large
    ldy #>msg_too_large
    jmp fail_with_ptr

render_payload_as_binary_or_fail:
    lda main_flags_hi
    beq :+
    lda #<msg_too_large
    ldy #>msg_too_large
    jmp fail_with_ptr
:   lda main_flags_lo
    cmp #245
    bcc :+
    lda #<msg_too_large
    ldy #>msg_too_large
    jmp fail_with_ptr
:   ldx main_flags_lo
    beq render_payload_as_binary_header
    dex
render_payload_as_binary_shift_loop:
    lda content_buffer,x
    sta content_buffer+AVM_HEADER_SIZE,x
    dex
    cpx #$FF
    bne render_payload_as_binary_shift_loop
render_payload_as_binary_header:
    lda #'A'
    sta content_buffer+0
    lda #'V'
    sta content_buffer+1
    lda #'M'
    sta content_buffer+2
    lda #'1'
    sta content_buffer+3
    lda #AVM_VERSION
    sta content_buffer+4
    lda main_flags_lo
    sta content_buffer+5
    lda #$00
    sta content_buffer+6
    ldx entry_export_index
    lda root_export_offsets_lo,x
    sta content_buffer+7
    lda root_export_offsets_hi,x
    sta content_buffer+8
    lda #AVM_FLAG_ACHERON
    sta content_buffer+9
    lda code_limit_data
    sta content_buffer+10
    lda #$00
    sta content_buffer+11
render_payload_as_binary_done:
    rts

save_current_string_state:
    lda string_count
    sta saved_string_count
    lda string_use_mask
    sta saved_string_use_mask
    ldx #$00
save_current_string_state_loop:
    lda string_literals,x
    sta saved_string_literals,x
    inx
    cpx #192
    bcc save_current_string_state_loop
    rts

restore_saved_string_state:
    lda saved_string_count
    sta string_count
    lda saved_string_use_mask
    sta string_use_mask
    ldx #$00
restore_saved_string_state_loop:
    lda saved_string_literals,x
    sta string_literals,x
    inx
    cpx #192
    bcc restore_saved_string_state_loop
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
    ldy main_flags_lo
    txa
    sta content_buffer,y
    pla
    tay
    inc main_flags_lo
    bne :+
    inc main_flags_hi
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

build_binary_save_target_path:
    lda #'B'
    sta target_path+0
    lda #'I'
    sta target_path+1
    lda #'N'
    sta target_path+2
    lda #'/'
    sta target_path+3
    ldy #$00
build_binary_save_target_path_loop:
    lda module_name,y
    beq build_binary_save_target_path_suffix
    sta target_path+4,y
    iny
    bne build_binary_save_target_path_loop
build_binary_save_target_path_suffix:
    lda #'.'
    sta target_path+4,y
    iny
    lda #'A'
    sta target_path+4,y
    iny
    lda #'V'
    sta target_path+4,y
    iny
    lda #'M'
    sta target_path+4,y
    iny
    lda #$00
    sta target_path+4,y
    rts

copy_target_path_to_binary_target_path:
    ldx #$00
copy_target_path_to_binary_target_path_loop:
    lda target_path,x
    sta binary_target_path,x
    beq copy_target_path_to_binary_target_path_done
    inx
    cpx #40
    bcc copy_target_path_to_binary_target_path_loop
copy_target_path_to_binary_target_path_done:
    rts

save_source_buffer_to_target:
    lda #$C2
    sta binary_target_path+16
    lda #<target_path
    sta save_params+0
    lda #>target_path
    sta save_params+1
    lda #<content_buffer
    sta save_params+2
    lda #>content_buffer
    sta save_params+3
    clc
    lda main_flags_lo
    adc #AVM_HEADER_SIZE
    sta save_params+4
    lda #$00
    adc main_flags_hi
    sta save_params+5
    lda #tool_file_status_fail
    sta save_params+6
    lda save_params+0
    sta $03E8
    lda save_params+1
    sta $03E9
    lda save_params+2
    sta $03EA
    lda save_params+3
    sta $03EB
    lda save_params+4
    sta $03EC
    lda save_params+5
    sta $03ED
    lda save_params+6
    sta $03EE
    tsx
    stx compare_char
    stx $03EF
    lda #$C3
    sta binary_target_path+16
    ldx #$00
save_source_buffer_to_target_snapshot_loop:
    lda save_params,x
    sta binary_target_path+17,x
    inx
    cpx #7
    bcc save_source_buffer_to_target_snapshot_loop
    lda $9580
    sta binary_target_path+24
    lda $9614
    sta binary_target_path+25
    lda $9615
    sta binary_target_path+26
    lda $9616
    sta binary_target_path+27
    lda $9617
    sta binary_target_path+28
    lda $CFF8
    sta binary_target_path+29
    lda $CFF9
    sta binary_target_path+30
    tsx
    stx save_params+8
    lda #$00
    ldx #$00
save_source_buffer_to_target_scrub_stack_loop:
    cpx save_params+8
    bcs save_source_buffer_to_target_scrub_stack_done
    sta $0100,x
    inx
    bne save_source_buffer_to_target_scrub_stack_loop
save_source_buffer_to_target_scrub_stack_done:
    ldx #save_params
    jsr svc_file_save_sc0
    lda #$C4
    sta binary_target_path+16
    lda save_params+6
    sta $03FD
    tsx
    stx $03FE
    lda #$A2
    sta $03FF
    lda save_params+6
    cmp #tool_file_status_ok
    beq save_source_buffer_to_target_ok
    sec
    rts
save_source_buffer_to_target_ok:
    clc
    rts

snapshot_second_load_state:
    lda #$A2
    sta $03D0
    ldx #$00
snapshot_second_load_target_loop:
    lda target_path,x
    sta $03D1,x
    inx
    cpx #10
    bcc snapshot_second_load_target_loop
    ldx #$00
snapshot_second_load_module_loop:
    lda module_name,x
    sta $03DB,x
    inx
    cpx #6
    bcc snapshot_second_load_module_loop
    ldx #$00
snapshot_second_load_file_loop:
    lda file_params,x
    sta $03E1,x
    inx
    cpx #7
    bcc snapshot_second_load_file_loop
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
    lda debug_phase_zp
    sta $03FD
    lda debug_phase
    sta $03FE
    tsx
    stx $03FF
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

bit_masks:
    .byte $01,$02,$04,$08,$10,$20,$40,$80

module_name:
    .res 25
target_path_pad:
    .res $0069
target_path:
    .res 40
binary_target_path:
    .res 40
saved_module_name:
    .res 25

.segment "BSS"

source_buffer_pad:
    .res $0026
source_buffer:
    .res SOURCE_LIMIT+1
content_buffer_pad:
    .res $00F7
content_buffer:
    .res 256
export_names:
    .res 200
export_offsets:
    .res 8
proc_sizes:
    .res 8
root_export_offsets_lo:
    .res 8
root_export_offsets_hi:
    .res 8
current_export_offsets_lo:
    .res 8
current_export_offsets_hi:
    .res 8
string_literals:
    .res 192
string_count:
    .res 1
saved_string_literals:
    .res 192
saved_string_count:
    .res 1
save_mode:
    .res 1
export_index_zp:
    .res 1
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
pending_active_index:
    .res 1
debug_phase:
    .res 1
saved_pending_index:
    .res 1
saved_state_lo:
    .res 1
saved_state_hi:
    .res 1
truncated_flag:
    .res 1
debug_phase_zp:
    .res 1
payload_bytes_data:
    .res 1
code_limit_data:
    .res 1
entry_export_index:
    .res 1
root_string_offsets_lo:
    .res 8
root_string_offsets_hi:
    .res 8
live_flags:
    .res 8
string_use_mask:
    .res 1
saved_string_use_mask:
    .res 1
body_ops_data:
    .res BODY_OPS_STRIDE * 8
manifest_entry:
    .res 32
external_names:
    .res 200
external_count:
    .res 1
pending_count:
    .res 1
pending_offsets_lo:
    .res PENDING_SYMBOL_MAX
pending_offsets_hi:
    .res PENDING_SYMBOL_MAX
pending_string_use_masks:
    .res PENDING_SYMBOL_MAX
pending_string_bases_lo:
    .res PENDING_SYMBOL_MAX
pending_string_bases_hi:
    .res PENDING_SYMBOL_MAX
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
