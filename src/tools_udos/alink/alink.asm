.include "udos_services.inc"

.export start

READST = $FFB7
CLOSE_K = $FFC3
CLRCHN = $FFCC
CHRIN = $FFCF
CHROUT = $FFD2
VICE_LFN_FILE = 2
TOOL_ABI_FILE_NAME_LO = $CDC6
TOOL_ABI_FILE_NAME_HI = $CDC7

MANIFEST_LIMIT = 191
.ifndef SOURCE_LIMIT
SOURCE_LIMIT = 255
.endif
.ifndef SOURCE_LOOKAHEAD
SOURCE_LOOKAHEAD = 0
.endif
SOURCE_READ_LIMIT = SOURCE_LIMIT + SOURCE_LOOKAHEAD
.ifndef BODY_OPS_STRIDE
BODY_OPS_STRIDE = 48
.endif
.ifndef INT_LITERAL_MAX
INT_LITERAL_MAX = 10
.endif
.ifndef STRING_LITERAL_MAX
STRING_LITERAL_MAX = 8
.endif
.ifndef VAR_MAX
VAR_MAX = 16
.endif
.ifndef EXPORT_MAX
EXPORT_MAX = 8
.endif
.ifndef EXTERNAL_MAX
EXTERNAL_MAX = 8
.endif
.ifndef RELOC_MAX
RELOC_MAX = 128
.endif
.ifndef ALINK_EXTERNAL_REU_BASE_LO
ALINK_EXTERNAL_REU_BASE_LO = $00
.endif
.ifndef ALINK_EXTERNAL_REU_BASE_HI
ALINK_EXTERNAL_REU_BASE_HI = $04
.endif
.ifndef ALINK_EXTERNAL_REU_BASE_BANK
ALINK_EXTERNAL_REU_BASE_BANK = $03
.endif
.ifndef ALINK_BODY_REU_BASE_LO
ALINK_BODY_REU_BASE_LO = $00
.endif
.ifndef ALINK_BODY_REU_BASE_HI
ALINK_BODY_REU_BASE_HI = $10
.endif
.ifndef ALINK_BODY_REU_BASE_BANK
ALINK_BODY_REU_BASE_BANK = $04
.endif
.ifndef ALINK_EXPORT_REU_BASE_LO
ALINK_EXPORT_REU_BASE_LO = $00
.endif
.ifndef ALINK_EXPORT_REU_BASE_HI
ALINK_EXPORT_REU_BASE_HI = $20
.endif
.ifndef ALINK_EXPORT_REU_BASE_BANK
ALINK_EXPORT_REU_BASE_BANK = $03
.endif
.ifndef ALINK_VAR_REU_BASE_LO
ALINK_VAR_REU_BASE_LO = $00
.endif
.ifndef ALINK_VAR_REU_BASE_HI
ALINK_VAR_REU_BASE_HI = $24
.endif
.ifndef ALINK_VAR_REU_BASE_BANK
ALINK_VAR_REU_BASE_BANK = $03
.endif
.ifndef ALINK_STRING_REU_BASE_LO
ALINK_STRING_REU_BASE_LO = $00
.endif
.ifndef ALINK_STRING_REU_BASE_HI
ALINK_STRING_REU_BASE_HI = $28
.endif
.ifndef ALINK_STRING_REU_BASE_BANK
ALINK_STRING_REU_BASE_BANK = $03
.endif
.ifndef ALINK_SAVED_STRING_REU_BASE_LO
ALINK_SAVED_STRING_REU_BASE_LO = $00
.endif
.ifndef ALINK_SAVED_STRING_REU_BASE_HI
ALINK_SAVED_STRING_REU_BASE_HI = $2C
.endif
.ifndef ALINK_SAVED_STRING_REU_BASE_BANK
ALINK_SAVED_STRING_REU_BASE_BANK = $03
.endif
.ifndef ALINK_PENDING_META_REU_BASE_LO
ALINK_PENDING_META_REU_BASE_LO = $00
.endif
.ifndef ALINK_PENDING_META_REU_BASE_HI
ALINK_PENDING_META_REU_BASE_HI = $30
.endif
.ifndef ALINK_PENDING_META_REU_BASE_BANK
ALINK_PENDING_META_REU_BASE_BANK = $03
.endif
.ifndef ALINK_INT_REU_BASE_LO
ALINK_INT_REU_BASE_LO = $00
.endif
.ifndef ALINK_INT_REU_BASE_HI
ALINK_INT_REU_BASE_HI = $34
.endif
.ifndef ALINK_INT_REU_BASE_BANK
ALINK_INT_REU_BASE_BANK = $03
.endif
.ifndef ALINK_VAR_META_REU_BASE_LO
ALINK_VAR_META_REU_BASE_LO = $00
.endif
.ifndef ALINK_VAR_META_REU_BASE_HI
ALINK_VAR_META_REU_BASE_HI = $38
.endif
.ifndef ALINK_VAR_META_REU_BASE_BANK
ALINK_VAR_META_REU_BASE_BANK = $03
.endif
.ifndef ALINK_EXPORT_META_REU_BASE_LO
ALINK_EXPORT_META_REU_BASE_LO = $00
.endif
.ifndef ALINK_EXPORT_META_REU_BASE_HI
ALINK_EXPORT_META_REU_BASE_HI = $3C
.endif
.ifndef ALINK_EXPORT_META_REU_BASE_BANK
ALINK_EXPORT_META_REU_BASE_BANK = $03
.endif
.ifndef ALINK_ROOT_EXPORT_LAYOUT_REU_BASE_LO
ALINK_ROOT_EXPORT_LAYOUT_REU_BASE_LO = $00
.endif
.ifndef ALINK_ROOT_EXPORT_LAYOUT_REU_BASE_HI
ALINK_ROOT_EXPORT_LAYOUT_REU_BASE_HI = $3D
.endif
.ifndef ALINK_ROOT_EXPORT_LAYOUT_REU_BASE_BANK
ALINK_ROOT_EXPORT_LAYOUT_REU_BASE_BANK = $03
.endif
.ifndef ALINK_CURRENT_EXPORT_LAYOUT_REU_BASE_LO
ALINK_CURRENT_EXPORT_LAYOUT_REU_BASE_LO = $00
.endif
.ifndef ALINK_CURRENT_EXPORT_LAYOUT_REU_BASE_HI
ALINK_CURRENT_EXPORT_LAYOUT_REU_BASE_HI = $3E
.endif
.ifndef ALINK_CURRENT_EXPORT_LAYOUT_REU_BASE_BANK
ALINK_CURRENT_EXPORT_LAYOUT_REU_BASE_BANK = $03
.endif
.ifndef ALINK_ROOT_VAR_LAYOUT_REU_BASE_LO
ALINK_ROOT_VAR_LAYOUT_REU_BASE_LO = $00
.endif
.ifndef ALINK_ROOT_VAR_LAYOUT_REU_BASE_HI
ALINK_ROOT_VAR_LAYOUT_REU_BASE_HI = $3F
.endif
.ifndef ALINK_ROOT_VAR_LAYOUT_REU_BASE_BANK
ALINK_ROOT_VAR_LAYOUT_REU_BASE_BANK = $03
.endif
.ifndef ALINK_CURRENT_VAR_LAYOUT_REU_BASE_LO
ALINK_CURRENT_VAR_LAYOUT_REU_BASE_LO = $00
.endif
.ifndef ALINK_CURRENT_VAR_LAYOUT_REU_BASE_HI
ALINK_CURRENT_VAR_LAYOUT_REU_BASE_HI = $40
.endif
.ifndef ALINK_CURRENT_VAR_LAYOUT_REU_BASE_BANK
ALINK_CURRENT_VAR_LAYOUT_REU_BASE_BANK = $03
.endif
.ifndef ALINK_ROOT_STRING_LAYOUT_REU_BASE_LO
ALINK_ROOT_STRING_LAYOUT_REU_BASE_LO = $00
.endif
.ifndef ALINK_ROOT_STRING_LAYOUT_REU_BASE_HI
ALINK_ROOT_STRING_LAYOUT_REU_BASE_HI = $41
.endif
.ifndef ALINK_ROOT_STRING_LAYOUT_REU_BASE_BANK
ALINK_ROOT_STRING_LAYOUT_REU_BASE_BANK = $03
.endif
.ifndef ALINK_LIVE_REU_BASE_LO
ALINK_LIVE_REU_BASE_LO = $00
.endif
.ifndef ALINK_LIVE_REU_BASE_HI
ALINK_LIVE_REU_BASE_HI = $42
.endif
.ifndef ALINK_LIVE_REU_BASE_BANK
ALINK_LIVE_REU_BASE_BANK = $03
.endif
.ifndef ALINK_LOOP_LAYOUT_REU_BASE_LO
ALINK_LOOP_LAYOUT_REU_BASE_LO = $00
.endif
.ifndef ALINK_LOOP_LAYOUT_REU_BASE_HI
ALINK_LOOP_LAYOUT_REU_BASE_HI = $43
.endif
.ifndef ALINK_LOOP_LAYOUT_REU_BASE_BANK
ALINK_LOOP_LAYOUT_REU_BASE_BANK = $03
.endif
.ifndef ALINK_RELOC_REU_BASE_LO
ALINK_RELOC_REU_BASE_LO = $00
.endif
.ifndef ALINK_RELOC_REU_BASE_HI
ALINK_RELOC_REU_BASE_HI = $44
.endif
.ifndef ALINK_RELOC_REU_BASE_BANK
ALINK_RELOC_REU_BASE_BANK = $03
.endif
.ifndef ALINK_ROOT_EXPORT_REU_BASE_LO
ALINK_ROOT_EXPORT_REU_BASE_LO = $00
.endif
.ifndef ALINK_ROOT_EXPORT_REU_BASE_HI
ALINK_ROOT_EXPORT_REU_BASE_HI = $47
.endif
.ifndef ALINK_ROOT_EXPORT_REU_BASE_BANK
ALINK_ROOT_EXPORT_REU_BASE_BANK = $03
.endif
.ifndef ALINK_FILE_LOAD_REU_BASE_LO
ALINK_FILE_LOAD_REU_BASE_LO = $00
.endif
.ifndef ALINK_FILE_LOAD_REU_BASE_HI
ALINK_FILE_LOAD_REU_BASE_HI = $00
.endif
.ifndef ALINK_FILE_LOAD_REU_BASE_BANK
ALINK_FILE_LOAD_REU_BASE_BANK = $02
.endif
.ifndef ALINK_DEBUG_REU_BASE_LO
ALINK_DEBUG_REU_BASE_LO = $00
.endif
.ifndef ALINK_DEBUG_REU_BASE_HI
ALINK_DEBUG_REU_BASE_HI = $00
.endif
.ifndef ALINK_DEBUG_REU_BASE_BANK
ALINK_DEBUG_REU_BASE_BANK = $01
.endif
.ifndef LOOP_MAX
LOOP_MAX = 8
.endif
.ifndef OUTPUT_CHUNK_SIZE
OUTPUT_CHUNK_SIZE = 128
.endif
.if OUTPUT_CHUNK_SIZE < 1
.error "OUTPUT_CHUNK_SIZE must be at least 1"
.endif
.if OUTPUT_CHUNK_SIZE > 255
.error "OUTPUT_CHUNK_SIZE > 255 not supported"
.endif
.if STRING_LITERAL_MAX > 36
.error "STRING_LITERAL_MAX > 36 not supported"
.endif
.if INT_LITERAL_MAX > 36
.error "INT_LITERAL_MAX > 36 not supported"
.endif
STRING_LITERAL_BYTES = 24 * STRING_LITERAL_MAX
STRING_LITERAL_ENTRY_BYTES = 24
STRING_MASK_BYTES = (STRING_LITERAL_MAX + 7) / 8
EXPORT_NAME_BYTES = 25
EXTERNAL_NAME_BYTES = 25
INT_VALUE_BYTES = 2
PENDING_NAME_BYTES = 25
VAR_NAME_BYTES = 25
PENDING_META_OFFSET_LO = 0
PENDING_META_OFFSET_HI = 1
PENDING_META_VAR_BASE_LO = 2
PENDING_META_VAR_BASE_HI = 3
PENDING_META_STRING_BASE_LO = 4
PENDING_META_STRING_BASE_HI = 5
PENDING_META_STRING_MASK = 6
PENDING_META_BYTES = PENDING_META_STRING_MASK + STRING_MASK_BYTES
VAR_META_INIT_LO = 0
VAR_META_INIT_HI = 1
VAR_META_WIDTH = 2
VAR_META_BYTES = 3
EXPORT_META_OFFSET_LO = 0
EXPORT_META_OFFSET_HI = 1
EXPORT_META_SIZE_LO = 2
EXPORT_META_SIZE_HI = 3
EXPORT_META_BYTES = 4
EXPORT_LAYOUT_LO = 0
EXPORT_LAYOUT_HI = 1
EXPORT_LAYOUT_BYTES = 2
EXTERNAL_NAME_REU_BYTES = $1C00
PENDING_META_REU_BYTES = $0400
.assert EXPORT_MAX > 0, error, "EXPORT_MAX must be positive"
.assert EXPORT_MAX < $100, error, "EXPORT_MAX must fit in export_count"
.assert EXPORT_MAX * EXPORT_NAME_BYTES <= $400, error, "export names exceed their REU window"
.assert EXPORT_MAX * EXPORT_META_BYTES <= $100, error, "export metadata exceeds its REU page"
.assert EXPORT_MAX * EXPORT_LAYOUT_BYTES <= $100, error, "export layout exceeds its REU page"
.assert (ALINK_BODY_REU_BASE_LO + (ALINK_BODY_REU_BASE_HI << 8)) + (EXPORT_MAX * BODY_OPS_STRIDE) <= $10000, error, "export bodies exceed their REU bank"
.assert EXTERNAL_MAX > 0, error, "EXTERNAL_MAX must be positive"
.assert EXTERNAL_MAX < $100, error, "EXTERNAL_MAX must fit in external_count"
.assert EXTERNAL_MAX * EXTERNAL_NAME_BYTES <= EXTERNAL_NAME_REU_BYTES, error, "external names exceed their REU window"
.assert EXTERNAL_MAX * PENDING_META_BYTES <= PENDING_META_REU_BYTES, error, "external placement metadata exceeds its REU window"
VAR_LAYOUT_LO = 0
VAR_LAYOUT_HI = 1
VAR_LAYOUT_BYTES = 2
STRING_LAYOUT_LO = 0
STRING_LAYOUT_HI = 1
STRING_LAYOUT_BYTES = 2
LIVE_FLAG_BYTES = 1
LOOP_LAYOUT_LO = 0
LOOP_LAYOUT_HI = 1
LOOP_LAYOUT_BYTES = 2
RELOC_RECORD_OFFSET_LO = 0
RELOC_RECORD_OFFSET_HI = 1
RELOC_RECORD_ADDR_LO = 2
RELOC_RECORD_ADDR_HI = 3
RELOC_RECORD_KIND = 4
RELOC_RECORD_BYTES = 5
RELOC_KIND_WORD = 0
RELOC_KIND_LOW = 1
RELOC_KIND_HIGH = 2
RELOC_REU_BYTES = $300
.assert RELOC_MAX > 0, error, "RELOC_MAX must be positive"
.assert RELOC_MAX < $100, error, "RELOC_MAX must fit in linked_reloc_count"
.assert RELOC_MAX * RELOC_RECORD_BYTES <= RELOC_REU_BYTES, error, "relocation records exceed their REU region"
.assert (ALINK_RELOC_REU_BASE_LO + (ALINK_RELOC_REU_BASE_HI << 8)) + RELOC_REU_BYTES <= (ALINK_ROOT_EXPORT_REU_BASE_LO + (ALINK_ROOT_EXPORT_REU_BASE_HI << 8)), error, "relocation region overlaps root exports"
PRG_BUILD_DIRECT = 0
PRG_BUILD_OBJECT_CODE = 15
ALINK_CHAIN_NONE = $00
ALINK_CHAIN_DEBUG = $01


