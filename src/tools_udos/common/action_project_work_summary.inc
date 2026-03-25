scan_current_dir:
    ldx #svc_retptr
    jsr svc_dir_begin_current
    lda svc_retptr
    ora svc_retptr+1
    beq scan_current_dir_done
scan_current_dir_loop:
    ldx #svc_retptr
    jsr svc_dir_next
    lda svc_retptr
    ora svc_retptr+1
    beq scan_current_dir_done
    lda svc_retptr
    sta entry_ptr
    lda svc_retptr+1
    sta entry_ptr+1

    lda #<project_marker
    ldy #>project_marker
    jsr entry_equals_const
    bcs :+
    lda status_flags
    ora #FLAG_PROJECT
    sta status_flags
:   lda #<src_dir_name
    ldy #>src_dir_name
    jsr entry_equals_const
    bcs :+
    lda status_flags
    ora #FLAG_SRC
    sta status_flags
:   lda #<bin_dir_name
    ldy #>bin_dir_name
    jsr entry_equals_const
    bcs :+
    lda status_flags
    ora #FLAG_BIN
    sta status_flags
:   lda #<obj_dir_name
    ldy #>obj_dir_name
    jsr entry_equals_const
    bcs :+
    lda status_flags
    ora #FLAG_OBJ
    sta status_flags
:   jmp scan_current_dir_loop
scan_current_dir_done:
    rts

entry_equals_const:
    sta const_ptr
    sty const_ptr+1
    ldy #$00
entry_equals_const_loop:
    lda (entry_ptr),y
    jsr normalize_compare_char
    sta compare_char
    lda (const_ptr),y
    jsr normalize_compare_char
    cmp compare_char
    bne entry_equals_const_fail
    cmp #$00
    beq entry_equals_const_ok
    iny
    bne entry_equals_const_loop
entry_equals_const_fail:
    sec
    rts
entry_equals_const_ok:
    clc
    rts

normalize_compare_char:
    cmp #$01
    bcc normalize_compare_ascii
    cmp #$1B
    bcs normalize_compare_ascii
    clc
    adc #$40
    rts
normalize_compare_ascii:
    cmp #'a'
    bcc :+
    cmp #'z'+1
    bcs :+
    and #$DF
:    
    rts

print_work_summary:
    lda #<msg_project_prefix
    ldy #>msg_project_prefix
    jsr print_ptr
    lda status_flags
    and #FLAG_PROJECT
    beq print_work_project_no
    lda #<msg_yes
    ldy #>msg_yes
    jsr print_line_ptr
    jmp print_work_src
print_work_project_no:
    lda #<msg_no
    ldy #>msg_no
    jsr print_line_ptr

print_work_src:
    lda #<msg_src_prefix
    ldy #>msg_src_prefix
    jsr print_ptr
    lda status_flags
    and #FLAG_SRC
    beq print_work_src_no
    lda #<msg_yes
    ldy #>msg_yes
    jsr print_line_ptr
    jmp print_work_bin
print_work_src_no:
    lda #<msg_no
    ldy #>msg_no
    jsr print_line_ptr

print_work_bin:
    lda #<msg_bin_prefix
    ldy #>msg_bin_prefix
    jsr print_ptr
    lda status_flags
    and #FLAG_BIN
    beq print_work_bin_no
    lda #<msg_yes
    ldy #>msg_yes
    jsr print_line_ptr
    jmp print_work_obj
print_work_bin_no:
    lda #<msg_no
    ldy #>msg_no
    jsr print_line_ptr

print_work_obj:
    lda #<msg_obj_prefix
    ldy #>msg_obj_prefix
    jsr print_ptr
    lda status_flags
    and #FLAG_OBJ
    beq print_work_obj_no
    lda #<msg_yes
    ldy #>msg_yes
    jsr print_line_ptr
    jmp print_work_modules
print_work_obj_no:
    lda #<msg_no
    ldy #>msg_no
    jsr print_line_ptr

print_work_modules:
    lda #<msg_modules_prefix
    ldy #>msg_modules_prefix
    jsr print_ptr
    jsr build_count_buffer
    lda #<count_buffer
    ldy #>count_buffer
    jsr print_line_ptr
    rts

build_count_buffer:
    lda module_count
    sta count_work
    ldx #$00
build_count_hundreds_loop:
    lda count_work
    cmp #100
    bcc build_count_hundreds_done
    sec
    sbc #100
    sta count_work
    inx
    bne build_count_hundreds_loop
build_count_hundreds_done:
    stx count_buffer+0
    ldx #$00
build_count_tens_loop:
    lda count_work
    cmp #10
    bcc build_count_tens_done
    sec
    sbc #10
    sta count_work
    inx
    bne build_count_tens_loop
build_count_tens_done:
    stx count_buffer+1
    lda count_work
    sta count_buffer+2

    ldy #$00
    lda count_buffer+0
    beq build_count_skip_hundreds
    clc
    adc #'0'
    sta count_buffer,y
    iny
build_count_skip_hundreds:
    lda count_buffer+1
    bne build_count_emit_tens
    cpy #$00
    beq build_count_skip_tens
build_count_emit_tens:
    clc
    adc #'0'
    sta count_buffer,y
    iny
build_count_skip_tens:
    lda count_buffer+2
    clc
    adc #'0'
    sta count_buffer,y
    iny
    lda status_flags
    and #FLAG_TRUNCATED
    beq build_count_done
    lda #'+'
    sta count_buffer,y
    iny
build_count_done:
    lda #$00
    sta count_buffer,y
    rts
