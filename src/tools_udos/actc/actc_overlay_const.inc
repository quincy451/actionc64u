; Typed constants share the bounded DEFINE table. Integer declarations are
; reduced to canonical text and then removed, so no OBJ storage is allocated.

PREPROCESS_CONST_BYTE = $00
PREPROCESS_CONST_CARD = $01
PREPROCESS_CONST_INT = $02
PREPROCESS_CONST_REAL = $03

preprocess_prepare_expanded_line:
    jsr preprocess_expand_line
    bcs preprocess_prepare_expanded_line_fail
    lda preprocess_expanded_ptr
    cmp #<preprocess_line_a
    bne preprocess_prepare_expanded_line_copy
    lda preprocess_expanded_ptr+1
    cmp #>preprocess_line_a
    beq preprocess_prepare_expanded_line_publish
preprocess_prepare_expanded_line_copy:
    lda preprocess_expanded_ptr
    sta ACTC_OVERLAY_WORK_ZP
    lda preprocess_expanded_ptr+1
    sta ACTC_OVERLAY_WORK_ZP+1
    ldy #$00
preprocess_prepare_expanded_line_copy_loop:
    cpy preprocess_expanded_len
    bcs preprocess_prepare_expanded_line_copy_done
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta preprocess_line_a,y
    iny
    bne preprocess_prepare_expanded_line_copy_loop
preprocess_prepare_expanded_line_copy_done:
    lda #$00
    sta preprocess_line_a,y
preprocess_prepare_expanded_line_publish:
    lda preprocess_expanded_len
    sta preprocess_line_len
    lda #<preprocess_line_a
    sta preprocess_expanded_ptr
    lda #>preprocess_line_a
    sta preprocess_expanded_ptr+1
    clc
preprocess_prepare_expanded_line_fail:
    rts

; Carry clear identifies a typed CONST line and leaves line_scan at its first
; declarator. Carry set means this is an ordinary expanded source line.
preprocess_match_typed_const:
    lda #$00
    sta preprocess_line_scan
    jsr preprocess_line_skip_spaces
    lda #<preprocess_const_keyword_byte
    ldy #>preprocess_const_keyword_byte
    jsr preprocess_const_match_line_word
    bcs preprocess_match_const_try_char
    lda #PREPROCESS_CONST_BYTE
    jmp preprocess_match_const_have_type
preprocess_match_const_try_char:
    lda #<preprocess_const_keyword_char
    ldy #>preprocess_const_keyword_char
    jsr preprocess_const_match_line_word
    bcs preprocess_match_const_try_card
    lda #PREPROCESS_CONST_BYTE
    jmp preprocess_match_const_have_type
preprocess_match_const_try_card:
    lda #<preprocess_const_keyword_card
    ldy #>preprocess_const_keyword_card
    jsr preprocess_const_match_line_word
    bcs preprocess_match_const_try_int
    lda #PREPROCESS_CONST_CARD
    jmp preprocess_match_const_have_type
preprocess_match_const_try_int:
    lda #<preprocess_const_keyword_int
    ldy #>preprocess_const_keyword_int
    jsr preprocess_const_match_line_word
    bcs preprocess_match_const_try_real
    lda #PREPROCESS_CONST_INT
    jmp preprocess_match_const_have_type
preprocess_match_const_try_real:
    lda #<preprocess_const_keyword_real
    ldy #>preprocess_const_keyword_real
    jsr preprocess_const_match_line_word
    bcs preprocess_match_typed_const_fail
    lda #PREPROCESS_CONST_REAL
preprocess_match_const_have_type:
    sta preprocess_const_type
    jsr preprocess_line_skip_spaces
    lda #<preprocess_const_keyword_const
    ldy #>preprocess_const_keyword_const
    jsr preprocess_const_match_line_word
    bcs preprocess_match_typed_const_fail
    jsr preprocess_line_skip_spaces
    clc
    rts
preprocess_match_typed_const_fail:
    sec
    rts

preprocess_const_match_line_word:
    sta ACTC_OVERLAY_SCAN_ZP
    sty ACTC_OVERLAY_SCAN_ZP+1
    lda preprocess_line_scan
    pha
    ldx #$00
preprocess_const_match_line_word_loop:
    txa
    tay
    lda (ACTC_OVERLAY_SCAN_ZP),y
    beq preprocess_const_match_line_word_tail
    sta preprocess_expected_char
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    jsr uppercase_ascii
    cmp preprocess_expected_char
    bne preprocess_const_match_line_word_fail
    inc preprocess_line_scan
    inx
    bne preprocess_const_match_line_word_loop
