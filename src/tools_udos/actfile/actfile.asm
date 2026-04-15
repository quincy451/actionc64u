.include "udos_services.inc"

.export start

MANIFEST_LIMIT = 191
SOURCE_LIMIT = 255

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
file_params:
    .res 9
src_ptr:
    .res 2
scan_ptr:
    .res 2
truncated_flag:
    .res 1

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
    jsr copy_module_arg
    bcc name_ok
    lda #<msg_bad_name
    ldy #>msg_bad_name
    jmp fail_with_ptr

name_ok:
    jsr build_manifest_entry
    jsr require_loaded_project
    jsr require_manifest_entry_tracked
    jsr build_target_path
    jsr load_source_file
    bcc source_ok
    lda file_params+6
    cmp #tool_file_status_nofile
    beq missing_source
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr

missing_source:
    lda #<msg_no_file
    ldy #>msg_no_file
    jmp fail_with_ptr

source_ok:
    lda #<source_buffer
    ldy #>source_buffer
    jsr print_ptr
    jsr svc_console_newline
    lda truncated_flag
    beq exit_ok
    lda #<msg_truncated
    ldy #>msg_truncated
    jsr print_ptr
    jsr svc_console_newline

exit_ok:
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

.include "../common/action_project_module_arg.inc"
.include "../common/action_project_load.inc"
.include "../common/action_project_load_guard.inc"
.include "../common/action_project_entry.inc"
.include "../common/action_project_entry_guard.inc"
.include "../common/action_project_path.inc"
.include "../common/action_project_source.inc"

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
msg_bad_name:
    .asciiz "BAD NAME"
msg_no_project:
    .asciiz "NO PROJECT"
msg_not_in_project:
    .asciiz "NOT IN PROJECT"
msg_no_file:
    .asciiz "NO FILE"
msg_load_fail:
    .asciiz "LOAD FAIL"
msg_truncated:
    .asciiz "TRUNCATED"
project_marker:
    .asciiz "ACTION.PROJ"
module_name:
    .res 25
manifest_entry:
    .res 32
target_path:
    .res 40
manifest_buffer:
    .res MANIFEST_LIMIT+1
source_buffer:
    .res 256
