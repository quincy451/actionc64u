# `ALINK` Status

Current as of `2026-04-08`.

This file is a focused ledger for the UDOS-native `ALINK.PRG` tool.
It tracks the real linker slice separately from the broader [action_matrix.md](/mnt/c/test/action/actionc64u/docs/action_matrix.md).

## Proven On The Committed Baseline

- [x] Launches from a UDOS Action workspace as `ALINK.PRG <module>`
- [x] Loads deterministic `AVO1` object stubs from `OBJ/`
- [x] Parses export metadata
- [x] Parses `body_ops`
- [x] Parses unresolved external symbol lines
- [x] Parses integer literal pools
- [x] Parses string literal pools
- [x] Uses compiler-emitted export sizes to recover procedure boundaries
- [x] Builds a live-set from the requested module entry
- [x] Resolves the current narrow external-object closure by loading child objects
- [x] Carries child-object int/string pools into the linked image
- [x] Emits direct binary `AVM1` to `BIN/<NAME>.AVM`
- [x] Narrow exact-byte proof exists for the emitted image
- [x] Narrow integrated proof exists through `ALINK -> AVMRUN`
- [x] Narrow integrated proof also exists through `ACTC -> ALINK -> AVMRUN`

## Proven Linker Behaviors

- [x] dead-strip on the current narrow local/export graph
- [x] child object loading for the already-proven narrow object shape
- [x] final binary target path `BIN/<NAME>.AVM`
- [x] direct binary output instead of text or planning-report output

## Current Widening Work

- [ ] broader object graph / external-resolution surface
- [ ] more robust child-object load path under the current dirty VICE debug line
- [ ] more robust final save/return path under the current dirty VICE debug line
- [ ] larger body-op surface than the current arithmetic/procedure/`IF` slice
- [ ] full historical dead-strip/link behavior

## Harness-Proven Current Widening Line

- [x] loads widened `ACTC` output for:
  `PrintI(50 + 7 - 3)` and `PrintIE(60 - 3 + 2)`
- [x] also loads mixed-precedence / parenthesized `ACTC` output for:
  `PrintI(2 + 3 * 4)` and `PrintIE((20 - 5) / 3)`
- [x] also loads arithmetic/comparison mixed `ACTC` output for:
  `PrintIE((2 + 3) * 4 = 20)` and `PrintIE((2 + 3 * 4) > 10)`
- [x] also loads arithmetic/comparison `IF/ELSE` `ACTC` output for:
  `IF 2 + 3 * 4 > 10 THEN ... ELSE ... FI`
- [x] also loads multi-procedure local-call `ACTC` output for:
  `PROC HELLO() ...` and `HELLO()`
- [x] also loads branch-local procedure-call `ACTC` output for:
  `IF 1 = 1 THEN HELLO() ELSE BYE() FI`
- [x] also loads arithmetic/comparison branch-local procedure-call `ACTC` output for:
  `IF 2 + 3 * 4 > 10 THEN HELLO() ELSE BYE() FI`
- [x] also loads nested branch-local procedure-call `ACTC` output for:
  `IF 1 = 1 THEN IF 2 + 3 * 4 > 10 THEN HELLO() ELSE BYE() FI ELSE OUTER() FI`
- [x] also loads branch-local unresolved-external `ACTC` output for:
  `IF 2 + 3 * 4 > 10 THEN W() ELSE ... FI`
- [x] also loads nested branch-local unresolved-external `ACTC` output for:
  `IF 1 = 1 THEN IF 2 + 3 * 4 > 10 THEN W() ELSE ... FI ELSE OUTER() FI`
- [x] also loads transitive unresolved-external `ACTC` output across modules:
  `MAIN -> W -> Z`
- [x] also loads transitive unresolved-external control-flow `ACTC` output:
  `IF 2 + 3 * 4 > 10 THEN W() ...` with `W -> Z`
- [x] also loads sibling unresolved-external `ACTC` output from one procedure:
  `W()` and `Z()`
- [x] also loads child-module sibling unresolved-external `ACTC` output:
  `W()` with `Z()` and `Q()`
- [x] also loads branch-local call + transitive unresolved-external `ACTC` output:
  `IF ... THEN LOCAL() W() ...` with `W -> Z`
- [x] also loads single-branch `IF` control-flow `ACTC` output for:
  `IF 1 = 0 THEN ... FI` and `IF 1 = 1 THEN ... FI`
- [x] also loads `ELSE` control-flow `ACTC` output for:
  `IF 1 = 0 THEN ... ELSE ... FI`
- [x] also loads nested `IF` control-flow `ACTC` output for:
  `IF 1 = 1 THEN IF 1 = 0 THEN ... FI ... FI`
- [x] also loads nested `ELSE` control-flow `ACTC` output for:
  `IF 1 = 1 THEN IF 1 = 0 THEN ... ELSE ... FI ELSE ... FI`
- [x] resolves the current widened child-object closure including `OBJ/W.AVO`
- [x] resolves the current widened transitive child-object closure including `OBJ/W.AVO` and `OBJ/Z.AVO`
- [x] resolves sibling child objects from the root:
  `OBJ/W.AVO` and `OBJ/Z.AVO`
- [x] resolves sibling child objects from a child module:
  `OBJ/Z.AVO` and `OBJ/Q.AVO`
- [x] emits a widened `BIN/MAIN.AVM` of `76` bytes on that slice
- [x] emits a precedence-slice `BIN/MAIN.AVM` of `31` bytes
- [x] emits an arithmetic/comparison slice `BIN/MAIN.AVM` of `72` bytes
- [x] emits an arithmetic/comparison `IF/ELSE` slice `BIN/MAIN.AVM` of `62` bytes
- [x] emits a branch-call `BIN/MAIN.AVM` of `69` bytes
- [x] emits an arithmetic/comparison branch-call `BIN/MAIN.AVM` of `73` bytes
- [x] emits a nested branch-call `BIN/MAIN.AVM` of `102` bytes
- [x] emits a branch-external `BIN/MAIN.AVM` of `74` bytes
- [x] emits a nested branch-external `BIN/MAIN.AVM` of `104` bytes
- [x] emits a transitive-external `BIN/MAIN.AVM` of `66` bytes
- [x] emits a transitive-branch-external `BIN/MAIN.AVM` of `93` bytes
- [x] emits a sibling-external `BIN/MAIN.AVM` of `68` bytes
- [x] emits a child-sibling-external `BIN/MAIN.AVM` of `82` bytes
- [x] emits a branch-local + transitive-external `BIN/MAIN.AVM` of `97` bytes
- [x] emits an `IF` slice `BIN/MAIN.AVM` of `65` bytes
- [x] emits an `ELSE` slice `BIN/MAIN.AVM` of `60` bytes
- [x] emits a nested-`IF` slice `BIN/MAIN.AVM` of `77` bytes
- [x] emits a nested-`ELSE` slice `BIN/MAIN.AVM` of `86` bytes
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

- Call-depth / return-context sensitivity around tool ABI file loads and saves.
  This is still the biggest blocker on the VICE-facing path. The harness now proves the widened linker logic itself on the current additive slice.
- Proof friction from VICE automation.
  This is real, but secondary. It slows narrowing because some dirty lines perturb shell launch, mount timing, or prompt detection before the actual linker boundary is reached.
- Lack of a small, stable comparator for every dirty line.
  When the control path itself gets perturbed, it becomes harder to make honest claims about whether the next failure is in `ALINK` or in the shared tool/service context.

## How Current Debugging Relates To The Linker

The current debugging is directly about core linker function, not side work.

`ALINK` only becomes meaningfully functional when it can:

1. load the root object
2. load child objects for unresolved externals
3. build the final live image
4. save `BIN/<NAME>.AVM`
5. hand that image to `AVMRUN`

The active failures are in steps `2` and `4` on the widened dirty line, so the current work is still central linker work.

## What Is Not Claimed Here

- full ACTION! linker coverage
- full historical module/runtime graph support
- stability for every currently dirty widening experiment
