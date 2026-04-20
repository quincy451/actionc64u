#include <stdbool.h>
#include <cpm.h>
#include <stdint.h>
#include <string.h>

#include "../../runtime/reu_backend.h"

#define MAX_SOURCE_BYTES 1536
#define MAX_LINES 96
#define MAX_ACTIONS 64
#define MAX_TEXT_POOL 1024
#define MAX_AVM_BYTES 2048
#define MAX_SYMBOLS 32
#define MAX_REU_ARRAYS 4
#define MAX_OVERLAYS 4
#define MAX_OVERLAY_PAYLOAD 48
#define MAX_OVERLAY_BLOB 256
#define MAX_IDENT_LEN 31
#define MAX_TOKEN_TEXT 255
#define MAX_MODULES 20
#define MAX_MODULE_IMPORTS 2
#define MAX_MODULE_PAYLOAD 48
#define MAX_MANIFEST_BYTES 2048
#define MAX_MAP_BYTES 1024
#define MAX_ROOT_IMPORTS 16
#define OPCODE_CALLN 0x49
#define OPCODE_SETP16 0x61
#define INTR_PRINT 0xff00
#define INTR_PRINTE 0xff10
#define INTR_EXIT 0xff20
#define AVM_HEADER_SIZE 10

typedef enum {
    TYPE_BYTE,
    TYPE_CARD,
    TYPE_INT,
    TYPE_REAL,
} ValueType;

typedef struct {
    uint16_t text_offset;
    bool newline;
} PrintAction;

typedef struct {
    uint16_t line_no;
    char* text;
} SourceLine;

typedef struct {
    char name[MAX_IDENT_LEN + 1];
    ValueType type;
    int32_t int_value;
    float real_value;
    bool assigned;
} Symbol;

typedef struct {
    ValueType type;
    int32_t int_value;
    float real_value;
} Value;

typedef struct {
    char name[MAX_IDENT_LEN + 1];
    ReuHandle handle;
    uint32_t length;
} ReuArray;

typedef struct {
    char name[MAX_IDENT_LEN + 1];
    uint16_t start_index;
    uint16_t end_index;
} OverlayBlock;

typedef struct {
    bool loaded;
    char filename[13];
    char module_name[MAX_IDENT_LEN + 1];
    uint8_t import_count;
    char imports[MAX_MODULE_IMPORTS][MAX_IDENT_LEN + 1];
    uint8_t payload_len;
    uint8_t payload[MAX_MODULE_PAYLOAD];
} DiskModule;

typedef enum {
    TOK_EOF,
    TOK_IDENT,
    TOK_NUMBER,
    TOK_STRING,
    TOK_LPAREN,
    TOK_RPAREN,
    TOK_COMMA,
    TOK_PLUS,
    TOK_MINUS,
    TOK_STAR,
    TOK_SLASH,
    TOK_EQ,
    TOK_NE,
    TOK_LT,
    TOK_LE,
    TOK_GT,
    TOK_GE,
    TOK_MODULE,
    TOK_PROC,
    TOK_RETURN,
    TOK_PRINT,
    TOK_PRINTE,
    TOK_PRINTI,
    TOK_PRINTIE,
    TOK_PRINTR,
    TOK_PRINTRE,
    TOK_IF,
    TOK_THEN,
    TOK_FI,
    TOK_REU,
    TOK_REUPOKE8,
    TOK_REUPOKE16,
    TOK_REUPEEK8,
    TOK_REUPEEK16,
    TOK_OVERLAY,
    TOK_ENDOVERLAY,
    TOK_OVERLAYCALL,
    TOK_BYTE,
    TOK_CARD,
    TOK_INT,
    TOK_REAL,
} TokenKind;

typedef struct {
    TokenKind kind;
    char text[MAX_TOKEN_TEXT + 1];
    int32_t number;
    float real_number;
    bool is_real;
} Token;

typedef struct {
    const char* cursor;
    uint16_t line_no;
    Token token;
} Lexer;

typedef struct {
    const char* name;
    TokenKind kind;
} Keyword;

static void add_root_import(const char* name);

static char source_buffer[MAX_SOURCE_BYTES];
static SourceLine lines[MAX_LINES];
static uint16_t line_count;
static PrintAction actions[MAX_ACTIONS];
static uint16_t action_count;
static char text_pool[MAX_TEXT_POOL];
static uint16_t text_pool_len;
static uint8_t avm_buffer[MAX_AVM_BYTES];
static Symbol symbols[MAX_SYMBOLS];
static uint16_t symbol_count;
static ReuArray reu_arrays[MAX_REU_ARRAYS];
static uint8_t reu_array_count;
static OverlayBlock overlays[MAX_OVERLAYS];
static uint8_t overlay_count;
static OverlayBlock* used_overlays[MAX_OVERLAYS];
static uint8_t used_overlay_count;
static DiskModule modules[MAX_MODULES];
static uint8_t module_count;
static DiskModule* included_modules[MAX_MODULES];
static uint8_t included_module_count;
static uint8_t module_blob[MAX_MODULES * MAX_MODULE_PAYLOAD];
static uint16_t module_blob_len;
static uint8_t overlay_blob[MAX_OVERLAY_BLOB];
static uint16_t overlay_blob_len;
static char manifest_buffer[MAX_MANIFEST_BYTES];
static char map_buffer[MAX_MAP_BYTES];
static char root_imports[MAX_ROOT_IMPORTS][MAX_IDENT_LEN + 1];
static uint8_t root_import_count;
static bool used_format_int;
static bool used_format_real;

static const Keyword KEYWORDS[] = {
    {"MODULE", TOK_MODULE},
    {"PROC", TOK_PROC},
    {"RETURN", TOK_RETURN},
    {"PRINT", TOK_PRINT},
    {"PRINTE", TOK_PRINTE},
    {"PRINTI", TOK_PRINTI},
    {"PRINTIE", TOK_PRINTIE},
    {"PRINTR", TOK_PRINTR},
    {"PRINTRE", TOK_PRINTRE},
    {"IF", TOK_IF},
    {"THEN", TOK_THEN},
    {"FI", TOK_FI},
    {"REU", TOK_REU},
    {"REUPOKE8", TOK_REUPOKE8},
    {"REUPOKE16", TOK_REUPOKE16},
    {"REUPEEK8", TOK_REUPEEK8},
    {"REUPEEK16", TOK_REUPEEK16},
    {"OVERLAY", TOK_OVERLAY},
    {"ENDOVERLAY", TOK_ENDOVERLAY},
    {"OVERLAYCALL", TOK_OVERLAYCALL},
    {"BYTE", TOK_BYTE},
    {"CARD", TOK_CARD},
    {"INT", TOK_INT},
    {"REAL", TOK_REAL},
};

static const char* LIBRARY_FILES[] = {
    "libpstr.mod",
    "libplin.mod",
    "libfint.mod",
    "libfadd.mod",
    "libfsub.mod",
    "libfmul.mod",
    "libfdiv.mod",
    "libfcmp.mod",
    "libitof.mod",
    "libftoi.mod",
    "libprf.mod",
    "libreua.mod",
    "librep8.mod",
    "librep16.mod",
    "librpo8.mod",
    "librpo16.mod",
    "libovll.mod",
    "libovlc.mod",
};
static const char LIBRARY_PACK_FILE[] = "libmods.dat";

static void print_cstr(const char* s)
{
    while (*s)
        cpm_conout((uint8_t)*s++);
}

static void print_uint16(uint16_t value)
{
    char digits[6];
    uint8_t len = 0;
    if (value == 0)
    {
        cpm_conout('0');
        return;
    }
    while (value && (len < sizeof(digits)))
    {
        digits[len++] = (char)('0' + (value % 10));
        value /= 10;
    }
    while (len)
        cpm_conout((uint8_t)digits[--len]);
}

static void crlf(void)
{
    print_cstr("\r\n");
}

static void fatal_at(uint16_t line_no, const char* message)
{
    print_cstr("actc:");
    if (line_no)
    {
        cpm_conout(' ');
        print_cstr("line ");
        print_uint16(line_no);
        cpm_conout(':');
    }
    cpm_conout(' ');
    print_cstr(message);
    crlf();
    cpm_warmboot();
}

static void fatal(const char* message)
{
    fatal_at(0, message);
}

static char upcase_ascii(char ch)
{
    if ((ch >= 'a') && (ch <= 'z'))
        return (char)(ch - 'a' + 'A');
    return ch;
}

static char* trim(char* text)
{
    while ((*text == ' ') || (*text == '\t'))
        text++;
    char* end = text + strlen(text);
    while ((end > text) && ((end[-1] == ' ') || (end[-1] == '\t') || (end[-1] == '\r') || (end[-1] == '\n')))
        *--end = 0;
    return text;
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

static void source_filename_from_primary_fcb(char* out)
{
    if (!fcb_has_filename(&cpm_fcb))
    {
        strcpy(out, "main.act");
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

static void replace_extension_from_source(const char* source_name, const char* extension, char* out)
{
    uint8_t stem_len = 0;
    while (source_name[stem_len] && (source_name[stem_len] != '.') && (stem_len < 8))
    {
        out[stem_len] = source_name[stem_len];
        stem_len++;
    }
    out[stem_len] = 0;
    strcat(out, extension);
}

static void read_text_file(const char* filename, char* buffer, uint16_t capacity, const char* label)
{
    FCB fcb;
    parse_filename(&fcb, filename);
    fcb.ex = 0;
    fcb.cr = 0;
    if (cpm_open_file(&fcb) != CPME_OK)
        fatal(label);

    uint16_t pos = 0;
    for (;;)
    {
        cpm_set_dma(cpm_default_dma);
        uint8_t rc = cpm_read_sequential(&fcb);
        if (rc != CPME_OK)
            break;
        for (uint8_t i = 0; i < 128; i++)
        {
            uint8_t ch = cpm_default_dma[i];
            if ((ch == 0) || (ch == 0x1a))
            {
                buffer[pos] = 0;
                return;
            }
            if (pos + 1 >= capacity)
                fatal("text file too large");
            buffer[pos++] = (char)ch;
        }
    }
    buffer[pos] = 0;
}

static void read_source_file(const char* filename)
{
    read_text_file(filename, source_buffer, MAX_SOURCE_BYTES, "cannot open source");
}

static void preprocess_source(void)
{
    char* cursor = source_buffer;
    uint16_t line_no = 1;
    line_count = 0;

    while (*cursor)
    {
        char* line_start = cursor;
        while (*cursor && (*cursor != '\n') && (*cursor != '\r'))
            cursor++;
        if (*cursor == '\r')
            *cursor++ = 0;
        if (*cursor == '\n')
            *cursor++ = 0;

        char* comment = strchr(line_start, ';');
        if (comment)
            *comment = 0;

        char* text = trim(line_start);
        if (*text)
        {
            if (line_count >= MAX_LINES)
                fatal("too many source lines");
            lines[line_count].line_no = line_no;
            lines[line_count].text = text;
            line_count++;
        }
        line_no++;
    }
}

static uint16_t append_text(const char* text)
{
    uint16_t offset = text_pool_len;
    while (*text)
    {
        if ((uint16_t)(text_pool_len + 1u) >= MAX_TEXT_POOL)
            fatal("text pool overflow");
        text_pool[text_pool_len++] = *text++;
    }
    if ((uint16_t)(text_pool_len + 1u) >= MAX_TEXT_POOL)
        fatal("text pool overflow");
    text_pool[text_pool_len++] = 0;
    return offset;
}

static void add_action(const char* text, bool newline)
{
    if (action_count >= MAX_ACTIONS)
        fatal("too many print actions");
    actions[action_count].text_offset = append_text(text);
    actions[action_count].newline = newline;
    action_count++;
}

static void format_int32(int32_t value, char* out)
{
    char digits[12];
    uint8_t len = 0;
    uint32_t raw;
    uint8_t pos = 0;

    if (value < 0)
    {
        out[pos++] = '-';
        raw = (uint32_t)(-value);
    }
    else
        raw = (uint32_t)value;

    if (raw == 0)
    {
        out[pos++] = '0';
        out[pos] = 0;
        return;
    }

    while (raw)
    {
        digits[len++] = (char)('0' + (raw % 10u));
        raw /= 10u;
    }

    while (len)
        out[pos++] = digits[--len];
    out[pos] = 0;
}

static void format_real32(float value, char* out)
{
    uint8_t pos = 0;
    if (value < 0.0f)
    {
        out[pos++] = '-';
        value = -value;
    }

    int32_t whole = (int32_t)value;
    float fraction = value - (float)whole;
    uint32_t scaled = (uint32_t)(fraction * 1000000.0f + 0.5f);
    if (scaled >= 1000000u)
    {
        whole++;
        scaled -= 1000000u;
    }

    format_int32(whole, out + pos);
    pos = (uint8_t)strlen(out);
    if (scaled != 0)
    {
        char fractional[7];
        fractional[6] = 0;
        for (int8_t i = 5; i >= 0; i--)
        {
            fractional[i] = (char)('0' + (scaled % 10u));
            scaled /= 10u;
        }
        int8_t end = 5;
        while ((end >= 0) && (fractional[end] == '0'))
            end--;
        out[pos++] = '.';
        for (int8_t i = 0; i <= end; i++)
            out[pos++] = fractional[i];
    }
    out[pos] = 0;
}

static Value make_int_value(ValueType type, int32_t raw)
{
    Value value;
    value.type = type;
    value.int_value = raw;
    value.real_value = (float)raw;
    return value;
}

static Value make_real_value(float raw)
{
    Value value;
    value.type = TYPE_REAL;
    value.int_value = (int32_t)raw;
    value.real_value = raw;
    return value;
}

static bool value_is_true(Value value)
{
    if (value.type == TYPE_REAL)
        return value.real_value != 0.0f;
    return value.int_value != 0;
}

static ValueType integer_arithmetic_type(ValueType left, ValueType right)
{
    if ((left == TYPE_INT) || (right == TYPE_INT))
        return TYPE_INT;
    return TYPE_CARD;
}

static float promote_to_real(Value value)
{
    if (value.type == TYPE_REAL)
        return value.real_value;
    add_root_import("rt.i_to_f");
    return (float)value.int_value;
}

static ReuArray* find_reu_array(const char* name)
{
    for (uint8_t i = 0; i < reu_array_count; i++)
    {
        if (strcmp(reu_arrays[i].name, name) == 0)
            return &reu_arrays[i];
    }
    return 0;
}

static OverlayBlock* find_overlay(const char* name)
{
    for (uint8_t i = 0; i < overlay_count; i++)
    {
        if (strcmp(overlays[i].name, name) == 0)
            return &overlays[i];
    }
    return 0;
}

static void remember_overlay_usage(OverlayBlock* overlay)
{
    for (uint8_t i = 0; i < used_overlay_count; i++)
    {
        if (used_overlays[i] == overlay)
            return;
    }
    if (used_overlay_count >= MAX_OVERLAYS)
        fatal("too many overlays");
    used_overlays[used_overlay_count++] = overlay;

    char payload[MAX_OVERLAY_PAYLOAD];
    strcpy(payload, "overlay:");
    strcat(payload, overlay->name);
    uint16_t payload_len = (uint16_t)(strlen(payload) + 1u);
    if ((uint16_t)(overlay_blob_len + payload_len) > MAX_OVERLAY_BLOB)
        fatal("overlay payload too large");
    memcpy(&overlay_blob[overlay_blob_len], payload, payload_len);
    overlay_blob_len = (uint16_t)(overlay_blob_len + payload_len);
}

static void emit_payload(uint16_t* out_len)
{
    uint16_t code_len = (uint16_t)(action_count * 6u + 3u);
    uint16_t string_base = code_len;
    uint16_t pos = AVM_HEADER_SIZE;
    uint16_t payload_len = (uint16_t)(code_len + text_pool_len + module_blob_len + overlay_blob_len);

    if ((uint16_t)(AVM_HEADER_SIZE + payload_len) > MAX_AVM_BYTES)
        fatal("AVM too large");

    memcpy(avm_buffer, "AVM1", 4);
    avm_buffer[4] = 1;
    avm_buffer[5] = (uint8_t)(payload_len & 0xff);
    avm_buffer[6] = (uint8_t)(payload_len >> 8);
    avm_buffer[7] = 0;
    avm_buffer[8] = 0;
    avm_buffer[9] = 0;

    for (uint16_t i = 0; i < action_count; i++)
    {
        uint16_t string_offset = (uint16_t)(string_base + actions[i].text_offset);
        avm_buffer[pos++] = OPCODE_SETP16;
        avm_buffer[pos++] = (uint8_t)(string_offset & 0xff);
        avm_buffer[pos++] = (uint8_t)(string_offset >> 8);
        avm_buffer[pos++] = OPCODE_CALLN;
        avm_buffer[pos++] = actions[i].newline ? 0x10 : 0x00;
        avm_buffer[pos++] = 0xff;
    }

    avm_buffer[pos++] = OPCODE_CALLN;
    avm_buffer[pos++] = 0x20;
    avm_buffer[pos++] = 0xff;

    memcpy(&avm_buffer[AVM_HEADER_SIZE + code_len], text_pool, text_pool_len);
    memcpy(&avm_buffer[AVM_HEADER_SIZE + code_len + text_pool_len], module_blob, module_blob_len);
    memcpy(&avm_buffer[AVM_HEADER_SIZE + code_len + text_pool_len + module_blob_len], overlay_blob, overlay_blob_len);
    *out_len = (uint16_t)(AVM_HEADER_SIZE + payload_len);
}

static void write_binary_file(const char* filename, const uint8_t* data, uint16_t len)
{
    FCB fcb;
    parse_filename(&fcb, filename);
    fcb.ex = 0;
    fcb.cr = 0;
    cpm_delete_file(&fcb);
    fcb.ex = 0;
    fcb.cr = 0;
    if (cpm_make_file(&fcb) != CPME_OK)
        fatal("cannot create output");

    uint16_t pos = 0;
    while (pos < len)
    {
        memset(cpm_default_dma, 0, 128);
        uint16_t chunk = (uint16_t)(len - pos);
        if (chunk > 128)
            chunk = 128;
        memcpy(cpm_default_dma, &data[pos], chunk);
        cpm_set_dma(cpm_default_dma);
        if (cpm_write_sequential(&fcb) != CPME_OK)
            fatal("cannot write output");
        pos = (uint16_t)(pos + chunk);
    }

    if (cpm_close_file(&fcb) != CPME_OK)
        fatal("cannot close output");
}

static void write_text_file(const char* filename, const char* text)
{
    write_binary_file(filename, (const uint8_t*)text, (uint16_t)strlen(text));
}

static bool starts_with_ascii(const char* text, const char* prefix)
{
    while (*prefix)
    {
        if (upcase_ascii(*text++) != upcase_ascii(*prefix++))
            return false;
    }
    return true;
}

static void copy_trimmed_ascii(char* out, uint16_t out_cap, const char* text)
{
    char local[MAX_MANIFEST_BYTES];
    strncpy(local, text, sizeof(local) - 1);
    local[sizeof(local) - 1] = 0;
    char* trimmed = trim(local);
    size_t len = strlen(trimmed);
    if ((len + 1) > out_cap)
        fatal("manifest field too long");
    memcpy(out, trimmed, len + 1);
}

static bool file_exists_on_disk(const char* filename)
{
    FCB fcb;
    parse_filename(&fcb, filename);
    fcb.ex = 0;
    fcb.cr = 0;
    if (cpm_open_file(&fcb) != CPME_OK)
        return false;
    cpm_close_file(&fcb);
    return true;
}

static bool manifest_already_loaded(const char* filename)
{
    for (uint8_t i = 0; i < module_count; i++)
    {
        if (strcmp(modules[i].filename, filename) == 0)
            return true;
    }
    return false;
}

static void load_manifest_text(const char* filename, char* buffer)
{
    if (manifest_already_loaded(filename))
        return;
    if (module_count >= MAX_MODULES)
        fatal("too many library manifests");

    DiskModule* module = &modules[module_count];
    memset(module, 0, sizeof(*module));
    strcpy(module->filename, filename);
    char* cursor = buffer;

    while (*cursor)
    {
        char* line_start = cursor;
        while (*cursor && (*cursor != '\n') && (*cursor != '\r'))
            cursor++;
        if (*cursor == '\r')
            *cursor++ = 0;
        if (*cursor == '\n')
            *cursor++ = 0;

        char* comment = strchr(line_start, ';');
        if (comment)
            *comment = 0;

        char* text = trim(line_start);
        if (!*text)
            continue;

        if (starts_with_ascii(text, "MODULE "))
        {
            copy_trimmed_ascii(module->module_name, sizeof(module->module_name), text + 7);
            continue;
        }

        if (starts_with_ascii(text, "IMPORT "))
        {
            if (module->import_count >= MAX_MODULE_IMPORTS)
                fatal("too many module imports");
            copy_trimmed_ascii(module->imports[module->import_count], sizeof(module->imports[module->import_count]), text + 7);
            module->import_count++;
            continue;
        }

        if (starts_with_ascii(text, "PAYLOAD "))
        {
            char payload_text[MAX_MODULE_PAYLOAD];
            copy_trimmed_ascii(payload_text, sizeof(payload_text), text + 8);
            module->payload_len = (uint8_t)(strlen(payload_text) + 1u);
            memcpy(module->payload, payload_text, module->payload_len);
            continue;
        }

        fatal("bad library manifest");
    }

    if (!module->module_name[0] || !module->payload_len)
        fatal("incomplete library manifest");
    module->loaded = true;
    module_count++;
}

static void load_manifest_file(const char* filename)
{
    read_text_file(filename, manifest_buffer, MAX_MANIFEST_BYTES, "cannot open library manifest");
    load_manifest_text(filename, manifest_buffer);
}

static void load_manifest_pack_file(const char* filename)
{
    char current_name[13];
    char current_text[256];
    uint16_t current_len = 0;
    current_name[0] = 0;

    read_text_file(filename, manifest_buffer, MAX_MANIFEST_BYTES, "cannot open library manifest pack");
    char* cursor = manifest_buffer;

    while (*cursor)
    {
        char* line_start = cursor;
        while (*cursor && (*cursor != '\n') && (*cursor != '\r'))
            cursor++;
        if (*cursor == '\r')
            *cursor++ = 0;
        if (*cursor == '\n')
            *cursor++ = 0;

        char* text = trim(line_start);
        if (!*text)
            continue;

        if (starts_with_ascii(text, "FILE "))
        {
            if (current_name[0])
            {
                current_text[current_len] = 0;
                load_manifest_text(current_name, current_text);
            }
            copy_trimmed_ascii(current_name, sizeof(current_name), text + 5);
            current_len = 0;
            continue;
        }

        if (starts_with_ascii(text, "END"))
        {
            if (current_name[0])
            {
                current_text[current_len] = 0;
                load_manifest_text(current_name, current_text);
            }
            current_name[0] = 0;
            current_len = 0;
            continue;
        }

        if (!current_name[0])
            fatal("bad library manifest pack");

        size_t len = strlen(text);
        if ((current_len + len + 2u) >= sizeof(current_text))
            fatal("manifest pack entry too large");
        memcpy(&current_text[current_len], text, len);
        current_len = (uint16_t)(current_len + len);
        current_text[current_len++] = '\n';
    }

    if (current_name[0])
    {
        current_text[current_len] = 0;
        load_manifest_text(current_name, current_text);
    }
}

static void load_library_manifests(void)
{
    module_count = 0;
    if (file_exists_on_disk(LIBRARY_PACK_FILE))
        load_manifest_pack_file(LIBRARY_PACK_FILE);
    for (uint8_t i = 0; i < (sizeof(LIBRARY_FILES) / sizeof(LIBRARY_FILES[0])); i++)
    {
        if (!file_exists_on_disk(LIBRARY_FILES[i]))
            continue;
        load_manifest_file(LIBRARY_FILES[i]);
    }
}

static void add_root_import(const char* name)
{
    for (uint8_t i = 0; i < root_import_count; i++)
    {
        if (strcmp(root_imports[i], name) == 0)
            return;
    }
    if (root_import_count >= MAX_ROOT_IMPORTS)
        fatal("too many root imports");
    strcpy(root_imports[root_import_count], name);
    root_import_count++;
}

static void collect_root_imports(void)
{
    bool uses_print = false;
    bool uses_print_line = false;

    for (uint16_t i = 0; i < action_count; i++)
    {
        if (actions[i].newline)
            uses_print_line = true;
        else
            uses_print = true;
    }

    if (uses_print)
        add_root_import("rt.print_str");
    if (uses_print_line)
        add_root_import("rt.print_line");
    if (used_format_int)
        add_root_import("rt.format_int");
    if (used_format_real)
        add_root_import("rt.print_f");
}

static DiskModule* find_module(const char* module_name)
{
    for (uint8_t i = 0; i < module_count; i++)
    {
        if (strcmp(modules[i].module_name, module_name) == 0)
            return &modules[i];
    }
    return 0;
}

static void include_module_recursive(const char* module_name)
{
    for (uint8_t i = 0; i < included_module_count; i++)
    {
        if (strcmp(included_modules[i]->module_name, module_name) == 0)
            return;
    }

    DiskModule* module = find_module(module_name);
    if (!module)
        fatal("required library manifest is missing");
    if (included_module_count >= MAX_MODULES)
        fatal("too many included modules");
    included_modules[included_module_count++] = module;

    for (uint8_t i = 0; i < module->import_count; i++)
        include_module_recursive(module->imports[i]);
}

static void resolve_runtime_modules(void)
{
    included_module_count = 0;
    module_blob_len = 0;

    load_library_manifests();
    collect_root_imports();
    for (uint8_t i = 0; i < root_import_count; i++)
        include_module_recursive(root_imports[i]);

    for (uint8_t i = 0; i < included_module_count; i++)
    {
        DiskModule* module = included_modules[i];
        if ((uint16_t)(module_blob_len + module->payload_len) > MAX_AVM_BYTES)
            fatal("library payload too large");
        memcpy(&module_blob[module_blob_len], module->payload, module->payload_len);
        module_blob_len = (uint16_t)(module_blob_len + module->payload_len);
    }
}

static uint16_t map_append_bytes(uint16_t pos, const char* text)
{
    size_t len = strlen(text);
    if ((pos + len + 1u) >= MAX_MAP_BYTES)
        fatal("map output too large");
    memcpy(&map_buffer[pos], text, len);
    return (uint16_t)(pos + len);
}

static void write_map_file(const char* filename)
{
    uint16_t pos = 0;
    map_buffer[0] = 0;

    pos = map_append_bytes(pos, "# ACTC Map\n\nroot imports:\n");
    for (uint8_t i = 0; i < root_import_count; i++)
    {
        pos = map_append_bytes(pos, "- ");
        pos = map_append_bytes(pos, root_imports[i]);
        pos = map_append_bytes(pos, "\n");
    }

    pos = map_append_bytes(pos, "\nincluded modules:\n");
    for (uint8_t i = 0; i < included_module_count; i++)
    {
        char size_text[16];
        format_int32(included_modules[i]->payload_len, size_text);
        pos = map_append_bytes(pos, "- ");
        pos = map_append_bytes(pos, included_modules[i]->module_name);
        pos = map_append_bytes(pos, " file=");
        pos = map_append_bytes(pos, included_modules[i]->filename);
        pos = map_append_bytes(pos, " size=");
        pos = map_append_bytes(pos, size_text);
        pos = map_append_bytes(pos, "\n");
    }

    if (used_overlay_count)
    {
        pos = map_append_bytes(pos, "\noverlays:\n");
        for (uint8_t i = 0; i < used_overlay_count; i++)
        {
            pos = map_append_bytes(pos, "- ");
            pos = map_append_bytes(pos, used_overlays[i]->name);
            pos = map_append_bytes(pos, "\n");
        }
    }

    map_buffer[pos] = 0;
    write_text_file(filename, map_buffer);
}

static Symbol* find_symbol(const char* name)
{
    for (uint16_t i = 0; i < symbol_count; i++)
    {
        if (strcmp(symbols[i].name, name) == 0)
            return &symbols[i];
    }
    return 0;
}

static void declare_symbol(const char* name, ValueType type, uint16_t line_no)
{
    if (find_symbol(name))
        fatal_at(line_no, "duplicate variable");
    if (symbol_count >= MAX_SYMBOLS)
        fatal("too many variables");
    strcpy(symbols[symbol_count].name, name);
    symbols[symbol_count].type = type;
    symbols[symbol_count].int_value = 0;
    symbols[symbol_count].real_value = 0.0f;
    symbols[symbol_count].assigned = false;
    symbol_count++;
}

static int32_t coerce_integer_to_type(ValueType target, int32_t raw, uint16_t line_no)
{
    if (target == TYPE_BYTE)
    {
        if ((raw < 0) || (raw > 0xff))
            fatal_at(line_no, "value does not fit in BYTE");
        return raw;
    }
    if (target == TYPE_CARD)
    {
        if ((raw < 0) || (raw > 0xffff))
            fatal_at(line_no, "value does not fit in CARD");
        return raw;
    }
    if ((raw < -0x8000) || (raw > 0x7fff))
        fatal_at(line_no, "value does not fit in INT");
    return raw;
}

static void assign_symbol_value(Symbol* symbol, Value value, uint16_t line_no)
{
    if (symbol->type == TYPE_REAL)
    {
        symbol->real_value = (value.type == TYPE_REAL) ? value.real_value : promote_to_real(value);
        symbol->int_value = (int32_t)symbol->real_value;
        symbol->assigned = true;
        return;
    }

    if (value.type == TYPE_REAL)
        fatal_at(line_no, "cannot assign REAL to integer storage without INT(...)");

    symbol->int_value = coerce_integer_to_type(symbol->type, value.int_value, line_no);
    symbol->real_value = (float)symbol->int_value;
    symbol->assigned = true;
}

static TokenKind lookup_keyword(const char* text)
{
    for (uint8_t i = 0; i < (sizeof(KEYWORDS) / sizeof(KEYWORDS[0])); i++)
    {
        if (strcmp(text, KEYWORDS[i].name) == 0)
            return KEYWORDS[i].kind;
    }
    return TOK_IDENT;
}

static float parse_real_literal(const char* text, const char** end_out, uint16_t line_no)
{
    const char* cursor = text;
    float value = 0.0f;
    bool saw_digit = false;

    while ((*cursor >= '0') && (*cursor <= '9'))
    {
        saw_digit = true;
        value = value * 10.0f + (float)(*cursor - '0');
        cursor++;
    }

    if (*cursor == '.')
    {
        float scale = 0.1f;
        cursor++;
        while ((*cursor >= '0') && (*cursor <= '9'))
        {
            saw_digit = true;
            value += (float)(*cursor - '0') * scale;
            scale *= 0.1f;
            cursor++;
        }
    }

    if ((*cursor == 'e') || (*cursor == 'E'))
    {
        bool negative = false;
        int8_t exponent = 0;
        cursor++;
        if ((*cursor == '+') || (*cursor == '-'))
        {
            negative = (*cursor == '-');
            cursor++;
        }
        if ((*cursor < '0') || (*cursor > '9'))
            fatal_at(line_no, "bad REAL literal");
        while ((*cursor >= '0') && (*cursor <= '9'))
        {
            exponent = (int8_t)(exponent * 10 + (*cursor - '0'));
            cursor++;
        }
        while (exponent--)
        {
            if (negative)
                value *= 0.1f;
            else
                value *= 10.0f;
        }
    }

    if (!saw_digit)
        fatal_at(line_no, "bad REAL literal");
    *end_out = cursor;
    return value;
}

static void lexer_next(Lexer* lexer)
{
    while ((*lexer->cursor == ' ') || (*lexer->cursor == '\t'))
        lexer->cursor++;

    lexer->token.text[0] = 0;
    lexer->token.number = 0;
    lexer->token.real_number = 0.0f;
    lexer->token.is_real = false;

    char ch = *lexer->cursor;
    if (!ch)
    {
        lexer->token.kind = TOK_EOF;
        return;
    }

    if (((ch >= 'A') && (ch <= 'Z')) || ((ch >= 'a') && (ch <= 'z')) || (ch == '_'))
    {
        uint16_t len = 0;
        while ((((ch = *lexer->cursor) >= 'A') && (ch <= 'Z')) ||
               ((ch >= 'a') && (ch <= 'z')) ||
               ((ch >= '0') && (ch <= '9')) ||
               (ch == '_'))
        {
            if (len >= MAX_IDENT_LEN)
                fatal_at(lexer->line_no, "identifier too long");
            lexer->token.text[len++] = upcase_ascii(ch);
            lexer->cursor++;
        }
        lexer->token.text[len] = 0;
        lexer->token.kind = lookup_keyword(lexer->token.text);
        return;
    }

    if (((ch >= '0') && (ch <= '9')) || (ch == '$'))
    {
        int32_t value = 0;
        if (ch == '$')
        {
            lexer->cursor++;
            if (!*lexer->cursor)
                fatal_at(lexer->line_no, "bad hex literal");
            while (((ch = *lexer->cursor) >= '0' && ch <= '9') ||
                   (ch >= 'A' && ch <= 'F') ||
                   (ch >= 'a' && ch <= 'f'))
            {
                value <<= 4;
                if (ch <= '9')
                    value += ch - '0';
                else
                    value += upcase_ascii(ch) - 'A' + 10;
                lexer->cursor++;
            }
        }
        else
        {
            const char* scan = lexer->cursor;
            while (((ch = *scan) >= '0') && (ch <= '9'))
                scan++;
            if ((*scan == '.') || (*scan == 'e') || (*scan == 'E'))
            {
                const char* end = lexer->cursor;
                float real_value = parse_real_literal(lexer->cursor, &end, lexer->line_no);
                lexer->cursor = end;
                lexer->token.kind = TOK_NUMBER;
                lexer->token.real_number = real_value;
                lexer->token.is_real = true;
                return;
            }
            while (((ch = *lexer->cursor) >= '0') && (ch <= '9'))
            {
                value = value * 10 + (ch - '0');
                lexer->cursor++;
            }
        }
        lexer->token.kind = TOK_NUMBER;
        lexer->token.number = value;
        return;
    }

    if (ch == '"')
    {
        uint16_t len = 0;
        lexer->cursor++;
        while ((ch = *lexer->cursor) && (ch != '"'))
        {
            if (len >= MAX_TOKEN_TEXT)
                fatal_at(lexer->line_no, "string literal too long");
            if (ch == '\\')
            {
                lexer->cursor++;
                ch = *lexer->cursor;
                if (ch == 'n')
                    lexer->token.text[len++] = '\n';
                else if (ch == 'r')
                    lexer->token.text[len++] = '\r';
                else if (ch == 't')
                    lexer->token.text[len++] = '\t';
                else if ((ch == '"') || (ch == '\\'))
                    lexer->token.text[len++] = ch;
                else
                    fatal_at(lexer->line_no, "unsupported string escape");
                if (!*lexer->cursor)
                    fatal_at(lexer->line_no, "unterminated string literal");
                lexer->cursor++;
                continue;
            }
            lexer->token.text[len++] = ch;
            lexer->cursor++;
        }
        if (*lexer->cursor != '"')
            fatal_at(lexer->line_no, "unterminated string literal");
        lexer->cursor++;
        lexer->token.text[len] = 0;
        lexer->token.kind = TOK_STRING;
        return;
    }

    lexer->cursor++;
    if (ch == '(')
        lexer->token.kind = TOK_LPAREN;
    else if (ch == ')')
        lexer->token.kind = TOK_RPAREN;
    else if (ch == ',')
        lexer->token.kind = TOK_COMMA;
    else if (ch == '+')
        lexer->token.kind = TOK_PLUS;
    else if (ch == '-')
        lexer->token.kind = TOK_MINUS;
    else if (ch == '*')
        lexer->token.kind = TOK_STAR;
    else if (ch == '/')
        lexer->token.kind = TOK_SLASH;
    else if (ch == '=')
        lexer->token.kind = TOK_EQ;
    else if (ch == '<')
    {
        if (*lexer->cursor == '=')
        {
            lexer->cursor++;
            lexer->token.kind = TOK_LE;
        }
        else if (*lexer->cursor == '>')
        {
            lexer->cursor++;
            lexer->token.kind = TOK_NE;
        }
        else
            lexer->token.kind = TOK_LT;
    }
    else if (ch == '>')
    {
        if (*lexer->cursor == '=')
        {
            lexer->cursor++;
            lexer->token.kind = TOK_GE;
        }
        else
            lexer->token.kind = TOK_GT;
    }
    else
        fatal_at(lexer->line_no, "unsupported character");
}

static void lexer_init(Lexer* lexer, const SourceLine* line)
{
    lexer->cursor = line->text;
    lexer->line_no = line->line_no;
    lexer_next(lexer);
}

static void expect_token(Lexer* lexer, TokenKind kind, const char* message)
{
    if (lexer->token.kind != kind)
        fatal_at(lexer->line_no, message);
}

static void expect_eof(Lexer* lexer)
{
    if (lexer->token.kind != TOK_EOF)
        fatal_at(lexer->line_no, "unexpected trailing text");
}

static Value parse_expression(Lexer* lexer, bool evaluate);

static Value parse_primary(Lexer* lexer, bool evaluate)
{
    if (lexer->token.kind == TOK_NUMBER)
    {
        Value value = lexer->token.is_real
            ? make_real_value(lexer->token.real_number)
            : make_int_value((lexer->token.number < 256) ? TYPE_BYTE : TYPE_CARD, lexer->token.number);
        lexer_next(lexer);
        return value;
    }

    if ((lexer->token.kind == TOK_REAL) || (lexer->token.kind == TOK_INT))
    {
        TokenKind target_kind = lexer->token.kind;
        lexer_next(lexer);
        expect_token(lexer, TOK_LPAREN, "expected '(' after conversion");
        lexer_next(lexer);
        Value operand = parse_expression(lexer, evaluate);
        expect_token(lexer, TOK_RPAREN, "expected ')' after conversion");
        lexer_next(lexer);
        if (!evaluate)
            return (target_kind == TOK_REAL) ? make_real_value(0.0f) : make_int_value(TYPE_INT, 0);

        if (target_kind == TOK_REAL)
            return make_real_value(promote_to_real(operand));

        if (operand.type != TYPE_REAL)
            return make_int_value(TYPE_INT, coerce_integer_to_type(TYPE_INT, operand.int_value, lexer->line_no));

        add_root_import("rt.f_to_i");
        if ((operand.real_value < -32768.0f) || (operand.real_value > 32767.0f))
            fatal_at(lexer->line_no, "REAL to INT conversion overflow");
        return make_int_value(TYPE_INT, (int32_t)operand.real_value);
    }

    if ((lexer->token.kind == TOK_REUPEEK8) || (lexer->token.kind == TOK_REUPEEK16))
    {
        bool wide = (lexer->token.kind == TOK_REUPEEK16);
        char name[MAX_IDENT_LEN + 1];
        lexer_next(lexer);
        expect_token(lexer, TOK_LPAREN, "expected '(' after REUPEEK");
        lexer_next(lexer);
        expect_token(lexer, TOK_IDENT, "expected REU array name");
        strcpy(name, lexer->token.text);
        lexer_next(lexer);
        expect_token(lexer, TOK_COMMA, "expected ',' after REU array name");
        lexer_next(lexer);
        Value index = parse_expression(lexer, evaluate);
        expect_token(lexer, TOK_RPAREN, "expected ')' after REUPEEK");
        lexer_next(lexer);

        if (!evaluate)
            return make_int_value(wide ? TYPE_CARD : TYPE_BYTE, 0);

        if (index.type == TYPE_REAL)
            fatal_at(lexer->line_no, "REU indexes must be integer expressions");
        ReuArray* array = find_reu_array(name);
        if (!array)
            fatal_at(lexer->line_no, "unknown REU array");
        if ((index.int_value < 0) || ((uint32_t)index.int_value >= array->length) ||
            (wide && (((uint32_t)index.int_value + 1u) >= array->length)))
            fatal_at(lexer->line_no, "REU access out of bounds");

        if (wide)
        {
            uint16_t raw = 0;
            add_root_import("rt.reu_peek16");
            if (!reu_peek16(array->handle, (uint32_t)index.int_value, &raw))
                fatal_at(lexer->line_no, "REU backend read failed");
            return make_int_value(TYPE_CARD, raw);
        }

        uint8_t raw = 0;
        add_root_import("rt.reu_peek8");
        if (!reu_peek8(array->handle, (uint32_t)index.int_value, &raw))
            fatal_at(lexer->line_no, "REU backend read failed");
        return make_int_value(TYPE_BYTE, raw);
    }

    if (lexer->token.kind == TOK_IDENT)
    {
        Value value;
        Symbol* symbol = find_symbol(lexer->token.text);
        if (evaluate)
        {
            if (!symbol)
                fatal_at(lexer->line_no, "unknown variable");
            if (!symbol->assigned)
                fatal_at(lexer->line_no, "variable used before assignment");
            value.type = symbol->type;
            value.int_value = symbol->int_value;
            value.real_value = symbol->real_value;
        }
        else
        {
            value = symbol ? ((symbol->type == TYPE_REAL) ? make_real_value(0.0f) : make_int_value(symbol->type, 0))
                           : make_int_value(TYPE_CARD, 0);
        }
        lexer_next(lexer);
        return value;
    }

    if (lexer->token.kind == TOK_LPAREN)
    {
        lexer_next(lexer);
        Value value = parse_expression(lexer, evaluate);
        expect_token(lexer, TOK_RPAREN, "expected ')' ");
        lexer_next(lexer);
        return value;
    }

    fatal_at(lexer->line_no, "expected expression");
    return make_int_value(TYPE_CARD, 0);
}

static Value parse_unary(Lexer* lexer, bool evaluate)
{
    if (lexer->token.kind == TOK_MINUS)
    {
        lexer_next(lexer);
        Value operand = parse_unary(lexer, evaluate);
        if (!evaluate)
        {
            return (operand.type == TYPE_REAL) ? make_real_value(0.0f) : make_int_value(TYPE_INT, 0);
        }
        if (operand.type == TYPE_REAL)
            return make_real_value(-operand.real_value);
        return make_int_value(TYPE_INT, -operand.int_value);
    }
    return parse_primary(lexer, evaluate);
}

static Value parse_muldiv(Lexer* lexer, bool evaluate)
{
    Value left = parse_unary(lexer, evaluate);
    while ((lexer->token.kind == TOK_STAR) || (lexer->token.kind == TOK_SLASH))
    {
        TokenKind op = lexer->token.kind;
        lexer_next(lexer);
        Value right = parse_unary(lexer, evaluate);
        if (!evaluate)
        {
            if ((left.type == TYPE_REAL) || (right.type == TYPE_REAL))
                left = make_real_value(0.0f);
            else
                left = make_int_value(integer_arithmetic_type(left.type, right.type), 0);
            continue;
        }

        if ((left.type == TYPE_REAL) || (right.type == TYPE_REAL))
        {
            float lhs = promote_to_real(left);
            float rhs = promote_to_real(right);
            if ((op == TOK_SLASH) && (rhs == 0.0f))
                fatal_at(lexer->line_no, "division by zero");
            add_root_import((op == TOK_STAR) ? "rt.f_mul" : "rt.f_div");
            left = make_real_value((op == TOK_STAR) ? (lhs * rhs) : (lhs / rhs));
            continue;
        }

        if ((op == TOK_SLASH) && (right.int_value == 0))
            fatal_at(lexer->line_no, "division by zero");

        ValueType result_type = integer_arithmetic_type(left.type, right.type);
        int32_t raw;
        if (op == TOK_STAR)
            raw = left.int_value * right.int_value;
        else if (result_type == TYPE_INT)
            raw = left.int_value / right.int_value;
        else
            raw = (int32_t)((uint32_t)left.int_value / (uint32_t)right.int_value);

        if ((result_type != TYPE_INT) && (raw < 0))
            fatal_at(lexer->line_no, "unsigned result became negative");
        left = make_int_value(result_type, raw);
    }
    return left;
}

static Value parse_addsub(Lexer* lexer, bool evaluate)
{
    Value left = parse_muldiv(lexer, evaluate);
    while ((lexer->token.kind == TOK_PLUS) || (lexer->token.kind == TOK_MINUS))
    {
        TokenKind op = lexer->token.kind;
        lexer_next(lexer);
        Value right = parse_muldiv(lexer, evaluate);
        if (!evaluate)
        {
            if ((left.type == TYPE_REAL) || (right.type == TYPE_REAL))
                left = make_real_value(0.0f);
            else if (op == TOK_MINUS)
                left = make_int_value(TYPE_INT, 0);
            else
                left = make_int_value(integer_arithmetic_type(left.type, right.type), 0);
            continue;
        }

        if ((left.type == TYPE_REAL) || (right.type == TYPE_REAL))
        {
            float lhs = promote_to_real(left);
            float rhs = promote_to_real(right);
            add_root_import((op == TOK_PLUS) ? "rt.f_add" : "rt.f_sub");
            left = make_real_value((op == TOK_PLUS) ? (lhs + rhs) : (lhs - rhs));
            continue;
        }

        int32_t raw = (op == TOK_PLUS) ? (left.int_value + right.int_value) : (left.int_value - right.int_value);
        ValueType result_type;
        if (op == TOK_MINUS)
            result_type = ((left.type == TYPE_INT) || (right.type == TYPE_INT) || (raw < 0)) ? TYPE_INT : TYPE_CARD;
        else
            result_type = integer_arithmetic_type(left.type, right.type);

        if ((result_type != TYPE_INT) && (raw < 0))
            fatal_at(lexer->line_no, "unsigned result became negative");
        left = make_int_value(result_type, raw);
    }
    return left;
}

static Value parse_expression(Lexer* lexer, bool evaluate)
{
    Value left = parse_addsub(lexer, evaluate);
    if ((lexer->token.kind == TOK_EQ) || (lexer->token.kind == TOK_NE) ||
        (lexer->token.kind == TOK_LT) || (lexer->token.kind == TOK_LE) ||
        (lexer->token.kind == TOK_GT) || (lexer->token.kind == TOK_GE))
    {
        TokenKind op = lexer->token.kind;
        lexer_next(lexer);
        Value right = parse_addsub(lexer, evaluate);
        Value result;
        if (!evaluate)
            return make_int_value(TYPE_CARD, 0);

        bool comparison;
        if ((left.type == TYPE_REAL) || (right.type == TYPE_REAL))
        {
            float lhs = promote_to_real(left);
            float rhs = promote_to_real(right);
            add_root_import("rt.f_cmp");
            if (op == TOK_EQ)
                comparison = (lhs == rhs);
            else if (op == TOK_NE)
                comparison = (lhs != rhs);
            else if (op == TOK_LT)
                comparison = (lhs < rhs);
            else if (op == TOK_LE)
                comparison = (lhs <= rhs);
            else if (op == TOK_GT)
                comparison = (lhs > rhs);
            else
                comparison = (lhs >= rhs);
            return make_int_value(TYPE_CARD, comparison ? 1 : 0);
        }

        if (op == TOK_EQ)
            comparison = (left.int_value == right.int_value);
        else if (op == TOK_NE)
            comparison = (left.int_value != right.int_value);
        else if (op == TOK_LT)
            comparison = (left.int_value < right.int_value);
        else if (op == TOK_LE)
            comparison = (left.int_value <= right.int_value);
        else if (op == TOK_GT)
            comparison = (left.int_value > right.int_value);
        else
            comparison = (left.int_value >= right.int_value);
        result = make_int_value(TYPE_CARD, comparison ? 1 : 0);
        return result;
    }
    return left;
}

static ValueType token_to_type(TokenKind kind)
{
    if (kind == TOK_BYTE)
        return TYPE_BYTE;
    if (kind == TOK_CARD)
        return TYPE_CARD;
    if (kind == TOK_INT)
        return TYPE_INT;
    return TYPE_REAL;
}

static bool line_is_decl_start(const SourceLine* line)
{
    Lexer lexer;
    lexer_init(&lexer, line);
    return (lexer.token.kind == TOK_BYTE) || (lexer.token.kind == TOK_CARD) ||
           (lexer.token.kind == TOK_INT) || (lexer.token.kind == TOK_REAL) ||
           (lexer.token.kind == TOK_REU);
}

static void parse_module_line(const SourceLine* line)
{
    Lexer lexer;
    lexer_init(&lexer, line);
    expect_token(&lexer, TOK_MODULE, "expected MODULE");
    lexer_next(&lexer);
    if (lexer.token.kind == TOK_IDENT)
        lexer_next(&lexer);
    expect_eof(&lexer);
}

static void parse_proc_line(const SourceLine* line)
{
    Lexer lexer;
    lexer_init(&lexer, line);
    expect_token(&lexer, TOK_PROC, "expected PROC");
    lexer_next(&lexer);
    expect_token(&lexer, TOK_IDENT, "expected procedure name");
    if (strcmp(lexer.token.text, "MAIN") != 0)
        fatal_at(line->line_no, "only PROC main() is supported");
    lexer_next(&lexer);
    expect_token(&lexer, TOK_LPAREN, "expected '(' ");
    lexer_next(&lexer);
    expect_token(&lexer, TOK_RPAREN, "expected ')' ");
    lexer_next(&lexer);
    expect_eof(&lexer);
}

static void parse_decl_line(const SourceLine* line)
{
    Lexer lexer;
    lexer_init(&lexer, line);
    ValueType type = token_to_type(lexer.token.kind);
    lexer_next(&lexer);

    for (;;)
    {
        expect_token(&lexer, TOK_IDENT, "expected variable name");
        declare_symbol(lexer.token.text, type, line->line_no);
        lexer_next(&lexer);
        if (lexer.token.kind != TOK_COMMA)
            break;
        lexer_next(&lexer);
    }

    expect_eof(&lexer);
}

static void parse_reu_decl_line(const SourceLine* line)
{
    Lexer lexer;
    lexer_init(&lexer, line);
    expect_token(&lexer, TOK_REU, "expected REU");
    lexer_next(&lexer);
    expect_token(&lexer, TOK_BYTE, "only REU BYTE ARRAY is supported");
    lexer_next(&lexer);
    expect_token(&lexer, TOK_IDENT, "expected ARRAY");
    if (strcmp(lexer.token.text, "ARRAY") != 0)
        fatal_at(line->line_no, "expected ARRAY");
    lexer_next(&lexer);
    expect_token(&lexer, TOK_IDENT, "expected REU array name");
    if (find_reu_array(lexer.token.text))
        fatal_at(line->line_no, "duplicate REU array");
    if (reu_array_count >= MAX_REU_ARRAYS)
        fatal("too many REU arrays");
    strcpy(reu_arrays[reu_array_count].name, lexer.token.text);
    lexer_next(&lexer);
    expect_token(&lexer, TOK_LPAREN, "expected '(' after REU array name");
    lexer_next(&lexer);
    expect_token(&lexer, TOK_NUMBER, "expected REU array length");
    if (lexer.token.is_real || (lexer.token.number <= 0))
        fatal_at(line->line_no, "REU array length must be positive");
    reu_arrays[reu_array_count].length = (uint32_t)lexer.token.number;
    lexer_next(&lexer);
    expect_token(&lexer, TOK_RPAREN, "expected ')' after REU array length");
    lexer_next(&lexer);
    expect_eof(&lexer);

    if (!reu_alloc(reu_arrays[reu_array_count].length, &reu_arrays[reu_array_count].handle))
        fatal_at(line->line_no, "REU allocation failed");
    add_root_import("rt.reu_alloc");
    reu_array_count++;
}

static void parse_overlay_header(const SourceLine* line, OverlayBlock* overlay)
{
    Lexer lexer;
    lexer_init(&lexer, line);
    expect_token(&lexer, TOK_OVERLAY, "expected OVERLAY");
    lexer_next(&lexer);
    expect_token(&lexer, TOK_IDENT, "expected overlay name");
    strcpy(overlay->name, lexer.token.text);
    lexer_next(&lexer);
    expect_eof(&lexer);
}

static void execute_block(uint16_t* index, bool executing, bool stop_on_fi, bool* saw_return);

static void execute_statement(uint16_t* index, bool executing)
{
    SourceLine* line = &lines[*index];
    Lexer lexer;
    lexer_init(&lexer, line);

    if ((lexer.token.kind == TOK_PRINT) || (lexer.token.kind == TOK_PRINTE))
    {
        bool newline = (lexer.token.kind == TOK_PRINTE);
        lexer_next(&lexer);
        expect_token(&lexer, TOK_LPAREN, "expected '(' after Print");
        lexer_next(&lexer);
        expect_token(&lexer, TOK_STRING, "Print requires a string literal");
        if (executing)
            add_action(lexer.token.text, newline);
        lexer_next(&lexer);
        expect_token(&lexer, TOK_RPAREN, "expected ')' after Print");
        lexer_next(&lexer);
        expect_eof(&lexer);
        (*index)++;
        return;
    }

    if ((lexer.token.kind == TOK_PRINTI) || (lexer.token.kind == TOK_PRINTIE))
    {
        bool newline = (lexer.token.kind == TOK_PRINTIE);
        char formatted[16];
        lexer_next(&lexer);
        expect_token(&lexer, TOK_LPAREN, "expected '(' after PrintI");
        lexer_next(&lexer);
        Value value = parse_expression(&lexer, executing);
        expect_token(&lexer, TOK_RPAREN, "expected ')' after PrintI");
        lexer_next(&lexer);
        expect_eof(&lexer);
        if (executing)
        {
            if (value.type == TYPE_REAL)
                fatal_at(line->line_no, "PrintI requires an integer expression");
            used_format_int = true;
            format_int32(value.int_value, formatted);
            add_action(formatted, newline);
        }
        (*index)++;
        return;
    }

    if ((lexer.token.kind == TOK_PRINTR) || (lexer.token.kind == TOK_PRINTRE))
    {
        bool newline = (lexer.token.kind == TOK_PRINTRE);
        char formatted[32];
        lexer_next(&lexer);
        expect_token(&lexer, TOK_LPAREN, "expected '(' after PrintR");
        lexer_next(&lexer);
        Value value = parse_expression(&lexer, executing);
        expect_token(&lexer, TOK_RPAREN, "expected ')' after PrintR");
        lexer_next(&lexer);
        expect_eof(&lexer);
        if (executing)
        {
            used_format_real = true;
            format_real32(promote_to_real(value), formatted);
            add_action(formatted, newline);
        }
        (*index)++;
        return;
    }

    if (lexer.token.kind == TOK_IF)
    {
        lexer_next(&lexer);
        Value condition = parse_expression(&lexer, executing);
        expect_token(&lexer, TOK_THEN, "expected THEN");
        lexer_next(&lexer);
        expect_eof(&lexer);
        (*index)++;
        bool inner_return = false;
        execute_block(index, executing && value_is_true(condition), true, &inner_return);
        if (*index >= line_count)
            fatal_at(line->line_no, "missing FI");
        (*index)++;
        return;
    }

    if ((lexer.token.kind == TOK_REUPOKE8) || (lexer.token.kind == TOK_REUPOKE16))
    {
        bool wide = (lexer.token.kind == TOK_REUPOKE16);
        char name[MAX_IDENT_LEN + 1];
        lexer_next(&lexer);
        expect_token(&lexer, TOK_LPAREN, "expected '(' after REUPOKE");
        lexer_next(&lexer);
        expect_token(&lexer, TOK_IDENT, "expected REU array name");
        strcpy(name, lexer.token.text);
        lexer_next(&lexer);
        expect_token(&lexer, TOK_COMMA, "expected ',' after REU array name");
        lexer_next(&lexer);
        Value index_value = parse_expression(&lexer, executing);
        expect_token(&lexer, TOK_COMMA, "expected ',' after REU index");
        lexer_next(&lexer);
        Value data_value = parse_expression(&lexer, executing);
        expect_token(&lexer, TOK_RPAREN, "expected ')' after REUPOKE");
        lexer_next(&lexer);
        expect_eof(&lexer);

        if (executing)
        {
            if (index_value.type == TYPE_REAL)
                fatal_at(line->line_no, "REU indexes must be integer expressions");
            if (data_value.type == TYPE_REAL)
                fatal_at(line->line_no, "REU poke requires an integer value");
            ReuArray* array = find_reu_array(name);
            if (!array)
                fatal_at(line->line_no, "unknown REU array");
            if ((index_value.int_value < 0) || ((uint32_t)index_value.int_value >= array->length) ||
                (wide && (((uint32_t)index_value.int_value + 1u) >= array->length)))
                fatal_at(line->line_no, "REU access out of bounds");

            if (wide)
            {
                add_root_import("rt.reu_poke16");
                if (!reu_poke16(array->handle, (uint32_t)index_value.int_value, (uint16_t)data_value.int_value))
                    fatal_at(line->line_no, "REU backend write failed");
            }
            else
            {
                add_root_import("rt.reu_poke8");
                if (!reu_poke8(array->handle, (uint32_t)index_value.int_value, (uint8_t)data_value.int_value))
                    fatal_at(line->line_no, "REU backend write failed");
            }
        }
        (*index)++;
        return;
    }

    if (lexer.token.kind == TOK_OVERLAYCALL)
    {
        char name[MAX_IDENT_LEN + 1];
        lexer_next(&lexer);
        expect_token(&lexer, TOK_LPAREN, "expected '(' after OverlayCall");
        lexer_next(&lexer);
        expect_token(&lexer, TOK_IDENT, "expected overlay name");
        strcpy(name, lexer.token.text);
        lexer_next(&lexer);
        expect_token(&lexer, TOK_RPAREN, "expected ')' after OverlayCall");
        lexer_next(&lexer);
        expect_eof(&lexer);
        if (executing)
        {
            OverlayBlock* overlay = find_overlay(name);
            if (!overlay)
                fatal_at(line->line_no, "unknown overlay");
            add_root_import("rt.ovl_load");
            add_root_import("rt.ovl_call");
            remember_overlay_usage(overlay);

            uint16_t overlay_index = overlay->start_index;
            while (overlay_index < overlay->end_index)
                execute_statement(&overlay_index, true);
        }
        (*index)++;
        return;
    }

    if (lexer.token.kind == TOK_IDENT)
    {
        char name[MAX_IDENT_LEN + 1];
        strcpy(name, lexer.token.text);
        lexer_next(&lexer);
        expect_token(&lexer, TOK_EQ, "expected '='");
        lexer_next(&lexer);
        Value value = parse_expression(&lexer, executing);
        expect_eof(&lexer);
        if (executing)
        {
            Symbol* symbol = find_symbol(name);
            if (!symbol)
                fatal_at(line->line_no, "unknown variable");
            assign_symbol_value(symbol, value, line->line_no);
        }
        (*index)++;
        return;
    }

    fatal_at(line->line_no, "unsupported statement");
}

static void execute_block(uint16_t* index, bool executing, bool stop_on_fi, bool* saw_return)
{
    while (*index < line_count)
    {
        Lexer lexer;
        lexer_init(&lexer, &lines[*index]);

        if (lexer.token.kind == TOK_FI)
        {
            if (!stop_on_fi)
                fatal_at(lines[*index].line_no, "unexpected FI");
            return;
        }

        if (lexer.token.kind == TOK_RETURN)
        {
            lexer_next(&lexer);
            expect_eof(&lexer);
            if (stop_on_fi)
                fatal_at(lines[*index].line_no, "RETURN inside IF is not supported");
            *saw_return = true;
            (*index)++;
            return;
        }

        execute_statement(index, executing);
    }

    if (stop_on_fi)
        fatal("unterminated IF block");
}

static void compile_program(void)
{
    uint16_t index = 0;
    bool saw_return = false;

    reu_backend_reset();
    symbol_count = 0;
    reu_array_count = 0;
    overlay_count = 0;
    used_overlay_count = 0;
    action_count = 0;
    text_pool_len = 0;
    overlay_blob_len = 0;
    root_import_count = 0;
    used_format_int = false;
    used_format_real = false;

    if ((index < line_count) && (line_is_decl_start(&lines[index]) == false))
    {
        Lexer lexer;
        lexer_init(&lexer, &lines[index]);
        if (lexer.token.kind == TOK_MODULE)
        {
            parse_module_line(&lines[index]);
            index++;
        }
    }

    while (index < line_count)
    {
        Lexer lexer;
        lexer_init(&lexer, &lines[index]);
        if (lexer.token.kind != TOK_OVERLAY)
            break;
        if (overlay_count >= MAX_OVERLAYS)
            fatal("too many overlays");
        parse_overlay_header(&lines[index], &overlays[overlay_count]);
        overlays[overlay_count].start_index = (uint16_t)(index + 1u);
        index++;
        while (index < line_count)
        {
            Lexer end_lexer;
            lexer_init(&end_lexer, &lines[index]);
            if (end_lexer.token.kind == TOK_ENDOVERLAY)
                break;
            index++;
        }
        if (index >= line_count)
            fatal("OVERLAY without ENDOVERLAY");
        overlays[overlay_count].end_index = index;
        overlay_count++;
        index++;
    }

    if (index >= line_count)
        fatal("empty source");
    parse_proc_line(&lines[index]);
    index++;

    while ((index < line_count) && line_is_decl_start(&lines[index]))
    {
        Lexer lexer;
        lexer_init(&lexer, &lines[index]);
        if (lexer.token.kind == TOK_REU)
            parse_reu_decl_line(&lines[index]);
        else
            parse_decl_line(&lines[index]);
        index++;
    }

    execute_block(&index, true, false, &saw_return);
    if (!saw_return)
        fatal("missing RETURN");
    if (index != line_count)
        fatal_at(lines[index].line_no, "unexpected text after RETURN");

    resolve_runtime_modules();
}

int actc_compile_filename(const char* source_name)
{
    char output_name[13];
    char map_name[13];
    uint16_t avm_len;

    replace_extension_from_source(source_name, ".avm", output_name);
    replace_extension_from_source(source_name, ".map", map_name);

    read_source_file(source_name);
    preprocess_source();
    compile_program();
    emit_payload(&avm_len);
    write_binary_file(output_name, avm_buffer, avm_len);
    write_map_file(map_name);

    print_cstr("wrote ");
    print_cstr(output_name);
    print_cstr(" and ");
    print_cstr(map_name);
    crlf();
    return 0;
}

#ifndef ACTC_LIBRARY
int main(void)
{
    char source_name[13];
    source_filename_from_primary_fcb(source_name);
    return actc_compile_filename(source_name);
}
#endif
