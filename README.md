# ActionC64U - Action! Commodore 64 Ultimate Edition

ActionC64U is a clean-room Action!-style toolchain project for the Commodore 64.

The current checked-in toolchain is still the older CP/M-65 bootstrap path. It
remains in the repo as a language/runtime reference and regression target while
the UDOS-native tool replacements are built.

The current alpha ships:

- `alink.com`: on-target dead-strip linker for `.avo` objects
- `actc.com`: on-target compiler
- `vm.com`: VM runner for `.avm` payloads
- `actmon.com`: monitor-style front end
- dead-strip linkable runtime modules
- REAL, REU, and overlay bootstrap support
- a reproducible C64 release disk image plus VICE verification

## Prerequisites

Required local sibling trees:

- `../cpm65-u64`
- `../acheronvm`

Required host tools:

- `python3`
- `git`
- `make`
- a C compiler and C++ compiler
- `pytest`
- `llvm-mos` with `mos-cpm65-clang`

The repo also carries a minimal `pytest` shim for constrained environments, but
a normal `pytest` install is still recommended.

Release-image and C64 verification tools:

- `cpmtools` (`cpmcp`, `cpmls`, `cpmchattr`)
- `x64sc` from VICE for automated C64 validation

Quick environment check:

```sh
./tools/env_check.sh
```

Strict required-dependency check:

```sh
./tools/env_check.sh --strict
```

WSL setup notes live in [docs/setup_wsl.md](/mnt/c/test/action/actionc64u/docs/setup_wsl.md).

## Host Tests

Run the full host-side suite:

```sh
python3 -m pytest -q
```

This covers:

- host compiler/linker behavior
- CP/M-65 `cpmemu` integration
- on-target `actc.com` / `vm.com` flows under `cpmemu`
- release-image build checks
- VICE verification when `x64sc` is installed

## Build CP/M Tools

Build the shipped CP/M executables:

```sh
./tools/build_alink.sh
./tools/build_actc.sh
./tools/build_vmrun.sh
./tools/build_actmon.sh
```

Or use the one-command build:

```sh
./tools/build_all.sh
```

`build_all.sh` does not run `sudo`. If a dependency is missing, it fails with
instructions and points back to `./tools/env_check.sh`.

## Build The Release Disk Image

Build the distributable C64 CP/M-65 disk image:

```sh
python3 tools/build_release_image.py
```

Output:

- `build/actionc64u_c64.d64`
- `build/actionc64u_c64.dir.txt`

The build output directory is ignored by git, so generated release images stay
out of version control.

## Export A UDOS Workspace

Build a UDOS-compatible Action workspace tree with guides, sample sources,
sample `AVM1` payloads, and runtime manifests:

```sh
python3 tools/export_udos_workspace.py
```

Default output:

- `build/udos-action-fs/IMAGES/ACTION.DNP`

This export is the current bridge artifact from the bootstrap Action repo into
the UDOS shell/runtime.

## Run Automated VICE Verification

Run the release verification harness:

```sh
python3 tools/verify_release.py
```

This:

- builds or reuses the release image
- injects a host-built `HELLO.AVM`
- injects `$$$.SUB` so CP/M autoruns `VM HELLO.AVM`
- waits for `HELLO FROM ACTIONC64U` on the C64 screen
- writes `build/verify_transcript.txt`

The automated VICE path uses CP/M submit-file autorun because that is more
reliable than live post-boot keyboard typing on this target.

## One-Command Smoke Pass

For a quick end-to-end sanity check:

```sh
./tools/smoke.sh
```

This runs:

- `env_check`
- `pytest`
- release-image build
- optional VICE verification when `x64sc` is available

## Documentation Map

Key docs:

- [docs/cpmemu.md](/mnt/c/test/action/actionc64u/docs/cpmemu.md)
- [docs/vice.md](/mnt/c/test/action/actionc64u/docs/vice.md)
- [docs/spec.md](/mnt/c/test/action/actionc64u/docs/spec.md)
- [docs/linker.md](/mnt/c/test/action/actionc64u/docs/linker.md)
- [docs/real32.md](/mnt/c/test/action/actionc64u/docs/real32.md)
- [docs/reu.md](/mnt/c/test/action/actionc64u/docs/reu.md)
- [docs/overlays.md](/mnt/c/test/action/actionc64u/docs/overlays.md)
- [docs/disk_layout.md](/mnt/c/test/action/actionc64u/docs/disk_layout.md)
- [docs/release.md](/mnt/c/test/action/actionc64u/docs/release.md)
- [docs/action_matrix.md](/mnt/c/test/action/actionc64u/docs/action_matrix.md)
- [docs/udos_resume.md](/mnt/c/test/action/actionc64u/docs/udos_resume.md)
- [docs/blockers.md](/mnt/c/test/action/actionc64u/docs/blockers.md)
- [docs/prompt_chain.md](/mnt/c/test/action/actionc64u/docs/prompt_chain.md)

## Prompt Chain

The repo was built through `prompt-1.txt` through `prompt-18.txt` from the
workspace root. The workflow is documented in
[docs/prompt_chain.md](/mnt/c/test/action/actionc64u/docs/prompt_chain.md).
