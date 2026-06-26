save_content_buffer_to_target:
    lda #<target_path
    sta save_params+0
    lda #>target_path
    sta save_params+1
    lda #<content_buffer
    sta save_params+2
    lda #>content_buffer
    sta save_params+3
    lda save_params+2
    sta svc_retptr
    lda save_params+3
    sta svc_retptr+1
.ifdef ACTION_PROJECT_SAVE_TREE_ONLY
    lda #$00
    sta save_params+4
    sta save_params+5
.else
    lda #$00
    sta save_params+4
    sta save_params+5
save_content_buffer_len_loop:
    ldy #$00
    lda (svc_retptr),y
    beq save_content_buffer_len_done
    inc svc_retptr
    bne :+
    inc svc_retptr+1
:
    inc save_params+4
    bne save_content_buffer_len_loop
    inc save_params+5
    bne save_content_buffer_len_loop
save_content_buffer_len_done:
.endif
    lda #tool_file_status_fail
    sta save_params+6
    ldx #save_params
.ifdef ACTADD_PRESERVE_ZP_SERVICES
    jsr actadd_svc_file_save_sc0
.else
    jsr svc_file_save_sc0
.endif
    lda save_params+6
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
