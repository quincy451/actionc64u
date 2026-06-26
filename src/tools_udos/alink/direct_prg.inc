; Direct PRG builders used by the ALINK proof surface.
REAL_PRINT_INT_VAR_LO = $2A
REAL_PRINT_INT_VAR_HI = $10
REAL_PRINT_INT_EXT_LO = $2E
REAL_PRINT_INT_EXT_HI = $10
REAL_TO_INT_REAL_LO = $30
REAL_TO_INT_REAL_HI = $10
REAL_TO_INT_INT_LO = $34
REAL_TO_INT_INT_HI = $10
REAL_TO_INT_EXT_LO = $36
REAL_TO_INT_EXT_HI = $10
INPUT_REAL_PRINT_INT_VAR_LO = $2F
INPUT_REAL_PRINT_INT_VAR_HI = $10
INPUT_REAL_PRINT_INT_EXT_LO = $33
INPUT_REAL_PRINT_INT_EXT_HI = $10
INPUT_STORED_REAL_PRINT_INT_STORE_LO = $37
INPUT_STORED_REAL_PRINT_INT_STORE_HI = $10
INPUT_STORED_REAL_PRINT_INT_VAR_LO = $39
INPUT_STORED_REAL_PRINT_INT_VAR_HI = $10
INPUT_STORED_REAL_PRINT_INT_EXT_LO = $3D
INPUT_STORED_REAL_PRINT_INT_EXT_HI = $10
REAL_PRINT_BINARY_A_LO = $54
REAL_PRINT_BINARY_A_HI = $10
REAL_PRINT_BINARY_B_LO = $58
REAL_PRINT_BINARY_B_HI = $10
REAL_PRINT_BINARY_X_LO = $5C
REAL_PRINT_BINARY_X_HI = $10
REAL_PRINT_BINARY_EXT_LO = $60
REAL_PRINT_BINARY_EXT_HI = $10
REAL_PRINT_FABS_A_LO = $3D
REAL_PRINT_FABS_A_HI = $10
REAL_PRINT_FABS_X_LO = $41
REAL_PRINT_FABS_X_HI = $10
REAL_PRINT_FABS_EXT_LO = $45
REAL_PRINT_FABS_EXT_HI = $10
REAL_IF_GT_A_LO = $5C
REAL_IF_GT_A_HI = $10
REAL_IF_GT_B_LO = $60
REAL_IF_GT_B_HI = $10
REAL_IF_GT_Y_LO = $64
REAL_IF_GT_Y_HI = $10
REAL_IF_GT_EXT_LO = $66
REAL_IF_GT_EXT_HI = $10
REAL_IF_GT_ELSE_A_LO = $6A
REAL_IF_GT_ELSE_A_HI = $10
REAL_IF_GT_ELSE_B_LO = $6E
REAL_IF_GT_ELSE_B_HI = $10
REAL_IF_GT_ELSE_Y_LO = $72
REAL_IF_GT_ELSE_Y_HI = $10
REAL_IF_GT_ELSE_EXT_LO = $74
REAL_IF_GT_ELSE_EXT_HI = $10
REAL_IF_GT_NESTED_A_LO = $74
REAL_IF_GT_NESTED_A_HI = $10
REAL_IF_GT_NESTED_B_LO = $78
REAL_IF_GT_NESTED_B_HI = $10
REAL_IF_GT_NESTED_Y_LO = $7C
REAL_IF_GT_NESTED_Y_HI = $10
REAL_IF_GT_NESTED_EXT_LO = $7E
REAL_IF_GT_NESTED_EXT_HI = $10
REAL_DO_UNTIL_A_LO = $6A
REAL_DO_UNTIL_A_HI = $10
REAL_DO_UNTIL_B_LO = $6E
REAL_DO_UNTIL_B_HI = $10
REAL_DO_UNTIL_Y_LO = $72
REAL_DO_UNTIL_Y_HI = $10
REAL_DO_UNTIL_EXT_LO = $74
REAL_DO_UNTIL_EXT_HI = $10
REAL_DO_UNTIL_BINARY_A_LO = $86
REAL_DO_UNTIL_BINARY_A_HI = $10
REAL_DO_UNTIL_BINARY_B_LO = $8A
REAL_DO_UNTIL_BINARY_B_HI = $10
REAL_DO_UNTIL_BINARY_C_LO = $8E
REAL_DO_UNTIL_BINARY_C_HI = $10
REAL_DO_UNTIL_BINARY_Y_LO = $92
REAL_DO_UNTIL_BINARY_Y_HI = $10
REAL_DO_UNTIL_BINARY_EXT_LO = $94
REAL_DO_UNTIL_BINARY_EXT_HI = $10
REAL_WHILE_A_LO = $6D
REAL_WHILE_A_HI = $10
REAL_WHILE_B_LO = $71
REAL_WHILE_B_HI = $10
REAL_WHILE_Y_LO = $75
REAL_WHILE_Y_HI = $10
REAL_WHILE_EXT_LO = $77
REAL_WHILE_EXT_HI = $10
REAL_WHILE_BINARY_A_LO = $89
REAL_WHILE_BINARY_A_HI = $10
REAL_WHILE_BINARY_B_LO = $8D
REAL_WHILE_BINARY_B_HI = $10
REAL_WHILE_BINARY_C_LO = $91
REAL_WHILE_BINARY_C_HI = $10
REAL_WHILE_BINARY_Y_LO = $95
REAL_WHILE_BINARY_Y_HI = $10
REAL_WHILE_BINARY_EXT_LO = $97
REAL_WHILE_BINARY_EXT_HI = $10

select_prg_build_strategy_or_fail:
    lda #PRG_BUILD_DIRECT
    sta prg_build_strategy
    jsr find_linked_printmath_prg_case
    bcs select_prg_build_strategy_not_printmath
    rts
select_prg_build_strategy_not_printmath:
    jsr find_linked_real_print_int_prg_case
    bcs select_prg_build_strategy_not_real_print_int
    rts
select_prg_build_strategy_not_real_print_int:
    jsr find_linked_real_to_int_prg_case
    bcs select_prg_build_strategy_not_real_to_int
    rts
select_prg_build_strategy_not_real_to_int:
    jsr find_linked_input_real_print_int_prg_case
    bcs select_prg_build_strategy_not_input_real_print_int
    rts
select_prg_build_strategy_not_input_real_print_int:
    jsr find_linked_input_stored_real_print_int_prg_case
    bcs select_prg_build_strategy_not_input_stored_real_print_int
    rts
select_prg_build_strategy_not_input_stored_real_print_int:
    jsr find_linked_real_print_binary_prg_case
    bcs select_prg_build_strategy_not_real_print_binary
    rts
select_prg_build_strategy_not_real_print_binary:
    jsr find_linked_real_print_fabs_prg_case
    bcs select_prg_build_strategy_not_real_print_fabs
    rts
select_prg_build_strategy_not_real_print_fabs:
    jsr find_linked_real_if_gt_prg_case
    bcs select_prg_build_strategy_not_real_if_gt
    rts
select_prg_build_strategy_not_real_if_gt:
    jsr find_linked_real_do_until_prg_case
    bcs select_prg_build_strategy_not_real_do_until
    rts
select_prg_build_strategy_not_real_do_until:
    jsr find_linked_real_while_prg_case
    bcs select_prg_build_strategy_not_real_while
    rts
select_prg_build_strategy_not_real_while:
    jsr find_runtime_helper_condition_prg_case
    bcs select_prg_build_strategy_not_runtime_helper_condition
    rts
select_prg_build_strategy_not_runtime_helper_condition:
    jsr find_runtime_helper_sequence_prg_case
    bcs select_prg_build_strategy_not_runtime_helper_sequence
    rts
select_prg_build_strategy_not_runtime_helper_sequence:
    jsr find_object_code_prg_case
    bcs select_prg_build_strategy_not_object_code
    rts
select_prg_build_strategy_not_object_code:
    jmp require_direct_prg_body_supported_or_fail

build_prg_content_or_fail:
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
    cmp #PRG_BUILD_REAL_TO_INT
    bne build_prg_content_not_real_to_int
    jmp build_real_to_int_prg_content_or_fail
build_prg_content_not_real_to_int:
    lda prg_build_strategy
    cmp #PRG_BUILD_INPUT_REAL_PRINT_INT
    bne build_prg_content_not_input_real_print_int
    jmp build_input_real_print_int_prg_content_or_fail
build_prg_content_not_input_real_print_int:
    lda prg_build_strategy
    cmp #PRG_BUILD_INPUT_STORED_REAL_PRINT_INT
    bne build_prg_content_not_input_stored_real_print_int
    jmp build_input_stored_real_print_int_prg_content_or_fail
build_prg_content_not_input_stored_real_print_int:
    lda prg_build_strategy
    cmp #PRG_BUILD_REAL_PRINT_BINARY
    bne build_prg_content_not_real_print_binary
    jmp build_real_print_binary_prg_content_or_fail
build_prg_content_not_real_print_binary:
    lda prg_build_strategy
    cmp #PRG_BUILD_REAL_PRINT_FABS
    bne build_prg_content_not_real_print_fabs
    jmp build_real_print_fabs_prg_content_or_fail
build_prg_content_not_real_print_fabs:
    lda prg_build_strategy
    cmp #PRG_BUILD_REAL_IF_GT
    bne build_prg_content_not_real_if_gt
    jmp build_real_if_gt_prg_content_or_fail
build_prg_content_not_real_if_gt:
    lda prg_build_strategy
    cmp #PRG_BUILD_REAL_DO_UNTIL
    bne build_prg_content_not_real_do_until
    jmp build_real_do_until_prg_content_or_fail
build_prg_content_not_real_do_until:
    lda prg_build_strategy
    cmp #PRG_BUILD_REAL_WHILE
    bne build_prg_content_not_real_while
    jmp build_real_while_prg_content_or_fail
build_prg_content_not_real_while:
    lda prg_build_strategy
    cmp #PRG_BUILD_RUNTIME_HELPER_CONDITION
    bne build_prg_content_not_runtime_helper_condition
    jmp build_runtime_helper_condition_prg_content_or_fail
build_prg_content_not_runtime_helper_condition:
    lda prg_build_strategy
    cmp #PRG_BUILD_RUNTIME_HELPER_SEQUENCE
    bne build_prg_content_not_runtime_helper_sequence
    jmp build_runtime_helper_sequence_prg_content_or_fail
build_prg_content_not_runtime_helper_sequence:
    lda prg_build_strategy
    cmp #PRG_BUILD_OBJECT_CODE
    bne build_prg_content_not_object_code
    jmp build_object_code_prg_content_or_fail
build_prg_content_not_object_code:
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
    cmp #$04
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
    jsr loaded_external_print_body_is_M
    bcs find_linked_real_print_int_prg_case_unsupported
    ldx #$01
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
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

find_linked_real_to_int_prg_case:
    lda #<direct_body_real_to_int
    sta const_ptr
    lda #>direct_body_real_to_int
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcc find_linked_real_to_int_prg_case_body_ok
    sec
    rts
find_linked_real_to_int_prg_case_body_ok:
    lda external_count
    cmp #$02
    bcs find_linked_real_to_int_prg_case_have_externals
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_to_int_prg_case_have_externals:
    lda int_count
    cmp #$02
    bcs find_linked_real_to_int_prg_case_have_ints
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_to_int_prg_case_have_ints:
    jsr save_current_module_name
    ldx #$00
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
    bcs find_linked_real_to_int_prg_case_unsupported
    ldx #$01
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
    bcs find_linked_real_to_int_prg_case_unsupported
    ldx #$00
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    bne find_linked_real_to_int_prg_case_unsupported
    ldx #$01
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    sta linked_store_value
    lda int_value_window+1
    sta linked_store_value_hi
    jsr restore_saved_module_name
    lda #PRG_BUILD_REAL_TO_INT
    sta prg_build_strategy
    clc
    rts
find_linked_real_to_int_prg_case_unsupported:
    jsr restore_saved_module_name
    sec
    rts

find_linked_input_real_print_int_prg_case:
    lda #<direct_body_input_real_print_int
    sta const_ptr
    lda #>direct_body_input_real_print_int
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcc find_linked_input_real_print_int_prg_case_body_ok
    sec
    rts
find_linked_input_real_print_int_prg_case_body_ok:
    lda external_count
    cmp #$03
    bcs find_linked_input_real_print_int_prg_case_have_externals
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_input_real_print_int_prg_case_have_externals:
    lda int_count
    cmp #$04
    bcs find_linked_input_real_print_int_prg_case_have_ints
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_input_real_print_int_prg_case_have_ints:
    jsr runtime_helper_sequence_load_ints_or_fail
    lda #$00
    sta linked_runtime_arg_count
    sta linked_runtime_result_pending
    ldx #$00
    jsr runtime_helper_kind_for_external_index_x
    bcc :+
    sec
    rts
:
    sta linked_runtime_helper_kind
    lda #$00
    jsr runtime_helper_sequence_store_arg_from_a
    bcc :+
    sec
    rts
:
    jsr runtime_helper_sequence_validate_current_call
    bcc :+
    sec
    rts
:
    jsr save_current_module_name
    lda #$00
    sta linked_object_index
find_linked_input_real_print_int_prg_case_object_loop:
    ldx linked_object_index
    cpx #$03
    beq find_linked_input_real_print_int_prg_case_objects_ok
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_first_body_is_object_code
    bcs find_linked_input_real_print_int_prg_case_unsupported
    inc linked_object_index
    jmp find_linked_input_real_print_int_prg_case_object_loop
find_linked_input_real_print_int_prg_case_objects_ok:
    ldx #$02
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    bne find_linked_input_real_print_int_prg_case_unsupported
    lda int_value_window
    sta linked_store_value
    ldx #$03
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    bne find_linked_input_real_print_int_prg_case_unsupported
    lda int_value_window
    cmp #$01
    bne find_linked_input_real_print_int_prg_case_unsupported
    jsr restore_saved_module_name
    lda #PRG_BUILD_INPUT_REAL_PRINT_INT
    sta prg_build_strategy
    clc
    rts
find_linked_input_real_print_int_prg_case_unsupported:
    jsr restore_saved_module_name
    sec
    rts

find_linked_input_stored_real_print_int_prg_case:
    lda #<direct_body_input_stored_real_print_int
    sta const_ptr
    lda #>direct_body_input_stored_real_print_int
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcc find_linked_input_stored_real_print_int_prg_case_body_ok
    sec
    rts
find_linked_input_stored_real_print_int_prg_case_body_ok:
    lda external_count
    cmp #$03
    bcs find_linked_input_stored_real_print_int_prg_case_have_externals
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_input_stored_real_print_int_prg_case_have_externals:
    lda int_count
    cmp #$04
    bcs find_linked_input_stored_real_print_int_prg_case_have_ints
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_input_stored_real_print_int_prg_case_have_ints:
    jsr runtime_helper_sequence_load_ints_or_fail
    lda #$00
    sta linked_runtime_arg_count
    sta linked_runtime_result_pending
    ldx #$00
    jsr runtime_helper_kind_for_external_index_x
    bcc :+
    sec
    rts
:
    sta linked_runtime_helper_kind
    lda #$00
    jsr runtime_helper_sequence_store_arg_from_a
    bcc :+
    sec
    rts
:
    jsr runtime_helper_sequence_validate_current_call
    bcc :+
    sec
    rts
:
    jsr save_current_module_name
    lda #$00
    sta linked_object_index
find_linked_input_stored_real_print_int_prg_case_object_loop:
    ldx linked_object_index
    cpx #$03
    beq find_linked_input_stored_real_print_int_prg_case_objects_ok
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_first_body_is_object_code
    bcs find_linked_input_stored_real_print_int_prg_case_unsupported
    inc linked_object_index
    jmp find_linked_input_stored_real_print_int_prg_case_object_loop
find_linked_input_stored_real_print_int_prg_case_objects_ok:
    ldx #$02
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    bne find_linked_input_stored_real_print_int_prg_case_unsupported
    lda int_value_window
    sta linked_store_value
    ldx #$03
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    bne find_linked_input_stored_real_print_int_prg_case_unsupported
    lda int_value_window
    cmp #$01
    bne find_linked_input_stored_real_print_int_prg_case_unsupported
    jsr restore_saved_module_name
    lda #PRG_BUILD_INPUT_STORED_REAL_PRINT_INT
    sta prg_build_strategy
    clc
    rts
find_linked_input_stored_real_print_int_prg_case_unsupported:
    jsr restore_saved_module_name
    sec
    rts

find_linked_real_print_binary_prg_case:
    lda #<direct_body_real_print_binary
    sta const_ptr
    lda #>direct_body_real_print_binary
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcc find_linked_real_print_binary_prg_case_body_ok
    sec
    rts
find_linked_real_print_binary_prg_case_body_ok:
    lda external_count
    cmp #$03
    bcs find_linked_real_print_binary_prg_case_have_externals
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_print_binary_prg_case_have_externals:
    lda int_count
    cmp #$05
    bcs find_linked_real_print_binary_prg_case_have_ints
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_print_binary_prg_case_have_ints:
    jsr save_current_module_name
    ldx #$00
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
    bcs find_linked_real_print_binary_prg_case_unsupported
    ldx #$01
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
    bcs find_linked_real_print_binary_prg_case_unsupported
    ldx #$02
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
    bcs find_linked_real_print_binary_prg_case_unsupported
    ldx #$01
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    bne find_linked_real_print_binary_prg_case_unsupported
    lda int_value_window
    sta linked_store_value
    ldx #$03
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    bne find_linked_real_print_binary_prg_case_unsupported
    lda int_value_window
    beq find_linked_real_print_binary_prg_case_unsupported
    cmp #26
    bcs find_linked_real_print_binary_prg_case_unsupported
    sta linked_binary_rhs_value
    ldx #$04
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    bne find_linked_real_print_binary_prg_case_unsupported
    lda int_value_window
    cmp #$01
    bne find_linked_real_print_binary_prg_case_unsupported
    jsr restore_saved_module_name
    lda #PRG_BUILD_REAL_PRINT_BINARY
    sta prg_build_strategy
    clc
    rts
find_linked_real_print_binary_prg_case_unsupported:
    jsr restore_saved_module_name
    sec
    rts

find_linked_real_print_fabs_prg_case:
    lda #<direct_body_real_print_fabs
    sta const_ptr
    lda #>direct_body_real_print_fabs
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    lda #$00
    sta linked_unary_value_index
    lda #$01
    sta linked_unary_print_index
    jmp find_linked_real_print_fabs_prg_case_body_ok
:
    lda #<direct_body_real_print_unary_positive
    sta const_ptr
    lda #>direct_body_real_print_unary_positive
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    lda #$01
    sta linked_unary_value_index
    lda #$02
    sta linked_unary_print_index
    jmp find_linked_real_print_fabs_prg_case_body_ok
:
    sec
    rts
find_linked_real_print_fabs_prg_case_body_ok:
    lda external_count
    cmp #$03
    bcs find_linked_real_print_fabs_prg_case_have_externals
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_print_fabs_prg_case_have_externals:
    lda linked_unary_print_index
    clc
    adc #$01
    sta compare_char
    lda int_count
    cmp compare_char
    bcs find_linked_real_print_fabs_prg_case_have_ints
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_print_fabs_prg_case_have_ints:
    jsr save_current_module_name
    ldx #$00
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
    bcs find_linked_real_print_fabs_prg_case_unsupported
    ldx #$01
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
    bcs find_linked_real_print_fabs_prg_case_unsupported
    ldx #$02
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
    bcs find_linked_real_print_fabs_prg_case_unsupported
    ldx linked_unary_value_index
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    sta linked_store_value
    lda int_value_window+1
    sta linked_store_value_hi
    ldx linked_unary_print_index
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    bne find_linked_real_print_fabs_prg_case_unsupported
    lda int_value_window
    cmp #$01
    bne find_linked_real_print_fabs_prg_case_unsupported
    jsr restore_saved_module_name
    lda #PRG_BUILD_REAL_PRINT_FABS
    sta prg_build_strategy
    clc
    rts
find_linked_real_print_fabs_prg_case_unsupported:
    jsr restore_saved_module_name
    sec
    rts

find_linked_real_if_gt_prg_case:
    lda #$00
    sta linked_condition_has_else
    sta linked_condition_is_nested
    sta linked_condition_is_loop
    lda #'g'
    sta linked_condition_body_op
    lda #<direct_body_real_if_gt
    sta const_ptr
    lda #>direct_body_real_if_gt
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_if_gt_prg_case_body_ok
:
    lda #'l'
    sta linked_condition_body_op
    lda #<direct_body_real_if_lt
    sta const_ptr
    lda #>direct_body_real_if_lt
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_if_gt_prg_case_body_ok
:
    lda #'q'
    sta linked_condition_body_op
    lda #<direct_body_real_if_eq
    sta const_ptr
    lda #>direct_body_real_if_eq
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_if_gt_prg_case_body_ok
:
    lda #'n'
    sta linked_condition_body_op
    lda #<direct_body_real_if_ne
    sta const_ptr
    lda #>direct_body_real_if_ne
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_if_gt_prg_case_body_ok
:
    lda #$01
    sta linked_condition_has_else
    lda #'g'
    sta linked_condition_body_op
    lda #<direct_body_real_if_gt_else
    sta const_ptr
    lda #>direct_body_real_if_gt_else
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_if_gt_prg_case_body_ok
:
    lda #'l'
    sta linked_condition_body_op
    lda #<direct_body_real_if_lt_else
    sta const_ptr
    lda #>direct_body_real_if_lt_else
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_if_gt_prg_case_body_ok
:
    lda #'q'
    sta linked_condition_body_op
    lda #<direct_body_real_if_eq_else
    sta const_ptr
    lda #>direct_body_real_if_eq_else
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_if_gt_prg_case_body_ok
:
    lda #'n'
    sta linked_condition_body_op
    lda #<direct_body_real_if_ne_else
    sta const_ptr
    lda #>direct_body_real_if_ne_else
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_if_gt_prg_case_body_ok
:
    lda #$00
    sta linked_condition_has_else
    lda #$01
    sta linked_condition_is_nested
    lda #'g'
    sta linked_condition_body_op
    lda #<direct_body_real_nested_if_gt
    sta const_ptr
    lda #>direct_body_real_nested_if_gt
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_if_gt_prg_case_body_ok
:
    lda #'l'
    sta linked_condition_body_op
    lda #<direct_body_real_nested_if_lt
    sta const_ptr
    lda #>direct_body_real_nested_if_lt
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_if_gt_prg_case_body_ok
:
    lda #'q'
    sta linked_condition_body_op
    lda #<direct_body_real_nested_if_eq
    sta const_ptr
    lda #>direct_body_real_nested_if_eq
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_if_gt_prg_case_body_ok
:
    lda #'n'
    sta linked_condition_body_op
    lda #<direct_body_real_nested_if_ne
    sta const_ptr
    lda #>direct_body_real_nested_if_ne
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_if_gt_prg_case_body_ok
:
    sec
    rts
find_linked_real_if_gt_prg_case_body_ok:
    lda external_count
    cmp #$02
    bcs find_linked_real_if_gt_prg_case_have_externals
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_if_gt_prg_case_have_externals:
    lda linked_condition_has_else
    bne find_linked_real_if_gt_prg_case_need_seven_ints
    lda linked_condition_is_nested
    bne find_linked_real_if_gt_prg_case_need_seven_ints
    lda int_count
    cmp #$06
    bcs find_linked_real_if_gt_prg_case_have_ints
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_if_gt_prg_case_need_seven_ints:
    lda int_count
    cmp #$07
    bcs find_linked_real_if_gt_prg_case_have_ints
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_if_gt_prg_case_have_ints:
    jsr save_current_module_name
    ldx #$00
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
    bcc :+
    jmp find_linked_real_if_gt_prg_case_unsupported
:
    ldx #$01
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
    bcc :+
    jmp find_linked_real_if_gt_prg_case_unsupported
:
    ldx #$01
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_if_gt_prg_case_unsupported
:
    lda int_value_window
    sta linked_store_value
    ldx #$03
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_if_gt_prg_case_unsupported
:
    lda int_value_window
    sta linked_binary_rhs_value
    ldx #$04
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_if_gt_prg_case_unsupported
:
    lda int_value_window
    sta compare_char
    lda linked_condition_body_op
    cmp #'g'
    bne find_linked_real_if_gt_prg_case_check_l
    lda int_value_window
    cmp #$01
    beq find_linked_real_if_gt_prg_case_condition_gt
    cmp #$00
    beq find_linked_real_if_gt_prg_case_condition_ge
    jmp find_linked_real_if_gt_prg_case_unsupported
find_linked_real_if_gt_prg_case_check_l:
    cmp #'l'
    bne find_linked_real_if_gt_prg_case_check_q
    lda int_value_window
    cmp #$01
    beq find_linked_real_if_gt_prg_case_condition_lt
    cmp #$02
    beq find_linked_real_if_gt_prg_case_condition_le
    jmp find_linked_real_if_gt_prg_case_unsupported
find_linked_real_if_gt_prg_case_check_q:
    cmp #'q'
    bne find_linked_real_if_gt_prg_case_check_n
    lda int_value_window
    cmp #$01
    beq find_linked_real_if_gt_prg_case_condition_eq
    jmp find_linked_real_if_gt_prg_case_unsupported
find_linked_real_if_gt_prg_case_check_n:
    cmp #'n'
    beq :+
    jmp find_linked_real_if_gt_prg_case_unsupported
:
    lda int_value_window
    cmp #$01
    beq find_linked_real_if_gt_prg_case_condition_ne
    jmp find_linked_real_if_gt_prg_case_unsupported
find_linked_real_if_gt_prg_case_condition_gt:
    lda #$D0
    sta linked_condition_skip_opcode
    lda #$01
    sta linked_condition_cmp_value
    jmp find_linked_real_if_gt_prg_case_condition_ok
find_linked_real_if_gt_prg_case_condition_ge:
    lda #$F0
    sta linked_condition_skip_opcode
    lda #$FF
    sta linked_condition_cmp_value
    jmp find_linked_real_if_gt_prg_case_condition_ok
find_linked_real_if_gt_prg_case_condition_lt:
    lda #$D0
    sta linked_condition_skip_opcode
    lda #$FF
    sta linked_condition_cmp_value
    jmp find_linked_real_if_gt_prg_case_condition_ok
find_linked_real_if_gt_prg_case_condition_le:
    lda #$F0
    sta linked_condition_skip_opcode
    lda #$01
    sta linked_condition_cmp_value
    jmp find_linked_real_if_gt_prg_case_condition_ok
find_linked_real_if_gt_prg_case_condition_eq:
    lda #$D0
    sta linked_condition_skip_opcode
    lda #$00
    sta linked_condition_cmp_value
    jmp find_linked_real_if_gt_prg_case_condition_ok
find_linked_real_if_gt_prg_case_condition_ne:
    lda #$F0
    sta linked_condition_skip_opcode
    lda #$00
    sta linked_condition_cmp_value
find_linked_real_if_gt_prg_case_condition_ok:
    lda linked_condition_is_nested
    beq find_linked_real_if_gt_prg_case_store_value
    ldx #$05
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    bne find_linked_real_if_gt_prg_case_unsupported
    lda int_value_window
    cmp compare_char
    bne find_linked_real_if_gt_prg_case_unsupported
    ldx #$06
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    bne find_linked_real_if_gt_prg_case_unsupported
    lda int_value_window
    sta linked_condition_store_value
    jmp find_linked_real_if_gt_prg_case_no_else_value
find_linked_real_if_gt_prg_case_store_value:
    ldx #$05
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    bne find_linked_real_if_gt_prg_case_unsupported
    lda int_value_window
    sta linked_condition_store_value
    lda linked_condition_has_else
    beq find_linked_real_if_gt_prg_case_no_else_value
    ldx #$06
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    bne find_linked_real_if_gt_prg_case_unsupported
    lda int_value_window
    sta linked_condition_else_value
find_linked_real_if_gt_prg_case_no_else_value:
    jsr restore_saved_module_name
    lda #PRG_BUILD_REAL_IF_GT
    sta prg_build_strategy
    clc
    rts
find_linked_real_if_gt_prg_case_unsupported:
    jsr restore_saved_module_name
    sec
    rts

find_linked_real_do_until_prg_case:
    lda #$00
    sta linked_loop_update_uses_real_binary
    sta linked_real_binary_literal_layout
    lda #$01
    sta linked_loop_update_uses_real_binary
    lda #'g'
    sta linked_condition_body_op
    lda #<direct_body_real_do_until_gt_real_add_loop
    sta const_ptr
    lda #>direct_body_real_do_until_gt_real_add_loop
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_do_until_prg_case_body_ok
:
    lda #'l'
    sta linked_condition_body_op
    lda #<direct_body_real_do_until_lt_real_add_loop
    sta const_ptr
    lda #>direct_body_real_do_until_lt_real_add_loop
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_do_until_prg_case_body_ok
:
    lda #$01
    sta linked_real_binary_literal_layout
    lda #'g'
    sta linked_condition_body_op
    lda #<direct_body_real_do_until_gt_real_sub_loop
    sta const_ptr
    lda #>direct_body_real_do_until_gt_real_sub_loop
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_do_until_prg_case_body_ok
:
    lda #'l'
    sta linked_condition_body_op
    lda #<direct_body_real_do_until_lt_real_sub_loop
    sta const_ptr
    lda #>direct_body_real_do_until_lt_real_sub_loop
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_do_until_prg_case_body_ok
:
    lda #$02
    sta linked_real_binary_literal_layout
    lda #'g'
    sta linked_condition_body_op
    lda #<direct_body_real_do_until_gt_real_sub_loop_rhs_nonzero
    sta const_ptr
    lda #>direct_body_real_do_until_gt_real_sub_loop_rhs_nonzero
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_do_until_prg_case_body_ok
:
    lda #'l'
    sta linked_condition_body_op
    lda #<direct_body_real_do_until_lt_real_sub_loop_rhs_nonzero
    sta const_ptr
    lda #>direct_body_real_do_until_lt_real_sub_loop_rhs_nonzero
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_do_until_prg_case_body_ok
:
    lda #$00
    sta linked_loop_update_uses_real_binary
    sta linked_real_binary_literal_layout
    lda #'q'
    sta linked_condition_body_op
    lda #<direct_body_real_do_until_eq
    sta const_ptr
    lda #>direct_body_real_do_until_eq
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_do_until_prg_case_body_ok
:
    lda #'g'
    sta linked_condition_body_op
    lda #<direct_body_real_do_until_gt
    sta const_ptr
    lda #>direct_body_real_do_until_gt
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_do_until_prg_case_body_ok
:
    lda #'l'
    sta linked_condition_body_op
    lda #<direct_body_real_do_until_lt
    sta const_ptr
    lda #>direct_body_real_do_until_lt
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_do_until_prg_case_body_ok
:
    lda #'n'
    sta linked_condition_body_op
    lda #<direct_body_real_do_until_ne
    sta const_ptr
    lda #>direct_body_real_do_until_ne
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcc find_linked_real_do_until_prg_case_body_ok
    sec
    rts
find_linked_real_do_until_prg_case_body_ok:
    lda #$00
    sta linked_condition_has_else
    sta linked_condition_is_nested
    lda #$01
    sta linked_condition_is_loop
    lda linked_loop_update_uses_real_binary
    beq find_linked_real_do_until_prg_case_check_two_externals
    lda external_count
    cmp #$03
    bcs find_linked_real_do_until_prg_case_have_externals
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_do_until_prg_case_check_two_externals:
    lda external_count
    cmp #$02
    bcs find_linked_real_do_until_prg_case_have_externals
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_do_until_prg_case_have_externals:
    lda int_count
    cmp #$07
    bcs find_linked_real_do_until_prg_case_have_ints
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_do_until_prg_case_have_ints:
    jsr save_current_module_name
    ldx #$00
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
    bcc :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    ldx #$01
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
    bcc :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda linked_loop_update_uses_real_binary
    beq find_linked_real_do_until_prg_case_externals_ok
    ldx #$02
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
    bcc find_linked_real_do_until_prg_case_externals_ok
    jmp find_linked_real_do_until_prg_case_unsupported
find_linked_real_do_until_prg_case_externals_ok:
    lda linked_loop_update_uses_real_binary
    bne :+
    jmp find_linked_real_do_until_prg_case_parse_once
:
    lda linked_real_binary_literal_layout
    cmp #$02
    bne :+
    jmp find_linked_real_do_until_prg_case_parse_real_sub_rhs_nonzero
:
    cmp #$01
    bne :+
    jmp find_linked_real_do_until_prg_case_parse_real_sub
:
    jmp find_linked_real_do_until_prg_case_parse_real_add
find_linked_real_do_until_prg_case_parse_real_add:
    ldx #$00
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda #$00
    sta linked_store_value
    ldx #$01
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    ldx #$02
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta linked_binary_rhs_value
    ldx #$03
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    ldx #$04
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta linked_loop_update_value
    ldx #$05
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta compare_char
    ldx #$06
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta linked_condition_store_value
    jmp find_linked_real_do_until_prg_case_compare_loaded
find_linked_real_do_until_prg_case_parse_real_sub:
    ldx #$00
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    ldx #$02
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda #$00
    sta linked_binary_rhs_value
    ldx #$03
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    ldx #$01
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta linked_store_value
    ldx #$04
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta linked_loop_update_value
    ldx #$05
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta compare_char
    ldx #$06
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta linked_condition_store_value
    jmp find_linked_real_do_until_prg_case_compare_loaded
find_linked_real_do_until_prg_case_parse_real_sub_rhs_nonzero:
    lda int_count
    cmp #$08
    bcs :+
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
:
    ldx #$00
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    ldx #$02
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    ldx #$04
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    ldx #$01
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta linked_store_value
    ldx #$03
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta linked_binary_rhs_value
    ldx #$05
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta linked_loop_update_value
    ldx #$06
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta compare_char
    ldx #$07
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta linked_condition_store_value
    jmp find_linked_real_do_until_prg_case_compare_loaded
find_linked_real_do_until_prg_case_parse_once:
    ldx #$00
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    ldx #$01
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    ldx #$03
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    ldx #$02
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta linked_binary_rhs_value
    ldx #$04
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta linked_store_value
    ldx #$05
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta compare_char
find_linked_real_do_until_prg_case_compare_loaded:
    lda linked_condition_body_op
    cmp #'g'
    bne find_linked_real_do_until_prg_case_check_l
    lda compare_char
    cmp #$01
    beq find_linked_real_do_until_prg_case_condition_gt
    cmp #$00
    beq find_linked_real_do_until_prg_case_condition_ge
    jmp find_linked_real_do_until_prg_case_unsupported
find_linked_real_do_until_prg_case_check_l:
    cmp #'l'
    bne find_linked_real_do_until_prg_case_check_q
    lda compare_char
    cmp #$01
    beq find_linked_real_do_until_prg_case_condition_lt
    cmp #$02
    beq find_linked_real_do_until_prg_case_condition_le
    jmp find_linked_real_do_until_prg_case_unsupported
find_linked_real_do_until_prg_case_check_q:
    cmp #'q'
    bne find_linked_real_do_until_prg_case_check_n
    lda compare_char
    cmp #$01
    beq find_linked_real_do_until_prg_case_condition_eq
    jmp find_linked_real_do_until_prg_case_unsupported
find_linked_real_do_until_prg_case_check_n:
    cmp #'n'
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:   lda compare_char
    cmp #$01
    beq find_linked_real_do_until_prg_case_condition_ne
    jmp find_linked_real_do_until_prg_case_unsupported
find_linked_real_do_until_prg_case_condition_gt:
    lda #$D0
    sta linked_condition_skip_opcode
    lda #$01
    sta linked_condition_cmp_value
    jmp find_linked_real_do_until_prg_case_condition_ok
find_linked_real_do_until_prg_case_condition_ge:
    lda #$F0
    sta linked_condition_skip_opcode
    lda #$FF
    sta linked_condition_cmp_value
    jmp find_linked_real_do_until_prg_case_condition_ok
find_linked_real_do_until_prg_case_condition_lt:
    lda #$D0
    sta linked_condition_skip_opcode
    lda #$FF
    sta linked_condition_cmp_value
    jmp find_linked_real_do_until_prg_case_condition_ok
find_linked_real_do_until_prg_case_condition_le:
    lda #$F0
    sta linked_condition_skip_opcode
    lda #$01
    sta linked_condition_cmp_value
    jmp find_linked_real_do_until_prg_case_condition_ok
find_linked_real_do_until_prg_case_condition_eq:
    lda #$D0
    sta linked_condition_skip_opcode
    lda #$00
    sta linked_condition_cmp_value
    jmp find_linked_real_do_until_prg_case_condition_ok
find_linked_real_do_until_prg_case_condition_ne:
    lda #$F0
    sta linked_condition_skip_opcode
    lda #$00
    sta linked_condition_cmp_value
find_linked_real_do_until_prg_case_condition_ok:
    lda linked_loop_update_uses_real_binary
    beq :+
    jmp find_linked_real_do_until_prg_case_condition_store_loaded
:
    ldx #$06
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_do_until_prg_case_unsupported
:
    lda int_value_window
    sta linked_condition_store_value
find_linked_real_do_until_prg_case_condition_store_loaded:
    jsr restore_saved_module_name
    lda #PRG_BUILD_REAL_DO_UNTIL
    sta prg_build_strategy
    clc
    rts
find_linked_real_do_until_prg_case_unsupported:
    jsr restore_saved_module_name
    sec
    rts

find_linked_real_while_prg_case:
    lda #$00
    sta linked_loop_update_uses_conversion
    sta linked_loop_update_uses_real_binary
    sta linked_real_binary_literal_layout
    sta linked_real_binary_update_op
    lda #'g'
    sta linked_condition_body_op
    lda #<direct_body_real_while_gt_once
    sta const_ptr
    lda #>direct_body_real_while_gt_once
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_while_prg_case_body_ok
:
    lda #$01
    sta linked_loop_update_uses_conversion
    lda #'g'
    sta linked_condition_body_op
    lda #<direct_body_real_while_gt_convert_once
    sta const_ptr
    lda #>direct_body_real_while_gt_convert_once
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_while_prg_case_body_ok
:
    lda #$00
    sta linked_loop_update_uses_conversion
    lda #$01
    sta linked_loop_update_uses_real_binary
    sta linked_real_binary_update_op
    sta linked_real_binary_literal_layout
    lda #'g'
    sta linked_condition_body_op
    lda #<direct_body_real_while_gt_real_sub_loop_rhs_nonzero
    sta const_ptr
    lda #>direct_body_real_while_gt_real_sub_loop_rhs_nonzero
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_while_prg_case_body_ok
:
    lda #$00
    sta linked_loop_update_uses_conversion
    sta linked_real_binary_literal_layout
    lda #$01
    sta linked_loop_update_uses_real_binary
    sta linked_real_binary_update_op
    lda #'g'
    sta linked_condition_body_op
    lda #<direct_body_real_while_gt_real_sub_loop
    sta const_ptr
    lda #>direct_body_real_while_gt_real_sub_loop
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_while_prg_case_body_ok
:
    lda #$00
    sta linked_loop_update_uses_conversion
    sta linked_real_binary_literal_layout
    sta linked_real_binary_update_op
    lda #$01
    sta linked_loop_update_uses_real_binary
    lda #'g'
    sta linked_condition_body_op
    lda #<direct_body_real_while_gt_real_add_loop
    sta const_ptr
    lda #>direct_body_real_while_gt_real_add_loop
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_while_prg_case_body_ok
:
    lda #$00
    sta linked_loop_update_uses_conversion
    sta linked_real_binary_literal_layout
    sta linked_real_binary_update_op
    lda #$01
    sta linked_loop_update_uses_real_binary
    lda #'l'
    sta linked_condition_body_op
    lda #<direct_body_real_while_lt_real_add_loop
    sta const_ptr
    lda #>direct_body_real_while_lt_real_add_loop
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_while_prg_case_body_ok
:
    lda #$00
    sta linked_loop_update_uses_conversion
    sta linked_real_binary_literal_layout
    lda #$01
    sta linked_loop_update_uses_real_binary
    sta linked_real_binary_update_op
    lda #'l'
    sta linked_condition_body_op
    lda #<direct_body_real_while_lt_real_sub_loop
    sta const_ptr
    lda #>direct_body_real_while_lt_real_sub_loop
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_while_prg_case_body_ok
:
    lda #$00
    sta linked_loop_update_uses_real_binary
    sta linked_loop_update_uses_conversion
    lda #'l'
    sta linked_condition_body_op
    lda #<direct_body_real_while_lt_once
    sta const_ptr
    lda #>direct_body_real_while_lt_once
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_while_prg_case_body_ok
:
    lda #$01
    sta linked_loop_update_uses_conversion
    lda #'l'
    sta linked_condition_body_op
    lda #<direct_body_real_while_lt_convert_once
    sta const_ptr
    lda #>direct_body_real_while_lt_convert_once
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    jmp find_linked_real_while_prg_case_body_ok
:
    sec
    rts
find_linked_real_while_prg_case_body_ok:
    lda linked_loop_update_uses_real_binary
    beq find_linked_real_while_prg_case_check_two_externals
    lda external_count
    cmp #$03
    bcs find_linked_real_while_prg_case_have_externals
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_while_prg_case_check_two_externals:
    lda external_count
    cmp #$02
    bcs find_linked_real_while_prg_case_have_externals
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_while_prg_case_have_externals:
    lda int_count
    cmp #$07
    bcs find_linked_real_while_prg_case_have_ints
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_linked_real_while_prg_case_have_ints:
    jsr save_current_module_name
    ldx #$00
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
    bcc :+
    jmp find_linked_real_while_prg_case_unsupported
:
    ldx #$01
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
    bcc :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda linked_loop_update_uses_real_binary
    beq find_linked_real_while_prg_case_externals_ok
    ldx #$02
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_external_print_body_is_M
    bcc find_linked_real_while_prg_case_externals_ok
    jmp find_linked_real_while_prg_case_unsupported
find_linked_real_while_prg_case_externals_ok:
    lda linked_loop_update_uses_real_binary
    beq find_linked_real_while_prg_case_parse_once
    lda linked_real_binary_update_op
    bne :+
    jmp find_linked_real_while_prg_case_parse_real_add
:
    jmp find_linked_real_while_prg_case_parse_real_sub
find_linked_real_while_prg_case_parse_once:
    ldx #$00
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    ldx #$02
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    ldx #$06
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda #$00
    sta linked_loop_update_value
    lda linked_loop_update_uses_conversion
    beq find_linked_real_while_prg_case_update_ok
    lda int_count
    cmp #$08
    bcs :+
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
:
    ldx #$07
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta linked_loop_update_value
find_linked_real_while_prg_case_update_ok:
    ldx #$01
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta linked_store_value
    ldx #$03
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta linked_binary_rhs_value
    ldx #$04
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta compare_char
    ldx #$05
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta linked_condition_store_value
    jmp find_linked_real_while_prg_case_compare_loaded
find_linked_real_while_prg_case_parse_real_sub:
    lda linked_real_binary_literal_layout
    beq :+
    jmp find_linked_real_while_prg_case_parse_real_sub_rhs_nonzero
:
    ldx #$00
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    ldx #$02
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda #$00
    sta linked_binary_rhs_value
    ldx #$03
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    ldx #$01
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta linked_store_value
    ldx #$04
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta linked_loop_update_value
    ldx #$05
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta compare_char
    ldx #$06
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta linked_condition_store_value
    jmp find_linked_real_while_prg_case_compare_loaded
find_linked_real_while_prg_case_parse_real_sub_rhs_nonzero:
    lda int_count
    cmp #$08
    bcs :+
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
:
    ldx #$00
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    ldx #$02
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    ldx #$04
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    ldx #$01
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta linked_store_value
    ldx #$03
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta linked_binary_rhs_value
    ldx #$05
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta linked_loop_update_value
    ldx #$06
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta compare_char
    ldx #$07
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta linked_condition_store_value
    jmp find_linked_real_while_prg_case_compare_loaded
find_linked_real_while_prg_case_parse_real_add:
    ldx #$00
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda #$00
    sta linked_store_value
    ldx #$01
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    ldx #$02
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta linked_binary_rhs_value
    ldx #$03
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ora int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    ldx #$04
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta linked_loop_update_value
    ldx #$05
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta compare_char
    ldx #$06
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    jmp find_linked_real_while_prg_case_unsupported
:
    lda int_value_window
    sta linked_condition_store_value
find_linked_real_while_prg_case_compare_loaded:
    lda linked_condition_body_op
    cmp #'g'
    bne find_linked_real_while_prg_case_check_l
    lda compare_char
    cmp #$01
    beq find_linked_real_while_prg_case_condition_gt
    cmp #$00
    beq find_linked_real_while_prg_case_condition_ge
    jmp find_linked_real_while_prg_case_unsupported
find_linked_real_while_prg_case_check_l:
    cmp #'l'
    bne find_linked_real_while_prg_case_unsupported
    lda compare_char
    cmp #$01
    beq find_linked_real_while_prg_case_condition_lt
    cmp #$02
    beq find_linked_real_while_prg_case_condition_le
    jmp find_linked_real_while_prg_case_unsupported
find_linked_real_while_prg_case_condition_gt:
    lda #$D0
    sta linked_condition_skip_opcode
    lda #$01
    sta linked_condition_cmp_value
    jmp find_linked_real_while_prg_case_condition_ok
find_linked_real_while_prg_case_condition_ge:
    lda #$F0
    sta linked_condition_skip_opcode
    lda #$FF
    sta linked_condition_cmp_value
    jmp find_linked_real_while_prg_case_condition_ok
find_linked_real_while_prg_case_condition_lt:
    lda #$D0
    sta linked_condition_skip_opcode
    lda #$FF
    sta linked_condition_cmp_value
    jmp find_linked_real_while_prg_case_condition_ok
find_linked_real_while_prg_case_condition_le:
    lda #$F0
    sta linked_condition_skip_opcode
    lda #$01
    sta linked_condition_cmp_value
find_linked_real_while_prg_case_condition_ok:
    jsr restore_saved_module_name
    lda #PRG_BUILD_REAL_WHILE
    sta prg_build_strategy
    clc
    rts
