#ifndef ACTIONC64U_REU_BACKEND_H
#define ACTIONC64U_REU_BACKEND_H

#include <stdbool.h>
#include <stdint.h>

typedef uint8_t ReuHandle;

void reu_backend_reset(void);
const char* reu_backend_name(void);
bool reu_alloc(uint32_t size, ReuHandle* handle_out);
bool reu_free(ReuHandle handle);
bool reu_copy(ReuHandle dest_handle, uint32_t dest_offset, ReuHandle src_handle, uint32_t src_offset, uint32_t length);
bool reu_peek8(ReuHandle handle, uint32_t offset, uint8_t* out);
bool reu_peek16(ReuHandle handle, uint32_t offset, uint16_t* out);
bool reu_poke8(ReuHandle handle, uint32_t offset, uint8_t value);
bool reu_poke16(ReuHandle handle, uint32_t offset, uint16_t value);

#endif
