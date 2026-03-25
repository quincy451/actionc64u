.ifndef ACTION_PROJECT_FLAG_TRUNCATED
ACTION_PROJECT_FLAG_TRUNCATED = 0
.endif

load_project_manifest:
.if ACTION_PROJECT_FLAG_TRUNCATED <> 0
    lda status_flags
    and #($ff-ACTION_PROJECT_FLAG_TRUNCATED)
    sta status_flags
.endif
    lda #<project_marker
    sta file_params+0
    lda #>project_marker
    sta file_params+1
    lda #<manifest_buffer
    sta file_params+2
    lda #>manifest_buffer
    sta file_params+3
    lda #<MANIFEST_LIMIT
    sta file_params+4
    lda #>MANIFEST_LIMIT
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    sta file_params+8
    ldx #file_params
    jsr svc_file_load_sc0
    lda file_params+6
    cmp #tool_file_status_ok
    beq load_project_manifest_ok
    cmp #tool_file_status_too_large
    bne load_project_manifest_fail
.if ACTION_PROJECT_FLAG_TRUNCATED <> 0
    lda status_flags
    ora #ACTION_PROJECT_FLAG_TRUNCATED
    sta status_flags
.endif
load_project_manifest_ok:
    ldy file_params+7
    lda #$00
    sta manifest_buffer,y
    clc
    rts
load_project_manifest_fail:
    sec
    rts

skip_current_line:
    ldy #$00
skip_current_line_loop:
    lda (scan_ptr),y
    beq skip_current_line_done
    cmp #13
    beq skip_current_line_done
    cmp #10
    beq skip_current_line_done
    jsr advance_scan_ptr
    jmp skip_current_line_loop
skip_current_line_done:
    rts

skip_line_breaks:
    ldy #$00
skip_line_breaks_loop:
    lda (scan_ptr),y
    cmp #13
    beq skip_line_breaks_advance
    cmp #10
    bne skip_line_breaks_done
skip_line_breaks_advance:
    jsr advance_scan_ptr
    jmp skip_line_breaks_loop
skip_line_breaks_done:
    rts

advance_scan_ptr:
    inc scan_ptr
    bne :+
    inc scan_ptr+1
:
    rts
