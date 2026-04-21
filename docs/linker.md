# ActionC64U Linker And Object Format

## Goals

- Keep the bootstrap linker deterministic and easy to inspect.
- Preserve the final runnable artifact as a single `.avm`.
- Support dead-strip inclusion of only the runtime modules the program imports.
- Provide an on-target dead-strip path via `alink.com`.

## `.avo` Object Format

Current object files use a small text container so they are easy to diff and
inspect during bootstrap work.

Structure:

```text
AVO1
{"entry_offset":0,"exports":[["main",0]],"imports":["rt.print_line"],"module":"hello","payload_hex":"...", "version":1}
```

Rules:

- line 1 is the fixed magic/header: `AVO1`
- line 2 is compact JSON encoded as ASCII
- `version`: object format version, currently `1`
- `module`: logical module name
- `entry_offset`: byte offset into the payload where this object's entry begins
- `exports`: ordered list of `[symbol_name, offset]`
- `imports`: ordered list of imported symbol names
- `payload_hex`: code+data payload bytes encoded as lowercase hex

This is intentionally not ELF and does not attempt relocation yet. The linker
simply concatenates object payloads in a deterministic order and records the
resulting symbol map.

## Symbol Resolution

- the main object is always included first
- imported symbols are resolved against `.avo` files found in the supplied
  runtime module directories
- when a module is included, its imports are added to the worklist
- duplicate exports are link errors
- unresolved imports are link errors
- module inclusion order is deterministic: imports are resolved in sorted symbol
  order, with the main object fixed at the front

## `alink.com`

The repo now ships a first on-target linker:

- input: `main.avo` by default
- output: `main.avm` plus `main.map`
- runtime search path: current CP/M directory, scanning `*.avo`
- dead-strip scope today: module level

Important current limit:

- full per-user-function stripping is not possible until the compiler emits
  separate callable bodies as separate exported/imported object sections or
  object files

So the current on-target dead-strip behavior is already correct for runtime
library modules and any user program split into multiple `.avo` units, but not
yet for unused functions trapped inside one monolithic user object.

## UDOS-Native `ALINK.PRG`

The current UDOS-native linker consumes the bootstrap text AVO form emitted by
`ACTC.PRG`, not the host JSON line shown above. For reachable pending externals
it now resolves objects in this order:

- `OBJ/<symbol>.AVO`
- `LIB/<symbol>.AVO`

The root module still must come from `OBJ/<module>.AVO`. The `LIB/` fallback is
only for dependent objects, which is the intended path for runtime helpers such
as REAL operator modules.

Dependency inclusion is driven by live body operations. A `u <symbol>` line
defines an external symbol table entry, but ALINK only queues that dependency
when a live body references it with `uN`. This keeps runtime helpers used only
by dead-stripped procedures out of the final AVM.

Current target-side symbol spelling is identifier-style. Runtime modules use
underscore aliases such as `rt_f_add` until the UDOS text-object parser accepts
the dotted logical names (`rt.f_add`) used by the host/reference toolchain.

## Final `.avm`

The linked output remains:

- AVM header (`AVM1`)
- entry offset
- linked payload bytes
- optional overlay segment trailer when used

The linker also emits a sidecar map file:

- `<program>.map.txt`
- lists included modules
- lists final export addresses
- lists resolved imports

## Current Runtime Modules

Host/reference bootstrap runtime modules live under `src/runtime/modules/`:

- `rt.print_str`
- `rt.print_line`
- `rt.format_int`
- `rt.f_add`
- `rt.f_sub`
- `rt.f_mul`
- `rt.f_div`
- `rt.f_cmp`
- `rt.i_to_f`
- `rt.f_to_i`
- `rt.print_f`
- `rt.reu_alloc`
- `rt.reu_free`
- `rt.reu_peek8`
- `rt.reu_peek16`
- `rt.reu_peek32`
- `rt.reu_poke8`
- `rt.reu_poke16`
- `rt.reu_poke32`
- `rt.reu_copy`
- `rt.ovl_load`
- `rt.ovl_call`

For the current host reference compiler, `PrintI` / `PrintIE` are still lowered
to compile-time string output in the payload, and the same is currently true for
REAL arithmetic/printing. The compiler retains the logical runtime imports in
the `.avo` object so the dead-strip linker flow is already exercised and
testable.

For the UDOS-native compiler/linker path, REAL must remain a link-time runtime
library surface. REAL routines are not AVM interpreter opcodes. ACTC should emit
only the runtime symbols required by the reachable REAL operations, and ALINK
should include only those runtime objects in the final AVM image.

UDOS-target text AVO runtime modules live separately under
`src/runtime/udos_modules/` because `ALINK.PRG` does not parse the host JSON AVO
metadata format. The current `rt_f_add.avo` there is an ABI stub that returns
REAL32 zero and exists to prove exported `LIB/RT_F_ADD.AVO` lookup and linking;
it is not the final floating-point addition implementation.
