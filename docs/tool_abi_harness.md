# Tool ABI Harness

The host harness runs UDOS-native tools against a mounted workspace and validates
file-service behavior without requiring manual C64 interaction.

Its 6502 execution engine is the MIT-licensed `lib6502` copy in
`third_party/lib6502`. Keeping that source in the maintained ActionC64U tree
makes the harness independent of retained historical workspace snapshots.

Current maintained uses:

- run `ACTC.PRG` and verify `OBJ/<MODULE>.OBJ`
- run `ALINK.PRG` and verify `BIN/<MODULE>.PRG`
- seed project/library objects for linker probes
- launch the linked PRG through UDOS/VICE direct-launch probes
- inspect resident service/debug state when a probe fails

Current direct PRG proof shape:

1. prepare a UDOS workspace under `IMAGES/ACTION.DNP`
2. compile source with `ACTC.PRG`
3. stage any required runtime/module objects
4. link with `ALINK.PRG`
5. verify `BIN/MAIN.PRG`
6. launch that PRG directly under UDOS/VICE

The harness should not reintroduce a generic runtime-launch step. If a test needs
runtime behavior, it should prove that ALINK placed the required code in the
final PRG or in a program-owned linked payload.
