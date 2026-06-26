.include "udos_services.inc"

.export start

MANIFEST_LIMIT = 191
SOURCE_LIMIT = 255
TEST_PAYLOAD_LEN = 18
.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
file_params:
    .res 9
save_params = file_params
src_ptr = svc_retptr
scan_ptr:
    .res 2
truncated_flag:
    .res 1

.code

start:
    jsr init_module_name
    jsr require_loaded_project
    jsr build_manifest_entry
    jsr require_manifest_entry_tracked
    jsr build_object_target_path
    lda #<target_path
    ldy #>target_path
    jsr load_seeded_file_or_fail
    bcc :+
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
:   lda truncated_flag
    beq :+
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
:   jsr build_test_binary_payload
    jsr build_fixed_binary_target_path
    jsr save_text_to_target
    bcc save_ok
    jmp save_fail

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

init_module_name:
    ldx #svc_retptr
    jsr act2save_svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    beq init_module_name_default
    ldx #svc_retptr
    jsr act2save_svc_program_get_cmdline_ptr
    lda svc_retptr
    sta src_ptr
    lda svc_retptr+1
    sta src_ptr+1
    jsr copy_module_arg
    bcc init_module_name_done
    lda #<msg_bad_name
    ldy #>msg_bad_name
    jmp fail_with_ptr
init_module_name_default:
    ldy #$00
init_module_name_default_loop:
    lda default_module_name,y
    sta module_name,y
    beq init_module_name_done
    iny
    bne init_module_name_default_loop
init_module_name_done:
    rts

copy_ptr_to_target_path:
    sta src_ptr
    sty src_ptr+1
    ldy #$00
copy_ptr_to_target_path_loop:
    lda (src_ptr),y
    sta target_path,y
    beq copy_ptr_to_target_path_done
    iny
    cpy #40
    bcc copy_ptr_to_target_path_loop
copy_ptr_to_target_path_done:
    rts

build_fixed_binary_target_path:
    lda #<fixed_binary_name
    ldy #>fixed_binary_name
    jmp copy_ptr_to_target_path

uppercase_ascii:
    cmp #'a'
    bcc uppercase_ascii_done
    cmp #'z'+1
    bcs uppercase_ascii_done
    and #$DF
uppercase_ascii_done:
    rts

save_text_to_target:
    lda #<target_path
    sta file_params+0
    lda #>target_path
    sta file_params+1
    lda #tool_file_status_fail
    sta file_params+2
    ldx #file_params
    jsr act2save_svc_file_write_begin_sc0
    lda file_params+2
    cmp #tool_file_status_ok
    bne save_text_to_target_fail

    lda #<save_buffer
    sta file_params+0
    lda #>save_buffer
    sta file_params+1
    lda #<TEST_PAYLOAD_LEN
    sta file_params+2
    lda #>TEST_PAYLOAD_LEN
    sta file_params+3
    lda #tool_file_status_fail
    sta file_params+4
    ldx #file_params
    jsr act2save_svc_file_write_chunk_sc0
    lda file_params+4
    cmp #tool_file_status_ok
    bne save_text_to_target_fail_close

    lda #tool_file_status_fail
    sta file_params+0
    ldx #file_params
    jsr act2save_svc_file_write_close_sc0
    lda file_params+0
    cmp #tool_file_status_ok
    bne save_text_to_target_fail
save_text_to_target_ok:
    clc
    rts
save_text_to_target_fail_close:
    lda #tool_file_status_fail
    sta file_params+0
    ldx #file_params
    jsr act2save_svc_file_write_close_sc0
save_text_to_target_fail:
    sec
    rts

build_test_binary_payload:
    ldx #$00
build_test_binary_payload_loop:
    lda test_binary_payload,x
    sta save_buffer,x
    cpx #TEST_PAYLOAD_LEN-1
    beq build_test_binary_payload_done
    inx
    bne build_test_binary_payload_loop
build_test_binary_payload_done:
    rts

try_load_seeded_file:
    sta src_ptr
    sty src_ptr+1
    lda #$00
    sta truncated_flag
    lda src_ptr
    sta file_params+0
    lda src_ptr+1
    sta file_params+1
    lda #<source_buffer
    sta file_params+2
    lda #>source_buffer
    sta file_params+3
    lda #<SOURCE_LIMIT
    sta file_params+4
    lda #>SOURCE_LIMIT
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    sta file_params+8
    ldx #file_params
    jsr act2save_svc_file_load_sc0
    lda file_params+6
    cmp #tool_file_status_ok
    beq try_load_seeded_file_done
    cmp #tool_file_status_too_large
    bne try_load_seeded_file_fail
    lda #$01
    sta truncated_flag
try_load_seeded_file_done:
    ldy file_params+7
    lda #$00
    sta source_buffer,y
    clc
    rts
try_load_seeded_file_fail:
    sec
    rts

load_seeded_file_or_fail:
    jsr try_load_seeded_file
    bcc load_seeded_file_or_fail_done
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_seeded_file_or_fail_done:
    rts

save_fail:
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr

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

act2save_save_zp_state:
    ldx #$00
act2save_save_zp_state_loop:
    lda $00E0,x
    sta act2save_zp_save,x
    inx
    cpx #$0E
    bcc act2save_save_zp_state_loop
    rts

act2save_restore_zp_state:
    ldx #$00
act2save_restore_zp_state_loop:
    lda act2save_zp_save,x
    sta $00E0,x
    inx
    cpx #$0E
    bcc act2save_restore_zp_state_loop
    rts

act2save_restore_service_status:
    lda act2save_service_status
    pha
    plp
    rts

act2save_svc_program_get_cmdline_len:
    jsr act2save_save_zp_state
    ldx #svc_retptr
    jsr svc_program_get_cmdline_len
    php
    pla
    sta act2save_service_status
    lda svc_retptr
    sta act2save_service_out+0
    lda svc_retptr+1
    sta act2save_service_out+1
    jsr act2save_restore_zp_state
    lda act2save_service_out+0
    sta svc_retptr
    lda act2save_service_out+1
    sta svc_retptr+1
    jmp act2save_restore_service_status

act2save_svc_program_get_cmdline_ptr:
    jsr act2save_save_zp_state
    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    php
    pla
    sta act2save_service_status
    lda svc_retptr
    sta act2save_service_out+0
    lda svc_retptr+1
    sta act2save_service_out+1
    jsr act2save_restore_zp_state
    lda act2save_service_out+0
    sta svc_retptr
    lda act2save_service_out+1
    sta svc_retptr+1
    jmp act2save_restore_service_status

act2save_svc_file_load_sc0:
    jsr act2save_save_zp_state
    ldx #file_params
    jsr svc_file_load_sc0
    php
    pla
    sta act2save_service_status
    lda file_params+6
    sta act2save_service_out+0
    lda file_params+7
    sta act2save_service_out+1
    lda file_params+8
    sta act2save_service_out+2
    jsr act2save_restore_zp_state
    lda act2save_service_out+0
    sta file_params+6
    lda act2save_service_out+1
    sta file_params+7
    lda act2save_service_out+2
    sta file_params+8
    jmp act2save_restore_service_status

act2save_svc_file_write_begin_sc0:
    jsr act2save_save_zp_state
    ldx #file_params
    jsr svc_file_write_begin_sc0
    php
    pla
    sta act2save_service_status
    lda file_params+2
    sta act2save_service_out+0
    jsr act2save_restore_zp_state
    lda act2save_service_out+0
    sta file_params+2
    jmp act2save_restore_service_status

act2save_svc_file_write_chunk_sc0:
    jsr act2save_save_zp_state
    ldx #file_params
    jsr svc_file_write_chunk_sc0
    php
    pla
    sta act2save_service_status
    lda file_params+4
    sta act2save_service_out+0
    jsr act2save_restore_zp_state
    lda act2save_service_out+0
    sta file_params+4
    jmp act2save_restore_service_status

act2save_svc_file_write_close_sc0:
    jsr act2save_save_zp_state
    ldx #file_params
    jsr svc_file_write_close_sc0
    php
    pla
    sta act2save_service_status
    lda file_params+0
    sta act2save_service_out+0
    jsr act2save_restore_zp_state
    lda act2save_service_out+0
    sta file_params+0
    jmp act2save_restore_service_status

.include "../common/action_project_entry.inc"
.include "../common/action_project_entry_guard.inc"
.include "../common/action_project_load_guard.inc"
.include "../common/action_project_load.inc"
.include "../common/action_project_source.inc"
.include "../common/action_project_module_arg.inc"
.include "../common/action_project_path.inc"
.include "../common/action_project_object_path.inc"

msg_bad_name:
    .asciiz "BAD NAME"
msg_save_fail:
    .asciiz "SAVE FAIL"
msg_load_fail:
    .asciiz "LOAD FAIL"
msg_no_project:
    .asciiz "NO PROJECT"
msg_not_in_project:
    .asciiz "NOT IN PROJECT"
msg_ok:
    .asciiz "ACT2SAVE OK"
default_module_name:
    .asciiz "MAIN"
project_marker:
    .asciiz "ACTION.PROJ"
load_name_main:
    .asciiz "OBJ/MAIN.OBJ"
load_name_work:
    .asciiz "OBJ/W.OBJ"
fixed_object_name:
fixed_binary_name:
    .asciiz "BIN/MAIN.PRG"
test_binary_payload:
    .byte $00,$10,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C
    .byte $0F,$CF

LOAD_BUFFER_LEN = 127

.segment "CODE"
; Keep the buffers at ACTC-like relative offsets so this proof exercises the
; same save/load layout class without depending on scratch-memory diagnostics.
actc_layout_pad_to_module_name:
    .res $0EBF
module_name:
    .res 25
target_path:
    .res 40
manifest_entry:
    .res 32
actc_layout_pad_to_load_buffer:
    .res $0074
load_buffer:
    .res LOAD_BUFFER_LEN
actc_layout_pad_to_save_buffer:
    .res $01D5
save_buffer:
    .res TEST_PAYLOAD_LEN
source_buffer:
    .res SOURCE_LIMIT+1
manifest_buffer:
    .res MANIFEST_LIMIT+1

.segment "BSS"
act2save_service_status:
    .res 1
act2save_service_out:
    .res 3
act2save_zp_save:
    .res $0E
