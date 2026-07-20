.include "udos_services.inc"

.export start

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 3

.code

start:
    ldx #svc_retptr
    jsr svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    beq begin_current
    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    ldx #svc_retptr
    jsr svc_dir_begin_sc0
    lda svc_retptr+2
    cmp #tool_dir_status_ok
    beq begin_done
    lda #<msg_bad_dir
    ldy #>msg_bad_dir
    jsr print_ptr
    jsr svc_console_newline
    jmp exit_ok

begin_current:
    ldx #svc_retptr
    jsr svc_dir_begin_current

begin_done:
    lda svc_retptr
    ora svc_retptr+1
    bne have_entries
    lda #<msg_empty
    ldy #>msg_empty
    jsr print_ptr
    jsr svc_console_newline
    jmp exit_ok

have_entries:
dir_loop:
    ldx #svc_retptr
    jsr svc_dir_next
    lda svc_retptr
    ora svc_retptr+1
    beq exit_ok
    ldx #svc_retptr
    jsr svc_console_write_sc0
    jsr svc_console_newline
    jmp dir_loop

exit_ok:
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

msg_empty:
    .asciiz "EMPTY"

msg_bad_dir:
    .asciiz "BAD DIR"
