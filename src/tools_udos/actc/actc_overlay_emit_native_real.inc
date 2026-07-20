; Compiler-owned native lowering for straight-line REAL bridge slices.

NATIVE_REAL_MODE_PRINT = 1
NATIVE_REAL_MODE_TO_INT = 2
NATIVE_REAL_MODE_BINARY = 3
NATIVE_REAL_MODE_UNARY = 4
NATIVE_REAL_MODE_INPUT_PRINT = 5
NATIVE_REAL_MODE_INPUT_STORED = 6
NATIVE_REAL_MODE_FUNCTION = 7
NATIVE_REAL_MODE_BITS_PRINT = 8
NATIVE_REAL_PATTERN_MATCH_SECOND_PARAM = $F5
NATIVE_REAL_PATTERN_CAPTURE_SECOND_PARAM = $F6
NATIVE_REAL_PATTERN_MATCH_SECOND_ARG = $F7
NATIVE_REAL_PATTERN_CAPTURE_SECOND_ARG = $F8
NATIVE_REAL_PATTERN_MATCH_PARAM = $F9
NATIVE_REAL_PATTERN_CAPTURE_PARAM = $FA
NATIVE_REAL_PATTERN_MATCH_TARGET = $FB
NATIVE_REAL_PATTERN_CAPTURE_TARGET = $FC
NATIVE_REAL_PATTERN_MATCH_SOURCE = $FD
NATIVE_REAL_PATTERN_CAPTURE_SOURCE = $FE

NATIVE_REAL_CODE_SIZE = 52
NATIVE_REAL_DATA_OFFSET = NATIVE_REAL_CODE_SIZE
NATIVE_REAL_POINTER_OFFSET = NATIVE_REAL_DATA_OFFSET + 4
NATIVE_REAL_ROOT_SIZE = NATIVE_REAL_POINTER_OFFSET + 2
NATIVE_REAL_BITS_CODE_SIZE = 32
NATIVE_REAL_BITS_DATA_OFFSET = NATIVE_REAL_BITS_CODE_SIZE
NATIVE_REAL_BITS_POINTER_OFFSET = NATIVE_REAL_BITS_DATA_OFFSET + 4
NATIVE_REAL_BITS_ROOT_SIZE = NATIVE_REAL_BITS_POINTER_OFFSET + 2
NATIVE_REAL_TO_INT_CODE_SIZE = 58
NATIVE_REAL_TO_INT_DATA_OFFSET = NATIVE_REAL_TO_INT_CODE_SIZE
NATIVE_REAL_TO_INT_RESULT_OFFSET = NATIVE_REAL_TO_INT_DATA_OFFSET + 4
NATIVE_REAL_TO_INT_RESULT_HI_OFFSET = NATIVE_REAL_TO_INT_RESULT_OFFSET + 1
NATIVE_REAL_TO_INT_POINTER_OFFSET = NATIVE_REAL_TO_INT_DATA_OFFSET + 6
NATIVE_REAL_TO_INT_ROOT_SIZE = NATIVE_REAL_TO_INT_POINTER_OFFSET + 2
NATIVE_REAL_BINARY_CODE_SIZE = 114
NATIVE_REAL_BINARY_DATA_OFFSET = NATIVE_REAL_BINARY_CODE_SIZE
NATIVE_REAL_BINARY_A_OFFSET = NATIVE_REAL_BINARY_DATA_OFFSET
NATIVE_REAL_BINARY_B_OFFSET = NATIVE_REAL_BINARY_A_OFFSET + 4
NATIVE_REAL_BINARY_X_OFFSET = NATIVE_REAL_BINARY_B_OFFSET + 4
NATIVE_REAL_BINARY_POINTER_OFFSET = NATIVE_REAL_BINARY_X_OFFSET + 4
NATIVE_REAL_BINARY_ROOT_SIZE = NATIVE_REAL_BINARY_POINTER_OFFSET + 6
NATIVE_REAL_UNARY_CODE_SIZE = 81
NATIVE_REAL_UNARY_DATA_OFFSET = NATIVE_REAL_UNARY_CODE_SIZE
NATIVE_REAL_UNARY_A_OFFSET = NATIVE_REAL_UNARY_DATA_OFFSET
NATIVE_REAL_UNARY_X_OFFSET = NATIVE_REAL_UNARY_A_OFFSET + 4
NATIVE_REAL_UNARY_POINTER_OFFSET = NATIVE_REAL_UNARY_X_OFFSET + 4
NATIVE_REAL_UNARY_ROOT_SIZE = NATIVE_REAL_UNARY_POINTER_OFFSET + 4
NATIVE_REAL_INPUT_CODE_SIZE = 60
NATIVE_REAL_INPUT_DATA_OFFSET = NATIVE_REAL_INPUT_CODE_SIZE
NATIVE_REAL_INPUT_POINTER_OFFSET = NATIVE_REAL_INPUT_DATA_OFFSET + 4
NATIVE_REAL_INPUT_ROOT_SIZE = NATIVE_REAL_INPUT_POINTER_OFFSET + 2
NATIVE_REAL_INPUT_STORED_CODE_SIZE = 68
NATIVE_REAL_INPUT_STORED_DATA_OFFSET = NATIVE_REAL_INPUT_STORED_CODE_SIZE
NATIVE_REAL_INPUT_STORED_RESULT_OFFSET = NATIVE_REAL_INPUT_STORED_DATA_OFFSET
NATIVE_REAL_INPUT_STORED_RESULT_HI_OFFSET = NATIVE_REAL_INPUT_STORED_RESULT_OFFSET + 1
NATIVE_REAL_INPUT_STORED_A_OFFSET = NATIVE_REAL_INPUT_STORED_DATA_OFFSET + 2
NATIVE_REAL_INPUT_STORED_POINTER_OFFSET = NATIVE_REAL_INPUT_STORED_A_OFFSET + 4
NATIVE_REAL_INPUT_STORED_ROOT_SIZE = NATIVE_REAL_INPUT_STORED_POINTER_OFFSET + 2
NATIVE_REAL_FUNCTION_MAIN_CODE_SIZE = 61
NATIVE_REAL_FUNCTION_CODE_OFFSET = NATIVE_REAL_FUNCTION_MAIN_CODE_SIZE
NATIVE_REAL_FUNCTION_CODE_SIZE = 5
NATIVE_REAL_FUNCTION_DATA_OFFSET = NATIVE_REAL_FUNCTION_CODE_OFFSET + NATIVE_REAL_FUNCTION_CODE_SIZE
NATIVE_REAL_PARAM_FUNCTION_MAIN_CODE_SIZE = 69
NATIVE_REAL_PARAM_FUNCTION_CODE_OFFSET = NATIVE_REAL_PARAM_FUNCTION_MAIN_CODE_SIZE
NATIVE_REAL_PARAM_FUNCTION_CODE_SIZE = 45
NATIVE_REAL_PARAM_FUNCTION_DATA_OFFSET = NATIVE_REAL_PARAM_FUNCTION_CODE_OFFSET + NATIVE_REAL_PARAM_FUNCTION_CODE_SIZE
NATIVE_REAL_REAL_PARAM_FUNCTION_MAIN_CODE_SIZE = 67
NATIVE_REAL_REAL_PARAM_FUNCTION_CODE_OFFSET = NATIVE_REAL_REAL_PARAM_FUNCTION_MAIN_CODE_SIZE
NATIVE_REAL_REAL_PARAM_FUNCTION_CODE_SIZE = 31
NATIVE_REAL_REAL_PARAM_FUNCTION_DATA_OFFSET = NATIVE_REAL_REAL_PARAM_FUNCTION_CODE_OFFSET + NATIVE_REAL_REAL_PARAM_FUNCTION_CODE_SIZE
NATIVE_REAL_TWO_PARAM_FUNCTION_MAIN_CODE_SIZE = 88
NATIVE_REAL_TWO_PARAM_FUNCTION_CODE_OFFSET = NATIVE_REAL_TWO_PARAM_FUNCTION_MAIN_CODE_SIZE
NATIVE_REAL_TWO_PARAM_FUNCTION_CODE_SIZE = 47
NATIVE_REAL_TWO_PARAM_FUNCTION_DATA_OFFSET = NATIVE_REAL_TWO_PARAM_FUNCTION_CODE_OFFSET + NATIVE_REAL_TWO_PARAM_FUNCTION_CODE_SIZE

native_real_detect:
    lda #$00
    sta native_real_active
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$02
    bne :+
    jmp native_real_detect_function
:
    cmp #$01
    beq :+
    jmp native_real_detect_no
:
    lda #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    jsr load_context_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcs :+
    jmp native_real_detect_no
:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcs :+
    jmp native_real_detect_no
:
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$01
    beq native_real_detect_print
    cmp #$02
    beq native_real_detect_two_vars
    cmp #$03
    beq native_real_detect_binary
    jmp native_real_detect_no

native_real_detect_two_vars:
    lda #$04
    ldx #$00
    jsr native_real_var_x_has_type_a
    beq native_real_detect_two_vars_real_first
    lda #$04
    ldx #$01
    jsr native_real_var_x_has_type_a
    beq native_real_detect_two_vars_input_stored
    jmp native_real_detect_no
native_real_detect_two_vars_real_first:
    lda #$02
    ldx #$01
    jsr native_real_var_x_has_type_a
    beq native_real_detect_two_vars_to_int
    lda #$04
    ldx #$01
    jsr native_real_var_x_has_type_a
    beq native_real_detect_two_vars_unary
    jmp native_real_detect_no
native_real_detect_two_vars_to_int:
    lda #NATIVE_REAL_MODE_TO_INT
    bne native_real_detect_mode_ok
native_real_detect_two_vars_unary:
    lda #NATIVE_REAL_MODE_UNARY
    bne native_real_detect_mode_ok
native_real_detect_two_vars_input_stored:
    lda #NATIVE_REAL_MODE_INPUT_STORED
    bne native_real_detect_mode_ok

native_real_detect_print:
    lda #$04
    ldx #$00
    jsr native_real_var_x_has_type_a
    beq :+
    jmp native_real_detect_no
:
    lda #NATIVE_REAL_MODE_PRINT
    bne native_real_detect_mode_ok

native_real_detect_binary:
    lda #$04
    ldx #$00
    jsr native_real_var_x_has_type_a
    beq :+
    jmp native_real_detect_no
:
    lda #$04
    ldx #$01
    jsr native_real_var_x_has_type_a
    beq :+
    jmp native_real_detect_no
:
    lda #$04
    ldx #$02
    jsr native_real_var_x_has_type_a
    beq :+
    jmp native_real_detect_no
:
    lda #NATIVE_REAL_MODE_BINARY
native_real_detect_mode_ok:
    sta compare_char_local
    lda #$01
    sta native_real_literal_index
    lda compare_char_local
    cmp #NATIVE_REAL_MODE_INPUT_STORED
    bne native_real_detect_mode_helper_ready
    lda #$02
    sta native_real_literal_index
    jsr native_real_detect_input_helper
    bcs native_real_detect_mode_helper_ready
    jmp native_real_detect_no
native_real_detect_mode_helper_ready:

    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda compare_char_local
    cmp #NATIVE_REAL_MODE_TO_INT
    beq native_real_detect_to_int_pattern
    cmp #NATIVE_REAL_MODE_BINARY
    beq native_real_detect_binary_pattern
    cmp #NATIVE_REAL_MODE_UNARY
    beq native_real_detect_unary_pattern
    cmp #NATIVE_REAL_MODE_INPUT_STORED
    beq native_real_detect_input_stored_pattern
    lda #<native_real_body_pattern
    sta ACTC_OVERLAY_WORK_ZP
    lda #>native_real_body_pattern
    sta ACTC_OVERLAY_WORK_ZP+1
    jmp native_real_detect_pattern_ready
native_real_detect_to_int_pattern:
    lda #<native_real_to_int_body_pattern
    sta ACTC_OVERLAY_WORK_ZP
    lda #>native_real_to_int_body_pattern
    sta ACTC_OVERLAY_WORK_ZP+1
    jmp native_real_detect_pattern_ready
native_real_detect_binary_pattern:
    lda #<native_real_binary_body_pattern
    sta ACTC_OVERLAY_WORK_ZP
    lda #>native_real_binary_body_pattern
    sta ACTC_OVERLAY_WORK_ZP+1
    jmp native_real_detect_pattern_ready
native_real_detect_unary_pattern:
    lda #$00
    sta native_real_literal_index
    lda #<native_real_unary_signed_body_pattern
    sta ACTC_OVERLAY_WORK_ZP
    lda #>native_real_unary_signed_body_pattern
    sta ACTC_OVERLAY_WORK_ZP+1
    jmp native_real_detect_pattern_ready
native_real_detect_input_stored_pattern:
    lda #<native_real_input_stored_body_pattern
    sta ACTC_OVERLAY_WORK_ZP
    lda #>native_real_input_stored_body_pattern
    sta ACTC_OVERLAY_WORK_ZP+1
native_real_detect_pattern_ready:
    ldy #$00
native_real_detect_body_loop:
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_byte
    jsr emit_object_peek_payload_y
    cmp native_real_byte
    beq native_real_detect_body_byte_ok
    lda compare_char_local
    cmp #NATIVE_REAL_MODE_PRINT
    bne native_real_detect_body_maybe_bits
    jsr native_real_prepare_bits_print_pattern
    bcc native_real_detect_body_no
    ldy #$00
    jmp native_real_detect_body_loop
native_real_detect_body_maybe_bits:
    cmp #NATIVE_REAL_MODE_BITS_PRINT
    bne native_real_detect_body_maybe_unary
    jsr native_real_prepare_input_print_pattern
    bcc native_real_detect_body_no
    ldy #$00
    jmp native_real_detect_body_loop
native_real_detect_body_maybe_unary:
    cmp #NATIVE_REAL_MODE_UNARY
    bne native_real_detect_body_no
    lda native_real_literal_index
    bne native_real_detect_body_no
    inc native_real_literal_index
    lda #<native_real_unary_positive_body_pattern
    sta ACTC_OVERLAY_WORK_ZP
    lda #>native_real_unary_positive_body_pattern
    sta ACTC_OVERLAY_WORK_ZP+1
    ldy #$00
    jmp native_real_detect_body_loop
native_real_detect_body_no:
    jmp native_real_detect_no
native_real_detect_body_byte_ok:
    lda native_real_byte
    beq native_real_detect_body_ok
    iny
    bne native_real_detect_body_loop
native_real_detect_no:
    clc
    rts
native_real_detect_body_ok:
    ldx native_real_literal_index
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_value_lo
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_value_hi
    lda compare_char_local
    cmp #NATIVE_REAL_MODE_BINARY
    beq native_real_detect_load_binary_rhs
    cmp #NATIVE_REAL_MODE_BITS_PRINT
    beq native_real_detect_load_bits_rhs
    cmp #NATIVE_REAL_MODE_INPUT_PRINT
    beq native_real_detect_load_input_literals
    cmp #NATIVE_REAL_MODE_INPUT_STORED
    beq native_real_detect_load_input_literals
    jmp native_real_detect_activate
native_real_detect_load_binary_rhs:
    ldx #$03
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_rhs_value_lo
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_rhs_value_hi
    jmp native_real_detect_activate
native_real_detect_load_bits_rhs:
    ldx #$01
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_rhs_value_lo
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_rhs_value_hi
    jmp native_real_detect_activate
native_real_detect_load_input_literals:
    jsr native_real_load_input_literals
    bcs native_real_detect_activate
    jmp native_real_detect_no
native_real_detect_activate:
    lda compare_char_local
    sta native_real_active
    sec
    rts

native_real_detect_function:
    lda #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    jsr load_context_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcs :+
    jmp native_real_detect_function_no
:
    ldx #$01
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcs :+
    jmp native_real_detect_function_no
:

    ldx #$00
    lda #ACTC_OVERLAY_CTX_LOAD_PROC_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_PROC_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_function_proc_meta
    and #(ACTC_PROC_META_FUNCTION | ACTC_PROC_META_REAL_RETURN)
    cmp #(ACTC_PROC_META_FUNCTION | ACTC_PROC_META_REAL_RETURN)
    beq :+
    jmp native_real_detect_function_no
:
    lda native_real_function_proc_meta
    and #ACTC_PROC_META_PARAM_COUNT_MASK
    cmp #$03
    bcs native_real_detect_function_no_near
    sta native_real_function_param_count
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_function_param_index
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq :+
    jmp native_real_detect_function_no
:

    ldx #$01
    lda #ACTC_OVERLAY_CTX_LOAD_PROC_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_PROC_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    bne native_real_detect_function_no_near
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    bne native_real_detect_function_no_near

    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$02
    bcc native_real_detect_function_no_near
    sta native_real_function_var_count
    lda #ACTC_OVERLAY_CTX_MODULE_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    sta native_real_function_module_var_count
    clc
    adc native_real_function_param_count
    cmp native_real_function_var_count
    beq native_real_detect_function_var_setup
native_real_detect_function_no_near:
    jmp native_real_detect_function_no
native_real_detect_function_var_setup:
    lda #$00
    sta native_real_function_data_size
    ldx #$00
native_real_detect_function_var_loop:
    lda native_real_function_param_count
    beq native_real_detect_function_var_width
    cpx native_real_function_param_index
    bne native_real_detect_function_var_width
    lda native_real_function_data_size
    sta native_real_function_param_offset
native_real_detect_function_var_width:
    jsr native_real_load_var_width_x
    cmp #$02
    beq native_real_detect_function_var_width_ok
    cmp #$04
    bne native_real_detect_function_no_near
native_real_detect_function_var_width_ok:
    clc
    adc native_real_function_data_size
    sta native_real_function_data_size
    inx
    cpx native_real_function_var_count
    bcc native_real_detect_function_var_loop
    lda native_real_function_param_count
    beq native_real_detect_function_counts
    lda native_real_function_param_index
    cmp native_real_function_module_var_count
    bne native_real_detect_function_no_near
    tax
    jsr native_real_load_var_width_x
    cmp #$02
    beq native_real_detect_function_counts
    cmp #$04
    bne native_real_detect_function_no_near
native_real_detect_function_counts:
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$01
    bne native_real_detect_function_no_near
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    ldx native_real_function_param_count
    cpx #$00
    beq native_real_detect_function_two_ints
    cpx #$02
    beq native_real_detect_function_two_real_param_ints
    sta native_real_value_lo
    ldx native_real_function_param_index
    jsr native_real_load_var_width_x
    cmp #$04
    beq native_real_detect_function_real_param_ints
    lda native_real_value_lo
    cmp #$01
    bne native_real_detect_function_no_near
    jmp native_real_detect_function_patterns
native_real_detect_function_real_param_ints:
    lda native_real_value_lo
    cmp #$02
    beq :+
    jmp native_real_detect_function_no_near
:
    jmp native_real_detect_function_patterns
native_real_detect_function_two_real_param_ints:
    cmp #$04
    beq :+
    jmp native_real_detect_function_no_near
:
    ldx native_real_function_param_index
    jsr native_real_load_var_width_x
    cmp #$04
    beq :+
    jmp native_real_detect_function_no_near
:
    inx
    jsr native_real_load_var_width_x
    cmp #$04
    beq :+
    jmp native_real_detect_function_no_near
:
    jmp native_real_detect_function_patterns
native_real_detect_function_two_ints:
    cmp #$02
    beq native_real_detect_function_patterns
    jmp native_real_detect_function_no_near
native_real_detect_function_patterns:
    lda #ACTC_OVERLAY_CTX_STRING_COUNT_PTR_LO
    jsr load_count_from_context
    beq :+
    jmp native_real_detect_function_no_near
:

    lda native_real_function_param_count
    bne :+
    jmp native_real_detect_function_no_param_patterns
:
    cmp #$02
    bne :+
    jmp native_real_detect_function_two_real_param_patterns
:
    ldx native_real_function_param_index
    jsr native_real_load_var_width_x
    cmp #$04
    beq native_real_detect_function_real_param_patterns
    ldx #$00
    lda #<native_real_param_function_return_body_pattern
    ldy #>native_real_param_function_return_body_pattern
    jsr native_real_body_x_matches_pattern_ay
    bcs :+
    jmp native_real_detect_function_no_near
:
    lda native_real_function_source_selector
    sta native_real_value_hi
    lda native_real_function_param_selector
    ora #$80
    sta native_real_function_arg_selector
    ldx #$01
    lda #<native_real_param_function_main_body_pattern
    ldy #>native_real_param_function_main_body_pattern
    jsr native_real_body_x_matches_pattern_ay
    bcc :+
    jmp native_real_detect_function_validate_vars
:
    ldx #$01
    lda #<native_real_param_function_variable_main_body_pattern
    ldy #>native_real_param_function_variable_main_body_pattern
    jsr native_real_body_x_matches_pattern_ay
    bcs :+
    jmp native_real_detect_function_no
:
    lda native_real_function_source_selector
    sta native_real_function_arg_selector
    jsr external_import_selector_to_index
    bcs :+
    jmp native_real_detect_function_no
:
    cmp native_real_function_module_var_count
    bcc :+
    jmp native_real_detect_function_no
:
    tax
    jsr native_real_load_var_width_x
    cmp #$02
    beq :+
    jmp native_real_detect_function_no
:
    lda native_real_value_hi
    sta native_real_function_source_selector
    jmp native_real_detect_function_validate_vars
native_real_detect_function_real_param_patterns:
    ldx #$00
    lda #<native_real_real_param_function_return_body_pattern
    ldy #>native_real_real_param_function_return_body_pattern
    jsr native_real_body_x_matches_pattern_ay
    bcs :+
    jmp native_real_detect_function_no_near
:
    ldx #$01
    lda #<native_real_real_param_function_main_body_pattern
    ldy #>native_real_real_param_function_main_body_pattern
    jsr native_real_body_x_matches_pattern_ay
    bcs :+
    jmp native_real_detect_function_no
:
    lda native_real_function_source_selector
    sta native_real_function_arg_selector
    jsr external_import_selector_to_index
    bcs :+
    jmp native_real_detect_function_no
:
    cmp native_real_function_module_var_count
    bcc :+
    jmp native_real_detect_function_no
:
    tax
    jsr native_real_load_var_width_x
    cmp #$04
    beq :+
    jmp native_real_detect_function_no
:
    lda native_real_function_param_selector
    sta native_real_function_source_selector
    lda #$02
    sta native_real_function_param_count
    jmp native_real_detect_function_validate_vars
native_real_detect_function_two_real_param_patterns:
    ldx #$00
    lda #<native_real_two_param_function_return_body_pattern
    ldy #>native_real_two_param_function_return_body_pattern
    jsr native_real_body_x_matches_pattern_ay
    bcs :+
    jmp native_real_detect_function_no_near
:
    ldx #$01
    lda #<native_real_two_param_function_main_body_pattern
    ldy #>native_real_two_param_function_main_body_pattern
    jsr native_real_body_x_matches_pattern_ay
    bcs :+
    jmp native_real_detect_function_no
:
    lda native_real_function_source_selector
    sta native_real_function_arg_selector
    lda native_real_function_param_selector
    sta native_real_function_source_selector
    lda #$03
    sta native_real_function_param_count
    lda native_real_function_second_param_selector
    jsr native_real_function_selector_a_is_real
    beq :+
    jmp native_real_detect_function_no
:
    lda native_real_function_arg_selector
    jsr native_real_function_selector_a_is_real
    beq :+
    jmp native_real_detect_function_no
