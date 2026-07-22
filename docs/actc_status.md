# ACTC Status

Current state:

- UDOS-native `ACTC.PRG` builds successfully.
- The maintained compiler output is `OBJ/<MODULE>.OBJ`.
- The active end-to-end proof is direct PRG launch through ALINK.
- Streamed source preflight remains resident, module validation remains in pass
  1, and atomic preprocessing now runs in dedicated base-36 pass
  `ACTC_OVLI.BIN`. This preserves directive-free REU bytes. Pass `I` now folds
  the shared signed 64-bit integer `CONST` grammar, packs definitions into the
  original 1,350-byte table footprint, canonicalizes routine-address constant
  expressions, and folds bounded `REAL CONST` expressions at binary32 precision.
  Decimal conversion and every operation use round-to-nearest, ties-to-even;
  constants emit literal words without selecting target arithmetic helpers.
  Pass I occupies 7,680 bytes and retains exactly its enforced 512-byte reserve
  because the evaluator is resident behind the overlay ABI.
- ACTC now emits real `m` machine-code records for the empty `MAIN` return
  case and the first no-data local-call graph slices (`single_call`, `fanout`).
  ALINK no longer carries matching root-body templates for those native cases.
- The native integer emitter now carries string literals in its initialized
  data range and lowers surrounding string output and ordinary external calls.
  The imported `printmath` proof uses this path for `PrintE`, a library call,
  variable-dependent integer arithmetic, and link-selected `rt_print_i`.
- Dynamic word expressions containing `*` or `/` now emit native 6502 machine
  records, overlapping local initialized-data exports, and generic relocations.
  ALINK consumes these through its normal object-code path rather than compiling
  an ACTC body sequence.
- Straight-line word assignments, loads, and load/store copies use the same
  native object emitter, including initialized-data and pointer relocations.
- `ACTC_OVL9.BIN` runs before the general integer emitter and owns
  multi-procedure local control plus simple one-procedure plain `DO`, `WHILE`,
  and `DO`/`WHILE` `EXIT` bodies. Remaining single-procedure native integer
  generation, including dynamic-arithmetic plain and post-test `DO`/`EXIT`,
  runs in `ACTC_OVL8.BIN`; native REAL
  bridge emission runs in base-36 pass `ACTC_OVLA.BIN`; native REAL control
  emission runs in `ACTC_OVLB.BIN`; native REAL `WHILE` emission runs in
  `ACTC_OVLC.BIN`; runtime condition, sequence, and nested-readback emission
  run in `ACTC_OVLD.BIN`, `ACTC_OVLE.BIN`, and `ACTC_OVLF.BIN`; one-argument
  byte-in-A and word-in-X/Y runtime calls inside integer control run in
  `ACTC_OVLG.BIN`; compact units containing bodyless numeric absolute-address
  declarations or fixed register-entry machine bodies run in `ACTC_OVLJ.BIN`;
  the bounded two-REAL-parameter finite comparison/select function runs in
  `ACTC_OVLK.BIN`; bounded nested straight-line REAL trees run in
  `ACTC_OVLL.BIN`;
  units that combine fixed-address calls,
  `=*(...)`, inline assembly, and runtime-argument calls run in the universal
  `ACTC_OVLH.BIN`;
  generic object emission remains in `ACTC_OVL5.BIN`. Each pass has an explicit
  capacity gate appropriate to its current role.
- Core ACTC accepts `ASMBLOCK [ ... ]` inside procedures and word functions.
  Pass 4 performs a two-pass official NMOS 6502 assembly into one REU page per
  block, while pass 9, or mixed pass H, inserts the bytes at the body marker and
  emits ordinary named word or low/high-byte relocations for block-local labels
  and module, parameter, or local variables.
  Relative branches resolve in the compiler. ALINK remains a generic OBJ
  closure/relocation linker and never interprets inline assembly.
- Pass 9 and mixed pass H preserve declared storage widths for ASMBLOCK-visible
  variables. `BYTE`/`CARD`/`INT` storage remains two bytes, while `REAL`
  globals and locals export and emit four bytes; indexed 6502 operands can
  address offsets zero through three. Decimal operands now commit through the
  same streaming source cursor as hexadecimal and binary operands.
- Pass J accepts fixed register-entry `=*(...)` procedures and BYTE/CARD/INT
  functions with complete ASMBLOCK or raw `[ ... ]` bodies. Raw blocks emit
  unchecked byte/word/character constants, positive constant sums, and
  current-address, local-routine, or storage relocations. Calls flatten at most 16 parameter
  bytes into A/X/Y and `$A3-$AF`; BYTE results return in A and word results in
  A/X. Machine bodies own `RTS`, have no Action locals, and reject REAL ABI
  shapes. A resident metadata scan forces every such unit through pass J and
  rejects unsupported or over-16-byte signatures before opening its object
  stream, so it cannot silently fall back to an older emitter. Decimal, `$`
  hexadecimal, and `%` binary arguments share the streamed 16-bit token path.
  Exact OBJ relocations, zero-lookahead REU-window tests, and an eight-byte live
  VICE result probe cover no-argument, two-byte, four-byte, and mixed-width
  calls in both body forms.
- Core ACTC accepts bodyless `PROC` and BYTE/CARD/INT `FUNC` declarations bound
  to checked numeric constant expressions from 0 through 65535.
  Calls use the same register ABI and emit a direct `JSR`, with no wrapper,
  export, import, or selected runtime object. Pass J owns compact fixed-only
  units and declines composed units before output; pass H owns compositions
  with ASMBLOCK, runtime arguments, and `=*` routines. Focused exact-OBJ,
  direct-ALINK, and live-VICE coverage calls KERNAL CHROUT at `$FFD2`.
  Forward/backward aliases to real routines in the same module use a named
  relocation and accept a signed 16-bit checked constant-expression addend on
  either side of the symbol. A second
  source-backed direct PRG resolves `WORKERALIAS=(1-1)+WORKER()`, prints `!`, and
  selects no library object.
- Core ACTC now accepts typed `BYTE`, `CARD`, and `INT FUNC` declarations.
  Function parameters and locals use the existing two-byte scalar ABI and are
  visible to `ASMBLOCK`; `RETURN(expression)` returns low/high bytes in A/X,
  and callers restore that pair to the expression stack. Declaration pass 2
  rejects bare function returns. Legacy procedure value returns remain accepted
  without declaring a typed function ABI.
- The core `REAL FUNC` path accepts a local no-argument function whose
  `RETURN` directly names four-byte `REAL` storage. The function returns that
  storage address in A/X, and a direct assignment call copies all four bytes
  before continuing. Source and destination selectors, every module REAL export,
  the aggregate data size, and pointer placement are declaration-derived rather
  than fixed to the first two variable slots. Mixed module-global layouts retain
  two-byte `BYTE`/`CARD`/`INT` and four-byte REAL widths while computing
  cumulative exports; the selected source and destination must still be REAL.
  A constrained parameterized form accepts one typed two-byte scalar, binds
  either a direct integer literal or a named module word scalar initialized by
  the immediately preceding literal assignment through the scalar stack ABI,
  converts it with `REAL(parameter)` into named module REAL storage, and returns
  that storage. A second bounded form accepts two REAL parameters by value,
  preserves left-to-right argument order while copying each named module REAL
  into separate callee storage, and returns either named parameter by pointer.
  Its current caller requires two immediately preceding `REAL(integer)`
  assignments. Other statement sequences, general variable/expression
  arguments, arbitrary REAL return expressions, nested/recursive calls, and
  external REAL functions remain outside this native path.
- Simple integer equality, inequality, and all four unsigned ordered
  comparisons (`<`, `>`, `<=`, `>=`) now emit native compare, branch, and
  named forward-target relocation records from that pass.
- A simple integer equality `IF/ELSE` now emits `__if0` and `__if1` local
  targets for the else entry and join. Both branches are linked as ordinary
  named relocations, including imports that follow the conditional.
- Integer control flow now supports two nested `IF` levels and an inner
  `ELSE`, using fixed outer `__if0`/`__if1` and inner `__if2`/`__if3` local
  targets. Ordered comparison inversion is tracked per condition.
- Integer equality `DO ... UNTIL` loops support two nesting levels through
  compiler-owned `__do0`/`__do1` backward targets; simple less-than loops use
  `__do0`. ALINK no longer recognizes or compiles those compact loop bodies.
- Single-procedure word `FOR counter=initial TO final [STEP increment]` loops
  support two sequential or nested instances. ACTC evaluates the initial,
  final, and increment expressions once, stages final/increment values in
  relocatable local data, chooses ascending or descending comparison from the
  runtime increment sign, and emits named `__forN`/`__fendN` relocations. A
  zero increment exits without entering the body, and carry guards terminate
  loops that cross `$FFFF` or `$0000` instead of allowing wraparound to run
  forever. ALINK only resolves the emitted machine OBJ.