.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
file_params:
    .res 9
scan_ptr:
    .res 2
src_ptr:
    .res 2
const_ptr = svc_retptr
content_ptr = const_ptr
export_count = truncated_flag
export_index = export_index_zp
export_ptr = svc_retptr
body_ptr = src_ptr

.code

start:
    jsr init_module_name
    jsr detect_alink_chain_mode
    jsr build_manifest_entry
    jsr require_loaded_project
    jsr require_manifest_entry_tracked
    jsr build_object_target_path
    lda #$10
    sta debug_phase_zp
    jsr load_object_or_fail
    lda #$11
    sta debug_phase_zp
    jsr parse_exports_or_fail
    lda #$12
    sta debug_phase_zp
    jsr parse_body_ops_or_fail
    lda #$13
    sta debug_phase_zp
    jsr parse_external_symbols_or_fail
    lda #$14
    sta debug_phase_zp
    jsr prune_direct_object_code_external_symbols
    lda #$15
    sta debug_phase_zp
    jsr parse_strings_or_fail
    lda #$16
    sta debug_phase_zp
    jsr parse_ints_or_fail
    lda #$17
    sta debug_phase_zp
    jsr parse_vars_or_fail
    lda #$18
    sta debug_phase_zp
    jsr resolve_external_objects_or_fail
    lda #$19
    sta debug_phase_zp
    jsr compute_code_bytes
    lda #$1A
    sta debug_phase_zp
    jsr build_live_set
    lda #$1B
    sta debug_phase_zp
    jsr select_prg_build_strategy_or_fail
    lda #$1C
    sta debug_phase_zp
    jsr validate_prg_build_inputs_or_fail
    lda #$41
    sta debug_phase_zp
    jsr build_binary_save_target_path
    jsr copy_target_path_to_binary_target_path
    jsr open_output_stream_to_target_or_fail
    jsr build_prg_content_or_fail
    lda #$42
    sta debug_phase_zp
    jsr save_source_buffer_to_target
    lda #$43
    sta debug_phase_zp
    bcc save_prg_ok
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr

save_prg_ok:
    lda #$44
    sta debug_phase_zp
    jsr emit_debug_sidecar_or_fail
    bcc save_ok
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr

save_ok:
    jsr queue_alink_successor
    bcc :+
    lda #<msg_chain_fail
    ldy #>msg_chain_fail
    jmp fail_with_ptr
:
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

init_module_name:
    ldx #svc_retptr
    jsr alink_svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    beq init_module_name_default
    ldx #svc_retptr
    jsr alink_svc_program_get_cmdline_ptr
    lda svc_retptr
    sta src_ptr
    lda svc_retptr+1
    sta src_ptr+1
    jsr skip_cmdline_spaces
    jsr copy_module_arg
    bcc init_module_name_done
    lda #<msg_bad_name
    ldy #>msg_bad_name
    jmp fail_with_ptr

init_module_name_default:
    ldy #$00
init_module_name_default_loop:
    lda default_module_name,y
    sta module_name,y
    beq init_module_name_done
    iny
    bne init_module_name_default_loop
init_module_name_done:
    rts

detect_alink_chain_mode:
    lda #ALINK_CHAIN_NONE
    sta alink_chain_mode
    ldx #svc_retptr
    jsr alink_svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    beq detect_alink_chain_mode_done
    ldx #svc_retptr
    jsr alink_svc_program_get_cmdline_ptr
    lda svc_retptr
    sta src_ptr
    lda svc_retptr+1
    sta src_ptr+1
    ldy #$00
detect_alink_chain_mode_scan:
    lda (src_ptr),y
    beq detect_alink_chain_mode_done
    cmp #':'
    beq detect_alink_chain_mode_debug
    iny
    bne detect_alink_chain_mode_scan
detect_alink_chain_mode_debug:
    lda #ALINK_CHAIN_DEBUG
    sta alink_chain_mode
detect_alink_chain_mode_done:
    rts

queue_alink_successor:
    lda alink_chain_mode
    beq queue_alink_successor_done
    ldy #$00
queue_alink_successor_prefix:
    lda actdbg_command_prefix,y
    beq queue_alink_successor_module_begin
    sta target_path,y
    iny
    bne queue_alink_successor_prefix
queue_alink_successor_module_begin:
    ldx #$00
queue_alink_successor_module:
    lda module_name,x
    beq queue_alink_successor_terminate
    sta target_path,y
    iny
    inx
    bne queue_alink_successor_module
queue_alink_successor_terminate:
    lda #$00
    sta target_path,y
    lda #<target_path
    sta svc_retptr
    lda #>target_path
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_chain_sc0
queue_alink_successor_done:
    clc
    rts

skip_cmdline_spaces:
    ldy #$00
skip_cmdline_spaces_loop:
    lda (src_ptr),y
    cmp #' '
    bne skip_cmdline_spaces_done
    inc src_ptr
    bne :+
    inc src_ptr+1
:   jmp skip_cmdline_spaces_loop
skip_cmdline_spaces_done:
    rts

load_object_or_fail:
    jsr load_source_file
    bcc load_object_loaded
    lda file_params+6
    cmp #tool_file_status_nofile
    beq load_object_missing
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_object_missing:
    lda #<msg_no_object
    ldy #>msg_no_object
    jmp fail_with_ptr
load_object_loaded:
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    rts

load_pending_object_or_library_or_fail:
    jsr load_source_file
    bcc load_pending_object_or_library_loaded
    lda file_params+6
    cmp #tool_file_status_nofile
    beq load_pending_object_or_library_try_lib
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_pending_object_or_library_try_lib:
    jsr build_library_object_target_path
    jsr load_source_file
    bcc load_pending_object_or_library_loaded
    lda file_params+6
    cmp #tool_file_status_nofile
    beq load_pending_object_or_library_missing
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_pending_object_or_library_missing:
    lda #<msg_no_object
    ldy #>msg_no_object
    jmp fail_with_ptr
load_pending_object_or_library_loaded:
    rts

resolve_external_objects_or_fail:
    lda export_count
    sta saved_export_count
    jsr save_current_module_name
    lda #$00
    sta pending_active_index
resolve_external_objects_loop:
    ldx pending_active_index
    cpx external_count
    beq resolve_external_objects_done
    jsr copy_external_name_to_module_name_from_x_or_fail
    jsr build_object_target_path
    jsr load_pending_object_or_library_or_fail
    jsr require_loaded_source_not_truncated_or_fail
    jsr require_supported_object_header_or_fail
    jsr require_loaded_object_exports_module_or_fail
    lda saved_export_count
    sta export_count
    jsr append_loaded_object_imports_to_queue_or_fail
    lda saved_export_count
    sta export_count
    inc pending_active_index
    jmp resolve_external_objects_loop
resolve_external_objects_done:
    jsr restore_saved_module_name
    lda saved_export_count
    sta export_count
    rts

copy_external_name_to_module_name_from_x_or_fail:
    jsr set_external_ptr_from_x
    ldy #$00
copy_external_name_to_module_name_loop:
    lda (export_ptr),y
    sta module_name,y
    beq copy_external_name_to_module_name_done
    iny
    cpy #25
    bcc copy_external_name_to_module_name_loop
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
copy_external_name_to_module_name_done:
    rts

save_current_module_name:
    ldy #$00
save_current_module_name_loop:
    lda module_name,y
    sta saved_module_name,y
    beq save_current_module_name_done
    iny
    cpy #25
    bcc save_current_module_name_loop
save_current_module_name_done:
    rts

restore_saved_module_name:
    ldy #$00
restore_saved_module_name_loop:
    lda saved_module_name,y
    sta module_name,y
    beq restore_saved_module_name_done
    iny
    cpy #25
    bcc restore_saved_module_name_loop
restore_saved_module_name_done:
    rts

require_loaded_object_exports_module_or_fail:
    jsr reset_scan_ptr_after_header
require_loaded_object_exports_module_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq require_loaded_object_exports_module_bad
    lda #<line_export
    sta const_ptr
    lda #>line_export
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs require_loaded_object_exports_module_next
    jsr advance_scan_ptr_by_const_ptr
    jsr scan_symbol_matches_module_name
    bcc require_loaded_object_exports_module_done
require_loaded_object_exports_module_next:
    jsr skip_current_line
    jmp require_loaded_object_exports_module_loop
require_loaded_object_exports_module_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
require_loaded_object_exports_module_done:
    rts

append_loaded_object_imports_to_queue_or_fail:
    jsr find_loaded_export_index_from_module_name_or_fail
    jsr load_loaded_export_meta_at_scan_ptr_or_fail
    jsr set_body_ptr_to_loaded_body_index_or_fail
    jsr loaded_body_ptr_is_object_code
    bcc append_loaded_object_imports_live
    jmp append_all_loaded_object_imports_to_queue_or_fail
append_loaded_object_imports_live:
    jsr append_imports_from_body_ptr_to_queue_or_fail
    jmp append_named_relocs_current_export_to_queue_or_fail

loaded_body_ptr_is_object_code:
    lda body_ptr
    sta scan_ptr
    lda body_ptr+1
    sta scan_ptr+1
    jmp object_code_body_at_scan_ptr_is_supported

find_loaded_export_index_from_module_name_or_fail:
    lda #$00
    sta linked_object_index
    jsr reset_scan_ptr_after_header
find_loaded_export_index_from_module_name_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq find_loaded_export_index_from_module_name_bad
    lda #<line_export
    sta const_ptr
    lda #>line_export
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs find_loaded_export_index_from_module_name_next
    jsr advance_scan_ptr_by_const_ptr
    jsr scan_symbol_matches_module_name
    bcc find_loaded_export_index_from_module_name_done
    inc linked_object_index
    beq find_loaded_export_index_from_module_name_bad
find_loaded_export_index_from_module_name_next:
    jsr skip_current_line
    jmp find_loaded_export_index_from_module_name_loop
find_loaded_export_index_from_module_name_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
find_loaded_export_index_from_module_name_done:
    rts

load_loaded_export_meta_at_scan_ptr_or_fail:
    jsr skip_symbol_at_scan_ptr_or_fail
    jsr require_space_or_fail
    jsr parse_decimal_word_or_fail
    lda current_bit_lo
    sta export_meta_window+EXPORT_META_OFFSET_LO
    lda current_bit_hi
    sta export_meta_window+EXPORT_META_OFFSET_HI
    jsr require_space_or_fail
    jsr parse_decimal_word_or_fail
    lda current_bit_lo
    sta export_meta_window+EXPORT_META_SIZE_LO
    lda current_bit_hi
    sta export_meta_window+EXPORT_META_SIZE_HI
    rts

skip_symbol_at_scan_ptr_or_fail:
    lda #$00
    sta linked_external_index
skip_symbol_at_scan_ptr_loop:
    ldy #$00
    lda (scan_ptr),y
    beq skip_symbol_at_scan_ptr_done
    cmp #' '
    beq skip_symbol_at_scan_ptr_done
    cmp #10
    beq skip_symbol_at_scan_ptr_done
    cmp #13
    beq skip_symbol_at_scan_ptr_done
    jsr advance_scan_ptr
    inc linked_external_index
    bne skip_symbol_at_scan_ptr_loop
skip_symbol_at_scan_ptr_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
skip_symbol_at_scan_ptr_done:
    lda linked_external_index
    beq skip_symbol_at_scan_ptr_bad
    rts

set_body_ptr_to_loaded_body_index_or_fail:
    lda #$00
    sta current_bit_lo
    jsr reset_scan_ptr_after_header
set_body_ptr_to_loaded_body_index_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq set_body_ptr_to_loaded_body_index_bad
    lda #<line_external
    sta const_ptr
    lda #>line_external
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcc set_body_ptr_to_loaded_body_index_next
    lda #<line_body
    sta const_ptr
    lda #>line_body
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs set_body_ptr_to_loaded_body_index_next
    jsr advance_scan_ptr_by_const_ptr
    lda current_bit_lo
    cmp linked_object_index
    beq set_body_ptr_to_loaded_body_index_found
    inc current_bit_lo
    beq set_body_ptr_to_loaded_body_index_bad
set_body_ptr_to_loaded_body_index_next:
    jsr skip_current_line
    jmp set_body_ptr_to_loaded_body_index_loop
set_body_ptr_to_loaded_body_index_found:
    lda scan_ptr
    sta body_ptr
    lda scan_ptr+1
    sta body_ptr+1
    rts
set_body_ptr_to_loaded_body_index_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr

append_imports_from_body_ptr_to_queue_or_fail:
    ldy #$00
append_imports_from_body_ptr_loop:
    lda (body_ptr),y
    beq append_imports_from_body_ptr_done
    cmp #10
    beq append_imports_from_body_ptr_done
    cmp #13
    beq append_imports_from_body_ptr_done
    cmp #'u'
    beq append_imports_from_body_ptr_import
    iny
    bne append_imports_from_body_ptr_loop
    jmp append_imports_from_body_ptr_bad
append_imports_from_body_ptr_import:
    iny
    lda (body_ptr),y
    jsr object_code_import_index_from_a
    bcs append_imports_from_body_ptr_bad
    sta linked_import_index
    iny
    tya
    pha
    lda body_ptr
    pha
    lda body_ptr+1
    pha
    lda linked_import_index
    jsr copy_loaded_import_index_to_pending_window_or_fail
    jsr append_pending_name_to_external_queue_or_fail
    pla
    sta body_ptr+1
    pla
    sta body_ptr
    pla
    tay
    jmp append_imports_from_body_ptr_loop
append_imports_from_body_ptr_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
append_imports_from_body_ptr_done:
    rts

append_all_loaded_object_imports_to_queue_or_fail:
    jsr reset_scan_ptr_after_header
append_all_loaded_object_imports_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq append_all_loaded_object_imports_done
    lda #<line_external
    sta const_ptr
    lda #>line_external
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs append_all_loaded_object_imports_next
    jsr advance_scan_ptr_by_const_ptr
    jsr copy_import_symbol_line_to_pending_window_or_fail
    jsr append_pending_name_to_external_queue_or_fail
append_all_loaded_object_imports_next:
    jsr skip_current_line
    jmp append_all_loaded_object_imports_loop
append_all_loaded_object_imports_done:
    rts

prune_direct_object_code_external_symbols:
    jsr find_export_index_from_module_name
    bcc prune_direct_object_code_external_symbols_have_entry
    rts
prune_direct_object_code_external_symbols_have_entry:
    stx entry_export_index
    jsr direct_entry_body_is_object_code
    bcc prune_direct_object_code_external_symbols_prune
    rts
prune_direct_object_code_external_symbols_prune:
    lda #$00
    sta external_count
    ldx entry_export_index
    jsr load_export_meta_window_from_x_or_fail
    ldx entry_export_index
    jsr set_body_ptr_from_x
    jsr append_imports_from_body_ptr_to_queue_or_fail
    ldx entry_export_index
    jsr load_export_meta_window_from_x_or_fail
    jmp append_named_relocs_current_export_to_queue_or_fail

copy_import_symbol_line_to_pending_window_or_fail:
    lda #<pending_name_window
    sta export_ptr
    lda #>pending_name_window
    sta export_ptr+1
    ldy #$00
copy_import_symbol_line_to_pending_window_loop:
    lda (scan_ptr),y
    beq copy_import_symbol_line_to_pending_window_done
    cmp #' '
    beq copy_import_symbol_line_to_pending_window_done
    cmp #10
    beq copy_import_symbol_line_to_pending_window_done
    cmp #13
    beq copy_import_symbol_line_to_pending_window_done
    jsr lowercase_ascii
    cmp #'a'
    bcc copy_import_symbol_line_to_pending_window_symbol
    cmp #'z'+1
    bcc copy_import_symbol_line_to_pending_window_store
copy_import_symbol_line_to_pending_window_symbol:
    cmp #'0'
    bcc copy_import_symbol_line_to_pending_window_check_underscore
    cmp #'9'+1
    bcc copy_import_symbol_line_to_pending_window_store
copy_import_symbol_line_to_pending_window_check_underscore:
    cmp #'_'
    bne copy_import_symbol_line_to_pending_window_bad
copy_import_symbol_line_to_pending_window_store:
    sta (export_ptr),y
    iny
    cpy #24
    bcc copy_import_symbol_line_to_pending_window_loop
copy_import_symbol_line_to_pending_window_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
copy_import_symbol_line_to_pending_window_done:
    cpy #$00
    beq copy_import_symbol_line_to_pending_window_bad
    lda #$00
    sta (export_ptr),y
    rts

append_pending_name_to_external_queue_or_fail:
    jsr pending_name_already_external
    bcc append_pending_name_to_external_queue_done
    jsr pending_name_already_exported
    bcc append_pending_name_to_external_queue_done
    lda external_count
    cmp #EXTERNAL_MAX
    bcc :+
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
:   jsr copy_pending_name_to_external_window
    ldx external_count
    jsr store_external_name_window_from_x_or_fail
    inc external_count
append_pending_name_to_external_queue_done:
    rts

pending_name_already_external:
    lda #$00
    sta saved_pending_index
pending_name_already_external_loop:
    ldx saved_pending_index
    cpx external_count
    beq pending_name_already_external_not_found
    jsr load_external_name_window_from_x_or_fail
    jsr pending_name_matches_external_window
    bcc pending_name_already_external_found
    inc saved_pending_index
    jmp pending_name_already_external_loop
pending_name_already_external_found:
    clc
    rts
pending_name_already_external_not_found:
    sec
    rts

pending_name_already_exported:
    lda #$00
    sta saved_pending_index
pending_name_already_exported_loop:
    ldx saved_pending_index
    cpx export_count
    beq pending_name_already_exported_not_found
    jsr load_export_name_window_from_x_or_fail
    jsr pending_name_matches_export_window
    bcc pending_name_already_exported_found
    inc saved_pending_index
    jmp pending_name_already_exported_loop
pending_name_already_exported_found:
    clc
    rts
pending_name_already_exported_not_found:
    sec
    rts

pending_name_matches_external_window:
    ldy #$00
pending_name_matches_external_window_loop:
    lda pending_name_window,y
    cmp external_name_window,y
    bne pending_name_matches_external_window_fail
    lda pending_name_window,y
    beq pending_name_matches_external_window_ok
    iny
    cpy #25
    bcc pending_name_matches_external_window_loop
pending_name_matches_external_window_fail:
    sec
    rts
pending_name_matches_external_window_ok:
    clc
    rts

pending_name_matches_export_window:
    ldy #$00
pending_name_matches_export_window_loop:
    lda pending_name_window,y
    jsr lowercase_ascii
    sta compare_char
    lda export_name_window,y
    jsr lowercase_ascii
    cmp compare_char
    bne pending_name_matches_export_window_fail
    lda pending_name_window,y
    beq pending_name_matches_export_window_ok
    iny
    cpy #25
    bcc pending_name_matches_export_window_loop
pending_name_matches_export_window_fail:
    sec
    rts
pending_name_matches_export_window_ok:
    clc
    rts

pending_name_already_loaded_exported:
    jsr reset_scan_ptr_after_header
pending_name_already_loaded_exported_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq pending_name_already_loaded_exported_not_found
    lda #<line_export
    sta const_ptr
    lda #>line_export
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs pending_name_already_loaded_exported_next
    jsr advance_scan_ptr_by_const_ptr
    jsr pending_name_matches_scan_symbol
    bcc pending_name_already_loaded_exported_found
pending_name_already_loaded_exported_next:
    jsr skip_current_line
    jmp pending_name_already_loaded_exported_loop
pending_name_already_loaded_exported_found:
    clc
    rts
pending_name_already_loaded_exported_not_found:
    sec
    rts

pending_name_matches_scan_symbol:
    ldy #$00
pending_name_matches_scan_symbol_loop:
    lda pending_name_window,y
    beq pending_name_matches_scan_symbol_check_source_end
    jsr lowercase_ascii
    sta compare_char
    lda (scan_ptr),y
    jsr lowercase_ascii
    cmp compare_char
    bne pending_name_matches_scan_symbol_fail
    iny
    cpy #25
    bcc pending_name_matches_scan_symbol_loop
pending_name_matches_scan_symbol_fail:
    sec
    rts
pending_name_matches_scan_symbol_check_source_end:
    lda (scan_ptr),y
    beq pending_name_matches_scan_symbol_ok
    cmp #' '
    beq pending_name_matches_scan_symbol_ok
    cmp #10
    beq pending_name_matches_scan_symbol_ok
    cmp #13
    beq pending_name_matches_scan_symbol_ok
    sec
    rts
pending_name_matches_scan_symbol_ok:
    clc
    rts

copy_pending_name_to_external_window:
    ldy #$00
copy_pending_name_to_external_window_loop:
    lda pending_name_window,y
    sta external_name_window,y
    beq copy_pending_name_to_external_window_done
    iny
    cpy #25
    bcc copy_pending_name_to_external_window_loop
copy_pending_name_to_external_window_done:
    rts

scan_symbol_matches_module_name:
    ldy #$00
scan_symbol_matches_module_name_loop:
    cpy #24
    bcs scan_symbol_matches_module_name_fail
    lda module_name,y
    jsr lowercase_ascii
    sta compare_char
    lda (scan_ptr),y
    cmp #' '
    beq scan_symbol_matches_module_name_source_end
    cmp #10
    beq scan_symbol_matches_module_name_source_end
    cmp #13
    beq scan_symbol_matches_module_name_source_end
    cmp #$00
    beq scan_symbol_matches_module_name_source_end
    jsr lowercase_ascii
    cmp compare_char
    bne scan_symbol_matches_module_name_fail
    iny
    jmp scan_symbol_matches_module_name_loop
scan_symbol_matches_module_name_source_end:
    lda module_name,y
    jsr lowercase_ascii
    cmp #$00
    bne scan_symbol_matches_module_name_fail
    clc
    rts
scan_symbol_matches_module_name_fail:
    sec
    rts

require_loaded_source_not_truncated_or_fail:
    lda truncated_flag
    beq require_loaded_source_not_truncated_or_fail_done
    lda #<msg_too_large
    ldy #>msg_too_large
    jmp fail_with_ptr
require_loaded_source_not_truncated_or_fail_done:
    rts

require_supported_object_header_or_fail:
    lda source_buffer+0
    cmp #'O'
    bne require_supported_object_header_bad
    lda source_buffer+1
    cmp #'B'
    bne require_supported_object_header_bad
    lda source_buffer+2
    cmp #'J'
    bne require_supported_object_header_bad
    lda source_buffer+3
    cmp #'1'
    beq require_supported_object_header_done
    bne require_supported_object_header_bad
require_supported_object_header_bad:
    jsr snapshot_bad_object_state
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
require_supported_object_header_done:
    rts

parse_exports_or_fail:
    lda #$00
    sta export_count
    jsr reset_scan_ptr_after_header
parse_exports_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq parse_exports_done_check
    lda #<line_export
    sta const_ptr
    lda #>line_export
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs parse_exports_next_line
    jsr advance_scan_ptr_by_const_ptr
    jsr copy_export_symbol_line_or_fail
    jsr reject_duplicate_export_or_fail
    jsr require_space_or_fail
    jsr parse_decimal_word_or_fail
    lda current_bit_lo
    sta export_meta_window+EXPORT_META_OFFSET_LO
    lda current_bit_hi
    sta export_meta_window+EXPORT_META_OFFSET_HI
    jsr require_space_or_fail
    jsr parse_decimal_word_or_fail
    lda current_bit_lo
    sta export_meta_window+EXPORT_META_SIZE_LO
    lda current_bit_hi
    sta export_meta_window+EXPORT_META_SIZE_HI
    ldx export_count
    jsr store_export_meta_window_from_x_or_fail
    inc export_count
parse_exports_next_line:
    jsr skip_current_line
    jmp parse_exports_loop
parse_exports_done_check:
    lda export_count
    bne parse_exports_done
parse_exports_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
parse_exports_done:
    rts

copy_export_symbol_line_or_fail:
    lda export_count
    cmp #EXPORT_MAX
    bcc :+
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
:   ldx export_count
    jsr set_export_window_ptr
    ldy #$00
copy_export_symbol_line_or_fail_loop:
    lda (scan_ptr),y
    beq parse_exports_bad
    cmp #' '
    beq copy_export_symbol_line_or_fail_done
    cmp #10
    beq copy_export_symbol_line_or_fail_done
    cmp #13
    beq copy_export_symbol_line_or_fail_done
    sta (export_ptr),y
    iny
    cpy #24
    bcc copy_export_symbol_line_or_fail_loop
    jmp parse_exports_bad
copy_export_symbol_line_or_fail_done:
    cpy #$00
    beq parse_exports_bad
    lda #$00
    sta (export_ptr),y
copy_export_symbol_line_advance_loop:
    cpy #$00
    beq copy_export_symbol_line_advanced
    jsr advance_scan_ptr
    dey
    bne copy_export_symbol_line_advance_loop
copy_export_symbol_line_advanced:
    ldx export_count
    jsr store_export_name_window_from_x_or_fail
    rts

reject_duplicate_export_or_fail:
    lda export_count
    beq reject_duplicate_export_done
    jsr copy_export_name_window_to_symbol_buffer
    lda #$00
    sta current_bit_hi
reject_duplicate_export_loop:
    ldx current_bit_hi
    cpx export_count
    beq reject_duplicate_export_done
    jsr load_export_name_window_from_x_or_fail
    jsr export_name_window_matches_symbol_buffer
    bcc reject_duplicate_export_bad
    inc current_bit_hi
    bne reject_duplicate_export_loop
reject_duplicate_export_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
reject_duplicate_export_done:
    rts

copy_export_name_window_to_symbol_buffer:
    ldy #$00
copy_export_name_window_to_symbol_buffer_loop:
    lda export_name_window,y
    sta symbol_buffer,y
    beq copy_export_name_window_to_symbol_buffer_done
    iny
    cpy #25
    bcc copy_export_name_window_to_symbol_buffer_loop
copy_export_name_window_to_symbol_buffer_done:
    rts

export_name_window_matches_symbol_buffer:
    ldy #$00
export_name_window_matches_symbol_buffer_loop:
    lda export_name_window,y
    jsr lowercase_ascii
    sta compare_char
    lda symbol_buffer,y
    jsr lowercase_ascii
    cmp compare_char
    bne export_name_window_matches_symbol_buffer_fail
    lda export_name_window,y
    beq export_name_window_matches_symbol_buffer_ok
    iny
    cpy #25
    bcc export_name_window_matches_symbol_buffer_loop
export_name_window_matches_symbol_buffer_fail:
    sec
    rts
export_name_window_matches_symbol_buffer_ok:
    clc
    rts

set_export_ptr_from_x:
    jsr load_export_name_window_from_x_or_fail
    jmp set_export_window_ptr

set_export_window_ptr:
    lda #<export_name_window
    sta export_ptr
    lda #>export_name_window
    sta export_ptr+1
    rts

load_export_name_window_from_x_or_fail:
    txa
    pha
    jsr set_export_name_reu_params_from_x
    lda #<export_name_window
    sta file_params+3
    lda #>export_name_window
    sta file_params+4
    lda #<EXPORT_NAME_BYTES
    sta file_params+5
    lda #>EXPORT_NAME_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_export_name_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_export_name_window_from_x_ok:
    pla
    tax
    rts

store_export_name_window_from_x_or_fail:
    txa
    pha
    jsr set_export_name_reu_params_from_x
    lda #<export_name_window
    sta file_params+3
    lda #>export_name_window
    sta file_params+4
    lda #<EXPORT_NAME_BYTES
    sta file_params+5
    lda #>EXPORT_NAME_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_export_name_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_export_name_window_from_x_ok:
    pla
    tax
    rts

load_root_export_name_window_from_x_or_fail:
    txa
    pha
    jsr set_root_export_name_reu_params_from_x
    lda #<export_name_window
    sta file_params+3
    lda #>export_name_window
    sta file_params+4
    lda #<EXPORT_NAME_BYTES
    sta file_params+5
    lda #>EXPORT_NAME_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_root_export_name_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_root_export_name_window_from_x_ok:
    pla
    tax
    rts

store_root_export_name_window_from_x_or_fail:
    txa
    pha
    jsr set_root_export_name_reu_params_from_x
    lda #<export_name_window
    sta file_params+3
    lda #>export_name_window
    sta file_params+4
    lda #<EXPORT_NAME_BYTES
    sta file_params+5
    lda #>EXPORT_NAME_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_root_export_name_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_root_export_name_window_from_x_ok:
    pla
    tax
    rts

set_root_export_name_reu_params_from_x:
    lda #ALINK_ROOT_EXPORT_REU_BASE_LO
    sta file_params+0
    lda #ALINK_ROOT_EXPORT_REU_BASE_HI
    sta file_params+1
    lda #ALINK_ROOT_EXPORT_REU_BASE_BANK
    sta file_params+2
set_root_export_name_reu_params_from_x_loop:
    cpx #$00
    beq set_root_export_name_reu_params_from_x_done
    clc
    lda file_params+0
    adc #EXPORT_NAME_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_root_export_name_reu_params_from_x_loop
set_root_export_name_reu_params_from_x_done:
    rts

set_export_name_reu_params_from_x:
    lda #ALINK_EXPORT_REU_BASE_LO
    sta file_params+0
    lda #ALINK_EXPORT_REU_BASE_HI
    sta file_params+1
    lda #ALINK_EXPORT_REU_BASE_BANK
    sta file_params+2
set_export_name_reu_params_from_x_loop:
    cpx #$00
    beq set_export_name_reu_params_from_x_done
    clc
    lda file_params+0
    adc #EXPORT_NAME_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_export_name_reu_params_from_x_loop
set_export_name_reu_params_from_x_done:
    rts

set_external_ptr_from_x:
    jsr load_external_name_window_from_x_or_fail
    jmp set_external_window_ptr

set_external_window_ptr:
    lda #<external_name_window
    sta export_ptr
    lda #>external_name_window
    sta export_ptr+1
    rts

load_external_name_window_from_x_or_fail:
    txa
    pha
    jsr set_external_name_reu_params_from_x
    lda #<external_name_window
    sta file_params+3
    lda #>external_name_window
    sta file_params+4
    lda #<EXTERNAL_NAME_BYTES
    sta file_params+5
    lda #>EXTERNAL_NAME_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_external_name_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_external_name_window_from_x_ok:
    pla
    tax
    rts

store_external_name_window_from_x_or_fail:
    txa
    pha
    jsr set_external_name_reu_params_from_x
    lda #<external_name_window
    sta file_params+3
    lda #>external_name_window
    sta file_params+4
    lda #<EXTERNAL_NAME_BYTES
    sta file_params+5
    lda #>EXTERNAL_NAME_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_external_name_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_external_name_window_from_x_ok:
    pla
    tax
    rts

set_external_name_reu_params_from_x:
    lda #ALINK_EXTERNAL_REU_BASE_LO
    sta file_params+0
    lda #ALINK_EXTERNAL_REU_BASE_HI
    sta file_params+1
    lda #ALINK_EXTERNAL_REU_BASE_BANK
    sta file_params+2
set_external_name_reu_params_from_x_loop:
    cpx #$00
    beq set_external_name_reu_params_from_x_done
    clc
    lda file_params+0
    adc #EXTERNAL_NAME_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_external_name_reu_params_from_x_loop
set_external_name_reu_params_from_x_done:
    rts

set_var_ptr_from_x:
    jsr load_var_name_window_from_x_or_fail
    jmp set_var_window_ptr

set_var_window_ptr:
    lda #<var_name_window
    sta export_ptr
    lda #>var_name_window
    sta export_ptr+1
    rts

load_var_name_window_from_x_or_fail:
    txa
    pha
    jsr set_var_name_reu_params_from_x
    lda #<var_name_window
    sta file_params+3
    lda #>var_name_window
    sta file_params+4
    lda #<VAR_NAME_BYTES
    sta file_params+5
    lda #>VAR_NAME_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_var_name_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_var_name_window_from_x_ok:
    pla
    tax
    rts

store_var_name_window_from_x_or_fail:
    txa
    pha
    jsr set_var_name_reu_params_from_x
    lda #<var_name_window
    sta file_params+3
    lda #>var_name_window
    sta file_params+4
    lda #<VAR_NAME_BYTES
    sta file_params+5
    lda #>VAR_NAME_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_var_name_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_var_name_window_from_x_ok:
    pla
    tax
    rts

set_var_name_reu_params_from_x:
    lda #ALINK_VAR_REU_BASE_LO
    sta file_params+0
    lda #ALINK_VAR_REU_BASE_HI
    sta file_params+1
    lda #ALINK_VAR_REU_BASE_BANK
    sta file_params+2
set_var_name_reu_params_from_x_loop:
    cpx #$00
    beq set_var_name_reu_params_from_x_done
    clc
    lda file_params+0
    adc #VAR_NAME_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_var_name_reu_params_from_x_loop
set_var_name_reu_params_from_x_done:
    rts

set_pending_window_ptr:
    lda #<pending_name_window
    sta export_ptr
    lda #>pending_name_window
    sta export_ptr+1
    rts

set_body_ptr_from_x:
    jsr load_body_window_from_x_or_fail
    jmp set_body_window_ptr

set_body_window_ptr:
    lda #<body_ops_window
    sta body_ptr
    lda #>body_ops_window
    sta body_ptr+1
    rts

load_body_window_from_x_or_fail:
    txa
    pha
    jsr set_body_reu_params_from_x
    lda #<body_ops_window
    sta file_params+3
    lda #>body_ops_window
    sta file_params+4
    lda #<BODY_OPS_STRIDE
    sta file_params+5
    lda #>BODY_OPS_STRIDE
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_body_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_body_window_from_x_ok:
    pla
    tax
    rts

store_body_window_from_x_or_fail:
    txa
    pha
    jsr set_body_reu_params_from_x
    lda #<body_ops_window
    sta file_params+3
    lda #>body_ops_window
    sta file_params+4
    lda #<BODY_OPS_STRIDE
    sta file_params+5
    lda #>BODY_OPS_STRIDE
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_body_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_body_window_from_x_ok:
    pla
    tax
    rts

set_body_reu_params_from_x:
    lda #ALINK_BODY_REU_BASE_LO
    sta file_params+0
    lda #ALINK_BODY_REU_BASE_HI
    sta file_params+1
    lda #ALINK_BODY_REU_BASE_BANK
    sta file_params+2
set_body_reu_params_from_x_loop:
    cpx #$00
    beq set_body_reu_params_from_x_done
    clc
    lda file_params+0
    adc #<BODY_OPS_STRIDE
    sta file_params+0
    lda file_params+1
    adc #>BODY_OPS_STRIDE
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_body_reu_params_from_x_loop
set_body_reu_params_from_x_done:
    rts

set_string_ptr_from_x:
    jsr load_string_window_from_x_or_fail
    jmp set_string_window_ptr

set_string_window_ptr:
    lda #<string_literal_window
    sta const_ptr
    lda #>string_literal_window
    sta const_ptr+1
    rts

load_string_window_from_x_or_fail:
    txa
    pha
    jsr set_string_reu_params_from_x
    lda #<string_literal_window
    sta file_params+3
    lda #>string_literal_window
    sta file_params+4
    lda #<STRING_LITERAL_ENTRY_BYTES
    sta file_params+5
    lda #>STRING_LITERAL_ENTRY_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_string_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_string_window_from_x_ok:
    pla
    tax
    rts

store_string_window_from_x_or_fail:
    txa
    pha
    jsr set_string_reu_params_from_x
    lda #<string_literal_window
    sta file_params+3
    lda #>string_literal_window
    sta file_params+4
    lda #<STRING_LITERAL_ENTRY_BYTES
    sta file_params+5
    lda #>STRING_LITERAL_ENTRY_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_string_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_string_window_from_x_ok:
    pla
    tax
    rts

load_saved_string_window_from_x_or_fail:
    txa
    pha
    jsr set_saved_string_reu_params_from_x
    lda #<string_literal_window
    sta file_params+3
    lda #>string_literal_window
    sta file_params+4
    lda #<STRING_LITERAL_ENTRY_BYTES
    sta file_params+5
    lda #>STRING_LITERAL_ENTRY_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_saved_string_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_saved_string_window_from_x_ok:
    pla
    tax
    rts

store_saved_string_window_from_x_or_fail:
    txa
    pha
    jsr set_saved_string_reu_params_from_x
    lda #<string_literal_window
    sta file_params+3
    lda #>string_literal_window
    sta file_params+4
    lda #<STRING_LITERAL_ENTRY_BYTES
    sta file_params+5
    lda #>STRING_LITERAL_ENTRY_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_saved_string_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_saved_string_window_from_x_ok:
    pla
    tax
    rts

copy_current_string_to_saved_string_from_x_or_fail:
    txa
    pha
    jsr load_string_window_from_x_or_fail
    pla
    tax
    jmp store_saved_string_window_from_x_or_fail

copy_saved_string_to_current_string_from_x_or_fail:
    txa
    pha
    jsr load_saved_string_window_from_x_or_fail
    pla
    tax
    jmp store_string_window_from_x_or_fail

set_string_reu_params_from_x:
    lda #ALINK_STRING_REU_BASE_LO
    sta file_params+0
    lda #ALINK_STRING_REU_BASE_HI
    sta file_params+1
    lda #ALINK_STRING_REU_BASE_BANK
    sta file_params+2
set_string_reu_params_from_x_loop:
    cpx #$00
    beq set_string_reu_params_from_x_done
    clc
    lda file_params+0
    adc #STRING_LITERAL_ENTRY_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_string_reu_params_from_x_loop
set_string_reu_params_from_x_done:
    rts

set_saved_string_reu_params_from_x:
    lda #ALINK_SAVED_STRING_REU_BASE_LO
    sta file_params+0
    lda #ALINK_SAVED_STRING_REU_BASE_HI
    sta file_params+1
    lda #ALINK_SAVED_STRING_REU_BASE_BANK
    sta file_params+2
set_saved_string_reu_params_from_x_loop:
    cpx #$00
    beq set_saved_string_reu_params_from_x_done
    clc
    lda file_params+0
    adc #STRING_LITERAL_ENTRY_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_saved_string_reu_params_from_x_loop
set_saved_string_reu_params_from_x_done:
    rts

clear_string_use_mask:
    ldy #$00
:   lda #$00
    sta string_use_mask,y
    iny
    cpy #STRING_MASK_BYTES
    bcc :-
    lda #$00
    rts

load_pending_meta_window_from_x_or_fail:
    txa
    pha
    jsr set_pending_meta_reu_params_from_x
    lda #<pending_meta_window
    sta file_params+3
    lda #>pending_meta_window
    sta file_params+4
    lda #<PENDING_META_BYTES
    sta file_params+5
    lda #>PENDING_META_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_pending_meta_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_pending_meta_window_from_x_ok:
    pla
    tax
    rts

store_pending_meta_window_from_x_or_fail:
    txa
    pha
    jsr set_pending_meta_reu_params_from_x
    lda #<pending_meta_window
    sta file_params+3
    lda #>pending_meta_window
    sta file_params+4
    lda #<PENDING_META_BYTES
    sta file_params+5
    lda #>PENDING_META_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_pending_meta_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_pending_meta_window_from_x_ok:
    pla
    tax
    rts

set_pending_meta_reu_params_from_x:
    lda #ALINK_PENDING_META_REU_BASE_LO
    sta file_params+0
    lda #ALINK_PENDING_META_REU_BASE_HI
    sta file_params+1
    lda #ALINK_PENDING_META_REU_BASE_BANK
    sta file_params+2
set_pending_meta_reu_params_from_x_loop:
    cpx #$00
    beq set_pending_meta_reu_params_from_x_done
    clc
    lda file_params+0
    adc #PENDING_META_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_pending_meta_reu_params_from_x_loop
set_pending_meta_reu_params_from_x_done:
    rts

load_pending_target_offset_from_x:
    jsr load_pending_meta_window_from_x_or_fail
    lda pending_meta_window+PENDING_META_OFFSET_LO
    sta current_bit_lo
    lda pending_meta_window+PENDING_META_OFFSET_HI
    sta current_bit_hi
    rts

load_pending_string_base_from_x:
    jsr load_pending_meta_window_from_x_or_fail
    lda pending_meta_window+PENDING_META_STRING_BASE_LO
    sta current_bit_lo
    lda pending_meta_window+PENDING_META_STRING_BASE_HI
    sta current_bit_hi
    rts

store_pending_string_use_mask_from_x:
    jsr load_pending_meta_window_from_x_or_fail
    ldy #$00
store_pending_string_use_mask_from_x_loop:
    lda string_use_mask,y
    sta pending_meta_window+PENDING_META_STRING_MASK,y
    iny
    cpy #STRING_MASK_BYTES
    bcc store_pending_string_use_mask_from_x_loop
    jmp store_pending_meta_window_from_x_or_fail

load_pending_string_use_mask_from_x:
    jsr load_pending_meta_window_from_x_or_fail
    ldy #$00
load_pending_string_use_mask_from_x_loop:
    lda pending_meta_window+PENDING_META_STRING_MASK,y
    sta string_use_mask,y
    iny
    cpy #STRING_MASK_BYTES
    bcc load_pending_string_use_mask_from_x_loop
    rts

load_linked_reloc_record_window_from_x_or_fail:
    txa
    pha
    jsr set_linked_reloc_reu_params_from_x
    lda #<reloc_record_window
    sta file_params+3
    lda #>reloc_record_window
    sta file_params+4
    lda #<RELOC_RECORD_BYTES
    sta file_params+5
    lda #>RELOC_RECORD_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_linked_reloc_record_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_linked_reloc_record_window_from_x_ok:
    pla
    tax
    rts

store_linked_reloc_record_window_from_x_or_fail:
    txa
    pha
    jsr set_linked_reloc_reu_params_from_x
    lda #<reloc_record_window
    sta file_params+3
    lda #>reloc_record_window
    sta file_params+4
    lda #<RELOC_RECORD_BYTES
    sta file_params+5
    lda #>RELOC_RECORD_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_linked_reloc_record_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_linked_reloc_record_window_from_x_ok:
    pla
    tax
    rts

set_linked_reloc_reu_params_from_x:
    lda #ALINK_RELOC_REU_BASE_LO
    sta file_params+0
    lda #ALINK_RELOC_REU_BASE_HI
    sta file_params+1
    lda #ALINK_RELOC_REU_BASE_BANK
    sta file_params+2
set_linked_reloc_reu_params_from_x_loop:
    cpx #$00
    beq set_linked_reloc_reu_params_from_x_done
    clc
    lda file_params+0
    adc #RELOC_RECORD_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_linked_reloc_reu_params_from_x_loop
set_linked_reloc_reu_params_from_x_done:
    rts

load_int_value_window_from_x_or_fail:
    txa
    pha
    jsr set_int_reu_params_from_x
    lda #<int_value_window
    sta file_params+3
    lda #>int_value_window
    sta file_params+4
    lda #<INT_VALUE_BYTES
    sta file_params+5
    lda #>INT_VALUE_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_int_value_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_int_value_window_from_x_ok:
    pla
    tax
    rts

store_int_value_window_from_x_or_fail:
    txa
    pha
    jsr set_int_reu_params_from_x
    lda #<int_value_window
    sta file_params+3
    lda #>int_value_window
    sta file_params+4
    lda #<INT_VALUE_BYTES
    sta file_params+5
    lda #>INT_VALUE_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_int_value_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_int_value_window_from_x_ok:
    pla
    tax
    rts

set_int_reu_params_from_x:
    lda #ALINK_INT_REU_BASE_LO
    sta file_params+0
    lda #ALINK_INT_REU_BASE_HI
    sta file_params+1
    lda #ALINK_INT_REU_BASE_BANK
    sta file_params+2
set_int_reu_params_from_x_loop:
    cpx #$00
    beq set_int_reu_params_from_x_done
    clc
    lda file_params+0
    adc #INT_VALUE_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_int_reu_params_from_x_loop
set_int_reu_params_from_x_done:
    rts

load_var_meta_window_from_x_or_fail:
    txa
    pha
    jsr set_var_meta_reu_params_from_x
    lda #<var_meta_window
    sta file_params+3
    lda #>var_meta_window
    sta file_params+4
    lda #<VAR_META_BYTES
    sta file_params+5
    lda #>VAR_META_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_var_meta_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_var_meta_window_from_x_ok:
    pla
    tax
    rts

store_var_meta_window_from_x_or_fail:
    txa
    pha
    jsr set_var_meta_reu_params_from_x
    lda #<var_meta_window
    sta file_params+3
    lda #>var_meta_window
    sta file_params+4
    lda #<VAR_META_BYTES
    sta file_params+5
    lda #>VAR_META_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_var_meta_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_var_meta_window_from_x_ok:
    pla
    tax
    rts

set_var_meta_reu_params_from_x:
    lda #ALINK_VAR_META_REU_BASE_LO
    sta file_params+0
    lda #ALINK_VAR_META_REU_BASE_HI
    sta file_params+1
    lda #ALINK_VAR_META_REU_BASE_BANK
    sta file_params+2
set_var_meta_reu_params_from_x_loop:
    cpx #$00
    beq set_var_meta_reu_params_from_x_done
    clc
    lda file_params+0
    adc #VAR_META_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_var_meta_reu_params_from_x_loop
set_var_meta_reu_params_from_x_done:
    rts

load_export_meta_window_from_x_or_fail:
    txa
    pha
    jsr set_export_meta_reu_params_from_x
    lda #<export_meta_window
    sta file_params+3
    lda #>export_meta_window
    sta file_params+4
    lda #<EXPORT_META_BYTES
    sta file_params+5
    lda #>EXPORT_META_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_export_meta_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_export_meta_window_from_x_ok:
    pla
    tax
    rts

store_export_meta_window_from_x_or_fail:
    txa
    pha
    jsr set_export_meta_reu_params_from_x
    lda #<export_meta_window
    sta file_params+3
    lda #>export_meta_window
    sta file_params+4
    lda #<EXPORT_META_BYTES
    sta file_params+5
    lda #>EXPORT_META_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_export_meta_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_export_meta_window_from_x_ok:
    pla
    tax
    rts

set_export_meta_reu_params_from_x:
    lda #ALINK_EXPORT_META_REU_BASE_LO
    sta file_params+0
    lda #ALINK_EXPORT_META_REU_BASE_HI
    sta file_params+1
    lda #ALINK_EXPORT_META_REU_BASE_BANK
    sta file_params+2
set_export_meta_reu_params_from_x_loop:
    cpx #$00
    beq set_export_meta_reu_params_from_x_done
    clc
    lda file_params+0
    adc #EXPORT_META_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_export_meta_reu_params_from_x_loop
set_export_meta_reu_params_from_x_done:
    rts

load_root_export_layout_window_from_x_or_fail:
    txa
    pha
    jsr set_root_export_layout_reu_params_from_x
    lda #<export_layout_window
    sta file_params+3
    lda #>export_layout_window
    sta file_params+4
    lda #<EXPORT_LAYOUT_BYTES
    sta file_params+5
    lda #>EXPORT_LAYOUT_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_root_export_layout_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_root_export_layout_window_from_x_ok:
    pla
    tax
    rts

store_root_export_layout_window_from_x_or_fail:
    txa
    pha
    jsr set_root_export_layout_reu_params_from_x
    lda #<export_layout_window
    sta file_params+3
    lda #>export_layout_window
    sta file_params+4
    lda #<EXPORT_LAYOUT_BYTES
    sta file_params+5
    lda #>EXPORT_LAYOUT_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_root_export_layout_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_root_export_layout_window_from_x_ok:
    pla
    tax
    rts

load_current_export_layout_window_from_x_or_fail:
    txa
    pha
    jsr set_current_export_layout_reu_params_from_x
    lda #<export_layout_window
    sta file_params+3
    lda #>export_layout_window
    sta file_params+4
    lda #<EXPORT_LAYOUT_BYTES
    sta file_params+5
    lda #>EXPORT_LAYOUT_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_current_export_layout_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_current_export_layout_window_from_x_ok:
    pla
    tax
    rts

store_current_export_layout_window_from_x_or_fail:
    txa
    pha
    jsr set_current_export_layout_reu_params_from_x
    lda #<export_layout_window
    sta file_params+3
    lda #>export_layout_window
    sta file_params+4
    lda #<EXPORT_LAYOUT_BYTES
    sta file_params+5
    lda #>EXPORT_LAYOUT_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_current_export_layout_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_current_export_layout_window_from_x_ok:
    pla
    tax
    rts

set_root_export_layout_reu_params_from_x:
    lda #ALINK_ROOT_EXPORT_LAYOUT_REU_BASE_LO
    sta file_params+0
    lda #ALINK_ROOT_EXPORT_LAYOUT_REU_BASE_HI
    sta file_params+1
    lda #ALINK_ROOT_EXPORT_LAYOUT_REU_BASE_BANK
    sta file_params+2
set_root_export_layout_reu_params_from_x_loop:
    cpx #$00
    beq set_root_export_layout_reu_params_from_x_done
    clc
    lda file_params+0
    adc #EXPORT_LAYOUT_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_root_export_layout_reu_params_from_x_loop
set_root_export_layout_reu_params_from_x_done:
    rts

set_current_export_layout_reu_params_from_x:
    lda #ALINK_CURRENT_EXPORT_LAYOUT_REU_BASE_LO
    sta file_params+0
    lda #ALINK_CURRENT_EXPORT_LAYOUT_REU_BASE_HI
    sta file_params+1
    lda #ALINK_CURRENT_EXPORT_LAYOUT_REU_BASE_BANK
    sta file_params+2
set_current_export_layout_reu_params_from_x_loop:
    cpx #$00
    beq set_current_export_layout_reu_params_from_x_done
    clc
    lda file_params+0
    adc #EXPORT_LAYOUT_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_current_export_layout_reu_params_from_x_loop
set_current_export_layout_reu_params_from_x_done:
    rts

load_root_var_layout_window_from_x_or_fail:
    txa
    pha
    jsr set_root_var_layout_reu_params_from_x
    lda #<var_layout_window
    sta file_params+3
    lda #>var_layout_window
    sta file_params+4
    lda #<VAR_LAYOUT_BYTES
    sta file_params+5
    lda #>VAR_LAYOUT_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_root_var_layout_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_root_var_layout_window_from_x_ok:
    pla
    tax
    rts

store_root_var_layout_window_from_x_or_fail:
    txa
    pha
    jsr set_root_var_layout_reu_params_from_x
    lda #<var_layout_window
    sta file_params+3
    lda #>var_layout_window
    sta file_params+4
    lda #<VAR_LAYOUT_BYTES
    sta file_params+5
    lda #>VAR_LAYOUT_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_root_var_layout_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_root_var_layout_window_from_x_ok:
    pla
    tax
    rts

load_current_var_layout_window_from_x_or_fail:
    txa
    pha
    jsr set_current_var_layout_reu_params_from_x
    lda #<var_layout_window
    sta file_params+3
    lda #>var_layout_window
    sta file_params+4
    lda #<VAR_LAYOUT_BYTES
    sta file_params+5
    lda #>VAR_LAYOUT_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_current_var_layout_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_current_var_layout_window_from_x_ok:
    pla
    tax
    rts

store_current_var_layout_window_from_x_or_fail:
    txa
    pha
    jsr set_current_var_layout_reu_params_from_x
    lda #<var_layout_window
    sta file_params+3
    lda #>var_layout_window
    sta file_params+4
    lda #<VAR_LAYOUT_BYTES
    sta file_params+5
    lda #>VAR_LAYOUT_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_current_var_layout_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_current_var_layout_window_from_x_ok:
    pla
    tax
    rts

set_root_var_layout_reu_params_from_x:
    lda #ALINK_ROOT_VAR_LAYOUT_REU_BASE_LO
    sta file_params+0
    lda #ALINK_ROOT_VAR_LAYOUT_REU_BASE_HI
    sta file_params+1
    lda #ALINK_ROOT_VAR_LAYOUT_REU_BASE_BANK
    sta file_params+2
set_root_var_layout_reu_params_from_x_loop:
    cpx #$00
    beq set_root_var_layout_reu_params_from_x_done
    clc
    lda file_params+0
    adc #VAR_LAYOUT_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_root_var_layout_reu_params_from_x_loop
set_root_var_layout_reu_params_from_x_done:
    rts

set_current_var_layout_reu_params_from_x:
    lda #ALINK_CURRENT_VAR_LAYOUT_REU_BASE_LO
    sta file_params+0
    lda #ALINK_CURRENT_VAR_LAYOUT_REU_BASE_HI
    sta file_params+1
    lda #ALINK_CURRENT_VAR_LAYOUT_REU_BASE_BANK
    sta file_params+2
set_current_var_layout_reu_params_from_x_loop:
    cpx #$00
    beq set_current_var_layout_reu_params_from_x_done
    clc
    lda file_params+0
    adc #VAR_LAYOUT_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_current_var_layout_reu_params_from_x_loop
set_current_var_layout_reu_params_from_x_done:
    rts

load_root_string_layout_window_from_x_or_fail:
    txa
    pha
    jsr set_root_string_layout_reu_params_from_x
    lda #<string_layout_window
    sta file_params+3
    lda #>string_layout_window
    sta file_params+4
    lda #<STRING_LAYOUT_BYTES
    sta file_params+5
    lda #>STRING_LAYOUT_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_root_string_layout_window_from_x_ok
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_root_string_layout_window_from_x_ok:
    pla
    tax
    rts

store_root_string_layout_window_from_x_or_fail:
    txa
    pha
    jsr set_root_string_layout_reu_params_from_x
    lda #<string_layout_window
    sta file_params+3
    lda #>string_layout_window
    sta file_params+4
    lda #<STRING_LAYOUT_BYTES
    sta file_params+5
    lda #>STRING_LAYOUT_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_root_string_layout_window_from_x_ok
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_root_string_layout_window_from_x_ok:
    pla
    tax
    rts

set_root_string_layout_reu_params_from_x:
    lda #ALINK_ROOT_STRING_LAYOUT_REU_BASE_LO
    sta file_params+0
    lda #ALINK_ROOT_STRING_LAYOUT_REU_BASE_HI
    sta file_params+1
    lda #ALINK_ROOT_STRING_LAYOUT_REU_BASE_BANK
    sta file_params+2
set_root_string_layout_reu_params_from_x_loop:
    cpx #$00
    beq set_root_string_layout_reu_params_from_x_done
    clc
    lda file_params+0
    adc #STRING_LAYOUT_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_root_string_layout_reu_params_from_x_loop
set_root_string_layout_reu_params_from_x_done:
    rts

load_live_flag_window_from_x_or_fail:
    txa
    pha
    tya
    pha
    jsr set_live_reu_params_from_x
    lda #<live_flag_window
    sta file_params+3
    lda #>live_flag_window
    sta file_params+4
    lda #<LIVE_FLAG_BYTES
    sta file_params+5
    lda #>LIVE_FLAG_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_live_flag_window_from_x_ok
    pla
    tay
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_live_flag_window_from_x_ok:
    pla
    tay
    pla
    tax
    rts

store_live_flag_window_from_x_or_fail:
    txa
    pha
    tya
    pha
    jsr set_live_reu_params_from_x
    lda #<live_flag_window
    sta file_params+3
    lda #>live_flag_window
    sta file_params+4
    lda #<LIVE_FLAG_BYTES
    sta file_params+5
    lda #>LIVE_FLAG_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_live_flag_window_from_x_ok
    pla
    tay
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_live_flag_window_from_x_ok:
    pla
    tay
    pla
    tax
    rts

set_live_reu_params_from_x:
    lda #ALINK_LIVE_REU_BASE_LO
    sta file_params+0
    lda #ALINK_LIVE_REU_BASE_HI
    sta file_params+1
    lda #ALINK_LIVE_REU_BASE_BANK
    sta file_params+2
set_live_reu_params_from_x_loop:
    cpx #$00
    beq set_live_reu_params_from_x_done
    clc
    inc file_params+0
    bne :+
    inc file_params+1
    bne :+
    inc file_params+2
:   dex
    bne set_live_reu_params_from_x_loop
set_live_reu_params_from_x_done:
    rts

load_loop_layout_window_from_x_or_fail:
    txa
    pha
    tya
    pha
    jsr set_loop_layout_reu_params_from_x
    lda #<loop_layout_window
    sta file_params+3
    lda #>loop_layout_window
    sta file_params+4
    lda #<LOOP_LAYOUT_BYTES
    sta file_params+5
    lda #>LOOP_LAYOUT_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_loop_layout_window_from_x_ok
    pla
    tay
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_loop_layout_window_from_x_ok:
    pla
    tay
    pla
    tax
    rts

store_loop_layout_window_from_x_or_fail:
    txa
    pha
    tya
    pha
    jsr set_loop_layout_reu_params_from_x
    lda #<loop_layout_window
    sta file_params+3
    lda #>loop_layout_window
    sta file_params+4
    lda #<LOOP_LAYOUT_BYTES
    sta file_params+5
    lda #>LOOP_LAYOUT_BYTES
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr alink_svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_loop_layout_window_from_x_ok
    pla
    tay
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_loop_layout_window_from_x_ok:
    pla
    tay
    pla
    tax
    rts

set_loop_layout_reu_params_from_x:
    lda #ALINK_LOOP_LAYOUT_REU_BASE_LO
    sta file_params+0
    lda #ALINK_LOOP_LAYOUT_REU_BASE_HI
    sta file_params+1
    lda #ALINK_LOOP_LAYOUT_REU_BASE_BANK
    sta file_params+2
set_loop_layout_reu_params_from_x_loop:
    cpx #$00
    beq set_loop_layout_reu_params_from_x_done
    clc
    lda file_params+0
    adc #LOOP_LAYOUT_BYTES
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_loop_layout_reu_params_from_x_loop
set_loop_layout_reu_params_from_x_done:
    rts

