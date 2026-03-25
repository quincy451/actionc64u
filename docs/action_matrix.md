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
| `ACTC` compiler | Yes | No | Partial | Yes | `ACTC.PRG` is now the first UDOS-native compiler front-end slice. The current proof validates a tracked project module, verifies the source `MODULE` header matches the requested module name, extracts top-level `PROC` exports from source, scans source text for the current runtime-call marker set, and emits a deterministic `OBJ/<NAME>.AVO` object stub with module/export/import/payload metadata. It is not full code generation yet, and the focused runtime proof verifies the host-side object file rather than shell-side `TYPE OBJ/...` readback. |
| `ALINK` dead-strip linker | Yes | No | Partial | Yes | `ALINK.PRG` is now the first UDOS-native linker slice. The current proof loads a deterministic `OBJ/<NAME>.AVO` text object stub, parses its export/import metadata, resolves the current small runtime closure, and emits `BIN/<NAME>.MAP` on the host fs tree with export and resolve lines. It is not a full object merger or final AVM linker yet. |
| `ACTDIR` tool proof | No | Yes | Yes | N/A | Enumerates the current mounted directory through the preserved UDOS directory ABI and returns to the prompt. |
| `ACTADD` tool proof | No | Yes | Yes | N/A | Adds `SRC/<NAME>.ACT` inside an Action project root marked by `ACTION.PROJ` through the preserved UDOS file-save ABI. Current proof refuses duplicate module creation with `EXISTS`. |
| `ACT2SAVE` tool proof | No | Yes | Yes | N/A | Validates `ACTION.PROJ`, requires a tracked module entry, rewrites `SRC/<NAME>.ACT` through the preserved UDOS file-save ABI, and reports `CREATED` or `UPDATED`. |
| `ACTCHK` integrity tool | No | Yes | Yes | N/A | UDOS-native checker for `ACTION.PROJ` projects. It verifies `SRC/`, `BIN/`, and `OBJ/`, probes tracked `SRC/<NAME>.ACT` entries, reports missing sources, and exits `ACTCHK OK` or `ACTCHK BROKEN`. The focused healthy-project headless VICE proof is green via `make vice-action-actchk`; broken-path automation is not claimed here. |
| `ACTFLOW.BAT` composite workspace proof | No | Yes | Yes | N/A | Batch-driven composite workspace flow proof that exercises preserved file write/copy/move/delete services in one UDOS run and returns control to the prompt. |
| `ACTNEW.BAT` project workflow proof | No | Yes | Yes | N/A | Batch-driven project skeleton proof that composes stable UDOS shell `MD`/`CD`/`COPY` commands with root-absolute template copies to create `SRC/`, `BIN/`, `OBJ/`, `ACTION.PROJ`, `README.TXT`, and `MAIN.ACT`. |
| `ACTNEW` tool proof | No | Yes | Yes | N/A | First non-trivial UDOS-native workspace tool proof. It creates a project directory, makes `SRC/`, `BIN/`, and `OBJ/`, writes `ACTION.PROJ`, `README.TXT`, and `SRC/MAIN.ACT`, prints `ACTNEW OK`, and returns control to UDOS. |
| `ACTSRC` tool proof | No | Yes | Yes | N/A | Reads `ACTION.PROJ` in the current project root through the preserved UDOS file-load ABI, prints the tracked source entries, and returns to the prompt. |
| `ACTFILE` tool proof | No | Yes | Yes | N/A | Loads `SRC/<NAME>.ACT` from the current Action project through the preserved UDOS file-load ABI after validating `ACTION.PROJ`, prints the source text, and returns to the prompt. |
| `ACTWORK` tool proof | No | Yes | Yes | N/A | Summarizes the current Action project/workspace through preserved directory and file-load services by reporting project-marker presence, expected directories, and manifest module count. |
| `ACTMON` front end proof | Yes | Yes | Yes | N/A | UDOS-native monitor-style front end that dispatches `WORK`, `CHECK`, `SRC`, `FILE <NAME>`, `ADD <NAME>`, `DEL <NAME>`, `REN <OLD> <NEW>`, `COPY <OLD> <NEW>`, and `SAVE <NAME>` through one entry point while the UDOS shell remains the prompt owner. Focused headless VICE proofs for `WORK` and `CHECK` are green again after reducing the monitor back under the current launch-safe size ceiling, and the broader mutation-sequence proof is green again through the generic mounted-tree composite runner. |
| `ACTINFO` tool proof | No | Yes | Yes | N/A | First UDOS-native external Action-side tool proof. It launches from `ACTION.DNP`, prints through the preserved launch-safe UDOS ABI, and returns to the UDOS prompt. |
| `ACTCOPY` tool proof | No | Yes | Yes | N/A | Copies a file in the current mounted workspace through the preserved UDOS file-copy ABI; success is validated by the shell reading the copied file after return. |
| `ACTDEL` tool proof | No | Yes | Yes | N/A | Deletes a file in the current mounted workspace through the preserved UDOS file-delete ABI and returns to the prompt. |
| `ACTMKDIR` tool proof | No | Yes | Yes | N/A | Creates a directory in the current mounted workspace through the preserved UDOS directory-mutation ABI and returns to the prompt. |
| `ACTMOVE` tool proof | No | Yes | Yes | N/A | Renames a file in the current mounted workspace through the preserved UDOS file-rename ABI; success is validated by the shell reading the renamed file after return. |
| `ACTRMDIR` tool proof | No | Yes | Yes | N/A | Removes an empty directory in the current mounted workspace through the preserved UDOS directory-mutation ABI and returns to the prompt. |
| `ACTWRITE` tool proof | No | Yes | Yes | N/A | Writes a text file into the current mounted directory through the preserved UDOS file-save ABI and returns to the prompt. |
| `AVMINFO` tool proof | No | Yes | Yes | N/A | Loads an `.AVM` file through the preserved UDOS file-load service, validates the `AVM1` header, prints `AVM OK`, and returns to the UDOS prompt. |
| `VM` `AVM1` runner | Yes | Yes | Partial | Yes | `AVMRUN.PRG` now runs a flagged Acheron-backed `AVM1` subset from the mounted Action workspace. Current proof surface is intentionally small but real: `setp16`, `calln`, `native`, `stringz`, `jump`, `call`, and `ret`. |
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
| Emit `.ACT` -> `.AVO` object stubs | Yes | No | Partial | Yes | `ACTC.PRG` now emits deterministic `AVO1` text object stubs into `OBJ/` for tracked project modules, verifies the source `MODULE` header matches the requested module name, extracts top-level `PROC` exports, and includes the current inferred runtime-import list from simple source-pattern scanning. The current UDOS-native slice is a project-aware front end/object emitter only, not a full compiler. |
| Emit `.AVO` -> `.MAP` dependency maps | Yes | No | Partial | Yes | `ALINK.PRG` now loads deterministic `AVO1` object stubs from `OBJ/`, parses export/import metadata, resolves the current small runtime import closure, and writes `BIN/<NAME>.MAP` on the host fs tree. The current UDOS-native slice is a map/link planning proof, not a full dead-strip object merger or final AVM image linker. |
| Link `.AVO` -> `AVM1` with dead-strip | Yes | No | No | Yes | Current implementation exists only as a legacy bootstrap reference. |
| Run `AVM1` payloads | Yes | Yes | Partial | Yes | UDOS now has a real `AVMRUN.PRG` proof for flagged Acheron-backed payloads such as `UDOSHELLO.AVM` and `UDOSFLOW.AVM`. The full historical bootstrap opcode surface is not considered compatible and is not claimed here. |
| Launch UDOS-native external Action tools | No | Yes | Yes | Yes | `ACTINFO.PRG` proves external-tool launch/return through the preserved launch-safe UDOS ABI. |
| Enumerate directories through UDOS ABI | No | Yes | Yes | Yes | `ACTDIR.PRG` proves current-directory enumeration from a UDOS-native external tool. |
| Compose multiple file services through one workflow | No | Yes | Yes | Yes | `ACTFLOW.BAT` composes preserved save/copy/move/delete services in one UDOS workflow instead of proving each service only in isolation. |
| Create a starter Action project workspace | No | Yes | Yes | Yes | `ACTNEW.BAT` composes shell `MD`/`CD`/`COPY` with root-absolute template files to create a minimal project skeleton, including `ACTION.PROJ`, from inside UDOS while staying within the resident shell line limit. |
| Create a starter Action project workspace from a native tool | No | Yes | Yes | Yes | `ACTNEW.PRG` proves preserved directory and file-save services are sufficient for a native project skeleton tool that emits `ACTION.PROJ` alongside the starter source tree. |
| Add a starter module inside a native Action project | No | Yes | Yes | Yes | `ACTADD.PRG` proves a native tool can validate `ACTION.PROJ`, create `SRC/<NAME>.ACT`, refuse duplicate creation with `EXISTS`, and persist the new source file on the host-backed VICE workspace. |
| Save or refresh a tracked project source from a native Action project | No | Yes | Yes | Yes | `ACT2SAVE.PRG` proves a native tool can validate `ACTION.PROJ`, require the module to be tracked already, and create or overwrite `SRC/<NAME>.ACT` through the preserved file-save ABI. |
| Validate tracked project source integrity from a native Action project | No | Yes | Yes | Yes | `ACTCHK.PRG` validates expected workspace directories and probes each tracked `SRC/<NAME>.ACT` entry from `ACTION.PROJ`. The focused healthy-project headless VICE proof is green via `make vice-action-actchk`; broken-path runtime coverage is still not separately claimed. |
| Inspect project source membership from a native Action project | No | Yes | Yes | Yes | `ACTSRC.PRG` proves a native tool can load `ACTION.PROJ` and list tracked source entries from the current project root. |
| Load project source text from a native Action project | No | Yes | Yes | Yes | `ACTFILE.PRG` proves a native tool can validate `ACTION.PROJ`, resolve `SRC/<NAME>.ACT`, and print source text from the current project root. |
| Summarize project workspace state from a native Action project | No | Yes | Yes | Yes | `ACTWORK.PRG` proves a native tool can inspect current-directory project markers, validate expected workspace directories, and count manifest modules from `ACTION.PROJ`. |
| Dispatch multiple project monitor actions through one native front end | No | Yes | Yes | Yes | `ACTMON.PRG` proves a single UDOS-native front end can expose workspace summary, integrity checking, manifest listing, source view, tracked-module creation, tracked-module removal, tracked-module rename/copy, and tracked-module save/update operations. |
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
3. use that ABI to move from `ACTADD`, `ACT2SAVE`, `ACTCOPY`, `ACTFILE`, `ACTFLOW.BAT`, `ACTINFO`, `ACTMON`, `ACTNEW`, `ACTNEW.BAT`, `ACTSRC`, `ACTWORK`, `ACTDEL`, `ACTMKDIR`, `ACTMOVE`, `ACTRMDIR`, `ACTWRITE`, `AVMINFO`, and `AVMRUN` into a broader Action-side tool surface
4. then port linker and compiler behavior onto UDOS-native tools

## Relationship To UDOS Utilities

The following are still tracked by the UDOS command matrix, not by this file:

- `XCOPY`
- `TREE`
- `DELTREE`

Those are shell/environment utilities, not Action toolchain surfaces. They are
still planned and still matter to the overall development environment.
