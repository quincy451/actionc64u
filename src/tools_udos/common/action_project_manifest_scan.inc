begin_manifest_scan:
    lda #<manifest_buffer
    sta scan_ptr
    lda #>manifest_buffer
    sta scan_ptr+1
    jsr skip_current_line
    jsr skip_line_breaks
    rts

manifest_scan_has_entry:
    jsr source_reader_peek_scan_ptr
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
    jsr source_reader_peek_scan_ptr
    beq copy_manifest_line_to_buffer_done
    cmp #13
    beq copy_manifest_line_to_buffer_done
    cmp #10
    beq copy_manifest_line_to_buffer_done
    ldy line_len
    sta line_buffer,y
    jsr project_reader_consume_manifest_line_byte_from_scan_ptr
    bcs copy_manifest_line_to_buffer_done
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
