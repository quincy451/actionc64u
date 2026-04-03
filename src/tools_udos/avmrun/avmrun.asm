.include "udos_services.inc"

.import acheron
.import clear_rstack
.importzp iptr
.importzp iptr_offset
.importzp pptr
.importzp rptr

.export start

.segment "STARTUP"
    jmp start

AVM_HEADER_SIZE = 10
AVM_HEADER_SIZE_V2 = 12
AVM_VERSION_V1 = 1
AVM_VERSION_V2 = 2
AVM_FLAG_ACHERON = 1
FILE_BUFFER_SIZE = 2048
PAYLOAD_BUFFER_SIZE = 1024
INTERP_STACK_MAX = 16

OPCODE_PUSH8 = $10
OPCODE_PUSH16 = $11
OPCODE_STORE = $12
OPCODE_LOAD = $13
OPCODE_ADD = $14
OPCODE_SUB = $15
OPCODE_EQ = $16
OPCODE_NE = $17
OPCODE_JZ = $18
OPCODE_JMP = $19
OPCODE_DUP = $1A
OPCODE_DROP = $1B
OPCODE_LT = $1C
OPCODE_GT = $1D
OPCODE_NATIVE = $2D
OPCODE_CALL = $45
OPCODE_JUMP = $46
OPCODE_RET = $48
OPCODE_CALLN = $49
OPCODE_CLRP = $5C
OPCODE_SETP8 = $5D
OPCODE_SETP16 = $61

INTRINSIC_PRINT = $FF00
INTRINSIC_PRINTE = $FF10
INTRINSIC_EXIT = $FF20
INTRINSIC_PRINTI = $FF30
INTRINSIC_PRINTIE = $FF31

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
file_params:
    .res 9
src_ptr:
    .res 2
payload_ptr:
    .res 2
entry_ptr:
    .res 2
scan_ptr:
    .res 2
scan_end:
    .res 2
word_tmp:
    .res 2
digit_flag:
    .res 1
hex_tmp:
    .res 1

.code

start:
    ldx #svc_retptr
    jsr svc_program_get_cmdline_len
    lda svc_retptr
    ora svc_retptr+1
    bne have_args
    lda #<msg_no_file
    ldy #>msg_no_file
    jmp fail_with_ptr

have_args:
    ldx #svc_retptr
    jsr svc_program_get_cmdline_ptr
    lda svc_retptr
    sta src_ptr
    lda svc_retptr+1
    sta src_ptr+1
    jsr copy_first_arg

    lda #<filename_buffer
    sta file_params+0
    lda #>filename_buffer
    sta file_params+1
    lda #<file_buffer
    sta file_params+2
    lda #>file_buffer
    sta file_params+3
    lda #<FILE_BUFFER_SIZE
    sta file_params+4
    lda #>FILE_BUFFER_SIZE
    sta file_params+5
    lda #$00
    sta file_params+6
    sta file_params+7
    sta file_params+8

    ldx #file_params
    jsr svc_file_load_sc0

    lda file_params+6
    cmp #tool_file_status_ok
    beq file_loaded
    cmp #tool_file_status_nofile
    beq show_no_file
    cmp #tool_file_status_too_large
    beq show_too_large
    lda #<msg_load_fail
    ldy #>msg_load_fail
    bne fail_with_ptr

show_no_file:
    lda #<msg_no_file
    ldy #>msg_no_file
    bne fail_with_ptr

show_too_large:
    lda #<msg_too_large
    ldy #>msg_too_large
    bne fail_with_ptr

file_loaded:
    lda file_params+8
    cmp #>FILE_BUFFER_SIZE
    bcc file_loaded_terminate
    bne file_loaded_skip_terminate
    lda file_params+7
    cmp #<FILE_BUFFER_SIZE
    bcs file_loaded_skip_terminate
file_loaded_terminate:
    clc
    lda #<file_buffer
    adc file_params+7
    sta src_ptr
    lda #>file_buffer
    adc file_params+8
    sta src_ptr+1
    ldy #$00
    lda #$00
    sta (src_ptr),y
file_loaded_skip_terminate:
    jsr prepare_loaded_payload
    bcc header_ok
    lda #<msg_bad_avm
    ldy #>msg_bad_avm
    bne fail_with_ptr

header_ok:
    jsr patch_payload
    bcc payload_ready
    jsr interpret_payload
    bcc interpreted_ok
    lda #<msg_unsupported
    ldy #>msg_unsupported
    bne fail_with_ptr

interpreted_ok:
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

payload_ready:
    jsr clear_rstack
    sec
    lda entry_ptr
    sbc #$01
    sta word_tmp
    lda entry_ptr+1
    sbc #$00
    sta word_tmp+1
    lda word_tmp+1
    pha
    lda word_tmp
    pha
    clc
    jmp acheron

fail_with_ptr:
    jsr print_ptr
    jsr svc_console_newline
    lda #$01
    sta svc_retptr
    lda #$00
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

prepare_loaded_payload:
    lda file_buffer+0
    cmp #'A'
    beq :+
    jmp decode_avm_text
: 
    lda file_buffer+1
    cmp #'V'
    beq :+
    jmp decode_avm_text
: 
    lda file_buffer+2
    cmp #'M'
    beq :+
    jmp decode_avm_text
: 
    lda file_buffer+3
    cmp #'1'
    beq :+
    jmp decode_avm_text
: 
    jmp validate_header

validate_header:
    lda file_buffer+0
    cmp #'A'
    beq :+
    jmp validate_header_fail
:   
    lda file_buffer+1
    cmp #'V'
    beq :+
    jmp validate_header_fail
:   
    lda file_buffer+2
    cmp #'M'
    beq :+
    jmp validate_header_fail
:   
    lda file_buffer+3
    cmp #'1'
    beq :+
    jmp validate_header_fail
:   
    lda file_buffer+4
    cmp #AVM_VERSION_V1
    beq validate_header_v1
    cmp #AVM_VERSION_V2
    beq validate_header_v2
    jmp validate_header_fail
