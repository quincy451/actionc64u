# ActionC64U UDOS Resume

This repo currently contains two distinct layers.

## Legacy Reference

The existing `actc.com`, `alink.com`, `vm.com`, and `actmon.com` flow is the
older bootstrap/toolchain reference. It remains useful as:

- a language and runtime reference
- a source of examples and manifests
- a host-side regression target while the UDOS-native tools are built

It is not the target operating environment going forward.

## UDOS Target Boundary

The current target environment is UDOS.

That means:

- shell and resident services live in the `udos` repo
- Action development tools need UDOS-native entry points
- the old bootstrap binaries are reference implementations, not the final on-target
  tools

## First Bridge Artifact

The first bridge from this repo into UDOS is a UDOS-compatible workspace export.

`tools/export_udos_workspace.py` writes a tree that the current UDOS VICE tree
backend can mount and inspect. The export contains:

- `README.TXT` with the current bootstrap/UDOS status
- `DOC/` guides derived from the current repo docs
- `SRC/` sample `.ACT` source files
- `BIN/` sample `AVM1` binaries and source text
- `LIB/` packed `LIBMODS.DAT` plus source manifests

This does not make the old bootstrap tools runnable inside UDOS. It gives UDOS a
real Action workspace with guides, sample programs, and runtime assets while
the UDOS-native tool replacements are built.

The first UDOS-native external Action-side tool proofs now exist:

- `ACTDIR.PRG`
- `ACTADD.PRG`
- `ACT2SAVE.PRG`
- `ACTC.PRG`
- `ACTFLOW.BAT`
- `ACTNEW.BAT`
- `ACTNEW.PRG`
- `ACTSRC.PRG`
- `ACTFILE.PRG`
- `ACTWORK.PRG`
- `ACTMON.PRG`
- `ACTINFO.PRG`
- `ACTCOPY.PRG`
- `ACTDEL.PRG`
- `ACTMKDIR.PRG`
- `ACTMOVE.PRG`
- `ACTRMDIR.PRG`
- `ACTWRITE.PRG`
- `AVMINFO.PRG`
- `AVMRUN.PRG`

They are exported into `ACTION.DNP` root and `BIN/`.

- `ACTDIR.PRG` enumerates the current mounted directory through the preserved
  UDOS directory ABI and returns to the prompt.
- `ACTADD.PRG` validates `ACTION.PROJ` in the current directory, writes
  `SRC/<NAME>.ACT` through the preserved UDOS file-save ABI, and returns to the
  prompt. The current proof refuses duplicate module creation with `EXISTS`.
- `ACT2SAVE.PRG` validates `ACTION.PROJ`, requires the requested module to
  already be tracked in the current project manifest, rewrites `SRC/<NAME>.ACT`
  through the preserved UDOS file-save ABI, and reports whether the save
  created or updated the module file.
- `ACTC.PRG` is the first UDOS-native compiler front-end slice. The current
  proof validates `ACTION.PROJ`, requires a tracked module entry, verifies the
  corresponding `SRC/<NAME>.ACT` source exists, checks that the source
  `MODULE` header matches the requested module name, extracts top-level
  `PROC` exports, scans the loaded source text for the current runtime-call
  marker set, folds the current narrow decimal `PrintI` / `PrintIE`
  `+` / `-` / `*` / `/` expressions with inline spaces, simple precedence,
  parenthesized grouping, and simple `=` / `<` / `>` / `<=` / `>=` / `<>`
  comparisons before
  object emission, and emits a
  deterministic `OBJ/<NAME>.AVO` text object stub with `AVO1`,
  module/export/call/import metadata where each export carries compiled offset
  and size, plus compiler-emitted `body_ops` and a minimal local control-flow
  `payload_hex` skeleton (`CALL` local proc, `RET`) plus explicit
  `payload_bytes`. The older flat local `calls` list is no longer emitted
  because local body semantics now live in `body_ops`. The focused
  headless VICE proof is
  green through `make vice-action-actc`, with host-side verification of the
  generated object file because `OBJ/UDOSDIR.TXT` is not yet refreshed
  reliably enough for a stable shell-side `TYPE OBJ/...` proof. The current
  import list is inferred from simple source-pattern scanning, not a full
  parser or code generator.
- `ALINK.PRG` is now the first UDOS-native linker slice. The current proof
  loads deterministic `OBJ/<NAME>.AVO` object stubs, parses export, body,
  payload, and unresolved external symbol metadata, uses compiler-emitted
  export offset/size triplets instead of inferring procedure spans from the
  payload shape, seeds the local live set from the module entry proc instead
  of assuming export slot `0`, propagates the local body-op call graph,
  resolves the current widened small-object closure, and emits
  `BIN/<NAME>.AVM` on the host fs tree as direct binary `AVM1`. The focused
  headless VICE proof is green through `make vice-action-alink`, with
  host-side verification of the exact emitted `AVM1` bytes and proof that an
  unused local export is stripped from the final image. The direct typed
  `make vice-action-alink-avmrun` proof is now also green and executes the
  emitted artifact through `AVMRUN.PRG`, printing `HELLOWORLD`, `TOOL7`, and
  `12342` before returning to the UDOS prompt. The integrated typed
  `make vice-action-actc-alink-avmrun` proof is also green and runs a real
  compiled `MAIN.ACT` object through `ALINK` and `AVMRUN`, printing `HELLO`,
  `TOOL7`, and `10`. The current `ALINK.PRG` slice is still a narrow
  object/link pipeline rather than a full historical Action code generator.
- `ACTFLOW.BAT` is the first composite workspace flow proof. It exercises the
  preserved UDOS file write/copy/move/delete services through the existing
  Action-side proof tools, prints `ACTFLOW OK`, and returns to the prompt.
- `ACTNEW.BAT` is the first project skeleton workflow proof. It composes
  stable UDOS shell `MD`/`CD`/`COPY` commands with root-absolute template files to
  create `SRC/`, `BIN/`, `OBJ/`, `ACTION.PROJ`, `README.TXT`, and `MAIN.ACT`,
  prints `ACTNEW OK`, and leaves the shell in the new project directory.
- `ACTNEW.PRG` is the first non-trivial UDOS-native workspace tool proof. It
  uses the preserved directory and file-save services to create the same
  project skeleton, including `ACTION.PROJ`, directly from a native tool
  instead of routing through shell batch composition.
- `ACTSRC.PRG` uses the preserved UDOS file-load ABI to read `ACTION.PROJ` in
  the current project root, skips the project header line, prints the tracked
  source entries, and returns to the prompt.
- `ACTFILE.PRG` uses the preserved UDOS file-load ABI to validate
  `ACTION.PROJ`, resolve `SRC/<NAME>.ACT` inside the current project root, and
  print the requested source text back through the shell.
- `ACTWORK.PRG` uses the preserved directory and file-load services to inspect
  the current directory as an Action project/workspace, report whether
  `ACTION.PROJ` plus `SRC/`, `BIN/`, and `OBJ/` are present, and count the
  tracked source entries from the project manifest.
- `ACTMON.PRG` is the first UDOS-native monitor-style Action front end. The
  current proof dispatches `WORK`, `CHECK`, `SRC`, `FILE <NAME>`, `ADD <NAME>`,
  `DEL <NAME>`, `REN <OLD> <NEW>`, `COPY <OLD> <NEW>`, and `SAVE <NAME>`
  subcommands through one entry point while leaving the UDOS shell in charge
  of the prompt.
  `DEL <NAME>` updates `ACTION.PROJ` and removes host-backed `SRC/<NAME>.ACT`
  files through the preserved UDOS file-delete ABI on the current host-backed
  VICE tree path; `REN <OLD> <NEW>` now renames tracked `SRC/<OLD>.ACT`
  modules through the preserved UDOS file-rename ABI while updating
  `ACTION.PROJ`; `COPY <OLD> <NEW>` now duplicates tracked `SRC/<OLD>.ACT`
  modules through the preserved UDOS file-copy ABI while appending the new
  module to `ACTION.PROJ`; the combined UDOS proof still follows the validated
  delete/rename paths with shell-side `TYPE` checks and expects the old source
  path to report `NO SUCH FILE`. The earlier `WORK`/`CHECK` failure turned
  out to be a real launch-window overlap: `ACTMON.PRG` had grown past the
  current `$0900-$180F` safe region and was clobbering resident code at
  `$1810+`. `ACTMON` is now reduced back under that limit, so focused
  headless runs for `ACTMON WORK`, `ACTMON CHECK`, `ACTMON HELP`,
  `ACTMON SRC`, and `ACTMON FILE MAIN` are green again on seeded project
  roots. The later combined mutation sequence is also green again through
  `make vice-action-actmon` after moving the composite runner onto the
  generic mounted-tree probe path with a clean host-tree reseed before each
  phase attempt.
- Shared `ACTION.PROJ` helpers now live under
  `src/tools_udos/common/` and back `ACTADD`, `ACT2SAVE`, `ACTFILE`,
  `ACTSRC`, `ACTWORK`, and `ACTMON`, so manifest load/count/entry/path/save
  behavior no longer drifts tool-by-tool. The current shared layer now also
  includes common load/track/create guard helpers, manifest-walk,
  workspace-summary, project-integrity, save-mode/save-write, manifest
  commit/replace/rollback, and rename/copy transfer helpers used by
  `ACTADD`, `ACT2SAVE`, `ACTCHK`, `ACTFILE`, `ACTSRC`, `ACTWORK`, and
  `ACTMON`.
- `ACTCHK.PRG` now exists as a build/exported UDOS-native integrity checker
  for project roots marked by `ACTION.PROJ`. It validates expected workspace
  directories, probes tracked `SRC/<NAME>.ACT` entries, prints missing-source
  diagnostics, and reports `ACTCHK OK` or `ACTCHK BROKEN`. The focused
  healthy-project headless VICE proof is green again via
  `make vice-action-actchk`, including the current autoexec/script-mode
  control path. `ACTMON CHECK` now also has a focused Make target through
  `make vice-action-actmon-check`, while the broader combined `ACTMON`
  mutation proof is back on the green path through `make vice-action-actmon`.
- `ACTINFO.PRG` launches from the UDOS shell, prints through the preserved
  launch-safe UDOS external-tool ABI, and returns to the prompt through the
  UDOS-aware external program return trampoline.
- `ACTCOPY.PRG` copies a file in the current mounted workspace through the
  preserved UDOS file-copy ABI. The current host-backed VICE tree proof now
  includes nested `SRC/...` copies.
- `ACTDEL.PRG` deletes a file in the current mounted workspace through the
  preserved UDOS file-delete ABI and returns to the prompt. The current
  host-backed VICE tree proof now includes nested `SRC/...` deletes.
- `ACTMKDIR.PRG` creates a directory in the current mounted workspace through
  the preserved UDOS directory-mutation ABI and returns to the prompt.
- `ACTMOVE.PRG` renames a file in the current mounted workspace through the
  preserved UDOS file-rename ABI. The current host-backed VICE tree proof now
  includes nested `SRC/...` renames.
- `ACTRMDIR.PRG` removes an empty directory in the current mounted workspace
  through the preserved UDOS directory-mutation ABI and returns to the prompt.
- `ACTWRITE.PRG` writes a text file into the current mounted directory through
  the preserved UDOS file-save ABI and returns to the prompt.
- `AVMINFO.PRG` uses the preserved UDOS file-load service to read `HELLO.AVM`
  from the mounted Action workspace, validates the `AVM1` header, prints
  `AVM OK`, and returns to the prompt.
- `AVMRUN.PRG` executes a constrained flagged `AVM1` subset on top of
  AcheronVM. The current proof payloads are `UDOSHELLO.AVM`, which prints
  `UDOS AVM OK`, and `UDOSFLOW.AVM`, which proves `jump`, `call`, and `ret`
  by printing `UDOS AVM FLOW OK` and returning to the prompt.

## Immediate Follow-On Work

1. expand `AVMRUN.PRG` beyond the current flagged Acheron-backed proof subset
2. expand the preserved UDOS external-tool ABI beyond the current
   console/cmdline/exit/read/write/delete/directory proofs into richer workspace services
3. define the broader UDOS program ABI expected by Action tools
4. port compiler, linker, editor, and debugger behavior onto UDOS-native tools

## Current Practical Use

Today, the exported workspace is useful for:

- mounting under UDOS during VICE testing
- reading the operator and language guides from inside UDOS
- browsing sample Action and AVM assets from the shell
- staging reference runtime data for later UDOS-native tools

Progress tracking for this repo now lives in:

- [docs/action_matrix.md](/mnt/c/test/action/actionc64u/docs/action_matrix.md)
