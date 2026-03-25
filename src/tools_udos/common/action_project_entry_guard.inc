require_manifest_entry_tracked:
    jsr manifest_contains_entry
    bcc require_manifest_entry_tracked_done
    lda #<msg_not_in_project
    ldy #>msg_not_in_project
    jmp fail_with_ptr
require_manifest_entry_tracked_done:
    rts