validate_header_v1:
    lda file_buffer+5
    sta scan_end
    lda file_buffer+6
    sta scan_end+1
    lda scan_end
    sta src_ptr
    lda scan_end+1
    sta src_ptr+1
    lda file_buffer+7
    sta word_tmp
    lda file_buffer+8
    sta word_tmp+1
    lda #<(file_buffer + AVM_HEADER_SIZE)
    sta payload_ptr
    lda #>(file_buffer + AVM_HEADER_SIZE)
    sta payload_ptr+1
    jmp validate_header_common
validate_header_v2:
    lda file_buffer+5
    sta scan_end
    lda file_buffer+6
    sta scan_end+1
    lda file_buffer+10
    sta src_ptr
    lda file_buffer+11
    sta src_ptr+1
    lda src_ptr+1
    cmp scan_end+1
    bcc :+
    bne validate_header_fail
    lda src_ptr
    cmp scan_end
    bcc :+
    beq :+
    jmp validate_header_fail
:   lda file_buffer+7
    sta word_tmp
    lda file_buffer+8
    sta word_tmp+1
    lda #<(file_buffer + AVM_HEADER_SIZE_V2)
    sta payload_ptr
    lda #>(file_buffer + AVM_HEADER_SIZE_V2)
    sta payload_ptr+1
validate_header_common:
    lda file_buffer+9
    cmp #AVM_FLAG_ACHERON
    bne validate_header_fail
    lda word_tmp+1
    cmp scan_end+1
    bcc :+
    bne validate_header_fail
    lda word_tmp
    cmp scan_end
    bcs validate_header_fail
:
    clc
    lda payload_ptr
    adc src_ptr
    sta scan_end
    lda payload_ptr+1
    adc src_ptr+1
    sta scan_end+1
    sec
    lda payload_ptr
    adc word_tmp
    sta entry_ptr
    lda payload_ptr+1
    adc word_tmp+1
    sta entry_ptr+1
    sec
    lda entry_ptr
    sbc #$01
    sta entry_ptr
    lda entry_ptr+1
    sbc #$00
    sta entry_ptr+1
    clc
    rts

validate_header_fail:
    sec
    rts

decode_avm_text:
    lda file_buffer+0
    cmp #'e'
    beq :+
    jmp decode_avm_text_fail
: 
    lda file_buffer+1
    cmp #'n'
    beq :+
    jmp decode_avm_text_fail
: 
    lda file_buffer+2
    cmp #'t'
    beq :+
    jmp decode_avm_text_fail
: 
    lda file_buffer+3
    cmp #'r'
    beq :+
    jmp decode_avm_text_fail
: 
    lda file_buffer+4
    cmp #'y'
    beq :+
    jmp decode_avm_text_fail
: 
    lda file_buffer+5
    cmp #' '
    beq :+
    jmp decode_avm_text_fail
: 
    lda #<(file_buffer + 6)
    sta scan_ptr
    lda #>(file_buffer + 6)
    sta scan_ptr+1
    jsr parse_decimal_word_at_scan_ptr
    bcc :+
    jmp decode_avm_text_fail
: 
    lda word_tmp
    sta entry_ptr
    lda word_tmp+1
    sta entry_ptr+1
    lda #$00
    sta scan_end
    sta scan_end+1
    jsr consume_line_break_at_scan_ptr
    bcc :+
    jmp decode_avm_text_fail
: 
    ldy #$00
    lda (scan_ptr),y
    cmp #'c'
    bne decode_avm_text_expect_db
    iny
    lda (scan_ptr),y
    cmp #'o'
    beq :+
    jmp decode_avm_text_fail
: 
    iny
    lda (scan_ptr),y
    cmp #'d'
    beq :+
    jmp decode_avm_text_fail
: 
    iny
    lda (scan_ptr),y
    cmp #'e'
    beq :+
    jmp decode_avm_text_fail
: 
    iny
    lda (scan_ptr),y
    cmp #' '
    beq :+
    jmp decode_avm_text_fail
: 
    lda #$05
    jsr advance_scan_ptr
    ldy #$00
    lda (scan_ptr),y
    cmp #'$'
    bne :+
    lda #$01
    jsr advance_scan_ptr
    jsr parse_hex_byte_at_scan_ptr
    bcc :+
    jmp decode_avm_text_fail
: 
    sta scan_end
    lda #$00
    sta scan_end+1
    jmp decode_avm_text_have_code_len
    jsr parse_decimal_word_at_scan_ptr
    bcc :+
    jmp decode_avm_text_fail
: 
    lda word_tmp
    sta scan_end
    lda word_tmp+1
    sta scan_end+1
decode_avm_text_have_code_len:
    jsr consume_line_break_at_scan_ptr
    bcc :+
    jmp decode_avm_text_fail
: 
decode_avm_text_expect_db:
    ldy #$00
    lda (scan_ptr),y
    cmp #'d'
    beq decode_avm_text_expect_db_prefix
    cmp #'h'
    beq decode_avm_text_expect_hex_prefix
    jmp decode_avm_text_fail
decode_avm_text_expect_db_prefix:
    iny
    lda (scan_ptr),y
    cmp #'b'
    beq :+
    jmp decode_avm_text_fail
: 
    iny
    lda (scan_ptr),y
    cmp #' '
    beq :+
    jmp decode_avm_text_fail
: 
    lda #$03
    jsr advance_scan_ptr
    jmp decode_avm_text_init_payload_ptr
decode_avm_text_expect_hex_prefix:
    iny
    lda (scan_ptr),y
    cmp #'e'
    beq :+
    jmp decode_avm_text_fail
: 
    iny
    lda (scan_ptr),y
    cmp #'x'
    beq :+
    jmp decode_avm_text_fail
: 
    iny
    lda (scan_ptr),y
    cmp #' '
    beq :+
    jmp decode_avm_text_fail