:
    lda native_real_function_second_arg_selector
    jsr native_real_function_selector_a_is_real
    beq :+
    jmp native_real_detect_function_no
:
    jmp native_real_detect_function_validate_vars
native_real_detect_function_no_param_patterns:
    ldx #$00
    lda #<native_real_function_return_body_pattern
    ldy #>native_real_function_return_body_pattern
    jsr native_real_body_x_matches_pattern_ay
    bcs :+
    jmp native_real_detect_function_no
:
    ldx #$01
    lda #<native_real_function_main_body_pattern
    ldy #>native_real_function_main_body_pattern
    jsr native_real_body_x_matches_pattern_ay
    bcs :+
    jmp native_real_detect_function_no
:
native_real_detect_function_validate_vars:
    lda native_real_function_source_selector
    jsr native_real_function_selector_a_is_real
    bne native_real_detect_function_no
    lda native_real_function_target_selector
    jsr native_real_function_selector_a_is_real
    bne native_real_detect_function_no

    lda native_real_function_param_count
    cmp #$03
    beq native_real_detect_function_two_literals
    cmp #$02
    beq native_real_detect_function_literal_one
    lda #$01
    sec
    sbc native_real_function_param_count
    jmp native_real_detect_function_literal_ready
native_real_detect_function_literal_one:
    lda #$01
native_real_detect_function_literal_ready:
    tax
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_value_lo
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_value_hi
    jmp native_real_detect_function_activate
native_real_detect_function_two_literals:
    ldx #$01
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_value_lo
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_value_hi
    ldx #$03
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_second_value_lo
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_second_value_hi
native_real_detect_function_activate:
    lda #NATIVE_REAL_MODE_FUNCTION
    sta native_real_active
    sec
    rts
native_real_detect_function_no:
    jmp native_real_detect_no

native_real_body_x_matches_pattern_ay:
    sta native_real_const_ptr
    sty native_real_const_ptr+1
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda native_real_const_ptr
    sta ACTC_OVERLAY_WORK_ZP
    lda native_real_const_ptr+1
    sta ACTC_OVERLAY_WORK_ZP+1
    ldy #$00
native_real_body_x_matches_pattern_loop:
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_byte
    cmp #NATIVE_REAL_PATTERN_CAPTURE_PARAM
    beq native_real_body_x_capture_param
    cmp #NATIVE_REAL_PATTERN_MATCH_PARAM
    bne :+
    jmp native_real_body_x_match_param
:
    cmp #NATIVE_REAL_PATTERN_CAPTURE_SOURCE
    beq native_real_body_x_capture_source
    cmp #NATIVE_REAL_PATTERN_MATCH_SOURCE
    bne :+
    jmp native_real_body_x_match_source
:
    cmp #NATIVE_REAL_PATTERN_CAPTURE_TARGET
    beq native_real_body_x_capture_target
    cmp #NATIVE_REAL_PATTERN_MATCH_TARGET
    bne :+
    jmp native_real_body_x_match_target
:
    cmp #NATIVE_REAL_PATTERN_CAPTURE_SECOND_PARAM
    beq native_real_body_x_capture_second_param
    cmp #NATIVE_REAL_PATTERN_MATCH_SECOND_PARAM
    beq native_real_body_x_match_second_param
    cmp #NATIVE_REAL_PATTERN_CAPTURE_SECOND_ARG
    beq native_real_body_x_capture_second_arg
    cmp #NATIVE_REAL_PATTERN_MATCH_SECOND_ARG
    beq native_real_body_x_match_second_arg
    jsr emit_object_peek_payload_y
    cmp native_real_byte
    beq native_real_body_x_matches_pattern_byte_ok
    jmp native_real_body_x_matches_pattern_no
native_real_body_x_matches_pattern_byte_ok:
    lda (ACTC_OVERLAY_WORK_ZP),y
    bne :+
    jmp native_real_body_x_matches_pattern_yes
:
    iny
    bne native_real_body_x_matches_pattern_loop
native_real_body_x_capture_source:
    jsr emit_object_peek_payload_y
    sta native_real_function_source_selector
    jmp native_real_body_x_validate_selector
native_real_body_x_capture_target:
    jsr emit_object_peek_payload_y
    sta native_real_function_target_selector
native_real_body_x_validate_selector:
    jsr external_import_selector_to_index
    bcc native_real_body_x_matches_pattern_no
    cmp native_real_function_var_count
    bcs native_real_body_x_matches_pattern_no
    bcc native_real_body_x_matches_pattern_byte_ok
native_real_body_x_capture_param:
    jsr emit_object_peek_payload_y
    sta native_real_function_param_selector
    jsr external_import_selector_to_index
    bcc native_real_body_x_matches_pattern_no
    cmp native_real_function_param_index
    beq native_real_body_x_matches_pattern_byte_ok
    bne native_real_body_x_matches_pattern_no
native_real_body_x_capture_second_param:
    jsr emit_object_peek_payload_y
    sta native_real_function_second_param_selector
    jsr external_import_selector_to_index
    bcc native_real_body_x_matches_pattern_no
    sec
    sbc native_real_function_param_index
    cmp #$01
    beq native_real_body_x_matches_pattern_byte_ok
    bne native_real_body_x_matches_pattern_no
native_real_body_x_match_second_param:
    jsr emit_object_peek_payload_y
    cmp native_real_function_second_param_selector
    beq native_real_body_x_matches_pattern_byte_ok
    bne native_real_body_x_matches_pattern_no
native_real_body_x_capture_second_arg:
    jsr emit_object_peek_payload_y
    sta native_real_function_second_arg_selector
    jmp native_real_body_x_validate_selector
native_real_body_x_match_second_arg:
    jsr emit_object_peek_payload_y
    cmp native_real_function_second_arg_selector
    beq native_real_body_x_matches_pattern_byte_ok
    bne native_real_body_x_matches_pattern_no
native_real_body_x_match_param:
    jsr emit_object_peek_payload_y
    cmp native_real_function_param_selector
    beq native_real_body_x_matches_pattern_byte_ok
    bne native_real_body_x_matches_pattern_no
native_real_body_x_match_source:
    jsr emit_object_peek_payload_y
    cmp native_real_function_source_selector
    beq native_real_body_x_matches_pattern_byte_ok
    bne native_real_body_x_matches_pattern_no
native_real_body_x_match_target:
    jsr emit_object_peek_payload_y
    cmp native_real_function_target_selector
    bne native_real_body_x_matches_pattern_no
    jmp native_real_body_x_matches_pattern_byte_ok
native_real_body_x_matches_pattern_no:
    clc
    rts
native_real_body_x_matches_pattern_yes:
    sec
    rts

native_real_var_x_has_type_a:
    sta native_real_byte
    jsr native_real_load_var_width_x
    cmp native_real_byte
    rts

native_real_function_selector_a_is_real:
    jsr external_import_selector_to_index
    tax
    jsr native_real_load_var_width_x
    cmp #$04
    rts

native_real_load_var_width_x:
    lda #ACTC_OVERLAY_CTX_LOAD_VAR_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    rts

native_real_prepare_bits_print_pattern:
    lda #NATIVE_REAL_MODE_BITS_PRINT
    sta compare_char_local
    lda #$00
    sta native_real_literal_index
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #<native_real_bits_body_pattern
    sta ACTC_OVERLAY_WORK_ZP
    lda #>native_real_bits_body_pattern
    sta ACTC_OVERLAY_WORK_ZP+1
    sec
    rts

native_real_prepare_input_print_pattern:
    jsr native_real_detect_input_helper
    bcc native_real_prepare_input_print_pattern_no
    lda #NATIVE_REAL_MODE_INPUT_PRINT
    sta compare_char_local
    lda #$02
    sta native_real_literal_index
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #<native_real_input_body_pattern
    sta ACTC_OVERLAY_WORK_ZP
    lda #>native_real_input_body_pattern
    sta ACTC_OVERLAY_WORK_ZP+1
    sec
    rts
native_real_prepare_input_print_pattern_no:
    clc
    rts

native_real_load_input_literals:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_input_value_lo
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_input_value_hi
    ldx #$03
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp #$01
    bne native_real_load_input_literals_no
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    bne native_real_load_input_literals_no
    sec
    rts
native_real_load_input_literals_no:
    clc
    rts

native_real_detect_input_helper:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_EXTERNAL_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    ldy #$00
    lda (ACTC_OVERLAY_SCAN_ZP),y
    cmp #'R'
    bne native_real_detect_input_helper_no
    iny
    lda (ACTC_OVERLAY_SCAN_ZP),y
    cmp #'T'
    bne native_real_detect_input_helper_no
    iny
    lda (ACTC_OVERLAY_SCAN_ZP),y
    cmp #'_'
    bne native_real_detect_input_helper_no
    sec
    rts
native_real_detect_input_helper_no:
    clc
    rts

native_real_emit_debug_offset:
    ldx body_debug_index_data
    lda native_real_active
    cmp #NATIVE_REAL_MODE_FUNCTION
    beq native_real_emit_debug_offset_function
    cmp #NATIVE_REAL_MODE_TO_INT
    beq native_real_emit_debug_offset_to_int
    cmp #NATIVE_REAL_MODE_BINARY
    beq native_real_emit_debug_offset_binary
    cmp #NATIVE_REAL_MODE_UNARY
    beq native_real_emit_debug_offset_unary
    cmp #NATIVE_REAL_MODE_INPUT_PRINT
    beq native_real_emit_debug_offset_input
    cmp #NATIVE_REAL_MODE_INPUT_STORED
    beq native_real_emit_debug_offset_input_stored
    cmp #NATIVE_REAL_MODE_BITS_PRINT
    beq native_real_emit_debug_offset_bits
    lda native_real_debug_offsets,x
    jmp native_real_emit_debug_offset_ready
native_real_emit_debug_offset_to_int:
    lda native_real_to_int_debug_offsets,x
    jmp native_real_emit_debug_offset_ready
native_real_emit_debug_offset_binary:
    lda native_real_binary_debug_offsets,x
    jmp native_real_emit_debug_offset_ready
native_real_emit_debug_offset_unary:
    lda native_real_unary_debug_offsets,x
    jmp native_real_emit_debug_offset_ready
native_real_emit_debug_offset_input:
    lda native_real_input_debug_offsets,x
    jmp native_real_emit_debug_offset_ready
native_real_emit_debug_offset_input_stored:
    lda native_real_input_stored_debug_offsets,x
    jmp native_real_emit_debug_offset_ready
native_real_emit_debug_offset_bits:
    lda native_real_bits_debug_offsets,x
    jmp native_real_emit_debug_offset_ready
native_real_emit_debug_offset_function:
    lda native_real_function_param_count
    beq native_real_emit_debug_offset_function_no_param
    lda entry_index_data
    beq native_real_emit_debug_offset_param_function_return
    lda native_real_function_param_count
    cmp #$03
    beq native_real_emit_debug_offset_two_param_function_main
    cmp #$02
    beq native_real_emit_debug_offset_real_param_function_main
    lda native_real_function_arg_selector
    bpl native_real_emit_debug_offset_param_function_variable
    lda native_real_param_function_main_debug_offsets,x
    jmp native_real_emit_debug_offset_ready
native_real_emit_debug_offset_param_function_variable:
    lda native_real_param_function_variable_main_debug_offsets,x
    jmp native_real_emit_debug_offset_ready
native_real_emit_debug_offset_real_param_function_main:
    lda native_real_real_param_function_main_debug_offsets,x
    jmp native_real_emit_debug_offset_ready
native_real_emit_debug_offset_two_param_function_main:
    lda native_real_two_param_function_main_debug_offsets,x
    jmp native_real_emit_debug_offset_ready
native_real_emit_debug_offset_param_function_return:
    lda native_real_function_param_count
    cmp #$03
    beq native_real_emit_debug_offset_two_param_function_return
    cmp #$02
    beq native_real_emit_debug_offset_real_param_function_return
    lda native_real_param_function_return_debug_offsets,x
    jmp native_real_emit_debug_offset_ready
