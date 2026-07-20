# ActionC64U REAL32

## Format

`REAL32` follows IEEE-754 binary32 layout:

- bit 31: sign
- bits 30..23: biased exponent
- bits 22..0: stored fraction

Precision is 24 bits for normalized values because the leading `1` is implicit.
The exponent bias is `127`.

## Source Semantics

Supported forms include decimal literals, exponent notation, arithmetic
operators, comparisons, `REAL(x)`, and `INT(r)`.

Rules:

- mixed integer/REAL expressions promote the integer operand to REAL first
- REAL comparisons produce integer truth values: `0` or `1`
- REAL-to-INT conversion truncates toward zero
- REAL-to-INT conversion fails if the truncated result is outside
  `-32768..32767`
- arithmetic uses round-to-nearest with ties to even across the complete
  binary32 finite range, including gradual underflow through subnormals
- arithmetic can produce signed infinity and canonical quiet NaN; native
  `REAL CONST` also accepts `INF`/`INFINITY` and `NAN`
- NaN is unordered: `<`, `<=`, `=`, `>=`, and `>` are false, while `<>` is true
- the runtime uses the default round-to-nearest, ties-to-even environment; it
  does not expose exception flags, traps, or alternate rounding modes

## Compile-Time Constants

Native ACTC evaluates `REAL CONST` expressions before object emission. The
grammar accepts decimal and exponent notation, `$`/`0x` hexadecimal and `%`
binary integers, earlier REAL constants, unary signs, grouping, binary
`+`/`-`/`*`/`/`, `REAL`, `FABS`, `FSQRT`, `INF`/`INFINITY`, and `NAN`.
Expressions are bounded to 64 bytes and a 16-value evaluation stack.

Decimal text is converted from an exact 448-bit integer ratio. Conversion and
every arithmetic step round to binary32 with round-to-nearest, ties-to-even,
including subnormal, overflow, signed-zero, infinity, and canonical-NaN cases.
The resulting two little-endian words are substituted directly into compiler
input. Constant-only work therefore imports no target conversion or arithmetic
helper. The resident evaluator reuses a deterministically generated private
copy of the shared OBJ1 runtime closure, so compile-time and target arithmetic
stay aligned without linking those private routines into an application.

## Runtime Symbols

The linker-level REAL runtime surface uses stable helper symbols:

- `rt_f_add`
- `rt_f_sub`
- `rt_f_mul`
- `rt_f_div`
- `rt_f_cmp`
- `rt_f_sign`
- `rt_f_min`
- `rt_f_max`
- `rt_f_abs`
- `rt_f_sqrt`
- `rt_i_to_f`
- `rt_s_to_f`
- `rt_f_to_i`
- `rt_print_f`

`rt_f_special` is an internal dependency selected transitively by ALINK for
arithmetic, comparison, and square-root helpers. Source code does not import it
directly.

## Target Helper ABI

The first implemented target-side helper ABI is intentionally narrow:

- `rt_i_to_f` accepts an unsigned 16-bit integer in `A` low and `X` high,
  and writes the converted REAL32 value through the destination pointer in zero
  page `$02/$03`
- `rt_s_to_f` accepts a signed 16-bit integer in `A` low and `X` high, and
  writes the exact REAL32 value through the destination pointer in zero page
  `$02/$03`
- `rt_f_to_i` reads a REAL32 value through the source pointer in zero page
  `$02/$03`, returns the signed 16-bit truncated result in `A` low and `X`
  high for every finite value whose truncated result is in `-32768..32767`;
  signed zeroes, subnormal magnitudes below one, and finite fractions truncate
  toward zero, while out-of-range values, infinities, and NaNs return zero
- `rt_f_add` reads source REAL32 pointers from `$02/$03` and `$04/$05`, writes
  the result through destination pointer `$06/$07`, and handles finite signed,
  normal, and subnormal operands through a shared binary32 core with
  guard/round/sticky alignment and nearest-even result rounding; infinities,
  NaNs, and finite overflow follow IEEE-754 default result semantics
- `rt_f_sub` reads source REAL32 pointers from `$02/$03` and `$04/$05`, writes
  the result through destination pointer `$06/$07`, and uses the same finite
  binary32 core with the second operand's sign inverted; cancellation,
  subnormal results, signed zero, infinities, NaNs, and nearest-even rounding
  are supported, with finite overflow producing signed infinity
- `rt_f_mul` reads source REAL32 pointers from `$02/$03` and `$04/$05`, writes
  the result through destination pointer `$06/$07`, and handles finite signed,
  normal, subnormal, and signed-zero operands using an exact 48-bit
  significand product with nearest-even result rounding; finite overflow
  produces signed infinity and invalid infinity-times-zero produces canonical
  quiet NaN
- `rt_f_div` reads source REAL32 pointers from `$02/$03` and `$04/$05`, writes
  the result through destination pointer `$06/$07`, and handles finite signed,
  normal, subnormal, and signed-zero operands using a restoring quotient with
  explicit guard, round, and sticky bits and nearest-even result rounding;
  division by zero, infinities, NaNs, and finite overflow follow IEEE-754
  default result semantics, while finite zero and underflow preserve the XOR
  result sign
- `rt_f_cmp` reads source REAL32 pointers from `$02/$03` and `$04/$05`, returns
  signed byte comparison in `A`/`X`: `-1` for less, `0` for equal, and `1` for
  greater, orders all signed finite and infinite binary32 values, and treats
  positive and negative zero as equal; it returns `2` for unordered NaN input
- `rt_f_sign` reads through `$02/$03`, writes through `$06/$07`, maps NaN to
  canonical quiet NaN, preserves either signed zero exactly, and writes
  `-1.0` or `1.0` for every other negative or positive input; it imports no
  other helper
- `rt_f_min` and `rt_f_max` read source REAL32 pointers from `$02/$03` and
  `$04/$05`, write through `$06/$07`, and preserve the selected operand's exact
  representation. One NaN is ignored, two NaNs select the right operand, and
  equal ordered operands select the left operand. Each imports `rt_f_cmp`, so
  comparison and exceptional-value support are selected transitively
- `rt_f_abs` reads a REAL32 value through zero page `$02/$03`, copies it to the
  destination pointer in `$06/$07`, and clears the sign bit in the copied value
- `rt_f_sqrt` reads a REAL32 value through zero page `$02/$03`, writes through
  destination pointer `$06/$07`, and handles every non-negative finite normal,
  subnormal, and signed-zero input using an exact 48-bit scaled radicand and a
  restoring integer square root with nearest result rounding; negative nonzero
  inputs produce canonical quiet NaN, positive infinity is preserved, and
  negative zero is preserved
- `rt_print_f` reads a REAL32 pointer from `$02/$03` and prints
  values through C64 `CHROUT` as their exact finite decimal expansion with
  trailing fractional zeroes removed; infinity and NaN print as `INF`, `-INF`,
  and `NAN`. The exact representation covers the complete normal and subnormal
  binary32 range without switching to a shortened scientific form
- REAL32 values are stored little-endian in memory, so `7.0` is
  `00 00 E0 40`
- unsupported wider inputs currently write `0.0`

ACTC lowers the covered REAL body operations to machine-code OBJ1 records and
ordinary helper imports. ALINK performs generic symbol closure, relocation, and
direct-PRG layout; it does not compile REAL source or interpret a private body
instruction set. Later slices should broaden ACTC's native REAL lowering beyond
the current bounded forms.

## Direct PRG Linking Rule

REAL support is link-time runtime-library code. ACTC should emit only the helper
imports required by reachable source code, and ALINK should include only those
helpers in the final PRG.

Examples:

- a REAL declaration by itself allocates four bytes and imports no arithmetic
  helper
- `+` on REAL values imports `rt_f_add`
- `-` on REAL values imports `rt_f_sub`
- `*` on REAL values imports `rt_f_mul`
- `/` on REAL values imports `rt_f_div`
- REAL comparisons import `rt_f_cmp`
- `REAL(x)` imports the matching integer bridge helper
- `INT(r)` imports `rt_f_to_i`
- `FAbs(r)` imports `rt_f_abs`
- `FSqrt(r)` imports `rt_f_sqrt`
- `FSign(r)` imports only `rt_f_sign`
- `FMin(a,b)` imports `rt_f_min` and its comparison closure
- `FMax(a,b)` imports `rt_f_max` and its comparison closure
- `PrintR` / `PrintRE` imports `rt_print_f` plus required text output support

Programs that do not use REAL must not pay for REAL helper code. Programs that
use only one REAL operation must not pay for unrelated REAL operators.

## Core Function ABI

A local core `REAL FUNC` returns a pointer to four-byte REAL storage in A/X;
the direct assignment caller copies all four bytes before continuing. In
addition to no-argument direct returns, the current C64-native parameterized
form accepts one typed two-byte scalar supplied by a direct integer literal or
by a named module word scalar initialized by the immediately preceding literal
assignment. It binds the value through the scalar stack ABI, evaluates
`REAL(parameter)` into named module REAL storage, and returns that storage. The
conversion helper remains an ordinary link-selected OBJ import. General
variable or expression arguments, arbitrary REAL return expressions,
nested/recursive calls, and external REAL functions remain separate compiler
work; they are not REAL32 range limitations.

## Action-Facing Reference

`LIB/MATH1.ACT` is the shipped Action-facing reference for the currently
implemented REAL32 helper surface. It documents the core source forms that ACTC
already recognizes directly: `REAL(x)`, `INT(x)`, REAL arithmetic/comparison
operators, `FAbs`, `FSqrt`, `FSign`, `FMin`, `FMax`, and `PrintR` / `PrintRE`.

`SRC/MATH1_DEMO.ACT` validates the exported-library path by compiling a small
REAL absolute-value program through ACTC, linking it with ALINK, and running
the linked `.PRG` directly. `FSqrt` covers all non-negative finite REAL32
inputs; broader math functions such as trig remain deferred
until matching link-selected `RT_*.OBJ` modules and their call ABI are
implemented.

## Current Status

The core REAL32 runtime helpers now implement default IEEE-754 binary32 value
semantics for addition, subtraction, multiplication, division, square root,
comparison, minimum/maximum selection, and signed decimal printing across
finite values, subnormals, signed zeroes, infinities, and NaNs. REAL-to-INT
remains the language conversion
defined above: out-of-range or non-finite input returns zero. The helpers
preserve lookup, dead-strip behavior, and the direct-PRG ABI; broader functions
such as trigonometry remain separate future link-selected modules.

The active implementation goal is direct linked PRG output with ALINK-owned
helper selection.
