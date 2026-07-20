# ALINK Status

Current state:

- `ALINK.PRG` builds as a UDOS-native tool.
- The default live output is `BIN/<MODULE>.PRG`.
- `ALINK MAIN` is verified by `make -C ../udos vice-action-alink`.
- The higher-level `ACTC.PRG -> ALINK.PRG -> BIN/MAIN.PRG` launch path is
  verified by `make -C ../udos vice-action-actc-alink-launch`.
- Broad direct-PRG object/link coverage is verified by
  `make -C ../udos vice-action-alink-prg-matrix`.
- The broad direct-PRG matrix currently enumerates 1333 probe shapes from
  `udos/tools/run_action_alink_prg_probe.py`.
- The source-backed `actc_fixed_register_machine_abi_linked` case proves that
  ALINK treats native `=*(...)` routines as ordinary machine exports and JSR
  relocations. The linked PRG verifies BYTE/CARD returns and mixed-width
  A/X/Y/`$A3` argument placement without a linker-specific ABI path.
- The source-backed `actc_raw_code_block_fixed_abi_linked` case proves the same
  direct ABI with unchecked raw bytes, compact constants, character/signed/sum
  values, local-routine/current-address relocations, and linked storage
  operands. ALINK still sees only ordinary machine and relocation records.
- The source-backed `actc_asmblock_symbols_labels_linked` case proves ALINK
  accepts ACTC-emitted inline machine bytes, module/parameter/local variable
  relocations, and block-local jump targets without any assembler-specific
  linker path.
- The source-backed `actc_asmblock_symbol_byte_relocations_linked` case proves
  `l`/`h` OBJ relocations construct linked pointers to globals, parameters,
  locals, and block labels and execute those indirect accesses in VICE.
- The source-backed `actc_asmblock_real_storage_linked` case proves four-byte
  global/local exports, indexed relocation targets, and direct PRG execution;
  ALINK still performs only generic OBJ closure, placement, and relocation.
- The source-backed `actc_real_function_nonfixed_storage_linked` case proves
  dynamic REAL export/data placement and relocations from the second module
  REAL slot to the third; ALINK selects only the referenced conversion object
  and executes the resulting direct PRG without a function-specific linker path.
- The source-backed `actc_real_function_mixed_width_storage_linked` case proves
  those offsets remain correct when a two-byte CARD precedes the returned and
  destination REAL storage. ALINK receives ordinary width-aware OBJ exports and
  requires no mixed-layout or REAL-function special case.
- The source-backed `actc_real_function_word_param_linked` case proves a CARD
  argument is stack-bound, converted into REAL storage, returned by pointer, and
  copied by the caller. `RT_I_TO_F.OBJ` is selected through ordinary import
  closure; ALINK has no parameterized-function special case.
- The source-backed `actc_real_function_finite_min_linked` case proves a
  two-REAL-parameter function can compare and select finite values using only
  ordinary OBJ1 exports, body import closure, and relocations. The root selects
  `RT_I_TO_F.OBJ`, `RT_F_CMP.OBJ`, and comparison's transitive
  `RT_F_SPECIAL.OBJ`; unrelated REAL arithmetic and print modules remain
  absent, and the resulting direct PRG executes in VICE without a REAL-specific
  linker path.
- The adjacent `actc_real_function_finite_min_permuted_linked` case reorders all
  three module REAL declarations and the two parameter names. Its ordinary
  relocations bind the same 185-byte object to the captured storage exports,
  and live VICE checks all five binary32 slots while ALINK remains unchanged.
- Direct object-code launch and rejection coverage is verified by
  `make -C ../udos vice-action-alink-prg-object-code-matrices`.
- The linker-owned direct PRG include is `src/tools_udos/alink/direct_prg.inc`.
- Object/export metadata, closure queues, machine-code bodies, and direct-PRG
  relocation records are REU-backed behind bounded resident windows. Production
  builds allow 36 exports per loaded OBJ and a 64-entry reachable external
  closure with placement metadata; body records use REU bank `$04`, separate
  from the other linker tables in bank `$03`.
- Generated chain probes exercise all 64 reachable external entries and reject
  a 65th dependency before loading it or creating an output PRG.
