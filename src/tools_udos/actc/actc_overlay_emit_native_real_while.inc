; Compiler-owned native lowering for the remaining compact REAL WHILE families.

NATIVE_REAL_WHILE_SIMPLE = 1
NATIVE_REAL_WHILE_BINARY = 2

NATIVE_REAL_WHILE_SIMPLE_CODE_SIZE = 135
NATIVE_REAL_WHILE_BINARY_CODE_SIZE = 177
NATIVE_REAL_WHILE_SIMPLE_DATA_SIZE = 14
NATIVE_REAL_WHILE_BINARY_DATA_SIZE = 20
NATIVE_REAL_WHILE_SIMPLE_LOOP_OFFSET = 40
NATIVE_REAL_WHILE_BINARY_LOOP_OFFSET = 60

native_real_while_detect:
    lda #$00
    sta native_real_while_mode
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$01
    beq :+
    jmp native_real_while_detect_no
:
    lda #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    jsr load_context_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcs :+
    jmp native_real_while_detect_no
:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcs :+
    jmp native_real_while_detect_no
:
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$03
    beq native_real_while_detect_simple_vars
    cmp #$04
    beq :+
    jmp native_real_while_detect_no
:
    jmp native_real_while_detect_binary_vars

native_real_while_detect_simple_vars:
    lda #$04
    ldx #$00
    jsr native_real_while_var_x_has_type_a
    beq :+
    jmp native_real_while_detect_no
:
    lda #$04
    ldx #$01
    jsr native_real_while_var_x_has_type_a
    beq :+
    jmp native_real_while_detect_no
:
    lda #$02
    ldx #$02
    jsr native_real_while_var_x_has_type_a
    beq :+
    jmp native_real_while_detect_no
:
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$02
    bcs :+
    jmp native_real_while_detect_no
:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #NATIVE_REAL_WHILE_SIMPLE
    sta native_real_while_mode
    lda #$00
    sta native_real_while_layout
    sta native_real_while_update_target
    lda #<native_real_while_simple_a_zero_pattern
    ldy #>native_real_while_simple_a_zero_pattern
    jsr native_real_while_match_pattern
    bcs native_real_while_detect_simple
    inc native_real_while_layout
    lda #<native_real_while_simple_a_convert_pattern
    ldy #>native_real_while_simple_a_convert_pattern
    jsr native_real_while_match_pattern
    bcs native_real_while_detect_simple
    inc native_real_while_layout
    lda #$02
    sta native_real_while_update_target
    lda #<native_real_while_simple_b_zero_pattern
    ldy #>native_real_while_simple_b_zero_pattern
    jsr native_real_while_match_pattern
    bcs native_real_while_detect_simple
    inc native_real_while_layout
    lda #<native_real_while_simple_b_convert_pattern
    ldy #>native_real_while_simple_b_convert_pattern
    jsr native_real_while_match_pattern
    bcs native_real_while_detect_simple
    jmp native_real_while_detect_no

native_real_while_detect_simple:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    ldx native_real_while_layout
    txa
    and #$01
    beq native_real_while_detect_simple_need_seven
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$08
    bcs native_real_while_detect_simple_have_ints
    jmp native_real_while_detect_no
native_real_while_detect_simple_need_seven:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$07
    bcs native_real_while_detect_simple_have_ints
    jmp native_real_while_detect_no
native_real_while_detect_simple_have_ints:
    ldx #$00
    jsr native_real_while_literal_x_is_zero
    bcs :+
    jmp native_real_while_detect_no
:
    ldx #$02
    jsr native_real_while_literal_x_is_zero
    bcs :+
    jmp native_real_while_detect_no
:
    ldx #$06
    jsr native_real_while_literal_x_is_zero
    bcs :+
    jmp native_real_while_detect_no
:
    ldx #$01
    jsr native_real_while_load_byte_literal
    bcs :+
    jmp native_real_while_detect_no
:
    sta native_real_while_left
    ldx #$03
    jsr native_real_while_load_byte_literal
    bcs :+
    jmp native_real_while_detect_no
:
    sta native_real_while_right
    ldx #$04
    jsr native_real_while_load_byte_literal
    bcs :+
    jmp native_real_while_detect_no
:
    sta native_real_while_relation
    ldx #$05
    jsr native_real_while_load_byte_literal
    bcs :+
    jmp native_real_while_detect_no
