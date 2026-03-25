probe_target_save_mode_or_fail:
    jsr probe_target_path
    lda file_params+6
    cmp #tool_file_status_nofile
    beq probe_target_save_mode_create
    cmp #tool_file_status_ok
    beq probe_target_save_mode_update
    cmp #tool_file_status_too_large
    beq probe_target_save_mode_update
    lda #<msg_probe_fail
    ldy #>msg_probe_fail
    jmp fail_with_ptr
probe_target_save_mode_create:
    lda #$01
    sta save_mode
    rts
probe_target_save_mode_update:
    lda #$00
    sta save_mode
    rts

report_save_mode_result:
    lda save_mode
    beq report_save_mode_updated
    lda #<msg_created
    ldy #>msg_created
    jmp print_line_ptr
report_save_mode_updated:
    lda #<msg_updated
    ldy #>msg_updated
    jmp print_line_ptr
