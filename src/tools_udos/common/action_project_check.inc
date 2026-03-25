count_missing_entries:
    lda #$00
    sta missing_count
    jsr begin_manifest_scan
    jsr manifest_scan_has_entry
    bcs count_missing_entries_done
count_missing_entries_loop:
    jsr copy_manifest_line_to_buffer
    bcs count_missing_entries_done
    jsr copy_line_buffer_to_manifest_entry
    jsr build_target_path
    jsr probe_target_path
    lda file_params+6
    cmp #tool_file_status_nofile
    beq count_missing_entries_mark_missing
    cmp #tool_file_status_ok
    beq count_missing_entries_next
    cmp #tool_file_status_too_large
    beq count_missing_entries_next
    lda #<msg_probe_fail
    ldy #>msg_probe_fail
    jmp fail_with_ptr
count_missing_entries_mark_missing:
    inc missing_count
count_missing_entries_next:
    jsr skip_line_breaks
    jsr manifest_scan_has_entry
    bcc count_missing_entries_loop
count_missing_entries_done:
    rts

print_missing_entries:
    jsr begin_manifest_scan
    jsr manifest_scan_has_entry
    bcs print_missing_entries_done
print_missing_entries_loop:
    jsr copy_manifest_line_to_buffer
    bcs print_missing_entries_done
    jsr copy_line_buffer_to_manifest_entry
    jsr build_target_path
    jsr probe_target_path
    lda file_params+6
    cmp #tool_file_status_nofile
    beq print_missing_entries_emit
    cmp #tool_file_status_ok
    beq print_missing_entries_next
    cmp #tool_file_status_too_large
    beq print_missing_entries_next
    lda #<msg_probe_fail
    ldy #>msg_probe_fail
    jmp fail_with_ptr
print_missing_entries_emit:
    lda #<msg_missing_prefix
    ldy #>msg_missing_prefix
    jsr print_ptr
    lda #<line_buffer
    ldy #>line_buffer
    jsr print_line_ptr
print_missing_entries_next:
    jsr skip_line_breaks
    jsr manifest_scan_has_entry
    bcc print_missing_entries_loop
print_missing_entries_done:
    rts

print_missing_count_line:
    lda #<msg_missing_prefix
    ldy #>msg_missing_prefix
    jsr print_ptr
    lda missing_count
    sta module_count
    jsr build_count_buffer
    lda #<count_buffer
    ldy #>count_buffer
    jmp print_line_ptr

copy_line_buffer_to_manifest_entry:
    ldy #$00
copy_line_buffer_to_manifest_entry_loop:
    lda line_buffer,y
    sta manifest_entry,y
    beq copy_line_buffer_to_manifest_entry_done
    iny
    bne copy_line_buffer_to_manifest_entry_loop
copy_line_buffer_to_manifest_entry_done:
    rts
