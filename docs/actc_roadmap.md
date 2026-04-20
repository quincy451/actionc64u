# `ACTC` Roadmap

Current as of `2026-04-20`.

This is the short planning document for the UDOS-native Action compiler, `ACTC.PRG`.
For the detailed proof ledger, see [actc_status.md](./actc_status.md).
For broader project coverage, see [action_matrix.md](./action_matrix.md).

## Current Position

Committed baseline:

- `ACTC.PRG` launches from a UDOS Action workspace.
- It loads the current project manifest and the tracked `SRC/<MODULE>.ACT` source file.
- It emits deterministic `AVO1` object output to `OBJ/<MODULE>.AVO`.
- The integrated `ACTC -> ALINK -> AVMRUN` path is proven on the committed Linux `VICE 3.7.1` line.

Current dirty-tree verification:

- `ACTC` front-end and codegen still appear correct.
- The previous mounted-tree save/service blocker has been cleared on the current
  UDOS line.
- `make -C ../udos vice-action-actc` is green again.
- The chained `ACTC -> ALINK -> AVMRUN` proof is green again on the current
  working tree.

## Accomplished

## Tool And Runtime Integration

- Stable UDOS packaging on release media as `ACTC.PRG`.
- Stable `A:` release-tool launch path on the committed baseline.
- Real-target build fits and launches under the widened tool load window.
- Real-target one-shot proof exists through `ACTC -> ALINK -> AVMRUN`.

## Compiler Front-End

- Module selection from the command line.
- Project/manifest guardrails.
- Source loading from `SRC/`.
- Module-header validation.
- Current narrow parser for arithmetic, comparisons, branching, loops, local calls, and unresolved external calls.
- Current narrow integer variable surface for module-scope and proc-local
  `INT` declarations.
- Narrow `BYTE`/`CARD` declaration acceptance through the existing 16-bit
  variable slot path.
- Declaration-only module-scope `REAL` support now records a 4-byte storage
  width in AVO variable metadata.
- Current safety guards reject REAL initializers and integer-path REAL variable
  reads/writes until REAL expression lowering exists.

## Object Emission

- Deterministic `AVO1` text object generation.
- Export metadata emission.
- `body_ops` emission.
- Literal-pool emission for the current narrow surface.
- Current runtime-import emission.
- Object-path generation to `OBJ/<MODULE>.AVO`.

## Proven Widening Already Landed

- Nested `IF` / `ELSE`.
- `WHILE ... DO ... OD`.
- `DO ... UNTIL ... OD`.
- Mixed arithmetic/comparison conditions.
- Current multi-variable integer state slice.
- Narrow module-scope `BYTE`/`CARD` and proc-local `BYTE` declaration slice.
- Module-scope `REAL` declaration storage-width slice.
- Current local/external integer arg/return slice.
- Current larger-object and larger-proc-size coverage proved through the harness.

## Remaining Work

## Immediate Stability Work

- Keep the restored `ACTC` save path green while other tool/runtime changes land.
- Preserve `vice-action-actc` and the chained `ACTC -> ALINK -> AVMRUN` proof as
  the first regression gates for compiler work.
- Remove temporary probe/debug noise once equivalent permanent diagnostics exist.

## Near-Term Compiler Work

- Widen diagnostics so save/load/parse failures are easier to localize without
  temporary probe code.
- Add more direct target-side proofs for the compiler save boundary, not just
  the integrated chain.
- Resume language-surface widening from a green real-target compiler baseline.

## Medium-Term Language Work

- Broaden expression lowering beyond the current proven narrow slice.
- Broaden statement coverage beyond the current branch/loop/call subset.
- Broaden stateful variable semantics beyond the current integer-only slice.
- Add full REAL32 lowering without AVM opcode growth: imports must be
  operator-specific runtime-library symbols, so `+`, `-`, `*`, `/`, compare,
  convert, and print support only link when used.
- Broaden procedure/function semantics beyond the current local/external integer path.

## Structural Work Still Outstanding

- Move proc-local integer storage from the current proc-scoped static-slot model toward a real frame/local model.
- Continue widening compatibility toward historical ACTION! source behavior.
- Improve compiler-oriented diagnostics and error reporting on the real target.

## Next Milestones

1. Keep `make -C ../udos vice-action-actc` green on the current working tree.
2. Keep `make -C ../udos vice-action-actc-alink-avmrun` green as the chained gate.
3. Widen REAL from declaration-only storage into typed expressions with
   per-operation runtime imports.
