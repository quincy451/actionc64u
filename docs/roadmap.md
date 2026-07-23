# Roadmap

Current roadmap:

1. Keep UDOS resident and Action tools building cleanly.
2. Widen ACTC source coverage and object emission.
3. Widen ALINK object closure resolution and direct PRG generation.
4. Convert optional runtime features into link-selected helper modules.
5. Keep direct PRG VICE gates green.

Retired roadmap items for CP/M-era runner flows are no longer maintained.

## 2026-07-09

- Added native `XCOPY.OVL` as a validated `UDOV` command module selected by the
  UDOS resident from the parsed `XCOPY` token.
- Added bounded recursive VICE tree copy through the fixed directory and file
  Tool ABI, including nested-path resolution and immediate release of transient
  file-cache slots after host persistence.
- Added release export/container checks and focused valid, invalid-module, and
  flat-image VICE gates; the valid gate copies eleven files over three levels.
- Added native `DELTREE.OVL` as command ID `22`, with bounded post-order VICE
  tree removal and preflight protection for the current directory and roots.
- Generalized Tool ABI directory removal to nested paths, persisted directory
  manifests safely across resident restore, and released transient host-delete
  cache slots so one invocation can exceed six files.
- Added release export/container checks plus valid, invalid-module, flat-image,
  and current-directory safety VICE gates; the valid gate removes eleven files
  and three directories.

## 2026-07-10

- Replaced the VICE tree backend's 255-byte `UDOSDIR.TXT` rewrite window with a
  line-streamed temporary catalog and deterministic copy-back path.
- Added first-catalog creation, unterminated-final-line handling, and exact
  oversized-catalog preservation across shell and Action Tool ABI mutations.
- Corrected VICE deferred file-not-found detection so newly created Action files
  retain live host state and subsequent rename/delete operations remove both
  physical files and catalog entries.
- Expanded focused `XCOPY.OVL`, `DELTREE.OVL`, `ACTMKDIR.PRG`, `ACTMOVE.PRG`,
  and `ACTRMDIR.PRG` gates to assert persisted manifests and no temporary
  catalog residue.

## 2026-07-10 Tool Overlay Boundary

- Kept all external-tool-callable resident services below the Action compiler's
  `$A000-$BFFF` pass-overlay window while retaining the larger streamed catalog
  implementation as REU-restored shell/post-return code.
- Normalized queued directory names during post-exit writeback and preserved
  directory-slot mappings across catalog persistence, keeping nested `XCOPY`
  manifests attached to their correct parents.

## 2026-07-10 Hardware/UCI Launch Staging

- Added a hardware/UCI tree-file staging route for direct PRGs and native
  `UDOV` command modules using `FILE_STAT`, `OPEN_FILE`, repeated `READ_DATA`
  transfers into the shared REU launch area, and `CLOSE_FILE`.
- Reused the linker-independent PRG load-address handling, `UDOV` validator,
  launch stub, and REU-backed resident restore used by the VICE path.
- Kept the hardware staging helpers above the `$A000` tool-callable boundary so
  external Action tools cannot overwrite resident services they call.
- The route is build- and VICE-compatibility-tested but remains unvalidated on
  real C64 Ultimate hardware. The corresponding recursive Tool ABI
  implementation is recorded below.

## 2026-07-10 Hardware/UCI Recursive Tool ABI

- Generalized nested tree-path resolution to select UCI `OPEN_DIR` / `READ_DIR`
  enumeration when the Ultimate transport is present and retain the VICE
  manifest path otherwise.
- Added UCI `CREATE_DIR`, file and empty-directory `DELETE_FILE`, same-drive
  `COPY_FILE`, and cross-drive read/write streaming behind the fixed recursive
  Tool ABI used by `TREE.OVL`, `XCOPY.OVL`, and `DELTREE.OVL`.
- Routed resident `MD` and `RD` through the same backend-generic directory
  operations.
- Made tool-time backend selection use UDOS's preserved transport snapshot so a
  large launched tool can overwrite low resident transport code and continue
  using the fixed Tool ABI; the 4,095-byte `ACTMON.PRG` gate covers this case.
- The implementation builds and preserves all focused VICE behavior, but it has
  not been validated on real C64 Ultimate hardware.

## 2026-07-10 ACTC Token Lookahead

- Added cached SourceReader lookahead for complete decimal, symbol, punctuation,
  and comparison tokens.
- Kept complete token caching in resident SourceReader while moving
  positive-word expression parsing into one shared body-overlay implementation
  reached through overlay-ABI v2 token callbacks. This keeps cold parser code
  outside resident ACTC without duplicating it between collect and preallocate
  passes.
- Added zero-lookahead page-boundary coverage for decimal and builtin-symbol
  tokens, operators, nested grouped expressions, and grouped signed values,
  and corrected sum/term state so normal arithmetic precedence remains intact.

## 2026-07-11 ACTC Small Decimal Tokens

- Replaced the resident byte-valued decimal factor's digit-by-digit scanner
  with complete SourceReader token consumption.
- Added a zero-lookahead proof with `255` crossing a 256-byte source-window
  boundary while preserving rejection of values outside the byte range.
- Consolidated duplicate byte-valued condition and decimal comparison parsing
  behind one complete-token tail covering `=`, `<`, `>`, `<=`, `>=`, and `<>`.
- Fixed nested declaration-initializer comparisons by preserving each outer
  left operand across recursive grouped right-hand expressions.
- Moved byte-valued arithmetic and grouping to complete-token dispatch and
  fixed recursive sum/term accumulator corruption for grouped operands.
- Moved resident byte-valued `AND`, `OR`, `NOT`, and boolean grouping to
  complete-token dispatch, including zero-lookahead keyword recognition across
  a page-aligned source-window boundary.
- Preserved boolean left operands on the machine stack across recursive right
  operands, fixing incorrect flat and nested `AND`/`OR` constant results.
- Moved resident runtime boolean grouping and all six integer comparison forms
  to complete-token dispatch, retaining zero-lookahead page-boundary coverage.
- Consolidated runtime comparison suffix lowering around one token classifier,
  recovering 26 resident bytes while preserving the existing direct-PRG op
  streams.
- Moved dynamic integer runtime `+`/`-` and grouped terms to complete-token
  dispatch, with variable-expression zero-lookahead proofs at a page boundary.
- Moved all six runtime REAL comparison forms to complete-token dispatch,
  preserving the existing `rt_f_cmp` lowering while recovering 76 resident
  bytes and adding zero-lookahead page-boundary proofs.
- Moved runtime call `(`, `,`, and `)` punctuation to a shared expected-token
  consume seam, retaining page-aligned zero-lookahead call proofs while keeping
  the parser independent of byte-oriented delimiter helpers.
- Moved shared conversion and unary-helper keyword opens to complete symbol plus
  `(` tokens, and moved resident runtime REAL conversion closes and the signed
  prefix to complete punctuation tokens. A resident-fallback proof places the
  keyword and delimiters independently at a zero-lookahead page boundary while
  preserving exact object emission and recovering 26 resident bytes.
- Moved the resident signed REAL conversion's single-zero sentinel to a strict
  decimal-token consume, including cross-page acceptance of `0-n` and rejection
  of `00-n`. Fixed source-cursor loss during conversion literal storage and
  preserved REAL comparison-control literals across RHS conversion arithmetic.
- Moved optional small-value `=`, `[`, and `]` punctuation in module,
  constant-expression, runtime-value, and resident integer-print paths to
  complete-token consumption, with a nine-case zero-lookahead boundary matrix.
- Made failed constant-expression probes transactional across REU page refills
  and aligned the legacy `PrintI`/`PrintIE` runtime fallback with the shared
  optional-wrapper syntax and complete-token close handling, including a
  production `ACTC_OVL6` boundary proof.
- Added dynamic integer `*` and `/` precedence lowering to ACTC, including
  complete-token page-boundary coverage and selective `rt_i_mul` / `rt_i_div`
  imports. ACTC now emits native 6502 `m` records with nested initialized-data
  exports and generic `r` relocations. ALINK links those records through the
  ordinary object-code path and includes only the referenced integer helpers
  plus `rt_print_i` when needed.
- Added exact-byte, malformed-body, missing-helper, stack-underflow, assignment
  store, divide-by-zero, and live VICE proofs. The linked programs are ordinary
  direct PRGs and do not use a runtime instruction runner.
- Removed ALINK's dedicated integer-body analyzer and code generator. The
  reduced linker now ends at `$8AE5`, leaving 3,354 bytes below the preserved
  UDOS Tool ABI boundary at `$9800`.
- Extended ACTC's native word emitter to straight-line assignments, loads, and
  load/store copies. Removed ALINK's matching word-body templates and converted
  the seeded positive cases to ordinary machine-code OBJ records, with the old
  compact bodies covered only as rejection inputs.
- Converted the remaining seeded empty-return and transitive-library fixtures
  to ordinary machine-code OBJ records with real relocations. Removed ALINK's
  empty-return, single-call, and fanout root-body templates, leaving the compact
  forms as explicit rejection probes.
- Extended ACTC's native integer emitter across string output and ordinary
  external calls. Converted the imported `printmath` root and its `W` library
  dependency to machine OBJ records, selected `rt_print_i` through normal
  closure, and removed ALINK's dedicated printmath strategy and template. The
  two old compact printmath bodies are retained only as rejection probes.
- Added compiler-owned native lowering for a simple integer equality `IF`.
  ACTC fuses the compact equality/branch pair into 6502 machine code and emits
  a named relocation to a synthetic `__if0` local export, so forward branch
  distance is not constrained by the 6502 relative-branch range.
- Removed ALINK's matching `if_eq` compact-body candidate and generated PRG
  template. The old body is now rejection-only.
- Split compiler-owned native integer object generation into `ACTC_OVL8.BIN`.
  The generic `ACTC_OVL5.BIN` now excludes the native generator, and explicit
  not-applicable dispatch preserves generic object output while leaving more
  than 2 KB free in each emission overlay for subsequent native control flow.
- Extended that native branch lowering to integer not-equal `IF`, removed
  ALINK's matching compact candidate/template, and retained the old body only
  as an explicit rejection case.
- Extended native branch lowering to unsigned integer less-than `IF`, removed
  ALINK's matching compact candidate/template, and retained the old body only
  as an explicit rejection case.
- Extended native branch lowering to unsigned integer greater-than `IF`,
  removed ALINK's matching compact candidate/template, and retained the old
  body only as an explicit rejection case.
- Fused the compiler's zero-inverted unsigned comparison forms into native
  greater-equal and less-equal branches, retired both matching ALINK templates,
  and retained their compact bodies as rejection cases.
- Extended the one-level native integer branch path through simple equality
  `IF/ELSE`, using `__if0` for the else entry and `__if1` for the join. Removed
  ALINK's matching candidate/template, added true/false live launch coverage,
  and retained the compact body as a rejection case. The broad direct-PRG
  matrix then contained 1258 cases.
- Extended native integer lowering to two nested `IF` levels, including an
  inner `ELSE`. ACTC emits fixed outer `__if0`/`__if1` and inner
  `__if2`/`__if3` relocation targets, while ordered comparison inversion is
  recalculated for each condition. Removed both nested ALINK templates, added
  an outer-false live case, and retained both compact bodies only as rejection
  probes. The broad direct-PRG matrix then contained 1261 cases.
- Migrated simple integer equality and less-than `DO ... UNTIL` loops to
  ACTC-owned native machine records with a `__do0` backward relocation.
  Removed both matching ALINK templates and retained their compact bodies as
  rejection probes. The broad direct-PRG matrix then contained 1263 cases.
- Generalized compiler-owned equality `DO ... UNTIL` lowering to two nested
  loops with `__do0`/`__do1` targets, removed ALINK's nested-loop template,
  and retained its compact body as a rejection probe. The broad direct-PRG
  matrix then contained 1269 cases.
- Added one-procedure integer equality `WHILE` lowering in `ACTC_OVL9.BIN`.
  ACTC emits the false exit and loop back-edge as ordinary named relocations;
  focused compile, link, and VICE launch coverage raises the broad direct-PRG
  matrix to 1270 cases and the source-backed launch matrix to 144 cases.
- Extended that compiler-owned `WHILE` path through `<>`, `<`, `>`, `>=`, and
  `<=`. Inclusive comparisons fuse the collector's zero-inversion sequence
  into one native branch, and all six forms use ordinary exit/back-edge
  relocations. The broad matrix now contains 1275 cases and the source-backed
  launch matrix contains 149 cases.
- Added `ACTC_OVL9.BIN` for compiler-owned multi-procedure integer lowering.
  Eleven local-call/control-flow shapes now emit machine bodies, named
  procedure exports, local control targets, and ordinary relocations.
- Removed the corresponding ten remaining local-call signatures/templates from
  ALINK, converted the seeded runtime smoke fixture to relocatable machine OBJ
  records, and removed ALINK's final generic compact-body candidate table.
- Added source-backed composition coverage for a local procedure call inside a
  compiler-owned less-than `WHILE`. The call, loop head, and exit remain normal
  named relocations through direct PRG launch; the broad matrix now contains
  1281 cases and the source-backed launch matrix contains 150 cases.

## 2026-07-14 Direct Tool Workflow

- Added ACTEDIT `Ctrl-O`, `Ctrl-B`, and `Ctrl-D` save-and-handoff commands for
  compile, build, and debug workflows.
- Added compact trailing `,` and `:` module workflow markers so all 24 supported
  module-name characters fit within UDOS's 31-byte command line.
- Added successful-output chaining from ACTC to ALINK and from ALINK to ACTDBG
  through the fixed UDOS Tool ABI; every stage remains an ordinary direct PRG.
- Added harness coverage for editor module derivation, exact successor commands,
  compile output, direct-PRG/debug-sidecar output, and no-chain plain ALINK use.

## 2026-07-14 ACTDBG Release Integration

- Made the UDOS release fail unless the full `ACTION.DNP` workspace contains
  `ACTDBG.PRG` and valid `DGOV` optional-UI and execution overlays.
- Kept the capacity-limited D64 as a boot/tool subset rather than removing
  maintained tools to duplicate the debugger payload.
- Added a mounted-workspace VICE workflow that follows `ACTC MAIN:` through
  direct ACTC, ALINK, and ACTDBG PRGs, exits ACTDBG, and verifies all compiler,
  linker, and debug-sidecar outputs.
- Cleared ACTDBG's full-screen canvas on normal interactive exit so the
  returning UDOS prompt is not mixed with stale debugger rows.

## 2026-07-14 Debugger-To-Editor Location Return

- Added strict `ACTEDIT <NAME-OR-PATH>:<LINE>` startup positioning with 16-bit
  decimal overflow, zero, and source-range checks.
- Added ACTDBG `E` handoff for the currently browsed linked source record. The
  debugger builds `ACTEDIT <SOURCE-PATH>:<LINE>` only when the complete command
  fits UDOS's 31-byte chain ABI and reports failure instead of truncating it.
- Corrected ACTEDIT path rendering for real UDOS screen-code command lines,
  where the letter `M` shares byte `$0D` with ASCII carriage return, and cleared
  the editor canvas on interactive exit.
- Extended the mounted-workspace VICE gate through direct ACTC, ALINK, ACTDBG,
  and ACTEDIT PRGs and back to the live project prompt.

## 2026-07-14 Compiler-Error Editor Return

- Added compile-only `ACTC <MODULE>;` and made compile, build, and debug modes
  queue `ACTEDIT <MODULE>:<LINE>` after source diagnostics while plain ACTC
  failures retain their nonzero shell return.
- Counted the failing line directly from the staged 24-bit REU source window,
  including offsets beyond the resident source cache, and rejected overlong
  editor commands instead of truncating the 31-byte chain ABI.
- Normalized screen-code module names to lowercase host paths in ACTEDIT so
  module entry works on case-sensitive VICE filesystems.
- Added an end-to-end VICE gate that drives ACTEDIT's compile key through ACTC
  failure, reopens line 3, returns to the project prompt, and verifies that no
  OBJ was emitted.

## 2026-07-14 ACTC Workflow Overlay

- Moved strict ALINK and source-positioned ACTEDIT successor-command assembly
  from resident ACTC into `ACTC_OVL0.BIN`, while preserving its zero-mode no-op
  ABI for direct pass-runner compatibility.
- Made the production ACTC build always emit pass 0 and added harness assertions
  that only requested compile/link/debug or error-return paths load it.
- Recovered enough resident space for the capacity guard: production ACTC BSS
  ends at `$4AF1`, below the UDOS resident floor at `$4AFE`.

## 2026-07-14 ACTEDIT Logical Line Index

- Added a persistent three-byte-per-line edited-document index in REU banks
  `$00-$02`, mapping each logical line directly to a derived piece and 16-bit
  offset while leaving undo/redo metadata in banks `$03-$04` untouched.
- Invalidated and rebuilt the index with piece metadata changes, then replaced
  linear piece-count scans during navigation and save with direct REU lookups.
- Added a 300-line split/save proof that crosses index write windows, verifies
  exact 301-line output, and observes both batched index writes and direct
  three-byte reads through the Tool ABI harness.

## 2026-07-14 ACTEDIT Direct Line-Patch Pieces

- Made clean source-line patches split or replace the indexed resident piece
  directly, persist the resulting source/patch/source spans, and rebuild only
  the edited-document logical index instead of reconstructing all descriptors.
- Retained the metadata-authoritative full-rebuild fallback for dirty caches and
  active structural transactions so reserved insert slots remain atomic across
  split, paste, undo, and save paths.
- Added a focused proof that patches and reloads a line in the middle of a source
  run with one initial descriptor rebuild and one direct piece mutation.

## 2026-07-14 ACTEDIT Direct Split Insert Pieces

- Reordered clean source-line split transactions so the shortened line first
  becomes a directly persisted PATCH piece, then captured that indexed boundary
  before insert metadata invalidates the cache.
- Added direct INSERT-piece persistence at the captured boundary, with the same
  metadata-authoritative capacity and I/O fallback used by direct line patches.
- Extended the 300-line split/save proof to require one initial descriptor
  rebuild, one direct patch, and one direct insert while preserving exact output.
- Recorded the resident-space boundary explicitly: `ACTEDIT.PRG` now ends at
  `$498A`, leaving `$174` bytes below the `$4AFE` UDOS floor.

## 2026-07-14 ACTEDIT Resident Mutation Sharing

- Shared clean-cache validation between direct patch and split-insert paths and
  replaced duplicate six-field piece-tail copies with one resident helper.
- Preserved direct mutation and fallback behavior while reducing `ACTEDIT.PRG`
  by `34` bytes; the resident image now ends at `$4968`, leaving `$196` bytes
  below the `$4AFE` UDOS floor.

## 2026-07-14 ACTEDIT Native Mutation Overlay

- Moved clean source-line patch and split-insert piece mutation into the native
  `ACTEDIT_OVL1.BIN` payload at `$A000`, retaining only bounded load, validation,
  dispatch, and fallback wrappers in `ACTEDIT.PRG`.
- Added an `AEOV` ABI header, one-load session lifecycle, and explicit load and
  failure counters; missing, oversized, or malformed payloads preserve edits by
  using the metadata-authoritative descriptor rebuild path.
- Reduced `ACTEDIT.PRG` from `16491` to `16041` bytes. Resident code now ends at
  `$47A6`, leaving `855` bytes below the `$4AFE` UDOS floor, while the mutation
  overlay occupies `853` bytes at `$A000-$A354`.
- Added complete `ACTION.DNP` release integration, focused valid and invalid
  overlay tests, and a VICE gate that edits, directly commits, saves, exits, and
  verifies the resulting source file.

## 2026-07-14 ACTEDIT Structural Mutation And Suffix Indexing

- Advanced the `AEOV` ABI to version 2 and added prepare/apply removal commands
  that validate logical-line identity before directly shrinking, splitting, or
  removing SOURCE, PATCH, and INSERT pieces.
- Routed joins and multiline cut/delete through that direct removal primitive,
  while malformed or missing overlays and stale caches retain the
  metadata-authoritative full descriptor rebuild.
- Prepared inserted-line splits before their text metadata changes, allowing
  source and inserted splits plus general multiline paste to remain on direct
  piece-table operations; text-only updates to an existing INSERT slot now
  preserve the unchanged piece/index cache.
- Replaced full logical-index rewrites after direct mutations with affected
  suffix writes. A 300-line split proof observes writes beginning at byte
  offsets `$01BF` and `$01C2` for lines 150 and 151.
- Kept `ACTEDIT.PRG` within the resident boundary at `16243` bytes
  (`$0900-$4870`, 653 bytes below `$4AFE`); the expanded overlay is `1758`
  bytes at `$A000-$A6DD`.
- Extended harness coverage across source-piece edges, PATCH and INSERT
  removal, inserted-line split, general paste, invalid-overlay fallback, and a
  live mounted-workspace VICE edit/remove/save workflow.

## 2026-07-16 REAL32 Finite To INT Verification

- Made the existing `rt_f_to_i` machine helper reproducible through the shared
  math-runtime generator without changing its 124-byte direct-PRG ABI.
- Added one link-selected direct fixture covering signed zero, subnormal and
  fractional truncation, both signed INT limits, adjacent overflow values,
  maximum finite magnitudes, infinities, and NaN safety.
- Kept `rt_f_to_i` independent of unrelated REAL helpers and raised the broad
  direct-PRG matrix to 1278 cases.

## 2026-07-16 REAL32 Addition And Subtraction

- Replaced the Q8.8 range-limited add/sub bodies with six-byte operation
  selectors and one shared link-selected `rt_f_addsub_core` module.
- Added finite signed binary32 alignment, subnormal handling, cancellation,
  signed-zero behavior, guard/round/sticky retention, and nearest-even rounding;
  unsupported non-finite inputs and finite overflow retain the zero-result policy.
- Added exact raw-result VICE fixtures for addition and subtraction, including
  tie rounding and normal/subnormal boundaries, raising the broad matrix to
  1280 cases without including the core when neither operation is referenced.

## 2026-07-16 REAL32 Multiplication

- Replaced the non-negative Q8.8 bridge with a generated standalone binary32
  multiplier that forms an exact 24-by-24-bit significand product in 48 bits.
- Added finite signs, signed zero, normal/subnormal normalization, underflow,
  nearest-even rounding, and the established zero policy for non-finite inputs
  and finite overflow without importing an integer conversion helper.
- Added a 22-case raw-result VICE fixture covering tie rounding, normal and
  subnormal boundaries, wide exponent spans, overflow, and dead stripping,
  raising the broad direct-PRG matrix to 1281 cases.

## 2026-07-16 REAL32 Division

- Replaced the non-negative Q8.8 bridge with a generated standalone finite
  signed binary32 divider that no longer imports `rt_s_to_f`.
- Added normal/subnormal normalization, signed zero and underflow behavior, a
  27-bit restoring quotient, nearest-even rounding, and the established zero
  policy for non-finite inputs, zero divisors, and finite overflow.
- Added a 26-case raw-result VICE fixture spanning quotient rounding,
  normal/subnormal boundaries, wide exponent spans, overflow, unsupported
  values, and dead stripping, raising the broad direct-PRG matrix to 1282 cases.

## 2026-07-16 REAL32 Square Root

- Replaced the unsigned 16-bit floor-root helper with a generated standalone
  binary32 square root covering every non-negative finite input.
- Added normal/subnormal normalization, signed-zero handling, an exact 48-bit
  scaled radicand, a 24-step restoring integer root, and exact nearest rounding
  from the final remainder without helper imports.
- Added a 27-case raw-result VICE fixture plus deterministic lib6502 verification
  across every exponent boundary and randomized raw values, raising the broad
  direct-PRG matrix to 1283 cases.

## 2026-07-16 REAL32 Decimal Printing

- Replaced the non-negative Q8.8 printer with a generated standalone full-range
  finite binary32 formatter that imports no arithmetic helper modules.
- Added exact power-of-ten thresholding and 160-bit rational scaling to produce
  seven correctly rounded significant digits, signed fixed notation for decimal
  exponents `-4..6`, and trimmed `E+/-n` scientific notation otherwise.
- Added deterministic lib6502 string verification and a direct screen fixture
  spanning fixed/scientific boundaries, signed values, minimum subnormal, and
  maximum finite output, raising the broad direct-PRG matrix to 1284 cases.

## 2026-07-16 ALINK Relocation Scaling

- Decoupled relocation capacity from external-symbol capacity and assigned all
  64 four-byte records to the dedicated 256-byte REU relocation page.
- Replaced the per-output-byte REU table scan with an order-independent cursor,
  allowing the 38-relocation REAL32 printer to link within the CPU harness limit.
- Added a direct-PRG case with deliberately unordered named relocations, raising
  the broad matrix to 1285 cases while preserving OBJ source-order compatibility.

## 2026-07-16 Native REAL Bridge And Print

- Added compiler-owned native object emission for the first straight-line REAL
  slice: one `REAL(integer)` assignment followed by `PrintR` or `PrintRE`.
- The emitted OBJ carries root/data/pointer exports, ordinary helper and local
  relocations, and exact native `L` records for ACTDBG.
- Removed ALINK's matching body recognizer and PRG builder. This source form now
  reaches `BIN/MAIN.PRG` only through normal machine-object closure and
  relocation.
- Kept the generic emission overlay at 5,651 bytes, leaving 2,541 bytes in its
  8 KiB execution window and preserving the 2 KiB growth-headroom gate.

## 2026-07-16 Native REAL To INT

- Added compiler-owned native object emission for a `REAL(integer)` assignment
  followed by `INT(real)` conversion and direct INT storage.
- Emitted a relocatable six-byte data range, one REAL pointer, named low/high INT
  result stores, ordinary imports for `rt_i_to_f` and `rt_f_to_i`, and exact
  native `L`/`V` mappings.
- Removed ALINK's matching abstract-body recognizer, fixed-address PRG builder,
  and storage helpers; the existing source-backed probe now uses generic OBJ
  closure and checks the linked result at its relocated address.
- Kept `ACTC_OVL5.BIN` at 6,082 bytes, leaving 2,110 bytes free in its 8 KiB
  execution window and preserving the enforced 2 KiB growth headroom.

## 2026-07-16 Dedicated Native REAL Overlay

- Extended ACTC's one-character overlay selector from decimal to base-36 and
  assigned native REAL object emission to pass 10, `ACTC_OVLA.BIN`.
- Preserved emitter precedence with a compact resident pass table: local
  integer pass 9, single-procedure integer pass 8, native REAL pass A, then
  generic pass 5. Resident ACTC still retains its enforced eight-byte margin.
- Compiled native REAL detection and generation out of generic OV5. OV5 is now
  4,981 bytes with 3,211 bytes free; after the binary arithmetic, unary helper,
  and helper-prefixed print transfers OVLA is 5,756 bytes with 2,436 bytes free.
- Added header, ownership, headroom, export, DNP/D64 packaging, host-harness,
  and VICE launch coverage. The exact REAL print and REAL-to-INT programs still
  link as ordinary ALINK machine OBJ closure and return to UDOS successfully.

## 2026-07-16 Native REAL Binary Arithmetic

- Moved the straight-line two-literal REAL `+`, `-`, `*`, and `/` plus
  `PrintR`/`PrintRE` family into compiler-owned pass `ACTC_OVLA.BIN`.
- Added a relocatable 132-byte root containing A/B/X storage and a six-byte
  pointer table. Named overlapping data exports avoid fixed runtime addresses,
  while ordinary import relocations select conversion, arithmetic, and print
  helpers only when referenced.
- Removed ALINK's compact-body detector, fixed `$10xx` layout, PRG builder,
  pointer/storage helpers, and strategy ID for this family.
- Verified all four source programs through ACTC, generic ALINK OBJ closure,
  VICE launch, expected numeric output, and return to the UDOS prompt. Addition
  and subtraction also prove transitive selection of `rt_f_addsub_core`.

## 2026-07-16 Native REAL Unary Helpers

- Moved signed `FAbs(real)` and positive `FSqrt(real)` assignments followed by
  `PrintRE` into compiler-owned pass `ACTC_OVLA.BIN`.
- Added a relocatable 93-byte root with A/X data exports, a four-byte pointer
  table, exact native debug offsets, and ordinary conversion, unary-helper, and
  print relocations.
- Removed ALINK's two compact unary-body signatures, recognizer, fixed-address
  PRG builder, pointer helpers, scratch state, and strategy ID.
- Verified focused FAbs and FSqrt output, both `math1.act` split-library forms,
  all 17 source-backed math shapes, and all eight full-range helper cases under
  VICE. Each linked PRG returned directly to the UDOS prompt.

## 2026-07-16 Native Helper-Prefixed REAL Print

- Moved one-argument helper calls followed by `REAL(integer)` and `PrintRE`,
  both with and without storing the helper result, into `ACTC_OVLA.BIN`.
- Added 65-byte and 75-byte relocatable roots with exact native line mappings.
  The emitter recognizes all one-argument ALINK helper ABIs and generates either
  byte-in-A or word-in-X/Y setup before ordinary import relocations.
- Removed both ALINK strategy IDs, compact signatures, recognizers,
  fixed-address builders, and pointer/result helpers, reducing `ALINK.PRG` by
  729 bytes.
- Added two source-backed direct-launch probes. Both exact linked images print
  `7`, set the success marker, and return directly to UDOS on the first VICE
  attempt. The broad matrix now has 1,288 cases and the source-backed object
  emission matrix has 152 cases.

## 2026-07-16 Native REAL Control Pass

