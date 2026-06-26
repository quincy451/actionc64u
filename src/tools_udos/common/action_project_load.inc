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
.ifdef ALINK_PRESERVE_ZP_SERVICES
    jsr alink_svc_file_load_sc0
.elseif .defined(ACTADD_PRESERVE_ZP_SERVICES)
    jsr actadd_svc_file_load_sc0
.else
    jsr svc_file_load_sc0
.endif
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
    jsr source_reader_peek_scan_ptr
    beq skip_current_line_done
    cmp #13
    beq skip_current_line_done
    cmp #10
    beq skip_current_line_done
    jsr source_reader_consume_scan_ptr
    jmp skip_current_line_loop
skip_current_line_done:
    rts

skip_line_breaks:
    ldy #$00
skip_line_breaks_loop:
    jsr source_reader_peek_scan_ptr
    cmp #13
    beq skip_line_breaks_advance
    cmp #10
    bne skip_line_breaks_done
skip_line_breaks_advance:
    jsr source_reader_consume_scan_ptr
    jmp skip_line_breaks_loop
skip_line_breaks_done:
    rts

source_reader_peek_scan_ptr:
    ldy #$00
    lda (scan_ptr),y
    clc
    rts

source_reader_peek_scan_y:
    lda (scan_ptr),y
    clc
    rts

source_reader_consume_scan_ptr:
    pha
    tya
    pha
    jsr source_reader_peek_scan_ptr
    bcc source_reader_consume_scan_ptr_ok
    pla
    tay
    pla
    sec
    rts
source_reader_consume_scan_ptr_ok:
    pla
    tay
    pla
advance_scan_ptr:
.ifdef ACTC_REU_SOURCE_CACHE
.if ACTC_REU_SOURCE_CACHE
    inc scan_ptr
    bne :+
    inc scan_ptr+1
:
    pha
    txa
    pha
    tya
    pha
    jsr source_reader_refill_if_at_window_end
    pla
    tay
    pla
    tax
    pla
    rts
.else
    inc scan_ptr
    bne :+
    inc scan_ptr+1
:
    rts
.endif
.else
    inc scan_ptr
    bne :+
    inc scan_ptr+1
:
    rts
.endif
