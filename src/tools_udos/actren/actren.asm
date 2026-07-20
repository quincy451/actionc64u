.include "udos_services.inc"

.export start

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
params:
    .res 5
src_ptr:
    .res 2

.code

start:
    jmp main

msg_bad_ren:
    .asciiz "BAD MOVE"
msg_no_such_file:
    .asciiz "NO SUCH FILE"
msg_move_fail:
    .asciiz "MOVE FAIL"

main:
    ldx #svc_retptr
    jsr svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    bne have_args
    lda #<msg_bad_ren
    ldy #>msg_bad_ren
    jmp fail_with_ptr

have_args:
    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    lda svc_retptr
    sta src_ptr
    lda svc_retptr+1
    sta src_ptr+1
    jsr copy_two_args
    bcc have_two_args
    lda #<msg_bad_ren
    ldy #>msg_bad_ren
    jmp fail_with_ptr

have_two_args:
    lda #<source_buffer
    sta params+0
    lda #>source_buffer
    sta params+1
    lda #<dest_buffer
    sta params+2
    lda #>dest_buffer
    sta params+3
    lda #tool_file_status_fail
    sta params+4

    ldx #params
    jsr svc_file_rename_sc0

    lda params+4
    cmp #tool_file_status_ok
    beq rename_ok
    cmp #tool_file_status_nofile
    beq rename_nofile
    lda #<msg_move_fail
    ldy #>msg_move_fail
    jmp fail_with_ptr

rename_nofile:
    lda #<msg_no_such_file
    ldy #>msg_no_such_file
    jmp fail_with_ptr

rename_ok:
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

copy_two_args:
    ldy #$00
copy_source_loop:
    lda (src_ptr),y
    beq copy_two_args_fail
    cmp #' '
    beq copy_source_done
    sta source_buffer,y
    iny
    cpy #31
    bcc copy_source_loop
copy_source_done:
    lda #$00
    sta source_buffer,y
skip_spaces:
    lda (src_ptr),y
    beq copy_two_args_fail
    cmp #' '
    bne copy_dest_start
    iny
    bne skip_spaces
copy_dest_start:
    ldx #$00
copy_dest_loop:
    lda (src_ptr),y
    beq copy_dest_done
    cmp #' '
    beq copy_dest_done
    sta dest_buffer,x
    inx
    iny
    cpx #31
    bcc copy_dest_loop
copy_dest_done:
    lda #$00
    sta dest_buffer,x
    cpx #$00
    beq copy_two_args_fail
    clc
    rts

copy_two_args_fail:
    lda #$00
    sta source_buffer
    sta dest_buffer
    sec
    rts

print_ptr:
    sta svc_retptr
    sty svc_retptr+1
    ldx #svc_retptr
    jmp svc_console_write_sc0
source_buffer:
    .res 32
dest_buffer:
    .res 32
