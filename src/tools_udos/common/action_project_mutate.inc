append_manifest_entry:
    ldy #$00
append_manifest_find_end:
    lda manifest_buffer,y
    beq append_manifest_at_end
    iny
    cpy #MANIFEST_LIMIT
    bcc append_manifest_find_end
    sec
    rts
append_manifest_at_end:
    cpy #$00
    beq append_manifest_copy
    dey
    lda manifest_buffer,y
    cmp #13
    beq append_manifest_step_past_break
    cmp #10
    beq append_manifest_step_past_break
    iny
    cpy #MANIFEST_LIMIT
    bcs append_manifest_fail
    lda #13
    sta manifest_buffer,y
    iny
    jmp append_manifest_copy
append_manifest_step_past_break:
    iny
append_manifest_copy:
    ldx #$00
append_manifest_copy_loop:
    lda manifest_entry,x
    beq append_manifest_suffix
    cpy #MANIFEST_LIMIT-1
    bcs append_manifest_fail
    sta manifest_buffer,y
    inx
    iny
    bne append_manifest_copy_loop
append_manifest_suffix:
    cpy #MANIFEST_LIMIT
    bcs append_manifest_fail
    lda #13
    sta manifest_buffer,y
    iny
    lda #$00
    sta manifest_buffer,y
    clc
    rts
append_manifest_fail:
    sec
    rts

remove_manifest_entry:
    lda scan_ptr
    sta entry_ptr
    lda scan_ptr+1
    sta entry_ptr+1

remove_manifest_skip_line:
    ldy #$00
    lda (entry_ptr),y
    beq remove_manifest_shift
    cmp #13
    beq remove_manifest_skip_breaks
    cmp #10
    beq remove_manifest_skip_breaks
    jsr advance_entry_ptr
    jmp remove_manifest_skip_line

remove_manifest_skip_breaks:
    ldy #$00
    lda (entry_ptr),y
    cmp #13
    beq remove_manifest_advance_break
    cmp #10
    bne remove_manifest_shift
remove_manifest_advance_break:
    jsr advance_entry_ptr
    jmp remove_manifest_skip_breaks

remove_manifest_shift:
    ldy #$00
remove_manifest_shift_loop:
    lda (entry_ptr),y
    sta (scan_ptr),y
    beq remove_manifest_done
    jsr advance_entry_ptr
    jsr advance_scan_ptr
    jmp remove_manifest_shift_loop
remove_manifest_done:
    rts

save_manifest_buffer:
    lda #<project_marker
    sta save_params+0
    lda #>project_marker
    sta save_params+1
    lda #<manifest_buffer
    sta save_params+2
    lda #>manifest_buffer
    sta save_params+3
    lda #tool_file_status_fail
    sta save_params+4
    ldx #save_params
    jsr svc_file_save_sc0
    lda save_params+4
    cmp #tool_file_status_ok
    beq save_manifest_buffer_ok
    sec
    rts
save_manifest_buffer_ok:
    clc
    rts
