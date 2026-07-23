# ActionC64U Language Guide

The language target is the UDOS-native ActionC64U toolchain.

Build flow:

- source files live under `SRC/`
- `ACTC.PRG` compiles source to `OBJ/`
- `ALINK.PRG` links objects and helpers to `BIN/<MODULE>.PRG`

Runtime features should be represented as language/library bindings that lower
to linker-visible helper imports. ALINK decides which helpers enter the final
PRG.

## Source Preprocessing

Native ACTC preprocesses the staged source in REU through dedicated pass `I`
before declaration and body passes. `DEFINE`, `SET`, and `INCLUDE` therefore
work in the same source stream as ordinary Action declarations; they do not
create runtime code or force any library OBJ into the linked PRG.

ACTC first scans physical line starts through the streamed source reader. A
unit with no preprocessing directive is compiled from its original REU bytes,
so its established multi-window behavior and long ordinary lines are
unchanged. A directive or typed `CONST` may appear before or after `MODULE`; if
one is present, the complete bounded unit enters the atomic transform.

`DEFINE` accepts case-insensitive token substitutions. Values may be quoted or
unquoted, multiple definitions may be comma-separated, and a comma at the end
of a physical line continues the definition list on the next line.

```action
DEFINE U16="CARD", ONE=1,
  DOUBLE="ONE+ONE"

U16 RESULT=DOUBLE
```

Expansion is repeated so a definition can reference an earlier or later
definition. Only complete identifier tokens are replaced. Text inside double-
quoted strings, apostrophe character constants, and `;` comments is preserved.
Directive lines become blank source lines so diagnostics retain stable line
numbers. A repeated expansion that does not make progress is rejected as a
cycle.

`SET left=right` is accepted and syntax-checked, then removed from the source.
It is a compatibility directive only: neither the UDOS compiler nor the Idun
host compiler writes target memory while compiling. Program initialization
belongs in declarations, emitted code, or a linked library routine.

`INCLUDE "name"` recursively inserts an Action source file at that position.
The `.ACT` suffix is optional. An unqualified include first searches the
including file's area (`SRC` or `LIB`) and then the other project area. Use
`SRC/name` or `LIB/name` to select one explicitly. Names are case-insensitive;
subdirectories, parent traversal, and device-qualified paths are deliberately
not accepted by the native UDOS path contract. Include cycles are rejected.

Native preprocessing stores up to 255 definition records in a packed 1,350-byte
table, with 24 characters per definition name, 64 characters per replacement,
16 expansion passes, seven simultaneously included files, 24 characters per
normalized include filename, 255 characters per physical input line in a
directive-bearing transform, 254 characters per expanded line, and 65,535
bytes per included or fully transformed source unit. Short names and values use
only their actual record space; a larger redefinition supersedes its old packed
record. The original REU source is replaced only after
preprocessing succeeds, so a bad directive cannot leave later compiler passes
with a partial transformation. Directive-free units retain ACTC's streamed
line behavior instead of inheriting the transform's physical-line bound.
Sources larger than 65,535 bytes retain ACTC's streamed multi-megabyte compile
path but do not enter the directive transform; split directive-using sources
into included units within the preprocessing bound.

Typed constants are compile-time substitutions and never allocate OBJ storage.
`BYTE`/`CHAR`, `CARD`, and `INT CONST` use the shared Idun integer-expression
grammar after earlier `DEFINE`/`CONST` substitutions. The bounded evaluator
supports parentheses; unary `+`/`-`; `+`, `-`, `*`, `/`, `MOD`, `LSH`, and
`RSH`; `&`, `%` (OR), and `!`/`XOR`; decimal, `$` hexadecimal, `%` binary, and
`0x` hexadecimal literals; apostrophe character literals; and the shared
input, SID, and sprite constants. Intermediate values are checked signed
64-bit integers, shift counts are `0..62`, and right shift follows Idun's
logical 64-bit behavior. Native ACTC then enforces `0..255`, `0..65535`, and
`-32768..32767` for BYTE/CHAR, CARD, and INT respectively. Comma-separated
declarations may continue on the next physical line. Typed constants share the
packed definition store and each replacement remains bounded to 64 characters;
redefining a built-in is accepted only with its existing value.

