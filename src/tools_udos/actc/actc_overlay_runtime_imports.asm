.include "actc_overlay_abi.inc"
.include "udos_services.inc"
.include "actc_asmblock_layout.inc"

.export actc_overlay_header
.export actc_overlay_entry
.export actc_overlay_end

IMPORT_PRINT_STR  = $01
IMPORT_PRINT_LINE = $02
IMPORT_FORMAT_INT = $04

.segment "CODE"

actc_overlay_header:
    .byte 'A','C','O','V'
    .byte ACTC_OVERLAY_ABI_VERSION
    .byte ACTC_OVERLAY_PASS_RUNTIME_IMPORTS
    .word ACTC_OVERLAY_EXEC_BASE
    .word actc_overlay_entry
    .word actc_overlay_end - actc_overlay_header
    .word $0000

actc_overlay_entry:
    stx ACTC_OVERLAY_CONTEXT_ZP
    sty ACTC_OVERLAY_CONTEXT_ZP+1
    ldy #ACTC_OVERLAY_CTX_PASS_ID
    lda #ACTC_OVERLAY_PASS_RUNTIME_IMPORTS
    sta (ACTC_OVERLAY_CONTEXT_ZP),y

    jsr detect_runtime_imports_overlay
    bcc :+
    jmp actc_overlay_fail
:
    jsr assemble_asmblocks_overlay
    bcc :+
    jmp actc_overlay_fail
:

    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_OK
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    clc
    lda #ACTC_OVERLAY_STATUS_OK
    rts

actc_overlay_fail:
    ldy #ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_OVERLAY_STATUS_FAILED
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    sec
    lda #ACTC_OVERLAY_STATUS_FAILED
    rts

detect_runtime_imports_overlay:
    lda #$00
    sta import_flags_local
    sta import_proc_index_local

detect_runtime_imports_overlay_proc_loop:
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp import_proc_index_local
    beq detect_runtime_imports_overlay_publish

    ldx import_proc_index_local
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_context_function
    jsr load_resident_body_ptr_to_work_zp
    ldy #$00
detect_runtime_imports_overlay_body_loop:
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq detect_runtime_imports_overlay_next_proc
    cmp #'s'
    beq detect_runtime_imports_overlay_print
    cmp #'e'
    beq detect_runtime_imports_overlay_printe
    cmp #'j'
    beq detect_runtime_imports_overlay_printi
    cmp #'y'
    beq detect_runtime_imports_overlay_printi
    cmp #'i'
    beq detect_runtime_imports_overlay_printie
    cmp #'z'
    beq detect_runtime_imports_overlay_printie
detect_runtime_imports_overlay_next_byte:
    iny
    cpy #$FF
    bne detect_runtime_imports_overlay_body_loop
    sec
    rts

detect_runtime_imports_overlay_print:
    lda import_flags_local
    ora #IMPORT_PRINT_STR
    sta import_flags_local
    jmp detect_runtime_imports_overlay_next_byte

detect_runtime_imports_overlay_printe:
    lda import_flags_local
    ora #IMPORT_PRINT_LINE
    sta import_flags_local
    jmp detect_runtime_imports_overlay_next_byte

detect_runtime_imports_overlay_printi:
    lda import_flags_local
    ora #IMPORT_FORMAT_INT|IMPORT_PRINT_STR
    sta import_flags_local
    jmp detect_runtime_imports_overlay_next_byte

detect_runtime_imports_overlay_printie:
    lda import_flags_local
    ora #IMPORT_FORMAT_INT|IMPORT_PRINT_LINE
    sta import_flags_local
    jmp detect_runtime_imports_overlay_next_byte

detect_runtime_imports_overlay_next_proc:
    inc import_proc_index_local
    jmp detect_runtime_imports_overlay_proc_loop

detect_runtime_imports_overlay_publish:
    lda #ACTC_OVERLAY_CTX_IMPORT_FLAGS_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda import_flags_local
    sta (ACTC_OVERLAY_WORK_ZP),y
    clc
    rts

load_resident_body_ptr_to_work_zp:
    lda #ACTC_OVERLAY_CTX_BODY_PTR_SLOT_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$01
    lda (ACTC_OVERLAY_WORK_ZP),y
    tax
    dey
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    stx ACTC_OVERLAY_WORK_ZP+1
    rts

load_context_ptr_to_work_zp:
    tay
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    iny
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP+1
    rts

call_context_function:
    tay
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target_ptr
    iny
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta call_target_ptr+1
    sec
    lda call_target_ptr
    sbc #$01
    sta call_target_minus_one
    lda call_target_ptr+1
    sbc #$00
    pha
    lda call_target_minus_one
    pha
    rts

call_target_minus_one:
    .byte $00
call_target_ptr:
    .word $0000
import_flags_local:
    .byte $00
import_proc_index_local:
    .byte $00

.include "actc_overlay_asmblock.inc"

actc_overlay_end:
