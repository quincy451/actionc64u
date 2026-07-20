.include "udos_services.inc"
.include "actedit_overlay_abi.inc"

.export start
.export actedit_test_mode
.export actedit_test_key_count
.export actedit_test_key_index
.export actedit_test_keys
.export actedit_test_key0
.export actedit_test_key1
.export actedit_test_key2
.export actedit_test_key3
.export actedit_test_key4
.export actedit_test_key5
.export actedit_test_key6
.export actedit_test_key7
.export actedit_test_key8
.export actedit_test_key9
.export actedit_test_key10
.export actedit_test_key11
.export actedit_test_key12
.export actedit_test_key13
.export actedit_test_key14
.export actedit_test_key15
.export actedit_test_key16
.export actedit_test_key17
.export actedit_test_key18
.export actedit_test_key19
.export actedit_test_key20
.export actedit_test_key21
.export actedit_test_key22
.export actedit_test_key23
.export actedit_source_path
.export actedit_module_name
.export actedit_current_line_lo
.export actedit_current_line_hi
.export actedit_left_col
.export actedit_cursor_col
.export actedit_dirty
.export actedit_source_stage_len_bank
.export actedit_source_line_count_lo
.export actedit_source_line_count_hi
.export actedit_source_line_index_ready
.export actedit_logical_line_count_lo
.export actedit_logical_line_count_hi
.export actedit_logical_line_index_ready
.export actedit_piece_rebuild_count
.export actedit_direct_patch_count
.export actedit_direct_insert_count
.export actedit_direct_remove_count
.export actedit_direct_insert_update_count
.export actedit_logical_index_suffix_count
.export actedit_mutation_overlay_load_count
.export actedit_mutation_overlay_fail_count

SCNKEY = $FF9F
GETIN = $FFE4
CHROUT = $FFD2

KEY_F1 = $85
KEY_F2 = $89
KEY_F3 = $86
KEY_F4 = $8A
KEY_F5 = $87
KEY_F7 = $88
KEY_F6 = $8B
KEY_RUNSTOP = $03
KEY_DELETE = $14
KEY_HOME = $13
KEY_CLRHOME = $93
KEY_INSERT = $94
KEY_RETURN = $0D
KEY_TEST_EXIT = $FF
KEY_DOWN = $11
KEY_RIGHT = $1D
KEY_UP = $91
KEY_LEFT = $9D
KEY_F8 = $8C
KEY_A = $01
KEY_B = $02
KEY_D = $04
KEY_G = $07
KEY_O = $0F
KEY_R = $12
KEY_U = $15
KEY_Y = $19

SCREEN_RAM = $0400
SCREEN_COLS = 40
SCREEN_ROWS = 25
SOURCE_ROWS = 23
SOURCE_ROW_FIRST = 1
HELP_ROW = 24
PATH_LIMIT = 127
LINE_BUFFER_LIMIT = 159
ACTEDIT_FILE_WINDOW_LIMIT = 255
ACTEDIT_SOURCE_REU_BASE_LO = $00
ACTEDIT_SOURCE_REU_BASE_HI = $00
ACTEDIT_SOURCE_REU_BASE_BANK = $07
ACTEDIT_REU_RESERVED_BANK = $FD
ACTEDIT_LINE_INDEX_ENTRY_BYTES = 3
ACTEDIT_LINE_INDEX_WINDOW_LIMIT = 255
ACTEDIT_LOGICAL_INDEX_ENTRY_BYTES = 3
ACTEDIT_LOGICAL_INDEX_WINDOW_LIMIT = 255
ACTEDIT_LOGICAL_INDEX_REU_BASE_LO = $00
ACTEDIT_LOGICAL_INDEX_REU_BASE_HI = $00
ACTEDIT_LOGICAL_INDEX_REU_BASE_BANK = $00
ACTEDIT_LOGICAL_INDEX_REU_END_BANK = $03
OUTPUT_CHUNK_SIZE = 128
PATCH_MAX = 64
INSERT_MAX = 64
DELETE_MAX = 64
TEXT_COL_FIRST = 2
TEXT_COLS = 38
TEST_KEY_LIMIT = 24
CLIPBOARD_LIMIT = 255

LINE_KIND_SOURCE = 0
LINE_KIND_INSERT = 1
PIECE_KIND_SOURCE = 0
PIECE_KIND_PATCH = 1
PIECE_KIND_INSERT = 2
PIECE_MAX = 255
UNDO_STATE_SIZE = 19
PATCH_TABLE_BYTES = PATCH_MAX*5
INSERT_TABLE_BYTES = INSERT_MAX*6
DELETE_TABLE_BYTES = DELETE_MAX*3
ACTEDIT_PIECE_WINDOW_BYTES = PIECE_MAX*6
ACTEDIT_META_REU_BASE_LO = $00
ACTEDIT_META_REU_BASE_HI = $00
ACTEDIT_META_REU_BASE_BANK = $05
ACTEDIT_PATCH_META_REU_OFFSET = $00
ACTEDIT_INSERT_META_REU_OFFSET = PATCH_TABLE_BYTES
ACTEDIT_DELETE_META_REU_OFFSET = PATCH_TABLE_BYTES+INSERT_TABLE_BYTES
ACTEDIT_PIECE_COUNT_REU_OFFSET = PATCH_TABLE_BYTES+INSERT_TABLE_BYTES+DELETE_TABLE_BYTES
ACTEDIT_PIECE_WINDOW_REU_OFFSET = ACTEDIT_PIECE_COUNT_REU_OFFSET+1
ACTEDIT_DESCRIPTOR_WINDOW_BYTES = INSERT_TABLE_BYTES
ACTEDIT_TEXT_REU_BASE_LO = $00
ACTEDIT_TEXT_REU_BASE_HI = $00
ACTEDIT_TEXT_REU_BASE_BANK = $06
UNDO_JOURNAL_DEPTH = 32
UNDO_ENTRY_BYTES = UNDO_STATE_SIZE + (LINE_BUFFER_LIMIT+1) + PATCH_TABLE_BYTES + INSERT_TABLE_BYTES + DELETE_TABLE_BYTES
ACTEDIT_UNDO_REU_BASE_LO = $00
ACTEDIT_UNDO_REU_BASE_HI = $00
ACTEDIT_UNDO_REU_BASE_BANK = $03
ACTEDIT_REDO_REU_BASE_LO = $00
ACTEDIT_REDO_REU_BASE_HI = $00
ACTEDIT_REDO_REU_BASE_BANK = $04
JOURNAL_KIND_UNDO = $00
JOURNAL_KIND_REDO = $01
ACTEDIT_WORKFLOW_COMPILE = $00
ACTEDIT_WORKFLOW_LINK = $01
ACTEDIT_WORKFLOW_DEBUG = $02

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
file_params:
    .res 9
src_ptr:
    .res 2
base_ptr:
    .res 2
row_ptr:
    .res 2
text_ptr:
    .res 2
line_start_ptr:
    .res 2
line_work_ptr:
    .res 2
line_length_ptr:
    .res 2
status_ptr:
    .res 2
line_work_ptr_bank:
    .res 1
line_length_ptr_bank:
    .res 1
status_ptr_bank:
    .res 1

.code

start:
    jsr clear_state
    ldx #svc_retptr
    jsr svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    bne have_args
    lda #<msg_usage
    ldy #>msg_usage
    jmp fail_with_ptr

have_args:
    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    lda svc_retptr
    sta src_ptr
    lda svc_retptr+1
    sta src_ptr+1
    jsr copy_first_arg
    lda arg_buffer
    bne have_arg_text
    lda #<msg_usage
    ldy #>msg_usage
    jmp fail_with_ptr

have_arg_text:
    jsr parse_start_location_suffix
    bcc :+
    lda #<msg_bad_location
    ldy #>msg_bad_location
    jmp fail_with_ptr
:
    jsr build_source_path
    jsr derive_module_name
    jsr load_source_file
    bcc source_ok
    lda #<msg_no_source
    ldy #>msg_no_source
    jmp fail_with_ptr

source_ok:
    jsr count_staged_source_lines
    bcc :+
    lda #<msg_no_source
    ldy #>msg_no_source
    jmp fail_with_ptr
:
    lda #$00
    sta actedit_top_line_hi
    sta actedit_left_col
    sta actedit_cursor_col
    lda #$01
    sta actedit_top_line_lo
    sta actedit_current_line_lo
    lda #$00
    sta actedit_current_line_hi
    lda actedit_start_line_valid
    beq source_position_ready
    lda actedit_start_line_lo
    sta line_number_lo
    lda actedit_start_line_hi
    sta line_number_hi
    jsr source_line_exists_for_line_number
    bcc :+
    lda #<msg_no_line
    ldy #>msg_no_line
    jmp fail_with_ptr
:
    lda line_number_lo
    sta actedit_current_line_lo
    lda line_number_hi
    sta actedit_current_line_hi
source_position_ready:
    jsr load_current_line_for_edit
    jsr ensure_cursor_visible
    jsr render_screen

input_loop:
    jsr read_input_key
    jsr normalize_input_key
    cmp #$00
    beq input_loop
    cmp #KEY_UP
    bne :+
    jmp move_up_key
:   cmp #KEY_DOWN
    bne :+
    jmp move_down_key
:   cmp #KEY_LEFT
    bne :+
    jmp move_left_key
:   cmp #KEY_RIGHT
    bne :+
    jmp move_right_key
:   cmp #KEY_DELETE
    bne :+
    jmp delete_left_key
:   cmp #KEY_HOME
    bne :+
    jmp home_key
:   cmp #KEY_CLRHOME
    bne :+
    jmp page_up_key
:   cmp #KEY_INSERT
    bne :+
    jmp insert_nav_key
:   cmp #KEY_RETURN
    bne :+
    jmp split_line_key
:   cmp #KEY_F3
    bne :+
    jmp mark_key
:   cmp #KEY_F2
    bne :+
    jmp find_next_key
:   cmp #KEY_F1
    bne :+
    jmp save_key
:   cmp #KEY_F4
    bne :+
    jmp find_prev_key
:   cmp #KEY_F5
    bne :+
    jmp copy_key
:   cmp #KEY_F6
    bne :+
    jmp cut_key
:   cmp #KEY_F7
    bne :+
    jmp paste_key
:   cmp #KEY_F8
    bne :+
    jmp page_down_key
:   cmp #KEY_B
    bne :+
    jmp build_key
:   cmp #KEY_D
    bne :+
    jmp debug_key
:   cmp #KEY_O
    bne :+
    jmp compile_key
:   cmp #KEY_A
    bne :+
    jmp replace_all_key
:   cmp #KEY_G
    bne :+
    jmp goto_line_key
:   cmp #KEY_R
    bne :+
    jmp replace_next_key
:   cmp #KEY_U
    bne :+
    jmp undo_key
:   cmp #KEY_Y
    bne :+
    jmp redo_key
:   cmp #KEY_RUNSTOP
    bne :+
    jmp exit_ok
:   cmp #KEY_TEST_EXIT
    bne :+
    jmp exit_ok
:   jsr is_insertable_char
    bcs :+
    pha
    jsr snapshot_undo_state_for_mutation
    pla
    jsr insert_char_at_cursor
    bcs :+
    jsr render_screen
    jmp input_loop
:   jmp input_loop

move_up_key:
    jsr move_cursor_up
    bcs :+
    jsr ensure_cursor_visible
    jsr render_screen
    jmp input_loop
:   jmp input_loop

move_down_key:
    jsr move_cursor_down
    bcs :+
    jsr ensure_cursor_visible
    jsr render_screen
    jmp input_loop
:   jmp input_loop

move_left_key:
    lda actedit_cursor_col
    beq :+
    dec actedit_cursor_col
    jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop
:   jmp input_loop

move_right_key:
    jsr move_cursor_right
    bcc :+
    jmp input_loop
:
    jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop

delete_left_key:
    lda actedit_mark_active
    beq delete_left_key_single
    jsr prepare_selection_bounds
    bcs delete_left_key_single
    lda actedit_selection_start_line_lo
    cmp actedit_selection_end_line_lo
    bne delete_left_key_marked
    lda actedit_selection_start_line_hi
    cmp actedit_selection_end_line_hi
    bne delete_left_key_marked
    lda actedit_selection_start_col
    cmp actedit_selection_end_col
    beq delete_left_key_single
delete_left_key_marked:
    jsr snapshot_undo_state_for_mutation
    jsr delete_marked_range
    bcc :+
    jmp input_loop
:   jsr ensure_cursor_visible
    jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop
delete_left_key_single:
    jsr snapshot_undo_state_for_mutation
    jsr delete_left_at_cursor
    bcc :+
    jmp input_loop
:
    jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop

home_key:
    lda actedit_cursor_col
    beq :+
    lda #$00
    sta actedit_cursor_col
    jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop
:   jsr move_to_file_top
    bcs :+
    jsr ensure_cursor_visible
    jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop
:   jmp input_loop

page_up_key:
    jsr move_page_up
    bcs :+
    jsr ensure_cursor_visible
    jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop
:   jmp input_loop

insert_nav_key:
    lda actedit_cursor_col
    cmp actedit_current_line_len
    beq :+
    lda actedit_current_line_len
    sta actedit_cursor_col
    jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop
:   jsr move_to_file_bottom
    bcs :+
    jsr ensure_cursor_visible
    jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop
:   jmp input_loop

split_line_key:
    jsr snapshot_undo_state_for_mutation
    jsr split_current_line_at_cursor
    bcc :+
    jmp input_loop
:   jsr ensure_cursor_visible
    jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop

mark_key:
    jsr set_mark_at_cursor
    jsr render_screen
    jmp input_loop

find_next_key:
    jsr find_next_from_context
    bcc :+
    jmp input_loop
:   jsr ensure_cursor_visible
    jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop

save_key:
    jsr save_current_file
    bcc :+
    jmp input_loop
:   
    jsr render_screen
    jmp input_loop

compile_key:
    lda #ACTEDIT_WORKFLOW_COMPILE
    beq workflow_key

build_key:
    lda #ACTEDIT_WORKFLOW_LINK
    bne workflow_key

debug_key:
    lda #ACTEDIT_WORKFLOW_DEBUG
workflow_key:
    sta actedit_workflow_mode
    jsr save_current_file
    bcs workflow_key_fail
    jsr build_workflow_command
    bcs workflow_key_fail
    lda #<arg_buffer
    sta svc_retptr
    lda #>arg_buffer
    sta svc_retptr+1
    ldx #svc_retptr
    jsr svc_program_chain_sc0
    bcs workflow_key_fail
    jmp exit_ok
workflow_key_fail:
    jsr render_screen
    jmp input_loop

find_prev_key:
    jsr find_prev_from_context
    bcc :+
    jmp input_loop
:   jsr ensure_cursor_visible
    jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop

copy_key:
    jsr copy_marked_range_to_clipboard
    bcc :+
    jmp input_loop
:   jsr render_screen
    jmp input_loop

cut_key:
    jsr snapshot_undo_state_for_mutation
    jsr cut_marked_range_to_clipboard
    bcc :+
    jmp input_loop
:   jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop

paste_key:
    jsr snapshot_undo_state_for_mutation
    jsr paste_clipboard_at_cursor
    bcc :+
    jmp input_loop
:   jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop

page_down_key:
    jsr move_page_down
    bcs :+
    jsr ensure_cursor_visible
    jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop
:   jmp input_loop

goto_line_key:
    jsr prompt_goto_line_number
    bcs :+
    jsr commit_current_line_patch_if_dirty
    bcs :+
    jsr source_line_exists_for_line_number
    bcs :+
    lda line_number_lo
    sta actedit_current_line_lo
    lda line_number_hi
    sta actedit_current_line_hi
    jsr load_current_line_for_edit
    lda #$00
    sta actedit_cursor_col
    jsr ensure_cursor_visible
    jsr render_screen
    jmp input_loop
:   jsr render_screen
    jmp input_loop

replace_next_key:
    jsr prompt_replace_text
    bcs :+
    jsr snapshot_undo_state_for_mutation
    jsr replace_next_from_context
    bcs :+
    jsr ensure_cursor_visible
    jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop
:   jsr render_screen
    jmp input_loop

replace_all_key:
    jsr prompt_replace_text
    bcs replace_all_key_render
    jsr snapshot_undo_state_for_mutation
    bcs replace_all_key_render
    jsr replace_all_from_context
    bcc replace_all_key_done
    jsr restore_undo_state
    jmp replace_all_key_render
replace_all_key_done:
    jsr ensure_cursor_visible
    jsr ensure_cursor_column_visible
replace_all_key_render:
    jsr render_screen
    jmp input_loop

undo_key:
    jsr snapshot_redo_state
    bcc :+
    jmp input_loop
:   jsr restore_undo_state
    bcc :+
    jsr discard_latest_redo_snapshot
    jmp input_loop
:   jsr ensure_cursor_visible
    jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop

redo_key:
    jsr snapshot_undo_state
    bcc :+
    jmp input_loop
:   jsr restore_redo_state
    bcc :+
    jsr discard_latest_undo_snapshot
    jmp input_loop
:   jsr ensure_cursor_visible
    jsr ensure_cursor_column_visible
    jsr render_screen
    jmp input_loop

exit_ok:
    lda actedit_test_mode
    bne :+
    lda #KEY_CLRHOME
    jsr CHROUT
:
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

clear_state:
    lda #$00
    sta actedit_source_stage_len_lo
    sta actedit_source_stage_len_hi
    sta actedit_source_stage_len_bank
    sta actedit_file_window_start_lo
    sta actedit_file_window_start_hi
    sta actedit_file_window_start_bank
    sta actedit_file_window_end_lo
    sta actedit_file_window_end_hi
    sta actedit_file_window_end_bank
    sta line_work_ptr_bank
    sta line_length_ptr_bank
    sta status_ptr_bank
    sta actedit_current_line_hi
    sta actedit_top_line_hi
    sta actedit_left_col
    sta actedit_cursor_col
    sta actedit_dirty
    sta actedit_current_line_dirty
    sta actedit_mark_active
    sta actedit_mark_col
    sta actedit_mark_line_lo
    sta actedit_mark_line_hi
    sta actedit_selection_start_line_lo
    sta actedit_selection_start_line_hi
    sta actedit_selection_start_col
    sta actedit_selection_end_line_lo
    sta actedit_selection_end_line_hi
    sta actedit_selection_end_col
    sta actedit_clipboard_len
    sta actedit_search_len
    sta actedit_search_start_col
    sta actedit_search_limit_col
    sta actedit_search_match_col
    sta actedit_search_last_col
    sta actedit_search_found
    sta actedit_output_chunk_len
    sta actedit_prompt_len
    sta actedit_clipboard_index
    sta actedit_undo_count
    sta actedit_undo_head_slot
    sta actedit_undo_slot
    sta actedit_redo_count
    sta actedit_redo_head_slot
    sta actedit_redo_slot
    sta actedit_journal_kind
    sta arg_buffer
    sta actedit_source_path
    sta actedit_prompt_buffer
    sta actedit_current_line_kind
    sta actedit_current_line_insert_slot
    sta actedit_current_source_line_lo
    sta actedit_current_source_line_hi
    sta actedit_loaded_line_kind
    sta actedit_loaded_insert_slot
    sta actedit_loaded_source_line_lo
    sta actedit_loaded_source_line_hi
    sta actedit_source_line_count_lo
    sta actedit_source_line_count_hi
    sta actedit_source_line_index_base_lo
    sta actedit_source_line_index_base_hi
    sta actedit_source_line_index_base_bank
    sta actedit_source_line_index_next_lo
    sta actedit_source_line_index_next_hi
    sta actedit_source_line_index_next_bank
    sta actedit_source_line_index_window_len
    sta actedit_source_line_index_ready
    sta actedit_logical_line_count_lo
    sta actedit_logical_line_count_hi
    sta actedit_logical_line_index_next_lo
    sta actedit_logical_line_index_next_hi
    sta actedit_logical_line_index_next_bank
    sta actedit_logical_line_index_window_len
    sta actedit_logical_line_index_ready
    sta actedit_start_line_valid
    sta actedit_start_line_lo
    sta actedit_start_line_hi
    sta actedit_piece_count
    sta actedit_piece_loaded
    sta actedit_piece_rebuild_count
    sta actedit_direct_patch_count
    sta actedit_direct_insert_count
    sta actedit_direct_remove_count
    sta actedit_direct_insert_update_count
    sta actedit_logical_index_suffix_count
    sta actedit_direct_patch_ready
    sta actedit_direct_insert_ready
    sta actedit_direct_remove_ready
    sta actedit_mutation_overlay_state
    sta actedit_mutation_overlay_load_count
    sta actedit_mutation_overlay_fail_count
    sta actedit_test_key_index
    lda #$01
    sta actedit_piece_dirty
    lda #$00
    lda actedit_test_mode
    bne :+
    sta actedit_test_key_count
:   
    jsr clear_patch_table
    jsr clear_insert_table
    jsr clear_delete_table
    jsr reset_add_buffer_state
    rts

snapshot_undo_state_for_mutation:
    jsr snapshot_undo_state
    bcs snapshot_undo_state_for_mutation_fail
    jsr clear_redo_state
    clc
    rts
snapshot_undo_state_for_mutation_fail:
    sec
    rts

snapshot_undo_state:
    lda #JOURNAL_KIND_UNDO
    sta actedit_journal_kind
    jmp snapshot_selected_state

snapshot_redo_state:
    lda #JOURNAL_KIND_REDO
    sta actedit_journal_kind
    jmp snapshot_selected_state

snapshot_selected_state:
    jsr fill_undo_state_buffer_from_live
    jsr get_selected_head_slot
    jsr set_word_tmp_to_selected_slot_base_a
    lda #<actedit_undo_state_buffer
    sta text_ptr
    lda #>actedit_undo_state_buffer
    sta text_ptr+1
    lda #<UNDO_STATE_SIZE
    sta line_number_lo
    lda #>UNDO_STATE_SIZE
    sta line_number_hi
    jsr write_undo_region
    bcc :+
    jmp snapshot_undo_state_fail
:
    jsr advance_word_tmp_by_line_number
    lda #<actedit_current_line_buffer
    sta text_ptr
    lda #>actedit_current_line_buffer
    sta text_ptr+1
    lda #<(LINE_BUFFER_LIMIT+1)
    sta line_number_lo
    lda #>(LINE_BUFFER_LIMIT+1)
    sta line_number_hi
    jsr write_undo_region
    bcc :+
    jmp snapshot_undo_state_fail
:
    jsr advance_word_tmp_by_line_number
    jsr load_patch_meta_window
    bcc :+
    jmp snapshot_undo_state_fail
