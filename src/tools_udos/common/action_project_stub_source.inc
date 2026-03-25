build_module_stub_content:
    lda #'P'
    sta content_buffer+0
    lda #'R'
    sta content_buffer+1
    lda #'O'
    sta content_buffer+2
    lda #'C'
    sta content_buffer+3
    lda #' '
    sta content_buffer+4
    ldy #$00
build_module_stub_copy_name:
    lda module_name,y
    beq build_module_stub_suffix
    sta content_buffer+5,y
    iny
    bne build_module_stub_copy_name
build_module_stub_suffix:
    lda #'('
    sta content_buffer+5,y
    iny
    lda #')'
    sta content_buffer+5,y
    iny
    lda #13
    sta content_buffer+5,y
    iny
    lda #'E'
    sta content_buffer+5,y
    iny
    lda #'N'
    sta content_buffer+5,y
    iny
    lda #'D'
    sta content_buffer+5,y
    iny
    lda #'P'
    sta content_buffer+5,y
    iny
    lda #'R'
    sta content_buffer+5,y
    iny
    lda #'O'
    sta content_buffer+5,y
    iny
    lda #'C'
    sta content_buffer+5,y
    iny
    lda #13
    sta content_buffer+5,y
    iny
    lda #$00
    sta content_buffer+5,y
    rts
