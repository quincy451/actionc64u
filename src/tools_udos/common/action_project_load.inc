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
    jsr project_reader_consume_non_line_end_from_scan_ptr
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
    jsr project_reader_consume_line_break_from_scan_ptr
    jmp skip_line_breaks_loop
skip_line_breaks_done:
    rts

project_reader_consume_non_line_end_from_scan_ptr:
    jsr source_reader_peek_scan_ptr
    beq project_reader_consume_non_line_end_from_scan_ptr_fail
    cmp #13
    beq project_reader_consume_non_line_end_from_scan_ptr_fail
    cmp #10
    beq project_reader_consume_non_line_end_from_scan_ptr_fail
    jsr source_reader_consume_scan_ptr
    bcs project_reader_consume_non_line_end_from_scan_ptr_fail
    clc
    rts
project_reader_consume_non_line_end_from_scan_ptr_fail:
    sec
    rts

project_reader_consume_line_break_from_scan_ptr:
    jsr source_reader_peek_scan_ptr
    cmp #13
    beq project_reader_consume_line_break_from_scan_ptr_consume
    cmp #10
    beq project_reader_consume_line_break_from_scan_ptr_consume
    sec
    rts
project_reader_consume_line_break_from_scan_ptr_consume:
    jsr source_reader_consume_scan_ptr
    bcs project_reader_consume_line_break_from_scan_ptr_fail
    clc
    rts
project_reader_consume_line_break_from_scan_ptr_fail:
    sec
    rts

project_reader_consume_manifest_line_byte_from_scan_ptr:
    jmp project_reader_consume_non_line_end_from_scan_ptr

project_reader_consume_nonzero_from_scan_ptr:
    jsr source_reader_peek_scan_ptr
    beq project_reader_consume_nonzero_from_scan_ptr_fail
    jsr source_reader_consume_scan_ptr
    bcs project_reader_consume_nonzero_from_scan_ptr_fail
    clc
    rts
project_reader_consume_nonzero_from_scan_ptr_fail:
    sec
    rts

project_reader_consume_manifest_shift_byte_from_scan_ptr:
    jmp project_reader_consume_nonzero_from_scan_ptr

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