test_string_use_mask_for_x:
    txa
    sta string_mask_saved_x
    and #$07
    tax
    lda bit_masks,x
    sta string_mask_saved_bit
    ldx string_mask_saved_x
    txa
    lsr
    lsr
    lsr
    tay
    lda string_mask_saved_bit
    and string_use_mask,y
    pha
    ldx string_mask_saved_x
    pla
    rts

or_string_use_mask_for_x:
    sty string_mask_saved_y
    txa
    sta string_mask_saved_x
    and #$07
    tax
    lda bit_masks,x
    sta string_mask_saved_bit
    ldx string_mask_saved_x
    txa
    lsr
    lsr
    lsr
    tay
    lda string_mask_saved_bit
    ora string_use_mask,y
    sta string_use_mask,y
    ldx string_mask_saved_x
    ldy string_mask_saved_y
    rts

copy_string_literal_block:
    lda saved_state_lo
    ora saved_state_hi
    beq copy_string_literal_block_done
    ldy #$00
copy_string_literal_block_loop:
    lda (src_ptr),y
    sta (const_ptr),y
    inc src_ptr
    bne :+
    inc src_ptr+1
:   inc const_ptr
    bne :+
    inc const_ptr+1
:   lda saved_state_lo
    bne :+
    dec saved_state_hi
:   dec saved_state_lo
    lda saved_state_lo
    ora saved_state_hi
    bne copy_string_literal_block_loop
copy_string_literal_block_done:
    rts

parse_body_ops_or_fail:
    lda #$00
    sta export_index
    sta debug_phase
    jsr reset_scan_ptr_after_header
parse_body_ops_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    bne :+
    jmp parse_body_ops_done_check
:
    lda #<line_body
    sta const_ptr
    lda #>line_body
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcc :+
    jmp parse_body_ops_next_line
:
    jsr advance_scan_ptr_by_const_ptr
    lda export_index
    cmp export_count
    bcc :+
    lda #$21
    sta debug_phase
    lda export_index
    sta $03FA
    lda export_count
    sta $03FB
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
:   ldx export_index
    jsr set_body_window_ptr
    ldy #$00
parse_body_ops_string_loop:
    lda (scan_ptr),y
    bne :+
    jmp parse_body_ops_string_done
:
    cmp #10
    bne :+
    jmp parse_body_ops_string_done
:
    cmp #13
    bne :+
    jmp parse_body_ops_string_done
:
    cmp #'c'
    beq parse_body_ops_store_branch
    cmp #'u'
    beq parse_body_ops_store_branch
    cmp #'s'
    beq parse_body_ops_store_branch
    cmp #'e'
    beq parse_body_ops_store_branch
    cmp #'i'
    beq parse_body_ops_store_branch
    cmp #'j'
    beq parse_body_ops_store_branch
    cmp #'p'
    beq parse_body_ops_store_branch
    cmp #'a'
    beq parse_body_ops_store_branch
    cmp #'m'
    beq parse_body_ops_store_branch
    cmp #'*'
    beq parse_body_ops_store_branch
    cmp #'/'
    beq parse_body_ops_store_branch
    cmp #'q'
    beq parse_body_ops_store_branch
    cmp #'n'
    beq parse_body_ops_store_branch
    cmp #'l'
    beq parse_body_ops_store_branch
    cmp #'g'
    beq parse_body_ops_store_branch
	    cmp #'y'
	    beq parse_body_ops_store_branch
	    cmp #'z'
	    beq parse_body_ops_store_branch
    cmp #'h'
    beq parse_body_ops_store_branch
    cmp #'f'
    beq parse_body_ops_store_branch
    cmp #'t'
    beq parse_body_ops_store_branch
    cmp #'w'
    beq parse_body_ops_store_branch
    cmp #'v'
    beq parse_body_ops_store_branch
    cmp #'d'
    beq parse_body_ops_store_branch
    cmp #'o'
    beq parse_body_ops_store_branch
    cmp #'x'
    beq parse_body_ops_store_branch
    cmp #'r'
    beq parse_body_ops_store_branch
    cmp #'0'
    bcc parse_body_ops_check_alpha
    cmp #'9'+1
    bcc parse_body_ops_store_branch
parse_body_ops_check_alpha:
    cmp #'A'
    bcc parse_body_ops_bad
    cmp #'Z'+1
    bcs parse_body_ops_bad
parse_body_ops_store_branch:
    jmp parse_body_ops_store
parse_body_ops_string_done_branch:
    jmp parse_body_ops_string_done
parse_body_ops_store:
    sta (body_ptr),y
    iny
    cpy #BODY_OPS_STRIDE
    bcc :+
    lda #$22
    sta debug_phase
    sty $03FA
    jmp parse_body_ops_bad
:
    jmp parse_body_ops_string_loop
parse_body_ops_bad:
    sta $03FB
    lda debug_phase
    bne :+
    lda #$23
    sta debug_phase
:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
parse_body_ops_string_done:
    lda #$00
    sta (body_ptr),y
    ldx export_index
    jsr store_body_window_from_x_or_fail
    inc export_index
parse_body_ops_next_line:
    jsr skip_current_line
    jmp parse_body_ops_loop
parse_body_ops_done_check:
    lda export_index
    cmp export_count
    beq parse_body_ops_done
    lda #$24
    sta debug_phase
    lda export_index
    sta $03FA
    lda export_count
    sta $03FB
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
parse_body_ops_done:
    rts

parse_external_symbols_or_fail:
    lda #$00
    sta external_count
    jsr reset_scan_ptr_after_header
parse_external_symbols_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq parse_external_symbols_done
    lda #<line_external
    sta const_ptr
    lda #>line_external
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs parse_external_symbols_next_line
    jsr advance_scan_ptr_by_const_ptr
    jsr copy_external_symbol_line_or_fail
parse_external_symbols_next_line:
    jsr skip_current_line
    jmp parse_external_symbols_loop
parse_external_symbols_done:
    rts

copy_external_symbol_line_or_fail:
    lda external_count
    cmp #EXTERNAL_MAX
    bcc :+
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
:   ldx external_count
    jsr set_external_window_ptr
    ldy #$00
copy_external_symbol_line_or_fail_loop:
    lda (scan_ptr),y
    beq copy_external_symbol_line_or_fail_done
    cmp #' '
    beq copy_external_symbol_line_or_fail_done
    cmp #10
    beq copy_external_symbol_line_or_fail_done
    cmp #13
    beq copy_external_symbol_line_or_fail_done
    jsr lowercase_ascii
    cmp #'a'
    bcc copy_external_symbol_line_or_fail_symbol
    cmp #'z'+1
    bcc copy_external_symbol_line_or_fail_store
copy_external_symbol_line_or_fail_symbol:
    cmp #'0'
    bcc copy_external_symbol_line_or_fail_check_underscore
    cmp #'9'+1
    bcc copy_external_symbol_line_or_fail_store
copy_external_symbol_line_or_fail_check_underscore:
    cmp #'_'
    bne copy_external_symbol_line_or_fail_bad
copy_external_symbol_line_or_fail_store:
    sta (export_ptr),y
    iny
    cpy #24
    bcc copy_external_symbol_line_or_fail_loop
copy_external_symbol_line_or_fail_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
copy_external_symbol_line_or_fail_done:
    cpy #$00
    beq copy_external_symbol_line_or_fail_bad
    lda #$00
    sta (export_ptr),y
    ldx external_count
    jsr store_external_name_window_from_x_or_fail
    inc external_count
    rts

parse_strings_or_fail:
    lda #$00
    sta string_count
    jsr reset_scan_ptr_after_header
parse_strings_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq parse_strings_done
    lda #<line_string
    sta const_ptr
    lda #>line_string
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs parse_strings_next_line
    jsr advance_scan_ptr_by_const_ptr
    ldx string_count
    cpx #STRING_LITERAL_MAX
    bcc :+
parse_strings_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
:   jsr set_string_window_ptr
    ldy #$00
parse_strings_value_loop:
    lda (scan_ptr),y
    beq parse_strings_value_done
    cmp #10
    beq parse_strings_value_done
    cmp #13
    beq parse_strings_done
    sta (const_ptr),y
    iny
    cpy #23
    bcc parse_strings_value_loop
    jmp parse_strings_bad
parse_strings_value_done:
    lda #$00
    sta (const_ptr),y
    ldx string_count
    jsr store_string_window_from_x_or_fail
    inc string_count
parse_strings_next_line:
    jsr skip_current_line
    jmp parse_strings_loop
parse_strings_done:
    rts

parse_ints_or_fail:
    lda #$00
    sta int_count
    jsr reset_scan_ptr_after_header
parse_ints_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq parse_ints_done
    lda #<line_int
    sta const_ptr
    lda #>line_int
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs parse_ints_next_line
    jsr advance_scan_ptr_by_const_ptr
    ldx int_count
    cpx #INT_LITERAL_MAX
    bcc :+
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
:   jsr parse_decimal_word_or_fail
    lda current_bit_lo
    sta int_value_window
    lda current_bit_hi
    sta int_value_window+1
    ldx int_count
    jsr store_int_value_window_from_x_or_fail
    inc int_count
parse_ints_next_line:
    jsr skip_current_line
    jmp parse_ints_loop
parse_ints_done:
    rts

parse_vars_or_fail:
    lda #$00
    sta var_count
    jsr reset_scan_ptr_after_header
parse_vars_loop:
    jsr skip_line_breaks
    ldy #$00
    lda (scan_ptr),y
    beq parse_vars_done
    lda #<line_var
    sta const_ptr
    lda #>line_var
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs parse_vars_next_line
    jsr advance_scan_ptr_by_const_ptr
    ldx var_count
    cpx #VAR_MAX
    bcc :+
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
:   jsr copy_var_symbol_line_or_fail
    jsr require_space_or_fail
    jsr parse_decimal_byte_or_fail
    sta var_meta_window+VAR_META_INIT_LO
    lda #$00
    sta var_meta_window+VAR_META_INIT_HI
    lda #$02
    sta var_meta_window+VAR_META_WIDTH
    ldy #$00
    lda (scan_ptr),y
    cmp #' '
    bne parse_vars_store_done
    jsr advance_scan_ptr
    jsr parse_decimal_byte_or_fail
    cmp #$02
    beq parse_vars_store_width
    cmp #$04
    beq parse_vars_store_width
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
parse_vars_store_width:
    sta var_meta_window+VAR_META_WIDTH
parse_vars_store_done:
    ldx var_count
    jsr store_var_meta_window_from_x_or_fail
    inc var_count
parse_vars_next_line:
    jsr skip_current_line
    jmp parse_vars_loop
parse_vars_done:
    rts

copy_var_symbol_line_or_fail:
    ldx var_count
    jsr set_var_window_ptr
    ldy #$00
copy_var_symbol_line_or_fail_loop:
    lda (scan_ptr),y
    beq copy_var_symbol_line_or_fail_done
    cmp #' '
    beq copy_var_symbol_line_or_fail_done
    cmp #10
    beq copy_var_symbol_line_or_fail_done
    cmp #13
    beq copy_var_symbol_line_or_fail_done
    jsr lowercase_ascii
    cmp #'a'
    bcc copy_var_symbol_line_or_fail_symbol
    cmp #'z'+1
    bcc copy_var_symbol_line_or_fail_store
copy_var_symbol_line_or_fail_symbol:
    cmp #'0'
    bcc copy_var_symbol_line_or_fail_check_underscore
    cmp #'9'+1
    bcc copy_var_symbol_line_or_fail_store
copy_var_symbol_line_or_fail_check_underscore:
    cmp #'_'
    bne copy_var_symbol_line_or_fail_bad
copy_var_symbol_line_or_fail_store:
    sta (export_ptr),y
    iny
    cpy #24
    bcc copy_var_symbol_line_or_fail_loop
copy_var_symbol_line_or_fail_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
copy_var_symbol_line_or_fail_done:
    cpy #$00
    beq copy_var_symbol_line_or_fail_bad
    lda #$00
    sta (export_ptr),y
copy_var_symbol_line_or_fail_advance_loop:
    cpy #$00
    beq copy_var_symbol_line_or_fail_advanced
    jsr advance_scan_ptr
    dey
    bne copy_var_symbol_line_or_fail_advance_loop
copy_var_symbol_line_or_fail_advanced:
    ldx var_count
    jsr store_var_name_window_from_x_or_fail
    rts

reset_scan_ptr_after_header:
    jsr source_reader_reset_to_start
    bcc reset_scan_ptr_after_header_ok
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
reset_scan_ptr_after_header_ok:
    clc
    lda scan_ptr
    adc #$05
    sta scan_ptr
    lda scan_ptr+1
    adc #$00
    sta scan_ptr+1
    rts

require_space_or_fail:
    ldy #$00
    lda (scan_ptr),y
    cmp #' '
    beq require_space_or_fail_ok
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr
require_space_or_fail_ok:
    jsr advance_scan_ptr
    rts

compute_code_bytes:
    lda #$00
    sta payload_bytes_data
    sta payload_bytes_data_hi
    ldx #$00
compute_code_bytes_loop:
    cpx export_count
    beq compute_code_bytes_done
    jsr load_export_meta_window_from_x_or_fail
    lda export_meta_window+EXPORT_META_OFFSET_LO
    sta current_bit_lo
    lda export_meta_window+EXPORT_META_OFFSET_HI
    sta current_bit_hi
    clc
    lda current_bit_lo
    adc export_meta_window+EXPORT_META_SIZE_LO
    sta current_bit_lo
    lda current_bit_hi
    adc export_meta_window+EXPORT_META_SIZE_HI
    sta current_bit_hi
    lda current_bit_hi
    cmp payload_bytes_data_hi
    bcc compute_code_bytes_next
    bne compute_code_bytes_store
    lda current_bit_lo
    cmp payload_bytes_data
    bcc compute_code_bytes_next
compute_code_bytes_store:
    lda current_bit_lo
    sta payload_bytes_data
    lda current_bit_hi
    sta payload_bytes_data_hi
compute_code_bytes_next:
    inx
    bne compute_code_bytes_loop
compute_code_bytes_done:
    rts

parse_decimal_word_or_fail:
    lda #$00
    sta current_bit_lo
    sta current_bit_hi
    sta compare_char
parse_decimal_word_or_fail_loop:
    ldy #$00
    lda (scan_ptr),y
    cmp #'0'
    bcc parse_decimal_word_or_fail_done_check
    cmp #'9'+1
    bcs parse_decimal_word_or_fail_done_check
    sec
    sbc #'0'
    pha
    lda current_bit_lo
    sta parse_word_temp_lo
    lda current_bit_hi
    sta parse_word_temp_hi
    asl current_bit_lo
    rol current_bit_hi
    asl parse_word_temp_lo
    rol parse_word_temp_hi
    asl parse_word_temp_lo
    rol parse_word_temp_hi
    asl parse_word_temp_lo
    rol parse_word_temp_hi
    clc
    lda current_bit_lo
    adc parse_word_temp_lo
    sta current_bit_lo
    lda current_bit_hi
    adc parse_word_temp_hi
    sta current_bit_hi
    bcs parse_decimal_word_or_fail_bad
    pla
    clc
    adc current_bit_lo
    sta current_bit_lo
    bcc :+
    inc current_bit_hi
    beq parse_decimal_word_or_fail_bad
:   lda #$01
    sta compare_char
    jsr advance_scan_ptr
    jmp parse_decimal_word_or_fail_loop
parse_decimal_word_or_fail_done_check:
    lda compare_char
    beq parse_decimal_word_or_fail_bad
    rts
parse_decimal_word_or_fail_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr

parse_decimal_byte_or_fail:
    lda #$00
    sta current_bit_lo
    sta compare_char
parse_decimal_byte_or_fail_loop:
    ldy #$00
    lda (scan_ptr),y
    cmp #'0'
    bcc parse_decimal_byte_or_fail_done_check
    cmp #'9'+1
    bcs parse_decimal_byte_or_fail_done_check
    sec
    sbc #'0'
    pha
    lda current_bit_lo
    asl a
    sta current_bit_hi
    asl a
    asl a
    clc
    adc current_bit_hi
    bcs parse_decimal_byte_or_fail_bad
    sta current_bit_lo
    pla
    clc
    adc current_bit_lo
    bcs parse_decimal_byte_or_fail_bad
    sta current_bit_lo
    lda #$01
    sta compare_char
    jsr advance_scan_ptr
    jmp parse_decimal_byte_or_fail_loop
parse_decimal_byte_or_fail_done_check:
    lda compare_char
    beq parse_decimal_byte_or_fail_bad
    lda current_bit_lo
    rts
parse_decimal_byte_or_fail_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr

build_live_set:
    lda #$00
    sta live_flag_window
    ldx #$00
build_live_set_clear_loop:
    cpx #EXPORT_MAX
    beq build_live_set_seed
    jsr store_live_flag_window_from_x_or_fail
    inx
    bne build_live_set_clear_loop
build_live_set_seed:
    lda export_count
    bne :+
    jmp build_live_set_done
:   jsr find_export_index_from_module_name
    bcc :+
    jmp build_live_set_bad
:
    stx entry_export_index
    lda #$01
    sta live_flag_window
    jsr store_live_flag_window_from_x_or_fail
build_live_set_scan_again:
    lda #$00
    sta compare_char
    ldx #$00
build_live_set_export_loop:
    cpx export_count
    bne :+
    jmp build_live_set_check
:
    jsr load_live_flag_window_from_x_or_fail
    lda live_flag_window
    bne :+
    jmp build_live_set_next_export
:
    stx current_bit_hi
    jsr set_body_ptr_from_x
    ldy #$00
build_live_set_body_loop:
    lda (body_ptr),y
    bne :+
    jmp build_live_set_next_export_restore
:
    cmp #'c'
    bne :+
    jmp build_live_set_call
:
    cmp #'u'
    bne :+
    jmp build_live_set_skip_pair
:
    cmp #'s'
    beq build_live_set_skip_pair_branch
    cmp #'e'
    beq build_live_set_skip_pair_branch
    cmp #'i'
    beq build_live_set_skip_pair_branch
    cmp #'j'
    beq build_live_set_skip_pair_branch
    cmp #'p'
    beq build_live_set_skip_pair_branch
    cmp #'L'
    beq build_live_set_skip_pair_branch
    cmp #'S'
    beq build_live_set_skip_pair_branch
    cmp #'U'
    beq build_live_set_skip_pair_branch
    cmp #'T'
    beq build_live_set_skip_pair_branch
    jmp build_live_set_check_single_ops
build_live_set_skip_pair_branch:
    jmp build_live_set_skip_pair
build_live_set_check_single_ops:
    cmp #'D'
    beq build_live_set_single_branch
    cmp #'K'
    beq build_live_set_single_branch
    cmp #'a'
    beq build_live_set_single_branch
    cmp #'m'
    beq build_live_set_single_branch
    cmp #'*'
    beq build_live_set_single_branch
    cmp #'/'
    beq build_live_set_single_branch
    cmp #'q'
    beq build_live_set_single_branch
    cmp #'n'
    beq build_live_set_single_branch
    cmp #'l'
    beq build_live_set_single_branch
    cmp #'g'
    beq build_live_set_single_branch
    cmp #'B'
    beq build_live_set_single_branch
    cmp #'O'
    beq build_live_set_single_branch
    cmp #'X'
    beq build_live_set_single_branch
    cmp #'H'
    beq build_live_set_single_branch
    cmp #'R'
    beq build_live_set_single_branch
    cmp #'M'
    beq build_live_set_single_branch
	    cmp #'y'
	    beq build_live_set_single_branch
	    cmp #'z'
	    beq build_live_set_single_branch
	    cmp #'h'
	    beq build_live_set_single_branch
	    cmp #'f'
	    beq build_live_set_single_branch
	    cmp #'t'
	    beq build_live_set_single_branch
	    cmp #'w'
	    beq build_live_set_single_branch
	    cmp #'v'
	    beq build_live_set_single_branch
	    cmp #'d'
	    beq build_live_set_single_branch
	    cmp #'o'
	    beq build_live_set_single_branch
	    cmp #'x'
	    beq build_live_set_single_branch
	    cmp #'r'
	    beq build_live_set_ret_branch
    jmp build_live_set_bad
build_live_set_call_branch:
    jmp build_live_set_call
build_live_set_single_branch:
    jmp build_live_set_single
build_live_set_ret_branch:
    jmp build_live_set_ret
build_live_set_call:
    iny
    lda (body_ptr),y
    cmp #'0'
    bcc build_live_set_call_check_alpha
    cmp #'9'+1
    bcc build_live_set_call_dec
build_live_set_call_check_alpha:
    cmp #'A'
    bcc build_live_set_bad
    cmp #'Z'+1
    bcs build_live_set_bad
    sec
    sbc #'A'
    clc
    adc #10
    bne build_live_set_call_index
build_live_set_call_dec:
    sec
    sbc #'0'
build_live_set_call_index:
    tax
    jsr load_live_flag_window_from_x_or_fail
    lda live_flag_window
    bne build_live_set_call_done
    lda #$01
    sta live_flag_window
    jsr store_live_flag_window_from_x_or_fail
    lda #$01
    sta compare_char
build_live_set_call_done:
    ldx current_bit_hi
    iny
    jmp build_live_set_body_loop
build_live_set_skip_pair:
    iny
    iny
    jmp build_live_set_body_loop
build_live_set_single:
    iny
    jmp build_live_set_body_loop
build_live_set_ret:
    iny
    jmp build_live_set_body_loop
build_live_set_next_export_restore:
    ldx current_bit_hi
build_live_set_next_export:
    inx
    beq :+
    jmp build_live_set_export_loop
:
build_live_set_check:
    lda compare_char
    beq :+
    jmp build_live_set_scan_again
:
build_live_set_done:
    rts
build_live_set_bad:
    lda #<msg_bad_object
    ldy #>msg_bad_object
    jmp fail_with_ptr

clear_tool_scratch_before_save:
    lda #$00
    ldx #$00
clear_tool_scratch_before_save_loop:
    sta file_params,x
    inx
    cpx #9
    bcc clear_tool_scratch_before_save_loop
    rts

find_export_index_from_module_name:
    ldx #$00
find_export_index_from_module_name_loop:
    cpx export_count
    beq find_export_index_from_module_name_fail
    stx compare_char
    jsr set_export_ptr_from_x
    ldx compare_char
    ldy #$00
find_export_index_from_module_name_compare_loop:
    lda module_name,y
    jsr lowercase_ascii
    cmp (export_ptr),y
    bne find_export_index_from_module_name_next
    lda (export_ptr),y
    beq find_export_index_from_module_name_done
    iny
    bne find_export_index_from_module_name_compare_loop
find_export_index_from_module_name_next:
    inx
    bne find_export_index_from_module_name_loop
find_export_index_from_module_name_fail:
    sec
    rts
find_export_index_from_module_name_done:
    clc
    rts

symbol_buffer_matches_const_ptr:
    ldy #$00
symbol_buffer_matches_const_ptr_loop:
    lda (const_ptr),y
    cmp symbol_buffer,y
    bne symbol_buffer_matches_const_ptr_fail
    lda (const_ptr),y
    beq symbol_buffer_matches_const_ptr_ok
    iny
    bne symbol_buffer_matches_const_ptr_loop
symbol_buffer_matches_const_ptr_fail:
    sec
    rts
symbol_buffer_matches_const_ptr_ok:
    clc
    rts

pattern_matches_scan_ptr:
    ldy #$00
pattern_matches_scan_ptr_loop:
    lda (const_ptr),y
    beq pattern_matches_scan_ptr_ok
    sta compare_char
    lda (scan_ptr),y
    beq pattern_matches_scan_ptr_fail
    cmp compare_char
    bne pattern_matches_scan_ptr_fail
    iny
    bne pattern_matches_scan_ptr_loop
pattern_matches_scan_ptr_fail:
    sec
    rts
pattern_matches_scan_ptr_ok:
    clc
    rts

advance_scan_ptr_by_const_ptr:
    ldy #$00
advance_scan_ptr_by_const_ptr_loop:
    lda (const_ptr),y
    beq advance_scan_ptr_by_const_ptr_done
    jsr advance_scan_ptr
    iny
    bne advance_scan_ptr_by_const_ptr_loop
advance_scan_ptr_by_const_ptr_done:
    rts

.include "direct_prg.inc"
.include "debug_sidecar.inc"


append_payload_byte:
    tax
    tya
    pha
    lda main_flags_hi
    cmp #$ff
    bne :+
    lda main_flags_lo
    cmp #$ff
    beq append_payload_byte_fail
:   ldy output_chunk_len
    txa
    sta content_buffer,y
    inc output_chunk_len
    lda output_chunk_len
    cmp #OUTPUT_CHUNK_SIZE
    bcc :+
    jsr flush_output_stream_or_fail
:   inc main_flags_lo
    bne :+
    inc main_flags_hi
:   pla
    tay
    rts
append_payload_byte_fail:
    pla
    tay
    lda #<msg_too_large
    ldy #>msg_too_large
    jmp fail_with_ptr



lowercase_ascii:
    cmp #'A'
    bcc lowercase_ascii_done
    cmp #'Z'+1
    bcs lowercase_ascii_done
    ora #$20
lowercase_ascii_done:
    rts

build_library_object_target_path:
    lda #'L'
    sta target_path+0
    lda #'I'
    sta target_path+1
    lda #'B'
    sta target_path+2
    lda #'/'
    sta target_path+3
    ldy #$00
build_library_object_target_path_loop:
    lda module_name,y
    beq build_library_object_target_path_suffix
    jsr normalize_module_arg_char
    sta target_path+4,y
    iny
    bne build_library_object_target_path_loop
build_library_object_target_path_suffix:
    lda #'.'
    sta target_path+4,y
    iny
    lda #'O'
    sta target_path+4,y
    iny
    lda #'B'
    sta target_path+4,y
    iny
    lda #'J'
    sta target_path+4,y
    iny
    lda #$00
    sta target_path+4,y
    rts

build_binary_save_target_path:
    lda #'B'
    sta target_path+0
    lda #'I'
    sta target_path+1
    lda #'N'
    sta target_path+2
    lda #'/'
    sta target_path+3
    ldy #$00
build_binary_save_target_path_loop:
    lda module_name,y
    beq build_binary_save_target_path_suffix
    sta target_path+4,y
    iny
    bne build_binary_save_target_path_loop
build_binary_save_target_path_suffix:
    lda #'.'
    sta target_path+4,y
    iny
    lda #'P'
    sta target_path+4,y
    iny
    lda #'R'
    sta target_path+4,y
    iny
    lda #'G'
    sta target_path+4,y
    iny
    lda #$00
    sta target_path+4,y
    rts

copy_target_path_to_binary_target_path:
    ldx #$00
copy_target_path_to_binary_target_path_loop:
    lda target_path,x
    sta binary_target_path,x
    beq copy_target_path_to_binary_target_path_done
    inx
    cpx #40
    bcc copy_target_path_to_binary_target_path_loop
copy_target_path_to_binary_target_path_done:
    rts

save_source_buffer_to_target:
    lda #$C2
    sta binary_target_path+16
    lda #$00
    jsr flush_output_stream_or_fail
    jsr close_output_stream
    bcc save_source_buffer_to_target_ok
    sec
    rts
save_source_buffer_to_target_ok:
    clc
    rts

open_output_stream_to_target_or_fail:
    lda #$00
    sta output_chunk_len
    lda #<target_path
    sta file_params+0
    lda #>target_path
    sta file_params+1
    lda #tool_file_status_fail
    sta file_params+2
    ldx #file_params
    jsr alink_svc_file_write_begin_sc0
    lda file_params+2
    cmp #tool_file_status_ok
    beq open_output_stream_to_target_ok
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
open_output_stream_to_target_ok:
    clc
    rts

flush_output_stream_or_fail:
    lda output_chunk_len
    beq flush_output_stream_done
    lda #<content_buffer
    sta file_params+0
    lda #>content_buffer
    sta file_params+1
    lda output_chunk_len
    sta file_params+2
    lda #$00
    sta file_params+3
    lda #tool_file_status_fail
    sta file_params+4
    ldx #file_params
    jsr alink_svc_file_write_chunk_sc0
    lda file_params+4
    cmp #tool_file_status_ok
    beq flush_output_stream_ok
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
flush_output_stream_ok:
    lda #$00
    sta output_chunk_len
flush_output_stream_done:
    clc
    rts

close_output_stream:
    lda #tool_file_status_fail
    sta file_params+0
    ldx #file_params
    jsr alink_svc_file_write_close_sc0
    lda file_params+0
    cmp #tool_file_status_ok
    beq close_output_stream_ok
    sec
    rts
close_output_stream_ok:
    clc
    rts

alink_save_zp_state:
    ldx #$00
alink_save_zp_state_loop:
    lda $00E0,x
    sta alink_zp_save,x
    inx
    cpx #$0F
    bcc alink_save_zp_state_loop
    rts

alink_restore_zp_state:
    ldx #$00
alink_restore_zp_state_loop:
    lda alink_zp_save,x
    sta $00E0,x
    inx
    cpx #$0F
    bcc alink_restore_zp_state_loop
    rts

alink_restore_service_status:
    lda alink_service_status
    pha
    plp
    rts

alink_svc_program_get_cmdline_len:
    jsr alink_save_zp_state
    ldx #svc_retptr
    jsr svc_program_get_cmdline_len
    php
    pla
    sta alink_service_status
    lda svc_retptr
    sta alink_service_out+0
    lda svc_retptr+1
    sta alink_service_out+1
    jsr alink_restore_zp_state
    lda alink_service_out+0
    sta svc_retptr
    lda alink_service_out+1
    sta svc_retptr+1
    jmp alink_restore_service_status

