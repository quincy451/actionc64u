; ASMBLOCK source prepass. This runs in pass 4, before body collection, and
; leaves one compact page per block in REU for the native-local object emitter.

ASMBLOCK_SYMBOL_LIMIT = 24

.macro ASMBLOCK_JEQ target
    bne :+
    jmp target
:
.endmacro

.macro ASMBLOCK_JNE target
    beq :+
    jmp target
:
.endmacro

.macro ASMBLOCK_JCC target
    bcs :+
    jmp target
:
.endmacro

.macro ASMBLOCK_JCS target
    bcc :+
    jmp target
:
.endmacro

assemble_asmblocks_overlay:
    lda #$00
    sta asmblock_count
    ldy #$00
    lda #ACTC_OVERLAY_CTX_BEGIN_BODY_SCAN_FN_LO
    jsr asmblock_call_context_function
    ASMBLOCK_JCS assemble_asmblocks_overlay_load_fail

assemble_asmblocks_overlay_loop:
    jsr asmblock_skip_source_space
    ASMBLOCK_JCS assemble_asmblocks_overlay_load_fail
    jsr asmblock_peek_char
    ASMBLOCK_JCS assemble_asmblocks_overlay_load_fail
    ASMBLOCK_JEQ assemble_asmblocks_overlay_done
    cmp #10
    beq assemble_asmblocks_overlay_line_break
    cmp #13
    beq assemble_asmblocks_overlay_line_break

    lda #<asmblock_pattern_proc
    ldy #>asmblock_pattern_proc
    jsr asmblock_pattern_matches
    bcc assemble_asmblocks_overlay_proc

    lda #ACTC_OVERLAY_CTX_MATCH_SCALAR_DECL_FN_LO
    ldy #$00
    jsr asmblock_call_context_function
    bcs assemble_asmblocks_overlay_not_scalar
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_BY_CONST_FN_LO
    ldy #$00
    jsr asmblock_call_context_function
    jsr asmblock_skip_source_space
    bcc :+
    jmp assemble_asmblocks_overlay_bad
:
    lda #<asmblock_pattern_func
    ldy #>asmblock_pattern_func
    jsr asmblock_pattern_matches_keyword
    bcc assemble_asmblocks_overlay_func
    jmp assemble_asmblocks_overlay_skip_line
assemble_asmblocks_overlay_not_scalar:

    jsr asmblock_load_current_proc
    cmp #$FF
    beq assemble_asmblocks_overlay_skip_line
    jsr asmblock_peek_char
    ASMBLOCK_JCS assemble_asmblocks_overlay_bad
    cmp #'['
    ASMBLOCK_JEQ assemble_asmblocks_overlay_raw_block
    lda #<asmblock_pattern_keyword
    ldy #>asmblock_pattern_keyword
    jsr asmblock_pattern_matches_keyword
    bcc assemble_asmblocks_overlay_block

assemble_asmblocks_overlay_skip_line:
    ldy #$00
    lda #ACTC_OVERLAY_CTX_SKIP_SOURCE_LINE_FN_LO
    jsr asmblock_call_context_function
    jmp assemble_asmblocks_overlay_loop

assemble_asmblocks_overlay_line_break:
    jsr asmblock_consume_char
    ASMBLOCK_JCS assemble_asmblocks_overlay_load_fail
    jmp assemble_asmblocks_overlay_loop

assemble_asmblocks_overlay_proc:
    lda #<asmblock_pattern_proc
    ldy #>asmblock_pattern_proc
    jsr asmblock_consume_pattern
    bcs assemble_asmblocks_overlay_bad
    jmp assemble_asmblocks_overlay_routine_after_keyword
assemble_asmblocks_overlay_func:
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_BY_CONST_FN_LO
    ldy #$00
    jsr asmblock_call_context_function
    bcs assemble_asmblocks_overlay_bad
assemble_asmblocks_overlay_routine_after_keyword:
    jsr asmblock_skip_source_space
    bcs assemble_asmblocks_overlay_bad
    ldy #$00
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_PTR_FN_LO
    jsr asmblock_call_context_function
    bcs assemble_asmblocks_overlay_bad
    ldy #$00
    lda #ACTC_OVERLAY_CTX_RESOLVE_ROUTINE_DECL_FN_LO
    jsr asmblock_call_context_function
    bcs assemble_asmblocks_overlay_bad
    txa
    jsr asmblock_store_current_proc
    jmp assemble_asmblocks_overlay_skip_line

assemble_asmblocks_overlay_block:
    lda asmblock_count
    cmp #ACTC_ASMBLOCK_MAX
    bcs assemble_asmblocks_overlay_bad
    lda #<asmblock_pattern_keyword
    ldy #>asmblock_pattern_keyword
    jsr asmblock_consume_pattern
    bcs assemble_asmblocks_overlay_bad
    jsr asmblock_skip_source_space
    bcs assemble_asmblocks_overlay_bad
    jsr asmblock_peek_char
    cmp #'['
    bne assemble_asmblocks_overlay_bad
    jsr asmblock_consume_char
    bcs assemble_asmblocks_overlay_bad
    jsr asmblock_assemble_current
    bcs assemble_asmblocks_overlay_bad
    inc asmblock_count
    jmp assemble_asmblocks_overlay_skip_line

assemble_asmblocks_overlay_raw_block:
    lda asmblock_count
    cmp #ACTC_ASMBLOCK_MAX
    bcs assemble_asmblocks_overlay_bad
    jsr asmblock_consume_char
    bcs assemble_asmblocks_overlay_bad
    jsr rawblock_assemble_current
    bcs assemble_asmblocks_overlay_bad
    inc asmblock_count
    jmp assemble_asmblocks_overlay_skip_line

assemble_asmblocks_overlay_done:
    ldy #$00
    lda #ACTC_OVERLAY_CTX_FINISH_BODY_SCAN_FN_LO
    jsr asmblock_call_context_function
    bcs assemble_asmblocks_overlay_save_fail
    jsr asmblock_publish_count
    clc
    rts

assemble_asmblocks_overlay_bad:
    lda #<asmblock_msg_bad
    ldy #>asmblock_msg_bad
    jmp asmblock_fail_with_diag
assemble_asmblocks_overlay_load_fail:
    lda #<asmblock_msg_load
    ldy #>asmblock_msg_load
    jmp asmblock_fail_with_diag
assemble_asmblocks_overlay_save_fail:
    lda #<asmblock_msg_save
    ldy #>asmblock_msg_save
    jmp asmblock_fail_with_diag

asmblock_assemble_current:
    jsr asmblock_clear_page
    jsr asmblock_load_current_proc
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_PROC_INDEX
    lda #ACTC_ASMBLOCK_MAGIC
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_MAGIC
    lda #ACTC_ASMBLOCK_VERSION
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_VERSION
    lda #$00
    sta asmblock_pass
    sta asmblock_code_offset
    sta asmblock_label_count
    sta asmblock_reloc_count
    ldy #$00
    lda #ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    jsr asmblock_call_context_function
    jsr asmblock_parse_block
    ASMBLOCK_JCS asmblock_assemble_current_fail
    lda asmblock_code_offset
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_CODE_LEN
    lda asmblock_label_count
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_LABEL_COUNT

    ldy #$00
    lda #ACTC_OVERLAY_CTX_RESTORE_SOURCE_MARK_FN_LO
    jsr asmblock_call_context_function
    lda #$01
    sta asmblock_pass
    lda #$00
    sta asmblock_code_offset
    sta asmblock_reloc_count
    jsr asmblock_parse_block
    ASMBLOCK_JCS asmblock_assemble_current_fail
    lda asmblock_code_offset
    cmp ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_CODE_LEN
    ASMBLOCK_JNE asmblock_assemble_current_fail
    lda asmblock_reloc_count
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_RELOC_COUNT
    jsr asmblock_store_page
    rts
asmblock_assemble_current_fail:
    sec
    rts

; Raw Action code blocks share the assembled-block REU page contract. Numeric
; values emit one byte unless they require a word; symbols and the current
; address emit ordinary word relocations for pass 9 and ALINK.
rawblock_assemble_current:
    jsr asmblock_clear_page
    jsr asmblock_load_current_proc
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_PROC_INDEX
    lda #ACTC_ASMBLOCK_MAGIC
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_MAGIC
    lda #ACTC_ASMBLOCK_VERSION
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_VERSION
    lda #$01
    sta asmblock_pass
    lda #$00
    sta asmblock_code_offset
    sta asmblock_label_count
    sta asmblock_reloc_count
    jsr rawblock_parse_block
    ASMBLOCK_JCS rawblock_assemble_current_fail
    lda asmblock_code_offset
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_CODE_LEN
    lda asmblock_label_count
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_LABEL_COUNT
    lda asmblock_reloc_count
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_HEADER_RELOC_COUNT
    jsr asmblock_store_page
    rts
rawblock_assemble_current_fail:
    sec
    rts

rawblock_parse_block:
rawblock_parse_block_loop:
    jsr asmblock_skip_all_space
    ASMBLOCK_JCS rawblock_parse_block_fail
    jsr asmblock_peek_char
    ASMBLOCK_JCS rawblock_parse_block_fail
    ASMBLOCK_JEQ rawblock_parse_block_fail
    cmp #']'
    ASMBLOCK_JEQ rawblock_parse_block_done
    cmp #';'
    ASMBLOCK_JEQ rawblock_parse_block_comment
    cmp #','
    ASMBLOCK_JEQ rawblock_parse_block_comma
    cmp #'*'
    ASMBLOCK_JEQ rawblock_parse_current_address
    cmp #$27
    ASMBLOCK_JEQ rawblock_parse_character
    cmp #'-'
    ASMBLOCK_JEQ rawblock_parse_negative
    jsr asmblock_parse_value
    ASMBLOCK_JCS rawblock_parse_block_fail
    lda asmblock_value_kind
    ASMBLOCK_JNE rawblock_parse_symbol
    lda #$00
    sta rawblock_force_word
rawblock_parse_numeric:
    jsr rawblock_parse_constant_sum
    ASMBLOCK_JCS rawblock_parse_block_fail
rawblock_emit_numeric:
    lda asmblock_value_lo
    jsr asmblock_emit_byte
    ASMBLOCK_JCS rawblock_parse_block_fail
    lda asmblock_value_hi
    ASMBLOCK_JNE rawblock_emit_numeric_high
    lda rawblock_force_word
    ASMBLOCK_JEQ rawblock_parse_block_loop
    lda #$00
rawblock_emit_numeric_high:
    jsr asmblock_emit_byte
    ASMBLOCK_JCS rawblock_parse_block_fail
    jmp rawblock_parse_block_loop

rawblock_parse_character:
    jsr rawblock_parse_character_constant
    ASMBLOCK_JCS rawblock_parse_block_fail
    lda #$00
    sta rawblock_force_word
    jmp rawblock_parse_numeric

rawblock_parse_negative:
    jsr rawblock_parse_negative_constant
    ASMBLOCK_JCS rawblock_parse_block_fail
    jmp rawblock_parse_numeric

rawblock_parse_symbol:
    jsr asmblock_parse_optional_addend
    ASMBLOCK_JCS rawblock_parse_block_fail
    jsr asmblock_resolve_symbol
    ASMBLOCK_JCS rawblock_parse_block_fail
    jsr rawblock_emit_word_reloc
    ASMBLOCK_JCS rawblock_parse_block_fail
    jmp rawblock_parse_block_loop

rawblock_parse_current_address:
    jsr asmblock_consume_char
    ASMBLOCK_JCS rawblock_parse_block_fail
    lda #$01
    sta asmblock_value_kind
    lda #$00
    sta asmblock_addend
    jsr asmblock_parse_optional_addend
    ASMBLOCK_JCS rawblock_parse_block_fail
    lda asmblock_label_count
    cmp #ACTC_ASMBLOCK_LABEL_MAX
    ASMBLOCK_JCS rawblock_parse_block_fail
    tay
    lda asmblock_code_offset
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_LABEL_BASE,y
    tya
    sta asmblock_reloc_target
    inc asmblock_label_count
    jsr rawblock_emit_word_reloc
    ASMBLOCK_JCS rawblock_parse_block_fail
    jmp rawblock_parse_block_loop

; Character constants use Action's apostrophe prefix and accept an optional
; closing apostrophe. The small escape set matches the Linux compiler.
rawblock_parse_character_constant:
    jsr asmblock_consume_char
    ASMBLOCK_JCS rawblock_parse_character_constant_fail
    jsr asmblock_peek_char
    ASMBLOCK_JCS rawblock_parse_character_constant_fail
    ASMBLOCK_JEQ rawblock_parse_character_constant_fail
    cmp #$5C
    ASMBLOCK_JNE rawblock_parse_character_constant_store
    jsr asmblock_consume_char
    ASMBLOCK_JCS rawblock_parse_character_constant_fail
    jsr asmblock_peek_char
    ASMBLOCK_JCS rawblock_parse_character_constant_fail
    cmp #'n'
    ASMBLOCK_JEQ rawblock_parse_character_constant_newline
    cmp #'r'
    ASMBLOCK_JEQ rawblock_parse_character_constant_return
    jmp rawblock_parse_character_constant_store
rawblock_parse_character_constant_newline:
    lda #10
    bne rawblock_parse_character_constant_store
rawblock_parse_character_constant_return:
    lda #13
rawblock_parse_character_constant_store:
    sta asmblock_value_lo
    jsr asmblock_consume_char
    ASMBLOCK_JCS rawblock_parse_character_constant_fail
    jsr asmblock_peek_char
    cmp #$27
    ASMBLOCK_JNE rawblock_parse_character_constant_done
    jsr asmblock_consume_char
    ASMBLOCK_JCS rawblock_parse_character_constant_fail
rawblock_parse_character_constant_done:
    lda #$00
    sta asmblock_value_hi
    sta asmblock_value_kind
    clc
    rts
rawblock_parse_character_constant_fail:
    sec
    rts

rawblock_parse_negative_constant:
    jsr asmblock_consume_char
    ASMBLOCK_JCS rawblock_parse_negative_constant_fail
    jsr asmblock_parse_value
    ASMBLOCK_JCS rawblock_parse_negative_constant_fail
    lda asmblock_value_kind
    ASMBLOCK_JNE rawblock_parse_negative_constant_fail
    lda asmblock_value_hi
    cmp #$80
    ASMBLOCK_JCC rawblock_parse_negative_constant_negate
    ASMBLOCK_JNE rawblock_parse_negative_constant_fail
    lda asmblock_value_lo
    ASMBLOCK_JNE rawblock_parse_negative_constant_fail
rawblock_parse_negative_constant_negate:
    lda asmblock_value_lo
    ora asmblock_value_hi
    ASMBLOCK_JEQ rawblock_parse_negative_constant_zero
    sec
    lda #$00
    sbc asmblock_value_lo
    sta asmblock_value_lo
    lda #$00
    sbc asmblock_value_hi
    sta asmblock_value_hi
    lda #$01
    sta rawblock_force_word
    clc
    rts
rawblock_parse_negative_constant_zero:
    lda #$00
    sta rawblock_force_word
    clc
    rts
rawblock_parse_negative_constant_fail:
    sec
    rts

; Raw block tokenization treats horizontal whitespace around '+' as part of
; the same compiler-constant expression. Keep sums unsigned after the first
; factor; standalone signed constants still retain Action's word behavior.
rawblock_parse_constant_sum:
    lda asmblock_value_lo
    sta rawblock_sum_lo
    lda asmblock_value_hi
    sta rawblock_sum_hi
rawblock_parse_constant_sum_loop:
    jsr asmblock_skip_horizontal_space
    ASMBLOCK_JCS rawblock_parse_constant_sum_fail
    jsr asmblock_peek_char
    cmp #'+'
    ASMBLOCK_JNE rawblock_parse_constant_sum_done
    lda rawblock_force_word
    ASMBLOCK_JNE rawblock_parse_constant_sum_fail
    jsr asmblock_consume_char
    ASMBLOCK_JCS rawblock_parse_constant_sum_fail
    jsr asmblock_skip_horizontal_space
    ASMBLOCK_JCS rawblock_parse_constant_sum_fail
    jsr asmblock_peek_char
    cmp #$27
    ASMBLOCK_JEQ rawblock_parse_constant_sum_character
    cmp #'-'
    ASMBLOCK_JEQ rawblock_parse_constant_sum_fail
    jsr asmblock_parse_value
    ASMBLOCK_JCS rawblock_parse_constant_sum_fail
    lda asmblock_value_kind
    ASMBLOCK_JNE rawblock_parse_constant_sum_fail
    jmp rawblock_parse_constant_sum_add
rawblock_parse_constant_sum_character:
    jsr rawblock_parse_character_constant
    ASMBLOCK_JCS rawblock_parse_constant_sum_fail
rawblock_parse_constant_sum_add:
    clc
    lda rawblock_sum_lo
    adc asmblock_value_lo
    sta rawblock_sum_lo
    lda rawblock_sum_hi
    adc asmblock_value_hi
    ASMBLOCK_JCS rawblock_parse_constant_sum_fail
    sta rawblock_sum_hi
    jmp rawblock_parse_constant_sum_loop
rawblock_parse_constant_sum_done:
    lda rawblock_sum_lo
    sta asmblock_value_lo
    lda rawblock_sum_hi
    sta asmblock_value_hi
    clc
    rts
rawblock_parse_constant_sum_fail:
    sec
    rts

rawblock_emit_word_reloc:
    lda #ACTC_ASMBLOCK_RELOC_WORD
    sta asmblock_reloc_kind
    jsr asmblock_add_reloc
    ASMBLOCK_JCS rawblock_emit_word_reloc_fail
    lda #$00
    jsr asmblock_emit_byte
    ASMBLOCK_JCS rawblock_emit_word_reloc_fail
    lda #$00
    jsr asmblock_emit_byte
    rts
rawblock_emit_word_reloc_fail:
    sec
    rts

rawblock_parse_block_comma:
    jsr asmblock_consume_char
    ASMBLOCK_JCS rawblock_parse_block_fail
    jmp rawblock_parse_block_loop
rawblock_parse_block_comment:
    jsr asmblock_skip_comment
    ASMBLOCK_JCS rawblock_parse_block_fail
    jmp rawblock_parse_block_loop
rawblock_parse_block_done:
    jsr asmblock_consume_char
    rts
rawblock_parse_block_fail:
    sec
    rts

asmblock_parse_block:
asmblock_parse_block_loop:
    jsr asmblock_skip_all_space
    ASMBLOCK_JCS asmblock_parse_block_fail
    jsr asmblock_peek_char
    ASMBLOCK_JCS asmblock_parse_block_fail
    ASMBLOCK_JEQ asmblock_parse_block_fail
    cmp #']'
    ASMBLOCK_JEQ asmblock_parse_block_done
    cmp #';'
    ASMBLOCK_JEQ asmblock_parse_block_comment
    jsr asmblock_parse_identifier
    ASMBLOCK_JCS asmblock_parse_block_fail
    jsr asmblock_skip_horizontal_space
    ASMBLOCK_JCS asmblock_parse_block_fail
    jsr asmblock_peek_char
    cmp #':'
    ASMBLOCK_JNE asmblock_parse_block_mnemonic
    jsr asmblock_consume_char
    ASMBLOCK_JCS asmblock_parse_block_fail
    jsr asmblock_process_label
    ASMBLOCK_JCS asmblock_parse_block_fail
    jsr asmblock_skip_horizontal_space
    ASMBLOCK_JCS asmblock_parse_block_fail
    jsr asmblock_peek_char
    ASMBLOCK_JEQ asmblock_parse_block_fail
    cmp #']'
    ASMBLOCK_JEQ asmblock_parse_block_loop
    cmp #';'
    ASMBLOCK_JEQ asmblock_parse_block_comment
    cmp #10
    ASMBLOCK_JEQ asmblock_parse_block_loop
    cmp #13
    ASMBLOCK_JEQ asmblock_parse_block_loop
    jsr asmblock_parse_identifier
    ASMBLOCK_JCS asmblock_parse_block_fail

asmblock_parse_block_mnemonic:
    lda asmblock_symbol_len
    cmp #$03
    ASMBLOCK_JNE asmblock_parse_block_fail
    ldx #$02
asmblock_parse_block_copy_mnemonic:
    lda asmblock_symbol,x
    sta asmblock_mnemonic,x
    dex
    bpl asmblock_parse_block_copy_mnemonic
    jsr asmblock_skip_horizontal_space
    ASMBLOCK_JCS asmblock_parse_block_fail
    jsr asmblock_parse_operand
    ASMBLOCK_JCS asmblock_parse_block_fail
    jsr asmblock_finish_statement
    ASMBLOCK_JCS asmblock_parse_block_fail
    jmp asmblock_parse_block_loop

asmblock_parse_block_comment:
    jsr asmblock_skip_comment
    ASMBLOCK_JCS asmblock_parse_block_fail
    jmp asmblock_parse_block_loop

asmblock_parse_block_done:
    jsr asmblock_consume_char
    rts
asmblock_parse_block_fail:
    sec
    rts

asmblock_process_label:
    lda asmblock_pass
    ASMBLOCK_JNE asmblock_process_label_verify
    lda asmblock_label_count
    cmp #ACTC_ASMBLOCK_LABEL_MAX
    ASMBLOCK_JCS asmblock_process_label_fail
    jsr asmblock_find_label
    ASMBLOCK_JCC asmblock_process_label_fail
    ldx asmblock_label_count
    jsr asmblock_set_label_ptr_x
    ldy #$00
asmblock_process_label_copy:
    lda asmblock_symbol,y
    sta (ACTC_OVERLAY_WORK_ZP),y
    ASMBLOCK_JEQ asmblock_process_label_copied
    iny
    cpy #ASMBLOCK_SYMBOL_LIMIT+1
    ASMBLOCK_JCC asmblock_process_label_copy
    ASMBLOCK_JCS asmblock_process_label_fail
asmblock_process_label_copied:
    ldy asmblock_label_count
    lda asmblock_code_offset
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_LABEL_BASE,y
    inc asmblock_label_count
    clc
    rts

asmblock_process_label_verify:
    jsr asmblock_find_label
    ASMBLOCK_JCS asmblock_process_label_fail
    lda ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_LABEL_BASE,x
    cmp asmblock_code_offset
    ASMBLOCK_JNE asmblock_process_label_fail
    clc
    rts
asmblock_process_label_fail:
    sec
    rts

asmblock_parse_operand:
    lda #ACTC_ASMBLOCK_RELOC_WORD
    sta asmblock_reloc_kind
    jsr asmblock_peek_char
    ASMBLOCK_JCS asmblock_parse_operand_fail
    ASMBLOCK_JEQ asmblock_parse_operand_fail
    cmp #10
    ASMBLOCK_JEQ asmblock_parse_no_operand
    cmp #13
    ASMBLOCK_JEQ asmblock_parse_no_operand
    cmp #';'
    ASMBLOCK_JEQ asmblock_parse_no_operand
    cmp #']'
    ASMBLOCK_JEQ asmblock_parse_no_operand

    lda #ACTC_ASM_MODE_RELATIVE
    jsr asmblock_find_opcode
    ASMBLOCK_JCC asmblock_parse_branch

    jsr asmblock_peek_char
    cmp #'#'
    ASMBLOCK_JEQ asmblock_parse_immediate
    cmp #'('
    ASMBLOCK_JEQ asmblock_parse_parenthesized
    jsr asmblock_parse_value
    ASMBLOCK_JCS asmblock_parse_operand_fail
    jsr asmblock_parse_optional_addend
    ASMBLOCK_JCS asmblock_parse_operand_fail
    jsr asmblock_skip_horizontal_space
    ASMBLOCK_JCS asmblock_parse_operand_fail
    lda #$00
    sta asmblock_index_kind
    jsr asmblock_parse_optional_index
    ASMBLOCK_JCS asmblock_parse_operand_fail
    lda asmblock_value_kind
    ASMBLOCK_JEQ asmblock_select_numeric_plain
    lda asmblock_index_kind
    ASMBLOCK_JEQ asmblock_select_symbol_plain
    cmp #$01
    ASMBLOCK_JEQ asmblock_select_symbol_x
    lda #ACTC_ASM_MODE_ABSOLUTE_Y
    jmp asmblock_emit_selected_mode
asmblock_select_symbol_plain:
    lda asmblock_symbol_len
    cmp #$01
    ASMBLOCK_JNE asmblock_select_symbol_absolute
    lda asmblock_symbol
    cmp #'A'
    ASMBLOCK_JNE asmblock_select_symbol_absolute
    lda #ACTC_ASM_MODE_ACCUMULATOR
    jsr asmblock_find_opcode
    ASMBLOCK_JCS asmblock_select_symbol_absolute
    lda #ACTC_ASM_MODE_ACCUMULATOR
    jmp asmblock_emit_selected_mode
asmblock_select_symbol_absolute:
    lda #ACTC_ASM_MODE_ABSOLUTE
    jmp asmblock_emit_selected_mode
asmblock_select_symbol_x:
    lda #ACTC_ASM_MODE_ABSOLUTE_X
    jmp asmblock_emit_selected_mode

asmblock_select_numeric_plain:
    lda asmblock_index_kind
    ASMBLOCK_JEQ asmblock_select_numeric_no_index
    cmp #$01
    ASMBLOCK_JEQ asmblock_select_numeric_x
    lda asmblock_value_hi
    ASMBLOCK_JNE asmblock_select_numeric_abs_y
    lda #ACTC_ASM_MODE_ZP_Y
    jsr asmblock_find_opcode
    ASMBLOCK_JCC asmblock_select_numeric_zp_y
asmblock_select_numeric_abs_y:
    lda #ACTC_ASM_MODE_ABSOLUTE_Y
    jmp asmblock_emit_selected_mode
asmblock_select_numeric_zp_y:
    lda #ACTC_ASM_MODE_ZP_Y
    jmp asmblock_emit_selected_mode
asmblock_select_numeric_x:
    lda asmblock_value_hi
    ASMBLOCK_JNE asmblock_select_numeric_abs_x
    lda #ACTC_ASM_MODE_ZP_X
    jsr asmblock_find_opcode
    ASMBLOCK_JCC asmblock_select_numeric_zp_x
asmblock_select_numeric_abs_x:
    lda #ACTC_ASM_MODE_ABSOLUTE_X
    jmp asmblock_emit_selected_mode
asmblock_select_numeric_zp_x:
    lda #ACTC_ASM_MODE_ZP_X
    jmp asmblock_emit_selected_mode
asmblock_select_numeric_no_index:
    lda asmblock_value_hi
    ASMBLOCK_JNE asmblock_select_numeric_absolute
    lda #ACTC_ASM_MODE_ZP
    jsr asmblock_find_opcode
    ASMBLOCK_JCC asmblock_select_numeric_zp
asmblock_select_numeric_absolute:
    lda #ACTC_ASM_MODE_ABSOLUTE
    jmp asmblock_emit_selected_mode
asmblock_select_numeric_zp:
    lda #ACTC_ASM_MODE_ZP
    jmp asmblock_emit_selected_mode

asmblock_parse_no_operand:
    lda #ACTC_ASM_MODE_IMPLIED
    jsr asmblock_find_opcode
    ASMBLOCK_JCC asmblock_parse_no_operand_implied
    lda #ACTC_ASM_MODE_ACCUMULATOR
    jsr asmblock_find_opcode
    ASMBLOCK_JCS asmblock_parse_operand_fail
    lda #ACTC_ASM_MODE_ACCUMULATOR
    jmp asmblock_emit_selected_mode
asmblock_parse_no_operand_implied:
    lda #ACTC_ASM_MODE_IMPLIED
    jmp asmblock_emit_selected_mode

asmblock_parse_immediate:
    jsr asmblock_consume_char
    jsr asmblock_peek_char
    cmp #'<'
    ASMBLOCK_JEQ asmblock_parse_immediate_low
    cmp #'>'
    ASMBLOCK_JEQ asmblock_parse_immediate_high
    jsr asmblock_parse_value
    ASMBLOCK_JCS asmblock_parse_operand_fail
    jsr asmblock_parse_optional_addend
    ASMBLOCK_JCS asmblock_parse_operand_fail
    lda asmblock_value_kind
    ASMBLOCK_JNE asmblock_parse_operand_fail
    lda asmblock_value_hi
    ASMBLOCK_JNE asmblock_parse_operand_fail
    lda #ACTC_ASM_MODE_IMMEDIATE
    jmp asmblock_emit_selected_mode
asmblock_parse_immediate_low:
    lda #ACTC_ASMBLOCK_RELOC_LOW
    bne asmblock_parse_immediate_byte_symbol
asmblock_parse_immediate_high:
    lda #ACTC_ASMBLOCK_RELOC_HIGH
asmblock_parse_immediate_byte_symbol:
    sta asmblock_reloc_kind
    jsr asmblock_consume_char
    jsr asmblock_parse_value
    ASMBLOCK_JCS asmblock_parse_operand_fail
    jsr asmblock_parse_optional_addend
    ASMBLOCK_JCS asmblock_parse_operand_fail
    lda asmblock_value_kind
    ASMBLOCK_JNE asmblock_parse_immediate_byte_ready
    lda asmblock_reloc_kind
    cmp #ACTC_ASMBLOCK_RELOC_HIGH
    ASMBLOCK_JNE asmblock_parse_immediate_numeric_low
    lda asmblock_value_hi
    sta asmblock_value_lo
asmblock_parse_immediate_numeric_low:
    lda #$00
    sta asmblock_value_hi
asmblock_parse_immediate_byte_ready:
    lda #ACTC_ASM_MODE_IMMEDIATE
    jmp asmblock_emit_selected_mode

asmblock_parse_parenthesized:
    jsr asmblock_consume_char
    jsr asmblock_skip_horizontal_space
    jsr asmblock_parse_value
    ASMBLOCK_JCS asmblock_parse_operand_fail
    jsr asmblock_parse_optional_addend
    ASMBLOCK_JCS asmblock_parse_operand_fail
    jsr asmblock_skip_horizontal_space
    jsr asmblock_peek_char
    cmp #','
    ASMBLOCK_JNE asmblock_parse_parenthesized_close
    jsr asmblock_consume_char
    jsr asmblock_skip_horizontal_space
    jsr asmblock_parse_register
    ASMBLOCK_JCS asmblock_parse_operand_fail
    cmp #'X'
    ASMBLOCK_JNE asmblock_parse_operand_fail
    jsr asmblock_skip_horizontal_space
    jsr asmblock_require_close_paren
    ASMBLOCK_JCS asmblock_parse_operand_fail
    lda asmblock_value_kind
    ASMBLOCK_JNE asmblock_parse_operand_fail
    lda asmblock_value_hi
    ASMBLOCK_JNE asmblock_parse_operand_fail
    lda #ACTC_ASM_MODE_INDEXED_INDIRECT
    jmp asmblock_emit_selected_mode

asmblock_parse_parenthesized_close:
    jsr asmblock_require_close_paren
    ASMBLOCK_JCS asmblock_parse_operand_fail
    jsr asmblock_skip_horizontal_space
    jsr asmblock_peek_char
    cmp #','
    ASMBLOCK_JNE asmblock_parse_indirect
    jsr asmblock_consume_char
    jsr asmblock_skip_horizontal_space
    jsr asmblock_parse_register
    ASMBLOCK_JCS asmblock_parse_operand_fail
    cmp #'Y'
    ASMBLOCK_JNE asmblock_parse_operand_fail
    lda asmblock_value_kind
    ASMBLOCK_JNE asmblock_parse_operand_fail
    lda asmblock_value_hi
    ASMBLOCK_JNE asmblock_parse_operand_fail
    lda #ACTC_ASM_MODE_INDIRECT_INDEXED
    jmp asmblock_emit_selected_mode
asmblock_parse_indirect:
    lda #ACTC_ASM_MODE_INDIRECT
    jmp asmblock_emit_selected_mode

asmblock_parse_branch:
    jsr asmblock_parse_value
    ASMBLOCK_JCS asmblock_parse_operand_fail
    lda asmblock_value_kind
    ASMBLOCK_JEQ asmblock_parse_operand_fail
    jsr asmblock_skip_horizontal_space
    jsr asmblock_peek_char
    cmp #','
    ASMBLOCK_JEQ asmblock_parse_operand_fail
    lda #ACTC_ASM_MODE_RELATIVE
    jsr asmblock_find_opcode
    ASMBLOCK_JCS asmblock_parse_operand_fail
    lda asmblock_opcode
    jsr asmblock_emit_byte
    ASMBLOCK_JCS asmblock_parse_operand_fail
    lda asmblock_pass
    ASMBLOCK_JEQ asmblock_parse_branch_placeholder
    jsr asmblock_find_label
    ASMBLOCK_JCS asmblock_parse_operand_fail
    lda ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_LABEL_BASE,x
    sta asmblock_target_offset
    lda asmblock_code_offset
    clc
    adc #$01
    sta asmblock_next_offset
    lda asmblock_target_offset
    cmp asmblock_next_offset
    ASMBLOCK_JCC asmblock_parse_branch_backward
    sec
    sbc asmblock_next_offset
    cmp #$80
    ASMBLOCK_JCS asmblock_parse_operand_fail
    jmp asmblock_parse_branch_emit
asmblock_parse_branch_backward:
    lda asmblock_next_offset
    sec
    sbc asmblock_target_offset
    cmp #$81
    ASMBLOCK_JCS asmblock_parse_operand_fail
    lda asmblock_target_offset
    sec
    sbc asmblock_next_offset
asmblock_parse_branch_emit:
    jsr asmblock_emit_byte
    rts
asmblock_parse_branch_placeholder:
    lda #$00
    jsr asmblock_emit_byte
    rts

asmblock_parse_operand_fail:
    sec
    rts

asmblock_emit_selected_mode:
    sta asmblock_mode
    jsr asmblock_find_opcode
    ASMBLOCK_JCS asmblock_emit_selected_fail
    lda asmblock_opcode
    jsr asmblock_emit_byte
    ASMBLOCK_JCS asmblock_emit_selected_fail
    lda asmblock_mode
    cmp #ACTC_ASM_MODE_IMPLIED
    ASMBLOCK_JEQ asmblock_emit_selected_done
    cmp #ACTC_ASM_MODE_ACCUMULATOR
    ASMBLOCK_JEQ asmblock_emit_selected_done
    cmp #ACTC_ASM_MODE_IMMEDIATE
    ASMBLOCK_JEQ asmblock_emit_selected_byte
    cmp #ACTC_ASM_MODE_ZP
    ASMBLOCK_JEQ asmblock_emit_selected_byte
    cmp #ACTC_ASM_MODE_ZP_X
    ASMBLOCK_JEQ asmblock_emit_selected_byte
    cmp #ACTC_ASM_MODE_ZP_Y
    ASMBLOCK_JEQ asmblock_emit_selected_byte
    cmp #ACTC_ASM_MODE_INDEXED_INDIRECT
    ASMBLOCK_JEQ asmblock_emit_selected_byte
    cmp #ACTC_ASM_MODE_INDIRECT_INDEXED
    ASMBLOCK_JEQ asmblock_emit_selected_byte
    lda asmblock_value_kind
    ASMBLOCK_JEQ asmblock_emit_selected_word
    lda asmblock_pass
    ASMBLOCK_JEQ asmblock_emit_selected_symbol_placeholder
    jsr asmblock_resolve_symbol
    ASMBLOCK_JCS asmblock_emit_selected_fail
    jsr asmblock_add_reloc
    ASMBLOCK_JCS asmblock_emit_selected_fail
asmblock_emit_selected_symbol_placeholder:
    lda #$00
    jsr asmblock_emit_byte
    ASMBLOCK_JCS asmblock_emit_selected_fail
    lda #$00
    jsr asmblock_emit_byte
    rts
asmblock_emit_selected_word:
    lda asmblock_value_lo
    jsr asmblock_emit_byte
    ASMBLOCK_JCS asmblock_emit_selected_fail
    lda asmblock_value_hi
    jsr asmblock_emit_byte
    rts
asmblock_emit_selected_byte:
    lda asmblock_value_kind
    ASMBLOCK_JEQ asmblock_emit_selected_numeric_byte
    lda asmblock_mode
    cmp #ACTC_ASM_MODE_IMMEDIATE
    ASMBLOCK_JNE asmblock_emit_selected_fail
    lda asmblock_reloc_kind
    ASMBLOCK_JEQ asmblock_emit_selected_fail
    lda asmblock_pass
    ASMBLOCK_JEQ asmblock_emit_selected_symbol_byte_placeholder
    jsr asmblock_resolve_symbol
    ASMBLOCK_JCS asmblock_emit_selected_fail
    jsr asmblock_add_reloc
    ASMBLOCK_JCS asmblock_emit_selected_fail
asmblock_emit_selected_symbol_byte_placeholder:
    lda #$00
    jsr asmblock_emit_byte
    rts
asmblock_emit_selected_numeric_byte:
    lda asmblock_value_hi
    ASMBLOCK_JNE asmblock_emit_selected_fail
    lda asmblock_value_lo
    jsr asmblock_emit_byte
    rts
asmblock_emit_selected_done:
    clc
    rts
asmblock_emit_selected_fail:
    sec
    rts

asmblock_parse_optional_index:
    jsr asmblock_peek_char
    cmp #','
    ASMBLOCK_JNE asmblock_parse_optional_index_done
    jsr asmblock_consume_char
    jsr asmblock_skip_horizontal_space
    jsr asmblock_parse_register
    ASMBLOCK_JCS asmblock_parse_optional_index_fail
    cmp #'X'
    ASMBLOCK_JEQ asmblock_parse_optional_index_x
    cmp #'Y'
    ASMBLOCK_JNE asmblock_parse_optional_index_fail
    lda #$02
    sta asmblock_index_kind
    clc
    rts
asmblock_parse_optional_index_x:
    lda #$01
    sta asmblock_index_kind
asmblock_parse_optional_index_done:
    clc
    rts
asmblock_parse_optional_index_fail:
    sec
    rts

asmblock_parse_register:
    jsr asmblock_peek_char
    ASMBLOCK_JCS asmblock_parse_register_fail
    jsr asmblock_uppercase
    cmp #'X'
    ASMBLOCK_JEQ asmblock_parse_register_valid
    cmp #'Y'
    ASMBLOCK_JNE asmblock_parse_register_fail
asmblock_parse_register_valid:
    pha
    jsr asmblock_consume_char
    pla
    clc
    rts
asmblock_parse_register_fail:
    sec
    rts

asmblock_require_close_paren:
    jsr asmblock_peek_char
    cmp #')'
    ASMBLOCK_JNE asmblock_require_close_paren_fail
    jsr asmblock_consume_char
    rts
asmblock_require_close_paren_fail:
    sec
    rts

asmblock_parse_value:
    lda #$00
    sta asmblock_resident_symbol_valid
    sta asmblock_addend
    jsr asmblock_peek_char
    ASMBLOCK_JCS asmblock_parse_value_fail
    cmp #'$'
    ASMBLOCK_JEQ asmblock_parse_hex
    cmp #'%'
    ASMBLOCK_JEQ asmblock_parse_binary
    cmp #'0'
    ASMBLOCK_JCC asmblock_parse_value_symbol
    cmp #'9'+1
    ASMBLOCK_JCC asmblock_parse_decimal
asmblock_parse_value_symbol:
    lda asmblock_pass
    ASMBLOCK_JEQ asmblock_parse_value_symbol_parse
    ldy #$00
    lda #ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_PTR_FN_LO
    jsr asmblock_call_context_function
    ASMBLOCK_JCS asmblock_parse_value_symbol_parse
    lda #$01
    sta asmblock_resident_symbol_valid
asmblock_parse_value_symbol_parse:
    jsr asmblock_parse_identifier
    ASMBLOCK_JCS asmblock_parse_value_fail
    lda #$01
    sta asmblock_value_kind
    clc
    rts

asmblock_parse_decimal:
    ldy #$00
    lda #ACTC_OVERLAY_CTX_SOURCE_READER_PEEK_TOKEN_FN_LO
    jsr asmblock_call_context_function
    ASMBLOCK_JCS asmblock_parse_value_fail
    cmp #SOURCE_TOKEN_DECIMAL
    ASMBLOCK_JNE asmblock_parse_value_fail
    lda #ACTC_OVERLAY_CTX_SOURCE_READER_TOKEN_VALUE_PTR_LO
    jsr asmblock_load_context_ptr
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta asmblock_value_lo
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta asmblock_value_hi
asmblock_parse_decimal_consume:
    jsr asmblock_peek_char
    cmp #'0'
    ASMBLOCK_JCC asmblock_parse_decimal_done
    cmp #'9'+1
    ASMBLOCK_JCS asmblock_parse_decimal_done
    jsr asmblock_consume_char
    ASMBLOCK_JCS asmblock_parse_value_fail
    jmp asmblock_parse_decimal_consume
asmblock_parse_decimal_done:
    lda #$00
    sta asmblock_value_kind
    clc
    rts

asmblock_parse_hex:
    jsr asmblock_consume_char
    lda #$00
    sta asmblock_value_lo
    sta asmblock_value_hi
    sta asmblock_digit_count
asmblock_parse_hex_loop:
    jsr asmblock_peek_char
    jsr asmblock_hex_nibble
    ASMBLOCK_JCS asmblock_parse_hex_done
    sta asmblock_digit
    lda asmblock_digit_count
    cmp #$04
    ASMBLOCK_JCS asmblock_parse_value_fail
    ldx #$04
asmblock_parse_hex_shift:
    asl asmblock_value_lo
    rol asmblock_value_hi
    dex
    ASMBLOCK_JNE asmblock_parse_hex_shift
    lda asmblock_value_lo
    ora asmblock_digit
    sta asmblock_value_lo
    jsr asmblock_consume_char
    inc asmblock_digit_count
    jmp asmblock_parse_hex_loop
asmblock_parse_hex_done:
    lda asmblock_digit_count
    ASMBLOCK_JEQ asmblock_parse_value_fail
    lda #$00
    sta asmblock_value_kind
    clc
    rts

asmblock_parse_binary:
    jsr asmblock_consume_char
    lda #$00
    sta asmblock_value_lo
    sta asmblock_value_hi
    sta asmblock_digit_count
asmblock_parse_binary_loop:
    jsr asmblock_peek_char
    cmp #'0'
    ASMBLOCK_JEQ asmblock_parse_binary_digit
    cmp #'1'
    ASMBLOCK_JNE asmblock_parse_binary_done
asmblock_parse_binary_digit:
    pha
    lda asmblock_digit_count
    cmp #16
    ASMBLOCK_JCS asmblock_parse_binary_too_long
    pla
    sec
    sbc #'0'
    sta asmblock_digit
    asl asmblock_value_lo
    rol asmblock_value_hi
    lda asmblock_value_lo
    ora asmblock_digit
    sta asmblock_value_lo
    jsr asmblock_consume_char
    inc asmblock_digit_count
    jmp asmblock_parse_binary_loop
asmblock_parse_binary_too_long:
    pla
    jmp asmblock_parse_value_fail
asmblock_parse_binary_done:
    lda asmblock_digit_count
    ASMBLOCK_JEQ asmblock_parse_value_fail
    lda #$00
    sta asmblock_value_kind
    clc
    rts
asmblock_parse_value_fail:
    sec
    rts

; Native block pages retain one signed-byte addend per relocation. This covers
; byte selection within CARD/INT/REAL/record storage without reducing code,
; label, or relocation capacity.
asmblock_parse_optional_addend:
    lda asmblock_value_kind
    ASMBLOCK_JEQ asmblock_parse_optional_addend_done
    jsr asmblock_skip_horizontal_space
    ASMBLOCK_JCS asmblock_parse_optional_addend_fail
    jsr asmblock_peek_char
    cmp #'+'
    ASMBLOCK_JEQ asmblock_parse_optional_addend_positive
    cmp #'-'
    ASMBLOCK_JNE asmblock_parse_optional_addend_done
    lda #$01
    bne asmblock_parse_optional_addend_sign
asmblock_parse_optional_addend_positive:
    lda #$00
asmblock_parse_optional_addend_sign:
    sta asmblock_addend_negative
    jsr asmblock_consume_char
    ASMBLOCK_JCS asmblock_parse_optional_addend_fail
    jsr asmblock_skip_horizontal_space
    ASMBLOCK_JCS asmblock_parse_optional_addend_fail
    jsr asmblock_peek_char
    cmp #'$'
    ASMBLOCK_JEQ asmblock_parse_optional_addend_hex
    cmp #'%'
    ASMBLOCK_JEQ asmblock_parse_optional_addend_binary
    cmp #'0'
    ASMBLOCK_JCC asmblock_parse_optional_addend_fail
    cmp #'9'+1
    ASMBLOCK_JCS asmblock_parse_optional_addend_fail
    jsr asmblock_parse_addend_decimal
    jmp asmblock_parse_optional_addend_value
asmblock_parse_optional_addend_hex:
    jsr asmblock_parse_hex
    jmp asmblock_parse_optional_addend_value
asmblock_parse_optional_addend_binary:
    jsr asmblock_parse_binary
asmblock_parse_optional_addend_value:
    ASMBLOCK_JCS asmblock_parse_optional_addend_fail
    lda asmblock_value_hi
    ASMBLOCK_JNE asmblock_parse_optional_addend_fail
    lda asmblock_addend_negative
    ASMBLOCK_JNE asmblock_parse_optional_addend_negative
    lda asmblock_value_lo
    cmp #$80
    ASMBLOCK_JCS asmblock_parse_optional_addend_fail
    sta asmblock_addend
    lda #$01
    sta asmblock_value_kind
asmblock_parse_optional_addend_done:
    clc
    rts
asmblock_parse_optional_addend_negative:
    lda asmblock_value_lo
    ASMBLOCK_JEQ asmblock_parse_optional_addend_zero
    cmp #$81
    ASMBLOCK_JCS asmblock_parse_optional_addend_fail
    eor #$FF
    clc
    adc #$01
    sta asmblock_addend
asmblock_parse_optional_addend_zero:
    lda #$01
    sta asmblock_value_kind
    clc
    rts
asmblock_parse_optional_addend_fail:
    sec
    rts

; Parse a decimal addend locally so the resident symbol copied for pass-1
; binding is not overwritten by the shared token reader.
asmblock_parse_addend_decimal:
    lda #$00
    sta asmblock_value_lo
    sta asmblock_value_hi
    sta asmblock_digit_count
asmblock_parse_addend_decimal_loop:
    jsr asmblock_peek_char
    cmp #'0'
    ASMBLOCK_JCC asmblock_parse_addend_decimal_done
    cmp #'9'+1
    ASMBLOCK_JCS asmblock_parse_addend_decimal_done
    sec
    sbc #'0'
    sta asmblock_digit
    lda asmblock_value_lo
    sta asmblock_addend_temp_lo
    lda asmblock_value_hi
    sta asmblock_addend_temp_hi
    asl asmblock_value_lo
    rol asmblock_value_hi
    asl asmblock_addend_temp_lo
    rol asmblock_addend_temp_hi
    asl asmblock_addend_temp_lo
    rol asmblock_addend_temp_hi
    asl asmblock_addend_temp_lo
    rol asmblock_addend_temp_hi
    clc
    lda asmblock_value_lo
    adc asmblock_addend_temp_lo
    sta asmblock_value_lo
    lda asmblock_value_hi
    adc asmblock_addend_temp_hi
    ASMBLOCK_JCS asmblock_parse_optional_addend_fail
    sta asmblock_value_hi
    clc
    lda asmblock_value_lo
    adc asmblock_digit
    sta asmblock_value_lo
    lda asmblock_value_hi
    adc #$00
    ASMBLOCK_JCS asmblock_parse_optional_addend_fail
    sta asmblock_value_hi
    jsr asmblock_consume_char
    ASMBLOCK_JCS asmblock_parse_optional_addend_fail
    inc asmblock_digit_count
    jmp asmblock_parse_addend_decimal_loop
asmblock_parse_addend_decimal_done:
    lda asmblock_digit_count
    ASMBLOCK_JEQ asmblock_parse_optional_addend_fail
    clc
    rts

asmblock_hex_nibble:
    jsr asmblock_uppercase
    cmp #'0'
    ASMBLOCK_JCC asmblock_hex_nibble_fail
    cmp #'9'+1
    ASMBLOCK_JCC asmblock_hex_nibble_digit
    cmp #'A'
    ASMBLOCK_JCC asmblock_hex_nibble_fail
    cmp #'F'+1
    ASMBLOCK_JCS asmblock_hex_nibble_fail
    sec
    sbc #('A'-10)
    clc
    rts
asmblock_hex_nibble_digit:
    sec
    sbc #'0'
    clc
    rts
asmblock_hex_nibble_fail:
    sec
    rts

asmblock_resolve_symbol:
    jsr asmblock_find_label
    ASMBLOCK_JCS asmblock_resolve_symbol_var
    txa
    sta asmblock_reloc_target
    clc
    rts
asmblock_resolve_symbol_var:
    lda asmblock_resident_symbol_valid
    ASMBLOCK_JEQ asmblock_resolve_symbol_fail
    ldy #$00
    lda #ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    jsr asmblock_call_context_function
    ASMBLOCK_JCS asmblock_resolve_symbol_export
    cpx #16
    ASMBLOCK_JCS asmblock_resolve_symbol_fail
    txa
    ora #ACTC_ASMBLOCK_RELOC_VAR
    sta asmblock_reloc_target
    clc
    rts
asmblock_resolve_symbol_export:
    ldy #$00
    lda #ACTC_OVERLAY_CTX_FIND_EXPORT_INDEX_FN_LO
    jsr asmblock_call_context_function
    ASMBLOCK_JCS asmblock_resolve_symbol_fail
    cpx #16
    ASMBLOCK_JCS asmblock_resolve_symbol_fail
    txa
    ora #ACTC_ASMBLOCK_RELOC_EXPORT
    sta asmblock_reloc_target
    clc
    rts
asmblock_resolve_symbol_fail:
    sec
    rts

asmblock_add_reloc:
    lda asmblock_reloc_count
    cmp #ACTC_ASMBLOCK_RELOC_MAX
    ASMBLOCK_JCS asmblock_add_reloc_fail
    asl a
    tay
    lda asmblock_code_offset
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_RELOC_BASE,y
    iny
    lda asmblock_reloc_target
    ora asmblock_reloc_kind
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_RELOC_BASE,y
    ldx asmblock_reloc_count
    lda asmblock_addend
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_RELOC_ADDEND_BASE,x
    inc asmblock_reloc_count
    clc
    rts
asmblock_add_reloc_fail:
    sec
    rts

asmblock_emit_byte:
    pha
    lda asmblock_code_offset
    cmp #ACTC_ASMBLOCK_CODE_CAPACITY
    ASMBLOCK_JCS asmblock_emit_byte_fail_pop
    lda asmblock_pass
    ASMBLOCK_JEQ asmblock_emit_byte_advance
    ldy asmblock_code_offset
    pla
    sta ACTC_ASMBLOCK_PAGE_BUFFER+ACTC_ASMBLOCK_CODE_BASE,y
    inc asmblock_code_offset
    clc
    rts
asmblock_emit_byte_advance:
    pla
    inc asmblock_code_offset
    clc
    rts
asmblock_emit_byte_fail_pop:
    pla
    sec
    rts

asmblock_find_opcode:
    sta asmblock_mode
    lda #<asmblock_opcode_table
    sta ACTC_OVERLAY_WORK_ZP
    lda #>asmblock_opcode_table
    sta ACTC_OVERLAY_WORK_ZP+1
asmblock_find_opcode_loop:
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    ASMBLOCK_JEQ asmblock_find_opcode_fail
    cmp asmblock_mnemonic
    ASMBLOCK_JNE asmblock_find_opcode_next
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp asmblock_mnemonic+1
    ASMBLOCK_JNE asmblock_find_opcode_next
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp asmblock_mnemonic+2
    ASMBLOCK_JNE asmblock_find_opcode_next
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp asmblock_mode
    ASMBLOCK_JNE asmblock_find_opcode_next
    iny
    lda (ACTC_OVERLAY_WORK_ZP),y
    sta asmblock_opcode
    clc
    rts
asmblock_find_opcode_next:
    clc
    lda ACTC_OVERLAY_WORK_ZP
    adc #$05
    sta ACTC_OVERLAY_WORK_ZP
    ASMBLOCK_JCC asmblock_find_opcode_loop
    inc ACTC_OVERLAY_WORK_ZP+1
    jmp asmblock_find_opcode_loop
asmblock_find_opcode_fail:
    sec
    rts

asmblock_find_label:
    lda #$00
    sta asmblock_label_scan
asmblock_find_label_loop:
    lda asmblock_label_scan
    cmp asmblock_label_count
    ASMBLOCK_JEQ asmblock_find_label_fail
    tax
    jsr asmblock_set_label_ptr_x
    ldy #$00
asmblock_find_label_compare:
    lda (ACTC_OVERLAY_WORK_ZP),y
    cmp asmblock_symbol,y
    ASMBLOCK_JNE asmblock_find_label_next
    ASMBLOCK_JEQ asmblock_find_label_test_end
asmblock_find_label_test_end:
    lda asmblock_symbol,y
    ASMBLOCK_JEQ asmblock_find_label_done
    iny
    cpy #ASMBLOCK_SYMBOL_LIMIT+1
    ASMBLOCK_JCC asmblock_find_label_compare
asmblock_find_label_next:
    inc asmblock_label_scan
    jmp asmblock_find_label_loop
asmblock_find_label_done:
    ldx asmblock_label_scan
    clc
    rts
asmblock_find_label_fail:
    sec
    rts

asmblock_set_label_ptr_x:
    lda #<asmblock_label_names
    sta ACTC_OVERLAY_WORK_ZP
    lda #>asmblock_label_names
    sta ACTC_OVERLAY_WORK_ZP+1
asmblock_set_label_ptr_x_loop:
    cpx #$00
    ASMBLOCK_JEQ asmblock_set_label_ptr_x_done
    clc
    lda ACTC_OVERLAY_WORK_ZP
    adc #ASMBLOCK_SYMBOL_LIMIT+1
    sta ACTC_OVERLAY_WORK_ZP
    bcc :+
    inc ACTC_OVERLAY_WORK_ZP+1
:   dex
    ASMBLOCK_JNE asmblock_set_label_ptr_x_loop
asmblock_set_label_ptr_x_done:
    rts

asmblock_parse_identifier:
    lda #$00
    sta asmblock_symbol_len
    jsr asmblock_peek_char
    ASMBLOCK_JCS asmblock_parse_identifier_fail
    jsr asmblock_uppercase
    jsr asmblock_identifier_start_valid
    ASMBLOCK_JCS asmblock_parse_identifier_fail
asmblock_parse_identifier_loop:
    ldx asmblock_symbol_len
    cpx #ASMBLOCK_SYMBOL_LIMIT
    ASMBLOCK_JCS asmblock_parse_identifier_fail
    sta asmblock_symbol,x
    jsr asmblock_consume_char
    ASMBLOCK_JCS asmblock_parse_identifier_fail
    inc asmblock_symbol_len
    jsr asmblock_peek_char
    ASMBLOCK_JCS asmblock_parse_identifier_fail
    jsr asmblock_uppercase
    jsr asmblock_identifier_body_valid
    ASMBLOCK_JCC asmblock_parse_identifier_loop
    ldx asmblock_symbol_len
    lda #$00
    sta asmblock_symbol,x
    clc
    rts
asmblock_parse_identifier_fail:
    sec
    rts

asmblock_identifier_start_valid:
    cmp #'_'
    ASMBLOCK_JEQ asmblock_identifier_valid
    cmp #'A'
    ASMBLOCK_JCC asmblock_identifier_invalid
    cmp #'Z'+1
    ASMBLOCK_JCS asmblock_identifier_invalid
asmblock_identifier_valid:
    clc
    rts
asmblock_identifier_body_valid:
    jsr asmblock_identifier_start_valid
    ASMBLOCK_JCC asmblock_identifier_valid
    cmp #'0'
    ASMBLOCK_JCC asmblock_identifier_invalid
    cmp #'9'+1
    ASMBLOCK_JCC asmblock_identifier_valid
asmblock_identifier_invalid:
    sec
    rts

asmblock_finish_statement:
    jsr asmblock_skip_horizontal_space
    ASMBLOCK_JCS asmblock_finish_statement_fail
    jsr asmblock_peek_char
    ASMBLOCK_JEQ asmblock_finish_statement_fail
    cmp #';'
    ASMBLOCK_JEQ asmblock_skip_comment
    cmp #10
    ASMBLOCK_JEQ asmblock_finish_statement_done
    cmp #13
    ASMBLOCK_JEQ asmblock_finish_statement_done
    cmp #']'
    ASMBLOCK_JEQ asmblock_finish_statement_done
asmblock_finish_statement_fail:
    sec
    rts
asmblock_finish_statement_done:
    clc
    rts

asmblock_skip_comment:
    jsr asmblock_consume_char
asmblock_skip_comment_loop:
    jsr asmblock_peek_char
    ASMBLOCK_JCS asmblock_skip_comment_fail
    ASMBLOCK_JEQ asmblock_skip_comment_fail
    cmp #10
    ASMBLOCK_JEQ asmblock_skip_comment_done
    cmp #13
    ASMBLOCK_JEQ asmblock_skip_comment_done
    jsr asmblock_consume_char
    ASMBLOCK_JCC asmblock_skip_comment_loop
asmblock_skip_comment_fail:
    sec
    rts
asmblock_skip_comment_done:
    clc
    rts

asmblock_skip_all_space:
    jsr asmblock_peek_char
    ASMBLOCK_JCS asmblock_skip_space_fail
    cmp #' '
    ASMBLOCK_JEQ asmblock_skip_all_space_consume
    cmp #9
    ASMBLOCK_JEQ asmblock_skip_all_space_consume
    cmp #10
    ASMBLOCK_JEQ asmblock_skip_all_space_consume
    cmp #13
    ASMBLOCK_JNE asmblock_skip_space_done
asmblock_skip_all_space_consume:
    jsr asmblock_consume_char
    ASMBLOCK_JCC asmblock_skip_all_space
asmblock_skip_space_fail:
    sec
    rts

asmblock_skip_horizontal_space:
    jsr asmblock_peek_char
    ASMBLOCK_JCS asmblock_skip_space_fail
    cmp #' '
    ASMBLOCK_JEQ asmblock_skip_horizontal_space_consume
    cmp #9
    ASMBLOCK_JNE asmblock_skip_space_done
asmblock_skip_horizontal_space_consume:
    jsr asmblock_consume_char
    ASMBLOCK_JCC asmblock_skip_horizontal_space
    ASMBLOCK_JCS asmblock_skip_space_fail
asmblock_skip_space_done:
    clc
    rts

asmblock_skip_source_space:
    ldy #$00
    lda #ACTC_OVERLAY_CTX_SKIP_SOURCE_SPACES_FN_LO
    jsr asmblock_call_context_function
    clc
    rts

asmblock_peek_char:
    ldy #$00
    lda #ACTC_OVERLAY_CTX_PEEK_SCAN_Y_FN_LO
    jsr asmblock_call_context_function
    clc
    rts

asmblock_consume_char:
    ldy #$00
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_FN_LO
    jmp asmblock_call_context_function

asmblock_pattern_matches:
    jsr asmblock_set_const_ptr
    ldy #$00
    lda #ACTC_OVERLAY_CTX_PATTERN_MATCHES_SCAN_PTR_FN_LO
    jmp asmblock_call_context_function

asmblock_pattern_matches_keyword:
    jsr asmblock_set_const_ptr
    ldy #$00
    lda #ACTC_OVERLAY_CTX_PATTERN_MATCHES_SCAN_PTR_KEYWORD_FN_LO
    jmp asmblock_call_context_function

asmblock_consume_pattern:
    jsr asmblock_set_const_ptr
    ldy #$00
    lda #ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_BY_CONST_FN_LO
    jmp asmblock_call_context_function

asmblock_set_const_ptr:
    sta asmblock_saved_a
    sty asmblock_saved_y
    lda #ACTC_OVERLAY_CTX_CONST_PTR_SLOT_PTR_LO
    jsr asmblock_load_context_ptr
    ldy #$00
    lda asmblock_saved_a
    sta (ACTC_OVERLAY_WORK_ZP),y
    iny
    lda asmblock_saved_y
    sta (ACTC_OVERLAY_WORK_ZP),y
    rts

asmblock_load_current_proc:
    lda #ACTC_OVERLAY_CTX_CURRENT_PROC_INDEX_PTR_LO
    jsr asmblock_load_context_ptr
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    rts

asmblock_store_current_proc:
    pha
    lda #ACTC_OVERLAY_CTX_CURRENT_PROC_INDEX_PTR_LO
    jsr asmblock_load_context_ptr
    pla
    ldy #$00
    sta (ACTC_OVERLAY_WORK_ZP),y
    rts

asmblock_publish_count:
    lda #ACTC_OVERLAY_CTX_IMPORT_FLAGS_PTR_LO
    jsr asmblock_load_context_ptr
    ldy #$00
    lda (ACTC_OVERLAY_WORK_ZP),y
    and #$0F
    sta asmblock_saved_a
    lda asmblock_count
    asl a
    asl a
    asl a
    asl a
    ora asmblock_saved_a
    sta (ACTC_OVERLAY_WORK_ZP),y
    rts

asmblock_clear_page:
    ldy #$00
    lda #$00
asmblock_clear_page_loop:
    sta ACTC_ASMBLOCK_PAGE_BUFFER,y
    iny
    ASMBLOCK_JNE asmblock_clear_page_loop
    rts

asmblock_store_page:
    lda #$00
    sta ACTC_ASMBLOCK_REU_PARAMS+0
    lda asmblock_count
    clc
    adc #ACTC_ASMBLOCK_REU_HI_BASE
    sta ACTC_ASMBLOCK_REU_PARAMS+1
    lda #ACTC_ASMBLOCK_REU_BANK
    sta ACTC_ASMBLOCK_REU_PARAMS+2
    lda #<ACTC_ASMBLOCK_PAGE_BUFFER
    sta ACTC_ASMBLOCK_REU_PARAMS+3
    lda #>ACTC_ASMBLOCK_PAGE_BUFFER
    sta ACTC_ASMBLOCK_REU_PARAMS+4
    lda #$00
    sta ACTC_ASMBLOCK_REU_PARAMS+5
    lda #$01
    sta ACTC_ASMBLOCK_REU_PARAMS+6
    lda #tool_file_status_fail
    sta ACTC_ASMBLOCK_REU_PARAMS+7
    ldx #ACTC_ASMBLOCK_REU_PARAMS
    jsr svc_reu_write_sc0
    lda ACTC_ASMBLOCK_REU_PARAMS+7
    cmp #tool_file_status_ok
    ASMBLOCK_JEQ asmblock_store_page_done
    sec
    rts
asmblock_store_page_done:
    clc
    rts

asmblock_uppercase:
    cmp #'a'
    ASMBLOCK_JCC asmblock_uppercase_done
    cmp #'z'+1
    ASMBLOCK_JCS asmblock_uppercase_done
    and #$DF
asmblock_uppercase_done:
    rts

asmblock_load_context_ptr:
    tay
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP
    iny
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta ACTC_OVERLAY_WORK_ZP+1
    rts

asmblock_call_context_function:
    sta asmblock_call_selector
    sty asmblock_saved_y
    tay
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta asmblock_call_target
    iny
    lda (ACTC_OVERLAY_CONTEXT_ZP),y
    sta asmblock_call_target+1
    sec
    lda asmblock_call_target
    sbc #$01
    sta asmblock_call_minus_one
    lda asmblock_call_target+1
    sbc #$00
    pha
    lda asmblock_call_minus_one
    pha
    ldy asmblock_saved_y
    lda #$00
    rts

asmblock_fail_with_diag:
    sta asmblock_saved_a
    sty asmblock_saved_y
    ldy #ACTC_OVERLAY_CTX_DIAG_PTR_LO
    lda asmblock_saved_a
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    iny
    lda asmblock_saved_y
    sta (ACTC_OVERLAY_CONTEXT_ZP),y
    sec
    rts

.include "actc_asmblock_6502.inc"

asmblock_pattern_proc:
    .asciiz "PROC"
asmblock_pattern_func:
    .asciiz "FUNC"
asmblock_pattern_keyword:
    .asciiz "ASMBLOCK"
asmblock_msg_bad:
    .asciiz "ASM"
asmblock_msg_load:
    .asciiz "LOAD"
asmblock_msg_save:
    .asciiz "SAVE"

asmblock_count:
    .byte $00
asmblock_pass:
    .byte $00
asmblock_code_offset:
    .byte $00
asmblock_label_count:
    .byte $00
asmblock_reloc_count:
    .byte $00
asmblock_symbol_len:
    .byte $00
asmblock_symbol:
    .res ASMBLOCK_SYMBOL_LIMIT+1, $00
asmblock_mnemonic:
    .res 3, $00
asmblock_label_names:
    .res ACTC_ASMBLOCK_LABEL_MAX*(ASMBLOCK_SYMBOL_LIMIT+1), $00
asmblock_label_scan:
    .byte $00
asmblock_opcode:
    .byte $00
asmblock_mode:
    .byte $00
asmblock_value_kind:
    .byte $00
asmblock_value_lo:
    .byte $00
asmblock_value_hi:
    .byte $00
asmblock_index_kind:
    .byte $00
asmblock_resident_symbol_valid:
    .byte $00
asmblock_reloc_target:
    .byte $00
asmblock_reloc_kind:
    .byte $00
asmblock_addend:
    .byte $00
asmblock_addend_negative:
    .byte $00
asmblock_addend_temp_lo:
    .byte $00
asmblock_addend_temp_hi:
    .byte $00
rawblock_force_word:
    .byte $00
rawblock_sum_lo:
    .byte $00
rawblock_sum_hi:
    .byte $00
asmblock_target_offset:
    .byte $00
asmblock_next_offset:
    .byte $00
asmblock_digit_count:
    .byte $00
asmblock_digit:
    .byte $00
asmblock_saved_a:
    .byte $00
asmblock_saved_y:
    .byte $00
asmblock_call_selector:
    .byte $00
asmblock_call_minus_one:
    .byte $00
asmblock_call_target:
    .word $0000
