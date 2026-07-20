; Native 6502 execution controller. The debugger and target alternate in low
; memory; this overlay remains above the linker output ceiling and performs
; the REU swaps without calling code that may have just been overwritten.

REU_COMMAND = $DF01
REU_C64ADDR_LO = $DF02
REU_C64ADDR_HI = $DF03
REU_REUADDR_LO = $DF04
REU_REUADDR_HI = $DF05
REU_REUADDR_BANK = $DF06
REU_COUNT_LO = $DF07
REU_COUNT_HI = $DF08
REU_IRQMASK = $DF09
REU_CONTROL = $DF0A
REU_TRIGGER = $FF00
REU_STORE = $EC
REU_FETCH = $ED

NATIVE_DEBUG_REU_BANK = $05
NATIVE_TARGET_REU_BANK = $06
NATIVE_SNAPSHOT_C64 = $0002
NATIVE_SNAPSHOT_LEN = $9FFE
NATIVE_TARGET_LIMIT = $A000
NATIVE_BRK_VECTOR = $0316
NATIVE_EXIT_SERVICE = $CF0F
NATIVE_PATCH_MAX = BREAKPOINT_MAX + 1
NATIVE_CALLSTACK_MAX = 16

NATIVE_CMD_STEP = 1
NATIVE_CMD_CONTINUE = 2
NATIVE_CMD_STEP_OVER = 3
NATIVE_CMD_STEP_OUT = 4

.macro native_reu_fixed command, c64_addr, reu_addr, reu_bank, byte_count
    lda #<c64_addr
    sta REU_C64ADDR_LO
    lda #>c64_addr
    sta REU_C64ADDR_HI
    lda #<reu_addr
    sta REU_REUADDR_LO
    lda #>reu_addr
    sta REU_REUADDR_HI
    lda #reu_bank
    sta REU_REUADDR_BANK
    lda #<byte_count
    sta REU_COUNT_LO
    lda #>byte_count
    sta REU_COUNT_HI
    lda #$00
    sta REU_IRQMASK
    sta REU_CONTROL
    lda #command
    sta REU_COMMAND
    lda #$30
    sta C64_MEMCFG
    lda #$00
    sta REU_TRIGGER
    lda #$36
    sta C64_MEMCFG
.endmacro

debug_step_instruction:
    lda #NATIVE_CMD_STEP
    jmp native_launch_command

debug_continue_execution:
    lda #NATIVE_CMD_CONTINUE
    jmp native_launch_command

debug_step_over_execution:
    lda #NATIVE_CMD_STEP_OVER
    jmp native_launch_command

debug_step_out_execution:
    lda #NATIVE_CMD_STEP_OUT
    jmp native_launch_command

native_launch_command:
    sta native_command
    lda actdbg_native_done
    ora actdbg_native_failed
    beq :+
    clc
    rts
:
    jsr native_copy_resident_state
    tsx
    stx native_debugger_sp
    native_reu_fixed REU_STORE, NATIVE_SNAPSHOT_C64, $0000, NATIVE_DEBUG_REU_BANK, NATIVE_SNAPSHOT_LEN
    lda native_target_valid_copy
    beq native_load_initial_target
    jmp native_restore_target

native_load_initial_target:
    jsr native_copy_staged_prg
    bcc :+
    jmp native_launch_restore_failed
:
    lda #<(native_target_completed-1)
    sta $01FE
    lda #>(native_target_completed-1)
    sta $01FF
    lda #$FD
    sta native_cpu_sp
    jmp native_target_ready

native_restore_target:
    native_reu_fixed REU_FETCH, NATIVE_SNAPSHOT_C64, $0000, NATIVE_TARGET_REU_BANK, NATIVE_SNAPSHOT_LEN
    jmp native_target_ready

native_target_ready:
    sei
    lda #<native_brk_handler
    sta NATIVE_BRK_VECTOR
    lda #>native_brk_handler
    sta NATIVE_BRK_VECTOR+1
    lda #$00
    sta native_patch_count
    sta native_auto_continue
    jsr native_install_exit_patch
    bcs native_target_setup_failed
    lda native_command
    cmp #NATIVE_CMD_CONTINUE
    beq native_setup_continue
    cmp #NATIVE_CMD_STEP_OUT
    beq native_setup_step_out
    jsr native_compute_step_target
    bcs native_target_setup_failed
    jsr native_patch_next_target
    bcs native_target_setup_failed
    jsr native_track_single_step
    jmp native_resume_target

native_setup_continue:
    jsr native_current_pc_is_breakpoint
    bcc native_setup_continue_all
    lda #$01
    sta native_auto_continue
    jsr native_compute_step_target
    bcs native_target_setup_failed
    jsr native_patch_next_target
    bcs native_target_setup_failed
    jmp native_resume_target
native_setup_continue_all:
    jsr native_install_user_breakpoints
    bcs native_target_setup_failed
    jmp native_resume_target

native_setup_step_out:
    jsr native_compute_return_target
    bcs native_target_setup_failed
    jsr native_patch_next_target
    bcs native_target_setup_failed
    lda native_call_depth
    beq :+
    dec native_call_depth
:
    jmp native_resume_target

native_target_setup_failed:
    jsr native_restore_patches
native_launch_restore_failed:
    lda #$01
    sta native_result_failed
    native_reu_fixed REU_FETCH, NATIVE_SNAPSHOT_C64, $0000, NATIVE_DEBUG_REU_BANK, NATIVE_SNAPSHOT_LEN
    jmp native_return_to_debugger

native_copy_resident_state:
    lda actdbg_current_pc_lo
    sta native_pc_lo
    lda actdbg_current_pc_hi
    sta native_pc_hi
    lda actdbg_native_a
    sta native_cpu_a
    lda actdbg_native_x
    sta native_cpu_x
    lda actdbg_native_y
    sta native_cpu_y
    lda actdbg_native_p
    sta native_cpu_p
    lda actdbg_native_sp
    sta native_cpu_sp
    lda actdbg_native_target_valid
    sta native_target_valid_copy
    lda actdbg_native_call_depth
    cmp #NATIVE_CALLSTACK_MAX+1
    bcc :+
    lda #$00
:
    sta native_call_depth
    lda actdbg_prg_header+0
    sta native_load_lo
    lda actdbg_prg_header+1
    sta native_load_hi
    sec
    lda actdbg_prg_stage_len_lo
    sbc #$02
    sta native_payload_len_lo
    lda actdbg_prg_stage_len_hi
    sbc #$00
    sta native_payload_len_hi
    lda #$00
    sta native_result_failed
    ldx #$00
native_copy_breakpoints_loop:
    lda actdbg_break_active,x
    sta native_break_active,x
    lda actdbg_break_pc_lo,x
    sta native_break_lo,x
    lda actdbg_break_pc_hi,x
    sta native_break_hi,x
    inx
    cpx #BREAKPOINT_MAX
    bcc native_copy_breakpoints_loop
    ldx #$00
native_copy_callstack_loop:
    lda actdbg_native_callstack_lo,x
    sta native_callstack_lo,x
    lda actdbg_native_callstack_hi,x
    sta native_callstack_hi,x
    inx
    cpx #NATIVE_CALLSTACK_MAX
    bcc native_copy_callstack_loop
    rts

native_track_single_step:
    lda native_command
    cmp #NATIVE_CMD_STEP
    bne native_track_single_step_done
    lda native_opcode
    cmp #$20
    beq native_track_jsr
    cmp #$60
    bne native_track_single_step_done
    lda native_call_depth
    beq native_track_single_step_done
    dec native_call_depth
    rts
native_track_jsr:
    ldx native_call_depth
    cpx #NATIVE_CALLSTACK_MAX
    bcs native_track_single_step_done
    clc
    lda native_pc_lo
    adc #$03
    sta native_callstack_lo,x
    lda native_pc_hi
    adc #$00
    sta native_callstack_hi,x
    inc native_call_depth
native_track_single_step_done:
    rts

native_copy_staged_prg:
    lda native_payload_len_lo
    ora native_payload_len_hi
    bne :+
    jmp native_copy_staged_prg_fail
:
    clc
    lda native_load_lo
    adc native_payload_len_lo
    sta native_target_end_lo
    lda native_load_hi
    adc native_payload_len_hi
    sta native_target_end_hi
    bcc :+
    jmp native_copy_staged_prg_fail
:
    lda native_target_end_hi
    cmp #>NATIVE_TARGET_LIMIT
    bcc native_copy_staged_prg_limit_ok
    beq native_copy_staged_prg_limit_edge
    jmp native_copy_staged_prg_fail
native_copy_staged_prg_limit_edge:
    lda native_target_end_lo
    beq native_copy_staged_prg_limit_ok
    jmp native_copy_staged_prg_fail
native_copy_staged_prg_limit_ok:
    lda native_pc_hi
    cmp native_load_hi
    bcs :+
    jmp native_copy_staged_prg_fail
:
    bne :+
    lda native_pc_lo
    cmp native_load_lo
    bcs :+
    jmp native_copy_staged_prg_fail
:
    lda native_pc_hi
    cmp native_target_end_hi
    bcc native_copy_staged_prg_entry_ok
    beq native_copy_staged_prg_entry_edge
    jmp native_copy_staged_prg_fail
native_copy_staged_prg_entry_edge:
    lda native_pc_lo
    cmp native_target_end_lo
    bcc native_copy_staged_prg_entry_ok
    jmp native_copy_staged_prg_fail
native_copy_staged_prg_entry_ok:
    lda native_load_lo
    sta REU_C64ADDR_LO
    lda native_load_hi
    sta REU_C64ADDR_HI
    lda #$02
    sta REU_REUADDR_LO
    lda #$00
    sta REU_REUADDR_HI
    sta REU_REUADDR_BANK
    lda native_payload_len_lo
    sta REU_COUNT_LO
    lda native_payload_len_hi
    sta REU_COUNT_HI
    lda #$00
    sta REU_IRQMASK
    sta REU_CONTROL
    lda #REU_FETCH
    sta REU_COMMAND
    lda #$30
    sta C64_MEMCFG
    lda #$00
    sta REU_TRIGGER
    lda #$36
    sta C64_MEMCFG
    clc
    rts
native_copy_staged_prg_fail:
    sec
    rts

native_compute_step_target:
    ldy #$00
    jsr native_read_pc_y
    sta native_opcode
    cmp #$00
    bne :+
    jmp native_compute_target_fail
:
    cmp #$20
    bne :+
    jmp native_compute_jsr_target
:
    cmp #$4C
    bne :+
    jmp native_compute_absolute_target
:
    cmp #$6C
    bne :+
    jmp native_compute_indirect_target
:
    cmp #$60
    bne :+
    jmp native_compute_return_target
:
    cmp #$40
    bne :+
    jmp native_compute_rti_target
:
    and #$1F
    cmp #$10
    bne :+
    jmp native_compute_branch_target
:
    ldx native_opcode
    lda native_opcode_lengths,x
    bne :+
    jmp native_compute_target_fail
:
    clc
    adc native_pc_lo
    sta native_next_lo
    lda native_pc_hi
    adc #$00
    sta native_next_hi
    clc
    rts

native_compute_jsr_target:
    lda native_command
    cmp #NATIVE_CMD_STEP_OVER
    bne native_compute_absolute_target
    lda #$03
    clc
    adc native_pc_lo
    sta native_next_lo
    lda native_pc_hi
    adc #$00
    sta native_next_hi
    clc
    rts

native_compute_absolute_target:
    ldy #$01
    jsr native_read_pc_y
    sta native_next_lo
    iny
    jsr native_read_pc_y
    sta native_next_hi
    clc
    rts

native_compute_indirect_target:
    ldy #$01
    jsr native_read_pc_y
    sta native_memory_read+1
    sta native_indirect_lo
    iny
    jsr native_read_pc_y
    sta native_memory_read+2
    sta native_indirect_hi
native_memory_read:
    lda $FFFF
    sta native_next_lo
    inc native_memory_read+1
    bne :+
    lda native_indirect_lo
    sta native_memory_read+1
    inc native_memory_read+2
:
    lda $FFFF
    sta native_next_hi
    clc
    rts

native_compute_return_target:
    ldx native_cpu_sp
    cpx #$FE
    bcc :+
    jmp native_compute_target_fail
:
    lda $0101,x
    sta native_next_lo
    lda $0102,x
    sta native_next_hi
    inc native_next_lo
    bne :+
    inc native_next_hi
:
    clc
    rts

native_compute_rti_target:
    ldx native_cpu_sp
    cpx #$FC
    bcc :+
    jmp native_compute_target_fail
:
    lda $0102,x
    sta native_next_lo
    lda $0103,x
    sta native_next_hi
    clc
    rts

native_compute_branch_target:
    jsr native_branch_is_taken
    bcs native_compute_branch_taken
    clc
    lda native_pc_lo
    adc #$02
    sta native_next_lo
    lda native_pc_hi
    adc #$00
    sta native_next_hi
    clc
    rts
native_compute_branch_taken:
    ldy #$01
    jsr native_read_pc_y
    sta native_branch_offset
    clc
    lda native_pc_lo
    adc #$02
    sta native_next_lo
    lda native_pc_hi
    adc #$00
    sta native_next_hi
    lda native_branch_offset
    bpl :+
    dec native_next_hi
:
    clc
    adc native_next_lo
    sta native_next_lo
    bcc :+
    inc native_next_hi
:
    clc
    rts

native_branch_is_taken:
    lda native_opcode
    cmp #$10
    beq native_branch_bpl
    cmp #$30
    beq native_branch_bmi
    cmp #$50
    beq native_branch_bvc
    cmp #$70
    beq native_branch_bvs
    cmp #$90
    beq native_branch_bcc
    cmp #$B0
    beq native_branch_bcs
    cmp #$D0
    beq native_branch_bne
    lda native_cpu_p
    and #$02
    beq native_branch_no
    sec
    rts
native_branch_bpl:
    lda native_cpu_p
    and #$80
    beq native_branch_yes
    bne native_branch_no
native_branch_bmi:
    lda native_cpu_p
    and #$80
    bne native_branch_yes
    beq native_branch_no
native_branch_bvc:
    lda native_cpu_p
    and #$40
    beq native_branch_yes
    bne native_branch_no
native_branch_bvs:
    lda native_cpu_p
    and #$40
    bne native_branch_yes
    beq native_branch_no
native_branch_bcc:
    lda native_cpu_p
    and #$01
    beq native_branch_yes
    bne native_branch_no
native_branch_bcs:
    lda native_cpu_p
    and #$01
    bne native_branch_yes
    beq native_branch_no
native_branch_bne:
    lda native_cpu_p
    and #$02
    beq native_branch_yes
native_branch_no:
    clc
    rts
native_branch_yes:
    sec
    rts

native_compute_target_fail:
    sec
    rts

native_read_pc_y:
    lda native_pc_lo
    sta native_read_pc_operand+1
    lda native_pc_hi
    sta native_read_pc_operand+2
native_read_pc_operand:
    lda $FFFF,y
    rts

native_patch_next_target:
    lda native_next_lo
    ldy native_next_hi
    jmp native_patch_address

native_install_exit_patch:
    lda #<NATIVE_EXIT_SERVICE
    ldy #>NATIVE_EXIT_SERVICE
    jmp native_patch_address

native_install_user_breakpoints:
    ldx #$00
native_install_user_breakpoints_loop:
    lda native_break_active,x
    beq native_install_user_breakpoints_next
    lda native_break_lo,x
    ldy native_break_hi,x
    stx native_break_index
    jsr native_patch_address
    bcs native_install_user_breakpoints_fail
    ldx native_break_index
