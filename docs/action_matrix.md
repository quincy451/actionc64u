# ActionC64U Tool And Feature Matrix

This file tracks the Action-side development surface as the project moves from
legacy bootstrap references toward UDOS-native tools.

Legend:

- `Yes`: implemented and usable in that column's environment
- `Partial`: exists, but incomplete or only usable as a bridge/reference
- `No`: not implemented
- `Planned`: explicitly intended, but not started yet

## Tool Matrix

| Tool | Legacy Reference | UDOS Workspace Export | UDOS-Native Tool | Planned | Notes |
|---|---:|---:|---:|---:|---|
| `ACTC` compiler | Yes | No | No | Yes | Current compiler is only a legacy bootstrap reference. |
| `ALINK` dead-strip linker | Yes | No | No | Yes | Current linker exists only as a legacy bootstrap reference. |
| `ACTINFO` tool proof | No | Yes | Yes | N/A | First UDOS-native external Action-side tool proof. It launches from `ACTION.DNP`, prints through the preserved launch-safe UDOS ABI, and returns to the UDOS prompt. |
| `VM` `AVM1` runner | Yes | Sample payloads only | No | Yes | The bridge exports sample `.AVM` assets, but no UDOS-native runner exists yet. |
| `ACTMON` front end | Yes | No | No | No | Historical bootstrap front end only. UDOS already owns the shell role. |
| Integrated editor | No | Guides only | No | Yes | No UDOS-native editor exists yet. |
| Debugger / monitor | No | No | No | Yes | No usable Action debugger yet. |
| Operator documentation | Yes | Yes | N/A | N/A | Exported into `ACTION.DNP/DOC`. |
| Language documentation | Yes | Yes | N/A | N/A | Exported into `ACTION.DNP/DOC`. |
| Sample source workspace | Yes | Yes | N/A | N/A | Exported into `ACTION.DNP/SRC`. |
| Runtime manifest bundle | Yes | Yes | N/A | N/A | Exported into `ACTION.DNP/LIB/LIBMODS.DAT`. |

## Feature Matrix

| Feature | Legacy Reference | UDOS Workspace Export | UDOS-Native Runtime | Planned | Notes |
|---|---:|---:|---:|---:|---|
| Compile `.ACT` -> `AVM1` | Yes | No | No | Yes | Current implementation exists only as a legacy bootstrap reference. |
| Link `.AVO` -> `AVM1` with dead-strip | Yes | No | No | Yes | Current implementation exists only as a legacy bootstrap reference. |
| Run `AVM1` payloads | Yes | Sample payloads only | No | Yes | Next immediate tool target on UDOS. |
| Launch UDOS-native external Action tools | No | Yes | Yes | Yes | `ACTINFO.PRG` proves external-tool launch/return through the preserved launch-safe UDOS ABI. |
| REAL / REU / overlay language reference | Yes | Partial | No | Yes | Semantics exist in legacy/reference form; exported guides and examples are available under UDOS. |
| File I/O runtime examples | Yes | Yes | No | Yes | `FILECOPY.AVM` is exported, but no UDOS-native runner exists yet. |
| Sample `.ACT` programs | Yes | Yes | N/A | N/A | Exported for shell browsing and later tool bring-up. |
| Sample `.AVM` programs | Yes | Yes | N/A | N/A | Exported for later UDOS-native VM bring-up. |
| Packed runtime library manifests | Yes | Yes | N/A | N/A | Exported for later linker/compiler integration. |

## Immediate Next Tool Steps

1. add a UDOS-native `AVM1` runner so the exported `BIN/*.AVM` payloads are executable from UDOS
2. expand the preserved UDOS external-tool ABI beyond console/cmdline/exit into file and directory services
3. use that ABI to move from `ACTINFO` into a real Action-side runner/tool surface
4. then port linker and compiler behavior onto UDOS-native tools

## Relationship To UDOS Utilities

The following are still tracked by the UDOS command matrix, not by this file:

- `XCOPY`
- `TREE`
- `DELTREE`

Those are shell/environment utilities, not Action toolchain surfaces. They are
still planned and still matter to the overall development environment.
