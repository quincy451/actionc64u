# ActionC64U Tool And Feature Matrix

This file tracks the Action-side development surface as the project moves from
CP/M bootstrap tooling toward UDOS-native tools.

Legend:

- `Yes`: implemented and usable in that column's environment
- `Partial`: exists, but incomplete or only usable as a bridge/reference
- `No`: not implemented
- `Planned`: explicitly intended, but not started yet

## Tool Matrix

| Tool | Bootstrap CP/M | UDOS Workspace Export | UDOS-Native Tool | Planned | Notes |
|---|---:|---:|---:|---:|---|
| `ACTC` compiler | Yes | No | No | Yes | Current on-target compiler is still the CP/M bootstrap reference. |
| `ALINK` dead-strip linker | Yes | No | No | Yes | Current linker exists only in the CP/M bootstrap path. |
| `VM` `AVM1` runner | Yes | Sample payloads only | No | Yes | Current runner exists in CP/M; the UDOS bridge exports sample `.AVM` assets but no UDOS-native runner yet. |
| `ACTMON` front end | Yes | No | No | No | Historical bootstrap front end only. UDOS already owns the shell role. |
| Integrated editor | No | Guides only | No | Yes | No UDOS-native editor exists yet. |
| Debugger / monitor | No | No | No | Yes | No usable Action debugger yet. |
| Operator documentation | Yes | Yes | N/A | N/A | Exported into `ACTION.DNP/DOC`. |
| Language documentation | Yes | Yes | N/A | N/A | Exported into `ACTION.DNP/DOC`. |
| Sample source workspace | Yes | Yes | N/A | N/A | Exported into `ACTION.DNP/SRC`. |
| Runtime manifest bundle | Yes | Yes | N/A | N/A | Exported into `ACTION.DNP/LIB/LIBMODS.DAT`. |

## Feature Matrix

| Feature | Bootstrap CP/M | UDOS Workspace Export | UDOS-Native Runtime | Planned | Notes |
|---|---:|---:|---:|---:|---|
| Compile `.ACT` -> `AVM1` | Yes | No | No | Yes | Current implementation is the CP/M bootstrap compiler. |
| Link `.AVO` -> `AVM1` with dead-strip | Yes | No | No | Yes | Current implementation is the CP/M bootstrap linker. |
| Run `AVM1` payloads | Yes | Sample payloads only | No | Yes | Next immediate tool target on UDOS. |
| REAL / REU / overlay language reference | Yes | Partial | No | Yes | Semantics exist in bootstrap/reference form; exported guides and examples are available under UDOS. |
| File I/O runtime examples | Yes | Yes | No | Yes | `FILECOPY.AVM` is exported, but no UDOS-native runner exists yet. |
| Sample `.ACT` programs | Yes | Yes | N/A | N/A | Exported for shell browsing and later tool bring-up. |
| Sample `.AVM` programs | Yes | Yes | N/A | N/A | Exported for later UDOS-native VM bring-up. |
| Packed runtime library manifests | Yes | Yes | N/A | N/A | Exported for later linker/compiler integration. |

## Immediate Next Tool Steps

1. add a UDOS-native `AVM1` runner so the exported `BIN/*.AVM` payloads are executable from UDOS
2. expose the resident UDOS services that external Action tools need for file and console I/O
3. define the first UDOS-native Action tool entrypoint contract
4. then port linker and compiler behavior onto UDOS-native tools

## Relationship To UDOS Utilities

The following are still tracked by the UDOS command matrix, not by this file:

- `XCOPY`
- `TREE`
- `DELTREE`

Those are shell/environment utilities, not Action toolchain surfaces. They are
still planned and still matter to the overall development environment.
