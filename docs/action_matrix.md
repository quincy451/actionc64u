# ActionC64U Matrix

| Area | Current Status | Proof |
| --- | --- | --- |
| UDOS resident | Native 6502 shell/resident path | `make -C ../udos resident` and VICE resident gates |
| ACTC compiler | Emits linker objects | `make -C ../udos vice-action-actc` |
| Inline assembly | Core `ASMBLOCK` emits checked NMOS 6502 instructions and scoped labels; raw blocks emit unchecked byte/word/character constants and relocatable addresses | `python3 -m unittest -v tests.test_actc_overlay.TestActcOverlay.test_raw_code_blocks_emit_native_bytes_and_relocations` |
| ALINK linker | Emits direct `BIN/<MODULE>.PRG` | `make -C ../udos vice-action-alink` |
| Compile/link/launch | Direct PRG launch under UDOS | `make -C ../udos vice-action-actc-alink-launch` |
| ACTC object emission | 171 source-backed direct-launch shapes | `make -C ../udos vice-action-actc-alink-launch-object-emission-matrix` |
| ALINK matrix | 1330 direct-PRG object/link shapes | `make -C ../udos vice-action-alink-prg-matrix` |
| Runtime helpers | Link-selected modules owned by final PRG, including ACTC-emitted native dynamic integer code | `make -C ../udos vice-action-actc-alink-launch-runtime-matrices` and shape-specific probes |
| Release export | Ships UDOS-native tools and PRG-oriented samples | `python3 -m unittest udos.tests.test_release_fs` |
| Optional Idun/Linux host tools | Linux project/compiler/linker/editor/debug-sidecar commands, including REAL arrays/pointers and typed user functions, that emit direct C64 artifacts | `python3 -m unittest -v tests.test_linux_workspace_tools` |
| Idun host export | Linux executables plus standalone link-selected 6502 modules, without changing the UDOS release | `python3 -m unittest -v tests.test_idun_workspace_export` |

Removed direction:

- CP/M-era runner flow
- separate generic runtime launch program
- instruction-stream runtime product as the maintained linker output

Next work:

- keep all source-backed ACTC object-emission shapes covered by the matrix
- widen ALINK dependency closure and helper selection around remaining edge shapes
- keep final output as direct PRG
