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

The current compiler still evaluates REAL expressions on the host and lowers the
final printed result to string output, but it records these logical runtime
dependencies in the `.avo` object so dead-strip linking is already testable.
