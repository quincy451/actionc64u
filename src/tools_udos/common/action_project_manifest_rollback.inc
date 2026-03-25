replace_old_manifest_entry_and_save_or_rollback:
    jsr replace_old_manifest_entry_and_save
    bcc replace_old_manifest_entry_and_save_or_rollback_done
    jsr rollback_rename_target_path
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
replace_old_manifest_entry_and_save_or_rollback_done:
    rts

append_manifest_entry_and_save_or_delete_target:
    jsr append_manifest_entry_and_save
    bcc append_manifest_entry_and_save_or_delete_target_done
    jsr delete_target_path
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
append_manifest_entry_and_save_or_delete_target_done:
    rts
