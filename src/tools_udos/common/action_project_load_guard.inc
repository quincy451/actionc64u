require_loaded_project:
    jsr load_project_manifest
    bcc require_loaded_project_done
    lda file_params+6
    cmp #tool_file_status_nofile
    beq require_loaded_project_missing
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
require_loaded_project_missing:
    lda #<msg_no_project
    ldy #>msg_no_project
    jmp fail_with_ptr
require_loaded_project_done:
    rts