:   lda #<actedit_descriptor_window
    sta text_ptr
    lda #>actedit_descriptor_window
    sta text_ptr+1
    lda #<PATCH_TABLE_BYTES
    sta line_number_lo
    lda #>PATCH_TABLE_BYTES
    sta line_number_hi
    jsr write_undo_region
    bcc :+
    jmp snapshot_undo_state_fail
:
    jsr advance_word_tmp_by_line_number
    jsr load_insert_meta_window
    bcc :+
    jmp snapshot_undo_state_fail
:   lda #<actedit_descriptor_window
    sta text_ptr
    lda #>actedit_descriptor_window
    sta text_ptr+1
    lda #<INSERT_TABLE_BYTES
    sta line_number_lo
    lda #>INSERT_TABLE_BYTES
    sta line_number_hi
    jsr write_undo_region
    bcc :+
    jmp snapshot_undo_state_fail
:
    jsr advance_word_tmp_by_line_number
    jsr load_delete_meta_window
    bcc :+
    jmp snapshot_undo_state_fail
:   lda #<actedit_descriptor_window
    sta text_ptr
    lda #>actedit_descriptor_window
    sta text_ptr+1
    lda #<DELETE_TABLE_BYTES
    sta line_number_lo
    lda #>DELETE_TABLE_BYTES
    sta line_number_hi
    jsr write_undo_region
    bcc :+
    jmp snapshot_undo_state_fail
:
    jsr advance_word_tmp_by_line_number
    jsr advance_selected_head_and_count
    clc
    rts
snapshot_undo_state_fail:
    sec
    rts

restore_undo_state:
    lda #JOURNAL_KIND_UNDO
    sta actedit_journal_kind
    jmp restore_selected_state

restore_redo_state:
    lda #JOURNAL_KIND_REDO
    sta actedit_journal_kind
    jmp restore_selected_state

restore_selected_state:
    jsr get_selected_count
    bne :+
    sec
    rts
:   jsr get_selected_head_slot
    bne :+
    lda #UNDO_JOURNAL_DEPTH
:   sec
    sbc #$01
    jsr set_selected_slot_from_a
    jsr set_word_tmp_to_selected_slot_base_a
    lda #<actedit_undo_state_buffer
    sta text_ptr
    lda #>actedit_undo_state_buffer
    sta text_ptr+1
    lda #<UNDO_STATE_SIZE
    sta line_number_lo
    lda #>UNDO_STATE_SIZE
    sta line_number_hi
    jsr read_undo_region
    bcc :+
    jmp restore_undo_state_fail
:   
    jsr advance_word_tmp_by_line_number
    lda #<actedit_current_line_buffer
    sta text_ptr
    lda #>actedit_current_line_buffer
    sta text_ptr+1
    lda #<(LINE_BUFFER_LIMIT+1)
    sta line_number_lo
    lda #>(LINE_BUFFER_LIMIT+1)
    sta line_number_hi
    jsr read_undo_region
    bcc :+
    jmp restore_undo_state_fail
:   
    jsr advance_word_tmp_by_line_number
    lda #<actedit_descriptor_window
    sta text_ptr
    lda #>actedit_descriptor_window
    sta text_ptr+1
    lda #<PATCH_TABLE_BYTES
    sta line_number_lo
    lda #>PATCH_TABLE_BYTES
    sta line_number_hi
    jsr read_undo_region
    bcc :+
    jmp restore_undo_state_fail
:   
    jsr save_patch_meta_window
    bcc :+
    jmp restore_undo_state_fail
:   
    jsr advance_word_tmp_by_line_number
    lda #<actedit_descriptor_window
    sta text_ptr
    lda #>actedit_descriptor_window
    sta text_ptr+1
    lda #<INSERT_TABLE_BYTES
    sta line_number_lo
    lda #>INSERT_TABLE_BYTES
    sta line_number_hi
    jsr read_undo_region
    bcc :+
    jmp restore_undo_state_fail
:   
    jsr save_insert_meta_window
    bcc :+
    jmp restore_undo_state_fail
:   
    jsr advance_word_tmp_by_line_number
    lda #<actedit_descriptor_window
    sta text_ptr
    lda #>actedit_descriptor_window
    sta text_ptr+1
    lda #<DELETE_TABLE_BYTES
    sta line_number_lo
    lda #>DELETE_TABLE_BYTES
    sta line_number_hi
    jsr read_undo_region
    bcc :+
    jmp restore_undo_state_fail
:   
    jsr save_delete_meta_window
    bcc :+
    jmp restore_undo_state_fail
:   
    jsr restore_live_state_from_undo_buffer
    jsr commit_selected_restore
    clc
    rts
restore_undo_state_fail:
    sec
    rts

discard_latest_undo_snapshot:
    lda #JOURNAL_KIND_UNDO
    sta actedit_journal_kind
    jmp discard_latest_selected_snapshot

discard_latest_redo_snapshot:
    lda #JOURNAL_KIND_REDO
    sta actedit_journal_kind
    jmp discard_latest_selected_snapshot

discard_latest_selected_snapshot:
    jsr get_selected_count
    bne :+
    sec
    rts
:   jsr get_selected_head_slot
    bne :+
    lda #UNDO_JOURNAL_DEPTH
:   sec
    sbc #$01
    jsr set_selected_head_slot_from_a
    jsr decrement_selected_count
    clc
    rts

fill_undo_state_buffer_from_live:
    lda actedit_current_line_lo
    sta actedit_undo_state_buffer+0
    lda actedit_current_line_hi
    sta actedit_undo_state_buffer+1
    lda actedit_top_line_lo
    sta actedit_undo_state_buffer+2
    lda actedit_top_line_hi
    sta actedit_undo_state_buffer+3
    lda actedit_left_col
    sta actedit_undo_state_buffer+4
    lda actedit_cursor_col
    sta actedit_undo_state_buffer+5
    lda actedit_current_line_len
    sta actedit_undo_state_buffer+6
    lda actedit_current_line_dirty
    sta actedit_undo_state_buffer+7
    lda actedit_dirty
    sta actedit_undo_state_buffer+8
    lda actedit_current_line_kind
    sta actedit_undo_state_buffer+9
    lda actedit_current_line_insert_slot
    sta actedit_undo_state_buffer+10
    lda actedit_current_source_line_lo
    sta actedit_undo_state_buffer+11
    lda actedit_current_source_line_hi
    sta actedit_undo_state_buffer+12
    lda actedit_mark_active
    sta actedit_undo_state_buffer+13
    lda actedit_mark_col
    sta actedit_undo_state_buffer+14
    lda actedit_mark_line_lo
    sta actedit_undo_state_buffer+15
    lda actedit_mark_line_hi
    sta actedit_undo_state_buffer+16
    lda actedit_text_next_lo
    sta actedit_undo_state_buffer+17
    lda actedit_text_next_hi
    sta actedit_undo_state_buffer+18
    rts

restore_live_state_from_undo_buffer:
    lda actedit_undo_state_buffer+0
    sta actedit_current_line_lo
    lda actedit_undo_state_buffer+1
    sta actedit_current_line_hi
    lda actedit_undo_state_buffer+2
    sta actedit_top_line_lo
    lda actedit_undo_state_buffer+3
    sta actedit_top_line_hi
    lda actedit_undo_state_buffer+4
    sta actedit_left_col
    lda actedit_undo_state_buffer+5
    sta actedit_cursor_col
    lda actedit_undo_state_buffer+6
    sta actedit_current_line_len
    lda actedit_undo_state_buffer+7
    sta actedit_current_line_dirty
    lda actedit_undo_state_buffer+8
    sta actedit_dirty
    lda actedit_undo_state_buffer+9
    sta actedit_current_line_kind
    lda actedit_undo_state_buffer+10
    sta actedit_current_line_insert_slot
    lda actedit_undo_state_buffer+11
    sta actedit_current_source_line_lo
    lda actedit_undo_state_buffer+12
    sta actedit_current_source_line_hi
    lda actedit_undo_state_buffer+13
    sta actedit_mark_active
    lda actedit_undo_state_buffer+14
    sta actedit_mark_col
    lda actedit_undo_state_buffer+15
    sta actedit_mark_line_lo
    lda actedit_undo_state_buffer+16
    sta actedit_mark_line_hi
    lda actedit_undo_state_buffer+17
    sta actedit_text_next_lo
    lda actedit_undo_state_buffer+18
    sta actedit_text_next_hi
    lda #$00
    sta actedit_selection_start_line_lo
    sta actedit_selection_start_line_hi
    sta actedit_selection_start_col
    sta actedit_selection_end_line_lo
    sta actedit_selection_end_line_hi
    sta actedit_selection_end_col
    sta actedit_loaded_line_kind
    sta actedit_loaded_insert_slot
    sta actedit_loaded_source_line_lo
    sta actedit_loaded_source_line_hi
    sta actedit_saved_line_kind
    sta actedit_saved_insert_slot
    sta actedit_saved_source_line_lo
    sta actedit_saved_source_line_hi
    sta actedit_insert_search_order
    sta actedit_insert_found_order
    sta actedit_insert_found_slot
    rts

advance_word_tmp_by_line_number:
    clc
    lda word_tmp
    adc line_number_lo
    sta word_tmp
    lda word_tmp+1
    adc line_number_hi
    sta word_tmp+1
    rts

set_word_tmp_to_selected_slot_base_a:
    jsr set_selected_slot_from_a
    lda #$00
    sta word_tmp
    sta word_tmp+1
    jsr get_selected_slot
    tax
    beq set_word_tmp_to_selected_slot_done
set_word_tmp_to_selected_slot_loop:
    clc
    lda word_tmp
    adc #<UNDO_ENTRY_BYTES
    sta word_tmp
    lda word_tmp+1
    adc #>UNDO_ENTRY_BYTES
    sta word_tmp+1
    dex
    bne set_word_tmp_to_selected_slot_loop
set_word_tmp_to_selected_slot_done:
    rts

set_undo_reu_params_from_word_tmp:
    lda word_tmp
    clc
    adc #ACTEDIT_UNDO_REU_BASE_LO
    sta file_params+0
    lda word_tmp+1
    adc #ACTEDIT_UNDO_REU_BASE_HI
    sta file_params+1
    lda actedit_journal_kind
    beq set_undo_reu_params_use_undo
    lda #ACTEDIT_REDO_REU_BASE_BANK
    bne set_undo_reu_params_store_bank
set_undo_reu_params_use_undo:
    lda #ACTEDIT_UNDO_REU_BASE_BANK
set_undo_reu_params_store_bank:
    sta file_params+2
    rts

get_selected_count:
    lda actedit_journal_kind
    beq :+
    lda actedit_redo_count
    rts
:   lda actedit_undo_count
    rts

get_selected_head_slot:
    lda actedit_journal_kind
    beq :+
    lda actedit_redo_head_slot
    rts
:   lda actedit_undo_head_slot
    rts

get_selected_slot:
    lda actedit_journal_kind
    beq :+
    lda actedit_redo_slot
    rts
:   lda actedit_undo_slot
    rts

set_selected_slot_from_a:
    ldx actedit_journal_kind
    beq :+
    sta actedit_redo_slot
    rts
:   sta actedit_undo_slot
    rts

set_selected_head_slot_from_a:
    ldx actedit_journal_kind
    beq :+
    sta actedit_redo_head_slot
    rts
:   sta actedit_undo_head_slot
    rts

advance_selected_head_and_count:
    ldx actedit_journal_kind
    beq advance_selected_head_and_count_undo
    inc actedit_redo_head_slot
    lda actedit_redo_head_slot
    cmp #UNDO_JOURNAL_DEPTH
    bcc :+
    lda #$00
    sta actedit_redo_head_slot
:   lda actedit_redo_count
    cmp #UNDO_JOURNAL_DEPTH
    bcs :+
    inc actedit_redo_count
:   rts
advance_selected_head_and_count_undo:
    inc actedit_undo_head_slot
    lda actedit_undo_head_slot
    cmp #UNDO_JOURNAL_DEPTH
    bcc :+
    lda #$00
    sta actedit_undo_head_slot
:   lda actedit_undo_count
    cmp #UNDO_JOURNAL_DEPTH
    bcs :+
    inc actedit_undo_count
:   rts

commit_selected_restore:
    ldx actedit_journal_kind
    beq commit_selected_restore_undo
    lda actedit_redo_slot
    sta actedit_redo_head_slot
    dec actedit_redo_count
    rts
commit_selected_restore_undo:
    lda actedit_undo_slot
    sta actedit_undo_head_slot
    dec actedit_undo_count
    rts

decrement_selected_count:
    ldx actedit_journal_kind
    beq :+
    dec actedit_redo_count
    rts
:   dec actedit_undo_count
    rts

clear_redo_state:
    lda #$00
    sta actedit_redo_count
    sta actedit_redo_head_slot
    sta actedit_redo_slot
    rts

write_undo_region:
    jsr set_undo_reu_params_from_word_tmp
    lda text_ptr
    sta file_params+3
    lda text_ptr+1
    sta file_params+4
    lda line_number_lo
    sta file_params+5
    lda line_number_hi
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:   clc
    rts

read_undo_region:
    jsr set_undo_reu_params_from_word_tmp
    lda text_ptr
    sta file_params+3
    lda text_ptr+1
    sta file_params+4
    lda line_number_lo
    sta file_params+5
    lda line_number_hi
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:   clc
    rts

copy_first_arg:
    ldy #$00
    ldx #$00
copy_first_arg_loop:
    lda (src_ptr),y
    beq copy_first_arg_done
    cmp #' '
    beq copy_first_arg_done
    cpx #PATH_LIMIT
    bcs copy_first_arg_done
    sta arg_buffer,x
    inx
    iny
    bne copy_first_arg_loop
copy_first_arg_done:
    lda #$00
    sta arg_buffer,x
    rts

parse_start_location_suffix:
    lda #$00
    sta actedit_start_line_valid
    ldx #$00
parse_start_location_find_end:
    lda arg_buffer,x
    beq parse_start_location_have_end
    inx
    cpx #PATH_LIMIT
    bcc parse_start_location_find_end
parse_start_location_have_end:
    stx actedit_arg_len
    cpx #$00
    beq parse_start_location_none
parse_start_location_find_separator:
    dex
    lda arg_buffer,x
    cmp #':'
    beq parse_start_location_candidate
    cpx #$00
    bne parse_start_location_find_separator
parse_start_location_none:
    clc
    rts

parse_start_location_candidate:
    stx actedit_location_separator
    cpx #$00
    bne :+
    jmp parse_start_location_invalid
:
    inx
    cpx actedit_arg_len
    bcs parse_start_location_none
parse_start_location_validate_digits:
    lda arg_buffer,x
    cmp #'0'
    bcc parse_start_location_none
    cmp #'9'+1
    bcs parse_start_location_none
    inx
    cpx actedit_arg_len
    bcc parse_start_location_validate_digits

    lda #$00
    sta actedit_start_line_lo
    sta actedit_start_line_hi
    ldx actedit_location_separator
    inx
parse_start_location_digit_loop:
    lda actedit_start_line_hi
    cmp #>6553
    bcc parse_start_location_multiply
    bne parse_start_location_invalid
    lda actedit_start_line_lo
    cmp #<6553
    bcc parse_start_location_multiply
    bne parse_start_location_invalid
    lda arg_buffer,x
    cmp #'5'+1
    bcs parse_start_location_invalid
parse_start_location_multiply:
    lda actedit_start_line_lo
    sta word_tmp
    lda actedit_start_line_hi
    sta word_tmp+1
    asl actedit_start_line_lo
    rol actedit_start_line_hi
    asl word_tmp
    rol word_tmp+1
    asl word_tmp
    rol word_tmp+1
    asl word_tmp
    rol word_tmp+1
    clc
    lda actedit_start_line_lo
    adc word_tmp
    sta actedit_start_line_lo
    lda actedit_start_line_hi
    adc word_tmp+1
    sta actedit_start_line_hi
    lda arg_buffer,x
    sec
    sbc #'0'
    clc
    adc actedit_start_line_lo
    sta actedit_start_line_lo
    bcc :+
    inc actedit_start_line_hi
:
    inx
    cpx actedit_arg_len
    bcc parse_start_location_digit_loop
    lda actedit_start_line_lo
    ora actedit_start_line_hi
    beq parse_start_location_invalid
    ldx actedit_location_separator
    lda #$00
    sta arg_buffer,x
    lda #$01
    sta actedit_start_line_valid
    clc
    rts

parse_start_location_invalid:
    sec
    rts

build_source_path:
    ldx #$00
build_source_path_probe:
    lda arg_buffer,x
    beq build_source_path_module
    cmp #'/'
    beq build_source_path_direct
    cmp #'.'
    beq build_source_path_direct
    inx
    bne build_source_path_probe
build_source_path_direct:
    ldx #$00
build_source_path_copy_direct:
    lda arg_buffer,x
    sta actedit_source_path,x
    beq build_source_path_done
    inx
    cpx #PATH_LIMIT
    bcc build_source_path_copy_direct
    lda #$00
    sta actedit_source_path+PATH_LIMIT
    rts
build_source_path_module:
    lda #'s'
    sta actedit_source_path+0
    lda #'r'
    sta actedit_source_path+1
    lda #'c'
    sta actedit_source_path+2
    lda #'/'
    sta actedit_source_path+3
    ldx #$00
build_source_path_module_loop:
    lda arg_buffer,x
    beq build_source_path_module_suffix
    cmp #$01
    bcc build_source_path_module_check_ascii
    cmp #$1B
    bcs build_source_path_module_check_ascii
    clc
    adc #$60
    bne build_source_path_module_store
build_source_path_module_check_ascii:
    cmp #'A'
    bcc build_source_path_module_store
    cmp #'Z'+1
    bcs build_source_path_module_store
    ora #$20
build_source_path_module_store:
    sta actedit_source_path+4,x
    inx
    cpx #120
    bcc build_source_path_module_loop
build_source_path_module_suffix:
    lda #'.'
    sta actedit_source_path+4,x
    inx
    lda #'a'
    sta actedit_source_path+4,x
    inx
    lda #'c'
    sta actedit_source_path+4,x
    inx
    lda #'t'
    sta actedit_source_path+4,x
    inx
    lda #$00
    sta actedit_source_path+4,x
build_source_path_done:
    rts

derive_module_name:
    lda #$00
    sta actedit_module_name
    sta actedit_prompt_len
    ldy #$00
derive_module_name_scan:
    lda actedit_source_path,y
    beq derive_module_name_copy_begin
    cmp #'/'
    bne derive_module_name_scan_next
    iny
    sty actedit_prompt_len
    dey
derive_module_name_scan_next:
    iny
    cpy #PATH_LIMIT
    bcc derive_module_name_scan
    jmp derive_module_name_fail
derive_module_name_copy_begin:
    ldy actedit_prompt_len
    ldx #$00
derive_module_name_copy:
    lda actedit_source_path,y
    beq derive_module_name_done
    cmp #'.'
    beq derive_module_name_done
    cpx #24
    bcs derive_module_name_fail
    cmp #$01
    bcc derive_module_name_ascii
    cmp #$1B
    bcs derive_module_name_ascii
    clc
    adc #$40
derive_module_name_ascii:
    cmp #'a'
    bcc derive_module_name_store
    cmp #'z'+1
    bcs derive_module_name_store
    and #$DF
derive_module_name_store:
    sta actedit_module_name,x
    inx
    iny
    bne derive_module_name_copy
derive_module_name_done:
    cpx #$00
    beq derive_module_name_fail
    lda #$00
    sta actedit_module_name,x
    sta actedit_prompt_len
    clc
    rts
derive_module_name_fail:
    lda #$00
    sta actedit_module_name
    sta actedit_prompt_len
    sec
    rts

build_workflow_command:
    lda actedit_module_name
    beq build_workflow_command_fail
    ldy #$00
build_workflow_command_prefix:
    lda workflow_actc_prefix,y
    beq build_workflow_command_module_begin
    sta arg_buffer,y
    iny
    bne build_workflow_command_prefix
build_workflow_command_module_begin:
    ldx #$00
build_workflow_command_module:
    lda actedit_module_name,x
    beq build_workflow_command_suffix
    sta arg_buffer,y
    iny
    inx
    bne build_workflow_command_module
build_workflow_command_suffix:
    lda actedit_workflow_mode
    beq build_workflow_command_compile
    cmp #ACTEDIT_WORKFLOW_LINK
    bne build_workflow_command_debug
    lda #','
    bne build_workflow_command_store_suffix
build_workflow_command_compile:
    lda #';'
    bne build_workflow_command_store_suffix
build_workflow_command_debug:
    lda #':'
build_workflow_command_store_suffix:
    sta arg_buffer,y
    iny
build_workflow_command_done:
    lda #$00
    sta arg_buffer,y
    cpy #$00
    beq build_workflow_command_fail
    clc
    rts
build_workflow_command_fail:
    sec
    rts

load_source_file:
    lda #<actedit_source_path
    sta file_params+0
    lda #>actedit_source_path
    sta file_params+1
    lda #ACTEDIT_SOURCE_REU_BASE_LO
    sta file_params+2
    lda #ACTEDIT_SOURCE_REU_BASE_HI
    sta file_params+3
    lda #ACTEDIT_SOURCE_REU_BASE_BANK
    sta file_params+4
    lda #$00
    sta file_params+5
    sta file_params+6
    sta file_params+7
    sta file_params+8
    ldx #file_params
    jsr svc_file_stage_reu_sc0
    lda file_params+5
    cmp #tool_file_status_ok
    bne load_source_fail
    lda file_params+6
    sta actedit_source_stage_len_lo
    lda file_params+7
    sta actedit_source_stage_len_hi
    lda file_params+8
    sta actedit_source_stage_len_bank
    jsr initialize_source_line_index
    bcs load_source_fail
    lda #$00
    sta actedit_file_window_start_lo
    sta actedit_file_window_start_hi
    sta actedit_file_window_start_bank
    sta actedit_file_window_end_lo
    sta actedit_file_window_end_hi
    sta actedit_file_window_end_bank
    clc
    rts
load_source_fail:
    sec
    rts

initialize_source_line_index:
    lda actedit_source_stage_len_lo
    sta actedit_source_line_index_base_lo
    sta actedit_source_line_index_next_lo
    lda actedit_source_stage_len_hi
    sta actedit_source_line_index_base_hi
    sta actedit_source_line_index_next_hi
    clc
    lda actedit_source_stage_len_bank
    adc #ACTEDIT_SOURCE_REU_BASE_BANK
    bcs initialize_source_line_index_fail
    cmp #ACTEDIT_REU_RESERVED_BANK
    bcs initialize_source_line_index_fail
    sta actedit_source_line_index_base_bank
    sta actedit_source_line_index_next_bank
    lda #$00
    sta actedit_source_line_index_window_len
    sta actedit_source_line_index_ready
    clc
    rts
initialize_source_line_index_fail:
    sec
    rts

render_screen:
    lda #<SCREEN_RAM
    sta base_ptr
    lda #>SCREEN_RAM
    sta base_ptr+1
    jsr fill_screen_spaces

    lda #$00
    sta current_row
    sta current_col
    lda #<title_prefix
    ldy #>title_prefix
    jsr draw_const_string_at
    lda #$00
    sta current_row
    lda #$08
    sta current_col
    lda #<actedit_source_path
    ldy #>actedit_source_path
    jsr draw_const_string_at

    lda actedit_top_line_lo
    sta work_line_lo
    lda actedit_top_line_hi
    sta work_line_hi
    ldx #$00
render_rows_loop:
    cpx #SOURCE_ROWS
    bcs render_help
    txa
    clc
    adc #SOURCE_ROW_FIRST
    sta current_row
    lda work_line_lo
    pha
    lda work_line_hi
    pha
    txa
    pha
    jsr draw_source_row
    pla
    tax
    pla
    sta work_line_hi
    pla
    sta work_line_lo
    inc work_line_lo
    bne :+
    inc work_line_hi
:   inx
    jmp render_rows_loop

render_help:
    lda #HELP_ROW
    sta current_row
    lda #$00
    sta current_col
    lda #<help_line
    ldy #>help_line
    jsr draw_const_string_at
    lda actedit_dirty
    beq render_help_done
    lda #HELP_ROW
    sta current_row
    lda #32
    sta current_col
    lda #<dirty_suffix
    ldy #>dirty_suffix
    jsr draw_const_string_at
render_help_done:
    rts

draw_source_row:
    lda current_row
    ldx #$00
    jsr calc_row_ptr
    ldy #$00
    lda work_line_lo
    cmp actedit_current_line_lo
    bne draw_source_row_not_cursor
    lda work_line_hi
    cmp actedit_current_line_hi
    bne draw_source_row_not_cursor
    lda #'>'
    bne draw_source_row_marker
draw_source_row_not_cursor:
    lda #' '
draw_source_row_marker:
    jsr ascii_to_screen
    sta (row_ptr),y
    iny
    lda #' '
    jsr ascii_to_screen
    sta (row_ptr),y
    iny
    sty current_col
    jsr select_render_text_for_work_line
    jsr apply_left_col_offset_to_text_ptr

draw_source_chars_loop:
    ldy #$00
    lda (text_ptr),y
    beq draw_source_chars_done
    cmp #$0D
    beq draw_source_chars_done
    cmp #$0A
    beq draw_source_chars_done
    ldy current_col
    cpy #SCREEN_COLS
    bcs draw_source_chars_done
    jsr ascii_to_screen
    sta (row_ptr),y
    inc text_ptr
    bne :+
    inc text_ptr+1
:   inc current_col
    jmp draw_source_chars_loop
draw_source_chars_done:
    rts

select_render_text_for_work_line:
    lda work_line_lo
    cmp actedit_current_line_lo
    bne select_render_text_other_line
    lda work_line_hi
    cmp actedit_current_line_hi
    bne select_render_text_other_line
    lda #<actedit_current_line_buffer
    sta text_ptr
    lda #>actedit_current_line_buffer
    sta text_ptr+1
    rts
select_render_text_other_line:
    lda work_line_lo
    sta line_number_lo
    lda work_line_hi
    sta line_number_hi
    jsr source_line_exists_for_line_number
    bcc select_render_text_load_line
    lda #$00
    sta line_buffer
    jmp select_render_text_use_line_buffer
select_render_text_load_line:
    jsr load_line_number_into_line_buffer
    bcc select_render_text_use_line_buffer
    lda #$00
    sta line_buffer
select_render_text_use_line_buffer:
    lda #<line_buffer
    sta text_ptr
    lda #>line_buffer
    sta text_ptr+1
    rts

apply_left_col_offset_to_text_ptr:
    ldx actedit_left_col
    beq apply_left_col_offset_done
apply_left_col_offset_loop:
    ldy #$00
    lda (text_ptr),y
    beq apply_left_col_offset_done
    cmp #$0D
    beq apply_left_col_offset_done
    cmp #$0A
    beq apply_left_col_offset_done
    inc text_ptr
    bne :+
    inc text_ptr+1
:   dex
    bne apply_left_col_offset_loop
apply_left_col_offset_done:
    rts

move_cursor_up:
    jsr commit_current_line_patch_if_dirty
    bcs move_cursor_up_fail
    lda actedit_current_line_hi
    bne move_cursor_up_step
    lda actedit_current_line_lo
    cmp #$02
    bcc move_cursor_up_fail
move_cursor_up_step:
    lda actedit_current_line_lo
    bne :+
    dec actedit_current_line_hi
:   dec actedit_current_line_lo
    jsr load_current_line_for_edit
    jsr clamp_cursor_col_to_line_len
    clc
    rts
move_cursor_up_fail:
    sec
    rts

move_cursor_down:
    jsr commit_current_line_patch_if_dirty
    bcs move_cursor_down_fail
    lda actedit_current_line_lo
    clc
    adc #$01
    sta line_number_lo
    lda actedit_current_line_hi
    adc #$00
    sta line_number_hi
    jsr source_line_exists_for_line_number
    bcs move_cursor_down_fail
    lda line_number_lo
    sta actedit_current_line_lo
    lda line_number_hi
    sta actedit_current_line_hi
    jsr load_current_line_for_edit
    jsr clamp_cursor_col_to_line_len
    clc
    rts
move_cursor_down_fail:
    sec
    rts

move_to_file_top:
    jsr commit_current_line_patch_if_dirty
    bcs move_to_file_top_fail
    lda #$01
    sta actedit_current_line_lo
    lda #$00
    sta actedit_current_line_hi
    sta actedit_top_line_hi
    sta actedit_left_col
    sta actedit_cursor_col
    lda #$01
    sta actedit_top_line_lo
    jsr load_current_line_for_edit
    clc
    rts
move_to_file_top_fail:
    sec
    rts

move_to_file_bottom:
    jsr commit_current_line_patch_if_dirty
    bcs move_to_file_bottom_fail
move_to_file_bottom_loop:
    lda actedit_current_line_lo
    clc
    adc #$01
    sta line_number_lo
    lda actedit_current_line_hi
    adc #$00
    sta line_number_hi
    jsr source_line_exists_for_line_number
    bcs move_to_file_bottom_done
    lda line_number_lo
    sta actedit_current_line_lo
    lda line_number_hi
    sta actedit_current_line_hi
    jsr load_current_line_for_edit
    jmp move_to_file_bottom_loop
move_to_file_bottom_done:
    lda actedit_current_line_len
    sta actedit_cursor_col
    clc
    rts
move_to_file_bottom_fail:
    sec
    rts

move_page_up:
    jsr commit_current_line_patch_if_dirty
    bcs move_page_up_fail
    ldx #(SOURCE_ROWS-1)
move_page_up_loop:
    cpx #$00
    beq move_page_up_done
    lda actedit_current_line_hi
    bne :+
    lda actedit_current_line_lo
    cmp #$02
    bcc move_page_up_done
:   lda actedit_current_line_lo
    bne :+
    dec actedit_current_line_hi
:   dec actedit_current_line_lo
    dex
    jmp move_page_up_loop
move_page_up_done:
    jsr load_current_line_for_edit
    jsr clamp_cursor_col_to_line_len
    clc
    rts
move_page_up_fail:
    sec
    rts

move_page_down:
    jsr commit_current_line_patch_if_dirty
    bcs move_page_down_fail
    ldx #(SOURCE_ROWS-1)
move_page_down_loop:
    cpx #$00
    beq move_page_down_done
    lda actedit_current_line_lo
    clc
    adc #$01
    sta line_number_lo
    lda actedit_current_line_hi
    adc #$00
    sta line_number_hi
    jsr source_line_exists_for_line_number
    bcs move_page_down_done
    lda line_number_lo
    sta actedit_current_line_lo
    lda line_number_hi
    sta actedit_current_line_hi
    dex
    jmp move_page_down_loop
move_page_down_done:
    jsr load_current_line_for_edit
    jsr clamp_cursor_col_to_line_len
    clc
    rts
move_page_down_fail:
    sec
    rts

ensure_cursor_visible:
    lda actedit_current_line_hi
    cmp actedit_top_line_hi
    bcc ensure_cursor_visible_move_up
    bne ensure_cursor_visible_check_bottom
    lda actedit_current_line_lo
    cmp actedit_top_line_lo
    bcc ensure_cursor_visible_move_up
ensure_cursor_visible_check_bottom:
    sec
    lda actedit_current_line_lo
    sbc actedit_top_line_lo
    sta word_tmp
    lda actedit_current_line_hi
    sbc actedit_top_line_hi
    sta word_tmp+1
    lda word_tmp+1
    bne ensure_cursor_visible_move_down
    lda word_tmp
    cmp #SOURCE_ROWS
    bcc ensure_cursor_visible_done
ensure_cursor_visible_move_down:
    sec
    lda actedit_current_line_lo
    sbc #(SOURCE_ROWS-1)
    sta actedit_top_line_lo
    lda actedit_current_line_hi
    sbc #$00
    sta actedit_top_line_hi
    rts
ensure_cursor_visible_move_up:
    lda actedit_current_line_lo
    sta actedit_top_line_lo
    lda actedit_current_line_hi
    sta actedit_top_line_hi
ensure_cursor_visible_done:
    rts

ensure_cursor_column_visible:
    lda actedit_cursor_col
    cmp actedit_left_col
    bcs ensure_cursor_column_visible_check_right
    sta actedit_left_col
    rts
ensure_cursor_column_visible_check_right:
    sec
    sbc actedit_left_col
    cmp #TEXT_COLS
    bcc ensure_cursor_column_visible_done
    lda actedit_cursor_col
    sec
    sbc #(TEXT_COLS-1)
    sta actedit_left_col
ensure_cursor_column_visible_done:
    rts

move_cursor_right:
    lda actedit_cursor_col
    cmp actedit_current_line_len
    bcs move_cursor_right_fail
    inc actedit_cursor_col
    clc
    rts
move_cursor_right_fail:
    sec
    rts

clamp_cursor_col_to_line_len:
    lda actedit_cursor_col
    cmp actedit_current_line_len
    bcc clamp_cursor_col_to_line_len_done
    lda actedit_current_line_len
    sta actedit_cursor_col
clamp_cursor_col_to_line_len_done:
    rts

load_current_line_for_edit:
    lda actedit_current_line_lo
    sta line_number_lo
    lda actedit_current_line_hi
    sta line_number_hi
    jsr load_line_number_into_line_buffer
    lda actedit_loaded_line_kind
    sta actedit_current_line_kind
    lda actedit_loaded_insert_slot
    sta actedit_current_line_insert_slot
    lda actedit_loaded_source_line_lo
    sta actedit_current_source_line_lo
    lda actedit_loaded_source_line_hi
    sta actedit_current_source_line_hi
    ldy #$00
load_current_line_for_edit_copy:
    lda line_buffer,y
    sta actedit_current_line_buffer,y
    beq load_current_line_for_edit_done
    iny
    cpy #LINE_BUFFER_LIMIT
    bcc load_current_line_for_edit_copy
load_current_line_for_edit_done:
    sty actedit_current_line_len
    lda #$00
    sta actedit_current_line_dirty
    rts

count_staged_source_lines:
    lda #$00
    sta status_ptr
    sta status_ptr+1
    sta status_ptr_bank
    sta actedit_source_line_count_lo
    sta actedit_source_line_count_hi
count_staged_source_lines_loop:
    jsr source_read_byte_at_status_ptr
    bcs count_staged_source_lines_done
    beq count_staged_source_lines_done
    jsr append_source_line_index_entry
    bcs count_staged_source_lines_fail
    inc actedit_source_line_count_lo
    bne count_staged_source_lines_advance
    inc actedit_source_line_count_hi
    beq count_staged_source_lines_fail
count_staged_source_lines_advance:
    jsr advance_ptr_to_next_line
    jmp count_staged_source_lines_loop
count_staged_source_lines_done:
    jsr flush_source_line_index_window
    bcs count_staged_source_lines_fail
    lda #$01
    sta actedit_source_line_index_ready
    jsr mark_piece_table_dirty
    clc
    rts
count_staged_source_lines_fail:
    lda #$00
    sta actedit_source_line_index_ready
    sec
    rts

append_source_line_index_entry:
    ldy actedit_source_line_index_window_len
    lda status_ptr
    sta actedit_source_line_index_window,y
    iny
    lda status_ptr+1
    sta actedit_source_line_index_window,y
    iny
    lda status_ptr_bank
    sta actedit_source_line_index_window,y
    iny
    sty actedit_source_line_index_window_len
    cpy #ACTEDIT_LINE_INDEX_WINDOW_LIMIT
    beq flush_source_line_index_window
    clc
    rts

flush_source_line_index_window:
    lda actedit_source_line_index_window_len
    beq flush_source_line_index_window_done
    lda actedit_source_line_index_next_bank
    cmp #ACTEDIT_REU_RESERVED_BANK
    bcs flush_source_line_index_window_fail
    clc
    lda actedit_source_line_index_next_lo
    adc actedit_source_line_index_window_len
    sta word_tmp
    lda actedit_source_line_index_next_hi
    adc #$00
    sta word_tmp+1
    lda actedit_source_line_index_next_bank
    adc #$00
    sta actedit_source_line_index_end_bank
    cmp #ACTEDIT_REU_RESERVED_BANK
    bcc flush_source_line_index_window_write
    bne flush_source_line_index_window_fail
    lda word_tmp
    ora word_tmp+1
    bne flush_source_line_index_window_fail
flush_source_line_index_window_write:
    lda actedit_source_line_index_next_lo
    sta file_params+0
    lda actedit_source_line_index_next_hi
    sta file_params+1
    lda actedit_source_line_index_next_bank
    sta file_params+2
    lda #<actedit_source_line_index_window
    sta file_params+3
    lda #>actedit_source_line_index_window
    sta file_params+4
    lda actedit_source_line_index_window_len
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    bne flush_source_line_index_window_fail
    lda word_tmp
    sta actedit_source_line_index_next_lo
    lda word_tmp+1
    sta actedit_source_line_index_next_hi
    lda actedit_source_line_index_end_bank
    sta actedit_source_line_index_next_bank
    lda #$00
    sta actedit_source_line_index_window_len
flush_source_line_index_window_done:
    clc
    rts
flush_source_line_index_window_fail:
    sec
    rts

load_line_number_into_line_buffer:
    lda line_number_lo
    sta requested_line_lo
    lda line_number_hi
    sta requested_line_hi
    lda requested_line_lo
    ora requested_line_hi
    bne :+
    jmp load_line_number_scan_eof
:   
    jsr rebuild_piece_table_if_dirty
    bcc :+
    jmp load_line_number_scan_eof
:   
    jsr load_logical_line_index_entry
    bcc :+
    jmp load_line_number_scan_eof
:   ldx actedit_piece_found_index
    lda piece_window_kind,x
    cmp #PIECE_KIND_INSERT
    beq load_line_from_insert_piece
    cmp #PIECE_KIND_PATCH
    beq load_line_from_patch_piece

load_line_from_source_piece:
    lda #LINE_KIND_SOURCE
    sta actedit_loaded_line_kind
    lda #$FF
    sta actedit_loaded_insert_slot
    clc
    lda piece_window_ref_lo,x
    adc word_tmp
    sta line_number_lo
    sta actedit_loaded_source_line_lo
    lda piece_window_ref_hi,x
    adc word_tmp+1
    sta line_number_hi
    sta actedit_loaded_source_line_hi
    jsr load_original_source_line_number_into_line_buffer
    bcs load_line_number_scan_eof
    jmp load_line_number_done

load_line_from_patch_piece:
    lda #LINE_KIND_SOURCE
    sta actedit_loaded_line_kind
    lda #$FF
    sta actedit_loaded_insert_slot
    lda piece_window_ref_lo,x
    sta line_number_lo
    sta actedit_loaded_source_line_lo
    lda piece_window_ref_hi,x
    sta line_number_hi
    sta actedit_loaded_source_line_hi
    lda piece_window_aux,x
    tax
    jsr copy_patch_slot_x_to_line_buffer
    bcs load_line_number_scan_eof
    jmp load_line_number_done

load_line_from_insert_piece:
    lda #LINE_KIND_INSERT
    sta actedit_loaded_line_kind
    lda piece_window_ref_lo,x
    sta actedit_loaded_source_line_lo
    lda piece_window_ref_hi,x
    sta actedit_loaded_source_line_hi
    lda piece_window_aux,x
    sta actedit_loaded_insert_slot
    tax
    jsr copy_insert_slot_x_to_line_buffer
    bcs load_line_number_scan_eof
    jmp load_line_number_done

load_line_number_scan_eof:
    lda requested_line_lo
    sta line_number_lo
    lda requested_line_hi
    sta line_number_hi
    sec
    rts
load_line_number_done:
    lda requested_line_lo
    sta line_number_lo
    lda requested_line_hi
    sta line_number_hi
    clc
    rts

load_logical_line_index_entry:
    lda actedit_logical_line_index_ready
    bne :+
    jmp load_logical_line_index_fail
:
    lda requested_line_lo
    ora requested_line_hi
    bne :+
    jmp load_logical_line_index_fail
:
    lda requested_line_hi
    cmp actedit_logical_line_count_hi
    bcc load_logical_line_index_in_range
    beq load_logical_line_index_check_low
    jmp load_logical_line_index_fail
load_logical_line_index_check_low:
    lda requested_line_lo
    cmp actedit_logical_line_count_lo
    bcc load_logical_line_index_in_range
    beq load_logical_line_index_in_range
    jmp load_logical_line_index_fail
load_logical_line_index_in_range:
    sec
    lda requested_line_lo
    sbc #$01
    sta word_tmp
    lda requested_line_hi
    sbc #$00
    sta word_tmp+1
    lda word_tmp
    sta status_ptr
    lda word_tmp+1
    sta status_ptr+1
    lda #$00
    sta status_ptr_bank
    asl status_ptr
    rol status_ptr+1
    rol status_ptr_bank
    clc
    lda status_ptr
    adc word_tmp
    sta file_params+0
    lda status_ptr+1
    adc word_tmp+1
    sta file_params+1
    lda status_ptr_bank
    adc #ACTEDIT_LOGICAL_INDEX_REU_BASE_BANK
    bcs load_logical_line_index_fail
    cmp #ACTEDIT_LOGICAL_INDEX_REU_END_BANK
    bcs load_logical_line_index_fail
    sta file_params+2
    lda #<actedit_source_line_index_window
    sta file_params+3
    lda #>actedit_source_line_index_window
    sta file_params+4
    lda #ACTEDIT_LOGICAL_INDEX_ENTRY_BYTES
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    bne load_logical_line_index_fail
    lda actedit_source_line_index_window+0
    cmp actedit_piece_count
    bcs load_logical_line_index_fail
    sta actedit_piece_found_index
    lda actedit_source_line_index_window+1
    sta word_tmp
    lda actedit_source_line_index_window+2
    sta word_tmp+1
    clc
    rts
load_logical_line_index_fail:
    sec
    rts

rebuild_piece_table_if_dirty:
    lda actedit_piece_dirty
    bne rebuild_piece_table_rebuild
    lda actedit_piece_loaded
    bne rebuild_piece_table_ready
    jsr load_piece_table_window
    bcs rebuild_piece_table_fail
rebuild_piece_table_ready:
    lda actedit_logical_line_index_ready
    bne rebuild_piece_table_done
    jmp rebuild_logical_line_index
rebuild_piece_table_done:
    clc
    rts
rebuild_piece_table_rebuild:
    inc actedit_piece_rebuild_count
    lda #$00
    sta actedit_piece_count
    lda #$01
    sta scan_source_line_lo
    lda #$00
    sta scan_source_line_hi
rebuild_piece_table_loop:
    jsr append_insert_pieces_for_scan_source
    bcs rebuild_piece_table_fail
    jsr scan_source_line_within_source_count
    bcc rebuild_piece_table_have_source
    jsr save_piece_table_window
    bcs rebuild_piece_table_fail
    jsr rebuild_logical_line_index
    bcs rebuild_piece_table_fail
    lda #$00
    sta actedit_piece_dirty
    lda #$01
    sta actedit_piece_loaded
    clc
    rts
rebuild_piece_table_have_source:
    jsr current_scan_source_line_deleted
    bcc rebuild_piece_table_next_source
    lda scan_source_line_lo
    sta line_number_lo
    lda scan_source_line_hi
    sta line_number_hi
    jsr find_patch_slot_for_line_number
    bcc rebuild_piece_table_add_patch
    jsr append_source_piece_for_scan_source
    bcs rebuild_piece_table_fail
    jmp rebuild_piece_table_next_source
rebuild_piece_table_add_patch:
    jsr append_patch_piece_slot_x_for_scan_source
    bcs rebuild_piece_table_fail
rebuild_piece_table_next_source:
    inc scan_source_line_lo
    bne rebuild_piece_table_loop
    inc scan_source_line_hi
    jmp rebuild_piece_table_loop
rebuild_piece_table_fail:
    sec
    rts

rebuild_logical_line_index:
    lda #$00
    sta actedit_logical_line_count_lo
    sta actedit_logical_line_count_hi
    sta actedit_logical_line_index_next_lo
    sta actedit_logical_line_index_next_hi
    sta actedit_logical_line_index_window_len
    sta actedit_logical_line_index_ready
    lda #ACTEDIT_LOGICAL_INDEX_REU_BASE_BANK
    sta actedit_logical_line_index_next_bank
    lda #$00
    sta actedit_piece_found_index
rebuild_logical_line_index_piece_loop:
    ldx actedit_piece_found_index
    cpx actedit_piece_count
    bcs rebuild_logical_line_index_finish
    lda #$00
    sta scan_logical_line_lo
    sta scan_logical_line_hi
rebuild_logical_line_index_line_loop:
    ldx actedit_piece_found_index
    lda scan_logical_line_hi
    cmp piece_window_count_hi,x
    bcc rebuild_logical_line_index_append
    bne rebuild_logical_line_index_next_piece
    lda scan_logical_line_lo
    cmp piece_window_count_lo,x
    bcs rebuild_logical_line_index_next_piece
rebuild_logical_line_index_append:
    jsr append_logical_line_index_entry
    bcs rebuild_logical_line_index_fail
    inc scan_logical_line_lo
    bne rebuild_logical_line_index_line_loop
    inc scan_logical_line_hi
    jmp rebuild_logical_line_index_line_loop
rebuild_logical_line_index_next_piece:
    inc actedit_piece_found_index
    jmp rebuild_logical_line_index_piece_loop
rebuild_logical_line_index_finish:
    jsr flush_logical_line_index_window
    bcs rebuild_logical_line_index_fail
    lda #$01
    sta actedit_logical_line_index_ready
    clc
    rts
rebuild_logical_line_index_fail:
    lda #$00
    sta actedit_logical_line_index_ready
    sec
    rts

append_logical_line_index_entry:
    ldy actedit_logical_line_index_window_len
    lda actedit_piece_found_index
    sta actedit_source_line_index_window,y
    iny
    lda scan_logical_line_lo
    sta actedit_source_line_index_window,y
    iny
    lda scan_logical_line_hi
    sta actedit_source_line_index_window,y
    iny
    sty actedit_logical_line_index_window_len
    inc actedit_logical_line_count_lo
    bne append_logical_line_index_check_flush
    inc actedit_logical_line_count_hi
    beq append_logical_line_index_fail
append_logical_line_index_check_flush:
    cpy #ACTEDIT_LOGICAL_INDEX_WINDOW_LIMIT
    beq flush_logical_line_index_window
    clc
    rts
append_logical_line_index_fail:
    sec
    rts

flush_logical_line_index_window:
    lda actedit_logical_line_index_window_len
    beq flush_logical_line_index_window_done
    clc
    lda actedit_logical_line_index_next_lo
    adc actedit_logical_line_index_window_len
    sta word_tmp
    lda actedit_logical_line_index_next_hi
    adc #$00
    sta word_tmp+1
    lda actedit_logical_line_index_next_bank
    adc #$00
    sta actedit_logical_line_index_end_bank
    cmp #ACTEDIT_LOGICAL_INDEX_REU_END_BANK
    bcc flush_logical_line_index_window_write
    bne flush_logical_line_index_window_fail
    lda word_tmp
    ora word_tmp+1
    bne flush_logical_line_index_window_fail
flush_logical_line_index_window_write:
    lda actedit_logical_line_index_next_lo
    sta file_params+0
    lda actedit_logical_line_index_next_hi
    sta file_params+1
    lda actedit_logical_line_index_next_bank
    sta file_params+2
    lda #<actedit_source_line_index_window
    sta file_params+3
    lda #>actedit_source_line_index_window
    sta file_params+4
    lda actedit_logical_line_index_window_len
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    bne flush_logical_line_index_window_fail
    lda word_tmp
    sta actedit_logical_line_index_next_lo
    lda word_tmp+1
    sta actedit_logical_line_index_next_hi
    lda actedit_logical_line_index_end_bank
    sta actedit_logical_line_index_next_bank
    lda #$00
    sta actedit_logical_line_index_window_len
flush_logical_line_index_window_done:
    clc
    rts
flush_logical_line_index_window_fail:
    sec
    rts

scan_source_line_within_source_count:
    lda scan_source_line_hi
    cmp actedit_source_line_count_hi
    bcc scan_source_line_within_source_count_ok
    bne scan_source_line_within_source_count_fail
    lda scan_source_line_lo
    cmp actedit_source_line_count_lo
    bcc scan_source_line_within_source_count_ok
    beq scan_source_line_within_source_count_ok
scan_source_line_within_source_count_fail:
    sec
    rts
scan_source_line_within_source_count_ok:
    clc
    rts

append_insert_pieces_for_scan_source:
    lda #$00
    sta actedit_insert_search_order
append_insert_pieces_for_scan_source_loop:
    jsr find_next_insert_slot_for_scan_source_after_order
    bcs append_insert_pieces_for_scan_source_done
    jsr append_insert_piece_for_found_slot
    bcs append_insert_pieces_for_scan_source_fail
    lda actedit_insert_found_order
    clc
    adc #$01
    sta actedit_insert_search_order
    jmp append_insert_pieces_for_scan_source_loop
append_insert_pieces_for_scan_source_done:
    clc
    rts
append_insert_pieces_for_scan_source_fail:
    sec
    rts

reserve_piece_slot:
    ldx actedit_piece_count
    cpx #PIECE_MAX
    bcs reserve_piece_slot_fail
    inc actedit_piece_count
    clc
    rts
reserve_piece_slot_fail:
    sec
    rts

append_insert_piece_for_found_slot:
    lda actedit_insert_found_slot
    sta actedit_piece_found_index
    jsr reserve_piece_slot
    bcs append_insert_piece_for_found_slot_fail
    lda #PIECE_KIND_INSERT
    sta piece_window_kind,x
    lda scan_source_line_lo
    sta piece_window_ref_lo,x
    lda scan_source_line_hi
    sta piece_window_ref_hi,x
    lda actedit_piece_found_index
    sta piece_window_aux,x
    lda #$01
    sta piece_window_count_lo,x
    lda #$00
    sta piece_window_count_hi,x
    clc
    rts
append_insert_piece_for_found_slot_fail:
    sec
    rts

append_patch_piece_slot_x_for_scan_source:
    txa
    sta actedit_piece_found_index
    jsr reserve_piece_slot
    bcs append_patch_piece_slot_x_for_scan_source_fail
    lda #PIECE_KIND_PATCH
    sta piece_window_kind,x
    lda scan_source_line_lo
    sta piece_window_ref_lo,x
    lda scan_source_line_hi
    sta piece_window_ref_hi,x
    lda actedit_piece_found_index
    sta piece_window_aux,x
    lda #$01
    sta piece_window_count_lo,x
    lda #$00
    sta piece_window_count_hi,x
    clc
    rts
append_patch_piece_slot_x_for_scan_source_fail:
    sec
    rts

append_source_piece_for_scan_source:
    lda actedit_piece_count
    beq append_source_piece_new
    tax
    dex
    lda piece_window_kind,x
    cmp #PIECE_KIND_SOURCE
    bne append_source_piece_new
    clc
    lda piece_window_ref_lo,x
    adc piece_window_count_lo,x
    sta word_tmp
    lda piece_window_ref_hi,x
    adc piece_window_count_hi,x
    sta word_tmp+1
    lda word_tmp
    cmp scan_source_line_lo
    bne append_source_piece_new
    lda word_tmp+1
    cmp scan_source_line_hi
    bne append_source_piece_new
    inc piece_window_count_lo,x
    bne append_source_piece_done
    inc piece_window_count_hi,x
append_source_piece_done:
    clc
    rts
append_source_piece_new:
    jsr reserve_piece_slot
    bcs append_source_piece_fail
    lda #PIECE_KIND_SOURCE
    sta piece_window_kind,x
    lda scan_source_line_lo
    sta piece_window_ref_lo,x
    lda scan_source_line_hi
    sta piece_window_ref_hi,x
    lda #$00
    sta piece_window_aux,x
    lda #$01
    sta piece_window_count_lo,x
    lda #$00
    sta piece_window_count_hi,x
    clc
    rts
append_source_piece_fail:
    sec
    rts

load_original_source_line_number_into_line_buffer:
    jsr find_line_start_for_requested_line
    bcc :+
    sec
    rts
:
    jsr source_read_byte_at_status_ptr
    bcc :+
    sec
    rts
:   beq load_original_source_line_fail
    lda status_ptr
    sta line_work_ptr
    lda status_ptr+1
    sta line_work_ptr+1
    lda status_ptr_bank
    sta line_work_ptr_bank
    jsr copy_source_line_to_buffer_from_line_work_ptr
    clc
    rts
load_original_source_line_fail:
    sec
    rts

find_next_insert_slot_for_scan_source_after_order:
    jsr load_insert_meta_window
    bcc :+
    jmp find_next_insert_slot_fail
:   
    lda #$FF
    sta actedit_insert_found_slot
    sta actedit_insert_found_order
    ldx #$00
find_next_insert_slot_loop:
    cpx #INSERT_MAX
    bcs find_next_insert_slot_done
    lda insert_meta_window_active,x
    beq find_next_insert_slot_next
    lda insert_meta_window_anchor_lo,x
    cmp scan_source_line_lo
    bne find_next_insert_slot_next
    lda insert_meta_window_anchor_hi,x
    cmp scan_source_line_hi
    bne find_next_insert_slot_next
    lda insert_meta_window_order,x
    cmp actedit_insert_search_order
    bcc find_next_insert_slot_next
    cmp actedit_insert_found_order
    bcs find_next_insert_slot_next
    sta actedit_insert_found_order
    txa
    sta actedit_insert_found_slot
find_next_insert_slot_next:
    inx
    jmp find_next_insert_slot_loop
find_next_insert_slot_done:
    lda actedit_insert_found_slot
    cmp #$FF
    beq find_next_insert_slot_fail
    clc
    rts
find_next_insert_slot_fail:
    sec
    rts

current_scan_source_line_deleted:
    jsr load_delete_meta_window
    bcc :+
    jmp current_scan_source_line_not_deleted
:   
    ldx #$00
current_scan_source_line_deleted_loop:
    cpx #DELETE_MAX
    bcs current_scan_source_line_not_deleted
    lda delete_meta_window_active,x
    beq current_scan_source_line_deleted_next
    lda delete_meta_window_source_lo,x
    cmp scan_source_line_lo
    bne current_scan_source_line_deleted_next
    lda delete_meta_window_source_hi,x
    cmp scan_source_line_hi
    beq current_scan_source_line_deleted_hit
current_scan_source_line_deleted_next:
    inx
    jmp current_scan_source_line_deleted_loop
current_scan_source_line_deleted_hit:
    clc
    rts
current_scan_source_line_not_deleted:
    sec
    rts

delete_left_at_cursor:
    lda actedit_cursor_col
    bne delete_left_at_cursor_do_delete
    jmp join_with_previous_line
delete_left_at_cursor_do_delete:
    tax
    dex
delete_left_shift_loop:
    lda actedit_current_line_buffer+1,x
    sta actedit_current_line_buffer,x
    inx
    cpx actedit_current_line_len
    bcc delete_left_shift_loop
    dec actedit_cursor_col
    dec actedit_current_line_len
    lda #$00
    ldy actedit_current_line_len
    sta actedit_current_line_buffer,y
    lda #$01
    sta actedit_current_line_dirty
    sta actedit_dirty
    clc
    rts
delete_left_at_cursor_fail:
    sec
    rts

is_insertable_char:
    cmp #' '
    bcc is_insertable_char_fail
    cmp #$7F
    bcs is_insertable_char_fail
    clc
    rts
is_insertable_char_fail:
    sec
    rts

insert_char_at_cursor:
    pha
    lda actedit_current_line_len
    cmp #LINE_BUFFER_LIMIT
    bcs insert_char_at_cursor_fail
    ldx actedit_current_line_len
    cpx #$00
    beq insert_char_store
insert_char_shift_loop:
    cpx actedit_cursor_col
    bcc insert_char_store
    lda actedit_current_line_buffer,x
    sta actedit_current_line_buffer+1,x
    dex
    cpx #$FF
    bne insert_char_shift_loop
insert_char_store:
    pla
    ldy actedit_cursor_col
    sta actedit_current_line_buffer,y
    inc actedit_current_line_len
    inc actedit_cursor_col
    lda #$00
    ldy actedit_current_line_len
    sta actedit_current_line_buffer,y
    lda #$01
    sta actedit_current_line_dirty
    sta actedit_dirty
    clc
    rts
insert_char_at_cursor_fail:
    pla
    sec
    rts

set_mark_at_cursor:
    lda #$01
    sta actedit_mark_active
    lda actedit_cursor_col
    sta actedit_mark_col
    lda actedit_current_line_lo
    sta actedit_mark_line_lo
    lda actedit_current_line_hi
    sta actedit_mark_line_hi
    clc
    rts

clear_mark:
    lda #$00
    sta actedit_mark_active
    rts

prepare_selection_bounds:
    lda actedit_mark_active
    bne :+
    sec
    rts
:   lda actedit_mark_line_hi
    cmp actedit_current_line_hi
    bcc prepare_selection_mark_first
    bne prepare_selection_cursor_first
    lda actedit_mark_line_lo
    cmp actedit_current_line_lo
    bcc prepare_selection_mark_first
    bne prepare_selection_cursor_first
    lda actedit_mark_col
    cmp actedit_cursor_col
    bcc prepare_selection_mark_first
    beq prepare_selection_mark_first
prepare_selection_cursor_first:
    lda actedit_current_line_lo
    sta actedit_selection_start_line_lo
    lda actedit_current_line_hi
    sta actedit_selection_start_line_hi
    lda actedit_cursor_col
    sta actedit_selection_start_col
    lda actedit_mark_line_lo
    sta actedit_selection_end_line_lo
    lda actedit_mark_line_hi
    sta actedit_selection_end_line_hi
    lda actedit_mark_col
    sta actedit_selection_end_col
    lda actedit_cursor_col
    sta word_tmp
    lda actedit_mark_col
    sta word_tmp+1
    clc
    rts
prepare_selection_mark_first:
    lda actedit_mark_line_lo
    sta actedit_selection_start_line_lo
    lda actedit_mark_line_hi
    sta actedit_selection_start_line_hi
    lda actedit_mark_col
    sta actedit_selection_start_col
    lda actedit_current_line_lo
    sta actedit_selection_end_line_lo
    lda actedit_current_line_hi
    sta actedit_selection_end_line_hi
    lda actedit_cursor_col
    sta actedit_selection_end_col
    lda actedit_mark_col
    sta word_tmp
    lda actedit_cursor_col
    sta word_tmp+1
    clc
    rts

copy_marked_range_to_clipboard:
    jsr commit_current_line_patch_if_dirty
    bcc :+
    jmp copy_marked_range_fail
:   
    jsr prepare_selection_bounds
    bcc :+
    jmp copy_marked_range_fail
:   
    jsr clear_clipboard_buffer
    lda actedit_selection_start_line_lo
    cmp actedit_selection_end_line_lo
    bne copy_marked_range_multiline
    lda actedit_selection_start_line_hi
    cmp actedit_selection_end_line_hi
    bne copy_marked_range_multiline
    ldy #$00
    ldx actedit_selection_start_col
copy_marked_range_loop:
    cpx actedit_selection_end_col
    bcs copy_marked_range_done
    lda actedit_current_line_buffer,x
    jsr append_a_to_clipboard
    bcs copy_marked_range_fail
    inx
    jmp copy_marked_range_loop
copy_marked_range_done:
    clc
    rts
copy_marked_range_multiline:
    lda actedit_selection_start_line_lo
    sta line_number_lo
    lda actedit_selection_start_line_hi
    sta line_number_hi
copy_marked_range_multiline_loop:
    jsr load_line_number_into_line_buffer
    bcs copy_marked_range_fail
    lda #$00
    sta word_tmp
    jsr measure_line_buffer_length
    lda actedit_search_limit_col
    sta word_tmp+1
    lda line_number_lo
    cmp actedit_selection_start_line_lo
    bne :+
    lda line_number_hi
    cmp actedit_selection_start_line_hi
    bne :+
    lda actedit_selection_start_col
    sta word_tmp
:   lda line_number_lo
    cmp actedit_selection_end_line_lo
    bne :+
    lda line_number_hi
    cmp actedit_selection_end_line_hi
    bne :+
    lda actedit_selection_end_col
    sta word_tmp+1
:   jsr append_line_buffer_range_word_tmp_to_clipboard
    bcs copy_marked_range_fail
    lda line_number_lo
    cmp actedit_selection_end_line_lo
    bne copy_marked_range_append_break
    lda line_number_hi
    cmp actedit_selection_end_line_hi
    beq copy_marked_range_done
copy_marked_range_append_break:
    lda #$0D
    jsr append_a_to_clipboard
    bcs copy_marked_range_fail
    inc line_number_lo
    bne copy_marked_range_multiline_loop
    inc line_number_hi
    jmp copy_marked_range_multiline_loop
copy_marked_range_fail:
    sec
    rts

delete_selection_bounds_in_word_tmp:
    ldx word_tmp
    ldy word_tmp+1
delete_selection_shift_loop:
    lda actedit_current_line_buffer,y
    sta actedit_current_line_buffer,x
    iny
    inx
    cpy actedit_current_line_len
    bcc delete_selection_shift_loop
delete_selection_finish:
    sec
    lda actedit_current_line_len
    sbc word_tmp+1
    clc
    adc word_tmp
    sta actedit_current_line_len
    lda #$00
    sta actedit_current_line_buffer,x
    lda word_tmp
    sta actedit_cursor_col
    lda #$01
    sta actedit_current_line_dirty
    sta actedit_dirty
    lda #$00
    sta actedit_mark_active
    clc
    rts

cut_marked_range_to_clipboard:
    jsr copy_marked_range_to_clipboard
    bcc :+
    jmp cut_marked_range_fail
:   
    lda actedit_clipboard_len
    bne :+
    jmp cut_marked_range_fail
:   
    lda actedit_selection_start_line_lo
    cmp actedit_selection_end_line_lo
    bne cut_marked_range_multiline
    lda actedit_selection_start_line_hi
    cmp actedit_selection_end_line_hi
    bne cut_marked_range_multiline
    jsr delete_selection_bounds_in_word_tmp
    rts
cut_marked_range_multiline:
    lda actedit_selection_start_line_lo
    sta line_number_lo
    lda actedit_selection_start_line_hi
    sta line_number_hi
    jsr load_line_number_into_line_buffer
    bcs cut_marked_range_fail
    jsr copy_line_buffer_prefix_to_prompt_from_selection_start
    lda actedit_selection_end_line_lo
    sta line_number_lo
    lda actedit_selection_end_line_hi
    sta line_number_hi
    jsr load_line_number_into_line_buffer
    bcs cut_marked_range_fail
    jsr copy_line_buffer_suffix_to_search_from_selection_end
    lda actedit_selection_end_line_lo
    sta line_number_lo
    lda actedit_selection_end_line_hi
    sta line_number_hi
cut_marked_range_remove_loop:
    lda line_number_lo
    cmp actedit_selection_start_line_lo
    bne :+
    lda line_number_hi
    cmp actedit_selection_start_line_hi
    beq cut_marked_range_removed_extra
:   jsr remove_logical_line_number_in_line_number
    bcs cut_marked_range_fail
    lda line_number_lo
    bne :+
    dec line_number_hi
:   dec line_number_lo
    jmp cut_marked_range_remove_loop
cut_marked_range_removed_extra:
    lda actedit_selection_start_line_lo
    sta actedit_current_line_lo
    lda actedit_selection_start_line_hi
    sta actedit_current_line_hi
    jsr load_current_line_for_edit
    jsr replace_current_line_with_prefix_and_suffix
    bcs cut_marked_range_fail
    clc
    rts
cut_marked_range_fail:
    sec
    rts

delete_marked_range:
    jsr commit_current_line_patch_if_dirty
    bcc :+
    jmp delete_marked_range_fail
:   
    jsr prepare_selection_bounds
    bcc :+
    jmp delete_marked_range_fail
:   
    lda actedit_selection_start_line_lo
    cmp actedit_selection_end_line_lo
    bne delete_marked_range_multiline
    lda actedit_selection_start_line_hi
    cmp actedit_selection_end_line_hi
    bne delete_marked_range_multiline
    lda actedit_selection_start_col
    cmp actedit_selection_end_col
    beq delete_marked_range_fail
    jsr delete_selection_bounds_in_word_tmp
    rts
delete_marked_range_multiline:
    lda actedit_selection_start_line_lo
    sta line_number_lo
    lda actedit_selection_start_line_hi
    sta line_number_hi
    jsr load_line_number_into_line_buffer
    bcs delete_marked_range_fail
    jsr copy_line_buffer_prefix_to_prompt_from_selection_start
    lda actedit_selection_end_line_lo
    sta line_number_lo
    lda actedit_selection_end_line_hi
    sta line_number_hi
    jsr load_line_number_into_line_buffer
    bcs delete_marked_range_fail
    jsr copy_line_buffer_suffix_to_search_from_selection_end
    lda actedit_selection_end_line_lo
    sta line_number_lo
    lda actedit_selection_end_line_hi
    sta line_number_hi
delete_marked_range_remove_loop:
    lda line_number_lo
    cmp actedit_selection_start_line_lo
    bne :+
    lda line_number_hi
    cmp actedit_selection_start_line_hi
    beq delete_marked_range_removed_extra
:   jsr remove_logical_line_number_in_line_number
    bcs delete_marked_range_fail
    lda line_number_lo
    bne :+
    dec line_number_hi
:   dec line_number_lo
    jmp delete_marked_range_remove_loop
delete_marked_range_removed_extra:
    lda actedit_selection_start_line_lo
    sta actedit_current_line_lo
    lda actedit_selection_start_line_hi
    sta actedit_current_line_hi
    jsr load_current_line_for_edit
    jsr replace_current_line_with_prefix_and_suffix
    bcs delete_marked_range_fail
    clc
    rts
delete_marked_range_fail:
    sec
    rts

paste_clipboard_at_cursor:
    lda actedit_clipboard_len
    bne :+
    jmp paste_clipboard_fail
:   
    ldx #$00
paste_clipboard_probe_loop:
    cpx actedit_clipboard_len
    bcs paste_clipboard_single_line
    lda actedit_clipboard_buffer,x
    cmp #$0D
    beq paste_clipboard_multiline
    inx
    bne paste_clipboard_probe_loop
paste_clipboard_single_line:
    lda actedit_clipboard_len
    clc
    adc actedit_current_line_len
    cmp #LINE_BUFFER_LIMIT+1
    bcc :+
    jmp paste_clipboard_fail
:   
    ldx #$00
paste_clipboard_loop:
    cpx actedit_clipboard_len
    bcs paste_clipboard_done
    txa
    pha
    lda actedit_clipboard_buffer,x
    jsr insert_char_at_cursor
    pla
    tax
    bcc :+
    jmp paste_clipboard_fail
:   
    inx
    bne paste_clipboard_loop
paste_clipboard_done:
    jsr clear_mark
    clc
    rts
paste_clipboard_multiline:
    jsr copy_current_line_suffix_from_cursor_to_search_buffer
    lda actedit_cursor_col
    sta actedit_current_line_len
    lda #$00
    ldy actedit_current_line_len
    sta actedit_current_line_buffer,y
    lda #$01
    sta actedit_current_line_dirty
    sta actedit_dirty
    ldx #$00
    stx actedit_clipboard_index
paste_clipboard_multiline_loop:
    ldx actedit_clipboard_index
    jsr paste_next_clipboard_segment_into_current_line_from_x
    bcc :+
    jmp paste_clipboard_fail
:   
    stx actedit_clipboard_index
    txa
    cmp actedit_clipboard_len
    bcs paste_clipboard_multiline_tail
    jsr split_current_line_at_cursor
    bcc :+
    jmp paste_clipboard_fail
:   
    jmp paste_clipboard_multiline_loop
paste_clipboard_multiline_tail:
    ldx #$00
paste_clipboard_tail_loop:
    cpx actedit_search_len
    bcs paste_clipboard_done
    lda actedit_search_buffer,x
    jsr insert_char_at_cursor
    bcc :+
    jmp paste_clipboard_fail
:   
    inx
    bne paste_clipboard_tail_loop
    jmp paste_clipboard_done
paste_clipboard_fail:
    sec
    rts

clear_clipboard_buffer:
    lda #$00
    sta actedit_clipboard_len
    sta actedit_clipboard_buffer
    rts

append_a_to_clipboard:
    pha
    ldy actedit_clipboard_len
    cpy #CLIPBOARD_LIMIT
    bcs append_a_to_clipboard_fail
    pla
    sta actedit_clipboard_buffer,y
    iny
    sty actedit_clipboard_len
    lda #$00
    sta actedit_clipboard_buffer,y
    clc
    rts
append_a_to_clipboard_fail:
    pla
    sec
    rts

append_line_buffer_range_word_tmp_to_clipboard:
    ldx word_tmp
append_line_buffer_range_loop:
    cpx word_tmp+1
    bcs append_line_buffer_range_done
    lda line_buffer,x
    jsr append_a_to_clipboard
    bcs append_line_buffer_range_fail
    inx
    jmp append_line_buffer_range_loop
append_line_buffer_range_done:
    clc
    rts
append_line_buffer_range_fail:
    sec
    rts

copy_line_buffer_prefix_to_prompt_from_selection_start:
    ldy #$00
    ldx #$00
copy_line_buffer_prefix_loop:
    cpx actedit_selection_start_col
    bcs copy_line_buffer_prefix_done
    lda line_buffer,x
    sta actedit_prompt_buffer,y
    inx
    iny
    jmp copy_line_buffer_prefix_loop
copy_line_buffer_prefix_done:
    lda #$00
    sta actedit_prompt_buffer,y
    sty actedit_prompt_len
    rts

copy_line_buffer_suffix_to_search_from_selection_end:
    jsr measure_line_buffer_length
    ldy #$00
    ldx actedit_selection_end_col
copy_line_buffer_suffix_loop:
    cpx actedit_search_limit_col
    bcs copy_line_buffer_suffix_done
    lda line_buffer,x
    sta actedit_search_buffer,y
    inx
    iny
    jmp copy_line_buffer_suffix_loop
copy_line_buffer_suffix_done:
    lda #$00
    sta actedit_search_buffer,y
    sty actedit_search_len
    rts

replace_current_line_with_prefix_and_suffix:
    ldy #$00
    ldx #$00
replace_current_line_prefix_loop:
    cpx actedit_prompt_len
    bcs replace_current_line_prefix_done
    lda actedit_prompt_buffer,x
    sta actedit_current_line_buffer,y
    inx
    iny
    jmp replace_current_line_prefix_loop
replace_current_line_prefix_done:
    ldx #$00
replace_current_line_suffix_loop:
    cpx actedit_search_len
    bcs replace_current_line_suffix_done
    lda actedit_search_buffer,x
    sta actedit_current_line_buffer,y
    inx
    iny
    cpy #LINE_BUFFER_LIMIT
    bcc replace_current_line_suffix_loop
replace_current_line_suffix_done:
    tya
    sta actedit_current_line_len
    lda #$00
    sta actedit_current_line_buffer,y
    lda actedit_selection_start_col
    sta actedit_cursor_col
    lda #$01
    sta actedit_current_line_dirty
    sta actedit_dirty
    jsr clear_mark
    clc
    rts

remove_logical_line_number_in_line_number:
    jsr load_line_number_into_line_buffer
    bcs remove_logical_line_fail
    jsr prepare_direct_remove_loaded_line
    lda actedit_loaded_line_kind
    cmp #LINE_KIND_INSERT
    beq remove_logical_insert_line
    lda line_number_lo
    sta work_line_lo
    lda line_number_hi
    sta work_line_hi
    lda actedit_loaded_source_line_lo
    sta line_number_lo
    lda actedit_loaded_source_line_hi
    sta line_number_hi
    jsr add_delete_slot_for_line_number
    bcs remove_logical_line_fail
    jsr apply_direct_remove_line
    lda work_line_lo
    sta line_number_lo
    lda work_line_hi
    sta line_number_hi
    clc
    rts
remove_logical_insert_line:
    jsr load_insert_meta_window
    bcc :+
    jmp remove_logical_line_fail
:   
    ldx actedit_loaded_insert_slot
    cpx #$FF
    bcs remove_logical_line_fail
    lda #$00
    sta insert_meta_window_active,x
    jsr save_insert_meta_window
    bcc :+
    jmp remove_logical_line_fail
:   jsr apply_direct_remove_line
    clc
    rts
remove_logical_line_fail:
    sec
    rts

copy_current_line_suffix_from_cursor_to_search_buffer:
    ldy #$00
    ldx actedit_cursor_col
copy_current_line_suffix_loop:
    cpx actedit_current_line_len
    bcs copy_current_line_suffix_done
    lda actedit_current_line_buffer,x
    sta actedit_search_buffer,y
    inx
    iny
    jmp copy_current_line_suffix_loop
copy_current_line_suffix_done:
    lda #$00
    sta actedit_search_buffer,y
    sty actedit_search_len
    rts

paste_next_clipboard_segment_into_current_line_from_x:
paste_next_clipboard_segment_loop:
    cpx actedit_clipboard_len
    bcs paste_next_clipboard_segment_done
    lda actedit_clipboard_buffer,x
    cmp #$0D
    beq paste_next_clipboard_segment_break
    pha
    txa
    pha
    lda actedit_clipboard_buffer,x
    jsr insert_char_at_cursor
    pla
    tax
    pla
    bcs paste_next_clipboard_segment_fail
    inx
    jmp paste_next_clipboard_segment_loop
paste_next_clipboard_segment_break:
    inx
paste_next_clipboard_segment_done:
    clc
    rts
paste_next_clipboard_segment_fail:
    sec
    rts

create_empty_insert_line_after_current:
    lda actedit_current_line_kind
    cmp #LINE_KIND_INSERT
    beq create_insert_after_current_insert
    lda actedit_current_source_line_lo
    clc
    adc #$01
    sta line_number_lo
    lda actedit_current_source_line_hi
    adc #$00
    sta line_number_hi
    lda #$00
    sta actedit_insert_search_order
    jmp create_insert_after_current_have_anchor
create_insert_after_current_insert:
    jsr load_insert_meta_window
    bcc :+
    jmp create_insert_after_current_fail
:   
    ldx actedit_current_line_insert_slot
    cpx #$FF
    bcc :+
    jmp create_insert_after_current_fail
:   lda insert_meta_window_anchor_lo,x
    sta line_number_lo
    lda insert_meta_window_anchor_hi,x
    sta line_number_hi
    lda insert_meta_window_order,x
    clc
    adc #$01
    sta actedit_insert_search_order
create_insert_after_current_have_anchor:
    jsr shift_insert_orders_for_line_number_from_search_order
    jsr find_free_insert_slot
    bcc :+
    jmp create_insert_after_current_fail
:   lda #$01
    sta insert_meta_window_active,x
    lda line_number_lo
    sta insert_meta_window_anchor_lo,x
    lda line_number_hi
    sta insert_meta_window_anchor_hi,x
    lda actedit_insert_search_order
    sta insert_meta_window_order,x
    txa
    pha
    jsr save_insert_meta_window
    bcc :+
    pla
    jmp create_insert_after_current_fail
:   
    pla
    tax
    jsr clear_edit_text_window
    jsr save_insert_text_slot_x_from_window
    bcs create_insert_after_current_fail
    inc actedit_current_line_lo
    bne :+
    inc actedit_current_line_hi
:   jsr load_current_line_for_edit
    lda #$00
    sta actedit_cursor_col
    clc
    rts
create_insert_after_current_fail:
    sec
    rts

copy_current_line_to_prompt_buffer:
    ldy #$00
copy_current_line_to_prompt_buffer_loop:
    lda actedit_current_line_buffer,y
    sta actedit_prompt_buffer,y
    beq copy_current_line_to_prompt_buffer_done
    iny
    cpy #LINE_BUFFER_LIMIT
    bcc copy_current_line_to_prompt_buffer_loop
copy_current_line_to_prompt_buffer_done:
    sty actedit_prompt_len
    rts

split_current_line_at_cursor:
    lda actedit_current_line_kind
    cmp #LINE_KIND_INSERT
    beq split_current_insert_line
    lda actedit_current_source_line_lo
    clc
    adc #$01
    sta line_number_lo
    lda actedit_current_source_line_hi
    adc #$00
    sta line_number_hi
    lda #$00
    sta actedit_insert_search_order
    jmp split_current_have_anchor
split_current_insert_line:
    jsr load_insert_meta_window
    bcc :+
    jmp split_current_line_fail
:   
    ldx actedit_current_line_insert_slot
    cpx #$FF
    bcc :+
    jmp split_current_line_fail
:   
    lda insert_meta_window_anchor_lo,x
    sta line_number_lo
    lda insert_meta_window_anchor_hi,x
    sta line_number_hi
    lda insert_meta_window_order,x
    clc
    adc #$01
    sta actedit_insert_search_order
split_current_have_anchor:
    jsr find_free_insert_slot
    bcc :+
    jmp split_current_line_fail
:   
    txa
    sta actedit_insert_found_slot
    lda actedit_current_line_kind
    cmp #LINE_KIND_INSERT
    bne :+
    jsr prepare_direct_split_insert
:
    lda line_number_lo
    sta actedit_pending_insert_anchor_lo
    lda line_number_hi
    sta actedit_pending_insert_anchor_hi
    ldy #$00
    ldx actedit_cursor_col
split_current_copy_right_loop:
    cpx actedit_current_line_len
    bcs split_current_copy_right_done
    lda actedit_current_line_buffer,x
    sta line_buffer,y
    inx
    iny
    cpy #LINE_BUFFER_LIMIT
    bcc split_current_copy_right_loop
split_current_copy_right_done:
    lda #$00
    sta line_buffer,y
    ldy actedit_cursor_col
    sty actedit_current_line_len
    lda #$00
    sta actedit_current_line_buffer,y
    lda #$01
    sta actedit_current_line_dirty
    sta actedit_dirty
    lda #$00
    sta actedit_mark_active
    jsr commit_current_line_patch_if_dirty
    bcs split_current_line_fail
    lda actedit_current_line_kind
    cmp #LINE_KIND_INSERT
    beq :+
    jsr prepare_direct_split_insert
:
    lda actedit_pending_insert_anchor_lo
    sta line_number_lo
    lda actedit_pending_insert_anchor_hi
    sta line_number_hi
    jsr shift_insert_orders_for_line_number_from_search_order
    jsr load_insert_meta_window
    bcc :+
    jmp split_current_line_fail
:   
    lda actedit_pending_insert_anchor_lo
    sta line_number_lo
    lda actedit_pending_insert_anchor_hi
    sta line_number_hi
    ldx actedit_insert_found_slot
    lda #$01
    sta insert_meta_window_active,x
    lda line_number_lo
    sta insert_meta_window_anchor_lo,x
    lda line_number_hi
    sta insert_meta_window_anchor_hi,x
    lda actedit_insert_search_order
    sta insert_meta_window_order,x
    txa
    pha
    jsr save_insert_meta_window
    bcc :+
    pla
    jmp split_current_line_fail
:   
    pla
    tax
    jsr copy_line_buffer_to_insert_x
    bcs split_current_line_fail
    jsr apply_direct_split_insert_slot_x
    inc actedit_current_line_lo
    bne :+
    inc actedit_current_line_hi
:   jsr load_current_line_for_edit
    lda #$00
    sta actedit_cursor_col
    clc
    rts
split_current_line_fail:
    sec
    rts

join_with_previous_line:
    lda actedit_current_line_hi
    bne join_with_previous_line_have_prev
    lda actedit_current_line_lo
    cmp #$02
    bcs join_with_previous_line_have_prev
    jmp join_with_previous_line_fail
join_with_previous_line_have_prev:
    jsr prepare_direct_remove_current_line
    jsr copy_current_line_to_prompt_buffer
    lda actedit_current_line_kind
    sta actedit_saved_line_kind
    lda actedit_current_line_insert_slot
    sta actedit_saved_insert_slot
    lda actedit_current_source_line_lo
    sta actedit_saved_source_line_lo
    lda actedit_current_source_line_hi
    sta actedit_saved_source_line_hi
    lda actedit_current_line_lo
    sta line_number_lo
    lda actedit_current_line_hi
    sta line_number_hi
    lda line_number_lo
    bne :+
    dec line_number_hi
:   dec line_number_lo
    jsr load_line_number_into_line_buffer
    bcs join_with_previous_line_fail
    jsr measure_line_buffer_length
    lda actedit_search_limit_col
    clc
    adc actedit_prompt_len
    cmp #LINE_BUFFER_LIMIT+1
    bcs join_with_previous_line_fail
    lda line_number_lo
    sta actedit_current_line_lo
    lda line_number_hi
    sta actedit_current_line_hi
    jsr load_current_line_for_edit
    lda actedit_current_line_len
    sta actedit_cursor_col
    ldx #$00
join_with_previous_line_append_loop:
    cpx actedit_prompt_len
    bcs join_with_previous_line_append_done
    lda actedit_prompt_buffer,x
    jsr insert_char_at_cursor
    bcs join_with_previous_line_fail
    inx
    bne join_with_previous_line_append_loop
join_with_previous_line_append_done:
    lda actedit_saved_line_kind
    cmp #LINE_KIND_INSERT
    beq join_with_previous_line_drop_insert
    lda actedit_saved_source_line_lo
    sta line_number_lo
    lda actedit_saved_source_line_hi
    sta line_number_hi
    jsr add_delete_slot_for_line_number
    bcs join_with_previous_line_fail
    jsr apply_direct_remove_line
    clc
    rts
join_with_previous_line_drop_insert:
    jsr load_insert_meta_window
    bcc :+
    jmp join_with_previous_line_fail
:   
    ldx actedit_saved_insert_slot
    cpx #$FF
    bcs join_with_previous_line_fail
    lda #$00
    sta insert_meta_window_active,x
    jsr save_insert_meta_window
    bcc :+
    jmp join_with_previous_line_fail
:   jsr apply_direct_remove_line
    clc
    rts
join_with_previous_line_fail:
    sec
    rts

prompt_clear_buffer:
    lda #$00
    sta actedit_prompt_len
    sta actedit_prompt_buffer
    rts

draw_prompt_row:
    lda #<SCREEN_RAM
    sta base_ptr
    lda #>SCREEN_RAM
    sta base_ptr+1
    lda #HELP_ROW
    sta current_row
    lda #$00
    sta current_col
    jsr calc_prompt_row_ptr
    ldy #$00
    lda #$20
draw_prompt_row_fill_loop:
    sta (row_ptr),y
    iny
    cpy #SCREEN_COLS
    bcc draw_prompt_row_fill_loop
    lda #HELP_ROW
    sta current_row
    lda #$00
    sta current_col
    lda line_start_ptr
    ldy line_start_ptr+1
    jsr draw_const_string_at
    lda #HELP_ROW
    sta current_row
    lda current_col
    clc
    adc #$01
    sta current_col
    lda #<actedit_prompt_buffer
    ldy #>actedit_prompt_buffer
    jsr draw_const_string_at
    rts

calc_prompt_row_ptr:
    lda current_row
    ldx #$00
    jmp calc_row_ptr

prompt_backspace:
    lda actedit_prompt_len
    beq prompt_backspace_done
    dec actedit_prompt_len
    ldy actedit_prompt_len
    lda #$00
    sta actedit_prompt_buffer,y
prompt_backspace_done:
    rts

prompt_goto_line_number:
    jsr prompt_clear_buffer
    lda #<goto_prompt
    sta line_start_ptr
    lda #>goto_prompt
    sta line_start_ptr+1
    jsr draw_prompt_row
prompt_goto_loop:
    jsr read_input_key
    jsr normalize_input_key
    cmp #$00
    beq prompt_goto_loop
    cmp #KEY_RUNSTOP
    beq prompt_goto_fail
    cmp #KEY_TEST_EXIT
    beq prompt_goto_fail
    cmp #KEY_RETURN
    beq prompt_goto_done
    cmp #KEY_DELETE
    bne :+
    jsr prompt_backspace
    jsr draw_prompt_row
    jmp prompt_goto_loop
:   cmp #'0'
    bcc prompt_goto_loop
    cmp #'9'+1
    bcs prompt_goto_loop
    ldy actedit_prompt_len
    cpy #5
    bcs prompt_goto_loop
    sta actedit_prompt_buffer,y
    iny
    sty actedit_prompt_len
    lda #$00
    sta actedit_prompt_buffer,y
    jsr draw_prompt_row
    jmp prompt_goto_loop
prompt_goto_done:
    lda actedit_prompt_len
    beq prompt_goto_fail
    jsr parse_prompt_line_number
    bcs prompt_goto_fail
    clc
    rts
prompt_goto_fail:
    sec
    rts

parse_prompt_line_number:
    lda #$00
    sta line_number_lo
    sta line_number_hi
    ldx #$00
parse_prompt_line_loop:
    cpx actedit_prompt_len
    bcs parse_prompt_line_done
    lda line_number_lo
    sta status_ptr
    lda line_number_hi
    sta status_ptr+1
    asl line_number_lo
    rol line_number_hi
    lda status_ptr
    sta word_tmp
    lda status_ptr+1
    sta word_tmp+1
    asl word_tmp
    rol word_tmp+1
    asl word_tmp
    rol word_tmp+1
    asl word_tmp
    rol word_tmp+1
    clc
    lda line_number_lo
    adc word_tmp
    sta line_number_lo
    lda line_number_hi
    adc word_tmp+1
    sta line_number_hi
    lda actedit_prompt_buffer,x
    sec
    sbc #'0'
    clc
    adc line_number_lo
    sta line_number_lo
    bcc :+
    inc line_number_hi
:   inx
    jmp parse_prompt_line_loop
parse_prompt_line_done:
    lda line_number_lo
    ora line_number_hi
    beq parse_prompt_line_fail
    clc
    rts
parse_prompt_line_fail:
    sec
    rts

prompt_replace_text:
    jsr prompt_clear_buffer
    lda #<replace_prompt
    sta line_start_ptr
    lda #>replace_prompt
    sta line_start_ptr+1
    jsr draw_prompt_row
prompt_replace_loop:
    jsr read_input_key
    jsr normalize_input_key
    cmp #$00
    beq prompt_replace_loop
    cmp #KEY_RUNSTOP
    beq prompt_replace_fail
    cmp #KEY_TEST_EXIT
    beq prompt_replace_fail
    cmp #KEY_RETURN
    beq prompt_replace_done
    cmp #KEY_DELETE
    bne :+
    jsr prompt_backspace
    jsr draw_prompt_row
    jmp prompt_replace_loop
:   jsr is_insertable_char
    bcs prompt_replace_loop
    ldy actedit_prompt_len
    cpy #CLIPBOARD_LIMIT
    bcs prompt_replace_loop
    sta actedit_prompt_buffer,y
    iny
    sty actedit_prompt_len
    lda #$00
    sta actedit_prompt_buffer,y
    jsr draw_prompt_row
    jmp prompt_replace_loop
prompt_replace_done:
    clc
    rts
prompt_replace_fail:
    sec
    rts

replace_next_from_context:
    jsr commit_current_line_patch_if_dirty
    bcs replace_next_fail
    jsr build_search_text_from_context
    bcs replace_next_fail

    lda actedit_current_line_lo
    sta line_number_lo
    lda actedit_current_line_hi
    sta line_number_hi
    jsr load_line_number_into_line_buffer
    lda actedit_cursor_col
    sta actedit_search_start_col
    lda actedit_current_line_len
    sta actedit_search_limit_col
    jsr find_first_search_in_line_buffer_range
    bcc replace_next_apply_match

    lda actedit_current_line_lo
    clc
    adc #$01
    sta line_number_lo
    lda actedit_current_line_hi
    adc #$00
    sta line_number_hi
replace_next_line_loop:
    jsr source_line_exists_for_line_number
    bcs replace_next_fail
    jsr load_line_number_into_line_buffer
    lda #$00
    sta actedit_search_start_col
    jsr measure_line_buffer_length
    jsr find_first_search_in_line_buffer_range
    bcc replace_next_apply_match
    inc line_number_lo
    bne replace_next_line_loop
    inc line_number_hi
    jmp replace_next_line_loop

replace_next_apply_match:
    lda line_number_lo
    sta actedit_current_line_lo
    lda line_number_hi
    sta actedit_current_line_hi
    jsr load_current_line_for_edit
    lda actedit_search_match_col
    sta actedit_cursor_col
    jsr replace_current_search_match_with_prompt
    bcs replace_next_fail
    clc
    rts
replace_next_fail:
    sec
    rts

replace_all_from_context:
    jsr commit_current_line_patch_if_dirty
    bcc :+
    jmp replace_all_fail
:
    jsr build_search_text_from_context
    bcc :+
    jmp replace_all_fail
:
    jsr compute_visible_line_count
    bcc :+
    jmp replace_all_fail
:
    lda word_tmp
    sta actedit_replace_limit_lo
    lda word_tmp+1
    sta actedit_replace_limit_hi
    lda #$01
    sta actedit_replace_line_lo
    lda #$00
    sta actedit_replace_line_hi
    sta actedit_search_found

replace_all_line_loop:
    lda actedit_replace_limit_hi
    cmp actedit_replace_line_hi
    bcc replace_all_done
    bne replace_all_scan_line
    lda actedit_replace_limit_lo
    cmp actedit_replace_line_lo
    bcc replace_all_done
replace_all_scan_line:
    lda actedit_replace_line_lo
    sta line_number_lo
    lda actedit_replace_line_hi
    sta line_number_hi
    jsr load_line_number_into_line_buffer
    bcs replace_all_fail
    lda #$00
    sta actedit_search_start_col
    jsr measure_line_buffer_length
    jsr find_first_search_in_line_buffer_range
    bcs replace_all_next_line

    lda #$01
    sta actedit_search_found
    lda actedit_replace_line_lo
    sta actedit_current_line_lo
    lda actedit_replace_line_hi
    sta actedit_current_line_hi
    jsr load_current_line_for_edit
replace_all_match_loop:
    lda actedit_search_match_col
    sta actedit_cursor_col
    jsr replace_current_search_match_with_prompt
    bcs replace_all_fail
    jsr copy_current_line_to_search_line_buffer
    lda actedit_cursor_col
    sta actedit_search_start_col
    lda actedit_current_line_len
    sta actedit_search_limit_col
    jsr find_first_search_in_line_buffer_range
    bcc replace_all_match_loop
    jsr commit_current_line_patch_if_dirty
    bcs replace_all_fail

replace_all_next_line:
    inc actedit_replace_line_lo
    bne replace_all_line_loop
    inc actedit_replace_line_hi
    jmp replace_all_line_loop

replace_all_done:
    lda actedit_search_found
    beq replace_all_fail
    clc
    rts
replace_all_fail:
    sec
    rts

copy_current_line_to_search_line_buffer:
    ldy #$00
copy_current_line_to_search_line_buffer_loop:
    lda actedit_current_line_buffer,y
    sta line_buffer,y
    beq copy_current_line_to_search_line_buffer_done
    iny
    cpy #LINE_BUFFER_LIMIT
    bcc copy_current_line_to_search_line_buffer_loop
copy_current_line_to_search_line_buffer_done:
    rts

replace_current_search_match_with_prompt:
    lda actedit_current_line_len
    sec
    sbc actedit_search_len
    clc
    adc actedit_prompt_len
    cmp #LINE_BUFFER_LIMIT+1
    bcs replace_current_search_match_fail
    lda actedit_cursor_col
    sta word_tmp
    clc
    adc actedit_search_len
    sta word_tmp+1
    jsr delete_selection_bounds_in_word_tmp
    bcs replace_current_search_match_fail
    ldx #$00
replace_insert_prompt_loop:
    cpx actedit_prompt_len
    bcs replace_current_search_match_done
    txa
    pha
    lda actedit_prompt_buffer,x
    jsr insert_char_at_cursor
    bcc :+
    pla
    tax
    jmp replace_current_search_match_fail
:
    pla
    tax
    inx
    bne replace_insert_prompt_loop
replace_current_search_match_done:
    clc
    rts
replace_current_search_match_fail:
    sec
    rts

find_next_from_context:
    jsr commit_current_line_patch_if_dirty
    bcs find_next_from_context_fail
    jsr build_search_text_from_context
    bcs find_next_from_context_fail

    lda actedit_current_line_lo
    sta line_number_lo
    lda actedit_current_line_hi
    sta line_number_hi
    jsr load_line_number_into_line_buffer
    lda actedit_cursor_col
    clc
    adc #$01
    sta actedit_search_start_col
    lda actedit_current_line_len
    sta actedit_search_limit_col
    jsr find_first_search_in_line_buffer_range
    bcc find_next_apply_match

    lda actedit_current_line_lo
    clc
    adc #$01
    sta line_number_lo
    lda actedit_current_line_hi
    adc #$00
    sta line_number_hi
find_next_line_loop:
    jsr source_line_exists_for_line_number
    bcs find_next_from_context_fail
    jsr load_line_number_into_line_buffer
    lda #$00
    sta actedit_search_start_col
    jsr measure_line_buffer_length
    jsr find_first_search_in_line_buffer_range
    bcc find_next_apply_match
    inc line_number_lo
    bne find_next_line_loop
    inc line_number_hi
    jmp find_next_line_loop

find_next_apply_match:
    lda line_number_lo
    sta actedit_current_line_lo
    lda line_number_hi
    sta actedit_current_line_hi
    jsr load_current_line_for_edit
    lda actedit_search_match_col
    sta actedit_cursor_col
    clc
    rts
find_next_from_context_fail:
    sec
    rts

find_prev_from_context:
    jsr commit_current_line_patch_if_dirty
    bcc :+
    jmp find_prev_from_context_fail
:   
    jsr build_search_text_from_context
    bcc :+
    jmp find_prev_from_context_fail
:   

    lda actedit_current_line_lo
    sta line_number_lo
    lda actedit_current_line_hi
    sta line_number_hi
    jsr load_line_number_into_line_buffer
    lda #$00
    sta actedit_search_start_col
    lda actedit_cursor_col
    sta actedit_search_limit_col
    jsr find_last_search_in_line_buffer_range
    bcc find_prev_apply_match

    lda actedit_current_line_hi
    bne :+
    lda actedit_current_line_lo
    cmp #$02
    bcc find_prev_from_context_fail
:   lda actedit_current_line_lo
    sta line_number_lo
    lda actedit_current_line_hi
    sta line_number_hi
    lda line_number_lo
    bne :+
    dec line_number_hi
:   dec line_number_lo
find_prev_line_loop:
    lda line_number_hi
    ora line_number_lo
    beq find_prev_from_context_fail
    jsr source_line_exists_for_line_number
    bcs find_prev_step_back
    jsr load_line_number_into_line_buffer
    lda #$00
    sta actedit_search_start_col
    jsr measure_line_buffer_length
    jsr find_last_search_in_line_buffer_range
    bcc find_prev_apply_match
find_prev_step_back:
    lda line_number_hi
    bne :+
    lda line_number_lo
    cmp #$02
    bcc find_prev_from_context_fail
:   lda line_number_lo
    bne :+
    dec line_number_hi
:   dec line_number_lo
    jmp find_prev_line_loop

find_prev_apply_match:
    lda line_number_lo
    sta actedit_current_line_lo
    lda line_number_hi
    sta actedit_current_line_hi
    jsr load_current_line_for_edit
    lda actedit_search_match_col
    sta actedit_cursor_col
    clc
    rts
find_prev_from_context_fail:
    sec
    rts

build_search_text_from_context:
    lda #$00
    sta actedit_search_len
    lda actedit_mark_active
    beq build_search_from_token
    lda actedit_mark_line_lo
    cmp actedit_current_line_lo
    bne build_search_from_token
    lda actedit_mark_line_hi
    cmp actedit_current_line_hi
    bne build_search_from_token
    jsr prepare_selection_bounds
    bcs build_search_from_token
    lda word_tmp
    cmp word_tmp+1
    bcs build_search_from_token
    ldy #$00
    ldx word_tmp
build_search_selection_loop:
    cpx word_tmp+1
    bcs build_search_store_done
    lda actedit_current_line_buffer,x
    sta actedit_search_buffer,y
    inx
    iny
    cpy #CLIPBOARD_LIMIT
    bcc build_search_selection_loop
build_search_store_done:
    sty actedit_search_len
    lda #$00
    sta actedit_search_buffer,y
    lda actedit_search_len
    beq build_search_from_token
    clc
    rts

build_search_from_token:
    lda actedit_cursor_col
    sta actedit_search_match_col
    lda actedit_search_match_col
    cmp actedit_current_line_len
    bcc build_search_have_probe
    beq build_search_step_left
    jmp build_search_fail
build_search_step_left:
    lda actedit_search_match_col
    beq build_search_fail
    dec actedit_search_match_col
build_search_have_probe:
    ldy actedit_search_match_col
    lda actedit_current_line_buffer,y
    jsr is_token_char_a
    bcc build_search_scan_left
    lda actedit_search_match_col
    beq build_search_fail
    dey
    lda actedit_current_line_buffer,y
    jsr is_token_char_a
    bcc build_search_use_left
    jmp build_search_fail
build_search_use_left:
    dec actedit_search_match_col
build_search_scan_left:
    lda actedit_search_match_col
    beq build_search_copy_token
build_search_scan_left_loop:
    ldy actedit_search_match_col
    dey
    lda actedit_current_line_buffer,y
    jsr is_token_char_a
    bcs build_search_copy_token
    dec actedit_search_match_col
    lda actedit_search_match_col
    bne build_search_scan_left_loop
build_search_copy_token:
    ldy actedit_search_match_col
    ldx #$00
build_search_copy_token_loop:
    lda actedit_current_line_buffer,y
    jsr is_token_char_a
    bcs build_search_token_done
    sta actedit_search_buffer,x
    iny
    inx
    cpx #CLIPBOARD_LIMIT
    bcc build_search_copy_token_loop
build_search_token_done:
    stx actedit_search_len
    lda #$00
    sta actedit_search_buffer,x
    lda actedit_search_len
    beq build_search_fail
    clc
    rts
build_search_fail:
    sec
    rts

is_token_char_a:
    cmp #'0'
    bcc is_token_char_check_upper
    cmp #'9'+1
    bcc is_token_char_hit
is_token_char_check_upper:
    cmp #'A'
    bcc is_token_char_check_lower
    cmp #'Z'+1
    bcc is_token_char_hit
is_token_char_check_lower:
    cmp #'a'
    bcc is_token_char_check_underscore
    cmp #'z'+1
    bcc is_token_char_hit
is_token_char_check_underscore:
    cmp #'_'
    beq is_token_char_hit
    sec
    rts
is_token_char_hit:
    clc
    rts

source_line_exists_for_line_number:
    lda line_number_lo
    sta actedit_exists_line_lo
    lda line_number_hi
    sta actedit_exists_line_hi
    lda actedit_exists_line_lo
    ora actedit_exists_line_hi
    beq source_line_exists_fail
    jsr compute_visible_line_count
    bcs source_line_exists_fail
    lda word_tmp+1
    cmp actedit_exists_line_hi
    bcc source_line_exists_fail
    bne source_line_exists_ok
    lda word_tmp
    cmp actedit_exists_line_lo
    bcc source_line_exists_fail
source_line_exists_ok:
    lda actedit_exists_line_lo
    sta line_number_lo
    lda actedit_exists_line_hi
    sta line_number_hi
    clc
    rts
source_line_exists_fail:
    lda actedit_exists_line_lo
    sta line_number_lo
    lda actedit_exists_line_hi
    sta line_number_hi
    sec
    rts

compute_visible_line_count:
    jsr rebuild_piece_table_if_dirty
    bcc :+
    sec
    rts
:   lda actedit_logical_line_count_lo
    sta word_tmp
    lda actedit_logical_line_count_hi
    sta word_tmp+1
    clc
    rts

document_has_active_line_edits:
    jsr load_patch_meta_window
    bcc :+
    sec
    rts
:   ldx #$00
document_has_patch_loop:
    cpx #PATCH_MAX
    bcs document_has_no_patches
    lda patch_meta_window_active,x
    bne document_has_line_edits
    inx
    jmp document_has_patch_loop
document_has_no_patches:
    jsr load_insert_meta_window
    bcc :+
    sec
    rts
:   ldx #$00
document_has_insert_loop:
    cpx #INSERT_MAX
    bcs document_has_no_inserts
    lda insert_meta_window_active,x
    bne document_has_line_edits
    inx
    jmp document_has_insert_loop
document_has_no_inserts:
    jsr load_delete_meta_window
    bcc :+
    sec
    rts
:   ldx #$00
document_has_delete_loop:
    cpx #DELETE_MAX
    bcs document_has_no_line_edits
    lda delete_meta_window_active,x
    bne document_has_line_edits
    inx
    jmp document_has_delete_loop
document_has_no_line_edits:
    clc
    rts
document_has_line_edits:
    sec
    rts

measure_line_buffer_length:
    ldy #$00
measure_line_buffer_length_loop:
    lda line_buffer,y
    beq measure_line_buffer_length_done
    iny
    cpy #LINE_BUFFER_LIMIT
    bcc measure_line_buffer_length_loop
measure_line_buffer_length_done:
    sty actedit_search_limit_col
    rts

find_first_search_in_line_buffer_range:
    lda actedit_search_len
    beq find_first_search_fail
    lda actedit_search_start_col
    sta actedit_search_match_col
find_first_search_loop:
    lda actedit_search_match_col
    cmp actedit_search_limit_col
    bcs find_first_search_fail
    jsr line_buffer_matches_search_at_match_col
    bcc find_first_search_hit
    inc actedit_search_match_col
    jmp find_first_search_loop
find_first_search_hit:
    clc
    rts
find_first_search_fail:
    sec
    rts

find_last_search_in_line_buffer_range:
    lda actedit_search_len
    beq find_last_search_fail
    lda #$00
    sta actedit_search_found
    lda actedit_search_start_col
    sta actedit_search_match_col
find_last_search_loop:
    lda actedit_search_match_col
    cmp actedit_search_limit_col
    bcs find_last_search_done
    jsr line_buffer_matches_search_at_match_col
    bcs find_last_search_next
    lda actedit_search_match_col
    sta actedit_search_last_col
    lda #$01
    sta actedit_search_found
find_last_search_next:
    inc actedit_search_match_col
    jmp find_last_search_loop
find_last_search_done:
    lda actedit_search_found
    beq find_last_search_fail
    lda actedit_search_last_col
    sta actedit_search_match_col
    clc
    rts
find_last_search_fail:
    sec
    rts

line_buffer_matches_search_at_match_col:
    ldy actedit_search_match_col
    ldx #$00
line_buffer_match_loop:
    cpx actedit_search_len
    beq line_buffer_match_hit
    lda line_buffer,y
    beq line_buffer_match_fail
    cmp actedit_search_buffer,x
    bne line_buffer_match_fail
    iny
    inx
    jmp line_buffer_match_loop
line_buffer_match_hit:
    clc
    rts
line_buffer_match_fail:
    sec
    rts

find_line_start_for_requested_line:
    lda actedit_source_line_index_ready
    bne :+
    jmp find_line_start_fail
:
    lda line_number_lo
    ora line_number_hi
    bne :+
    jmp find_line_start_fail
:
    lda line_number_hi
    cmp actedit_source_line_count_hi
    bcc find_line_start_in_range
    beq find_line_start_check_low
    jmp find_line_start_fail
find_line_start_check_low:
    lda line_number_lo
    cmp actedit_source_line_count_lo
    bcc find_line_start_in_range
    beq find_line_start_in_range
    jmp find_line_start_fail
find_line_start_in_range:
    sec
    lda line_number_lo
    sbc #$01
    sta word_tmp
    lda line_number_hi
    sbc #$00
    sta word_tmp+1
    lda word_tmp
    sta status_ptr
    lda word_tmp+1
    sta status_ptr+1
    lda #$00
    sta status_ptr_bank
    asl status_ptr
    rol status_ptr+1
    rol status_ptr_bank
    clc
    lda status_ptr
    adc word_tmp
    sta status_ptr
    lda status_ptr+1
    adc word_tmp+1
    sta status_ptr+1
    lda status_ptr_bank
    adc #$00
    sta status_ptr_bank
    clc
    lda actedit_source_line_index_base_lo
    adc status_ptr
    sta file_params+0
    lda actedit_source_line_index_base_hi
    adc status_ptr+1
    sta file_params+1
    lda actedit_source_line_index_base_bank
    adc status_ptr_bank
    bcs find_line_start_fail
    cmp #ACTEDIT_REU_RESERVED_BANK
    bcs find_line_start_fail
    sta file_params+2
    lda #<actedit_source_line_index_window
    sta file_params+3
    lda #>actedit_source_line_index_window
    sta file_params+4
    lda #ACTEDIT_LINE_INDEX_ENTRY_BYTES
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    bne find_line_start_fail
    lda actedit_source_line_index_window+0
    sta status_ptr
    lda actedit_source_line_index_window+1
    sta status_ptr+1
    lda actedit_source_line_index_window+2
    sta status_ptr_bank
    clc
    rts
find_line_start_fail:
    sec
    rts

advance_source_line_ptr:
    lda line_work_ptr
    sta status_ptr
    lda line_work_ptr+1
    sta status_ptr+1
    lda line_work_ptr_bank
    sta status_ptr_bank
    jsr advance_ptr_to_next_line
    lda status_ptr
    sta line_work_ptr
    lda status_ptr+1
    sta line_work_ptr+1
    lda status_ptr_bank
    sta line_work_ptr_bank
    rts

advance_ptr_to_next_line:
advance_ptr_to_next_line_loop:
    jsr source_read_byte_at_status_ptr
    bcc :+
    jmp advance_ptr_to_next_line_done
:   beq advance_ptr_to_next_line_done
    cmp #$0D
    beq advance_ptr_skip_breaks
    cmp #$0A
    beq advance_ptr_skip_breaks
    jsr inc_status_ptr
    jmp advance_ptr_to_next_line_loop
advance_ptr_skip_breaks:
advance_ptr_skip_breaks_loop:
    jsr source_read_byte_at_status_ptr
    bcc :+
    rts
:   cmp #$0D
    beq advance_ptr_skip_break_char
    cmp #$0A
    beq advance_ptr_skip_break_char
    rts
advance_ptr_skip_break_char:
    jsr inc_status_ptr
    jmp advance_ptr_skip_breaks_loop
advance_ptr_to_next_line_done:
    rts

copy_source_line_to_buffer_from_line_work_ptr:
    lda line_work_ptr
    sta line_length_ptr
    lda line_work_ptr+1
    sta line_length_ptr+1
    lda line_work_ptr_bank
    sta line_length_ptr_bank
    ldx #$00
copy_source_line_loop:
    jsr source_read_byte_at_line_length_ptr
    bcc :+
    jmp copy_source_line_done
:   beq copy_source_line_done
    cmp #$0D
    beq copy_source_line_done
    cmp #$0A
    beq copy_source_line_done
    cpx #LINE_BUFFER_LIMIT
    bcs copy_source_line_skip_store
    sta line_buffer,x
    inx
copy_source_line_skip_store:
    inc line_length_ptr
    bne copy_source_line_loop
    inc line_length_ptr+1
    bne copy_source_line_loop
    inc line_length_ptr_bank
    jmp copy_source_line_loop
copy_source_line_done:
    lda #$00
    sta line_buffer,x
    rts

load_patch_meta_window:
    lda #<ACTEDIT_PATCH_META_REU_OFFSET
    sta file_params+0
    lda #>ACTEDIT_PATCH_META_REU_OFFSET
    sta file_params+1
    lda #ACTEDIT_META_REU_BASE_BANK
    sta file_params+2
    lda #<actedit_descriptor_window
    sta file_params+3
    lda #>actedit_descriptor_window
    sta file_params+4
    lda #<PATCH_TABLE_BYTES
    sta file_params+5
    lda #>PATCH_TABLE_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:   clc
    rts

save_patch_meta_window:
    lda #<ACTEDIT_PATCH_META_REU_OFFSET
    sta file_params+0
    lda #>ACTEDIT_PATCH_META_REU_OFFSET
    sta file_params+1
    lda #ACTEDIT_META_REU_BASE_BANK
    sta file_params+2
    lda #<actedit_descriptor_window
    sta file_params+3
    lda #>actedit_descriptor_window
    sta file_params+4
    lda #<PATCH_TABLE_BYTES
    sta file_params+5
    lda #>PATCH_TABLE_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:   jsr mark_piece_table_dirty
    clc
    rts

load_insert_meta_window:
    lda #<ACTEDIT_INSERT_META_REU_OFFSET
    sta file_params+0
    lda #>ACTEDIT_INSERT_META_REU_OFFSET
    sta file_params+1
    lda #ACTEDIT_META_REU_BASE_BANK
    sta file_params+2
    lda #<actedit_descriptor_window
    sta file_params+3
    lda #>actedit_descriptor_window
    sta file_params+4
    lda #<INSERT_TABLE_BYTES
    sta file_params+5
    lda #>INSERT_TABLE_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:   clc
    rts

save_insert_meta_window:
    lda #<ACTEDIT_INSERT_META_REU_OFFSET
    sta file_params+0
    lda #>ACTEDIT_INSERT_META_REU_OFFSET
    sta file_params+1
    lda #ACTEDIT_META_REU_BASE_BANK
    sta file_params+2
    lda #<actedit_descriptor_window
    sta file_params+3
    lda #>actedit_descriptor_window
    sta file_params+4
    lda #<INSERT_TABLE_BYTES
    sta file_params+5
    lda #>INSERT_TABLE_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:   jsr mark_piece_table_dirty
    clc
    rts

load_delete_meta_window:
    lda #<ACTEDIT_DELETE_META_REU_OFFSET
    sta file_params+0
    lda #>ACTEDIT_DELETE_META_REU_OFFSET
    sta file_params+1
    lda #ACTEDIT_META_REU_BASE_BANK
    sta file_params+2
    lda #<actedit_descriptor_window
    sta file_params+3
    lda #>actedit_descriptor_window
    sta file_params+4
    lda #<DELETE_TABLE_BYTES
    sta file_params+5
    lda #>DELETE_TABLE_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:   clc
    rts

save_delete_meta_window:
    lda #<ACTEDIT_DELETE_META_REU_OFFSET
    sta file_params+0
    lda #>ACTEDIT_DELETE_META_REU_OFFSET
    sta file_params+1
    lda #ACTEDIT_META_REU_BASE_BANK
    sta file_params+2
    lda #<actedit_descriptor_window
    sta file_params+3
    lda #>actedit_descriptor_window
    sta file_params+4
    lda #<DELETE_TABLE_BYTES
    sta file_params+5
    lda #>DELETE_TABLE_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:   jsr mark_piece_table_dirty
    clc
    rts

mark_piece_table_dirty:
    lda #$01
    sta actedit_piece_dirty
    lda #$00
    sta actedit_piece_loaded
    sta actedit_logical_line_index_ready
    rts

load_piece_table_window:
    lda #<ACTEDIT_PIECE_COUNT_REU_OFFSET
    sta file_params+0
    lda #>ACTEDIT_PIECE_COUNT_REU_OFFSET
    sta file_params+1
    lda #ACTEDIT_META_REU_BASE_BANK
    sta file_params+2
    lda #<actedit_piece_count
    sta file_params+3
    lda #>actedit_piece_count
    sta file_params+4
    lda #$01
    sta file_params+5
    lda #$00
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:   lda #<ACTEDIT_PIECE_WINDOW_REU_OFFSET
    sta file_params+0
    lda #>ACTEDIT_PIECE_WINDOW_REU_OFFSET
    sta file_params+1
    lda #ACTEDIT_META_REU_BASE_BANK
    sta file_params+2
    lda #<actedit_piece_window
    sta file_params+3
    lda #>actedit_piece_window
    sta file_params+4
    lda #<ACTEDIT_PIECE_WINDOW_BYTES
    sta file_params+5
    lda #>ACTEDIT_PIECE_WINDOW_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:   lda #$01
    sta actedit_piece_loaded
    clc
    rts

save_piece_table_window:
    lda #<ACTEDIT_PIECE_COUNT_REU_OFFSET
    sta file_params+0
    lda #>ACTEDIT_PIECE_COUNT_REU_OFFSET
    sta file_params+1
    lda #ACTEDIT_META_REU_BASE_BANK
    sta file_params+2
    lda #<actedit_piece_count
    sta file_params+3
    lda #>actedit_piece_count
    sta file_params+4
    lda #$01
    sta file_params+5
    lda #$00
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:   lda #<ACTEDIT_PIECE_WINDOW_REU_OFFSET
    sta file_params+0
    lda #>ACTEDIT_PIECE_WINDOW_REU_OFFSET
    sta file_params+1
    lda #ACTEDIT_META_REU_BASE_BANK
    sta file_params+2
    lda #<actedit_piece_window
    sta file_params+3
    lda #>actedit_piece_window
    sta file_params+4
    lda #<ACTEDIT_PIECE_WINDOW_BYTES
    sta file_params+5
    lda #>ACTEDIT_PIECE_WINDOW_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:   clc
    rts

set_text_reu_params_from_word_tmp:
    lda word_tmp
    sta file_params+0
    lda word_tmp+1
    sta file_params+1
    lda #ACTEDIT_TEXT_REU_BASE_BANK
    sta file_params+2
    rts

