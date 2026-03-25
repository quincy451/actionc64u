build_target_path:
    lda #'S'
    sta target_path+0
    lda #'R'
    sta target_path+1
    lda #'C'
    sta target_path+2
    lda #'/'
    sta target_path+3
    ldy #$00
build_target_path_loop:
    lda manifest_entry,y
    sta target_path+4,y
    beq build_target_path_done
    iny
    bne build_target_path_loop
build_target_path_done:
    rts

probe_target_path:
    lda #<target_path
    sta file_params+0
    lda #>target_path
    sta file_params+1
    lda #$00
    sta file_params+2
    sta file_params+3
    sta file_params+4
    sta file_params+5
    sta file_params+6
    sta file_params+7
    sta file_params+8
    ldx #file_params
    jmp svc_file_load_sc0

delete_target_path:
    lda #<target_path
    sta file_params+0
    lda #>target_path
    sta file_params+1
    lda #tool_file_status_fail
    sta file_params+2
    ldx #file_params
    jmp svc_file_delete_sc0
