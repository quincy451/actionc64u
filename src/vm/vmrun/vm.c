#include <stdbool.h>
#include <cpm.h>
#include <stdint.h>
#include <string.h>

#include "../../runtime/reu_backend.h"

#define MAX_AVM_BYTES 4096
#define AVM_HEADER_SIZE 10
#define OPCODE_CALLN 0x49
#define OPCODE_NATIVE 0x2d
#define OPCODE_SETP16 0x61
#define INTR_EXAMPLE_HELLO 0x0000
#define INTR_PRINT 0xff00
#define INTR_PRINTE 0xff10
#define INTR_EXIT 0xff20

static uint8_t avm_data[MAX_AVM_BYTES];
static uint8_t current_string_offset_lo;
static uint8_t current_string_offset_hi;

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
        uint8_t ch = cpm_fcb.f[i] & 0x7f;
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
            uint8_t ch = cpm_fcb.f[i] & 0x7f;
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
    return (uint16_t)((value + 127u) & 0xff80u);
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

int vm_run_filename(const char* filename)
{
    reu_backend_reset();
    read_avm_file(filename);
    uint16_t payload_len = load_u16(&avm_data[5]);
    uint16_t entry_offset = load_u16(&avm_data[7]);
    const uint8_t* payload = &avm_data[AVM_HEADER_SIZE];
    const uint8_t* ip = payload + entry_offset;
    const uint8_t* end = payload + payload_len;

    current_string_offset_lo = 0;
    current_string_offset_hi = 0;

    while (ip < end)
    {
        uint8_t opcode = *ip++;
        if (opcode == OPCODE_SETP16)
        {
            if ((uint16_t)(end - ip) < 2)
                fatal("truncated setp16");
            current_string_offset_lo = *ip++;
            current_string_offset_hi = *ip++;
            continue;
        }

        if (opcode == OPCODE_CALLN)
        {
            if ((uint16_t)(end - ip) < 2)
                fatal("truncated calln");
            uint16_t target = load_u16(ip);
            ip += 2;
            if (target == INTR_PRINT)
            {
                uint16_t string_offset = (uint16_t)current_string_offset_lo | ((uint16_t)current_string_offset_hi << 8);
                print_payload_string(payload, payload_len, string_offset, false);
                continue;
            }
            if (target == INTR_PRINTE)
            {
                uint16_t string_offset = (uint16_t)current_string_offset_lo | ((uint16_t)current_string_offset_hi << 8);
                print_payload_string(payload, payload_len, string_offset, true);
                continue;
            }
            if (target == INTR_EXAMPLE_HELLO)
            {
                print_cstr("HELLO FROM AVM FILE");
                crlf();
                continue;
            }
            if (target == INTR_EXIT)
                return 0;
            fatal("unknown intrinsic");
        }

        if (opcode == OPCODE_NATIVE)
            return 0;

        fatal("unknown opcode");
    }

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
