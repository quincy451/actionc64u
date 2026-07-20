; Resident, bounded IEEE-754 binary32 evaluator used by preprocessing pass I.
; Input: A/Y points at a NUL-terminated expression no longer than 64 bytes.
; Output: the same buffer contains REALBITS($LLLL:$HHHH), A is its length,
; and carry is clear. Carry set reports a malformed or over-capacity expression.

.macpack longbranch

ACTC_REAL_CONST_BIG_BYTES = 56
ACTC_REAL_CONST_VALUE_STACK_MAX = 16

actc_eval_real_const:
    sta actc_real_const_input_ptr
    sty actc_real_const_input_ptr+1
    lda scan_ptr
    sta actc_real_const_saved_scan_ptr
    lda scan_ptr+1
    sta actc_real_const_saved_scan_ptr+1
    lda const_ptr
    sta actc_real_const_saved_const_ptr
    lda const_ptr+1
    sta actc_real_const_saved_const_ptr+1
    jsr actc_real_const_save_runtime_zp
    lda actc_real_const_input_ptr
    sta scan_ptr
    lda actc_real_const_input_ptr+1
    sta scan_ptr+1
    lda #$00
    sta actc_real_const_scan
    sta actc_real_const_value_depth
    jsr actc_real_const_parse_expr
    bcs actc_eval_real_const_fail
    jsr actc_real_const_skip_spaces
    jsr actc_real_const_peek
    bne actc_eval_real_const_fail
    lda actc_real_const_value_depth
    bne actc_eval_real_const_fail
    jsr actc_real_const_canonicalize_nan
    jsr actc_real_const_format
    pha
    jsr actc_real_const_restore_state
    pla
    clc
    rts
actc_eval_real_const_fail:
    jsr actc_real_const_restore_state
    sec
    rts

actc_real_const_restore_state:
    jsr actc_real_const_restore_runtime_zp
    lda actc_real_const_saved_scan_ptr
    sta scan_ptr
    lda actc_real_const_saved_scan_ptr+1
    sta scan_ptr+1
    lda actc_real_const_saved_const_ptr
    sta const_ptr
    lda actc_real_const_saved_const_ptr+1
    sta const_ptr+1
    rts

actc_real_const_save_runtime_zp:
    ldx #$1D
actc_real_const_save_runtime_zp_loop:
    lda $02,x
    sta actc_real_const_saved_runtime_zp,x
    dex
    bpl actc_real_const_save_runtime_zp_loop
    rts

actc_real_const_restore_runtime_zp:
    ldx #$1D
actc_real_const_restore_runtime_zp_loop:
    lda actc_real_const_saved_runtime_zp,x
    sta $02,x
    dex
    bpl actc_real_const_restore_runtime_zp_loop
    rts

; Recursive descent is bounded by the explicit 16-value stack. Each operation
; rounds through the same target helpers that ALINK selects for user programs.
actc_real_const_parse_expr:
    jsr actc_real_const_parse_term
    bcs actc_real_const_parse_expr_fail
actc_real_const_parse_expr_loop:
    jsr actc_real_const_skip_spaces
    jsr actc_real_const_peek
    cmp #'+'
    beq actc_real_const_parse_expr_op
    cmp #'-'
    bne actc_real_const_parse_expr_done
actc_real_const_parse_expr_op:
    pha
    inc actc_real_const_scan
    jsr actc_real_const_push_acc
    bcs actc_real_const_parse_expr_drop
    jsr actc_real_const_parse_term
    bcs actc_real_const_parse_expr_drop
    jsr actc_real_const_pop_lhs
    pla
    jsr actc_real_const_apply_binary
    bcs actc_real_const_parse_expr_fail
    jmp actc_real_const_parse_expr_loop
actc_real_const_parse_expr_drop:
    pla
actc_real_const_parse_expr_fail:
    sec
    rts
actc_real_const_parse_expr_done:
    clc
    rts

actc_real_const_parse_term:
    jsr actc_real_const_parse_factor
    bcs actc_real_const_parse_term_fail
actc_real_const_parse_term_loop:
    jsr actc_real_const_skip_spaces
    jsr actc_real_const_peek
    cmp #'*'
    beq actc_real_const_parse_term_op
    cmp #'/'
    bne actc_real_const_parse_term_done
actc_real_const_parse_term_op:
    pha
    inc actc_real_const_scan
    jsr actc_real_const_push_acc
    bcs actc_real_const_parse_term_drop
    jsr actc_real_const_parse_factor
    bcs actc_real_const_parse_term_drop
    jsr actc_real_const_pop_lhs
    pla
    jsr actc_real_const_apply_binary
    bcs actc_real_const_parse_term_fail
    jmp actc_real_const_parse_term_loop
actc_real_const_parse_term_drop:
    pla
actc_real_const_parse_term_fail:
    sec
    rts
actc_real_const_parse_term_done:
    clc
    rts

actc_real_const_parse_factor:
    jsr actc_real_const_skip_spaces
    jsr actc_real_const_peek
    cmp #'+'
    beq actc_real_const_parse_factor_plus
    cmp #'-'
    beq actc_real_const_parse_factor_minus
    cmp #'('
    beq actc_real_const_parse_factor_group
    cmp #'.'
    beq actc_real_const_parse_factor_number
    cmp #'$'
    beq actc_real_const_parse_factor_number
    cmp #'%'
    beq actc_real_const_parse_factor_number
    cmp #'0'
    bcc actc_real_const_parse_factor_name
    cmp #('9'+1)
    bcc actc_real_const_parse_factor_number
actc_real_const_parse_factor_name:
    jsr actc_real_const_parse_named_factor
    rts
actc_real_const_parse_factor_number:
    jsr actc_real_const_parse_number
    rts
actc_real_const_parse_factor_plus:
    inc actc_real_const_scan
    jmp actc_real_const_parse_factor
actc_real_const_parse_factor_minus:
    inc actc_real_const_scan
    jsr actc_real_const_parse_factor
    bcs actc_real_const_parse_factor_fail
    lda actc_real_const_acc+3
    eor #$80
    sta actc_real_const_acc+3
    clc
    rts
actc_real_const_parse_factor_group:
    inc actc_real_const_scan
    jsr actc_real_const_parse_expr
    bcs actc_real_const_parse_factor_fail
    lda #')'
    jsr actc_real_const_expect_char
    rts
actc_real_const_parse_factor_fail:
    sec
    rts

actc_real_const_parse_named_factor:
    lda #<actc_real_const_word_realbits
    ldy #>actc_real_const_word_realbits
    jsr actc_real_const_match_word
    bcs actc_real_const_parse_named_nan
    jmp actc_real_const_parse_realbits