alink_svc_program_get_cmdline_ptr:
    jsr alink_save_zp_state
    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    php
    pla
    sta alink_service_status
    lda svc_retptr
    sta alink_service_out+0
    lda svc_retptr+1
    sta alink_service_out+1
    jsr alink_restore_zp_state
    lda alink_service_out+0
    sta svc_retptr
    lda alink_service_out+1
    sta svc_retptr+1
    jmp alink_restore_service_status

alink_svc_file_load_sc0:
    jsr alink_save_zp_state
    lda alink_zp_save+2
    sta TOOL_ABI_FILE_NAME_LO
    lda alink_zp_save+3
    sta TOOL_ABI_FILE_NAME_HI
    lda #$00
    sta alink_service_out+0
    sta alink_service_out+1
    sta alink_service_out+2
    jsr svc_open_program_read_path_preserved
    bcc alink_svc_file_load_open_ok
    lda #tool_file_status_nofile
    sta alink_service_out+0
    jmp alink_svc_file_load_fail_flags
alink_svc_file_load_open_ok:
    lda alink_zp_save+4
    ora alink_zp_save+5
    ora alink_zp_save+6
    ora alink_zp_save+7
    bne alink_svc_file_load_has_dest
    lda #tool_file_status_ok
    sta alink_service_out+0
    jsr alink_close_current_file
    jmp alink_svc_file_load_success_flags
alink_svc_file_load_has_dest:
    jsr alink_svc_file_load_prepare_dest
alink_svc_file_load_read_loop:
    lda alink_service_out+2
    cmp alink_zp_save+7
    bcc alink_svc_file_load_read_byte
    bne alink_svc_file_load_too_large
    lda alink_service_out+1
    cmp alink_zp_save+6
    bcc alink_svc_file_load_read_byte
alink_svc_file_load_too_large:
    lda #tool_file_status_too_large
    sta alink_service_out+0
    jsr alink_close_current_file
    jmp alink_svc_file_load_success_flags
alink_svc_file_load_read_byte:
    jsr CHRIN
    ldy #$00
    sta (svc_retptr),y
    inc svc_retptr
    bne :+
    inc svc_retptr+1
:
    inc alink_service_out+1
    bne :+
    inc alink_service_out+2
:
    jsr READST
    and #$40
    beq alink_svc_file_load_read_loop
    lda #tool_file_status_ok
    sta alink_service_out+0
    jsr alink_close_current_file
    jmp alink_svc_file_load_success_flags

alink_close_current_file:
    jsr CLRCHN
    lda #VICE_LFN_FILE
    jmp CLOSE_K

alink_svc_file_load_prepare_dest:
    lda alink_zp_save+4
    sta svc_retptr
    lda alink_zp_save+5
    sta svc_retptr+1
    rts
alink_svc_file_load_fail_flags:
    sec
    php
    pla
    sta alink_service_status
    jmp alink_svc_file_load_done
alink_svc_file_load_success_flags:
    clc
    php
    pla
    sta alink_service_status
alink_svc_file_load_done:
    jsr alink_restore_zp_state
    lda alink_service_out+0
    sta file_params+6
    lda alink_service_out+1
    sta file_params+7
    lda alink_service_out+2
    sta file_params+8
    jmp alink_restore_service_status

alink_svc_file_stage_reu_sc0:
    jsr alink_save_zp_state
    ldx #file_params
    jsr svc_file_stage_reu_sc0
    php
    pla
    sta alink_service_status
    lda file_params+5
    sta alink_service_out+0
    lda file_params+6
    sta alink_service_out+1
    lda file_params+7
    sta alink_service_out+2
    lda file_params+8
    sta alink_service_out+3
    jsr alink_restore_zp_state
    lda alink_service_out+0
    sta file_params+5
    lda alink_service_out+1
    sta file_params+6
    lda alink_service_out+2
    sta file_params+7
    lda alink_service_out+3
    sta file_params+8
    jmp alink_restore_service_status

alink_svc_reu_read_sc0:
    jsr alink_save_zp_state
    ldx #file_params
    jsr svc_reu_read_sc0
    jmp alink_restore_reu_result

alink_svc_reu_write_sc0:
    jsr alink_save_zp_state
    ldx #file_params
    jsr svc_reu_write_sc0
alink_restore_reu_result:
    php
    pla
    sta alink_service_status
    lda file_params+7
    sta alink_service_out+0
    jsr alink_restore_zp_state
    lda alink_service_out+0
    sta file_params+7
    jmp alink_restore_service_status

alink_svc_file_write_begin_sc0:
    jsr alink_save_zp_state
    ldx #file_params
    jsr svc_file_write_begin_sc0
    php
    pla
    sta alink_service_status
    lda file_params+2
    sta alink_service_out+0
    jsr alink_restore_zp_state
    lda alink_service_out+0
    sta file_params+2
    jmp alink_restore_service_status

alink_svc_file_write_chunk_sc0:
    jsr alink_save_zp_state
    ldx #file_params
    jsr svc_file_write_chunk_sc0
    php
    pla
    sta alink_service_status
    lda file_params+4
    sta alink_service_out+0
    jsr alink_restore_zp_state
    lda alink_service_out+0
    sta file_params+4
    jmp alink_restore_service_status

alink_svc_file_write_close_sc0:
    jsr alink_save_zp_state
    ldx #file_params
    jsr svc_file_write_close_sc0
    php
    pla
    sta alink_service_status
    lda file_params+0
    sta alink_service_out+0
    jsr alink_restore_zp_state
    lda alink_service_out+0
    sta file_params+0
    jmp alink_restore_service_status

alink_svc_file_delete_sc0:
    jsr alink_save_zp_state
    ldx #file_params
    jsr svc_file_delete_sc0
    php
    pla
    sta alink_service_status
    lda file_params+2
    sta alink_service_out+0
    jsr alink_restore_zp_state
    lda alink_service_out+0
    sta file_params+2
    jmp alink_restore_service_status

snapshot_bad_object_state:
    ldx #$00
snapshot_bad_object_source_loop:
    lda source_buffer,x
    sta $03D0,x
    sta $CFD0,x
    inx
    cpx #$10
    bcc snapshot_bad_object_source_loop
    ldx #$00
snapshot_bad_object_target_loop:
    lda target_path,x
    sta $03E0,x
    sta $CFC0,x
    inx
    cpx #$10
    bcc snapshot_bad_object_target_loop
    rts

.include "../common/action_project_module_arg.inc"
.include "../common/action_project_load.inc"
.include "../common/action_project_load_guard.inc"
.include "../common/action_project_entry.inc"
.include "../common/action_project_entry_guard.inc"
.include "../common/action_project_object_path.inc"
.include "../common/action_project_path.inc"
.include "../common/action_project_save_mode.inc"
.include "../common/action_project_source.inc"

print_line_ptr:
    jsr print_ptr
    lda #13
    jmp CHROUT

fail_with_ptr:
    sta svc_retptr
    sty svc_retptr+1
    tsx
    stx $03FF
    lda svc_retptr
    sta $03F8
    lda svc_retptr+1
    sta $03F9
    ldy #$00
fail_with_ptr_snapshot_loop:
    lda (svc_retptr),y
    sta $03D0,y
    beq fail_with_ptr_snapshot_done
    iny
    cpy #$10
    bcc fail_with_ptr_snapshot_loop
fail_with_ptr_snapshot_done:
    lda #$00
    sta $03D0,y
    lda svc_retptr
    cmp #<msg_save_fail
    bne fail_with_ptr_snapshot_meta
    lda svc_retptr+1
    cmp #>msg_save_fail
    bne fail_with_ptr_snapshot_meta
    ldx #$00
fail_with_ptr_save_target_loop:
    lda target_path,x
    sta $03E0,x
    beq fail_with_ptr_snapshot_meta
    inx
    cpx #$10
    bcc fail_with_ptr_save_target_loop
fail_with_ptr_snapshot_meta:
    lda debug_phase_zp
    sta $03FD
    lda debug_phase
    sta $03FE
    lda svc_retptr
    ldy svc_retptr+1
    jsr print_line_ptr
    lda #$01
    sta svc_retptr
    lda #$00
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

print_ptr:
    sta svc_retptr
    sty svc_retptr+1
    ldy #$00
print_ptr_loop:
    lda (svc_retptr),y
    beq print_ptr_done
    jsr CHROUT
    iny
    bne print_ptr_loop
print_ptr_done:
    rts

msg_bad_name:
    .asciiz "BAD NAME"
msg_no_project:
    .asciiz "NO PROJECT"
msg_not_in_project:
    .asciiz "NOT IN PROJECT"
msg_no_object:
    .asciiz "NO OBJECT"
msg_probe_fail:
    .asciiz "PROBE FAIL"
msg_load_fail:
    .asciiz "LOAD FAIL"
msg_save_fail:
    .asciiz "SAVE FAIL"
msg_chain_fail:
    .asciiz "CHAIN FAIL"
msg_bad_object:
    .asciiz "BAD OBJECT"
msg_too_large:
    .asciiz "TOO LARGE"
msg_unsupported_body:
    .asciiz "UNSUPPORTED BODY"
msg_created:
    .asciiz "CREATED"
msg_updated:
    .asciiz "UPDATED"
msg_ok:
    .asciiz "ALINK OK"

actdbg_command_prefix:
    .asciiz "ACTDBG "

default_module_name:
    .asciiz "MAIN"
project_marker:
    .asciiz "ACTION.PROJ"

line_import_mask:
    .byte "k ",0
line_export:
    .byte "x ",0
line_body:
    .byte "b ",0
line_external:
    .byte "u ",0
line_string:
    .byte "s ",0
line_int:
    .byte "i ",0
line_var:
    .byte "v ",0
line_machine_code:
    .byte "m ",0
line_reloc:
    .byte "r ",0

bit_masks:
    .byte $01,$02,$04,$08,$10,$20,$40,$80

module_name:
    .res 25
alink_chain_mode:
    .res 1
target_path_pad:
    .res $0000
target_path:
    .res 40
binary_target_path:
    .res 40
saved_module_name:
    .res 25

.segment "BSS"

source_buffer_pad:
    .res $0000
source_buffer:
.if ACTC_REU_SOURCE_CACHE
    .res SOURCE_READ_LIMIT+1
.else
    .res SOURCE_LIMIT+1
.endif
manifest_buffer = source_buffer
content_buffer_pad:
    .res $0010
content_buffer:
    .res OUTPUT_CHUNK_SIZE
output_chunk_len:
    .res 1
export_name_window:
    .res EXPORT_NAME_BYTES
export_meta_window:
    .res EXPORT_META_BYTES
var_name_window:
    .res VAR_NAME_BYTES
var_meta_window:
    .res VAR_META_BYTES
var_count:
    .res 1
export_layout_window:
    .res EXPORT_LAYOUT_BYTES
var_layout_window:
    .res VAR_LAYOUT_BYTES
string_literal_window:
    .res STRING_LITERAL_ENTRY_BYTES
string_count:
    .res 1
saved_string_count:
    .res 1
source_total_len:
    .res 3
source_window_next_offset:
    .res 3
source_window_len:
    .res 2
source_window_read_len:
    .res 2
source_window_end_ptr:
    .res 2
source_window_valid:
    .res 1
alink_source_direct_cached:
    .res 1
prg_build_strategy:
    .res 1
save_mode:
    .res 1
export_index_zp:
    .res 1
compare_char:
    .res 1
current_bit_lo:
    .res 1
current_bit_hi:
    .res 1
main_flags_lo:
    .res 1
main_flags_hi:
    .res 1
pending_active_index:
    .res 1
debug_phase:
    .res 1
saved_pending_index:
    .res 1
saved_export_count:
    .res 1
saved_state_lo:
    .res 1
saved_state_hi:
    .res 1
parse_word_temp_lo:
    .res 1
parse_word_temp_hi:
    .res 1
truncated_flag:
    .res 1
debug_phase_zp:
    .res 1
alink_service_status:
    .res 1
alink_service_out:
    .res 4
alink_zp_save:
    .res 15
debug_sp_before_strings:
    .res 1
debug_sp_after_strings:
    .res 1
payload_bytes_data:
    .res 1
payload_bytes_data_hi:
    .res 1
code_limit_data:
    .res 1
code_limit_data_hi:
    .res 1
entry_export_index:
    .res 1
root_entry_export_index:
    .res 1
string_layout_window:
    .res STRING_LAYOUT_BYTES
loop_layout_window:
    .res LOOP_LAYOUT_BYTES
live_flag_window:
    .res LIVE_FLAG_BYTES
string_use_mask:
    .res STRING_MASK_BYTES
saved_string_use_mask:
    .res STRING_MASK_BYTES
body_ops_window:
    .res BODY_OPS_STRIDE
manifest_entry:
    .res 32
external_name_window:
    .res EXTERNAL_NAME_BYTES
external_count:
    .res 1
pending_name_window:
    .res PENDING_NAME_BYTES
pending_meta_window:
    .res PENDING_META_BYTES
linked_store_value:
    .res 1
linked_store_value_hi:
    .res 1
linked_machine_byte:
    .res 1
linked_binary_rhs_value:
    .res 1
linked_next_addr_lo:
    .res 1
linked_next_addr_hi:
    .res 1
linked_object_index:
    .res 1
current_object_addr_lo:
    .res 1
current_object_addr_hi:
    .res 1
current_object_export_start_lo:
    .res 1
current_object_export_start_hi:
    .res 1
current_object_export_end_lo:
    .res 1
current_object_export_end_hi:
    .res 1
linked_import_index:
    .res 1
linked_external_index:
    .res 1
linked_reloc_count:
    .res 1
linked_reloc_cursor_consumed:
    .res 1
linked_reloc_cursor_valid:
    .res 1
linked_reloc_cursor_advance:
    .res 1
linked_reloc_previous_lo:
    .res 1
linked_reloc_previous_hi:
    .res 1
linked_reloc_previous_kind:
    .res 1
linked_reloc_kind:
    .res 1
linked_reloc_addend_lo:
    .res 1
linked_reloc_addend_hi:
    .res 1
linked_reloc_addend_negative:
    .res 1
linked_reloc_cursor_window:
    .res RELOC_RECORD_BYTES
linked_reloc_saved_scan_lo:
    .res 1
linked_reloc_saved_scan_hi:
    .res 1
linked_reloc_saved_scan_bank:
    .res 1
linked_reloc_saved_scan_abs:
    .res 1
reloc_record_window:
    .res RELOC_RECORD_BYTES
string_mask_saved_x:
    .res 1
string_mask_saved_bit:
    .res 1
string_mask_saved_y:
    .res 1
symbol_buffer:
    .res 25
int_value_window:
    .res INT_VALUE_BYTES
int_count:
    .res 1
bss_end:
