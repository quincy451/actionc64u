.include "udos_services.inc"

.export start

MANIFEST_LIMIT = 191

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
file_params:
    .res 9
src_ptr:
    .res 2
scan_ptr = src_ptr
line_len:
    .res 1

.code

start:
    jsr load_project_manifest
    bcc project_ok
    lda #<msg_no_project
    ldy #>msg_no_project
    jmp fail_with_ptr

project_ok:
    jsr begin_manifest_scan
    jsr manifest_scan_has_entry
    bcc have_entries
    lda #<msg_empty
    ldy #>msg_empty
    jsr print_ptr
    jsr svc_console_newline
    jmp exit_ok

have_entries:
print_loop:
    jsr copy_manifest_line_to_buffer
    bcc print_line
    jmp exit_ok

print_line:
    lda #<line_buffer
    ldy #>line_buffer
    jsr print_ptr
    jsr svc_console_newline
    jsr skip_line_breaks
    ldy #$00
    lda (src_ptr),y
    bne print_loop

exit_ok:
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

.include "../common/action_project_load.inc"
.include "../common/action_project_manifest_scan.inc"

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

msg_no_project:
    .asciiz "NO PROJECT"
msg_empty:
    .asciiz "EMPTY"
project_marker:
    .asciiz "ACTION.PROJ"
line_buffer:
    .res 32
manifest_buffer:
    .res MANIFEST_LIMIT+1