actc_real_const_parse_named_nan:
    lda #<actc_real_const_word_nan
    ldy #>actc_real_const_word_nan
    jsr actc_real_const_match_word
    bcs actc_real_const_parse_named_infinity
    jsr actc_real_const_require_name_end
    bcs actc_real_const_parse_named_fail
    lda #$00
    sta actc_real_const_acc
    sta actc_real_const_acc+1
    lda #$C0
    sta actc_real_const_acc+2
    lda #$7F
    sta actc_real_const_acc+3
    clc
    rts
actc_real_const_parse_named_infinity:
    lda #<actc_real_const_word_infinity
    ldy #>actc_real_const_word_infinity
    jsr actc_real_const_match_word
    bcc actc_real_const_parse_named_inf_value
    lda #<actc_real_const_word_inf
    ldy #>actc_real_const_word_inf
    jsr actc_real_const_match_word
    bcs actc_real_const_parse_named_real
actc_real_const_parse_named_inf_value:
    jsr actc_real_const_require_name_end
    bcs actc_real_const_parse_named_fail
    jsr actc_real_const_set_infinity
    clc
    rts
actc_real_const_parse_named_real:
    lda #<actc_real_const_word_real
    ldy #>actc_real_const_word_real
    jsr actc_real_const_match_word
    bcs actc_real_const_parse_named_fabs
    jsr actc_real_const_parse_function_argument
    rts
actc_real_const_parse_named_fabs:
    lda #<actc_real_const_word_fabs
    ldy #>actc_real_const_word_fabs
    jsr actc_real_const_match_word
    bcs actc_real_const_parse_named_fsqrt
    jsr actc_real_const_parse_function_argument
    bcs actc_real_const_parse_named_fail
    lda actc_real_const_acc+3
    and #$7F
    sta actc_real_const_acc+3
    clc
    rts
actc_real_const_parse_named_fsqrt:
    lda #<actc_real_const_word_fsqrt
    ldy #>actc_real_const_word_fsqrt
    jsr actc_real_const_match_word
    bcs actc_real_const_parse_named_fail
    jsr actc_real_const_parse_function_argument
    bcs actc_real_const_parse_named_fail
    jsr actc_real_const_apply_sqrt
    rts
actc_real_const_parse_named_fail:
    sec
    rts

actc_real_const_parse_function_argument:
    lda #'('
    jsr actc_real_const_expect_char
    bcs actc_real_const_parse_function_argument_fail
    jsr actc_real_const_parse_expr
    bcs actc_real_const_parse_function_argument_fail
    lda #')'
    jsr actc_real_const_expect_char
    rts
actc_real_const_parse_function_argument_fail:
    sec
    rts

actc_real_const_parse_realbits:
    lda #'('
    jsr actc_real_const_expect_char
    bcs actc_real_const_parse_realbits_fail
    jsr actc_real_const_parse_hex_word
    bcs actc_real_const_parse_realbits_fail
    lda actc_real_const_word_value
    sta actc_real_const_acc
    lda actc_real_const_word_value+1
    sta actc_real_const_acc+1
    lda #':'
    jsr actc_real_const_expect_char
    bcs actc_real_const_parse_realbits_fail
    jsr actc_real_const_parse_hex_word
    bcs actc_real_const_parse_realbits_fail
    lda actc_real_const_word_value
    sta actc_real_const_acc+2
    lda actc_real_const_word_value+1
    sta actc_real_const_acc+3
    lda #')'
    jsr actc_real_const_expect_char
    rts
actc_real_const_parse_realbits_fail:
    sec
    rts

actc_real_const_parse_hex_word:
    jsr actc_real_const_skip_spaces
    jsr actc_real_const_peek
    cmp #'$'
    bne actc_real_const_parse_hex_word_fail
    inc actc_real_const_scan
    lda #$00
    sta actc_real_const_word_value
    sta actc_real_const_word_value+1
    sta actc_real_const_digit_count
actc_real_const_parse_hex_word_loop:
    jsr actc_real_const_peek
    jsr actc_real_const_hex_digit
    bcs actc_real_const_parse_hex_word_done
    pha
    lda actc_real_const_digit_count
    cmp #$04
    bcs actc_real_const_parse_hex_word_drop_fail
    asl actc_real_const_word_value
    rol actc_real_const_word_value+1
    asl actc_real_const_word_value
    rol actc_real_const_word_value+1
    asl actc_real_const_word_value
    rol actc_real_const_word_value+1
    asl actc_real_const_word_value
    rol actc_real_const_word_value+1
    pla
    ora actc_real_const_word_value
    sta actc_real_const_word_value
    inc actc_real_const_digit_count
    inc actc_real_const_scan
    jmp actc_real_const_parse_hex_word_loop
actc_real_const_parse_hex_word_drop_fail:
    pla
actc_real_const_parse_hex_word_fail:
    sec
    rts
actc_real_const_parse_hex_word_done:
    lda actc_real_const_digit_count
    beq actc_real_const_parse_hex_word_fail
    clc
    rts

actc_real_const_parse_number:
    jsr actc_real_const_big_clear_num
    lda #$00
    sta actc_real_const_number_significant
    sta actc_real_const_significant_digits
    sta actc_real_const_fraction_digits
    sta actc_real_const_decimal_seen
    sta actc_real_const_digit_seen
    sta actc_real_const_explicit_negative
    sta actc_real_const_explicit_exp
    sta actc_real_const_explicit_exp+1
    jsr actc_real_const_peek
    cmp #'$'
    beq actc_real_const_parse_number_hex
    cmp #'%'
    beq actc_real_const_parse_number_binary
    cmp #'0'
    bne actc_real_const_parse_number_decimal
    ldy actc_real_const_scan
    iny
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'X'
    beq actc_real_const_parse_number_c_hex
    jmp actc_real_const_parse_number_decimal
actc_real_const_parse_number_hex:
    inc actc_real_const_scan
    lda #16
    bne actc_real_const_parse_integer_base
actc_real_const_parse_number_c_hex:
    inc actc_real_const_scan
    inc actc_real_const_scan
    lda #16
    bne actc_real_const_parse_integer_base
actc_real_const_parse_number_binary:
    inc actc_real_const_scan
    lda #2
actc_real_const_parse_integer_base:
    sta actc_real_const_number_base
actc_real_const_parse_integer_loop:
    jsr actc_real_const_peek
    jsr actc_real_const_hex_digit
    bcs actc_real_const_parse_integer_done
    cmp actc_real_const_number_base
    bcs actc_real_const_parse_integer_done
    sta actc_real_const_digit
    lda actc_real_const_number_base
    jsr actc_real_const_big_mul_num_small
    jcs actc_real_const_parse_number_fail
    lda actc_real_const_digit
    jsr actc_real_const_big_add_num_byte
    jcs actc_real_const_parse_number_fail
    inc actc_real_const_digit_seen
    inc actc_real_const_scan
    jmp actc_real_const_parse_integer_loop
actc_real_const_parse_integer_done:
    lda actc_real_const_digit_seen
    jeq actc_real_const_parse_number_fail
    lda #$00
    sta actc_real_const_exp10
    sta actc_real_const_exp10+1
    jmp actc_real_const_decimal_to_binary32

