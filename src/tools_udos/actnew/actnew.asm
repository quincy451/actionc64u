.include "udos_services.inc"

.export start

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
dir_params:
    .res 3
save_params:
    .res 5
src_ptr:
    .res 2
dst_ptr:
    .res 2

.code

start:
    ldx #svc_retptr
    jsr svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    bne have_args
    lda #<msg_no_name
    ldy #>msg_no_name
    jmp fail_with_ptr

have_args:
    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    lda svc_retptr
    sta src_ptr
    lda svc_retptr+1
    sta src_ptr+1
    jsr copy_first_arg
    jsr build_paths
    lda #<project_root
    ldy #>project_root
    jsr mkdir_ptr_strict
    bcc :+
    lda #<msg_exists
    ldy #>msg_exists
    jmp fail_with_ptr
:
    lda #<project_src
    ldy #>project_src
    jsr mkdir_ptr_allow_exists
    bcc :+
    lda #<msg_mkdir_fail
    ldy #>msg_mkdir_fail
    jmp fail_with_ptr
:
    lda #<project_bin
    ldy #>project_bin
    jsr mkdir_ptr_allow_exists
    bcc :+
    lda #<msg_mkdir_fail
    ldy #>msg_mkdir_fail
    jmp fail_with_ptr
:
    lda #<project_obj
    ldy #>project_obj
    jsr mkdir_ptr_allow_exists
    bcc :+
    lda #<msg_mkdir_fail
    ldy #>msg_mkdir_fail
    jmp fail_with_ptr
:
    lda #<project_marker
    sta save_params+0
    lda #>project_marker
    sta save_params+1
    lda #<marker_text
    sta save_params+2
    lda #>marker_text
    sta save_params+3
    lda #tool_file_status_fail
    sta save_params+4
    ldx #save_params
    jsr svc_file_save_sc0
    lda save_params+4
    cmp #tool_file_status_ok
    beq :+
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
:
    lda #<project_readme
    sta save_params+0
    lda #>project_readme
    sta save_params+1
    lda #<readme_text
    sta save_params+2
    lda #>readme_text
    sta save_params+3
    lda #tool_file_status_fail
    sta save_params+4
    ldx #save_params
    jsr svc_file_save_sc0
    lda save_params+4
    cmp #tool_file_status_ok
    beq :+
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
:
    lda #<project_main
    sta save_params+0
    lda #>project_main
    sta save_params+1
    lda #<main_text
    sta save_params+2
    lda #>main_text
    sta save_params+3
    lda #tool_file_status_fail
    sta save_params+4
    ldx #save_params
    jsr svc_file_save_sc0
    lda save_params+4
    cmp #tool_file_status_ok
    beq :+
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
:
    lda #<msg_ok
    ldy #>msg_ok
    jsr print_ptr
    jsr svc_console_newline
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

mkdir_ptr_strict:
    sta dir_params+0
    sty dir_params+1
    lda #tool_dir_status_fail
    sta dir_params+2
    ldx #dir_params
    jsr svc_dir_make_sc0
    lda dir_params+2
    cmp #tool_dir_status_ok
    beq mkdir_ptr_ok
    sec
    rts

mkdir_ptr_allow_exists:
    sta dir_params+0
    sty dir_params+1
    lda #tool_dir_status_fail
    sta dir_params+2
    ldx #dir_params
    jsr svc_dir_make_sc0
    lda dir_params+2
    cmp #tool_dir_status_ok
    beq mkdir_ptr_ok
    cmp #tool_dir_status_exists
    beq mkdir_ptr_ok
    sec
    rts
mkdir_ptr_ok:
    clc
    rts

copy_first_arg:
    ldy #$00
copy_first_arg_loop:
    lda (src_ptr),y
    beq copy_first_arg_done
    cmp #' '
    beq copy_first_arg_done
    sta project_root,y
    iny
    cpy #28
    bcc copy_first_arg_loop
copy_first_arg_done:
    lda #$00
    sta project_root,y
    rts

