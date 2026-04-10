.include "udos_services.inc"

.export start

MANIFEST_LIMIT = 191
.ifndef SOURCE_LIMIT
SOURCE_LIMIT = 255
.endif
.ifndef BODY_OPS_STRIDE
BODY_OPS_STRIDE = 48
.endif
.ifndef INT_LITERAL_MAX
INT_LITERAL_MAX = 10
.endif
.ifndef STRING_LITERAL_MAX
STRING_LITERAL_MAX = 8
.endif
.ifndef VAR_MAX
VAR_MAX = 16
.endif
.ifndef EXPORT_MAX
EXPORT_MAX = 8
.endif
.ifndef EXTERNAL_MAX
EXTERNAL_MAX = 8
.endif
.ifndef LOOP_MAX
LOOP_MAX = 8
.endif

IMPORT_PRINT_STR  = $01
IMPORT_PRINT_LINE = $02
IMPORT_FORMAT_INT = $04

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
file_params:
    .res 9
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
save_mode:
    .res 1
list_started:
    .res 1
payload_offset:
    .res 1
proc_index:
    .res 1

save_params = file_params

export_index = list_started
export_ptr = src_ptr
body_ptr = src_ptr

.code

start:
    lda #$10
    sta actc_trace_byte
    jsr init_module_name
    jsr build_manifest_entry
    jsr require_loaded_project
    jsr require_manifest_entry_tracked
    jsr build_target_path
    jsr load_source_file
    bcc source_loaded
    lda file_params+6
    cmp #tool_file_status_nofile
    beq source_missing
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
source_missing:
    lda #<msg_no_file
    ldy #>msg_no_file
    jmp fail_with_ptr
source_loaded:
    jsr parse_module_header_or_fail
    jsr collect_module_vars_or_fail
    jsr collect_proc_exports_or_fail
    jsr collect_proc_locals_or_fail
    jsr collect_proc_body_ops
    lda body_ops_data+0
    sta $03E8
    lda body_ops_data+1
    sta $03E9
    lda body_ops_data+2
    sta $03EA
    lda body_ops_data+3
    sta $03EB
    jsr detect_runtime_imports
    jsr compute_payload_layout
    jsr build_avo_content
    jsr build_object_target_path
    lda #$01
    sta save_mode
    lda #$1F
    sta actc_trace_byte
    jmp save_and_exit_clean_stack

save_ok:
    lda #$21
    sta actc_trace_byte
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

scrub_unused_stack_before_save:
    tsx
    stx save_stack_top
    lda #$00
    ldx #$00
scrub_unused_stack_before_save_loop:
    cpx save_stack_top
    bcs scrub_unused_stack_before_save_done
    sta $0100,x
    inx
    bne scrub_unused_stack_before_save_loop
scrub_unused_stack_before_save_done:
    rts

clear_post_build_state:
    lda #$00
    sta src_ptr
    sta src_ptr+1
    sta scan_ptr
    sta scan_ptr+1
    sta content_ptr
    sta content_ptr+1
    sta const_ptr
    sta const_ptr+1
    sta import_flags_lo
    sta truncated_flag
    sta save_mode
    sta list_started
    sta payload_offset
    sta proc_index
    sta current_proc_index_data
    rts

save_and_exit_clean_stack:
    ldx #$FF
    txs
    jsr save_content_buffer_to_target
    lda #$20
    sta actc_trace_byte
    bcc save_ok
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr

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
    cpy #$00
    bne copy_declared_module_or_fail_body
    jsr uppercase_symbol_start_valid
    bcc copy_declared_module_or_fail_store
    jmp copy_declared_module_or_fail_done
copy_declared_module_or_fail_body:
    jsr uppercase_symbol_body_valid
    bcc copy_declared_module_or_fail_store
    jmp copy_declared_module_or_fail_done
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

collect_module_vars_or_fail:
    lda #$00
    sta var_count_data
    sta module_var_count_data
    lda #<source_buffer
    sta scan_ptr
    lda #>source_buffer
    sta scan_ptr+1
    jsr skip_source_line
collect_module_vars_or_fail_loop:
    ldy #$00
    lda (scan_ptr),y
    beq collect_module_vars_or_fail_done
    cmp #10
    beq collect_module_vars_or_fail_advance_blank
    cmp #13
    beq collect_module_vars_or_fail_advance_blank
    jsr skip_source_spaces
    ldy #$00
    lda (scan_ptr),y
    beq collect_module_vars_or_fail_done
    lda #<pattern_proc
    sta const_ptr
    lda #>pattern_proc
    sta const_ptr+1
    jsr pattern_matches_scan_ptr_keyword
    bcc collect_module_vars_or_fail_done
    lda #<pattern_int_decl
    sta const_ptr
    lda #>pattern_int_decl
    sta const_ptr+1
    jsr pattern_matches_scan_ptr_keyword
    bcs collect_module_vars_or_fail_bad
    jsr store_module_var_from_scan_ptr_or_fail
    jsr skip_source_line
    jmp collect_module_vars_or_fail_loop
collect_module_vars_or_fail_advance_blank:
    jsr advance_scan_ptr
    jmp collect_module_vars_or_fail_loop
collect_module_vars_or_fail_bad:
    lda #<msg_bad_var
    ldy #>msg_bad_var
    jmp fail_with_ptr
collect_module_vars_or_fail_done:
    lda var_count_data
    sta module_var_count_data
    rts

store_module_var_from_scan_ptr_or_fail:
    lda #<pattern_int_decl
    sta const_ptr
    lda #>pattern_int_decl
    sta const_ptr+1
    jsr advance_scan_ptr_by_const_ptr
    jsr skip_source_spaces
    jsr copy_symbol_from_scan_ptr
    bcc :+
    lda #<msg_bad_var
    ldy #>msg_bad_var
    jmp fail_with_ptr
:   sty compare_char
    jsr find_module_var_index_from_declared
    bcc store_module_var_from_scan_ptr_or_fail_bad
    ldy #$00
store_module_var_from_scan_ptr_or_fail_save_name_loop:
    lda declared_module_name,y
    sta saved_var_name_data,y
    beq store_module_var_from_scan_ptr_or_fail_save_name_done
    iny
    cpy #25
    bcc store_module_var_from_scan_ptr_or_fail_save_name_loop
    jmp store_module_var_from_scan_ptr_or_fail_bad
store_module_var_from_scan_ptr_or_fail_save_name_done:
    lda #$00
    sta expr_value_lo
    sta expr_term_lo
    ldy compare_char
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    beq store_module_var_from_scan_ptr_or_fail_store
    cmp #10
    beq store_module_var_from_scan_ptr_or_fail_store
    cmp #13
    beq store_module_var_from_scan_ptr_or_fail_store
    cmp #'='
    bne store_module_var_from_scan_ptr_or_fail_bad
    iny
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'['
    bne store_module_var_from_scan_ptr_or_fail_parse_value
    iny
    jsr parse_small_value_expr_at_scan_y
    bcs store_module_var_from_scan_ptr_or_fail_bad
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #']'
    bne store_module_var_from_scan_ptr_or_fail_bad
    iny
    jmp store_module_var_from_scan_ptr_or_fail_after_value
store_module_var_from_scan_ptr_or_fail_parse_value:
    jsr parse_small_value_expr_at_scan_y
    bcs store_module_var_from_scan_ptr_or_fail_bad
store_module_var_from_scan_ptr_or_fail_after_value:
    jsr require_line_end_at_scan_y
    bcs store_module_var_from_scan_ptr_or_fail_bad
store_module_var_from_scan_ptr_or_fail_store:
    ldx var_count_data
    cpx #VAR_MAX
    bcc :+
    lda #<msg_bad_var
    ldy #>msg_bad_var
    jmp fail_with_ptr
:   txa
    pha
    jsr set_var_ptr_from_x
    ldy #$00
store_module_var_from_scan_ptr_or_fail_copy_loop:
    lda saved_var_name_data,y
    sta (export_ptr),y
    beq store_module_var_from_scan_ptr_or_fail_copy_done
    iny
    cpy #25
    bcc store_module_var_from_scan_ptr_or_fail_copy_loop
store_module_var_from_scan_ptr_or_fail_bad:
    lda #<msg_bad_var
    ldy #>msg_bad_var
    jmp fail_with_ptr
store_module_var_from_scan_ptr_or_fail_copy_done:
    pla
    tax
    lda expr_value_lo
    sta var_init_lo,x
    lda #$00
    sta var_init_hi,x
    inc var_count_data
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

collect_proc_locals_or_fail:
    lda #$00
    ldx #$00
collect_proc_locals_or_fail_clear_loop:
    sta proc_local_count_data,x
    sta proc_local_var_base_data,x
    inx
    cpx #EXPORT_MAX
    bcc collect_proc_locals_or_fail_clear_loop
    lda #$FF
    sta current_proc_index_data
    lda #<source_buffer
    sta scan_ptr
    lda #>source_buffer
    sta scan_ptr+1
collect_proc_locals_or_fail_loop:
    ldy #$00
    lda (scan_ptr),y
    beq collect_proc_locals_or_fail_done
    cmp #10
    beq collect_proc_locals_or_fail_advance_blank
    cmp #13
    beq collect_proc_locals_or_fail_advance_blank
    jsr skip_source_spaces
    ldy #$00
    lda (scan_ptr),y
    beq collect_proc_locals_or_fail_done
    lda #<pattern_proc
    sta const_ptr
    lda #>pattern_proc
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs collect_proc_locals_or_fail_try_int_decl
    jsr advance_scan_ptr_by_const_ptr
    jsr skip_source_spaces
    jsr copy_symbol_from_scan_ptr
    bcs collect_proc_locals_or_fail_bad_proc
    jsr find_export_index_from_declared
    bcs collect_proc_locals_or_fail_bad_proc
    stx current_proc_index_data
    lda var_count_data
    sta proc_local_var_base_data,x
    lda #$00
    sta proc_local_count_data,x
    jsr skip_source_line
    jmp collect_proc_locals_or_fail_loop
collect_proc_locals_or_fail_try_int_decl:
    lda current_proc_index_data
    cmp #$FF
    beq collect_proc_locals_or_fail_skip_line
    lda #<pattern_int_decl
    sta const_ptr
    lda #>pattern_int_decl
    sta const_ptr+1
    jsr pattern_matches_scan_ptr_keyword
    bcs collect_proc_locals_or_fail_skip_line
    jsr store_proc_local_var_from_scan_ptr_or_fail
collect_proc_locals_or_fail_skip_line:
    jsr skip_source_line
    jmp collect_proc_locals_or_fail_loop
collect_proc_locals_or_fail_advance_blank:
    jsr advance_scan_ptr
    jmp collect_proc_locals_or_fail_loop
collect_proc_locals_or_fail_bad_proc:
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_ptr
collect_proc_locals_or_fail_done:
    lda #$FF
    sta current_proc_index_data
    rts

store_proc_local_var_from_scan_ptr_or_fail:
    lda #<pattern_int_decl
    sta const_ptr
    lda #>pattern_int_decl
    sta const_ptr+1
    jsr advance_scan_ptr_by_const_ptr
    jsr skip_source_spaces
    jsr copy_symbol_from_scan_ptr
    bcc :+
    jmp store_proc_local_var_from_scan_ptr_or_fail_bad
:   ldx current_proc_index_data
    jsr find_current_proc_param_index_from_declared_for_proc_x
    bcs :+
    jmp store_proc_local_var_from_scan_ptr_or_fail_bad
:   ldx current_proc_index_data
    jsr find_current_proc_local_index_from_declared_for_proc_x
    bcs :+
    jmp store_proc_local_var_from_scan_ptr_or_fail_bad
:   ldx var_count_data
    cpx #VAR_MAX
    bcc :+
    jmp store_proc_local_var_from_scan_ptr_or_fail_bad
:   txa
    pha
    jsr set_var_ptr_from_x
    pla
    tax
    ldy #$00
store_proc_local_var_from_scan_ptr_or_fail_copy_loop:
    lda declared_module_name,y
    sta (export_ptr),y
    beq store_proc_local_var_from_scan_ptr_or_fail_copy_done
    iny
    cpy #25
    bcc store_proc_local_var_from_scan_ptr_or_fail_copy_loop
store_proc_local_var_from_scan_ptr_or_fail_bad:
    lda #<msg_bad_var
    ldy #>msg_bad_var
    jmp fail_with_ptr
store_proc_local_var_from_scan_ptr_or_fail_copy_done:
    lda #$00
    sta var_init_lo,x
    sta var_init_hi,x
    inc var_count_data
    ldx current_proc_index_data
    inc proc_local_count_data,x
    rts

