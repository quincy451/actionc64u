; Compiler-owned lowering for a runtime value tested before a side-effect call.

NATIVE_RUNTIME_CONDITION_ARG = 1
NATIVE_RUNTIME_CONDITION_NOARG = 2

NATIVE_RUNTIME_CONDITION_ARG_CODE_SIZE = 30
NATIVE_RUNTIME_CONDITION_NOARG_CODE_SIZE = 28

native_runtime_condition_detect:
    lda #$00
    sta native_runtime_condition_mode
    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$01
    beq :+
    jmp native_runtime_condition_detect_no
:
    lda #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    jsr load_context_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcs :+
    jmp native_runtime_condition_detect_no
:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcs :+
    jmp native_runtime_condition_detect_no
:
    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$02
    bcs :+
    jmp native_runtime_condition_detect_no
:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp

    lda #NATIVE_RUNTIME_CONDITION_ARG
    sta native_runtime_condition_mode
    lda #$D0
    sta native_runtime_condition_skip
    lda #<native_runtime_condition_arg_eq_pattern
    ldy #>native_runtime_condition_arg_eq_pattern
    jsr native_runtime_condition_match_pattern
    bcs native_runtime_condition_detect_arg
    lda #$F0
    sta native_runtime_condition_skip
    lda #<native_runtime_condition_arg_ne_pattern
    ldy #>native_runtime_condition_arg_ne_pattern
    jsr native_runtime_condition_match_pattern
    bcs native_runtime_condition_detect_arg

    lda #NATIVE_RUNTIME_CONDITION_NOARG
    sta native_runtime_condition_mode
    lda #$D0
    sta native_runtime_condition_skip
    lda #<native_runtime_condition_noarg_eq_pattern
    ldy #>native_runtime_condition_noarg_eq_pattern
    jsr native_runtime_condition_match_pattern
    bcs native_runtime_condition_detect_noarg
    lda #$F0
    sta native_runtime_condition_skip
    lda #<native_runtime_condition_noarg_ne_pattern
    ldy #>native_runtime_condition_noarg_ne_pattern
    jsr native_runtime_condition_match_pattern
    bcs native_runtime_condition_detect_noarg
    jmp native_runtime_condition_detect_no

native_runtime_condition_detect_arg:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$03
    bne native_runtime_condition_detect_no
    ldx #$00
    jsr native_runtime_condition_load_byte_literal
    bcc native_runtime_condition_detect_no
    sta native_runtime_condition_arg0
    ldx #$01
    jsr native_runtime_condition_load_byte_literal
    bcc native_runtime_condition_detect_no
    sta native_runtime_condition_cmp
    ldx #$02
    jsr native_runtime_condition_load_byte_literal
    bcc native_runtime_condition_detect_no
    sta native_runtime_condition_arg1
    sec
    rts

native_runtime_condition_detect_noarg:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$02
    bne native_runtime_condition_detect_no
    ldx #$00
    jsr native_runtime_condition_load_byte_literal
    bcc native_runtime_condition_detect_no
    sta native_runtime_condition_cmp
    ldx #$01
    jsr native_runtime_condition_load_byte_literal
    bcc native_runtime_condition_detect_no
    sta native_runtime_condition_arg1
    sec
    rts

native_runtime_condition_detect_no:
    lda #$00
    sta native_runtime_condition_mode
    clc
    rts

native_runtime_condition_match_pattern:
    sta ACTC_OVERLAY_WORK_ZP
    sty ACTC_OVERLAY_WORK_ZP+1
    ldy #$00
native_runtime_condition_match_pattern_loop:
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_runtime_condition_byte
    jsr emit_object_peek_payload_y
    cmp native_runtime_condition_byte
    bne native_runtime_condition_match_pattern_no
    lda native_runtime_condition_byte
    beq native_runtime_condition_match_pattern_yes
    iny
    bne native_runtime_condition_match_pattern_loop
native_runtime_condition_match_pattern_no:
    clc
    rts
native_runtime_condition_match_pattern_yes:
    sec
    rts

native_runtime_condition_load_byte_literal:
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$01
    lda (ACTC_OVERLAY_WORK_ZP),y
    bne native_runtime_condition_load_byte_literal_no
    dey
    lda (ACTC_OVERLAY_WORK_ZP),y
    sec
    rts
native_runtime_condition_load_byte_literal_no:
    clc
    rts

native_runtime_condition_emit_debug_offset:
    ldx body_debug_index_data
    lda native_runtime_condition_mode
    cmp #NATIVE_RUNTIME_CONDITION_ARG
    bne :+
    lda native_runtime_condition_arg_debug_offsets,x
    bne native_runtime_condition_emit_debug_offset_ready
:
    lda native_runtime_condition_noarg_debug_offsets,x
native_runtime_condition_emit_debug_offset_ready:
    ldy #$00
    jmp emit_word_decimal

native_runtime_condition_emit_export_list:
    lda #$00
    sta word_value_lo
    sta word_value_hi
    lda native_runtime_condition_mode
    cmp #NATIVE_RUNTIME_CONDITION_ARG
    bne :+
    lda #NATIVE_RUNTIME_CONDITION_ARG_CODE_SIZE
    bne native_runtime_condition_emit_export_ready
:
    lda #NATIVE_RUNTIME_CONDITION_NOARG_CODE_SIZE
native_runtime_condition_emit_export_ready:
    ldx #$00
    jmp emit_machine_export_line

native_runtime_condition_emit_body_marker_list:
    lda #'b'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda #'u'
    jsr emit_char_overlay
    lda #'0'
    jsr emit_char_overlay
    lda #'u'
    jsr emit_char_overlay
    lda #'1'
    jsr emit_char_overlay
    lda #'M'
    jsr emit_char_overlay
    jsr emit_newline
    clc
    rts

native_runtime_condition_emit_machine_code_list:
    lda #'m'
    jsr emit_char_overlay
    lda native_runtime_condition_mode
    cmp #NATIVE_RUNTIME_CONDITION_ARG
    bne native_runtime_condition_emit_machine_noarg
    lda #$A9
    jsr native_runtime_condition_emit_byte
    lda native_runtime_condition_arg0
    jsr native_runtime_condition_emit_byte
native_runtime_condition_emit_machine_noarg:
    lda #$20
    jsr native_runtime_condition_emit_byte
    lda #$00
    jsr native_runtime_condition_emit_byte
    jsr native_runtime_condition_emit_byte
    lda #$C9
    jsr native_runtime_condition_emit_byte
    lda native_runtime_condition_cmp
    jsr native_runtime_condition_emit_byte
    lda native_runtime_condition_skip
    jsr native_runtime_condition_emit_byte
    lda #$05
    jsr native_runtime_condition_emit_byte
    lda #$A9
    jsr native_runtime_condition_emit_byte
    lda native_runtime_condition_arg1
    jsr native_runtime_condition_emit_byte
    lda #$20
    jsr native_runtime_condition_emit_byte
    lda #$00
    jsr native_runtime_condition_emit_byte
    jsr native_runtime_condition_emit_byte
    lda #<native_runtime_condition_exit
    ldy #>native_runtime_condition_exit
    ldx #(native_runtime_condition_exit_end-native_runtime_condition_exit)
    jsr native_runtime_condition_emit_const
    jsr emit_newline
    lda native_runtime_condition_mode
    cmp #NATIVE_RUNTIME_CONDITION_ARG
    bne native_runtime_condition_emit_relocs_noarg
    lda #$03
    ldx #$00
    jsr native_runtime_condition_emit_import_reloc
    lda #$0C
    ldx #$01
    jsr native_runtime_condition_emit_import_reloc
    clc
    rts
native_runtime_condition_emit_relocs_noarg:
    lda #$01
    ldx #$00
    jsr native_runtime_condition_emit_import_reloc
    lda #$0A
    ldx #$01
    jsr native_runtime_condition_emit_import_reloc
    clc
    rts

native_runtime_condition_emit_byte:
    sta native_runtime_condition_byte
    lda #' '
    jsr emit_char_overlay
    lda native_runtime_condition_byte
    jmp emit_hex_byte_overlay

native_runtime_condition_emit_const:
    sta native_runtime_condition_const_ptr
    sty native_runtime_condition_const_ptr+1
    stx native_runtime_condition_count
    ldy #$00
native_runtime_condition_emit_const_loop:
    cpy native_runtime_condition_count
    beq native_runtime_condition_emit_const_done
    lda native_runtime_condition_const_ptr
    sta ACTC_OVERLAY_WORK_ZP
    lda native_runtime_condition_const_ptr+1
    sta ACTC_OVERLAY_WORK_ZP+1
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr native_runtime_condition_emit_byte
    iny
    bne native_runtime_condition_emit_const_loop
native_runtime_condition_emit_const_done:
    rts

native_runtime_condition_emit_import_reloc:
    stx native_runtime_condition_import_index
    sta native_runtime_condition_byte
    lda #'r'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda native_runtime_condition_byte
    jsr emit_small_decimal
    lda #' '
    jsr emit_char_overlay
    lda #'u'
    jsr emit_char_overlay
    lda native_runtime_condition_import_index
    jsr emit_object_selector_overlay
    jmp emit_newline

native_runtime_condition_arg_eq_pattern:
    .asciiz "p0u0p1qhp2u1vr"
native_runtime_condition_arg_ne_pattern:
    .asciiz "p0u0p1nhp2u1vr"
native_runtime_condition_noarg_eq_pattern:
    .asciiz "u0p0qhp1u1vr"
native_runtime_condition_noarg_ne_pattern:
    .asciiz "u0p0nhp1u1vr"

native_runtime_condition_exit:
    .byte $A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF
native_runtime_condition_exit_end:

native_runtime_condition_arg_debug_offsets:
    .byte 0,2,5,5,7,9,11,14,14
native_runtime_condition_noarg_debug_offsets:
    .byte 0,3,3,5,7,9,12,12

native_runtime_condition_mode:
    .byte $00
native_runtime_condition_skip:
    .byte $00
native_runtime_condition_arg0:
    .byte $00
native_runtime_condition_cmp:
    .byte $00
native_runtime_condition_arg1:
    .byte $00
native_runtime_condition_byte:
    .byte $00
native_runtime_condition_count:
    .byte $00
native_runtime_condition_import_index:
    .byte $00
native_runtime_condition_const_ptr:
    .word $0000
