# REU Backend ABI

ActionC64U keeps the REU-facing API stable across simulated and hardware
backends so the compiler and VM can switch implementations without changing
source-level semantics.

## Build Selection

The CP/M build scripts select the backend with:

```text
ACTIONC64U_REU_BACKEND=sim
ACTIONC64U_REU_BACKEND=hw
```

Current defaults:

- `sim` for local `cpmemu` builds
- `hw` is reserved for VICE / real C64 validation builds

## Stable C API

Declared in `src/runtime/reu_backend.h`:

- `reu_backend_reset()`
- `reu_backend_name()`
- `reu_alloc(size, &handle)`
- `reu_free(handle)`
- `reu_copy(dest_handle, dest_offset, src_handle, src_offset, length)`
- `reu_peek8(handle, offset, &value)`
- `reu_peek16(handle, offset, &value)`
- `reu_poke8(handle, offset, value)`
- `reu_poke16(handle, offset, value)`

## Simulated Backend

`src/runtime/reu_sim.c` is sparse and deterministic:

- allocations are handle-based
- unwritten bytes read back as zero
- only touched offsets consume local memory
- bounds checks are enforced on every access

This is the backend used by prompt-16 on-target tests under `cpmemu`.

## Hardware Backend

`src/runtime/reu_hw.c` currently preserves the API and backend-selection path
for VICE / real C64 work, but the transfer implementation is still a bootstrap
stub pending fuller VM runtime integration.
