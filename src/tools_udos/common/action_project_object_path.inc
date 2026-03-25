build_object_target_path:
    lda #'O'
    sta target_path+0
    lda #'B'
    sta target_path+1
    lda #'J'
    sta target_path+2
    lda #'/'
    sta target_path+3
    ldy #$00
build_object_target_path_loop:
    lda module_name,y
    beq build_object_target_path_suffix
    sta target_path+4,y
    iny
    bne build_object_target_path_loop
build_object_target_path_suffix:
    lda #'.'
    sta target_path+4,y
    iny
    lda #'A'
    sta target_path+4,y
    iny
    lda #'V'
    sta target_path+4,y
    iny
    lda #'O'
    sta target_path+4,y
    iny
    lda #$00
    sta target_path+4,y
    rts