native_real_emit_debug_offset_real_param_function_return:
    lda native_real_real_param_function_return_debug_offsets,x
    jmp native_real_emit_debug_offset_ready
native_real_emit_debug_offset_two_param_function_return:
    lda native_real_two_param_function_return_debug_offsets,x
    jmp native_real_emit_debug_offset_ready
native_real_emit_debug_offset_function_no_param:
    lda entry_index_data
    beq native_real_emit_debug_offset_function_return
    lda native_real_function_main_debug_offsets,x
    jmp native_real_emit_debug_offset_ready
native_real_emit_debug_offset_function_return:
    lda native_real_function_return_debug_offsets,x
native_real_emit_debug_offset_ready:
    ldy #$00
    jmp emit_word_decimal

native_real_emit_export_list:
    lda native_real_active
    cmp #NATIVE_REAL_MODE_FUNCTION
    bne :+
    jmp native_real_emit_export_function
:
    lda #$00
    sta word_value_lo
    sta word_value_hi
    ldx #$00
    lda native_real_active
    cmp #NATIVE_REAL_MODE_BINARY
    bne native_real_emit_export_not_binary
    jmp native_real_emit_export_binary
native_real_emit_export_not_binary:
    cmp #NATIVE_REAL_MODE_UNARY
    bne :+
    jmp native_real_emit_export_unary
:
    cmp #NATIVE_REAL_MODE_INPUT_PRINT
    bne :+
    jmp native_real_emit_export_input
:
    cmp #NATIVE_REAL_MODE_INPUT_STORED
    bne :+
    jmp native_real_emit_export_input_stored
:
    lda native_real_active
    cmp #NATIVE_REAL_MODE_TO_INT
    beq native_real_emit_export_root_to_int
    cmp #NATIVE_REAL_MODE_BITS_PRINT
    beq native_real_emit_export_root_bits
    lda #NATIVE_REAL_ROOT_SIZE
    bne native_real_emit_export_root_ready
native_real_emit_export_root_to_int:
    lda #NATIVE_REAL_TO_INT_ROOT_SIZE
    bne native_real_emit_export_root_ready
native_real_emit_export_root_bits:
    lda #NATIVE_REAL_BITS_ROOT_SIZE
native_real_emit_export_root_ready:
    jsr emit_machine_export_line
    jsr native_real_set_scan_name_data
    lda native_real_active
    cmp #NATIVE_REAL_MODE_TO_INT
    beq native_real_emit_export_data_to_int
    cmp #NATIVE_REAL_MODE_BITS_PRINT
    beq native_real_emit_export_data_bits
    lda #NATIVE_REAL_DATA_OFFSET
    ldx #$04
    bne native_real_emit_export_data_ready
native_real_emit_export_data_to_int:
    lda #NATIVE_REAL_TO_INT_DATA_OFFSET
    ldx #$06
    bne native_real_emit_export_data_ready
native_real_emit_export_data_bits:
    lda #NATIVE_REAL_BITS_DATA_OFFSET
    ldx #$04
native_real_emit_export_data_ready:
    jsr native_real_emit_named_export
    lda native_real_active
    cmp #NATIVE_REAL_MODE_TO_INT
    bne native_real_emit_export_pointer
    jsr native_real_set_scan_name_result
    lda #NATIVE_REAL_TO_INT_RESULT_OFFSET
    ldx #$02
    jsr native_real_emit_named_export
    jsr native_real_set_scan_name_result_hi
    lda #NATIVE_REAL_TO_INT_RESULT_HI_OFFSET
    ldx #$01
    jsr native_real_emit_named_export
native_real_emit_export_pointer:
    jsr native_real_set_scan_name_pointer
    lda native_real_active
    cmp #NATIVE_REAL_MODE_TO_INT
    beq native_real_emit_export_pointer_to_int
    cmp #NATIVE_REAL_MODE_BITS_PRINT
    beq native_real_emit_export_pointer_bits
    lda #NATIVE_REAL_POINTER_OFFSET
    ldx #$02
    jmp native_real_emit_named_export
native_real_emit_export_pointer_to_int:
    lda #NATIVE_REAL_TO_INT_POINTER_OFFSET
    ldx #$02
    jmp native_real_emit_named_export
native_real_emit_export_pointer_bits:
    lda #NATIVE_REAL_BITS_POINTER_OFFSET
    ldx #$02
    jmp native_real_emit_named_export

native_real_emit_export_binary:
    lda #NATIVE_REAL_BINARY_ROOT_SIZE
    ldx #$00
    jsr emit_machine_export_line
    jsr native_real_set_scan_name_data
    lda #NATIVE_REAL_BINARY_DATA_OFFSET
    ldx #12
    jsr native_real_emit_named_export
    jsr native_real_set_scan_name_a
    lda #NATIVE_REAL_BINARY_A_OFFSET
    ldx #$04
    jsr native_real_emit_named_export
    jsr native_real_set_scan_name_b
    lda #NATIVE_REAL_BINARY_B_OFFSET
    ldx #$04
    jsr native_real_emit_named_export
    jsr native_real_set_scan_name_x
    lda #NATIVE_REAL_BINARY_X_OFFSET
    ldx #$04
    jsr native_real_emit_named_export
    jsr native_real_set_scan_name_pointer
    lda #NATIVE_REAL_BINARY_POINTER_OFFSET
    ldx #$06
    jmp native_real_emit_named_export

native_real_emit_export_unary:
    lda #NATIVE_REAL_UNARY_ROOT_SIZE
    ldx #$00
    jsr emit_machine_export_line
    jsr native_real_set_scan_name_data
    lda #NATIVE_REAL_UNARY_DATA_OFFSET
    ldx #$08
    jsr native_real_emit_named_export
    jsr native_real_set_scan_name_a
    lda #NATIVE_REAL_UNARY_A_OFFSET
    ldx #$04
    jsr native_real_emit_named_export
    jsr native_real_set_scan_name_x
    lda #NATIVE_REAL_UNARY_X_OFFSET
    ldx #$04
    jsr native_real_emit_named_export
    jsr native_real_set_scan_name_pointer
    lda #NATIVE_REAL_UNARY_POINTER_OFFSET
    ldx #$04
    jmp native_real_emit_named_export

native_real_emit_export_input:
    lda #NATIVE_REAL_INPUT_ROOT_SIZE
    ldx #$00
    jsr emit_machine_export_line
    jsr native_real_set_scan_name_data
    lda #NATIVE_REAL_INPUT_DATA_OFFSET
    ldx #$04
    jsr native_real_emit_named_export
    jsr native_real_set_scan_name_pointer
    lda #NATIVE_REAL_INPUT_POINTER_OFFSET
    ldx #$02
    jmp native_real_emit_named_export

native_real_emit_export_input_stored:
    lda #NATIVE_REAL_INPUT_STORED_ROOT_SIZE
    ldx #$00
    jsr emit_machine_export_line
    jsr native_real_set_scan_name_data
    lda #NATIVE_REAL_INPUT_STORED_DATA_OFFSET
    ldx #$06
    jsr native_real_emit_named_export
    jsr native_real_set_scan_name_result
    lda #NATIVE_REAL_INPUT_STORED_RESULT_OFFSET
    ldx #$02
    jsr native_real_emit_named_export
    jsr native_real_set_scan_name_result_hi
    lda #NATIVE_REAL_INPUT_STORED_RESULT_HI_OFFSET
    ldx #$01
    jsr native_real_emit_named_export
    jsr native_real_set_scan_name_a
    lda #NATIVE_REAL_INPUT_STORED_A_OFFSET
    ldx #$04
    jsr native_real_emit_named_export
    jsr native_real_set_scan_name_pointer
    lda #NATIVE_REAL_INPUT_STORED_POINTER_OFFSET
    ldx #$02
    jmp native_real_emit_named_export

native_real_emit_export_function:
    lda #$00
    sta word_value_lo
    sta word_value_hi
    jsr native_real_function_pointer_offset
    adc #$02
    ldx #$01
    jsr emit_machine_export_line
    jsr native_real_function_code_offset
    sta word_value_lo
    lda #$00
    sta word_value_hi
    jsr native_real_function_code_size
    ldx #$00
    jsr emit_machine_export_line
    lda #$00
    sta native_real_function_var_index
    jsr native_real_function_data_offset
    sta native_real_function_var_offset
native_real_emit_export_function_var_loop:
    lda native_real_function_var_index
    jsr native_real_set_function_var_name_from_index
    ldx native_real_function_var_index
    jsr native_real_load_var_width_x
    sta native_real_function_var_width
    tax
    lda native_real_function_var_offset
    jsr native_real_emit_named_export
    clc
    lda native_real_function_var_offset
    adc native_real_function_var_width
    sta native_real_function_var_offset
    inc native_real_function_var_index
    lda native_real_function_var_index
    cmp native_real_function_var_count
    bcc native_real_emit_export_function_var_loop
    jsr native_real_set_scan_name_data
    ldx native_real_function_data_size
    jsr native_real_function_data_offset
    jsr native_real_emit_named_export
    jsr native_real_set_scan_name_pointer
    jsr native_real_function_pointer_offset
    ldx #$02
native_real_emit_named_export:
    sta word_value_lo
    stx compare_char_local
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
    lda compare_char_local
    ldy #$00
    jsr emit_word_decimal
    jmp emit_newline

native_real_function_pointer_offset:
    jsr native_real_function_data_offset
    clc
    adc native_real_function_data_size
    rts

native_real_function_data_offset:
    lda native_real_function_param_count
    beq native_real_function_data_offset_no_param
    cmp #$03
    beq native_real_function_data_offset_two_param
    cmp #$02
    beq native_real_function_data_offset_real_param
    lda #NATIVE_REAL_PARAM_FUNCTION_DATA_OFFSET
    bne native_real_function_data_offset_store
native_real_function_data_offset_real_param:
    lda #NATIVE_REAL_REAL_PARAM_FUNCTION_DATA_OFFSET
    bne native_real_function_data_offset_store
native_real_function_data_offset_two_param:
    lda #NATIVE_REAL_TWO_PARAM_FUNCTION_DATA_OFFSET
    bne native_real_function_data_offset_store
native_real_function_data_offset_no_param:
    lda #NATIVE_REAL_FUNCTION_DATA_OFFSET
native_real_function_data_offset_store:
    rts

native_real_function_code_offset:
    lda native_real_function_param_count
    beq native_real_function_code_offset_no_param
    cmp #$03
    beq native_real_function_code_offset_two_param
    cmp #$02
    beq native_real_function_code_offset_real_param
    lda #NATIVE_REAL_PARAM_FUNCTION_CODE_OFFSET
    rts
native_real_function_code_offset_real_param:
    lda #NATIVE_REAL_REAL_PARAM_FUNCTION_CODE_OFFSET
    rts
native_real_function_code_offset_two_param:
    lda #NATIVE_REAL_TWO_PARAM_FUNCTION_CODE_OFFSET
    rts
native_real_function_code_offset_no_param:
    lda #NATIVE_REAL_FUNCTION_CODE_OFFSET
    rts

native_real_function_code_size:
    lda native_real_function_param_count
    beq native_real_function_code_size_no_param
    cmp #$03
    beq native_real_function_code_size_two_param
    cmp #$02
    beq native_real_function_code_size_real_param
    lda #NATIVE_REAL_PARAM_FUNCTION_CODE_SIZE
    rts
native_real_function_code_size_real_param:
    lda #NATIVE_REAL_REAL_PARAM_FUNCTION_CODE_SIZE
    rts
native_real_function_code_size_two_param:
    lda #NATIVE_REAL_TWO_PARAM_FUNCTION_CODE_SIZE
    rts
native_real_function_code_size_no_param:
    lda #NATIVE_REAL_FUNCTION_CODE_SIZE
    rts

native_real_set_scan_name_data:
    lda #<native_real_name_data
    ldy #>native_real_name_data
    bne native_real_set_scan_name_ay

native_real_set_scan_name_pointer:
    lda #<native_real_name_pointer
    ldy #>native_real_name_pointer
    bne native_real_set_scan_name_ay

native_real_set_scan_name_a:
    lda #<native_real_name_a
    ldy #>native_real_name_a
    bne native_real_set_scan_name_ay

native_real_set_scan_name_b:
    lda #<native_real_name_b
    ldy #>native_real_name_b
    bne native_real_set_scan_name_ay

native_real_set_scan_name_x:
    lda #<native_real_name_x
    ldy #>native_real_name_x
    bne native_real_set_scan_name_ay

native_real_set_scan_name_result:
    lda #<native_real_name_result
    ldy #>native_real_name_result
    bne native_real_set_scan_name_ay

native_real_set_scan_name_result_hi:
    lda #<native_real_name_result_hi
    ldy #>native_real_name_result_hi
native_real_set_scan_name_ay:
    sta ACTC_OVERLAY_SCAN_ZP
    sty ACTC_OVERLAY_SCAN_ZP+1
    rts

native_real_set_function_var_name_from_index:
    cmp #10
    bcc native_real_function_index_to_selector_digit
    adc #('A'-10-1)
    bne native_real_set_function_var_name
native_real_function_index_to_selector_digit:
    adc #'0'

native_real_set_function_var_name:
    sta native_real_name_var+3
    lda #<native_real_name_var
    ldy #>native_real_name_var
    bne native_real_set_scan_name_ay

native_real_emit_body_marker_list:
    lda native_real_active
    cmp #NATIVE_REAL_MODE_FUNCTION
    bne :+
    jmp native_real_emit_body_marker_function
:
    lda #'b'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #'u'
    jsr emit_char_overlay
    lda #'0'
    jsr emit_char_overlay
    lda native_real_active
    cmp #NATIVE_REAL_MODE_BITS_PRINT
    beq native_real_emit_body_marker_imports_done
    lda #'u'
    jsr emit_char_overlay
    lda #'1'
    jsr emit_char_overlay
    lda native_real_active
    cmp #NATIVE_REAL_MODE_BINARY
    beq native_real_emit_body_marker_third_import
    cmp #NATIVE_REAL_MODE_UNARY
    beq native_real_emit_body_marker_third_import
    cmp #NATIVE_REAL_MODE_INPUT_PRINT
    beq native_real_emit_body_marker_third_import
    cmp #NATIVE_REAL_MODE_INPUT_STORED
    bne native_real_emit_body_marker_imports_done
native_real_emit_body_marker_third_import:
    lda #'u'
    jsr emit_char_overlay
    lda #'2'
    jsr emit_char_overlay
native_real_emit_body_marker_imports_done:
    lda #'M'
    jsr emit_char_overlay
    jsr emit_newline
    lda native_real_active
    cmp #NATIVE_REAL_MODE_TO_INT
    beq native_real_emit_body_marker_to_int
    cmp #NATIVE_REAL_MODE_BINARY
    beq native_real_emit_body_marker_binary
    cmp #NATIVE_REAL_MODE_UNARY
    beq native_real_emit_body_marker_unary
    cmp #NATIVE_REAL_MODE_INPUT_PRINT
    beq native_real_emit_body_marker_input
    cmp #NATIVE_REAL_MODE_INPUT_STORED
    beq native_real_emit_body_marker_input_stored
    lda #$02
    bne native_real_emit_body_marker_count_ready
native_real_emit_body_marker_to_int:
    lda #$04
    bne native_real_emit_body_marker_count_ready
native_real_emit_body_marker_binary:
    lda #$05
    bne native_real_emit_body_marker_count_ready
native_real_emit_body_marker_unary:
    lda #$04
    bne native_real_emit_body_marker_count_ready
native_real_emit_body_marker_input:
    lda #$02
    bne native_real_emit_body_marker_count_ready
native_real_emit_body_marker_input_stored:
    lda #$05
native_real_emit_body_marker_count_ready:
    sta native_real_const_len
native_real_emit_body_marker_loop:
    jsr emit_machine_body_marker_line
    dec native_real_const_len
    bne native_real_emit_body_marker_loop
    rts

native_real_emit_body_marker_function:
    lda #<native_real_function_root_body_marker
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>native_real_function_root_body_marker
    sta ACTC_OVERLAY_SCAN_ZP+1
    jsr emit_scan_zp_string
    jsr emit_newline
    lda native_real_function_param_count
    beq native_real_emit_body_marker_function_count
    jsr emit_scan_zp_string
    jsr emit_newline
    clc
    lda native_real_function_var_count
    adc #$02
    bne native_real_emit_body_marker_function_count_ready
native_real_emit_body_marker_function_count:
    clc
    lda native_real_function_var_count
    adc #$03
native_real_emit_body_marker_function_count_ready:
    sta native_real_const_len
native_real_emit_body_marker_function_loop:
    jsr emit_machine_body_marker_line
    dec native_real_const_len
    bne native_real_emit_body_marker_function_loop
    rts

native_real_emit_machine_code_list:
    lda #'m'
    jsr emit_char_overlay
    lda native_real_active
    cmp #NATIVE_REAL_MODE_FUNCTION
    bne :+
    jmp native_real_emit_function_machine_code
:
    cmp #NATIVE_REAL_MODE_BINARY
    bne native_real_emit_machine_not_binary
    jmp native_real_emit_binary_machine_code
native_real_emit_machine_not_binary:
    cmp #NATIVE_REAL_MODE_UNARY
    bne :+
    jmp native_real_emit_unary_machine_code
:
    cmp #NATIVE_REAL_MODE_INPUT_PRINT
    bne :+
    jmp native_real_emit_input_machine_code
:
    cmp #NATIVE_REAL_MODE_INPUT_STORED
    bne :+
    jmp native_real_emit_input_machine_code
:
    cmp #NATIVE_REAL_MODE_BITS_PRINT
    bne :+
    jmp native_real_emit_bits_machine_code
:
    lda native_real_active
    cmp #NATIVE_REAL_MODE_TO_INT
    bne :+
    jmp native_real_emit_to_int_machine_code
:
    lda #<native_real_set_zp2
    ldy #>native_real_set_zp2
    ldx #(native_real_set_zp2_end-native_real_set_zp2)
    jsr native_real_emit_const_bytes
    jsr native_real_emit_a9
    lda native_real_value_lo
    jsr native_real_emit_byte
    jsr native_real_emit_a2
    lda native_real_value_hi
    jsr native_real_emit_byte
    jsr native_real_emit_jsr_placeholder
    lda #<native_real_set_zp2
    ldy #>native_real_set_zp2
    ldx #(native_real_set_zp2_end-native_real_set_zp2)
    jsr native_real_emit_const_bytes
    jsr native_real_emit_jsr_placeholder
    lda #<native_real_exit
    ldy #>native_real_exit
    ldx #(native_real_exit_end-native_real_exit)
    jsr native_real_emit_const_bytes
    lda #$06
    sta native_real_const_len
:   lda #$00
    jsr native_real_emit_byte
    dec native_real_const_len
    bne :-
    jsr emit_newline
    lda #$03
    jsr native_real_emit_pointer_reloc
    lda #$09
    jsr native_real_emit_pointer_reloc
    lda #18
    ldx #$00
    jsr native_real_emit_import_reloc
    lda #23
    jsr native_real_emit_pointer_reloc
    lda #29
    jsr native_real_emit_pointer_reloc
    lda #34
    ldx #$01
    jsr native_real_emit_import_reloc
    lda #NATIVE_REAL_POINTER_OFFSET
    jsr native_real_emit_data_reloc
    clc
    rts

native_real_emit_bits_machine_code:
    lda #<native_real_set_zp2
    ldy #>native_real_set_zp2
    ldx #(native_real_set_zp2_end-native_real_set_zp2)
    jsr native_real_emit_const_bytes
    jsr native_real_emit_jsr_placeholder
    lda #<native_real_exit
    ldy #>native_real_exit
    ldx #(native_real_exit_end-native_real_exit)
    jsr native_real_emit_const_bytes
    lda native_real_value_lo
    jsr native_real_emit_byte
    lda native_real_value_hi
    jsr native_real_emit_byte
    lda native_real_rhs_value_lo
    jsr native_real_emit_byte
    lda native_real_rhs_value_hi
    jsr native_real_emit_byte
    jsr native_real_emit_zero
    jsr native_real_emit_zero
    jsr emit_newline
    lda #$03
    jsr native_real_emit_pointer_reloc
    lda #$09
    jsr native_real_emit_pointer_reloc
    lda #14
    ldx #$00
    jsr native_real_emit_import_reloc
    lda #NATIVE_REAL_BITS_POINTER_OFFSET
    jsr native_real_emit_data_reloc
    clc
    rts

native_real_emit_function_machine_code:
    lda native_real_function_param_count
    beq native_real_emit_function_machine_code_no_param
    cmp #$03
    bne :+
    jmp native_real_emit_two_param_function_machine_code
:
    cmp #$02
    bne :+
    jmp native_real_emit_real_param_function_machine_code
:   jmp native_real_emit_param_function_machine_code
native_real_emit_function_machine_code_no_param:
    lda #<native_real_function_set_zp6
    ldy #>native_real_function_set_zp6
    ldx #(native_real_function_set_zp6_end-native_real_function_set_zp6)
    jsr native_real_emit_const_bytes
    lda native_real_value_lo
    jsr native_real_emit_byte
    jsr native_real_emit_a2
    lda native_real_value_hi
    jsr native_real_emit_byte
    jsr native_real_emit_jsr_placeholder
    lda #<native_real_function_call_copy
    ldy #>native_real_function_call_copy
    ldx #(native_real_function_call_copy_end-native_real_function_call_copy)
    jsr native_real_emit_const_bytes
    lda #<native_real_exit
    ldy #>native_real_exit
    ldx #(native_real_exit_end-native_real_exit)
    jsr native_real_emit_const_bytes
    lda #<native_real_function_return_pointer
    ldy #>native_real_function_return_pointer
    ldx #(native_real_function_return_pointer_end-native_real_function_return_pointer)
    jsr native_real_emit_const_bytes
    jsr native_real_emit_function_zeros
    lda #$03
    jsr native_real_emit_pointer_reloc
    lda #$09
    jsr native_real_emit_pointer_reloc
    lda #14
    ldx #'l'
    jsr native_real_emit_function_source_byte_reloc
    lda #18
    ldx #'h'
    jsr native_real_emit_function_source_byte_reloc
    lda #26
    ldx #$00
    jsr native_real_emit_import_reloc
    lda #29
    ldx #$00
    jsr native_real_emit_export_reloc
    lda native_real_function_target_selector
    jsr native_real_set_function_var_name
    lda #40
    jsr native_real_emit_named_reloc
    lda #62
    ldx #'l'
    jsr native_real_emit_function_source_byte_reloc
    lda #64
    ldx #'h'
    jsr native_real_emit_function_source_byte_reloc
    jsr native_real_function_pointer_offset
    jsr native_real_emit_data_reloc
    clc
    rts

native_real_emit_param_function_machine_code:
    lda #<native_real_function_set_zp6
    ldy #>native_real_function_set_zp6
    ldx #(native_real_function_set_zp6_pointer_end-native_real_function_set_zp6)
    jsr native_real_emit_const_bytes
    lda native_real_value_lo
    sta native_real_param_argument_setup+3
    lda native_real_value_hi
    sta native_real_param_argument_setup+9
    lda #<native_real_param_argument_setup
    ldy #>native_real_param_argument_setup
    ldx #(native_real_param_argument_setup_end-native_real_param_argument_setup)
    jsr native_real_emit_const_bytes
    lda #<native_real_function_call_copy
    ldy #>native_real_function_call_copy
    ldx #(native_real_function_call_copy_end-native_real_function_call_copy)
    jsr native_real_emit_const_bytes
    lda #<native_real_exit
    ldy #>native_real_exit
    ldx #(native_real_exit_end-native_real_exit)
    jsr native_real_emit_const_bytes

    lda #<native_real_param_store_entry
    ldy #>native_real_param_store_entry
    ldx #(native_real_param_store_entry_end-native_real_param_store_entry)
    jsr native_real_emit_const_bytes
    lda native_real_function_param_offset
    clc
    adc #$01
    jsr native_real_emit_byte
    lda #<native_real_param_store_middle
    ldy #>native_real_param_store_middle
    ldx #(native_real_param_store_middle_end-native_real_param_store_middle)
    jsr native_real_emit_const_bytes
    lda native_real_function_param_offset
    jsr native_real_emit_byte
    lda #<native_real_param_convert_return
    ldy #>native_real_param_convert_return
    ldx #(native_real_param_convert_return_end-native_real_param_convert_return)
    jsr native_real_emit_const_bytes
    jsr native_real_emit_function_zeros
    lda #$03
    jsr native_real_emit_pointer_reloc
    lda #$09
    jsr native_real_emit_pointer_reloc
    lda native_real_function_arg_selector
    and #$7F
    jsr native_real_set_function_var_name
    lda #18
    jsr native_real_emit_named_reloc
    lda #24
    jsr native_real_emit_named_reloc
    lda #28
    jsr native_real_emit_named_reloc
    lda #33
    jsr native_real_emit_named_reloc
    lda #37
    ldx #$00
    jsr native_real_emit_export_reloc
    lda native_real_function_target_selector
    jsr native_real_set_function_var_name
    lda #48
    jsr native_real_emit_named_reloc
    lda #89
    ldx #'l'
    jsr native_real_emit_function_source_byte_reloc
    lda #93
    ldx #'h'
    jsr native_real_emit_function_source_byte_reloc
    lda #107
    ldx #$00
    jsr native_real_emit_import_reloc
    lda #110
    ldx #'l'
    jsr native_real_emit_function_source_byte_reloc
    lda #112
    ldx #'h'
    jsr native_real_emit_function_source_byte_reloc
    jsr native_real_function_pointer_offset
    jsr native_real_emit_data_reloc
    clc
    rts

native_real_emit_real_param_function_machine_code:
    lda #<native_real_function_set_zp6
    ldy #>native_real_function_set_zp6
    ldx #(native_real_function_set_zp6_end-native_real_function_set_zp6)
    jsr native_real_emit_const_bytes
    lda native_real_value_lo
    jsr native_real_emit_byte
    jsr native_real_emit_a2
    lda native_real_value_hi
    jsr native_real_emit_byte
    jsr native_real_emit_jsr_placeholder
    lda #<native_real_real_param_argument_setup
    ldy #>native_real_real_param_argument_setup
    ldx #(native_real_real_param_argument_setup_end-native_real_real_param_argument_setup)
    jsr native_real_emit_const_bytes
    lda #<native_real_function_call_copy
    ldy #>native_real_function_call_copy
    ldx #(native_real_function_call_copy_end-native_real_function_call_copy)
    jsr native_real_emit_const_bytes
    lda #<native_real_exit
    ldy #>native_real_exit
    ldx #(native_real_exit_end-native_real_exit)
    jsr native_real_emit_const_bytes
    lda #<native_real_real_param_store_return
    ldy #>native_real_real_param_store_return
    ldx #(native_real_real_param_store_return_end-native_real_real_param_store_return)
    jsr native_real_emit_const_bytes
    jsr native_real_emit_function_zeros
    lda #$03
    jsr native_real_emit_pointer_reloc
    lda #$09
    jsr native_real_emit_pointer_reloc
    lda #14
    ldx #'l'
    jsr native_real_emit_function_arg_byte_reloc
    lda #18
    ldx #'h'
    jsr native_real_emit_function_arg_byte_reloc
    lda #26
    ldx #$00
    jsr native_real_emit_import_reloc
    lda #29
    ldx #'l'
    jsr native_real_emit_function_arg_byte_reloc
    lda #32
    ldx #'h'
    jsr native_real_emit_function_arg_byte_reloc
    lda #35
    ldx #$00
    jsr native_real_emit_export_reloc
    lda native_real_function_target_selector
    jsr native_real_set_function_var_name
    lda #46
    jsr native_real_emit_named_reloc
    lda native_real_function_source_selector
    jsr native_real_set_function_var_name
    lda #88
    jsr native_real_emit_named_reloc
    lda #94
    ldx #'l'
    jsr native_real_emit_function_source_byte_reloc
    lda #96
    ldx #'h'
    jsr native_real_emit_function_source_byte_reloc
    jsr native_real_function_pointer_offset
    jsr native_real_emit_data_reloc
    clc
    rts

native_real_emit_two_param_function_machine_code:
    lda #<native_real_function_set_zp6
    ldy #>native_real_function_set_zp6
    ldx #(native_real_function_set_zp6_end-native_real_function_set_zp6)
    jsr native_real_emit_const_bytes
    lda native_real_value_lo
    jsr native_real_emit_byte
    jsr native_real_emit_a2
    lda native_real_value_hi
    jsr native_real_emit_byte
    jsr native_real_emit_jsr_placeholder
    lda #<native_real_two_param_next_destination
    ldy #>native_real_two_param_next_destination
    ldx #(native_real_two_param_next_destination_end-native_real_two_param_next_destination)
    jsr native_real_emit_const_bytes
    lda native_real_second_value_lo
    jsr native_real_emit_byte
    jsr native_real_emit_a2
    lda native_real_second_value_hi
    jsr native_real_emit_byte
    jsr native_real_emit_jsr_placeholder
    lda #<native_real_real_param_argument_setup
    ldy #>native_real_real_param_argument_setup
    ldx #(native_real_real_param_argument_setup_end-native_real_real_param_argument_setup)
    jsr native_real_emit_const_bytes
    lda #<native_real_real_param_argument_setup
    ldy #>native_real_real_param_argument_setup
    ldx #(native_real_real_param_argument_setup_end-native_real_real_param_argument_setup)
    jsr native_real_emit_const_bytes
    lda #<native_real_function_call_copy
    ldy #>native_real_function_call_copy
    ldx #(native_real_function_call_copy_end-native_real_function_call_copy)
    jsr native_real_emit_const_bytes
    lda #<native_real_exit
    ldy #>native_real_exit
    ldx #(native_real_exit_end-native_real_exit)
    jsr native_real_emit_const_bytes
    lda #<native_real_two_param_store_return
    ldy #>native_real_two_param_store_return
    ldx #(native_real_two_param_store_return_end-native_real_two_param_store_return)
    jsr native_real_emit_const_bytes
    jsr native_real_emit_function_zeros

    lda #$03
    jsr native_real_emit_pointer_reloc
    lda #$09
    jsr native_real_emit_pointer_reloc
    lda #14
    ldx #'l'
    jsr native_real_emit_function_arg_byte_reloc
    lda #18
    ldx #'h'
    jsr native_real_emit_function_arg_byte_reloc
    lda #26
    ldx #$00
    jsr native_real_emit_import_reloc
    lda #29
    ldx #'l'
    jsr native_real_emit_function_second_arg_byte_reloc
    lda #33
    ldx #'h'
    jsr native_real_emit_function_second_arg_byte_reloc
    lda #41
    ldx #$00
    jsr native_real_emit_import_reloc
    lda #44
    ldx #'l'
    jsr native_real_emit_function_arg_byte_reloc
    lda #47
    ldx #'h'
    jsr native_real_emit_function_arg_byte_reloc
    lda #50
    ldx #'l'
    jsr native_real_emit_function_second_arg_byte_reloc
    lda #53
    ldx #'h'
    jsr native_real_emit_function_second_arg_byte_reloc
    lda #56
    ldx #$00
    jsr native_real_emit_export_reloc
    lda native_real_function_target_selector
    jsr native_real_set_function_var_name
    lda #67
    jsr native_real_emit_named_reloc
    lda native_real_function_second_param_selector
    jsr native_real_set_function_var_name
    lda #104
    jsr native_real_emit_named_reloc
    lda native_real_function_source_selector
    jsr native_real_set_function_var_name
    lda #120
    jsr native_real_emit_named_reloc
    lda #131
    ldx #'l'
    jsr native_real_emit_function_source_byte_reloc
    lda #133
    ldx #'h'
    jsr native_real_emit_function_source_byte_reloc
    jsr native_real_function_pointer_offset
    jsr native_real_emit_data_reloc
    clc
    rts

native_real_emit_function_zeros:
    lda native_real_function_data_size
    clc
    adc #$02
    sta native_real_const_len
native_real_emit_function_zero_loop:
    jsr native_real_emit_zero
    dec native_real_const_len
    bne native_real_emit_function_zero_loop
    jmp emit_newline

native_real_emit_to_int_machine_code:
    lda #<native_real_set_zp2
    ldy #>native_real_set_zp2
    ldx #(native_real_set_zp2_end-native_real_set_zp2)
    jsr native_real_emit_const_bytes
    jsr native_real_emit_a9
    lda native_real_value_lo
    jsr native_real_emit_byte
    jsr native_real_emit_a2
    lda native_real_value_hi
    jsr native_real_emit_byte
    jsr native_real_emit_jsr_placeholder
    lda #<native_real_set_zp2
    ldy #>native_real_set_zp2
    ldx #(native_real_set_zp2_end-native_real_set_zp2)
    jsr native_real_emit_const_bytes
    jsr native_real_emit_jsr_placeholder
    lda #$8D
    jsr native_real_emit_byte
    jsr native_real_emit_zero
    jsr native_real_emit_zero
    lda #$8E
    jsr native_real_emit_byte
    jsr native_real_emit_zero
    jsr native_real_emit_zero
    lda #<native_real_exit
    ldy #>native_real_exit
    ldx #(native_real_exit_end-native_real_exit)
    jsr native_real_emit_const_bytes
    lda #$08
    sta native_real_const_len
:   lda #$00
    jsr native_real_emit_byte
    dec native_real_const_len
    bne :-
    jsr emit_newline
    lda #$03
    jsr native_real_emit_pointer_reloc
    lda #$09
    jsr native_real_emit_pointer_reloc
    lda #18
    ldx #$00
    jsr native_real_emit_import_reloc
    lda #23
    jsr native_real_emit_pointer_reloc
    lda #29
    jsr native_real_emit_pointer_reloc
    lda #34
    ldx #$01
    jsr native_real_emit_import_reloc
    lda #37
    jsr native_real_emit_result_reloc
    lda #40
    jsr native_real_emit_result_hi_reloc
    lda #NATIVE_REAL_TO_INT_POINTER_OFFSET
    jsr native_real_emit_data_reloc
    clc
    rts

native_real_emit_binary_machine_code:
    lda #$00
    ldx #$02
    jsr native_real_emit_pointer_setup
    jsr native_real_emit_a9
    lda native_real_value_lo
    jsr native_real_emit_byte
    jsr native_real_emit_a2
    lda native_real_value_hi
    jsr native_real_emit_byte
    jsr native_real_emit_jsr_placeholder
    lda #$02
    ldx #$02
    jsr native_real_emit_pointer_setup
    jsr native_real_emit_a9
    lda native_real_rhs_value_lo
    jsr native_real_emit_byte
    jsr native_real_emit_a2
    lda native_real_rhs_value_hi
    jsr native_real_emit_byte
    jsr native_real_emit_jsr_placeholder
    lda #$00
    ldx #$02
    jsr native_real_emit_pointer_setup
    lda #$02
    ldx #$04
    jsr native_real_emit_pointer_setup
    lda #$04
    ldx #$06
    jsr native_real_emit_pointer_setup
    jsr native_real_emit_jsr_placeholder
    lda #$04
    ldx #$02
    jsr native_real_emit_pointer_setup
    jsr native_real_emit_jsr_placeholder
    lda #<native_real_exit
    ldy #>native_real_exit
    ldx #(native_real_exit_end-native_real_exit)
    jsr native_real_emit_const_bytes
    lda #18
    sta native_real_const_len
