# ACTC REU Overlay Pass Plan

Current as of `2026-04-23`.

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

The first artifacts are intentionally small and raw:

- `src/tools_udos/actc/actc_overlay_abi.inc` defines overlay ABI version `1`.
- `src/tools_udos/actc/actc_overlay_noop.asm` builds a no-op pass.
- `tools/build_actc_overlay_noop.sh` emits `build/udos_tools/ACTC_OVL0.BIN`.
- `src/tools_udos/actc/actc_overlay_source_header.asm` builds the first
  source-aware pass.
- `tools/build_actc_overlay_source_header.sh` emits
  `build/udos_tools/ACTC_OVL1.BIN`.
- `src/tools_udos/actc/actc_overlay_decl_counts.asm` builds the first
  declaration-scanning pass.
- `tools/build_actc_overlay_decl_counts.sh` emits
  `build/udos_tools/ACTC_OVL2.BIN`.
- The workspace exporter and UDOS release Makefile include `ACTC_OVL0.BIN`
  through `ACTC_OVL7.BIN` next to `ACTC.PRG`, so pass files are present when
  the scheduler runs from an exported or release image.
- `tests/test_actc_overlay.py` proves the `ACOV` header, ABI version, pass id,
  `$A000` execution base, encoded byte length, no-op return sequence, and the
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
- `actc_overlay_run_pass` in `ACTC.PRG` accepts a pass id in `A`, finds a pass
  descriptor, stages that file into REU at `$008000`, copies it to `$A000`, passes
  a context block to the overlay in `X/Y`, banks out BASIC ROM for the call,
  executes it, and restores the previous memory configuration.
- `ACTC.PRG` now has a multi-stage compile-path overlay handoff. When built with
  `ACTC_USE_SOURCE_HEADER_OVERLAY=1` and `ACTC_USE_DECL_OVERLAY=1`, it calls
  `ACTC_OVL1.BIN` for module-header validation and then `ACTC_OVL2.BIN` for
  declaration scanning. The current production path also stages `ACTC_OVL6.BIN`
  for proc-body lowering, `ACTC_OVL4.BIN` for runtime-import detection,
  `ACTC_OVL3.BIN` for payload layout, `ACTC_OVL5.BIN` for streamed object
  emission, and `ACTC_OVL7.BIN` for overlay-hosted body external
  preallocation; on
  success, later compiler phases consume the overlay-written REU metadata.
  Overlay staging uses the executable-relative tool ABI path prefix, so
  `!ACTC_OVL1.BIN` through `!ACTC_OVL7.BIN` resolve beside the launched
  `ACTC.PRG`.
- `tools/build_actc_overlay_body_collect.sh` now also builds
  `build/udos_tools/ACTC_OVL6.BIN`, pass id `6`, which is the current
  proc-body lowering overlay. `tools/build_actc_overlay_body_preallocate.sh`
  builds `build/udos_tools/ACTC_OVL7.BIN`, pass id `7`, which owns the
  overlay-hosted preallocation scanner. Both are packaged beside `ACTC.PRG` and
  enabled in the default production build.
- In the normal production build that path is now mandatory rather than
  best-effort: resident module-header parsing and resident declaration
  collection are compiled out, the build emits `ACTC_OVL1.BIN` and
  `ACTC_OVL2.BIN` automatically, and both overlays must be present beside
  `ACTC.PRG`.
- The overlay context includes a resident `load next source window` callback.
  `ACTC_OVL2.BIN` uses it to page source windows after the current committed
  window is consumed, while keeping a 24-bit source mark and a per-window
  remaining counter. This proves declaration scans can continue after the
  current `1280` byte production source window, and overlay staging now stays
  below the bank-0 metadata slabs instead of colliding with source staged at
  `$010000+`. The target-side executable-relative overlay load path is now
  covered by release/VICE proofs, so the default build enables
  `ACTC_USE_DECL_OVERLAY=1`.
- The overlay context also exposes resident SourceReader peek/consume callbacks
  for body-collect source scans, keeping `ACTC_OVL6.BIN` from owning raw source
  pointer reads.
- The focused REU source-cache harness now also runs with declaration overlay
  collection by default. The wrap-edge cases that had blocked it are fixed in
  `ACTC_OVL2.BIN`.

The overlay execution window is `$A000-$BFFF`, which means the ACTC resident
driver must clear LORAM in `$0001` before calling overlay code and restore the
previous memory configuration after the pass returns. This keeps the existing
`$0900-$9FFF` tool window available while opening an 8 KiB pass-code window
under BASIC ROM.

## Initial Pass Split

1. `actc_p0_load`: validate project/module and stage source.
2. `actc_p1_decls`: collect module variables, procedure exports, params, and locals.
3. `actc_p2_body`: lower procedure bodies into REU-backed `body_ops`. Current
   production state: implemented in `ACTC_OVL6.BIN`.
4. `actc_p3_imports`: detect runtime imports and unresolved externals. Current
   production state: runtime-import detection is in `ACTC_OVL4.BIN`; unresolved
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
   implemented in `ACTC_OVL5.BIN`.

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
