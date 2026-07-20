# Overlay Direction

Overlay-style implementation remains useful for tool internals, but normal
linked programs should not rely on a separate runtime host.

For final programs, ALINK should either place required helper code directly in
the PRG or generate an explicitly program-owned linked payload.

The Idun compiler currently accepts `OVERLAY name` / `ENDOVERLAY` and lowers
`OverlayCall(name)` to a local JSR relocation. The referenced body remains a
resident, program-owned section of the direct PRG; it is not loaded by Linux or
UDOS at runtime.

Native `ACTC.PRG` does not yet implement that source syntax. Its `ACTC_OVL*.BIN`
files are compiler-pass implementation overlays and are unrelated. The native
`examples/ovl_demo.act` file is a porting fixture until ACTC emits named overlay
exports, body relocations, and `OverlayCall` relocations as ordinary OBJ1
records. ALINK should require no source-specific behavior for the baseline
resident-section implementation.
