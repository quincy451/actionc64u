# ActionC64U Roadmap

## Phases

### Phase A
Host harness + CP/M user-mode emulation (`cpmemu`).

### Phase B
Integrate AcheronVM and run bytecode programs.

### Phase C
Minimal Action compiler (host reference compiler first).

### Phase D
Language expansion + dead-strip linker.

### Phase E
REAL32 implementation.

### Phase F
REU + overlays (simulated first, then VICE validation).

### Phase G
Release disk image (C64 CP/M-65) with tools + examples + automated verification.

## Progress Log (Append-Only)

- 2026-03-03: Bootstrap repository created with initial structure, docs seeds, inspiration copy script, and smoke tests.
- 2026-03-06: Added WSL2 environment probe/setup scripts, local path validation, and non-destructive tooling tests.
- 2026-03-06: Added a cpmemu runner, CP/M-65 build notes, and skip-aware host harness tests for adjacent cpm65-u64 builds.
- 2026-03-06: Added a hello.com smoke program, ABI notes, and a build path that prefers native CP/M-65 ASM with llvm-mos fallback.
- 2026-03-06: Added AcheronVM planning docs, a staged vmhello proof source, and blockers-aware build/test plumbing for the VM backend.
- 2026-03-06: Defined the versioned `.avm` file format, added a host packer, and staged the file-based vm.com runner/test path.
- 2026-03-06: Added a minimal Action-like compiler for Print/PrintE, plus a VM ABI doc and compiler-to-.avm smoke test path.
- 2026-03-06: Expanded the host reference compiler with BYTE/CARD/INT declarations, expressions, IF, and integer printing, plus compile-time output tests for `math.act` and `if.act`.
- 2026-03-06: Added the text-based `.avo` object format, a deterministic dead-strip linker with map output, and linkable bootstrap runtime modules for print helpers and integer formatting.
- 2026-03-06: Added REAL32 syntax/semantics, logical float runtime modules, and host-side REAL compile/link/output tests while keeping float-free programs dead-stripped.
- 2026-03-06: Added simulated REU declarations/peek/poke support, a minimal overlay block/call flow, overlay packing in the linker, and host-side tests for both features.
- 2026-03-06: Added a skip-aware VICE harness using the binary monitor plus a C64 CP/M boot smoke test path that activates when `x64sc` and a `c64*.d64` image are available.
