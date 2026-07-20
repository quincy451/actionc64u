.include "actc_overlay_abi.inc"

.export actc_overlay_header
.export actc_overlay_entry
.export actc_overlay_end

.segment "CODE"

actc_overlay_header:
    .byte 'A','C','O','V'
    .byte ACTC_OVERLAY_ABI_VERSION
    .byte ACTC_OVERLAY_PASS_PAYLOAD_LAYOUT
    .word ACTC_OVERLAY_EXEC_BASE
    .word actc_overlay_entry
    .word actc_overlay_end - actc_overlay_header
    .word $0000

actc_overlay_entry:
    stx ACTC_OVERLAY_CONTEXT_ZP
    sty ACTC_OVERLAY_CONTEXT_ZP+1
    ldy #ACTC_OVERLAY_CTX_PASS_ID
    lda #ACTC_OVERLAY_PASS_PAYLOAD_LAYOUT
    sta (ACTC_OVERLAY_CONTEXT_ZP),y

    jsr compute_payload_layout_overlay
    bcs actc_overlay_fail

    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_OK
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    clc
    lda #ACTC_OVERLAY_STATUS_OK
    rts

actc_overlay_fail:
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_FAILED
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    sec
    lda #ACTC_OVERLAY_STATUS_FAILED
    rts

compute_payload_layout_overlay:
    lda #$00
    sta payload_offset_lo
    sta payload_offset_hi
    sta proc_index_data
compute_payload_layout_overlay_loop:
    ldx proc_index_data
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp proc_index_data
    bne :+
    jmp compute_payload_layout_overlay_done
:

    lda payload_offset_lo
    sta layout_offset_lo_local
    lda payload_offset_hi
    sta layout_offset_hi_local
    lda #$01
    sta layout_size_lo_local
    lda #$00
    sta layout_size_hi_local

    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_context_function
    jsr load_resident_body_ptr_to_scan_zp
    ldy #$00
compute_payload_layout_overlay_body_loop:
    jsr payload_layout_peek_payload_y
    bne :+
    jmp compute_payload_layout_overlay_ret
:
    cmp #'X'
    bne :+
    jmp compute_payload_layout_overlay_add_call
:
    cmp #'c'
    bne :+
    jmp compute_payload_layout_overlay_add_call
:   cmp #ACTC_BODY_OP_FIXED_CALL
    bne :+
    jmp compute_payload_layout_overlay_add_call
:   cmp #'C'
    bne :+
    jmp compute_payload_layout_overlay_add_call
:   cmp #'A'
    bne :+
    jmp compute_payload_layout_overlay_add_call
:   cmp #'u'
    bne :+
    jmp compute_payload_layout_overlay_add_call
:   cmp #'p'
    bne :+
    jmp compute_payload_layout_overlay_add_call
:
    cmp #'@'
    bne :+
    jmp compute_payload_layout_overlay_skip_selector
:
    cmp #'s'
    bne :+
    jmp compute_payload_layout_overlay_add_string
:
    cmp #'e'
    bne :+
    jmp compute_payload_layout_overlay_add_string
:
    cmp #'i'
    bne :+
    jmp compute_payload_layout_overlay_add_int
:
    cmp #'j'
    bne :+
    jmp compute_payload_layout_overlay_add_int
:
    cmp #'L'
    bne :+
    jmp compute_payload_layout_overlay_add_single_int_pair
:   cmp #'S'
    bne :+
    jmp compute_payload_layout_overlay_add_single_int_pair
:   cmp #'U'
    bne :+
    jmp compute_payload_layout_overlay_add_single_int_pair
:   cmp #'T'
    bne :+
    jmp compute_payload_layout_overlay_add_single_int_pair
:   cmp #'y'
    beq compute_payload_layout_overlay_add_single_int
    cmp #'z'
    beq compute_payload_layout_overlay_add_single_int
    cmp #'h'
    beq compute_payload_layout_overlay_add_single_int
    cmp #'f'
    beq compute_payload_layout_overlay_add_single_int
    cmp #'t'
    beq compute_payload_layout_overlay_add_single_int
    cmp #'w'
    beq compute_payload_layout_overlay_add_single_int
    cmp #'v'
    beq compute_payload_layout_overlay_add_zero
    cmp #'d'
    beq compute_payload_layout_overlay_add_zero
    cmp #'o'
    beq compute_payload_layout_overlay_add_zero
    cmp #'x'
    beq compute_payload_layout_overlay_add_single_int
    cmp #'a'
    beq compute_payload_layout_overlay_add_single
    cmp #'m'
    beq compute_payload_layout_overlay_add_single
    cmp #'*'
    beq compute_payload_layout_overlay_add_single
    cmp #'/'
    beq compute_payload_layout_overlay_add_single
    cmp #'q'
    beq compute_payload_layout_overlay_add_single
    cmp #'n'
    beq compute_payload_layout_overlay_add_single
    cmp #'l'
    beq compute_payload_layout_overlay_add_single
    cmp #'g'
    beq compute_payload_layout_overlay_add_single
    cmp #'r'
    beq compute_payload_layout_overlay_add_single
    cmp #'F'
    beq compute_payload_layout_overlay_skip_for
    cmp #'O'
    beq compute_payload_layout_overlay_add_zero
    jmp compute_payload_layout_overlay_bad

compute_payload_layout_overlay_skip_for:
    iny
    iny
    iny
    jmp compute_payload_layout_overlay_body_loop

compute_payload_layout_overlay_skip_selector:
    iny
    iny
    jmp compute_payload_layout_overlay_body_loop

compute_payload_layout_overlay_add_call:
    lda #$03
    jsr add_a_to_layout_size
    iny
    iny
    jmp compute_payload_layout_overlay_body_loop

compute_payload_layout_overlay_add_string:
    lda #$06
    jsr add_a_to_layout_size
    iny
    iny
    jmp compute_payload_layout_overlay_body_loop

compute_payload_layout_overlay_add_single:
    lda #$01
    jsr add_a_to_layout_size
    iny
    jmp compute_payload_layout_overlay_body_loop

compute_payload_layout_overlay_add_single_int:
    lda #$03
    jsr add_a_to_layout_size
    iny
    jmp compute_payload_layout_overlay_body_loop

compute_payload_layout_overlay_add_single_int_pair:
    lda #$03
    jsr add_a_to_layout_size
    iny
    iny
    jmp compute_payload_layout_overlay_body_loop

compute_payload_layout_overlay_add_zero:
    iny
    jmp compute_payload_layout_overlay_body_loop

compute_payload_layout_overlay_add_int:
    lda #$06
    jsr add_a_to_layout_size
    iny
    iny
    beq :+
    jmp compute_payload_layout_overlay_body_loop
:
compute_payload_layout_overlay_ret:
    cpy #$00
    beq compute_payload_layout_overlay_ret_add
    dey
    jsr payload_layout_peek_payload_y
    cmp #'r'
    bne compute_payload_layout_overlay_ret_add
    lda layout_size_lo_local
    bne :+
    dec layout_size_hi_local
:
    dec layout_size_lo_local
compute_payload_layout_overlay_ret_add:
    clc
    lda payload_offset_lo
    adc layout_size_lo_local
    sta payload_offset_lo
    lda payload_offset_hi
    adc layout_size_hi_local
    sta payload_offset_hi
    jsr store_layout_locals_to_resident
    ldx proc_index_data
    lda #ACTC_OVERLAY_CTX_STORE_LAYOUT_FN_LO
    jsr call_context_function
    inc proc_index_data
    jmp compute_payload_layout_overlay_loop

compute_payload_layout_overlay_done:
    ldx #$00
compute_payload_layout_overlay_strings_loop:
    lda #ACTC_OVERLAY_CTX_STRING_COUNT_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    txa
    cmp (ACTC_OVERLAY_WORK_ZP),y
    beq compute_payload_layout_overlay_done_ok
    lda payload_offset_lo
    jsr store_string_offset_local_to_resident
    txa
    pha
    lda #ACTC_OVERLAY_CTX_STORE_STRING_OFFSET_FN_LO
    jsr call_context_function
    pla
    tax
    txa
    pha
    lda #ACTC_OVERLAY_CTX_SET_STRING_PTR_FN_LO
    jsr call_context_function
    pla
    tax
    jsr load_resident_body_ptr_to_scan_zp
    ldy #$00
compute_payload_layout_overlay_string_len_loop:
    jsr payload_layout_peek_payload_y
    beq compute_payload_layout_overlay_string_done
    inc payload_offset_lo
    bne :+
    inc payload_offset_hi
:
    iny
    bne compute_payload_layout_overlay_string_len_loop
compute_payload_layout_overlay_string_done:
    inc payload_offset_lo
    bne :+
    inc payload_offset_hi
:
    inx
    bne compute_payload_layout_overlay_strings_loop

compute_payload_layout_overlay_done_ok:
    clc
    rts

compute_payload_layout_overlay_bad:
    ldy #ACTC_OVERLAY_CTX_DIAG_PTR_LO
    lda #<msg_bad_call
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    ldy #ACTC_OVERLAY_CTX_DIAG_PTR_HI
    lda #>msg_bad_call
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    sec
    rts

add_a_to_layout_size:
    clc
    adc layout_size_lo_local
    sta layout_size_lo_local
    bcc add_a_to_layout_size_done
    inc layout_size_hi_local
add_a_to_layout_size_done:
    rts

payload_layout_peek_payload_y:
    ; Reads resident body/string payload windows selected by SET_*_PTR,
    ; not source text. Source-window paging belongs to SourceReader helpers.
    lda (ACTC_OVERLAY_SCAN_ZP),y
    rts

store_layout_locals_to_resident:
    lda #ACTC_OVERLAY_CTX_LAYOUT_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda layout_offset_lo_local
    sta (ACTC_OVERLAY_WORK_ZP),y
    iny
    lda layout_offset_hi_local
    sta (ACTC_OVERLAY_WORK_ZP),y
    iny
    lda layout_size_lo_local
    sta (ACTC_OVERLAY_WORK_ZP),y
    iny
    lda layout_size_hi_local
    sta (ACTC_OVERLAY_WORK_ZP),y
    rts

store_string_offset_local_to_resident:
    pha
    lda #ACTC_OVERLAY_CTX_STRING_OFFSET_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    pla
    sta (ACTC_OVERLAY_WORK_ZP),y
    rts

load_resident_body_ptr_to_scan_zp:
    lda #ACTC_OVERLAY_CTX_BODY_PTR_SLOT_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP+1
    rts

load_context_ptr_to_work_zp:
    tay
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    iny
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP+1
    rts

call_context_function:
    tay
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target_ptr
    iny
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target_ptr+1
    sec
    lda call_target_ptr
    sbc #$01
    sta call_target_minus_one
    lda call_target_ptr+1
    sbc #$00
    pha
    lda call_target_minus_one
    pha
    rts

msg_bad_call:
    .asciiz "BAD CALL"
call_target_minus_one:
    .byte $00
call_target_ptr:
    .word $0000
payload_offset_lo:
    .byte $00
payload_offset_hi:
    .byte $00
proc_index_data:
    .byte $00
layout_offset_lo_local:
    .byte $00
layout_offset_hi_local:
    .byte $00
layout_size_lo_local:
    .byte $00
layout_size_hi_local:
    .byte $00

actc_overlay_end:
