; Canonicalize linked routine-address addends before the nearly full
; declaration overlay sees them. One side of the top-level plus must be a bare
; routine name; the other uses the checked signed 64-bit CONST evaluator and is
; reduced to the signed 16-bit literal form already stored by pass 2.

preprocess_canonicalize_routine_address:
    lda #$00
    sta preprocess_line_scan
    jsr preprocess_line_skip_spaces
    lda #<preprocess_routine_keyword_proc
    ldy #>preprocess_routine_keyword_proc
    jsr preprocess_const_match_line_word
    bcc preprocess_routine_have_prefix
    lda #<preprocess_const_keyword_byte
    ldy #>preprocess_const_keyword_byte
    jsr preprocess_const_match_line_word
    bcc preprocess_routine_have_type
    lda #<preprocess_const_keyword_card
    ldy #>preprocess_const_keyword_card
    jsr preprocess_const_match_line_word
    bcc preprocess_routine_have_type
    lda #<preprocess_const_keyword_int
    ldy #>preprocess_const_keyword_int
    jsr preprocess_const_match_line_word
    bcc :+
    jmp preprocess_routine_unchanged
:
preprocess_routine_have_type:
    jsr preprocess_line_skip_spaces
    lda #<preprocess_routine_keyword_func
    ldy #>preprocess_routine_keyword_func
    jsr preprocess_const_match_line_word
    bcc :+
    jmp preprocess_routine_unchanged
:
preprocess_routine_have_prefix:
    jsr preprocess_line_skip_spaces
    jsr preprocess_parse_define_name
    bcc :+
    jmp preprocess_routine_unchanged
:
    jsr preprocess_line_skip_spaces
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    cmp #'='
    beq :+
    jmp preprocess_routine_unchanged
:
    inc preprocess_line_scan
    jsr preprocess_line_skip_spaces
    lda preprocess_line_scan
    sta preprocess_expand_token_start
    lda #$00
    sta preprocess_expand_saved_char
    lda #$FF
    sta preprocess_expand_scan
    sta preprocess_expand_copy_index

; The last opening parenthesis at depth zero begins the parameter list. A plus
; inside a grouped constant expression is not the symbol/addend separator.
preprocess_routine_scan_expression:
    ldy preprocess_line_scan
    cpy preprocess_line_len
    bcs preprocess_routine_expression_ready
    lda preprocess_line_a,y
    cmp #';'
    beq preprocess_routine_expression_ready
    cmp #'('
    beq preprocess_routine_open
    cmp #')'
    beq preprocess_routine_close
    cmp #'+'
    bne preprocess_routine_scan_next
    lda preprocess_expand_saved_char
    bne preprocess_routine_scan_next
    lda preprocess_expand_scan
    cmp #$FF
    bne preprocess_routine_scan_next
    sty preprocess_expand_scan
    jmp preprocess_routine_scan_next
preprocess_routine_open:
    lda preprocess_expand_saved_char
    bne :+
    sty preprocess_expand_copy_index
:
    inc preprocess_expand_saved_char
    bne preprocess_routine_scan_next
    jmp preprocess_routine_unchanged
preprocess_routine_close:
    lda preprocess_expand_saved_char
    beq preprocess_routine_scan_next
    dec preprocess_expand_saved_char
preprocess_routine_scan_next:
    inc preprocess_line_scan
    bne preprocess_routine_scan_expression

preprocess_routine_expression_ready:
    lda preprocess_expand_copy_index
    cmp #$FF
    bne :+
    jmp preprocess_routine_unchanged
:
    lda preprocess_expand_scan
    cmp #$FF
    beq preprocess_routine_numeric_expression
    cmp preprocess_expand_copy_index
    bcc :+
    jmp preprocess_routine_numeric_expression
:
    lda preprocess_expand_token_start
    sta preprocess_emit_index
    lda preprocess_expand_scan
    sta preprocess_expected_char
    jsr preprocess_routine_copy_symbol_range
    bcc preprocess_routine_symbol_left
    lda preprocess_expand_scan
    clc
    adc #$01
    sta preprocess_emit_index
    lda preprocess_expand_copy_index
    sta preprocess_expected_char
    jsr preprocess_routine_copy_symbol_range
    bcc :+
    jmp preprocess_routine_numeric_expression
:
    lda preprocess_expand_token_start
    sta preprocess_emit_index
    lda preprocess_expand_scan
    sta preprocess_expected_char
    jmp preprocess_routine_linked_expression
preprocess_routine_symbol_left:
    lda preprocess_expand_scan
    clc
    adc #$01
    sta preprocess_emit_index
    lda preprocess_expand_copy_index
    sta preprocess_expected_char

preprocess_routine_linked_expression:
    lda #$01
    sta preprocess_expand_saved_char
    lda #PREPROCESS_CONST_INT
    sta preprocess_const_type
    jmp preprocess_routine_evaluate_addend