preprocess_const_match_line_word_tail:
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    beq preprocess_const_match_line_word_ok
    cmp #' '
    beq preprocess_const_match_line_word_ok
    cmp #9
    beq preprocess_const_match_line_word_ok
preprocess_const_match_line_word_fail:
    pla
    sta preprocess_line_scan
    sec
    rts
preprocess_const_match_line_word_ok:
    pla
    clc
    rts

preprocess_parse_const_items:
    lda #$00
    sta preprocess_const_continues
preprocess_parse_const_items_loop:
    jsr preprocess_line_skip_spaces
    jsr preprocess_parse_define_name
    bcc :+
    jmp preprocess_bad_const
:
    ldy #$00
preprocess_const_save_name_loop:
    lda preprocess_name_temp,y
    sta preprocess_const_name_temp,y
    beq preprocess_const_name_saved
    iny
    cpy #PREPROCESS_DEFINE_NAME_SIZE
    bcc preprocess_const_save_name_loop
    jmp preprocess_bad_const
preprocess_const_name_saved:
    jsr preprocess_find_define
    bcs :+
    jmp preprocess_bad_const
:
    jsr preprocess_line_skip_spaces
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    cmp #'='
    beq :+
    jmp preprocess_bad_const
:
    inc preprocess_line_scan
    jsr preprocess_line_skip_spaces
    lda #$00
    sta preprocess_value_len
preprocess_const_copy_expr_loop:
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    beq preprocess_const_expr_ready
    cmp #';'
    beq preprocess_const_expr_ready
    cmp #','
    beq preprocess_const_expr_ready
    jsr preprocess_append_value_char
    bcc :+
    jmp preprocess_bad_const
:
    inc preprocess_line_scan
    jmp preprocess_const_copy_expr_loop
preprocess_const_expr_ready:
    jsr preprocess_trim_value_spaces
    lda preprocess_value_len
    beq preprocess_bad_const
    tax
    lda #$00
    sta preprocess_value_temp,x
    lda preprocess_const_type
    cmp #PREPROCESS_CONST_REAL
    bne preprocess_const_value_integer
    jsr preprocess_const_eval_real
    bcc :+
    jmp preprocess_bad_const
:
    sta preprocess_value_len
    jmp preprocess_const_value_ready
preprocess_const_value_integer:
    jsr preprocess_const_eval_integer
    bcs preprocess_bad_const_range
preprocess_const_value_ready:
    jsr preprocess_const_validate_builtin_redefinition
    bcc :+
    jmp preprocess_bad_const
:
    ldy #$00
preprocess_const_restore_name_loop:
    lda preprocess_const_name_temp,y
    sta preprocess_name_temp,y
    beq preprocess_const_name_restored
    iny
    cpy #PREPROCESS_DEFINE_NAME_SIZE
    bcc preprocess_const_restore_name_loop
    jmp preprocess_bad_const
preprocess_const_name_restored:
    jsr preprocess_store_define
    bcs preprocess_parse_const_items_fail
    jsr preprocess_line_skip_spaces
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    beq preprocess_parse_const_items_done
    cmp #';'
    beq preprocess_parse_const_items_done
    cmp #','
    bne preprocess_bad_const
    inc preprocess_line_scan
    jsr preprocess_line_skip_spaces
    ldy preprocess_line_scan
    lda preprocess_line_a,y
    beq preprocess_parse_const_items_continues
    cmp #';'
    beq preprocess_parse_const_items_continues
    jmp preprocess_parse_const_items_loop
preprocess_parse_const_items_continues:
    lda #$01
    sta preprocess_const_continues
preprocess_parse_const_items_done:
    clc
    rts
preprocess_parse_const_items_fail:
    rts

preprocess_bad_const_range:
    lda #<preprocess_msg_const_range
    ldy #>preprocess_msg_const_range
    jsr preprocess_set_diag
    sec
    rts
preprocess_bad_const:
    lda #<preprocess_msg_bad_const
    ldy #>preprocess_msg_bad_const
    jsr preprocess_set_diag
    sec
    rts

preprocess_const_eval_real:
    ldy #ACTC_OVERLAY_CTX_EVAL_REAL_CONST_FN_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta preprocess_const_eval_target
    iny
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta preprocess_const_eval_target+1
    lda preprocess_const_eval_target
    ora preprocess_const_eval_target+1
    beq preprocess_const_eval_real_fail
    sec
    lda preprocess_const_eval_target
    sbc #$01
    sta preprocess_const_eval_target_minus_one
    lda preprocess_const_eval_target+1
    sbc #$00
    pha
    lda preprocess_const_eval_target_minus_one
    pha
    lda #<preprocess_value_temp
    ldy #>preprocess_value_temp
    rts
preprocess_const_eval_real_fail:
    sec
    rts

.include "actc_overlay_const_expr.inc"

preprocess_const_skip_expr_spaces:
    ldy preprocess_const_expr_scan
    lda preprocess_value_temp,y
    cmp #' '
    beq :+
    cmp #9
    bne preprocess_const_skip_expr_spaces_done
:
    inc preprocess_const_expr_scan
    bne preprocess_const_skip_expr_spaces
preprocess_const_skip_expr_spaces_done:
    rts

preprocess_const_match_expr_word:
    sta ACTC_OVERLAY_SCAN_ZP
    sty ACTC_OVERLAY_SCAN_ZP+1
    lda preprocess_const_expr_scan
    pha
    ldx #$00
preprocess_const_match_expr_word_loop:
    txa
    tay
    lda (ACTC_OVERLAY_SCAN_ZP),y
    beq preprocess_const_match_expr_word_tail
    sta preprocess_expected_char
    ldy preprocess_const_expr_scan
    lda preprocess_value_temp,y
    jsr uppercase_ascii
    cmp preprocess_expected_char
    bne preprocess_const_match_expr_word_fail
    inc preprocess_const_expr_scan
    inx
    bne preprocess_const_match_expr_word_loop
preprocess_const_match_expr_word_tail:
    ldy preprocess_const_expr_scan
    lda preprocess_value_temp,y
    jsr uppercase_ascii
    jsr uppercase_symbol_body_valid
    bcc preprocess_const_match_expr_word_fail
    pla
    clc
    rts
preprocess_const_match_expr_word_fail:
    pla
    sta preprocess_const_expr_scan
    sec
    rts

; Canonical hexadecimal keeps substitutions compact. Signed INT uses a unary
; minus plus a positive magnitude, which native expression and raw parsers know.
preprocess_const_format_integer:
    lda #$00
    sta preprocess_value_len
    lda preprocess_const_type
    cmp #PREPROCESS_CONST_INT
    bne preprocess_const_format_magnitude
    lda preprocess_const_value_hi
    bpl preprocess_const_format_magnitude
    lda #'-'
    sta preprocess_value_temp
    inc preprocess_value_len
    lda preprocess_const_value_lo
    eor #$FF
    clc
    adc #$01
    sta preprocess_const_value_lo
    lda preprocess_const_value_hi
    eor #$FF
    adc #$00
    sta preprocess_const_value_hi
preprocess_const_format_magnitude:
    ldy preprocess_value_len
    lda #'$'
    sta preprocess_value_temp,y
    iny
    lda preprocess_const_value_hi
    lsr
    lsr
    lsr
    lsr
    jsr preprocess_const_format_nibble
    sta preprocess_value_temp,y
    iny
    lda preprocess_const_value_hi
    and #$0F
    jsr preprocess_const_format_nibble
    sta preprocess_value_temp,y
    iny
    lda preprocess_const_value_lo
    lsr
    lsr
    lsr
    lsr
    jsr preprocess_const_format_nibble
    sta preprocess_value_temp,y
    iny
    lda preprocess_const_value_lo
    and #$0F
    jsr preprocess_const_format_nibble
    sta preprocess_value_temp,y
    iny
    sty preprocess_value_len
    lda #$00
    sta preprocess_value_temp,y
    rts
preprocess_const_format_nibble:
    cmp #10
    bcc :+
    clc
    adc #('A'-10)
    rts
:
    clc
    adc #'0'
    rts

preprocess_const_keyword_byte:
    .asciiz "BYTE"
preprocess_const_keyword_char:
    .asciiz "CHAR"
preprocess_const_keyword_card:
    .asciiz "CARD"
preprocess_const_keyword_int:
    .asciiz "INT"
preprocess_const_keyword_real:
    .asciiz "REAL"
preprocess_const_keyword_const:
    .asciiz "CONST"
preprocess_const_keyword_lsh:
    .asciiz "LSH"
preprocess_const_keyword_rsh:
    .asciiz "RSH"
preprocess_const_keyword_mod:
    .asciiz "MOD"
preprocess_const_keyword_xor:
    .asciiz "XOR"
