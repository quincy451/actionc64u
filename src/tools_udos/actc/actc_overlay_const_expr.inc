; Bounded shunting-yard evaluator for the Idun-compatible integer CONST
; grammar. Values are signed 64-bit little-endian integers while expressions
; are evaluated; the declaration type applies the final C64 range check.

PREPROCESS_CONST_VALUE_WIDTH = 8
PREPROCESS_CONST_VALUE_STACK_MAX = 32
PREPROCESS_CONST_OPERATOR_STACK_MAX = 32

PREPROCESS_CONST_OP_MARK = 0
PREPROCESS_CONST_OP_XOR = 1
PREPROCESS_CONST_OP_OR = 2
PREPROCESS_CONST_OP_AND = 3
PREPROCESS_CONST_OP_ADD = 4
PREPROCESS_CONST_OP_SUB = 5
PREPROCESS_CONST_OP_MUL = 6
PREPROCESS_CONST_OP_DIV = 7
PREPROCESS_CONST_OP_MOD = 8
PREPROCESS_CONST_OP_LSH = 9
PREPROCESS_CONST_OP_RSH = 10
PREPROCESS_CONST_OP_NEG = 11

preprocess_const_eval_integer:
    cld
    lda #$00
    sta preprocess_const_expr_scan
    sta preprocess_const_value_count
    sta preprocess_const_operator_count
    lda #$01
    sta preprocess_const_expect_operand
preprocess_const_eval_token_loop:
    jsr preprocess_const_skip_expr_spaces
    ldy preprocess_const_expr_scan
    lda preprocess_value_temp,y
    bne :+
    jmp preprocess_const_eval_finish
:
    lda preprocess_const_expect_operand
    beq preprocess_const_eval_operator

    ldy preprocess_const_expr_scan
    lda preprocess_value_temp,y
    cmp #'+'
    beq preprocess_const_eval_unary_plus
    cmp #'-'
    beq preprocess_const_eval_unary_minus
    cmp #'('
    beq preprocess_const_eval_open
    jsr preprocess_const_parse_atom
    bcc :+
    jmp preprocess_const_eval_fail
:
    jsr preprocess_const_push_value
    bcc :+
    jmp preprocess_const_eval_fail
:
    lda #$00
    sta preprocess_const_expect_operand
    jmp preprocess_const_eval_token_loop

preprocess_const_eval_unary_plus:
    inc preprocess_const_expr_scan
    jmp preprocess_const_eval_token_loop
preprocess_const_eval_unary_minus:
    inc preprocess_const_expr_scan
    lda #PREPROCESS_CONST_OP_NEG
    jsr preprocess_const_push_operator
    bcs preprocess_const_eval_fail
    jmp preprocess_const_eval_token_loop
preprocess_const_eval_open:
    inc preprocess_const_expr_scan
    lda #PREPROCESS_CONST_OP_MARK
    jsr preprocess_const_push_operator
    bcs preprocess_const_eval_fail
    jmp preprocess_const_eval_token_loop

preprocess_const_eval_operator:
    ldy preprocess_const_expr_scan
    lda preprocess_value_temp,y
    cmp #')'
    beq preprocess_const_eval_close
    jsr preprocess_const_parse_binary_operator
    bcs preprocess_const_eval_fail
    jsr preprocess_const_queue_binary_operator
    bcs preprocess_const_eval_fail
    lda #$01
    sta preprocess_const_expect_operand
    jmp preprocess_const_eval_token_loop

preprocess_const_eval_close:
    inc preprocess_const_expr_scan
preprocess_const_eval_close_loop:
    lda preprocess_const_operator_count
    beq preprocess_const_eval_fail
    tax
    dex
    lda preprocess_const_operator_stack,x
    beq preprocess_const_eval_close_mark
    jsr preprocess_const_apply_top_operator
    bcs preprocess_const_eval_fail
    jmp preprocess_const_eval_close_loop
preprocess_const_eval_close_mark:
    dec preprocess_const_operator_count
    jmp preprocess_const_eval_token_loop

preprocess_const_eval_finish:
    lda preprocess_const_expect_operand
    bne preprocess_const_eval_fail
preprocess_const_eval_finish_loop:
    lda preprocess_const_operator_count
    beq preprocess_const_eval_have_value
    jsr preprocess_const_apply_top_operator
    bcs preprocess_const_eval_fail
    jmp preprocess_const_eval_finish_loop
preprocess_const_eval_have_value:
    lda preprocess_const_value_count
    cmp #$01
    bne preprocess_const_eval_fail
    jsr preprocess_const_pop_value
    bcs preprocess_const_eval_fail
    jsr preprocess_const_check_decl_range
    bcs preprocess_const_eval_fail
    jsr preprocess_const_format_integer
    clc
    rts
preprocess_const_eval_fail:
    sec
    rts

preprocess_const_parse_atom:
    ldy preprocess_const_expr_scan
    lda preprocess_value_temp,y
    cmp #$27
    beq preprocess_const_parse_character
    cmp #'$'
    bne :+
    jmp preprocess_const_parse_number
:
    cmp #'%'
    bne :+
    jmp preprocess_const_parse_number
:
    cmp #'0'
    bcc preprocess_const_parse_identifier
    cmp #('9'+1)
    bcs preprocess_const_parse_identifier
    jmp preprocess_const_parse_number
preprocess_const_parse_identifier:
    jsr uppercase_ascii
    cmp #'_'
    beq preprocess_const_parse_identifier_start
    jsr uppercase_symbol_start_valid
    bcs preprocess_const_parse_atom_fail
preprocess_const_parse_identifier_start:
    ldx #$00
preprocess_const_parse_identifier_loop:
    ldy preprocess_const_expr_scan
    lda preprocess_value_temp,y
    jsr uppercase_ascii
    jsr uppercase_symbol_body_valid
    bcs preprocess_const_parse_identifier_done
    cpx #(PREPROCESS_DEFINE_NAME_SIZE - 1)
    bcs preprocess_const_parse_atom_fail
    sta preprocess_name_temp,x
    inx
    inc preprocess_const_expr_scan
    jmp preprocess_const_parse_identifier_loop
preprocess_const_parse_identifier_done:
    lda #$00
    sta preprocess_name_temp,x
    jsr preprocess_const_lookup_builtin
    bcs preprocess_const_parse_atom_fail
    sta preprocess_const_builtin_value
    jsr preprocess_const_zero_value
    lda preprocess_const_builtin_value
    sta preprocess_const_value_lo
    clc
    rts

preprocess_const_parse_character:
    inc preprocess_const_expr_scan
    ldy preprocess_const_expr_scan
    lda preprocess_value_temp,y
    beq preprocess_const_parse_atom_fail
    cmp #$5C
    bne preprocess_const_parse_character_value
    inc preprocess_const_expr_scan
    ldy preprocess_const_expr_scan
    lda preprocess_value_temp,y
    beq preprocess_const_parse_atom_fail
    cmp #'n'
    bne :+
    lda #10
    bne preprocess_const_parse_character_value
:
    cmp #'r'
    bne preprocess_const_parse_character_value
    lda #13
preprocess_const_parse_character_value:
    sta preprocess_const_digit
    inc preprocess_const_expr_scan
    ldy preprocess_const_expr_scan
    lda preprocess_value_temp,y
    cmp #$27
    bne :+
    inc preprocess_const_expr_scan
:
    jsr preprocess_const_zero_value
    lda preprocess_const_digit
    sta preprocess_const_value_lo
    clc
    rts
preprocess_const_parse_atom_fail:
    sec
    rts

preprocess_const_parse_number:
    jsr preprocess_const_zero_value
    lda #$00
    sta preprocess_const_digit_seen
    lda #10
    sta preprocess_const_base
    ldy preprocess_const_expr_scan
    lda preprocess_value_temp,y
    cmp #'$'
    bne preprocess_const_parse_number_binary
    lda #16
    sta preprocess_const_base
    inc preprocess_const_expr_scan
    jmp preprocess_const_parse_number_loop
preprocess_const_parse_number_binary:
    cmp #'%'
    bne preprocess_const_parse_number_c_hex
    lda #2
    sta preprocess_const_base
    inc preprocess_const_expr_scan
    jmp preprocess_const_parse_number_loop
preprocess_const_parse_number_c_hex:
    cmp #'0'
    bne preprocess_const_parse_number_loop
    iny
    lda preprocess_value_temp,y
    jsr uppercase_ascii
    cmp #'X'
    bne preprocess_const_parse_number_loop
    lda #16
    sta preprocess_const_base
    inc preprocess_const_expr_scan
    inc preprocess_const_expr_scan
preprocess_const_parse_number_loop:
    ldy preprocess_const_expr_scan
    lda preprocess_value_temp,y
    jsr preprocess_const_digit_value
    bcs preprocess_const_parse_number_done
    cmp preprocess_const_base
    bcs preprocess_const_parse_number_done
    sta preprocess_const_digit
    lda #$01
    sta preprocess_const_digit_seen
    jsr preprocess_const_multiply_value_by_base
    bcs preprocess_const_parse_number_fail
    clc
    lda preprocess_const_value_lo
    adc preprocess_const_digit
    sta preprocess_const_value_lo
    .repeat 7, I
        lda preprocess_const_value_lo + 1 + I
        adc #$00
        sta preprocess_const_value_lo + 1 + I
    .endrepeat
    bcs preprocess_const_parse_number_fail
    lda preprocess_const_value_lo+7
    bmi preprocess_const_parse_number_fail
    inc preprocess_const_expr_scan
    jmp preprocess_const_parse_number_loop
preprocess_const_parse_number_done:
    lda preprocess_const_digit_seen
    beq preprocess_const_parse_number_fail
    clc
    rts
preprocess_const_parse_number_fail:
    sec
    rts

preprocess_const_multiply_value_by_base:
    ldx #$00
preprocess_const_copy_value_to_lhs_loop:
    lda preprocess_const_value_lo,x
    sta preprocess_const_lhs_lo,x
    inx
    cpx #PREPROCESS_CONST_VALUE_WIDTH
    bcc preprocess_const_copy_value_to_lhs_loop
    jsr preprocess_const_zero_value
    ldx preprocess_const_base
preprocess_const_multiply_value_by_base_loop:
    jsr preprocess_const_add_lhs_unsigned
    bcs preprocess_const_multiply_value_by_base_fail
    dex
    bne preprocess_const_multiply_value_by_base_loop
    lda preprocess_const_value_lo+7
    bmi preprocess_const_multiply_value_by_base_fail
    clc
    rts
preprocess_const_multiply_value_by_base_fail:
    sec
    rts

preprocess_const_digit_value:
    cmp #'0'
    bcc preprocess_const_digit_fail
    cmp #('9'+1)
    bcc preprocess_const_digit_decimal
    jsr uppercase_ascii
    cmp #'A'
    bcc preprocess_const_digit_fail
    cmp #('F'+1)
    bcs preprocess_const_digit_fail
    sec
    sbc #('A'-10)
    clc
    rts
preprocess_const_digit_decimal:
    sec
    sbc #'0'
    clc
    rts
preprocess_const_digit_fail:
    sec
    rts

preprocess_const_parse_binary_operator:
    ldy preprocess_const_expr_scan
    lda preprocess_value_temp,y
    cmp #'+'
    bne :+
    inc preprocess_const_expr_scan
    lda #PREPROCESS_CONST_OP_ADD
    clc
    rts
:
    cmp #'-'
    bne :+
    inc preprocess_const_expr_scan
    lda #PREPROCESS_CONST_OP_SUB
    clc
    rts
:
    cmp #'*'
    bne :+
    inc preprocess_const_expr_scan
    lda #PREPROCESS_CONST_OP_MUL
    clc
    rts
:
    cmp #'/'
    bne :+
    inc preprocess_const_expr_scan
    lda #PREPROCESS_CONST_OP_DIV
    clc
    rts
:
    cmp #'&'
    bne :+
    inc preprocess_const_expr_scan
    lda #PREPROCESS_CONST_OP_AND
    clc
    rts
:
    cmp #'%'
    bne :+
    inc preprocess_const_expr_scan
    lda #PREPROCESS_CONST_OP_OR
    clc
    rts
:
    cmp #'!'
    bne preprocess_const_parse_binary_word
    inc preprocess_const_expr_scan
    ldy preprocess_const_expr_scan
    lda preprocess_value_temp,y
    cmp #'='
    beq preprocess_const_parse_binary_fail
    lda #PREPROCESS_CONST_OP_XOR
    clc
    rts
preprocess_const_parse_binary_word:
    lda #<preprocess_const_keyword_mod
    ldy #>preprocess_const_keyword_mod
    jsr preprocess_const_match_expr_word
    bcs :+
    lda #PREPROCESS_CONST_OP_MOD
    clc
    rts
:
    lda #<preprocess_const_keyword_lsh
    ldy #>preprocess_const_keyword_lsh
    jsr preprocess_const_match_expr_word
    bcs :+
    lda #PREPROCESS_CONST_OP_LSH
    clc
    rts
:
    lda #<preprocess_const_keyword_rsh
    ldy #>preprocess_const_keyword_rsh
    jsr preprocess_const_match_expr_word
    bcs :+
    lda #PREPROCESS_CONST_OP_RSH
    clc
    rts
:
    lda #<preprocess_const_keyword_xor
    ldy #>preprocess_const_keyword_xor
    jsr preprocess_const_match_expr_word
    bcs preprocess_const_parse_binary_fail
    lda #PREPROCESS_CONST_OP_XOR
    clc
    rts
preprocess_const_parse_binary_fail:
    sec
    rts

preprocess_const_queue_binary_operator:
    sta preprocess_const_current_operator
preprocess_const_queue_binary_loop:
    lda preprocess_const_operator_count
    beq preprocess_const_queue_binary_push
    tax
    dex
    lda preprocess_const_operator_stack,x
    beq preprocess_const_queue_binary_push
    tax
    lda preprocess_const_operator_precedence,x
    sta preprocess_const_top_precedence
    ldx preprocess_const_current_operator
    lda preprocess_const_operator_precedence,x
    cmp preprocess_const_top_precedence
    bcc preprocess_const_queue_binary_apply
    beq preprocess_const_queue_binary_apply
preprocess_const_queue_binary_push:
    lda preprocess_const_current_operator
    jmp preprocess_const_push_operator
preprocess_const_queue_binary_apply:
    jsr preprocess_const_apply_top_operator
    bcs preprocess_const_queue_binary_fail
    jmp preprocess_const_queue_binary_loop
preprocess_const_queue_binary_fail:
    sec
    rts

preprocess_const_push_operator:
    ldx preprocess_const_operator_count
    cpx #PREPROCESS_CONST_OPERATOR_STACK_MAX
    bcs preprocess_const_push_operator_fail
    sta preprocess_const_operator_stack,x
    inc preprocess_const_operator_count
    clc
    rts
preprocess_const_push_operator_fail:
    sec
    rts

preprocess_const_push_value:
    lda preprocess_const_value_count
    cmp #PREPROCESS_CONST_VALUE_STACK_MAX
    bcs preprocess_const_push_value_fail
    asl
    asl
    asl
    tax
    ldy #$00
preprocess_const_push_value_loop:
    lda preprocess_const_value_lo,y
    sta preprocess_const_value_stack,x
    inx
    iny
    cpy #PREPROCESS_CONST_VALUE_WIDTH
    bcc preprocess_const_push_value_loop
    inc preprocess_const_value_count
    clc
    rts
preprocess_const_push_value_fail:
    sec
    rts

preprocess_const_pop_value:
    lda #<preprocess_const_value_lo
    ldy #>preprocess_const_value_lo
    jmp preprocess_const_pop_to_ptr
preprocess_const_pop_lhs:
    lda #<preprocess_const_lhs_lo
    ldy #>preprocess_const_lhs_lo
    jmp preprocess_const_pop_to_ptr
preprocess_const_pop_rhs:
    lda #<preprocess_const_rhs_lo
    ldy #>preprocess_const_rhs_lo
preprocess_const_pop_to_ptr:
    sta ACTC_OVERLAY_WORK_ZP
    sty ACTC_OVERLAY_WORK_ZP+1
    lda preprocess_const_value_count
    beq preprocess_const_pop_to_ptr_fail
    dec preprocess_const_value_count
    lda preprocess_const_value_count
    asl
    asl
    asl
    tax
    ldy #$00
preprocess_const_pop_to_ptr_loop:
    lda preprocess_const_value_stack,x
    sta (ACTC_OVERLAY_WORK_ZP),y
    inx
    iny
    cpy #PREPROCESS_CONST_VALUE_WIDTH
    bcc preprocess_const_pop_to_ptr_loop
    clc
    rts
preprocess_const_pop_to_ptr_fail:
    sec
    rts

preprocess_const_apply_top_operator:
    lda preprocess_const_operator_count
    beq preprocess_const_apply_fail
    dec preprocess_const_operator_count
    ldx preprocess_const_operator_count
    lda preprocess_const_operator_stack,x
    beq preprocess_const_apply_fail
    cmp #PREPROCESS_CONST_OP_NEG
    beq preprocess_const_apply_negate
    sta preprocess_const_apply_operator
    jsr preprocess_const_pop_rhs
    bcs preprocess_const_apply_fail
    jsr preprocess_const_pop_lhs
    bcs preprocess_const_apply_fail
    lda preprocess_const_apply_operator
    cmp #PREPROCESS_CONST_OP_ADD
    bne :+
    jsr preprocess_const_add
    jmp preprocess_const_apply_result
:
    cmp #PREPROCESS_CONST_OP_SUB
    bne :+
    jsr preprocess_const_subtract
    jmp preprocess_const_apply_result
:
    cmp #PREPROCESS_CONST_OP_MUL
    bne :+
    jsr preprocess_const_multiply
    jmp preprocess_const_apply_result
:
    cmp #PREPROCESS_CONST_OP_DIV
    beq preprocess_const_apply_divmod
    cmp #PREPROCESS_CONST_OP_MOD
    beq preprocess_const_apply_divmod
    cmp #PREPROCESS_CONST_OP_LSH
    bne :+
    jsr preprocess_const_shift_left
    jmp preprocess_const_apply_result
:
    cmp #PREPROCESS_CONST_OP_RSH
    bne :+
    jsr preprocess_const_shift_right
    jmp preprocess_const_apply_result
:
    jsr preprocess_const_bitwise
    jmp preprocess_const_apply_result
preprocess_const_apply_divmod:
    jsr preprocess_const_divmod
preprocess_const_apply_result:
    bcs preprocess_const_apply_fail
    jsr preprocess_const_push_value
    rts
preprocess_const_apply_negate:
    jsr preprocess_const_pop_value
    bcs preprocess_const_apply_fail
    jsr preprocess_const_negate_value
    bcs preprocess_const_apply_fail
    jsr preprocess_const_push_value
    rts
preprocess_const_apply_fail:
    sec
    rts

preprocess_const_add:
    clc
    .repeat PREPROCESS_CONST_VALUE_WIDTH, I
        lda preprocess_const_lhs_lo + I
        adc preprocess_const_rhs_lo + I
        sta preprocess_const_value_lo + I
    .endrepeat
    bvs preprocess_const_add_fail
    clc
    rts
preprocess_const_add_fail:
    sec
    rts

preprocess_const_subtract:
    sec
    .repeat PREPROCESS_CONST_VALUE_WIDTH, I
        lda preprocess_const_lhs_lo + I
        sbc preprocess_const_rhs_lo + I
        sta preprocess_const_value_lo + I
    .endrepeat
    bvs preprocess_const_subtract_fail
    clc
    rts
preprocess_const_subtract_fail:
    sec
    rts

preprocess_const_bitwise:
    ldx #$00
    lda preprocess_const_apply_operator
    cmp #PREPROCESS_CONST_OP_AND
    beq preprocess_const_bitwise_and
    cmp #PREPROCESS_CONST_OP_OR
    beq preprocess_const_bitwise_or
preprocess_const_bitwise_xor:
    lda preprocess_const_lhs_lo,x
    eor preprocess_const_rhs_lo,x
    sta preprocess_const_value_lo,x
    inx
    cpx #PREPROCESS_CONST_VALUE_WIDTH
    bcc preprocess_const_bitwise_xor
    clc
    rts
preprocess_const_bitwise_and:
    lda preprocess_const_lhs_lo,x
    and preprocess_const_rhs_lo,x
    sta preprocess_const_value_lo,x
    inx
    cpx #PREPROCESS_CONST_VALUE_WIDTH
    bcc preprocess_const_bitwise_and
    clc
    rts
preprocess_const_bitwise_or:
    lda preprocess_const_lhs_lo,x
    ora preprocess_const_rhs_lo,x
    sta preprocess_const_value_lo,x
    inx
    cpx #PREPROCESS_CONST_VALUE_WIDTH
    bcc preprocess_const_bitwise_or
    clc
    rts

preprocess_const_negate_value:
    lda preprocess_const_value_lo+7
    cmp #$80
    bne preprocess_const_twos_complement_value
    ldx #$06
preprocess_const_negate_min_check:
    lda preprocess_const_value_lo,x
    bne preprocess_const_twos_complement_value
    dex
    bpl preprocess_const_negate_min_check
    sec
    rts
preprocess_const_twos_complement_value:
    sec
    .repeat PREPROCESS_CONST_VALUE_WIDTH, I
        lda preprocess_const_value_lo + I
        eor #$FF
        adc #$00
        sta preprocess_const_value_lo + I
    .endrepeat
    clc
    rts

preprocess_const_abs_lhs:
    lda preprocess_const_lhs_lo+7
    bpl preprocess_const_abs_lhs_done
    sec
    .repeat PREPROCESS_CONST_VALUE_WIDTH, I
        lda preprocess_const_lhs_lo + I
        eor #$FF
        adc #$00
        sta preprocess_const_lhs_lo + I
    .endrepeat
preprocess_const_abs_lhs_done:
    rts

preprocess_const_abs_rhs:
    lda preprocess_const_rhs_lo+7
    bpl preprocess_const_abs_rhs_done
    sec
    .repeat PREPROCESS_CONST_VALUE_WIDTH, I
        lda preprocess_const_rhs_lo + I
        eor #$FF
        adc #$00
        sta preprocess_const_rhs_lo + I
    .endrepeat
preprocess_const_abs_rhs_done:
    rts

preprocess_const_add_lhs_unsigned:
    clc
    .repeat PREPROCESS_CONST_VALUE_WIDTH, I
        lda preprocess_const_value_lo + I
        adc preprocess_const_lhs_lo + I
        sta preprocess_const_value_lo + I
    .endrepeat
    rts

preprocess_const_shift_lhs_left:
    asl preprocess_const_lhs_lo
    .repeat 7, I
        rol preprocess_const_lhs_lo + 1 + I
    .endrepeat
    rts

preprocess_const_shift_rhs_right:
    lsr preprocess_const_rhs_lo+7
    .repeat 7, I
        ror preprocess_const_rhs_lo + 6 - I
    .endrepeat
    rts

preprocess_const_rhs_is_zero:
    lda #$00
    ldx #$00
preprocess_const_rhs_is_zero_loop:
    ora preprocess_const_rhs_lo,x
    inx
    cpx #PREPROCESS_CONST_VALUE_WIDTH
    bcc preprocess_const_rhs_is_zero_loop
    cmp #$00
    rts

preprocess_const_multiply:
    lda preprocess_const_lhs_lo+7
    eor preprocess_const_rhs_lo+7
    and #$80
    sta preprocess_const_math_sign
    jsr preprocess_const_abs_lhs
    jsr preprocess_const_abs_rhs
    jsr preprocess_const_zero_value
    lda #64
    sta preprocess_const_math_count
preprocess_const_multiply_loop:
    lda preprocess_const_rhs_lo
    and #$01
    beq preprocess_const_multiply_no_add
    jsr preprocess_const_add_lhs_unsigned
    bcs preprocess_const_multiply_fail
preprocess_const_multiply_no_add:
    jsr preprocess_const_shift_rhs_right
    jsr preprocess_const_rhs_is_zero
    beq preprocess_const_multiply_done
    jsr preprocess_const_shift_lhs_left
    bcs preprocess_const_multiply_fail
    dec preprocess_const_math_count
    bne preprocess_const_multiply_loop
preprocess_const_multiply_fail:
    sec
    rts
preprocess_const_multiply_done:
    lda preprocess_const_math_sign
    jmp preprocess_const_finalize_signed_magnitude

preprocess_const_divmod:
    jsr preprocess_const_rhs_is_zero
    bne :+
    jmp preprocess_const_divmod_fail
:
    jsr preprocess_const_lhs_is_min
    bcc preprocess_const_divmod_signs
    jsr preprocess_const_rhs_is_minus_one
    bcc preprocess_const_divmod_signs
    jmp preprocess_const_divmod_fail
preprocess_const_divmod_signs:
    lda preprocess_const_lhs_lo+7
    and #$80
    sta preprocess_const_left_negative
    lda preprocess_const_lhs_lo+7
    eor preprocess_const_rhs_lo+7
    and #$80
    sta preprocess_const_math_sign
    jsr preprocess_const_abs_lhs
    jsr preprocess_const_abs_rhs
    jsr preprocess_const_zero_value
    ldx #$07
    lda #$00
preprocess_const_divmod_zero_work:
    sta preprocess_const_work,x
    dex
    bpl preprocess_const_divmod_zero_work
    lda #64
    sta preprocess_const_math_count
preprocess_const_divmod_loop:
    asl preprocess_const_lhs_lo
    .repeat 7, I
        rol preprocess_const_lhs_lo + 1 + I
    .endrepeat
    .repeat PREPROCESS_CONST_VALUE_WIDTH, I
        rol preprocess_const_work + I
    .endrepeat
    asl preprocess_const_value_lo
    .repeat 7, I
        rol preprocess_const_value_lo + 1 + I
    .endrepeat
    jsr preprocess_const_work_compare_rhs
    bcc preprocess_const_divmod_no_subtract
    sec
    .repeat PREPROCESS_CONST_VALUE_WIDTH, I
        lda preprocess_const_work + I
        sbc preprocess_const_rhs_lo + I
        sta preprocess_const_work + I
    .endrepeat
    lda preprocess_const_value_lo
    ora #$01
    sta preprocess_const_value_lo
preprocess_const_divmod_no_subtract:
    dec preprocess_const_math_count
    beq :+
    jmp preprocess_const_divmod_loop
:
    lda preprocess_const_apply_operator
    cmp #PREPROCESS_CONST_OP_MOD
    bne preprocess_const_divmod_quotient
    ldx #$00
preprocess_const_divmod_copy_remainder:
    lda preprocess_const_work,x
    sta preprocess_const_value_lo,x
    inx
    cpx #PREPROCESS_CONST_VALUE_WIDTH
    bcc preprocess_const_divmod_copy_remainder
    lda preprocess_const_left_negative
    jmp preprocess_const_finalize_signed_magnitude
preprocess_const_divmod_quotient:
    lda preprocess_const_math_sign
    jmp preprocess_const_finalize_signed_magnitude
preprocess_const_divmod_fail:
    sec
    rts

preprocess_const_lhs_is_min:
    lda preprocess_const_lhs_lo+7
    cmp #$80
    bne preprocess_const_lhs_is_min_no
    ldx #$06
preprocess_const_lhs_is_min_loop:
    lda preprocess_const_lhs_lo,x
    bne preprocess_const_lhs_is_min_no
    dex
    bpl preprocess_const_lhs_is_min_loop
    sec
    rts
preprocess_const_lhs_is_min_no:
    clc
    rts

preprocess_const_rhs_is_minus_one:
    ldx #$07
preprocess_const_rhs_is_minus_one_loop:
    lda preprocess_const_rhs_lo,x
    cmp #$FF
    bne preprocess_const_rhs_is_minus_one_no
    dex
    bpl preprocess_const_rhs_is_minus_one_loop
    sec
    rts
preprocess_const_rhs_is_minus_one_no:
    clc
    rts

preprocess_const_work_compare_rhs:
    ldx #$07
preprocess_const_work_compare_rhs_loop:
    lda preprocess_const_work,x
    cmp preprocess_const_rhs_lo,x
    bcc preprocess_const_work_compare_rhs_less
    bne preprocess_const_work_compare_rhs_greater
    dex
    bpl preprocess_const_work_compare_rhs_loop
preprocess_const_work_compare_rhs_greater:
    sec
    rts
preprocess_const_work_compare_rhs_less:
    clc
    rts

preprocess_const_finalize_signed_magnitude:
    and #$80
    beq preprocess_const_finalize_positive
    lda preprocess_const_value_lo+7
    cmp #$80
    bcc preprocess_const_finalize_negative
    bne preprocess_const_finalize_fail
    ldx #$06
preprocess_const_finalize_min_check:
    lda preprocess_const_value_lo,x
    bne preprocess_const_finalize_fail
    dex
    bpl preprocess_const_finalize_min_check
preprocess_const_finalize_negative:
    jsr preprocess_const_twos_complement_value
    clc
    rts
preprocess_const_finalize_positive:
    lda preprocess_const_value_lo+7
    bmi preprocess_const_finalize_fail
    clc
    rts
preprocess_const_finalize_fail:
    sec
    rts

preprocess_const_validate_shift_count:
    lda preprocess_const_rhs_lo+7
    bmi preprocess_const_validate_shift_fail
    ldx #$01
preprocess_const_validate_shift_high_loop:
    lda preprocess_const_rhs_lo,x
    bne preprocess_const_validate_shift_fail
    inx
    cpx #PREPROCESS_CONST_VALUE_WIDTH
    bcc preprocess_const_validate_shift_high_loop
    lda preprocess_const_rhs_lo
    cmp #63
    bcs preprocess_const_validate_shift_fail
    sta preprocess_const_math_count
    clc
    rts
preprocess_const_validate_shift_fail:
    sec
    rts

preprocess_const_copy_lhs_to_value:
    ldx #$00
preprocess_const_copy_lhs_to_value_loop:
    lda preprocess_const_lhs_lo,x
    sta preprocess_const_value_lo,x
    inx
    cpx #PREPROCESS_CONST_VALUE_WIDTH
    bcc preprocess_const_copy_lhs_to_value_loop
    rts

preprocess_const_shift_left:
    jsr preprocess_const_validate_shift_count
    bcs preprocess_const_shift_left_fail
    jsr preprocess_const_copy_lhs_to_value
    lda preprocess_const_math_count
    beq preprocess_const_shift_left_done
preprocess_const_shift_left_loop:
    asl preprocess_const_value_lo
    .repeat 7, I
        rol preprocess_const_value_lo + 1 + I
    .endrepeat
    dec preprocess_const_math_count
    bne preprocess_const_shift_left_loop
preprocess_const_shift_left_done:
    clc
    rts
preprocess_const_shift_left_fail:
    sec
    rts

preprocess_const_shift_right:
    jsr preprocess_const_validate_shift_count
    bcs preprocess_const_shift_right_fail
    jsr preprocess_const_copy_lhs_to_value
    lda preprocess_const_math_count
    beq preprocess_const_shift_right_done
preprocess_const_shift_right_loop:
    lsr preprocess_const_value_lo+7
    .repeat 7, I
        ror preprocess_const_value_lo + 6 - I
    .endrepeat
    dec preprocess_const_math_count
    bne preprocess_const_shift_right_loop
preprocess_const_shift_right_done:
    clc
    rts
preprocess_const_shift_right_fail:
    sec
    rts

preprocess_const_check_decl_range:
    lda preprocess_const_type
    cmp #PREPROCESS_CONST_BYTE
    beq preprocess_const_check_byte_range
    cmp #PREPROCESS_CONST_CARD
    beq preprocess_const_check_card_range
    lda preprocess_const_value_hi
    bmi preprocess_const_check_int_negative
    ldx #$02
preprocess_const_check_int_positive_loop:
    lda preprocess_const_value_lo,x
    bne preprocess_const_check_decl_range_fail
    inx
    cpx #PREPROCESS_CONST_VALUE_WIDTH
    bcc preprocess_const_check_int_positive_loop
    clc
    rts
preprocess_const_check_int_negative:
    ldx #$02
preprocess_const_check_int_negative_loop:
    lda preprocess_const_value_lo,x
    cmp #$FF
    bne preprocess_const_check_decl_range_fail
    inx
    cpx #PREPROCESS_CONST_VALUE_WIDTH
    bcc preprocess_const_check_int_negative_loop
    clc
    rts
preprocess_const_check_byte_range:
    lda preprocess_const_value_hi
    bne preprocess_const_check_decl_range_fail
preprocess_const_check_card_range:
    ldx #$02
preprocess_const_check_unsigned_loop:
    lda preprocess_const_value_lo,x
    bne preprocess_const_check_decl_range_fail
    inx
    cpx #PREPROCESS_CONST_VALUE_WIDTH
    bcc preprocess_const_check_unsigned_loop
    clc
    rts
preprocess_const_check_decl_range_fail:
    sec
    rts

preprocess_const_zero_value:
    lda #$00
    ldx #$07
preprocess_const_zero_value_loop:
    sta preprocess_const_value_lo,x
    dex
    bpl preprocess_const_zero_value_loop
    rts

; Builtins are available to Idun source without an INCLUDE. Native library
; declarations may repeat them only with the same value.
preprocess_const_lookup_builtin:
    lda #<preprocess_const_builtin_table
    sta ACTC_OVERLAY_SCAN_ZP
    lda #>preprocess_const_builtin_table
    sta ACTC_OVERLAY_SCAN_ZP+1
preprocess_const_lookup_builtin_entry:
    ldy #$00
    lda (ACTC_OVERLAY_SCAN_ZP),y
    beq preprocess_const_lookup_builtin_fail
    sta preprocess_const_builtin_len
    iny
    lda (ACTC_OVERLAY_SCAN_ZP),y
    sta preprocess_const_builtin_value
    ldx #$00
preprocess_const_lookup_builtin_compare:
    cpx preprocess_const_builtin_len
    bcs preprocess_const_lookup_builtin_tail
    txa
    clc
    adc #$02
    tay
    lda (ACTC_OVERLAY_SCAN_ZP),y
    cmp preprocess_name_temp,x
    bne preprocess_const_lookup_builtin_next
    inx
    bne preprocess_const_lookup_builtin_compare
preprocess_const_lookup_builtin_tail:
    lda preprocess_name_temp,x
    bne preprocess_const_lookup_builtin_next
    lda preprocess_const_builtin_value
    clc
    rts
preprocess_const_lookup_builtin_next:
    clc
    lda ACTC_OVERLAY_SCAN_ZP
    adc preprocess_const_builtin_len
    sta ACTC_OVERLAY_SCAN_ZP
    lda ACTC_OVERLAY_SCAN_ZP+1
    adc #$00
    sta ACTC_OVERLAY_SCAN_ZP+1
    clc
    lda ACTC_OVERLAY_SCAN_ZP
    adc #$02
    sta ACTC_OVERLAY_SCAN_ZP
    bcc :+
    inc ACTC_OVERLAY_SCAN_ZP+1
:
    jmp preprocess_const_lookup_builtin_entry
preprocess_const_lookup_builtin_fail:
    sec
    rts

preprocess_const_validate_builtin_redefinition:
    ldx #$00
preprocess_const_copy_decl_name_loop:
    lda preprocess_const_name_temp,x
    sta preprocess_name_temp,x
    beq preprocess_const_copy_decl_name_done
    inx
    cpx #PREPROCESS_DEFINE_NAME_SIZE
    bcc preprocess_const_copy_decl_name_loop
    sec
    rts
preprocess_const_copy_decl_name_done:
    jsr preprocess_const_lookup_builtin
    bcs preprocess_const_builtin_redefinition_ok
    sta preprocess_const_builtin_value
    lda preprocess_const_type
    cmp #PREPROCESS_CONST_REAL
    beq preprocess_const_builtin_redefinition_fail
    lda preprocess_const_value_lo
    cmp preprocess_const_builtin_value
    bne preprocess_const_builtin_redefinition_fail
    ldx #$01
preprocess_const_builtin_redefinition_high_loop:
    lda preprocess_const_value_lo,x
    bne preprocess_const_builtin_redefinition_fail
    inx
    cpx #PREPROCESS_CONST_VALUE_WIDTH
    bcc preprocess_const_builtin_redefinition_high_loop
preprocess_const_builtin_redefinition_ok:
    clc
    rts
preprocess_const_builtin_redefinition_fail:
    sec
    rts

preprocess_const_operator_precedence:
    .byte 0,1,2,3,4,4,5,5,5,5,5,6

preprocess_const_builtin_table:
    .byte 6,$01,"JOY_UP"
    .byte 8,$02,"JOY_DOWN"
    .byte 8,$04,"JOY_LEFT"
    .byte 9,$08,"JOY_RIGHT"
    .byte 11,$10,"JOY_BUTTON1"
    .byte 11,$20,"JOY_BUTTON2"
    .byte 13,$01,"MOUSE_BUTTON1"
    .byte 13,$02,"MOUSE_BUTTON2"
    .byte 7,$10,"SID_TRI"
    .byte 7,$20,"SID_SAW"
    .byte 9,$40,"SID_PULSE"
    .byte 9,$80,"SID_NOISE"
    .byte 7,$10,"SID_LOW"
    .byte 8,$20,"SID_BAND"
    .byte 8,$40,"SID_HIGH"
    .byte 9,$00,"SPR_FRONT"
    .byte 8,$01,"SPR_BACK"
    .byte 0
