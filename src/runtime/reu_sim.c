#include "reu_backend.h"

#include <string.h>

#define MAX_HANDLES 8
#define MAX_SPARSE_BYTES 64

typedef struct {
    bool in_use;
    uint32_t size;
} SimHandle;

typedef struct {
    bool in_use;
    ReuHandle handle;
    uint32_t offset;
    uint8_t value;
} SparseByte;

static SimHandle handles[MAX_HANDLES];
static SparseByte sparse_bytes[MAX_SPARSE_BYTES];

static bool handle_valid(ReuHandle handle)
{
    return (handle < MAX_HANDLES) && handles[handle].in_use;
}

static SparseByte* find_sparse_byte(ReuHandle handle, uint32_t offset)
{
    for (uint16_t i = 0; i < MAX_SPARSE_BYTES; i++)
    {
        if (sparse_bytes[i].in_use && (sparse_bytes[i].handle == handle) && (sparse_bytes[i].offset == offset))
            return &sparse_bytes[i];
    }
    return 0;
}

static SparseByte* ensure_sparse_byte(ReuHandle handle, uint32_t offset)
{
    SparseByte* existing = find_sparse_byte(handle, offset);
    if (existing)
        return existing;

    for (uint16_t i = 0; i < MAX_SPARSE_BYTES; i++)
    {
        if (!sparse_bytes[i].in_use)
        {
            sparse_bytes[i].in_use = true;
            sparse_bytes[i].handle = handle;
            sparse_bytes[i].offset = offset;
            sparse_bytes[i].value = 0;
            return &sparse_bytes[i];
        }
    }
    return 0;
}

void reu_backend_reset(void)
{
    memset(handles, 0, sizeof(handles));
    memset(sparse_bytes, 0, sizeof(sparse_bytes));
}

const char* reu_backend_name(void)
{
    return "sim";
}

bool reu_alloc(uint32_t size, ReuHandle* handle_out)
{
    for (ReuHandle handle = 0; handle < MAX_HANDLES; handle++)
    {
        if (!handles[handle].in_use)
        {
            handles[handle].in_use = true;
            handles[handle].size = size;
            *handle_out = handle;
            return true;
        }
    }
    return false;
}

bool reu_free(ReuHandle handle)
{
    if (!handle_valid(handle))
        return false;
    handles[handle].in_use = false;
    handles[handle].size = 0;
    for (uint16_t i = 0; i < MAX_SPARSE_BYTES; i++)
    {
        if (sparse_bytes[i].in_use && (sparse_bytes[i].handle == handle))
            sparse_bytes[i].in_use = false;
    }
    return true;
}

bool reu_copy(ReuHandle dest_handle, uint32_t dest_offset, ReuHandle src_handle, uint32_t src_offset, uint32_t length)
{
    for (uint32_t i = 0; i < length; i++)
    {
        uint8_t value = 0;
        if (!reu_peek8(src_handle, src_offset + i, &value))
            return false;
        if (!reu_poke8(dest_handle, dest_offset + i, value))
            return false;
    }
    return true;
}

bool reu_peek8(ReuHandle handle, uint32_t offset, uint8_t* out)
{
    if (!handle_valid(handle) || (offset >= handles[handle].size))
        return false;
    SparseByte* cell = find_sparse_byte(handle, offset);
    *out = cell ? cell->value : 0;
    return true;
}

bool reu_peek16(ReuHandle handle, uint32_t offset, uint16_t* out)
{
    uint8_t lo = 0;
    uint8_t hi = 0;
    if (!reu_peek8(handle, offset, &lo))
        return false;
    if (!reu_peek8(handle, offset + 1u, &hi))
        return false;
    *out = (uint16_t)lo | ((uint16_t)hi << 8);
    return true;
}

bool reu_poke8(ReuHandle handle, uint32_t offset, uint8_t value)
{
    if (!handle_valid(handle) || (offset >= handles[handle].size))
        return false;
    SparseByte* cell = ensure_sparse_byte(handle, offset);
    if (!cell)
        return false;
    cell->value = value;
    return true;
}

bool reu_poke16(ReuHandle handle, uint32_t offset, uint16_t value)
{
    if (!reu_poke8(handle, offset, (uint8_t)(value & 0xff)))
        return false;
    if (!reu_poke8(handle, offset + 1u, (uint8_t)(value >> 8)))
        return false;
    return true;
}
