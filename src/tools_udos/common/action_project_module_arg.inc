copy_module_arg:
    ldy #$00
    ldx #$00
copy_module_arg_loop:
    lda (src_ptr),y
    beq copy_module_arg_done
    cmp #' '
    beq copy_module_arg_done
    cmp #'.'
    beq copy_module_arg_extension
    cpx #24
    bcs copy_module_arg_fail
    jsr normalize_module_arg_char
    sta module_name,x
    inx
    iny
    bne copy_module_arg_loop
copy_module_arg_extension:
    iny
    lda (src_ptr),y
    jsr normalize_module_arg_char
    cmp #'A'
    bne copy_module_arg_fail
    iny
    lda (src_ptr),y
    jsr normalize_module_arg_char
    cmp #'C'
    bne copy_module_arg_fail
    iny
    lda (src_ptr),y
    jsr normalize_module_arg_char
    cmp #'T'
    bne copy_module_arg_fail
    iny
    lda (src_ptr),y
    beq copy_module_arg_done
    cmp #' '
    bne copy_module_arg_fail
copy_module_arg_done:
    cpx #$00
    beq copy_module_arg_fail
    lda #$00
    sta module_name,x
    clc
    rts
copy_module_arg_fail:
    sec
    rts

normalize_module_arg_char:
    cmp #$01
    bcc normalize_module_arg_ascii
    cmp #$1B
    bcs normalize_module_arg_ascii
    clc
    adc #$40
    rts
normalize_module_arg_ascii:
    cmp #'a'
    bcc :+
    cmp #'z'+1
    bcs :+
    and #$DF
:    
    rts