collect_proc_body_ops:
    lda #$00
    sta string_count_data
    sta int_count_data
    sta extern_count_data
    sta loop_depth_data
    lda #$FF
    sta current_proc_index_data
    lda #<body_ops_data
    sta body_ptr
    lda #>body_ops_data
    sta body_ptr+1
    ldy #$00
collect_proc_body_ops_clear_loop:
    lda #$00
    sta (body_ptr),y
    iny
    bne collect_proc_body_ops_clear_loop
    lda #<source_buffer
    sta scan_ptr
    lda #>source_buffer
    sta scan_ptr+1
collect_proc_body_ops_loop:
    ldy #$00
    lda (scan_ptr),y
    bne collect_proc_body_ops_have_char
    jmp collect_proc_body_ops_done
collect_proc_body_ops_have_char:
    cmp #10
    bne :+
    jmp collect_proc_body_ops_advance_blank
:   cmp #13
    bne :+
    jmp collect_proc_body_ops_advance_blank
:
    jsr skip_source_spaces
    ldy #$00
    lda (scan_ptr),y
    bne collect_proc_body_ops_after_space_check
    jmp collect_proc_body_ops_done
collect_proc_body_ops_after_space_check:
    lda #<pattern_proc
    sta const_ptr
    lda #>pattern_proc
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs :+
    jmp collect_proc_body_ops_proc_decl
	:
	    lda current_proc_index_data
	    cmp #$FF
	    bne :+
	    jmp collect_proc_body_ops_skip_line
	:
        lda #<pattern_int_decl
        sta const_ptr
        lda #>pattern_int_decl
        sta const_ptr+1
        jsr pattern_matches_scan_ptr_keyword
        bcc :+
        jmp collect_proc_body_ops_try_od
: 
        jsr advance_scan_ptr_by_const_ptr
        jsr skip_source_spaces
        jsr copy_symbol_from_scan_ptr
        bcc :+
        jmp collect_proc_body_ops_bad_var
: 
        sty symbol_end_y_data
        ldx current_proc_index_data
        jsr find_current_proc_local_index_from_declared_for_proc_x
        bcc :+
        jmp collect_proc_body_ops_bad_var
: 
        stx assignment_target_index_data
        ldy symbol_end_y_data
        jsr skip_inline_spaces_at_scan_y
        lda (scan_ptr),y
        bne :+
        jmp collect_proc_body_ops_skip_line
: 
        cmp #10
        bne :+
        jmp collect_proc_body_ops_skip_line
: 
        cmp #13
        bne :+
        jmp collect_proc_body_ops_skip_line
: 
        cmp #'='
        beq :+
        jmp collect_proc_body_ops_bad_var
: 
        iny
        jsr skip_inline_spaces_at_scan_y
        lda (scan_ptr),y
        cmp #'['
        beq :+
        jmp collect_proc_body_ops_try_local_int_parse_value
: 
        iny
        jsr emit_runtime_value_from_scan_y_or_fail
        bcc :+
        jmp collect_proc_body_ops_bad_literal
: 
        jsr skip_inline_spaces_at_scan_y
        lda (scan_ptr),y
        cmp #']'
        beq :+
        jmp collect_proc_body_ops_bad_literal
: 
        iny
        jmp collect_proc_body_ops_try_local_int_after_value
collect_proc_body_ops_try_local_int_parse_value:
        jsr emit_runtime_value_from_scan_y_or_fail
        bcc :+
        jmp collect_proc_body_ops_bad_literal
: 
collect_proc_body_ops_try_local_int_after_value:
        jsr require_line_end_at_scan_y
        bcc :+
        jmp collect_proc_body_ops_bad_literal
: 
        ldx assignment_target_index_data
        lda #'S'
        jsr append_body_op_for_current_proc
        jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_od:
	    lda #<pattern_od
	    sta const_ptr
	    lda #>pattern_od
	    sta const_ptr+1
	    jsr pattern_matches_scan_ptr_keyword
	    bcs collect_proc_body_ops_try_until
	    jsr pop_loop_kind_to_compare_char_or_fail
	    lda compare_char
	    beq :+
	    lda #'x'
	    jsr append_body_op_no_arg_for_current_proc
	    jmp collect_proc_body_ops_skip_line
:
	    lda #'o'
	    jsr append_body_op_no_arg_for_current_proc
	    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_until:
	    lda #<pattern_until
	    sta const_ptr
	    lda #>pattern_until
	    sta const_ptr+1
	    jsr pattern_matches_scan_ptr_keyword
	    bcs collect_proc_body_ops_try_do
	    jsr advance_scan_ptr_by_const_ptr
	    jsr store_small_runtime_until_from_scan_ptr
	    bcc :+
	    jmp collect_proc_body_ops_if_bad_literal
: 
	    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_do:
	    lda #<pattern_while
	    sta const_ptr
	    lda #>pattern_while
	    sta const_ptr+1
	    jsr pattern_matches_scan_ptr_keyword
	    bcs collect_proc_body_ops_try_do_keyword
	    jsr push_while_loop_kind_or_fail
	    lda #'d'
	    jsr append_body_op_no_arg_for_current_proc
	    jsr advance_scan_ptr_by_const_ptr
	    lda #'f'
	    sta expr_print_op
	    jsr store_small_runtime_condition_core
	    bcs collect_proc_body_ops_if_bad_literal
	    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_do_keyword:
	    lda #<pattern_do
	    sta const_ptr
	    lda #>pattern_do
	    sta const_ptr+1
	    jsr pattern_matches_scan_ptr_keyword
	    bcs collect_proc_body_ops_try_endif
	    jsr push_do_loop_kind_or_fail
	    lda #'d'
	    jsr append_body_op_no_arg_for_current_proc
	    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_endif:
	    lda #<pattern_endif
	    sta const_ptr
	    lda #>pattern_endif
	    sta const_ptr+1
	    jsr pattern_matches_scan_ptr_keyword
	    bcs collect_proc_body_ops_try_fi
	    lda #'v'
	    jsr append_body_op_no_arg_for_current_proc
	    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_fi:
	    lda #<pattern_fi
	    sta const_ptr
	    lda #>pattern_fi
	    sta const_ptr+1
	    jsr pattern_matches_scan_ptr_keyword
	    bcs collect_proc_body_ops_try_else
	    lda #'v'
	    jsr append_body_op_no_arg_for_current_proc
	    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_else:
	    lda #<pattern_else
	    sta const_ptr
	    lda #>pattern_else
	    sta const_ptr+1
	    jsr pattern_matches_scan_ptr_keyword
	    bcs collect_proc_body_ops_try_if
	    lda #'w'
	    jsr append_body_op_no_arg_for_current_proc
	    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_if:
	    lda #<pattern_if
	    sta const_ptr
	    lda #>pattern_if
	    sta const_ptr+1
	    jsr pattern_matches_scan_ptr_keyword
	    bcs collect_proc_body_ops_try_printe
	    jsr advance_scan_ptr_by_const_ptr
	    jsr store_small_runtime_condition_from_scan_ptr
	    bcs collect_proc_body_ops_if_bad_literal
	    jmp collect_proc_body_ops_skip_line
collect_proc_body_ops_if_bad_literal:
	    jmp collect_proc_body_ops_bad_literal

	    lda #<pattern_print_quote
	    sta const_ptr
	    lda #>pattern_print_quote
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs collect_proc_body_ops_try_printe
    jsr advance_scan_ptr_by_const_ptr
    lda #$12
    sta actc_trace_byte
    jsr store_string_literal_from_scan_ptr
    bcc :+
    jmp collect_proc_body_ops_bad_literal
:
    lda #$13
    sta actc_trace_byte
    lda #'s'
    jsr append_body_op_for_current_proc
    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_printe:
    lda #<pattern_printe_quote
    sta const_ptr
    lda #>pattern_printe_quote
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs collect_proc_body_ops_try_printie
    jsr advance_scan_ptr_by_const_ptr
    lda #$14
    sta actc_trace_byte
    jsr store_string_literal_from_scan_ptr
    bcc :+
    jmp collect_proc_body_ops_bad_literal
:
    lda #$15
    sta actc_trace_byte
    lda #'e'
    jsr append_body_op_for_current_proc
    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_printie:
    lda #<pattern_printie
    sta const_ptr
    lda #>pattern_printie
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs collect_proc_body_ops_try_printi
    jsr advance_scan_ptr_by_const_ptr
    lda #'z'
    sta expr_print_op
    jsr store_small_runtime_expr_from_scan_ptr
    bcc collect_proc_body_ops_try_printie_runtime_done
    jsr store_small_decimal_literal_from_scan_ptr
    bcc collect_proc_body_ops_try_printie_literal_done
    jmp collect_proc_body_ops_bad_literal
collect_proc_body_ops_try_printie_runtime_done:
    jmp collect_proc_body_ops_skip_line
collect_proc_body_ops_try_printie_literal_done:
    lda #'i'
    jsr append_body_op_for_current_proc
    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_printi:
    lda #<pattern_printi
    sta const_ptr
    lda #>pattern_printi
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs collect_proc_body_ops_try_return
    jsr advance_scan_ptr_by_const_ptr
    lda #'y'
    sta expr_print_op
    jsr store_small_runtime_expr_from_scan_ptr
    bcc collect_proc_body_ops_try_printi_runtime_done
    jsr store_small_decimal_literal_from_scan_ptr
    bcc collect_proc_body_ops_try_printi_literal_done
    jmp collect_proc_body_ops_bad_literal
collect_proc_body_ops_try_printi_runtime_done:
    jmp collect_proc_body_ops_skip_line
collect_proc_body_ops_try_printi_literal_done:
    lda #'j'
    jsr append_body_op_for_current_proc
    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_return:
    lda #<pattern_return
    sta const_ptr
    lda #>pattern_return
    sta const_ptr+1
    jsr pattern_matches_scan_ptr_keyword
    bcs collect_proc_body_ops_try_assignment
    jsr advance_scan_ptr_by_const_ptr
    ldy #$00
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    beq collect_proc_body_ops_try_return_emit
    cmp #10
    beq collect_proc_body_ops_try_return_emit
    cmp #13
    beq collect_proc_body_ops_try_return_emit
    jsr emit_runtime_value_from_scan_y_or_fail
    bcc :+
    jmp collect_proc_body_ops_bad_literal
: 
    jsr require_line_end_at_scan_y
    bcc collect_proc_body_ops_try_return_emit
    jmp collect_proc_body_ops_bad_literal
collect_proc_body_ops_try_return_emit:
    lda #'r'
    jsr append_body_op_no_arg_for_current_proc
    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_assignment:
    jsr copy_symbol_from_scan_ptr
    bcs collect_proc_body_ops_skip_line
    sty hex_work
    ldy hex_work
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'='
    bne collect_proc_body_ops_try_local_call
    jsr find_var_index_from_declared
    bcs collect_proc_body_ops_bad_var
    stx assignment_target_index_data
    iny
    jsr emit_runtime_value_from_scan_y_or_fail
    bcs collect_proc_body_ops_bad_literal
    jsr require_line_end_at_scan_y
    bcs collect_proc_body_ops_bad_literal
    ldx assignment_target_index_data
    lda #'S'
    jsr append_body_op_for_current_proc
    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_local_call:
    ldy hex_work
    lda (scan_ptr),y
    cmp #'('
    bne collect_proc_body_ops_skip_line
    sty symbol_end_y_data
    jsr resolve_call_target_from_declared_or_fail
    bcs collect_proc_body_ops_bad_proc
    ldy symbol_end_y_data
    jsr emit_call_args_from_scan_y_or_fail
    bcs collect_proc_body_ops_bad_proc
    lda call_target_kind
    ldx call_target_index_data
    jsr append_body_op_for_current_proc
collect_proc_body_ops_skip_line:
    jsr skip_source_line
    jmp collect_proc_body_ops_loop
collect_proc_body_ops_proc_decl:
    jsr advance_scan_ptr_by_const_ptr
    jsr skip_source_spaces
    jsr copy_symbol_from_scan_ptr
    bcs collect_proc_body_ops_bad_proc
    jsr find_export_index_from_declared
    bcs collect_proc_body_ops_bad_proc
    stx current_proc_index_data
    jsr emit_current_proc_param_binds_or_fail
    jsr skip_source_line
    jmp collect_proc_body_ops_loop
collect_proc_body_ops_advance_blank:
    jsr advance_scan_ptr
    jmp collect_proc_body_ops_loop
collect_proc_body_ops_bad_proc:
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_ptr
collect_proc_body_ops_bad_var:
    lda #<msg_bad_var
    ldy #>msg_bad_var
    jmp fail_with_ptr
collect_proc_body_ops_bad_literal:
    lda #<msg_bad_literal
    ldy #>msg_bad_literal
    jmp fail_with_ptr
collect_proc_body_ops_done:
    rts

append_body_op_for_current_proc:
    sta compare_char
    stx hex_work
    tya
    pha
    ldx current_proc_index_data
    jsr set_body_ptr_from_x
    ldy #$00
append_body_op_for_current_proc_loop:
    lda (body_ptr),y
    beq append_body_op_for_current_proc_store
    iny
    cpy #(BODY_OPS_STRIDE - 2)
    bcc append_body_op_for_current_proc_loop
    lda compare_char
    sta actc_trace_byte
    sty $03FC
    lda #'A'
    sta $03FD
    lda #<msg_bad_call
    ldy #>msg_bad_call
    jmp fail_with_ptr
append_body_op_for_current_proc_store:
    lda compare_char
    sta (body_ptr),y
    iny
    lda hex_work
    cmp #10
    bcc :+
    sec
    sbc #10
    clc
    adc #'A'
    bne append_body_op_for_current_proc_store_index
:   clc
    adc #'0'
append_body_op_for_current_proc_store_index:
    sta (body_ptr),y
    iny
    lda #$00
    sta (body_ptr),y
    pla
    tay
    rts

append_body_op_no_arg_for_current_proc:
    sta compare_char
    tya
    pha
    ldx current_proc_index_data
    jsr set_body_ptr_from_x
    ldy #$00
append_body_op_no_arg_for_current_proc_loop:
    lda (body_ptr),y
    beq append_body_op_no_arg_for_current_proc_store
    iny
    cpy #(BODY_OPS_STRIDE - 1)
    bcc append_body_op_no_arg_for_current_proc_loop
    lda compare_char
    sta actc_trace_byte
    sty $03FC
    lda #'N'
    sta $03FD
    lda #<msg_bad_call
    ldy #>msg_bad_call
    jmp fail_with_ptr
append_body_op_no_arg_for_current_proc_store:
    lda compare_char
    sta (body_ptr),y
    iny
    lda #$00
    sta (body_ptr),y
    pla
    tay
    rts

push_do_loop_kind_or_fail:
    lda #$00
    jmp push_loop_kind_a_or_fail

push_while_loop_kind_or_fail:
    lda #$01

push_loop_kind_a_or_fail:
    ldx loop_depth_data
    cpx #LOOP_MAX
    bcc :+
    jmp collect_proc_body_ops_bad_proc
:   sta loop_kind_stack,x
    inc loop_depth_data
    rts

emit_current_proc_param_binds_or_fail:
    ldx current_proc_index_data
    lda proc_param_count_data,x
    beq emit_current_proc_param_binds_or_fail_done
    sta param_bind_count_data
    lda proc_param_var_base_data,x
    sta param_bind_base_data
emit_current_proc_param_binds_or_fail_loop:
    lda param_bind_count_data
    beq emit_current_proc_param_binds_or_fail_done
    clc
    lda param_bind_base_data
    adc param_bind_count_data
    sec
    sbc #$01
    tax
    lda #'S'
    jsr append_body_op_for_current_proc
    dec param_bind_count_data
    jmp emit_current_proc_param_binds_or_fail_loop
emit_current_proc_param_binds_or_fail_done:
    rts

pop_loop_kind_to_compare_char_or_fail:
    ldx loop_depth_data
    bne :+
    jmp collect_proc_body_ops_bad_proc
:   dex
    stx loop_depth_data
    lda loop_kind_stack,x
    sta compare_char
    rts

set_body_ptr_from_x:
    txa
    pha
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
    pla
    tax
    rts

set_string_ptr_from_x:
    lda #<string_literals
    sta body_ptr
    lda #>string_literals
    sta body_ptr+1
set_string_ptr_from_x_loop:
    cpx #$00
    beq set_string_ptr_from_x_done
    clc
    lda body_ptr
    adc #24
    sta body_ptr
    lda body_ptr+1
    adc #$00
    sta body_ptr+1
    dex
    bne set_string_ptr_from_x_loop
set_string_ptr_from_x_done:
    rts

store_string_literal_from_scan_ptr:
    ldx string_count_data
    cpx #STRING_LITERAL_MAX
    bcc :+
    sec
    rts
:   txa
    pha
    jsr set_string_ptr_from_x
    pla
    tax
    ldy #$00
store_string_literal_from_scan_ptr_loop:
    lda (scan_ptr),y
    beq store_string_literal_from_scan_ptr_fail
    cmp #'"'
    beq store_string_literal_from_scan_ptr_done
    sta (body_ptr),y
    iny
    cpy #23
    bcc store_string_literal_from_scan_ptr_loop
store_string_literal_from_scan_ptr_fail:
    sec
    rts
store_string_literal_from_scan_ptr_done:
    lda #$00
    sta (body_ptr),y
    inc string_count_data
    clc
    rts

store_small_decimal_literal_from_scan_ptr:
    ldx int_count_data
    cpx #INT_LITERAL_MAX
    bcc :+
    sec
    rts
:   ldy #$00
    jsr parse_small_value_expr_at_scan_y
    bcs store_small_decimal_literal_from_scan_ptr_fail
    lda expr_value_lo
    sta int_values_lo,x
    lda #$00
    sta int_values_hi,x
    inc int_count_data
    clc
    rts
store_small_decimal_literal_from_scan_ptr_fail:
    sec
    rts

store_small_runtime_expr_from_scan_ptr:
    ldy #$00
    jsr scan_value_expr_for_top_level_arith_from_scan_y
    bcs :+
    jmp store_small_runtime_expr_sum_entry
: 
    jsr scan_print_expr_for_bool_keywords_from_scan_y
    bcs :+
    jmp store_small_runtime_expr_bool_entry
: 
store_small_runtime_expr_sum_entry:
    lda #$00
    sta expr_runtime_post_zero
    jsr emit_runtime_sum_from_scan_y_or_fail
    bcc :+
    sec
    rts
:   jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    sta expr_compare_lo
    cmp #')'
    bne :+
    jmp store_small_runtime_expr_print
: 
    cmp #'='
    beq store_small_runtime_expr_compare_entry
    cmp #'<'
    beq store_small_runtime_expr_compare_entry
    cmp #'>' 
    beq store_small_runtime_expr_compare_entry
    sec
    rts
store_small_runtime_expr_compare_entry:
    lda #$00
    sta expr_runtime_post_zero
    lda expr_compare_lo
    cmp #'='
    beq store_small_runtime_expr_eq
    cmp #'<'
    beq store_small_runtime_expr_lt_entry
    cmp #'>' 
    beq store_small_runtime_expr_gt_entry
    sec
    rts
store_small_runtime_expr_eq:
    lda #'q'
    sta expr_runtime_op
    iny
    jmp store_small_runtime_expr_rhs
store_small_runtime_expr_lt_entry:
    iny
    lda (scan_ptr),y
    cmp #'>'
    beq store_small_runtime_expr_ne
    cmp #'='
    beq store_small_runtime_expr_le
    lda #'l'
    sta expr_runtime_op
    jmp store_small_runtime_expr_rhs
store_small_runtime_expr_gt_entry:
    iny
    lda (scan_ptr),y
    cmp #'='
    beq store_small_runtime_expr_ge
    lda #'g'
    sta expr_runtime_op
    jmp store_small_runtime_expr_rhs
store_small_runtime_expr_le:
    lda #'g'
    sta expr_runtime_op
    lda #$01
    sta expr_runtime_post_zero
    iny
    jmp store_small_runtime_expr_rhs
store_small_runtime_expr_ge:
    lda #'l'
    sta expr_runtime_op
    lda #$01
    sta expr_runtime_post_zero
    iny
    jmp store_small_runtime_expr_rhs
store_small_runtime_expr_ne:
    lda #'n'
    sta expr_runtime_op
    iny
store_small_runtime_expr_rhs:
    jsr emit_runtime_sum_from_scan_y_or_fail
    bcc :+
store_small_runtime_expr_fail:
    sec
    rts
:   jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne store_small_runtime_expr_fail
    lda expr_runtime_op
    jsr append_body_op_no_arg_for_current_proc
    lda expr_runtime_post_zero
    beq store_small_runtime_expr_print
    lda #$00
    sta expr_value_lo
    jsr store_expr_value_as_int_literal
    bcs store_small_runtime_expr_fail
    lda #'p'
    jsr append_body_op_for_current_proc
    lda #'q'
    jsr append_body_op_no_arg_for_current_proc
store_small_runtime_expr_print:
    lda expr_print_op
    jsr append_body_op_no_arg_for_current_proc
    clc
    rts

store_small_runtime_expr_bool_entry:
    lda #$00
    sta bool_ops_used_data
    jsr emit_runtime_bool_or_from_scan_y_or_fail
    bcs store_small_runtime_expr_fail
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne store_small_runtime_expr_fail
    jmp store_small_runtime_expr_print

store_small_runtime_condition_from_scan_ptr:
    lda #'h'
    sta expr_print_op
    jmp store_small_runtime_condition_core

store_small_runtime_until_from_scan_ptr:
    lda #'t'
    sta expr_print_op
store_small_runtime_condition_core:
    lda #$00
    sta bool_ops_used_data
    ldy #$00
    jsr emit_runtime_bool_or_from_scan_y_or_fail
    bcc store_small_runtime_condition_done_check
    sec
    rts
store_small_runtime_condition_done_check:
    lda expr_print_op
    cmp #'h'
    bne :+
    jsr require_then_or_line_end_at_scan_y
    bcc store_small_runtime_condition_done_ok
    jmp store_small_runtime_condition_fail
:   cmp #'f'
    bne :+
    jsr require_do_or_line_end_at_scan_y
    bcc store_small_runtime_condition_done_ok
    jmp store_small_runtime_condition_fail
:   jsr require_line_end_at_scan_y
    bcc store_small_runtime_condition_done_ok
store_small_runtime_condition_fail:
    sec
    rts
store_small_runtime_condition_done_ok:
    lda expr_print_op
    jsr append_body_op_no_arg_for_current_proc
    clc
    rts

require_line_end_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    beq require_line_end_at_scan_y_ok
    cmp #10
    beq require_line_end_at_scan_y_ok
    cmp #13
    beq require_line_end_at_scan_y_ok
    sec
    rts
require_line_end_at_scan_y_ok:
    clc
    rts

require_then_or_line_end_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    beq require_then_or_line_end_at_scan_y_ok
    cmp #10
    beq require_then_or_line_end_at_scan_y_ok
    cmp #13
    beq require_then_or_line_end_at_scan_y_ok
    jsr uppercase_ascii
    cmp #'T'
    bne require_then_or_line_end_at_scan_y_fail
    iny
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'H'
    bne require_then_or_line_end_at_scan_y_fail
    iny
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'E'
    bne require_then_or_line_end_at_scan_y_fail
    iny
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'N'
    bne require_then_or_line_end_at_scan_y_fail
    iny
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    beq require_then_or_line_end_at_scan_y_ok
    cmp #10
    beq require_then_or_line_end_at_scan_y_ok
    cmp #13
    beq require_then_or_line_end_at_scan_y_ok
require_then_or_line_end_at_scan_y_fail:
    sec
    rts
require_then_or_line_end_at_scan_y_ok:
    clc
    rts

require_do_or_line_end_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    beq require_do_or_line_end_at_scan_y_ok
    cmp #10
    beq require_do_or_line_end_at_scan_y_ok
    cmp #13
    beq require_do_or_line_end_at_scan_y_ok
    jsr uppercase_ascii
    cmp #'D'
    bne require_do_or_line_end_at_scan_y_fail
    iny
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'O'
    bne require_do_or_line_end_at_scan_y_fail
    iny
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    beq require_do_or_line_end_at_scan_y_ok
    cmp #10
    beq require_do_or_line_end_at_scan_y_ok
    cmp #13
    beq require_do_or_line_end_at_scan_y_ok
require_do_or_line_end_at_scan_y_fail:
    sec
    rts
require_do_or_line_end_at_scan_y_ok:
    clc
    rts

emit_saved_expr_push_or_fail:
    lda expr_saved_lo
    sta expr_value_lo
emit_current_expr_push_or_fail:
    jsr store_expr_value_as_int_literal
    bcs emit_runtime_expr_push_fail
    lda #'p'
    jsr append_body_op_for_current_proc
    clc
    rts
emit_runtime_expr_push_fail:
    sec
    rts

emit_runtime_term_push_from_scan_y_or_fail:
    jsr skip_inline_spaces_at_scan_y
    tya
    pha
    jsr find_var_index_from_scan_y
    bcs emit_runtime_term_push_literal
    lda #'L'
    jsr append_body_op_for_current_proc
    pla
    clc
    rts
emit_runtime_term_push_literal:
    pla
    tay
    jsr emit_runtime_call_term_from_scan_y_or_fail
    bcc :+
    tya
    pha
    jsr parse_small_decimal_term_at_scan_y
    bcc emit_runtime_term_push_literal_decimal
    pla
    tay
    jsr emit_runtime_group_value_term_from_scan_y_or_fail
    bcs emit_runtime_expr_push_fail
    clc
    rts
emit_runtime_term_push_literal_decimal:
    pla
    jmp emit_current_expr_push_or_fail
:   clc
    rts

emit_runtime_group_value_term_from_scan_y_or_fail:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'('
    bne emit_runtime_group_value_term_from_scan_y_or_fail_fail
    iny
    jsr emit_runtime_value_from_scan_y_or_fail
    bcs emit_runtime_group_value_term_from_scan_y_or_fail_fail
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne emit_runtime_group_value_term_from_scan_y_or_fail_fail
    iny
    clc
    rts
emit_runtime_group_value_term_from_scan_y_or_fail_fail:
    sec
    rts

emit_runtime_call_term_from_scan_y_or_fail:
    jsr copy_symbol_from_scan_y
    bcc :+
    sec
    rts
:
    sty symbol_end_y_data
    jsr resolve_call_target_from_declared_or_fail
    bcs emit_runtime_call_term_from_scan_y_or_fail_fail
    ldy symbol_end_y_data
    jsr emit_call_args_from_scan_y_or_fail
    bcs emit_runtime_call_term_from_scan_y_or_fail_fail
    lda call_target_kind
    ldx call_target_index_data
    jsr append_body_op_for_current_proc
    clc
    rts
emit_runtime_call_term_from_scan_y_or_fail_fail:
    sec
    rts

resolve_call_target_from_declared_or_fail:
    jsr find_export_index_from_declared
    bcc resolve_call_target_from_declared_or_fail_local
    jsr find_or_store_external_from_declared
    bcs resolve_call_target_from_declared_or_fail_fail
    stx call_target_index_data
    lda #'u'
    sta call_target_kind
    lda #$FF
    sta call_expected_arg_count
    clc
    rts
resolve_call_target_from_declared_or_fail_local:
    cpx current_proc_index_data
    beq resolve_call_target_from_declared_or_fail_fail
    stx call_target_index_data
    lda #'c'
    sta call_target_kind
    lda proc_param_count_data,x
    sta call_expected_arg_count
    clc
    rts
resolve_call_target_from_declared_or_fail_fail:
    sec
    rts

emit_call_args_from_scan_y_or_fail:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'('
    beq :+
    sec
    rts
:   iny
    lda #$00
    sta call_arg_count_data
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    beq emit_call_args_from_scan_y_or_fail_done
emit_call_args_from_scan_y_or_fail_loop:
    lda call_arg_count_data
    pha
    lda call_expected_arg_count
    pha
    lda call_target_index_data
    pha
    lda call_target_kind
    pha
    jsr emit_runtime_value_from_scan_y_or_fail
    bcc emit_call_args_from_scan_y_or_fail_restore_ok
    pla
    sta call_target_kind
    pla
    sta call_target_index_data
    pla
    sta call_expected_arg_count
    pla
    sta call_arg_count_data
    sec
    rts
emit_call_args_from_scan_y_or_fail_restore_ok:
    pla
    sta call_target_kind
    pla
    sta call_target_index_data
    pla
    sta call_expected_arg_count
    pla
    sta call_arg_count_data
    inc call_arg_count_data
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #','
    beq emit_call_args_from_scan_y_or_fail_next
    cmp #')'
    beq emit_call_args_from_scan_y_or_fail_done
    sec
    rts
emit_call_args_from_scan_y_or_fail_next:
    iny
    jsr skip_inline_spaces_at_scan_y
    jmp emit_call_args_from_scan_y_or_fail_loop
emit_call_args_from_scan_y_or_fail_done:
    iny
    lda call_target_kind
    cmp #'c'
    bne emit_call_args_from_scan_y_or_fail_ok
    lda call_arg_count_data
    cmp call_expected_arg_count
    bne emit_call_args_from_scan_y_or_fail_fail
emit_call_args_from_scan_y_or_fail_ok:
    clc
    rts
emit_call_args_from_scan_y_or_fail_fail:
    sec
    rts

emit_runtime_value_from_scan_y_or_fail:
    jsr scan_value_expr_for_top_level_arith_from_scan_y
    bcs :+
    jmp emit_runtime_sum_from_scan_y_or_fail
: 
    jsr scan_value_expr_for_bool_tokens_from_scan_y
    bcc emit_runtime_value_from_scan_y_or_fail_bool
    jmp emit_runtime_sum_from_scan_y_or_fail
emit_runtime_value_from_scan_y_or_fail_bool:
    lda #$00
    sta bool_ops_used_data
    jmp emit_runtime_bool_or_from_scan_y_or_fail

scan_value_expr_for_top_level_arith_from_scan_y:
    sty symbol_start_y_data
    lda #$00
    sta hex_work
scan_value_expr_for_top_level_arith_from_scan_y_loop:
    lda (scan_ptr),y
    beq scan_value_expr_for_top_level_arith_from_scan_y_not_found
    cmp #10
    beq scan_value_expr_for_top_level_arith_from_scan_y_not_found
    cmp #13
    beq scan_value_expr_for_top_level_arith_from_scan_y_not_found
    cmp #','
    beq scan_value_expr_for_top_level_arith_from_scan_y_comma
    cmp #')'
    beq scan_value_expr_for_top_level_arith_from_scan_y_rparen
    cmp #'('
    beq scan_value_expr_for_top_level_arith_from_scan_y_lparen
    ldx hex_work
    bne scan_value_expr_for_top_level_arith_from_scan_y_next
    cmp #'+'
    beq scan_value_expr_for_top_level_arith_from_scan_y_found
    cmp #'-'
    beq scan_value_expr_for_top_level_arith_from_scan_y_found
    cmp #'*'
    beq scan_value_expr_for_top_level_arith_from_scan_y_found
    cmp #'/'
    beq scan_value_expr_for_top_level_arith_from_scan_y_found
scan_value_expr_for_top_level_arith_from_scan_y_next:
    iny
    bne scan_value_expr_for_top_level_arith_from_scan_y_loop
scan_value_expr_for_top_level_arith_from_scan_y_not_found:
    ldy symbol_start_y_data
    sec
    rts
scan_value_expr_for_top_level_arith_from_scan_y_comma:
    lda hex_work
    beq scan_value_expr_for_top_level_arith_from_scan_y_not_found
    iny
    jmp scan_value_expr_for_top_level_arith_from_scan_y_loop
scan_value_expr_for_top_level_arith_from_scan_y_rparen:
    lda hex_work
    beq scan_value_expr_for_top_level_arith_from_scan_y_not_found
    dec hex_work
    iny
    jmp scan_value_expr_for_top_level_arith_from_scan_y_loop
scan_value_expr_for_top_level_arith_from_scan_y_lparen:
    inc hex_work
    iny
    jmp scan_value_expr_for_top_level_arith_from_scan_y_loop
scan_value_expr_for_top_level_arith_from_scan_y_found:
    ldy symbol_start_y_data
    clc
    rts

scan_print_expr_for_bool_keywords_from_scan_y:
    sty symbol_start_y_data
    lda #$00
    sta hex_work
scan_print_expr_for_bool_keywords_from_scan_y_loop:
    lda (scan_ptr),y
    beq scan_print_expr_for_bool_keywords_from_scan_y_not_found
    cmp #10
    beq scan_print_expr_for_bool_keywords_from_scan_y_not_found
    cmp #13
    beq scan_print_expr_for_bool_keywords_from_scan_y_not_found
    cmp #')'
    beq scan_print_expr_for_bool_keywords_from_scan_y_rparen
    cmp #'('
    beq scan_print_expr_for_bool_keywords_from_scan_y_lparen
    jsr uppercase_ascii
    cmp #'A'
    beq scan_print_expr_for_bool_keywords_from_scan_y_try_and
    cmp #'O'
    beq scan_print_expr_for_bool_keywords_from_scan_y_try_or
    cmp #'N'
    beq scan_print_expr_for_bool_keywords_from_scan_y_try_not
scan_print_expr_for_bool_keywords_from_scan_y_next:
    iny
    bne scan_print_expr_for_bool_keywords_from_scan_y_loop
scan_print_expr_for_bool_keywords_from_scan_y_not_found:
    ldy symbol_start_y_data
    sec
    rts
scan_print_expr_for_bool_keywords_from_scan_y_rparen:
    lda hex_work
    beq scan_print_expr_for_bool_keywords_from_scan_y_not_found
    dec hex_work
    iny
    jmp scan_print_expr_for_bool_keywords_from_scan_y_loop
scan_print_expr_for_bool_keywords_from_scan_y_lparen:
    inc hex_work
    iny
    jmp scan_print_expr_for_bool_keywords_from_scan_y_loop
scan_print_expr_for_bool_keywords_from_scan_y_try_and:
    jsr consume_and_keyword_from_scan_y
    bcc scan_print_expr_for_bool_keywords_from_scan_y_found
    jmp scan_print_expr_for_bool_keywords_from_scan_y_next
scan_print_expr_for_bool_keywords_from_scan_y_try_or:
    jsr consume_or_keyword_from_scan_y
    bcc scan_print_expr_for_bool_keywords_from_scan_y_found
    jmp scan_print_expr_for_bool_keywords_from_scan_y_next
scan_print_expr_for_bool_keywords_from_scan_y_try_not:
    jsr consume_not_keyword_from_scan_y
    bcc scan_print_expr_for_bool_keywords_from_scan_y_found
    jmp scan_print_expr_for_bool_keywords_from_scan_y_next
scan_print_expr_for_bool_keywords_from_scan_y_found:
    ldy symbol_start_y_data
    clc
    rts

scan_value_expr_for_bool_tokens_from_scan_y:
    sty symbol_start_y_data
    lda #$00
    sta hex_work
scan_value_expr_for_bool_tokens_from_scan_y_loop:
    lda (scan_ptr),y
    beq scan_value_expr_for_bool_tokens_from_scan_y_not_found
    cmp #10
    beq scan_value_expr_for_bool_tokens_from_scan_y_not_found
    cmp #13
    beq scan_value_expr_for_bool_tokens_from_scan_y_not_found
    cmp #','
    beq scan_value_expr_for_bool_tokens_from_scan_y_comma
    cmp #')'
    beq scan_value_expr_for_bool_tokens_from_scan_y_rparen
    cmp #'('
    beq scan_value_expr_for_bool_tokens_from_scan_y_lparen
    cmp #'='
    beq scan_value_expr_for_bool_tokens_from_scan_y_found
    cmp #'<'
    beq scan_value_expr_for_bool_tokens_from_scan_y_found
    cmp #'>'
    beq scan_value_expr_for_bool_tokens_from_scan_y_found
    jsr uppercase_ascii
    cmp #'A'
    beq scan_value_expr_for_bool_tokens_from_scan_y_try_and
    cmp #'O'
    beq scan_value_expr_for_bool_tokens_from_scan_y_try_or
    cmp #'N'
    beq scan_value_expr_for_bool_tokens_from_scan_y_try_not
scan_value_expr_for_bool_tokens_from_scan_y_next:
    iny
    bne scan_value_expr_for_bool_tokens_from_scan_y_loop
scan_value_expr_for_bool_tokens_from_scan_y_not_found:
    ldy symbol_start_y_data
    sec
    rts
scan_value_expr_for_bool_tokens_from_scan_y_comma:
    lda hex_work
    beq scan_value_expr_for_bool_tokens_from_scan_y_not_found
    iny
    jmp scan_value_expr_for_bool_tokens_from_scan_y_loop
scan_value_expr_for_bool_tokens_from_scan_y_rparen:
    lda hex_work
    beq scan_value_expr_for_bool_tokens_from_scan_y_not_found
    dec hex_work
    iny
    jmp scan_value_expr_for_bool_tokens_from_scan_y_loop
scan_value_expr_for_bool_tokens_from_scan_y_lparen:
    inc hex_work
    iny
    jmp scan_value_expr_for_bool_tokens_from_scan_y_loop
scan_value_expr_for_bool_tokens_from_scan_y_try_and:
    jsr consume_and_keyword_from_scan_y
    bcc scan_value_expr_for_bool_tokens_from_scan_y_found
    jmp scan_value_expr_for_bool_tokens_from_scan_y_next
scan_value_expr_for_bool_tokens_from_scan_y_try_or:
    jsr consume_or_keyword_from_scan_y
    bcc scan_value_expr_for_bool_tokens_from_scan_y_found
    jmp scan_value_expr_for_bool_tokens_from_scan_y_next
scan_value_expr_for_bool_tokens_from_scan_y_try_not:
    jsr consume_not_keyword_from_scan_y
    bcc scan_value_expr_for_bool_tokens_from_scan_y_found
    jmp scan_value_expr_for_bool_tokens_from_scan_y_next
scan_value_expr_for_bool_tokens_from_scan_y_found:
    ldy symbol_start_y_data
    clc
    rts

emit_runtime_bool_or_from_scan_y_or_fail:
    jsr emit_runtime_bool_and_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
emit_runtime_bool_or_from_scan_y_or_fail_loop:
    jsr consume_or_keyword_from_scan_y
    bcs emit_runtime_bool_or_from_scan_y_or_fail_done
    lda #$01
    sta bool_ops_used_data
    jsr normalize_runtime_top_to_bool_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
    jsr emit_runtime_bool_and_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
    jsr normalize_runtime_top_to_bool_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
    lda #'a'
    jsr append_body_op_no_arg_for_current_proc
    lda #$00
    sta expr_value_lo
    jsr store_expr_value_as_int_literal
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
    lda #'p'
    jsr append_body_op_for_current_proc
    lda #'g'
    jsr append_body_op_no_arg_for_current_proc
    jmp emit_runtime_bool_or_from_scan_y_or_fail_loop
emit_runtime_bool_or_from_scan_y_or_fail_done:
    clc
    rts

emit_runtime_bool_and_from_scan_y_or_fail:
    jsr emit_runtime_bool_not_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
emit_runtime_bool_and_from_scan_y_or_fail_loop:
    jsr consume_and_keyword_from_scan_y
    bcs emit_runtime_bool_and_from_scan_y_or_fail_done
    lda #$01
    sta bool_ops_used_data
    jsr normalize_runtime_top_to_bool_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
    jsr emit_runtime_bool_not_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
    jsr normalize_runtime_top_to_bool_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
    lda #'a'
    jsr append_body_op_no_arg_for_current_proc
    lda #$01
    sta expr_value_lo
    jsr store_expr_value_as_int_literal
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
    lda #'p'
    jsr append_body_op_for_current_proc
    lda #'g'
    jsr append_body_op_no_arg_for_current_proc
    jmp emit_runtime_bool_and_from_scan_y_or_fail_loop
emit_runtime_bool_and_from_scan_y_or_fail_done:
    clc
    rts

emit_runtime_bool_not_from_scan_y_or_fail:
    jsr consume_not_keyword_from_scan_y
    bcs emit_runtime_bool_primary_from_scan_y_or_fail
    lda #$01
    sta bool_ops_used_data
    jsr emit_runtime_bool_not_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
    jsr normalize_runtime_top_to_bool_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
    lda #$00
    sta expr_value_lo
    jsr store_expr_value_as_int_literal
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
    lda #'p'
    jsr append_body_op_for_current_proc
    lda #'q'
    jsr append_body_op_no_arg_for_current_proc
    clc
    rts

emit_runtime_bool_primary_from_scan_y_or_fail:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'('
    bne emit_runtime_condition_clause_from_scan_y_or_fail
    tya
    pha
    iny
    jsr emit_runtime_bool_or_from_scan_y_or_fail
    bcs emit_runtime_bool_primary_restore_clause
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne emit_runtime_bool_primary_restore_clause
    iny
    sty compare_char
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'='
    beq emit_runtime_bool_primary_restore_clause
    cmp #'<'
    beq emit_runtime_bool_primary_restore_clause
    cmp #'>'
    beq emit_runtime_bool_primary_restore_clause
    ldy compare_char
    pla
    clc
    rts
emit_runtime_bool_primary_restore_clause:
    pla
    tay
    jmp emit_runtime_condition_clause_from_scan_y_or_fail

emit_runtime_condition_clause_from_scan_y_or_fail:
    jsr emit_runtime_sum_from_scan_y_or_fail
    bcc :+
    sec
    rts
:   jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    sta expr_compare_lo
    cmp #'='
    beq emit_runtime_condition_clause_compare_entry
    cmp #'<'
    beq emit_runtime_condition_clause_compare_entry
    cmp #'>'
    beq emit_runtime_condition_clause_compare_entry
    jmp emit_runtime_condition_clause_done
emit_runtime_condition_clause_compare_entry:
    lda #$00
    sta expr_runtime_post_zero
    lda expr_compare_lo
    cmp #'='
    beq emit_runtime_condition_clause_eq
    cmp #'<'
    beq emit_runtime_condition_clause_lt_entry
    cmp #'>'
    beq emit_runtime_condition_clause_gt_entry
    sec
    rts
emit_runtime_condition_clause_eq:
    lda #'q'
    sta expr_runtime_op
    iny
    jmp emit_runtime_condition_clause_rhs
emit_runtime_condition_clause_lt_entry:
    iny
    lda (scan_ptr),y
    cmp #'>'
    beq emit_runtime_condition_clause_ne
    cmp #'='
    beq emit_runtime_condition_clause_le
    lda #'l'
    sta expr_runtime_op
    jmp emit_runtime_condition_clause_rhs
emit_runtime_condition_clause_gt_entry:
    iny
    lda (scan_ptr),y
    cmp #'='
    beq emit_runtime_condition_clause_ge
    lda #'g'
    sta expr_runtime_op
    jmp emit_runtime_condition_clause_rhs
emit_runtime_condition_clause_le:
    lda #'g'
    sta expr_runtime_op
    lda #$01
    sta expr_runtime_post_zero
    iny
    jmp emit_runtime_condition_clause_rhs
emit_runtime_condition_clause_ge:
    lda #'l'
    sta expr_runtime_op
    lda #$01
    sta expr_runtime_post_zero
    iny
    jmp emit_runtime_condition_clause_rhs
emit_runtime_condition_clause_ne:
    lda #'n'
    sta expr_runtime_op
    iny
emit_runtime_condition_clause_rhs:
    jsr emit_runtime_sum_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
    lda expr_runtime_op
    jsr append_body_op_no_arg_for_current_proc
    lda expr_runtime_post_zero
    beq emit_runtime_condition_clause_done
    lda #$00
    sta expr_value_lo
    jsr store_expr_value_as_int_literal
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
    lda #'p'
    jsr append_body_op_for_current_proc
    lda #'q'
    jsr append_body_op_no_arg_for_current_proc
emit_runtime_condition_clause_done:
    clc
    rts

normalize_runtime_top_to_bool_or_fail:
    lda #$00
    sta expr_value_lo
    jsr store_expr_value_as_int_literal
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
    lda #'p'
    jsr append_body_op_for_current_proc
    lda #'n'
    jsr append_body_op_no_arg_for_current_proc
    clc
    rts

emit_runtime_sum_from_scan_y_or_fail:
    jsr emit_runtime_term_push_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
emit_runtime_sum_from_scan_y_loop:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'+' 
    beq emit_runtime_sum_from_scan_y_add
    cmp #'-'
    beq emit_runtime_sum_from_scan_y_sub
    clc
    rts
emit_runtime_sum_from_scan_y_add:
    iny
    jsr emit_runtime_term_push_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
    lda #'a'
    jsr append_body_op_no_arg_for_current_proc
    jmp emit_runtime_sum_from_scan_y_loop
emit_runtime_sum_from_scan_y_sub:
    iny
    jsr emit_runtime_term_push_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
: 
    lda #'m'
    jsr append_body_op_no_arg_for_current_proc
    jmp emit_runtime_sum_from_scan_y_loop

store_expr_value_as_int_literal:
    ldx int_count_data
    cpx #INT_LITERAL_MAX
    bcc :+
    sec
    rts
:   lda expr_value_lo
    sta int_values_lo,x
    lda #$00
    sta int_values_hi,x
    inc int_count_data
    clc
    rts

parse_small_value_expr_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    jsr scan_value_expr_for_top_level_arith_from_scan_y
    bcc parse_small_value_expr_at_scan_y_sum_entry
    jsr scan_value_expr_for_bool_tokens_from_scan_y
    bcc parse_small_value_expr_at_scan_y_bool_entry
parse_small_value_expr_at_scan_y_sum_entry:
    jmp parse_small_decimal_expr_at_scan_y
parse_small_value_expr_at_scan_y_bool_entry:
    jmp parse_small_bool_or_at_scan_y

normalize_small_expr_value_to_bool:
    lda expr_value_lo
    beq :+
    lda #$01
    sta expr_value_lo
:   clc
    rts

parse_small_bool_or_at_scan_y:
    jsr parse_small_bool_and_at_scan_y
    bcs parse_small_bool_or_at_scan_y_fail
parse_small_bool_or_at_scan_y_loop:
    jsr consume_or_keyword_from_scan_y
    bcs parse_small_bool_or_at_scan_y_done
    jsr normalize_small_expr_value_to_bool
    lda expr_value_lo
    sta expr_saved_lo
    jsr parse_small_bool_and_at_scan_y
    bcs parse_small_bool_or_at_scan_y_fail
    jsr normalize_small_expr_value_to_bool
    lda expr_saved_lo
    ora expr_value_lo
    beq parse_small_bool_or_at_scan_y_store
    lda #$01
parse_small_bool_or_at_scan_y_store:
    sta expr_value_lo
    jmp parse_small_bool_or_at_scan_y_loop
parse_small_bool_or_at_scan_y_done:
    clc
    rts
parse_small_bool_or_at_scan_y_fail:
    sec
    rts

parse_small_bool_and_at_scan_y:
    jsr parse_small_bool_not_at_scan_y
    bcs parse_small_bool_and_at_scan_y_fail
parse_small_bool_and_at_scan_y_loop:
    jsr consume_and_keyword_from_scan_y
    bcs parse_small_bool_and_at_scan_y_done
    jsr normalize_small_expr_value_to_bool
    lda expr_value_lo
    sta expr_saved_lo
    jsr parse_small_bool_not_at_scan_y
    bcs parse_small_bool_and_at_scan_y_fail
    jsr normalize_small_expr_value_to_bool
    lda expr_saved_lo
    and expr_value_lo
    beq parse_small_bool_and_at_scan_y_store
    lda #$01
parse_small_bool_and_at_scan_y_store:
    sta expr_value_lo
    jmp parse_small_bool_and_at_scan_y_loop
parse_small_bool_and_at_scan_y_done:
    clc
    rts
parse_small_bool_and_at_scan_y_fail:
    sec
    rts

parse_small_bool_not_at_scan_y:
    jsr consume_not_keyword_from_scan_y
    bcs parse_small_bool_primary_at_scan_y
    jsr parse_small_bool_not_at_scan_y
    bcs parse_small_bool_not_at_scan_y_fail
    jsr normalize_small_expr_value_to_bool
    lda expr_value_lo
    eor #$01
    sta expr_value_lo
    clc
    rts
parse_small_bool_not_at_scan_y_fail:
    sec
    rts

parse_small_bool_primary_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'('
    bne parse_small_bool_condition_clause_at_scan_y
    tya
    pha
    iny
    jsr parse_small_bool_or_at_scan_y
    bcs parse_small_bool_primary_restore_clause
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne parse_small_bool_primary_restore_clause
    iny
    sty compare_char
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'='
    beq parse_small_bool_primary_restore_clause
    cmp #'<'
    beq parse_small_bool_primary_restore_clause
    cmp #'>'
    beq parse_small_bool_primary_restore_clause
    ldy compare_char
    pla
    clc
    rts
parse_small_bool_primary_restore_clause:
    pla
    tay
parse_small_bool_condition_clause_at_scan_y:
    jmp parse_small_condition_clause_at_scan_y

parse_small_condition_clause_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_condition_clause_lhs_ok
    jmp parse_small_condition_clause_at_scan_y_fail
parse_small_condition_clause_lhs_ok:
    lda expr_value_lo
    sta expr_compare_lo
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'='
    beq parse_small_condition_clause_eq
    cmp #'<'
    beq parse_small_condition_clause_lt_entry
    cmp #'>'
    beq parse_small_condition_clause_gt_entry
    lda expr_compare_lo
    sta expr_value_lo
    clc
    rts

parse_small_condition_clause_eq:
    iny
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_condition_clause_eq_ok
    jmp parse_small_condition_clause_at_scan_y_fail
parse_small_condition_clause_eq_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_condition_clause_true
    jmp parse_small_condition_clause_false

parse_small_condition_clause_lt_entry:
    iny
    lda (scan_ptr),y
    cmp #'='
    beq parse_small_condition_clause_le
    cmp #'>'
    beq parse_small_condition_clause_ne
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_condition_clause_lt_ok
    jmp parse_small_condition_clause_at_scan_y_fail
parse_small_condition_clause_lt_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    bcc parse_small_condition_clause_true
    jmp parse_small_condition_clause_false

parse_small_condition_clause_gt_entry:
    iny
    lda (scan_ptr),y
    cmp #'='
    beq parse_small_condition_clause_ge
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_condition_clause_gt_ok
    jmp parse_small_condition_clause_at_scan_y_fail
parse_small_condition_clause_gt_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_condition_clause_false
    bcs parse_small_condition_clause_true
    jmp parse_small_condition_clause_false

parse_small_condition_clause_le:
    iny
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_condition_clause_le_ok
    jmp parse_small_condition_clause_at_scan_y_fail
parse_small_condition_clause_le_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_condition_clause_true
    bcc parse_small_condition_clause_true
    jmp parse_small_condition_clause_false

parse_small_condition_clause_ge:
    iny
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_condition_clause_ge_ok
    jmp parse_small_condition_clause_at_scan_y_fail
parse_small_condition_clause_ge_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_condition_clause_true
    bcs parse_small_condition_clause_true
    jmp parse_small_condition_clause_false

parse_small_condition_clause_ne:
    iny
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_condition_clause_ne_ok
    jmp parse_small_condition_clause_at_scan_y_fail
parse_small_condition_clause_ne_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_condition_clause_false
    jmp parse_small_condition_clause_true

parse_small_condition_clause_true:
    lda #$01
    sta expr_value_lo
    clc
    rts

parse_small_condition_clause_false:
    lda #$00
    sta expr_value_lo
    clc
    rts

parse_small_condition_clause_at_scan_y_fail:
    sec
    rts

parse_small_decimal_expr_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_decimal_expr_lhs_ok
    jmp parse_small_decimal_expr_at_scan_y_fail
parse_small_decimal_expr_lhs_ok:
    lda expr_value_lo
    sta expr_compare_lo
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'='
    beq parse_small_decimal_expr_eq
    cmp #'<'
    beq parse_small_decimal_expr_lt_entry
    cmp #'>'
    beq parse_small_decimal_expr_gt_entry
    lda expr_compare_lo
    sta expr_value_lo
    clc
    rts

parse_small_decimal_expr_eq:
    iny
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_decimal_expr_eq_ok
    jmp parse_small_decimal_expr_at_scan_y_fail
parse_small_decimal_expr_eq_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_decimal_expr_eq_true
    jmp parse_small_decimal_expr_false
parse_small_decimal_expr_eq_true:
    jmp parse_small_decimal_expr_true

parse_small_decimal_expr_lt_entry:
    iny
    lda (scan_ptr),y
    cmp #'='
    beq parse_small_decimal_expr_le
    cmp #'>'
    beq parse_small_decimal_expr_ne
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_decimal_expr_lt_ok
    jmp parse_small_decimal_expr_at_scan_y_fail
parse_small_decimal_expr_lt_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    bcc parse_small_decimal_expr_lt_true
    jmp parse_small_decimal_expr_false
parse_small_decimal_expr_lt_true:
    jmp parse_small_decimal_expr_true

parse_small_decimal_expr_gt_entry:
    iny
    lda (scan_ptr),y
    cmp #'='
    beq parse_small_decimal_expr_ge
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_decimal_expr_gt_ok
    jmp parse_small_decimal_expr_at_scan_y_fail
parse_small_decimal_expr_gt_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_decimal_expr_gt_false
    bcs parse_small_decimal_expr_gt_true
    jmp parse_small_decimal_expr_false
parse_small_decimal_expr_gt_true:
    jmp parse_small_decimal_expr_true
parse_small_decimal_expr_gt_false:
    jmp parse_small_decimal_expr_false

parse_small_decimal_expr_le:
    iny
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_decimal_expr_le_ok
    jmp parse_small_decimal_expr_at_scan_y_fail
parse_small_decimal_expr_le_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_decimal_expr_le_true
    bcc parse_small_decimal_expr_le_true
    jmp parse_small_decimal_expr_false
parse_small_decimal_expr_le_true:
    jmp parse_small_decimal_expr_true

parse_small_decimal_expr_ge:
    iny
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_decimal_expr_ge_ok
    jmp parse_small_decimal_expr_at_scan_y_fail
parse_small_decimal_expr_ge_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_decimal_expr_ge_true
    bcs parse_small_decimal_expr_ge_true
    jmp parse_small_decimal_expr_false
parse_small_decimal_expr_ge_true:
    jmp parse_small_decimal_expr_true

parse_small_decimal_expr_ne:
    iny
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_decimal_expr_ne_ok
    jmp parse_small_decimal_expr_at_scan_y_fail
parse_small_decimal_expr_ne_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_decimal_expr_ne_false
    jmp parse_small_decimal_expr_true
parse_small_decimal_expr_ne_false:
    jmp parse_small_decimal_expr_false

parse_small_decimal_expr_done:
    lda expr_compare_lo
    sta expr_value_lo
    clc
    rts

parse_small_decimal_expr_true:
    lda #$01
    sta expr_value_lo
    clc
    rts

parse_small_decimal_expr_false:
    lda #$00
    sta expr_value_lo
    clc
    rts

parse_small_decimal_expr_at_scan_y_fail:
    sec
    rts

parse_small_decimal_sum_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    jsr parse_small_decimal_term_at_scan_y
    bcc :+
    jmp parse_small_decimal_sum_at_scan_y_fail
:   lda expr_value_lo
    sta expr_saved_lo
parse_small_decimal_sum_loop:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'+'
    beq parse_small_decimal_sum_add
    cmp #'-'
    beq parse_small_decimal_sum_sub
    cmp #')'
    beq parse_small_decimal_sum_done
    cmp #']'
    beq parse_small_decimal_sum_done
    cmp #'='
    beq parse_small_decimal_sum_done
    cmp #'<'
    beq parse_small_decimal_sum_done
    cmp #'>'
    beq parse_small_decimal_sum_done
    jsr uppercase_ascii
    cmp #'A'
    beq parse_small_decimal_sum_try_and
    cmp #'O'
    beq parse_small_decimal_sum_try_or
    jmp parse_small_decimal_sum_at_scan_y_fail

parse_small_decimal_sum_try_and:
    sty symbol_start_y_data
    jsr consume_and_keyword_from_scan_y
    bcc :+
    jmp parse_small_decimal_sum_at_scan_y_fail
:   ldy symbol_start_y_data
    jmp parse_small_decimal_sum_done

parse_small_decimal_sum_try_or:
    sty symbol_start_y_data
    jsr consume_or_keyword_from_scan_y
    bcc :+
    jmp parse_small_decimal_sum_at_scan_y_fail
:   ldy symbol_start_y_data
    jmp parse_small_decimal_sum_done

parse_small_decimal_sum_add:
    iny
    jsr parse_small_decimal_term_at_scan_y
    bcc :+
    jmp parse_small_decimal_sum_at_scan_y_fail
:   lda expr_saved_lo
    clc
    adc expr_value_lo
    bcc :+
    jmp parse_small_decimal_sum_at_scan_y_fail
:   sta expr_saved_lo
    jmp parse_small_decimal_sum_loop

parse_small_decimal_sum_sub:
    iny
    jsr parse_small_decimal_term_at_scan_y
    bcc :+
    jmp parse_small_decimal_sum_at_scan_y_fail
:   lda expr_saved_lo
    sec
    sbc expr_value_lo
    bcs :+
    jmp parse_small_decimal_sum_at_scan_y_fail
:   sta expr_saved_lo
    jmp parse_small_decimal_sum_loop

parse_small_decimal_sum_done:
    lda expr_saved_lo
    sta expr_value_lo
    clc
    rts

parse_small_decimal_sum_at_scan_y_fail:
    sec
    rts

parse_small_decimal_term_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    jsr parse_small_decimal_factor_at_scan_y
    bcs parse_small_decimal_term_at_scan_y_fail
    lda expr_value_lo
    sta expr_term_lo
parse_small_decimal_term_loop:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'*'
    beq parse_small_decimal_term_mul
    cmp #'/'
    beq parse_small_decimal_term_div
    lda expr_term_lo
    sta expr_value_lo
    clc
    rts

parse_small_decimal_term_mul:
    iny
    jsr parse_small_decimal_factor_at_scan_y
    bcs parse_small_decimal_term_at_scan_y_fail
    lda expr_term_lo
    sta compare_char
    lda expr_value_lo
    sta hex_work
    lda #$00
    sta expr_term_lo
parse_small_decimal_term_mul_loop:
    lda hex_work
    beq parse_small_decimal_term_loop
    dec hex_work
    lda expr_term_lo
    clc
    adc compare_char
    bcs parse_small_decimal_term_at_scan_y_fail
    sta expr_term_lo
    jmp parse_small_decimal_term_mul_loop

parse_small_decimal_term_div:
    iny
    jsr parse_small_decimal_factor_at_scan_y
    bcs parse_small_decimal_term_at_scan_y_fail
    lda expr_value_lo
    beq parse_small_decimal_term_at_scan_y_fail
    sta hex_work
    lda expr_term_lo
    sta compare_char
    lda #$00
    sta expr_term_lo
parse_small_decimal_term_div_loop:
    lda compare_char
    cmp hex_work
    bcc parse_small_decimal_term_loop
    sec
    sbc hex_work
    sta compare_char
    inc expr_term_lo
    bne parse_small_decimal_term_div_loop

parse_small_decimal_term_at_scan_y_fail:
    sec
    rts

parse_small_decimal_factor_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'('
    beq parse_small_decimal_factor_group
    jmp parse_small_decimal_at_scan_y

parse_small_decimal_factor_group:
    iny
    jsr parse_small_value_expr_at_scan_y
    bcs parse_small_decimal_factor_at_scan_y_fail
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne parse_small_decimal_factor_at_scan_y_fail
    iny
    clc
    rts

parse_small_decimal_factor_at_scan_y_fail:
    sec
    rts

parse_small_decimal_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    lda #$00
    sta expr_value_lo
    sta expr_digit_count
parse_small_decimal_at_scan_y_loop:
    lda (scan_ptr),y
    cmp #'0'
    bcc parse_small_decimal_at_scan_y_done_check
    cmp #'9'+1
    bcs parse_small_decimal_at_scan_y_done_check
    sec
    sbc #'0'
    sta compare_char
    lda expr_value_lo
    sta hex_work
    asl a
    sta truncated_flag
    lda hex_work
    asl a
    asl a
    asl a
    clc
    adc truncated_flag
    bcs parse_small_decimal_at_scan_y_fail
    adc compare_char
    bcs parse_small_decimal_at_scan_y_fail
    sta expr_value_lo
    iny
    inc expr_digit_count
    bne parse_small_decimal_at_scan_y_loop
parse_small_decimal_at_scan_y_done_check:
    lda expr_digit_count
    beq parse_small_decimal_at_scan_y_fail
    clc
    rts
parse_small_decimal_at_scan_y_fail:
    sec
    rts

skip_inline_spaces_at_scan_y:
    lda (scan_ptr),y
    cmp #' '
    beq skip_inline_spaces_at_scan_y_advance
    cmp #9
    beq skip_inline_spaces_at_scan_y_advance
    rts
skip_inline_spaces_at_scan_y_advance:
    iny
    bne skip_inline_spaces_at_scan_y
    rts

compute_payload_layout:
    lda #$00
    sta payload_offset
    sta proc_index
compute_payload_layout_loop:
    ldx proc_index
    cpx export_count_data
    bne :+
    jmp compute_payload_layout_done
:
    lda payload_offset
    sta export_offsets,x
    lda #1
    sta proc_sizes_data,x
    jsr set_body_ptr_from_x
    ldy #$00
compute_payload_layout_body_loop:
    lda (body_ptr),y
    bne :+
    jmp compute_payload_layout_ret
:
    cmp #'c'
    beq compute_payload_layout_add_call
    cmp #'u'
    beq compute_payload_layout_add_call
    cmp #'p'
    beq compute_payload_layout_add_call
    cmp #'s'
    beq compute_payload_layout_add_string
    cmp #'e'
    beq compute_payload_layout_add_string
    cmp #'i'
    bne :+
    jmp compute_payload_layout_add_int
: 
	    cmp #'j'
	    bne :+
	    jmp compute_payload_layout_add_int
: 
		    cmp #'L'
		    bne :+
		    jmp compute_payload_layout_add_single_int_pair
:		    cmp #'S'
		    bne :+
		    jmp compute_payload_layout_add_single_int_pair
:		    cmp #'y'
		    beq compute_payload_layout_add_single_int
	    cmp #'z'
	    beq compute_payload_layout_add_single_int
	    cmp #'h'
	    beq compute_payload_layout_add_single_int
	    cmp #'f'
	    beq compute_payload_layout_add_single_int
	    cmp #'t'
	    beq compute_payload_layout_add_single_int
	    cmp #'w'
	    beq compute_payload_layout_add_single_int
	    cmp #'v'
	    beq compute_payload_layout_add_zero
	    cmp #'d'
	    beq compute_payload_layout_add_zero
	    cmp #'o'
	    beq compute_payload_layout_add_zero
	    cmp #'x'
	    beq compute_payload_layout_add_single_int
	    cmp #'a'
	    beq compute_payload_layout_add_single
    cmp #'m'
    beq compute_payload_layout_add_single
    cmp #'q'
    beq compute_payload_layout_add_single
    cmp #'n'
    beq compute_payload_layout_add_single
    cmp #'l'
    beq compute_payload_layout_add_single
    cmp #'g'
    beq compute_payload_layout_add_single
    cmp #'r'
    beq compute_payload_layout_add_single
    jmp compute_payload_layout_bad
compute_payload_layout_add_call:
    clc
    lda proc_sizes_data,x
    adc #3
    sta proc_sizes_data,x
    iny
    iny
    jmp compute_payload_layout_body_loop
compute_payload_layout_add_string:
    clc
    lda proc_sizes_data,x
    adc #6
    sta proc_sizes_data,x
    iny
    iny
    jmp compute_payload_layout_body_loop
compute_payload_layout_add_single:
    clc
    lda proc_sizes_data,x
    adc #1
    sta proc_sizes_data,x
    iny
    jmp compute_payload_layout_body_loop
compute_payload_layout_add_single_int:
	    clc
	    lda proc_sizes_data,x
	    adc #3
	    sta proc_sizes_data,x
	    iny
	    jmp compute_payload_layout_body_loop
compute_payload_layout_add_single_int_pair:
	    clc
	    lda proc_sizes_data,x
	    adc #3
	    sta proc_sizes_data,x
	    iny
	    iny
	    jmp compute_payload_layout_body_loop
compute_payload_layout_add_zero:
	    iny
	    jmp compute_payload_layout_body_loop
compute_payload_layout_add_int:
    clc
    lda proc_sizes_data,x
    adc #6
    sta proc_sizes_data,x
    iny
    iny
    beq :+
    jmp compute_payload_layout_body_loop
:
compute_payload_layout_ret:
    cpy #$00
    beq :+
    dey
    lda (body_ptr),y
    cmp #'r'
    bne :+
    dec proc_sizes_data,x
:
    clc
    lda payload_offset
    adc proc_sizes_data,x
    sta payload_offset
    inc proc_index
    jmp compute_payload_layout_loop
compute_payload_layout_done:
    ldx #$00
compute_payload_layout_strings_loop:
    cpx string_count_data
    beq compute_payload_layout_done_ok
    lda payload_offset
    sta string_offsets,x
    txa
    pha
    jsr set_string_ptr_from_x
    ldy #$00
compute_payload_layout_string_len_loop:
    lda (body_ptr),y
    beq compute_payload_layout_string_done
    inc payload_offset
    iny
    bne compute_payload_layout_string_len_loop
compute_payload_layout_string_done:
    inc payload_offset
    pla
    tax
    inx
    bne compute_payload_layout_strings_loop
compute_payload_layout_done_ok:
    rts
compute_payload_layout_bad:
    sta compare_char
    lda body_ops_data+0
    sta $C59F
    lda body_ops_data+1
    sta $C5A0
    lda body_ops_data+2
    sta $C5A1
    lda body_ops_data+3
    sta $C5A2
    lda compare_char
    sta actc_trace_byte
    sty $03FC
    stx $03FD
    lda #<msg_bad_call
    ldy #>msg_bad_call
    jmp fail_with_ptr

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
    cmp #EXPORT_MAX
    bcc :+
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_ptr
:   ldx export_count_data
    txa
    pha
    jsr set_export_ptr_from_x
    pla
    tax
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
    cpy #$00
    bne store_proc_export_from_scan_ptr_or_fail_body
    jsr uppercase_symbol_start_valid
    bcc store_proc_export_from_scan_ptr_or_fail_store
    jmp store_proc_export_from_scan_ptr_or_fail_bad
store_proc_export_from_scan_ptr_or_fail_body:
    jsr uppercase_symbol_body_valid
    bcc store_proc_export_from_scan_ptr_or_fail_store
    jmp store_proc_export_from_scan_ptr_or_fail_bad
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
    txa
    pha
    jsr store_proc_params_from_scan_y_for_current_export_or_fail
    pla
    tax
    inc export_count_data
    rts

store_proc_params_from_scan_y_for_current_export_or_fail:
    stx proc_index
    ldx proc_index
    lda #$00
    sta proc_param_count_data,x
    lda var_count_data
    sta proc_param_var_base_data,x
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'('
    beq :+
    clc
    rts
:   iny
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    beq store_proc_params_from_scan_y_for_current_export_done
store_proc_params_from_scan_y_for_current_export_loop:
    jsr copy_symbol_from_scan_y
    bcc :+
    jmp store_proc_export_from_scan_ptr_or_fail_bad
:   sty symbol_end_y_data
    jsr find_module_var_index_from_declared
    bcs :+
    jmp store_proc_export_from_scan_ptr_or_fail_bad
:   ldx proc_index
    jsr find_current_proc_param_index_from_declared_for_proc_x
    bcs :+
    jmp store_proc_export_from_scan_ptr_or_fail_bad
:   ldx var_count_data
    cpx #VAR_MAX
    bcc :+
    jmp store_proc_export_from_scan_ptr_or_fail_bad
:   txa
    pha
    jsr set_var_ptr_from_x
    pla
    tax
    ldy #$00
store_proc_params_from_scan_y_for_current_export_copy_loop:
    lda declared_module_name,y
    sta (export_ptr),y
    beq store_proc_params_from_scan_y_for_current_export_copy_done
    iny
    cpy #25
    bcc store_proc_params_from_scan_y_for_current_export_copy_loop
    jmp store_proc_export_from_scan_ptr_or_fail_bad
store_proc_params_from_scan_y_for_current_export_copy_done:
    lda #$00
    sta var_init_lo,x
    sta var_init_hi,x
    inc var_count_data
    ldx proc_index
    inc proc_param_count_data,x
    ldy symbol_end_y_data
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #','
    beq store_proc_params_from_scan_y_for_current_export_next
    cmp #')'
    beq store_proc_params_from_scan_y_for_current_export_done
    jmp store_proc_export_from_scan_ptr_or_fail_bad
store_proc_params_from_scan_y_for_current_export_next:
    iny
    jsr skip_inline_spaces_at_scan_y
    jmp store_proc_params_from_scan_y_for_current_export_loop
store_proc_params_from_scan_y_for_current_export_done:
    clc
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

set_var_ptr_from_x:
    lda #<var_names
    sta export_ptr
    lda #>var_names
    sta export_ptr+1
set_var_ptr_from_x_loop:
    cpx #$00
    beq set_var_ptr_from_x_done
    clc
    lda export_ptr
    adc #25
    sta export_ptr
    lda export_ptr+1
    adc #$00
    sta export_ptr+1
    dex
    bne set_var_ptr_from_x_loop
set_var_ptr_from_x_done:
    rts

copy_symbol_from_scan_ptr:
    ldy #$00
copy_symbol_from_scan_ptr_loop:
    lda (scan_ptr),y
    beq copy_symbol_from_scan_ptr_done
    jsr uppercase_ascii
    cpy #$00
    bne copy_symbol_from_scan_ptr_body
    jsr uppercase_symbol_start_valid
    bcc copy_symbol_from_scan_ptr_store
    jmp copy_symbol_from_scan_ptr_done
copy_symbol_from_scan_ptr_body:
    jsr uppercase_symbol_body_valid
    bcc copy_symbol_from_scan_ptr_store
    jmp copy_symbol_from_scan_ptr_done
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

copy_symbol_from_scan_y:
    txa
    pha
    ldx #$00
copy_symbol_from_scan_y_loop:
    lda (scan_ptr),y
    beq copy_symbol_from_scan_y_done_check
    jsr uppercase_ascii
    cpx #$00
    bne copy_symbol_from_scan_y_body
    jsr uppercase_symbol_start_valid
    bcc copy_symbol_from_scan_y_store
    jmp copy_symbol_from_scan_y_done_check
copy_symbol_from_scan_y_body:
    jsr uppercase_symbol_body_valid
    bcc copy_symbol_from_scan_y_store
    jmp copy_symbol_from_scan_y_done_check
copy_symbol_from_scan_y_store:
    sta declared_module_name,x
    iny
    inx
    cpx #24
    bcc copy_symbol_from_scan_y_loop
copy_symbol_from_scan_y_fail:
    pla
    tax
    sec
    rts
copy_symbol_from_scan_y_done_check:
    cpx #$00
    beq copy_symbol_from_scan_y_fail
    lda #$00
    sta declared_module_name,x
    pla
    tax
    clc
    rts

consume_and_keyword_from_scan_y:
    lda #<pattern_and
    sta const_ptr
    lda #>pattern_and
    sta const_ptr+1
    jmp consume_keyword_from_scan_y

consume_or_keyword_from_scan_y:
    lda #<pattern_or
    sta const_ptr
    lda #>pattern_or
    sta const_ptr+1
    jmp consume_keyword_from_scan_y

consume_not_keyword_from_scan_y:
    lda #<pattern_not
    sta const_ptr
    lda #>pattern_not
    sta const_ptr+1

consume_keyword_from_scan_y:
    sty hex_work
    jsr skip_inline_spaces_at_scan_y
    jsr copy_symbol_from_scan_y
    bcc :+
    ldy hex_work
    sec
    rts
:   sty compare_char
    jsr symbol_buffer_matches_const_ptr
    bcc :+
    ldy hex_work
    sec
    rts
:   ldy compare_char
    clc
    rts

symbol_buffer_matches_const_ptr:
    ldy #$00
symbol_buffer_matches_const_ptr_loop:
    lda (const_ptr),y
    cmp declared_module_name,y
    bne symbol_buffer_matches_const_ptr_fail
    lda declared_module_name,y
    beq symbol_buffer_matches_const_ptr_done
    iny
    bne symbol_buffer_matches_const_ptr_loop
symbol_buffer_matches_const_ptr_fail:
    sec
    rts
symbol_buffer_matches_const_ptr_done:
    clc
    rts

find_var_index_from_scan_y:
    sty symbol_start_y_data
    jsr copy_symbol_from_scan_y
    bcc :+
    ldy symbol_start_y_data
    sec
    rts
:   sty symbol_end_y_data
    jsr find_var_index_from_declared
    bcc :+
    ldy symbol_start_y_data
    sec
    rts
:   ldy symbol_end_y_data
    clc
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

find_var_index_from_declared:
    lda current_proc_index_data
    cmp #$FF
    beq find_module_var_index_from_declared
    tax
    jsr find_current_proc_local_index_from_declared_for_proc_x
    bcc find_var_index_from_declared_done
    ldx current_proc_index_data
    jsr find_current_proc_param_index_from_declared_for_proc_x
    bcs find_module_var_index_from_declared
    clc
    rts

find_module_var_index_from_declared:
    ldx #$00
find_module_var_index_from_declared_loop:
    cpx module_var_count_data
    beq find_var_index_from_declared_fail
    stx hex_work
    jsr set_var_ptr_from_x
    ldx hex_work
    ldy #$00
find_module_var_index_from_declared_compare_loop:
    lda (export_ptr),y
    cmp declared_module_name,y
    bne find_module_var_index_from_declared_next
    lda declared_module_name,y
    beq find_var_index_from_declared_done
    iny
    bne find_module_var_index_from_declared_compare_loop
find_module_var_index_from_declared_next:
    inx
    bne find_module_var_index_from_declared_loop
find_var_index_from_declared_fail:
    sec
    rts
find_var_index_from_declared_done:
    clc
    rts

find_current_proc_param_index_from_declared_for_proc_x:
    stx proc_index
    lda proc_param_count_data,x
    beq find_current_proc_param_index_from_declared_for_proc_x_fail
    lda proc_param_var_base_data,x
    sta hex_work
find_current_proc_param_index_from_declared_for_proc_x_loop:
    ldx proc_index
    lda proc_param_var_base_data,x
    clc
    adc proc_param_count_data,x
    sta compare_char
    ldx hex_work
    cpx compare_char
    beq find_current_proc_param_index_from_declared_for_proc_x_fail
    stx hex_work
    jsr set_var_ptr_from_x
    ldx hex_work
    ldy #$00
find_current_proc_param_index_from_declared_for_proc_x_compare_loop:
    lda (export_ptr),y
    cmp declared_module_name,y
    bne find_current_proc_param_index_from_declared_for_proc_x_next
    lda declared_module_name,y
    beq find_var_index_from_declared_done
    iny
    bne find_current_proc_param_index_from_declared_for_proc_x_compare_loop
find_current_proc_param_index_from_declared_for_proc_x_next:
    inc hex_work
    jmp find_current_proc_param_index_from_declared_for_proc_x_loop
find_current_proc_param_index_from_declared_for_proc_x_fail:
    sec
    rts

find_current_proc_local_index_from_declared_for_proc_x:
    stx proc_index
    lda proc_local_count_data,x
    beq find_current_proc_local_index_from_declared_for_proc_x_fail
    lda proc_local_var_base_data,x
    sta hex_work
find_current_proc_local_index_from_declared_for_proc_x_loop:
    ldx proc_index
    lda proc_local_var_base_data,x
    clc
    adc proc_local_count_data,x
    sta compare_char
    ldx hex_work
    cpx compare_char
    beq find_current_proc_local_index_from_declared_for_proc_x_fail
    stx hex_work
    jsr set_var_ptr_from_x
    ldx hex_work
    ldy #$00
find_current_proc_local_index_from_declared_for_proc_x_compare_loop:
    lda (export_ptr),y
    cmp declared_module_name,y
    bne find_current_proc_local_index_from_declared_for_proc_x_next
    lda declared_module_name,y
    beq find_var_index_from_declared_done
    iny
    bne find_current_proc_local_index_from_declared_for_proc_x_compare_loop
find_current_proc_local_index_from_declared_for_proc_x_next:
    inc hex_work
    jmp find_current_proc_local_index_from_declared_for_proc_x_loop
find_current_proc_local_index_from_declared_for_proc_x_fail:
    sec
    rts

find_or_store_external_from_declared:
    ldx #$00
find_or_store_external_from_declared_loop:
    cpx extern_count_data
    beq find_or_store_external_from_declared_add
    stx hex_work
    jsr set_external_ptr_from_x
    ldx hex_work
    ldy #$00
find_or_store_external_from_declared_compare_loop:
    lda (export_ptr),y
    cmp declared_module_name,y
    bne find_or_store_external_from_declared_next
    lda declared_module_name,y
    beq find_or_store_external_from_declared_done
    iny
    bne find_or_store_external_from_declared_compare_loop
find_or_store_external_from_declared_next:
    inx
    bne find_or_store_external_from_declared_loop
find_or_store_external_from_declared_add:
    ldx extern_count_data
    cpx #EXTERNAL_MAX
    bcc :+
    sec
    rts
:   txa
    pha
    jsr set_external_ptr_from_x
    pla
    tax
    ldy #$00
find_or_store_external_from_declared_copy_loop:
    lda declared_module_name,y
    sta (export_ptr),y
    beq find_or_store_external_from_declared_copy_done
    iny
    cpy #25
    bcc find_or_store_external_from_declared_copy_loop
    sec
    rts
find_or_store_external_from_declared_copy_done:
    inc extern_count_data
find_or_store_external_from_declared_done:
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

pattern_matches_scan_ptr_keyword:
    jsr pattern_matches_scan_ptr
    bcc :+
    sec
    rts
:   ldy #$00
pattern_matches_scan_ptr_keyword_len_loop:
    lda (const_ptr),y
    beq pattern_matches_scan_ptr_keyword_boundary
    iny
    bne pattern_matches_scan_ptr_keyword_len_loop
pattern_matches_scan_ptr_keyword_boundary:
    lda (scan_ptr),y
    beq pattern_matches_scan_ptr_keyword_ok
    cmp #' '
    beq pattern_matches_scan_ptr_keyword_ok
    cmp #9
    beq pattern_matches_scan_ptr_keyword_ok
    cmp #10
    beq pattern_matches_scan_ptr_keyword_ok
    cmp #13
    beq pattern_matches_scan_ptr_keyword_ok
    sec
    rts
pattern_matches_scan_ptr_keyword_ok:
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

    lda #<avo_header
    sta const_ptr
    lda #>avo_header
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_export_list
    jsr append_body_ops_list
    jsr append_external_list
    jsr append_string_list
    jsr append_int_list
    jsr append_var_list
    lda #'k'
    jsr append_char
    lda #' '
    jsr append_char
    lda import_flags_lo
    jsr append_small_decimal
    jsr append_newline
    lda #'n'
    jsr append_char
    lda #' '
    jsr append_char
    jsr append_module_symbol_lower
    jsr append_newline

    lda #$00
    jmp append_char

append_export_list:
    lda #$00
    sta export_index
append_export_list_loop:
    ldx export_index
    cpx export_count_data
    beq append_export_list_done
    lda #'x'
    jsr append_char
    lda #' '
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
    lda #' '
    jsr append_char
    ldx export_index
    lda export_offsets,x
    jsr append_small_decimal
    lda #' '
    jsr append_char
    ldx export_index
    lda proc_sizes_data,x
    jsr append_small_decimal
    jsr append_newline
    inc export_index
    jmp append_export_list_loop
append_export_list_done:
    rts

append_body_ops_list:
    lda #$00
    sta proc_index
append_body_ops_list_proc_loop:
    ldx proc_index
    cpx export_count_data
    beq append_body_ops_list_done
    lda #'b'
    jsr append_char
    lda #' '
    jsr append_char
    ldx proc_index
    jsr set_body_ptr_from_x
    ldy #$00
append_body_ops_list_body_loop:
    lda (body_ptr),y
    beq append_body_ops_list_ret
    jsr append_char
    iny
    bne append_body_ops_list_body_loop
append_body_ops_list_ret:
    cpy #$00
    beq append_body_ops_list_emit_ret
    dey
    lda (body_ptr),y
    cmp #'r'
    beq append_body_ops_list_newline
    iny
append_body_ops_list_emit_ret:
    lda #'r'
    jsr append_char
append_body_ops_list_newline:
    jsr append_newline
    inc proc_index
    jmp append_body_ops_list_proc_loop
append_body_ops_list_done:
    rts

append_external_list:
    lda #$00
    sta proc_index
append_external_list_loop:
    ldx proc_index
    cpx extern_count_data
    beq append_external_list_done
    lda #'u'
    jsr append_char
    lda #' '
    jsr append_char
    ldx proc_index
    jsr set_external_ptr_from_x
    ldy #$00
append_external_list_value_loop:
    lda (export_ptr),y
    beq append_external_list_value_done
    jsr lowercase_ascii
    jsr append_char
    iny
    bne append_external_list_value_loop
append_external_list_value_done:
    jsr append_newline
    inc proc_index
    jmp append_external_list_loop
append_external_list_done:
    rts

append_string_list:
    lda #$00
    sta proc_index
append_string_list_loop:
    ldx proc_index
    cpx string_count_data
    beq append_string_list_done
    lda #'s'
    jsr append_char
    lda #' '
    jsr append_char
    ldx proc_index
    jsr set_string_ptr_from_x
    ldy #$00
append_string_list_value_loop:
    lda (body_ptr),y
    beq append_string_list_value_done
    jsr append_char
    iny
    bne append_string_list_value_loop
append_string_list_value_done:
    jsr append_newline
    inc proc_index
    jmp append_string_list_loop
append_string_list_done:
    rts

append_int_list:
    lda #$00
    sta proc_index
append_int_list_loop:
    ldx proc_index
    cpx int_count_data
    beq append_int_list_done
    lda #'i'
    jsr append_char
    lda #' '
    jsr append_char
    ldx proc_index
    lda int_values_hi,x
    bne append_int_list_bad
    lda int_values_lo,x
    jsr append_small_decimal
    jsr append_newline
    inc proc_index
    jmp append_int_list_loop
append_int_list_bad:
    lda #<msg_bad_literal
    ldy #>msg_bad_literal
    jmp fail_with_ptr
append_int_list_done:
    rts

append_var_list:
    lda #$00
    sta proc_index
append_var_list_loop:
    ldx proc_index
    cpx var_count_data
    beq append_var_list_done
    lda #'v'
    jsr append_char
    lda #' '
    jsr append_char
    ldx proc_index
    jsr set_var_ptr_from_x
    ldy #$00
append_var_list_name_loop:
    lda (export_ptr),y
    beq append_var_list_name_done
    jsr lowercase_ascii
    jsr append_char
    iny
    bne append_var_list_name_loop
append_var_list_name_done:
    lda #' '
    jsr append_char
    ldx proc_index
    lda var_init_hi,x
    bne append_var_list_bad
    lda var_init_lo,x
    jsr append_small_decimal
    jsr append_newline
    inc proc_index
    jmp append_var_list_loop
append_var_list_bad:
    lda #<msg_bad_var
    ldy #>msg_bad_var
    jmp fail_with_ptr
append_var_list_done:
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

append_newline:
    lda #10
    jmp append_char

append_small_decimal:
    ldx #$00
append_small_decimal_hundreds_loop:
    cmp #100
    bcc append_small_decimal_tens_prep
    sec
    sbc #100
    inx
    bne append_small_decimal_hundreds_loop
append_small_decimal_tens_prep:
    stx compare_char
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
    pha
    lda compare_char
    beq append_small_decimal_emit_tens
    clc
    adc #'0'
    jsr append_char
append_small_decimal_emit_tens:
    pla
    bne :+
    lda compare_char
    beq append_small_decimal_ones_pop
    lda #$00
: 
    clc
    adc #'0'
    jsr append_char
append_small_decimal_ones_pop:
    pla
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
msg_bad_var:
    .asciiz "BAD VAR"
msg_bad_call:
    .asciiz "BAD CALL"
msg_bad_literal:
    .asciiz "BAD LITERAL"
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
module_name:
    .res 25

pattern_module:
    .asciiz "MODULE"
pattern_int_decl:
    .asciiz "INT"
pattern_proc:
    .asciiz "PROC"
pattern_if:
    .asciiz "IF"
pattern_while:
    .asciiz "WHILE"
pattern_do:
    .asciiz "DO"
pattern_od:
    .asciiz "OD"
pattern_until:
    .asciiz "UNTIL"
pattern_and:
    .asciiz "AND"
pattern_or:
    .asciiz "OR"
pattern_not:
    .asciiz "NOT"
pattern_else:
    .asciiz "ELSE"
pattern_fi:
    .asciiz "FI"
pattern_endif:
    .asciiz "ENDIF"
pattern_return:
    .asciiz "RETURN"
pattern_print_quote:
    .byte "PRINT(",34,0
pattern_printe_quote:
    .byte "PRINTE(",34,0
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

avo_header:
    .byte "AVO1",10,0

target_path:
    .res 40
source_buffer:
    .res SOURCE_LIMIT+1
body_ops_data:
    .res BODY_OPS_STRIDE * EXPORT_MAX
string_literals:
    .res 24 * STRING_LITERAL_MAX
int_values_lo:
    .res INT_LITERAL_MAX
int_values_hi:
    .res INT_LITERAL_MAX
var_init_lo:
    .res VAR_MAX
var_init_hi:
    .res VAR_MAX
export_offsets:
    .res EXPORT_MAX
proc_sizes_data:
    .res EXPORT_MAX
string_offsets:
    .res STRING_LITERAL_MAX

.segment "BSS"

declared_module_name:
    .res 25
saved_var_name_data:
    .res 25
manifest_entry:
    .res 32
content_buffer:
    .res 640
manifest_buffer:
    .res MANIFEST_LIMIT+1
export_count_data:
    .res 1
string_count_data:
    .res 1
int_count_data:
    .res 1
var_count_data:
    .res 1
module_var_count_data:
    .res 1
current_proc_index_data:
    .res 1
extern_count_data:
    .res 1
proc_param_count_data:
    .res EXPORT_MAX
proc_param_var_base_data:
    .res EXPORT_MAX
proc_local_count_data:
    .res EXPORT_MAX
proc_local_var_base_data:
    .res EXPORT_MAX
loop_depth_data:
    .res 1
loop_kind_stack:
    .res LOOP_MAX
expr_saved_lo:
    .res 1
expr_compare_lo:
    .res 1
expr_runtime_op:
    .res 1
expr_runtime_post_zero:
    .res 1
expr_term_lo:
    .res 1
expr_print_op:
    .res 1
expr_value_lo:
    .res 1
expr_digit_count:
    .res 1
compare_char:
    .res 1
actc_trace_byte:
    .res 1
save_stack_top:
    .res 1
call_target_kind:
    .res 1
call_target_index_data:
    .res 1
call_expected_arg_count:
    .res 1
call_arg_count_data:
    .res 1
param_bind_count_data:
    .res 1
param_bind_base_data:
    .res 1
symbol_start_y_data:
    .res 1
symbol_end_y_data:
    .res 1
assignment_target_index_data:
    .res 1
bool_ops_used_data:
    .res 1
hex_work:
    .res 1
export_names:
    .res 25 * EXPORT_MAX
external_names:
    .res 25 * EXTERNAL_MAX
var_names:
    .res 25 * VAR_MAX
bss_end:
