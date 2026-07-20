; Native two-REAL-parameter comparison/select function lowering.

NATIVE_REAL_FUNCTION_MAIN_CODE_SIZE = 88
NATIVE_REAL_FUNCTION_CODE_OFFSET = NATIVE_REAL_FUNCTION_MAIN_CODE_SIZE
NATIVE_REAL_FUNCTION_CODE_SIZE = 75
NATIVE_REAL_FUNCTION_DATA_OFFSET = NATIVE_REAL_FUNCTION_CODE_OFFSET + NATIVE_REAL_FUNCTION_CODE_SIZE
NATIVE_REAL_FUNCTION_DATA_SIZE = 20
NATIVE_REAL_FUNCTION_POINTER_OFFSET = NATIVE_REAL_FUNCTION_DATA_OFFSET + NATIVE_REAL_FUNCTION_DATA_SIZE
NATIVE_REAL_FUNCTION_ROOT_SIZE = NATIVE_REAL_FUNCTION_POINTER_OFFSET + 2

NATIVE_REAL_FUNCTION_NAME_V0 = 0
NATIVE_REAL_FUNCTION_NAME_V1 = 1
NATIVE_REAL_FUNCTION_NAME_V2 = 2
NATIVE_REAL_FUNCTION_NAME_V3 = 3
NATIVE_REAL_FUNCTION_NAME_V4 = 4
NATIVE_REAL_FUNCTION_NAME_DATA = 5
NATIVE_REAL_FUNCTION_NAME_POINTER = 6
NATIVE_REAL_FUNCTION_NAME_COUNT = 7

native_real_function_detect:
    lda #$00
    sta native_real_function_active

    lda #ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$02
    beq :+
    jmp native_real_function_detect_no
:
    lda #ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    jsr load_context_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcs :+
    jmp native_real_function_detect_no
:
    ldx #$01
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    jsr scan_zp_is_main_symbol
    bcs :+
    jmp native_real_function_detect_no
:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_LOAD_PROC_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_PROC_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp #(ACTC_PROC_META_FUNCTION | ACTC_PROC_META_REAL_RETURN | 2)
    beq :+
    jmp native_real_function_detect_no
:
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp #$03
    beq :+
    jmp native_real_function_detect_no
:
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq :+
    jmp native_real_function_detect_no
:
    ldx #$01
    lda #ACTC_OVERLAY_CTX_LOAD_PROC_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_PROC_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq :+
    jmp native_real_function_detect_no
:
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq :+
    jmp native_real_function_detect_no
:
    lda #ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$05
    beq :+
    jmp native_real_function_detect_no
:
    lda #ACTC_OVERLAY_CTX_MODULE_VAR_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$03
    beq :+
    jmp native_real_function_detect_no
:
    ldx #$00
native_real_function_detect_var_loop:
    jsr native_real_function_var_x_is_real
    bcs :+
    jmp native_real_function_detect_no
:
    inx
    cpx #$05
    bcc native_real_function_detect_var_loop

    lda #ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$02
    beq :+
    jmp native_real_function_detect_no
:
    lda #ACTC_OVERLAY_CTX_STRING_COUNT_PTR_LO
    jsr load_count_from_context
    beq :+
    jmp native_real_function_detect_no
:
    lda #ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    jsr load_count_from_context
    cmp #$05
    beq :+
    jmp native_real_function_detect_no
:
    ldx #$00
    lda #<native_real_function_external_cmp
    ldy #>native_real_function_external_cmp
    jsr native_real_function_external_x_matches
    bcs :+
    jmp native_real_function_detect_no
:
    ldx #$01
    lda #<native_real_function_external_i_to_f
    ldy #>native_real_function_external_i_to_f
    jsr native_real_function_external_x_matches
    bcs :+
    jmp native_real_function_detect_no
:
    ldx #$00
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #<native_real_function_select_body_pattern
    ldy #>native_real_function_select_body_pattern
    jsr native_real_function_match_scan_pattern
    bcs :+
    jmp native_real_function_detect_no
:
    ldx #$01
    lda #ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_body_ptr_to_scan_zp
    lda #<native_real_function_main_body_pattern
    ldy #>native_real_function_main_body_pattern
    jsr native_real_function_match_scan_pattern
    bcs :+
    jmp native_real_function_detect_no
:
    ldx #$00
    jsr native_real_function_load_literal_x
    lda native_real_function_literal_hi
    bne native_real_function_detect_no
    lda native_real_function_literal_lo
    cmp #$01
    bne native_real_function_detect_no
    ldx #$01
    jsr native_real_function_load_literal_x
    lda native_real_function_literal_lo
    ora native_real_function_literal_hi
    bne native_real_function_detect_no
    ldx #$03
    jsr native_real_function_load_literal_x
    lda native_real_function_literal_lo
    ora native_real_function_literal_hi
    bne native_real_function_detect_no

    ldx #$02
    jsr native_real_function_load_literal_x
    lda native_real_function_literal_lo
    sta native_real_function_left_lo
    lda native_real_function_literal_hi
    sta native_real_function_left_hi
    ldx #$04
    jsr native_real_function_load_literal_x
    lda native_real_function_literal_lo
    sta native_real_function_right_lo
    lda native_real_function_literal_hi
    sta native_real_function_right_hi

    lda #$01
    sta native_real_function_active
    sec
    rts
native_real_function_detect_no:
    lda #$00
    sta native_real_function_active
    clc
    rts

native_real_function_var_x_is_real:
    lda #ACTC_OVERLAY_CTX_LOAD_VAR_META_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$02
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp #$04
    bne native_real_function_var_x_is_real_no
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    jsr lowercase_ascii_overlay
    cmp #'r'
    bne native_real_function_var_x_is_real_no
    sec
    rts
native_real_function_var_x_is_real_no:
    clc
    rts

native_real_function_external_x_matches:
    sta native_real_function_pattern_ptr
    sty native_real_function_pattern_ptr+1
    lda #ACTC_OVERLAY_CTX_SET_EXTERNAL_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    lda native_real_function_pattern_ptr
    sta ACTC_OVERLAY_WORK_ZP
    lda native_real_function_pattern_ptr+1
    sta ACTC_OVERLAY_WORK_ZP+1
    jmp native_real_function_compare_scan_pattern

native_real_function_match_scan_pattern:
    sta ACTC_OVERLAY_WORK_ZP
    sty ACTC_OVERLAY_WORK_ZP+1
    ldy #$00
native_real_function_match_scan_pattern_loop:
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_function_byte
    jsr emit_object_peek_payload_y
    cmp native_real_function_byte
    bne native_real_function_match_scan_pattern_no
    lda native_real_function_byte
    beq native_real_function_match_scan_pattern_yes
    iny
    bne native_real_function_match_scan_pattern_loop
native_real_function_match_scan_pattern_no:
    clc
    rts
native_real_function_match_scan_pattern_yes:
    sec
    rts

native_real_function_compare_scan_pattern:
    ldy #$00
native_real_function_compare_scan_pattern_loop:
    lda (ACTC_OVERLAY_SCAN_ZP),y
    jsr lowercase_ascii_overlay
    cmp (ACTC_OVERLAY_WORK_ZP),y
    bne native_real_function_compare_scan_pattern_no
    lda (ACTC_OVERLAY_WORK_ZP),y
    beq native_real_function_compare_scan_pattern_yes
    iny
    bne native_real_function_compare_scan_pattern_loop
native_real_function_compare_scan_pattern_no:
    clc
    rts
native_real_function_compare_scan_pattern_yes:
    sec
    rts

native_real_function_load_literal_x:
    lda #ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    jsr call_indexed_context_function
    lda #ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    jsr load_context_ptr_to_work_zp
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_function_literal_lo
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta native_real_function_literal_hi
    rts

native_real_function_emit_debug_offset:
    ldx body_debug_index_data
    lda entry_index_data
    beq native_real_function_emit_debug_offset_function
    lda native_real_function_main_debug_offsets,x
    bne native_real_function_emit_debug_offset_ready
native_real_function_emit_debug_offset_function:
    lda native_real_function_select_debug_offsets,x
native_real_function_emit_debug_offset_ready:
    ldy #$00
    jmp emit_word_decimal

native_real_function_emit_export_list:
    lda #$00
    sta word_value_lo
    sta word_value_hi
    lda #NATIVE_REAL_FUNCTION_ROOT_SIZE
    ldx #$01
    jsr emit_machine_export_line

    lda #NATIVE_REAL_FUNCTION_CODE_OFFSET
    sta word_value_lo
    lda #$00
    sta word_value_hi
    lda #NATIVE_REAL_FUNCTION_CODE_SIZE
    ldx #$00
    jsr emit_machine_export_line

    lda #$00
    sta native_real_function_index
native_real_function_emit_export_name_loop:
    ldx native_real_function_index
    jsr native_real_function_set_name_x
    ldx native_real_function_index
    lda native_real_function_name_offsets,x
    pha
    lda native_real_function_name_sizes,x
    tax
    pla
    jsr native_real_function_emit_named_export
    inc native_real_function_index
    lda native_real_function_index
    cmp #NATIVE_REAL_FUNCTION_NAME_COUNT
    bcc native_real_function_emit_export_name_loop
    clc
    rts

native_real_function_emit_named_export:
    sta word_value_lo
    stx compare_char_local
    lda #$00
    sta word_value_hi
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr emit_scan_zp_string
    lda #' '
    jsr emit_char_overlay
    lda word_value_lo
    ldy word_value_hi
    jsr emit_word_decimal
    lda #' '
    jsr emit_char_overlay
    lda compare_char_local
    ldy #$00
    jsr emit_word_decimal
    jmp emit_newline

native_real_function_emit_body_marker_list:
    lda #<native_real_function_main_body_marker
    ldy #>native_real_function_main_body_marker
    jsr native_real_function_emit_line_ay
    lda #<native_real_function_select_body_marker
    ldy #>native_real_function_select_body_marker
    jsr native_real_function_emit_line_ay
    lda #NATIVE_REAL_FUNCTION_NAME_COUNT
    sta native_real_function_count
native_real_function_emit_body_marker_loop:
    lda #<native_real_function_data_body_marker
    ldy #>native_real_function_data_body_marker
    jsr native_real_function_emit_line_ay
    dec native_real_function_count
    bne native_real_function_emit_body_marker_loop
    clc
    rts

native_real_function_emit_line_ay:
    sta ACTC_OVERLAY_SCAN_ZP
    sty ACTC_OVERLAY_SCAN_ZP+1
    jsr emit_scan_zp_string
    jmp emit_newline

native_real_function_emit_machine_code_list:
    lda #'m'
    jsr emit_char_overlay
    lda #$00
    sta native_real_function_index
native_real_function_emit_machine_loop:
    ldy native_real_function_index
    lda native_real_function_machine_template,y
    ldx native_real_function_index
    cpx #22
    bne :+
    lda native_real_function_left_lo
    jmp native_real_function_emit_machine_byte_ready
:
    cpx #24
    bne :+
    lda native_real_function_left_hi
    jmp native_real_function_emit_machine_byte_ready
:
    cpx #37
    bne :+
    lda native_real_function_right_lo
    jmp native_real_function_emit_machine_byte_ready
:
    cpx #39
    bne native_real_function_emit_machine_byte_ready
    lda native_real_function_right_hi
native_real_function_emit_machine_byte_ready:
    jsr native_real_function_emit_byte
    inc native_real_function_index
    lda native_real_function_index
    cmp #NATIVE_REAL_FUNCTION_ROOT_SIZE
    bcc native_real_function_emit_machine_loop
    jsr emit_newline
    jsr native_real_function_emit_reloc_list
    clc
    rts

native_real_function_emit_byte:
    sta native_real_function_byte
    lda #' '
    jsr emit_char_overlay
    lda native_real_function_byte
    jmp emit_hex_byte_overlay

native_real_function_emit_reloc_list:
    lda #3
    ldx #NATIVE_REAL_FUNCTION_NAME_POINTER
    jsr native_real_function_emit_named_word_reloc
    lda #9
    ldx #NATIVE_REAL_FUNCTION_NAME_POINTER
    jsr native_real_function_emit_named_word_reloc
    lda #14
    ldx #NATIVE_REAL_FUNCTION_NAME_V0
    ldy #'l'
    jsr native_real_function_emit_named_byte_reloc
    lda #18
    ldx #NATIVE_REAL_FUNCTION_NAME_V0
    ldy #'h'
    jsr native_real_function_emit_named_byte_reloc
    lda #26
    ldx #$01
    jsr native_real_function_emit_import_reloc
    lda #29
    ldx #NATIVE_REAL_FUNCTION_NAME_V1
    ldy #'l'
    jsr native_real_function_emit_named_byte_reloc
    lda #33
    ldx #NATIVE_REAL_FUNCTION_NAME_V1
    ldy #'h'
    jsr native_real_function_emit_named_byte_reloc
    lda #41
    ldx #$01
    jsr native_real_function_emit_import_reloc
    lda #44
    ldx #NATIVE_REAL_FUNCTION_NAME_V0
    ldy #'l'
    jsr native_real_function_emit_named_byte_reloc
    lda #47
    ldx #NATIVE_REAL_FUNCTION_NAME_V0
    ldy #'h'
    jsr native_real_function_emit_named_byte_reloc
    lda #50
    ldx #NATIVE_REAL_FUNCTION_NAME_V1
    ldy #'l'
    jsr native_real_function_emit_named_byte_reloc
    lda #53
    ldx #NATIVE_REAL_FUNCTION_NAME_V1
    ldy #'h'
    jsr native_real_function_emit_named_byte_reloc
    lda #56
    ldx #$00
    jsr native_real_function_emit_export_reloc
    lda #67
    ldx #NATIVE_REAL_FUNCTION_NAME_V2
    jsr native_real_function_emit_named_word_reloc
    lda #104
    ldx #NATIVE_REAL_FUNCTION_NAME_V4
    jsr native_real_function_emit_named_word_reloc
    lda #120
    ldx #NATIVE_REAL_FUNCTION_NAME_V3
    jsr native_real_function_emit_named_word_reloc
    lda #131
    ldx #NATIVE_REAL_FUNCTION_NAME_V4
    ldy #'l'
    jsr native_real_function_emit_named_byte_reloc
    lda #135
    ldx #NATIVE_REAL_FUNCTION_NAME_V4
    ldy #'h'
    jsr native_real_function_emit_named_byte_reloc
    lda #139
    ldx #NATIVE_REAL_FUNCTION_NAME_V3
    ldy #'l'
    jsr native_real_function_emit_named_byte_reloc
    lda #143
    ldx #NATIVE_REAL_FUNCTION_NAME_V3
    ldy #'h'
    jsr native_real_function_emit_named_byte_reloc
    lda #147
    ldx #$00
    jsr native_real_function_emit_import_reloc
    lda #154
    ldx #NATIVE_REAL_FUNCTION_NAME_V4
    ldy #'l'
    jsr native_real_function_emit_named_byte_reloc
    lda #156
    ldx #NATIVE_REAL_FUNCTION_NAME_V4
    ldy #'h'
    jsr native_real_function_emit_named_byte_reloc
    lda #159
    ldx #NATIVE_REAL_FUNCTION_NAME_V3
    ldy #'l'
    jsr native_real_function_emit_named_byte_reloc
    lda #161
    ldx #NATIVE_REAL_FUNCTION_NAME_V3
    ldy #'h'
    jsr native_real_function_emit_named_byte_reloc
    lda #NATIVE_REAL_FUNCTION_POINTER_OFFSET
    ldx #NATIVE_REAL_FUNCTION_NAME_DATA
    jmp native_real_function_emit_named_word_reloc

native_real_function_emit_named_word_reloc:
    sta native_real_function_reloc_offset
    jsr native_real_function_set_name_x
    lda native_real_function_reloc_offset
    jsr native_real_function_emit_reloc_prefix
    jmp native_real_function_emit_named_reloc_target

native_real_function_emit_named_byte_reloc:
    sta native_real_function_reloc_offset
    sty native_real_function_reloc_modifier
    jsr native_real_function_set_name_x
    lda native_real_function_reloc_offset
    jsr native_real_function_emit_reloc_prefix
    lda native_real_function_reloc_modifier
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jmp native_real_function_emit_named_reloc_target

native_real_function_emit_export_reloc:
    sta native_real_function_reloc_offset
    lda #ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    jsr call_indexed_context_function
    jsr load_resident_export_ptr_to_scan_zp
    lda native_real_function_reloc_offset
    jsr native_real_function_emit_reloc_prefix
    jmp native_real_function_emit_named_reloc_target

native_real_function_emit_named_reloc_target:
    lda #'x'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    jsr emit_lower_scan_zp_string
    jmp emit_newline

native_real_function_emit_import_reloc:
    sta native_real_function_reloc_offset
    stx native_real_function_import_index
    jsr native_real_function_emit_reloc_prefix
    lda #'u'
    jsr emit_char_overlay
    lda native_real_function_import_index
    jsr emit_object_selector_overlay
    jmp emit_newline

native_real_function_emit_reloc_prefix:
    sta native_real_function_reloc_offset
    lda #'r'
    jsr emit_char_overlay
    lda #' '
    jsr emit_char_overlay
    lda native_real_function_reloc_offset
    jsr emit_small_decimal
    lda #' '
    jmp emit_char_overlay

native_real_function_set_name_x:
    lda native_real_function_name_ptr_lo,x
    sta ACTC_OVERLAY_SCAN_ZP
    lda native_real_function_name_ptr_hi,x
    sta ACTC_OVERLAY_SCAN_ZP+1
    rts

native_real_function_select_body_pattern:
    .asciiz "S4S3L4U4L3U3u0p0lhL4U4rvL3U3r"
native_real_function_main_body_pattern:
    .asciiz "p2u1T0S0p4u1T1S1L0U0L1U1C0T2S2r"
native_real_function_external_cmp:
    .asciiz "rt_f_cmp"
native_real_function_external_i_to_f:
    .asciiz "rt_i_to_f"

native_real_function_main_body_marker:
    .asciiz "b u0u1M"
native_real_function_select_body_marker:
    .asciiz "b u0M"
native_real_function_data_body_marker:
    .asciiz "b M"

native_real_function_name_v0:
    .asciiz "__v0"
native_real_function_name_v1:
    .asciiz "__v1"
native_real_function_name_v2:
    .asciiz "__v2"
native_real_function_name_v3:
    .asciiz "__v3"
native_real_function_name_v4:
    .asciiz "__v4"
native_real_function_name_data:
    .asciiz "__idata"
native_real_function_name_pointer:
    .asciiz "__iptr"

native_real_function_name_ptr_lo:
    .byte <native_real_function_name_v0,<native_real_function_name_v1
    .byte <native_real_function_name_v2,<native_real_function_name_v3
    .byte <native_real_function_name_v4,<native_real_function_name_data
    .byte <native_real_function_name_pointer
native_real_function_name_ptr_hi:
    .byte >native_real_function_name_v0,>native_real_function_name_v1
    .byte >native_real_function_name_v2,>native_real_function_name_v3
    .byte >native_real_function_name_v4,>native_real_function_name_data
    .byte >native_real_function_name_pointer
native_real_function_name_offsets:
    .byte 163,167,171,175,179,163,183
native_real_function_name_sizes:
    .byte 4,4,4,4,4,20,2

native_real_function_select_debug_offsets:
    .byte 88,109,130,130,138,138,146,149,151,151,153,153,157,158,158,158,162
native_real_function_main_debug_offsets:
    .byte 21,25,13,25,36,40,28,40,43,46,49,52,55,66,66,72

native_real_function_machine_template:
    .byte $A2,$00,$BD,$00,$00,$85,$06,$E8,$BD,$00,$00,$85,$07,$A9,$00,$85
    .byte $02,$A9,$00,$85,$03,$A9,$00,$A2,$00,$20,$00,$00,$A9,$00,$85,$02
    .byte $A9,$00,$85,$03,$A9,$00,$A2,$00,$20,$00,$00,$A9,$00,$48,$A9,$00
    .byte $48,$A9,$00,$48,$A9,$00,$48,$20,$00,$00,$85,$04,$86,$05,$A0,$03
    .byte $B1,$04,$99,$00,$00,$88,$10,$F8,$A9,$A5,$8D,$D0,$03,$A9,$00,$85
    .byte $02,$85,$03,$A2,$02,$4C,$0F,$CF,$68,$AA,$68,$85,$04,$68,$85,$03
    .byte $68,$85,$02,$A0,$03,$B1,$02,$99,$00,$00,$88,$10,$F8,$68,$85,$03
    .byte $68,$85,$02,$A0,$03,$B1,$02,$99,$00,$00,$88,$10,$F8,$A5,$04,$48
    .byte $8A,$48,$A9,$00,$85,$02,$A9,$00,$85,$03,$A9,$00,$85,$04,$A9,$00
    .byte $85,$05,$20,$00,$00,$C9,$FF,$D0,$05,$A9,$00,$A2,$00,$60,$A9,$00
    .byte $A2,$00,$60,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .byte $00,$00,$00,$00,$00,$00,$00,$00,$00

native_real_function_active:
    .byte $00
native_real_function_left_lo:
    .byte $00
native_real_function_left_hi:
    .byte $00
native_real_function_right_lo:
    .byte $00
native_real_function_right_hi:
    .byte $00
native_real_function_literal_lo:
    .byte $00
native_real_function_literal_hi:
    .byte $00
native_real_function_byte:
    .byte $00
native_real_function_index:
    .byte $00
native_real_function_count:
    .byte $00
native_real_function_reloc_offset:
    .byte $00
native_real_function_reloc_modifier:
    .byte $00
native_real_function_import_index:
    .byte $00
native_real_function_pattern_ptr:
    .word $0000
