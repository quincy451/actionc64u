.include "udos_services.inc"
.include "actc_overlay_abi.inc"

.export start
.export actc_overlay_run_pass
.export actc_overlay_run_noop

MANIFEST_LIMIT = 191
.ifndef ACTC_REU_SOURCE_CACHE
ACTC_REU_SOURCE_CACHE = 0
.endif
.ifndef ACTC_USE_DECL_OVERLAY
ACTC_USE_DECL_OVERLAY = 0
.endif
.ifndef ACTC_USE_SOURCE_HEADER_OVERLAY
ACTC_USE_SOURCE_HEADER_OVERLAY = 0
.endif
.ifndef ACTC_USE_LAYOUT_OVERLAY
ACTC_USE_LAYOUT_OVERLAY = 0
.endif
.ifndef ACTC_USE_IMPORT_OVERLAY
ACTC_USE_IMPORT_OVERLAY = 0
.endif
.ifndef ACTC_USE_EMIT_OVERLAY
ACTC_USE_EMIT_OVERLAY = 0
.endif
.ifndef ACTC_USE_BODY_OVERLAY
ACTC_USE_BODY_OVERLAY = 0
.endif
.ifndef ACTC_KEEP_SOURCE_HEADER_RESIDENT_FALLBACK
.if ACTC_USE_SOURCE_HEADER_OVERLAY
    .if ACTC_REU_SOURCE_CACHE
ACTC_KEEP_SOURCE_HEADER_RESIDENT_FALLBACK = 0
    .else
ACTC_KEEP_SOURCE_HEADER_RESIDENT_FALLBACK = 1
    .endif
.else
ACTC_KEEP_SOURCE_HEADER_RESIDENT_FALLBACK = 1
.endif
.endif
.ifndef ACTC_KEEP_DECL_RESIDENT_FALLBACK
.if ACTC_USE_DECL_OVERLAY
    .if ACTC_REU_SOURCE_CACHE
ACTC_KEEP_DECL_RESIDENT_FALLBACK = 0
    .else
ACTC_KEEP_DECL_RESIDENT_FALLBACK = 1
    .endif
.else
ACTC_KEEP_DECL_RESIDENT_FALLBACK = 1
.endif
.endif
.ifndef ACTC_REU_TABLES
ACTC_REU_TABLES = 1
.endif
.ifndef ACTC_REU_BODY_OPS
ACTC_REU_BODY_OPS = ACTC_REU_TABLES
.endif
.ifndef ACTC_REU_STRING_LITERALS
ACTC_REU_STRING_LITERALS = ACTC_REU_TABLES
.endif
.ifndef ACTC_REU_VAR_NAMES
ACTC_REU_VAR_NAMES = ACTC_REU_TABLES
.endif
.ifndef ACTC_REU_EXPORT_NAMES
ACTC_REU_EXPORT_NAMES = ACTC_REU_TABLES
.endif
.ifndef ACTC_REU_INT_LITERALS
ACTC_REU_INT_LITERALS = ACTC_REU_TABLES
.endif
.ifndef ACTC_REU_VAR_META
ACTC_REU_VAR_META = ACTC_REU_TABLES
.endif
.ifndef ACTC_REU_PROC_META
ACTC_REU_PROC_META = ACTC_REU_TABLES
.endif
.ifndef ACTC_REU_PROC_DEBUG
ACTC_REU_PROC_DEBUG = ACTC_REU_TABLES
.endif
.ifndef ACTC_REU_BODY_DEBUG
ACTC_REU_BODY_DEBUG = ACTC_REU_PROC_DEBUG
.endif
.ifndef ACTC_REU_VAR_DEBUG
ACTC_REU_VAR_DEBUG = ACTC_REU_PROC_DEBUG
.endif
.ifndef ACTC_REU_LAYOUT_META
ACTC_REU_LAYOUT_META = ACTC_REU_TABLES
.endif
.ifndef ACTC_REU_STRING_OFFSETS
ACTC_REU_STRING_OFFSETS = ACTC_REU_TABLES
.endif
.ifndef ACTC_KEEP_LAYOUT_RESIDENT_FALLBACK
.if ACTC_USE_LAYOUT_OVERLAY
    .if ACTC_REU_LAYOUT_META
        .if ACTC_REU_STRING_OFFSETS
ACTC_KEEP_LAYOUT_RESIDENT_FALLBACK = 0
        .else
ACTC_KEEP_LAYOUT_RESIDENT_FALLBACK = 1
        .endif
    .else
ACTC_KEEP_LAYOUT_RESIDENT_FALLBACK = 1
    .endif
.else
ACTC_KEEP_LAYOUT_RESIDENT_FALLBACK = 1
.endif
.endif
.ifndef ACTC_KEEP_IMPORT_RESIDENT_FALLBACK
.if ACTC_USE_IMPORT_OVERLAY
ACTC_KEEP_IMPORT_RESIDENT_FALLBACK = 0
.else
ACTC_KEEP_IMPORT_RESIDENT_FALLBACK = 1
.endif
.endif
.ifndef ACTC_KEEP_EMIT_RESIDENT_FALLBACK
.if ACTC_USE_EMIT_OVERLAY
    .if STREAM_OUTPUT
        .if ACTC_REU_LAYOUT_META
            .if ACTC_REU_VAR_META
                .if ACTC_REU_INT_LITERALS
ACTC_KEEP_EMIT_RESIDENT_FALLBACK = 0
                .else
ACTC_KEEP_EMIT_RESIDENT_FALLBACK = 1
                .endif
            .else
ACTC_KEEP_EMIT_RESIDENT_FALLBACK = 1
            .endif
        .else
ACTC_KEEP_EMIT_RESIDENT_FALLBACK = 1
        .endif
    .else
ACTC_KEEP_EMIT_RESIDENT_FALLBACK = 1
    .endif
.else
ACTC_KEEP_EMIT_RESIDENT_FALLBACK = 1
.endif
.endif
.ifndef ACTC_KEEP_BODY_RESIDENT_FALLBACK
.if ACTC_USE_BODY_OVERLAY
ACTC_KEEP_BODY_RESIDENT_FALLBACK = 0
.else
ACTC_KEEP_BODY_RESIDENT_FALLBACK = 1
.endif
.endif
.ifndef ACTC_TABLE_REU_BASE_LO
ACTC_TABLE_REU_BASE_LO = $00
.endif
.ifndef ACTC_TABLE_REU_BASE_HI
ACTC_TABLE_REU_BASE_HI = $C0
.endif
.ifndef ACTC_TABLE_REU_BASE_BANK
ACTC_TABLE_REU_BASE_BANK = $00
.endif
.ifndef ACTC_BODY_OPS_REU_BASE_LO
ACTC_BODY_OPS_REU_BASE_LO = $00
.endif
.ifndef ACTC_BODY_OPS_REU_BASE_HI
ACTC_BODY_OPS_REU_BASE_HI = $D0
.endif
.ifndef ACTC_BODY_OPS_REU_BASE_BANK
ACTC_BODY_OPS_REU_BASE_BANK = $00
.endif
.ifndef ACTC_STRING_REU_BASE_LO
ACTC_STRING_REU_BASE_LO = $00
.endif
.ifndef ACTC_STRING_REU_BASE_HI
ACTC_STRING_REU_BASE_HI = $E0
.endif
.ifndef ACTC_STRING_REU_BASE_BANK
ACTC_STRING_REU_BASE_BANK = $00
.endif
.ifndef ACTC_VAR_REU_BASE_LO
ACTC_VAR_REU_BASE_LO = $00
.endif
.ifndef ACTC_VAR_REU_BASE_HI
ACTC_VAR_REU_BASE_HI = $E4
.endif
.ifndef ACTC_VAR_REU_BASE_BANK
ACTC_VAR_REU_BASE_BANK = $00
.endif
.ifndef ACTC_EXPORT_REU_BASE_LO
ACTC_EXPORT_REU_BASE_LO = $00
.endif
.ifndef ACTC_EXPORT_REU_BASE_HI
ACTC_EXPORT_REU_BASE_HI = $E6
.endif
.ifndef ACTC_EXPORT_REU_BASE_BANK
ACTC_EXPORT_REU_BASE_BANK = $00
.endif
.ifndef ACTC_INT_REU_BASE_LO
ACTC_INT_REU_BASE_LO = $00
.endif
.ifndef ACTC_INT_REU_BASE_HI
ACTC_INT_REU_BASE_HI = $E8
.endif
.ifndef ACTC_INT_REU_BASE_BANK
ACTC_INT_REU_BASE_BANK = $00
.endif
.ifndef ACTC_VAR_META_REU_BASE_LO
ACTC_VAR_META_REU_BASE_LO = $00
.endif
.ifndef ACTC_VAR_META_REU_BASE_HI
ACTC_VAR_META_REU_BASE_HI = $E9
.endif
.ifndef ACTC_VAR_META_REU_BASE_BANK
ACTC_VAR_META_REU_BASE_BANK = $00
.endif
.ifndef ACTC_PROC_META_REU_BASE_LO
ACTC_PROC_META_REU_BASE_LO = $00
.endif
.ifndef ACTC_PROC_META_REU_BASE_HI
ACTC_PROC_META_REU_BASE_HI = $EA
.endif
.ifndef ACTC_PROC_META_REU_BASE_BANK
ACTC_PROC_META_REU_BASE_BANK = $00
.endif
.ifndef ACTC_LAYOUT_REU_BASE_LO
ACTC_LAYOUT_REU_BASE_LO = $00
.endif
.ifndef ACTC_LAYOUT_REU_BASE_HI
ACTC_LAYOUT_REU_BASE_HI = $EB
.endif
.ifndef ACTC_LAYOUT_REU_BASE_BANK
ACTC_LAYOUT_REU_BASE_BANK = $00
.endif
.ifndef ACTC_STRING_OFFSET_REU_BASE_LO
ACTC_STRING_OFFSET_REU_BASE_LO = $00
.endif
.ifndef ACTC_STRING_OFFSET_REU_BASE_HI
ACTC_STRING_OFFSET_REU_BASE_HI = $EC
.endif
.ifndef ACTC_STRING_OFFSET_REU_BASE_BANK
ACTC_STRING_OFFSET_REU_BASE_BANK = $00
.endif
.ifndef ACTC_PROC_DEBUG_REU_BASE_LO
ACTC_PROC_DEBUG_REU_BASE_LO = $00
.endif
.ifndef ACTC_PROC_DEBUG_REU_BASE_HI
ACTC_PROC_DEBUG_REU_BASE_HI = $ED
.endif
.ifndef ACTC_PROC_DEBUG_REU_BASE_BANK
ACTC_PROC_DEBUG_REU_BASE_BANK = $00
.endif
.ifndef ACTC_BODY_DEBUG_REU_BASE_LO
ACTC_BODY_DEBUG_REU_BASE_LO = $00
.endif
.ifndef ACTC_BODY_DEBUG_REU_BASE_HI
ACTC_BODY_DEBUG_REU_BASE_HI = $EE
.endif
.ifndef ACTC_BODY_DEBUG_REU_BASE_BANK
ACTC_BODY_DEBUG_REU_BASE_BANK = $00
.endif
.ifndef ACTC_VAR_DEBUG_REU_BASE_LO
ACTC_VAR_DEBUG_REU_BASE_LO = $00
.endif
.ifndef ACTC_VAR_DEBUG_REU_BASE_HI
ACTC_VAR_DEBUG_REU_BASE_HI = $EF
.endif
.ifndef ACTC_VAR_DEBUG_REU_BASE_BANK
ACTC_VAR_DEBUG_REU_BASE_BANK = $00
.endif
.ifndef ACTC_SOURCE_REU_BASE_LO
ACTC_SOURCE_REU_BASE_LO = $00
.endif
.ifndef ACTC_SOURCE_REU_BASE_HI
ACTC_SOURCE_REU_BASE_HI = $00
.endif
.ifndef ACTC_SOURCE_REU_BASE_BANK
ACTC_SOURCE_REU_BASE_BANK = $01
.endif
.ifndef SOURCE_LIMIT
SOURCE_LIMIT = 255
.endif
.ifndef SOURCE_LOOKAHEAD
SOURCE_LOOKAHEAD = 255
.endif
SOURCE_READ_LIMIT = SOURCE_LIMIT + SOURCE_LOOKAHEAD
PROC_DEBUG_SCAN_CHUNK_SIZE = 64
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
.ifndef LOOP_MAX
LOOP_MAX = 8
.endif
.ifndef CONTENT_BUFFER_SIZE
CONTENT_BUFFER_SIZE = 640
.endif
.ifndef STREAM_OUTPUT
STREAM_OUTPUT = 0
.endif
.ifndef OUTPUT_CHUNK_SIZE
OUTPUT_CHUNK_SIZE = 128
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

IMPORT_PRINT_STR  = $01
IMPORT_PRINT_LINE = $02
IMPORT_FORMAT_INT = $04
ACTC_PERSIST_TRACE = $03E7

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
file_params:
    .res 9
src_ptr:
    .res 2
scan_ptr:
    .res 2
content_ptr:
    .res 2
const_ptr:
    .res 2
import_flags_lo:
    .res 1
truncated_flag:
    .res 1
save_mode:
    .res 1
list_started:
    .res 1
payload_offset:
    .res 1
proc_index:
    .res 1

save_params = file_params

export_index = list_started
export_ptr = src_ptr
body_ptr = src_ptr

.code

start:
    jmp actc_start_main

set_actc_trace:
    sta actc_trace_byte
    sta ACTC_PERSIST_TRACE
    rts

actc_start_main:
    lda #$10
    jsr set_actc_trace
    jsr init_module_name
    lda #$11
    jsr set_actc_trace
    jsr build_manifest_entry
    lda #$12
    jsr set_actc_trace
    jsr require_loaded_project
    lda #$13
    jsr set_actc_trace
    jsr require_manifest_entry_tracked
    lda #$14
    jsr set_actc_trace
    jsr build_target_path
    lda #$15
    jsr set_actc_trace
    jsr load_source_file
    bcc source_loaded
    lda file_params+6
    cmp #tool_file_status_nofile
    beq source_missing
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
source_missing:
    lda #<msg_no_file
    ldy #>msg_no_file
    jmp fail_with_ptr
source_loaded:
    lda #$16
    jsr set_actc_trace
    jsr parse_module_header_or_fail
    lda #$17
    jsr set_actc_trace
    jsr collect_decls_or_fail
    lda #$18
    jsr set_actc_trace
    jsr collect_proc_body_ops
    lda #$19
    jsr set_actc_trace
.if ACTC_REU_BODY_OPS
    ldx #$00
    jsr set_body_ptr_from_x
    lda body_ops_window+0
    sta $03E8
    lda body_ops_window+1
    sta $03E9
    lda body_ops_window+2
    sta $03EA
    lda body_ops_window+3
    sta $03EB
.else
    lda body_ops_data+0
    sta $03E8
    lda body_ops_data+1
    sta $03E9
    lda body_ops_data+2
    sta $03EA
    lda body_ops_data+3
    sta $03EB
	.endif
    jsr detect_runtime_imports
    lda #$1A
    jsr set_actc_trace
    jsr compute_payload_layout
    lda #$1B
    jsr set_actc_trace
    jsr build_object_target_path
    lda #$1C
    jsr set_actc_trace
.if STREAM_OUTPUT
    jsr open_output_stream_to_target_or_fail
    lda #$1D
    jsr set_actc_trace
    jsr build_object_content
    lda #$1E
    jsr set_actc_trace
    jsr flush_output_stream_or_fail
    lda #$22
    jsr set_actc_trace
    jsr close_output_stream
    lda #$20
    jsr set_actc_trace
    bcc save_ok
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
.else
    jsr build_object_content
    lda #$01
    sta save_mode
    lda #$1F
    jsr set_actc_trace
    jmp save_and_exit_clean_stack
.endif

save_ok:
    lda #$21
    jsr set_actc_trace
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

scrub_unused_stack_before_save:
    tsx
    stx save_stack_top
    lda #$00
    ldx #$00
scrub_unused_stack_before_save_loop:
    cpx save_stack_top
    bcs scrub_unused_stack_before_save_done
    sta $0100,x
    inx
    bne scrub_unused_stack_before_save_loop
scrub_unused_stack_before_save_done:
    rts

clear_post_build_state:
    lda #$00
    sta src_ptr
    sta src_ptr+1
    sta scan_ptr
    sta scan_ptr+1
    sta content_ptr
    sta content_ptr+1
    sta const_ptr
    sta const_ptr+1
    sta import_flags_lo
    sta truncated_flag
    sta save_mode
    sta list_started
    sta payload_offset
    sta proc_index
    sta current_proc_index_data
    rts

save_and_exit_clean_stack:
    jsr save_content_buffer_to_target
    lda #$20
    jsr set_actc_trace
    bcc save_ok
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr

actc_overlay_run_noop:
    lda #ACTC_OVERLAY_PASS_NOOP
    jmp actc_overlay_run_pass

actc_overlay_run_pass:
    sta actc_overlay_requested_pass
    jsr actc_overlay_init_context
    jsr actc_overlay_find_pass_descriptor
    bcc :+
    lda #ACTC_OVERLAY_STATUS_UNSUPPORTED_ABI
    sec
    rts
:
    jsr actc_overlay_stage_selected_to_reu
    bcc :+
    lda #ACTC_OVERLAY_STATUS_FAILED
    sec
    rts
:
    jsr actc_overlay_copy_staged_to_exec
    bcc :+
    lda #ACTC_OVERLAY_STATUS_FAILED
    sec
    rts
:
    jsr actc_overlay_validate_selected
    bcc :+
    lda #ACTC_OVERLAY_STATUS_UNSUPPORTED_ABI
    sec
    rts
:
    jmp actc_overlay_call_exec

actc_overlay_init_context:
    lda #$00
    ldx #$00
actc_overlay_init_context_loop:
    sta actc_overlay_context,x
    inx
    cpx #ACTC_OVERLAY_CTX_SIZE
    bcc actc_overlay_init_context_loop
    lda actc_overlay_requested_pass
    sta actc_overlay_context+ACTC_OVERLAY_CTX_PASS_ID
    lda #ACTC_OVERLAY_STATUS_FAILED
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STATUS
    lda #ACTC_SOURCE_REU_BASE_LO
    sta actc_overlay_context+ACTC_OVERLAY_CTX_INPUT_BASE_LO
    lda #ACTC_SOURCE_REU_BASE_HI
    sta actc_overlay_context+ACTC_OVERLAY_CTX_INPUT_BASE_HI
    lda #ACTC_SOURCE_REU_BASE_BANK
    sta actc_overlay_context+ACTC_OVERLAY_CTX_INPUT_BASE_BANK
    lda #<source_buffer
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SOURCE_WINDOW_PTR_LO
    lda #>source_buffer
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SOURCE_WINDOW_PTR_HI
    lda source_window_len
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SOURCE_WINDOW_LEN_LO
    lda source_window_len+1
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SOURCE_WINDOW_LEN_HI
    lda source_total_len
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SOURCE_TOTAL_LEN_LO
    lda source_total_len+1
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SOURCE_TOTAL_LEN_HI
    lda source_total_len+2
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SOURCE_TOTAL_LEN_BANK
    lda #<module_name
    sta actc_overlay_context+ACTC_OVERLAY_CTX_MODULE_NAME_PTR_LO
    lda #>module_name
    sta actc_overlay_context+ACTC_OVERLAY_CTX_MODULE_NAME_PTR_HI
    lda #<var_count_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_VAR_COUNT_PTR_LO
    lda #>var_count_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_VAR_COUNT_PTR_HI
    lda #<module_var_count_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_MODULE_VAR_COUNT_PTR_LO
    lda #>module_var_count_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_MODULE_VAR_COUNT_PTR_HI
    lda #<export_count_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_LO
    lda #>export_count_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_EXPORT_COUNT_PTR_HI
    lda #<string_count_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STRING_COUNT_PTR_LO
    lda #>string_count_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STRING_COUNT_PTR_HI
    lda #<body_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_BODY_PTR_SLOT_PTR_LO
    lda #>body_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_BODY_PTR_SLOT_PTR_HI
    lda #<export_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_EXPORT_PTR_SLOT_PTR_LO
    lda #>export_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_EXPORT_PTR_SLOT_PTR_HI
    lda #<set_body_ptr_from_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_LO
    lda #>set_body_ptr_from_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SET_BODY_PTR_FN_HI
    lda #<set_string_ptr_from_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SET_STRING_PTR_FN_LO
    lda #>set_string_ptr_from_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SET_STRING_PTR_FN_HI
    lda #<int_count_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_INT_COUNT_PTR_LO
    lda #>int_count_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_INT_COUNT_PTR_HI
    lda #<extern_count_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_LO
    lda #>extern_count_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_EXTERN_COUNT_PTR_HI
    lda #<current_proc_index_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_CURRENT_PROC_INDEX_PTR_LO
    lda #>current_proc_index_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_CURRENT_PROC_INDEX_PTR_HI
    lda #<assignment_target_index_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_LO
    lda #>assignment_target_index_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_ASSIGNMENT_TARGET_INDEX_PTR_HI
    lda #<call_target_kind
    sta actc_overlay_context+ACTC_OVERLAY_CTX_CALL_TARGET_KIND_PTR_LO
    lda #>call_target_kind
    sta actc_overlay_context+ACTC_OVERLAY_CTX_CALL_TARGET_KIND_PTR_HI
    lda #<call_target_index_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_CALL_TARGET_INDEX_PTR_LO
    lda #>call_target_index_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_CALL_TARGET_INDEX_PTR_HI
    lda #<scan_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SCAN_PTR_SLOT_PTR_LO
    lda #>scan_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SCAN_PTR_SLOT_PTR_HI
    lda #<set_export_ptr_from_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_LO
    lda #>set_export_ptr_from_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SET_EXPORT_PTR_FN_HI
    lda #<set_external_ptr_from_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SET_EXTERNAL_PTR_FN_LO
    lda #>set_external_ptr_from_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SET_EXTERNAL_PTR_FN_HI
    lda #<set_var_ptr_from_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SET_VAR_PTR_FN_LO
    lda #>set_var_ptr_from_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SET_VAR_PTR_FN_HI
.if ACTC_REU_LAYOUT_META
    lda #<layout_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LAYOUT_WINDOW_PTR_LO
    lda #>layout_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LAYOUT_WINDOW_PTR_HI
    lda #<load_layout_from_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LOAD_LAYOUT_FN_LO
    lda #>load_layout_from_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LOAD_LAYOUT_FN_HI
    lda #<store_layout_to_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_LAYOUT_FN_LO
    lda #>store_layout_to_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_LAYOUT_FN_HI
.endif
.if ACTC_REU_STRING_OFFSETS
    lda #<string_offset_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STRING_OFFSET_PTR_LO
    lda #>string_offset_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STRING_OFFSET_PTR_HI
    lda #<store_string_offset_to_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_STRING_OFFSET_FN_LO
    lda #>store_string_offset_to_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_STRING_OFFSET_FN_HI
.endif
    lda #<const_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_CONST_PTR_SLOT_PTR_LO
    lda #>const_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_CONST_PTR_SLOT_PTR_HI
    lda #<import_flags_lo
    sta actc_overlay_context+ACTC_OVERLAY_CTX_IMPORT_FLAGS_PTR_LO
    lda #>import_flags_lo
    sta actc_overlay_context+ACTC_OVERLAY_CTX_IMPORT_FLAGS_PTR_HI
    lda #<find_pattern_at_const_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_PATTERN_FN_LO
    lda #>find_pattern_at_const_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_PATTERN_FN_HI
.if ACTC_REU_VAR_NAMES
    lda #<var_name_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_VAR_NAME_WINDOW_PTR_LO
    lda #>var_name_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_VAR_NAME_WINDOW_PTR_HI
    lda #<store_var_name_to_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_VAR_NAME_FN_LO
    lda #>store_var_name_to_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_VAR_NAME_FN_HI
.endif
.if ACTC_REU_VAR_META
    lda #<var_meta_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_LO
    lda #>var_meta_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_VAR_META_WINDOW_PTR_HI
    lda #<load_var_meta_from_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LOAD_VAR_META_FN_LO
    lda #>load_var_meta_from_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LOAD_VAR_META_FN_HI
    lda #<store_var_meta_to_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_VAR_META_FN_LO
    lda #>store_var_meta_to_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_VAR_META_FN_HI
.endif
.if ACTC_REU_INT_LITERALS
    lda #<int_literal_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_LO
    lda #>int_literal_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_INT_LITERAL_WINDOW_PTR_HI
    lda #<load_int_literal_from_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_LO
    lda #>load_int_literal_from_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LOAD_INT_LITERAL_FN_HI
.endif
.if STREAM_OUTPUT
    lda #<append_char
    sta actc_overlay_context+ACTC_OVERLAY_CTX_APPEND_CHAR_FN_LO
    lda #>append_char
    sta actc_overlay_context+ACTC_OVERLAY_CTX_APPEND_CHAR_FN_HI
.endif
    lda #<collect_proc_body_ops_overlay_begin
    sta actc_overlay_context+ACTC_OVERLAY_CTX_BEGIN_BODY_SCAN_FN_LO
    lda #>collect_proc_body_ops_overlay_begin
    sta actc_overlay_context+ACTC_OVERLAY_CTX_BEGIN_BODY_SCAN_FN_HI
    lda #<collect_proc_body_ops_overlay_finish
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FINISH_BODY_SCAN_FN_LO
    lda #>collect_proc_body_ops_overlay_finish
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FINISH_BODY_SCAN_FN_HI
    lda #<advance_scan_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_FN_LO
    lda #>advance_scan_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_FN_HI
    lda #<skip_source_spaces
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SKIP_SOURCE_SPACES_FN_LO
    lda #>skip_source_spaces
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SKIP_SOURCE_SPACES_FN_HI
    lda #<pattern_matches_scan_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_PATTERN_MATCHES_SCAN_PTR_FN_LO
    lda #>pattern_matches_scan_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_PATTERN_MATCHES_SCAN_PTR_FN_HI
    lda #<pattern_matches_scan_ptr_keyword
    sta actc_overlay_context+ACTC_OVERLAY_CTX_PATTERN_MATCHES_SCAN_PTR_KEYWORD_FN_LO
    lda #>pattern_matches_scan_ptr_keyword
    sta actc_overlay_context+ACTC_OVERLAY_CTX_PATTERN_MATCHES_SCAN_PTR_KEYWORD_FN_HI
    lda #<match_scalar_decl_at_scan_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_MATCH_SCALAR_DECL_FN_LO
    lda #>match_scalar_decl_at_scan_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_MATCH_SCALAR_DECL_FN_HI
    lda #<advance_scan_ptr_by_const_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_BY_CONST_FN_LO
    lda #>advance_scan_ptr_by_const_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_ADVANCE_SCAN_PTR_BY_CONST_FN_HI
    lda #<copy_symbol_from_scan_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_PTR_FN_LO
    lda #>copy_symbol_from_scan_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_PTR_FN_HI
    lda #<find_current_proc_local_index_from_declared_for_proc_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_CURRENT_PROC_LOCAL_FN_LO
    lda #>find_current_proc_local_index_from_declared_for_proc_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_CURRENT_PROC_LOCAL_FN_HI
    lda #<skip_inline_spaces_at_scan_y
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_LO
    lda #>skip_inline_spaces_at_scan_y
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SKIP_INLINE_SPACES_FN_HI
    lda #<advance_scan_y
    sta actc_overlay_context+ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_LO
    lda #>advance_scan_y
    sta actc_overlay_context+ACTC_OVERLAY_CTX_ADVANCE_SCAN_Y_FN_HI
    lda #<require_var_index_word_or_fail
    sta actc_overlay_context+ACTC_OVERLAY_CTX_REQUIRE_WORD_VAR_FN_LO
    lda #>require_var_index_word_or_fail
    sta actc_overlay_context+ACTC_OVERLAY_CTX_REQUIRE_WORD_VAR_FN_HI
    lda #<require_var_index_real_or_fail
    sta actc_overlay_context+ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_LO
    lda #>require_var_index_real_or_fail
    sta actc_overlay_context+ACTC_OVERLAY_CTX_REQUIRE_REAL_VAR_FN_HI
    lda #<emit_runtime_value_from_scan_y_or_fail
    sta actc_overlay_context+ACTC_OVERLAY_CTX_EMIT_RUNTIME_VALUE_FN_LO
    lda #>emit_runtime_value_from_scan_y_or_fail
    sta actc_overlay_context+ACTC_OVERLAY_CTX_EMIT_RUNTIME_VALUE_FN_HI
    lda #<require_line_end_at_scan_y
    sta actc_overlay_context+ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_LO
    lda #>require_line_end_at_scan_y
    sta actc_overlay_context+ACTC_OVERLAY_CTX_REQUIRE_LINE_END_FN_HI
    lda #<append_body_op_for_current_proc
    sta actc_overlay_context+ACTC_OVERLAY_CTX_APPEND_BODY_OP_FN_LO
    lda #>append_body_op_for_current_proc
    sta actc_overlay_context+ACTC_OVERLAY_CTX_APPEND_BODY_OP_FN_HI
    lda #<append_body_op_no_arg_for_current_proc
    sta actc_overlay_context+ACTC_OVERLAY_CTX_APPEND_BODY_OP_NO_ARG_FN_LO
    lda #>append_body_op_no_arg_for_current_proc
    sta actc_overlay_context+ACTC_OVERLAY_CTX_APPEND_BODY_OP_NO_ARG_FN_HI
    lda #<store_string_literal_from_scan_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_STRING_LITERAL_FN_LO
    lda #>store_string_literal_from_scan_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_STRING_LITERAL_FN_HI
    lda #<store_small_decimal_literal_from_scan_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_SMALL_DECIMAL_LITERAL_FN_LO
    lda #>store_small_decimal_literal_from_scan_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_SMALL_DECIMAL_LITERAL_FN_HI
    lda #<store_zero_int_literal
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_ZERO_INT_LITERAL_FN_LO
    lda #>store_zero_int_literal
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_ZERO_INT_LITERAL_FN_HI
    lda #<parse_small_value_expr_at_scan_y
    sta actc_overlay_context+ACTC_OVERLAY_CTX_PARSE_SMALL_VALUE_EXPR_FN_LO
    lda #>parse_small_value_expr_at_scan_y
    sta actc_overlay_context+ACTC_OVERLAY_CTX_PARSE_SMALL_VALUE_EXPR_FN_HI
    lda #<require_var_index_real_bridge_word_or_fail
    sta actc_overlay_context+ACTC_OVERLAY_CTX_REQUIRE_REAL_BRIDGE_WORD_VAR_FN_LO
    lda #>require_var_index_real_bridge_word_or_fail
    sta actc_overlay_context+ACTC_OVERLAY_CTX_REQUIRE_REAL_BRIDGE_WORD_VAR_FN_HI
    lda #<find_or_store_real_bridge_external_from_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_OR_STORE_REAL_BRIDGE_EXTERNAL_FN_LO
    lda #>find_or_store_real_bridge_external_from_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_OR_STORE_REAL_BRIDGE_EXTERNAL_FN_HI
    lda #<save_source_reader_mark
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_LO
    lda #>save_source_reader_mark
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SAVE_SOURCE_MARK_FN_HI
    lda #<restore_source_reader_mark
    sta actc_overlay_context+ACTC_OVERLAY_CTX_RESTORE_SOURCE_MARK_FN_LO
    lda #>restore_source_reader_mark
    sta actc_overlay_context+ACTC_OVERLAY_CTX_RESTORE_SOURCE_MARK_FN_HI
.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
    lda #<parse_positive_word_sum_at_scan_y
    sta actc_overlay_context+ACTC_OVERLAY_CTX_PARSE_POSITIVE_WORD_SUM_FN_LO
    lda #>parse_positive_word_sum_at_scan_y
    sta actc_overlay_context+ACTC_OVERLAY_CTX_PARSE_POSITIVE_WORD_SUM_FN_HI
.endif
    lda #<store_word_literal_from_ay
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_WORD_LITERAL_FN_LO
    lda #>store_word_literal_from_ay
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_WORD_LITERAL_FN_HI
    lda #<expr_value_lo
    sta actc_overlay_context+ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_LO
    lda #>expr_value_lo
    sta actc_overlay_context+ACTC_OVERLAY_CTX_EXPR_VALUE_PTR_HI
    lda #<find_or_store_rt_i_to_f_external
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_I_TO_F_FN_LO
    lda #>find_or_store_rt_i_to_f_external
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_I_TO_F_FN_HI
    lda #<find_or_store_rt_s_to_f_external
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_S_TO_F_FN_LO
    lda #>find_or_store_rt_s_to_f_external
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_S_TO_F_FN_HI
    lda #<emit_runtime_real_value_from_scan_y_or_fail
    sta actc_overlay_context+ACTC_OVERLAY_CTX_EMIT_RUNTIME_REAL_VALUE_FN_LO
    lda #>emit_runtime_real_value_from_scan_y_or_fail
    sta actc_overlay_context+ACTC_OVERLAY_CTX_EMIT_RUNTIME_REAL_VALUE_FN_HI
    lda #<find_or_store_rt_print_f_external
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_PRINT_F_FN_LO
    lda #>find_or_store_rt_print_f_external
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_PRINT_F_FN_HI
    lda #<find_or_store_rt_f_to_i_external
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_F_TO_I_FN_LO
    lda #>find_or_store_rt_f_to_i_external
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_OR_STORE_RT_F_TO_I_FN_HI
    lda #<copy_symbol_from_scan_y
    sta actc_overlay_context+ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_LO
    lda #>copy_symbol_from_scan_y
    sta actc_overlay_context+ACTC_OVERLAY_CTX_COPY_SYMBOL_FROM_SCAN_Y_FN_HI
    lda #<find_var_index_from_declared
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_LO
    lda #>find_var_index_from_declared
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_VAR_INDEX_FN_HI
    lda #<find_or_store_real_operator_external_from_a
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_OR_STORE_REAL_OPERATOR_EXTERNAL_FN_LO
    lda #>find_or_store_real_operator_external_from_a
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_OR_STORE_REAL_OPERATOR_EXTERNAL_FN_HI
    lda #<resolve_call_target_from_declared_or_fail
    sta actc_overlay_context+ACTC_OVERLAY_CTX_RESOLVE_CALL_TARGET_FN_LO
    lda #>resolve_call_target_from_declared_or_fail
    sta actc_overlay_context+ACTC_OVERLAY_CTX_RESOLVE_CALL_TARGET_FN_HI
    lda #<emit_call_args_from_scan_y_or_fail
    sta actc_overlay_context+ACTC_OVERLAY_CTX_EMIT_CALL_ARGS_FN_LO
    lda #>emit_call_args_from_scan_y_or_fail
    sta actc_overlay_context+ACTC_OVERLAY_CTX_EMIT_CALL_ARGS_FN_HI
    lda #<skip_source_line
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SKIP_SOURCE_LINE_FN_LO
    lda #>skip_source_line
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SKIP_SOURCE_LINE_FN_HI
    lda #<find_export_index_from_declared
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_EXPORT_INDEX_FN_LO
    lda #>find_export_index_from_declared
    sta actc_overlay_context+ACTC_OVERLAY_CTX_FIND_EXPORT_INDEX_FN_HI
.if ACTC_REU_PROC_META
    lda #<load_proc_meta_from_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LOAD_PROC_META_FN_LO
    lda #>load_proc_meta_from_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LOAD_PROC_META_FN_HI
.endif
.if ACTC_REU_EXPORT_NAMES
    lda #<export_name_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_EXPORT_NAME_WINDOW_PTR_LO
    lda #>export_name_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_EXPORT_NAME_WINDOW_PTR_HI
    lda #<store_export_name_to_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_EXPORT_NAME_FN_LO
    lda #>store_export_name_to_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_EXPORT_NAME_FN_HI
.endif
.if ACTC_REU_PROC_META
    lda #<proc_meta_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_PROC_META_WINDOW_PTR_LO
    lda #>proc_meta_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_PROC_META_WINDOW_PTR_HI
    lda #<store_proc_meta_to_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_PROC_META_FN_LO
    lda #>store_proc_meta_to_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_PROC_META_FN_HI
.endif
.if ACTC_REU_PROC_DEBUG
    lda #<proc_debug_offset_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_PROC_DEBUG_OFFSET_WINDOW_PTR_LO
    lda #>proc_debug_offset_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_PROC_DEBUG_OFFSET_WINDOW_PTR_HI
    lda #<store_proc_debug_offset_to_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_PROC_DEBUG_OFFSET_FN_LO
    lda #>store_proc_debug_offset_to_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_PROC_DEBUG_OFFSET_FN_HI
    lda #<proc_debug_linecol_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_PROC_DEBUG_LINECOL_WINDOW_PTR_LO
    lda #>proc_debug_linecol_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_PROC_DEBUG_LINECOL_WINDOW_PTR_HI
    lda #<load_proc_debug_linecol_from_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LOAD_PROC_DEBUG_LINECOL_FN_LO
    lda #>load_proc_debug_linecol_from_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LOAD_PROC_DEBUG_LINECOL_FN_HI
.endif
.if ACTC_REU_BODY_DEBUG
    lda #<body_debug_count_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_BODY_DEBUG_COUNT_PTR_LO
    lda #>body_debug_count_data
    sta actc_overlay_context+ACTC_OVERLAY_CTX_BODY_DEBUG_COUNT_PTR_HI
    lda #<load_body_debug_linecol_from_xy
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LOAD_BODY_DEBUG_LINECOL_FN_LO
    lda #>load_body_debug_linecol_from_xy
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LOAD_BODY_DEBUG_LINECOL_FN_HI
    lda #<store_current_body_debug_mark_from_scan_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_CURRENT_BODY_DEBUG_MARK_FN_LO
    lda #>store_current_body_debug_mark_from_scan_ptr
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_CURRENT_BODY_DEBUG_MARK_FN_HI
.endif
.if ACTC_REU_VAR_DEBUG
    lda #<store_var_debug_offset_to_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_VAR_DEBUG_OFFSET_FN_LO
    lda #>store_var_debug_offset_to_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_STORE_VAR_DEBUG_OFFSET_FN_HI
    lda #<load_var_debug_linecol_from_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LOAD_VAR_DEBUG_LINECOL_FN_LO
    lda #>load_var_debug_linecol_from_reu_x
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LOAD_VAR_DEBUG_LINECOL_FN_HI
.endif
.if ACTC_REU_SOURCE_CACHE
    lda #<actc_overlay_load_next_source_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LOAD_NEXT_SOURCE_WINDOW_FN_LO
    lda #>actc_overlay_load_next_source_window
    sta actc_overlay_context+ACTC_OVERLAY_CTX_LOAD_NEXT_SOURCE_WINDOW_FN_HI
.endif
    rts

actc_overlay_refresh_source_window_context:
    lda #<source_buffer
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SOURCE_WINDOW_PTR_LO
    lda #>source_buffer
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SOURCE_WINDOW_PTR_HI
    lda source_window_len
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SOURCE_WINDOW_LEN_LO
    lda source_window_len+1
    sta actc_overlay_context+ACTC_OVERLAY_CTX_SOURCE_WINDOW_LEN_HI
    rts

actc_overlay_load_next_source_window:
.if ACTC_REU_SOURCE_CACHE
    jsr source_reader_load_next_window
    bcs actc_overlay_load_next_source_window_fail
    jsr actc_overlay_refresh_source_window_context
    clc
    rts
actc_overlay_load_next_source_window_fail:
    sec
    rts
.else
    sec
    rts
.endif

actc_overlay_find_pass_descriptor:
    lda #<actc_overlay_pass_table
    sta const_ptr
    lda #>actc_overlay_pass_table
    sta const_ptr+1
actc_overlay_find_pass_descriptor_loop:
    ldy #ACTC_OVERLAY_DESC_PASS_ID
    lda (const_ptr),y
    cmp #ACTC_OVERLAY_PASS_END
    beq actc_overlay_find_pass_descriptor_fail
    cmp actc_overlay_requested_pass
    beq actc_overlay_find_pass_descriptor_ok
    clc
    lda const_ptr
    adc #ACTC_OVERLAY_DESC_STRIDE
    sta const_ptr
    lda const_ptr+1
    adc #$00
    sta const_ptr+1
    jmp actc_overlay_find_pass_descriptor_loop
actc_overlay_find_pass_descriptor_ok:
    clc
    rts
actc_overlay_find_pass_descriptor_fail:
    sec
    rts

actc_overlay_stage_selected_to_reu:
    ldy #ACTC_OVERLAY_DESC_PATH_LO
    lda (const_ptr),y
    sta file_params+0
    ldy #ACTC_OVERLAY_DESC_PATH_HI
    lda (const_ptr),y
    sta file_params+1
    ldy #ACTC_OVERLAY_DESC_REU_LO
    lda (const_ptr),y
    sta file_params+2
    ldy #ACTC_OVERLAY_DESC_REU_HI
    lda (const_ptr),y
    sta file_params+3
    ldy #ACTC_OVERLAY_DESC_REU_BANK
    lda (const_ptr),y
    sta file_params+4
    lda #$00
    sta file_params+5
    sta file_params+6
    sta file_params+7
    sta file_params+8
    ldx #file_params
    jsr svc_file_stage_reu_sc0
    lda file_params+5
    sta actc_overlay_service_status
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:
    lda file_params+6
    sta actc_overlay_loaded_len
    lda file_params+7
    sta actc_overlay_loaded_len+1
    lda file_params+8
    beq :+
    sec
    rts
:
    lda actc_overlay_loaded_len
    ora actc_overlay_loaded_len+1
    bne :+
    sec
    rts
:
    lda actc_overlay_loaded_len+1
    cmp #>ACTC_OVERLAY_EXEC_SIZE
    bcc actc_overlay_stage_selected_to_reu_ok
    bne actc_overlay_stage_selected_to_reu_too_large
    lda actc_overlay_loaded_len
    beq actc_overlay_stage_selected_to_reu_ok
actc_overlay_stage_selected_to_reu_too_large:
    lda #tool_file_status_too_large
    sta actc_overlay_service_status
    sec
    rts
actc_overlay_stage_selected_to_reu_ok:
    clc
    rts

actc_overlay_copy_staged_to_exec:
    ldy #ACTC_OVERLAY_DESC_REU_LO
    lda (const_ptr),y
    sta file_params+0
    ldy #ACTC_OVERLAY_DESC_REU_HI
    lda (const_ptr),y
    sta file_params+1
    ldy #ACTC_OVERLAY_DESC_REU_BANK
    lda (const_ptr),y
    sta file_params+2
    lda #<ACTC_OVERLAY_EXEC_BASE
    sta file_params+3
    lda #>ACTC_OVERLAY_EXEC_BASE
    sta file_params+4
    lda actc_overlay_loaded_len
    sta file_params+5
    lda actc_overlay_loaded_len+1
    sta file_params+6
    lda #$00
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    sta actc_overlay_service_status
    cmp #tool_file_status_ok
    beq :+
    sec
    rts
:
    clc
    rts

actc_overlay_validate_selected:
    lda ACTC_OVERLAY_EXEC_BASE+0
    cmp #'A'
    bne actc_overlay_validate_selected_fail
    lda ACTC_OVERLAY_EXEC_BASE+1
    cmp #'C'
    bne actc_overlay_validate_selected_fail
    lda ACTC_OVERLAY_EXEC_BASE+2
    cmp #'O'
    bne actc_overlay_validate_selected_fail
    lda ACTC_OVERLAY_EXEC_BASE+3
    cmp #'V'
    bne actc_overlay_validate_selected_fail
    lda ACTC_OVERLAY_EXEC_BASE+4
    cmp #ACTC_OVERLAY_ABI_VERSION
    bne actc_overlay_validate_selected_fail
    lda ACTC_OVERLAY_EXEC_BASE+5
    cmp actc_overlay_requested_pass
    bne actc_overlay_validate_selected_fail
    lda ACTC_OVERLAY_EXEC_BASE+6
    cmp #<ACTC_OVERLAY_EXEC_BASE
    bne actc_overlay_validate_selected_fail
    lda ACTC_OVERLAY_EXEC_BASE+7
    cmp #>ACTC_OVERLAY_EXEC_BASE
    bne actc_overlay_validate_selected_fail
    lda ACTC_OVERLAY_EXEC_BASE+10
    cmp actc_overlay_loaded_len
    bne actc_overlay_validate_selected_fail
    lda ACTC_OVERLAY_EXEC_BASE+11
    cmp actc_overlay_loaded_len+1
    bne actc_overlay_validate_selected_fail
    clc
    rts
actc_overlay_validate_selected_fail:
    sec
    rts

actc_overlay_call_exec:
    lda C64_MEMCFG
    sta actc_overlay_saved_memcfg
    and #C64_MEMCFG_BASIC_OFF_MASK
    sta C64_MEMCFG
    lda C64_MEMCFG
    sta actc_overlay_memcfg_before_call
    jsr actc_overlay_jsr_entry
    sta actc_overlay_status
    php
    lda C64_MEMCFG
    sta actc_overlay_memcfg_after_call
    lda actc_overlay_saved_memcfg
    sta C64_MEMCFG
    lda C64_MEMCFG
    sta actc_overlay_memcfg_after_restore
    lda actc_overlay_status
    plp
    rts

actc_overlay_jsr_entry:
    sec
    lda ACTC_OVERLAY_EXEC_BASE+8
    sbc #$01
    sta actc_overlay_entry_minus_one
    lda ACTC_OVERLAY_EXEC_BASE+9
    sbc #$00
    pha
    lda actc_overlay_entry_minus_one
    pha
    ldx #<actc_overlay_context
    ldy #>actc_overlay_context
    rts

init_module_name:
    ldx #svc_retptr
    jsr svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    beq init_module_name_default
    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    lda svc_retptr
    sta src_ptr
    lda svc_retptr+1
    sta src_ptr+1
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

parse_module_header_or_fail:
.if ACTC_USE_SOURCE_HEADER_OVERLAY
    .if ACTC_REU_SOURCE_CACHE
    jsr parse_module_header_with_overlay_if_possible
    bcc parse_module_header_or_fail_done
    .endif
.endif
.if ACTC_KEEP_SOURCE_HEADER_RESIDENT_FALLBACK
    jsr source_reader_reset_to_start
    bcc :+
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
:
    jsr skip_source_whitespace
    lda #<pattern_module
    sta const_ptr
    lda #>pattern_module
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcc :+
    jsr debug_bad_module_scan_head
    lda #<msg_bad_module
    ldy #>msg_bad_module
    jmp fail_with_ptr
:   ldy #$00
parse_module_header_keyword_advance:
    lda (const_ptr),y
    beq parse_module_header_keyword_done
    jsr advance_scan_ptr
    iny
    bne parse_module_header_keyword_advance
parse_module_header_keyword_done:
    jsr skip_source_spaces
    jsr copy_declared_module_or_fail
    jsr compare_declared_module_or_fail
.endif
parse_module_header_or_fail_done:
    rts

skip_source_whitespace:
    ldy #$00
skip_source_whitespace_loop:
    lda (scan_ptr),y
    cmp #' '
    beq skip_source_whitespace_advance
    cmp #9
    beq skip_source_whitespace_advance
    cmp #10
    beq skip_source_whitespace_advance
    cmp #13
    beq skip_source_whitespace_advance
    rts
skip_source_whitespace_advance:
    jsr advance_scan_ptr
    jmp skip_source_whitespace_loop

skip_source_spaces:
    ldy #$00
skip_source_spaces_loop:
    lda (scan_ptr),y
    cmp #' '
    beq skip_source_spaces_advance
    cmp #9
    beq skip_source_spaces_advance
    rts
skip_source_spaces_advance:
    jsr advance_scan_ptr
    jmp skip_source_spaces_loop

.if ACTC_USE_SOURCE_HEADER_OVERLAY
    .if ACTC_REU_SOURCE_CACHE
parse_module_header_with_overlay_if_possible:
    jsr source_reader_reset_to_start
    bcc :+
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
:
    lda #ACTC_OVERLAY_PASS_SOURCE_HEADER
    jsr actc_overlay_run_pass
    bcc parse_module_header_with_overlay_ok
    lda actc_overlay_context+ACTC_OVERLAY_CTX_DIAG_PTR_LO
    ora actc_overlay_context+ACTC_OVERLAY_CTX_DIAG_PTR_HI
    beq parse_module_header_with_overlay_fallback
    lda actc_overlay_context+ACTC_OVERLAY_CTX_DIAG_PTR_LO
    ldy actc_overlay_context+ACTC_OVERLAY_CTX_DIAG_PTR_HI
    jmp fail_with_ptr
parse_module_header_with_overlay_fallback:
.if ACTC_KEEP_SOURCE_HEADER_RESIDENT_FALLBACK
    sec
    rts
.else
    lda #<msg_header_overlay
    ldy #>msg_header_overlay
    jmp fail_with_ptr
.endif
parse_module_header_with_overlay_ok:
    cmp #ACTC_OVERLAY_STATUS_OK
    beq :+
    jmp parse_module_header_with_overlay_fallback
:
    clc
    rts
    .endif
.endif

.if ACTC_KEEP_SOURCE_HEADER_RESIDENT_FALLBACK
copy_declared_module_or_fail:
    ldy #$00
copy_declared_module_or_fail_loop:
    lda (scan_ptr),y
    beq copy_declared_module_or_fail_bad
    jsr uppercase_ascii
    cpy #$00
    bne copy_declared_module_or_fail_body
    jsr uppercase_symbol_start_valid
    bcc copy_declared_module_or_fail_store
    jmp copy_declared_module_or_fail_done
copy_declared_module_or_fail_body:
    jsr uppercase_symbol_body_valid
    bcc copy_declared_module_or_fail_store
    jmp copy_declared_module_or_fail_done
copy_declared_module_or_fail_store:
    sta declared_module_name,y
    iny
    cpy #24
    bcc copy_declared_module_or_fail_loop
copy_declared_module_or_fail_bad:
    jsr debug_bad_module_scan_head
    lda #<msg_bad_module
    ldy #>msg_bad_module
    jmp fail_with_ptr
copy_declared_module_or_fail_done:
    cpy #$00
    beq copy_declared_module_or_fail_bad
    lda #$00
    sta declared_module_name,y
    rts

compare_declared_module_or_fail:
    ldy #$00
compare_declared_module_or_fail_loop:
    lda declared_module_name,y
    sta compare_char
    lda module_name,y
    jsr uppercase_ascii
    cmp compare_char
    bne compare_declared_module_or_fail_bad
    lda compare_char
    beq compare_declared_module_or_fail_done
    iny
    bne compare_declared_module_or_fail_loop
compare_declared_module_or_fail_bad:
    jsr debug_bad_module_scan_head
    lda #<msg_bad_module
    ldy #>msg_bad_module
    jmp fail_with_ptr
compare_declared_module_or_fail_done:
    rts

debug_bad_module_scan_head:
    ldy #$00
debug_bad_module_scan_head_loop:
    lda (scan_ptr),y
    sta $03E8,y
    iny
    cpy #$08
    bcc debug_bad_module_scan_head_loop
    rts
.endif

collect_decls_or_fail:
    lda #$30
    jsr set_actc_trace
.if ACTC_USE_DECL_OVERLAY
    .if ACTC_REU_SOURCE_CACHE
    jsr collect_decls_with_overlay_if_possible
    bcc collect_decls_or_fail_done
    .endif
.endif
.if ACTC_KEEP_DECL_RESIDENT_FALLBACK
    jsr collect_module_vars_or_fail
    lda #$31
    jsr set_actc_trace
    jsr collect_proc_exports_or_fail
    lda #$32
    jsr set_actc_trace
    jsr collect_proc_locals_or_fail
    lda #$33
    jsr set_actc_trace
.endif
collect_decls_or_fail_done:
    rts

.if ACTC_USE_DECL_OVERLAY
    .if ACTC_REU_SOURCE_CACHE
collect_decls_with_overlay_if_possible:
    lda #ACTC_OVERLAY_PASS_DECL_COUNTS
    jsr actc_overlay_run_pass
    bcs collect_decls_with_overlay_fallback
    cmp #ACTC_OVERLAY_STATUS_OK
    beq collect_decls_with_overlay_ok
collect_decls_with_overlay_fallback:
.if ACTC_KEEP_DECL_RESIDENT_FALLBACK
    sec
    rts
.else
    lda #<msg_decl_overlay
    ldy #>msg_decl_overlay
    jmp fail_with_ptr
.endif
collect_decls_with_overlay_ok:
    clc
    rts
    .endif
.endif

.if ACTC_KEEP_DECL_RESIDENT_FALLBACK
collect_module_vars_or_fail:
    lda #$40
    jsr set_actc_trace
    lda #$00
    sta var_count_data
    sta module_var_count_data
    jsr source_reader_reset_to_start
    bcc :+
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
:
    lda #$41
    jsr set_actc_trace
    jsr skip_source_line
collect_module_vars_or_fail_loop:
    ldy #$00
    lda (scan_ptr),y
    beq collect_module_vars_or_fail_done
    cmp #10
    beq collect_module_vars_or_fail_advance_blank
    cmp #13
    beq collect_module_vars_or_fail_advance_blank
    jsr skip_source_spaces
    ldy #$00
    lda (scan_ptr),y
    beq collect_module_vars_or_fail_done
    lda #<pattern_proc
    sta const_ptr
    lda #>pattern_proc
    sta const_ptr+1
    jsr pattern_matches_scan_ptr_keyword
    bcc collect_module_vars_or_fail_done
    jsr match_scalar_decl_at_scan_ptr
    bcs collect_module_vars_or_fail_bad
    jsr store_module_var_from_scan_ptr_or_fail
    jsr skip_source_line
    jmp collect_module_vars_or_fail_loop
collect_module_vars_or_fail_advance_blank:
    jsr advance_scan_ptr
    jmp collect_module_vars_or_fail_loop
collect_module_vars_or_fail_bad:
    lda #<msg_bad_var
    ldy #>msg_bad_var
    jmp fail_with_ptr
collect_module_vars_or_fail_done:
    lda var_count_data
    sta module_var_count_data
    lda #$42
    jsr set_actc_trace
    rts

store_module_var_from_scan_ptr_or_fail:
    jsr match_scalar_decl_at_scan_ptr
    bcc :+
    jmp store_module_var_from_scan_ptr_or_fail_bad
:
    jsr advance_scan_ptr_by_const_ptr
    jsr skip_source_spaces
    jsr copy_symbol_from_scan_ptr
    bcc :+
    lda #<msg_bad_var
    ldy #>msg_bad_var
    jmp fail_with_ptr
:   sty compare_char
    jsr find_module_var_index_from_declared
    bcs :+
    jmp store_module_var_from_scan_ptr_or_fail_bad
:
    ldy #$00
store_module_var_from_scan_ptr_or_fail_save_name_loop:
    lda declared_module_name,y
    sta saved_var_name_data,y
    beq store_module_var_from_scan_ptr_or_fail_save_name_done
    iny
    cpy #25
    bcc store_module_var_from_scan_ptr_or_fail_save_name_loop
    jmp store_module_var_from_scan_ptr_or_fail_bad
store_module_var_from_scan_ptr_or_fail_save_name_done:
    lda #$00
    sta expr_value_lo
    sta expr_term_lo
    ldy compare_char
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    beq store_module_var_from_scan_ptr_or_fail_store
    cmp #10
    beq store_module_var_from_scan_ptr_or_fail_store
    cmp #13
    beq store_module_var_from_scan_ptr_or_fail_store
    cmp #'='
    beq :+
    jmp store_module_var_from_scan_ptr_or_fail_bad
:
    lda decl_width_data
    cmp #$02
    beq :+
    cmp #$04
    bne store_module_var_from_scan_ptr_or_fail_bad
    lda decl_type_data
    cmp #'r'
    bne store_module_var_from_scan_ptr_or_fail_bad
:
    jsr advance_scan_y
    bcc :+
    jmp store_module_var_from_scan_ptr_or_fail_bad
:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'['
    bne store_module_var_from_scan_ptr_or_fail_parse_value
    jsr advance_scan_y
    bcc :+
    jmp store_module_var_from_scan_ptr_or_fail_bad
:
    jsr parse_small_value_expr_at_scan_y
    bcs store_module_var_from_scan_ptr_or_fail_bad
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #']'
    bne store_module_var_from_scan_ptr_or_fail_bad
    jsr advance_scan_y
    bcc :+
    jmp store_module_var_from_scan_ptr_or_fail_bad
:
    jmp store_module_var_from_scan_ptr_or_fail_after_value
store_module_var_from_scan_ptr_or_fail_parse_value:
    jsr parse_small_value_expr_at_scan_y
    bcs store_module_var_from_scan_ptr_or_fail_bad
store_module_var_from_scan_ptr_or_fail_after_value:
    jsr require_line_end_at_scan_y
    bcs store_module_var_from_scan_ptr_or_fail_bad
    lda decl_width_data
    cmp #$04
    bne store_module_var_from_scan_ptr_or_fail_store
    lda expr_value_lo
    beq store_module_var_from_scan_ptr_or_fail_store
    jmp store_module_var_from_scan_ptr_or_fail_bad
store_module_var_from_scan_ptr_or_fail_store:
    ldx var_count_data
    cpx #VAR_MAX
    bcc :+
    lda #<msg_bad_var
    ldy #>msg_bad_var
    jmp fail_with_ptr
:   txa
    pha
.if ACTC_REU_VAR_DEBUG
    jsr store_var_debug_offset_from_current_scan_x
.endif
    jsr set_var_ptr_from_x
    ldy #$00
store_module_var_from_scan_ptr_or_fail_copy_loop:
    lda saved_var_name_data,y
    sta (export_ptr),y
    beq store_module_var_from_scan_ptr_or_fail_copy_done
    iny
    cpy #25
    bcc store_module_var_from_scan_ptr_or_fail_copy_loop
store_module_var_from_scan_ptr_or_fail_bad:
    lda #<msg_bad_var
    ldy #>msg_bad_var
    jmp fail_with_ptr
store_module_var_from_scan_ptr_or_fail_copy_done:
    pla
    tax
.if ACTC_REU_VAR_NAMES
    jsr store_var_name_to_reu_x
.endif
.if ACTC_REU_VAR_META
    lda expr_value_lo
    sta var_meta_init_lo_data
    lda #$00
    sta var_meta_init_hi_data
    lda decl_width_data
    sta var_meta_width_data
    lda decl_type_data
    sta var_meta_type_data
    jsr store_var_meta_to_reu_x
.else
    lda expr_value_lo
    sta var_init_lo,x
    lda #$00
    sta var_init_hi,x
    lda decl_width_data
    sta var_width_data,x
    lda decl_type_data
    sta var_type_data,x
.endif
    inc var_count_data
    rts
.endif

.if ACTC_KEEP_DECL_RESIDENT_FALLBACK
collect_proc_exports_or_fail:
    lda #$50
    jsr set_actc_trace
    lda #$00
    sta export_count_data
.if ACTC_REU_PROC_META
    jsr init_proc_meta_reu
    lda #$54
    jsr set_actc_trace
.endif
.if ACTC_REU_PROC_DEBUG
    jsr init_proc_debug_reu
.endif
    jsr source_reader_reset_to_start
    bcc :+
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
:
    lda #$51
    jsr set_actc_trace
collect_proc_exports_or_fail_loop:
    ldy #$00
    lda (scan_ptr),y
    beq collect_proc_exports_or_fail_done_check
    cmp #10
    beq collect_proc_exports_or_fail_advance_blank
    cmp #13
    beq collect_proc_exports_or_fail_advance_blank
    jsr skip_source_spaces
    ldy #$00
    lda (scan_ptr),y
    beq collect_proc_exports_or_fail_done_check
    lda #<pattern_proc
    sta const_ptr
    lda #>pattern_proc
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs collect_proc_exports_or_fail_skip_line
    jsr advance_scan_ptr_by_const_ptr
    jsr skip_source_spaces
    lda #$52
    jsr set_actc_trace
    jsr store_proc_export_from_scan_ptr_or_fail
collect_proc_exports_or_fail_skip_line:
    jsr skip_source_line
    jmp collect_proc_exports_or_fail_loop
collect_proc_exports_or_fail_advance_blank:
    jsr advance_scan_ptr
    jmp collect_proc_exports_or_fail_loop
collect_proc_exports_or_fail_done_check:
    lda export_count_data
    bne collect_proc_exports_or_fail_done
    lda #<msg_no_proc
    ldy #>msg_no_proc
    jmp fail_with_ptr
collect_proc_exports_or_fail_done:
    lda #$53
    jsr set_actc_trace
    rts
.endif

.if ACTC_KEEP_DECL_RESIDENT_FALLBACK
collect_proc_locals_or_fail:
    lda #$60
    jsr set_actc_trace
.if ACTC_REU_PROC_META
    ldx #$00
collect_proc_locals_or_fail_clear_loop:
    jsr load_proc_meta_from_reu_x
    lda #$00
    sta proc_meta_local_count_data
    sta proc_meta_local_base_data
    jsr store_proc_meta_to_reu_x
    inx
    cpx #EXPORT_MAX
    bcc collect_proc_locals_or_fail_clear_loop
.else
    lda #$00
    ldx #$00
collect_proc_locals_or_fail_clear_loop:
    sta proc_local_count_data,x
    sta proc_local_var_base_data,x
    inx
    cpx #EXPORT_MAX
    bcc collect_proc_locals_or_fail_clear_loop
.endif
    lda #$FF
    sta current_proc_index_data
    jsr source_reader_reset_to_start
    bcc :+
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
:
    lda #$61
    jsr set_actc_trace
collect_proc_locals_or_fail_loop:
    ldy #$00
    lda (scan_ptr),y
    beq collect_proc_locals_or_fail_done
    cmp #10
    beq collect_proc_locals_or_fail_advance_blank
    cmp #13
    beq collect_proc_locals_or_fail_advance_blank
    jsr skip_source_spaces
    ldy #$00
    lda (scan_ptr),y
    beq collect_proc_locals_or_fail_done
    lda #<pattern_proc
    sta const_ptr
    lda #>pattern_proc
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs collect_proc_locals_or_fail_try_int_decl
    jsr advance_scan_ptr_by_const_ptr
    jsr skip_source_spaces
    jsr copy_symbol_from_scan_ptr
    bcs collect_proc_locals_or_fail_bad_proc
    jsr find_export_index_from_declared
    bcs collect_proc_locals_or_fail_bad_proc
    stx current_proc_index_data
.if ACTC_REU_PROC_META
    jsr load_proc_meta_from_reu_x
    lda var_count_data
    sta proc_meta_local_base_data
    lda #$00
    sta proc_meta_local_count_data
    jsr store_proc_meta_to_reu_x
.else
    lda var_count_data
    sta proc_local_var_base_data,x
    lda #$00
    sta proc_local_count_data,x
.endif
    jsr skip_source_line
    jmp collect_proc_locals_or_fail_loop
collect_proc_locals_or_fail_try_int_decl:
    lda current_proc_index_data
    cmp #$FF
    beq collect_proc_locals_or_fail_skip_line
    jsr match_scalar_decl_at_scan_ptr
    bcs collect_proc_locals_or_fail_skip_line
    jsr store_proc_local_var_from_scan_ptr_or_fail
collect_proc_locals_or_fail_skip_line:
    jsr skip_source_line
    jmp collect_proc_locals_or_fail_loop
collect_proc_locals_or_fail_advance_blank:
    jsr advance_scan_ptr
    jmp collect_proc_locals_or_fail_loop
collect_proc_locals_or_fail_bad_proc:
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_ptr
collect_proc_locals_or_fail_done:
    lda #$FF
    sta current_proc_index_data
    lda #$62
    jsr set_actc_trace
    rts
.endif

.if ACTC_KEEP_DECL_RESIDENT_FALLBACK
store_proc_local_var_from_scan_ptr_or_fail:
    jsr match_scalar_decl_at_scan_ptr
    bcs store_proc_local_var_from_scan_ptr_or_fail_bad
    jsr advance_scan_ptr_by_const_ptr
    jsr skip_source_spaces
    jsr copy_symbol_from_scan_ptr
    bcc :+
    jmp store_proc_local_var_from_scan_ptr_or_fail_bad
:   ldx current_proc_index_data
    jsr find_current_proc_param_index_from_declared_for_proc_x
    bcs :+
    jmp store_proc_local_var_from_scan_ptr_or_fail_bad
:   ldx current_proc_index_data
    jsr find_current_proc_local_index_from_declared_for_proc_x
    bcs :+
    jmp store_proc_local_var_from_scan_ptr_or_fail_bad
:   ldx var_count_data
    cpx #VAR_MAX
    bcc :+
    jmp store_proc_local_var_from_scan_ptr_or_fail_bad
:   txa
    pha
    jsr set_var_ptr_from_x
    pla
    tax
    ldy #$00
store_proc_local_var_from_scan_ptr_or_fail_copy_loop:
    lda declared_module_name,y
    sta (export_ptr),y
    beq store_proc_local_var_from_scan_ptr_or_fail_copy_done
    iny
    cpy #25
    bcc store_proc_local_var_from_scan_ptr_or_fail_copy_loop
store_proc_local_var_from_scan_ptr_or_fail_bad:
    lda #<msg_bad_var
    ldy #>msg_bad_var
    jmp fail_with_ptr
store_proc_local_var_from_scan_ptr_or_fail_copy_done:
.if ACTC_REU_VAR_NAMES
    jsr store_var_name_to_reu_x
.endif
.if ACTC_REU_VAR_META
    lda #$00
    sta var_meta_init_lo_data
    sta var_meta_init_hi_data
    lda decl_width_data
    sta var_meta_width_data
    lda decl_type_data
    sta var_meta_type_data
    jsr store_var_meta_to_reu_x
.else
    lda #$00
    sta var_init_lo,x
    sta var_init_hi,x
    lda decl_width_data
    sta var_width_data,x
    lda decl_type_data
    sta var_type_data,x
.endif
    inc var_count_data
    ldx current_proc_index_data
.if ACTC_REU_PROC_META
    jsr load_proc_meta_from_reu_x
    inc proc_meta_local_count_data
    jsr store_proc_meta_to_reu_x
.else
    inc proc_local_count_data,x
.endif
    rts
.endif

collect_proc_body_ops:
.if ACTC_USE_BODY_OVERLAY
    jsr collect_proc_body_ops_with_overlay_if_possible
    bcs :+
    jmp collect_proc_body_ops_done_entry
:
.endif
.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
collect_proc_body_ops_resident:
    lda #$00
    sta string_count_data
    sta int_count_data
    sta extern_count_data
    sta loop_depth_data
    lda #$FF
    sta current_proc_index_data
.if ACTC_REU_BODY_DEBUG
    jsr init_body_debug_reu
.endif
.if ACTC_REU_BODY_OPS
    jsr init_body_ops_reu
.else
    lda #<body_ops_data
    sta body_ptr
    lda #>body_ops_data
    sta body_ptr+1
    ldy #$00
collect_proc_body_ops_clear_loop:
    lda #$00
    sta (body_ptr),y
    iny
    bne collect_proc_body_ops_clear_loop
.endif
    jsr source_reader_reset_to_start
    bcc :+
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
:
collect_proc_body_ops_loop:
    ldy #$00
    lda (scan_ptr),y
    bne collect_proc_body_ops_have_char
    jmp collect_proc_body_ops_done
collect_proc_body_ops_have_char:
    cmp #10
    bne :+
    jmp collect_proc_body_ops_advance_blank
:   cmp #13
    bne :+
    jmp collect_proc_body_ops_advance_blank
:
    jsr skip_source_spaces
    ldy #$00
    lda (scan_ptr),y
    bne collect_proc_body_ops_after_space_check
    jmp collect_proc_body_ops_done
collect_proc_body_ops_after_space_check:
    lda #<pattern_proc
    sta const_ptr
    lda #>pattern_proc
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs :+
    jmp collect_proc_body_ops_proc_decl
	:
	    lda current_proc_index_data
	    cmp #$FF
	    bne :+
	    jmp collect_proc_body_ops_skip_line
	:
.if ACTC_REU_BODY_DEBUG
        jsr store_current_body_debug_mark_from_scan_ptr
.endif
        jsr match_scalar_decl_at_scan_ptr
        bcc :+
        jmp collect_proc_body_ops_try_od
:
        jsr advance_scan_ptr_by_const_ptr
        jsr skip_source_spaces
        jsr copy_symbol_from_scan_ptr
        bcc :+
        jmp collect_proc_body_ops_bad_var
:
        tya
        pha
        ldx current_proc_index_data
        jsr find_current_proc_local_index_from_declared_for_proc_x
        bcc :+
        pla
        jmp collect_proc_body_ops_bad_var
:
        stx assignment_target_index_data
        pla
        tay
        jsr skip_inline_spaces_at_scan_y
        lda (scan_ptr),y
        bne :+
        jmp collect_proc_body_ops_skip_line
:
        cmp #10
        bne :+
        jmp collect_proc_body_ops_skip_line
:
        cmp #13
        bne :+
        jmp collect_proc_body_ops_skip_line
:
        cmp #'='
        beq :+
        jmp collect_proc_body_ops_bad_var
:
        ldx assignment_target_index_data
        jsr require_var_index_word_or_fail
        bcc collect_proc_body_ops_try_local_int_assignment
        ldx assignment_target_index_data
        jsr require_var_index_real_or_fail
        bcc collect_proc_body_ops_try_local_real_assignment
        jmp collect_proc_body_ops_bad_var
collect_proc_body_ops_try_local_int_assignment:
        jsr advance_scan_y
        bcc :+
        jmp collect_proc_body_ops_bad_literal
:
        jsr skip_inline_spaces_at_scan_y
        lda (scan_ptr),y
        cmp #'='
        bne :+
        jsr advance_scan_y
        bcc :+
        jmp collect_proc_body_ops_bad_literal
:
        jsr skip_inline_spaces_at_scan_y
        lda (scan_ptr),y
        cmp #'['
        beq :+
        jmp collect_proc_body_ops_try_local_int_parse_value
:
        jsr advance_scan_y
        bcc :+
        jmp collect_proc_body_ops_bad_literal
:
        jsr emit_runtime_value_from_scan_y_or_fail
        bcc :+
        jmp collect_proc_body_ops_bad_literal
:
        jsr skip_inline_spaces_at_scan_y
        lda (scan_ptr),y
        cmp #']'
        beq :+
        jmp collect_proc_body_ops_bad_literal
:
        jsr advance_scan_y
        bcc :+
        jmp collect_proc_body_ops_bad_literal
:
        jmp collect_proc_body_ops_try_local_int_after_value
collect_proc_body_ops_try_local_int_parse_value:
        jsr emit_runtime_value_from_scan_y_or_fail
        bcc :+
        jmp collect_proc_body_ops_bad_literal
:
collect_proc_body_ops_try_local_int_after_value:
        jsr require_line_end_at_scan_y
        bcc :+
        jmp collect_proc_body_ops_bad_literal
:
        ldx assignment_target_index_data
        lda #'S'
        jsr append_body_op_for_current_proc
        jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_local_real_assignment:
        jsr advance_scan_y
        bcc :+
        jmp collect_proc_body_ops_bad_literal
:
        jsr skip_inline_spaces_at_scan_y
        lda (scan_ptr),y
        cmp #'='
        bne :+
        jsr advance_scan_y
        bcc :+
        jmp collect_proc_body_ops_bad_literal
:       jsr emit_real_add_assignment_from_scan_y_or_fail
        bcs :+
        jmp collect_proc_body_ops_skip_line
:
        jmp collect_proc_body_ops_bad_literal

collect_proc_body_ops_try_od:
	    lda #<pattern_od
	    sta const_ptr
	    lda #>pattern_od
	    sta const_ptr+1
	    jsr pattern_matches_scan_ptr_keyword
	    bcs collect_proc_body_ops_try_until
	    jsr pop_loop_kind_to_compare_char_or_fail
	    lda compare_char
	    beq :+
	    lda #'x'
	    jsr append_body_op_no_arg_for_current_proc
	    jmp collect_proc_body_ops_skip_line
:
	    lda #'o'
	    jsr append_body_op_no_arg_for_current_proc
	    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_until:
	    lda #<pattern_until
	    sta const_ptr
	    lda #>pattern_until
	    sta const_ptr+1
	    jsr pattern_matches_scan_ptr_keyword
	    bcs collect_proc_body_ops_try_do
	    jsr advance_scan_ptr_by_const_ptr
	    jsr store_small_runtime_until_from_scan_ptr
	    bcc :+
	    jmp collect_proc_body_ops_if_bad_literal
:
	    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_do:
	    lda #<pattern_while
	    sta const_ptr
	    lda #>pattern_while
	    sta const_ptr+1
	    jsr pattern_matches_scan_ptr_keyword
	    bcs collect_proc_body_ops_try_do_keyword
	    jsr push_while_loop_kind_or_fail
	    lda #'d'
	    jsr append_body_op_no_arg_for_current_proc
	    jsr advance_scan_ptr_by_const_ptr
	    lda #'f'
	    sta expr_print_op
	    jsr store_small_runtime_condition_core
	    bcs collect_proc_body_ops_if_bad_literal
	    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_do_keyword:
	    lda #<pattern_do
	    sta const_ptr
	    lda #>pattern_do
	    sta const_ptr+1
	    jsr pattern_matches_scan_ptr_keyword
	    bcs collect_proc_body_ops_try_endif
	    jsr push_do_loop_kind_or_fail
	    lda #'d'
	    jsr append_body_op_no_arg_for_current_proc
	    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_endif:
	    lda #<pattern_endif
	    sta const_ptr
	    lda #>pattern_endif
	    sta const_ptr+1
	    jsr pattern_matches_scan_ptr_keyword
	    bcs collect_proc_body_ops_try_fi
	    lda #'v'
	    jsr append_body_op_no_arg_for_current_proc
	    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_fi:
	    lda #<pattern_fi
	    sta const_ptr
	    lda #>pattern_fi
	    sta const_ptr+1
	    jsr pattern_matches_scan_ptr_keyword
	    bcs collect_proc_body_ops_try_else
	    lda #'v'
	    jsr append_body_op_no_arg_for_current_proc
	    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_else:
	    lda #<pattern_else
	    sta const_ptr
	    lda #>pattern_else
	    sta const_ptr+1
	    jsr pattern_matches_scan_ptr_keyword
	    bcs collect_proc_body_ops_try_if
	    lda #'w'
	    jsr append_body_op_no_arg_for_current_proc
	    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_if:
	    lda #<pattern_if
	    sta const_ptr
	    lda #>pattern_if
	    sta const_ptr+1
	    jsr pattern_matches_scan_ptr_keyword
	    bcs collect_proc_body_ops_try_printe
	    jsr advance_scan_ptr_by_const_ptr
	    jsr store_small_runtime_condition_from_scan_ptr
	    bcs collect_proc_body_ops_if_bad_literal
	    jmp collect_proc_body_ops_skip_line
collect_proc_body_ops_if_bad_literal:
	    jmp collect_proc_body_ops_bad_literal

	    lda #<pattern_print_quote
	    sta const_ptr
	    lda #>pattern_print_quote
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs collect_proc_body_ops_try_printe
    jsr advance_scan_ptr_by_const_ptr
    lda #$12
    jsr set_actc_trace
    jsr store_string_literal_from_scan_ptr
    bcc :+
    jmp collect_proc_body_ops_bad_literal
:
    lda #$13
    jsr set_actc_trace
    lda #'s'
    jsr append_body_op_for_current_proc
    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_printe:
    lda #<pattern_printe_quote
    sta const_ptr
    lda #>pattern_printe_quote
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs collect_proc_body_ops_try_printre
    jsr advance_scan_ptr_by_const_ptr
    lda #$14
    jsr set_actc_trace
    jsr store_string_literal_from_scan_ptr
    bcc :+
    jmp collect_proc_body_ops_bad_literal
:
    lda #$15
    jsr set_actc_trace
    lda #'e'
    jsr append_body_op_for_current_proc
    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_printre:
    lda #<pattern_printre
    sta const_ptr
    lda #>pattern_printre
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs collect_proc_body_ops_try_printr
    jsr advance_scan_ptr_by_const_ptr
    lda #$01
    jsr store_runtime_real_print_with_newline_flag_from_scan_ptr
    bcs :+
    jmp collect_proc_body_ops_skip_line
:
    jmp collect_proc_body_ops_bad_literal

collect_proc_body_ops_try_printr:
    lda #<pattern_printr
    sta const_ptr
    lda #>pattern_printr
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs collect_proc_body_ops_try_printie
    jsr advance_scan_ptr_by_const_ptr
    lda #$00
    jsr store_runtime_real_print_with_newline_flag_from_scan_ptr
    bcs :+
    jmp collect_proc_body_ops_skip_line
:
    jmp collect_proc_body_ops_bad_literal

collect_proc_body_ops_try_printie:
    lda #<pattern_printie
    sta const_ptr
    lda #>pattern_printie
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs collect_proc_body_ops_try_printi
    jsr advance_scan_ptr_by_const_ptr
    jsr store_small_decimal_literal_from_scan_ptr
    bcc collect_proc_body_ops_try_printie_literal_done
    lda #'z'
    sta expr_print_op
    jsr store_small_runtime_expr_from_scan_ptr
    bcc collect_proc_body_ops_try_printie_runtime_done
    jmp collect_proc_body_ops_bad_literal
collect_proc_body_ops_try_printie_runtime_done:
    jmp collect_proc_body_ops_skip_line
collect_proc_body_ops_try_printie_literal_done:
    lda #'i'
    jsr append_body_op_for_current_proc
    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_printi:
    lda #<pattern_printi
    sta const_ptr
    lda #>pattern_printi
    sta const_ptr+1
    jsr pattern_matches_scan_ptr
    bcs collect_proc_body_ops_try_return
    jsr advance_scan_ptr_by_const_ptr
    jsr store_small_decimal_literal_from_scan_ptr
    bcc collect_proc_body_ops_try_printi_literal_done
    lda #'y'
    sta expr_print_op
    jsr store_small_runtime_expr_from_scan_ptr
    bcc collect_proc_body_ops_try_printi_runtime_done
    jmp collect_proc_body_ops_bad_literal
collect_proc_body_ops_try_printi_runtime_done:
    jmp collect_proc_body_ops_skip_line
collect_proc_body_ops_try_printi_literal_done:
    lda #'j'
    jsr append_body_op_for_current_proc
    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_return:
    lda #<pattern_return
    sta const_ptr
    lda #>pattern_return
    sta const_ptr+1
    jsr pattern_matches_scan_ptr_keyword
    bcs collect_proc_body_ops_try_assignment
    jsr advance_scan_ptr_by_const_ptr
    ldy #$00
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    beq collect_proc_body_ops_try_return_emit
    cmp #10
    beq collect_proc_body_ops_try_return_emit
    cmp #13
    beq collect_proc_body_ops_try_return_emit
    jsr emit_runtime_value_from_scan_y_or_fail
    bcc :+
    jmp collect_proc_body_ops_bad_literal
:
    jsr require_line_end_at_scan_y
    bcc collect_proc_body_ops_try_return_emit
    jmp collect_proc_body_ops_bad_literal
collect_proc_body_ops_try_return_emit:
    lda #'r'
    jsr append_body_op_no_arg_for_current_proc
    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_assignment:
    jsr copy_symbol_from_scan_ptr
    bcc :+
    jmp collect_proc_body_ops_skip_line
:
    sty hex_work
    ldy hex_work
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'='
    bne collect_proc_body_ops_try_local_call
    sty symbol_end_y_data
    jsr find_var_index_from_declared
    bcc :+
    jmp collect_proc_body_ops_bad_var
:
    stx assignment_target_index_data
.if ACTC_REU_VAR_META
    jsr load_var_meta_from_reu_x
    lda var_meta_width_data
.else
    lda var_width_data,x
.endif
    cmp #$02
    beq collect_proc_body_ops_try_assignment_word
    cmp #$04
    beq collect_proc_body_ops_try_assignment_real
    jmp collect_proc_body_ops_bad_var
collect_proc_body_ops_try_assignment_word:
    ldy symbol_end_y_data
    jsr advance_scan_y
    bcc :+
    jmp collect_proc_body_ops_bad_literal
:
    jsr emit_runtime_value_from_scan_y_or_fail
    bcs collect_proc_body_ops_bad_literal
    jsr require_line_end_at_scan_y
    bcs collect_proc_body_ops_bad_literal
    ldx assignment_target_index_data
    lda #'S'
    jsr append_body_op_for_current_proc
    jmp collect_proc_body_ops_skip_line
collect_proc_body_ops_try_assignment_real:
    ldy symbol_end_y_data
    jsr advance_scan_y
    bcc :+
    jmp collect_proc_body_ops_bad_literal
:
    jsr emit_real_add_assignment_from_scan_y_or_fail
    bcs collect_proc_body_ops_bad_literal
    jmp collect_proc_body_ops_skip_line

collect_proc_body_ops_try_local_call:
    ldy hex_work
    lda (scan_ptr),y
    cmp #'('
    bne collect_proc_body_ops_skip_line
    sty symbol_end_y_data
    jsr resolve_call_target_from_declared_or_fail
    bcs collect_proc_body_ops_bad_proc
    ldy symbol_end_y_data
    jsr emit_call_args_from_scan_y_or_fail
    bcs collect_proc_body_ops_bad_proc
    lda call_target_kind
    ldx call_target_index_data
    jsr append_body_op_for_current_proc
collect_proc_body_ops_skip_line:
    jsr skip_source_line
    jmp collect_proc_body_ops_loop
collect_proc_body_ops_proc_decl:
    jsr advance_scan_ptr_by_const_ptr
    jsr skip_source_spaces
    jsr copy_symbol_from_scan_ptr
    bcs collect_proc_body_ops_bad_proc
    jsr find_export_index_from_declared
    bcs collect_proc_body_ops_bad_proc
    stx current_proc_index_data
.if ACTC_REU_BODY_DEBUG
    jsr store_current_body_debug_mark_from_scan_ptr
.endif
    jsr emit_current_proc_param_binds_or_fail
    jsr skip_source_line
    jmp collect_proc_body_ops_loop
collect_proc_body_ops_advance_blank:
    jsr advance_scan_ptr
    jmp collect_proc_body_ops_loop
collect_proc_body_ops_bad_proc:
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_ptr
collect_proc_body_ops_bad_var:
    lda #<msg_bad_var
    ldy #>msg_bad_var
    jmp fail_with_ptr
collect_proc_body_ops_bad_literal:
    lda #<msg_bad_literal
    ldy #>msg_bad_literal
    jmp fail_with_ptr
collect_proc_body_ops_done:
.if ACTC_REU_BODY_OPS
    jsr flush_body_window_if_dirty
.endif
.endif
collect_proc_body_ops_done_entry:
    rts

collect_proc_body_ops_overlay_begin:
    lda #$00
    sta string_count_data
    sta int_count_data
    sta extern_count_data
    lda #$FF
    sta current_proc_index_data
.if ACTC_REU_BODY_DEBUG
    jsr init_body_debug_reu
.endif
.if ACTC_REU_BODY_OPS
    jsr init_body_ops_reu
.else
    lda #<body_ops_data
    sta body_ptr
    lda #>body_ops_data
    sta body_ptr+1
    ldy #$00
collect_proc_body_ops_overlay_begin_clear_loop:
    lda #$00
    sta (body_ptr),y
    iny
    bne collect_proc_body_ops_overlay_begin_clear_loop
.endif
    jsr source_reader_reset_to_start
    rts

collect_proc_body_ops_overlay_finish:
.if ACTC_REU_BODY_OPS
    jsr flush_body_window_if_dirty
.endif
    clc
    rts

append_body_op_for_current_proc:
    sta compare_char
    stx hex_work
    tya
    pha
    ldx current_proc_index_data
    jsr set_body_ptr_from_x
    ldy #$00
append_body_op_for_current_proc_loop:
    lda (body_ptr),y
    beq append_body_op_for_current_proc_store
    iny
    cpy #(BODY_OPS_STRIDE - 2)
    bcc append_body_op_for_current_proc_loop
    lda compare_char
    jsr set_actc_trace
    lda #<msg_bad_call
    ldy #>msg_bad_call
    jmp fail_with_ptr
append_body_op_for_current_proc_store:
    lda compare_char
    sta (body_ptr),y
    iny
    lda hex_work
    cmp #10
    bcc :+
    sec
    sbc #10
    clc
    adc #'A'
    bne append_body_op_for_current_proc_store_index
:   clc
    adc #'0'
append_body_op_for_current_proc_store_index:
    sta (body_ptr),y
    iny
    lda #$00
    sta (body_ptr),y
.if ACTC_REU_BODY_OPS
    lda #$01
    sta body_window_dirty_data
.endif
.if ACTC_REU_BODY_DEBUG
    jsr record_body_debug_offset_for_current_proc
.endif
    pla
    tay
    rts

append_body_op_no_arg_for_current_proc:
    sta compare_char
    tya
    pha
    ldx current_proc_index_data
    jsr set_body_ptr_from_x
    ldy #$00
append_body_op_no_arg_for_current_proc_loop:
    lda (body_ptr),y
    beq append_body_op_no_arg_for_current_proc_store
    iny
    cpy #(BODY_OPS_STRIDE - 1)
    bcc append_body_op_no_arg_for_current_proc_loop
    lda compare_char
    jsr set_actc_trace
    lda #<msg_bad_call
    ldy #>msg_bad_call
    jmp fail_with_ptr
append_body_op_no_arg_for_current_proc_store:
    lda compare_char
    sta (body_ptr),y
    iny
    lda #$00
    sta (body_ptr),y
.if ACTC_REU_BODY_OPS
    lda #$01
    sta body_window_dirty_data
.endif
.if ACTC_REU_BODY_DEBUG
    jsr record_body_debug_offset_for_current_proc
.endif
    pla
    tay
    rts

.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
push_do_loop_kind_or_fail:
    lda #$00
    jmp push_loop_kind_a_or_fail

push_while_loop_kind_or_fail:
    lda #$01

push_loop_kind_a_or_fail:
    ldx loop_depth_data
    cpx #LOOP_MAX
    bcc :+
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_ptr
:   sta loop_kind_stack,x
    inc loop_depth_data
    rts
.endif

.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
emit_current_proc_param_binds_or_fail:
    ldx current_proc_index_data
.if ACTC_REU_PROC_META
    jsr load_proc_meta_from_reu_x
    lda proc_meta_param_count_data
    beq emit_current_proc_param_binds_or_fail_done
    sta param_bind_count_data
    lda proc_meta_param_base_data
    sta param_bind_base_data
.else
    lda proc_param_count_data,x
    beq emit_current_proc_param_binds_or_fail_done
    sta param_bind_count_data
    lda proc_param_var_base_data,x
    sta param_bind_base_data
.endif
emit_current_proc_param_binds_or_fail_loop:
    lda param_bind_count_data
    beq emit_current_proc_param_binds_or_fail_done
    clc
    lda param_bind_base_data
    adc param_bind_count_data
    sec
    sbc #$01
    tax
    lda #'S'
    jsr append_body_op_for_current_proc
    dec param_bind_count_data
    jmp emit_current_proc_param_binds_or_fail_loop
emit_current_proc_param_binds_or_fail_done:
    rts
.endif

.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
pop_loop_kind_to_compare_char_or_fail:
    ldx loop_depth_data
    bne :+
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_ptr
:   dex
    stx loop_depth_data
    lda loop_kind_stack,x
    sta compare_char
    rts
.endif

set_body_ptr_from_x:
.if ACTC_REU_BODY_OPS
    txa
    pha
    cpx body_window_index_data
    beq set_body_ptr_from_x_window_ready
    stx body_window_request_data
    jsr flush_body_window_if_dirty
    ldx body_window_request_data
    jsr load_body_window_from_reu_x
    ldx body_window_request_data
    stx body_window_index_data
set_body_ptr_from_x_window_ready:
    lda #<body_ops_window
    sta body_ptr
    lda #>body_ops_window
    sta body_ptr+1
    pla
    tax
    rts
.else
    txa
    pha
    lda #<body_ops_data
    sta body_ptr
    lda #>body_ops_data
    sta body_ptr+1
set_body_ptr_from_x_loop:
    cpx #$00
    beq set_body_ptr_from_x_done
    clc
    lda body_ptr
    adc #BODY_OPS_STRIDE
    sta body_ptr
    lda body_ptr+1
    adc #$00
    sta body_ptr+1
    dex
    bne set_body_ptr_from_x_loop
set_body_ptr_from_x_done:
    pla
    tax
    rts
.endif

.if ACTC_REU_BODY_OPS
init_body_ops_reu:
    lda #$FF
    sta body_window_index_data
    lda #$00
    sta body_window_dirty_data
    ldy #$00
init_body_ops_reu_clear_loop:
    sta body_ops_window,y
    iny
    cpy #BODY_OPS_STRIDE
    bcc init_body_ops_reu_clear_loop
    ldx #$00
init_body_ops_reu_store_loop:
    txa
    pha
    jsr store_body_window_to_reu_x
    pla
    tax
    inx
    cpx #EXPORT_MAX
    bcc init_body_ops_reu_store_loop
    rts

flush_body_window_if_dirty:
    lda body_window_dirty_data
    beq flush_body_window_if_dirty_done
    ldx body_window_index_data
    cpx #$FF
    beq flush_body_window_if_dirty_clean
    jsr store_body_window_to_reu_x
flush_body_window_if_dirty_clean:
    lda #$00
    sta body_window_dirty_data
flush_body_window_if_dirty_done:
    rts

set_body_reu_params_from_x:
    lda #ACTC_BODY_OPS_REU_BASE_LO
    sta file_params+0
    lda #ACTC_BODY_OPS_REU_BASE_HI
    sta file_params+1
    lda #ACTC_BODY_OPS_REU_BASE_BANK
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

load_body_window_from_reu_x:
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
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_body_window_from_reu_x_ok
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_body_window_from_reu_x_ok:
    rts

store_body_window_to_reu_x:
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
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_body_window_to_reu_x_ok
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_body_window_to_reu_x_ok:
    rts
.endif

set_string_ptr_from_x:
.if ACTC_REU_STRING_LITERALS
    jsr load_string_literal_from_reu_x
    lda #<string_literal_window
    sta body_ptr
    lda #>string_literal_window
    sta body_ptr+1
    rts
.else
    lda #<string_literals
    sta body_ptr
    lda #>string_literals
    sta body_ptr+1
set_string_ptr_from_x_loop:
    cpx #$00
    beq set_string_ptr_from_x_done
    clc
    lda body_ptr
    adc #24
    sta body_ptr
    lda body_ptr+1
    adc #$00
    sta body_ptr+1
    dex
    bne set_string_ptr_from_x_loop
set_string_ptr_from_x_done:
    rts
.endif

.if ACTC_REU_STRING_LITERALS
set_string_reu_params_from_x:
    lda #ACTC_STRING_REU_BASE_LO
    sta file_params+0
    lda #ACTC_STRING_REU_BASE_HI
    sta file_params+1
    lda #ACTC_STRING_REU_BASE_BANK
    sta file_params+2
set_string_reu_params_from_x_loop:
    cpx #$00
    beq set_string_reu_params_from_x_done
    clc
    lda file_params+0
    adc #24
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

load_string_literal_from_reu_x:
    jsr set_string_reu_params_from_x
    lda #<string_literal_window
    sta file_params+3
    lda #>string_literal_window
    sta file_params+4
    lda #24
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_string_literal_from_reu_x_ok
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_string_literal_from_reu_x_ok:
    rts

store_string_literal_to_reu_x:
    txa
    pha
    jsr set_string_reu_params_from_x
    lda #<string_literal_window
    sta file_params+3
    lda #>string_literal_window
    sta file_params+4
    lda #24
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_string_literal_to_reu_x_ok
    pla
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_string_literal_to_reu_x_ok:
    pla
    tax
    rts
.endif

store_string_literal_from_scan_ptr:
    ldx string_count_data
    cpx #STRING_LITERAL_MAX
    bcc :+
    sec
    rts
:   txa
    pha
    jsr set_string_ptr_from_x
    pla
    tax
    ldy #$00
store_string_literal_from_scan_ptr_loop:
    lda (scan_ptr),y
    beq store_string_literal_from_scan_ptr_fail
    cmp #'"'
    beq store_string_literal_from_scan_ptr_done
    sta (body_ptr),y
    iny
    cpy #23
    bcc store_string_literal_from_scan_ptr_loop
store_string_literal_from_scan_ptr_fail:
    sec
    rts
store_string_literal_from_scan_ptr_done:
    lda #$00
    sta (body_ptr),y
.if ACTC_REU_STRING_LITERALS
    jsr store_string_literal_to_reu_x
.endif
    inc string_count_data
    clc
    rts

store_small_decimal_literal_from_scan_ptr:
    ldx int_count_data
    cpx #INT_LITERAL_MAX
    bcc :+
    sec
    rts
:   ldy #$00
    txa
    pha
    jsr parse_small_value_expr_at_scan_y
    pla
    tax
    bcs store_small_decimal_literal_from_scan_ptr_fail
.if ACTC_REU_INT_LITERALS
    lda expr_value_lo
    sta int_literal_lo_data
    lda #$00
    sta int_literal_hi_data
    jsr store_int_literal_to_reu_x
.else
    lda expr_value_lo
    sta int_values_lo,x
    lda #$00
    sta int_values_hi,x
.endif
    inc int_count_data
    clc
    rts
store_small_decimal_literal_from_scan_ptr_fail:
    sec
    rts

store_zero_int_literal:
    ldx int_count_data
    cpx #INT_LITERAL_MAX
    bcc :+
    sec
    rts
:
.if ACTC_REU_INT_LITERALS
    lda #$00
    sta int_literal_lo_data
    sta int_literal_hi_data
    jsr store_int_literal_to_reu_x
.else
    lda #$00
    sta int_values_lo,x
    sta int_values_hi,x
.endif
    inc int_count_data
    clc
    rts

store_word_literal_from_ay:
    sta compare_char
    sty expr_saved_lo
    ldx int_count_data
    cpx #INT_LITERAL_MAX
    bcc :+
    sec
    rts
:
.if ACTC_REU_INT_LITERALS
    lda compare_char
    sta int_literal_lo_data
    lda expr_saved_lo
    sta int_literal_hi_data
    jsr store_int_literal_to_reu_x
.else
    lda compare_char
    sta int_values_lo,x
    lda expr_saved_lo
    sta int_values_hi,x
.endif
    inc int_count_data
    clc
    rts

.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
store_small_runtime_expr_from_scan_ptr:
    ldy #$00
    jsr scan_value_expr_for_top_level_arith_from_scan_y
    bcs :+
    jmp store_small_runtime_expr_sum_entry
:
    jsr scan_print_expr_for_bool_keywords_from_scan_y
    bcs :+
    jmp store_small_runtime_expr_bool_entry
:
store_small_runtime_expr_sum_entry:
    lda #$00
    sta expr_runtime_post_zero
    jsr emit_runtime_sum_from_scan_y_or_fail
    bcc :+
    sec
    rts
:   jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    sta expr_compare_lo
    cmp #')'
    bne :+
    jmp store_small_runtime_expr_print
:
    cmp #'='
    beq store_small_runtime_expr_compare_entry
    cmp #'<'
    beq store_small_runtime_expr_compare_entry
    cmp #'>'
    beq store_small_runtime_expr_compare_entry
    sec
    rts
store_small_runtime_expr_compare_entry:
    lda #$00
    sta expr_runtime_post_zero
    lda expr_compare_lo
    cmp #'='
    beq store_small_runtime_expr_eq
    cmp #'<'
    beq store_small_runtime_expr_lt_entry
    cmp #'>'
    beq store_small_runtime_expr_gt_entry
    sec
    rts
store_small_runtime_expr_eq:
    lda #'q'
    sta expr_runtime_op
    jsr advance_scan_y
    jmp store_small_runtime_expr_rhs
store_small_runtime_expr_lt_entry:
    jsr advance_scan_y
    lda (scan_ptr),y
    cmp #'>'
    beq store_small_runtime_expr_ne
    cmp #'='
    beq store_small_runtime_expr_le
    lda #'l'
    sta expr_runtime_op
    jmp store_small_runtime_expr_rhs
store_small_runtime_expr_gt_entry:
    jsr advance_scan_y
    lda (scan_ptr),y
    cmp #'='
    beq store_small_runtime_expr_ge
    lda #'g'
    sta expr_runtime_op
    jmp store_small_runtime_expr_rhs
store_small_runtime_expr_le:
    lda #'g'
    sta expr_runtime_op
    lda #$01
    sta expr_runtime_post_zero
    jsr advance_scan_y
    jmp store_small_runtime_expr_rhs
store_small_runtime_expr_ge:
    lda #'l'
    sta expr_runtime_op
    lda #$01
    sta expr_runtime_post_zero
    jsr advance_scan_y
    jmp store_small_runtime_expr_rhs
store_small_runtime_expr_ne:
    lda #'n'
    sta expr_runtime_op
    jsr advance_scan_y
store_small_runtime_expr_rhs:
    jsr emit_runtime_sum_from_scan_y_or_fail
    bcc :+
store_small_runtime_expr_fail:
    sec
    rts
:   jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne store_small_runtime_expr_fail
    lda expr_runtime_op
    jsr append_body_op_no_arg_for_current_proc
    lda expr_runtime_post_zero
    beq store_small_runtime_expr_print
    lda #$00
    sta expr_value_lo
    jsr store_expr_value_as_int_literal
    bcs store_small_runtime_expr_fail
    lda #'p'
    jsr append_body_op_for_current_proc
    lda #'q'
    jsr append_body_op_no_arg_for_current_proc
store_small_runtime_expr_print:
    lda expr_print_op
    jsr append_body_op_no_arg_for_current_proc
    clc
    rts

store_small_runtime_expr_bool_entry:
    lda #$00
    sta bool_ops_used_data
    jsr emit_runtime_bool_or_from_scan_y_or_fail
    bcs store_small_runtime_expr_fail
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne store_small_runtime_expr_fail
    jmp store_small_runtime_expr_print

store_small_runtime_condition_with_a_from_scan_ptr:
    sta expr_print_op
    jmp store_small_runtime_condition_core

store_small_runtime_expr_with_a_from_scan_ptr:
    sta expr_print_op
    jmp store_small_runtime_expr_from_scan_ptr

.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
store_small_runtime_condition_from_scan_ptr:
    lda #'h'
    sta expr_print_op
    jmp store_small_runtime_condition_core

store_small_runtime_while_from_scan_ptr:
    lda #'f'
    sta expr_print_op
    jmp store_small_runtime_condition_core

store_small_runtime_printie_from_scan_ptr:
    lda #'z'
    sta expr_print_op
    jmp store_small_runtime_expr_from_scan_ptr

store_small_runtime_printi_from_scan_ptr:
    lda #'y'
    sta expr_print_op
    jmp store_small_runtime_expr_from_scan_ptr

store_runtime_real_print_with_newline_flag_from_scan_ptr:
    sta expr_runtime_post_zero
    jsr emit_runtime_real_value_from_scan_y_or_fail
    bcs store_small_runtime_expr_fail
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    beq :+
    jmp store_small_runtime_expr_fail
:
    jsr advance_scan_y
    bcc :+
    jmp store_small_runtime_expr_fail
:
    jsr skip_inline_spaces_at_scan_y
    jsr require_line_end_at_scan_y
    bcc :+
    jmp store_small_runtime_expr_fail
:
    lda expr_runtime_post_zero
    beq store_runtime_real_print_with_newline_flag_zero
    lda #$01
    ldy #$00
    jsr store_word_literal_from_ay
    bcc :+
    jmp store_small_runtime_expr_fail
:
    bcc store_runtime_real_print_with_newline_flag_have_flag
store_runtime_real_print_with_newline_flag_zero:
    jsr store_zero_int_literal
    bcc :+
    jmp store_small_runtime_expr_fail
:
store_runtime_real_print_with_newline_flag_have_flag:
    lda #'p'
    jsr append_body_op_for_current_proc
    jsr find_or_store_rt_print_f_external
    bcc :+
    jmp store_small_runtime_expr_fail
:
    lda #'u'
    jsr append_body_op_for_current_proc
    clc
    rts

store_small_runtime_until_from_scan_ptr:
    lda #'t'
    sta expr_print_op
.endif
store_small_runtime_condition_core:
    lda #$00
    sta bool_ops_used_data
    ldy #$00
    jsr emit_runtime_bool_or_from_scan_y_or_fail
    bcc store_small_runtime_condition_done_check
    sec
    rts
store_small_runtime_condition_done_check:
    lda expr_print_op
    cmp #'h'
    bne :+
    jsr require_then_or_line_end_at_scan_y
    bcc store_small_runtime_condition_done_ok
    jmp store_small_runtime_condition_fail
:   cmp #'f'
    bne :+
    jsr require_do_or_line_end_at_scan_y
    bcc store_small_runtime_condition_done_ok
    jmp store_small_runtime_condition_fail
:   jsr require_line_end_at_scan_y
    bcc store_small_runtime_condition_done_ok
store_small_runtime_condition_fail:
    sec
    rts
store_small_runtime_condition_done_ok:
    lda expr_print_op
    jsr append_body_op_no_arg_for_current_proc
    clc
    rts
.endif

require_line_end_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    beq require_line_end_at_scan_y_ok
    cmp #10
    beq require_line_end_at_scan_y_ok
    cmp #13
    beq require_line_end_at_scan_y_ok
    sec
    rts
require_line_end_at_scan_y_ok:
    clc
    rts

.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
require_then_or_line_end_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    beq require_then_or_line_end_at_scan_y_ok
    cmp #10
    beq require_then_or_line_end_at_scan_y_ok
    cmp #13
    beq require_then_or_line_end_at_scan_y_ok
    jsr uppercase_ascii
    cmp #'T'
    bne require_then_or_line_end_at_scan_y_fail
    jsr advance_scan_y
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'H'
    bne require_then_or_line_end_at_scan_y_fail
    jsr advance_scan_y
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'E'
    bne require_then_or_line_end_at_scan_y_fail
    jsr advance_scan_y
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'N'
    bne require_then_or_line_end_at_scan_y_fail
    jsr advance_scan_y
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    beq require_then_or_line_end_at_scan_y_ok
    cmp #10
    beq require_then_or_line_end_at_scan_y_ok
    cmp #13
    beq require_then_or_line_end_at_scan_y_ok
require_then_or_line_end_at_scan_y_fail:
    sec
    rts
require_then_or_line_end_at_scan_y_ok:
    clc
    rts

require_do_or_line_end_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    beq require_do_or_line_end_at_scan_y_ok
    cmp #10
    beq require_do_or_line_end_at_scan_y_ok
    cmp #13
    beq require_do_or_line_end_at_scan_y_ok
    jsr uppercase_ascii
    cmp #'D'
    bne require_do_or_line_end_at_scan_y_fail
    jsr advance_scan_y
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'O'
    bne require_do_or_line_end_at_scan_y_fail
    jsr advance_scan_y
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    beq require_do_or_line_end_at_scan_y_ok
    cmp #10
    beq require_do_or_line_end_at_scan_y_ok
    cmp #13
    beq require_do_or_line_end_at_scan_y_ok
require_do_or_line_end_at_scan_y_fail:
    sec
    rts
require_do_or_line_end_at_scan_y_ok:
    clc
    rts
.endif

emit_saved_expr_push_or_fail:
    lda expr_saved_lo
    sta expr_value_lo
emit_current_expr_push_or_fail:
    jsr store_expr_value_as_int_literal
    bcs emit_runtime_expr_push_fail
    lda #'p'
    jsr append_body_op_for_current_proc
    clc
    rts
emit_runtime_expr_push_fail:
    sec
    rts

emit_runtime_term_push_from_scan_y_or_fail:
    jsr skip_inline_spaces_at_scan_y
    jsr try_consume_int_open_from_scan_y
    bcs :+
    jmp emit_runtime_int_explicit_value_from_scan_y_or_fail
:
    tya
    pha
    jsr find_var_index_from_scan_y
    bcs emit_runtime_term_push_literal
    jsr require_var_index_word_or_fail
    bcc :+
    pla
    sec
    rts
:
    lda #'L'
    jsr append_body_op_for_current_proc
    pla
    clc
    rts
emit_runtime_term_push_literal:
    pla
    tay
    jsr emit_runtime_call_term_from_scan_y_or_fail
    bcc :+
    tya
    pha
    jsr parse_small_decimal_term_at_scan_y
    bcc emit_runtime_term_push_literal_decimal
    pla
    tay
    jsr emit_runtime_group_value_term_from_scan_y_or_fail
    bcs emit_runtime_expr_push_fail
    clc
    rts
emit_runtime_term_push_literal_decimal:
    pla
    jmp emit_current_expr_push_or_fail
:   clc
    rts

emit_runtime_group_value_term_from_scan_y_or_fail:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'('
    bne emit_runtime_group_value_term_from_scan_y_or_fail_fail
    jsr advance_scan_y
    jsr emit_runtime_value_from_scan_y_or_fail
    bcs emit_runtime_group_value_term_from_scan_y_or_fail_fail
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne emit_runtime_group_value_term_from_scan_y_or_fail_fail
    jsr advance_scan_y
    clc
    rts
emit_runtime_group_value_term_from_scan_y_or_fail_fail:
    sec
    rts

emit_runtime_call_term_from_scan_y_or_fail:
    jsr copy_symbol_from_scan_y
    bcc :+
    sec
    rts
:
    sty symbol_end_y_data
    jsr resolve_call_target_from_declared_or_fail
    bcs emit_runtime_call_term_from_scan_y_or_fail_fail
    ldy symbol_end_y_data
    jsr emit_call_args_from_scan_y_or_fail
    bcs emit_runtime_call_term_from_scan_y_or_fail_fail
    lda call_target_kind
    ldx call_target_index_data
    jsr append_body_op_for_current_proc
    clc
    rts
emit_runtime_call_term_from_scan_y_or_fail_fail:
    sec
    rts

try_consume_int_open_from_scan_y:
    sty symbol_start_y_data
    jsr save_source_reader_mark
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'I'
    bne try_consume_int_open_from_scan_y_fail_restore
    jsr advance_scan_y
    bcs try_consume_int_open_from_scan_y_fail_restore
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'N'
    bne try_consume_int_open_from_scan_y_fail_restore
    jsr advance_scan_y
    bcs try_consume_int_open_from_scan_y_fail_restore
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'T'
    bne try_consume_int_open_from_scan_y_fail_restore
    jsr advance_scan_y
    bcs try_consume_int_open_from_scan_y_fail_restore
    lda (scan_ptr),y
    cmp #'('
    bne try_consume_int_open_from_scan_y_fail_restore
    jsr advance_scan_y
    bcs try_consume_int_open_from_scan_y_fail_restore
    jsr skip_inline_spaces_at_scan_y
    clc
    rts
try_consume_int_open_from_scan_y_fail_restore:
    jsr restore_source_reader_mark
    ldy symbol_start_y_data
    sec
    rts

emit_runtime_int_explicit_value_from_scan_y_or_fail:
    jsr copy_symbol_from_scan_y
    bcs emit_runtime_int_explicit_value_from_scan_y_or_fail_fail
    sty symbol_end_y_data
    jsr find_var_index_from_declared
    bcs emit_runtime_int_explicit_value_from_scan_y_or_fail_fail
    stx real_lhs_index_data
    jsr require_var_index_real_or_fail
    bcs emit_runtime_int_explicit_value_from_scan_y_or_fail_fail
    ldy symbol_end_y_data
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne emit_runtime_int_explicit_value_from_scan_y_or_fail_fail
    jsr advance_scan_y
    bcs emit_runtime_int_explicit_value_from_scan_y_or_fail_fail
    ldx real_lhs_index_data
    lda #'L'
    jsr append_body_op_for_current_proc
    ldx real_lhs_index_data
    lda #'U'
    jsr append_body_op_for_current_proc
    jsr find_or_store_rt_f_to_i_external
    bcs emit_runtime_int_explicit_value_from_scan_y_or_fail_fail
    lda #'u'
    jsr append_body_op_for_current_proc
    jsr skip_inline_spaces_at_scan_y
    clc
    rts
emit_runtime_int_explicit_value_from_scan_y_or_fail_fail:
    sec
    rts

pack_expr_value_lo_as_positive_real_high_word:
    lda expr_value_lo
    ldx #$00
pack_expr_value_lo_as_positive_real_high_word_shift_loop:
    cmp #$80
    bcs pack_expr_value_lo_as_positive_real_high_word_shift_done
    asl a
    inx
    bne pack_expr_value_lo_as_positive_real_high_word_shift_loop
pack_expr_value_lo_as_positive_real_high_word_shift_done:
    sec
    sbc #$80
    sta compare_char
    txa
    eor #$07
    clc
    adc #127
    sta expr_saved_lo
    and #$01
    beq :+
    lda compare_char
    ora #$80
    sta compare_char
:   lda expr_saved_lo
    lsr a
    tay
    lda compare_char
    clc
    rts

.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
emit_real_literal_assignment_from_saved_indexes:
    ldx keyword_scan_ptr_lo_data
    lda #'p'
    jsr append_body_op_for_current_proc
    ldx keyword_scan_ptr_hi_data
    lda #'p'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'T'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'S'
    jsr append_body_op_for_current_proc
    clc
    rts

try_consume_real_open_from_scan_y:
    sty symbol_start_y_data
    jsr save_source_reader_mark
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'R'
    bne try_consume_real_open_from_scan_y_fail_restore
    jsr advance_scan_y
    bcs try_consume_real_open_from_scan_y_fail_restore
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'E'
    bne try_consume_real_open_from_scan_y_fail_restore
    jsr advance_scan_y
    bcs try_consume_real_open_from_scan_y_fail_restore
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'A'
    bne try_consume_real_open_from_scan_y_fail_restore
    jsr advance_scan_y
    bcs try_consume_real_open_from_scan_y_fail_restore
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'L'
    bne try_consume_real_open_from_scan_y_fail_restore
    jsr advance_scan_y
    bcs try_consume_real_open_from_scan_y_fail_restore
    lda (scan_ptr),y
    cmp #'('
    bne try_consume_real_open_from_scan_y_fail_restore
    jsr advance_scan_y
    bcs try_consume_real_open_from_scan_y_fail_restore
    jsr skip_inline_spaces_at_scan_y
    clc
    rts
try_consume_real_open_from_scan_y_fail_restore:
    jsr restore_source_reader_mark
    ldy symbol_start_y_data
    sec
    rts

emit_real_explicit_bridge_assignment_from_scan_y_or_fail:
    jsr find_var_index_from_scan_y
    bcs emit_real_explicit_bridge_assignment_from_scan_y_or_fail_fail
    stx real_lhs_index_data
    jsr require_var_index_real_bridge_word_or_fail
    bcs emit_real_explicit_bridge_assignment_from_scan_y_or_fail_fail
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne emit_real_explicit_bridge_assignment_from_scan_y_or_fail_fail
    jsr advance_scan_y
    bcs emit_real_explicit_bridge_assignment_from_scan_y_or_fail_fail
    jsr skip_inline_spaces_at_scan_y
    jsr require_line_end_at_scan_y
    bcs emit_real_explicit_bridge_assignment_from_scan_y_or_fail_fail
    jmp emit_real_bridge_assignment_from_var_index_ok
emit_real_explicit_bridge_assignment_from_scan_y_or_fail_fail:
    sec
    rts

emit_real_explicit_value_after_open_from_scan_y_or_fail:
    sty symbol_start_y_data
    jsr save_group_reader_mark
    jsr emit_real_explicit_bridge_assignment_from_scan_y_or_fail
    bcs :+
    clc
    rts
:
    jsr restore_group_reader_mark
    ldy symbol_start_y_data

    jsr parse_positive_word_sum_at_scan_y
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_wide
:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    beq :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_wide
:
    jsr advance_scan_y
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_wide
:
    jsr skip_inline_spaces_at_scan_y
    jsr require_line_end_at_scan_y
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_wide
:
    lda expr_value_hi
    bne emit_real_explicit_value_after_open_from_scan_y_or_fail_wide
    lda expr_value_lo
    beq emit_real_explicit_value_after_open_from_scan_y_or_fail_zero
    jsr store_zero_int_literal
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_fail
:
    stx keyword_scan_ptr_lo_data
    ldy #$00
    jsr store_word_literal_from_ay
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_fail
:
    stx keyword_scan_ptr_lo_data
    jsr find_or_store_rt_i_to_f_external
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_fail
:
    stx keyword_scan_ptr_hi_data
    ldx keyword_scan_ptr_lo_data
    lda #'p'
    jsr append_body_op_for_current_proc
    ldx keyword_scan_ptr_hi_data
    lda #'u'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'T'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'S'
    jsr append_body_op_for_current_proc
    clc
    rts
emit_real_explicit_value_after_open_from_scan_y_or_fail_zero:
    jsr store_zero_int_literal
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_fail
:
    stx keyword_scan_ptr_lo_data
    stx keyword_scan_ptr_hi_data
    jmp emit_real_literal_assignment_from_saved_indexes

