# Language and System Spec (Very Early Draft)

## Language Direction

- Action-like syntax and ergonomics.
- Structured programming first.
- Clean-room implementation.

## Current Supported Source Shape

The host reference compiler currently accepts a single-file program in this form:

```text
[MODULE <identifier>]
PROC main()
  [BYTE|CARD|INT name[,name...]]
  ...
  <statements>
RETURN
```

Current constraints:

- one source file produces one program
- `MODULE` is optional and currently ignored by code generation
- only `PROC main()` is recognized
- declarations must appear at the top of `main`, before executable statements
- comments start with `;`
- string literals must be ASCII

## Supported Statements

```text
name = expr
Print("string")
PrintE("string")
PrintI(expr)
PrintIE(expr)
PrintR(expr)
PrintRE(expr)
IF expr [THEN]
  ...
FI
```

Semantics:

- `Print` prints a string with no newline
- `PrintE` prints a string and a newline
- `PrintI` prints the decimal value of an integer expression with no newline
- `PrintIE` prints the decimal value of an integer expression and a newline
- `PrintR` prints the decimal form of a REAL expression with no newline
- `PrintRE` prints the decimal form of a REAL expression and a newline
- `IF` executes its body when the expression is non-zero

The parser already tolerates nested `IF ... FI`, but the implementation is still
intentionally small and single-procedure.

## Integer Types

- `BYTE`: 8-bit unsigned, range `0..255`
- `CARD`: 16-bit unsigned, range `0..65535`
- `INT`: 16-bit signed, range `-32768..32767`
- `REAL`: 32-bit floating-point value, format = 1 sign, 8 exponent, 24-bit precision

## Expressions

Supported expression forms:

- decimal literals, for example `123`
- hex literals, for example `$1A2B`
- REAL literals, for example `1.0`, `3.14`, `2e-3`
- variable references
- conversions: `REAL(x)`, `INT(r)`
- unary minus
- `+`, `-`, `*`, `/`
- comparisons: `=`, `<>`, `<`, `<=`, `>`, `>=`
- parentheses

## Promotion And Range Rules

Current reference-compiler rules:

- literals start as integer constants and are range-checked on assignment
- REAL literals are rounded to REAL32 immediately
- unary minus produces an `INT` for integer operands and `REAL` for REAL operands
- `+`, `*`, and `/` produce `INT` when either operand is `INT`; otherwise they produce `CARD`
- `-` produces `INT` when either operand is `INT` or when the computed result is negative; otherwise it produces `CARD`
- if either operand is `REAL`, the other operand is promoted to `REAL`
- REAL arithmetic rounds each result back to REAL32
- `REAL(x)` converts integers to REAL
- `INT(r)` truncates toward zero
- comparisons produce `CARD` values `0` or `1`
- assignment performs the final range check for the destination type
- assigning REAL directly to integer storage is rejected without an explicit `INT(...)`
- using an undeclared variable, reading an uninitialized variable, dividing by zero, or assigning an out-of-range value is a compile error

## Current Execution Model

The compiler is still a host-side reference implementation:

- it parses, type-checks, and evaluates the currently supported subset on the host
- it emits a deterministic `.avo` object first, then optionally auto-links to `.avm`
- it then lowers the resulting print actions into the minimal `.avm` payload format already used by the bootstrap VM path
- integer printing is currently lowered to string printing at compile time rather than emitted as a separate runtime intrinsic
- REAL arithmetic and printing likewise execute on the host today, while the compiler records logical float-runtime imports for the linker/map flow

This is deliberate while the CP/M-65 `vm.com` runner and fuller AcheronVM code
generation are still blocked by external toolchain availability.

## Future Expansion

Planned later work includes:

- procedure calls beyond `main`
- loops and richer control flow
- runtime-backed integer operations instead of host-only lowering
- dead-strip linking and library modules
- richer runtime/file/VM services

## Memory Model

- Conventional near memory plus REU-backed far data.
- Overlay loading support for larger programs.

## Backend

- AcheronVM target with project-specific extensions where justified.
