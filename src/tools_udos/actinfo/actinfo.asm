.include "udos_services.inc"

.export start

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2

.code

start:
    lda #<banner
    ldy #>banner
    jsr print_ptr

    ldx #svc_retptr
    jsr svc_get_abi_version
    jsr print_dec16_zp
    jsr svc_console_newline

    ldx #svc_retptr
    jsr svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    beq no_args

    lda #<args_prefix
    ldy #>args_prefix
    jsr print_ptr

    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    ldx #svc_retptr
    jsr svc_console_write_sc0
    jsr svc_console_newline

    lda #<done_msg
    ldy #>done_msg
    jsr print_ptr
    jsr svc_console_newline
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

no_args:
    lda #<noargs_msg
    ldy #>noargs_msg
    jsr print_ptr
    jsr svc_console_newline
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

print_ptr:
    sta svc_retptr
    sty svc_retptr+1
    ldx #svc_retptr
    jmp svc_console_write_sc0

print_dec16_zp:
    lda svc_retptr
    sta value_lo
    lda svc_retptr+1
    sta value_hi
    ldx #$00
thousands_loop:
    lda value_hi
    cmp #>1000
    bcc hundreds_start
    bne thousands_sub
    lda value_lo
    cmp #<1000
    bcc hundreds_start
thousands_sub:
    sec
    lda value_lo
    sbc #<1000
    sta value_lo
    lda value_hi
    sbc #>1000
    sta value_hi
    inx
    bne thousands_loop
hundreds_start:
    txa
    ldy #$00
    jsr emit_digit_if_needed
    ldx #$00
hundreds_loop:
    lda value_hi
    cmp #>100
    bcc tens_start
    bne hundreds_sub
    lda value_lo
    cmp #<100
    bcc tens_start
hundreds_sub:
    sec
    lda value_lo
    sbc #<100
    sta value_lo
    lda value_hi
    sbc #>100
    sta value_hi
    inx
    bne hundreds_loop
tens_start:
    txa
    jsr emit_digit_if_needed
    ldx #$00
tens_loop:
    lda value_hi
    bne tens_sub
    lda value_lo
    cmp #10
    bcc ones_digit
tens_sub:
    sec
    lda value_lo
    sbc #10
    sta value_lo
    lda value_hi
    sbc #0
    sta value_hi
    inx
    bne tens_loop
ones_digit:
    txa
    jsr emit_digit_if_needed
    lda value_lo
    clc
    adc #'0'
    jmp emit_char

emit_digit_if_needed:
    pha
    cpy #$00
    bne emit_digit_now
    pla
    beq emit_digit_skip
    pha
emit_digit_now:
    pla
    clc
    adc #'0'
    jsr emit_char
    ldy #$01
    rts
emit_digit_skip:
    rts

emit_char:
    sta char_buf
    lda #<char_buf
    sta svc_retptr
    lda #>char_buf
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_console_write_sc0

banner:
    .asciiz "ACTINFO ABI "
args_prefix:
    .asciiz "ARGS "
noargs_msg:
    .asciiz "NO ARGS"
done_msg:
    .asciiz "ACTINFO DONE"
char_buf:
    .byte 0, 0
value_lo:
    .byte 0
value_hi:
    .byte 0
