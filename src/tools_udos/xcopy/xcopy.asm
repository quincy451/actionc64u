.include "udos_services.inc"
.include "udos_overlay.inc"
.macpack longbranch

.export start
.export udos_overlay_header
.export udos_overlay_end

PATH_LEN = 32
ENTRY_MAX = 6
STACK_DEPTH = 16
MUTATION_LIMIT = 48
ASCII_SPACE = $20
ASCII_SLASH = $2F
ASCII_COLON = $3A

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 3
params:
    .res 5
src_ptr:
    .res 2
dst_ptr:
    .res 2
slot_ptr:
    .res 2
entry_ptr:
    .res 2
slot_index:
    .res 1

.code

udos_overlay_header:
    .byte 'U','D','O','V'
    .byte UDOS_OVERLAY_FORMAT_VERSION
    .byte udos_tool_abi_version
    .byte UDOS_OVERLAY_COMMAND_XCOPY
    .byte $00
    .word UDOS_OVERLAY_LOAD_ADDR
    .word start
    .word udos_overlay_end - udos_overlay_header

start:
    lda #$00
    sta stack_count
    sta mutation_count

    ldx #svc_retptr
    jsr svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    jeq fail_bad_xcopy

    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    lda svc_retptr
    sta src_ptr
    lda svc_retptr+1
    sta src_ptr+1
    jsr parse_two_paths
    jcs fail_bad_xcopy

    lda #<source_root
    sta src_ptr
    lda #>source_root
    sta src_ptr+1
    jsr trim_trailing_slash
    lda #<dest_root
    sta src_ptr
    lda #>dest_root
    sta src_ptr+1
    jsr trim_trailing_slash
    jsr destination_is_source_child
    jcs fail_bad_xcopy

    jsr validate_source_root
    lda #<dest_root
    sta dst_ptr
    lda #>dest_root
    sta dst_ptr+1
    jsr ensure_dest_dir

    lda #<source_root
    sta src_ptr
    lda #>source_root
    sta src_ptr+1
    lda #<dest_root
    sta dst_ptr
    lda #>dest_root
    sta dst_ptr+1
    jsr push_path_pair
    jcs fail_too_large

main_loop:
    lda stack_count
    jeq exit_ok
    jsr pop_path_pair
    jsr snapshot_current_dir
    lda #$00
    sta entry_index

process_entry_loop:
    lda entry_index
    cmp entry_count
    bcs main_loop
    sta slot_index
    jsr set_entry_slot_ptr
    lda slot_ptr
    sta entry_ptr
    lda slot_ptr+1
    sta entry_ptr+1
    jsr classify_entry
    jcs fail_copy

    lda #<current_src
    sta src_ptr
    lda #>current_src
    sta src_ptr+1
    lda #<child_src
    sta dst_ptr
    lda #>child_src
    sta dst_ptr+1
    jsr build_child_path
    jcs fail_path_too_long

    lda #<current_dst
    sta src_ptr
    lda #>current_dst
    sta src_ptr+1
    lda #<child_dst
    sta dst_ptr
    lda #>child_dst
    sta dst_ptr+1
    jsr build_child_path
    jcs fail_path_too_long

    lda child_is_dir
    beq process_file
    lda #<child_dst
    sta dst_ptr
    lda #>child_dst
    sta dst_ptr+1
    jsr ensure_dest_dir
    lda #<child_src
    sta src_ptr
    lda #>child_src
    sta src_ptr+1
    lda #<child_dst
    sta dst_ptr
    lda #>child_dst
    sta dst_ptr+1
    jsr push_path_pair
    jcs fail_too_large
    jmp process_entry_next

process_file:
    jsr reserve_mutation
    jcs fail_too_large
    lda #<child_src
    sta params+0
    lda #>child_src
    sta params+1
    lda #<child_dst
    sta params+2
    lda #>child_dst
    sta params+3
    lda #tool_file_status_fail
    sta params+4
    ldx #params
    jsr svc_file_copy_sc0
    lda params+4
    cmp #tool_file_status_ok
    beq process_file_ok
    cmp #tool_file_status_nofile
    jeq fail_no_such_file
    cmp #tool_file_status_exists
    jeq fail_exists
    cmp #tool_file_status_too_large
    jeq fail_too_large
    jmp fail_copy
process_file_ok:
    inc mutation_count

process_entry_next:
    inc entry_index
    jmp process_entry_loop

validate_source_root:
    lda #<source_root
    sta params+0
    lda #>source_root
    sta params+1
    ldx #params
    jsr svc_dir_begin_sc0
    lda params+2
    cmp #tool_dir_status_ok
    beq validate_source_ok
    cmp #tool_dir_status_flat
    jeq fail_flat_image
    cmp #tool_dir_status_unmounted
    jeq fail_unmounted
    jmp fail_no_such_dir
validate_source_ok:
    rts

; Input: dst_ptr points at a complete destination directory path.
ensure_dest_dir:
    lda dst_ptr
    sta saved_dest_ptr
    lda dst_ptr+1
    sta saved_dest_ptr+1
    jsr reserve_mutation
    jcs fail_too_large
    lda saved_dest_ptr
    sta params+0
    lda saved_dest_ptr+1
    sta params+1
    lda #tool_dir_status_fail
    sta params+2
    ldx #params
    jsr svc_dir_make_sc0
    lda params+2
    cmp #tool_dir_status_ok
    beq ensure_dest_created
    cmp #tool_dir_status_exists
    beq ensure_dest_ok
    jsr begin_dest_dir
    lda params+2
    cmp #tool_dir_status_flat
    jeq fail_flat_image
    cmp #tool_dir_status_unmounted
    jeq fail_unmounted
    jmp fail_copy
ensure_dest_created:
    inc mutation_count
ensure_dest_ok:
    rts

begin_dest_dir:
    lda saved_dest_ptr
    sta params+0
    lda saved_dest_ptr+1
    sta params+1
    ldx #params
    jmp svc_dir_begin_sc0

snapshot_current_dir:
    lda #<current_src
    sta params+0
    lda #>current_src
    sta params+1
    ldx #params
    jsr svc_dir_begin_sc0
    lda params+2
    cmp #tool_dir_status_ok
    beq snapshot_begin_ok
    cmp #tool_dir_status_flat
    jeq fail_flat_image
    cmp #tool_dir_status_unmounted
    jeq fail_unmounted
    jmp fail_no_such_dir
snapshot_begin_ok:
    lda #$00
    sta entry_count
snapshot_loop:
    ldx #svc_retptr
    jsr svc_dir_next
    lda svc_retptr
    ora svc_retptr+1
    beq snapshot_done
    lda entry_count
    cmp #ENTRY_MAX
    jcs fail_too_large
    sta slot_index
    jsr set_entry_slot_ptr
    lda svc_retptr
    sta src_ptr
    lda svc_retptr+1
    sta src_ptr+1
    lda slot_ptr
    sta dst_ptr
    lda slot_ptr+1
    sta dst_ptr+1
    jsr copy_path
    jcs fail_path_too_long
    inc entry_count
    jmp snapshot_loop
snapshot_done:
    rts

classify_entry:
    lda #$00
    sta child_is_dir
    ldy #$00
classify_entry_scan:
    lda (entry_ptr),y
    beq classify_entry_end
    iny
    cpy #PATH_LEN
    bcc classify_entry_scan
    sec
    rts
classify_entry_end:
    cpy #$00
    beq classify_entry_fail
    dey
    lda (entry_ptr),y
    cmp #ASCII_SLASH
    bne classify_entry_ok
    lda #$00
    sta (entry_ptr),y
    lda #$01
    sta child_is_dir
classify_entry_ok:
    clc
    rts
classify_entry_fail:
    sec
    rts

; Input: src_ptr is the parent, dst_ptr is the output, entry_ptr is the child.
build_child_path:
    ldy #$00
build_child_parent_loop:
    lda (src_ptr),y
    beq build_child_parent_done
    cpy #PATH_LEN-1
    bcs build_child_fail
    sta (dst_ptr),y
    iny
    bne build_child_parent_loop
build_child_parent_done:
    cpy #$00
    beq build_child_add_slash
    dey
    lda (dst_ptr),y
    iny
    cmp #ASCII_SLASH
    beq build_child_entry_start
build_child_add_slash:
    cpy #PATH_LEN-1
    bcs build_child_fail
    lda #ASCII_SLASH
    sta (dst_ptr),y
    iny
build_child_entry_start:
    sty path_prefix_len
    tya
    clc
    adc dst_ptr
    sta dst_ptr
    bcc :+
    inc dst_ptr+1
:
    lda #PATH_LEN-1
    sec
    sbc path_prefix_len
    sta path_remaining
    ldy #$00
build_child_entry_loop:
    lda (entry_ptr),y
    beq build_child_done
    ldx path_remaining
    beq build_child_fail
    sta (dst_ptr),y
    dec path_remaining
    iny
    bne build_child_entry_loop
build_child_done:
    lda #$00
    sta (dst_ptr),y
    clc
    rts
build_child_fail:
    sec
    rts

parse_two_paths:
    ldy #$00
parse_source_skip_space:
    lda (src_ptr),y
    beq parse_paths_fail
    cmp #ASCII_SPACE
    bne parse_source_start
    iny
    bne parse_source_skip_space
parse_source_start:
    ldx #$00
parse_source_loop:
    lda (src_ptr),y
    beq parse_paths_fail
    cmp #ASCII_SPACE
    beq parse_source_done
    cpx #PATH_LEN-1
    bcs parse_paths_fail
    sta source_root,x
    inx
    iny
    bne parse_source_loop
parse_source_done:
    lda #$00
    sta source_root,x
    cpx #$00
    beq parse_paths_fail
parse_dest_skip_space:
    lda (src_ptr),y
    beq parse_paths_fail
    cmp #ASCII_SPACE
    bne parse_dest_start
    iny
    bne parse_dest_skip_space
parse_dest_start:
    ldx #$00
parse_dest_loop:
    lda (src_ptr),y
    beq parse_dest_done
    cmp #ASCII_SPACE
    beq parse_dest_done
    cpx #PATH_LEN-1
    bcs parse_paths_fail
    sta dest_root,x
    inx
    iny
    bne parse_dest_loop
parse_dest_done:
    lda #$00
    sta dest_root,x
    cpx #$00
    beq parse_paths_fail
parse_trailing_space:
    lda (src_ptr),y
    beq parse_paths_ok
    cmp #ASCII_SPACE
    bne parse_paths_fail
    iny
    bne parse_trailing_space
parse_paths_ok:
    clc
    rts
parse_paths_fail:
    sec
    rts

trim_trailing_slash:
    ldy #$00
trim_path_scan:
    lda (src_ptr),y
    beq trim_path_end
    iny
    cpy #PATH_LEN
    bcc trim_path_scan
    rts
trim_path_end:
    cpy #$01
    beq trim_path_done
    dey
    lda (src_ptr),y
    cmp #ASCII_SLASH
    bne trim_path_done
    cpy #$02
    bne trim_path_remove
    ldy #$01
    lda (src_ptr),y
    cmp #ASCII_COLON
    beq trim_path_done
    ldy #$02
trim_path_remove:
    lda #$00
    sta (src_ptr),y
trim_path_done:
    rts

destination_is_source_child:
    ldy #$00
dest_source_compare:
    lda source_root,y
    beq dest_source_prefix
    cmp dest_root,y
    bne dest_source_distinct
    iny
    cpy #PATH_LEN
    bcc dest_source_compare
    sec
    rts
dest_source_prefix:
    lda dest_root,y
    beq dest_source_reject
    cmp #ASCII_SLASH
    beq dest_source_reject
    cpy #$00
    beq dest_source_distinct
    dey
    lda source_root,y
    cmp #ASCII_SLASH
    beq dest_source_reject
dest_source_distinct:
    clc
    rts
dest_source_reject:
    sec
    rts

reserve_mutation:
    lda mutation_count
    cmp #MUTATION_LIMIT
    bcs reserve_mutation_fail
    clc
    rts
reserve_mutation_fail:
    sec
    rts

push_path_pair:
    lda stack_count
    cmp #STACK_DEPTH
    bcs push_pair_fail
    sta slot_index
    lda dst_ptr
    sta entry_ptr
    lda dst_ptr+1
    sta entry_ptr+1
    jsr set_source_stack_slot
    lda slot_ptr
    sta dst_ptr
    lda slot_ptr+1
    sta dst_ptr+1
    jsr copy_path
    bcs push_pair_fail
    lda entry_ptr
    sta src_ptr
    lda entry_ptr+1
    sta src_ptr+1
    jsr set_dest_stack_slot
    lda slot_ptr
    sta dst_ptr
    lda slot_ptr+1
    sta dst_ptr+1
    jsr copy_path
    bcs push_pair_fail
    inc stack_count
    clc
    rts
push_pair_fail:
    sec
    rts

pop_path_pair:
    dec stack_count
    lda stack_count
    sta slot_index
    jsr set_source_stack_slot
    lda slot_ptr
    sta src_ptr
    lda slot_ptr+1
    sta src_ptr+1
    lda #<current_src
    sta dst_ptr
    lda #>current_src
    sta dst_ptr+1
    jsr copy_path
    jsr set_dest_stack_slot
    lda slot_ptr
    sta src_ptr
    lda slot_ptr+1
    sta src_ptr+1
    lda #<current_dst
    sta dst_ptr
    lda #>current_dst
    sta dst_ptr+1
    jmp copy_path

set_source_stack_slot:
    lda #<source_stack
    sta slot_ptr
    lda #>source_stack
    sta slot_ptr+1
    jmp advance_path_slot
set_dest_stack_slot:
    lda #<dest_stack
    sta slot_ptr
    lda #>dest_stack
    sta slot_ptr+1
advance_path_slot:
    ldx slot_index
    beq advance_path_done
advance_path_loop:
    clc
    lda slot_ptr
    adc #PATH_LEN
    sta slot_ptr
    lda slot_ptr+1
    adc #$00
    sta slot_ptr+1
    dex
    bne advance_path_loop
advance_path_done:
    rts

set_entry_slot_ptr:
    lda #<entry_list
    sta slot_ptr
    lda #>entry_list
    sta slot_ptr+1
    jmp advance_path_slot

copy_path:
    ldy #$00
copy_path_loop:
    lda (src_ptr),y
    sta (dst_ptr),y
    beq copy_path_done
    iny
    cpy #PATH_LEN
    bcc copy_path_loop
    sec
    rts
copy_path_done:
    clc
    rts

fail_bad_xcopy:
    lda #<msg_bad_xcopy
    ldy #>msg_bad_xcopy
    jmp fail_with_ptr
fail_flat_image:
    lda #<msg_flat_image
    ldy #>msg_flat_image
    jmp fail_with_ptr
fail_unmounted:
    lda #<msg_unmounted
    ldy #>msg_unmounted
    jmp fail_with_ptr
fail_no_such_dir:
    lda #<msg_no_such_dir
    ldy #>msg_no_such_dir
    jmp fail_with_ptr
fail_no_such_file:
    lda #<msg_no_such_file
    ldy #>msg_no_such_file
    jmp fail_with_ptr
fail_exists:
    lda #<msg_exists
    ldy #>msg_exists
    jmp fail_with_ptr
fail_path_too_long:
    lda #<msg_path_too_long
    ldy #>msg_path_too_long
    jmp fail_with_ptr
fail_too_large:
    lda #<msg_too_large
    ldy #>msg_too_large
    jmp fail_with_ptr
fail_copy:
    lda #<msg_copy_fail
    ldy #>msg_copy_fail

fail_with_ptr:
    jsr print_ptr
    jsr svc_console_newline
    lda #$01
    sta svc_retptr
    lda #$00
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

exit_ok:
    lda #<msg_xcopy_ok
    ldy #>msg_xcopy_ok
    jsr print_ptr
    jsr svc_console_newline
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

print_ptr:
    sta svc_retptr
    sty svc_retptr+1
    ldx #svc_retptr
    jmp svc_console_write_sc0

msg_bad_xcopy:
    .asciiz "BAD XCOPY"
msg_flat_image:
    .asciiz "FLAT IMAGE"
msg_unmounted:
    .asciiz "UNMOUNTED"
msg_no_such_dir:
    .asciiz "NO SUCH DIR"
msg_no_such_file:
    .asciiz "NO SUCH FILE"
msg_exists:
    .asciiz "EXISTS"
msg_path_too_long:
    .asciiz "PATH TOO LONG"
msg_too_large:
    .asciiz "XCOPY TOO LARGE"
msg_copy_fail:
    .asciiz "XCOPY FAIL"
msg_xcopy_ok:
    .asciiz "XCOPY OK"

udos_overlay_end:

.segment "BSS"
stack_count:
    .res 1
mutation_count:
    .res 1
entry_count:
    .res 1
entry_index:
    .res 1
child_is_dir:
    .res 1
path_prefix_len:
    .res 1
path_remaining:
    .res 1
saved_dest_ptr:
    .res 2
source_root:
    .res PATH_LEN
dest_root:
    .res PATH_LEN
current_src:
    .res PATH_LEN
current_dst:
    .res PATH_LEN
child_src:
    .res PATH_LEN
child_dst:
    .res PATH_LEN
entry_list:
    .res ENTRY_MAX * PATH_LEN
source_stack:
    .res STACK_DEPTH * PATH_LEN
dest_stack:
    .res STACK_DEPTH * PATH_LEN
