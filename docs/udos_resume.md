# ActionC64U UDOS Resume

This repo currently contains two distinct layers.

## Bootstrap Reference

The existing `actc.com`, `alink.com`, `vm.com`, and `actmon.com` flow is the
older CP/M-65 bootstrap/toolchain path. It remains useful as:

- a language and runtime reference
- a source of examples and manifests
- a host-side regression target while the UDOS-native tools are built

It is not the target operating environment going forward.

## UDOS Target Boundary

The current target environment is UDOS, not CP/M-65.

That means:

- shell and resident services live in the `udos` repo
- Action development tools need UDOS-native entry points
- the old CP/M binaries are reference implementations, not the final on-target
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

This does not make the old CP/M tools runnable inside UDOS. It gives UDOS a
real Action workspace with guides, sample programs, and runtime assets while
the UDOS-native tool replacements are built.

## Immediate Follow-On Work

1. add a UDOS-native VM runner for `AVM1` payloads
2. define the UDOS program ABI expected by Action tools
3. replace CP/M-specific file/process assumptions in the toolchain surface
4. port compiler, linker, editor, and debugger behavior onto UDOS-native tools

## Current Practical Use

Today, the exported workspace is useful for:

- mounting under UDOS during VICE testing
- reading the operator and language guides from inside UDOS
- browsing sample Action and AVM assets from the shell
- staging reference runtime data for later UDOS-native tools

Progress tracking for this repo now lives in:

- [docs/action_matrix.md](/mnt/c/test/action/actionc64u/docs/action_matrix.md)
