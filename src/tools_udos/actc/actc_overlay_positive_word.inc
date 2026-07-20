; Shared token-driven positive-word parser for the body overlays. Resident
; SourceReader owns token caching and complete cross-window token scans.

parse_positive_word_sum_local_or_fail:
    jsr positive_word_skip_inline_spaces_local
    jsr parse_positive_word_term_local_or_fail
    bcc :+
    sec
    rts
:   lda positive_word_value_lo_local
    sta positive_word_sum_lo_local
    lda positive_word_value_hi_local
    sta positive_word_sum_hi_local
parse_positive_word_sum_local_loop:
    jsr positive_word_skip_inline_spaces_local
    jsr positive_word_peek_token_local
    bcs parse_positive_word_sum_local_fail
    jsr positive_word_token_is_sum_stop_local
    bcs :+
    jmp parse_positive_word_sum_local_done
:
    cmp #'+'
    beq parse_positive_word_sum_local_add
    cmp #'-'
    beq parse_positive_word_sum_local_sub
parse_positive_word_sum_local_fail:
    sec
    rts

parse_positive_word_sum_local_add:
    jsr positive_word_consume_token_local
    bcs parse_positive_word_sum_local_fail
    lda positive_word_sum_hi_local
    pha
    lda positive_word_sum_lo_local
    pha
    jsr parse_positive_word_term_local_or_fail
    bcs parse_positive_word_sum_local_pop_fail
    lda positive_word_value_lo_local
    sta positive_word_temp_lo_local
    lda positive_word_value_hi_local
    sta positive_word_temp_hi_local
    pla
    sta positive_word_sum_lo_local
    pla
    sta positive_word_sum_hi_local
    clc
    lda positive_word_sum_lo_local
    adc positive_word_temp_lo_local
    sta positive_word_sum_lo_local
    lda positive_word_sum_hi_local
    adc positive_word_temp_hi_local
    sta positive_word_sum_hi_local
    bcc parse_positive_word_sum_local_loop
    sec
    rts

parse_positive_word_sum_local_sub:
    jsr positive_word_consume_token_local
    bcs parse_positive_word_sum_local_fail
    lda positive_word_sum_hi_local
    pha
    lda positive_word_sum_lo_local
    pha
    jsr parse_positive_word_term_local_or_fail
    bcs parse_positive_word_sum_local_pop_fail
    lda positive_word_value_lo_local
    sta positive_word_temp_lo_local
    lda positive_word_value_hi_local
    sta positive_word_temp_hi_local
    pla
    sta positive_word_sum_lo_local
    pla
    sta positive_word_sum_hi_local
    lda positive_word_sum_lo_local
    sec
    sbc positive_word_temp_lo_local
    sta positive_word_sum_lo_local
    lda positive_word_sum_hi_local
    sbc positive_word_temp_hi_local
    sta positive_word_sum_hi_local
    bcc :+
    jmp parse_positive_word_sum_local_loop
:
    sec
    rts

parse_positive_word_sum_local_pop_fail:
    pla
    pla
    sec
    rts

parse_positive_word_sum_local_done:
    lda positive_word_sum_lo_local
    sta positive_word_value_lo_local
    lda positive_word_sum_hi_local
    sta positive_word_value_hi_local
    jmp positive_word_store_expr_value_local

parse_positive_word_term_local_or_fail:
    jsr positive_word_skip_inline_spaces_local
    jsr parse_positive_word_factor_local_or_fail
    bcc :+
    sec
    rts
:   lda positive_word_value_lo_local
    sta positive_word_term_lo_local
    lda positive_word_value_hi_local
    sta positive_word_term_hi_local
parse_positive_word_term_local_loop:
    jsr positive_word_skip_inline_spaces_local
    jsr positive_word_peek_token_local
    bcc :+
    jmp parse_positive_word_term_local_fail
:
    cmp #'*'
    beq parse_positive_word_term_local_mul
    cmp #'/'
    beq parse_positive_word_term_local_div
    lda positive_word_term_lo_local
    sta positive_word_value_lo_local
    lda positive_word_term_hi_local
    sta positive_word_value_hi_local
    clc
    rts

parse_positive_word_term_local_mul:
    jsr positive_word_consume_token_local
    bcc :+
    jmp parse_positive_word_term_local_fail
