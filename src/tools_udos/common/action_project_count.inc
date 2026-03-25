count_manifest_entries:
    lda #$00
    sta module_count
    lda #<manifest_buffer
    sta scan_ptr
    lda #>manifest_buffer
    sta scan_ptr+1
    jsr skip_current_line
    jsr skip_line_breaks
count_manifest_entries_loop:
    ldy #$00
    lda (scan_ptr),y
    beq count_manifest_entries_done
    inc module_count
    jsr skip_current_line
    jsr skip_line_breaks
    jmp count_manifest_entries_loop
count_manifest_entries_done:
    rts
