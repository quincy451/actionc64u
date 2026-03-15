.include "udos_services.inc"

.export start

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
dir_params:
    .res 3
src_ptr:
    .res 2

.code

start:
    ldx #svc_retptr
    jsr svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    bne have_args
    lda #<msg_no_dir
    ldy #>msg_no_dir
    bne fail_with_ptr

have_args:
    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    lda svc_retptr
    sta src_ptr
    lda svc_retptr+1
    sta src_ptr+1
    jsr copy_first_arg

    lda #<dirname_buffer
    sta dir_params+0
    lda #>dirname_buffer
    sta dir_params+1
    lda #tool_dir_status_fail
    sta dir_params+2

    ldx #dir_params
    jsr svc_dir_remove_sc0

    lda dir_params+2
    cmp #tool_dir_status_ok
    beq rmdir_ok
    cmp #tool_dir_status_nofile
    beq rmdir_nofile
    cmp #tool_dir_status_not_empty
    beq rmdir_not_empty
    cmp #tool_dir_status_busy
    beq rmdir_busy
    lda #<msg_rmdir_fail
    ldy #>msg_rmdir_fail
    bne fail_with_ptr

rmdir_nofile:
    lda #<msg_no_such_dir
    ldy #>msg_no_such_dir
    bne fail_with_ptr

rmdir_not_empty:
    lda #<msg_not_empty
    ldy #>msg_not_empty
    bne fail_with_ptr

rmdir_busy:
    lda #<msg_busy
    ldy #>msg_busy
    bne fail_with_ptr

rmdir_ok:
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
    sta dirname_buffer,y
    iny
    cpy #31
    bcc copy_first_arg_loop
copy_first_arg_done:
    lda #$00
    sta dirname_buffer,y
    rts

print_ptr:
    sta svc_retptr
    sty svc_retptr+1
    ldx #svc_retptr
    jmp svc_console_write_sc0

msg_no_dir:
    .asciiz "NO DIR"
msg_no_such_dir:
    .asciiz "NO SUCH DIR"
msg_not_empty:
    .asciiz "DIR NOT EMPTY"
msg_busy:
    .asciiz "DIR BUSY"
msg_rmdir_fail:
    .asciiz "RMDIR FAIL"
msg_ok:
    .asciiz "ACTRMDIR OK"
dirname_buffer:
    .res 32