: 
    lda #$04
    jsr advance_scan_ptr
decode_avm_text_init_payload_ptr:
    lda #<payload_buffer
    sta payload_ptr
    sta src_ptr
    lda #>payload_buffer
    sta payload_ptr+1
    sta src_ptr+1
    ldy #$00
    lda (scan_ptr),y
    cmp #'$'
    beq decode_avm_text_byte_loop
    jmp decode_avm_text_hex_loop
decode_avm_text_byte_loop:
    ldy #$00
    lda (scan_ptr),y
    beq decode_avm_text_byte_done
    cmp #10
    beq decode_avm_text_byte_done
    cmp #13
    beq decode_avm_text_byte_done
    cmp #'$'
    beq :+
    jmp decode_avm_text_fail
: 
    lda #$01
    jsr advance_scan_ptr
    jsr parse_hex_byte_at_scan_ptr
    bcc :+
    jmp decode_avm_text_fail
: 
    ldy #$00
    sta (src_ptr),y
    inc src_ptr
    bne :+
    inc src_ptr+1
:   lda src_ptr+1
    cmp #>(payload_buffer + PAYLOAD_BUFFER_SIZE)
    bcc :+
    beq :+
    jmp decode_avm_text_fail
: 
    lda src_ptr
    cmp #<(payload_buffer + PAYLOAD_BUFFER_SIZE)
    bcc :+
    bne :+
    jmp decode_avm_text_fail
:   ldy #$00
    lda (scan_ptr),y
    cmp #','
    beq decode_avm_text_consume_comma
    cmp #$00
    beq decode_avm_text_byte_done
    cmp #10
    beq decode_avm_text_byte_done
    cmp #13
    beq decode_avm_text_byte_done
    jmp decode_avm_text_fail
decode_avm_text_consume_comma:
    lda #$01
    jsr advance_scan_ptr
    jmp decode_avm_text_byte_loop
decode_avm_text_byte_done:
    jmp decode_avm_text_done
decode_avm_text_hex_loop:
    ldy #$00
    lda (scan_ptr),y
    beq decode_avm_text_done
    cmp #10
    beq decode_avm_text_done
    cmp #13
    beq decode_avm_text_done
    jsr parse_hex_byte_at_scan_ptr
    bcc :+
    jmp decode_avm_text_fail
: 
    ldy #$00
    sta (src_ptr),y
    inc src_ptr
    bne :+
    inc src_ptr+1
:   lda src_ptr+1
    cmp #>(payload_buffer + PAYLOAD_BUFFER_SIZE)
    bcc :+
    beq :+
    jmp decode_avm_text_fail
: 
    lda src_ptr
    cmp #<(payload_buffer + PAYLOAD_BUFFER_SIZE)
    bcc :+
    bne :+
    jmp decode_avm_text_fail
:   jmp decode_avm_text_hex_loop
decode_avm_text_done:
    lda src_ptr
    cmp payload_ptr
    bne decode_avm_text_have_payload
    lda src_ptr+1
    cmp payload_ptr+1
    bne decode_avm_text_have_payload
    jmp decode_avm_text_fail
decode_avm_text_have_payload:
    lda scan_end
    ora scan_end+1
    beq decode_avm_text_use_payload_end
    clc
    lda payload_ptr
    adc scan_end
    sta scan_end
    lda payload_ptr+1
    adc scan_end+1
    sta scan_end+1
    jmp decode_avm_text_check_entry
decode_avm_text_use_payload_end:
    lda src_ptr
    sta scan_end
    lda src_ptr+1
    sta scan_end+1
decode_avm_text_check_entry:
    lda payload_ptr
    clc
    adc entry_ptr
    sta entry_ptr
    lda payload_ptr+1
    adc entry_ptr+1
    sta entry_ptr+1
    lda entry_ptr+1
    cmp scan_end+1
    bcc decode_avm_text_check_code_end
    bne decode_avm_text_entry_fail
    lda entry_ptr
    cmp scan_end
    bcc decode_avm_text_check_code_end
decode_avm_text_entry_fail:
    jmp decode_avm_text_fail
decode_avm_text_check_code_end:
    lda scan_end+1
    cmp src_ptr+1
    bcc decode_avm_text_success
    bne decode_avm_text_code_end_fail
    lda scan_end
    cmp src_ptr
    bcc decode_avm_text_success
    beq decode_avm_text_success
decode_avm_text_code_end_fail:
    jmp decode_avm_text_fail
decode_avm_text_success:
    clc
    rts
decode_avm_text_fail:
    sec
    rts

parse_decimal_word_at_scan_ptr:
    lda #$00
    sta word_tmp
    sta word_tmp+1
    sta digit_flag
parse_decimal_word_at_scan_ptr_loop:
    ldy #$00
    lda (scan_ptr),y
    cmp #'0'
    bcc parse_decimal_word_at_scan_ptr_done
    cmp #'9'+1
    bcs parse_decimal_word_at_scan_ptr_done
    sec
    sbc #'0'
    pha
    lda word_tmp
    sta hex_tmp
    lda word_tmp+1
    pha
    lda word_tmp
    asl a
    rol word_tmp+1
    sta word_tmp
    lda word_tmp
    asl a
    rol word_tmp+1
    asl a
    rol word_tmp+1
    clc
    adc hex_tmp
    sta word_tmp
    pla
    adc word_tmp+1
    sta word_tmp+1
    lda hex_tmp
    clc
    adc word_tmp
    sta word_tmp
    bcc :+
    inc word_tmp+1
:   pla
    clc
    adc word_tmp
    sta word_tmp
    bcc :+
    inc word_tmp+1
:   lda #$01
    sta digit_flag
    lda #$01
    jsr advance_scan_ptr
    jmp parse_decimal_word_at_scan_ptr_loop
parse_decimal_word_at_scan_ptr_done:
    lda digit_flag
    beq decode_avm_text_fail
    clc
    rts

consume_line_break_at_scan_ptr:
    ldy #$00
    lda (scan_ptr),y
    cmp #13
    beq consume_line_break_cr
    cmp #10
    beq consume_line_break_lf
    sec
    rts
consume_line_break_cr:
    lda #$01
    jsr advance_scan_ptr
    ldy #$00
    lda (scan_ptr),y
    cmp #10
    bne :+
    lda #$01
    jsr advance_scan_ptr
:   clc
    rts
consume_line_break_lf:
    lda #$01
    jsr advance_scan_ptr
    clc
    rts

parse_hex_byte_at_scan_ptr:
    jsr parse_hex_nibble_at_scan_ptr
    bcs parse_hex_byte_at_scan_ptr_fail
    asl a
    asl a
    asl a
    asl a
    sta hex_tmp
    jsr parse_hex_nibble_at_scan_ptr
    bcs parse_hex_byte_at_scan_ptr_fail
    ora hex_tmp
    clc
    rts
parse_hex_byte_at_scan_ptr_fail:
    sec
    rts

parse_hex_nibble_at_scan_ptr:
    ldy #$00
    lda (scan_ptr),y
    cmp #'0'
    bcc parse_hex_nibble_at_scan_ptr_bad
    cmp #'9'+1
    bcc parse_hex_nibble_at_scan_ptr_digit
    cmp #'a'
    bcc parse_hex_nibble_at_scan_ptr_upper
    cmp #'f'+1
    bcs parse_hex_nibble_at_scan_ptr_bad
    sec
    sbc #'a'-10
    pha
    lda #$01
    jsr advance_scan_ptr
    pla
    clc
    rts
parse_hex_nibble_at_scan_ptr_upper:
    cmp #'A'
    bcc parse_hex_nibble_at_scan_ptr_bad
    cmp #'F'+1
    bcs parse_hex_nibble_at_scan_ptr_bad
    sec
    sbc #'A'-10
    pha
    lda #$01
    jsr advance_scan_ptr
    pla
    clc
    rts
parse_hex_nibble_at_scan_ptr_digit:
    sec
    sbc #'0'
    pha
    lda #$01
    jsr advance_scan_ptr
    pla
    clc
    rts
parse_hex_nibble_at_scan_ptr_bad:
    sec
    rts

patch_payload:
    lda payload_ptr
    sta scan_ptr
    lda payload_ptr+1
    sta scan_ptr+1
patch_payload_loop:
    lda scan_ptr
    cmp scan_end
    bne :+
    lda scan_ptr+1
    cmp scan_end+1
    bne :+
    jmp patch_payload_done
: 
    jsr scan_ptr_before_end
    bcc :+
    jmp patch_payload_fail
:
    ldy #$00
    lda (scan_ptr),y
    cmp #OPCODE_PUSH8
    bne :+
    jmp patch_byte_arg
:
    cmp #OPCODE_PUSH16
    bne :+
    jmp patch_literal_word_arg
:
    cmp #OPCODE_NATIVE
    bne :+
    jmp patch_payload_done
:
    cmp #OPCODE_RET
    bne :+
    jmp patch_zero_arg
:
    cmp #OPCODE_CLRP
    bne :+
    jmp patch_zero_arg
:
    cmp #OPCODE_SETP8
    bne :+
    jmp patch_byte_arg
:
    cmp #OPCODE_CALL
    bne :+
    jmp patch_word_arg
:
    cmp #OPCODE_JUMP
    bne :+
    jmp patch_word_arg
:
    cmp #OPCODE_SETP16
    bne :+
    jmp patch_setp16
:
    cmp #OPCODE_CALLN
    bne :+
    jmp patch_calln
:
    sec
    rts

patch_zero_arg:
    lda #$01
    jsr advance_scan_ptr
    jmp patch_payload_loop

patch_byte_arg:
    jsr ensure_scan_room_2
    bcc :+
    jmp patch_payload_fail
:
    lda #$02
    jsr advance_scan_ptr
    jmp patch_payload_loop

patch_literal_word_arg:
    jsr ensure_scan_room_3
    bcc :+
    jmp patch_payload_fail
:
    lda #$03
    jsr advance_scan_ptr
    jmp patch_payload_loop

patch_word_arg:
    jsr ensure_scan_room_3
    bcc :+
    jmp patch_payload_fail
:
    ldy #$01
    lda (scan_ptr),y
    sta word_tmp
    iny
    lda (scan_ptr),y
    sta word_tmp+1
    clc
    lda word_tmp
    adc payload_ptr
    sta word_tmp
    lda word_tmp+1
    adc payload_ptr+1
    sta word_tmp+1
    ldy #$01
    lda word_tmp
    sta (scan_ptr),y
    iny
    lda word_tmp+1
    sta (scan_ptr),y
    lda #$03
    jsr advance_scan_ptr
    jmp patch_payload_loop

patch_setp16:
    jsr ensure_scan_room_3
    bcc :+
    jmp patch_payload_fail
:
    ldy #$01
    lda (scan_ptr),y
    sta word_tmp
    iny
    lda (scan_ptr),y
    sta word_tmp+1
    clc
    lda word_tmp
    adc payload_ptr
    sta word_tmp
    lda word_tmp+1
    adc payload_ptr+1
    sta word_tmp+1
    ldy #$01
    lda word_tmp
    sta (scan_ptr),y
    iny
    lda word_tmp+1
    sta (scan_ptr),y
    lda #$03
    jsr advance_scan_ptr
    jmp patch_payload_loop

patch_calln:
    jsr ensure_scan_room_3
    bcc :+
    jmp patch_payload_fail
: 
    ldy #$01
    lda (scan_ptr),y
    sta word_tmp
    iny
    lda (scan_ptr),y
    sta word_tmp+1
    lda word_tmp
    cmp #<INTRINSIC_PRINT
    bne patch_check_printe
    lda word_tmp+1
    cmp #>INTRINSIC_PRINT
    beq patch_calln_print
patch_check_printe:
    lda word_tmp
    cmp #<INTRINSIC_PRINTE
    bne patch_check_printi
    lda word_tmp+1
    cmp #>INTRINSIC_PRINTE
    beq patch_calln_printe
patch_check_printi:
    lda word_tmp
    cmp #<INTRINSIC_PRINTI
    bne patch_check_printie
    lda word_tmp+1
    cmp #>INTRINSIC_PRINTI
    beq patch_calln_printi
patch_check_printie:
    lda word_tmp
    cmp #<INTRINSIC_PRINTIE
    bne patch_check_exit_real
    lda word_tmp+1
    cmp #>INTRINSIC_PRINTIE
    beq patch_calln_printie
patch_check_exit:
patch_check_exit_real:
    lda word_tmp
    cmp #<INTRINSIC_EXIT
    bne patch_payload_fail
    lda word_tmp+1
    cmp #>INTRINSIC_EXIT
    bne patch_payload_fail
    lda #<native_exit
    sta word_tmp
    lda #>native_exit
    sta word_tmp+1
    bne patch_calln_store
patch_calln_print:
    lda #<native_print
    sta word_tmp
    lda #>native_print
    sta word_tmp+1
    bne patch_calln_store
patch_calln_printe:
    lda #<native_printe
    sta word_tmp
    lda #>native_printe
    sta word_tmp+1
    bne patch_calln_store
patch_calln_printi:
    jsr lower_previous_push16_to_setp16
    bcc :+
    jmp patch_payload_fail
: 
    lda #<native_printi
    sta word_tmp
    lda #>native_printi
    sta word_tmp+1
    bne patch_calln_store
patch_calln_printie:
    jsr lower_previous_push16_to_setp16
    bcc :+
    jmp patch_payload_fail
: 
    lda #<native_printie
    sta word_tmp
    lda #>native_printie
    sta word_tmp+1
patch_calln_store:
    ldy #$01
    lda word_tmp
    sta (scan_ptr),y
    iny
    lda word_tmp+1
    sta (scan_ptr),y
    lda #$03
    jsr advance_scan_ptr
    jmp patch_payload_loop

patch_payload_done:
    clc
    rts

patch_payload_fail:
    sec
    rts

interpret_payload:
    lda #$00
    sta interp_sp
    sta interp_rsp
    lda entry_ptr
    sta scan_ptr
    lda entry_ptr+1
    sta scan_ptr+1
    lda payload_ptr
    sta interp_string_ptr
    lda payload_ptr+1
    sta interp_string_ptr+1
interpret_payload_loop:
    lda scan_ptr
    cmp scan_end
    bne :+
    lda scan_ptr+1
    cmp scan_end+1
    bne :+
    jmp interpret_payload_done
:   jsr scan_ptr_before_end
    bcc :+
    jmp interpret_payload_fail
:   ldy #$00
    lda (scan_ptr),y
    cmp #OPCODE_PUSH8
    bne :+
    jmp interpret_push8
:   cmp #OPCODE_PUSH16
    bne :+
    jmp interpret_push16
:   cmp #OPCODE_ADD
    bne :+
    jmp interpret_add
:   cmp #OPCODE_SUB
    bne :+
    jmp interpret_sub
:   cmp #OPCODE_EQ
    bne :+
    jmp interpret_eq
:   cmp #OPCODE_NE
    bne :+
    jmp interpret_ne
:   cmp #OPCODE_LT
    bne :+
    jmp interpret_lt
:   cmp #OPCODE_GT
    bne :+
    jmp interpret_gt
:   cmp #OPCODE_DUP
    bne :+
    jmp interpret_dup
:   cmp #OPCODE_DROP
    bne :+
    jmp interpret_drop
:   cmp #OPCODE_SETP16
    bne :+
    jmp interpret_setp16
:   cmp #OPCODE_CALL
    bne :+
    jmp interpret_call
:   cmp #OPCODE_RET
    bne :+
    jmp interpret_ret
:   cmp #OPCODE_CALLN
    bne :+
    jmp interpret_calln
:   sec
    rts

interpret_push8:
    jsr ensure_scan_room_2
    bcc :+
    jmp interpret_payload_fail
:   ldy #$01
    lda (scan_ptr),y
    sta word_tmp
    lda #$00
    sta word_tmp+1
    jsr interp_push_word_tmp
    bcc :+
    jmp interpret_payload_fail
:   lda #$02
    jsr advance_scan_ptr
    jmp interpret_payload_loop

interpret_push16:
    jsr ensure_scan_room_3
    bcc :+
    jmp interpret_payload_fail
:   ldy #$01
    lda (scan_ptr),y
    sta word_tmp
    iny
    lda (scan_ptr),y
    sta word_tmp+1
    jsr interp_push_word_tmp
    bcc :+
    jmp interpret_payload_fail
:   lda #$03
    jsr advance_scan_ptr
    jmp interpret_payload_loop

interpret_add:
    jsr interp_pop_to_word_tmp
    bcc :+
    jmp interpret_payload_fail
:   jsr interp_pop_to_svc_retptr
    bcc :+
    jmp interpret_payload_fail
:   clc
    lda svc_retptr
    adc word_tmp
    sta word_tmp
    lda svc_retptr+1
    adc word_tmp+1
    sta word_tmp+1
    jsr interp_push_word_tmp
    bcc :+
    jmp interpret_payload_fail
:   lda #$01
    jsr advance_scan_ptr
    jmp interpret_payload_loop

interpret_sub:
    jsr interp_pop_to_word_tmp
    bcc :+
    jmp interpret_payload_fail
:   jsr interp_pop_to_svc_retptr
    bcc :+
    jmp interpret_payload_fail
:   sec
    lda svc_retptr
    sbc word_tmp
    sta word_tmp
    lda svc_retptr+1
    sbc word_tmp+1
    sta word_tmp+1
    jsr interp_push_word_tmp
    bcc :+
    jmp interpret_payload_fail
:   lda #$01
    jsr advance_scan_ptr
    jmp interpret_payload_loop

interpret_eq:
    jsr interp_compare_to_bool_eq
    jmp interpret_compare_common

interpret_ne:
    jsr interp_compare_to_bool_ne
    jmp interpret_compare_common

interpret_lt:
    jsr interp_compare_to_bool_lt
    jmp interpret_compare_common

interpret_gt:
    jsr interp_compare_to_bool_gt
interpret_compare_common:
    bcc :+
    jmp interpret_payload_fail
:   jsr interp_push_word_tmp
    bcc :+
    jmp interpret_payload_fail
:   lda #$01
    jsr advance_scan_ptr
    jmp interpret_payload_loop

interpret_dup:
    jsr interp_peek_to_word_tmp
    bcc :+
    jmp interpret_payload_fail
:   jsr interp_push_word_tmp
    bcc :+
    jmp interpret_payload_fail
:   lda #$01
    jsr advance_scan_ptr
    jmp interpret_payload_loop

interpret_drop:
    lda interp_sp
    bne :+
    jmp interpret_payload_fail
: 
    dec interp_sp
    lda #$01
    jsr advance_scan_ptr
    jmp interpret_payload_loop

interpret_setp16:
    jsr ensure_scan_room_3
    bcc :+
    jmp interpret_payload_fail
:   ldy #$01
    lda (scan_ptr),y
    sta word_tmp
    iny
    lda (scan_ptr),y
    sta word_tmp+1
    jsr interpret_resolve_word_tmp_to_absolute
    bcc :+
    jmp interpret_payload_fail
:   lda word_tmp
    sta interp_string_ptr
    lda word_tmp+1
    sta interp_string_ptr+1
    lda #$03
    jsr advance_scan_ptr
    jmp interpret_payload_loop

interpret_call:
    jsr ensure_scan_room_3
    bcc :+
    jmp interpret_payload_fail
:   lda interp_rsp
    cmp #INTERP_STACK_MAX
    bcc :+
    jmp interpret_payload_fail
:   ldx interp_rsp
    clc
    lda scan_ptr
    adc #$03
    sta interp_rstack_lo,x
    lda scan_ptr+1
    adc #$00
    sta interp_rstack_hi,x
    inc interp_rsp
    ldy #$01
    lda (scan_ptr),y
    sta word_tmp
    iny
    lda (scan_ptr),y
    sta word_tmp+1
    jsr interpret_resolve_word_tmp_to_absolute
    bcc :+
    jmp interpret_payload_fail
:   lda word_tmp
    sta scan_ptr
    lda word_tmp+1
    sta scan_ptr+1
    jmp interpret_payload_loop

interpret_ret:
    lda interp_rsp
    bne :+
    jmp interpret_payload_done
:   dec interp_rsp
    ldx interp_rsp
    lda interp_rstack_lo,x
    sta scan_ptr
    lda interp_rstack_hi,x
    sta scan_ptr+1
    jmp interpret_payload_loop

interpret_calln:
    jsr ensure_scan_room_3
    bcc :+
    jmp interpret_payload_fail
:   ldy #$01
    lda (scan_ptr),y
    sta word_tmp
    iny
    lda (scan_ptr),y
    sta word_tmp+1
    lda word_tmp
    cmp #<INTRINSIC_PRINT
    bne :+
    lda word_tmp+1
    cmp #>INTRINSIC_PRINT
    beq interpret_calln_print
:   lda word_tmp
    cmp #<native_print
    bne interpret_calln_check_printe
    lda word_tmp+1
    cmp #>native_print
    beq interpret_calln_print
interpret_calln_check_printe:
    lda word_tmp
    cmp #<INTRINSIC_PRINTE
    bne :+
    lda word_tmp+1
    cmp #>INTRINSIC_PRINTE
    beq interpret_calln_printe
:   lda word_tmp
    cmp #<native_printe
    bne interpret_calln_check_printi
    lda word_tmp+1
    cmp #>native_printe
    beq interpret_calln_printe
interpret_calln_check_printi:
    lda word_tmp
    cmp #<INTRINSIC_PRINTI
    bne :+
    lda word_tmp+1
    cmp #>INTRINSIC_PRINTI
    beq interpret_calln_printi
:   lda word_tmp
    cmp #<native_printi
    bne interpret_calln_check_printie
    lda word_tmp+1
    cmp #>native_printi
    beq interpret_calln_printi
interpret_calln_check_printie:
    lda word_tmp
    cmp #<INTRINSIC_PRINTIE
    bne :+
    lda word_tmp+1
    cmp #>INTRINSIC_PRINTIE
    beq interpret_calln_printie
:   lda word_tmp
    cmp #<native_printie
    bne interpret_calln_check_exit
    lda word_tmp+1
    cmp #>native_printie
    beq interpret_calln_printie
interpret_calln_check_exit:
    lda word_tmp
    cmp #<INTRINSIC_EXIT
    bne :+
    lda word_tmp+1
    cmp #>INTRINSIC_EXIT
    beq :++
:   lda word_tmp
    cmp #<native_exit
    bne interpret_payload_fail
    lda word_tmp+1
    cmp #>native_exit
    bne interpret_payload_fail
:   lda #$03
    jsr advance_scan_ptr
    jmp interpret_payload_done

interpret_calln_print:
    lda interp_string_ptr
    sta svc_retptr
    lda interp_string_ptr+1
    sta svc_retptr+1
    ldx #svc_retptr
    jsr svc_console_write_sc0
    lda #$03
    jsr advance_scan_ptr
    jmp interpret_payload_loop

interpret_calln_printe:
    lda interp_string_ptr
    sta svc_retptr
    lda interp_string_ptr+1
    sta svc_retptr+1
    ldx #svc_retptr
    jsr svc_console_write_sc0
    jsr svc_console_newline
    lda #$03
    jsr advance_scan_ptr
    jmp interpret_payload_loop

interpret_calln_printi:
    jsr interp_peek_to_word_tmp
    bcc :+
    jmp interpret_payload_fail
:   jsr print_u16_word_tmp
    lda #$03
    jsr advance_scan_ptr
    jmp interpret_payload_loop

interpret_calln_printie:
    jsr interp_peek_to_word_tmp
    bcc :+
    jmp interpret_payload_fail
:   jsr print_u16_word_tmp
    jsr svc_console_newline
    lda #$03
    jsr advance_scan_ptr
    jmp interpret_payload_loop

interpret_payload_done:
    clc
    rts

interpret_payload_fail:
    sec
    rts

interp_push_word_tmp:
    ldx interp_sp
    cpx #INTERP_STACK_MAX
    bcc :+
    sec
    rts
:   lda word_tmp
    sta interp_stack_lo,x
    lda word_tmp+1
    sta interp_stack_hi,x
    inc interp_sp
    clc
    rts

interp_pop_to_word_tmp:
    lda interp_sp
    beq interp_pop_fail
    dec interp_sp
    ldx interp_sp
    lda interp_stack_lo,x
    sta word_tmp
    lda interp_stack_hi,x
    sta word_tmp+1
    clc
    rts

interp_pop_to_svc_retptr:
    lda interp_sp
    beq interp_pop_fail
    dec interp_sp
    ldx interp_sp
    lda interp_stack_lo,x
    sta svc_retptr
    lda interp_stack_hi,x
    sta svc_retptr+1
    clc
    rts

interp_peek_to_word_tmp:
    lda interp_sp
    beq interp_pop_fail
    sec
    sbc #$01
    tax
    lda interp_stack_lo,x
    sta word_tmp
    lda interp_stack_hi,x
    sta word_tmp+1
    clc
    rts

interp_pop_fail:
    sec
    rts

interp_compare_to_bool_eq:
    jsr interp_pop_to_word_tmp
    bcc :+
    sec
    rts
:   jsr interp_pop_to_svc_retptr
    bcc :+
    sec
    rts
:   lda svc_retptr
    cmp word_tmp
    bne interp_compare_false
    lda svc_retptr+1
    cmp word_tmp+1
    bne interp_compare_false
    jmp interp_compare_true

interp_compare_to_bool_ne:
    jsr interp_pop_to_word_tmp
    bcc :+
    sec
    rts
:   jsr interp_pop_to_svc_retptr
    bcc :+
    sec
    rts
:   lda svc_retptr
    cmp word_tmp
    bne interp_compare_true
    lda svc_retptr+1
    cmp word_tmp+1
    bne interp_compare_true
    jmp interp_compare_false

interp_compare_to_bool_lt:
    jsr interp_pop_to_word_tmp
    bcc :+
    sec
    rts
:   jsr interp_pop_to_svc_retptr
    bcc :+
    sec
    rts
:   lda svc_retptr+1
    cmp word_tmp+1
    bcc interp_compare_true
    bne interp_compare_false
    lda svc_retptr
    cmp word_tmp
    bcc interp_compare_true
    jmp interp_compare_false

interp_compare_to_bool_gt:
    jsr interp_pop_to_word_tmp
    bcc :+
    sec
    rts
:   jsr interp_pop_to_svc_retptr
    bcc :+
    sec
    rts
:   lda svc_retptr+1
    cmp word_tmp+1
    bcc interp_compare_false
    bne interp_compare_true
    lda svc_retptr
    cmp word_tmp
    bcc interp_compare_false
    beq interp_compare_false
    jmp interp_compare_true

interp_compare_true:
    lda #$01
    sta word_tmp
    lda #$00
    sta word_tmp+1
    clc
    rts

interp_compare_false:
    lda #$00
    sta word_tmp
    sta word_tmp+1
    clc
    rts

interpret_resolve_word_tmp_to_absolute:
    lda word_tmp+1
    cmp payload_ptr+1
    bcc interpret_resolve_relative
    bne interpret_resolve_absolute
    lda word_tmp
    cmp payload_ptr
    bcc interpret_resolve_relative
    bcs interpret_resolve_absolute
interpret_resolve_relative:
    clc
    lda word_tmp
    adc payload_ptr
    sta word_tmp
    lda word_tmp+1
    adc payload_ptr+1
    sta word_tmp+1
interpret_resolve_absolute:
    clc
    rts

lower_previous_push16_to_setp16:
    sec
    lda scan_ptr
    sbc #$03
    sta word_tmp
    lda scan_ptr+1
    sbc #$00
    sta word_tmp+1
    lda word_tmp+1
    cmp payload_ptr+1
    bcc lower_previous_push16_to_setp16_fail
    bne :+
    lda word_tmp
    cmp payload_ptr
    bcc lower_previous_push16_to_setp16_fail
:  ldy #$00
    lda (word_tmp),y
    cmp #OPCODE_PUSH16
    bne lower_previous_push16_to_setp16_fail
    lda #OPCODE_SETP16
    sta (word_tmp),y
    clc
    rts
lower_previous_push16_to_setp16_fail:
    sec
    rts

scan_ptr_before_end:
    lda scan_ptr+1
    cmp scan_end+1
    bcc scan_ptr_before_end_ok
    bne scan_ptr_before_end_fail
    lda scan_ptr
    cmp scan_end
    bcc scan_ptr_before_end_ok
scan_ptr_before_end_fail:
    sec
    rts
scan_ptr_before_end_ok:
    clc
    rts

ensure_scan_room_3:
    clc
    lda scan_ptr
    adc #$03
    sta word_tmp
    lda scan_ptr+1
    adc #$00
    sta word_tmp+1
    lda word_tmp+1
    cmp scan_end+1
    bcc ensure_scan_room_3_ok
    bne ensure_scan_room_3_fail
    lda word_tmp
    cmp scan_end
    bcc ensure_scan_room_3_ok
    beq ensure_scan_room_3_ok
ensure_scan_room_3_fail:
    sec
    rts
ensure_scan_room_3_ok:
    clc
    rts

ensure_scan_room_2:
    clc
    lda scan_ptr
    adc #$02
    sta word_tmp
    lda scan_ptr+1
    adc #$00
    sta word_tmp+1
    lda word_tmp+1
    cmp scan_end+1
    bcc ensure_scan_room_2_ok
    bne ensure_scan_room_2_fail
    lda word_tmp
    cmp scan_end
    bcc ensure_scan_room_2_ok
    beq ensure_scan_room_2_ok
ensure_scan_room_2_fail:
    sec
    rts
ensure_scan_room_2_ok:
    clc
    rts

advance_scan_ptr:
    clc
    adc scan_ptr
    sta scan_ptr
    bcc :+
    inc scan_ptr+1
:
    rts

native_print:
    jsr save_vm_state
    lda 0,x
    sta svc_retptr
    lda 1,x
    sta svc_retptr+1
    ldx #svc_retptr
    jsr svc_console_write_sc0
    jsr restore_vm_state
    rts

native_printe:
    jsr save_vm_state
    lda 0,x
    sta svc_retptr
    lda 1,x
    sta svc_retptr+1
    ldx #svc_retptr
    jsr svc_console_write_sc0
    jsr svc_console_newline
    jsr restore_vm_state
    rts

native_printi:
    jsr save_vm_state
    lda 0,x
    sta word_tmp
    lda 1,x
    sta word_tmp+1
    jsr print_u16_word_tmp
    jsr restore_vm_state
    rts

native_printie:
    jsr save_vm_state
    lda 0,x
    sta word_tmp
    lda 1,x
    sta word_tmp+1
    jsr print_u16_word_tmp
    jsr svc_console_newline
    jsr restore_vm_state
    rts

native_exit:
    lda #$00
    sta svc_retptr
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

print_u16_word_tmp:
    lda #$00
    sta digit_flag
    ldx #$00
print_u16_word_tmp_loop:
    cpx #$04
    beq print_u16_word_tmp_ones
    jsr print_digit_divisor_x
    inx
    bne print_u16_word_tmp_loop
print_u16_word_tmp_ones:
    lda word_tmp
    clc
    adc #'0'
    jmp print_char_a

print_digit_divisor_x:
    lda #$00
    sta hex_tmp
print_digit_divisor_x_sub_loop:
    lda word_tmp+1
    cmp decimal_divisors_hi,x
    bcc print_digit_divisor_x_done
    bne :+
    lda word_tmp
    cmp decimal_divisors_lo,x
    bcc print_digit_divisor_x_done
:   sec
    lda word_tmp
    sbc decimal_divisors_lo,x
    sta word_tmp
    lda word_tmp+1
    sbc decimal_divisors_hi,x
    sta word_tmp+1
    inc hex_tmp
    bne print_digit_divisor_x_sub_loop
print_digit_divisor_x_done:
    lda digit_flag
    bne print_digit_divisor_x_emit
    lda hex_tmp
    beq print_digit_divisor_x_skip
print_digit_divisor_x_emit:
    lda hex_tmp
    clc
    adc #'0'
    jsr print_char_a
    lda #$01
    sta digit_flag
print_digit_divisor_x_skip:
    rts

print_char_a:
    sta char_buffer
    lda #$00
    sta char_buffer+1
    tya
    pha
    txa
    pha
    lda #<char_buffer
    sta svc_retptr
    lda #>char_buffer
    sta svc_retptr+1
    ldx #svc_retptr
    jsr svc_console_write_sc0
    pla
    tax
    pla
    tay
    rts

copy_first_arg:
    ldy #$00
copy_first_arg_loop:
    lda (src_ptr),y
    beq copy_first_arg_done
    cmp #' '
    beq copy_first_arg_done
    sta filename_buffer,y
    iny
    cpy #31
    bcc copy_first_arg_loop
copy_first_arg_done:
    lda #$00
    sta filename_buffer,y
    rts

print_ptr:
    sta svc_retptr
    sty svc_retptr+1
    ldx #svc_retptr
    jmp svc_console_write_sc0

save_vm_state:
    lda iptr
    sta saved_iptr
    lda iptr+1
    sta saved_iptr+1
    lda iptr_offset
    sta saved_iptr_offset
    lda pptr
    sta saved_pptr
    lda rptr
    sta saved_rptr
    rts

restore_vm_state:
    lda saved_iptr
    sta iptr
    lda saved_iptr+1
    sta iptr+1
    lda saved_iptr_offset
    sta iptr_offset
    lda saved_pptr
    sta pptr
    lda saved_rptr
    sta rptr
    rts

msg_no_file:
    .asciiz "NO FILE"
msg_too_large:
    .asciiz "TOO LARGE"
msg_load_fail:
    .asciiz "LOAD FAIL"
msg_bad_avm:
    .asciiz "BAD AVM"
msg_unsupported:
    .asciiz "UNSUPPORTED AVM"

decimal_divisors_lo:
    .byte <10000,<1000,<100,<10
decimal_divisors_hi:
    .byte >10000,>1000,>100,>10

.segment "BSS"

filename_buffer:
    .res 32
file_buffer:
    .res FILE_BUFFER_SIZE
payload_buffer:
    .res PAYLOAD_BUFFER_SIZE
char_buffer:
    .res 2
interp_sp:
    .res 1
interp_rsp:
    .res 1
interp_string_ptr:
    .res 2
interp_stack_lo:
    .res INTERP_STACK_MAX
interp_stack_hi:
    .res INTERP_STACK_MAX
interp_rstack_lo:
    .res INTERP_STACK_MAX
interp_rstack_hi:
    .res INTERP_STACK_MAX

saved_iptr:
    .res 2
saved_iptr_offset:
    .res 1
saved_pptr:
    .res 1
saved_rptr:
    .res 1
