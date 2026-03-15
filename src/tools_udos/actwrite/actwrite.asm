.include "udos_services.inc"

.export start

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
save_params:
    .res 5
src_ptr:
    .res 2

.code

start:
    ldx #svc_retptr
    jsr svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    bne have_args
    lda #<msg_no_file
    ldy #>msg_no_file
    bne fail_with_ptr

have_args:
    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    lda svc_retptr
    sta src_ptr
    lda svc_retptr+1
    sta src_ptr+1
    jsr copy_first_arg

    lda #<filename_buffer
    sta save_params+0
    lda #>filename_buffer
    sta save_params+1
    lda #<content_buffer
    sta save_params+2
    lda #>content_buffer
    sta save_params+3
    lda #tool_file_status_fail
    sta save_params+4

    ldx #save_params
    jsr svc_file_save_sc0

    lda save_params+4
    cmp #tool_file_status_ok
    beq save_ok
    lda #<msg_save_fail
    ldy #>msg_save_fail
    bne fail_with_ptr

save_ok:
    lda #<msg_ok
    ldy #>msg_ok
    jsr print_ptr
    jsr svc_console_newline
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

fail_with_ptr:
    jsr print_ptr
    jsr svc_console_newline
    lda #$01
    sta svc_retptr
    lda #$00
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

copy_first_arg:
    ldy #$00
copy_first_arg_loop:
    lda (src_ptr),y
    beq copy_first_arg_done
    cmp #' '
    beq copy_first_arg_done
    sta filename_buffer,y
    iny
    cpy #31
    bcc copy_first_arg_loop
copy_first_arg_done:
    lda #$00
    sta filename_buffer,y
    rts

print_ptr:
    sta svc_retptr
    sty svc_retptr+1
    ldx #svc_retptr
    jmp svc_console_write_sc0

msg_no_file:
    .asciiz "NO FILE"
msg_save_fail:
    .asciiz "SAVE FAIL"
msg_ok:
    .asciiz "ACTWRITE OK"
content_buffer:
    .asciiz "ACTION WRITE OK"
filename_buffer:
    .res 32
