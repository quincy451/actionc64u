build_map_target_path:
    lda #'B'
    sta target_path+0
    lda #'I'
    sta target_path+1
    lda #'N'
    sta target_path+2
    lda #'/'
    sta target_path+3
    ldy #$00
build_map_target_path_loop:
    lda module_name,y
    beq build_map_target_path_suffix
    sta target_path+4,y
    iny
    bne build_map_target_path_loop
build_map_target_path_suffix:
    lda #'.'
    sta target_path+4,y
    iny
    lda #'M'
    sta target_path+4,y
    iny
    lda #'A'
    sta target_path+4,y
    iny
    lda #'P'
    sta target_path+4,y
    iny
    lda #$00
    sta target_path+4,y
    rts