:
    sta native_real_while_store
    lda #$00
    sta native_real_while_update
    lda native_real_while_layout
    and #$01
    beq native_real_while_detect_simple_update_ready
    ldx #$07
    jsr native_real_while_load_byte_literal
    bcs :+
    jmp native_real_while_detect_no
:
    sta native_real_while_update
native_real_while_detect_simple_update_ready:
    jsr native_real_while_map_relation
    bcc native_real_while_detect_simple_no
    jmp native_real_while_detect_yes
native_real_while_detect_simple_no:
    jmp native_real_while_detect_no

native_real_while_detect_binary_vars:
    lda #$04
    ldx #$00
    jsr native_real_while_var_x_has_type_a
    beq :+
    jmp native_real_while_detect_no
:
    lda #$04
    ldx #$01
    jsr native_real_while_var_x_has_type_a
    beq :+
    jmp native_real_while_detect_no
:
    lda #$04
    ldx #$02
    jsr native_real_while_var_x_has_type_a
    beq :+
    jmp native_real_while_detect_no
:
    lda #$02
    ldx #$03
    jsr native_real_while_var_x_has_type_a
    beq :+
    jmp native_real_while_detect_no
:
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$03
    bcs :+
    jmp native_real_while_detect_no
:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #NATIVE_REAL_WHILE_BINARY
    sta native_real_while_mode
    lda #$00
    sta native_real_while_layout
    lda #<native_real_while_binary_add_pattern
    ldy #>native_real_while_binary_add_pattern
    jsr native_real_while_match_pattern
    bcs native_real_while_detect_binary
    inc native_real_while_layout
    lda #<native_real_while_binary_sub_zero_pattern
    ldy #>native_real_while_binary_sub_zero_pattern
    jsr native_real_while_match_pattern
    bcs native_real_while_detect_binary
    inc native_real_while_layout
    lda #<native_real_while_binary_sub_nonzero_pattern
    ldy #>native_real_while_binary_sub_nonzero_pattern
    jsr native_real_while_match_pattern
    bcs native_real_while_detect_binary
    jmp native_real_while_detect_no

native_real_while_detect_binary:
    lda native_real_while_layout
    beq native_real_while_detect_binary_add
    cmp #$01
    beq native_real_while_detect_binary_sub_zero
    jmp native_real_while_detect_binary_sub_nonzero

native_real_while_detect_binary_add:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$07
    bcs :+
    jmp native_real_while_detect_no
:
    ldx #$00
    jsr native_real_while_literal_x_is_zero
    bcc native_real_while_detect_binary_add_no
    ldx #$01
    jsr native_real_while_literal_x_is_zero
    bcc native_real_while_detect_binary_add_no
    ldx #$03
    jsr native_real_while_literal_x_is_zero
    bcc native_real_while_detect_binary_add_no
    lda #$00
    sta native_real_while_left
    ldx #$02
    jsr native_real_while_load_byte_literal
    bcc native_real_while_detect_binary_add_no
    sta native_real_while_right
    ldx #$04
    jsr native_real_while_load_byte_literal
    bcc native_real_while_detect_binary_add_no
    sta native_real_while_update
    ldx #$05
    jsr native_real_while_load_byte_literal
    bcc native_real_while_detect_binary_add_no
    sta native_real_while_relation
    ldx #$06
    jmp native_real_while_detect_binary_store
native_real_while_detect_binary_add_no:
    jmp native_real_while_detect_no

native_real_while_detect_binary_sub_zero:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$07
    bcs :+
    jmp native_real_while_detect_no
:
    ldx #$00
    jsr native_real_while_literal_x_is_zero
    bcc native_real_while_detect_binary_sub_zero_no
    ldx #$02
    jsr native_real_while_literal_x_is_zero
    bcc native_real_while_detect_binary_sub_zero_no
    ldx #$03
    jsr native_real_while_literal_x_is_zero
    bcc native_real_while_detect_binary_sub_zero_no
    ldx #$01
    jsr native_real_while_load_byte_literal
    bcc native_real_while_detect_binary_sub_zero_no
    sta native_real_while_left
    lda #$00
    sta native_real_while_right
    ldx #$04
    jsr native_real_while_load_byte_literal
    bcc native_real_while_detect_binary_sub_zero_no
    sta native_real_while_update
    ldx #$05
    jsr native_real_while_load_byte_literal
    bcc native_real_while_detect_binary_sub_zero_no
    sta native_real_while_relation
    ldx #$06
    jmp native_real_while_detect_binary_store
