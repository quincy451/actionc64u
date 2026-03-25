load_source_file:
    lda #$00
    sta truncated_flag
    lda #<target_path
    sta file_params+0
    lda #>target_path
    sta file_params+1
    lda #<source_buffer
    sta file_params+2
    lda #>source_buffer
    sta file_params+3
    lda #<SOURCE_LIMIT
    sta file_params+4
    lda #>SOURCE_LIMIT
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    sta file_params+8
    ldx #file_params
    jsr svc_file_load_sc0
    lda file_params+6
    cmp #tool_file_status_ok
    beq load_source_file_ok
    cmp #tool_file_status_too_large
    bne load_source_file_fail
    lda #$01
    sta truncated_flag
load_source_file_ok:
    ldy file_params+7
    lda #$00
    sta source_buffer,y
    clc
    rts
load_source_file_fail:
    sec
    rts
