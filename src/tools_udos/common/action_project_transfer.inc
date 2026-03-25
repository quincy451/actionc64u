copy_manifest_entry_to_old_manifest:
    lda #<manifest_entry
    sta entry_ptr
    lda #>manifest_entry
    sta entry_ptr+1
    lda #<old_manifest_entry
    sta const_ptr
    lda #>old_manifest_entry
    sta const_ptr+1
    jmp copy_zero_string

copy_old_manifest_to_manifest_entry:
    lda #<old_manifest_entry
    sta entry_ptr
    lda #>old_manifest_entry
    sta entry_ptr+1
    lda #<manifest_entry
    sta const_ptr
    lda #>manifest_entry
    sta const_ptr+1
    jmp copy_zero_string

copy_target_path_to_old_target:
    lda #<target_path
    sta entry_ptr
    lda #>target_path
    sta entry_ptr+1
    lda #<old_target_path
    sta const_ptr
    lda #>old_target_path
    sta const_ptr+1
    jmp copy_zero_string

copy_zero_string:
    ldy #$00
copy_zero_string_loop:
    lda (entry_ptr),y
    sta (const_ptr),y
    beq copy_zero_string_done
    iny
    bne copy_zero_string_loop
copy_zero_string_done:
    rts

rename_old_target_to_target:
    lda #<old_target_path
    sta save_params+0
    lda #>old_target_path
    sta save_params+1
    lda #<target_path
    sta save_params+2
    lda #>target_path
    sta save_params+3
    lda #tool_file_status_fail
    sta save_params+4
    ldx #save_params
    jsr svc_file_rename_sc0
    lda save_params+4
    rts

copy_old_target_to_target:
    lda #<old_target_path
    sta save_params+0
    lda #>old_target_path
    sta save_params+1
    lda #<target_path
    sta save_params+2
    lda #>target_path
    sta save_params+3
    lda #tool_file_status_fail
    sta save_params+4
    ldx #save_params
    jsr svc_file_copy_sc0
    lda save_params+4
    rts

rollback_rename_target_path:
    lda #<target_path
    sta save_params+0
    lda #>target_path
    sta save_params+1
    lda #<old_target_path
    sta save_params+2
    lda #>old_target_path
    sta save_params+3
    lda #tool_file_status_fail
    sta save_params+4
    ldx #save_params
    jsr svc_file_rename_sc0
    rts
