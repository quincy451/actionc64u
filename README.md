# ActionC64U - Action! Commodore 64 Ultimate Edition

ActionC64U is a clean-room Action!-style toolchain project for the Commodore 64.

The active project path is UDOS-native. Action tools are built as standalone
`.PRG` programs that run under the sibling `../udos` shell/runtime and use the
UDOS resident service layer to reach Commodore 64 Ultimate ROM/Ultimate DOS
services.

Retired CP/M-65 notes remain only where explicitly labeled as historical
documentation. They are not an active implementation target and should not drive
feature work. See [docs/active_direction.md](./docs/active_direction.md).

The current UDOS-facing alpha ships:

- `ALINK.PRG`: UDOS-native linker; the default live gate now emits direct `.PRG` output
- `ACTC.PRG`: UDOS-native compiler front end
- core `ASMBLOCK [ ... ]` inline NMOS 6502 assembly with local labels and
  relocatable global/parameter/local references, including `#<`/`#>` addresses
- raw `[ ... ]` machine-code bodies for fixed register-entry routines, with
  byte/word/character constants and ordinary OBJ1 address relocations
- `ACTDBG.PRG`: native source debugger for ALINK-linked `.PRG` output
- `ACTMON.PRG`: monitor-style front end
- workspace/project helper tools under `src/tools_udos/`
- dead-strip linkable runtime modules
- a reproducible UDOS release/workspace image plus VICE verification

## Prerequisites

Required local sibling trees:

- `../udos`

Required host tools:

- `python3`
- `git`
- `make`
- a C compiler and C++ compiler
- `pytest`
- `cc65` tools for UDOS `.PRG` assembly

The optional Idun/Linux host tools additionally require `pkg-config` and the
SQLite 3 development package.

The host 6502 execution harness uses the MIT-licensed `lib6502` sources vendored
under `third_party/lib6502`; no retired sibling tree is a build dependency.

The repo also carries a minimal `pytest` shim for constrained environments, but
a normal `pytest` install is still recommended.

Release-image and C64/VICE verification tools:

- `c1541`
- `x64sc` from VICE for automated C64 validation

Quick environment check:

```sh
./tools/env_check.sh
```

Strict required-dependency check:

```sh
./tools/env_check.sh --strict
```

WSL setup notes live in [docs/setup_wsl.md](docs/setup_wsl.md).

## Active UDOS Verification

Use the sibling UDOS repo as the source of truth for current development:

```sh
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-actc
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-alink
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-actc-alink-launch
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-actc-alink-launch-object-emission-matrix
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-alink-prg-matrix
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-alink-prg-object-code-matrices
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-actc-alink-launch-runtime-matrices
make -C ../udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-actc-alink-launch-printmath
```

These gates build the UDOS release image, install the Action `.PRG` tools, boot
UDOS under VICE, and validate the real tool path. The helper-free higher-level
default is:

```text
ACTC.PRG -> ALINK.PRG -> MAIN.PRG
```

ALINK also writes `BIN/MAIN.DBG`. It is used only when launching
`ACTDBG.PRG MAIN`; normal execution remains the linked `MAIN.PRG` itself.

The lower-level default linker gate is `make -C ../udos vice-action-alink`,
which now verifies `ALINK.PRG -> BIN/MAIN.PRG`.
The broad linker matrix is `make -C ../udos vice-action-alink-prg-matrix`,
which currently enumerates 1372 direct-PRG object/link shapes.
The non-runtime source-backed matrix contains 196 native ACTC/ALINK/VICE
shapes, including canonical and permuted-storage versions of the shared finite
two-REAL-parameter comparison fixture plus a reordered second-parameter return
fixture, a nested REAL function-call fixture, its REAL-local extension, and the
two-function call-chain, nested local-call-expression, nested user-call-argument,
frame-preserved forward-call, bounded single/two/four-control forms,
conditional early-return extensions through depth four, bounded REAL-function
`DO ... UNTIL`/`WHILE ... DO` loops, plain/guarded nearest-loop `EXIT`, and
constant-bound positive/negative-step CARD-counter `FOR` loops, nested loops
whose initial or final bound is a named CARD value, and one-parameter MATH1
angle conversions with folded binary32 constants in `tests/parity`.
The MATH1 runtime matrix additionally launches link-selected `FSign`, `FTrunc`, `FFloor`, `FCeil`, `FRound`, `FFrac`, `FMod`, `FHypot`, `FPow`, `FExp`, `FLn`, `FSin`,
`FLog2`, `FLog10`, `FMin`, `FMax`, and canonical plus permuted-storage `FClamp` programs and verifies that
each prunes unreferenced helpers.

## Build UDOS Tools

Build individual UDOS-native tools:

```sh
./tools/build_actc_udos.sh
./tools/build_alink_udos.sh
./tools/build_actdbg_udos.sh
./tools/build_actmon_udos.sh
./tools/build_acttree_udos.sh
./tools/build_xcopy_udos.sh
./tools/build_deltree_udos.sh
```

The outputs are written under `build/udos_tools/`. `build_acttree_udos.sh`,
`build_xcopy_udos.sh`, and `build_deltree_udos.sh` emit the UDOS command modules
`TREE.OVL`, `XCOPY.OVL`, and `DELTREE.OVL`; the Action compiler and linker remain
direct `.PRG` tools.


## Host Tests

Run the full host-side suite:

```sh
python3 -m pytest -q
```

This covers:

- UDOS workspace export checks
- VICE verification when `x64sc` is installed
- UDOS-native compiler/linker overlay and capacity checks

Host tests are useful, but they are not the current target proof. UDOS VICE
gates above are authoritative for current toolchain work.

## Optional Idun/Linux Host Tools

The same project tree includes Linux-native workspace, compiler, linker,
editor-index, and debugger-sidecar commands for the Raspberry Pi side of an
Idun cartridge. This is an additional host-development path; it does not replace
the maintained UDOS tools. Host `alink` still emits a direct C64 `.PRG` with
only referenced 6502 runtime modules and no separate runtime runner.

Host `alink` consumes the native machine-code OBJ1 records emitted by the UDOS
compiler, including canonical `f`/`q`/`L`/`V` source-debug metadata. Dependency
lookup first uses conventional object names, then scans project and library
objects by exported symbol. A selected malformed object or multiple providers
for one export is rejected rather than linked nondeterministically.
Reachability is export-body-specific: only selected byte ranges, relocations,
and imports enter the final PRG. OBJ1 import references use one-character
indexes (`0`-`9`, then `A`-`Z`); lowercase letters are accepted on input.

The Linux compiler path supports dynamically sized metadata for
`BYTE`/`CARD`/`INT`/`REAL` arrays, typed pointers and indirect parameters, and
typed `BYTE`/`CARD`/`INT`/`REAL FUNC` declarations. Function calls participate
in word and REAL expressions. Local-call edges in direct or mutual recursion
preserve mutable scalar parameters, scalar locals, and compiler temporaries on
the 6502 hardware stack. Recursion depth is stack-bounded; local array storage
remains shared, and asynchronous or general reentry remains unsupported.

```sh
bash tools/build_linux_tools.sh
python3 -m unittest -v tests.test_linux_workspace_tools
python3 -m unittest -v tests.test_idun_workspace_export
python3 tools/export_idun_workspace.py
```

The default export is `build/idun-action/`. See
[docs/idun_linux_process_split.md](docs/idun_linux_process_split.md) for the
host/target boundary and current limitations.

## Export A UDOS Workspace

Build a UDOS-compatible Action workspace tree with guides and sample sources:

```sh
python3 tools/export_udos_workspace.py
```

Default output:

- `build/udos-action-fs/IMAGES/ACTION.DNP`

This export is the current bridge artifact from the Action tool repo into the
UDOS shell.

## Removed Legacy Paths

The older host VM compiler/linker, CP/M runner, and legacy CP/M release-image
scripts have been removed. The maintained target path is the UDOS-native
toolchain and direct `.PRG` output from `ALINK.PRG`.

## Documentation Map

Key current docs:

- [docs/idun_feature_parity.md](docs/idun_feature_parity.md)
- [docs/actc_roadmap.md](docs/actc_roadmap.md)
- [docs/alink_roadmap.md](docs/alink_roadmap.md)
- [docs/source_debugger_roadmap.md](docs/source_debugger_roadmap.md)
- [docs/idun_linux_process_split.md](docs/idun_linux_process_split.md)
- [docs/active_direction.md](docs/active_direction.md)
- [docs/real32.md](docs/real32.md)
- [docs/new_math_func.txt](docs/new_math_func.txt)
- [docs/new_gfx_func.txt](docs/new_gfx_func.txt)
- [docs/reu.md](docs/reu.md)
- [docs/disk_layout.md](docs/disk_layout.md)
- [docs/release.md](docs/release.md)
- [docs/action_matrix.md](docs/action_matrix.md)
- [docs/udos_resume.md](docs/udos_resume.md)
- [docs/blockers.md](docs/blockers.md)
- [docs/prompt_chain.md](docs/prompt_chain.md)

## Prompt Chain

The repo was built through `prompt-1.txt` through `prompt-18.txt` from the
workspace root. The workflow is documented in
[docs/prompt_chain.md](docs/prompt_chain.md).
