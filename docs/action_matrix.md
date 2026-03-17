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
| `ACTDIR` tool proof | No | Yes | Yes | N/A | Enumerates the current mounted directory through the preserved UDOS directory ABI and returns to the prompt. |
| `ACTFLOW.BAT` composite workspace proof | No | Yes | Yes | N/A | Batch-driven composite workspace flow proof that exercises preserved file write/copy/move/delete services in one UDOS run and returns control to the prompt. |
| `ACTNEW.BAT` project workflow proof | No | Yes | Yes | N/A | Batch-driven project skeleton proof that composes stable UDOS shell `MD`/`CD`/`COPY` commands with root-absolute template copies to create `SRC/`, `BIN/`, `OBJ/`, `README.TXT`, and `MAIN.ACT`. |
| `ACTINFO` tool proof | No | Yes | Yes | N/A | First UDOS-native external Action-side tool proof. It launches from `ACTION.DNP`, prints through the preserved launch-safe UDOS ABI, and returns to the UDOS prompt. |
| `ACTCOPY` tool proof | No | Yes | Yes | N/A | Copies a file in the current mounted workspace through the preserved UDOS file-copy ABI; success is validated by the shell reading the copied file after return. |
| `ACTDEL` tool proof | No | Yes | Yes | N/A | Deletes a file in the current mounted workspace through the preserved UDOS file-delete ABI and returns to the prompt. |
| `ACTMKDIR` tool proof | No | Yes | Yes | N/A | Creates a directory in the current mounted workspace through the preserved UDOS directory-mutation ABI and returns to the prompt. |
| `ACTMOVE` tool proof | No | Yes | Yes | N/A | Renames a file in the current mounted workspace through the preserved UDOS file-rename ABI; success is validated by the shell reading the renamed file after return. |
| `ACTRMDIR` tool proof | No | Yes | Yes | N/A | Removes an empty directory in the current mounted workspace through the preserved UDOS directory-mutation ABI and returns to the prompt. |
| `ACTWRITE` tool proof | No | Yes | Yes | N/A | Writes a text file into the current mounted directory through the preserved UDOS file-save ABI and returns to the prompt. |
| `AVMINFO` tool proof | No | Yes | Yes | N/A | Loads an `.AVM` file through the preserved UDOS file-load service, validates the `AVM1` header, prints `AVM OK`, and returns to the UDOS prompt. |
| `VM` `AVM1` runner | Yes | Yes | Partial | Yes | `AVMRUN.PRG` now runs a flagged Acheron-backed `AVM1` subset from the mounted Action workspace. Current proof surface is intentionally small but real: `setp16`, `calln`, `native`, `stringz`, `jump`, `call`, and `ret`. |
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
| Run `AVM1` payloads | Yes | Yes | Partial | Yes | UDOS now has a real `AVMRUN.PRG` proof for flagged Acheron-backed payloads such as `UDOSHELLO.AVM` and `UDOSFLOW.AVM`. The full historical bootstrap opcode surface is not considered compatible and is not claimed here. |
| Launch UDOS-native external Action tools | No | Yes | Yes | Yes | `ACTINFO.PRG` proves external-tool launch/return through the preserved launch-safe UDOS ABI. |
| Enumerate directories through UDOS ABI | No | Yes | Yes | Yes | `ACTDIR.PRG` proves current-directory enumeration from a UDOS-native external tool. |
| Compose multiple file services through one workflow | No | Yes | Yes | Yes | `ACTFLOW.BAT` composes preserved save/copy/move/delete services in one UDOS workflow instead of proving each service only in isolation. |
| Create a starter Action project workspace | No | Yes | Yes | Yes | `ACTNEW.BAT` composes shell `MD`/`CD`/`COPY` with root-absolute template files to create a minimal project skeleton from inside UDOS while staying within the resident shell line limit. |
| Make/remove directories through UDOS ABI | No | Yes | Yes | Yes | `ACTMKDIR.PRG` and `ACTRMDIR.PRG` prove current-directory directory creation/removal from a UDOS-native external tool. |
| Copy files through UDOS ABI | No | Yes | Yes | Yes | `ACTCOPY.PRG` proves current-directory file copy from a UDOS-native external tool, with shell-side readback validating the copied file content after return. |
| Delete files through UDOS ABI | No | Yes | Yes | Yes | `ACTDEL.PRG` proves current-directory file deletion from a UDOS-native external tool. |
| Rename files through UDOS ABI | No | Yes | Yes | Yes | `ACTMOVE.PRG` proves current-directory file rename from a UDOS-native external tool, with shell-side readback validating the renamed file content after return. |
| Save tool-side files through UDOS ABI | No | Yes | Yes | Yes | `ACTWRITE.PRG` proves current-directory file creation/update from a UDOS-native external tool. |
| Load tool-side files through UDOS ABI | No | Yes | Yes | Yes | `AVMINFO.PRG` proves mounted-workspace file loading from a UDOS-native external tool. |
| REAL / REU / overlay language reference | Yes | Partial | No | Yes | Semantics exist in legacy/reference form; exported guides and examples are available under UDOS. |
| File I/O runtime examples | Yes | Yes | No | Yes | `FILECOPY.AVM` is exported, but no UDOS-native runner exists yet. |
| Sample `.ACT` programs | Yes | Yes | N/A | N/A | Exported for shell browsing and later tool bring-up. |
| Sample `.AVM` programs | Yes | Yes | N/A | N/A | Exported for later UDOS-native VM bring-up. |
| Packed runtime library manifests | Yes | Yes | N/A | N/A | Exported for later linker/compiler integration. |

## Immediate Next Tool Steps

1. expand `AVMRUN.PRG` from the current flagged Acheron subset into a broader executable `AVM1` surface
2. expand the preserved UDOS external-tool ABI beyond the current console/cmdline/exit/read/write/delete/directory proofs into richer workspace services
3. use that ABI to move from `ACTCOPY`, `ACTFLOW.BAT`, `ACTINFO`, `ACTNEW.BAT`, `ACTDEL`, `ACTMKDIR`, `ACTMOVE`, `ACTRMDIR`, `ACTWRITE`, `AVMINFO`, and `AVMRUN` into a broader Action-side tool surface
4. then port linker and compiler behavior onto UDOS-native tools

## Relationship To UDOS Utilities

The following are still tracked by the UDOS command matrix, not by this file:

- `XCOPY`
- `TREE`
- `DELTREE`

Those are shell/environment utilities, not Action toolchain surfaces. They are
still planned and still matter to the overall development environment.
