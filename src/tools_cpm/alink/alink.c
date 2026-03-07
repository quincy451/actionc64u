#include <stdbool.h>
#include <cpm.h>
#include <stdint.h>
#include <string.h>

#define MAX_TEXT_BYTES 2048
#define MAX_AVM_BYTES 2048
#define MAX_OBJECT_PAYLOAD 1536
#define MAX_MODULES 12
#define MAX_EXPORTS 8
#define MAX_IMPORTS 8
#define MAX_SYMBOL_LEN 24
#define AVM_HEADER_SIZE 10

typedef struct {
    char name[MAX_SYMBOL_LEN];
    uint16_t offset;
} Symbol;

typedef struct {
    char module_name[MAX_SYMBOL_LEN];
    uint16_t entry_offset;
    uint16_t payload_len;
    uint8_t payload[MAX_OBJECT_PAYLOAD];
    uint8_t export_count;
    Symbol exports[MAX_EXPORTS];
    uint8_t import_count;
    char imports[MAX_IMPORTS][MAX_SYMBOL_LEN];
} AvoObject;

typedef struct {
    char filename[13];
    char module_name[MAX_SYMBOL_LEN];
    uint16_t base_offset;
    uint16_t payload_len;
    uint8_t export_count;
    Symbol exports[MAX_EXPORTS];
} IncludedModule;

static char text_buffer[MAX_TEXT_BYTES];
static uint8_t avm_buffer[MAX_AVM_BYTES];
static IncludedModule included_modules[MAX_MODULES];
static uint8_t included_count;
static uint16_t linked_payload_len;
static uint16_t map_len;
static uint16_t main_entry_offset;

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
    print_cstr("alink: ");
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

static void replace_extension(const char* source_name, const char* ext, char* out)
{
    uint8_t pos = 0;
    while (source_name[pos] && source_name[pos] != '.' && pos < 8)
    {
        out[pos] = source_name[pos];
        pos++;
    }
    out[pos] = 0;
    strcat(out, ext);
}

static bool strings_equal(const char* a, const char* b)
{
    return strcmp(a, b) == 0;
}

static bool read_text_file(const char* filename, char* out, uint16_t max_len)
{
    FCB fcb;
    uint16_t used = 0;

    parse_filename(&fcb, filename);
    fcb.ex = 0;
    fcb.cr = 0;
    if (cpm_open_file(&fcb) != CPME_OK)
        return false;

    for (;;)
    {
        cpm_set_dma(cpm_default_dma);
        if (cpm_read_sequential(&fcb) != CPME_OK)
            break;
        if ((uint16_t)(used + 128u) >= max_len)
            fatal("input too large");
        memcpy(&out[used], cpm_default_dma, 128);
        used = (uint16_t)(used + 128u);
    }
    cpm_close_file(&fcb);

    while (used && ((out[used - 1] == 0) || (out[used - 1] == 0x1a)))
        used--;
    out[used] = 0;
    return true;
}

static void write_file_common(FCB* fcb, const char* filename)
{
    parse_filename(fcb, filename);
    cpm_delete_file(fcb);
    fcb->ex = 0;
    fcb->cr = 0;
    if (cpm_make_file(fcb) != CPME_OK)
        fatal("cannot create output");
}

static void write_binary_file(const char* filename, const uint8_t* data, uint16_t len)
{
    FCB fcb;
    uint16_t offset = 0;

    write_file_common(&fcb, filename);
    while (offset < len)
    {
        uint8_t chunk = 128;
        if ((uint16_t)(len - offset) < 128u)
            chunk = (uint8_t)(len - offset);
        memset(cpm_default_dma, 0, 128);
        memcpy(cpm_default_dma, &data[offset], chunk);
        cpm_set_dma(cpm_default_dma);
        if (cpm_write_sequential(&fcb) != CPME_OK)
            fatal("write failed");
        offset = (uint16_t)(offset + chunk);
    }
    if (cpm_close_file(&fcb) != CPME_OK)
        fatal("close failed");
}

static void write_text_file(const char* filename, const char* data, uint16_t len)
{
    write_binary_file(filename, (const uint8_t*)data, len);
}

static void skip_newline(char** cursor)
{
    if (**cursor == '\r')
        (*cursor)++;
    if (**cursor == '\n')
        (*cursor)++;
}

static void expect_literal(char** cursor, const char* literal)
{
    uint8_t len = (uint8_t)strlen(literal);
    if (memcmp(*cursor, literal, len) != 0)
        fatal("bad AVO format");
    *cursor += len;
}

static uint16_t parse_decimal(char** cursor)
{
    uint16_t value = 0;
    if ((**cursor < '0') || (**cursor > '9'))
        fatal("bad decimal");
    while ((**cursor >= '0') && (**cursor <= '9'))
    {
        value = (uint16_t)(value * 10u + (uint16_t)(**cursor - '0'));
        (*cursor)++;
    }
    return value;
}

