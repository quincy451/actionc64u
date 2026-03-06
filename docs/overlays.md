# ActionC64U Overlays

## Goals

- allow code larger than the near execution window
- keep overlay loading explicit and linkable
- make the bootstrap path testable without requiring VICE yet

## Model

Current overlay design:

- each overlay is compiled to a fixed logical name
- the linker packs used overlays into a separate overlay segment in the final
  `.avm`
- the runtime model assumes a single-slot load window is acceptable initially
- the logical loader API is explicit: load/swap, then call

## Syntax Implemented Now

Implemented bootstrap syntax:

```text
OVERLAY Math
  PrintIE(42)
ENDOVERLAY

PROC main()
  OverlayCall(Math)
RETURN
```

Current constraints:

- overlay blocks must appear before `PROC main()`
- only `PROC main()` exists as a direct entry today
- overlay calls use `OverlayCall(<name>)`
- the current host reference compiler executes overlay bodies on the host, then
  records logical overlay segments and runtime imports in the emitted `.avo`

## Runtime Surface

Stable logical symbols:

- `rt.ovl_load`
- `rt.ovl_call`

## Linker Behavior

- only overlays actually reached during the current reference compilation pass
  are emitted into the object/link output
- linked overlays are written into a distinct overlay segment after the main
  payload/modules
- the link map lists included overlays with their final offsets
