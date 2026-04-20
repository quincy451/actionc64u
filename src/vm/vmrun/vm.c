#include <stdbool.h>
#include <cpm.h>
#include <stdint.h>
#include <string.h>

#include "../../runtime/reu_backend.h"

#define MAX_AVM_BYTES 4096
#define AVM_HEADER_SIZE 10
#define VM_STACK_SIZE 32
#define VM_LOCAL_COUNT 16

#define OPCODE_PUSH8 0x10
#define OPCODE_PUSH16 0x11
#define OPCODE_STORE 0x12
#define OPCODE_LOAD 0x13
#define OPCODE_ADD 0x14
#define OPCODE_SUB 0x15
#define OPCODE_EQ 0x16
#define OPCODE_NE 0x17
#define OPCODE_JZ 0x18
#define OPCODE_JMP 0x19
#define OPCODE_DUP 0x1A
#define OPCODE_DROP 0x1B
#define OPCODE_LT 0x1C
#define OPCODE_GT 0x1D
#define OPCODE_NATIVE 0x2D
#define OPCODE_CALLN 0x49
#define OPCODE_SETP16 0x61

#define INTR_EXAMPLE_HELLO 0x0000
#define INTR_PRINT 0xFF00
#define INTR_PRINTE 0xFF10
#define INTR_EXIT 0xFF20
#define INTR_PRINTI 0xFF30
#define INTR_PRINTIE 0xFF31
#define INTR_REU_ALLOC 0xFF40
#define INTR_REU_FREE 0xFF41
#define INTR_REU_PEEK8 0xFF42
#define INTR_REU_POKE8 0xFF43
#define INTR_REU_PEEK16 0xFF44
#define INTR_REU_POKE16 0xFF45
#define INTR_CONIN 0xFF50
#define INTR_CONOUT 0xFF51
#define INTR_FOPENR 0xFF60
#define INTR_FCLOSER 0xFF61
#define INTR_FREAD8 0xFF62
#define INTR_FOPENW 0xFF63
#define INTR_FCLOSEW 0xFF64
#define INTR_FWRITE8 0xFF65
#define INTR_FDELETE 0xFF66

static uint8_t avm_data[MAX_AVM_BYTES];
static uint16_t current_string_offset;
static uint16_t vm_stack[VM_STACK_SIZE];
static uint16_t vm_locals[VM_LOCAL_COUNT];
static uint8_t vm_sp;

typedef struct FileReadState
{
    bool open;
    bool eof;
    FCB fcb;
    uint8_t buffer[128];
    uint8_t index;
    uint8_t valid;
} FileReadState;

typedef struct FileWriteState
{
    bool open;
    FCB fcb;
    uint8_t buffer[128];
    uint8_t used;
} FileWriteState;

static FileReadState vm_reader;
static FileWriteState vm_writer;

static void print_cstr(const char* s)
{
    while (*s)
        cpm_conout((uint8_t)*s++);
}

static void crlf(void)
{
    print_cstr("\r\n");
}

static void fatal(const char* message)
{
    print_cstr("vm: ");
    print_cstr(message);
    crlf();
    cpm_warmboot();
}

static void parse_filename(FCB* fcb, const char* name)
{
    memset(fcb, 0, sizeof(*fcb));
    cpm_set_dma(fcb);
    if (!cpm_parse_filename(name))
        fatal("bad filename");
}

static bool fcb_has_filename(const FCB* fcb)
{
    return fcb->f[0] != ' ';
}

static void primary_fcb_to_name(char* out, const char* fallback)
{
    if (!fcb_has_filename(&cpm_fcb))
    {
        strcpy(out, fallback);
        return;
    }

    uint8_t pos = 0;
    for (uint8_t i = 0; i < 8; i++)
    {
        uint8_t ch = cpm_fcb.f[i] & 0x7F;
        if (ch == ' ')
            break;
        if ((ch >= 'A') && (ch <= 'Z'))
            ch = (uint8_t)(ch - 'A' + 'a');
        out[pos++] = (char)ch;
    }

    if (cpm_fcb.f[8] != ' ')
    {
        out[pos++] = '.';
        for (uint8_t i = 8; i < 11; i++)
        {
            uint8_t ch = cpm_fcb.f[i] & 0x7F;
            if (ch == ' ')
                break;
            if ((ch >= 'A') && (ch <= 'Z'))
                ch = (uint8_t)(ch - 'A' + 'a');
            out[pos++] = (char)ch;
        }
    }
    out[pos] = 0;
}