find_linked_real_while_prg_case_unsupported:
    jsr restore_saved_module_name
    sec
    rts

find_runtime_helper_condition_prg_case:
    lda #<direct_body_runtime_helper_if_eq
    sta const_ptr
    lda #>direct_body_runtime_helper_if_eq
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    lda #'q'
    sta linked_condition_body_op
    jmp find_runtime_helper_condition_prg_case_arg_body_ok
:
    lda #<direct_body_runtime_helper_if_ne
    sta const_ptr
    lda #>direct_body_runtime_helper_if_ne
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    lda #'n'
    sta linked_condition_body_op
    jmp find_runtime_helper_condition_prg_case_arg_body_ok
:
    lda #<direct_body_runtime_helper_noarg_if_eq
    sta const_ptr
    lda #>direct_body_runtime_helper_noarg_if_eq
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    lda #'q'
    sta linked_condition_body_op
    jmp find_runtime_helper_condition_prg_case_noarg_body_ok
:
    lda #<direct_body_runtime_helper_noarg_if_ne
    sta const_ptr
    lda #>direct_body_runtime_helper_noarg_if_ne
    sta const_ptr+1
    jsr direct_entry_body_matches_const
    bcs :+
    lda #'n'
    sta linked_condition_body_op
    jmp find_runtime_helper_condition_prg_case_noarg_body_ok
:
    sec
    rts
find_runtime_helper_condition_prg_case_arg_body_ok:
    lda #$01
    sta linked_runtime_arg2
    lda external_count
    cmp #$02
    bcs :+
    sec
    rts
:
    lda int_count
    cmp #$03
    beq :+
    sec
    rts
:
    ldx #$00
    jsr runtime_helper_kind_for_external_index_x
    bcc :+
    sec
    rts
:
    cmp #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    beq :+
    sec
    rts
:
    jsr find_runtime_helper_condition_side_effect_ok_or_fail
    bcc :+
    sec
    rts
:
    jsr load_runtime_helper_condition_literals_or_fail
    bcc find_runtime_helper_condition_prg_case_load_objects
    sec
    rts
find_runtime_helper_condition_prg_case_noarg_body_ok:
    lda #$00
    sta linked_runtime_arg2
    lda external_count
    cmp #$02
    bcs :+
    sec
    rts
:
    lda int_count
    cmp #$02
    beq :+
    sec
    rts
:
    ldx #$00
    jsr runtime_helper_kind_for_external_index_x
    bcc :+
    sec
    rts
:
    cmp #RUNTIME_HELPER_KIND_BYTE_READBACK
    beq :+
    sec
    rts
:
    jsr find_runtime_helper_condition_side_effect_ok_or_fail
    bcc :+
    sec
    rts
:
    jsr load_runtime_helper_condition_noarg_literals_or_fail
    bcc find_runtime_helper_condition_prg_case_load_objects
    sec
    rts
find_runtime_helper_condition_side_effect_ok_or_fail:
    ldx #$01
    jsr runtime_helper_kind_for_external_index_x
    bcc :+
    sec
    rts
:
    cmp #RUNTIME_HELPER_KIND_GFX_BGCOLOR
    beq find_runtime_helper_condition_prg_case_kind_ok
    cmp #RUNTIME_HELPER_KIND_A_BYTE
    beq find_runtime_helper_condition_prg_case_kind_ok
    sec
    rts
find_runtime_helper_condition_prg_case_kind_ok:
    clc
    rts
find_runtime_helper_condition_prg_case_load_objects:
    jsr save_current_module_name
    lda #$00
    sta linked_object_index
find_runtime_helper_condition_prg_case_object_loop:
    ldx linked_object_index
    cpx external_count
    beq find_runtime_helper_condition_prg_case_supported
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_first_body_is_object_code
    bcc :+
    jmp find_runtime_helper_condition_prg_case_unsupported
:
    inc linked_object_index
    jmp find_runtime_helper_condition_prg_case_object_loop
find_runtime_helper_condition_prg_case_supported:
    jsr restore_saved_module_name
    lda #PRG_BUILD_RUNTIME_HELPER_CONDITION
    sta prg_build_strategy
    clc
    rts
find_runtime_helper_condition_prg_case_unsupported:
    jsr restore_saved_module_name
    sec
    rts

load_runtime_helper_condition_literals_or_fail:
    ldx #$00
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    sec
    rts
:
    lda int_value_window
    sta linked_runtime_arg0
    ldx #$01
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    sec
    rts
:
    lda int_value_window
    sta linked_condition_cmp_value
    ldx #$02
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    sec
    rts
:
    lda int_value_window
    sta linked_runtime_arg1
    jsr set_runtime_helper_condition_skip_opcode
    clc
    rts

load_runtime_helper_condition_noarg_literals_or_fail:
    ldx #$00
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    sec
    rts
:
    lda int_value_window
    sta linked_condition_cmp_value
    ldx #$01
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window+1
    beq :+
    sec
    rts
:
    lda int_value_window
    sta linked_runtime_arg1
    jsr set_runtime_helper_condition_skip_opcode
    clc
    rts

set_runtime_helper_condition_skip_opcode:
    lda linked_condition_body_op
    cmp #'n'
    bne :+
    lda #$F0
    sta linked_condition_skip_opcode
    rts
:
    lda #$D0
    sta linked_condition_skip_opcode
    rts

find_runtime_helper_sequence_prg_case:
    lda external_count
    cmp #$01
    bcs :+
    sec
    rts
:
    jsr runtime_helper_sequence_load_ints_or_fail
    jsr runtime_helper_sequence_reset_body_parse
find_runtime_helper_sequence_prg_case_loop:
    ldy linked_runtime_body_pos
    lda (body_ptr),y
    cmp #'p'
    beq find_runtime_helper_sequence_prg_case_param
    cmp #'u'
    beq find_runtime_helper_sequence_prg_case_call
    cmp #'L'
    bne :+
    jmp find_runtime_helper_sequence_prg_case_load
:
    cmp #'S'
    bne :+
    jmp find_runtime_helper_sequence_prg_case_store
:
    cmp #'a'
    bne :+
    jmp find_runtime_helper_sequence_prg_case_add
:
    cmp #'r'
    bne :+
    jmp find_runtime_helper_sequence_prg_case_return
:
    sec
    rts
find_runtime_helper_sequence_prg_case_param:
    iny
    lda (body_ptr),y
    jsr object_code_import_index_from_a
    bcc :+
    sec
    rts
:
    cmp int_count
    bcc :+
    sec
    rts
:
    iny
    sty linked_runtime_body_pos
    jsr runtime_helper_sequence_store_arg_from_a
    bcc :+
    sec
    rts
:
    jmp find_runtime_helper_sequence_prg_case_loop
find_runtime_helper_sequence_prg_case_call:
    iny
    lda (body_ptr),y
    jsr object_code_import_index_from_a
    bcc :+
    sec
    rts
:
    cmp external_count
    bcc :+
    sec
    rts
:
    sta linked_external_index
    iny
    sty linked_runtime_body_pos
    ldx linked_external_index
    jsr runtime_helper_kind_for_external_index_x
    bcc :+
    sec
    rts
:
    sta linked_runtime_helper_kind
    jsr runtime_helper_sequence_validate_current_call
    bcc :+
    sec
    rts
:
    inc linked_runtime_call_count
    lda #$00
    sta linked_runtime_arg_count
    jsr runtime_helper_sequence_update_result_pending
    jmp find_runtime_helper_sequence_prg_case_loop
find_runtime_helper_sequence_prg_case_store:
    iny
    lda (body_ptr),y
    jsr object_code_import_index_from_a
    bcc :+
    sec
    rts
:
    iny
    sty linked_runtime_body_pos
    jsr runtime_helper_sequence_note_store_or_fail
    bcc :+
    sec
    rts
:
    jmp find_runtime_helper_sequence_prg_case_loop
find_runtime_helper_sequence_prg_case_load:
    iny
    lda (body_ptr),y
    jsr object_code_import_index_from_a
    bcc :+
    sec
    rts
:
    iny
    sty linked_runtime_body_pos
    jsr runtime_helper_sequence_note_load_or_fail
    bcc :+
    sec
    rts
:
    jmp find_runtime_helper_sequence_prg_case_loop
find_runtime_helper_sequence_prg_case_add:
    iny
    sty linked_runtime_body_pos
    jsr runtime_helper_sequence_fold_add_or_fail
    bcc :+
    sec
    rts
:
    jmp find_runtime_helper_sequence_prg_case_loop
find_runtime_helper_sequence_prg_case_return:
    iny
    lda (body_ptr),y
    beq :+
    sec
    rts
:
    lda linked_runtime_arg_count
    beq :+
    sec
    rts
:
    lda linked_runtime_call_count
    cmp #$01
    bcs find_runtime_helper_sequence_prg_case_load_objects
    sec
    rts
find_runtime_helper_sequence_prg_case_load_objects:
    jsr save_current_module_name
    lda #$00
    sta linked_object_index
find_runtime_helper_sequence_prg_case_object_loop:
    ldx linked_object_index
    cpx external_count
    beq find_runtime_helper_sequence_prg_case_supported
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    jsr loaded_first_body_is_object_code
    bcc :+
    jmp find_runtime_helper_sequence_prg_case_unsupported
:
    inc linked_object_index
    jmp find_runtime_helper_sequence_prg_case_object_loop
find_runtime_helper_sequence_prg_case_supported:
    jsr restore_saved_module_name
    lda #PRG_BUILD_RUNTIME_HELPER_SEQUENCE
    sta prg_build_strategy
    clc
    rts
find_runtime_helper_sequence_prg_case_unsupported:
    jsr restore_saved_module_name
    sec
    rts

runtime_helper_sequence_load_ints_or_fail:
    lda #$00
    sta linked_object_index
runtime_helper_sequence_load_ints_loop:
    ldx linked_object_index
    cpx int_count
    beq runtime_helper_sequence_load_ints_done
    jsr load_int_value_window_from_x_or_fail
    lda int_value_window
    ldx linked_object_index
    sta linked_literal_window+LINKED_LITERAL_LO
    lda int_value_window+1
    sta linked_literal_window+LINKED_LITERAL_HI
    jsr store_linked_literal_window_from_x_or_fail
    inc linked_object_index
    jmp runtime_helper_sequence_load_ints_loop
runtime_helper_sequence_load_ints_done:
    lda int_count
    sta linked_literal_count
    rts

runtime_helper_sequence_reset_body_parse:
    ldx entry_export_index
    jsr set_body_ptr_from_x
    lda #$00
    sta linked_runtime_arg_count
    sta linked_runtime_call_count
    sta linked_runtime_body_pos
    sta linked_runtime_helper_kind
    sta linked_runtime_result_pending
    sta linked_runtime_result_arg_count
    sta linked_runtime_result_loaded
    sta linked_runtime_result_store_ordinal
    sta linked_runtime_store_count
    rts

runtime_helper_sequence_store_arg_from_a:
    pha
    lda linked_runtime_result_pending
    beq :+
    lda linked_runtime_result_loaded
    bne :+
    lda #$00
    sta linked_runtime_result_pending
    sta linked_runtime_result_arg_count
    sta linked_runtime_result_loaded
    sta linked_runtime_result_store_ordinal
:
    lda linked_runtime_arg_count
    cmp #$04
    bcc :+
    pla
    sec
    rts
:
    tax
    pla
    cpx #$00
    bne :+
    sta linked_runtime_arg0
    jmp runtime_helper_sequence_store_arg_done
:
    cpx #$01
    bne :+
    sta linked_runtime_arg1
    jmp runtime_helper_sequence_store_arg_done
:
    cpx #$02
    bne :+
    sta linked_runtime_arg2
    jmp runtime_helper_sequence_store_arg_done
:
    sta linked_runtime_arg3
runtime_helper_sequence_store_arg_done:
    inc linked_runtime_arg_count
    clc
    rts

runtime_helper_sequence_update_result_pending:
    lda linked_runtime_helper_kind
    cmp #RUNTIME_HELPER_KIND_BYTE_READBACK
    bne :+
    lda #$01
    sta linked_runtime_result_pending
    lda #$00
    sta linked_runtime_result_arg_count
    sta linked_runtime_result_loaded
    sta linked_runtime_result_store_ordinal
    rts
:
    cmp #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    bne :+
    lda #$01
    sta linked_runtime_result_pending
    lda #$00
    sta linked_runtime_result_arg_count
    sta linked_runtime_result_loaded
    sta linked_runtime_result_store_ordinal
    rts
:
    cmp #RUNTIME_HELPER_KIND_XY_WORD_READBACK
    bne :+
    lda #$01
    sta linked_runtime_result_pending
    lda #$00
    sta linked_runtime_result_arg_count
    sta linked_runtime_result_loaded
    sta linked_runtime_result_store_ordinal
    rts
:
    cmp #RUNTIME_HELPER_KIND_AY_BYTE_READBACK
    bne :+
    lda #$01
    sta linked_runtime_result_pending
    lda #$00
    sta linked_runtime_result_arg_count
    sta linked_runtime_result_loaded
    sta linked_runtime_result_store_ordinal
    rts
:
    cmp #RUNTIME_HELPER_KIND_AXY_BYTES_CLC_READBACK
    bne :+
    lda #$01
    sta linked_runtime_result_pending
    lda #$00
    sta linked_runtime_result_arg_count
    sta linked_runtime_result_loaded
    sta linked_runtime_result_store_ordinal
    rts
:
    cmp #RUNTIME_HELPER_KIND_AXY_E0_BYTES_CLC_READBACK
    bne :+
    lda #$01
    sta linked_runtime_result_pending
    lda #$00
    sta linked_runtime_result_arg_count
    sta linked_runtime_result_loaded
    sta linked_runtime_result_store_ordinal
    rts
:
    lda #$00
    sta linked_runtime_result_pending
    sta linked_runtime_result_arg_count
    sta linked_runtime_result_loaded
    sta linked_runtime_result_store_ordinal
    rts

runtime_helper_sequence_note_store_or_fail:
    cmp #VAR_MAX
    bcc :+
    sec
    rts
:
    sta linked_import_index
    lda linked_runtime_store_count
    cmp #VAR_MAX
    bcc :+
    sec
    rts
:
    lda linked_runtime_result_pending
    beq runtime_helper_sequence_note_literal_store
    ldx linked_runtime_store_count
    lda linked_import_index
    sta linked_runtime_store_window+RUNTIME_STORE_VAR
    lda #$FF
    sta linked_runtime_store_window+RUNTIME_STORE_LITERAL
    jsr store_linked_runtime_store_window_from_x_or_fail
    inc linked_runtime_store_count
    lda #$00
    sta linked_runtime_result_pending
    sta linked_runtime_result_arg_count
    sta linked_runtime_result_loaded
    sta linked_runtime_result_store_ordinal
    clc
    rts
runtime_helper_sequence_note_literal_store:
    lda linked_runtime_arg_count
    cmp #$01
    beq :+
    sec
    rts
:
    ldx linked_runtime_store_count
    lda linked_import_index
    sta linked_runtime_store_window+RUNTIME_STORE_VAR
    lda linked_runtime_arg0
    sta linked_runtime_store_window+RUNTIME_STORE_LITERAL
    jsr store_linked_runtime_store_window_from_x_or_fail
    inc linked_runtime_store_count
    lda #$00
    sta linked_runtime_arg_count
    sta linked_runtime_result_pending
    sta linked_runtime_result_arg_count
    sta linked_runtime_result_loaded
    sta linked_runtime_result_store_ordinal
    clc
    rts

runtime_helper_sequence_note_load_or_fail:
    jsr runtime_helper_sequence_find_store_ordinal_for_a
    bcc :+
    sec
    rts
:
    tax
    stx linked_object_index
    jsr load_linked_runtime_store_window_from_x_or_fail
    lda linked_runtime_store_window+RUNTIME_STORE_LITERAL
    cmp #$FF
    beq runtime_helper_sequence_note_runtime_load
    jsr runtime_helper_sequence_store_arg_from_a
    rts
runtime_helper_sequence_note_runtime_load:
    ldx linked_object_index
    jsr runtime_helper_sequence_commit_loaded_arg_or_fail
    bcc :+
    rts
:
    ldx linked_object_index
    lda #$01
    sta linked_runtime_result_pending
    lda linked_runtime_arg_count
    sta linked_runtime_result_arg_count
    lda #$01
    sta linked_runtime_result_loaded
    stx linked_runtime_result_store_ordinal
    clc
    rts

runtime_helper_sequence_commit_loaded_arg_or_fail:
    lda linked_runtime_result_pending
    bne :+
    jmp runtime_helper_sequence_commit_loaded_arg_ok
:
    lda linked_runtime_result_loaded
    bne :+
    jmp runtime_helper_sequence_commit_loaded_arg_ok
:
    lda linked_runtime_arg_count
    cmp #$04
    bcc :+
    sec
    rts
:
    lda linked_runtime_result_arg_count
    cmp #$04
    bcc :+
    sec
    rts
:
    cmp linked_runtime_arg_count
    bcc :+
    beq :+
    sec
    rts
:
    sta linked_import_index
    lda linked_runtime_arg_count
    cmp #$03
    bcc runtime_helper_sequence_commit_loaded_arg_shift_two
    lda linked_import_index
    cmp #$03
    bcs runtime_helper_sequence_commit_loaded_arg_shift_two
    lda linked_runtime_arg2
    sta linked_runtime_arg3
runtime_helper_sequence_commit_loaded_arg_shift_two:
    lda linked_runtime_arg_count
    cmp #$02
    bcc runtime_helper_sequence_commit_loaded_arg_shift_one
    lda linked_import_index
    cmp #$02
    bcs runtime_helper_sequence_commit_loaded_arg_shift_one
    lda linked_runtime_arg1
    sta linked_runtime_arg2
runtime_helper_sequence_commit_loaded_arg_shift_one:
    lda linked_runtime_arg_count
    cmp #$01
    bcc runtime_helper_sequence_commit_loaded_arg_store
    lda linked_import_index
    cmp #$01
    bcs runtime_helper_sequence_commit_loaded_arg_store
    lda linked_runtime_arg0
    sta linked_runtime_arg1
runtime_helper_sequence_commit_loaded_arg_store:
    lda linked_runtime_result_store_ordinal
    ora #$80
    ldx linked_import_index
    cpx #$00
    bne :+
    sta linked_runtime_arg0
    jmp runtime_helper_sequence_commit_loaded_arg_done
:
    cpx #$01
    bne :+
    sta linked_runtime_arg1
    jmp runtime_helper_sequence_commit_loaded_arg_done
:
    cpx #$02
    bne :+
    sta linked_runtime_arg2
    jmp runtime_helper_sequence_commit_loaded_arg_done
:
    sta linked_runtime_arg3
runtime_helper_sequence_commit_loaded_arg_done:
    inc linked_runtime_arg_count
    lda #$00
    sta linked_runtime_result_pending
    sta linked_runtime_result_arg_count
    sta linked_runtime_result_loaded
    sta linked_runtime_result_store_ordinal
runtime_helper_sequence_commit_loaded_arg_ok:
    clc
    rts

runtime_helper_sequence_fold_add_or_fail:
    lda linked_runtime_arg_count
    cmp #$02
    beq :+
    sec
    rts
:
    ldx linked_runtime_arg0
    jsr load_linked_literal_window_from_x_or_fail
    lda linked_literal_window+LINKED_LITERAL_LO
    sta linked_store_value
    lda linked_literal_window+LINKED_LITERAL_HI
    sta linked_store_value_hi
    ldx linked_runtime_arg1
    jsr load_linked_literal_window_from_x_or_fail
    clc
    lda linked_store_value
    adc linked_literal_window+LINKED_LITERAL_LO
    sta linked_store_value
    lda linked_store_value_hi
    adc linked_literal_window+LINKED_LITERAL_HI
    bcc :+
    sec
    rts
:
    sta linked_store_value_hi
    ldx linked_literal_count
    cpx #INT_LITERAL_MAX
    bcc :+
    sec
    rts
:
    lda linked_store_value
    sta linked_literal_window+LINKED_LITERAL_LO
    lda linked_store_value_hi
    sta linked_literal_window+LINKED_LITERAL_HI
    jsr store_linked_literal_window_from_x_or_fail
    inc linked_literal_count
    txa
    pha
    lda #$00
    sta linked_runtime_arg_count
    pla
    jmp runtime_helper_sequence_store_arg_from_a

runtime_helper_sequence_find_store_ordinal_for_a:
    sta linked_import_index
    lda linked_runtime_store_count
    beq runtime_helper_sequence_find_store_ordinal_fail
    tax
    dex
runtime_helper_sequence_find_store_ordinal_loop:
    jsr load_linked_runtime_store_window_from_x_or_fail
    lda linked_runtime_store_window+RUNTIME_STORE_VAR
    cmp linked_import_index
    beq runtime_helper_sequence_find_store_ordinal_found
    txa
    beq runtime_helper_sequence_find_store_ordinal_fail
    dex
    jmp runtime_helper_sequence_find_store_ordinal_loop
runtime_helper_sequence_find_store_ordinal_fail:
    sec
    rts
runtime_helper_sequence_find_store_ordinal_found:
    txa
    clc
    rts

runtime_helper_kind_for_external_index_x:
    stx linked_external_index
    lda #<runtime_name_rt_sprite_data
    sta const_ptr
    lda #>runtime_name_rt_sprite_data
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_SPRITE_DATA
    clc
    rts
:
    lda #<runtime_name_rt_sprite_pos
    sta const_ptr
    lda #>runtime_name_rt_sprite_pos
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_SPRITE_POS
    clc
    rts
:
    lda #<runtime_name_rt_sprite_color
    sta const_ptr
    lda #>runtime_name_rt_sprite_color
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_XA_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_sprite_ptr
    sta const_ptr
    lda #>runtime_name_rt_sprite_ptr
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_XA_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_sprite_set_mc
    sta const_ptr
    lda #>runtime_name_rt_sprite_set_mc
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_X1_A0_BYTES
    clc
    rts
:
    lda #<runtime_name_rt_sprite_on
    sta const_ptr
    lda #>runtime_name_rt_sprite_on
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_sprite_off
    sta const_ptr
    lda #>runtime_name_rt_sprite_off
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_sprite_mc
    sta const_ptr
    lda #>runtime_name_rt_sprite_mc
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_AY_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_sprite_xexp
    sta const_ptr
    lda #>runtime_name_rt_sprite_xexp
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_AY_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_sprite_yexp
    sta const_ptr
    lda #>runtime_name_rt_sprite_yexp
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_AY_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_sprite_prio
    sta const_ptr
    lda #>runtime_name_rt_sprite_prio
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_AY_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_gfx_bgcolor
    sta const_ptr
    lda #>runtime_name_rt_gfx_bgcolor
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_GFX_BGCOLOR
    clc
    rts
:
    lda #<runtime_name_rt_gfx_bordercolor
    sta const_ptr
    lda #>runtime_name_rt_gfx_bordercolor
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_GFX_BGCOLOR
    clc
    rts
:
    lda #<runtime_name_rt_gfx_vic_bank
    sta const_ptr
    lda #>runtime_name_rt_gfx_vic_bank
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_gfx_screen_base
    sta const_ptr
    lda #>runtime_name_rt_gfx_screen_base
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_XY_WORD
    clc
    rts
:
    lda #<runtime_name_rt_gfx_bitmap_base
    sta const_ptr
    lda #>runtime_name_rt_gfx_bitmap_base
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_XY_WORD
    clc
    rts
:
    lda #<runtime_name_rt_gfx_screen_cell
    sta const_ptr
    lda #>runtime_name_rt_gfx_screen_cell
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_AXY_BYTES_CLC
    clc
    rts
:
    lda #<runtime_name_rt_gfx_color_cell
    sta const_ptr
    lda #>runtime_name_rt_gfx_color_cell
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_AXY_BYTES_CLC
    clc
    rts
:
    lda #<runtime_name_rt_gfx_bitmap_fill
    sta const_ptr
    lda #>runtime_name_rt_gfx_bitmap_fill
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_gfx_screen_copy
    sta const_ptr
    lda #>runtime_name_rt_gfx_screen_copy
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_XY_WORD
    clc
    rts
:
    lda #<runtime_name_rt_gfx_color_copy
    sta const_ptr
    lda #>runtime_name_rt_gfx_color_copy
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_XY_WORD
    clc
    rts
:
    lda #<runtime_name_rt_gfx_bitmap_copy
    sta const_ptr
    lda #>runtime_name_rt_gfx_bitmap_copy
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_XY_WORD
    clc
    rts
:
    lda #<runtime_name_rt_sid_freq
    sta const_ptr
    lda #>runtime_name_rt_sid_freq
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_SID_FREQ
    clc
    rts
:
    lda #<runtime_name_rt_sid_pulse
    sta const_ptr
    lda #>runtime_name_rt_sid_pulse
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_SID_FREQ
    clc
    rts
:
    lda #<runtime_name_rt_sid_wave
    sta const_ptr
    lda #>runtime_name_rt_sid_wave
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_AY_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_sid_ad
    sta const_ptr
    lda #>runtime_name_rt_sid_ad
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_AY_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_sid_sr
    sta const_ptr
    lda #>runtime_name_rt_sid_sr
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_AY_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_sid_on
    sta const_ptr
    lda #>runtime_name_rt_sid_on
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_sid_off
    sta const_ptr
    lda #>runtime_name_rt_sid_off
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_sid_vol
    sta const_ptr
    lda #>runtime_name_rt_sid_vol
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_sid_mode
    sta const_ptr
    lda #>runtime_name_rt_sid_mode
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_sid_route
    sta const_ptr
    lda #>runtime_name_rt_sid_route
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_sid_res
    sta const_ptr
    lda #>runtime_name_rt_sid_res
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_sid_cutoff
    sta const_ptr
    lda #>runtime_name_rt_sid_cutoff
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_XY_WORD
    clc
    rts
:
    lda #<runtime_name_rt_sid_rst
    sta const_ptr
    lda #>runtime_name_rt_sid_rst
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_NO_ARG
    clc
    rts
:
    lda #<runtime_name_rt_sid_osc3
    sta const_ptr
    lda #>runtime_name_rt_sid_osc3
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_sid_env3
    sta const_ptr
    lda #>runtime_name_rt_sid_env3
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_sprite_hit
    sta const_ptr
    lda #>runtime_name_rt_sprite_hit
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_sprite_hit_bg
    sta const_ptr
    lda #>runtime_name_rt_sprite_hit_bg
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_joy
    sta const_ptr
    lda #>runtime_name_rt_joy
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_jp
    sta const_ptr
    lda #>runtime_name_rt_jp
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_jb1
    sta const_ptr
    lda #>runtime_name_rt_jb1
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_jb2
    sta const_ptr
    lda #>runtime_name_rt_jb2
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_mp
    sta const_ptr
    lda #>runtime_name_rt_mp
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_create
    sta const_ptr
    lda #>runtime_name_rt_dbf_create
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_XY_WORD_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_open
    sta const_ptr
    lda #>runtime_name_rt_dbf_open
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_XY_WORD_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_close
    sta const_ptr
    lda #>runtime_name_rt_dbf_close
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE
    clc
    rts
:
    lda #<runtime_name_rt_dbf_go
    sta const_ptr
    lda #>runtime_name_rt_dbf_go
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_AY_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_fieldcount
    sta const_ptr
    lda #>runtime_name_rt_dbf_fieldcount
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_fieldlen
    sta const_ptr
    lda #>runtime_name_rt_dbf_fieldlen
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_AY_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_readbyte
    sta const_ptr
    lda #>runtime_name_rt_dbf_readbyte
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_AY_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_readfieldbyte
    sta const_ptr
    lda #>runtime_name_rt_dbf_readfieldbyte
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_AXY_BYTES_CLC_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_writefieldbyte
    sta const_ptr
    lda #>runtime_name_rt_dbf_writefieldbyte
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_AXY_E0_BYTES_CLC_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_writebyte
    sta const_ptr
    lda #>runtime_name_rt_dbf_writebyte
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_AXY_BYTES_CLC_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_append
    sta const_ptr
    lda #>runtime_name_rt_dbf_append
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_pack
    sta const_ptr
    lda #>runtime_name_rt_dbf_pack
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_save
    sta const_ptr
    lda #>runtime_name_rt_dbf_save
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_delete
    sta const_ptr
    lda #>runtime_name_rt_dbf_delete
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_undelete
    sta const_ptr
    lda #>runtime_name_rt_dbf_undelete
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_deleted
    sta const_ptr
    lda #>runtime_name_rt_dbf_deleted
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_headerlen
    sta const_ptr
    lda #>runtime_name_rt_dbf_headerlen
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_recordlen
    sta const_ptr
    lda #>runtime_name_rt_dbf_recordlen
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_totalrecs
    sta const_ptr
    lda #>runtime_name_rt_dbf_totalrecs
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_dbf_currrecno
    sta const_ptr
    lda #>runtime_name_rt_dbf_currrecno
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_mx
    sta const_ptr
    lda #>runtime_name_rt_mx
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_my
    sta const_ptr
    lda #>runtime_name_rt_my
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_mb
    sta const_ptr
    lda #>runtime_name_rt_mb
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_mb1
    sta const_ptr
    lda #>runtime_name_rt_mb1
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_mb2
    sta const_ptr
    lda #>runtime_name_rt_mb2
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_mseen
    sta const_ptr
    lda #>runtime_name_rt_mseen
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_BYTE_READBACK
    clc
    rts
:
    lda #<runtime_name_rt_gfx_bitmap_on
    sta const_ptr
    lda #>runtime_name_rt_gfx_bitmap_on
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_NO_ARG
    clc
    rts
:
    lda #<runtime_name_rt_gfx_bitmap_off
    sta const_ptr
    lda #>runtime_name_rt_gfx_bitmap_off
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_NO_ARG
    clc
    rts
:
    lda #<runtime_name_rt_gfx_mbitmap_on
    sta const_ptr
    lda #>runtime_name_rt_gfx_mbitmap_on
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_NO_ARG
    clc
    rts
:
    lda #<runtime_name_rt_gfx_mbitmap_off
    sta const_ptr
    lda #>runtime_name_rt_gfx_mbitmap_off
    sta const_ptr+1
    ldx linked_external_index
    jsr runtime_external_index_matches_const
    bcs :+
    lda #RUNTIME_HELPER_KIND_NO_ARG
    clc
    rts
:
    sec
    rts

runtime_helper_sequence_validate_current_call:
    lda linked_runtime_helper_kind
    cmp #RUNTIME_HELPER_KIND_SPRITE_DATA
    bne :+
    jmp runtime_helper_sequence_validate_sprite_data
:
    cmp #RUNTIME_HELPER_KIND_SPRITE_POS
    bne :+
    jmp runtime_helper_sequence_validate_sprite_pos
:
    cmp #RUNTIME_HELPER_KIND_GFX_BGCOLOR
    bne :+
    jmp runtime_helper_sequence_validate_gfx_bgcolor
:
    cmp #RUNTIME_HELPER_KIND_SID_FREQ
    bne :+
    jmp runtime_helper_sequence_validate_sid_freq
:
    cmp #RUNTIME_HELPER_KIND_XA_BYTE
    bne :+
    jmp runtime_helper_sequence_validate_xa_byte
:
    cmp #RUNTIME_HELPER_KIND_XY_WORD
    bne :+
    jmp runtime_helper_sequence_validate_xy_word
:
    cmp #RUNTIME_HELPER_KIND_XY_WORD_READBACK
    bne :+
    jmp runtime_helper_sequence_validate_xy_word
:
    cmp #RUNTIME_HELPER_KIND_NO_ARG
    bne :+
    jmp runtime_helper_sequence_validate_no_arg
:
    cmp #RUNTIME_HELPER_KIND_BYTE_READBACK
    bne :+
    jmp runtime_helper_sequence_validate_no_arg
:
    cmp #RUNTIME_HELPER_KIND_A_BYTE
    bne :+
    jmp runtime_helper_sequence_validate_a_byte
:
    cmp #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    bne :+
    jmp runtime_helper_sequence_validate_a_byte
:
    cmp #RUNTIME_HELPER_KIND_AY_BYTE
    bne :+
    jmp runtime_helper_sequence_validate_ay_byte
:
    cmp #RUNTIME_HELPER_KIND_AY_BYTE_READBACK
    bne :+
    jmp runtime_helper_sequence_validate_ay_byte
:
    cmp #RUNTIME_HELPER_KIND_AXY_BYTES_CLC
    bne :+
    jmp runtime_helper_sequence_validate_axy_bytes
:
    cmp #RUNTIME_HELPER_KIND_AXY_BYTES_CLC_READBACK
    bne :+
    jmp runtime_helper_sequence_validate_axy_bytes
:
    cmp #RUNTIME_HELPER_KIND_AXY_E0_BYTES_CLC_READBACK
    bne :+
    jmp runtime_helper_sequence_validate_axy_e0_bytes
:
    cmp #RUNTIME_HELPER_KIND_X1_A0_BYTES
    bne :+
    jmp runtime_helper_sequence_validate_x1_a0_bytes
:
    sec
    rts

runtime_helper_sequence_validate_no_arg:
    lda #$00
    jmp runtime_helper_sequence_require_arg_count

runtime_helper_sequence_validate_a_byte:
    jsr runtime_helper_sequence_pending_a_arg_active
    bcs :+
    lda #$00
    jmp runtime_helper_sequence_require_arg_count
:
    lda #$01
    jsr runtime_helper_sequence_require_arg_count
    bcc :+
    rts
:
    jmp runtime_helper_sequence_arg0_hi_zero

runtime_helper_sequence_validate_ay_byte:
    jsr runtime_helper_sequence_pending_a_arg_active
    bcc runtime_helper_sequence_validate_ay_byte_single_literal_arg
    jsr runtime_helper_sequence_pending_a_arg1_active
    bcs runtime_helper_sequence_validate_ay_byte_literal_args
runtime_helper_sequence_validate_ay_byte_single_literal_arg:
    lda #$01
    jsr runtime_helper_sequence_require_arg_count
    bcc :+
    rts
:
    jmp runtime_helper_sequence_arg0_hi_zero
runtime_helper_sequence_validate_ay_byte_literal_args:
    lda #$02
    jsr runtime_helper_sequence_require_arg_count
    bcc :+
    rts
:
    jsr runtime_helper_sequence_arg0_hi_zero
    bcc :+
    rts
:
    jmp runtime_helper_sequence_arg1_hi_zero

runtime_helper_sequence_validate_axy_bytes:
    jsr runtime_helper_sequence_pending_a_arg_active
    bcc runtime_helper_sequence_validate_axy_bytes_two_literal_args
    jsr runtime_helper_sequence_pending_a_arg1_active
    bcc runtime_helper_sequence_validate_axy_bytes_two_literal_args
    jsr runtime_helper_sequence_pending_a_arg2_active
    bcs runtime_helper_sequence_validate_axy_bytes_literal_args
runtime_helper_sequence_validate_axy_bytes_two_literal_args:
    lda #$02
    jsr runtime_helper_sequence_require_arg_count
    bcc :+
    rts
:
    jsr runtime_helper_sequence_arg0_hi_zero
    bcc :+
    rts
:
    jmp runtime_helper_sequence_arg1_hi_zero
runtime_helper_sequence_validate_axy_bytes_literal_args:
    lda #$03
    jsr runtime_helper_sequence_require_arg_count
    bcc :+
    rts
:
    jsr runtime_helper_sequence_arg0_hi_zero
    bcc :+
    rts
:
    jsr runtime_helper_sequence_arg1_hi_zero
    bcc :+
    rts
:
    jmp runtime_helper_sequence_arg2_hi_zero

runtime_helper_sequence_validate_axy_e0_bytes:
    jsr runtime_helper_sequence_pending_a_arg_active
    bcc runtime_helper_sequence_validate_axy_e0_bytes_pending_arg0
    jsr runtime_helper_sequence_pending_a_arg3_active
    bcc runtime_helper_sequence_validate_axy_e0_bytes_pending_arg3
    lda #$04
    jsr runtime_helper_sequence_require_arg_count
    bcc :+
    rts
:
    jsr runtime_helper_sequence_arg0_hi_zero
    bcc :+
    rts
:
    jsr runtime_helper_sequence_arg1_hi_zero
    bcc :+
    rts
:
    jsr runtime_helper_sequence_arg2_hi_zero
    bcc :+
    rts
:
    jmp runtime_helper_sequence_arg3_hi_zero
runtime_helper_sequence_validate_axy_e0_bytes_pending_arg0:
    lda #$03
    jsr runtime_helper_sequence_require_arg_count
    bcc :+
    rts
:
    jsr runtime_helper_sequence_arg0_hi_zero
    bcc :+
    rts
:
    jsr runtime_helper_sequence_arg1_hi_zero
    bcc :+
    rts
:
    jmp runtime_helper_sequence_arg2_hi_zero
runtime_helper_sequence_validate_axy_e0_bytes_pending_arg3:
    lda #$03
    jsr runtime_helper_sequence_require_arg_count
    bcc :+
    rts
:
    jsr runtime_helper_sequence_arg0_hi_zero
    bcc :+
    rts
:
    jsr runtime_helper_sequence_arg1_hi_zero
    bcc :+
    rts
:
    jmp runtime_helper_sequence_arg2_hi_zero

runtime_helper_sequence_validate_sprite_data:
    jsr runtime_helper_sequence_pending_a_arg_active
    bcs runtime_helper_sequence_validate_sprite_data_arg1
    lda #$01
    jmp runtime_helper_sequence_require_arg_count
runtime_helper_sequence_validate_sprite_data_arg1:
    jsr runtime_helper_sequence_pending_a_arg1_active
    bcs runtime_helper_sequence_validate_sprite_data_literal_args
    lda #$01
    jsr runtime_helper_sequence_require_arg_count
    bcc :+
    rts
:
    jmp runtime_helper_sequence_arg0_hi_zero
runtime_helper_sequence_validate_sprite_data_literal_args:
    lda #$02
    jsr runtime_helper_sequence_require_arg_count
    bcc :+
    rts
:
    jmp runtime_helper_sequence_arg0_hi_zero

runtime_helper_sequence_validate_sprite_pos:
    jsr runtime_helper_sequence_pending_a_arg_active
    bcs runtime_helper_sequence_validate_sprite_pos_arg1
    lda #$02
    jsr runtime_helper_sequence_require_arg_count
    bcc :+
    rts
:
    jsr runtime_helper_sequence_arg0_hi_lt_two
    bcc :+
    rts
:
    jmp runtime_helper_sequence_arg1_hi_zero
runtime_helper_sequence_validate_sprite_pos_arg1:
    jsr runtime_helper_sequence_pending_a_arg1_active
    bcs runtime_helper_sequence_validate_sprite_pos_arg2
    lda #$02
    jsr runtime_helper_sequence_require_arg_count
    bcc :+
    rts
:
    jsr runtime_helper_sequence_arg0_hi_zero
    bcc :+
    rts
:
    jmp runtime_helper_sequence_arg1_hi_zero
runtime_helper_sequence_validate_sprite_pos_arg2:
    jsr runtime_helper_sequence_pending_a_arg2_active
    bcs runtime_helper_sequence_validate_sprite_pos_literal_args
    lda #$02
    jsr runtime_helper_sequence_require_arg_count
    bcc :+
    rts
:
    jsr runtime_helper_sequence_arg0_hi_zero
    bcc :+
    rts
:
    jmp runtime_helper_sequence_arg1_hi_lt_two
runtime_helper_sequence_validate_sprite_pos_literal_args:
    lda #$03
    jsr runtime_helper_sequence_require_arg_count
    bcc :+
    rts
:
    jsr runtime_helper_sequence_arg0_hi_zero
    bcc :+
    rts
:
    jsr runtime_helper_sequence_arg1_hi_lt_two
    bcc :+
    rts
:
    jmp runtime_helper_sequence_arg2_hi_zero

runtime_helper_sequence_validate_gfx_bgcolor:
    jmp runtime_helper_sequence_validate_a_byte

runtime_helper_sequence_validate_sid_freq:
        jsr runtime_helper_sequence_pending_a_arg_active
        bcs runtime_helper_sequence_validate_sid_freq_arg1
        lda #$01
        jmp runtime_helper_sequence_require_arg_count
runtime_helper_sequence_validate_sid_freq_arg1:
        jsr runtime_helper_sequence_pending_a_arg1_active
        bcs runtime_helper_sequence_validate_sid_freq_literal_args
        lda #$01
        jsr runtime_helper_sequence_require_arg_count
        bcc :+
        rts
    :
        jmp runtime_helper_sequence_arg0_hi_zero
runtime_helper_sequence_validate_sid_freq_literal_args:
        lda #$02
        jsr runtime_helper_sequence_require_arg_count
    bcc :+
    rts
    :
        jmp runtime_helper_sequence_arg0_hi_zero

runtime_helper_sequence_validate_xa_byte:
        lda linked_runtime_helper_kind
        cmp #RUNTIME_HELPER_KIND_XA_BYTE
        bne runtime_helper_sequence_validate_xa_byte_literal_args
        jsr runtime_helper_sequence_pending_a_arg_active
        bcc runtime_helper_sequence_validate_xa_byte_single_literal_arg
        jsr runtime_helper_sequence_pending_a_arg1_active
        bcs runtime_helper_sequence_validate_xa_byte_literal_args
runtime_helper_sequence_validate_xa_byte_single_literal_arg:
        lda #$01
        jsr runtime_helper_sequence_require_arg_count
        bcc :+
        rts
    :
        jmp runtime_helper_sequence_arg0_hi_zero
runtime_helper_sequence_validate_xa_byte_literal_args:
        lda #$02
        jsr runtime_helper_sequence_require_arg_count
        bcc :+
        rts
    :
        jsr runtime_helper_sequence_arg0_hi_zero
        bcc :+
        rts
    :
        jmp runtime_helper_sequence_arg1_hi_zero

runtime_helper_sequence_validate_x1_a0_bytes:
        jsr runtime_helper_sequence_pending_a_arg_active
        bcc runtime_helper_sequence_validate_x1_a0_bytes_single_literal_arg
        jsr runtime_helper_sequence_pending_a_arg1_active
        bcs runtime_helper_sequence_validate_x1_a0_bytes_literal_args
runtime_helper_sequence_validate_x1_a0_bytes_single_literal_arg:
        lda #$01
        jsr runtime_helper_sequence_require_arg_count
        bcc :+
        rts
    :
        jmp runtime_helper_sequence_arg0_hi_zero
runtime_helper_sequence_validate_x1_a0_bytes_literal_args:
        jmp runtime_helper_sequence_validate_xa_byte_literal_args

runtime_helper_sequence_validate_xy_word:
        jsr runtime_helper_sequence_pending_a_arg_active
        bcs :+
        lda #$00
        jmp runtime_helper_sequence_require_arg_count
    :
        lda #$01
        jmp runtime_helper_sequence_require_arg_count

runtime_helper_sequence_require_arg_count:
    cmp linked_runtime_arg_count
    beq :+
    sec
    rts
:
    clc
    rts

runtime_helper_sequence_arg0_hi_zero:
    ldx linked_runtime_arg0
    bmi runtime_helper_sequence_hi_ok
    jsr load_linked_literal_window_from_x_or_fail
    lda linked_literal_window+LINKED_LITERAL_HI
    beq runtime_helper_sequence_hi_ok
    sec
    rts
runtime_helper_sequence_arg0_hi_lt_two:
        ldx linked_runtime_arg0
        bmi runtime_helper_sequence_hi_ok
        jsr load_linked_literal_window_from_x_or_fail
        lda linked_literal_window+LINKED_LITERAL_HI
        cmp #$02
        bcc runtime_helper_sequence_hi_ok
        sec
        rts
runtime_helper_sequence_arg1_hi_lt_two:
        ldx linked_runtime_arg1
        bmi runtime_helper_sequence_hi_ok
        jsr load_linked_literal_window_from_x_or_fail
        lda linked_literal_window+LINKED_LITERAL_HI
        cmp #$02
        bcc runtime_helper_sequence_hi_ok
        sec
        rts
runtime_helper_sequence_arg1_hi_zero:
        ldx linked_runtime_arg1
        bmi runtime_helper_sequence_hi_ok
        jsr load_linked_literal_window_from_x_or_fail
        lda linked_literal_window+LINKED_LITERAL_HI
        beq runtime_helper_sequence_hi_ok
        sec
        rts
runtime_helper_sequence_arg2_hi_zero:
        ldx linked_runtime_arg2
        bmi runtime_helper_sequence_hi_ok
        jsr load_linked_literal_window_from_x_or_fail
        lda linked_literal_window+LINKED_LITERAL_HI
    beq runtime_helper_sequence_hi_ok
    sec
    rts
runtime_helper_sequence_arg3_hi_zero:
        ldx linked_runtime_arg3
        bmi runtime_helper_sequence_hi_ok
        jsr load_linked_literal_window_from_x_or_fail
        lda linked_literal_window+LINKED_LITERAL_HI
    beq runtime_helper_sequence_hi_ok
    sec
    rts
runtime_helper_sequence_hi_ok:
    clc
    rts

runtime_helper_sequence_pending_a_arg_active:
    lda linked_runtime_result_pending
    beq runtime_helper_sequence_pending_a_arg_inactive
    lda linked_runtime_result_arg_count
    bne runtime_helper_sequence_pending_a_arg_inactive
    clc
    rts
runtime_helper_sequence_pending_a_arg_inactive:
    sec
    rts

runtime_helper_sequence_pending_a_arg1_active:
    lda linked_runtime_result_pending
    beq runtime_helper_sequence_pending_a_arg1_inactive
    lda linked_runtime_result_arg_count
    cmp #$01
    bne runtime_helper_sequence_pending_a_arg1_inactive
    clc
    rts
runtime_helper_sequence_pending_a_arg1_inactive:
    sec
    rts

runtime_helper_sequence_pending_a_arg2_active:
    lda linked_runtime_result_pending
    beq runtime_helper_sequence_pending_a_arg2_inactive
    lda linked_runtime_result_arg_count
    cmp #$02
    bne runtime_helper_sequence_pending_a_arg2_inactive
    clc
    rts
runtime_helper_sequence_pending_a_arg2_inactive:
    sec
    rts

runtime_helper_sequence_pending_a_arg3_active:
    lda linked_runtime_result_pending
    beq runtime_helper_sequence_pending_a_arg3_inactive
    lda linked_runtime_result_arg_count
    cmp #$03
    bne runtime_helper_sequence_pending_a_arg3_inactive
    clc
    rts
runtime_helper_sequence_pending_a_arg3_inactive:
    sec
    rts

runtime_external_index_matches_const:
    jsr load_external_name_window_from_x_or_fail
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

loaded_external_print_body_is_s0i0r:
    lda #<linked_body_string_int
    sta const_ptr
    lda #>linked_body_string_int
    sta const_ptr+1
    jmp loaded_first_body_matches_const_ptr

loaded_external_print_body_is_M:
    jmp loaded_first_body_is_object_code

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
    lda #$00
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    lda #REAL_PRINT_INT_EXT_LO
    sta linked_next_addr_lo
    lda #REAL_PRINT_INT_EXT_HI
    sta linked_next_addr_hi
    jsr build_object_code_address_table_with_current_next_or_fail
    jsr append_real_print_int_var_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_store_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_print_int_var_ptr_02
    ldx #$01
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_runtime_exit_marker_template
    jsr append_real_print_int_storage
    jmp append_object_code_external_modules_or_fail

build_real_to_int_prg_content_or_fail:
    lda #$00
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    lda #REAL_TO_INT_EXT_LO
    sta linked_next_addr_lo
    lda #REAL_TO_INT_EXT_HI
    sta linked_next_addr_hi
    jsr build_object_code_address_table_with_current_next_or_fail
    jsr append_real_to_int_real_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_store_value
    jsr append_payload_byte
    lda #$A2
    jsr append_payload_byte
    lda linked_store_value_hi
    jsr append_payload_byte
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_to_int_real_ptr_02
    ldx #$01
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_to_int_result_store
    jsr append_runtime_exit_marker_template
    jsr append_real_print_int_storage
    lda #$00
    jsr append_payload_byte
    lda #$00
    jsr append_payload_byte
    jmp append_object_code_external_modules_or_fail

build_input_real_print_int_prg_content_or_fail:
    lda #$00
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    lda #INPUT_REAL_PRINT_INT_EXT_LO
    sta linked_next_addr_lo
    lda #INPUT_REAL_PRINT_INT_EXT_HI
    sta linked_next_addr_hi
    jsr build_object_code_address_table_with_current_next_or_fail
    jsr runtime_helper_sequence_load_ints_or_fail
    lda #$00
    sta linked_runtime_arg_count
    sta linked_runtime_result_pending
    ldx #$00
    jsr runtime_helper_kind_for_external_index_x
    bcc :+
    jmp build_object_code_prg_bad
:
    sta linked_runtime_helper_kind
    lda #$00
    jsr runtime_helper_sequence_store_arg_from_a
    bcc :+
    jmp build_object_code_prg_bad
:
    jsr append_runtime_helper_sequence_current_call_or_fail
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_input_real_print_int_var_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_store_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$01
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_input_real_print_int_var_ptr_02
    ldx #$02
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_runtime_exit_marker_template
    jsr append_real_print_int_storage
    jmp append_object_code_external_modules_or_fail

build_input_stored_real_print_int_prg_content_or_fail:
    lda #$00
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    lda #INPUT_STORED_REAL_PRINT_INT_EXT_LO
    sta linked_next_addr_lo
    lda #INPUT_STORED_REAL_PRINT_INT_EXT_HI
    sta linked_next_addr_hi
    jsr build_object_code_address_table_with_current_next_or_fail
    jsr runtime_helper_sequence_load_ints_or_fail
    lda #$00
    sta linked_runtime_arg_count
    sta linked_runtime_result_pending
    ldx #$00
    jsr runtime_helper_kind_for_external_index_x
    bcc :+
    jmp build_object_code_prg_bad
:
    sta linked_runtime_helper_kind
    lda #$00
    jsr runtime_helper_sequence_store_arg_from_a
    bcc :+
    jmp build_object_code_prg_bad
:
    jsr append_runtime_helper_sequence_current_call_or_fail
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_input_stored_real_print_int_result_store
    jsr append_input_stored_real_print_int_var_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_store_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$01
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_input_stored_real_print_int_var_ptr_02
    ldx #$02
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_runtime_exit_marker_template
    lda #$00
    jsr append_payload_byte
    lda #$00
    jsr append_payload_byte
    jsr append_real_print_int_storage
    jmp append_object_code_external_modules_or_fail

build_real_print_binary_prg_content_or_fail:
    lda #$00
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    lda #REAL_PRINT_BINARY_EXT_LO
    sta linked_next_addr_lo
    lda #REAL_PRINT_BINARY_EXT_HI
    sta linked_next_addr_hi
    jsr build_object_code_address_table_with_current_next_or_fail
    jsr append_real_print_binary_a_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_store_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_print_binary_b_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_binary_rhs_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_print_binary_a_ptr_02
    jsr append_real_print_binary_b_ptr_04
    jsr append_real_print_binary_x_ptr_06
    ldx #$01
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_print_binary_x_ptr_02
    ldx #$02
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_runtime_exit_marker_template
    jsr append_real_print_binary_storage
    jmp append_object_code_external_modules_or_fail

build_real_print_fabs_prg_content_or_fail:
    lda #$00
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    lda #REAL_PRINT_FABS_EXT_LO
    sta linked_next_addr_lo
    lda #REAL_PRINT_FABS_EXT_HI
    sta linked_next_addr_hi
    jsr build_object_code_address_table_with_current_next_or_fail
    jsr append_real_print_fabs_a_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_store_value
    jsr append_payload_byte
    lda #$A2
    jsr append_payload_byte
    lda linked_store_value_hi
    jsr append_payload_byte
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_print_fabs_a_ptr_02
    jsr append_real_print_fabs_x_ptr_06
    ldx #$01
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_print_fabs_x_ptr_02
    ldx #$02
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_runtime_exit_marker_template
    jsr append_real_print_int_storage
    jsr append_real_print_int_storage
    jmp append_object_code_external_modules_or_fail

build_real_if_gt_prg_content_or_fail:
    lda #$00
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    lda linked_condition_is_nested
    beq build_real_if_gt_prg_check_else_module_base
    lda #REAL_IF_GT_NESTED_EXT_LO
    sta linked_next_addr_lo
    lda #REAL_IF_GT_NESTED_EXT_HI
    jmp build_real_if_gt_prg_store_module_base_hi
build_real_if_gt_prg_check_else_module_base:
    lda linked_condition_has_else
    beq build_real_if_gt_prg_use_if_only_module_base
    lda #REAL_IF_GT_ELSE_EXT_LO
    sta linked_next_addr_lo
    lda #REAL_IF_GT_ELSE_EXT_HI
    jmp build_real_if_gt_prg_store_module_base_hi
build_real_if_gt_prg_use_if_only_module_base:
    lda #REAL_IF_GT_EXT_LO
    sta linked_next_addr_lo
    lda #REAL_IF_GT_EXT_HI
build_real_if_gt_prg_store_module_base_hi:
    sta linked_next_addr_hi
    jsr build_object_code_address_table_with_current_next_or_fail
    jsr append_real_if_gt_a_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_store_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_if_gt_b_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_binary_rhs_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_if_gt_a_ptr_02
    jsr append_real_if_gt_b_ptr_04
    ldx #$01
    jsr append_runtime_jsr_to_pending_target_x
    lda linked_condition_is_nested
    beq build_real_if_gt_prg_check_else
    jsr append_real_if_gt_condition_nested_store
    jmp build_real_if_gt_prg_after_condition_store
build_real_if_gt_prg_check_else:
    lda linked_condition_has_else
    beq build_real_if_gt_prg_no_else
    jsr append_real_if_gt_condition_else_store
    jmp build_real_if_gt_prg_after_condition_store
build_real_if_gt_prg_no_else:
    jsr append_real_if_gt_condition_store
build_real_if_gt_prg_after_condition_store:
    jsr append_real_if_gt_y_check_store
    lda #$EA
    jsr append_payload_byte
    lda linked_condition_is_nested
    beq build_real_if_gt_prg_no_nested_align
    lda #$EA
    jsr append_payload_byte
build_real_if_gt_prg_no_nested_align:
    jsr append_runtime_exit_marker_template
    jsr append_real_if_gt_storage
    jmp append_object_code_external_modules_or_fail

build_real_do_until_prg_content_or_fail:
    lda linked_loop_update_uses_real_binary
    beq build_real_do_until_prg_content_once_or_fail
    jmp build_real_do_until_binary_prg_content_or_fail
build_real_do_until_prg_content_once_or_fail:
    lda #$00
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    lda #REAL_DO_UNTIL_EXT_LO
    sta linked_next_addr_lo
    lda #REAL_DO_UNTIL_EXT_HI
    sta linked_next_addr_hi
    jsr build_object_code_address_table_with_current_next_or_fail
    jsr append_real_do_until_a_zero_store
    jsr append_real_if_gt_b_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_binary_rhs_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_if_gt_a_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_store_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_if_gt_a_ptr_02
    jsr append_real_if_gt_b_ptr_04
    ldx #$01
    jsr append_runtime_jsr_to_pending_target_x
    lda #$C9
    jsr append_payload_byte
    lda linked_condition_cmp_value
    jsr append_payload_byte
    lda linked_condition_skip_opcode
    jsr append_payload_byte
    lda #$DA
    jsr append_payload_byte
    lda linked_condition_store_value
    sta current_bit_lo
    jsr append_real_if_gt_y_store_current
    jsr append_real_if_gt_y_check_store
    lda #$EA
    jsr append_payload_byte
    jsr append_runtime_exit_marker_template
    jsr append_real_if_gt_storage
    jmp append_object_code_external_modules_or_fail

build_real_do_until_binary_prg_content_or_fail:
    lda #$00
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    lda #REAL_DO_UNTIL_BINARY_EXT_LO
    sta linked_next_addr_lo
    lda #REAL_DO_UNTIL_BINARY_EXT_HI
    sta linked_next_addr_hi
    jsr build_object_code_address_table_with_current_next_or_fail
    jsr append_real_do_until_binary_a_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_store_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_do_until_binary_b_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_binary_rhs_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_do_until_binary_c_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_loop_update_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_do_until_binary_update_store
    jsr append_real_do_until_binary_a_ptr_02
    jsr append_real_do_until_binary_b_ptr_04
    ldx #$02
    jsr append_runtime_jsr_to_pending_target_x
    lda #$C9
    jsr append_payload_byte
    lda linked_condition_cmp_value
    jsr append_payload_byte
    lda linked_condition_skip_opcode
    jsr append_payload_byte
    lda #$CE
    jsr append_payload_byte
    lda linked_condition_store_value
    sta current_bit_lo
    jsr append_real_do_until_binary_y_store_current
    jsr append_real_do_until_binary_y_check_store
    lda #$EA
    jsr append_payload_byte
    jsr append_runtime_exit_marker_template
    jsr append_real_while_binary_storage
    jmp append_object_code_external_modules_or_fail

build_real_while_prg_content_or_fail:
    lda linked_loop_update_uses_real_binary
    beq build_real_while_prg_content_once_or_fail
    jmp build_real_while_binary_prg_content_or_fail
build_real_while_prg_content_once_or_fail:
    lda #$00
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    lda #REAL_WHILE_EXT_LO
    clc
    adc linked_loop_update_uses_conversion
    sta linked_next_addr_lo
    lda #REAL_WHILE_EXT_HI
    sta linked_next_addr_hi
    jsr build_object_code_address_table_with_current_next_or_fail
    jsr append_real_while_a_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_store_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_while_b_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_binary_rhs_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_while_a_ptr_02
    jsr append_real_while_b_ptr_04
    ldx #$01
    jsr append_runtime_jsr_to_pending_target_x
    lda #$C9
    jsr append_payload_byte
    lda linked_condition_cmp_value
    jsr append_payload_byte
    lda linked_condition_skip_opcode
    jsr append_payload_byte
    lda #$1B
    clc
    adc linked_loop_update_uses_conversion
    jsr append_payload_byte
    lda linked_condition_store_value
    sta current_bit_lo
    jsr append_real_while_y_store_current
    lda linked_condition_body_op
    cmp #'l'
    beq build_real_while_prg_content_update_b
    jsr append_real_while_a_update_store
    jmp build_real_while_prg_content_update_done
build_real_while_prg_content_update_b:
    jsr append_real_while_b_update_store
build_real_while_prg_content_update_done:
    lda #$4C
    jsr append_payload_byte
    lda #$1E
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    jsr append_real_while_y_check_store
    lda #$EA
    jsr append_payload_byte
    jsr append_runtime_exit_marker_template
    jsr append_real_if_gt_storage
    jmp append_object_code_external_modules_or_fail

build_real_while_binary_prg_content_or_fail:
    lda #$00
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    lda #REAL_WHILE_BINARY_EXT_LO
    sta linked_next_addr_lo
    lda #REAL_WHILE_BINARY_EXT_HI
    sta linked_next_addr_hi
    jsr build_object_code_address_table_with_current_next_or_fail
    jsr append_real_while_a_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_store_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_while_b_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_binary_rhs_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_while_c_ptr_02
    lda #$A9
    jsr append_payload_byte
    lda linked_loop_update_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    jsr append_real_while_a_ptr_02
    jsr append_real_while_b_ptr_04
    ldx #$01
    jsr append_runtime_jsr_to_pending_target_x
    lda #$C9
    jsr append_payload_byte
    lda linked_condition_cmp_value
    jsr append_payload_byte
    lda linked_condition_skip_opcode
    jsr append_payload_byte
    lda #$28
    jsr append_payload_byte
    lda linked_condition_store_value
    sta current_bit_lo
    jsr append_real_while_y_store_current
    jsr append_real_while_binary_update_store
    lda #$4C
    jsr append_payload_byte
    lda #$2D
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    jsr append_real_while_y_check_store
    lda #$EA
    jsr append_payload_byte
    jsr append_runtime_exit_marker_template
    jsr append_real_while_binary_storage
    jmp append_object_code_external_modules_or_fail

append_real_do_until_a_zero_store:
    lda #$A9
    jsr append_payload_byte
    lda #$00
    jsr append_payload_byte
    jsr set_real_if_gt_a_addr_current
    jsr append_sta_current_addr
    jsr inc_current_addr
    jsr append_sta_current_addr
    jsr inc_current_addr
    jsr append_sta_current_addr
    jsr inc_current_addr
    jmp append_sta_current_addr

append_real_while_a_update_store:
    lda linked_loop_update_uses_conversion
    beq append_real_while_a_update_store_raw
    jsr append_real_while_a_ptr_02
    jmp append_real_while_convert_update_store
append_real_while_a_update_store_raw:
    lda #$A9
    jsr append_payload_byte
    lda linked_loop_update_value
    jsr append_payload_byte
    jsr set_real_while_a_addr_current
    jsr append_sta_current_addr
    jsr inc_current_addr
    jsr append_sta_current_addr
    jsr inc_current_addr
    jsr append_sta_current_addr
    jsr inc_current_addr
    jmp append_sta_current_addr

append_real_while_b_update_store:
    lda linked_loop_update_uses_conversion
    beq append_real_while_b_update_store_raw
    jsr append_real_while_b_ptr_02
    jmp append_real_while_convert_update_store
append_real_while_b_update_store_raw:
    lda #$A9
    jsr append_payload_byte
    lda linked_loop_update_value
    jsr append_payload_byte
    jsr set_real_while_b_addr_current
    jsr append_sta_current_addr
    jsr inc_current_addr
    jsr append_sta_current_addr
    jsr inc_current_addr
    jsr append_sta_current_addr
    jsr inc_current_addr
    jmp append_sta_current_addr

append_real_while_convert_update_store:
    lda #$A9
    jsr append_payload_byte
    lda linked_loop_update_value
    jsr append_payload_byte
    jsr append_ldx_zero
    ldx #$00
    jmp append_runtime_jsr_to_pending_target_x

append_real_while_binary_update_store:
    jsr append_real_while_a_ptr_02
    jsr append_real_while_c_ptr_04
    jsr append_real_while_a_ptr_06
    ldx #$02
    jmp append_runtime_jsr_to_pending_target_x

append_real_do_until_binary_update_store:
    jsr append_real_do_until_binary_a_ptr_02
    jsr append_real_do_until_binary_c_ptr_04
    jsr append_real_do_until_binary_a_ptr_06
    ldx #$01
    jmp append_runtime_jsr_to_pending_target_x

append_sta_current_addr:
    lda #$8D
    jsr append_payload_byte
    lda current_bit_lo
    jsr append_payload_byte
    lda current_bit_hi
    jmp append_payload_byte

inc_current_addr:
    inc current_bit_lo
    bne :+
    inc current_bit_hi
:   rts

append_real_if_gt_condition_store:
    lda #$C9
    jsr append_payload_byte
    lda linked_condition_cmp_value
    jsr append_payload_byte
    lda linked_condition_skip_opcode
    jsr append_payload_byte
    lda #$0A
    jsr append_payload_byte
    lda linked_condition_store_value
    sta current_bit_lo
    jmp append_real_if_gt_y_store_current

append_real_if_gt_condition_nested_store:
    lda #$C9
    jsr append_payload_byte
    lda linked_condition_cmp_value
    jsr append_payload_byte
    lda linked_condition_skip_opcode
    jsr append_payload_byte
    lda #$21
    jsr append_payload_byte
    jsr append_real_if_gt_a_ptr_02
    jsr append_real_if_gt_b_ptr_04
    ldx #$01
    jsr append_runtime_jsr_to_pending_target_x
    jmp append_real_if_gt_condition_store

append_real_if_gt_condition_else_store:
    lda #$C9
    jsr append_payload_byte
    lda linked_condition_cmp_value
    jsr append_payload_byte
    lda linked_condition_skip_opcode
    jsr append_payload_byte
    lda #$0E
    jsr append_payload_byte
    lda linked_condition_store_value
    sta current_bit_lo
    jsr append_real_if_gt_y_store_current
    lda #$A9
    jsr append_payload_byte
    lda #$01
    jsr append_payload_byte
    lda #$D0
    jsr append_payload_byte
    lda #$0A
    jsr append_payload_byte
    lda linked_condition_else_value
    sta current_bit_lo
    jmp append_real_if_gt_y_store_current

append_real_if_gt_y_store_current:
    lda #$A9
    jsr append_payload_byte
    lda current_bit_lo
    jsr append_payload_byte
    jsr append_ldx_zero
    lda #$8D
    jsr append_payload_byte
    jsr set_real_if_gt_y_addr_current
    lda current_bit_lo
    jsr append_payload_byte
    lda current_bit_hi
    jsr append_payload_byte
    lda #$8E
    jsr append_payload_byte
    jsr set_real_if_gt_y_addr_current
    lda current_bit_lo
    clc
    adc #$01
    jsr append_payload_byte
    lda current_bit_hi
    jmp append_payload_byte

append_real_if_gt_y_check_store:
    lda #$AD
    jsr append_payload_byte
    jsr set_real_if_gt_y_addr_current
    lda current_bit_lo
    jsr append_payload_byte
    lda current_bit_hi
    jsr append_payload_byte
    lda #$AE
    jsr append_payload_byte
    jsr set_real_if_gt_y_addr_current
    lda current_bit_lo
    clc
    adc #$01
    jsr append_payload_byte
    lda current_bit_hi
    jsr append_payload_byte
    lda #$8D
    jsr append_payload_byte
    lda #$D1
    jsr append_payload_byte
    lda #$03
    jsr append_payload_byte
    lda #$8E
    jsr append_payload_byte
    lda #$D2
    jsr append_payload_byte
    lda #$03
    jmp append_payload_byte

append_ldx_zero:
    lda #$A2
    jsr append_payload_byte
    lda #$00
    jmp append_payload_byte

append_runtime_exit_marker_template:
    lda #<runtime_helper_prg_exit_template
    sta const_ptr
    lda #>runtime_helper_prg_exit_template
    sta const_ptr+1
    lda #<(runtime_helper_prg_exit_template_end - runtime_helper_prg_exit_template)
    sta current_bit_lo
    lda #>(runtime_helper_prg_exit_template_end - runtime_helper_prg_exit_template)
    sta current_bit_hi
    jmp copy_direct_prg_template

append_real_print_int_var_ptr_02:
    lda #$02
    sta compare_char
    lda #REAL_PRINT_INT_VAR_LO
    sta current_bit_lo
    lda #REAL_PRINT_INT_VAR_HI
    sta current_bit_hi
    jmp append_immediate_word_to_zp

append_real_to_int_real_ptr_02:
    lda #$02
    sta compare_char
    lda #REAL_TO_INT_REAL_LO
    sta current_bit_lo
    lda #REAL_TO_INT_REAL_HI
    sta current_bit_hi
    jmp append_immediate_word_to_zp

append_real_to_int_result_store:
    lda #$8D
    jsr append_payload_byte
    lda #REAL_TO_INT_INT_LO
    jsr append_payload_byte
    lda #REAL_TO_INT_INT_HI
    jsr append_payload_byte
    lda #$8E
    jsr append_payload_byte
    lda #REAL_TO_INT_INT_LO + 1
    jsr append_payload_byte
    lda #REAL_TO_INT_INT_HI
    jmp append_payload_byte

append_input_real_print_int_var_ptr_02:
    lda #$02
    sta compare_char
    lda #INPUT_REAL_PRINT_INT_VAR_LO
    sta current_bit_lo
    lda #INPUT_REAL_PRINT_INT_VAR_HI
    sta current_bit_hi
    jmp append_immediate_word_to_zp

append_input_stored_real_print_int_result_store:
    lda #$8D
    jsr append_payload_byte
    lda #INPUT_STORED_REAL_PRINT_INT_STORE_LO
    jsr append_payload_byte
    lda #INPUT_STORED_REAL_PRINT_INT_STORE_HI
    jsr append_payload_byte
    lda #$A9
    jsr append_payload_byte
    lda #$00
    jsr append_payload_byte
    lda #$8D
    jsr append_payload_byte
    lda #$38
    jsr append_payload_byte
    lda #INPUT_STORED_REAL_PRINT_INT_STORE_HI
    jmp append_payload_byte

append_input_stored_real_print_int_var_ptr_02:
    lda #$02
    sta compare_char
    lda #INPUT_STORED_REAL_PRINT_INT_VAR_LO
    sta current_bit_lo
    lda #INPUT_STORED_REAL_PRINT_INT_VAR_HI
    sta current_bit_hi
    jmp append_immediate_word_to_zp

append_real_print_binary_a_ptr_02:
    lda #$02
    sta compare_char
    lda #REAL_PRINT_BINARY_A_LO
    sta current_bit_lo
    lda #REAL_PRINT_BINARY_A_HI
    sta current_bit_hi
    jmp append_immediate_word_to_zp

append_real_print_binary_b_ptr_02:
    lda #$02
    sta compare_char
    lda #REAL_PRINT_BINARY_B_LO
    sta current_bit_lo
    lda #REAL_PRINT_BINARY_B_HI
    sta current_bit_hi
    jmp append_immediate_word_to_zp

append_real_print_binary_b_ptr_04:
    lda #$04
    sta compare_char
    lda #REAL_PRINT_BINARY_B_LO
    sta current_bit_lo
    lda #REAL_PRINT_BINARY_B_HI
    sta current_bit_hi
    jmp append_immediate_word_to_zp

append_real_print_binary_x_ptr_02:
    lda #$02
    sta compare_char
    lda #REAL_PRINT_BINARY_X_LO
    sta current_bit_lo
    lda #REAL_PRINT_BINARY_X_HI
    sta current_bit_hi
    jmp append_immediate_word_to_zp

append_real_print_binary_x_ptr_06:
    lda #$06
    sta compare_char
    lda #REAL_PRINT_BINARY_X_LO
    sta current_bit_lo
    lda #REAL_PRINT_BINARY_X_HI
    sta current_bit_hi
    jmp append_immediate_word_to_zp

append_real_print_fabs_a_ptr_02:
    lda #$02
    sta compare_char
    lda #REAL_PRINT_FABS_A_LO
    sta current_bit_lo
    lda #REAL_PRINT_FABS_A_HI
    sta current_bit_hi
    jmp append_immediate_word_to_zp

append_real_print_fabs_x_ptr_02:
    lda #$02
    sta compare_char
    lda #REAL_PRINT_FABS_X_LO
    sta current_bit_lo
    lda #REAL_PRINT_FABS_X_HI
    sta current_bit_hi
    jmp append_immediate_word_to_zp

append_real_print_fabs_x_ptr_06:
    lda #$06
    sta compare_char
    lda #REAL_PRINT_FABS_X_LO
    sta current_bit_lo
    lda #REAL_PRINT_FABS_X_HI
    sta current_bit_hi
    jmp append_immediate_word_to_zp

append_real_if_gt_a_ptr_02:
    lda #$02
    sta compare_char
    jsr set_real_if_gt_a_addr_current
    jmp append_immediate_word_to_zp

append_real_if_gt_b_ptr_02:
    lda #$02
    sta compare_char
    jsr set_real_if_gt_b_addr_current
    jmp append_immediate_word_to_zp

append_real_if_gt_b_ptr_04:
    lda #$04
    sta compare_char
    jsr set_real_if_gt_b_addr_current
    jmp append_immediate_word_to_zp

append_real_while_a_ptr_02:
    lda #$02
    sta compare_char
    jsr set_real_while_a_addr_current
    jmp append_immediate_word_to_zp

append_real_while_a_ptr_06:
    lda #$06
    sta compare_char
    jsr set_real_while_a_addr_current
    jmp append_immediate_word_to_zp

append_real_while_b_ptr_02:
    lda #$02
    sta compare_char
    jsr set_real_while_b_addr_current
    jmp append_immediate_word_to_zp

append_real_while_b_ptr_04:
    lda #$04
    sta compare_char
    jsr set_real_while_b_addr_current
    jmp append_immediate_word_to_zp

append_real_while_c_ptr_02:
    lda #$02
    sta compare_char
    jsr set_real_while_c_addr_current
    jmp append_immediate_word_to_zp

append_real_while_c_ptr_04:
    lda #$04
    sta compare_char
    jsr set_real_while_c_addr_current
    jmp append_immediate_word_to_zp

append_real_while_y_store_current:
    lda #$A9
    jsr append_payload_byte
    lda current_bit_lo
    jsr append_payload_byte
    jsr append_ldx_zero
    lda #$8D
    jsr append_payload_byte
    jsr set_real_while_y_addr_current
    lda current_bit_lo
    jsr append_payload_byte
    lda current_bit_hi
    jsr append_payload_byte
    lda #$8E
    jsr append_payload_byte
    jsr set_real_while_y_addr_current
    lda current_bit_lo
    clc
    adc #$01
    jsr append_payload_byte
    lda current_bit_hi
    jmp append_payload_byte

append_real_while_y_check_store:
    lda #$AD
    jsr append_payload_byte
    jsr set_real_while_y_addr_current
    lda current_bit_lo
    jsr append_payload_byte
    lda current_bit_hi
    jsr append_payload_byte
    lda #$AE
    jsr append_payload_byte
    jsr set_real_while_y_addr_current
    lda current_bit_lo
    clc
    adc #$01
    jsr append_payload_byte
    lda current_bit_hi
    jsr append_payload_byte
    lda #$8D
    jsr append_payload_byte
    lda #$D1
    jsr append_payload_byte
    lda #$03
    jsr append_payload_byte
    lda #$8E
    jsr append_payload_byte
    lda #$D2
    jsr append_payload_byte
    lda #$03
    jmp append_payload_byte

append_real_do_until_binary_a_ptr_02:
    lda #$02
    sta compare_char
    jsr set_real_do_until_binary_a_addr_current
    jmp append_immediate_word_to_zp

append_real_do_until_binary_a_ptr_06:
    lda #$06
    sta compare_char
    jsr set_real_do_until_binary_a_addr_current
    jmp append_immediate_word_to_zp

append_real_do_until_binary_b_ptr_02:
    lda #$02
    sta compare_char
    jsr set_real_do_until_binary_b_addr_current
    jmp append_immediate_word_to_zp

append_real_do_until_binary_b_ptr_04:
    lda #$04
    sta compare_char
    jsr set_real_do_until_binary_b_addr_current
    jmp append_immediate_word_to_zp

append_real_do_until_binary_c_ptr_02:
    lda #$02
    sta compare_char
    jsr set_real_do_until_binary_c_addr_current
    jmp append_immediate_word_to_zp

append_real_do_until_binary_c_ptr_04:
    lda #$04
    sta compare_char
    jsr set_real_do_until_binary_c_addr_current
    jmp append_immediate_word_to_zp

append_real_do_until_binary_y_store_current:
    lda #$A9
    jsr append_payload_byte
    lda current_bit_lo
    jsr append_payload_byte
    jsr append_ldx_zero
    lda #$8D
    jsr append_payload_byte
    jsr set_real_do_until_binary_y_addr_current
    lda current_bit_lo
    jsr append_payload_byte
    lda current_bit_hi
    jsr append_payload_byte
    lda #$8E
    jsr append_payload_byte
    jsr set_real_do_until_binary_y_addr_current
    lda current_bit_lo
    clc
    adc #$01
    jsr append_payload_byte
    lda current_bit_hi
    jmp append_payload_byte

append_real_do_until_binary_y_check_store:
    lda #$AD
    jsr append_payload_byte
    jsr set_real_do_until_binary_y_addr_current
    lda current_bit_lo
    jsr append_payload_byte
    lda current_bit_hi
    jsr append_payload_byte
    lda #$AE
    jsr append_payload_byte
    jsr set_real_do_until_binary_y_addr_current
    lda current_bit_lo
    clc
    adc #$01
    jsr append_payload_byte
    lda current_bit_hi
    jsr append_payload_byte
    lda #$8D
    jsr append_payload_byte
    lda #$D1
    jsr append_payload_byte
    lda #$03
    jsr append_payload_byte
    lda #$8E
    jsr append_payload_byte
    lda #$D2
    jsr append_payload_byte
    lda #$03
    jmp append_payload_byte

set_real_do_until_binary_a_addr_current:
    lda #REAL_DO_UNTIL_BINARY_A_LO
    sta current_bit_lo
    lda #REAL_DO_UNTIL_BINARY_A_HI
    sta current_bit_hi
    rts

set_real_do_until_binary_b_addr_current:
    lda #REAL_DO_UNTIL_BINARY_B_LO
    sta current_bit_lo
    lda #REAL_DO_UNTIL_BINARY_B_HI
    sta current_bit_hi
    rts

set_real_do_until_binary_c_addr_current:
    lda #REAL_DO_UNTIL_BINARY_C_LO
    sta current_bit_lo
    lda #REAL_DO_UNTIL_BINARY_C_HI
    sta current_bit_hi
    rts

set_real_do_until_binary_y_addr_current:
    lda #REAL_DO_UNTIL_BINARY_Y_LO
    sta current_bit_lo
    lda #REAL_DO_UNTIL_BINARY_Y_HI
    sta current_bit_hi
    rts

set_real_while_a_addr_current:
    lda linked_loop_update_uses_real_binary
    beq :+
    lda #REAL_WHILE_BINARY_A_LO
    sta current_bit_lo
    lda #REAL_WHILE_BINARY_A_HI
    sta current_bit_hi
    rts
:
    lda #REAL_WHILE_A_LO
    clc
    adc linked_loop_update_uses_conversion
    sta current_bit_lo
    lda #REAL_WHILE_A_HI
    sta current_bit_hi
    rts

set_real_while_b_addr_current:
    lda linked_loop_update_uses_real_binary
    beq :+
    lda #REAL_WHILE_BINARY_B_LO
    sta current_bit_lo
    lda #REAL_WHILE_BINARY_B_HI
    sta current_bit_hi
    rts
:
    lda #REAL_WHILE_B_LO
    clc
    adc linked_loop_update_uses_conversion
    sta current_bit_lo
    lda #REAL_WHILE_B_HI
    sta current_bit_hi
    rts

set_real_while_y_addr_current:
    lda linked_loop_update_uses_real_binary
    beq :+
    lda #REAL_WHILE_BINARY_Y_LO
    sta current_bit_lo
    lda #REAL_WHILE_BINARY_Y_HI
    sta current_bit_hi
    rts
:
    lda #REAL_WHILE_Y_LO
    clc
    adc linked_loop_update_uses_conversion
    sta current_bit_lo
    lda #REAL_WHILE_Y_HI
    sta current_bit_hi
    rts

set_real_while_c_addr_current:
    lda #REAL_WHILE_BINARY_C_LO
    sta current_bit_lo
    lda #REAL_WHILE_BINARY_C_HI
    sta current_bit_hi
    rts

set_real_if_gt_a_addr_current:
    lda linked_condition_is_nested
    beq :+
    lda #REAL_IF_GT_NESTED_A_LO
    sta current_bit_lo
    lda #REAL_IF_GT_NESTED_A_HI
    sta current_bit_hi
    rts
:   lda linked_condition_is_loop
    beq :+
    lda #REAL_DO_UNTIL_A_LO
    sta current_bit_lo
    lda #REAL_DO_UNTIL_A_HI
    sta current_bit_hi
    rts
:   lda linked_condition_has_else
    beq :+
    lda #REAL_IF_GT_ELSE_A_LO
    sta current_bit_lo
    lda #REAL_IF_GT_ELSE_A_HI
    sta current_bit_hi
    rts
:   lda #REAL_IF_GT_A_LO
    sta current_bit_lo
    lda #REAL_IF_GT_A_HI
    sta current_bit_hi
    rts

set_real_if_gt_b_addr_current:
    lda linked_condition_is_nested
    beq :+
    lda #REAL_IF_GT_NESTED_B_LO
    sta current_bit_lo
    lda #REAL_IF_GT_NESTED_B_HI
    sta current_bit_hi
    rts
:   lda linked_condition_is_loop
    beq :+
    lda #REAL_DO_UNTIL_B_LO
    sta current_bit_lo
    lda #REAL_DO_UNTIL_B_HI
    sta current_bit_hi
    rts
:   lda linked_condition_has_else
    beq :+
    lda #REAL_IF_GT_ELSE_B_LO
    sta current_bit_lo
    lda #REAL_IF_GT_ELSE_B_HI
    sta current_bit_hi
    rts
:   lda #REAL_IF_GT_B_LO
    sta current_bit_lo
    lda #REAL_IF_GT_B_HI
    sta current_bit_hi
    rts

set_real_if_gt_y_addr_current:
    lda linked_condition_is_nested
    beq :+
    lda #REAL_IF_GT_NESTED_Y_LO
    sta current_bit_lo
    lda #REAL_IF_GT_NESTED_Y_HI
    sta current_bit_hi
    rts
:   lda linked_condition_is_loop
    beq :+
    lda #REAL_DO_UNTIL_Y_LO
    sta current_bit_lo
    lda #REAL_DO_UNTIL_Y_HI
    sta current_bit_hi
    rts
:   lda linked_condition_has_else
    beq :+
    lda #REAL_IF_GT_ELSE_Y_LO
    sta current_bit_lo
    lda #REAL_IF_GT_ELSE_Y_HI
    sta current_bit_hi
    rts
:   lda #REAL_IF_GT_Y_LO
    sta current_bit_lo
    lda #REAL_IF_GT_Y_HI
    sta current_bit_hi
    rts

append_immediate_word_to_zp:
    lda #$A9
    jsr append_payload_byte
    lda current_bit_lo
    jsr append_payload_byte
    lda #$85
    jsr append_payload_byte
    lda compare_char
    jsr append_payload_byte
    lda #$A9
    jsr append_payload_byte
    lda current_bit_hi
    jsr append_payload_byte
    lda #$85
    jsr append_payload_byte
    lda compare_char
    clc
    adc #$01
    jmp append_payload_byte

append_real_print_int_storage:
    lda #$00
    jsr append_payload_byte
    lda #$00
    jsr append_payload_byte
    lda #$00
    jsr append_payload_byte
    lda #$00
    jmp append_payload_byte

append_real_print_binary_storage:
    jsr append_real_print_int_storage
    jsr append_real_print_int_storage
    jmp append_real_print_int_storage

append_real_if_gt_storage:
    jsr append_real_print_int_storage
    jsr append_real_print_int_storage
    lda #$00
    jsr append_payload_byte
    lda #$00
    jmp append_payload_byte

append_real_while_binary_storage:
    jsr append_real_print_int_storage
    jsr append_real_print_int_storage
    jsr append_real_print_int_storage
    lda #$00
    jsr append_payload_byte
    lda #$00
    jmp append_payload_byte

build_runtime_helper_condition_prg_content_or_fail:
    lda #$00
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    lda linked_runtime_arg2
    beq build_runtime_helper_condition_load_noarg
    jsr load_runtime_helper_condition_literals_or_fail
    bcc :+
    jmp build_object_code_prg_bad
:
    jmp build_runtime_helper_condition_loaded
build_runtime_helper_condition_load_noarg:
    jsr load_runtime_helper_condition_noarg_literals_or_fail
    bcc :+
    jmp build_object_code_prg_bad
:
build_runtime_helper_condition_loaded:
    lda linked_runtime_arg2
    beq build_runtime_helper_condition_noarg_root_len
    lda #$1E
    sta linked_next_addr_lo
    lda #$10
    sta linked_next_addr_hi
    jmp build_runtime_helper_condition_address_table
build_runtime_helper_condition_noarg_root_len:
    lda #$1C
    sta linked_next_addr_lo
    lda #$10
    sta linked_next_addr_hi
build_runtime_helper_condition_address_table:
    jsr build_object_code_address_table_with_current_next_or_fail
    lda linked_runtime_arg2
    beq build_runtime_helper_condition_readback_call
    lda #$A9
    jsr append_payload_byte
    lda linked_runtime_arg0
    jsr append_payload_byte
build_runtime_helper_condition_readback_call:
    ldx #$00
    jsr append_runtime_jsr_to_pending_target_x
    lda #$C9
    jsr append_payload_byte
    lda linked_condition_cmp_value
    jsr append_payload_byte
    lda linked_condition_skip_opcode
    jsr append_payload_byte
    lda #$05
    jsr append_payload_byte
    lda #$A9
    jsr append_payload_byte
    lda linked_runtime_arg1
    jsr append_payload_byte
    ldx #$01
    jsr append_runtime_jsr_to_pending_target_x
    lda #<runtime_helper_prg_exit_template
    sta const_ptr
    lda #>runtime_helper_prg_exit_template
    sta const_ptr+1
    lda #<(runtime_helper_prg_exit_template_end - runtime_helper_prg_exit_template)
    sta current_bit_lo
    lda #>(runtime_helper_prg_exit_template_end - runtime_helper_prg_exit_template)
    sta current_bit_hi
    jsr copy_direct_prg_template
    jmp append_object_code_external_modules_or_fail

build_runtime_helper_sequence_prg_content_or_fail:
    lda #$00
    jsr append_payload_byte
    lda #$10
    jsr append_payload_byte
    jsr runtime_helper_sequence_compute_next_addr_or_fail
    jsr runtime_helper_sequence_capture_store_addr
    jsr build_object_code_address_table_with_current_next_or_fail
    jsr runtime_helper_sequence_load_ints_or_fail
    jsr runtime_helper_sequence_reset_body_parse
build_runtime_helper_sequence_prg_loop:
    ldy linked_runtime_body_pos
    lda (body_ptr),y
    cmp #'p'
    beq build_runtime_helper_sequence_prg_param
    cmp #'u'
    beq build_runtime_helper_sequence_prg_call
    cmp #'L'
    bne :+
    jmp build_runtime_helper_sequence_prg_load
:
    cmp #'S'
    bne :+
    jmp build_runtime_helper_sequence_prg_store
:
    cmp #'a'
    bne :+
    jmp build_runtime_helper_sequence_prg_add
:
    cmp #'r'
    bne :+
    jmp build_runtime_helper_sequence_prg_return
:
    jmp build_object_code_prg_bad
build_runtime_helper_sequence_prg_param:
    iny
    lda (body_ptr),y
    jsr object_code_import_index_from_a
    bcc :+
    jmp build_object_code_prg_bad
:
    iny
    sty linked_runtime_body_pos
    jsr runtime_helper_sequence_store_arg_from_a
    bcc :+
    jmp build_object_code_prg_bad
:
    jmp build_runtime_helper_sequence_prg_loop
build_runtime_helper_sequence_prg_call:
    iny
    lda (body_ptr),y
    jsr object_code_import_index_from_a
    bcc :+
    jmp build_object_code_prg_bad
:
    sta linked_external_index
    iny
    sty linked_runtime_body_pos
    tax
    jsr runtime_helper_kind_for_external_index_x
    bcc :+
    jmp build_object_code_prg_bad
:
    sta linked_runtime_helper_kind
    jsr runtime_helper_sequence_validate_current_call
    bcc :+
    jmp build_object_code_prg_bad
:
    jsr append_runtime_helper_sequence_current_call_or_fail
    ldx linked_external_index
    jsr append_runtime_jsr_to_pending_target_x
    lda #$00
    sta linked_runtime_arg_count
    jsr runtime_helper_sequence_update_result_pending
    jmp build_runtime_helper_sequence_prg_loop
build_runtime_helper_sequence_prg_store:
    iny
    lda (body_ptr),y
    jsr object_code_import_index_from_a
    bcc :+
    jmp build_object_code_prg_bad
:
    pha
    iny
    sty linked_runtime_body_pos
    jsr append_runtime_helper_sequence_lda_pending_low
    pla
    jsr runtime_helper_sequence_note_store_or_fail
    bcc :+
    jmp build_object_code_prg_bad
:
    ldx linked_runtime_store_count
    dex
    jsr load_linked_runtime_store_window_from_x_or_fail
    lda linked_runtime_store_window+RUNTIME_STORE_LITERAL
    cmp #$FF
    bne :+
    jsr append_runtime_helper_sequence_result_store_or_fail
:
    jmp build_runtime_helper_sequence_prg_loop
build_runtime_helper_sequence_prg_load:
    iny
    lda (body_ptr),y
    jsr object_code_import_index_from_a
    bcc :+
    jmp build_object_code_prg_bad
:
    iny
    sty linked_runtime_body_pos
    jsr runtime_helper_sequence_note_load_or_fail
    bcc :+
    jmp build_object_code_prg_bad
:
    jmp build_runtime_helper_sequence_prg_loop
build_runtime_helper_sequence_prg_add:
    iny
    sty linked_runtime_body_pos
    jsr runtime_helper_sequence_fold_add_or_fail
    bcc :+
    jmp build_object_code_prg_bad
:
    jmp build_runtime_helper_sequence_prg_loop
build_runtime_helper_sequence_prg_return:
    lda #<runtime_helper_prg_exit_template
    sta const_ptr
    lda #>runtime_helper_prg_exit_template
    sta const_ptr+1
    lda #<(runtime_helper_prg_exit_template_end - runtime_helper_prg_exit_template)
    sta current_bit_lo
    lda #>(runtime_helper_prg_exit_template_end - runtime_helper_prg_exit_template)
    sta current_bit_hi
    jsr copy_direct_prg_template
    jsr append_runtime_helper_sequence_storage_if_needed
    jmp append_object_code_external_modules_or_fail

runtime_helper_sequence_compute_next_addr_or_fail:
    jsr runtime_helper_sequence_load_ints_or_fail
    lda #$00
    sta linked_next_addr_lo
    lda #$10
    sta linked_next_addr_hi
    jsr runtime_helper_sequence_reset_body_parse
runtime_helper_sequence_compute_loop:
    ldy linked_runtime_body_pos
    lda (body_ptr),y
    cmp #'p'
    beq runtime_helper_sequence_compute_param
    cmp #'u'
    beq runtime_helper_sequence_compute_call
    cmp #'L'
    bne :+
    jmp runtime_helper_sequence_compute_load
:
    cmp #'S'
    bne :+
    jmp runtime_helper_sequence_compute_store
:
    cmp #'a'
    bne :+
    jmp runtime_helper_sequence_compute_add
:
    cmp #'r'
    bne :+
    jmp runtime_helper_sequence_compute_return
:
    jmp build_object_code_prg_bad
runtime_helper_sequence_compute_param:
    iny
    lda (body_ptr),y
    jsr object_code_import_index_from_a
    bcc :+
    jmp build_object_code_prg_bad
:
    iny
    sty linked_runtime_body_pos
    jsr runtime_helper_sequence_store_arg_from_a
    bcc :+
    jmp build_object_code_prg_bad
:
    jmp runtime_helper_sequence_compute_loop
runtime_helper_sequence_compute_call:
    iny
    lda (body_ptr),y
    jsr object_code_import_index_from_a
    bcc :+
    jmp build_object_code_prg_bad
:
    sta linked_external_index
    iny
    sty linked_runtime_body_pos
    ldx linked_external_index
    jsr runtime_helper_kind_for_external_index_x
    bcc :+
    jmp build_object_code_prg_bad
:
    sta linked_runtime_helper_kind
    jsr runtime_helper_sequence_validate_current_call
    bcc :+
    jmp build_object_code_prg_bad
:
    jsr runtime_helper_sequence_add_current_call_length
    lda #$00
    sta linked_runtime_arg_count
    jsr runtime_helper_sequence_update_result_pending
    jmp runtime_helper_sequence_compute_loop
runtime_helper_sequence_compute_store:
    iny
    lda (body_ptr),y
    jsr object_code_import_index_from_a
    bcc :+
    jmp build_object_code_prg_bad
:
    pha
    iny
    sty linked_runtime_body_pos
    jsr runtime_helper_sequence_add_pending_loaded_len
    pla
    jsr runtime_helper_sequence_note_store_or_fail
    bcc :+
    jmp build_object_code_prg_bad
:
    ldx linked_runtime_store_count
    dex
    jsr load_linked_runtime_store_window_from_x_or_fail
    lda linked_runtime_store_window+RUNTIME_STORE_LITERAL
    cmp #$FF
    bne :+
    lda #$08
    jsr runtime_helper_sequence_add_a_to_next_addr
:
    jmp runtime_helper_sequence_compute_loop
runtime_helper_sequence_compute_load:
    iny
    lda (body_ptr),y
    jsr object_code_import_index_from_a
    bcc :+
    jmp build_object_code_prg_bad
:
    iny
    sty linked_runtime_body_pos
    jsr runtime_helper_sequence_note_load_or_fail
    bcc :+
    jmp build_object_code_prg_bad
:
    jmp runtime_helper_sequence_compute_loop
runtime_helper_sequence_compute_add:
    iny
    sty linked_runtime_body_pos
    jsr runtime_helper_sequence_fold_add_or_fail
    bcc :+
    jmp build_object_code_prg_bad
:
    jmp runtime_helper_sequence_compute_loop
runtime_helper_sequence_compute_return:
    lda #<(runtime_helper_prg_exit_template_end - runtime_helper_prg_exit_template)
    jsr runtime_helper_sequence_add_a_to_next_addr
    lda linked_runtime_store_count
    sta linked_object_index
    beq runtime_helper_sequence_compute_return_done
runtime_helper_sequence_compute_storage_loop:
    lda #$02
    jsr runtime_helper_sequence_add_a_to_next_addr
    dec linked_object_index
    bne runtime_helper_sequence_compute_storage_loop
runtime_helper_sequence_compute_return_done:
    rts

runtime_helper_sequence_capture_store_addr:
    lda linked_runtime_store_count
    bne :+
    lda #$00
    sta linked_runtime_store_addr_lo
    sta linked_runtime_store_addr_hi
    rts
:
    lda linked_next_addr_lo
    sta linked_runtime_store_addr_lo
    lda linked_next_addr_hi
    sta linked_runtime_store_addr_hi
    ldx linked_runtime_store_count
runtime_helper_sequence_capture_store_addr_loop:
    sec
    lda linked_runtime_store_addr_lo
    sbc #$02
    sta linked_runtime_store_addr_lo
    lda linked_runtime_store_addr_hi
    sbc #$00
    sta linked_runtime_store_addr_hi
    dex
    bne runtime_helper_sequence_capture_store_addr_loop
    rts

runtime_helper_sequence_add_current_call_length:
    jsr runtime_helper_sequence_pending_a_arg_active
    bcs runtime_helper_sequence_add_current_call_literal_args
    jsr runtime_helper_sequence_add_pending_loaded_len
    lda linked_runtime_helper_kind
    cmp #RUNTIME_HELPER_KIND_GFX_BGCOLOR
    beq runtime_helper_sequence_add_arg0_three
    cmp #RUNTIME_HELPER_KIND_A_BYTE
    beq runtime_helper_sequence_add_arg0_three
    cmp #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    beq runtime_helper_sequence_add_arg0_three
    cmp #RUNTIME_HELPER_KIND_XY_WORD
    beq runtime_helper_sequence_add_arg0_six
    cmp #RUNTIME_HELPER_KIND_XY_WORD_READBACK
    beq runtime_helper_sequence_add_arg0_six
    cmp #RUNTIME_HELPER_KIND_XA_BYTE
    beq runtime_helper_sequence_add_arg0_six
    cmp #RUNTIME_HELPER_KIND_AY_BYTE
    beq runtime_helper_sequence_add_arg0_five
    cmp #RUNTIME_HELPER_KIND_AY_BYTE_READBACK
    beq runtime_helper_sequence_add_arg0_five
    cmp #RUNTIME_HELPER_KIND_X1_A0_BYTES
    beq runtime_helper_sequence_add_arg0_five
    cmp #RUNTIME_HELPER_KIND_AXY_BYTES_CLC
    beq runtime_helper_sequence_add_arg0_eight
    cmp #RUNTIME_HELPER_KIND_AXY_BYTES_CLC_READBACK
    beq runtime_helper_sequence_add_arg0_eight
    cmp #RUNTIME_HELPER_KIND_AXY_E0_BYTES_CLC_READBACK
    bne :+
    lda linked_runtime_result_loaded
    beq runtime_helper_sequence_add_arg0_fourteen
    lda #$0C
    jmp runtime_helper_sequence_add_a_to_next_addr
:
    cmp #RUNTIME_HELPER_KIND_SPRITE_POS
    beq runtime_helper_sequence_add_arg0_eight
    cmp #RUNTIME_HELPER_KIND_SPRITE_DATA
    beq runtime_helper_sequence_add_arg0_seven
    cmp #RUNTIME_HELPER_KIND_SID_FREQ
    beq runtime_helper_sequence_add_arg0_seven
    jmp runtime_helper_sequence_add_current_call_literal_args
runtime_helper_sequence_add_arg0_three:
    jmp runtime_helper_sequence_add_three_to_next_addr
runtime_helper_sequence_add_arg0_five:
    jmp runtime_helper_sequence_add_five_to_next_addr
runtime_helper_sequence_add_arg0_six:
    jmp runtime_helper_sequence_add_six_to_next_addr
runtime_helper_sequence_add_arg0_seven:
    jmp runtime_helper_sequence_add_seven_to_next_addr
runtime_helper_sequence_add_arg0_eight:
    lda #$08
    jmp runtime_helper_sequence_add_a_to_next_addr
runtime_helper_sequence_add_arg0_fourteen:
    lda #$0E
    jmp runtime_helper_sequence_add_a_to_next_addr
runtime_helper_sequence_add_current_call_literal_args:
    jsr runtime_helper_sequence_pending_a_arg1_active
    bcs runtime_helper_sequence_add_current_call_arg2_literal_args
    jsr runtime_helper_sequence_add_pending_loaded_len
    lda linked_runtime_helper_kind
    cmp #RUNTIME_HELPER_KIND_XA_BYTE
    bne :+
    jmp runtime_helper_sequence_add_five_to_next_addr
:
    cmp #RUNTIME_HELPER_KIND_AY_BYTE
    bne :+
    jmp runtime_helper_sequence_add_six_to_next_addr
:
    cmp #RUNTIME_HELPER_KIND_AY_BYTE_READBACK
    bne :+
    jmp runtime_helper_sequence_add_six_to_next_addr
:
    cmp #RUNTIME_HELPER_KIND_X1_A0_BYTES
    bne :+
    jmp runtime_helper_sequence_add_six_to_next_addr
:
    cmp #RUNTIME_HELPER_KIND_SPRITE_DATA
    beq runtime_helper_sequence_add_arg0_eight
    cmp #RUNTIME_HELPER_KIND_AXY_BYTES_CLC
    bne :+
    jmp runtime_helper_sequence_add_nine_to_next_addr
:
    cmp #RUNTIME_HELPER_KIND_AXY_BYTES_CLC_READBACK
    bne :+
    jmp runtime_helper_sequence_add_nine_to_next_addr
:
    cmp #RUNTIME_HELPER_KIND_SPRITE_POS
    bne :+
    jmp runtime_helper_sequence_add_nine_to_next_addr
:
    cmp #RUNTIME_HELPER_KIND_SID_FREQ
    beq runtime_helper_sequence_add_arg0_eight
runtime_helper_sequence_add_current_call_arg2_literal_args:
    jsr runtime_helper_sequence_pending_a_arg2_active
    bcs runtime_helper_sequence_add_current_call_arg3_literal_args
    jsr runtime_helper_sequence_add_pending_loaded_len
    lda linked_runtime_helper_kind
    cmp #RUNTIME_HELPER_KIND_AXY_BYTES_CLC
    bne :+
    jmp runtime_helper_sequence_add_nine_to_next_addr
:
    cmp #RUNTIME_HELPER_KIND_AXY_BYTES_CLC_READBACK
    bne :+
    jmp runtime_helper_sequence_add_nine_to_next_addr
:
    cmp #RUNTIME_HELPER_KIND_SPRITE_POS
    bne :+
    jmp runtime_helper_sequence_add_nine_to_next_addr
:
runtime_helper_sequence_add_current_call_arg3_literal_args:
    jsr runtime_helper_sequence_pending_a_arg3_active
    bcs runtime_helper_sequence_add_current_call_all_literal_args
    jsr runtime_helper_sequence_add_pending_loaded_len
    lda linked_runtime_helper_kind
    cmp #RUNTIME_HELPER_KIND_AXY_E0_BYTES_CLC_READBACK
    bne runtime_helper_sequence_add_current_call_all_literal_args
    lda #$0C
    jmp runtime_helper_sequence_add_a_to_next_addr
runtime_helper_sequence_add_current_call_all_literal_args:
    lda linked_runtime_helper_kind
    cmp #RUNTIME_HELPER_KIND_AXY_E0_BYTES_CLC_READBACK
    bne :+
    jmp runtime_helper_sequence_add_arg0_fourteen
:
    cmp #RUNTIME_HELPER_KIND_SPRITE_POS
    beq runtime_helper_sequence_add_ten_to_next_addr
    cmp #RUNTIME_HELPER_KIND_AXY_BYTES_CLC
    beq runtime_helper_sequence_add_ten_to_next_addr
    cmp #RUNTIME_HELPER_KIND_AXY_BYTES_CLC_READBACK
    bne :+
runtime_helper_sequence_add_ten_to_next_addr:
    lda #$0A
    jmp runtime_helper_sequence_add_a_to_next_addr
:
    cmp #RUNTIME_HELPER_KIND_GFX_BGCOLOR
    bne :+
    jmp runtime_helper_sequence_add_five_to_next_addr
:
    cmp #RUNTIME_HELPER_KIND_A_BYTE
    bne :+
    jmp runtime_helper_sequence_add_five_to_next_addr
:
    cmp #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    bne :+
runtime_helper_sequence_add_five_to_next_addr:
    lda #$05
    jmp runtime_helper_sequence_add_a_to_next_addr
:
    cmp #RUNTIME_HELPER_KIND_XA_BYTE
    beq runtime_helper_sequence_add_seven_to_next_addr
    cmp #RUNTIME_HELPER_KIND_XY_WORD
    beq runtime_helper_sequence_add_seven_to_next_addr
    cmp #RUNTIME_HELPER_KIND_XY_WORD_READBACK
    beq runtime_helper_sequence_add_seven_to_next_addr
    cmp #RUNTIME_HELPER_KIND_AY_BYTE
    beq runtime_helper_sequence_add_seven_to_next_addr
    cmp #RUNTIME_HELPER_KIND_AY_BYTE_READBACK
    bne :+
runtime_helper_sequence_add_seven_to_next_addr:
    lda #$07
    jmp runtime_helper_sequence_add_a_to_next_addr
:
    cmp #RUNTIME_HELPER_KIND_X1_A0_BYTES
    beq runtime_helper_sequence_add_seven_to_next_addr
    cmp #RUNTIME_HELPER_KIND_NO_ARG
    bne :+
runtime_helper_sequence_add_three_to_next_addr:
    lda #$03
    jmp runtime_helper_sequence_add_a_to_next_addr
:
    cmp #RUNTIME_HELPER_KIND_BYTE_READBACK
    bne runtime_helper_sequence_add_nine_to_next_addr
    lda #$03
    jmp runtime_helper_sequence_add_a_to_next_addr
runtime_helper_sequence_add_six_to_next_addr:
    lda #$06
    jmp runtime_helper_sequence_add_a_to_next_addr
runtime_helper_sequence_add_nine_to_next_addr:
    lda #$09
    jmp runtime_helper_sequence_add_a_to_next_addr
runtime_helper_sequence_add_pending_loaded_len:
    lda linked_runtime_result_loaded
    beq :+
    lda #$03
    jsr runtime_helper_sequence_add_a_to_next_addr
:
    rts
runtime_helper_sequence_add_a_to_next_addr:
    clc
    adc linked_next_addr_lo
    sta linked_next_addr_lo
    lda linked_next_addr_hi
    adc #$00
    sta linked_next_addr_hi
    rts

append_runtime_helper_sequence_current_call_or_fail:
    lda linked_runtime_helper_kind
    cmp #RUNTIME_HELPER_KIND_SPRITE_DATA
    bne :+
    jmp append_runtime_helper_sequence_sprite_data
:
    cmp #RUNTIME_HELPER_KIND_SPRITE_POS
    bne :+
    jmp append_runtime_helper_sequence_sprite_pos
:
    cmp #RUNTIME_HELPER_KIND_GFX_BGCOLOR
    bne :+
    jmp append_runtime_helper_sequence_gfx_bgcolor
:
    cmp #RUNTIME_HELPER_KIND_SID_FREQ
    bne :+
    jmp append_runtime_helper_sequence_sid_freq
:
    cmp #RUNTIME_HELPER_KIND_XA_BYTE
    bne :+
    jmp append_runtime_helper_sequence_xa_byte
:
    cmp #RUNTIME_HELPER_KIND_XY_WORD
    bne :+
    jmp append_runtime_helper_sequence_xy_word
:
    cmp #RUNTIME_HELPER_KIND_XY_WORD_READBACK
    bne :+
    jmp append_runtime_helper_sequence_xy_word
:
    cmp #RUNTIME_HELPER_KIND_NO_ARG
    bne :+
    rts
:
    cmp #RUNTIME_HELPER_KIND_BYTE_READBACK
    bne :+
    rts
:
    cmp #RUNTIME_HELPER_KIND_A_BYTE
    bne :+
    jmp append_runtime_helper_sequence_a_byte
:
    cmp #RUNTIME_HELPER_KIND_A_BYTE_READBACK
    bne :+
    jmp append_runtime_helper_sequence_a_byte
:
    cmp #RUNTIME_HELPER_KIND_AY_BYTE
    bne :+
    jmp append_runtime_helper_sequence_ay_byte
:
    cmp #RUNTIME_HELPER_KIND_AY_BYTE_READBACK
    bne :+
    jmp append_runtime_helper_sequence_ay_byte
:
    cmp #RUNTIME_HELPER_KIND_AXY_BYTES_CLC
    bne :+
    jmp append_runtime_helper_sequence_axy_bytes_clc
:
    cmp #RUNTIME_HELPER_KIND_AXY_BYTES_CLC_READBACK
    bne :+
    jmp append_runtime_helper_sequence_axy_bytes_clc
:
    cmp #RUNTIME_HELPER_KIND_AXY_E0_BYTES_CLC_READBACK
    bne :+
    jmp append_runtime_helper_sequence_axy_e0_bytes_clc
:
    cmp #RUNTIME_HELPER_KIND_X1_A0_BYTES
    bne :+
    jmp append_runtime_helper_sequence_x1_a0_bytes
:
    jmp build_object_code_prg_bad

append_runtime_helper_sequence_sprite_data:
    jsr runtime_helper_sequence_pending_a_arg_active
    bcs :+
    jsr append_runtime_helper_sequence_lda_pending_low
    jsr append_runtime_helper_sequence_ldx_arg0_low
    jmp append_runtime_helper_sequence_ldy_arg0_hi
:
    jsr runtime_helper_sequence_pending_a_arg1_active
    bcs :+
    jsr append_runtime_helper_sequence_lda_pending_low
    lda #$AA
    jsr append_payload_byte
    jsr append_runtime_helper_sequence_lda_arg0_low
    lda #$A0
    jsr append_payload_byte
    lda #$00
    jmp append_payload_byte
:
    jsr append_runtime_helper_sequence_lda_arg0_low
    jsr append_runtime_helper_sequence_ldx_arg1_low
    jmp append_runtime_helper_sequence_ldy_arg1_hi

append_runtime_helper_sequence_sprite_pos:
    jsr runtime_helper_sequence_pending_a_arg_active
    bcs :+
    jsr append_runtime_helper_sequence_lda_pending_low
    jsr append_runtime_helper_sequence_ldx_arg0_low
    jsr append_runtime_helper_sequence_ldy_arg1_low
    ldx linked_runtime_arg0
    jmp append_runtime_helper_sequence_sprite_pos_carry_from_x
:
    jsr runtime_helper_sequence_pending_a_arg1_active
    bcs :+
    jsr append_runtime_helper_sequence_lda_pending_low
    lda #$AA
    jsr append_payload_byte
    jsr append_runtime_helper_sequence_lda_arg0_low
    jsr append_runtime_helper_sequence_ldy_arg1_low
    lda #$18
    jmp append_payload_byte
:
    jsr runtime_helper_sequence_pending_a_arg2_active
    bcs :+
    jsr append_runtime_helper_sequence_lda_pending_low
    lda #$A8
    jsr append_payload_byte
    jsr append_runtime_helper_sequence_lda_arg0_low
    jsr append_runtime_helper_sequence_ldx_arg1_low
    ldx linked_runtime_arg1
    jmp append_runtime_helper_sequence_sprite_pos_carry_from_x
:
    jsr append_runtime_helper_sequence_lda_arg0_low
    jsr append_runtime_helper_sequence_ldx_arg1_low
    jsr append_runtime_helper_sequence_ldy_arg2_low
    ldx linked_runtime_arg1
append_runtime_helper_sequence_sprite_pos_carry_from_x:
    txa
    bmi append_runtime_helper_sequence_sprite_pos_clc
    jsr load_linked_literal_window_from_x_or_fail
    lda linked_literal_window+LINKED_LITERAL_HI
    beq append_runtime_helper_sequence_sprite_pos_clc
    lda #$38
    jmp append_payload_byte
append_runtime_helper_sequence_sprite_pos_clc:
    lda #$18
    jmp append_payload_byte

append_runtime_helper_sequence_gfx_bgcolor:
    jsr runtime_helper_sequence_pending_a_arg_active
    bcs :+
    jmp append_runtime_helper_sequence_lda_pending_low
:
    jmp append_runtime_helper_sequence_lda_arg0_low

append_runtime_helper_sequence_sid_freq:
        jsr runtime_helper_sequence_pending_a_arg_active
        bcs :+
        jsr append_runtime_helper_sequence_lda_pending_low
        jsr append_runtime_helper_sequence_ldx_arg0_low
        jmp append_runtime_helper_sequence_ldy_arg0_hi
    :
        jsr runtime_helper_sequence_pending_a_arg1_active
        bcs :+
        jsr append_runtime_helper_sequence_lda_pending_low
        lda #$AA
        jsr append_payload_byte
        jsr append_runtime_helper_sequence_lda_arg0_low
        lda #$A0
        jsr append_payload_byte
        lda #$00
        jmp append_payload_byte
    :
        jsr append_runtime_helper_sequence_lda_arg0_low
        jsr append_runtime_helper_sequence_ldx_arg1_low
        jmp append_runtime_helper_sequence_ldy_arg1_hi

append_runtime_helper_sequence_xa_byte:
        jsr runtime_helper_sequence_pending_a_arg_active
        bcs :+
        jsr append_runtime_helper_sequence_lda_pending_low
        lda #$AA
        jsr append_payload_byte
        jmp append_runtime_helper_sequence_lda_arg0_low
    :
        jsr runtime_helper_sequence_pending_a_arg1_active
        bcs :+
        jsr append_runtime_helper_sequence_lda_pending_low
        jmp append_runtime_helper_sequence_ldx_arg0_low
:
        jsr append_runtime_helper_sequence_ldx_arg0_low
        jmp append_runtime_helper_sequence_lda_arg1_low

append_runtime_helper_sequence_x1_a0_bytes:
        jsr runtime_helper_sequence_pending_a_arg_active
        bcs :+
        jsr append_runtime_helper_sequence_lda_pending_low
        jmp append_runtime_helper_sequence_ldx_arg0_low
    :
        jsr runtime_helper_sequence_pending_a_arg1_active
        bcs :+
        jsr append_runtime_helper_sequence_lda_pending_low
        lda #$AA
        jsr append_payload_byte
        jmp append_runtime_helper_sequence_lda_arg0_low
    :
        jsr append_runtime_helper_sequence_ldx_arg1_low
        jmp append_runtime_helper_sequence_lda_arg0_low

append_runtime_helper_sequence_xy_word:
        jsr runtime_helper_sequence_pending_a_arg_active
        bcs :+
        jsr append_runtime_helper_sequence_lda_pending_low
        lda #$AA
        jsr append_payload_byte
        lda #$A0
        jsr append_payload_byte
        lda #$00
        jmp append_payload_byte
    :
        jsr append_runtime_helper_sequence_ldx_arg0_low
        jmp append_runtime_helper_sequence_ldy_arg0_hi

append_runtime_helper_sequence_a_byte:
    jsr runtime_helper_sequence_pending_a_arg_active
    bcs :+
    jmp append_runtime_helper_sequence_lda_pending_low
:
    jmp append_runtime_helper_sequence_lda_arg0_low

append_runtime_helper_sequence_ay_byte:
        jsr runtime_helper_sequence_pending_a_arg_active
        bcs :+
        jsr append_runtime_helper_sequence_lda_pending_low
        jmp append_runtime_helper_sequence_ldy_arg0_low
    :
        jsr runtime_helper_sequence_pending_a_arg1_active
        bcs append_runtime_helper_sequence_ay_byte_literal_args
        lda linked_runtime_arg0
        bpl :+
        jsr append_runtime_helper_sequence_ldy_pending_low
        jmp append_runtime_helper_sequence_lda_arg0_low
    :
        jsr append_runtime_helper_sequence_lda_pending_low
        lda #$A8
        jsr append_payload_byte
        jmp append_runtime_helper_sequence_lda_arg0_low
append_runtime_helper_sequence_ay_byte_literal_args:
        jsr append_runtime_helper_sequence_lda_arg0_low
        jmp append_runtime_helper_sequence_ldy_arg1_low

append_runtime_helper_sequence_axy_bytes_clc:
        jsr runtime_helper_sequence_pending_a_arg_active
        bcs :+
        jsr append_runtime_helper_sequence_lda_pending_low
        jsr append_runtime_helper_sequence_ldx_arg0_low
        jsr append_runtime_helper_sequence_ldy_arg1_low
        lda #$18
        jmp append_payload_byte
    :
        jsr runtime_helper_sequence_pending_a_arg1_active
        bcs :+
        jsr append_runtime_helper_sequence_lda_pending_low
        lda #$AA
        jsr append_payload_byte
        jsr append_runtime_helper_sequence_lda_arg0_low
        jsr append_runtime_helper_sequence_ldy_arg1_low
        lda #$18
        jmp append_payload_byte
    :
        jsr runtime_helper_sequence_pending_a_arg2_active
        bcs :+
        jsr append_runtime_helper_sequence_lda_pending_low
        lda #$A8
        jsr append_payload_byte
        jsr append_runtime_helper_sequence_lda_arg0_low
        jsr append_runtime_helper_sequence_ldx_arg1_low
        lda #$18
        jmp append_payload_byte
:
        jsr append_runtime_helper_sequence_lda_arg0_low
        jsr append_runtime_helper_sequence_ldx_arg1_low
        jsr append_runtime_helper_sequence_ldy_arg2_low
        lda #$18
        jmp append_payload_byte

append_runtime_helper_sequence_axy_e0_bytes_clc:
        jsr runtime_helper_sequence_pending_a_arg_active
        bcs :+
        lda linked_runtime_result_loaded
        bne append_runtime_helper_sequence_axy_e0_bytes_pending_arg0_loaded
        lda #$48
        jsr append_payload_byte
        jsr append_runtime_helper_sequence_lda_arg2_low
        jsr append_runtime_helper_sequence_sta_e0
        lda #$68
        jsr append_payload_byte
        jmp append_runtime_helper_sequence_axy_e0_bytes_pending_arg0_regs
append_runtime_helper_sequence_axy_e0_bytes_pending_arg0_loaded:
        jsr append_runtime_helper_sequence_lda_arg2_low
        jsr append_runtime_helper_sequence_sta_e0
        jsr append_runtime_helper_sequence_lda_pending_low
append_runtime_helper_sequence_axy_e0_bytes_pending_arg0_regs:
        jsr append_runtime_helper_sequence_ldx_arg0_low
        jsr append_runtime_helper_sequence_ldy_arg1_low
        lda #$18
        jmp append_payload_byte
    :
        jsr runtime_helper_sequence_pending_a_arg3_active
        bcs :+
        jsr append_runtime_helper_sequence_lda_pending_low
        jsr append_runtime_helper_sequence_sta_e0
        jsr append_runtime_helper_sequence_lda_arg0_low
        jsr append_runtime_helper_sequence_ldx_arg1_low
        jsr append_runtime_helper_sequence_ldy_arg2_low
        lda #$18
        jmp append_payload_byte
:
        jsr append_runtime_helper_sequence_lda_arg3_low
        jsr append_runtime_helper_sequence_sta_e0
        jsr append_runtime_helper_sequence_lda_arg0_low
        jsr append_runtime_helper_sequence_ldx_arg1_low
        jsr append_runtime_helper_sequence_ldy_arg2_low
        lda #$18
        jmp append_payload_byte

append_runtime_helper_sequence_lda_arg0_low:
    ldx linked_runtime_arg0
    jmp append_runtime_helper_sequence_lda_arg_x_low

append_runtime_helper_sequence_lda_arg1_low:
    ldx linked_runtime_arg1
    jmp append_runtime_helper_sequence_lda_arg_x_low

append_runtime_helper_sequence_lda_arg2_low:
    ldx linked_runtime_arg2
    jmp append_runtime_helper_sequence_lda_arg_x_low

append_runtime_helper_sequence_lda_arg3_low:
    ldx linked_runtime_arg3
    jmp append_runtime_helper_sequence_lda_arg_x_low

append_runtime_helper_sequence_ldx_arg0_low:
    ldx linked_runtime_arg0
    jmp append_runtime_helper_sequence_ldx_arg_x_low

append_runtime_helper_sequence_ldx_arg1_low:
    ldx linked_runtime_arg1
    jmp append_runtime_helper_sequence_ldx_arg_x_low

append_runtime_helper_sequence_ldy_arg1_low:
    ldx linked_runtime_arg1
    jmp append_runtime_helper_sequence_ldy_arg_x_low

append_runtime_helper_sequence_ldy_arg0_low:
    ldx linked_runtime_arg0
    jmp append_runtime_helper_sequence_ldy_arg_x_low

append_runtime_helper_sequence_ldy_arg0_hi:
    ldx linked_runtime_arg0
    jmp append_runtime_helper_sequence_ldy_arg_x_hi

append_runtime_helper_sequence_ldy_arg1_hi:
    ldx linked_runtime_arg1
    jmp append_runtime_helper_sequence_ldy_arg_x_hi

append_runtime_helper_sequence_ldy_arg2_low:
    ldx linked_runtime_arg2
    jmp append_runtime_helper_sequence_ldy_arg_x_low

append_runtime_helper_sequence_lda_pending_low:
    lda linked_runtime_result_loaded
    bne :+
    rts
:
    ldx linked_runtime_result_store_ordinal
    jmp append_runtime_helper_sequence_lda_store_ordinal_x_low

append_runtime_helper_sequence_ldy_pending_low:
    lda linked_runtime_result_loaded
    bne :+
    rts
:
    ldx linked_runtime_result_store_ordinal
    jmp append_runtime_helper_sequence_ldy_store_ordinal_x_low

append_runtime_helper_sequence_lda_arg_x_low:
    stx linked_object_index
    txa
    bmi :+
    lda #$A9
    jsr append_payload_byte
    ldx linked_object_index
    jsr load_linked_literal_window_from_x_or_fail
    lda linked_literal_window+LINKED_LITERAL_LO
    jmp append_payload_byte
:
    lda linked_object_index
    and #$7F
    tax
    jmp append_runtime_helper_sequence_lda_store_ordinal_x_low

append_runtime_helper_sequence_ldx_arg_x_low:
    stx linked_object_index
    txa
    bmi :+
    lda #$A2
    jsr append_payload_byte
    ldx linked_object_index
    jsr load_linked_literal_window_from_x_or_fail
    lda linked_literal_window+LINKED_LITERAL_LO
    jmp append_payload_byte
:
    lda linked_object_index
    and #$7F
    tax
    jmp append_runtime_helper_sequence_ldx_store_ordinal_x_low

append_runtime_helper_sequence_ldy_arg_x_low:
    stx linked_object_index
    txa
    bmi :+
    lda #$A0
    jsr append_payload_byte
    ldx linked_object_index
    jsr load_linked_literal_window_from_x_or_fail
    lda linked_literal_window+LINKED_LITERAL_LO
    jmp append_payload_byte
:
    lda linked_object_index
    and #$7F
    tax
    jmp append_runtime_helper_sequence_ldy_store_ordinal_x_low

append_runtime_helper_sequence_ldy_arg_x_hi:
    stx linked_object_index
    txa
    bmi :+
    lda #$A0
    jsr append_payload_byte
    ldx linked_object_index
    jsr load_linked_literal_window_from_x_or_fail
    lda linked_literal_window+LINKED_LITERAL_HI
    jmp append_payload_byte
:
    lda #$A0
    jsr append_payload_byte
    lda #$00
    jmp append_payload_byte

append_runtime_helper_sequence_sta_e0:
    lda #$85
    jsr append_payload_byte
    lda #$E0
    jmp append_payload_byte

append_runtime_helper_sequence_lda_store_ordinal_x_low:
    jsr runtime_helper_sequence_store_addr_for_ordinal_x
    lda #$AD
    jsr append_payload_byte
    lda linked_store_value
    jsr append_payload_byte
    lda linked_store_value_hi
    jmp append_payload_byte

append_runtime_helper_sequence_ldx_store_ordinal_x_low:
    jsr runtime_helper_sequence_store_addr_for_ordinal_x
    lda #$AE
    jsr append_payload_byte
    lda linked_store_value
    jsr append_payload_byte
    lda linked_store_value_hi
    jmp append_payload_byte

append_runtime_helper_sequence_ldy_store_ordinal_x_low:
    jsr runtime_helper_sequence_store_addr_for_ordinal_x
    lda #$AC
    jsr append_payload_byte
    lda linked_store_value
    jsr append_payload_byte
    lda linked_store_value_hi
    jmp append_payload_byte

runtime_helper_sequence_store_addr_for_ordinal_x:
    lda linked_runtime_store_addr_lo
    sta linked_store_value
    lda linked_runtime_store_addr_hi
    sta linked_store_value_hi
    cpx #$00
    beq runtime_helper_sequence_store_addr_done
runtime_helper_sequence_store_addr_loop:
    clc
    lda linked_store_value
    adc #$02
    sta linked_store_value
    lda linked_store_value_hi
    adc #$00
    sta linked_store_value_hi
    dex
    bne runtime_helper_sequence_store_addr_loop
runtime_helper_sequence_store_addr_done:
    rts

append_runtime_helper_sequence_load_store_ordinal_or_fail:
    jsr runtime_helper_sequence_store_addr_for_ordinal_x
    lda #$AD
    jsr append_payload_byte
    lda linked_store_value
    jsr append_payload_byte
    lda linked_store_value_hi
    jmp append_payload_byte

append_runtime_helper_sequence_result_store_or_fail:
    ldx linked_runtime_store_count
    dex
    jsr runtime_helper_sequence_store_addr_for_ordinal_x
    clc
    lda linked_store_value
    adc #$01
    sta current_bit_lo
    lda linked_store_value_hi
    adc #$00
    sta current_bit_hi
    lda #$8D
    jsr append_payload_byte
    lda linked_store_value
    jsr append_payload_byte
    lda linked_store_value_hi
    jsr append_payload_byte
    lda #$A9
    jsr append_payload_byte
    lda #$00
    jsr append_payload_byte
    lda #$8D
    jsr append_payload_byte
    lda current_bit_lo
    jsr append_payload_byte
    lda current_bit_hi
    jmp append_payload_byte

append_runtime_helper_sequence_storage_if_needed:
    lda linked_runtime_store_count
    sta linked_object_index
    bne append_runtime_helper_sequence_storage_loop
    rts
append_runtime_helper_sequence_storage_loop:
    lda #$00
    jsr append_payload_byte
    lda #$00
    jsr append_payload_byte
    dec linked_object_index
    bne append_runtime_helper_sequence_storage_loop
    rts

append_runtime_jsr_to_pending_target_x:
    stx linked_object_index
    lda #$20
    jsr append_payload_byte
    ldx linked_object_index
    jsr load_pending_target_offset_from_x
    lda current_bit_lo
    jsr append_payload_byte
    lda current_bit_hi
    jsr append_payload_byte
    rts

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
    rts
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
    jsr reloc_offset_is_in_current_export
    bcs load_reloc_records_current_object_next
    jsr require_space_or_fail
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
    ldx linked_reloc_count
    cpx #EXTERNAL_MAX
    bcs load_reloc_records_current_object_bad
    lda saved_state_lo
    sta reloc_record_window+RELOC_RECORD_OFFSET_LO
    lda saved_state_hi
    sta reloc_record_window+RELOC_RECORD_OFFSET_HI
    lda pending_meta_window+PENDING_META_OFFSET_LO
    sta reloc_record_window+RELOC_RECORD_ADDR_LO
    lda pending_meta_window+PENDING_META_OFFSET_HI
    sta reloc_record_window+RELOC_RECORD_ADDR_HI
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
    jsr reloc_offset_is_in_current_export
    bcs append_named_relocs_current_export_to_queue_next
    jsr require_space_or_fail
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
    clc
    lda saved_state_lo
    adc #$01
    sta current_bit_lo
    lda saved_state_hi
    adc #$00
    sta current_bit_hi
    bcs reloc_offset_is_in_current_export_no
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

find_reloc_patch_byte_for_current_offset:
    clc
    lda export_meta_window+EXPORT_META_OFFSET_LO
    adc linked_store_value
    sta current_bit_lo
    lda export_meta_window+EXPORT_META_OFFSET_HI
    adc linked_store_value_hi
    sta current_bit_hi
    bcs find_reloc_patch_byte_for_current_offset_not_found
    ldx #$00
find_reloc_patch_byte_for_current_offset_loop:
    cpx linked_reloc_count
    beq find_reloc_patch_byte_for_current_offset_not_found
    jsr load_linked_reloc_record_window_from_x_or_fail
    lda current_bit_lo
    cmp reloc_record_window+RELOC_RECORD_OFFSET_LO
    bne find_reloc_patch_byte_for_current_offset_check_hi
    lda current_bit_hi
    cmp reloc_record_window+RELOC_RECORD_OFFSET_HI
    beq find_reloc_patch_byte_for_current_offset_lo
find_reloc_patch_byte_for_current_offset_check_hi:
    clc
    lda reloc_record_window+RELOC_RECORD_OFFSET_LO
    adc #$01
    sta parse_word_temp_lo
    lda reloc_record_window+RELOC_RECORD_OFFSET_HI
    adc #$00
    sta parse_word_temp_hi
    bcs find_reloc_patch_byte_for_current_offset_next
    lda current_bit_lo
    cmp parse_word_temp_lo
    bne find_reloc_patch_byte_for_current_offset_next
    lda current_bit_hi
    cmp parse_word_temp_hi
    beq find_reloc_patch_byte_for_current_offset_hi
find_reloc_patch_byte_for_current_offset_next:
    inx
    jmp find_reloc_patch_byte_for_current_offset_loop
find_reloc_patch_byte_for_current_offset_lo:
    lda reloc_record_window+RELOC_RECORD_ADDR_LO
    clc
    rts
find_reloc_patch_byte_for_current_offset_hi:
    lda reloc_record_window+RELOC_RECORD_ADDR_HI
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
direct_body_runtime_helper_if_eq:
    .asciiz "p0u0p1qhp2u1vr"
direct_body_runtime_helper_if_ne:
    .asciiz "p0u0p1nhp2u1vr"
direct_body_runtime_helper_noarg_if_eq:
    .asciiz "u0p0qhp1u1vr"
direct_body_runtime_helper_noarg_if_ne:
    .asciiz "u0p0nhp1u1vr"
runtime_name_rt_sid_freq:
    .asciiz "rt_sid_freq"
runtime_name_rt_sid_pulse:
    .asciiz "rt_sid_pulse"
runtime_name_rt_sid_wave:
    .asciiz "rt_sid_wave"
runtime_name_rt_sid_on:
    .asciiz "rt_sid_on"
runtime_name_rt_sid_off:
    .asciiz "rt_sid_off"
runtime_name_rt_sid_ad:
    .asciiz "rt_sid_ad"
runtime_name_rt_sid_sr:
    .asciiz "rt_sid_sr"
runtime_name_rt_sid_vol:
    .asciiz "rt_sid_vol"
runtime_name_rt_sid_mode:
    .asciiz "rt_sid_mode"
runtime_name_rt_sid_route:
    .asciiz "rt_sid_route"
runtime_name_rt_sid_res:
    .asciiz "rt_sid_res"
runtime_name_rt_sid_rst:
    .asciiz "rt_sid_rst"
runtime_name_rt_sid_cutoff:
    .asciiz "rt_sid_cutoff"
runtime_name_rt_sid_osc3:
    .asciiz "rt_sid_osc3"
runtime_name_rt_sid_env3:
    .asciiz "rt_sid_env3"
runtime_name_rt_sprite_data:
    .asciiz "rt_sprite_data"
runtime_name_rt_sprite_pos:
    .asciiz "rt_sprite_pos"
runtime_name_rt_sprite_on:
    .asciiz "rt_sprite_on"
runtime_name_rt_sprite_off:
    .asciiz "rt_sprite_off"
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
runtime_name_rt_sprite_set_mc:
    .asciiz "rt_sprite_set_mc"
runtime_name_rt_sprite_hit:
    .asciiz "rt_sprite_hit"
runtime_name_rt_sprite_hit_bg:
    .asciiz "rt_sprite_hit_bg"
runtime_name_rt_joy:
    .asciiz "rt_joy"
runtime_name_rt_jp:
    .asciiz "rt_jp"
runtime_name_rt_jb1:
    .asciiz "rt_jb1"
runtime_name_rt_jb2:
    .asciiz "rt_jb2"
runtime_name_rt_mp:
    .asciiz "rt_mp"
runtime_name_rt_mx:
    .asciiz "rt_mx"
runtime_name_rt_my:
    .asciiz "rt_my"
runtime_name_rt_mb:
    .asciiz "rt_mb"
runtime_name_rt_mb1:
    .asciiz "rt_mb1"
runtime_name_rt_mb2:
    .asciiz "rt_mb2"
runtime_name_rt_mseen:
    .asciiz "rt_mseen"
runtime_name_rt_dbf_create:
    .asciiz "rt_dbf_create"
runtime_name_rt_dbf_open:
    .asciiz "rt_dbf_open"
runtime_name_rt_dbf_close:
    .asciiz "rt_dbf_close"
runtime_name_rt_dbf_go:
    .asciiz "rt_dbf_go"
runtime_name_rt_dbf_fieldcount:
    .asciiz "rt_dbf_fieldcount"
runtime_name_rt_dbf_fieldlen:
    .asciiz "rt_dbf_fieldlen"
runtime_name_rt_dbf_readbyte:
    .asciiz "rt_dbf_readbyte"
runtime_name_rt_dbf_readfieldbyte:
    .asciiz "rt_dbf_readfieldbyte"
runtime_name_rt_dbf_writefieldbyte:
    .asciiz "rt_dbf_writefieldbyte"
runtime_name_rt_dbf_writebyte:
    .asciiz "rt_dbf_writebyte"
runtime_name_rt_dbf_append:
    .asciiz "rt_dbf_append"
runtime_name_rt_dbf_pack:
    .asciiz "rt_dbf_pack"
runtime_name_rt_dbf_save:
    .asciiz "rt_dbf_save"
runtime_name_rt_dbf_delete:
    .asciiz "rt_dbf_delete"
runtime_name_rt_dbf_undelete:
    .asciiz "rt_dbf_undelete"
runtime_name_rt_dbf_deleted:
    .asciiz "rt_dbf_deleted"
runtime_name_rt_dbf_headerlen:
    .asciiz "rt_dbf_headerlen"
runtime_name_rt_dbf_recordlen:
    .asciiz "rt_dbf_recordlen"
runtime_name_rt_dbf_totalrecs:
    .asciiz "rt_dbf_totalrecs"
runtime_name_rt_dbf_currrecno:
    .asciiz "rt_dbf_currrecno"
runtime_name_rt_gfx_bitmap_on:
    .asciiz "rt_gfx_bitmap_on"
runtime_name_rt_gfx_bitmap_off:
    .asciiz "rt_gfx_bitmap_off"
runtime_name_rt_gfx_mbitmap_on:
    .asciiz "rt_gfx_mbitmap_on"
runtime_name_rt_gfx_mbitmap_off:
    .asciiz "rt_gfx_mbitmap_off"
runtime_name_rt_gfx_bgcolor:
    .asciiz "rt_gfx_bgcolor"
runtime_name_rt_gfx_bordercolor:
    .asciiz "rt_gfx_bordercolor"
runtime_name_rt_gfx_vic_bank:
    .asciiz "rt_gfx_vic_bank"
runtime_name_rt_gfx_screen_base:
    .asciiz "rt_gfx_screen_base"
runtime_name_rt_gfx_bitmap_base:
    .asciiz "rt_gfx_bitmap_base"
runtime_name_rt_gfx_bitmap_fill:
    .asciiz "rt_gfx_bitmap_fill"
runtime_name_rt_gfx_screen_cell:
    .asciiz "rt_gfx_screen_cell"
runtime_name_rt_gfx_color_cell:
    .asciiz "rt_gfx_color_cell"
runtime_name_rt_gfx_screen_copy:
    .asciiz "rt_gfx_screen_copy"
runtime_name_rt_gfx_color_copy:
    .asciiz "rt_gfx_color_copy"
runtime_name_rt_gfx_bitmap_copy:
    .asciiz "rt_gfx_bitmap_copy"
direct_body_real_print_int:
    .asciiz "p1u0T0S0L0U0p2u1r"
direct_body_real_to_int:
    .asciiz "p1u0T0S0L0U0u1S1r"
direct_body_input_real_print_int:
    .asciiz "p0u0p2u1T0S0L0U0p3u2r"
direct_body_input_stored_real_print_int:
    .asciiz "p0u0S0p2u1T1S1L1U1p3u2r"
direct_body_real_print_binary:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1T2S2L2U2p4u2r"
direct_body_real_print_fabs:
    .asciiz "p0u0T0S0L0U0u1T1S1L1U1p1u2r"
direct_body_real_print_unary_positive:
    .asciiz "p1u0T0S0L0U0u1T1S1L1U1p2u2r"
direct_body_real_if_gt:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghp5S2vr"
direct_body_real_if_lt:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1p4lhp5S2vr"
direct_body_real_if_eq:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1p4qhp5S2vr"
direct_body_real_if_ne:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1p4nhp5S2vr"
direct_body_real_if_gt_else:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghp5S2wp6S2vr"
direct_body_real_if_lt_else:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1p4lhp5S2wp6S2vr"
direct_body_real_if_eq_else:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1p4qhp5S2wp6S2vr"
direct_body_real_if_ne_else:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1p4nhp5S2wp6S2vr"
direct_body_real_nested_if_gt:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghL0U0L1U1u1p5ghp6S2vvr"
direct_body_real_nested_if_lt:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1p4lhL0U0L1U1u1p5lhp6S2vvr"
direct_body_real_nested_if_eq:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1p4qhL0U0L1U1u1p5qhp6S2vvr"
direct_body_real_nested_if_ne:
    .asciiz "p1u0T0S0p3u0T1S1L0U0L1U1u1p4nhL0U0L1U1u1p5nhp6S2vvr"
direct_body_real_do_until_eq:
    .asciiz "p0p0T0S0p2u0T1S1dp4u0T0S0L0U0L1U1u1p5qtop6S2r"
direct_body_real_do_until_gt:
    .asciiz "p0p0T0S0p2u0T1S1dp4u0T0S0L0U0L1U1u1p5gtop6S2r"
direct_body_real_do_until_lt:
    .asciiz "p0p0T0S0p2u0T1S1dp4u0T0S0L0U0L1U1u1p5ltop6S2r"
direct_body_real_do_until_ne:
    .asciiz "p0p0T0S0p2u0T1S1dp4u0T0S0L0U0L1U1u1p5ntop6S2r"
direct_body_real_do_until_gt_real_add_loop:
    .asciiz "p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p5gtop6S3r"
direct_body_real_do_until_lt_real_add_loop:
    .asciiz "p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p5ltop6S3r"
direct_body_real_do_until_gt_real_sub_loop:
    .asciiz "p1u0T0S0p2p2T1S1p4u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p5gtop6S3r"
direct_body_real_do_until_lt_real_sub_loop:
    .asciiz "p1u0T0S0p2p2T1S1p4u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p5ltop6S3r"
direct_body_real_do_until_gt_real_sub_loop_rhs_nonzero:
    .asciiz "p1u0T0S0p3u0T1S1p5u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p6gtop7S3r"
direct_body_real_do_until_lt_real_sub_loop_rhs_nonzero:
    .asciiz "p1u0T0S0p3u0T1S1p5u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p6ltop7S3r"
direct_body_real_while_gt_once:
    .asciiz "p1u0T0S0p3u0T1S1dL0U0L1U1u1p4gfp5S2p6p6T0S0xr"
direct_body_real_while_gt_convert_once:
    .asciiz "p1u0T0S0p3u0T1S1dL0U0L1U1u1p4gfp5S2p7u0T0S0xr"
direct_body_real_while_gt_real_sub_loop:
    .asciiz "p1u0T0S0p2p2T1S1p4u0T2S2dL0U0L1U1u1p5gfp6S3L0U0L2U2u2T0S0xr"
direct_body_real_while_gt_real_sub_loop_rhs_nonzero:
    .asciiz "p1u0T0S0p3u0T1S1p5u0T2S2dL0U0L1U1u1p6gfp7S3L0U0L2U2u2T0S0xr"
direct_body_real_while_gt_real_add_loop:
    .asciiz "p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L1U1u1p5gfp6S3L0U0L2U2u2T0S0xr"
direct_body_real_while_lt_real_add_loop:
    .asciiz "p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L1U1u1p5lfp6S3L0U0L2U2u2T0S0xr"
direct_body_real_while_lt_real_sub_loop:
    .asciiz "p1u0T0S0p2p2T1S1p4u0T2S2dL0U0L1U1u1p5lfp6S3L0U0L2U2u2T0S0xr"
direct_body_real_while_lt_once:
    .asciiz "p1u0T0S0p3u0T1S1dL0U0L1U1u1p4lfp5S2p6p6T1S1xr"
direct_body_real_while_lt_convert_once:
    .asciiz "p1u0T0S0p3u0T1S1dL0U0L1U1u1p4lfp5S2p7u0T1S1xr"
linked_body_string_int:
    .asciiz "s0i0r"
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

runtime_helper_prg_exit_template:
    .byte $A9,$A5,$8D,$D0,$03,$A9,$00,$85,$02,$85,$03,$A2,$02,$4C,$0F,$CF
runtime_helper_prg_exit_template_end:
