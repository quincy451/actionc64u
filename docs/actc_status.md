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
- [x] `IF ... THEN ... FI`
- [x] `IF ... THEN ... ELSE ... FI`
- [x] nested `IF ... THEN ... FI`
- [x] nested `IF ... THEN ... ELSE ... FI`

## Current Widening Work

- [ ] broader runtime-emitted integer expression chains beyond the already-proven narrow path
- [ ] larger statement/control-flow surface beyond the current single-branch `IF` path
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
- [x] arithmetic/comparison conditions inside `IF ... THEN ... ELSE ... FI`:
  `IF 2 + 3 * 4 > 10 THEN ... ELSE ... FI`
- [x] multiple local procedures in one module:
  `PROC HELLO() ...` and `PROC MAIN() ...`
- [x] local user procedure calls:
  `HELLO()`
- [x] local user procedure calls inside `IF ... THEN ... ELSE ... FI`:
  `IF 1 = 1 THEN HELLO() ELSE BYE() FI`
- [x] arithmetic/comparison-driven local procedure calls inside `IF ... THEN ... ELSE ... FI`:
  `IF 2 + 3 * 4 > 10 THEN HELLO() ELSE BYE() FI`
- [x] nested local procedure calls inside control flow:
  `IF 1 = 1 THEN IF 2 + 3 * 4 > 10 THEN HELLO() ELSE BYE() FI ELSE OUTER() FI`
- [x] unresolved external calls inside arithmetic/comparison-driven `IF ... THEN ... ELSE ... FI`:
  `IF 2 + 3 * 4 > 10 THEN W() ELSE ... FI`
- [x] nested unresolved external calls inside control flow:
  `IF 1 = 1 THEN IF 2 + 3 * 4 > 10 THEN W() ELSE ... FI ELSE OUTER() FI`
- [x] transitive unresolved-external emission across multiple modules:
  `MAIN -> W -> Z`
- [x] transitive unresolved-external calls inside arithmetic/comparison-driven control flow:
  `IF 2 + 3 * 4 > 10 THEN W() ...` with `W -> Z`
- [x] multiple sibling unresolved-external calls from one procedure:
  `W()` and `Z()`
- [x] child-module sibling unresolved-external calls:
  `W()` with `Z()` and `Q()`
- [x] local procedure calls mixed with transitive unresolved externals inside branch control flow:
  `IF ... THEN LOCAL() W() ...` with `W -> Z`
- [x] single-branch control flow:
  `IF 1 = 0 THEN ... FI` and `IF 1 = 1 THEN ... FI`
- [x] `ELSE` control flow:
  `IF 1 = 0 THEN ... ELSE ... FI`
- [x] nested control flow:
  `IF 1 = 1 THEN IF 1 = 0 THEN ... FI ... FI`
- [x] nested `ELSE` control flow:
  `IF 1 = 1 THEN IF 1 = 0 THEN ... ELSE ... FI ELSE ... FI`
- [x] current widened control-flow object emission:
  `b p0p1qhe0vp2p3qhe1ve2r`
- [x] current widened `ELSE` object emission:
  `b p0p1qhe0we1ve2r`
- [x] current widened nested-control-flow object emission:
  `b p0p1qhp2p3qhe0ve1ve2r`
- [x] current widened nested-`ELSE` object emission:
  `b p0p1qhp2p3qhe0we1vwe2ve3r`
- [x] current widened additive object emission:
  `b e0u0p0p1ap2myp3p4mp5azr`
- [x] current widened precedence object emission:
  `b p0p1ayi2r`
- [x] current widened arithmetic/comparison object emission:
  `b p0p1azi2p3p4qzp5p6gzu0r`
- [x] current widened arithmetic/comparison `IF/ELSE` object emission:
  `b p0p1ap2ghe0we1ve2r`
- [x] current widened branch-call object emission:
  `b p0p1qhc0wc1ve2r`
- [x] current widened arithmetic/comparison branch-call object emission:
  `b p0p1ap2ghc0wc1ve2r`
- [x] current widened nested branch-call object emission:
  `b p0p1qhp2p3ap4ghc0wc1vwc2ve3r`
- [x] current widened branch-external object emission:
  `b p0p1ap2ghu0we0ve1r`
- [x] current widened nested branch-external object emission:
  `b p0p1qhp2p3ap4ghu0we1vwc0ve2r`
- [x] current widened transitive-external root object emission:
  `b e0u0e1r`
- [x] current widened transitive-branch-external root object emission:
  `b p0p1ap2ghe0u0we1ve2r`
- [x] current widened sibling-external root object emission:
  `b e0u0u1e1r`
- [x] current widened child-sibling-external object emission:
  `b e0u0u1r`
- [x] current widened branch-local + transitive-external object emission:
  `b p0p1ap2ghc0u0we1ve2r`
- [x] harness proof exists through:
  `ACTC -> ALINK -> AVMRUN`
- [x] current harness runtime output for that widened slice:
  `HELLO`, `TOOL7`, `5459`
- [x] current harness runtime output for the precedence slice:
  `145`
- [x] current harness runtime output for the arithmetic/comparison slice:
  `14`, `5`, `1`, `1`, `TOOL7`
- [x] current harness runtime output for the arithmetic/comparison `IF/ELSE` slice:
  `YES`, `DONE`
- [x] current harness runtime output for the branch-call slice:
  `HELLO`, `DONE`
- [x] current harness runtime output for the arithmetic/comparison branch-call slice:
  `HELLO`, `DONE`
- [x] current harness runtime output for the nested branch-call slice:
  `HELLO`, `DONE`
- [x] current harness runtime output for the branch-external slice:
  `TOOL7`, `DONE`
- [x] current harness runtime output for the nested branch-external slice:
  `TOOL7`, `DONE`
- [x] current harness runtime output for the transitive-external slice:
  `START`, `MID`, `END`, `DONE`
- [x] current harness runtime output for the transitive-branch-external slice:
  `START`, `MID`, `END`, `DONE`
- [x] current harness runtime output for the sibling-external slice:
  `START`, `MID1`, `MID2`, `DONE`
- [x] current harness runtime output for the child-sibling-external slice:
  `START`, `MID`, `END1`, `END2`, `DONE`
- [x] current harness runtime output for the branch-local + transitive-external slice:
  `LOCAL`, `MID`, `END`, `DONE`
- [x] current harness runtime output for the local-procedure slice:
  `ONE`, `TWO`
- [x] current harness runtime output for the `IF` slice:
  `YES`, `DONE`
- [x] current harness runtime output for the `ELSE` slice:
  `GOOD`, `DONE`
- [x] current harness runtime output for the nested-`IF` slice:
  `INNERDONE`, `OUTERDONE`
- [x] current harness runtime output for the nested-`ELSE` slice:
  `GOOD1`, `DONE`

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
