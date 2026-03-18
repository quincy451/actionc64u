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
- `ACTFLOW.BAT`
- `ACTNEW.BAT`
- `ACTNEW.PRG`
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
  prompt. The current proof is create-or-replace, not overwrite-protected.
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
- `ACTINFO.PRG` launches from the UDOS shell, prints through the preserved
  launch-safe UDOS external-tool ABI, and returns to the prompt through the
  UDOS-aware external program return trampoline.
- `ACTCOPY.PRG` copies a file in the current mounted workspace through the
  preserved UDOS file-copy ABI. Success is validated by shell-side readback of
  the copied file after return.
- `ACTDEL.PRG` deletes a file in the current mounted workspace through the
  preserved UDOS file-delete ABI and returns to the prompt.
- `ACTMKDIR.PRG` creates a directory in the current mounted workspace through
  the preserved UDOS directory-mutation ABI and returns to the prompt.
- `ACTMOVE.PRG` renames a file in the current mounted workspace through the
  preserved UDOS file-rename ABI. Success is validated by shell-side readback
  of the renamed file after return.
- `ACTRMDIR.PRG` removes an empty directory in the current mounted workspace
  through the preserved UDOS directory-mutation ABI and returns to the prompt.
- `ACTWRITE.PRG` writes a text file into the current mounted directory through
  the preserved UDOS file-save ABI and now supports small template modes used
  by `ACTNEW.BAT`.
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
