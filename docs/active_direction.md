# Active Project Direction

This project has pivoted away from CP/M-65 as an execution target.

The active product path is:

- UDOS as the standalone Commodore 64 Ultimate shell/runtime
- Action tooling as UDOS-aware `.PRG` programs
- C64 Ultimate ROM/Ultimate DOS services through the UDOS resident service layer
- direct linked `.PRG` output as the only maintained runtime artifact

The active code paths are:

- `../udos/src/asm/udos_resident.asm`
- `../udos/tools/run_action_*.py`
- `src/tools_udos/`
- `tools/build_*_udos.sh`
- `tools/export_udos_workspace.py`

The CP/M-65 compiler/linker/bootstrap code and the old VM toolchain have been
removed. Repository code should not add new runtime-runner flows. Action-linked
programs now target direct 6502 `.PRG` output, and the UDOS resident shell is
native 6502 rather than a VM bytecode host.

## Optional Idun/Linux Host Path

`src/tools_linux/action_workspace_tools.cpp` provides Linux-native project,
compiler, linker, editor-index, and debugger-sidecar commands for the Raspberry
Pi side of an Idun cartridge. `tools/export_idun_workspace.py` packages those
commands with standalone link-selected 6502 modules. This path is additive: it
does not replace the UDOS-native C64 tools or their verification gates.

Host `alink` must preserve the same product boundary as `ALINK.PRG`: its output
is a self-contained direct C64 `.PRG`, and only referenced 6502 helpers enter
the link. SQLite is host-only workspace/debug metadata and never enters the C64
program.

Host execution tests build the vendored `third_party/lib6502` source. No active
compiler, linker, setup, or verification path depends on a retired sibling
toolchain tree.

Common target runtime modules are owned by this native repository and recorded
in `resources/shared_6502_manifest.json`. Run
`tools/shared_6502_sync.py --write-manifest` after an intentional common 6502
change, then use its peer check and the Idun `make sync-native` target to update
the Linux fork. The two documented DBF create/open adapters remain
OS-specific; all other target modules are shared.

The host linker accepts canonical native OBJ1 machine and debug records shared
with the UDOS compiler. It resolves dependencies by exported symbol even when a
library filename differs from that symbol, preserves `f`/`q`/`L`/`V` records in
the linked DBG1 sidecar, and rejects malformed selected objects or ambiguous
export providers.
It places only reachable export ranges, follows only their body imports and
relocations, and accepts the canonical single-character `u0` through `uZ`
import-index encoding (including lowercase letter input).

Linux `actc` currently covers `BYTE`/`CARD`/`INT`/`REAL` arrays, typed pointers
and indirect parameters, and typed user-function returns. The compiler metadata
for these forms is dynamically sized. The compiler identifies local call edges
that participate in direct or mutual recursion, spills each caller's mutable
scalar parameter, local, and compiler-temporary cells to the 6502 hardware stack,
and restores them around the call. Recursion depth is stack-bounded. Local array
storage remains shared, while asynchronous or general reentry remains host-path
work.

Focused host verification is:

```sh
bash tools/build_linux_tools.sh
python3 -m unittest -v tests.test_linux_workspace_tools
python3 -m unittest -v tests.test_idun_workspace_export
```

## Cross-Product Feature Parity

Parity with the Idun/Alpine fork is measured at the Action language, library,
OBJ1, linked-PRG, runtime-result, and user-workflow boundaries. Linux C++,
SQLite, sockets, and APK packaging are not copied into UDOS; native tools use
6502 overlays, REU workspace, UDOS filesystem services, and release images.

Direct PRG linking, OBJ1 closure, ordinary ASMBLOCK composition, comment-
prefixed modules, the fixed register-entry `=*(...)` ABI, IEEE-754 core
behavior, INPUT1, DBF1, SIDSPR1, and source debugging have native equivalents.
Core raw fixed-routine byte blocks plus numeric-expression and linked-local
absolute-address routine declarations now have native object/link/live coverage.
Native `REAL CONST` expressions now fold to binary32 with exact decimal
conversion and nearest-even intermediate rounding. Pass K proves one finite
two-REAL-parameter comparison/select function through generic OBJ1/ALINK/VICE.
Bounded named-REAL `FSign`, `FMin`, `FMax`, and `FClamp` calls now have
complete portable call semantics through independently link-selected helpers.
The pass-K clamp root captures initializer, argument, destination, and print
storage rather than assuming declaration order, but it remains a fixed
three-initializer/one-call/one-print skeleton rather than a general expression
parser.
Remaining source parity includes general arrays/pointers/records, nested and
recursive typed functions, and complete REAL expression/call/return behavior.
Complete portable MATH1 follows, then
graphics-resource declarations, expanded GFX1, native resource editors, and
UDOS equivalents for formatting/help conveniences. The detailed matrix and
ordered implementation plan are in `docs/idun_feature_parity.md`.

## Active Verification Gates

Use UDOS gates as the source of truth:

```sh
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-actc
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-alink
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-actc-alink-launch
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-actc-alink-launch-object-emission-matrix
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-alink-prg-matrix
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-alink-prg-object-code-matrices
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-actc-alink-launch-runtime-matrices
```

Treat `vice-action-alink` as the default direct-native linker gate that emits
`BIN/MAIN.PRG`.
Treat `vice-action-actc-alink-launch` as the helper-free higher-level default.
Treat `vice-action-actc-alink-launch-object-emission-matrix` as the all
source-backed ACTC object-emission launch matrix; it currently enumerates 171
non-runtime, non-object-code source shapes.
Treat `vice-action-alink-prg-matrix` as the broad direct-PRG object/link matrix;
it currently enumerates 1332 shape probes.
Treat `vice-action-alink-prg-object-code-matrices` as the focused direct
object-code graph, behavior, and rejection gate.
Treat `vice-action-actc-alink-launch-runtime-matrices` as the focused
link-selected runtime helper gate, including exported helper demo programs via
`vice-action-actc-alink-launch-helper-demos`.
Treat `vice-action-actc-alink-launch-printmath` as a green named direct
launch gate for the imported `printmath` shape.

Use narrower UDOS gates when working on a specific tool:

```sh
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-actadd
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-act2save
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-actcopy
```

## Development Rules

- Prefer `src/tools_udos` over deleted CP/M-era compiler/linker paths.
- Prefer `tools/build_*_udos.sh`; do not reintroduce CP/M `.COM` build scripts.
- Do not treat `cpmemu` success as proof that the active target works.
- Do not add new CP/M or runtime-runner features.

## Current Design Inputs

Optional runtime/library work should follow the link-selected helper direction:
helpers are selected by the linker and carried by the final `.PRG`, not by a
separate runtime program.

Current concrete API inputs:

- graphics/resource datatype direction:
  - `docs/graphics_ideas.txt`
- SID and sprite helper direction:
  - `docs/sid_and_sprite_ideas.txt`
- first Action-facing math binding sketch:
  - `docs/math1_bindings_draft.act`
- DBF-style database API sketch:
  - `docs/dbf_test.c`
- concrete helper-family ABI draft:
  - `docs/helper_family_abi_draft.md`
- first Action-facing SID/sprite binding sketch:
  - `docs/sidspr1_bindings_draft.act`
- first Action-facing joystick/mouse input binding sketch:
  - `docs/input1_bindings_draft.act`

These are design inputs for optional helper families. They should not be
implemented as permanent runner-global features.

## Current Next Work

The current practical path is:

1. Generalize native REAL declarations, frames, expressions, calls, and returns
   enough to compile the portable multi-function MATH1 source.
2. Port MATH1 as dependency-sized OBJ modules and prove ALINK includes only
   referenced functions.
3. Widen arrays, pointers, records, typed calls, and recursive frames where
   portable programs require them, with explicit C64/REU bounds.
4. Map portable `MAIN(argc,argv)` to UDOS command-tail storage after native
   arrays are available; do not copy the Idun upload transport.
5. Add application `REU BYTE ARRAY` lowering and program-owned source
   `OVERLAY` sections; neither is the same as ACTC's internal REU/pass overlays.
6. Implement ASP1/ABM1-backed `SPRITE`, `MSPRITE`, `BITMAP`, and `MBITMAP`
   declarations with relocatable embedded data.
7. Port expanded GFX1 groups, then implement native ACTSPRITE/ACTBITMAP and
   ACTEDIT F8 resource dispatch.
8. Add UDOS-appropriate formatting/help workflow parity and retain ACTDBG as
   the native debugging path; profiling remains an optional product decision.
9. Keep all helper families link-selected and all ACTC/ALINK direct-PRG,
   release-image, and VICE gates green as each slice lands.
10. Finish with physical C64U display, SID, input, REU, and disk validation.