preprocess_routine_numeric_expression:
    lda #$00
    sta preprocess_expand_saved_char
    lda #PREPROCESS_CONST_CARD
    sta preprocess_const_type
    lda preprocess_expand_token_start
    sta preprocess_emit_index
    lda preprocess_expand_copy_index
    sta preprocess_expected_char

preprocess_routine_evaluate_addend:
    ldx #$00
    ldy preprocess_emit_index
preprocess_routine_copy_addend:
    cpy preprocess_expected_char
    bcs preprocess_routine_addend_ready
    cpx #(PREPROCESS_DEFINE_VALUE_SIZE - 1)
    bcc :+
    jmp preprocess_routine_too_long
:
    lda preprocess_line_a,y
    sta preprocess_value_temp,x
    inx
    iny
    bne preprocess_routine_copy_addend
preprocess_routine_addend_ready:
    lda #$00
    sta preprocess_value_temp,x
    stx preprocess_value_len
    jsr preprocess_const_eval_integer
    bcc preprocess_routine_evaluate_ok
    lda preprocess_expand_saved_char
    beq preprocess_routine_evaluate_unchanged
    jmp preprocess_routine_bad_address
preprocess_routine_evaluate_unchanged:
    jmp preprocess_routine_unchanged
preprocess_routine_evaluate_ok:

    ldx #$00
    ldy #$00
preprocess_routine_copy_prefix:
    cpy preprocess_expand_token_start
    bcs preprocess_routine_copy_target
    lda preprocess_line_a,y
    sta preprocess_line_b,x
    inx
    iny
    bne preprocess_routine_copy_prefix
preprocess_routine_copy_target:
    lda preprocess_expand_saved_char
    beq preprocess_routine_copy_value_start
    ldy #$00
preprocess_routine_copy_target_loop:
    lda preprocess_const_name_temp,y
    beq preprocess_routine_copy_plus
    cpx #$FE
    bcc :+
    jmp preprocess_routine_too_long
:
    sta preprocess_line_b,x
    inx
    iny
    bne preprocess_routine_copy_target_loop
preprocess_routine_copy_plus:
    cpx #$FE
    bcc :+
    jmp preprocess_routine_too_long
:
    lda #'+'
    sta preprocess_line_b,x
    inx
preprocess_routine_copy_value_start:
    ldy #$00
preprocess_routine_copy_value:
    lda preprocess_value_temp,y
    beq preprocess_routine_copy_suffix_start
    cpx #$FE
    bcc :+
    jmp preprocess_routine_too_long
:
    sta preprocess_line_b,x
    inx
    iny
    bne preprocess_routine_copy_value
preprocess_routine_copy_suffix_start:
    ldy preprocess_expand_copy_index
preprocess_routine_copy_suffix:
    cpy preprocess_line_len
    bcs preprocess_routine_publish
    cpx #$FE
    bcs preprocess_routine_too_long
    lda preprocess_line_a,y
    sta preprocess_line_b,x
    inx
    iny
    bne preprocess_routine_copy_suffix
preprocess_routine_publish:
    lda #$00
    sta preprocess_line_b,x
    stx preprocess_expanded_len
    lda #<preprocess_line_b
    sta preprocess_expanded_ptr
    lda #>preprocess_line_b
    sta preprocess_expanded_ptr+1
    lda #$01
    sta preprocess_source_changed
preprocess_routine_unchanged:
    clc
    rts

; Match a trimmed bare symbol in [emit_index, expected_char), preserving it in
; const_name_temp while the evaluator uses name_temp as scratch.
preprocess_routine_copy_symbol_range:
    lda preprocess_emit_index
    sta preprocess_line_scan
    jsr preprocess_line_skip_spaces
    jsr preprocess_parse_define_name
    bcs preprocess_routine_symbol_fail
    jsr preprocess_line_skip_spaces
    lda preprocess_line_scan
    cmp preprocess_expected_char
    bne preprocess_routine_symbol_fail
    ldy #$00
preprocess_routine_save_symbol:
    lda preprocess_name_temp,y
    sta preprocess_const_name_temp,y
    beq preprocess_routine_symbol_ok
    iny
    cpy #PREPROCESS_DEFINE_NAME_SIZE
    bcc preprocess_routine_save_symbol
preprocess_routine_symbol_fail:
    sec
    rts
preprocess_routine_symbol_ok:
    clc
    rts

preprocess_routine_too_long:
    lda #<preprocess_msg_expand_long
    ldy #>preprocess_msg_expand_long
    jsr preprocess_set_diag
    sec
    rts
preprocess_routine_bad_address:
    lda #<preprocess_routine_msg_bad_address
    ldy #>preprocess_routine_msg_bad_address
    jsr preprocess_set_diag
    sec
    rts

preprocess_routine_keyword_proc:
    .asciiz "PROC"
preprocess_routine_keyword_func:
    .asciiz "FUNC"
preprocess_routine_msg_bad_address:
    .asciiz "ROUTINE ADDRESS"