- Plain `DO ... OD` and post-test `DO ... UNTIL ... OD` bodies containing
  dynamic word arithmetic now remain in `ACTC_OVL8.BIN`. The compiler emits a
  named backward relocation to `__doN` and a distinct post-loop target for the
  nearest `EXIT`; ALINK does not recognize either control-flow shape. Pass-8
  FOR and post-test-loop debug mappings preserve exact machine offsets and
  control-token alignment across page boundaries.
- Pre-test `WHILE ... DO ... OD` bodies can combine dynamic word `+` and
  `-` updates with nested conditions and nearest-loop `EXIT`. Pass 9 emits
  the arithmetic, loop entry/exit, nested branch targets, and initialized data
  as one relocatable machine OBJ; unused integer helper modules remain absent.
- `EXIT` leaves the nearest active integer `DO`, `WHILE`, or `FOR` loop and is
  rejected outside a loop. FOR exits use the existing `__fendN` exports from
  `ACTC_OVL8.BIN`; simple DO and WHILE exits use pass-9 local labels, while
  arithmetic plain-DO exits use pass-8 labels. A plain `DO ... OD` emits its
  own backward JMP, and an EXIT target resolves after that loop-back
  instruction. All are ordinary absolute JMP relocations in compiler-emitted
  machine OBJ records.
- `ACTC_OVL8.BIN` is 6,719 bytes after FOR/FOR-EXIT, arithmetic plain/post-test
  DO/EXIT, relocation, and debug-offset compaction, leaving 1,473 bytes free in
  the 8 KiB emitter window under a pass-specific 1 KiB capacity reserve.
- `ACTC_OVL9.BIN` is 7,599 bytes after word-function call/return lowering,
  ASMBLOCK insertion, local-label and variable relocations, dynamic arithmetic,
  link-selected helpers, and
  DO/WHILE EXIT lowering. It leaves 593 bytes free under its dedicated
  128-byte minimum reserve. `ACTC_OVL6.BIN` is 8,094 bytes with 98 bytes free
  under a 96-byte gate. `ACTC_OVL7.BIN` is 6,678 bytes with 1,514 bytes free in
  its 8 KiB window, and raw-block-capable `ACTC_OVL4.BIN` is 5,603 bytes.
  Function-aware pass G is 6,645 bytes with 1,547 bytes free under a 512-byte
  gate. Universal mixed pass H is 8,064 bytes with exactly 128 bytes free under a
  128-byte gate. Fixed-address and register-machine pass J is 7,901 bytes with
  291 bytes free under a 256-byte gate. REAL function/ternary pass K is 5,877
  bytes with 2,315 bytes free in its 8 KiB window. Nested REAL postfix pass L
  is 6,124 bytes with 2,068 bytes free. Function-control pass M is 6,998 bytes
  with 1,194 bytes free under its dedicated 1 KiB gate. Two-control pass N is
  7,120 bytes with 1,072 bytes free under the same gate. Four-control pass O is
  7,123 bytes with 1,069 bytes free. Conditional-early-return pass P is 7,147
  bytes with 1,045 bytes free. Native REAL emitter
  pass A is 7,418 bytes with 774 bytes free under its 768-byte growth reserve.
  Passes H and J share pass 9's typed-parameter bind prologue, so runtime helper calls
  inside supported functions retain the word-return ABI. Pass F is 6,709 bytes
  with 1,483 bytes free under a 1,264-byte gate.
  Other native emission overlays retain their pass-specific capacity gates.
- One-procedure integer `WHILE` conditions using `=`, `<>`, `<`, `>`, `>=`,
  or `<=` emit compiler-owned head and exit targets plus ordinary forward and
  backward relocations. ALINK links the machine-code OBJ without recognizing
  the source control-flow shape.
- Local procedures now emit named exports, local-call relocations, per-procedure
  control targets, shared initialized data, nested `IF`/`ELSE`, and nested
  equality loops as ordinary machine-code OBJ records. The eleven local-call
  matrix shapes no longer rely on linker-side body templates.
- A local helper call inside a less-than `WHILE` now has source-backed compile,
  link, and launch coverage. Its call, loop head, and loop exit are independent
  named relocations in the compiler-emitted machine OBJ.
- Stack-neutral no-argument external calls inside pass-9 integer control emit
  ordinary `JSR` import relocations. Each exported procedure body carries its
  own transitive import closure, while pure call-only bodies continue through
  the general emitter. A live `SidRst()` WHILE case proves ALINK selects its
  transitive SID state helpers, prunes unrelated SID objects, clears prefilled
  SID registers, and leaves the loop variable equal to one.
