.include "udos_services.inc"

.export start

ACTADD_PRESERVE_ZP_SERVICES = 1
MANIFEST_LIMIT = 191

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
file_params:
    .res 9
save_params = file_params
src_ptr:
    .res 2
scan_ptr:
    .res 2
entry_ptr:
    .res 2

.code

start:
    ldx #svc_retptr
    jsr actadd_svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    bne have_args
    lda #<msg_no_name
    ldy #>msg_no_name
    jmp fail_with_ptr

have_args:
    ldx #svc_retptr
    jsr actadd_svc_program_get_cmdline_ptr
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
    jsr require_manifest_entry_missing
    jsr build_target_path
    jsr build_module_stub_content
    jsr require_target_missing

save_file:
    jsr save_stub_content_to_target_or_fail

save_ok:
    jsr append_manifest_entry_and_save
    bcc report_ok
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr

report_ok:
    lda #<msg_ok
    ldy #>msg_ok
    jsr print_ptr
    jsr svc_console_newline
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

.include "../common/action_project_module_arg.inc"
.include "../common/action_project_stub_source.inc"

.include "../common/action_project_load.inc"
.include "../common/action_project_load_guard.inc"
.include "../common/action_project_entry.inc"
.include "../common/action_project_create_guard.inc"
.include "../common/action_project_manifest_commit.inc"
.include "../common/action_project_mutate.inc"
.include "../common/action_project_path.inc"
.include "../common/action_project_save_write.inc"

advance_entry_ptr:
    inc entry_ptr
    bne :+
    inc entry_ptr+1
:
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

actadd_save_zp_state:
    ldx #$00
actadd_save_zp_state_loop:
    lda $00E0,x
    sta actadd_zp_save,x
    inx
    cpx #$20
    bcc actadd_save_zp_state_loop
    rts

actadd_restore_zp_state:
    ldx #$00
actadd_restore_zp_state_loop:
    lda actadd_zp_save,x
    sta $00E0,x
    inx
    cpx #$20
    bcc actadd_restore_zp_state_loop
    rts

actadd_restore_service_status:
    lda actadd_service_status
    pha
    plp
    rts

actadd_svc_program_get_cmdline_len:
    jsr actadd_save_zp_state
    ldx #svc_retptr
    jsr svc_program_get_cmdline_len
    php
    pla
    sta actadd_service_status
    lda svc_retptr
    sta actadd_service_out+0
    lda svc_retptr+1
    sta actadd_service_out+1
    jsr actadd_restore_zp_state
    lda actadd_service_out+0
    sta svc_retptr
    lda actadd_service_out+1
    sta svc_retptr+1
    jmp actadd_restore_service_status

actadd_svc_program_get_cmdline_ptr:
    jsr actadd_save_zp_state
    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    php
    pla
    sta actadd_service_status
    lda svc_retptr
    sta actadd_service_out+0
    lda svc_retptr+1
    sta actadd_service_out+1
    jsr actadd_restore_zp_state
    lda actadd_service_out+0
    sta svc_retptr
    lda actadd_service_out+1
    sta svc_retptr+1
    jmp actadd_restore_service_status

actadd_svc_file_load_sc0:
    jsr actadd_save_zp_state
    ldx #file_params
    jsr svc_file_load_sc0
    php
    pla
    sta actadd_service_status
    lda file_params+6
    sta actadd_service_out+0
    lda file_params+7
    sta actadd_service_out+1
    lda file_params+8
    sta actadd_service_out+2
    jsr actadd_restore_zp_state
    lda actadd_service_out+0
    sta file_params+6
    lda actadd_service_out+1
    sta file_params+7
    lda actadd_service_out+2
    sta file_params+8
    jmp actadd_restore_service_status

actadd_svc_file_save_sc0:
    jsr actadd_save_zp_state
    ldx #save_params
    jsr svc_file_save_sc0
    php
    pla
    sta actadd_service_status
    lda save_params+6
    sta actadd_service_out+0
    jsr actadd_restore_zp_state
    lda actadd_service_out+0
    sta save_params+6
    jmp actadd_restore_service_status

msg_no_name:
    .asciiz "NO NAME"
msg_bad_name:
    .asciiz "BAD NAME"
msg_no_project:
    .asciiz "NO PROJECT"
msg_exists:
    .asciiz "EXISTS"
msg_probe_fail:
    .asciiz "PROBE FAIL"
msg_load_fail:
    .asciiz "LOAD FAIL"
msg_save_fail:
    .asciiz "SAVE FAIL"
msg_ok:
    .asciiz "ACTADD OK"
project_marker:
    .asciiz "ACTION.PROJ"
module_name:
    .res 25
manifest_entry:
    .res 32
target_path:
    .res 40
content_buffer:
    .res 64
manifest_buffer:
    .res MANIFEST_LIMIT+1

.segment "BSS"
actadd_service_status:
    .res 1
actadd_service_out:
    .res 3
actadd_zp_save:
    .res $20
