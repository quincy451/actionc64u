save_content_buffer_to_target:
    lda #<target_path
    sta save_params+0
    lda #>target_path
    sta save_params+1
    lda #<content_buffer
    sta save_params+2
    lda #>content_buffer
    sta save_params+3
    lda #tool_file_status_fail
    sta save_params+4
    ldx #save_params
    jsr svc_file_save_sc0
    lda save_params+4
    cmp #tool_file_status_ok
    beq save_content_buffer_to_target_ok
    sec
    rts
save_content_buffer_to_target_ok:
    clc
    rts

save_stub_content_to_target_or_fail:
    jsr build_module_stub_content
    jsr save_content_buffer_to_target
    bcc save_stub_content_to_target_or_fail_done
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
save_stub_content_to_target_or_fail_done:
    rts
