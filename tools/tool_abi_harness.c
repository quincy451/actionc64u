#define _POSIX_C_SOURCE 200809L

#include <ctype.h>
#include <dirent.h>
#include <errno.h>
#include <limits.h>
#include <setjmp.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include "lib6502.h"

#define CMDLINE_ADDR 0xCF80
#define RTS_STUB_ADDR 0xFFF0
#define STOP_STUB_ADDR 0xFFF2
#define KERNAL_READST 0xFFB7
#define KERNAL_SETLFS 0xFFBA
#define KERNAL_SETNAM 0xFFBD
#define KERNAL_OPEN 0xFFC0
#define KERNAL_CLOSE 0xFFC3
#define KERNAL_CHKIN 0xFFC6
#define KERNAL_CHKOUT 0xFFC9
#define KERNAL_CLRCHN 0xFFCC
#define KERNAL_CHRIN 0xFFCF
#define KERNAL_CHROUT 0xFFD2
#define KERNAL_BRK_STUB 0xFFE0
#define REU_COMMAND 0xDF01
#define REU_C64ADDR_LO 0xDF02
#define REU_C64ADDR_HI 0xDF03
#define REU_REUADDR_LO 0xDF04
#define REU_REUADDR_HI 0xDF05
#define REU_REUADDR_BANK 0xDF06
#define REU_COUNT_LO 0xDF07
#define REU_COUNT_HI 0xDF08
#define REU_TRIGGER 0xFF00
#define REU_STORE 0xEC
#define REU_FETCH 0xED
#define TOOL_ABI_FILE_NAME_LO 0xCDC6
#define TOOL_ABI_FILE_NAME_HI 0xCDC7
#define VICE_LFN_FILE 2
#define VICE_SA_READ 2
#define MAX_OPS 1024
#define MAX_REU_TRACE_OPS 400
#define MAX_PATH_LEN 1024
#define TRACE_HEAD_LEN 16
#define STACK_WINDOW_LEN 16
#define MAX_LABELS 20000
#define MAX_DUMPS 64
#define MAX_OP_DUMPS 16
#define MAX_OP_DUMP_LEN 64
#define MAX_SIM_PUSHES 32
#define MAX_POKES 64
#define MAX_CHANNELS 16
#define MAX_KERNAL_OPS 256
#define MAX_PC_TRACE 2048
#define SIM_REU_SIZE (16u * 1024u * 1024u)

typedef struct {
    uint16_t svc_console_write_sc0;
    uint16_t svc_console_newline;
    uint16_t svc_program_get_cmdline_ptr;
    uint16_t svc_program_get_cmdline_len;
    uint16_t svc_program_exit;
    uint16_t svc_program_chain_sc0;
    uint16_t svc_file_load_sc0;
    uint16_t svc_file_save_sc0;
    uint16_t svc_file_write_begin_sc0;
    uint16_t svc_file_write_chunk_sc0;
    uint16_t svc_file_write_close_sc0;
    uint16_t svc_file_stage_reu_sc0;
    uint16_t svc_reu_read_sc0;
    uint16_t svc_reu_write_sc0;
    uint16_t svc_open_program_read_path_preserved;
    uint8_t tool_file_status_fail;
    uint8_t tool_file_status_ok;
    uint8_t tool_file_status_too_large;
    uint8_t tool_file_status_nofile;
    uint8_t tool_file_status_exists;
} ServiceAbi;

typedef struct {
    bool valid;
    bool truncated;
    uint16_t requested_len;
    uint16_t captured_len;
    uint8_t bytes[MAX_OP_DUMP_LEN];
} OpDumpValue;

typedef struct {
    char kind[5];
    char path[MAX_PATH_LEN];
    char full_path[MAX_PATH_LEN];
    uint16_t ptr;
    uint16_t limit;
    uint32_t actual_len;
    uint8_t status;
    uint8_t x_reg;
    uint8_t sp;
    uint16_t stack_rts_raw;
    uint16_t stack_rts_next;
    uint16_t approx_jsr_site;
    uint8_t params[16];
    uint8_t head[TRACE_HEAD_LEN];
    uint8_t head_len;
    uint8_t stack_window[STACK_WINDOW_LEN];
    OpDumpValue dumps[MAX_OP_DUMPS];
} FileOp;

typedef struct {
    char name[80];
    uint16_t addr;
} LabelEntry;

typedef enum {
    DUMP_BYTES = 0,
    DUMP_CSTR = 1,
} DumpKind;

typedef struct {
    DumpKind kind;
    char name[80];
    uint16_t length;
} DumpRequest;

typedef struct {
    uint16_t addr;
    uint8_t old_value;
} SavedByte;

typedef enum {
    POKE_BYTE = 0,
    POKE_WORD = 1,
    POKE_CSTR = 2,
    POKE_SCSTR = 3,
} PokeKind;

typedef struct {
    PokeKind kind;
    char name[80];
    uint16_t value;
    char text[256];
} PokeRequest;

typedef struct {
    bool open;
    bool is_write;
    bool is_cmd;
    uint8_t lfn;
    uint8_t sa;
    char raw_name[128];
    char host_path[MAX_PATH_LEN];
    uint8_t* data;
    size_t len;
    size_t cap;
    size_t pos;
} HostChannel;

typedef struct {
    char kind[8];
    uint8_t a;
    uint8_t x;
    uint8_t y;
    uint8_t sp;
    uint8_t status;
    uint8_t current_input_lfn;
    uint8_t current_output_lfn;
    char name[128];
    char path[MAX_PATH_LEN];
} KernalOp;

typedef struct {
    uint16_t pc;
    uint8_t sp;
    uint8_t a;
    uint8_t x;
    uint8_t y;
    uint8_t p;
} PcTraceEntry;

typedef struct {
    M6502* cpu;
    uint8_t mem[0x10000];
    M6502_Callbacks callbacks;
    ServiceAbi abi;
    char workspace[MAX_PATH_LEN];
    char program_dir[MAX_PATH_LEN];
    char cmdline[256];
    char chain_command[32];
    bool chain_requested;
    uint8_t exit_status;
    bool exited;
    bool hit_limit;
    uint64_t steps;
    jmp_buf escape;
    char* console;
    size_t console_len;
    size_t console_cap;
    FileOp ops[MAX_OPS];
    size_t op_count;
    size_t reu_trace_op_count;
    LabelEntry labels[MAX_LABELS];
    size_t label_count;
    DumpRequest dumps[MAX_DUMPS];
    size_t dump_count;
    DumpRequest op_dumps[MAX_OP_DUMPS];
    size_t op_dump_count;
    PokeRequest pokes[MAX_POKES];
    size_t poke_count;
    uint8_t extra_load_frames;
    uint8_t extra_save_frames;
    uint8_t extra_entry_frames;
    const char* entry_label;
    uint16_t entry_addr;
    bool entry_addr_set;
    bool stop_on_pc;
    uint16_t stop_pc;
    bool break_on_pc;
    uint16_t break_pc;
    bool broke_on_pc;
    uint8_t reg_a_init;
    uint8_t reg_x_init;
    uint8_t reg_y_init;
    uint8_t reg_sp_init;
    bool reg_a_set;
    bool reg_x_set;
    bool reg_y_set;
    bool reg_sp_set;
    uint8_t pending_lfn;
    uint8_t pending_device;
    uint8_t pending_sa;
    char pending_name[128];
    uint8_t current_input_lfn;
    uint8_t current_output_lfn;
    uint8_t kernal_status;
    HostChannel channels[MAX_CHANNELS];
    FILE* stream_write_fp;
    char stream_write_path[MAX_PATH_LEN];
    uint8_t* reu;
    size_t reu_size;
    KernalOp kernal_ops[MAX_KERNAL_OPS];
    size_t kernal_op_count;
    bool trace_pc_enabled;
    uint16_t trace_pc_start;
    uint16_t trace_pc_end;
    PcTraceEntry pc_trace[MAX_PC_TRACE];
    size_t pc_trace_count;
} Harness;

static Harness* G = NULL;

static void die(const char* msg)
{
    fprintf(stderr, "%s\n", msg);
    exit(1);
}

static void die_errno(const char* msg)
{
    fprintf(stderr, "%s: %s\n", msg, strerror(errno));
    exit(1);
}

static void append_console(Harness* h, const char* text)
{
    size_t add = strlen(text);
    size_t need = h->console_len + add + 1;
    if (need > h->console_cap) {
        size_t next = h->console_cap ? h->console_cap * 2 : 256;
        while (next < need) {
            next *= 2;
        }
        char* grown = realloc(h->console, next);
        if (!grown) {
            die("realloc failed for console buffer");
        }
        h->console = grown;
        h->console_cap = next;
    }
    memcpy(h->console + h->console_len, text, add + 1);
    h->console_len += add;
}

static void append_console_char(Harness* h, char c)
{
    char s[2] = {c, 0};
    append_console(h, s);
}

static void set_zn_flags(M6502* cpu, uint8_t value)
{
    cpu->registers->p &= (uint8_t)~(0x80u | 0x02u);
    if (value == 0) {
        cpu->registers->p |= 0x02u;
    }
    if (value & 0x80u) {
        cpu->registers->p |= 0x80u;
    }
}

static void set_carry_flag(M6502* cpu, bool carry)
{
    if (carry) {
        cpu->registers->p |= 0x01u;
    } else {
        cpu->registers->p &= (uint8_t)~0x01u;
    }
}

static void record_kernal_op(Harness* h, const char* kind, M6502* cpu, const char* name, const char* path)
{
    if (h->kernal_op_count >= MAX_KERNAL_OPS) {
        return;
    }
    KernalOp* op = &h->kernal_ops[h->kernal_op_count++];
    memset(op, 0, sizeof(*op));
    snprintf(op->kind, sizeof(op->kind), "%s", kind);
    op->a = cpu->registers->a;
    op->x = cpu->registers->x;
    op->y = cpu->registers->y;
    op->sp = cpu->registers->s;
    op->status = h->kernal_status;
    op->current_input_lfn = h->current_input_lfn;
    op->current_output_lfn = h->current_output_lfn;
    if (name) {
        snprintf(op->name, sizeof(op->name), "%s", name);
    }
    if (path) {
        snprintf(op->path, sizeof(op->path), "%s", path);
    }
}

static void maybe_record_pc_trace(Harness* h)
{
    if (!h->trace_pc_enabled || h->pc_trace_count >= MAX_PC_TRACE) {
        return;
    }
    uint16_t pc = h->cpu->registers->pc;
    if (pc < h->trace_pc_start || pc > h->trace_pc_end) {
        return;
    }
    PcTraceEntry* e = &h->pc_trace[h->pc_trace_count++];
    e->pc = pc;
    e->sp = h->cpu->registers->s;
    e->a = h->cpu->registers->a;
    e->x = h->cpu->registers->x;
    e->y = h->cpu->registers->y;
    e->p = h->cpu->registers->p;
}

static bool parse_u16_value(const char* text, uint16_t* out)
{
    while (*text == ' ' || *text == '\t') {
        text++;
    }
    if (!*text) {
        return false;
    }
    char* end = NULL;
    unsigned long value = 0;
    if (text[0] == '$') {
        value = strtoul(text + 1, &end, 16);
    } else {
        int base = 0;
        for (const char* p = text; *p; p++) {
            if ((*p >= 'a' && *p <= 'f') || (*p >= 'A' && *p <= 'F')) {
                base = 16;
                break;
            }
        }
        value = strtoul(text, &end, base);
    }
    if (end == text || value > 0xFFFFUL) {
        return false;
    }
    *out = (uint16_t)value;
    return true;
}

static bool parse_u8_value(const char* text, uint8_t* out)
{
    uint16_t value = 0;
    if (!parse_u16_value(text, &value) || value > 0xFF) {
        return false;
    }
    *out = (uint8_t)value;
    return true;
}

static void load_services_inc(ServiceAbi* abi, const char* path)
{
    FILE* fp = fopen(path, "r");
    if (!fp) {
        die_errno("unable to open services include");
    }
    char line[256];
    while (fgets(line, sizeof(line), fp)) {
        char name[80];
        char value[80];
        if (sscanf(line, " %79[^= ] = %79s", name, value) != 2) {
            continue;
        }
        if (strcmp(name, "svc_console_write_sc0") == 0) {
            parse_u16_value(value, &abi->svc_console_write_sc0);
        } else if (strcmp(name, "svc_console_newline") == 0) {
            parse_u16_value(value, &abi->svc_console_newline);
        } else if (strcmp(name, "svc_program_get_cmdline_ptr") == 0) {
            parse_u16_value(value, &abi->svc_program_get_cmdline_ptr);
        } else if (strcmp(name, "svc_program_get_cmdline_len") == 0) {
            parse_u16_value(value, &abi->svc_program_get_cmdline_len);
        } else if (strcmp(name, "svc_program_exit") == 0) {
            parse_u16_value(value, &abi->svc_program_exit);
        } else if (strcmp(name, "svc_program_chain_sc0") == 0) {
            parse_u16_value(value, &abi->svc_program_chain_sc0);
        } else if (strcmp(name, "svc_file_load_sc0") == 0) {
            parse_u16_value(value, &abi->svc_file_load_sc0);
        } else if (strcmp(name, "svc_file_save_sc0") == 0) {
            parse_u16_value(value, &abi->svc_file_save_sc0);
        } else if (strcmp(name, "svc_file_write_begin_sc0") == 0) {
            parse_u16_value(value, &abi->svc_file_write_begin_sc0);
        } else if (strcmp(name, "svc_file_write_chunk_sc0") == 0) {
            parse_u16_value(value, &abi->svc_file_write_chunk_sc0);
        } else if (strcmp(name, "svc_file_write_close_sc0") == 0) {
            parse_u16_value(value, &abi->svc_file_write_close_sc0);
        } else if (strcmp(name, "svc_file_stage_reu_sc0") == 0) {
            parse_u16_value(value, &abi->svc_file_stage_reu_sc0);
        } else if (strcmp(name, "svc_reu_read_sc0") == 0) {
            parse_u16_value(value, &abi->svc_reu_read_sc0);
        } else if (strcmp(name, "svc_reu_write_sc0") == 0) {
            parse_u16_value(value, &abi->svc_reu_write_sc0);
        } else if (strcmp(name, "svc_open_program_read_path_preserved") == 0) {
            parse_u16_value(value, &abi->svc_open_program_read_path_preserved);
        } else if (strcmp(name, "tool_file_status_fail") == 0) {
            parse_u8_value(value, &abi->tool_file_status_fail);
        } else if (strcmp(name, "tool_file_status_ok") == 0) {
            parse_u8_value(value, &abi->tool_file_status_ok);
        } else if (strcmp(name, "tool_file_status_too_large") == 0) {
            parse_u8_value(value, &abi->tool_file_status_too_large);
        } else if (strcmp(name, "tool_file_status_nofile") == 0) {
            parse_u8_value(value, &abi->tool_file_status_nofile);
        } else if (strcmp(name, "tool_file_status_exists") == 0) {
            parse_u8_value(value, &abi->tool_file_status_exists);
        }
    }
    fclose(fp);
}

static void copy_truncated(char* out, size_t out_size, const char* in);
static bool join_path_components(char* out, size_t out_size, const char* left, const char* right);

static void load_ld65_labels(Harness* h, const char* path)
{
    FILE* fp = fopen(path, "r");
    if (!fp) {
        die_errno("unable to open labels file");
    }
    char line[256];
    while (fgets(line, sizeof(line), fp)) {
        char col0[16], col1[16], col2[128];
        if (sscanf(line, "%15s %15s %127s", col0, col1, col2) != 3) {
            continue;
        }
        if (h->label_count >= MAX_LABELS) {
            break;
        }
        char* end = NULL;
        unsigned long raw = strtoul(col1, &end, 16);
        if (end == col1 || raw > 0xFFFFUL) {
            continue;
        }
        uint16_t addr = (uint16_t)raw;
        LabelEntry* e = &h->labels[h->label_count++];
        copy_truncated(e->name, sizeof(e->name), col2[0] == '.' ? col2 + 1 : col2);
        e->addr = addr;
    }
    fclose(fp);
}

static bool find_label_addr(Harness* h, const char* name, uint16_t* out)
{
    for (size_t i = 0; i < h->label_count; i++) {
        if (strcmp(h->labels[i].name, name) == 0) {
            *out = h->labels[i].addr;
            return true;
        }
    }
    return false;
}

static uint16_t read_u16(Harness* h, uint16_t addr)
{
    return (uint16_t)h->mem[addr] | ((uint16_t)h->mem[(uint16_t)(addr + 1)] << 8);
}

static uint32_t read_u24(Harness* h, uint16_t addr)
{
    return (uint32_t)h->mem[addr] |
           ((uint32_t)h->mem[(uint16_t)(addr + 1)] << 8) |
           ((uint32_t)h->mem[(uint16_t)(addr + 2)] << 16);
}

static void write_result_ptr(Harness* h, uint8_t x, uint16_t value)
{
    h->mem[x] = (uint8_t)(value & 0xFF);
    h->mem[(uint8_t)(x + 1)] = (uint8_t)(value >> 8);
}

static void read_cstr_mem(Harness* h, uint16_t addr, char* out, size_t out_size)
{
    size_t i = 0;
    if (!out_size) {
        return;
    }
    while (i + 1 < out_size) {
        uint8_t c = h->mem[(uint16_t)(addr + (uint16_t)i)];
        if (!c) {
            break;
        }
        out[i++] = (char)c;
    }
    out[i] = 0;
}

static void copy_truncated(char* out, size_t out_size, const char* in)
{
    if (!out_size) {
        return;
    }
    size_t len = strlen(in);
    if (len >= out_size) {
        len = out_size - 1;
    }
    memcpy(out, in, len);
    out[len] = 0;
}

static bool join_path_components(char* out, size_t out_size, const char* left, const char* right)
{
    if (!out_size) {
        return false;
    }
    size_t left_len = strlen(left);
    size_t right_len = strlen(right);
    if (left_len > (SIZE_MAX - right_len - 2) || left_len + right_len + 2 > out_size) {
        out[0] = 0;
        return false;
    }
    memcpy(out, left, left_len);
    out[left_len] = '/';
    memcpy(out + left_len + 1, right, right_len + 1);
    return true;
}

static uint8_t ascii_to_screen_code(uint8_t c)
{
    if (c >= 'A' && c <= 'Z') {
        return (uint8_t)(c - 0x40);
    }
    return c;
}

static uint16_t read_stack_rts_raw(Harness* h, uint8_t sp)
{
    uint8_t lo = h->mem[(uint16_t)(0x0100u + (uint16_t)(uint8_t)(sp + 1u))];
    uint8_t hi = h->mem[(uint16_t)(0x0100u + (uint16_t)(uint8_t)(sp + 2u))];
    return (uint16_t)lo | ((uint16_t)hi << 8);
}

static bool ci_equal(const char* a, const char* b)
{
    while (*a && *b) {
        if (tolower((unsigned char)*a) != tolower((unsigned char)*b)) {
            return false;
        }
        a++;
        b++;
    }
    return *a == 0 && *b == 0;
}

static bool find_existing_component(const char* dir, const char* name, char* out, size_t out_size)
{
    DIR* dp = opendir(dir);
    if (!dp) {
        return false;
    }
    struct dirent* ent;
    bool found = false;
    while ((ent = readdir(dp)) != NULL) {
        if (ci_equal(ent->d_name, name)) {
            snprintf(out, out_size, "%s", ent->d_name);
            found = true;
            break;
        }
    }
    closedir(dp);
    return found;
}

static void ensure_dir_exists(const char* path)
{
    struct stat st;
    if (stat(path, &st) == 0) {
        if (!S_ISDIR(st.st_mode)) {
            die("path exists but is not a directory");
        }
        return;
    }
    if (mkdir(path, 0777) != 0 && errno != EEXIST) {
        die_errno("mkdir failed");
    }
}

static bool resolve_workspace_path(Harness* h, const char* rel, bool create_parents, char* out, size_t out_size)
{
    char current[MAX_PATH_LEN];
    copy_truncated(current, sizeof(current), h->workspace);
    char rel_copy[MAX_PATH_LEN];
    copy_truncated(rel_copy, sizeof(rel_copy), rel);
    char* save = NULL;
    char* part = strtok_r(rel_copy, "/\\", &save);
    while (part) {
        char next[MAX_PATH_LEN];
        char actual[256];
        char* upcoming = strtok_r(NULL, "/\\", &save);
        bool is_last = (upcoming == NULL);
        if (find_existing_component(current, part, actual, sizeof(actual))) {
            if (!join_path_components(next, sizeof(next), current, actual)) {
                return false;
            }
        } else {
            if (!join_path_components(next, sizeof(next), current, part)) {
                return false;
            }
            if (!is_last && create_parents) {
                ensure_dir_exists(next);
            }
        }
        copy_truncated(current, sizeof(current), next);
        part = upcoming;
    }
    copy_truncated(out, out_size, current);
    return true;
}

static bool resolve_image_absolute_path(Harness* h, const char* rel, bool create_parents, char* out, size_t out_size)
{
    const char* marker = strstr(h->workspace, "/IMAGES/");
    if (!marker) {
        return false;
    }
    size_t prefix_len = (size_t)(marker - h->workspace);
    char root[MAX_PATH_LEN];
    if (prefix_len >= sizeof(root)) {
        return false;
    }
    memcpy(root, h->workspace, prefix_len);
    root[prefix_len] = 0;
    char combined[MAX_PATH_LEN];
    snprintf(combined, sizeof(combined), "%s", rel[0] == '/' ? rel + 1 : rel);
    char saved_workspace[MAX_PATH_LEN];
    snprintf(saved_workspace, sizeof(saved_workspace), "%s", h->workspace);
    snprintf(h->workspace, sizeof(h->workspace), "%s", root);
    bool ok = resolve_workspace_path(h, combined, create_parents, out, out_size);
    snprintf(h->workspace, sizeof(h->workspace), "%s", saved_workspace);
    return ok;
}

static bool resolve_program_path(Harness* h, const char* rel, bool create_parents, char* out, size_t out_size)
{
    char saved_workspace[MAX_PATH_LEN];
    snprintf(saved_workspace, sizeof(saved_workspace), "%s", h->workspace);
    snprintf(h->workspace, sizeof(h->workspace), "%s", h->program_dir);
    bool ok = resolve_workspace_path(h, rel, create_parents, out, out_size);
    snprintf(h->workspace, sizeof(h->workspace), "%s", saved_workspace);
    return ok;
}

static bool resolve_tool_path(Harness* h, const char* rel, bool create_parents, char* out, size_t out_size)
{
    if (rel[0] == '!') {
        return resolve_program_path(h, rel + 1, create_parents, out, out_size);
    }
    return resolve_workspace_path(h, rel, create_parents, out, out_size);
}

static void copy_parent_dir(const char* path, char* out, size_t out_size)
{
    const char* slash = strrchr(path, '/');
    const char* backslash = strrchr(path, '\\');
    if (!slash || (backslash && backslash > slash)) {
        slash = backslash;
    }
    if (!slash) {
        snprintf(out, out_size, ".");
        return;
    }
    size_t len = (size_t)(slash - path);
    if (len == 0) {
        len = 1;
    }
    if (len >= out_size) {
        len = out_size - 1;
    }
    memcpy(out, path, len);
    out[len] = 0;
}

static HostChannel* find_channel(Harness* h, uint8_t lfn, bool create)
{
    HostChannel* free_slot = NULL;
    for (size_t i = 0; i < MAX_CHANNELS; i++) {
        HostChannel* ch = &h->channels[i];
        if (ch->open && ch->lfn == lfn) {
            return ch;
        }
        if (!ch->open && !free_slot) {
            free_slot = ch;
        }
    }
    if (!create || !free_slot) {
        return NULL;
    }
    memset(free_slot, 0, sizeof(*free_slot));
    free_slot->open = true;
    free_slot->lfn = lfn;
    return free_slot;
}

static void close_channel(HostChannel* ch)
{
    if (!ch->open) {
        return;
    }
    free(ch->data);
    memset(ch, 0, sizeof(*ch));
}

static void normalize_c64_name(const char* raw, char* out, size_t out_size, bool* is_write, bool* is_cmd)
{
    *is_write = false;
    *is_cmd = false;
    const char* start = raw;
    if (raw[0] == '@' && raw[1] == ':') {
        *is_write = true;
        start = raw + 2;
    } else if (raw[0] == '$' && raw[1] == ':') {
        start = raw + 2;
    } else if (raw[1] == ':') {
        *is_cmd = true;
        start = raw + 2;
    }
    size_t i = 0;
    while (start[i] && start[i] != ',' && i + 1 < out_size) {
        out[i] = start[i];
        i++;
    }
    out[i] = 0;
}

static bool resolve_kernal_path(Harness* h, const char* raw_name, bool create_parents, char* out, size_t out_size, bool* is_write, bool* is_cmd)
{
    char normalized[MAX_PATH_LEN];
    normalize_c64_name(raw_name, normalized, sizeof(normalized), is_write, is_cmd);
    if (!normalized[0]) {
        return false;
    }
    if (normalized[0] == '/') {
        return resolve_image_absolute_path(h, normalized, create_parents, out, out_size);
    }
    return resolve_workspace_path(h, normalized, create_parents, out, out_size);
}

static void write_file_bytes(const char* path, const uint8_t* data, size_t len)
{
    FILE* fp = fopen(path, "wb");
    if (!fp) {
        die_errno("unable to open output file");
    }
    if (len && fwrite(data, 1, len, fp) != len) {
        fclose(fp);
        die_errno("fwrite output failed");
    }
    fclose(fp);
}

static FileOp* record_op(Harness* h, const char* kind)
{
    if ((strcmp(kind, "rrd") == 0 || strcmp(kind, "rwr") == 0) &&
        h->reu_trace_op_count >= MAX_REU_TRACE_OPS) {
        return NULL;
    }
    if (h->op_count >= MAX_OPS) {
        return NULL;
    }
    FileOp* op = &h->ops[h->op_count++];
    memset(op, 0, sizeof(*op));
    snprintf(op->kind, sizeof(op->kind), "%s", kind);
    if (strcmp(kind, "rrd") == 0 || strcmp(kind, "rwr") == 0) {
        h->reu_trace_op_count++;
    }
    return op;
}

static bool has_logged_reu_op(Harness* h, const char* kind, uint8_t x)
{
    for (size_t i = 0; i < h->op_count; i++) {
        FileOp* op = &h->ops[i];
        if (strcmp(op->kind, kind) != 0) {
            continue;
        }
        bool match = true;
        for (size_t j = 0; j < 8; j++) {
            if (op->params[j] != h->mem[(uint8_t)(x + (uint8_t)j)]) {
                match = false;
                break;
            }
        }
        if (match) {
            return true;
        }
    }
    return false;
}

static bool has_logged_reu_write_op(Harness* h, uint8_t x, uint16_t src_ptr, uint16_t len)
{
    uint16_t head_len = len < TRACE_HEAD_LEN ? len : TRACE_HEAD_LEN;
    for (size_t i = 0; i < h->op_count; i++) {
        FileOp* op = &h->ops[i];
        if (strcmp(op->kind, "rwr") != 0) {
            continue;
        }
        bool match = true;
        for (size_t j = 0; j < 8; j++) {
            if (op->params[j] != h->mem[(uint8_t)(x + (uint8_t)j)]) {
                match = false;
                break;
            }
        }
        if (!match || op->head_len != head_len) {
            continue;
        }
        for (uint16_t j = 0; j < head_len; j++) {
            if (op->head[j] != h->mem[(uint16_t)(src_ptr + j)]) {
                match = false;
                break;
            }
        }
        if (match) {
            return true;
        }
    }
    return false;
}

static void fill_op_common(Harness* h, FileOp* op, M6502* cpu, uint8_t x, const char* rel, const char* full, uint16_t ptr, uint16_t limit)
{
    snprintf(op->path, sizeof(op->path), "%s", rel);
    snprintf(op->full_path, sizeof(op->full_path), "%s", full);
    op->ptr = ptr;
    op->limit = limit;
    op->x_reg = x;
    op->sp = cpu->registers->s;
    op->stack_rts_raw = read_stack_rts_raw(h, op->sp);
    op->stack_rts_next = (uint16_t)(op->stack_rts_raw + 1u);
    op->approx_jsr_site = (uint16_t)(op->stack_rts_raw - 2u);
    for (size_t i = 0; i < sizeof(op->params); i++) {
        op->params[i] = h->mem[(uint8_t)(x + (uint8_t)i)];
    }
    for (size_t i = 0; i < STACK_WINDOW_LEN; i++) {
        op->stack_window[i] = h->mem[(uint16_t)(0x0100u + (uint16_t)(uint8_t)(op->sp + 1u + (uint8_t)i))];
    }
}

static void fill_op_head_from_mem(Harness* h, FileOp* op, uint16_t ptr, uint16_t len)
{
    uint16_t head_len = len < TRACE_HEAD_LEN ? len : TRACE_HEAD_LEN;
    op->head_len = (uint8_t)head_len;
    for (uint16_t i = 0; i < head_len; i++) {
        op->head[i] = h->mem[(uint16_t)(ptr + i)];
    }
}

static void fill_op_head_from_buf(FileOp* op, const uint8_t* buf, uint16_t len)
{
    uint16_t head_len = len < TRACE_HEAD_LEN ? len : TRACE_HEAD_LEN;
    op->head_len = (uint8_t)head_len;
    for (uint16_t i = 0; i < head_len; i++) {
        op->head[i] = buf[i];
    }
}

static void fill_op_symbol_dumps(Harness* h, FileOp* op)
{
    for (size_t i = 0; i < h->op_dump_count; i++) {
        DumpRequest* req = &h->op_dumps[i];
        OpDumpValue* value = &op->dumps[i];
        uint16_t addr = 0;
        memset(value, 0, sizeof(*value));
        value->requested_len = req->length;
        if (!find_label_addr(h, req->name, &addr)) {
            continue;
        }
        value->valid = true;
        uint16_t want = req->length;
        if (want > MAX_OP_DUMP_LEN) {
            want = MAX_OP_DUMP_LEN;
            value->truncated = true;
        }
        if (req->kind == DUMP_CSTR) {
            uint16_t actual = 0;
            while (actual < want) {
                uint8_t c = h->mem[(uint16_t)(addr + actual)];
                value->bytes[actual++] = c;
                if (!c) {
                    break;
                }
            }
            value->captured_len = actual;
        } else {
            for (uint16_t j = 0; j < want; j++) {
                value->bytes[j] = h->mem[(uint16_t)(addr + j)];
            }
            value->captured_len = want;
        }
    }
}

static uint8_t apply_extra_frames(Harness* h, uint8_t frame_count, SavedByte* saved, size_t* saved_count)
{
    uint8_t original_sp = h->cpu->registers->s;
    *saved_count = 0;
    for (uint8_t i = 0; i < frame_count; i++) {
        if (*saved_count + 2 > MAX_SIM_PUSHES) {
            die("too many simulated stack pushes");
        }
        uint8_t hi_addr = h->cpu->registers->s;
        uint16_t abs_hi = (uint16_t)(0x0100u + hi_addr);
        saved[*saved_count].addr = abs_hi;
        saved[*saved_count].old_value = h->mem[abs_hi];
        (*saved_count)++;
        h->mem[abs_hi] = (uint8_t)(0xE0u + (i & 0x0Fu));
        h->cpu->registers->s--;

        uint8_t lo_addr = h->cpu->registers->s;
        uint16_t abs_lo = (uint16_t)(0x0100u + lo_addr);
        saved[*saved_count].addr = abs_lo;
        saved[*saved_count].old_value = h->mem[abs_lo];
        (*saved_count)++;
        h->mem[abs_lo] = (uint8_t)(0x40u + (i & 0x0Fu));
        h->cpu->registers->s--;
    }
    return original_sp;
}

static void restore_extra_frames(Harness* h, uint8_t original_sp, SavedByte* saved, size_t saved_count)
{
    for (size_t i = 0; i < saved_count; i++) {
        h->mem[saved[i].addr] = saved[i].old_value;
    }
    h->cpu->registers->s = original_sp;
}

static int kernal_setlfs(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    Harness* h = G;
    h->pending_lfn = cpu->registers->a;
    h->pending_device = cpu->registers->x;
    h->pending_sa = cpu->registers->y;
    h->kernal_status = 0;
    record_kernal_op(h, "SETLFS", cpu, NULL, NULL);
    return RTS_STUB_ADDR;
}

static int kernal_setnam(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    Harness* h = G;
    uint16_t ptr = (uint16_t)cpu->registers->x | ((uint16_t)cpu->registers->y << 8);
    uint8_t len = cpu->registers->a;
    size_t copy = len < sizeof(h->pending_name) - 1 ? len : sizeof(h->pending_name) - 1;
    for (size_t i = 0; i < copy; i++) {
        h->pending_name[i] = (char)h->mem[(uint16_t)(ptr + (uint16_t)i)];
    }
    h->pending_name[copy] = 0;
    h->kernal_status = 0;
    record_kernal_op(h, "SETNAM", cpu, h->pending_name, NULL);
    return RTS_STUB_ADDR;
}