static void parse_symbol_string(char** cursor, char* out)
{
    uint8_t len = 0;
    while (**cursor && (**cursor != '"'))
    {
        if (len + 1 >= MAX_SYMBOL_LEN)
            fatal("symbol too long");
        out[len++] = **cursor;
        (*cursor)++;
    }
    if (**cursor != '"')
        fatal("unterminated string");
    out[len] = 0;
}

static uint8_t hex_value(uint8_t ch)
{
    if ((ch >= '0') && (ch <= '9'))
        return (uint8_t)(ch - '0');
    if ((ch >= 'a') && (ch <= 'f'))
        return (uint8_t)(10 + ch - 'a');
    fatal("bad hex");
    return 0;
}

static void parse_exports(char** cursor, AvoObject* obj)
{
    obj->export_count = 0;
    if (**cursor == ']')
    {
        (*cursor)++;
        return;
    }

    for (;;)
    {
        if (obj->export_count >= MAX_EXPORTS)
            fatal("too many exports");
        expect_literal(cursor, "[\"");
        parse_symbol_string(cursor, obj->exports[obj->export_count].name);
        expect_literal(cursor, "\",");
        obj->exports[obj->export_count].offset = parse_decimal(cursor);
        expect_literal(cursor, "]");
        obj->export_count++;
        if (**cursor == ',')
        {
            (*cursor)++;
            continue;
        }
        if (**cursor != ']')
            fatal("bad exports");
        (*cursor)++;
        return;
    }
}

static void parse_imports(char** cursor, AvoObject* obj)
{
    obj->import_count = 0;
    if (**cursor == ']')
    {
        (*cursor)++;
        return;
    }

    for (;;)
    {
        if (obj->import_count >= MAX_IMPORTS)
            fatal("too many imports");
        expect_literal(cursor, "\"");
        parse_symbol_string(cursor, obj->imports[obj->import_count]);
        expect_literal(cursor, "\"");
        obj->import_count++;
        if (**cursor == ',')
        {
            (*cursor)++;
            continue;
        }
        if (**cursor != ']')
            fatal("bad imports");
        (*cursor)++;
        return;
    }
}

static void parse_payload_hex(char** cursor, AvoObject* obj)
{
    uint16_t len = 0;
    while (**cursor && (**cursor != '"'))
    {
        uint8_t hi;
        uint8_t lo;
        if (!(*cursor)[1])
            fatal("odd payload hex");
        if (len >= MAX_OBJECT_PAYLOAD)
            fatal("payload too large");
        hi = hex_value((uint8_t)(*cursor)[0]);
        lo = hex_value((uint8_t)(*cursor)[1]);
        obj->payload[len++] = (uint8_t)((hi << 4) | lo);
        *cursor += 2;
    }
    obj->payload_len = len;
}

static void parse_avo_text(char* text, AvoObject* obj)
{
    char* cursor = text;

    memset(obj, 0, sizeof(*obj));
    expect_literal(&cursor, "AVO1");
    skip_newline(&cursor);
    expect_literal(&cursor, "{\"entry_offset\":");
    obj->entry_offset = parse_decimal(&cursor);
    expect_literal(&cursor, ",\"exports\":[");
    parse_exports(&cursor, obj);
    expect_literal(&cursor, ",\"imports\":[");
    parse_imports(&cursor, obj);
    expect_literal(&cursor, ",\"module\":\"");
    parse_symbol_string(&cursor, obj->module_name);
    expect_literal(&cursor, "\"");
    if (memcmp(cursor, ",\"overlays\":[", 13) == 0)
    {
        cursor += 13;
        if (*cursor != ']')
            fatal("overlays unsupported");
        cursor++;
    }
    expect_literal(&cursor, ",\"payload_hex\":\"");
    parse_payload_hex(&cursor, obj);
    expect_literal(&cursor, "\",\"version\":1}");
}

static void load_avo(const char* filename, AvoObject* obj)
{
    if (!read_text_file(filename, text_buffer, sizeof(text_buffer) - 1u))
        fatal("cannot open object");
    parse_avo_text(text_buffer, obj);
}

static bool object_exports(const AvoObject* obj, const char* symbol)
{
    for (uint8_t i = 0; i < obj->export_count; i++)
    {
        if (strings_equal(obj->exports[i].name, symbol))
            return true;
    }
    return false;
}

static int8_t find_included_provider(const char* symbol)
{
    for (uint8_t i = 0; i < included_count; i++)
    {
        for (uint8_t j = 0; j < included_modules[i].export_count; j++)
        {
            if (strings_equal(included_modules[i].exports[j].name, symbol))
                return (int8_t)i;
        }
    }
    return -1;
}

static bool module_already_included(const char* module_name)
{
    for (uint8_t i = 0; i < included_count; i++)
    {
        if (strings_equal(included_modules[i].module_name, module_name))
            return true;
    }
    return false;
}

static void copy_module_metadata(IncludedModule* dest, const AvoObject* src, const char* filename, uint16_t base_offset)
{
    memset(dest, 0, sizeof(*dest));
    strcpy(dest->filename, filename);
    strcpy(dest->module_name, src->module_name);
    dest->base_offset = base_offset;
    dest->payload_len = src->payload_len;
    dest->export_count = src->export_count;
    memcpy(dest->exports, src->exports, sizeof(src->exports));
}

static void include_module(const AvoObject* obj, const char* filename)
{
    if (included_count >= MAX_MODULES)
        fatal("too many modules");
    if ((uint16_t)(linked_payload_len + obj->payload_len) > (MAX_AVM_BYTES - AVM_HEADER_SIZE))
        fatal("linked payload too large");
    memcpy(&avm_buffer[AVM_HEADER_SIZE + linked_payload_len], obj->payload, obj->payload_len);
    copy_module_metadata(&included_modules[included_count], obj, filename, linked_payload_len);
    linked_payload_len = (uint16_t)(linked_payload_len + obj->payload_len);
    included_count++;
}

static void fcb_match_to_name(const FCB* fcb, char* out)
{
    uint8_t pos = 0;
    for (uint8_t i = 0; i < 8; i++)
    {
        uint8_t ch = fcb->f[i] & 0x7f;
        if (ch == ' ')
            break;
        if ((ch >= 'A') && (ch <= 'Z'))
            ch = (uint8_t)(ch - 'A' + 'a');
        out[pos++] = (char)ch;
    }
    if (fcb->f[8] != ' ')
    {
        out[pos++] = '.';
        for (uint8_t i = 8; i < 11; i++)
        {
            uint8_t ch = fcb->f[i] & 0x7f;
            if (ch == ' ')
                break;
            if ((ch >= 'A') && (ch <= 'Z'))
                ch = (uint8_t)(ch - 'A' + 'a');
            out[pos++] = (char)ch;
        }
    }
    out[pos] = 0;
}

static bool load_provider_for_symbol(const char* symbol, const char* main_filename, AvoObject* provider, char* provider_filename)
{
    FCB search;
    uint8_t last_name[11];
    bool have_last = false;
    bool found = false;
    AvoObject candidate;

    parse_filename(&search, "*.avo");
    search.ex = '?';
    cpm_set_dma(cpm_default_dma);

    uint8_t result = cpm_findfirst(&search);
    while (result != 0xff)
    {
        FCB* match = ((FCB*)cpm_default_dma) + result;
        if (!have_last || (memcmp(last_name, match->f, sizeof(last_name)) != 0))
        {
            char filename[13];
            memcpy(last_name, match->f, sizeof(last_name));
            have_last = true;
            fcb_match_to_name(match, filename);
            if (!strings_equal(filename, main_filename))
            {
                load_avo(filename, &candidate);
                if (object_exports(&candidate, symbol))
                {
                    if (found)
                        fatal("duplicate export");
                    *provider = candidate;
                    strcpy(provider_filename, filename);
                    found = true;
                }
            }
        }
        result = cpm_findnext(&search);
    }

    return found;
}

static bool pending_contains(char pending[][MAX_SYMBOL_LEN], uint16_t pending_count, const char* symbol)
{
    for (uint8_t i = 0; i < pending_count; i++)
    {
        if (strings_equal(pending[i], symbol))
            return true;
    }
    return false;
}

static void add_pending_imports(char pending[][MAX_SYMBOL_LEN], uint16_t* pending_count, const AvoObject* obj)
{
    for (uint8_t i = 0; i < obj->import_count; i++)
    {
        if ((find_included_provider(obj->imports[i]) < 0) &&
            !pending_contains(pending, *pending_count, obj->imports[i]))
        {
            if (*pending_count >= MAX_MODULES * MAX_IMPORTS)
                fatal("too many pending imports");
            strcpy(pending[*pending_count], obj->imports[i]);
            (*pending_count)++;
        }
    }
}

static int8_t pick_pending_symbol(char pending[][MAX_SYMBOL_LEN], uint16_t* pending_count, char* out)
{
    if (*pending_count == 0)
        return -1;
    uint8_t best = 0;
    for (uint8_t i = 1; i < *pending_count; i++)
    {
        if (strcmp(pending[i], pending[best]) < 0)
            best = i;
    }
    strcpy(out, pending[best]);
    for (uint8_t i = best + 1; i < *pending_count; i++)
        strcpy(pending[i - 1], pending[i]);
    (*pending_count)--;
    return 0;
}

static void append_map_text(const char* text)
{
    uint16_t len = (uint16_t)strlen(text);
    if ((uint16_t)(map_len + len) >= sizeof(text_buffer))
        fatal("map too large");
    memcpy(&text_buffer[map_len], text, len);
    map_len = (uint16_t)(map_len + len);
    text_buffer[map_len] = 0;
}

static void append_map_hex16(uint16_t value)
{
    static const char HEX[] = "0123456789abcdef";
    char text[5];
    text[0] = HEX[(value >> 12) & 0x0f];
    text[1] = HEX[(value >> 8) & 0x0f];
    text[2] = HEX[(value >> 4) & 0x0f];
    text[3] = HEX[value & 0x0f];
    text[4] = 0;
    append_map_text(text);
}

static void append_map_dec(uint16_t value)
{
    char digits[6];
    uint8_t len = 0;
    if (value == 0)
    {
        append_map_text("0");
        return;
    }
    while (value)
    {
        digits[len++] = (char)('0' + (value % 10u));
        value /= 10u;
    }
    while (len)
    {
        char text[2];
        text[0] = digits[--len];
        text[1] = 0;
        append_map_text(text);
    }
}

static void build_map(void)
{
    map_len = 0;
    append_map_text("# ActionC64U Link Map\n\n");
    append_map_text("entry main @ 0x");
    append_map_hex16(main_entry_offset);
    append_map_text("\n\nincluded modules:\n");
    for (uint8_t i = 0; i < included_count; i++)
    {
        append_map_text("- ");
        append_map_text(included_modules[i].module_name);
        append_map_text(" path=");
        append_map_text(included_modules[i].filename);
        append_map_text(" base=0x");
        append_map_hex16(included_modules[i].base_offset);
        append_map_text(" size=");
        append_map_dec(included_modules[i].payload_len);
        append_map_text("\n");
    }
    append_map_text("\nexports:\n");
    for (uint8_t i = 0; i < included_count; i++)
    {
        for (uint8_t j = 0; j < included_modules[i].export_count; j++)
        {
            append_map_text("- ");
            append_map_text(included_modules[i].exports[j].name);
            append_map_text(" = 0x");
            append_map_hex16((uint16_t)(included_modules[i].base_offset + included_modules[i].exports[j].offset));
            append_map_text(" (");
            append_map_text(included_modules[i].module_name);
            append_map_text(")\n");
        }
    }
}

static void link_objects(const char* main_filename, const char* avm_filename, const char* map_filename)
{
    AvoObject main_obj;
    char pending[MAX_MODULES * MAX_IMPORTS][MAX_SYMBOL_LEN];
    uint16_t pending_count = 0;
    char symbol[MAX_SYMBOL_LEN];

    included_count = 0;
    linked_payload_len = 0;
    load_avo(main_filename, &main_obj);
    main_entry_offset = main_obj.entry_offset;
    include_module(&main_obj, main_filename);
    add_pending_imports(pending, &pending_count, &main_obj);

    while (pick_pending_symbol(pending, &pending_count, symbol) == 0)
    {
        AvoObject provider;
        char provider_filename[13];
        if (find_included_provider(symbol) >= 0)
            continue;
        if (!load_provider_for_symbol(symbol, main_filename, &provider, provider_filename))
            fatal("unresolved symbol");
        if (!module_already_included(provider.module_name))
        {
            include_module(&provider, provider_filename);
            add_pending_imports(pending, &pending_count, &provider);
        }
    }

    memcpy(avm_buffer, "AVM1", 4);
    avm_buffer[4] = 1;
    avm_buffer[5] = (uint8_t)(linked_payload_len & 0xff);
    avm_buffer[6] = (uint8_t)(linked_payload_len >> 8);
    avm_buffer[7] = (uint8_t)(main_obj.entry_offset & 0xff);
    avm_buffer[8] = (uint8_t)(main_obj.entry_offset >> 8);
    avm_buffer[9] = 0;
    write_binary_file(avm_filename, avm_buffer, (uint16_t)(AVM_HEADER_SIZE + linked_payload_len));

    build_map();
    write_text_file(map_filename, text_buffer, map_len);
}

int main(void)
{
    char main_filename[13];
    char avm_filename[13];
    char map_filename[13];

    primary_fcb_to_name(main_filename, "main.avo");
    replace_extension(main_filename, ".avm", avm_filename);
    replace_extension(main_filename, ".map", map_filename);
    link_objects(main_filename, avm_filename, map_filename);
    print_cstr("wrote ");
    print_cstr(avm_filename);
    crlf();
    print_cstr("wrote ");
    print_cstr(map_filename);
    crlf();
    return 0;
}