allocate_edit_text_chunk:
    lda actedit_text_next_lo
    sta word_tmp
    lda actedit_text_next_hi
    sta word_tmp+1
    clc
    lda actedit_text_next_lo
    adc #<(LINE_BUFFER_LIMIT+1)
    sta line_number_lo
    lda actedit_text_next_hi
    adc #>(LINE_BUFFER_LIMIT+1)
    sta line_number_hi
    bcs allocate_edit_text_chunk_fail
    jsr set_text_reu_params_from_word_tmp
    lda #<actedit_edit_text_window
    sta file_params+3
    lda #>actedit_edit_text_window
    sta file_params+4
    lda #<(LINE_BUFFER_LIMIT+1)
    sta file_params+5
    lda #>(LINE_BUFFER_LIMIT+1)
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    bne allocate_edit_text_chunk_fail
    lda line_number_lo
    sta actedit_text_next_lo
    lda line_number_hi
    sta actedit_text_next_hi
    clc
    rts
allocate_edit_text_chunk_fail:
    sec
    rts

load_patch_text_slot_x_to_window:
    txa
    pha
    jsr load_patch_meta_window
    bcc :+
    pla
    sec
    rts
:   pla
    tax
    lda patch_meta_window_text_lo,x
    sta word_tmp
    lda patch_meta_window_text_hi,x
    sta word_tmp+1
    jsr set_text_reu_params_from_word_tmp
    lda #<actedit_edit_text_window
    sta file_params+3
    lda #>actedit_edit_text_window
    sta file_params+4
    lda #<(LINE_BUFFER_LIMIT+1)
    sta file_params+5
    lda #>(LINE_BUFFER_LIMIT+1)
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:   clc
    rts

save_patch_text_slot_x_from_window:
    txa
    pha
    jsr load_patch_meta_window
    bcc :+
    pla
    sec
    rts
:   pla
    tax
    txa
    pha
    jsr allocate_edit_text_chunk
    bcc :+
    pla
    sec
    rts
:   pla
    tax
    lda word_tmp
    sta patch_meta_window_text_lo,x
    lda word_tmp+1
    sta patch_meta_window_text_hi,x
    txa
    pha
    jsr save_patch_meta_window
    pla
    tax
    rts

load_insert_text_slot_x_to_window:
    txa
    pha
    jsr load_insert_meta_window
    bcc :+
    pla
    sec
    rts
:   pla
    tax
    lda insert_meta_window_text_lo,x
    sta word_tmp
    lda insert_meta_window_text_hi,x
    sta word_tmp+1
    jsr set_text_reu_params_from_word_tmp
    lda #<actedit_edit_text_window
    sta file_params+3
    lda #>actedit_edit_text_window
    sta file_params+4
    lda #<(LINE_BUFFER_LIMIT+1)
    sta file_params+5
    lda #>(LINE_BUFFER_LIMIT+1)
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:   clc
    rts

save_insert_text_slot_x_from_window:
    txa
    pha
    jsr load_insert_meta_window
    bcc :+
    pla
    sec
    rts
:   pla
    tax
    txa
    pha
    jsr allocate_edit_text_chunk
    bcc :+
    pla
    sec
    rts
:   pla
    tax
    lda word_tmp
    sta insert_meta_window_text_lo,x
    lda word_tmp+1
    sta insert_meta_window_text_hi,x
    txa
    pha
    jsr save_insert_meta_window
    pla
    tax
    rts

save_current_insert_text_slot_x_from_window:
    lda actedit_piece_dirty
    bne save_current_insert_text_slot_generic
    lda actedit_piece_loaded
    beq save_current_insert_text_slot_generic
    lda actedit_logical_line_index_ready
    beq save_current_insert_text_slot_generic
    jsr save_insert_text_slot_x_from_window
    bcs save_current_insert_text_slot_fail
    lda #$00
    sta actedit_piece_dirty
    lda #$01
    sta actedit_piece_loaded
    sta actedit_logical_line_index_ready
    inc actedit_direct_insert_update_count
    clc
    rts
save_current_insert_text_slot_generic:
    jmp save_insert_text_slot_x_from_window
save_current_insert_text_slot_fail:
    sec
    rts

clear_edit_text_window:
    ldy #$00
    lda #$00
clear_edit_text_window_loop:
    sta actedit_edit_text_window,y
    iny
    cpy #(LINE_BUFFER_LIMIT+1)
    bcc clear_edit_text_window_loop
    rts

reset_add_buffer_state:
    lda #$00
    sta actedit_text_next_lo
    sta actedit_text_next_hi
    jsr mark_piece_table_dirty
    clc
    rts

clear_insert_table:
    ldx #$00
clear_insert_table_loop:
    cpx #INSERT_MAX
    bcs clear_insert_table_done
    lda #$00
    sta insert_meta_window_active,x
    sta insert_meta_window_anchor_lo,x
    sta insert_meta_window_anchor_hi,x
    sta insert_meta_window_order,x
    sta insert_meta_window_text_lo,x
    sta insert_meta_window_text_hi,x
    inx
    jmp clear_insert_table_loop
clear_insert_table_done:
    jmp save_insert_meta_window

clear_delete_table:
    ldx #$00
clear_delete_table_loop:
    cpx #DELETE_MAX
    bcs clear_delete_table_done
    lda #$00
    sta delete_meta_window_active,x
    sta delete_meta_window_source_lo,x
    sta delete_meta_window_source_hi,x
    inx
    jmp clear_delete_table_loop
clear_delete_table_done:
    jmp save_delete_meta_window

find_free_insert_slot:
    jsr load_insert_meta_window
    bcc :+
    jmp find_free_insert_slot_fail
:   
    ldx #$00
find_free_insert_slot_loop:
    cpx #INSERT_MAX
    bcs find_free_insert_slot_fail
    lda insert_meta_window_active,x
    beq find_free_insert_slot_done
    inx
    jmp find_free_insert_slot_loop
find_free_insert_slot_done:
    clc
    rts
find_free_insert_slot_fail:
    sec
    rts

copy_insert_slot_x_to_line_buffer:
    jsr load_insert_text_slot_x_to_window
    bcs copy_insert_slot_fail
    ldy #$00
copy_insert_slot_loop:
    lda actedit_edit_text_window,y
    sta line_buffer,y
    beq copy_insert_slot_done
    iny
    cpy #LINE_BUFFER_LIMIT
    bcc copy_insert_slot_loop
copy_insert_slot_done:
    lda #$00
    sta line_buffer,y
    clc
    rts
copy_insert_slot_fail:
    lda #$00
    sta line_buffer
    sec
    rts

copy_line_buffer_to_insert_x:
    ldy #$00
copy_line_buffer_to_insert_loop:
    lda line_buffer,y
    sta actedit_edit_text_window,y
    beq copy_line_buffer_to_insert_done
    iny
    cpy #LINE_BUFFER_LIMIT
    bcc copy_line_buffer_to_insert_loop
copy_line_buffer_to_insert_done:
    lda #$00
    sta actedit_edit_text_window,y
    jmp save_insert_text_slot_x_from_window

copy_current_line_buffer_to_insert_x:
    ldy #$00
copy_current_line_buffer_to_insert_loop:
    lda actedit_current_line_buffer,y
    sta actedit_edit_text_window,y
    beq copy_current_line_buffer_to_insert_done
    iny
    cpy #LINE_BUFFER_LIMIT
    bcc copy_current_line_buffer_to_insert_loop
copy_current_line_buffer_to_insert_done:
    lda #$00
    sta actedit_edit_text_window,y
    jmp save_current_insert_text_slot_x_from_window

shift_insert_orders_for_line_number_from_search_order:
    jsr load_insert_meta_window
    bcc :+
    rts
:   
    ldx #$00
shift_insert_orders_loop:
    cpx #INSERT_MAX
    bcs shift_insert_orders_done
    lda insert_meta_window_active,x
    beq shift_insert_orders_next
    lda insert_meta_window_anchor_lo,x
    cmp line_number_lo
    bne shift_insert_orders_next
    lda insert_meta_window_anchor_hi,x
    cmp line_number_hi
    bne shift_insert_orders_next
    lda insert_meta_window_order,x
    cmp actedit_insert_search_order
    bcc shift_insert_orders_next
    inc insert_meta_window_order,x
shift_insert_orders_next:
    inx
    jmp shift_insert_orders_loop
shift_insert_orders_done:
    jmp save_insert_meta_window

add_delete_slot_for_line_number:
    jsr load_delete_meta_window
    bcc :+
    jmp add_delete_slot_fail
:   
    ldx #$00
add_delete_slot_probe_loop:
    cpx #DELETE_MAX
    bcs add_delete_slot_find_free
    lda delete_meta_window_active,x
    beq add_delete_slot_probe_next
    lda delete_meta_window_source_lo,x
    cmp line_number_lo
    bne add_delete_slot_probe_next
    lda delete_meta_window_source_hi,x
    cmp line_number_hi
    beq add_delete_slot_done
add_delete_slot_probe_next:
    inx
    jmp add_delete_slot_probe_loop
add_delete_slot_find_free:
    ldx #$00
add_delete_slot_find_free_loop:
    cpx #DELETE_MAX
    bcs add_delete_slot_fail
    lda delete_meta_window_active,x
    beq add_delete_slot_store
    inx
    jmp add_delete_slot_find_free_loop
add_delete_slot_store:
    lda #$01
    sta delete_meta_window_active,x
    lda line_number_lo
    sta delete_meta_window_source_lo,x
    lda line_number_hi
    sta delete_meta_window_source_hi,x
    jsr save_delete_meta_window
    bcc :+
    jmp add_delete_slot_fail
:   
add_delete_slot_done:
    clc
    rts
add_delete_slot_fail:
    sec
    rts

clear_patch_table:
    ldx #$00
clear_patch_table_loop:
    cpx #PATCH_MAX
    bcs clear_patch_table_done
    lda #$00
    sta patch_meta_window_active,x
    sta patch_meta_window_line_lo,x
    sta patch_meta_window_line_hi,x
    sta patch_meta_window_text_lo,x
    sta patch_meta_window_text_hi,x
    inx
    jmp clear_patch_table_loop
clear_patch_table_done:
    jmp save_patch_meta_window

find_patch_slot_for_line_number:
    jsr load_patch_meta_window
    bcc :+
    jmp find_patch_slot_fail
:   
    ldx #$00
find_patch_slot_loop:
    cpx #PATCH_MAX
    bcs find_patch_slot_fail
    lda patch_meta_window_active,x
    beq find_patch_slot_next
    lda patch_meta_window_line_lo,x
    cmp line_number_lo
    bne find_patch_slot_next
    lda patch_meta_window_line_hi,x
    cmp line_number_hi
    beq find_patch_slot_hit
find_patch_slot_next:
    inx
    jmp find_patch_slot_loop
find_patch_slot_hit:
    clc
    rts
find_patch_slot_fail:
    sec
    rts

find_or_allocate_patch_slot_for_line_number:
    jsr find_patch_slot_for_line_number
    bcc find_or_allocate_patch_slot_done
    jsr load_patch_meta_window
    bcc :+
    jmp find_or_allocate_patch_slot_fail
:   
    ldx #$00
find_free_patch_slot_loop:
    cpx #PATCH_MAX
    bcs find_or_allocate_patch_slot_fail
    lda patch_meta_window_active,x
    beq find_free_patch_slot_hit
    inx
    jmp find_free_patch_slot_loop
find_free_patch_slot_hit:
    lda #$01
    sta patch_meta_window_active,x
    lda line_number_lo
    sta patch_meta_window_line_lo,x
    lda line_number_hi
    sta patch_meta_window_line_hi,x
    txa
    pha
    jsr save_patch_meta_window
    bcc :+
    pla
    jmp find_or_allocate_patch_slot_fail
:   
    pla
    tax
find_or_allocate_patch_slot_done:
    clc
    rts
find_or_allocate_patch_slot_fail:
    sec
    rts

copy_patch_slot_x_to_line_buffer:
    jsr load_patch_text_slot_x_to_window
    bcs copy_patch_slot_fail
    ldy #$00
copy_patch_slot_loop:
    lda actedit_edit_text_window,y
    sta line_buffer,y
    beq copy_patch_slot_done
    iny
    cpy #LINE_BUFFER_LIMIT
    bcc copy_patch_slot_loop
copy_patch_slot_done:
    lda #$00
    sta line_buffer,y
    clc
    rts
copy_patch_slot_fail:
    lda #$00
    sta line_buffer
    sec
    rts

copy_current_line_buffer_to_patch_x:
    ldy #$00
copy_current_line_to_patch_loop:
    lda actedit_current_line_buffer,y
    sta actedit_edit_text_window,y
    beq copy_current_line_to_patch_done
    iny
    cpy #LINE_BUFFER_LIMIT
    bcc copy_current_line_to_patch_loop
copy_current_line_to_patch_done:
    lda #$00
    sta actedit_edit_text_window,y
    jmp save_patch_text_slot_x_from_window

prepare_direct_patch_piece:
    lda #$00
    sta actedit_direct_patch_ready
    lda #ACTEDIT_OVERLAY_CMD_PREPARE_PATCH
    jsr actedit_mutation_overlay_run_command
    rts

apply_direct_patch_piece_slot_x:
    stx actedit_direct_patch_slot
    lda actedit_direct_patch_ready
    beq apply_direct_patch_piece_done
    lda #ACTEDIT_OVERLAY_CMD_APPLY_PATCH
    jsr actedit_mutation_overlay_run_command
    bcc apply_direct_patch_piece_done
    jsr mark_piece_table_dirty
    lda #$00
    sta actedit_direct_patch_ready
apply_direct_patch_piece_done:
    rts

prepare_direct_split_insert:
    lda #$00
    sta actedit_direct_insert_ready
    lda #ACTEDIT_OVERLAY_CMD_PREPARE_SPLIT_INSERT
    jsr actedit_mutation_overlay_run_command
    rts

apply_direct_split_insert_slot_x:
    stx actedit_direct_insert_slot
    lda actedit_direct_insert_ready
    beq apply_direct_split_insert_done
    lda #ACTEDIT_OVERLAY_CMD_APPLY_SPLIT_INSERT
    jsr actedit_mutation_overlay_run_command
    bcc apply_direct_split_insert_done
    jsr mark_piece_table_dirty
    lda #$00
    sta actedit_direct_insert_ready
apply_direct_split_insert_done:
    rts

prepare_direct_remove_current_line:
    lda actedit_current_line_lo
    sta requested_line_lo
    lda actedit_current_line_hi
    sta requested_line_hi
    lda actedit_current_line_kind
    sta actedit_direct_remove_line_kind
    lda actedit_current_source_line_lo
    sta actedit_direct_patch_source_lo
    lda actedit_current_source_line_hi
    sta actedit_direct_patch_source_hi
    lda actedit_current_line_insert_slot
    sta actedit_direct_insert_slot
    jmp prepare_direct_remove_line

prepare_direct_remove_loaded_line:
    lda line_number_lo
    sta requested_line_lo
    lda line_number_hi
    sta requested_line_hi
    lda actedit_loaded_line_kind
    sta actedit_direct_remove_line_kind
    lda actedit_loaded_source_line_lo
    sta actedit_direct_patch_source_lo
    lda actedit_loaded_source_line_hi
    sta actedit_direct_patch_source_hi
    lda actedit_loaded_insert_slot
    sta actedit_direct_insert_slot
prepare_direct_remove_line:
    lda #$00
    sta actedit_direct_remove_ready
    lda #ACTEDIT_OVERLAY_CMD_PREPARE_REMOVE
    jsr actedit_mutation_overlay_run_command
    rts

apply_direct_remove_line:
    lda actedit_direct_remove_ready
    beq apply_direct_remove_line_done
    lda #ACTEDIT_OVERLAY_CMD_APPLY_REMOVE
    jsr actedit_mutation_overlay_run_command
    bcc apply_direct_remove_line_done
    jsr mark_piece_table_dirty
    lda #$00
    sta actedit_direct_remove_ready
apply_direct_remove_line_done:
    rts

actedit_mutation_overlay_run_command:
    sta actedit_mutation_overlay_command
    lda actedit_mutation_overlay_state
    cmp #ACTEDIT_OVERLAY_STATE_FAILED
    beq actedit_mutation_overlay_run_fail
    cmp #ACTEDIT_OVERLAY_STATE_READY
    beq actedit_mutation_overlay_call
    jsr actedit_mutation_overlay_load
    bcs actedit_mutation_overlay_run_fail
actedit_mutation_overlay_call:
    lda C64_MEMCFG
    sta actedit_mutation_overlay_saved_memcfg
    and #C64_MEMCFG_BASIC_OFF_MASK
    sta C64_MEMCFG
    jsr ACTEDIT_OVERLAY_ENTRY
    php
    lda actedit_mutation_overlay_saved_memcfg
    sta C64_MEMCFG
    plp
    bcc actedit_mutation_overlay_run_ok
    jsr actedit_mutation_overlay_mark_failed
actedit_mutation_overlay_run_fail:
    sec
    rts
actedit_mutation_overlay_run_ok:
    clc
    rts

actedit_mutation_overlay_load:
    lda #<actedit_mutation_overlay_path
    sta file_params+0
    lda #>actedit_mutation_overlay_path
    sta file_params+1
    lda #<ACTEDIT_OVERLAY_EXEC_BASE
    sta file_params+2
    lda #>ACTEDIT_OVERLAY_EXEC_BASE
    sta file_params+3
    lda #<ACTEDIT_OVERLAY_EXEC_SIZE
    sta file_params+4
    lda #>ACTEDIT_OVERLAY_EXEC_SIZE
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    sta file_params+8
    ldx #file_params
    jsr svc_file_load_sc0
    lda file_params+6
    cmp #tool_file_status_ok
    bne actedit_mutation_overlay_load_fail
    lda file_params+8
    bne actedit_mutation_overlay_load_length_ok
    lda file_params+7
    cmp #ACTEDIT_OVERLAY_HEADER_SIZE
    bcc actedit_mutation_overlay_load_fail
actedit_mutation_overlay_load_length_ok:
    lda file_params+7
    sta actedit_mutation_overlay_loaded_len
    lda file_params+8
    sta actedit_mutation_overlay_loaded_len+1
    lda C64_MEMCFG
    sta actedit_mutation_overlay_saved_memcfg
    and #C64_MEMCFG_BASIC_OFF_MASK
    sta C64_MEMCFG
    jsr actedit_mutation_overlay_validate_visible
    php
    lda actedit_mutation_overlay_saved_memcfg
    sta C64_MEMCFG
    plp
    bcs actedit_mutation_overlay_load_fail
    lda #ACTEDIT_OVERLAY_STATE_READY
    sta actedit_mutation_overlay_state
    inc actedit_mutation_overlay_load_count
    clc
    rts
actedit_mutation_overlay_load_fail:
    jsr actedit_mutation_overlay_mark_failed
    sec
    rts

actedit_mutation_overlay_validate_visible:
    lda ACTEDIT_OVERLAY_EXEC_BASE+0
    cmp #'A'
    bne actedit_mutation_overlay_validate_fail
    lda ACTEDIT_OVERLAY_EXEC_BASE+1
    cmp #'E'
    bne actedit_mutation_overlay_validate_fail
    lda ACTEDIT_OVERLAY_EXEC_BASE+2
    cmp #'O'
    bne actedit_mutation_overlay_validate_fail
    lda ACTEDIT_OVERLAY_EXEC_BASE+3
    cmp #'V'
    bne actedit_mutation_overlay_validate_fail
    lda ACTEDIT_OVERLAY_EXEC_BASE+4
    cmp #ACTEDIT_OVERLAY_ABI_VERSION
    bne actedit_mutation_overlay_validate_fail
    lda ACTEDIT_OVERLAY_EXEC_BASE+5
    cmp #<ACTEDIT_OVERLAY_EXEC_BASE
    bne actedit_mutation_overlay_validate_fail
    lda ACTEDIT_OVERLAY_EXEC_BASE+6
    cmp #>ACTEDIT_OVERLAY_EXEC_BASE
    bne actedit_mutation_overlay_validate_fail
    lda ACTEDIT_OVERLAY_EXEC_BASE+7
    cmp #<ACTEDIT_OVERLAY_ENTRY
    bne actedit_mutation_overlay_validate_fail
    lda ACTEDIT_OVERLAY_EXEC_BASE+8
    cmp #>ACTEDIT_OVERLAY_ENTRY
    bne actedit_mutation_overlay_validate_fail
    lda ACTEDIT_OVERLAY_EXEC_BASE+9
    cmp actedit_mutation_overlay_loaded_len
    bne actedit_mutation_overlay_validate_fail
    lda ACTEDIT_OVERLAY_EXEC_BASE+10
    cmp actedit_mutation_overlay_loaded_len+1
    bne actedit_mutation_overlay_validate_fail
    lda ACTEDIT_OVERLAY_EXEC_BASE+11
    ora ACTEDIT_OVERLAY_EXEC_BASE+12
    bne actedit_mutation_overlay_validate_fail
    clc
    rts
actedit_mutation_overlay_validate_fail:
    sec
    rts

actedit_mutation_overlay_mark_failed:
    lda actedit_mutation_overlay_state
    cmp #ACTEDIT_OVERLAY_STATE_FAILED
    beq actedit_mutation_overlay_mark_failed_done
    lda #ACTEDIT_OVERLAY_STATE_FAILED
    sta actedit_mutation_overlay_state
    inc actedit_mutation_overlay_fail_count
actedit_mutation_overlay_mark_failed_done:
    rts

commit_current_line_patch_if_dirty:
    lda actedit_current_line_dirty
    beq commit_current_line_patch_done
    lda actedit_current_line_kind
    cmp #LINE_KIND_INSERT
    bne commit_current_line_patch_source
    ldx actedit_current_line_insert_slot
    cpx #$FF
    bcs commit_current_line_patch_fail
    jsr copy_current_line_buffer_to_insert_x
    bcs commit_current_line_patch_fail
    lda #$00
    sta actedit_current_line_dirty
    clc
    rts
commit_current_line_patch_source:
    jsr prepare_direct_patch_piece
    lda actedit_current_source_line_lo
    sta line_number_lo
    lda actedit_current_source_line_hi
    sta line_number_hi
    jsr find_or_allocate_patch_slot_for_line_number
    bcs commit_current_line_patch_fail
    jsr copy_current_line_buffer_to_patch_x
    bcs commit_current_line_patch_fail
    jsr apply_direct_patch_piece_slot_x
    lda #$00
    sta actedit_current_line_dirty
commit_current_line_patch_done:
    clc
    rts
commit_current_line_patch_fail:
    sec
    rts

append_output_byte:
    ldy actedit_output_chunk_len
    sta actedit_output_chunk_buffer,y
    inc actedit_output_chunk_len
    lda actedit_output_chunk_len
    cmp #OUTPUT_CHUNK_SIZE
    bcc append_output_byte_done
    jsr flush_output_stream
    bcs append_output_byte_fail
append_output_byte_done:
    clc
    rts
append_output_byte_fail:
    sec
    rts

append_line_buffer_to_output_stream:
    ldy #$00
append_line_buffer_loop:
    lda line_buffer,y
    beq append_line_buffer_done
    tax
    tya
    pha
    txa
    jsr append_output_byte
    pla
    tay
    bcs append_line_buffer_fail
    iny
    cpy #LINE_BUFFER_LIMIT
    bcc append_line_buffer_loop
append_line_buffer_done:
    clc
    rts
append_line_buffer_fail:
    sec
    rts

open_output_stream_to_target:
    lda #$00
    sta actedit_output_chunk_len
    lda #<actedit_source_path
    sta file_params+0
    lda #>actedit_source_path
    sta file_params+1
    lda #tool_file_status_fail
    sta file_params+2
    ldx #file_params
    jsr svc_file_write_begin_sc0
    lda file_params+2
    cmp #tool_file_status_ok
    beq open_output_stream_to_target_ok
    sec
    rts
open_output_stream_to_target_ok:
    clc
    rts

flush_output_stream:
    lda actedit_output_chunk_len
    beq flush_output_stream_done
    lda #<actedit_output_chunk_buffer
    sta file_params+0
    lda #>actedit_output_chunk_buffer
    sta file_params+1
    lda actedit_output_chunk_len
    sta file_params+2
    lda #$00
    sta file_params+3
    lda #tool_file_status_fail
    sta file_params+4
    ldx #file_params
    jsr svc_file_write_chunk_sc0
    lda file_params+4
    cmp #tool_file_status_ok
    bne flush_output_stream_fail
    lda #$00
    sta actedit_output_chunk_len
flush_output_stream_done:
    clc
    rts
flush_output_stream_fail:
    sec
    rts

close_output_stream:
    lda #tool_file_status_fail
    sta file_params+0
    ldx #file_params
    jsr svc_file_write_close_sc0
    lda file_params+0
    cmp #tool_file_status_ok
    beq close_output_stream_ok
    sec
    rts
close_output_stream_ok:
    clc
    rts

save_current_file:
    jsr commit_current_line_patch_if_dirty
    bcs save_current_file_fail
    jsr compute_visible_line_count
    bcs save_current_file_fail
    lda word_tmp
    sta actedit_save_limit_lo
    lda word_tmp+1
    sta actedit_save_limit_hi
    jsr open_output_stream_to_target
    bcs save_current_file_fail
    lda #$01
    sta line_number_lo
    lda #$00
    sta line_number_hi
save_current_file_loop:
    lda actedit_save_limit_hi
    cmp line_number_hi
    bcc save_current_file_finish
    bne :+
    lda actedit_save_limit_lo
    cmp line_number_lo
    bcc save_current_file_finish
:   
    jsr load_line_number_into_line_buffer
    bcs save_current_file_abort
    jsr append_line_buffer_to_output_stream
    bcs save_current_file_abort
    lda #$0D
    jsr append_output_byte
    bcs save_current_file_abort
    inc line_number_lo
    bne save_current_file_loop
    inc line_number_hi
    jmp save_current_file_loop
save_current_file_finish:
    jsr flush_output_stream
    bcs save_current_file_abort
    jsr close_output_stream
    bcs save_current_file_fail
    lda #$00
    sta actedit_dirty
    clc
    rts
save_current_file_abort:
    jsr close_output_stream
save_current_file_fail:
    sec
    rts

source_read_byte_at_status_ptr:
    lda status_ptr
    sta line_length_ptr
    lda status_ptr+1
    sta line_length_ptr+1
    lda status_ptr_bank
    sta line_length_ptr_bank
    jmp source_read_byte_at_line_length_ptr

source_read_byte_at_line_length_ptr:
    lda line_length_ptr_bank
    cmp actedit_file_window_start_bank
    bcc refill_source_file_window
    bne source_read_byte_check_window_end
    lda line_length_ptr+1
    cmp actedit_file_window_start_hi
    bcc refill_source_file_window
    bne source_read_byte_check_window_end
    lda line_length_ptr
    cmp actedit_file_window_start_lo
    bcc refill_source_file_window
source_read_byte_check_window_end:
    lda line_length_ptr_bank
    cmp actedit_file_window_end_bank
    bcc source_read_byte_from_window
    bne refill_source_file_window
    lda line_length_ptr+1
    cmp actedit_file_window_end_hi
    bcc source_read_byte_from_window
    bne refill_source_file_window
    lda line_length_ptr
    cmp actedit_file_window_end_lo
    bcc source_read_byte_from_window
refill_source_file_window:
    jsr refill_source_file_window_from_line_length_ptr
    bcc source_read_byte_from_window
    sec
    rts

source_read_byte_from_window:
    sec
    lda line_length_ptr
    sbc actedit_file_window_start_lo
    tay
    lda actedit_file_window,y
    clc
    rts

refill_source_file_window_from_line_length_ptr:
    sec
    lda actedit_source_stage_len_lo
    sbc line_length_ptr
    sta word_tmp
    lda actedit_source_stage_len_hi
    sbc line_length_ptr+1
    sta word_tmp+1
    lda actedit_source_stage_len_bank
    sbc line_length_ptr_bank
    bcc refill_source_file_window_fail
    bne refill_source_file_window_limit
    lda word_tmp+1
    bne refill_source_file_window_limit
    lda word_tmp
    beq refill_source_file_window_fail
    cmp #ACTEDIT_FILE_WINDOW_LIMIT
    bcs refill_source_file_window_limit
    bcc refill_source_file_window_remaining
refill_source_file_window_limit:
    lda #ACTEDIT_FILE_WINDOW_LIMIT
refill_source_file_window_remaining:
    sta file_params+5
    lda line_length_ptr
    sta file_params+0
    lda line_length_ptr+1
    sta file_params+1
    clc
    lda #ACTEDIT_SOURCE_REU_BASE_BANK
    adc line_length_ptr_bank
    bcs refill_source_file_window_fail
    sta file_params+2
    lda #<actedit_file_window
    sta file_params+3
    lda #>actedit_file_window
    sta file_params+4
    lda #$00
    sta file_params+6
    sta file_params+7
    txa
    pha
    ldx #file_params
    jsr svc_reu_read_sc0
    pla
    tax
    lda file_params+7
    cmp #tool_file_status_ok
    bne refill_source_file_window_fail
    lda line_length_ptr
    sta actedit_file_window_start_lo
    lda line_length_ptr+1
    sta actedit_file_window_start_hi
    lda line_length_ptr_bank
    sta actedit_file_window_start_bank
    clc
    lda line_length_ptr
    adc file_params+5
    sta actedit_file_window_end_lo
    lda line_length_ptr+1
    adc #$00
    sta actedit_file_window_end_hi
    lda line_length_ptr_bank
    adc #$00
    sta actedit_file_window_end_bank
    clc
    rts
refill_source_file_window_fail:
    sec
    rts

read_input_key:
    lda actedit_test_mode
    beq read_input_real
    lda actedit_test_key_count
    beq read_input_real
    ldy actedit_test_key_index
    lda actedit_test_keys,y
    inc actedit_test_key_index
    dec actedit_test_key_count
    rts
read_input_real:
    jsr SCNKEY
    jsr GETIN
    rts

normalize_input_key:
    cmp #'a'
    bcc normalize_input_key_petscii
    cmp #'z'+1
    bcs normalize_input_key_petscii
    and #$DF
    rts
normalize_input_key_petscii:
    cmp #$C1
    bcc normalize_input_key_done
    cmp #$DB
    bcs normalize_input_key_done
    and #$7F
normalize_input_key_done:
    rts

fill_screen_spaces:
    ldy #$00
    lda #$20
fill_page0:
    sta (base_ptr),y
    iny
    bne fill_page0
    inc base_ptr+1
    ldy #$00
fill_page1:
    sta (base_ptr),y
    iny
    bne fill_page1
    inc base_ptr+1
    ldy #$00
fill_page2:
    sta (base_ptr),y
    iny
    bne fill_page2
    inc base_ptr+1
    ldy #$00
fill_page3:
    sta (base_ptr),y
    iny
    bne fill_page3
    lda base_ptr+1
    sec
    sbc #$03
    sta base_ptr+1
    rts

calc_row_ptr:
    tay
    lda base_ptr
    clc
    adc row_offset_lo,y
    sta row_ptr
    lda base_ptr+1
    adc row_offset_hi,y
    sta row_ptr+1
    txa
    clc
    adc row_ptr
    sta row_ptr
    bcc :+
    inc row_ptr+1
:   rts

draw_const_string_at:
    sta text_ptr
    sty text_ptr+1
    lda current_row
    ldx current_col
    jsr calc_row_ptr
draw_const_string_loop:
    ldy #$00
    lda (text_ptr),y
    beq draw_const_string_done
    ldy current_col
    cpy #SCREEN_COLS
    bcs draw_const_string_done
    jsr ascii_to_screen
    ldy #$00
    sta (row_ptr),y
    inc text_ptr
    bne :+
    inc text_ptr+1
:   
    inc row_ptr
    bne :+
    inc row_ptr+1
:   inc current_col
    jmp draw_const_string_loop
draw_const_string_done:
    rts

ascii_to_screen:
    cmp #'a'
    bcc ascii_upper
    cmp #'z'+1
    bcs ascii_upper
    sec
    sbc #$60
    rts
ascii_upper:
    cmp #'A'
    bcc ascii_digit
    cmp #'Z'+1
    bcs ascii_digit
    sec
    sbc #$40
    rts
ascii_digit:
    cmp #' '
    beq ascii_space
    cmp #'0'
    bcc ascii_symbol
    cmp #'9'+1
    bcs ascii_symbol
    rts
ascii_space:
    lda #$20
    rts
ascii_symbol:
    rts

inc_status_ptr:
    inc status_ptr
    bne :+
    inc status_ptr+1
    bne :+
    inc status_ptr_bank
:   rts

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

msg_usage:
    .asciiz "ACTEDIT NAME OR PATH[:LINE]"
msg_no_source:
    .asciiz "NO SOURCE"
msg_bad_location:
    .asciiz "BAD SOURCE LINE"
actedit_mutation_overlay_path:
    .asciiz "!ACTEDIT_OVL1.BIN"
msg_no_line:
    .asciiz "NO SOURCE LINE"
title_prefix:
    .asciiz "ACTEDIT "
help_line:
    .asciiz "F1SV ^OCMP ^BBLD ^DDBG F2/4 F5/6/7"
dirty_suffix:
    .asciiz "* DIRTY"
goto_prompt:
    .asciiz "GOTO"
replace_prompt:
    .asciiz "REPL"
workflow_actc_prefix:
    .asciiz "ACTC "

row_offset_lo:
    .byte <(0*40), <(1*40), <(2*40), <(3*40), <(4*40), <(5*40), <(6*40), <(7*40), <(8*40), <(9*40)
    .byte <(10*40), <(11*40), <(12*40), <(13*40), <(14*40), <(15*40), <(16*40), <(17*40), <(18*40), <(19*40)
    .byte <(20*40), <(21*40), <(22*40), <(23*40), <(24*40)
row_offset_hi:
    .byte >(0*40), >(1*40), >(2*40), >(3*40), >(4*40), >(5*40), >(6*40), >(7*40), >(8*40), >(9*40)
    .byte >(10*40), >(11*40), >(12*40), >(13*40), >(14*40), >(15*40), >(16*40), >(17*40), >(18*40), >(19*40)
    .byte >(20*40), >(21*40), >(22*40), >(23*40), >(24*40)

patch_meta_window_active = actedit_descriptor_window+0
patch_meta_window_line_lo = actedit_descriptor_window+PATCH_MAX
patch_meta_window_line_hi = actedit_descriptor_window+(PATCH_MAX*2)
patch_meta_window_text_lo = actedit_descriptor_window+(PATCH_MAX*3)
patch_meta_window_text_hi = actedit_descriptor_window+(PATCH_MAX*4)
insert_meta_window_active = actedit_descriptor_window+0
insert_meta_window_anchor_lo = actedit_descriptor_window+INSERT_MAX
insert_meta_window_anchor_hi = actedit_descriptor_window+(INSERT_MAX*2)
insert_meta_window_order = actedit_descriptor_window+(INSERT_MAX*3)
insert_meta_window_text_lo = actedit_descriptor_window+(INSERT_MAX*4)
insert_meta_window_text_hi = actedit_descriptor_window+(INSERT_MAX*5)
delete_meta_window_active = actedit_descriptor_window+0
delete_meta_window_source_lo = actedit_descriptor_window+DELETE_MAX
delete_meta_window_source_hi = actedit_descriptor_window+(DELETE_MAX*2)
piece_window_kind = actedit_piece_window+0
piece_window_ref_lo = actedit_piece_window+PIECE_MAX
piece_window_ref_hi = actedit_piece_window+(PIECE_MAX*2)
piece_window_aux = actedit_piece_window+(PIECE_MAX*3)
piece_window_count_lo = actedit_piece_window+(PIECE_MAX*4)
piece_window_count_hi = actedit_piece_window+(PIECE_MAX*5)

arg_buffer:
    .res PATH_LIMIT+1
actedit_source_path:
    .res PATH_LIMIT+1
actedit_module_name:
    .res 25
line_buffer:
    .res LINE_BUFFER_LIMIT+1
actedit_current_line_buffer:
    .res LINE_BUFFER_LIMIT+1
actedit_source_stage_len_lo:
    .res 1
actedit_source_stage_len_hi:
    .res 1
actedit_source_stage_len_bank:
    .res 1
actedit_source_line_count_lo:
    .res 1
actedit_source_line_count_hi:
    .res 1
actedit_source_line_index_base_lo:
    .res 1
actedit_source_line_index_base_hi:
    .res 1
actedit_source_line_index_base_bank:
    .res 1
actedit_source_line_index_next_lo:
    .res 1
actedit_source_line_index_next_hi:
    .res 1
actedit_source_line_index_next_bank:
    .res 1
actedit_source_line_index_end_bank:
    .res 1
actedit_source_line_index_window_len:
    .res 1
actedit_source_line_index_ready:
    .res 1
actedit_logical_line_count_lo:
    .res 1
actedit_logical_line_count_hi:
    .res 1
actedit_logical_line_index_next_lo:
    .res 1
actedit_logical_line_index_next_hi:
    .res 1
actedit_logical_line_index_next_bank:
    .res 1
actedit_logical_line_index_end_bank:
    .res 1
actedit_logical_line_index_window_len:
    .res 1
actedit_logical_line_index_ready:
    .res 1
actedit_piece_count:
    .res 1
actedit_piece_loaded:
    .res 1
actedit_piece_dirty:
    .res 1
actedit_piece_found_index:
    .res 1
actedit_piece_rebuild_count:
    .res 1
actedit_direct_patch_count:
    .res 1
actedit_direct_insert_count:
    .res 1
actedit_direct_remove_count:
    .res 1
actedit_direct_insert_update_count:
    .res 1
actedit_logical_index_suffix_count:
    .res 1
actedit_mutation_overlay_state:
    .res 1
actedit_mutation_overlay_load_count:
    .res 1
actedit_mutation_overlay_fail_count:
    .res 1
actedit_mutation_overlay_command:
    .res 1
actedit_mutation_overlay_loaded_len:
    .res 2
actedit_mutation_overlay_saved_memcfg:
    .res 1
actedit_direct_patch_ready:
    .res 1
actedit_direct_insert_ready:
    .res 1
actedit_direct_remove_ready:
    .res 1
actedit_direct_remove_line_kind:
    .res 1
actedit_direct_insert_piece_index:
    .res 1
actedit_direct_insert_slot:
    .res 1
actedit_direct_patch_kind:
    .res 1
actedit_direct_patch_piece_index:
    .res 1
actedit_direct_patch_ref_lo:
    .res 1
actedit_direct_patch_ref_hi:
    .res 1
actedit_direct_patch_piece_count_lo:
    .res 1
actedit_direct_patch_piece_count_hi:
    .res 1
actedit_direct_patch_offset_lo:
    .res 1
actedit_direct_patch_offset_hi:
    .res 1
actedit_direct_patch_source_lo:
    .res 1
actedit_direct_patch_source_hi:
    .res 1
actedit_direct_patch_after_lo:
    .res 1
actedit_direct_patch_after_hi:
    .res 1
actedit_direct_patch_extra:
    .res 1
actedit_direct_patch_slot:
    .res 1
actedit_direct_patch_shift_index:
    .res 1
actedit_text_next_lo:
    .res 1
actedit_text_next_hi:
    .res 1
word_tmp:
    .res 2
actedit_arg_len:
    .res 1
actedit_location_separator:
    .res 1
actedit_start_line_valid:
    .res 1
actedit_start_line_lo:
    .res 1
actedit_start_line_hi:
    .res 1
line_number_lo:
    .res 1
line_number_hi:
    .res 1
work_line_lo:
    .res 1
work_line_hi:
    .res 1
requested_line_lo:
    .res 1
requested_line_hi:
    .res 1
actedit_exists_line_lo:
    .res 1
actedit_exists_line_hi:
    .res 1
scan_source_line_lo:
    .res 1
scan_source_line_hi:
    .res 1
scan_logical_line_lo:
    .res 1
scan_logical_line_hi:
    .res 1
current_row:
    .res 1
current_col:
    .res 1
actedit_file_window_start_lo:
    .res 1
actedit_file_window_start_hi:
    .res 1
actedit_file_window_start_bank:
    .res 1
actedit_file_window_end_lo:
    .res 1
actedit_file_window_end_hi:
    .res 1
actedit_file_window_end_bank:
    .res 1
actedit_current_line_lo:
    .res 1
actedit_current_line_hi:
    .res 1
actedit_top_line_lo:
    .res 1
actedit_top_line_hi:
    .res 1
actedit_left_col:
    .res 1
actedit_cursor_col:
    .res 1
actedit_current_line_len:
    .res 1
actedit_current_line_dirty:
    .res 1
actedit_dirty:
    .res 1
actedit_current_line_kind:
    .res 1
actedit_current_line_insert_slot:
    .res 1
actedit_current_source_line_lo:
    .res 1
actedit_current_source_line_hi:
    .res 1
actedit_loaded_line_kind:
    .res 1
actedit_loaded_insert_slot:
    .res 1
actedit_loaded_source_line_lo:
    .res 1
actedit_loaded_source_line_hi:
    .res 1
actedit_save_limit_lo:
    .res 1
actedit_save_limit_hi:
    .res 1
actedit_pending_insert_anchor_lo:
    .res 1
actedit_pending_insert_anchor_hi:
    .res 1
actedit_saved_line_kind:
    .res 1
actedit_saved_insert_slot:
    .res 1
actedit_saved_source_line_lo:
    .res 1
actedit_saved_source_line_hi:
    .res 1
actedit_mark_active:
    .res 1
actedit_mark_col:
    .res 1
actedit_mark_line_lo:
    .res 1
actedit_mark_line_hi:
    .res 1
actedit_selection_start_line_lo:
    .res 1
actedit_selection_start_line_hi:
    .res 1
actedit_selection_start_col:
    .res 1
actedit_selection_end_line_lo:
    .res 1
actedit_selection_end_line_hi:
    .res 1
actedit_selection_end_col:
    .res 1
actedit_clipboard_len:
    .res 1
actedit_search_len:
    .res 1
actedit_search_start_col:
    .res 1
actedit_search_limit_col:
    .res 1
actedit_search_match_col:
    .res 1
actedit_search_last_col:
    .res 1
actedit_search_found:
    .res 1
actedit_replace_line_lo:
    .res 1
actedit_replace_line_hi:
    .res 1
actedit_replace_limit_lo:
    .res 1
actedit_replace_limit_hi:
    .res 1
actedit_output_chunk_len:
    .res 1
actedit_prompt_len:
    .res 1
actedit_clipboard_index:
    .res 1
actedit_descriptor_window:
    .res ACTEDIT_DESCRIPTOR_WINDOW_BYTES
actedit_undo_count:
    .res 1
actedit_undo_head_slot:
    .res 1
actedit_undo_slot:
    .res 1
actedit_redo_count:
    .res 1
actedit_redo_head_slot:
    .res 1
actedit_redo_slot:
    .res 1
actedit_journal_kind:
    .res 1
actedit_workflow_mode:
    .res 1
actedit_insert_search_order:
    .res 1
actedit_insert_found_order:
    .res 1
actedit_insert_found_slot:
    .res 1
actedit_test_mode:
    .res 1
actedit_test_key_count:
    .res 1
actedit_test_key_index:
    .res 1
actedit_test_keys:
    .res TEST_KEY_LIMIT
actedit_test_key0 = actedit_test_keys+0
actedit_test_key1 = actedit_test_keys+1
actedit_test_key2 = actedit_test_keys+2
actedit_test_key3 = actedit_test_keys+3
actedit_test_key4 = actedit_test_keys+4
actedit_test_key5 = actedit_test_keys+5
actedit_test_key6 = actedit_test_keys+6
actedit_test_key7 = actedit_test_keys+7
actedit_test_key8 = actedit_test_keys+8
actedit_test_key9 = actedit_test_keys+9
actedit_test_key10 = actedit_test_keys+10
actedit_test_key11 = actedit_test_keys+11
actedit_test_key12 = actedit_test_keys+12
actedit_test_key13 = actedit_test_keys+13
actedit_test_key14 = actedit_test_keys+14
actedit_test_key15 = actedit_test_keys+15
actedit_test_key16 = actedit_test_keys+16
actedit_test_key17 = actedit_test_keys+17
actedit_test_key18 = actedit_test_keys+18
actedit_test_key19 = actedit_test_keys+19
actedit_test_key20 = actedit_test_keys+20
actedit_test_key21 = actedit_test_keys+21
actedit_test_key22 = actedit_test_keys+22
actedit_test_key23 = actedit_test_keys+23
actedit_file_window:
    .res ACTEDIT_FILE_WINDOW_LIMIT
actedit_source_line_index_window:
    .res ACTEDIT_LINE_INDEX_WINDOW_LIMIT
actedit_output_chunk_buffer:
    .res OUTPUT_CHUNK_SIZE
actedit_undo_state_buffer:
    .res UNDO_STATE_SIZE
actedit_clipboard_buffer:
    .res CLIPBOARD_LIMIT+1
actedit_search_buffer:
    .res CLIPBOARD_LIMIT+1
actedit_prompt_buffer:
    .res CLIPBOARD_LIMIT+1
actedit_edit_text_window:
    .res LINE_BUFFER_LIMIT+1
actedit_piece_window:
    .res ACTEDIT_PIECE_WINDOW_BYTES