:
    lda positive_word_term_hi_local
    pha
    lda positive_word_term_lo_local
    pha
    jsr parse_positive_word_factor_local_or_fail
    bcc :+
    jmp parse_positive_word_term_local_pop_fail
:
    lda positive_word_value_lo_local
    sta positive_word_temp_lo_local
    lda positive_word_value_hi_local
    sta positive_word_temp_hi_local
    pla
    sta positive_word_term_saved_lo_local
    pla
    sta positive_word_term_saved_hi_local
    lda #$00
    sta positive_word_term_lo_local
    sta positive_word_term_hi_local
parse_positive_word_term_local_mul_loop:
    lda positive_word_temp_lo_local
    ora positive_word_temp_hi_local
    beq parse_positive_word_term_local_loop
    clc
    lda positive_word_term_lo_local
    adc positive_word_term_saved_lo_local
    sta positive_word_term_lo_local
    lda positive_word_term_hi_local
    adc positive_word_term_saved_hi_local
    sta positive_word_term_hi_local
    bcs parse_positive_word_term_local_fail
    lda positive_word_temp_lo_local
    sec
    sbc #$01
    sta positive_word_temp_lo_local
    lda positive_word_temp_hi_local
    sbc #$00
    sta positive_word_temp_hi_local
    jmp parse_positive_word_term_local_mul_loop

parse_positive_word_term_local_div:
    jsr positive_word_consume_token_local
    bcs parse_positive_word_term_local_fail
    lda positive_word_term_hi_local
    pha
    lda positive_word_term_lo_local
    pha
    jsr parse_positive_word_factor_local_or_fail
    bcs parse_positive_word_term_local_pop_fail
    lda positive_word_value_lo_local
    ora positive_word_value_hi_local
    beq parse_positive_word_term_local_pop_fail
    lda positive_word_value_lo_local
    sta positive_word_temp_lo_local
    lda positive_word_value_hi_local
    sta positive_word_temp_hi_local
    pla
    sta positive_word_term_saved_lo_local
    pla
    sta positive_word_term_saved_hi_local
    lda #$00
    sta positive_word_term_lo_local
    sta positive_word_term_hi_local
parse_positive_word_term_local_div_loop:
    lda positive_word_term_saved_hi_local
    cmp positive_word_temp_hi_local
    bcc parse_positive_word_term_local_div_done
    bne :+
    lda positive_word_term_saved_lo_local
    cmp positive_word_temp_lo_local
    bcc parse_positive_word_term_local_div_done
:   lda positive_word_term_saved_lo_local
    sec
    sbc positive_word_temp_lo_local
    sta positive_word_term_saved_lo_local
    lda positive_word_term_saved_hi_local
    sbc positive_word_temp_hi_local
    sta positive_word_term_saved_hi_local
    inc positive_word_term_lo_local
    bne parse_positive_word_term_local_div_loop
    inc positive_word_term_hi_local
    bne parse_positive_word_term_local_div_loop
parse_positive_word_term_local_div_done:
    jmp parse_positive_word_term_local_loop

parse_positive_word_term_local_pop_fail:
    pla
    pla
parse_positive_word_term_local_fail:
    sec
    rts

parse_positive_word_factor_local_or_fail:
    jsr positive_word_skip_inline_spaces_local
    jsr positive_word_peek_token_local
    bcs parse_positive_word_term_local_fail
    cmp #'('
    beq parse_positive_word_factor_local_group
    cmp #SOURCE_TOKEN_SYMBOL
    beq parse_positive_word_factor_local_symbol
    cmp #SOURCE_TOKEN_DECIMAL
    beq parse_positive_word_factor_local_decimal
    sec
    rts

parse_positive_word_factor_local_symbol:
    lda #ACTC_OVERLAY_CTX_FIND_BUILTIN_CONSTANT_FN_LO
    jsr call_context_function
    bcs parse_positive_word_term_local_fail
    jmp positive_word_load_expr_value_local

parse_positive_word_factor_local_decimal:
    jsr positive_word_load_token_value_local
    jsr positive_word_consume_token_local
    bcs parse_positive_word_term_local_fail
    clc
    rts

parse_positive_word_factor_local_group:
    jsr positive_word_consume_token_local
    bcs parse_positive_word_term_local_fail
    jsr parse_positive_word_sum_local_or_fail
    bcs parse_positive_word_term_local_fail
    jsr positive_word_skip_inline_spaces_local
    jsr positive_word_peek_token_local
    bcs parse_positive_word_term_local_fail
    cmp #')'
    bne parse_positive_word_term_local_fail
    jsr positive_word_consume_token_local
    bcs parse_positive_word_term_local_fail
    clc
    rts

parse_optional_grouped_positive_word_sum_local_or_fail:
    jsr positive_word_skip_inline_spaces_local
    jsr positive_word_peek_token_local
    bcs parse_optional_grouped_positive_word_sum_local_fail
    cmp #'('
    beq :+
    jmp parse_positive_word_sum_local_or_fail
:   jsr positive_word_consume_token_local
    bcs parse_optional_grouped_positive_word_sum_local_fail
    jsr parse_positive_word_sum_local_or_fail
    bcs parse_optional_grouped_positive_word_sum_local_fail
    jsr positive_word_skip_inline_spaces_local
    jsr positive_word_peek_token_local
    bcs parse_optional_grouped_positive_word_sum_local_fail
    cmp #')'
    bne parse_optional_grouped_positive_word_sum_local_fail
    jsr positive_word_consume_token_local
    bcs parse_optional_grouped_positive_word_sum_local_fail
    clc
    rts
parse_optional_grouped_positive_word_sum_local_fail:
    sec
    rts

positive_word_skip_inline_spaces_local:
    lda #ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    jmp call_context_function

positive_word_peek_token_local:
    lda #ACTC_OVERLAY_CTX_SOURCE_READER_PEEK_TOKEN_FN_LO
    jmp call_context_function

positive_word_consume_token_local:
    lda #ACTC_OVERLAY_CTX_SOURCE_READER_CONSUME_TOKEN_FN_LO
    jmp call_context_function

positive_word_load_token_value_local:
    sty positive_word_source_y_local
    lda #ACTC_OVERLAY_CTX_SOURCE_READER_TOKEN_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta positive_word_value_lo_local
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta positive_word_value_hi_local
    ldy positive_word_source_y_local
    clc
    rts

positive_word_load_expr_value_local:
    sty positive_word_source_y_local
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta positive_word_value_lo_local
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta positive_word_value_hi_local
    ldy positive_word_source_y_local
    clc
    rts

positive_word_store_expr_value_local:
    sty positive_word_source_y_local
    lda #ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda positive_word_value_lo_local
    sta (ACTC_OVERLAY_WORK_ZP),y
    iny
    lda positive_word_value_hi_local
    sta (ACTC_OVERLAY_WORK_ZP),y
    ldy positive_word_source_y_local
    clc
    rts

positive_word_token_is_sum_stop_local:
    cmp #SOURCE_TOKEN_EOF
    beq positive_word_token_is_sum_stop_local_yes
    cmp #SOURCE_TOKEN_LINE_END
    beq positive_word_token_is_sum_stop_local_yes
    cmp #','
    beq positive_word_token_is_sum_stop_local_yes
    cmp #')'
    beq positive_word_token_is_sum_stop_local_yes
    cmp #']'
    beq positive_word_token_is_sum_stop_local_yes
    cmp #SOURCE_TOKEN_EQ
    beq positive_word_token_is_sum_stop_local_yes
    cmp #SOURCE_TOKEN_LT
    beq positive_word_token_is_sum_stop_local_yes
    cmp #SOURCE_TOKEN_GT
    beq positive_word_token_is_sum_stop_local_yes
    cmp #SOURCE_TOKEN_LE
    beq positive_word_token_is_sum_stop_local_yes
    cmp #SOURCE_TOKEN_GE
    beq positive_word_token_is_sum_stop_local_yes
    cmp #SOURCE_TOKEN_NE
    beq positive_word_token_is_sum_stop_local_yes
    sec
    rts
positive_word_token_is_sum_stop_local_yes:
    clc
    rts

positive_word_value_lo_local:
    .byte $00
positive_word_value_hi_local:
    .byte $00
positive_word_sum_lo_local:
    .byte $00
positive_word_sum_hi_local:
    .byte $00
positive_word_term_lo_local:
    .byte $00
positive_word_term_hi_local:
    .byte $00
positive_word_term_saved_lo_local:
    .byte $00
positive_word_term_saved_hi_local:
    .byte $00
positive_word_temp_lo_local:
    .byte $00
positive_word_temp_hi_local:
    .byte $00
positive_word_source_y_local:
    .byte $00