- Added base-36 compiler pass 11, `ACTC_OVLB.BIN`, with 4,145 bytes free in its
  8 KiB execution window.
- Moved plain, ELSE, and two-level nested REAL comparisons into compiler-owned
  126-, 140-, and 160-byte relocatable machine roots with A/B/Y data exports,
  pointer tables, exact debug records, and ordinary helper relocations.
- Removed ALINK's REAL IF strategy ID, all twelve compact signatures, its
  recognizer, and fixed-address builder, shrinking `ALINK.PRG` from 28,557 to
  27,043 bytes.
- Verified all 36 comparison variants through exact ACTC/ALINK output checks;
  representative plain, ELSE, and nested paths also execute and return to UDOS
  under VICE.

## 2026-07-16 Native REAL DO/UNTIL

- Extended `ACTC_OVLB.BIN` to own all six simple REAL `DO ... UNTIL`
  comparisons and eight ordered `A=A+C` / `A=A-C` update-loop forms.
- Added relocatable 146-byte simple roots and 194-byte binary-update roots with
  local A/B/C/Y data, pointer tables, exact debug offsets, and ordinary helper
  and backward-branch relocations. The pass is 5,655 bytes with 2,537 bytes of
  its 8 KiB window free.
- Removed ALINK's REAL DO/UNTIL strategy ID, recognizer, fixed-address builders,
  address/storage helpers, and ten compact signatures, shrinking `ALINK.PRG`
  from 27,043 to 24,431 bytes.
- Verified all 14 forms through exact ACTC/ALINK object and final-image checks
  and through the complete live VICE matrix. The release D64 builds with four
  blocks free.

## 2026-07-16 Generic ALINK Machine-Object Completion

- Moved the remaining REAL WHILE, runtime-condition, runtime-sequence, and
  nested-runtime lowering into ACTC passes `ACTC_OVLC.BIN` through
  `ACTC_OVLF.BIN` as relocatable machine OBJ records.
- Removed ALINK's remaining runtime-helper recognition, compact-body compiler,
  fixed-address templates, literal queues, and result-store queues. ALINK now
  accepts only OBJ1 machine bodies and computes the complete reachable
  project/library dependency closure before writing a self-contained PRG.
- Converted 102 historical seeded runtime fixtures to machine records. Kept
  194 simple runtime sequences under static exact-byte checks and added an
  independent object-parser/relocator oracle for 271 complex compiled-runtime
  cases, including two nested readbacks in `SpritePos(1,MouseX(),MouseY())`.
- Reduced production `ALINK.PRG` to 13,515 bytes while retaining 36 exports per
  loaded OBJ, a 64-entry reachable external closure, and a separate 64-record
  relocation table. The complete 1,288-case direct-PRG matrix includes a
  40-module transitive closure without a runtime runner or linker-side
  instruction synthesis.

## 2026-07-16 ALINK External Closure Boundary

- Added a generated 64-module transitive library chain that fills every entry
  in ALINK's production reachable-external queue and still emits and launches a
  self-contained direct PRG.
- Added a matching 65-module rejection case that requires `BAD OBJECT`, proves
  the 65th module is never loaded, and proves no partial output PRG is written.
- Raised the broad direct-PRG matrix to 1,290 cases and bound the success and
  overflow probes to the production `EXTERNAL_MAX=64` build contract.

## 2026-07-17 Linux Direct Recursive Calls

- Added direct self-call frame preservation to the optional Linux `actc` path.
  Mutable scalar parameters, scalar locals, and compiler temporaries are spilled
  to the 6502 hardware stack and restored in reverse order around each self-call.
- Preserved BYTE, CARD, and INT return values across frame restoration while
  retaining the existing immediate-copy contract for function-owned REAL result
  cells. Nonrecursive call emission remains unchanged.
- Added an execution regression that compiles and directly links a recursive
  CARD function, verifies `SumDown(5)` writes 15, and verifies the hardware stack
  returns to `$FF` after the PRG exits.
- Added a REAL-frame execution regression with a REAL parameter, REAL local, and
  recursive subtraction/addition. `SumDown(3.0)` writes exact binary32 `6.0`
  (`00 00 C0 40`) and returns with the hardware stack at `$FF`, proving the
  function-owned REAL return cell survives caller-frame restoration.

## 2026-07-17 Linux Mutually Recursive Calls

- Derived a local-routine call graph from parsed source and identified only the
  call edges whose target can reach the caller. The existing frame spill/restore
  sequence now covers those cyclic edges while acyclic local-call output remains
  byte-for-byte unchanged.
- Added an execution regression using mutually recursive `EvenSum` and `OddSum`
  CARD functions. The linked PRG writes 15 for an input of 5 and restores the
  hardware stack to `$FF`; the prior static-cell behavior produced 3.
- Documented scalar frame recursion precisely: direct and mutual cycles are
  stack-bounded, local array storage remains shared, and asynchronous reentry is
  still outside the host ABI.

## 2026-07-17 Self-Contained Host 6502 Harness

- Vendored the existing MIT-licensed `lib6502` source under
  `third_party/lib6502` and repointed the Tool ABI harness and exact floating-
  point runtime verifiers to that maintained copy.
- Removed the retired sibling tree from active setup probing and root cleanup;
  ActionC64U host verification now requires only the ActionC64U and UDOS trees.
- Added layout and active-path guards, then verified the harness plus exact
  division, square-root, and decimal-print reference suites through the new
  dependency location.

## 2026-07-17 Native C64 Input Semantics

- Replaced the hand-maintained joystick and mouse objects with a deterministic
  generator shared by the host and UDOS runtime trees.
- Made joystick button 2 follow the C64GS pin-9/POTX convention and made 1351
  proportional-mode mouse buttons follow the FIRE/UP lines. Both paths select
  the requested CIA1 paddle mux and allow the SID conversion to settle.
- Filtered the 1351 noise and don't-care bits, accumulated signed modulo-64
  movement in C64 screen coordinates, and retained independent position and
  inferred-presence state for both control ports.
- Added a direct linked-PRG execution proof covering both buttons, directions,
  noisy samples, coordinate wraparound, port switching, and idle/activity
  presence behavior.

## 2026-07-17 ACTC Fallback Scratch Ownership

- Removed seventeen bytes of resident BSS from the production compiler by
  allocating body-preallocation, body-collection, layout, positive-word-parser,
  and emitter scratch only when the corresponding resident fallback is built.
- Raised the production resident-headroom gate from 8 to 24 bytes. The measured
  BSS end is `$4AE5`, leaving 25 bytes before the `$4AFE` UDOS floor.
- Added inverse build coverage proving body, layout, and emitter fallback modes
  still retain their required state. That coverage also fixed two out-of-range
  layout dispatch branches and made the shared hardware runtime-symbol strings
  available when either the body or emitter fallback owns their use.

## 2026-07-17 ACTC Overlay ABI v3 Compaction

- Removed 28 legacy overlay-context bytes for source/output REU bases and
  resident callbacks that no shipped overlay consumes, then compacted the ABI
  from 237 to 209 contiguous bytes.
- Removed 35 bytes of resident initialization code for the retired source-base,
  scan-pointer-slot, and small-expression callback groups. Production CODE now
  ends at `$47D5` and BSS at `$4AA6`, leaving 88 bytes before the `$4AFE` UDOS
  floor.
- Bumped the internal overlay ABI to version 3 so stale binaries are rejected,
  raised the resident-headroom gate from 24 to 80 bytes, and added structural
  tests for contiguous offsets and absence of retired exports.
- Added a target-harness regression that stages and copies a deliberately
  downgraded v2 overlay, then proves ACTC returns `UNSUPPORTED_ABI` before
  changing the memory map or calling its entry point.

## 2026-07-17 Native Word FOR Loops

- Added target parser and compact body IR support for
  `FOR counter=initial TO final [STEP increment]`, the required following
  `DO`, and matching `OD`, with two sequential or nested loop instances.
- Extended `ACTC_OVL8.BIN` to stage final and increment expressions once,
  select unsigned ascending or descending comparison from the runtime step
  sign, emit named loop/exit exports, and terminate safely on zero increments
  and 16-bit overflow or underflow. ALINK performs only normal object closure
  and relocation.
- Added exact object-emission checks and direct ACTC-to-ALINK-to-PRG VICE
  coverage for default ascending loops, variable negative increments, zero
  increments, nested loops, and both `$FFFF` and `$0000` wrap boundaries. The
  linked tests also prove unreferenced integer multiply/divide runtime objects
  are pruned.
- Made loop-stack underflow and overflow explicit parser failures, with target
  regressions for unmatched `OD`/`UNTIL`, a missing required `DO`, and
  unterminated `FOR`/`DO` structure. `OD` is the sole closer for both loop
  forms, and failed sources leave no partial OBJ behind.

## 2026-07-17 Native Integer EXIT

- Added parser and compact-body support for `EXIT`, with compile-time rejection
  outside a loop and nearest-loop selection across nested `DO`, `WHILE`, and
  `FOR` bodies.
- Kept FOR EXIT in `ACTC_OVL8.BIN`, where it relocates directly to the existing
  `__fendN` export. Routed DO and WHILE EXIT through `ACTC_OVL9.BIN`, where the
  local-control stack allocates the concrete end label. ALINK performs only
  generic object closure and named relocation.
- Added malformed-source, exact-OBJ, nested inner-FOR, DO, WHILE, selective
  runtime-library pruning, and live direct-PRG VICE coverage. The DO execution
  proof cannot terminate through its `UNTIL` condition and therefore verifies
  that the EXIT jump actually executes.
- Compacted pass-8 duplicate target, relocation-offset, debug-offset, and
  helper lookup machinery and changed in-range pass-9 long-branch macros to
  direct 6502 branches. Pass 8 now owns dynamic-arithmetic plain `DO ... OD`
  and post-test `DO ... UNTIL ... OD` with nearest `EXIT`, using distinct
  backward and post-loop named relocations. Its 7,154-byte image retains 1,038
  bytes under the 1 KiB reserve, and FOR/post-test debug records remain exact
  across offset pages and consumed control tokens.
  Pass 9 owns simple plain `DO ... OD` loop-back
  relocation, including a post-loop EXIT target and a valid no-EXIT infinite
  form. Shared absolute-jump emission leaves `ACTC_OVL9.BIN` at 6,136 bytes with
  2,056 bytes free under its 2 KiB reserve. Exact OBJ and live direct-PRG tests
  prove the plain loop can terminate only through EXIT while unreferenced integer
  helper objects remain pruned.

## 2026-07-17 Native Dynamic WHILE Arithmetic

- Extended `ACTC_OVL9.BIN` with native 16-bit `+` and `-` stack operations,
  allowing dynamic updates inside pre-test WHILE control and multi-procedure
  local-control bodies without returning compact code to ALINK.
- Added exact OBJ coverage for a WHILE containing add, subtract, nested IF, and
  nearest-loop EXIT. The object carries independent loop, branch, EXIT, data,
  and pointer relocations.
- Added a live direct-PRG VICE proof that exits with both word variables equal
  to three and verifies that unreferenced print, multiply, and divide helpers
  are not linked.
- Extended the same emitter with helper-backed word multiply and divide. It
  discovers only the referenced runtime imports, emits ordinary `uN` call
  relocations, and leaves ALINK responsible only for generic dependency closure
  and relocation.
- Added exact OBJ and live direct-PRG coverage for multiply/divide inside a
  WHILE with nested IF/EXIT. The program exits with both word variables equal
  to six, links `rt_i_mul` and `rt_i_div`, and prunes the available print helper.
- Added pass-9 `PrintI`/`PrintIE` lowering inside WHILE control. The compiler
  emits an ordinary `rt_print_i` import relocation, ALINK includes print and
  arithmetic modules only when referenced, and a live direct PRG prints `1`
  and `2` before exiting with the loop variable equal to four.
- Added generic stack-neutral no-argument external calls to pass-9 control
  bodies. Each procedure marker carries its direct and reachable-local import
  closure; pure call-only bodies remain with the general emitter. Exact OBJ
  tests cover single- and multi-procedure calls, while a live `SidRst()` WHILE
  case verifies transitive SID dependency selection, unrelated SID pruning,
  register clearing, and loop completion. At that milestone the broad
  direct-PRG matrix contained 1303 cases and its compiled-runtime oracle
  covered 284.
- Pass 9 is now 7,167 bytes with 1,025 bytes free under its dedicated 1 KiB
  minimum reserve.

## 2026-07-18 Native Controlled One-Argument Runtime Calls

- Added base-36 pass 16, `ACTC_OVLG.BIN`, for one-word runtime calls nested in
  integer control when the selected helper consumes the low argument byte in A.
  The pass reuses compiler-owned local-control lowering and declines wider or
  unknown helper ABIs rather than guessing a calling convention.
- Added exact object coverage for the emitted argument pops, helper import,
  loop targets, initialized data, and relocations. ALINK remains generic and
  performs only reachable OBJ closure and relocation.
- Added a source-backed `SidVol(I+10)` WHILE launch proof. The linked PRG pulls
  only `RT_SID_VOL.OBJ` and its transitive volume-state object, sets `$D418` to
  volume 10, stores loop variable one, and prunes unrelated SID helpers.
- Extended the table-driven pass to complete one-word X/Y helper ABIs, with X
  receiving the low byte and Y the high byte. A source-backed
  `SidCutoff(I+300)` WHILE proof observes `$D415=$04`, `$D416=$25`, loop variable
  one, and only the referenced cutoff OBJ in ALINK's closure.
- Pass G is 7,621 bytes with 571 bytes free under its 512-byte minimum reserve.
  The broad direct-PRG matrix now contains 1306 cases and the independent
  compiled-runtime link oracle covers 288.

## 2026-07-18 Core ASMBLOCK Inline 6502

- Added `ASMBLOCK [ ... ]` to the UDOS-native C64 ACTC procedure grammar. The
  integrated two-pass assembler accepts all official NMOS 6502 opcodes and
  addressing modes, decimal/hex/binary operands, semicolon comments, forward
  and backward block-local labels, and normal absolute references to current
  module globals, procedure parameters, and locals.
- Pass 4 writes each assembled block to a private bank-0 REU page and derives
  legacy print flags from parsed body operations rather than raw source text.
  Pass 9 inserts the bytes and emits ordinary named OBJ relocations. ALINK
  remains unaware of ASMBLOCK syntax and only performs generic reachable-object
  closure and relocation.
- Corrected the native local-procedure parameter prologue to preserve the JSR
  return address while binding parameters in reverse declaration order. Mutable
  ASMBLOCK workspace now lives at `$9E00-$9F1E`, in a linker-reserved portion
  of overlay scratch below pass code and below the UDOS HIRAM boundary.
- Added exact opcode/addressing, symbol/parameter/local/global relocation,
  label/JMP, malformed-source, capacity, link, and live VICE coverage. The live
  direct PRG stores `$5A` at the expected result address after executing the
  linked ASMBLOCK path. The broad matrix now contains 1306 cases and the
  source-backed object-emission matrix contains 153 cases.
- `ACTC_OVL4.BIN` is 4,250 bytes. `ACTC_OVL9.BIN` is 7,878 bytes and leaves 314
  bytes under its dedicated 256-byte reserve. The complete `ACTION.DNP` carries
  ACTC, all overlays, ALINK, and ACTDBG; the capacity-limited D64 still retains
  15 free blocks.

## 2026-07-18 OBJ1 Byte Relocations

- Extended the existing OBJ1 `r` record with optional `l` and `h` modes that
  patch one low or high address byte. Existing records retain their 16-bit
  little-endian behavior, and ALINK still performs only generic symbol closure,
  placement, and relocation.
- Added `#<NAME` and `#>NAME` ASMBLOCK operands for globals, current procedure
  parameters and locals, and block-local labels. Numeric low/high extraction is
  accepted as well. The pass-4 page remains 256 bytes by encoding relocation
  kind in unused target bits.
- Added exact OBJ, malformed-source, malformed-object, independent link-oracle,
  and live VICE coverage. The live program constructs four linked pointers,
  jumps indirectly to a block label, and copies a parameter through local
  storage into a global. An adjacent low/high import case also jumps directly
  into a link-selected library export, while a final-byte overlap fixture proves
  duplicate relocation spans are rejected. The broad direct-PRG matrix now
  contains 1311 cases, and the source-backed object-emission matrix contains 155.
- `ACTC_OVL4.BIN` is 4,378 bytes, `ACTC_OVL9.BIN` is 7,927 bytes with 265 bytes
  free under its 256-byte reserve, and `ALINK.PRG` is 13,806 bytes.

## 2026-07-18 Core Word Functions And ASMBLOCK Symbols

- Added `BYTE`, `CARD`, and `INT FUNC` declarations to core UDOS-native ACTC.
  Typed scalar parameters and locals use the existing two-byte storage ABI;
  function metadata uses the high bit of the parameter-count byte without
  changing OBJ1 or the overlay context layout.
- Added native local-function calls and returns to pass 9. Calls emit `JSR`
  followed by A/X result pushes, and `RETURN(expression)` restores the low byte
  to A and high byte to X before `RTS`. Procedure calls remain no-result calls,
  and bare `RETURN` remains their normal return form.
- Extended every source-body pass so `ASMBLOCK` inside a function resolves that
  function's parameters and locals, module globals, and private assembly labels.
  Declaration pass 2 rejects bare function returns and unsupported `REAL FUNC`
  declarations before generic fallback emission while preserving legacy
  procedure value-return source compatibility.
- Added exact compiler OBJ coverage and a direct ALINK/VICE proof. The linked
  PRG binds grouped `CARD P,Q` parameters, returns 42 through A/X to `$033C`,
  and writes the first input value 40 from the function ASMBLOCK to `$033D`.
  The broad direct-PRG matrix now contains 1,311 cases and the source-backed
  object-emission matrix contains 155.
- `ACTC_OVL2.BIN` is 6,110 bytes, `ACTC_OVL4.BIN` is 4,431 bytes,
  `ACTC_OVL6.BIN` is 8,081 bytes with 111 bytes free under its 96-byte gate, and
  `ACTC_OVL9.BIN` is 8,064 bytes with 128 bytes free under its 128-byte gate.
  Function-aware `ACTC_OVLG.BIN` is 7,960 bytes with 232 bytes free under its
  224-byte gate; rebuilt pass F retains 1,278 bytes under a 1,264-byte gate.

## 2026-07-18 Mixed ASMBLOCK And Runtime Functions

- Added base-36 pass 17, `ACTC_OVLH.BIN`, for typed integer units that combine
  pass-4 ASMBLOCK pages with one-word runtime calls inside native control flow.
  Pass H emits one machine OBJ; ALINK still performs only generic closure and
  relocation and selects runtime modules only when imported.
- Shared resident decimal and uppercase-hex formatter callbacks across object
  emitters. Pass 9 is now 7,859 bytes, pass G is 7,491 bytes, and pass H is
  8,054 bytes with 138 bytes free under a 128-byte gate.
- Added exact OBJ and live ACTC/ALINK/VICE coverage. The linked PRG binds a
  function parameter in ASMBLOCK, invokes `SidVol` in a WHILE loop, returns 42,
  stores trace value 41, and writes SID volume 8. The direct matrix has 1,312
  cases and the source-backed object-emission matrix has 156.
- Packaged passes 0 through H in both `ACTION.DNP` and the D64. The D64 retains
  ALINK plus compact copy/delete/directory/tree tools and has three blocks free;
  the complete workspace retains every development tool.

## 2026-07-18 ASMBLOCK REAL Storage And Decimal Operands

- Extended pass 9 and mixed pass H to preserve each ASMBLOCK-visible variable's
  declared storage width. `REAL` globals and locals now receive four-byte OBJ
  exports and data allocation, while word scalar exports remain two bytes.
- Corrected decimal operand consumption to advance the streaming source cursor,
  and made X/Y register parsing preserve the preceding operand symbol. Exact
  tests cover decimal constants, indexed block labels, four-byte native data,
  relocations, and mixed ASMBLOCK/runtime emission.
- Added source-backed exact ALINK and live VICE coverage. The linked direct PRG
  writes and reads offsets zero and three of global and local REAL storage and
  observes `$033C-$033F = $11,$44,$22,$55` with no runtime helper imports.
  The broad matrix now has 1,313 cases and the source-backed object-emission
  matrix has 157.
- Rebuilt `ACTC_OVL4.BIN` is 4,456 bytes. `ACTC_OVL9.BIN` is 7,868 bytes with
  324 bytes free, and `ACTC_OVLH.BIN` is 8,063 bytes with 129 bytes free; both
  native passes retain their 128-byte minimum reserve. The release D64 retains
  three free blocks.

## 2026-07-18 Initial Core REAL Function Return

- Added local no-argument `REAL FUNC` declaration, direct REAL-variable return,
  and direct REAL-assignment call lowering to the UDOS-native compiler. A/X
  carries the returned storage address and the caller copies all four bytes.
- Added exact OBJ relocation checks plus a source-backed ACTC/ALINK/VICE proof.
  The linked direct PRG converts 42 to binary32 and copies `00 00 28 42` through
  the function return path. The broad direct-PRG matrix now has 1,314 cases and
  the source-backed object-emission matrix has 158.
- Compacted `ACTC.PRG` to the exact 65-block D64 boundary and
  `ACTC_OVLA.BIN` to 6,347 bytes. The release image retains every listed
  compiler/linker/tree component and builds at full D64 capacity.

## 2026-07-18 Generalized Core REAL Function Storage

- Replaced fixed source/destination selectors in the initial local no-argument
  REAL-function emitter with captured base-36 module-variable selectors. OBJ
  exports, aggregate data allocation, root size, and pointer placement now
  derive from the complete all-REAL module-global declaration list.
- Added exact OBJ and live ACTC/ALINK/VICE coverage with an unused first REAL,
  source in `__v1`, and destination in `__v2`. The linked direct PRG stores
  binary32 42.0 (`00 00 28 42`) at `$104A-$104D` while selecting only
  `RT_I_TO_F.OBJ`. The broad matrix now has 1,315 cases and the source-backed
  object-emission matrix has 159.
- Shared repeated opcode and scan-name emission reduced `ACTC_OVLA.BIN` to
  6,313 bytes while retaining the 1,792-byte headroom gate. `ACTC.PRG` remains
  16,510 bytes, and the full-capacity release D64 still builds successfully.

## 2026-07-18 Mixed-Width Core REAL Function Storage

- Replaced the remaining four-bytes-per-global assumption with declaration
  width accumulation. Function-mode OBJ exports now preserve two-byte
  `BYTE`/`CARD`/`INT` and four-byte REAL module globals while still requiring
  the captured return source and direct assignment destination to be REAL.
- Added exact OBJ and live ACTC/ALINK/VICE coverage for a leading CARD followed
  by source and destination REAL variables. The linked direct PRG stores
  binary32 42.0 at `$1048-$104B`, and ALINK selects only `RT_I_TO_F.OBJ`.
  The broad matrix now has 1,316 cases and the source-backed object-emission
  matrix has 160.
- Consolidated repeated scan-name setup while adding width-aware layout logic.
  `ACTC_OVLA.BIN` is 6,345 bytes, `ACTC.PRG` remains 16,510 bytes, and the
  full-capacity release D64 still builds with zero blocks free.

## 2026-07-18 IEEE-754 REAL32 Exceptional Values

- Replaced the former zero-result fallbacks for non-finite arithmetic, finite
  overflow, division by zero, and negative square root with default IEEE-754
  binary32 value semantics. Results now include signed infinity, signed zero,
  gradual underflow, and canonical quiet NaN (`$7FC00000`) as appropriate.
- Added dependency-only `RT_F_SPECIAL.OBJ` for shared classification and result
  construction. Arithmetic, comparison, and square-root modules import it;
  ALINK selects it through ordinary reachable OBJ closure and leaves it out of
  programs that do not reference those helpers.
- Defined comparator result `2` as unordered. ACTC's `<`, `<=`, `=`, `>=`, and
  `>` predicates reject it while `<>` accepts it. `RT_PRINT_F.OBJ` now prints
  `Infinity`, `-Infinity`, and `NaN` instead of mapping non-finite values to
  zero.
- Added exact lib6502 verification for 9,216 add/subtract/multiply/compare,
  4,537 divide, 5,662 square-root, and 4,127 formatting vectors, plus live
  target-linked VICE probes for all seven helper paths. Generated runtime OBJ
  symbols are now checked against ALINK's 23-character format limit.
- Rebuilt the complete `ACTION.DNP` and capacity-limited release D64 with the
  new helper. The D64 remains valid at zero blocks free.

## 2026-07-18 One-Word-Parameter Core REAL Function

- Extended the local core REAL-function specialization from no arguments to one
  typed two-byte scalar supplied by a direct integer literal. The callee binds
  the argument through the established scalar stack ABI, converts it with
  `REAL(parameter)` into named module REAL storage, and returns that storage
  pointer in A/X for the caller's four-byte copy.
- Emitted only ordinary OBJ exports, machine records, local/export/import
  relocations, and a reachable `rt_i_to_f` import. Exact compiler checks, the
  source-emission entrypoint, and live VICE prove the parameter is `$002A` and
  both source and destination hold binary32 42.0 (`00 00 28 42`). ALINK has no
  REAL-function or parameter-binding special case.
- The broad direct-PRG matrix now contains 1,317 cases and the source-backed
  object-emission matrix contains 161. Its complete segmented run also corrected
  two stale nonzero-update REAL `WHILE >=`/`<=` expectations to reject unordered
  compare result `2`; both corrected cases pass linked and live.
- Compacted adjacent parameter byte templates and shared function zero-fill
  emission. `ACTC_OVLA.BIN` is 6,843 bytes with 1,349 bytes free under a
  1,280-byte reserve. The complete `ACTION.DNP` retains every tool; the
  full-capacity D64 omits redundant `ACTCOPY.PRG` because resident `COPY` covers
  flat-image use and has zero blocks free.

## 2026-07-18 Imported MATH1 And GFX1 Completion Goals

- Added `new_math_func.txt` and `new_gfx_func.txt` as the maintained port
  contracts for the larger MATH1, GFX1, ACTSPRITE, and ACTBITMAP surfaces. They
  preserve direct C64 6502 PRG execution: generated programs must not call a
  UDOS resident service or a separate runtime runner.
- The existing link-selected IEEE-754 arithmetic, conversion, print, low-level
  VIC-II, and sprite OBJ modules are the implementation base. New helpers,
  portable library bodies, and embedded resources must enter a linked PRG only
  through ordinary reachable import/export closure.
- Compiler prerequisites come first: general REAL constants/literals,
  parameters, locals, calls, expressions, and returns for MATH1; then global
  `SPRITE`/`MSPRITE`/`BITMAP`/`MBITMAP` resource declarations, validated ASP1
  and ABM1 loading, 64-byte sprite alignment, and relocatable asset exports.
- Library delivery follows the compiler ABI rather than bypassing it with
  linker synthesis. Port MATH1 utilities before transcendental families, then
  tracked GFX setup/pixels/shapes, bitmap-resource operations, and sprite-
  resource operations. Preserve export-body reachability so an unused family
  contributes no code or data.
- Tooling follows the resource format: add ACTSPRITE and ACTBITMAP editors,
  bind ACTEDIT F8 dispatch, add library-help catalog entries, and validate
  known math values plus graphics boundary, banking, mode, and `$01` restore
  behavior in target-linked VICE probes before recording real-hardware results.

## 2026-07-18 Named-Storage Core REAL Function Argument

- Extended the one-word-parameter REAL-function specialization with the first
  named-storage caller form: a module word scalar initialized by the immediately
  preceding literal assignment can be passed to the local REAL function.
  Caller machine code stores and reloads the scalar, pushes low/high bytes via
  the established stack ABI, and the unchanged callee binds and converts it.
- The OBJ contains ordinary named relocations for all four argument store/load
  operands plus the existing local-function, destination, source-byte, helper,
  and data relocations. ALINK remains a generic closure/relocation linker.
- Exact compiler checks, direct ALINK launch, the source-emission wrapper, and
  live VICE validate the argument and bound parameter as `$002A` and source and
  destination as binary32 42.0. The broad matrix now has 1,318 cases and the
  source-backed object-emission matrix has 162.
- Compressed the repeated `RT_` prefix from pass A's 37 internal helper-match
  strings and shared scan-name pointer setup. `ACTC_OVLA.BIN` is 6,847 bytes,
  four bytes above the prior build, with 1,345 bytes free under the 1,280-byte
  reserve; the release D64 remains valid at zero free blocks.

## 2026-07-18 Idun-To-UDOS Feature Parity Baseline

- Audited the native UDOS product against the current Idun/Alpine fork at the
  language, library, OBJ1, direct-PRG, runtime, editor, debugger, example, and
  release boundaries. Direct linking, ASMBLOCK, IEEE-754 core behavior,
  INPUT1's 19 declarations, DBF1's 20 declarations, SIDSPR1's 37 declarations,
  and native source debugging already have OS-appropriate equivalents.
- Recorded the actual gaps in `docs/idun_feature_parity.md`: general mixed
  ASMBLOCK composition and source-prefix comments, the complete MATH1 surface
  beyond four native declarations, the complete GFX1/resource surface beyond
  fifteen native declarations, native resource editors/F8 dispatch, and
  formatter/help workflow parity. Linux sockets, SQLite, APKs, and `actsvc` are
  explicitly Idun-only rather than false native requirements.
- Added `ASMBLOCK_DEMO.ACT` as a native-specific example that emits ordinary
  machine OBJ records, relocates a global, uses a private branch label, and
  writes the result to screen memory. Added compiler and exported-workspace
  regressions; the focused layout, export, and native ACTC tests pass 11/11.
- Probed the richer Idun sample before porting it. Leading comments fail before
  MODULE in the native streamed pipeline, and assignment/PrintIE surrounding
  ASMBLOCK can select a compact rejection body. Those behaviors remain listed
  as compiler work instead of being hidden by an example that ALINK cannot use.
- The full project gate exposed D64 overflow after the current compiler and
  recursive-tool growth. Kept `ACTDEL.PRG` and `ACTDIR.PRG` in complete
  `ACTION.DNP`, and kept recursive `DELTREE.OVL` there as well. The
  capacity-limited D64 relies on resident `COPY`, `DEL`, and `DIR`, retains
  unique `TREE` and `XCOPY`, and now has capacity safety instead of an invalid
  exactly-full image.

## 2026-07-18 Feature-Parity Integration Gate

- Replaced pass A's duplicated 37-name input-helper classification catalog
  with reserved `RT_` namespace validation and one emitted setup that supplies
  the argument in both supported ABIs: A receives the low byte and X/Y receive
  the word. Future one-argument link-selected helpers no longer require a
  second compiler-side name table.
- Updated exact machine, relocation, source-debug, and non-runtime rejection
  checks. `ACTC_OVLA.BIN` is now 6,703 bytes with 1,489 bytes free, restoring
  the 1,280-byte native-REAL overlay reserve without weakening the guard.
- Synchronized Linux test-library closure with dependency-only
  `RT_F_SPECIAL`, current IEEE-754 module sizes, and exact division,
  square-root, and formatting proof totals. Updated current ACTC and ALINK
  matrix counts to 163 and 1,319 respectively.
- Rebuilt the UDOS release and refreshed the generated direct-PRG oracles.
  VICE launched both native REAL input bridge cases on the first attempt,
  printed `7`, and reached the exit marker using only reachable runtime
  modules. The release D64 remains valid with four blocks free.
- The complete ActionC64U suite passes 741/741 tests in 653.155 seconds. The
  separately maintained Idun fork documentation and Linux product suite pass
  141/141 tests; the remaining cross-product gaps stay explicit in
  `docs/idun_feature_parity.md`.

## 2026-07-18 Cross-Product Prefix Comment Parity

- Made the resident source-header path and the source-header overlay skip any
  number of leading semicolon comment lines before `MODULE`, without relying
  on lookahead beyond the current REU source window.
- Made the declaration-count overlay use the same comment-aware top-level
  source scan. This closes the later `DECL OVL FAIL` path that remained after
  header recognition alone was corrected.
- Added resident-boundary and multi-window overlay regressions; the latter
  crosses more than two 128-byte REU windows. The shipped ASMBLOCK example now
  begins with documentation comments so normal compile/export tests retain the
  behavior.
- Updated the Idun/UDOS capability matrix to mark prefix comments and ordinary
  ASMBLOCK composition as parity. The richer Idun sample isolates the remaining
  native syntax gaps as relocatable `symbol+constant` operands and fixed
  register-entry `=*(...)` routines.
- The focused source-reader, shipped-example compile, and workspace-export
  regressions pass. The pre-change integration baselines remain 745 native
  tests, 133 UDOS tests with one intentional capacity skip, 145 Idun tests, and
  20 Idun direct-PRG tests with the local VICE 3.7 long-DBF version skip.

## 2026-07-18 Cross-Product OBJ1 Relocation Addends

- Added signed `symbol+constant` and `symbol-constant` ASMBLOCK operands for
  word, low-byte, and high-byte relocations. Native source addends are bounded
  to -128 through 127 and occupy the previously spare per-relocation bytes in
  the fixed REU block page, preserving existing code, label, and relocation
  capacities.
- Extended native ALINK to apply optional signed decimal OBJ1 addends after
  placement with 16-bit range checks. Both native and Linux linkers now accept
  compact `l`/`h` and long `lo`/`hi` byte-selector spellings, so either
  compiler's objects can be consumed by either linker.
- Extended the independent direct-PRG oracle to parse and range-check the same
  records. Direct VICE launches passed for source-generated word `+1`/`-1`,
  low/high `+1`, and Linux-style selector records; the broad ALINK matrix passes
  all 1,320 cases.
- Corrected an existing native REAL binary emitter off-by-one that produced one
  more body marker than export. The strengthened regression requires exact
  export/body cardinality, and the repaired fraction object links through the
  exact-printer and division dependency closure.
- Measured the heaviest repaired REAL closure at 26,462,369 host-emulated ALINK
  instructions and set the deterministic harness ceiling to 40 million. This
  changes only the verifier budget, not generated PRGs or target execution.

## 2026-07-18 Native Fixed Register-Entry ABI

- Added pass-2 metadata and pass-9 lowering for `PROC` and BYTE/CARD/INT
  `FUNC name=*(...)` machine routines. Up to 16 parameter bytes flatten
  left-to-right into A, X, Y, then `$A3-$AF`; BYTE results return in A and word
  results in A/X. REAL ABI shapes and Action locals are rejected.
- Kept the implementation entirely in compiler-emitted OBJ1 machine exports
  and ordinary JSR relocations. Machine bodies use ASMBLOCK and own `RTS`;
  ALINK remains a generic closure/placement linker and no runtime runner was
  introduced.
- Added exact object coverage and a direct ACTC/ALINK/VICE probe. The live PRG
  verifies no-argument BYTE return, CARD return, fourth-byte `$A3` placement,
  and mixed BYTE/CARD/BYTE A/X/Y/`$A3` placement across eight result bytes.
- Compacted the body parameter-bind loop after the new metadata check.
  `ACTC_OVL6.BIN` is 8,091 bytes with 101 bytes free under its 96-byte gate;
  machine-enabled `ACTC_OVL9.BIN` is 8,062 bytes with 130 bytes free under its
  128-byte gate.
- Expanded the broad direct-PRG inventory to 1,321 cases and the source-backed
  object-emission inventory to 165, including the previously unlisted
  ASMBLOCK-addend launch shape. Updated both product parity documents to
  separate shared generated-program behavior from Linux-only and UDOS-only
  implementations and to expose the remaining raw-body, expression, general
  type/function/REAL, MATH1, GFX1, resource, editor, and workflow work.

## 2026-07-18 Fixed-Entry Selector And Numeric-Literal Closure

- Added a resident metadata scan that routes every fixed register-entry unit to
  the capable pass-9 emitter. Unsupported REAL results/parameters, Action
  locals, and signatures wider than 16 flattened bytes now fail explicitly
  before an OBJ stream is opened instead of falling back to opaque output.
- Generalized streamed numeric tokens and ordinary word-call parsing to accept
  decimal, `$` hexadecimal, and `%` binary 16-bit literals. A zero-lookahead
  REU regression splits each radix form across a 256-byte source window.
- Rebuilt the UDOS release and passed the direct ACTC/ALINK/VICE fixed-entry
  probe with radix arguments and exact A/X/Y/`$A3` result checks. Raw bracketed
  machine bodies remain the next fixed-routine syntax-parity task.
- Passed all 165 source-backed ACTC/ALINK/live-VICE shapes and all 1,321 broad
  direct-PRG ALINK shapes with the rebuilt artifacts.
- Rechecked the synchronized Idun fork: 146/146 Linux product tests, 132/132
  ASan/UBSan tests, and 20 direct-PRG tests pass with the one documented local
  VICE 3.7 DBF/REU version skip. Its 31-command, 260-topic export and strict
  environment/path verification pass.

## 2026-07-18 Native Raw Code Blocks

- Added unchecked `[ ... ]` code bodies to the native fixed register-entry
  path. Decimal/hex/binary byte and little-endian word values, apostrophe
  characters, signed words, positive constant sums, compact adjacent values,
  storage/local-routine addends, and current-code-address relocations emit as
  ordinary OBJ1 records; ALINK remains source-agnostic and no runner exists.
- Added exact object coverage and a direct ACTC/ALINK/VICE ABI shape. The live
  PRG verifies BYTE/CARD returns plus A/X/Y/`$A3` argument placement and forces
  ALINK to process raw local-routine/current-address records after an
  unreachable `RTS` payload.
- Shared the duplicated normal/machine call-relocation tail instead of reducing
  the capacity gate. `ACTC_OVL4.BIN` is 5,603 bytes, `ACTC_OVL6.BIN` is 8,090
  bytes with 102 free, and `ACTC_OVL9.BIN` is 8,063 bytes with 129 free under
  its 128-byte reserve. Inventories are now 1,322 broad and 166 source-backed
  shapes; named `DEFINE` and external/fixed-address expressions remain in the
  wider native compiler-constant backlog.
- Passed the complete 166-case source-backed ACTC/ALINK/live-VICE matrix and
  added focused coverage for ordinary ASMBLOCK calls to module-local routines.
  The 1,322-case broad inventory remains a separate release-validation gate.
- Revalidated all 754 native unittests after classifying the hexadecimal and
  binary source-token scanners under the existing REU-reader guard.

## 2026-07-19 Native Preprocessing And Typed Constants

- Added atomic REU preprocessing for token-aware `DEFINE`, compatibility
  `SET`, recursive project `SRC`/`LIB` `INCLUDE`, source precedence, cycle
  detection, and bounded diagnostics. Failed preprocessing leaves the original
  staged source untouched.
- Added storage-free BYTE/CHAR/CARD/INT typed constants with decimal, hex, and
  binary literals, signed INT ranges, prior constant substitution, literal
  `LSH` evaluation, and multiline declarations. At this checkpoint, REAL
  constant text was substituted into source forms supported by the native REAL
  compiler; later entries complete integer and binary32 expression folding.
- Widened declaration validation and OBJ `v` emission for canonical 16-bit
  initializers. Focused tests cover `$C130`, `7`, `7 LSH 4`, `-2`, range
  rejection, REAL text substitution, directive nesting, token boundaries,
  source precedence, capacity limits, and include cycles.
- Reclassified the capacity-constrained D64 as a valid UDOS boot plus
  standalone ALINK disk. The complete ACTC and passes 0 through I remain in
  `ACTION.DNP`, which is the primary C64 Ultimate development medium. Release
  construction and image-contract tests pass without publishing a partial
  compiler.
- Updated both product parity documents with an OS adaptation map and the
  remaining dependency-ordered native work. Linux process, SQLite, socket,
  and APK mechanics are not native feature requirements; shared Action,
  OBJ1, runtime, PRG, library, and useful workflow semantics are.
- Split atomic preprocessing from the full pass-1 image into dedicated pass
  `I`. Pass 1 is now a 788-byte streamed module validator; pass `I` is 4,648
  bytes and leaves 3,544 bytes of code-window headroom. Its transform workspace
  was subsequently moved to the shared `$8000-$9FFF` scratch window. Focused preprocessing,
  long-source, overlay-contract, and export-inventory tests pass.

## 2026-07-19 Native Integer Constant-Expression Parity

- Replaced the literal-only typed-constant evaluator with a bounded shunting-
  yard evaluator for Idun's complete integer `CONST` grammar: signed 64-bit
  checked arithmetic, parentheses, shifts, bitwise operations, apostrophe
  characters, all numeric radices, and shared built-in constants.
- Added a portable source fixture compiled by both products. Native substitution
  values and Idun OBJ initializer bytes agree for every operator, precedence,
  signed division/remainder, wide intermediate, logical shift, and built-in
  constant case; invalid overflow, divide-by-zero, shift, and syntax cases fail.
- Added a peer guard requiring all `tests/parity/*.act` fixtures to remain
  byte-identical alongside the existing shared target-module digest guard.
- Replaced the fixed 15-slot definition arrays with packed records in the same
  1,350-byte footprint. A shared 24-constant fixture carries the complete GFX1
  and MATH1 constant headers, and redefinition plus actual-store exhaustion
  regressions enforce the new contract.
- Pass `I` was 7,019 bytes with 1,173 bytes of code-window headroom at this
  checkpoint. Its 3,147-byte workspace now occupies `$8000-$8C4A`. Binary32
  constant folding and external routine-symbol expressions remained next.

## 2026-07-19 Native Numeric Absolute-Address Routines

- Added bodyless `PROC` and BYTE/CARD/INT `FUNC` declarations at decimal, `$`
  hexadecimal, or `%` binary 16-bit addresses. Calls use the shared register
  ABI and emit a direct `JSR` with no wrapper, export, import, or runtime object.
- Added compact pass `J` and widened universal pass `H` so fixed addresses can
  compose with ASMBLOCK, `=*(...)`, runtime-argument calls, and integer control.
  Pass J is now 7,901 bytes with 291 bytes free under a 256-byte reserve; pass H
  is 8,064 bytes with exactly 128 bytes free in the `$A000-$BFFF` emitter window.
- Moved ASMBLOCK pages, body/debug records, and fixed declaration metadata into
  reserved REU bank `$FF`, outside source-cache banks `$01-$FE`. Every pass has
  the same hard `$A000-$BFFF` code ceiling; mutable pass state uses
  `$8000-$9DFF`, with `$9E00-$9FFF` reserved for ASMBLOCK; UDOS live state at
  `$C000+` is never touched.
- Added exact OBJ, direct ALINK closure, and live VICE coverage using KERNAL
  CHROUT at `$FFD2`.
- Added forward/backward local routine aliases with signed 16-bit symbol-first
  literal addends. ACTC emits named OBJ1 relocations rather than guessing final
  addresses; a source-backed direct PRG resolves a `WORKERALIAS` declaration,
  prints `!`, and selects no library object. Inventories are now 1,324 broad and 168
  source-backed shapes; both new focused shapes pass, while refreshed complete
  matrices remain release-validation gates.
- Extended pass I to canonicalize grouped numeric address expressions and local
  routine aliases with a checked signed 16-bit expression on either side of the
  symbol. `WORKER+(2*3)` and `(1 LSH 2)+WORKER` emit ordinary named relocations
  with addends 6 and 4; `($FFD0+2)` emits the same direct call as `$FFD2`.
- At this checkpoint pass I was 7,616 bytes with 576 bytes free under its
  unchanged 512-byte
  reserve. The Idun parser now locates the final top-level parameter group, and
  both products pass equivalent grouped-address regressions. Linux process
  services and UDOS implementation mechanics remain deliberate differences.

## 2026-07-19 Native REAL CONST Binary32 Parity

- Added bounded native folding for decimal and exponent literals, radix-prefixed
  integers, prior REAL constants, unary signs, grouping, `+`, `-`, `*`, `/`,
  `REAL`, `FABS`, `FSQRT`, `INF`/`INFINITY`, and `NAN`.
- Decimal conversion uses an exact 448-bit integer ratio. Conversion and every
  intermediate operation round to binary32 with round-to-nearest, ties-to-even;
  tests cover minimum subnormal, half-way underflow, maximum finite, overflow,
  signed zero, ties, infinity, NaN, precedence, and malformed expressions.
- Added a deterministic generator that closes the shared OBJ1 floating-point
  modules into a compiler-private resident evaluator. Overlay ABI v5 exposes
  that evaluator to pass I without linking compiler-private code into generated
  applications.
- Pass I is now 7,680 bytes at `$A000-$BDFF` and retains exactly its enforced
  512-byte reserve. Its mutable workspace is 3,150 bytes at `$8000-$8C4D`.
- Added a source-backed direct-PRG proof for `(1.5+2.25)*2.0`. It emits literal
  binary32 `7.5`, links only `RT_PRINT_F.OBJ`, prints `7.5` in VICE, and rejects
  unrelated conversion and arithmetic modules. Current inventories are 1,325
  broad direct-PRG cases and 169 source-backed shapes; both matrices pass.
- The next parity dependency is general native REAL declarations, locals,
  parameters, expressions, calls, and returns sufficient to compile portable
  multi-function MATH1 modules.

## 2026-07-19 Native Two-REAL-Parameter ABI Checkpoint

- Extended native pass A with a bounded `REAL FUNC F(REAL A,B)` form. The
  caller pushes named REAL addresses left-to-right, the callee copies each
  four-byte value into distinct parameter storage, restores the 6502 return
  address, and returns the first parameter's storage pointer in A/X.
- Kept ALINK generic. The emitted OBJ contains ordinary machine/export/body/
  relocation records and selects only `RT_I_TO_F.OBJ` for the two immediate
  `REAL(integer)` initializers; no runner or function-specific linker path was
  added.
- Added exact OBJ and direct-PRG matrix coverage. The deterministic ACTC/ALINK
  probe and live VICE launch verify both caller values, both callee copies, and
  the returned IEEE-754 value. Inventories are now 1,326 broad and 170
  source-backed cases.
- Pass A is 7,406 bytes with 786 bytes free under its revised 768-byte reserve.
  General REAL expressions, control-flow function bodies, nested calls, and
  dependency-sized MATH1 modules remain the next compiler work.

## 2026-07-19 Native Finite REAL Function Control Checkpoint

- Added dedicated pass `K`, `ACTC_OVLK.BIN`, for the exact two-parameter form
  `REAL FUNC MIN2(REAL A,B)` with `IF B<A THEN RETURN(B) FI RETURN(A)`.
- The caller initializes two named REAL values, passes them by value, invokes a
  named function export, and copies the returned pointer value into independent
  result storage. The function calls ordinary `RT_F_CMP.OBJ` and selects the
  correct parameter without a linker-specific REAL path.
- The enclosing root body records both reachable imports while the function
  export records only comparison. Generic ALINK therefore selects
  `RT_I_TO_F.OBJ`, `RT_F_CMP.OBJ`, and transitive `RT_F_SPECIAL.OBJ` and prunes
  unrelated REAL arithmetic and print modules.
- The rebuilt release, focused static probe, and live VICE launch pass with
  exact storage checks for caller values 2.0/1.0, callee copies 2.0/1.0, and
  result 1.0. The complete 171-case source-backed live matrix passes; the broad
  inventory remains 1,327 direct-PRG cases.
- The exact source now lives in both products' `tests/parity` trees. Idun
  ACTC/ALINK compile and link it directly, and its PRG returns binary32 1.0 in
  VICE. Idun folds the constant conversions while native executes reachable
  `RT_I_TO_F.OBJ`; the different helper closure is optimizer-owned.
- Pass K is 3,257 bytes with 4,935 bytes free in its 8 KiB code window. This
  bounded finite select is not full `FMin` NaN behavior; general REAL expression
  trees, arbitrary function control, nested calls, and MATH1 modules remain next.

## 2026-07-20 Native MATH1 Minimum/Maximum Selector Slice

- Added independently link-selected `RT_F_MIN.OBJ` and `RT_F_MAX.OBJ` modules.
  Each is 77 bytes, imports only `RT_F_CMP.OBJ`, and obtains exceptional-value
  support through comparison's ordinary dependency closure.
- Matched portable MATH1 semantics exactly: one NaN selects the other operand,
  two NaNs select the right operand, and equal ordered values preserve the left
  operand bit-for-bit, including signed zero.
- Extended native ACTC's bounded REAL value parser to lower `FMin(A,B)` and
  `FMax(A,B)` with named REAL operands in assignments, `PrintR`/`PrintRE`, and
  REAL conditions. The existing infix parser and emitter paths are reused;
  general nested REAL expressions and arbitrary MATH1 bodies remain separate
  work.
- Passed 2,304 deterministic edge/random pairs for each selector in the exact
  host runtime verifier. Focused ACTC object checks, rebuilt-release VICE
  launches, all 32 MATH1 source shapes, and all eight full-range helper probes
  pass while proving sibling-helper pruning.
- The broad direct-PRG matrix now contains 1,329 shapes, the source-backed
  object-emission matrix remains at 171 shapes, and 288 complex runtime cases
  use the independent object/relocation oracle. The shared target manifest and
  Idun peer comparison pass.
- The next dependency remains general native REAL expression/call/return
  lowering sufficient to split the rest of portable MATH1 into reachable-only
  OBJ modules. ALINK remains generic and no runtime launcher was introduced.

## 2026-07-20 Native MATH1 Sign Slice

- Added dependency-free `RT_F_SIGN.OBJ` generation and synchronized native and
  UDOS runtime copies. It maps every NaN to canonical quiet NaN, preserves both
  signed zero representations, and returns signed one for every other finite
  or infinite input.
- Refactored REAL assignment collection to reuse the shared REAL-value emitter,
  removing duplicated copy and unary lowering. `ACTC_OVL6.BIN` now uses 7,962
  bytes and leaves 230 bytes in its 8 KiB window, exceeding the enforced
  96-byte reserve while adding `FSign` syntax.
- Extended preallocation and body collection for named-REAL `FSign(A)` in
  assignments, REAL prints, and conditions. The compiler emits only
  `RT_F_SIGN.OBJ`; no sibling MATH1 helper becomes reachable.
- Passed 2,304 exact edge/random runtime cases, focused compiler object checks,
  and the direct-link matrix case that prints `-1`. At this checkpoint, the
  broad direct-PRG matrix contained 1,330 shapes, its compiled-runtime
  relocation oracle covered 289 cases, and the source-backed object-emission
  matrix remained at 171 shapes.
- Native MATH1 now exposes seven low-level calls. General REAL expression,
  function, and frame lowering remains the dependency for the other 36 public
  MATH1 routines and eight constants.

## 2026-07-20 Native MATH1 Clamp Slice

- Added generated, independently link-selected `RT_F_CLAMP.OBJ` modules to the
  native and UDOS-format runtime trees. The 199-byte helper reads value, lower,
  and upper pointers through `$02-$05` and `$08/$09`, writes through `$06/$07`,
  and imports only comparison, minimum, and maximum.
- Matched portable MATH1 behavior: any NaN argument or `lower>upper` produces
  canonical quiet NaN; valid bounds compute
  `FMin(FMax(value,lower),upper)` while preserving selected operand bits and
  signed zero.
- Extended preallocation and body collection for the ternary call and placed
  its exact three-initializer assignment/print root in pass K. Keeping the
  171-byte emitter out of pass A preserves that overlay's enforced 768-byte
  reserve: pass A is 7,406 bytes with 786 free, while pass K is 4,208 bytes
  with 3,984 free.
- Added an exact three-input host oracle, focused compiler object assertions,
  a direct-link runtime case, and live VICE coverage. The broad direct-PRG
  matrix now contains 1,331 shapes, its compiled-runtime relocation oracle
  covers 290 cases, and the source-backed object-emission matrix remains at
  171 shapes.
- Native MATH1 now exposes eight low-level calls. General REAL expression,
  function, and frame lowering remained the dependency for the other 35 public
  MATH1 routines and eight constants at that checkpoint.

## 2026-07-20 Native MATH1 Clamp Storage Mapping

- Replaced pass K's fixed `A/B/C/X` body match with a bounded capture matcher
  for all three initializer destinations, three clamp arguments, the result
  destination, and the printed value. Every capture must be a declared one of
  the four REAL slots, and paired low/high body references must agree.
- Kept the emitted object at 171 machine bytes and retained ordinary imports
  for integer conversion, clamp, and print. Generic ALINK still chooses the
  comparison/minimum/maximum dependency closure and prunes unrelated helpers.
- Added exact pointer-patch assertions and a source-backed direct VICE launch
  that initializes slots 1/3/2, clamps slots 3/2/1 into slot 0, prints slot 0,
  and produces 5.0.
- At that checkpoint the inventories were 1,332 broad direct-PRG shapes, 171 non-runtime
  source-backed object-emission shapes, and 291 compiled-runtime
  relocation-oracle cases.
  Pass K is 4,359 bytes with 3,833 bytes free in its 8 KiB window.
- This removes declaration-order assumptions only. General REAL expression
  trees, arbitrary call placement, locals, returns, and portable MATH1 bodies
  remain the next compiler dependency.

## 2026-07-20 Native Finite REAL Function Storage Mapping

- Replaced pass K's fixed module and parameter slot signatures for the bounded
  finite comparison/select function with validated wildcard captures. The
  matcher still requires exactly three module REALs, two REAL parameters, two
  immediate conversions, one call, and `IF left<right THEN RETURN(left) FI
  RETURN(right)`.
- Relocation roles now independently follow both initializer destinations,
  call arguments, the result, reverse stack parameter binds, comparison
  operands, and return operands. The emitted root/function/data layout remains
  185 bytes and ALINK continues to perform only generic OBJ1 closure.
- Added a shared fixture that declares `RESULT/RIGHT/LEFT`, names parameters
  `B/A`, and verifies role-correct relocations. Its direct VICE PRG checks all
  five REAL cells and returns 1.0; Linux ACTC/ALINK in the Idun fork accepts and
  executes the same source through its existing general compiler.
- At that checkpoint the inventories were 1,333 broad direct-PRG shapes, 172 non-runtime
  source-backed object-emission shapes, and 291 compiled-runtime relocation-
  oracle cases. Pass K is 4,594 bytes with 3,598 bytes free in its 8 KiB window.
- This removes one more declaration-order assumption, not the bounded grammar.
  General native REAL expressions, locals, arbitrary calls/returns, recursive
  frames, and dependency-sized portable MATH1 modules remain next.

## 2026-07-20 Native Two-REAL-Parameter Return Mapping

- Separated pass A's bounded two-parameter return selector from its first caller
  argument and preserved the first parameter selector outside relocation
  scratch. The existing 157-byte root/function/data layout and reverse stack
  bind ABI are unchanged.
- The form can now return any captured named REAL storage rather than only its
  first parameter. A shared `RESULT/RIGHT/LEFT` fixture binds parameters `B/A`,
  returns second parameter `A`, and writes binary32 2.0.
- Native exact OBJ assertions and a direct UDOS/VICE launch verify both caller
  values, both callee copies, and the result. Idun's existing general Linux
  compiler/linker compiles and executes the same fixture without implementation
  changes.
- At that checkpoint inventories were 1,334 broad direct-PRG shapes, 173 non-runtime
  source-backed object-emission shapes, and 291 compiled-runtime relocation-
  oracle cases. Pass A is 7,418 bytes with 774 bytes free under its enforced
  768-byte reserve.
- This advances named return selection only. Arbitrary REAL expression returns,
  local REAL frames, nested/recursive calls, and dependency-sized portable
  MATH1 compilation remain next.

## 2026-07-20 Native MATH1 Include Constants

- Replaced the non-includable `MODULE MATH1` binding reference with a native
  include header that defines all eight portable IEEE-754 constants and
  documented the eight compiler-recognized calls available at that checkpoint.
- `INCLUDE "MATH1"` now works before or after the application `MODULE` line.
  The focused compiler check folds `MATH_PI` to literal words 4059/16457,
  allocates only the caller's `RESULT` cell, and emits no OBJ import.
- Export and UDOS release tests verify the include-safe header and constants.
  A shared source fixture also compiles and links through Idun's Linux tools.
- The complete native suite passes 799 tests, including 210 overlay tests; the
  Idun active host suite passes 152 tests and its ASan/UBSan suite passes 137
  tests with the new shared fixture.
- The cross-product review exposed a separate Idun packaging gap: including
  its complete MATH1 source currently places every function body in the root
  object. Reachable-only Idun pruning and the remaining 35 native routines at
  that checkpoint became explicit work item 2 in the parity matrix.

## 2026-07-20 Native MATH1 Truncation

- Added dependency-free `RT_F_TRUNC.OBJ`, a 107-byte binary32 helper that
  truncates toward zero by clearing fractional significand bits. Signed zero,
  infinities, NaN payloads, and already integral values are preserved exactly.
- Native ACTC recognizes `FTrunc(A)` for named REAL values in assignment, print,
  and condition positions through the existing pass-A unary emitter. ALINK
  selects only truncation plus the conversion/printing helpers actually used by
  the root program.
- Refactored pass 6's duplicated unary keyword consumers into one parameterized
  matcher. Pass 6 is 8,071 bytes and retains 121 bytes under its enforced
  96-byte growth reserve; pass A remains 7,418 bytes.
- Exact host execution covers exponent boundaries, exceptional values, signed
  zero, subnormals, and random bit patterns. The focused direct-PRG case raised
  inventories at that checkpoint to 1,335 broad shapes and 292 compiled-runtime relocation
  oracles; the non-runtime source-backed inventory remains 173.
- Native MATH1 now exposes nine link-selected calls and all eight constants. The
  remaining native library gap is 34 public routines, plus the general REAL
  expression/call/frame support needed by their portable bodies.

## 2026-07-20 Native MATH1 Floor

- Added `RT_F_FLOOR.OBJ`, a 135-byte binary32 helper that imports only
  `RT_F_TRUNC.OBJ`. It supports aliased source/destination pointers, preserves
  NaN payloads, infinities, signed zero, and integral values, and rounds finite
  nonintegers toward negative infinity.
- Native ACTC recognizes `FFloor(A)` in assignment, direct-print, and
  REAL-condition positions. A compact intrinsic-name table keeps pass 6 at
  8,082 bytes with 110 bytes free under its enforced 96-byte reserve.
- The focused VICE case proves direct `floor -> trunc` ALINK dependency closure,
  output `-7`, and pruning of staged sibling helpers. The broad matrix is now
  1,336 shapes and the independent compiled-runtime oracle covers 293 cases.
- Idun ACTC parses, constant-folds, and emits the same shared helper. Its MATH1
  source now declares `FFloor` without a body, and 116 full-domain VICE vectors
  cover both truncation and floor results.
- At that checkpoint native MATH1 exposed ten link-selected calls plus all
  eight constants, leaving a 33-routine native library gap.
- Native ACTC now recognizes `FCeil(A)` in assignment, direct-print, and
  REAL-condition positions. The 42-byte helper imports floor and transitively
  truncation, implements `-FFloor(-A)`, supports aliased pointers, and preserves
  NaN payloads, infinities, signed zero, and integral values.
- Linux ACTC parses and constant-folds the same intrinsic, emits `RT_F_CEIL`
  for dynamic expressions, and no longer compiles the portable MATH1 ceiling
  body. Exact host checks, 116 Idun VICE vectors, and a focused native direct
  PRG prove complete semantics and `ceil -> floor -> trunc` closure.
- At that checkpoint inventories were 1,337 broad and 294 compiled-runtime
  cases. Pass 6 was 8,062 bytes with 130 bytes free after compacting unary
  dispatch. Native MATH1 exposed eleven link-selected calls and lacked 32
  public routines.

## 2026-07-20 Native MATH1 Round

- Added `RT_F_ROUND.OBJ`, a 152-byte binary32 helper that imports only
  `RT_F_TRUNC.OBJ`. It rounds nearest with halfway cases away from zero,
  preserves NaN payloads, infinities, signed zero, and integral values, and is
  safe for aliased source/destination pointers.
- The helper inspects binary32 exponent/fraction bits rather than adding or
  subtracting 0.5, so large integral values such as 8,388,609 are not changed.
- Native ACTC recognizes `FRound(A)` in assignment, direct-print, and
  REAL-condition positions. Idun ACTC constant-folds constant calls and selects
  the same shared OBJ for dynamic calls.
- Exact host verification, 116-vector Idun VICE execution, and the focused
  native direct-PRG case prove ties-away behavior, `round -> trunc` closure,
  and pruning of staged sibling helpers.
- At that checkpoint inventories were 1,338 broad and 295 compiled-runtime
  cases. Pass 6 was 8,074 bytes with 118 bytes free under its 96-byte reserve.
  Native MATH1 exposed twelve link-selected calls and lacked 31 public routines.

## 2026-07-20 Native MATH1 Fractional Part

- Added `RT_F_FRAC.OBJ`, a 93-byte binary32 helper that imports
  `RT_F_TRUNC.OBJ` and `RT_F_SUB.OBJ` and computes `value-FTrunc(value)`.
  Its private operand/temporary storage makes aliased source and destination
  pointers safe.
- Native ACTC recognizes `FFrac(A)` in assignment, direct-print, and
  REAL-condition positions. Idun ACTC constant-folds constant calls and
  selects the same shared OBJ only for dynamic calls.
- Exact host verification, 116-vector Idun VICE execution, and the focused
  native direct-PRG case prove signed finite fractions, integral cancellation,
  exceptional-value policy, full dependency closure, and sibling pruning.
- At that checkpoint inventories were 1,339 broad and 296 compiled-runtime
  cases. Pass 6 was 8,085 bytes with 107 bytes free under its 96-byte reserve.
  Native MATH1 exposed thirteen link-selected calls and lacked 30 public
  routines.

## 2026-07-20 Native MATH1 Remainder

- Added `RT_F_MOD.OBJ`, a 245-byte alias-safe binary32 helper that imports
  division, truncation, multiplication, and subtraction and computes
  `value-FTrunc(value/divisor)*divisor`.
- Zero divisors, NaN operands, and infinite dividends return canonical quiet
  NaN. A finite dividend with either infinity as divisor is returned exactly.
- Native ACTC recognizes `FMod(A,B)` in assignment, direct-print, and
  REAL-condition positions. Idun ACTC constant-folds constant calls and emits
  the same shared OBJ only for dynamic calls.
- Exact host verification covers 332 vectors in each of the ordinary,
  left-alias, and right-alias modes. The
  116-pair Idun VICE fixture and focused native direct PRG prove full semantics,
  dependency closure, and sibling pruning.
- At that checkpoint inventories were 1,340 broad and 297 compiled-runtime cases. Pass 6
  was 8,094 bytes with 98 bytes free under its 96-byte reserve. Native MATH1 then
  exposed fourteen link-selected calls and lacked 29 public routines.

## 2026-07-20 Shared MATH1 Hypotenuse

- Added the 503-byte alias-safe `RT_F_HYPOT.OBJ`, which computes a scaled
  hypotenuse through seven independently selected direct dependencies and a
  3,617-byte linked closure.
- Native and Linux ACTC recognize `FHypot(A,B)`; Linux constant-folds constant
  calls, and both compilers import the helper only for reachable dynamic calls.
- Exact host verification covers 2,316 vectors in ordinary, left-alias, and
  right-alias modes. The 116-pair Idun VICE fixture, focused native launch, and
  complete native MATH1 matrix pass.
- Fixed ALINK import discovery for paged objects by stabilizing body-selector
  records before recursive module lookups. An 11-import object regression now
  crosses the source-window boundary.
- At that checkpoint inventories were 1,341 broad and 298 compiled-runtime cases. Pass 6
  is 8,093 bytes with 99 bytes free under its 96-byte reserve. Native MATH1 now
  exposes fifteen link-selected calls and lacks 28 public routines.

## 2026-07-21 Native Binary REAL Function Return

- Generalized body collection and preallocation so a REAL `RETURN(...)` uses
  the same bounded value parser as assignments and conditions without growing
  capacity-constrained pass 6.
- Pass K now emits a two-REAL-parameter function returning one selected binary
  arithmetic, min/max, remainder, or hypotenuse result through a hidden
  non-aliasing four-byte cell.
- Added a shared `RETURN(FHypot(A,B))` fixture plus exact OBJ, ALINK closure,
  sibling-pruning, Linux ACTC/ALINK, and live native VICE checks. Both products
  produce binary32 5.0 from the same portable source.
- At that checkpoint inventories were 1,342 broad direct-PRG and 174
  non-runtime source-backed shapes; the compiled-runtime oracle remained 298. Pass K is
  5,877 bytes with 2,315 bytes free. General REAL trees, locals, nested calls,
  and the remaining 28 MATH1 routines are still pending.

## 2026-07-21 Native Nested REAL Postfix Emission

- Added base-36 pass L, `ACTC_OVLL.BIN`, to lower the bounded child-first REAL
  stream produced by passes 6 and 7 into ordinary executable OBJ1 machine
  records. ALINK performs only normal reachability, placement, and relocation.
- The pass supports one `MAIN`, module REAL storage, integer conversion,
  assignment, `PrintR`/`PrintRE`, the maintained unary and binary REAL helpers,
  and ternary `FClamp`. It requires a genuinely nested helper result so the
  older specialized emitters retain their established simple forms.
- Internal variable and temporary exports use 16-bit offsets. An overlapping
  `__idata` export anchors source-variable records in DBG1 without exposing
  compiler temporaries as Action variables.
- Exact compiler tests and direct ALINK/VICE probes cover
  `FMin(FMax(A,B),C)` and `FClamp(FAbs(A),FMin(B,C),FMax(A,C))`; both print `2`
  and select only their reachable runtime closure. The clamp case places
  temporary exports at offsets 256, 260, and 264.
- Current inventories are 1,344 broad direct-PRG and 176 non-runtime
  source-backed shapes; the compiled-runtime oracle remains 298. Pass L is
  4,195 bytes with 3,997 bytes free. General REAL functions, locals, control
  flow, mixed-type expressions, arbitrary calls, and recursive frames remain
  pending.

## 2026-07-21 Native Nested REAL Function Call

- Extended pass L across one bounded procedure boundary: `MAIN` can call one
  nonrecursive function with exactly two REAL parameters, no locals, and one
  nested straight-line REAL return expression.
- The caller pushes low/high argument pointers, the callee preserves the JSR
  return address while reverse-binding both parameters into static four-byte
  cells, and the function returns a result pointer in A/X. ALINK sees only
  ordinary exports and relocations and remains solely responsible for closure
  and placement.
- Added the shared `real_function_nested_postfix.act` fixture. Linux ACTC/ALINK
  compiles it, while native ACTC emits the exact OBJ1 call ABI and the linked
  native PRG prints `5` in VICE after evaluating
  `FHypot(FAbs(A),FAbs(B))`.
- At that checkpoint inventories were 1,345 broad direct-PRG and 177 non-runtime
  source-backed shapes; the compiled-runtime oracle remains 298. Pass L is
  5,443 bytes with 2,749 bytes free. General call graphs, REAL locals, control
  flow, mixed types, arbitrary signatures, and recursive frames remain pending.

## 2026-07-21 Native REAL Function Local Storage

- Extended pass L's existing nonrecursive two-REAL-parameter function path to
  accept bounded all-REAL local declarations. Locals use the same ordinary
  four-byte OBJ1 data exports as module variables and parameters; DBG1 records
  retain procedure-local scope.
- Added the shared `real_function_local_nested_postfix.act` fixture. Its
  function stores `FAbs(A)` in local `ABSLEFT`, then returns
  `FHypot(ABSLEFT,FAbs(B))` through the existing A/X result-pointer ABI.
- Linux ACTC/ALINK compiles and links the same fixture. Native ACTC emits exact
  local load/store relocations, and the direct native PRG prints `5`, stores
  binary32 5.0 in `RESULT`, and stores binary32 3.0 in `ABSLEFT` under VICE.
  ALINK retains the existing reachable `FAbs`/`FHypot` closure and prunes
  staged siblings.
- Current inventories are 1,346 broad direct-PRG and 178 non-runtime
  source-backed shapes; the compiled-runtime oracle remains 298. Pass L is
  5,455 bytes with 2,737 bytes free. General call graphs, reentrant local
  frames, control flow, mixed types, arbitrary signatures, and recursive
  frames remain pending.

## 2026-07-21 Idun Source Call-Graph Pruning

- The Linux fork now retains every project routine and prunes source-defined
  MATH1/GFX1 library routines to the transitive graph referenced by project
  code, while shared intrinsic helpers remain independent OBJ modules selected
  by ALINK.
- Bare routine addresses, `OverlayCall` targets, globals, and declaration-time
  address expressions preserve their referenced routines. Focused real-library
  and synthetic chain tests prove reachable bodies remain and unused siblings
  are absent.
- Idun's active host suite now contains 153 tests and its sanitizer suite
  contains 138 hardware-free tests. This is a compiler-packaging change only;
  the portable source contract, OBJ1 semantics, ALINK closure, and direct-PRG
  runtime model are unchanged.

## 2026-07-21 Native Two-Function REAL Module

- Generalized pass L from one bounded REAL callee to up to two independent
  nonrecursive two-REAL-parameter functions called directly by `MAIN`. Each
  function receives disjoint static parameter/local storage and its own DBG1
  procedure bank; function-to-function calls and recursion remain rejected.
- Added the shared `real_two_function_nested_postfix.act` fixture. Native ACTC
  emits `length` and `shorter` exports plus both selector relocations, and ALINK
  continues to perform ordinary closure, placement, and relocation only.
- The rebuilt native direct PRG prints `5` and `3`; VICE verifies binary32 5.0
  and 3.0 in both result cells plus 3.0 and 4.0 in the two function locals.
  Idun ACTC now lowers direct `FMin`/`FMax` expressions to `RT_F_MIN` and
  `RT_F_MAX`, folds constants with the same NaN/signed-zero operand selection,
  and executes the same fixture with identical result cells.
- Current inventories are 1,347 broad direct-PRG and 179 non-runtime
  source-backed shapes; the compiled-runtime oracle remains 298. Pass L is
  5,636 bytes with 2,556 bytes free. Function-to-function calls, reentrant
  local frames, control flow, mixed types, arbitrary signatures, and recursive
  frames remain pending.

## 2026-07-21 Native Declaration-Order REAL Call Chain

- Extended pass L's two-function ABI with one safe function-to-function edge.
  `MAIN` may call either function, and the later function may assign the earlier
  function's A/X result pointer into a bounded REAL local before continuing its
  return tree.
- Static parameter/local storage remains nonreentrant. Pass L therefore accepts
  only strictly earlier function selectors and now hard-fails forward, self, or
  cyclic edges instead of allowing the generic emitter to claim them.
- Added `real_function_call_chain_postfix.act` to both parity trees. Native ACTC
  emits ordinary `MAIN -> CHAIN` and `CHAIN -> LENGTH` OBJ1 relocations; ALINK
  needs no function-specific behavior. The direct PRG prints `5`, and VICE
  verifies binary32 5.0 in both `RESULT` and `CHAIN.BASE`.
- Idun ACTC/ALINK compiles, links, and executes the same fixture. Current native
  inventories are 1,348 broad direct-PRG and 180 non-runtime source-backed
  shapes; the compiled-runtime oracle remains 298. Pass L is 5,667 bytes with
  2,525 bytes free. Reentrant frames, control flow, nested call expressions,
  mixed types, arbitrary signatures, and recursion remain pending.

## 2026-07-21 Native Nested Local REAL Call Expression

- Extended the resident REAL value parser to recognize a declared local
  REAL-returning function after a variable lookup misses. It validates the
  function metadata, emits the existing argument body operations, and appends
  the existing `C` selector, so pass L and ALINK need no new opcode or ABI.
- Extended pass 7's recursive dependency scan to traverse a bounded
  two-REAL-parameter local call as an expression operand. The scan follows both
  arguments for helper dependencies without preallocating the local function or
  misclassifying the enclosing intrinsic as an unresolved import.
- Added the shared `real_function_nested_local_call_postfix.act` fixture. Its
  later function returns `FMax(LENGTH(A,B),FAbs(A))`; native ACTC emits ordinary
  `MAIN -> CHAIN` and `CHAIN -> LENGTH` relocations, and ALINK selects only
  `FAbs`, `FHypot`, `FMax`, conversion, and printing. The direct PRG prints `5`
  and VICE verifies binary32 5.0 in both `RESULT` and the nested-call temporary.
- Idun ACTC/ALINK compiles, links, and executes the byte-identical fixture.
  Current native inventories are 1,349 broad direct-PRG and 181 non-runtime
  source-backed shapes; the compiled-runtime oracle remains 298. Pass L remains
  5,667 bytes with 2,525 bytes free, while pass 7 is 6,678 bytes with 1,514 bytes
  free. Reentrant frames, control flow, user calls as arguments to other user
  calls, unrestricted nested calls, mixed types, arbitrary signatures, and
  recursion remain pending.

## 2026-07-21 Native Nested REAL User-Call Arguments

- Extended pass L ownership detection to recognize a local-call temporary used
  by another local call. Existing resident argument parsing and pass-7 recursive
  preallocation already preserve outer call state and traverse both arguments;
  pass L now claims the body and copies every returned A/X pointer into a distinct
  private four-byte temporary before evaluating the next call.
- Added the shared `real_function_user_call_arguments_postfix.act` fixture. Its
  later `CHAIN` function returns `LOWER(LOWER(A,A),LOWER(B,B))`, exercising three
  calls to the earlier `LOWER` function without aliasing its static parameter or
  result cells. Native ACTC emits ordinary OBJ1 relocations, ALINK selects only
  `FMin`, conversion, and printing, and the direct PRG prints binary32 `3`.
- VICE verifies 3.0 and 4.0 in the two inner spills and 3.0 in the outer spill and
  module result. Idun ACTC/ALINK compiles, links, and executes the byte-identical
  fixture with the same result.
- Current native inventories are 1,350 broad direct-PRG and 182 non-runtime
  source-backed shapes; the native unittest inventory is 819 and the
  compiled-runtime oracle remains 298. Pass L is 5,670 bytes with 2,522 bytes
  free, while pass 7 remains 6,678 bytes with 1,514 bytes free. Reentrant frames,
  control flow, unrestricted user-call argument trees and nested calls, mixed
  types, arbitrary signatures, and recursion remain pending.

## 2026-07-21 Native Frame-Preserved Forward REAL Calls

- Pass L now accepts acyclic function-to-function calls in either declaration
  direction. Before each such call it saves the caller's static REAL parameters,
  locals, and live temporaries on the 6502 stack; after staging the A/X-returned
  four-byte value in `$0C-$0F`, it restores those cells in reverse and copies
  the result to an independent temporary.
- Added byte-identical `real_function_forward_frame_postfix.act` fixtures. Its
  `FIRST -> SECOND` forward edge keeps `FAbs(A)` live across the call. Native
  ACTC emits ordinary OBJ1 export/storage relocations, ALINK performs generic
  closure and placement, and the rebuilt direct PRG produces binary32 3.0 in
  VICE while selecting only `FAbs`, `FMax`, `FMin`, conversion, and printing.
  Idun ACTC/ALINK executes the same source with the same result.
- Self and mutual cycles remain hard errors. Pass L still has no function
  control flow or recursive/reentrant frame allocation, so bounded terminating
  recursion is the next call-ABI dependency rather than a claim of completion.
- Current native inventories are 1,351 broad direct-PRG and 183 non-runtime
  source-backed shapes; the native unittest inventory is 821 and the
  compiled-runtime oracle remains 298. Native pass L is 6,124 bytes with 2,068
  bytes free, while native pass 7 remains 6,678 bytes with 1,514 bytes free.

## 2026-07-21 Bounded REAL Function IF/ELSE

- Added pass M, `ACTC_OVLM.BIN`, as the control-capable build of the shared
  postfix REAL emitter. Pass L remains byte-for-byte 6,124 bytes and keeps its
  2,068-byte reserve; pass M is 6,998 bytes with 1,194 bytes free under a
  dedicated 1 KiB capacity gate.
- Pass M claims only a supported REAL function containing one nonnested
  `IF`/`ELSE`. It maps all six relations through `rt_f_cmp`, emits a branch-over
  plus absolute `JMP`, and relocates those jumps to ordinary internal `__rfN`
  false and `__reN` end code exports. This avoids relative-branch span limits
  and requires no ALINK source-shape handling.
- Added byte-identical `real_function_if_else_postfix.act` fixtures. `PICK(3,4)`
  takes the then arm and `PICK(4,3)` takes the `FMax` else arm; native ACTC and
  ALINK produce a direct PRG that prints `34`, and Idun ACTC/ALINK executes the
  same source with identical results.
- Current native inventories are 1,352 broad direct-PRG and 184 non-runtime
  source-backed shapes; the native unittest inventory is 825 and the
  compiled-runtime oracle remains 298. Sequential/nested function controls,
  loops, early returns, recursive/reentrant frames, mixed types, arbitrary
  signatures, and recursion remain pending.

## 2026-07-22 Bounded Sequential/Nested REAL Function Control

- Added pass N, `ACTC_OVLN.BIN`, as a separate two-control build of the shared
  postfix REAL emitter. Pass N claims a supported program only when at least one
  REAL function contains a second conditional. Each function may contain at
  most two conditionals, either sequentially or nested to depth two.
- Each control receives independent `__rfNN` and `__reNN` code exports. The
  nested fixture intentionally produces non-monotonic export offsets, proving
  that ALINK resolves generic OBJ1 exports and relocations rather than assuming
  source or label order.
- Added byte-identical `real_function_sequential_if_else_postfix.act` and
  `real_function_nested_if_else_postfix.act` fixtures to native and Idun test
  trees. Their direct PRGs print `43` and `143`; the nested case covers inner
  true, inner false, and outer false paths.
- Passes L and M remain byte-identical at 6,124 and 6,998 bytes. Pass N is 7,120
  bytes with 1,072 bytes free under its dedicated 1 KiB capacity gate.
- Current native inventories are 1,354 broad direct-PRG and 186 non-runtime
  source-backed shapes; the native unittest inventory is 830, the overlay suite
  is 228 tests, the source-cache suite is 198 tests, and the compiled-runtime
  oracle remains 298. Loops, early returns, more than two controls, deeper
  nesting, recursive/reentrant frames, mixed types, arbitrary signatures, and
  recursion remain pending.

## 2026-07-22 Bounded Four-Control REAL Function Control

- Added pass O, `ACTC_OVLO.BIN` (id 24), as the four-control build of the
  shared postfix REAL emitter. It claims a supported program when at least one
  REAL function contains a third conditional and permits at most four controls
  per function, either sequentially or nested to depth four.
- Each slot retains an independent `__rfNN` false export and optional `__reNN`
  end export. Power-of-two slot arithmetic keeps nested label resolution
  independent of source order while ALINK continues to process ordinary OBJ1
  exports and relocations only.
- Added byte-identical `real_function_four_sequential_if_postfix.act` and
  `real_function_four_deep_if_postfix.act` fixtures. Rebuilt release artifacts
  launch directly in VICE and print `43` and `154`; exact memory checks cover
  all sequential results plus depth-four deep-true, deep-false, and outer-false
  paths. Idun ACTC/ALINK executes the same sources with identical results.
- Passes L, M, and N remain byte-identical. Pass O is 7,123 bytes with 1,069
  bytes free under its 1 KiB gate and has SHA-256
  `dd71aaa1d07600ce5e8004376879746ee046a56c33a49d5db727563feade0211`.
- Current native inventories are 1,356 broad direct-PRG and 188 non-runtime
  source-backed shapes; the native unittest inventory is 835, the overlay suite
  is 231 tests, the source-cache suite is 198 tests, and the compiled-runtime
  oracle remains 298. Tracked build scripts are executable so fresh GitHub
  clones can run Makefile entrypoints without local mode repairs.
- Loops, early returns, controls beyond four or depth four,
  recursive/reentrant frames, mixed types, arbitrary signatures, and recursion
  remain pending.

## 2026-07-22 Bounded REAL Function Early Returns

- Added pass P, `ACTC_OVLP.BIN` (id 25), as the early-return build of the
  shared postfix REAL emitter. It accepts immediate `RETURN(expr)` exits inside
  the existing four-control/depth-four bound and requires a terminal fallback
  return so programs outside that contract remain available to later passes.
- Added byte-identical `real_function_early_return_if_postfix.act` and
  `real_function_early_return_four_deep_postfix.act` fixtures. Rebuilt release
  artifacts launch directly in VICE and print `33` and `154`; exact memory
  checks cover the immediate true/else exits and terminal fallback path. Idun
  ACTC/ALINK executes both sources with identical results.
- Passes L through O remain byte-identical. Pass P is 7,147 bytes with 1,045
  bytes free under its 1 KiB gate and has SHA-256
  `7b32fc5bd2e84120572ae25e097ec6004297e3d502922d32d5384e17ad29394e`.
- Current native inventories are 1,358 broad direct-PRG and 190 non-runtime
  source-backed shapes; the native unittest inventory is 840, the overlay suite
  is 234 tests, the source-cache suite is 198 tests, and the compiled-runtime
  oracle remains 298.
- Loops, controls beyond four or depth four, unrestricted call-expression
  trees, recursive/reentrant frames, mixed types, arbitrary signatures, and
  recursion remain pending.

## 2026-07-22 Bounded REAL Function Loops

- Added pass Q, `ACTC_OVLQ.BIN` (id 26), for up to four bounded
  `DO ... UNTIL ... OD` and `WHILE ... DO ... OD` loops per supported REAL
  function. Back edges and pre-test exits use ordinary relocatable `__rbNN` and
  `__rzNN` OBJ1 code exports; ALINK remains source-shape agnostic.
- Added the byte-identical `real_function_loops_postfix.act` fixture. Rebuilt
  native ACTC/ALINK artifacts launch directly in VICE and produce FIRST=4.0 and
  SECOND=3.0, displayed as `43`. Idun ACTC/ALINK's generated-6502 execution path
  produces the same values.
- Passes L through P remain byte-identical. Pass Q is 7,151 bytes with 1,041
  bytes free under its 1 KiB gate and has SHA-256
  `40273408c14c54a618e92d60d5fae12370820a8ea9a60cddc3c508fb4ac67507`.
- Current native inventories are 1,359 broad direct-PRG and 191 non-runtime
  source-backed shapes; the native unittest inventory is 844, the overlay suite
  is 237 tests, the source-cache suite is 198 tests, and the compiled-runtime
  oracle remains 298.
- Plain infinite `DO`, loop `EXIT`, mixed loop/conditional nesting, returns
  from inside loops, controls beyond four or depth four, unrestricted call
  trees, recursive/reentrant frames, mixed types, arbitrary signatures, and
  recursion remain pending.

## 2026-07-22 Bounded REAL Function Plain Loops And EXIT

- Added pass R, `ACTC_OVLR.BIN` (id 27), for plain `DO ... OD` and
  unconditional `EXIT` within the existing four-loop REAL-function bound. The
  collector's base-36 loop-kind selector is decoded without changing the body
  or OBJ1 formats; `EXIT` targets the nearest active `DO` or `WHILE` through
  that loop's ordinary relocatable `__rzNN` export, while `OD` retains the
  independent `__rbNN` back edge.
- Added byte-identical `real_function_loop_exit_postfix.act` fixtures. Native
  ACTC/ALINK launches the linked PRG directly in VICE, exits one plain and one
  guarded loop, stores FIRST=4.0 and SECOND=3.0, and displays `43`. Idun's
  Linux ACTC/ALINK generated-6502 path executes the same source with identical
  values. A compiler regression also proves that nested `EXIT` binds to the
  nearest active plain loop.
- Pass Q remains exactly 7,151 bytes with SHA-256
  `40273408c14c54a618e92d60d5fae12370820a8ea9a60cddc3c508fb4ac67507`;
  passes L through Q remain byte-identical. Pass R is 7,334 bytes with 858
  bytes free under its dedicated 768-byte gate and has SHA-256
  `1ef9ff4c164ee353025da5e3f4d02dceadfadd0a833ea244e7c798f88f72db15`.
- Current native inventories are 1,360 broad direct-PRG and 192 non-runtime
  source-backed shapes; the native unittest inventory is 848, the overlay suite
  is 240 tests, the source-cache suite is 198 tests, and the compiled-runtime
  oracle remains 298.
- REAL-function `FOR`, mixed loop/conditional nesting, returns from inside
  loops, controls beyond four or depth four, unrestricted call trees,
  recursive/reentrant frames, mixed types, arbitrary signatures, and recursion
  remain pending.

## 2026-07-22 Bounded REAL Function FOR Loops

- Added pass S, `ACTC_OVLS.BIN` (id 28), for up to four nested or sequential
  local CARD-counter `FOR` loops per supported REAL function. Initial and final
  values are constants; the optional signed constant step defaults to `1` and
  must be nonzero. Inclusive unsigned comparisons and carry-based
  overflow/underflow exits prevent counter wraparound from restarting a loop.
- Added byte-identical `real_function_for_postfix.act` fixtures. The ascending
  `FOR I=1 TO 3` function produces 4.0; the descending
  `FOR J=5 TO 1 STEP -2` function produces 7.0. Native ACTC/ALINK emits and
  launches the direct PRG in VICE, displays `47`, and selects only the five
  reachable REAL add/conversion/print modules. Idun ACTC/ALINK's generated-6502
  path compiles, links, and executes the same source with identical result
  cells.
- Pass Q remains byte-identical at SHA-256
  `40273408c14c54a618e92d60d5fae12370820a8ea9a60cddc3c508fb4ac67507`;
  pass R remains byte-identical at SHA-256
  `1ef9ff4c164ee353025da5e3f4d02dceadfadd0a833ea244e7c798f88f72db15`.
  Pass S is 7,828 bytes with 364 bytes free under its dedicated 256-byte gate
  and has SHA-256
  `0291077c9a1895313eb5fe1ad5b9914b3b4c8ebe64cd9c75634863d96e639128`.
- Current native inventories are 1,361 broad direct-PRG and 193 non-runtime
  source-backed shapes; the native unittest inventory is 851, the overlay suite
  is 242 tests, the source-cache suite is 198 tests, and the compiled-runtime
  oracle remains 298.
- Dynamic `FOR` bounds, nested counter-to-REAL body composition, mixed
  loop/conditional nesting, returns inside loops, controls beyond four or depth
  four, unrestricted call trees, recursive/reentrant frames, mixed types,
  arbitrary signatures, and recursion remain pending.

## 2026-07-22 Named CARD Bounds In REAL Function FOR Loops

- Added pass T, `ACTC_OVLT.BIN` (id 29), for named CARD initial/final bounds
  in the bounded pass-S `FOR` form. Named initial values are copied into the
  counter at entry; named final values are staged before the recorded back edge,
  preserving once-only bound evaluation. Steps remain nonzero signed constants.
- Added byte-identical `real_function_dynamic_for_postfix.act` fixtures. One
  function nests `FOR J=I TO 3`; the other nests `FOR L=1 TO K`. Native
  ACTC/ALINK and Idun's generated-6502 path both store 7.0 twice; native VICE
  displays `77` and ALINK selects only the five reachable add/conversion/print
  modules.
- Fixed loop-label bookkeeping exposed by the final-bound case so second-slot
  `__rb11`/`__rz11` exports accompany every emitted relocation.
- Pass S remains byte-identical at SHA-256
  `0291077c9a1895313eb5fe1ad5b9914b3b4c8ebe64cd9c75634863d96e639128`.
  Pass T is 8,147 bytes with 45 bytes free under its dedicated 32-byte gate and
  has SHA-256
  `e07b16dab80f22685e86c0b50c1018862ed5721eca1c07d66151ead5727fe3d3`.
- Current native inventories are 1,362 broad direct-PRG and 194 non-runtime
  source-backed shapes; the native unittest inventory is 854, the overlay suite
  is 244 tests, the source-cache suite is 198 tests, and the compiled-runtime
  oracle remains 298.
- General `FOR` bound expressions, runtime steps, nested counter-to-REAL body
  composition, mixed loop/conditional nesting, returns inside loops, controls
  beyond four or depth four, unrestricted call trees, recursive/reentrant
  frames, mixed types, arbitrary signatures, and recursion remain pending.
