# ActionC64U REAL32

## Format

`REAL32` follows the IEEE-754 binary32 bit layout:

- bit 31: sign
- bits 30..23: biased exponent
- bits 22..0: stored fraction

Precision is 24 bits for normalized values because the leading `1` is implicit.
The exponent bias is `127`.

## Special Cases

- zero uses exponent `0` and fraction `0`
- the current host reference compiler permits signed zero after underflow
- NaN and infinity are not source-level values; if an operation would overflow to
  a non-finite result, compilation fails with `REAL32 overflow`

## Rounding Model

The current compiler evaluates REAL expressions on the host, but rounds each
REAL literal, conversion, and arithmetic result back to binary32 by packing and
unpacking a native 32-bit float. That keeps the reference behavior aligned with
the intended 32-bit format even before a full runtime implementation exists.

## Literals

Supported forms:

- `1.0`
- `3.14`
- `2e-3`
- `-1.2E+5`

Unary minus is parsed separately, so negative literals are represented as a
positive REAL literal with a unary `-` operator applied to it.

## Operators

Supported REAL operators:

- arithmetic: `+`, `-`, `*`, `/`
- comparisons: `=`, `<>`, `<`, `<=`, `>`, `>=`

Mixed integer/REAL expressions promote the integer operand to REAL first.

## Conversions

- `REAL(x)`: converts an integer value to REAL32
- `INT(r)`: converts REAL32 to `INT` by truncating toward zero

Rules:

- integer-to-REAL conversion rounds to binary32 if needed
- REAL-to-INT conversion fails if the truncated result does not fit in
  `-32768..32767`
- assigning REAL directly to `BYTE`, `CARD`, or `INT` is rejected unless an
  explicit `INT(...)` conversion is used first

## Comparison Rules

- integer/REAL mixed comparisons promote the integer side to REAL
- comparison results are still integer truth values: `0` or `1`
- only finite REAL values are supported in the bootstrap compiler

## Overflow And Underflow Policy

- overflow: compile error
- division by zero: compile error
- underflow: allowed to round to signed zero

## Runtime Symbols

The linker-level REAL runtime surface currently uses these stable symbol names:

- `rt.f_add`
- `rt.f_sub`
- `rt.f_mul`
- `rt.f_div`
- `rt.f_cmp`
- `rt.i_to_f`
- `rt.f_to_i`
- `rt.print_f`

## UDOS-Native Linking Rule

REAL support must stay out of the AVM interpreter opcode set. REAL arithmetic,
conversion, comparison, and printing are link-time runtime-library routines.

ACTC should emit only the runtime symbols required by reachable source code:

- a REAL declaration by itself allocates REAL32 storage and does not import
  arithmetic or print code
- `+` on REAL values imports only `rt.f_add`
- `-` on REAL values imports only `rt.f_sub`
- `*` on REAL values imports only `rt.f_mul`
- `/` on REAL values imports only `rt.f_div`
- REAL comparisons import only `rt.f_cmp`
- `REAL(x)` imports only `rt.i_to_f`
- `INT(r)` imports only `rt.f_to_i`
- `PrintR` or `PrintRE` imports only `rt.print_f` plus the needed line/string
  output support

ALINK is then responsible for pulling only those runtime objects into the final
AVM image. Programs that do not use REAL must not pay for REAL code, and REAL
programs must not pay for unused REAL operators.

## Current UDOS-Native Slice

The current UDOS-native compiler/linker slice proves REAL declaration storage
metadata and the first operator-specific runtime import:

- `REAL X` emits a 4-byte variable slot in the AVO object
- ALINK preserves that 4-byte width in the linked AVM data layout
- `R=A+B`, where all three variables are `REAL`, emits a live import of only
  `RT_F_ADD` / `rt_f_add`
- no `-`, `*`, `/`, conversion, comparison, or print helper is imported for
  that source unless that operator is actually lowered later

The linker now has the required runtime-library lookup shape for per-operation
REAL helpers: pending externals search `OBJ/` first and then `LIB/`. The current
target-side text AVO spelling uses underscore aliases such as `rt_f_add`, which
map to the logical runtime symbols such as `rt.f_add`.

ALINK now queues helper objects from live `uN` body operations, not from
object-level `u <symbol>` metadata alone. That is required for REAL operator
dead-stripping: a helper mentioned only by a dead procedure must not enter the
final AVM image.

The repo now carries the first UDOS-target text runtime object under
`src/runtime/udos_modules/rt_f_add.avo`, and the workspace exporter overlays it
into `LIB/RT_F_ADD.AVO`. This file is currently an ABI stub: it returns REAL32
zero as low word then high word, so it proves library lookup, stack shape, and
dead-strip behavior without claiming numeric IEEE-754 addition yet.

## Current REAL Helper ABI

The current target-side REAL value ABI is intentionally simple:

- a `REAL32` stack value is two 16-bit cells
- cells are ordered low word first, then high word
- `RT_F_ADD` consumes `lhs.low`, `lhs.high`, `rhs.low`, `rhs.high`
- `RT_F_ADD` pushes `result.low`, `result.high`
- ACTC emits `L` / `U` body ops to load the low and high words
- ALINK lowers `U` to the existing AVM `LOAD` opcode at variable offset `+2`
- ACTC emits `T` / `S` after the helper so the high word is stored first and
  then the low word is stored
- ALINK lowers `T` to the existing AVM `STORE` opcode at variable offset `+2`

Until broader REAL expression lowering exists, the UDOS-native compiler still
rejects REAL initializers and rejects REAL use in the 16-bit integer expression
path. This avoids false success where only the low word of a REAL32 slot would
be read or written.

Full UDOS-native REAL32 literals, real IEEE-754 `+`, `-`, `*`, `/`,
comparisons, conversions, and `PrintR` / `PrintRE` lowering remain future work.
The host/reference compiler still has broader REAL behavior than the
UDOS-native ACTC path.
