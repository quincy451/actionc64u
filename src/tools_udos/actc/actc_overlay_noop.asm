.include "actc_overlay_abi.inc"

.export actc_overlay_header
.export actc_overlay_entry
.export actc_overlay_end

.segment "CODE"

ACTC_CHAIN_SUCCESS_MASK = $03
ACTC_CHAIN_DEBUG = $02
ACTC_WORKFLOW_FAILURE = $01
ACTC_COMMAND_MAX = 31

actc_overlay_header:
    .byte 'A','C','O','V'
    .byte ACTC_OVERLAY_ABI_VERSION
    .byte ACTC_OVERLAY_PASS_NOOP
    .word ACTC_OVERLAY_EXEC_BASE
    .word actc_overlay_entry
    .word actc_overlay_end - actc_overlay_header
    .word $0000

actc_overlay_entry:
    stx actc_overlay_context_lo_seen
    sty actc_overlay_context_hi_seen
    stx ACTC_OVERLAY_CONTEXT_ZP
    sty ACTC_OVERLAY_CONTEXT_ZP+1
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_OK
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    ldy #ACTC_OVERLAY_CTX_PASS_ID
    lda #ACTC_OVERLAY_PASS_NOOP
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    lda C64_MEMCFG
    sta actc_overlay_memcfg_seen
    ldy #ACTC_OVERLAY_CTX_BODY_MODE
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    bne :+
    jmp actc_overlay_ok
:
    sta workflow_chain_mode
    ldy #ACTC_OVERLAY_CTX_DECL_VAR_COUNT
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta workflow_phase
    jsr load_workflow_command_ptr
    lda workflow_phase
    beq build_success_command
    jsr load_failure_line
    jsr load_workflow_module_ptr
    ldx #$00
build_failure_prefix:
    lda actedit_command_prefix,x
    beq build_command_module
    jsr append_command_char
    bcs actc_overlay_fail
    inx
    bne build_failure_prefix

build_success_command:
    jsr load_workflow_module_ptr
    ldx #$00
build_success_prefix:
    lda alink_command_prefix,x
    beq build_command_module
    jsr append_command_char
    bcs actc_overlay_fail
    inx
    bne build_success_prefix

build_command_module:
    ldx #$00
build_command_module_loop:
    txa
    tay
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq build_command_module_done
    jsr append_command_char
    bcs actc_overlay_fail
    inx
    cpx #24
    bcc build_command_module_loop
    txa
    tay
    lda (ACTC_OVERLAY_WORK_ZP),y
    bne actc_overlay_fail
build_command_module_done:
    lda workflow_phase
    bne build_failure_location
    lda workflow_chain_mode
    and #ACTC_CHAIN_SUCCESS_MASK
    cmp #ACTC_CHAIN_DEBUG
    bne finish_workflow_command
    lda #':'
    jsr append_command_char
    bcs actc_overlay_fail
    jmp finish_workflow_command

build_failure_location:
    lda #':'
    jsr append_command_char
    bcs actc_overlay_fail
    jsr append_failure_line_decimal
    bcs actc_overlay_fail

finish_workflow_command:
    ldy command_len
    lda #$00
    sta (ACTC_OVERLAY_SCAN_ZP),y
    jmp actc_overlay_ok

actc_overlay_ok:
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

load_workflow_command_ptr:
    lda #$00
    sta command_len
    ldy #ACTC_OVERLAY_CTX_SOURCE_WINDOW_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP
    ldy #ACTC_OVERLAY_CTX_SOURCE_WINDOW_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_SCAN_ZP+1
    rts

load_workflow_module_ptr:
    ldy #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    ldy #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP+1
    rts

load_failure_line:
    ldy #ACTC_OVERLAY_CTX_PROC_DEBUG_LINECOL_WINDOW_PTR_LO
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    ldy #ACTC_OVERLAY_CTX_PROC_DEBUG_LINECOL_WINDOW_PTR_HI
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP+1
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta failure_line
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta failure_line+1
    rts

append_command_char:
    ldy command_len
    cpy #ACTC_COMMAND_MAX
    bcs append_command_char_fail
    sta (ACTC_OVERLAY_SCAN_ZP),y
    inc command_len
    clc
    rts
append_command_char_fail:
    sec
    rts

append_failure_line_decimal:
    lda failure_line
    sta decimal_value
    lda failure_line+1
    sta decimal_value+1
    lda #$00
    sta decimal_started
    ldx #$00
append_failure_line_decimal_loop:
    cpx #$04
    beq append_failure_line_decimal_ones
    lda #$00
    sta decimal_digit
append_failure_line_decimal_subtract:
    lda decimal_value+1
    cmp decimal_divisors_hi,x
    bcc append_failure_line_decimal_digit
    bne :+
    lda decimal_value
    cmp decimal_divisors_lo,x
    bcc append_failure_line_decimal_digit
:
    sec
    lda decimal_value
    sbc decimal_divisors_lo,x
    sta decimal_value
    lda decimal_value+1
    sbc decimal_divisors_hi,x
    sta decimal_value+1
    inc decimal_digit
    bne append_failure_line_decimal_subtract
append_failure_line_decimal_digit:
    lda decimal_started
    bne append_failure_line_decimal_emit
    lda decimal_digit
    beq append_failure_line_decimal_next
append_failure_line_decimal_emit:
    lda decimal_digit
    clc
    adc #'0'
    jsr append_command_char
    bcs append_failure_line_decimal_fail
    lda #$01
    sta decimal_started
append_failure_line_decimal_next:
    inx
    bne append_failure_line_decimal_loop
append_failure_line_decimal_ones:
    lda decimal_value
    clc
    adc #'0'
    jmp append_command_char
append_failure_line_decimal_fail:
    sec
    rts

alink_command_prefix:
    .asciiz "ALINK "
actedit_command_prefix:
    .asciiz "ACTEDIT "
decimal_divisors_lo:
    .byte <10000, <1000, <100, <10
decimal_divisors_hi:
    .byte >10000, >1000, >100, >10

workflow_chain_mode:
    .byte $00
workflow_phase:
    .byte $00
command_len:
    .byte $00
failure_line:
    .word $0000
decimal_value:
    .word $0000
decimal_started:
    .byte $00
decimal_digit:
    .byte $00

actc_overlay_context_lo_seen:
    .byte $00
actc_overlay_context_hi_seen:
    .byte $00
actc_overlay_memcfg_seen:
    .byte $00

actc_overlay_end:
