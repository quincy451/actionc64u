# ACTC

`ACTC.PRG` is the UDOS-native compiler front end.

Current contract:

- input: `SRC/<MODULE>.ACT`
- output: `OBJ/<MODULE>.OBJ`
- object format: text object records consumed by `ALINK.PRG`
- runtime policy: emit object-level calls/imports only; final runtime selection
  belongs to `ALINK.PRG`
- preprocessing: bounded, atomic REU preprocessing supports token-aware
  `DEFINE`, compatibility `SET`, and recursive project `SRC`/`LIB` `INCLUDE`;
  storage-free BYTE/CHAR/CARD/INT constants use Idun's checked signed 64-bit
  parenthesized arithmetic, shift, and bitwise expression grammar, while REAL
  constant text is substituted into source forms handled by the current
  bounded REAL compiler
- inline assembly: `ASMBLOCK [ ... ]` emits official NMOS 6502 instructions,
  block-local labels, and ordinary OBJ word or `#<`/`#>` byte relocations to
  current globals, procedure/function parameters, locals, and module-local
  routine exports, including
  four-byte `REAL` global/local storage; relocatable operands accept signed
  `+constant`/`-constant` byte offsets from -128 through 127
- raw code blocks: `[ ... ]` emits unchecked byte constants, little-endian
  word and signed constants, apostrophe character constants, positive constant
  sums, and word relocations for current storage, local routines, or the
  current code address. Compact adjacent values are accepted. Native
  relocation addends remain bounded to -128 through 127
- core word functions: `BYTE`/`CARD`/`INT FUNC` declarations accept typed
  scalar parameters, require `RETURN(expression)`, and return low/high bytes in
  A/X; bare `RETURN` remains the normal procedure form
- fixed register-entry routines: `PROC` and `BYTE`/`CARD`/`INT FUNC` declarations
  using `=*(...)` may contain an `ASMBLOCK` or raw `[ ... ]` machine body.
  Parameter bytes are
  flattened left-to-right into A, X, Y, then `$A3` upward, with a maximum of 16
  bytes. BYTE results return in A and CARD/INT results in A/X. These bodies own
  their `RTS`, cannot declare Action locals, and do not support REAL parameters
  or results. Ordinary calls accept decimal, `$` hexadecimal, and `%` binary
  16-bit literal arguments
- absolute-address routines: bodyless `PROC` and `BYTE`/`CARD`/`INT FUNC`
  declarations may bind directly to a decimal, `$` hexadecimal, or `%` binary
  16-bit address, for example `PROC CHROUT=$FFD2(BYTE VALUE)`. Calls use the
  same 16-byte register ABI and emit a direct `JSR`; ACTC emits no wrapper,
  export, import, or runtime module for the declaration. They may instead alias
  a forward or backward local routine with an optional signed 16-bit literal
  addend, emitting an ordinary named OBJ1 relocation resolved by ALINK
- core REAL functions: a local no-argument `REAL FUNC` may return any directly
  named module four-byte `REAL` variable; the first parameterized form also
  accepts one typed word scalar supplied either by a direct integer literal or
  by a named module word scalar initialized by the immediately preceding
  literal assignment. It binds that parameter through the scalar stack ABI,
  converts it through `REAL(parameter)`, and returns the named converted
  storage. A/X carries the storage address and the assignment caller
  immediately copies all four bytes to any directly named module REAL
  destination, with export/data placement derived from each two-byte word
  scalar or four-byte REAL module-global declaration. A second bounded form
  accepts two `REAL` parameters by value, copies two named module REAL
  arguments into distinct callee storage in source order, and can return the
  first parameter by pointer. Its current caller shape requires the two named
  arguments to be initialized by the two immediately preceding `REAL(integer)`
  assignments. Dedicated pass K also accepts the exact finite select body
  `IF B<A THEN RETURN(B) FI RETURN(A)`, returning either parameter pointer after
  an ordinary `RT_F_CMP` call. Pass K also accepts a bounded single-return body
  whose expression is one selected binary operation over the two parameters:
  `+`, `-`, `*`, `/`, `FMin`, `FMax`, `FMod`, or `FHypot`. It emits the result
  into a hidden four-byte cell before returning its address, which keeps
  alias-unsafe helpers isolated from both parameters. Separately, the bounded REAL value parser lowers
  `FSign(A)`, `FTrunc(A)`, `FFloor(A)`, `FCeil(A)`, `FRound(A)`, `FFrac(A)`, `FMod(A,B)`, `FHypot(A,B)`, `FMin(A,B)`, and `FMax(A,B)` with named REAL operands in
  assignments, REAL printing, and conditions. Those calls use independently
  selected helpers with complete MATH1 NaN/signed-zero semantics. Pass L also
  accepts bounded nested combinations of those helpers plus `FAbs`, `FSqrt`,
  arithmetic, and `FClamp` in a one-procedure straight-line module-REAL program.
  It emits executable machine OBJ1 with private temporaries and selective
  imports. This is not general REAL function, local, control-flow, arbitrary-
  call, or return lowering.
  Pass K additionally owns a bounded four-REAL root that initializes three
  named values with `REAL(integer)`, assigns one named destination from
  `FClamp(value,lower,upper)`, prints a named value, and returns. The body
  matcher captures all initializer, argument, destination, and print operands
  and maps them to declared storage, so declaration and use order need not
  match the original `A/B/C/X` proof. It emits only integer conversion, clamp,
  and print imports; the clamp module's comparison/minimum/maximum dependencies
  remain ALINK-selected. The fixed statement skeleton is still not general
  three-argument call lowering.

`ACTC.PRG` should not emit a standalone runtime artifact and should not depend
on a separate launch program. The direct runtime product is created by ALINK.

The complete ASMBLOCK syntax and current resource limits are documented in
[language_guide.md](language_guide.md#inline-6502-assembly).

## Optional Linux Host Compiler

The additive Linux `actc` implementation supports linked
`BYTE`/`CARD`/`INT`/`REAL` arrays and typed pointers. REAL indices scale by four,
and indirect REAL reads and writes copy the complete four-byte target value.
Compiler-side array, pointer, and syntax metadata is dynamically sized; emitted
target storage remains constrained by the C64 address space.

Local `PROC` and typed `BYTE`/`CARD`/`INT`/`REAL FUNC` declarations accept
scalar, array, pointer, and REAL parameters. `RETURN(expression)` returns word
results in `A`/`X` and REAL results through a function-owned four-byte cell whose
address is returned in `A`/`X`. Function calls can be nested in word or REAL
expressions. The compiler derives the local call graph and spills a caller's
mutable scalar parameters, scalar locals, and compiler temporaries on every call
edge that participates in a recursion cycle. It restores those cells while
preserving the returned value. This supports stack-bounded direct and mutual
recursion for scalar state. Local array storage remains shared, and asynchronous
or general reentry remains unsupported.