static int kernal_open(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)cpu;
    (void)address;
    (void)data;
    Harness* h = G;
    HostChannel* ch = find_channel(h, h->pending_lfn, true);
    bool is_write = false;
    bool is_cmd = false;
    char host_path[MAX_PATH_LEN];
    if (!resolve_kernal_path(h, h->pending_name, true, host_path, sizeof(host_path), &is_write, &is_cmd)) {
        h->kernal_status = 0x04;
        record_kernal_op(h, "OPEN", cpu, h->pending_name, NULL);
        return RTS_STUB_ADDR;
    }
    close_channel(ch);
    memset(ch, 0, sizeof(*ch));
    ch->open = true;
    ch->lfn = h->pending_lfn;
    ch->sa = h->pending_sa;
    ch->is_write = is_write;
    ch->is_cmd = is_cmd;
    copy_truncated(ch->raw_name, sizeof(ch->raw_name), h->pending_name);
    copy_truncated(ch->host_path, sizeof(ch->host_path), host_path);
    if (is_cmd) {
        if (strncmp(h->pending_name, "S:", 2) == 0) {
            if (unlink(host_path) != 0 && errno != ENOENT) {
                h->kernal_status = 0x04;
                return RTS_STUB_ADDR;
            }
        } else if (strncmp(h->pending_name, "MD:", 3) == 0) {
            ensure_dir_exists(host_path);
        } else if (strncmp(h->pending_name, "RD:", 3) == 0) {
            if (rmdir(host_path) != 0 && errno != ENOENT) {
                h->kernal_status = 0x04;
                return RTS_STUB_ADDR;
            }
        }
        h->kernal_status = 0;
        record_kernal_op(h, "OPEN", cpu, h->pending_name, host_path);
        return RTS_STUB_ADDR;
    }
    if (is_write) {
        char parent[MAX_PATH_LEN];
        snprintf(parent, sizeof(parent), "%s", host_path);
        char* slash = strrchr(parent, '/');
        if (slash) {
            *slash = 0;
            ensure_dir_exists(parent);
        }
        h->kernal_status = 0;
        record_kernal_op(h, "OPEN", cpu, h->pending_name, host_path);
        return RTS_STUB_ADDR;
    }
    FILE* fp = fopen(host_path, "rb");
    if (!fp) {
        h->kernal_status = 0x04;
        record_kernal_op(h, "OPEN", cpu, h->pending_name, host_path);
        return RTS_STUB_ADDR;
    }
    if (fseek(fp, 0, SEEK_END) != 0) {
        fclose(fp);
        die_errno("fseek kernal_open failed");
    }
    long end = ftell(fp);
    if (end < 0) {
        fclose(fp);
        die_errno("ftell kernal_open failed");
    }
    if (fseek(fp, 0, SEEK_SET) != 0) {
        fclose(fp);
        die_errno("fseek rewind kernal_open failed");
    }
    ch->cap = (size_t)end;
    ch->len = (size_t)end;
    ch->data = malloc(ch->cap ? ch->cap : 1);
    if (!ch->data) {
        fclose(fp);
        die("malloc failed for kernal read channel");
    }
    if (ch->len && fread(ch->data, 1, ch->len, fp) != ch->len) {
        fclose(fp);
        die_errno("fread kernal_open failed");
    }
    fclose(fp);
    ch->pos = 0;
    h->kernal_status = 0;
    record_kernal_op(h, "OPEN", cpu, h->pending_name, host_path);
    return RTS_STUB_ADDR;
}

static int service_open_program_read_path_preserved(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    Harness* h = G;
    uint16_t name_ptr = (uint16_t)h->mem[TOOL_ABI_FILE_NAME_LO] |
                        ((uint16_t)h->mem[TOOL_ABI_FILE_NAME_HI] << 8);
    char rel[MAX_PATH_LEN];
    char host_path[MAX_PATH_LEN];
    bool is_write = false;
    bool is_cmd = false;
    read_cstr_mem(h, name_ptr, rel, sizeof(rel));
    FileOp* op = record_op(h, "load");
    HostChannel* ch = find_channel(h, VICE_LFN_FILE, true);
    if (!resolve_kernal_path(h, rel, false, host_path, sizeof(host_path), &is_write, &is_cmd) ||
        is_write || is_cmd) {
        h->kernal_status = 0x04;
        if (op) {
            fill_op_common(h, op, cpu, 0xE2, rel, "", 0, 0);
            op->status = h->abi.tool_file_status_nofile;
        }
        record_kernal_op(h, "OPEN", cpu, rel, NULL);
        set_carry_flag(cpu, true);
        return RTS_STUB_ADDR;
    }

    close_channel(ch);
    memset(ch, 0, sizeof(*ch));
    ch->open = true;
    ch->lfn = VICE_LFN_FILE;
    ch->sa = VICE_SA_READ;
    ch->is_write = false;
    ch->is_cmd = false;
    copy_truncated(ch->raw_name, sizeof(ch->raw_name), rel);
    copy_truncated(ch->host_path, sizeof(ch->host_path), host_path);

    FILE* fp = fopen(host_path, "rb");
    if (!fp) {
        h->kernal_status = 0x04;
        if (op) {
            fill_op_common(h, op, cpu, 0xE2, rel, host_path, 0, 0);
            op->status = h->abi.tool_file_status_nofile;
        }
        record_kernal_op(h, "OPEN", cpu, rel, host_path);
        set_carry_flag(cpu, true);
        return RTS_STUB_ADDR;
    }
    if (fseek(fp, 0, SEEK_END) != 0) {
        fclose(fp);
        die_errno("fseek preserved open failed");
    }
    long end = ftell(fp);
    if (end < 0) {
        fclose(fp);
        die_errno("ftell preserved open failed");
    }
    if (fseek(fp, 0, SEEK_SET) != 0) {
        fclose(fp);
        die_errno("fseek rewind preserved open failed");
    }
    ch->cap = (size_t)end;
    ch->len = (size_t)end;
    ch->data = malloc(ch->cap ? ch->cap : 1);
    if (!ch->data) {
        fclose(fp);
        die("malloc failed for preserved read channel");
    }
    if (ch->len && fread(ch->data, 1, ch->len, fp) != ch->len) {
        fclose(fp);
        die_errno("fread preserved open failed");
    }
    fclose(fp);
    ch->pos = 0;
    h->current_input_lfn = VICE_LFN_FILE;
    h->kernal_status = 0;
    if (op) {
        fill_op_common(h, op, cpu, 0xE2, rel, host_path, 0, 0);
        op->actual_len = (uint16_t)(ch->len > 0xFFFFu ? 0xFFFFu : ch->len);
        op->status = h->abi.tool_file_status_ok;
        fill_op_head_from_buf(op, ch->data, op->actual_len);
    }
    record_kernal_op(h, "OPEN", cpu, rel, host_path);
    set_carry_flag(cpu, false);
    return RTS_STUB_ADDR;
}

static int kernal_close(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    Harness* h = G;
    HostChannel* ch = find_channel(h, cpu->registers->a, false);
    if (ch && ch->open && ch->is_write && !ch->is_cmd) {
        write_file_bytes(ch->host_path, ch->data, ch->len);
    }
    if (ch) {
        close_channel(ch);
    }
    h->kernal_status = 0;
    record_kernal_op(h, "CLOSE", cpu, NULL, NULL);
    return RTS_STUB_ADDR;
}

static int kernal_chkin(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    G->current_input_lfn = cpu->registers->x;
    G->kernal_status = 0;
    record_kernal_op(G, "CHKIN", cpu, NULL, NULL);
    return RTS_STUB_ADDR;
}

static int kernal_chkout(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    G->current_output_lfn = cpu->registers->x;
    G->kernal_status = 0;
    record_kernal_op(G, "CHKOUT", cpu, NULL, NULL);
    return RTS_STUB_ADDR;
}

static int kernal_clrchn(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)cpu;
    (void)address;
    (void)data;
    G->current_input_lfn = 0;
    G->current_output_lfn = 0;
    G->kernal_status = 0;
    record_kernal_op(G, "CLRCHN", cpu, NULL, NULL);
    return RTS_STUB_ADDR;
}

static int kernal_chrin(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    Harness* h = G;
    HostChannel* ch = find_channel(h, h->current_input_lfn, false);
    if (!ch || !ch->open || ch->is_write || ch->is_cmd) {
        cpu->registers->a = 0;
        h->kernal_status = 0x40;
        set_zn_flags(cpu, cpu->registers->a);
        record_kernal_op(h, "CHRIN", cpu, NULL, NULL);
        return RTS_STUB_ADDR;
    }
    if (ch->pos >= ch->len) {
        cpu->registers->a = 0;
        h->kernal_status = 0x40;
        set_zn_flags(cpu, cpu->registers->a);
        record_kernal_op(h, "CHRIN", cpu, NULL, NULL);
        return RTS_STUB_ADDR;
    }
    cpu->registers->a = ch->data[ch->pos++];
    h->kernal_status = (ch->pos >= ch->len) ? 0x40 : 0x00;
    set_zn_flags(cpu, cpu->registers->a);
    record_kernal_op(h, "CHRIN", cpu, NULL, NULL);
    return RTS_STUB_ADDR;
}

static int kernal_chrout(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    Harness* h = G;
    if (h->current_output_lfn == 0) {
        append_console_char(h, (char)cpu->registers->a);
        h->kernal_status = 0;
        record_kernal_op(h, "CHROUT", cpu, NULL, NULL);
        return RTS_STUB_ADDR;
    }
    HostChannel* ch = find_channel(h, h->current_output_lfn, false);
    if (!ch || !ch->open || !ch->is_write || ch->is_cmd) {
        h->kernal_status = 0x04;
        record_kernal_op(h, "CHROUT", cpu, NULL, NULL);
        return RTS_STUB_ADDR;
    }
    if (ch->len + 1 > ch->cap) {
        size_t next = ch->cap ? ch->cap * 2 : 256;
        while (next < ch->len + 1) {
            next *= 2;
        }
        uint8_t* grown = realloc(ch->data, next);
        if (!grown) {
            die("realloc failed for write channel");
        }
        ch->data = grown;
        ch->cap = next;
    }
    ch->data[ch->len++] = cpu->registers->a;
    h->kernal_status = 0;
    record_kernal_op(h, "CHROUT", cpu, NULL, NULL);
    return RTS_STUB_ADDR;
}

static int kernal_readst(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    cpu->registers->a = G->kernal_status;
    set_zn_flags(cpu, cpu->registers->a);
    record_kernal_op(G, "READST", cpu, NULL, NULL);
    return RTS_STUB_ADDR;
}

static int service_console_write(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    Harness* h = G;
    uint16_t ptr = read_u16(h, cpu->registers->x);
    char text[4096];
    read_cstr_mem(h, ptr, text, sizeof(text));
    append_console(h, text);
    return RTS_STUB_ADDR;
}

static int service_console_newline(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)cpu;
    (void)address;
    (void)data;
    append_console_char(G, '\n');
    return RTS_STUB_ADDR;
}

static int service_program_get_cmdline_ptr(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    write_result_ptr(G, cpu->registers->x, CMDLINE_ADDR);
    return RTS_STUB_ADDR;
}

static int service_program_get_cmdline_len(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    write_result_ptr(G, cpu->registers->x, (uint16_t)strlen(G->cmdline));
    return RTS_STUB_ADDR;
}

static int service_program_exit(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)data;
    if (G->mem[address] == 0x00) {
        return 0;
    }
    G->exit_status = G->mem[cpu->registers->x];
    G->exited = true;
    longjmp(G->escape, 1);
}

static int service_program_chain(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    uint8_t x = cpu->registers->x;
    uint16_t command_ptr = read_u16(G, x);
    char command[256];
    read_cstr_mem(G, command_ptr, command, sizeof(command));
    size_t command_len = strlen(command);
    bool accepted = command_len > 0 && command_len <= 31;
    set_carry_flag(cpu, !accepted);
    if (accepted) {
        memcpy(G->chain_command, command, command_len + 1);
        G->chain_requested = true;
    }
    return RTS_STUB_ADDR;
}

static int service_file_load(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    Harness* h = G;
    SavedByte saved[MAX_SIM_PUSHES];
    size_t saved_count = 0;
    uint8_t original_sp = apply_extra_frames(h, h->extra_load_frames, saved, &saved_count);
    uint8_t x = cpu->registers->x;
    uint16_t name_ptr = read_u16(h, x + 0);
    uint16_t dest_ptr = read_u16(h, x + 2);
    uint16_t limit = read_u16(h, x + 4);
    char rel[MAX_PATH_LEN];
    char full[MAX_PATH_LEN];
    read_cstr_mem(h, name_ptr, rel, sizeof(rel));
    resolve_tool_path(h, rel, false, full, sizeof(full));
    FileOp* op = record_op(h, "load");
    if (op) {
        fill_op_common(h, op, cpu, x, rel, full, dest_ptr, limit);
        fill_op_symbol_dumps(h, op);
    }

    FILE* fp = fopen(full, "rb");
    if (!fp) {
        h->mem[x + 6] = h->abi.tool_file_status_nofile;
        h->mem[x + 7] = 0;
        h->mem[x + 8] = 0;
        if (op) {
            op->actual_len = 0;
            op->status = h->abi.tool_file_status_nofile;
        }
        restore_extra_frames(h, original_sp, saved, saved_count);
        return RTS_STUB_ADDR;
    }

    uint8_t* temp = NULL;
    size_t size = 0;
    if (fseek(fp, 0, SEEK_END) != 0) {
        fclose(fp);
        restore_extra_frames(h, original_sp, saved, saved_count);
        die_errno("fseek load failed");
    }
    long end = ftell(fp);
    if (end < 0) {
        fclose(fp);
        restore_extra_frames(h, original_sp, saved, saved_count);
        die_errno("ftell load failed");
    }
    size = (size_t)end;
    if (fseek(fp, 0, SEEK_SET) != 0) {
        fclose(fp);
        restore_extra_frames(h, original_sp, saved, saved_count);
        die_errno("fseek rewind failed");
    }
    temp = malloc(size ? size : 1);
    if (!temp) {
        fclose(fp);
        restore_extra_frames(h, original_sp, saved, saved_count);
        die("malloc failed for load buffer");
    }
    if (size && fread(temp, 1, size, fp) != size) {
        fclose(fp);
        free(temp);
        restore_extra_frames(h, original_sp, saved, saved_count);
        die_errno("fread load failed");
    }
    fclose(fp);

    size_t copy_len = size;
    uint8_t status = h->abi.tool_file_status_ok;
    if (copy_len > limit) {
        copy_len = limit;
        status = h->abi.tool_file_status_too_large;
    }
    for (size_t i = 0; i < copy_len; i++) {
        h->mem[(uint16_t)(dest_ptr + (uint16_t)i)] = temp[i];
    }
    if (op) {
        fill_op_head_from_buf(op, temp, (uint16_t)copy_len);
    }
    free(temp);

    h->mem[x + 6] = status;
    h->mem[x + 7] = (uint8_t)(copy_len & 0xFF);
    h->mem[x + 8] = (uint8_t)(copy_len >> 8);
    if (op) {
        op->actual_len = (uint16_t)copy_len;
        op->status = status;
    }
    restore_extra_frames(h, original_sp, saved, saved_count);
    return RTS_STUB_ADDR;
}

static void ensure_reu(Harness* h)
{
    if (h->reu) {
        return;
    }
    h->reu = calloc(1, SIM_REU_SIZE);
    if (!h->reu) {
        die("calloc failed for simulated REU");
    }
    h->reu_size = SIM_REU_SIZE;
}

static int service_file_stage_reu(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    Harness* h = G;
    uint8_t x = cpu->registers->x;
    uint16_t name_ptr = read_u16(h, x + 0);
    uint32_t reu_base = read_u24(h, x + 2);
    char rel[MAX_PATH_LEN];
    char full[MAX_PATH_LEN];
    read_cstr_mem(h, name_ptr, rel, sizeof(rel));
    resolve_tool_path(h, rel, false, full, sizeof(full));

    FileOp* op = record_op(h, "rsta");
    if (op) {
        fill_op_common(h, op, cpu, x, rel, full, (uint16_t)(reu_base & 0xFFFFu), (uint16_t)(reu_base >> 16));
        fill_op_symbol_dumps(h, op);
    }

    FILE* fp = fopen(full, "rb");
    if (!fp) {
        h->mem[x + 5] = h->abi.tool_file_status_nofile;
        h->mem[x + 6] = 0;
        h->mem[x + 7] = 0;
        h->mem[x + 8] = 0;
        if (op) {
            op->status = h->abi.tool_file_status_nofile;
        }
        return RTS_STUB_ADDR;
    }
    if (fseek(fp, 0, SEEK_END) != 0) {
        fclose(fp);
        die_errno("fseek REU stage failed");
    }
    long end = ftell(fp);
    if (end < 0) {
        fclose(fp);
        die_errno("ftell REU stage failed");
    }
    size_t size = (size_t)end;
    if (fseek(fp, 0, SEEK_SET) != 0) {
        fclose(fp);
        die_errno("fseek REU stage rewind failed");
    }

    ensure_reu(h);
    size_t copy_len = size;
    uint8_t status = h->abi.tool_file_status_ok;
    if (reu_base >= h->reu_size) {
        copy_len = 0;
        status = h->abi.tool_file_status_too_large;
    } else if (copy_len > h->reu_size - reu_base) {
        copy_len = h->reu_size - reu_base;
        status = h->abi.tool_file_status_too_large;
    }

    if (copy_len && fread(h->reu + reu_base, 1, copy_len, fp) != copy_len) {
        fclose(fp);
        die_errno("fread REU stage failed");
    }
    fclose(fp);

    h->mem[x + 5] = status;
    h->mem[x + 6] = (uint8_t)(copy_len & 0xFFu);
    h->mem[x + 7] = (uint8_t)((copy_len >> 8) & 0xFFu);
    h->mem[x + 8] = (uint8_t)((copy_len >> 16) & 0xFFu);
    if (op) {
        op->actual_len = (uint32_t)copy_len;
        op->status = status;
        if (copy_len) {
            fill_op_head_from_buf(op, h->reu + reu_base, (uint16_t)(copy_len > TRACE_HEAD_LEN ? TRACE_HEAD_LEN : copy_len));
        }
    }
    return RTS_STUB_ADDR;
}

static int service_reu_read(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    Harness* h = G;
    uint8_t x = cpu->registers->x;
    uint32_t reu_addr = read_u24(h, x + 0);
    uint16_t dest_ptr = read_u16(h, x + 3);
    uint16_t len = read_u16(h, x + 5);

    FileOp* op = NULL;
    if (!has_logged_reu_op(h, "rrd", x)) {
        op = record_op(h, "rrd");
    }
    if (op) {
        fill_op_common(h, op, cpu, x, "", "", dest_ptr, len);
        fill_op_symbol_dumps(h, op);
    }

    ensure_reu(h);
    if (reu_addr >= h->reu_size || (size_t)len > h->reu_size - reu_addr) {
        h->mem[x + 7] = h->abi.tool_file_status_too_large;
        if (op) {
            op->status = h->abi.tool_file_status_too_large;
        }
        return RTS_STUB_ADDR;
    }
    for (uint16_t i = 0; i < len; i++) {
        h->mem[(uint16_t)(dest_ptr + i)] = h->reu[reu_addr + i];
    }
    h->mem[x + 7] = h->abi.tool_file_status_ok;
    if (op) {
        op->actual_len = len;
        op->status = h->abi.tool_file_status_ok;
        fill_op_head_from_mem(h, op, dest_ptr, len);
    }
    return RTS_STUB_ADDR;
}

static int service_reu_write(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    Harness* h = G;
    uint8_t x = cpu->registers->x;
    uint32_t reu_addr = read_u24(h, x + 0);
    uint16_t src_ptr = read_u16(h, x + 3);
    uint16_t len = read_u16(h, x + 5);

    FileOp* op = NULL;
    if (!has_logged_reu_write_op(h, x, src_ptr, len)) {
        op = record_op(h, "rwr");
    }
    if (op) {
        fill_op_common(h, op, cpu, x, "", "", src_ptr, len);
        fill_op_symbol_dumps(h, op);
        fill_op_head_from_mem(h, op, src_ptr, len);
    }

    ensure_reu(h);
    if (reu_addr >= h->reu_size || (size_t)len > h->reu_size - reu_addr) {
        h->mem[x + 7] = h->abi.tool_file_status_too_large;
        if (op) {
            op->status = h->abi.tool_file_status_too_large;
        }
        return RTS_STUB_ADDR;
    }
    for (uint16_t i = 0; i < len; i++) {
        h->reu[reu_addr + i] = h->mem[(uint16_t)(src_ptr + i)];
    }
    h->mem[x + 7] = h->abi.tool_file_status_ok;
    if (op) {
        op->actual_len = len;
        op->status = h->abi.tool_file_status_ok;
    }
    return RTS_STUB_ADDR;
}

static int service_file_save(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    Harness* h = G;
    SavedByte saved[MAX_SIM_PUSHES];
    size_t saved_count = 0;
    uint8_t original_sp = apply_extra_frames(h, h->extra_save_frames, saved, &saved_count);
    uint8_t x = cpu->registers->x;
    uint16_t name_ptr = read_u16(h, x + 0);
    uint16_t src_ptr = read_u16(h, x + 2);
    uint16_t len = read_u16(h, x + 4);
    uint16_t save_len = len;
    char rel[MAX_PATH_LEN];
    char full[MAX_PATH_LEN];
    read_cstr_mem(h, name_ptr, rel, sizeof(rel));
    resolve_tool_path(h, rel, true, full, sizeof(full));
    if (save_len == 0) {
        while ((uint32_t)src_ptr + (uint32_t)save_len < 0x10000u &&
               h->mem[(uint16_t)(src_ptr + save_len)] != 0) {
            save_len++;
        }
    }
    FileOp* op = record_op(h, "save");
    if (op) {
        fill_op_common(h, op, cpu, x, rel, full, src_ptr, len);
        fill_op_symbol_dumps(h, op);
        fill_op_head_from_mem(h, op, src_ptr, save_len);
    }

    char parent[MAX_PATH_LEN];
    snprintf(parent, sizeof(parent), "%s", full);
    char* slash = strrchr(parent, '/');
    if (slash) {
        *slash = 0;
        ensure_dir_exists(parent);
    }

    FILE* fp = fopen(full, "wb");
    if (!fp) {
        h->mem[x + 6] = h->abi.tool_file_status_fail;
        if (op) {
            op->actual_len = 0;
            op->status = h->abi.tool_file_status_fail;
        }
        restore_extra_frames(h, original_sp, saved, saved_count);
        return RTS_STUB_ADDR;
    }
    if (save_len && fwrite(&h->mem[src_ptr], 1, save_len, fp) != save_len) {
        fclose(fp);
        h->mem[x + 6] = h->abi.tool_file_status_fail;
        if (op) {
            op->actual_len = 0;
            op->status = h->abi.tool_file_status_fail;
        }
        restore_extra_frames(h, original_sp, saved, saved_count);
        return RTS_STUB_ADDR;
    }
    fclose(fp);
    h->mem[x + 6] = h->abi.tool_file_status_ok;
    if (op) {
        op->actual_len = save_len;
        op->status = h->abi.tool_file_status_ok;
    }
    restore_extra_frames(h, original_sp, saved, saved_count);
    return RTS_STUB_ADDR;
}

static int service_file_write_begin(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    Harness* h = G;
    uint8_t x = cpu->registers->x;
    uint16_t name_ptr = read_u16(h, x + 0);
    char rel[MAX_PATH_LEN];
    char full[MAX_PATH_LEN];
    read_cstr_mem(h, name_ptr, rel, sizeof(rel));
    resolve_tool_path(h, rel, true, full, sizeof(full));

    FileOp* op = record_op(h, "wopn");
    if (op) {
        fill_op_common(h, op, cpu, x, rel, full, 0, 0);
        fill_op_symbol_dumps(h, op);
    }

    if (h->stream_write_fp) {
        fclose(h->stream_write_fp);
        h->stream_write_fp = NULL;
    }

    char parent[MAX_PATH_LEN];
    snprintf(parent, sizeof(parent), "%s", full);
    char* slash = strrchr(parent, '/');
    if (slash) {
        *slash = 0;
        ensure_dir_exists(parent);
    }

    h->stream_write_fp = fopen(full, "wb");
    if (!h->stream_write_fp) {
        h->mem[x + 2] = h->abi.tool_file_status_fail;
        if (op) {
            op->status = h->abi.tool_file_status_fail;
        }
        return RTS_STUB_ADDR;
    }
    snprintf(h->stream_write_path, sizeof(h->stream_write_path), "%s", full);
    h->mem[x + 2] = h->abi.tool_file_status_ok;
    if (op) {
        op->status = h->abi.tool_file_status_ok;
    }
    return RTS_STUB_ADDR;
}

static int service_file_write_chunk(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    Harness* h = G;
    uint8_t x = cpu->registers->x;
    uint16_t src_ptr = read_u16(h, x + 0);
    uint16_t len = read_u16(h, x + 2);

    FileOp* op = record_op(h, "wrte");
    if (op) {
        fill_op_common(h, op, cpu, x, "", h->stream_write_path, src_ptr, len);
        fill_op_symbol_dumps(h, op);
        fill_op_head_from_mem(h, op, src_ptr, len);
    }

    if (!h->stream_write_fp) {
        h->mem[x + 4] = h->abi.tool_file_status_fail;
        if (op) {
            op->status = h->abi.tool_file_status_fail;
        }
        return RTS_STUB_ADDR;
    }
    for (uint16_t i = 0; i < len; i++) {
        if (fputc(h->mem[(uint16_t)(src_ptr + i)], h->stream_write_fp) == EOF) {
            h->mem[x + 4] = h->abi.tool_file_status_fail;
            if (op) {
                op->actual_len = i;
                op->status = h->abi.tool_file_status_fail;
            }
            return RTS_STUB_ADDR;
        }
    }
    h->mem[x + 4] = h->abi.tool_file_status_ok;
    if (op) {
        op->actual_len = len;
        op->status = h->abi.tool_file_status_ok;
    }
    return RTS_STUB_ADDR;
}

static int service_file_write_close(M6502* cpu, uint16_t address, uint8_t data)
{
    (void)address;
    (void)data;
    Harness* h = G;
    uint8_t x = cpu->registers->x;

    FileOp* op = record_op(h, "wcls");
    if (op) {
        fill_op_common(h, op, cpu, x, "", h->stream_write_path, 0, 0);
        fill_op_symbol_dumps(h, op);
    }

    if (!h->stream_write_fp) {
        h->mem[x + 0] = h->abi.tool_file_status_fail;
        if (op) {
            op->status = h->abi.tool_file_status_fail;
        }
        return RTS_STUB_ADDR;
    }
    if (fclose(h->stream_write_fp) != 0) {
        h->stream_write_fp = NULL;
        h->mem[x + 0] = h->abi.tool_file_status_fail;
        if (op) {
            op->status = h->abi.tool_file_status_fail;
        }
        return RTS_STUB_ADDR;
    }
    h->stream_write_fp = NULL;
    h->mem[x + 0] = h->abi.tool_file_status_ok;
    if (op) {
        op->status = h->abi.tool_file_status_ok;
    }
    return RTS_STUB_ADDR;
}

static int reu_trigger_write(M6502* cpu, uint16_t address, uint8_t data)
{
    Harness* h = G;
    uint16_t c64_addr = read_u16(h, REU_C64ADDR_LO);
    uint32_t reu_addr = read_u24(h, REU_REUADDR_LO);
    uint32_t count = read_u16(h, REU_COUNT_LO);
    uint8_t command = h->mem[REU_COMMAND];
    (void)cpu;
    h->mem[address] = data;
    if (count == 0) {
        count = 0x10000u;
    }
    if (reu_addr + count > h->reu_size) {
        die("raw REU transfer exceeds simulated REU");
    }
    for (uint32_t i = 0; i < count; i++) {
        uint16_t mem_addr = (uint16_t)(c64_addr + (uint16_t)i);
        if (command == REU_STORE) {
            h->reu[reu_addr + i] = h->mem[mem_addr];
        } else if (command == REU_FETCH) {
            h->mem[mem_addr] = h->reu[reu_addr + i];
        } else {
            die("unsupported raw REU command");
        }
    }
    return data;
}

static void install_callbacks(Harness* h)
{
    memset(&h->callbacks, 0, sizeof(h->callbacks));
    M6502_setCallback(h->cpu, call, KERNAL_READST, kernal_readst);
    M6502_setCallback(h->cpu, call, KERNAL_SETLFS, kernal_setlfs);
    M6502_setCallback(h->cpu, call, KERNAL_SETNAM, kernal_setnam);
    M6502_setCallback(h->cpu, call, KERNAL_OPEN, kernal_open);
    M6502_setCallback(h->cpu, call, KERNAL_CLOSE, kernal_close);
    M6502_setCallback(h->cpu, call, KERNAL_CHKIN, kernal_chkin);
    M6502_setCallback(h->cpu, call, KERNAL_CHKOUT, kernal_chkout);
    M6502_setCallback(h->cpu, call, KERNAL_CLRCHN, kernal_clrchn);
    M6502_setCallback(h->cpu, call, KERNAL_CHRIN, kernal_chrin);
    M6502_setCallback(h->cpu, call, KERNAL_CHROUT, kernal_chrout);
    M6502_setCallback(h->cpu, call, h->abi.svc_console_write_sc0, service_console_write);
    M6502_setCallback(h->cpu, call, h->abi.svc_console_newline, service_console_newline);
    M6502_setCallback(h->cpu, call, h->abi.svc_program_get_cmdline_ptr, service_program_get_cmdline_ptr);
    M6502_setCallback(h->cpu, call, h->abi.svc_program_get_cmdline_len, service_program_get_cmdline_len);
    M6502_setCallback(h->cpu, call, h->abi.svc_program_exit, service_program_exit);
    h->mem[h->abi.svc_program_exit] = 0x60;
    if (h->abi.svc_program_chain_sc0) {
        M6502_setCallback(h->cpu, call, h->abi.svc_program_chain_sc0, service_program_chain);
    }
    M6502_setCallback(h->cpu, call, h->abi.svc_file_load_sc0, service_file_load);
    M6502_setCallback(h->cpu, call, h->abi.svc_file_save_sc0, service_file_save);
    M6502_setCallback(h->cpu, call, h->abi.svc_file_write_begin_sc0, service_file_write_begin);
    M6502_setCallback(h->cpu, call, h->abi.svc_file_write_chunk_sc0, service_file_write_chunk);
    M6502_setCallback(h->cpu, call, h->abi.svc_file_write_close_sc0, service_file_write_close);
    if (h->abi.svc_file_stage_reu_sc0) {
        M6502_setCallback(h->cpu, call, h->abi.svc_file_stage_reu_sc0, service_file_stage_reu);
    }
    if (h->abi.svc_reu_read_sc0) {
        M6502_setCallback(h->cpu, call, h->abi.svc_reu_read_sc0, service_reu_read);
    }
    if (h->abi.svc_reu_write_sc0) {
        M6502_setCallback(h->cpu, call, h->abi.svc_reu_write_sc0, service_reu_write);
    }
    if (h->abi.svc_open_program_read_path_preserved) {
        M6502_setCallback(
            h->cpu,
            call,
            h->abi.svc_open_program_read_path_preserved,
            service_open_program_read_path_preserved);
    }
    M6502_setCallback(h->cpu, write, REU_TRIGGER, reu_trigger_write);
}

static void load_prg(Harness* h, const char* path, uint16_t* entry_out)
{
    FILE* fp = fopen(path, "rb");
    if (!fp) {
        die_errno("unable to open PRG");
    }
    int lo = fgetc(fp);
    int hi = fgetc(fp);
    if (lo < 0 || hi < 0) {
        fclose(fp);
        die("short PRG header");
    }
    uint16_t load_addr = (uint16_t)lo | ((uint16_t)hi << 8);
    size_t offset = 0;
    int c;
    while ((c = fgetc(fp)) != EOF) {
        h->mem[(uint16_t)(load_addr + (uint16_t)offset)] = (uint8_t)c;
        offset++;
    }
    fclose(fp);
    *entry_out = load_addr;
}

static void json_escape(FILE* out, const char* text)
{
    fputc('"', out);
    for (const unsigned char* p = (const unsigned char*)text; *p; p++) {
        switch (*p) {
            case '\\': fputs("\\\\", out); break;
            case '"': fputs("\\\"", out); break;
            case '\n': fputs("\\n", out); break;
            case '\r': fputs("\\r", out); break;
            case '\t': fputs("\\t", out); break;
            default:
                if (*p < 32) {
                    fprintf(out, "\\u%04x", *p);
                } else {
                    fputc(*p, out);
                }
        }
    }
    fputc('"', out);
}

static bool add_dump_request_to(DumpRequest* requests, size_t* count, size_t max_count, DumpKind kind, const char* spec);

static bool add_dump_request(Harness* h, DumpKind kind, const char* spec)
{
    return add_dump_request_to(h->dumps, &h->dump_count, MAX_DUMPS, kind, spec);
}

static bool add_dump_request_to(DumpRequest* requests, size_t* count, size_t max_count, DumpKind kind, const char* spec)
{
    if (*count >= max_count) {
        return false;
    }
    const char* colon = strrchr(spec, ':');
    if (!colon || colon == spec) {
        return false;
    }
    uint16_t length = 0;
    if (!parse_u16_value(colon + 1, &length)) {
        return false;
    }
    DumpRequest* req = &requests[(*count)++];
    memset(req, 0, sizeof(*req));
    req->kind = kind;
    req->length = length;
    size_t name_len = (size_t)(colon - spec);
    if (name_len >= sizeof(req->name)) {
        name_len = sizeof(req->name) - 1;
    }
    memcpy(req->name, spec, name_len);
    req->name[name_len] = 0;
    return true;
}

static bool add_poke_request(Harness* h, PokeKind kind, const char* spec)
{
    if (h->poke_count >= MAX_POKES) {
        return false;
    }
    const char* eq = strchr(spec, '=');
    if (!eq || eq == spec) {
        return false;
    }
    PokeRequest* req = &h->pokes[h->poke_count++];
    memset(req, 0, sizeof(*req));
    req->kind = kind;
    size_t name_len = (size_t)(eq - spec);
    if (name_len >= sizeof(req->name)) {
        name_len = sizeof(req->name) - 1;
    }
    memcpy(req->name, spec, name_len);
    req->name[name_len] = 0;
    if (kind == POKE_CSTR || kind == POKE_SCSTR) {
        snprintf(req->text, sizeof(req->text), "%s", eq + 1);
        return true;
    }
    return parse_u16_value(eq + 1, &req->value);
}

static void apply_pokes(Harness* h)
{
    for (size_t i = 0; i < h->poke_count; i++) {
        PokeRequest* req = &h->pokes[i];
        uint16_t addr = 0;
        if (!find_label_addr(h, req->name, &addr)) {
            char* end = NULL;
            unsigned long raw = strtoul(req->name, &end, 0);
            if (end == req->name || *end != 0 || raw > 0xFFFFUL) {
                fprintf(stderr, "poke target not found: %s\n", req->name);
                die("poke label not found");
            }
            addr = (uint16_t)raw;
        }
        if (req->kind == POKE_CSTR || req->kind == POKE_SCSTR) {
            size_t len = strlen(req->text);
            for (size_t j = 0; j < len; j++) {
                uint8_t value = (uint8_t)req->text[j];
                if (req->kind == POKE_SCSTR) {
                    value = ascii_to_screen_code(value);
                }
                h->mem[(uint16_t)(addr + (uint16_t)j)] = value;
            }
            h->mem[(uint16_t)(addr + (uint16_t)len)] = 0;
        } else if (req->kind == POKE_WORD) {
            h->mem[addr] = (uint8_t)(req->value & 0xFF);
            h->mem[(uint16_t)(addr + 1)] = (uint8_t)(req->value >> 8);
        } else {
            h->mem[addr] = (uint8_t)(req->value & 0xFF);
        }
    }
}

static void json_escape_len(FILE* out, const uint8_t* bytes, size_t len)
{
    fputc('"', out);
    for (size_t i = 0; i < len; i++) {
        unsigned char c = bytes[i];
        if (!c) {
            break;
        }
        switch (c) {
            case '\\': fputs("\\\\", out); break;
            case '"': fputs("\\\"", out); break;
            case '\n': fputs("\\n", out); break;
            case '\r': fputs("\\r", out); break;
            case '\t': fputs("\\t", out); break;
            default:
                if (c < 32) {
                    fprintf(out, "\\u%04x", c);
                } else {
                    fputc(c, out);
                }
        }
    }
    fputc('"', out);
}

static void print_summary(Harness* h)
{
    printf("{\n");
    printf("  \"exit_status\": %u,\n", h->exit_status);
    printf("  \"exited\": %s,\n", h->exited ? "true" : "false");
    printf("  \"chain_requested\": %s,\n", h->chain_requested ? "true" : "false");
    printf("  \"chain_command\": ");
    json_escape(stdout, h->chain_command);
    printf(",\n");
    printf("  \"hit_limit\": %s,\n", h->hit_limit ? "true" : "false");
    printf("  \"broke_on_pc\": %s,\n", h->broke_on_pc ? "true" : "false");
    printf("  \"steps\": %llu,\n", (unsigned long long)h->steps);
    printf("  \"registers\": {\n");
    printf("    \"pc\": %u,\n", h->cpu->registers->pc);
    printf("    \"a\": %u,\n", h->cpu->registers->a);
    printf("    \"x\": %u,\n", h->cpu->registers->x);
    printf("    \"y\": %u,\n", h->cpu->registers->y);
    printf("    \"sp\": %u,\n", h->cpu->registers->s);
    printf("    \"p\": %u\n", h->cpu->registers->p);
    printf("  },\n");
    printf("  \"console\": ");
    json_escape(stdout, h->console ? h->console : "");
    printf(",\n");
    printf("  \"ops\": [\n");
    for (size_t i = 0; i < h->op_count; i++) {
        FileOp* op = &h->ops[i];
        printf("    {\"kind\": ");
        json_escape(stdout, op->kind);
        printf(", \"path\": ");
        json_escape(stdout, op->path);
        printf(", \"full_path\": ");
        json_escape(stdout, op->full_path);
        printf(", \"ptr\": %u, \"limit\": %u, \"actual_len\": %u, \"status\": %u",
               op->ptr, op->limit, (unsigned)op->actual_len, op->status);
        printf(", \"x\": %u, \"sp\": %u, \"stack_rts_raw\": %u, \"stack_rts_next\": %u, \"approx_jsr_site\": %u", op->x_reg, op->sp, op->stack_rts_raw, op->stack_rts_next, op->approx_jsr_site);
        printf(", \"params\": [");
        for (size_t j = 0; j < sizeof(op->params); j++) {
            printf("%s%u", j ? ", " : "", op->params[j]);
        }
        printf("], \"head\": [");
        for (uint8_t j = 0; j < op->head_len; j++) {
            printf("%s%u", j ? ", " : "", op->head[j]);
        }
        printf("], \"stack_window\": [");
        for (size_t j = 0; j < STACK_WINDOW_LEN; j++) {
            printf("%s%u", j ? ", " : "", op->stack_window[j]);
        }
        printf("], \"trace\": {");
        for (size_t j = 0; j < h->op_dump_count; j++) {
            DumpRequest* req = &h->op_dumps[j];
            OpDumpValue* value = &op->dumps[j];
            if (j) {
                printf(", ");
            }
            json_escape(stdout, req->name);
            printf(": ");
            if (!value->valid) {
                json_escape(stdout, "<missing>");
            } else if (req->kind == DUMP_CSTR) {
                json_escape_len(stdout, value->bytes, value->captured_len);
            } else {
                printf("[");
                for (uint16_t k = 0; k < value->captured_len; k++) {
                    printf("%s%u", k ? ", " : "", value->bytes[k]);
                }
                printf("]");
            }
        }
        printf("}}%s\n", (i + 1 == h->op_count) ? "" : ",");
    }
    printf("  ],\n");
    printf("  \"kernal_ops\": [\n");
    for (size_t i = 0; i < h->kernal_op_count; i++) {
        KernalOp* op = &h->kernal_ops[i];
        printf("    {\"kind\": ");
        json_escape(stdout, op->kind);
        printf(", \"a\": %u, \"x\": %u, \"y\": %u, \"sp\": %u, \"status\": %u, \"current_input_lfn\": %u, \"current_output_lfn\": %u, \"name\": ",
               op->a, op->x, op->y, op->sp, op->status, op->current_input_lfn, op->current_output_lfn);
        json_escape(stdout, op->name);
        printf(", \"path\": ");
        json_escape(stdout, op->path);
        printf("}%s\n", (i + 1 == h->kernal_op_count) ? "" : ",");
    }
    printf("  ],\n");
    printf("  \"pc_trace\": [\n");
    for (size_t i = 0; i < h->pc_trace_count; i++) {
        PcTraceEntry* e = &h->pc_trace[i];
        printf("    {\"pc\": %u, \"sp\": %u, \"a\": %u, \"x\": %u, \"y\": %u, \"p\": %u}%s\n",
               e->pc, e->sp, e->a, e->x, e->y, e->p,
               (i + 1 == h->pc_trace_count) ? "" : ",");
    }
    printf("  ],\n");
    printf("  \"dumps\": {\n");
    for (size_t i = 0; i < h->dump_count; i++) {
        DumpRequest* req = &h->dumps[i];
        uint16_t addr = 0;
        printf("    ");
        json_escape(stdout, req->name);
        printf(": ");
        if (!find_label_addr(h, req->name, &addr)) {
            char* end = NULL;
            unsigned long raw = strtoul(req->name, &end, 0);
            if (end == req->name || *end != 0 || raw > 0xFFFFUL) {
                json_escape(stdout, "<missing>");
                printf("%s\n", (i + 1 == h->dump_count) ? "" : ",");
                continue;
            }
            addr = (uint16_t)raw;
        }
        if (req->kind == DUMP_CSTR) {
            char text[4096];
            read_cstr_mem(h, addr, text, req->length < sizeof(text) ? req->length : sizeof(text));
            json_escape(stdout, text);
        } else {
            printf("[");
            for (uint16_t j = 0; j < req->length; j++) {
                printf("%s%u", j ? ", " : "", h->mem[(uint16_t)(addr + j)]);
            }
            printf("]");
        }
        printf("%s\n", (i + 1 == h->dump_count) ? "" : ",");
    }
    printf("  }\n");
    printf("}\n");
}

int main(int argc, char** argv)
{
    Harness h;
    memset(&h, 0, sizeof(h));

    const char* prg_path = NULL;
    const char* workspace = NULL;
    const char* cmdline = "";
    const char* services_inc = NULL;
    const char* labels_path = NULL;
    const char* overlay_prg = NULL;
    bool cmdline_screen_code = false;
    uint64_t max_steps = 10000000ULL;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--prg") == 0 && i + 1 < argc) {
            prg_path = argv[++i];
        } else if (strcmp(argv[i], "--overlay-prg") == 0 && i + 1 < argc) {
            overlay_prg = argv[++i];
        } else if (strcmp(argv[i], "--workspace") == 0 && i + 1 < argc) {
            workspace = argv[++i];
        } else if (strcmp(argv[i], "--cmdline") == 0 && i + 1 < argc) {
            cmdline = argv[++i];
        } else if (strcmp(argv[i], "--cmdline-screen-code") == 0) {
            cmdline_screen_code = true;
        } else if (strcmp(argv[i], "--services-inc") == 0 && i + 1 < argc) {
            services_inc = argv[++i];
        } else if (strcmp(argv[i], "--labels") == 0 && i + 1 < argc) {
            labels_path = argv[++i];
        } else if (strcmp(argv[i], "--entry-label") == 0 && i + 1 < argc) {
            h.entry_label = argv[++i];
        } else if (strcmp(argv[i], "--entry-addr") == 0 && i + 1 < argc) {
            uint16_t addr = 0;
            if (!parse_u16_value(argv[++i], &addr)) {
                die("bad --entry-addr value");
            }
            h.entry_addr = addr;
            h.entry_addr_set = true;
        } else if (strcmp(argv[i], "--stop-pc") == 0 && i + 1 < argc) {
            uint16_t addr = 0;
            if (!parse_u16_value(argv[++i], &addr)) {
                die("bad --stop-pc value");
            }
            h.break_pc = addr;
            h.break_on_pc = true;
        } else if (strcmp(argv[i], "--max-steps") == 0 && i + 1 < argc) {
            max_steps = strtoull(argv[++i], NULL, 0);
        } else if (strcmp(argv[i], "--reg-a") == 0 && i + 1 < argc) {
            h.reg_a_init = (uint8_t)strtoul(argv[++i], NULL, 0);
            h.reg_a_set = true;
        } else if (strcmp(argv[i], "--reg-x") == 0 && i + 1 < argc) {
            h.reg_x_init = (uint8_t)strtoul(argv[++i], NULL, 0);
            h.reg_x_set = true;
        } else if (strcmp(argv[i], "--reg-y") == 0 && i + 1 < argc) {
            h.reg_y_init = (uint8_t)strtoul(argv[++i], NULL, 0);
            h.reg_y_set = true;
        } else if (strcmp(argv[i], "--reg-sp") == 0 && i + 1 < argc) {
            h.reg_sp_init = (uint8_t)strtoul(argv[++i], NULL, 0);
            h.reg_sp_set = true;
        } else if (strcmp(argv[i], "--extra-load-frames") == 0 && i + 1 < argc) {
            h.extra_load_frames = (uint8_t)strtoul(argv[++i], NULL, 0);
        } else if (strcmp(argv[i], "--extra-save-frames") == 0 && i + 1 < argc) {
            h.extra_save_frames = (uint8_t)strtoul(argv[++i], NULL, 0);
        } else if (strcmp(argv[i], "--extra-entry-frames") == 0 && i + 1 < argc) {
            h.extra_entry_frames = (uint8_t)strtoul(argv[++i], NULL, 0);
        } else if (strcmp(argv[i], "--trace-pc-range") == 0 && i + 1 < argc) {
            const char* spec = argv[++i];
            const char* colon = strchr(spec, ':');
            uint16_t start = 0;
            uint16_t end = 0;
            if (!colon) {
                die("bad --trace-pc-range spec, expected START:END");
            }
            char left[32];
            size_t left_len = (size_t)(colon - spec);
            if (left_len >= sizeof(left)) {
                die("bad --trace-pc-range start");
            }
            memcpy(left, spec, left_len);
            left[left_len] = 0;
            if (!parse_u16_value(left, &start) || !parse_u16_value(colon + 1, &end)) {
                die("bad --trace-pc-range values");
            }
            h.trace_pc_enabled = true;
            h.trace_pc_start = start;
            h.trace_pc_end = end;
        } else if (strcmp(argv[i], "--dump") == 0 && i + 1 < argc) {
            if (!add_dump_request(&h, DUMP_BYTES, argv[++i])) {
                die("bad --dump spec, expected NAME:LEN");
            }
        } else if (strcmp(argv[i], "--dump-cstr") == 0 && i + 1 < argc) {
            if (!add_dump_request(&h, DUMP_CSTR, argv[++i])) {
                die("bad --dump-cstr spec, expected NAME:LEN");
            }
        } else if (strcmp(argv[i], "--op-dump") == 0 && i + 1 < argc) {
            if (!add_dump_request_to(h.op_dumps, &h.op_dump_count, MAX_OP_DUMPS, DUMP_BYTES, argv[++i])) {
                die("bad --op-dump spec, expected NAME:LEN");
            }
        } else if (strcmp(argv[i], "--op-dump-cstr") == 0 && i + 1 < argc) {
            if (!add_dump_request_to(h.op_dumps, &h.op_dump_count, MAX_OP_DUMPS, DUMP_CSTR, argv[++i])) {
                die("bad --op-dump-cstr spec, expected NAME:LEN");
            }
        } else if (strcmp(argv[i], "--poke-byte") == 0 && i + 1 < argc) {
            if (!add_poke_request(&h, POKE_BYTE, argv[++i])) {
                die("bad --poke-byte spec, expected NAME=VALUE");
            }
        } else if (strcmp(argv[i], "--poke-word") == 0 && i + 1 < argc) {
            if (!add_poke_request(&h, POKE_WORD, argv[++i])) {
                die("bad --poke-word spec, expected NAME=VALUE");
            }
        } else if (strcmp(argv[i], "--poke-cstr") == 0 && i + 1 < argc) {
            if (!add_poke_request(&h, POKE_CSTR, argv[++i])) {
                die("bad --poke-cstr spec, expected NAME=TEXT");
            }
        } else if (strcmp(argv[i], "--poke-scstr") == 0 && i + 1 < argc) {
            if (!add_poke_request(&h, POKE_SCSTR, argv[++i])) {
                die("bad --poke-scstr spec, expected NAME=TEXT");
            }
        } else {
            fprintf(stderr, "usage: %s --prg TOOL.PRG [--overlay-prg RESIDENT.PRG] --workspace DIR [--cmdline TEXT] [--cmdline-screen-code] --services-inc udos_services.inc [--labels file] [--entry-label NAME] [--entry-addr ADDR] [--stop-pc ADDR] [--reg-a N] [--reg-x N] [--reg-y N] [--reg-sp N] [--poke-byte NAME=VALUE] [--poke-word NAME=VALUE] [--poke-cstr NAME=TEXT] [--poke-scstr NAME=TEXT] [--dump NAME:LEN] [--dump-cstr NAME:LEN] [--op-dump NAME:LEN] [--op-dump-cstr NAME:LEN] [--trace-pc-range START:END] [--extra-entry-frames N] [--extra-load-frames N] [--extra-save-frames N] [--max-steps N]\n", argv[0]);
            return 2;
        }
    }

    if (!prg_path || !workspace || !services_inc) {
        fprintf(stderr, "missing required arguments\n");
        return 2;
    }

    snprintf(h.workspace, sizeof(h.workspace), "%s", workspace);
    copy_parent_dir(prg_path, h.program_dir, sizeof(h.program_dir));
    snprintf(h.cmdline, sizeof(h.cmdline), "%s", cmdline);
    if (cmdline_screen_code) {
        for (size_t i = 0; h.cmdline[i] != 0; i++) {
            h.cmdline[i] = (char)ascii_to_screen_code((uint8_t)h.cmdline[i]);
        }
    }
    load_services_inc(&h.abi, services_inc);
    if (labels_path) {
        load_ld65_labels(&h, labels_path);
    }
    h.cpu = M6502_new(NULL, h.mem, &h.callbacks);
    if (!h.cpu) {
        die("M6502_new failed");
    }
    G = &h;
    install_callbacks(&h);
    h.mem[RTS_STUB_ADDR] = 0x60;

    uint16_t entry = 0;
    load_prg(&h, prg_path, &entry);
    if (overlay_prg) {
        uint16_t overlay_entry = 0;
        load_prg(&h, overlay_prg, &overlay_entry);
    }
    size_t cmdline_len = strlen(h.cmdline);
    memcpy(&h.mem[CMDLINE_ADDR], h.cmdline, cmdline_len);
    h.mem[CMDLINE_ADDR + cmdline_len] = 0;
    apply_pokes(&h);

    if (h.entry_label) {
        if (!find_label_addr(&h, h.entry_label, &entry)) {
            die("entry label not found");
        }
        h.stop_on_pc = true;
        h.stop_pc = STOP_STUB_ADDR;
    } else if (h.entry_addr_set) {
        entry = h.entry_addr;
        h.stop_on_pc = true;
        h.stop_pc = STOP_STUB_ADDR;
    }

    h.cpu->registers->a = h.reg_a_set ? h.reg_a_init : 0;
    h.cpu->registers->x = h.reg_x_set ? h.reg_x_init : 0;
    h.cpu->registers->y = h.reg_y_set ? h.reg_y_init : 0;
    h.cpu->registers->p = 0x24;
    h.cpu->registers->s = h.reg_sp_set ? h.reg_sp_init : 0xFF;
    h.cpu->registers->pc = entry;
    h.mem[RTS_STUB_ADDR] = 0x60;
    h.mem[STOP_STUB_ADDR] = 0x60;
    h.mem[KERNAL_BRK_STUB + 0] = 0x48; /* PHA */
    h.mem[KERNAL_BRK_STUB + 1] = 0x8A; /* TXA */
    h.mem[KERNAL_BRK_STUB + 2] = 0x48; /* PHA */
    h.mem[KERNAL_BRK_STUB + 3] = 0x98; /* TYA */
    h.mem[KERNAL_BRK_STUB + 4] = 0x48; /* PHA */
    h.mem[KERNAL_BRK_STUB + 5] = 0x6C; /* JMP ($0316) */
    h.mem[KERNAL_BRK_STUB + 6] = 0x16;
    h.mem[KERNAL_BRK_STUB + 7] = 0x03;
    h.mem[0xFFFE] = (uint8_t)(KERNAL_BRK_STUB & 0xFF);
    h.mem[0xFFFF] = (uint8_t)(KERNAL_BRK_STUB >> 8);
    if (h.stop_on_pc) {
        uint8_t sp = (uint8_t)(0xFDu - (uint8_t)(h.extra_entry_frames * 2u));
        h.cpu->registers->s = sp;
        for (uint8_t i = 0; i < h.extra_entry_frames; i++) {
            uint16_t addr = (uint16_t)(0x0100u + (uint16_t)(sp + 1u + (uint8_t)(i * 2u)));
            h.mem[addr] = (uint8_t)((RTS_STUB_ADDR - 1) & 0xFF);
            h.mem[(uint16_t)(addr + 1u)] = (uint8_t)((RTS_STUB_ADDR - 1) >> 8);
        }
        {
            uint16_t stop_addr = (uint16_t)(0x0100u + (uint16_t)(sp + 1u + (uint16_t)(h.extra_entry_frames * 2u)));
            h.mem[stop_addr] = (uint8_t)((STOP_STUB_ADDR - 1) & 0xFF);
            h.mem[(uint16_t)(stop_addr + 1u)] = (uint8_t)((STOP_STUB_ADDR - 1) >> 8);
        }
    }

    if (setjmp(h.escape) == 0) {
        for (h.steps = 0; h.steps < max_steps; h.steps++) {
            maybe_record_pc_trace(&h);
            if (h.break_on_pc && h.cpu->registers->pc == h.break_pc) {
                h.broke_on_pc = true;
                h.exited = true;
                break;
            }
            if (h.stop_on_pc && h.cpu->registers->pc == h.stop_pc) {
                h.exited = true;
                break;
            }
            M6502_run(h.cpu);
        }
        if (!h.exited) {
            h.hit_limit = true;
        }
    }

    print_summary(&h);
    if (h.stream_write_fp) {
        fclose(h.stream_write_fp);
    }
    M6502_delete(h.cpu);
    free(h.console);
    return h.exit_status ? 1 : 0;
}
