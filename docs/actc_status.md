# `ACTC` Status

Current as of `2026-04-09`.

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
- [x] explicit `RETURN`
- [x] `DO ... UNTIL ... OD`
- [x] local and unresolved-external calls inside `DO ... UNTIL ... OD`
- [x] `IF ... THEN ... ELSE ... FI` inside `DO ... UNTIL ... OD`
- [x] local branch calls inside `DO ... UNTIL ... OD`
- [x] unresolved-external branch calls inside `DO ... UNTIL ... OD`
- [x] nested `DO ... UNTIL ... OD`
- [x] local and unresolved-external calls inside nested `DO ... UNTIL ... OD`
- [x] `DO ... UNTIL ... OD` containing nested `WHILE ... DO ... OD`
- [x] `WHILE ... DO ... OD` containing nested `DO ... UNTIL ... OD`
- [x] mixed local/external and branch content across `DO`/`WHILE` mixed nesting

## Current Widening Work

- [ ] broader runtime-emitted integer expression chains beyond the already-proven narrow path
- [ ] larger statement/control-flow surface beyond the current `IF`/`ELSE`/`WHILE ... DO ... OD`/`DO ... UNTIL ... OD`/nested-loop/branch-combined path
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
- [x] repeated root unresolved-external reuse from multiple call sites:
  `W()`, `Z()`, `W()`
- [x] shared transitive unresolved-external reuse:
  `W -> Z` and `Q -> Z`
- [x] sibling unresolved-external calls inside arithmetic/comparison-driven control flow:
  `IF ... THEN W() Z() ...`
- [x] shared transitive unresolved-external calls inside arithmetic/comparison-driven control flow:
  `IF ... THEN W() Q() ...` with `W -> Z` and `Q -> Z`
- [x] single-branch control flow:
  `IF 1 = 0 THEN ... FI` and `IF 1 = 1 THEN ... FI`
- [x] `ELSE` control flow:
  `IF 1 = 0 THEN ... ELSE ... FI`
- [x] nested control flow:
  `IF 1 = 1 THEN IF 1 = 0 THEN ... FI ... FI`
- [x] nested `ELSE` control flow:
  `IF 1 = 1 THEN IF 1 = 0 THEN ... ELSE ... FI ELSE ... FI`
- [x] explicit early return inside current control-flow forms:
  `IF ... THEN RETURN FI`, `IF ... ELSE RETURN FI`, `DO ... RETURN UNTIL ... OD`, `WHILE ... RETURN OD`
- [x] explicit early return after local/external calls:
  `IF HELLO() RETURN FI`, `IF W() RETURN FI`, `WHILE HELLO() W() RETURN OD`
- [x] explicit early return with transitive external closure inside nested control flow:
  `IF ... THEN IF ... THEN W() RETURN FI ... FI` with `W -> Z`
- [x] explicit early return inside mixed nested loop/branch control flow:
  `DO IF ... THEN W() ELSE HELLO() FI RETURN UNTIL ... OD`
- [x] explicit early return inside nested loop forms with transitive externals:
  `WHILE ... DO DO W() RETURN UNTIL ... OD OD` with `W -> Z`
- [x] `DO ... UNTIL ... OD` loop control flow:
  `DO ... UNTIL 1 = 1 OD`
- [x] local and unresolved-external calls inside `DO ... UNTIL ... OD`:
  `DO HELLO() W() UNTIL 1 = 1 OD`
- [x] branch control flow inside `DO ... UNTIL ... OD`:
  `DO IF 2 + 3 * 4 > 10 THEN ... ELSE ... FI UNTIL 1 = 1 OD`
- [x] local branch calls inside `DO ... UNTIL ... OD`:
  `DO IF 2 + 3 * 4 > 10 THEN HELLO() ELSE BYE() FI UNTIL 1 = 1 OD`
- [x] unresolved-external branch calls inside `DO ... UNTIL ... OD`:
  `DO IF 2 + 3 * 4 > 10 THEN W() ELSE ... FI UNTIL 1 = 1 OD`
- [x] nested `DO ... UNTIL ... OD`:
  `DO ... DO ... UNTIL 1 = 1 OD UNTIL 1 = 1 OD`
- [x] local and unresolved-external calls inside nested `DO ... UNTIL ... OD`:
  `DO HELLO() DO W() UNTIL 1 = 1 OD UNTIL 1 = 1 OD`
- [x] nested `IF ... THEN ... ELSE ... FI` inside nested `DO ... UNTIL ... OD`:
  `DO IF ... THEN ... FI DO IF ... THEN ... ELSE ... FI UNTIL ... OD UNTIL ... OD`
- [x] mixed local/external branch calls inside nested `DO ... UNTIL ... OD`:
  `DO IF ... THEN W() ELSE ... FI DO IF ... THEN HELLO() ELSE ... FI UNTIL ... OD UNTIL ... OD`
- [x] top-tested `WHILE ... DO ... OD` with false entry condition:
  `WHILE 1 = 0 DO ... OD`
- [x] local and unresolved-external calls inside top-tested `WHILE ... DO ... OD`
- [x] `IF ... THEN ... ELSE ... FI` inside top-tested `WHILE ... DO ... OD`
- [x] local branch calls inside top-tested `WHILE ... DO ... OD`
- [x] unresolved-external branch calls inside top-tested `WHILE ... DO ... OD`
- [x] nested top-tested `WHILE ... DO ... OD`
- [x] local and unresolved-external calls inside nested top-tested `WHILE ... DO ... OD`
- [x] mixed local/external branch content inside nested top-tested `WHILE ... DO ... OD`
- [x] shared transitive unresolved-external reuse inside top-tested `WHILE ... DO ... OD`
- [x] compiler body-op stride widened to support the current nested-loop surface:
  `BODY_OPS_STRIDE = 48`
- [x] compiler integer literal pool widened for the current nested-loop + nested-branch surface:
  `INT_LITERAL_MAX = 10`
- [x] current widened control-flow object emission:
  `b p0p1qhe0vp2p3qhe1ve2r`
- [x] current widened `ELSE` object emission:
  `b p0p1qhe0we1ve2r`
- [x] current widened nested-control-flow object emission:
  `b p0p1qhp2p3qhe0ve1ve2r`
- [x] current widened nested-`ELSE` object emission:
  `b p0p1qhp2p3qhe0we1vwe2ve3r`
- [x] current widened `DO ... UNTIL ... OD` object emission:
  `b de0p0p1qtoe1r`
- [x] current widened call/external loop object emission:
  `b dc0u0p0p1qtoe1r`
- [x] current widened loop + branch object emission:
  `b dp0p1ap2ghe0we1vp3p4qtoe2r`
- [x] current widened loop + branch-call object emission:
  `b dp0p1ap2ghc0wc1vp3p4qtoe2r`
- [x] current widened loop + branch-external object emission:
  `b dp0p1ap2ghu0we0vp3p4qtoe1r`
- [x] current widened nested-loop object emission:
  `b de0de1p0p1qtop2p3qtoe2r`
- [x] current widened nested loop + call/external object emission:
  `b dc0du0p0p1qtop2p3qtoe1r`
- [x] current widened nested loop + nested-branch object emission:
  `b dp0p1ap2ghe0vdp3p4qhe1we2vp5p6qtop7p8qtoe3r`
- [x] current widened nested loop + mixed branch local/external object emission:
  `b dp0p1ap2ghu0we1vdp3p4qhc0we2vp5p6qtop7p8qtoe3r`
- [x] current widened `WHILE ... DO ... OD` object emission:
  `b dp0p1qfe0xe1r`
- [x] current widened `WHILE` + call/external object emission:
  `b dp0p1qfc0u0xe1r`
- [x] current widened `WHILE` + branch object emission:
  `b dp0p1qfp2p3ap4ghe0we1vxe2r`
- [x] current widened `WHILE` + branch-call object emission:
  `b dp0p1qfp2p3ap4ghc0wc1vxe2r`
- [x] current widened `WHILE` + branch-external object emission:
  `b dp0p1qfp2p3ap4ghu0we0vxe1r`
- [x] current widened nested `WHILE` object emission:
  `b dp0p1qfe0dp2p3qfe1xxe2r`
- [x] current widened nested `WHILE` + call/external object emission:
  `b dp0p1qfc0dp2p3qfu0xxe1r`
- [x] current widened nested `WHILE` + mixed branch local/external object emission:
  `b dp0p1qfp2p3ap4ghu0we1vdp5p6qfp7p8qhc0we2vxxe3r`
- [x] current widened `WHILE` + shared-transitive object emission:
  `b dp0p1qfu0u1xe0r`
- [x] current widened `DO` + nested `WHILE` object emission:
  `b de0dp0p1qfe1xp2p3qtoe2r`
- [x] current widened `WHILE` + nested `DO` object emission:
  `b dp0p1qfe0de1p2p3qtoxe2r`
- [x] current widened `DO` + nested `WHILE` + call/external object emission:
  `b dc0dp0p1qfu0xp2p3qtoe1r`
- [x] current widened `WHILE` + nested `DO` + call/external object emission:
  `b dp0p1qfc0du0p2p3qtoxe1r`
- [x] current widened mixed `DO`/`WHILE` + branch local/external object emission:
  `b dp0p1ap2ghu0we1vdp3p4qfp5p6qhc0we2vxp7p8qtoe3r`
- [x] current widened `WHILE` + nested `DO` + shared-transitive object emission:
  `b dp0p1qfu0du1p2p3qtoxe0r`
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
- [x] current widened repeated-root-external object emission:
  `b e0u0u1u0e1r`
- [x] current widened branch-sibling-external object emission:
  `b p0p1ap2ghu0u1we0ve1r`
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
- [x] current harness runtime output for the `DO` + nested `WHILE` slice:
  `OUTER`, `DONE`
- [x] current harness runtime output for the `WHILE` + nested `DO` slice:
  `DONE`
- [x] current harness runtime output for the `DO` + nested `WHILE` + call/external slice:
  `HELLO`, `DONE`
- [x] current harness runtime output for the `WHILE` + nested `DO` + call/external slice:
  `DONE`
- [x] current harness runtime output for the mixed `DO`/`WHILE` + branch local/external slice:
  `TOOL7`, `DONE`
- [x] current harness runtime output for the `WHILE` + nested `DO` + shared-transitive slice:
  `DONE`
- [x] current harness runtime output for the sibling-external slice:
  `START`, `MID1`, `MID2`, `DONE`
- [x] current harness runtime output for the child-sibling-external slice:
  `START`, `MID`, `END1`, `END2`, `DONE`
- [x] current harness runtime output for the branch-local + transitive-external slice:
  `LOCAL`, `MID`, `END`, `DONE`
- [x] current harness runtime output for the repeated-root-external slice:
  `START`, `MID1`, `MID2`, `MID1`, `DONE`
- [x] current harness runtime output for the shared-transitive-external slice:
  `START`, `MID1`, `END`, `MID2`, `END`, `DONE`
- [x] current harness runtime output for the branch-sibling-external slice:
  `MID1`, `MID2`, `DONE`
- [x] current harness runtime output for the branch-shared-transitive slice:
  `MID1`, `END`, `MID2`, `END`, `DONE`
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
- [x] current harness runtime output for the `DO ... UNTIL ... OD` slice:
  `BODY`, `DONE`
- [x] current harness runtime output for the call/external loop slice:
  `HELLO`, `TOOL7`, `DONE`
- [x] current harness runtime output for the loop + branch slice:
  `YES`, `DONE`
- [x] current harness runtime output for the loop + branch-call slice:
  `HELLO`, `DONE`
- [x] current harness runtime output for the loop + branch-external slice:
  `TOOL7`, `DONE`
- [x] current harness runtime output for the nested-loop slice:
  `OUTER`, `INNER`, `DONE`
- [x] current harness runtime output for the nested loop + call/external slice:
  `HELLO`, `TOOL7`, `DONE`
- [x] current harness runtime output for the nested loop + nested-branch slice:
  `OUTER`, `INNER`, `DONE`
- [x] current harness runtime output for the nested loop + mixed branch local/external slice:
  `TOOL7`, `HELLO`, `DONE`
- [x] current harness runtime output for the `WHILE ... DO ... OD` slice:
  `DONE`
- [x] current harness runtime output for the `WHILE` + call/external slice:
  `DONE`
- [x] current harness runtime output for the `WHILE` + branch slice:
  `DONE`
- [x] current harness runtime output for the `WHILE` + branch-call slice:
  `DONE`
- [x] current harness runtime output for the `WHILE` + branch-external slice:
  `DONE`
- [x] current harness runtime output for the nested `WHILE` slice:
  `DONE`
- [x] current harness runtime output for the nested `WHILE` + call/external slice:
  `DONE`
- [x] current harness runtime output for the nested `WHILE` + mixed branch local/external slice:
  `DONE`
- [x] current harness runtime output for the `WHILE` + shared-transitive slice:
  `DONE`

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
