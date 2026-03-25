build_manifest_entry:
    ldy #$00
build_manifest_entry_loop:
    lda module_name,y
    beq build_manifest_entry_suffix
    sta manifest_entry,y
    iny
    bne build_manifest_entry_loop
build_manifest_entry_suffix:
    lda #'.'
    sta manifest_entry,y
    iny
    lda #'A'
    sta manifest_entry,y
    iny
    lda #'C'
    sta manifest_entry,y
    iny
    lda #'T'
    sta manifest_entry,y
    iny
    lda #$00
    sta manifest_entry,y
    rts

manifest_contains_entry:
    lda #<manifest_buffer
    sta scan_ptr
    lda #>manifest_buffer
    sta scan_ptr+1
    jsr skip_current_line
    jsr skip_line_breaks
manifest_contains_entry_loop:
    ldy #$00
    lda (scan_ptr),y
    beq manifest_contains_entry_fail
    jsr entry_matches_current_line
    bcc manifest_contains_entry_ok
    jsr skip_current_line
    jsr skip_line_breaks
    jmp manifest_contains_entry_loop
manifest_contains_entry_ok:
    clc
    rts
manifest_contains_entry_fail:
    sec
    rts

entry_matches_current_line:
    ldy #$00
entry_matches_current_line_loop:
    lda manifest_entry,y
    beq entry_matches_current_line_end
    cmp (scan_ptr),y
    bne entry_matches_current_line_fail
    iny
    cpy #31
    bcc entry_matches_current_line_loop
entry_matches_current_line_fail:
    sec
    rts
entry_matches_current_line_end:
    lda (scan_ptr),y
    beq entry_matches_current_line_ok
    cmp #13
    beq entry_matches_current_line_ok
    cmp #10
    bne entry_matches_current_line_fail
entry_matches_current_line_ok:
    clc
    rts
