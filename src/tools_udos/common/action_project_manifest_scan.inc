begin_manifest_scan:
    lda #<manifest_buffer
    sta scan_ptr
    lda #>manifest_buffer
    sta scan_ptr+1
    jsr skip_current_line
    jsr skip_line_breaks
    rts

manifest_scan_has_entry:
    ldy #$00
    lda (scan_ptr),y
    beq manifest_scan_empty
    clc
    rts
manifest_scan_empty:
    sec
    rts

copy_manifest_line_to_buffer:
    lda #$00
    sta line_len
copy_manifest_line_to_buffer_loop:
    ldy #$00
    lda (scan_ptr),y
    beq copy_manifest_line_to_buffer_done
    cmp #13
    beq copy_manifest_line_to_buffer_done
    cmp #10
    beq copy_manifest_line_to_buffer_done
    ldy line_len
    sta line_buffer,y
    jsr advance_scan_ptr
    inc line_len
    lda line_len
    cmp #31
    bcc copy_manifest_line_to_buffer_loop
copy_manifest_line_to_buffer_done:
    ldy line_len
    lda #$00
    sta line_buffer,y
    lda line_len
    beq copy_manifest_line_to_buffer_empty
    clc
    rts
copy_manifest_line_to_buffer_empty:
    sec
    rts
