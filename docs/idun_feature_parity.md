# Idun And UDOS Feature Parity

This document compares user-visible capabilities, not executable
implementations. The Idun fork runs development tools as Alpine Linux
processes. The native product runs its tools as 6502 programs under UDOS.
Generated applications in both products remain self-contained C64 PRGs built
from OBJ1 modules, and ALINK selects only reachable 6502 code and data.

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
| Typed functions and recursive frames | BYTE/CARD/INT/REAL, nested calls, direct/mutual recursion | Scalar nonrecursive word functions plus constrained REAL forms | Native compiler/ABI gap |
| Application REU arrays | `REU BYTE ARRAY` plus 8/16-bit accessors | Runtime helpers exist, but native ACTC has no declaration/access lowering | Native compiler gap; compiler REU workspace is not equivalent |
| Program-owned overlay sections | `OVERLAY`/`ENDOVERLAY` and relocated `OverlayCall` | No native source lowering | Native compiler gap; ACTC tool overlays are not equivalent |
| Program argument entry | `MAIN(argc,argv)` through the Idun target service | `MAIN()` and UDOS command-tail workflow | OS-specific contracts; expose equivalent user arguments without copying the Idun upload ABI |
| IEEE-754 binary32 arithmetic and exceptional values | Standalone modules | Standalone modules plus native support modules | Parity at runtime |
| General REAL source expressions, calls, and returns | Full binary32 compiler path | Core operations, direct `FSign`/`FMin`/`FMax` on named REAL values, and constrained zero-, one-, and two-parameter native function shapes | Native compiler gap; these builtin semantics are complete, but arbitrary expression trees, calls, and returns are not |
| INPUT1 joystick/two-button mouse API | 19 declarations | 19 declarations | Parity; physical checks remain |
| DBF1 API | 20 declarations | 20 declarations | Parity; physical REU/disk checks remain |
| SIDSPR1 API | 37 declarations | 37 declarations | Parity; physical SID/display checks remain |
| Full MATH1 source library | 43 public routines plus 8 constants, 51 catalog features; one private helper | Seven callable declarations: `PrintR`, `PrintRE`, `FAbs`, `FSqrt`, `FSign`, `FMin`, and `FMax` | Native implementation gap |
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

## Native Work Order

The constant foundation is complete. Native pass I folds `REAL CONST` decimal
and exponent literals, dependent constants, unary and grouped expressions,
`+`, `-`, `*`, `/`, `REAL`, `FABS`, `FSQRT`, `INF`/`INFINITY`, and `NAN` at
binary32 precision. Decimal conversion and every operation use
round-to-nearest, ties-to-even. The result is emitted as four literal bytes, so
constant-only arithmetic does not select target conversion or arithmetic
helpers. The evaluator is resident, while pass I retains its full 512-byte code
reserve.

The first item now has four tested checkpoints. Native pass A accepts two named
REAL arguments after their immediate `REAL(integer)` initializers, copies both
values into distinct parameter storage, and returns the first parameter by
pointer. Dedicated pass K then lowers the exact finite comparison/select form
`IF B<A THEN RETURN(B) FI RETURN(A)`. Its focused OBJ/ALINK/VICE proof selects
`RT_I_TO_F.OBJ`, `RT_F_CMP.OBJ`, and transitive `RT_F_SPECIAL.OBJ`, while
unrelated REAL helpers remain absent. Native ACTC now also lowers `FMin(A,B)`
and `FMax(A,B)` for named REAL operands in assignment, print, and REAL-condition
positions. Their 77-byte modules implement the complete MATH1 NaN and signed-
zero selection policy through ordinary `RT_F_CMP.OBJ` closure. Native ACTC also
lowers `FSign(A)` in those positions through a dependency-free 123-byte helper
that canonicalizes NaN, preserves signed zero, and returns signed one for every
other input. General REAL expression trees, nested calls, and the rest of MATH1
remain incomplete.

Remaining work is dependency ordered:

1. Generalize native REAL declarations, parameters, locals, expressions, calls,
   and returns enough to compile portable multi-function MATH1 modules.
2. Port MATH1 in dependency-sized OBJ modules and prove representative values
   in direct linked PRGs without making unused functions reachable.
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
The complete ACTC compiler, passes 0 through K, development tools, libraries,
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

The 2026-07-20 current cross-product baseline passed:

- 792 native ActionC64U unittests, including compiler-overlay capacity, OBJ1,
  ALINK closure, IEEE-754, ACTEDIT, ACTDBG, Linux compatibility, export, and
  release-image checks;
- 133 UDOS integration tests, with one intentional embedded-AUTOEXEC capacity
  skip, plus rebuilt release artifacts and direct VICE launches for both
  side-effect and stored-result runtime calls through the native REAL bridge;
- 151 Idun/Alpine unittests covering the Linux compiler/linker, libraries,
  resource editors, help, semantic map, debugger/profiler transport, export,
  and packaging contracts;
- 136 Idun ASan/UBSan tests covering the Linux tools under instrumented builds;
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
1,330 shapes, the source-backed object-emission inventory remains 171 shapes,
and the compiled-runtime relocation oracle covers 289 cases. Idun carries the
same generated target modules and manifest; its portable MATH1 source remains
the general implementation. Current hardware-independent Idun release gates
also pass: 151 active Linux tests, 136 sanitizer tests, 21 direct-PRG tests with
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
is 7,901 bytes with 291 bytes free under its 256-byte reserve; pass K is 3,257
bytes with 4,935 bytes free. The complete
204-test overlay suite and 198-test source-cache suite pass with this layout.

Shipped and ordinary harness builds default to
`ACTC_ENABLE_REAL_CONST_EVALUATOR=1`. The legacy all-resident body, layout, and
emitter configurations are capacity diagnostics rather than release compilers;
their tests explicitly set the option to `0`, retain the pass-I callback ABI,
and reject `REAL CONST` instead of carrying the 6502 evaluator alongside every
resident fallback implementation.