native_real_while_detect_binary_sub_zero_no:
    jmp native_real_while_detect_no

native_real_while_detect_binary_sub_nonzero:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$08
    bcs :+
    jmp native_real_while_detect_no
:
    ldx #$00
    jsr native_real_while_literal_x_is_zero
    bcc native_real_while_detect_binary_sub_nonzero_no
    ldx #$02
    jsr native_real_while_literal_x_is_zero
    bcc native_real_while_detect_binary_sub_nonzero_no
    ldx #$04
    jsr native_real_while_literal_x_is_zero
    bcc native_real_while_detect_binary_sub_nonzero_no
    ldx #$01
    jsr native_real_while_load_byte_literal
    bcc native_real_while_detect_binary_sub_nonzero_no
    sta native_real_while_left
    ldx #$03
    jsr native_real_while_load_byte_literal
    bcc native_real_while_detect_binary_sub_nonzero_no
    sta native_real_while_right
    ldx #$05
    jsr native_real_while_load_byte_literal
    bcc native_real_while_detect_binary_sub_nonzero_no
    sta native_real_while_update
    ldx #$06
    jsr native_real_while_load_byte_literal
    bcc native_real_while_detect_binary_sub_nonzero_no
    sta native_real_while_relation
    ldx #$07
    jmp native_real_while_detect_binary_store
native_real_while_detect_binary_sub_nonzero_no:
    jmp native_real_while_detect_no
native_real_while_detect_binary_store:
    jsr native_real_while_load_byte_literal
    bcc native_real_while_detect_no
    sta native_real_while_store
    jsr native_real_while_map_relation
    bcc native_real_while_detect_no
native_real_while_detect_yes:
    sec
    rts
native_real_while_detect_no:
    lda #$00
    sta native_real_while_mode
    clc
    rts

native_real_while_literal_x_is_zero:
    jsr native_real_while_load_byte_literal
    bcc native_real_while_literal_x_is_zero_no
    cmp #$00
    bne native_real_while_literal_x_is_zero_no
    sec
    rts
native_real_while_literal_x_is_zero_no:
    clc
    rts

native_real_while_var_x_has_type_a:
    sta native_real_while_byte
    lda #ACTC_OVERLAY_CTX_LOAD_VAR_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp native_real_while_byte
    rts

native_real_while_match_pattern:
    sta ACTC_OVERLAY_WORK_ZP
    sty ACTC_OVERLAY_WORK_ZP+1
    lda #$00
    sta native_real_while_body_op
    ldy #$00
native_real_while_match_pattern_loop:
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp #'*'
    beq native_real_while_match_pattern_wild
    sta native_real_while_byte
    jsr emit_object_peek_payload_y
    cmp native_real_while_byte
    bne native_real_while_match_pattern_no
    lda native_real_while_byte
    beq native_real_while_match_pattern_yes
    iny
    bne native_real_while_match_pattern_loop
native_real_while_match_pattern_no:
    clc
    rts
native_real_while_match_pattern_wild:
    jsr emit_object_peek_payload_y
    cmp #'g'
    beq native_real_while_match_pattern_store
    cmp #'l'
    bne native_real_while_match_pattern_no
native_real_while_match_pattern_store:
    sta native_real_while_body_op
    iny
    bne native_real_while_match_pattern_loop
native_real_while_match_pattern_yes:
    sec
    rts

native_real_while_load_byte_literal:
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$01
    lda (ACTC_OVERLAY_WORK_ZP),y
    bne native_real_while_load_byte_literal_no
    dey
    lda (ACTC_OVERLAY_WORK_ZP),y
    sec
    rts
native_real_while_load_byte_literal_no:
    clc
    rts

native_real_while_map_relation:
    lda native_real_while_body_op
    cmp #'g'
    bne native_real_while_map_relation_l
    lda native_real_while_relation
    cmp #$01
    beq native_real_while_map_gt
    cmp #$00
    beq native_real_while_map_ge
    clc
    rts
native_real_while_map_relation_l:
    cmp #'l'
    bne native_real_while_map_relation_no
    lda native_real_while_relation
    cmp #$01
    beq native_real_while_map_lt
    cmp #$02
    beq native_real_while_map_le
native_real_while_map_relation_no:
    clc
    rts
native_real_while_map_gt:
    lda #$01
    ldx #$D0
    bne native_real_while_map_store
native_real_while_map_ge:
    lda #$02
    ldx #$B0
    bne native_real_while_map_store
native_real_while_map_lt:
    lda #$FF
    ldx #$D0
    bne native_real_while_map_store
native_real_while_map_le:
    lda #$01
    ldx #$10
native_real_while_map_store:
    sta native_real_while_cmp
    stx native_real_while_skip
    sec
    rts

native_real_while_emit_debug_offset:
    ldx body_debug_index_data
    lda native_real_while_mode
    cmp #NATIVE_REAL_WHILE_BINARY
    beq :+
    lda native_real_while_simple_debug_offsets,x
    bne native_real_while_emit_debug_offset_ready
:
    lda native_real_while_binary_debug_offsets,x
native_real_while_emit_debug_offset_ready:
    ldy #$00
    jmp emit_word_decimal

native_real_while_emit_export_list:
    lda #$00
    sta word_value_lo
    sta word_value_hi
    jsr native_real_while_code_size
    sta native_real_while_byte
    jsr native_real_while_data_size
    clc
    adc native_real_while_byte
    ldx #$00
    jsr emit_machine_export_line

    jsr native_real_while_loop_offset
    sta word_value_lo
    lda #$00
    sta word_value_hi
    lda #<native_real_while_name_loop
    ldy #>native_real_while_name_loop
    ldx #$01
    jsr native_real_while_emit_named_export

    jsr native_real_while_data_size
    tax
    jsr native_real_while_code_size
    sta word_value_lo
    lda #$00
    sta word_value_hi
    lda #<native_real_while_name_data
    ldy #>native_real_while_name_data
    jsr native_real_while_emit_named_export

    jsr native_real_while_code_size
    sta word_value_lo
    lda #$00
    sta word_value_hi
    lda #<native_real_while_name_a
    ldy #>native_real_while_name_a
    ldx #$04
    jsr native_real_while_emit_named_export

    jsr native_real_while_code_size
    clc
    adc #$04
    sta word_value_lo
    lda #$00
    sta word_value_hi
    lda #<native_real_while_name_b
    ldy #>native_real_while_name_b
    ldx #$04
    jsr native_real_while_emit_named_export
    lda native_real_while_mode
    cmp #NATIVE_REAL_WHILE_BINARY
    bne native_real_while_emit_export_y

    jsr native_real_while_code_size
    clc
    adc #$08
    sta word_value_lo
    lda #$00
    sta word_value_hi
    lda #<native_real_while_name_c
    ldy #>native_real_while_name_c
    ldx #$04
    jsr native_real_while_emit_named_export
native_real_while_emit_export_y:
    jsr native_real_while_code_size
    ldx native_real_while_mode
    cpx #NATIVE_REAL_WHILE_BINARY
    beq :+
    clc
    adc #$08
    bne native_real_while_emit_export_y_offset_ready
:
    clc
    adc #$0C
native_real_while_emit_export_y_offset_ready:
    sta word_value_lo
    lda #$00
    sta word_value_hi
    lda #<native_real_while_name_y
    ldy #>native_real_while_name_y
    ldx #$02
    jsr native_real_while_emit_named_export

    jsr native_real_while_code_size
    ldx native_real_while_mode
    cpx #NATIVE_REAL_WHILE_BINARY
    beq :+
    clc
    adc #$09
    bne native_real_while_emit_export_y_hi_offset_ready
:
    clc
    adc #$0D
native_real_while_emit_export_y_hi_offset_ready:
    sta word_value_lo
    lda #$00
    sta word_value_hi
    lda #<native_real_while_name_y_hi
    ldy #>native_real_while_name_y_hi
    ldx #$01
    jsr native_real_while_emit_named_export

    jsr native_real_while_code_size
    ldx native_real_while_mode
    cpx #NATIVE_REAL_WHILE_BINARY
    beq :+
    clc
    adc #$0A
    ldx #$04
    bne native_real_while_emit_export_pointer_offset_ready
:
    clc
    adc #$0E
    ldx #$06
native_real_while_emit_export_pointer_offset_ready:
    sta word_value_lo
    lda #$00
    sta word_value_hi
    lda #<native_real_while_name_pointer
    ldy #>native_real_while_name_pointer
    jmp native_real_while_emit_named_export

native_real_while_emit_named_export:
    sta ACTC_OVERLAY_SCAN_ZP
    sty ACTC_OVERLAY_SCAN_ZP+1
    stx native_real_while_export_size
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr emit_scan_zp_string
    lda #' '
    jsr emit_char_overlay
    lda word_value_lo
    ldy word_value_hi
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda native_real_while_export_size
    ldy #$00
    jsr emit_word_decimal
    jmp emit_newline

native_real_while_code_size:
    lda native_real_while_mode
    cmp #NATIVE_REAL_WHILE_BINARY
    beq :+
    lda #NATIVE_REAL_WHILE_SIMPLE_CODE_SIZE
    rts
:
    lda #NATIVE_REAL_WHILE_BINARY_CODE_SIZE
    rts

native_real_while_data_size:
    lda native_real_while_mode
    cmp #NATIVE_REAL_WHILE_BINARY
    beq :+
    lda #NATIVE_REAL_WHILE_SIMPLE_DATA_SIZE
    rts
:
    lda #NATIVE_REAL_WHILE_BINARY_DATA_SIZE
    rts

native_real_while_loop_offset:
    lda native_real_while_mode
    cmp #NATIVE_REAL_WHILE_BINARY
    beq :+
    lda #NATIVE_REAL_WHILE_SIMPLE_LOOP_OFFSET
    rts
:
    lda #NATIVE_REAL_WHILE_BINARY_LOOP_OFFSET
    rts

native_real_while_emit_body_marker_list:
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
    lda native_real_while_mode
    cmp #NATIVE_REAL_WHILE_BINARY
    bne :+
    lda #'u'
    jsr emit_char_overlay
    lda #'2'
    jsr emit_char_overlay
:
    lda #'M'
    jsr emit_char_overlay
    jsr emit_newline
    lda #$07
    ldx native_real_while_mode
    cpx #NATIVE_REAL_WHILE_BINARY
    bne :+
    lda #$08
:
    sta native_real_while_count
native_real_while_emit_body_marker_loop:
    jsr emit_machine_body_marker_line
    dec native_real_while_count
    bne native_real_while_emit_body_marker_loop
    rts

native_real_while_emit_machine_code_list:
    lda #'m'
    jsr emit_char_overlay
    lda #$00
    ldx #$02
    jsr native_real_while_emit_pointer_setup
    lda native_real_while_left
    jsr native_real_while_emit_conversion
    lda #$02
    ldx #$02
    jsr native_real_while_emit_pointer_setup
    lda native_real_while_right
    jsr native_real_while_emit_conversion
    lda native_real_while_mode
    cmp #NATIVE_REAL_WHILE_BINARY
    beq :+
    jmp native_real_while_emit_simple_machine_tail
:
    lda #$04
    ldx #$02
    jsr native_real_while_emit_pointer_setup
    lda native_real_while_update
    jsr native_real_while_emit_conversion
    lda #$00
    ldx #$02
    jsr native_real_while_emit_pointer_setup
    lda #$02
    ldx #$04
    jsr native_real_while_emit_pointer_setup
    jsr native_real_while_emit_jsr
    lda #$37
    jsr native_real_while_emit_condition
    lda native_real_while_store
    jsr native_real_while_emit_store_word
    lda #$00
    ldx #$02
    jsr native_real_while_emit_pointer_setup
    lda #$04
    ldx #$04
    jsr native_real_while_emit_pointer_setup
    lda #$00
    ldx #$06
    jsr native_real_while_emit_pointer_setup
    jsr native_real_while_emit_jsr
    jmp native_real_while_emit_jump_and_exit

native_real_while_emit_simple_machine_tail:
    lda #$00
    ldx #$02
    jsr native_real_while_emit_pointer_setup
    lda #$02
    ldx #$04
    jsr native_real_while_emit_pointer_setup
    jsr native_real_while_emit_jsr
    lda #$21
    jsr native_real_while_emit_condition
    lda native_real_while_store
    jsr native_real_while_emit_store_word
    lda native_real_while_update_target
    ldx #$02
    jsr native_real_while_emit_pointer_setup
    lda native_real_while_update
    jsr native_real_while_emit_conversion

native_real_while_emit_jump_and_exit:
    lda #$4C
    jsr native_real_while_emit_byte
    lda #$00
    jsr native_real_while_emit_byte
    lda #$00
    jsr native_real_while_emit_byte
    lda #<native_real_while_check
    ldy #>native_real_while_check
    ldx #(native_real_while_check_end-native_real_while_check)
    jsr native_real_while_emit_const
    lda #$EA
    jsr native_real_while_emit_byte
    lda #<native_real_while_exit
    ldy #>native_real_while_exit
    ldx #(native_real_while_exit_end-native_real_while_exit)
    jsr native_real_while_emit_const
    jsr native_real_while_data_size
    sta native_real_while_count
native_real_while_emit_zero_loop:
    lda #$00
    jsr native_real_while_emit_byte
    dec native_real_while_count
    bne native_real_while_emit_zero_loop
    jsr emit_newline
    jsr native_real_while_emit_relocs
    clc
    rts

native_real_while_emit_conversion:
    sta native_real_while_value_temp
    lda #$A9
    jsr native_real_while_emit_byte
    lda native_real_while_value_temp
    jsr native_real_while_emit_byte
    lda #$A2
    jsr native_real_while_emit_byte
    lda #$00
    jsr native_real_while_emit_byte
    jmp native_real_while_emit_jsr

native_real_while_emit_condition:
    sta native_real_while_value_temp
    lda #$C9
    jsr native_real_while_emit_byte
    lda native_real_while_cmp
    jsr native_real_while_emit_byte
    lda native_real_while_skip
    jsr native_real_while_emit_byte
    lda native_real_while_value_temp
    jmp native_real_while_emit_byte

native_real_while_emit_store_word:
    sta native_real_while_value_temp
    lda #$A9
    jsr native_real_while_emit_byte
    lda native_real_while_value_temp
    jsr native_real_while_emit_byte
    lda #$A2
    jsr native_real_while_emit_byte
    lda #$00
    jsr native_real_while_emit_byte
    lda #$8D
    jsr native_real_while_emit_byte
    lda #$00
    jsr native_real_while_emit_byte
    lda #$00
    jsr native_real_while_emit_byte
    lda #$8E
    jsr native_real_while_emit_byte
    lda #$00
    jsr native_real_while_emit_byte
    lda #$00
    jmp native_real_while_emit_byte

native_real_while_emit_pointer_setup:
    sta native_real_while_pointer_index
    stx native_real_while_pointer_zp
    lda #$A2
    jsr native_real_while_emit_byte
    lda native_real_while_pointer_index
    jsr native_real_while_emit_byte
    lda #$BD
    jsr native_real_while_emit_byte
    lda #$00
    jsr native_real_while_emit_byte
    lda #$00
    jsr native_real_while_emit_byte
    lda #$85
    jsr native_real_while_emit_byte
    lda native_real_while_pointer_zp
    jsr native_real_while_emit_byte
    lda #$E8
    jsr native_real_while_emit_byte
    lda #$BD
    jsr native_real_while_emit_byte
    lda #$00
    jsr native_real_while_emit_byte
    lda #$00
    jsr native_real_while_emit_byte
    lda #$85
    jsr native_real_while_emit_byte
    lda native_real_while_pointer_zp
    clc
    adc #$01
    jmp native_real_while_emit_byte

native_real_while_emit_jsr:
    lda #$20
    jsr native_real_while_emit_byte
    lda #$00
    jsr native_real_while_emit_byte
    lda #$00
    jmp native_real_while_emit_byte

native_real_while_emit_const:
    sta native_real_while_const_ptr
    sty native_real_while_const_ptr+1
    stx native_real_while_count
    ldy #$00
native_real_while_emit_const_loop:
    cpy native_real_while_count
    beq native_real_while_emit_const_done
    lda native_real_while_const_ptr
    sta ACTC_OVERLAY_WORK_ZP
    lda native_real_while_const_ptr+1
    sta ACTC_OVERLAY_WORK_ZP+1
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr native_real_while_emit_byte
    iny
    bne native_real_while_emit_const_loop
native_real_while_emit_const_done:
    rts

native_real_while_emit_byte:
    sta native_real_while_byte
    lda #' '
    jsr emit_char_overlay
    lda native_real_while_byte
    jmp emit_hex_byte_overlay

native_real_while_emit_relocs:
    lda native_real_while_mode
    cmp #NATIVE_REAL_WHILE_BINARY
    beq :+
    jmp native_real_while_emit_relocs_simple
:
    lda #3
    jsr native_real_while_emit_pointer_reloc
    lda #9
    jsr native_real_while_emit_pointer_reloc
    lda #18
    ldx #$00
    jsr native_real_while_emit_import_reloc
    lda #23
    jsr native_real_while_emit_pointer_reloc
    lda #29
    jsr native_real_while_emit_pointer_reloc
    lda #38
    ldx #$00
    jsr native_real_while_emit_import_reloc
    lda #43
    jsr native_real_while_emit_pointer_reloc
    lda #49
    jsr native_real_while_emit_pointer_reloc
    lda #58
    ldx #$00
    jsr native_real_while_emit_import_reloc
    lda #63
    jsr native_real_while_emit_pointer_reloc
    lda #69
    jsr native_real_while_emit_pointer_reloc
    lda #76
    jsr native_real_while_emit_pointer_reloc
    lda #82
    jsr native_real_while_emit_pointer_reloc
    lda #87
    ldx #$01
    jsr native_real_while_emit_import_reloc
    lda #98
    jsr native_real_while_emit_y_reloc
    lda #101
    jsr native_real_while_emit_y_hi_reloc
    lda #106
    jsr native_real_while_emit_pointer_reloc
    lda #112
    jsr native_real_while_emit_pointer_reloc
    lda #119
    jsr native_real_while_emit_pointer_reloc
    lda #125
    jsr native_real_while_emit_pointer_reloc
    lda #132
    jsr native_real_while_emit_pointer_reloc
    lda #138
    jsr native_real_while_emit_pointer_reloc
    lda #143
    ldx #$02
    jsr native_real_while_emit_import_reloc
    lda #146
    jsr native_real_while_emit_loop_reloc
    lda #149
    jsr native_real_while_emit_y_reloc
    lda #152
    jsr native_real_while_emit_y_hi_reloc
    lda #191
    jsr native_real_while_emit_a_reloc
    lda #193
    jsr native_real_while_emit_b_reloc
    lda #195
    jmp native_real_while_emit_c_reloc

native_real_while_emit_relocs_simple:
    lda #3
    jsr native_real_while_emit_pointer_reloc
    lda #9
    jsr native_real_while_emit_pointer_reloc
    lda #18
    ldx #$00
    jsr native_real_while_emit_import_reloc
    lda #23
    jsr native_real_while_emit_pointer_reloc
    lda #29
    jsr native_real_while_emit_pointer_reloc
    lda #38
    ldx #$00
    jsr native_real_while_emit_import_reloc
    lda #43
    jsr native_real_while_emit_pointer_reloc
    lda #49
    jsr native_real_while_emit_pointer_reloc
    lda #56
    jsr native_real_while_emit_pointer_reloc
    lda #62
    jsr native_real_while_emit_pointer_reloc
    lda #67
    ldx #$01
    jsr native_real_while_emit_import_reloc
    lda #78
    jsr native_real_while_emit_y_reloc
    lda #81
    jsr native_real_while_emit_y_hi_reloc
    lda #86
    jsr native_real_while_emit_pointer_reloc
    lda #92
    jsr native_real_while_emit_pointer_reloc
    lda #101
    ldx #$00
    jsr native_real_while_emit_import_reloc
    lda #104
    jsr native_real_while_emit_loop_reloc
    lda #107
    jsr native_real_while_emit_y_reloc
    lda #110
    jsr native_real_while_emit_y_hi_reloc
    lda #145
    jsr native_real_while_emit_a_reloc
    lda #147
    jmp native_real_while_emit_b_reloc

native_real_while_emit_pointer_reloc:
    pha
    lda #<native_real_while_name_pointer
    ldy #>native_real_while_name_pointer
    bne native_real_while_emit_named_reloc_saved
native_real_while_emit_loop_reloc:
    pha
    lda #<native_real_while_name_loop
    ldy #>native_real_while_name_loop
    bne native_real_while_emit_named_reloc_saved
native_real_while_emit_a_reloc:
    pha
    lda #<native_real_while_name_a
    ldy #>native_real_while_name_a
    bne native_real_while_emit_named_reloc_saved
native_real_while_emit_b_reloc:
    pha
    lda #<native_real_while_name_b
    ldy #>native_real_while_name_b
    bne native_real_while_emit_named_reloc_saved
native_real_while_emit_c_reloc:
    pha
    lda #<native_real_while_name_c
    ldy #>native_real_while_name_c
    bne native_real_while_emit_named_reloc_saved
