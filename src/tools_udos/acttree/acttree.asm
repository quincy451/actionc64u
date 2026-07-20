.include "udos_services.inc"
.include "udos_overlay.inc"

.export start
.export udos_overlay_header
.export udos_overlay_end

PATH_LEN = 64
STACK_DEPTH = 10
ASCII_SLASH = $2F

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 3
src_ptr:
    .res 2
dst_ptr:
    .res 2
slot_ptr:
    .res 2
entry_ptr:
    .res 2
slot_index:
    .res 1

.code

udos_overlay_header:
    .byte 'U','D','O','V'
    .byte UDOS_OVERLAY_FORMAT_VERSION
    .byte udos_tool_abi_version
    .byte UDOS_OVERLAY_COMMAND_TREE
    .byte $00
    .word UDOS_OVERLAY_LOAD_ADDR
    .word start
    .word udos_overlay_end - udos_overlay_header

start:
    lda #$00
    sta stack_count
    sta child_is_dir
    ldx #svc_retptr
    jsr svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    beq start_current_dir

    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    lda svc_retptr
    sta src_ptr
    lda svc_retptr+1
    sta src_ptr+1
    lda #<current_path
    sta dst_ptr
    lda #>current_path
    sta dst_ptr+1
    jsr copy_ptr_to_path
    jmp start_push_root

start_current_dir:
    lda #$00
    sta current_path

start_push_root:
    jsr push_current_path
    bcc main_loop
    lda #<msg_too_deep
    ldy #>msg_too_deep
    jmp fail_with_ptr

main_loop:
    lda stack_count
    bne main_loop_have_path
    jmp exit_ok
main_loop_have_path:
    jsr pop_current_path
    jsr enumerate_current_path
    jmp main_loop

enumerate_current_path:
    lda current_path
    beq enumerate_current_dir
    lda #<current_path
    sta svc_retptr
    lda #>current_path
    sta svc_retptr+1
    ldx #svc_retptr
    jsr svc_dir_begin_sc0
    lda svc_retptr+2
    cmp #tool_dir_status_ok
    beq enumerate_have_status
    lda #<msg_bad_dir
    ldy #>msg_bad_dir
    jsr print_ptr
    jsr svc_console_newline
    rts

enumerate_current_dir:
    ldx #svc_retptr
    jsr svc_dir_begin_current

enumerate_have_status:
    lda svc_retptr
    ora svc_retptr+1
    bne enumerate_loop
    rts

enumerate_loop:
    ldx #svc_retptr
    jsr svc_dir_next
    lda svc_retptr
    ora svc_retptr+1
    beq enumerate_done
    lda svc_retptr
    sta entry_ptr
    lda svc_retptr+1
    sta entry_ptr+1
    jsr build_child_path
    lda #<child_path
    ldy #>child_path
    jsr print_ptr
    jsr svc_console_newline
    lda child_is_dir
    beq enumerate_loop
    jsr strip_child_trailing_slash
    jsr push_child_path
    bcc enumerate_loop
    lda #<msg_too_deep
    ldy #>msg_too_deep
    jsr print_ptr
    jsr svc_console_newline
    jmp enumerate_loop

enumerate_done:
    rts

build_child_path:
    lda #$00
    sta child_is_dir
    ldx #$00
    ldy #$00
build_child_current_loop:
    lda current_path,y
    beq build_child_current_done
    cpx #PATH_LEN-2
    bcs build_child_current_done
    sta child_path,x
    inx
    iny
    bne build_child_current_loop

build_child_current_done:
    cpx #$00
    beq build_child_copy_entry
    lda child_path-1,x
    cmp #ASCII_SLASH
    beq build_child_copy_entry
    lda #ASCII_SLASH
    sta child_path,x
    inx

build_child_copy_entry:
    ldy #$00
build_child_entry_loop:
    lda (entry_ptr),y
    beq build_child_done
    cpx #PATH_LEN-1
    bcs build_child_done
    sta child_path,x
    cmp #ASCII_SLASH
    bne :+
    lda #$01
    sta child_is_dir
:
    inx
    iny
    bne build_child_entry_loop

build_child_done:
    lda #$00
    sta child_path,x
    rts

strip_child_trailing_slash:
    ldy #$00
strip_child_loop:
    lda child_path,y
    beq strip_child_at_end
    iny
    cpy #PATH_LEN
    bcc strip_child_loop
    rts
strip_child_at_end:
    cpy #$00
    beq strip_child_done
    dey
    lda child_path,y
    cmp #ASCII_SLASH
    bne strip_child_done
    lda #$00
    sta child_path,y
strip_child_done:
    rts

push_current_path:
    lda #<current_path
    sta src_ptr
    lda #>current_path
    sta src_ptr+1
    jmp push_path_ptr

push_child_path:
    lda #<child_path
    sta src_ptr
    lda #>child_path
    sta src_ptr+1

push_path_ptr:
    lda stack_count
    cmp #STACK_DEPTH
    bcs push_path_fail
    sta slot_index
    jsr set_slot_ptr
    lda slot_ptr
    sta dst_ptr
    lda slot_ptr+1
    sta dst_ptr+1
    jsr copy_ptr_to_path
    inc stack_count
    clc
    rts
push_path_fail:
    sec
    rts

pop_current_path:
    dec stack_count
    lda stack_count
    sta slot_index
    jsr set_slot_ptr
    lda slot_ptr
    sta src_ptr
    lda slot_ptr+1
    sta src_ptr+1
    lda #<current_path
    sta dst_ptr
    lda #>current_path
    sta dst_ptr+1
    jmp copy_ptr_to_path

set_slot_ptr:
    lda #<path_stack
    sta slot_ptr
    lda #>path_stack
    sta slot_ptr+1
    ldx slot_index
    beq set_slot_done
set_slot_loop:
    clc
    lda slot_ptr
    adc #PATH_LEN
    sta slot_ptr
    lda slot_ptr+1
    adc #$00
    sta slot_ptr+1
    dex
    bne set_slot_loop
set_slot_done:
    rts

copy_ptr_to_path:
    ldy #$00
copy_ptr_loop:
    lda (src_ptr),y
    sta (dst_ptr),y
    beq copy_ptr_done
    iny
    cpy #PATH_LEN-1
    bcc copy_ptr_loop
    lda #$00
    sta (dst_ptr),y
copy_ptr_done:
    rts

fail_with_ptr:
    jsr print_ptr
    jsr svc_console_newline
    lda #$01
    sta svc_retptr
    lda #$00
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

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

msg_bad_dir:
    .asciiz "BAD DIR"
msg_too_deep:
    .asciiz "TREE TOO DEEP"

stack_count:
    .byte $00
child_is_dir:
    .byte $00
current_path:
    .res PATH_LEN
child_path:
    .res PATH_LEN
path_stack:
    .res PATH_LEN * STACK_DEPTH

udos_overlay_end:
