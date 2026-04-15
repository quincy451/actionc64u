.include "udos_services.inc"

.export start

MANIFEST_LIMIT = 191

FLAG_PROJECT = $01
FLAG_SRC = $02
FLAG_BIN = $04
FLAG_OBJ = $08
FLAG_TRUNCATED = $10
ACTION_PROJECT_FLAG_TRUNCATED = FLAG_TRUNCATED

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
file_params:
    .res 9
entry_ptr:
    .res 2
const_ptr:
    .res 2
scan_ptr:
    .res 2
status_flags:
    .res 1
module_count:
    .res 1
count_work:
    .res 1
compare_char:
    .res 1

.code

start:
    lda #$00
    sta status_flags
    sta module_count
    jsr load_project_manifest
    bcc have_manifest
    lda file_params+6
    cmp #tool_file_status_nofile
    beq no_manifest
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr

have_manifest:
    lda status_flags
    ora #FLAG_PROJECT
    sta status_flags
    jsr count_manifest_entries

no_manifest:
    jsr scan_current_dir

status_ready:
    jsr print_work_summary

    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

.include "../common/action_project_load.inc"
.include "../common/action_project_count.inc"
.include "../common/action_project_work_summary.inc"

print_line_ptr:
    jsr print_ptr
    jmp svc_console_newline

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

msg_project_prefix:
    .asciiz "PROJECT "
msg_src_prefix:
    .asciiz "SRC "
msg_bin_prefix:
    .asciiz "BIN "
msg_obj_prefix:
    .asciiz "OBJ "
msg_modules_prefix:
    .asciiz "MODULES "
msg_yes:
    .asciiz "YES"
msg_no:
    .asciiz "NO"
msg_load_fail:
    .asciiz "LOAD FAIL"
project_marker:
    .asciiz "ACTION.PROJ"
src_dir_name:
    .asciiz "SRC/"
bin_dir_name:
    .asciiz "BIN/"
obj_dir_name:
    .asciiz "OBJ/"
count_buffer:
    .res 5
manifest_buffer:
    .res MANIFEST_LIMIT+1