build_paths:
    lda #<project_root
    sta src_ptr
    lda #>project_root
    sta src_ptr+1
    lda #<project_src
    sta dst_ptr
    lda #>project_src
    sta dst_ptr+1
    lda #<suffix_src
    ldy #>suffix_src
    jsr build_path_from_suffix
    lda #<project_root
    sta src_ptr
    lda #>project_root
    sta src_ptr+1
    lda #<project_bin
    sta dst_ptr
    lda #>project_bin
    sta dst_ptr+1
    lda #<suffix_bin
    ldy #>suffix_bin
    jsr build_path_from_suffix
    lda #<project_root
    sta src_ptr
    lda #>project_root
    sta src_ptr+1
    lda #<project_obj
    sta dst_ptr
    lda #>project_obj
    sta dst_ptr+1
    lda #<suffix_obj
    ldy #>suffix_obj
    jsr build_path_from_suffix
    lda #<project_root
    sta src_ptr
    lda #>project_root
    sta src_ptr+1
    lda #<project_readme
    sta dst_ptr
    lda #>project_readme
    sta dst_ptr+1
    lda #<suffix_readme
    ldy #>suffix_readme
    jsr build_path_from_suffix
    lda #<project_root
    sta src_ptr
    lda #>project_root
    sta src_ptr+1
    lda #<project_marker
    sta dst_ptr
    lda #>project_marker
    sta dst_ptr+1
    lda #<suffix_marker
    ldy #>suffix_marker
    jsr build_path_from_suffix
    lda #<project_root
    sta src_ptr
    lda #>project_root
    sta src_ptr+1
    lda #<project_main
    sta dst_ptr
    lda #>project_main
    sta dst_ptr+1
    lda #<suffix_main
    ldy #>suffix_main
    jsr build_path_from_suffix
    rts

build_path_from_suffix:
    sta svc_retptr
    sty svc_retptr+1
    ldy #$00
build_path_copy_root:
    lda (src_ptr),y
    beq build_path_copy_suffix
    sta (dst_ptr),y
    iny
    cpy #39
    bcc build_path_copy_root
    lda #$00
    sta (dst_ptr),y
    rts
build_path_copy_suffix:
    sty dir_params+0
    clc
    lda dst_ptr
    adc dir_params+0
    sta dst_ptr
    lda dst_ptr+1
    adc #$00
    sta dst_ptr+1
    lda #39
    sec
    sbc dir_params+0
    sta dir_params+1
    ldy #$00
build_path_copy_suffix_loop:
    lda (svc_retptr),y
    sta (dst_ptr),y
    beq build_path_done
    iny
    cpy dir_params+1
    bcc build_path_copy_suffix_loop
    lda #$00
    sta (dst_ptr),y
build_path_done:
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

print_ptr:
    sta svc_retptr
    sty svc_retptr+1
    ldx #svc_retptr
    jmp svc_console_write_sc0

msg_no_name:
    .asciiz "NO NAME"
msg_exists:
    .asciiz "EXISTS"
msg_mkdir_fail:
    .asciiz "MKDIR FAIL"
msg_save_fail:
    .asciiz "SAVE FAIL"
msg_ok:
    .asciiz "ACTNEW OK"

suffix_src:
    .asciiz "/SRC"
suffix_bin:
    .asciiz "/BIN"
suffix_obj:
    .asciiz "/OBJ"
suffix_readme:
    .asciiz "/README.TXT"
suffix_marker:
    .asciiz "/ACTION.PROJ"
suffix_main:
    .asciiz "/SRC/MAIN.ACT"

marker_text:
    .byte "ACTION PROJECT", 13, 0

readme_text:
    .byte "ACTION PROJECT READY", 13
    .byte 13
    .byte "SRC contains Action source.", 13
    .byte "BIN contains build outputs.", 13
    .byte "OBJ contains intermediate artifacts.", 13, 0

main_text:
    .byte "PROC MAIN()", 13
    .byte "ENDPROC", 13, 0

project_root:
    .res 40
project_src:
    .res 40
project_bin:
    .res 40
project_obj:
    .res 40
project_marker:
    .res 40
project_readme:
    .res 40
project_main:
    .res 40
