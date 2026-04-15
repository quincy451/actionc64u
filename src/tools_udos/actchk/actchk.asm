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
line_len:
    .res 1
missing_count:
    .res 1
broken_flag:
    .res 1

.code

start:
    lda #$00
    sta status_flags
    sta module_count
    sta missing_count
    sta broken_flag
    jsr require_loaded_project
    lda status_flags
    ora #FLAG_PROJECT
    sta status_flags
    jsr count_manifest_entries
    jsr scan_current_dir
    jsr count_missing_entries
    jsr print_work_summary
    jsr print_missing_count_line

    lda status_flags
    and #FLAG_SRC|FLAG_BIN|FLAG_OBJ
    cmp #FLAG_SRC|FLAG_BIN|FLAG_OBJ
    beq :+
    lda #$01
    sta broken_flag
:   lda missing_count
    beq :+
    lda #$01
    sta broken_flag
    jsr print_missing_entries
:   lda broken_flag
    beq report_ok
    lda #<msg_broken
    ldy #>msg_broken
    jsr print_line_ptr
    lda #$01
    sta svc_retptr
    lda #$00
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

report_ok:
    lda #<msg_ok
    ldy #>msg_ok
    jsr print_line_ptr
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

print_line_ptr:
    jsr print_ptr
    jmp svc_console_newline

fail_with_ptr:
    jsr print_line_ptr
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

.include "../common/action_project_load.inc"
.include "../common/action_project_load_guard.inc"
.include "../common/action_project_count.inc"
.include "../common/action_project_path.inc"
.include "../common/action_project_work_summary.inc"
.include "../common/action_project_manifest_scan.inc"
.include "../common/action_project_check.inc"

msg_no_project:
    .asciiz "NO PROJECT"
msg_load_fail:
    .asciiz "LOAD FAIL"
msg_probe_fail:
    .asciiz "PROBE FAIL"
msg_missing_prefix:
    .asciiz "MISSING "
msg_ok:
    .asciiz "ACTCHK OK"
msg_broken:
    .asciiz "ACTCHK BROKEN"
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
line_buffer:
    .res 32
manifest_entry:
    .res 32
target_path:
    .res 40
manifest_buffer:
    .res MANIFEST_LIMIT+1
