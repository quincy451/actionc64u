append_manifest_entry_and_save:
    jsr append_manifest_entry
    bcs append_manifest_entry_and_save_fail
    jmp save_manifest_buffer
append_manifest_entry_and_save_fail:
    sec
    rts

remove_manifest_entry_and_save:
    jsr remove_manifest_entry
    jmp save_manifest_buffer
