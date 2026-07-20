.include "actc_overlay_abi.inc"
.include "udos_services.inc"

.export actc_overlay_header
.export actc_overlay_entry
.export actc_overlay_end

.segment "CODE"

actc_overlay_header:
    .byte 'A','C','O','V'
    .byte ACTC_OVERLAY_ABI_VERSION
    .byte ACTC_OVERLAY_PASS_SOURCE_HEADER
    .word ACTC_OVERLAY_EXEC_BASE
    .word actc_overlay_entry
    .word actc_overlay_end - actc_overlay_header
    .word $0000

actc_overlay_entry:
    stx ACTC_OVERLAY_CONTEXT_ZP
    sty ACTC_OVERLAY_CONTEXT_ZP+1
    ldy #ACTC_OVERLAY_CTX_PASS_ID
    lda #ACTC_OVERLAY_PASS_SOURCE_HEADER
    sta (ACTC_OVERLAY_CONTEXT_ZP),y

    ldy #ACTC_OVERLAY_CTX_SOURCE_WINDOW_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP
    ldy #ACTC_OVERLAY_CTX_SOURCE_WINDOW_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP+1
    ldy #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    ldy #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP+1
    lda #$00
    sta source_mark
    sta source_mark+1
    sta source_mark+2
    sta source_page_failed
    jsr load_source_window_remaining_from_context

    jsr skip_source_prefix
    jsr match_module_keyword
    bcs source_header_fail_bad_module
    jsr skip_source_spaces
    jsr save_module_start_mark
    jsr compare_requested_module
    bcs source_header_fail_bad_module

    ldy #ACTC_OVERLAY_CTX_SOURCE_MARK_LO
    lda module_start_mark
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    ldy #ACTC_OVERLAY_CTX_SOURCE_MARK_HI
    lda module_start_mark+1
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    ldy #ACTC_OVERLAY_CTX_SOURCE_MARK_BANK
    lda module_start_mark+2
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_OK
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    clc
    lda #ACTC_OVERLAY_STATUS_OK
    rts

source_header_fail_bad_module:
    jsr debug_bad_module_scan_head
    ldy #ACTC_OVERLAY_CTX_DIAG_PTR_LO
    lda #<msg_bad_module
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    ldy #ACTC_OVERLAY_CTX_DIAG_PTR_HI
    lda #>msg_bad_module
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
source_header_fail:
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_FAILED
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    sec
    lda #ACTC_OVERLAY_STATUS_FAILED
    rts

skip_source_prefix:
skip_source_prefix_loop:
    jsr skip_source_whitespace
    ldy #$00
    jsr source_header_peek_scan_y
    cmp #';'
    bne skip_source_prefix_done
    jsr skip_source_comment_line
    jmp skip_source_prefix_loop
skip_source_prefix_done:
    rts

skip_source_comment_line:
skip_source_comment_line_loop:
    ldy #$00
    jsr source_header_peek_scan_y
    beq skip_source_comment_line_done
    cmp #10
    beq skip_source_comment_line_done
    cmp #13
    beq skip_source_comment_line_done
    jsr source_header_consume_scan_y
    bcs skip_source_comment_line_done
    jmp skip_source_comment_line_loop
skip_source_comment_line_done:
    rts

skip_source_whitespace:
skip_source_whitespace_loop:
    jsr source_header_consume_whitespace_char
    bcs skip_source_whitespace_done
    jmp skip_source_whitespace_loop
skip_source_whitespace_done:
    rts

skip_source_spaces:
skip_source_spaces_loop:
    jsr source_header_consume_inline_space_char
    bcs skip_source_spaces_done
    jmp skip_source_spaces_loop
skip_source_spaces_done:
    rts

source_header_consume_whitespace_char:
    ldy #$00
    jsr source_header_peek_scan_y
    cmp #' '
    beq source_header_consume_whitespace_char_consume
    cmp #9
    beq source_header_consume_whitespace_char_consume
    cmp #10
    beq source_header_consume_whitespace_char_consume
    cmp #13
    beq source_header_consume_whitespace_char_consume
    sec
    rts
source_header_consume_whitespace_char_consume:
    jsr source_header_consume_scan_y
    rts

source_header_consume_inline_space_char:
    ldy #$00
    jsr source_header_peek_scan_y
    cmp #' '
    beq source_header_consume_inline_space_char_consume
    cmp #9
    beq source_header_consume_inline_space_char_consume
    sec
    rts
source_header_consume_inline_space_char_consume:
    jsr source_header_consume_scan_y
    rts

match_module_keyword:
    ldx #$00
match_module_keyword_loop:
    lda module_keyword,x
    beq match_module_keyword_ok
    jsr source_header_consume_uppercase_char
    bcs match_module_keyword_fail
    inx
    bne match_module_keyword_loop
match_module_keyword_ok:
    clc
    rts
match_module_keyword_fail:
    sec
    rts

compare_requested_module:
    ldx #$00
compare_requested_module_loop:
    jsr source_header_consume_requested_module_char
    bcc compare_requested_module_char_valid
    lda compare_char
    beq compare_requested_module_done
    jmp compare_requested_module_fail
compare_requested_module_char_valid:
    inx
    cpx #24
    bcc compare_requested_module_loop
compare_requested_module_fail:
    sec
    rts
compare_requested_module_done:
    cpx #$00
    beq compare_requested_module_fail
    txa
    tay
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr uppercase_ascii
    cmp #$00
    bne compare_requested_module_fail
    clc
    rts

source_header_consume_uppercase_char:
    sta expected_char
    ldy #$00
    jsr source_header_peek_scan_y
    beq source_header_consume_uppercase_char_fail
    jsr uppercase_ascii
    cmp expected_char
    bne source_header_consume_uppercase_char_fail
    jsr source_header_consume_scan_y
    bcs source_header_consume_uppercase_char_fail
    clc
    rts
source_header_consume_uppercase_char_fail:
    sec
    rts

.include "actc_overlay_lexical.inc"

source_header_symbol_token_char_valid_x:
    lda expected_char
    jsr uppercase_ascii
    sta expected_char
    cpx #$00
    bne source_header_symbol_token_char_valid_x_body
    jmp uppercase_symbol_start_valid
source_header_symbol_token_char_valid_x_body:
    jmp uppercase_symbol_body_valid

source_header_consume_requested_module_char:
    ldy #$00
    jsr source_header_peek_scan_y
    bne source_header_consume_requested_module_have_char
    lda #$FF
    sta compare_char
    sec
    rts
source_header_consume_requested_module_have_char:
    sta expected_char
    jsr source_header_symbol_token_char_valid_x
    bcc source_header_consume_requested_module_char_valid
    lda #$00
    sta compare_char
    sec
    rts
source_header_consume_requested_module_char_valid:
    lda expected_char
    sta compare_char
    txa
    tay
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr uppercase_ascii
    cmp compare_char
    bne source_header_consume_requested_module_fail
    ldy #$00
    jsr source_header_consume_scan_y
    bcs source_header_consume_requested_module_fail
    clc
    rts
source_header_consume_requested_module_fail:
    lda #$FF
    sta compare_char
    sec
    rts

save_module_start_mark:
    lda source_mark
    sta module_start_mark
    lda source_mark+1
    sta module_start_mark+1
    lda source_mark+2
    sta module_start_mark+2
    rts

load_source_window_remaining_from_context:
    ldy #ACTC_OVERLAY_CTX_SOURCE_WINDOW_LEN_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta source_window_remaining
    ldy #ACTC_OVERLAY_CTX_SOURCE_WINDOW_LEN_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta source_window_remaining+1
    rts

load_source_window_ptr_from_context:
    ldy #ACTC_OVERLAY_CTX_SOURCE_WINDOW_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP
    ldy #ACTC_OVERLAY_CTX_SOURCE_WINDOW_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP+1
    rts

source_mark_before_total:
    ldy #ACTC_OVERLAY_CTX_SOURCE_TOTAL_LEN_BANK
    lda source_mark+2
    cmp (ACTC_OVERLAY_CONTEXT_ZP),y
    bcc source_mark_before_total_yes
    bne source_mark_before_total_no
    ldy #ACTC_OVERLAY_CTX_SOURCE_TOTAL_LEN_HI
    lda source_mark+1
    cmp (ACTC_OVERLAY_CONTEXT_ZP),y
    bcc source_mark_before_total_yes
    bne source_mark_before_total_no
    ldy #ACTC_OVERLAY_CTX_SOURCE_TOTAL_LEN_LO
    lda source_mark
    cmp (ACTC_OVERLAY_CONTEXT_ZP),y
    bcc source_mark_before_total_yes
