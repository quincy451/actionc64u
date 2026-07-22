# Idun And UDOS Feature Parity

This document compares user-visible capabilities, not executable
implementations. The Idun fork runs development tools as Alpine Linux
processes. The native product runs its tools as 6502 programs under UDOS.
Generated applications in both products remain self-contained C64 PRGs built
from OBJ1 modules. ALINK selects only reachable OBJ1 modules. Idun ACTC also
prunes unreachable source-defined library routines from an application OBJ
before linking while retaining every project routine; native ACTC retains only
the bounded routines it can currently lower.

Status date: 2026-07-21. Full cross-product parity is not yet complete; the
matrix and ordered implementation plan below are the authoritative gap list.

## Executive Status

The native C64U/UDOS product already has the direct-PRG/OBJ1 foundation,
link-selected common 6502 runtime, scalar compiler core, ASMBLOCK and fixed
machine-call ABI, IEEE-754 binary32 runtime, INPUT1, DBF1, SIDSPR1, and native
ACTDBG. It does not yet accept the full portable source surface that the Idun
compiler accepts.

What is still missing on native UDOS falls into five portable groups:

1. General expression and ABI lowering: arbitrary REAL trees, typed nested
   calls and returns, reentrant/frame-backed locals, arrays, pointers, records,
   strings, indirect parameters, bounded recursive frames, and complete
   structured-expression control including `ELSEIF`.
2. Libraries: 28 MATH1 routines and 45 high-level GFX1 routines, each packaged
   so ALINK includes only reachable OBJ1 dependencies.
3. Application facilities: command-tail-backed program arguments, application
   REU arrays, program-owned overlays, and ASP1/ABM1 resource declarations and
   embedding.
4. Native workflows: sprite/bitmap editors plus ACTEDIT F8, source formatting,
   fuller help/navigation, and an explicit decision on a separate profiler.
5. Acceptance: physical C64U input, display, SID, REU, filesystem, debugger,
   and release checks after the implementation work passes VICE.

The Idun fork's hardware-free feature set is otherwise ahead of native. Its
compiler treats every project routine and module-level routine reference as a
root, then emits only the transitive included-library call graph. This closes
the previously tracked full-source MATH1/GFX1 packaging gap without suppressing
project diagnostics. Attached Idun/cartridge validation remains a release gate.
Linux processes, POSIX paths, SQLite, sockets, AArch64/APK packaging, and
the Idun target protocol are intentional Idun mechanisms, not code to port into
UDOS. Native PRGs, overlays, REU compiler workspace, UDOS services, and DNP/D64
media are the corresponding intentional native mechanisms.

The active native dependency is general REAL lowering. Passes 6 and 7 collect
and preallocate bounded REAL operands in child-first postfix order. Pass L now
consumes that stream for a straight-line module-REAL subset and emits ordinary
machine, relocation, data, line, and variable OBJ1 records. Besides one
`MAIN`, it now supports up to two nonrecursive two-REAL-parameter functions
whose nested REAL return trees are called directly by `MAIN`. Each function may
use bounded all-REAL static locals with DBG1 local records. Either function may
call the other while the graph remains acyclic, including calls used directly
in a supported intrinsic return tree or as arguments to another call. Pass L
stack-preserves caller parameters, locals, and live temporaries around every
such edge. Pass M adds one nonnested `IF`/`ELSE` per supported REAL function,
all six REAL relations, and relocatable internal branch labels while preserving
the same terminal-return ABI. Pass N permits at most two controls per function,
either sequentially or nested to depth two, and preserves independent
relocatable false/end labels. Self and mutual cycles are rejected. Loops, early
returns, more than two controls, deeper nesting, unrestricted user-call
argument trees and nested call expressions, recursive/reentrant local
frames, mixed types, arrays, pointers,
strings, arbitrary signatures, and recursive frames remain tracked native gaps.

## Parity Rules

- Shared Action syntax, library APIs, OBJ1 records, runtime results, PRG layout
  rules, and debug-sidecar meaning should match.
- Linux filesystems, SQLite, sockets, APK packaging, and terminal UI code are
  not copied into UDOS. UDOS receives an equivalent workflow only where the
  capability is useful on the C64.
- `actsvc`, the fake socket target, Linux ACTDBG/ACTPROF transport, AArch64
  builds, and APK publication are Idun-specific.
- UDOS resident file/project services, native tool overlays, REU workspace, and
  disk-image packaging are UDOS-specific.

Parity is measured at the portable boundary: the same supported Action source
must produce compatible OBJ1 semantics and the same observable result in the
linked C64 PRG. Every selected 6502 helper must be reachable, but helper
closure and instruction layout may differ when one compiler folds an operation
that the other executes at runtime. Host compiler data structures, tool
executable formats, filesystems, user interfaces, and deployment packages are
not parity artifacts.

## Current Matrix

| Capability | Idun/Alpine | Native UDOS | Status |
| --- | --- | --- | --- |
| Direct C64 PRG and link-selected OBJ1 closure | Linux ACTC/ALINK | `ACTC.PRG`/`ALINK.PRG` | Parity |
| No VM runner or private instruction set | Yes | Yes | Parity |
| Shared link-selected 6502 runtime modules | Native manifest snapshot | Authoritative module set | Parity with two OS adapters excluded |
| BYTE/CARD/INT scalar control and calls | Dynamic host compiler | Bounded overlay compiler | Parity for the maintained native scalar matrix; Idun accepts additional expression and type shapes |
| Structured control | `IF`/`ELSEIF`/`ELSE`, loops, `FOR`, and `EXIT` | Bounded `IF`/`ELSE`, loops, `FOR`, and `EXIT` subsets | Native `ELSEIF` and general-expression gap |
| Source constants and inclusion | Dynamic `DEFINE`, compatibility `SET`, full typed `CONST` expressions, and recursive host-path `INCLUDE` | Bounded `DEFINE`, compatibility `SET`, recursive project `SRC`/`LIB` `INCLUDE`, checked signed 64-bit integer expressions, and binary32 `REAL CONST` expressions before or after `MODULE` | Expression parity for the supported constant grammar, with explicit native table, path, 64-byte expression, and 16-value-stack bounds |
| Leading comments before MODULE | Accepted | Accepted across streamed REU windows | Parity |
| General ASMBLOCK composition | Mixes with ordinary supported statements | Mixes with ordinary supported statements | Parity for maintained statement set |
| `ASMBLOCK` with labels and Action symbols | Unbounded host tables | REU-backed bounded tables | Parity with documented native limits |
| ASMBLOCK symbol byte offsets | Signed relocation addends | Signed `-128..127` source addends; wider OBJ1 addends link | Parity with documented native source bound |
| Fixed register-entry ABI | `=*(...)`, up to 16 flattened bytes in `A`, `X`, `Y`, then `$A3+` | Same ABI in pass J for ASMBLOCK and raw bodies; pass H owns runtime compositions | Parity; emitter selection, rejection, object/link, and VICE proofs pass |
| Absolute-address routine declarations | Numeric expressions and linked local-symbol/addend expressions | Numeric expressions plus forward/backward local aliases with a signed 16-bit checked expression on either side of the symbol, canonicalized by pass I and lowered by passes J/H | Parity for the shared signed-16-bit contract; Idun host tables permit wider addends, while final C64 addresses remain 16-bit |
| Raw bracketed machine-code bodies | Constants, symbols, current address, routine addresses | Byte/word/character/sum constants plus preprocessed `DEFINE`, storage, local-routine, and current-address relocations | Core parity; linked external routine-symbol expressions remain a native compiler/address gap |
| Numeric literals in call arguments | Decimal, hexadecimal, and binary forms | Same three 16-bit forms through streamed SourceReader tokens | Parity; object, REU-window, and live VICE proofs pass |
| Arrays, pointers, records, and indirect parameters | Dynamically sized compiler metadata and typed target operations | Not part of the maintained native direct-machine core | Native compiler gap |
| Typed functions and recursive frames | BYTE/CARD/INT/REAL, nested calls, direct/mutual recursion | Scalar nonrecursive word functions plus constrained REAL forms, including up to two nested two-REAL-parameter callees with bounded static REAL locals, acyclic calls in either declaration direction with caller-cell stack preservation, bounded calls as intrinsic or local-call operands, and up to two sequential or depth-two nested conditionals per function | Native compiler/ABI gap beyond the bounded pass-L/M/N call ABI |
| Application REU arrays | `REU BYTE ARRAY` plus 8/16-bit accessors | Runtime helpers exist, but native ACTC has no declaration/access lowering | Native compiler gap; compiler REU workspace is not equivalent |
| Program-owned overlay sections | `OVERLAY`/`ENDOVERLAY` and relocated `OverlayCall` | No native source lowering | Native compiler gap; ACTC tool overlays are not equivalent |
| Program argument entry | `MAIN(argc,argv)` through the Idun target service | `MAIN()` and UDOS command-tail workflow | OS-specific contracts; expose equivalent user arguments without copying the Idun upload ABI |
| IEEE-754 binary32 arithmetic and exceptional values | Standalone modules | Standalone modules plus native support modules | Parity at runtime |
| General REAL source expressions, calls, and returns | Full binary32 compiler path with intrinsic `FTrunc`, `FFloor`, `FCeil`, `FRound`, `FFrac`, `FMod`, `FHypot`, `FMin`, and `FMax` | Core operations, bounded nested straight-line trees over module REAL values, and up to two nested two-REAL-parameter functions with bounded static REAL locals, frame-preserved acyclic calls, and at most two sequential or depth-two nested conditionals per function | Partial parity; recursive/reentrant locals, loops, early returns, more/deeper controls, unrestricted user-call argument trees and nested calls, mixed types, arbitrary signatures/calls, and recursive frames remain gaps |
| INPUT1 joystick/two-button mouse API | 19 declarations | 19 declarations | Parity; physical checks remain |
| DBF1 API | 20 declarations | 20 declarations | Parity; physical REU/disk checks remain |
| SIDSPR1 API | 37 declarations | 37 declarations | Parity; physical SID/display checks remain |
| Full MATH1 source library | 43 public routines plus 8 constants, 51 catalog features; `FTrunc`, `FFloor`, `FCeil`, `FRound`, `FFrac`, `FMod`, `FHypot`, `FMin`, and `FMax` are intrinsic and the remaining implementations are portable source | Eight compile-time constants plus fifteen link-selected callable builtins: `PrintR`, `PrintRE`, `FAbs`, `FSqrt`, `FSign`, `FTrunc`, `FFloor`, `FCeil`, `FRound`, `FFrac`, `FMod`, `FHypot`, `FMin`, `FMax`, and `FClamp` | Constants plus nine shared intrinsic semantics are at parity; native implementation gap remains for 28 public routines |
| MATH1 reachable-only packaging | Included library routines are pruned to the transitive graph referenced by project routines and module-level routine addresses; `FTrunc`, `FFloor`, `FCeil`, `FRound`, `FFrac`, `FMod`, `FHypot`, `FMin`, and `FMax` remain independent OBJs | Constants emit no code; fifteen callable builtins import independent OBJ modules | Packaging behavior is at parity for implemented routines; native still lacks 28 public routines |
| Full GFX1 source library | 67 public source routines plus 16 constants; 60 routines plus the constants form the 76-feature GFX1 catalog, while seven low-level sprite aliases are cataloged under SIDSPR1 | Fifteen low-level callable declarations | Native implementation gap |
| ASP1/ABM1 resources and compiler embedding | Linux editors and ACTC loader | Contract documented only | Native implementation gap |
| Source formatting | `actspc` and ACTEDIT F6 | No complete UDOS formatter | Native workflow gap |
| Language/library help | SQLite `acthelp`, ACTEDIT F1-F4 | Exported text guides and editor help | Partial workflow parity |
| Source debugger | Linux ACTDBG plus `actsvc` | Native ACTDBG with REU snapshots | OS-appropriate parity; hardware checks remain |
| Sampling profiler | Linux ACTPROF | No separate native profiler | Optional native workflow decision |
| Semantic navigation | SQLite code map | DBG1 sidecar and native editor/debugger | OS-appropriate partial parity |
| Graphics resource editors and ACTEDIT F8 | `actsprite`, `actbitmap`, F8 | Not implemented | Native implementation gap |
| Linux/APK deployment | Static AArch64 and signed APKs | Not applicable | Idun-specific |
| UDOS disk/DNP release | Not applicable | Native release image | UDOS-specific |

## Concrete Native Gaps

The 28 missing MATH1 routines are `FExp`, `FLn`, `FLog2`, `FLog10`,
`FPow`, `FSin`, `FCos`, `FTan`, `FATan`, `FATan2`, `FASin`,
`FACos`, `FSec`, `FCsc`, `FCot`, `FASec`, `FACsc`, `FACot`,
`FVersin`, `FHaversin`, `FSinh`, `FCosh`, `FTanh`, `FASinh`,
`FACosh`, `FATanh`, `DegToRad`, and `RadToDeg`. They require general
REAL function lowering first, then dependency-sized OBJ modules so unused
routines remain absent from the linked PRG.

Native GFX1 is missing 45 high-level routines: `GfxUseBank`,
`GfxUseScreen`, `GfxUseBitmap`, `GfxUseSprites`, `GfxHires`,
`GfxMulticolor`, `GfxBitmapClear`, `GfxScreenClear`, `ClipSet`,
`ClipReset`, `Plot`, `Unplot`, `PlotXor`, `Point`, `MPlot`,
`MPoint`, `GfxCellColors`, `GfxMCellColors`, `HLineDraw`,
`HLineUnplot`, `VLineDraw`, `LineDraw`, `RectangleDraw`,
`RectangleFill`, `RectangleClear`, `SquareDraw`, `SquareFill`,
`CircleDraw`, `CircleFill`, `TriangleDraw`, `BitmapStamp`,
`BitmapDrawResource`, `BitmapErase`, `BitmapMove`, `MBitmapStamp`,
`MBitmapDrawResource`, `MBitmapErase`, `MBitmapMove`,
`SpriteDefaultColor`, `SpriteIsMulticolor`, `SpritePlace`, `SpriteMove`,
`SpriteShow`, `SpriteHide`, and `SpriteSharedColors`. The seven low-level
sprite aliases exposed by Idun GFX1 already exist in the native
SIDSPR1/compiler surface and are not separate 6502 implementation gaps.

The remaining language/runtime gaps are general arrays, pointers, records,
length-prefixed strings, indirect parameters, typed nested calls and returns,
bounded recursive frames, application REU arrays, program-owned overlays,
resource declarations/embedding, and a UDOS command-tail implementation of the
portable argument-entry contract. The remaining workflow gaps are native
sprite/bitmap editors with ACTEDIT F8, a UDOS formatter/help path, and the
optional profiler decision. Physical C64U input, display, SID, REU, and disk
acceptance remains required after implementation.

Linux processes, POSIX paths, SQLite, sockets, AArch64/APK packaging, and the
Idun target protocol are deliberately not native gaps. Conversely, UDOS
resident services, compiler overlays, REU compiler workspace, and D64/DNP
release media are deliberately not Idun gaps.

## Parity Delivery Ledger

This ledger is the implementation boundary for the remaining work. A row is
complete only when the portable result passes the acceptance gates below; using
the same host-side implementation is neither required nor desirable.

| Work package | Portable result | Native C64U/UDOS work | Idun/Alpine work | State |
| --- | --- | --- | --- | --- |
| Compiler expression and call core | The same supported typed source produces equivalent OBJ1 calls, storage, returns, and direct-PRG results | Extend passes L/M/N beyond two nonrecursive two-REAL-parameter callees, bounded static REAL locals, frame-preserved acyclic calls, and two bounded controls to general functions, parameters, recursive/reentrant locals, structured control, and nested calls; then add arrays, pointers, records, strings, indirect parameters, and bounded frames | Keep Linux ACTC as the behavioral oracle and add every shared fixture to its regression suite | In progress; passes L/M/N prove both `MAIN` selectors, backward and forward acyclic edges, and sequential/depth-two function conditionals, but not a general or recursive call graph |
| MATH1 | All 43 routines and 8 constants have the same binary32/domain behavior and unused routines are absent from the PRG | Lower the 28 missing source routines after general REAL calls work; package each routine or dependency group as OBJ1 | Complete: ACTC emits only source routines reachable from `MAIN`, while intrinsic helpers remain independent OBJ1 modules | Blocked on the native compiler core; Idun packaging is complete |
| GFX1 | The common 60-routine/16-constant catalog behaves the same on the C64 target | Implement the 45 missing high-level routines in reachable OBJ1 groups and retain the existing 15 low-level calls | Keep the implemented source library and generated-program tests as the reference | Native implementation pending |
| Resources | `SPRITE`, `MSPRITE`, `BITMAP`, and `MBITMAP` validate ASP1/ABM1 and expose equivalent linked asset addresses | Load through UDOS/REU services, emit aligned relocatable data, and add native ACTSPRITE/ACTBITMAP plus ACTEDIT F8 | Keep POSIX loading and Linux editors; add shared malformed-resource and emitted-layout fixtures | Native implementation pending |
| Program entry and application storage | Portable argument values, application REU arrays, and program-owned overlays have matching target semantics | Decode the UDOS command tail into target-owned `argc`/`argv`; add source lowering for REU arrays and application overlays | Retain Idun upload arguments and Linux-side placement; do not export that transport as a language contract | Native implementation pending |
| Development workflow | Users can edit, format, inspect help, debug source, and manage graphics resources on either product | Extend ACTEDIT/help and native resource tools; use DBG1/ACTDBG and decide separately whether a profiler is useful | Retain Linux terminal tools, SQLite index/help, `actsvc`, ACTDBG, and ACTPROF | Partial OS-appropriate parity |
| Product acceptance | Shared fixtures agree in both toolchains and generated PRGs; hardware-dependent behavior is recorded | Run native unit, UDOS release, VICE, ACTDBG, then physical C64U input/display/SID/REU/disk gates | Run Linux, sanitizer, export/APK, VICE, then attached Idun/cartridge gates | Emulated baseline passes; physical gates pending |

The critical path is the table order: general native typed lowering, MATH1,
general aggregate/frame support, program entry/storage, resources and GFX1,
native workflows, then physical acceptance. Independent shared-runtime fixes and
Idun library call-graph pruning are complete. No work package may add
a runtime launcher; ALINK remains solely responsible for selecting and laying
out the code present in the final PRG.


## Native Work Order

The constant foundation is complete. Native pass I folds `REAL CONST` decimal
and exponent literals, dependent constants, unary and grouped expressions,
`+`, `-`, `*`, `/`, `REAL`, `FABS`, `FSQRT`, `INF`/`INFINITY`, and `NAN` at
binary32 precision. Decimal conversion and every operation use
round-to-nearest, ties-to-even. The result is emitted as four literal bytes, so
constant-only arithmetic does not select target conversion or arithmetic
helpers. The evaluator is resident, while pass I retains its full 512-byte code
reserve.

The shipped native `LIB/MATH1.ACT` is now an actual include header rather than
a second application module. `INCLUDE "MATH1"` exposes all eight portable
constants before or after the caller's `MODULE` declaration. The constants
fold to literal binary32 words, allocate no target storage, and select no
runtime object. The fifteen currently supported calls remain compiler-recognized
builtins documented in the header; each helper is still an independent OBJ1
module selected only when reachable. Idun lowers `FTrunc`, `FFloor`, `FCeil`, `FRound`, `FFrac`, `FMod`, and `FHypot` to the
same shared helpers and keeps portable source implementations for the other
MATH1 routines because its host compiler can lower those bodies directly.

The first item now has thirteen tested checkpoints. Native pass A accepts two named
REAL arguments after their immediate `REAL(integer)` initializers, copies both
values into distinct parameter storage, and returns either named parameter by
pointer. Dedicated pass K then lowers the exact finite comparison/select form
`IF B<A THEN RETURN(B) FI RETURN(A)`. Its focused OBJ/ALINK/VICE proof selects
`RT_I_TO_F.OBJ`, `RT_F_CMP.OBJ`, and transitive `RT_F_SPECIAL.OBJ`, while
unrelated REAL helpers remain absent. The bounded matcher captures all caller
and callee storage roles, including either parameter-name ordering, while still
requiring the exact finite select skeleton. Native ACTC now also lowers `FMin(A,B)`
and `FMax(A,B)` for named REAL operands in assignment, print, and REAL-condition
positions. Their 77-byte modules implement the complete MATH1 NaN and signed-
zero selection policy through ordinary `RT_F_CMP.OBJ` closure. Native ACTC also
lowers `FSign(A)` in those positions through a dependency-free 123-byte helper
that canonicalizes NaN, preserves signed zero, and returns signed one for every
other input. `FTrunc(A)` uses a dependency-free 107-byte helper in assignment,
print, and condition positions. It preserves NaN payloads, infinities, signed
zero, and integral values while clearing only fractional significand bits for
finite nonintegers. `FFloor(A)` uses a 135-byte helper in the same positions;
ALINK selects its truncation dependency transitively, and finite nonintegers
round toward negative infinity while exceptional and integral values are
preserved. `FCeil(A)` uses a 42-byte helper in those same positions and imports
floor, which in turn imports truncation. It implements `-FFloor(-A)`, preserving
NaN payloads, infinities, signed zero, and integral values while rounding finite
nonintegers toward positive infinity. `FRound(A)` uses a 152-byte bit-level
helper, imports only truncation, and
rounds nearest with halfway cases away from zero without perturbing large
integral binary32 values. `FFrac(A)` uses a 93-byte alias-safe helper that
imports truncation and subtraction and computes `A-FTrunc(A)`. `FMod(A,B)`
uses a 245-byte alias-safe helper and computes
`A-FTrunc(A/B)*B` through independently linked division, truncation,
multiplication, and subtraction helpers. A zero divisor, NaN operand, or
infinite dividend returns canonical quiet NaN; a finite dividend with an
infinite divisor is returned bit-for-bit. `FHypot(A,B)` uses a 503-byte
alias-safe helper that imports absolute value, minimum, maximum, division,
multiplication, addition, and square root. Its scaled calculation avoids
avoidable intermediate overflow and underflow, returns positive zero for two
zero inputs, and gives infinity precedence when paired with NaN. Pass K also owns a bounded four-REAL root that initializes three
values, assigns a named destination from `FClamp(value,lower,upper)`, prints a
named value, and returns. It captures initializer, argument, destination, and
print storage independently, so those roles need not follow declaration order.
Its 199-byte selected helper validates all three inputs and bound order, then
uses the ordinary comparison/minimum/maximum closure. This establishes the
ternary ABI and complete portable clamp semantics without claiming arbitrary
three-argument expression lowering. Pass K now also lowers a bounded
two-REAL-parameter function whose single return expression selects `+`, `-`,
`*`, `/`, `FMin`, `FMax`, `FMod`, or `FHypot`. It uses a hidden four-byte
result cell so helper output never aliases either parameter. The shared
`RETURN(FHypot(A,B))` fixture compiles in both products; native ALINK selects
only the twelve-module conversion/hypotenuse closure, and its direct PRG writes
binary32 5.0 in VICE. This closes that exact function-return shape. Pass L
handles bounded nested straight-line trees and now extends them across up to two
`MAIN`-to-function calls. Each function has exactly two REAL
parameters, bounded all-REAL static locals, and returns a
nested helper result through A/X after reverse-binding caller-pushed pointers.
The shared `real_function_nested_postfix.act` fixture compiles and links in both
products;
the native direct PRG evaluates `FHypot(FAbs(A),FAbs(B))` and prints `5` in
VICE. The shared `real_function_local_nested_postfix.act` fixture stores
`FAbs(A)` in a DBG1-scoped local before the same nested return; its native PRG
prints `5` and verifies binary32 3.0 in that local. The shared
`real_two_function_nested_postfix.act` fixture verifies both direct callee
selectors, disjoint static storage, and separate DBG1 banks. The shared
`real_function_call_chain_postfix.act` fixture adds ordinary `MAIN -> CHAIN` and
`CHAIN -> LENGTH` relocations and produces binary32 5.0 in both products.
The shared `real_function_nested_local_call_postfix.act` fixture uses the same
declaration-order edge directly inside `FMax` and also produces binary32 5.0 in
both products. The shared `real_function_user_call_arguments_postfix.act`
fixture returns `LOWER(LOWER(A,A),LOWER(B,B))`; distinct native temporary spills
preserve binary32 3.0 and 4.0 inner results before the outer call, and both
products produce 3.0. The shared `real_function_if_else_postfix.act` fixture
then executes both arms of one REAL-function conditional: `(3,4)` selects the
left value and `(4,3)` selects `FMax`, so both products print `34`. Native pass
M imports `rt_f_cmp` and relocates long branches to internal `__rf0`/`__re0`
code exports. Pass N adds byte-identical
`real_function_sequential_if_else_postfix.act` and
`real_function_nested_if_else_postfix.act` fixtures. They print `43` and `143`,
respectively, proving two sequential controls and depth-two inner true/false
plus outer-false paths through ordinary OBJ1 closure. Reentrant local frames,
loops, early returns, more than two controls, deeper nesting, unrestricted
user-call argument trees and nested call expressions, mixed types, arbitrary
signatures, recursive frames, and the rest of MATH1 remain incomplete.

Remaining work is dependency ordered:

1. Generalize native REAL declarations, parameters, frame-backed locals,
   expressions, calls, and returns enough to compile portable multi-function
   MATH1 modules.
2. Port the remaining 28 MATH1 routines in dependency-sized OBJ modules and
   prove representative values in direct linked PRGs without making unused
   functions reachable. Keep Idun's project-rooted library call-graph pruning
   and independent intrinsic modules covered as the packaging reference.
3. Widen native arrays, pointers, length-prefixed strings, records, typed
   function calls, and stack-bounded recursive frames where shared libraries or
   portable programs require them. Keep fixed C64/REU limits explicit rather
   than imitating the Linux compiler's unbounded host metadata.
4. Populate portable `MAIN(CARD argc,CARD ARRAY argv)` from the UDOS command
   tail using linked target-owned storage, without copying Idun's Linux upload
   transport.
5. Add application `REU BYTE ARRAY` declaration/access lowering and program-
   owned `OVERLAY`/`ENDOVERLAY` plus `OverlayCall`. Keep both independent of
   ACTC's internal REU workspace and compiler-pass overlays.
6. Add global `SPRITE`, `MSPRITE`, `BITMAP`, and `MBITMAP` resource declarations,
   ASP1/ABM1 validation, REU/UDOS file loading, 64-byte sprite alignment, and
   relocatable embedded-data exports.
7. Port the expanded GFX1 library in link-selected groups, then add target tests
   for clipping, VIC banking, `$01` restoration, hires/multicolor pixels,
   shapes, bitmap resources, and sprite resources.
8. Implement native ACTSPRITE and ACTBITMAP tools, then bind ACTEDIT F8 to the
   resource declaration under the cursor.
9. Add a UDOS-appropriate formatter/help workflow and decide whether native
   sampling profiling adds value beyond ACTDBG.
10. Port or adapt the three Idun-only examples and two graphics assets as each
   prerequisite lands. Preserve UDOS command-tail semantics rather than the
   Idun `argc`/`argv` upload ABI.
11. Run the complete UDOS ACTC/ALINK/ACTDBG/release VICE gates, then perform the
   remaining physical C64U display, input, SID, REU, and disk checks.

The portable products are therefore not yet at full feature parity. The
direct-PRG/OBJ1 foundation, link-selected common 6502 runtime, scalar core,
ASMBLOCK, fixed/absolute routine calls, INPUT1/DBF1/SIDSPR1 APIs, and
OS-appropriate debugger paths are present. Work items 1 through 11 are the
remaining parity and acceptance work. Items 1 through 10 are implementation
work; item 11 is the final emulated and physical acceptance phase.

The native D64 is intentionally a valid UDOS boot plus standalone ALINK disk.
The complete ACTC compiler, passes 0 through N, development tools, libraries,
examples, and assets live in `ACTION.DNP`, the primary C64 Ultimate workspace.
New native parity work targets the DNP and must not produce a partial compiler
on the capacity-constrained D64.
Feature parity must not reintroduce a runtime runner or cause helper-free
programs to absorb unused library code.

## Acceptance Gates

Each native parity slice is complete only when all applicable gates pass:

1. Compile the same portable source with Linux ACTC and native ACTC and compare
   public exports, type/call behavior, valid relocations, and runtime results.
   Optimizer-specific temporaries, instructions, and folded-helper imports need
   not be byte-identical.
2. Link both OBJ1 graphs with only reachable project and library modules; an
   unused library declaration must not change either PRG or dependency closure.
3. Run the resulting direct PRG in VICE and compare console output, selected
   memory results, and failure diagnostics. No runtime launcher is permitted.
4. Keep every common module byte-identical through the shared manifest check,
   except the two documented DBF filesystem adapters.
5. Run native unit, ALINK matrix, UDOS integration, release-image, and focused
   ACTDBG gates. Run Idun Linux, sanitizer, export, and direct-PRG gates when a
   shared contract changes.
6. Record physical C64U evidence for behavior that emulation cannot establish,
   including real input devices, SID/display timing, REU hardware, and disk
   handling.

The library declaration and help-catalog counts are verified from the Idun
`lib/*.act` and `resources/action_help.json`; they are not manually maintained
API definitions.

## Completion Definition

Parity is complete when shared Action sources that avoid documented OS-only
entry points compile to interchangeable OBJ1 semantics and direct C64 PRGs;
all common 6502 modules remain manifest-identical; each native replacement for
an Idun workflow is documented and tested; and the remaining C64U input,
display, SID, REU, and filesystem checks have recorded physical results.
Linux process transport, SQLite, sockets, APK/AArch64 packaging, and UDOS
resident/REU/DNP implementation details are deliberate differences, not work
items to copy across products.

## OS Adaptation Map

| Idun/Alpine mechanism | Native C64U/UDOS equivalent | Parity rule |
| --- | --- | --- |
| Linux tool processes and host memory | Native PRGs plus bounded 6502 overlays and REU tables | Match source/OBJ/PRG semantics, not process layout |
| POSIX project paths | UDOS `SRC`/`OBJ`/`BIN`/`LIB` directories in `ACTION.DNP` | Match project behavior within UDOS path limits |
| SQLite help and semantic map | Exported guides/editor help plus DBG1 sidecars | Match useful lookup/debug meaning without embedding SQLite |
| `actsvc`, sockets, and Linux ACTDBG/ACTPROF transport | Native ACTDBG snapshots and UDOS/C64U services | Do not copy the Idun upload protocol; profiling remains optional |
| `MAIN(argc,argv)` upload storage | UDOS command-tail-backed target storage | Match portable argument values after array lowering exists |
| APK/AArch64 package | Boot D64 plus complete `ACTION.DNP` release | Product-specific packaging, not a language feature |

## Shared 6502 Ownership

The native ActionC64U tree is authoritative for common files under
`src/runtime/modules/`. `resources/shared_6502_manifest.json` records every
shared module and its SHA-256 digest. `tools/shared_6502_sync.py` verifies that
manifest and can compare a native checkout with an Idun checkout.

Only `rt_dbf_create.obj` and `rt_dbf_file_open_write.obj` are excluded. Those
modules implement OS-specific DBF creation and replacement policy: UDOS uses
its native filesystem contract, while Idun uses direct KERNAL file handling.
All arithmetic, graphics, SID/sprite, input, REU, common DBF, and other target
modules must remain byte-identical across products.

After changing common 6502 code in this repository:

```sh
python3 tools/shared_6502_sync.py --write-manifest
python3 tools/shared_6502_sync.py --check-peer /path/to/idun_action
```

The Idun checkout applies the corresponding snapshot with:

```sh
make sync-native NATIVE_ACTION_ROOT=/path/to/actionc64u
make sync-native-check NATIVE_ACTION_ROOT=/path/to/actionc64u
```

## Validation Snapshot

The 2026-07-22 current cross-product baseline passed:

- 830 native ActionC64U unittests, including compiler-overlay capacity, OBJ1,
  ALINK closure, IEEE-754, ACTEDIT, ACTDBG, Linux compatibility, export, and
  release-image checks;
- 133 UDOS integration tests, with one intentional embedded-AUTOEXEC capacity
  skip, plus rebuilt release artifacts and direct VICE launches for both
  side-effect and stored-result runtime calls through the native REAL bridge;
- 153 Idun/Alpine unittests covering the Linux compiler/linker, libraries,
  resource editors, help, semantic map, debugger/profiler transport, export,
  and packaging contracts;
- 138 Idun ASan/UBSan tests covering the Linux tools under instrumented builds;
  and
- 21 Idun direct-PRG tests on VICE, with the known VICE 3.7 long-DBF case
  version-skipped on the local host.

Focused native regressions additionally prove comment-prefixed modules through
both the resident and overlay source readers, including comments spanning more
than two REU windows. Native ACTC `symbol+constant` output and ALINK's compact
and long byte-selector aliases are covered by host-oracle checks and direct VICE
launch; the complete ALINK matrix also passes. These gates are
included in the current native count above.

The subsequent fixed-register slice compiles through native pass J, links
directly with ALINK, and executes in VICE with exact checks for BYTE and CARD
returns plus `A`/`X`/`Y`/`$A3` mixed-width argument placement. It raises the
prior broad matrix inventory to 1,321 cases and the source-backed launch
inventory to 165; both complete matrices passed. Minimal machine-only units are
forced through the capable emitter, unsupported REAL/local/oversized
signatures fail instead of falling
back to opaque output, and decimal, hexadecimal, and binary call literals pass
object, zero-lookahead REU-window, and live VICE checks. This closes the
maintained ASMBLOCK-based fixed-entry ABI. Core raw blocks subsequently added
the 1,322nd broad and 166th source-backed shapes; their focused OBJ probes and
the complete 166-case source-backed ACTC/ALINK/live-VICE matrix pass. Numeric
absolute-address declarations subsequently added the 1,323rd broad and 167th
source-backed shapes. The new focused compile, exact OBJ, ALINK closure, and
live-VICE launch pass with no selected library objects; the refreshed complete
1,323/167 matrices remain release-validation gates. Forward/backward linked
local-routine aliases and signed 16-bit literal addends then added the 1,324th
broad and 168th source-backed shapes. Their focused native compile, named OBJ1
relocation, direct ALINK closure, and live-VICE launch pass without a selected
library object; refreshed complete 1,324/168 matrices remain release gates.
Numeric and linked routine-address expression parity is now covered by native
and Idun object regressions plus native direct-PRG VICE launches using grouped
`$FFD0+2` and zero-addend `(1-1)+WORKER`. General REAL, MATH1,
array/pointer/record, graphics-resource, expanded GFX1,
resource-editor, workflow, and physical-hardware work remain as listed above.

The 2026-07-19 native preprocessing slice now runs atomically in dedicated
pass `I` over the REU-staged source. Focused compiler regressions pass for multiline and
recursive token-aware `DEFINE`, compatibility `SET`, nested library includes,
project-source precedence, include-cycle rejection, definition-capacity
diagnostics, comment/character preservation, and ordinary OBJ emission. Native
limits and the intentionally narrower UDOS path contract are recorded in the
language guide. The bounded typed-constant path removes BYTE/CHAR/CARD/INT
declarations without OBJ storage, evaluates Idun's checked signed 64-bit
parenthesized arithmetic, shift, bitwise, character, and built-in-constant
grammar, enforces target type ranges, folds REAL expressions to canonical
binary32 literal words, and emits
full 16-bit variable initializers. A streamed whole-source preflight recognizes transform-bearing
lines before or after `MODULE`, while directive-free units retain their exact
REU bytes and established long-line streaming behavior. Eleven focused
preprocessing/constant regressions, the rebuilt DNP release, and the complete
791-test native suite pass. A shared fixture additionally compares exact
native substitutions with Idun OBJ bytes. A second shared fixture proves that
all 16 GFX1 and 8 MATH1 constants fit together without allocating target
storage. The binary32 evaluator accepts decimal and exponent forms, prior REAL
constants, arithmetic and grouping, `REAL`, `FABS`, `FSQRT`, infinity, and NaN.
Its exact integer-ratio decimal conversion and every intermediate operation use
round-to-nearest, ties-to-even. A source-backed direct-PRG case prints `7.5`,
selects only `RT_PRINT_F.OBJ`, and rejects unrelated conversion and arithmetic
modules. That case raises the current inventories to 1,325 broad and 169
source-backed shapes; both complete matrices pass.

The subsequent two-REAL-parameter ABI checkpoint raises those inventories to
1,326 broad and 170 source-backed shapes. Its focused native object test,
deterministic ALINK probe, and live VICE launch pass with separate checks for
both caller values, both callee parameter copies, and the returned value. Pass
A is 7,406 bytes and retains 786 bytes in its 8 KiB code window under a
768-byte reserve. General REAL bodies, nested calls, and MATH1 remain work item
1 rather than being claimed by this bounded form.

The subsequent finite comparison/select checkpoint raises the current
inventories to 1,327 broad and 171 source-backed shapes. Dedicated pass K emits
ordinary machine exports, named storage relocations, separate root/function
body markers, and imports for comparison plus integer conversion. The root
marker carries the reachable union so generic ALINK resolves all relocations;
the function marker remains comparison-only when that export is selected
independently. The rebuilt release, deterministic linker probe, and live VICE
launch pass, with exact checks for 2.0 and 1.0 caller/callee values and the 1.0
result. The complete 171-case source-backed ACTC/ALINK/live-VICE matrix also
passes. Pass K is 3,257 bytes and leaves 4,935 bytes in its 8 KiB code window.
The same source is a shared parity fixture and compiles/links with Idun ACTC.
Idun folds the two constant `REAL(integer)` initializers, while native pass K
executes the reachable `RT_I_TO_F.OBJ`; both select `RT_F_CMP.OBJ` and produce
the same finite result. This optimizer difference is not an OS dependency.
General expression trees, arbitrary control flow, nested calls, and the
remaining dependency-sized MATH1 modules remain work item 1.

The 2026-07-20 selector slice adds independently link-selected
`RT_F_MIN.OBJ` and `RT_F_MAX.OBJ`. Exact host execution checks all 2,304
edge/random input pairs per operation, including one-NaN, two-NaN, signed-zero,
and equal-value bit preservation. Native ACTC focused OBJ checks and live VICE
launches print `1` for minimum and `2` for maximum while proving that the
unselected sibling helper is absent. The broad direct-PRG inventory is now
1,331 shapes, the source-backed object-emission inventory remains 171 shapes,
and the compiled-runtime relocation oracle covers 290 cases. Idun carries the
same generated target modules and manifest; its portable MATH1 source remains
the general implementation. Current hardware-independent Idun release gates
also pass: 153 active Linux tests, 138 sanitizer tests, 21 direct-PRG tests with
the documented VICE 3.7 DBF/REU skip, and verified host plus static AArch64
exports containing 31 commands and 260 help topics. This selector refresh has
not yet been redeployed to the Pi or accepted on an attached cartridge/C64.

The subsequent native `FSign` slice adds byte-identical `RT_F_SIGN.OBJ` to the
shared runtime snapshot. The helper is 123 bytes with no imports, so ALINK adds
it only when reachable and does not pull comparison or exceptional-value
support into an otherwise unary program. Native ACTC recognizes `FSign(A)` for
a named REAL in assignment, print, and REAL-condition positions. The exact
host oracle checks 2,304 edge/random inputs, including all NaN classes,
infinities, subnormals, and both signed zeroes. The focused direct PRG prints
`-1` and proves that `RT_F_ABS`, `RT_F_SQRT`, `RT_F_MIN`, and `RT_F_MAX` remain
unselected. The collector refactor reuses the shared REAL-value emitter and
increases its 8 KiB overlay reserve from 96 to 230 bytes despite adding this
syntax. This closes only the seventh native MATH1 declaration; portable
multi-function MATH1 still depends on work items 1 and 2.

The following native `FClamp` slice adds byte-identical `RT_F_CLAMP.OBJ` to
both products. The 199-byte module reads value/lower/upper pointers through
`$02-$05` and `$08/$09`, writes through `$06/$07`, rejects any NaN or inverted
bounds with canonical quiet NaN, and otherwise preserves the selected operand
through `FMin(FMax(value,lower),upper)`. Pass K emits the bounded constrained
three-initializer assignment-and-print root because adding it to pass A would
have violated that overlay's enforced 768-byte growth reserve. A follow-up
matcher captures all eight named-storage uses and patches the same 171-byte
machine root, proving permuted initializer, argument, destination, and print
roles without widening the statement grammar. Pass A remains 7,406 bytes with
786 bytes free; pass K is 4,359 bytes with 3,833 bytes free. At that checkpoint,
the direct-PRG inventory was 1,332 shapes, the non-runtime source-backed
object-emission inventory remains 171 shapes, and the compiled-runtime
relocation oracle covers 291 cases. This closed the eighth native call at that
checkpoint; the later constants-header slice completed all eight compile-time
constants, while the other 35 public MATH1 routines still depend on general
REAL source lowering.

The next finite-function storage slice replaces pass K's fixed root and callee
slot assumptions with bounded role captures. A shared permuted fixture declares
`RESULT/RIGHT/LEFT`, names the parameters `B/A`, and still returns 1.0 from the
same 185-byte object layout. Native object assertions and a direct VICE launch
verify all five REAL cells; Idun compiles, links, and executes both fixtures with
its existing general Linux compiler. At that checkpoint the inventories were
1,333 broad direct-PRG shapes, 172 non-runtime source-backed object-emission shapes, and 291
compiled-runtime relocation-oracle cases. Pass K is 4,594 bytes with 3,598
bytes free; no shared runtime module changed.

The next pass-A return slice separates the bounded two-parameter function's
captured return storage from its caller argument storage. A shared fixture
declares `RESULT/RIGHT/LEFT`, binds `B/A`, returns the second parameter `A`, and
writes 2.0 while all five caller/callee REAL cells are checked. Linux ACTC/ALINK
already accepts and executes the same source. At that checkpoint the inventories
were 1,334 broad direct-PRG shapes, 173 non-runtime source-backed object-emission
shapes, and 291 compiled-runtime relocation-oracle cases. Pass A is 7,418 bytes with
774 bytes free under its 768-byte reserve; no shared runtime or linker changed.

The next MATH1 slice adds `FTrunc` as a 107-byte, dependency-free common OBJ1
module and routes native assignment, direct-print, and REAL-condition calls
through the existing unary emitter. Idun ACTC recognizes the same intrinsic,
constant-folds constant calls, emits `RT_F_TRUNC` for dynamic calls, and no
longer embeds the former portable FTrunc body. Exact host and Idun VICE execution covers all exponent
classes plus random binary32 bit patterns, including signed zero, subnormals,
infinities, and NaN payloads. The focused direct PRG loads only integer
conversion, truncation, and printing modules; its deliberately staged sibling
helpers remain absent. At that checkpoint inventories were 1,335 broad direct-PRG shapes,
173 non-runtime source-backed object-emission shapes, and
292 compiled-runtime relocation-oracle cases. Pass 6 is 8,071 bytes and retains 121 bytes under its
96-byte growth reserve; pass A remains unchanged at 7,418 bytes.

The following MATH1 floor slice adds the 135-byte `RT_F_FLOOR.OBJ`. It imports
`RT_F_TRUNC.OBJ`, is safe when source and destination alias, and preserves NaN
payloads, infinities, signed zero, and integral values while rounding finite
nonintegers toward negative infinity. Native ACTC handles assignment,
direct-print, and REAL-condition forms; the focused VICE PRG proves the
`floor -> trunc` ALINK closure and sibling pruning. Idun ACTC parses,
constant-folds, and emits the same intrinsic, and MATH1 no longer embeds its
portable `FFloor` body. Exact host checks and 116 full-domain Idun VICE vectors
pass. At that checkpoint inventories were 1,336 broad direct-PRG shapes, 173 non-runtime
source-backed object-emission shapes, and
293 compiled-runtime relocation-oracle cases. Pass 6 is 8,082 bytes and retains 110 bytes under its
96-byte growth reserve; the native MATH1 gap was 33 public routines.

The next MATH1 ceiling slice adds the 42-byte `RT_F_CEIL.OBJ`. It implements
`ceil(x) = -floor(-x)`, imports `RT_F_FLOOR.OBJ` and therefore transitively
`RT_F_TRUNC.OBJ`, is safe when source and destination alias, and preserves NaN
payloads, infinities, signed zero, and integral values while rounding finite
nonintegers toward positive infinity. Native ACTC handles assignment,
direct-print, and REAL-condition forms; the focused VICE PRG proves the
`ceil -> floor -> trunc` ALINK closure and sibling pruning. Idun ACTC parses,
constant-folds, and emits the same intrinsic, and MATH1 no longer embeds its
portable `FCeil` body. Exact host checks and 116 full-domain Idun VICE vectors
pass. At that checkpoint inventories were 1,337 broad direct-PRG shapes, 173
non-runtime source-backed object-emission shapes, and 294 compiled-runtime
relocation-oracle cases. Refactoring pass 6 unary dispatch reduced it to 8,062
bytes with 130 bytes free under its 96-byte growth reserve.

The following MATH1 round slice adds the 152-byte `RT_F_ROUND.OBJ`. It imports
only `RT_F_TRUNC.OBJ`, is safe when source and destination alias, preserves NaN
payloads, infinities, signed zero, and integral values, and rounds finite
nonintegers nearest with halfway cases away from zero. The implementation is
bit-level rather than `floor(x+0.5)`/`ceil(x-0.5)`, so binary32 integers above
the 24-bit precision boundary are unchanged. Native ACTC handles assignment,
direct-print, and REAL-condition forms; Idun parses and constant-folds the same
intrinsic and emits the shared module only for dynamic calls. Exact host checks,
116 full-domain Idun VICE vectors, and the focused native direct PRG cover ties,
large integral values, aliasing, `round -> trunc` closure, and sibling pruning.
At that checkpoint inventories were 1,338 broad direct-PRG shapes, 173 non-runtime
source-backed object-emission shapes, and 295 compiled-runtime relocation-oracle
cases. Native pass 6 was 8,074 bytes with 118 bytes free under its 96-byte growth
reserve; the native MATH1 gap was 31 public routines.

The next MATH1 fractional-part slice adds the 93-byte `RT_F_FRAC.OBJ`. It
imports `RT_F_TRUNC.OBJ` and `RT_F_SUB.OBJ`, with the ordinary add/sub core and
special-value module selected transitively, and implements
`value-FTrunc(value)`. The helper is safe for aliased source/destination
pointers. Native ACTC handles assignment, direct-print, and REAL-condition
forms; Idun parses and constant-folds the same intrinsic and emits the shared
module only for dynamic calls. Exact host checks, 116 full-domain Idun VICE
vectors, and the focused native direct PRG cover signed finite fractions,
integral cancellation, exceptional values, aliasing, complete dependency
closure, and sibling pruning. At that checkpoint inventories were 1,339 broad direct-PRG
shapes, 173 non-runtime source-backed object-emission shapes, and
296 compiled-runtime relocation-oracle cases. Native pass 6 was 8,085 bytes with
107 bytes free under its 96-byte growth reserve; the native MATH1 gap was 30
public routines.

The following MATH1 remainder slice adds the 245-byte `RT_F_MOD.OBJ`. It is
safe when either source pointer aliases the destination and imports
`RT_F_DIV.OBJ`, `RT_F_TRUNC.OBJ`, `RT_F_MUL.OBJ`, and `RT_F_SUB.OBJ`, with the
ordinary add/sub special-value closure selected transitively. Native ACTC
handles assignment, direct-print, and REAL-condition forms. Idun ACTC parses
and constant-folds the same intrinsic, emits `RT_F_MOD` only for dynamic calls,
and no longer embeds the former portable FMod body. Exact host checks cover 332
vectors in each of the ordinary, left-alias, and right-alias modes; the
116-pair Idun VICE fixture
and focused native direct PRG prove end-to-end semantics, complete dependency
closure, and sibling pruning. At that checkpoint inventories were 1,340 broad direct-PRG
shapes, 173 non-runtime source-backed object-emission shapes, and
297 compiled-runtime relocation-oracle cases. Native pass 6 was 8,094 bytes with 98
bytes free under its 96-byte growth reserve; the native MATH1 gap was 29
public routines.

The next MATH1 hypotenuse slice adds the 503-byte `RT_F_HYPOT.OBJ`. It is safe
when either source pointer aliases the destination and imports
`RT_F_ABS.OBJ`, `RT_F_MIN.OBJ`, `RT_F_MAX.OBJ`, `RT_F_DIV.OBJ`,
`RT_F_MUL.OBJ`, `RT_F_ADD.OBJ`, and `RT_F_SQRT.OBJ`. The scaled
maximum/minimum algorithm avoids avoidable intermediate overflow and
underflow. Native ACTC handles assignment, direct-print, and REAL-condition
forms; Idun parses and constant-folds the same intrinsic and emits the shared
module only for dynamic calls. Exact host checks cover 2,316 vectors in each
of the ordinary, left-alias, and right-alias modes. The 116-pair Idun VICE
fixture, focused native direct PRG, and complete native MATH1 runtime matrix
prove end-to-end behavior, dependency closure, and sibling pruning. The same
slice fixes ALINK paged-object import discovery by stabilizing each body
selector before recursive lookups can reload the source window; an 11-import
fixture exercises that boundary. At that checkpoint inventories were 1,341 broad
direct-PRG shapes, 173 non-runtime source-backed object-emission shapes, and
298 compiled-runtime relocation-oracle cases. Native pass 6 is 8,093 bytes
with 99 bytes free under its 96-byte growth reserve; the native MATH1 gap is
now 28 public routines.

The next native compiler slice generalizes REAL function returns through the
body-overlay auxiliary parser entry. Pass K accepts the bounded selected-binary
return described above and allocates a hidden non-aliasing result cell. The
shared `real_function_binary_hypot.act` fixture compiles and links through Idun,
while native ACTC/ALINK and VICE prove the same source and result with unused
MATH1 siblings staged but not loaded. At that checkpoint inventories were
1,342 broad direct-PRG shapes, 174 non-runtime source-backed object-emission
shapes, and 298 compiled-runtime relocation-oracle cases. Pass K is 5,877 bytes with
2,315 bytes free in its 8 KiB window. The following internal parser preparation
lets pass 6 collect bounded nested REAL operands without changing the runnable
source contract; it is 8,094 bytes with 98 bytes free under the 96-byte gate.
Pass 7 now preallocates the same tree in postfix helper order; it is 6,587 bytes
with 1,605 bytes free. A mixed unary/binary/ternary regression starts its outer
helper at source byte 1,270 and proves the tree across the production 1,280-byte
source-window boundary. Pass L now lowers those postfix trees to executable
OBJ1 for one `MAIN`, up to 16 module REAL variables, 16 temporary REAL cells,
an eight-value expression stack, and 64 debug offsets. It accepts integer-to-
REAL conversion, REAL assignment/print, the supported unary and binary MATH1
helpers, and `FClamp`; it emits `__idata` plus source-variable debug records so
ACTDBG sidecars remain usable. Focused ALINK/VICE cases execute
`FMin(FMax(A,B),C)` and `FClamp(FAbs(A),FMin(B,C),FMax(A,C))`, print `2`, prove
16-bit internal export offsets, and prune unreferenced helpers. That one-`MAIN`
checkpoint had 1,344 broad direct-PRG shapes, 176 non-runtime source-backed
object-emission shapes, and 298 compiled-runtime relocation-oracle cases. Pass
L then added the bounded two-REAL-parameter callee ABI described above. Its
exact OBJ regression verifies separate root and function exports, caller
pointer pushes, reverse parameter binds, an A/X result pointer, DBG1
line/variable records, and ordinary ALINK relocations. The shared fixture
compiles and links with Idun; the rebuilt native release prints `5` in VICE
while loading only the `FAbs`/`FHypot` closure plus conversion and printing.
Pass L then added bounded all-REAL static locals to that same nonrecursive
callee. The shared `real_function_local_nested_postfix.act` fixture emits a
DBG1 local record plus ordinary local load/store relocations; Linux ACTC/ALINK
accepts the same source, and native VICE verifies binary32 5.0 in the result and
3.0 in the local while printing `5`. Pass L now also accepts two independent
callees in one module. The shared `real_two_function_nested_postfix.act`
fixture emits distinct `length` and `shorter` exports, disjoint parameter/local
storage, and three DBG1 procedure banks; native ACTC/ALINK prints `5` and `3`
while VICE verifies both results and both locals. Linux ACTC gained direct
`FMin`/`FMax` expression lowering to the same selected runtime objects and
executes the fixture with identical results. Pass L first added one
declaration-order function edge. The shared
`real_function_call_chain_postfix.act` fixture emits ordinary `MAIN -> CHAIN`
and `CHAIN -> LENGTH` export relocations. Native VICE verifies binary32 5.0 in
both the module result and `CHAIN.BASE`; Idun ACTC/ALINK executes the same source
with the same result. The shared
`real_function_nested_local_call_postfix.act` fixture then removes the temporary
source local and feeds `LENGTH(A,B)` directly into `FMax`; pass 7 traverses the
local call without creating a phantom library import. Pass 7 is now 6,678 bytes
with 1,514 bytes free in its 8 KiB window; native VICE verifies 5.0 in both the
module result and nested-call temporary, and Idun executes the same source.
The shared `real_function_user_call_arguments_postfix.act` fixture next feeds
two calls to `LOWER` into a third call. Pass L copies each returned A/X pointer
to a distinct temporary, so overwriting the callee's static cells cannot alias
the outer arguments; native VICE and Idun both produce 3.0.
The shared `real_function_forward_frame_postfix.act` fixture then reverses the
declaration direction with `FIRST -> SECOND` while keeping the `FAbs(A)`
temporary live. Pass L stack-saves `FIRST`'s parameters and live temporary,
stages `SECOND`'s A/X result, restores the caller cells, and produces 3.0 in
both products. Self and mutual cycles remain rejected.
The shared `real_function_if_else_postfix.act` fixture next executes both paths
of one nonnested REAL-function `IF`/`ELSE`. Pass M maps `A<B` through
`rt_f_cmp`, relocates long branches to ordinary internal code exports, and both
products print `34`. Pass N then runs two sequential controls and a depth-two
nested pair through the shared fixtures; both products print `43` and `143`.
Current inventories are 1,354 broad direct-PRG shapes, 186 non-runtime
source-backed object-emission shapes, and 298 compiled-runtime relocation-oracle
cases. Pass L is 6,124 bytes with 2,068 bytes free; pass M is 6,998 bytes with
1,194 bytes free; pass N is 7,120 bytes with 1,072 bytes free under its 1 KiB
gate. The 28-routine MATH1 gap is unchanged.

Pass 1 now contains only the streamed module-header validator. Moving the
transform into `ACTC_OVLI.BIN` reduced pass 1 to 788 bytes. Integer folding,
the packed definition store, address canonicalization, and the resident
binary32-evaluator callback expand pass `I` to 7,680 bytes, occupying
`$A000-$BDFF` and retaining exactly the enforced 512-byte reserve. The evaluator
itself is resident and uses a deterministically generated private copy of the
shared target arithmetic closure. Its 3,150-byte `$8000-$8C4D` scratch is
Tool-ABI-preserved and active only before body/ASMBLOCK work. All pass code is
hard-limited to `$A000-$BFFF`; UDOS live state at `$C000+` is forbidden.
Linker-allocated pass BSS is limited to `$8000-$9DFF`; ASMBLOCK's transfer page,
label index, and emitter state occupy the reserved `$9E00-$9F1E` range. Pass J
is 7,901 bytes with 291 bytes free under its 256-byte reserve; pass A is 7,418
bytes with 774 bytes free under its 768-byte reserve; pass K is 5,877 bytes with
2,315 bytes free. The complete
228-test overlay suite and 198-test source-cache suite pass with this layout.

Shipped and ordinary harness builds default to
`ACTC_ENABLE_REAL_CONST_EVALUATOR=1`. The legacy all-resident body, layout, and
emitter configurations are capacity diagnostics rather than release compilers;
their tests explicitly set the option to `0`, retain the pass-I callback ABI,
and reject `REAL CONST` instead of carrying the 6502 evaluator alongside every
resident fallback implementation.
