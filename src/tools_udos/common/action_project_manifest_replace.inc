replace_old_manifest_entry_and_save:
    jsr copy_old_manifest_to_manifest_entry
    jsr manifest_contains_entry
    bcs replace_old_manifest_entry_and_save_fail
    jsr remove_manifest_entry
    jsr build_manifest_entry
    jsr append_manifest_entry
    bcs replace_old_manifest_entry_and_save_fail
    jmp save_manifest_buffer
replace_old_manifest_entry_and_save_fail:
    sec
    rts
