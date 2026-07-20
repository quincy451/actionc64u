; Direct PRG builders used by the ALINK proof surface.
select_prg_build_strategy_or_fail:
    lda #PRG_BUILD_DIRECT
    sta prg_build_strategy
    jsr find_object_code_prg_case
    bcs select_prg_build_strategy_not_object_code
    rts
select_prg_build_strategy_not_object_code:
    jmp require_direct_prg_body_supported_or_fail

build_prg_content_or_fail:
    lda prg_build_strategy
    cmp #PRG_BUILD_OBJECT_CODE
    bne build_prg_content_not_object_code
    jmp build_object_code_prg_content_or_fail
build_prg_content_not_object_code:
    jmp build_direct_prg_fallback

build_direct_prg_content_or_fail:
    jmp build_direct_prg_fallback

require_direct_prg_body_supported_or_fail:
    jmp build_direct_prg_fallback

build_direct_prg_fallback:
    lda #<msg_unsupported_body
    ldy #>msg_unsupported_body
    jmp fail_with_ptr

find_object_code_prg_case:
    jsr direct_entry_body_is_object_code
    bcc find_object_code_prg_case_body_ok
    sec
    rts
find_object_code_prg_case_body_ok:
    jsr save_current_module_name
    lda #$00
    sta linked_object_index
find_object_code_prg_case_loop:
    ldx linked_object_index
    cpx external_count
    beq find_object_code_prg_case_supported
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_first_body_is_object_code
    bcs find_object_code_prg_case_unsupported
    inc linked_object_index
    jmp find_object_code_prg_case_loop
find_object_code_prg_case_supported:
    jsr restore_saved_module_name
    lda #PRG_BUILD_OBJECT_CODE
    sta prg_build_strategy
    clc
    rts
find_object_code_prg_case_unsupported:
    jsr restore_saved_module_name
    sec
    rts

loaded_external_print_body_is_M:
    jmp loaded_first_body_is_object_code

copy_loaded_first_import_to_module_name_or_fail:
    jsr reset_scan_ptr_after_header
copy_loaded_first_import_to_module_name_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq copy_loaded_first_import_to_module_name_bad
    lda #<line_external
    sta const_ptr
    lda #>line_external
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs copy_loaded_first_import_to_module_name_next
    jsr advance_scan_ptr_by_const_ptr
    jsr copy_import_symbol_line_to_pending_window_or_fail
    ldy #$00
copy_loaded_first_import_to_module_name_copy_loop:
    lda pending_name_window,y
    sta module_name,y
    beq copy_loaded_first_import_to_module_name_done
    iny
    cpy #25
    bcc copy_loaded_first_import_to_module_name_copy_loop
    jmp copy_loaded_first_import_to_module_name_bad
copy_loaded_first_import_to_module_name_next:
    jsr skip_current_line
    jmp copy_loaded_first_import_to_module_name_loop
copy_loaded_first_import_to_module_name_done:
    rts
copy_loaded_first_import_to_module_name_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr

build_object_code_prg_content_or_fail:
    lda #$00
    sta main_flags_lo
    sta main_flags_hi
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    jsr reload_root_object_or_fail
    jsr parse_exports_or_fail
    jsr find_export_index_from_module_name
    bcc build_object_code_prg_content_have_entry
    jmp build_object_code_prg_bad
build_object_code_prg_content_have_entry:
    stx entry_export_index
    stx root_entry_export_index
    jsr build_object_code_root_export_layout_or_fail
    jsr build_object_code_address_table_or_fail
    jsr reload_root_object_or_fail
    jsr parse_exports_or_fail
    ldx root_entry_export_index
    jmp build_object_code_have_root_export

validate_prg_build_inputs_or_fail:
    lda prg_build_strategy
    cmp #PRG_BUILD_OBJECT_CODE
    beq validate_object_code_prg_content_or_fail
    rts

validate_object_code_prg_content_or_fail:
    jsr reload_root_object_or_fail
    jsr parse_exports_or_fail
    jsr find_export_index_from_module_name
    bcc validate_object_code_prg_content_have_entry
    jmp build_object_code_prg_bad
validate_object_code_prg_content_have_entry:
    stx entry_export_index
    stx root_entry_export_index
    jsr build_object_code_root_export_layout_or_fail
    jsr build_object_code_address_table_or_fail
    jsr reload_root_object_or_fail
    jsr parse_exports_or_fail
    ldx root_entry_export_index
    jsr load_export_meta_window_from_x_or_fail
    jsr set_current_object_context_to_root_export_or_fail
    jsr validate_machine_code_record_current_object_or_fail
    jmp validate_object_code_external_modules_or_fail

validate_object_code_external_modules_or_fail:
    jsr save_current_module_name
    lda #$00
    sta linked_object_index
validate_object_code_external_modules_loop:
    ldx linked_object_index
    cpx external_count
    beq validate_object_code_external_modules_done
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr parse_exports_or_fail
    jsr find_export_index_from_module_name
    bcc validate_object_code_external_modules_have_export
    jmp build_object_code_prg_bad
validate_object_code_external_modules_have_export:
    jsr load_export_meta_window_from_x_or_fail
    ldx linked_object_index
    jsr set_current_object_context_from_pending_index_x_or_fail
    jsr validate_machine_code_record_current_object_or_fail
    inc linked_object_index
    jmp validate_object_code_external_modules_loop
validate_object_code_external_modules_done:
    jmp restore_saved_module_name

validate_machine_code_record_current_object_or_fail:
    jsr load_reloc_records_current_object_or_fail
    jsr find_machine_code_record_or_fail
    lda export_meta_window+EXPORT_META_SIZE_LO
    ora export_meta_window+EXPORT_META_SIZE_HI
    bne validate_machine_code_record_size_ok
    jmp build_object_code_prg_bad
validate_machine_code_record_size_ok:
    clc
    lda export_meta_window+EXPORT_META_OFFSET_LO
    adc export_meta_window+EXPORT_META_SIZE_LO
    sta current_bit_lo
    lda export_meta_window+EXPORT_META_OFFSET_HI
    adc export_meta_window+EXPORT_META_SIZE_HI
    sta current_bit_hi
    bcc validate_machine_code_record_range_ok
    jmp build_object_code_prg_bad
validate_machine_code_record_range_ok:
    jsr skip_machine_code_bytes_to_export_offset_or_fail
    lda #$00
    sta linked_store_value
    sta linked_store_value_hi
validate_machine_code_record_loop:
    lda linked_store_value_hi
    cmp export_meta_window+EXPORT_META_SIZE_HI
    bne validate_machine_code_record_read
    lda linked_store_value
    cmp export_meta_window+EXPORT_META_SIZE_LO
    beq validate_machine_code_record_done
validate_machine_code_record_read:
    jsr read_machine_code_byte_or_fail
    inc linked_store_value
    bne validate_machine_code_record_loop
    inc linked_store_value_hi
    jmp validate_machine_code_record_loop
validate_machine_code_record_done:
    rts

build_object_code_have_root_export:
    stx entry_export_index
    stx root_entry_export_index
    jsr load_export_meta_window_from_x_or_fail
    jsr set_current_object_context_to_root_export_or_fail
    jsr append_machine_code_record_current_object_or_fail
    jmp append_object_code_external_modules_or_fail

build_object_code_address_table_or_fail:
    ldx entry_export_index
    jsr load_export_meta_window_from_x_or_fail
    clc
    lda export_meta_window+EXPORT_META_SIZE_LO
    adc #$00
    sta linked_next_addr_lo
    lda export_meta_window+EXPORT_META_SIZE_HI
    adc #$10
    sta linked_next_addr_hi
build_object_code_address_table_with_current_next_or_fail:
    jsr save_current_module_name
    lda #$00
    sta linked_object_index
build_object_code_address_table_loop:
    ldx linked_object_index
    cpx external_count
    beq build_object_code_address_table_done
    lda linked_next_addr_lo
    sta pending_meta_window+PENDING_META_OFFSET_LO
    lda linked_next_addr_hi
    sta pending_meta_window+PENDING_META_OFFSET_HI
    ldx linked_object_index
    jsr store_pending_meta_window_from_x_or_fail
    ldx linked_object_index
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr parse_exports_or_fail
    jsr find_export_index_from_module_name
    bcc build_object_code_address_table_have_export
    jmp build_object_code_prg_bad
build_object_code_address_table_have_export:
    jsr load_export_meta_window_from_x_or_fail
    clc
    lda linked_next_addr_lo
    adc export_meta_window+EXPORT_META_SIZE_LO
    sta linked_next_addr_lo
    lda linked_next_addr_hi
    adc export_meta_window+EXPORT_META_SIZE_HI
    sta linked_next_addr_hi
    bcc build_object_code_address_table_size_ok
    jmp build_object_code_prg_bad
build_object_code_address_table_size_ok:
    inc linked_object_index
    jmp build_object_code_address_table_loop
build_object_code_address_table_done:
    jsr restore_saved_module_name
    rts

build_object_code_root_export_layout_or_fail:
    lda export_count
    sta saved_export_count
    ldx entry_export_index
    jsr load_export_meta_window_from_x_or_fail
    lda export_meta_window+EXPORT_META_OFFSET_LO
    sta linked_store_value
    lda export_meta_window+EXPORT_META_OFFSET_HI
    sta linked_store_value_hi
    clc
    lda linked_store_value
    adc export_meta_window+EXPORT_META_SIZE_LO
    sta linked_next_addr_lo
    lda linked_store_value_hi
    adc export_meta_window+EXPORT_META_SIZE_HI
    sta linked_next_addr_hi
    bcc build_object_code_root_export_layout_range_ok
    jmp build_object_code_prg_bad
build_object_code_root_export_layout_range_ok:
    lda #$00
    sta linked_object_index
build_object_code_root_export_layout_loop:
    ldx linked_object_index
    cpx saved_export_count
    beq build_object_code_root_export_layout_done
    jsr load_export_name_window_from_x_or_fail
    ldx linked_object_index
    jsr store_root_export_name_window_from_x_or_fail
    ldx linked_object_index
    jsr load_export_meta_window_from_x_or_fail
    lda #$00
    sta export_layout_window+EXPORT_LAYOUT_LO
    sta export_layout_window+EXPORT_LAYOUT_HI
    lda export_meta_window+EXPORT_META_OFFSET_HI
    cmp linked_store_value_hi
    bcc build_object_code_root_export_layout_store
    bne build_object_code_root_export_layout_after_start
    lda export_meta_window+EXPORT_META_OFFSET_LO
    cmp linked_store_value
    bcc build_object_code_root_export_layout_store
build_object_code_root_export_layout_after_start:
    lda export_meta_window+EXPORT_META_OFFSET_HI
    cmp linked_next_addr_hi
    bcc build_object_code_root_export_layout_in_range
    bne build_object_code_root_export_layout_store
    lda export_meta_window+EXPORT_META_OFFSET_LO
    cmp linked_next_addr_lo
    bcs build_object_code_root_export_layout_store
build_object_code_root_export_layout_in_range:
    sec
    lda export_meta_window+EXPORT_META_OFFSET_LO
    sbc linked_store_value
    sta export_layout_window+EXPORT_LAYOUT_LO
    lda export_meta_window+EXPORT_META_OFFSET_HI
    sbc linked_store_value_hi
    sta export_layout_window+EXPORT_LAYOUT_HI
    clc
    lda export_layout_window+EXPORT_LAYOUT_LO
    adc #$00
    sta export_layout_window+EXPORT_LAYOUT_LO
    lda export_layout_window+EXPORT_LAYOUT_HI
    adc #$10
    sta export_layout_window+EXPORT_LAYOUT_HI
    bcc build_object_code_root_export_layout_store
    jmp build_object_code_prg_bad
build_object_code_root_export_layout_store:
    ldx linked_object_index
    jsr store_root_export_layout_window_from_x_or_fail
    inc linked_object_index
    jmp build_object_code_root_export_layout_loop
build_object_code_root_export_layout_done:
    rts

append_object_code_external_modules_or_fail:
    jsr save_current_module_name
    lda #$00
    sta linked_object_index
append_object_code_external_modules_loop:
    ldx linked_object_index
    cpx external_count
    beq append_object_code_external_modules_done
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr parse_exports_or_fail
    jsr find_export_index_from_module_name
    bcc append_object_code_external_modules_have_export
    jmp build_object_code_prg_bad
append_object_code_external_modules_have_export:
    jsr load_export_meta_window_from_x_or_fail
    ldx linked_object_index
    jsr set_current_object_context_from_pending_index_x_or_fail
    jsr append_machine_code_record_current_object_or_fail
    inc linked_object_index
    jmp append_object_code_external_modules_loop
append_object_code_external_modules_done:
    jsr restore_saved_module_name
    rts

reload_root_object_or_fail:
    jsr build_object_target_path
    jmp load_object_or_fail

append_machine_code_record_current_object_or_fail:
    jsr load_reloc_records_current_object_or_fail
    jsr prepare_linked_reloc_cursor_or_fail
    jsr find_machine_code_record_or_fail
    lda export_meta_window+EXPORT_META_SIZE_LO
    ora export_meta_window+EXPORT_META_SIZE_HI
    beq build_object_code_prg_bad
    clc
    lda export_meta_window+EXPORT_META_OFFSET_LO
    adc export_meta_window+EXPORT_META_SIZE_LO
    sta current_bit_lo
    lda export_meta_window+EXPORT_META_OFFSET_HI
    adc export_meta_window+EXPORT_META_SIZE_HI
    sta current_bit_hi
    bcc build_object_code_prg_range_ok
    jmp build_object_code_prg_bad
build_object_code_prg_range_ok:
    jsr skip_machine_code_bytes_to_export_offset_or_fail
    lda #$00
    sta linked_store_value
    sta linked_store_value_hi
build_object_code_prg_loop:
    lda linked_store_value_hi
    cmp export_meta_window+EXPORT_META_SIZE_HI
    bne build_object_code_prg_read
    lda linked_store_value
    cmp export_meta_window+EXPORT_META_SIZE_LO
    beq build_object_code_prg_done
build_object_code_prg_read:
    jsr read_machine_code_byte_or_fail
    sta linked_machine_byte
    jsr find_reloc_patch_byte_for_current_offset
    bcs build_object_code_prg_unpatched_byte
    jmp build_object_code_prg_append_byte
build_object_code_prg_unpatched_byte:
    lda linked_machine_byte
build_object_code_prg_append_byte:
    jsr append_payload_byte
    inc linked_store_value
    bne build_object_code_prg_loop
    inc linked_store_value_hi
    jmp build_object_code_prg_loop
build_object_code_prg_done:
    jmp finish_linked_reloc_cursor_or_fail
build_object_code_prg_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr

skip_machine_code_bytes_to_export_offset_or_fail:
    lda export_meta_window+EXPORT_META_OFFSET_LO
    sta current_bit_lo
    lda export_meta_window+EXPORT_META_OFFSET_HI
    sta current_bit_hi
skip_machine_code_bytes_to_export_offset_loop:
    lda current_bit_lo
    ora current_bit_hi
    beq skip_machine_code_bytes_to_export_offset_done
    jsr read_machine_code_byte_or_fail
    lda current_bit_lo
    bne skip_machine_code_bytes_to_export_offset_dec_lo
    dec current_bit_hi
skip_machine_code_bytes_to_export_offset_dec_lo:
    dec current_bit_lo
    jmp skip_machine_code_bytes_to_export_offset_loop
skip_machine_code_bytes_to_export_offset_done:
    rts

read_machine_code_byte_or_fail:
    ldy #$00
    lda (scan_ptr),y
    beq read_machine_code_byte_bad
    cmp #10
    beq read_machine_code_byte_next_record
    cmp #13
    beq read_machine_code_byte_next_record
    cmp #' '
    bne read_machine_code_byte_hex_hi
    jsr advance_scan_ptr
    jmp read_machine_code_byte_or_fail
read_machine_code_byte_hex_hi:
    jsr parse_hex_nibble_from_a_or_fail
    asl a
    asl a
    asl a
    asl a
    sta parse_word_temp_lo
    jsr advance_scan_ptr
    ldy #$00
    lda (scan_ptr),y
    jsr parse_hex_nibble_from_a_or_fail
    ora parse_word_temp_lo
    sta parse_word_temp_hi
    jsr advance_scan_ptr
    lda parse_word_temp_hi
    rts
read_machine_code_byte_next_record:
    jsr skip_line_breaks
    lda #<line_machine_code
    sta const_ptr
    lda #>line_machine_code
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs read_machine_code_byte_bad
    jsr advance_scan_ptr_by_const_ptr
    jmp read_machine_code_byte_or_fail
read_machine_code_byte_bad:
    jmp build_object_code_prg_bad

find_machine_code_record_or_fail:
    jsr reset_scan_ptr_after_header
find_machine_code_record_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq find_machine_code_record_bad
    lda #<line_machine_code
    sta const_ptr
    lda #>line_machine_code
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcc find_machine_code_record_found
    jsr skip_current_line
    jmp find_machine_code_record_loop
find_machine_code_record_found:
    jmp advance_scan_ptr_by_const_ptr
find_machine_code_record_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr

load_reloc_records_current_object_or_fail:
    lda #$00
    sta linked_reloc_count
    jsr reset_scan_ptr_after_header
load_reloc_records_current_object_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    bne load_reloc_records_current_object_not_done
    jmp load_reloc_records_current_object_done
load_reloc_records_current_object_not_done:
    lda #<line_reloc
    sta const_ptr
    lda #>line_reloc
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcc load_reloc_records_current_object_found
    jsr skip_current_line
    jmp load_reloc_records_current_object_loop
load_reloc_records_current_object_found:
    jsr advance_scan_ptr_by_const_ptr
    jsr parse_decimal_word_or_fail
    lda current_bit_lo
    sta saved_state_lo
    lda current_bit_hi
    sta saved_state_hi
    jsr require_space_or_fail
    jsr parse_object_code_reloc_kind_or_fail
    jsr reloc_offset_is_in_current_export
    bcc :+
    jmp load_reloc_records_current_object_next
:
    ldy #$00
    lda (scan_ptr),y
    cmp #'u'
    beq load_reloc_records_current_object_import
    cmp #'x'
    beq load_reloc_records_current_object_symbol
    jmp load_reloc_records_current_object_bad
load_reloc_records_current_object_import:
    jsr advance_scan_ptr
    jsr parse_object_code_import_index_at_scan_ptr_or_fail
    sta linked_import_index
    jsr save_linked_reloc_scan_position
    lda linked_import_index
    jsr copy_loaded_import_index_to_pending_window_or_fail
    jsr resolve_pending_name_target_meta_or_fail
    jsr restore_linked_reloc_scan_position_or_fail
    jmp load_reloc_records_current_object_store
load_reloc_records_current_object_symbol:
    jsr advance_scan_ptr
    jsr require_space_or_fail
    jsr copy_object_code_reloc_symbol_to_pending_window_or_fail
    jsr save_linked_reloc_scan_position
    jsr resolve_pending_name_target_meta_or_fail
    jsr restore_linked_reloc_scan_position_or_fail
load_reloc_records_current_object_store:
    jsr parse_optional_reloc_addend_or_fail
    jsr apply_reloc_addend_to_pending_meta_or_fail
    ldx linked_reloc_count
    cpx #RELOC_MAX
    bcs load_reloc_records_current_object_bad
    jsr validate_new_linked_reloc_span_or_fail
    lda saved_state_lo
    sta reloc_record_window+RELOC_RECORD_OFFSET_LO
    lda saved_state_hi
    sta reloc_record_window+RELOC_RECORD_OFFSET_HI
    lda pending_meta_window+PENDING_META_OFFSET_LO
    sta reloc_record_window+RELOC_RECORD_ADDR_LO
    lda pending_meta_window+PENDING_META_OFFSET_HI
    sta reloc_record_window+RELOC_RECORD_ADDR_HI
    lda linked_reloc_kind
    sta reloc_record_window+RELOC_RECORD_KIND
    ldx linked_reloc_count
    jsr store_linked_reloc_record_window_from_x_or_fail
    inc linked_reloc_count
    ldy #$00
    lda (scan_ptr),y
    beq load_reloc_records_current_object_next
    cmp #10
    beq load_reloc_records_current_object_next
    cmp #13
    beq load_reloc_records_current_object_next
load_reloc_records_current_object_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
load_reloc_records_current_object_next:
    jsr skip_current_line
    jmp load_reloc_records_current_object_loop
load_reloc_records_current_object_done:
    rts

append_named_relocs_current_export_to_queue_or_fail:
    jsr reset_scan_ptr_after_header
append_named_relocs_current_export_to_queue_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    bne append_named_relocs_current_export_to_queue_not_done
    rts
append_named_relocs_current_export_to_queue_not_done:
    lda #<line_reloc
    sta const_ptr
    lda #>line_reloc
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcc append_named_relocs_current_export_to_queue_found
    jsr skip_current_line
    jmp append_named_relocs_current_export_to_queue_loop
append_named_relocs_current_export_to_queue_found:
    jsr advance_scan_ptr_by_const_ptr
    jsr parse_decimal_word_or_fail
    lda current_bit_lo
    sta saved_state_lo
    lda current_bit_hi
    sta saved_state_hi
    jsr require_space_or_fail
    jsr parse_object_code_reloc_kind_or_fail
    jsr reloc_offset_is_in_current_export
    bcs append_named_relocs_current_export_to_queue_next
    ldy #$00
    lda (scan_ptr),y
    cmp #'u'
    beq append_named_relocs_current_export_to_queue_next
    cmp #'x'
    bne append_named_relocs_current_export_to_queue_bad
    jsr advance_scan_ptr
    jsr require_space_or_fail
    jsr copy_object_code_reloc_symbol_to_pending_window_or_fail
    jsr save_linked_reloc_scan_position
    jsr pending_name_already_loaded_exported
    bcc append_named_relocs_current_export_to_queue_local
    jsr append_pending_name_to_external_queue_or_fail
append_named_relocs_current_export_to_queue_local:
    jsr restore_linked_reloc_scan_position_or_fail
    jsr parse_optional_reloc_addend_or_fail
    ldy #$00
    lda (scan_ptr),y
    beq append_named_relocs_current_export_to_queue_next
    cmp #10
    beq append_named_relocs_current_export_to_queue_next
    cmp #13
    beq append_named_relocs_current_export_to_queue_next
append_named_relocs_current_export_to_queue_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
append_named_relocs_current_export_to_queue_next:
    jsr skip_current_line
    jmp append_named_relocs_current_export_to_queue_loop

parse_object_code_reloc_kind_or_fail:
    lda #RELOC_KIND_WORD
    sta linked_reloc_kind
    ldy #$00
    lda (scan_ptr),y
    jsr lowercase_ascii
    cmp #'l'
    beq parse_object_code_reloc_kind_low
    cmp #'h'
    beq parse_object_code_reloc_kind_high
    rts
parse_object_code_reloc_kind_low:
    lda #RELOC_KIND_LOW
    sta linked_reloc_kind
    jsr advance_scan_ptr
    ldy #$00
    lda (scan_ptr),y
    jsr lowercase_ascii
    cmp #'o'
    bne parse_object_code_reloc_kind_space
    jsr advance_scan_ptr
    jmp require_space_or_fail
parse_object_code_reloc_kind_high:
    lda #RELOC_KIND_HIGH
    sta linked_reloc_kind
    jsr advance_scan_ptr
    ldy #$00
    lda (scan_ptr),y
    jsr lowercase_ascii
    cmp #'i'
    bne parse_object_code_reloc_kind_space
    jsr advance_scan_ptr
    jmp require_space_or_fail
parse_object_code_reloc_kind_space:
    jmp require_space_or_fail

parse_optional_reloc_addend_or_fail:
    lda #$00
    sta linked_reloc_addend_lo
    sta linked_reloc_addend_hi
    sta linked_reloc_addend_negative
    ldy #$00
    lda (scan_ptr),y
    beq parse_optional_reloc_addend_done
    cmp #10
    beq parse_optional_reloc_addend_done
    cmp #13
    beq parse_optional_reloc_addend_done
    cmp #' '
    bne parse_optional_reloc_addend_bad
    jsr advance_scan_ptr
    ldy #$00
    lda (scan_ptr),y
    cmp #'-'
    beq parse_optional_reloc_addend_negative
    cmp #'+'
    bne parse_optional_reloc_addend_value
    jsr advance_scan_ptr
    jmp parse_optional_reloc_addend_value
parse_optional_reloc_addend_negative:
    lda #$01
    sta linked_reloc_addend_negative
    jsr advance_scan_ptr
parse_optional_reloc_addend_value:
    jsr parse_decimal_word_or_fail
    lda current_bit_lo
    sta linked_reloc_addend_lo
    lda current_bit_hi
    sta linked_reloc_addend_hi
parse_optional_reloc_addend_done:
    rts
parse_optional_reloc_addend_bad:
    jmp build_object_code_prg_bad

apply_reloc_addend_to_pending_meta_or_fail:
    lda linked_reloc_addend_lo
    ora linked_reloc_addend_hi
    beq apply_reloc_addend_to_pending_meta_done
    lda linked_reloc_addend_negative
    bne apply_reloc_addend_to_pending_meta_negative
    clc
    lda pending_meta_window+PENDING_META_OFFSET_LO
    adc linked_reloc_addend_lo
    sta pending_meta_window+PENDING_META_OFFSET_LO
    lda pending_meta_window+PENDING_META_OFFSET_HI
    adc linked_reloc_addend_hi
    bcs apply_reloc_addend_to_pending_meta_bad
    sta pending_meta_window+PENDING_META_OFFSET_HI
apply_reloc_addend_to_pending_meta_done:
    rts
apply_reloc_addend_to_pending_meta_negative:
    sec
    lda pending_meta_window+PENDING_META_OFFSET_LO
    sbc linked_reloc_addend_lo
    sta pending_meta_window+PENDING_META_OFFSET_LO
    lda pending_meta_window+PENDING_META_OFFSET_HI
    sbc linked_reloc_addend_hi
    bcc apply_reloc_addend_to_pending_meta_bad
    sta pending_meta_window+PENDING_META_OFFSET_HI
    rts
apply_reloc_addend_to_pending_meta_bad:
    jmp build_object_code_prg_bad

validate_new_linked_reloc_span_or_fail:
    ldx #$00
validate_new_linked_reloc_span_loop:
    cpx linked_reloc_count
    beq validate_new_linked_reloc_span_ok
    jsr load_linked_reloc_record_window_from_x_or_fail
    lda reloc_record_window+RELOC_RECORD_OFFSET_HI
    cmp saved_state_hi
    bne validate_new_linked_reloc_span_check_old_word
    lda reloc_record_window+RELOC_RECORD_OFFSET_LO
    cmp saved_state_lo
    beq validate_new_linked_reloc_span_bad
validate_new_linked_reloc_span_check_old_word:
    lda reloc_record_window+RELOC_RECORD_KIND
    bne validate_new_linked_reloc_span_check_new_word
    clc
    lda reloc_record_window+RELOC_RECORD_OFFSET_LO
    adc #$01
    sta current_bit_lo
    lda reloc_record_window+RELOC_RECORD_OFFSET_HI
    adc #$00
    sta current_bit_hi
    lda current_bit_hi
    cmp saved_state_hi
    bne validate_new_linked_reloc_span_check_new_word
    lda current_bit_lo
    cmp saved_state_lo
    beq validate_new_linked_reloc_span_bad
validate_new_linked_reloc_span_check_new_word:
    lda linked_reloc_kind
    bne validate_new_linked_reloc_span_next
    clc
    lda saved_state_lo
    adc #$01
    sta current_bit_lo
    lda saved_state_hi
    adc #$00
    sta current_bit_hi
    lda current_bit_hi
    cmp reloc_record_window+RELOC_RECORD_OFFSET_HI
    bne validate_new_linked_reloc_span_next
    lda current_bit_lo
    cmp reloc_record_window+RELOC_RECORD_OFFSET_LO
    beq validate_new_linked_reloc_span_bad
validate_new_linked_reloc_span_next:
    inx
    jmp validate_new_linked_reloc_span_loop
validate_new_linked_reloc_span_bad:
    jmp build_object_code_prg_bad
validate_new_linked_reloc_span_ok:
    rts

copy_object_code_reloc_symbol_to_pending_window_or_fail:
    lda #<pending_name_window
    sta export_ptr
    lda #>pending_name_window
    sta export_ptr+1
    lda #$00
    sta linked_external_index
copy_object_code_reloc_symbol_to_pending_window_loop:
    ldy #$00
    lda (scan_ptr),y
    beq copy_object_code_reloc_symbol_to_pending_window_done
    cmp #' '
    beq copy_object_code_reloc_symbol_to_pending_window_done
    cmp #10
    beq copy_object_code_reloc_symbol_to_pending_window_done
    cmp #13
    beq copy_object_code_reloc_symbol_to_pending_window_done
    jsr lowercase_ascii
    cmp #'a'
    bcc copy_object_code_reloc_symbol_to_pending_window_symbol
    cmp #'z'+1
    bcc copy_object_code_reloc_symbol_to_pending_window_store
copy_object_code_reloc_symbol_to_pending_window_symbol:
    cmp #'0'
    bcc copy_object_code_reloc_symbol_to_pending_window_check_underscore
    cmp #'9'+1
    bcc copy_object_code_reloc_symbol_to_pending_window_store
copy_object_code_reloc_symbol_to_pending_window_check_underscore:
    cmp #'_'
    bne copy_object_code_reloc_symbol_to_pending_window_bad
copy_object_code_reloc_symbol_to_pending_window_store:
    ldy #$00
    sta (export_ptr),y
    jsr advance_scan_ptr
    inc export_ptr
    bne :+
    inc export_ptr+1
:   inc linked_external_index
    lda linked_external_index
    cmp #24
    bcc copy_object_code_reloc_symbol_to_pending_window_loop
copy_object_code_reloc_symbol_to_pending_window_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
copy_object_code_reloc_symbol_to_pending_window_done:
    lda linked_external_index
    beq copy_object_code_reloc_symbol_to_pending_window_bad
    lda #$00
    ldy #$00
    sta (export_ptr),y
    rts

save_linked_reloc_scan_position:
.if ACTC_REU_SOURCE_CACHE
    lda #$01
    sta linked_reloc_saved_scan_abs
    sec
    lda source_window_next_offset
    sbc source_window_len
    sta linked_reloc_saved_scan_lo
    lda source_window_next_offset+1
    sbc source_window_len+1
    sta linked_reloc_saved_scan_hi
    lda source_window_next_offset+2
    sbc #$00
    sta linked_reloc_saved_scan_bank
    sec
    lda scan_ptr
    sbc #<source_buffer
    sta parse_word_temp_lo
    lda scan_ptr+1
    sbc #>source_buffer
    sta parse_word_temp_hi
    clc
    lda linked_reloc_saved_scan_lo
    adc parse_word_temp_lo
    sta linked_reloc_saved_scan_lo
    lda linked_reloc_saved_scan_hi
    adc parse_word_temp_hi
    sta linked_reloc_saved_scan_hi
    lda linked_reloc_saved_scan_bank
    adc #$00
    sta linked_reloc_saved_scan_bank
    rts
.else
    lda scan_ptr
    sta linked_reloc_saved_scan_lo
    lda scan_ptr+1
    sta linked_reloc_saved_scan_hi
    rts
.endif

restore_linked_reloc_scan_position_or_fail:
.if ACTC_REU_SOURCE_CACHE
    lda linked_reloc_saved_scan_abs
    bne restore_linked_reloc_scan_position_abs
    lda linked_reloc_saved_scan_lo
    sta scan_ptr
    lda linked_reloc_saved_scan_hi
    sta scan_ptr+1
    rts
restore_linked_reloc_scan_position_abs:
.ifdef ALINK_PRESERVE_ZP_SERVICES
    lda alink_source_direct_cached
    beq restore_linked_reloc_scan_position_reu
    lda linked_reloc_saved_scan_bank
    beq restore_linked_reloc_scan_position_direct_bank_ok
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
restore_linked_reloc_scan_position_direct_bank_ok:
    clc
    lda #<source_buffer
    adc linked_reloc_saved_scan_lo
    sta scan_ptr
    lda #>source_buffer
    adc linked_reloc_saved_scan_hi
    sta scan_ptr+1
    rts
restore_linked_reloc_scan_position_reu:
.endif
    lda linked_reloc_saved_scan_lo
    sta source_window_next_offset
    lda linked_reloc_saved_scan_hi
    sta source_window_next_offset+1
    lda linked_reloc_saved_scan_bank
    sta source_window_next_offset+2
    jsr source_reader_load_next_window
    bcc restore_linked_reloc_scan_position_ok
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
restore_linked_reloc_scan_position_ok:
    rts
.else
    lda linked_reloc_saved_scan_lo
    sta scan_ptr
    lda linked_reloc_saved_scan_hi
    sta scan_ptr+1
    rts
.endif

reloc_offset_is_in_current_export:
    lda saved_state_hi
    cmp export_meta_window+EXPORT_META_OFFSET_HI
    bcc reloc_offset_is_in_current_export_no
    bne reloc_offset_is_in_current_export_after_start
    lda saved_state_lo
    cmp export_meta_window+EXPORT_META_OFFSET_LO
    bcc reloc_offset_is_in_current_export_no
reloc_offset_is_in_current_export_after_start:
    clc
    lda export_meta_window+EXPORT_META_OFFSET_LO
    adc export_meta_window+EXPORT_META_SIZE_LO
    sta parse_word_temp_hi
    lda export_meta_window+EXPORT_META_OFFSET_HI
    adc export_meta_window+EXPORT_META_SIZE_HI
    sta parse_word_temp_lo
    bcs reloc_offset_is_in_current_export_no
    lda saved_state_lo
    sta current_bit_lo
    lda saved_state_hi
    sta current_bit_hi
    lda linked_reloc_kind
    bne reloc_offset_is_in_current_export_compare_end
    clc
    lda current_bit_lo
    adc #$01
    sta current_bit_lo
    lda current_bit_hi
    adc #$00
    sta current_bit_hi
    bcs reloc_offset_is_in_current_export_no
reloc_offset_is_in_current_export_compare_end:
    lda current_bit_hi
    cmp parse_word_temp_lo
    bcc reloc_offset_is_in_current_export_yes
    bne reloc_offset_is_in_current_export_no
    lda current_bit_lo
    cmp parse_word_temp_hi
    bcs reloc_offset_is_in_current_export_no
reloc_offset_is_in_current_export_yes:
    clc
    rts
reloc_offset_is_in_current_export_no:
    sec
    rts

prepare_linked_reloc_cursor_or_fail:
    lda #$00
    sta linked_reloc_cursor_consumed
    sta linked_reloc_cursor_valid
    sta linked_reloc_cursor_advance
    sta linked_reloc_previous_lo
    sta linked_reloc_previous_hi
    sta linked_reloc_previous_kind
    jmp select_next_linked_reloc_or_fail

finish_linked_reloc_cursor_or_fail:
    lda linked_reloc_cursor_advance
    beq finish_linked_reloc_cursor_compare
    lda #$00
    sta linked_reloc_cursor_advance
    inc linked_reloc_cursor_consumed
finish_linked_reloc_cursor_compare:
    lda linked_reloc_cursor_consumed
    cmp linked_reloc_count
    beq finish_linked_reloc_cursor_ok
    jmp build_object_code_prg_bad
finish_linked_reloc_cursor_ok:
    rts

select_next_linked_reloc_or_fail:
    lda #$00
    sta linked_reloc_cursor_valid
    lda linked_reloc_cursor_consumed
    beq select_next_linked_reloc_zero_threshold
    cmp linked_reloc_count
    bne :+
    jmp select_next_linked_reloc_done
:
    clc
    lda linked_reloc_previous_lo
    adc #$01
    sta current_bit_lo
    lda linked_reloc_previous_hi
    adc #$00
    sta current_bit_hi
    bcs select_next_linked_reloc_threshold_bad
    lda linked_reloc_previous_kind
    beq select_next_linked_reloc_word_threshold
    jmp select_next_linked_reloc_scan
select_next_linked_reloc_word_threshold:
    clc
    lda current_bit_lo
    adc #$01
    sta current_bit_lo
    lda current_bit_hi
    adc #$00
    sta current_bit_hi
    bcs select_next_linked_reloc_threshold_bad
    jmp select_next_linked_reloc_scan
select_next_linked_reloc_threshold_bad:
    jmp build_object_code_prg_bad
select_next_linked_reloc_zero_threshold:
    sta current_bit_lo
    sta current_bit_hi
select_next_linked_reloc_scan:
    ldx #$00
select_next_linked_reloc_loop:
    cpx linked_reloc_count
    beq select_next_linked_reloc_done
    jsr load_linked_reloc_record_window_from_x_or_fail
    lda reloc_record_window+RELOC_RECORD_OFFSET_HI
    cmp current_bit_hi
    bcc select_next_linked_reloc_next
    bne select_next_linked_reloc_candidate
    lda reloc_record_window+RELOC_RECORD_OFFSET_LO
    cmp current_bit_lo
    bcc select_next_linked_reloc_next
select_next_linked_reloc_candidate:
    lda linked_reloc_cursor_valid
    beq select_next_linked_reloc_store
    lda reloc_record_window+RELOC_RECORD_OFFSET_HI
    cmp linked_reloc_cursor_window+RELOC_RECORD_OFFSET_HI
    bcc select_next_linked_reloc_store
    bne select_next_linked_reloc_next
    lda reloc_record_window+RELOC_RECORD_OFFSET_LO
    cmp linked_reloc_cursor_window+RELOC_RECORD_OFFSET_LO
    bcs select_next_linked_reloc_next
select_next_linked_reloc_store:
    ldy #$00
select_next_linked_reloc_copy_loop:
    lda reloc_record_window,y
    sta linked_reloc_cursor_window,y
    iny
    cpy #RELOC_RECORD_BYTES
    bcc select_next_linked_reloc_copy_loop
    lda #$01
    sta linked_reloc_cursor_valid
select_next_linked_reloc_next:
    inx
    jmp select_next_linked_reloc_loop
select_next_linked_reloc_done:
    lda linked_reloc_cursor_valid
    bne select_next_linked_reloc_ok
    lda linked_reloc_cursor_consumed
    cmp linked_reloc_count
    beq select_next_linked_reloc_ok
    jmp build_object_code_prg_bad
select_next_linked_reloc_ok:
    rts

find_reloc_patch_byte_for_current_offset:
    lda linked_reloc_cursor_advance
    beq find_reloc_patch_byte_for_current_offset_ready
    lda #$00
    sta linked_reloc_cursor_advance
    lda linked_reloc_cursor_window+RELOC_RECORD_OFFSET_LO
    sta linked_reloc_previous_lo
    lda linked_reloc_cursor_window+RELOC_RECORD_OFFSET_HI
    sta linked_reloc_previous_hi
    lda linked_reloc_cursor_window+RELOC_RECORD_KIND
    sta linked_reloc_previous_kind
    inc linked_reloc_cursor_consumed
    jsr select_next_linked_reloc_or_fail
find_reloc_patch_byte_for_current_offset_ready:
    clc
    lda export_meta_window+EXPORT_META_OFFSET_LO
    adc linked_store_value
    sta current_bit_lo
    lda export_meta_window+EXPORT_META_OFFSET_HI
    adc linked_store_value_hi
    sta current_bit_hi
    bcs find_reloc_patch_byte_for_current_offset_not_found
    lda linked_reloc_cursor_valid
    beq find_reloc_patch_byte_for_current_offset_not_found
    lda current_bit_lo
    cmp linked_reloc_cursor_window+RELOC_RECORD_OFFSET_LO
    bne find_reloc_patch_byte_for_current_offset_check_hi
    lda current_bit_hi
    cmp linked_reloc_cursor_window+RELOC_RECORD_OFFSET_HI
    beq find_reloc_patch_byte_for_current_offset_at_start
find_reloc_patch_byte_for_current_offset_check_hi:
    lda linked_reloc_cursor_window+RELOC_RECORD_KIND
    bne find_reloc_patch_byte_for_current_offset_not_found
    clc
    lda linked_reloc_cursor_window+RELOC_RECORD_OFFSET_LO
    adc #$01
    sta parse_word_temp_lo
    lda linked_reloc_cursor_window+RELOC_RECORD_OFFSET_HI
    adc #$00
    sta parse_word_temp_hi
    bcs find_reloc_patch_byte_for_current_offset_not_found
    lda current_bit_lo
    cmp parse_word_temp_lo
    bne find_reloc_patch_byte_for_current_offset_not_found
    lda current_bit_hi
    cmp parse_word_temp_hi
    beq find_reloc_patch_byte_for_current_offset_hi
    bne find_reloc_patch_byte_for_current_offset_not_found
find_reloc_patch_byte_for_current_offset_at_start:
    lda linked_reloc_cursor_window+RELOC_RECORD_KIND
    beq find_reloc_patch_byte_for_current_offset_lo
    cmp #RELOC_KIND_LOW
    beq find_reloc_patch_byte_for_current_offset_byte_lo
    cmp #RELOC_KIND_HIGH
    beq find_reloc_patch_byte_for_current_offset_byte_hi
    jmp build_object_code_prg_bad
find_reloc_patch_byte_for_current_offset_byte_lo:
    lda linked_reloc_cursor_window+RELOC_RECORD_ADDR_LO
    jmp find_reloc_patch_byte_for_current_offset_byte_done
find_reloc_patch_byte_for_current_offset_byte_hi:
    lda linked_reloc_cursor_window+RELOC_RECORD_ADDR_HI
find_reloc_patch_byte_for_current_offset_byte_done:
    pha
    lda #$01
    sta linked_reloc_cursor_advance
    pla
    clc
    rts
find_reloc_patch_byte_for_current_offset_lo:
    lda linked_reloc_cursor_window+RELOC_RECORD_ADDR_LO
    clc
    rts
find_reloc_patch_byte_for_current_offset_hi:
    lda #$01
    sta linked_reloc_cursor_advance
    lda linked_reloc_cursor_window+RELOC_RECORD_ADDR_HI
    clc
    rts
find_reloc_patch_byte_for_current_offset_not_found:
    sec
    rts

parse_object_code_import_index_at_scan_ptr_or_fail:
    ldy #$00
    lda (scan_ptr),y
    jsr object_code_import_index_from_a
    bcc parse_object_code_import_index_at_scan_ptr_ok
    jmp build_object_code_prg_bad
parse_object_code_import_index_at_scan_ptr_ok:
    pha
    jsr advance_scan_ptr
    pla
    rts

object_code_import_index_from_a:
    cmp #'0'
    bcc object_code_import_index_check_upper
    cmp #'9'+1
    bcc object_code_import_index_digit
object_code_import_index_check_upper:
    cmp #'A'
    bcc object_code_import_index_check_lower
    cmp #'Z'+1
    bcc object_code_import_index_upper
object_code_import_index_check_lower:
    cmp #'a'
    bcc object_code_import_index_bad
    cmp #'z'+1
    bcc object_code_import_index_lower
object_code_import_index_bad:
    sec
    rts
object_code_import_index_digit:
    sec
    sbc #'0'
    clc
    rts
object_code_import_index_upper:
    sec
    sbc #'A'
    clc
    adc #10
    clc
    rts
object_code_import_index_lower:
    sec
    sbc #'a'
    clc
    adc #10
    clc
    rts

copy_loaded_import_index_to_pending_window_or_fail:
    sta linked_import_index
    lda #$00
    sta linked_external_index
    jsr reset_scan_ptr_after_header
copy_loaded_import_index_to_pending_window_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq copy_loaded_import_index_to_pending_window_bad
    lda #<line_external
    sta const_ptr
    lda #>line_external
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs copy_loaded_import_index_to_pending_window_next
    lda linked_external_index
    cmp linked_import_index
    beq copy_loaded_import_index_to_pending_window_found
    inc linked_external_index
copy_loaded_import_index_to_pending_window_next:
    jsr skip_current_line
    jmp copy_loaded_import_index_to_pending_window_loop
copy_loaded_import_index_to_pending_window_found:
    jsr advance_scan_ptr_by_const_ptr
    jmp copy_import_symbol_line_to_pending_window_or_fail
copy_loaded_import_index_to_pending_window_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr

find_pending_name_in_external_queue_or_fail:
    jsr find_pending_name_in_external_queue
    bcs find_pending_name_in_external_queue_or_fail_bad
    rts

find_pending_name_in_external_queue:
    lda #$00
    sta linked_external_index
find_pending_name_in_external_queue_loop:
    ldx linked_external_index
    cpx external_count
    beq find_pending_name_in_external_queue_bad
    jsr load_external_name_window_from_x_or_fail
    jsr pending_name_matches_external_window
    bcc find_pending_name_in_external_queue_found
    inc linked_external_index
    jmp find_pending_name_in_external_queue_loop
find_pending_name_in_external_queue_found:
    ldx linked_external_index
    clc
    rts
find_pending_name_in_external_queue_bad:
    sec
    rts

find_pending_name_in_external_queue_or_fail_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr

resolve_pending_name_target_meta_or_fail:
    jsr find_pending_name_in_external_queue
    bcs resolve_pending_name_target_meta_try_current
    jsr load_pending_meta_window_from_x_or_fail
    rts
resolve_pending_name_target_meta_try_current:
    jsr load_current_object_export_target_to_pending_meta
    bcs resolve_pending_name_target_meta_try_root
    rts
resolve_pending_name_target_meta_try_root:
    jsr load_root_export_target_to_pending_meta_or_fail
    rts

set_current_object_context_to_root_export_or_fail:
    lda #$00
    sta current_object_addr_lo
    lda #$10
    sta current_object_addr_hi
    jmp set_current_object_selected_export_range_or_fail

set_current_object_context_from_pending_index_x_or_fail:
    jsr load_pending_meta_window_from_x_or_fail
    lda pending_meta_window+PENDING_META_OFFSET_LO
    sta current_object_addr_lo
    lda pending_meta_window+PENDING_META_OFFSET_HI
    sta current_object_addr_hi
    jmp set_current_object_selected_export_range_or_fail

set_current_object_selected_export_range_or_fail:
    lda export_meta_window+EXPORT_META_OFFSET_LO
    sta current_object_export_start_lo
    lda export_meta_window+EXPORT_META_OFFSET_HI
    sta current_object_export_start_hi
    clc
    lda export_meta_window+EXPORT_META_OFFSET_LO
    adc export_meta_window+EXPORT_META_SIZE_LO
    sta current_object_export_end_lo
    lda export_meta_window+EXPORT_META_OFFSET_HI
    adc export_meta_window+EXPORT_META_SIZE_HI
    sta current_object_export_end_hi
    bcc set_current_object_selected_export_range_ok
    jmp build_object_code_prg_bad
set_current_object_selected_export_range_ok:
    rts

load_current_object_export_target_to_pending_meta:
    jsr reset_scan_ptr_after_header
load_current_object_export_target_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq load_current_object_export_target_not_found
    lda #<line_export
    sta const_ptr
    lda #>line_export
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs load_current_object_export_target_next
    jsr advance_scan_ptr_by_const_ptr
    jsr pending_name_matches_scan_symbol
    bcc load_current_object_export_target_found
load_current_object_export_target_next:
    jsr skip_current_line
    jmp load_current_object_export_target_loop
load_current_object_export_target_found:
    jsr skip_symbol_at_scan_ptr_or_fail
    jsr require_space_or_fail
    jsr parse_decimal_word_or_fail
    jsr current_object_export_target_is_selected
    bcs load_current_object_export_target_bad
    sec
    lda current_bit_lo
    sbc current_object_export_start_lo
    sta parse_word_temp_lo
    lda current_bit_hi
    sbc current_object_export_start_hi
    sta parse_word_temp_hi
    clc
    lda current_object_addr_lo
    adc parse_word_temp_lo
    sta pending_meta_window+PENDING_META_OFFSET_LO
    lda current_object_addr_hi
    adc parse_word_temp_hi
    sta pending_meta_window+PENDING_META_OFFSET_HI
    bcc load_current_object_export_target_ok
load_current_object_export_target_bad:
    jmp build_object_code_prg_bad
load_current_object_export_target_ok:
    clc
    rts
load_current_object_export_target_not_found:
    sec
    rts

current_object_export_target_is_selected:
    lda current_bit_hi
    cmp current_object_export_start_hi
    bcc current_object_export_target_is_selected_no
    bne current_object_export_target_is_selected_after_start
    lda current_bit_lo
    cmp current_object_export_start_lo
    bcc current_object_export_target_is_selected_no
current_object_export_target_is_selected_after_start:
    lda current_bit_hi
    cmp current_object_export_end_hi
    bcc current_object_export_target_is_selected_yes
    bne current_object_export_target_is_selected_no
    lda current_bit_lo
    cmp current_object_export_end_lo
    bcc current_object_export_target_is_selected_yes
current_object_export_target_is_selected_no:
    sec
    rts
current_object_export_target_is_selected_yes:
    clc
    rts

load_root_export_target_to_pending_meta_or_fail:
    lda #$00
    sta linked_external_index
load_root_export_target_to_pending_meta_loop:
    ldx linked_external_index
    cpx saved_export_count
    beq load_root_export_target_to_pending_meta_bad
    jsr load_root_export_name_window_from_x_or_fail
    jsr pending_name_matches_export_window
    bcc load_root_export_target_to_pending_meta_found
    inc linked_external_index
    jmp load_root_export_target_to_pending_meta_loop
load_root_export_target_to_pending_meta_found:
    ldx linked_external_index
    jsr load_root_export_layout_window_from_x_or_fail
    lda export_layout_window+EXPORT_LAYOUT_LO
    ora export_layout_window+EXPORT_LAYOUT_HI
    beq load_root_export_target_to_pending_meta_bad
    lda export_layout_window+EXPORT_LAYOUT_LO
    sta pending_meta_window+PENDING_META_OFFSET_LO
    lda export_layout_window+EXPORT_LAYOUT_HI
    sta pending_meta_window+PENDING_META_OFFSET_HI
    rts
load_root_export_target_to_pending_meta_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr

direct_entry_body_is_object_code:
    ldx entry_export_index
    jsr set_body_ptr_from_x
    lda body_ptr
    sta scan_ptr
    lda body_ptr+1
    sta scan_ptr+1
    jmp object_code_body_at_scan_ptr_is_supported

loaded_first_body_is_object_code:
    jsr reset_scan_ptr_after_header
loaded_first_body_is_object_code_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq loaded_first_body_is_object_code_fail
    lda #<line_body
    sta const_ptr
    lda #>line_body
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs loaded_first_body_is_object_code_next
    jsr advance_scan_ptr_by_const_ptr
    jmp object_code_body_at_scan_ptr_is_supported
loaded_first_body_is_object_code_next:
    jsr skip_current_line
    jmp loaded_first_body_is_object_code_loop
loaded_first_body_is_object_code_fail:
    sec
    rts

object_code_body_at_scan_ptr_is_supported:
    ldy #$00
    lda (scan_ptr),y
    cmp #'M'
    beq object_code_body_at_scan_ptr_check_end_after_m
    cmp #'u'
    bne object_code_body_at_scan_ptr_fail
object_code_body_at_scan_ptr_loop:
    lda (scan_ptr),y
    cmp #'u'
    bne object_code_body_at_scan_ptr_fail
    iny
    lda (scan_ptr),y
    jsr object_code_import_index_from_a
    bcs object_code_body_at_scan_ptr_fail
    iny
    lda (scan_ptr),y
    cmp #'u'
    beq object_code_body_at_scan_ptr_loop
    cmp #'M'
    bne object_code_body_at_scan_ptr_fail
object_code_body_at_scan_ptr_check_end_after_m:
    iny
    lda (scan_ptr),y
    beq object_code_body_at_scan_ptr_ok
    cmp #10
    beq object_code_body_at_scan_ptr_ok
    cmp #13
    beq object_code_body_at_scan_ptr_ok
object_code_body_at_scan_ptr_fail:
    sec
    rts
object_code_body_at_scan_ptr_ok:
    clc
    rts

parse_hex_nibble_from_a_or_fail:
    cmp #'0'
    bcc parse_hex_nibble_bad
    cmp #'9'+1
    bcc parse_hex_nibble_digit
    cmp #'A'
    bcc parse_hex_nibble_check_lower
    cmp #'F'+1
    bcc parse_hex_nibble_upper
parse_hex_nibble_check_lower:
    cmp #'a'
    bcc parse_hex_nibble_bad
    cmp #'f'+1
    bcs parse_hex_nibble_bad
    sec
    sbc #('a' - 10)
    rts
parse_hex_nibble_upper:
    sec
    sbc #('A' - 10)
    rts
parse_hex_nibble_digit:
    sec
    sbc #'0'
    rts
parse_hex_nibble_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr

copy_direct_prg_template:
    lda current_bit_lo
    sta saved_state_lo
    lda current_bit_hi
    sta saved_state_hi
copy_direct_prg_template_loop:
    lda saved_state_lo
    ora saved_state_hi
    beq copy_direct_prg_template_done
    ldy #$00
    lda (const_ptr),y
    jsr append_payload_byte
    inc const_ptr
    bne :+
    inc const_ptr+1
:   lda saved_state_lo
    bne :+
    dec saved_state_hi
:   dec saved_state_lo
    jmp copy_direct_prg_template_loop
copy_direct_prg_template_done:
    rts
