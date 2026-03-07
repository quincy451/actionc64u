#include <stdbool.h>
#include <cpm.h>
#include <stdint.h>
#include <string.h>

#define MAX_SOURCE_BYTES 4096
#define MAX_LINES 256
#define MAX_ACTIONS 128
#define MAX_TEXT_POOL 2048
#define MAX_AVM_BYTES 4096
#define MAX_SYMBOLS 64
#define MAX_IDENT_LEN 31
#define MAX_TOKEN_TEXT 255
#define MAX_MODULES 8
#define MAX_MODULE_IMPORTS 4
#define MAX_MODULE_PAYLOAD 96
#define MAX_MANIFEST_BYTES 512
#define MAX_MAP_BYTES 1024
#define MAX_ROOT_IMPORTS 8
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
    int32_t value;
    bool assigned;
} Symbol;

typedef struct {
    ValueType type;
    int32_t value;
} Value;

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
    TOK_IF,
    TOK_THEN,
    TOK_FI,
    TOK_BYTE,
    TOK_CARD,
    TOK_INT,
} TokenKind;

typedef struct {
    TokenKind kind;
    char text[MAX_TOKEN_TEXT + 1];
    int32_t number;
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
static DiskModule modules[MAX_MODULES];
static uint8_t module_count;
static DiskModule* included_modules[MAX_MODULES];
static uint8_t included_module_count;
static uint8_t module_blob[MAX_AVM_BYTES];
static uint16_t module_blob_len;
static char manifest_buffer[MAX_MANIFEST_BYTES];
static char map_buffer[MAX_MAP_BYTES];
static char root_imports[MAX_ROOT_IMPORTS][MAX_IDENT_LEN + 1];
static uint8_t root_import_count;
static bool used_format_int;

static const Keyword KEYWORDS[] = {
    {"MODULE", TOK_MODULE},
    {"PROC", TOK_PROC},
    {"RETURN", TOK_RETURN},
    {"PRINT", TOK_PRINT},
    {"PRINTE", TOK_PRINTE},
    {"PRINTI", TOK_PRINTI},
    {"PRINTIE", TOK_PRINTIE},
    {"IF", TOK_IF},
    {"THEN", TOK_THEN},
    {"FI", TOK_FI},
    {"BYTE", TOK_BYTE},
    {"CARD", TOK_CARD},
    {"INT", TOK_INT},
};

static const char* LIBRARY_FILES[] = {
    "libpstr.mod",
    "libplin.mod",
    "libfint.mod",
};

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

static void emit_payload(uint16_t* out_len)
{
    uint16_t code_len = (uint16_t)(action_count * 6u + 3u);
    uint16_t string_base = code_len;
    uint16_t pos = AVM_HEADER_SIZE;
    uint16_t payload_len = (uint16_t)(code_len + text_pool_len + module_blob_len);

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

static void load_manifest_file(const char* filename)
{
    if (module_count >= MAX_MODULES)
        fatal("too many library manifests");

    DiskModule* module = &modules[module_count];
    memset(module, 0, sizeof(*module));
    strcpy(module->filename, filename);

    read_text_file(filename, manifest_buffer, MAX_MANIFEST_BYTES, "cannot open library manifest");
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

static void load_library_manifests(void)
{
    module_count = 0;
    for (uint8_t i = 0; i < (sizeof(LIBRARY_FILES) / sizeof(LIBRARY_FILES[0])); i++)
    {
        FCB fcb;
        parse_filename(&fcb, LIBRARY_FILES[i]);
        fcb.ex = 0;
        fcb.cr = 0;
        if (cpm_open_file(&fcb) != CPME_OK)
            continue;
        cpm_close_file(&fcb);
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
    root_import_count = 0;

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
    symbols[symbol_count].value = 0;
    symbols[symbol_count].assigned = false;
    symbol_count++;
}

static ValueType arithmetic_type(ValueType left, ValueType right)
{
    if ((left == TYPE_INT) || (right == TYPE_INT))
        return TYPE_INT;
    return TYPE_CARD;
}

static int32_t coerce_to_type(ValueType target, int32_t raw, uint16_t line_no)
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

static TokenKind lookup_keyword(const char* text)
{
    for (uint8_t i = 0; i < (sizeof(KEYWORDS) / sizeof(KEYWORDS[0])); i++)
    {
        if (strcmp(text, KEYWORDS[i].name) == 0)
            return KEYWORDS[i].kind;
    }
    return TOK_IDENT;
}

static void lexer_next(Lexer* lexer)
{
    while ((*lexer->cursor == ' ') || (*lexer->cursor == '\t'))
        lexer->cursor++;

    lexer->token.text[0] = 0;
    lexer->token.number = 0;

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
    Value value;
    if (lexer->token.kind == TOK_NUMBER)
    {
        value.type = (lexer->token.number < 256) ? TYPE_BYTE : TYPE_CARD;
        value.value = lexer->token.number;
        lexer_next(lexer);
        return value;
    }

    if (lexer->token.kind == TOK_IDENT)
    {
        if (evaluate)
        {
            Symbol* symbol = find_symbol(lexer->token.text);
            if (!symbol)
                fatal_at(lexer->line_no, "unknown variable");
            if (!symbol->assigned)
                fatal_at(lexer->line_no, "variable used before assignment");
            value.type = symbol->type;
            value.value = symbol->value;
        }
        else
        {
            value.type = TYPE_CARD;
            value.value = 0;
        }
        lexer_next(lexer);
        return value;
    }

    if (lexer->token.kind == TOK_LPAREN)
    {
        lexer_next(lexer);
        value = parse_expression(lexer, evaluate);
        expect_token(lexer, TOK_RPAREN, "expected ')' ");
        lexer_next(lexer);
        return value;
    }

    fatal_at(lexer->line_no, "expected expression");
    value.type = TYPE_CARD;
    value.value = 0;
    return value;
}

static Value parse_unary(Lexer* lexer, bool evaluate)
{
    if (lexer->token.kind == TOK_MINUS)
    {
        lexer_next(lexer);
        Value operand = parse_unary(lexer, evaluate);
        if (!evaluate)
        {
            operand.type = TYPE_INT;
            operand.value = 0;
            return operand;
        }
        operand.type = TYPE_INT;
        operand.value = -operand.value;
        return operand;
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
            left.type = arithmetic_type(left.type, right.type);
            left.value = 0;
            continue;
        }

        if ((op == TOK_SLASH) && (right.value == 0))
            fatal_at(lexer->line_no, "division by zero");

        ValueType result_type = arithmetic_type(left.type, right.type);
        int32_t raw;
        if (op == TOK_STAR)
            raw = left.value * right.value;
        else if (result_type == TYPE_INT)
            raw = left.value / right.value;
        else
            raw = (int32_t)((uint32_t)left.value / (uint32_t)right.value);

        if ((result_type != TYPE_INT) && (raw < 0))
            fatal_at(lexer->line_no, "unsigned result became negative");
        left.type = result_type;
        left.value = raw;
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
            left.type = arithmetic_type(left.type, right.type);
            left.value = 0;
            continue;
        }

        int32_t raw = (op == TOK_PLUS) ? (left.value + right.value) : (left.value - right.value);
        ValueType result_type;
        if (op == TOK_MINUS)
            result_type = ((left.type == TYPE_INT) || (right.type == TYPE_INT) || (raw < 0)) ? TYPE_INT : TYPE_CARD;
        else
            result_type = arithmetic_type(left.type, right.type);

        if ((result_type != TYPE_INT) && (raw < 0))
            fatal_at(lexer->line_no, "unsigned result became negative");
        left.type = result_type;
        left.value = raw;
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
        result.type = TYPE_CARD;
        if (!evaluate)
        {
            result.value = 0;
            return result;
        }

        bool comparison;
        if (op == TOK_EQ)
            comparison = (left.value == right.value);
        else if (op == TOK_NE)
            comparison = (left.value != right.value);
        else if (op == TOK_LT)
            comparison = (left.value < right.value);
        else if (op == TOK_LE)
            comparison = (left.value <= right.value);
        else if (op == TOK_GT)
            comparison = (left.value > right.value);
        else
            comparison = (left.value >= right.value);
        result.value = comparison ? 1 : 0;
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
    return TYPE_INT;
}

static bool line_is_decl_start(const SourceLine* line)
{
    Lexer lexer;
    lexer_init(&lexer, line);
    return (lexer.token.kind == TOK_BYTE) || (lexer.token.kind == TOK_CARD) || (lexer.token.kind == TOK_INT);
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
            used_format_int = true;
            format_int32(value.value, formatted);
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
        execute_block(index, executing && (condition.value != 0), true, &inner_return);
        if (*index >= line_count)
            fatal_at(line->line_no, "missing FI");
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
            symbol->value = coerce_to_type(symbol->type, value.value, line->line_no);
            symbol->assigned = true;
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

    symbol_count = 0;
    action_count = 0;
    text_pool_len = 0;
    used_format_int = false;

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

    if (index >= line_count)
        fatal("empty source");
    parse_proc_line(&lines[index]);
    index++;

    while ((index < line_count) && line_is_decl_start(&lines[index]))
    {
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