- One-argument runtime calls whose helper ABI consumes the low argument byte in
  A now compose with the same integer control lowering through pass G. The
  emitter consumes exactly one word expression, emits ordinary argument setup
  and a `JSR` import relocation, and declines helpers with wider or unknown
  ABIs. A live `SidVol(I+10)` WHILE case proves link-selected SID closure,
  unrelated SID pruning, volume register value 10, and loop-variable value one.
- One-argument runtime calls whose helper ABI consumes a complete word in X/Y
  use the same pass. X receives the low byte and Y the high byte. The table-driven
  set is `SidCutoff`, `ScreenBase`, `BitmapBase`, `ScreenCopy`, `ColorCopy`,
  `BitmapCopy`, `DbfCreate`, and `DbfOpen`; wider and unknown ABIs still decline.
  A live `SidCutoff(I+300)` WHILE case proves exact X/Y setup, generic ALINK
  relocation, cutoff registers `$04/$25`, loop-variable value one, and pruning
  of unrelated SID objects.
- `ACTC_OVLH.BIN` composes ASMBLOCK insertion with byte-in-A or word-in-X/Y
  runtime calls without returning abstract operations to ALINK. Exact OBJ
  coverage checks parameter/local/global relocations and the helper import; a
  live linked PRG returns 42, stores trace value 41, and writes SID volume 8.
- Straight-line `REAL(integer)` assignment followed by `PrintR` or `PrintRE`
  now emits compiler-owned machine code, local data/pointer exports, helper
  relocations, and exact native line records from the dedicated native REAL
  emission overlay.
  ALINK no longer recognizes or compiles that abstract REAL body shape.
- Straight-line `REAL(integer)` assignment followed by `INT(real)` conversion
  now uses the same compiler-owned path. Its OBJ carries a six-byte data range,
  a relocatable REAL pointer, named low/high INT-result stores, both conversion
  helper imports, and exact native line/variable mappings; ALINK only resolves
  the resulting OBJ. Native REAL ownership is isolated in `ACTC_OVLA.BIN`, so
  these shapes no longer consume generic `ACTC_OVL5.BIN` capacity.
- Straight-line two-literal REAL `+`, `-`, `*`, and `/` assignments followed by
  `PrintR` or `PrintRE` now also use `ACTC_OVLA.BIN`. The compiler emits a
  relocatable 132-byte root with distinct A/B/X data exports, a pointer table,
  and ordinary relocations for conversion, arithmetic, and print helpers.
  ALINK's matching compact-body recognizer and fixed-address PRG builder are
  removed; only referenced helpers and their transitive dependencies are linked.
- Straight-line signed `FAbs(real)` and positive `FSqrt(real)` assignments
  followed by `PrintRE` use the same compiler-owned pass. Their relocatable
  93-byte root exports A/X storage and a four-byte pointer table, and imports
  conversion, unary, and print helpers only when referenced. ALINK no longer
  recognizes either compact unary body or supplies a fixed-address PRG layout.
- One-argument runtime helper calls followed by `REAL(integer)` and `PrintRE`,
  both as side effects and with a stored helper result, now use compiler-owned
  65-byte and 75-byte relocatable roots. Pass A selects byte-in-A or word-in-X/Y
  argument setup from the referenced helper ABI and emits ordinary helper,
  data, result, and pointer relocations. ALINK's two fixed-address input/REAL
  strategies and compact signatures are removed.
- Pass A's bounded two-REAL-parameter identity form now captures the return
  storage independently from its caller arguments and reverse-order parameter
  binds. It can return either named parameter while preserving the existing
  157-byte OBJ layout and generic A/X storage-pointer ABI. A reordered shared
  fixture returns its second parameter as binary32 2.0 and verifies all five
  REAL cells in VICE. Arbitrary return expressions remain outside this form.
- Plain, ELSE, and two-level nested REAL comparisons now use compiler-owned
  pass B. It emits 126-, 140-, and 160-byte relocatable roots with A/B/Y data,
  a pointer table, exact native line/variable records, and ordinary conversion
  and compare-helper imports. All 36 comparison variants link through generic
  OBJ closure; ALINK's fixed-address REAL IF strategy is removed. The compare
  helper's unordered result makes `<`, `<=`, `=`, `>=`, and `>` false and `<>`
  true for NaN, including the inclusive branch forms in IF and WHILE emitters.
- Pass K owns the first bounded REAL control-flow function body:
  `IF B<A THEN RETURN(B) FI RETURN(A)` for two REAL parameters. It emits a
  relocatable main/root, function export, five four-byte storage exports, and
  ordinary comparison/conversion imports. The root body records the reachable
  import union and the function body remains comparison-only, so ALINK's normal
  closure selects comparison, integer conversion, and transitive special-value
  support while pruning unrelated REAL helpers. Exact OBJ, deterministic link,
  and live VICE checks pass for finite inputs 2.0 and 1.0. Its matcher now
  captures the two initializer destinations, two call arguments, result
  destination, stack-bound parameter slots, comparison operands, and both
  return operands. Canonical and permuted declaration/parameter orders therefore
  emit the same bounded layout with role-correct named relocations. General
  function expression/control lowering and MATH1 remain outside this pass.
- Pass K also owns a bounded selected-binary REAL return. A two-REAL-parameter
  function may return one `+`, `-`, `*`, `/`, `FMin`, `FMax`, `FMod`, or
  `FHypot` expression over its parameters. The generated function writes a
  hidden four-byte result cell, invokes only the selected import, and returns
  that cell by A/X pointer. The shared FHypot fixture links its complete
  transitive closure, prunes staged sibling helpers, and writes binary32 5.0 in
  VICE. Arbitrary trees, nested calls, locals, and multiple statements remain
  outside this bounded emitter.
- The bounded REAL value parser also recognizes `FSign(A)`, `FTrunc(A)`, `FFloor(A)`, `FCeil(A)`, `FRound(A)`, `FFrac(A)`, `FMod(A,B)`, `FHypot(A,B)`,
  `FMin(A,B)`, and `FMax(A,B)` for named REAL operands in assignment, print, and condition
  positions. ACTC emits ordinary imports for the selected helper. The
  dependency-free 123-byte sign helper canonicalizes NaN, preserves signed
  zero, and returns signed one. The dependency-free 107-byte truncation helper
  preserves NaN payloads, infinities, signed zero, and integral values while
  clearing only finite fractional bits. The 135-byte floor helper imports
  truncation and rounds finite nonintegers toward negative infinity. The
  42-byte ceiling helper imports floor and transitively truncation, and rounds
  finite nonintegers toward positive infinity. The 152-byte round helper imports
  truncation and rounds nearest with halfway cases away from zero while preserving
  large integral values. The 93-byte fractional helper imports truncation and
  subtraction. The 245-byte remainder helper imports division, truncation,
  multiplication, and subtraction. The 503-byte scaled hypotenuse helper
  imports absolute value, minimum, maximum, division, multiplication, addition,
  and square root; the 77-byte selectors reach comparison and exceptional-value
  support transitively. Exact checks and focused live VICE launches prove that
  unrelated helpers are pruned. This completes ten
  utility routines, not general MATH1 source lowering. Pass K separately owns
  a bounded three-initializer `FClamp` assignment/print root. It captures all
  eight named-storage uses, so initializer order, clamp arguments, destination,
  and printed variable can differ from declaration order. Its 171-byte
  relocatable object imports only conversion, clamp, and print entry points;
  ALINK selects clamp's comparison/minimum/maximum closure and prunes unrelated
  REAL helpers. The fixed statement skeleton is not a general parser path.
- REAL `DO ... UNTIL` now uses the same compiler-owned pass for all six
  comparisons and for eight `A=A+C` / `A=A-C` ordered update loops. Simple
  loops emit a 146-byte relocatable root; binary-update loops emit a 194-byte
  root with A/B/C/Y storage and a six-byte pointer table. All 14 forms use
  ordinary conversion, arithmetic, compare, data, and backward-branch
  relocations. ALINK's matching recognizer, fixed-address builders, compact
  signatures, and strategy ID are removed, and the complete matrix executes
  successfully under VICE.
- `ACTC_OVLB.BIN` is now 5,220 bytes, leaving 2,972 bytes free in its 8 KiB
  execution window while remaining above the enforced 2 KiB headroom gate.
- REAL `WHILE` comparisons use compiler-owned pass C with named loop/exit
  targets and ordinary conversion, compare, and branch relocations. Runtime
  equality/inequality conditions use pass D. ALINK does not recognize either
  source shape.
- Pass E owns 194 native runtime-call sequences, including 106 stateful and 77
  readback cases. Pass F owns nine nested-readback cases and can spill two
  pending results into compiler-owned relocatable storage, including
  `SpritePos(1,MouseX(),MouseY())`. Both passes emit only machine records,
  imports, and relocations for generic ALINK processing.
- Compile-only `ACTC <MODULE>;` returns source diagnostics to
  `ACTEDIT <MODULE>:<LINE>`. Build `,` and debug `:` modes use the same failure
  return while preserving their existing successful ALINK/ACTDBG chains;
  unmarked compiler invocations still return failure directly to UDOS. Strict
  successor-command construction lives in `ACTC_OVL0.BIN`, retaining pass 0's
  compatibility no-op mode and resident compiler headroom.
- Legacy runner-oriented compiler paths have been removed from the maintained
  source tree.
- All maintained ALINK input is now compiler-owned machine OBJ. The 102 seeded
  runtime fixtures are machine objects as well; unsupported historical compact
  bodies remain only as linker rejection tests.
- Production ACTC no longer reserves scratch bytes used only by disabled
  resident fallback paths. Overlay ABI v5 exposes a contiguous 231-byte context,
  including resident decimal/hexadecimal formatter callbacks and the binary32
  constant evaluator shared by pass I. CODE ends at `$674E` and BSS ends at
  `$6BC1`. Current UDOS swaps the overwritten low resident and preserves the
  callable Tool ABI from `$9800`, leaving 11,327 bytes below that enforced
  floor. Body, layout, and emitter fallback configurations are separately
  build-tested and retain the scratch state and symbol tables they require.
  Those capacity-only configurations explicitly build with
  `ACTC_ENABLE_REAL_CONST_EVALUATOR=0`; their ABI-compatible callback rejects
  `REAL CONST`. Production and ordinary harness builds default to the complete
  evaluator.
- Pass L consumes the bounded child-first REAL stream from passes 6 and 7 for
  straight-line module-REAL programs. It emits machine
  bytes, 16-bit named/import relocations, `__idata`, source-variable records,
  native line records, and compiler-private four-byte temporaries. The supported
  calls are integer-to-REAL conversion, `PrintR`/`PrintRE`, the maintained
  unary and binary REAL helpers, and `FClamp`; stack depth is eight, temporary
  count is 16, and debug-operation count is 64 per procedure. In addition to
  one `MAIN`, pass L accepts up to two nonrecursive two-REAL-parameter functions
  with bounded all-REAL locals and nested REAL return trees.
  `MAIN` may call either function, and either declaration direction may assign
  the other function's result to a local, feed it directly to a supported
  intrinsic return tree, or pass bounded calls as arguments to another call
  while the graph remains acyclic. The caller pushes
  argument pointers, each callee reverse-binds them to disjoint static parameter
  cells, and A/X returns a result pointer. A function-to-function edge also
  stack-saves the caller's parameter, local, and live-temporary cells, stages
  the result, and restores those cells in reverse. Direct PRGs prove nested
  expression trees, both root-to-function selectors, function-local storage,
  backward and forward acyclic function edges, a nested local-call operand,
  nested user-call arguments with independent result spills, and reachable-only
  runtime objects. Pass L is 6,124 bytes with 2,068 bytes free.
  Pass M extends the same ABI with one nonnested `IF`/`ELSE` per REAL function,
  six REAL relations through `rt_f_cmp`, relocatable internal false/end labels,
  supported expressions in both arms, and one terminal return. Its direct PRG
  executes both paths and prints `34`. Self and mutual cycles are rejected.
  Pass N separately claims a second conditional and supports at most two per
  function, either sequentially or nested to depth two. Its direct PRGs print
  `43` and `143`, proving both sequential decisions and inner true/false plus
  outer-false paths. Pass O claims a third conditional and supports up to four
  controls per function or nesting depth four. Its direct PRGs print `43` and
  `154`, proving all four sequential slots plus deep true, deep false, and outer
  false paths. Pass P adds immediate pointer returns inside one-control and
  depth-four `IF`/`ELSE` bodies while retaining a terminal fallback; its direct
  PRGs print `33` and `154`. Recursive/reentrant frames, loops, controls beyond
  four, deeper nesting, unrestricted user-call argument trees and nested call
  expressions, mixed declarations, arbitrary signatures, and recursive frames
  remain unsupported.

Current focus:

- widen source coverage
- keep object metadata stable for ALINK
- move large compiler working sets toward REU-backed streaming
- keep `ACTC.PRG -> ALINK.PRG -> BIN/MAIN.PRG` green under UDOS/VICE
