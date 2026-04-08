# `ACTC` Status

Current as of `2026-04-08`.

This file is a focused ledger for the UDOS-native `ACTC.PRG` tool.
It is narrower and easier to update than the broad [action_matrix.md](/mnt/c/test/action/actionc64u/docs/action_matrix.md).

## Proven On The Committed Baseline

- [x] Launches from a UDOS Action workspace as `ACTC.PRG <module>`
- [x] Requires a loaded project and a tracked manifest entry
- [x] Reads `SRC/<NAME>.ACT` for the requested module
- [x] Validates the source `MODULE` header against the requested module name
- [x] Emits deterministic `AVO1` object text into `OBJ/<NAME>.AVO`
- [x] Emits compiler-owned export names plus offset/size metadata
- [x] Emits `body_ops`
- [x] Emits a minimal payload skeleton plus `payload_bytes`
- [x] Emits current inferred runtime-import lines
- [x] Supports the current narrow decimal print-expression subset for object emission
- [x] Integrated narrow proof exists through `ACTC -> ALINK -> AVMRUN`

## Proven Narrow Source Surface

- [x] `MODULE <name>`
- [x] top-level `PROC` discovery for current object emission flow
- [x] `PrintI(...)`
- [x] `PrintIE(...)`
- [x] inline-space tolerant decimal arithmetic for the current narrow path
- [x] `+`
- [x] `-`
- [x] `*`
- [x] `/`
- [x] parenthesized grouping in the current narrow expression path
- [x] simple comparisons:
  `=`, `<>`, `<`, `<=`, `>`, `>=`

## Current Widening Work

- [ ] broader runtime-emitted integer expression chains beyond the already-proven narrow path
- [ ] larger statement/control-flow surface
- [ ] broader procedure/function surface
- [ ] full historical ACTION! source compatibility

## Harness-Proven Current Widening Line

- [x] additive integer print chains:
  `PrintI(50 + 7 - 3)`
- [x] additive integer print-expression chains in `PrintIE(...)`:
  `PrintIE(60 - 3 + 2)`
- [x] mixed-precedence integer print chains:
  `PrintI(2 + 3 * 4)`
- [x] parenthesized integer print-expression chains:
  `PrintIE((20 - 5) / 3)`
- [x] arithmetic/comparison mixes in print-expression chains:
  `PrintIE((2 + 3) * 4 = 20)` and `PrintIE((2 + 3 * 4) > 10)`
- [x] multiple local procedures in one module:
  `PROC HELLO() ...` and `PROC MAIN() ...`
- [x] local user procedure calls:
  `HELLO()`
- [x] current widened additive object emission:
  `b e0u0p0p1ap2myp3p4mp5azr`
- [x] current widened precedence object emission:
  `b p0p1ayi2r`
- [x] current widened arithmetic/comparison object emission:
  `b p0p1azi2p3p4qzp5p6gzu0r`
- [x] harness proof exists through:
  `ACTC -> ALINK -> AVMRUN`
- [x] current harness runtime output for that widened slice:
  `HELLO`, `TOOL7`, `5459`
- [x] current harness runtime output for the precedence slice:
  `145`
- [x] current harness runtime output for the arithmetic/comparison slice:
  `14`, `5`, `1`, `1`, `TOOL7`
- [x] current harness runtime output for the local-procedure slice:
  `ONE`, `TWO`

## Current Biggest Blockers

- Resident/VICE tool-service ABI instability.
  The harness now proves the current additive compiler logic cleanly. The main blocker to proving the same slice under VICE is still the resident-facing load/save path, not the compiler core.
- Probe stability.
  VICE automation is good enough to prove narrow slices, but it still costs time whenever a dirty line perturbs boot, mount, or prompt timing.
- Dirty-line versus committed-line drift.
  The committed narrow compiler/linker/runtime path is real. The active work is widening it without reintroducing the older ABI sensitivity.

## What Is Not Claimed Here

- full ACTION! compiler coverage
- full runtime lowering for arbitrary expressions/statements
- stable proof for every currently dirty widening experiment
