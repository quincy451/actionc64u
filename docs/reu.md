# ActionC64U REU Model

## Goals

- provide far-data storage beyond the near working set
- support later overlay loading without changing source-level intent
- keep the first implementation host-testable under the current reference flow

## Logical Model

The bootstrap REU model is handle-based:

- each REU declaration allocates a logical handle
- accesses are expressed as `handle + byte offset`
- the simulated backend stores the bytes in host RAM
- a later real backend can map the same logical operations to actual C64 REU
  transfers

## Current Source Syntax

Implemented now:

```text
REU BYTE ARRAY big(50000)
ReuPoke8(big, 0, 65)
ReuPoke16(big, 2, 1234)
ReuPeek8(big, 0)
ReuPeek16(big, 2)
```

Current limitations:

- only `REU BYTE ARRAY` declarations are accepted
- source-level peek/poke support is currently `8` and `16` bit
- the runtime surface reserves `32` bit and copy helpers for later direct use

## Minimum Runtime API Surface

Stable logical symbols:

- `rt.reu_alloc`
- `rt.reu_free`
- `rt.reu_peek8`
- `rt.reu_peek16`
- `rt.reu_peek32`
- `rt.reu_poke8`
- `rt.reu_poke16`
- `rt.reu_poke32`
- `rt.reu_copy`

## Simulated Backend

The simulated backend is the first implementation:

- allocate a large host-side byte buffer per REU declaration
- bounds-check every access
- treat multi-byte values as little-endian
- keep behavior deterministic for tests and linker map inspection

This backend is the one used by the current host/reference compiler path.

## Real Backend

The real REU backend is deferred, but it is expected to preserve the same
logical API:

- same handle + offset abstraction
- same byte widths
- same copy semantics
- different storage/transfer implementation
