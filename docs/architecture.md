# Architecture

ActionC64U is now a UDOS-native Action-style toolchain.

Active flow:

- `ACTC.PRG` compiles source into `OBJ/*.OBJ` object files.
- `ALINK.PRG` resolves the object closure and emits `BIN/<MODULE>.PRG`.
- UDOS launches the linked PRG directly.

The linked PRG must contain the entry path, selected runtime helpers, and all
program-owned code/data needed for execution. A separate runtime host is not
part of the maintained architecture.

An optional Idun/Linux host implementation under `src/tools_linux/` performs
project, compile, link, editor-index, and debugger-sidecar work on the
cartridge's Raspberry Pi. It preserves the same target boundary: the output is
a direct C64 `.PRG`, standalone 6502 helpers are selected only when referenced,
and Linux/SQLite state is never a target runtime dependency.

Its linker consumes the native machine OBJ1 format, discovers closure by
exports across project and library objects, rejects duplicate providers, and
translates canonical object source records into the linked DBG1 sidecar.

The host compiler lowers `BYTE`/`CARD`/`INT`/`REAL` arrays, typed pointers,
local-routine parameters, and typed user-function returns to ordinary linked
storage, register results, and indirect 6502 operations. Host syntax and symbol
metadata is dynamically sized; target data and addresses retain C64 limits.
