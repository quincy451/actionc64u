# `ALINK` Roadmap

Current as of `2026-04-20`.

This is the short planning document for the UDOS-native Action linker, `ALINK.PRG`.
For the detailed proof ledger, see [alink_status.md](./alink_status.md).
For object-format context, see [linker.md](./linker.md).

## Current Position

Committed baseline:

- `ALINK.PRG` launches from a UDOS Action workspace.
- It loads deterministic `AVO1` objects from `OBJ/`.
- It emits deterministic `AVM1` binaries to `BIN/<MODULE>.AVM`.
- `ALINK -> AVMRUN` is proven.
- `ACTC -> ALINK -> AVMRUN` is also proven on the committed Linux `VICE 3.7.1` line.

Current working-tree verification:

- The previous upstream `ACTC` save regression has been cleared on the current
  UDOS line.
- Standalone `ALINK` is green again on the current working tree.
- `ALINK -> AVMRUN` is green again on the current working tree.
- `ACTC -> ALINK -> AVMRUN` is green again on the current working tree.
- Linker work can move back from rescue verification to object/link-surface
  widening.

## Accomplished

## Tool And Runtime Integration

- Stable UDOS packaging on release media as `ALINK.PRG`.
- Stable `A:` release-tool launch path on the committed baseline.
- `AVMRUN.PRG` is packaged on release media, which keeps chained linker/runtime proofs off the weaker host-tree PRG launch path.
- Seeded `ALINK` and chained `ALINK -> AVMRUN` probes are stabilized on the committed baseline.

## Linker Core

- `AVO1` object loading from `OBJ/`.
- Parsing of export metadata.
- Parsing of `body_ops`.
- Parsing of unresolved external symbol lines.
- Parsing of integer and string literal pools.
- Use of compiler-emitted procedure sizes to recover procedure boundaries.
- Live-set construction from the requested module entry.
- Deterministic child-object loading across the current narrow dependency closure.

## Output Generation

- Deterministic `AVM1` binary emission to `BIN/<MODULE>.AVM`.
- Narrow exact-byte proof for emitted output.
- Proven handoff to `AVMRUN` on the real target.
- Proven chained handoff from compiler output on the committed baseline.

## Proven Widening Already Landed

- Larger object files beyond the old `255`-byte ceiling.
- Larger payloads beyond the old `255`-byte payload ceiling.
- Larger procedure sizes past `255` bytes.
- Deeper child-object closure than the old small-graph limit.
- Current loop/control-flow/body-op slice emitted by the widened compiler.
- Narrow `BYTE`/`CARD` compiler declaration output through the existing
  16-bit variable slot path.
- Optional variable-width metadata for compiler-emitted data, currently proving
  4-byte module-scope `REAL` storage.

## Remaining Work

## Immediate Stability Work

- Keep standalone `ALINK` green while compiler and runtime changes continue.
- Keep `ALINK -> AVMRUN` and `ACTC -> ALINK -> AVMRUN` as the first chained
  regression gates.
- Continue reducing probe-specific noise so linker failures are easier to
  separate from boot/mount noise.

## Medium-Term Linker Work

- Broaden supported object-graph shapes and external-resolution patterns.
- Broaden body-op coverage as `ACTC` widens.
- Broaden data/variable support beyond the current integer-centered slice.
- Add REAL runtime-module resolution as operator-specific link inputs rather
  than AVM opcode growth or one monolithic REAL blob.
- Broaden procedure/function semantics as compiler output becomes richer.

## Structural Work Still Outstanding

- Move beyond the current narrow dead-strip model toward fuller historical behavior.
- Improve map/debug output so linker decisions are easier to inspect on target.
- Keep object format, linker expectations, and compiler emission aligned as the compiler widens.

## Dependency Note

- The linker still depends on stable compiler object emission.
- That dependency is currently green again, so the next meaningful linker work
  can widen object-graph and body-op coverage instead of chasing the prior
  save-path blocker.

## Next Milestones

1. Keep `make -C ../udos vice-action-alink` green.
2. Keep `make -C ../udos vice-action-alink-avmrun` and `vice-action-actc-alink-avmrun` green.
3. Wire REAL runtime lookup so only used REAL operators are pulled into the
   linked AVM image.
