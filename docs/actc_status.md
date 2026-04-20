# `ACTC` Status

Current as of `2026-04-20`.

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
- [x] Current shipped UDOS build links again under the real target after widening the tool load window from `$2000` to `$4000`

Current real-target build note:

- `./tools/build_actc_udos.sh` is green again
- `make -C ../udos vice-action-actc` is green again on the current working tree
- `make -C ../udos vice-action-actc-alink-avmrun` is green again on the
  current working tree
- current shipped `ACTC` map footprint is:
  - `CODE`: `$24B9`
  - `BSS`: `$06F9`
  - total runtime span from `$0900` through `$34B1`

Current lowering note:

- [x] proc-local `INT` declarations currently lower to proc-scoped static slots plus declaration-site runtime init stores; this is not a stack-frame model yet
- [x] current harness-proven variable slot ceiling is `16`, aligned with the current VM local-slot count
- [x] module-scope `REAL` declarations now emit 4-byte storage-width metadata;
  REAL32 expressions and runtime-library calls are not lowered yet

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
- [ ] broader stateful variable surface beyond the current multi-var module-scope
  `INT`, narrow `BYTE`/`CARD`, and declaration-only 4-byte `REAL` slices
- [ ] broader procedure/function surface beyond the current local/external integer arg/return slice
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
- [x] direct comparison operator print-expression chains:
  `PrintIE(2 <> 3)`, `PrintIE(2 < 3)`, `PrintIE(3 <= 3)`, `PrintIE(4 >= 3)`
- [x] string-literal pool indices widened through `Z` on the harness line with dead-stripped locals:
  `PROC F() PrintE("0") ... PrintE("Y") RETURN` and `PROC MAIN() PrintE("Z") RETURN`
- [x] integer-literal pool indices widened through `Z` on the harness line with dead-stripped locals:
  `PROC F() PrintIE(0..30) RETURN`, `PROC G() PrintIE(31..34) RETURN`, `PROC MAIN() PrintIE(35) RETURN`
- [x] dense local-call proc bodies widened beyond the old `96`-char harness ceiling:
  `PROC MAIN() T() ... T() PrintIE(X) RETURN` with `74` local calls in one body
- [x] compiler-emitted export offsets now print past `255` on the harness line:
  `PROC T() RETURN`, `PROC F() T() ...`, `PROC G() T() ...`, `PROC MAIN() PrintE("OK") RETURN`, proving `x main 261 7` in one `AVO1`
- [x] compiler-emitted proc sizes now print past `255` on the harness line:
  `PROC BIG() PrintI(X) ... RETURN`, `PROC MAIN() PrintE("OK") RETURN`, proving `x big 0 259`
- [x] high string-index control flow under `IF/ELSE`:
  `IF 1 = 0 THEN ... ELSE PrintE("I") ... PrintE("P") FI`
- [x] high string-index loop bodies:
  `DO PrintE("A") ... PrintE("P") UNTIL 1 = 1 OD`
- [x] high string-index loop bodies combined with `IF/ELSE`:
  `DO IF 1 = 0 THEN PrintE("A") ... ELSE PrintE("I") ... PrintE("P") FI UNTIL 1 = 1 OD`
- [x] high int-index control flow under `IF/ELSE`:
  `IF 1 = 0 THEN PrintIE(0..7) ELSE PrintIE(8..15) FI`
- [x] high int-index loop bodies combined with `IF/ELSE`:
  `DO IF 1 = 0 THEN PrintIE(0..7) ELSE PrintIE(8..15) FI UNTIL 1 = 1 OD`
- [x] high string indices mixed with unresolved externals under branch control:
  `IF 1 = 1 THEN W() PrintE("A") ... PrintE("L") ELSE PrintE("BAD") FI`
- [x] high string indices mixed with transitive externals under branch control:
  `IF 1 = 1 THEN W() PrintE("A") ... PrintE("L") ELSE PrintE("BAD") FI` with `W -> Z`
- [x] high string indices mixed with shared transitive externals under branch control:
  `IF 1 = 1 THEN W() Q() PrintE("A") ... PrintE("L") ELSE PrintE("BAD") FI` with `W -> Z` and `Q -> Z`
- [x] high string indices beyond the old 16-literal root ceiling under shared transitive branch control:
  `IF 1 = 1 THEN W() Q() PrintE("A") ... PrintE("P") ELSE PrintE("BAD") FI` with `W -> Z` and `Q -> Z`
- [x] high string indices mixed with shared transitive externals inside loop control:
  `DO W() Q() PrintE("A") ... PrintE("J") UNTIL 1 = 1 OD` with `W -> Z` and `Q -> Z`
- [x] high string indices mixed with nested branch + shared transitive externals:
  `IF 1 = 1 THEN IF 2 + 3 * 4 > 10 THEN W() Q() PrintE("A") ... PrintE("H") ELSE ... FI ELSE ... FI`
- [x] high string indices mixed with nested-loop external control:
  `DO WHILE 1 = 0 DO PrintE("BAD") OD W() PrintE("A") ... PrintE("J") UNTIL 1 = 1 OD`
- [x] full high int indices inside nested loop + `IF/ELSE` control:
  `DO WHILE 1 = 0 DO OD IF 1 = 0 THEN PrintIE(0..7) ELSE PrintIE(8..15) FI UNTIL 1 = 1 OD`
- [x] full high string indices inside nested loop + `IF/ELSE` control:
  `DO WHILE 1 = 0 DO OD IF 1 = 0 THEN PrintE("A") ... PrintE("H") ELSE PrintE("I") ... PrintE("P") FI UNTIL 1 = 1 OD`
- [x] arithmetic/comparison conditions inside `IF ... THEN ... ELSE ... FI`:
  `IF 2 + 3 * 4 > 10 THEN ... ELSE ... FI`
- [x] module-scope integer variable declaration plus direct read/assignment:
  `INT X=[0]`, `PrintIE(X)`, `X=X+1`, `PrintIE(X)`
- [x] module-scope integer variable state carried through loop control:
  `DO PrintIE(X) X=X+1 UNTIL X=2 OD`
- [x] module-scope integer variables driving branch control:
  `IF X=1 THEN ... ELSE ... FI`
- [x] module-scope integer variables driving `WHILE ... DO ... OD`:
  `WHILE X<2 DO ... OD`
- [x] module-scope integer variables driving local/external calls under control flow:
  `IF X=1 THEN HELLO() ...`, `IF X=2 THEN W() FI`, `WHILE X<1 DO W() ... OD`
- [x] multiple module-scope integer variables in one module:
  `INT X=[0]`, `INT Y=[2]`, `PrintIE(X)`, `PrintIE(Y)`, `X=Y+1`
- [x] narrow module-scope `BYTE`/`CARD` declarations lower through the existing
  16-bit variable slot path:
  `BYTE X=[0]`, `CARD Y=[2]`, `PrintIE(X)`, `PrintIE(Y)`, `X=Y+1`
- [x] module-scope `REAL` declarations emit a 4-byte variable slot without
  importing unused REAL runtime operators:
  `REAL X`, `PrintIE(7)`
- [x] variable-to-variable arithmetic assignment:
  `X=X+Y`
- [x] multiple module-scope integer variables driving `WHILE ... DO ... OD`:
  `WHILE X<Y DO ... OD`
- [x] multiple module-scope integer variables driving local/external calls under branch control:
  `IF X<Y THEN HELLO() W() FI`
- [x] multiple module-scope integer variables driving shared-transitive external closure under branch control:
  `IF X<Y THEN W() Q() FI` with `W -> Z` and `Q -> Z`
- [x] multiple module-scope integer variables driving shared-transitive external closure under `WHILE` control:
  `WHILE X<Y DO W() Q() X=X+1 OD` with `W -> Z` and `Q -> Z`
- [x] direct comparison operator conditions inside `IF ... THEN ... FI`:
  `IF 2 <> 3 THEN ... FI`, `IF 2 < 3 THEN ... FI`, `IF 3 <= 3 THEN ... FI`, `IF 4 >= 3 THEN ... FI`
- [x] direct comparison operator conditions inside loop forms:
  `DO ... UNTIL 3 <= 3 OD` and `WHILE 2 >= 3 DO ... OD`
- [x] direct comparison operator conditions driving local branch calls:
  `IF 2 < 3 THEN HELLO() FI` and `IF 2 >= 3 THEN ... ELSE ... FI`
- [x] multiple local procedures in one module:
  `PROC HELLO() ...` and `PROC MAIN() ...`
- [x] local user procedure calls:
  `HELLO()`
- [x] explicit integer return values from zero-arg local procedures:
  `PROC TWO() RETURN 2`
- [x] expression-position local procedure calls with returned values:
  `PrintIE(TWO())`, `PrintIE(TWO()+THREE())`
- [x] expression-position unresolved-external calls with returned values:
  `PrintIE(W())`, `PrintIE(W()+1)`
- [x] returned values used in assignment and control flow:
  `X=NEXT()` and `IF W()=7 THEN ... FI`
- [x] local procedure parameters and expression-valued call arguments:
  `PROC INC(N) RETURN N+1`, `PrintIE(INC(2+3))`
- [x] multiple local procedure parameters:
  `PROC ADD(X,Y) RETURN X+Y`, `PrintIE(ADD(2,3))`
- [x] unresolved-external procedure parameters:
  `PrintIE(W(5))` with `PROC W(N) RETURN N+2`
- [x] multiple unresolved-external procedure parameters:
  `PrintIE(W(2,3))` with `PROC W(X,Y) RETURN X+Y`
- [x] nested call results reused as later call arguments:
  `PrintIE(W(INC(2+3)))`
- [x] composed boolean conditions with `AND`, `OR`, and `NOT`:
  `IF (X<Y AND W()=7) OR Z()=1 THEN ... FI` and `IF NOT(Z()=1) THEN ... FI`
- [x] local/external arg-bearing calls inside branch and loop control:
  `IF 1 = 1 THEN PrintIE(INC(2+3)) ELSE ... FI` and `WHILE X < 2 DO PrintIE(W(X+5)) X=X+1 OD`
- [x] composed boolean predicates driven by arg-bearing local/external calls:
  `IF (X<Y AND W(5)=7) OR Z(1)=1 THEN ... FI` and `IF (INC(X)=2 AND W(Y+5)=9) OR NOT(Z(1)=1) THEN ... FI`
- [x] boolean/comparison expressions used as value expressions in assignment, return, and call-arg position:
  `X=(X<Y AND W(5)=7) OR Z(1)=1`, `RETURN N<3`, and `PrintIE(INC((X<Y AND W(5)=7) OR Z(1)=1))`
- [x] compound boolean/comparison expressions used in print-value position:
  `PrintIE((X<Y AND W(5)=7) OR Z(1)=1)`, `PrintIE((INC(X)=2 AND W(Y+5)=9) OR NOT(Z(1)=1))`, and `PrintI((X<Y AND W(5)=7) OR Z(1)=1)`
- [x] parenthesized boolean/comparison value expressions reused as arithmetic factors:
  `RETURN (N<3)+1`, `X=((X<Y AND W(5)=7) OR Z(1)=1)+1`, `PrintIE(INC(((X<Y AND W(5)=7) OR Z(1)=1)+1))`, and `PrintIE(((X<Y AND W(5)=7) OR Z(1)=1)+1)`
- [x] module-scope integer initializers from composed boolean/comparison literal expressions:
  `INT X=[(1<2 AND 2<3) OR NOT(0=1)]`
- [x] module-scope integer initializers from parenthesized boolean/comparison literal expressions reused as arithmetic factors:
  `INT X=[((1<2 AND 2<3) OR NOT(0=1))+1]`
- [x] proc-local integer declarations with declaration-site runtime initialization:
  `PROC TICK() INT X=[0] ...`
- [x] narrow proc-local `BYTE` declarations use the existing declaration-site
  runtime initialization path:
  `PROC TICK() BYTE X=[0] ...`
- [x] proc-local integer initializers rerun on each call:
  `TICK()` then `TICK()` prints `0`, `1`, `0`, `1`
- [x] proc-local integer initializers can read proc parameters and drive loop control:
  `PROC COUNT(N) INT X=[N] DO ... UNTIL X=2 OD`
- [x] module-scope integer storage/read/write reaches the current slot-`F` ceiling:
  `INT A=[0] ... INT P=[15]`, `PrintIE(K)`, `PrintIE(P)`, `P=P+1`
- [x] proc-local integer storage/read/write reaches the current slot-`F` ceiling with params plus locals:
  `PROC SHOW(Z) INT A ... INT O`, `O=Z+2`, `PrintIE(O)`
- [x] harness local procedure export tables reach the current slot-`A` ceiling with live calls beyond `7`:
  `PROC MAIN() P7() P8() P9() RETURN` with `PROC P0() ... PROC P9()`, proving `c8`, `c9`, and `cA` body-op emission
- [x] harness unresolved-external symbol tables reach the current digit-bearing `10`-entry fanout:
  `PROC MAIN() W0() ... W9() RETURN`, proving `u w0` through `u w9` emission in one root object
- [x] harness loop nesting reaches `9` deep across both loop forms:
  nested `DO ... UNTIL ... OD` printing `DEEP` and nested `WHILE 0=1 DO ... OD` falling through to `DONE`
- [x] identifiers can include digits after the first character across vars, proc names, params, and locals:
  `INT V0=[1]`, `PROC ADD1(N1)`, `INT X2=[N1+1]`, `ADD1(5)`
- [x] digit-bearing module/proc names compile through command-line module selection and module-header validation:
  `ACTC.PRG W1` on `MODULE W1`, `PROC W1()`
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
- [x] multi-arg local/external calls inside early-return control flow:
  `IF 1 = 1 THEN PrintIE(W(X,Y)) RETURN FI` and `DO IF X<Y THEN PrintIE(ADD(X,Y)) PrintIE(W(X+1,Y+1)) RETURN FI UNTIL 1 = 1 OD`
- [x] multi-arg transitive external calls inside nested mixed-loop early return:
  `WHILE X<3 DO DO IF W(X,Y)=3 THEN PrintIE(Q(X+3,Y+4)) RETURN FI UNTIL 1 = 1 OD X=X+1 OD` with `Q -> Z`
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
- [x] harness `ACTC` source-load limit widened beyond one page for dense source scenarios:
  `SOURCE_LIMIT = 511`
- [x] harness `ACTC` per-proc body-op storage widened beyond the old `96`-char ceiling for dense local-call bodies:
  `BODY_OPS_STRIDE = 160`
- [x] harness `ACTC` integer-literal pool widened through base-36 slot `Z` for dense local dead-strip proofs:
  `INT_LITERAL_MAX = 36`
- [x] harness `ACTC` string-literal pool widened through base-36 slot `Z` for dense module graphs:
  `STRING_LITERAL_MAX = 36`
- [x] harness `ACTC` local export/proc table widened beyond the old `8`-proc ceiling for dense modules:
  `EXPORT_MAX = 16`
- [x] harness `ACTC` unresolved-external table widened beyond the old `8`-symbol ceiling for wide root fanout:
  `EXTERNAL_MAX = 16`
- [x] harness `ACTC` loop-kind stack widened beyond the old `8`-deep nesting ceiling:
  `LOOP_MAX = 16`
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
- [x] current widened direct-comparison object emission:
  `b p0p1nzp2p3lzp4p5gp6qzp7p8lp9qzpApBgpCqzpDpElpFqzr`
- [x] current widened string-index object emission:
  `b e0e1e2e3e4e5e6e7e8e9eAeBeCeDeEeFr`
- [x] current widened int-index object emission:
  `b i0i1i2i3i4i5i6i7i8i9iAiBiCiDiEiFiGiHiIiJr`
- [x] current widened high string-index `IF/ELSE` object emission:
  `b p0p1qhe0e1e2e3e4e5e6e7we8e9eAeBeCeDeEeFvr`
- [x] current widened high string-index `DO ... UNTIL ... OD` object emission:
  `b de0e1e2e3e4e5e6e7e8e9eAeBeCeDeEeFp0p1qtor`
- [x] current widened high int-index `IF/ELSE` object emission:
  `b p0p1qhi2i3i4i5i6i7i8i9wiAiBiCiDiEiFiGiHvr`
- [x] current widened high string-index branch-external object emission:
  `b p0p1qhu0e0e1e2e3e4e5e6e7e8e9eAeBweCvr`
- [x] current widened direct-comparison `IF` object emission:
  `b p0p1nhe0vp2p3lhe1vp4p5gp6qhe2vp7p8lp9qhe3vpApBgpCqhe4vpDpElpFqhe5vr`
- [x] current widened direct-comparison loop object emission:
  `b de0p0p1gp2qtodp3p4lp5qfe1xe2r`
- [x] current widened direct-comparison branch-call object emission:
  `b p0p1lhc0vp2p3lp4qhe1we2vr`
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
- [x] current harness runtime output for the dense shared-transitive branch + early-return slice:
  `MID1`, `END`, `MID2`, `END`, `A` through `P`
- [x] current harness runtime output for the dense mixed nested-loop + shared-transitive slice:
  `MID2`, `END`, `A` through `P`
- [x] current harness runtime output for the dense early-return nested mixed-loop + shared-transitive slice:
  `MID1`, `END`, `MID2`, `END`, `A` through `P`
- [x] current harness runtime output for the dense branch-gated early-return nested mixed-loop + shared-transitive slice:
  `MID1`, `END`, `MID2`, `END`, `A` through `P`

## Current Biggest Risks

- Resident/VICE tool-service ABI sensitivity.
  The previous resident-facing load/save blocker is cleared on the current
  working tree, but this remains the first area to watch when widening compiler
  output.
- Probe stability.
  VICE automation is good enough to prove narrow slices, but it still costs time whenever a dirty line perturbs boot, mount, or prompt timing.
- Dirty-line versus committed-line drift.
  The current narrow compiler/linker/runtime path is green again. The active
  work is widening it without reintroducing the older ABI sensitivity.

## What Is Not Claimed Here

- full ACTION! compiler coverage
- full runtime lowering for arbitrary expressions/statements
- stable proof for every currently dirty widening experiment