emit_real_explicit_value_after_open_from_scan_y_or_fail_wide:
    jsr restore_group_reader_mark
    ldy symbol_start_y_data
    jsr parse_positive_word_sum_at_scan_y
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_signed
:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    beq :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_signed
:
    jsr advance_scan_y
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_signed
:
    jsr skip_inline_spaces_at_scan_y
    jsr require_line_end_at_scan_y
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_signed
:
    lda expr_value_lo
    ora expr_value_hi
    beq emit_real_explicit_value_after_open_from_scan_y_or_fail_zero
    lda expr_value_lo
    ldy expr_value_hi
    jsr store_word_literal_from_ay
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_fail
:
    stx keyword_scan_ptr_lo_data
    jsr find_or_store_rt_i_to_f_external
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_fail
:
    stx keyword_scan_ptr_hi_data
    ldx keyword_scan_ptr_lo_data
    lda #'p'
    jsr append_body_op_for_current_proc
    ldx keyword_scan_ptr_hi_data
    lda #'u'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'T'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'S'
    jsr append_body_op_for_current_proc
    clc
    rts

emit_real_explicit_value_after_open_from_scan_y_or_fail_signed:
    jsr restore_group_reader_mark
    ldy symbol_start_y_data
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'0'
    beq :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_fail
:
    jsr advance_scan_y
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_fail
:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'-'
    beq :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_fail
:
    jsr advance_scan_y
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_fail
:
    jsr parse_optional_grouped_positive_word_sum_at_scan_y
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_fail
:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    beq :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_fail
:
    jsr advance_scan_y
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_fail
:
    jsr skip_inline_spaces_at_scan_y
    jsr require_line_end_at_scan_y
    bcc :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_fail
:
    lda expr_value_lo
    ora expr_value_hi
    bne :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail_zero
:
    lda #$00
    sec
    sbc expr_value_lo
    sta expr_value_lo
    lda #$00
    sbc expr_value_hi
    sta expr_value_hi
    lda expr_value_lo
    ldy expr_value_hi
    jsr store_word_literal_from_ay
    bcs emit_real_explicit_value_after_open_from_scan_y_or_fail_fail
    stx keyword_scan_ptr_lo_data
    jsr find_or_store_rt_s_to_f_external
    bcs emit_real_explicit_value_after_open_from_scan_y_or_fail_fail
    stx keyword_scan_ptr_hi_data
    ldx keyword_scan_ptr_lo_data
    lda #'p'
    jsr append_body_op_for_current_proc
    ldx keyword_scan_ptr_hi_data
    lda #'u'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'T'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'S'
    jsr append_body_op_for_current_proc
    clc
    rts

emit_real_explicit_value_after_open_from_scan_y_or_fail_fail:
    sec
    rts

emit_real_explicit_value_assignment_from_scan_y_or_fail:
    jsr try_consume_real_open_from_scan_y
    bcs emit_real_explicit_value_assignment_from_scan_y_or_fail_fail
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail
emit_real_explicit_value_assignment_from_scan_y_or_fail_fail:
    sec
    rts
.endif

.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
emit_real_small_int_assignment_from_scan_y_or_fail:
    tya
    pha
    jsr save_group_reader_mark
    jsr parse_positive_word_sum_at_scan_y
    bcs emit_real_small_int_assignment_from_scan_y_or_fail_wide
    jsr skip_inline_spaces_at_scan_y
    jsr require_line_end_at_scan_y
    bcs emit_real_small_int_assignment_from_scan_y_or_fail_wide
    lda expr_value_hi
    bne emit_real_small_int_assignment_from_scan_y_or_fail_wide
    pla
    lda expr_value_lo
    beq emit_real_small_int_assignment_from_scan_y_or_fail_zero
    jsr store_zero_int_literal
    bcs emit_real_small_int_assignment_from_scan_y_or_fail_fail
    stx keyword_scan_ptr_lo_data
    jsr pack_expr_value_lo_as_positive_real_high_word
    jsr store_word_literal_from_ay
    bcs emit_real_small_int_assignment_from_scan_y_or_fail_fail
    stx keyword_scan_ptr_hi_data
    jmp emit_real_literal_assignment_from_saved_indexes
emit_real_small_int_assignment_from_scan_y_or_fail_zero:
    jsr store_zero_int_literal
    bcs emit_real_small_int_assignment_from_scan_y_or_fail_fail
    stx keyword_scan_ptr_lo_data
    stx keyword_scan_ptr_hi_data
    jmp emit_real_literal_assignment_from_saved_indexes
emit_real_small_int_assignment_from_scan_y_or_fail_wide:
    jsr restore_group_reader_mark
    pla
    tay
    jmp emit_real_wide_positive_int_assignment_from_scan_y_or_fail
emit_real_small_int_assignment_from_scan_y_or_fail_fail:
    sec
    rts

emit_real_wide_positive_int_assignment_from_scan_y_or_fail:
    tya
    pha
    jsr save_group_reader_mark
    jsr parse_positive_word_sum_at_scan_y
    bcs emit_real_wide_positive_int_assignment_from_scan_y_or_fail_signed
    jsr skip_inline_spaces_at_scan_y
    jsr require_line_end_at_scan_y
    bcs emit_real_wide_positive_int_assignment_from_scan_y_or_fail_signed
    pla
    lda expr_value_lo
    ora expr_value_hi
    beq emit_real_wide_positive_int_assignment_from_scan_y_or_fail_zero
    lda expr_value_lo
    ldy expr_value_hi
    jsr store_word_literal_from_ay
    bcs emit_real_wide_positive_int_assignment_from_scan_y_or_fail_fail
    stx keyword_scan_ptr_lo_data
    jsr find_or_store_rt_i_to_f_external
    bcs emit_real_wide_positive_int_assignment_from_scan_y_or_fail_fail
    stx keyword_scan_ptr_hi_data
    ldx keyword_scan_ptr_lo_data
    lda #'p'
    jsr append_body_op_for_current_proc
    ldx keyword_scan_ptr_hi_data
    lda #'u'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'T'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'S'
    jsr append_body_op_for_current_proc
    clc
    rts
emit_real_wide_positive_int_assignment_from_scan_y_or_fail_zero:
    jsr store_zero_int_literal
    bcs emit_real_wide_positive_int_assignment_from_scan_y_or_fail_fail
    stx keyword_scan_ptr_lo_data
    stx keyword_scan_ptr_hi_data
    jmp emit_real_literal_assignment_from_saved_indexes
emit_real_wide_positive_int_assignment_from_scan_y_or_fail_signed:
    jsr restore_group_reader_mark
    pla
    tay
    jmp emit_real_wide_signed_int_assignment_from_scan_y_or_fail
emit_real_wide_positive_int_assignment_from_scan_y_or_fail_fail:
    sec
    rts

emit_real_wide_signed_int_assignment_from_scan_y_or_fail:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'0'
    bne emit_real_wide_signed_int_assignment_from_scan_y_or_fail_fail
    jsr advance_scan_y
    bcs emit_real_wide_signed_int_assignment_from_scan_y_or_fail_fail
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'-'
    bne emit_real_wide_signed_int_assignment_from_scan_y_or_fail_fail
    jsr advance_scan_y
    bcs emit_real_wide_signed_int_assignment_from_scan_y_or_fail_fail
    jsr parse_optional_grouped_positive_word_sum_at_scan_y
    bcs emit_real_wide_signed_int_assignment_from_scan_y_or_fail_fail
    jsr skip_inline_spaces_at_scan_y
    jsr require_line_end_at_scan_y
    bcs emit_real_wide_signed_int_assignment_from_scan_y_or_fail_fail
    lda expr_value_lo
    ora expr_value_hi
    beq emit_real_wide_positive_int_assignment_from_scan_y_or_fail_zero
    lda #$00
    sec
    sbc expr_value_lo
    sta expr_value_lo
    lda #$00
    sbc expr_value_hi
    sta expr_value_hi
    lda expr_value_lo
    ldy expr_value_hi
    jsr store_word_literal_from_ay
    bcs emit_real_wide_signed_int_assignment_from_scan_y_or_fail_fail
    stx keyword_scan_ptr_lo_data
    jsr find_or_store_rt_s_to_f_external
    bcs emit_real_wide_signed_int_assignment_from_scan_y_or_fail_fail
    stx keyword_scan_ptr_hi_data
    ldx keyword_scan_ptr_lo_data
    lda #'p'
    jsr append_body_op_for_current_proc
    ldx keyword_scan_ptr_hi_data
    lda #'u'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'T'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'S'
    jsr append_body_op_for_current_proc
    clc
    rts
emit_real_wide_signed_int_assignment_from_scan_y_or_fail_fail:
    sec
    rts

emit_real_bridge_assignment_from_var_index_ok:
    ldx real_lhs_index_data
    lda #'L'
    jsr append_body_op_for_current_proc
    ldx real_lhs_index_data
    jsr find_or_store_real_bridge_external_from_x
    bcs emit_real_bridge_assignment_from_var_index_ok_fail
    lda #'u'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'T'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'S'
    jsr append_body_op_for_current_proc
    clc
    rts
emit_real_bridge_assignment_from_var_index_ok_fail:
    sec
    rts

emit_real_add_assignment_from_scan_y_or_fail:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'('
    bne :+
    jmp emit_real_small_int_assignment_from_scan_y_or_fail
:
    cmp #'0'
    bcc :+
    cmp #'9'+1
    bcs :+
    jmp emit_real_small_int_assignment_from_scan_y_or_fail
:
    jsr try_consume_real_open_from_scan_y
    bcs :+
    jmp emit_real_explicit_value_after_open_from_scan_y_or_fail
:
    jsr find_var_index_from_scan_y
    bcc :+
    jmp emit_real_add_assignment_from_scan_y_or_fail_fail
:   stx real_lhs_index_data
    jsr skip_inline_spaces_at_scan_y
    jsr require_line_end_at_scan_y
    bcs emit_real_add_assignment_after_copy_check
    ldx real_lhs_index_data
    jsr require_var_index_real_or_fail
    bcc emit_real_add_assignment_copy
    ldx real_lhs_index_data
    jsr require_var_index_real_bridge_word_or_fail
    bcc emit_real_add_assignment_bridge
    jmp emit_real_add_assignment_from_scan_y_or_fail_fail
emit_real_add_assignment_copy:
    jmp emit_real_copy_assignment_from_scan_y_ok
emit_real_add_assignment_bridge:
    jmp emit_real_bridge_assignment_from_var_index_ok
emit_real_add_assignment_after_copy_check:
    ldx real_lhs_index_data
    jsr require_var_index_real_or_fail
    bcc :+
    jmp emit_real_add_assignment_from_scan_y_or_fail_fail
:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'+'
    beq :+
    cmp #'-'
    beq :+
    cmp #'*'
    beq :+
    cmp #'/'
    beq :+
    jmp emit_real_add_assignment_from_scan_y_or_fail_fail
:   sta real_operator_data
    jsr advance_scan_y
    jsr skip_inline_spaces_at_scan_y
    jsr find_var_index_from_scan_y
    bcc :+
    jmp emit_real_add_assignment_from_scan_y_or_fail_fail
:   jsr require_var_index_real_or_fail
    bcc :+
    jmp emit_real_add_assignment_from_scan_y_or_fail_fail
:   stx real_rhs_index_data
    jsr require_line_end_at_scan_y
    bcc :+
    jmp emit_real_add_assignment_from_scan_y_or_fail_fail
:   ldx real_lhs_index_data
    lda #'L'
    jsr append_body_op_for_current_proc
    ldx real_lhs_index_data
    lda #'U'
    jsr append_body_op_for_current_proc
    ldx real_rhs_index_data
    lda #'L'
    jsr append_body_op_for_current_proc
    ldx real_rhs_index_data
    lda #'U'
    jsr append_body_op_for_current_proc
    jsr find_or_store_real_operator_external
    bcc :+
    jmp emit_real_add_assignment_from_scan_y_or_fail_fail
:   lda #'u'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'T'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'S'
    jsr append_body_op_for_current_proc
    clc
    rts
emit_real_copy_assignment_from_scan_y_ok:
    ldx real_lhs_index_data
    lda #'L'
    jsr append_body_op_for_current_proc
    ldx real_lhs_index_data
    lda #'U'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'T'
    jsr append_body_op_for_current_proc
    ldx assignment_target_index_data
    lda #'S'
    jsr append_body_op_for_current_proc
    clc
    rts
emit_real_zero_assignment_from_scan_y_or_fail:
    jsr store_zero_int_literal
    bcs emit_real_add_assignment_from_scan_y_or_fail_fail
    stx keyword_scan_ptr_lo_data
    jsr advance_scan_y
    bcs emit_real_add_assignment_from_scan_y_or_fail_fail
    jsr require_line_end_at_scan_y
    bcs emit_real_add_assignment_from_scan_y_or_fail_fail
    lda keyword_scan_ptr_lo_data
    sta keyword_scan_ptr_hi_data
    jmp emit_real_literal_assignment_from_saved_indexes
emit_real_add_assignment_from_scan_y_or_fail_fail:
    sec
    rts
.endif

resolve_call_target_from_declared_or_fail:
    jsr find_export_index_from_declared
    bcc resolve_call_target_from_declared_or_fail_local
    jsr find_or_store_builtin_runtime_external_from_declared
    bcs :+
    stx call_target_index_data
    lda #'u'
    sta call_target_kind
    clc
    rts
:
    jsr find_or_store_external_from_declared
    bcs resolve_call_target_from_declared_or_fail_fail
    stx call_target_index_data
    lda #'u'
    sta call_target_kind
    lda #$FF
    sta call_expected_arg_count
    clc
    rts
resolve_call_target_from_declared_or_fail_local:
    cpx current_proc_index_data
    beq resolve_call_target_from_declared_or_fail_fail
    stx call_target_index_data
    lda #'c'
    sta call_target_kind
.if ACTC_REU_PROC_META
    jsr load_proc_meta_from_reu_x
    lda proc_meta_param_count_data
.else
    lda proc_param_count_data,x
.endif
    sta call_expected_arg_count
    clc
    rts
resolve_call_target_from_declared_or_fail_fail:
    sec
    rts

emit_call_args_from_scan_y_or_fail:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'('
    beq :+
    sec
    rts
:   jsr advance_scan_y
    lda #$00
    sta call_arg_count_data
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    beq emit_call_args_from_scan_y_or_fail_done
emit_call_args_from_scan_y_or_fail_loop:
    lda call_arg_count_data
    pha
    lda call_expected_arg_count
    pha
    lda call_target_index_data
    pha
    lda call_target_kind
    pha
    jsr emit_runtime_value_from_scan_y_or_fail
    bcc emit_call_args_from_scan_y_or_fail_restore_ok
    pla
    sta call_target_kind
    pla
    sta call_target_index_data
    pla
    sta call_expected_arg_count
    pla
    sta call_arg_count_data
    sec
    rts
emit_call_args_from_scan_y_or_fail_restore_ok:
    pla
    sta call_target_kind
    pla
    sta call_target_index_data
    pla
    sta call_expected_arg_count
    pla
    sta call_arg_count_data
    inc call_arg_count_data
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #','
    beq emit_call_args_from_scan_y_or_fail_next
    cmp #')'
    beq emit_call_args_from_scan_y_or_fail_done
    sec
    rts
emit_call_args_from_scan_y_or_fail_next:
    jsr advance_scan_y
    jsr skip_inline_spaces_at_scan_y
    jmp emit_call_args_from_scan_y_or_fail_loop
emit_call_args_from_scan_y_or_fail_done:
    jsr advance_scan_y
    lda call_expected_arg_count
    cmp #$FF
    beq emit_call_args_from_scan_y_or_fail_ok
    lda call_arg_count_data
    cmp call_expected_arg_count
    bne emit_call_args_from_scan_y_or_fail_fail
emit_call_args_from_scan_y_or_fail_ok:
    clc
    rts
emit_call_args_from_scan_y_or_fail_fail:
    sec
    rts

emit_runtime_value_from_scan_y_or_fail:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'='
    bne emit_runtime_value_from_scan_y_or_fail_after_equals
    jsr advance_scan_y
    bcc emit_runtime_value_from_scan_y_or_fail_after_equals
    jmp emit_runtime_expr_push_fail
emit_runtime_value_from_scan_y_or_fail_after_equals:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'['
    bne emit_runtime_value_from_scan_y_or_fail_after_group
    jsr advance_scan_y
    bcc :+
    jmp emit_runtime_expr_push_fail
:   jsr emit_runtime_value_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
:   jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #']'
    beq :+
    jmp emit_runtime_expr_push_fail
:   jsr advance_scan_y
    bcc :+
    jmp emit_runtime_expr_push_fail
:   clc
    rts
emit_runtime_value_from_scan_y_or_fail_after_group:
    lda (scan_ptr),y
    cmp #'('
    bne :+
    jsr scan_value_expr_for_top_level_arith_from_scan_y
    bcc emit_runtime_value_from_scan_y_or_fail_sum
:
    jsr scan_value_expr_for_bool_tokens_from_scan_y
    bcc emit_runtime_value_from_scan_y_or_fail_bool
emit_runtime_value_from_scan_y_or_fail_sum:
    jmp emit_runtime_sum_from_scan_y_or_fail
emit_runtime_value_from_scan_y_or_fail_bool:
    lda #$00
    sta bool_ops_used_data
    jmp emit_runtime_bool_or_from_scan_y_or_fail

scan_value_expr_for_top_level_arith_from_scan_y:
    sty symbol_start_y_data
    jsr save_source_reader_mark
    lda #$00
    sta hex_work
scan_value_expr_for_top_level_arith_from_scan_y_loop:
    lda (scan_ptr),y
    beq scan_value_expr_for_top_level_arith_from_scan_y_not_found
    cmp #10
    beq scan_value_expr_for_top_level_arith_from_scan_y_not_found
    cmp #13
    beq scan_value_expr_for_top_level_arith_from_scan_y_not_found
    cmp #','
    beq scan_value_expr_for_top_level_arith_from_scan_y_comma
    cmp #')'
    beq scan_value_expr_for_top_level_arith_from_scan_y_rparen
    cmp #'('
    beq scan_value_expr_for_top_level_arith_from_scan_y_lparen
    ldx hex_work
    bne scan_value_expr_for_top_level_arith_from_scan_y_next
    cmp #'+'
    beq scan_value_expr_for_top_level_arith_from_scan_y_found
    cmp #'-'
    beq scan_value_expr_for_top_level_arith_from_scan_y_found
    cmp #'*'
    beq scan_value_expr_for_top_level_arith_from_scan_y_found
    cmp #'/'
    beq scan_value_expr_for_top_level_arith_from_scan_y_found
scan_value_expr_for_top_level_arith_from_scan_y_next:
    jsr advance_scan_y
    bcc scan_value_expr_for_top_level_arith_from_scan_y_loop
scan_value_expr_for_top_level_arith_from_scan_y_not_found:
    jsr restore_source_reader_mark
    ldy symbol_start_y_data
    sec
    rts
scan_value_expr_for_top_level_arith_from_scan_y_comma:
    lda hex_work
    beq scan_value_expr_for_top_level_arith_from_scan_y_not_found
    jsr advance_scan_y
    bcc :+
    jmp scan_value_expr_for_top_level_arith_from_scan_y_not_found
:
    jmp scan_value_expr_for_top_level_arith_from_scan_y_loop
scan_value_expr_for_top_level_arith_from_scan_y_rparen:
    lda hex_work
    beq scan_value_expr_for_top_level_arith_from_scan_y_not_found
    dec hex_work
    jsr advance_scan_y
    bcc :+
    jmp scan_value_expr_for_top_level_arith_from_scan_y_not_found
:
    jmp scan_value_expr_for_top_level_arith_from_scan_y_loop
scan_value_expr_for_top_level_arith_from_scan_y_lparen:
    inc hex_work
    jsr advance_scan_y
    bcc :+
    jmp scan_value_expr_for_top_level_arith_from_scan_y_not_found
:
    jmp scan_value_expr_for_top_level_arith_from_scan_y_loop
scan_value_expr_for_top_level_arith_from_scan_y_found:
    jsr restore_source_reader_mark
    ldy symbol_start_y_data
    clc
    rts

.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
scan_print_expr_for_bool_keywords_from_scan_y:
    sty symbol_start_y_data
    jsr save_source_reader_mark
    lda #$00
    sta hex_work
scan_print_expr_for_bool_keywords_from_scan_y_loop:
    lda (scan_ptr),y
    beq scan_print_expr_for_bool_keywords_from_scan_y_not_found
    cmp #10
    beq scan_print_expr_for_bool_keywords_from_scan_y_not_found
    cmp #13
    beq scan_print_expr_for_bool_keywords_from_scan_y_not_found
    cmp #')'
    beq scan_print_expr_for_bool_keywords_from_scan_y_rparen
    cmp #'('
    beq scan_print_expr_for_bool_keywords_from_scan_y_lparen
    jsr uppercase_ascii
    cmp #'A'
    beq scan_print_expr_for_bool_keywords_from_scan_y_try_and
    cmp #'O'
    beq scan_print_expr_for_bool_keywords_from_scan_y_try_or
    cmp #'N'
    beq scan_print_expr_for_bool_keywords_from_scan_y_try_not
scan_print_expr_for_bool_keywords_from_scan_y_next:
    jsr advance_scan_y
    bcc scan_print_expr_for_bool_keywords_from_scan_y_loop
    jmp scan_print_expr_for_bool_keywords_from_scan_y_found
scan_print_expr_for_bool_keywords_from_scan_y_not_found:
    jsr restore_source_reader_mark
    ldy symbol_start_y_data
    sec
    rts
scan_print_expr_for_bool_keywords_from_scan_y_rparen:
    lda hex_work
    beq scan_print_expr_for_bool_keywords_from_scan_y_not_found
    dec hex_work
    jsr advance_scan_y
    bcc :+
    jmp scan_print_expr_for_bool_keywords_from_scan_y_found
:
    jmp scan_print_expr_for_bool_keywords_from_scan_y_loop
scan_print_expr_for_bool_keywords_from_scan_y_lparen:
    inc hex_work
    jsr advance_scan_y
    bcc :+
    jmp scan_print_expr_for_bool_keywords_from_scan_y_found
:
    jmp scan_print_expr_for_bool_keywords_from_scan_y_loop
scan_print_expr_for_bool_keywords_from_scan_y_try_and:
    jmp scan_print_expr_for_bool_keywords_from_scan_y_found
scan_print_expr_for_bool_keywords_from_scan_y_try_or:
    jmp scan_print_expr_for_bool_keywords_from_scan_y_found
scan_print_expr_for_bool_keywords_from_scan_y_try_not:
    jmp scan_print_expr_for_bool_keywords_from_scan_y_found
scan_print_expr_for_bool_keywords_from_scan_y_found:
    jsr restore_source_reader_mark
    ldy symbol_start_y_data
    clc
    rts
.endif

scan_value_expr_for_bool_tokens_from_scan_y:
    sty symbol_start_y_data
    jsr save_source_reader_mark
    lda #$00
    sta hex_work
scan_value_expr_for_bool_tokens_from_scan_y_loop:
    lda (scan_ptr),y
    beq scan_value_expr_for_bool_tokens_from_scan_y_not_found
    cmp #10
    beq scan_value_expr_for_bool_tokens_from_scan_y_not_found
    cmp #13
    beq scan_value_expr_for_bool_tokens_from_scan_y_not_found
    cmp #','
    beq scan_value_expr_for_bool_tokens_from_scan_y_comma
    cmp #')'
    beq scan_value_expr_for_bool_tokens_from_scan_y_rparen
    cmp #'('
    beq scan_value_expr_for_bool_tokens_from_scan_y_lparen
    cmp #'='
    beq scan_value_expr_for_bool_tokens_from_scan_y_found
    cmp #'<'
    beq scan_value_expr_for_bool_tokens_from_scan_y_found
    cmp #'>'
    beq scan_value_expr_for_bool_tokens_from_scan_y_found
    jsr uppercase_ascii
    cmp #'A'
    beq scan_value_expr_for_bool_tokens_from_scan_y_try_and
    cmp #'O'
    beq scan_value_expr_for_bool_tokens_from_scan_y_try_or
    cmp #'N'
    beq scan_value_expr_for_bool_tokens_from_scan_y_try_not
scan_value_expr_for_bool_tokens_from_scan_y_next:
    jsr advance_scan_y
    bcc scan_value_expr_for_bool_tokens_from_scan_y_loop
    jmp scan_value_expr_for_bool_tokens_from_scan_y_found
scan_value_expr_for_bool_tokens_from_scan_y_not_found:
    jsr restore_source_reader_mark
    ldy symbol_start_y_data
    sec
    rts
scan_value_expr_for_bool_tokens_from_scan_y_comma:
    lda hex_work
    beq scan_value_expr_for_bool_tokens_from_scan_y_not_found
    jsr advance_scan_y
    bcc :+
    jmp scan_value_expr_for_bool_tokens_from_scan_y_found
:
    jmp scan_value_expr_for_bool_tokens_from_scan_y_loop
scan_value_expr_for_bool_tokens_from_scan_y_rparen:
    lda hex_work
    beq scan_value_expr_for_bool_tokens_from_scan_y_not_found
    dec hex_work
    jsr advance_scan_y
    bcc :+
    jmp scan_value_expr_for_bool_tokens_from_scan_y_found
:
    jmp scan_value_expr_for_bool_tokens_from_scan_y_loop
scan_value_expr_for_bool_tokens_from_scan_y_lparen:
    inc hex_work
    jsr advance_scan_y
    bcc :+
    jmp scan_value_expr_for_bool_tokens_from_scan_y_found
:
    jmp scan_value_expr_for_bool_tokens_from_scan_y_loop
scan_value_expr_for_bool_tokens_from_scan_y_try_and:
    jmp scan_value_expr_for_bool_tokens_from_scan_y_found
scan_value_expr_for_bool_tokens_from_scan_y_try_or:
    jmp scan_value_expr_for_bool_tokens_from_scan_y_found
scan_value_expr_for_bool_tokens_from_scan_y_try_not:
    jmp scan_value_expr_for_bool_tokens_from_scan_y_found
scan_value_expr_for_bool_tokens_from_scan_y_found:
    jsr restore_source_reader_mark
    ldy symbol_start_y_data
    clc
    rts

emit_runtime_bool_or_from_scan_y_or_fail:
    jsr emit_runtime_bool_and_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
:
emit_runtime_bool_or_from_scan_y_or_fail_loop:
    jsr consume_or_keyword_from_scan_y
    bcs emit_runtime_bool_or_from_scan_y_or_fail_done
    lda #$01
    sta bool_ops_used_data
    jsr normalize_runtime_top_to_bool_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
:
    jsr emit_runtime_bool_and_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
:
    jsr normalize_runtime_top_to_bool_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
:
    lda #'a'
    jsr append_body_op_no_arg_for_current_proc
    lda #$00
    sta expr_value_lo
    jsr store_expr_value_as_int_literal
    bcc :+
    jmp emit_runtime_expr_push_fail
:
    lda #'p'
    jsr append_body_op_for_current_proc
    lda #'g'
    jsr append_body_op_no_arg_for_current_proc
    jmp emit_runtime_bool_or_from_scan_y_or_fail_loop
emit_runtime_bool_or_from_scan_y_or_fail_done:
    clc
    rts

emit_runtime_bool_and_from_scan_y_or_fail:
    jsr emit_runtime_bool_not_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
:
emit_runtime_bool_and_from_scan_y_or_fail_loop:
    jsr consume_and_keyword_from_scan_y
    bcs emit_runtime_bool_and_from_scan_y_or_fail_done
    lda #$01
    sta bool_ops_used_data
    jsr normalize_runtime_top_to_bool_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
:
    jsr emit_runtime_bool_not_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
:
    jsr normalize_runtime_top_to_bool_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
:
    lda #'a'
    jsr append_body_op_no_arg_for_current_proc
    lda #$01
    sta expr_value_lo
    jsr store_expr_value_as_int_literal
    bcc :+
    jmp emit_runtime_expr_push_fail
:
    lda #'p'
    jsr append_body_op_for_current_proc
    lda #'g'
    jsr append_body_op_no_arg_for_current_proc
    jmp emit_runtime_bool_and_from_scan_y_or_fail_loop
emit_runtime_bool_and_from_scan_y_or_fail_done:
    clc
    rts

emit_runtime_bool_not_from_scan_y_or_fail:
    jsr consume_not_keyword_from_scan_y
    bcs emit_runtime_bool_primary_from_scan_y_or_fail
    lda #$01
    sta bool_ops_used_data
    jsr emit_runtime_bool_not_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
:
    jsr normalize_runtime_top_to_bool_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
:
    lda #$00
    sta expr_value_lo
    jsr store_expr_value_as_int_literal
    bcc :+
    jmp emit_runtime_expr_push_fail
:
    lda #'p'
    jsr append_body_op_for_current_proc
    lda #'q'
    jsr append_body_op_no_arg_for_current_proc
    clc
    rts

emit_runtime_bool_primary_from_scan_y_or_fail:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'('
    beq :+
    jmp emit_runtime_condition_clause_from_scan_y_or_fail
:
    tya
    pha
    jsr save_group_reader_mark
    jsr advance_scan_y
    jsr emit_runtime_bool_or_from_scan_y_or_fail
    bcs emit_runtime_bool_primary_restore_clause
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne emit_runtime_bool_primary_restore_clause
    jsr advance_scan_y
    sty compare_char
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'='
    beq emit_runtime_bool_primary_restore_clause
    cmp #'<'
    beq emit_runtime_bool_primary_restore_clause
    cmp #'>'
    beq emit_runtime_bool_primary_restore_clause
    ldy compare_char
    pla
    clc
    rts
emit_runtime_bool_primary_restore_clause:
    jsr restore_group_reader_mark
    pla
    tay
    jmp emit_runtime_condition_clause_from_scan_y_or_fail

.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
emit_runtime_real_push_literal_from_saved_indexes:
    ldx keyword_scan_ptr_lo_data
    lda #'p'
    jsr append_body_op_for_current_proc
    ldx keyword_scan_ptr_hi_data
    lda #'p'
    jsr append_body_op_for_current_proc
    clc
    rts

try_consume_real_open_for_runtime_condition_from_scan_y:
    sty symbol_start_y_data
    jsr save_source_reader_mark
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'R'
    bne try_consume_real_open_for_runtime_condition_from_scan_y_fail_restore
    jsr advance_scan_y
    bcs try_consume_real_open_for_runtime_condition_from_scan_y_fail_restore
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'E'
    bne try_consume_real_open_for_runtime_condition_from_scan_y_fail_restore
    jsr advance_scan_y
    bcs try_consume_real_open_for_runtime_condition_from_scan_y_fail_restore
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'A'
    bne try_consume_real_open_for_runtime_condition_from_scan_y_fail_restore
    jsr advance_scan_y
    bcs try_consume_real_open_for_runtime_condition_from_scan_y_fail_restore
    lda (scan_ptr),y
    jsr uppercase_ascii
    cmp #'L'
    bne try_consume_real_open_for_runtime_condition_from_scan_y_fail_restore
    jsr advance_scan_y
    bcs try_consume_real_open_for_runtime_condition_from_scan_y_fail_restore
    lda (scan_ptr),y
    cmp #'('
    bne try_consume_real_open_for_runtime_condition_from_scan_y_fail_restore
    jsr advance_scan_y
    bcs try_consume_real_open_for_runtime_condition_from_scan_y_fail_restore
    jsr skip_inline_spaces_at_scan_y
    clc
    rts
try_consume_real_open_for_runtime_condition_from_scan_y_fail_restore:
    jsr restore_source_reader_mark
    ldy symbol_start_y_data
    sec
    rts

emit_runtime_real_explicit_bridge_value_from_scan_y_or_fail:
    jsr copy_symbol_from_scan_y
    bcs emit_runtime_real_explicit_bridge_value_from_scan_y_or_fail_fail
    sty symbol_end_y_data
    jsr find_var_index_from_declared
    bcs emit_runtime_real_explicit_bridge_value_from_scan_y_or_fail_fail
    stx real_lhs_index_data
    jsr require_var_index_real_bridge_word_or_fail
    bcs emit_runtime_real_explicit_bridge_value_from_scan_y_or_fail_fail
    ldy symbol_end_y_data
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne emit_runtime_real_explicit_bridge_value_from_scan_y_or_fail_fail
    jsr advance_scan_y
    bcs emit_runtime_real_explicit_bridge_value_from_scan_y_or_fail_fail
    ldx real_lhs_index_data
    lda #'L'
    jsr append_body_op_for_current_proc
    ldx real_lhs_index_data
    sty symbol_start_y_data
    jsr find_or_store_real_bridge_external_from_x
    bcs emit_runtime_real_explicit_bridge_value_from_scan_y_or_fail_fail
    ldy symbol_start_y_data
    lda #'u'
    jsr append_body_op_for_current_proc
    jsr skip_inline_spaces_at_scan_y
    clc
    rts
emit_runtime_real_explicit_bridge_value_from_scan_y_or_fail_fail:
    sec
    rts

emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail:
    sty symbol_start_y_data
    jsr save_group_reader_mark
    jsr emit_runtime_real_explicit_bridge_value_from_scan_y_or_fail
    bcc :+
    jsr restore_group_reader_mark
    ldy symbol_start_y_data
    jsr parse_positive_word_sum_at_scan_y
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_wide
:   jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    beq :+
    jmp emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_wide
:   jsr advance_scan_y
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_wide
:   jsr skip_inline_spaces_at_scan_y
    lda expr_value_hi
    bne emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_wide
    lda expr_value_lo
    beq emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_zero
    jsr store_zero_int_literal
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_fail
:   stx keyword_scan_ptr_lo_data
    ldy #$00
    jsr store_word_literal_from_ay
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_fail
:   stx keyword_scan_ptr_lo_data
    sty symbol_end_y_data
    jsr find_or_store_rt_i_to_f_external
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_fail
:   stx keyword_scan_ptr_hi_data
    ldy symbol_end_y_data
    ldx keyword_scan_ptr_lo_data
    lda #'p'
    jsr append_body_op_for_current_proc
    ldx keyword_scan_ptr_hi_data
    lda #'u'
    jsr append_body_op_for_current_proc
    jsr skip_inline_spaces_at_scan_y
    clc
    rts
emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_zero:
    jsr store_zero_int_literal
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_fail
:   stx keyword_scan_ptr_lo_data
    stx keyword_scan_ptr_hi_data
    jmp emit_runtime_real_push_literal_from_saved_indexes

emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_wide:
    jsr restore_group_reader_mark
    ldy symbol_start_y_data
    jsr parse_positive_word_sum_at_scan_y
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_signed
:   jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    beq :+
    jmp emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_signed
:   jsr advance_scan_y
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_signed
:   jsr skip_inline_spaces_at_scan_y
    lda expr_value_lo
    ora expr_value_hi
    beq emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_zero
    lda expr_value_lo
    ldy expr_value_hi
    jsr store_word_literal_from_ay
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_fail
:   stx keyword_scan_ptr_lo_data
    sty symbol_end_y_data
    jsr find_or_store_rt_i_to_f_external
    bcc :+
    jmp emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_fail
:   stx keyword_scan_ptr_hi_data
    ldy symbol_end_y_data
    ldx keyword_scan_ptr_lo_data
    lda #'p'
    jsr append_body_op_for_current_proc
    ldx keyword_scan_ptr_hi_data
    lda #'u'
    jsr append_body_op_for_current_proc
    jsr skip_inline_spaces_at_scan_y
    clc
    rts

emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_signed:
    jsr restore_group_reader_mark
    ldy symbol_start_y_data
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'0'
    bne emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_fail
    jsr advance_scan_y
    bcs emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_fail
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'-'
    bne emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_fail
    jsr advance_scan_y
    bcs emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_fail
    jsr parse_optional_grouped_positive_word_sum_at_scan_y
    bcs emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_fail
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_fail
    jsr advance_scan_y
    bcs emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_fail
    jsr skip_inline_spaces_at_scan_y
    lda expr_value_lo
    ora expr_value_hi
    bne :+
    jmp emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_zero
:
    lda #$00
    sec
    sbc expr_value_lo
    sta expr_value_lo
    lda #$00
    sbc expr_value_hi
    sta expr_value_hi
    lda expr_value_lo
    ldy expr_value_hi
    jsr store_word_literal_from_ay
    bcs emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_fail
    stx keyword_scan_ptr_lo_data
    sty symbol_end_y_data
    jsr find_or_store_rt_s_to_f_external
    bcs emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_fail
    stx keyword_scan_ptr_hi_data
    ldy symbol_end_y_data
    ldx keyword_scan_ptr_lo_data
    lda #'p'
    jsr append_body_op_for_current_proc
    ldx keyword_scan_ptr_hi_data
    lda #'u'
    jsr append_body_op_for_current_proc
    jsr skip_inline_spaces_at_scan_y
    clc
    rts

emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail_fail:
    sec
    rts
.endif

emit_runtime_real_value_from_scan_y_or_fail:
    jsr skip_inline_spaces_at_scan_y
.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
    jsr try_consume_real_open_for_runtime_condition_from_scan_y
    bcs :+
    jmp emit_runtime_real_explicit_value_after_open_from_scan_y_or_fail
:
.endif
    jsr copy_symbol_from_scan_y
    bcs emit_runtime_real_value_from_scan_y_or_fail_fail
    sty symbol_end_y_data
    jsr find_var_index_from_declared
    bcs emit_runtime_real_value_from_scan_y_or_fail_fail
    stx real_lhs_index_data
    jsr require_var_index_real_or_fail
    bcs emit_runtime_real_value_from_scan_y_or_fail_fail
    ldy symbol_end_y_data
    ldx real_lhs_index_data
    lda #'L'
    jsr append_body_op_for_current_proc
    ldx real_lhs_index_data
    lda #'U'
    jsr append_body_op_for_current_proc
    jsr skip_inline_spaces_at_scan_y
    clc
    rts
emit_runtime_real_value_from_scan_y_or_fail_fail:
    sec
    rts

emit_runtime_real_condition_clause_from_scan_y_or_fail:
    jsr emit_runtime_real_value_from_scan_y_or_fail
    bcc :+
    sec
    rts
:   lda (scan_ptr),y
    sta expr_compare_lo
    cmp #'='
    beq emit_runtime_real_condition_clause_eq
    cmp #'<'
    beq emit_runtime_real_condition_clause_lt_entry
    cmp #'>'
    beq emit_runtime_real_condition_clause_gt_entry
    sec
    rts
emit_runtime_real_condition_clause_eq:
    lda #'q'
    sta expr_runtime_op
    lda #$01
    sta expr_value_lo
    jsr advance_scan_y
    jmp emit_runtime_real_condition_clause_rhs
emit_runtime_real_condition_clause_lt_entry:
    jsr advance_scan_y
    lda (scan_ptr),y
    cmp #'>'
    beq emit_runtime_real_condition_clause_ne
    cmp #'='
    beq emit_runtime_real_condition_clause_le
    lda #'l'
    sta expr_runtime_op
    lda #$01
    sta expr_value_lo
    jmp emit_runtime_real_condition_clause_rhs
emit_runtime_real_condition_clause_gt_entry:
    jsr advance_scan_y
    lda (scan_ptr),y
    cmp #'='
    beq emit_runtime_real_condition_clause_ge
    lda #'g'
    sta expr_runtime_op
    lda #$01
    sta expr_value_lo
    jmp emit_runtime_real_condition_clause_rhs
emit_runtime_real_condition_clause_ne:
    lda #'n'
    sta expr_runtime_op
    lda #$01
    sta expr_value_lo
    jsr advance_scan_y
    jmp emit_runtime_real_condition_clause_rhs
emit_runtime_real_condition_clause_le:
    lda #'l'
    sta expr_runtime_op
    lda #$02
    sta expr_value_lo
    jsr advance_scan_y
    jmp emit_runtime_real_condition_clause_rhs
emit_runtime_real_condition_clause_ge:
    lda #'g'
    sta expr_runtime_op
    lda #$00
    sta expr_value_lo
    jsr advance_scan_y
emit_runtime_real_condition_clause_rhs:
    jsr emit_runtime_real_value_from_scan_y_or_fail
    bcc :+
    sec
    rts
:   sty symbol_start_y_data
    jsr find_or_store_rt_f_cmp_external
    bcc :+
    sec
    rts
:   ldy symbol_start_y_data
    lda #'u'
    jsr append_body_op_for_current_proc
    lda expr_value_lo
    beq :+
    jsr store_expr_value_as_int_literal
    bcc :++
    sec
    rts
:   jsr store_zero_int_literal
    bcc :+
    sec
    rts
:   lda #'p'
    jsr append_body_op_for_current_proc
    lda expr_runtime_op
    jsr append_body_op_no_arg_for_current_proc
    clc
    rts

emit_runtime_condition_clause_from_scan_y_or_fail:
    sty expr_saved_y_data
    jsr save_condition_reader_mark
    jsr emit_runtime_real_condition_clause_from_scan_y_or_fail
    bcs :+
    jmp emit_runtime_condition_clause_real_done
:
    jsr restore_condition_reader_mark
    ldy expr_saved_y_data
    jsr emit_runtime_sum_from_scan_y_or_fail
    bcc :+
    sec
    rts
:   jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    sta expr_compare_lo
    cmp #'='
    beq emit_runtime_condition_clause_compare_entry
    cmp #'<'
    beq emit_runtime_condition_clause_compare_entry
    cmp #'>'
    beq emit_runtime_condition_clause_compare_entry
    jmp emit_runtime_condition_clause_done
emit_runtime_condition_clause_compare_entry:
    lda #$00
    sta expr_runtime_post_zero
    lda expr_compare_lo
    cmp #'='
    beq emit_runtime_condition_clause_eq
    cmp #'<'
    beq emit_runtime_condition_clause_lt_entry
    cmp #'>'
    beq emit_runtime_condition_clause_gt_entry
    sec
    rts
emit_runtime_condition_clause_eq:
    lda #'q'
    sta expr_runtime_op
    jsr advance_scan_y
    jmp emit_runtime_condition_clause_rhs
emit_runtime_condition_clause_lt_entry:
    jsr advance_scan_y
    lda (scan_ptr),y
    cmp #'>'
    beq emit_runtime_condition_clause_ne
    cmp #'='
    beq emit_runtime_condition_clause_le
    lda #'l'
    sta expr_runtime_op
    jmp emit_runtime_condition_clause_rhs
emit_runtime_condition_clause_gt_entry:
    jsr advance_scan_y
    lda (scan_ptr),y
    cmp #'='
    beq emit_runtime_condition_clause_ge
    lda #'g'
    sta expr_runtime_op
    jmp emit_runtime_condition_clause_rhs
emit_runtime_condition_clause_le:
    lda #'g'
    sta expr_runtime_op
    lda #$01
    sta expr_runtime_post_zero
    jsr advance_scan_y
    jmp emit_runtime_condition_clause_rhs
emit_runtime_condition_clause_ge:
    lda #'l'
    sta expr_runtime_op
    lda #$01
    sta expr_runtime_post_zero
    jsr advance_scan_y
    jmp emit_runtime_condition_clause_rhs
emit_runtime_condition_clause_ne:
    lda #'n'
    sta expr_runtime_op
    jsr advance_scan_y
emit_runtime_condition_clause_rhs:
    jsr emit_runtime_sum_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
:
    lda expr_runtime_op
    jsr append_body_op_no_arg_for_current_proc
    lda expr_runtime_post_zero
    beq emit_runtime_condition_clause_done
    lda #$00
    sta expr_value_lo
    jsr store_expr_value_as_int_literal
    bcc :+
    jmp emit_runtime_expr_push_fail
:
    lda #'p'
    jsr append_body_op_for_current_proc
    lda #'q'
    jsr append_body_op_no_arg_for_current_proc
emit_runtime_condition_clause_done:
    clc
    rts
emit_runtime_condition_clause_real_done:
    clc
    rts

normalize_runtime_top_to_bool_or_fail:
    lda #$00
    sta expr_value_lo
    jsr store_expr_value_as_int_literal
    bcc :+
    jmp emit_runtime_expr_push_fail
:
    lda #'p'
    jsr append_body_op_for_current_proc
    lda #'n'
    jsr append_body_op_no_arg_for_current_proc
    clc
    rts

emit_runtime_sum_from_scan_y_or_fail:
    jsr emit_runtime_term_push_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
:
emit_runtime_sum_from_scan_y_loop:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'+'
    beq emit_runtime_sum_from_scan_y_add
    cmp #'-'
    beq emit_runtime_sum_from_scan_y_sub
    clc
    rts
emit_runtime_sum_from_scan_y_add:
    jsr advance_scan_y
    jsr emit_runtime_term_push_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
:
    lda #'a'
    jsr append_body_op_no_arg_for_current_proc
    jmp emit_runtime_sum_from_scan_y_loop
emit_runtime_sum_from_scan_y_sub:
    jsr advance_scan_y
    jsr emit_runtime_term_push_from_scan_y_or_fail
    bcc :+
    jmp emit_runtime_expr_push_fail
:
    lda #'m'
    jsr append_body_op_no_arg_for_current_proc
    jmp emit_runtime_sum_from_scan_y_loop

store_expr_value_as_int_literal:
    ldx int_count_data
    cpx #INT_LITERAL_MAX
    bcc :+
    sec
    rts
:   lda expr_value_lo
.if ACTC_REU_INT_LITERALS
    sta int_literal_lo_data
    lda #$00
    sta int_literal_hi_data
    jsr store_int_literal_to_reu_x
.else
    lda expr_value_lo
    sta int_values_lo,x
    lda #$00
    sta int_values_hi,x
.endif
    inc int_count_data
    clc
    rts

parse_small_value_expr_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'='
    bne parse_small_value_expr_at_scan_y_after_equals
    jsr advance_scan_y
    bcs parse_small_value_expr_at_scan_y_fail
    jsr skip_inline_spaces_at_scan_y
parse_small_value_expr_at_scan_y_after_equals:
    lda (scan_ptr),y
    cmp #'['
    bne parse_small_value_expr_at_scan_y_after_group
    jsr advance_scan_y
    bcs parse_small_value_expr_at_scan_y_fail
    jsr parse_small_value_expr_at_scan_y
    bcs parse_small_value_expr_at_scan_y_fail
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #']'
    bne parse_small_value_expr_at_scan_y_fail
    jsr advance_scan_y
    bcs parse_small_value_expr_at_scan_y_fail
    clc
    rts
parse_small_value_expr_at_scan_y_after_group:
    lda (scan_ptr),y
    cmp #'('
    bne :+
    jsr scan_value_expr_for_top_level_arith_from_scan_y
    bcc parse_small_value_expr_at_scan_y_sum_entry
:
    jsr scan_value_expr_for_bool_tokens_from_scan_y
    bcc parse_small_value_expr_at_scan_y_bool_entry
parse_small_value_expr_at_scan_y_sum_entry:
    jmp parse_small_decimal_expr_at_scan_y
parse_small_value_expr_at_scan_y_bool_entry:
    jmp parse_small_bool_or_at_scan_y

parse_small_value_expr_at_scan_y_fail:
    sec
    rts

normalize_small_expr_value_to_bool:
    lda expr_value_lo
    beq :+
    lda #$01
    sta expr_value_lo
:   clc
    rts

parse_small_bool_or_at_scan_y:
    jsr parse_small_bool_and_at_scan_y
    bcs parse_small_bool_or_at_scan_y_fail
parse_small_bool_or_at_scan_y_loop:
    jsr consume_or_keyword_from_scan_y
    bcs parse_small_bool_or_at_scan_y_done
    jsr normalize_small_expr_value_to_bool
    lda expr_value_lo
    sta expr_saved_lo
    jsr parse_small_bool_and_at_scan_y
    bcs parse_small_bool_or_at_scan_y_fail
    jsr normalize_small_expr_value_to_bool
    lda expr_saved_lo
    ora expr_value_lo
    beq parse_small_bool_or_at_scan_y_store
    lda #$01
parse_small_bool_or_at_scan_y_store:
    sta expr_value_lo
    jmp parse_small_bool_or_at_scan_y_loop
parse_small_bool_or_at_scan_y_done:
    clc
    rts
parse_small_bool_or_at_scan_y_fail:
    sec
    rts

parse_small_bool_and_at_scan_y:
    jsr parse_small_bool_not_at_scan_y
    bcs parse_small_bool_and_at_scan_y_fail
parse_small_bool_and_at_scan_y_loop:
    jsr consume_and_keyword_from_scan_y
    bcs parse_small_bool_and_at_scan_y_done
    jsr normalize_small_expr_value_to_bool
    lda expr_value_lo
    sta expr_saved_lo
    jsr parse_small_bool_not_at_scan_y
    bcs parse_small_bool_and_at_scan_y_fail
    jsr normalize_small_expr_value_to_bool
    lda expr_saved_lo
    and expr_value_lo
    beq parse_small_bool_and_at_scan_y_store
    lda #$01
parse_small_bool_and_at_scan_y_store:
    sta expr_value_lo
    jmp parse_small_bool_and_at_scan_y_loop
parse_small_bool_and_at_scan_y_done:
    clc
    rts
parse_small_bool_and_at_scan_y_fail:
    sec
    rts

parse_small_bool_not_at_scan_y:
    jsr consume_not_keyword_from_scan_y
    bcs parse_small_bool_primary_at_scan_y
    jsr parse_small_bool_not_at_scan_y
    bcs parse_small_bool_not_at_scan_y_fail
    jsr normalize_small_expr_value_to_bool
    lda expr_value_lo
    eor #$01
    sta expr_value_lo
    clc
    rts
parse_small_bool_not_at_scan_y_fail:
    sec
    rts

parse_small_bool_primary_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'('
    bne parse_small_bool_condition_clause_at_scan_y
    tya
    pha
    jsr save_group_reader_mark
    jsr advance_scan_y
    jsr parse_small_bool_or_at_scan_y
    bcs parse_small_bool_primary_restore_clause
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne parse_small_bool_primary_restore_clause
    jsr advance_scan_y
    sty compare_char
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'='
    beq parse_small_bool_primary_restore_clause
    cmp #'<'
    beq parse_small_bool_primary_restore_clause
    cmp #'>'
    beq parse_small_bool_primary_restore_clause
    ldy compare_char
    pla
    clc
    rts
parse_small_bool_primary_restore_clause:
    jsr restore_group_reader_mark
    pla
    tay
parse_small_bool_condition_clause_at_scan_y:
    jmp parse_small_condition_clause_at_scan_y

parse_small_condition_clause_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_condition_clause_lhs_ok
    jmp parse_small_condition_clause_at_scan_y_fail
parse_small_condition_clause_lhs_ok:
    lda expr_value_lo
    sta expr_compare_lo
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'='
    beq parse_small_condition_clause_eq
    cmp #'<'
    beq parse_small_condition_clause_lt_entry
    cmp #'>'
    beq parse_small_condition_clause_gt_entry
    lda expr_compare_lo
    sta expr_value_lo
    clc
    rts

parse_small_condition_clause_eq:
    jsr advance_scan_y
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_condition_clause_eq_ok
    jmp parse_small_condition_clause_at_scan_y_fail
parse_small_condition_clause_eq_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    bne :+
    jmp parse_small_condition_clause_true
:
    jmp parse_small_condition_clause_false

parse_small_condition_clause_lt_entry:
    jsr advance_scan_y
    lda (scan_ptr),y
    cmp #'='
    beq parse_small_condition_clause_le
    cmp #'>'
    beq parse_small_condition_clause_ne
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_condition_clause_lt_ok
    jmp parse_small_condition_clause_at_scan_y_fail
parse_small_condition_clause_lt_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    bcc parse_small_condition_clause_true
    jmp parse_small_condition_clause_false

parse_small_condition_clause_gt_entry:
    jsr advance_scan_y
    lda (scan_ptr),y
    cmp #'='
    beq parse_small_condition_clause_ge
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_condition_clause_gt_ok
    jmp parse_small_condition_clause_at_scan_y_fail
parse_small_condition_clause_gt_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_condition_clause_false
    bcs parse_small_condition_clause_true
    jmp parse_small_condition_clause_false

parse_small_condition_clause_le:
    jsr advance_scan_y
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_condition_clause_le_ok
    jmp parse_small_condition_clause_at_scan_y_fail
parse_small_condition_clause_le_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_condition_clause_true
    bcc parse_small_condition_clause_true
    jmp parse_small_condition_clause_false

parse_small_condition_clause_ge:
    jsr advance_scan_y
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_condition_clause_ge_ok
    jmp parse_small_condition_clause_at_scan_y_fail
parse_small_condition_clause_ge_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_condition_clause_true
    bcs parse_small_condition_clause_true
    jmp parse_small_condition_clause_false

parse_small_condition_clause_ne:
    jsr advance_scan_y
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_condition_clause_ne_ok
    jmp parse_small_condition_clause_at_scan_y_fail
parse_small_condition_clause_ne_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_condition_clause_false
    jmp parse_small_condition_clause_true

parse_small_condition_clause_true:
    lda #$01
    sta expr_value_lo
    clc
    rts

parse_small_condition_clause_false:
    lda #$00
    sta expr_value_lo
    clc
    rts

parse_small_condition_clause_at_scan_y_fail:
    sec
    rts

parse_small_decimal_expr_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_decimal_expr_lhs_ok
    jmp parse_small_decimal_expr_at_scan_y_fail
parse_small_decimal_expr_lhs_ok:
    lda expr_value_lo
    sta expr_compare_lo
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'='
    beq parse_small_decimal_expr_eq
    cmp #'<'
    beq parse_small_decimal_expr_lt_entry
    cmp #'>'
    beq parse_small_decimal_expr_gt_entry
    lda expr_compare_lo
    sta expr_value_lo
    clc
    rts

parse_small_decimal_expr_eq:
    jsr advance_scan_y
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_decimal_expr_eq_ok
    jmp parse_small_decimal_expr_at_scan_y_fail
parse_small_decimal_expr_eq_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_decimal_expr_eq_true
    jmp parse_small_decimal_expr_false
parse_small_decimal_expr_eq_true:
    jmp parse_small_decimal_expr_true

parse_small_decimal_expr_lt_entry:
    jsr advance_scan_y
    lda (scan_ptr),y
    cmp #'='
    beq parse_small_decimal_expr_le
    cmp #'>'
    beq parse_small_decimal_expr_ne
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_decimal_expr_lt_ok
    jmp parse_small_decimal_expr_at_scan_y_fail
parse_small_decimal_expr_lt_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    bcc parse_small_decimal_expr_lt_true
    jmp parse_small_decimal_expr_false
parse_small_decimal_expr_lt_true:
    jmp parse_small_decimal_expr_true

parse_small_decimal_expr_gt_entry:
    jsr advance_scan_y
    lda (scan_ptr),y
    cmp #'='
    beq parse_small_decimal_expr_ge
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_decimal_expr_gt_ok
    jmp parse_small_decimal_expr_at_scan_y_fail
parse_small_decimal_expr_gt_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_decimal_expr_gt_false
    bcs parse_small_decimal_expr_gt_true
    jmp parse_small_decimal_expr_false
parse_small_decimal_expr_gt_true:
    jmp parse_small_decimal_expr_true
parse_small_decimal_expr_gt_false:
    jmp parse_small_decimal_expr_false

parse_small_decimal_expr_le:
    jsr advance_scan_y
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_decimal_expr_le_ok
    jmp parse_small_decimal_expr_at_scan_y_fail
parse_small_decimal_expr_le_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_decimal_expr_le_true
    bcc parse_small_decimal_expr_le_true
    jmp parse_small_decimal_expr_false
parse_small_decimal_expr_le_true:
    jmp parse_small_decimal_expr_true

parse_small_decimal_expr_ge:
    jsr advance_scan_y
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_decimal_expr_ge_ok
    jmp parse_small_decimal_expr_at_scan_y_fail
parse_small_decimal_expr_ge_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_decimal_expr_ge_true
    bcs parse_small_decimal_expr_ge_true
    jmp parse_small_decimal_expr_false
parse_small_decimal_expr_ge_true:
    jmp parse_small_decimal_expr_true

parse_small_decimal_expr_ne:
    jsr advance_scan_y
    jsr parse_small_decimal_sum_at_scan_y
    bcc parse_small_decimal_expr_ne_ok
    jmp parse_small_decimal_expr_at_scan_y_fail
parse_small_decimal_expr_ne_ok:
    lda expr_compare_lo
    cmp expr_value_lo
    beq parse_small_decimal_expr_ne_false
    jmp parse_small_decimal_expr_true
parse_small_decimal_expr_ne_false:
    jmp parse_small_decimal_expr_false

parse_small_decimal_expr_done:
    lda expr_compare_lo
    sta expr_value_lo
    clc
    rts

parse_small_decimal_expr_true:
    lda #$01
    sta expr_value_lo
    clc
    rts

parse_small_decimal_expr_false:
    lda #$00
    sta expr_value_lo
    clc
    rts

parse_small_decimal_expr_at_scan_y_fail:
    sec
    rts

parse_small_decimal_sum_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    jsr parse_small_decimal_term_at_scan_y
    bcc :+
    jmp parse_small_decimal_sum_at_scan_y_fail
:   lda expr_value_lo
    sta expr_saved_lo
parse_small_decimal_sum_loop:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    beq :+
    cmp #10
    beq :+
    cmp #13
    beq :+
    cmp #','
    beq :+
    cmp #'+'
    beq parse_small_decimal_sum_add
    cmp #'-'
    beq parse_small_decimal_sum_sub
    cmp #')'
    beq parse_small_decimal_sum_done
    cmp #']'
    beq parse_small_decimal_sum_done
    cmp #'='
    beq parse_small_decimal_sum_done
    cmp #'<'
    beq parse_small_decimal_sum_done
    cmp #'>'
    beq parse_small_decimal_sum_done
    jsr uppercase_ascii
    cmp #'A'
    beq parse_small_decimal_sum_try_and
    cmp #'O'
    beq parse_small_decimal_sum_try_or
    jmp parse_small_decimal_sum_at_scan_y_fail
:   jmp parse_small_decimal_sum_done

parse_small_decimal_sum_try_and:
    sty symbol_start_y_data
    jsr consume_and_keyword_from_scan_y
    bcc :+
    jmp parse_small_decimal_sum_at_scan_y_fail
:   ldy symbol_start_y_data
    jmp parse_small_decimal_sum_done

parse_small_decimal_sum_try_or:
    sty symbol_start_y_data
    jsr consume_or_keyword_from_scan_y
    bcc :+
    jmp parse_small_decimal_sum_at_scan_y_fail
:   ldy symbol_start_y_data
    jmp parse_small_decimal_sum_done

parse_small_decimal_sum_add:
    jsr advance_scan_y
    jsr parse_small_decimal_term_at_scan_y
    bcc :+
    jmp parse_small_decimal_sum_at_scan_y_fail
:   lda expr_saved_lo
    clc
    adc expr_value_lo
    bcc :+
    jmp parse_small_decimal_sum_at_scan_y_fail
:   sta expr_saved_lo
    jmp parse_small_decimal_sum_loop

parse_small_decimal_sum_sub:
    jsr advance_scan_y
    jsr parse_small_decimal_term_at_scan_y
    bcc :+
    jmp parse_small_decimal_sum_at_scan_y_fail
:   lda expr_saved_lo
    sec
    sbc expr_value_lo
    bcs :+
    jmp parse_small_decimal_sum_at_scan_y_fail
:   sta expr_saved_lo
    jmp parse_small_decimal_sum_loop

parse_small_decimal_sum_done:
    lda expr_saved_lo
    sta expr_value_lo
    clc
    rts

parse_small_decimal_sum_at_scan_y_fail:
    sec
    rts

parse_small_decimal_term_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    jsr parse_small_decimal_factor_at_scan_y
    bcs parse_small_decimal_term_at_scan_y_fail
    lda expr_value_lo
    sta expr_term_lo
parse_small_decimal_term_loop:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'*'
    beq parse_small_decimal_term_mul
    cmp #'/'
    beq parse_small_decimal_term_div
    lda expr_term_lo
    sta expr_value_lo
    clc
    rts

parse_small_decimal_term_mul:
    jsr advance_scan_y
    jsr parse_small_decimal_factor_at_scan_y
    bcs parse_small_decimal_term_at_scan_y_fail
    lda expr_term_lo
    sta compare_char
    lda expr_value_lo
    sta hex_work
    lda #$00
    sta expr_term_lo
parse_small_decimal_term_mul_loop:
    lda hex_work
    beq parse_small_decimal_term_loop
    dec hex_work
    lda expr_term_lo
    clc
    adc compare_char
    bcs parse_small_decimal_term_at_scan_y_fail
    sta expr_term_lo
    jmp parse_small_decimal_term_mul_loop

parse_small_decimal_term_div:
    jsr advance_scan_y
    jsr parse_small_decimal_factor_at_scan_y
    bcs parse_small_decimal_term_at_scan_y_fail
    lda expr_value_lo
    beq parse_small_decimal_term_at_scan_y_fail
    sta hex_work
    lda expr_term_lo
    sta compare_char
    lda #$00
    sta expr_term_lo
parse_small_decimal_term_div_loop:
    lda compare_char
    cmp hex_work
    bcc parse_small_decimal_term_loop
    sec
    sbc hex_work
    sta compare_char
    inc expr_term_lo
    bne parse_small_decimal_term_div_loop

parse_small_decimal_term_at_scan_y_fail:
    sec
    rts

parse_small_decimal_factor_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'('
    beq parse_small_decimal_factor_group
    jmp parse_small_decimal_at_scan_y

parse_small_decimal_factor_group:
    jsr advance_scan_y
    jsr parse_small_value_expr_at_scan_y
    bcs parse_small_decimal_factor_at_scan_y_fail
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne parse_small_decimal_factor_at_scan_y_fail
    jsr advance_scan_y
    clc
    rts

parse_small_decimal_factor_at_scan_y_fail:
    sec
    rts

parse_small_decimal_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    lda #$00
    sta expr_value_lo
    sta expr_digit_count
parse_small_decimal_at_scan_y_loop:
    lda (scan_ptr),y
    cmp #'0'
    bcc parse_small_decimal_at_scan_y_done_check
    cmp #'9'+1
    bcs parse_small_decimal_at_scan_y_done_check
    sec
    sbc #'0'
    sta compare_char
    lda expr_value_lo
    sta hex_work
    asl a
    sta truncated_flag
    lda hex_work
    asl a
    asl a
    asl a
    clc
    adc truncated_flag
    bcs parse_small_decimal_at_scan_y_fail
    adc compare_char
    bcs parse_small_decimal_at_scan_y_fail
    sta expr_value_lo
    jsr advance_scan_y
    inc expr_digit_count
    bne parse_small_decimal_at_scan_y_loop
parse_small_decimal_at_scan_y_done_check:
    lda expr_digit_count
    beq parse_small_decimal_at_scan_y_fail
    clc
    rts
parse_small_decimal_at_scan_y_fail:
    sec
    rts

.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
parse_positive_word_sum_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    jsr parse_positive_word_term_at_scan_y
    bcc :+
    sec
    rts
:   lda expr_value_lo
    sta expr_compare_lo
    lda expr_value_hi
    sta expr_compare_hi
parse_positive_word_sum_loop:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    beq parse_positive_word_sum_done
    cmp #10
    beq parse_positive_word_sum_done
    cmp #13
    beq parse_positive_word_sum_done
    cmp #','
    beq parse_positive_word_sum_done
    cmp #')'
    beq parse_positive_word_sum_done
    cmp #']'
    beq parse_positive_word_sum_done
    cmp #'='
    beq parse_positive_word_sum_done
    cmp #'<'
    beq parse_positive_word_sum_done
    cmp #'>'
    beq parse_positive_word_sum_done
    cmp #'+'
    beq parse_positive_word_sum_add
    cmp #'-'
    beq parse_positive_word_sum_sub
    sec
    rts

parse_positive_word_sum_add:
    jsr advance_scan_y
    jsr parse_positive_word_term_at_scan_y
    bcc :+
    sec
    rts
:   clc
    lda expr_compare_lo
    adc expr_value_lo
    sta expr_compare_lo
    lda expr_compare_hi
    adc expr_value_hi
    sta expr_compare_hi
    bcc parse_positive_word_sum_loop
    sec
    rts

parse_positive_word_sum_sub:
    jsr advance_scan_y
    jsr parse_positive_word_term_at_scan_y
    bcc :+
    sec
    rts
:   lda expr_compare_lo
    sec
    sbc expr_value_lo
    sta expr_compare_lo
    lda expr_compare_hi
    sbc expr_value_hi
    sta expr_compare_hi
    bcs parse_positive_word_sum_loop
    sec
    rts

parse_positive_word_sum_done:
    lda expr_compare_lo
    sta expr_value_lo
    lda expr_compare_hi
    sta expr_value_hi
    clc
    rts

parse_positive_word_term_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    jsr parse_positive_word_factor_at_scan_y
    bcc :+
    sec
    rts
:   lda expr_value_lo
    sta expr_term_lo
    lda expr_value_hi
    sta expr_term_hi
parse_positive_word_term_loop:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'*'
    beq parse_positive_word_term_mul
    cmp #'/'
    beq parse_positive_word_term_div
    lda expr_term_lo
    sta expr_value_lo
    lda expr_term_hi
    sta expr_value_hi
    clc
    rts

parse_positive_word_term_mul:
    lda expr_term_lo
    sta expr_compare_lo
    lda expr_term_hi
    sta expr_compare_hi
    jsr advance_scan_y
    jsr parse_positive_word_factor_at_scan_y
    bcc :+
    sec
    rts
:
    lda expr_value_lo
    sta expr_saved_lo
    lda expr_value_hi
    sta expr_saved_hi
    lda #$00
    sta expr_term_lo
    sta expr_term_hi
parse_positive_word_term_mul_loop:
    lda expr_saved_lo
    ora expr_saved_hi
    beq parse_positive_word_term_loop
    clc
    lda expr_term_lo
    adc expr_compare_lo
    sta expr_term_lo
    lda expr_term_hi
    adc expr_compare_hi
    sta expr_term_hi
    bcs parse_positive_word_term_at_scan_y_fail
    lda expr_saved_lo
    sec
    sbc #$01
    sta expr_saved_lo
    lda expr_saved_hi
    sbc #$00
    sta expr_saved_hi
    jmp parse_positive_word_term_mul_loop

parse_positive_word_term_div:
    lda expr_term_lo
    sta expr_compare_lo
    lda expr_term_hi
    sta expr_compare_hi
    jsr advance_scan_y
    jsr parse_positive_word_factor_at_scan_y
    bcc :+
    sec
    rts
:   lda expr_value_lo
    ora expr_value_hi
    bne :+
    sec
    rts
:   lda expr_value_lo
    sta expr_saved_lo
    lda expr_value_hi
    sta expr_saved_hi
    lda #$00
    sta expr_term_lo
    sta expr_term_hi
parse_positive_word_term_div_loop:
    lda expr_compare_hi
    cmp expr_saved_hi
    bcc parse_positive_word_term_div_done
    bne :+
    lda expr_compare_lo
    cmp expr_saved_lo
    bcc parse_positive_word_term_div_done
:   lda expr_compare_lo
    sec
    sbc expr_saved_lo
    sta expr_compare_lo
    lda expr_compare_hi
    sbc expr_saved_hi
    sta expr_compare_hi
    inc expr_term_lo
    bne parse_positive_word_term_div_loop
    inc expr_term_hi
    bne parse_positive_word_term_div_loop
parse_positive_word_term_div_done:
    jmp parse_positive_word_term_loop
parse_positive_word_term_at_scan_y_fail:
    sec
    rts

parse_positive_word_factor_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'('
    beq parse_positive_word_factor_group
    jmp parse_positive_word_decimal_at_scan_y

parse_positive_word_factor_group:
    lda expr_compare_lo
    sta expr_group_saved_compare_lo
    lda expr_compare_hi
    sta expr_group_saved_compare_hi
    lda expr_saved_lo
    sta expr_group_saved_saved_lo
    lda expr_saved_hi
    sta expr_group_saved_saved_hi
    jsr advance_scan_y
    jsr parse_positive_word_sum_at_scan_y
    bcc :+
    sec
    rts
:   jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne parse_positive_word_decimal_at_scan_y_fail
    jsr advance_scan_y
    lda expr_group_saved_compare_lo
    sta expr_compare_lo
    lda expr_group_saved_compare_hi
    sta expr_compare_hi
    lda expr_group_saved_saved_lo
    sta expr_saved_lo
    lda expr_group_saved_saved_hi
    sta expr_saved_hi
    clc
    rts

parse_optional_grouped_positive_word_sum_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'('
    bne parse_positive_word_sum_at_scan_y
    jsr advance_scan_y
    bcs parse_positive_word_term_at_scan_y_fail
    jsr parse_positive_word_sum_at_scan_y
    bcs parse_positive_word_term_at_scan_y_fail
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne parse_positive_word_decimal_at_scan_y_fail
    jsr advance_scan_y
    clc
    rts

parse_positive_word_decimal_at_scan_y:
    jsr skip_inline_spaces_at_scan_y
    lda #$00
    sta expr_value_lo
    sta expr_value_hi
    sta expr_digit_count
parse_positive_word_decimal_at_scan_y_loop:
    lda (scan_ptr),y
    cmp #'0'
    bcc parse_positive_word_decimal_at_scan_y_done_check
    cmp #'9'+1
    bcs parse_positive_word_decimal_at_scan_y_done_check
    sec
    sbc #'0'
    sta compare_char
    lda expr_value_lo
    sta expr_saved_lo
    lda expr_value_hi
    sta expr_saved_hi
    lda #$00
    sta expr_term_lo
    sta expr_term_hi
    ldx #10
parse_positive_word_decimal_at_scan_y_mul10_loop:
    clc
    lda expr_term_lo
    adc expr_saved_lo
    sta expr_term_lo
    lda expr_term_hi
    adc expr_saved_hi
    sta expr_term_hi
    bcs parse_positive_word_decimal_at_scan_y_fail
    dex
    bne parse_positive_word_decimal_at_scan_y_mul10_loop
    clc
    lda expr_term_lo
    adc compare_char
    sta expr_value_lo
    lda expr_term_hi
    adc #$00
    sta expr_value_hi
    bcs parse_positive_word_decimal_at_scan_y_fail
    jsr advance_scan_y
    inc expr_digit_count
    bne parse_positive_word_decimal_at_scan_y_loop
parse_positive_word_decimal_at_scan_y_done_check:
    lda expr_digit_count
    beq parse_positive_word_decimal_at_scan_y_fail
    clc
    rts
parse_positive_word_decimal_at_scan_y_fail:
    sec
    rts
.endif

skip_inline_spaces_at_scan_y:
    lda (scan_ptr),y
    cmp #' '
    beq skip_inline_spaces_at_scan_y_advance
    cmp #9
    beq skip_inline_spaces_at_scan_y_advance
    rts
skip_inline_spaces_at_scan_y_advance:
    jsr advance_scan_y
    bcc skip_inline_spaces_at_scan_y
    rts

advance_scan_y:
    iny
    bne advance_scan_y_ok
    pha
    txa
    pha
    jsr source_reader_commit_256_from_scan_ptr
    bcs advance_scan_y_commit_fail
    pla
    tax
    pla
    ldy #$00
    clc
    rts
advance_scan_y_commit_fail:
    pla
    tax
    pla
    ldy #$00
    sec
    rts
advance_scan_y_ok:
    clc
    rts

save_source_reader_mark:
    lda scan_ptr
    sta keyword_scan_ptr_lo_data
    lda scan_ptr+1
    sta keyword_scan_ptr_hi_data
.if ACTC_REU_SOURCE_CACHE
    sec
    lda source_window_next_offset
    sbc source_window_len
    sta keyword_window_start_data
    lda source_window_next_offset+1
    sbc source_window_len+1
    sta keyword_window_start_data+1
    lda source_window_next_offset+2
    sbc #$00
    sta keyword_window_start_data+2
.endif
    rts

restore_source_reader_mark:
.if ACTC_REU_SOURCE_CACHE
    txa
    pha
    sec
    lda source_window_next_offset
    sbc source_window_len
    sta file_params+0
    lda source_window_next_offset+1
    sbc source_window_len+1
    sta file_params+1
    lda source_window_next_offset+2
    sbc #$00
    sta file_params+2
    lda file_params+0
    cmp keyword_window_start_data
    bne restore_source_reader_mark_reload
    lda file_params+1
    cmp keyword_window_start_data+1
    bne restore_source_reader_mark_reload
    lda file_params+2
    cmp keyword_window_start_data+2
    bne restore_source_reader_mark_reload
    jmp restore_source_reader_mark_after_reload
restore_source_reader_mark_reload:
    lda keyword_window_start_data
    sta source_window_next_offset
    lda keyword_window_start_data+1
    sta source_window_next_offset+1
    lda keyword_window_start_data+2
    sta source_window_next_offset+2
    jsr source_reader_load_next_window
restore_source_reader_mark_after_reload:
    pla
    tax
.endif
    lda keyword_scan_ptr_lo_data
    sta scan_ptr
    lda keyword_scan_ptr_hi_data
    sta scan_ptr+1
    rts

save_group_reader_mark:
    lda scan_ptr
    sta group_scan_ptr_lo_data
    lda scan_ptr+1
    sta group_scan_ptr_hi_data
.if ACTC_REU_SOURCE_CACHE
    sec
    lda source_window_next_offset
    sbc source_window_len
    sta group_window_start_data
    lda source_window_next_offset+1
    sbc source_window_len+1
    sta group_window_start_data+1
    lda source_window_next_offset+2
    sbc #$00
    sta group_window_start_data+2
.endif
    rts

restore_group_reader_mark:
.if ACTC_REU_SOURCE_CACHE
    txa
    pha
    lda group_window_start_data
    sta source_window_next_offset
    lda group_window_start_data+1
    sta source_window_next_offset+1
    lda group_window_start_data+2
    sta source_window_next_offset+2
    jsr source_reader_load_next_window
    pla
    tax
.endif
    lda group_scan_ptr_lo_data
    sta scan_ptr
    lda group_scan_ptr_hi_data
    sta scan_ptr+1
    rts

save_condition_reader_mark:
    lda scan_ptr
    sta condition_scan_ptr_lo_data
    lda scan_ptr+1
    sta condition_scan_ptr_hi_data
.if ACTC_REU_SOURCE_CACHE
    sec
    lda source_window_next_offset
    sbc source_window_len
    sta condition_window_start_data
    lda source_window_next_offset+1
    sbc source_window_len+1
    sta condition_window_start_data+1
    lda source_window_next_offset+2
    sbc #$00
    sta condition_window_start_data+2
.endif
    rts

restore_condition_reader_mark:
.if ACTC_REU_SOURCE_CACHE
    txa
    pha
    lda condition_window_start_data
    sta source_window_next_offset
    lda condition_window_start_data+1
    sta source_window_next_offset+1
    lda condition_window_start_data+2
    sta source_window_next_offset+2
    jsr source_reader_load_next_window
    pla
    tax
.endif
    lda condition_scan_ptr_lo_data
    sta scan_ptr
    lda condition_scan_ptr_hi_data
    sta scan_ptr+1
    rts

compute_payload_layout:
.if ACTC_USE_LAYOUT_OVERLAY
    jsr compute_payload_layout_with_overlay_if_possible
    bcc compute_payload_layout_done_entry
.endif
.if ACTC_KEEP_LAYOUT_RESIDENT_FALLBACK
    lda #$00
    sta payload_offset
    sta payload_offset_hi
    sta proc_index
compute_payload_layout_loop:
    ldx proc_index
    cpx export_count_data
    bne :+
    jmp compute_payload_layout_done
:
.if ACTC_REU_LAYOUT_META
    lda payload_offset
    sta layout_offset_lo_data
    lda payload_offset_hi
    sta layout_offset_hi_data
    lda #1
    sta layout_size_lo_data
    lda #0
    sta layout_size_hi_data
.else
    lda payload_offset
    sta export_offsets,x
    lda payload_offset_hi
    sta export_offsets_hi,x
    lda #1
    sta proc_sizes_data,x
    lda #0
    sta proc_sizes_hi,x
.endif
    jsr set_body_ptr_from_x
    ldy #$00
compute_payload_layout_body_loop:
    lda (body_ptr),y
    bne :+
    jmp compute_payload_layout_ret
:
    cmp #'c'
    bne :+
    jmp compute_payload_layout_add_call
:   cmp #'u'
    bne :+
    jmp compute_payload_layout_add_call
:   cmp #'p'
    bne :+
    jmp compute_payload_layout_add_call
:
    cmp #'s'
    beq compute_payload_layout_add_string
    cmp #'e'
    beq compute_payload_layout_add_string
    cmp #'i'
    bne :+
    jmp compute_payload_layout_add_int
:
	    cmp #'j'
	    bne :+
	    jmp compute_payload_layout_add_int
:
		    cmp #'L'
		    bne :+
		    jmp compute_payload_layout_add_single_int_pair
:		    cmp #'S'
		    bne :+
		    jmp compute_payload_layout_add_single_int_pair
:		    cmp #'U'
		    bne :+
		    jmp compute_payload_layout_add_single_int_pair
:		    cmp #'T'
		    bne :+
		    jmp compute_payload_layout_add_single_int_pair
:		    cmp #'y'
		    beq compute_payload_layout_add_single_int
	    cmp #'z'
	    beq compute_payload_layout_add_single_int
	    cmp #'h'
	    beq compute_payload_layout_add_single_int
	    cmp #'f'
	    beq compute_payload_layout_add_single_int
	    cmp #'t'
	    beq compute_payload_layout_add_single_int
	    cmp #'w'
	    beq compute_payload_layout_add_single_int
	    cmp #'v'
	    beq compute_payload_layout_add_zero
	    cmp #'d'
	    beq compute_payload_layout_add_zero
	    cmp #'o'
	    beq compute_payload_layout_add_zero
	    cmp #'x'
	    beq compute_payload_layout_add_single_int
	    cmp #'a'
	    beq compute_payload_layout_add_single
    cmp #'m'
    beq compute_payload_layout_add_single
    cmp #'q'
    beq compute_payload_layout_add_single
    cmp #'n'
    beq compute_payload_layout_add_single
    cmp #'l'
    beq compute_payload_layout_add_single
    cmp #'g'
    beq compute_payload_layout_add_single
    cmp #'r'
    beq compute_payload_layout_add_single
    jmp compute_payload_layout_bad
compute_payload_layout_add_call:
    lda #3
    jsr add_a_to_proc_size_x
    iny
    iny
    jmp compute_payload_layout_body_loop
compute_payload_layout_add_string:
    lda #6
    jsr add_a_to_proc_size_x
    iny
    iny
    jmp compute_payload_layout_body_loop
compute_payload_layout_add_single:
    lda #1
    jsr add_a_to_proc_size_x
    iny
    jmp compute_payload_layout_body_loop
compute_payload_layout_add_single_int:
	    lda #3
	    jsr add_a_to_proc_size_x
	    iny
	    jmp compute_payload_layout_body_loop
compute_payload_layout_add_single_int_pair:
	    lda #3
	    jsr add_a_to_proc_size_x
	    iny
	    iny
	    jmp compute_payload_layout_body_loop
compute_payload_layout_add_zero:
	    iny
	    jmp compute_payload_layout_body_loop
compute_payload_layout_add_int:
    lda #6
    jsr add_a_to_proc_size_x
    iny
    iny
    beq :+
    jmp compute_payload_layout_body_loop
:
compute_payload_layout_ret:
    cpy #$00
    beq compute_payload_layout_ret_add
    dey
    lda (body_ptr),y
    cmp #'r'
    bne compute_payload_layout_ret_add
.if ACTC_REU_LAYOUT_META
    lda layout_size_lo_data
    bne compute_payload_layout_ret_dec
    dec layout_size_hi_data
compute_payload_layout_ret_dec:
    dec layout_size_lo_data
.else
    lda proc_sizes_data,x
    bne compute_payload_layout_ret_dec
    dec proc_sizes_hi,x
compute_payload_layout_ret_dec:
    dec proc_sizes_data,x
.endif
compute_payload_layout_ret_add:
    clc
    lda payload_offset
.if ACTC_REU_LAYOUT_META
    adc layout_size_lo_data
    sta payload_offset
    lda payload_offset_hi
    adc layout_size_hi_data
    sta payload_offset_hi
    ldx proc_index
    jsr store_layout_to_reu_x
.else
    adc proc_sizes_data,x
    sta payload_offset
    lda payload_offset_hi
    adc proc_sizes_hi,x
    sta payload_offset_hi
.endif
    inc proc_index
    jmp compute_payload_layout_loop
compute_payload_layout_done:
    ldx #$00
compute_payload_layout_strings_loop:
    cpx string_count_data
    beq compute_payload_layout_done_ok
    lda payload_offset
.if ACTC_REU_STRING_OFFSETS
    sta string_offset_data
    jsr store_string_offset_to_reu_x
.else
    sta string_offsets,x
.endif
    txa
    pha
    jsr set_string_ptr_from_x
    ldy #$00
compute_payload_layout_string_len_loop:
    lda (body_ptr),y
    beq compute_payload_layout_string_done
    inc payload_offset
    bne :+
    inc payload_offset_hi
:
    iny
    bne compute_payload_layout_string_len_loop
compute_payload_layout_string_done:
    inc payload_offset
    bne :+
    inc payload_offset_hi
:
    pla
    tax
    inx
    bne compute_payload_layout_strings_loop
compute_payload_layout_done_ok:
    rts
compute_payload_layout_bad:
    sta compare_char
.if ACTC_REU_BODY_OPS
    lda body_ops_window+0
    sta $C59F
    lda body_ops_window+1
    sta $C5A0
    lda body_ops_window+2
    sta $C5A1
    lda body_ops_window+3
    sta $C5A2
.else
    lda body_ops_data+0
    sta $C59F
    lda body_ops_data+1
    sta $C5A0
    lda body_ops_data+2
    sta $C5A1
    lda body_ops_data+3
    sta $C5A2
.endif
    lda compare_char
    jsr set_actc_trace
    sty $03FC
    stx $03FD
    lda #<msg_bad_call
    ldy #>msg_bad_call
    jmp fail_with_ptr
.endif
compute_payload_layout_done_entry:
    rts

.if ACTC_USE_LAYOUT_OVERLAY
compute_payload_layout_with_overlay_if_possible:
    lda #ACTC_OVERLAY_PASS_PAYLOAD_LAYOUT
    jsr actc_overlay_run_pass
    bcc compute_payload_layout_with_overlay_ok
    lda actc_overlay_context+ACTC_OVERLAY_CTX_DIAG_PTR_LO
    ora actc_overlay_context+ACTC_OVERLAY_CTX_DIAG_PTR_HI
    beq compute_payload_layout_with_overlay_fallback
    lda actc_overlay_context+ACTC_OVERLAY_CTX_DIAG_PTR_LO
    ldy actc_overlay_context+ACTC_OVERLAY_CTX_DIAG_PTR_HI
    jmp fail_with_ptr
compute_payload_layout_with_overlay_fallback:
.if ACTC_KEEP_LAYOUT_RESIDENT_FALLBACK
    sec
    rts
.else
    lda #<msg_layout_overlay
    ldy #>msg_layout_overlay
    jmp fail_with_ptr
.endif
compute_payload_layout_with_overlay_ok:
    cmp #ACTC_OVERLAY_STATUS_OK
    beq :+
    jmp compute_payload_layout_with_overlay_fallback
:
    clc
    rts
.endif

skip_source_line:
    ldy #$00
skip_source_line_loop:
    lda (scan_ptr),y
    beq skip_source_line_done
    cmp #10
    beq skip_source_line_done
    cmp #13
    beq skip_source_line_done
    jsr advance_scan_ptr
    jmp skip_source_line_loop
skip_source_line_done:
    rts

.if ACTC_KEEP_DECL_RESIDENT_FALLBACK
store_proc_export_from_scan_ptr_or_fail:
    lda export_count_data
    cmp #EXPORT_MAX
    bcc :+
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_ptr
:   ldx export_count_data
    txa
    pha
    jsr set_export_ptr_from_x
    pla
    tax
.if ACTC_REU_PROC_DEBUG
    jsr store_proc_debug_offset_from_current_scan_x
.endif
    ldy #$00
store_proc_export_from_scan_ptr_or_fail_loop:
    lda (scan_ptr),y
    beq store_proc_export_from_scan_ptr_or_fail_done
    cmp #'('
    beq store_proc_export_from_scan_ptr_or_fail_done
    cmp #'='
    beq store_proc_export_from_scan_ptr_or_fail_done
    cmp #' '
    beq store_proc_export_from_scan_ptr_or_fail_done
    cmp #9
    beq store_proc_export_from_scan_ptr_or_fail_done
    cmp #10
    beq store_proc_export_from_scan_ptr_or_fail_done
    cmp #13
    beq store_proc_export_from_scan_ptr_or_fail_done
    jsr uppercase_ascii
    cpy #$00
    bne store_proc_export_from_scan_ptr_or_fail_body
    jsr uppercase_symbol_start_valid
    bcc store_proc_export_from_scan_ptr_or_fail_store
    jmp store_proc_export_from_scan_ptr_or_fail_bad
store_proc_export_from_scan_ptr_or_fail_body:
    jsr uppercase_symbol_body_valid
    bcc store_proc_export_from_scan_ptr_or_fail_store
    jmp store_proc_export_from_scan_ptr_or_fail_bad
store_proc_export_from_scan_ptr_or_fail_store:
    sta (export_ptr),y
    iny
    cpy #24
    bcc store_proc_export_from_scan_ptr_or_fail_loop
store_proc_export_from_scan_ptr_or_fail_bad:
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_ptr
store_proc_export_from_scan_ptr_or_fail_done:
    cpy #$00
    beq store_proc_export_from_scan_ptr_or_fail_bad
    lda #$00
    sta (export_ptr),y
.if ACTC_REU_EXPORT_NAMES
    jsr store_export_name_to_reu_x
.endif
    txa
    pha
    jsr store_proc_params_from_scan_y_for_current_export_or_fail
    pla
    tax
    inc export_count_data
    rts

store_proc_params_from_scan_y_for_current_export_or_fail:
    stx proc_index
    ldx proc_index
.if ACTC_REU_PROC_META
    jsr load_proc_meta_from_reu_x
    lda #$00
    sta proc_meta_param_count_data
    lda var_count_data
    sta proc_meta_param_base_data
    jsr store_proc_meta_to_reu_x
.else
    lda #$00
    sta proc_param_count_data,x
    lda var_count_data
    sta proc_param_var_base_data,x
.endif
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #'('
    beq :+
    clc
    rts
:   jsr advance_scan_y
    bcc :+
    jmp store_proc_export_from_scan_ptr_or_fail_bad
:
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #')'
    bne :+
    jmp store_proc_params_from_scan_y_for_current_export_done
:
store_proc_params_from_scan_y_for_current_export_loop:
    jsr copy_symbol_from_scan_y
    bcc :+
    jmp store_proc_export_from_scan_ptr_or_fail_bad
:   sty symbol_end_y_data
    jsr find_module_var_index_from_declared
    bcs :+
    jmp store_proc_export_from_scan_ptr_or_fail_bad
:   ldx proc_index
    jsr find_current_proc_param_index_from_declared_for_proc_x
    bcs :+
    jmp store_proc_export_from_scan_ptr_or_fail_bad
:   ldx var_count_data
    cpx #VAR_MAX
    bcc :+
    jmp store_proc_export_from_scan_ptr_or_fail_bad
:   txa
    pha
    jsr set_var_ptr_from_x
    pla
    tax
    ldy #$00
store_proc_params_from_scan_y_for_current_export_copy_loop:
    lda declared_module_name,y
    sta (export_ptr),y
    beq store_proc_params_from_scan_y_for_current_export_copy_done
    iny
    cpy #25
    bcc store_proc_params_from_scan_y_for_current_export_copy_loop
    jmp store_proc_export_from_scan_ptr_or_fail_bad
store_proc_params_from_scan_y_for_current_export_copy_done:
.if ACTC_REU_VAR_NAMES
    jsr store_var_name_to_reu_x
.endif
.if ACTC_REU_VAR_META
    lda #$00
    sta var_meta_init_lo_data
    sta var_meta_init_hi_data
    lda #$02
    sta var_meta_width_data
    lda #'i'
    sta var_meta_type_data
    jsr store_var_meta_to_reu_x
.else
    lda #$00
    sta var_init_lo,x
    sta var_init_hi,x
    lda #$02
    sta var_width_data,x
    lda #'i'
    sta var_type_data,x
.endif
    inc var_count_data
    ldx proc_index
.if ACTC_REU_PROC_META
    jsr load_proc_meta_from_reu_x
    inc proc_meta_param_count_data
    jsr store_proc_meta_to_reu_x
.else
    inc proc_param_count_data,x
.endif
    ldy symbol_end_y_data
    jsr skip_inline_spaces_at_scan_y
    lda (scan_ptr),y
    cmp #','
    beq store_proc_params_from_scan_y_for_current_export_next
    cmp #')'
    beq store_proc_params_from_scan_y_for_current_export_done
    jmp store_proc_export_from_scan_ptr_or_fail_bad
store_proc_params_from_scan_y_for_current_export_next:
    jsr advance_scan_y
    bcc :+
    jmp store_proc_export_from_scan_ptr_or_fail_bad
:
    jsr skip_inline_spaces_at_scan_y
    jmp store_proc_params_from_scan_y_for_current_export_loop
store_proc_params_from_scan_y_for_current_export_done:
    clc
    rts
.endif

set_export_ptr_from_x:
.if ACTC_REU_EXPORT_NAMES
    jsr load_export_name_from_reu_x
    lda #<export_name_window
    sta export_ptr
    lda #>export_name_window
    sta export_ptr+1
    rts
.else
    lda #<export_names
    sta export_ptr
    lda #>export_names
    sta export_ptr+1
set_export_ptr_from_x_loop:
    cpx #$00
    beq set_export_ptr_from_x_done
    clc
    lda export_ptr
    adc #25
    sta export_ptr
    lda export_ptr+1
    adc #$00
    sta export_ptr+1
    dex
    bne set_export_ptr_from_x_loop
set_export_ptr_from_x_done:
    rts
.endif

.if ACTC_REU_EXPORT_NAMES
set_export_reu_params_from_x:
    lda #ACTC_EXPORT_REU_BASE_LO
    sta file_params+0
    lda #ACTC_EXPORT_REU_BASE_HI
    sta file_params+1
    lda #ACTC_EXPORT_REU_BASE_BANK
    sta file_params+2
set_export_reu_params_from_x_loop:
    cpx #$00
    beq set_export_reu_params_from_x_done
    clc
    lda file_params+0
    adc #25
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_export_reu_params_from_x_loop
set_export_reu_params_from_x_done:
    rts

load_export_name_from_reu_x:
    jsr set_export_reu_params_from_x
    lda #<export_name_window
    sta file_params+3
    lda #>export_name_window
    sta file_params+4
    lda #25
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_export_name_from_reu_x_ok
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_export_name_from_reu_x_ok:
    rts

store_export_name_to_reu_x:
    txa
    pha
    jsr set_export_reu_params_from_x
    lda #<export_name_window
    sta file_params+3
    lda #>export_name_window
    sta file_params+4
    lda #25
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_export_name_to_reu_x_ok
    pla
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_export_name_to_reu_x_ok:
    pla
    tax
    rts
.endif

set_external_ptr_from_x:
.if ACTC_REU_TABLES
    jsr load_external_name_from_reu_x
    lda #<external_name_buffer
    sta export_ptr
    lda #>external_name_buffer
    sta export_ptr+1
    rts
.else
    lda #<external_names
    sta export_ptr
    lda #>external_names
    sta export_ptr+1
set_external_ptr_from_x_loop:
    cpx #$00
    beq set_external_ptr_from_x_done
    clc
    lda export_ptr
    adc #25
    sta export_ptr
    lda export_ptr+1
    adc #$00
    sta export_ptr+1
    dex
    bne set_external_ptr_from_x_loop
set_external_ptr_from_x_done:
    rts
.endif

.if ACTC_REU_TABLES
set_external_reu_params_from_x:
    lda #ACTC_TABLE_REU_BASE_LO
    sta file_params+0
    lda #ACTC_TABLE_REU_BASE_HI
    sta file_params+1
    lda #ACTC_TABLE_REU_BASE_BANK
    sta file_params+2
set_external_reu_params_from_x_loop:
    cpx #$00
    beq set_external_reu_params_from_x_done
    clc
    lda file_params+0
    adc #25
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_external_reu_params_from_x_loop
set_external_reu_params_from_x_done:
    rts

load_external_name_from_reu_x:
    jsr set_external_reu_params_from_x
    lda #<external_name_buffer
    sta file_params+3
    lda #>external_name_buffer
    sta file_params+4
    lda #25
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_external_name_from_reu_x_ok
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_external_name_from_reu_x_ok:
    rts

store_external_name_to_reu_x:
    txa
    pha
    jsr set_external_reu_params_from_x
    lda #<external_name_buffer
    sta file_params+3
    lda #>external_name_buffer
    sta file_params+4
    lda #25
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_external_name_to_reu_x_ok
    pla
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_external_name_to_reu_x_ok:
    pla
    tax
    rts
.endif

set_var_ptr_from_x:
.if ACTC_REU_VAR_NAMES
    jsr load_var_name_from_reu_x
    lda #<var_name_window
    sta export_ptr
    lda #>var_name_window
    sta export_ptr+1
    rts
.else
    lda #<var_names
    sta export_ptr
    lda #>var_names
    sta export_ptr+1
set_var_ptr_from_x_loop:
    cpx #$00
    beq set_var_ptr_from_x_done
    clc
    lda export_ptr
    adc #25
    sta export_ptr
    lda export_ptr+1
    adc #$00
    sta export_ptr+1
    dex
    bne set_var_ptr_from_x_loop
set_var_ptr_from_x_done:
    rts
.endif

.if ACTC_REU_VAR_NAMES
set_var_reu_params_from_x:
    lda #ACTC_VAR_REU_BASE_LO
    sta file_params+0
    lda #ACTC_VAR_REU_BASE_HI
    sta file_params+1
    lda #ACTC_VAR_REU_BASE_BANK
    sta file_params+2
set_var_reu_params_from_x_loop:
    cpx #$00
    beq set_var_reu_params_from_x_done
    clc
    lda file_params+0
    adc #25
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_var_reu_params_from_x_loop
set_var_reu_params_from_x_done:
    rts

load_var_name_from_reu_x:
    jsr set_var_reu_params_from_x
    lda #<var_name_window
    sta file_params+3
    lda #>var_name_window
    sta file_params+4
    lda #25
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_var_name_from_reu_x_ok
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_var_name_from_reu_x_ok:
    rts

store_var_name_to_reu_x:
    txa
    pha
    jsr set_var_reu_params_from_x
    lda #<var_name_window
    sta file_params+3
    lda #>var_name_window
    sta file_params+4
    lda #25
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_var_name_to_reu_x_ok
    pla
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_var_name_to_reu_x_ok:
    pla
    tax
    rts
.endif

.if ACTC_REU_INT_LITERALS
set_int_reu_params_from_x:
    lda #ACTC_INT_REU_BASE_LO
    sta file_params+0
    lda #ACTC_INT_REU_BASE_HI
    sta file_params+1
    lda #ACTC_INT_REU_BASE_BANK
    sta file_params+2
set_int_reu_params_from_x_loop:
    cpx #$00
    beq set_int_reu_params_from_x_done
    clc
    lda file_params+0
    adc #2
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

load_int_literal_from_reu_x:
    txa
    pha
    jsr set_int_reu_params_from_x
    lda #<int_literal_window
    sta file_params+3
    lda #>int_literal_window
    sta file_params+4
    lda #2
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_int_literal_from_reu_x_ok
    pla
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_int_literal_from_reu_x_ok:
    pla
    tax
    rts

store_int_literal_to_reu_x:
    txa
    pha
    jsr set_int_reu_params_from_x
    lda #<int_literal_window
    sta file_params+3
    lda #>int_literal_window
    sta file_params+4
    lda #2
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_int_literal_to_reu_x_ok
    pla
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_int_literal_to_reu_x_ok:
    pla
    tax
    rts
.endif

.if ACTC_REU_VAR_META
set_var_meta_reu_params_from_x:
    lda #ACTC_VAR_META_REU_BASE_LO
    sta file_params+0
    lda #ACTC_VAR_META_REU_BASE_HI
    sta file_params+1
    lda #ACTC_VAR_META_REU_BASE_BANK
    sta file_params+2
set_var_meta_reu_params_from_x_loop:
    cpx #$00
    beq set_var_meta_reu_params_from_x_done
    clc
    lda file_params+0
    adc #4
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

load_var_meta_from_reu_x:
    txa
    pha
    jsr set_var_meta_reu_params_from_x
    lda #<var_meta_window
    sta file_params+3
    lda #>var_meta_window
    sta file_params+4
    lda #4
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_var_meta_from_reu_x_ok
    pla
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_var_meta_from_reu_x_ok:
    pla
    tax
    rts

store_var_meta_to_reu_x:
    txa
    pha
    jsr set_var_meta_reu_params_from_x
    lda #<var_meta_window
    sta file_params+3
    lda #>var_meta_window
    sta file_params+4
    lda #4
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_var_meta_to_reu_x_ok
    pla
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_var_meta_to_reu_x_ok:
    pla
    tax
    rts
.endif

.if ACTC_REU_PROC_META
set_proc_meta_reu_params_from_x:
    lda #ACTC_PROC_META_REU_BASE_LO
    sta file_params+0
    lda #ACTC_PROC_META_REU_BASE_HI
    sta file_params+1
    lda #ACTC_PROC_META_REU_BASE_BANK
    sta file_params+2
set_proc_meta_reu_params_from_x_loop:
    cpx #$00
    beq set_proc_meta_reu_params_from_x_done
    clc
    lda file_params+0
    adc #4
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_proc_meta_reu_params_from_x_loop
set_proc_meta_reu_params_from_x_done:
    rts

load_proc_meta_from_reu_x:
    txa
    pha
    jsr set_proc_meta_reu_params_from_x
    lda #<proc_meta_window
    sta file_params+3
    lda #>proc_meta_window
    sta file_params+4
    lda #4
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_proc_meta_from_reu_x_ok
    pla
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_proc_meta_from_reu_x_ok:
    pla
    tax
    rts

store_proc_meta_to_reu_x:
    txa
    pha
    jsr set_proc_meta_reu_params_from_x
    lda #<proc_meta_window
    sta file_params+3
    lda #>proc_meta_window
    sta file_params+4
    lda #4
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_proc_meta_to_reu_x_ok
    pla
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_proc_meta_to_reu_x_ok:
    pla
    tax
    rts

init_proc_meta_reu:
    lda #$00
    sta proc_meta_param_count_data
    sta proc_meta_param_base_data
    sta proc_meta_local_count_data
    sta proc_meta_local_base_data
    ldx #$00
init_proc_meta_reu_loop:
    txa
    pha
    jsr store_proc_meta_to_reu_x
    pla
    tax
    inx
    cpx #EXPORT_MAX
    bcc init_proc_meta_reu_loop
    rts
.endif

.if ACTC_REU_PROC_DEBUG
set_proc_debug_reu_params_from_x:
    lda #ACTC_PROC_DEBUG_REU_BASE_LO
    sta file_params+0
    lda #ACTC_PROC_DEBUG_REU_BASE_HI
    sta file_params+1
    lda #ACTC_PROC_DEBUG_REU_BASE_BANK
    sta file_params+2
set_proc_debug_reu_params_from_x_loop:
    cpx #$00
    beq set_proc_debug_reu_params_from_x_done
    clc
    lda file_params+0
    adc #3
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_proc_debug_reu_params_from_x_loop
set_proc_debug_reu_params_from_x_done:
    rts

load_proc_debug_offset_from_reu_x:
    txa
    pha
    jsr set_proc_debug_reu_params_from_x
    lda #<proc_debug_offset_window
    sta file_params+3
    lda #>proc_debug_offset_window
    sta file_params+4
    lda #3
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_proc_debug_offset_from_reu_x_ok
    pla
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_proc_debug_offset_from_reu_x_ok:
    pla
    tax
    rts

store_proc_debug_offset_to_reu_x:
    txa
    pha
    jsr set_proc_debug_reu_params_from_x
    lda #<proc_debug_offset_window
    sta file_params+3
    lda #>proc_debug_offset_window
    sta file_params+4
    lda #3
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_proc_debug_offset_to_reu_x_ok
    pla
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_proc_debug_offset_to_reu_x_ok:
    pla
    tax
    rts

snapshot_current_scan_source_offset:
.if ACTC_REU_SOURCE_CACHE
    sec
    lda source_window_next_offset
    sbc source_window_len
    sta proc_debug_offset_data
    lda source_window_next_offset+1
    sbc source_window_len+1
    sta proc_debug_offset_data+1
    lda source_window_next_offset+2
    sbc #$00
    sta proc_debug_offset_data+2
    clc
    lda proc_debug_offset_data
    adc scan_ptr
    sta proc_debug_offset_data
    lda proc_debug_offset_data+1
    adc scan_ptr+1
    sta proc_debug_offset_data+1
    lda proc_debug_offset_data+2
    adc #$00
    sta proc_debug_offset_data+2
    sec
    lda proc_debug_offset_data
    sbc #<source_buffer
    sta proc_debug_offset_data
    lda proc_debug_offset_data+1
    sbc #>source_buffer
    sta proc_debug_offset_data+1
    lda proc_debug_offset_data+2
    sbc #$00
    sta proc_debug_offset_data+2
.else
    lda scan_ptr
    sec
    sbc #<source_buffer
    sta proc_debug_offset_data
    lda scan_ptr+1
    sbc #>source_buffer
    sta proc_debug_offset_data+1
    lda #$00
    sta proc_debug_offset_data+2
.endif
    rts

store_proc_debug_offset_from_current_scan_x:
    txa
    pha
    jsr snapshot_current_scan_source_offset
    pla
    tax
    jmp store_proc_debug_offset_to_reu_x

.if ACTC_REU_VAR_DEBUG
set_var_debug_reu_params_from_x:
    lda #ACTC_VAR_DEBUG_REU_BASE_LO
    sta file_params+0
    lda #ACTC_VAR_DEBUG_REU_BASE_HI
    sta file_params+1
    lda #ACTC_VAR_DEBUG_REU_BASE_BANK
    sta file_params+2
set_var_debug_reu_params_from_x_loop:
    cpx #$00
    beq set_var_debug_reu_params_from_x_done
    clc
    lda file_params+0
    adc #3
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_var_debug_reu_params_from_x_loop
set_var_debug_reu_params_from_x_done:
    rts

store_var_debug_offset_to_reu_x:
    txa
    pha
    jsr set_var_debug_reu_params_from_x
    lda #<proc_debug_offset_window
    sta file_params+3
    lda #>proc_debug_offset_window
    sta file_params+4
    lda #3
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_var_debug_offset_to_reu_x_ok
    pla
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_var_debug_offset_to_reu_x_ok:
    pla
    tax
    rts

load_var_debug_offset_from_reu_x:
    txa
    pha
    jsr set_var_debug_reu_params_from_x
    lda #<proc_debug_offset_window
    sta file_params+3
    lda #>proc_debug_offset_window
    sta file_params+4
    lda #3
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_var_debug_offset_from_reu_x_ok
    pla
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_var_debug_offset_from_reu_x_ok:
    pla
    tax
    rts

store_var_debug_offset_from_current_scan_x:
    txa
    pha
    jsr snapshot_current_scan_source_offset
    pla
    tax
    jmp store_var_debug_offset_to_reu_x

load_var_debug_linecol_from_reu_x:
    txa
    pha
    jsr load_var_debug_offset_from_reu_x
    jsr load_linecol_from_loaded_debug_offset
    pla
    tax
    rts
.endif

load_proc_debug_linecol_from_reu_x:
    txa
    pha
    jsr load_proc_debug_offset_from_reu_x
    jsr load_linecol_from_loaded_debug_offset
    pla
    tax
    rts

load_linecol_from_loaded_debug_offset:
    lda #$01
    sta proc_debug_line_data
    lda #$00
    sta proc_debug_line_data+1
    lda #$01
    sta proc_debug_col_data
    lda #$00
    sta proc_debug_col_data+1
    lda #$00
    sta proc_debug_prev_cr
    lda proc_debug_offset_data
    sta proc_debug_remaining_data
    lda proc_debug_offset_data+1
    sta proc_debug_remaining_data+1
    lda proc_debug_offset_data+2
    sta proc_debug_remaining_data+2
    lda #$00
    sta proc_debug_scan_offset
    sta proc_debug_scan_offset+1
    sta proc_debug_scan_offset+2
load_proc_debug_linecol_loop:
    lda proc_debug_remaining_data
    ora proc_debug_remaining_data+1
    ora proc_debug_remaining_data+2
    beq load_proc_debug_linecol_done
    lda proc_debug_remaining_data+2
    bne load_proc_debug_linecol_full_chunk
    lda proc_debug_remaining_data+1
    bne load_proc_debug_linecol_full_chunk
    lda proc_debug_remaining_data
    cmp #PROC_DEBUG_SCAN_CHUNK_SIZE
    bcc load_proc_debug_linecol_chunk_ready
load_proc_debug_linecol_full_chunk:
    lda #PROC_DEBUG_SCAN_CHUNK_SIZE
load_proc_debug_linecol_chunk_ready:
    sta proc_debug_chunk_len
    jsr read_proc_debug_chunk_from_reu_or_fail
    ldx #$00
load_proc_debug_linecol_chunk_loop:
    cpx proc_debug_chunk_len
    beq load_proc_debug_linecol_advance_offset
    lda proc_debug_scan_buffer,x
    jsr update_proc_debug_linecol_from_char
    inx
    bne load_proc_debug_linecol_chunk_loop
load_proc_debug_linecol_advance_offset:
    clc
    lda proc_debug_scan_offset
    adc proc_debug_chunk_len
    sta proc_debug_scan_offset
    lda proc_debug_scan_offset+1
    adc #$00
    sta proc_debug_scan_offset+1
    lda proc_debug_scan_offset+2
    adc #$00
    sta proc_debug_scan_offset+2
    sec
    lda proc_debug_remaining_data
    sbc proc_debug_chunk_len
    sta proc_debug_remaining_data
    lda proc_debug_remaining_data+1
    sbc #$00
    sta proc_debug_remaining_data+1
    lda proc_debug_remaining_data+2
    sbc #$00
    sta proc_debug_remaining_data+2
    jmp load_proc_debug_linecol_loop
load_proc_debug_linecol_done:
    rts

read_proc_debug_chunk_from_reu_or_fail:
    lda #ACTC_SOURCE_REU_BASE_LO
    clc
    adc proc_debug_scan_offset
    sta file_params+0
    lda #ACTC_SOURCE_REU_BASE_HI
    adc proc_debug_scan_offset+1
    sta file_params+1
    lda #ACTC_SOURCE_REU_BASE_BANK
    adc proc_debug_scan_offset+2
    sta file_params+2
    lda #<proc_debug_scan_buffer
    sta file_params+3
    lda #>proc_debug_scan_buffer
    sta file_params+4
    lda proc_debug_chunk_len
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq read_proc_debug_chunk_from_reu_or_fail_ok
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
read_proc_debug_chunk_from_reu_or_fail_ok:
    rts

update_proc_debug_linecol_from_char:
    cmp #13
    beq update_proc_debug_linecol_from_char_cr
    cmp #10
    beq update_proc_debug_linecol_from_char_lf
    lda #$00
    sta proc_debug_prev_cr
    inc proc_debug_col_data
    bne update_proc_debug_linecol_from_char_done
    inc proc_debug_col_data+1
update_proc_debug_linecol_from_char_done:
    rts
update_proc_debug_linecol_from_char_cr:
    inc proc_debug_line_data
    bne :+
    inc proc_debug_line_data+1
:
    lda #$01
    sta proc_debug_col_data
    lda #$00
    sta proc_debug_col_data+1
    lda #$01
    sta proc_debug_prev_cr
    rts
update_proc_debug_linecol_from_char_lf:
    lda proc_debug_prev_cr
    beq update_proc_debug_linecol_from_char_lf_newline
    lda #$00
    sta proc_debug_prev_cr
    rts
update_proc_debug_linecol_from_char_lf_newline:
    inc proc_debug_line_data
    bne :+
    inc proc_debug_line_data+1
:
    lda #$01
    sta proc_debug_col_data
    lda #$00
    sta proc_debug_col_data+1
    rts

init_proc_debug_reu:
    lda #$00
    sta proc_debug_offset_data
    sta proc_debug_offset_data+1
    sta proc_debug_offset_data+2
    ldx #$00
init_proc_debug_reu_loop:
    txa
    pha
    jsr store_proc_debug_offset_to_reu_x
    pla
    tax
    inx
    cpx #EXPORT_MAX
    bcc init_proc_debug_reu_loop
    rts
.endif

.if ACTC_REU_BODY_DEBUG
init_body_debug_reu:
    lda #$00
    ldx #$00
init_body_debug_reu_loop:
    sta body_debug_count_data,x
    inx
    cpx #EXPORT_MAX
    bcc init_body_debug_reu_loop
    lda #$00
    sta body_debug_current_offset_data
    sta body_debug_current_offset_data+1
    sta body_debug_current_offset_data+2
    rts

store_current_body_debug_mark_from_scan_ptr:
    jsr snapshot_current_scan_source_offset
    lda proc_debug_offset_data
    sta body_debug_current_offset_data
    lda proc_debug_offset_data+1
    sta body_debug_current_offset_data+1
    lda proc_debug_offset_data+2
    sta body_debug_current_offset_data+2
    rts

set_body_debug_reu_params_from_xy:
    txa
    pha
    tya
    pha
    lda #ACTC_BODY_DEBUG_REU_BASE_LO
    sta file_params+0
    lda #ACTC_BODY_DEBUG_REU_BASE_HI
    sta file_params+1
    lda #ACTC_BODY_DEBUG_REU_BASE_BANK
    sta file_params+2
set_body_debug_reu_params_from_xy_proc_loop:
    cpx #$00
    beq set_body_debug_reu_params_from_xy_proc_done
    clc
    lda file_params+0
    adc #<(BODY_OPS_STRIDE * 3)
    sta file_params+0
    lda file_params+1
    adc #>(BODY_OPS_STRIDE * 3)
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_body_debug_reu_params_from_xy_proc_loop
set_body_debug_reu_params_from_xy_proc_done:
    pla
    tay
set_body_debug_reu_params_from_xy_op_loop:
    cpy #$00
    beq set_body_debug_reu_params_from_xy_done
    clc
    lda file_params+0
    adc #3
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dey
    bne set_body_debug_reu_params_from_xy_op_loop
set_body_debug_reu_params_from_xy_done:
    pla
    tax
    rts

load_body_debug_offset_from_reu_xy:
    txa
    pha
    tya
    pha
    jsr set_body_debug_reu_params_from_xy
    lda #<proc_debug_offset_window
    sta file_params+3
    lda #>proc_debug_offset_window
    sta file_params+4
    lda #3
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_body_debug_offset_from_reu_xy_ok
    pla
    tay
    pla
    tax
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_body_debug_offset_from_reu_xy_ok:
    pla
    tay
    pla
    tax
    rts

store_body_debug_offset_to_reu_xy:
    txa
    pha
    tya
    pha
    jsr set_body_debug_reu_params_from_xy
    lda #<proc_debug_offset_window
    sta file_params+3
    lda #>proc_debug_offset_window
    sta file_params+4
    lda #3
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_body_debug_offset_to_reu_xy_ok
    pla
    tay
    pla
    tax
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_body_debug_offset_to_reu_xy_ok:
    pla
    tay
    pla
    tax
    rts

record_body_debug_offset_for_current_proc:
    ldx current_proc_index_data
    cpx #$FF
    bne :+
    rts
:   lda body_debug_count_data,x
    cmp #BODY_OPS_STRIDE
    bcc :+
    lda #<msg_bad_call
    ldy #>msg_bad_call
    jmp fail_with_ptr
:   tay
    lda body_debug_current_offset_data
    sta proc_debug_offset_data
    lda body_debug_current_offset_data+1
    sta proc_debug_offset_data+1
    lda body_debug_current_offset_data+2
    sta proc_debug_offset_data+2
    jsr store_body_debug_offset_to_reu_xy
    inc body_debug_count_data,x
    rts

load_body_debug_linecol_from_xy:
    jsr load_body_debug_offset_from_reu_xy
    jmp load_linecol_from_loaded_debug_offset
.endif

.if ACTC_REU_LAYOUT_META
set_layout_reu_params_from_x:
    lda #ACTC_LAYOUT_REU_BASE_LO
    sta file_params+0
    lda #ACTC_LAYOUT_REU_BASE_HI
    sta file_params+1
    lda #ACTC_LAYOUT_REU_BASE_BANK
    sta file_params+2
set_layout_reu_params_from_x_loop:
    cpx #$00
    beq set_layout_reu_params_from_x_done
    clc
    lda file_params+0
    adc #4
    sta file_params+0
    lda file_params+1
    adc #$00
    sta file_params+1
    lda file_params+2
    adc #$00
    sta file_params+2
    dex
    bne set_layout_reu_params_from_x_loop
set_layout_reu_params_from_x_done:
    rts

load_layout_from_reu_x:
    txa
    pha
    jsr set_layout_reu_params_from_x
    lda #<layout_window
    sta file_params+3
    lda #>layout_window
    sta file_params+4
    lda #4
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_read_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq load_layout_from_reu_x_ok
    pla
    lda #<msg_load_fail
    ldy #>msg_load_fail
    jmp fail_with_ptr
