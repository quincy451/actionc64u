# AcheronVM Notes for ActionC64U

## Register Model

From the local `../acheronvm/README.md`:

- Acheron registers are 16-bit, little-endian values stored in zeropage.
- The register file is a sliding window, so a callee can grow new registers
  without copying the caller's frame.
- `rP` is the implicit "prior" register used by many instructions.
- `mgrow`/`retm` preserve and restore window marks for call frames.

This matters for ActionC64U because it gives us a compact VM target with a
function-local register model that still maps efficiently onto 6502 zeropage.

## Native 6502 Interop

Acheron can execute inline with native 6502 code:

- `jsr acheron` enters VM mode and starts interpreting bytecode immediately
  after the `jsr`.
- `native` exits VM mode and resumes native 6502 execution at the next byte.
- `calln <addr>` invokes a native 6502 routine from Acheron bytecode.
- Per the local Acheron docs, `calln` saves and restores `.X` and `.Y`, and
  `.X` points at `rP` while the native subroutine runs.

For `vmhello`, the Acheron bytecode uses `calln` to reach a native routine that
prints through the CP/M-65 BDOS console interface.

## Planned ActionC64U Use

The current plan is:

- the Action-like compiler emits Acheron instruction bytes
- a CP/M-65 runner program loads those bytes and enters AcheronVM
- embedded/native helpers provide CP/M-65 services such as console output,
  file access, and later runtime hooks
- project-specific Acheron opcodes can be added later for REU access, overlays,
  and other machine-specific services

For now we are proving the smallest possible loop: embedded Acheron bytecode
inside a CP/M-65 program that can call back out to native 6502 code and print a
known string.

## VM Runner Direction

The next bootstrap step is a real CP/M-65 VM runner program:

- program name: `vm.com`
- input file format: `.avm`
- default input file: `main.avm`
- job: load the payload, validate its header, and enter AcheronVM at the file's
  entry offset

For the first file-based payloads we will keep the ABI narrow:

- payload bytes are raw Acheron instruction bytes
- entry offset is an offset into that payload
- the runner supplies any native helper routines needed by the demo programs
- later compiler/runtime work can expand this with relocation data, exports, and
  project-specific opcodes
