.include "actedit_overlay_abi.inc"
.include "actedit_overlay_resident.inc"

.export actedit_overlay_header
.export actedit_overlay_entry
.export actedit_overlay_end

PIECE_KIND_SOURCE = 0
PIECE_KIND_PATCH = 1
PIECE_KIND_INSERT = 2
LINE_KIND_SOURCE = 0
LINE_KIND_INSERT = 1
PIECE_MAX = 255

requested_line_lo = ACTEDIT_RES_requested_line_lo
requested_line_hi = ACTEDIT_RES_requested_line_hi
word_tmp = ACTEDIT_RES_word_tmp
actedit_current_line_lo = ACTEDIT_RES_actedit_current_line_lo
actedit_current_line_hi = ACTEDIT_RES_actedit_current_line_hi
actedit_current_source_line_lo = ACTEDIT_RES_actedit_current_source_line_lo
actedit_current_source_line_hi = ACTEDIT_RES_actedit_current_source_line_hi
actedit_current_line_insert_slot = ACTEDIT_RES_actedit_current_line_insert_slot
actedit_piece_count = ACTEDIT_RES_actedit_piece_count
actedit_piece_loaded = ACTEDIT_RES_actedit_piece_loaded
actedit_piece_dirty = ACTEDIT_RES_actedit_piece_dirty
actedit_piece_found_index = ACTEDIT_RES_actedit_piece_found_index
actedit_piece_window = ACTEDIT_RES_actedit_piece_window
actedit_logical_line_count_lo = ACTEDIT_RES_actedit_logical_line_count_lo
actedit_logical_line_count_hi = ACTEDIT_RES_actedit_logical_line_count_hi
actedit_logical_line_index_next_lo = ACTEDIT_RES_actedit_logical_line_index_next_lo
actedit_logical_line_index_next_hi = ACTEDIT_RES_actedit_logical_line_index_next_hi
actedit_logical_line_index_next_bank = ACTEDIT_RES_actedit_logical_line_index_next_bank
actedit_logical_line_index_window_len = ACTEDIT_RES_actedit_logical_line_index_window_len
actedit_logical_line_index_ready = ACTEDIT_RES_actedit_logical_line_index_ready
actedit_logical_index_suffix_count = ACTEDIT_RES_actedit_logical_index_suffix_count
scan_logical_line_lo = ACTEDIT_RES_scan_logical_line_lo
scan_logical_line_hi = ACTEDIT_RES_scan_logical_line_hi
actedit_direct_patch_count = ACTEDIT_RES_actedit_direct_patch_count
actedit_direct_insert_count = ACTEDIT_RES_actedit_direct_insert_count
actedit_direct_remove_count = ACTEDIT_RES_actedit_direct_remove_count
actedit_direct_patch_ready = ACTEDIT_RES_actedit_direct_patch_ready
actedit_direct_insert_ready = ACTEDIT_RES_actedit_direct_insert_ready
actedit_direct_remove_ready = ACTEDIT_RES_actedit_direct_remove_ready
actedit_direct_remove_line_kind = ACTEDIT_RES_actedit_direct_remove_line_kind
actedit_direct_insert_piece_index = ACTEDIT_RES_actedit_direct_insert_piece_index
actedit_direct_insert_slot = ACTEDIT_RES_actedit_direct_insert_slot
actedit_direct_patch_kind = ACTEDIT_RES_actedit_direct_patch_kind
actedit_direct_patch_piece_index = ACTEDIT_RES_actedit_direct_patch_piece_index
actedit_direct_patch_ref_lo = ACTEDIT_RES_actedit_direct_patch_ref_lo
actedit_direct_patch_ref_hi = ACTEDIT_RES_actedit_direct_patch_ref_hi
actedit_direct_patch_piece_count_lo = ACTEDIT_RES_actedit_direct_patch_piece_count_lo
actedit_direct_patch_piece_count_hi = ACTEDIT_RES_actedit_direct_patch_piece_count_hi
actedit_direct_patch_offset_lo = ACTEDIT_RES_actedit_direct_patch_offset_lo
actedit_direct_patch_offset_hi = ACTEDIT_RES_actedit_direct_patch_offset_hi
actedit_direct_patch_source_lo = ACTEDIT_RES_actedit_direct_patch_source_lo
actedit_direct_patch_source_hi = ACTEDIT_RES_actedit_direct_patch_source_hi
actedit_direct_patch_after_lo = ACTEDIT_RES_actedit_direct_patch_after_lo
actedit_direct_patch_after_hi = ACTEDIT_RES_actedit_direct_patch_after_hi
actedit_direct_patch_extra = ACTEDIT_RES_actedit_direct_patch_extra
actedit_direct_patch_slot = ACTEDIT_RES_actedit_direct_patch_slot
actedit_direct_patch_shift_index = ACTEDIT_RES_actedit_direct_patch_shift_index
actedit_pending_insert_anchor_lo = ACTEDIT_RES_actedit_pending_insert_anchor_lo
actedit_pending_insert_anchor_hi = ACTEDIT_RES_actedit_pending_insert_anchor_hi

piece_window_kind = actedit_piece_window+0
piece_window_ref_lo = actedit_piece_window+PIECE_MAX
piece_window_ref_hi = actedit_piece_window+(PIECE_MAX*2)
piece_window_aux = actedit_piece_window+(PIECE_MAX*3)
piece_window_count_lo = actedit_piece_window+(PIECE_MAX*4)
piece_window_count_hi = actedit_piece_window+(PIECE_MAX*5)

load_logical_line_index_entry = ACTEDIT_RES_load_logical_line_index_entry
save_piece_table_window = ACTEDIT_RES_save_piece_table_window
rebuild_logical_line_index = ACTEDIT_RES_rebuild_logical_line_index
append_logical_line_index_entry = ACTEDIT_RES_append_logical_line_index_entry
flush_logical_line_index_window = ACTEDIT_RES_flush_logical_line_index_window
mark_piece_table_dirty = ACTEDIT_RES_mark_piece_table_dirty
actedit_mutation_overlay_command = ACTEDIT_RES_actedit_mutation_overlay_command

.segment "CODE"

actedit_overlay_header:
    .byte 'A','E','O','V'
    .byte ACTEDIT_OVERLAY_ABI_VERSION
    .word ACTEDIT_OVERLAY_EXEC_BASE
    .word actedit_overlay_entry
    .word actedit_overlay_end - actedit_overlay_header
    .word $0000

.assert actedit_overlay_entry = ACTEDIT_OVERLAY_ENTRY, error, "ACTEDIT overlay header size changed"

actedit_overlay_entry:
    lda actedit_mutation_overlay_command
    cmp #ACTEDIT_OVERLAY_CMD_PREPARE_PATCH
    bne :+
    jmp prepare_direct_patch_piece
:
    cmp #ACTEDIT_OVERLAY_CMD_APPLY_PATCH
    bne :+
    jmp apply_direct_patch_piece
:
    cmp #ACTEDIT_OVERLAY_CMD_PREPARE_SPLIT_INSERT
    bne :+
    jmp prepare_direct_split_insert
:
    cmp #ACTEDIT_OVERLAY_CMD_APPLY_SPLIT_INSERT
    bne :+
    jmp apply_direct_split_insert
:
    cmp #ACTEDIT_OVERLAY_CMD_PREPARE_REMOVE
    bne :+
    jmp prepare_direct_remove_line
:
    cmp #ACTEDIT_OVERLAY_CMD_APPLY_REMOVE
    bne :+
    jmp apply_direct_remove_line
:
    sec
    rts

direct_piece_cache_ready:
    lda actedit_piece_dirty
    bne direct_piece_cache_not_ready
    lda actedit_piece_loaded
    beq direct_piece_cache_not_ready
    lda actedit_logical_line_index_ready
    beq direct_piece_cache_not_ready
    clc
    rts
direct_piece_cache_not_ready:
    sec
    rts

prepare_direct_patch_piece:
    lda #$00
    sta actedit_direct_patch_ready
    jsr direct_piece_cache_ready
    bcc :+
    clc
    rts
:
    lda actedit_current_line_lo
    sta requested_line_lo
    lda actedit_current_line_hi
    sta requested_line_hi
    jsr load_logical_line_index_entry
    bcc :+
    clc
    rts
:
    ldx actedit_piece_found_index
    lda piece_window_kind,x
    cmp #PIECE_KIND_SOURCE
    beq prepare_direct_patch_kind_ok
    cmp #PIECE_KIND_PATCH
    beq prepare_direct_patch_kind_ok
    clc
    rts
prepare_direct_patch_kind_ok:
    sta actedit_direct_patch_kind
    stx actedit_direct_patch_piece_index
    lda piece_window_ref_lo,x
    sta actedit_direct_patch_ref_lo
    lda piece_window_ref_hi,x
    sta actedit_direct_patch_ref_hi
    lda piece_window_count_lo,x
    sta actedit_direct_patch_piece_count_lo
    lda piece_window_count_hi,x
    sta actedit_direct_patch_piece_count_hi
    lda word_tmp
    sta actedit_direct_patch_offset_lo
    lda word_tmp+1
    sta actedit_direct_patch_offset_hi
    lda actedit_current_source_line_lo
    sta actedit_direct_patch_source_lo
    lda actedit_current_source_line_hi
    sta actedit_direct_patch_source_hi
    lda actedit_direct_patch_kind
    cmp #PIECE_KIND_PATCH
    beq prepare_direct_patch_validate_patch
    clc
    lda actedit_direct_patch_ref_lo
    adc actedit_direct_patch_offset_lo
    sta word_tmp
    lda actedit_direct_patch_ref_hi
    adc actedit_direct_patch_offset_hi
    sta word_tmp+1
    lda word_tmp
    cmp actedit_direct_patch_source_lo
    bne prepare_direct_patch_done
    lda word_tmp+1
    cmp actedit_direct_patch_source_hi
    bne prepare_direct_patch_done
    jmp prepare_direct_patch_ready
prepare_direct_patch_validate_patch:
    lda actedit_direct_patch_offset_lo
    ora actedit_direct_patch_offset_hi
    bne prepare_direct_patch_done
    lda actedit_direct_patch_ref_lo
    cmp actedit_direct_patch_source_lo
    bne prepare_direct_patch_done
    lda actedit_direct_patch_ref_hi
    cmp actedit_direct_patch_source_hi
    bne prepare_direct_patch_done
prepare_direct_patch_ready:
    lda #$01
    sta actedit_direct_patch_ready
prepare_direct_patch_done:
    clc
    rts

apply_direct_patch_piece:
    lda actedit_direct_patch_ready
    bne :+
    clc
    rts
:
    lda actedit_direct_patch_kind
    cmp #PIECE_KIND_PATCH
    bne apply_direct_patch_split_source
    lda #$00
    sta actedit_direct_patch_after_lo
    sta actedit_direct_patch_after_hi
    sta actedit_direct_patch_extra
    jmp apply_direct_patch_write_replacement

apply_direct_patch_split_source:
    sec
    lda actedit_direct_patch_piece_count_lo
    sbc actedit_direct_patch_offset_lo
    sta actedit_direct_patch_after_lo
    lda actedit_direct_patch_piece_count_hi
    sbc actedit_direct_patch_offset_hi
    sta actedit_direct_patch_after_hi
    sec
    lda actedit_direct_patch_after_lo
    sbc #$01
    sta actedit_direct_patch_after_lo
    lda actedit_direct_patch_after_hi
    sbc #$00
    sta actedit_direct_patch_after_hi
    lda #$00
    sta actedit_direct_patch_extra
    lda actedit_direct_patch_offset_lo
    ora actedit_direct_patch_offset_hi
    beq :+
    inc actedit_direct_patch_extra
:
    lda actedit_direct_patch_after_lo
    ora actedit_direct_patch_after_hi
    beq :+
    inc actedit_direct_patch_extra
:
    lda actedit_direct_patch_extra
    cmp #$02
    bne apply_direct_patch_check_one_slot
    lda actedit_piece_count
    cmp #(PIECE_MAX-1)
    bcc apply_direct_patch_shift_tail
    jmp apply_direct_patch_fallback
apply_direct_patch_check_one_slot:
    cmp #$01
    bne apply_direct_patch_shift_tail
    lda actedit_piece_count
    cmp #PIECE_MAX
    bcc apply_direct_patch_shift_tail
    jmp apply_direct_patch_fallback

apply_direct_patch_shift_tail:
    lda actedit_direct_patch_extra
    beq apply_direct_patch_update_count
    lda actedit_piece_count
    bne :+
    jmp apply_direct_patch_fallback
:
    sec
    sbc #$01
    sta actedit_direct_patch_shift_index
apply_direct_patch_shift_loop:
    lda actedit_direct_patch_shift_index
    cmp actedit_direct_patch_piece_index
    beq apply_direct_patch_update_count
    clc
    adc actedit_direct_patch_extra
    tay
    ldx actedit_direct_patch_shift_index
    jsr copy_piece_x_to_y
    dec actedit_direct_patch_shift_index
    jmp apply_direct_patch_shift_loop

copy_piece_x_to_y:
    lda piece_window_kind,x
    sta piece_window_kind,y
    lda piece_window_ref_lo,x
    sta piece_window_ref_lo,y
    lda piece_window_ref_hi,x
    sta piece_window_ref_hi,y
    lda piece_window_aux,x
    sta piece_window_aux,y
    lda piece_window_count_lo,x
    sta piece_window_count_lo,y
    lda piece_window_count_hi,x
    sta piece_window_count_hi,y
    rts

apply_direct_patch_update_count:
    clc
    lda actedit_piece_count
    adc actedit_direct_patch_extra
    sta actedit_piece_count
apply_direct_patch_write_replacement:
    lda actedit_direct_patch_piece_index
    sta actedit_direct_patch_shift_index
    lda actedit_direct_patch_offset_lo
    ora actedit_direct_patch_offset_hi
    beq apply_direct_patch_write_patch
    ldx actedit_direct_patch_shift_index
    lda #PIECE_KIND_SOURCE
    sta piece_window_kind,x
    lda actedit_direct_patch_ref_lo
    sta piece_window_ref_lo,x
    lda actedit_direct_patch_ref_hi
    sta piece_window_ref_hi,x
    lda #$00
    sta piece_window_aux,x
    lda actedit_direct_patch_offset_lo
    sta piece_window_count_lo,x
    lda actedit_direct_patch_offset_hi
    sta piece_window_count_hi,x
    inc actedit_direct_patch_shift_index

apply_direct_patch_write_patch:
    ldx actedit_direct_patch_shift_index
    lda #PIECE_KIND_PATCH
    sta piece_window_kind,x
    lda actedit_direct_patch_source_lo
    sta piece_window_ref_lo,x
    lda actedit_direct_patch_source_hi
    sta piece_window_ref_hi,x
    lda actedit_direct_patch_slot
    sta piece_window_aux,x
    lda #$01
    sta piece_window_count_lo,x
    lda #$00
    sta piece_window_count_hi,x
    lda actedit_direct_patch_after_lo
    ora actedit_direct_patch_after_hi
    beq apply_direct_patch_persist
    inc actedit_direct_patch_shift_index
    ldx actedit_direct_patch_shift_index
    lda #PIECE_KIND_SOURCE
    sta piece_window_kind,x
    clc
    lda actedit_direct_patch_source_lo
    adc #$01
    sta piece_window_ref_lo,x
    lda actedit_direct_patch_source_hi
    adc #$00
    sta piece_window_ref_hi,x
    lda #$00
    sta piece_window_aux,x
    lda actedit_direct_patch_after_lo
    sta piece_window_count_lo,x
    lda actedit_direct_patch_after_hi
    sta piece_window_count_hi,x

apply_direct_patch_persist:
    jsr save_piece_table_window
    bcs apply_direct_patch_fallback
    lda #$00
    sta actedit_piece_dirty
    sta actedit_logical_line_index_ready
    sta actedit_direct_patch_ready
    lda #$01
    sta actedit_piece_loaded
    inc actedit_direct_patch_count
    lda actedit_direct_patch_kind
    cmp #PIECE_KIND_PATCH
    bne :+
    lda #$01
    sta actedit_logical_line_index_ready
    clc
    rts
:
    jsr rebuild_logical_line_index_suffix
    clc
    rts
apply_direct_patch_fallback:
    jsr mark_piece_table_dirty
    lda #$00
    sta actedit_direct_patch_ready
    clc
    rts

prepare_direct_split_insert:
    lda #$00
    sta actedit_direct_insert_ready
    jsr direct_piece_cache_ready
    bcc :+
    clc
    rts
:
    lda actedit_current_line_lo
    sta requested_line_lo
    lda actedit_current_line_hi
    sta requested_line_hi
    jsr load_logical_line_index_entry
    bcc :+
    clc
    rts
:
    ldx actedit_piece_found_index
    lda piece_window_kind,x
    cmp #PIECE_KIND_PATCH
    beq prepare_direct_split_insert_validate_line
    cmp #PIECE_KIND_INSERT
    bne prepare_direct_split_insert_done
    lda piece_window_aux,x
    cmp actedit_current_line_insert_slot
    bne prepare_direct_split_insert_done
prepare_direct_split_insert_validate_line:
    lda word_tmp
    ora word_tmp+1
    bne prepare_direct_split_insert_done
    lda piece_window_count_lo,x
    cmp #$01
    bne prepare_direct_split_insert_done
    lda piece_window_count_hi,x
    bne prepare_direct_split_insert_done
    lda piece_window_ref_lo,x
    cmp actedit_current_source_line_lo
    bne prepare_direct_split_insert_done
    lda piece_window_ref_hi,x
    cmp actedit_current_source_line_hi
    bne prepare_direct_split_insert_done
    txa
    clc
    adc #$01
    sta actedit_direct_insert_piece_index
    lda #$01
    sta actedit_direct_insert_ready
prepare_direct_split_insert_done:
    clc
    rts

apply_direct_split_insert:
    lda actedit_direct_insert_ready
    bne :+
    clc
    rts
:
    lda actedit_piece_count
    cmp #PIECE_MAX
    bcc :+
    jmp apply_direct_split_insert_fallback
:
    sec
    sbc #$01
    sta actedit_direct_patch_shift_index
apply_direct_split_insert_shift_loop:
    lda actedit_direct_patch_shift_index
    cmp actedit_direct_insert_piece_index
    bcc apply_direct_split_insert_write
    clc
    adc #$01
    tay
    ldx actedit_direct_patch_shift_index
    jsr copy_piece_x_to_y
    dec actedit_direct_patch_shift_index
    jmp apply_direct_split_insert_shift_loop
apply_direct_split_insert_write:
    inc actedit_piece_count
    ldx actedit_direct_insert_piece_index
    lda #PIECE_KIND_INSERT
    sta piece_window_kind,x
    lda actedit_pending_insert_anchor_lo
    sta piece_window_ref_lo,x
    lda actedit_pending_insert_anchor_hi
    sta piece_window_ref_hi,x
    lda actedit_direct_insert_slot
    sta piece_window_aux,x
    lda #$01
    sta piece_window_count_lo,x
    lda #$00
    sta piece_window_count_hi,x
    jsr save_piece_table_window
    bcs apply_direct_split_insert_fallback
    lda #$00
    sta actedit_piece_dirty
    sta actedit_logical_line_index_ready
    sta actedit_direct_insert_ready
    lda #$01
    sta actedit_piece_loaded
    inc actedit_direct_insert_count
    inc requested_line_lo
    bne :+
    inc requested_line_hi
:
    jsr rebuild_logical_line_index_suffix
    clc
    rts
apply_direct_split_insert_fallback:
    jsr mark_piece_table_dirty
    lda #$00
    sta actedit_direct_insert_ready
    clc
    rts

prepare_direct_remove_line:
    lda #$00
    sta actedit_direct_remove_ready
    jsr direct_piece_cache_ready
    bcc :+
    clc
    rts
:
    jsr load_logical_line_index_entry
    bcc :+
    clc
    rts
:
    ldx actedit_piece_found_index
    lda piece_window_kind,x
    sta actedit_direct_patch_kind
    stx actedit_direct_patch_piece_index
    lda piece_window_ref_lo,x
    sta actedit_direct_patch_ref_lo
    lda piece_window_ref_hi,x
    sta actedit_direct_patch_ref_hi
    lda piece_window_count_lo,x
    sta actedit_direct_patch_piece_count_lo
    lda piece_window_count_hi,x
    sta actedit_direct_patch_piece_count_hi
    lda word_tmp
    sta actedit_direct_patch_offset_lo
    lda word_tmp+1
    sta actedit_direct_patch_offset_hi
    cmp actedit_direct_patch_piece_count_hi
    bcc prepare_direct_remove_in_range
    beq :+
    jmp prepare_direct_remove_done
:
    lda actedit_direct_patch_offset_lo
    cmp actedit_direct_patch_piece_count_lo
    bcc prepare_direct_remove_in_range
    jmp prepare_direct_remove_done
prepare_direct_remove_in_range:
    lda actedit_direct_remove_line_kind
    cmp #LINE_KIND_INSERT
    beq prepare_direct_remove_insert
    cmp #LINE_KIND_SOURCE
    beq :+
    jmp prepare_direct_remove_done
:
    lda actedit_direct_patch_kind
    cmp #PIECE_KIND_SOURCE
    beq prepare_direct_remove_source
    cmp #PIECE_KIND_PATCH
    bne prepare_direct_remove_done
    lda actedit_direct_patch_offset_lo
    ora actedit_direct_patch_offset_hi
    bne prepare_direct_remove_done
    lda actedit_direct_patch_piece_count_lo
    cmp #$01
    bne prepare_direct_remove_done
    lda actedit_direct_patch_piece_count_hi
    bne prepare_direct_remove_done
    lda actedit_direct_patch_ref_lo
    cmp actedit_direct_patch_source_lo
    bne prepare_direct_remove_done
    lda actedit_direct_patch_ref_hi
    cmp actedit_direct_patch_source_hi
    bne prepare_direct_remove_done
    jmp prepare_direct_remove_ready

prepare_direct_remove_source:
    clc
    lda actedit_direct_patch_ref_lo
    adc actedit_direct_patch_offset_lo
    sta word_tmp
    lda actedit_direct_patch_ref_hi
    adc actedit_direct_patch_offset_hi
    sta word_tmp+1
    lda word_tmp
    cmp actedit_direct_patch_source_lo
    bne prepare_direct_remove_done
    lda word_tmp+1
    cmp actedit_direct_patch_source_hi
    bne prepare_direct_remove_done
    jmp prepare_direct_remove_ready

prepare_direct_remove_insert:
    lda actedit_direct_patch_kind
    cmp #PIECE_KIND_INSERT
    bne prepare_direct_remove_done
    lda actedit_direct_patch_offset_lo
    ora actedit_direct_patch_offset_hi
    bne prepare_direct_remove_done
    lda actedit_direct_patch_piece_count_lo
    cmp #$01
    bne prepare_direct_remove_done
    lda actedit_direct_patch_piece_count_hi
    bne prepare_direct_remove_done
    ldx actedit_direct_patch_piece_index
    lda piece_window_aux,x
    cmp actedit_direct_insert_slot
    bne prepare_direct_remove_done
prepare_direct_remove_ready:
    lda #$01
    sta actedit_direct_remove_ready
prepare_direct_remove_done:
    clc
    rts

apply_direct_remove_line:
    lda actedit_direct_remove_ready
    bne :+
    clc
    rts
:
    lda actedit_direct_patch_kind
    cmp #PIECE_KIND_SOURCE
    beq apply_direct_remove_source
    cmp #PIECE_KIND_PATCH
    bne :+
    jmp apply_direct_remove_whole_piece
:
    cmp #PIECE_KIND_INSERT
    bne :+
    jmp apply_direct_remove_whole_piece
:
    jmp apply_direct_remove_fallback

apply_direct_remove_source:
    sec
    lda actedit_direct_patch_piece_count_lo
    sbc actedit_direct_patch_offset_lo
    sta actedit_direct_patch_after_lo
    lda actedit_direct_patch_piece_count_hi
    sbc actedit_direct_patch_offset_hi
    sta actedit_direct_patch_after_hi
    sec
    lda actedit_direct_patch_after_lo
    sbc #$01
    sta actedit_direct_patch_after_lo
    lda actedit_direct_patch_after_hi
    sbc #$00
    sta actedit_direct_patch_after_hi
    lda actedit_direct_patch_offset_lo
    ora actedit_direct_patch_offset_hi
    beq apply_direct_remove_source_at_start
    lda actedit_direct_patch_after_lo
    ora actedit_direct_patch_after_hi
    beq apply_direct_remove_source_at_end
    jmp apply_direct_remove_split_source

apply_direct_remove_source_at_start:
    lda actedit_direct_patch_after_lo
    ora actedit_direct_patch_after_hi
    bne :+
    jmp apply_direct_remove_whole_piece
:
    ldx actedit_direct_patch_piece_index
    lda #PIECE_KIND_SOURCE
    sta piece_window_kind,x
    clc
    lda actedit_direct_patch_source_lo
    adc #$01
    sta piece_window_ref_lo,x
    lda actedit_direct_patch_source_hi
    adc #$00
    sta piece_window_ref_hi,x
    lda #$00
    sta piece_window_aux,x
    lda actedit_direct_patch_after_lo
    sta piece_window_count_lo,x
    lda actedit_direct_patch_after_hi
    sta piece_window_count_hi,x
    jmp apply_direct_remove_persist

apply_direct_remove_source_at_end:
    ldx actedit_direct_patch_piece_index
    lda actedit_direct_patch_offset_lo
    sta piece_window_count_lo,x
    lda actedit_direct_patch_offset_hi
    sta piece_window_count_hi,x
    jmp apply_direct_remove_persist

apply_direct_remove_split_source:
    lda actedit_piece_count
    cmp #PIECE_MAX
    bcc :+
    jmp apply_direct_remove_fallback
:
    bne :+
    jmp apply_direct_remove_fallback
:
    sec
    sbc #$01
    sta actedit_direct_patch_shift_index
apply_direct_remove_split_shift_loop:
    lda actedit_direct_patch_shift_index
    cmp actedit_direct_patch_piece_index
    beq apply_direct_remove_split_write
    clc
    adc #$01
    tay
    ldx actedit_direct_patch_shift_index
    jsr copy_piece_x_to_y
    dec actedit_direct_patch_shift_index
    jmp apply_direct_remove_split_shift_loop
apply_direct_remove_split_write:
    inc actedit_piece_count
    ldx actedit_direct_patch_piece_index
    lda actedit_direct_patch_offset_lo
    sta piece_window_count_lo,x
    lda actedit_direct_patch_offset_hi
    sta piece_window_count_hi,x
    inx
    lda #PIECE_KIND_SOURCE
    sta piece_window_kind,x
    clc
    lda actedit_direct_patch_source_lo
    adc #$01
    sta piece_window_ref_lo,x
    lda actedit_direct_patch_source_hi
    adc #$00
    sta piece_window_ref_hi,x
    lda #$00
    sta piece_window_aux,x
    lda actedit_direct_patch_after_lo
    sta piece_window_count_lo,x
    lda actedit_direct_patch_after_hi
    sta piece_window_count_hi,x
    jmp apply_direct_remove_persist

apply_direct_remove_whole_piece:
    lda actedit_piece_count
    beq apply_direct_remove_fallback
    lda actedit_direct_patch_piece_index
    sta actedit_direct_patch_shift_index
apply_direct_remove_left_shift_loop:
    clc
    lda actedit_direct_patch_shift_index
    adc #$01
    cmp actedit_piece_count
    bcs apply_direct_remove_left_shift_done
    tax
    ldy actedit_direct_patch_shift_index
    jsr copy_piece_x_to_y
    inc actedit_direct_patch_shift_index
    jmp apply_direct_remove_left_shift_loop
apply_direct_remove_left_shift_done:
    dec actedit_piece_count
    ldx actedit_piece_count
    lda #$00
    sta piece_window_kind,x
    sta piece_window_ref_lo,x
    sta piece_window_ref_hi,x
    sta piece_window_aux,x
    sta piece_window_count_lo,x
    sta piece_window_count_hi,x

apply_direct_remove_persist:
    jsr save_piece_table_window
    bcs apply_direct_remove_fallback
    lda #$00
    sta actedit_piece_dirty
    sta actedit_logical_line_index_ready
    sta actedit_direct_remove_ready
    lda #$01
    sta actedit_piece_loaded
    inc actedit_direct_remove_count
    jsr rebuild_logical_line_index_suffix
    clc
    rts
apply_direct_remove_fallback:
    jsr mark_piece_table_dirty
    lda #$00
    sta actedit_direct_remove_ready
    clc
    rts

rebuild_logical_line_index_suffix:
    lda requested_line_lo
    ora requested_line_hi
    bne :+
    jmp rebuild_logical_line_index_suffix_fail
:
    sec
    lda requested_line_lo
    sbc #$01
    sta actedit_direct_patch_after_lo
    sta actedit_logical_line_count_lo
    sta actedit_logical_line_index_next_lo
    lda requested_line_hi
    sbc #$00
    sta actedit_direct_patch_after_hi
    sta actedit_logical_line_count_hi
    sta actedit_logical_line_index_next_hi
    lda #$00
    sta actedit_logical_line_index_next_bank
    sta actedit_logical_line_index_window_len
    sta actedit_logical_line_index_ready
    asl actedit_logical_line_index_next_lo
    rol actedit_logical_line_index_next_hi
    rol actedit_logical_line_index_next_bank
    clc
    lda actedit_logical_line_index_next_lo
    adc actedit_direct_patch_after_lo
    sta actedit_logical_line_index_next_lo
    lda actedit_logical_line_index_next_hi
    adc actedit_direct_patch_after_hi
    sta actedit_logical_line_index_next_hi
    lda actedit_logical_line_index_next_bank
    adc #$00
    sta actedit_logical_line_index_next_bank
    ldx #$00
rebuild_logical_line_index_suffix_find_piece:
    cpx actedit_piece_count
    bcc rebuild_logical_line_index_suffix_check_piece
    lda actedit_direct_patch_after_lo
    ora actedit_direct_patch_after_hi
    bne :+
    jmp rebuild_logical_line_index_suffix_finish
:
    jmp rebuild_logical_line_index_suffix_fail
rebuild_logical_line_index_suffix_check_piece:
    lda piece_window_count_lo,x
    ora piece_window_count_hi,x
    bne :+
    jmp rebuild_logical_line_index_suffix_fail
:
    lda actedit_direct_patch_after_hi
    cmp piece_window_count_hi,x
    bcc rebuild_logical_line_index_suffix_found
    bne rebuild_logical_line_index_suffix_advance
    lda actedit_direct_patch_after_lo
    cmp piece_window_count_lo,x
    bcc rebuild_logical_line_index_suffix_found
rebuild_logical_line_index_suffix_advance:
    sec
    lda actedit_direct_patch_after_lo
    sbc piece_window_count_lo,x
    sta actedit_direct_patch_after_lo
    lda actedit_direct_patch_after_hi
    sbc piece_window_count_hi,x
    sta actedit_direct_patch_after_hi
    inx
    jmp rebuild_logical_line_index_suffix_find_piece
rebuild_logical_line_index_suffix_found:
    stx actedit_piece_found_index
    lda actedit_direct_patch_after_lo
    sta scan_logical_line_lo
    lda actedit_direct_patch_after_hi
    sta scan_logical_line_hi
rebuild_logical_line_index_suffix_piece_loop:
    ldx actedit_piece_found_index
    cpx actedit_piece_count
    bcs rebuild_logical_line_index_suffix_finish
rebuild_logical_line_index_suffix_line_loop:
    ldx actedit_piece_found_index
    lda scan_logical_line_hi
    cmp piece_window_count_hi,x
    bcc rebuild_logical_line_index_suffix_append
    bne rebuild_logical_line_index_suffix_next_piece
    lda scan_logical_line_lo
    cmp piece_window_count_lo,x
    bcs rebuild_logical_line_index_suffix_next_piece
rebuild_logical_line_index_suffix_append:
    jsr append_logical_line_index_entry
    bcs rebuild_logical_line_index_suffix_fail
    inc scan_logical_line_lo
    bne rebuild_logical_line_index_suffix_line_loop
    inc scan_logical_line_hi
    jmp rebuild_logical_line_index_suffix_line_loop
rebuild_logical_line_index_suffix_next_piece:
    inc actedit_piece_found_index
    lda #$00
    sta scan_logical_line_lo
    sta scan_logical_line_hi
    jmp rebuild_logical_line_index_suffix_piece_loop
rebuild_logical_line_index_suffix_finish:
    jsr flush_logical_line_index_window
    bcs rebuild_logical_line_index_suffix_fail
    lda #$01
    sta actedit_logical_line_index_ready
    inc actedit_logical_index_suffix_count
    clc
    rts
rebuild_logical_line_index_suffix_fail:
    lda #$00
    sta actedit_logical_line_index_ready
    sec
    rts

actedit_overlay_end:

.assert actedit_overlay_end - actedit_overlay_header <= ACTEDIT_OVERLAY_EXEC_SIZE, error, "ACTEDIT mutation overlay exceeds execution window"