- Five-byte relocation records have an independent 128-record capacity in the
  existing `$300`-byte REU region and do not compete with the 64-entry reachable
  external closure. The exact binary32 formatter exercises 73 records in one
  ordinary OBJ module.
- ALINK contains no runtime-helper recognizer, abstract-body compiler, or
  fixed-address PRG synthesizer. Every accepted body is an OBJ1 `M` machine
  record, and unsupported compact bodies fail with `UNSUPPORTED BODY`.
- The production `ALINK.PRG` is 13,806 bytes. Runtime helpers are ordinary
  transitive `RT_*.OBJ` dependencies selected only by reachable imports and
  relocations.
- REAL arithmetic, comparison, and square-root objects import the shared
  dependency-only `RT_F_SPECIAL.OBJ`. ALINK includes it only when one of those
  helpers is reachable; live full-range probes cover signed infinity, canonical
  quiet NaN, unordered comparison, and non-finite printing without a
  REAL-specific linker path.
- ALINK code is constrained below UDOS's preserved tool ABI at `$9800`; its
  mutable BSS workspace occupies tool-owned RAM at `$A000-$BFFF` so linker
  growth cannot overwrite live file services.
- Direct-PRG runtime helper coverage includes link-selected math, graphics,
  SID/sprite, input, and DBF helper families.
- ACTC emits dynamic integer products as ordinary native OBJ1 machine records,
  nested local data exports, and named/import relocations. ALINK handles those
  modules through its generic object-code path; the dedicated integer-sequence
  build strategy and its linker-side compiler have been removed. This recovers
  1,536 bytes of ALINK code while preserving helper dead strip and rejection of
  unsupported legacy bodies.
- Plain word store and load/store programs now reach the generic object-code
  linker path. The two matching linker-side body templates have been removed,
  and seeded compact versions are retained only as rejection probes.
- Empty return, single local-call, and local fanout programs now rely only on
  ACTC-emitted machine records. Their three root-body templates have been
  removed from ALINK, and the compact forms are rejection-only probe inputs.
- The imported `printmath` program and its library dependency now use ordinary
  machine records, named relocations, and import closure. ALINK's dedicated
  printmath strategy, compact `s0i0r` library parser, and generated PRG template
  have been removed; both compact forms are rejection-only inputs.
- A simple integer equality `IF` now uses ACTC-emitted machine code plus a
  named relocation to the synthetic `__if0` local export. ALINK's matching
  compact-body candidate and generated PRG template have been removed, and the
  retired body is retained only as a rejection input.
- The matching integer not-equal `IF` path now uses the same compiler-owned
  native object and named-relocation design. Its linker candidate/template are
  removed and the compact body is rejection-only.
- The simple unsigned integer less-than `IF` path is compiler-owned as well.
  Its former linker candidate/template are removed and the compact body is
  rejection-only.
- The simple unsigned integer greater-than `IF` path now uses ACTC-emitted
  machine code and a named relocation to `__if0`. Its linker candidate/template
  are removed and the compact body is rejection-only.
- The simple unsigned integer greater-equal and less-equal `IF` paths now use
  ACTC-emitted machine code and named `__if0` relocations as well. Their former
  ALINK candidates/templates are removed, and both compact bodies are retained
  only as rejection probes.
- The simple equality `IF/ELSE` path now uses ACTC-emitted `__if0` and `__if1`
  local exports for the else entry and join. Its ALINK candidate/template is
  removed, both true and false direct-PRG paths are live-tested, and the compact
  body is retained only as a rejection probe.
- Two-level integer `IF` and inner `IF/ELSE` paths now use ACTC-emitted
  `__if0` through `__if3` local exports. Their ALINK candidates/templates are
  removed, inner true/false and outer-false paths are launch-tested, and both
  retired compact bodies are rejection probes.
- All eleven local-procedure control-flow shapes now arrive as machine-code OBJ
  records with named procedure/label relocations. Their linker body signatures
  and generated PRG templates have been removed.
- Straight-line `REAL(integer)` assignment followed by `PrintR` or `PrintRE`
  now arrives as compiler-emitted machine code with ordinary helper, data, and
  pointer relocations. ALINK's matching body recognizer and PRG builder have
  been removed, so this source form uses only generic OBJ closure and relocation.
- The adjacent `REAL(integer)` followed by `INT(real)` conversion is also a
  compiler-emitted machine OBJ. Its former linker-side recognizer, fixed-address
  PRG builder, and storage helpers are removed; generic named/import relocation
  now determines all code, data, result-store, pointer, and helper addresses.
- A one-argument runtime helper followed by `REAL(integer)` and `PrintRE`, with
  or without storing the helper result, now arrives as compiler-emitted machine
  OBJ as well. ACTC preserves byte-in-A and word-in-X/Y helper ABIs. ALINK's two
  matching recognizers, fixed-address builders, and compact signatures are
  removed, recovering 729 bytes while leaving only generic closure and relocation.
- All plain, ELSE, and two-level nested REAL IF comparison forms now arrive as
  compiler-emitted machine OBJ from `ACTC_OVLB.BIN`. The dedicated REAL IF
  recognizer, fixed `$10xx` builder, compact signatures, and strategy ID are
  removed, recovering another 1,514 bytes. All 36 variants use only generic
  closure and relocation.
- All six simple REAL `DO ... UNTIL` comparisons and eight REAL add/sub update
  loops now also arrive as relocatable machine OBJ from `ACTC_OVLB.BIN`.
  ALINK's REAL DO/UNTIL strategy ID, recognizer, fixed-address builders,
  pointer/storage helpers, and ten compact signatures are removed. This shrinks
  `ALINK.PRG` from 27,043 to 24,431 bytes; all 14 forms pass exact object/link
  checks and execute as self-contained PRGs under VICE.
- The seeded ALINK smoke fixture now uses a machine root, an external `u w`
  import, an `r 1 u0` relocation, and a machine `W` module. With that final
  migration, ALINK has no generic compact-body candidate/template table;
  unsupported non-machine bodies are rejected instead of compiled by ALINK.
- The remaining 102 seeded runtime fixtures have also been converted from
  compact bodies to native machine records and ordinary import relocations.
  ACTC owns 194 exact runtime-sequence machine cases, including 77 readback and
  nine nested cases; 271 more complex source-runtime cases validate ACTC's OBJ
  fragments before an independent host object parser/relocator checks ALINK's
  exact final image.
- Seeded direct-object input coverage now includes joystick state plus joystick
  button 1 and 2 state nested into graphics, SID volume, SID frequency, SID
  pulse, SID cutoff, SID wave, SID attack/decay, SID sustain/release, and
  sprite helpers, joystick state plus joystick button 1 and 2 state
  source-emitted from stored results or nested into graphics, sprite color,
  SID volume, SID frequency, SID pulse, SID cutoff, SID wave, SID attack/decay, and
  SID sustain/release helpers, joystick and mouse presence state
  source-emitted from stored results or nested into graphics, SID volume,
  SID frequency, SID pulse, SID cutoff, SID wave, SID attack/decay,
  SID sustain/release, and sprite color helpers, mouse button state plus
  mouse button 1 and 2 state source-emitted or nested into graphics helpers,
  mouse button 1 and 2 state source-emitted or nested into sprite color helpers,
  mouse button 1 and 2 state source-emitted or nested into SID frequency,
  SID pulse, SID cutoff, SID wave, SID attack/decay, and SID sustain/release
  helpers, mouse button state nested into SID volume and sprite color helpers,
  mouse button 1 and 2 state nested into direct sprite helpers,
  and mouse button 1 and 2 state nested into direct graphics helpers,
  proving `RT_JOY.OBJ`, `RT_JB1.OBJ` / `RT_JOY.OBJ`,
  `RT_JB2.OBJ` / `RT_JOY.OBJ`, `RT_MB.OBJ` / `RT_MS.OBJ`,
  `RT_MB1.OBJ` / `RT_MB.OBJ` / `RT_MS.OBJ`, and
  `RT_MB2.OBJ` / `RT_MB.OBJ` / `RT_MS.OBJ` dependency closure without pulling
  unrelated input helpers.

Current focus:

- Host ALINK now selects non-first OBJ1 exports, follows only imports and
  relocations in each reachable export body, copies only selected byte ranges,
  and decodes canonical `u0` through `uZ` import references.
- preserve generic object closure and relocation behavior as ACTC source
  coverage grows
- keep legacy compact bodies rejection-only so synthesis cannot return
- keep direct PRG layout deterministic
- keep optional helper families link-selected
- keep stale runner assumptions out of tests, release images, and docs