:   lda #$00
    jsr native_real_emit_byte
    dec native_real_const_len
    bne :-
    jsr emit_newline
    lda #$03
    jsr native_real_emit_pointer_reloc
    lda #$09
    jsr native_real_emit_pointer_reloc
    lda #18
    ldx #$00
    jsr native_real_emit_import_reloc
    lda #23
    jsr native_real_emit_pointer_reloc
    lda #29
    jsr native_real_emit_pointer_reloc
    lda #38
    ldx #$00
    jsr native_real_emit_import_reloc
    lda #43
    jsr native_real_emit_pointer_reloc
    lda #49
    jsr native_real_emit_pointer_reloc
    lda #56
    jsr native_real_emit_pointer_reloc
    lda #62
    jsr native_real_emit_pointer_reloc
    lda #69
    jsr native_real_emit_pointer_reloc
    lda #75
    jsr native_real_emit_pointer_reloc
    lda #80
    ldx #$01
    jsr native_real_emit_import_reloc
    lda #85
    jsr native_real_emit_pointer_reloc
    lda #91
    jsr native_real_emit_pointer_reloc
    lda #96
    ldx #$02
    jsr native_real_emit_import_reloc
    lda #NATIVE_REAL_BINARY_POINTER_OFFSET
    jsr native_real_emit_a_reloc
    lda #(NATIVE_REAL_BINARY_POINTER_OFFSET + 2)
    jsr native_real_emit_b_reloc
    lda #(NATIVE_REAL_BINARY_POINTER_OFFSET + 4)
    jsr native_real_emit_x_reloc
    clc
    rts

native_real_emit_unary_machine_code:
    lda #$00
    ldx #$02
    jsr native_real_emit_pointer_setup
    jsr native_real_emit_a9
    lda native_real_value_lo
    jsr native_real_emit_byte
    jsr native_real_emit_a2
    lda native_real_value_hi
    jsr native_real_emit_byte
    jsr native_real_emit_jsr_placeholder
    lda #$00
    ldx #$02
    jsr native_real_emit_pointer_setup
    lda #$02
    ldx #$06
    jsr native_real_emit_pointer_setup
    jsr native_real_emit_jsr_placeholder
    lda #$02
    ldx #$02
    jsr native_real_emit_pointer_setup
    jsr native_real_emit_jsr_placeholder
    lda #<native_real_exit
    ldy #>native_real_exit
    ldx #(native_real_exit_end-native_real_exit)
    jsr native_real_emit_const_bytes
    lda #12
    sta native_real_const_len
:   lda #$00
    jsr native_real_emit_byte
    dec native_real_const_len
    bne :-
    jsr emit_newline
    lda #$03
    jsr native_real_emit_pointer_reloc
    lda #$09
    jsr native_real_emit_pointer_reloc
    lda #18
    ldx #$00
    jsr native_real_emit_import_reloc
    lda #23
    jsr native_real_emit_pointer_reloc
    lda #29
    jsr native_real_emit_pointer_reloc
    lda #36
    jsr native_real_emit_pointer_reloc
    lda #42
    jsr native_real_emit_pointer_reloc
    lda #47
    ldx #$01
    jsr native_real_emit_import_reloc
    lda #52
    jsr native_real_emit_pointer_reloc
    lda #58
    jsr native_real_emit_pointer_reloc
    lda #63
    ldx #$02
    jsr native_real_emit_import_reloc
    lda #NATIVE_REAL_UNARY_POINTER_OFFSET
    jsr native_real_emit_a_reloc
    lda #(NATIVE_REAL_UNARY_POINTER_OFFSET + 2)
    jsr native_real_emit_x_reloc
    clc
    rts

native_real_emit_input_machine_code:
    jsr native_real_emit_input_arg_setup
    jsr native_real_emit_jsr_placeholder
    lda native_real_active
    cmp #NATIVE_REAL_MODE_INPUT_STORED
    bne native_real_emit_input_machine_no_store
    lda #$8D
    jsr native_real_emit_byte
    jsr native_real_emit_zero
    jsr native_real_emit_zero
    jsr native_real_emit_a9
    jsr native_real_emit_zero
    lda #$8D
    jsr native_real_emit_byte
    jsr native_real_emit_zero
    jsr native_real_emit_zero
native_real_emit_input_machine_no_store:
    lda #$00
    ldx #$02
    jsr native_real_emit_pointer_setup
    jsr native_real_emit_a9
    lda native_real_value_lo
    jsr native_real_emit_byte
    jsr native_real_emit_a2
    lda native_real_value_hi
    jsr native_real_emit_byte
    jsr native_real_emit_jsr_placeholder
    lda #$00
    ldx #$02
    jsr native_real_emit_pointer_setup
    jsr native_real_emit_jsr_placeholder
    lda #<native_real_exit
    ldy #>native_real_exit
    ldx #(native_real_exit_end-native_real_exit)
    jsr native_real_emit_const_bytes
    lda native_real_active
    cmp #NATIVE_REAL_MODE_INPUT_STORED
    beq native_real_emit_input_machine_stored_zeros
    lda #$06
    bne native_real_emit_input_machine_zeros_ready
native_real_emit_input_machine_stored_zeros:
    lda #$08
native_real_emit_input_machine_zeros_ready:
    sta native_real_const_len
native_real_emit_input_machine_zero_loop:
    jsr native_real_emit_zero
    dec native_real_const_len
    bne native_real_emit_input_machine_zero_loop
    jsr emit_newline
    lda native_real_active
    cmp #NATIVE_REAL_MODE_INPUT_STORED
    beq native_real_emit_input_machine_stored_relocs
    lda #$06
    ldx #$00
    jsr native_real_emit_import_reloc
    lda #11
    jsr native_real_emit_pointer_reloc
    lda #17
    jsr native_real_emit_pointer_reloc
    lda #26
    ldx #$01
    jsr native_real_emit_import_reloc
    lda #31
    jsr native_real_emit_pointer_reloc
    lda #37
    jsr native_real_emit_pointer_reloc
    lda #42
    ldx #$02
    jsr native_real_emit_import_reloc
    lda #NATIVE_REAL_INPUT_POINTER_OFFSET
    jsr native_real_emit_data_reloc
    clc
    rts
native_real_emit_input_machine_stored_relocs:
    lda #$06
    ldx #$00
    jsr native_real_emit_import_reloc
    lda #$09
    jsr native_real_emit_result_reloc
    lda #14
    jsr native_real_emit_result_hi_reloc
    lda #19
    jsr native_real_emit_pointer_reloc
    lda #25
    jsr native_real_emit_pointer_reloc
    lda #34
    ldx #$01
    jsr native_real_emit_import_reloc
    lda #39
    jsr native_real_emit_pointer_reloc
    lda #45
    jsr native_real_emit_pointer_reloc
    lda #50
    ldx #$02
    jsr native_real_emit_import_reloc
    lda #NATIVE_REAL_INPUT_STORED_POINTER_OFFSET
    jsr native_real_emit_a_reloc
    clc
    rts

native_real_emit_input_arg_setup:
    ; A receives the byte ABI value while X/Y receive the same value as a word.
    jsr native_real_emit_a9
    lda native_real_input_value_lo
    jsr native_real_emit_byte
    lda #$AA
    jsr native_real_emit_byte
    lda #$A0
    jsr native_real_emit_byte
    lda native_real_input_value_hi
    jmp native_real_emit_byte

native_real_emit_pointer_setup:
    sta native_real_pointer_index
    stx native_real_pointer_zp
    jsr native_real_emit_a2
    lda native_real_pointer_index
    jsr native_real_emit_byte
    lda #$BD
    jsr native_real_emit_byte
    jsr native_real_emit_zero
    jsr native_real_emit_zero
    lda #$85
    jsr native_real_emit_byte
    lda native_real_pointer_zp
    jsr native_real_emit_byte
    lda #$E8
    jsr native_real_emit_byte
    lda #$BD
    jsr native_real_emit_byte
    jsr native_real_emit_zero
    jsr native_real_emit_zero
    lda #$85
    jsr native_real_emit_byte
    lda native_real_pointer_zp
    clc
    adc #$01
    jmp native_real_emit_byte

native_real_emit_jsr_placeholder:
    lda #$20
    jsr native_real_emit_byte
    jsr native_real_emit_zero
    lda #$00
    jmp native_real_emit_byte

native_real_emit_const_bytes:
    sta native_real_const_ptr
    sty native_real_const_ptr+1
    stx native_real_const_len
    ldy #$00
:   cpy native_real_const_len
    beq :+
    lda native_real_const_ptr
    sta ACTC_OVERLAY_WORK_ZP
    lda native_real_const_ptr+1
    sta ACTC_OVERLAY_WORK_ZP+1
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr native_real_emit_byte
    iny
    bne :-
:   rts

native_real_emit_a2:
    lda #$A2
    jmp native_real_emit_byte

native_real_emit_a9:
    lda #$A9
    jmp native_real_emit_byte

native_real_emit_zero:
    lda #$00
    jmp native_real_emit_byte

native_real_emit_byte:
    sta native_real_byte
    lda #' '
    jsr emit_char_overlay
    lda native_real_byte
    jmp emit_hex_byte_overlay

native_real_emit_pointer_reloc:
    pha
    jsr native_real_set_scan_name_pointer
    pla
    bne native_real_emit_named_reloc
native_real_emit_data_reloc:
    pha
    jsr native_real_set_scan_name_data
    pla
    bne native_real_emit_named_reloc
native_real_emit_result_reloc:
    pha
    jsr native_real_set_scan_name_result
    pla
    bne native_real_emit_named_reloc
native_real_emit_result_hi_reloc:
    pha
    jsr native_real_set_scan_name_result_hi
    pla
    bne native_real_emit_named_reloc
native_real_emit_a_reloc:
    pha
    jsr native_real_set_scan_name_a
    pla
    bne native_real_emit_named_reloc
native_real_emit_b_reloc:
    pha
    jsr native_real_set_scan_name_b
    pla
    bne native_real_emit_named_reloc
native_real_emit_x_reloc:
    pha
    jsr native_real_set_scan_name_x
    pla
native_real_emit_named_reloc:
    jsr native_real_emit_reloc_prefix
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr emit_scan_zp_string
    jmp emit_newline

native_real_emit_function_source_byte_reloc:
    sta native_real_byte
    stx native_real_import_index
    lda native_real_function_source_selector
    jmp native_real_emit_function_byte_reloc
native_real_emit_function_arg_byte_reloc:
    sta native_real_byte
    stx native_real_import_index
    lda native_real_function_arg_selector
    bne native_real_emit_function_byte_reloc
native_real_emit_function_second_arg_byte_reloc:
    sta native_real_byte
    stx native_real_import_index
    lda native_real_function_second_arg_selector
native_real_emit_function_byte_reloc:
    jsr native_real_set_function_var_name
    lda native_real_byte
    jsr native_real_emit_reloc_prefix
    lda native_real_import_index
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr emit_scan_zp_string
    jmp emit_newline

native_real_emit_export_reloc:
    sta native_real_byte
    stx native_real_import_index
    jsr native_real_emit_reloc_prefix
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    ldx native_real_import_index
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr emit_lower_scan_zp_string
    jmp emit_newline

native_real_emit_import_reloc:
    stx native_real_import_index
    jsr native_real_emit_reloc_prefix
    lda #'u'
    jsr emit_char_overlay
    lda native_real_import_index
    jsr emit_object_selector_overlay
    jmp emit_newline

native_real_emit_reloc_prefix:
    sta native_real_byte
    lda #'r'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda native_real_byte
    jsr emit_small_decimal
    lda #' '
    jmp emit_char_overlay

native_real_set_zp2:
    .byte $A2,$00,$BD,$00,$00,$85,$02,$E8,$BD,$00,$00,$85,$03
native_real_set_zp2_end:
native_real_function_set_zp6:
    .byte $A2,$00,$BD,$00,$00,$85,$06,$E8,$BD,$00,$00,$85,$07
native_real_function_set_zp6_pointer_end:
    .byte $A9,$00,$85,$02,$A9,$00,$85,$03,$A9
native_real_function_set_zp6_end:
native_real_param_argument_setup:
    .byte $A2,$00,$A9,$00,$9D,$00,$00,$E8,$A9,$00,$9D,$00,$00
    .byte $CA,$BD,$00,$00,$48,$E8,$BD,$00,$00,$48
native_real_param_argument_setup_end:
native_real_real_param_argument_setup:
    .byte $A9,$00,$48,$A9,$00,$48
native_real_real_param_argument_setup_end:
native_real_two_param_next_destination:
    .byte $A9,$00,$85,$02,$A9,$00,$85,$03,$A9
native_real_two_param_next_destination_end:
native_real_function_call_copy:
    .byte $20,$00,$00,$85,$04,$86,$05,$A0,$03,$B1,$04,$99,$00,$00,$88,$10,$F8
native_real_function_call_copy_end:
native_real_function_return_pointer:
    .byte $A9,$00,$A2,$00,$60
native_real_function_return_pointer_end:
native_real_param_store_entry:
    .byte $68,$AA,$68,$85,$04,$68,$A0
native_real_param_store_entry_end:
native_real_param_store_middle:
    .byte $91,$06,$68,$88,$91,$06,$A5,$04,$48,$8A,$48
    .byte $A9,$00,$85,$02,$A9,$00,$85,$03,$A0
native_real_param_store_middle_end:
native_real_param_convert_return:
    .byte $B1,$06,$48,$C8,$B1,$06,$AA,$68,$20,$00,$00,$A9,$00,$A2,$00,$60
native_real_param_convert_return_end:
native_real_real_param_store_return:
    .byte $68,$AA,$68,$85,$04,$68,$85,$03,$68,$85,$02,$A5,$04,$48,$8A,$48
    .byte $A0,$03,$B1,$02,$99,$00,$00,$88,$10,$F8,$A9,$00,$A2,$00,$60
native_real_real_param_store_return_end:
native_real_two_param_store_return:
    .byte $68,$AA,$68,$85,$04,$68,$85,$03,$68,$85,$02
    .byte $A0,$03,$B1,$02,$99,$00,$00,$88,$10,$F8
    .byte $68,$85,$03,$68,$85,$02
    .byte $A0,$03,$B1,$02,$99,$00,$00,$88,$10,$F8
    .byte $A5,$04,$48,$8A,$48,$A9,$00,$A2,$00,$60
native_real_two_param_store_return_end:
native_real_exit:
    .byte $A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF
native_real_exit_end:
native_real_body_pattern:
    .asciiz "p1u0T0S0L0U0p2u1r"
native_real_bits_body_pattern:
    .asciiz "p0p1T0S0L0U0p2u0r"
native_real_to_int_body_pattern:
    .asciiz "p1u0T0S0L0U0u1S1r"
native_real_binary_body_pattern:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1T2S2L2U2p4u2r"
native_real_unary_signed_body_pattern:
    .asciiz "p0u0T0S0L0U0u1T1S1L1U1p1u2r"
native_real_unary_positive_body_pattern:
    .asciiz "p1u0T0S0L0U0u1T1S1L1U1p2u2r"
native_real_input_body_pattern:
    .asciiz "p0u0p2u1T0S0L0U0p3u2r"
native_real_input_stored_body_pattern:
    .asciiz "p0u0S0p2u1T1S1L1U1p3u2r"
native_real_function_return_body_pattern:
    .byte 'L',NATIVE_REAL_PATTERN_CAPTURE_SOURCE,'U',NATIVE_REAL_PATTERN_MATCH_SOURCE,'r',$00
native_real_function_main_body_pattern:
    .byte 'p','1','u','0','T',NATIVE_REAL_PATTERN_MATCH_SOURCE
    .byte 'S',NATIVE_REAL_PATTERN_MATCH_SOURCE,'C','0'
    .byte 'T',NATIVE_REAL_PATTERN_CAPTURE_TARGET,'S',NATIVE_REAL_PATTERN_MATCH_TARGET,'r',$00
native_real_param_function_return_body_pattern:
    .byte 'S',NATIVE_REAL_PATTERN_CAPTURE_PARAM,'L',NATIVE_REAL_PATTERN_MATCH_PARAM
    .byte 'u','0','T',NATIVE_REAL_PATTERN_CAPTURE_SOURCE,'S',NATIVE_REAL_PATTERN_MATCH_SOURCE
    .byte 'L',NATIVE_REAL_PATTERN_MATCH_SOURCE,'U',NATIVE_REAL_PATTERN_MATCH_SOURCE,'r',$00
native_real_param_function_main_body_pattern:
    .byte 'p','0','C','0','T',NATIVE_REAL_PATTERN_CAPTURE_TARGET
    .byte 'S',NATIVE_REAL_PATTERN_MATCH_TARGET,'r',$00
native_real_param_function_variable_main_body_pattern:
    .byte 'p','0','S',NATIVE_REAL_PATTERN_CAPTURE_SOURCE
    .byte 'L',NATIVE_REAL_PATTERN_MATCH_SOURCE,'C','0'
    .byte 'T',NATIVE_REAL_PATTERN_CAPTURE_TARGET,'S',NATIVE_REAL_PATTERN_MATCH_TARGET,'r',$00
native_real_real_param_function_return_body_pattern:
    .byte 'S',NATIVE_REAL_PATTERN_CAPTURE_PARAM
    .byte 'L',NATIVE_REAL_PATTERN_MATCH_PARAM,'U',NATIVE_REAL_PATTERN_MATCH_PARAM,'r',$00
native_real_real_param_function_main_body_pattern:
    .byte 'p','1','u','0','T',NATIVE_REAL_PATTERN_CAPTURE_SOURCE
    .byte 'S',NATIVE_REAL_PATTERN_MATCH_SOURCE,'L',NATIVE_REAL_PATTERN_MATCH_SOURCE
    .byte 'U',NATIVE_REAL_PATTERN_MATCH_SOURCE,'C','0'
    .byte 'T',NATIVE_REAL_PATTERN_CAPTURE_TARGET,'S',NATIVE_REAL_PATTERN_MATCH_TARGET,'r',$00
native_real_two_param_function_return_body_pattern:
    .byte 'S',NATIVE_REAL_PATTERN_CAPTURE_SECOND_PARAM
    .byte 'S',NATIVE_REAL_PATTERN_CAPTURE_PARAM
    .byte 'L',NATIVE_REAL_PATTERN_MATCH_PARAM,'U',NATIVE_REAL_PATTERN_MATCH_PARAM,'r',$00
native_real_two_param_function_main_body_pattern:
    .byte 'p','1','u','0','T',NATIVE_REAL_PATTERN_CAPTURE_SOURCE
    .byte 'S',NATIVE_REAL_PATTERN_MATCH_SOURCE
    .byte 'p','3','u','0','T',NATIVE_REAL_PATTERN_CAPTURE_SECOND_ARG
    .byte 'S',NATIVE_REAL_PATTERN_MATCH_SECOND_ARG
    .byte 'L',NATIVE_REAL_PATTERN_MATCH_SOURCE,'U',NATIVE_REAL_PATTERN_MATCH_SOURCE
    .byte 'L',NATIVE_REAL_PATTERN_MATCH_SECOND_ARG,'U',NATIVE_REAL_PATTERN_MATCH_SECOND_ARG
    .byte 'C','0','T',NATIVE_REAL_PATTERN_CAPTURE_TARGET
    .byte 'S',NATIVE_REAL_PATTERN_MATCH_TARGET,'r',$00
native_real_function_root_body_marker:
    .asciiz "b u0M"
native_real_name_data:
    .asciiz "__idata"
native_real_name_var:
    .asciiz "__v0"
native_real_name_a:
    .asciiz "__ireala"
native_real_name_b:
    .asciiz "__irealb"
native_real_name_x:
    .asciiz "__irealx"
native_real_name_result:
    .asciiz "__iresult"
native_real_name_result_hi:
    .asciiz "__iresulthi"
native_real_name_pointer:
    .asciiz "__iptr"
native_real_debug_offsets:
    .byte 0,17,20,20,20,33,33,33,36
native_real_bits_debug_offsets:
    .byte 0,0,0,0,0,0,14,14,16
native_real_to_int_debug_offsets:
    .byte 0,17,20,20,20,33,33,36,42
native_real_binary_debug_offsets:
    .byte 0,17,20,20,20,37,40,40,40,53,53,66,79,82,82,82,95,95,95,98
native_real_unary_debug_offsets:
    .byte 0,17,20,20,20,33,46,49,49,49,62,62,62,65
native_real_input_debug_offsets:
    .byte 0,5,8,25,28,28,28,28,41,41,44
native_real_input_stored_debug_offsets:
    .byte 0,5,8,16,33,36,36,36,36,49,49,52
native_real_function_return_debug_offsets:
    .byte 61,63,65
native_real_function_main_debug_offsets:
    .byte 21,25,13,25,28,39,39,45
native_real_param_function_return_debug_offsets:
    .byte 69,96,106,109,109,109,111,113
native_real_param_function_main_debug_offsets:
    .byte 15,36,39,39,53
native_real_param_function_variable_main_debug_offsets:
    .byte 15,17,27,36,39,39,53
native_real_real_param_function_return_debug_offsets:
    .byte 67,93,95,97
native_real_real_param_function_main_debug_offsets:
    .byte 21,25,13,25,28,31,34,45,45,51
native_real_two_param_function_return_debug_offsets:
    .byte 88,109,130,132,134
native_real_two_param_function_main_debug_offsets:
    .byte 21,25,13,25,36,40,28,40,43,46,49,52,55,66,66,72

native_real_active:
    .byte $00
native_real_value_lo:
    .byte $00
native_real_value_hi:
    .byte $00
native_real_second_value_lo:
    .byte $00
native_real_second_value_hi:
    .byte $00
native_real_rhs_value_lo:
    .byte $00
native_real_rhs_value_hi:
    .byte $00
native_real_input_value_lo:
    .byte $00
native_real_input_value_hi:
    .byte $00
native_real_function_var_width_storage:
    .byte $00
native_real_literal_index:
    .byte $00
native_real_byte:
    .byte $00
native_real_import_index:
    .byte $00
native_real_const_ptr:
    .word $0000
native_real_external_ptr:
    .word $0000
native_real_const_len:
    .byte $00
native_real_table_offset:
    .byte $00
native_real_pointer_index:
    .byte $00
native_real_pointer_zp:
    .byte $00
native_real_function_param_count:
    .byte $00
native_real_function_param_index:
    .byte $00
native_real_function_param_offset:
    .byte $00
native_real_function_second_param_selector:
    .byte $00
native_real_function_second_arg_selector:
    .byte $00

native_real_function_var_count = native_real_pointer_index
native_real_function_source_selector = native_real_pointer_zp
native_real_function_target_selector = native_real_rhs_value_lo
native_real_function_var_index = native_real_rhs_value_hi
native_real_function_data_size = native_real_input_value_lo
native_real_function_var_width = native_real_function_var_width_storage
native_real_function_var_offset = native_real_table_offset
native_real_function_param_selector = native_real_import_index
native_real_function_arg_selector = native_real_function_param_index
native_real_function_module_var_count = native_real_external_ptr
native_real_function_proc_meta = native_real_byte