load_layout_from_reu_x_ok:
    pla
    tax
    rts

store_layout_to_reu_x:
    txa
    pha
    jsr set_layout_reu_params_from_x
    lda #<layout_window
    sta file_params+3
    lda #>layout_window
    sta file_params+4
    lda #4
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_layout_to_reu_x_ok
    pla
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_layout_to_reu_x_ok:
    pla
    tax
    rts
.endif

.if ACTC_REU_STRING_OFFSETS
set_string_offset_reu_params_from_x:
    lda #ACTC_STRING_OFFSET_REU_BASE_LO
    sta file_params+0
    lda #ACTC_STRING_OFFSET_REU_BASE_HI
    sta file_params+1
    lda #ACTC_STRING_OFFSET_REU_BASE_BANK
    sta file_params+2
    txa
    clc
    adc file_params+0
    sta file_params+0
    bcc set_string_offset_reu_params_from_x_done
    inc file_params+1
    bne set_string_offset_reu_params_from_x_done
    inc file_params+2
set_string_offset_reu_params_from_x_done:
    rts

store_string_offset_to_reu_x:
    txa
    pha
    jsr set_string_offset_reu_params_from_x
    lda #<string_offset_window
    sta file_params+3
    lda #>string_offset_window
    sta file_params+4
    lda #1
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    ldx #file_params
    jsr svc_reu_write_sc0
    lda file_params+7
    cmp #tool_file_status_ok
    beq store_string_offset_to_reu_x_ok
    pla
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
store_string_offset_to_reu_x_ok:
    pla
    tax
    rts
.endif

copy_symbol_from_scan_ptr:
    ldy #$00
copy_symbol_from_scan_ptr_loop:
    lda (scan_ptr),y
    beq copy_symbol_from_scan_ptr_done
    jsr uppercase_ascii
    cpy #$00
    bne copy_symbol_from_scan_ptr_body
    jsr uppercase_symbol_start_valid
    bcc copy_symbol_from_scan_ptr_store
    jmp copy_symbol_from_scan_ptr_done
copy_symbol_from_scan_ptr_body:
    jsr uppercase_symbol_body_valid
    bcc copy_symbol_from_scan_ptr_store
    jmp copy_symbol_from_scan_ptr_done
copy_symbol_from_scan_ptr_store:
    sta declared_module_name,y
    iny
    cpy #24
    bcc copy_symbol_from_scan_ptr_loop
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_ptr
copy_symbol_from_scan_ptr_done:
    cpy #$00
    beq copy_symbol_from_scan_ptr_fail
    pha
    lda #$00
    sta declared_module_name,y
    pla
    clc
    rts
copy_symbol_from_scan_ptr_fail:
    sec
    rts

copy_symbol_from_scan_y:
    txa
    pha
    ldx #$00
copy_symbol_from_scan_y_loop:
    lda (scan_ptr),y
    beq copy_symbol_from_scan_y_done_check
    jsr uppercase_ascii
    cpx #$00
    bne copy_symbol_from_scan_y_body
    jsr uppercase_symbol_start_valid
    bcc copy_symbol_from_scan_y_store
    jmp copy_symbol_from_scan_y_done_check
copy_symbol_from_scan_y_body:
    jsr uppercase_symbol_body_valid
    bcc copy_symbol_from_scan_y_store
    jmp copy_symbol_from_scan_y_done_check
copy_symbol_from_scan_y_store:
    sta declared_module_name,x
    jsr advance_scan_y
    inx
    cpx #24
    bcc copy_symbol_from_scan_y_loop
copy_symbol_from_scan_y_fail:
    pla
    tax
    sec
    rts
copy_symbol_from_scan_y_done_check:
    cpx #$00
    beq copy_symbol_from_scan_y_fail
    lda #$00
    sta declared_module_name,x
    pla
    tax
    clc
    rts

consume_and_keyword_from_scan_y:
    lda #<pattern_and
    sta const_ptr
    lda #>pattern_and
    sta const_ptr+1
    jmp consume_keyword_from_scan_y

consume_or_keyword_from_scan_y:
    lda #<pattern_or
    sta const_ptr
    lda #>pattern_or
    sta const_ptr+1
    jmp consume_keyword_from_scan_y

consume_not_keyword_from_scan_y:
    lda #<pattern_not
    sta const_ptr
    lda #>pattern_not
    sta const_ptr+1

consume_keyword_from_scan_y:
    sty hex_work
    jsr save_source_reader_mark
    jsr skip_inline_spaces_at_scan_y
    jsr copy_symbol_from_scan_y
    bcc :+
    jmp consume_keyword_from_scan_y_fail_restore
:   sty compare_char
    jsr symbol_buffer_matches_const_ptr
    bcc :+
    jmp consume_keyword_from_scan_y_fail_restore
:   ldy compare_char
    clc
    rts
consume_keyword_from_scan_y_fail_restore:
    jsr restore_source_reader_mark
    ldy hex_work
    sec
    rts

symbol_buffer_matches_const_ptr:
    ldy #$00
symbol_buffer_matches_const_ptr_loop:
    lda (const_ptr),y
    cmp declared_module_name,y
    bne symbol_buffer_matches_const_ptr_fail
    lda declared_module_name,y
    beq symbol_buffer_matches_const_ptr_done
    iny
    bne symbol_buffer_matches_const_ptr_loop
symbol_buffer_matches_const_ptr_fail:
    sec
    rts
symbol_buffer_matches_const_ptr_done:
    clc
    rts

find_var_index_from_scan_y:
    sty symbol_start_y_data
    jsr copy_symbol_from_scan_y
    bcc :+
    ldy symbol_start_y_data
    sec
    rts
:   sty symbol_end_y_data
    jsr find_var_index_from_declared
    bcc :+
    ldy symbol_start_y_data
    sec
    rts
:   ldy symbol_end_y_data
    clc
    rts

find_export_index_from_declared:
    ldx #$00
find_export_index_from_declared_loop:
    cpx export_count_data
    beq find_export_index_from_declared_fail
    stx hex_work
    jsr set_export_ptr_from_x
    ldx hex_work
    ldy #$00
find_export_index_from_declared_compare_loop:
    lda (export_ptr),y
    cmp declared_module_name,y
    bne find_export_index_from_declared_next
    lda declared_module_name,y
    beq find_export_index_from_declared_done
    iny
    bne find_export_index_from_declared_compare_loop
find_export_index_from_declared_next:
    inx
    bne find_export_index_from_declared_loop
find_export_index_from_declared_fail:
    sec
    rts
find_export_index_from_declared_done:
    clc
    rts

find_var_index_from_declared:
    lda current_proc_index_data
    cmp #$FF
    beq find_module_var_index_from_declared
    tax
    jsr find_current_proc_local_index_from_declared_for_proc_x
    bcc find_var_index_from_declared_done
    ldx current_proc_index_data
    jsr find_current_proc_param_index_from_declared_for_proc_x
    bcs find_module_var_index_from_declared
    clc
    rts

find_module_var_index_from_declared:
    ldx #$00
find_module_var_index_from_declared_loop:
    cpx module_var_count_data
    beq find_var_index_from_declared_fail
    stx hex_work
    jsr set_var_ptr_from_x
    ldx hex_work
    ldy #$00
find_module_var_index_from_declared_compare_loop:
    lda (export_ptr),y
    cmp declared_module_name,y
    bne find_module_var_index_from_declared_next
    lda declared_module_name,y
    beq find_var_index_from_declared_done
    iny
    bne find_module_var_index_from_declared_compare_loop
find_module_var_index_from_declared_next:
    inx
    bne find_module_var_index_from_declared_loop
find_var_index_from_declared_fail:
    sec
    rts
find_var_index_from_declared_done:
    clc
    rts

require_var_index_word_or_fail:
    tya
    pha
.if ACTC_REU_VAR_META
    jsr load_var_meta_from_reu_x
    lda var_meta_width_data
.else
    lda var_width_data,x
.endif
    cmp #$02
    beq require_var_index_word_or_fail_ok
    pla
    tay
    sec
    rts
require_var_index_word_or_fail_ok:
    pla
    tay
    clc
    rts

require_var_index_real_or_fail:
    tya
    pha
.if ACTC_REU_VAR_META
    jsr load_var_meta_from_reu_x
    lda var_meta_width_data
.else
    lda var_width_data,x
.endif
    cmp #$04
    beq require_var_index_real_or_fail_ok
    pla
    tay
    sec
    rts
require_var_index_real_or_fail_ok:
    pla
    tay
    clc
    rts

require_var_index_real_bridge_word_or_fail:
    tya
    pha
.if ACTC_REU_VAR_META
    jsr load_var_meta_from_reu_x
    lda var_meta_width_data
    cmp #$02
    bne require_var_index_real_bridge_word_or_fail_fail
    lda var_meta_type_data
.else
    lda var_width_data,x
    cmp #$02
    bne require_var_index_real_bridge_word_or_fail_fail
    lda var_type_data,x
.endif
    cmp #'b'
    beq require_var_index_real_bridge_word_or_fail_ok
    cmp #'c'
    beq require_var_index_real_bridge_word_or_fail_ok
    cmp #'i'
    beq require_var_index_real_bridge_word_or_fail_ok
require_var_index_real_bridge_word_or_fail_fail:
    pla
    tay
    sec
    rts
require_var_index_real_bridge_word_or_fail_ok:
    pla
    tay
    clc
    rts

find_current_proc_param_index_from_declared_for_proc_x:
    stx proc_index
.if ACTC_REU_PROC_META
    jsr load_proc_meta_from_reu_x
    lda proc_meta_param_count_data
    beq find_current_proc_param_index_from_declared_for_proc_x_fail
    lda proc_meta_param_base_data
    sta hex_work
find_current_proc_param_index_from_declared_for_proc_x_loop:
    lda proc_meta_param_base_data
    clc
    adc proc_meta_param_count_data
    sta compare_char
.else
    lda proc_param_count_data,x
    beq find_current_proc_param_index_from_declared_for_proc_x_fail
    lda proc_param_var_base_data,x
    sta hex_work
find_current_proc_param_index_from_declared_for_proc_x_loop:
    ldx proc_index
    lda proc_param_var_base_data,x
    clc
    adc proc_param_count_data,x
    sta compare_char
.endif
    ldx hex_work
    cpx compare_char
    beq find_current_proc_param_index_from_declared_for_proc_x_fail
    stx hex_work
    jsr set_var_ptr_from_x
    ldx hex_work
    ldy #$00
find_current_proc_param_index_from_declared_for_proc_x_compare_loop:
    lda (export_ptr),y
    cmp declared_module_name,y
    bne find_current_proc_param_index_from_declared_for_proc_x_next
    lda declared_module_name,y
    bne :+
    jmp find_var_index_from_declared_done
:
    iny
    bne find_current_proc_param_index_from_declared_for_proc_x_compare_loop
find_current_proc_param_index_from_declared_for_proc_x_next:
    inc hex_work
    jmp find_current_proc_param_index_from_declared_for_proc_x_loop
find_current_proc_param_index_from_declared_for_proc_x_fail:
    sec
    rts

find_current_proc_local_index_from_declared_for_proc_x:
    stx proc_index
.if ACTC_REU_PROC_META
    jsr load_proc_meta_from_reu_x
    lda proc_meta_local_count_data
    beq find_current_proc_local_index_from_declared_for_proc_x_fail
    lda proc_meta_local_base_data
    sta hex_work
find_current_proc_local_index_from_declared_for_proc_x_loop:
    lda proc_meta_local_base_data
    clc
    adc proc_meta_local_count_data
    sta compare_char
.else
    lda proc_local_count_data,x
    beq find_current_proc_local_index_from_declared_for_proc_x_fail
    lda proc_local_var_base_data,x
    sta hex_work
find_current_proc_local_index_from_declared_for_proc_x_loop:
    ldx proc_index
    lda proc_local_var_base_data,x
    clc
    adc proc_local_count_data,x
    sta compare_char
.endif
    ldx hex_work
    cpx compare_char
    beq find_current_proc_local_index_from_declared_for_proc_x_fail
    stx hex_work
    jsr set_var_ptr_from_x
    ldx hex_work
    ldy #$00
find_current_proc_local_index_from_declared_for_proc_x_compare_loop:
    lda (export_ptr),y
    cmp declared_module_name,y
    bne find_current_proc_local_index_from_declared_for_proc_x_next
    lda declared_module_name,y
    beq find_current_proc_local_index_from_declared_for_proc_x_done
    iny
    bne find_current_proc_local_index_from_declared_for_proc_x_compare_loop
find_current_proc_local_index_from_declared_for_proc_x_next:
    inc hex_work
    jmp find_current_proc_local_index_from_declared_for_proc_x_loop
find_current_proc_local_index_from_declared_for_proc_x_done:
    clc
    rts
find_current_proc_local_index_from_declared_for_proc_x_fail:
    sec
    rts

find_or_store_rt_f_add_external:
    lda #<runtime_symbol_rt_f_add
    sta const_ptr
    lda #>runtime_symbol_rt_f_add
    sta const_ptr+1
    jsr copy_const_ptr_to_declared_module_name
    jmp find_or_store_external_from_declared

find_or_store_rt_f_sub_external:
    lda #<runtime_symbol_rt_f_sub
    sta const_ptr
    lda #>runtime_symbol_rt_f_sub
    sta const_ptr+1
    jsr copy_const_ptr_to_declared_module_name
    jmp find_or_store_external_from_declared

find_or_store_rt_f_mul_external:
    lda #<runtime_symbol_rt_f_mul
    sta const_ptr
    lda #>runtime_symbol_rt_f_mul
    sta const_ptr+1
    jsr copy_const_ptr_to_declared_module_name
    jmp find_or_store_external_from_declared

find_or_store_rt_f_div_external:
    lda #<runtime_symbol_rt_f_div
    sta const_ptr
    lda #>runtime_symbol_rt_f_div
    sta const_ptr+1
    jsr copy_const_ptr_to_declared_module_name
    jmp find_or_store_external_from_declared

find_or_store_rt_f_cmp_external:
    lda #<runtime_symbol_rt_f_cmp
    sta const_ptr
    lda #>runtime_symbol_rt_f_cmp
    sta const_ptr+1
    jsr copy_const_ptr_to_declared_module_name
    jmp find_or_store_external_from_declared

find_or_store_rt_i_to_f_external:
    lda #<runtime_symbol_rt_i_to_f
    sta const_ptr
    lda #>runtime_symbol_rt_i_to_f
    sta const_ptr+1
    jsr copy_const_ptr_to_declared_module_name
    jmp find_or_store_external_from_declared

find_or_store_rt_f_to_i_external:
    lda #<runtime_symbol_rt_f_to_i
    sta const_ptr
    lda #>runtime_symbol_rt_f_to_i
    sta const_ptr+1
    jsr copy_const_ptr_to_declared_module_name
    jmp find_or_store_external_from_declared

find_or_store_rt_s_to_f_external:
    lda #<runtime_symbol_rt_s_to_f
    sta const_ptr
    lda #>runtime_symbol_rt_s_to_f
    sta const_ptr+1
    jsr copy_const_ptr_to_declared_module_name
    jmp find_or_store_external_from_declared

find_or_store_rt_print_f_external:
    lda #<runtime_symbol_rt_print_f
    sta const_ptr
    lda #>runtime_symbol_rt_print_f
    sta const_ptr+1
    jsr copy_const_ptr_to_declared_module_name
    jmp find_or_store_external_from_declared

find_or_store_real_bridge_external_from_x:
.if ACTC_REU_VAR_META
    jsr load_var_meta_from_reu_x
    lda var_meta_type_data
.else
    lda var_type_data,x
.endif
    cmp #'i'
    beq find_or_store_rt_s_to_f_external
    jmp find_or_store_rt_i_to_f_external

find_or_store_real_operator_external_from_a:
    cmp #'+'
    bne :+
    jmp find_or_store_rt_f_add_external
:   cmp #'-'
    bne :+
    jmp find_or_store_rt_f_sub_external
:   cmp #'*'
    bne :+
    jmp find_or_store_rt_f_mul_external
:   cmp #'/'
    bne :+
    jmp find_or_store_rt_f_div_external
:   sec
    rts

.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
find_or_store_real_operator_external:
    lda real_operator_data
    jmp find_or_store_real_operator_external_from_a
.endif

find_or_store_builtin_runtime_external_from_declared:
    lda #<builtin_symbol_sid_freq
    sta const_ptr
    lda #>builtin_symbol_sid_freq
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #$02
    sta call_expected_arg_count
    lda #<runtime_symbol_rt_sid_freq
    ldy #>runtime_symbol_rt_sid_freq
    jmp find_or_store_runtime_external_from_ay
:
    lda #<builtin_symbol_sid_wave
    sta const_ptr
    lda #>builtin_symbol_sid_wave
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #$02
    sta call_expected_arg_count
    lda #<runtime_symbol_rt_sid_wave
    ldy #>runtime_symbol_rt_sid_wave
    jmp find_or_store_runtime_external_from_ay
:
    lda #<builtin_symbol_sid_ad
    sta const_ptr
    lda #>builtin_symbol_sid_ad
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #$02
    sta call_expected_arg_count
    lda #<runtime_symbol_rt_sid_ad
    ldy #>runtime_symbol_rt_sid_ad
    jmp find_or_store_runtime_external_from_ay
:
    lda #<builtin_symbol_sid_sr
    sta const_ptr
    lda #>builtin_symbol_sid_sr
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #$02
    sta call_expected_arg_count
    lda #<runtime_symbol_rt_sid_sr
    ldy #>runtime_symbol_rt_sid_sr
    jmp find_or_store_runtime_external_from_ay
:
    lda #<builtin_symbol_sid_vol
    sta const_ptr
    lda #>builtin_symbol_sid_vol
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #$01
    sta call_expected_arg_count
    lda #<runtime_symbol_rt_sid_vol
    ldy #>runtime_symbol_rt_sid_vol
    jmp find_or_store_runtime_external_from_ay
:
    lda #<builtin_symbol_sprite_on
    sta const_ptr
    lda #>builtin_symbol_sprite_on
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #$01
    sta call_expected_arg_count
    lda #<runtime_symbol_rt_sprite_on
    ldy #>runtime_symbol_rt_sprite_on
    jmp find_or_store_runtime_external_from_ay
:
    lda #<builtin_symbol_sprite_off
    sta const_ptr
    lda #>builtin_symbol_sprite_off
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #$01
    sta call_expected_arg_count
    lda #<runtime_symbol_rt_sprite_off
    ldy #>runtime_symbol_rt_sprite_off
    jmp find_or_store_runtime_external_from_ay
:
    lda #<builtin_symbol_sprite_color
    sta const_ptr
    lda #>builtin_symbol_sprite_color
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #$02
    sta call_expected_arg_count
    lda #<runtime_symbol_rt_sprite_color
    ldy #>runtime_symbol_rt_sprite_color
    jmp find_or_store_runtime_external_from_ay
:
    lda #<builtin_symbol_sprite_pos
    sta const_ptr
    lda #>builtin_symbol_sprite_pos
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #$03
    sta call_expected_arg_count
    lda #<runtime_symbol_rt_sprite_pos
    ldy #>runtime_symbol_rt_sprite_pos
    jmp find_or_store_runtime_external_from_ay
:
    lda #<builtin_symbol_sprite_mc
    sta const_ptr
    lda #>builtin_symbol_sprite_mc
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #$02
    sta call_expected_arg_count
    lda #<runtime_symbol_rt_sprite_mc
    ldy #>runtime_symbol_rt_sprite_mc
    jmp find_or_store_runtime_external_from_ay
:
    lda #<builtin_symbol_sprite_xexp
    sta const_ptr
    lda #>builtin_symbol_sprite_xexp
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #$02
    sta call_expected_arg_count
    lda #<runtime_symbol_rt_sprite_xexp
    ldy #>runtime_symbol_rt_sprite_xexp
    jmp find_or_store_runtime_external_from_ay
:
    lda #<builtin_symbol_sprite_yexp
    sta const_ptr
    lda #>builtin_symbol_sprite_yexp
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #$02
    sta call_expected_arg_count
    lda #<runtime_symbol_rt_sprite_yexp
    ldy #>runtime_symbol_rt_sprite_yexp
    jmp find_or_store_runtime_external_from_ay
:
    lda #<builtin_symbol_sprite_prio
    sta const_ptr
    lda #>builtin_symbol_sprite_prio
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #$02
    sta call_expected_arg_count
    lda #<runtime_symbol_rt_sprite_prio
    ldy #>runtime_symbol_rt_sprite_prio
    jmp find_or_store_runtime_external_from_ay
:
    lda #<builtin_symbol_sprite_data
    sta const_ptr
    lda #>builtin_symbol_sprite_data
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs :+
    lda #$02
    sta call_expected_arg_count
    lda #<runtime_symbol_rt_sprite_data
    ldy #>runtime_symbol_rt_sprite_data
    jmp find_or_store_runtime_external_from_ay
:
    lda #<builtin_symbol_set_sprite_mc
    sta const_ptr
    lda #>builtin_symbol_set_sprite_mc
    sta const_ptr+1
    jsr symbol_buffer_matches_const_ptr
    bcs find_or_store_builtin_runtime_external_from_declared_fail
    lda #$02
    sta call_expected_arg_count
    lda #<runtime_symbol_rt_sprite_set_mc
    ldy #>runtime_symbol_rt_sprite_set_mc
    jmp find_or_store_runtime_external_from_ay
find_or_store_builtin_runtime_external_from_declared_fail:
    sec
    rts

find_or_store_runtime_external_from_ay:
    sta const_ptr
    sty const_ptr+1
    jsr copy_const_ptr_to_declared_module_name
    jmp find_or_store_external_from_declared

copy_const_ptr_to_declared_module_name:
    ldy #$00
copy_const_ptr_to_declared_module_name_loop:
    lda (const_ptr),y
    sta declared_module_name,y
    beq copy_const_ptr_to_declared_module_name_done
    iny
    cpy #25
    bcc copy_const_ptr_to_declared_module_name_loop
    lda #<msg_bad_proc
    ldy #>msg_bad_proc
    jmp fail_with_ptr
copy_const_ptr_to_declared_module_name_done:
    rts

find_or_store_external_from_declared:
    ldx #$00
find_or_store_external_from_declared_loop:
    cpx extern_count_data
    beq find_or_store_external_from_declared_add
    stx hex_work
    jsr set_external_ptr_from_x
    ldx hex_work
    ldy #$00
find_or_store_external_from_declared_compare_loop:
    lda (export_ptr),y
    cmp declared_module_name,y
    bne find_or_store_external_from_declared_next
    lda declared_module_name,y
    beq find_or_store_external_from_declared_done
    iny
    bne find_or_store_external_from_declared_compare_loop
find_or_store_external_from_declared_next:
    inx
    bne find_or_store_external_from_declared_loop
find_or_store_external_from_declared_add:
    ldx extern_count_data
    cpx #EXTERNAL_MAX
    bcc :+
    sec
    rts
:   txa
    pha
    jsr set_external_ptr_from_x
    pla
    tax
    ldy #$00
find_or_store_external_from_declared_copy_loop:
    lda declared_module_name,y
    sta (export_ptr),y
    beq find_or_store_external_from_declared_copy_done
    iny
    cpy #25
    bcc find_or_store_external_from_declared_copy_loop
    sec
    rts
find_or_store_external_from_declared_copy_done:
.if ACTC_REU_TABLES
    jsr store_external_name_to_reu_x
.endif
    inc extern_count_data
find_or_store_external_from_declared_done:
    clc
    rts

detect_runtime_imports:
.if ACTC_USE_IMPORT_OVERLAY
    jsr detect_runtime_imports_with_overlay_if_possible
    bcc detect_runtime_imports_done
.endif
.if ACTC_KEEP_IMPORT_RESIDENT_FALLBACK
    lda #$00
    sta import_flags_lo

    lda #<pattern_print
    sta const_ptr
    lda #>pattern_print
    sta const_ptr+1
    jsr find_pattern_at_const_ptr
    bcs :+
    lda import_flags_lo
    ora #IMPORT_PRINT_STR
    sta import_flags_lo
:   lda #<pattern_printe
    sta const_ptr
    lda #>pattern_printe
    sta const_ptr+1
    jsr find_pattern_at_const_ptr
    bcs :+
    lda import_flags_lo
    ora #IMPORT_PRINT_LINE
    sta import_flags_lo
:   lda #<pattern_printi
    sta const_ptr
    lda #>pattern_printi
    sta const_ptr+1
    jsr find_pattern_at_const_ptr
    bcs :+
    lda import_flags_lo
    ora #IMPORT_FORMAT_INT|IMPORT_PRINT_STR
    sta import_flags_lo
:   lda #<pattern_printie
    sta const_ptr
    lda #>pattern_printie
    sta const_ptr+1
    jsr find_pattern_at_const_ptr
    bcs :+
    lda import_flags_lo
    ora #IMPORT_FORMAT_INT|IMPORT_PRINT_LINE
    sta import_flags_lo
:
.endif
detect_runtime_imports_done:
    rts

.if ACTC_USE_IMPORT_OVERLAY
detect_runtime_imports_with_overlay_if_possible:
    lda #ACTC_OVERLAY_PASS_RUNTIME_IMPORTS
    jsr actc_overlay_run_pass
    bcc detect_runtime_imports_with_overlay_ok
    sec
    rts
detect_runtime_imports_with_overlay_ok:
    cmp #ACTC_OVERLAY_STATUS_OK
    beq :+
    sec
    rts
:
    clc
    rts
.endif

find_pattern_at_const_ptr:
    jsr source_reader_reset_to_start
    bcc :+
    sec
    rts
:
find_pattern_at_const_ptr_loop:
    ldy #$00
    lda (scan_ptr),y
    beq find_pattern_at_const_ptr_fail
    jsr pattern_matches_scan_ptr
    bcc find_pattern_at_const_ptr_ok
    jsr advance_scan_ptr
    jmp find_pattern_at_const_ptr_loop
find_pattern_at_const_ptr_ok:
    clc
    rts
find_pattern_at_const_ptr_fail:
    sec
    rts

pattern_matches_scan_ptr:
    ldy #$00
pattern_matches_scan_ptr_loop:
    lda (const_ptr),y
    beq pattern_matches_scan_ptr_ok
    sta compare_char
    lda (scan_ptr),y
    beq pattern_matches_scan_ptr_fail
    jsr uppercase_ascii
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

pattern_matches_scan_ptr_keyword:
    jsr pattern_matches_scan_ptr
    bcc :+
    sec
    rts
:   ldy #$00
pattern_matches_scan_ptr_keyword_len_loop:
    lda (const_ptr),y
    beq pattern_matches_scan_ptr_keyword_boundary
    iny
    bne pattern_matches_scan_ptr_keyword_len_loop
pattern_matches_scan_ptr_keyword_boundary:
    lda (scan_ptr),y
    beq pattern_matches_scan_ptr_keyword_ok
    cmp #' '
    beq pattern_matches_scan_ptr_keyword_ok
    cmp #9
    beq pattern_matches_scan_ptr_keyword_ok
    cmp #10
    beq pattern_matches_scan_ptr_keyword_ok
    cmp #13
    beq pattern_matches_scan_ptr_keyword_ok
    sec
    rts
pattern_matches_scan_ptr_keyword_ok:
    clc
    rts

match_scalar_decl_at_scan_ptr:
    lda #<pattern_int_decl
    sta const_ptr
    lda #>pattern_int_decl
    sta const_ptr+1
    jsr pattern_matches_scan_ptr_keyword
    bcc match_scalar_decl_at_scan_ptr_width2
    lda #<pattern_byte_decl
    sta const_ptr
    lda #>pattern_byte_decl
    sta const_ptr+1
    jsr pattern_matches_scan_ptr_keyword
    bcc match_scalar_decl_at_scan_ptr_byte
    lda #<pattern_card_decl
    sta const_ptr
    lda #>pattern_card_decl
    sta const_ptr+1
    jsr pattern_matches_scan_ptr_keyword
    bcc match_scalar_decl_at_scan_ptr_card
    lda #<pattern_real_decl
    sta const_ptr
    lda #>pattern_real_decl
    sta const_ptr+1
    jsr pattern_matches_scan_ptr_keyword
    bcc match_scalar_decl_at_scan_ptr_width4
    sec
    rts
match_scalar_decl_at_scan_ptr_width2:
    lda #$02
    sta decl_width_data
    lda #'i'
    sta decl_type_data
    clc
    rts
match_scalar_decl_at_scan_ptr_byte:
    lda #$02
    sta decl_width_data
    lda #'b'
    sta decl_type_data
    clc
    rts
match_scalar_decl_at_scan_ptr_card:
    lda #$02
    sta decl_width_data
    lda #'c'
    sta decl_type_data
    clc
    rts
match_scalar_decl_at_scan_ptr_width4:
    lda #$04
    sta decl_width_data
    lda #'r'
    sta decl_type_data
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

uppercase_ascii:
    cmp #'a'
    bcc uppercase_ascii_done
    cmp #'z'+1
    bcs uppercase_ascii_done
    and #$DF
uppercase_ascii_done:
    rts

uppercase_symbol_start_valid:
    cmp #'A'
    bcc uppercase_symbol_start_valid_fail
    cmp #'Z'+1
    bcs uppercase_symbol_start_valid_fail
    clc
    rts
uppercase_symbol_start_valid_fail:
    sec
    rts

uppercase_symbol_body_valid:
    cmp #'A'
    bcc uppercase_symbol_body_valid_check_digit
    cmp #'Z'+1
    bcc uppercase_symbol_body_valid_ok
uppercase_symbol_body_valid_check_digit:
    cmp #'0'
    bcc uppercase_symbol_body_valid_check_underscore
    cmp #'9'+1
    bcc uppercase_symbol_body_valid_ok
uppercase_symbol_body_valid_check_underscore:
    cmp #'_'
    beq uppercase_symbol_body_valid_ok
    sec
    rts
uppercase_symbol_body_valid_ok:
    clc
    rts

build_object_content:
.if ACTC_USE_EMIT_OVERLAY
    jsr build_object_content_with_overlay_if_possible
    bcc build_object_content_done_entry
.endif
.if ACTC_KEEP_EMIT_RESIDENT_FALLBACK
    jmp build_object_content_resident
.else
    lda #<msg_emit_overlay
    ldy #>msg_emit_overlay
    jmp fail_with_ptr
.endif

.if ACTC_USE_EMIT_OVERLAY
build_object_content_with_overlay_if_possible:
    lda #ACTC_OVERLAY_PASS_EMIT_OBJECT
    jsr actc_overlay_run_pass
    bcc build_object_content_with_overlay_ok
    lda actc_overlay_context+ACTC_OVERLAY_CTX_DIAG_PTR_LO
    ora actc_overlay_context+ACTC_OVERLAY_CTX_DIAG_PTR_HI
    beq build_object_content_with_overlay_fallback
    lda actc_overlay_context+ACTC_OVERLAY_CTX_DIAG_PTR_LO
    ldy actc_overlay_context+ACTC_OVERLAY_CTX_DIAG_PTR_HI
    jmp fail_with_ptr
build_object_content_with_overlay_fallback:
.if ACTC_KEEP_EMIT_RESIDENT_FALLBACK
    sec
    rts
.else
    lda #<msg_emit_overlay
    ldy #>msg_emit_overlay
    jmp fail_with_ptr
.endif
build_object_content_with_overlay_ok:
    cmp #ACTC_OVERLAY_STATUS_OK
    beq :+
    jmp build_object_content_with_overlay_fallback
:
    clc
    rts
.endif

build_object_content_done_entry:
    rts

.if ACTC_USE_BODY_OVERLAY
collect_proc_body_ops_with_overlay_if_possible:
    lda #ACTC_OVERLAY_PASS_BODY_COLLECT
    jsr actc_overlay_run_pass
    bcc collect_proc_body_ops_with_overlay_ok
    lda actc_overlay_context+ACTC_OVERLAY_CTX_DIAG_PTR_LO
    ora actc_overlay_context+ACTC_OVERLAY_CTX_DIAG_PTR_HI
    beq collect_proc_body_ops_with_overlay_fallback
    lda actc_overlay_context+ACTC_OVERLAY_CTX_DIAG_PTR_LO
    ldy actc_overlay_context+ACTC_OVERLAY_CTX_DIAG_PTR_HI
    jmp fail_with_ptr
collect_proc_body_ops_with_overlay_fallback:
.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
    sec
    rts
.else
    lda #<msg_body_overlay
    ldy #>msg_body_overlay
    jmp fail_with_ptr
.endif
collect_proc_body_ops_with_overlay_ok:
    cmp #ACTC_OVERLAY_STATUS_OK
    beq :+
    jmp collect_proc_body_ops_with_overlay_fallback
:
    clc
    rts
.endif

.if ACTC_KEEP_EMIT_RESIDENT_FALLBACK

lowercase_ascii:
    cmp #'A'
    bcc lowercase_ascii_done
    cmp #'Z'+1
    bcs lowercase_ascii_done
    ora #$20
lowercase_ascii_done:
    rts

build_object_content_resident:
.if STREAM_OUTPUT
.else
    lda #<content_buffer
    sta content_ptr
    lda #>content_buffer
    sta content_ptr+1
.endif

    lda #<object_header
    sta const_ptr
    lda #>object_header
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_export_list
    jsr append_body_ops_list
    jsr append_machine_code_list
    jsr append_external_list
    jsr append_string_list
    jsr append_int_list
    jsr append_var_list
    lda #'k'
    jsr append_char
    lda #' '
    jsr append_char
    lda import_flags_lo
    jsr append_small_decimal
    jsr append_newline
    lda #'n'
    jsr append_char
    lda #' '
    jsr append_char
    jsr append_module_symbol_lower
    jsr append_newline

.if STREAM_OUTPUT
    rts
.else
    lda #$00
    jmp append_char
.endif

append_export_list:
    jsr is_main_fanout_machine_object_resident
    bcc append_export_list_not_fanout
    jmp append_machine_fanout_export_list
append_export_list_not_fanout:
    jsr is_main_single_local_call_machine_object_resident
    bcc append_export_list_standard
    jmp append_machine_local_call_export_list
append_export_list_standard:
    lda #$00
    sta export_index
append_export_list_loop:
    ldx export_index
    cpx export_count_data
    beq append_export_list_done
    lda #'x'
    jsr append_char
    lda #' '
    jsr append_char
    ldx export_index
    jsr set_export_ptr_from_x
    ldy #$00
append_export_list_symbol_loop:
    lda (export_ptr),y
    beq append_export_list_symbol_done
    jsr lowercase_ascii
    jsr append_char
    iny
    bne append_export_list_symbol_loop
append_export_list_symbol_done:
    lda #' '
    jsr append_char
    ldx export_index
.if ACTC_REU_LAYOUT_META
    jsr load_layout_from_reu_x
    lda layout_offset_lo_data
    ldy layout_offset_hi_data
.else
    lda export_offsets,x
    ldy export_offsets_hi,x
.endif
    jsr append_word_decimal
    lda #' '
    jsr append_char
    ldx export_index
    lda export_index
    bne append_export_list_layout_size
    jsr is_empty_main_machine_object_resident
    bcc append_export_list_layout_size
    lda #16
    ldy #$00
    jsr append_word_decimal
    jmp append_export_list_newline
append_export_list_layout_size:
    ldx export_index
.if ACTC_REU_LAYOUT_META
    lda layout_size_lo_data
    ldy layout_size_hi_data
.else
    lda proc_sizes_data,x
    ldy proc_sizes_hi,x
.endif
    jsr append_word_decimal
append_export_list_newline:
    jsr append_newline
    inc export_index
    jmp append_export_list_loop
append_export_list_done:
    rts

append_machine_local_call_export_list:
    ldx #$01
    lda #$00
    tay
    sta expr_value_lo
    sty expr_value_hi
    lda #20
    jsr append_machine_export_line
    ldx #$00
    lda #19
    ldy #$00
    sta expr_value_lo
    sty expr_value_hi
    lda #$01
    jsr append_machine_export_line
    rts

append_machine_fanout_export_list:
    ldx #$02
    lda #$00
    tay
    sta expr_value_lo
    sty expr_value_hi
    lda #27
    jsr append_machine_export_line
    ldx #$01
    lda #22
    ldy #$00
    sta expr_value_lo
    sty expr_value_hi
    lda #$04
    jsr append_machine_export_line
    ldx #$00
    lda #26
    ldy #$00
    sta expr_value_lo
    sty expr_value_hi
    lda #$01
    jsr append_machine_export_line
    rts

append_machine_export_line:
    sta hex_work
    stx proc_index
    lda #'x'
    jsr append_char
    lda #' '
    jsr append_char
    ldx proc_index
    jsr set_export_ptr_from_x
    ldy #$00
append_machine_export_line_name_loop:
    lda (export_ptr),y
    beq append_machine_export_line_name_done
    jsr lowercase_ascii
    jsr append_char
    iny
    bne append_machine_export_line_name_loop
append_machine_export_line_name_done:
    lda #' '
    jsr append_char
    lda expr_value_lo
    ldy expr_value_hi
    jsr append_word_decimal
    lda #' '
    jsr append_char
    lda hex_work
    ldy #$00
    jsr append_word_decimal
    jmp append_newline

append_body_ops_list:
    jsr is_main_fanout_machine_object_resident
    bcc append_body_ops_list_not_fanout
    jsr append_machine_body_marker_line
    jsr append_machine_body_marker_line
    jsr append_machine_body_marker_line
    rts
append_body_ops_list_not_fanout:
    jsr is_main_single_local_call_machine_object_resident
    bcc append_body_ops_list_standard
    jsr append_machine_body_marker_line
    jsr append_machine_body_marker_line
    rts
append_body_ops_list_standard:
    lda #$00
    sta proc_index
append_body_ops_list_proc_loop:
    ldx proc_index
    cpx export_count_data
    beq append_body_ops_list_done
    lda #'b'
    jsr append_char
    lda #' '
    jsr append_char
    lda proc_index
    bne append_body_ops_list_portable
    jsr is_empty_main_machine_object_resident
    bcc append_body_ops_list_portable
    lda #'M'
    jsr append_char
    jsr append_newline
    inc proc_index
    jmp append_body_ops_list_proc_loop
append_body_ops_list_portable:
    ldx proc_index
    jsr set_body_ptr_from_x
    ldy #$00
append_body_ops_list_body_loop:
    lda (body_ptr),y
    beq append_body_ops_list_ret
    jsr append_char
    iny
    bne append_body_ops_list_body_loop
append_body_ops_list_ret:
    cpy #$00
    beq append_body_ops_list_emit_ret
    dey
    lda (body_ptr),y
    cmp #'r'
    beq append_body_ops_list_newline
    iny
append_body_ops_list_emit_ret:
    lda #'r'
    jsr append_char
append_body_ops_list_newline:
    jsr append_newline
    inc proc_index
    jmp append_body_ops_list_proc_loop
append_body_ops_list_done:
    rts

append_machine_code_list:
    jsr is_empty_main_machine_object_resident
    bcc append_machine_code_list_check_local_call
    lda #<empty_main_machine_record
    sta const_ptr
    lda #>empty_main_machine_record
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_newline
    jmp append_machine_code_list_done
append_machine_code_list_check_local_call:
    jsr is_main_single_local_call_machine_object_resident
    bcc append_machine_code_list_check_fanout
    lda #<single_local_call_machine_record
    sta const_ptr
    lda #>single_local_call_machine_record
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_newline
    jmp append_machine_code_list_done
append_machine_code_list_check_fanout:
    jsr is_main_fanout_machine_object_resident
    bcc append_machine_code_list_done
    lda #<fanout_machine_record
    sta const_ptr
    lda #>fanout_machine_record
    sta const_ptr+1
    jsr append_const_ptr
    jsr append_newline
append_machine_code_list_done:
    rts

is_empty_main_machine_object_resident:
    lda export_count_data
    cmp #$01
    bne is_empty_main_machine_object_resident_no
    lda extern_count_data
    bne is_empty_main_machine_object_resident_no
    lda string_count_data
    bne is_empty_main_machine_object_resident_no
    lda int_count_data
    bne is_empty_main_machine_object_resident_no
    lda var_count_data
    bne is_empty_main_machine_object_resident_no
    lda module_var_count_data
    bne is_empty_main_machine_object_resident_no
    jsr module_name_is_main_symbol
    bcc is_empty_main_machine_object_resident_no
    ldx #$00
    jsr set_export_ptr_from_x
    jsr export_ptr_is_main_symbol
    bcc is_empty_main_machine_object_resident_no
    ldx #$00
    jsr set_body_ptr_from_x
    ldy #$00
    lda (body_ptr),y
    beq is_empty_main_machine_object_resident_yes
    cmp #'r'
    bne is_empty_main_machine_object_resident_no
    iny
    lda (body_ptr),y
    bne is_empty_main_machine_object_resident_no
is_empty_main_machine_object_resident_yes:
    sec
    rts
is_empty_main_machine_object_resident_no:
    clc
    rts

module_name_is_main_symbol:
    ldy #$00
    lda module_name,y
    jsr lowercase_ascii
    cmp #'m'
    bne main_symbol_no
    iny
    lda module_name,y
    jsr lowercase_ascii
    cmp #'a'
    bne main_symbol_no
    iny
    lda module_name,y
    jsr lowercase_ascii
    cmp #'i'
    bne main_symbol_no
    iny
    lda module_name,y
    jsr lowercase_ascii
    cmp #'n'
    bne main_symbol_no
    iny
    lda module_name,y
    bne main_symbol_no
    sec
    rts

export_ptr_is_main_symbol:
    ldy #$00
    lda (export_ptr),y
    jsr lowercase_ascii
    cmp #'m'
    bne main_symbol_no
    iny
    lda (export_ptr),y
    jsr lowercase_ascii
    cmp #'a'
    bne main_symbol_no
    iny
    lda (export_ptr),y
    jsr lowercase_ascii
    cmp #'i'
    bne main_symbol_no
    iny
    lda (export_ptr),y
    jsr lowercase_ascii
    cmp #'n'
    bne main_symbol_no
    iny
    lda (export_ptr),y
    bne main_symbol_no
    sec
    rts

main_symbol_no:
    clc
    rts

is_main_single_local_call_machine_object_resident:
    lda export_count_data
    cmp #$02
    bne is_main_single_local_call_machine_object_resident_no
    lda extern_count_data
    bne is_main_single_local_call_machine_object_resident_no
    lda string_count_data
    bne is_main_single_local_call_machine_object_resident_no
    lda int_count_data
    bne is_main_single_local_call_machine_object_resident_no
    lda var_count_data
    bne is_main_single_local_call_machine_object_resident_no
    lda module_var_count_data
    bne is_main_single_local_call_machine_object_resident_no
    jsr module_name_is_main_symbol
    bcc is_main_single_local_call_machine_object_resident_no
    ldx #$01
    jsr set_export_ptr_from_x
    jsr export_ptr_is_main_symbol
    bcc is_main_single_local_call_machine_object_resident_no
    ldx #$00
    jsr set_body_ptr_from_x
    jsr body_ptr_is_return_body
    bcc is_main_single_local_call_machine_object_resident_no
    ldx #$01
    jsr set_body_ptr_from_x
    jsr body_ptr_is_call_zero_return_body
    bcc is_main_single_local_call_machine_object_resident_no
    sec
    rts
is_main_single_local_call_machine_object_resident_no:
    clc
    rts

body_ptr_is_return_body:
    ldy #$00
    lda (body_ptr),y
    beq body_ptr_is_return_body_yes
    cmp #'r'
    bne body_ptr_is_return_body_no
    iny
    lda (body_ptr),y
    bne body_ptr_is_return_body_no
body_ptr_is_return_body_yes:
    sec
    rts
body_ptr_is_return_body_no:
    clc
    rts

body_ptr_is_call_zero_return_body:
    ldy #$00
    lda (body_ptr),y
    cmp #'c'
    bne body_ptr_is_call_zero_return_body_no
    iny
    lda (body_ptr),y
    cmp #'0'
    bne body_ptr_is_call_zero_return_body_no
    iny
    lda (body_ptr),y
    cmp #'r'
    bne body_ptr_is_call_zero_return_body_no
    iny
    lda (body_ptr),y
    bne body_ptr_is_call_zero_return_body_no
    sec
    rts
body_ptr_is_call_zero_return_body_no:
    clc
    rts

is_main_fanout_machine_object_resident:
    lda export_count_data
    cmp #$03
    bne is_main_fanout_machine_object_resident_no
    lda extern_count_data
    bne is_main_fanout_machine_object_resident_no
    lda string_count_data
    bne is_main_fanout_machine_object_resident_no
    lda int_count_data
    bne is_main_fanout_machine_object_resident_no
    lda var_count_data
    bne is_main_fanout_machine_object_resident_no
    lda module_var_count_data
    bne is_main_fanout_machine_object_resident_no
    jsr module_name_is_main_symbol
    bcc is_main_fanout_machine_object_resident_no
    ldx #$02
    jsr set_export_ptr_from_x
    jsr export_ptr_is_main_symbol
    bcc is_main_fanout_machine_object_resident_no
    ldx #$00
    jsr set_body_ptr_from_x
    jsr body_ptr_is_return_body
    bcc is_main_fanout_machine_object_resident_no
    ldx #$01
    jsr set_body_ptr_from_x
    jsr body_ptr_is_call_zero_return_body
    bcc is_main_fanout_machine_object_resident_no
    ldx #$02
    jsr set_body_ptr_from_x
    jsr body_ptr_is_call_zero_call_one_return_body
    bcc is_main_fanout_machine_object_resident_no
    sec
    rts
is_main_fanout_machine_object_resident_no:
    clc
    rts

body_ptr_is_call_zero_call_one_return_body:
    ldy #$00
    lda (body_ptr),y
    cmp #'c'
    bne body_ptr_is_call_zero_call_one_return_body_no
    iny
    lda (body_ptr),y
    cmp #'0'
    bne body_ptr_is_call_zero_call_one_return_body_no
    iny
    lda (body_ptr),y
    cmp #'c'
    bne body_ptr_is_call_zero_call_one_return_body_no
    iny
    lda (body_ptr),y
    cmp #'1'
    bne body_ptr_is_call_zero_call_one_return_body_no
    iny
    lda (body_ptr),y
    cmp #'r'
    bne body_ptr_is_call_zero_call_one_return_body_no
    iny
    lda (body_ptr),y
    bne body_ptr_is_call_zero_call_one_return_body_no
    sec
    rts
body_ptr_is_call_zero_call_one_return_body_no:
    clc
    rts

append_machine_body_marker_line:
    lda #'b'
    jsr append_char
    lda #' '
    jsr append_char
    lda #'M'
    jsr append_char
    jmp append_newline

append_external_list:
    lda #$00
    sta proc_index
append_external_list_loop:
    ldx proc_index
    cpx extern_count_data
    beq append_external_list_done
    lda #'u'
    jsr append_char
    lda #' '
    jsr append_char
    ldx proc_index
    jsr set_external_ptr_from_x
    ldy #$00
append_external_list_value_loop:
    lda (export_ptr),y
    beq append_external_list_value_done
    jsr lowercase_ascii
    jsr append_char
    iny
    bne append_external_list_value_loop
append_external_list_value_done:
    jsr append_newline
    inc proc_index
    jmp append_external_list_loop
append_external_list_done:
    rts

append_string_list:
    lda #$00
    sta proc_index
append_string_list_loop:
    ldx proc_index
    cpx string_count_data
    beq append_string_list_done
    lda #'s'
    jsr append_char
    lda #' '
    jsr append_char
    ldx proc_index
    jsr set_string_ptr_from_x
    ldy #$00
append_string_list_value_loop:
    lda (body_ptr),y
    beq append_string_list_value_done
    jsr append_char
    iny
    bne append_string_list_value_loop
append_string_list_value_done:
    jsr append_newline
    inc proc_index
    jmp append_string_list_loop
append_string_list_done:
    rts

append_int_list:
    lda #$00
    sta proc_index
append_int_list_loop:
    ldx proc_index
    cpx int_count_data
    beq append_int_list_done
    lda #'i'
    jsr append_char
    lda #' '
    jsr append_char
    ldx proc_index
.if ACTC_REU_INT_LITERALS
    jsr load_int_literal_from_reu_x
    lda int_literal_lo_data
    ldy int_literal_hi_data
.else
    lda int_values_lo,x
    ldy int_values_hi,x
.endif
    jsr append_word_decimal
    jsr append_newline
    inc proc_index
    jmp append_int_list_loop
append_int_list_done:
    rts

append_var_list:
    lda #$00
    sta proc_index
append_var_list_loop:
    ldx proc_index
    cpx var_count_data
    beq append_var_list_done
    lda #'v'
    jsr append_char
    lda #' '
    jsr append_char
    ldx proc_index
    jsr set_var_ptr_from_x
    ldy #$00
append_var_list_name_loop:
    lda (export_ptr),y
    beq append_var_list_name_done
    jsr lowercase_ascii
    jsr append_char
    iny
    bne append_var_list_name_loop
append_var_list_name_done:
    lda #' '
    jsr append_char
    ldx proc_index
.if ACTC_REU_VAR_META
    jsr load_var_meta_from_reu_x
    lda var_meta_init_hi_data
    bne append_var_list_bad
    lda var_meta_init_lo_data
.else
    lda var_init_hi,x
    bne append_var_list_bad
    lda var_init_lo,x
.endif
    jsr append_small_decimal
    ldx proc_index
.if ACTC_REU_VAR_META
    lda var_meta_width_data
.else
    lda var_width_data,x
.endif
    cmp #$02
    beq append_var_list_newline
    lda #' '
    jsr append_char
    ldx proc_index
.if ACTC_REU_VAR_META
    lda var_meta_width_data
.else
    lda var_width_data,x
.endif
    jsr append_small_decimal
append_var_list_newline:
    jsr append_newline
    inc proc_index
    jmp append_var_list_loop
append_var_list_bad:
    lda #<msg_bad_var
    ldy #>msg_bad_var
    jmp fail_with_ptr
append_var_list_done:
    rts

append_module_symbol_lower:
    ldy #$00
append_module_symbol_lower_loop:
    lda module_name,y
    beq append_module_symbol_lower_done
    jsr lowercase_ascii
    jsr append_char
    iny
    bne append_module_symbol_lower_loop
append_module_symbol_lower_done:
    rts

append_newline:
    lda #10
    jmp append_char

append_small_decimal:
    ldx #$00
append_small_decimal_hundreds_loop:
    cmp #100
    bcc append_small_decimal_tens_prep
    sec
    sbc #100
    inx
    bne append_small_decimal_hundreds_loop
append_small_decimal_tens_prep:
    stx compare_char
    ldx #$00
append_small_decimal_tens_loop:
    cmp #10
    bcc append_small_decimal_tens_done
    sec
    sbc #10
    inx
    bne append_small_decimal_tens_loop
append_small_decimal_tens_done:
    pha
    txa
    pha
    lda compare_char
    beq append_small_decimal_emit_tens
    clc
    adc #'0'
    jsr append_char
append_small_decimal_emit_tens:
    pla
    bne :+
    lda compare_char
    beq append_small_decimal_ones_pop
    lda #$00
:
    clc
    adc #'0'
    jsr append_char
append_small_decimal_ones_pop:
    pla
    clc
    adc #'0'
    jmp append_char

append_word_decimal:
    sta expr_value_lo
    sty compare_char
    lda #$00
    sta expr_digit_count
    ldx #$00
append_word_decimal_10000_loop:
    lda compare_char
    cmp #$27
    bcc append_word_decimal_10000_done
    bne append_word_decimal_10000_sub
    lda expr_value_lo
    cmp #$10
    bcc append_word_decimal_10000_done
append_word_decimal_10000_sub:
    lda expr_value_lo
    sec
    sbc #$10
    sta expr_value_lo
    lda compare_char
    sbc #$27
    sta compare_char
    inx
    bne append_word_decimal_10000_loop
append_word_decimal_10000_done:
    txa
    jsr append_word_decimal_emit_digit_if_needed
    ldx #$00
append_word_decimal_1000_loop:
    lda compare_char
    cmp #$03
    bcc append_word_decimal_1000_done
    bne append_word_decimal_1000_sub
    lda expr_value_lo
    cmp #$E8
    bcc append_word_decimal_1000_done
append_word_decimal_1000_sub:
    lda expr_value_lo
    sec
    sbc #$E8
    sta expr_value_lo
    lda compare_char
    sbc #$03
    sta compare_char
    inx
    bne append_word_decimal_1000_loop
append_word_decimal_1000_done:
    txa
    jsr append_word_decimal_emit_digit_if_needed
    ldx #$00
append_word_decimal_100_loop:
    lda compare_char
    bne append_word_decimal_100_sub
    lda expr_value_lo
    cmp #100
    bcc append_word_decimal_100_done
append_word_decimal_100_sub:
    lda expr_value_lo
    sec
    sbc #100
    sta expr_value_lo
    lda compare_char
    sbc #$00
    sta compare_char
    inx
    bne append_word_decimal_100_loop
append_word_decimal_100_done:
    txa
    jsr append_word_decimal_emit_digit_if_needed
    ldx #$00
append_word_decimal_10_loop:
    lda compare_char
    bne append_word_decimal_10_sub
    lda expr_value_lo
    cmp #10
    bcc append_word_decimal_10_done
append_word_decimal_10_sub:
    lda expr_value_lo
    sec
    sbc #10
    sta expr_value_lo
    lda compare_char
    sbc #$00
    sta compare_char
    inx
    bne append_word_decimal_10_loop
append_word_decimal_10_done:
    txa
    jsr append_word_decimal_emit_digit_if_needed
    lda expr_value_lo
    clc
    adc #'0'
    jmp append_char

append_word_decimal_emit_digit_if_needed:
    pha
    txa
    bne append_word_decimal_emit_digit
    lda expr_digit_count
    beq append_word_decimal_skip_digit
append_word_decimal_emit_digit:
    pla
    clc
    adc #'0'
    jsr append_char
    lda #$01
    sta expr_digit_count
    rts
append_word_decimal_skip_digit:
    pla
    rts
.endif

.if ACTC_KEEP_LAYOUT_RESIDENT_FALLBACK
add_a_to_proc_size_x:
.if ACTC_REU_LAYOUT_META
    clc
    adc layout_size_lo_data
    sta layout_size_lo_data
    bcc add_a_to_proc_size_x_done
    inc layout_size_hi_data
.else
    clc
    adc proc_sizes_data,x
    sta proc_sizes_data,x
    bcc add_a_to_proc_size_x_done
    inc proc_sizes_hi,x
.endif
add_a_to_proc_size_x_done:
    rts
.endif

.if ACTC_KEEP_EMIT_RESIDENT_FALLBACK
append_const_ptr:
    ldy #$00
append_const_ptr_loop:
    lda (const_ptr),y
    beq append_const_ptr_done
    jsr append_char
    iny
    bne append_const_ptr_loop
append_const_ptr_done:
    rts

append_hex_byte:
    sta hex_work
    lsr a
    lsr a
    lsr a
    lsr a
    jsr append_hex_nibble
    lda hex_work
    and #$0F
    jmp append_hex_nibble

append_hex_nibble:
    cmp #$0A
    bcc append_hex_nibble_digit
    clc
    adc #('a'-10)
    jmp append_char
append_hex_nibble_digit:
    clc
    adc #'0'
    jmp append_char
.endif

append_char:
.if STREAM_OUTPUT
    tax
    tya
    pha
    txa
    jsr append_stream_byte_y_saved
    pla
    tay
    rts
.else
    tax
    tya
    pha
    ldy #$00
    txa
    sta (content_ptr),y
    pla
    tay
    inc content_ptr
    bne :+
    inc content_ptr+1
:   rts
.endif

.if STREAM_OUTPUT
append_stream_byte_y_saved:
    ldy output_chunk_len
    sta output_chunk_buffer,y
    inc output_chunk_len
    lda output_chunk_len
    cmp #OUTPUT_CHUNK_SIZE
    bcc append_stream_byte_y_saved_done
    jsr flush_output_stream_or_fail
append_stream_byte_y_saved_done:
    rts

flush_output_stream_or_fail:
    lda output_chunk_len
    beq flush_output_stream_done
    lda #<output_chunk_buffer
    sta file_params+0
    lda #>output_chunk_buffer
    sta file_params+1
    lda output_chunk_len
    sta file_params+2
    lda #$00
    sta file_params+3
    lda #tool_file_status_fail
    sta file_params+4
    lda #$23
    jsr set_actc_trace
    lda output_chunk_len
    sta $03E8
    ldx #file_params
    jsr svc_file_write_chunk_sc0
    lda #$24
    jsr set_actc_trace
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
    jsr svc_file_write_begin_sc0
    lda file_params+2
    cmp #tool_file_status_ok
    beq open_output_stream_to_target_ok
    lda #<msg_save_fail
    ldy #>msg_save_fail
    jmp fail_with_ptr
open_output_stream_to_target_ok:
    clc
    rts

close_output_stream:
    lda #tool_file_status_fail
    sta file_params+0
    lda #$25
    jsr set_actc_trace
    ldx #file_params
    jsr svc_file_write_close_sc0
    lda #$26
    jsr set_actc_trace
    lda file_params+0
    cmp #tool_file_status_ok
    beq close_output_stream_ok
    sec
    rts
close_output_stream_ok:
    clc
    rts
.endif

; action_project_save_write.inc also exposes a stub-save helper that expects this
; entry point. ACTC owns object emission directly, so this is intentionally empty.
build_module_stub_content:
    rts

.include "../common/action_project_module_arg.inc"
.include "../common/action_project_load.inc"
.include "../common/action_project_load_guard.inc"
.include "../common/action_project_entry.inc"
.include "../common/action_project_entry_guard.inc"
.include "../common/action_project_object_path.inc"
.include "../common/action_project_path.inc"
.include "../common/action_project_save_mode.inc"
.include "../common/action_project_save_write.inc"
.include "../common/action_project_source.inc"

print_line_ptr:
    jsr print_ptr
    jmp svc_console_newline

fail_with_ptr:
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
    ldx #svc_retptr
    jmp svc_console_write_sc0

msg_bad_name:
    .asciiz "BAD NAME"
msg_no_project:
    .asciiz "NO PROJECT"
msg_not_in_project:
    .asciiz "NOT IN PROJECT"
msg_no_file:
    .asciiz "NO FILE"
msg_probe_fail:
    .asciiz "PROBE FAIL"
msg_load_fail:
    .asciiz "LOAD FAIL"
msg_bad_module:
    .asciiz "BAD MODULE"
msg_header_overlay:
    .asciiz "HDR OVL FAIL"
msg_layout_overlay:
    .asciiz "LAY OVL FAIL"
msg_emit_overlay:
    .asciiz "EMIT OVL FAIL"
msg_body_overlay:
    .asciiz "BODY OVL FAIL"
msg_bad_proc:
    .asciiz "BAD PROC"
msg_bad_var:
    .asciiz "BAD VAR"
msg_bad_call:
    .asciiz "BAD CALL"
msg_bad_literal:
    .asciiz "BAD LITERAL"
msg_decl_overlay:
    .asciiz "DECL OVL FAIL"
msg_save_fail:
    .asciiz "SAVE FAIL"
msg_created:
    .asciiz "CREATED"
msg_updated:
    .asciiz "UPDATED"
msg_no_proc:
    .asciiz "NO PROC"
msg_ok:
    .asciiz "ACTC OK"

default_module_name:
    .asciiz "MAIN"
project_marker:
    .asciiz "ACTION.PROJ"
module_name:
    .res 25

pattern_module:
    .asciiz "MODULE"
pattern_int_decl:
    .asciiz "INT"
pattern_byte_decl:
    .asciiz "BYTE"
pattern_card_decl:
    .asciiz "CARD"
pattern_real_decl:
    .asciiz "REAL"
pattern_proc:
    .asciiz "PROC"
pattern_if:
    .asciiz "IF"
pattern_while:
    .asciiz "WHILE"
pattern_do:
    .asciiz "DO"
pattern_od:
    .asciiz "OD"
pattern_until:
    .asciiz "UNTIL"
pattern_and:
    .asciiz "AND"
pattern_or:
    .asciiz "OR"
pattern_not:
    .asciiz "NOT"
pattern_else:
    .asciiz "ELSE"
pattern_fi:
    .asciiz "FI"
pattern_endif:
    .asciiz "ENDIF"
pattern_return:
    .asciiz "RETURN"
pattern_print_quote:
    .byte "PRINT(",34,0
pattern_printe_quote:
    .byte "PRINTE(",34,0
pattern_print:
    .asciiz "PRINT("
pattern_printe:
    .asciiz "PRINTE("
pattern_printr:
    .asciiz "PRINTR("
pattern_printre:
    .asciiz "PRINTRE("
pattern_printi:
    .asciiz "PRINTI("
pattern_printie:
    .asciiz "PRINTIE("

import_rt_format_int:
    .asciiz "rt.format_int"
import_rt_print_line:
    .asciiz "rt.print_line"
import_rt_print_str:
    .asciiz "rt.print_str"
runtime_symbol_rt_f_add:
    .asciiz "RT_F_ADD"
runtime_symbol_rt_f_sub:
    .asciiz "RT_F_SUB"
runtime_symbol_rt_f_mul:
    .asciiz "RT_F_MUL"
runtime_symbol_rt_f_div:
    .asciiz "RT_F_DIV"
runtime_symbol_rt_f_cmp:
    .asciiz "RT_F_CMP"
runtime_symbol_rt_i_to_f:
    .asciiz "RT_I_TO_F"
runtime_symbol_rt_f_to_i:
    .asciiz "RT_F_TO_I"
runtime_symbol_rt_s_to_f:
    .asciiz "RT_S_TO_F"
runtime_symbol_rt_print_f:
    .asciiz "RT_PRINT_F"
runtime_symbol_rt_sid_freq:
    .asciiz "RT_SID_FREQ"
runtime_symbol_rt_sid_wave:
    .asciiz "RT_SID_WAVE"
runtime_symbol_rt_sid_ad:
    .asciiz "RT_SID_AD"
runtime_symbol_rt_sid_sr:
    .asciiz "RT_SID_SR"
runtime_symbol_rt_sid_vol:
    .asciiz "RT_SID_VOL"
runtime_symbol_rt_sprite_on:
    .asciiz "RT_SPRITE_ON"
runtime_symbol_rt_sprite_off:
    .asciiz "RT_SPRITE_OFF"
runtime_symbol_rt_sprite_color:
    .asciiz "RT_SPRITE_COLOR"
runtime_symbol_rt_sprite_pos:
    .asciiz "RT_SPRITE_POS"
runtime_symbol_rt_sprite_mc:
    .asciiz "RT_SPRITE_MC"
runtime_symbol_rt_sprite_xexp:
    .asciiz "RT_SPRITE_XEXP"
runtime_symbol_rt_sprite_yexp:
    .asciiz "RT_SPRITE_YEXP"
runtime_symbol_rt_sprite_prio:
    .asciiz "RT_SPRITE_PRIO"
runtime_symbol_rt_sprite_data:
    .asciiz "RT_SPRITE_DATA"
runtime_symbol_rt_sprite_set_mc:
    .asciiz "RT_SPRITE_SET_MC"
builtin_symbol_sprite_on:
    .asciiz "SPRITEON"
builtin_symbol_sprite_off:
    .asciiz "SPRITEOFF"
builtin_symbol_sprite_color:
    .asciiz "SPRITECOLOR"
builtin_symbol_sprite_pos:
    .asciiz "SPRITEPOS"
builtin_symbol_sprite_mc:
    .asciiz "SPRITEMC"
builtin_symbol_sprite_xexp:
    .asciiz "SPRITEXEXP"
builtin_symbol_sprite_yexp:
    .asciiz "SPRITEYEXP"
builtin_symbol_sprite_prio:
    .asciiz "SPRITEPRIO"
builtin_symbol_sprite_data:
    .asciiz "SPRITEDATA"
builtin_symbol_set_sprite_mc:
    .asciiz "SETSPRITEMC"
builtin_symbol_sid_freq:
    .asciiz "SIDFREQ"
builtin_symbol_sid_wave:
    .asciiz "SIDWAVE"
builtin_symbol_sid_ad:
    .asciiz "SIDAD"
builtin_symbol_sid_sr:
    .asciiz "SIDSR"
builtin_symbol_sid_vol:
    .asciiz "SIDVOL"

object_header:
    .byte "OBJ1",10,0
empty_main_machine_record:
    .asciiz "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF"
single_local_call_machine_record:
    .asciiz "m 20 13 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60"
fanout_machine_record:
    .asciiz "m 20 1A 10 20 16 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 1A 10 60 60"
actc_overlay_pass_table:
    .byte ACTC_OVERLAY_PASS_NOOP
    .byte ACTC_OVERLAY_REU_BASE_LO, ACTC_OVERLAY_REU_BASE_HI, ACTC_OVERLAY_REU_BASE_BANK
    .word actc_overlay_noop_path
    .byte ACTC_OVERLAY_PASS_SOURCE_HEADER
    .byte ACTC_OVERLAY_REU_BASE_LO, ACTC_OVERLAY_REU_BASE_HI, ACTC_OVERLAY_REU_BASE_BANK
    .word actc_overlay_source_header_path
    .byte ACTC_OVERLAY_PASS_DECL_COUNTS
    .byte ACTC_OVERLAY_REU_BASE_LO, ACTC_OVERLAY_REU_BASE_HI, ACTC_OVERLAY_REU_BASE_BANK
    .word actc_overlay_decl_counts_path
    .byte ACTC_OVERLAY_PASS_PAYLOAD_LAYOUT
    .byte ACTC_OVERLAY_REU_BASE_LO, ACTC_OVERLAY_REU_BASE_HI, ACTC_OVERLAY_REU_BASE_BANK
    .word actc_overlay_payload_layout_path
    .byte ACTC_OVERLAY_PASS_RUNTIME_IMPORTS
    .byte ACTC_OVERLAY_REU_BASE_LO, ACTC_OVERLAY_REU_BASE_HI, ACTC_OVERLAY_REU_BASE_BANK
    .word actc_overlay_runtime_imports_path
    .byte ACTC_OVERLAY_PASS_EMIT_OBJECT
    .byte ACTC_OVERLAY_REU_BASE_LO, ACTC_OVERLAY_REU_BASE_HI, ACTC_OVERLAY_REU_BASE_BANK
    .word actc_overlay_emit_object_path
    .byte ACTC_OVERLAY_PASS_BODY_COLLECT
    .byte ACTC_OVERLAY_REU_BASE_LO, ACTC_OVERLAY_REU_BASE_HI, ACTC_OVERLAY_REU_BASE_BANK
    .word actc_overlay_body_collect_path
    .byte ACTC_OVERLAY_PASS_END
actc_overlay_noop_path:
    .asciiz "!ACTC_OVL0.BIN"
actc_overlay_source_header_path:
    .asciiz "!ACTC_OVL1.BIN"
actc_overlay_decl_counts_path:
    .asciiz "!ACTC_OVL2.BIN"
actc_overlay_payload_layout_path:
    .asciiz "!ACTC_OVL3.BIN"
actc_overlay_runtime_imports_path:
    .asciiz "!ACTC_OVL4.BIN"
actc_overlay_emit_object_path:
    .asciiz "!ACTC_OVL5.BIN"
actc_overlay_body_collect_path:
    .asciiz "!ACTC_OVL6.BIN"

source_buffer:
.if ACTC_REU_SOURCE_CACHE
    .res SOURCE_READ_LIMIT+1
.else
    .res SOURCE_LIMIT+1
.endif
; Reuse the source window storage for path assembly. The source path is only
; needed before the source reader loads the first window, and the object path is
; only needed after parsing is complete.
target_path = source_buffer
.if !ACTC_REU_BODY_OPS
body_ops_data:
    .res BODY_OPS_STRIDE * EXPORT_MAX
.endif
.if !ACTC_REU_STRING_LITERALS
string_literals:
    .res 24 * STRING_LITERAL_MAX
.endif
.if !ACTC_REU_INT_LITERALS
int_values_lo:
    .res INT_LITERAL_MAX
int_values_hi:
    .res INT_LITERAL_MAX
.endif
.if !ACTC_REU_VAR_META
var_init_lo:
    .res VAR_MAX
var_init_hi:
    .res VAR_MAX
var_width_data:
    .res VAR_MAX
var_type_data:
    .res VAR_MAX
.endif
decl_width_data:
    .res 1
decl_type_data:
    .res 1
.if !ACTC_REU_LAYOUT_META
export_offsets:
    .res EXPORT_MAX
export_offsets_hi:
    .res EXPORT_MAX
proc_sizes_data:
    .res EXPORT_MAX
proc_sizes_hi:
    .res EXPORT_MAX
.endif
.if !ACTC_REU_STRING_OFFSETS
string_offsets:
    .res STRING_LITERAL_MAX
.endif

.segment "BSS"

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

declared_module_name:
    .res 25
.if ACTC_REU_EXPORT_NAMES
saved_var_name_data = export_name_window
.else
.if ACTC_REU_TABLES
saved_var_name_data = external_name_buffer
.else
saved_var_name_data:
    .res 25
.endif
.endif
manifest_entry:
    .res 32
.if !STREAM_OUTPUT
content_buffer:
    .res CONTENT_BUFFER_SIZE
.else
content_buffer = source_buffer
.endif
.if STREAM_OUTPUT
; The source window is dead once object emission begins, so stream-output can
; reuse it instead of reserving a separate staging buffer.
output_chunk_buffer = source_buffer
output_chunk_len:
    .res 1
.endif
; The project manifest is loaded and validated before the source path is built,
; so the same storage can hold both the manifest text and the later source
; window/path data.
manifest_buffer = source_buffer
export_count_data:
    .res 1
string_count_data:
    .res 1
int_count_data:
    .res 1
var_count_data:
    .res 1
module_var_count_data:
    .res 1
current_proc_index_data:
    .res 1
extern_count_data:
    .res 1
.if !ACTC_REU_PROC_META
proc_param_count_data:
    .res EXPORT_MAX
proc_param_var_base_data:
    .res EXPORT_MAX
proc_local_count_data:
    .res EXPORT_MAX
proc_local_var_base_data:
    .res EXPORT_MAX
.endif
.if ACTC_KEEP_BODY_RESIDENT_FALLBACK
loop_depth_data:
    .res 1
loop_kind_stack:
    .res LOOP_MAX
.endif
payload_offset_hi:
    .res 1
expr_saved_lo:
    .res 1
expr_saved_hi:
    .res 1
expr_group_saved_saved_lo:
    .res 1
expr_group_saved_saved_hi:
    .res 1
expr_compare_lo:
    .res 1
expr_compare_hi:
    .res 1
expr_group_saved_compare_lo:
    .res 1
expr_group_saved_compare_hi:
    .res 1
expr_runtime_op:
    .res 1
expr_runtime_post_zero:
    .res 1
expr_saved_y_data:
    .res 1
expr_term_lo:
    .res 1
expr_term_hi:
    .res 1
expr_print_op:
    .res 1
expr_runtime_saved_int_count:
    .res 1
expr_runtime_saved_extern_count:
    .res 1
expr_runtime_saved_body_end:
    .res 1
expr_value_lo:
    .res 1
expr_value_hi:
    .res 1
expr_digit_count:
    .res 1
compare_char:
    .res 1
actc_trace_byte:
    .res 1
save_stack_top:
    .res 1
call_target_kind:
    .res 1
call_target_index_data:
    .res 1
call_expected_arg_count:
    .res 1
call_arg_count_data:
    .res 1
param_bind_count_data:
    .res 1
param_bind_base_data:
    .res 1
symbol_start_y_data:
    .res 1
symbol_end_y_data:
    .res 1
assignment_target_index_data:
    .res 1
real_lhs_index_data:
    .res 1
real_rhs_index_data:
    .res 1
real_operator_data:
    .res 1
bool_ops_used_data:
    .res 1
keyword_scan_ptr_lo_data:
    .res 1
keyword_scan_ptr_hi_data:
    .res 1
.if ACTC_REU_SOURCE_CACHE
keyword_window_start_data:
    .res 3
.endif
group_scan_ptr_lo_data:
    .res 1
group_scan_ptr_hi_data:
    .res 1
.if ACTC_REU_SOURCE_CACHE
group_window_start_data:
    .res 3
.endif
condition_scan_ptr_lo_data:
    .res 1
condition_scan_ptr_hi_data:
    .res 1
.if ACTC_REU_SOURCE_CACHE
condition_window_start_data:
    .res 3
.endif
hex_work:
    .res 1
.if ACTC_REU_EXPORT_NAMES
export_name_window:
    .res 25
.else
export_names:
    .res 25 * EXPORT_MAX
.endif
.if ACTC_REU_TABLES
.if ACTC_REU_EXPORT_NAMES
external_name_buffer = export_name_window
.else
external_name_buffer:
    .res 25
.endif
.else
external_names:
    .res 25 * EXTERNAL_MAX
.endif
.if ACTC_REU_BODY_OPS
    body_ops_window:
    .res BODY_OPS_STRIDE
body_window_index_data:
    .res 1
body_window_request_data:
    .res 1
body_window_dirty_data:
    .res 1
.endif
.if ACTC_REU_BODY_DEBUG
body_debug_count_data:
    .res EXPORT_MAX
body_debug_current_offset_data:
    .res 3
.endif
.if ACTC_REU_STRING_LITERALS
string_literal_window:
    .res 24
.endif
.if ACTC_REU_VAR_NAMES
var_name_window:
    .res 25
.else
var_names:
    .res 25 * VAR_MAX
.endif
.if ACTC_REU_INT_LITERALS
int_literal_window:
int_literal_lo_data:
    .res 1
int_literal_hi_data:
    .res 1
.endif
.if ACTC_REU_VAR_META
var_meta_window:
var_meta_init_lo_data:
    .res 1
var_meta_init_hi_data:
    .res 1
var_meta_width_data:
    .res 1
var_meta_type_data:
    .res 1
.endif
.if ACTC_REU_PROC_META
proc_meta_window:
proc_meta_param_count_data:
    .res 1
proc_meta_param_base_data:
    .res 1
proc_meta_local_count_data:
    .res 1
proc_meta_local_base_data:
    .res 1
.endif
.if ACTC_REU_PROC_DEBUG
proc_debug_offset_window:
proc_debug_offset_data:
    .res 3
proc_debug_remaining_data:
    .res 3
proc_debug_scan_offset:
    .res 3
proc_debug_chunk_len:
    .res 1
proc_debug_linecol_window:
proc_debug_line_data:
    .res 2
proc_debug_col_data:
    .res 2
proc_debug_prev_cr:
    .res 1
proc_debug_scan_buffer:
    .res PROC_DEBUG_SCAN_CHUNK_SIZE
.endif
.if ACTC_REU_LAYOUT_META
layout_window:
layout_offset_lo_data:
    .res 1
layout_offset_hi_data:
    .res 1
layout_size_lo_data:
    .res 1
layout_size_hi_data:
    .res 1
.endif
.if ACTC_REU_STRING_OFFSETS
string_offset_window:
string_offset_data:
    .res 1
.endif
actc_overlay_loaded_len:
    .res 2
actc_overlay_requested_pass:
    .res 1
actc_overlay_context:
    .res ACTC_OVERLAY_CTX_SIZE
actc_overlay_service_status:
    .res 1
actc_overlay_status:
    .res 1
actc_overlay_saved_memcfg:
    .res 1
actc_overlay_memcfg_before_call:
    .res 1
actc_overlay_memcfg_after_call:
    .res 1
actc_overlay_memcfg_after_restore:
    .res 1
actc_overlay_entry_minus_one:
    .res 1
bss_end:
