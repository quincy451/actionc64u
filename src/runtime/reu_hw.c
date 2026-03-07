#include "reu_backend.h"

/*
 * The hardware backend is only selected for C64/VICE-oriented builds. The
 * bootstrap implementation keeps the API stable but defers the actual DMA
 * transfer sequence until the full VM/runtime path is ready.
 */

void reu_backend_reset(void)
{
}

const char* reu_backend_name(void)
{
    return "hw";
}

bool reu_alloc(uint32_t _size, ReuHandle* _handle_out)
{
    return false;
}

bool reu_free(ReuHandle _handle)
{
    return false;
}

bool reu_copy(ReuHandle _dest_handle, uint32_t _dest_offset, ReuHandle _src_handle, uint32_t _src_offset, uint32_t _length)
{
    return false;
}

bool reu_peek8(ReuHandle _handle, uint32_t _offset, uint8_t* _out)
{
    return false;
}

bool reu_peek16(ReuHandle _handle, uint32_t _offset, uint16_t* _out)
{
    return false;
}

bool reu_poke8(ReuHandle _handle, uint32_t _offset, uint8_t _value)
{
    return false;
}

bool reu_poke16(ReuHandle _handle, uint32_t _offset, uint16_t _value)
{
    return false;
}
