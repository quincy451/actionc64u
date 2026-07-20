; Native lowering for local-control integer bodies. Procedures are emitted in
; one machine record with MAIN first, followed by helpers in reverse declaration
; order. Named exports carry local calls and control-flow relocations. The pass
; also owns single-procedure local-control bodies that the older native pass
; cannot lower.

NATIVE_LOCAL_PROC_MAX = 9
NATIVE_LOCAL_CONTROL_MAX = 4
NATIVE_LOCAL_LABEL_MAX = 8
NATIVE_LOCAL_CONTROL_IF = 1
NATIVE_LOCAL_CONTROL_DO = 2
NATIVE_LOCAL_CONTROL_WHILE = 3
NATIVE_LOCAL_USE_MUL = $01
NATIVE_LOCAL_USE_DIV = $02
NATIVE_LOCAL_USE_PRINT = $04

.ifndef ACTC_NATIVE_LOCAL_RUNTIME_ARGS
ACTC_NATIVE_LOCAL_RUNTIME_ARGS = 0
.endif
.ifndef ACTC_NATIVE_LOCAL_ASMBLOCK
ACTC_NATIVE_LOCAL_ASMBLOCK = 0
.endif
.ifndef ACTC_NATIVE_LOCAL_PARAM_BINDS
ACTC_NATIVE_LOCAL_PARAM_BINDS = ACTC_NATIVE_LOCAL_ASMBLOCK
.endif

.ifndef ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
ACTC_NATIVE_LOCAL_MACHINE_ROUTINES = 0
.endif
.ifndef ACTC_NATIVE_LOCAL_FIXED_ROUTINES
ACTC_NATIVE_LOCAL_FIXED_ROUTINES = 0
.endif
.if ACTC_NATIVE_LOCAL_ASMBLOCK
; Pass-9 runtime scratch follows the external assembly page workspace.
native_local_asmblock_count = ACTC_ASMBLOCK_PASS9_SCRATCH+0
native_local_asmblock_index = ACTC_ASMBLOCK_PASS9_SCRATCH+1
native_local_asm_label_index = ACTC_ASMBLOCK_PASS9_SCRATCH+2
native_local_asm_var_index = ACTC_ASMBLOCK_PASS9_SCRATCH+3
native_local_asm_reloc_index = ACTC_ASMBLOCK_PASS9_SCRATCH+4
native_local_asm_plain_count = ACTC_ASMBLOCK_PASS9_SCRATCH+5
.endif
.if ACTC_NATIVE_LOCAL_PARAM_BINDS
native_local_param_bind_phase = ACTC_ASMBLOCK_PASS9_SCRATCH+6
.endif
.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
native_local_current_machine = ACTC_ASMBLOCK_PASS9_SCRATCH+7
native_local_machine_meta = ACTC_ASMBLOCK_PASS9_SCRATCH+8
native_local_machine_param_count = ACTC_ASMBLOCK_PASS9_SCRATCH+9
native_local_machine_param_base = ACTC_ASMBLOCK_PASS9_SCRATCH+10
native_local_machine_param_index = ACTC_ASMBLOCK_PASS9_SCRATCH+11
native_local_machine_byte_count = ACTC_ASMBLOCK_PASS9_SCRATCH+12
native_local_machine_byte_pos = ACTC_ASMBLOCK_PASS9_SCRATCH+13
native_local_machine_setup_size = ACTC_ASMBLOCK_PASS9_SCRATCH+14
.endif

; Use these only when a direct conditional branch cannot reach its target.
.macro NATIVE_LOCAL_JEQ target
    bne :+
    jmp target
:
.endmacro

.macro NATIVE_LOCAL_JNE target
    beq :+
    jmp target
:
.endmacro

.macro NATIVE_LOCAL_JCC target
    bcs :+
    jmp target
:
.endmacro

.macro NATIVE_LOCAL_JCS target
    bcc :+
    jmp target
:
.endmacro

native_local_object_no_near:
    jmp native_local_object_no
is_main_native_integer_machine_object:
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$01
    bcc native_local_object_no_near
    cmp #NATIVE_LOCAL_PROC_MAX+1
    bcs native_local_object_no_near
    sta native_local_proc_count
    sec
    sbc #$01
    sta native_local_main_proc

    lda #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    jsr load_context_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcc native_local_object_no_near
    ldx native_local_main_proc
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcc native_local_object_no_near

    lda #ACTC_OVERLAY_CTX_STRING_COUNT_PTR_LO
    jsr load_count_from_context
    bne native_local_object_no_near

    jsr native_local_find_helper_indices
    jsr native_local_compute_data_size
    bcc native_local_object_no_near
.if ACTC_NATIVE_LOCAL_ASMBLOCK
    jsr native_local_init_asmblocks
.endif
    jsr native_local_count_debug_ops
    bcc native_local_object_no_near

    lda #$00
    sta native_local_total_code_lo
    sta native_local_total_code_hi
    sta native_local_debug_count
    sta native_local_used_helpers
.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
    sta native_local_runtime_arg_seen
.endif
    lda #$01
    sta native_local_record_debug
    lda native_local_main_proc
    sta native_local_current_proc
native_local_layout_loop:
    ldx native_local_current_proc
    lda native_local_total_code_lo
    sta native_local_proc_offset_lo,x
    lda native_local_total_code_hi
    sta native_local_proc_offset_hi,x
    lda native_local_debug_count
    sta native_local_proc_debug_base,x
    jsr native_local_analyze_current_proc
    bcc native_local_object_no
    ldx native_local_current_proc
    lda native_local_label_count
    sta native_local_proc_label_count,x
    sec
    lda native_local_code_size_lo
    sbc native_local_proc_offset_lo,x
    sta native_local_proc_size_lo,x
    lda native_local_code_size_hi
    sbc native_local_proc_offset_hi,x
    sta native_local_proc_size_hi,x
    lda native_local_code_size_lo
    sta native_local_total_code_lo
    lda native_local_code_size_hi
    sta native_local_total_code_hi
    lda native_local_current_proc
    beq native_local_layout_done
    dec native_local_current_proc
    jmp native_local_layout_loop
native_local_layout_done:
    lda native_local_debug_count
    cmp native_local_expected_debug_count
    bne native_local_object_no
    lda native_local_proc_count
    cmp #$01
    bne native_local_layout_applicable
    lda native_local_arithmetic_seen
    beq :+
    lda native_local_while_seen
    beq native_local_object_no
:
    lda native_local_single_proc_applicable
    beq native_local_object_no
native_local_layout_applicable:
.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
    lda native_local_runtime_arg_seen
    beq native_local_object_no
.endif
.if ACTC_EMIT_NATIVE_LOCAL_MIXED_ONLY
    lda native_local_asmblock_count
    beq native_local_object_no
.endif
    jsr native_local_compute_root_size
    sec
    rts
native_local_object_no:
    clc
    rts

native_local_count_debug_ops:
    lda #$00
    sta native_local_expected_debug_count
    ldx #$00
native_local_count_debug_ops_loop:
    cpx native_local_proc_count
    beq native_local_count_debug_ops_done
    lda #ACTC_OVERLAY_CTX_BODY_DEBUG_COUNT_PTR_LO
    jsr load_indexed_byte_from_context_ptr
    clc
    adc native_local_expected_debug_count
    bcs native_local_count_debug_ops_bad
    cmp #ACTC_OVERLAY_BODY_OP_LIMIT+1
    bcs native_local_count_debug_ops_bad
    sta native_local_expected_debug_count
    inx
    jmp native_local_count_debug_ops_loop
native_local_count_debug_ops_done:
    sec
    rts
native_local_count_debug_ops_bad:
    clc
    rts

native_local_compute_data_size:
    lda #$00
    sta native_local_data_size_lo
    sta native_local_data_size_hi
    sta entry_index_data
native_local_compute_data_size_loop:
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq native_local_compute_data_size_done
    ldx entry_index_data
    jsr native_local_load_var_width_x
    cmp #$02
    beq :+
    cmp #$04
    bne native_local_compute_data_size_bad
:   clc
    adc native_local_data_size_lo
    sta native_local_data_size_lo
    bcc :+
    inc native_local_data_size_hi
:   inc entry_index_data
    jmp native_local_compute_data_size_loop
native_local_compute_data_size_done:
    sec
    rts
native_local_compute_data_size_bad:
    clc
    rts

native_local_compute_root_size:
    clc
    lda native_local_total_code_lo
    adc native_local_data_size_lo
    sta native_local_root_size_lo
    lda native_local_total_code_hi
    adc native_local_data_size_hi
    sta native_local_root_size_hi
    lda native_local_data_size_lo
    ora native_local_data_size_hi
    beq native_local_compute_root_size_done
    clc
    lda native_local_root_size_lo
    adc #$02
    sta native_local_root_size_lo
    bcc native_local_compute_root_size_done
    inc native_local_root_size_hi
native_local_compute_root_size_done:
    rts

native_local_analyze_current_proc:
    lda #$00
    sta native_local_stack_depth
    sta native_local_control_depth
    sta native_local_label_count
    sta native_local_lowering_seen
    sta native_local_single_proc_applicable
    sta native_local_arithmetic_seen
    sta native_local_while_seen
    sta native_local_body_pos
.if ACTC_NATIVE_LOCAL_PARAM_BINDS
    lda #$01
    sta native_local_param_bind_phase
.endif
    ldx native_local_current_proc
    lda native_local_proc_offset_lo,x
    sta native_local_code_size_lo
    lda native_local_proc_offset_hi,x
    sta native_local_code_size_hi
    cpx native_local_main_proc
    bne native_local_analyze_select_body
    lda native_local_data_size_lo
    ora native_local_data_size_hi
    beq native_local_analyze_select_body
    lda #13
    jsr native_local_add_code_size
native_local_analyze_select_body:
    ldx native_local_current_proc
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
    jsr native_local_load_current_machine
.endif
native_local_analyze_loop:
    ldy native_local_body_pos
    jsr emit_object_peek_payload_y
.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
    ldx native_local_current_machine
    beq native_local_analyze_normal_op
    cmp #$00
    beq native_local_analyze_machine_done
    cmp #'@'
    beq native_local_analyze_normal_op
    clc
    rts
native_local_analyze_normal_op:
.endif
    pha
    jsr native_local_record_debug_offset
    pla
.if ACTC_NATIVE_LOCAL_PARAM_BINDS
    cmp #'S'
    NATIVE_LOCAL_JEQ native_local_analyze_store
    ldx #$00
    stx native_local_param_bind_phase
.endif
    jsr native_local_classify_body_op
    bcs :+
    rts
:
    lda native_local_analyze_target_lo,x
    sta ACTC_OVERLAY_WORK_ZP
    lda native_local_analyze_target_hi,x
    sta ACTC_OVERLAY_WORK_ZP+1
    jmp (ACTC_OVERLAY_WORK_ZP)

native_local_analyze_target_lo:
    .byte <native_local_analyze_compare_found,<native_local_analyze_compare_found
    .byte <native_local_analyze_compare_found,<native_local_analyze_compare_found
    .byte <native_local_analyze_literal,<native_local_analyze_load,<native_local_analyze_store
    .byte <native_local_analyze_add_sub,<native_local_analyze_add_sub
    .byte <native_local_analyze_mul,<native_local_analyze_div
    .byte <native_local_analyze_print,<native_local_analyze_print_line
.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
    .byte <native_local_analyze_external_a_call,<native_local_analyze_external_xy_call
.endif
    .byte <native_local_analyze_external_call
.if ACTC_NATIVE_LOCAL_FIXED_ROUTINES
    .byte <native_local_analyze_fixed_call
.endif
.if ACTC_NATIVE_LOCAL_ASMBLOCK
    .byte <native_local_analyze_asmblock
.endif
    .byte <native_local_analyze_do,<native_local_analyze_else,<native_local_analyze_endif
    .byte <native_local_analyze_while_end,<native_local_analyze_od
    .byte <native_local_analyze_exit,<native_local_analyze_call,<native_local_analyze_return
native_local_analyze_target_hi:
    .byte >native_local_analyze_compare_found,>native_local_analyze_compare_found
    .byte >native_local_analyze_compare_found,>native_local_analyze_compare_found
    .byte >native_local_analyze_literal,>native_local_analyze_load,>native_local_analyze_store
    .byte >native_local_analyze_add_sub,>native_local_analyze_add_sub
    .byte >native_local_analyze_mul,>native_local_analyze_div
    .byte >native_local_analyze_print,>native_local_analyze_print_line
.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
    .byte >native_local_analyze_external_a_call,>native_local_analyze_external_xy_call
.endif
    .byte >native_local_analyze_external_call
.if ACTC_NATIVE_LOCAL_FIXED_ROUTINES
    .byte >native_local_analyze_fixed_call
.endif
.if ACTC_NATIVE_LOCAL_ASMBLOCK
    .byte >native_local_analyze_asmblock
.endif
    .byte >native_local_analyze_do,>native_local_analyze_else,>native_local_analyze_endif
    .byte >native_local_analyze_while_end,>native_local_analyze_od
    .byte >native_local_analyze_exit,>native_local_analyze_call,>native_local_analyze_return
native_local_analyze_target_end:

.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
native_local_analyze_machine_done:
    lda native_local_current_machine
    beq native_local_analyze_bad_near_load
    ldx native_local_current_proc
    cpx native_local_main_proc
    beq native_local_analyze_bad_near_load
    lda native_local_stack_depth
    ora native_local_control_depth
    bne native_local_analyze_bad_near_load
    lda native_local_lowering_seen
    beq native_local_analyze_bad_near_load
    sec
    rts
.endif

native_local_analyze_compare_found:
    lda native_local_compare_size_table,x
    sta native_local_instruction_size
    txa
    and #$02
    sta native_local_compare_ordered
    jmp native_local_analyze_compare

native_local_analyze_literal:
    jsr native_local_read_selector
    bcc native_local_analyze_bad_near_load
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp native_local_operand_index
    beq native_local_analyze_bad_near_load
    bcc native_local_analyze_bad_near_load
    jsr native_local_push
    bcc native_local_analyze_bad_near_load
    lda #$06
    jsr native_local_add_code_size
    jmp native_local_analyze_mark

native_local_analyze_bad_near_load:
    jmp native_local_analyze_bad
native_local_analyze_load:
    jsr native_local_read_selector
    bcc native_local_analyze_bad_near_load
    lda native_local_operand_index
    jsr native_local_word_var_offset
    bcc native_local_analyze_bad_near_load
    jsr native_local_push
    bcc native_local_analyze_bad_near_load
    lda #$09
    jsr native_local_add_code_size
    jmp native_local_analyze_mark

native_local_analyze_store:
    jsr native_local_read_selector
    bcc native_local_analyze_bad_near_load
    lda native_local_operand_index
    jsr native_local_word_var_offset
    bcc native_local_analyze_bad_near_load
    lda native_local_stack_depth
    bne native_local_analyze_store_value
.if ACTC_NATIVE_LOCAL_PARAM_BINDS
    lda native_local_param_bind_phase
    beq native_local_analyze_bad_near_load
    jsr native_local_param_bind_size
    jsr native_local_add_code_size
    jmp native_local_analyze_mark
.else
    jmp native_local_analyze_bad
.endif
native_local_analyze_store_value:
    dec native_local_stack_depth
    lda #11
    jsr native_local_add_code_size
    jmp native_local_analyze_mark

.if ACTC_NATIVE_LOCAL_PARAM_BINDS
native_local_param_bind_size:
    lda #$09
    sta native_local_instruction_size
    lda native_local_param_bind_phase
    cmp #$01
    bne :+
    inc native_local_param_bind_phase
    lda #$0E
    sta native_local_instruction_size
:
    ldy native_local_body_pos
    jsr emit_object_peek_payload_y
    cmp #'S'
    beq :+
    lda #$00
    sta native_local_param_bind_phase
    lda native_local_instruction_size
    clc
    adc #$05
    rts
:
    lda native_local_instruction_size
    rts
.endif

native_local_analyze_add_sub:
    lda #19
native_local_analyze_binary:
    sta native_local_instruction_size
    lda native_local_stack_depth
    cmp #$02
    bcc native_local_analyze_bad_near_external
    dec native_local_stack_depth
    lda #$01
    sta native_local_arithmetic_seen
    inc native_local_body_pos
    lda native_local_instruction_size
    jsr native_local_add_code_size
    jmp native_local_analyze_mark_no_advance

native_local_analyze_mul:
    lda native_local_mul_index
    cmp #$FF
    beq native_local_analyze_bad_near_external
    lda native_local_used_helpers
    ora #NATIVE_LOCAL_USE_MUL
    sta native_local_used_helpers
    lda #23
    bne native_local_analyze_binary

native_local_analyze_div:
    lda native_local_div_index
    cmp #$FF
    beq native_local_analyze_bad_near_external
    lda native_local_used_helpers
    ora #NATIVE_LOCAL_USE_DIV
    sta native_local_used_helpers
    lda #23
    bne native_local_analyze_binary

native_local_analyze_print:
    lda #6
    bne native_local_analyze_print_common
native_local_analyze_print_line:
    lda #11
native_local_analyze_print_common:
    sta native_local_instruction_size
    lda native_local_print_index
    cmp #$FF
    beq native_local_analyze_bad_near_external
    jsr native_local_pop
    bcc native_local_analyze_bad_near_external
    lda native_local_used_helpers
    ora #NATIVE_LOCAL_USE_PRINT
    sta native_local_used_helpers
    inc native_local_body_pos
    lda native_local_instruction_size
    jsr native_local_add_code_size
    jmp native_local_analyze_mark_no_advance

native_local_analyze_bad_near_external:
    jmp native_local_analyze_bad
native_local_analyze_external_call:
.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
    lda #$00
    beq native_local_analyze_external_common
native_local_analyze_external_a_call:
    lda #$05
    bne native_local_analyze_external_common
native_local_analyze_external_xy_call:
    lda #$07
native_local_analyze_external_common:
    sta native_local_instruction_size
.endif
    lda native_local_control_depth
    beq native_local_analyze_bad_near_external
    jsr native_local_read_selector
    bcc native_local_analyze_bad_near_external
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp native_local_operand_index
    beq native_local_analyze_bad_near_external
    bcc native_local_analyze_bad_near_external
.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
    lda native_local_instruction_size
    bne native_local_analyze_external_arg
native_local_analyze_external_arg:
    lda native_local_stack_depth
    cmp #$01
    bne native_local_analyze_bad_near_external
    dec native_local_stack_depth
    lda #$01
    sta native_local_runtime_arg_seen
    lda native_local_instruction_size
    jsr native_local_add_code_size
    jmp native_local_analyze_mark_no_advance
.endif
    lda native_local_stack_depth
    bne native_local_analyze_bad_near_external
    lda #$03
    jsr native_local_add_code_size
    jmp native_local_analyze_mark_no_advance

.if ACTC_NATIVE_LOCAL_FIXED_ROUTINES
native_local_analyze_fixed_call:
    jsr native_local_read_selector
    bcc native_local_analyze_bad_near_external
    ldx native_local_operand_index
    lda #ACTC_OVERLAY_CTX_PREPARE_FIXED_CALL_FN_LO
    jsr call_indexed_context_function
    bcc native_local_analyze_bad_near_external
    sta native_local_machine_meta
    sty native_local_instruction_size
    and #ACTC_PROC_META_PARAM_COUNT_MASK
    sta native_local_machine_param_count
    lda native_local_stack_depth
    sec
    sbc native_local_machine_param_count
    bcc native_local_analyze_bad_near_external
    sta native_local_stack_depth
    lda native_local_machine_meta
    bpl native_local_analyze_fixed_call_proc
    jsr native_local_push
    bcc native_local_analyze_bad_near_external
native_local_analyze_fixed_call_proc:
    lda #$01
    sta native_local_single_proc_applicable
    lda native_local_instruction_size
    jsr native_local_add_code_size
    jmp native_local_analyze_mark
.endif

.if ACTC_NATIVE_LOCAL_ASMBLOCK
.if ACTC_NATIVE_LOCAL_FIXED_ROUTINES
; Fixed-call analysis pushes the shared failure target outside branch range in
; the composed pass. Keep one nearby trampoline instead of four long branches.
native_local_analyze_asmblock_bad_near:
    jmp native_local_analyze_bad_near_external
.else
native_local_analyze_asmblock_bad_near = native_local_analyze_bad_near_external
.endif
native_local_analyze_asmblock:
    lda native_local_stack_depth
    bne native_local_analyze_asmblock_bad_near
    jsr native_local_read_selector
    bcc native_local_analyze_asmblock_bad_near
    jsr native_local_load_asmblock_page
    bcs native_local_analyze_asmblock_bad_near
    lda ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_PROC_INDEX
    cmp native_local_current_proc
    bne native_local_analyze_asmblock_bad_near
    ldx native_local_operand_index
    lda native_local_label_count
    sta ACTC_ASMBLOCK_LABEL_INDEX_BASE,x
    lda #$00
    sta native_local_asm_label_index
native_local_analyze_asmblock_label_loop:
    lda native_local_asm_label_index
    cmp ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_LABEL_COUNT
    beq native_local_analyze_asmblock_labels_done
    jsr native_local_allocate_label
    bcs :+
    rts
:
    tax
    ldy native_local_asm_label_index
    clc
    lda native_local_code_size_lo
    adc ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_LABEL_BASE,y
    sta native_local_label_offset_lo,x
    lda native_local_code_size_hi
    adc #$00
    sta native_local_label_offset_hi,x
    inc native_local_asm_label_index
    jmp native_local_analyze_asmblock_label_loop
native_local_analyze_asmblock_labels_done:
    lda #$01
    sta native_local_single_proc_applicable
    lda ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_CODE_LEN
    jsr native_local_add_code_size
    jmp native_local_analyze_mark
.endif

native_local_analyze_bad_near_compare:
    jmp native_local_analyze_bad
native_local_analyze_compare:
    lda native_local_stack_depth
    cmp #$02
    bcc native_local_analyze_bad_near_compare
    sec
    sbc #$02
    sta native_local_stack_depth
    ldy native_local_body_pos
    iny
    jsr emit_object_peek_payload_y
    cmp #'p'
    beq native_local_analyze_compare_inverse
    cmp #'h'
    beq native_local_analyze_compare_direct_if
    cmp #'f'
    bne native_local_analyze_compare_try_until
    lda #$02
    sta native_local_compare_advance
    jmp native_local_analyze_compare_while
native_local_analyze_compare_direct_if:
    lda #$02
    sta native_local_compare_advance
    jmp native_local_analyze_compare_if
native_local_analyze_compare_try_until:
    cmp #'t'
    bne native_local_analyze_bad_near_compare
    iny
    jsr emit_object_peek_payload_y
    cmp #'o'
    bne native_local_analyze_bad_near_compare
    lda #$03
    sta native_local_compare_advance
    jmp native_local_analyze_compare_until

native_local_analyze_compare_inverse:
    lda native_local_compare_ordered
    beq native_local_analyze_bad_near_until
    iny
    jsr emit_object_peek_payload_y
    cmp #'0'
    bcc native_local_analyze_bad_near_until
    cmp #':'
    bcs native_local_analyze_bad_near_until
    sec
    sbc #'0'
    sta native_local_operand_index
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp native_local_operand_index
    beq native_local_analyze_bad_near_until
    bcc native_local_analyze_bad_near_until
    ldx native_local_operand_index
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    iny
    ora (ACTC_OVERLAY_WORK_ZP),y
    bne native_local_analyze_bad_near_until
    ldy native_local_body_pos
    iny
    iny
    iny
    jsr emit_object_peek_payload_y
    cmp #'q'
    bne native_local_analyze_bad_near_until
    iny
    jsr emit_object_peek_payload_y
    cmp #'h'
    beq native_local_analyze_compare_inverse_if
    cmp #'f'
    bne native_local_analyze_compare_inverse_try_until
    lda #$05
    sta native_local_compare_advance
    jmp native_local_analyze_compare_while
native_local_analyze_compare_inverse_if:
    lda #$05
    sta native_local_compare_advance
    jmp native_local_analyze_compare_if
native_local_analyze_compare_inverse_try_until:
    cmp #'t'
    bne native_local_analyze_bad_near_until
    iny
    jsr emit_object_peek_payload_y
    cmp #'o'
    bne native_local_analyze_bad_near_until
    lda #$06
    sta native_local_compare_advance
native_local_analyze_bad_near_until:
    jmp native_local_analyze_bad
native_local_analyze_compare_until:
    ldx native_local_control_depth
    beq native_local_analyze_bad_near_if
    dex
    lda native_local_control_kind,x
    cmp #NATIVE_LOCAL_CONTROL_DO
    bne native_local_analyze_bad_near_if
    lda native_local_control_end,x
    sta native_local_saved_label
    stx native_local_control_depth
    lda native_local_instruction_size
    jsr native_local_add_code_size
    lda native_local_saved_label
    cmp #$FF
    beq :+
    tay
    lda native_local_code_size_lo
    sta native_local_label_offset_lo,y
    lda native_local_code_size_hi
    sta native_local_label_offset_hi,y
:
    jsr native_local_record_compare_debug_offsets
    jsr native_local_advance_compare_body
    jmp native_local_analyze_mark_no_advance
native_local_analyze_compare_while:
    ldx native_local_control_depth
    beq native_local_analyze_bad_near_if
    dex
    lda native_local_control_kind,x
    cmp #NATIVE_LOCAL_CONTROL_DO
    bne native_local_analyze_bad_near_if
    lda native_local_control_end,x
    cmp #$FF
    bne native_local_analyze_bad_near_if
    jsr native_local_allocate_label
    bcc native_local_analyze_bad_near_if
    sta native_local_control_end,x
    lda #NATIVE_LOCAL_CONTROL_WHILE
    sta native_local_control_kind,x
    lda #$01
    sta native_local_single_proc_applicable
    sta native_local_while_seen
    lda native_local_instruction_size
    jsr native_local_add_code_size
    jsr native_local_record_compare_debug_offsets
    jsr native_local_advance_compare_body
    jmp native_local_analyze_mark_no_advance
native_local_analyze_bad_near_if:
    jmp native_local_analyze_bad
native_local_analyze_compare_if:
    lda native_local_control_depth
    cmp #NATIVE_LOCAL_CONTROL_MAX
    bcs native_local_analyze_bad_near_if
    jsr native_local_allocate_label
    bcc native_local_analyze_bad_near_if
    ldx native_local_control_depth
    sta native_local_control_target,x
    lda #$FF
    sta native_local_control_end,x
    lda #NATIVE_LOCAL_CONTROL_IF
    sta native_local_control_kind,x
    inc native_local_control_depth
    lda native_local_instruction_size
    jsr native_local_add_code_size
    jsr native_local_record_compare_debug_offsets
    jsr native_local_advance_compare_body
    jmp native_local_analyze_mark_no_advance

native_local_record_compare_debug_offsets:
    lda native_local_compare_advance
    sec
    sbc #$01
    cmp #$04
    bcc :+
    sec
    sbc #$01
:   sta native_local_compare_debug_remaining
native_local_record_compare_debug_loop:
    lda native_local_compare_debug_remaining
    beq native_local_record_compare_debug_done
    jsr native_local_record_debug_offset
    dec native_local_compare_debug_remaining
    jmp native_local_record_compare_debug_loop
native_local_record_compare_debug_done:
    rts

native_local_advance_compare_body:
    clc
    lda native_local_body_pos
    adc native_local_compare_advance
    sta native_local_body_pos
    rts

native_local_analyze_do:
    lda native_local_stack_depth
    bne native_local_analyze_bad_near_if
    lda native_local_control_depth
    cmp #NATIVE_LOCAL_CONTROL_MAX
    bcs native_local_analyze_bad_near_if
    jsr native_local_allocate_label
    bcc native_local_analyze_bad_near_if
    pha
    tax
    lda native_local_code_size_lo
    sta native_local_label_offset_lo,x
    lda native_local_code_size_hi
    sta native_local_label_offset_hi,x
    pla
    ldx native_local_control_depth
    sta native_local_control_target,x
    lda #$FF
    sta native_local_control_end,x
    lda #NATIVE_LOCAL_CONTROL_DO
    sta native_local_control_kind,x
    inc native_local_control_depth
    inc native_local_body_pos
    jmp native_local_analyze_mark_no_advance

native_local_analyze_exit:
    lda native_local_stack_depth
    bne native_local_analyze_bad_near_od
    jsr native_local_read_selector
    bcc native_local_analyze_bad_near_od
    jsr native_local_ensure_exit_label
    bcc native_local_analyze_bad_near_od
    lda #$01
    sta native_local_single_proc_applicable
    lda #$03
    jsr native_local_add_code_size
    jmp native_local_analyze_mark_no_advance

native_local_analyze_while_end:
    lda native_local_stack_depth
    bne native_local_analyze_bad_near_od
    ldx native_local_control_depth
    beq native_local_analyze_bad_near_od
    dex
    lda native_local_control_kind,x
    and #$FE
    cmp #NATIVE_LOCAL_CONTROL_DO
    bne native_local_analyze_bad_near_od
    lda #$03
    jsr native_local_add_code_size
    lda native_local_control_end,x
    bmi :+
    tay
    lda native_local_code_size_lo
    sta native_local_label_offset_lo,y
    lda native_local_code_size_hi
    sta native_local_label_offset_hi,y
:
    stx native_local_control_depth
    inc native_local_body_pos
    jmp native_local_analyze_mark_no_advance

native_local_analyze_bad_near_od:
    jmp native_local_analyze_bad
native_local_analyze_od:
    lda #$01
    sta native_local_single_proc_applicable
    jmp native_local_analyze_while_end

native_local_analyze_else:
    ldx native_local_control_depth
    beq native_local_analyze_bad_near_od
    dex
    lda native_local_control_kind,x
    cmp #NATIVE_LOCAL_CONTROL_IF
    bne native_local_analyze_bad_near_od
    lda native_local_control_end,x
    cmp #$FF
    bne native_local_analyze_bad_near_od
    txa
    pha
    jsr native_local_allocate_label
    bcc native_local_analyze_else_bad_pop
    sta native_local_saved_label
    lda #$03
    jsr native_local_add_code_size
    pla
    tax
    lda native_local_saved_label
    sta native_local_control_end,x
    lda native_local_control_target,x
    tax
    lda native_local_code_size_lo
    sta native_local_label_offset_lo,x
    lda native_local_code_size_hi
    sta native_local_label_offset_hi,x
    inc native_local_body_pos
    jmp native_local_analyze_mark_no_advance
native_local_analyze_else_bad_pop:
    pla
    jmp native_local_analyze_bad

native_local_analyze_endif:
    ldx native_local_control_depth
    beq native_local_analyze_bad_near_od
    dex
    lda native_local_control_kind,x
    cmp #NATIVE_LOCAL_CONTROL_IF
    bne native_local_analyze_bad_near_od
    lda native_local_control_end,x
    cmp #$FF
    bne :+
    lda native_local_control_target,x
:   tay
    lda native_local_code_size_lo
    sta native_local_label_offset_lo,y
    lda native_local_code_size_hi
    sta native_local_label_offset_hi,y
    stx native_local_control_depth
    inc native_local_body_pos
    jmp native_local_analyze_mark_no_advance

native_local_analyze_bad_near_call:
    jmp native_local_analyze_bad
native_local_analyze_call:
    jsr native_local_read_selector
    bcc native_local_analyze_bad_near_call
    lda native_local_operand_index
    cmp native_local_main_proc
    bcs native_local_analyze_bad_near_call
.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
    ldx native_local_operand_index
    jsr native_local_load_proc_meta_byte_x
    sta native_local_machine_meta
    and #ACTC_PROC_META_MACHINE
    bne native_local_analyze_machine_call
    lda native_local_machine_meta
.else
    ldx native_local_operand_index
    jsr native_local_load_proc_meta_byte_x
.endif
    bpl native_local_analyze_proc_call
    and #ACTC_PROC_META_PARAM_COUNT_MASK
    sta native_local_instruction_size
    lda native_local_stack_depth
    sec
    sbc native_local_instruction_size
    bcc native_local_analyze_bad_near_call
    sta native_local_stack_depth
    jsr native_local_push
    bcc native_local_analyze_bad_near_call
    lda #$06
    jsr native_local_add_code_size
    jmp native_local_analyze_mark
native_local_analyze_proc_call:
    lda #$00
    sta native_local_stack_depth
    lda #$03
    jsr native_local_add_code_size
    jmp native_local_analyze_mark

.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
native_local_analyze_machine_call:
    jsr native_local_prepare_machine_call
    bcc native_local_analyze_bad_near_call
    lda native_local_stack_depth
    sec
    sbc native_local_machine_param_count
    bcc native_local_analyze_bad_near_call
    sta native_local_stack_depth
    lda native_local_machine_meta
    bpl native_local_analyze_machine_call_proc
    jsr native_local_push
    bcc native_local_analyze_bad_near_call
native_local_analyze_machine_call_proc:
    lda native_local_instruction_size
    jsr native_local_add_code_size
    jmp native_local_analyze_mark
.endif

native_local_analyze_return:
    ldy native_local_body_pos
    iny
    jsr emit_object_peek_payload_y
    bne native_local_analyze_bad
    lda native_local_control_depth
    beq :+
    jmp native_local_analyze_bad
:   lda native_local_lowering_seen
    beq native_local_analyze_bad
    lda native_local_current_proc
    cmp native_local_main_proc
    bne :+
    lda #16
    jsr native_local_add_code_size
    sec
    rts
:   ldx native_local_current_proc
    jsr native_local_load_proc_meta_byte_x
    asl
    lda #$00
    rol
    cmp native_local_stack_depth
    bne native_local_analyze_bad
    sta native_local_instruction_size
    asl
    adc native_local_instruction_size
    adc #$01
    jsr native_local_add_code_size
    sec
    rts

native_local_analyze_mark:
    ; Selector operations leave body_pos immediately after their operand.
native_local_analyze_mark_no_advance:
    lda #$01
    sta native_local_lowering_seen
    jmp native_local_analyze_loop
native_local_analyze_bad:
    clc
    rts

native_local_record_debug_offset:
    lda native_local_record_debug
    beq native_local_record_debug_offset_done
    ldx native_local_debug_count
    cpx #ACTC_OVERLAY_BODY_OP_LIMIT
    bcs native_local_record_debug_offset_done
    lda native_local_code_size_lo
    sta native_int_debug_offsets_lo,x
    lda native_local_code_size_hi
    sta native_int_debug_offsets_hi,x
    inc native_local_debug_count
native_local_record_debug_offset_done:
    rts

native_int_load_debug_offset:
    ldx entry_index_data
    lda native_local_proc_debug_base,x
    clc
    adc body_debug_index_data
    tax
    lda native_int_debug_offsets_lo,x
    ldy native_int_debug_offsets_hi,x
    rts

native_local_read_selector:
    inc native_local_body_pos
    ldy native_local_body_pos
    jsr emit_object_peek_payload_y
    cmp #'0'
    bcc native_local_read_selector_bad
    cmp #':'
    bcc native_local_read_selector_digit
    cmp #'A'
    bcc native_local_read_selector_bad
    cmp #'Z'+1
    bcs native_local_read_selector_bad
    sec
    sbc #('A'-10)
    bne native_local_read_selector_store
native_local_read_selector_digit:
    sec
    sbc #'0'
native_local_read_selector_store:
    sta native_local_operand_index
    inc native_local_body_pos
    sec
    rts
native_local_read_selector_bad:
    clc
    rts

native_local_push:
    lda native_local_stack_depth
    cmp #96
    bcs native_local_stack_bad
    inc native_local_stack_depth
    sec
    rts
native_local_pop:
    lda native_local_stack_depth
    beq native_local_stack_bad
    dec native_local_stack_depth
    sec
    rts
native_local_stack_bad:
    clc
    rts

native_local_allocate_label:
    lda native_local_label_count
    cmp #NATIVE_LOCAL_LABEL_MAX
    bcs native_local_allocate_label_bad
    inc native_local_label_count
    sec
    rts
native_local_allocate_label_bad:
    clc
    rts

native_local_ensure_exit_label:
    ldx native_local_control_depth
native_local_ensure_exit_label_loop:
    cpx #$00
    beq native_local_ensure_exit_label_bad
    dex
    lda native_local_control_kind,x
    cmp #NATIVE_LOCAL_CONTROL_DO
    beq native_local_ensure_exit_label_found
    cmp #NATIVE_LOCAL_CONTROL_WHILE
    bne native_local_ensure_exit_label_loop
native_local_ensure_exit_label_found:
    lda native_local_control_end,x
    cmp #$FF
    bne native_local_ensure_exit_label_ready
    txa
    pha
    jsr native_local_allocate_label
    bcc native_local_ensure_exit_label_bad_pop
    sta native_local_saved_label
    pla
    tax
    lda native_local_saved_label
    sta native_local_control_end,x
native_local_ensure_exit_label_ready:
    sta native_local_saved_label
    sec
    rts
native_local_ensure_exit_label_bad_pop:
    pla
native_local_ensure_exit_label_bad:
    clc
    rts

native_local_add_code_size:
    clc
    adc native_local_code_size_lo
    sta native_local_code_size_lo
    bcc :+
    inc native_local_code_size_hi
:   rts

native_local_word_var_offset:
    sta native_local_target_var
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp native_local_target_var
    beq native_local_word_var_offset_bad
    bcc native_local_word_var_offset_bad
    lda native_local_target_var
    asl
    bcs native_local_word_var_offset_bad
    sec
    rts
native_local_word_var_offset_bad:
    clc
    rts

native_local_load_proc_meta_byte_x:
    lda #ACTC_OVERLAY_CTX_LOAD_PROC_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_PROC_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    rts

native_local_load_var_width_x:
    lda #ACTC_OVERLAY_CTX_LOAD_VAR_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    rts

.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
native_local_load_var_type_x:
    jsr native_local_load_var_width_x
    ldy #$03
    lda (ACTC_OVERLAY_WORK_ZP),y
    rts

native_local_load_current_machine:
    ldx native_local_current_proc
    jsr native_local_load_proc_meta_byte_x
    and #ACTC_PROC_META_MACHINE
    sta native_local_current_machine
    rts

; Prepare the register ABI for the local machine routine selected by the
; current body operand. All source arguments occupy one compiler stack word;
; BYTE contributes one ABI byte while CARD/INT contributes two.
native_local_prepare_machine_call:
    lda native_local_machine_meta
    and #ACTC_PROC_META_PARAM_COUNT_MASK
    sta native_local_machine_param_count
    ldy #$01
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_local_machine_param_base
    lda #$00
    sta native_local_machine_param_index
    sta native_local_machine_byte_count
native_local_prepare_machine_param_loop:
    lda native_local_machine_param_index
    cmp native_local_machine_param_count
    beq native_local_prepare_machine_sizes
    clc
    adc native_local_machine_param_base
    tax
    jsr native_local_load_var_type_x
    cmp #'b'
    beq native_local_prepare_machine_byte_param
native_local_prepare_machine_word_param:
    inc native_local_machine_byte_count
native_local_prepare_machine_byte_param:
    inc native_local_machine_byte_count
    lda native_local_machine_byte_count
    cmp #17
    bcs native_local_prepare_machine_call_bad
    inc native_local_machine_param_index
    jmp native_local_prepare_machine_param_loop

native_local_prepare_machine_sizes:
    lda native_local_machine_param_count
    asl a
    sta native_local_machine_setup_size
    lda native_local_machine_byte_count
    cmp #$02
    bcc native_local_prepare_machine_call_size
    beq native_local_prepare_machine_assign_one
    cmp #$03
    beq native_local_prepare_machine_assign_two
    sta native_local_machine_byte_pos
    asl a
    clc
    adc native_local_machine_byte_pos
    sec
    sbc #$07
    bne native_local_prepare_machine_assign_add
native_local_prepare_machine_assign_two:
    lda #$02
    bne native_local_prepare_machine_assign_add
native_local_prepare_machine_assign_one:
    lda #$01
native_local_prepare_machine_assign_add:
    clc
    adc native_local_machine_setup_size
    sta native_local_machine_setup_size

native_local_prepare_machine_call_size:
    clc
    lda native_local_machine_setup_size
    adc #$03
    sta native_local_instruction_size
    lda native_local_machine_meta
    bpl native_local_prepare_machine_call_ok
    and #ACTC_PROC_META_BYTE_RETURN
    beq native_local_prepare_machine_word_return
    lda #$05
    bne native_local_prepare_machine_return_add
native_local_prepare_machine_word_return:
    lda #$03
native_local_prepare_machine_return_add:
    clc
    adc native_local_instruction_size
    sta native_local_instruction_size
native_local_prepare_machine_call_ok:
    sec
    rts
native_local_prepare_machine_call_bad:
    clc
    rts
.endif

.if ACTC_NATIVE_LOCAL_ASMBLOCK
native_local_init_asmblocks:
    lda #ACTC_OVERLAY_CTX_IMPORT_FLAGS_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    lsr a
    lsr a
    lsr a
    lsr a
    sta native_local_asmblock_count
    lda #$00
    sta native_local_asm_plain_count
    rts

native_local_load_asmblock_page:
    lda native_local_operand_index
    cmp native_local_asmblock_count
    bcs native_local_load_asmblock_page_fail
    clc
    adc #ACTC_ASMBLOCK_REU_HI_BASE
    sta ACTC_ASMBLOCK_REU_PARAMS+1
    lda #$00
    sta ACTC_ASMBLOCK_REU_PARAMS+0
    lda #ACTC_ASMBLOCK_REU_BANK
    sta ACTC_ASMBLOCK_REU_PARAMS+2
    lda #<ACTC_ASMBLOCK_PAGE_BUFFER
    sta ACTC_ASMBLOCK_REU_PARAMS+3
    lda #>ACTC_ASMBLOCK_PAGE_BUFFER
    sta ACTC_ASMBLOCK_REU_PARAMS+4
    lda #$00
    sta ACTC_ASMBLOCK_REU_PARAMS+5
    lda #$01
    sta ACTC_ASMBLOCK_REU_PARAMS+6
    lda #tool_file_status_fail
    sta ACTC_ASMBLOCK_REU_PARAMS+7
    ldx #ACTC_ASMBLOCK_REU_PARAMS
    jsr svc_reu_read_sc0
    lda ACTC_ASMBLOCK_REU_PARAMS+7
    cmp #tool_file_status_ok
    bne native_local_load_asmblock_page_fail
    lda ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_MAGIC
    cmp #ACTC_ASMBLOCK_MAGIC
    bne native_local_load_asmblock_page_fail
    lda ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_VERSION
    cmp #ACTC_ASMBLOCK_VERSION
    bne native_local_load_asmblock_page_fail
    lda ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_CODE_LEN
    cmp #ACTC_ASMBLOCK_CODE_CAPACITY+1
    bcs native_local_load_asmblock_page_fail
    lda ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_LABEL_COUNT
    cmp #ACTC_ASMBLOCK_LABEL_MAX+1
    bcs native_local_load_asmblock_page_fail
    lda ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_RELOC_COUNT
    cmp #ACTC_ASMBLOCK_RELOC_MAX+1
    bcs native_local_load_asmblock_page_fail
    clc
    rts
native_local_load_asmblock_page_fail:
    sec
    rts
.endif

native_local_find_helper_indices:
    ldx #$02
native_local_find_helper_indices_loop:
    lda #$FF
    sta native_local_mul_index,x
    lda native_local_helper_name_lo,x
    ldy native_local_helper_name_hi,x
    stx native_local_operand_index
    jsr native_local_find_external
    ldx native_local_operand_index
    bcc :+
    sta native_local_mul_index,x
:   dex
    bpl native_local_find_helper_indices_loop
    rts

native_local_find_external:
    sta native_local_const_ptr_lo
    sty native_local_const_ptr_hi
    lda #$00
    sta entry_index_data
native_local_find_external_loop:
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq native_local_find_external_no
    ldx entry_index_data
    lda #ACTC_OVERLAY_CTX_SET_EXTERNAL_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    lda native_local_const_ptr_lo
    sta ACTC_OVERLAY_WORK_ZP
    lda native_local_const_ptr_hi
    sta ACTC_OVERLAY_WORK_ZP+1
    ldy #$00
native_local_find_external_compare:
    lda (ACTC_OVERLAY_SCAN_ZP),y
    jsr lowercase_ascii_overlay
    cmp (ACTC_OVERLAY_WORK_ZP),y
    bne native_local_find_external_next
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq native_local_find_external_yes
    iny
    bne native_local_find_external_compare
native_local_find_external_next:
    inc entry_index_data
    jmp native_local_find_external_loop
native_local_find_external_yes:
    lda entry_index_data
    sec
    rts
native_local_find_external_no:
    clc
    rts

emit_native_integer_export_list:
    lda #$00
    sta native_local_export_offset_lo
    sta native_local_export_offset_hi
    lda native_local_root_size_lo
    sta native_local_export_size_lo
    lda native_local_root_size_hi
    sta native_local_export_size_hi
    ldx native_local_main_proc
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr native_local_emit_export_line

    lda native_local_main_proc
    beq native_local_emit_proc_exports_done
    sec
    sbc #$01
    sta native_local_current_proc
native_local_emit_proc_exports_loop:
    ldx native_local_current_proc
    lda native_local_proc_offset_lo,x
    sta native_local_export_offset_lo
    lda native_local_proc_offset_hi,x
    sta native_local_export_offset_hi
    lda native_local_proc_size_lo,x
    sta native_local_export_size_lo
    lda native_local_proc_size_hi,x
    sta native_local_export_size_hi
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr native_local_emit_export_line
    lda native_local_current_proc
    beq native_local_emit_proc_exports_done
    dec native_local_current_proc
    jmp native_local_emit_proc_exports_loop
native_local_emit_proc_exports_done:
    lda #$00
    sta native_local_record_debug
    lda native_local_main_proc
    sta native_local_current_proc
native_local_emit_label_proc_loop:
    jsr native_local_analyze_current_proc
    NATIVE_LOCAL_JCC native_local_emit_export_fail
    lda #$00
    sta native_local_label_index
native_local_emit_label_loop:
    lda native_local_label_index
    cmp native_local_label_count
    beq native_local_emit_label_next_proc
    tax
    lda native_local_label_offset_lo,x
    sta native_local_export_offset_lo
    lda native_local_label_offset_hi,x
    sta native_local_export_offset_hi
    lda #$01
    sta native_local_export_size_lo
    lda #$00
    sta native_local_export_size_hi
    ldx native_local_label_index
    jsr native_local_build_label_name
    jsr native_local_emit_export_line
    inc native_local_label_index
    jmp native_local_emit_label_loop
native_local_emit_label_next_proc:
    lda native_local_current_proc
    beq native_local_emit_data_exports
    dec native_local_current_proc
    jmp native_local_emit_label_proc_loop

native_local_emit_data_exports:
.if ACTC_NATIVE_LOCAL_ASMBLOCK
    jsr native_local_emit_asmblock_exports
.endif
    lda native_local_data_size_lo
    ora native_local_data_size_hi
    beq native_local_emit_export_done
    lda native_local_total_code_lo
    sta native_local_export_offset_lo
    lda native_local_total_code_hi
    sta native_local_export_offset_hi
    lda native_local_data_size_lo
    sta native_local_export_size_lo
    lda native_local_data_size_hi
    sta native_local_export_size_hi
    lda #<native_local_name_data
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>native_local_name_data
    sta ACTC_OVERLAY_SCAN_ZP+1
    jsr native_local_emit_export_line
    clc
    lda native_local_total_code_lo
    adc native_local_data_size_lo
    sta native_local_export_offset_lo
    lda native_local_total_code_hi
    adc native_local_data_size_hi
    sta native_local_export_offset_hi
    lda #$02
    sta native_local_export_size_lo
    lda #$00
    sta native_local_export_size_hi
    lda #<native_local_name_pointer
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>native_local_name_pointer
    sta ACTC_OVERLAY_SCAN_ZP+1
    jsr native_local_emit_export_line
native_local_emit_export_done:
    clc
    rts
native_local_emit_export_fail:
    sec
    rts

native_local_emit_export_line:
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr emit_lower_scan_zp_string
    lda #' '
    jsr emit_char_overlay
    lda native_local_export_offset_lo
    ldy native_local_export_offset_hi
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda native_local_export_size_lo
    ldy native_local_export_size_hi
    jsr emit_word_decimal
    jmp emit_newline

native_local_build_label_name:
    txa
    clc
    adc #'0'
    sta native_local_label_name+5
    lda native_local_current_proc
    clc
    adc #'0'
    sta native_local_label_name+3
    lda #<native_local_label_name
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>native_local_label_name
    sta ACTC_OVERLAY_SCAN_ZP+1
    rts

.if ACTC_NATIVE_LOCAL_ASMBLOCK
native_local_emit_asmblock_exports:
    lda #$00
    sta native_local_asm_plain_count
    lda native_local_asmblock_count
    beq native_local_emit_asmblock_export_done
    lda #$00
    sta native_local_asm_var_index
    lda native_local_total_code_lo
    sta native_local_export_offset_lo
    lda native_local_total_code_hi
    sta native_local_export_offset_hi
native_local_emit_asmblock_var_loop:
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp native_local_asm_var_index
    beq native_local_emit_asmblock_export_done
    ldx native_local_asm_var_index
    jsr native_local_load_var_width_x
    sta native_local_export_size_lo
    lda #$00
    sta native_local_export_size_hi
    jsr native_local_build_asm_var_name
    jsr native_local_emit_export_line
    inc native_local_asm_plain_count
    inc native_local_asm_var_index
    clc
    lda native_local_export_offset_lo
    adc native_local_export_size_lo
    sta native_local_export_offset_lo
    bcc native_local_emit_asmblock_var_loop
    inc native_local_export_offset_hi
    jmp native_local_emit_asmblock_var_loop
native_local_emit_asmblock_export_done:
    clc
    rts

native_local_build_asm_var_name:
    lda native_local_asm_var_index
    jsr native_local_selector_ascii
    sta native_local_asm_var_name+3
    lda #<native_local_asm_var_name
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>native_local_asm_var_name
    sta ACTC_OVERLAY_SCAN_ZP+1
    rts

native_local_selector_ascii:
    cmp #10
    bcc native_local_selector_ascii_digit
    clc
    adc #('A'-10)
    rts
native_local_selector_ascii_digit:
    clc
    adc #'0'
    rts
.endif

emit_native_integer_body_marker_list:
    lda #$00
    sta native_local_marker_count
    ldx #$00
native_local_count_label_markers_loop:
    cpx native_local_proc_count
    beq native_local_count_label_markers_done
    clc
    lda native_local_marker_count
    adc native_local_proc_label_count,x
    sta native_local_marker_count
    inx
    jmp native_local_count_label_markers_loop
native_local_count_label_markers_done:
.if ACTC_NATIVE_LOCAL_ASMBLOCK
    clc
    lda native_local_marker_count
    adc native_local_asm_plain_count
    bcs native_local_emit_markers_fail
    sta native_local_marker_count
.endif
    lda native_local_data_size_lo
    ora native_local_data_size_hi
    beq native_local_emit_proc_markers
    inc native_local_marker_count
    inc native_local_marker_count
native_local_emit_proc_markers:
    lda native_local_main_proc
    sta native_local_current_proc
native_local_emit_proc_marker_loop:
    jsr native_local_clear_marker_visits
    lda #$00
    sta native_local_used_helpers
    lda #'b'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx native_local_current_proc
    jsr native_local_emit_marker_closure
    lda #'M'
    jsr emit_char_overlay
    jsr emit_newline
    dec native_local_current_proc
    bpl native_local_emit_proc_marker_loop

native_local_emit_plain_markers:
    jsr native_local_clear_marker_visits
native_local_emit_plain_markers_loop:
    lda native_local_marker_count
    beq native_local_emit_markers_done
    jsr emit_machine_body_marker_line
    dec native_local_marker_count
    jmp native_local_emit_plain_markers_loop
native_local_emit_markers_done:
    clc
    rts
.if ACTC_NATIVE_LOCAL_ASMBLOCK
native_local_emit_markers_fail:
    sec
    rts
.endif

native_local_clear_marker_visits:
    ldx #$00
native_local_clear_marker_visits_loop:
    cpx native_local_proc_count
    beq native_local_clear_marker_visits_done
    lda native_local_proc_label_count,x
    and #$7F
    sta native_local_proc_label_count,x
    inx
    bne native_local_clear_marker_visits_loop
native_local_clear_marker_visits_done:
    rts

native_local_emit_marker_closure:
    lda native_local_proc_label_count,x
    bmi native_local_emit_marker_closure_done
    ora #$80
    sta native_local_proc_label_count,x
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    jsr native_local_emit_marker_direct_imports
    lda #$00
    sta native_local_body_pos
native_local_emit_marker_closure_loop:
    ldy native_local_body_pos
    jsr emit_object_peek_payload_y
    beq native_local_emit_marker_closure_done
    cmp #'c'
    beq native_local_emit_marker_closure_call
.if ACTC_NATIVE_LOCAL_FIXED_ROUTINES
    cmp #ACTC_BODY_OP_FIXED_CALL
    beq native_local_emit_marker_closure_skip_selector
.endif
    inc native_local_body_pos
    jmp native_local_emit_marker_closure_loop
.if ACTC_NATIVE_LOCAL_FIXED_ROUTINES
native_local_emit_marker_closure_skip_selector:
    inc native_local_body_pos
    inc native_local_body_pos
    jmp native_local_emit_marker_closure_loop
.endif
native_local_emit_marker_closure_call:
    jsr native_local_read_selector
    ldx native_local_operand_index
    inc native_local_body_pos
    lda native_local_body_pos
    pha
    lda ACTC_OVERLAY_SCAN_ZP
    pha
    lda ACTC_OVERLAY_SCAN_ZP+1
    pha
    jsr native_local_emit_marker_closure
    pla
    sta ACTC_OVERLAY_SCAN_ZP+1
    pla
    sta ACTC_OVERLAY_SCAN_ZP
    pla
    sta native_local_body_pos
    jmp native_local_emit_marker_closure_loop
native_local_emit_marker_closure_done:
    rts

native_local_emit_marker_direct_imports:
    lda #$00
    sta native_local_body_pos
native_local_emit_marker_direct_imports_loop:
    ldy native_local_body_pos
    jsr emit_object_peek_payload_y
    beq native_local_emit_marker_direct_imports_done
.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
    cmp #'A'
    beq native_local_emit_marker_direct_external
    cmp #'U'
    beq native_local_emit_marker_direct_external
.endif
    cmp #'u'
    beq native_local_emit_marker_direct_external
.if ACTC_NATIVE_LOCAL_FIXED_ROUTINES
    cmp #ACTC_BODY_OP_FIXED_CALL
    beq native_local_emit_marker_direct_skip_selector
.endif
    cmp #'*'
    beq native_local_emit_marker_direct_mul
    cmp #'/'
    beq native_local_emit_marker_direct_div
    cmp #'y'
    beq native_local_emit_marker_direct_print
    cmp #'z'
    beq native_local_emit_marker_direct_print
native_local_emit_marker_direct_advance:
    inc native_local_body_pos
    jmp native_local_emit_marker_direct_imports_loop
.if ACTC_NATIVE_LOCAL_FIXED_ROUTINES
native_local_emit_marker_direct_skip_selector:
    inc native_local_body_pos
    inc native_local_body_pos
    jmp native_local_emit_marker_direct_imports_loop
.endif
native_local_emit_marker_direct_external:
    lda #'u'
    jsr emit_char_overlay
    jsr native_local_read_selector
    lda native_local_operand_index
    jsr emit_object_selector_overlay
    jmp native_local_emit_marker_direct_advance
native_local_emit_marker_direct_mul:
    lda #NATIVE_LOCAL_USE_MUL
    ldx native_local_mul_index
    jmp native_local_emit_marker_direct_helper
native_local_emit_marker_direct_div:
    lda #NATIVE_LOCAL_USE_DIV
    ldx native_local_div_index
    jmp native_local_emit_marker_direct_helper
native_local_emit_marker_direct_print:
    lda #NATIVE_LOCAL_USE_PRINT
    ldx native_local_print_index
native_local_emit_marker_direct_helper:
    sta native_local_instruction_size
    and native_local_used_helpers
    bne native_local_emit_marker_direct_advance
    lda native_local_instruction_size
    ora native_local_used_helpers
    sta native_local_used_helpers
    stx native_local_operand_index
    lda #'u'
    jsr emit_char_overlay
    lda native_local_operand_index
    jsr emit_object_selector_overlay
    jmp native_local_emit_marker_direct_advance
native_local_emit_marker_direct_imports_done:
    rts

emit_native_integer_machine_code_list:
    lda #'m'
    jsr emit_char_overlay
    lda native_local_main_proc
    sta native_local_current_proc
native_local_emit_code_proc_loop:
.if ACTC_NATIVE_LOCAL_PARAM_BINDS
    lda #$01
    sta native_local_param_bind_phase
.endif
    lda native_local_current_proc
    cmp native_local_main_proc
    bne native_local_emit_code_select_body
    lda native_local_data_size_lo
    ora native_local_data_size_hi
    beq native_local_emit_code_select_body
    lda #<native_local_prologue
    ldy #>native_local_prologue
    ldx #(native_local_prologue_end-native_local_prologue)
    jsr native_local_emit_const_bytes
native_local_emit_code_select_body:
    ldx native_local_current_proc
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
    jsr native_local_load_current_machine
.endif
    lda #$00
    sta native_local_body_pos
    jsr native_local_emit_code_loop
    lda native_local_current_proc
    beq native_local_emit_code_done_procs
    dec native_local_current_proc
    jmp native_local_emit_code_proc_loop
native_local_emit_code_done_procs:
    jsr native_local_emit_data
    jsr emit_newline
    jmp native_local_emit_reloc_list

native_local_emit_code_loop:
    ldy native_local_body_pos
    jsr emit_object_peek_payload_y
.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
    ldx native_local_current_machine
    beq native_local_emit_normal_op
    cmp #$00
    beq native_local_emit_machine_done
    cmp #'@'
    beq native_local_emit_normal_op
    sec
    rts
native_local_emit_normal_op:
.endif
.if ACTC_NATIVE_LOCAL_PARAM_BINDS
    cmp #'S'
    NATIVE_LOCAL_JEQ native_local_emit_store
    ldx #$00
    stx native_local_param_bind_phase
.endif
    jsr native_local_classify_body_op
    bcs :+
    sec
    rts
:
    lda native_local_emit_target_lo,x
    sta ACTC_OVERLAY_WORK_ZP
    lda native_local_emit_target_hi,x
    sta ACTC_OVERLAY_WORK_ZP+1
    jmp (ACTC_OVERLAY_WORK_ZP)

native_local_emit_target_lo:
    .byte <native_local_emit_compare_found,<native_local_emit_compare_found
    .byte <native_local_emit_compare_found,<native_local_emit_compare_found
    .byte <native_local_emit_literal,<native_local_emit_load,<native_local_emit_store
    .byte <native_local_emit_add,<native_local_emit_sub
    .byte <native_local_emit_mul_div,<native_local_emit_mul_div
    .byte <native_local_emit_print,<native_local_emit_print_line
.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
    .byte <native_local_emit_external_a_call,<native_local_emit_external_xy_call
    .byte <native_local_emit_external_call
.else
    .byte <native_local_emit_call
.endif
.if ACTC_NATIVE_LOCAL_FIXED_ROUTINES
    .byte <native_local_emit_fixed_call
.endif
.if ACTC_NATIVE_LOCAL_ASMBLOCK
    .byte <native_local_emit_asmblock
.endif
    .byte <native_local_emit_no_code,<native_local_emit_else,<native_local_emit_no_code
    .byte <native_local_emit_while_end,<native_local_emit_while_end
    .byte <native_local_emit_exit,<native_local_emit_call,<native_local_emit_return
native_local_emit_target_hi:
    .byte >native_local_emit_compare_found,>native_local_emit_compare_found
    .byte >native_local_emit_compare_found,>native_local_emit_compare_found
    .byte >native_local_emit_literal,>native_local_emit_load,>native_local_emit_store
    .byte >native_local_emit_add,>native_local_emit_sub
    .byte >native_local_emit_mul_div,>native_local_emit_mul_div
    .byte >native_local_emit_print,>native_local_emit_print_line
.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
    .byte >native_local_emit_external_a_call,>native_local_emit_external_xy_call
    .byte >native_local_emit_external_call
.else
    .byte >native_local_emit_call
.endif
.if ACTC_NATIVE_LOCAL_FIXED_ROUTINES
    .byte >native_local_emit_fixed_call
.endif
.if ACTC_NATIVE_LOCAL_ASMBLOCK
    .byte >native_local_emit_asmblock
.endif
    .byte >native_local_emit_no_code,>native_local_emit_else,>native_local_emit_no_code
    .byte >native_local_emit_while_end,>native_local_emit_while_end
    .byte >native_local_emit_exit,>native_local_emit_call,>native_local_emit_return
native_local_emit_target_end:

.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
native_local_emit_machine_done:
    clc
    rts
.endif

native_local_emit_compare_found:
    stx native_local_compare_index
    cpx #$02
    bcc native_local_emit_compare_select
    ldy native_local_body_pos
    iny
    jsr emit_object_peek_payload_y
    cmp #'p'
    bne native_local_emit_compare_select
    inc native_local_compare_index
    inc native_local_compare_index
native_local_emit_compare_select:
    ldx native_local_compare_index
    txa
    pha
    lda native_local_compare_bytes_len,x
    tax
    pla
    tay
    lda native_local_compare_bytes_lo,y
    pha
    lda native_local_compare_bytes_hi,y
    tay
    pla
    jmp native_local_emit_compare

native_local_emit_literal:
    jsr native_local_read_selector
    ldx native_local_operand_index
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    lda #$A9
    jsr native_local_emit_byte
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr native_local_emit_byte
    lda #$48
    jsr native_local_emit_byte
    lda #$A9
    jsr native_local_emit_byte
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$01
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr native_local_emit_byte
    lda #$48
    jsr native_local_emit_byte
    jmp native_local_emit_code_loop

.if ACTC_NATIVE_LOCAL_ASMBLOCK
native_local_emit_asmblock:
    jsr native_local_read_selector
    jsr native_local_load_asmblock_page
    bcs native_local_emit_asmblock_fail
    lda #<(ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_CODE_BASE)
    ldy #>(ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_CODE_BASE)
    ldx ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_CODE_LEN
    jsr native_local_emit_const_bytes
    jmp native_local_emit_code_loop
native_local_emit_asmblock_fail:
    sec
    rts
.endif

native_local_emit_load:
    jsr native_local_read_selector
    lda native_local_operand_index
    jsr native_local_word_var_offset
    sta native_local_var_offset
    lda #$A0
    jsr native_local_emit_byte
    lda native_local_var_offset
    jsr native_local_emit_byte
    lda #<native_local_load_tail
    ldy #>native_local_load_tail
    ldx #(native_local_load_tail_end-native_local_load_tail)
    jsr native_local_emit_const_bytes
    jmp native_local_emit_code_loop

native_local_emit_store:
    jsr native_local_read_selector
    lda native_local_operand_index
    jsr native_local_word_var_offset
    sta native_local_var_offset
.if ACTC_NATIVE_LOCAL_PARAM_BINDS
    lda native_local_param_bind_phase
    beq native_local_emit_store_value
    cmp #$01
    bne :+
    inc native_local_param_bind_phase
    lda #<native_local_param_return_save
    ldy #>native_local_param_return_save
    ldx #(native_local_param_return_save_end-native_local_param_return_save)
    jsr native_local_emit_const_bytes
:
    lda #<native_local_param_store_head
    ldy #>native_local_param_store_head
    ldx #(native_local_param_store_head_end-native_local_param_store_head)
    jsr native_local_emit_const_bytes
    lda native_local_var_offset
    clc
    adc #$01
    jsr native_local_emit_byte
    lda #<native_local_param_store_tail
    ldy #>native_local_param_store_tail
    ldx #(native_local_param_store_tail_end-native_local_param_store_tail)
    jsr native_local_emit_const_bytes
    ldy native_local_body_pos
    jsr emit_object_peek_payload_y
    cmp #'S'
    beq native_local_emit_store_done
    lda #$00
    sta native_local_param_bind_phase
    lda #<native_local_param_return_restore
    ldy #>native_local_param_return_restore
    ldx #(native_local_param_return_restore_end-native_local_param_return_restore)
    jsr native_local_emit_const_bytes
native_local_emit_store_done:
    jmp native_local_emit_code_loop
native_local_emit_store_value:
.endif
    lda #<native_local_store_head
    ldy #>native_local_store_head
    ldx #(native_local_store_head_end-native_local_store_head)
    jsr native_local_emit_const_bytes
    lda native_local_var_offset
    jsr native_local_emit_byte
    lda #<native_local_store_tail
    ldy #>native_local_store_tail
    ldx #(native_local_store_tail_end-native_local_store_tail)
    jsr native_local_emit_const_bytes
    jmp native_local_emit_code_loop

native_local_emit_add:
    lda #<native_local_add_bytes
    ldy #>native_local_add_bytes
    bne native_local_emit_add_sub
native_local_emit_sub:
    lda #<native_local_sub_bytes
    ldy #>native_local_sub_bytes
native_local_emit_add_sub:
    ldx #19
    jsr native_local_emit_const_bytes
    inc native_local_body_pos
    jmp native_local_emit_code_loop

native_local_emit_mul_div:
    lda #<native_local_mul_div_bytes
    ldy #>native_local_mul_div_bytes
    ldx #23
    jsr native_local_emit_const_bytes
    inc native_local_body_pos
    jmp native_local_emit_code_loop

native_local_emit_print:
    lda #<native_local_print_bytes
    ldy #>native_local_print_bytes
    ldx #6
    jsr native_local_emit_const_bytes
    inc native_local_body_pos
    jmp native_local_emit_code_loop
native_local_emit_print_line:
    lda #<native_local_print_bytes
    ldy #>native_local_print_bytes
    ldx #6
    jsr native_local_emit_const_bytes
    lda #<native_local_newline_bytes
    ldy #>native_local_newline_bytes
    ldx #5
    jsr native_local_emit_const_bytes
    inc native_local_body_pos
    jmp native_local_emit_code_loop

native_local_emit_compare:
    jsr native_local_emit_const_bytes
    ldy native_local_body_pos
    iny
    jsr emit_object_peek_payload_y
    cmp #'p'
    beq native_local_emit_compare_inverse_advance
    cmp #'h'
    beq native_local_emit_compare_direct_advance
    cmp #'f'
    beq native_local_emit_compare_direct_advance
    lda native_local_body_pos
    clc
    adc #$03
    sta native_local_body_pos
    jmp native_local_emit_code_loop
native_local_emit_compare_inverse_advance:
    ldy native_local_body_pos
    iny
    iny
    iny
    iny
    jsr emit_object_peek_payload_y
    cmp #'t'
    beq native_local_emit_compare_inverse_until_advance
    lda #$05
    bne native_local_emit_compare_add_advance
native_local_emit_compare_inverse_until_advance:
    lda #$06
native_local_emit_compare_add_advance:
    clc
    adc native_local_body_pos
    sta native_local_body_pos
    jmp native_local_emit_code_loop
native_local_emit_compare_direct_advance:
    lda native_local_body_pos
    clc
    adc #$02
    sta native_local_body_pos
    jmp native_local_emit_code_loop

native_local_emit_no_code:
    inc native_local_body_pos
    jmp native_local_emit_code_loop

native_local_emit_while_end:
native_local_emit_else:
    inc native_local_body_pos
native_local_emit_jump:
    lda #<native_local_jump_bytes
    ldy #>native_local_jump_bytes
    ldx #(native_local_jump_bytes_end-native_local_jump_bytes)
    jsr native_local_emit_const_bytes
    jmp native_local_emit_code_loop

native_local_emit_exit:
    jsr native_local_read_selector
    jmp native_local_emit_jump

.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
native_local_emit_external_xy_call:
    jsr native_local_read_selector
    lda #<native_local_xy_word_call_bytes
    ldy #>native_local_xy_word_call_bytes
    ldx #(native_local_xy_word_call_bytes_end-native_local_xy_word_call_bytes)
    jsr native_local_emit_const_bytes
    jmp native_local_emit_code_loop

native_local_emit_external_call:
    jsr native_local_read_selector
    clc
    bcc native_local_emit_call_selected

native_local_emit_external_a_call:
    jsr native_local_read_selector
    lda #<native_local_a_byte_call_bytes
    ldy #>native_local_a_byte_call_bytes
    ldx #(native_local_a_byte_call_bytes_end-native_local_a_byte_call_bytes)
    jsr native_local_emit_const_bytes
    jmp native_local_emit_code_loop
.endif
.if ACTC_NATIVE_LOCAL_FIXED_ROUTINES
native_local_emit_fixed_call:
    jsr native_local_read_selector
    ldx native_local_operand_index
    lda #ACTC_OVERLAY_CTX_EMIT_FIXED_CALL_FN_LO
    jsr call_indexed_context_function
    bcc native_local_emit_machine_call_bad
    jmp native_local_emit_code_loop
.endif
native_local_emit_call:
    jsr native_local_read_selector
    ldx native_local_operand_index
.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
    jsr native_local_load_proc_meta_byte_x
    sta native_local_machine_meta
    and #ACTC_PROC_META_MACHINE
    bne native_local_emit_machine_call
    lda native_local_machine_meta
.else
    jsr native_local_load_proc_meta_byte_x
.endif
    asl
native_local_emit_call_selected:
    ldx #$03
    bcc native_local_emit_local_call_bytes
    ldx #$06
native_local_emit_local_call_bytes:
    lda #<native_local_function_call_bytes
    ldy #>native_local_function_call_bytes
    jsr native_local_emit_const_bytes
    jmp native_local_emit_code_loop

.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
native_local_emit_machine_call:
    jsr native_local_prepare_machine_call
    bcc native_local_emit_machine_call_bad
    jsr native_local_emit_machine_arguments
    lda native_local_machine_meta
    bmi native_local_emit_machine_function_call
    lda #<native_local_function_call_bytes
    ldy #>native_local_function_call_bytes
    ldx #$03
    bne native_local_emit_machine_call_bytes
native_local_emit_machine_function_call:
    and #ACTC_PROC_META_BYTE_RETURN
    bne native_local_emit_machine_byte_call
    lda #<native_local_function_call_bytes
    ldy #>native_local_function_call_bytes
    ldx #$06
    bne native_local_emit_machine_call_bytes
native_local_emit_machine_byte_call:
    lda #<native_local_byte_function_call_bytes
    ldy #>native_local_byte_function_call_bytes
    ldx #(native_local_byte_function_call_bytes_end-native_local_byte_function_call_bytes)
native_local_emit_machine_call_bytes:
    jsr native_local_emit_const_bytes
native_local_emit_machine_call_done:
    jmp native_local_emit_code_loop
native_local_emit_machine_call_bad:
    sec
    rts

native_local_emit_machine_arguments:
    lda native_local_machine_param_count
    sta native_local_machine_param_index
    lda native_local_machine_byte_count
    sta native_local_machine_byte_pos
native_local_emit_machine_argument_loop:
    lda native_local_machine_param_index
    beq native_local_emit_machine_arguments_done
    dec native_local_machine_param_index
    clc
    lda native_local_machine_param_base
    adc native_local_machine_param_index
    tax
    jsr native_local_load_var_type_x
    cmp #'b'
    beq native_local_emit_machine_byte_argument
native_local_emit_machine_word_argument:
    dec native_local_machine_byte_pos
    jsr native_local_emit_machine_pop_assignment
    dec native_local_machine_byte_pos
    jsr native_local_emit_machine_pop_assignment
    jmp native_local_emit_machine_argument_loop
native_local_emit_machine_byte_argument:
    lda #$68
    jsr native_local_emit_byte
    dec native_local_machine_byte_pos
    jsr native_local_emit_machine_pop_assignment
    jmp native_local_emit_machine_argument_loop
native_local_emit_machine_pop_assignment:
    lda #$68
    jsr native_local_emit_byte
    jmp native_local_emit_machine_assignment
native_local_emit_machine_arguments_done:
    rts

native_local_emit_machine_assignment:
    lda native_local_machine_byte_pos
    beq native_local_emit_machine_assignment_done
    cmp #$03
    bcs native_local_emit_machine_assignment_memory
    tax
    lda native_local_machine_assignment_opcodes-1,x
    jmp native_local_emit_byte
native_local_emit_machine_assignment_memory:
    pha
    lda #$8D
    jsr native_local_emit_byte
    pla
    clc
    adc #$A0
    jsr native_local_emit_byte
    lda #$00
    jsr native_local_emit_byte
    rts
native_local_emit_machine_assignment_done:
    rts
native_local_machine_assignment_opcodes:
    .byte $AA,$A8
.endif

native_local_emit_return:
    lda native_local_current_proc
    cmp native_local_main_proc
    bne native_local_emit_helper_return
    lda #<native_local_exit_bytes
    ldy #>native_local_exit_bytes
    ldx #(native_local_exit_bytes_end-native_local_exit_bytes)
    jsr native_local_emit_const_bytes
    clc
    rts
native_local_emit_helper_return:
    ldx native_local_current_proc
    jsr native_local_load_proc_meta_byte_x
    bmi native_local_emit_function_return
    lda #$60
    jsr native_local_emit_byte
    clc
    rts
native_local_emit_function_return:
    lda #<native_local_function_return_bytes
    ldy #>native_local_function_return_bytes
    ldx #(native_local_function_return_bytes_end-native_local_function_return_bytes)
    jsr native_local_emit_const_bytes
    clc
    rts

native_local_emit_data:
    lda #$00
    sta entry_index_data
native_local_emit_data_loop:
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp entry_index_data
    beq native_local_emit_data_pointer
    ldx entry_index_data
    jsr native_local_load_var_width_x
    cmp #$04
    php
    ldy #$01
    lda (ACTC_OVERLAY_WORK_ZP),y
    pha
    dey
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr native_local_emit_byte
    pla
    jsr native_local_emit_byte
    plp
    bne native_local_emit_data_next
    jsr native_local_emit_zero_word
native_local_emit_data_next:
    inc entry_index_data
    jmp native_local_emit_data_loop
native_local_emit_data_pointer:
    lda native_local_data_size_lo
    ora native_local_data_size_hi
    beq native_local_emit_data_done
native_local_emit_zero_word:
    lda #$00
    jsr native_local_emit_byte
    lda #$00
    jmp native_local_emit_byte
native_local_emit_data_done:
    rts

native_local_emit_const_bytes:
    sta native_local_const_ptr_lo
    sty native_local_const_ptr_hi
    stx native_local_const_len
    lda #$00
    sta native_local_const_index
native_local_emit_const_loop:
    lda native_local_const_index
    cmp native_local_const_len
    beq native_local_emit_const_done
    lda native_local_const_ptr_lo
    sta ACTC_OVERLAY_WORK_ZP
    lda native_local_const_ptr_hi
    sta ACTC_OVERLAY_WORK_ZP+1
    ldy native_local_const_index
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr native_local_emit_byte
    inc native_local_const_index
    jmp native_local_emit_const_loop
native_local_emit_const_done:
    rts

native_local_emit_byte:
    sta native_local_machine_byte
    lda #' '
    jsr emit_char_overlay
    lda native_local_machine_byte
    jmp emit_hex_byte_overlay

native_local_emit_reloc_list:
    lda native_local_data_size_lo
    ora native_local_data_size_hi
    beq native_local_emit_reloc_procs
    lda #$03
    ldy #$00
    jsr native_local_emit_pointer_reloc
    lda #$09
    ldy #$00
    jsr native_local_emit_pointer_reloc
native_local_emit_reloc_procs:
    lda native_local_main_proc
    sta native_local_current_proc
native_local_emit_reloc_proc_loop:
    ldx native_local_current_proc
    lda native_local_proc_offset_lo,x
    sta native_local_reloc_offset_lo
    lda native_local_proc_offset_hi,x
    sta native_local_reloc_offset_hi
    cpx native_local_main_proc
    bne :+
    lda native_local_data_size_lo
    ora native_local_data_size_hi
    beq :+
    lda #13
    jsr native_local_add_reloc_offset
:   lda #$00
    sta native_local_body_pos
    sta native_local_control_depth
    sta native_local_label_count
.if ACTC_NATIVE_LOCAL_PARAM_BINDS
    lda #$01
    sta native_local_param_bind_phase
.endif
    ldx native_local_current_proc
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
    jsr native_local_load_current_machine
.endif
    jsr native_local_emit_reloc_body
    bcs native_local_emit_reloc_fail
    lda native_local_current_proc
    beq native_local_emit_data_reloc
    dec native_local_current_proc
    jmp native_local_emit_reloc_proc_loop

native_local_emit_data_reloc:
    lda native_local_data_size_lo
    ora native_local_data_size_hi
    beq native_local_emit_reloc_done
    clc
    lda native_local_total_code_lo
    adc native_local_data_size_lo
    sta native_local_temp_offset_lo
    lda native_local_total_code_hi
    adc native_local_data_size_hi
    tay
    lda native_local_temp_offset_lo
    jsr native_local_emit_reloc_prefix
    lda #<native_local_name_data
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>native_local_name_data
    sta ACTC_OVERLAY_SCAN_ZP+1
    jsr native_local_emit_named_target
native_local_emit_reloc_done:
    clc
    rts
native_local_emit_reloc_fail:
    sec
    rts

native_local_emit_reloc_body:
    ldy native_local_body_pos
    jsr emit_object_peek_payload_y
.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
    ldx native_local_current_machine
    beq native_local_reloc_normal_op
    cmp #$00
    beq native_local_reloc_machine_done
    cmp #'@'
    beq native_local_reloc_normal_op
    sec
    rts
native_local_reloc_normal_op:
.endif
.if ACTC_NATIVE_LOCAL_PARAM_BINDS
    cmp #'S'
    beq native_local_reloc_store
    ldx #$00
    stx native_local_param_bind_phase
.endif
    jsr native_local_classify_body_op
    bcs :+
    sec
    rts
:
    lda native_local_reloc_target_lo,x
    sta ACTC_OVERLAY_WORK_ZP
    lda native_local_reloc_target_hi,x
    sta ACTC_OVERLAY_WORK_ZP+1
    jmp (ACTC_OVERLAY_WORK_ZP)

native_local_reloc_target_lo:
    .byte <native_local_reloc_compare_found,<native_local_reloc_compare_found
    .byte <native_local_reloc_compare_found,<native_local_reloc_compare_found
    .byte <native_local_reloc_literal,<native_local_reloc_load,<native_local_reloc_store
    .byte <native_local_reloc_add_sub,<native_local_reloc_add_sub
    .byte <native_local_reloc_mul,<native_local_reloc_div
    .byte <native_local_reloc_print,<native_local_reloc_print_line
.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
    .byte <native_local_reloc_external_a_call,<native_local_reloc_external_xy_call
.endif
    .byte <native_local_reloc_external_call
.if ACTC_NATIVE_LOCAL_FIXED_ROUTINES
    .byte <native_local_reloc_fixed_call
.endif
.if ACTC_NATIVE_LOCAL_ASMBLOCK
    .byte <native_local_reloc_asmblock
.endif
    .byte <native_local_reloc_do,<native_local_reloc_else,<native_local_reloc_endif
    .byte <native_local_reloc_while_end,<native_local_reloc_while_end
    .byte <native_local_reloc_exit,<native_local_reloc_call,<native_local_reloc_body_done
native_local_reloc_target_hi:
    .byte >native_local_reloc_compare_found,>native_local_reloc_compare_found
    .byte >native_local_reloc_compare_found,>native_local_reloc_compare_found
    .byte >native_local_reloc_literal,>native_local_reloc_load,>native_local_reloc_store
    .byte >native_local_reloc_add_sub,>native_local_reloc_add_sub
    .byte >native_local_reloc_mul,>native_local_reloc_div
    .byte >native_local_reloc_print,>native_local_reloc_print_line
.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
    .byte >native_local_reloc_external_a_call,>native_local_reloc_external_xy_call
.endif
    .byte >native_local_reloc_external_call
.if ACTC_NATIVE_LOCAL_FIXED_ROUTINES
    .byte >native_local_reloc_fixed_call
.endif
.if ACTC_NATIVE_LOCAL_ASMBLOCK
    .byte >native_local_reloc_asmblock
.endif
    .byte >native_local_reloc_do,>native_local_reloc_else,>native_local_reloc_endif
    .byte >native_local_reloc_while_end,>native_local_reloc_while_end
    .byte >native_local_reloc_exit,>native_local_reloc_call,>native_local_reloc_body_done
native_local_reloc_target_end:
.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
native_local_reloc_machine_done:
    jmp native_local_reloc_body_done
.endif
native_local_reloc_compare_found:
    lda native_local_compare_size_table,x
    sta native_local_instruction_size
    lda native_local_compare_addend_table,x
    jmp native_local_reloc_compare
native_local_reloc_literal:
    inc native_local_body_pos
    inc native_local_body_pos
    lda #$06
    jsr native_local_add_reloc_offset
    jmp native_local_emit_reloc_body
native_local_reloc_load:
    inc native_local_body_pos
    inc native_local_body_pos
    lda #$09
    jsr native_local_add_reloc_offset
    jmp native_local_emit_reloc_body
native_local_reloc_store:
    inc native_local_body_pos
    inc native_local_body_pos
.if ACTC_NATIVE_LOCAL_PARAM_BINDS
    lda native_local_param_bind_phase
    beq :+
    jsr native_local_param_bind_size
    jsr native_local_add_reloc_offset
    jmp native_local_emit_reloc_body
:
.endif
    lda #11
    jsr native_local_add_reloc_offset
    jmp native_local_emit_reloc_body

native_local_reloc_add_sub:
    inc native_local_body_pos
    lda #19
    jsr native_local_add_reloc_offset
    jmp native_local_emit_reloc_body

native_local_reloc_mul:
    ldx native_local_mul_index
    jmp native_local_reloc_mul_div
native_local_reloc_div:
    ldx native_local_div_index
native_local_reloc_mul_div:
    lda #18
    jsr native_local_emit_import_reloc_addend
    inc native_local_body_pos
    lda #23
    jsr native_local_add_reloc_offset
    jmp native_local_emit_reloc_body

native_local_reloc_print:
    lda #6
    bne native_local_reloc_print_common
native_local_reloc_print_line:
    lda #11
native_local_reloc_print_common:
    sta native_local_instruction_size
    ldx native_local_print_index
    lda #4
    jsr native_local_emit_import_reloc_addend
    inc native_local_body_pos
    lda native_local_instruction_size
    jsr native_local_add_reloc_offset
    jmp native_local_emit_reloc_body

native_local_reloc_external_call:
    jsr native_local_read_selector
    ldx native_local_operand_index
    lda #$01
    jsr native_local_emit_import_reloc_addend
    lda #$03
    jsr native_local_add_reloc_offset
    jmp native_local_emit_reloc_body

.if ACTC_NATIVE_LOCAL_FIXED_ROUTINES
native_local_reloc_fixed_call:
    jsr native_local_read_selector
    ldx native_local_operand_index
    lda #ACTC_OVERLAY_CTX_PREPARE_FIXED_CALL_FN_LO
    jsr call_indexed_context_function
    bcs :+
    jmp native_local_reloc_bad
:
    sta native_local_machine_meta
    sty native_local_instruction_size
    lda #ACTC_OVERLAY_CTX_FIXED_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #ACTC_FIXED_META_BINDING
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp #ACTC_FIXED_BINDING_LINKED
    bne native_local_reloc_fixed_call_advance
    ldy #ACTC_FIXED_META_ADDRESS_LO
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_local_fixed_reloc_addend_lo
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_local_fixed_reloc_addend_hi
    ldy #ACTC_FIXED_META_RESERVED
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_local_fixed_reloc_target
    lda #$00
    sta native_local_fixed_return_size
    lda native_local_machine_meta
    bpl native_local_reloc_fixed_call_offset
    and #ACTC_PROC_META_BYTE_RETURN
    beq native_local_reloc_fixed_call_word_return
    lda #$05
    bne native_local_reloc_fixed_call_store_return
native_local_reloc_fixed_call_word_return:
    lda #$03
native_local_reloc_fixed_call_store_return:
    sta native_local_fixed_return_size
native_local_reloc_fixed_call_offset:
    sec
    lda native_local_instruction_size
    sbc native_local_fixed_return_size
    sbc #$02
    clc
    adc native_local_reloc_offset_lo
    sta native_local_temp_offset_lo
    lda native_local_reloc_offset_hi
    adc #$00
    tay
    lda native_local_temp_offset_lo
    jsr native_local_emit_reloc_prefix
    ldx native_local_fixed_reloc_target
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr native_local_emit_named_target_text
    jsr native_local_emit_fixed_reloc_addend
    jsr emit_newline
    jsr native_local_restore_body_scan
native_local_reloc_fixed_call_advance:
    lda native_local_instruction_size
    jsr native_local_add_reloc_offset
    jmp native_local_emit_reloc_body

native_local_emit_fixed_reloc_addend:
    lda native_local_fixed_reloc_addend_lo
    ora native_local_fixed_reloc_addend_hi
    beq native_local_emit_fixed_reloc_addend_done
    lda #' '
    jsr emit_char_overlay
    lda native_local_fixed_reloc_addend_hi
    bpl native_local_emit_fixed_reloc_addend_positive
    lda #'-'
    jsr emit_char_overlay
    sec
    lda #$00
    sbc native_local_fixed_reloc_addend_lo
    sta native_local_fixed_reloc_addend_lo
    lda #$00
    sbc native_local_fixed_reloc_addend_hi
    sta native_local_fixed_reloc_addend_hi
native_local_emit_fixed_reloc_addend_positive:
    lda native_local_fixed_reloc_addend_lo
    ldy native_local_fixed_reloc_addend_hi
    jmp emit_word_decimal
native_local_emit_fixed_reloc_addend_done:
    rts
.endif

.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
native_local_reloc_external_a_call:
    jsr native_local_read_selector
    ldx native_local_operand_index
    lda #$03
    jsr native_local_emit_import_reloc_addend
    lda #$05
    jsr native_local_add_reloc_offset
    jmp native_local_emit_reloc_body
.endif

.if ACTC_NATIVE_LOCAL_ASMBLOCK
native_local_reloc_bad_near_asmblock:
    jmp native_local_reloc_bad
native_local_reloc_asmblock:
    jsr native_local_read_selector
    lda native_local_operand_index
    sta native_local_asmblock_index
    jsr native_local_load_asmblock_page
    bcs native_local_reloc_bad_near_asmblock
    lda #$00
    sta native_local_asm_reloc_index
native_local_reloc_asmblock_loop:
    lda native_local_asm_reloc_index
    cmp ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_RELOC_COUNT
    beq native_local_reloc_asmblock_done
    asl a
    tay
    clc
    lda ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_RELOC_BASE,y
    adc native_local_reloc_offset_lo
    sta native_local_temp_offset_lo
    lda native_local_reloc_offset_hi
    adc #$00
    tay
    lda native_local_temp_offset_lo
    jsr native_local_emit_reloc_prefix
    lda native_local_asm_reloc_index
    asl a
    tay
    iny
    lda ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_RELOC_BASE,y
    sta native_local_asm_reloc_target
    and #ACTC_ASMBLOCK_RELOC_KIND_MASK
    sta native_local_asm_reloc_kind
    lda native_local_asm_reloc_target
    bmi native_local_reloc_asmblock_var
    and #ACTC_ASMBLOCK_RELOC_EXPORT
    bne native_local_reloc_asmblock_export
    lda native_local_asm_reloc_target
    and #ACTC_ASMBLOCK_RELOC_TARGET_MASK
    sta native_local_saved_label
    ldx native_local_asmblock_index
    clc
    lda native_local_saved_label
    adc ACTC_ASMBLOCK_LABEL_INDEX_BASE,x
    tax
    jsr native_local_build_label_name
    jmp native_local_reloc_asmblock_target
native_local_reloc_asmblock_export:
    lda native_local_asm_reloc_target
    and #ACTC_ASMBLOCK_RELOC_INDEX_MASK
    tax
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jmp native_local_reloc_asmblock_target
native_local_reloc_asmblock_var:
    and #ACTC_ASMBLOCK_RELOC_TARGET_MASK
    sta native_local_asm_var_index
    jsr native_local_build_asm_var_name
native_local_reloc_asmblock_target:
    jsr native_local_emit_asm_reloc_kind
    jsr native_local_emit_named_target_text
    ldx native_local_asm_reloc_index
    lda ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_RELOC_ADDEND_BASE,x
    jsr native_local_emit_asm_reloc_addend
    jsr emit_newline
    inc native_local_asm_reloc_index
    jmp native_local_reloc_asmblock_loop
native_local_reloc_asmblock_done:
    lda ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_CODE_LEN
    jsr native_local_add_reloc_offset
    jsr native_local_restore_body_scan
    jmp native_local_emit_reloc_body

native_local_emit_asm_reloc_kind:
    lda native_local_asm_reloc_kind
    beq native_local_emit_asm_reloc_kind_done
    cmp #ACTC_ASMBLOCK_RELOC_LOW
    beq native_local_emit_asm_reloc_kind_low
    cmp #ACTC_ASMBLOCK_RELOC_HIGH
    bne native_local_emit_asm_reloc_kind_bad
    lda #'h'
    bne native_local_emit_asm_reloc_kind_char
native_local_emit_asm_reloc_kind_low:
    lda #'l'
native_local_emit_asm_reloc_kind_char:
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
native_local_emit_asm_reloc_kind_done:
    rts
native_local_emit_asm_reloc_kind_bad:
    jmp native_local_reloc_bad

native_local_emit_asm_reloc_addend:
    beq native_local_emit_asm_reloc_addend_done
    pha
    lda #' '
    jsr emit_char_overlay
    pla
    bpl native_local_emit_asm_reloc_addend_magnitude
    pha
    lda #'-'
    jsr emit_char_overlay
    pla
    eor #$FF
    clc
    adc #$01
native_local_emit_asm_reloc_addend_magnitude:
    ldy #$00
    jsr emit_word_decimal
native_local_emit_asm_reloc_addend_done:
    rts
.endif

.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
native_local_reloc_external_xy_call:
    jsr native_local_read_selector
    ldx native_local_operand_index
    lda #$05
    jsr native_local_emit_import_reloc_addend
    lda #$07
    jsr native_local_add_reloc_offset
    jmp native_local_emit_reloc_body
.endif

native_local_reloc_do:
    jsr native_local_allocate_label
    bcc native_local_reloc_bad_near_compare
    ldx native_local_control_depth
    sta native_local_control_target,x
    lda #$FF
    sta native_local_control_end,x
    lda #NATIVE_LOCAL_CONTROL_DO
    sta native_local_control_kind,x
    inc native_local_control_depth
    inc native_local_body_pos
    jmp native_local_emit_reloc_body

native_local_reloc_exit:
    jsr native_local_read_selector
    bcc native_local_reloc_bad_near_compare
    jsr native_local_ensure_exit_label
    bcc native_local_reloc_bad_near_compare
    lda #$01
    jsr native_local_reloc_label_at_addend
    lda #$03
    jsr native_local_add_reloc_offset
    jmp native_local_emit_reloc_body

native_local_reloc_bad_near_compare:
    jmp native_local_reloc_bad
native_local_reloc_compare:
    sta native_local_compare_addend
    ldy native_local_body_pos
    iny
    jsr emit_object_peek_payload_y
    cmp #'p'
    beq native_local_reloc_compare_inverse_suffix
    cmp #'t'
    beq :+
    lda #$02
    bne native_local_reloc_compare_have_advance
:   lda #$03
native_local_reloc_compare_have_advance:
    sta native_local_compare_advance
    ldy native_local_body_pos
    iny
    jsr emit_object_peek_payload_y
    jmp native_local_reloc_compare_dispatch_suffix
native_local_reloc_compare_inverse_suffix:
    ldy native_local_body_pos
    iny
    iny
    iny
    iny
    jsr emit_object_peek_payload_y
    cmp #'t'
    beq :+
    lda #$05
    bne native_local_reloc_compare_inverse_have_advance
:   lda #$06
native_local_reloc_compare_inverse_have_advance:
    sta native_local_compare_advance
    ldy native_local_body_pos
    iny
    iny
    iny
    iny
    jsr emit_object_peek_payload_y
native_local_reloc_compare_dispatch_suffix:
    cmp #'h'
    beq native_local_reloc_compare_if
    cmp #'f'
    beq native_local_reloc_compare_while
    cmp #'t'
    bne native_local_reloc_bad_near_compare
    ldx native_local_control_depth
    beq native_local_reloc_bad_near_compare
    dex
    lda native_local_control_kind,x
    cmp #NATIVE_LOCAL_CONTROL_DO
    bne native_local_reloc_bad_near_compare
    lda native_local_control_target,x
    sta native_local_saved_label
    stx native_local_control_depth
    lda native_local_compare_addend
    jsr native_local_reloc_label_at_addend
    lda native_local_instruction_size
    jsr native_local_add_reloc_offset
    jsr native_local_advance_compare_body
    jmp native_local_emit_reloc_body
native_local_reloc_compare_while:
    ldx native_local_control_depth
    beq native_local_reloc_bad_near_if
    dex
    lda native_local_control_kind,x
    cmp #NATIVE_LOCAL_CONTROL_DO
    bne native_local_reloc_bad_near_if
    jsr native_local_allocate_label
    bcc native_local_reloc_bad_near_if
    sta native_local_saved_label
    sta native_local_control_end,x
    lda #NATIVE_LOCAL_CONTROL_WHILE
    sta native_local_control_kind,x
    lda native_local_compare_addend
    jsr native_local_reloc_label_at_addend
    lda native_local_instruction_size
    jsr native_local_add_reloc_offset
    jsr native_local_advance_compare_body
    jmp native_local_emit_reloc_body
native_local_reloc_bad_near_if:
    jmp native_local_reloc_bad
native_local_reloc_compare_if:
    jsr native_local_allocate_label
    bcc native_local_reloc_bad_near_if
    sta native_local_saved_label
    ldx native_local_control_depth
    sta native_local_control_target,x
    lda #$FF
    sta native_local_control_end,x
    lda #NATIVE_LOCAL_CONTROL_IF
    sta native_local_control_kind,x
    inc native_local_control_depth
    lda native_local_compare_addend
    jsr native_local_reloc_label_at_addend
    lda native_local_instruction_size
    jsr native_local_add_reloc_offset
    jsr native_local_advance_compare_body
    jmp native_local_emit_reloc_body

native_local_reloc_else:
    ldx native_local_control_depth
    beq native_local_reloc_bad_near_if
    dex
    lda native_local_control_kind,x
    cmp #NATIVE_LOCAL_CONTROL_IF
    bne native_local_reloc_bad_near_if
    txa
    pha
    jsr native_local_allocate_label
    bcc native_local_reloc_else_bad_pop
    sta native_local_saved_label
    pla
    tax
    lda native_local_saved_label
    sta native_local_control_end,x
    lda #$01
    jsr native_local_reloc_label_at_addend
    lda #$03
    jsr native_local_add_reloc_offset
    inc native_local_body_pos
    jmp native_local_emit_reloc_body
native_local_reloc_else_bad_pop:
    pla
    jmp native_local_reloc_bad

native_local_reloc_endif:
    ldx native_local_control_depth
    beq native_local_reloc_bad_near_if
    dex
    stx native_local_control_depth
    inc native_local_body_pos
    jmp native_local_emit_reloc_body

native_local_reloc_while_end:
    ldx native_local_control_depth
    beq native_local_reloc_bad_near_call
    dex
    lda native_local_control_kind,x
    and #$FE
    cmp #NATIVE_LOCAL_CONTROL_DO
    bne native_local_reloc_bad_near_call
    lda native_local_control_target,x
    sta native_local_saved_label
    stx native_local_control_depth
    lda #$01
    jsr native_local_reloc_label_at_addend
    lda #$03
    jsr native_local_add_reloc_offset
    inc native_local_body_pos
    jmp native_local_emit_reloc_body

native_local_reloc_bad_near_call:
    jmp native_local_reloc_bad
native_local_reloc_call:
    jsr native_local_read_selector
    ldx native_local_operand_index
.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
    jsr native_local_load_proc_meta_byte_x
    sta native_local_machine_meta
    and #ACTC_PROC_META_MACHINE
    bne native_local_reloc_machine_call
    lda native_local_machine_meta
.else
    jsr native_local_load_proc_meta_byte_x
.endif
    asl
    lda #$03
    bcc native_local_reloc_call_size
    asl
native_local_reloc_call_size:
    sta native_local_instruction_size
    clc
    lda native_local_reloc_offset_lo
    adc #$01
    sta native_local_temp_offset_lo
    lda native_local_reloc_offset_hi
    adc #$00
    tay
    lda native_local_temp_offset_lo
    jsr native_local_emit_reloc_prefix
native_local_reloc_call_emit_target:
    ldx native_local_operand_index
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr native_local_emit_named_target
    jsr native_local_restore_body_scan
    lda native_local_instruction_size
    jsr native_local_add_reloc_offset
    jmp native_local_emit_reloc_body

.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
native_local_reloc_machine_call:
    jsr native_local_prepare_machine_call
    clc
    lda native_local_reloc_offset_lo
    adc native_local_machine_setup_size
    adc #$01
    sta native_local_temp_offset_lo
    lda native_local_reloc_offset_hi
    adc #$00
    tay
    lda native_local_temp_offset_lo
    jsr native_local_emit_reloc_prefix
    jmp native_local_reloc_call_emit_target
.endif

native_local_reloc_body_done:
    clc
    rts
native_local_reloc_bad:
    sec
    rts

native_local_reloc_label_at_addend:
    clc
    adc native_local_reloc_offset_lo
    sta native_local_temp_offset_lo
    lda native_local_reloc_offset_hi
    adc #$00
    tay
    lda native_local_temp_offset_lo
    jsr native_local_emit_reloc_prefix
    ldx native_local_saved_label
    jsr native_local_build_label_name
    jsr native_local_emit_named_target
    jmp native_local_restore_body_scan

native_local_emit_import_reloc_addend:
    stx native_local_reloc_import_index
    clc
    adc native_local_reloc_offset_lo
    sta native_local_temp_offset_lo
    lda native_local_reloc_offset_hi
    adc #$00
    tay
    lda native_local_temp_offset_lo
    jsr native_local_emit_reloc_prefix
    lda #'u'
    jsr emit_char_overlay
    lda native_local_reloc_import_index
    jsr emit_object_selector_overlay
    jsr emit_newline
    jmp native_local_restore_body_scan

native_local_restore_body_scan:
    ldx native_local_current_proc
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jmp load_resident_body_ptr_to_scan_zp

native_local_emit_pointer_reloc:
    jsr native_local_emit_reloc_prefix
    lda #<native_local_name_pointer
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>native_local_name_pointer
    sta ACTC_OVERLAY_SCAN_ZP+1
    jmp native_local_emit_named_target

native_local_emit_reloc_prefix:
    sta native_local_temp_offset_lo
    sty native_local_temp_offset_hi
    lda #'r'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda native_local_temp_offset_lo
    ldy native_local_temp_offset_hi
    jsr emit_word_decimal
    lda #' '
    jmp emit_char_overlay

native_local_emit_named_target:
    jsr native_local_emit_named_target_text
    jmp emit_newline
native_local_emit_named_target_text:
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jmp emit_lower_scan_zp_string

native_local_add_reloc_offset:
    clc
    adc native_local_reloc_offset_lo
    sta native_local_reloc_offset_lo
    bcc :+
    inc native_local_reloc_offset_hi
:   rts

native_local_prologue:
    .byte $A2,$00,$BD,$00,$00,$85,$06,$E8,$BD,$00,$00,$85,$07
native_local_prologue_end:
native_local_load_tail:
    .byte $B1,$06,$48,$C8,$B1,$06,$48
native_local_load_tail_end:
native_local_store_head:
    .byte $68,$AA,$68,$A0
native_local_store_head_end:
native_local_store_tail:
    .byte $91,$06,$C8,$8A,$91,$06
native_local_store_tail_end:
.if ACTC_NATIVE_LOCAL_PARAM_BINDS
native_local_param_return_save:
    .byte $68,$AA,$68,$85,$04
native_local_param_return_save_end:
native_local_param_store_head:
    .byte $68,$A0
native_local_param_store_head_end:
native_local_param_store_tail:
    .byte $91,$06,$68,$88,$91,$06
native_local_param_store_tail_end:
native_local_param_return_restore:
    .byte $A5,$04,$48,$8A,$48
native_local_param_return_restore_end:
.endif
native_local_add_bytes:
    .byte $68,$85,$05,$68,$85,$04,$68,$85,$03,$68,$18,$65,$04,$48,$A5,$03,$65,$05,$48
native_local_sub_bytes:
    .byte $68,$85,$05,$68,$85,$04,$68,$85,$03,$68,$38,$E5,$04,$48,$A5,$03,$E5,$05,$48
native_local_mul_div_bytes:
    .byte $A9,$04,$85,$02,$A9,$00,$85,$03,$68,$85,$05,$68,$85,$04,$68,$AA,$68,$20,$00,$00,$48,$8A,$48
native_local_print_bytes:
    .byte $68,$AA,$68,$20,$00,$00
native_local_newline_bytes:
    .byte $A9,$0D,$20,$D2,$FF
native_local_equal_bytes:
    .byte $68,$85,$05,$68,$85,$04,$68,$85,$03,$68,$C5,$04,$D0,$06,$A5,$03,$C5,$05,$F0,$03,$4C,$00,$00
native_local_equal_bytes_end:
native_local_not_equal_bytes:
    .byte $68,$85,$05,$68,$85,$04,$68,$85,$03,$68,$C5,$04,$D0,$09,$A5,$03,$C5,$05,$D0,$03,$4C,$00,$00
native_local_not_equal_bytes_end:
native_local_less_bytes:
    .byte $68,$85,$05,$68,$85,$04,$68,$AA,$68,$E4,$05,$90,$09,$D0,$04,$C5,$04,$90,$03,$4C,$00,$00
native_local_less_bytes_end:
native_local_greater_bytes:
    .byte $68,$85,$05,$68,$85,$04,$68,$AA,$68,$E4,$05,$90,$08,$D0,$09,$C5,$04,$90,$02,$D0,$03,$4C,$00,$00
native_local_greater_bytes_end:
native_local_greater_equal_bytes:
    .byte $68,$85,$05,$68,$85,$04,$68,$AA,$68,$E4,$05,$90,$06,$D0,$07,$C5,$04,$B0,$03,$4C,$00,$00
native_local_greater_equal_bytes_end:
native_local_less_equal_bytes:
    .byte $68,$85,$05,$68,$85,$04,$68,$AA,$68,$E4,$05,$90,$0B,$D0,$06,$C5,$04,$90,$05,$F0,$03,$4C,$00,$00
native_local_less_equal_bytes_end:
; One classifier replaces three long opcode comparison chains. The first four
; indices intentionally retain the comparison-table order used by each phase.
native_local_classify_body_op:
    ldx #(native_local_body_op_table_end-native_local_body_op_table)-1
native_local_classify_body_op_loop:
    cmp native_local_body_op_table,x
    beq native_local_classify_body_op_found
    dex
    bpl native_local_classify_body_op_loop
    clc
    rts
native_local_classify_body_op_found:
    sec
    rts

native_local_body_op_table:
    .byte 'q','n','l','g'
    .byte 'p','L','S','a','m','*','/','y','z'
.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
    .byte 'A','U'
.endif
    .byte 'u'
.if ACTC_NATIVE_LOCAL_FIXED_ROUTINES
    .byte ACTC_BODY_OP_FIXED_CALL
.endif
.if ACTC_NATIVE_LOCAL_ASMBLOCK
    .byte '@'
.endif
    .byte 'd','w','v','x','o','X','c','r'
native_local_body_op_table_end:

.assert native_local_analyze_target_hi-native_local_analyze_target_lo = native_local_body_op_table_end-native_local_body_op_table, error, "analyze opcode table mismatch"
.assert native_local_analyze_target_end-native_local_analyze_target_hi = native_local_body_op_table_end-native_local_body_op_table, error, "analyze opcode high table mismatch"
.assert native_local_emit_target_hi-native_local_emit_target_lo = native_local_body_op_table_end-native_local_body_op_table, error, "emit opcode table mismatch"
.assert native_local_emit_target_end-native_local_emit_target_hi = native_local_body_op_table_end-native_local_body_op_table, error, "emit opcode high table mismatch"
.assert native_local_reloc_target_hi-native_local_reloc_target_lo = native_local_body_op_table_end-native_local_body_op_table, error, "reloc opcode table mismatch"
.assert native_local_reloc_target_end-native_local_reloc_target_hi = native_local_body_op_table_end-native_local_body_op_table, error, "reloc opcode high table mismatch"

native_local_compare_size_table:
    .byte 23,23,22,24
native_local_compare_addend_table:
    .byte 21,21,20,22
native_local_compare_bytes_lo:
    .byte <native_local_equal_bytes,<native_local_not_equal_bytes
    .byte <native_local_less_bytes,<native_local_greater_bytes
    .byte <native_local_greater_equal_bytes,<native_local_less_equal_bytes
native_local_compare_bytes_hi:
    .byte >native_local_equal_bytes,>native_local_not_equal_bytes
    .byte >native_local_less_bytes,>native_local_greater_bytes
    .byte >native_local_greater_equal_bytes,>native_local_less_equal_bytes
native_local_compare_bytes_len:
    .byte native_local_equal_bytes_end-native_local_equal_bytes
    .byte native_local_not_equal_bytes_end-native_local_not_equal_bytes
    .byte native_local_less_bytes_end-native_local_less_bytes
    .byte native_local_greater_bytes_end-native_local_greater_bytes
    .byte native_local_greater_equal_bytes_end-native_local_greater_equal_bytes
    .byte native_local_less_equal_bytes_end-native_local_less_equal_bytes
native_local_jump_bytes:
    .byte $4C,$00,$00
native_local_jump_bytes_end:
native_local_function_call_bytes:
    .byte $20,$00,$00,$48,$8A,$48
native_local_function_call_bytes_end:
.if ACTC_NATIVE_LOCAL_MACHINE_ROUTINES
native_local_byte_function_call_bytes:
    .byte $20,$00,$00,$A2,$00,$48,$8A,$48
native_local_byte_function_call_bytes_end:
.endif
native_local_function_return_bytes:
    .byte $68,$AA,$68,$60
native_local_function_return_bytes_end:
.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
native_local_a_byte_call_bytes:
    .byte $68,$68,$20,$00,$00
native_local_a_byte_call_bytes_end:
native_local_xy_word_call_bytes:
    .byte $68,$A8,$68,$AA,$20,$00,$00
native_local_xy_word_call_bytes_end:
.endif
native_local_exit_bytes:
    .byte $A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF
native_local_exit_bytes_end:

native_local_name_data:
    .asciiz "__idata"
native_local_name_pointer:
    .asciiz "__iptr"
native_local_name_mul:
    .asciiz "rt_i_mul"
native_local_name_div:
    .asciiz "rt_i_div"
native_local_name_print:
    .asciiz "rt_print_i"
native_local_helper_name_lo:
    .byte <native_local_name_mul,<native_local_name_div,<native_local_name_print
native_local_helper_name_hi:
    .byte >native_local_name_mul,>native_local_name_div,>native_local_name_print
native_local_label_name:
    .byte '_','_','p','0','l','0',$00
.if ACTC_NATIVE_LOCAL_ASMBLOCK
native_local_asm_var_name:
    .byte '_','_','v','0',$00
.endif

.segment "BSS"

native_local_proc_count:
    .res 1
native_local_main_proc:
    .res 1
native_local_current_proc:
    .res 1
native_local_proc_offset_lo:
    .res NATIVE_LOCAL_PROC_MAX
native_local_proc_offset_hi:
    .res NATIVE_LOCAL_PROC_MAX
native_local_proc_size_lo:
    .res NATIVE_LOCAL_PROC_MAX
native_local_proc_size_hi:
    .res NATIVE_LOCAL_PROC_MAX
native_local_proc_label_count:
    .res NATIVE_LOCAL_PROC_MAX
native_local_proc_debug_base:
    .res NATIVE_LOCAL_PROC_MAX
native_local_total_code_lo:
    .res 1
native_local_total_code_hi:
    .res 1
native_local_code_size_lo:
    .res 1
native_local_code_size_hi:
    .res 1
native_local_data_size_lo:
    .res 1
native_local_data_size_hi:
    .res 1
native_local_root_size_lo:
    .res 1
native_local_root_size_hi:
    .res 1
native_local_export_offset_lo:
    .res 1
native_local_export_offset_hi:
    .res 1
native_local_export_size_lo:
    .res 1
native_local_export_size_hi:
    .res 1
native_local_stack_depth:
    .res 1
native_local_control_depth:
    .res 1
native_local_control_kind:
    .res NATIVE_LOCAL_CONTROL_MAX
native_local_control_target:
    .res NATIVE_LOCAL_CONTROL_MAX
native_local_control_end:
    .res NATIVE_LOCAL_CONTROL_MAX
native_local_label_count:
    .res 1
native_local_label_index:
    .res 1
native_local_label_offset_lo:
    .res NATIVE_LOCAL_LABEL_MAX
native_local_label_offset_hi:
    .res NATIVE_LOCAL_LABEL_MAX
native_local_saved_label:
    .res 1
native_local_body_pos:
    .res 1
native_local_operand_index:
    .res 1
native_local_target_var:
    .res 1
native_local_var_offset:
    .res 1
native_local_lowering_seen:
    .res 1
native_local_single_proc_applicable:
    .res 1
native_local_arithmetic_seen:
    .res 1
native_local_while_seen:
    .res 1
native_local_used_helpers:
    .res 1
.if ACTC_NATIVE_LOCAL_RUNTIME_ARGS
native_local_runtime_arg_seen:
    .res 1
.endif
native_local_mul_index:
    .res 1
native_local_div_index:
    .res 1
native_local_print_index:
    .res 1
native_local_record_debug:
    .res 1
native_local_expected_debug_count:
    .res 1
native_local_debug_count:
    .res 1
native_int_debug_offsets_lo:
    .res ACTC_OVERLAY_BODY_OP_LIMIT
native_int_debug_offsets_hi:
    .res ACTC_OVERLAY_BODY_OP_LIMIT
native_local_marker_count:
    .res 1
native_local_const_ptr_lo:
    .res 1
native_local_const_ptr_hi:
    .res 1
native_local_const_len:
    .res 1
native_local_const_index:
    .res 1
native_local_machine_byte:
    .res 1
native_local_instruction_size:
    .res 1
native_local_compare_addend:
    .res 1
native_local_compare_ordered:
    .res 1
native_local_compare_advance:
    .res 1
native_local_compare_debug_remaining:
    .res 1
native_local_compare_index:
    .res 1
native_local_reloc_import_index:
    .res 1
native_local_reloc_offset_lo:
    .res 1
native_local_reloc_offset_hi:
    .res 1
native_local_temp_offset_lo:
    .res 1
native_local_temp_offset_hi:
    .res 1
.if ACTC_NATIVE_LOCAL_FIXED_ROUTINES
native_local_fixed_reloc_target:
    .res 1
native_local_fixed_reloc_addend_lo:
    .res 1
native_local_fixed_reloc_addend_hi:
    .res 1
native_local_fixed_return_size:
    .res 1
.endif
.if ACTC_NATIVE_LOCAL_ASMBLOCK
native_local_asm_reloc_target:
    .res 1
native_local_asm_reloc_kind:
    .res 1
.endif

.segment "CODE"