native_install_user_breakpoints_next:
    inx
    cpx #BREAKPOINT_MAX
    bcc native_install_user_breakpoints_loop
    clc
    rts
native_install_user_breakpoints_fail:
    sec
    rts

native_current_pc_is_breakpoint:
    ldx #$00
native_current_pc_is_breakpoint_loop:
    lda native_break_active,x
    beq native_current_pc_is_breakpoint_next
    lda native_break_lo,x
    cmp native_pc_lo
    bne native_current_pc_is_breakpoint_next
    lda native_break_hi,x
    cmp native_pc_hi
    beq native_current_pc_is_breakpoint_yes
native_current_pc_is_breakpoint_next:
    inx
    cpx #BREAKPOINT_MAX
    bcc native_current_pc_is_breakpoint_loop
    clc
    rts
native_current_pc_is_breakpoint_yes:
    sec
    rts

native_patch_address:
    sta native_patch_candidate_lo
    sty native_patch_candidate_hi
    ldx #$00
native_patch_duplicate_loop:
    cpx native_patch_count
    bcs native_patch_new
    lda native_patch_lo,x
    cmp native_patch_candidate_lo
    bne native_patch_duplicate_next
    lda native_patch_hi,x
    cmp native_patch_candidate_hi
    beq native_patch_ok
native_patch_duplicate_next:
    inx
    bne native_patch_duplicate_loop
native_patch_new:
    cpx #NATIVE_PATCH_MAX
    bcs native_patch_fail
    lda native_patch_candidate_lo
    sta native_patch_lo,x
    sta native_patch_read+1
    sta native_patch_write+1
    lda native_patch_candidate_hi
    sta native_patch_hi,x
    sta native_patch_read+2
    sta native_patch_write+2
native_patch_read:
    lda $FFFF
    sta native_patch_byte,x
    lda #$00
native_patch_write:
    sta $FFFF
    inc native_patch_count
native_patch_ok:
    clc
    rts
native_patch_fail:
    sec
    rts

native_restore_patches:
    ldx #$00
native_restore_patches_loop:
    cpx native_patch_count
    bcs native_restore_patches_done
    lda native_patch_lo,x
    sta native_restore_write+1
    lda native_patch_hi,x
    sta native_restore_write+2
    lda native_patch_byte,x
native_restore_write:
    sta $FFFF
    inx
    bne native_restore_patches_loop
native_restore_patches_done:
    lda #$00
    sta native_patch_count
    rts

native_resume_target:
    lda native_cpu_p
    ora #$20
    and #$EF
    sta native_resume_p
    ldx native_cpu_sp
    txs
    lda native_pc_hi
    pha
    lda native_pc_lo
    pha
    lda native_resume_p
    pha
    lda native_cpu_a
    ldx native_cpu_x
    ldy native_cpu_y
    rti

; The KERNAL BRK dispatcher has pushed A, X, and Y after the CPU's P/PC frame.
native_brk_handler:
    sei
    cld
    tsx
    stx native_brk_sp
    lda $0103,x
    sta native_cpu_a
    lda $0102,x
    sta native_cpu_x
    lda $0101,x
    sta native_cpu_y
    lda $0104,x
    and #$EF
    ora #$20
    sta native_cpu_p
    lda $0105,x
    sec
    sbc #$02
    sta native_pc_lo
    lda $0106,x
    sbc #$00
    sta native_pc_hi
    txa
    clc
    adc #$06
    sta native_cpu_sp
    jsr native_stop_is_known
    lda #$00
    adc #$00
    sta native_stop_known_flag
    jsr native_restore_patches
    lda native_auto_continue
    beq native_brk_stop
    lda #$00
    sta native_auto_continue
    jsr native_install_exit_patch
    bcc :+
    jmp native_brk_fail
:
    jsr native_install_user_breakpoints
    bcc :+
    jmp native_brk_fail
:
    jmp native_resume_target

native_brk_stop:
    lda native_stop_known_flag
    bne :+
    jmp native_brk_fail
:
    native_reu_fixed REU_STORE, SCREEN_RAM, $0000, ACTDBG_OUTPUT_REU_BASE_BANK, 1000
    native_reu_fixed REU_STORE, NATIVE_SNAPSHOT_C64, $0000, NATIVE_TARGET_REU_BANK, NATIVE_SNAPSHOT_LEN
    native_reu_fixed REU_FETCH, NATIVE_SNAPSHOT_C64, $0000, NATIVE_DEBUG_REU_BANK, NATIVE_SNAPSHOT_LEN
    jmp native_commit_stop

native_brk_fail:
    lda #$01
    sta native_result_failed
    native_reu_fixed REU_STORE, NATIVE_SNAPSHOT_C64, $0000, NATIVE_TARGET_REU_BANK, NATIVE_SNAPSHOT_LEN
    native_reu_fixed REU_FETCH, NATIVE_SNAPSHOT_C64, $0000, NATIVE_DEBUG_REU_BANK, NATIVE_SNAPSHOT_LEN
    jmp native_commit_stop

native_stop_is_known:
    lda native_pc_lo
    cmp #<native_target_completed
    bne :+
    lda native_pc_hi
    cmp #>native_target_completed
    beq native_stop_known
:
    lda native_pc_lo
    cmp #<NATIVE_EXIT_SERVICE
    bne native_stop_check_patches
    lda native_pc_hi
    cmp #>NATIVE_EXIT_SERVICE
    beq native_stop_known
native_stop_check_patches:
    ldx #$00
native_stop_check_patches_loop:
    cpx native_patch_count
    bcs native_stop_unknown
    lda native_patch_lo,x
    cmp native_pc_lo
    bne native_stop_check_patches_next
    lda native_patch_hi,x
    cmp native_pc_hi
    beq native_stop_known
native_stop_check_patches_next:
    inx
    bne native_stop_check_patches_loop
native_stop_unknown:
    clc
    rts
native_stop_known:
    sec
    rts

native_commit_stop:
    lda native_cpu_a
    sta actdbg_native_a
    lda native_cpu_x
    sta actdbg_native_x
    lda native_cpu_y
    sta actdbg_native_y
    lda native_cpu_p
    sta actdbg_native_p
    lda native_cpu_sp
    sta actdbg_native_sp
    lda native_pc_lo
    sta actdbg_current_pc_lo
    sta actdbg_native_scan_lo
    lda native_pc_hi
    sta actdbg_current_pc_hi
    sta actdbg_native_scan_hi
    lda #$01
    sta actdbg_native_target_valid
    lda native_call_depth
    sta actdbg_native_call_depth
    ldx #$00
native_commit_callstack_loop:
    lda native_callstack_lo,x
    sta actdbg_native_callstack_lo,x
    lda native_callstack_hi,x
    sta actdbg_native_callstack_hi,x
    inx
    cpx #NATIVE_CALLSTACK_MAX
    bcc native_commit_callstack_loop
    lda native_result_failed
    sta actdbg_native_failed
    beq :+
    jmp native_return_to_debugger
:
    lda native_pc_lo
    cmp #<native_target_completed
    bne :+
    lda native_pc_hi
    cmp #>native_target_completed
    beq native_commit_done
:
    lda native_pc_lo
    cmp #<NATIVE_EXIT_SERVICE
    bne native_commit_break
    lda native_pc_hi
    cmp #>NATIVE_EXIT_SERVICE
    bne native_commit_break
native_commit_done:
    lda #$01
    sta actdbg_native_done
    sta actdbg_view_mode
    jmp native_return_to_debugger
native_commit_break:
    lda #$00
    sta actdbg_break_hit
    ldx #$00
native_commit_break_loop:
    lda native_break_active,x
    beq native_commit_break_next
    lda native_break_lo,x
    cmp native_pc_lo
    bne native_commit_break_next
    lda native_break_hi,x
    cmp native_pc_hi
    bne native_commit_break_next
    lda #$01
    sta actdbg_break_hit
    bne native_return_to_debugger
native_commit_break_next:
    inx
    cpx #BREAKPOINT_MAX
    bcc native_commit_break_loop

native_return_to_debugger:
    ldx native_debugger_sp
    txs
    lda native_result_failed
    beq :+
    sec
    rts
:
    clc
    rts

native_target_completed:
    brk

; NMOS 6502 instruction lengths, including stable lengths for undocumented
; opcodes so source stepping cannot lose synchronization on inline data.
native_opcode_lengths:
    .byte 1,2,1,2,2,2,2,2,1,2,1,2,3,3,3,3
    .byte 2,2,1,2,2,2,2,2,1,3,1,3,3,3,3,3
    .byte 3,2,1,2,2,2,2,2,1,2,1,2,3,3,3,3
    .byte 2,2,1,2,2,2,2,2,1,3,1,3,3,3,3,3
    .byte 1,2,1,2,2,2,2,2,1,2,1,2,3,3,3,3
    .byte 2,2,1,2,2,2,2,2,1,3,1,3,3,3,3,3
    .byte 1,2,1,2,2,2,2,2,1,2,1,2,3,3,3,3
    .byte 2,2,1,2,2,2,2,2,1,3,1,3,3,3,3,3
    .byte 2,2,2,2,2,2,2,2,1,2,1,2,3,3,3,3
    .byte 2,2,1,2,2,2,2,2,1,3,1,3,3,3,3,3
    .byte 2,2,2,2,2,2,2,2,1,2,1,2,3,3,3,3
    .byte 2,2,1,2,2,2,2,2,1,3,1,3,3,3,3,3
    .byte 2,2,2,2,2,2,2,2,1,2,1,2,3,3,3,3
    .byte 2,2,1,2,2,2,2,2,1,3,1,3,3,3,3,3
    .byte 2,2,2,2,2,2,2,2,1,2,1,2,3,3,3,3
    .byte 2,2,1,2,2,2,2,2,1,3,1,3,3,3,3,3

native_command:
    .res 1
native_debugger_sp:
    .res 1
native_target_valid_copy:
    .res 1
native_result_failed:
    .res 1
native_auto_continue:
    .res 1
native_stop_known_flag:
    .res 1
native_cpu_a:
    .res 1
native_cpu_x:
    .res 1
native_cpu_y:
    .res 1
native_cpu_p:
    .res 1
native_cpu_sp:
    .res 1
native_resume_p:
    .res 1
native_brk_sp:
    .res 1
native_pc_lo:
    .res 1
native_pc_hi:
    .res 1
native_next_lo:
    .res 1
native_next_hi:
    .res 1
native_load_lo:
    .res 1
native_load_hi:
    .res 1
native_payload_len_lo:
    .res 1
native_payload_len_hi:
    .res 1
native_target_end_lo:
    .res 1
native_target_end_hi:
    .res 1
native_opcode:
    .res 1
native_branch_offset:
    .res 1
native_indirect_lo:
    .res 1
native_indirect_hi:
    .res 1
native_patch_count:
    .res 1
native_patch_candidate_lo:
    .res 1
native_patch_candidate_hi:
    .res 1
native_patch_lo:
    .res NATIVE_PATCH_MAX
native_patch_hi:
    .res NATIVE_PATCH_MAX
native_patch_byte:
    .res NATIVE_PATCH_MAX
native_break_index:
    .res 1
native_break_active:
    .res BREAKPOINT_MAX
native_break_lo:
    .res BREAKPOINT_MAX
native_break_hi:
    .res BREAKPOINT_MAX
native_call_depth:
    .res 1
native_callstack_lo:
    .res NATIVE_CALLSTACK_MAX
native_callstack_hi:
    .res NATIVE_CALLSTACK_MAX
