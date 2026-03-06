# Language and System Spec (Very Early Draft)

## Language Direction

- Action-like syntax and ergonomics.
- Structured programming first.
- Clean-room implementation.

## Minimal Supported Syntax

Current host compiler support is intentionally tiny:

```text
[MODULE <identifier>]
PROC main()
  Print("string")
  PrintE("string")
RETURN
```

Rules:

- one source file produces one program
- `MODULE` is optional and currently ignored by code generation
- only `PROC main()` is recognized
- statements are limited to `Print("...")` and `PrintE("...")`
- `Print` emits no newline
- `PrintE` emits a newline after the string
- string literals must be ASCII

## Future Expansion

Planned later work includes:

- variables and expressions
- procedure calls beyond `main`
- conditionals and loops
- numeric types beyond the first print-only bootstrap
- richer runtime/file/VM services

## Numeric Types

- Integer primitives (details TBD).
- `REAL32`: 1 sign, 8 exponent, 24 mantissa.

## Memory Model

- Conventional near memory plus REU-backed far data.
- Overlay loading support for larger programs.

## Backend

- AcheronVM target with project-specific extensions where justified.