`REAL CONST` is also a storage-free compile-time substitution. Its bounded
binary32 evaluator accepts decimal and exponent literals, `$`/`0x` hexadecimal
and `%` binary integers, prior REAL constants, unary `+`/`-`, parentheses,
`+`, `-`, `*`, `/`, `REAL(...)`, `FABS(...)`, `FSQRT(...)`, `INF`/`INFINITY`,
and `NAN`. Decimal conversion and every intermediate operation use
round-to-nearest, ties-to-even. Expressions are limited to 64 bytes and the
recursive evaluator has a 16-value stack. A malformed or over-capacity
expression reports `BAD CONST`.

ACTC substitutes the final four-byte value, not the source expression. A use
such as `REAL CONST VALUE=(1.5+2.25)*2.0` therefore emits the binary32 value
`7.5` directly and does not import conversion, arithmetic, absolute-value, or
square-root runtime helpers. Only subsequent runtime operations, such as
`PrintRE(VALUE)`, select their referenced OBJ modules.

## Inline 6502 Assembly

The core C64 compiler accepts `ASMBLOCK [ ... ]` inside a `PROC` or word
`FUNC` body. The
block is assembled by ACTC and inserted at that source position as ordinary
machine bytes and relocation records in the module OBJ. ALINK does not parse
the assembly; it performs its normal symbol closure and emits the final direct
PRG.

```action
CARD RESULT

PROC SET(P)
  CARD LOCAL
  ASMBLOCK [
START:
    LDA P
    STA LOCAL
    LDA LOCAL
    STA RESULT
    LDA #<RESULT
    STA $FB
    LDA #>RESULT
    STA $FC
    JMP DONE
DONE:
  ]
  RETURN
```

The assembler accepts the official NMOS 6502 instruction set and implied,
accumulator, immediate, zero-page, zero-page indexed, absolute, absolute
indexed, indirect, indexed-indirect, indirect-indexed, and relative addressing.
Numbers may be decimal, `$` hexadecimal, or `%` binary. Identifiers are
case-insensitive, and `;` starts a comment through the end of the source line.

An absolute symbol operand may name a module global, a parameter or local
scalar of the current routine, or a module-local routine export. ACTC emits a
normal OBJ relocation to that linked target. Core `BYTE`, `CARD`, and `INT`
scalar storage is two bytes; an ordinary `LDA` or `STA` accesses the low byte,
while indexed addressing can select the next byte. `REAL` globals and locals
have four-byte storage; use indexed addressing with offsets zero through three
to access the complete value. ASMBLOCK treats those bytes as storage and does
not perform floating-point conversion or arithmetic implicitly.

Labels declared with `NAME:` are private to that block. Relative branches are
resolved by ACTC, including forward branches. Absolute `JMP` and `JSR` label
operands become named local relocations. A label cannot be referenced from a
different ASMBLOCK.

`#<NAME` and `#>NAME` load the low and high byte of the final linked address of
a module global, current routine parameter or local, module-local routine, or
block-local label.
ACTC emits one-byte OBJ relocations, so these forms remain correct when ALINK
changes object placement. The same operators may extract bytes from numeric
constants, for example `#<$1234` is `$34` and `#>$1234` is `$12`.

Relocatable operands may add or subtract a constant, for example `LDA VALUE+1`,
`STA VALUE-1`, `LDA #<VALUE+1`, or `LDA #>VALUE+1`. Native ACTC accepts decimal,
hexadecimal, and binary addend magnitudes whose signed result is -128 through
127. The addend remains in the OBJ relocation and is applied by ALINK after
final placement, rather than being folded into a guessed compile-time address.

Current limits are 15 ASMBLOCKs per module, 176 emitted bytes per block, 16
assembler labels and 16 relocations in each block page, and 24 characters per
assembler identifier. Pass 9 has eight local-label slots per procedure shared
by Action control-flow lowering and ASMBLOCK labels, so the effective emitted
label limit can be lower than the page-format limit. Parameter and local-symbol
binding applies equally to procedures and core word functions.

Assembly directives, macros, and data declarations are not accepted; use
instructions and Action-linked storage.

ASMBLOCK may be combined with normal Action control and link-selected library
calls in the same routine. ACTC emits one machine-code OBJ for the routine; the
assembly references and helper calls remain ordinary relocations and imports,
so ALINK includes only the referenced helper closure. For example, a function
may copy a `CARD` parameter to a local in ASMBLOCK, call `SidVol(local)` inside a
`WHILE`, inspect that local in another ASMBLOCK, and return it through A/X.

## Fixed Register-Entry Routines

`PROC name=*(...)` and `BYTE`, `CARD`, or `INT FUNC name=*(...)` declare an
inline 6502 routine with the shared Idun register ABI. The body may use
instruction-oriented `ASMBLOCK [ ... ]` or an unchecked raw `[ ... ]` code
block. Either form supplies the complete routine and must execute `RTS` itself.

Parameter bytes are flattened from left to right. A BYTE contributes one byte;
a CARD or INT contributes low byte then high byte. Byte positions zero, one,
and two arrive in A, X, and Y. Positions three through fifteen arrive in
zero-page cells `$A3` through `$AF`. A routine may therefore accept at most 16
flattened bytes and at most 15 source parameters. REAL parameters and results
are not part of this ABI.

A BYTE function returns its value in A; ACTC zero-extends X at the call site. A
CARD or INT function returns low byte in A and high byte in X. A procedure has
no result. Fixed register-entry bodies cannot declare Action locals or contain
ordinary Action statements; use globals, registers, fixed memory, parameters
through the ABI above, and ASMBLOCK-local labels. ALINK receives an ordinary
machine-code export and JSR relocation and does not add a runner or interpreter.

```action
BYTE FUNC FOURTH=*(BYTE A,B,C,D)
  ASMBLOCK [
    LDA $A3
    RTS
  ]

PROC MAIN()
  RESULT=FOURTH(1,2,3,77)
  RETURN
```

Decimal, hexadecimal (`$`), and binary (`%`) call arguments are covered by the
native object, REU-window, and live machine-routine matrix. Raw blocks emit
numeric values up to 255 as one byte and larger or negative values as a
little-endian word. They also accept apostrophe character constants, positive
constant sums such as `4+$A7`, compact values such as `[$FFA2$A686]`, current
storage or local-routine symbols with signed addends, and `*` for the current
code address. These values become ordinary OBJ1 bytes and relocations; ALINK
does not parse the raw source. `DEFINE` substitutions are applied before raw
blocks are parsed, including fixed numeric addresses and constant sums.
Linked external routine-symbol expressions remain part of the wider native
compiler/address backlog. Use ASMBLOCK for checked opcodes and local jump
labels.

## Absolute-Address Routines

A bodyless procedure or BYTE/CARD/INT function may bind directly to a checked
constant expression whose result is a 16-bit machine address.

```action
PROC KERNALOUT=($FFD0+2)(BYTE VALUE)

PROC MAIN()
  KERNALOUT(33)
  RETURN
```

The declaration emits no wrapper, export, import, or library dependency. Each
call flattens its arguments through the same A/X/Y/`$A3+` ABI documented above
and emits a direct `JSR` to the declared address. BYTE results return in A and
CARD/INT results return in A/X. The same 15-parameter, 16-byte ABI limits apply;
REAL parameters/results, duplicate declarations, out-of-range addresses, and a
declaration body are rejected.

Numeric absolute-address calls can coexist in one unit with ordinary Action
control, runtime-library calls, ASMBLOCK, and `=*(...)` routines. Pass J owns
compact fixed-only units; composed units fall through to the universal pass H
without changing OBJ1 or direct-PRG semantics.

A declaration may also alias a real routine in the same module. Forward and
backward targets are accepted. One side of a top-level `+` is the routine name;
the other is any checked integer constant expression whose result fits signed
16-bit. Negative values use forms such as `WORKER+-1`.

```action
PROC WORKERALIAS=WORKER()
PROC ENTRYPLUSSIX=WORKER+(2*3)()
PROC ENTRYPLUSFOUR=(1 LSH 2)+WORKER()
```

ACTC emits a zero JSR operand and an ordinary `x worker [addend]` OBJ1
relocation, so ALINK remains responsible for final placement. The alias itself
has no export or target storage. Native pass I canonicalizes numeric and linked
address expressions before the bounded declaration pass; Idun accepts the same
portable forms through its host parser.

## Core Word Functions

The UDOS-native C64 compiler supports `BYTE`, `CARD`, and `INT` functions with
two-byte scalar parameters and locals. Parameters may carry an explicit scalar
type, including grouped declarations such as `CARD A,B`.

```action
CARD RESULT

CARD FUNC VALUE(CARD P)
  CARD LOCAL
  ASMBLOCK [
    LDA P
    STA LOCAL
  ]
  RETURN(LOCAL+1)

PROC MAIN()
  RESULT=VALUE(41)
  RETURN
```

A function must use `RETURN(expression)`; bare `RETURN` remains the normal
procedure form. Legacy `RETURN(expression)` under `PROC` remains accepted for
source compatibility but does not declare a typed callable result. Function
calls may appear in word expressions. The generated 6502 ABI returns the low
result byte in A and the high result byte in X; ACTC immediately places both
bytes back on its expression stack at a call site. Array/pointer parameters and
recursive core word-function calls are not part of this C64 compiler slice.

## Core REAL Functions

The native C64 compiler accepts a direct-return form for a local, no-argument
`REAL FUNC`:

```action
REAL SOURCE
REAL RESULT

REAL FUNC VALUE()
  RETURN(SOURCE)

PROC MAIN()
  SOURCE=REAL(42)
  RESULT=VALUE()
  RETURN
```

The function returns the address of the named four-byte REAL storage in A/X.
The direct assignment caller immediately copies all four bytes to its target,
and ALINK still selects only the conversion/runtime helpers referenced by the
module. The source and target need not be the first two declarations; ACTC
derives each module REAL export, aggregate data size, and return-pointer offset
from declaration order. Mixed module-global layouts preserve two-byte
`BYTE`/`CARD`/`INT` scalar storage and four-byte REAL storage; the selected
return source and assignment destination must be REAL. Parameterized REAL
functions have one additional native form: exactly one typed two-byte scalar
parameter, a direct integer-literal argument, conversion into named module REAL
storage, and return of that storage:

```action
REAL SOURCE
REAL RESULT

REAL FUNC VALUE(CARD P)
  SOURCE=REAL(P)
  RETURN(SOURCE)

PROC MAIN()
  RESULT=VALUE(42)
  RETURN
```

The argument uses the established scalar stack ABI and is bound to its declared
two-byte storage before `REAL(P)` calls the link-selected conversion helper.
The first named-storage form also accepts an immediately initialized module word
scalar:

```action
CARD ARG

PROC MAIN()
  ARG=42
  RESULT=VALUE(ARG)
  RETURN
```

ACTC emits ordinary relocations for every store and load of `ARG`; ALINK does
not interpret the function body. This early named-storage path remains bounded.

Pass L provides a broader all-REAL straight-line form with up to two functions,
exactly two REAL parameters per function, bounded REAL locals, and nested REAL
return trees. `MAIN` may call either function. The later function may call the
earlier one as the complete right side of a REAL assignment:

```action
REAL FUNC LENGTH(REAL A,B)
  RETURN(FHypot(FAbs(A),FAbs(B)))

REAL FUNC CHAIN(REAL A,B)
  REAL BASE
  BASE=LENGTH(A,B)
  RETURN(FMax(BASE,FAbs(A)))
```

The earlier call may also feed a supported intrinsic expression directly:

```action
REAL FUNC CHAIN(REAL A,B)
  RETURN(FMax(LENGTH(A,B),FAbs(A)))
```

Bounded calls to another function in the acyclic graph may also supply both
arguments to a call. ACTC spills each completed result before evaluating the next argument, so
the callee's static result and parameter cells cannot alias the outer call:

```action
REAL FUNC LOWER(REAL A,B)
  RETURN(FMin(A,B))

REAL FUNC CHAIN(REAL A,B)
  RETURN(LOWER(LOWER(A,A),LOWER(B,B)))
```

Each call uses an ordinary OBJ1 export relocation and returns a four-byte result
pointer in A/X. An assignment copies that result; a nested intrinsic consumes a
private temporary, and a nested user call receives independently spilled
argument results. Around every function-to-function call, ACTC stack-saves the
caller's static parameters, locals, and live temporaries, stages the returned
value, and restores the caller cells. Edges may therefore point forward or
backward when the graph remains acyclic. ACTC rejects self and mutual cycles
instead of falling back to generic object emission.

Pass M also accepts one nonnested `IF`/`ELSE` per supported REAL function when
both arms join before one terminal return:

```action
REAL FUNC PICK(REAL A,B)
  REAL CHOICE
  IF A<B THEN
    CHOICE=A
  ELSE
    CHOICE=FMax(A,B)
  FI
  RETURN(CHOICE)
```

All six REAL relations use `rt_f_cmp`; the false and end destinations are
ordinary relocatable OBJ1 code labels. Pass N extends this form to at most two
conditionals per function. They may appear sequentially or one may be nested
inside either arm of the other, up to depth two. Each conditional receives an
independent `__rfNN` false label and `__reNN` end label, so ALINK sees only
ordinary OBJ1 exports and relocations.

Pass O claims functions containing a third conditional and extends the same
format to four controls per function and nesting depth four. Four is the
documented native bound because a fully formed function must also fit the
64-operation debug bank; the compiler does not advertise unreachable slots.

Pass P accepts `RETURN(expr)` inside any of those bounded `IF`/`ELSE` arms. The
return value pointer is produced immediately and the machine routine exits;
ACTC continues parsing only to validate and relocate the remaining labels. A
terminal fallback `RETURN(expr)` after the controls is still required.

Pass Q accepts up to four bounded REAL-function loops, in either post-test
`DO ... UNTIL condition ... OD` form or pre-test
`WHILE condition DO ... OD` form. Conditions use the same six REAL relations
as Passes M through P. Each loop receives an ordinary relocatable `__rbNN`
back-edge label; a `WHILE` loop also receives a relocatable `__rzNN` exit label.

Pass R accepts the same four-loop bound plus plain `DO ... OD` and
unconditional `EXIT`. `EXIT` always targets the nearest active `DO` or
`WHILE`; ACTC emits it as a relocation to that loop's independent `__rzNN`
post-loop label. A plain loop without `EXIT` intentionally remains infinite.

Pass S accepts up to four nested or sequential local CARD-counter loops in the
supported REAL-function form, subject to the shared 64-operation body/debug
budget:

```action
FOR I=1 TO 5 STEP 2
DO
TOTAL=TOTAL+DELTA
OD
```

The initial and final values must be integer constants. The optional signed
constant step defaults to `1` and must be nonzero. Comparison is unsigned and
inclusive; overflow or underflow ends the loop instead of wrapping.

Pass T extends the same bounded form so either initial or final value may be a
named CARD. A named initial value is copied when the loop is entered; a named
final value is staged once before the loop back edge, so later changes do not
alter that invocation's bound. General bound expressions, nonconstant steps,
and composing `REAL(I)` into the nested REAL body expression are not yet
accepted by this collector/emitter path.

Mixed loop/conditional nesting, returns from inside loops, more than four
controls, deeper control nesting,
recursive/reentrant frames, unrestricted user-call argument trees and
nested call expressions, mixed parameter types, arbitrary signatures,
recursive calls, and external REAL functions are not yet part of this native
path.

## Dynamic Word Arithmetic

ACTC preserves normal product-before-sum precedence for dynamic word
expressions using `+`, `-`, `*`, `/`, and parentheses. ACTC lowers product
expressions into ordinary OBJ1 `m` machine-code records with local data exports
and `r` relocations. ALINK follows the reachable imports and selects
`RT_I_MUL.OBJ`, `RT_I_DIV.OBJ`, and `RT_PRINT_I.OBJ` only when referenced; it
does not compile a separate integer instruction stream. Multiplication keeps
the low 16 product bits. Division currently uses an unsigned 16-bit quotient
and returns zero for a zero divisor. `PrintI` and `PrintIE` format their 16-bit
argument as signed decimal text.

## Word Loops And EXIT

Word `FOR` loops use this form:

```action
FOR I=0 TO 10 STEP 2
DO
  PrintIE(I)
OD
```

`STEP` is optional and defaults to one. ACTC evaluates the initial, final, and
step expressions once. A positive step selects an unsigned ascending test and
a negative step selects an unsigned descending test. A zero step skips the
body. Crossing `$FFFF` or `$0000` terminates the loop rather than wrapping into
an unbounded iteration.

A plain `DO ... OD` is an infinite loop. Post-test and pre-test loops use
`DO ... UNTIL condition OD` and `WHILE condition DO ... OD`. `OD` is the sole
loop closer. `EXIT` leaves the nearest active `DO`, `WHILE`, or `FOR` loop;
using it outside a loop is a compile error. ACTC lowers plain loop-back and EXIT
transfers to named machine-code relocations in the OBJ, so ALINK only resolves
normal object closure and does not interpret loop instructions.
Plain, post-test, and pre-test WHILE loops can contain dynamic word arithmetic
such as `I=I+1`. ACTC emits the update, condition, EXIT, and backward jump in
one relocatable machine OBJ. Only helpers actually referenced by that object
are selected into the PRG.

Integer control bodies can also call one-argument runtime procedures whose ABI
accepts the low argument byte in A, such as `SidVol(I+10)`, or a complete word
in X/Y, such as `SidCutoff(I+300)`. For word calls X receives the low byte and Y
the high byte. ACTC emits the argument expression and call as ordinary machine
code plus an import relocation. ALINK follows that import and its transitive OBJ
dependencies; it does not interpret the source control-flow or call shape.

## Optional Linux Arrays, Pointers, And Functions

The additive Linux compiler accepts `BYTE ARRAY`, `CARD ARRAY`, `INT ARRAY`, and
`REAL ARRAY` declarations globally or inside procedures. Array subscripts are
zero-based word expressions and do not add target-side bounds checks. REAL
elements occupy four bytes and can be used directly in REAL expressions,
assignments, and comparisons.

`BYTE POINTER`, `CARD POINTER`, `INT POINTER`, and `REAL POINTER` values are
16-bit C64 addresses. `@variable` obtains linked storage's address and
`pointer^` reads or writes the pointed-to value. REAL array and pointer
parameters pass that address through the local-routine ABI.

Typed functions use declarations such as `CARD FUNC Square(CARD value)`.
Every function must contain a `RETURN(expression)`; ordinary procedures may
only use bare `RETURN`. BYTE, CARD, and INT results return in `A`/`X`, while REAL
results return the address of a function-owned four-byte cell in `A`/`X`.
Function calls can be nested in word and REAL expressions. Call edges in direct
or mutual recursion preserve mutable scalar parameters, scalar locals, and
compiler temporaries on the 6502 hardware stack. Recursion depth is therefore
stack-bounded. Local array storage remains shared, and the ABI does not support
asynchronous or general reentry.
