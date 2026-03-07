#include <stdbool.h>
#include <cpm.h>
#include <stdint.h>
#include <string.h>

#define MAX_COMMAND_LEN 80
#define MAX_SUBMIT_COMMANDS 4

typedef struct {
    char text[MAX_COMMAND_LEN];
} SubmitCommand;

int actc_compile_filename(const char* source_name);
int vm_run_filename(const char* filename);

static void print_cstr(const char* s)
{
    while (*s)
        cpm_conout((uint8_t)*s++);
}

static void crlf(void)
{
    print_cstr("\r\n");
}

static char upcase_ascii(char ch)
{
    if ((ch >= 'a') && (ch <= 'z'))
        return (char)(ch - 'a' + 'A');
    return ch;
}

static char lowcase_ascii(char ch)
{
    if ((ch >= 'A') && (ch <= 'Z'))
        return (char)(ch - 'A' + 'a');
    return ch;
}

static bool equals_ignore_case(const char* left, const char* right)
{
    while (*left && *right)
    {
        if (upcase_ascii(*left++) != upcase_ascii(*right++))
            return false;
    }
    return (*left == 0) && (*right == 0);
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
    cpm_parse_filename(name);
}

static bool file_exists(const char* name)
{
    FCB fcb;
    parse_filename(&fcb, name);
    fcb.ex = 0;
    fcb.cr = 0;
    if (cpm_open_file(&fcb) != CPME_OK)
        return false;
    cpm_close_file(&fcb);
    return true;
}

static void derive_avm_name(const char* source_name, char* out)
{
    uint8_t stem_len = 0;
    while (source_name[stem_len] && (source_name[stem_len] != '.') && (stem_len < 8))
    {
        out[stem_len] = lowcase_ascii(source_name[stem_len]);
        stem_len++;
    }
    out[stem_len] = 0;
    strcat(out, ".avm");
}

static void lowercase_copy(char* out, const char* in)
{
    while (*in)
    {
        *out++ = lowcase_ascii(*in++);
    }
    *out = 0;
}

static bool can_chain_external_tools(void)
{
    return file_exists("submit.com") || file_exists("ccp.sys");
}

static void print_dir_entry(const FCB* fcb)
{
    for (uint8_t i = 0; i < 11; i++)
    {
        uint8_t ch = fcb->f[i] & 0x7f;
        if (ch == ' ')
            continue;
        if (i == 8)
            cpm_conout('.');
        cpm_conout(ch);
    }
    crlf();
}

static void list_directory(void)
{
    FCB search;
    uint8_t last_name[11];
    bool have_last = false;

    parse_filename(&search, "*.*");
    search.ex = '?';
    cpm_set_dma(cpm_default_dma);

    uint8_t result = cpm_findfirst(&search);
    while (result != 0xff)
    {
        FCB* match = ((FCB*)cpm_default_dma) + result;
        if (!have_last || (memcmp(last_name, match->f, sizeof(last_name)) != 0))
        {
            memcpy(last_name, match->f, sizeof(last_name));
            have_last = true;
            print_dir_entry(match);
        }
        result = cpm_findnext(&search);
    }
}

static void type_file(const char* name)
{
    FCB fcb;
    parse_filename(&fcb, name);
    fcb.ex = 0;
    fcb.cr = 0;
    if (cpm_open_file(&fcb) != CPME_OK)
    {
        print_cstr("ACTMON: cannot open file\r\n");
        return;
    }

    for (;;)
    {
        cpm_set_dma(cpm_default_dma);
        if (cpm_read_sequential(&fcb) != CPME_OK)
            break;
        for (uint8_t i = 0; i < 128; i++)
        {
            uint8_t ch = cpm_default_dma[i];
            if ((ch == 0) || (ch == 0x1a))
            {
                cpm_close_file(&fcb);
                return;
            }
            cpm_conout(ch);
        }
    }

    cpm_close_file(&fcb);
}

static void write_submit_file(const SubmitCommand* commands, uint8_t count)
{
    FCB out_fcb = {
        1,
        "$$$     SUB"
    };

    cpm_delete_file(&out_fcb);
    out_fcb.ex = 0;
    out_fcb.cr = 0;
    if (cpm_make_file(&out_fcb) != CPME_OK)
    {
        print_cstr("ACTMON: cannot create $$$.SUB\r\n");
        cpm_warmboot();
    }

    while (count)
    {
        const char* line = commands[--count].text;
        uint8_t len = (uint8_t)strlen(line);
        memset(cpm_default_dma, 0, 128);
        cpm_default_dma[0] = 126;
        cpm_default_dma[1] = len;
        memcpy(&cpm_default_dma[2], line, len);
        cpm_set_dma(cpm_default_dma);
        if (cpm_write_sequential(&out_fcb) != CPME_OK)
        {
            print_cstr("ACTMON: cannot write $$$.SUB\r\n");
            cpm_warmboot();
        }
    }

    cpm_close_file(&out_fcb);
}

static void queue_and_warmboot(SubmitCommand* commands, uint8_t count)
{
    write_submit_file(commands, count);
    cpm_warmboot();
}

static void print_help(void)
{
    print_cstr("ACTMON COMMANDS\r\n");
    print_cstr("  HELP\r\n");
    print_cstr("  EDIT <file>\r\n");
    print_cstr("  COMPILE <file>\r\n");
    print_cstr("  RUN <file.avm>\r\n");
    print_cstr("  BUILD <file>\r\n");
    print_cstr("  DIR\r\n");
    print_cstr("  TYPE <file>\r\n");
    print_cstr("  EXIT\r\n");
}

static bool handle_command(char* line, bool reenter_shell)
{
    SubmitCommand commands[MAX_SUBMIT_COMMANDS];
    char* cursor = trim(line);
    char lowered_arg[13];
    if (!*cursor)
        return true;

    char* command = cursor;
    while (*cursor && (*cursor != ' '))
        cursor++;
    if (*cursor)
        *cursor++ = 0;
    char* arg = trim(cursor);
    if (!*arg)
        arg = 0;
    else
    {
        lowercase_copy(lowered_arg, arg);
        arg = lowered_arg;
    }

    if (equals_ignore_case(command, "HELP"))
    {
        print_help();
        return true;
    }

    if (equals_ignore_case(command, "EXIT"))
        return false;

    if (equals_ignore_case(command, "COMPILE"))
    {
        if (!arg)
        {
            print_cstr("ACTMON: COMPILE needs a file\r\n");
            return true;
        }
        actc_compile_filename(arg);
        return true;
    }

    if (equals_ignore_case(command, "RUN"))
    {
        if (!arg)
        {
            print_cstr("ACTMON: RUN needs a file\r\n");
            return true;
        }
        vm_run_filename(arg);
        return true;
    }

    if (equals_ignore_case(command, "BUILD"))
    {
        if (!arg)
        {
            print_cstr("ACTMON: BUILD needs a file\r\n");
            return true;
        }
        char avm_name[13];
        derive_avm_name(arg, avm_name);
        actc_compile_filename(arg);
        vm_run_filename(avm_name);
        return true;
    }

    if (equals_ignore_case(command, "EDIT"))
    {
        if (!arg)
        {
            print_cstr("ACTMON: EDIT needs a file\r\n");
            return true;
        }
        const char* editor = 0;
        if (file_exists("qe.com"))
            editor = "qe";
        else if (file_exists("bedit.com"))
            editor = "bedit";
        if (!editor)
        {
            print_cstr("ACTMON: no editor found\r\n");
            return true;
        }
        if (!can_chain_external_tools())
        {
            print_cstr("ACTMON: editor found but CCP chaining is unavailable\r\n");
            return true;
        }
        strcpy(commands[0].text, editor);
        strcat(commands[0].text, " ");
        strcat(commands[0].text, arg);
        if (reenter_shell)
        {
            strcpy(commands[1].text, "actmon");
            queue_and_warmboot(commands, 2);
        }
        queue_and_warmboot(commands, 1);
    }

    if (equals_ignore_case(command, "DIR"))
    {
        list_directory();
        return true;
    }

    if (equals_ignore_case(command, "TYPE"))
    {
        if (!arg)
        {
            print_cstr("ACTMON: TYPE needs a file\r\n");
            return true;
        }
        type_file(arg);
        return true;
    }

    print_cstr("ACTMON: unknown command\r\n");
    return true;
}

int main(void)
{
    if (cpm_cmdlinelen)
    {
        cpm_cmdline[cpm_cmdlinelen] = 0;
        handle_command(cpm_cmdline, false);
        return 0;
    }

    for (;;)
    {
        char line_buffer[130];
        print_cstr("ACTMON> ");
        line_buffer[0] = 126;
        line_buffer[1] = 0;
        cpm_readline((uint8_t*)line_buffer);
        crlf();
        line_buffer[(uint8_t)line_buffer[1] + 2] = 0;
        if (!handle_command(line_buffer + 2, true))
            return 0;
    }
}
