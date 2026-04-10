# `ALINK` Status

Current as of `2026-04-09`.

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
- [ ] larger body-op surface than the current arithmetic/procedure/branch/`WHILE`/nested-loop-combined slice
- [ ] broader variable/data surface beyond the current multi-var module-scope integer storage/read/write/control slice
- [ ] broader procedure/function surface beyond the current local/external integer arg/return slice
- [ ] full historical dead-strip/link behavior

## Harness-Proven Current Widening Line

- [x] loads widened `ACTC` output for:
  `PrintI(50 + 7 - 3)` and `PrintIE(60 - 3 + 2)`
- [x] also loads mixed-precedence / parenthesized `ACTC` output for:
  `PrintI(2 + 3 * 4)` and `PrintIE((20 - 5) / 3)`
- [x] also loads arithmetic/comparison mixed `ACTC` output for:
  `PrintIE((2 + 3) * 4 = 20)` and `PrintIE((2 + 3 * 4) > 10)`
- [x] also loads module-scope integer storage/read/write `ACTC` output for:
  `INT X=[0]`, `PrintIE(X)`, `X=X+1`, `PrintIE(X)`
- [x] also loads module-scope integer storage/read/write under loop control:
  `DO PrintIE(X) X=X+1 UNTIL X=2 OD`
- [x] also loads module-scope integer storage/read/write under branch control:
  `IF X=1 THEN ... ELSE ... FI`
- [x] also loads module-scope integer storage/read/write under `WHILE` control:
  `WHILE X<2 DO ... OD`
- [x] also loads module-scope integer storage/read/write driving local/external calls:
  `IF X=1 THEN HELLO() ...`, `IF X=2 THEN W() FI`, `WHILE X<1 DO W() ... OD`
- [x] also loads multiple module-scope integer vars in one module:
  `INT X=[0]`, `INT Y=[2]`, `PrintIE(X)`, `PrintIE(Y)`, `X=Y+1`
- [x] also loads variable-to-variable arithmetic assignment:
  `X=X+Y`
- [x] also loads multiple module-scope integer vars under `WHILE` control:
  `WHILE X<Y DO ... OD`
- [x] also loads multiple module-scope integer vars driving local/external calls:
  `IF X<Y THEN HELLO() W() FI`
- [x] also loads multiple module-scope integer vars driving shared-transitive external closure under branch control:
  `IF X<Y THEN W() Q() FI` with `W -> Z` and `Q -> Z`
- [x] also loads multiple module-scope integer vars driving shared-transitive external closure under `WHILE` control:
  `WHILE X<Y DO W() Q() X=X+1 OD` with `W -> Z` and `Q -> Z`
- [x] also loads zero-arg local procedures that return integer values:
  `PROC TWO() RETURN 2`
- [x] also loads expression-position local procedure calls with returned values:
  `PrintIE(TWO())`, `PrintIE(TWO()+THREE())`
- [x] also loads expression-position unresolved-external calls with returned values:
  `PrintIE(W())`, `PrintIE(W()+1)`
- [x] also loads returned values used in assignment and control flow:
  `X=NEXT()` and `IF W()=7 THEN ... FI`
- [x] also loads local procedure parameters and expression-valued call arguments:
  `PROC INC(N) RETURN N+1`, `PrintIE(INC(2+3))`
- [x] also loads multiple local procedure parameters:
  `PROC ADD(X,Y) RETURN X+Y`, `PrintIE(ADD(2,3))`
- [x] also loads unresolved-external procedure parameters:
  `PrintIE(W(5))` with `PROC W(N) RETURN N+2`
- [x] also loads multiple unresolved-external procedure parameters:
  `PrintIE(W(2,3))` with `PROC W(X,Y) RETURN X+Y`
- [x] also loads nested call results reused as later call arguments:
  `PrintIE(W(INC(2+3)))`
- [x] also loads composed boolean conditions with `AND`, `OR`, and `NOT`:
  `IF (X<Y AND W()=7) OR Z()=1 THEN ... FI` and `IF NOT(Z()=1) THEN ... FI`
- [x] also loads arg-bearing local/external calls under branch and loop control:
  `IF 1 = 1 THEN PrintIE(INC(2+3)) ELSE ... FI` and `WHILE X < 2 DO PrintIE(W(X+5)) X=X+1 OD`
- [x] also loads composed boolean predicates driven by arg-bearing local/external calls:
  `IF (X<Y AND W(5)=7) OR Z(1)=1 THEN ... FI` and `IF (INC(X)=2 AND W(Y+5)=9) OR NOT(Z(1)=1) THEN ... FI`
- [x] also loads direct comparison-operator `ACTC` output for:
  `PrintIE(2 <> 3)`, `PrintIE(2 < 3)`, `PrintIE(3 <= 3)`, `PrintIE(4 >= 3)`
- [x] also loads high string-index `ACTC` output through `F`:
  `PrintE("A")` through `PrintE("P")`
- [x] also loads high integer-index `ACTC` output through `J`:
  `PrintIE(0)` through `PrintIE(19)`
- [x] also loads high string-index `IF/ELSE` control-flow `ACTC` output:
  `IF 1 = 0 THEN ... ELSE PrintE("I") ... PrintE("P") FI`
- [x] also loads high string-index `DO ... UNTIL ... OD` control-flow `ACTC` output:
  `DO PrintE("A") ... PrintE("P") UNTIL 1 = 1 OD`
- [x] also loads high string-index `DO ... UNTIL ... OD` + `IF/ELSE` control-flow `ACTC` output:
  `DO IF 1 = 0 THEN PrintE("A") ... ELSE PrintE("I") ... PrintE("P") FI UNTIL 1 = 1 OD`
- [x] also loads high integer-index `IF/ELSE` control-flow `ACTC` output:
  `IF 1 = 0 THEN PrintIE(0..7) ELSE PrintIE(8..15) FI`
- [x] also loads high integer-index `DO ... UNTIL ... OD` + `IF/ELSE` control-flow `ACTC` output:
  `DO IF 1 = 0 THEN PrintIE(0..7) ELSE PrintIE(8..15) FI UNTIL 1 = 1 OD`
- [x] also loads high string-index branch-local unresolved-external output:
  `IF 1 = 1 THEN W() PrintE("A") ... PrintE("L") ELSE PrintE("BAD") FI`
- [x] also loads high string-index transitive branch-local unresolved-external output:
  `IF 1 = 1 THEN W() PrintE("A") ... PrintE("L") ELSE PrintE("BAD") FI` with `W -> Z`
- [x] also loads high string-index shared-transitive branch-local unresolved-external output:
  `IF 1 = 1 THEN W() Q() PrintE("A") ... PrintE("L") ELSE PrintE("BAD") FI` with `W -> Z` and `Q -> Z`
- [x] also loads high string-index shared-transitive branch-local unresolved-external output beyond the old 16-literal root ceiling:
  `IF 1 = 1 THEN W() Q() PrintE("A") ... PrintE("P") ELSE PrintE("BAD") FI` with `W -> Z` and `Q -> Z`
- [x] also loads high string-index shared-transitive loop output:
  `DO W() Q() PrintE("A") ... PrintE("J") UNTIL 1 = 1 OD` with `W -> Z` and `Q -> Z`
- [x] also loads high string-index nested shared-transitive branch output:
  `IF 1 = 1 THEN IF 2 + 3 * 4 > 10 THEN W() Q() PrintE("A") ... PrintE("H") ELSE ... FI ELSE ... FI`
- [x] also loads high string-index nested-loop unresolved-external output:
  `DO WHILE 1 = 0 DO PrintE("BAD") OD W() PrintE("A") ... PrintE("J") UNTIL 1 = 1 OD`
- [x] also loads full high int-index nested-loop `IF/ELSE` output:
  `DO WHILE 1 = 0 DO OD IF 1 = 0 THEN PrintIE(0..7) ELSE PrintIE(8..15) FI UNTIL 1 = 1 OD`
- [x] also loads full high string-index nested-loop `IF/ELSE` output:
  `DO WHILE 1 = 0 DO OD IF 1 = 0 THEN PrintE("A") ... PrintE("H") ELSE PrintE("I") ... PrintE("P") FI UNTIL 1 = 1 OD`
- [x] also loads arithmetic/comparison `IF/ELSE` `ACTC` output for:
  `IF 2 + 3 * 4 > 10 THEN ... ELSE ... FI`
- [x] also loads direct comparison-operator branch and loop `ACTC` output for:
  `IF 2 <> 3 THEN ... FI`, `DO ... UNTIL 3 <= 3 OD`, `WHILE 2 >= 3 DO ... OD`
- [x] also loads direct comparison-operator branch-local procedure-call `ACTC` output for:
  `IF 2 < 3 THEN HELLO() FI` and `IF 2 >= 3 THEN ... ELSE ... FI`
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
- [x] also loads repeated root unresolved-external reuse:
  `W()`, `Z()`, `W()`
- [x] also loads shared transitive unresolved-external reuse:
  `W -> Z` and `Q -> Z`
- [x] also loads sibling unresolved-external calls inside arithmetic/comparison-driven control flow:
  `IF ... THEN W() Z() ...`
- [x] also loads shared transitive unresolved-external calls inside arithmetic/comparison-driven control flow:
  `IF ... THEN W() Q() ...` with `W -> Z` and `Q -> Z`
- [x] also loads single-branch `IF` control-flow `ACTC` output for:
  `IF 1 = 0 THEN ... FI` and `IF 1 = 1 THEN ... FI`
- [x] also loads `ELSE` control-flow `ACTC` output for:
  `IF 1 = 0 THEN ... ELSE ... FI`
- [x] also loads nested `IF` control-flow `ACTC` output for:
  `IF 1 = 1 THEN IF 1 = 0 THEN ... FI ... FI`
- [x] also loads nested `ELSE` control-flow `ACTC` output for:
  `IF 1 = 1 THEN IF 1 = 0 THEN ... ELSE ... FI ELSE ... FI`
- [x] also loads explicit early-return control-flow `ACTC` output for:
  `IF ... THEN RETURN FI`, `IF ... ELSE RETURN FI`, `DO ... RETURN UNTIL ... OD`, `WHILE ... RETURN OD`
- [x] also loads explicit early-return control flow after local/external calls:
  `IF HELLO() RETURN FI`, `IF W() RETURN FI`, `WHILE HELLO() W() RETURN OD`
- [x] also loads explicit early-return control flow with transitive externals under nested branches:
  `IF ... THEN IF ... THEN W() RETURN FI ... FI` with `W -> Z`
- [x] also loads explicit early-return mixed branch/local-external loop control:
  `DO IF ... THEN W() ELSE HELLO() FI RETURN UNTIL ... OD`
- [x] also loads explicit early-return nested-loop control with transitive externals:
  `WHILE ... DO DO W() RETURN UNTIL ... OD OD` with `W -> Z`
- [x] also loads `DO ... UNTIL ... OD` loop `ACTC` output for:
  `DO ... UNTIL 1 = 1 OD`
- [x] also loads local-call plus unresolved-external loop `ACTC` output for:
  `DO HELLO() W() UNTIL 1 = 1 OD`
- [x] also loads branch control flow inside `DO ... UNTIL ... OD`:
  `DO IF 2 + 3 * 4 > 10 THEN ... ELSE ... FI UNTIL 1 = 1 OD`
- [x] also loads branch-local procedure calls inside `DO ... UNTIL ... OD`:
  `DO IF 2 + 3 * 4 > 10 THEN HELLO() ELSE BYE() FI UNTIL 1 = 1 OD`
- [x] also loads branch-local unresolved externals inside `DO ... UNTIL ... OD`:
  `DO IF 2 + 3 * 4 > 10 THEN W() ELSE ... FI UNTIL 1 = 1 OD`
- [x] also loads nested `DO ... UNTIL ... OD` `ACTC` output for:
  `DO ... DO ... UNTIL 1 = 1 OD UNTIL 1 = 1 OD`
- [x] also loads local-call plus unresolved-external nested-loop `ACTC` output for:
  `DO HELLO() DO W() UNTIL 1 = 1 OD UNTIL 1 = 1 OD`
- [x] also loads nested branch control flow inside nested `DO ... UNTIL ... OD`:
  `DO IF ... THEN ... FI DO IF ... THEN ... ELSE ... FI UNTIL ... OD UNTIL ... OD`
- [x] also loads mixed local/external branch calls inside nested `DO ... UNTIL ... OD`:
  `DO IF ... THEN W() ELSE ... FI DO IF ... THEN HELLO() ELSE ... FI UNTIL ... OD UNTIL ... OD`
- [x] also loads top-tested `WHILE ... DO ... OD` `ACTC` output for:
  `WHILE 1 = 0 DO ... OD`
- [x] also loads local/external calls inside top-tested `WHILE ... DO ... OD`
- [x] also loads `IF ... THEN ... ELSE ... FI` inside top-tested `WHILE ... DO ... OD`
- [x] also loads local branch calls inside top-tested `WHILE ... DO ... OD`
- [x] also loads unresolved-external branch calls inside top-tested `WHILE ... DO ... OD`
- [x] also loads nested top-tested `WHILE ... DO ... OD`
- [x] also loads local/external calls inside nested top-tested `WHILE ... DO ... OD`
- [x] also loads mixed local/external branch content inside nested top-tested `WHILE ... DO ... OD`
- [x] also loads shared transitive unresolved-external reuse inside top-tested `WHILE ... DO ... OD`
- [x] also loads `DO ... UNTIL ... OD` containing nested `WHILE ... DO ... OD`
- [x] also loads `WHILE ... DO ... OD` containing nested `DO ... UNTIL ... OD`
- [x] also loads mixed local/external and branch content across `DO`/`WHILE` mixed nesting
- [x] also loads shared transitive unresolved-external reuse across `WHILE` containing nested `DO ... UNTIL ... OD`
- [x] resolves the current widened child-object closure including `OBJ/W.AVO`
- [x] resolves the current widened transitive child-object closure including `OBJ/W.AVO` and `OBJ/Z.AVO`
- [x] resolves sibling child objects from the root:
  `OBJ/W.AVO` and `OBJ/Z.AVO`
- [x] resolves sibling child objects from a child module:
  `OBJ/Z.AVO` and `OBJ/Q.AVO`
- [x] reuses the same root child object across repeated call sites
- [x] reuses the same transitive child object across multiple parents
- [x] emits a widened `BIN/MAIN.AVM` of `76` bytes on that slice
- [x] emits a precedence-slice `BIN/MAIN.AVM` of `31` bytes
- [x] emits an arithmetic/comparison slice `BIN/MAIN.AVM` of `72` bytes
- [x] emits a direct-comparison print slice `BIN/MAIN.AVM` of `91` bytes
- [x] emits a high string-index slice `BIN/MAIN.AVM` of `143` bytes
- [x] emits a high integer-index slice `BIN/MAIN.AVM` of `135` bytes
- [x] emits a high string-index `IF/ELSE` slice `BIN/MAIN.AVM` of `156` bytes
- [x] emits a high string-index `DO ... UNTIL ... OD` slice `BIN/MAIN.AVM` of `153` bytes
- [x] emits a high string-index `DO ... UNTIL ... OD` + `IF/ELSE` slice `BIN/MAIN.AVM` of `166` bytes
- [x] emits a high integer-index `IF/ELSE` slice `BIN/MAIN.AVM` of `124` bytes
- [x] emits a high integer-index `DO ... UNTIL ... OD` + `IF/ELSE` slice `BIN/MAIN.AVM` of `134` bytes
- [x] emits a high string-index branch-external slice `BIN/MAIN.AVM` of `155` bytes
- [x] emits a high string-index transitive branch-external slice `BIN/MAIN.AVM` of `162` bytes
- [x] emits a high string-index shared-transitive branch-external slice `BIN/MAIN.AVM` of `181` bytes
- [x] emits a 17-root-string shared-transitive branch-external slice `BIN/MAIN.AVM` of `213` bytes
- [x] emits a high string-index shared-transitive `DO ... UNTIL ... OD` slice `BIN/MAIN.AVM` of `152` bytes
- [x] emits a high string-index nested shared-transitive branch slice `BIN/MAIN.AVM` of `178` bytes
- [x] emits a high string-index nested-loop external slice `BIN/MAIN.AVM` of `144` bytes
- [x] emits a full high int-index nested-loop `IF/ELSE` slice `BIN/MAIN.AVM` of `147` bytes
- [x] emits a full high string-index nested-loop `IF/ELSE` slice `BIN/MAIN.AVM` of `179` bytes
- [x] emits a direct-comparison branch slice `BIN/MAIN.AVM` of `149` bytes
- [x] emits a direct-comparison loop slice `BIN/MAIN.AVM` of `76` bytes
- [x] emits a direct-comparison branch-call slice `BIN/MAIN.AVM` of `77` bytes
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
- [x] emits a repeated-root-external `BIN/MAIN.AVM` of `71` bytes
- [x] emits a shared-transitive-external `BIN/MAIN.AVM` of `85` bytes
- [x] emits a branch-sibling-external `BIN/MAIN.AVM` of `83` bytes
- [x] emits a branch-shared-transitive `BIN/MAIN.AVM` of `100` bytes
- [x] emits an `IF` slice `BIN/MAIN.AVM` of `65` bytes
- [x] emits an `ELSE` slice `BIN/MAIN.AVM` of `60` bytes
- [x] emits a nested-`IF` slice `BIN/MAIN.AVM` of `77` bytes
- [x] emits a nested-`ELSE` slice `BIN/MAIN.AVM` of `86` bytes
- [x] emits an early-return `IF` slice `BIN/MAIN.AVM` of `62` bytes
- [x] emits an early-return `ELSE` slice `BIN/MAIN.AVM` of `64` bytes
- [x] emits an early-return `DO ... UNTIL ... OD` slice `BIN/MAIN.AVM` of `62` bytes
- [x] emits an early-return `WHILE ... DO ... OD` slice `BIN/MAIN.AVM` of `65` bytes
- [x] emits a nested early-return `IF` slice `BIN/MAIN.AVM` of `105` bytes
- [x] emits an early-return local-call `IF` slice `BIN/MAIN.AVM` of `66` bytes
- [x] emits an early-return external `IF` slice `BIN/MAIN.AVM` of `66` bytes
- [x] emits an early-return external `ELSE` slice `BIN/MAIN.AVM` of `68` bytes
- [x] emits an early-return external `DO ... UNTIL ... OD` slice `BIN/MAIN.AVM` of `66` bytes
- [x] emits an early-return `WHILE` local/external slice `BIN/MAIN.AVM` of `85` bytes
- [x] emits a nested early-return transitive-external `IF` slice `BIN/MAIN.AVM` of `121` bytes
- [x] emits an early-return mixed branch/local-external `DO ... UNTIL ... OD` slice `BIN/MAIN.AVM` of `99` bytes
- [x] emits an early-return nested `DO ... UNTIL ... OD` external slice `BIN/MAIN.AVM` of `76` bytes
- [x] emits an early-return transitive-external `WHILE` slice `BIN/MAIN.AVM` of `81` bytes
- [x] emits an early-return nested `WHILE`/`DO` transitive-external slice `BIN/MAIN.AVM` of `91` bytes
- [x] emits a `DO ... UNTIL ... OD` slice `BIN/MAIN.AVM` of `47` bytes
- [x] emits a call/external `DO ... UNTIL ... OD` slice `BIN/MAIN.AVM` of `73` bytes
- [x] emits a branch `DO ... UNTIL ... OD` slice `BIN/MAIN.AVM` of `73` bytes
- [x] emits a branch-call `DO ... UNTIL ... OD` slice `BIN/MAIN.AVM` of `83` bytes
- [x] emits a branch-external `DO ... UNTIL ... OD` slice `BIN/MAIN.AVM` of `84` bytes
- [x] emits a nested `DO ... UNTIL ... OD` slice `BIN/MAIN.AVM` of `70` bytes
- [x] emits a nested loop + call/external slice `BIN/MAIN.AVM` of `83` bytes
- [x] emits a nested loop + nested-branch slice `BIN/MAIN.AVM` of `107` bytes
- [x] emits a nested loop + mixed branch local/external slice `BIN/MAIN.AVM` of `135` bytes
- [x] emits a `WHILE ... DO ... OD` slice `BIN/MAIN.AVM` of `49` bytes
- [x] emits a `WHILE` + call/external slice `BIN/MAIN.AVM` of `76` bytes
- [x] emits a `WHILE` + branch slice `BIN/MAIN.AVM` of `78` bytes
- [x] emits a `WHILE` + branch-call slice `BIN/MAIN.AVM` of `86` bytes
- [x] emits a `WHILE` + branch-external slice `BIN/MAIN.AVM` of `87` bytes
- [x] emits a nested `WHILE` slice `BIN/MAIN.AVM` of `76` bytes
- [x] emits a nested `WHILE` + call/external slice `BIN/MAIN.AVM` of `89` bytes
- [x] emits a nested `WHILE` + mixed branch local/external slice `BIN/MAIN.AVM` of `141` bytes
- [x] emits a `WHILE` + shared-transitive slice `BIN/MAIN.AVM` of `86` bytes
- [x] emits a `DO` + nested `WHILE` slice `BIN/MAIN.AVM` of `73` bytes
- [x] emits a `WHILE` + nested `DO` slice `BIN/MAIN.AVM` of `73` bytes
- [x] emits a `DO` + nested `WHILE` + call/external slice `BIN/MAIN.AVM` of `86` bytes
- [x] emits a `WHILE` + nested `DO` + call/external slice `BIN/MAIN.AVM` of `86` bytes
- [x] emits a mixed `DO`/`WHILE` + branch local/external slice `BIN/MAIN.AVM` of `138` bytes
- [x] emits a `WHILE` + nested `DO` + shared-transitive slice `BIN/MAIN.AVM` of `96` bytes
- [x] harness proof exists through:
  `ACTC -> ALINK -> AVMRUN`