source_mark_before_total_no:
    clc
    rts
source_mark_before_total_yes:
    sec
    rts

ensure_source_window_available:
    lda source_window_remaining
    ora source_window_remaining+1
    bne ensure_source_window_available_done
    jsr source_mark_before_total
    bcs ensure_source_window_available_load_next
ensure_source_window_available_done:
    rts
ensure_source_window_available_load_next:
    jmp load_next_source_window_from_context

call_load_next_source_window:
    ldy #ACTC_OVERLAY_CTX_LOAD_NEXT_SOURCE_WINDOW_FN_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target
    ldy #ACTC_OVERLAY_CTX_LOAD_NEXT_SOURCE_WINDOW_FN_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target+1
    lda call_target
    ora call_target+1
    beq call_load_next_source_window_fail
    jsr call_target_address
    rts
call_load_next_source_window_fail:
    sec
    rts

call_target_address:
    sec
    lda call_target
    sbc #$01
    sta call_target_minus_one
    lda call_target+1
    sbc #$00
    pha
    lda call_target_minus_one
    pha
    rts

load_next_source_window_from_context:
    pha
    txa
    pha
    tya
    pha
    jsr call_load_next_source_window
    bcc load_next_source_window_from_context_ok
    lda #$01
    sta source_page_failed
    jmp load_next_source_window_from_context_restore
load_next_source_window_from_context_ok:
    jsr load_source_window_ptr_from_context
    jsr load_source_window_remaining_from_context
load_next_source_window_from_context_restore:
    pla
    tay
    pla
    tax
    pla
    rts

advance_source_window_remaining:
    lda source_window_remaining
    ora source_window_remaining+1
    beq advance_source_window_remaining_done
    lda source_window_remaining
    bne :+
    dec source_window_remaining+1
:
    dec source_window_remaining
    lda source_window_remaining
    ora source_window_remaining+1
    bne advance_source_window_remaining_done
    tya
    pha
    jsr source_mark_before_total
    bcs advance_source_window_load_next
    pla
    tay
    rts
advance_source_window_load_next:
    pla
    tay
    jmp load_next_source_window_from_context
advance_source_window_remaining_done:
    rts

advance_source_scan:
    inc ACTC_OVERLAY_SCAN_ZP
    bne :+
    inc ACTC_OVERLAY_SCAN_ZP+1
:
    inc source_mark
    bne :+
    inc source_mark+1
    bne :+
    inc source_mark+2
:
    jsr advance_source_window_remaining
    rts

source_header_peek_scan_y:
    jsr ensure_source_window_available
    lda source_page_failed
    beq source_header_peek_scan_y_read
    lda #$00
    rts
source_header_peek_scan_y_read:
    lda (ACTC_OVERLAY_SCAN_ZP),y
    rts

source_header_consume_scan_y:
    jsr source_header_peek_scan_y
    bne source_header_consume_scan_y_advance
    lda source_page_failed
    bne source_header_consume_scan_y_fail
    clc
    rts
source_header_consume_scan_y_advance:
    jsr advance_source_scan
    lda source_page_failed
    bne source_header_consume_scan_y_fail
    clc
    rts
source_header_consume_scan_y_fail:
    sec
    rts

debug_bad_module_scan_head:
    ldy #$00
debug_bad_module_scan_head_loop:
    jsr source_header_peek_scan_y
    sta $03E8,y
    iny
    cpy #$08
    bcc debug_bad_module_scan_head_loop
    rts

module_keyword:
    .asciiz "MODULE"
msg_bad_module:
    .asciiz "BAD MODULE"
source_mark:
    .byte $00,$00,$00
module_start_mark:
    .byte $00,$00,$00
source_window_remaining:
    .word $0000
source_page_failed:
    .byte $00
call_target:
    .word $0000
call_target_minus_one:
    .byte $00
expected_char:
    .byte $00
compare_char:
    .byte $00

actc_overlay_end:
