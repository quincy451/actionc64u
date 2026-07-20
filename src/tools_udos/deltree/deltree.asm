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
STATE_VISIT = 0
STATE_REMOVE = 1
ASCII_SPACE = $20
ASCII_SLASH = $2F
ASCII_DOT = $2E
ASCII_COLON = $3A
SCREEN_A = $01
SCREEN_B = $02

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 3
params:
    .res 3
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
push_state:
    .res 1

.code

udos_overlay_header:
    .byte 'U','D','O','V'
    .byte UDOS_OVERLAY_FORMAT_VERSION
    .byte udos_tool_abi_version
    .byte UDOS_OVERLAY_COMMAND_DELTREE
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
    jeq fail_bad_deltree

    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    lda svc_retptr
    sta src_ptr
    lda svc_retptr+1
    sta src_ptr+1
    jsr parse_one_path
    jcs fail_bad_deltree

    lda #<target_root
    sta src_ptr
    lda #>target_root
    sta src_ptr+1
    jsr trim_trailing_slash
    jsr target_is_protected
    jcs fail_bad_deltree

    jsr preflight_target
    lda target_was_removed
    jne exit_ok

    lda #<target_root
    sta src_ptr
    lda #>target_root
    sta src_ptr+1
    lda #STATE_VISIT
    sta push_state
    jsr push_path_ptr
    jcs fail_too_large

main_loop:
    lda stack_count
    jeq exit_ok
    jsr pop_current_path
    lda current_state
    jne remove_current_dir

    jsr snapshot_current_dir
    lda #<current_path
    sta src_ptr
    lda #>current_path
    sta src_ptr+1
    lda #STATE_REMOVE
    sta push_state
    jsr push_path_ptr
    jcs fail_too_large
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
    jcs fail_delete

    lda #<current_path
    sta src_ptr
    lda #>current_path
    sta src_ptr+1
    lda #<child_path
    sta dst_ptr
    lda #>child_path
    sta dst_ptr+1
    jsr build_child_path
    jcs fail_path_too_long

    lda child_is_dir
    beq delete_child_file
    lda #<child_path
    sta src_ptr
    lda #>child_path
    sta src_ptr+1
    lda #STATE_VISIT
    sta push_state
    jsr push_path_ptr
    jcs fail_too_large
    jmp process_entry_next

delete_child_file:
    jsr reserve_mutation
    jcs fail_too_large
    lda #<child_path
    sta params+0
    lda #>child_path
    sta params+1
    lda #tool_file_status_fail
    sta params+2
    ldx #params
    jsr svc_file_delete_sc0
    lda params+2
    cmp #tool_file_status_ok
    beq delete_child_ok
    cmp #tool_file_status_nofile
    jeq fail_no_such_file
    jmp fail_delete
delete_child_ok:
    inc mutation_count

process_entry_next:
    inc entry_index
    jmp process_entry_loop

remove_current_dir:
    jsr reserve_mutation
    jcs fail_too_large
    lda #<current_path
    sta params+0
    lda #>current_path
    sta params+1
    lda #tool_dir_status_fail
    sta params+2
    ldx #params
    jsr svc_dir_remove_sc0
    lda params+2
    cmp #tool_dir_status_ok
    beq remove_current_ok
    cmp #tool_dir_status_nofile
    jeq fail_no_such_dir
    cmp #tool_dir_status_not_empty
    jeq fail_not_empty
    cmp #tool_dir_status_busy
    jeq fail_busy
    jmp fail_delete
remove_current_ok:
    inc mutation_count
    jmp main_loop

; Remove an empty target immediately; a non-empty target is safe to traverse.
; The service reports BUSY before looking at contents, protecting the live cwd.
preflight_target:
    lda #$00
    sta target_was_removed
    lda #<target_root
    sta params+0
    lda #>target_root
    sta params+1
    lda #tool_dir_status_fail
    sta params+2
    ldx #params
    jsr svc_dir_remove_sc0
    lda params+2
    cmp #tool_dir_status_ok
    beq preflight_removed
    cmp #tool_dir_status_not_empty
    beq preflight_nonempty
    cmp #tool_dir_status_nofile
    jeq fail_no_such_dir
    cmp #tool_dir_status_busy
    jeq fail_busy
    jsr validate_target
    jmp fail_delete
preflight_removed:
    inc mutation_count
    inc target_was_removed
preflight_nonempty:
    rts

validate_target:
    lda #<target_root
    sta params+0
    lda #>target_root
    sta params+1
    ldx #params
    jsr svc_dir_begin_sc0
    lda params+2
    cmp #tool_dir_status_ok
    beq validate_target_ok
    cmp #tool_dir_status_flat
    jeq fail_flat_image
    cmp #tool_dir_status_unmounted
    jeq fail_unmounted
    jmp fail_no_such_dir
validate_target_ok:
    rts

snapshot_current_dir:
    lda #<current_path
    sta params+0
    lda #>current_path
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

parse_one_path:
    ldy #$00
parse_path_skip_space:
    lda (src_ptr),y
    beq parse_path_fail
    cmp #ASCII_SPACE
    bne parse_path_start
    iny
    bne parse_path_skip_space
parse_path_start:
    ldx #$00
parse_path_loop:
    lda (src_ptr),y
    beq parse_path_done
    cmp #ASCII_SPACE
    beq parse_path_done
    cpx #PATH_LEN-1
    bcs parse_path_fail
    sta target_root,x
    inx
    iny
    bne parse_path_loop
parse_path_done:
    lda #$00
    sta target_root,x
    cpx #$00
    beq parse_path_fail
parse_path_trailing_space:
    lda (src_ptr),y
    beq parse_path_ok
    cmp #ASCII_SPACE
    bne parse_path_fail
    iny
    bne parse_path_trailing_space
parse_path_ok:
    clc
    rts
parse_path_fail:
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

target_is_protected:
    lda target_root
    cmp #ASCII_SLASH
    bne target_check_dot
    lda target_root+1
    beq target_protected
target_check_dot:
    lda target_root
    cmp #ASCII_DOT
    bne target_check_drive
    lda target_root+1
    beq target_protected
target_check_drive:
    lda target_root
    cmp #SCREEN_A
    beq target_check_drive_tail
    cmp #SCREEN_B
    bne target_not_protected
target_check_drive_tail:
    lda target_root+1
    cmp #ASCII_COLON
    bne target_not_protected
    lda target_root+2
    beq target_protected
    cmp #ASCII_SLASH
    bne target_not_protected
    lda target_root+3
    bne target_not_protected
target_protected:
    sec
    rts
target_not_protected:
    clc
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

push_path_ptr:
    lda stack_count
    cmp #STACK_DEPTH
    bcs push_path_fail
    sta slot_index
    tax
    lda push_state
    sta state_stack,x
    jsr set_path_slot_ptr
    lda slot_ptr
    sta dst_ptr
    lda slot_ptr+1
    sta dst_ptr+1
    jsr copy_path
    bcs push_path_fail
    inc stack_count
    clc
    rts
push_path_fail:
    sec
    rts

pop_current_path:
    dec stack_count
    lda stack_count
    sta slot_index
    tax
    lda state_stack,x
    sta current_state
    jsr set_path_slot_ptr
    lda slot_ptr
    sta src_ptr
    lda slot_ptr+1
    sta src_ptr+1
    lda #<current_path
    sta dst_ptr
    lda #>current_path
    sta dst_ptr+1
    jmp copy_path

set_path_slot_ptr:
    lda #<path_stack
    sta slot_ptr
    lda #>path_stack
    sta slot_ptr+1
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
    ldx slot_index
    beq advance_entry_done
advance_entry_loop:
    clc
    lda slot_ptr
    adc #PATH_LEN
    sta slot_ptr
    lda slot_ptr+1
    adc #$00
    sta slot_ptr+1
    dex
    bne advance_entry_loop
advance_entry_done:
    rts

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

fail_bad_deltree:
    lda #<msg_bad_deltree
    ldy #>msg_bad_deltree
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
fail_not_empty:
    lda #<msg_not_empty
    ldy #>msg_not_empty
    jmp fail_with_ptr
fail_busy:
    lda #<msg_busy
    ldy #>msg_busy
    jmp fail_with_ptr
fail_path_too_long:
    lda #<msg_path_too_long
    ldy #>msg_path_too_long
    jmp fail_with_ptr
fail_too_large:
    lda #<msg_too_large
    ldy #>msg_too_large
    jmp fail_with_ptr
fail_delete:
    lda #<msg_delete_fail
    ldy #>msg_delete_fail

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
    lda #<msg_deltree_ok
    ldy #>msg_deltree_ok
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

msg_bad_deltree:
    .asciiz "BAD DELTREE"
msg_flat_image:
    .asciiz "FLAT IMAGE"
msg_unmounted:
    .asciiz "UNMOUNTED"
msg_no_such_dir:
    .asciiz "NO SUCH DIR"
msg_no_such_file:
    .asciiz "NO SUCH FILE"
msg_not_empty:
    .asciiz "DIR NOT EMPTY"
msg_busy:
    .asciiz "DIR BUSY"
msg_path_too_long:
    .asciiz "PATH TOO LONG"
msg_too_large:
    .asciiz "DELTREE TOO LARGE"
msg_delete_fail:
    .asciiz "DELTREE FAIL"
msg_deltree_ok:
    .asciiz "DELTREE OK"

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
current_state:
    .res 1
target_was_removed:
    .res 1
target_root:
    .res PATH_LEN
current_path:
    .res PATH_LEN
child_path:
    .res PATH_LEN
entry_list:
    .res ENTRY_MAX * PATH_LEN
path_stack:
    .res STACK_DEPTH * PATH_LEN
state_stack:
    .res STACK_DEPTH