- [x] current harness runtime output for that widened slice:
  `HELLO`, `TOOL7`, `5459`
- [x] current harness runtime output for the precedence slice:
  `145`
- [x] current harness runtime output for the arithmetic/comparison slice:
  `14`, `5`, `1`, `1`, `TOOL7`
- [x] current harness runtime output for the direct-comparison slice:
  `1`, `1`, `1`, `1`, `0`, `0`
- [x] current harness runtime output for the high string-index slice:
  `A` through `P`
- [x] current harness runtime output for the high integer-index slice:
  `0` through `19`
- [x] current harness runtime output for the high string-index `IF/ELSE` slice:
  `I` through `P`
- [x] current harness runtime output for the high string-index `DO ... UNTIL ... OD` slice:
  `A` through `P`
- [x] current harness runtime output for the high integer-index `IF/ELSE` slice:
  `8` through `15`
- [x] current harness runtime output for the high string-index branch-external slice:
  `TOOL7` then `A` through `L`
- [x] current harness runtime output for the direct-comparison branch slice:
  `NE`, `LT`, `LE`, `GE`
- [x] current harness runtime output for the direct-comparison loop slice:
  `DO`, `DONE`
- [x] current harness runtime output for the direct-comparison branch-call slice:
  `HELLO`, `OK`
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
- [x] current harness runtime output for the early-return `IF` slice:
  `START`, `EARLY`
- [x] current harness runtime output for the early-return `ELSE` slice:
  `EARLY`
- [x] current harness runtime output for the early-return `DO ... UNTIL ... OD` slice:
  `START`, `EARLY`
- [x] current harness runtime output for the early-return `WHILE ... DO ... OD` slice:
  `START`, `EARLY`
- [x] current harness runtime output for the nested early-return `IF` slice:
  `START`, `EARLY`
- [x] current harness runtime output for the early-return local-call `IF` slice:
  `START`, `HELLO`
- [x] current harness runtime output for the early-return external `IF` slice:
  `START`, `TOOL7`
- [x] current harness runtime output for the early-return external `ELSE` slice:
  `TOOL7`
- [x] current harness runtime output for the early-return external `DO ... UNTIL ... OD` slice:
  `START`, `TOOL7`
- [x] current harness runtime output for the early-return `WHILE` local/external slice:
  `START`, `HELLO`, `TOOL7`
- [x] current harness runtime output for the nested early-return transitive-external `IF` slice:
  `START`, `MID`, `END`
- [x] current harness runtime output for the early-return mixed branch/local-external `DO ... UNTIL ... OD` slice:
  `START`, `TOOL7`
- [x] current harness runtime output for the early-return nested `DO ... UNTIL ... OD` external slice:
  `START`, `TOOL7`
- [x] current harness runtime output for the early-return transitive-external `WHILE` slice:
  `START`, `MID`, `END`
- [x] current harness runtime output for the early-return nested `WHILE`/`DO` transitive-external slice:
  `START`, `MID`, `END`
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
- [x] current harness runtime output for the dense shared-transitive branch + early-return slice:
  `MID1`, `END`, `MID2`, `END`, `A` through `P`
- [x] emits a dense shared-transitive branch + early-return slice `BIN/MAIN.AVM` of `227` bytes
- [x] current harness runtime output for the dense mixed nested-loop + shared-transitive slice:
  `MID2`, `END`, `A` through `P`
- [x] emits a dense mixed nested-loop + shared-transitive slice `BIN/MAIN.AVM` of `223` bytes
- [x] current harness runtime output for the dense early-return nested mixed-loop + shared-transitive slice:
  `MID1`, `END`, `MID2`, `END`, `A` through `P`
- [x] emits a dense early-return nested mixed-loop + shared-transitive slice `BIN/MAIN.AVM` of `226` bytes
- [x] current harness runtime output for the dense branch-gated early-return nested mixed-loop + shared-transitive slice:
  `MID1`, `END`, `MID2`, `END`, `A` through `P`
- [x] emits a dense branch-gated early-return nested mixed-loop + shared-transitive slice `BIN/MAIN.AVM` of `251` bytes

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
