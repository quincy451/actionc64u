; Compiler-owned native lowering for compact REAL control-flow proof families.

NATIVE_REAL_CONTROL_PLAIN = 1
NATIVE_REAL_CONTROL_ELSE = 2
NATIVE_REAL_CONTROL_NESTED = 3
NATIVE_REAL_CONTROL_DO_SIMPLE = 4
NATIVE_REAL_CONTROL_DO_BINARY = 5

NATIVE_REAL_CONTROL_PLAIN_CODE_SIZE = 112
NATIVE_REAL_CONTROL_ELSE_CODE_SIZE = 126
NATIVE_REAL_CONTROL_NESTED_CODE_SIZE = 146
NATIVE_REAL_CONTROL_DO_SIMPLE_CODE_SIZE = 132
NATIVE_REAL_CONTROL_DO_BINARY_CODE_SIZE = 174
NATIVE_REAL_CONTROL_SMALL_DATA_SIZE = 14
NATIVE_REAL_CONTROL_DO_BINARY_DATA_SIZE = 20

native_real_control_detect:
    lda #$00
    sta native_real_control_mode
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$01
    beq :+
    jmp native_real_control_detect_no
:
    lda #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    jsr load_context_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcs :+
    jmp native_real_control_detect_no
:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcs :+
    jmp native_real_control_detect_no
:
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$03
    beq native_real_control_detect_three_vars
    cmp #$04
    bne :+
    jmp native_real_control_detect_binary_vars
:
    jmp native_real_control_detect_no

native_real_control_detect_three_vars:
    lda #$04
    ldx #$00
    jsr native_real_control_var_x_has_type_a
    beq :+
    jmp native_real_control_detect_no
:
    lda #$04
    ldx #$01
    jsr native_real_control_var_x_has_type_a
    beq :+
    jmp native_real_control_detect_no
:
    lda #$02
    ldx #$02
    jsr native_real_control_var_x_has_type_a
    beq :+
    jmp native_real_control_detect_no
:
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$02
    bcs :+
    jmp native_real_control_detect_no
:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp

    lda #NATIVE_REAL_CONTROL_PLAIN
    sta native_real_control_mode
    lda #<native_real_control_plain_pattern
    ldy #>native_real_control_plain_pattern
    jsr native_real_control_match_pattern
    bcs native_real_control_detect_if_pattern_ok
    lda #NATIVE_REAL_CONTROL_ELSE
    sta native_real_control_mode
    lda #<native_real_control_else_pattern
    ldy #>native_real_control_else_pattern
    jsr native_real_control_match_pattern
    bcs native_real_control_detect_if_pattern_ok
    lda #NATIVE_REAL_CONTROL_NESTED
    sta native_real_control_mode
    lda #<native_real_control_nested_pattern
    ldy #>native_real_control_nested_pattern
    jsr native_real_control_match_pattern
    bcs native_real_control_detect_if_pattern_ok
    lda #NATIVE_REAL_CONTROL_DO_SIMPLE
    sta native_real_control_mode
    lda #<native_real_control_do_simple_pattern
    ldy #>native_real_control_do_simple_pattern
    jsr native_real_control_match_pattern
    bcc :+
    jmp native_real_control_detect_do_simple
:
    jmp native_real_control_detect_no

native_real_control_detect_if_pattern_ok:
    lda native_real_control_mode
    cmp #NATIVE_REAL_CONTROL_PLAIN
    beq native_real_control_detect_plain_ints
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$07
    bcs native_real_control_detect_load_values
    jmp native_real_control_detect_no
native_real_control_detect_plain_ints:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$06
    bcs native_real_control_detect_load_values
    jmp native_real_control_detect_no

native_real_control_detect_load_values:
    ldx #$01
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_if_no
    sta native_real_control_left
    ldx #$03
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_if_no
    sta native_real_control_right
    ldx #$04
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_if_no
    sta native_real_control_relation
    jsr native_real_control_map_relation
    bcc native_real_control_detect_if_no
    lda native_real_control_mode
    cmp #NATIVE_REAL_CONTROL_NESTED
    bne native_real_control_detect_store
    ldx #$05
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_if_no
    cmp native_real_control_relation
    bne native_real_control_detect_if_no
    ldx #$06
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_if_no
    sta native_real_control_store
    jmp native_real_control_detect_yes
native_real_control_detect_store:
    ldx #$05
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_if_no
    sta native_real_control_store
    lda native_real_control_mode
    cmp #NATIVE_REAL_CONTROL_ELSE
    beq :+
    jmp native_real_control_detect_yes
:
    ldx #$06
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_if_no
    sta native_real_control_else
    jmp native_real_control_detect_yes
native_real_control_detect_if_no:
    jmp native_real_control_detect_no

native_real_control_detect_do_simple:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$07
    bcs :+
    jmp native_real_control_detect_no
:
    ldx #$00
    jsr native_real_control_literal_x_is_zero
    bcs :+
    jmp native_real_control_detect_no
:
    ldx #$01
    jsr native_real_control_literal_x_is_zero
    bcs :+
    jmp native_real_control_detect_no
:
    ldx #$03
    jsr native_real_control_literal_x_is_zero
    bcs :+
    jmp native_real_control_detect_no
:
    lda #$00
    sta native_real_control_left
    ldx #$02
    jsr native_real_control_load_byte_literal
    bcs :+
    jmp native_real_control_detect_no
:
    sta native_real_control_right
    ldx #$04
    jsr native_real_control_load_byte_literal
    bcs :+
    jmp native_real_control_detect_no
:
    sta native_real_control_store
    ldx #$05
    jsr native_real_control_load_byte_literal
    bcs :+
    jmp native_real_control_detect_no
:
    sta native_real_control_relation
    jsr native_real_control_map_relation
    bcs :+
    jmp native_real_control_detect_no
:
    ldx #$06
    jsr native_real_control_load_byte_literal
    bcs :+
    jmp native_real_control_detect_no
:
    sta native_real_control_else
    jmp native_real_control_detect_yes

native_real_control_detect_binary_vars:
    lda #$04
    ldx #$00
    jsr native_real_control_var_x_has_type_a
    beq :+
    jmp native_real_control_detect_no
:
    lda #$04
    ldx #$01
    jsr native_real_control_var_x_has_type_a
    beq :+
    jmp native_real_control_detect_no
:
    lda #$04
    ldx #$02
    jsr native_real_control_var_x_has_type_a
    beq :+
    jmp native_real_control_detect_no
:
    lda #$02
    ldx #$03
    jsr native_real_control_var_x_has_type_a
    beq :+
    jmp native_real_control_detect_no
:
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$03
    bcs :+
    jmp native_real_control_detect_no
:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #NATIVE_REAL_CONTROL_DO_BINARY
    sta native_real_control_mode
    lda #$00
    sta native_real_control_layout
    lda #<native_real_control_do_binary_add_pattern
    ldy #>native_real_control_do_binary_add_pattern
    jsr native_real_control_match_pattern
    bcs native_real_control_detect_do_binary
    inc native_real_control_layout
    lda #<native_real_control_do_binary_sub_zero_pattern
    ldy #>native_real_control_do_binary_sub_zero_pattern
    jsr native_real_control_match_pattern
    bcs native_real_control_detect_do_binary
    inc native_real_control_layout
    lda #<native_real_control_do_binary_sub_nonzero_pattern
    ldy #>native_real_control_do_binary_sub_nonzero_pattern
    jsr native_real_control_match_pattern
    bcs native_real_control_detect_do_binary
    jmp native_real_control_detect_no

native_real_control_detect_do_binary:
    lda native_real_control_layout
    beq native_real_control_detect_do_binary_add
    cmp #$01
    beq native_real_control_detect_do_binary_sub_zero
    jmp native_real_control_detect_do_binary_sub_nonzero

native_real_control_detect_do_binary_add:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$07
    bcs :+
    jmp native_real_control_detect_no
:
    ldx #$00
    jsr native_real_control_literal_x_is_zero
    bcc native_real_control_detect_do_binary_add_no
    ldx #$01
    jsr native_real_control_literal_x_is_zero
    bcc native_real_control_detect_do_binary_add_no
    ldx #$03
    jsr native_real_control_literal_x_is_zero
    bcc native_real_control_detect_do_binary_add_no
    lda #$00
    sta native_real_control_left
    ldx #$02
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_do_binary_add_no
    sta native_real_control_right
    ldx #$04
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_do_binary_add_no
    sta native_real_control_store
    ldx #$05
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_do_binary_add_no
    sta native_real_control_relation
    ldx #$06
    jmp native_real_control_detect_do_binary_store_value
native_real_control_detect_do_binary_add_no:
    jmp native_real_control_detect_no

native_real_control_detect_do_binary_sub_zero:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$07
    bcs :+
    jmp native_real_control_detect_no
:
    ldx #$00
    jsr native_real_control_literal_x_is_zero
    bcc native_real_control_detect_do_binary_sub_zero_no
    ldx #$02
    jsr native_real_control_literal_x_is_zero
    bcc native_real_control_detect_do_binary_sub_zero_no
    ldx #$03
    jsr native_real_control_literal_x_is_zero
    bcc native_real_control_detect_do_binary_sub_zero_no
    ldx #$01
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_do_binary_sub_zero_no
    sta native_real_control_left
    lda #$00
    sta native_real_control_right
    ldx #$04
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_do_binary_sub_zero_no
    sta native_real_control_store
    ldx #$05
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_do_binary_sub_zero_no
    sta native_real_control_relation
    ldx #$06
    jmp native_real_control_detect_do_binary_store_value
native_real_control_detect_do_binary_sub_zero_no:
    jmp native_real_control_detect_no

native_real_control_detect_do_binary_sub_nonzero:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$08
    bcs :+
    jmp native_real_control_detect_no
:
    ldx #$00
    jsr native_real_control_literal_x_is_zero
    bcc native_real_control_detect_do_binary_sub_nonzero_no
    ldx #$02
    jsr native_real_control_literal_x_is_zero
    bcc native_real_control_detect_do_binary_sub_nonzero_no
    ldx #$04
    jsr native_real_control_literal_x_is_zero
    bcc native_real_control_detect_do_binary_sub_nonzero_no
    ldx #$01
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_do_binary_sub_nonzero_no
    sta native_real_control_left
    ldx #$03
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_do_binary_sub_nonzero_no
    sta native_real_control_right
    ldx #$05
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_do_binary_sub_nonzero_no
    sta native_real_control_store
    ldx #$06
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_do_binary_sub_nonzero_no
    sta native_real_control_relation
    ldx #$07
    jmp native_real_control_detect_do_binary_store_value
native_real_control_detect_do_binary_sub_nonzero_no:
    jmp native_real_control_detect_no
native_real_control_detect_do_binary_store_value:
    jsr native_real_control_load_byte_literal
    bcc native_real_control_detect_no
    sta native_real_control_else
    jsr native_real_control_map_relation
    bcc native_real_control_detect_no
native_real_control_detect_yes:
    sec
    rts
native_real_control_detect_no:
    lda #$00
    sta native_real_control_mode
    clc
    rts

native_real_control_literal_x_is_zero:
    jsr native_real_control_load_byte_literal
    bcc native_real_control_literal_x_is_zero_no
    cmp #$00
    bne native_real_control_literal_x_is_zero_no
    sec
    rts
native_real_control_literal_x_is_zero_no:
    clc
    rts

native_real_control_var_x_has_type_a:
    sta native_real_control_byte
    lda #ACTC_OVERLAY_CTX_LOAD_VAR_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp native_real_control_byte
    rts

native_real_control_match_pattern:
    sta ACTC_OVERLAY_WORK_ZP
    sty ACTC_OVERLAY_WORK_ZP+1
    lda #$00
    sta native_real_control_body_op
    ldy #$00
native_real_control_match_pattern_loop:
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp #'*'
    beq native_real_control_match_pattern_wild
    sta native_real_control_byte
    jsr emit_object_peek_payload_y
    cmp native_real_control_byte
    bne native_real_control_match_pattern_no
    lda native_real_control_byte
    beq native_real_control_match_pattern_yes
    iny
    bne native_real_control_match_pattern_loop
native_real_control_match_pattern_no:
    clc
    rts
native_real_control_match_pattern_wild:
    jsr emit_object_peek_payload_y
    sta native_real_control_byte
    lda native_real_control_body_op
    bne native_real_control_match_pattern_repeat
    lda native_real_control_byte
    cmp #'g'
    beq native_real_control_match_pattern_store
    cmp #'l'
    beq native_real_control_match_pattern_store
    cmp #'q'
    beq native_real_control_match_pattern_store
    cmp #'n'
    bne native_real_control_match_pattern_no
native_real_control_match_pattern_store:
    lda native_real_control_byte
    sta native_real_control_body_op
    iny
    bne native_real_control_match_pattern_loop
native_real_control_match_pattern_repeat:
    cmp native_real_control_byte
    bne native_real_control_match_pattern_no
    iny
    bne native_real_control_match_pattern_loop
native_real_control_match_pattern_yes:
    sec
    rts

native_real_control_load_byte_literal:
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$01
    lda (ACTC_OVERLAY_WORK_ZP),y
    bne native_real_control_load_byte_literal_no
    dey
    lda (ACTC_OVERLAY_WORK_ZP),y
    sec
    rts
native_real_control_load_byte_literal_no:
    clc
    rts

native_real_control_map_relation:
    lda native_real_control_body_op
    cmp #'g'
    bne native_real_control_map_relation_l
    lda native_real_control_relation
    cmp #$01
    beq native_real_control_map_gt
    cmp #$00
    beq native_real_control_map_ge
    clc
    rts
native_real_control_map_relation_l:
    cmp #'l'
    bne native_real_control_map_relation_q
    lda native_real_control_relation
    cmp #$01
    beq native_real_control_map_lt
    cmp #$02
    beq native_real_control_map_le
    clc
    rts
native_real_control_map_relation_q:
    cmp #'q'
    bne native_real_control_map_relation_n
    lda native_real_control_relation
    cmp #$01
    beq native_real_control_map_eq
    clc
    rts
native_real_control_map_relation_n:
    cmp #'n'
    bne native_real_control_map_relation_no
    lda native_real_control_relation
    cmp #$01
    beq native_real_control_map_ne
native_real_control_map_relation_no:
    clc
    rts
native_real_control_map_gt:
    lda #$01
    ldx #$D0
    bne native_real_control_map_store
native_real_control_map_ge:
    lda #$02
    ldx #$B0
    bne native_real_control_map_store
native_real_control_map_lt:
    lda #$FF
    ldx #$D0
    bne native_real_control_map_store
native_real_control_map_le:
    lda #$01
    ldx #$10
    bne native_real_control_map_store
native_real_control_map_eq:
    lda #$00
    ldx #$D0
    bne native_real_control_map_store
native_real_control_map_ne:
    lda #$00
    ldx #$F0
native_real_control_map_store:
    sta native_real_control_cmp
    stx native_real_control_skip
    sec
    rts

native_real_control_emit_debug_offset:
    ldx body_debug_index_data
    lda native_real_control_mode
    cmp #NATIVE_REAL_CONTROL_DO_SIMPLE
    beq native_real_control_emit_debug_offset_do_simple
    cmp #NATIVE_REAL_CONTROL_DO_BINARY
    beq native_real_control_emit_debug_offset_do_binary
    cmp #NATIVE_REAL_CONTROL_ELSE
    beq native_real_control_emit_debug_offset_else
    cmp #NATIVE_REAL_CONTROL_NESTED
    beq native_real_control_emit_debug_offset_nested
    lda native_real_control_plain_debug_offsets,x
    bne native_real_control_emit_debug_offset_ready
native_real_control_emit_debug_offset_else:
    lda native_real_control_else_debug_offsets,x
    bne native_real_control_emit_debug_offset_ready
native_real_control_emit_debug_offset_nested:
    lda native_real_control_nested_debug_offsets,x
    bne native_real_control_emit_debug_offset_ready
native_real_control_emit_debug_offset_do_simple:
    lda native_real_control_do_simple_debug_offsets,x
    bne native_real_control_emit_debug_offset_ready
native_real_control_emit_debug_offset_do_binary:
    lda native_real_control_do_binary_debug_offsets,x
native_real_control_emit_debug_offset_ready:
    ldy #$00
    jmp emit_word_decimal

native_real_control_emit_export_list:
    lda #$00
    sta word_value_lo
    sta word_value_hi
    jsr native_real_control_code_size
    sta native_real_control_byte
    jsr native_real_control_data_size
    clc
    adc native_real_control_byte
    ldx #$00
    jsr emit_machine_export_line
    jsr native_real_control_data_size
    tax
    lda #<native_real_control_name_data
    ldy #>native_real_control_name_data
    jsr native_real_control_emit_named_at_code
    lda native_real_control_mode
    cmp #NATIVE_REAL_CONTROL_DO_SIMPLE
    beq native_real_control_emit_do_simple_export_list
    cmp #NATIVE_REAL_CONTROL_DO_BINARY
    beq native_real_control_emit_do_binary_export_list
    lda #<native_real_control_name_a
    ldy #>native_real_control_name_a
    ldx #$04
    jsr native_real_control_emit_named_at_code
    lda #<native_real_control_name_b
    ldy #>native_real_control_name_b
    ldx #$04
    jsr native_real_control_emit_named_at_code_plus4
    lda #<native_real_control_name_y
    ldy #>native_real_control_name_y
    ldx #$02
    jsr native_real_control_emit_named_at_code_plus8
    lda #<native_real_control_name_y_hi
    ldy #>native_real_control_name_y_hi
    ldx #$01
    jsr native_real_control_emit_named_at_code_plus9
    lda #<native_real_control_name_pointer
    ldy #>native_real_control_name_pointer
    ldx #$04
    jmp native_real_control_emit_named_at_code_plus10

native_real_control_emit_do_simple_export_list:
    lda #<native_real_control_name_do_a
    ldy #>native_real_control_name_do_a
    ldx #$04
    jsr native_real_control_emit_named_at_code
    lda #<native_real_control_name_do_b
    ldy #>native_real_control_name_do_b
    ldx #$04
    jsr native_real_control_emit_named_at_code_plus4
    lda #<native_real_control_name_do_y
    ldy #>native_real_control_name_do_y
    ldx #$02
    jsr native_real_control_emit_named_at_code_plus8
    lda #<native_real_control_name_do_y_hi
    ldy #>native_real_control_name_do_y_hi
    ldx #$01
    jsr native_real_control_emit_named_at_code_plus9
    lda #<native_real_control_name_do_pointer
    ldy #>native_real_control_name_do_pointer
    ldx #$04
    jmp native_real_control_emit_named_at_code_plus10

native_real_control_emit_do_binary_export_list:
    lda #<native_real_control_name_do_a
    ldy #>native_real_control_name_do_a
    ldx #$04
    jsr native_real_control_emit_named_at_code
    lda #<native_real_control_name_do_b
    ldy #>native_real_control_name_do_b
    ldx #$04
    jsr native_real_control_emit_named_at_code_plus4
    lda #<native_real_control_name_do_c
    ldy #>native_real_control_name_do_c
    ldx #$04
    jsr native_real_control_emit_named_at_code_plus8
    lda #<native_real_control_name_do_y
    ldy #>native_real_control_name_do_y
    ldx #$02
    jsr native_real_control_emit_named_at_code_plus12
    lda #<native_real_control_name_do_y_hi
    ldy #>native_real_control_name_do_y_hi
    ldx #$01
    jsr native_real_control_emit_named_at_code_plus13
    lda #<native_real_control_name_do_pointer
    ldy #>native_real_control_name_do_pointer
    ldx #$06
    jmp native_real_control_emit_named_at_code_plus14

native_real_control_emit_named_at_code_plus14:
    pha
    jsr native_real_control_code_size
    clc
    adc #14
    bne native_real_control_emit_named_offset_ready
native_real_control_emit_named_at_code_plus13:
    pha
    jsr native_real_control_code_size
    clc
    adc #13
    bne native_real_control_emit_named_offset_ready
native_real_control_emit_named_at_code_plus12:
    pha
    jsr native_real_control_code_size
    clc
    adc #12
    bne native_real_control_emit_named_offset_ready

native_real_control_emit_named_at_code_plus10:
    pha
    jsr native_real_control_code_size
    clc
    adc #10
    bne native_real_control_emit_named_offset_ready
native_real_control_emit_named_at_code_plus9:
    pha
    jsr native_real_control_code_size
    clc
    adc #9
    bne native_real_control_emit_named_offset_ready
native_real_control_emit_named_at_code_plus8:
    pha
    jsr native_real_control_code_size
    clc
    adc #8
    bne native_real_control_emit_named_offset_ready
native_real_control_emit_named_at_code_plus4:
    pha
    jsr native_real_control_code_size
    clc
    adc #4
    bne native_real_control_emit_named_offset_ready
native_real_control_emit_named_at_code:
    pha
    jsr native_real_control_code_size
native_real_control_emit_named_offset_ready:
    sta word_value_lo
    stx native_real_control_export_size
    pla
    sta ACTC_OVERLAY_SCAN_ZP
    sty ACTC_OVERLAY_SCAN_ZP+1
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr emit_scan_zp_string
    lda #' '
    jsr emit_char_overlay
    lda word_value_lo
    ldy #$00
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda native_real_control_export_size
    ldy #$00
    jsr emit_word_decimal
    jmp emit_newline

native_real_control_code_size:
    lda native_real_control_mode
    cmp #NATIVE_REAL_CONTROL_DO_SIMPLE
    beq native_real_control_code_size_do_simple
    cmp #NATIVE_REAL_CONTROL_DO_BINARY
    beq native_real_control_code_size_do_binary
    cmp #NATIVE_REAL_CONTROL_ELSE
    beq native_real_control_code_size_else
    cmp #NATIVE_REAL_CONTROL_NESTED
    beq native_real_control_code_size_nested
    lda #NATIVE_REAL_CONTROL_PLAIN_CODE_SIZE
    rts
native_real_control_code_size_else:
    lda #NATIVE_REAL_CONTROL_ELSE_CODE_SIZE
    rts
native_real_control_code_size_nested:
    lda #NATIVE_REAL_CONTROL_NESTED_CODE_SIZE
    rts
native_real_control_code_size_do_simple:
    lda #NATIVE_REAL_CONTROL_DO_SIMPLE_CODE_SIZE
    rts
native_real_control_code_size_do_binary:
    lda #NATIVE_REAL_CONTROL_DO_BINARY_CODE_SIZE
    rts

native_real_control_data_size:
    lda native_real_control_mode
    cmp #NATIVE_REAL_CONTROL_DO_BINARY
    beq :+
    lda #NATIVE_REAL_CONTROL_SMALL_DATA_SIZE
    rts
:
    lda #NATIVE_REAL_CONTROL_DO_BINARY_DATA_SIZE
    rts

native_real_control_emit_body_marker_list:
    lda #'b'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #'u'
    jsr emit_char_overlay
    lda #'0'
    jsr emit_char_overlay
    lda #'u'
    jsr emit_char_overlay
    lda #'1'
    jsr emit_char_overlay
    lda native_real_control_mode
    cmp #NATIVE_REAL_CONTROL_DO_BINARY
    bne :+
    lda #'u'
    jsr emit_char_overlay
    lda #'2'
    jsr emit_char_overlay
:
    lda #'M'
    jsr emit_char_overlay
    jsr emit_newline
    lda #$06
    ldx native_real_control_mode
    cpx #NATIVE_REAL_CONTROL_DO_BINARY
    bne :+
    lda #$07
:
    sta native_real_control_count
native_real_control_emit_body_marker_loop:
    jsr emit_machine_body_marker_line
    dec native_real_control_count
    bne native_real_control_emit_body_marker_loop
    rts

native_real_control_emit_machine_code_list:
    lda #'m'
    jsr emit_char_overlay
    lda native_real_control_mode
    cmp #NATIVE_REAL_CONTROL_DO_SIMPLE
    bne :+
    jmp native_real_control_emit_do_simple_machine_code
:
    cmp #NATIVE_REAL_CONTROL_DO_BINARY
    bne :+
    jmp native_real_control_emit_do_binary_machine_code
:
    lda #$00
    ldx #$02
    jsr native_real_control_emit_pointer_setup
    lda native_real_control_left
    jsr native_real_control_emit_conversion
    lda #$02
    ldx #$02
    jsr native_real_control_emit_pointer_setup
    lda native_real_control_right
    jsr native_real_control_emit_conversion
    lda #$00
    ldx #$02
    jsr native_real_control_emit_pointer_setup
    lda #$02
    ldx #$04
    jsr native_real_control_emit_pointer_setup
    jsr native_real_control_emit_jsr
    lda native_real_control_cmp
    jsr native_real_control_emit_condition
    lda native_real_control_mode
    cmp #NATIVE_REAL_CONTROL_NESTED
    bne native_real_control_emit_not_nested
    lda #$00
    ldx #$02
    jsr native_real_control_emit_pointer_setup
    lda #$02
    ldx #$04
    jsr native_real_control_emit_pointer_setup
    jsr native_real_control_emit_jsr
    lda native_real_control_cmp
    jsr native_real_control_emit_inner_condition
    lda native_real_control_store
    jsr native_real_control_emit_store_word
    jmp native_real_control_emit_check
native_real_control_emit_not_nested:
    lda native_real_control_store
    jsr native_real_control_emit_store_word
    lda native_real_control_mode
    cmp #NATIVE_REAL_CONTROL_ELSE
    beq :+
    jmp native_real_control_emit_check
:
    lda #$A9
    jsr native_real_control_emit_byte
    lda #$01
    jsr native_real_control_emit_byte
    lda #$D0
    jsr native_real_control_emit_byte
    lda #$0A
    jsr native_real_control_emit_byte
    lda native_real_control_else
    jsr native_real_control_emit_store_word
    jmp native_real_control_emit_check

native_real_control_emit_do_simple_machine_code:
    lda #$00
    ldx #$02
    jsr native_real_control_emit_pointer_setup
    lda native_real_control_left
    jsr native_real_control_emit_conversion
    lda #$02
    ldx #$02
    jsr native_real_control_emit_pointer_setup
    lda native_real_control_right
    jsr native_real_control_emit_conversion
    lda #$00
    ldx #$02
    jsr native_real_control_emit_pointer_setup
    lda native_real_control_store
    jsr native_real_control_emit_conversion
    lda #$00
    ldx #$02
    jsr native_real_control_emit_pointer_setup
    lda #$02
    ldx #$04
    jsr native_real_control_emit_pointer_setup
    jsr native_real_control_emit_jsr
    lda #$CB
    ldx native_real_control_cmp
    jsr native_real_control_emit_loop_condition
    lda native_real_control_else
    jsr native_real_control_emit_store_word
    jmp native_real_control_emit_check

native_real_control_emit_do_binary_machine_code:
    lda #$00
    ldx #$02
    jsr native_real_control_emit_pointer_setup
    lda native_real_control_left
    jsr native_real_control_emit_conversion
    lda #$02
    ldx #$02
    jsr native_real_control_emit_pointer_setup
    lda native_real_control_right
    jsr native_real_control_emit_conversion
    lda #$04
    ldx #$02
    jsr native_real_control_emit_pointer_setup
    lda native_real_control_store
    jsr native_real_control_emit_conversion
    lda #$00
    ldx #$02
    jsr native_real_control_emit_pointer_setup
    lda #$04
    ldx #$04
    jsr native_real_control_emit_pointer_setup
    lda #$00
    ldx #$06
    jsr native_real_control_emit_pointer_setup
    jsr native_real_control_emit_jsr
    lda #$00
    ldx #$02
    jsr native_real_control_emit_pointer_setup
    lda #$02
    ldx #$04
    jsr native_real_control_emit_pointer_setup
    jsr native_real_control_emit_jsr
    lda #$B5
    ldx native_real_control_cmp
    jsr native_real_control_emit_loop_condition
    lda native_real_control_else
    jsr native_real_control_emit_store_word
native_real_control_emit_check:
    lda #<native_real_control_check
    ldy #>native_real_control_check
    ldx #(native_real_control_check_end-native_real_control_check)
    jsr native_real_control_emit_const
    lda #$EA
    jsr native_real_control_emit_byte
    lda native_real_control_mode
    cmp #NATIVE_REAL_CONTROL_NESTED
    bne :+
    lda #$EA
    jsr native_real_control_emit_byte
:
    lda #<native_real_control_exit
    ldy #>native_real_control_exit
    ldx #(native_real_control_exit_end-native_real_control_exit)
    jsr native_real_control_emit_const
    jsr native_real_control_data_size
    sta native_real_control_count
native_real_control_emit_zero_loop:
    lda #$00
    jsr native_real_control_emit_byte
    dec native_real_control_count
    bne native_real_control_emit_zero_loop
    jsr emit_newline
    jsr native_real_control_emit_relocs
    clc
    rts

native_real_control_emit_conversion:
    sta native_real_control_value_temp
    lda #$A9
    jsr native_real_control_emit_byte
    lda native_real_control_value_temp
    jsr native_real_control_emit_byte
    lda #$A2
    jsr native_real_control_emit_byte
    lda #$00
    jsr native_real_control_emit_byte
    jmp native_real_control_emit_jsr

native_real_control_emit_condition:
    sta native_real_control_value_temp
    lda #$C9
    jsr native_real_control_emit_byte
    lda native_real_control_value_temp
    jsr native_real_control_emit_byte
    lda native_real_control_skip
    jsr native_real_control_emit_byte
    lda native_real_control_mode
    cmp #NATIVE_REAL_CONTROL_ELSE
    beq native_real_control_emit_condition_else
    cmp #NATIVE_REAL_CONTROL_NESTED
    beq native_real_control_emit_condition_nested
    lda #$0A
    jmp native_real_control_emit_byte
native_real_control_emit_condition_else:
    lda #$0E
    jmp native_real_control_emit_byte
native_real_control_emit_condition_nested:
    lda #$2B
    jmp native_real_control_emit_byte

native_real_control_emit_loop_condition:
    sta native_real_control_pointer_index
    stx native_real_control_value_temp
    lda #$C9
    jsr native_real_control_emit_byte
    lda native_real_control_value_temp
    jsr native_real_control_emit_byte
    lda native_real_control_skip
    jsr native_real_control_emit_byte
    lda native_real_control_pointer_index
    jmp native_real_control_emit_byte

native_real_control_emit_inner_condition:
    sta native_real_control_value_temp
    lda #$C9
    jsr native_real_control_emit_byte
    lda native_real_control_value_temp
    jsr native_real_control_emit_byte
    lda native_real_control_skip
    jsr native_real_control_emit_byte
    lda #$0A
    jmp native_real_control_emit_byte

native_real_control_emit_store_word:
    sta native_real_control_value_temp
    lda #$A9
    jsr native_real_control_emit_byte
    lda native_real_control_value_temp
    jsr native_real_control_emit_byte
    lda #$A2
    jsr native_real_control_emit_byte
    lda #$00
    jsr native_real_control_emit_byte
    lda #$8D
    jsr native_real_control_emit_byte
    lda #$00
    jsr native_real_control_emit_byte
    lda #$00
    jsr native_real_control_emit_byte
    lda #$8E
    jsr native_real_control_emit_byte
    lda #$00
    jsr native_real_control_emit_byte
    lda #$00
    jmp native_real_control_emit_byte

native_real_control_emit_pointer_setup:
    sta native_real_control_pointer_index
    stx native_real_control_pointer_zp
    lda #$A2
    jsr native_real_control_emit_byte
    lda native_real_control_pointer_index
    jsr native_real_control_emit_byte
    lda #$BD
    jsr native_real_control_emit_byte
    lda #$00
    jsr native_real_control_emit_byte
    lda #$00
    jsr native_real_control_emit_byte
    lda #$85
    jsr native_real_control_emit_byte
    lda native_real_control_pointer_zp
    jsr native_real_control_emit_byte
    lda #$E8
    jsr native_real_control_emit_byte
    lda #$BD
    jsr native_real_control_emit_byte
    lda #$00
    jsr native_real_control_emit_byte
    lda #$00
    jsr native_real_control_emit_byte
    lda #$85
    jsr native_real_control_emit_byte
    lda native_real_control_pointer_zp
    clc
    adc #$01
    jmp native_real_control_emit_byte

native_real_control_emit_jsr:
    lda #$20
    jsr native_real_control_emit_byte
    lda #$00
    jsr native_real_control_emit_byte
    lda #$00
    jmp native_real_control_emit_byte

native_real_control_emit_const:
    sta native_real_control_const_ptr
    sty native_real_control_const_ptr+1
    stx native_real_control_count
    ldy #$00
native_real_control_emit_const_loop:
    cpy native_real_control_count
    beq native_real_control_emit_const_done
    lda native_real_control_const_ptr
    sta ACTC_OVERLAY_WORK_ZP
    lda native_real_control_const_ptr+1
    sta ACTC_OVERLAY_WORK_ZP+1
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr native_real_control_emit_byte
    iny
    bne native_real_control_emit_const_loop
native_real_control_emit_const_done:
    rts

native_real_control_emit_byte:
    sta native_real_control_byte
    lda #' '
    jsr emit_char_overlay
    lda native_real_control_byte
    jmp emit_hex_byte_overlay

native_real_control_emit_relocs:
    lda native_real_control_mode
    cmp #NATIVE_REAL_CONTROL_DO_SIMPLE
    bne :+
    jmp native_real_control_emit_relocs_do_simple
:
    cmp #NATIVE_REAL_CONTROL_DO_BINARY
    bne :+
    jmp native_real_control_emit_relocs_do_binary
:
    lda #$03
    jsr native_real_control_emit_pointer_reloc
    lda #$09
    jsr native_real_control_emit_pointer_reloc
    lda #18
    ldx #$00
    jsr native_real_control_emit_import_reloc
    lda #23
    jsr native_real_control_emit_pointer_reloc
    lda #29
    jsr native_real_control_emit_pointer_reloc
    lda #38
    ldx #$00
    jsr native_real_control_emit_import_reloc
    lda #43
    jsr native_real_control_emit_pointer_reloc
    lda #49
    jsr native_real_control_emit_pointer_reloc
    lda #56
    jsr native_real_control_emit_pointer_reloc
    lda #62
    jsr native_real_control_emit_pointer_reloc
    lda #67
    ldx #$01
    jsr native_real_control_emit_import_reloc
    lda native_real_control_mode
    cmp #NATIVE_REAL_CONTROL_ELSE
    beq native_real_control_emit_relocs_else
    cmp #NATIVE_REAL_CONTROL_NESTED
    beq native_real_control_emit_relocs_nested
    lda #78
    jsr native_real_control_emit_y_reloc
    lda #81
    jsr native_real_control_emit_y_hi_reloc
    lda #84
    jsr native_real_control_emit_y_reloc
    lda #87
    jsr native_real_control_emit_y_hi_reloc
    lda #122
    jsr native_real_control_emit_a_reloc
    lda #124
    jmp native_real_control_emit_b_reloc
native_real_control_emit_relocs_else:
    lda #78
    jsr native_real_control_emit_y_reloc
    lda #81
    jsr native_real_control_emit_y_hi_reloc
    lda #92
    jsr native_real_control_emit_y_reloc
    lda #95
    jsr native_real_control_emit_y_hi_reloc
    lda #98
    jsr native_real_control_emit_y_reloc
    lda #101
    jsr native_real_control_emit_y_hi_reloc
    lda #136
    jsr native_real_control_emit_a_reloc
    lda #138
    jmp native_real_control_emit_b_reloc
native_real_control_emit_relocs_nested:
    lda #76
    jsr native_real_control_emit_pointer_reloc
    lda #82
    jsr native_real_control_emit_pointer_reloc
    lda #89
    jsr native_real_control_emit_pointer_reloc
    lda #95
    jsr native_real_control_emit_pointer_reloc
    lda #100
    ldx #$01
    jsr native_real_control_emit_import_reloc
    lda #111
    jsr native_real_control_emit_y_reloc
    lda #114
    jsr native_real_control_emit_y_hi_reloc
    lda #117
    jsr native_real_control_emit_y_reloc
    lda #120
    jsr native_real_control_emit_y_hi_reloc
    lda #156
    jsr native_real_control_emit_a_reloc
    lda #158
    jmp native_real_control_emit_b_reloc

native_real_control_emit_relocs_do_simple:
    lda #3
    jsr native_real_control_emit_do_pointer_reloc
    lda #9
    jsr native_real_control_emit_do_pointer_reloc
    lda #18
    ldx #$00
    jsr native_real_control_emit_import_reloc
    lda #23
    jsr native_real_control_emit_do_pointer_reloc
    lda #29
    jsr native_real_control_emit_do_pointer_reloc
    lda #38
    ldx #$00
    jsr native_real_control_emit_import_reloc
    lda #43
    jsr native_real_control_emit_do_pointer_reloc
    lda #49
    jsr native_real_control_emit_do_pointer_reloc
    lda #58
    ldx #$00
    jsr native_real_control_emit_import_reloc
    lda #63
    jsr native_real_control_emit_do_pointer_reloc
    lda #69
    jsr native_real_control_emit_do_pointer_reloc
    lda #76
    jsr native_real_control_emit_do_pointer_reloc
    lda #82
    jsr native_real_control_emit_do_pointer_reloc
    lda #87
    ldx #$01
    jsr native_real_control_emit_import_reloc
    lda #98
    jsr native_real_control_emit_do_y_reloc
    lda #101
    jsr native_real_control_emit_do_y_hi_reloc
    lda #104
    jsr native_real_control_emit_do_y_reloc
    lda #107
    jsr native_real_control_emit_do_y_hi_reloc
    lda #142
    jsr native_real_control_emit_do_a_reloc
    lda #144
    jmp native_real_control_emit_do_b_reloc

native_real_control_emit_relocs_do_binary:
    lda #3
    jsr native_real_control_emit_do_pointer_reloc
    lda #9
    jsr native_real_control_emit_do_pointer_reloc
    lda #18
    ldx #$00
    jsr native_real_control_emit_import_reloc
    lda #23
    jsr native_real_control_emit_do_pointer_reloc
    lda #29
    jsr native_real_control_emit_do_pointer_reloc
    lda #38
    ldx #$00
    jsr native_real_control_emit_import_reloc
    lda #43
    jsr native_real_control_emit_do_pointer_reloc
    lda #49
    jsr native_real_control_emit_do_pointer_reloc
    lda #58
    ldx #$00
    jsr native_real_control_emit_import_reloc
    lda #63
    jsr native_real_control_emit_do_pointer_reloc
    lda #69
    jsr native_real_control_emit_do_pointer_reloc
    lda #76
    jsr native_real_control_emit_do_pointer_reloc
    lda #82
    jsr native_real_control_emit_do_pointer_reloc
    lda #89
    jsr native_real_control_emit_do_pointer_reloc
    lda #95
    jsr native_real_control_emit_do_pointer_reloc
    lda #100
    ldx #$01
    jsr native_real_control_emit_import_reloc
    lda #105
    jsr native_real_control_emit_do_pointer_reloc
    lda #111
    jsr native_real_control_emit_do_pointer_reloc
    lda #118
    jsr native_real_control_emit_do_pointer_reloc
    lda #124
    jsr native_real_control_emit_do_pointer_reloc
    lda #129
    ldx #$02
    jsr native_real_control_emit_import_reloc
    lda #140
    jsr native_real_control_emit_do_y_reloc
    lda #143
    jsr native_real_control_emit_do_y_hi_reloc
    lda #146
    jsr native_real_control_emit_do_y_reloc
    lda #149
    jsr native_real_control_emit_do_y_hi_reloc
    lda #188
    jsr native_real_control_emit_do_a_reloc
    lda #190
    jsr native_real_control_emit_do_b_reloc
    lda #192
    jmp native_real_control_emit_do_c_reloc

native_real_control_emit_pointer_reloc:
    pha
    lda #<native_real_control_name_pointer
    ldy #>native_real_control_name_pointer
    bne native_real_control_emit_named_reloc_saved
native_real_control_emit_a_reloc:
    pha
    lda #<native_real_control_name_a
    ldy #>native_real_control_name_a
    bne native_real_control_emit_named_reloc_saved
native_real_control_emit_b_reloc:
    pha
    lda #<native_real_control_name_b
    ldy #>native_real_control_name_b
    bne native_real_control_emit_named_reloc_saved
native_real_control_emit_y_reloc:
    pha
    lda #<native_real_control_name_y
    ldy #>native_real_control_name_y
    bne native_real_control_emit_named_reloc_saved
native_real_control_emit_y_hi_reloc:
    pha
    lda #<native_real_control_name_y_hi
    ldy #>native_real_control_name_y_hi
    bne native_real_control_emit_named_reloc_saved
native_real_control_emit_do_pointer_reloc:
    pha
    lda #<native_real_control_name_do_pointer
    ldy #>native_real_control_name_do_pointer
    bne native_real_control_emit_named_reloc_saved
native_real_control_emit_do_a_reloc:
    pha
    lda #<native_real_control_name_do_a
    ldy #>native_real_control_name_do_a
    bne native_real_control_emit_named_reloc_saved
native_real_control_emit_do_b_reloc:
    pha
    lda #<native_real_control_name_do_b
    ldy #>native_real_control_name_do_b
    bne native_real_control_emit_named_reloc_saved
native_real_control_emit_do_c_reloc:
    pha
    lda #<native_real_control_name_do_c
    ldy #>native_real_control_name_do_c
    bne native_real_control_emit_named_reloc_saved
native_real_control_emit_do_y_reloc:
    pha
    lda #<native_real_control_name_do_y
    ldy #>native_real_control_name_do_y
    bne native_real_control_emit_named_reloc_saved
native_real_control_emit_do_y_hi_reloc:
    pha
    lda #<native_real_control_name_do_y_hi
    ldy #>native_real_control_name_do_y_hi
native_real_control_emit_named_reloc_saved:
    sta ACTC_OVERLAY_SCAN_ZP
    sty ACTC_OVERLAY_SCAN_ZP+1
    pla
    jsr native_real_control_emit_reloc_prefix
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr emit_scan_zp_string
    jmp emit_newline

native_real_control_emit_import_reloc:
    stx native_real_control_import_index
    jsr native_real_control_emit_reloc_prefix
    lda #'u'
    jsr emit_char_overlay
    lda native_real_control_import_index
    jsr emit_object_selector_overlay
    jmp emit_newline

native_real_control_emit_reloc_prefix:
    sta native_real_control_byte
    lda #'r'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda native_real_control_byte
    jsr emit_small_decimal
    lda #' '
    jmp emit_char_overlay

native_real_control_plain_pattern:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1p4*hp5S2vr"
native_real_control_else_pattern:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1p4*hp5S2wp6S2vr"
native_real_control_nested_pattern:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1p4*hL0U0L1U1u1p5*hp6S2vvr"
native_real_control_do_simple_pattern:
    .asciiz "p0p0T0S0p2u0T1S1dp4u0T0S0L0U0L1U1u1p5*top6S2r"
native_real_control_do_binary_add_pattern:
    .asciiz "p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p5*top6S3r"
native_real_control_do_binary_sub_zero_pattern:
    .asciiz "p1u0T0S0p2p2T1S1p4u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p5*top6S3r"
native_real_control_do_binary_sub_nonzero_pattern:
    .asciiz "p1u0T0S0p3u0T1S1p5u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p6*top7S3r"

native_real_control_check:
    .byte $AD,$00,$00,$AE,$00,$00,$8D,$D1,$03,$8E,$D2,$03
native_real_control_check_end:
native_real_control_exit:
    .byte $A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF
native_real_control_exit_end:

native_real_control_name_data:
    .asciiz "__idata"
native_real_control_name_a:
    .asciiz "__ifa"
native_real_control_name_b:
    .asciiz "__ifb"
native_real_control_name_y:
    .asciiz "__ify"
native_real_control_name_y_hi:
    .asciiz "__ifyhi"
native_real_control_name_pointer:
    .asciiz "__ifptr"
native_real_control_name_do_a:
    .asciiz "__doa"
native_real_control_name_do_b:
    .asciiz "__dob"
native_real_control_name_do_c:
    .asciiz "__doc"
native_real_control_name_do_y:
    .asciiz "__doy"
native_real_control_name_do_y_hi:
    .asciiz "__doyhi"
native_real_control_name_do_pointer:
    .asciiz "__doptr"

native_real_control_plain_debug_offsets:
    .byte 0,17,20,20,20,37,40,40,40,40,53,53,66,69,69,69,73,73,83,96
native_real_control_else_debug_offsets:
    .byte 0,17,20,20,20,37,40,40,40,40,53,53,66,69,69,69,73,73,83,87,87,97,110
native_real_control_nested_debug_offsets:
    .byte 0,17,20,20,20,37,40,40,40,40,53,53,66,69,69,69,73,73,86,86,99,102,102,102,106,106,116,116,130
native_real_control_do_simple_debug_offsets:
    .byte 0,0,20,20,20,37,40,40,40,40,57,60,60,60,60,73,73,86,89,89,89,89,93,93,116
native_real_control_do_binary_debug_offsets:
    .byte 0,0,20,20,20,37,40,40,40,57,60,60,60,60,60,73,73,99,102,102,102,102,115,115,128,131,131,131,131,135,135,158

native_real_control_mode:
    .byte $00
native_real_control_layout:
    .byte $00
native_real_control_body_op:
    .byte $00
native_real_control_relation:
    .byte $00
native_real_control_left:
    .byte $00
native_real_control_right:
    .byte $00
native_real_control_store:
    .byte $00
native_real_control_else:
    .byte $00
native_real_control_cmp:
    .byte $00
native_real_control_skip:
    .byte $00
native_real_control_byte:
    .byte $00
native_real_control_value_temp:
    .byte $00
native_real_control_count:
    .byte $00
native_real_control_export_size:
    .byte $00
native_real_control_pointer_index:
    .byte $00
native_real_control_pointer_zp:
    .byte $00
native_real_control_import_index:
    .byte $00
native_real_control_const_ptr:
    .word $0000
