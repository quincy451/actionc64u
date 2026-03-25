rename_old_target_or_fail:
    jsr rename_old_target_to_target
    cmp #tool_file_status_ok
    beq rename_old_target_or_fail_done
    cmp #tool_file_status_nofile
    bne :+
    lda #<msg_no_file
    ldy #>msg_no_file
    jmp fail_with_ptr
:   cmp #tool_file_status_exists
    bne :+
    lda #<msg_exists
    ldy #>msg_exists
    jmp fail_with_ptr
:   lda #<msg_ren_fail
    ldy #>msg_ren_fail
    jmp fail_with_ptr
rename_old_target_or_fail_done:
    rts

copy_old_target_or_fail:
    jsr copy_old_target_to_target
    cmp #tool_file_status_ok
    beq copy_old_target_or_fail_done
    cmp #tool_file_status_nofile
    bne :+
    lda #<msg_no_file
    ldy #>msg_no_file
    jmp fail_with_ptr
:   cmp #tool_file_status_exists
    bne :+
    lda #<msg_exists
    ldy #>msg_exists
    jmp fail_with_ptr
:   lda #<msg_copy_fail
    ldy #>msg_copy_fail
    jmp fail_with_ptr
copy_old_target_or_fail_done:
    rts
