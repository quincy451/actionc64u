; Direct PRG templates used by the helper-free ALINK proof surface.
select_prg_build_strategy_or_fail:
    lda #PRG_BUILD_DIRECT
    sta prg_build_strategy
    jsr find_linked_return_pair_prg_case
    bcs select_prg_build_strategy_not_return_pair
    rts
select_prg_build_strategy_not_return_pair:
    jsr find_linked_printmath_prg_case
    bcs select_prg_build_strategy_not_printmath
    rts
select_prg_build_strategy_not_printmath:
    jsr find_linked_real_print_int_prg_case
    bcs select_prg_build_strategy_not_real_print_int
    rts
select_prg_build_strategy_not_real_print_int:
    jsr find_linked_real_print_div_prg_case
    bcs select_prg_build_strategy_not_real_print_div
    rts
select_prg_build_strategy_not_real_print_div:
    jsr find_runtime_literal_call_prg_case
    bcs select_prg_build_strategy_not_runtime_literal_call
    rts
select_prg_build_strategy_not_runtime_literal_call:
    jsr find_object_code_external_prg_case
    bcs select_prg_build_strategy_not_object_code_external
    rts
select_prg_build_strategy_not_object_code_external:
    jsr find_object_code_prg_case
    bcs select_prg_build_strategy_not_object_code
    rts
select_prg_build_strategy_not_object_code:
    jsr find_linked_print_prg_case
    bcs select_prg_build_strategy_direct
    rts
select_prg_build_strategy_direct:
    jmp require_direct_prg_body_supported_or_fail

build_prg_content_or_fail:
    lda prg_build_strategy
    cmp #PRG_BUILD_TRANSITIVE_EXTERNAL_PRINT
    bne build_prg_content_not_transitive_external_print
    jmp build_transitive_external_print_prg_content_or_fail
build_prg_content_not_transitive_external_print:
    lda prg_build_strategy
    cmp #PRG_BUILD_EXTERNAL_PRINT
    bne build_prg_content_not_external_print
    jmp build_external_print_prg_content_or_fail
build_prg_content_not_external_print:
    lda prg_build_strategy
    cmp #PRG_BUILD_TRANSITIVE_EXTERNAL_RETURN
    bne build_prg_content_not_transitive_external_return
    jmp build_transitive_external_return_prg_content_or_fail
build_prg_content_not_transitive_external_return:
    lda prg_build_strategy
    cmp #PRG_BUILD_EXTERNAL_RETURN
    bne build_prg_content_not_external_return
    jmp build_external_return_prg_content_or_fail
build_prg_content_not_external_return:
    lda prg_build_strategy
    cmp #PRG_BUILD_EXTERNAL_RETURN_PAIR
    bne build_prg_content_not_external_return_pair
    jmp build_external_return_pair_prg_content_or_fail
build_prg_content_not_external_return_pair:
    lda prg_build_strategy
    cmp #PRG_BUILD_EXTERNAL_STORE
    bne build_prg_content_not_external_store
    jmp build_external_store_prg_content_or_fail
build_prg_content_not_external_store:
    lda prg_build_strategy
    cmp #PRG_BUILD_TRANSITIVE_EXTERNAL_STORE
    bne build_prg_content_not_transitive_external_store
    jmp build_transitive_external_store_prg_content_or_fail
build_prg_content_not_transitive_external_store:
    lda prg_build_strategy
    cmp #PRG_BUILD_EXTERNAL_LOAD_STORE
    bne build_prg_content_not_external_load_store
    jmp build_external_load_store_prg_content_or_fail
build_prg_content_not_external_load_store:
    lda prg_build_strategy
    cmp #PRG_BUILD_TRANSITIVE_EXTERNAL_LOAD_STORE
    bne build_prg_content_not_transitive_external_load_store
    jmp build_transitive_external_load_store_prg_content_or_fail
build_prg_content_not_transitive_external_load_store:
    lda prg_build_strategy
    cmp #PRG_BUILD_EXTERNAL_STRING_INT
    bne build_prg_content_not_external_string_int
    jmp build_external_string_int_prg_content_or_fail
build_prg_content_not_external_string_int:
    lda prg_build_strategy
    cmp #PRG_BUILD_TRANSITIVE_EXTERNAL_STRING_INT
    bne build_prg_content_not_transitive_external_string_int
    jmp build_transitive_external_string_int_prg_content_or_fail
build_prg_content_not_transitive_external_string_int:
    lda prg_build_strategy
    cmp #PRG_BUILD_PRINTMATH_STRING_INT
    bne build_prg_content_not_printmath_string_int
    jmp build_printmath_linked_string_int_prg_content_or_fail
build_prg_content_not_printmath_string_int:
    lda prg_build_strategy
    cmp #PRG_BUILD_REAL_PRINT_INT
    bne build_prg_content_not_real_print_int
    jmp build_real_print_int_prg_content_or_fail
build_prg_content_not_real_print_int:
    lda prg_build_strategy
    cmp #PRG_BUILD_REAL_PRINT_DIV
    bne build_prg_content_not_real_print_div
    jmp build_real_print_div_prg_content_or_fail
build_prg_content_not_real_print_div:
    lda prg_build_strategy
    cmp #PRG_BUILD_RUNTIME_LITERAL_CALL
    bne build_prg_content_not_runtime_literal_call
    jmp build_runtime_literal_call_prg_content_or_fail
build_prg_content_not_runtime_literal_call:
    lda prg_build_strategy
    cmp #PRG_BUILD_OBJECT_CODE
    bne build_prg_content_not_object_code
    jmp build_object_code_prg_content_or_fail
build_prg_content_not_object_code:
    lda prg_build_strategy
    cmp #PRG_BUILD_OBJECT_CODE_EXTERNAL
    bne build_prg_content_direct
    jmp build_object_code_external_prg_content_or_fail
build_prg_content_direct:
    jmp build_direct_prg_content_or_fail

build_direct_prg_content_or_fail:
    jsr find_direct_prg_candidate_or_fail
    ldx direct_candidate_index
    lda direct_template_table_lo,x
    sta const_ptr
    lda direct_template_table_hi,x
    sta const_ptr+1
    lda direct_template_len_lo,x
    sta current_bit_lo
    lda direct_template_len_hi,x
    sta current_bit_hi
    jmp copy_direct_prg_template

require_direct_prg_body_supported_or_fail:
    jmp find_direct_prg_candidate_or_fail

find_direct_prg_candidate_or_fail:
    lda #$00
    sta direct_candidate_index
find_direct_prg_candidate_loop:
    ldx direct_candidate_index
    cpx #34
    beq build_direct_prg_fallback
    lda direct_body_table_lo,x
    sta const_ptr
    lda direct_body_table_hi,x
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcc find_direct_prg_candidate_done
    inc direct_candidate_index
    jmp find_direct_prg_candidate_loop
find_direct_prg_candidate_done:
    rts
build_direct_prg_fallback:
    lda #<msg_unsupported_body
    ldy #>msg_unsupported_body
    jmp fail_with_ptr

find_linked_return_pair_prg_case:
    lda #<linked_body_external_return_pair
    sta const_ptr
    lda #>linked_body_external_return_pair
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcc find_linked_return_pair_prg_case_body_ok
    sec
    rts
find_linked_return_pair_prg_case_body_ok:
    lda external_count
    cmp #$02
    bcs find_linked_return_pair_prg_case_have_externals
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_return_pair_prg_case_have_externals:
    jsr save_current_module_name
    ldx #$00
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_r
    bcs find_linked_return_pair_prg_case_unsupported
    ldx #$01
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_r
    bcs find_linked_return_pair_prg_case_unsupported
    jsr restore_saved_module_name
    lda #PRG_BUILD_EXTERNAL_RETURN_PAIR
    sta prg_build_strategy
    clc
    rts
find_linked_return_pair_prg_case_unsupported:
    jsr restore_saved_module_name
    sec
    rts

find_linked_printmath_prg_case:
    lda #<direct_body_printmath
    sta const_ptr
    lda #>direct_body_printmath
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcc find_linked_printmath_prg_case_body_ok
    sec
    rts
find_linked_printmath_prg_case_body_ok:
    lda external_count
    bne find_linked_printmath_prg_case_have_external
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_printmath_prg_case_have_external:
    jsr save_current_module_name
    ldx #$00
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_s0i0r
    bcs find_linked_printmath_prg_case_unsupported
    jsr require_loaded_external_print_string_or_fail
    jsr require_loaded_external_store_int_or_fail
    jsr restore_saved_module_name
    lda #PRG_BUILD_PRINTMATH_STRING_INT
    sta prg_build_strategy
    clc
    rts
find_linked_printmath_prg_case_unsupported:
    jsr restore_saved_module_name
    sec
    rts

find_linked_real_print_int_prg_case:
    lda #<direct_body_real_print_int
    sta const_ptr
    lda #>direct_body_real_print_int
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcc find_linked_real_print_int_prg_case_body_ok
    sec
    rts
find_linked_real_print_int_prg_case_body_ok:
    lda external_count
    cmp #$02
    bcs find_linked_real_print_int_prg_case_have_externals
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_print_int_prg_case_have_externals:
    lda int_count
    cmp #$03
    bcs find_linked_real_print_int_prg_case_have_ints
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_print_int_prg_case_have_ints:
    jsr save_current_module_name
    ldx #$00
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_Wr
    bcs find_linked_real_print_int_prg_case_unsupported
    ldx #$01
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_Yr
    bcs find_linked_real_print_int_prg_case_unsupported
    ldx #$01
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    bne find_linked_real_print_int_prg_case_unsupported
    lda int_value_window
    sta linked_store_value
    jsr restore_saved_module_name
    lda #PRG_BUILD_REAL_PRINT_INT
    sta prg_build_strategy
    clc
    rts
find_linked_real_print_int_prg_case_unsupported:
    jsr restore_saved_module_name
    sec
    rts

find_linked_real_print_div_prg_case:
    lda #<direct_body_real_print_div
    sta const_ptr
    lda #>direct_body_real_print_div
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcc find_linked_real_print_div_prg_case_body_ok
    sec
    rts
find_linked_real_print_div_prg_case_body_ok:
    lda external_count
    cmp #$03
    bcs find_linked_real_print_div_prg_case_have_externals
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_print_div_prg_case_have_externals:
    lda int_count
    cmp #$05
    bcs find_linked_real_print_div_prg_case_have_ints
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_print_div_prg_case_have_ints:
    jsr save_current_module_name
    ldx #$00
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_Wr
    bcs find_linked_real_print_div_prg_case_unsupported
    ldx #$01
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_Vr
    bcs find_linked_real_print_div_prg_case_unsupported
    ldx #$02
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_Yr
    bcs find_linked_real_print_div_prg_case_unsupported
    ldx #$01
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    bne find_linked_real_print_div_prg_case_unsupported
    lda int_value_window
    sta linked_store_value
    ldx #$03
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    bne find_linked_real_print_div_prg_case_unsupported
    lda int_value_window
    beq find_linked_real_print_div_prg_case_unsupported
    cmp #26
    bcs find_linked_real_print_div_prg_case_unsupported
    sta linked_divisor_value
    ldx #$04
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    bne find_linked_real_print_div_prg_case_unsupported
    lda int_value_window
    cmp #$01
    bne find_linked_real_print_div_prg_case_unsupported
    jsr restore_saved_module_name
    lda #PRG_BUILD_REAL_PRINT_DIV
    sta prg_build_strategy
    clc
    rts
find_linked_real_print_div_prg_case_unsupported:
    jsr restore_saved_module_name
    sec
    rts

find_runtime_literal_call_prg_case:
    lda #<direct_body_runtime_literal_call
    sta const_ptr
    lda #>direct_body_runtime_literal_call
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs find_runtime_literal_call_prg_case_not_single_byte
    lda #$01
    sta linked_literal_count
    jmp find_runtime_literal_call_prg_case_body_ok
find_runtime_literal_call_prg_case_not_single_byte:
    lda #<direct_body_runtime_sprite_data_literal_call
    sta const_ptr
    lda #>direct_body_runtime_sprite_data_literal_call
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs find_runtime_literal_call_prg_case_not_sprite_data
    lda #$02
    sta linked_literal_count
    jmp find_runtime_literal_call_prg_case_body_ok
find_runtime_literal_call_prg_case_not_sprite_data:
    lda #<direct_body_runtime_sprite_pos_literal_call
    sta const_ptr
    lda #>direct_body_runtime_sprite_pos_literal_call
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs find_runtime_literal_call_prg_case_not_sprite_pos
    lda #$03
    sta linked_literal_count
    jmp find_runtime_literal_call_prg_case_body_ok
find_runtime_literal_call_prg_case_not_sprite_pos:
    lda #<direct_body_runtime_sound_literal_call
    sta const_ptr
    lda #>direct_body_runtime_sound_literal_call
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs find_runtime_literal_call_prg_case_no_match
    lda #$04
    sta linked_literal_count
    jmp find_runtime_literal_call_prg_case_body_ok
find_runtime_literal_call_prg_case_no_match:
    sec
    rts
find_runtime_literal_call_prg_case_body_ok:
    lda external_count
    bne find_runtime_literal_call_prg_case_have_external
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_runtime_literal_call_prg_case_have_external:
    lda linked_literal_count
    cmp #$02
    bne find_runtime_literal_call_prg_case_not_sprite_data_external
    jsr runtime_literal_call_first_external_is_rt_sprite_data
    bcc find_runtime_literal_call_prg_case_have_supported_external
    jsr runtime_literal_call_first_external_is_rt_sprite_color
    bcc find_runtime_literal_call_prg_case_have_supported_external
    jsr runtime_literal_call_first_external_is_rt_sprite_ptr
    bcc find_runtime_literal_call_prg_case_have_supported_external
    jsr runtime_literal_call_first_external_is_sprite_flag_helper
    bcc find_runtime_literal_call_prg_case_have_supported_external
    jmp find_runtime_literal_call_prg_case_unsupported_value
find_runtime_literal_call_prg_case_not_sprite_data_external:
    lda linked_literal_count
    cmp #$03
    bne find_runtime_literal_call_prg_case_not_sprite_pos_external
    jsr runtime_literal_call_first_external_is_rt_sprite_pos
    bcc find_runtime_literal_call_prg_case_have_supported_external
    jmp find_runtime_literal_call_prg_case_unsupported_value
find_runtime_literal_call_prg_case_not_sprite_pos_external:
    lda linked_literal_count
    cmp #$04
    bne find_runtime_literal_call_prg_case_have_supported_external
    jsr runtime_literal_call_first_external_is_rt_sound
    bcc find_runtime_literal_call_prg_case_have_supported_external
    jmp find_runtime_literal_call_prg_case_unsupported_value
find_runtime_literal_call_prg_case_have_supported_external:
    lda int_count
    cmp linked_literal_count
    bcs find_runtime_literal_call_prg_case_have_int
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_runtime_literal_call_prg_case_have_int:
    lda #$00
    sta linked_object_index
find_runtime_literal_call_prg_case_int_loop:
    ldx linked_object_index
    cpx linked_literal_count
    beq find_runtime_literal_call_prg_case_loaded_ints
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ldx linked_object_index
    sta linked_literal_values,x
    lda int_value_window+1
    sta linked_literal_hi_values,x
    beq find_runtime_literal_call_prg_case_int_ok
    lda linked_literal_count
    cmp #$02
    beq find_runtime_literal_call_prg_case_allow_sprite_data_word
    cmp #$03
    bne find_runtime_literal_call_prg_case_unsupported_value
    ldx linked_object_index
    cpx #$01
    bne find_runtime_literal_call_prg_case_unsupported_value
    lda int_value_window+1
    cmp #$02
    bcs find_runtime_literal_call_prg_case_unsupported_value
    jmp find_runtime_literal_call_prg_case_int_ok
find_runtime_literal_call_prg_case_allow_sprite_data_word:
    jsr runtime_literal_call_first_external_is_rt_sprite_data
    bcs find_runtime_literal_call_prg_case_unsupported_value
    ldx linked_object_index
    cpx #$01
    bne find_runtime_literal_call_prg_case_unsupported_value
find_runtime_literal_call_prg_case_int_ok:
    inc linked_object_index
    jmp find_runtime_literal_call_prg_case_int_loop
find_runtime_literal_call_prg_case_loaded_ints:
    jsr save_current_module_name
    lda #$00
    sta linked_object_index
find_runtime_literal_call_prg_case_loop:
    ldx linked_object_index
    cpx external_count
    beq find_runtime_literal_call_prg_case_supported
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_first_body_is_object_code
    bcs find_runtime_literal_call_prg_case_unsupported
    inc linked_object_index
    jmp find_runtime_literal_call_prg_case_loop
find_runtime_literal_call_prg_case_supported:
    jsr restore_saved_module_name
    lda #PRG_BUILD_RUNTIME_LITERAL_CALL
    sta prg_build_strategy
    clc
    rts
find_runtime_literal_call_prg_case_unsupported:
    jsr restore_saved_module_name
find_runtime_literal_call_prg_case_unsupported_value:
    sec
    rts

runtime_literal_call_first_external_is_rt_sound:
    ldx #$00
    jsr load_external_name_window_from_x_or_fail
    lda #<runtime_name_rt_sound
    sta const_ptr
    lda #>runtime_name_rt_sound
    sta const_ptr+1
    jmp external_name_window_matches_const_ptr

runtime_literal_call_first_external_is_rt_sprite_data:
    ldx #$00
    jsr load_external_name_window_from_x_or_fail
    lda #<runtime_name_rt_sprite_data
    sta const_ptr
    lda #>runtime_name_rt_sprite_data
    sta const_ptr+1
    jmp external_name_window_matches_const_ptr

runtime_literal_call_first_external_is_rt_sprite_pos:
    ldx #$00
    jsr load_external_name_window_from_x_or_fail
    lda #<runtime_name_rt_sprite_pos
    sta const_ptr
    lda #>runtime_name_rt_sprite_pos
    sta const_ptr+1
    jmp external_name_window_matches_const_ptr

runtime_literal_call_first_external_is_rt_sprite_color:
    ldx #$00
    jsr load_external_name_window_from_x_or_fail
    lda #<runtime_name_rt_sprite_color
    sta const_ptr
    lda #>runtime_name_rt_sprite_color
    sta const_ptr+1
    jmp external_name_window_matches_const_ptr

runtime_literal_call_first_external_is_rt_sprite_ptr:
    ldx #$00
    jsr load_external_name_window_from_x_or_fail
    lda #<runtime_name_rt_sprite_ptr
    sta const_ptr
    lda #>runtime_name_rt_sprite_ptr
    sta const_ptr+1
    jmp external_name_window_matches_const_ptr

runtime_literal_call_first_external_is_sprite_flag_helper:
    jsr runtime_literal_call_first_external_is_rt_sprite_mc
    bcc runtime_literal_call_first_external_is_sprite_flag_ok
    jsr runtime_literal_call_first_external_is_rt_sprite_xexp
    bcc runtime_literal_call_first_external_is_sprite_flag_ok
    jsr runtime_literal_call_first_external_is_rt_sprite_yexp
    bcc runtime_literal_call_first_external_is_sprite_flag_ok
    jsr runtime_literal_call_first_external_is_rt_sprite_prio
    bcc runtime_literal_call_first_external_is_sprite_flag_ok
    sec
    rts
runtime_literal_call_first_external_is_sprite_flag_ok:
    clc
    rts

runtime_literal_call_first_external_is_rt_sprite_mc:
    ldx #$00
    jsr load_external_name_window_from_x_or_fail
    lda #<runtime_name_rt_sprite_mc
    sta const_ptr
    lda #>runtime_name_rt_sprite_mc
    sta const_ptr+1
    jmp external_name_window_matches_const_ptr

runtime_literal_call_first_external_is_rt_sprite_xexp:
    ldx #$00
    jsr load_external_name_window_from_x_or_fail
    lda #<runtime_name_rt_sprite_xexp
    sta const_ptr
    lda #>runtime_name_rt_sprite_xexp
    sta const_ptr+1
    jmp external_name_window_matches_const_ptr

runtime_literal_call_first_external_is_rt_sprite_yexp:
    ldx #$00
    jsr load_external_name_window_from_x_or_fail
    lda #<runtime_name_rt_sprite_yexp
    sta const_ptr
    lda #>runtime_name_rt_sprite_yexp
    sta const_ptr+1
    jmp external_name_window_matches_const_ptr

runtime_literal_call_first_external_is_rt_sprite_prio:
    ldx #$00
    jsr load_external_name_window_from_x_or_fail
    lda #<runtime_name_rt_sprite_prio
    sta const_ptr
    lda #>runtime_name_rt_sprite_prio
    sta const_ptr+1
    jmp external_name_window_matches_const_ptr

external_name_window_matches_const_ptr:
    ldy #$00
external_name_window_matches_const_ptr_loop:
    lda (const_ptr),y
    cmp external_name_window,y
    bne external_name_window_matches_const_ptr_fail
    lda (const_ptr),y
    beq external_name_window_matches_const_ptr_ok
    iny
    cpy #25
    bcc external_name_window_matches_const_ptr_loop
external_name_window_matches_const_ptr_fail:
    sec
    rts
external_name_window_matches_const_ptr_ok:
    clc
    rts

find_object_code_external_prg_case:
    jsr direct_entry_body_is_object_code_external
    bcc find_object_code_external_prg_case_body_ok
    sec
    rts
find_object_code_external_prg_case_body_ok:
    lda external_count
    bne find_object_code_external_prg_case_have_external
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_object_code_external_prg_case_have_external:
    jsr save_current_module_name
    lda #$00
    sta linked_object_index
find_object_code_external_prg_case_loop:
    ldx linked_object_index
    cpx external_count
    beq find_object_code_external_prg_case_supported
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_first_body_is_object_code
    bcs find_object_code_external_prg_case_unsupported
    inc linked_object_index
    jmp find_object_code_external_prg_case_loop
find_object_code_external_prg_case_supported:
    jsr restore_saved_module_name
    lda #PRG_BUILD_OBJECT_CODE_EXTERNAL
    sta prg_build_strategy
    clc
    rts
find_object_code_external_prg_case_unsupported:
    jsr restore_saved_module_name
    sec
    rts

find_object_code_prg_case:
    lda #<direct_body_object_code
    sta const_ptr
    lda #>direct_body_object_code
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcc find_object_code_prg_case_body_ok
    sec
    rts
find_object_code_prg_case_body_ok:
    lda #PRG_BUILD_OBJECT_CODE
    sta prg_build_strategy
    clc
    rts

find_linked_print_prg_case:
    ldx entry_export_index
    jsr set_body_ptr_from_x
    ldy #$00
    lda (body_ptr),y
    cmp #'u'
    beq find_linked_print_prg_case_root_u
    jmp find_linked_print_prg_case_no
find_linked_print_prg_case_root_u:
    iny
    lda (body_ptr),y
    cmp #'0'
    beq find_linked_print_prg_case_root_zero
    jmp find_linked_print_prg_case_no
find_linked_print_prg_case_root_zero:
    iny
    lda (body_ptr),y
    cmp #'r'
    beq find_linked_print_prg_case_root_return
    jmp find_linked_print_prg_case_no
find_linked_print_prg_case_root_return:
    iny
    lda (body_ptr),y
    beq find_linked_print_prg_case_root_ok
    jmp find_linked_print_prg_case_no
find_linked_print_prg_case_root_ok:
    lda external_count
    bne find_linked_print_prg_case_have_external
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_print_prg_case_have_external:
    jsr save_current_module_name
    ldx #$00
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_e0r
    bcs find_linked_print_prg_case_check_return
    jsr require_loaded_external_print_string_or_fail
    jsr restore_saved_module_name
    lda #PRG_BUILD_EXTERNAL_PRINT
    sta prg_build_strategy
    clc
    rts
find_linked_print_prg_case_check_return:
    jsr loaded_external_print_body_is_r
    bcs find_linked_print_prg_case_check_store
    jsr restore_saved_module_name
    lda #PRG_BUILD_EXTERNAL_RETURN
    sta prg_build_strategy
    clc
    rts
find_linked_print_prg_case_check_store:
    jsr loaded_external_print_body_is_p0S0r
    bcs find_linked_print_prg_case_check_load_store
    jsr require_loaded_external_store_int_or_fail
    jsr restore_saved_module_name
    lda #PRG_BUILD_EXTERNAL_STORE
    sta prg_build_strategy
    clc
    rts
find_linked_print_prg_case_check_load_store:
    jsr loaded_external_print_body_is_p0S0L0S1r
    bcs find_linked_print_prg_case_check_string_int
    jsr require_loaded_external_store_int_or_fail
    jsr restore_saved_module_name
    lda #PRG_BUILD_EXTERNAL_LOAD_STORE
    sta prg_build_strategy
    clc
    rts
find_linked_print_prg_case_check_string_int:
    jsr loaded_external_print_body_is_s0i0r
    bcs find_linked_print_prg_case_check_transitive
    jsr require_loaded_external_print_string_or_fail
    jsr require_loaded_external_store_int_or_fail
    jsr restore_saved_module_name
    lda #PRG_BUILD_EXTERNAL_STRING_INT
    sta prg_build_strategy
    clc
    rts
find_linked_print_prg_case_check_transitive:
    jsr loaded_external_print_body_is_u0r
    bcc find_linked_print_prg_case_load_transitive
    jsr restore_saved_module_name
    sec
    rts
find_linked_print_prg_case_load_transitive:
    jsr copy_loaded_first_import_to_module_name_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_e0r
    bcs find_linked_print_prg_case_check_transitive_return
    jsr require_loaded_external_print_string_or_fail
    jsr restore_saved_module_name
    lda #PRG_BUILD_TRANSITIVE_EXTERNAL_PRINT
    sta prg_build_strategy
    clc
    rts
find_linked_print_prg_case_check_transitive_return:
    jsr loaded_external_print_body_is_r
    bcs find_linked_print_prg_case_check_transitive_store
    jsr restore_saved_module_name
    lda #PRG_BUILD_TRANSITIVE_EXTERNAL_RETURN
    sta prg_build_strategy
    clc
    rts
find_linked_print_prg_case_check_transitive_store:
    jsr loaded_external_print_body_is_p0S0r
    bcs find_linked_print_prg_case_check_transitive_load_store
    jsr require_loaded_external_store_int_or_fail
    jsr restore_saved_module_name
    lda #PRG_BUILD_TRANSITIVE_EXTERNAL_STORE
    sta prg_build_strategy
    clc
    rts
find_linked_print_prg_case_check_transitive_load_store:
    jsr loaded_external_print_body_is_p0S0L0S1r
    bcs find_linked_print_prg_case_check_transitive_string_int
    jsr require_loaded_external_store_int_or_fail
    jsr restore_saved_module_name
    lda #PRG_BUILD_TRANSITIVE_EXTERNAL_LOAD_STORE
    sta prg_build_strategy
    clc
    rts
find_linked_print_prg_case_check_transitive_string_int:
    jsr loaded_external_print_body_is_s0i0r
    bcs find_linked_print_prg_case_transitive_unsupported
    jsr require_loaded_external_print_string_or_fail
    jsr require_loaded_external_store_int_or_fail
    jsr restore_saved_module_name
    lda #PRG_BUILD_TRANSITIVE_EXTERNAL_STRING_INT
    sta prg_build_strategy
    clc
    rts
find_linked_print_prg_case_transitive_unsupported:
    jsr restore_saved_module_name
    sec
    rts
find_linked_print_prg_case_no:
    sec
    rts

require_loaded_external_print_body_or_fail:
    jsr loaded_external_print_body_is_e0r
    bcc require_loaded_external_print_body_ok
    jmp require_loaded_external_print_body_bad
require_loaded_external_print_body_ok:
    rts

loaded_external_print_body_is_e0r:
    lda #<linked_body_print_e
    sta const_ptr
    lda #>linked_body_print_e
    sta const_ptr+1
    jmp loaded_first_body_matches_const_ptr

loaded_external_print_body_is_u0r:
    lda #<linked_body_external_call
    sta const_ptr
    lda #>linked_body_external_call
    sta const_ptr+1
    jmp loaded_first_body_matches_const_ptr

loaded_external_print_body_is_r:
    lda #<linked_body_return
    sta const_ptr
    lda #>linked_body_return
    sta const_ptr+1
    jmp loaded_first_body_matches_const_ptr

loaded_external_print_body_is_p0S0r:
    lda #<linked_body_word_store
    sta const_ptr
    lda #>linked_body_word_store
    sta const_ptr+1
    jmp loaded_first_body_matches_const_ptr

loaded_external_print_body_is_p0S0L0S1r:
    lda #<linked_body_word_load_store
    sta const_ptr
    lda #>linked_body_word_load_store
    sta const_ptr+1
    jmp loaded_first_body_matches_const_ptr

loaded_external_print_body_is_s0i0r:
    lda #<linked_body_string_int
    sta const_ptr
    lda #>linked_body_string_int
    sta const_ptr+1
    jmp loaded_first_body_matches_const_ptr

loaded_external_print_body_is_Wr:
    lda #<linked_body_rt_i_to_f
    sta const_ptr
    lda #>linked_body_rt_i_to_f
    sta const_ptr+1
    jmp loaded_first_body_matches_const_ptr

loaded_external_print_body_is_Vr:
    lda #<linked_body_rt_f_div
    sta const_ptr
    lda #>linked_body_rt_f_div
    sta const_ptr+1
    jmp loaded_first_body_matches_const_ptr

loaded_external_print_body_is_M:
    lda #<direct_body_object_code
    sta const_ptr
    lda #>direct_body_object_code
    sta const_ptr+1
    jmp loaded_first_body_matches_const_ptr

loaded_external_print_body_is_Yr:
    lda #<linked_body_rt_print_f
    sta const_ptr
    lda #>linked_body_rt_print_f
    sta const_ptr+1
    jmp loaded_first_body_matches_const_ptr

loaded_first_body_matches_const_ptr:
    lda const_ptr
    sta saved_state_lo
    lda const_ptr+1
    sta saved_state_hi
    jsr reset_scan_ptr_after_header
loaded_first_body_matches_const_ptr_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq loaded_first_body_matches_const_ptr_no
    lda #<line_body
    sta const_ptr
    lda #>line_body
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs loaded_first_body_matches_const_ptr_next
    jsr advance_scan_ptr_by_const_ptr
    lda saved_state_lo
    sta const_ptr
    lda saved_state_hi
    sta const_ptr+1
    ldy #$00
loaded_first_body_matches_const_ptr_compare:
    lda (const_ptr),y
    beq loaded_first_body_matches_const_ptr_check_end
    cmp (scan_ptr),y
    bne loaded_first_body_matches_const_ptr_no
    iny
    bne loaded_first_body_matches_const_ptr_compare
loaded_first_body_matches_const_ptr_check_end:
    lda (scan_ptr),y
    beq loaded_first_body_matches_const_ptr_ok
    cmp #10
    beq loaded_first_body_matches_const_ptr_ok
    cmp #13
    beq loaded_first_body_matches_const_ptr_ok
    sec
    rts
loaded_first_body_matches_const_ptr_next:
    jsr skip_current_line
    jmp loaded_first_body_matches_const_ptr_loop
loaded_first_body_matches_const_ptr_ok:
    clc
    rts
loaded_first_body_matches_const_ptr_no:
    sec
    rts

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

require_loaded_external_print_body_bad:
    lda #<msg_unsupported_body
    ldy #>msg_unsupported_body
    jmp fail_with_ptr

require_loaded_external_print_string_or_fail:
    jsr reset_scan_ptr_after_header
require_loaded_external_print_string_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq require_loaded_external_print_string_bad
    lda #<line_string
    sta const_ptr
    lda #>line_string
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs require_loaded_external_print_string_next
    jsr advance_scan_ptr_by_const_ptr
    lda scan_ptr
    sta external_print_string_ptr
    lda scan_ptr+1
    sta external_print_string_ptr+1
    rts
require_loaded_external_print_string_next:
    jsr skip_current_line
    jmp require_loaded_external_print_string_loop
require_loaded_external_print_string_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr

require_loaded_external_store_int_or_fail:
    jsr reset_scan_ptr_after_header
require_loaded_external_store_int_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq require_loaded_external_store_int_bad
    lda #<line_int
    sta const_ptr
    lda #>line_int
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs require_loaded_external_store_int_next
    jsr advance_scan_ptr_by_const_ptr
    jsr parse_decimal_byte_or_fail
    sta linked_store_value
    rts
require_loaded_external_store_int_next:
    jsr skip_current_line
    jmp require_loaded_external_store_int_loop
require_loaded_external_store_int_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr

build_external_print_prg_content_or_fail:
    lda #<external_print_prg_template
    sta const_ptr
    lda #>external_print_prg_template
    sta const_ptr+1
    lda #<(external_print_prg_template_end - external_print_prg_template)
    sta current_bit_lo
    lda #>(external_print_prg_template_end - external_print_prg_template)
    sta current_bit_hi
    jsr copy_direct_prg_template
append_external_print_string_to_prg:
    lda external_print_string_ptr
    sta src_ptr
    lda external_print_string_ptr+1
    sta src_ptr+1
build_external_print_prg_string_loop:
    ldy #$00
    lda (src_ptr),y
    beq build_external_print_prg_string_done
    cmp #10
    beq build_external_print_prg_string_done
    cmp #13
    beq build_external_print_prg_string_done
    jsr append_payload_byte
    inc src_ptr
    bne build_external_print_prg_string_loop
    inc src_ptr+1
    jmp build_external_print_prg_string_loop
build_external_print_prg_string_done:
    lda #$00
    jmp append_payload_byte

build_transitive_external_print_prg_content_or_fail:
    lda #<transitive_external_print_prg_template
    sta const_ptr
    lda #>transitive_external_print_prg_template
    sta const_ptr+1
    lda #<(transitive_external_print_prg_template_end - transitive_external_print_prg_template)
    sta current_bit_lo
    lda #>(transitive_external_print_prg_template_end - transitive_external_print_prg_template)
    sta current_bit_hi
    jsr copy_direct_prg_template
    lda external_print_string_ptr
    sta src_ptr
    lda external_print_string_ptr+1
    sta src_ptr+1
    jmp build_external_print_prg_string_loop

build_external_return_prg_content_or_fail:
    lda #<external_return_prg_template
    sta const_ptr
    lda #>external_return_prg_template
    sta const_ptr+1
    lda #<(external_return_prg_template_end - external_return_prg_template)
    sta current_bit_lo
    lda #>(external_return_prg_template_end - external_return_prg_template)
    sta current_bit_hi
    jmp copy_direct_prg_template

build_transitive_external_return_prg_content_or_fail:
    lda #<transitive_external_return_prg_template
    sta const_ptr
    lda #>transitive_external_return_prg_template
    sta const_ptr+1
    lda #<(transitive_external_return_prg_template_end - transitive_external_return_prg_template)
    sta current_bit_lo
    lda #>(transitive_external_return_prg_template_end - transitive_external_return_prg_template)
    sta current_bit_hi
    jmp copy_direct_prg_template

build_external_return_pair_prg_content_or_fail:
    lda #<external_return_pair_prg_template
    sta const_ptr
    lda #>external_return_pair_prg_template
    sta const_ptr+1
    lda #<(external_return_pair_prg_template_end - external_return_pair_prg_template)
    sta current_bit_lo
    lda #>(external_return_pair_prg_template_end - external_return_pair_prg_template)
    sta current_bit_hi
    jmp copy_direct_prg_template

build_external_store_prg_content_or_fail:
    lda #<external_store_prg_template_prefix
    sta const_ptr
    lda #>external_store_prg_template_prefix
    sta const_ptr+1
    lda #<(external_store_prg_template_prefix_end - external_store_prg_template_prefix)
    sta current_bit_lo
    lda #>(external_store_prg_template_prefix_end - external_store_prg_template_prefix)
    sta current_bit_hi
    jsr copy_direct_prg_template
    lda linked_store_value
    jsr append_payload_byte
    lda #<external_store_prg_template_suffix
    sta const_ptr
    lda #>external_store_prg_template_suffix
    sta const_ptr+1
    lda #<(external_store_prg_template_suffix_end - external_store_prg_template_suffix)
    sta current_bit_lo
    lda #>(external_store_prg_template_suffix_end - external_store_prg_template_suffix)
    sta current_bit_hi
    jmp copy_direct_prg_template

build_transitive_external_store_prg_content_or_fail:
    lda #<transitive_external_store_prg_template_prefix
    sta const_ptr
    lda #>transitive_external_store_prg_template_prefix
    sta const_ptr+1
    lda #<(transitive_external_store_prg_template_prefix_end - transitive_external_store_prg_template_prefix)
    sta current_bit_lo
    lda #>(transitive_external_store_prg_template_prefix_end - transitive_external_store_prg_template_prefix)
    sta current_bit_hi
    jsr copy_direct_prg_template
    lda linked_store_value
    jsr append_payload_byte
    lda #<external_store_prg_template_suffix
    sta const_ptr
    lda #>external_store_prg_template_suffix
    sta const_ptr+1
    lda #<(external_store_prg_template_suffix_end - external_store_prg_template_suffix)
    sta current_bit_lo
    lda #>(external_store_prg_template_suffix_end - external_store_prg_template_suffix)
    sta current_bit_hi
    jmp copy_direct_prg_template

build_external_load_store_prg_content_or_fail:
    lda #<external_store_prg_template_prefix
    sta const_ptr
    lda #>external_store_prg_template_prefix
    sta const_ptr+1
    lda #<(external_store_prg_template_prefix_end - external_store_prg_template_prefix)
    sta current_bit_lo
    lda #>(external_store_prg_template_prefix_end - external_store_prg_template_prefix)
    sta current_bit_hi
    jsr copy_direct_prg_template
    lda linked_store_value
    jsr append_payload_byte
    lda #<external_load_store_prg_template_suffix
    sta const_ptr
    lda #>external_load_store_prg_template_suffix
    sta const_ptr+1
    lda #<(external_load_store_prg_template_suffix_end - external_load_store_prg_template_suffix)
    sta current_bit_lo
    lda #>(external_load_store_prg_template_suffix_end - external_load_store_prg_template_suffix)
    sta current_bit_hi
    jmp copy_direct_prg_template

build_transitive_external_load_store_prg_content_or_fail:
    lda #<transitive_external_store_prg_template_prefix
    sta const_ptr
    lda #>transitive_external_store_prg_template_prefix
    sta const_ptr+1
    lda #<(transitive_external_store_prg_template_prefix_end - transitive_external_store_prg_template_prefix)
    sta current_bit_lo
    lda #>(transitive_external_store_prg_template_prefix_end - transitive_external_store_prg_template_prefix)
    sta current_bit_hi
    jsr copy_direct_prg_template
    lda linked_store_value
    jsr append_payload_byte
    lda #<external_load_store_prg_template_suffix
    sta const_ptr
    lda #>external_load_store_prg_template_suffix
    sta const_ptr+1
    lda #<(external_load_store_prg_template_suffix_end - external_load_store_prg_template_suffix)
    sta current_bit_lo
    lda #>(external_load_store_prg_template_suffix_end - external_load_store_prg_template_suffix)
    sta current_bit_hi
    jmp copy_direct_prg_template

build_external_string_int_prg_content_or_fail:
    lda #<external_string_int_prg_template_prefix
    sta const_ptr
    lda #>external_string_int_prg_template_prefix
    sta const_ptr+1
    lda #<(external_string_int_prg_template_prefix_end - external_string_int_prg_template_prefix)
    sta current_bit_lo
    lda #>(external_string_int_prg_template_prefix_end - external_string_int_prg_template_prefix)
    sta current_bit_hi
    jsr copy_direct_prg_template
    lda linked_store_value
    jsr append_payload_byte
    lda #<external_string_int_prg_template_suffix
    sta const_ptr
    lda #>external_string_int_prg_template_suffix
    sta const_ptr+1
    lda #<(external_string_int_prg_template_suffix_end - external_string_int_prg_template_suffix)
    sta current_bit_lo
    lda #>(external_string_int_prg_template_suffix_end - external_string_int_prg_template_suffix)
    sta current_bit_hi
    jsr copy_direct_prg_template
    jmp append_external_print_string_to_prg

build_transitive_external_string_int_prg_content_or_fail:
    lda #<transitive_external_string_int_prg_template_prefix
    sta const_ptr
    lda #>transitive_external_string_int_prg_template_prefix
    sta const_ptr+1
    lda #<(transitive_external_string_int_prg_template_prefix_end - transitive_external_string_int_prg_template_prefix)
    sta current_bit_lo
    lda #>(transitive_external_string_int_prg_template_prefix_end - transitive_external_string_int_prg_template_prefix)
    sta current_bit_hi
    jsr copy_direct_prg_template
    lda linked_store_value
    jsr append_payload_byte
    lda #<transitive_external_string_int_prg_template_suffix
    sta const_ptr
    lda #>transitive_external_string_int_prg_template_suffix
    sta const_ptr+1
    lda #<(transitive_external_string_int_prg_template_suffix_end - transitive_external_string_int_prg_template_suffix)
    sta current_bit_lo
    lda #>(transitive_external_string_int_prg_template_suffix_end - transitive_external_string_int_prg_template_suffix)
    sta current_bit_hi
    jsr copy_direct_prg_template
    jmp append_external_print_string_to_prg

build_printmath_linked_string_int_prg_content_or_fail:
    lda #<direct_prg_template_printmath
    sta const_ptr
    lda #>direct_prg_template_printmath
    sta const_ptr+1
    lda #<(direct_prg_template_printmath_linked_int - direct_prg_template_printmath)
    sta current_bit_lo
    lda #>(direct_prg_template_printmath_linked_int - direct_prg_template_printmath)
    sta current_bit_hi
    jsr copy_direct_prg_template
    lda linked_store_value
    jsr append_payload_byte
    lda #<direct_prg_template_printmath_linked_int_end
    sta const_ptr
    lda #>direct_prg_template_printmath_linked_int_end
    sta const_ptr+1
    lda #<(direct_prg_template_printmath_linked_string - direct_prg_template_printmath_linked_int_end)
    sta current_bit_lo
    lda #>(direct_prg_template_printmath_linked_string - direct_prg_template_printmath_linked_int_end)
    sta current_bit_hi
    jsr copy_direct_prg_template
    jmp append_external_print_string_to_prg

build_real_print_int_prg_content_or_fail:
    lda #<real_print_int_prg_template
    sta const_ptr
    lda #>real_print_int_prg_template
    sta const_ptr+1
    lda #<(real_print_int_prg_template_end - real_print_int_prg_template)
    sta current_bit_lo
    lda #>(real_print_int_prg_template_end - real_print_int_prg_template)
    sta current_bit_hi
    jsr copy_direct_prg_template
    jsr append_linked_store_decimal_byte
    lda #$00
    jmp append_payload_byte

build_real_print_div_prg_content_or_fail:
    lda #<real_print_int_prg_template
    sta const_ptr
    lda #>real_print_int_prg_template
    sta const_ptr+1
    lda #<(real_print_int_prg_template_end - real_print_int_prg_template)
    sta current_bit_lo
    lda #>(real_print_int_prg_template_end - real_print_int_prg_template)
    sta current_bit_hi
    jsr copy_direct_prg_template
    jsr append_linked_div_decimal_byte
    lda #$00
    jmp append_payload_byte

build_runtime_literal_call_prg_content_or_fail:
    lda #$00
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    jsr build_runtime_literal_call_address_table_or_fail
    lda linked_literal_count
    cmp #$04
    bne build_runtime_literal_call_single_arg
    jsr append_runtime_sound_literal_call_prefix
    jmp build_runtime_literal_call_jsr_and_exit
build_runtime_literal_call_single_arg:
    lda linked_literal_count
    cmp #$03
    bne build_runtime_literal_call_not_sprite_pos
    jsr append_runtime_sprite_pos_literal_call_prefix
    jmp build_runtime_literal_call_jsr_and_exit
build_runtime_literal_call_not_sprite_pos:
    lda linked_literal_count
    cmp #$02
    bne build_runtime_literal_call_one_arg
    jsr runtime_literal_call_first_external_is_rt_sprite_data
    bcs build_runtime_literal_call_not_sprite_data
    jsr append_runtime_sprite_data_literal_call_prefix
    jmp build_runtime_literal_call_jsr_and_exit
build_runtime_literal_call_not_sprite_data:
    jsr runtime_literal_call_first_external_is_sprite_flag_helper
    bcs build_runtime_literal_call_not_sprite_flag
    jsr append_runtime_sprite_flag_literal_call_prefix
    jmp build_runtime_literal_call_jsr_and_exit
build_runtime_literal_call_not_sprite_flag:
    jsr append_runtime_sprite_color_literal_call_prefix
    jmp build_runtime_literal_call_jsr_and_exit
build_runtime_literal_call_one_arg:
    jsr append_runtime_single_literal_call_prefix
build_runtime_literal_call_jsr_and_exit:
    lda #$20
    jsr append_payload_byte
    ldx #$00
    jsr load_pending_target_offset_from_x
    lda current_bit_lo
    jsr append_payload_byte
    lda current_bit_hi
    jsr append_payload_byte
    lda #<runtime_literal_call_prg_exit_template
    sta const_ptr
    lda #>runtime_literal_call_prg_exit_template
    sta const_ptr+1
    lda #<(runtime_literal_call_prg_exit_template_end - runtime_literal_call_prg_exit_template)
    sta current_bit_lo
    lda #>(runtime_literal_call_prg_exit_template_end - runtime_literal_call_prg_exit_template)
    sta current_bit_hi
    jsr copy_direct_prg_template
    jmp append_object_code_external_modules_or_fail

append_runtime_single_literal_call_prefix:
    lda #$A9
    jsr append_payload_byte
    lda linked_literal_values
    jsr append_payload_byte
    rts

append_runtime_sound_literal_call_prefix:
    lda #$A9
    jsr append_payload_byte
    lda linked_literal_values+3
    jsr append_payload_byte
    lda #$85
    jsr append_payload_byte
    lda #$02
    jsr append_payload_byte
    lda #$A9
    jsr append_payload_byte
    lda linked_literal_values
    jsr append_payload_byte
    lda #$A2
    jsr append_payload_byte
    lda linked_literal_values+1
    jsr append_payload_byte
    lda #$A0
    jsr append_payload_byte
    lda linked_literal_values+2
    jmp append_payload_byte

append_runtime_sprite_data_literal_call_prefix:
    lda #$A9
    jsr append_payload_byte
    lda linked_literal_values
    jsr append_payload_byte
    lda #$A2
    jsr append_payload_byte
    lda linked_literal_values+1
    jsr append_payload_byte
    lda #$A0
    jsr append_payload_byte
    lda linked_literal_hi_values+1
    jmp append_payload_byte

append_runtime_sprite_pos_literal_call_prefix:
    lda #$A9
    jsr append_payload_byte
    lda linked_literal_values
    jsr append_payload_byte
    lda #$A2
    jsr append_payload_byte
    lda linked_literal_values+1
    jsr append_payload_byte
    lda #$A0
    jsr append_payload_byte
    lda linked_literal_values+2
    jsr append_payload_byte
    lda linked_literal_hi_values+1
    beq append_runtime_sprite_pos_literal_call_clc
    lda #$38
    jmp append_payload_byte
append_runtime_sprite_pos_literal_call_clc:
    lda #$18
    jmp append_payload_byte

append_runtime_sprite_color_literal_call_prefix:
    lda #$A2
    jsr append_payload_byte
    lda linked_literal_values
    jsr append_payload_byte
    lda #$A9
    jsr append_payload_byte
    lda linked_literal_values+1
    jmp append_payload_byte

append_runtime_sprite_flag_literal_call_prefix:
    lda #$A9
    jsr append_payload_byte
    lda linked_literal_values
    jsr append_payload_byte
    lda #$A0
    jsr append_payload_byte
    lda linked_literal_values+1
    jmp append_payload_byte

build_object_code_prg_content_or_fail:
    lda #$00
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    jsr reload_root_object_or_fail
    ldx entry_export_index
    jsr load_export_meta_window_from_x_or_fail
    jsr append_machine_code_record_current_object_or_fail
    rts

build_object_code_external_prg_content_or_fail:
    lda #$00
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    jsr build_object_code_address_table_or_fail
    jsr reload_root_object_or_fail
    jsr parse_exports_or_fail
    jsr find_export_index_from_module_name
    bcc build_object_code_external_have_root_export
    jmp build_object_code_prg_bad
build_object_code_external_have_root_export:
    stx entry_export_index
    jsr load_export_meta_window_from_x_or_fail
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
    lda export_meta_window+EXPORT_META_SIZE_HI
    beq build_object_code_address_table_size_ok
    jmp build_object_code_prg_bad
build_object_code_address_table_size_ok:
    clc
    lda linked_next_addr_lo
    adc export_meta_window+EXPORT_META_SIZE_LO
    sta linked_next_addr_lo
    lda linked_next_addr_hi
    adc #$00
    sta linked_next_addr_hi
    inc linked_object_index
    jmp build_object_code_address_table_loop
build_object_code_address_table_done:
    jsr restore_saved_module_name
    rts

build_runtime_literal_call_address_table_or_fail:
    lda linked_literal_count
    cmp #$04
    bne build_runtime_literal_call_address_table_single_arg
    lda #$1D
    sta linked_next_addr_lo
    lda #$10
    sta linked_next_addr_hi
    jmp build_object_code_address_table_with_current_next_or_fail
build_runtime_literal_call_address_table_single_arg:
    lda linked_literal_count
    cmp #$03
    bne build_runtime_literal_call_address_table_not_sprite_pos
    lda #$1A
    sta linked_next_addr_lo
    lda #$10
    sta linked_next_addr_hi
    jmp build_object_code_address_table_with_current_next_or_fail
build_runtime_literal_call_address_table_not_sprite_pos:
    lda linked_literal_count
    cmp #$02
    bne build_runtime_literal_call_address_table_one_arg
    jsr runtime_literal_call_first_external_is_rt_sprite_data
    bcs build_runtime_literal_call_address_table_not_sprite_data
    lda #$19
    sta linked_next_addr_lo
    lda #$10
    sta linked_next_addr_hi
    jmp build_object_code_address_table_with_current_next_or_fail
build_runtime_literal_call_address_table_not_sprite_data:
    lda #$17
    sta linked_next_addr_lo
    lda #$10
    sta linked_next_addr_hi
    jmp build_object_code_address_table_with_current_next_or_fail
build_runtime_literal_call_address_table_one_arg:
    lda #$15
    sta linked_next_addr_lo
    lda #$10
    sta linked_next_addr_hi
    jmp build_object_code_address_table_with_current_next_or_fail

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
    jsr find_machine_code_record_or_fail
    lda export_meta_window+EXPORT_META_OFFSET_HI
    bne build_object_code_prg_bad
    lda export_meta_window+EXPORT_META_SIZE_HI
    bne build_object_code_prg_bad
    clc
    lda export_meta_window+EXPORT_META_OFFSET_LO
    adc export_meta_window+EXPORT_META_SIZE_LO
    bcc build_object_code_prg_range_ok
    beq build_object_code_prg_range_ok
    jmp build_object_code_prg_bad
build_object_code_prg_range_ok:
    jsr skip_machine_code_bytes_to_export_offset_or_fail
    lda #$00
    sta linked_store_value
build_object_code_prg_loop:
    lda linked_store_value
    cmp export_meta_window+EXPORT_META_SIZE_LO
    beq build_object_code_prg_done
    jsr read_machine_code_byte_or_fail
    jsr find_reloc_patch_byte_for_current_offset
    bcs build_object_code_prg_unpatched_byte
    jmp build_object_code_prg_append_byte
build_object_code_prg_unpatched_byte:
    lda parse_word_temp_hi
build_object_code_prg_append_byte:
    jsr append_payload_byte
    inc linked_store_value
    beq build_object_code_prg_bad
    jmp build_object_code_prg_loop
build_object_code_prg_done:
    lda linked_store_value
    beq build_object_code_prg_bad
    rts
build_object_code_prg_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr

skip_machine_code_bytes_to_export_offset_or_fail:
    lda export_meta_window+EXPORT_META_OFFSET_LO
    sta current_bit_lo
skip_machine_code_bytes_to_export_offset_loop:
    lda current_bit_lo
    beq skip_machine_code_bytes_to_export_offset_done
    jsr read_machine_code_byte_or_fail
    dec current_bit_lo
    jmp skip_machine_code_bytes_to_export_offset_loop
skip_machine_code_bytes_to_export_offset_done:
    rts

read_machine_code_byte_or_fail:
    ldy #$00
    lda (scan_ptr),y
    beq read_machine_code_byte_bad
    cmp #10
    beq read_machine_code_byte_bad
    cmp #13
    beq read_machine_code_byte_bad
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
    jsr parse_decimal_byte_or_fail
    sta saved_state_lo
    cmp #$FF
    beq load_reloc_records_current_object_bad
    clc
    adc #$01
    bcs load_reloc_records_current_object_bad
    jsr reloc_offset_is_in_current_export
    bcs load_reloc_records_current_object_next
    jsr require_space_or_fail
    ldy #$00
    lda (scan_ptr),y
    cmp #'u'
    bne load_reloc_records_current_object_bad
    jsr advance_scan_ptr
    jsr parse_object_code_import_index_at_scan_ptr_or_fail
    sta linked_import_index
    lda scan_ptr
    sta linked_reloc_saved_scan_lo
    lda scan_ptr+1
    sta linked_reloc_saved_scan_hi
    lda linked_import_index
    jsr copy_loaded_import_index_to_pending_window_or_fail
    jsr find_pending_name_in_external_queue_or_fail
    jsr load_pending_meta_window_from_x_or_fail
    lda linked_reloc_saved_scan_lo
    sta scan_ptr
    lda linked_reloc_saved_scan_hi
    sta scan_ptr+1
    ldx linked_reloc_count
    cpx #EXTERNAL_MAX
    bcs load_reloc_records_current_object_bad
    lda saved_state_lo
    sta linked_reloc_offsets,x
    lda pending_meta_window+PENDING_META_OFFSET_LO
    sta linked_reloc_addr_los,x
    lda pending_meta_window+PENDING_META_OFFSET_HI
    sta linked_reloc_addr_his,x
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

reloc_offset_is_in_current_export:
    lda saved_state_lo
    cmp export_meta_window+EXPORT_META_OFFSET_LO
    bcc reloc_offset_is_in_current_export_no
    clc
    lda export_meta_window+EXPORT_META_OFFSET_LO
    adc export_meta_window+EXPORT_META_SIZE_LO
    sta parse_word_temp_hi
    bcc reloc_offset_is_in_current_export_low_end
    lda parse_word_temp_hi
    beq reloc_offset_is_in_current_export_yes
    jmp reloc_offset_is_in_current_export_no
reloc_offset_is_in_current_export_low_end:
    clc
    lda saved_state_lo
    adc #$01
    bcs reloc_offset_is_in_current_export_no
    cmp parse_word_temp_hi
    bcs reloc_offset_is_in_current_export_no
reloc_offset_is_in_current_export_yes:
    clc
    rts
reloc_offset_is_in_current_export_no:
    sec
    rts

find_reloc_patch_byte_for_current_offset:
    clc
    lda export_meta_window+EXPORT_META_OFFSET_LO
    adc linked_store_value
    sta current_bit_lo
    ldx #$00
find_reloc_patch_byte_for_current_offset_loop:
    cpx linked_reloc_count
    beq find_reloc_patch_byte_for_current_offset_not_found
    lda current_bit_lo
    cmp linked_reloc_offsets,x
    beq find_reloc_patch_byte_for_current_offset_lo
    clc
    lda linked_reloc_offsets,x
    adc #$01
    cmp current_bit_lo
    beq find_reloc_patch_byte_for_current_offset_hi
    inx
    jmp find_reloc_patch_byte_for_current_offset_loop
find_reloc_patch_byte_for_current_offset_lo:
    lda linked_reloc_addr_los,x
    clc
    rts
find_reloc_patch_byte_for_current_offset_hi:
    lda linked_reloc_addr_his,x
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
    rts
find_pending_name_in_external_queue_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr

direct_entry_body_is_object_code_external:
    ldx entry_export_index
    jsr set_body_ptr_from_x
    ldy #$00
    lda (body_ptr),y
    cmp #'u'
    bne direct_entry_body_is_object_code_external_fail
direct_entry_body_is_object_code_external_loop:
    lda (body_ptr),y
    cmp #'u'
    bne direct_entry_body_is_object_code_external_fail
    iny
    lda (body_ptr),y
    jsr object_code_import_index_from_a
    bcs direct_entry_body_is_object_code_external_fail
    iny
    lda (body_ptr),y
    cmp #'u'
    beq direct_entry_body_is_object_code_external_loop
    cmp #'M'
    bne direct_entry_body_is_object_code_external_fail
    iny
    lda (body_ptr),y
    bne direct_entry_body_is_object_code_external_fail
    clc
    rts
direct_entry_body_is_object_code_external_fail:
    sec
    rts

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

append_linked_store_decimal_byte:
    lda linked_store_value
    sta current_bit_lo
    lda #$00
    sta current_bit_hi
append_linked_store_decimal_hundreds_loop:
    lda current_bit_lo
    cmp #100
    bcc append_linked_store_decimal_hundreds_done
    sec
    sbc #100
    sta current_bit_lo
    inc current_bit_hi
    jmp append_linked_store_decimal_hundreds_loop
append_linked_store_decimal_hundreds_done:
    lda current_bit_hi
    beq append_linked_store_decimal_tens_prep
    clc
    adc #'0'
    jsr append_payload_byte
append_linked_store_decimal_tens_prep:
    lda #$00
    sta compare_char
append_linked_store_decimal_tens_loop:
    lda current_bit_lo
    cmp #10
    bcc append_linked_store_decimal_tens_done
    sec
    sbc #10
    sta current_bit_lo
    inc compare_char
    jmp append_linked_store_decimal_tens_loop
append_linked_store_decimal_tens_done:
    lda compare_char
    beq append_linked_store_decimal_ones
    clc
    adc #'0'
    jsr append_payload_byte
append_linked_store_decimal_ones:
    clc
    lda current_bit_lo
    adc #'0'
    jmp append_payload_byte

append_linked_div_decimal_byte:
    lda linked_store_value
    sta current_bit_lo
    lda #$00
    sta compare_char
append_linked_div_decimal_quotient_loop:
    lda current_bit_lo
    cmp linked_divisor_value
    bcc append_linked_div_decimal_quotient_done
    sec
    sbc linked_divisor_value
    sta current_bit_lo
    inc compare_char
    jmp append_linked_div_decimal_quotient_loop
append_linked_div_decimal_quotient_done:
    lda compare_char
    sta linked_store_value
    jsr append_linked_store_decimal_byte
    lda #'.'
    jsr append_payload_byte
    lda #$00
    sta current_bit_hi
    lda #10
    sta parse_word_temp_lo
append_linked_div_decimal_fraction_mul_loop:
    lda parse_word_temp_lo
    beq append_linked_div_decimal_fraction_mul_done
    clc
    lda current_bit_hi
    adc current_bit_lo
    sta current_bit_hi
    dec parse_word_temp_lo
    jmp append_linked_div_decimal_fraction_mul_loop
append_linked_div_decimal_fraction_mul_done:
    lda #$00
    sta compare_char
append_linked_div_decimal_fraction_loop:
    lda current_bit_hi
    cmp linked_divisor_value
    bcc append_linked_div_decimal_fraction_done
    sec
    sbc linked_divisor_value
    sta current_bit_hi
    inc compare_char
    jmp append_linked_div_decimal_fraction_loop
append_linked_div_decimal_fraction_done:
    clc
    lda compare_char
    adc #'0'
    jmp append_payload_byte

direct_entry_body_matches_const:
    ldx entry_export_index
    jsr set_body_ptr_from_x
    ldy #$00
direct_entry_body_matches_const_loop:
    lda (const_ptr),y
    cmp (body_ptr),y
    bne direct_entry_body_matches_const_fail
    lda (const_ptr),y
    beq direct_entry_body_matches_const_ok
    iny
    bne direct_entry_body_matches_const_loop
direct_entry_body_matches_const_fail:
    sec
    rts
direct_entry_body_matches_const_ok:
    clc
    rts

copy_direct_prg_template:
    lda #$00
    sta main_flags_lo
    sta main_flags_hi
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

direct_body_table_lo:
    .byte <direct_body_single_call
    .byte <direct_body_fanout
    .byte <direct_body_word_store
    .byte <direct_body_word_load_store
    .byte <direct_body_printmath
    .byte <direct_body_if_eq
    .byte <direct_body_if_lt
    .byte <direct_body_if_gt
    .byte <direct_body_if_ge
    .byte <direct_body_if_ne
    .byte <direct_body_if_le
    .byte <direct_body_if_else
    .byte <direct_body_nested_if
    .byte <direct_body_nested_else
    .byte <direct_body_nested_do_until_eq
    .byte <direct_body_do_if_until_eq
    .byte <direct_body_do_if_else_until_eq
    .byte <direct_body_if_do_until_eq
    .byte <direct_body_if_else_do_until_eq
    .byte <direct_body_if_local_call_do_until_eq
    .byte <direct_body_if_else_local_call_do_until_eq
    .byte <direct_body_nested_if_local_call
    .byte <direct_body_nested_else_local_call
    .byte <direct_body_nested_do_local_call
    .byte <direct_body_nested_do_if_else_local_call
    .byte <direct_body_if_local_call_nested_do_if_else
    .byte <direct_body_if_else_local_call_nested_do_if_else
    .byte <direct_body_nested_else_local_call_nested_do_if_else
    .byte <direct_body_if_else_local_call_chain_nested_do_if_else
    .byte <direct_body_nested_else_local_call_chain_nested_do_if_else
    .byte <direct_body_do_until_eq
    .byte <direct_body_do_until_lt
    .byte <direct_body_return
    .byte <direct_body_seeded_runtime
direct_body_table_hi:
    .byte >direct_body_single_call
    .byte >direct_body_fanout
    .byte >direct_body_word_store
    .byte >direct_body_word_load_store
    .byte >direct_body_printmath
    .byte >direct_body_if_eq
    .byte >direct_body_if_lt
    .byte >direct_body_if_gt
    .byte >direct_body_if_ge
    .byte >direct_body_if_ne
    .byte >direct_body_if_le
    .byte >direct_body_if_else
    .byte >direct_body_nested_if
    .byte >direct_body_nested_else
    .byte >direct_body_nested_do_until_eq
    .byte >direct_body_do_if_until_eq
    .byte >direct_body_do_if_else_until_eq
    .byte >direct_body_if_do_until_eq
    .byte >direct_body_if_else_do_until_eq
    .byte >direct_body_if_local_call_do_until_eq
    .byte >direct_body_if_else_local_call_do_until_eq
    .byte >direct_body_nested_if_local_call
    .byte >direct_body_nested_else_local_call
    .byte >direct_body_nested_do_local_call
    .byte >direct_body_nested_do_if_else_local_call
    .byte >direct_body_if_local_call_nested_do_if_else
    .byte >direct_body_if_else_local_call_nested_do_if_else
    .byte >direct_body_nested_else_local_call_nested_do_if_else
    .byte >direct_body_if_else_local_call_chain_nested_do_if_else
    .byte >direct_body_nested_else_local_call_chain_nested_do_if_else
    .byte >direct_body_do_until_eq
    .byte >direct_body_do_until_lt
    .byte >direct_body_return
    .byte >direct_body_seeded_runtime
direct_template_table_lo:
    .byte <direct_prg_template_single_call
    .byte <direct_prg_template_fanout
    .byte <direct_prg_template_word_store
    .byte <direct_prg_template_word_load_store
    .byte <direct_prg_template_printmath
    .byte <direct_prg_template_if_eq
    .byte <direct_prg_template_if_lt
    .byte <direct_prg_template_if_gt
    .byte <direct_prg_template_if_ge
    .byte <direct_prg_template_if_ne
    .byte <direct_prg_template_if_le
    .byte <direct_prg_template_if_else
    .byte <direct_prg_template_nested_if
    .byte <direct_prg_template_nested_else
    .byte <direct_prg_template_nested_do_until_eq
    .byte <direct_prg_template_do_if_until_eq
    .byte <direct_prg_template_do_if_else_until_eq
    .byte <direct_prg_template_if_do_until_eq
    .byte <direct_prg_template_if_else_do_until_eq
    .byte <direct_prg_template_if_local_call_do_until_eq
    .byte <direct_prg_template_if_else_local_call_do_until_eq
    .byte <direct_prg_template_nested_if_local_call
    .byte <direct_prg_template_nested_else_local_call
    .byte <direct_prg_template_nested_do_local_call
    .byte <direct_prg_template_nested_do_if_else_local_call
    .byte <direct_prg_template_if_local_call_nested_do_if_else
    .byte <direct_prg_template_if_else_local_call_nested_do_if_else
    .byte <direct_prg_template_nested_else_local_call_nested_do_if_else
    .byte <direct_prg_template_if_else_local_call_chain_nested_do_if_else
    .byte <direct_prg_template_nested_else_local_call_chain_nested_do_if_else
    .byte <direct_prg_template_do_until_eq
    .byte <direct_prg_template_do_until_lt
    .byte <direct_prg_template_seeded_runtime
    .byte <direct_prg_template_seeded_runtime
direct_template_table_hi:
    .byte >direct_prg_template_single_call
    .byte >direct_prg_template_fanout
    .byte >direct_prg_template_word_store
    .byte >direct_prg_template_word_load_store
    .byte >direct_prg_template_printmath
    .byte >direct_prg_template_if_eq
    .byte >direct_prg_template_if_lt
    .byte >direct_prg_template_if_gt
    .byte >direct_prg_template_if_ge
    .byte >direct_prg_template_if_ne
    .byte >direct_prg_template_if_le
    .byte >direct_prg_template_if_else
    .byte >direct_prg_template_nested_if
    .byte >direct_prg_template_nested_else
    .byte >direct_prg_template_nested_do_until_eq
    .byte >direct_prg_template_do_if_until_eq
    .byte >direct_prg_template_do_if_else_until_eq
    .byte >direct_prg_template_if_do_until_eq
    .byte >direct_prg_template_if_else_do_until_eq
    .byte >direct_prg_template_if_local_call_do_until_eq
    .byte >direct_prg_template_if_else_local_call_do_until_eq
    .byte >direct_prg_template_nested_if_local_call
    .byte >direct_prg_template_nested_else_local_call
    .byte >direct_prg_template_nested_do_local_call
    .byte >direct_prg_template_nested_do_if_else_local_call
    .byte >direct_prg_template_if_local_call_nested_do_if_else
    .byte >direct_prg_template_if_else_local_call_nested_do_if_else
    .byte >direct_prg_template_nested_else_local_call_nested_do_if_else
    .byte >direct_prg_template_if_else_local_call_chain_nested_do_if_else
    .byte >direct_prg_template_nested_else_local_call_chain_nested_do_if_else
    .byte >direct_prg_template_do_until_eq
    .byte >direct_prg_template_do_until_lt
    .byte >direct_prg_template_seeded_runtime
    .byte >direct_prg_template_seeded_runtime
direct_template_len_lo:
    .byte <(direct_prg_template_single_call_end - direct_prg_template_single_call)
    .byte <(direct_prg_template_fanout_end - direct_prg_template_fanout)
    .byte <(direct_prg_template_word_store_end - direct_prg_template_word_store)
    .byte <(direct_prg_template_word_load_store_end - direct_prg_template_word_load_store)
    .byte <(direct_prg_template_printmath_end - direct_prg_template_printmath)
    .byte <(direct_prg_template_if_eq_end - direct_prg_template_if_eq)
    .byte <(direct_prg_template_if_lt_end - direct_prg_template_if_lt)
    .byte <(direct_prg_template_if_gt_end - direct_prg_template_if_gt)
    .byte <(direct_prg_template_if_ge_end - direct_prg_template_if_ge)
    .byte <(direct_prg_template_if_ne_end - direct_prg_template_if_ne)
    .byte <(direct_prg_template_if_le_end - direct_prg_template_if_le)
    .byte <(direct_prg_template_if_else_end - direct_prg_template_if_else)
    .byte <(direct_prg_template_nested_if_end - direct_prg_template_nested_if)
    .byte <(direct_prg_template_nested_else_end - direct_prg_template_nested_else)
    .byte <(direct_prg_template_nested_do_until_eq_end - direct_prg_template_nested_do_until_eq)
    .byte <(direct_prg_template_do_if_until_eq_end - direct_prg_template_do_if_until_eq)
    .byte <(direct_prg_template_do_if_else_until_eq_end - direct_prg_template_do_if_else_until_eq)
    .byte <(direct_prg_template_if_do_until_eq_end - direct_prg_template_if_do_until_eq)
    .byte <(direct_prg_template_if_else_do_until_eq_end - direct_prg_template_if_else_do_until_eq)
    .byte <(direct_prg_template_if_local_call_do_until_eq_end - direct_prg_template_if_local_call_do_until_eq)
    .byte <(direct_prg_template_if_else_local_call_do_until_eq_end - direct_prg_template_if_else_local_call_do_until_eq)
    .byte <(direct_prg_template_nested_if_local_call_end - direct_prg_template_nested_if_local_call)
    .byte <(direct_prg_template_nested_else_local_call_end - direct_prg_template_nested_else_local_call)
    .byte <(direct_prg_template_nested_do_local_call_end - direct_prg_template_nested_do_local_call)
    .byte <(direct_prg_template_nested_do_if_else_local_call_end - direct_prg_template_nested_do_if_else_local_call)
    .byte <(direct_prg_template_if_local_call_nested_do_if_else_end - direct_prg_template_if_local_call_nested_do_if_else)
    .byte <(direct_prg_template_if_else_local_call_nested_do_if_else_end - direct_prg_template_if_else_local_call_nested_do_if_else)
    .byte <(direct_prg_template_nested_else_local_call_nested_do_if_else_end - direct_prg_template_nested_else_local_call_nested_do_if_else)
    .byte <(direct_prg_template_if_else_local_call_chain_nested_do_if_else_end - direct_prg_template_if_else_local_call_chain_nested_do_if_else)
    .byte <(direct_prg_template_nested_else_local_call_chain_nested_do_if_else_end - direct_prg_template_nested_else_local_call_chain_nested_do_if_else)
    .byte <(direct_prg_template_do_until_eq_end - direct_prg_template_do_until_eq)
    .byte <(direct_prg_template_do_until_lt_end - direct_prg_template_do_until_lt)
    .byte <(direct_prg_template_seeded_runtime_end - direct_prg_template_seeded_runtime)
    .byte <(direct_prg_template_seeded_runtime_end - direct_prg_template_seeded_runtime)
direct_template_len_hi:
    .byte >(direct_prg_template_single_call_end - direct_prg_template_single_call)
    .byte >(direct_prg_template_fanout_end - direct_prg_template_fanout)
    .byte >(direct_prg_template_word_store_end - direct_prg_template_word_store)
    .byte >(direct_prg_template_word_load_store_end - direct_prg_template_word_load_store)
    .byte >(direct_prg_template_printmath_end - direct_prg_template_printmath)
    .byte >(direct_prg_template_if_eq_end - direct_prg_template_if_eq)
    .byte >(direct_prg_template_if_lt_end - direct_prg_template_if_lt)
    .byte >(direct_prg_template_if_gt_end - direct_prg_template_if_gt)
    .byte >(direct_prg_template_if_ge_end - direct_prg_template_if_ge)
    .byte >(direct_prg_template_if_ne_end - direct_prg_template_if_ne)
    .byte >(direct_prg_template_if_le_end - direct_prg_template_if_le)
    .byte >(direct_prg_template_if_else_end - direct_prg_template_if_else)
    .byte >(direct_prg_template_nested_if_end - direct_prg_template_nested_if)
    .byte >(direct_prg_template_nested_else_end - direct_prg_template_nested_else)
    .byte >(direct_prg_template_nested_do_until_eq_end - direct_prg_template_nested_do_until_eq)
    .byte >(direct_prg_template_do_if_until_eq_end - direct_prg_template_do_if_until_eq)
    .byte >(direct_prg_template_do_if_else_until_eq_end - direct_prg_template_do_if_else_until_eq)
    .byte >(direct_prg_template_if_do_until_eq_end - direct_prg_template_if_do_until_eq)
    .byte >(direct_prg_template_if_else_do_until_eq_end - direct_prg_template_if_else_do_until_eq)
    .byte >(direct_prg_template_if_local_call_do_until_eq_end - direct_prg_template_if_local_call_do_until_eq)
    .byte >(direct_prg_template_if_else_local_call_do_until_eq_end - direct_prg_template_if_else_local_call_do_until_eq)
    .byte >(direct_prg_template_nested_if_local_call_end - direct_prg_template_nested_if_local_call)
    .byte >(direct_prg_template_nested_else_local_call_end - direct_prg_template_nested_else_local_call)
    .byte >(direct_prg_template_nested_do_local_call_end - direct_prg_template_nested_do_local_call)
    .byte >(direct_prg_template_nested_do_if_else_local_call_end - direct_prg_template_nested_do_if_else_local_call)
    .byte >(direct_prg_template_if_local_call_nested_do_if_else_end - direct_prg_template_if_local_call_nested_do_if_else)
    .byte >(direct_prg_template_if_else_local_call_nested_do_if_else_end - direct_prg_template_if_else_local_call_nested_do_if_else)
    .byte >(direct_prg_template_nested_else_local_call_nested_do_if_else_end - direct_prg_template_nested_else_local_call_nested_do_if_else)
    .byte >(direct_prg_template_if_else_local_call_chain_nested_do_if_else_end - direct_prg_template_if_else_local_call_chain_nested_do_if_else)
    .byte >(direct_prg_template_nested_else_local_call_chain_nested_do_if_else_end - direct_prg_template_nested_else_local_call_chain_nested_do_if_else)
    .byte >(direct_prg_template_do_until_eq_end - direct_prg_template_do_until_eq)
    .byte >(direct_prg_template_do_until_lt_end - direct_prg_template_do_until_lt)
    .byte >(direct_prg_template_seeded_runtime_end - direct_prg_template_seeded_runtime)
    .byte >(direct_prg_template_seeded_runtime_end - direct_prg_template_seeded_runtime)

direct_body_single_call:
    .asciiz "c0r"
direct_body_fanout:
    .asciiz "c0c1r"
direct_body_word_store:
    .asciiz "p0S0r"
direct_body_word_load_store:
    .asciiz "p0S0L0S1r"
direct_body_printmath:
    .asciiz "e0u0j0i1r"
direct_body_if_eq:
    .asciiz "p0S0L0p1qhp2S1vr"
direct_body_if_lt:
    .asciiz "p0S0p1S1L0L1lhp2S1vr"
direct_body_if_gt:
    .asciiz "p0S0p1S1L0L1ghp2S1vr"
direct_body_if_ge:
    .asciiz "p0S0p1S1L0L1lp2qhp3S1vr"
direct_body_if_ne:
    .asciiz "p0S0p1S1L0L1nhp2S1vr"
direct_body_if_le:
    .asciiz "p0S0p1S1L0L1gp2qhp3S1vr"
direct_body_if_else:
    .asciiz "p0S0L0p1qhp2S1wp3S1vr"
direct_body_nested_if:
    .asciiz "p0S0p1S1L0L1lhL1p2ghp3S2vvr"
direct_body_nested_else:
    .asciiz "p0S0p1S1L0L1lhL1p2ghp3S2wp4S2vvr"
direct_body_nested_do_until_eq:
    .asciiz "p0S0p1S1dp2S0dp3S1L1p4qtoL0p5qtor"
direct_body_do_if_until_eq:
    .asciiz "p0S0p1S1dp2S0L0p3qhp4S1vL1p5qtor"
direct_body_do_if_else_until_eq:
    .asciiz "p0S0p1S1dp2S0L0p3qhp4S1wp5S1vL1p6qtor"
direct_body_if_do_until_eq:
    .asciiz "p0S0p1S1L0p2qhdp3S1L1p4qtovr"
direct_body_if_else_do_until_eq:
    .asciiz "p0S0p1S1L0p2qhdp3S1L1p4qtowdp5S1L1p6qtovr"
direct_body_if_local_call_do_until_eq:
    .asciiz "p2S0p3S1L0p4qhc0vr"
direct_body_if_else_local_call_do_until_eq:
    .asciiz "p2S0p3S1L0p4qhp5S1wc0vr"
direct_body_nested_if_local_call:
    .asciiz "p1S0p2S1L0p3qhL1p4qhc0vvr"
direct_body_nested_else_local_call:
    .asciiz "p1S0p2S1L0p3qhL1p4qhp5S1wc0vvr"
direct_body_nested_do_local_call:
    .asciiz "p1S0p2S1dp3S0dc0L1p4qtoL0p5qtor"
direct_body_nested_do_if_else_local_call:
    .asciiz "p1S0p2S1dp3S0dL0p4qhp5S1wc0vL1p6qtoL0p7qtor"
direct_body_if_local_call_nested_do_if_else:
    .asciiz "p4S0p5S1L0p6qhc0vr"
direct_body_if_else_local_call_nested_do_if_else:
    .asciiz "p4S0p5S1L0p6qhp7S1wc0vr"
direct_body_nested_else_local_call_nested_do_if_else:
    .asciiz "p4S0p5S1L0p6qhL1p7qhp8S1wc0vvr"
direct_body_if_else_local_call_chain_nested_do_if_else:
    .asciiz "p4S0p5S1L0p6qhp7S1wc1vr"
direct_body_nested_else_local_call_chain_nested_do_if_else:
    .asciiz "p4S0p5S1L0p6qhL1p7qhp8S1wc1vvr"
direct_body_do_until_eq:
    .asciiz "p0S0dp1S0L0p2qtor"
direct_body_do_until_lt:
    .asciiz "p0S0p1S1dp2S0L0L1ltor"
direct_body_return:
    .asciiz "r"
direct_body_seeded_runtime:
    .asciiz "e0u0p0p1ayp2p3gzr"
direct_body_runtime_literal_call:
    .asciiz "p0u0r"
direct_body_runtime_sprite_data_literal_call:
    .asciiz "p0p1u0r"
direct_body_runtime_sprite_pos_literal_call:
    .asciiz "p0p1p2u0r"
direct_body_runtime_sound_literal_call:
    .asciiz "p0p1p2p3u0r"
runtime_name_rt_sound:
    .asciiz "rt_sound"
runtime_name_rt_sprite_data:
    .asciiz "rt_sprite_data"
runtime_name_rt_sprite_pos:
    .asciiz "rt_sprite_pos"
runtime_name_rt_sprite_color:
    .asciiz "rt_sprite_color"
runtime_name_rt_sprite_ptr:
    .asciiz "rt_sprite_ptr"
runtime_name_rt_sprite_mc:
    .asciiz "rt_sprite_mc"
runtime_name_rt_sprite_xexp:
    .asciiz "rt_sprite_xexp"
runtime_name_rt_sprite_yexp:
    .asciiz "rt_sprite_yexp"
runtime_name_rt_sprite_prio:
    .asciiz "rt_sprite_prio"
direct_body_real_print_int:
    .asciiz "p1u0T0S0L0U0p2u1r"
direct_body_real_print_div:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1T2S2L2U2p4u2r"
direct_body_object_code:
    .asciiz "M"
direct_body_object_code_external:
    .asciiz "u0M"
linked_body_print_e:
    .asciiz "e0r"
linked_body_external_call:
    .asciiz "u0r"
linked_body_return:
    .asciiz "r"
linked_body_external_return_pair:
    .asciiz "u0u1r"
linked_body_word_store:
    .asciiz "p0S0r"
linked_body_word_load_store:
    .asciiz "p0S0L0S1r"
linked_body_string_int:
    .asciiz "s0i0r"
linked_body_rt_i_to_f:
    .asciiz "Wr"
linked_body_rt_f_div:
    .asciiz "Vr"
linked_body_rt_print_f:
    .asciiz "Yr"

direct_prg_template_single_call:
    .byte $00,$10,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C
    .byte $0F,$CF,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .byte $00,$00,$48,$45,$20,$10,$49,$18,$10
direct_prg_template_single_call_end:

direct_prg_template_fanout:
    .byte $00,$10,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C
    .byte $0F,$CF,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    .byte $00,$00,$48,$45,$20,$10,$48,$45,$20,$10,$45,$21,$10,$49,$18,$10
direct_prg_template_fanout_end:

direct_prg_template_word_store:
    .byte $00,$10,$A9,$07,$A2,$00,$8D,$22,$10,$8E,$23,$10,$8D,$D1,$03,$8E
    .byte $D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C
    .byte $0F,$CF,$00,$00,$00,$00
direct_prg_template_word_store_end:

direct_prg_template_word_load_store:
    .byte $00,$10,$A9,$07,$A2,$00,$8D,$2E,$10,$8E,$2F,$10,$AD,$2E,$10,$AE
    .byte $2F,$10,$8D,$30,$10,$8E,$31,$10,$8D,$D1,$03,$8E,$D2,$03,$A9,$A5
    .byte $8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF,$00,$00
    .byte $00,$00,$00,$00
direct_prg_template_word_load_store_end:

direct_prg_template_printmath:
    .byte $00,$10,$A9,$7B,$85,$02,$A9,$13,$85,$03,$A2,$02,$20,$03,$CF,$20
    .byte $06,$CF,$20,$50,$12,$A9,$36,$A2,$00,$8D,$77,$13,$8E,$78,$13,$A9
    .byte $79,$85,$02,$A9,$13,$85,$03,$A0,$00,$A2,$00,$AD,$78,$13,$C9,$27
    .byte $90,$1D,$D0,$07,$AD,$77,$13,$C9,$10,$90,$14,$38,$AD,$77,$13,$E9
    .byte $10,$8D,$77,$13,$AD,$78,$13,$E9,$27,$8D,$78,$13,$E8,$D0,$DC,$E0
    .byte $00,$D0,$04,$C0,$00,$F0,$0E,$8A,$18,$69,$30,$8D,$79,$13,$A2,$02
    .byte $20,$03,$CF,$A0,$01,$A2,$00,$AD,$78,$13,$C9,$03,$90,$1D,$D0,$07
    .byte $AD,$77,$13,$C9,$E8,$90,$14,$38,$AD,$77,$13,$E9,$E8,$8D,$77,$13
    .byte $AD,$78,$13,$E9,$03,$8D,$78,$13,$E8,$D0,$DC,$E0,$00,$D0,$04,$C0
    .byte $00,$F0,$0E,$8A,$18,$69,$30,$8D,$79,$13,$A2,$02,$20,$03,$CF,$A0
    .byte $01,$A2,$00,$AD,$78,$13,$C9,$00,$90,$1D,$D0,$07,$AD,$77,$13,$C9
    .byte $64,$90,$14,$38,$AD,$77,$13,$E9,$64,$8D,$77,$13,$AD,$78,$13,$E9
    .byte $00,$8D,$78,$13,$E8,$D0,$DC,$E0,$00,$D0,$04,$C0,$00,$F0,$0E,$8A
    .byte $18,$69,$30,$8D,$79,$13,$A2,$02,$20,$03,$CF,$A0,$01,$A2,$00,$AD
    .byte $78,$13,$C9,$00,$90,$1D,$D0,$07,$AD,$77,$13,$C9,$0A,$90,$14,$38
    .byte $AD,$77,$13,$E9,$0A,$8D,$77,$13,$AD,$78,$13,$E9,$00,$8D,$78,$13
    .byte $E8,$D0,$DC,$E0,$00,$D0,$04,$C0,$00,$F0,$0E,$8A,$18,$69,$30,$8D
    .byte $79,$13,$A2,$02,$20,$03,$CF,$A0,$01,$AD,$77,$13,$18,$69,$30,$8D
    .byte $79,$13,$A2,$02,$20,$03,$CF,$A9,$3B,$A2,$00,$8D,$77,$13,$8E,$78
    .byte $13,$A9,$79,$85,$02,$A9,$13,$85,$03,$A0,$00,$A2,$00,$AD,$78,$13
    .byte $C9,$27,$90,$1D,$D0,$07,$AD,$77,$13,$C9,$10,$90,$14,$38,$AD,$77
    .byte $13,$E9,$10,$8D,$77,$13,$AD,$78,$13,$E9,$27,$8D,$78,$13,$E8,$D0
    .byte $DC,$E0,$00,$D0,$04,$C0,$00,$F0,$0E,$8A,$18,$69,$30,$8D,$79,$13
    .byte $A2,$02,$20,$03,$CF,$A0,$01,$A2,$00,$AD,$78,$13,$C9,$03,$90,$1D
    .byte $D0,$07,$AD,$77,$13,$C9,$E8,$90,$14,$38,$AD,$77,$13,$E9,$E8,$8D
    .byte $77,$13,$AD,$78,$13,$E9,$03,$8D,$78,$13,$E8,$D0,$DC,$E0,$00,$D0
    .byte $04,$C0,$00,$F0,$0E,$8A,$18,$69,$30,$8D,$79,$13,$A2,$02,$20,$03
    .byte $CF,$A0,$01,$A2,$00,$AD,$78,$13,$C9,$00,$90,$1D,$D0,$07,$AD,$77
    .byte $13,$C9,$64,$90,$14,$38,$AD,$77,$13,$E9,$64,$8D,$77,$13,$AD,$78
    .byte $13,$E9,$00,$8D,$78,$13,$E8,$D0,$DC,$E0,$00,$D0,$04,$C0,$00,$F0
    .byte $0E,$8A,$18,$69,$30,$8D,$79,$13,$A2,$02,$20,$03,$CF,$A0,$01,$A2
    .byte $00,$AD,$78,$13,$C9,$00,$90,$1D,$D0,$07,$AD,$77,$13,$C9,$0A,$90
    .byte $14,$38,$AD,$77,$13,$E9,$0A,$8D,$77,$13,$AD,$78,$13,$E9,$00,$8D
    .byte $78,$13,$E8,$D0,$DC,$E0,$00,$D0,$04,$C0,$00,$F0,$0E,$8A,$18,$69
    .byte $30,$8D,$79,$13,$A2,$02,$20,$03,$CF,$A0,$01,$AD,$77,$13,$18,$69
    .byte $30,$8D,$79,$13,$A2,$02,$20,$03,$CF,$20,$06,$CF,$8D,$D1,$03,$8E
    .byte $D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C
    .byte $0F,$CF,$A9,$81,$85,$02,$A9,$13,$85,$03,$A2,$02,$20,$03,$CF,$A9
direct_prg_template_printmath_linked_int:
    .byte $07
direct_prg_template_printmath_linked_int_end:
    .byte $A2,$00,$8D,$77,$13,$8E,$78,$13,$A9,$79,$85,$02,$A9,$13,$85
    .byte $03,$A0,$00,$A2,$00,$AD,$78,$13,$C9,$27,$90,$1D,$D0,$07,$AD,$77
    .byte $13,$C9,$10,$90,$14,$38,$AD,$77,$13,$E9,$10,$8D,$77,$13,$AD,$78
    .byte $13,$E9,$27,$8D,$78,$13,$E8,$D0,$DC,$E0,$00,$D0,$04,$C0,$00,$F0
    .byte $0E,$8A,$18,$69,$30,$8D,$79,$13,$A2,$02,$20,$03,$CF,$A0,$01,$A2
    .byte $00,$AD,$78,$13,$C9,$03,$90,$1D,$D0,$07,$AD,$77,$13,$C9,$E8,$90
    .byte $14,$38,$AD,$77,$13,$E9,$E8,$8D,$77,$13,$AD,$78,$13,$E9,$03,$8D
    .byte $78,$13,$E8,$D0,$DC,$E0,$00,$D0,$04,$C0,$00,$F0,$0E,$8A,$18,$69
    .byte $30,$8D,$79,$13,$A2,$02,$20,$03,$CF,$A0,$01,$A2,$00,$AD,$78,$13
    .byte $C9,$00,$90,$1D,$D0,$07,$AD,$77,$13,$C9,$64,$90,$14,$38,$AD,$77
    .byte $13,$E9,$64,$8D,$77,$13,$AD,$78,$13,$E9,$00,$8D,$78,$13,$E8,$D0
    .byte $DC,$E0,$00,$D0,$04,$C0,$00,$F0,$0E,$8A,$18,$69,$30,$8D,$79,$13
    .byte $A2,$02,$20,$03,$CF,$A0,$01,$A2,$00,$AD,$78,$13,$C9,$00,$90,$1D
    .byte $D0,$07,$AD,$77,$13,$C9,$0A,$90,$14,$38,$AD,$77,$13,$E9,$0A,$8D
    .byte $77,$13,$AD,$78,$13,$E9,$00,$8D,$78,$13,$E8,$D0,$DC,$E0,$00,$D0
    .byte $04,$C0,$00,$F0,$0E,$8A,$18,$69,$30,$8D,$79,$13,$A2,$02,$20,$03
    .byte $CF,$A0,$01,$AD,$77,$13,$18,$69,$30,$8D,$79,$13,$A2,$02,$20,$03
    .byte $CF,$20,$06,$CF,$60,$00,$00,$00,$00,$00,$00,$00,$00,$48,$45,$4C
    .byte $4C,$4F,$00
direct_prg_template_printmath_linked_string:
    .byte $54,$4F,$4F,$4C,$00
direct_prg_template_printmath_end:

direct_prg_template_if_eq:
    .byte $00,$10,$A9,$07,$A2,$00,$8D,$49,$10,$8E,$4A,$10,$AD,$49,$10,$AE
    .byte $4A,$10,$8D,$47,$10,$8E,$48,$10,$A9,$07,$A2,$00,$EC,$48,$10,$D0
    .byte $05,$CD,$47,$10,$F0,$03,$4C,$31,$10,$A9,$01,$A2,$00,$8D,$4B,$10
    .byte $8E,$4C,$10,$8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00
    .byte $85,$02,$85,$03,$A2,$02,$4C,$0F,$CF,$00,$00,$00,$00,$00,$00
direct_prg_template_if_eq_end:

direct_prg_template_if_lt:
    .byte $00,$10,$A9,$01,$A2,$00,$8D,$65,$10,$8E,$66,$10,$A9,$02,$A2,$00
    .byte $8D,$67,$10,$8E,$68,$10,$AD,$65,$10,$AE,$66,$10,$8D,$63,$10,$8E
    .byte $64,$10,$AD,$67,$10,$AE,$68,$10,$EC,$64,$10,$90,$0D,$D0,$07,$CD
    .byte $63,$10,$90,$06,$F0,$04,$A9,$01,$D0,$02,$A9,$00,$A2,$00,$C9,$00
    .byte $D0,$03,$4C,$4D,$10,$A9,$03,$A2,$00,$8D,$67,$10,$8E,$68,$10,$8D
    .byte $D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03
    .byte $A2,$02,$4C,$0F,$CF,$00,$00,$00,$00,$00,$00
direct_prg_template_if_lt_end:

direct_prg_template_if_gt:
    .byte $00,$10,$A9,$02,$A2,$00,$8D,$65,$10,$8E,$66,$10,$A9,$01,$A2,$00
    .byte $8D,$67,$10,$8E,$68,$10,$AD,$65,$10,$AE,$66,$10,$8D,$63,$10,$8E
    .byte $64,$10,$AD,$67,$10,$AE,$68,$10,$EC,$64,$10,$90,$07,$D0,$0D,$CD
    .byte $63,$10,$90,$02,$F0,$04,$A9,$01,$D0,$02,$A9,$00,$A2,$00,$C9,$00
    .byte $D0,$03,$4C,$4D,$10,$A9,$03,$A2,$00,$8D,$67,$10,$8E,$68,$10,$8D
    .byte $D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03
    .byte $A2,$02,$4C,$0F,$CF,$00,$00,$00,$00,$00,$00
direct_prg_template_if_gt_end:

direct_prg_template_if_ge:
    .byte $00,$10,$A9,$02,$A2,$00,$8D,$75,$10,$8E,$76,$10,$A9,$01,$A2,$00
    .byte $8D,$77,$10,$8E,$78,$10,$AD,$75,$10,$AE,$76,$10,$8D,$73,$10,$8E
    .byte $74,$10,$AD,$77,$10,$AE,$78,$10,$EC,$74,$10,$90,$0D,$D0,$07,$CD
    .byte $73,$10,$90,$06,$F0,$04,$A9,$01,$D0,$02,$A9,$00,$A2,$00,$8D,$73
    .byte $10,$8E,$74,$10,$A9,$00,$A2,$00,$EC,$74,$10,$D0,$05,$CD,$73,$10
    .byte $F0,$03,$4C,$5D,$10,$A9,$03,$A2,$00,$8D,$77,$10,$8E,$78,$10,$8D
    .byte $D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03
    .byte $A2,$02,$4C,$0F,$CF,$00,$00,$00,$00,$00,$00
direct_prg_template_if_ge_end:

direct_prg_template_if_ne:
    .byte $00,$10,$A9,$02,$A2,$00,$8D,$61,$10,$8E,$62,$10,$A9,$01,$A2,$00
    .byte $8D,$63,$10,$8E,$64,$10,$AD,$61,$10,$AE,$62,$10,$8D,$5F,$10,$8E
    .byte $60,$10,$AD,$63,$10,$AE,$64,$10,$EC,$60,$10,$D0,$05,$CD,$5F,$10
    .byte $F0,$04,$A9,$01,$D0,$02,$A9,$00,$A2,$00,$C9,$00,$D0,$03,$4C,$49
    .byte $10,$A9,$03,$A2,$00,$8D,$63,$10,$8E,$64,$10,$8D,$D1,$03,$8E,$D2
    .byte $03,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F
    .byte $CF,$00,$00,$00,$00,$00,$00
direct_prg_template_if_ne_end:

direct_prg_template_if_le:
    .byte $00,$10,$A9,$01,$A2,$00,$8D,$75,$10,$8E,$76,$10,$A9,$01,$A2,$00
    .byte $8D,$77,$10,$8E,$78,$10,$AD,$75,$10,$AE,$76,$10,$8D,$73,$10,$8E
    .byte $74,$10,$AD,$77,$10,$AE,$78,$10,$EC,$74,$10,$90,$07,$D0,$0D,$CD
    .byte $73,$10,$90,$02,$F0,$04,$A9,$01,$D0,$02,$A9,$00,$A2,$00,$8D,$73
    .byte $10,$8E,$74,$10,$A9,$00,$A2,$00,$EC,$74,$10,$D0,$05,$CD,$73,$10
    .byte $F0,$03,$4C,$5D,$10,$A9,$03,$A2,$00,$8D,$77,$10,$8E,$78,$10,$8D
    .byte $D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03
    .byte $A2,$02,$4C,$0F,$CF,$00,$00,$00,$00,$00,$00
direct_prg_template_if_le_end:

direct_prg_template_if_else:
    .byte $00,$10,$A9,$07,$A2,$00,$8D,$56,$10,$8E,$57,$10,$AD,$56,$10,$AE
    .byte $57,$10,$8D,$54,$10,$8E,$55,$10,$A9,$08,$A2,$00,$EC,$55,$10,$D0
    .byte $05,$CD,$54,$10,$F0,$03,$4C,$34,$10,$A9,$01,$A2,$00,$8D,$58,$10
    .byte $8E,$59,$10,$4C,$3E,$10,$A9,$02,$A2,$00,$8D,$58,$10,$8E,$59,$10
    .byte $8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85
    .byte $03,$A2,$02,$4C,$0F,$CF,$00,$00,$00,$00,$00,$00
direct_prg_template_if_else_end:

direct_prg_template_nested_if:
    .byte $00,$10,$A9,$01,$A2,$00,$8D,$92,$10,$8E,$93,$10,$A9,$02,$A2,$00
    .byte $8D,$94,$10,$8E,$95,$10,$AD,$92,$10,$AE,$93,$10,$8D,$90,$10,$8E
    .byte $91,$10,$AD,$94,$10,$AE,$95,$10,$EC,$91,$10,$90,$0D,$D0,$07,$CD
    .byte $90,$10,$90,$06,$F0,$04,$A9,$01,$D0,$02,$A9,$00,$A2,$00,$C9,$00
    .byte $D0,$03,$4C,$7A,$10,$AD,$94,$10,$AE,$95,$10,$8D,$90,$10,$8E,$91
    .byte $10,$A9,$01,$A2,$00,$EC,$91,$10,$90,$07,$D0,$0D,$CD,$90,$10,$90
    .byte $02,$F0,$04,$A9,$01,$D0,$02,$A9,$00,$A2,$00,$C9,$00,$D0,$03,$4C
    .byte $7A,$10,$A9,$03,$A2,$00,$8D,$96,$10,$8E,$97,$10,$8D,$D1,$03,$8E
    .byte $D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C
    .byte $0F,$CF,$00,$00,$00,$00,$00,$00,$00,$00
direct_prg_template_nested_if_end:

direct_prg_template_nested_else:
    .byte $00,$10,$A9,$01,$A2,$00,$8D,$9F,$10,$8E,$A0,$10,$A9,$02,$A2,$00
    .byte $8D,$A1,$10,$8E,$A2,$10,$AD,$9F,$10,$AE,$A0,$10,$8D,$9D,$10,$8E
    .byte $9E,$10,$AD,$A1,$10,$AE,$A2,$10,$EC,$9E,$10,$90,$0D,$D0,$07,$CD
    .byte $9D,$10,$90,$06,$F0,$04,$A9,$01,$D0,$02,$A9,$00,$A2,$00,$C9,$00
    .byte $D0,$03,$4C,$87,$10,$AD,$A1,$10,$AE,$A2,$10,$8D,$9D,$10,$8E,$9E
    .byte $10,$A9,$02,$A2,$00,$EC,$9E,$10,$90,$07,$D0,$0D,$CD,$9D,$10,$90
    .byte $02,$F0,$04,$A9,$01,$D0,$02,$A9,$00,$A2,$00,$C9,$00,$D0,$03,$4C
    .byte $7D,$10,$A9,$03,$A2,$00,$8D,$A3,$10,$8E,$A4,$10,$4C,$87,$10,$A9
    .byte $04,$A2,$00,$8D,$A3,$10,$8E,$A4,$10,$8D,$D1,$03,$8E,$D2,$03,$A9
    .byte $A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF,$00
    .byte $00,$00,$00,$00,$00,$00,$00
direct_prg_template_nested_else_end:

direct_prg_template_nested_do_until_eq:
    .byte $00,$10,$A9,$00,$A2,$00,$8D,$7A,$10,$8E,$7B,$10,$A9,$00,$A2,$00
    .byte $8D,$7C,$10,$8E,$7D,$10,$A9,$01,$A2,$00,$8D,$7A,$10,$8E,$7B,$10
    .byte $A9,$02,$A2,$00,$8D,$7C,$10,$8E,$7D,$10,$AD,$7C,$10,$AE,$7D,$10
    .byte $8D,$78,$10,$8E,$79,$10,$A9,$02,$A2,$00,$EC,$79,$10,$D0,$05,$CD
    .byte $78,$10,$F0,$03,$4C,$1E,$10,$AD,$7A,$10,$AE,$7B,$10,$8D,$78,$10
    .byte $8E,$79,$10,$A9,$01,$A2,$00,$EC,$79,$10,$D0,$05,$CD,$78,$10,$F0
    .byte $03,$4C,$14,$10,$8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9
    .byte $00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF,$00,$00,$00,$00,$00,$00
direct_prg_template_nested_do_until_eq_end:

direct_prg_template_do_if_until_eq:
    .byte $00,$10,$A9,$00,$A2,$00,$8D,$7A,$10,$8E,$7B,$10,$A9,$00,$A2,$00
    .byte $8D,$7C,$10,$8E,$7D,$10,$A9,$01,$A2,$00,$8D,$7A,$10,$8E,$7B,$10
    .byte $AD,$7A,$10,$AE,$7B,$10,$8D,$78,$10,$8E,$79,$10,$A9,$01,$A2,$00
    .byte $EC,$79,$10,$D0,$05,$CD,$78,$10,$F0,$03,$4C,$45,$10,$A9,$02,$A2
    .byte $00,$8D,$7C,$10,$8E,$7D,$10,$AD,$7C,$10,$AE,$7D,$10,$8D,$78,$10
    .byte $8E,$79,$10,$A9,$02,$A2,$00,$EC,$79,$10,$D0,$05,$CD,$78,$10,$F0
    .byte $03,$4C,$14,$10,$8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9
    .byte $00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF,$00,$00,$00,$00,$00,$00
direct_prg_template_do_if_until_eq_end:

direct_prg_template_do_if_else_until_eq:
    .byte $00,$10,$A9,$00,$A2,$00,$8D,$87,$10,$8E,$88,$10,$A9,$00,$A2,$00
    .byte $8D,$89,$10,$8E,$8A,$10,$A9,$01,$A2,$00,$8D,$87,$10,$8E,$88,$10
    .byte $AD,$87,$10,$AE,$88,$10,$8D,$85,$10,$8E,$86,$10,$A9,$02,$A2,$00
    .byte $EC,$86,$10,$D0,$05,$CD,$85,$10,$F0,$03,$4C,$48,$10,$A9,$03,$A2
    .byte $00,$8D,$89,$10,$8E,$8A,$10,$4C,$52,$10,$A9,$04,$A2,$00,$8D,$89
    .byte $10,$8E,$8A,$10,$AD,$89,$10,$AE,$8A,$10,$8D,$85,$10,$8E,$86,$10
    .byte $A9,$04,$A2,$00,$EC,$86,$10,$D0,$05,$CD,$85,$10,$F0,$03,$4C,$14
    .byte $10,$8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02
    .byte $85,$03,$A2,$02,$4C,$0F,$CF,$00,$00,$00,$00,$00,$00
direct_prg_template_do_if_else_until_eq_end:

direct_prg_template_if_do_until_eq:
    .byte $00,$10,$A9,$01,$A2,$00,$8D,$70,$10,$8E,$71,$10,$A9,$00,$A2,$00
    .byte $8D,$72,$10,$8E,$73,$10,$AD,$70,$10,$AE,$71,$10,$8D,$6E,$00,$8E
    .byte $6F,$00,$A9,$01,$A2,$00,$EC,$6F,$00,$D0,$05,$CD,$6E,$00,$F0,$03
    .byte $4C,$58,$10,$A9,$02,$A2,$00,$8D,$72,$10,$8E,$73,$10,$AD,$72,$10
    .byte $AE,$73,$10,$8D,$6E,$00,$8E,$6F,$00,$A9,$02,$A2,$00,$EC,$6F,$00
    .byte $D0,$05,$CD,$6E,$00,$F0,$03,$4C,$31,$10,$8D,$D1,$03,$8E,$D2,$03
    .byte $A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF
    .byte $00,$00,$00,$00,$00,$00
direct_prg_template_if_do_until_eq_end:

direct_prg_template_if_else_do_until_eq:
    .byte $00,$10,$A9,$01,$A2,$00,$8D,$9A,$10,$8E,$9B,$10,$A9,$00,$A2,$00
    .byte $8D,$9C,$10,$8E,$9D,$10,$AD,$9A,$10,$AE,$9B,$10,$8D,$98,$10,$8E
    .byte $99,$10,$A9,$02,$A2,$00,$EC,$99,$10,$D0,$05,$CD,$98,$10,$F0,$03
    .byte $4C,$5B,$10,$A9,$03,$A2,$00,$8D,$9C,$10,$8E,$9D,$10,$AD,$9C,$10
    .byte $AE,$9D,$10,$8D,$98,$10,$8E,$99,$10,$A9,$03,$A2,$00,$EC,$99,$10
    .byte $D0,$05,$CD,$98,$10,$F0,$03,$4C,$31,$10,$4C,$82,$10,$A9,$04,$A2
    .byte $00,$8D,$9C,$10,$8E,$9D,$10,$AD,$9C,$10,$AE,$9D,$10,$8D,$98,$10
    .byte $8E,$99,$10,$A9,$04,$A2,$00,$EC,$99,$10,$D0,$05,$CD,$98,$10,$F0
    .byte $03,$4C,$5B,$10,$8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9
    .byte $00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF,$00,$00,$00,$00,$00,$00
direct_prg_template_if_else_do_until_eq_end:

direct_prg_template_if_local_call_do_until_eq:
    .byte $00,$10,$A9,$01,$A2,$00,$8D,$74,$10,$8E,$75,$10,$A9,$00,$A2,$00
    .byte $8D,$76,$10,$8E,$77,$10,$AD,$74,$10,$AE,$75,$10,$8D,$72,$00,$8E
    .byte $73,$00,$A9,$01,$A2,$00,$EC,$73,$00,$D0,$05,$CD,$72,$00,$F0,$03
    .byte $4C,$34,$10,$20,$4A,$10,$8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0
    .byte $03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF,$A9,$02,$A2,$00
    .byte $8D,$76,$10,$8E,$77,$10,$AD,$76,$10,$AE,$77,$10,$8D,$4A,$00,$8E
    .byte $4B,$00,$A9,$02,$A2,$00,$EC,$4B,$00,$D0,$05,$CD,$4A,$00,$F0,$03
    .byte $4C,$00,$10,$60,$00,$00,$00,$00,$00,$00
direct_prg_template_if_local_call_do_until_eq_end:

direct_prg_template_if_else_local_call_do_until_eq:
    .byte $00,$10,$A9,$01,$A2,$00,$8D,$81,$10,$8E,$82,$10,$A9,$00,$A2,$00
    .byte $8D,$83,$10,$8E,$84,$10,$AD,$81,$10,$AE,$82,$10,$8D,$7F,$00,$8E
    .byte $80,$00,$A9,$02,$A2,$00,$EC,$80,$00,$D0,$05,$CD,$7F,$00,$F0,$03
    .byte $4C,$3E,$10,$A9,$03,$A2,$00,$8D,$83,$10,$8E,$84,$10,$4C,$41,$10
    .byte $20,$57,$10,$8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00
    .byte $85,$02,$85,$03,$A2,$02,$4C,$0F,$CF,$A9,$04,$A2,$00,$8D,$83,$10
    .byte $8E,$84,$10,$AD,$83,$10,$AE,$84,$10,$8D,$57,$00,$8E,$58,$00,$A9
    .byte $04,$A2,$00,$EC,$58,$00,$D0,$05,$CD,$57,$00,$F0,$03,$4C,$00,$10
    .byte $60,$00,$00,$00,$00,$00,$00
direct_prg_template_if_else_local_call_do_until_eq_end:

direct_prg_template_nested_if_local_call:
    .byte $00,$10,$A9,$01,$A2,$00,$8D,$74,$10,$8E,$75,$10,$A9,$00,$A2,$00
    .byte $8D,$76,$10,$8E,$77,$10,$AD,$74,$10,$AE,$75,$10,$8D,$72,$00,$8E
    .byte $73,$00,$A9,$01,$A2,$00,$EC,$73,$00,$D0,$05,$CD,$72,$00,$F0,$03
    .byte $4C,$51,$10,$AD,$76,$10,$AE,$77,$10,$8D,$72,$00,$8E,$73,$00,$A9
    .byte $00,$A2,$00,$EC,$73,$00,$D0,$05,$CD,$72,$00,$F0,$03,$4C,$51,$10
    .byte $20,$67,$10,$8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00
    .byte $85,$02,$85,$03,$A2,$02,$4C,$0F,$CF,$A9,$05,$A2,$00,$8D,$76,$10
    .byte $8E,$77,$10,$60,$00,$00,$00,$00,$00,$00
direct_prg_template_nested_if_local_call_end:

direct_prg_template_nested_else_local_call:
    .byte $00,$10,$A9,$01,$A2,$00,$8D,$81,$10,$8E,$82,$10,$A9,$00,$A2,$00
    .byte $8D,$83,$10,$8E,$84,$10,$AD,$81,$10,$AE,$82,$10,$8D,$7F,$00,$8E
    .byte $80,$00,$A9,$01,$A2,$00,$EC,$80,$00,$D0,$05,$CD,$7F,$00,$F0,$03
    .byte $4C,$5E,$10,$AD,$83,$10,$AE,$84,$10,$8D,$7F,$00,$8E,$80,$00,$A9
    .byte $01,$A2,$00,$EC,$80,$00,$D0,$05,$CD,$7F,$00,$F0,$03,$4C,$5B,$10
    .byte $A9,$03,$A2,$00,$8D,$83,$10,$8E,$84,$10,$4C,$5E,$10,$20,$74,$10
    .byte $8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85
    .byte $03,$A2,$02,$4C,$0F,$CF,$A9,$06,$A2,$00,$8D,$83,$10,$8E,$84,$10
    .byte $60,$00,$00,$00,$00,$00,$00
direct_prg_template_nested_else_local_call_end:

direct_prg_template_nested_do_local_call:
    .byte $00,$10,$A9,$00,$A2,$00,$8D,$7E,$10,$8E,$7F,$10,$A9,$00,$A2,$00
    .byte $8D,$80,$10,$8E,$81,$10,$A9,$01,$A2,$00,$8D,$7E,$10,$8E,$7F,$10
    .byte $20,$71,$10,$AD,$80,$10,$AE,$81,$10,$8D,$71,$00,$8E,$72,$00,$A9
    .byte $07,$A2,$00,$EC,$72,$00,$D0,$05,$CD,$71,$00,$F0,$03,$4C,$1E,$10
    .byte $AD,$7E,$10,$AE,$7F,$10,$8D,$71,$00,$8E,$72,$00,$A9,$01,$A2,$00
    .byte $EC,$72,$00,$D0,$05,$CD,$71,$00,$F0,$03,$4C,$14,$10,$8D,$D1,$03
    .byte $8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02
    .byte $4C,$0F,$CF,$A9,$07,$A2,$00,$8D,$80,$10,$8E,$81,$10,$60,$00,$00
    .byte $00,$00,$00,$00
direct_prg_template_nested_do_local_call_end:

direct_prg_template_nested_do_if_else_local_call:
    .byte $00,$10,$A9,$00,$A2,$00,$8D,$A8,$10,$8E,$A9,$10,$A9,$00,$A2,$00
    .byte $8D,$AA,$10,$8E,$AB,$10,$A9,$01,$A2,$00,$8D,$A8,$10,$8E,$A9,$10
    .byte $AD,$A8,$10,$AE,$A9,$10,$8D,$A6,$00,$8E,$A7,$00,$A9,$02,$A2,$00
    .byte $EC,$A7,$00,$D0,$05,$CD,$A6,$00,$F0,$03,$4C,$48,$10,$A9,$03,$A2
    .byte $00,$8D,$AA,$10,$8E,$AB,$10,$4C,$4B,$10,$20,$9B,$10,$AD,$AA,$10
    .byte $AE,$AB,$10,$8D,$9B,$00,$8E,$9C,$00,$A9,$08,$A2,$00,$EC,$9C,$00
    .byte $D0,$05,$CD,$9B,$00,$F0,$03,$4C,$1E,$10,$AD,$A8,$10,$AE,$A9,$10
    .byte $8D,$9B,$00,$8E,$9C,$00,$A9,$01,$A2,$00,$EC,$9C,$00,$D0,$05,$CD
    .byte $9B,$00,$F0,$03,$4C,$14,$10,$8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D
    .byte $D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF,$A9,$08,$A2
    .byte $00,$8D,$AA,$10,$8E,$AB,$10,$60,$00,$00,$00,$00,$00,$00
direct_prg_template_nested_do_if_else_local_call_end:

direct_prg_template_if_local_call_nested_do_if_else:
    .byte $00,$10,$A9,$01,$A2,$00,$8D,$9E,$10,$8E,$9F,$10,$A9,$00,$A2,$00
    .byte $8D,$A0,$10,$8E,$A1,$10,$AD,$9E,$10,$AE,$9F,$10,$8D,$9C,$00,$8E
    .byte $9D,$00,$A9,$01,$A2,$00,$EC,$9D,$00,$D0,$05,$CD,$9C,$00,$F0,$03
    .byte $4C,$34,$10,$20,$4A,$10,$8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0
    .byte $03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF,$AD,$A0,$10,$AE
    .byte $A1,$10,$8D,$4A,$00,$8E,$4B,$00,$A9,$01,$A2,$00,$EC,$4B,$00,$D0
    .byte $05,$CD,$4A,$00,$F0,$03,$4C,$74,$10,$A9,$03,$A2,$00,$8D,$A0,$10
    .byte $8E,$A1,$10,$4C,$7E,$10,$A9,$09,$A2,$00,$8D,$A0,$10,$8E,$A1,$10
    .byte $AD,$A0,$10,$AE,$A1,$10,$8D,$4A,$00,$8E,$4B,$00,$A9,$09,$A2,$00
    .byte $EC,$4B,$00,$D0,$05,$CD,$4A,$00,$F0,$03,$4C,$4A,$10,$60,$00,$00
    .byte $00,$00,$00,$00
direct_prg_template_if_local_call_nested_do_if_else_end:

direct_prg_template_if_else_local_call_nested_do_if_else:
    .byte $00,$10,$A9,$01,$A2,$00,$8D,$AB,$10,$8E,$AC,$10,$A9,$00,$A2,$00
    .byte $8D,$AD,$10,$8E,$AE,$10,$AD,$AB,$10,$AE,$AC,$10,$8D,$A9,$00,$8E
    .byte $AA,$00,$A9,$02,$A2,$00,$EC,$AA,$00,$D0,$05,$CD,$A9,$00,$F0,$03
    .byte $4C,$3E,$10,$A9,$04,$A2,$00,$8D,$AD,$10,$8E,$AE,$10,$4C,$41,$10
    .byte $20,$57,$10,$8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00
    .byte $85,$02,$85,$03,$A2,$02,$4C,$0F,$CF,$AD,$AD,$10,$AE,$AE,$10,$8D
    .byte $57,$00,$8E,$58,$00,$A9,$01,$A2,$00,$EC,$58,$00,$D0,$05,$CD,$57
    .byte $00,$F0,$03,$4C,$81,$10,$A9,$03,$A2,$00,$8D,$AD,$10,$8E,$AE,$10
    .byte $4C,$8B,$10,$A9,$0A,$A2,$00,$8D,$AD,$10,$8E,$AE,$10,$AD,$AD,$10
    .byte $AE,$AE,$10,$8D,$57,$00,$8E,$58,$00,$A9,$0A,$A2,$00,$EC,$58,$00
    .byte $D0,$05,$CD,$57,$00,$F0,$03,$4C,$57,$10,$60,$00,$00,$00,$00,$00
    .byte $00
direct_prg_template_if_else_local_call_nested_do_if_else_end:

direct_prg_template_nested_else_local_call_nested_do_if_else:
    .byte $00,$10,$A9,$01,$A2,$00,$8D,$C8,$10,$8E,$C9,$10,$A9,$00,$A2,$00
    .byte $8D,$CA,$10,$8E,$CB,$10,$AD,$C8,$10,$AE,$C9,$10,$8D,$C6,$00,$8E
    .byte $C7,$00,$A9,$01,$A2,$00,$EC,$C7,$00,$D0,$05,$CD,$C6,$00,$F0,$03
    .byte $4C,$5E,$10,$AD,$CA,$10,$AE,$CB,$10,$8D,$00,$00,$8E,$01,$00,$A9
    .byte $01,$A2,$00,$EC,$01,$00,$D0,$05,$CD,$00,$00,$F0,$03,$4C,$5B,$10
    .byte $A9,$04,$A2,$00,$8D,$CA,$10,$8E,$CB,$10,$4C,$5E,$10,$20,$74,$10
    .byte $8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85
    .byte $03,$A2,$02,$4C,$0F,$CF,$AD,$CA,$10,$AE,$CB,$10,$8D,$74,$00,$8E
    .byte $75,$00,$A9,$01,$A2,$00,$EC,$75,$00,$D0,$05,$CD,$74,$00,$F0,$03
    .byte $4C,$9E,$10,$A9,$03,$A2,$00,$8D,$CA,$10,$8E,$CB,$10,$4C,$A8,$10
    .byte $A9,$0B,$A2,$00,$8D,$CA,$10,$8E,$CB,$10,$AD,$CA,$10,$AE,$CB,$10
    .byte $8D,$74,$00,$8E,$75,$00,$A9,$0B,$A2,$00,$EC,$75,$00,$D0,$05,$CD
    .byte $74,$00,$F0,$03,$4C,$74,$10,$60,$00,$00,$00,$00,$00,$00
direct_prg_template_nested_else_local_call_nested_do_if_else_end:

direct_prg_template_if_else_local_call_chain_nested_do_if_else:
    .byte $00,$10,$A9,$01,$A2,$00,$8D,$AF,$10,$8E,$B0,$10,$A9,$00,$A2,$00
    .byte $8D,$B1,$10,$8E,$B2,$10,$AD,$AF,$10,$AE,$B0,$10,$8D,$AD,$00,$8E
    .byte $AE,$00,$A9,$02,$A2,$00,$EC,$AE,$00,$D0,$05,$CD,$AD,$00,$F0,$03
    .byte $4C,$3E,$10,$A9,$04,$A2,$00,$8D,$B1,$10,$8E,$B2,$10,$4C,$41,$10
    .byte $20,$A9,$10,$8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00
    .byte $85,$02,$85,$03,$A2,$02,$4C,$0F,$CF,$AD,$B1,$10,$AE,$B2,$10,$8D
    .byte $A9,$00,$8E,$AA,$00,$A9,$01,$A2,$00,$EC,$AA,$00,$D0,$05,$CD,$A9
    .byte $00,$F0,$03,$4C,$81,$10,$A9,$03,$A2,$00,$8D,$B1,$10,$8E,$B2,$10
    .byte $4C,$8B,$10,$A9,$0C,$A2,$00,$8D,$B1,$10,$8E,$B2,$10,$AD,$B1,$10
    .byte $AE,$B2,$10,$8D,$57,$00,$8E,$58,$00,$A9,$0C,$A2,$00,$EC,$58,$00
    .byte $D0,$05,$CD,$57,$00,$F0,$03,$4C,$57,$10,$60,$20,$57,$10,$60,$00
    .byte $00,$00,$00,$00,$00
direct_prg_template_if_else_local_call_chain_nested_do_if_else_end:

direct_prg_template_nested_else_local_call_chain_nested_do_if_else:
    .byte $00,$10,$A9,$01,$A2,$00,$8D,$CC,$10,$8E,$CD,$10,$A9,$00,$A2,$00
    .byte $8D,$CE,$10,$8E,$CF,$10,$AD,$CC,$10,$AE,$CD,$10,$8D,$CA,$00,$8E
    .byte $CB,$00,$A9,$01,$A2,$00,$EC,$CB,$00,$D0,$05,$CD,$CA,$00,$F0,$03
    .byte $4C,$5E,$10,$AD,$CE,$10,$AE,$CF,$10,$8D,$00,$00,$8E,$01,$00,$A9
    .byte $01,$A2,$00,$EC,$01,$00,$D0,$05,$CD,$00,$00,$F0,$03,$4C,$5B,$10
    .byte $A9,$04,$A2,$00,$8D,$CE,$10,$8E,$CF,$10,$4C,$5E,$10,$20,$C6,$10
    .byte $8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85
    .byte $03,$A2,$02,$4C,$0F,$CF,$AD,$CE,$10,$AE,$CF,$10,$8D,$C6,$00,$8E
    .byte $C7,$00,$A9,$01,$A2,$00,$EC,$C7,$00,$D0,$05,$CD,$C6,$00,$F0,$03
    .byte $4C,$9E,$10,$A9,$03,$A2,$00,$8D,$CE,$10,$8E,$CF,$10,$4C,$A8,$10
    .byte $A9,$0D,$A2,$00,$8D,$CE,$10,$8E,$CF,$10,$AD,$CE,$10,$AE,$CF,$10
    .byte $8D,$74,$00,$8E,$75,$00,$A9,$0D,$A2,$00,$EC,$75,$00,$D0,$05,$CD
    .byte $74,$00,$F0,$03,$4C,$74,$10,$60,$20,$74,$10,$60,$00,$00,$00,$00
    .byte $00,$00
direct_prg_template_nested_else_local_call_chain_nested_do_if_else_end:

direct_prg_template_do_until_eq:
    .byte $00,$10,$A9,$00,$A2,$00,$8D,$49,$10,$8E,$4A,$10,$A9,$01,$A2,$00
    .byte $8D,$49,$10,$8E,$4A,$10,$AD,$49,$10,$AE,$4A,$10,$8D,$47,$10,$8E
    .byte $48,$10,$A9,$01,$A2,$00,$EC,$48,$10,$D0,$05,$CD,$47,$10,$F0,$03
    .byte $4C,$0A,$10,$8D,$D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00
    .byte $85,$02,$85,$03,$A2,$02,$4C,$0F,$CF,$00,$00,$00,$00
direct_prg_template_do_until_eq_end:

direct_prg_template_do_until_lt:
    .byte $00,$10,$A9,$01,$A2,$00,$8D,$65,$10,$8E,$66,$10,$A9,$02,$A2,$00
    .byte $8D,$67,$10,$8E,$68,$10,$A9,$01,$A2,$00,$8D,$65,$10,$8E,$66,$10
    .byte $AD,$65,$10,$AE,$66,$10,$8D,$63,$10,$8E,$64,$10,$AD,$67,$10,$AE
    .byte $68,$10,$EC,$64,$10,$90,$0D,$D0,$07,$CD,$63,$10,$90,$06,$F0,$04
    .byte $A9,$01,$D0,$02,$A9,$00,$A2,$00,$C9,$00,$D0,$03,$4C,$14,$10,$8D
    .byte $D1,$03,$8E,$D2,$03,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03
    .byte $A2,$02,$4C,$0F,$CF,$00,$00,$00,$00,$00,$00
direct_prg_template_do_until_lt_end:

direct_prg_template_seeded_runtime:
    .byte $00,$10,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C
    .byte $0F,$CF
direct_prg_template_seeded_runtime_end:

runtime_literal_call_prg_exit_template:
    .byte $A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF
runtime_literal_call_prg_exit_template_end:

real_print_int_prg_template:
    .byte $00,$10,$A9,$20,$85,$02,$A9,$10,$85,$03,$A2,$02,$20,$03,$CF,$20
    .byte $06,$CF,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C
    .byte $0F,$CF
real_print_int_prg_template_end:

external_print_prg_template:
    .byte $00,$10,$20,$13,$10,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03
    .byte $A2,$02,$4C,$0F,$CF,$A9,$24,$85,$02,$A9,$10,$85,$03,$A2,$02,$20
    .byte $03,$CF,$20,$06,$CF,$60
external_print_prg_template_end:

transitive_external_print_prg_template:
    .byte $00,$10,$20,$13,$10,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03
    .byte $A2,$02,$4C,$0F,$CF,$20,$17,$10,$60,$A9,$28,$85,$02,$A9,$10,$85
    .byte $03,$A2,$02,$20,$03,$CF,$20,$06,$CF,$60
transitive_external_print_prg_template_end:

external_return_prg_template:
    .byte $00,$10,$20,$13,$10,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03
    .byte $A2,$02,$4C,$0F,$CF,$60
external_return_prg_template_end:

transitive_external_return_prg_template:
    .byte $00,$10,$20,$13,$10,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03
    .byte $A2,$02,$4C,$0F,$CF,$20,$17,$10,$60,$60
transitive_external_return_prg_template_end:

external_return_pair_prg_template:
    .byte $00,$10,$20,$16,$10,$20,$17,$10,$A9,$A5,$8D,$D0,$03,$A9,$00,$85
    .byte $02,$85,$03,$A2,$02,$4C,$0F,$CF,$60,$60
external_return_pair_prg_template_end:

external_store_prg_template_prefix:
    .byte $00,$10,$20,$13,$10,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03
    .byte $A2,$02,$4C,$0F,$CF,$A9
external_store_prg_template_prefix_end:

external_store_prg_template_suffix:
    .byte $A2,$00,$8D,$D1,$03,$8E,$D2,$03,$60
external_store_prg_template_suffix_end:

transitive_external_store_prg_template_prefix:
    .byte $00,$10,$20,$13,$10,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03
    .byte $A2,$02,$4C,$0F,$CF,$20,$17,$10,$60,$A9
transitive_external_store_prg_template_prefix_end:

external_load_store_prg_template_suffix:
    .byte $A2,$00,$8D,$38,$10,$8E,$39,$10,$AD,$38,$10,$AE,$39,$10,$8D
    .byte $3A,$10,$8E,$3B,$10,$8D,$D1,$03,$8E,$D2,$03,$60
external_load_store_prg_template_suffix_end:

external_string_int_prg_template_prefix:
    .byte $00,$10,$20,$13,$10,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03
    .byte $A2,$02,$4C,$0F,$CF,$A9,$95,$85,$02,$A9,$10,$85,$03,$A2,$02
    .byte $20,$03,$CF,$A9
external_string_int_prg_template_prefix_end:

external_string_int_prg_template_suffix:
    .byte $8D,$91,$10,$A9,$00,$8D,$92,$10,$A2,$00,$AD,$91,$10,$C9,$64,$90
    .byte $09,$38,$E9,$64,$8D,$91,$10,$E8,$D0,$F0,$E0,$00,$F0,$0C,$8A
    .byte $18,$69,$30,$20,$7B,$10,$A9,$01,$8D,$92,$10,$A2,$00,$AD,$91
    .byte $10,$C9,$0A,$90,$09,$38,$E9,$0A,$8D,$91,$10,$E8,$D0,$F0,$E0
    .byte $00,$D0,$05,$AD,$92,$10,$F0,$07,$8A,$18,$69,$30,$20,$7B,$10
    .byte $AD,$91,$10,$18,$69,$30,$20,$7B,$10,$20,$06,$CF,$60,$8D,$93
    .byte $10,$A9,$00,$8D,$94,$10,$A9,$93,$85,$02,$A9,$10,$85,$03,$A2
    .byte $02,$20,$03,$CF,$60,$00,$00,$00,$00
external_string_int_prg_template_suffix_end:

transitive_external_string_int_prg_template_prefix:
    .byte $00,$10,$20,$13,$10,$A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03
    .byte $A2,$02,$4C,$0F,$CF,$20,$17,$10,$60,$A9,$99,$85,$02,$A9,$10
    .byte $85,$03,$A2,$02,$20,$03,$CF,$A9
transitive_external_string_int_prg_template_prefix_end:

transitive_external_string_int_prg_template_suffix:
    .byte $8D,$95,$10,$A9,$00,$8D,$96,$10,$A2,$00,$AD,$95,$10,$C9,$64,$90
    .byte $09,$38,$E9,$64,$8D,$95,$10,$E8,$D0,$F0,$E0,$00,$F0,$0C,$8A
    .byte $18,$69,$30,$20,$7F,$10,$A9,$01,$8D,$96,$10,$A2,$00,$AD,$95
    .byte $10,$C9,$0A,$90,$09,$38,$E9,$0A,$8D,$95,$10,$E8,$D0,$F0,$E0
    .byte $00,$D0,$05,$AD,$96,$10,$F0,$07,$8A,$18,$69,$30,$20,$7F,$10
    .byte $AD,$95,$10,$18,$69,$30,$20,$7F,$10,$20,$06,$CF,$60,$8D,$97
    .byte $10,$A9,$00,$8D,$98,$10,$A9,$97,$85,$02,$A9,$10,$85,$03,$A2
    .byte $02,$20,$03,$CF,$60,$00,$00,$00,$00
transitive_external_string_int_prg_template_suffix_end:
