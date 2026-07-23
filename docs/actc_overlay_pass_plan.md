# ACTC REU Overlay Pass Plan

Current as of `2026-07-19`.

## Goal

Turn `ACTC.PRG` from one large resident compiler image into a small batch driver
that runs compiler passes from reusable overlay memory.

The driver should keep only permanent services, source/table window helpers, and
the pass scheduler resident. Each compiler pass should be loaded into REU once,
copied into the same C64 execution window when needed, run, and then replaced by
the next pass.

## Proposed Shape

- `ACTC.PRG` remains the user-facing command.
- On startup, `ACTC.PRG` stages source and pass overlays into REU.
- One fixed C64 overlay execution window is reserved for pass code.
- The driver copies pass code from REU into that window with `svc_reu_read_sc0`.
- Each pass reads and writes REU-backed program data through stable helper ABI
  routines.
- Passes advance the representation instead of all passes sharing one resident
  code body.

## Data Model

- Source text: staged in REU and paged through source-reader windows.
- Symbols and names: REU-backed string tables with small resident windows.
- Procedure bodies: REU-backed `body_ops` windows.
- Literals and metadata: now REU-backed fixed-record tables for the current
  ACTC cold metadata set.
- Final object output: streamed through write begin/chunk/close services.

## Current Overlay Artifacts

The overlay artifacts share one stable execution ABI:

- `src/tools_udos/actc/actc_overlay_abi.inc` defines overlay ABI version `5`.
  Version 5 extends the compact v4 context to 231 contiguous bytes with the
  resident binary32 `REAL CONST` evaluator callback; the resident loader rejects
  stale overlay binaries.
- `src/tools_udos/actc/actc_overlay_noop.asm` builds the pass-0 workflow helper.
  A zero body mode preserves the original no-op ABI, while nonzero workflow
  modes construct strict 31-byte `ALINK` or source-positioned `ACTEDIT`
  successor commands outside resident ACTC.
- `tools/build_actc_overlay_noop.sh` emits `build/udos_tools/ACTC_OVL0.BIN`.
- `src/tools_udos/actc/actc_overlay_source_header.asm` builds the first
  source-aware pass.
- `tools/build_actc_overlay_source_header.sh` emits
  `build/udos_tools/ACTC_OVL1.BIN`.
- `src/tools_udos/actc/actc_overlay_decl_counts.asm` builds the first
  declaration-scanning pass.
- `tools/build_actc_overlay_decl_counts.sh` emits
  `build/udos_tools/ACTC_OVL2.BIN`. Forward/backward linked-routine alias
  resolution plus general routine-address expressions occupy 6,348 code bytes,
  leaving 1,844 bytes under the hard 8 KiB ceiling. Its mutable declaration
  caches live in the shared `$8000-$9FFF` overlay scratch window.
- `src/tools_udos/actc/actc_overlay_preprocess.asm` builds the atomic source
  transform as base-36 pass `I`; `tools/build_actc_overlay_preprocess.sh` emits
  `build/udos_tools/ACTC_OVLI.BIN`.
- The workspace exporter and UDOS release Makefile include base-36 passes
  `ACTC_OVL0.BIN` through `ACTC_OVLU.BIN` next to `ACTC.PRG`, so pass files are
  present when the scheduler runs from an exported or release image.
- `tests/test_actc_overlay.py` proves the `ACOV` header, ABI version, pass id,
  `$A000` execution base, encoded byte length, compatibility no-op return, and the
  source-header/declaration-count passes receiving the resident source-window
  context. The declaration-count pass also proves writing resident count state
  through explicit context pointers and writing module variable names/metadata,
  procedure export names, and procedure parameter/local names/metadata through
  the resident REU table helpers. It also emits module-scope decimal arithmetic,
  helper-constant, and comparison/boolean initializer values in var metadata. It
  keeps an overlay-local declaration cache plus declaration initializer
  validation so duplicate names, malformed
  declaration tails, and invalid initializer tails return failed overlay status
  instead of partial success.
- `actc_overlay_run_pass` in `ACTC.PRG` accepts a pass id in `A`, constructs its
  base-36 pass filename, stages that file into REU at `$008000`, copies it to `$A000`, passes
  a context block to the overlay in `X/Y`, banks out BASIC ROM for the call,
  executes it, and restores the previous memory configuration.
- `ACTC.PRG` now has a multi-stage compile-path overlay handoff. When built with
  `ACTC_USE_SOURCE_HEADER_OVERLAY=1` and `ACTC_USE_DECL_OVERLAY=1`, it calls
  `ACTC_OVL1.BIN` for module-header validation, conditionally calls
  `ACTC_OVLI.BIN` when the streamed whole-source preflight finds a transform,
  and then calls `ACTC_OVL2.BIN` for declaration scanning. The current
  production path also stages `ACTC_OVL6.BIN`
  for proc-body lowering, `ACTC_OVL4.BIN` for runtime-import detection,
  two-pass ASMBLOCK assembly, and raw code-block encoding, `ACTC_OVL3.BIN` for payload layout,
  `ACTC_OVL9.BIN` for multi-procedure native integer and ASMBLOCK object
  emission, `ACTC_OVLG.BIN` for runtime-argument integer control,
  `ACTC_OVLH.BIN` as the universal composed emitter for runtime-argument calls,
  ASMBLOCK, `=*(...)`, and numeric absolute-address declarations in one unit,
  `ACTC_OVLJ.BIN` for compact numeric absolute-address routine units, and
  `ACTC_OVLK.BIN` for bounded two-REAL-parameter finite comparison/select
  functions, `ACTC_OVLL.BIN` for bounded nested straight-line REAL trees, and
  `ACTC_OVLM.BIN` for the same function form with one bounded `IF`/`ELSE`, and
  `ACTC_OVLN.BIN` for two sequential or depth-two nested conditionals,
  `ACTC_OVLO.BIN` for up to four sequential or depth-four nested controls, and
  `ACTC_OVLP.BIN` for bounded conditional early returns with a terminal
  fallback, and `ACTC_OVLQ.BIN` for bounded REAL-function post-test and
  pre-test loops, `ACTC_OVLR.BIN` for plain loops plus nearest-loop `EXIT`, and
  `ACTC_OVLS.BIN` for constant-bound CARD-counter REAL-function `FOR` loops,
  `ACTC_OVLT.BIN` for named CARD initial/final bounds, and `ACTC_OVLU.BIN` for
  folded binary32 literals plus one- or two-REAL-parameter functions.
  Passes 8 and A through H retain their native integer, REAL,
  runtime, and composition roles.
  The same path stages `ACTC_OVL5.BIN` as the generic object-emission fallback
  and `ACTC_OVL7.BIN` for overlay-hosted body external preallocation. On
  success, later compiler phases consume the overlay-written REU metadata.
  Overlay staging uses the executable-relative tool ABI path prefix, so
  `!ACTC_OVL1.BIN` through `!ACTC_OVLU.BIN` resolve beside the launched
  `ACTC.PRG`.
- `tools/build_actc_udos.sh` always builds `ACTC_OVL0.BIN`, including compiler
  harness builds, because compile/link/debug chaining and compile-error editor
  return use pass 0 even when no normal compilation pass needs it.
- `tools/build_actc_overlay_body_collect.sh` now also builds
  `build/udos_tools/ACTC_OVL6.BIN`, pass id `6`, which is the current
  proc-body lowering overlay. `tools/build_actc_overlay_body_preallocate.sh`
  builds `build/udos_tools/ACTC_OVL7.BIN`, pass id `7`, which owns the
  overlay-hosted preallocation scanner. Its current 6,678-byte image leaves
  1,514 bytes free in the 8 KiB window. Both are packaged beside `ACTC.PRG` and
  enabled in the default production build.
- `tools/build_actc_overlay_emit_native_local_object.sh` builds
  `build/udos_tools/ACTC_OVL9.BIN`, pass id `9`. It owns native local-procedure
  exports, calls, control-flow targets, debug offsets, and relocations. It also
  owns single-procedure plain DO, WHILE, and DO/WHILE EXIT bodies that pass 8
  declines, including dynamic word arithmetic, integer printing, and
  stack-neutral no-argument external calls inside WHILE control. Multiply,
  divide, printing, and external procedures remain ordinary link-selected
  imports with compiler-emitted call relocations.
  It also consumes pass-4 ASMBLOCK/raw-block pages, inserts their machine bytes at body
  markers, exports block-local absolute targets, and emits normal word or
  low/high-byte variable, local-routine, and label relocations. Variable data allocation and
  exports preserve two-byte scalar and four-byte REAL widths.
  It returns not-applicable before the remaining single-procedure or generic
  emitters run. Its 7,599-byte image leaves 593 bytes free under a dedicated
  128-byte minimum reserve.
- `tools/build_actc_overlay_emit_native_local_runtime_object.sh` builds
  `ACTC_OVLG.BIN`, pass id `16`, for one-word byte-in-A and word-in-X/Y runtime
  calls inside integer control. Its 6,645-byte image leaves 1,547 bytes free under
  a 512-byte reserve.
- `tools/build_actc_overlay_emit_native_local_mixed_object.sh` builds
  `ACTC_OVLH.BIN`, pass id `17`. It requires both assembled blocks and a
  supported runtime argument call, or acts as the fallback for a composed
  numeric fixed-address unit, then emits one native OBJ with ordinary imports
  and relocations. Writable emitter state is BSS in the shared scratch window;
  the 8,064-byte code image leaves exactly 128 bytes free under a
  128-byte reserve.
- `ACTC_OVLI.BIN`, pass id `18`, owns bounded token-aware `DEFINE`, `SET`,
  recursive `INCLUDE`, typed-constant transformation, and routine-address
  expression canonicalization, including the shared signed 64-bit integer-
  expression grammar, binary32 `REAL CONST` folding, and a packed 1,350-byte
  definition store. Its 7,680-byte code image occupies `$A000-$BDFF` and leaves
  exactly the enforced 512-byte reserve in the `$A000-$BFFF` overlay window.
  Binary32 parsing and arithmetic run through the ABI-v5 resident callback, so
  the evaluator does not consume pass I's reserve. Its 3,150-byte mutable
  workspace occupies `$8000-$8C4D`, reusing
  ACTC's Tool-ABI-preserved overlay scratch area before ASMBLOCK collection begins.
  Production and ordinary harness builds enable this callback. Explicit legacy
  all-resident capacity builds use an ABI-compatible rejecting stub so the
  evaluator is not duplicated beside resident body/layout/emitter fallbacks.
- `tools/build_actc_overlay_emit_native_fixed_object.sh` builds
  `ACTC_OVLJ.BIN`, pass id `19`. It emits numeric and linked absolute-address
  declarations as direct or relocated `JSR` instructions and owns `*=...`
  register-ABI machine routines with ASMBLOCK bodies. It declines composed
  runtime units so pass H can own them. Its 7,901-byte image leaves 291 bytes
  free in the 8 KiB execution window, guarded by a 256-byte reserve.
- `tools/build_actc_overlay_emit_native_real_function_object.sh` builds
  `ACTC_OVLK.BIN`, pass id `20`. It owns the bounded finite
  two-REAL-parameter comparison/select checkpoint plus the bounded four-REAL
  `FClamp` assignment/print skeleton and a bounded two-parameter selected-binary
  return. The function matcher captures caller and
  parameter storage roles while retaining the exact finite select statement
  shape; the clamp matcher captures initializer, argument, destination, and
  print storage indices. Neither assumes declaration order. The pass emits
  ordinary named/import relocations and declines unsupported bodies before
  opening output. Its 5,877-byte image leaves 2,315 bytes free in the 8 KiB
  execution window.
- `tools/build_actc_overlay_emit_native_real_postfix_object.sh` builds
  `ACTC_OVLL.BIN`, pass id `21`. It consumes bounded postfix REAL operations
  for one module-only `MAIN` or up to two bounded two-REAL-parameter functions,
  and emits ordinary machine/data/export/import,
  relocation, line, and variable records. The function form uses caller-pushed
  argument pointers, reverse-bound static parameter cells, an A/X result
  pointer, and bounded all-REAL local storage with DBG1 local records. `MAIN`
  may call either function, and either declaration direction may assign the
  other function's result, feed it directly to a supported intrinsic return
  tree, or use bounded calls as arguments to another such call while the graph
  remains acyclic. Each function-to-function edge saves caller parameters,
  locals, and live temporaries on the hardware stack, stages the A/X result,
  then restores the caller cells. Self and mutual cycles are hard errors; the
  pass remains explicitly nonrecursive and has no control flow. Its private
  four-byte temporaries and every export/relocation offset are 16-bit; an
  overlapping `__idata` aggregate anchors only source variables in DBG1. The
  6,124-byte image leaves 2,068 bytes free in the 8 KiB execution window.
- `tools/build_actc_overlay_emit_native_real_postfix_control_object.sh` builds
  `ACTC_OVLM.BIN`, pass id `22`, from the shared pass-L emitter with control
  lowering enabled. It only claims programs containing function control and
  supports one nonnested `IF`/`ELSE` per REAL function followed by a terminal
  return. Comparisons call `rt_f_cmp`; long conditional branches relocate to
  ordinary internal `__rfN` false and `__reN` end code exports, avoiding an
  8-bit branch-span dependency. Sequential or nested controls, loops, early
  returns, and recursive/reentrant functions remain unsupported. Its 6,998-byte
  image leaves 1,194 bytes free under a dedicated 1 KiB capacity gate, while
  pass L retains its 2 KiB reserve.
- `tools/build_actc_overlay_emit_native_real_postfix_multi_control_object.sh`
  builds `ACTC_OVLN.BIN`, pass id `23`, from a distinct configuration of the
  shared emitter. It claims only a supported program in which at least one REAL
  function contains a second conditional, and permits at most two controls per
  function either sequentially or nested to depth two. Independent `__rfNN`
  and `__reNN` exports keep each long branch fully relocatable. The 7,120-byte
  image leaves 1,072 bytes free under a dedicated 1 KiB gate; passes L and M
  remain byte-identical to their prior builds.
- `tools/build_actc_overlay_emit_native_real_postfix_extended_control_object.sh`
  builds `ACTC_OVLO.BIN`, pass id `24`, from the same emitter with four
  power-of-two control slots per REAL function. It claims only when a supported
  function contains a third conditional, permits at most four controls and
  nesting depth four, and emits independent `__rfNN`/`__reNN` targets for every
  occupied slot. Its 7,123-byte image leaves 1,069 bytes free under the 1 KiB
  gate; passes L, M, and N remain byte-identical.
- `tools/build_actc_overlay_emit_native_real_postfix_early_return_object.sh`
  builds `ACTC_OVLP.BIN`, pass id `25`, from the four-control emitter with
  conditional early-return parsing enabled. It claims only when a supported
  REAL function returns from inside an open `IF`/`ELSE`, requires a terminal
  fallback return, and preserves ordinary `__rfNN`/`__reNN` relocation. Its
  7,147-byte image leaves 1,045 bytes free under the 1 KiB gate; passes L
  through O remain byte-identical.
- `tools/build_actc_overlay_emit_native_real_postfix_loop_object.sh` builds
  `ACTC_OVLQ.BIN`, pass id `26`, from the shared postfix emitter with loop and
  condition parsing enabled. It accepts up to four `DO ... UNTIL ... OD` or
  `WHILE ... DO ... OD` loops per supported REAL function and emits ordinary
  relocatable `__rbNN` back-edge plus `__rzNN` while-exit labels. Its 7,151-byte
  image leaves 1,041 bytes free under the 1 KiB gate; passes L through P remain
  byte-identical. Plain `DO`, loop `EXIT`, mixed loop/conditional nesting, and
  returns from inside a loop remain outside this bounded pass.
- `tools/build_actc_overlay_emit_native_real_postfix_loop_exit_object.sh`
  builds `ACTC_OVLR.BIN`, pass id `27`, from the same emitter with plain-loop
  and nearest-loop `EXIT` parsing enabled. It accepts up to four loops per
  supported REAL function, adds plain `DO ... OD`, decodes `EXIT`'s collector
  selector, and relocates each unconditional exit to the active loop's
  independent `__rzNN` target while preserving `__rbNN` back edges. Its
  7,334-byte image leaves 858 bytes free under a dedicated 768-byte gate;
  passes L through Q remain byte-identical. REAL-function `FOR`, mixed
  loop/conditional nesting, and returns from inside a loop remain outside this
  bounded pass.
- `tools/build_actc_overlay_emit_native_real_postfix_for_object.sh` builds
  `ACTC_OVLS.BIN`, pass id `28`, from the shared postfix emitter with only the
  bounded `FOR` specialization enabled. It accepts up to four nested or
  sequential local CARD-counter loops per supported REAL function within the
  shared 64-operation body/debug budget. Initial and final values are
  constants; the optional signed constant step must be nonzero. Inclusive
  unsigned bounds and carry-based overflow/underflow exits
  prevent wraparound from restarting the loop. Its 7,828-byte image leaves 364
  bytes free under a dedicated 256-byte gate; passes Q and R remain
  byte-identical. Named CARD bounds are handled by pass T below; general bound
  expressions, runtime steps, nested counter-to-REAL body expressions, mixed
  controls, and returns inside loops remain outside this pass.
- `tools/build_actc_overlay_emit_native_real_postfix_for_dynamic_object.sh`
  builds `ACTC_OVLT.BIN`, pass id `29`. It claims the same bounded function
  form only when at least one `FOR` initial or final bound is a named CARD. A
  named initial value is copied into the counter at loop entry; a named final
  value is copied into hidden four-byte storage before the recorded back edge,
  preserving once-only bound evaluation. The byte-identical nested-loop
  fixture exercises both forms and produces 7.0 twice. Its 8,147-byte image
  leaves 45 bytes free under a dedicated 32-byte gate; pass S remains
  byte-identical. General bound expressions, runtime steps, counter-to-REAL
  body expressions, mixed controls, and returns inside loops remain outside
  this pass.
- `tools/build_actc_overlay_emit_native_real_postfix_literal_object.sh` builds
  `ACTC_OVLU.BIN`, pass id `30`. It extends the bounded straight-line REAL
  function form to one- or two-REAL-parameter signatures and materializes
  folded binary32 constants from the existing two-word literal stream into
  hidden four-byte cells. It also claims public `DegToRad` and `RadToDeg`
  intrinsic calls and emits imports for their separately selected OBJ modules.
  The shared project-local angle-conversion fixture still emits three copies of
  binary32 pi (`DB 0F 49 40`) plus ordinary `RT_F_DIV`/`RT_F_MUL` imports. Its
  6,514-byte image leaves 1,678 bytes free under a dedicated 1,536-byte gate;
  passes L through T remain byte-identical. General decimal expressions and
  arbitrary signatures remain outside this pass.
- `tools/build_actc_overlay_emit_native_object.sh` builds
  `build/udos_tools/ACTC_OVL8.BIN`, pass id `8`. In addition to straight-line
  word expressions and integer IF/DO control flow, it owns two word FOR loop
  instances with once-only final/step staging, runtime step direction, zero-step
  exit, nearest-loop FOR EXIT, and 16-bit wrap termination. It also owns plain
  plain and post-test DO/EXIT when the body contains dynamic word arithmetic,
  including named backward and post-loop relocations. Its 6,719-byte image
  leaves 1,473 bytes free and retains a dedicated 1 KiB minimum reserve; the
  other emission overlays retain 2 KiB.
- `tools/build_actc_overlay_emit_native_real_object.sh` builds
  `build/udos_tools/ACTC_OVLA.BIN`, pass id `10`. The resident selector encodes
  pass filenames as one-character base-36 values, and this overlay owns native
  REAL bridge, REAL-to-INT, straight-line binary REAL print, unary
  `FAbs`/`FSqrt` print, and one-argument helper plus REAL print detection,
  machine records, relocations, and debug offsets. Its bounded two-REAL-
  parameter identity form captures caller, bind, destination, and named return
  storage independently, so either parameter can be returned. Its 7,418-byte
  image leaves 774 bytes free under the 768-byte reserve. It runs after integer
  passes 9 and 8 and before generic pass 5.
- `tools/build_actc_overlay_emit_native_real_control_object.sh` builds
  `build/udos_tools/ACTC_OVLB.BIN`, pass id `11`. It owns plain, ELSE, and
  two-level nested REAL comparisons plus simple and binary-update REAL
  `DO ... UNTIL` loops. It emits relocatable machine roots instead of leaving
  those compact bodies for ALINK to compile. The current 5,220-byte pass leaves
  2,972 bytes free in the 8 KiB execution window.
- In the normal production build that path is now mandatory rather than
  best-effort: resident module-header parsing and resident declaration
  collection are compiled out, the build emits `ACTC_OVL1.BIN`,
  `ACTC_OVLI.BIN`, and `ACTC_OVL2.BIN` automatically, and all three overlays
  must be present beside `ACTC.PRG`.
- The overlay context includes a resident `load next source window` callback.
  `ACTC_OVL2.BIN` uses it to page source windows after the current committed
  window is consumed, while keeping a 24-bit source mark and a per-window
  remaining counter. This proves declaration scans can continue after the
  current `1280` byte production source window, and overlay staging now stays
  below the reserved-bank metadata slabs instead of colliding with source staged at
  `$010000+`. The target-side executable-relative overlay load path is now
  covered by release/VICE proofs, so the default build enables
  `ACTC_USE_DECL_OVERLAY=1`.
- The overlay context also exposes resident SourceReader peek/consume callbacks
  for body-collect source scans, keeping `ACTC_OVL6.BIN` from owning raw source
  pointer reads.
- The focused REU source-cache harness now also runs with declaration overlay
  collection by default. The wrap-edge cases that had blocked it are fixed in
  `ACTC_OVL2.BIN`.

Every ACTC pass has the same hard `$A000-$BFFF` execution window (8,192 bytes).
The driver clears LORAM in `$0001` before calling overlay code and restores the
previous memory configuration after the pass returns. UDOS owns live resident
state at `$C000` and above, so no pass code or scratch may cross that boundary.
Mutable pass state shares `$8000-$9DFF`; production and fallback ACTC builds are
guarded to end below `$8000`. The linker reserves `$9E00-$9FFF` from pass BSS;
ASMBLOCK emission uses `$9E00` for its page buffer, `$9F00` for its label index,
and `$9F10+` for scratch. Tool ABI calls preserve that low-memory state while
resident UDOS services execute.

## Initial Pass Split

1. `actc_p0_load`: validate project/module and stage source.
2. `actc_p1_decls`: collect module variables, procedure exports, params, and locals.
3. `actc_p2_body`: lower procedure bodies into REU-backed `body_ops`. Current
   production state: implemented in `ACTC_OVL6.BIN`.
4. `actc_p3_imports`: detect runtime imports and unresolved externals. Current
   production state: runtime-import detection is in `ACTC_OVL4.BIN`; this pass
   also assembles each ASMBLOCK or encodes each raw code block into a private
   page in reserved REU bank `$FF`, within `$FF0000-$FF0EFF`. Import flags are
   derived from parsed body operations, so assembly text and comments are
   opaque to Action helper selection. Unresolved
   external discovery still happens during body lowering, behind a dedicated
   body-overlay resolver seam and isolated unresolved-external helper. The gated
   `ACTC_PREALLOCATE_BODY_EXTERNALS=1` proof preallocates body externals:
   plain-call externals, simple nested call-argument externals in plain calls
   including call names inside grouped/arithmetic/nested-call arguments, and
   simple assignment/return call expressions, assignment/return boolean
   call-expression chains, the first REAL
   plain positive/signed word assignment helper, simple
   `REAL(wordExpr)`/`REAL(signedWordExpr)`/`REAL(wordVar)` assignment
   conversion imports, simple
   `INT(realVar)` word-assignment and runtime-expression conversion imports,
   simple flat-argument call expression imports from word assignments and
   return expressions, simple
   REAL copy/direct word-bridge assignment imports, simple
   `PrintR`/`PrintRE(realVar)` `rt_print_f` imports, simple
   `PrintI`/`PrintIE` call-expression imports with simple nested call,
   direct SID/GFX/sprite helper calls including remaining SID/sprite controls,
   GFX copy/bitmap helpers, zero-argument runtime helpers, and
   variable-argument runtime helpers,
   DBF helper assignments and close calls,
   joystick/mouse input result assignments feeding SID/GFX helper arguments,
   boolean-call, and multi-call arithmetic arguments, simple
   `FABS(realVar)`/`FSQRT(realVar)` assignment runtime imports, and simple
   `realVar (+|-|*|/) realVar` assignment runtime imports, plus simple
   `IF realVar cmp realVar THEN`, `WHILE realVar cmp realVar DO`, and
   `UNTIL realVar cmp realVar` `rt_f_cmp` imports, plus simple boolean call
   conditions, simple `AND`/`OR` call-condition chains, `NOT` call conditions,
   grouped boolean call-condition expressions, call-term comparisons, and
   boolean chains of call-term comparisons with simple nested call arguments for
   `IF`, `WHILE`, and `UNTIL`, before body lowering while preserving existing
   `uN` output. The
   proof scanner also guards language print statements before generic
   `Symbol(...)` call resolution, so `PrintI`/`PrintIE` do not become bogus
   unresolved externals. A second gated flag,
   `ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY=1`, now routes a first
   overlay-hosted preallocation pass through `ACTC_OVL7.BIN` for top-level
   plain-call external discovery, nested call-name discovery inside
   plain-call arguments, simple assignment and return expression
   call-name discovery, and simple `PrintI`/`PrintIE` argument
   call-name discovery, plus simple `IF`/`WHILE`/`UNTIL` condition
   call-expression discovery, real unary assignment runtime imports for
   `FABS(realVar)`/`FSQRT(realVar)`, real binary assignment runtime imports
   for `realVar (+|-|*|/) realVar`, real copy and word-bridge assignment
   imports, plain and explicit positive/signed REAL numeric assignment
   imports, explicit `REAL(wordVar)` bridge conversion imports, simple
   `INT(realVar)` word-assignment imports, `PrintR`/`PrintRE` real variable,
   explicit real conversion, numeric real conversion, unary real operator, and
   binary real operator expression imports including `rt_print_f`, richer
   `IF`/`WHILE`/`UNTIL` real condition operand imports for `REAL(...)`,
   `FABS(...)`, `FSQRT(...)`, `realVar (+|-|*|/) realVar`, and bare real vars
   through `rt_f_cmp`, and table-driven SID/GFX/sprite/input/DBF helper family
   runtime imports. The explicit overlay-preallocation gate now covers the
   complete joystick/mouse input helper family from `INPUT1.ACT`, including
   direct `IF`/`WHILE`/`UNTIL` condition references while preserving the same
   resident resolver seam,
   builtin runtime table handoff, reserved-keyword filtering, and `uN`
   object-code output.
5. `actc_p4_layout`: compute proc sizes, offsets, and literal offsets. Current
   production state: implemented in `ACTC_OVL3.BIN`.
6. `actc_p5_emit`: stream `OBJ1` object output. Current production state:
   generic emission is implemented in `ACTC_OVL5.BIN`; single-procedure native
   integer machine emission, including word FOR loops, FOR EXIT, and dynamic
   arithmetic plain/post-test DO/EXIT, is isolated in `ACTC_OVL8.BIN`;
   multi-procedure native local-call/control-flow plus single-procedure plain
   DO, WHILE, dynamic WHILE arithmetic, DO/WHILE EXIT, and ASMBLOCK byte and
   relocation emission is isolated in `ACTC_OVL9.BIN`;
   native REAL bridge, conversion, binary arithmetic, unary helper, and
   helper-prefixed REAL print emission are isolated in base-36 pass
   `ACTC_OVLA.BIN`; REAL IF/ELSE/nested-IF and REAL `DO ... UNTIL` emission is
   isolated in `ACTC_OVLB.BIN`; REAL `WHILE` emission is isolated in
   `ACTC_OVLC.BIN`; runtime condition, runtime sequence, and nested-readback
   machine emission are isolated in `ACTC_OVLD.BIN`, `ACTC_OVLE.BIN`, and
   `ACTC_OVLF.BIN`; one-word byte-in-A and word-in-X/Y runtime calls nested in
   integer control are isolated in `ACTC_OVLG.BIN`; units combining that control
   with ASMBLOCK, `=*(...)`, or numeric absolute-address declarations are
   isolated in `ACTC_OVLH.BIN`; compact fixed-address-only units first use
   `ACTC_OVLJ.BIN`; the bounded two-REAL-parameter finite comparison/select
   function first uses `ACTC_OVLK.BIN`; nested straight-line REAL postfix trees
   first use `ACTC_OVLL.BIN`; one bounded REAL-function `IF`/`ELSE` first uses
   `ACTC_OVLM.BIN`; two sequential or depth-two nested controls first use
   `ACTC_OVLN.BIN`; three or four controls and depth-three/four nesting first
   use `ACTC_OVLO.BIN`; returns inside those bounded controls first use
   `ACTC_OVLP.BIN`; bounded REAL-function post-test and pre-test loops first use
   `ACTC_OVLQ.BIN`; plain REAL-function loops and nearest-loop `EXIT` first use
   `ACTC_OVLR.BIN`; constant-bound CARD-counter REAL-function `FOR` loops first
   use `ACTC_OVLS.BIN`; named CARD initial/final bounds first use
   `ACTC_OVLT.BIN`; folded REAL literals and one-parameter REAL functions first
   use `ACTC_OVLU.BIN`.
   Native passes return explicit not-applicable status before writing output so
   the resident driver can try the next emitter without rolling back a partial
   object.

ABI v5 retains v4's fixed-address routine metadata and formatter callbacks and
adds the resident binary32 `REAL CONST` evaluator, producing one contiguous
231-byte context. Native emitters continue to share the resident decimal-word
and uppercase-hex-byte formatters rather than duplicate those routines. Body
collection and preallocation both include one shared token-driven positive-word
parser source. The generated overlays each carry the cold parser code they
execute, while resident ACTC retains only token ownership; this keeps the
compiler below the UDOS resident floor without maintaining two parser
implementations.

## Why This Matters

The current REU table work increases the immediate development window, but a
full-feature compiler still should not require every parser and lowering routine
to be resident at the same time. Overlay passes let compiler features grow by
adding pass-specific code modules instead of consuming one fixed `$0900-$9FFF`
tool image.

## Next Engineering Steps

1. Keep the remaining ACTC metadata slab REU-backed and covered by capacity
   tests.
2. Continue splitting unresolved-external discovery and other follow-on body
   helpers out of resident ACTC code. The first top-level plain-call branch,
   its nested plain-call argument scan, and simple assignment/return expression
   print-statement, and condition call scans now have a gated
   `ACTC_OVL7.BIN` pass, and helper-family runtime imports are resolved through
   the overlay-owned builtin table. Simple real unary assignment imports are
   also handled there now, as are simple real binary and word-bridge assignment
   imports plus plain/explicit REAL numeric conversions, explicit
   `REAL(wordVar)`, `INT(realVar)` conversion imports, richer real
   `PrintR`/`PrintRE` expression imports, and richer real condition expression
   imports. Overlay preallocation is now enabled in the production build by
   default; next keep expanding overlay-owned body lowering and preallocation
   coverage so later language growth does not refill the resident tool image.
3. Keep release packaging for every overlay binary next to `ACTC.PRG`.
4. Keep `ACTC -> ALINK -> BIN/MAIN.PRG` as the regression gate while each pass moves.
