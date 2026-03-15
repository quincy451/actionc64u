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

banner:
    .asciiz "ACTINFO ABI 1"
args_prefix:
    .asciiz "ARGS "
noargs_msg:
    .asciiz "NO ARGS"
done_msg:
    .asciiz "ACTINFO DONE"