actc_real_const_parse_number_decimal:
    jsr actc_real_const_peek
    cmp #'.'
    beq actc_real_const_parse_number_dot
    cmp #'0'
    bcc actc_real_const_parse_number_decimal_done
    cmp #('9'+1)
    bcs actc_real_const_parse_number_decimal_done
    sec
    sbc #'0'
    sta actc_real_const_digit
    lda #10
    jsr actc_real_const_big_mul_num_small
    jcs actc_real_const_parse_number_fail
    lda actc_real_const_digit
    jsr actc_real_const_big_add_num_byte
    jcs actc_real_const_parse_number_fail
    lda #$01
    sta actc_real_const_digit_seen
    lda actc_real_const_decimal_seen
    beq actc_real_const_parse_number_not_fraction
    inc actc_real_const_fraction_digits
actc_real_const_parse_number_not_fraction:
    lda actc_real_const_number_significant
    bne actc_real_const_parse_number_count_significant
    lda actc_real_const_digit
    beq actc_real_const_parse_number_advance
    lda #$01
    sta actc_real_const_number_significant
actc_real_const_parse_number_count_significant:
    inc actc_real_const_significant_digits
actc_real_const_parse_number_advance:
    inc actc_real_const_scan
    jmp actc_real_const_parse_number_decimal
actc_real_const_parse_number_dot:
    lda actc_real_const_decimal_seen
    bne actc_real_const_parse_number_decimal_done
    lda #$01
    sta actc_real_const_decimal_seen
    inc actc_real_const_scan
    jmp actc_real_const_parse_number_decimal
actc_real_const_parse_number_decimal_done:
    lda actc_real_const_digit_seen
    jeq actc_real_const_parse_number_fail
    jsr actc_real_const_peek
    jsr uppercase_ascii
    cmp #'E'
    bne actc_real_const_parse_number_have_exp
    inc actc_real_const_scan
    jsr actc_real_const_peek
    cmp #'+'
    beq actc_real_const_parse_number_exp_sign
    cmp #'-'
    bne actc_real_const_parse_number_exp_digits
    lda #$01
    sta actc_real_const_explicit_negative
actc_real_const_parse_number_exp_sign:
    inc actc_real_const_scan
actc_real_const_parse_number_exp_digits:
    lda #$00
    sta actc_real_const_digit_count
actc_real_const_parse_number_exp_loop:
    jsr actc_real_const_peek
    cmp #'0'
    bcc actc_real_const_parse_number_exp_done
    cmp #('9'+1)
    bcs actc_real_const_parse_number_exp_done
    sec
    sbc #'0'
    sta actc_real_const_digit
    lda actc_real_const_explicit_exp+1
    bne actc_real_const_parse_number_exp_clamp
    lda actc_real_const_explicit_exp
    cmp #100
    bcs actc_real_const_parse_number_exp_clamp
    asl actc_real_const_explicit_exp
    lda actc_real_const_explicit_exp
    sta actc_real_const_word_value
    asl actc_real_const_explicit_exp
    asl actc_real_const_explicit_exp
    clc
    lda actc_real_const_explicit_exp
    adc actc_real_const_word_value
    adc actc_real_const_digit
    sta actc_real_const_explicit_exp
    lda #$00
    adc #$00
    sta actc_real_const_explicit_exp+1
    jmp actc_real_const_parse_number_exp_advance
actc_real_const_parse_number_exp_clamp:
    lda #$E8
    sta actc_real_const_explicit_exp
    lda #$03
    sta actc_real_const_explicit_exp+1
actc_real_const_parse_number_exp_advance:
    inc actc_real_const_digit_count
    inc actc_real_const_scan
    jmp actc_real_const_parse_number_exp_loop
actc_real_const_parse_number_exp_done:
    lda actc_real_const_digit_count
    beq actc_real_const_parse_number_fail
actc_real_const_parse_number_have_exp:
    sec
    lda actc_real_const_explicit_exp
    sbc actc_real_const_fraction_digits
    sta actc_real_const_exp10
    lda actc_real_const_explicit_exp+1
    sbc #$00
    sta actc_real_const_exp10+1
    lda actc_real_const_explicit_negative
    beq actc_real_const_decimal_to_binary32
    sec
    lda #$00
    sbc actc_real_const_explicit_exp
    sta actc_real_const_exp10
    lda #$00
    sbc actc_real_const_explicit_exp+1
    sta actc_real_const_exp10+1
    sec
    lda actc_real_const_exp10
    sbc actc_real_const_fraction_digits
    sta actc_real_const_exp10
    lda actc_real_const_exp10+1
    sbc #$00
    sta actc_real_const_exp10+1
    jmp actc_real_const_decimal_to_binary32
actc_real_const_parse_number_fail:
    sec
    rts

; Convert exact N*10^exp10 to binary32. Relevant decimal orders fit in the
; 448-bit work arrays; orders outside binary32's rounding envelope are decided
; before any power expansion.
actc_real_const_decimal_to_binary32:
    jsr actc_real_const_big_num_is_zero
    bne actc_real_const_decimal_nonzero
    jsr actc_real_const_set_zero
    clc
    rts
actc_real_const_decimal_nonzero:
    lda actc_real_const_significant_digits
    bne actc_real_const_decimal_have_significant
    ; Radix-prefixed integers do not use decimal-order screening.
    jmp actc_real_const_decimal_build_ratio
actc_real_const_decimal_have_significant:
    clc
    lda actc_real_const_exp10
    adc actc_real_const_significant_digits
    sta actc_real_const_decimal_order
    lda actc_real_const_exp10+1
    adc #$00
    sta actc_real_const_decimal_order+1
    sec
    lda actc_real_const_decimal_order
    sbc #$01
    sta actc_real_const_decimal_order
    lda actc_real_const_decimal_order+1
    sbc #$00
    sta actc_real_const_decimal_order+1
    lda actc_real_const_decimal_order+1
    bmi actc_real_const_decimal_order_negative
    bne actc_real_const_decimal_overflow
    lda actc_real_const_decimal_order
    cmp #39
    bcs actc_real_const_decimal_overflow
    jmp actc_real_const_decimal_build_ratio
actc_real_const_decimal_order_negative:
    lda actc_real_const_decimal_order+1
    cmp #$FF
    bne actc_real_const_decimal_underflow
    lda actc_real_const_decimal_order
    cmp #($D2) ; -46
    bcc actc_real_const_decimal_underflow
    jmp actc_real_const_decimal_build_ratio
actc_real_const_decimal_overflow:
    jsr actc_real_const_set_infinity
    clc
    rts
actc_real_const_decimal_underflow:
    jsr actc_real_const_set_zero
    clc
    rts

actc_real_const_decimal_build_ratio:
    jsr actc_real_const_big_clear_den
    lda #$01
    sta actc_real_const_big_den
    lda actc_real_const_exp10+1
    bmi actc_real_const_decimal_negative_exp
    lda actc_real_const_exp10
    sta actc_real_const_loop_count
    lda actc_real_const_exp10+1
    sta actc_real_const_loop_count+1
actc_real_const_decimal_positive_exp_loop:
    jsr actc_real_const_loop_count_is_zero
    beq actc_real_const_decimal_positive_shift_setup
    jsr actc_real_const_big_mul_num_by_five
    jcs actc_real_const_parse_number_fail
    jsr actc_real_const_dec_loop_count
    jmp actc_real_const_decimal_positive_exp_loop
actc_real_const_decimal_positive_shift_setup:
    lda actc_real_const_exp10
    sta actc_real_const_loop_count
    lda actc_real_const_exp10+1
    sta actc_real_const_loop_count+1
actc_real_const_decimal_positive_shift_loop:
    jsr actc_real_const_loop_count_is_zero
    beq actc_real_const_ratio_to_binary32
    jsr actc_real_const_big_shift_num_left
    jcs actc_real_const_parse_number_fail
    jsr actc_real_const_dec_loop_count
    jmp actc_real_const_decimal_positive_shift_loop
actc_real_const_decimal_negative_exp:
    sec
    lda #$00
    sbc actc_real_const_exp10
    sta actc_real_const_loop_count
    lda #$00
    sbc actc_real_const_exp10+1
    sta actc_real_const_loop_count+1
    lda actc_real_const_loop_count
    sta actc_real_const_shift_count
    lda actc_real_const_loop_count+1
    sta actc_real_const_shift_count+1
actc_real_const_decimal_negative_mul_loop:
    jsr actc_real_const_loop_count_is_zero
    beq actc_real_const_decimal_negative_shift_loop
    jsr actc_real_const_big_mul_den_by_five
    jcs actc_real_const_parse_number_fail
    jsr actc_real_const_dec_loop_count
    jmp actc_real_const_decimal_negative_mul_loop
actc_real_const_decimal_negative_shift_loop:
    jsr actc_real_const_shift_count_is_zero
    beq actc_real_const_ratio_to_binary32
    jsr actc_real_const_big_shift_den_left
    jcs actc_real_const_parse_number_fail
    jsr actc_real_const_dec_shift_count
    jmp actc_real_const_decimal_negative_shift_loop

actc_real_const_ratio_to_binary32:
    jsr actc_real_const_big_num_bits
    jsr actc_real_const_big_den_bits
    sec
    lda actc_real_const_num_bits
    sbc actc_real_const_den_bits
    sta actc_real_const_e2
    lda actc_real_const_num_bits+1
    sbc actc_real_const_den_bits+1
    sta actc_real_const_e2+1
    lda actc_real_const_e2+1
    bmi actc_real_const_ratio_adjust_negative
    jsr actc_real_const_big_copy_den_to_work
    lda actc_real_const_e2
    sta actc_real_const_shift_count
    lda actc_real_const_e2+1
    sta actc_real_const_shift_count+1
    jsr actc_real_const_big_shift_work_count
    jcs actc_real_const_parse_number_fail
    jsr actc_real_const_big_compare_num_work
    bcs actc_real_const_ratio_e2_ready
    jmp actc_real_const_ratio_dec_e2
actc_real_const_ratio_adjust_negative:
    jsr actc_real_const_big_copy_num_to_work
    sec
    lda #$00
    sbc actc_real_const_e2
    sta actc_real_const_shift_count
    lda #$00
    sbc actc_real_const_e2+1
    sta actc_real_const_shift_count+1
    jsr actc_real_const_big_shift_work_count
    jcs actc_real_const_parse_number_fail
    jsr actc_real_const_big_compare_work_den
    bcs actc_real_const_ratio_e2_ready
actc_real_const_ratio_dec_e2:
    sec
    lda actc_real_const_e2
    sbc #$01
    sta actc_real_const_e2
    lda actc_real_const_e2+1
    sbc #$00
    sta actc_real_const_e2+1
actc_real_const_ratio_e2_ready:
    lda actc_real_const_e2+1
    bmi actc_real_const_ratio_maybe_subnormal
    jne actc_real_const_decimal_overflow
    lda actc_real_const_e2
    cmp #128
    jcs actc_real_const_decimal_overflow
    jmp actc_real_const_ratio_normal
actc_real_const_ratio_maybe_subnormal:
    lda actc_real_const_e2+1
    cmp #$FF
    bne actc_real_const_ratio_subnormal
    lda actc_real_const_e2
    cmp #$82
    bcc actc_real_const_ratio_subnormal
actc_real_const_ratio_normal:
    lda #$01
    sta actc_real_const_normal
    sec
    lda #23
    sbc actc_real_const_e2
    sta actc_real_const_scale
    lda #$00
    sbc actc_real_const_e2+1
    sta actc_real_const_scale+1
    jmp actc_real_const_ratio_apply_scale
actc_real_const_ratio_subnormal:
    lda #$00
    sta actc_real_const_normal
    lda #149
    sta actc_real_const_scale
    lda #$00
    sta actc_real_const_scale+1
actc_real_const_ratio_apply_scale:
    lda actc_real_const_scale+1
    bmi actc_real_const_ratio_scale_den
    lda actc_real_const_scale
    sta actc_real_const_shift_count
    lda actc_real_const_scale+1
    sta actc_real_const_shift_count+1
    jsr actc_real_const_big_shift_num_count
    jcs actc_real_const_parse_number_fail
    jmp actc_real_const_ratio_divide
actc_real_const_ratio_scale_den:
    sec
    lda #$00
    sbc actc_real_const_scale
    sta actc_real_const_shift_count
    lda #$00
    sbc actc_real_const_scale+1
    sta actc_real_const_shift_count+1
    jsr actc_real_const_big_shift_den_count
    jcs actc_real_const_parse_number_fail
actc_real_const_ratio_divide:
    jsr actc_real_const_big_divide
    jcs actc_real_const_parse_number_fail
    jsr actc_real_const_round_quotient
    jcs actc_real_const_parse_number_fail
    lda actc_real_const_normal
    beq actc_real_const_pack_subnormal
    lda actc_real_const_quotient+3
    and #$01
    beq actc_real_const_pack_normal_ready
    lsr actc_real_const_quotient+3
    ror actc_real_const_quotient+2
    ror actc_real_const_quotient+1
    ror actc_real_const_quotient
    inc actc_real_const_e2
    bne actc_real_const_pack_normal_ready
    inc actc_real_const_e2+1
actc_real_const_pack_normal_ready:
    lda actc_real_const_e2+1
    jne actc_real_const_decimal_overflow
    lda actc_real_const_e2
    cmp #128
    jcs actc_real_const_decimal_overflow
    clc
    adc #127
    sta actc_real_const_biased_exp
    lda actc_real_const_quotient
    sta actc_real_const_acc
    lda actc_real_const_quotient+1
    sta actc_real_const_acc+1
    lda actc_real_const_quotient+2
    and #$7F
    sta actc_real_const_acc+2
    lda actc_real_const_biased_exp
    and #$01
    beq actc_real_const_pack_normal_exp_high
    lda actc_real_const_acc+2
    ora #$80
    sta actc_real_const_acc+2
actc_real_const_pack_normal_exp_high:
    lda actc_real_const_biased_exp
    lsr a
    sta actc_real_const_acc+3
    clc
    rts
actc_real_const_pack_subnormal:
    lda actc_real_const_quotient
    sta actc_real_const_acc
    lda actc_real_const_quotient+1
    sta actc_real_const_acc+1
    lda actc_real_const_quotient+2
    sta actc_real_const_acc+2
    lda #$00
    sta actc_real_const_acc+3
    clc
    rts

actc_real_const_apply_binary:
    sta actc_real_const_operator
    lda #<actc_real_const_lhs
    sta $02
    lda #>actc_real_const_lhs
    sta $03
    lda #<actc_real_const_acc
    sta $04
    lda #>actc_real_const_acc
    sta $05
    lda #<actc_real_const_acc
    sta $06
    lda #>actc_real_const_acc
    sta $07
    lda actc_real_const_operator
    cmp #'+'
    beq actc_real_const_apply_add
    cmp #'-'
    beq actc_real_const_apply_sub
    cmp #'*'
    beq actc_real_const_apply_mul
    cmp #'/'
    beq actc_real_const_apply_div
    sec
    rts
actc_real_const_apply_add:
    jsr actc_const_rt_f_add
    clc
    rts
actc_real_const_apply_sub:
    jsr actc_const_rt_f_sub
    clc
    rts
actc_real_const_apply_mul:
    jsr actc_const_rt_f_mul
    clc
    rts
actc_real_const_apply_div:
    jsr actc_const_rt_f_div
    clc
    rts

actc_real_const_apply_sqrt:
    lda #<actc_real_const_acc
    sta $02
    sta $06
    lda #>actc_real_const_acc
    sta $03
    sta $07
    jsr actc_const_rt_f_sqrt
    clc
    rts

actc_real_const_push_acc:
    lda actc_real_const_value_depth
    cmp #ACTC_REAL_CONST_VALUE_STACK_MAX
    bcs actc_real_const_push_acc_fail
    asl a
    asl a
    tax
    lda actc_real_const_acc
    sta actc_real_const_value_stack,x
    lda actc_real_const_acc+1
    sta actc_real_const_value_stack+1,x
    lda actc_real_const_acc+2
    sta actc_real_const_value_stack+2,x
    lda actc_real_const_acc+3
    sta actc_real_const_value_stack+3,x
    inc actc_real_const_value_depth
    clc
    rts
actc_real_const_push_acc_fail:
    sec
    rts

actc_real_const_pop_lhs:
    dec actc_real_const_value_depth
    lda actc_real_const_value_depth
    asl a
    asl a
    tax
    lda actc_real_const_value_stack,x
    sta actc_real_const_lhs
    lda actc_real_const_value_stack+1,x
    sta actc_real_const_lhs+1
    lda actc_real_const_value_stack+2,x
    sta actc_real_const_lhs+2
    lda actc_real_const_value_stack+3,x
    sta actc_real_const_lhs+3
    rts

actc_real_const_skip_spaces:
    jsr actc_real_const_peek
    cmp #' '
    beq actc_real_const_skip_spaces_one
    cmp #9
    bne actc_real_const_skip_spaces_done
actc_real_const_skip_spaces_one:
    inc actc_real_const_scan
    bne actc_real_const_skip_spaces
actc_real_const_skip_spaces_done:
    rts

actc_real_const_peek:
    ldy actc_real_const_scan
    lda (scan_ptr),y
    rts

actc_real_const_expect_char:
    sta actc_real_const_expected_char
    jsr actc_real_const_skip_spaces
    jsr actc_real_const_peek
    cmp actc_real_const_expected_char
    bne actc_real_const_expect_char_fail
    inc actc_real_const_scan
    clc
    rts
actc_real_const_expect_char_fail:
    sec
    rts

actc_real_const_match_word:
    sta const_ptr
    sty const_ptr+1
    lda actc_real_const_scan
    pha
    ldx #$00
actc_real_const_match_word_loop:
    txa
    tay
    lda (const_ptr),y
    beq actc_real_const_match_word_ok
    sta actc_real_const_expected_char
    jsr actc_real_const_peek
    jsr uppercase_ascii
    cmp actc_real_const_expected_char
    bne actc_real_const_match_word_fail
    inc actc_real_const_scan
    inx
    bne actc_real_const_match_word_loop
actc_real_const_match_word_fail:
    pla
    sta actc_real_const_scan
    sec
    rts
actc_real_const_match_word_ok:
    pla
    clc
    rts

actc_real_const_require_name_end:
    jsr actc_real_const_peek
    cmp #'_'
    beq actc_real_const_require_name_end_fail
    jsr uppercase_symbol_body_valid
    bcc actc_real_const_require_name_end_fail
    clc
    rts
actc_real_const_require_name_end_fail:
    sec
    rts

actc_real_const_hex_digit:
    cmp #'0'
    bcc actc_real_const_hex_digit_fail
    cmp #('9'+1)
    bcc actc_real_const_hex_digit_decimal
    jsr uppercase_ascii
    cmp #'A'
    bcc actc_real_const_hex_digit_fail
    cmp #('F'+1)
    bcs actc_real_const_hex_digit_fail
    sec
    sbc #('A'-10)
    clc
    rts
actc_real_const_hex_digit_decimal:
    sec
    sbc #'0'
    clc
    rts
actc_real_const_hex_digit_fail:
    sec
    rts

actc_real_const_set_zero:
    lda #$00
    sta actc_real_const_acc
    sta actc_real_const_acc+1
    sta actc_real_const_acc+2
    sta actc_real_const_acc+3
    rts

actc_real_const_set_infinity:
    lda #$00
    sta actc_real_const_acc
    sta actc_real_const_acc+1
    lda #$80
    sta actc_real_const_acc+2
    lda #$7F
    sta actc_real_const_acc+3
    rts

actc_real_const_canonicalize_nan:
    lda actc_real_const_acc+3
    and #$7F
    cmp #$7F
    bne actc_real_const_canonicalize_nan_done
    lda actc_real_const_acc+2
    and #$80
    beq actc_real_const_canonicalize_nan_done
    lda actc_real_const_acc
    ora actc_real_const_acc+1
    sta actc_real_const_digit
    lda actc_real_const_acc+2
    and #$7F
    ora actc_real_const_digit
    beq actc_real_const_canonicalize_nan_done
    lda #$00
    sta actc_real_const_acc
    sta actc_real_const_acc+1
    lda #$C0
    sta actc_real_const_acc+2
    lda #$7F
    sta actc_real_const_acc+3
actc_real_const_canonicalize_nan_done:
    rts

actc_real_const_format:
    ldy #$00
    ldx #$00
actc_real_const_format_prefix_loop:
    lda actc_real_const_canonical_prefix,x
    beq actc_real_const_format_low
    sta (scan_ptr),y
    iny
    inx
    bne actc_real_const_format_prefix_loop
actc_real_const_format_low:
    lda actc_real_const_acc+1
    jsr actc_real_const_format_hex_byte
    lda actc_real_const_acc
    jsr actc_real_const_format_hex_byte
    lda #':'
    sta (scan_ptr),y
    iny
    lda #'$'
    sta (scan_ptr),y
    iny
    lda actc_real_const_acc+3
    jsr actc_real_const_format_hex_byte
    lda actc_real_const_acc+2
    jsr actc_real_const_format_hex_byte
    lda #')'
    sta (scan_ptr),y
    iny
    lda #$00
    sta (scan_ptr),y
    tya
    rts

actc_real_const_format_hex_byte:
    pha
    lsr a
    lsr a
    lsr a
    lsr a
    jsr actc_real_const_format_hex_nibble
    pla
    and #$0F
actc_real_const_format_hex_nibble:
    cmp #10
    bcc actc_real_const_format_hex_decimal
    adc #('A'-10-1)
    bne actc_real_const_format_hex_store
actc_real_const_format_hex_decimal:
    adc #'0'
actc_real_const_format_hex_store:
    sta (scan_ptr),y
    iny
    rts

; Fixed-width unsigned big-integer helpers. Carry from compares means left is
; greater than or equal to right; carry from shifts/multiplies means overflow.
actc_real_const_big_clear_num:
    ldx #(ACTC_REAL_CONST_BIG_BYTES-1)
    lda #$00
actc_real_const_big_clear_num_loop:
    sta actc_real_const_big_num,x
    dex
    bpl actc_real_const_big_clear_num_loop
    rts

actc_real_const_big_clear_den:
    ldx #(ACTC_REAL_CONST_BIG_BYTES-1)
    lda #$00
actc_real_const_big_clear_den_loop:
    sta actc_real_const_big_den,x
    dex
    bpl actc_real_const_big_clear_den_loop
    rts

actc_real_const_big_clear_work:
    ldx #(ACTC_REAL_CONST_BIG_BYTES-1)
    lda #$00
actc_real_const_big_clear_work_loop:
    sta actc_real_const_big_work,x
    dex
    bpl actc_real_const_big_clear_work_loop
    rts

actc_real_const_big_clear_quotient:
    lda #$00
    sta actc_real_const_quotient
    sta actc_real_const_quotient+1
    sta actc_real_const_quotient+2
    sta actc_real_const_quotient+3
    rts

actc_real_const_big_num_is_zero:
    ldx #(ACTC_REAL_CONST_BIG_BYTES-1)
actc_real_const_big_num_is_zero_loop:
    lda actc_real_const_big_num,x
    bne actc_real_const_big_num_is_zero_no
    dex
    bpl actc_real_const_big_num_is_zero_loop
    lda #$00
    rts
actc_real_const_big_num_is_zero_no:
    lda #$01
    rts

actc_real_const_big_mul_num_small:
    sta actc_real_const_small_count
    ldx #(ACTC_REAL_CONST_BIG_BYTES-1)
actc_real_const_big_mul_num_copy:
    lda actc_real_const_big_num,x
    sta actc_real_const_big_work,x
    dex
    bpl actc_real_const_big_mul_num_copy
    jsr actc_real_const_big_clear_num
actc_real_const_big_mul_num_loop:
    lda actc_real_const_small_count
    beq actc_real_const_big_mul_num_done
    clc
    ldx #$00
    ldy #ACTC_REAL_CONST_BIG_BYTES
actc_real_const_big_mul_num_add_loop:
    lda actc_real_const_big_num,x
    adc actc_real_const_big_work,x
    sta actc_real_const_big_num,x
    inx
    dey
    bne actc_real_const_big_mul_num_add_loop
    bcs actc_real_const_big_mul_num_fail
    dec actc_real_const_small_count
    jmp actc_real_const_big_mul_num_loop
actc_real_const_big_mul_num_done:
    clc
    rts
actc_real_const_big_mul_num_fail:
    sec
    rts

actc_real_const_big_mul_num_by_five:
    lda #$05
    jmp actc_real_const_big_mul_num_small

actc_real_const_big_mul_den_by_five:
    ldx #(ACTC_REAL_CONST_BIG_BYTES-1)
actc_real_const_big_mul_den_copy:
    lda actc_real_const_big_den,x
    sta actc_real_const_big_work,x
    dex
    bpl actc_real_const_big_mul_den_copy
    jsr actc_real_const_big_clear_den
    lda #$05
    sta actc_real_const_small_count
actc_real_const_big_mul_den_loop:
    clc
    ldx #$00
    ldy #ACTC_REAL_CONST_BIG_BYTES
actc_real_const_big_mul_den_add_loop:
    lda actc_real_const_big_den,x
    adc actc_real_const_big_work,x
    sta actc_real_const_big_den,x
    inx
    dey
    bne actc_real_const_big_mul_den_add_loop
    bcs actc_real_const_big_mul_den_fail
    dec actc_real_const_small_count
    bne actc_real_const_big_mul_den_loop
    clc
    rts
actc_real_const_big_mul_den_fail:
    sec
    rts

actc_real_const_big_add_num_byte:
    clc
    adc actc_real_const_big_num
    sta actc_real_const_big_num
    bcc actc_real_const_big_add_num_byte_done
    ldx #$01
    ldy #(ACTC_REAL_CONST_BIG_BYTES-1)
actc_real_const_big_add_num_byte_loop:
    lda actc_real_const_big_num,x
    adc #$00
    sta actc_real_const_big_num,x
    bcc actc_real_const_big_add_num_byte_done
    inx
    dey
    bne actc_real_const_big_add_num_byte_loop
    sec
    rts
actc_real_const_big_add_num_byte_done:
    clc
    rts

actc_real_const_big_shift_num_left:
    clc
    ldx #$00
    ldy #ACTC_REAL_CONST_BIG_BYTES
actc_real_const_big_shift_num_left_loop:
    rol actc_real_const_big_num,x
    inx
    dey
    bne actc_real_const_big_shift_num_left_loop
    rts

actc_real_const_big_shift_den_left:
    clc
    ldx #$00
    ldy #ACTC_REAL_CONST_BIG_BYTES
actc_real_const_big_shift_den_left_loop:
    rol actc_real_const_big_den,x
    inx
    dey
    bne actc_real_const_big_shift_den_left_loop
    rts

