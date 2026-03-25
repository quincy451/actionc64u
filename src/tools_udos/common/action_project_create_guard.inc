require_manifest_entry_missing:
    jsr manifest_contains_entry
    bcs require_manifest_entry_missing_done
    lda #<msg_exists
    ldy #>msg_exists
    jmp fail_with_ptr
require_manifest_entry_missing_done:
    rts

require_target_missing:
    jsr probe_target_path
    lda file_params+6
    cmp #tool_file_status_nofile
    beq require_target_missing_done
    cmp #tool_file_status_ok
    beq require_target_missing_exists
    cmp #tool_file_status_too_large
    beq require_target_missing_exists
    lda #<msg_probe_fail
    ldy #>msg_probe_fail
    jmp fail_with_ptr
require_target_missing_exists:
    lda #<msg_exists
    ldy #>msg_exists
    jmp fail_with_ptr
require_target_missing_done:
    rts
