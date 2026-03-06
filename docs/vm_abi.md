# VM ABI for Minimal ActionC64U Intrinsics

This ABI is intentionally tiny and stable for the first compiler bootstrap.

## Register Convention

- `rP` carries the single argument for string-print intrinsics.
- The value in `rP` is a **payload-relative offset** to a NUL-terminated ASCII
  string inside the current `.avm` payload.
- The current payload base address is owned by `vm.com`, which will translate
  the relative offset into a real host address before printing.

## Intrinsic Pseudo-Targets

The compiler emits `calln` with reserved pseudo-addresses:

- `0xff00`: `Print`
- `0xff10`: `PrintE`
- `0xff20`: `Exit`

These are not final machine addresses. `vm.com` is expected to recognize or
rewrite them to the actual native helper entry points in its own process image
before execution.

## Semantics

### `Print`

- input: `rP = offset of NUL-terminated string`
- effect: print the string with no newline
- return: returns to the next Acheron instruction

### `PrintE`

- input: `rP = offset of NUL-terminated string`
- effect: print the string followed by the standard CP/M newline sequence
- return: returns to the next Acheron instruction

### `Exit`

- input: none
- effect: terminate the current payload/program cleanly
- return: does not return to the caller

## Integer Printing

For the current host-side reference compiler, `PrintI(expr)` and `PrintIE(expr)`
are lowered at compile time into ordinary `Print` / `PrintE` string operations.
That keeps the VM ABI stable while the CP/M-65 runner is still blocked.

## Minimal Compiler Pattern

For each emitted print action, the compiler writes:

1. `setp16 <string_offset>`
2. `calln <pseudo-target>`

At the end of `main`, the compiler emits:

1. `calln 0xff20`

This keeps the payload format compact while deferring machine-address fixups to
`vm.com`.