static uint16_t load_u16(const uint8_t* ptr)
{
    return (uint16_t)ptr[0] | ((uint16_t)ptr[1] << 8);
}

static uint16_t round_up_128(uint16_t value)
{
    return (uint16_t)((value + 127u) & 0xFF80u);
}

static uint16_t read_avm_file(const char* filename)
{
    FCB fcb;
    parse_filename(&fcb, filename);
    fcb.ex = 0;
    fcb.cr = 0;
    if (cpm_open_file(&fcb) != CPME_OK)
        fatal("cannot open input");

    uint16_t stored_bytes = 0;
    uint16_t total_bytes = 0;
    uint16_t needed_bytes = 0;

    for (;;)
    {
        cpm_set_dma(cpm_default_dma);
        uint8_t rc = cpm_read_sequential(&fcb);
        if (rc != CPME_OK)
            break;

        if ((uint16_t)(stored_bytes + 128u) > MAX_AVM_BYTES)
            fatal("input too large");

        memcpy(&avm_data[stored_bytes], cpm_default_dma, 128);
        stored_bytes = (uint16_t)(stored_bytes + 128u);

        if ((total_bytes == 0) && (stored_bytes >= AVM_HEADER_SIZE))
        {
            if (memcmp(avm_data, "AVM1", 4) != 0)
                fatal("bad AVM magic");
            if (avm_data[4] != 1)
                fatal("unsupported AVM version");
            total_bytes = (uint16_t)(AVM_HEADER_SIZE + load_u16(&avm_data[5]));
            if (total_bytes > MAX_AVM_BYTES)
                fatal("AVM exceeds buffer");
            if (load_u16(&avm_data[7]) > load_u16(&avm_data[5]))
                fatal("entry offset outside payload");
            if (avm_data[9] != 0)
                fatal("unsupported AVM flags");
            needed_bytes = round_up_128(total_bytes);
        }

        if (needed_bytes && (stored_bytes >= needed_bytes))
            break;
    }

    if (total_bytes == 0)
        fatal("empty or unreadable AVM file");
    return total_bytes;
}

static const char* payload_string_ptr(const uint8_t* payload, uint16_t payload_len, uint16_t offset)
{
    if (offset >= payload_len)
        fatal("string offset outside payload");

    for (uint16_t cursor = offset; cursor < payload_len; cursor++)
    {
        if (payload[cursor] == 0)
            return (const char*)&payload[offset];
    }

    fatal("unterminated payload string");
    return 0;
}

static bool close_reader(void)
{
    if (!vm_reader.open)
        return false;
    vm_reader.open = false;
    vm_reader.eof = true;
    vm_reader.index = 0;
    vm_reader.valid = 0;
    return cpm_close_file(&vm_reader.fcb) == CPME_OK;
}

static bool flush_writer(void)
{
    if (vm_writer.used == 0)
        return true;

    memset(cpm_default_dma, 0, 128);
    memcpy(cpm_default_dma, vm_writer.buffer, vm_writer.used);
    cpm_set_dma(cpm_default_dma);
    if (cpm_write_sequential(&vm_writer.fcb) != CPME_OK)
        return false;

    vm_writer.used = 0;
    return true;
}

static bool close_writer(void)
{
    bool ok;

    if (!vm_writer.open)
        return false;

    ok = flush_writer();
    if (cpm_close_file(&vm_writer.fcb) != CPME_OK)
        ok = false;

    vm_writer.open = false;
    vm_writer.used = 0;
    return ok;
}

static bool open_reader(const uint8_t* payload, uint16_t payload_len, uint16_t offset)
{
    const char* filename = payload_string_ptr(payload, payload_len, offset);

    if (vm_reader.open)
        (void)close_reader();

    parse_filename(&vm_reader.fcb, filename);
    vm_reader.fcb.ex = 0;
    vm_reader.fcb.cr = 0;
    if (cpm_open_file(&vm_reader.fcb) != CPME_OK)
    {
        vm_reader.open = false;
        vm_reader.eof = true;
        vm_reader.index = 0;
        vm_reader.valid = 0;
        return false;
    }

    vm_reader.open = true;
    vm_reader.eof = false;
    vm_reader.index = 0;
    vm_reader.valid = 0;
    return true;
}

static bool open_writer(const uint8_t* payload, uint16_t payload_len, uint16_t offset)
{
    const char* filename = payload_string_ptr(payload, payload_len, offset);

    if (vm_writer.open)
        (void)close_writer();

    parse_filename(&vm_writer.fcb, filename);
    cpm_delete_file(&vm_writer.fcb);
    if (cpm_make_file(&vm_writer.fcb) != CPME_OK)
    {
        vm_writer.open = false;
        vm_writer.used = 0;
        return false;
    }

    vm_writer.open = true;
    vm_writer.used = 0;
    return true;
}

static uint16_t read_text_byte(void)
{
    uint8_t value;

    if (!vm_reader.open || vm_reader.eof)
        return 0xFFFFu;

    while (vm_reader.index >= vm_reader.valid)
    {
        cpm_set_dma(cpm_default_dma);
        if (cpm_read_sequential(&vm_reader.fcb) != CPME_OK)
        {
            vm_reader.eof = true;
            return 0xFFFFu;
        }
        memcpy(vm_reader.buffer, cpm_default_dma, 128);
        vm_reader.index = 0;
        vm_reader.valid = 128;
    }

    value = vm_reader.buffer[vm_reader.index++];
    if (value == 0x1Au)
    {
        vm_reader.eof = true;
        return 0xFFFFu;
    }
    return value;
}

static void write_text_byte(uint8_t value)
{
    if (!vm_writer.open)
        fatal("write channel not open");

    vm_writer.buffer[vm_writer.used++] = value;
    if (vm_writer.used < sizeof(vm_writer.buffer))
        return;

    if (!flush_writer())
        fatal("write failed");
}

static void print_payload_string(const uint8_t* payload, uint16_t payload_len, uint16_t offset, bool newline)
{
    if (offset >= payload_len)
        fatal("string offset outside payload");

    while (offset < payload_len)
    {
        uint8_t ch = payload[offset++];
        if (ch == 0)
        {
            if (newline)
                crlf();
            return;
        }
        cpm_conout(ch);
    }

    fatal("unterminated payload string");
}

static void print_i16(int16_t value)
{
    char buf[7];
    uint8_t pos = 0;
    uint16_t magnitude;

    if (value < 0)
    {
        cpm_conout('-');
        magnitude = (uint16_t)(0u - (uint16_t)value);
    }
    else
    {
        magnitude = (uint16_t)value;
    }

    do
    {
        buf[pos++] = (char)('0' + (magnitude % 10u));
        magnitude /= 10u;
    } while (magnitude);

    while (pos)
        cpm_conout((uint8_t)buf[--pos]);
}

static void stack_push(uint16_t value)
{
    if (vm_sp >= VM_STACK_SIZE)
        fatal("stack overflow");
    vm_stack[vm_sp++] = value;
}

static uint16_t stack_pop(void)
{
    if (vm_sp == 0)
        fatal("stack underflow");
    return vm_stack[--vm_sp];
}

static uint16_t stack_peek(void)
{
    if (vm_sp == 0)
        fatal("stack underflow");
    return vm_stack[vm_sp - 1];
}

static const uint8_t* resolve_target(const uint8_t* payload, uint16_t payload_len, uint16_t target)
{
    if (target > payload_len)
        fatal("jump target outside payload");
    return payload + target;
}

static void run_intrinsic(uint16_t target, const uint8_t* payload, uint16_t payload_len)
{
    uint16_t handle_word;
    uint16_t offset;
    uint16_t value;
    uint8_t byte_value;
    uint16_t word_value;
    ReuHandle handle;

    if (target == INTR_PRINT)
    {
        print_payload_string(payload, payload_len, current_string_offset, false);
        return;
    }
    if (target == INTR_PRINTE)
    {
        print_payload_string(payload, payload_len, current_string_offset, true);
        return;
    }
    if (target == INTR_EXAMPLE_HELLO)
    {
        print_cstr("HELLO FROM AVM FILE");
        crlf();
        return;
    }
    if (target == INTR_EXIT)
        return;
    if (target == INTR_PRINTI)
    {
        print_i16((int16_t)stack_pop());
        return;
    }
    if (target == INTR_PRINTIE)
    {
        print_i16((int16_t)stack_pop());
        crlf();
        return;
    }
    if (target == INTR_REU_ALLOC)
    {
        value = stack_pop();
        if (!reu_alloc(value, &handle))
            fatal("reu alloc failed");
        stack_push(handle);
        return;
    }
    if (target == INTR_REU_FREE)
    {
        handle_word = stack_pop();
        if (!reu_free((ReuHandle)handle_word))
            fatal("reu free failed");
        return;
    }
    if (target == INTR_REU_PEEK8)
    {
        offset = stack_pop();
        handle_word = stack_pop();
        if (!reu_peek8((ReuHandle)handle_word, offset, &byte_value))
            fatal("reu peek8 failed");
        stack_push(byte_value);
        return;
    }
    if (target == INTR_REU_POKE8)
    {
        value = stack_pop();
        offset = stack_pop();
        handle_word = stack_pop();
        if (!reu_poke8((ReuHandle)handle_word, offset, (uint8_t)value))
            fatal("reu poke8 failed");
        return;
    }
    if (target == INTR_REU_PEEK16)
    {
        offset = stack_pop();
        handle_word = stack_pop();
        if (!reu_peek16((ReuHandle)handle_word, offset, &word_value))
            fatal("reu peek16 failed");
        stack_push(word_value);
        return;
    }
    if (target == INTR_REU_POKE16)
    {
        value = stack_pop();
        offset = stack_pop();
        handle_word = stack_pop();
        if (!reu_poke16((ReuHandle)handle_word, offset, value))
            fatal("reu poke16 failed");
        return;
    }
    if (target == INTR_CONIN)
    {
        stack_push(cpm_conin());
        return;
    }
    if (target == INTR_CONOUT)
    {
        cpm_conout((uint8_t)stack_pop());
        return;
    }
    if (target == INTR_FOPENR)
    {
        offset = stack_pop();
        stack_push(open_reader(payload, payload_len, offset) ? 1u : 0u);
        return;
    }
    if (target == INTR_FCLOSER)
    {
        stack_push(close_reader() ? 1u : 0u);
        return;
    }
    if (target == INTR_FREAD8)
    {
        stack_push(read_text_byte());
        return;
    }
    if (target == INTR_FOPENW)
    {
        offset = stack_pop();
        stack_push(open_writer(payload, payload_len, offset) ? 1u : 0u);
        return;
    }
    if (target == INTR_FCLOSEW)
    {
        stack_push(close_writer() ? 1u : 0u);
        return;
    }
    if (target == INTR_FWRITE8)
    {
        write_text_byte((uint8_t)stack_pop());
        return;
    }
    if (target == INTR_FDELETE)
    {
        FCB fcb;
        offset = stack_pop();
        parse_filename(&fcb, payload_string_ptr(payload, payload_len, offset));
        stack_push(cpm_delete_file(&fcb) == CPME_OK ? 1u : 0u);
        return;
    }

    fatal("unknown intrinsic");
}

int vm_run_filename(const char* filename)
{
    reu_backend_reset();
    read_avm_file(filename);
    uint16_t payload_len = load_u16(&avm_data[5]);
    uint16_t entry_offset = load_u16(&avm_data[7]);
    const uint8_t* payload = &avm_data[AVM_HEADER_SIZE];
    const uint8_t* ip = payload + entry_offset;
    const uint8_t* end = payload + payload_len;

    current_string_offset = 0;
    vm_sp = 0;
    memset(vm_locals, 0, sizeof(vm_locals));
    memset(&vm_reader, 0, sizeof(vm_reader));
    memset(&vm_writer, 0, sizeof(vm_writer));

    while (ip < end)
    {
        uint8_t opcode = *ip++;
        uint8_t slot;
        uint16_t lhs;
        uint16_t rhs;
        uint16_t target;

        if (opcode == OPCODE_PUSH8)
        {
            if (ip >= end)
                fatal("truncated push8");
            stack_push(*ip++);
            continue;
        }

        if (opcode == OPCODE_PUSH16)
        {
            if ((uint16_t)(end - ip) < 2)
                fatal("truncated push16");
            stack_push(load_u16(ip));
            ip += 2;
            continue;
        }

        if (opcode == OPCODE_STORE)
        {
            if (ip >= end)
                fatal("truncated store");
            slot = *ip++;
            if (slot >= VM_LOCAL_COUNT)
                fatal("local index out of range");
            vm_locals[slot] = stack_pop();
            continue;
        }

        if (opcode == OPCODE_LOAD)
        {
            if (ip >= end)
                fatal("truncated load");
            slot = *ip++;
            if (slot >= VM_LOCAL_COUNT)
                fatal("local index out of range");
            stack_push(vm_locals[slot]);
            continue;
        }

        if (opcode == OPCODE_ADD)
        {
            rhs = stack_pop();
            lhs = stack_pop();
            stack_push((uint16_t)(lhs + rhs));
            continue;
        }

        if (opcode == OPCODE_SUB)
        {
            rhs = stack_pop();
            lhs = stack_pop();
            stack_push((uint16_t)(lhs - rhs));
            continue;
        }

        if (opcode == OPCODE_EQ)
        {
            rhs = stack_pop();
            lhs = stack_pop();
            stack_push(lhs == rhs ? 1u : 0u);
            continue;
        }

        if (opcode == OPCODE_NE)
        {
            rhs = stack_pop();
            lhs = stack_pop();
            stack_push(lhs != rhs ? 1u : 0u);
            continue;
        }

        if (opcode == OPCODE_LT)
        {
            rhs = stack_pop();
            lhs = stack_pop();
            stack_push(((int16_t)lhs < (int16_t)rhs) ? 1u : 0u);
            continue;
        }

        if (opcode == OPCODE_GT)
        {
            rhs = stack_pop();
            lhs = stack_pop();
            stack_push(((int16_t)lhs > (int16_t)rhs) ? 1u : 0u);
            continue;
        }

        if (opcode == OPCODE_DUP)
        {
            stack_push(stack_peek());
            continue;
        }

        if (opcode == OPCODE_DROP)
        {
            (void)stack_pop();
            continue;
        }

        if (opcode == OPCODE_JZ)
        {
            if ((uint16_t)(end - ip) < 2)
                fatal("truncated jz");
            target = load_u16(ip);
            ip += 2;
            if (stack_pop() == 0)
                ip = resolve_target(payload, payload_len, target);
            continue;
        }

        if (opcode == OPCODE_JMP)
        {
            if ((uint16_t)(end - ip) < 2)
                fatal("truncated jmp");
            target = load_u16(ip);
            ip = resolve_target(payload, payload_len, target);
            continue;
        }

        if (opcode == OPCODE_SETP16)
        {
            if ((uint16_t)(end - ip) < 2)
                fatal("truncated setp16");
            current_string_offset = load_u16(ip);
            ip += 2;
            continue;
        }

        if (opcode == OPCODE_CALLN)
        {
            if ((uint16_t)(end - ip) < 2)
                fatal("truncated calln");
            target = load_u16(ip);
            ip += 2;
            if (target == INTR_EXIT)
            {
                (void)close_reader();
                (void)close_writer();
                return 0;
            }
            run_intrinsic(target, payload, payload_len);
            continue;
        }

        if (opcode == OPCODE_NATIVE)
            return 0;

        fatal("unknown opcode");
    }

    (void)close_reader();
    (void)close_writer();
    return 0;
}

#ifndef VM_LIBRARY
int main(void)
{
    char filename[13];
    primary_fcb_to_name(filename, "main.avm");
    return vm_run_filename(filename);
}
#endif
