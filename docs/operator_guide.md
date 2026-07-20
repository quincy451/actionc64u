# Operator Guide

Current UDOS-native workflow:

1. Put source in `SRC/<MODULE>.ACT`.
2. Run `ACTC <MODULE>`.
3. Run `ALINK <MODULE>`.
4. Launch `BIN/<MODULE>.PRG` under UDOS.

The linked PRG is the final runnable program.

From `ACTEDIT <MODULE>`:

- `Ctrl-O` saves and compiles
- `Ctrl-B` saves, compiles, and links
- `Ctrl-D` saves, compiles, links, and enters ACTDBG

The workflow uses trailing `,` and `:` command markers internally so the full
24-character module-name limit still fits the UDOS command line. Each tool
queues the next ordinary PRG only after its own output succeeds.

Optional Idun/Linux host workflow:

1. Build with `bash tools/build_linux_tools.sh`.
2. Run `build/linux_tools/actc <MODULE>` in an Action project.
3. Run `build/linux_tools/alink <MODULE>` to emit `BIN/<MODULE>.PRG` and the
   debugger sidecar.
4. Use `actedit ... index/find/symbols` and
   `actdbg ... source/line/symbols/break/breaks/clear` for host-side metadata.

Prepared host breakpoints are not live C64 control. Installing breakpoints,
stepping, and reading registers or memory still require a C64-side agent or an
equivalent Idun control protocol.