native_real_while_emit_y_reloc:
    pha
    lda #<native_real_while_name_y
    ldy #>native_real_while_name_y
    bne native_real_while_emit_named_reloc_saved
native_real_while_emit_y_hi_reloc:
    pha
    lda #<native_real_while_name_y_hi
    ldy #>native_real_while_name_y_hi
native_real_while_emit_named_reloc_saved:
    sta ACTC_OVERLAY_SCAN_ZP
    sty ACTC_OVERLAY_SCAN_ZP+1
    pla
    jsr native_real_while_emit_reloc_prefix
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr emit_scan_zp_string
    jmp emit_newline

native_real_while_emit_import_reloc:
    stx native_real_while_import_index
    jsr native_real_while_emit_reloc_prefix
    lda #'u'
    jsr emit_char_overlay
    lda native_real_while_import_index
    jsr emit_object_selector_overlay
    jmp emit_newline

native_real_while_emit_reloc_prefix:
    sta native_real_while_byte
    lda #'r'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda native_real_while_byte
    jsr emit_small_decimal
    lda #' '
    jmp emit_char_overlay

native_real_while_simple_a_zero_pattern:
    .asciiz "p1u0T0S0p3u0T1S1dL0U0L1U1u1p4*fp5S2p6p6T0S0xr"
native_real_while_simple_a_convert_pattern:
    .asciiz "p1u0T0S0p3u0T1S1dL0U0L1U1u1p4*fp5S2p7u0T0S0xr"
native_real_while_simple_b_zero_pattern:
    .asciiz "p1u0T0S0p3u0T1S1dL0U0L1U1u1p4*fp5S2p6p6T1S1xr"
native_real_while_simple_b_convert_pattern:
    .asciiz "p1u0T0S0p3u0T1S1dL0U0L1U1u1p4*fp5S2p7u0T1S1xr"
native_real_while_binary_add_pattern:
    .asciiz "p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L1U1u1p5*fp6S3L0U0L2U2u2T0S0xr"
native_real_while_binary_sub_zero_pattern:
    .asciiz "p1u0T0S0p2p2T1S1p4u0T2S2dL0U0L1U1u1p5*fp6S3L0U0L2U2u2T0S0xr"
native_real_while_binary_sub_nonzero_pattern:
    .asciiz "p1u0T0S0p3u0T1S1p5u0T2S2dL0U0L1U1u1p6*fp7S3L0U0L2U2u2T0S0xr"

native_real_while_check:
    .byte $AD,$00,$00,$AE,$00,$00,$8D,$D1,$03,$8E,$D2,$03
native_real_while_check_end:
native_real_while_exit:
    .byte $A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF
native_real_while_exit_end:

native_real_while_name_loop:
    .asciiz "__whloop"
native_real_while_name_data:
    .asciiz "__idata"
native_real_while_name_a:
    .asciiz "__wha"
native_real_while_name_b:
    .asciiz "__whb"
native_real_while_name_c:
    .asciiz "__whc"
native_real_while_name_y:
    .asciiz "__why"
native_real_while_name_y_hi:
    .asciiz "__whyhi"
native_real_while_name_pointer:
    .asciiz "__whptr"

native_real_while_simple_debug_offsets:
    .byte 0,17,20,20,20,37,40,40,40,40,40,53,53,66,69,69,69,73,73,83,96,103,103,103,119
native_real_while_binary_debug_offsets:
    .byte 0,17,20,20,20,37,40,40,40,57,60,60,60,60,60,73,73,86,89,89,89,93,93,103,103,116,116,142,145,145,145,161

native_real_while_mode:
    .byte $00
native_real_while_layout:
    .byte $00
native_real_while_body_op:
    .byte $00
native_real_while_relation:
    .byte $00
native_real_while_left:
    .byte $00
native_real_while_right:
    .byte $00
native_real_while_update:
    .byte $00
native_real_while_store:
    .byte $00
native_real_while_cmp:
    .byte $00
native_real_while_skip:
    .byte $00
native_real_while_update_target:
    .byte $00
native_real_while_byte:
    .byte $00
native_real_while_value_temp:
    .byte $00
native_real_while_count:
    .byte $00
native_real_while_export_size:
    .byte $00
native_real_while_pointer_index:
    .byte $00
native_real_while_pointer_zp:
    .byte $00
native_real_while_import_index:
    .byte $00
native_real_while_const_ptr:
    .word $0000