actc_real_const_big_shift_work_left:
    clc
    ldx #$00
    ldy #ACTC_REAL_CONST_BIG_BYTES
actc_real_const_big_shift_work_left_loop:
    rol actc_real_const_big_work,x
    inx
    dey
    bne actc_real_const_big_shift_work_left_loop
    rts

actc_real_const_big_shift_divisor_left:
    clc
    ldx #$00
    ldy #ACTC_REAL_CONST_BIG_BYTES
actc_real_const_big_shift_divisor_left_loop:
    rol actc_real_const_big_divisor,x
    inx
    dey
    bne actc_real_const_big_shift_divisor_left_loop
    rts

actc_real_const_big_shift_divisor_right:
    clc
    ldx #(ACTC_REAL_CONST_BIG_BYTES-1)
actc_real_const_big_shift_divisor_right_loop:
    ror actc_real_const_big_divisor,x
    dex
    bpl actc_real_const_big_shift_divisor_right_loop
    rts

actc_real_const_big_shift_num_count:
    jsr actc_real_const_shift_count_is_zero
    beq actc_real_const_big_shift_count_done
    jsr actc_real_const_big_shift_num_left
    bcs actc_real_const_big_shift_count_fail
    jsr actc_real_const_dec_shift_count
    jmp actc_real_const_big_shift_num_count
actc_real_const_big_shift_den_count:
    jsr actc_real_const_shift_count_is_zero
    beq actc_real_const_big_shift_count_done
    jsr actc_real_const_big_shift_den_left
    bcs actc_real_const_big_shift_count_fail
    jsr actc_real_const_dec_shift_count
    jmp actc_real_const_big_shift_den_count
actc_real_const_big_shift_work_count:
    jsr actc_real_const_shift_count_is_zero
    beq actc_real_const_big_shift_count_done
    jsr actc_real_const_big_shift_work_left
    bcs actc_real_const_big_shift_count_fail
    jsr actc_real_const_dec_shift_count
    jmp actc_real_const_big_shift_work_count
actc_real_const_big_shift_count_done:
    clc
    rts
actc_real_const_big_shift_count_fail:
    sec
    rts

actc_real_const_big_copy_num_to_work:
    ldx #(ACTC_REAL_CONST_BIG_BYTES-1)
actc_real_const_big_copy_num_to_work_loop:
    lda actc_real_const_big_num,x
    sta actc_real_const_big_work,x
    dex
    bpl actc_real_const_big_copy_num_to_work_loop
    rts
actc_real_const_big_copy_den_to_work:
    ldx #(ACTC_REAL_CONST_BIG_BYTES-1)
actc_real_const_big_copy_den_to_work_loop:
    lda actc_real_const_big_den,x
    sta actc_real_const_big_work,x
    dex
    bpl actc_real_const_big_copy_den_to_work_loop
    rts
actc_real_const_big_copy_den_to_divisor:
    ldx #(ACTC_REAL_CONST_BIG_BYTES-1)
actc_real_const_big_copy_den_to_divisor_loop:
    lda actc_real_const_big_den,x
    sta actc_real_const_big_divisor,x
    dex
    bpl actc_real_const_big_copy_den_to_divisor_loop
    rts

actc_real_const_big_num_bits:
    ldx #(ACTC_REAL_CONST_BIG_BYTES-1)
actc_real_const_big_num_bits_find:
    lda actc_real_const_big_num,x
    bne actc_real_const_big_num_bits_byte
    dex
    bpl actc_real_const_big_num_bits_find
    lda #$00
    sta actc_real_const_num_bits
    sta actc_real_const_num_bits+1
    rts
actc_real_const_big_num_bits_byte:
    jsr actc_real_const_big_bits_from_xa
    sta actc_real_const_num_bits
    sty actc_real_const_num_bits+1
    rts
actc_real_const_big_den_bits:
    ldx #(ACTC_REAL_CONST_BIG_BYTES-1)
actc_real_const_big_den_bits_find:
    lda actc_real_const_big_den,x
    bne actc_real_const_big_den_bits_byte
    dex
    bpl actc_real_const_big_den_bits_find
    lda #$00
    sta actc_real_const_den_bits
    sta actc_real_const_den_bits+1
    rts
actc_real_const_big_den_bits_byte:
    jsr actc_real_const_big_bits_from_xa
    sta actc_real_const_den_bits
    sty actc_real_const_den_bits+1
    rts
actc_real_const_big_bits_from_xa:
    sta actc_real_const_digit
    txa
    asl a
    asl a
    asl a
    sta actc_real_const_word_value
    lda #$00
    rol a
    sta actc_real_const_word_value+1
    lda actc_real_const_digit
    ldx #$08
actc_real_const_big_bits_from_xa_loop:
    ora #$00
    bmi actc_real_const_big_bits_from_xa_ready
    asl a
    dex
    bne actc_real_const_big_bits_from_xa_loop
actc_real_const_big_bits_from_xa_ready:
    txa
    clc
    adc actc_real_const_word_value
    sta actc_real_const_word_value
    lda actc_real_const_word_value+1
    adc #$00
    tay
    lda actc_real_const_word_value
    rts

actc_real_const_big_compare_num_work:
    ldx #(ACTC_REAL_CONST_BIG_BYTES-1)
actc_real_const_big_compare_num_work_loop:
    lda actc_real_const_big_num,x
    cmp actc_real_const_big_work,x
    bne actc_real_const_big_compare_done
    dex
    bpl actc_real_const_big_compare_num_work_loop
    lda #$00
    sec
    rts
actc_real_const_big_compare_work_den:
    ldx #(ACTC_REAL_CONST_BIG_BYTES-1)
actc_real_const_big_compare_work_den_loop:
    lda actc_real_const_big_work,x
    cmp actc_real_const_big_den,x
    bne actc_real_const_big_compare_done
    dex
    bpl actc_real_const_big_compare_work_den_loop
    lda #$00
    sec
    rts
actc_real_const_big_compare_num_den:
    ldx #(ACTC_REAL_CONST_BIG_BYTES-1)
actc_real_const_big_compare_num_den_loop:
    lda actc_real_const_big_num,x
    cmp actc_real_const_big_den,x
    bne actc_real_const_big_compare_done
    dex
    bpl actc_real_const_big_compare_num_den_loop
    lda #$00
    sec
    rts
actc_real_const_big_compare_num_divisor:
    ldx #(ACTC_REAL_CONST_BIG_BYTES-1)
actc_real_const_big_compare_num_divisor_loop:
    lda actc_real_const_big_num,x
    cmp actc_real_const_big_divisor,x
    bne actc_real_const_big_compare_done
    dex
    bpl actc_real_const_big_compare_num_divisor_loop
    lda #$00
    sec
actc_real_const_big_compare_done:
    rts

actc_real_const_big_subtract_divisor:
    sec
    ldx #$00
    ldy #ACTC_REAL_CONST_BIG_BYTES
actc_real_const_big_subtract_divisor_loop:
    lda actc_real_const_big_num,x
    sbc actc_real_const_big_divisor,x
    sta actc_real_const_big_num,x
    inx
    dey
    bne actc_real_const_big_subtract_divisor_loop
    rts

actc_real_const_big_divide:
    jsr actc_real_const_big_clear_quotient
    jsr actc_real_const_big_compare_num_den
    bcc actc_real_const_big_divide_done
    jsr actc_real_const_big_num_bits
    jsr actc_real_const_big_den_bits
    sec
    lda actc_real_const_num_bits
    sbc actc_real_const_den_bits
    sta actc_real_const_div_bit
    lda actc_real_const_num_bits+1
    sbc actc_real_const_den_bits+1
    bne actc_real_const_big_divide_fail
    lda actc_real_const_div_bit
    cmp #32
    bcs actc_real_const_big_divide_fail
    jsr actc_real_const_big_copy_den_to_divisor
    lda actc_real_const_div_bit
    sta actc_real_const_shift_count
    lda #$00
    sta actc_real_const_shift_count+1
actc_real_const_big_divide_shift_loop:
    jsr actc_real_const_shift_count_is_zero
    beq actc_real_const_big_divide_loop
    jsr actc_real_const_big_shift_divisor_left
    bcs actc_real_const_big_divide_fail
    jsr actc_real_const_dec_shift_count
    jmp actc_real_const_big_divide_shift_loop
actc_real_const_big_divide_loop:
    jsr actc_real_const_big_compare_num_divisor
    bcc actc_real_const_big_divide_next
    jsr actc_real_const_big_subtract_divisor
    ldx actc_real_const_div_bit
    lda actc_real_const_bit_masks,x
    pha
    txa
    lsr a
    lsr a
    lsr a
    tax
    pla
    ora actc_real_const_quotient,x
    sta actc_real_const_quotient,x
actc_real_const_big_divide_next:
    lda actc_real_const_div_bit
    beq actc_real_const_big_divide_done
    jsr actc_real_const_big_shift_divisor_right
    dec actc_real_const_div_bit
    jmp actc_real_const_big_divide_loop
actc_real_const_big_divide_done:
    clc
    rts
actc_real_const_big_divide_fail:
    sec
    rts

actc_real_const_round_quotient:
    jsr actc_real_const_big_copy_num_to_work
    jsr actc_real_const_big_shift_work_left
    bcs actc_real_const_round_up
    jsr actc_real_const_big_compare_work_den
    bcc actc_real_const_round_done
    bne actc_real_const_round_up
    lda actc_real_const_quotient
    and #$01
    beq actc_real_const_round_done
actc_real_const_round_up:
    inc actc_real_const_quotient
    bne actc_real_const_round_done
    inc actc_real_const_quotient+1
    bne actc_real_const_round_done
    inc actc_real_const_quotient+2
    bne actc_real_const_round_done
    inc actc_real_const_quotient+3
    beq actc_real_const_round_fail
actc_real_const_round_done:
    clc
    rts
actc_real_const_round_fail:
    sec
    rts

actc_real_const_loop_count_is_zero:
    lda actc_real_const_loop_count
    ora actc_real_const_loop_count+1
    rts
actc_real_const_shift_count_is_zero:
    lda actc_real_const_shift_count
    ora actc_real_const_shift_count+1
    rts
actc_real_const_dec_loop_count:
    sec
    lda actc_real_const_loop_count
    sbc #$01
    sta actc_real_const_loop_count
    lda actc_real_const_loop_count+1
    sbc #$00
    sta actc_real_const_loop_count+1
    rts
actc_real_const_dec_shift_count:
    sec
    lda actc_real_const_shift_count
    sbc #$01
    sta actc_real_const_shift_count
    lda actc_real_const_shift_count+1
    sbc #$00
    sta actc_real_const_shift_count+1
    rts

actc_real_const_word_realbits:
    .asciiz "REALBITS"
actc_real_const_word_real:
    .asciiz "REAL"
actc_real_const_word_fabs:
    .asciiz "FABS"
actc_real_const_word_fsqrt:
    .asciiz "FSQRT"
actc_real_const_word_nan:
    .asciiz "NAN"
actc_real_const_word_inf:
    .asciiz "INF"
actc_real_const_word_infinity:
    .asciiz "INFINITY"
actc_real_const_canonical_prefix:
    .asciiz "REALBITS($"
actc_real_const_bit_masks:
    .byte $01,$02,$04,$08,$10,$20,$40,$80
    .byte $01,$02,$04,$08,$10,$20,$40,$80
    .byte $01,$02,$04,$08,$10,$20,$40,$80
    .byte $01,$02,$04,$08,$10,$20,$40,$80

.segment "BSS"
actc_real_const_input_ptr:
    .res 2
actc_real_const_saved_scan_ptr:
    .res 2
actc_real_const_saved_const_ptr:
    .res 2
actc_real_const_saved_runtime_zp:
    .res $1E
actc_real_const_scan:
    .res 1
actc_real_const_acc:
    .res 4
actc_real_const_lhs:
    .res 4
actc_real_const_value_depth:
    .res 1
actc_real_const_value_stack:
    .res 4 * ACTC_REAL_CONST_VALUE_STACK_MAX
actc_real_const_expected_char:
    .res 1
actc_real_const_operator:
    .res 1
actc_real_const_word_value:
    .res 2
actc_real_const_digit_count:
    .res 1
actc_real_const_digit:
    .res 1
actc_real_const_number_base:
    .res 1
actc_real_const_number_significant:
    .res 1
actc_real_const_significant_digits:
    .res 1
actc_real_const_fraction_digits:
    .res 1
actc_real_const_decimal_seen:
    .res 1
actc_real_const_digit_seen:
    .res 1
actc_real_const_explicit_negative:
    .res 1
actc_real_const_explicit_exp:
    .res 2
actc_real_const_exp10:
    .res 2
actc_real_const_decimal_order:
    .res 2
actc_real_const_loop_count:
    .res 2
actc_real_const_shift_count:
    .res 2
actc_real_const_num_bits:
    .res 2
actc_real_const_den_bits:
    .res 2
actc_real_const_e2:
    .res 2
actc_real_const_scale:
    .res 2
actc_real_const_normal:
    .res 1
actc_real_const_biased_exp:
    .res 1
actc_real_const_small_count:
    .res 1
actc_real_const_div_bit:
    .res 1
actc_real_const_quotient:
    .res 4
actc_real_const_big_num:
    .res ACTC_REAL_CONST_BIG_BYTES
actc_real_const_big_den:
    .res ACTC_REAL_CONST_BIG_BYTES
actc_real_const_big_work:
    .res ACTC_REAL_CONST_BIG_BYTES
actc_real_const_big_divisor:
    .res ACTC_REAL_CONST_BIG_BYTES

.segment "CODE"
